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
    call :configure_ports silent
    call :offer_firewall_rule
    call :build_frontend
    if errorlevel 1 exit /b 1
    call :create_desktop_shortcut
    goto :setup_complete_cli
)
if /i "%~1"=="--deps" (
    call :install_dependencies
    if errorlevel 1 exit /b 1
    call :build_frontend
    exit /b !errorlevel!
)
if /i "%~1"=="--shortcut" (
    call :create_desktop_shortcut
    exit /b 0
)
if /i "%~1"=="--ports" (
    call :configure_ports
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
echo         Install deps, build the frontend, Start menu + desktop shortcut
echo.
echo     [2] Install dependencies only
echo         Deps + frontend build, no desktop shortcut
echo.
echo     [3] Create shortcuts only
echo         Adds VDock to the Start menu and your Desktop
echo.
echo     [4] Configure ports
echo         Change which localhost ports VDock uses
echo.
echo     [5] Launch VDock now
echo.
echo     [6] Exit
echo.
set "MENU_CHOICE="
set /p "MENU_CHOICE=  Choose an option [1-6] (Enter = 1): "
if "%MENU_CHOICE%"=="" set "MENU_CHOICE=1"

if "%MENU_CHOICE%"=="1" goto :run_full
if "%MENU_CHOICE%"=="2" goto :run_deps
if "%MENU_CHOICE%"=="3" goto :run_shortcut
if "%MENU_CHOICE%"=="4" goto :run_ports
if "%MENU_CHOICE%"=="5" goto :run_launch
if "%MENU_CHOICE%"=="6" goto :exit_ok
echo.
echo   Invalid choice. Press any key to try again...
pause >nul
goto :main_menu

:run_full
echo.
echo   This takes a few minutes the first time ^(downloads Python and
echo   Node packages^). Ports are chosen automatically; change them any
echo   time with: setup.bat --ports
call :install_dependencies
if errorlevel 1 goto :fail
call :configure_ports silent
call :offer_firewall_rule
call :build_frontend
if errorlevel 1 goto :fail
call :create_desktop_shortcut
goto :setup_complete

:run_deps
call :install_dependencies
if errorlevel 1 goto :fail
call :build_frontend
if errorlevel 1 goto :fail
echo.
echo   Dependencies installed. Run setup again to create a shortcut.
goto :pause_and_menu

:run_shortcut
call :create_desktop_shortcut
goto :pause_and_menu

:run_ports
call :configure_ports
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

echo   [1/7] Checking Python and Node.js...
call :ensure_prerequisites
if errorlevel 1 exit /b 1
for /f "tokens=*" %%v in ('%PYTHON_CMD% --version 2^>^&1') do echo   [OK]    %%v ^(%PYTHON_CMD%^)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo   [OK]    Node.js %%v
for /f "tokens=*" %%v in ('npm --version 2^>^&1') do echo   [OK]    npm %%v

echo   [2/7] Python virtual environment...
set "VENV_PY=%ROOT%\backend\venv\Scripts\python.exe"
REM A venv whose Python was upgraded, moved or uninstalled (or is a version
REM VDock does not support) is rebuilt instead of failing later (DL-010).
if exist "!ROOT!\backend\venv" (
    call :venv_python_ok
    if errorlevel 1 (
        echo   [WARN]  backend\venv can't be used: !VENV_PROBLEM!. Recreating it.
        rmdir /s /q "!ROOT!\backend\venv"
    )
)
if not exist "%VENV_PY%" (
    echo           Creating venv with !PYTHON_CMD!...
    %PYTHON_CMD% -m venv "!ROOT!\backend\venv"
    if errorlevel 1 (
        echo   [ERROR] Could not create backend\venv with !PYTHON_CMD!.
        exit /b 1
    )
    echo   [OK]    Virtual environment created
) else (
    echo   [OK]    Virtual environment already exists
)

echo   [3/7] Backend dependencies...
set "PIP_LOG=%ROOT%\backend\data\pip-install.log"
if not exist "%ROOT%\backend\data" mkdir "%ROOT%\backend\data" 2>nul
"%VENV_PY%" -m pip install --upgrade pip --quiet --disable-pip-version-check >nul 2>&1
echo           Installing packages ^(log: backend\data\pip-install.log^)...
"%VENV_PY%" -m pip install -r "%ROOT%\backend\requirements.txt" --disable-pip-version-check > "%PIP_LOG%" 2>&1
if errorlevel 1 (
    call :report_pip_failure
    exit /b 1
)
echo   [OK]    Backend dependencies installed

echo   [4/7] Frontend dependencies...
REM Always run: npm install is a no-op when node_modules already matches the
REM lockfile, and picks up packages added by a git pull when it doesn't.
pushd "%ROOT%\frontend"
call npm install --no-fund --no-audit --loglevel=error
if errorlevel 1 (
    popd
    echo   [ERROR] npm install failed in frontend. Check your connection and try again.
    exit /b 1
)
popd
echo   [OK]    Frontend dependencies installed

echo   [5/7] Electron dependencies...
pushd "%ROOT%\frontend\electron"
call npm install --no-fund --no-audit --loglevel=error
if errorlevel 1 (
    popd
    echo   [ERROR] npm install failed in frontend\electron.
    exit /b 1
)
popd

REM npm is moving to block dependency install scripts by default, and Electron
REM downloads its runtime in one. Without the runtime the VDock window cannot
REM open, so run the download ourselves whenever npm did not.
if not exist "%ROOT%\frontend\electron\node_modules\electron\path.txt" (
    echo           Downloading the Electron runtime...
    pushd "%ROOT%\frontend\electron\node_modules\electron"
    node install.js
    if errorlevel 1 (
        popd
        echo   [ERROR] Electron download failed. Check your connection and run setup.bat again.
        exit /b 1
    )
    popd
)
echo   [OK]    Electron dependencies installed

echo   [6/7] Data directories...
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

echo   [7/7] Integrations...
if not exist "%ROOT%\backend\.env" (
    if exist "%ROOT%\backend\.env.example" (
        copy /y "%ROOT%\backend\.env.example" "%ROOT%\backend\.env" >nul 2>&1
        echo   [OK]    Created backend\.env from the example
    )
) else (
    echo   [OK]    backend\.env already exists
)

REM VDock works with none of these. Each pack detects what it can use and
REM greys out only the actions it cannot run, so this is information, not a
REM requirement.
set "FOUND_ANY="
where claude >nul 2>&1
if not errorlevel 1 (
    echo   [OK]    Claude Code CLI detected - Claude actions enabled
    set "FOUND_ANY=1"
) else (
    echo   [ --]   Claude Code CLI not found - install from https://claude.com/product/claude-code
)
where gh >nul 2>&1
if not errorlevel 1 (
    echo   [OK]    GitHub CLI detected - GitHub actions enabled
    set "FOUND_ANY=1"
) else (
    echo   [ --]   GitHub CLI not found - install from https://cli.github.com
)
where git >nul 2>&1
if not errorlevel 1 (
    echo   [OK]    Git detected - repository-aware actions enabled
) else (
    echo   [ --]   Git not found - repo detection will fall back to a default folder
)
if not defined FOUND_ANY (
    echo           No integration CLIs found. VDock still works fully;
    echo           the Claude and GitHub buttons will show why they are unavailable.
)
exit /b 0

:ensure_prerequisites
REM Python 3.9-3.14 (with venv) and Node 20+ must be available. When something
REM is missing, offer to install it with winget (built into Windows 10/11).
set "MIN_NODE_MAJOR=20"
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%APPDATA%\npm;%PATH%"
set "MISSING_PACKAGES="
set "MISSING_LABELS="

call :find_python
if errorlevel 1 (
    call :report_unsupported_python
    set "MISSING_PACKAGES=!MISSING_PACKAGES! Python.Python.3.13"
    set "MISSING_LABELS=!MISSING_LABELS! Python 3.13"
)
call :check_node
if errorlevel 1 (
    set "MISSING_PACKAGES=!MISSING_PACKAGES! OpenJS.NodeJS.LTS"
    set "MISSING_LABELS=!MISSING_LABELS! Node.js"
)
if not defined MISSING_PACKAGES exit /b 0

where winget >nul 2>&1
if errorlevel 1 goto :prereq_manual_help

echo   [WARN]  Missing:!MISSING_LABELS!
set "INSTALL_ANSWER="
set /p "INSTALL_ANSWER=  Install it now with winget? [Y/n]: "
call :is_yes_answer "!INSTALL_ANSWER!"
if errorlevel 1 goto :prereq_manual_help

for %%p in (!MISSING_PACKAGES!) do (
    winget install -e --id %%p --accept-package-agreements --accept-source-agreements
    if errorlevel 1 goto :prereq_manual_help
)

call :refresh_path
call :find_python
if errorlevel 1 goto :prereq_manual_help
call :check_node
if errorlevel 1 goto :prereq_manual_help
exit /b 0

:prereq_manual_help
echo.
echo   [ERROR] Python 3.9-3.14 ^(3.13 recommended^) and Node.js %MIN_NODE_MAJOR%+ are required.
echo           Python:  https://www.python.org/downloads/ ^(pick 3.13, tick "Add Python to PATH"^)
echo           Node.js: https://nodejs.org/
echo           Or run:  winget install Python.Python.3.13
echo                    winget install OpenJS.NodeJS.LTS
echo           Then close this window and run setup.bat again.
exit /b 1

:is_yes_answer
REM Prompts are [Y/n]: Enter means yes, and only an explicit yes counts as
REM yes. Anything else ^(n, no, a typo^) must never start an install or launch.
if "%~1"=="" exit /b 0
if /i "%~1"=="Y" exit /b 0
if /i "%~1"=="YES" exit /b 0
exit /b 1

:find_python
REM Picks a supported Python into PYTHON_CMD (DL-010): through the py launcher
REM 3.13, 3.12, 3.14, 3.11, 3.10; then "python" when it is 3.9-3.14; then
REM py -3.9. Python 3.15 is too new - pywinrt and other Windows packages have
REM no 3.15 builds yet, so pip would fail half-way.
set "PYTHON_CMD="
set "UNSUPPORTED_PY="
where py >nul 2>&1
if not errorlevel 1 (
    for %%v in (3.13 3.12 3.14 3.11 3.10) do (
        if not defined PYTHON_CMD (
            py -%%v -c "import sys, venv, ensurepip" >nul 2>&1
            if not errorlevel 1 set "PYTHON_CMD=py -%%v"
        )
    )
)
if defined PYTHON_CMD exit /b 0
python -c "import sys, venv, ensurepip; sys.exit(0 if (3, 9) <= sys.version_info[:2] <= (3, 14) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)
py -3.9 -c "import sys, venv, ensurepip" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.9"
    exit /b 0
)
REM Nothing supported. Remember what is installed for the explanation.
for /f "tokens=2" %%v in ('python --version 2^>nul') do set "UNSUPPORTED_PY=%%v"
if not defined UNSUPPORTED_PY (
    for /f "tokens=2" %%v in ('py --version 2^>nul') do set "UNSUPPORTED_PY=%%v"
)
REM The Microsoft Store "python" alias prints a sentence, not a version.
if defined UNSUPPORTED_PY if not "!UNSUPPORTED_PY:~0,2!"=="3." set "UNSUPPORTED_PY="
exit /b 1

:report_unsupported_python
if not defined UNSUPPORTED_PY exit /b 0
echo   [WARN]  Found Python !UNSUPPORTED_PY!, but VDock needs Python 3.9-3.14.
echo           Some of its Windows packages have no builds for that version yet.
echo           Install Python 3.13 next to it - setup then picks it automatically.
exit /b 0

:venv_python_ok
REM OK when backend\venv's python.exe still starts its base Python and that
REM Python is a supported version. VENV_PROBLEM says why not.
set "VENV_PROBLEM="
if not exist "%VENV_PY%" (
    set "VENV_PROBLEM=its Python is missing"
    exit /b 1
)
"%VENV_PY%" -c "import sys; sys.exit(0 if (3, 9) <= sys.version_info[:2] <= (3, 14) else 7)" >nul 2>&1
set "VENV_CHECK=%errorlevel%"
if "%VENV_CHECK%"=="0" exit /b 0
if "%VENV_CHECK%"=="7" (
    set "VENV_PROBLEM=it uses a Python version VDock does not support"
) else (
    set "VENV_PROBLEM=its Python no longer runs - it was moved, upgraded or uninstalled"
)
exit /b 1

:report_pip_failure
REM pip's own ERROR lines plus what they usually mean - never just "check
REM your connection" when a package simply has no build for this Python.
set "PIP_PY_VERSION="
for /f "tokens=2" %%v in ('call "%VENV_PY%" --version 2^>^&1') do set "PIP_PY_VERSION=%%v"
echo   [ERROR] Installing the backend's Python packages failed ^(Python !PIP_PY_VERSION!, %PROCESSOR_ARCHITECTURE%^).
findstr /b /c:"ERROR:" "%PIP_LOG%"
findstr /i /c:"No matching distribution" /c:"Could not find a version that satisfies" /c:"requires a different Python" /c:"Failed building wheel" /c:"Failed to build" /c:"subprocess-exited-with-error" "%PIP_LOG%" >nul 2>&1
if not errorlevel 1 (
    echo           A package has no ready-made build for Python !PIP_PY_VERSION! on this PC.
    echo           Install Python 3.13 ^(winget install Python.Python.3.13^), then run:
    echo             rmdir /s /q backend\venv ^&^& setup.bat
    goto :report_pip_failure_log
)
findstr /i /c:"connection" /c:"timed out" /c:"getaddrinfo" /c:"SSLError" /c:"ProxyError" /c:"Could not fetch URL" "%PIP_LOG%" >nul 2>&1
if not errorlevel 1 echo           pip could not reach the package index - check your internet connection or proxy.
:report_pip_failure_log
echo           Full log: %PIP_LOG%
exit /b 0

:offer_firewall_rule
REM Phones reach VDock over Wi-Fi, and Windows Defender Firewall blocks the
REM backend until a rule allows it (DL-010). Offered once (a "no" is
REM remembered): Private networks only, TCP, the backend port, for the venv
REM python.exe and the base python.exe it starts - a venv's python.exe is a
REM launcher, the base interpreter is the process that listens. One UAC prompt.
set "FW_RULE=VDock backend - source install"
set "FW_DECLINED=%ROOT%\backend\data\.firewall-rule-declined"
netsh advfirewall firewall show rule name="%FW_RULE%" >nul 2>&1
if not errorlevel 1 (
    echo   [OK]    Windows Firewall already lets phones reach VDock ^(private networks^)
    exit /b 0
)
if exist "%FW_DECLINED%" exit /b 0
if not defined BACKEND_PORT exit /b 0
set "VENV_PY=%ROOT%\backend\venv\Scripts\python.exe"
if not exist "%VENV_PY%" exit /b 0
set "BASE_PY="
for /f "usebackq delims=" %%p in (`call "%VENV_PY%" -c "import sys; print(getattr(sys, '_base_executable', '') or sys.executable)"`) do set "BASE_PY=%%p"
echo.
echo   Phones and tablets reach VDock over your Wi-Fi, which Windows Firewall
echo   blocks until it is allowed. Setup can add a rule now: private networks
echo   only ^(home or work Wi-Fi, never public^), port !BACKEND_PORT!. Windows asks
echo   for approval once.
set "FW_ANSWER="
set /p "FW_ANSWER=  Allow phones through the firewall? [Y/n]: "
call :is_yes_answer "!FW_ANSWER!"
if errorlevel 1 (
    type nul > "%FW_DECLINED%" 2>nul
    echo   [ --]   Skipped. Windows asks the first time you turn on LAN access.
    exit /b 0
)
set "FW_SCRIPT=%TEMP%\vdock-firewall-rule.cmd"
> "%FW_SCRIPT%" echo @echo off
>> "%FW_SCRIPT%" echo netsh advfirewall firewall delete rule name="%FW_RULE%" ^>nul 2^>^&1
>> "%FW_SCRIPT%" echo netsh advfirewall firewall add rule name="%FW_RULE%" dir=in action=allow protocol=TCP localport=!BACKEND_PORT! profile=private program="!VENV_PY!" enable=yes
if defined BASE_PY if /i not "!BASE_PY!"=="!VENV_PY!" >> "%FW_SCRIPT%" echo netsh advfirewall firewall add rule name="%FW_RULE%" dir=in action=allow protocol=TCP localport=!BACKEND_PORT! profile=private program="!BASE_PY!" enable=yes
powershell -NoProfile -NonInteractive -Command "try { Start-Process -FilePath $env:FW_SCRIPT -Verb RunAs -Wait -WindowStyle Hidden } catch { exit 1 }" >nul 2>&1
del "%FW_SCRIPT%" 2>nul
netsh advfirewall firewall show rule name="%FW_RULE%" >nul 2>&1
if errorlevel 1 (
    echo   [WARN]  No firewall rule added ^(approval declined?^). Windows asks when you turn on LAN access.
) else (
    echo   [OK]    Windows Firewall lets phones reach VDock ^(private networks, port !BACKEND_PORT!^)
)
exit /b 0

:check_node
set "NODE_MAJOR="
for /f "usebackq delims=" %%v in (`node -p "process.versions.node.split('.')[0]" 2^>nul`) do set "NODE_MAJOR=%%v"
if not defined NODE_MAJOR exit /b 1
if !NODE_MAJOR! LSS %MIN_NODE_MAJOR% exit /b 1
where npm >nul 2>&1
exit /b %errorlevel%

:refresh_path
REM A fresh winget install updates the registry PATH, not this window's.
for /f "usebackq delims=" %%p in (`powershell -NoProfile -NonInteractive -Command "[Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')"`) do set "PATH=%%p"
set "PATH=%ProgramFiles%\nodejs;%PATH%"
exit /b 0

:build_frontend
echo.
echo   Building the frontend...
REM VDock serves frontend\dist, which git does not track - without this
REM step a pull or reinstall keeps showing the previously built UI. Runs
REM after :configure_ports because the ports in frontend\.env are baked
REM into the bundle.
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%APPDATA%\npm;%PATH%"
pushd "%ROOT%\frontend"
call npm run build
if errorlevel 1 (
    popd
    echo   [ERROR] Frontend build failed. See the output above.
    exit /b 1
)
popd
echo   [OK]    Frontend built ^(frontend\dist^)
exit /b 0

:create_desktop_shortcut
echo.
echo   Creating VDock shortcuts ^(Start menu and Desktop^)...
set "LAUNCHER=%ROOT%\launch.bat"
set "ICON=%ROOT%\frontend\public\vdock-icon.ico"
set "CREATED_SHORTCUTS_FILE=%TEMP%\vdock-shortcuts.txt"

REM 'Programs' is the per-user Start menu, so VDock shows up in Start search
REM and the All apps list without admin rights.
powershell -NoProfile -NonInteractive -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "foreach ($folderName in 'Programs','Desktop') {" ^
  "  $shortcutPath = Join-Path ([Environment]::GetFolderPath($folderName)) 'VDock.lnk';" ^
  "  $sc = $ws.CreateShortcut($shortcutPath);" ^
  "  $sc.TargetPath = '%LAUNCHER%';" ^
  "  $sc.Arguments = '--in-console';" ^
  "  $sc.WorkingDirectory = '%ROOT%';" ^
  "  if (Test-Path '%ICON%') { $sc.IconLocation = '%ICON%' };" ^
  "  $sc.Description = 'VDock Virtual Stream Deck';" ^
  "  $sc.WindowStyle = 1;" ^
  "  $sc.Save();" ^
  "  Write-Output $shortcutPath" ^
  "}" > "%CREATED_SHORTCUTS_FILE%" 2>nul

set "CREATED_ANY="
if exist "%CREATED_SHORTCUTS_FILE%" (
    for /f "usebackq delims=" %%s in ("%CREATED_SHORTCUTS_FILE%") do (
        if exist "%%s" (
            echo   [OK]    Shortcut created: %%s
            set "CREATED_ANY=1"
        )
    )
    del "%CREATED_SHORTCUTS_FILE%" 2>nul
)
if not defined CREATED_ANY echo   [WARN]  Could not create shortcuts
exit /b 0

:configure_ports
echo.
echo   ==========================================
echo     Port configuration
echo   ==========================================
echo.

set "CUR_FRONTEND_PORT=3000"
if exist "%ROOT%\frontend\.env" (
    for /f "tokens=2 delims==" %%p in ('findstr /b /i "VITE_PORT=" "%ROOT%\frontend\.env" 2^>nul') do set "CUR_FRONTEND_PORT=%%p"
)
set "CUR_BACKEND_PORT=5000"
if exist "%ROOT%\backend\.env" (
    for /f "tokens=2 delims==" %%p in ('findstr /b /i "PORT=" "%ROOT%\backend\.env" 2^>nul') do set "CUR_BACKEND_PORT=%%p"
)

REM Another app may already own the backend port (AirPlay on macOS, dev
REM servers, ...). Never default to a port something else listens on; a
REM running VDock backend is fine to keep.
set "FREE_BACKEND_PORT="
for /f "usebackq delims=" %%p in (`powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%ROOT%\scripts\find-free-port.ps1" -Port %CUR_BACKEND_PORT% 2^>nul`) do set "FREE_BACKEND_PORT=%%p"
if defined FREE_BACKEND_PORT if not "!FREE_BACKEND_PORT!"=="!CUR_BACKEND_PORT!" (
    echo   [WARN]  Port !CUR_BACKEND_PORT! is used by another app.
    echo   [WARN]  Defaulting the backend to port !FREE_BACKEND_PORT! instead.
    set "CUR_BACKEND_PORT=!FREE_BACKEND_PORT!"
)

if /i "%~1"=="silent" (
    set "FRONTEND_PORT=!CUR_FRONTEND_PORT!"
    set "BACKEND_PORT=!CUR_BACKEND_PORT!"
    goto :configure_ports_write
)

echo   3000/5000 are common defaults - change them if another app already
echo   uses one. Press Enter to keep the current value shown in [brackets].
echo.
set "FRONTEND_PORT="
set /p "FRONTEND_PORT=  Frontend port [!CUR_FRONTEND_PORT!]: "
if "!FRONTEND_PORT!"=="" set "FRONTEND_PORT=!CUR_FRONTEND_PORT!"

set "BACKEND_PORT="
set /p "BACKEND_PORT=  Backend port [!CUR_BACKEND_PORT!]: "
if "!BACKEND_PORT!"=="" set "BACKEND_PORT=!CUR_BACKEND_PORT!"

echo !FRONTEND_PORT!| findstr /r "^[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo   [WARN]  "!FRONTEND_PORT!" is not a valid port number. Using !CUR_FRONTEND_PORT!.
    set "FRONTEND_PORT=!CUR_FRONTEND_PORT!"
)
echo !BACKEND_PORT!| findstr /r "^[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo   [WARN]  "!BACKEND_PORT!" is not a valid port number. Using !CUR_BACKEND_PORT!.
    set "BACKEND_PORT=!CUR_BACKEND_PORT!"
)
if "!FRONTEND_PORT!"=="!BACKEND_PORT!" (
    echo   [WARN]  Frontend and backend ports must differ. Keeping current values.
    set "FRONTEND_PORT=!CUR_FRONTEND_PORT!"
    set "BACKEND_PORT=!CUR_BACKEND_PORT!"
)

:configure_ports_write
if not exist "%ROOT%\backend\.env" type nul > "%ROOT%\backend\.env"
findstr /v /b /i "PORT= CORS_ORIGINS=" "%ROOT%\backend\.env" > "%ROOT%\backend\.env.tmp"
(
    type "%ROOT%\backend\.env.tmp"
    echo PORT=!BACKEND_PORT!
    echo CORS_ORIGINS=http://localhost:!FRONTEND_PORT!,http://127.0.0.1:!FRONTEND_PORT!
) > "%ROOT%\backend\.env"
del "%ROOT%\backend\.env.tmp" 2>nul

if not exist "%ROOT%\frontend\.env" type nul > "%ROOT%\frontend\.env"
findstr /v /b /i "VITE_PORT= VITE_BACKEND_PORT=" "%ROOT%\frontend\.env" > "%ROOT%\frontend\.env.tmp"
(
    type "%ROOT%\frontend\.env.tmp"
    echo VITE_PORT=!FRONTEND_PORT!
    echo VITE_BACKEND_PORT=!BACKEND_PORT!
) > "%ROOT%\frontend\.env"
del "%ROOT%\frontend\.env.tmp" 2>nul

echo   [OK]    Frontend port: !FRONTEND_PORT!
echo   [OK]    Backend port:  !BACKEND_PORT!
exit /b 0

:launch_vdock
if not exist "%ROOT%\backend\venv\Scripts\activate.bat" (
    echo   [ERROR] Run Full setup first ^(option 1^).
    exit /b 1
)
echo.
echo   Starting VDock...
start "VDock Launcher" cmd /c ""%ROOT%\launch.bat" --in-console"
exit /b 0

:setup_complete
echo.
echo   ==========================================
echo     Setup complete!
echo   ==========================================
echo.
echo   Launch VDock:
echo     - Open VDock from the Start menu ^(search "VDock"^) or your Desktop
echo     - Or run launch.bat from this folder
echo.
echo   VDock opens at: http://localhost:!BACKEND_PORT!
echo.
echo   Phone or tablet: mobile access is OFF by default, so your phone can't
echo   open VDock yet. To use it: Settings ^> Devices ^& network ^> turn on
echo   "Allow LAN access", relaunch VDock, then scan the QR code.
echo.
set "LAUNCH="
set /p "LAUNCH=  Start VDock now? [Y/n]: "
call :is_yes_answer "!LAUNCH!"
if not errorlevel 1 call :launch_vdock
goto :pause_and_menu

:setup_complete_cli
echo.
echo   ==========================================
echo     Setup complete!
echo   ==========================================
echo.
echo   VDock opens at: http://localhost:!BACKEND_PORT!
echo.
echo   Phone or tablet: mobile access is OFF by default, so your phone can't
echo   open VDock yet. To use it: Settings ^> Devices ^& network ^> turn on
echo   "Allow LAN access", relaunch VDock, then scan the QR code.
echo.
set "LAUNCH="
set /p "LAUNCH=  Start VDock now? [Y/n]: "
call :is_yes_answer "!LAUNCH!"
if not errorlevel 1 call :launch_vdock
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
