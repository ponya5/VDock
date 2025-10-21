@echo off
echo Building VDock Portable Distribution...
echo.

REM Set error handling
setlocal enabledelayedexpansion

REM Check if we're in the right directory
if not exist "frontend" (
    echo Error: Please run this script from the VDock root directory
    pause
    exit /b 1
)

REM Create portable directory
set PORTABLE_DIR=VDock-Portable
if exist "%PORTABLE_DIR%" (
    echo Removing existing portable directory...
    rmdir /s /q "%PORTABLE_DIR%"
)

echo Creating portable directory structure...
mkdir "%PORTABLE_DIR%"
mkdir "%PORTABLE_DIR%\backend"
mkdir "%PORTABLE_DIR%\frontend"
mkdir "%PORTABLE_DIR%\data"
mkdir "%PORTABLE_DIR%\logs"

REM Build frontend
echo Building frontend...
cd frontend
call npm run build
if errorlevel 1 (
    echo Error: Frontend build failed
    pause
    exit /b 1
)
cd ..

REM Copy frontend build
echo Copying frontend build...
xcopy "frontend\dist\*" "%PORTABLE_DIR%\frontend\" /E /I /Y

REM Copy backend files (excluding venv, __pycache__, .git)
echo Copying backend files...
xcopy "backend\*" "%PORTABLE_DIR%\backend\" /E /I /Y /EXCLUDE:exclude.txt

REM Create exclude.txt for xcopy
echo __pycache__ > exclude.txt
echo venv >> exclude.txt
echo .git >> exclude.txt
echo *.pyc >> exclude.txt
echo .env >> exclude.txt
echo node_modules >> exclude.txt

REM Copy data directory
if exist "data" (
    echo Copying data directory...
    xcopy "data\*" "%PORTABLE_DIR%\data\" /E /I /Y
)

REM Create launch.bat
echo Creating launch.bat...
(
echo @echo off
echo echo Starting VDock...
echo echo.
echo.
echo REM Check for Python
echo python --version ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo Error: Python is not installed or not in PATH
echo     echo Please install Python 3.8+ from https://python.org
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Check for Node.js
echo node --version ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo Error: Node.js is not installed or not in PATH
echo     echo Please install Node.js from https://nodejs.org
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Install Python dependencies if needed
echo if not exist "backend\venv" ^(
echo     echo Installing Python dependencies...
echo     cd backend
echo     python -m venv venv
echo     call venv\Scripts\activate
echo     pip install -r requirements.txt
echo     cd ..
echo ^)
echo.
echo REM Install Node.js dependencies if needed
echo if not exist "frontend\node_modules" ^(
echo     echo Installing Node.js dependencies...
echo     cd frontend
echo     npm install
echo     cd ..
echo ^)
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
echo echo VDock is starting! Check the opened browser window.
echo echo Backend: http://localhost:5000
echo echo Frontend: http://localhost:3000
echo echo.
echo echo Press any key to exit...
echo pause ^>nul
) > "%PORTABLE_DIR%\launch.bat"

REM Create README
echo Creating README-PORTABLE.txt...
(
echo VDock Portable Distribution
echo ===========================
echo.
echo This is a portable version of VDock that can run without installation.
echo.
echo Requirements:
echo - Windows 10/11
echo - Python 3.8+ ^(will be checked automatically^)
echo - Node.js ^(will be checked automatically^)
echo.
echo To run VDock:
echo 1. Extract this zip file to any folder
echo 2. Double-click launch.bat
echo 3. Wait for the servers to start
echo 4. VDock will open automatically in your browser
echo.
echo First run will take longer as dependencies are installed.
echo Subsequent runs will be faster.
echo.
echo Troubleshooting:
echo - If Python is not found: Install from https://python.org
echo - If Node.js is not found: Install from https://nodejs.org
echo - If ports 3000/5000 are busy: Close other applications using these ports
echo - For support: Check the logs folder for error messages
echo.
echo Backend runs on: http://localhost:5000
echo Frontend runs on: http://localhost:3000
echo.
echo Enjoy using VDock!
) > "%PORTABLE_DIR%\README-PORTABLE.txt"

REM Clean up
del exclude.txt

REM Create zip file
echo Creating zip package...
if exist "VDock-Portable.zip" del "VDock-Portable.zip"

REM Use PowerShell to create zip (available on Windows 10+)
powershell -command "Compress-Archive -Path '%PORTABLE_DIR%\*' -DestinationPath 'VDock-Portable.zip' -Force"

if errorlevel 1 (
    echo Error: Failed to create zip file
    echo Please install 7-Zip or WinRAR to create the zip manually
    pause
    exit /b 1
)

REM Clean up portable directory
rmdir /s /q "%PORTABLE_DIR%"

echo.
echo ========================================
echo VDock Portable Distribution Complete!
echo ========================================
echo.
echo Created: VDock-Portable.zip
echo Size: 
for %%I in (VDock-Portable.zip) do echo %%~zI bytes
echo.
echo To distribute:
echo 1. Share VDock-Portable.zip
echo 2. Recipients extract and run launch.bat
echo 3. VDock will start automatically
echo.
echo Press any key to exit...
pause >nul