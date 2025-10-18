@echo off
echo ========================================
echo    Restarting VDock Backend
echo ========================================
echo.

echo [1/2] Stopping existing backend processes...
taskkill /F /FI "WINDOWTITLE eq VDock Backend*" 2>nul
timeout /t 2 /nobreak >nul

echo [2/2] Starting backend server...
start "VDock Backend" cmd /c "cd /d %~dp0backend && call venv\Scripts\activate.bat && python app.py && pause"

echo.
echo ========================================
echo    Backend Restarted Successfully!
echo ========================================
echo.
echo Backend is running at: http://localhost:5000
echo.
pause
