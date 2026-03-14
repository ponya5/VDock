@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM  VDock Setup Installer
REM  Installs all dependencies and creates a desktop shortcut
REM ============================================================

REM Resolve repo root (this file lives at the repo root)
set "ROOT=%~dp0"
REM Strip trailing backslash
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

title VDock Setup

echo.
echo  ==========================================
echo    VDock  ^|  Setup Installer
echo  ==========================================
echo.

REM ── [1/6] Python ─────────────────────────────────────────────
echo  [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo         Install Python 3.9+ from https://www.python.org/downloads/
    echo         Make sure to tick "Add Python to PATH".
    goto :fail
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [OK]    %%v

REM ── [2/6] Node.js ────────────────────────────────────────────
echo  [2/6] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found.
    echo         Install Node.js from https://nodejs.org/
    goto :fail
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo  [OK]    Node.js %%v

REM ── [3/6] Python virtual environment ─────────────────────────
echo  [3/6] Setting up Python virtual environment...
if not exist "%ROOT%\backend\venv\Scripts\activate.bat" (
    python -m venv "%ROOT%\backend\venv"
    if errorlevel 1 ( echo  [ERROR] Failed to create venv & goto :fail )
    echo  [OK]    Virtual environment created
) else (
    echo  [OK]    Virtual environment already exists
)

REM ── [4/6] Python dependencies ────────────────────────────────
echo  [4/6] Installing backend dependencies...
call "%ROOT%\backend\venv\Scripts\activate.bat"
pip install -r "%ROOT%\backend\requirements.txt" --quiet --disable-pip-version-check
if errorlevel 1 ( echo  [ERROR] pip install failed & goto :fail )
echo  [OK]    Backend dependencies installed

REM ── [5/6] Node dependencies ──────────────────────────────────
echo  [5/6] Installing frontend dependencies...

if not exist "%ROOT%\frontend\node_modules" (
    pushd "%ROOT%\frontend"
    call npm install --silent
    if errorlevel 1 ( echo  [ERROR] npm install failed ^(frontend^) & popd & goto :fail )
    popd
    echo  [OK]    Frontend node_modules installed
) else (
    echo  [OK]    Frontend node_modules already present
)

if not exist "%ROOT%\frontend\electron\node_modules" (
    pushd "%ROOT%\frontend\electron"
    call npm install --silent
    if errorlevel 1 ( echo  [ERROR] npm install failed ^(electron^) & popd & goto :fail )
    popd
    echo  [OK]    Electron node_modules installed
) else (
    echo  [OK]    Electron node_modules already present
)

REM ── [6/6] Data directories ───────────────────────────────────
echo  [6/6] Creating data directories...
for %%d in (
    "%ROOT%\backend\data"
    "%ROOT%\backend\data\profiles"
    "%ROOT%\backend\data\uploads"
    "%ROOT%\backend\data\uploads\backgrounds"
    "%ROOT%\backend\data\uploads\button_backgrounds"
    "%ROOT%\backend\data\uploads\dashboard_backgrounds"
    "%ROOT%\backend\data\plugins"
    "%ROOT%\backend\data\themes"
) do (
    if not exist %%d mkdir %%d
)
echo  [OK]    Data directories ready

REM ── Desktop shortcut ─────────────────────────────────────────
echo.
echo  Creating desktop shortcut...

set "LAUNCHER=%ROOT%\scripts\launchers\Launch-VDock-Electron.bat"
set "ICON=%ROOT%\frontend\public\vdock-icon.ico"
set "SHORTCUT=%USERPROFILE%\Desktop\VDock.lnk"

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$sc = $ws.CreateShortcut('%SHORTCUT%');" ^
  "$sc.TargetPath = '%LAUNCHER%';" ^
  "$sc.WorkingDirectory = '%ROOT%';" ^
  "$sc.IconLocation = '%ICON%';" ^
  "$sc.Description = 'VDock Virtual Stream Deck';" ^
  "$sc.WindowStyle = 1;" ^
  "$sc.Save()"

if exist "%SHORTCUT%" (
    echo  [OK]    Desktop shortcut created: VDock.lnk
) else (
    echo  [WARN]  Could not create desktop shortcut ^(non-fatal^)
)

REM ── Done ─────────────────────────────────────────────────────
echo.
echo  ==========================================
echo    Setup complete!
echo  ==========================================
echo.
echo  Launch VDock:
echo    ^> Double-click the VDock icon on your desktop
echo    ^> Or run:  scripts\launchers\Launch-VDock-Electron.bat
echo.
echo  URLs (once running):
echo    Backend:   http://localhost:5000
echo    Frontend:  http://localhost:3000
echo.

set /p "LAUNCH=  Start VDock now? [Y/N]: "
if /i "!LAUNCH!"=="Y" (
    echo.
    echo  Starting VDock...
    start "" "%LAUNCHER%"
)

echo.
pause
exit /b 0

:fail
echo.
echo  ==========================================
echo    Setup failed. Fix the error above and
echo    run setup.bat again.
echo  ==========================================
echo.
pause
exit /b 1
