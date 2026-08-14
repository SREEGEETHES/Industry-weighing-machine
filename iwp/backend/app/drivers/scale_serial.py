"""
Scale driver for a scale/indicator wired directly into the machine running
this software over RS232/RS485 (no WiFi bridge). Use this if you decide to
run the software on an industrial PC sitting right next to the indicator.
"""
import re
import serial
from app.drivers.base import (
    ScaleDriver, WeightReading,
    DriverConnectionError, DriverReadTimeoutError, DriverProtocolError,
)


class SerialScaleDriver(ScaleDriver):
    def __init__(self, serial_port: str, baud_rate: int, parity: str,
                 stopbits: int, bytesize: int, parse_pattern: str,
                 unit: str = "kg", timeout_sec: float = 3.0):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.parity = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN,
                        "O": serial.PARITY_ODD}.get(parity.upper(), serial.PARITY_NONE)
        self.stopbits = {1: serial.STOPBITS_ONE, 2: serial.STOPBITS_TWO}.get(
            stopbits, serial.STOPBITS_ONE)
        self.bytesize = {7: serial.SEVENBITS, 8: serial.EIGHTBITS}.get(
            bytesize, serial.EIGHTBITS)
        self.parse_pattern = re.compile(parse_pattern)
        self.unit = unit
        self.timeout_sec = timeout_sec
        self._ser: serial.Serial | None = None
        self._connected = False

    def connect(self) -> None:
        try:
            self._ser = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=self.timeout_sec,
            )
            self._connected = True
        except serial.SerialException as e:
            self._connected = False
            raise DriverConnectionError(
                f"Could not open serial port {self.serial_port}: {e}"
            ) from e

    def read_weight(self) -> WeightReading:
        if not self._connected or self._ser is None:
            raise DriverConnectionError("Scale not connected. Call connect() first.")
        try:
            raw_bytes = self._ser.readline()
        except serial.SerialException as e:
            self._connected = False
            raise DriverConnectionError(f"Lost connection to scale: {e}") from e

        if not raw_bytes:
            raise DriverReadTimeoutError(
                f"No data from scale within {self.timeout_sec}s "
                f"(is something placed on the platform?)"
            )

        raw = raw_bytes.decode(errors="ignore").strip()
        match = self.parse_pattern.search(raw)
        if not match:
            raise DriverProtocolError(
                f"Could not parse a weight value out of scale response: {raw!r} "
                f"using pattern {self.parse_pattern.pattern!r}. "
                f"Adjust the parse pattern in the station's device settings."
            )
        try:
            value = float(match.group(1))
        except (ValueError, IndexError) as e:
            raise DriverProtocolError(f"Matched text was not a valid number: {raw!r}") from e

        return WeightReading(value=value, unit=self.unit, raw=raw)

    def disconnect(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()
        self._ser = None
        self._connected = False
