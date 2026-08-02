@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM  VDock Setup Installer
REM  Installs all dependencies and creates a desktop shortcut
REM  Run this once before using launch.bat
REM ============================================================

REM Resolve repo root (this file lives at the repo root)
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

title VDock Setup
cd /d "%ROOT%"

echo.
echo  ==========================================
echo    VDock  ^|  Setup Installer
echo  ==========================================
echo.

REM ── [1/7] Python ─────────────────────────────────────────────
echo  [1/7] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Python not found.
    echo         Install Python 3.9+ from https://www.python.org/downloads/
    echo         Make sure to tick "Add Python to PATH".
    echo.
    goto :fail
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [OK]    %%v

REM Warn if Python < 3.9
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set "PYMAJ=%%a"
    set "PYMIN=%%b"
)
if !PYMAJ! LSS 3 (
    echo  [ERROR] Python 3.9+ required. Found !PYVER!
    goto :fail
)
if !PYMAJ! EQU 3 if !PYMIN! LSS 9 (
    echo  [ERROR] Python 3.9+ required. Found !PYVER!
    goto :fail
)

REM ── [2/7] Node.js ────────────────────────────────────────────
echo  [2/7] Checking Node.js...
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%APPDATA%\npm;%PATH%"
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Node.js not found.
    echo         Install Node.js 18+ from https://nodejs.org/
    echo.
    goto :fail
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo  [OK]    Node.js %%v

call npm --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] npm not found. Reinstall Node.js from https://nodejs.org/
    goto :fail
)
for /f "tokens=*" %%v in ('npm --version 2^>^&1') do echo  [OK]    npm %%v

REM ── [3/7] Python virtual environment ─────────────────────────
echo  [3/7] Setting up Python virtual environment...
if not exist "%ROOT%\backend\venv\Scripts\activate.bat" (
    echo         Creating venv...
    python -m venv "%ROOT%\backend\venv"
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment
        goto :fail
    )
    echo  [OK]    Virtual environment created
) else (
    echo  [OK]    Virtual environment already exists
)

REM ── [4/7] Python dependencies ────────────────────────────────
echo  [4/7] Installing backend dependencies...
call "%ROOT%\backend\venv\Scripts\activate.bat"

REM Upgrade pip first to avoid build failures on newer Python versions
echo         Upgrading pip...
python -m pip install --upgrade pip --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  [WARN]  pip upgrade failed (non-fatal, continuing)
)

pip install -r "%ROOT%\backend\requirements.txt" --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo  [ERROR] pip install failed.
    echo         Check your internet connection, or try running setup.bat again.
    echo.
    goto :fail
)
echo  [OK]    Backend dependencies installed

REM ── [5/7] Frontend Node dependencies ─────────────────────────
echo  [5/7] Installing frontend dependencies...

if not exist "%ROOT%\frontend\node_modules" (
    echo         Running npm install in frontend\...
    pushd "%ROOT%\frontend"
    call npm install --no-fund --no-audit
    set "NPM_EXIT=!errorlevel!"
    popd
    if not exist "%ROOT%\frontend\node_modules" (
        echo  [ERROR] npm install failed (frontend^) exit=!NPM_EXIT!
        goto :fail
    )
    if not "!NPM_EXIT!"=="0" (
        echo  [WARN]  npm reported exit !NPM_EXIT! but node_modules exists; continuing
    )
    echo  [OK]    Frontend node_modules installed
) else (
    echo  [OK]    frontend\node_modules already present
)

REM ── [6/7] Electron Node dependencies ─────────────────────────
echo  [6/7] Installing Electron dependencies...

if not exist "%ROOT%\frontend\electron\node_modules" (
    echo         Running npm install in frontend\electron\...
    pushd "%ROOT%\frontend\electron"
    call npm install --no-fund --no-audit
    set "NPM_EXIT=!errorlevel!"
    popd
    if not exist "%ROOT%\frontend\electron\node_modules" (
        echo  [ERROR] npm install failed (electron^) exit=!NPM_EXIT!
        goto :fail
    )
    if not "!NPM_EXIT!"=="0" (
        echo  [WARN]  npm reported exit !NPM_EXIT! but node_modules exists; continuing
    )
    echo  [OK]    Electron node_modules installed
) else (
    echo  [OK]    frontend\electron\node_modules already present
)

REM ── [7/7] Data directories ───────────────────────────────────
echo  [7/7] Creating data directories...
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
    if not exist %%d mkdir %%d 2>nul
)
echo  [OK]    Data directories ready

REM ── Desktop shortcut ─────────────────────────────────────────
echo.
echo  Creating desktop shortcut...

set "LAUNCHER=%ROOT%\launch.bat"
set "ICON=%ROOT%\frontend\public\vdock-icon.ico"

REM Resolve real Desktop path (supports OneDrive-backed desktops)
for /f "usebackq delims=" %%d in (`powershell -NoProfile -NonInteractive -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP_DIR=%%d"
if not defined DESKTOP_DIR set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP_DIR%\VDock.lnk"

powershell -NoProfile -NonInteractive -Command ^
  "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%SHORTCUT%'); $sc.TargetPath = '%LAUNCHER%'; $sc.WorkingDirectory = '%ROOT%'; if (Test-Path '%ICON%') { $sc.IconLocation = '%ICON%' }; $sc.Description = 'VDock Virtual Stream Deck'; $sc.WindowStyle = 1; $sc.Save()" >nul 2>&1

if exist "%SHORTCUT%" (
    echo  [OK]    Desktop shortcut created
) else (
    echo  [WARN]  Could not create desktop shortcut ^(non-fatal^)
)

REM ── Done ─────────────────────────────────────────────────────
echo.
echo  ==========================================
echo    Setup complete!
echo  ==========================================
echo.
echo  To launch VDock:
echo    - Double-click VDock on your desktop, or
echo    - Run: launch.bat from this folder
echo.
echo  URLs (once running):
echo    Backend:   http://localhost:5000
echo    Frontend:  http://localhost:3000
echo.

set /p "LAUNCH=  Start VDock now? [Y/N]: "
if /i "!LAUNCH!"=="Y" (
    echo.
    echo  Starting VDock...
    start "" "%ROOT%\launch.bat"
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
