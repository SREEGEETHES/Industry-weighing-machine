"""
Linx RCI (Remote Command Interface) printer driver.

RCI is a binary, packet-based protocol used by Linx CJ-series printers.
The packet framing below (STX/ETX wrapper, length byte, checksum) follows
the general structure Linx documents in their RCI Programmer's Manual for
the CJ range, but the exact command byte codes and field indices depend on
your printer's firmware version - Linx has changed these across product
generations, and I do not have your specific manual to copy exact byte
values from.

WHAT'S REAL HERE: the TCP socket handling, packet framing, checksum
calculation, and field-mapping logic are fully implemented and will talk to
a real printer over the network. WHAT YOU MUST CONFIRM before going live:
the three constants marked "CONFIRM WITH RCI MANUAL" below - open your
printer's RCI Programmer's Manual (Linx ships one per printer family), find
the "Select stored message" and "Update variable field" command codes, and
paste the exact byte values in. This is a half-day task once you have the
manual/printer in hand, not something I can guess correctly without it -
guessing here would risk sending malformed commands to a live printer on
your line, which is worse than telling you plainly what's still needed.

If your chosen printer instead supports the simpler Ethernet text protocol
(common on newer firmware / as an alternative integration mode), use
`printer_tcp_text.py` instead and skip this file entirely - it needs no
calibration.
"""
import socket
from app.drivers.base import (
    PrinterDriver, DriverConnectionError, DriverProtocolError,
)

STX = 0x02
ETX = 0x03

# CONFIRM WITH RCI MANUAL: command byte for "select stored message by slot"
CMD_SELECT_MESSAGE = 0x10
# CONFIRM WITH RCI MANUAL: command byte for "update a variable text field"
CMD_UPDATE_FIELD = 0x11
# CONFIRM WITH RCI MANUAL: command byte for "trigger print of current message"
CMD_PRINT_TRIGGER = 0x12


def _checksum(payload: bytes) -> int:
    """Simple XOR checksum over the payload bytes. Confirm this matches
    your printer manual's checksum algorithm - some RCI variants use XOR,
    others use a summed modulo-256 checksum."""
    cksum = 0
    for b in payload:
        cksum ^= b
    return cksum


def _build_packet(command: int, data: bytes) -> bytes:
    length = len(data) + 1  # +1 for the command byte itself
    payload = bytes([command]) + data
    packet = bytes([STX, length]) + payload
    packet += bytes([_checksum(payload), ETX])
    return packet


class LinxRciPrinterDriver(PrinterDriver):
    def __init__(self, ip_address: str, port: int, timeout_sec: float = 3.0,
                 message_slot: int = 1, field_map: dict[str, int] | None = None):
        self.ip_address = ip_address
        self.port = port
        self.timeout_sec = timeout_sec
        self.message_slot = message_slot
        # field_map: {"BOX_ID": 1, "WEIGHT": 2, "PRODUCT": 3, ...}
        # Maps our template keys to the printer's stored-message field
        # index. Set this per-printer in the admin panel (rci_field_map),
        # since every stored message layout is designed differently.
        self.field_map = field_map or {}
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
                f"Could not connect to Linx printer at "
                f"{self.ip_address}:{self.port} - {e}"
            ) from e

    def _send_and_ack(self, packet: bytes, context: str) -> None:
        try:
            self._sock.sendall(packet)
            response = self._sock.recv(64)
        except (OSError, socket.timeout) as e:
            self._connected = False
            raise DriverConnectionError(f"Lost connection during {context}: {e}") from e

        if not response or response[0] != STX:
            raise DriverProtocolError(
                f"Printer did not ACK {context} (got {response!r}). "
                f"Verify command codes against your RCI manual."
            )

    def print_fields(self, fields: dict) -> None:
        if not self._connected or self._sock is None:
            raise DriverConnectionError("Printer not connected. Call connect() first.")
        if not self.field_map:
            raise DriverProtocolError(
                "No RCI field map configured for this printer. Set "
                "rci_field_map in the station's printer settings to map "
                "template keys (BOX_ID, WEIGHT, ...) to stored-message "
                "field indices before printing."
            )

        # 1. Select the stored message template
        select_packet = _build_packet(
            CMD_SELECT_MESSAGE, bytes([self.message_slot])
        )
        self._send_and_ack(select_packet, "message select")

        # 2. Push each field's value into its mapped field index
        for key, field_index in self.field_map.items():
            value = str(fields.get(key, ""))
            data = bytes([field_index]) + value.encode("ascii", errors="ignore")
            update_packet = _build_packet(CMD_UPDATE_FIELD, data)
            self._send_and_ack(update_packet, f"field update ({key})")

        # 3. Trigger the physical print
        print_packet = _build_packet(CMD_PRINT_TRIGGER, b"")
        self._send_and_ack(print_packet, "print trigger")

    def disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        self._connected = False
