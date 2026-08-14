# Trade Kings Weigh-Print-Audit System

**Fully automatic bridge between Scale → PC → Printer with complete audit trail**

Based on your factory photo, this system integrates into your final packing stage where filled boxes are weighed, sealed, and labeled before warehouse.

---

## 🎯 What This System Does

### Your Production Line Integration

```
┌──────────────────────────────────────────────────────────────────┐
│  PACKING LINE (your factory floor)                                │
│                                                                    │
│  1. Workers fill boxes with washing powder packets                │
│  2. Box placed on SCALE [P marker in photo]                       │
│  3. ──→ Weight auto-detected (system monitors continuously)       │
│  4. ──→ PC reads weight via WiFi bridge                           │
│  5. ──→ Box moves through SEALER (tape applied)                   │
│  6. ──→ PRINTER above conveyor prints label on moving box         │
│  7. ──→ Labeled box to WAREHOUSE                                  │
│                                                                    │
│  ✓ Zero button presses - fully automatic!                         │
│  ✓ Full audit trail in database                                   │
│  ✓ Tolerance check (warns if under/overweight)                    │
│  ✓ Failed print detection → supervisor reprints                   │
└──────────────────────────────────────────────────────────────────┘
```

### Worker Process (Zero Buttons!)

1. **Fill box** with washing powder packets
2. **Place on scale** (position marked "P")
3. **Walk away** — System auto-detects box, weighs, prints label
4. **Box moves to sealer** — Tape applied
5. **Label prints overhead** on moving box
6. **Box to warehouse** with printed ID

**No computer, no button, no screen at weighing station!**

---

## ⚡ Quick Start (Demo Mode)

### Easiest Way: Double-click `START_DEMO.bat`

This automatically opens 3 terminal windows with all services running.

**OR manually start 3 services:**

#### Terminal 1: Backend API
```powershell
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```
Wait for: `Uvicorn running on http://127.0.0.1:8000`

#### Terminal 2: Mock Scale
```powershell
python test_harness\mock_scale_server.py 5005 12.180
```
Wait for: `[mock-scale] Listening on 0.0.0.0:5005`

#### Terminal 3: Mock Printer ⚠️ **DON'T SKIP THIS!**
```powershell
python test_harness\mock_printer_server.py 9100
```
Wait for: `[mock-printer] Listening on 0.0.0.0:9100`

**Why all 3?** Backend talks to scale to get weight, then talks to printer to print label. If printer isn't running, print fails but weight is still saved (correct behavior for production safety).

---

## 🔧 Configure Station

1. Open browser: http://localhost:8000/admin/login.html
2. Login: `admin` / `tradekings2026`
3. Create Station:
   - Name: Line 1
   - Machine ID: L1
   - Weight Preset: (optional - for tolerance checking)
4. Configure Scale:
   - Connection Type: TCP
   - IP: 127.0.0.1
   - Port: 5005
5. Configure Printer:
   - Protocol: TCP Text
   - IP: 127.0.0.1
   - Port: 9100
6. Station will show: 🟢 **AUTO-MONITORING ACTIVE**

---

## 🎨 Features

### Automatic Weighing Mode

**How it works:**
- Background service continuously monitors scale (every 0.5 seconds)
- When weight goes from ~0 kg → >0.5 kg (box placed)
- Auto-triggers: Read stable weight → Generate Box ID → Print label → Save record
- No button press needed!

**Detection Timeline:**
```
0s:  Empty scale (0.02 kg) → Monitoring...
5s:  Box placed (weight rising: 8.45 kg)
6s:  Settling (12.18 kg)
7s:  Stable! → Auto-trigger weigh+print
8s:  BOX-2026-000042 created
9s:  Print command sent
10s: Label printed!
11s: Record saved
14s: Box removed → Ready for next box
```

### Dark Mode
- Click 🌙/☀️ icon (top-right, next to Logout)
- Toggles between light and dark themes
- Preference saved in browser

### Three User Interfaces

| Interface | URL | Login Required | Purpose |
|-----------|-----|----------------|---------|
| **Admin Panel** | http://localhost:8000/admin/ | Yes | Configure stations, view records, reports |
| **Operator UI** | http://localhost:8000/operator/ | No | View recent boxes (read-only) |
| **Box Lookup** | http://localhost:8000/lookup/ | No | Public verification (scan box ID) |

---

## 📋 Demo Testing

### Single Box Test
```powershell
# Start all 3 services first (see Quick Start above)
# System will auto-detect and process boxes
# Watch backend logs for: "Station 1: Box detected"
```

### Batch Test (20 boxes)
```powershell
python test_harness\demo_batch.py 1 20
```

**Expected output:**
```
[01/20] ✓ BOX-2026-000019 | 12.180 kg | printed ✅
[02/20] ✓ BOX-2026-000020 | 12.177 kg | printed ✅
...all 20 printed!
```

---

## 🚨 Common Issues

### "All boxes show failed status"

**Cause:** Mock printer server not running (Terminal 3)

**Fix:** 
1. Start mock printer: `python test_harness\mock_printer_server.py 9100`
2. Use `START_DEMO.bat` to launch all 3 services automatically

**Why this happens:** App saves weight data even if printer fails (correct production behavior - never lose audit data!)

### "Auto-monitoring disabled" shows on station card

**Cause:** Backend needs restart to start monitoring threads

**Fix:** 
1. Verify station has scale + printer configured
2. Verify station "Enabled" checkbox is checked
3. Restart backend

### Dark mode not switching

**Fix:** Refresh browser (Ctrl+F5)

### Scale shows "timeout" error

**Cause:** Weight not stabilizing

**Fix:**
1. Check if box is fully placed on scale platform
2. Verify scale is level and calibrated
3. Weight threshold: Box must be >0.5 kg to detect

---

## 📂 File Structure

```
iwp/
├── README.md                          ← You are here
├── PRODUCTION_SETUP.md                ← Hardware installation guide
├── DEPLOYMENT_CHECKLIST.md            ← Go-live checklist
├── PRINT_QUEUE_DESIGN.md              ← **CRITICAL** Queue timing info
├── DEPLOYMENT_OPTIONS.md              ← How to create .exe installer
│
├── backend/                           ← Server application
│   ├── app/
│   │   ├── drivers/                   ← Scale & printer drivers
│   │   ├── routers/                   ← API endpoints
│   │   ├── services/                  ← Business logic + auto-monitoring
│   │   └── main.py                    ← App entry point
│   ├── data/iwpas.db                  ← SQLite database
│   ├── requirements.txt               ← Python dependencies
│   └── scheduler.py                   ← Weekly report scheduler
│
├── frontend/                          ← Web interfaces
│   ├── admin/                         ← Admin panel (login required)
│   ├── operator/                      ← Operator UI (read-only)
│   └── lookup/                        ← Public box lookup
│
└── test_harness/                      ← Demo/testing tools (not for production)
    ├── mock_scale_server.py           ← Simulated scale
    ├── mock_printer_server.py         ← Simulated printer
    ├── demo_batch.py                  ← Batch testing script
    └── START_DEMO.bat                 ← Launch all services
```

---

## 🏭 Production Deployment

**See detailed guides:**

1. **PRODUCTION_SETUP.md** — Complete hardware setup, network config, Windows service
2. **DEPLOYMENT_CHECKLIST.md** — Pre-deployment tests, go-live procedure
3. **PRINT_QUEUE_DESIGN.md** — ⚠️ **CRITICAL** — Queue system for weigh→seal→print timing
4. **DEPLOYMENT_OPTIONS.md** — Creating .exe installer for customer delivery

**Key production differences:**
- Real scale IP (e.g., 192.168.1.50) instead of mock
- Real printer IP (e.g., 192.168.1.60) instead of mock
- Windows Service (auto-starts on boot) instead of manual terminals
- **Print queue system** to handle timing gap between weigh and print positions

---

## 🔐 Default Credentials

**Admin Panel Login:**
- Username: `admin`
- Password: `tradekings2026`

⚠️ **CHANGE THIS IN PRODUCTION!**

Edit: `backend/app/routers/auth.py` line 18

---

## 📊 What Gets Printed on Each Box

```
BOX-2026-000001
Weight: 12.180 kg
Date: 14/08/2026
Time: 08:36:39
Machine: L1
Product: AB
Batch: 20260814-A
```

---

## 🗄️ Database Location

**Audit records stored in:** `backend/data/iwpas.db`

**Backup:** Copy this file weekly to external drive

---

## 🆘 Support

For issues:
1. Check `PRODUCTION_SETUP.md` for hardware setup
2. Check `DEPLOYMENT_CHECKLIST.md` for common issues
3. Review backend logs (console output)
4. Check `PRINT_QUEUE_DESIGN.md` for timing/queue questions

---

## ✨ Key Features Summary

✅ **Fully automatic** — No button press needed  
✅ **Auto-detects weight** — Monitors scale continuously  
✅ **Unique Box IDs** — BOX-2026-000001, 000002, ...  
✅ **Full audit trail** — Every box recorded forever  
✅ **Tolerance checking** — Warns if under/overweight  
✅ **Failed print detection** — Box weighed but NOT printed → manual reprint  
✅ **Weekly Excel reports** — Auto-generates production summary  
✅ **Public box lookup** — Scan box ID to verify authenticity  
✅ **Multiple stations** — Support Line 1, Line 2, etc.  
✅ **Offline operation** — No internet required  
✅ **Dark mode** — Better for factory floor lighting  

---

## 📄 License

Proprietary software for Trade Kings internal use only.

---

**System Status:** ✅ Production-Ready with Automatic Weighing Mode
