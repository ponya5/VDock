# VDock Icon Generator
# Copies the official VDock icon from Assets folder

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$IconPath = Join-Path $ScriptDir "vdock-icon.ico"
$SourceIconPath = Join-Path $ScriptDir "..\backend\Assets\VdockIcon.ico"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VDock Icon Generator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if source icon exists
if (!(Test-Path $SourceIconPath)) {
    Write-Host "[ERROR] Source icon not found: $SourceIconPath" -ForegroundColor Red
    Write-Host "Please ensure the VdockIcon.ico file exists in backend/Assets/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Copying VDock icon from Assets..." -ForegroundColor Yellow

try {
    # Copy the icon from Assets folder
    Copy-Item -Path $SourceIconPath -Destination $IconPath -Force

    # Verify the copy was successful
    if (Test-Path $IconPath) {
        $sourceSize = (Get-Item $SourceIconPath).Length
        $destSize = (Get-Item $IconPath).Length

        if ($sourceSize -eq $destSize) {
            Write-Host "[SUCCESS] Icon copied successfully: vdock-icon.ico" -ForegroundColor Green
            Write-Host "  Source: $SourceIconPath" -ForegroundColor Gray
            Write-Host "  Destination: $IconPath" -ForegroundColor Gray
            Write-Host "  Size: $([math]::Round($destSize/1KB, 2)) KB" -ForegroundColor Gray
            Write-Host ""
            Write-Host "This icon contains:" -ForegroundColor Cyan
            Write-Host "  - Official VDock branding" -ForegroundColor Gray
            Write-Host "  - Professional icon design" -ForegroundColor Gray
            Write-Host "  - Compatible with Windows desktop shortcuts" -ForegroundColor Gray
            Write-Host ""
            Write-Host "Icon ready for use with PyInstaller and desktop shortcuts!" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Icon copy verification failed - file sizes don't match" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[ERROR] Icon copy failed - destination file not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Error copying icon: $_" -ForegroundColor Red
    exit 1
}
