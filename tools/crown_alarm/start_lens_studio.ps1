$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $repo 'tools/sky_depth/resource_guard.ps1')
Assert-SkyResourceSlot 'Alarm lens MCP studio'
Assert-NoOtherBlender
$env:PYTHONDONTWRITEBYTECODE='1'
$studio=Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList @('--factory-startup','--python','tools/crown_alarm/mcp_bootstrap.py') -WorkingDirectory $repo -WindowStyle Hidden -RedirectStandardOutput (Join-Path $repo 'tmp/alarm_lens_repair/studio.log') -RedirectStandardError (Join-Path $repo 'tmp/alarm_lens_repair/studio.err') -PassThru
$watch=Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $repo 'tools/sky_depth/watch_studio.ps1'),'-OwnedProcessId',$studio.Id,'-StartFileTime',$studio.StartTime.ToFileTimeUtc()) -WindowStyle Hidden -PassThru
[pscustomobject]@{pid=$studio.Id;start_filetime=$studio.StartTime.ToFileTimeUtc();watcher=$watch.Id;port=9885} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $repo 'tmp/alarm_lens_repair/studio_process.json')
Get-Content -LiteralPath (Join-Path $repo 'tmp/alarm_lens_repair/studio_process.json')
