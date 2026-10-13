# THE LUCKY SOURCES' guarded build (docs/197): waits until BO3 is closed and no other build is running, gives a quick
# relaunch 30 s to show up, then runs ONE full build (tools/build_map.ps1; geom_key reuses the bake when the map, its
# materials and the sky are unchanged). Never closes or launches BO3. Status: tmp/lucky/status.json; log tmp/lucky/<LogName>.log.
param([string]$LogName = 'full4')
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $root
$dir = Join-Path $root 'tmp/lucky'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$log = Join-Path $dir ($LogName + '.log')

function State($value, $detail) {
    @{ state = $value; detail = $detail; time = (Get-Date).ToString('o'); pid = $PID; log = $log } |
        ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $dir 'status.json')
    Write-Output ('{0} {1} : {2}' -f (Get-Date).ToString('HH:mm:ss'), $value, $detail)
}

function Busy() {
    $game = @(Get-Process BlackOps3 -ErrorAction SilentlyContinue)
    $builders = @(Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and (
            $_.Name -in @('linker_modtools.exe', 'cod2map64.exe', 'Radiant_modtools.exe') -or
            ($_.Name -in @('powershell.exe', 'pwsh.exe') -and $_.CommandLine -match '-File\s+[^\r\n]*tools[\\/]build_map\.ps1')
        )
    })
    if ($game.Count) { return 'BO3 is running' }
    if ($builders.Count) { return 'another build is running' }
    return ''
}

State 'waiting' 'Waiting for BO3 and any other build to close.'
while ($true) {
    if (-not (Busy)) {
        Start-Sleep -Seconds 30                    # a quick relaunch, or a peer's queued build, gets the first word
        $why = Busy
        if (-not $why) { break }
    }
    Start-Sleep -Seconds 5
}
State 'building' 'Full guarded build.'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'tools/build_map.ps1') *> $log
$code = $LASTEXITCODE
$ok = Select-String -LiteralPath $log -Pattern '=== BUILD OK ===' -Quiet
if ($ok -and $code -eq 0) { State 'built' ('BUILD OK, exit 0: ' + $log) }
else { State 'failed' ('exit ' + $code + ', BUILD OK line present: ' + $ok + ': ' + $log) }
