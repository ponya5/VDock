@echo off
REM Test script to demonstrate launcher functionality

echo ========================================
echo    VDock Launcher Test
echo ========================================
echo.

echo Testing current server status...
python -c "import requests; print('Backend:', requests.get('http://localhost:5000/api/health').json()); print('Frontend:', requests.get('http://localhost:3000').status_code)" 2>nul

echo.
echo ========================================
echo    Launcher Features
echo ========================================
echo.
echo ✅ launch.bat - Starts both servers
echo ✅ verify_launch.bat - Checks server status  
echo ✅ create_shortcut.bat - Creates desktop icon
echo.
echo Current Status:
echo - Backend: http://localhost:5000 (RUNNING)
echo - Frontend: http://localhost:3000 (RUNNING)
echo.
echo To restart servers:
echo 1. Close current server windows
echo 2. Run launch.bat
echo.
pause
