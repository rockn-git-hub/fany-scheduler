<#
.SYNOPSIS
GitHub PagesのHTML反映を確認してから一覧URLをLINEへ送信
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$pageUrl = 'https://rockn-git-hub.github.io/fany-scheduler/kinzoku_bat_events.html'
$htmlPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'kinzoku_bat_events.html'
$expected = [IO.File]::ReadAllText($htmlPath).Replace("`r`n", "`n")
$published = $false
for ($attempt = 0; $attempt -lt 40; $attempt++) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $pageUrl -Headers @{ 'Cache-Control' = 'no-cache' } -TimeoutSec 20
        if ($response.Content.Replace("`r`n", "`n") -ceq $expected) {
            $published = $true
            break
        }
    } catch {
        Write-Output ('Page verification pending: ' + $attempt)
    }
    Start-Sleep -Seconds 5
}
if (-not $published) { throw 'Published HTML does not match; LINE notification withheld.' }
if (-not $env:LINE_TOKEN -or -not $env:LINE_TO) { throw 'LINE credentials are missing.' }
# PowerShell 5.1での日本語リテラル読取りに依存しない通知文の取得
$python = Join-Path $env:RUNNER_TOOL_CACHE 'fany-python-env\Scripts\python.exe'
$messageFile = Join-Path $env:RUNNER_TEMP 'fany-line-message.json'
& $python (Join-Path $PSScriptRoot 'line_message.py') $messageFile
if ($LASTEXITCODE -ne 0) { throw 'Notification payload creation failed.' }
$payload = [IO.File]::ReadAllBytes($messageFile)
$result = Invoke-RestMethod -Uri 'https://api.line.me/v2/bot/message/push' -Method Post -Headers @{ Authorization = ('Bearer ' + $env:LINE_TOKEN) } -ContentType 'application/json; charset=utf-8' -Body $payload -TimeoutSec 30
if (@($result.sentMessages).Count -ne 1) { throw 'Unexpected LINE response.' }
Write-Output 'Published HTML verified; LINE accepted one message.'
Write-Output ('Sent at: ' + [DateTimeOffset]::Now.ToString('o'))
