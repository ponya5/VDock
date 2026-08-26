@echo off
title VDock Launcher
cd /d "%~dp0"

REM ── Launcher window behavior ───────────────────────────────────
REM Optional override: set VDOCK_AUTO_CLOSE_LAUNCHER=0 or 1 here.
REM Otherwise controlled from Settings → Server → "Close launcher terminal after startup".
REM if not defined VDOCK_AUTO_CLOSE_LAUNCHER set "VDOCK_AUTO_CLOSE_LAUNCHER=1"

:: Add common Node.js paths so npm is available even in restricted environments
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%APPDATA%\npm;%PATH%"

python scripts\VDock-Launcher.py
if errorlevel 1 (
    pause
    exit /b 1
)
exit /b 0
