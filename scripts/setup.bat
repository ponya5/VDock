@echo off
REM VDock Easy Installer for Windows
REM This script will set up VDock automatically

echo ========================================
echo    VDock Installation Wizard
echo ========================================
echo.

REM Check if Python is installed
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
echo ✓ Python found

REM Check if Node.js is installed
echo [2/6] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo ✓ Node.js found

REM Create Python virtual environment
echo [3/6] Creating Python virtual environment...
if not exist "backend\venv" (
    cd backend
    python -m venv venv
    cd ..
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Install Python dependencies
echo [4/6] Installing backend dependencies...
cd backend
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
cd ..
echo ✓ Backend dependencies installed

REM Install frontend dependencies
echo [5/6] Installing frontend dependencies...
cd frontend
if not exist "node_modules" (
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install Node.js dependencies
        pause
        exit /b 1
    )
    echo ✓ Frontend dependencies installed
) else (
    echo ✓ Frontend dependencies already installed
)

REM Install Electron-specific dependencies
echo [6/6] Installing Electron dependencies...
cd electron
if not exist "node_modules" (
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install Electron dependencies
        cd ..\..
        pause
        exit /b 1
    )
    echo ✓ Electron dependencies installed
) else (
    echo ✓ Electron dependencies already installed
)
cd ..\..

REM Create data directories
echo [7/7] Setting up data directories...
if not exist "backend\data" mkdir "backend\data"
if not exist "backend\data\profiles" mkdir "backend\data\profiles"
if not exist "backend\data\uploads" mkdir "backend\data\uploads"
echo ✓ Data directories created

REM Create desktop shortcut for Electron app
echo.
echo Creating desktop shortcut...
set SCRIPT_DIR=%~dp0
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=%DESKTOP%\VDock.lnk

powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%SHORTCUT%'); $SC.TargetPath = '%SCRIPT_DIR%launchers\Launch-VDock-Electron.bat'; $SC.WorkingDirectory = '%SCRIPT_DIR%'; $SC.IconLocation = '%SCRIPT_DIR%backend\Assets\VdIcon.ico'; $SC.Description = 'VDock Virtual Stream Deck'; $SC.Save()"

if exist "%SHORTCUT%" (
    echo ✓ Desktop shortcut created: VDock.lnk
) else (
    echo ! Could not create desktop shortcut
)

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo VDock has been installed successfully!
echo.
echo To start VDock:
echo   1. Double-click "VDock" shortcut on your desktop
echo   2. Or run: scripts\launchers\Launch-VDock-Electron.bat
echo.
echo Default login: admin / admin
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Would you like to start VDock now? (Y/N)
set /p START_NOW=

if /i "%START_NOW%"=="Y" (
    echo.
    echo Starting VDock...
    call launch.bat
) else (
    echo.
    echo You can start VDock anytime by:
    echo   - Double-clicking the desktop shortcut
    echo   - Running launch.bat
)

echo.
pause
