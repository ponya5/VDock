# VDock Installer Build Script
# This script creates a Windows installer for VDock

param(
    [switch]$BuildNSIS = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VDock Installer Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $DistDir "VDock-Portable"

# Create distribution directory
Write-Host "[1/4] Creating distribution directory..." -ForegroundColor Yellow
if (Test-Path $DistDir) {
    Remove-Item $DistDir -Recurse -Force
}
New-Item -ItemType Directory -Path $BuildDir | Out-Null
Write-Host "  ✓ Distribution directory created at: $BuildDir" -ForegroundColor Green
Write-Host ""

# Copy application files
Write-Host "[2/4] Copying application files..." -ForegroundColor Yellow
$copyItems = @(
    "backend",
    "frontend",
    "docs",
    "scripts",
    "launch.bat",
    "launch.ps1",
    "launch.sh",
    "install.bat",
    "install.sh",
    "README.md",
    "LICENSE",
    "docker-compose.yml"
)

foreach ($item in $copyItems) {
    $sourcePath = Join-Path $ProjectRoot $item
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $BuildDir $item
        if ((Get-Item $sourcePath).PSIsContainer) {
            Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force | Out-Null
        } else {
            Copy-Item -Path $sourcePath -Destination $destPath -Force | Out-Null
        }
        Write-Host "  ✓ Copied $item" -ForegroundColor Green
    }
}
Write-Host ""

# Create launcher script
Write-Host "[3/4] Creating VDock launcher scripts..." -ForegroundColor Yellow

# PowerShell launcher wrapper
$psLauncher = @'
# VDock PowerShell Launcher
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendPath = Join-Path $ScriptRoot "backend"
$FrontendPath = Join-Path $ScriptRoot "frontend"

Write-Host "Starting VDock Virtual Stream Deck..." -ForegroundColor Cyan

# Check dependencies
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Host "ERROR: Python not found. Please install Python 3.8+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$npmPath = (Get-Command npm -ErrorAction SilentlyContinue).Source
if (-not $npmPath) {
    Write-Host "ERROR: Node.js (npm) not found. Please install Node.js" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Start services in separate windows
Write-Host "Starting Backend Server..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$BackendPath`" && call venv\Scripts\activate.bat && python app.py" -WindowStyle Normal

Write-Host "Waiting for backend initialization..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Starting Frontend Server..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$FrontendPath`" && npm run dev" -WindowStyle Normal

Write-Host "Waiting for servers to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Opening VDock in browser..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "VDock is starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Backend:  http://localhost:5000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Login: admin / admin" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close this window"
'@

$psLauncherPath = Join-Path $BuildDir "Launch-VDock.ps1"
Set-Content -Path $psLauncherPath -Value $psLauncher
Write-Host "  ✓ Created PowerShell launcher: Launch-VDock.ps1" -ForegroundColor Green

# Create batch launcher wrapper
$batLauncher = @"
@echo off
REM VDock Launcher
setlocal enabledelayedexpansion

REM Get script directory
set SCRIPT_DIR=%~dp0

echo ========================================
echo    VDock Virtual Stream Deck Launcher
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Node.js installation
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js
    pause
    exit /b 1
)

REM Check virtual environment
if not exist "!SCRIPT_DIR!backend\venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

echo [1/4] Starting Backend Server...
start "VDock Backend" cmd /c "cd /d !SCRIPT_DIR!backend && call venv\Scripts\activate.bat && python app.py && pause"

echo [2/4] Waiting for backend initialization...
timeout /t 5 /nobreak >nul

echo [3/4] Starting Frontend Server...
start "VDock Frontend" cmd /c "cd /d !SCRIPT_DIR!frontend && npm run dev && pause"

echo [4/4] Waiting for servers to be ready...
timeout /t 3 /nobreak >nul

echo Opening VDock in your browser...
start http://localhost:3000

echo.
echo ========================================
echo    VDock launched successfully!
echo ========================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Login: admin / admin
echo.
pause
"@

$batLauncherPath = Join-Path $BuildDir "Launch-VDock.bat"
Set-Content -Path $batLauncherPath -Value $batLauncher -Encoding ASCII
Write-Host "  ✓ Created Batch launcher: Launch-VDock.bat" -ForegroundColor Green
Write-Host ""

# Create setup instructions
Write-Host "[4/4] Creating setup documentation..." -ForegroundColor Yellow

$setupGuide = @"
# VDock Installation Guide

## Quick Start

1. **Extract the installer files** to your desired location
2. **Run `install.bat`** to set up dependencies
3. **Run `Launch-VDock.bat`** or `Launch-VDock.ps1`** to start VDock

## System Requirements

- Windows 10 or later
- Python 3.8+
- Node.js 16+
- Administrator privileges for first-time setup

## Default Login

- Username: `admin`
- Password: `admin`

## Accessing VDock

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000

## Troubleshooting

### Python/Node.js not found errors
Ensure Python and Node.js are installed and added to your system PATH.

### Port already in use
If ports 3000 or 5000 are busy, modify the configuration in:
- Backend: `backend/config.py`
- Frontend: `frontend/vite.config.js`

### Permission denied
Run the install.bat as Administrator (right-click > Run as administrator)

## Support
For issues, check the README.md or visit the project repository.
"@

$setupPath = Join-Path $BuildDir "SETUP_GUIDE.md"
Set-Content -Path $setupPath -Value $setupGuide
Write-Host "  ✓ Created setup guide: SETUP_GUIDE.md" -ForegroundColor Green
Write-Host ""

# Optional: Build NSIS installer
if ($BuildNSIS) {
    Write-Host "[5/5] Building NSIS installer (if available)..." -ForegroundColor Yellow
    $nsisPath = Get-Command makensis -ErrorAction SilentlyContinue
    if ($nsisPath) {
        Write-Host "  ✓ NSIS compiler found" -ForegroundColor Green
        # NSIS compilation would go here
    } else {
        Write-Host "  ⚠ NSIS compiler not found - skipping" -ForegroundColor Yellow
        Write-Host "    Download NSIS from: https://nsis.sourceforge.io/" -ForegroundColor Gray
    }
    Write-Host ""
}

# Create archive
Write-Host "Creating portable archive..." -ForegroundColor Yellow
$zipPath = Join-Path $DistDir "VDock-Portable.zip"
if (Get-Command Compress-Archive -ErrorAction SilentlyContinue) {
    Compress-Archive -Path $BuildDir -DestinationPath $zipPath -Force
    Write-Host "  ✓ Created: VDock-Portable.zip" -ForegroundColor Green
} else {
    Write-Host "  ⚠ PowerShell zip compression not available" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Distribution files available at:" -ForegroundColor Cyan
Write-Host "  $DistDir" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run install.bat in the VDock-Portable folder" -ForegroundColor Gray
Write-Host "2. Run Launch-VDock.bat to start the application" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to exit"
