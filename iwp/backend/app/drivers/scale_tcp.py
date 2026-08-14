"""
Scale driver for scales/indicators reached over TCP - this is the expected
path for your setup since the communication is wireless: the RS232/RS485
output of the indicator goes into a serial-to-WiFi bridge, and the bridge
exposes a plain TCP socket on the factory LAN. The software here just needs
the bridge's IP and port.
"""
import re
import socket
from app.drivers.base import (
    ScaleDriver, WeightReading,
    DriverConnectionError, DriverReadTimeoutError, DriverProtocolError,
)


class TcpScaleDriver(ScaleDriver):
    def __init__(self, ip_address: str, port: int, parse_pattern: str,
                 unit: str = "kg", timeout_sec: float = 3.0):
        self.ip_address = ip_address
        self.port = port
        self.parse_pattern = re.compile(parse_pattern)
        self.unit = unit
        self.timeout_sec = timeout_sec
        self._sock: socket.socket | None = None
        self._connected = False

    def connect(self) -> None:
        try:
            self._sock = socket.create_connection(
                (self.ip_address, self.port), timeout=self.timeout_sec
            )
            self._sock.settimeout(self.timeout_sec)
            self._connected = True
        except (OSError, socket.timeout) as e:
            self._connected = False
            raise DriverConnectionError(
                f"Could not connect to scale bridge at "
                f"{self.ip_address}:{self.port} - {e}"
            ) from e

    def read_weight(self) -> WeightReading:
        if not self._connected or self._sock is None:
            raise DriverConnectionError("Scale not connected. Call connect() first.")
        try:
            raw_bytes = self._sock.recv(256)
        except socket.timeout as e:
            raise DriverReadTimeoutError(
                f"No data from scale within {self.timeout_sec}s "
                f"(is something placed on the platform?)"
            ) from e
        except OSError as e:
            self._connected = False
            raise DriverConnectionError(f"Lost connection to scale: {e}") from e

        if not raw_bytes:
            self._connected = False
            raise DriverConnectionError("Scale closed the connection.")

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
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        self._connected = False
