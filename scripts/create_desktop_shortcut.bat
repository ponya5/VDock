@echo off
REM Create VDock Desktop Shortcut
echo Creating VDock desktop shortcut...

set SCRIPT_DIR=%~dp0..
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=%DESKTOP%\VDock.lnk

echo Script directory: %SCRIPT_DIR%
echo Desktop: %DESKTOP%
echo Shortcut path: %SHORTCUT%

REM Remove existing shortcut if it exists
if exist "%SHORTCUT%" (
    echo Removing old shortcut...
    del "%SHORTCUT%"
)

REM Create new shortcut pointing to Browser launcher
echo Creating new shortcut...
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%SHORTCUT%'); $SC.TargetPath = '%SCRIPT_DIR%\scripts\launchers\Launch-VDock-Browser.bat'; $SC.WorkingDirectory = '%SCRIPT_DIR%'; $SC.IconLocation = '%SCRIPT_DIR%\backend\Assets\VdIcon.ico'; $SC.Description = 'VDock Virtual Stream Deck'; $SC.Save()"

if exist "%SHORTCUT%" (
    echo ✓ Desktop shortcut created successfully: %SHORTCUT%
    echo.
    echo You can now double-click the VDock icon on your desktop to launch the app!
) else (
    echo ✗ Failed to create desktop shortcut
    echo.
    echo Alternative: You can run this file directly:
    echo   %SCRIPT_DIR%\scripts\launchers\Launch-VDock-Electron.bat
)

pause
