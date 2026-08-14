# Print Queue Design - Critical for Production

## The Problem You Identified

**Scenario:**
```
Box A: Weighed at 0s → 12.180 kg
Box B: Weighed at 5s → 12.150 kg (while Box A still moving to printer)

If printer receives Box B's data while Box A is physically under the print head,
Box A gets printed with Box B's weight! 🚨 CRITICAL FLAW
```

**Your workflow timing (from photo):**
1. Scale position (P marker) → Weigh
2. ~2-3 seconds → Sealer station
3. ~2-3 seconds → Printer overhead
4. **Total: ~5 seconds from scale to printer**

**Problem:** Workers can place boxes every 3-5 seconds, but print position is 5 seconds away!

---

## Solution 1: Printer with Built-In Product Detector (RECOMMENDED)

### How Industrial Printers Handle This

Most continuous inkjet printers (Linx, Domino, Videojet, Matthews) have:

1. **Photo-eye sensor** mounted on printer
2. **Detects box presence** under print head
3. **Internal print queue** (FIFO - First In, First Out)
4. **Prints when sensor triggers**

### Modified System Flow

```
┌─────────────────────────────────────────────────────────┐
│ SCALE STATION (Position P)                              │
├─────────────────────────────────────────────────────────┤
│ 0s: Box A placed                                        │
│ 2s: Weight stable = 12.180 kg                           │
│ 3s: System sends to printer queue:                      │
│     {BOX-2026-000042, 12.180 kg, L1, 14/08/2026}       │
│     Status: "queued_for_print"                          │
│ 4s: Box A moves to sealer                               │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ SEALER STATION                                          │
├─────────────────────────────────────────────────────────┤
│ 5s: Box A being sealed with tape                        │
│                                                          │
│ Meanwhile at scale:                                     │
│ 5s: Box B placed                                        │
│ 7s: Weight stable = 12.150 kg                           │
│ 8s: System sends to printer queue:                      │
│     {BOX-2026-000043, 12.150 kg, L1, 14/08/2026}       │
│     Status: "queued_for_print"                          │
│                                                          │
│ Queue now: [Box A, Box B] ← FIFO order maintained      │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ PRINTER STATION (Overhead)                              │
├─────────────────────────────────────────────────────────┤
│ 8s: Box A arrives under printer                         │
│ 9s: Printer photo-eye detects box                       │
│10s: Printer pulls FIRST job from queue (Box A)          │
│11s: Prints on Box A: BOX-2026-000042, 12.180 kg        │
│12s: Database updated: Box A status = "printed"          │
│                                                          │
│15s: Box B arrives under printer                         │
│16s: Printer photo-eye detects box                       │
│17s: Printer pulls NEXT job from queue (Box B)           │
│18s: Prints on Box B: BOX-2026-000043, 12.150 kg        │
│19s: Database updated: Box B status = "printed"          │
└─────────────────────────────────────────────────────────┘
```

**Key:** Printer's sensor ensures correct box gets correct data!

---

## Solution 2: Software-Only Queue (Fallback)

If printer **doesn't have** product detector:

### Approach A: Conveyor Speed Calculation

```python
# Calculate delay from scale to printer
SCALE_TO_PRINTER_DISTANCE = 3.0  # meters (measure your line)
CONVEYOR_SPEED = 0.5  # meters/second (measure with stopwatch)
PRINT_DELAY = SCALE_TO_PRINTER_DISTANCE / CONVEYOR_SPEED  # = 6 seconds

# Modified flow:
1. Box A weighed → 12.180 kg
2. Save to queue with timestamp
3. Start 6-second timer
4. After 6 seconds → Send print command
5. Pray box is aligned! 🤞
```

**Problem:** Conveyor speed varies (jam, power fluctuation) = misalignment

### Approach B: External Photo-Eye + PLC

Add a photo-eye sensor at printer position, wire it to a PLC (Programmable Logic Controller), PLC triggers print:

```
Scale → Weighs → Sends to queue
                      ↓
Photo-eye at printer detects box → Triggers PLC
                      ↓
PLC tells system: "Print now!"
                      ↓
System pulls next job from queue → Prints
```

**Cost:** ~$500 for sensor + PLC + wiring

---

## Printer Capabilities

### Can Your Printer Handle Queuing?

**Check your printer manual for:**

1. **Product detector input** (photo-eye)
   - Most have: "External trigger" or "Print-on-demand" mode
   - Wiring: Sensor → Printer's trigger input

2. **Print buffer/queue**
   - Industrial printers hold 10-50 messages in memory
   - Prints them in FIFO order when triggered

3. **Message selection**
   - Can printer receive "message ID" from our system?
   - Example: Linx RCI protocol supports `SELECT|1` (message slot 1)

### Common Printer Protocols

| Brand | Protocol | Queue Support | Trigger Input |
|-------|----------|---------------|---------------|
| Linx | RCI (binary) | ✅ Yes | ✅ Yes |
| Domino | i-Tech | ✅ Yes | ✅ Yes |
| Videojet | Ethernet/IP | ✅ Yes | ✅ Yes |
| Matthews | TCP Text | ⚠️ Limited | ✅ Yes (external) |

**Your current setup:** TCP Text (generic) — printer receives full message each time

---

## Implementation Options

### Option 1: Printer Manages Queue (Best)

**Requirements:**
- Printer with photo-eye sensor (most have it)
- Printer supports message slots or queue

**System changes:**
1. Scale sends message to printer immediately
2. Printer stores in internal queue
3. Printer's sensor triggers print when box aligned
4. **No software changes needed!**

**How to configure:**
1. Check printer manual: "External trigger mode"
2. Connect photo-eye to printer's trigger input
3. Set printer to "Print-on-trigger" mode
4. Done!

### Option 2: Our System Manages Queue (Software)

**Requirements:**
- Database tracks print queue
- Photo-eye sensor wired to PC (via Arduino/PLC)
- Software monitors sensor

**System changes:**
- Add `print_queue` table
- Add sensor monitoring thread
- Send print command when sensor triggers

**Trade-off:** More complex, but works with any printer

### Option 3: Hybrid (Current + Delay)

**Quick fix for demo:**
```python
# In auto_weighing_service.py:
PRINT_DELAY_SECONDS = 5  # Time from scale to printer

# After weighing:
threading.Timer(PRINT_DELAY_SECONDS, send_to_printer, args=[box_data]).start()
```

**Limitation:** Works only if boxes placed at consistent intervals

---

## Recommendation for Trade Kings

### Phase 1: Current Demo (No Changes)
- Mock printer accepts commands immediately
- Good for testing weight detection, database, reports

### Phase 2: Production Deployment

**Check your actual printer:**
1. Does it have a product detector (photo-eye)?
2. Does it support external trigger?

**If YES (90% of industrial printers):**
- Connect photo-eye sensor
- Configure printer for trigger mode
- **No software changes needed!**
- Printer handles queue automatically

**If NO:**
- We add software queue + sensor monitoring
- Estimate: 2-3 days additional development

---

## Testing the Queue

### Test Scenario

```
Time | Action                    | Queue State
-----|---------------------------|---------------------------
0s   | Box A weighed 12.180      | [Box A]
3s   | Box B weighed 12.150      | [Box A, Box B]
5s   | Box A under printer       | [Box A, Box B]
5s   | Sensor triggers           | → Print Box A
6s   | Print complete            | [Box B] → Status: printed
8s   | Box B under printer       | [Box B]
8s   | Sensor triggers           | → Print Box B
9s   | Print complete            | [] → Status: printed
10s  | Box C weighed 12.200      | [Box C]
```

**Verification:**
- Box A has weight 12.180 ✅
- Box B has weight 12.150 ✅
- Box C has weight 12.200 ✅
- No mix-ups!

---

## Next Steps

1. **Check your printer model** — Look at manual or control panel
2. **Look for "External trigger" or "Product detector" input**
3. **Take photo of printer's wiring terminals** — I can help identify trigger input
4. **Measure timing:**
   - Place box on scale
   - Time how long until it reaches printer
   - This is your print delay

---

## Summary

**Your concern:** ✅ Valid and critical!  
**Solution exists:** ✅ Yes — printer queuing  
**Common in industry:** ✅ Yes — standard feature  
**Software ready:** ✅ Queue system can be added  
**Best approach:** Check if your printer already has trigger input (likely yes!)

**Without queue:** Boxes get wrong labels 🚨  
**With queue:** Perfect label every time ✅

---

**Status:** Design documented, awaiting printer specifications to implement
