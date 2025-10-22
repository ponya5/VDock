@echo off
REM VDock Single Launch Button
REM Starts both backend and frontend servers

echo ========================================
echo    VDock Virtual Stream Deck Launcher
echo ========================================
echo.

echo [1/5] Checking virtual environment...
if not exist "backend\venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

echo [2/5] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo [3/5] Starting Backend Server...
start "VDock Backend" cmd /c "cd /d %~dp0backend && call venv\Scripts\activate.bat && python app.py && pause"

echo [4/5] Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo [5/5] Starting Frontend Server...
start "VDock Frontend" cmd /c "cd /d %~dp0frontend && npm run dev && pause"

echo.
echo ========================================
echo    VDock is starting up!
echo ========================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Login: admin / admin
echo.
echo Waiting for servers to be ready...
timeout /t 3 /nobreak >nul

echo Opening VDock in your browser...
start http://localhost:3000

echo.
echo ========================================
echo    VDock launched successfully!
echo ========================================
echo.
echo Both servers are running in separate windows.
echo Backend window: Shows server logs and status
echo Frontend window: Shows development server info
echo.
echo To stop VDock: Close both server windows
echo.
echo Press any key to exit this launcher...
pause >nul
