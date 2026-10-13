# Explicitly requested interactive preview. File loads can reset Rendered mode.
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList @('art/sky3d/middle_ground_preview.blend','--python','tools/sky_middle_ground/activate_preview.py') -WorkingDirectory $repo -WindowStyle Normal
