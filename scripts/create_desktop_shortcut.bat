@echo off
REM Create VDock 2 Desktop Shortcut
echo Creating VDock 2 desktop shortcut...

REM Resolve repo root (parent of scripts folder)
for %%I in ("%~dp0..") do set "ROOT=%%~fI"

REM Resolve real Desktop path (supports OneDrive-backed desktops)
for /f "usebackq delims=" %%d in (`powershell -NoProfile -NonInteractive -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP_DIR=%%d"
if not defined DESKTOP_DIR set "DESKTOP_DIR=%USERPROFILE%\Desktop"

set "LAUNCHER=%ROOT%\scripts\launchers\Launch-VDock.bat"
set "ICON=%ROOT%\frontend\public\vdock-icon.ico"
set "SHORTCUT=%DESKTOP_DIR%\VDock 2.lnk"

echo Project root: %ROOT%
echo Desktop:      %DESKTOP_DIR%
echo Shortcut:     %SHORTCUT%
echo Launcher:     %LAUNCHER%
echo.

if not exist "%LAUNCHER%" (
    echo [ERROR] Launcher not found: %LAUNCHER%
    pause & exit /b 1
)

if exist "%SHORTCUT%" (
    echo Removing old shortcut...
    del "%SHORTCUT%"
)

echo Creating shortcut...
powershell -NoProfile -NonInteractive -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$sc = $ws.CreateShortcut('%SHORTCUT%');" ^
  "$sc.TargetPath = '%LAUNCHER%';" ^
  "$sc.WorkingDirectory = '%ROOT%';" ^
  "if (Test-Path '%ICON%') { $sc.IconLocation = '%ICON%' };" ^
  "$sc.Description = 'VDock 2 Virtual Stream Deck';" ^
  "$sc.WindowStyle = 1;" ^
  "$sc.Save()"

if exist "%SHORTCUT%" (
    echo.
    echo [OK] Desktop shortcut created: %SHORTCUT%
    echo.
    echo Double-click "VDock 2" on your desktop to launch the app.
    echo.
    echo Other launchers in scripts\launchers\:
    echo   Launch-VDock.bat          - Full launcher ^(Electron + browser fallback^)
    echo   Launch-VDock-Electron.bat - Electron desktop app only
    echo   Launch-VDock-Browser.bat  - Browser mode only
) else (
    echo.
    echo [ERROR] Failed to create desktop shortcut.
    echo You can run this launcher directly:
    echo   %LAUNCHER%
)

echo.
pause
