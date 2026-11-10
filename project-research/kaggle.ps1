$ErrorActionPreference = 'Stop'
$installedKaggle = Get-Command kaggle -ErrorAction SilentlyContinue
$kaggleCommand = if ($installedKaggle) { $installedKaggle.Source } else { Join-Path $env:APPDATA 'Python\Python312\Scripts\kaggle.exe' }
if (-not (Test-Path -LiteralPath $kaggleCommand)) { throw 'Install the Kaggle CLI in your active environment: python -m pip install kaggle' }
& $kaggleCommand @args
exit $LASTEXITCODE
