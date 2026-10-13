# Authorized crown visibility + balcony + Necromancer + Fire Bow + C4 + Warrior fixes. Never closes or launches BO3.
param([switch]$GscOnly)
$ErrorActionPreference = 'Stop'
$alarmRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $alarmRoot
$evidence = Join-Path $alarmRoot 'tmp/necro_staff_build'
New-Item -ItemType Directory -Force -Path $evidence | Out-Null
function State($value, $detail) {
    @{state=$value;detail=$detail;time=(Get-Date).ToString('o');pid=$PID} |
        ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $evidence 'status.json')
    Write-Output "$value : $detail"
}
try {
    State 'waiting' 'Waiting for BO3 and other builds to close.'
    while ($true) {
        $game = @(Get-Process BlackOps3 -ErrorAction SilentlyContinue)
        $builders = @(Get-CimInstance Win32_Process | Where-Object {
            $_.ProcessId -ne $PID -and (
                $_.Name -in @('linker_modtools.exe','cod2map64.exe','Radiant_modtools.exe') -or
                ($_.Name -in @('powershell.exe','pwsh.exe') -and $_.CommandLine -match '-File\s+[^\r\n]*tools[\\/]build_map\.ps1')
            )
        })
        if (-not $game.Count -and -not $builders.Count) { break }
        Start-Sleep -Seconds 5
    }
    # Preserve the source actually requested, then require it unchanged after link.
    $inputs = @{}
    foreach ($folder in @('scripts','ui','zone_source','gamedata','model_export/tod_crown_alarm','share/raw/fx/tod/crown_alarm','model_export/tod_necro','share/raw/fx/tod/necro','model_export/tod_fire_bow','model_export/tod_warrior','xanim_export/tod_warrior','model_export/tod_necro_staff','xanim_export/tod_necro_staff')) {
        Get-ChildItem -LiteralPath (Join-Path $alarmRoot $folder) -File -Recurse | ForEach-Object {
            $inputs[$_.FullName] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    }
    foreach ($file in @('source_data/tod_necro_staff_art.gdt','source_data/tod_necro_staff_anims.gdt','source_data/tod_necro_staff.gdt','source_data/tod_crown_alarm.gdt','tools/crown_alarm/light_profile.json','source_data/tod_necro_pulse.gdt','tools/necromancer/make_soul_fx.py','source_data/tod_fire_bow.gdt','source_data/tod_weapon_twins.gdt','tools/gen_tod_twins.js','source_data/tod_warrior_hook.gdt','source_data/tod_warrior_punch.gdt','tools/warrior/install_punch.py','tools/warrior/author_hook.py','tools/gen_tower_map.js','map_source/zm/zm_tod2_cybercity.map')) {
        $path = Join-Path $alarmRoot $file
        $inputs[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    }
    $inputs | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $evidence 'source_snapshot.json')
    if ($GscOnly) { State 'building' 'Guarded script relink; completed geometry and fresh lighting bake retained.' }
    else { State 'building' 'Full guarded build and fresh lighting bake.' }
    # Keep all native stderr (including multi-line tracebacks). Exit status still
    # decides success; PowerShell must not truncate a child at its first error line.
    $ErrorActionPreference = 'Continue'
    if ($GscOnly) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_map.ps1 -GscOnly *> (Join-Path $evidence 'full_build.log')
    } else {
        & powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_map.ps1 *> (Join-Path $evidence 'full_build.log')
    }
    $guardedExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($guardedExit -ne 0) { throw 'Guarded build failed; inspect full_build.log.' }
    foreach ($path in $inputs.Keys) {
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $inputs[$path]) {
            throw "Source changed during build: $path"
        }
    }
    $ErrorActionPreference = 'Continue'
    & python -B tools/necro_staff/record_build.py --build-log tmp/necro_staff_build/full_build.log *> (Join-Path $evidence 'deployment.log')
    $auditExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($auditExit -ne 0) { throw 'Deployment audit failed; inspect deployment.log.' }
    State 'built' 'Full build and exact-source deployment verified. User playtest pending; game not launched.'
} catch {
    State 'failed' $_.Exception.Message
    throw
}
