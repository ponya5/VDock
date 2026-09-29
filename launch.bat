@echo off
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

REM ── Transient launcher console ─────────────────────────────────
REM The python launcher exits after startup, but when launch.bat is run from
REM an existing terminal the window belongs to that shell and stays open —
REM a script can't close a console it doesn't own. So we re-dispatch into a
REM dedicated console that closes with the script: the invoking terminal
REM returns to the prompt right away, the launcher window shows progress and
REM closes itself on success (a failure pauses so the error stays readable).
REM Run `launch.bat --in-console` to keep the old in-place behavior.
if /i "%~1"=="--in-console" goto :in_console
if /i "%~x0"=="" (
    start "VDock Launcher" cmd /c ""%~f0.bat" --in-console %*"
) else (
    start "VDock Launcher" cmd /c ""%~f0" --in-console %*"
)
exit /b 0

:in_console
shift
title VDock Launcher

python scripts\VDock-Launcher.py
if errorlevel 1 (
    pause
    exit /b 1
)
exit /b 0
