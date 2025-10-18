@echo off
REM VDock Setup Script for Windows

echo ========================================
echo VDock Virtual Stream Deck Setup
echo ========================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8 or higher.
    pause
    exit /b 1
)
echo [OK] Python found

REM Check Node.js
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Please install Node.js 18 or higher.
    pause
    exit /b 1
)
echo [OK] Node.js found

echo.
echo ========================================
echo Setting up Backend
echo ========================================
cd backend

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install backend dependencies
echo Installing backend dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies
    pause
    exit /b 1
)

REM Copy .env file
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
)

cd ..

echo.
echo ========================================
echo Setting up Frontend
echo ========================================
cd frontend

REM Install frontend dependencies
echo Installing frontend dependencies...
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install frontend dependencies
    pause
    exit /b 1
)

REM Copy .env file
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
)

cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo.
echo 1. Backend:
echo    cd backend
echo    venv\Scripts\activate
echo    python app.py
echo.
echo 2. Frontend (in a new terminal):
echo    cd frontend
echo    npm run dev
echo.
echo 3. Or use the provided start scripts:
echo    - start_backend.bat
echo    - start_frontend.bat
echo.
echo Default login password: admin
echo (Change this in backend\.env)
echo.
pause

