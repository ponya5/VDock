@echo off
REM VDock Browser Launcher
REM Double-click this file to launch VDock in your default browser

echo ========================================
echo    VDock Virtual Stream Deck (Browser)
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Navigate to backend directory
cd /d "%~dp0..\..\backend"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo [OK] Virtual environment found
echo.

echo Starting VDock backend server...
echo.

REM Start backend server in background
start /B cmd /c "venv\Scripts\activate.bat && python app.py"

REM Wait for server to start
timeout /t 3 /nobreak >nul

echo Opening VDock in your default browser...
echo.
echo VDock will be available at: http://localhost:5000
echo.

REM Open in default browser
start http://localhost:5000

echo.
echo ========================================
echo VDock is running in your browser!
echo Close this window to stop the backend.
echo ========================================
echo.
echo Press Ctrl+C to stop the server...

REM Keep the backend running
cmd /c "venv\Scripts\activate.bat && python app.py"
