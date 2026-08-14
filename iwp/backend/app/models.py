import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.database import Base


class Station(Base):
    """One physical weigh + print line. The photo shows what would be one
    Station: scale at position 2 feeding the sealer/printer at position 3."""
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)          # e.g. "Line 1"
    machine_id = Column(String(50), unique=True, nullable=False)      # printed on box, e.g. "L1"
    active_preset_id = Column(Integer, ForeignKey("weight_presets.id"), nullable=True)
    is_enabled = Column(Boolean, default=True)

    active_preset = relationship("WeightPreset")
    scale = relationship("ScaleDevice", back_populates="station", uselist=False)
    printer = relationship("PrinterDevice", back_populates="station", uselist=False)


class ScaleDevice(Base):
    __tablename__ = "scale_devices"

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.id"), unique=True, nullable=False)

    brand = Column(String(100), default="")
    model = Column(String(100), default="")

    # "serial" (RS232/RS485 direct or via WiFi-to-serial bridge exposing a
    # local COM/tty port) or "tcp" (bridge/scale exposes a raw TCP socket,
    # which is what most RS232-to-WiFi bridges do).
    connection_type = Column(String(10), default="tcp")   # "tcp" | "serial"

    # TCP connection (used when connection_type == "tcp")
    ip_address = Column(String(50), default="")
    port = Column(Integer, default=4001)

    # Serial connection (used when connection_type == "serial")
    serial_port = Column(String(50), default="")   # e.g. COM3 or /dev/ttyUSB0
    baud_rate = Column(Integer, default=9600)
    parity = Column(String(1), default="N")
    stopbits = Column(Integer, default=1)
    bytesize = Column(Integer, default=8)

    # Regex used to pull the numeric weight out of whatever string the scale
    # sends, e.g. an Avery Weigh-Tronix indicator might send "ST,GS,+012.250,kg"
    # This is fully configurable per-device instead of hardcoded per-brand.
    parse_pattern = Column(String(200), default=r"([-+]?\d+\.?\d*)")
    unit = Column(String(10), default="kg")
    timeout_sec = Column(Float, default=3.0)

    station = relationship("Station", back_populates="scale")


class PrinterDevice(Base):
    __tablename__ = "printer_devices"

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.id"), unique=True, nullable=False)

    brand = Column(String(100), default="")
    model = Column(String(100), default="")

    # "tcp_text"  -> raw TCP socket, plain text message field protocol
    # "linx_rci"  -> Linx RCI binary packet protocol
    protocol = Column(String(20), default="tcp_text")

    ip_address = Column(String(50), default="")
    port = Column(Integer, default=9100)
    timeout_sec = Column(Float, default=3.0)

    # RCI-specific fields (only relevant when protocol == "linx_rci")
    rci_message_slot = Column(Integer, default=1)   # which stored message to trigger
    rci_field_map = Column(Text, default="{}")       # JSON: {"field_index": "template_key"}

    station = relationship("Station", back_populates="printer")


class WeightPreset(Base):
    """Matches the format you described:
    {"500g x 24": {"target": 12.000, "min": 12.000, "max": 12.250}}"""
    __tablename__ = "weight_presets"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    target_weight = Column(Float, nullable=False)
    min_weight = Column(Float, nullable=False)
    max_weight = Column(Float, nullable=False)
    product_code = Column(String(2), default="")


class BoxRecord(Base):
    """One row per box weighed and printed. This is the audit trail."""
    __tablename__ = "box_records"

    id = Column(Integer, primary_key=True)
    box_id = Column(String(30), unique=True, nullable=False, index=True)   # BOX-2026-000001
    sequence_number = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    machine_id = Column(String(50), nullable=False)

    weight = Column(Float, nullable=False)
    unit = Column(String(10), default="kg")

    product_code = Column(String(2), default="")
    batch_number = Column(String(50), default="")

    target_weight = Column(Float, nullable=True)
    min_weight = Column(Float, nullable=True)
    max_weight = Column(Float, nullable=True)
    within_tolerance = Column(Boolean, nullable=True)
    variance = Column(Float, nullable=True)   # weight - target_weight

    operator = Column(String(100), default="")

    print_status = Column(String(20), default="pending")  # pending|printed|failed
    print_retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=dt.datetime.utcnow, index=True)


class EmailRecipient(Base):
    __tablename__ = "email_recipients"

    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, nullable=False)
    name = Column(String(100), default="")
    is_active = Column(Boolean, default=True)


class ReportLog(Base):
    """Keeps a record of every weekly report actually sent, for audit."""
    __tablename__ = "report_logs"

    id = Column(Integer, primary_key=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    recipients = Column(Text, default="")   # comma-separated, snapshot at send time
    box_count = Column(Integer, default=0)
    file_path = Column(String(300), default="")
    sent_at = Column(DateTime, default=dt.datetime.utcnow)
    status = Column(String(20), default="sent")  # sent|failed
    error_message = Column(Text, default="")
