# Classifier tests only: no OS process is created, stopped or waited on.
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'resource_guard.ps1')
function Get-Process { param($Name,$ErrorAction) $script:caseProcesses | Where-Object { !$Name -or $_.ProcessName -in @($Name) } }
$cases=@()
foreach ($name in @('Radiant','Radiant_modtools','OtherRadiantEditor','BlackOps3','cod2map64','linker_modtools','gdtdb')) {
    $script:caseProcesses=@([pscustomobject]@{ProcessName=$name;Id=12345})
    $detected=@(Get-SkyResourceUsers)
    if ($detected.Count -ne 1) { throw "Missed resource user $name" }
    $refused=$false
    try { Assert-SkyResourceSlot 'Classifier test' }
    catch {
        $refused=$true
        if ($_.ToString() -notlike "*$name (PID 12345)*") { throw "Missing process context for $name" }
    }
    if (!$refused) { throw "Did not refuse $name" }
    $cases+=@{name=$name;refused=$true}
}
foreach ($name in @('blender','powershell','notepad')) {
    $script:caseProcesses=@([pscustomobject]@{ProcessName=$name;Id=12345})
    if (@(Get-SkyResourceUsers).Count -ne 0) { throw "False resource match $name" }
    Assert-SkyResourceSlot 'Negative classifier test'
    $cases+=@{name=$name;refused=$false}
}
$script:caseProcesses=@([pscustomobject]@{ProcessName='blender';Id=12345})
$blenderRefused=$false
try { Assert-NoOtherBlender } catch { $blenderRefused=$true }
if (!$blenderRefused) { throw 'Background/interactive launcher must reject another Blender.' }
$script:caseProcesses=@([pscustomobject]@{ProcessName='notepad';Id=12345})
Assert-NoOtherBlender
$ownedStart=[datetime]'2026-09-30T23:00:00Z'
$script:caseProcesses=@([pscustomobject]@{ProcessName='blender';Id=12345;StartTime=$ownedStart})
if (@(Get-SkyResourceConflicts -OwnedProcessId 12345 -StartFileTime $ownedStart.ToFileTimeUtc()).Count) { throw 'Owned Blender was mistaken for a peer' }
$script:caseProcesses+=@([pscustomobject]@{ProcessName='blender';Id=12346;StartTime=$ownedStart})
$conflicts=@(Get-SkyResourceConflicts -OwnedProcessId 12345 -StartFileTime $ownedStart.ToFileTimeUtc())
if ($conflicts.Count -ne 1 -or $conflicts[0].Id -ne 12346) { throw 'Peer Blender appearing after launch was missed' }
$script:caseProcesses=@([pscustomobject]@{ProcessName='blender';Id=12345;StartTime=$ownedStart.AddSeconds(1)})
if (@(Get-SkyResourceConflicts -OwnedProcessId 12345 -StartFileTime $ownedStart.ToFileTimeUtc()).Count -ne 1) { throw 'Reused PID was mistaken for owned Blender' }
[pscustomobject]@{status='pass';cases=$cases;other_blender_refusal=$true;owned_blender_excluded=$true;late_peer_detected=$true;reused_pid_not_owned=$true;os_processes_created_or_stopped=0} | ConvertTo-Json -Depth 4
