$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $repo 'tools/sky_depth/resource_guard.ps1')
Assert-SkyResourceSlot 'Alarm glass preview'
Assert-NoOtherBlender
$blend=Join-Path $repo 'art/crown_alarm/lens_review/native_preview.blend'
if (!(Test-Path -LiteralPath $blend)) { throw 'Reviewed native-model preview is missing' }
$receipt=Get-Content -LiteralPath (Join-Path $repo 'art/crown_alarm/lens_review/preview.json') -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $blend -Algorithm SHA256).Hash.ToLowerInvariant() -ne $receipt.native_preview_sha256) { throw 'Reviewed preview does not match its receipt' }
$env:PYTHONDONTWRITEBYTECODE='1'
# The user explicitly requested a visible Blender material preview.
$studio=Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList @(('"'+$blend+'"'),'--python','tools/crown_alarm/configure_lens_preview.py','--','--alarm-preview') -WorkingDirectory $repo -WindowStyle Normal -RedirectStandardOutput (Join-Path $repo 'tmp/alarm_lens_repair/visible_preview.log') -RedirectStandardError (Join-Path $repo 'tmp/alarm_lens_repair/visible_preview.err') -PassThru
$watch=Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $repo 'tools/sky_depth/watch_studio.ps1'),'-OwnedProcessId',$studio.Id,'-StartFileTime',$studio.StartTime.ToFileTimeUtc()) -WindowStyle Hidden -PassThru
[pscustomobject]@{pid=$studio.Id;start_filetime=$studio.StartTime.ToFileTimeUtc();watcher=$watch.Id;port=9885;mode='reviewed native-model Rendered preview'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $repo 'tmp/alarm_lens_repair/visible_process.json')
Get-Content -LiteralPath (Join-Path $repo 'tmp/alarm_lens_repair/visible_process.json')
