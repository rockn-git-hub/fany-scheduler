<#
.SYNOPSIS
指定したFANYランナーのサービス管理とGitHub登録解除
#>
[CmdletBinding()]
param(
    [ValidateSet('Status', 'Start', 'Stop', 'Restart', 'Remove')][string]$Action = 'Status',
    [string]$RunnerDirectory = 'C:\Codex\Runners\fany'
)
$ErrorActionPreference = 'Stop'
$servicePath = Join-Path $RunnerDirectory '.service'
if (-not (Test-Path -LiteralPath $servicePath)) { throw 'Runner service configuration not found.' }
$serviceName = [IO.File]::ReadAllText($servicePath).Trim()
switch ($Action) {
    'Start' { Start-Service -Name $serviceName }
    'Stop' { Stop-Service -Name $serviceName }
    'Restart' { Restart-Service -Name $serviceName }
    'Remove' {
        Stop-Service -Name $serviceName
        $response = & gh api --method POST repos/rockn-git-hub/fany-scheduler/actions/runners/remove-token
        if ($LASTEXITCODE -ne 0) { throw 'Cannot obtain runner removal token.' }
        $removalToken = (($response -join "`n") | ConvertFrom-Json).token
        Push-Location $RunnerDirectory
        try {
            & .\config.cmd remove --unattended --token $removalToken
            if ($LASTEXITCODE -ne 0) { throw 'Runner removal failed.' }
        } finally {
            $removalToken = $null
            Pop-Location
        }
        return
    }
}
Get-Service -Name $serviceName | Select-Object Name, Status, StartType

