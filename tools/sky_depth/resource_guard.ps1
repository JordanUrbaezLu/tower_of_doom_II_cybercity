# Read-only process discovery for this pass's memory/GPU-heavy launchers.
# Native compiler list matches build_map.ps1's build-stage wait list:
# linker_modtools,cod2map64,Radiant_modtools,gdtdb. Radiant uses a broad match
# because both interactive and LED instances can have variant executable names.
function Get-SkyResourceUsers {
    @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -like '*Radiant*' -or
        $_.ProcessName -in @('BlackOps3','cod2map64','linker_modtools','gdtdb')
    })
}
function Format-SkyResourceUsers($items) {
    (($items | ForEach-Object { '{0} (PID {1})' -f $_.ProcessName,$_.Id }) -join ', ')
}
function Assert-SkyResourceSlot([string]$Action) {
    $busy=@(Get-SkyResourceUsers)
    if ($busy.Count -gt 0) {
        throw ('{0} refused: game/editor/native build stage running: {1}. No Blender launched; staged files and logs preserved.' -f $Action,(Format-SkyResourceUsers $busy))
    }
}
function Assert-NoOtherBlender {
    $other=@(Get-Process blender -ErrorAction SilentlyContinue)
    if ($other.Count) { throw ('Another Blender is open: {0}. Coordinate the resource slot first.' -f (Format-SkyResourceUsers $other)) }
}
function Get-SkyResourceConflicts([int]$OwnedProcessId,[long]$StartFileTime) {
    # Native work always conflicts. A Blender is excluded only if BOTH its PID
    # and creation time match the child captured by this particular launcher.
    @(Get-SkyResourceUsers)
    @(Get-Process blender -ErrorAction SilentlyContinue | Where-Object {
        $_.Id -ne $OwnedProcessId -or $_.StartTime.ToFileTimeUtc() -ne $StartFileTime
    })
}
function Invoke-SkyBlenderStage([string[]]$BlenderArguments,[string]$StageName,[string]$StdoutLog,[string]$StderrLog,[string]$Repo) {
    # Recheck immediately before launch, after any caller's hashing/setup work.
    Assert-SkyResourceSlot $StageName
    Assert-NoOtherBlender
    $child=Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList $BlenderArguments -WorkingDirectory $Repo -WindowStyle Hidden -RedirectStandardOutput $StdoutLog -RedirectStandardError $StderrLog -PassThru
    $startFileTime=$child.StartTime.ToFileTimeUtc()
    while (!$child.HasExited) {
        $busy=@(Get-SkyResourceConflicts -OwnedProcessId $child.Id -StartFileTime $startFileTime)
        if ($busy.Count) {
            $child.Refresh()
            if (!$child.HasExited -and $child.StartTime.ToFileTimeUtc() -eq $startFileTime) { Stop-Process -InputObject $child }
            throw ('{0} interrupted by {1}. Stopped only owned Blender PID {2}; logs and staged files preserved.' -f $StageName,(Format-SkyResourceUsers $busy),$child.Id)
        }
        Start-Sleep -Seconds 2
        $child.Refresh()
    }
    $child.WaitForExit()
    $child.Refresh()
    if ($child.ExitCode -ne 0) { throw ('{0} Blender exited {1}; inspect {2}' -f $StageName,$child.ExitCode,$StderrLog) }
}
