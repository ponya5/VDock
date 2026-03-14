@echo off
title VDock Launcher
cd /d "%~dp0"

:: Add common Node.js paths so npm is available even in restricted environments
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%APPDATA%\npm;%PATH%"

python scripts\VDock-Launcher.py
pause
