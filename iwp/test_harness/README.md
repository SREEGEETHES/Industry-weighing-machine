# Test Harness — Mock Hardware for Testing

This folder contains **mock (simulated) hardware** for testing the Trade Kings system before real scale and printer hardware is available.

⚠️ **NOT NEEDED FOR PRODUCTION DEPLOYMENT**

---

## What's In Here

### 1. `mock_scale_server.py`
**Simulates a digital scale connected via TCP/IP**

- Listens on port 5005 (configurable)
- Sends weight readings in the format: `ST,GS,+012.180,kg`
- Simulates box placement: weight bounces around for 2 seconds, then settles
- Matches the exact protocol of real Avery Weigh-Tronix / Essae scales

**Usage:**
```powershell
python mock_scale_server.py 5005 12.180
#                           ^^^^  ^^^^^^
#                           port  target weight (kg)
```

**What it does:**
- Waits for app to connect
- Streams weight readings (with realistic noise)
- Settles at target weight after 2 seconds
- Simulates box removal (weight returns to ~0)

---

### 2. `mock_printer_server.py`
**Simulates an industrial inkjet printer connected via TCP/IP**

- Listens on port 9100 (configurable)
- Receives print commands in TCP Text protocol
- Displays what would be printed on the box
- Matches the protocol of generic TCP printers

**Usage:**
```powershell
python mock_printer_server.py 9100
#                             ^^^^
#                             port
```

**What it does:**
- Waits for app to connect
- Receives commands: `SELECT|1`, `SET|FIELD=VALUE`, `PRINT`
- Prints to console what would appear on physical box
- Sends ACK acknowledgments back to app

**Example output:**
```
============================================
 PRINTED ON BOX:
   BOX_ID      : BOX-2026-000042
   WEIGHT      : 12.180 kg
   DATE        : 14/08/2026
   TIME        : 08:36:39
   MACHINE_ID  : L1
============================================
```

---

### 3. `demo_batch.py`
**Batch testing script — triggers multiple weigh+print cycles**

- Calls the real API (not a mock)
- Simulates placing 15-20 boxes on the scale
- Useful for testing throughput, database, reports

**Usage:**
```powershell
python demo_batch.py 1      # 15-20 boxes on station 1
python demo_batch.py 1 50   # exactly 50 boxes on station 1
```

**What it does:**
- Loops through N boxes
- Calls `POST /api/stations/{id}/weigh` for each
- Displays results: Box ID, Weight, Print Status
- Adds realistic delays between boxes (0.3-0.7 seconds)

---

### 4. `START_DEMO.bat`
**Convenience launcher — starts all 3 services automatically**

- Opens 3 separate command windows
- Terminal 1: Backend API
- Terminal 2: Mock Scale
- Terminal 3: Mock Printer

**Usage:**
```powershell
# Just double-click the file, or:
START_DEMO.bat
```

---

## When To Use This

### ✅ Use test_harness for:
- **Demo mode** — Show system to management/clients
- **Development** — Test code changes without real hardware
- **Training** — Train operators/supervisors safely
- **Pre-deployment testing** — Verify system before factory installation

### ❌ Don't use test_harness for:
- **Production deployment** — Use real scale and printer
- **Real box weighing** — Mocks don't connect to actual hardware
- **Accuracy testing** — Mocks simulate fixed weights

---

## Production vs Demo

| Item | Demo Mode (test_harness) | Production Mode |
|------|--------------------------|-----------------|
| **Scale** | `mock_scale_server.py` (port 5005) | Real scale via WiFi bridge (e.g., 192.168.1.50:4001) |
| **Printer** | `mock_printer_server.py` (port 9100) | Real printer via Ethernet (e.g., 192.168.1.60:9100) |
| **Data** | Test database (can be deleted) | Real audit records (permanent) |
| **Labels** | Printed to console | Printed on physical boxes |

---

## Troubleshooting

### Mock scale/printer won't start

**Error:** `Address already in use`

**Fix:** Another program is using that port. Kill existing process or change port:
```powershell
# Change port number
python mock_scale_server.py 5006 12.180  # Changed 5005 → 5006
```

### "All boxes show failed status"

**Fix:** Start mock printer! The most common mistake is forgetting Terminal 3.
```powershell
python mock_printer_server.py 9100
```

### Mock scripts close immediately

**Fix:** Run from PowerShell/CMD terminal, not by double-clicking `.py` files.

---

## How Mocks Work

### Network Flow

```
Backend App
    ↓ (connects to 127.0.0.1:5005)
Mock Scale Server
    ↓ (sends weight data)
Backend App
    ↓ (connects to 127.0.0.1:9100)
Mock Printer Server
    ↓ (displays print data to console)
```

### Protocol Match

**Mock scale output:**
```
ST,GS,+012.180,kg
```

**Real scale output (Avery/Essae):**
```
ST,GS,+012.180,kg
```

→ **Identical!** App can't tell the difference.

---

## Files You Can Delete in Production

When deploying to factory, you can safely delete:
- This entire `test_harness/` folder
- All mock scripts
- Demo batch script

The backend code has no dependency on these files.

---

## Summary

**Purpose:** Safe testing environment before real hardware  
**When to use:** Development, demos, training  
**When to stop using:** Production deployment  
**Can be deleted:** Yes, not needed in factory  

**Start all 3 mocks before testing!** 🎯

---

For production hardware setup, see: `../PRODUCTION_SETUP.md`
