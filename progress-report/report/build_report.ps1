param([string]$OutputDirectory = (Join-Path $PSScriptRoot '..\..\output\pdf'))
$ErrorActionPreference = 'Stop'
$pdflatexCommand = Get-Command pdflatex -ErrorAction SilentlyContinue
$bibtexCommand = Get-Command bibtex -ErrorAction SilentlyContinue
if ($pdflatexCommand -and $bibtexCommand) {
    $latexExecutable = $pdflatexCommand.Source
    $bibtexExecutable = $bibtexCommand.Source
} else {
    $latexExecutable = Join-Path $env:LOCALAPPDATA 'Programs\MiKTeX\miktex\bin\x64\pdflatex.exe'
    $bibtexExecutable = Join-Path $env:LOCALAPPDATA 'Programs\MiKTeX\miktex\bin\x64\bibtex.exe'
}
if (-not (Test-Path -LiteralPath $latexExecutable)) { throw 'Install LaTeX/MiKTeX or add pdflatex and bibtex to PATH.' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$resolvedOutput = (Resolve-Path -LiteralPath $OutputDirectory).Path
$buildDirectory = Join-Path $resolvedOutput 'latex-build'
New-Item -ItemType Directory -Path $buildDirectory -Force | Out-Null
Push-Location $PSScriptRoot
try {
    & $latexExecutable --enable-installer -interaction=nonstopmode -halt-on-error "-output-directory=$buildDirectory" main.tex
    if ($LASTEXITCODE -ne 0) { throw 'First LaTeX pass failed; inspect main.log.' }
    # BibTeX resolves the bibliography and the copied ACL style relative to this source folder.
    & $bibtexExecutable (Join-Path $buildDirectory 'main')
    if ($LASTEXITCODE -ne 0) { throw 'Bibliography build failed.' }
    1..2 | ForEach-Object {
        & $latexExecutable --enable-installer -interaction=nonstopmode -halt-on-error "-output-directory=$buildDirectory" main.tex
        if ($LASTEXITCODE -ne 0) { throw 'LaTeX reference-resolution pass failed.' }
    }
    Copy-Item -LiteralPath (Join-Path $buildDirectory 'main.pdf') -Destination (Join-Path $resolvedOutput 'Group27_ProgressReport_DRAFT.pdf') -Force
    Write-Output (Join-Path $resolvedOutput 'Group27_ProgressReport_DRAFT.pdf')
} finally { Pop-Location }
