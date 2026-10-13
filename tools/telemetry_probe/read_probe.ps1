# read_probe.ps1 - read the TELEMETRY PROBE's evidence after a user run (2026-10-04).
#
# Two witnesses, both printed:
#   1. every [TOD_TELEM] line from the newest console log (the live <game>\console_mp.log, or the
#      newest archive under tmp\elite_tracking\runs\<stamp>\console_mp.log when -Archived is given,
#      or an explicit -Log path)
#   2. <game>\players\tod2_telem_probe.txt (token line, "second", "trace ...") written by the Lua
# and one verdict line. Read-only; touches nothing.
#
#   .\tools\telemetry_probe\read_probe.ps1            # live console_mp.log
#   .\tools\telemetry_probe\read_probe.ps1 -Archived  # newest capture_ai_logs.ps1 archive
#   .\tools\telemetry_probe\read_probe.ps1 -Log <path\to\console_mp.log>

param(
    [string]$Log = '',
    [switch]$Archived,
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III'
)

$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

if ($Log -eq '') {
    if ($Archived) {
        $runs = Join-Path $repo 'tmp\elite_tracking\runs'
        $newest = Get-ChildItem -LiteralPath $runs -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending | Select-Object -First 1
        if ($null -eq $newest) { Write-Host "[read_probe] no archives under $runs"; exit 1 }
        $Log = Join-Path $newest.FullName 'console_mp.log'
    } else {
        $Log = Join-Path $GameRoot 'console_mp.log'
    }
}

Write-Host "[read_probe] console log: $Log"
if (-not (Test-Path -LiteralPath $Log)) { Write-Host "[read_probe] log not found"; exit 1 }
$item = Get-Item -LiteralPath $Log
Write-Host ("[read_probe] log written {0}  ({1:N0} bytes)" -f $item.LastWriteTime, $item.Length)

$ff = Select-String -LiteralPath $Log -Pattern 'Loading fastfile' | Select-Object -Last 1
if ($null -ne $ff) { Write-Host ("[read_probe] " + $ff.Line.Trim()) }

$lines = @(Select-String -LiteralPath $Log -Pattern '\[TOD_TELEM\]' | ForEach-Object { $_.Line.Trim() })
Write-Host ("[read_probe] [TOD_TELEM] lines: {0}" -f $lines.Count)
$lines | ForEach-Object { Write-Host ("   " + $_) }

$probe = Join-Path $GameRoot 'players\tod2_telem_probe.txt'
Write-Host "[read_probe] probe file: $probe"
if (Test-Path -LiteralPath $probe) {
    $p = Get-Item -LiteralPath $probe
    Write-Host ("[read_probe] file written {0}  ({1} bytes)" -f $p.LastWriteTime, $p.Length)
    Get-Content -LiteralPath $probe | ForEach-Object { Write-Host ("   | " + $_) }
} else {
    Write-Host "[read_probe] probe file ABSENT (the Lua never wrote it, or the game runs from another folder)"
}

# lane census (rev 3): which report lanes reached GSC
$lanes = @($lines | Where-Object { $_ -match 'LANES L1=' })
if ($lanes.Count -gt 0) {
    Write-Host ("[read_probe] lane census lines: {0}" -f $lanes.Count)
    $lanes | ForEach-Object { if ($_ -match '(mode=\w+ LANES .*)$') { Write-Host ("   " + $Matches[1]) } }
}

# verdict (rev 1 said "boot io probe", rev 2+ say "first" / "second io probe")
$boot = $lines | Where-Object { $_ -match '(boot|first|second) io probe VERDICT=(.+?) trace=' } | Select-Object -Last 1
$url  = $lines | Where-Object { $_ -match 'end_game url probe trace=' } | Select-Object -Last 1
if ($null -eq $boot -and $lines.Count -eq 0) {
    Write-Host "[read_probe] VERDICT: no probe lines in this log - was the probe build the one loaded, and was developer logging on?"
} elseif ($null -eq $boot) {
    Write-Host "[read_probe] VERDICT: probe init seen but no boot verdict - read the lines above (NO_REPORT = overlay never answered)"
} else {
    $v = [regex]::Match($boot, 'VERDICT=(.+?) trace=').Groups[1].Value
    Write-Host ("[read_probe] VERDICT local file storage: {0}" -f $v)
    if ($boot -match 'io_(\w+)_os_(\w+)') { Write-Host ("[read_probe]   io={0} os={1}" -f $Matches[1], $Matches[2]) }
    if ($boot -match 'OpenUrl_(\w+)')     { Write-Host ("[read_probe]   Engine.OpenUrl exists: {0}" -f ($Matches[1] -eq 'function')) }
}
if ($null -ne $url) {
    Write-Host "[read_probe] url probe ran at game over - the trace shows whether Engine.OpenUrl exists (OpenUrl_function) and whether the call threw (open1_true/false). Only WHERE the page opened is not in any log."
    Write-Host ("   " + $url)
} else {
    Write-Host "[read_probe] url probe did not run (no game over in this run) - that half stays unanswered."
}
