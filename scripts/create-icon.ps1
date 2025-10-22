# VDock Icon Generator
# Creates an ICO file from a simple SVG/bitmap

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$IconPath = Join-Path $ScriptDir "vdock-icon.ico"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VDock Icon Generator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we can create the icon
Write-Host "Creating VDock icon..." -ForegroundColor Yellow

# Create icon using .NET
Add-Type -AssemblyName System.Drawing

# Create a bitmap
$bitmap = New-Object System.Drawing.Bitmap(256, 256)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.Clear([System.Drawing.Color]::White)

# Draw VDock icon (simple design)
$brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(50, 100, 200))
$pen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(30, 60, 150), 3)

# Draw a deck shape (rounded rectangle)
$graphics.FillRoundedRectangle($brush, 40, 40, 176, 176, 20, 20)
$graphics.DrawRoundedRectangle($pen, 40, 40, 176, 176, 20, 20)

# Draw button grid (4x4 buttons)
$buttonBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(100, 150, 255))
$buttonPen = New-Object System.Drawing.Pen([System.Drawing.Color]::White, 1)

$startX = 60
$startY = 60
$buttonSize = 35
$spacing = 5

for ($row = 0; $row -lt 4; $row++) {
    for ($col = 0; $col -lt 4; $col++) {
        $x = $startX + ($col * ($buttonSize + $spacing))
        $y = $startY + ($row * ($buttonSize + $spacing))

        $graphics.FillRectangle($buttonBrush, $x, $y, $buttonSize, $buttonSize)
        $graphics.DrawRectangle($buttonPen, $x, $y, $buttonSize, $buttonSize)
    }
}

$graphics.Dispose()

# Convert bitmap to icon and save
try {
    # Save as a temporary PNG first
    $tempPng = Join-Path $env:TEMP "vdock_icon_temp.png"
    $bitmap.Save($tempPng, [System.Drawing.Imaging.ImageFormat]::Png)

    # Create icon from bitmap
    $icon = [System.Drawing.Icon]::FromHandle($bitmap.GetHicon())
    $icon.Save($IconPath)
    $icon.Dispose()

    Remove-Item $tempPng -Force -ErrorAction SilentlyContinue

    Write-Host "✓ Icon created successfully: vdock-icon.ico" -ForegroundColor Green
    Write-Host "  Location: $IconPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "This icon features:" -ForegroundColor Cyan
    Write-Host "  - Blue gradient background (VDock theme)" -ForegroundColor Gray
    Write-Host "  - 4x4 button grid (representing Stream Deck layout)" -ForegroundColor Gray
    Write-Host "  - Scalable for various sizes" -ForegroundColor Gray
} catch {
    Write-Host "✗ Error creating icon: $_" -ForegroundColor Red
    exit 1
} finally {
    $bitmap.Dispose()
}

Write-Host ""
Write-Host "Icon ready for use with PyInstaller!" -ForegroundColor Green
Read-Host "Press Enter to exit"
