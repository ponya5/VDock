@echo off
title VDock Launcher
cd /d "%~dp0"

REM ── Launcher window behavior ───────────────────────────────────
REM Set to 1 to close this window automatically after VDock starts.
REM Set to 0 to keep it open until you press Enter (useful for debugging).
set "VDOCK_AUTO_CLOSE_LAUNCHER=1"

:: Add common Node.js paths so npm is available even in restricted environments
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%APPDATA%\npm;%PATH%"

python scripts\VDock-Launcher.py
if errorlevel 1 (
    pause
    exit /b 1
)

if "%VDOCK_AUTO_CLOSE_LAUNCHER%"=="1" exit /b 0
pause
