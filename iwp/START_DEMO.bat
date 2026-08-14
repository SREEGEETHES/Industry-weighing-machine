@echo off
echo ========================================
echo Trade Kings Demo Launcher
echo ========================================
echo.
echo This will start ALL 3 required services:
echo   1. Backend API
echo   2. Mock Scale
echo   3. Mock Printer
echo.
echo Press Ctrl+C in any window to stop
echo ========================================
echo.
pause

cd /d "%~dp0"

echo Starting Backend in new window...
start "Trade Kings Backend" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn app.main:app --reload"
timeout /t 3 >nul

echo Starting Mock Scale in new window...
start "Mock Scale" cmd /k "python test_harness\mock_scale_server.py 5005 12.180"
timeout /t 2 >nul

echo Starting Mock Printer in new window...
start "Mock Printer" cmd /k "python test_harness\mock_printer_server.py 9100"
timeout /t 2 >nul

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Admin Panel: http://localhost:8000/admin/
echo Login: admin / tradekings2026
echo.
echo To run 20-box demo:
echo   python test_harness\demo_batch.py 1 20
echo.
echo Press any key to exit (services will keep running)
pause >nul
