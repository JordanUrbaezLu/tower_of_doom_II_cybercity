# Explicitly requested interactive preview. File loads can reset Rendered mode.
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList @('art/sky3d/consistency_preview.blend','--python','tools/sky_consistency/activate_preview.py') -WorkingDirectory $repo -WindowStyle Normal
