# Isolated material link. Never overwrite the playable map's zone or fastfile.
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $repo 'tools/tod2_workspace.ps1')
$toolsRoot = Resolve-Tod2Root
Set-Tod2ProcessEnvironment
$work = Join-Path $repo 'tmp/alarm_lens_repair/packaging_probe'
$probeName = 'tod_alarm_lens_packaging_probe'

function Assert-ProbeIdle {
    $active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -match '^(BlackOps3|Blender|Radiant.*|gdtdb|cod2map64|linker_modtools)$'
    })
    if ($active.Count) { throw ('Native probe blocked by ' + (($active | ForEach-Object { "$($_.Name):$($_.Id)" }) -join ', ')) }
    $builders = @(Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and $_.Name -match '^(powershell|pwsh)\.exe$' -and
        $_.CommandLine -match '-File\s+["\S]*[\\/]build_map\.ps1'
    })
    if ($builders.Count) { throw 'A guarded map build is still active; the diagnostic must wait.' }
}
function Invoke-OwnedProbe([string]$exe, [string[]]$arguments, [string]$cwd, [string]$label) {
    Assert-ProbeIdle
    $out = Join-Path $work ($label + '.out.log')
    $err = Join-Path $work ($label + '.err.log')
    $owned = Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $cwd -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
    $ownedHandle = $owned.Handle
    $creation = $owned.StartTime.ToFileTimeUtc()
    $ownedIds = @{}
    $ownedIds[$owned.Id] = $true
    while (-not $owned.HasExited) {
        Start-Sleep -Seconds 1
        # The linker starts its own language child. Its descendants belong to
        # this diagnostic, unlike another session's native build processes.
        $processes = @(Get-CimInstance Win32_Process)
        do {
            $added = $false
            foreach ($proc in $processes) {
                if (!$ownedIds.ContainsKey([int]$proc.ProcessId) -and $ownedIds.ContainsKey([int]$proc.ParentProcessId) -and $proc.CreationDate.ToFileTimeUtc() -ge $creation) {
                    $ownedIds[[int]$proc.ProcessId] = $true
                    $added = $true
                }
            }
        } while ($added)
        $conflict = @($processes | Where-Object { !$ownedIds.ContainsKey([int]$_.ProcessId) -and $_.Name -match '^(BlackOps3|Blender|Radiant.*|gdtdb|cod2map64|linker_modtools)\.exe$' })
        if ($conflict.Count) {
            $current = Get-Process -Id $owned.Id -ErrorAction SilentlyContinue
            if ($current -and $current.StartTime.ToFileTimeUtc() -eq $creation) { Stop-Process -Id $owned.Id }
            throw 'Another game/editor/native stage started. Stopped only the owned diagnostic.'
        }
        $owned.Refresh()
    }
    $owned.WaitForExit()
    if ($label -eq 'gdtdb' -and $owned.ExitCode -ne 0) { throw "$label exited $($owned.ExitCode); inspect the isolated logs." }
    if ($label -eq 'linker') { Write-Host "Diagnostic linker exit=$($owned.ExitCode); native record validation decides success." }
    Get-Content -LiteralPath $out -Tail 8
}

Assert-ProbeIdle
$shippingFf = Join-Path $toolsRoot 'usermaps/zm_tod2_cybercity/zone/zm_tod2_cybercity.ff'
$shippingHash = (Get-FileHash -LiteralPath $shippingFf -Algorithm SHA256).Hash
& python -B (Join-Path $PSScriptRoot 'probe_lens_packaging.py')
if ($LASTEXITCODE -ne 0) { throw 'Isolated probe preparation failed.' }
$probeGdt = Join-Path $toolsRoot 'temp_assets/tod_alarm_lens_packaging_probe.gdt'
$probeZone = Join-Path $toolsRoot ('zone_source/' + $probeName + '.zone')
Assert-Tod2WritePath $probeGdt
Assert-Tod2WritePath $probeZone
Assert-ProbeIdle
New-Item -ItemType Directory -Path (Split-Path $probeGdt -Parent) -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path $probeZone -Parent) -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $work 'probe.gdt') -Destination $probeGdt
Copy-Item -LiteralPath (Join-Path $work ($probeName + '.zone')) -Destination $probeZone
Invoke-OwnedProbe (Join-Path $toolsRoot 'gdtdb/gdtdb.exe') @('/update') (Join-Path $toolsRoot 'gdtdb') 'gdtdb'
$probeStarted = Get-Date
Invoke-OwnedProbe (Join-Path $toolsRoot 'bin/linker_modtools.exe') @('-language','english',$probeName) (Join-Path $toolsRoot 'bin') 'linker'
$probeFf = Join-Path $toolsRoot ('zone/' + $probeName + '.ff')
if (!(Test-Path -LiteralPath $probeFf) -or (Get-Item -LiteralPath $probeFf).LastWriteTime -lt $probeStarted) { throw 'Diagnostic linker produced no fresh isolated fastfile.' }
& python -B (Join-Path $PSScriptRoot 'verify_lens_packaging_probe.py')
if ($LASTEXITCODE -ne 0) { throw 'Isolated native material controls failed.' }
if ((Get-FileHash -LiteralPath $shippingFf -Algorithm SHA256).Hash -ne $shippingHash) { throw 'Shipping fastfile changed during isolated diagnosis.' }
if (!(Select-String -LiteralPath (Join-Path $work 'linker.out.log') -SimpleMatch ('Linking "' + $probeName + '"'))) { throw 'Native linker did not identify the isolated diagnostic zone.' }
Set-Content -LiteralPath (Join-Path $work 'shipping_ff_unchanged.sha256') -Value $shippingHash
Write-Host 'LENS_PACKAGING_PROBE_LINKED: isolated native zone; shipping map outputs were untouched.'
