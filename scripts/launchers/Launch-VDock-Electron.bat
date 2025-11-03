@echo off
REM VDock Electron Desktop Launcher
REM Double-click this file to launch VDock with Electron

echo ========================================
echo    VDock Virtual Stream Deck (Electron)
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo [OK] Node.js found
echo.

REM Check if Electron dependencies are installed
if not exist "frontend\electron\node_modules" (
    echo [WARNING] Electron dependencies not found!
    echo Installing Electron dependencies...
    cd frontend\electron
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install Electron dependencies
        cd ..\..
        pause
        exit /b 1
    )
    cd ..\..
    echo [OK] Electron dependencies installed
) else (
    echo [OK] Electron dependencies found
)

echo.
echo Starting VDock Electron App...
echo.

REM Launch the Electron app
cd frontend\electron
call npm start

echo.
echo VDock Electron app closed.
pause
