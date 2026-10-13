param([int]$Width=4096, [double]$DisplayMult=10, [string]$Review='preview4096', [string]$Views='')
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$raw=Join-Path $repo "tmp/sky_cohesion/raw_$Width.exr"
$mask=Join-Path $repo "tmp/sky_cohesion/raw_$Width.sign.exr"
$receipt=Join-Path $repo "tmp/sky_cohesion/raw_$Width.render.json"
if (!(Test-Path $receipt) -or !(Test-Path $raw) -or !(Test-Path $mask)) { throw 'Render and paired sign AOV must finish first' }
if ((Get-Item $mask).LastWriteTime -lt (Get-Item $raw).LastWriteTime.AddSeconds(-10)) { throw 'Stale sign AOV' }
$preview=Join-Path $repo "art/sky3d/cohesion_review/$Review"
$out=Join-Path $repo "tmp/sky_cohesion/finished_$Width.exr"
$filterArgs=@()
if ($Views) { $filterArgs=@('--views',$Views) }
& 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -b --factory-startup -P (Join-Path $repo 'tools/sky3d/finish_sky.py') -- --in $raw --sign-mask $mask --out $out --preview-dir $preview --tag cohesion --target-score 0.64 --white 1 --knee-w 0.70 --knee-max-w 1 --display-mult $DisplayMult --sat 1.2 --roll 0 @filterArgs
if ($LASTEXITCODE -ne 0) { throw "Sky finish failed: $LASTEXITCODE" }
