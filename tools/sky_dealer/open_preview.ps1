# Explicitly requested interactive preview. File loads can reset Rendered mode.
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $PSScriptRoot 'resource_guard.ps1')
Assert-SkyResourceSlot 'Sky preview'
Assert-NoOtherBlender
$preview=Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList @('art/sky3d/dealer_preview.blend','--python','tools/sky_dealer/activate_preview.py') -WorkingDirectory $repo -WindowStyle Normal -PassThru
Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'watch_studio.ps1'),'-OwnedProcessId',$preview.Id,'-StartFileTime',$preview.StartTime.ToFileTimeUtc()) -WindowStyle Hidden | Out-Null
