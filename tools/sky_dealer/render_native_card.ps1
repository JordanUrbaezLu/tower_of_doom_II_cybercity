# Guarded entry point for the already-proven native-card renderer. Keep that
# renderer unchanged so earlier material-bake provenance remains truthful.
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $PSScriptRoot 'resource_guard.ps1')
$start=Get-Date
Invoke-SkyBlenderStage -BlenderArguments @('-b','tmp/sky_dealer/native_card_bake.blend','-P','tools/sky_dealer/render_native_card.py') -StageName 'Native sign material bake' -StdoutLog (Join-Path $repo 'tmp/sky_dealer/native_card_render.log') -StderrLog (Join-Path $repo 'tmp/sky_dealer/native_card_render.err') -Repo $repo
$receipt=Join-Path $repo 'art/sky3d/dealer_review/native_card_art.json'
if (!(Test-Path $receipt) -or (Get-Item $receipt).LastWriteTime -lt $start) { throw 'Native card renderer produced no fresh receipt; inspect its logs.' }
