"""
Generic TCP "text message field" printer driver.

Most modern industrial CIJ/thermal inkjet printers (Domino Ax-series,
Videojet 1000-series in Ethernet mode, Markem-Imaje, EBS, many Linx models
too) support a simple Ethernet interface where you open a TCP socket and
send a delimited text command to update a stored message's variable
fields, then trigger a print. This driver implements that general pattern.

IMPORTANT: The exact command syntax (field delimiter, message name syntax,
trigger command) differs per printer brand/firmware. The three lines below
marked "CONFIRM WITH PRINTER MANUAL" are the only lines you need to adjust
once you've picked a printer model - everything else in the system is
protocol-agnostic.
"""
import socket
from app.drivers.base import (
    PrinterDriver, DriverConnectionError, DriverProtocolError,
)


class TcpTextPrinterDriver(PrinterDriver):
    def __init__(self, ip_address: str, port: int, timeout_sec: float = 3.0,
                 field_delimiter: str = "|", line_terminator: str = "\r\n",
                 message_name: str = "IWPAS_MSG"):
        self.ip_address = ip_address
        self.port = port
        self.timeout_sec = timeout_sec
        self.field_delimiter = field_delimiter          # CONFIRM WITH PRINTER MANUAL
        self.line_terminator = line_terminator           # CONFIRM WITH PRINTER MANUAL
        self.message_name = message_name                 # CONFIRM WITH PRINTER MANUAL
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
                f"Could not connect to printer at {self.ip_address}:{self.port} - {e}"
            ) from e

    def print_fields(self, fields: dict) -> None:
        if not self._connected or self._sock is None:
            raise DriverConnectionError("Printer not connected. Call connect() first.")

        # Build "SELECT|IWPAS_MSG" then "SET|KEY=VALUE|KEY=VALUE|..." then "PRINT"
        # This is a generic pattern - swap for your printer's exact command
        # set once confirmed (most vendors publish an "Ethernet Integration"
        # or "Host Comms" manual with the exact grammar).
        select_cmd = f"SELECT{self.field_delimiter}{self.message_name}{self.line_terminator}"
        field_pairs = self.field_delimiter.join(f"{k}={v}" for k, v in fields.items())
        set_cmd = f"SET{self.field_delimiter}{field_pairs}{self.line_terminator}"
        print_cmd = f"PRINT{self.line_terminator}"

        try:
            for cmd in (select_cmd, set_cmd, print_cmd):
                self._sock.sendall(cmd.encode())
            ack = self._sock.recv(256).decode(errors="ignore").strip()
        except (OSError, socket.timeout) as e:
            self._connected = False
            raise DriverConnectionError(f"Lost connection to printer while printing: {e}") from e

        if ack and ("ERR" in ack.upper() or "NAK" in ack.upper()):
            raise DriverProtocolError(f"Printer rejected the print command: {ack}")

    def disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        self._connected = False
