param([Parameter(Mandatory=$true)][ValidateSet('before','after_old','after')][string]$Case)
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $PSScriptRoot 'resource_guard.ps1')
Assert-SkyResourceSlot 'Depth crop review'
Assert-NoOtherBlender
$blend=if ($Case -eq 'before') { 'art/sky3d/depth_review/before/tod2_sky.blend' } else { 'tmp/sky_depth/depth.blend' }
if (!(Test-Path -LiteralPath (Join-Path $repo $blend))) { throw 'Save the actual reviewed source master before crop rendering.' }
$cropArguments=@('-b',$blend,'-P','tools/sky_depth/render_quality.py','--',$Case)
Invoke-SkyBlenderStage -BlenderArguments $cropArguments -StageName "Depth crops $Case" -StdoutLog (Join-Path $repo "tmp/sky_depth/crops_$Case.log") -StderrLog (Join-Path $repo "tmp/sky_depth/crops_$Case.err") -Repo $repo
