@echo off
REM Verify that both backend and frontend are running

echo ========================================
echo    VDock Server Verification
echo ========================================
echo.

echo Checking Backend Server (port 5000)...
python -c "import requests; r = requests.get('http://localhost:5000/api/health'); print('Backend Status:', r.json() if r.status_code == 200 else 'ERROR')" 2>nul
if errorlevel 1 (
    echo Backend: NOT RUNNING
) else (
    echo Backend: RUNNING
)

echo.
echo Checking Frontend Server (port 3000)...
python -c "import requests; r = requests.get('http://localhost:3000'); print('Frontend Status:', 'RUNNING' if r.status_code == 200 else 'ERROR')" 2>nul
if errorlevel 1 (
    echo Frontend: NOT RUNNING
) else (
    echo Frontend: RUNNING
)

echo.
echo ========================================
echo    Verification Complete
echo ========================================
echo.
pause
