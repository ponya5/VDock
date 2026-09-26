# Freeze the VDock backend into dist/vdock-backend/ via PyInstaller.
# Output is consumed by electron-builder's extraResources (packaged app)
# and is also runnable standalone. Requires backend/venv — run setup.bat first.

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$VenvPython = Join-Path $BackendDir "venv\Scripts\python.exe"
$DistDir = Join-Path $ProjectRoot "dist"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VDock Backend Freeze (PyInstaller)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-not (Test-Path $VenvPython)) {
    Write-Host "ERROR: backend venv not found at $VenvPython" -ForegroundColor Red
    Write-Host "Run setup.bat first." -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/2] Installing build dependencies..." -ForegroundColor Yellow
& $VenvPython -m pip install -q -r (Join-Path $BackendDir "requirements-build.txt")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/2] Running PyInstaller spec..." -ForegroundColor Yellow
Push-Location $BackendDir
try {
    & $VenvPython -m PyInstaller vdock-backend.spec `
        --distpath $DistDir --workpath "$DistDir\build" --noconfirm
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

$exe = Join-Path $DistDir "vdock-backend\vdock-backend.exe"
if (Test-Path $exe) {
    Write-Host ""
    Write-Host "OK - frozen backend at $exe" -ForegroundColor Green
} else {
    Write-Host "ERROR: expected output missing: $exe" -ForegroundColor Red
    exit 1
}
