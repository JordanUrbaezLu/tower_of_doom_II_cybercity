# A bounded-lifetime watcher for ONE captured Blender process. It exits when
# that process exits; PID plus creation time prevent acting on a reused PID.
param([Parameter(Mandatory=$true)][int]$OwnedProcessId,[Parameter(Mandatory=$true)][long]$StartFileTime)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'resource_guard.ps1')
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$log=Join-Path $repo 'tmp/sky_dealer/studio_watch.log'
while ($true) {
    $owned=Get-Process -Id $OwnedProcessId -ErrorAction SilentlyContinue
    if (!$owned -or $owned.ProcessName -ne 'blender' -or $owned.StartTime.ToFileTimeUtc() -ne $StartFileTime) { exit 0 }
    $busy=@(Get-SkyResourceUsers)
    if ($busy.Count) {
        $owned.Refresh()
        if (!$owned.HasExited -and $owned.StartTime.ToFileTimeUtc() -eq $StartFileTime) {
            Stop-Process -InputObject $owned
            Add-Content -LiteralPath $log -Value ('{0}: stopped only owned Blender PID {1} for {2}; saved files retained.' -f (Get-Date).ToString('o'),$OwnedProcessId,(Format-SkyResourceUsers $busy))
        }
        exit 1
    }
    Start-Sleep -Seconds 2
}
