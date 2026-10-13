# Tiny authoring studio only. Native builds and other Blender studios own priority.
param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$blender = 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe'
if (-not (Test-Path -LiteralPath $blender)) { throw "Blender is missing: $blender" }
& python -B (Join-Path $PSScriptRoot 'process_guard.py') --launch
if ($LASTEXITCODE -ne 0) { throw 'Dealer studio held: another native tool or Blender is active.' }
if ($CheckOnly) { return }
$logRoot = Join-Path $repo 'tmp\dealer_presence_mcp'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$studio = Start-Process -FilePath $blender -ArgumentList @('--factory-startup','--python','tools/dealer_presence/mcp_bootstrap.py') -WorkingDirectory $repo -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'studio.log') -RedirectStandardError (Join-Path $logRoot 'studio.err.log') -PassThru
@{ pid=$studio.Id; bootstrap='tools/dealer_presence/mcp_bootstrap.py'; port=9897; started_utc=[DateTime]::UtcNow.ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logRoot 'launch.json') -Encoding UTF8
Write-Output "Dealer-only Blender studio started: PID $($studio.Id), MCP port 9897."
