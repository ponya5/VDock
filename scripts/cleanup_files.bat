@echo off
REM Cleanup duplicate and temporary files
echo Cleaning up duplicate and temporary files...

cd /d "%~dp0.."

REM Remove duplicate launch files from root
if exist "launch.bat" (
    echo Removing duplicate launch.bat from root...
    del launch.bat
)

REM Remove old and duplicate launcher files
if exist "scripts\launchers\Launch-VDock.bat" (
    echo Removing old Launch-VDock.bat...
    del scripts\launchers\Launch-VDock.bat
)

if exist "scripts\launchers\launch.bat" (
    echo Removing duplicate launch.bat...
    del scripts\launchers\launch.bat
)

if exist "scripts\launchers\launch.ps1" (
    echo Removing launch.ps1 (not needed for Windows)...
    del scripts\launchers\launch.ps1
)

if exist "scripts\launchers\launch.sh" (
    echo Removing launch.sh (not needed for Windows)...
    del scripts\launchers\launch.sh
)

REM Remove temporary fix files
if exist "scripts\fix_setup.bat" (
    echo Removing temporary fix_setup.bat...
    del scripts\fix_setup.bat
)

if exist "scripts\fix_shortcut.bat" (
    echo Removing temporary fix_shortcut.bat...
    del scripts\fix_shortcut.bat
)

if exist "scripts\install_cross_env.bat" (
    echo Removing temporary install_cross_env.bat...
    del scripts\install_cross_env.bat
)

if exist "scripts\install_electron_deps.bat" (
    echo Removing temporary install_electron_deps.bat...
    del scripts\install_electron_deps.bat
)

REM Remove duplicate desktop shortcut script
if exist "scripts\create-desktop-shortcut.bat" (
    echo Removing duplicate create-desktop-shortcut.bat...
    del scripts\create-desktop-shortcut.bat
)

echo.
echo Cleanup completed!
echo.
echo Remaining essential files:
echo - scripts\setup.bat (main setup)
echo - scripts\launchers\Launch-VDock-Electron.bat (main launcher)
echo - scripts\create_desktop_shortcut.bat (desktop shortcut creator)
echo - Desktop: VDock.lnk (your desktop shortcut)
echo.
pause
