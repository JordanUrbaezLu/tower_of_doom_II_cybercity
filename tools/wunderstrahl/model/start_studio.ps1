# Wunderstrahl model studio: a VISIBLE Blender 4.2 window with the MCP server on loopback 9893 (docs/219).
# Guarded: refuses while the game, a Radiant bake, cod2map, the linker or gdtdb runs (16 GB workstation), or while
# something already listens on 9893. Never closes anything it did not start.
param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$blender = 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe'
if (-not (Test-Path -LiteralPath $blender)) { throw "Blender 4.2 is missing: $blender" }
$busy = Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -like 'Radiant*' -or $_.ProcessName -like 'BlackOps3*' -or $_.ProcessName -like 'cod2map*' -or
    $_.ProcessName -like 'linker*' -or $_.ProcessName -like 'gdtdb*' }
if ($busy) { throw ('Wunderstrahl studio held: ' + (($busy | ForEach-Object { $_.ProcessName }) -join ', ')) }
$listen = Get-NetTCPConnection -LocalPort 9893 -State Listen -ErrorAction SilentlyContinue
if ($listen) { throw 'Port 9893 is already listening (a Wunderstrahl studio is probably open already).' }
if ($CheckOnly) { Write-Output 'WUNDERSTRAHL_STUDIO_GUARD_CLEAR'; return }
$logRoot = Join-Path $repo 'tmp\wunderstrahl\mcp'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$studio = Start-Process -FilePath $blender -ArgumentList @('--factory-startup', '--python', 'tools/wunderstrahl/model/mcp_bootstrap.py') `
    -WorkingDirectory $repo -RedirectStandardOutput (Join-Path $logRoot 'studio.log') `
    -RedirectStandardError (Join-Path $logRoot 'studio.err.log') -PassThru
@{ pid = $studio.Id; bootstrap = 'tools/wunderstrahl/model/mcp_bootstrap.py'; port = 9893; started_utc = [DateTime]::UtcNow.ToString('o') } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logRoot 'launch.json') -Encoding UTF8
Write-Output "Wunderstrahl Blender studio started: PID $($studio.Id), MCP port 9893 (visible window)."
