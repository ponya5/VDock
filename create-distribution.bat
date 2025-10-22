@echo off
echo ========================================
echo VDock Distribution Package Creator
echo ========================================
echo.

REM Set error handling
setlocal enabledelayedexpansion

REM Check if we're in the right directory
if not exist "frontend" (
    echo Error: Please run this script from the VDock root directory
    pause
    exit /b 1
)

REM Create distribution directory
set DIST_DIR=VDock-Distribution
if exist "%DIST_DIR%" (
    echo Removing existing distribution directory...
    rmdir /s /q "%DIST_DIR%"
)

echo Creating distribution directory structure...
mkdir "%DIST_DIR%"
mkdir "%DIST_DIR%\backend"
mkdir "%DIST_DIR%\frontend"
mkdir "%DIST_DIR%\data"
mkdir "%DIST_DIR%\docs"

REM Copy backend files (excluding venv, __pycache__, .git)
echo Copying backend files...
robocopy "backend" "%DIST_DIR%\backend" /E /XD venv __pycache__ .git node_modules /XF *.pyc .env

REM Copy frontend build (already built)
echo Copying frontend build...
robocopy "frontend\dist" "%DIST_DIR%\frontend" /E

REM Copy launcher executable if it exists
if exist "dist\VDock-Launcher.exe" (
    echo Copying VDock-Launcher.exe...
    copy "dist\VDock-Launcher.exe" "%DIST_DIR%\"
)

REM Copy documentation
echo Copying documentation...
robocopy "docs" "%DIST_DIR%\docs" /E

REM Copy root files
echo Copying root files...
copy "README.md" "%DIST_DIR%\"
copy "LICENSE" "%DIST_DIR%\"
copy "requirements.txt" "%DIST_DIR%\"
copy "package.json" "%DIST_DIR%\"
copy "install.bat" "%DIST_DIR%\"
copy "install.sh" "%DIST_DIR%\"
copy "launch.bat" "%DIST_DIR%\"
copy "launch.sh" "%DIST_DIR%\"

REM Create enhanced launch.bat for distribution
echo Creating enhanced launch.bat...
(
echo @echo off
echo echo ========================================
echo echo VDock Virtual Stream Deck
echo echo ========================================
echo echo.
echo.
echo REM Check for Python
echo python --version ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo Error: Python is not installed or not in PATH
echo     echo Please install Python 3.8+ from https://python.org
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Check for Node.js
echo node --version ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo Error: Node.js is not installed or not in PATH
echo     echo Please install Node.js from https://nodejs.org
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo ✓ Python found
echo echo ✓ Node.js found
echo echo.
echo.
echo REM Install Python dependencies if needed
echo if not exist "backend\venv" ^(
echo     echo Installing Python dependencies...
echo     cd backend
echo     python -m venv venv
echo     call venv\Scripts\activate
echo     pip install -r requirements.txt
echo     cd ..
echo     echo ✓ Python dependencies installed
echo ^) else ^(
echo     echo ✓ Python dependencies already installed
echo ^)
echo.
echo REM Install Node.js dependencies if needed
echo if not exist "frontend\node_modules" ^(
echo     echo Installing Node.js dependencies...
echo     cd frontend
echo     npm install
echo     cd ..
echo     echo ✓ Node.js dependencies installed
echo ^) else ^(
echo     echo ✓ Node.js dependencies already installed
echo ^)
echo.
echo echo Starting VDock services...
echo echo.
echo.
echo REM Start backend server
echo echo Starting backend server...
echo start "VDock Backend" cmd /k "cd backend ^&^& call venv\Scripts\activate ^&^& python app.py"
echo.
echo REM Wait a moment for backend to start
echo timeout /t 3 /nobreak ^>nul
echo.
echo REM Start frontend server
echo echo Starting frontend server...
echo start "VDock Frontend" cmd /k "cd frontend ^&^& npm run dev"
echo.
echo REM Wait for servers to start
echo echo Waiting for servers to start...
echo timeout /t 5 /nobreak ^>nul
echo.
echo REM Open browser
echo echo Opening VDock in browser...
echo start http://localhost:3000
echo.
echo echo ========================================
echo echo VDock Started Successfully!
echo echo ========================================
echo echo.
echo echo Backend:  http://localhost:5000
echo echo Frontend: http://localhost:3000
echo echo.
echo echo Default login:
echo echo   Username: admin
echo echo   Password: admin
echo echo.
echo echo Both servers are running in the background.
echo echo Close the server windows to stop VDock.
echo echo.
echo pause
) > "%DIST_DIR%\launch.bat"

REM Create README for distribution
echo Creating distribution README...
(
echo # VDock Virtual Stream Deck - Distribution Package
echo.
echo This is a complete distribution package of VDock that includes everything needed to run the application.
echo.
echo ## What's Included
echo.
echo - **VDock-Launcher.exe**: Standalone executable launcher ^(if available^)
echo - **Backend**: Python Flask server with all dependencies
echo - **Frontend**: Vue.js web application ^(pre-built^)
echo - **Documentation**: Complete user guides and API documentation
echo - **Launch Scripts**: Easy-to-use startup scripts
echo.
echo ## System Requirements
echo.
echo - **Windows 10/11** ^(recommended^)
echo - **Python 3.8+** - Download from https://python.org
echo - **Node.js 16+** - Download from https://nodejs.org
echo - **4GB RAM** minimum
echo - **1GB free disk space**
echo.
echo ## Quick Start
echo.
echo ### Option 1: Using the Executable Launcher ^(Easiest^)
echo 1. Double-click `VDock-Launcher.exe`
echo 2. Wait for the application to start
echo 3. VDock will open automatically in your browser
echo.
echo ### Option 2: Using Launch Script
echo 1. Double-click `launch.bat`
echo 2. Wait for dependencies to install ^(first run only^)
echo 3. VDock will open automatically in your browser
echo.
echo ### Option 3: Manual Setup
echo 1. Run `install.bat` to install dependencies
echo 2. Run `launch.bat` to start the application
echo.
echo ## First Time Setup
echo.
echo 1. **Install Dependencies**: The first run will automatically install all required dependencies
echo 2. **Login**: Use the default credentials ^(admin/admin^) or set up authentication
echo 3. **Create Profile**: Set up your first button profile
echo 4. **Add Buttons**: Start adding buttons to your virtual stream deck
echo.
echo ## Default Access URLs
echo.
echo - **Main Application**: http://localhost:3000
echo - **Backend API**: http://localhost:5000
echo.
echo ## Troubleshooting
echo.
echo ### Common Issues
echo.
echo **Python not found**
echo - Install Python from https://python.org
echo - Make sure to check "Add Python to PATH" during installation
echo.
echo **Node.js not found**
echo - Install Node.js from https://nodejs.org
echo - Restart your command prompt after installation
echo.
echo **Ports already in use**
echo - Close other applications using ports 3000 or 5000
echo - Or modify the port settings in the configuration files
echo.
echo **Permission errors**
echo - Run as Administrator if you encounter permission issues
echo - Check your antivirus software settings
echo.
echo ### Getting Help
echo.
echo - Check the `docs` folder for detailed documentation
echo - Visit the project repository for updates and support
echo - Review the log files in the `data` folder for error details
echo.
echo ## Features
echo.
echo - **Virtual Stream Deck**: Create custom button layouts
echo - **Multiple Profiles**: Switch between different button configurations
echo - **Action Types**: Support for various actions ^(commands, hotkeys, URLs, etc.^)
echo - **Themes**: Customize the appearance
echo - **Plugins**: Extend functionality with custom plugins
echo - **Web-based**: Access from any modern web browser
echo - **Cross-platform**: Works on Windows, macOS, and Linux
echo.
echo ## Security Notes
echo.
echo - VDock runs locally on your machine
echo - No data is sent to external servers
echo - Authentication can be configured for additional security
echo - All data is stored locally in the `data` folder
echo.
echo ---
echo.
echo **Enjoy using VDock!**
echo.
echo For more information, visit the documentation in the `docs` folder.
) > "%DIST_DIR%\README-DISTRIBUTION.md"

REM Create zip file
echo Creating zip package...
if exist "VDock-Distribution.zip" del "VDock-Distribution.zip"

REM Use PowerShell to create zip (available on Windows 10+)
powershell -command "Compress-Archive -Path '%DIST_DIR%\*' -DestinationPath 'VDock-Distribution.zip' -Force"

if errorlevel 1 (
    echo Error: Failed to create zip file
    echo The distribution folder is ready at: %DIST_DIR%
    echo You can manually zip it or use 7-Zip/WinRAR
) else (
    echo ✓ Zip package created successfully
    REM Clean up distribution directory
    rmdir /s /q "%DIST_DIR%"
)

echo.
echo ========================================
echo VDock Distribution Package Complete!
echo ========================================
echo.
if exist "VDock-Distribution.zip" (
    echo Created: VDock-Distribution.zip
    for %%I in (VDock-Distribution.zip) do echo Size: %%~zI bytes
) else (
    echo Created: %DIST_DIR% folder
)
echo.
echo To distribute:
echo 1. Share VDock-Distribution.zip ^(or the folder^)
echo 2. Recipients extract and run launch.bat or VDock-Launcher.exe
echo 3. VDock will start automatically
echo.
echo Press any key to exit...
pause >nul
