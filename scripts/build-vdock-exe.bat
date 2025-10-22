@echo off
echo ========================================
echo VDock Executable Builder
echo ========================================
echo.

REM Check if PyInstaller is installed
echo [1/3] Checking PyInstaller installation...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo   Installing PyInstaller...
    pip install pyinstaller --upgrade
    if errorlevel 1 (
        echo   Error: Failed to install PyInstaller
        pause
        exit /b 1
    )
    echo   ✓ PyInstaller installed
) else (
    echo   ✓ PyInstaller found
)
echo.

REM Build launcher executable
echo [2/3] Building VDock-Launcher.exe...
pyinstaller --onefile --windowed --name=VDock-Launcher --distpath=dist --workpath=dist\build --noupx VDock-Launcher.py

if errorlevel 1 (
    echo   Error: Build failed
    pause
    exit /b 1
)
echo   ✓ Executable built successfully
echo.

REM Verify output
echo [3/3] Verifying build...
if exist "dist\VDock-Launcher.exe" (
    echo   ✓ VDock-Launcher.exe created successfully
    echo   Location: %CD%\dist\VDock-Launcher.exe
) else (
    echo   Error: Build verification failed
    pause
    exit /b 1
)
echo.

echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable ready at: %CD%\dist\VDock-Launcher.exe
echo.
echo You can now:
echo 1. Copy VDock-Launcher.exe to your VDock directory
echo 2. Create a shortcut on your desktop
echo 3. Pin it to your taskbar
echo.
pause
