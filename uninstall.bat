@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM  VDock Uninstall — source checkout
REM  Stops running VDock processes, removes the startup entry
REM  and desktop shortcut. The folder itself is deleted by hand
REM  at the end; everything else lives inside it.
REM ============================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if /i "%~1"=="--yes" goto :run

echo.
echo   ========================================================
echo     VDock Uninstall
echo   ========================================================
echo.
echo     This will:
echo       - Stop running VDock processes (launcher, backend,
echo         Vite dev server, Electron)
echo       - Remove the Windows startup entry (if set)
echo       - Remove the Desktop shortcut (if present)
echo.
echo     It does NOT delete this folder. Afterwards, delete
echo       %ROOT%
echo     to remove VDock completely — profiles and settings in
echo     backend\data go with it.
echo.
set "CONFIRM="
set /p "CONFIRM=  Continue? [y/N]: "
if /i not "!CONFIRM!"=="y" (
    echo   Aborted.
    exit /b 0
)

:run
echo.
echo   [1/3] Stopping VDock processes...

REM Ports the source install runs on. Read them from the .env files
REM setup wrote, falling back to the factory defaults.
set "BACKEND_PORT=5000"
set "FRONTEND_PORT=3000"
if exist "%ROOT%\backend\.env" (
    for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b "PORT=" "%ROOT%\backend\.env"`) do set "BACKEND_PORT=%%b"
)
if exist "%ROOT%\frontend\.env" (
    for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b "VITE_PORT=" "%ROOT%\frontend\.env"`) do set "FRONTEND_PORT=%%b"
)

REM Kill listeners on both ports plus any process whose command line
REM points inside this folder or names VDock-Launcher.py (the launcher
REM starts it with a relative path). Explicitly never match cmd.exe or
REM this script — CommandLine would contain %ROOT% and we'd kill the
REM shell running this file.
powershell -NoProfile -NonInteractive -Command ^
  "$root = '%ROOT%';" ^
  "$ports = @(%BACKEND_PORT%, %FRONTEND_PORT%);" ^
  "$pids = @();" ^
  "foreach ($port in $ports) {" ^
  "  try { Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop | ForEach-Object { $pids += $_.OwningProcess } } catch {};" ^
  "}" ^
  "$procs = Get-CimInstance Win32_Process | Where-Object {" ^
  "  $_.Name -notmatch '^(cmd|powershell|pwsh)\.exe$' -and" ^
  "  $_.CommandLine -and" ^
  "  ($_.CommandLine.Contains($root) -or $_.CommandLine.Contains('VDock-Launcher.py') -or $_.CommandLine.Contains('vdock-backend'))" ^
  "};" ^
  "foreach ($p in $procs) { $pids += $p.ProcessId };" ^
  "foreach ($id in ($pids | Sort-Object -Unique)) {" ^
  "  try { Stop-Process -Id $id -Force -ErrorAction Stop; Write-Host ('   stopped pid ' + $id) } catch {}" ^
  "}"
echo   [OK]    Process sweep done

echo.
echo   [2/3] Removing startup entry...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v VDock /f >nul 2>&1
if errorlevel 1 (
    echo   [ --]   No startup entry found
) else (
    echo   [OK]    Removed VDock from Windows startup
)

echo.
echo   [3/3] Removing desktop shortcut...
set "DESKTOP_DIR="
for /f "usebackq delims=" %%d in (`powershell -NoProfile -NonInteractive -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP_DIR=%%d"
if not defined DESKTOP_DIR set "DESKTOP_DIR=%USERPROFILE%\Desktop"
if exist "%DESKTOP_DIR%\VDock.lnk" (
    del "%DESKTOP_DIR%\VDock.lnk" >nul 2>&1
    echo   [OK]    Removed %DESKTOP_DIR%\VDock.lnk
) else (
    echo   [ --]   No desktop shortcut found
)

echo.
echo   ========================================================
echo     Done. To finish removing VDock, delete this folder:
echo       %ROOT%
echo   ========================================================
echo.
if /i not "%~1"=="--yes" pause
exit /b 0
