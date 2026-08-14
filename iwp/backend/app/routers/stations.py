from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/stations", tags=["stations"])


@router.get("", response_model=list[schemas.StationOut])
def list_stations(db: Session = Depends(get_db)):
    return db.query(models.Station).all()


@router.post("", response_model=schemas.StationOut)
def create_station(payload: schemas.StationIn, db: Session = Depends(get_db)):
    if db.query(models.Station).filter_by(name=payload.name).first():
        raise HTTPException(400, "A station with this name already exists.")
    if db.query(models.Station).filter_by(machine_id=payload.machine_id).first():
        raise HTTPException(400, "A station with this machine_id already exists.")
    station = models.Station(**payload.model_dump())
    db.add(station)
    db.commit()
    db.refresh(station)
    return station


@router.get("/{station_id}", response_model=schemas.StationOut)
def get_station(station_id: int, db: Session = Depends(get_db)):
    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "Station not found.")
    return station


@router.put("/{station_id}", response_model=schemas.StationOut)
def update_station(station_id: int, payload: schemas.StationIn, db: Session = Depends(get_db)):
    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "Station not found.")
    for k, v in payload.model_dump().items():
        setattr(station, k, v)
    db.commit()
    db.refresh(station)
    return station


@router.delete("/{station_id}")
def delete_station(station_id: int, db: Session = Depends(get_db)):
    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "Station not found.")
    db.delete(station)
    db.commit()
    return {"status": "deleted"}


# ---------------- Scale device on a station ----------------
@router.put("/{station_id}/scale", response_model=schemas.ScaleDeviceOut)
def upsert_scale(station_id: int, payload: schemas.ScaleDeviceIn, db: Session = Depends(get_db)):
    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "Station not found.")
    if station.scale:
        for k, v in payload.model_dump().items():
            setattr(station.scale, k, v)
        device = station.scale
    else:
        device = models.ScaleDevice(station_id=station_id, **payload.model_dump())
        db.add(device)
    db.commit()
    db.refresh(device)
    return device


# ---------------- Printer device on a station ----------------
@router.put("/{station_id}/printer", response_model=schemas.PrinterDeviceOut)
def upsert_printer(station_id: int, payload: schemas.PrinterDeviceIn, db: Session = Depends(get_db)):
    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "Station not found.")
    if station.printer:
        for k, v in payload.model_dump().items():
            setattr(station.printer, k, v)
        device = station.printer
    else:
        device = models.PrinterDevice(station_id=station_id, **payload.model_dump())
        db.add(device)
    db.commit()
    db.refresh(device)
    return device


# ---------------- Trigger a weigh+print cycle on this station ----------------
@router.post("/{station_id}/weigh")
def trigger_weigh(station_id: int, payload: schemas.ManualWeighRequest, db: Session = Depends(get_db)):
    from app.services.weighing_service import (
        perform_weigh_and_print, StationNotConfiguredError,
    )
    from app.drivers.base import (
        DriverConnectionError, DriverReadTimeoutError, DriverProtocolError,
    )

    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "Station not found.")
    if not station.is_enabled:
        raise HTTPException(400, f"Station '{station.name}' is disabled in the admin panel.")

    try:
        result = perform_weigh_and_print(
            db, station,
            batch_number=payload.batch_number,
            operator=payload.operator,
        )
    except StationNotConfiguredError as e:
        raise HTTPException(400, str(e))
    except DriverConnectionError as e:
        raise HTTPException(502, f"Device connection error: {e}")
    except DriverReadTimeoutError as e:
        raise HTTPException(408, f"Scale read timeout: {e}")
    except DriverProtocolError as e:
        raise HTTPException(422, f"Device protocol error: {e}")

    return {
        "box_id": result.box_id,
        "weight": result.weight,
        "unit": result.unit,
        "within_tolerance": result.within_tolerance,
        "variance": result.variance,
        "print_status": result.print_status,
    }


@router.post("/{station_id}/reprint/{box_id}")
def reprint(station_id: int, box_id: str, db: Session = Depends(get_db)):
    from app.services.weighing_service import reprint_box, StationNotConfiguredError
    from app.drivers.base import DriverConnectionError, DriverProtocolError

    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "Station not found.")
    record = db.query(models.BoxRecord).filter_by(box_id=box_id).first()
    if not record:
        raise HTTPException(404, "Box record not found.")

    try:
        status = reprint_box(db, station, record)
    except StationNotConfiguredError as e:
        raise HTTPException(400, str(e))
    except (DriverConnectionError, DriverProtocolError) as e:
        raise HTTPException(502, f"Reprint failed: {e}")

    return {"box_id": box_id, "print_status": status}


@router.post("/{station_id}/start-monitoring")
def start_monitoring(station_id: int, db: Session = Depends(get_db)):
    """Start automatic weighing monitoring for this station."""
    from app.services.auto_weighing_service import start_auto_monitoring
    
    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "Station not found.")
    
    if not station.scale or not station.printer:
        raise HTTPException(400, "Station must have both scale and printer configured.")
    
    start_auto_monitoring(station_id)
    return {"status": "monitoring_started", "station_id": station_id}


@router.post("/{station_id}/stop-monitoring")
def stop_monitoring(station_id: int, db: Session = Depends(get_db)):
    """Stop automatic weighing monitoring for this station."""
    from app.services.auto_weighing_service import stop_auto_monitoring
    
    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "Station not found.")
    
    stop_auto_monitoring(station_id)
    return {"status": "monitoring_stopped", "station_id": station_id}
