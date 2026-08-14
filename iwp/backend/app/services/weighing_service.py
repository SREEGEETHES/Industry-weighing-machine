"""
Core weighing service.

For each Station this:
  1. Connects to the real scale driver.
  2. Polls real readings until STABILITY_SAMPLE_COUNT consecutive readings
     agree within STABILITY_TOLERANCE_KG (i.e. the box has actually settled
     on the platform, not mid-placement noise).
  3. Validates the stable weight against the station's active WeightPreset
     tolerance (target/min/max).
  4. Generates the next sequential Box ID.
  5. Builds the print field dict and sends it to the real printer driver.
  6. Writes one BoxRecord row - this is the permanent audit trail.

No part of this simulates a reading or a print. If the scale or printer is
unreachable, the relevant DriverConnectionError/DriverReadTimeoutError
propagates up and the station is reported offline/failed - by design.
"""
import datetime as dt
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import (
    STABILITY_SAMPLE_COUNT, STABILITY_TOLERANCE_KG, STABILITY_POLL_INTERVAL_SEC,
)
from app.models import Station, BoxRecord
from app.drivers.base import (
    WeightReading, DriverReadTimeoutError, DriverConnectionError, DriverProtocolError,
)
from app.drivers.registry import build_scale_driver, build_printer_driver
from app.services.box_id_generator import generate_box_id

logger = logging.getLogger("iwpas.weighing")


class StationNotConfiguredError(Exception):
    pass


@dataclass
class WeighAndPrintResult:
    box_id: str
    weight: float
    unit: str
    within_tolerance: bool | None
    variance: float | None
    print_status: str


def wait_for_stable_weight(scale_driver, max_wait_sec: float = 15.0) -> WeightReading:
    """Poll the real scale until STABILITY_SAMPLE_COUNT consecutive readings
    agree within tolerance, or raise DriverReadTimeoutError if nothing
    stabilizes within max_wait_sec."""
    import time

    readings: list[WeightReading] = []
    start = time.monotonic()

    while time.monotonic() - start < max_wait_sec:
        reading = scale_driver.read_weight()
        readings.append(reading)
        if len(readings) >= STABILITY_SAMPLE_COUNT:
            window = readings[-STABILITY_SAMPLE_COUNT:]
            spread = max(r.value for r in window) - min(r.value for r in window)
            if spread <= STABILITY_TOLERANCE_KG:
                return window[-1]
        time.sleep(STABILITY_POLL_INTERVAL_SEC)

    raise DriverReadTimeoutError(
        f"Weight did not stabilize within {max_wait_sec}s "
        f"(last readings: {[r.value for r in readings[-STABILITY_SAMPLE_COUNT:]]})"
    )


def perform_weigh_and_print(
    db: Session,
    station: Station,
    batch_number: str = "",
    operator: str = "",
) -> WeighAndPrintResult:
    if station.scale is None:
        raise StationNotConfiguredError(f"Station '{station.name}' has no scale configured.")
    if station.printer is None:
        raise StationNotConfiguredError(f"Station '{station.name}' has no printer configured.")

    scale_driver = build_scale_driver(station.scale)
    printer_driver = build_printer_driver(station.printer)

    scale_driver.connect()
    try:
        reading = wait_for_stable_weight(scale_driver)
    finally:
        scale_driver.disconnect()

    preset = station.active_preset
    within_tolerance = None
    variance = None
    if preset is not None:
        variance = round(reading.value - preset.target_weight, 3)
        within_tolerance = preset.min_weight <= reading.value <= preset.max_weight

    box_id, sequence_number, year = generate_box_id(db)
    now = dt.datetime.utcnow()

    fields = {
        "BOX_ID": box_id,
        "WEIGHT": f"{reading.value:.3f} {reading.unit}",
        "PRODUCT": preset.product_code if preset else "",
        "BATCH": batch_number,
        "DATE": now.strftime("%d/%m/%Y"),
        "TIME": now.strftime("%H:%M:%S"),
        "MACHINE_ID": station.machine_id,
    }

    print_status = "pending"
    retry_count = 0
    try:
        printer_driver.connect()
        try:
            printer_driver.print_fields(fields)
            print_status = "printed"
        finally:
            printer_driver.disconnect()
    except (DriverConnectionError, DriverProtocolError) as e:
        print_status = "failed"
        retry_count = 1
        logger.error("Print failed for %s on station %s: %s", box_id, station.name, e)

    record = BoxRecord(
        box_id=box_id,
        sequence_number=sequence_number,
        year=year,
        station_id=station.id,
        machine_id=station.machine_id,
        weight=round(reading.value, 3),
        unit=reading.unit,
        product_code=preset.product_code if preset else "",
        batch_number=batch_number,
        target_weight=preset.target_weight if preset else None,
        min_weight=preset.min_weight if preset else None,
        max_weight=preset.max_weight if preset else None,
        within_tolerance=within_tolerance,
        variance=variance,
        operator=operator,
        print_status=print_status,
        print_retry_count=retry_count,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    if print_status == "failed":
        # The audit row still exists (weight is on record) but the physical
        # box was NOT marked - this must surface to the operator UI clearly
        # so they know to retry the print before the box leaves the station.
        logger.warning("Box %s weighed but NOT printed - requires reprint.", box_id)

    return WeighAndPrintResult(
        box_id=box_id,
        weight=record.weight,
        unit=record.unit,
        within_tolerance=within_tolerance,
        variance=variance,
        print_status=print_status,
    )


def reprint_box(db: Session, station: Station, record: BoxRecord) -> str:
    """Re-send an existing audit record's fields to the printer without
    generating a new Box ID or weighing again - for when print_status
    is 'failed' and the operator wants to retry."""
    if station.printer is None:
        raise StationNotConfiguredError(f"Station '{station.name}' has no printer configured.")

    printer_driver = build_printer_driver(station.printer)
    fields = {
        "BOX_ID": record.box_id,
        "WEIGHT": f"{record.weight:.3f} {record.unit}",
        "PRODUCT": record.product_code,
        "BATCH": record.batch_number,
        "DATE": record.created_at.strftime("%d/%m/%Y"),
        "TIME": record.created_at.strftime("%H:%M:%S"),
        "MACHINE_ID": record.machine_id,
    }

    printer_driver.connect()
    try:
        printer_driver.print_fields(fields)
        record.print_status = "printed"
    except (DriverConnectionError, DriverProtocolError) as e:
        record.print_status = "failed"
        record.print_retry_count += 1
        db.commit()
        raise
    else:
        db.commit()
    finally:
        printer_driver.disconnect()

    return record.print_status
