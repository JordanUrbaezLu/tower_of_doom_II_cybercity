[CmdletBinding()]
param(
    [string]$GameRoot = 'C:\Program Files (x86)\Call of Duty Black Ops 6\_retail_',
    [string]$Output = 'tmp\wunderfizz\assets\direct_extraction_preflight.json'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$toolRoot = 'C:\Users\jorda\Documents\BO3_tools\Cordycep-2.8.3.0'
$pilot = @{
    game_exe = 'b14476a9b94ce65be56a07e24ab1da65525c86b72e2c0f01dbaea05eccc6bb79'
    loader = 'ec0d0f5b69f8b919484a4a0843ae6e15a0949790fcdfa8c693e28dd074c64873'
    dump = '15f77032a6e3c3fd89d8dc24be1cc965b286f409e3ac8759ec6e8773864897e3'
}
$inputs = @(
    @{role='game_exe';path=(Join-Path $GameRoot 'cod24-cod.exe')},
    @{role='ingame_zm';path=(Join-Path $GameRoot 'cod24\ingame_zm.ff')},
    @{role='loader';path=(Join-Path $toolRoot 'Cordycep.CLI.exe')},
    @{role='dump';path=(Join-Path $toolRoot 'Data\Dumps\cod24-cod_dump.exe')},
    @{role='saluki';path='C:\Users\jorda\Documents\BO3_tools\Saluki\Saluki.exe'}
)
$missing = @()
$changed = @()
$rows = @()
foreach ($inputFile in $inputs) {
    $exists = Test-Path -LiteralPath $inputFile.path -PathType Leaf
    $hash = $null
    $bytes = $null
    if ($exists) {
        $bytes = (Get-Item -LiteralPath $inputFile.path).Length
        if ($pilot.ContainsKey($inputFile.role)) {
            $hash = (Get-FileHash -LiteralPath $inputFile.path -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($hash -ne $pilot[$inputFile.role]) { $changed += $inputFile.role }
        }
    } else { $missing += $inputFile.role }
    $rows += [ordered]@{role=$inputFile.role;path=$inputFile.path;exists=$exists;bytes=$bytes;sha256=$hash}
}
$games = @(Get-Process -Name 'BlackOps3','cod24-cod','cod','sp24-cod','cod25-cod' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName)
$extractors = @(Get-Process -Name 'Cordycep.CLI','Saluki' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime)
$result = [ordered]@{
    checked_at_utc = [DateTime]::UtcNow.ToString('o')
    source_game = 'Black Ops 6; explicitly selected by user'
    game_root = $GameRoot
    required_files = $rows
    missing_roles = $missing
    changed_verified_roles = $changed
    actual_games = $games
    extraction_processes = $extractors
    can_start_exact_source_extraction = ($missing.Count -eq 0 -and $changed.Count -eq 0 -and $games.Count -eq 0)
    game_launched = $false
    extractor_launched = $false
    network_changed = $false
    output_kind = 'read-only input audit; task-owned receipt only'
    next_step = 'Supply the actual BO6 content root. Re-run with -GameRoot before any normal UAC extractor startup. A changed executable needs compatibility verification; never alter the expected hash to bypass it.'
}
$outputPath = $Output
if (-not [System.IO.Path]::IsPathRooted($outputPath)) { $outputPath = Join-Path $repoRoot $outputPath }
$resolvedOutput = [System.IO.Path]::GetFullPath($outputPath)
if (-not $resolvedOutput.StartsWith(($repoRoot.TrimEnd('\') + '\'),[StringComparison]::OrdinalIgnoreCase)) {
    throw 'The preflight receipt must stay in this repository.'
}
New-Item -ItemType Directory -Path (Split-Path -Parent $resolvedOutput) -Force | Out-Null
[System.IO.File]::WriteAllText($resolvedOutput,(($result | ConvertTo-Json -Depth 8) + "`n"),(New-Object System.Text.UTF8Encoding($false)))
$result | ConvertTo-Json -Depth 8
if (-not $result.can_start_exact_source_extraction) { exit 2 }
