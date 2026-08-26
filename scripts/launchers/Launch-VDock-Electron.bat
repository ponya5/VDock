@echo off
REM VDock Electron Desktop Launcher
REM Starts backend, Vite dev server, then Electron

setlocal

echo ========================================
echo    VDock 2 Virtual Stream Deck (Electron)
echo ========================================
echo.

REM Resolve repo root (two levels up from scripts\launchers\)
set "ROOT=%~dp0..\.."
pushd "%ROOT%"
set "ROOT=%CD%"
popd

REM ── Check Node.js ────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause & exit /b 1
)
echo [OK] Node.js found

REM ── Check Python ─────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)
echo [OK] Python found

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

REM ── Install electron deps if needed ───────────────────────────
if not exist "%ROOT%\frontend\electron\node_modules" (
    echo [INFO] Installing Electron dependencies...
    pushd "%ROOT%\frontend\electron"
    call npm install
    popd
)
echo [OK] Dependencies ready
echo.

REM ── Start backend in a new window ─────────────────────────────
echo [1/3] Starting backend server...
start "VDock 2 Backend" /min cmd /c "cd /d "%ROOT%\backend" && call "%VENV%" && python app.py"

REM ── Start Vite dev server in a new window ─────────────────────
echo [2/3] Starting Vite dev server...
start "VDock 2 Frontend" /min cmd /c "cd /d "%ROOT%\frontend" && npm run dev"

REM ── Wait for servers to be ready ──────────────────────────────
echo Waiting for servers to start...
timeout /t 5 /nobreak >nul

REM ── Launch Electron ───────────────────────────────────────────
REM Backend is already running in its own window above — tell Electron's main
REM process not to spawn a second copy (it would just fail to bind the port).
set "VDOCK_SKIP_BACKEND_SPAWN=1"
echo [3/3] Launching Electron...
pushd "%ROOT%\frontend\electron"
call npx electron .
popd

echo.
echo VDock closed.
pause
