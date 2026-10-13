# One sequential MCP session: inspect the saved master, author its small preview,
# then close it for the native build. Preview mode restores the saved display.
param([ValidateSet('master','preview')][string]$Mode='master')
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $PSScriptRoot 'resource_guard.ps1')
Assert-SkyResourceSlot 'Sky MCP studio'
Assert-NoOtherBlender
$blend=if ($Mode -eq 'master') { 'tmp/sky_dealer/dealer.blend' } else { 'art/sky3d/dealer_preview.blend' }
$launchArgs=@($blend,'--python','tools/sky_cohesion/mcp_bootstrap.py')
if ($Mode -eq 'preview') { $launchArgs+=@('--python','tools/sky_dealer/activate_preview.py') }
$env:PYTHONDONTWRITEBYTECODE='1'
$studio=Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList $launchArgs -WorkingDirectory $repo -WindowStyle Normal -PassThru -RedirectStandardOutput (Join-Path $repo 'tmp/sky_dealer/studio.log') -RedirectStandardError (Join-Path $repo 'tmp/sky_dealer/studio.err')
$watch=Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'watch_studio.ps1'),'-OwnedProcessId',$studio.Id,'-StartFileTime',$studio.StartTime.ToFileTimeUtc()) -WindowStyle Hidden -PassThru
$receipt=[pscustomobject]@{pid=$studio.Id;start_filetime=$studio.StartTime.ToFileTimeUtc();watcher_pid=$watch.Id;mode=$Mode;blend=$blend;port=9896}
$receipt | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $repo 'tmp/sky_dealer/studio_process.json') -Encoding UTF8
$receipt | ConvertTo-Json -Compress
