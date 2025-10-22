# VDock Launcher Builder Script
# Builds VDock-Launcher.exe using PyInstaller

param(
    [switch]$WithIcon = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VDock Launcher Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$LauncherScript = Join-Path $ProjectRoot "VDock-Launcher.py"
$OutputDir = Join-Path $ProjectRoot "dist"
$IconPath = Join-Path $ProjectRoot "scripts\vdock-icon.ico"

# Check if PyInstaller is installed
Write-Host "[1/3] Checking PyInstaller installation..." -ForegroundColor Yellow
try {
    $pyinstallerVersion = pip show pyinstaller | Select-String "Version" | ForEach-Object { $_ -split ":" | Select-Object -Last 1 }
    Write-Host "  ✓ PyInstaller found: $($pyinstallerVersion.Trim())" -ForegroundColor Green
} catch {
    Write-Host "  ✗ PyInstaller not found" -ForegroundColor Red
    Write-Host "  Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller --upgrade
    Write-Host "  ✓ PyInstaller installed" -ForegroundColor Green
}
Write-Host ""

# Build launcher executable
Write-Host "[2/3] Building VDock-Launcher.exe..." -ForegroundColor Yellow

$pyinstallerArgs = @(
    "--onefile",
    "--windowed",
    "--name=VDock-Launcher",
    "--distpath=$OutputDir",
    "--specpath=$OutputDir\build",
    "--buildpath=$OutputDir\build",
    "--noupx"
)

# Add icon if provided
if ($WithIcon -and (Test-Path $IconPath)) {
    $pyinstallerArgs += "--icon=$IconPath"
    Write-Host "  Using custom icon: vdock-icon.ico" -ForegroundColor Gray
}

$pyinstallerArgs += $LauncherScript

# Run PyInstaller
$pyinstallerPath = (Get-Command pyinstaller -ErrorAction SilentlyContinue).Source
if ($pyinstallerPath) {
    & $pyinstallerPath @pyinstallerArgs
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Executable built successfully" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Build failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✗ PyInstaller command not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verify output
Write-Host "[3/3] Verifying build..." -ForegroundColor Yellow
$exePath = Join-Path $OutputDir "VDock-Launcher.exe"
if (Test-Path $exePath) {
    $fileSize = (Get-Item $exePath).Length / 1MB
    Write-Host "  ✓ VDock-Launcher.exe created" -ForegroundColor Green
    Write-Host "    Location: $exePath" -ForegroundColor Gray
    Write-Host "    Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Gray
} else {
    Write-Host "  ✗ Build verification failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Launcher executable ready at:" -ForegroundColor Cyan
Write-Host "  $exePath" -ForegroundColor White
Write-Host ""
Write-Host "You can now:" -ForegroundColor Yellow
Write-Host "1. Copy VDock-Launcher.exe to your VDock directory" -ForegroundColor Gray
Write-Host "2. Create a shortcut on your desktop" -ForegroundColor Gray
Write-Host "3. Pin it to your taskbar" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to exit"
