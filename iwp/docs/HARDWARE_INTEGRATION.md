# Hardware Integration Guide

This is the checklist for going from "software works with nothing plugged
in" to "software works on the real line." Nothing here requires touching
the core service logic — only device config in the admin panel, and in one
case (Linx RCI), a handful of constants in one file.

## Scale

### If you go with a TCP/WiFi-bridge setup (recommended, matches "wireless")

1. Wire the scale indicator's RS232/RS485 output into a serial-to-WiFi (or
   serial-to-Ethernet) bridge. Any industrial device server works (e.g.
   USR-IOT USR-W610, Moxa NPort, or a cheap ESP32 running a serial-to-TCP
   passthrough sketch if you want to DIY it).
2. Note the bridge's IP address and TCP port (commonly 4001 or 8899 —
   check the bridge's own config page).
3. In the admin panel, open the station's **Edit Scale** modal, set
   Connection Type = TCP, enter that IP/port.
4. **Parse Pattern**: place a known weight on the scale and check what raw
   string the bridge sends (you can test with `nc <bridge_ip> <port>` or
   any TCP terminal tool). Most indicators send something like:
   - `ST,GS,+012.250,kg` (Avery Weigh-Tronix style)
   - `+  12.250 kg` (simpler indicators)
   The default pattern `([-+]?\d+\.?\d*)` grabs the first number in the
   string, which works for most formats. If your indicator sends multiple
   numbers (e.g. both gross and net weight) and the wrong one gets picked
   up, tighten the regex — tell me the exact raw string and I'll write the
   correct pattern.

### If you go with direct serial (software runs right next to the scale)

Same as above, but skip the bridge: set Connection Type = Serial, and
enter the OS's port name (`COM3` on Windows, `/dev/ttyUSB0` on Linux) and
the baud rate/parity/stopbits from the indicator's manual (commonly 9600,
8N1).

## Printer

### If your printer supports a plain TCP/Ethernet text message protocol

This is the easiest path and works with `printer_tcp_text.py` as-is for
many printers. You'll need three things from the printer's "Ethernet
Integration" or "Host Communications" manual:
- The field delimiter it expects in commands
- The line terminator (usually `\r\n`)
- The exact command keywords for "select message" / "set field" / "print"

Send me those three details (or the manual/PDF) and I'll adjust the three
constants at the top of `printer_tcp_text.py` to match exactly.

### If you go with Linx and its RCI protocol

`printer_linx_rci.py` implements the packet framing, checksum, and
socket handling for real — but three command byte values
(`CMD_SELECT_MESSAGE`, `CMD_UPDATE_FIELD`, `CMD_PRINT_TRIGGER`) and the
checksum algorithm need to be confirmed against your specific printer's
RCI Programmer's Manual (Linx ships a different one per printer
family/firmware version). This is not something I can guess safely —
sending the wrong byte codes to a live printer risks it misfiring or
jamming. Once you have the printer and its manual in hand, send me the
relevant page (the command code table) and I'll fill in the exact values
— it's a five-minute change once we have the real numbers.

Also set, per printer, in the admin panel:
- **RCI Message Slot** — which stored message template on the printer to
  trigger (set this up once on the printer itself with the field layout
  matching BOX_ID / WEIGHT / PRODUCT / BATCH / DATE / TIME / MACHINE_ID).
- **RCI Field Map** — JSON mapping our field names to the printer's field
  indices, e.g. `{"BOX_ID": 1, "WEIGHT": 2, "PRODUCT": 3, "BATCH": 4,
  "DATE": 5, "TIME": 6}`.

## Weight capture mode

Currently the system auto-captures once `STABILITY_SAMPLE_COUNT`
consecutive readings agree within `STABILITY_TOLERANCE_KG` (both
configurable in `.env`). If your chosen scale/workflow needs a manual
trigger instead (operator presses a button/foot pedal once the box is
settled), tell me and I'll add a "manual capture" mode as a per-station
toggle — the `ManualWeighRequest` API endpoint already exists and is ready
for this; it just needs a physical trigger (USB foot pedal acting as a
keypress, or a GPIO input if the deployment machine has one) wired to call
it.

## What to send me once hardware is chosen

1. Scale bridge/indicator IP + a sample of the raw string it sends for a
   known weight.
2. Printer brand/model + its Ethernet integration manual (PDF) or RCI
   Programmer's Manual, whichever applies.
3. Confirmation of which weight-capture mode you want (auto-stable vs.
   manual trigger).

With those three, I can lock the drivers to your exact hardware and we can
run a real end-to-end test on the factory floor.
