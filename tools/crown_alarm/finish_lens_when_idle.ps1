# Finish only this reviewed alarm repair after the workstation is available.
# Never launch or stop a game, editor, or another session's process.
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$work = Join-Path $repo 'tmp/alarm_lens_repair'
Set-Location -LiteralPath $repo
function Get-LensConflicts {
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^(BlackOps3|Blender|Radiant.*|gdtdb|cod2map64|linker_modtools)\.exe$' -or
        ($_.ProcessId -ne $PID -and $_.Name -match '^(powershell|pwsh)\.exe$' -and
         $_.CommandLine -match '-File\s+["\S]*[\\/]build_map\.ps1')
    })
}
$quietSince = $null
$lastStatus = ''
while ($true) {
    $busy = @(Get-LensConflicts)
    $status = ($busy | ForEach-Object { "$($_.Name):$($_.ProcessId)" }) -join ', '
    if ($busy.Count) {
        $quietSince = $null
        if ($status -ne $lastStatus) { Write-Host "[alarmfinish] Waiting for $status"; $lastStatus = $status }
    } else {
        if (!$quietSince) { $quietSince = Get-Date; Write-Host '[alarmfinish] Workstation free; requiring 30 seconds quiet.' }
        if (((Get-Date) - $quietSince).TotalSeconds -ge 30) { break }
    }
    Start-Sleep -Seconds 3
}
Write-Host '[alarmfinish] Finishing the verified native-model rotating-light preview.'
& powershell -NoProfile -ExecutionPolicy Bypass -File tools/crown_alarm/start_lens_studio.ps1
if ($LASTEXITCODE -ne 0) { throw 'Guarded preview studio could not start.' }
$owned = Get-Content -LiteralPath (Join-Path $work 'studio_process.json') -Raw | ConvertFrom-Json
try {
    $deadline = (Get-Date).AddSeconds(30)
    while (!(Select-String -LiteralPath (Join-Path $work 'studio.log') -SimpleMatch 'TOD2_ALARM_MCP_READY' -Quiet)) {
        if ((Get-Date) -gt $deadline) { throw 'Owned MCP studio did not become ready.' }
        Start-Sleep -Seconds 1
    }
    $calledAt = Get-Date
    # Python's MCP library logs harmless INFO to stderr. Parse its retained
    # response as well as its exit status rather than treating INFO as failure.
    $ErrorActionPreference = 'Continue'
    & '../tower_of_doom_II_hellbound/tmp/gold_sword_env/Scripts/python.exe' -B tools/crown_alarm/mcp_call.py tools/crown_alarm/18_finish_lens_preview.py > (Join-Path $work 'binding_finish_mcp.log') 2>&1
    $mcpCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($mcpCode -ne 0) { throw 'Actual MCP preview execution failed; staged primary renders remain intact.' }
    $response = Get-ChildItem -LiteralPath (Join-Path $repo 'tmp/crown_alarm_mcp') -Filter '*.json' -File | Where-Object { $_.LastWriteTime -ge $calledAt } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (!$response) { throw 'No fresh actual MCP response was saved.' }
    $result = Get-Content -LiteralPath $response.FullName -Raw | ConvertFrom-Json
    if ($result.isError -or ($result.content | Where-Object { $_.text -match 'Error executing code' })) { throw 'Actual MCP response reports a failed preview.' }
} finally {
    $ErrorActionPreference = 'Stop'
    $current = Get-Process -Id $owned.pid -ErrorAction SilentlyContinue
    if ($current -and $current.Name -eq 'blender' -and $current.StartTime.ToFileTimeUtc() -eq $owned.start_filetime) { Stop-Process -InputObject $current }
}
if (@(Get-LensConflicts).Count) { throw 'Workstation became busy before publication; reviewed assets remain staged.' }
& python -B tools/crown_alarm/publish_lens_binding.py
if ($LASTEXITCODE -ne 0) { throw 'Strict reviewed binding publication failed.' }
Copy-Item -LiteralPath (Join-Path $work 'full_build.log') -Destination (Join-Path $work 'full_build_attempt1.log')
Write-Host '[alarmfinish] Reviewed source set installed; guarded FULL build starting.'
$ErrorActionPreference = 'Continue'
& powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_map.ps1 > (Join-Path $work 'full_build.log') 2>&1
$buildCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($buildCode -ne 0) { throw 'Guarded full build failed; inspect full_build.log.' }
& python -B tools/crown_alarm/record_lens_build.py
if ($LASTEXITCODE -ne 0) { throw 'Exact native build delivery audit failed.' }
Write-Host '[alarmfinish] ALARM GLASS BUILD VERIFIED; game remains unlaunched.'
