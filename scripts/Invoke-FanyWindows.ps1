<#
.SYNOPSIS
Windowsランナー上で専用Python環境を用意して公演情報を取得
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
if (-not $env:FANY_PYTHON -or -not (Test-Path -LiteralPath $env:FANY_PYTHON)) {
    throw 'FANY_PYTHON must identify the runner Python executable.'
}
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$environmentDirectory = Join-Path $env:RUNNER_TOOL_CACHE 'fany-python-env'
$python = Join-Path $environmentDirectory 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    & $env:FANY_PYTHON -m venv $environmentDirectory
    if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed.' }
}
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUNBUFFERED = '1'
Push-Location $repositoryRoot
try {
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & $python kinzoku_fany.py
    if ($LASTEXITCODE -ne 0) { throw 'FANY retrieval failed; publication and notification withheld.' }
} finally {
    Pop-Location
}

