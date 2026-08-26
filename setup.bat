@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM  VDock Setup — single installer for end users
REM  Run once after cloning. Use the menu to pick what you need.
REM ============================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

if /i "%~1"=="--full" (
    call :install_dependencies
    if errorlevel 1 exit /b 1
    call :create_desktop_shortcut
    goto :setup_complete_cli
)
if /i "%~1"=="--deps" (
    call :install_dependencies
    exit /b %errorlevel%
)
if /i "%~1"=="--shortcut" (
    call :create_desktop_shortcut
    exit /b 0
)
if /i "%~1"=="--launch" (
    call :launch_vdock
    exit /b %errorlevel%
)

:main_menu
cls
title VDock Setup
echo.
echo   ========================================================
echo     VDock Setup
echo   ========================================================
echo.
echo     [1] Full setup (recommended)
echo         Install Python + Node deps, Electron, desktop shortcut
echo.
echo     [2] Install dependencies only
echo         Skip desktop shortcut creation
echo.
echo     [3] Create desktop shortcut only
echo         Adds a VDock icon to your Desktop
echo.
echo     [4] Launch VDock now
echo.
echo     [5] Exit
echo.
set "MENU_CHOICE="
set /p "MENU_CHOICE=  Choose an option [1-5]: "

if "%MENU_CHOICE%"=="1" goto :run_full
if "%MENU_CHOICE%"=="2" goto :run_deps
if "%MENU_CHOICE%"=="3" goto :run_shortcut
if "%MENU_CHOICE%"=="4" goto :run_launch
if "%MENU_CHOICE%"=="5" goto :exit_ok
echo.
echo   Invalid choice. Press any key to try again...
pause >nul
goto :main_menu

:run_full
call :install_dependencies
if errorlevel 1 goto :fail
call :create_desktop_shortcut
goto :setup_complete

:run_deps
call :install_dependencies
if errorlevel 1 goto :fail
echo.
echo   Dependencies installed. Run setup again to create a shortcut.
goto :pause_and_menu

:run_shortcut
call :create_desktop_shortcut
goto :pause_and_menu

:run_launch
call :launch_vdock
goto :pause_and_menu

:install_dependencies
echo.
echo   ==========================================
echo     Installing VDock dependencies
echo   ==========================================
echo.

echo   [1/7] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [ERROR] Python not found.
    echo           Install Python 3.9+ from https://www.python.org/downloads/
    echo           Tick "Add Python to PATH" during installation.
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   [OK]    %%v

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set "PYMAJ=%%a"
    set "PYMIN=%%b"
)
if !PYMAJ! LSS 3 exit /b 1
if !PYMAJ! EQU 3 if !PYMIN! LSS 9 (
    echo   [ERROR] Python 3.9+ required. Found !PYVER!
    exit /b 1
)

echo   [2/7] Checking Node.js...
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%APPDATA%\npm;%PATH%"
node --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Node.js not found. Install Node.js 18+ from https://nodejs.org/
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo   [OK]    Node.js %%v
for /f "tokens=*" %%v in ('npm --version 2^>^&1') do echo   [OK]    npm %%v

echo   [3/7] Python virtual environment...
if not exist "%ROOT%\backend\venv\Scripts\activate.bat" (
    echo           Creating venv...
    python -m venv "%ROOT%\backend\venv"
    if errorlevel 1 exit /b 1
    echo   [OK]    Virtual environment created
) else (
    echo   [OK]    Virtual environment already exists
)

echo   [4/7] Backend dependencies...
call "%ROOT%\backend\venv\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet --disable-pip-version-check >nul 2>&1
pip install -r "%ROOT%\backend\requirements.txt" --quiet --disable-pip-version-check
if errorlevel 1 (
    echo   [ERROR] pip install failed. Check your connection and try again.
    exit /b 1
)
echo   [OK]    Backend dependencies installed

echo   [5/7] Frontend dependencies...
if not exist "%ROOT%\frontend\node_modules" (
    pushd "%ROOT%\frontend"
    call npm install --no-fund --no-audit
    if not exist "%ROOT%\frontend\node_modules" (
        popd
        exit /b 1
    )
    popd
    echo   [OK]    Frontend node_modules installed
) else (
    echo   [OK]    frontend\node_modules already present
)

echo   [6/7] Electron dependencies...
if not exist "%ROOT%\frontend\electron\node_modules" (
    pushd "%ROOT%\frontend\electron"
    call npm install --no-fund --no-audit
    if not exist "%ROOT%\frontend\electron\node_modules" (
        popd
        exit /b 1
    )
    popd
    echo   [OK]    Electron node_modules installed
) else (
    echo   [OK]    frontend\electron\node_modules already present
)

echo   [7/7] Data directories...
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
echo   [OK]    Data directories ready
exit /b 0

:create_desktop_shortcut
echo.
echo   Creating desktop shortcut...
set "LAUNCHER=%ROOT%\launch.bat"
set "ICON=%ROOT%\frontend\public\vdock-icon.ico"
for /f "usebackq delims=" %%d in (`powershell -NoProfile -NonInteractive -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP_DIR=%%d"
if not defined DESKTOP_DIR set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP_DIR%\VDock.lnk"

powershell -NoProfile -NonInteractive -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$sc = $ws.CreateShortcut('%SHORTCUT%');" ^
  "$sc.TargetPath = '%LAUNCHER%';" ^
  "$sc.WorkingDirectory = '%ROOT%';" ^
  "if (Test-Path '%ICON%') { $sc.IconLocation = '%ICON%' };" ^
  "$sc.Description = 'VDock Virtual Stream Deck';" ^
  "$sc.WindowStyle = 1;" ^
  "$sc.Save()" >nul 2>&1

if exist "%SHORTCUT%" (
    echo   [OK]    Desktop shortcut created: %SHORTCUT%
) else (
    echo   [WARN]  Could not create desktop shortcut
)
exit /b 0

:launch_vdock
if not exist "%ROOT%\backend\venv\Scripts\activate.bat" (
    echo   [ERROR] Run Full setup first (option 1).
    exit /b 1
)
echo.
echo   Starting VDock...
start "" "%ROOT%\launch.bat"
exit /b 0

:setup_complete
echo.
echo   ==========================================
echo     Setup complete!
echo   ==========================================
echo.
echo   Launch VDock:
echo     - Double-click VDock on your Desktop
echo     - Or run launch.bat from this folder
echo.
echo   URLs once running:
echo     Frontend: http://localhost:3000
echo     Backend:  http://localhost:5000
echo.
set /p "LAUNCH=  Start VDock now? [Y/N]: "
if /i "!LAUNCH!"=="Y" call :launch_vdock
goto :pause_and_menu

:setup_complete_cli
echo.
echo   ==========================================
echo     Setup complete!
echo   ==========================================
echo.
set /p "LAUNCH=  Start VDock now? [Y/N]: "
if /i "!LAUNCH!"=="Y" call :launch_vdock
exit /b 0

:pause_and_menu
echo.
pause
goto :main_menu

:fail
echo.
echo   ==========================================
echo     Setup failed. Fix the error above.
echo   ==========================================
echo.
pause
exit /b 1

:exit_ok
exit /b 0
