@echo off
REM Create VDock desktop shortcut (also available from setup.bat option 3)
cd /d "%~dp0.."
call "%~dp0..\setup.bat" --shortcut
pause
