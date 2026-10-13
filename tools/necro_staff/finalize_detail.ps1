# Serialized final promotion and FULL build. Never stops or launches the game.
$ErrorActionPreference = 'Stop'
$staffRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $staffRoot
Write-Output 'Waiting for the active guarded build and BO3 to close before promoting the final grip correction.'
while ($true) {
    $busy = @(Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and (
            $_.Name -in @('BlackOps3.exe','linker_modtools.exe','cod2map64.exe','Radiant_modtools.exe','gdtdb.exe') -or
            ($_.Name -in @('powershell.exe','pwsh.exe') -and $_.CommandLine -match '-File\s+[^\r\n]*tools[\\/]build_map\.ps1')
        )
    })
    if (-not $busy.Count) { break }
    Start-Sleep -Seconds 5
}
& python -B tools/necro_staff/promote_grip.py
if ($LASTEXITCODE -ne 0) { throw 'Final art promotion refused; inputs untouched or promotion failed.' }
& python -B tools/necro_staff/verify.py
if ($LASTEXITCODE -ne 0) { throw 'Final exported asset checks failed before build.' }
& powershell -NoProfile -ExecutionPolicy Bypass -File tools/necro_staff/build_when_idle.ps1
if ($LASTEXITCODE -ne 0) { throw 'Final guarded build or deployment audit failed.' }
