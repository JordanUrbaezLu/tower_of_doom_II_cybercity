# import_bundle.ps1 - NEW LAPTOP: clone Tower II from GitHub and put every file of the transfer bundle
# where it belongs (docs/220 step B3). Run it from the bundle's own copy:
#
#   powershell -ExecutionPolicy Bypass -File C:\tod_transfer\round2\migrate_scripts\import_bundle.ps1
#
# Before running: Map One's migration is done on this laptop (docs/174 there: Steam BO3 + Mod Tools at
# ...\Call of Duty Black Ops III 455130, the usermaps junction, Git + LFS, Python 3.14, Node 24,
# Blender 4.2), BO3 is closed and no build is running.
#
# Safe to re-run: the root import resumes its own earlier run (and refuses a root it did not create);
# the repo-extras copy goes through .part files, repairs short copies and keeps only files changed here
# after the bundle was made; robocopy /XO never takes an older file. It ends by running check_machine.ps1.
param(
    [string]$Source = (Split-Path $PSScriptRoot -Parent),   # the bundle folder (parent of migrate_scripts)
    [string]$ReposDir = (Join-Path $env:USERPROFILE 'Repositories'),
    [string]$Branch = 'main',
    [string]$SteamCommon = 'C:\Program Files (x86)\Steam\steamapps\common',
    [string]$Tod2Root = 'C:\BO3Tools\TOD2Cybercity',
    [switch]$Force,
    [switch]$SkipRoot
)
$ErrorActionPreference = 'Stop'
function NoErr([scriptblock]$sb) { $ErrorActionPreference = 'Continue'; & $sb 2>$null }
function Info($m) { Write-Host "[import] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[import] WARN: $m" -ForegroundColor Yellow }
function Die($m)  { Write-Host "[import] FAIL: $m" -ForegroundColor Red; exit 1 }

$H = $env:USERPROFILE
$RepoRoot = Join-Path $ReposDir 'tower_of_doom_II_cybercity'
$Game  = Join-Path $SteamCommon 'Call of Duty Black Ops III'
$Tools = Join-Path $SteamCommon 'Call of Duty Black Ops III 455130'
$Py = Join-Path $PSScriptRoot 'bundle_tool.py'
$RoboLog = Join-Path $env:TEMP 'tod2_import_robocopy.log'
$Map = 'zm_tod2_cybercity'

# robocopy that never replaces a newer local file (/XO). -NoOverwrite: only files missing at the
# destination (/XC /XN /XO). /XJ: never follow a junction.
function Robo([string]$label, [string]$src, [string]$dst, [switch]$NoOverwrite) {
    if (-not (Test-Path -LiteralPath $src)) { Warn "$label - not in the bundle, skipped"; return }
    $a = @($src, $dst, '/E', '/XO', '/XJ', '/COPY:DAT', '/DCOPY:T', '/R:1', '/W:1', '/MT:16', '/NFL', '/NDL', '/NP', '/NJH', '/NJS', "/LOG+:$RoboLog")
    if ($NoOverwrite) { $a += @('/XC', '/XN') }
    & robocopy @a | Out-Null
    if ($LASTEXITCODE -ge 8 -or $LASTEXITCODE -lt 0) { Die "robocopy failed ($LASTEXITCODE): $src -> $dst (see $RoboLog)" }
    Info "$label -> $dst"
}

# ---------------------------------------------------------------- preflight
# a shell opened before an install can carry a stale PATH (no python / node): take the current one
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not (Test-Path (Join-Path $Source 'bundle_manifest.json'))) { Die "no bundle_manifest.json in $Source - pass -Source <bundle folder>" }
foreach ($c in 'git', 'python', 'node', 'robocopy') {
    if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { Die "$c is not installed / not on PATH (Map One's docs/174 step B2), then open a NEW terminal" }
}
foreach ($p in 'BlackOps3', 'linker_modtools', 'cod2map64', 'radiant_modtools', 'converter', 'gdtdb') {
    if (Get-Process -Name $p -ErrorAction SilentlyContinue) { Die "$p is running - close BO3 / wait for the build, then re-run" }
}
if ($H -ne 'C:\Users\jorda') { Warn "your profile is $H, not C:\Users\jorda: Tower II tools and build gates hardcode C:\Users\jorda (docs/220 'Paths')" }
if (-not (Test-Path (Join-Path $Tools 'bin\modlauncher.exe'))) {
    Die "BO3 Mod Tools not found at $Tools. Finish Map One's migration first (its import_bundle.ps1 makes this folder or a junction to it)."
}
if (-not (Test-Path (Join-Path $Game 'BlackOps3.exe'))) { Die "BO3 not found at $Game" }
$stampPath = Join-Path $Tod2Root '.tod2-import.json'
if ((Test-Path -LiteralPath (Join-Path $Tod2Root '.tod2-workspace.json')) -and -not (Test-Path -LiteralPath $stampPath) -and -not $SkipRoot) {
    Die "$Tod2Root already exists and was NOT made by this import (was tools\setup_tod2_workspace.ps1 run here?). It holds today's Steam / Map One files, not Tower II's. Rename it aside (e.g. $Tod2Root.before_import), then re-run. Never run setup_tod2_workspace.ps1 on a migrated machine."
}
# free space: the bundle's contents are copied once more onto this disk (plus the clone, ~13 GB)
$bm0 = Get-Content (Join-Path $Source 'bundle_manifest.json') -Raw | ConvertFrom-Json
if (-not (Test-Path -LiteralPath $stampPath)) {
    $need = [int64]$bm0.total_bytes + 25e9
    $free = (Get-PSDrive C).Free
    if ($free -lt $need) { Die ("C: has {0:N0} GB free; the import needs about {1:N0} GB (bundle contents + clone + headroom). Free space, then re-run." -f ($free / 1e9), ($need / 1e9)) }
    Info ("C: free {0:N0} GB, import needs about {1:N0} GB" -f ($free / 1e9), ($need / 1e9))
}
git config --global core.longpaths true

# ---------------------------------------------------------------- 1. the repo from GitHub (LFS checked)
New-Item -ItemType Directory -Force -Path $ReposDir | Out-Null
NoErr { git lfs install } | Out-Null
if (Test-Path (Join-Path $RepoRoot '.git')) {
    # a clone that died mid-checkout leaves .git + a partial tree: refuse to build on it
    $missing = @(git -C $RepoRoot ls-files --deleted).Count
    if ($missing -gt 0) { Die "$RepoRoot is an incomplete clone ($missing tracked files missing). Delete the folder and re-run." }
    Info "already cloned: $RepoRoot"
} else {
    if ((Test-Path $RepoRoot) -and @(Get-ChildItem -LiteralPath $RepoRoot -Force).Count -gt 0) {
        Die "$RepoRoot exists, is not a git clone and is not empty - move it aside, then re-run"
    }
    $env:GIT_LFS_SKIP_SMUDGE = '1'                     # big files come down in one checked step below
    & git clone --branch $Branch 'https://github.com/JordanUrbaezLu/tower_of_doom_II_cybercity.git' $RepoRoot
    $code = $LASTEXITCODE
    Remove-Item Env:\GIT_LFS_SKIP_SMUDGE -ErrorAction SilentlyContinue
    if ($code -ne 0) { Die "git clone failed (delete $RepoRoot if it exists, then re-run)" }
}
& git -C $RepoRoot lfs pull
if ($LASTEXITCODE -ne 0) { Die "git lfs pull failed in $RepoRoot (GitHub LFS quota or login) - fix, then: git -C `"$RepoRoot`" lfs pull" }
# the export recorded the commit the bundle belongs with: the clone must contain it
$bm = Get-Content (Join-Path $Source 'bundle_manifest.json') -Raw | ConvertFrom-Json
NoErr { git -C $RepoRoot merge-base --is-ancestor $bm.repo_head HEAD }
if ($LASTEXITCODE -ne 0) { Warn "the clone does not contain the export's commit $($bm.repo_head) - git -C `"$RepoRoot`" pull, then re-run" }

# untracked repo files: only the paths the export listed, never over a file the clone already has
$lst = Join-Path $Source 'repo_extras.lst'
$xman = Join-Path $Source 'repo_extras_manifest.json'
if (Test-Path $lst) {
    # copies through .part files; replaces a partial copy from an interrupted run; keeps only a file
    # changed here after the bundle was made; then checks every file's size against the export manifest
    $ca = @($Py, 'copylist', '--src', (Join-Path $Source 'repo_extras'), '--dest', $RepoRoot, '--list', $lst, '--no-overwrite')
    if (Test-Path $xman) { $ca += @('--manifest', $xman) } else { Warn 'repo_extras_manifest.json missing from the bundle - the untracked files cannot be size-checked' }
    & python @ca
    if ($LASTEXITCODE -ne 0) { Die 'repo extras copy failed or a file arrived short (see above) - re-run the import' }
} else { Warn 'repo_extras.lst missing from the bundle - tmp\ and source_library\ were not restored' }

# ---------------------------------------------------------------- 2. the private Mod Tools root (sha1-checked)
if (-not $SkipRoot) {
    $ra = @($Py, 'root-import', '--src', (Join-Path $Source 'tod2_root'), '--root', $Tod2Root)
    if ($Force) { $ra += '--force' }
    & python @ra
    if ($LASTEXITCODE -ne 0) { Die 'private root import failed (see above)' }
}
# Runtimes: Tower II runs cod2map64 / linker / Radiant from the PRIVATE bin (that folder is the working
# directory), so a DLL that exists only in the Steam tools bin is not found (2026-10-13 review). When
# System32 lacks one, copy it into the private bin.
foreach ($dll in 'msvcr110.dll', 'msvcp110.dll', 'vcomp110.dll', 'd3dx9_43.dll') {
    $priv = Join-Path $Tod2Root "bin\$dll"
    if ((Test-Path "$env:WINDIR\System32\$dll") -or (Test-Path $priv)) { continue }
    $steamCopy = Join-Path $Tools "bin\$dll"
    if (Test-Path $steamCopy) { Copy-Item -LiteralPath $steamCopy -Destination $priv; Info "runtime $dll copied into $Tod2Root\bin (System32 has none)" }
    else { Warn "runtime $dll is in neither System32 nor any tools bin - install the VC++ 2012 x64 / DirectX June 2010 runtimes (Steam > Mod Tools > Play once, accept the admin prompt)" }
}
$mig = Join-Path $RepoRoot 'tmp\migration'
New-Item -ItemType Directory -Force -Path $mig | Out-Null
foreach ($f in 'tod2_root\root_manifest.json', 'repo_extras_manifest.json', 'bundle_manifest.json', 'machine_facts.txt') {
    $p = Join-Path $Source $f
    if (Test-Path $p) { Copy-Item $p $mig -Force }
}
if (Test-Path (Join-Path $Source 'python')) { Copy-Item (Join-Path $Source 'python') $mig -Recurse -Force }

# ---------------------------------------------------------------- 3. the game sees the private build output
# Same rule as tools/tod2_workspace.ps1 Connect-Tod2GameFolder: create ONLY our own child junction, never
# repoint the global usermaps junction or touch another map's folder.
$gu = Join-Path $Game 'usermaps'
$link = Join-Path $gu $Map
$target = Join-Path $Tod2Root "usermaps\$Map"
if (-not (Test-Path -LiteralPath $gu)) {
    Warn "$gu does not exist - Map One's import makes it (a junction to the tools usermaps); run that first"
} elseif (Test-Path -LiteralPath $link) {
    $it = Get-Item -LiteralPath $link -Force
    $tgt = "$(@($it.Target)[0])".TrimEnd('\')
    if (($it.Attributes -band [IO.FileAttributes]::ReparsePoint) -and $tgt -eq $target) { Info "game junction already -> $target" }
    else { Warn "$link exists and does not point at $target (left alone) - fix it by hand" }
} else {
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    Info "junction: $link -> $target"
}

# ---------------------------------------------------------------- 4. Downloads (literal paths: tools name them)
if (Test-Path (Join-Path $Source 'downloads')) {
    Robo 'Downloads (Tower II raw sources + T7 pack)' (Join-Path $Source 'downloads') (Join-Path $H 'Downloads') -NoOverwrite
}
# T7 Assets V2.8.rar is a BUILD input (keeper / dealer gates re-extract from it every build): prove the copy
$t7sha = Join-Path $Source 'downloads\T7 Assets V2.8.rar.sha1'
$t7 = Join-Path $H 'Downloads\T7 Assets V2.8.rar'
if (Test-Path -LiteralPath $t7sha) {
    $wantSha, $wantLen = (Get-Content -LiteralPath $t7sha -Raw).Trim() -split ' '
    if (-not (Test-Path -LiteralPath $t7)) { Die "Downloads\T7 Assets V2.8.rar missing after the copy - re-run the import" }
    if ((Get-Item -LiteralPath $t7).Length -ne [int64]$wantLen) { Die "Downloads\T7 Assets V2.8.rar is $((Get-Item -LiteralPath $t7).Length) bytes, expected $wantLen (a partial copy?) - delete it and re-run the import" }
    Info 'checking T7 Assets V2.8.rar SHA1 (~3 min) ...'
    if ((Get-FileHash -LiteralPath $t7 -Algorithm SHA1).Hash -ne $wantSha) { Die "Downloads\T7 Assets V2.8.rar SHA1 differs from the old laptop's - delete it and re-run the import" }
    Info 'T7 Assets V2.8.rar SHA1 matches the old laptop'
} elseif (-not (Test-Path -LiteralPath $t7)) {
    Warn 'Downloads\T7 Assets V2.8.rar is not here and not in the bundle - the keeper / dealer build gates will fail until it is'
}

# ---------------------------------------------------------------- 5. Claude memory
$key = $RepoRoot -replace '[^A-Za-z0-9]', '-'
$mem = Join-Path $H ".claude\projects\$key\memory"
$oldIdx = Join-Path $Source 'claude\memory\MEMORY.md'; $newIdx = Join-Path $mem 'MEMORY.md'
if ((Test-Path $newIdx) -and (Test-Path $oldIdx) -and -not $Force -and
    ((Get-FileHash $newIdx).Hash -ne (Get-FileHash $oldIdx).Hash)) {
    Warn "this laptop already has a different Claude MEMORY.md for Tower II (Claude was opened in the repo before the import). The old laptop's index is $oldIdx - merge its lines in, or re-run with -Force to take the old one."
}
if ($Force) { Robo 'Claude project memory' (Join-Path $Source 'claude\memory') $mem }
else { Robo 'Claude project memory (missing files only)' (Join-Path $Source 'claude\memory') $mem -NoOverwrite }
Robo 'Claude session history' (Join-Path $Source 'claude\project') (Join-Path $H ".claude\projects\$key") -NoOverwrite

# ---------------------------------------------------------------- 6. Python packages
& python -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { Warn 'pip install of tools requirements failed - see tools\migrate\requirements.txt' }
if (-not [Environment]::GetEnvironmentVariable('ELEVENLABS_API_KEY', 'User')) {
    Warn 'ELEVENLABS_API_KEY is not set (credentials are never copied). Only the voice/SFX generators need it: set it as a USER environment variable when you next generate sound.'
}

# ---------------------------------------------------------------- 7. check everything
Info 'running check_machine.ps1 ...'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot 'tools\migrate\check_machine.ps1') -RepoRoot $RepoRoot -SteamCommon $SteamCommon -Tod2Root $Tod2Root
exit $LASTEXITCODE
