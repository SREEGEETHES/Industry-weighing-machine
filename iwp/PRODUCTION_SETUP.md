# Trade Kings Weigh-Print-Audit System
## Production Setup Guide

This guide will walk you through setting up the system on your production line.

---

## Hardware Requirements

### 1. PC / Industrial Computer
- **OS:** Windows 10/11 (64-bit)
- **RAM:** 4GB minimum
- **Storage:** 20GB free space
- **Network:** Ethernet port (for scale/printer connection)
- **Location:** Near the weighing station, protected from dust/moisture

### 2. Digital Scale
- Must support one of these protocols:
  - **RS232/RS485** (serial) with WiFi-to-serial bridge
  - **TCP/IP** network output
- Your scale must output weight readings as text (most industrial scales do)
- Example compatible brands: Avery Weigh-Tronix, Mettler Toledo, Essae, etc.

### 3. Industrial Inkjet Printer
- Must support TCP/IP network connection
- Must support text-based command protocol or Linx RCI protocol
- Example compatible brands: Linx, Domino, Matthews, Videojet
- **Placement:** Mounted after the sealing station (see your factory photo)

### 4. Network Setup
- All devices (PC, Scale, Printer) connected to same **local network**
- Use static IP addresses (not DHCP) to prevent IP changes
- Ethernet cable: Cat5e or better

---

## Step 1: Install Python

1. Download Python 3.11 or 3.12 from https://www.python.org/downloads/windows/
2. Run installer
3. ✅ **Check "Add Python to PATH"** (critical!)
4. Click "Install Now"
5. Verify installation:
   ```powershell
   python --version
   ```
   Should show: `Python 3.11.x` or `Python 3.12.x`

---

## Step 2: Install the Application

1. Copy the `iwp` folder to: `C:\TradeKings\iwp`

2. Open PowerShell as Administrator

3. Navigate to the app folder:
   ```powershell
   cd C:\TradeKings\iwp\backend
   ```

4. Create Python virtual environment:
   ```powershell
   python -m venv venv
   ```

5. Activate the environment:
   ```powershell
   venv\Scripts\activate
   ```

6. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

---

## Step 3: Configure Scale Connection

### Option A: TCP/IP Scale (most common with WiFi bridges)

1. Connect scale to network via WiFi bridge or Ethernet
2. Note the scale's IP address (e.g., `192.168.1.50`)
3. Note the port (usually `4001` or specified in bridge manual)

### Option B: Serial Scale (direct RS232 connection)

1. Connect scale to PC via RS232/USB-Serial cable
2. Note the COM port (e.g., `COM3`)
3. Check Device Manager → Ports to confirm

### Test Scale Connection

Run the backend server:
```powershell
cd C:\TradeKings\iwp\backend
venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open browser: http://localhost:8000/docs (API documentation)

---

## Step 4: Configure Printer Connection

1. Connect printer to network via Ethernet
2. Set printer to static IP (e.g., `192.168.1.60`)
3. Note the port (usually `9100` for raw TCP)
4. Test printer by sending test print from its control panel

---

## Step 5: Configure Station in Admin Panel

1. Open browser: http://localhost:8000
2. Login with default credentials:
   - **Username:** `admin`
   - **Password:** `tradekings2026` *(change this after first login!)*

3. Click **"+ New Station"**
   - **Station Name:** Line 1
   - **Machine ID:** L1 (this prints on the box)
   - **Weight Preset:** (optional - set if you want tolerance checking)

4. Click **"Scale"** button:
   - **Connection Type:** TCP (if using WiFi bridge) or Serial (if direct cable)
   - **IP Address:** Your scale's IP (e.g., `192.168.1.50`)
   - **Port:** Your scale's port (e.g., `4001`)
   - **Parse Pattern:** `([-+]?\d+\.?\d*)` (default, works for most scales)
   - **Unit:** kg
   - Save

5. Click **"Printer"** button:
   - **Protocol:** TCP Text (for generic printers)
   - **IP Address:** Your printer's IP (e.g., `192.168.1.60`)
   - **Port:** `9100` (standard)
   - Save

---

## Step 6: Test the System

### Manual Test

1. In Admin Panel, click **"Weigh & Print"** on your station
2. Place a box on the scale
3. Wait for weight to stabilize (~2 seconds)
4. App reads weight → sends to printer → saves record
5. Check if box label printed correctly
6. Check **"Box Records"** tab to see the audit entry

### Operator UI Test

1. Open in browser: http://localhost:8000/operator/index.html?station=1
2. Bookmark this page on operator's PC
3. Operator only sees big "Weigh & Print" button
4. No admin settings visible

---

## Step 7: Set Up as Windows Service (Auto-Start)

Create a batch file: `C:\TradeKings\start_backend.bat`

```batch
@echo off
cd C:\TradeKings\iwp\backend
call venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Use Task Scheduler to run at startup:

1. Open Task Scheduler
2. Create Task → General tab:
   - Name: Trade Kings Backend
   - ✅ Run whether user is logged on or not
   - ✅ Run with highest privileges
3. Triggers tab → New:
   - Begin: At startup
4. Actions tab → New:
   - Action: Start a program
   - Program: `C:\TradeKings\start_backend.bat`
5. Save

Restart PC and verify backend starts automatically.

---

## Step 8: Network Access (Optional)

If you want operators on **other PCs** to access the system:

1. Find the main PC's IP address:
   ```powershell
   ipconfig
   ```
   Look for IPv4 Address (e.g., `192.168.1.100`)

2. On operator PCs, open browser:
   - Admin: `http://192.168.1.100:8000/admin/`
   - Operator: `http://192.168.1.100:8000/operator/index.html?station=1`

3. Add Windows Firewall rule:
   ```powershell
   netsh advfirewall firewall add rule name="Trade Kings" dir=in action=allow protocol=TCP localport=8000
   ```

---

## Step 9: Change Default Password

1. Open: `C:\TradeKings\iwp\backend\app\routers\auth.py`
2. Change line 18:
   ```python
   "admin": "tradekings2026",  # Change this!
   ```
   To your secure password:
   ```python
   "admin": "YourSecurePassword123!",
   ```
3. Restart backend service

---

## Troubleshooting

### Scale not connecting
- Check IP/port in scale bridge web interface
- Try `ping 192.168.1.50` (your scale IP) - should reply
- Check firewall isn't blocking the port
- Try telnet test: `telnet 192.168.1.50 4001`

### Printer not printing
- Check printer IP/port in printer's control panel
- Try `ping 192.168.1.60` (your printer IP)
- Send test print from printer's control panel first
- Check printer has ink/ribbon and no error lights

### "Failed" print status
- Printer offline or unreachable at print time
- Use "Reprint" button in Box Records tab to retry
- Physical box was weighed but NOT printed - do not ship!

### Weight reads as 0 or wrong value
- Check "Parse Pattern" in scale settings
- Look at raw scale output in backend logs
- Contact support with scale model number

---

## Daily Operation

### Operator Workflow
1. Open Operator UI: http://localhost:8000/operator/
2. Place filled box on scale
3. Click "Weigh & Print"
4. Wait for green "PRINTED" status
5. Remove box, seal, send to warehouse

### Supervisor Workflow
1. Open Admin Panel: http://localhost:8000/admin/
2. Check "Box Records" tab for today's production
3. Export weekly report from "Reports" tab
4. Review any "failed" print status boxes

---

## Support & Maintenance

- **Database location:** `C:\TradeKings\iwp\backend\data\iwpas.db`
- **Backup:** Copy entire `iwp` folder weekly
- **Logs:** Backend console shows all weigh/print events
- **Updates:** Contact developer for new versions

---

**System Ready!** 🎉
