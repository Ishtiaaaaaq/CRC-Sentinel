@echo off
cd /d "%~dp0"
echo.
echo ================================================
echo   CRC Sentinel - USB Backup Verification Utility
echo ================================================
echo.
echo Starting Python backend on http://127.0.0.1:5000 ...
start "CRC Sentinel Backend" /min cmd /c "python app.py"
timeout /t 2 /nobreak >nul
start "CRC Sentinel Dashboard" http://127.0.0.1:5000

echo.
echo Dashboard opened in your browser.
echo Keep the backend window running while using the dashboard.
echo Close the backend window when finished.
pause
