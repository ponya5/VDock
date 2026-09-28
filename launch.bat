@echo off
title VDock Launcher
cd /d "%~dp0"

REM ── Launcher window behavior ───────────────────────────────────
REM Optional override: set VDOCK_AUTO_CLOSE_LAUNCHER=0 or 1 here.
REM Otherwise controlled from Settings → Server → "Close launcher terminal after startup".
REM if not defined VDOCK_AUTO_CLOSE_LAUNCHER set "VDOCK_AUTO_CLOSE_LAUNCHER=1"

REM ── Frontend dev server ────────────────────────────────────────
REM With frontend\dist built, launches serve the bundle via the backend —
REM no Vite dev server, no extra console. Uncomment to opt back into
REM hot-reload development mode:
REM if not defined VDOCK_DEV_SERVER set "VDOCK_DEV_SERVER=1"

:: Add common Node.js paths so npm is available even in restricted environments
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%APPDATA%\npm;%PATH%"

python scripts\VDock-Launcher.py
if errorlevel 1 (
    pause
    exit /b 1
)
exit /b 0
