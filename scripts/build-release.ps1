# Full release pipeline: freeze backend -> build frontend -> electron-builder.
# Produces installer artifacts in frontend/electron/dist-electron/.
# Prerequisites: setup.bat already ran (backend/venv + frontend/node_modules
# + frontend/electron/node_modules must exist).

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VDock Release Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Freeze the backend (PyInstaller onedir -> dist/vdock-backend)
Write-Host ""
Write-Host "[1/3] Freezing backend..." -ForegroundColor Yellow
& (Join-Path $ScriptDir "build-backend.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 2. Build the frontend SPA (frontend/dist — served by the frozen backend)
Write-Host ""
Write-Host "[2/3] Building frontend..." -ForegroundColor Yellow
Push-Location (Join-Path $ProjectRoot "frontend")
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

# 3. Package the Electron app (nsis + portable)
Write-Host ""
Write-Host "[3/3] Packaging Electron app..." -ForegroundColor Yellow
Push-Location (Join-Path $ProjectRoot "frontend\electron")
try {
    npx electron-builder
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Release build complete!" -ForegroundColor Green
Write-Host "Artifacts: frontend\electron\dist-electron\" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
