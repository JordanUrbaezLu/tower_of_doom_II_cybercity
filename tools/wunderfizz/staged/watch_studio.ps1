param([Parameter(Mandatory=$true)][int]$OwnedProcessId,[Parameter(Mandatory=$true)][long]$StartFileTime)
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $repo 'tools/sky_depth/resource_guard.ps1')
while ($true) {
    $owned=Get-Process -Id $OwnedProcessId -ErrorAction SilentlyContinue
    if (!$owned -or $owned.ProcessName -ne 'blender' -or $owned.StartTime.ToFileTimeUtc() -ne $StartFileTime) { exit 0 }
    $busy=@(Get-SkyResourceUsers)
    $free=[long](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024
    if ($busy.Count -or $free -lt 512MB) {
        $owned.Refresh()
        if (!$owned.HasExited -and $owned.StartTime.ToFileTimeUtc() -eq $StartFileTime) { Stop-Process -InputObject $owned }
        Add-Content -LiteralPath (Join-Path $repo 'tmp/wunderfizz/assets/studio_watch.log') -Value ('{0}: stopped only Wunderfizz-owned PID {1}; conflicts {2}; free memory {3}.' -f (Get-Date).ToString('o'),$OwnedProcessId,(Format-SkyResourceUsers $busy),$free)
        exit 1
    }
    Start-Sleep -Seconds 2
}
