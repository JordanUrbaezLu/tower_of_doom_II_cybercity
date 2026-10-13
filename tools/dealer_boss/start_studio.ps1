# Start the VISIBLE Dealer boss Blender studio (Blender 4.2: the PyCoD addon lives there).
param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$blender = 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe'
if (-not (Test-Path -LiteralPath $blender)) { throw "Blender is missing: $blender" }
$py = 'C:\Users\jorda\Repositories\tower_of_doom_II_hellbound\tmp\gold_sword_env\Scripts\python.exe'
& $py -B (Join-Path $PSScriptRoot 'process_guard.py')
if ($LASTEXITCODE -ne 0) { throw 'Dealer boss studio held: a native build stage, the game, or low memory.' }
if ($CheckOnly) { return }
$logRoot = Join-Path $repo 'tmp\dealer_boss_mcp'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$studio = Start-Process -FilePath $blender -ArgumentList @('--factory-startup','--python','tools/dealer_boss/mcp_bootstrap.py') -WorkingDirectory $repo -RedirectStandardOutput (Join-Path $logRoot 'studio.log') -RedirectStandardError (Join-Path $logRoot 'studio.err.log') -PassThru
@{ pid=$studio.Id; bootstrap='tools/dealer_boss/mcp_bootstrap.py'; port=9899; started_utc=[DateTime]::UtcNow.ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logRoot 'launch.json') -Encoding UTF8
Write-Output "Dealer boss Blender studio started (visible): PID $($studio.Id), MCP port 9899."
