param([ValidateSet(2048,4096,8192)][int]$Width=8192,[ValidateRange(1,4096)][int]$Samples=160,[switch]$CheckOnly)
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $PSScriptRoot 'resource_guard.ps1')
Assert-SkyResourceSlot 'Sky render'
Assert-NoOtherBlender
if ($CheckOnly) { Write-Output 'Sky resource preflight passed; CheckOnly never launches Blender.'; exit 0 }
$start=Get-Date
$render=Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList @('-b','tmp/sky_depth/depth.blend','-P','tools/sky_depth/render_saved.py','--',$Width,$Samples) -WorkingDirectory $repo -WindowStyle Hidden -RedirectStandardOutput (Join-Path $repo "tmp/sky_depth/render$Width.log") -RedirectStandardError (Join-Path $repo "tmp/sky_depth/render$Width.err") -PassThru
$startFileTime=$render.StartTime.ToFileTimeUtc()
while (!$render.HasExited) {
    $busy=@(Get-SkyResourceConflicts -OwnedProcessId $render.Id -StartFileTime $startFileTime)
    if ($busy.Count -gt 0) {
        $render.Refresh()
        if (!$render.HasExited -and $render.StartTime.ToFileTimeUtc() -eq $startFileTime) { Stop-Process -InputObject $render }
        throw ('Resource conflict during sky render: {0}. Stopped only owned Blender PID {1}; staged files and logs preserved.' -f (Format-SkyResourceUsers $busy),$render.Id)
    }
    Start-Sleep -Seconds 5
    $render.Refresh()
}
$render.WaitForExit()
$render.Refresh()
if ($render.ExitCode -ne 0) { throw ('Sky Blender exited {0}; inspect its log' -f $render.ExitCode) }
$receipt=Join-Path $repo "tmp/sky_depth/raw_$Width.render.json"
if (!(Test-Path $receipt) -or (Get-Item $receipt).LastWriteTime -lt $start) { throw 'Render did not finish; inspect its log' }
Get-Content $receipt
