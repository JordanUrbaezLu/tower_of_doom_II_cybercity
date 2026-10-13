# export_bundle.ps1 - OLD LAPTOP: pack everything GitHub does not carry for TOWER II into ONE folder
# (docs/220; adapted from Map One's docs/174 export, which already moved the shared toolchain).
#
#   powershell -ExecutionPolicy Bypass -File tools\migrate\export_bundle.ps1 -Dest \\10.0.0.149\tod_transfer\round2 -DryRun
#   powershell -ExecutionPolicy Bypass -File tools\migrate\export_bundle.ps1 -Dest \\10.0.0.149\tod_transfer\round2
#
# -Dest can be an external drive or a network share. Re-running RESUMES: the root copy and the
# repo-extras copy both skip files that are already there and current.
#
# GitHub carries the repo itself (code, docs, art, model_export, sounds; every file byte-for-byte,
# Blender masters via LFS). This bundle carries the rest:
#   tod2_root\        the PRIVATE Mod Tools root C:\BO3Tools\TOD2Cybercity (~34 GB): every physical file,
#                     its 123 junctions as (path, target), every folder; minus the converter cache
#   repo_extras\      every file in this repo git does not track (tmp\, source_library\, *.blend1 ...)
#   downloads\        Tower II's raw sources in Downloads that Map One's bundle did not carry (TOD2_*), and
#                     T7 Assets V2.8.rar (58 GB) - two build gates re-extract from it on every build
#   claude\           this project's Claude memory (+ transcripts with -IncludeAgentHistory)
#   migrate_scripts\  this folder, so the new laptop can run import_bundle.ps1 before anything is cloned
#
# NOT here, already on the new laptop from Map One's migration (2026-10-09): Steam BO3 + Mod Tools and
# their pack overlay, Documents\BO3_tools, test+map (PyCoD), Blender addons, BO3 keybinds, Radiant prefs,
# git identity, Codex config, the Blender MCP venv. Nothing of the Hellbound map moves (user 2026-10-12).
# Credentials (Claude, Codex, git, ELEVENLABS_API_KEY) are NOT copied.
param(
    [Parameter(Mandatory = $true)][string]$Dest,
    [switch]$DryRun,
    [switch]$AllowUnpushed,         # skip the "all work committed and pushed" gate (testing only)
    [switch]$SkipBuildOutput,       # leave the last build (usermaps\zm_tod2_cybercity, ~17 GB) behind
    [switch]$IncludeAgentHistory,   # this project's Claude session transcripts, not just memory
    [switch]$SkipT7Pack,            # leave Downloads\T7 Assets V2.8.rar (58 GB) behind - ONLY if the new laptop already has it
    [string]$Tod2Root = 'C:\BO3Tools\TOD2Cybercity'
)
$ErrorActionPreference = 'Stop'

# string join: Join-Path throws when -Dest's drive is not mounted yet (dry runs before the drive is in)
function PJ([string]$a, [string]$b) { return [System.IO.Path]::Combine($a, $b) }
# Windows PowerShell 5.1: under ErrorActionPreference Stop, `2>$null` on a NATIVE command turns its
# first stderr line into a terminating error. Run those here.
function NoErr([scriptblock]$sb) { $ErrorActionPreference = 'Continue'; & $sb 2>$null }
function Info($m) { Write-Host "[export] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[export] WARN: $m" -ForegroundColor Yellow; [void]$script:Warnings.Add($m) }
function Die($m)  { Write-Host "[export] FAIL: $m" -ForegroundColor Red; exit 1 }
$script:Warnings = New-Object System.Collections.ArrayList
$script:MissingRequired = New-Object System.Collections.ArrayList

$Repo     = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$H        = $env:USERPROFILE
$Py       = Join-Path $PSScriptRoot 'bundle_tool.py'
$ClaudeKey = $Repo -replace '[^A-Za-z0-9]', '-'
$ClaudeProj = Join-Path $H ".claude\projects\$ClaudeKey"

# ---------------------------------------------------------------- preflight
foreach ($p in 'BlackOps3', 'linker_modtools', 'cod2map64', 'radiant_modtools', 'converter', 'modlauncher', 'gdtdb', 'export2bin', 'GdtDBTray', 'asseteditor_modtools', 'blender') {
    if (Get-Process -Name $p -ErrorAction SilentlyContinue) {
        if ($DryRun) { Warn "$p is running - close it before the real export" } else { Die "$p is running. Close BO3 / the mod tools / Blender / any build first, so nothing changes mid-copy." }
    }
}
# a build is a powershell hosting build_map.ps1 (CLAUDE.md "Builds, gates, peers") - or its Start-Job host
# ('-s -NoLogo'), which is all a build started from a Claude shell tool shows (2026-10-13 review)
$builds = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" -ErrorAction SilentlyContinue | Where-Object { "$($_.CommandLine)" -match 'build_map\.ps1|build_when_idle|sync_to_modtools|\s-s\s+-NoLogo' })
if ($builds.Count -gt 0) {
    if ($DryRun) { Warn 'a Tower II build/sync (or a PowerShell job host) is running - wait for it before the real export' } else { Die 'a Tower II build/sync (or a PowerShell Start-Job host, which is how a build looks from a Claude shell) is running. Wait for it, then re-run.' }
}
foreach ($c in 'git', 'python', 'robocopy') { if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { Die "$c not found on PATH" } }
if (-not (Test-Path -LiteralPath (Join-Path $Tod2Root '.tod2-workspace.json'))) { Die "Tower II private root not found: $Tod2Root (pass -Tod2Root)" }

Push-Location $Repo
$dirty = @(git status --porcelain --untracked-files=no)
$ahead = NoErr { git rev-list --count '@{u}..HEAD' }
$branch = (git rev-parse --abbrev-ref HEAD)
$headAtStart = (git rev-parse HEAD)
Pop-Location
if ($dirty.Count -gt 0 -or "$ahead" -ne '0') {
    $msg = "the repo has $($dirty.Count) uncommitted tracked change(s) and '$ahead' unpushed commit(s) on $branch. GitHub + this bundle must together equal this folder: commit and push first (docs/220 step A2)."
    if ($DryRun -or $AllowUnpushed) { Warn $msg } else { Die $msg }
}

# (only when missing: PS 5.1 New-Item throws "not of a legal form" on a share root such as \\host\share)
if (-not $DryRun -and -not (Test-Path -LiteralPath $Dest)) { New-Item -ItemType Directory -Force -Path $Dest | Out-Null }
$LogDir = PJ $Dest 'logs'
if (-not $DryRun) { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null }
$RoboLog = PJ $LogDir 'robocopy.log'
$Items = New-Object System.Collections.ArrayList

function Add-Item($label, $bytes, $files, $dst) {
    [void]$Items.Add([pscustomobject]@{ item = $label; bytes = [int64]$bytes; files = $files; dest = $dst })
    Info ("{0,-52} {1,9:N2} GB" -f $label, ($bytes / 1e9))
}

# robocopy wrapper: reports the "Copied" byte column of the job summary (/BYTES); /L in dry runs.
# /XJ: never follow a junction. -Required: a missing source is listed at the end and the export exits 1.
function Robo([string]$label, [string]$src, [string]$dst, [string[]]$opts, [switch]$Required) {
    if (-not (Test-Path -LiteralPath $src)) {
        if ($Required) { [void]$script:MissingRequired.Add("$label ($src)") }
        Warn "$label - source missing, skipped: $src"; return
    }
    $a = @($src, $dst) + $opts + @('/XJ', '/COPY:DAT', '/DCOPY:T', '/R:1', '/W:1', '/NFL', '/NDL', '/NP', '/BYTES', '/NJH')
    if ($DryRun) { $a += '/L' } else { $a += @('/MT:64', '/TEE', "/LOG+:$RoboLog") }
    $out = & robocopy @a
    # >= 8 = robocopy failure; < 0 = robocopy killed from outside (-1) - never count either as copied
    if ($LASTEXITCODE -ge 8 -or $LASTEXITCODE -lt 0) { Die "robocopy failed ($LASTEXITCODE): $src -> $dst (see $RoboLog)" }
    $bytes = 0
    foreach ($l in $out) { if ($l -match '^\s*Bytes\s*:\s*(\d+)\s+(\d+)') { $bytes = [int64]$matches[2] } }
    Add-Item $label $bytes '' $dst
}

function Parse-Bytes($lines) {
    $b = 0; $f = 0
    foreach ($l in $lines) { if ("$l" -match 'BYTES=(\d+) FILES=(\d+)') { $b = [int64]$matches[1]; $f = [int]$matches[2] } }
    return @($b, $f)
}

Info "repo:         $Repo ($branch)"
Info "private root: $Tod2Root"
Info "bundle:       $Dest $(if ($DryRun) { '(DRY RUN - nothing is copied)' })"

# ---------------------------------------------------------------- 1. the private Mod Tools root (the big one)
$rtArgs = @($Py, 'root-export', '--dest', (PJ $Dest 'tod2_root'), '--root', $Tod2Root)
if ($DryRun) { $rtArgs += '--dry-run' }
if ($SkipBuildOutput) { $rtArgs += '--skip-build-output' }
$rt = & python @rtArgs   # no stderr redirect: a traceback must stay visible
$rtCode = $LASTEXITCODE
$rt | Where-Object { "$_" -notmatch '^BYTES=' } | ForEach-Object { Write-Host "    $_" }
if ($rtCode -ne 0) { Die 'private root export failed (see above) - fix it and re-run; finished files are kept' }
$r = Parse-Bytes $rt; Add-Item 'tod2_root (C:\BO3Tools\TOD2Cybercity)' $r[0] $r[1] 'tod2_root'

# ---------------------------------------------------------------- 2. repo files git does not track
$clArgs = @($Py, 'copylist', '--src', $Repo, '--dest', (PJ $Dest 'repo_extras'), '--git-untracked')
if ($DryRun) { $clArgs += '--dry-run' } else { $clArgs += @('--save-list', (PJ $Dest 'repo_extras.lst')) }
$cl = & python @clArgs
$clCode = $LASTEXITCODE
$cl | Where-Object { "$_" -notmatch '^BYTES=' } | ForEach-Object { Write-Host "    $_" }
if ($clCode -ne 0) { Die 'repo extras copy failed (see above)' }
$r = Parse-Bytes $cl; Add-Item 'repo_extras (tmp, source_library, *.blend1 ...)' $r[0] $r[1] 'repo_extras'

# ---------------------------------------------------------------- 3. Downloads Map One's bundle did not carry
# (Map One's took every loose file < 50 MB, BO6_Pilot_Export and the 3D Models zips on 2026-10-08; no
# loose Downloads file has changed since.) Hellbound_* stay: nothing of Hellbound moves (user 2026-10-12).
$DL = Join-Path $H 'Downloads'
foreach ($d in @(Get-ChildItem -LiteralPath $DL -Directory -Filter 'TOD2_*' -ErrorAction SilentlyContinue)) {
    Robo "downloads\$($d.Name)" $d.FullName (PJ $Dest "downloads\$($d.Name)") @('/E')
}
# T7 Assets V2.8.rar IS A BUILD INPUT (2026-10-12 audit): keeper/install_keeper.py --check and
# dealer_boss/install.py --check re-extract their members from it with 7-Zip on EVERY build, -GscOnly
# included, and build_map.ps1 dies without it. 58 GB, one file: /Z restartable (a Wi-Fi drop resumes it),
# and its SHA1 rides along so the import can prove the copy. -SkipT7Pack only when the new laptop already
# holds a byte-identical copy (compare the SHA1 below).
$T7 = Join-Path $DL 'T7 Assets V2.8.rar'
if (-not $SkipT7Pack) {
    Robo 'downloads\T7 Assets V2.8.rar (build input)' $DL (PJ $Dest 'downloads') @('T7 Assets V2.8.rar', '/Z') -Required
    if (-not $DryRun -and (Test-Path -LiteralPath $T7)) {
        $shaFile = PJ $Dest 'downloads\T7 Assets V2.8.rar.sha1'
        $len = (Get-Item -LiteralPath $T7).Length
        $have = if (Test-Path -LiteralPath $shaFile) { (Get-Content -LiteralPath $shaFile -Raw).Trim() } else { '' }
        if ($have -notmatch "^[0-9A-F]{40} $len$") {
            Info 'hashing T7 Assets V2.8.rar (SHA1, ~3 min) ...'
            "$((Get-FileHash -LiteralPath $T7 -Algorithm SHA1).Hash) $len" | Set-Content -Encoding ascii -LiteralPath $shaFile
        }
    }
} else { Warn 'T7 Assets V2.8.rar skipped (-SkipT7Pack): the new laptop must already hold a byte-identical copy in Downloads, or the keeper / dealer gates fail every build' }

# ---------------------------------------------------------------- 4. Claude memory (+ history)
Robo 'claude\memory (this project)' (Join-Path $ClaudeProj 'memory') (PJ $Dest 'claude\memory') @('/E') -Required
if ($IncludeAgentHistory) {
    Robo 'claude\project (session transcripts)' $ClaudeProj (PJ $Dest 'claude\project') @('/E', '/XD', 'memory')
}

# ---------------------------------------------------------------- 5. versions + the scripts themselves
if (-not $DryRun) {
    $pyd = PJ $Dest 'python'; New-Item -ItemType Directory -Force -Path $pyd | Out-Null
    NoErr { & python -m pip freeze } | Set-Content -Encoding utf8 (PJ $pyd 'global-freeze.txt')
    $facts = @(
        "exported   : $(Get-Date -Format s)",
        "computer   : $env:COMPUTERNAME  user: $env:USERNAME  profile: $H",
        "repo       : $Repo  branch: $branch  head: $(git -C $Repo rev-parse --short HEAD)",
        "root       : $Tod2Root",
        "git        : $(git --version)",
        "git-lfs    : $(NoErr { git lfs version })",
        "node       : $(node --version)",
        "python     : $(NoErr { python --version })",
        "user env   : $(((Get-ItemProperty 'HKCU:\Environment' -ErrorAction SilentlyContinue).PSObject.Properties.Name | Where-Object { $_ -notmatch '^PS' }) -join ', ') (names only)"
    )
    $facts | Set-Content -Encoding utf8 (PJ $Dest 'machine_facts.txt')
    Robo 'migrate_scripts (run import_bundle.ps1 from here)' $PSScriptRoot (PJ $Dest 'migrate_scripts') @('/E', '/XD', '__pycache__')
    Copy-Item (Join-Path $Repo 'docs\220_new_laptop_migration.md') (PJ $Dest 'SETUP_GUIDE.md') -Force
}

# ---------------------------------------------------------------- the repo must not have moved during the copy
# (2026-10-13 review): a tracked edit or a new commit after the start gate is neither on GitHub nor in
# repo_extras (which carries only untracked files) - BUNDLE OK would then be a lie.
if (-not $DryRun -and -not $AllowUnpushed) {
    Push-Location $Repo
    $dirty2 = @(git status --porcelain --untracked-files=no)
    $ahead2 = NoErr { git rev-list --count '@{u}..HEAD' }
    $head2 = (git rev-parse HEAD)
    Pop-Location
    if ($dirty2.Count -gt 0 -or "$ahead2" -ne '0' -or $head2 -ne $headAtStart) {
        Die "the repo changed while the bundle was being made ($($dirty2.Count) uncommitted tracked change(s), '$ahead2' unpushed, HEAD $headAtStart -> $head2). Commit + push, then re-run this export: it resumes and only refreshes what changed."
    }
}

# ---------------------------------------------------------------- summary
$total = ($Items | Measure-Object -Property bytes -Sum).Sum
Info ('-' * 64)
if (-not $DryRun) {
    # a resumed run copies only what was missing, so measure the bundle itself for the real size
    $du = & python $Py du $Dest --json | ConvertFrom-Json
    $total = [int64]$du[0].bytes
    Info ("bundle on disk: {0:N0} files" -f $du[0].files)
}
Info ("TOTAL {0,56:N2} GB" -f ($total / 1e9))
if ($script:Warnings.Count -gt 0) {
    Info "$($script:Warnings.Count) warning(s) during the export:"
    foreach ($w in $script:Warnings) { Write-Host "    - $w" -ForegroundColor Yellow }
}
if ($DryRun) {
    Info 'DRY RUN only. Nothing was copied. Run again without -DryRun to build the bundle.'
    if ($script:MissingRequired.Count -gt 0) { Warn "REQUIRED items missing: $($script:MissingRequired -join '; ')" }
    exit 0
}
$manifest = [pscustomobject]@{
    created = (Get-Date -Format s); source_computer = $env:COMPUTERNAME; repo_branch = $branch
    repo_head = (git -C $Repo rev-parse HEAD); github = 'https://github.com/JordanUrbaezLu/tower_of_doom_II_cybercity'
    tod2_root = $Tod2Root; total_bytes = $total; items = $Items
    warnings = $script:Warnings; missing_required = $script:MissingRequired
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 (PJ $Dest 'bundle_manifest.json')
@"
TOWER OF DOOM II: CYBERCITY - TRANSFER BUNDLE ($(Get-Date -Format s), from $env:COMPUTERNAME)

On the NEW laptop (Map One's migration already done there: Steam BO3 + Mod Tools, Git, Python, Node,
Blender), with BO3 and every build closed:

  powershell -ExecutionPolicy Bypass -File "<this folder>\migrate_scripts\import_bundle.ps1"

It clones the repo from GitHub, puts every file in this bundle where it belongs (the private root
C:\BO3Tools\TOD2Cybercity included) and finishes with check_machine.ps1. Full instructions:
SETUP_GUIDE.md (= docs/220 in the repo).
"@ | Set-Content -Encoding utf8 (PJ $Dest 'README.txt')
if ($script:MissingRequired.Count -gt 0) {
    Write-Host "[export] FAIL: the bundle is INCOMPLETE - required item(s) missing:" -ForegroundColor Red
    foreach ($m in $script:MissingRequired) { Write-Host "    - $m" -ForegroundColor Red }
    exit 1
}
Info "BUNDLE OK -> $Dest"
