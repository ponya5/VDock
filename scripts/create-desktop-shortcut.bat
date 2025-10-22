@echo off
REM Create Desktop Shortcut for VDock
REM This script creates a shortcut on the desktop to launch VDock

echo ========================================
echo VDock Desktop Shortcut Creator
echo ========================================
echo.

REM Get the project root directory
set "PROJECT_ROOT=%~dp0.."
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

REM Check if running from scripts folder
if not exist "%PROJECT_ROOT%\backend" (
    echo Error: Please run this script from the scripts folder
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Get desktop path
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul') do set "DESKTOP=%%b"

if not defined DESKTOP (
    echo Error: Could not find desktop path
    pause
    exit /b 1
)

echo Project root: %PROJECT_ROOT%
echo Desktop path: %DESKTOP%
echo.

REM Check if VDock-Launcher.exe exists
if exist "%PROJECT_ROOT%\dist\VDock-Launcher.exe" (
    set "LAUNCHER_PATH=%PROJECT_ROOT%\dist\VDock-Launcher.exe"
    echo Found VDock-Launcher.exe
) else if exist "%PROJECT_ROOT%\VDock-Launcher.exe" (
    set "LAUNCHER_PATH=%PROJECT_ROOT%\VDock-Launcher.exe"
    echo Found VDock-Launcher.exe in root
) else if exist "%PROJECT_ROOT%\Launch-VDock.bat" (
    set "LAUNCHER_PATH=%PROJECT_ROOT%\Launch-VDock.bat"
    echo Found Launch-VDock.bat
) else (
    echo No launcher found. Using Launch-VDock.bat as default.
    set "LAUNCHER_PATH=%PROJECT_ROOT%\Launch-VDock.bat"
)

echo.
echo Creating desktop shortcut...

REM Create VBScript to create shortcut
set "VBS_FILE=%TEMP%\create_shortcut.vbs"
set "SHORTCUT_PATH=%DESKTOP%\VDock.lnk"

(
echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo sLinkFile = "%SHORTCUT_PATH%"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
echo oLink.TargetPath = "%LAUNCHER_PATH%"
echo oLink.WorkingDirectory = "%PROJECT_ROOT%"
echo oLink.Description = "VDock Virtual Stream Deck Launcher"
echo oLink.IconLocation = "%LAUNCHER_PATH%"
echo oLink.Save
) > "%VBS_FILE%"

REM Run VBScript
cscript //nologo "%VBS_FILE%"

REM Clean up
del "%VBS_FILE%"

if exist "%SHORTCUT_PATH%" (
    echo ✓ Desktop shortcut created successfully!
    echo.
    echo Shortcut location: %SHORTCUT_PATH%
    echo.
    echo You can now:
    echo 1. Double-click the shortcut on your desktop to launch VDock
    echo 2. Right-click the shortcut ^> Properties to customize
    echo 3. Drag it to your taskbar to pin it
    echo.
) else (
    echo ✗ Failed to create shortcut
    echo.
    echo Try running this script as Administrator
    pause
    exit /b 1
)

echo ========================================
echo Done!
echo ========================================
echo.
pause

