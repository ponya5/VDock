@echo off
REM VDock 2 Desktop Launcher
REM Starts backend, frontend, then Electron (with browser fallback)

set "ROOT=%~dp0..\.."
cd /d "%ROOT%"

set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%APPDATA%\npm;%PATH%"

call "%ROOT%\launch.bat"
