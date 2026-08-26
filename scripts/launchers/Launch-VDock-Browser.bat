@echo off
REM VDock 2 Browser Launcher
REM Double-click to start backend + frontend and open VDock in your browser

setlocal

echo ========================================
echo    VDock 2 Virtual Stream Deck (Browser)
echo ========================================
echo.

REM Resolve repo root (two levels up from scripts\launchers\)
set "ROOT=%~dp0..\.."
pushd "%ROOT%"
set "ROOT=%CD%"
popd

REM ── Check Python ─────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)
echo [OK] Python found

REM ── Check Node.js ────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause & exit /b 1
)
echo [OK] Node.js found

REM ── Check virtual environment ─────────────────────────────────
set "VENV=%ROOT%\backend\venv\Scripts\activate.bat"
if not exist "%VENV%" set "VENV=%ROOT%\.venv\Scripts\activate.bat"
if not exist "%VENV%" (
    echo [ERROR] Virtual environment not found. Run setup.bat first.
    pause & exit /b 1
)
echo [OK] Virtual environment found

REM ── Install frontend deps if needed ───────────────────────────
if not exist "%ROOT%\frontend\node_modules" (
    echo [INFO] Installing frontend dependencies...
    pushd "%ROOT%\frontend"
    call npm install
    popd
)
echo [OK] Dependencies ready
echo.

REM ── Start backend in a new window ─────────────────────────────
echo [1/2] Starting backend server...
start "VDock 2 Backend" /min cmd /c "cd /d "%ROOT%\backend" && call "%VENV%" && python app.py"

REM ── Start Vite dev server in a new window ─────────────────────
echo [2/2] Starting frontend dev server...
start "VDock 2 Frontend" /min cmd /c "cd /d "%ROOT%\frontend" && npm run dev"

REM ── Wait for servers to be ready ──────────────────────────────
echo Waiting for servers to start...
timeout /t 8 /nobreak >nul

echo Opening VDock in your default browser...
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:5000
echo.

start http://localhost:3000

echo.
echo ========================================
echo VDock 2 is running in your browser!
echo.
echo Backend and frontend run in minimized windows.
echo Close those windows to stop VDock.
echo ========================================
echo.
pause
