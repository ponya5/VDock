# Prints the port VDock's backend should use, starting from -Port.
#
# Keeps -Port when it is free or already served by a VDock backend; otherwise
# walks upward to the next free port. Mirrors find_free_port in setup.sh so
# Windows and macOS pick ports the same way.
param(
    [Parameter(Mandatory = $true)]
    [int]$Port
)

$highestValidPort = 65535

function Test-PortListening {
    param([int]$CandidatePort)

    $listeners = Get-NetTCPConnection -State Listen -LocalPort $CandidatePort -ErrorAction SilentlyContinue
    return [bool]$listeners
}

function Test-PortServesVdock {
    param([int]$CandidatePort)

    $healthUrl = "http://127.0.0.1:$CandidatePort/api/health"
    try {
        $response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri $healthUrl
    }
    catch {
        return $false
    }
    return $response.Content -match 'uptime_s'
}

$chosenPort = $Port
$portIsTakenByOtherApp = (Test-PortListening $chosenPort) -and -not (Test-PortServesVdock $chosenPort)

if ($portIsTakenByOtherApp) {
    do {
        $chosenPort++
    } while ((Test-PortListening $chosenPort) -and ($chosenPort -lt $highestValidPort))
}

Write-Output $chosenPort
