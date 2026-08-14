import datetime as dt
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Weight Presets ----------
class WeightPresetIn(BaseModel):
    name: str
    target_weight: float
    min_weight: float
    max_weight: float
    product_code: str = ""


class WeightPresetOut(WeightPresetIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Scale device ----------
class ScaleDeviceIn(BaseModel):
    brand: str = ""
    model: str = ""
    connection_type: str = "tcp"          # "tcp" | "serial"
    ip_address: str = ""
    port: int = 4001
    serial_port: str = ""
    baud_rate: int = 9600
    parity: str = "N"
    stopbits: int = 1
    bytesize: int = 8
    parse_pattern: str = r"([-+]?\d+\.?\d*)"
    unit: str = "kg"
    timeout_sec: float = 3.0


class ScaleDeviceOut(ScaleDeviceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    station_id: int


# ---------- Printer device ----------
class PrinterDeviceIn(BaseModel):
    brand: str = ""
    model: str = ""
    protocol: str = "tcp_text"            # "tcp_text" | "linx_rci"
    ip_address: str = ""
    port: int = 9100
    timeout_sec: float = 3.0
    rci_message_slot: int = 1
    rci_field_map: str = "{}"


class PrinterDeviceOut(PrinterDeviceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    station_id: int


# ---------- Station ----------
class StationIn(BaseModel):
    name: str
    machine_id: str
    active_preset_id: Optional[int] = None
    is_enabled: bool = True


class StationOut(StationIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    scale: Optional[ScaleDeviceOut] = None
    printer: Optional[PrinterDeviceOut] = None


# ---------- Box record ----------
class BoxRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    box_id: str
    sequence_number: int
    year: int
    station_id: int
    machine_id: str
    weight: float
    unit: str
    product_code: str
    batch_number: str
    target_weight: Optional[float]
    min_weight: Optional[float]
    max_weight: Optional[float]
    within_tolerance: Optional[bool]
    variance: Optional[float]
    operator: str
    print_status: str
    print_retry_count: int
    created_at: dt.datetime


class ManualWeighRequest(BaseModel):
    """Used when an operator triggers weighing manually (button/pedal mode)
    instead of the station auto-capturing on a stable reading."""
    station_id: int
    batch_number: str = ""
    operator: str = ""


# ---------- Email recipients ----------
class EmailRecipientIn(BaseModel):
    email: EmailStr
    name: str = ""
    is_active: bool = True


class EmailRecipientOut(EmailRecipientIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
