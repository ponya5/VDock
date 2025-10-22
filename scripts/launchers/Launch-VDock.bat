@echo off
REM VDock Desktop Launcher
REM Double-click this file to launch VDock

echo ========================================
echo    VDock Virtual Stream Deck
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo [OK] Python found
echo [OK] Node.js found
echo.

REM Check virtual environment
if not exist "backend\venv\Scripts\activate.bat" (
    echo [WARNING] Virtual environment not found!
    echo Run install.bat first to set up dependencies.
    pause
    exit /b 1
)

echo Starting Backend Server...
start "VDock Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python app.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "VDock Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 5 /nobreak >nul

echo Opening VDock in browser...
start http://localhost:3000

echo.
echo ========================================
echo    VDock Started!
echo ========================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Login: admin / admin
echo.
echo Press any key to close this window...
pause >nul

