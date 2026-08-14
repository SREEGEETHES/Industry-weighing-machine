# Trade Kings System — Deployment Checklist

Use this checklist before going live in production.

---

## ✅ Pre-Deployment Checks

### Hardware Setup
- [ ] PC installed near weighing station
- [ ] PC has stable power supply (UPS recommended)
- [ ] Scale connected to network (WiFi bridge or Ethernet)
- [ ] Printer connected to network (Ethernet)
- [ ] All devices on same network/subnet
- [ ] Static IP addresses assigned (not DHCP)
- [ ] Network cables secured and labeled

### Software Installation
- [ ] Python 3.11+ installed with PATH enabled
- [ ] Virtual environment created (`venv` folder exists)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Backend starts without errors
- [ ] Admin panel loads in browser (http://localhost:8000/admin/)
- [ ] Login page shows correctly
- [ ] Default password changed in `auth.py`

### Scale Configuration
- [ ] Scale IP address verified (ping test passes)
- [ ] Scale port confirmed from device manual
- [ ] Scale device created in Admin Panel
- [ ] Parse pattern tested (weight reads correctly)
- [ ] Unit set to "kg" (or your preferred unit)
- [ ] Stability detection working (2-second settle time)

### Printer Configuration
- [ ] Printer IP address verified (ping test passes)
- [ ] Printer port confirmed (usually 9100)
- [ ] Printer device created in Admin Panel
- [ ] Protocol set correctly (TCP Text or Linx RCI)
- [ ] Test print successful from Admin Panel

### Station Configuration
- [ ] Station created with correct name
- [ ] Machine ID set (this will print on every box)
- [ ] Scale device linked to station
- [ ] Printer device linked to station
- [ ] Weight preset configured (if using tolerance checking)
- [ ] Station shows green status dots (scale OK, printer OK)

---

## ✅ Testing Phase

### Manual Test (1 Box)
- [ ] Backend running
- [ ] Place test box on scale
- [ ] Click "Weigh & Print" in Admin Panel
- [ ] Weight stabilizes within 2 seconds
- [ ] Weight reading is accurate (verify with scale display)
- [ ] Printer prints label on test box
- [ ] Label shows: Box ID, Weight, Date, Time, Machine ID
- [ ] Box record appears in "Box Records" tab
- [ ] Print status shows "printed" (not "failed")
- [ ] Box ID increments correctly (BOX-2026-000001, 000002, etc.)

### Batch Test (10 Boxes)
- [ ] Run 10 consecutive boxes through the system
- [ ] All 10 print successfully
- [ ] No "failed" print status
- [ ] All 10 appear in Box Records
- [ ] Weights vary realistically (not all identical)
- [ ] No scale timeout errors
- [ ] No printer connection errors

### Operator UI Test
- [ ] Open: http://localhost:8000/operator/index.html?station=1
- [ ] Operator can weigh without accessing admin settings
- [ ] "Weigh & Print" button works
- [ ] Recent boxes list updates automatically
- [ ] UI is simple and clear for factory floor use

### Error Scenario Tests
- [ ] **Scale unplugged:** App shows "Device connection error"
- [ ] **Printer unplugged:** App shows "failed" print status, but box record still saved
- [ ] **Wrong IP address:** App shows timeout error
- [ ] **No box on scale:** App waits for stable weight (timeout after 15s)

---

## ✅ Production Deployment

### Windows Service Setup
- [ ] Batch file created: `C:\TradeKings\start_backend.bat`
- [ ] Task Scheduler configured to run at startup
- [ ] PC restarted to test auto-start
- [ ] Backend starts automatically after reboot
- [ ] Service runs without logged-in user

### Network Access (if using multiple PCs)
- [ ] Main PC's IP address documented
- [ ] Firewall rule added for port 8000
- [ ] Operator PCs can access Operator UI via network
- [ ] Admin PCs can access Admin Panel via network
- [ ] Bookmarks created on operator PCs

### Security
- [ ] Default password changed from "tradekings2026"
- [ ] Admin credentials shared only with supervisors
- [ ] Operator PCs only have Operator UI bookmark (not admin)
- [ ] Physical PC access restricted (locked room/cabinet)

### Backup & Recovery
- [ ] Database backed up: `backend\data\iwpas.db`
- [ ] Backup location documented: _______________
- [ ] Backup schedule set (weekly recommended)
- [ ] Recovery procedure documented
- [ ] Test restore performed successfully

---

## ✅ Training

### Operator Training
- [ ] Show how to open Operator UI
- [ ] Demonstrate "Weigh & Print" workflow
- [ ] Explain "printed" vs "failed" status
- [ ] Show recent boxes list
- [ ] Explain what to do if status shows "failed" (call supervisor)
- [ ] Practice with 5 test boxes per operator

### Supervisor Training
- [ ] Show how to log in to Admin Panel
- [ ] Navigate Stations, Presets, Box Records tabs
- [ ] Demonstrate how to "Reprint" a failed box
- [ ] Show weekly report generation
- [ ] Explain how to check if scale/printer is online (green dots)
- [ ] Show how to add/edit stations
- [ ] Demonstrate backup procedure

---

## ✅ Go-Live Day

### Morning Setup
- [ ] PC powered on and backend running
- [ ] Scale powered on and displaying zero
- [ ] Printer powered on with no error lights
- [ ] Test 1 box before production starts
- [ ] Operator UI loaded on operator's PC
- [ ] Supervisor has Admin Panel open for monitoring

### During Production
- [ ] Monitor first 10 boxes closely
- [ ] Check Box Records tab every hour
- [ ] Watch for any "failed" print status
- [ ] Supervisor available for first shift
- [ ] Document any issues encountered

### End of Day
- [ ] Review Box Records for the day
- [ ] Check for any failed prints (reprint before shipping)
- [ ] Export daily report
- [ ] Note total boxes processed: _______
- [ ] Note any issues: ___________________

---

## ✅ Week 1 Monitoring

- [ ] Day 1: No critical issues
- [ ] Day 2: Operators comfortable with workflow
- [ ] Day 3: No failed prints or all reprinted
- [ ] Day 4: Scale/printer connection stable
- [ ] Day 5: Weekly report generated successfully
- [ ] End of week review meeting held
- [ ] Issues log reviewed and addressed

---

## 🔧 Common Issues & Fixes

| Issue | Check | Fix |
|-------|-------|-----|
| "Connection error" | Scale/printer IP reachable? | `ping` the device, check cables |
| "Timeout" | Weight stabilizing? | Wait longer, check scale calibration |
| "Failed" print | Printer online? | Check printer status, use Reprint button |
| Label not printing | IP/port correct? | Verify in printer control panel |
| Wrong weight | Parse pattern correct? | Check scale output format |
| Backend won't start | Python installed? | Check `python --version` |
| Can't login | Password changed? | Check `auth.py` file |

---

## 📞 Emergency Contacts

- **System Administrator:** _______________
- **Scale Vendor Support:** _______________
- **Printer Vendor Support:** _______________
- **IT Department:** _______________
- **Developer Support:** _______________

---

## ✅ Sign-Off

**System deployed by:** ___________________ **Date:** __________

**Tested by:** ___________________ **Date:** __________

**Approved by:** ___________________ **Date:** __________

---

**Production Status:** ✅ Ready to Go Live
