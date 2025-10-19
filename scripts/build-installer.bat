@echo off
echo Building VDock Windows Installer...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org/
    pause
    exit /b 1
)

echo Step 1: Building Frontend...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo Error: Failed to install frontend dependencies
    pause
    exit /b 1
)

call npm run build
if %errorlevel% neq 0 (
    echo Error: Failed to build frontend
    pause
    exit /b 1
)

echo Step 2: Installing Electron Dependencies...
cd electron
call npm install
if %errorlevel% neq 0 (
    echo Error: Failed to install electron dependencies
    pause
    exit /b 1
)

echo Step 3: Building Backend Dependencies...
cd ..\..\backend
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install backend dependencies
    pause
    exit /b 1
)

echo Step 4: Creating Python Executable...
python -m pip install pyinstaller
if %errorlevel% neq 0 (
    echo Error: Failed to install pyinstaller
    pause
    exit /b 1
)

REM Create a standalone Python executable for the backend
pyinstaller --onefile --windowed --name "vdock-backend" app.py
if %errorlevel% neq 0 (
    echo Error: Failed to create backend executable
    pause
    exit /b 1
)

echo Step 5: Building Electron App...
cd ..\frontend\electron
call npm run build-win
if %errorlevel% neq 0 (
    echo Error: Failed to build electron app
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo.
echo Installer files are located in:
echo - frontend\electron\dist-electron\
echo.
echo You can find:
echo - VDock Setup.exe (Windows Installer)
echo - VDock-Portable.exe (Portable Version)
echo.
pause
