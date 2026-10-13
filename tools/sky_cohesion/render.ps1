param([int]$Width=8192,[int]$Samples=160)
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (Get-Process BlackOps3 -ErrorAction SilentlyContinue) { throw 'User match active; render must wait' }
$start=Get-Date
$render=Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList @('-b','tmp/sky_cohesion/cohesion.blend','-P','tools/sky_cohesion/render_saved.py','--',$Width,$Samples) -WorkingDirectory $repo -WindowStyle Hidden -RedirectStandardOutput (Join-Path $repo "tmp/sky_cohesion/render$Width.log") -RedirectStandardError (Join-Path $repo "tmp/sky_cohesion/render$Width.err") -PassThru
while (!$render.HasExited) {
    if (Get-Process BlackOps3 -ErrorAction SilentlyContinue) {
        Stop-Process -Id $render.Id
        throw 'User started a match; stopped this staged GPU render'
    }
    Start-Sleep -Seconds 5
    $render.Refresh()
}
$receipt=Join-Path $repo "tmp/sky_cohesion/raw_$Width.render.json"
if (!(Test-Path $receipt) -or (Get-Item $receipt).LastWriteTime -lt $start) { throw 'Render did not finish; inspect its log' }
Get-Content $receipt
