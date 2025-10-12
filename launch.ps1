# VDock Single Launch Button
# Starts both backend and frontend servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   VDock Virtual Stream Deck Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Checking virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup.bat first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[2/4] Starting Backend Server..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\Daniel\CursorRepo\VDock\backend"
    & "C:\Users\Daniel\CursorRepo\VDock\.venv\Scripts\Activate.ps1"
    python app.py
}

Write-Host "[3/4] Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "[4/4] Starting Frontend Server..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\Daniel\CursorRepo\VDock\frontend"
    npm run dev
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   VDock is starting up!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:5000" -ForegroundColor White
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Login: admin / admin" -ForegroundColor White
Write-Host ""

# Wait a moment for servers to start
Start-Sleep -Seconds 2

# Open browser
Write-Host "Opening VDock in your browser..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "VDock launched successfully!" -ForegroundColor Green
Write-Host "Both servers are running in background jobs." -ForegroundColor White
Write-Host ""
Write-Host "To stop the servers, press Ctrl+C or close this window." -ForegroundColor Yellow
Write-Host ""

# Keep the script running and show status
try {
    while ($true) {
        $backendStatus = if ($backendJob.State -eq "Running") { "Running" } else { "Stopped" }
        $frontendStatus = if ($frontendJob.State -eq "Running") { "Running" } else { "Stopped" }
        
        Write-Host "Backend: $backendStatus | Frontend: $frontendStatus" -ForegroundColor Gray
        Start-Sleep -Seconds 10
    }
} catch {
    Write-Host "Stopping VDock servers..." -ForegroundColor Yellow
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
    Write-Host "VDock stopped." -ForegroundColor Red
}
