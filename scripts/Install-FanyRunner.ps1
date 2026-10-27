<#
.SYNOPSIS
管理者PowerShellからFANY専用ランナーをWindowsサービスとして登録
#>
[CmdletBinding()]
param(
    [string]$RunnerDirectory = 'C:\Codex\Runners\fany',
    [string]$RunnerName = ('fany-' + $env:COMPUTERNAME.ToLowerInvariant()),
    [string]$RunnerLabel = 'fany-windows',
    [Parameter(Mandatory = $true)][string]$PythonExecutable
)
$ErrorActionPreference = 'Stop'
$principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script from an administrator PowerShell.'
}
if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) { throw 'Python executable not found.' }
if (Test-Path -LiteralPath $RunnerDirectory) { throw 'Choose a new, empty runner directory.' }
$repository = 'rockn-git-hub/fany-scheduler'
$account = & gh api user --jq .login
if ($LASTEXITCODE -ne 0 -or $account -ne 'rockn-git-hub') { throw 'Sign in to gh as rockn-git-hub first.' }
$packageResponse = & gh api "repos/$repository/actions/runners/downloads"
if ($LASTEXITCODE -ne 0) { throw 'Cannot obtain official runner package.' }
$packages = ($packageResponse -join "`n") | ConvertFrom-Json
$package = @($packages | Where-Object { $_.os -eq 'win' -and $_.architecture -eq 'x64' })
if (@($package).Count -ne 1) { throw 'Expected exactly one Windows x64 runner package.' }
New-Item -ItemType Directory -Path $RunnerDirectory | Out-Null
$archive = Join-Path $RunnerDirectory $package.filename
Invoke-WebRequest -Uri $package.download_url -OutFile $archive
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $package.sha256_checksum) {
    throw 'Runner package checksum mismatch.'
}
Expand-Archive -LiteralPath $archive -DestinationPath $RunnerDirectory
# サービス専用のPythonコピーによるユーザープロファイルへの依存の除去
$runtimeDirectory = Join-Path $RunnerDirectory 'python'
Copy-Item -LiteralPath (Split-Path -Parent $PythonExecutable) -Destination $runtimeDirectory -Recurse
$servicePython = Join-Path $runtimeDirectory 'python.exe'
& $servicePython -c 'import sys, venv, ssl; print(sys.version)'
if ($LASTEXITCODE -ne 0) { throw 'Copied Python runtime is not usable.' }
$environmentText = "FANY_PYTHON=$servicePython`r`nPYTHONIOENCODING=utf-8`r`nPYTHONDONTWRITEBYTECODE=1`r`n"
[IO.File]::WriteAllText((Join-Path $RunnerDirectory '.env'), $environmentText, [Text.UTF8Encoding]::new($false))
$tokenResponse = & gh api --method POST "repos/$repository/actions/runners/registration-token"
if ($LASTEXITCODE -ne 0) { throw 'Cannot obtain runner registration token.' }
$registrationToken = (($tokenResponse -join "`n") | ConvertFrom-Json).token
Push-Location $RunnerDirectory
try {
    & .\config.cmd --unattended --url "https://github.com/$repository" --token $registrationToken --name $RunnerName --labels $RunnerLabel --work '_work' --runasservice --windowslogonaccount 'NT AUTHORITY\NETWORK SERVICE'
    if ($LASTEXITCODE -ne 0) { throw 'Runner configuration failed.' }
} finally {
    $registrationToken = $null
    Pop-Location
}
$serviceName = [IO.File]::ReadAllText((Join-Path $RunnerDirectory '.service')).Trim()
Set-Service -Name $serviceName -StartupType Automatic
Start-Service -Name $serviceName
Get-Service -Name $serviceName | Select-Object Name, Status, StartType

