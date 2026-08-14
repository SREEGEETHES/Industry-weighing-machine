"""
Driver abstraction layer.

Every real scale and every real printer, no matter the brand, implements
one of these two interfaces. The core weighing service only ever talks to
`ScaleDriver` and `PrinterDriver` — it never knows or cares whether the
scale underneath is a Mettler Toledo on RS232 or an Essae on TCP. This is
what lets you swap hardware brands from the admin panel without touching
code, per your requirement.

There is deliberately no "SimulatedScaleDriver" or "SimulatedPrinterDriver"
in this codebase. If hardware is not reachable, `connect()` must raise -
the caller is responsible for surfacing that as a real "station offline"
condition, not a fake reading.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


class DriverConnectionError(Exception):
    """Raised when the physical device cannot be reached at all
    (wrong IP, cable unplugged, bridge offline, etc.)."""


class DriverReadTimeoutError(Exception):
    """Raised when connected but no data arrived within the configured
    timeout (e.g. nothing placed on the scale, or scale not sending)."""


class DriverProtocolError(Exception):
    """Raised when data was received but could not be parsed / the device
    rejected the command (bad checksum, malformed frame, NAK, etc.)."""


@dataclass
class WeightReading:
    value: float
    unit: str
    raw: str


class ScaleDriver(ABC):
    """Implement this for every new scale connection method."""

    @abstractmethod
    def connect(self) -> None:
        """Open the physical connection. Must raise DriverConnectionError
        on failure. Must be safe to call again after disconnect()."""

    @abstractmethod
    def read_weight(self) -> WeightReading:
        """Return exactly one reading from the scale right now.
        Must raise DriverReadTimeoutError if nothing arrives in time."""

    @abstractmethod
    def disconnect(self) -> None:
        ...

    def is_connected(self) -> bool:
        return getattr(self, "_connected", False)


class PrinterDriver(ABC):
    """Implement this for every new printer protocol."""

    @abstractmethod
    def connect(self) -> None:
        """Must raise DriverConnectionError on failure."""

    @abstractmethod
    def print_fields(self, fields: dict) -> None:
        """`fields` is the fully-rendered dict of template values, e.g.
        {"BOX_ID": "BOX-2026-000001", "WEIGHT": "12.250 kg",
         "PRODUCT": "AB", "BATCH": "B240813",
         "DATE": "13/08/2026", "TIME": "14:30:25", "MACHINE_ID": "L1"}
        Must raise DriverConnectionError / DriverProtocolError on failure
        so the caller can mark print_status = 'failed' and retry."""

    @abstractmethod
    def disconnect(self) -> None:
        ...
