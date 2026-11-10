$ErrorActionPreference = 'Stop'
$researchPython = if ($env:LEAGUE_PREDICTOR_PYTHON) { $env:LEAGUE_PREDICTOR_PYTHON } else { 'python' }
& $researchPython (Join-Path $PSScriptRoot 'riot_pilot.py') @args
exit $LASTEXITCODE
