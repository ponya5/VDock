<#
.SYNOPSIS
  Run the same checks CI runs, locally, in one command.

.DESCRIPTION
  backend pytest -> vue-tsc -> vitest -> production build.
  Prints one PASS/FAIL line per step and exits non-zero if any step failed.
  Uses backend\venv when present, otherwise `python` on PATH.

.EXAMPLE
  .\scripts\check.ps1
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'

$venvPython = Join-Path $backend 'venv\Scripts\python.exe'
$python = if (Test-Path $venvPython) { $venvPython } else { 'python' }

$results = @()

function Invoke-Step {
    param([string]$Name, [string]$Dir, [scriptblock]$Command)
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    Push-Location $Dir
    try {
        & $Command
        $ok = ($LASTEXITCODE -eq 0)
    } catch {
        Write-Host $_.Exception.Message -ForegroundColor Red
        $ok = $false
    } finally {
        Pop-Location
    }
    $script:results += [pscustomobject]@{ Step = $Name; Ok = $ok }
}

$env:PYTHONIOENCODING = 'utf-8'
Invoke-Step 'Backend tests (pytest)' $backend { & $python -m pytest tests -q }
Invoke-Step 'Type check (vue-tsc)'   $frontend { npx vue-tsc --noEmit }
Invoke-Step 'Frontend tests (vitest)' $frontend { npx vitest run }
Invoke-Step 'Build (vite)'           $frontend { npm run build }

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
foreach ($r in $results) {
    if ($r.Ok) { Write-Host ("PASS  {0}" -f $r.Step) -ForegroundColor Green }
    else       { Write-Host ("FAIL  {0}" -f $r.Step) -ForegroundColor Red }
}
if ($results | Where-Object { -not $_.Ok }) { exit 1 }
exit 0
