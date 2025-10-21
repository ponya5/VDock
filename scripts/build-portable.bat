@echo off
REM VDock Portable Distribution Builder
REM Creates a ready-to-use portable zip package for Windows

setlocal EnableDelayedExpansion

echo ============================================
echo    VDock Portable Distribution Builder
echo ============================================
echo.

REM Set variables
set BUILD_DIR=VDock-Portable
set ZIP_NAME=VDock-Portable-v1.0.zip
set ROOT_DIR=%CD%

REM Check if 7-Zip is available (optional, for better compression)
where 7z >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set HAS_7ZIP=1
    echo [INFO] 7-Zip detected - will use for compression
) else (
    set HAS_7ZIP=0
    echo [INFO] 7-Zip not found - will use PowerShell compression
)

echo.
echo [Step 1/10] Cleaning previous build...
if exist "%BUILD_DIR%" (
    echo Removing old build directory...
    rmdir /s /q "%BUILD_DIR%" 2>nul
)
if exist "%ZIP_NAME%" (
    echo Removing old zip file...
    del /f /q "%ZIP_NAME%" 2>nul
)

echo.
echo [Step 2/10] Creating build directory structure...
mkdir "%BUILD_DIR%"
mkdir "%BUILD_DIR%\backend"
mkdir "%BUILD_DIR%\frontend"
mkdir "%BUILD_DIR%\docs"

echo.
echo [Step 3/10] Building frontend production bundle...
cd frontend
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Frontend build failed!
    pause
    exit /b 1
)
cd ..

echo.
echo [Step 4/10] Copying backend files...
echo Copying Python source files...
xcopy /E /I /Y /Q backend\*.py "%BUILD_DIR%\backend\" >nul
xcopy /E /I /Y /Q backend\actions "%BUILD_DIR%\backend\actions" >nul
xcopy /E /I /Y /Q backend\auth "%BUILD_DIR%\backend\auth" >nul
xcopy /E /I /Y /Q backend\models "%BUILD_DIR%\backend\models" >nul
xcopy /E /I /Y /Q backend\plugins "%BUILD_DIR%\backend\plugins" >nul
xcopy /E /I /Y /Q backend\routes "%BUILD_DIR%\backend\routes" >nul
xcopy /E /I /Y /Q backend\utils "%BUILD_DIR%\backend\utils" >nul
xcopy /E /I /Y /Q backend\integrations "%BUILD_DIR%\backend\integrations" >nul

echo Copying backend data...
xcopy /E /I /Y /Q backend\data\templates "%BUILD_DIR%\backend\data\templates" >nul
xcopy /E /I /Y /Q backend\Assets "%BUILD_DIR%\backend\Assets" >nul
xcopy /E /I /Y /Q backend\Avatars "%BUILD_DIR%\backend\Avatars" >nul

echo Copying backend config...
copy /Y backend\requirements.txt "%BUILD_DIR%\backend\" >nul
copy /Y backend\env.example "%BUILD_DIR%\backend\.env" >nul
copy /Y backend\config.py "%BUILD_DIR%\backend\" >nul

echo.
echo [Step 5/10] Copying frontend production build...
xcopy /E /I /Y /Q frontend\dist "%BUILD_DIR%\frontend\dist" >nul
copy /Y frontend\package.json "%BUILD_DIR%\frontend\" >nul
copy /Y frontend\package-lock.json "%BUILD_DIR%\frontend\" >nul

echo.
echo [Step 6/10] Copying documentation...
copy /Y README.md "%BUILD_DIR%\" >nul
copy /Y LICENSE "%BUILD_DIR%\" >nul
xcopy /E /I /Y /Q docs "%BUILD_DIR%\docs" >nul

echo.
echo [Step 7/10] Creating portable launcher...
(
echo @echo off
echo REM VDock Portable Launcher
echo REM Auto-setup and launch script
echo.
echo title VDock Virtual Stream Deck
echo color 0B
echo echo ========================================
echo echo    VDock Virtual Stream Deck
echo echo    Portable Edition
echo echo ========================================
echo echo.
echo.
echo REM Check Python
echo echo [1/7] Checking Python installation...
echo python --version ^>nul 2^>^&1
echo if %%ERRORLEVEL%% NEQ 0 ^(
echo     echo ERROR: Python 3.8+ is required but not found!
echo     echo.
echo     echo Please install Python from: https://www.python.org/downloads/
echo     echo Make sure to check "Add Python to PATH" during installation.
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Check Node.js
echo echo [2/7] Checking Node.js installation...
echo node --version ^>nul 2^>^&1
echo if %%ERRORLEVEL%% NEQ 0 ^(
echo     echo ERROR: Node.js 16+ is required but not found!
echo     echo.
echo     echo Please install Node.js from: https://nodejs.org/
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Setup virtual environment
echo echo [3/7] Setting up Python virtual environment...
echo if not exist "backend\venv" ^(
echo     echo Creating virtual environment...
echo     cd backend
echo     python -m venv venv
echo     if %%ERRORLEVEL%% NEQ 0 ^(
echo         echo ERROR: Failed to create virtual environment!
echo         pause
echo         exit /b 1
echo     ^)
echo     cd ..
echo ^)
echo.
echo REM Install Python dependencies
echo echo [4/7] Installing Python dependencies...
echo if not exist "backend\venv\Lib\site-packages\flask" ^(
echo     echo This may take a few minutes on first run...
echo     cd backend
echo     call venv\Scripts\activate.bat
echo     pip install -r requirements.txt ^>nul 2^>^&1
echo     if %%ERRORLEVEL%% NEQ 0 ^(
echo         echo ERROR: Failed to install Python dependencies!
echo         deactivate
echo         cd ..
echo         pause
echo         exit /b 1
echo     ^)
echo     deactivate
echo     cd ..
echo ^) else ^(
echo     echo Dependencies already installed.
echo ^)
echo.
echo REM Install Node.js dependencies  
echo echo [5/7] Installing frontend dependencies...
echo if not exist "frontend\node_modules" ^(
echo     echo This may take a few minutes on first run...
echo     cd frontend
echo     call npm install ^>nul 2^>^&1
echo     if %%ERRORLEVEL%% NEQ 0 ^(
echo         echo ERROR: Failed to install Node.js dependencies!
echo         cd ..
echo         pause
echo         exit /b 1
echo     ^)
echo     cd ..
echo ^) else ^(
echo     echo Dependencies already installed.
echo ^)
echo.
echo REM Start backend
echo echo [6/7] Starting backend server...
echo start "VDock Backend" cmd /c "cd /d %%~dp0backend ^&^& call venv\Scripts\activate.bat ^&^& python app.py ^&^& pause"
echo.
echo REM Wait for backend
echo echo Waiting for backend to initialize...
echo timeout /t 5 /nobreak ^>nul
echo.
echo REM Start frontend
echo echo [7/7] Starting frontend server...
echo start "VDock Frontend" cmd /c "cd /d %%~dp0frontend ^&^& npm run dev ^&^& pause"
echo.
echo REM Wait and open browser
echo echo.
echo echo ========================================
echo echo    VDock is starting up!
echo echo ========================================
echo echo.
echo echo Backend:  http://localhost:5000
echo echo Frontend: http://localhost:3000
echo echo.
echo echo Default login: admin / admin
echo echo.
echo echo Waiting for servers to be ready...
echo timeout /t 3 /nobreak ^>nul
echo.
echo echo Opening VDock in your browser...
echo start http://localhost:3000
echo.
echo echo.
echo echo ========================================
echo echo    VDock launched successfully!
echo echo ========================================
echo echo.
echo echo Both servers are running in separate windows.
echo echo To stop VDock: Close both server windows
echo echo.
echo echo This window can be closed safely.
echo echo.
echo echo Press any key to exit...
echo pause ^>nul
) > "%BUILD_DIR%\launch.bat"

echo.
echo [Step 8/10] Creating README for portable version...
(
echo # VDock Portable Edition
echo.
echo ## Quick Start
echo.
echo 1. Extract this folder anywhere on your computer
echo 2. Double-click `launch.bat`
echo 3. Wait for installation ^(first launch only^)
echo 4. VDock will open in your browser
echo.
echo **Default Login:** admin / admin
echo.
echo ## Requirements
echo.
echo - Windows 10/11
echo - Python 3.8+ ^(https://www.python.org/downloads/^)
echo - Node.js 16+ ^(https://nodejs.org/^)
echo.
echo ## First Launch
echo.
echo The first time you run VDock, it will:
echo - Create a Python virtual environment
echo - Install required Python packages
echo - Install required Node.js packages
echo.
echo This takes 3-5 minutes. Subsequent launches are instant.
echo.
echo ## Stopping VDock
echo.
echo Close the two server windows ^(Backend and Frontend^)
echo.
echo ## Troubleshooting
echo.
echo ### "Python not found"
echo Install Python and ensure "Add to PATH" is checked
echo.
echo ### "Node not found"
echo Install Node.js from the official website
echo.
echo ### Port already in use
echo Close any programs using ports 5000 or 3000
echo.
echo ## Support
echo.
echo See `docs/` folder for detailed documentation
echo.
echo ---
echo.
echo **Version:** 1.0 Portable Edition
) > "%BUILD_DIR%\README-PORTABLE.txt"

echo.
echo [Step 9/10] Creating requirements info...
(
echo VDock Portable Edition - Requirements
echo ======================================
echo.
echo REQUIRED SOFTWARE:
echo.
echo 1. Python 3.8 or higher
echo    Download: https://www.python.org/downloads/
echo    IMPORTANT: Check "Add Python to PATH" during installation
echo.
echo 2. Node.js 16 or higher  
echo    Download: https://nodejs.org/
echo    LTS version recommended
echo.
echo DISK SPACE:
echo - Extracted: ~500 MB
echo - After first launch: ~1 GB ^(includes dependencies^)
echo.
echo INTERNET:
echo - Required only for first launch ^(downloads packages^)
echo - Not required for normal use
echo.
echo PORTS USED:
echo - Backend: 5000
echo - Frontend: 3000
echo.
echo Make sure these ports are not in use by other programs.
) > "%BUILD_DIR%\REQUIREMENTS.txt"

echo.
echo [Step 10/10] Creating zip archive...
cd "%ROOT_DIR%"

if %HAS_7ZIP% EQU 1 (
    echo Using 7-Zip compression...
    7z a -tzip "%ZIP_NAME%" "%BUILD_DIR%\*" -mx=9 >nul
) else (
    echo Using PowerShell compression...
    powershell -command "Compress-Archive -Path '%BUILD_DIR%\*' -DestinationPath '%ZIP_NAME%' -Force"
)

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create zip file!
    pause
    exit /b 1
)

echo.
echo ============================================
echo    Build Complete!
echo ============================================
echo.
echo Portable package created: %ZIP_NAME%
echo Build directory: %BUILD_DIR%\
echo.
echo You can now distribute %ZIP_NAME% to users.
echo.
echo Package contents:
dir /B "%BUILD_DIR%"
echo.
echo Package size:
for %%A in ("%ZIP_NAME%") do echo %%~zA bytes (%%~zAKB)
echo.
echo ============================================
echo.
pause

endlocal

