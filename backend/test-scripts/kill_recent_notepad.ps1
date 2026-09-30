$recent = Get-Process Notepad -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-15) }
$recent | Select-Object Id, StartTime | Format-Table -AutoSize
$recent | Stop-Process -Force
Write-Host "killed $($recent.Count) recent notepad process(es)"
