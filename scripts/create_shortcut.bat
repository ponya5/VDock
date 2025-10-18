@echo off
REM Create desktop shortcut for VDock launcher

echo Creating VDock desktop shortcut...

set "shortcutPath=%USERPROFILE%\Desktop\VDock.lnk"
set "targetPath=%CD%\launch.bat"
set "iconPath=%CD%\frontend\public\favicon.ico"

powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%shortcutPath%'); $Shortcut.TargetPath = '%targetPath%'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Description = 'VDock Virtual Stream Deck'; $Shortcut.IconLocation = '%iconPath%'; $Shortcut.Save()}"

if exist "%shortcutPath%" (
    echo Desktop shortcut created successfully!
    echo You can now double-click "VDock" on your desktop to launch the app.
) else (
    echo Failed to create desktop shortcut.
)

pause
