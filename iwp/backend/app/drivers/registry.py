"""
Factory functions that turn a Station's DB-stored device config into a live
driver instance. This is the one place that knows how to map admin-panel
settings to a concrete driver class - add a new brand/protocol by adding
one branch here, nothing else in the system needs to change.
"""
import json
from app.models import ScaleDevice, PrinterDevice
from app.drivers.base import ScaleDriver, PrinterDriver
from app.drivers.scale_tcp import TcpScaleDriver
from app.drivers.scale_serial import SerialScaleDriver
from app.drivers.printer_tcp_text import TcpTextPrinterDriver
from app.drivers.printer_linx_rci import LinxRciPrinterDriver


def build_scale_driver(device: ScaleDevice) -> ScaleDriver:
    if device.connection_type == "tcp":
        return TcpScaleDriver(
            ip_address=device.ip_address,
            port=device.port,
            parse_pattern=device.parse_pattern,
            unit=device.unit,
            timeout_sec=device.timeout_sec,
        )
    elif device.connection_type == "serial":
        return SerialScaleDriver(
            serial_port=device.serial_port,
            baud_rate=device.baud_rate,
            parity=device.parity,
            stopbits=device.stopbits,
            bytesize=device.bytesize,
            parse_pattern=device.parse_pattern,
            unit=device.unit,
            timeout_sec=device.timeout_sec,
        )
    raise ValueError(f"Unknown scale connection_type: {device.connection_type}")


def build_printer_driver(device: PrinterDevice) -> PrinterDriver:
    if device.protocol == "tcp_text":
        return TcpTextPrinterDriver(
            ip_address=device.ip_address,
            port=device.port,
            timeout_sec=device.timeout_sec,
        )
    elif device.protocol == "linx_rci":
        try:
            field_map = json.loads(device.rci_field_map or "{}")
        except json.JSONDecodeError:
            field_map = {}
        return LinxRciPrinterDriver(
            ip_address=device.ip_address,
            port=device.port,
            timeout_sec=device.timeout_sec,
            message_slot=device.rci_message_slot,
            field_map=field_map,
        )
    raise ValueError(f"Unknown printer protocol: {device.protocol}")
