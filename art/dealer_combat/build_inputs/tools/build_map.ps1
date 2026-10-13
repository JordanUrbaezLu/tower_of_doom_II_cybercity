# =============================================================================
# build_map.ps1 - ONE-COMMAND headless build of zm_tod2_cybercity.
# Ported from abandoned_cyber_city_zombies (proven pipeline; same gotchas).
#
#   .\tools\build_map.ps1            FULL geometry build (any .map / brush /
#                                    entity / material / sky change):
#                                    sync -> cod2map64 (BSP+navmesh, cwd=bin)
#                                    -> Radiant LED -> linker -> verify .ff
#                                    cod2map + the LED bake are SKIPPED when the
#                                    .map, its materials/textures and the sky are
#                                    byte-identical to the last full build
#                                    (tools/geom_key.js; -ForceBake overrides,
#                                    -Publish always bakes).
#   .\tools\build_map.ps1 -GscOnly   FAST path for GSC/CSC/.zone-only changes:
#                                    sync -> linker (reuses the last BSP).
#   .\tools\build_map.ps1 -Run       build, then launch run_game.ps1 on success.
#   .\tools\build_map.ps1 -CleanPak  FULL build that also rewrites zone\*.xpak
#                                    from scratch (the linker only ever appends
#                                    to it; -Publish implies this, -KeepPak
#                                    opts out; node tools/xpak_report.js proves it).
#
# Other switches: -SkipSync, -SkipLED (RED FLAG - hides a broken bake),
# -DryRun, -ModToolsRoot <path>.
#
# Exit 0 = a fresh .ff was written (THE success oracle - the linker exit code
# lies: it prints ERROR: for waived/substituted assets yet still packs a valid
# .ff). Exit 1 = a stage failed.
# =============================================================================

[CmdletBinding()]
param(
    # Publish builds: also link every non-English language fastfile (fr_/ge_/...).
    # Without these, NON-ENGLISH game clients fail AT MAP LOAD with
    # "Could not find zone '<xx>_zm_tod2_cybercity'" (live Workshop report
    # 2026-08-26, French player). ~1 min per language, opt-in.
    [switch]$AllLanguages,
    # PUBLISH GATE (repo review 2026-09-01): refuses an armed level.tod_dev /
    # level.tod_god, refuses -GscOnly, implies -AllLanguages, and refuses
    # backup files parked in the deployed zone\. See section 0b below.
    [switch]$Publish,
    # PATCH-NOTES GATE (user 2026-09-02: "when I ask for a full build for
    # publish prep we need to generate patch notes as well"): -Publish refuses
    # to build until tools/patch_notes.js check passes (a staged ledger row
    # whose cutoff is the top CHANGELOG entry, and docs/68 + the BBCode file
    # lead with that version's section). Emergency bypass only:
    [switch]$SkipNotesGate,
    # CLEAN PACK (2026-09-03, docs/86): the linker only APPENDS to
    # zone\<map>.xpak - every full build leaves the previous build's
    # reflection probes / probe volumes / sun-shadow tree behind and every
    # replaced asset leaves a hole, so the pack the Workshop ships grew to
    # 9.5 GB with ~5.3 GB of build history in it (47 shadow trees under one
    # name). -CleanPak moves ALL map/language packs OUT of zone\ before the
    # link, implies -AllLanguages, and retains previous fastfiles/sound banks
    # until every language passes. Failure restores the complete old set.
    # FULL build only. -Publish implies it;
    # -KeepPak opts a publish out. Prove it: node tools/xpak_report.js
    [switch]$CleanPak,
    [switch]$KeepPak,
    # FRESH OCCLUSION (2026-09-28, the Battle Arena "no textures, everything
    # invisible" report): clear this map's Umbra caches before the link. FULL
    # builds always do it; this switch makes a -GscOnly relink do it too
    # (needed once to repair a .ff linked against a stale cache).
    [switch]$FreshOcclusion,
    [string]$ModToolsRoot = '',
    [switch]$GscOnly,
    [switch]$SkipSync,
    [switch]$SkipLED,
    # FORCE BAKE (2026-09-29): a FULL build normally reuses the last full build's
    # compiled map + lighting when tools/geom_key.js proves every input identical
    # (the bake peaks at ~16 GB and froze the PC). This always compiles + bakes.
    [switch]$ForceBake,
    [switch]$Run,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$MapName  = 'zm_tod2_cybercity'
$RepoRoot = Split-Path $PSScriptRoot -Parent

# Known NON-FATAL linker 'ERROR:' substrings (missing-but-substituted assets).
# Empty for now - grow it only for user-waived, verified-cosmetic errors.
# Known NON-FATAL linker 'ERROR:' substrings — the linker substitutes a default
# and still packs a valid .ff. All five are BYTE-IDENTICAL to map 1's shipped
# errorlog (its Panzer/zod boss packs; map 1 played fine with them):
#   - the electroball 115-grenade's 4 unbundled materials (cosmetic substitution)
#   - mechz.zpkg (map 1 CHANGELOG: "cosmetic")
$WaivedLinkerErrors = @(
    # 2026-10-05: the 115-grenade / gobblegum / mechz.zpkg / knife_melee_surface waivers are GONE with the Panzer pack and the Map One kit (W2E); the wave-2 link printed only the three below. A reappearance is a real regression.
    # The fuse-quest prop model: the STOCK companion package (share\zone_source\zm_ai_zod_companion.zpkg, the
    # Civil Protector partner's AI) lists xmodel p7_zm_zod_fuse + the two _hb21_zm_craft_fuse scripts. The model
    # has no source here (cosmetic, unused); the scripts must stay in scripts/zm/craftables/ because that package
    # names them. The 2026-10-04 Map 1 purge archived both and dropped this waiver; the link failed (full4.log).
    "xmodel 'p7_zm_zod_fuse' is missing"
    # v9.37 breather teleporters (_tod_teleport.gsc): the kino arrival FX
    # (dlc5/theater/fx_teleport_flashback_kino) spawns a BEAM whose material
    # exists only as a beam reference in stock t7_beams.gdt — no material GDT
    # anywhere, so the linker logs it and substitutes. The beam RENDERS in
    # game (user-verified 2026-08-23: "Seems good, the teleporters").
    'gfx_teleport_tube_em_scroll_nocull'
    # THE THREE reflex_* ERRORS: CLOSED 2026-08-28 — FIXED, NEVER WAIVED,
    # and the answer to the recorded in-game exit condition was NOT BENIGN.
    # The user's play report ("the UDM has a weird sight. Like a sight that
    # you cant even see through") was the exit condition firing negative:
    # reflex_reddot_lens_ads is literally the ADS lens material, and missing
    # meant an OPAQUE optic on the PaP'd SLASHER tier-2 sidearm. Resolution
    # (parallel cybercity session, same day): the port was incomplete —
    # skinOverride SOURCES need not exist, TARGETS and un-remapped slots
    # must, and the porter had remapped exactly one mesh's slots. Every
    # reflex_* slot on all four UDM meshes now remaps to materials the UDM's
    # own GDT declares (lens -> weapon_udm45_glass etc.); edit lives in the
    # TOOLS-ROOT-ONLY source_data\skye_iw7_udm.gdt (backup .tod-reflex-orig;
    # root-only GDTs SURVIVE builds — our sync copies, never mirrors).
    # Verified: the 20:22 build logged ZERO reflex errors.
    # DO NOT ADD THE THREE NAMES TO THE WAIVE LIST — if a reflex_* error
    # ever reappears here it means the root GDT fix was lost (a pack
    # reinstall, a new machine), and the UNEXPECTED lane below flagging it
    # is exactly the alarm we want. Portable lesson for any ported gun
    # throwing "material not found in gdtDB": check the skinOverride
    # source/target asymmetry before waiving or dropping the gun.
    # (History: briefly waived 2026-08-28 on root-cause evidence alone;
    # reverted the same hour — the bar was seeing it render, and holding
    # that bar is what caught a real defect. A cross-map "fires with zero
    # UDM assets" scare was RETRACTED: it paired remembered console output
    # with a later run's assetlist. Pair build symptoms only with artifacts
    # from the SAME run. The HK21 was a red herring — only its unused
    # reflex variant is packed.)
    # Gift of Death pack's bundled window-glass-shard debris props — their
    # native material isn't in the modtools gdtDB (stock material, substitutes
    # at runtime). Cosmetic; the .ff builds. (skinOverride black_glass blanked)
    'mtl_glass was not found'
    # STORMBREAKER (the Leviathan Axe port, 2026-08-22): its sharedweaponsounds
    # "fireaxe" chain references the STOCK surfacesounddef assets
    # knife_melee_surface / knife_melee_surface_plr, which are not in the
    # modtools gdtDB. Map 1 shipped the same axe with the identical two lines
    # (its CHANGELOG attributes them to leviathan_zm); surface-impact sound
    # defs only — the weapon links and plays. Cosmetic.
)

function Info($m) { Write-Host "[build] $m" -ForegroundColor Cyan }
function Step($m) { Write-Host ""; Write-Host "[build] === $m ===" -ForegroundColor White }
function Warn($m) { Write-Host "[build] WARN: $m" -ForegroundColor Yellow }
function Die($m)  {
    if ($script:TodPakTransaction) { Undo-TodCleanPaks $script:TodPakTransaction }
    Write-Host ""; Write-Host "[build] FAIL: $m" -ForegroundColor Red; exit 1
}
. (Join-Path $PSScriptRoot 'clean_paks.ps1')
$script:TodPakTransaction = $null
trap {
    if ($script:TodPakTransaction) { Undo-TodCleanPaks $script:TodPakTransaction }
    throw
}

. (Join-Path $PSScriptRoot 'tod2_workspace.ps1')
if ($MapName -ne $script:Tod2Map) { throw 'TOD II isolation: wrong map identity in build script.' }
function Resolve-ToolsRoot([string]$override) { Resolve-Tod2Root $override }

# GAME-RUNNING GUARD (2026-08-18 crash incident, map 1 precedent): the game
# file-locks the .sabs sound bank while running — a build regenerating the
# banks against the locked/stale cache emits CORRUPT banks -> silent
# 0xC0000005 mid-DB-load at the NEXT launch (no log error, just a minidump).
# CROSS-SESSION LINKER LOCK (2026-08-21): two Claude sessions built this map
# at once; the later linker overwrote the earlier clean output with banks it
# generated while the game held the alias file -> black-screen hang. One
# linker per usermap, ever. If another linker_modtools.exe is alive, it is
# either a concurrent build or a zombie from a collided one — both are
# reasons to STOP, not race. Never remove this.
$otherLinker = Get-Process linker_modtools -ErrorAction SilentlyContinue
if ($otherLinker) {
    Die "another linker_modtools.exe is RUNNING (pid $($otherLinker.Id)) - a concurrent or zombie build. Wait for it (or kill it if it is a leftover), then build. Two linkers on one usermap corrupt the sound banks."
}

# THE OTHER TWO BUILD STAGES (2026-09-01). The linker check above is necessary
# and was NOT sufficient: it only covers the PACK stage. A full build spends most
# of its wall time in cod2map64 (BSP) and Radiant_modtools (LED bake), and during
# those stages NO linker_modtools exists — so this script would happily start,
# and the very first thing it does is SYNC THE SOURCE TREE. That means a second
# build launched during someone else's bake rewrites the inputs underneath it and
# then links against a half-written BSP.
#
# That failure is WORSE than the two-linker one this guard was built for, because
# it is not obviously broken: it produces a .ff that is internally inconsistent,
# and the sanctioned freshness diff CANNOT catch it — that diff compares SOURCE
# trees and knows nothing about the compiled BSP.
#
# Live near-miss 2026-09-01: a -GscOnly was about to start while Radiant_modtools
# (pid 35416) was 66 seconds into a peer session's LED bake, with ~3.6 cores
# pegged. Nothing in this script would have stopped it; it was caught by a human
# -- well, by an agent -- looking at the process list by hand.
$otherBake = Get-Process Radiant_modtools,cod2map64 -ErrorAction SilentlyContinue
if ($otherBake) {
    $names = ($otherBake | ForEach-Object { "$($_.Name) (pid $($_.Id))" }) -join ', '
    Die "a build STAGE is already running: $names - that is someone else's cod2map/LED bake. This script SYNCS THE SOURCE TREE as its first step, so starting now would rewrite that build's inputs mid-flight and link against a half-written BSP. Wait for it to finish, then build."
}

# Never build while BlackOps3 is up. (run_game.ps1 has the inverse guard.)
$gameProc = Get-Process BlackOps3 -ErrorAction SilentlyContinue
if ($gameProc) {
    Die "BlackOps3 is RUNNING (pid $($gameProc.Id)) - a build now would corrupt the sound banks (locked .sabs). Close the game, then build."
}

# GAME WATCHDOG (2026-08-24, user: "make sure to never start a build if im in
# game. Should be something as part of the process that we keep missing").
# The check above covers the START; the end-of-linker sample covers the END.
# The blind spot both nights was the MIDDLE: a session that starts AND ends
# inside the ~4-minute build window trips neither, and that overlap is the top
# suspect for the intermittent wav-converter faults. This job polls every 2s
# for the whole build and drops a flag file the instant BlackOps3 appears; the
# end guard treats that flag exactly like catching the game live. The job is a
# child of THIS PowerShell session, so it dies with the script — it can never
# outlive the build (the 2026-08-21 orphaned-watcher lesson does not apply).
$GameSeenFlag = Join-Path $env:TEMP ("tod_build_gameseen_{0}.flag" -f $PID)
if (Test-Path $GameSeenFlag) { Remove-Item $GameSeenFlag -Force }
$GameWatchJob = Start-Job -ArgumentList $GameSeenFlag -ScriptBlock {
    param($flag)
    while ($true) {
        if (Get-Process BlackOps3 -ErrorAction SilentlyContinue) {
            Set-Content -Path $flag -Value (Get-Date -Format o)
        }
        Start-Sleep -Seconds 2
    }
}

# --- resolve tools root + exe paths ----------------------------------------
try { $Tools = Resolve-ToolsRoot $ModToolsRoot } catch { Die $_.Exception.Message }
Set-Tod2ProcessEnvironment
$Bin     = Join-Path $Tools 'bin'
$Cod2    = Join-Path $Bin 'cod2map64.exe'
$Radiant = Join-Path $Bin 'Radiant_modtools.exe'
$Linker  = Join-Path $Bin 'linker_modtools.exe'
$MapSrc  = Join-Path $Tools ("map_source\zm\{0}.map"        -f $MapName)
$Bsp     = Join-Path $Tools ("share\raw\maps\zm\{0}.d3dbsp" -f $MapName)
$NavHkt  = Join-Path $Tools ("share\raw\maps\zm\{0}_navmesh.hkt" -f $MapName)
$FfDir   = Join-Path $Tools ("usermaps\{0}\zone" -f $MapName)
$RepoMap = Join-Path $RepoRoot ("map_source\zm\{0}.map" -f $MapName)

# ===========================================================================
# 0b. PUBLISH GATE (-Publish; repo review 2026-09-01). CLAUDE.md: "A PUBLISH IS
#     NEVER A RELABEL OF AN ARMED ARTIFACT: flags false, then a fresh FULL
#     build, then publish." The two flags have cycled armed/disarmed at least
#     five times by their own comment history, and three sessions share this
#     repo, so the rule is now a gate rather than a memory:
#       * level.tod_dev / level.tod_god armed -> WARN on every build,
#         FAIL with -Publish (the assignment lines are the truth, not comments)
#       * -Publish refuses -GscOnly (a publish is a fresh FULL build)
#       * -Publish implies -AllLanguages (non-English clients need their ff;
#         the deploy tree carried five-day-old language ffs on 2026-09-01)
#       * -Publish refuses *.orig / *.bak* files parked in the deployed zone\
#         (they upload with the item)
# ===========================================================================
# devw* NOT dev (2026-09-07): level.tod_dev_money was added as a SEPARATE
# flag so "unlimited money" stops implying upgrades-every-round and a Panzer
# from round 3 -- and the old pattern did not match it, because `tod_dev` is
# followed by `_money`, not by `=`. A dev flag this gate cannot see is a dev
# flag that ships. Any future tod_dev<anything> is caught now.
$EntryGsc   = Join-Path $RepoRoot 'scripts\zm\zm_tod2_cybercity.gsc'
$armedFlags = @()
if (Test-Path $EntryGsc) {
    $armedFlags = @(Select-String -Path $EntryGsc -Pattern '^\s*level\.tod_(dev\w*|god)\s*=\s*true\s*;' |
                    ForEach-Object { $_.Line.Trim() })
}
if ($armedFlags.Count -gt 0) {
    if ($Publish) {
        Die ("PUBLISH GATE: dev/test flags are ARMED in {0}: {1}  -> set both to false, rebuild FULL, then publish" -f $EntryGsc, ($armedFlags -join ' | '))
    }
    Warn ("dev/test flags ARMED ({0}) - fine for a test build; NEVER publish this .ff" -f ($armedFlags -join ' | '))
}

# THE LUA MOCK FLAG (v17.3). TOD_MOCK_PARTY in AetheriumHud.lua replaces the
# three party rows with fakes so the co-op HUD can be seen solo. Lua has no
# level.tod_dev, so it CANNOT be dev-gated in the file itself - and while armed
# it MASKS REAL TEAMMATES in co-op. Map 1 carried the identical flag with a
# comment saying to manage it by hand; this is that comment turned into a gate.
$HudLua = Join-Path $RepoRoot 'ui\uieditor\menus\hud\AetheriumHud.lua'
if (Test-Path $HudLua) {
    $armedMock = @(Select-String -Path $HudLua -Pattern '^\s*local\s+TOD_MOCK_PARTY\s*=\s*true\b' |
                   ForEach-Object { $_.Line.Trim() })
    if ($armedMock.Count -gt 0) {
        if ($Publish) {
            Die ("PUBLISH GATE: TOD_MOCK_PARTY is ARMED in {0}: {1}  -> set it to false, rebuild FULL, then publish (armed, it hides real teammates)" -f $HudLua, ($armedMock -join ' | '))
        }
        Warn ("TOD_MOCK_PARTY ARMED - fake party rows are ON and REAL teammates are hidden; fine solo, NEVER publish this .ff")
    }
}

# THE CROWN PARTNER TEST BENCHES (2026-09-28). TOD_PARTNER_TEST_BENCHES in
# _tod_partners.gsc puts four free equip/swap benches in the crown hall for
# the user's companion testing. Players must never get free partners.
$PartnersGsc = Join-Path $RepoRoot 'scripts\zm\zm_tod2_cybercity\_tod_partners.gsc'
if (Test-Path $PartnersGsc) {
    $armedBench = @(Select-String -Path $PartnersGsc -Pattern '^\s*#define\s+TOD_PARTNER_TEST_BENCHES\s+1\b' |
                    ForEach-Object { $_.Line.Trim() })
    if ($armedBench.Count -gt 0) {
        if ($Publish) {
            Die ("PUBLISH GATE: TOD_PARTNER_TEST_BENCHES is ARMED in {0} -> set it to 0, rebuild, then publish (armed, the crown hands out free partners)" -f $PartnersGsc)
        }
        Warn ("TOD_PARTNER_TEST_BENCHES ARMED - four free partner benches in the crown hall; NEVER publish this .ff")
    }
}

# THE CROWN TESTER KIT (2026-10-01). TOD_TESTER_KIT in _tod_tester.gsh places the crown's CLASS
# TERMINAL (any player can switch class for the rest of the run). The user plans a TESTING-PHASE
# release that ships it on purpose ("testers have access to everything in the crown"), so -Publish
# WARNS instead of refusing: set it to 0 for an ordinary release.
$TesterGsh = Join-Path $RepoRoot 'scripts\zm\zm_tod2_cybercity\_tod_tester.gsh'
if (Test-Path $TesterGsh) {
    $armedKit = @(Select-String -Path $TesterGsh -Pattern '^\s*#define\s+TOD_TESTER_KIT\s+1\b' |
                  ForEach-Object { $_.Line.Trim() })
    if ($armedKit.Count -gt 0) {
        Warn ("TOD_TESTER_KIT is ON ({0}) - the crown's CLASS TERMINAL ships in this .ff. Right for a TESTING-PHASE release; set it to 0 for an ordinary one" -f $TesterGsh)
    }
}

# THE DEALER TEST SPAWN + LOG (docs/199). TOD_DEALER_TEST_SPAWN in _tod_dealer_finale.gsc spawns the
# final boss in the crown hall after the opening for the playtest; TOD_DEALER_LOG prints with dev OFF.
$DealerGsc = Join-Path $RepoRoot 'scripts\zm\zm_tod2_cybercity\_tod_dealer_finale.gsc'
if (Test-Path $DealerGsc) {
    $armedDealer = @(Select-String -Path $DealerGsc -Pattern '^\s*#define\s+TOD_DEALER_(TEST_SPAWN|LOG)\s+1\b' |
                    ForEach-Object { $_.Line.Trim() })
    if ($armedDealer.Count -gt 0) {
        if ($Publish) {
            Die ("PUBLISH GATE: {0} is ARMED in {1} -> set it to 0, rebuild, then publish" -f ($armedDealer -join '; '), $DealerGsc)
        }
        Warn ("THE DEALER test state ARMED ({0}) - he spawns in the crown hall / logs with dev off; NEVER publish this .ff" -f ($armedDealer -join '; '))
    }
}

# THE DEALER'S HOUSE LOG (docs/207). TOD_HOUSE_LOG in _tod_house.gsc prints the finale's records with dev OFF for
# the playtest; the same rule as the Dealer's own log.
$HouseGsc = Join-Path $RepoRoot 'scripts\zm\zm_tod2_cybercity\_tod_house.gsc'
if (Test-Path $HouseGsc) {
    $armedHouse = @(Select-String -Path $HouseGsc -Pattern '^\s*#define\s+TOD_HOUSE_LOG\s+1\b' | ForEach-Object { $_.Line.Trim() })
    if ($armedHouse.Count -gt 0) {
        if ($Publish) {
            Die ("PUBLISH GATE: {0} is ARMED in {1} -> set it to 0, rebuild, then publish" -f ($armedHouse -join '; '), $HouseGsc)
        }
        Warn ("THE DEALER'S HOUSE log ARMED ({0}) - prints with dev off; NEVER publish this .ff" -f ($armedHouse -join '; '))
    }
}

# THE LUA HUD PROBE (v17.21). TOD_HUD_DEBUG in AetheriumLoadout.lua appends the
# resolved weapon CATEGORY to the weapon-name band ("MAC-10 SMG" / "MAC-10 NIL")
# so a single play session can say which link of the gun-icon chain is broken.
# Same reasoning as TOD_MOCK_PARTY above: Lua cannot read level.tod_dev, so the
# file cannot gate itself, and armed it puts debug text on a player's HUD.
$LoadoutLua = Join-Path $RepoRoot 'ui\uieditor\widgets\HUD\AetheriumWidgets\AetheriumLoadout.lua'
if (Test-Path $LoadoutLua) {
    $armedProbe = @(Select-String -Path $LoadoutLua -Pattern '^\s*local\s+TOD_HUD_DEBUG\s*=\s*true\b' |
                    ForEach-Object { $_.Line.Trim() })
    if ($armedProbe.Count -gt 0) {
        if ($Publish) {
            Die ("PUBLISH GATE: TOD_HUD_DEBUG is ARMED in {0}: {1}  -> set it to false, rebuild, then publish (armed, it prints the weapon category on the HUD)" -f $LoadoutLua, ($armedProbe -join ' | '))
        }
        Warn ("TOD_HUD_DEBUG ARMED - the weapon name band reads '<NAME> <CATEGORY>'; fine for a test build, NEVER publish this .ff")
    }
}

# CLASS COUNT LOCKSTEP (2026-10-04): the GSC draft count and the Lua card count are one number in two languages.
# TOD_CLS_COUNT (scripts\zm\zm_tod2_cybercity\_tod_class_count.gsh, #inserted by _tod_class_select.gsc and
# _tod_class_terminal.gsc) sizes the server's draft; CLASS_N (tod_class_select.lua) sizes the panel's cards, because Lua
# cannot read a GSC define. Every disagreement is SILENT in game (a card the server refuses, or a class nobody can pick),
# so a mismatch is a hard Die here.
$ClsGsh = Join-Path $RepoRoot 'scripts\zm\zm_tod2_cybercity\_tod_class_count.gsh'
$ClsLua = Join-Path $RepoRoot 'ui\uieditor\menus\hud\tod_class_select.lua'
if (-not (Test-Path -LiteralPath $ClsGsh) -or -not (Test-Path -LiteralPath $ClsLua)) { Die ("CLASS COUNT: missing {0} or {1}" -f $ClsGsh,$ClsLua) }
$gscN = [regex]::Match((Get-Content -LiteralPath $ClsGsh -Raw), '(?m)^\s*#define\s+TOD_CLS_COUNT\s+(\d+)').Groups[1].Value
$luaN = [regex]::Match((Get-Content -LiteralPath $ClsLua -Raw), '(?m)^\s*local\s+CLASS_N\s*=\s*(\d+)').Groups[1].Value
if (-not $gscN -or $gscN -ne $luaN) { Die ("CLASS COUNT MISMATCH: TOD_CLS_COUNT={0} in {1} but CLASS_N={2} in {3}" -f $gscN,$ClsGsh,$luaN,$ClsLua) }

if ($Publish) {
    if ($GscOnly) { Die "PUBLISH GATE: -Publish needs a FULL build (drop -GscOnly)" }
    if (-not $AllLanguages) { $AllLanguages = $true; Info "-Publish: language fastfiles enabled (-AllLanguages)" }
    if ($KeepPak) { Warn "-KeepPak: this publish will upload the pack WITH its build history (node tools/xpak_report.js shows how much)" }
    elseif (-not $CleanPak) { $CleanPak = $true; Info "-Publish: clean pack enabled (-CleanPak; -KeepPak to opt out)" }
    $stray = @(Get-ChildItem $FfDir -File -ErrorAction SilentlyContinue |
               Where-Object { $_.Name -match 'tod-preart-orig$|\.orig$|\.bak(-|$)' })
    if ($stray.Count -gt 0) {
        Die ("PUBLISH GATE: backup files in the deployed zone\ would upload with the item: {0}" -f (($stray | ForEach-Object { $_.Name }) -join ', '))
    }
    Info "PUBLISH GATE: flags disarmed, full build, language ffs on, zone\ clean"
    # PATCH-NOTES GATE — see the -SkipNotesGate comment in param(). The flow:
    #   node tools/patch_notes.js window   (what changed since the last upload)
    #   write the section in docs/68_patch_notes.md + docs/68_patch_notes_steam_bbcode.txt
    #   node tools/patch_notes.js stage --version vX.Y
    #   .\tools\build_map.ps1 -Publish     (this gate; 'built' stamps the .ff time below)
    #   upload, then: node tools/patch_notes.js uploaded
    if ($SkipNotesGate) {
        Warn "PATCH-NOTES GATE SKIPPED (-SkipNotesGate) - this upload will go out without notes again"
    } else {
        $pn = Join-Path $PSScriptRoot 'patch_notes.js'
        & node $pn check
        if ($LASTEXITCODE -ne 0) { Die "PATCH-NOTES GATE: no patch notes staged for this publish (see the message above; -SkipNotesGate to bypass in an emergency)" }
    }
}

Info "mod tools root = $Tools"
# (the FULL wording keeps "FULL geometry": tools/art_cohesion/record_color_build.py reads it)
Info ("mode = {0}{1}" -f $(if ($GscOnly) { 'GSC-ONLY (linker only)' } else { 'FULL geometry (cod2map64 + LED + linker; cod2map + LED reused when nothing they read changed)' }), $(if ($DryRun) { '  [DRY RUN]' } else { '' }))
foreach ($e in @($Cod2, $Radiant, $Linker)) {
    if (-not (Test-Path $e)) { Die "missing compiler exe: $e" }
}

# --- native-exe runner: capture stdout/stderr to temp files ------------------
function Invoke-BuildExe($exe, [string[]]$argList, $label, $workDir) {
    Info ("{0}: {1} {2}" -f $label, (Split-Path $exe -Leaf), ($argList -join ' '))
    if ($DryRun) { Info "  DRY: not executed"; return [pscustomobject]@{ Code = 0; Out = ''; Err = '' } }
    # Another repo can start during our long source-validation phase. Recheck
    # at each native stage so separate roots do not exhaust memory together.
    $waiting = $false
    while (Get-Process linker_modtools,cod2map64,Radiant_modtools,gdtdb -ErrorAction SilentlyContinue) {
        if (-not $waiting) { Info 'waiting for the other native build stage to finish'; $waiting = $true }
        if (Get-Process BlackOps3 -ErrorAction SilentlyContinue) { Die 'BlackOps3 started while waiting; build stopped.' }
        Start-Sleep -Seconds 2
    }
    if (Get-Process BlackOps3 -ErrorAction SilentlyContinue) { Die 'BlackOps3 is running; refusing to start a native build stage.' }
    $o  = New-TemporaryFile
    $er = New-TemporaryFile
    try {
        $p = Start-Process -FilePath $exe -ArgumentList $argList -WorkingDirectory $workDir `
                 -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $o.FullName -RedirectStandardError $er.FullName
        $out = Get-Content $o.FullName -Raw -ErrorAction SilentlyContinue
        $err = Get-Content $er.FullName -Raw -ErrorAction SilentlyContinue
        if ($label -like 'linker*') {
            # Preserve converter diagnostics before temporary output is removed.
            # The summary alone hides useful model/texture conversion messages.
            $linkTranscriptDir = Join-Path $RepoRoot 'tmp\native_build'
            New-Item -ItemType Directory -Force -Path $linkTranscriptDir | Out-Null
            $linkTranscriptName = ($label -replace '[^a-zA-Z0-9_-]', '_') + '_last.log'
            @($out, $err) | Set-Content -LiteralPath (Join-Path $linkTranscriptDir $linkTranscriptName) -Encoding UTF8
        }
    } finally {
        Remove-Item $o.FullName, $er.FullName -ErrorAction SilentlyContinue
    }
    return [pscustomobject]@{ Code = $p.ExitCode; Out = [string]$out; Err = [string]$err }
}

function Q($p) { '"' + $p + '"' }

# ===========================================================================
# 1. sync repo -> Mod Tools (linker builds the DEPLOYED copy - skipping this
#    silently builds STALE code; cost map 1 hours)
# ===========================================================================
if (-not $DryRun) {
    & python (Join-Path $PSScriptRoot 'teleporter\generate_fx.py') --check
    if ($LASTEXITCODE -ne 0) { Die 'Teleporter FX sources differ from the reviewed generator.' }
    & node (Join-Path $PSScriptRoot 'test_teleporter_fx.js')
    if ($LASTEXITCODE -ne 0) { Die 'Teleporter FX host lifecycle check failed.' }
    & node (Join-Path $PSScriptRoot 'verify_weapon_costs.js')
    if ($LASTEXITCODE -ne 0) { Die 'Weapon-cost table budget failed; client startup would be at risk.' }
    # 2026-10-04 (-5e, docs/208): gdtdb /update exits 1 on a // line ANYWHERE in a GDT and on one asset
    # (name + type) defined twice; no other gate runs gdtdb, so check every repo GDT before the sync.
    & node (Join-Path $PSScriptRoot 'lint_tod_gdt.js')
    if ($LASTEXITCODE -ne 0) { Die 'A repo GDT would fail gdtdb /update (a // comment, a stray token, a missing brace or one asset defined twice). Fix the generator that wrote it.' }
}
if (-not $SkipSync) {
    Step "sync repo -> Mod Tools"
    if ($DryRun) {
        & (Join-Path $PSScriptRoot 'sync_to_modtools.ps1') -ModToolsRoot $Tools -DryRun
    } else {
        & (Join-Path $PSScriptRoot 'sync_to_modtools.ps1') -ModToolsRoot $Tools
        if ((Test-Path $RepoMap) -and (Test-Path $MapSrc)) {
            $rh = (Get-FileHash $RepoMap).Hash
            $dh = (Get-FileHash $MapSrc).Hash
            if ($rh -eq $dh) { Info "deployed .map hash matches repo (sync OK)" }
            else { Die "deployed map_source .map does NOT match repo after sync - aborting before a stale build" }
        }
    }
} else {
    Warn "-SkipSync: building whatever is already deployed"
}

# Re-copying an old source must not silently undo the reviewed size pass.
$sizeState = Join-Path $Tools '_tod_size_originals\20260910\state.json'
if (-not $DryRun -and (Test-Path $sizeState)) {
    $sizeApplied = (Get-Content -LiteralPath $sizeState -Raw | ConvertFrom-Json).applied
    if ($sizeApplied) {
        Step 'optimized asset source verification'
        & python (Join-Path $PSScriptRoot 'optimize_tod_assets.py') --root $Tools --verify
        if ($LASTEXITCODE -ne 0) { Die 'Optimized asset sources changed or were overwritten by sync. Review the size manifest before rebuilding.' }
    }
}

# ===========================================================================
# 1b. gdtdb /update - refresh the asset DB when the repo ships GDTs. The
#     linker does NOT do this itself; a stale DB errors "unable to locate
#     asset in gdtdb for '<asset>'" (map 1's deploy_perk_shaders lesson).
# ===========================================================================
if (-not $DryRun -and (Test-Path (Join-Path $RepoRoot 'source_data'))) {
    Step "gdtdb /update (repo GDTs present)"
    $GdtDb = Join-Path $Tools 'gdtdb\gdtdb.exe'
    if (Test-Path $GdtDb) {
        $r = Invoke-BuildExe $GdtDb @('/update') 'gdtdb' (Join-Path $Tools 'gdtdb')
        if ($r.Code -ne 0) {
            Write-Host $r.Out
            Write-Host $r.Err
            Die "gdtdb /update exited $($r.Code) - private database refresh failed"
        }
        else { Info "asset DB refreshed" }
        & python (Join-Path $PSScriptRoot 'verify_tod2_database.py')
        if ($LASTEXITCODE -ne 0) { Die 'TOD II asset database contains foreign source paths or missing map models.' }
    } else {
        Warn "gdtdb.exe not found at $GdtDb - skipping DB refresh"
    }
}

# ===========================================================================
# 2. cod2map64 - BSP + navmesh (FULL builds only). MUST run with cwd = bin or
#    navmesh gen aborts while still writing the .d3dbsp (silent stale navmesh).
# ===========================================================================
# ===========================================================================
# 1a. WEAPON / PACK-A-PUNCH GATE - runs on EVERY build, GscOnly included.
#
# WHY THIS IS HERE (2026-08-25, user: "Why do we continuously keep breaking the
# game? ... It specifically happens with pap where we make a change and somehow
# guns cant be papped anymore. It seems random too").
#
# It kept happening because these two lints EXISTED and the build never ran
# them. Only the geometry lint was wired in, so every PaP regression shipped
# unless a human remembered to run `node tools/lint_tod_weapons.js` by hand -
# and the failure mode is silent in the build, silent in the linker, and only
# shows up at the PaP machine in game. That is not a run-of-bad-luck, it is a
# missing gate, and this is the gate.
#
# Both are fast (~1s) and both are HARD failures. Neither is optional on
# -GscOnly: a weapons CSV or _tod_classes.gsc edit is exactly the kind of change
# that takes the fast path.
# ===========================================================================
Step "weapon / Pack-a-Punch lint"
if (-not $DryRun) {
    $wOut = & node (Join-Path $PSScriptRoot 'lint_tod_weapons.js') 2>&1 | Out-String
    Write-Host $wOut
    if ($LASTEXITCODE -ne 0) {
        Die "weapon/PaP lint FAILED - a gun would be unpackapunchable in game. Fix the generator or the CSV; do NOT build past this."
    }
}

# THE PERK MACHINES (docs/208, map 1's v19.32 + v19.45 + v19.48b): Double Tap's cowboy fires his sixteen
# authored shots at the zombies in front of the machine (scheduled on the clip's frames, aimed, credited to the
# buyer), the fourteen recovered WAVs, Wisp Tea's activation audio and the cue cleanup on interruption. The state
# machine runs through the real GSC; the clips, notes, aliases, zone lines and sync rows are pinned.
Step "perk machine purchase / shot / asset validation"
if (-not $DryRun) {
    & node (Join-Path $PSScriptRoot "test_perk_anims.js")
    if ($LASTEXITCODE -ne 0) { Die "Perk machine state/shot validation failed." }
    & python -B (Join-Path $PSScriptRoot "verify_perk_machine_presentation.py")
    if ($LASTEXITCODE -ne 0) { Die "Perk machine animation/FX/audio validation failed." }
}

# Exact BO6 machine: frozen native source/audio, every-floor geometry and per-player transactions.
# Legacy individual-machine assets remain frozen; their old runtime initializers are retired.
Step "BO6 Wunderfizz source / purchase / placement validation"
if (-not $DryRun) {
    & python -B (Join-Path $PSScriptRoot 'wunderfizz/verify_source_assets.py')
    if ($LASTEXITCODE -ne 0) { Die "BO6 Wunderfizz original source, material/image or collision integrity failed." }
    & python -B (Join-Path $PSScriptRoot 'wunderfizz/verify_audio.py')
    if ($LASTEXITCODE -ne 0) { Die "BO6 Wunderfizz original PCM/native alias integrity failed." }
    & node (Join-Path $PSScriptRoot 'wunderfizz/test_runtime.js')
    if ($LASTEXITCODE -ne 0) { Die "Wunderfizz per-player price, transaction or refund validation failed." }
    & node (Join-Path $PSScriptRoot 'wunderfizz/test_machine.js')
    if ($LASTEXITCODE -ne 0) { Die "Wunderfizz native machine power, animation or sound lifecycle failed." }
    & node (Join-Path $PSScriptRoot 'wunderfizz/test_layout.js')
    if ($LASTEXITCODE -ne 0) { Die "Wunderfizz fifty-floor coverage, route or native collision clearance failed." }
    & node (Join-Path $PSScriptRoot 'wunderfizz/native_navcheck.js')
    if ($LASTEXITCODE -ne 0) { Die "Wunderfizz native navigation checker controls failed." }
}

Step "GSC arity / resolution lint"
if (-not $DryRun) {
    # GSC STRICT LINT (2026-10-03, the war damage pass, build 6): the BO3 compiler's strict-syntax rules - an unwrapped
    # ternary, ( expr ).field, a late #using, a keyword-less function, a never-assigned local, unbalanced brackets -
    # checked FIRST, because the linker compiles scripts only at the very end of a build and stops at the first
    # failure with "No generated data" (build 6 baked 20 minutes, then died on one ternary). Self-tests every run.
    & node (Join-Path $PSScriptRoot "lint_tod_gsc_strict.js")
    if ($LASTEXITCODE -ne 0) { Die "GSC strict lint FAILED - the linker would refuse this script after the whole build. See tools/lint_tod_gsc_strict.js." }
    & python (Join-Path $PSScriptRoot "verify_cyber_reference_sources.py")
    if ($LASTEXITCODE -ne 0) { Die "Cyber equipment masters and baked textures do not match." }
    & python (Join-Path $PSScriptRoot "test_cyber_equipment_layout.py")
    if ($LASTEXITCODE -ne 0) { Die "Cyber equipment limb separation failed." }
    & python (Join-Path $PSScriptRoot "verify_cyber_zombie.py")
    if ($LASTEXITCODE -ne 0) { Die "Cyber zombie model structure failed." }
    & python (Join-Path $PSScriptRoot "verify_cyber_roster.py")
    if ($LASTEXITCODE -ne 0) { Die "Cyber roster model structure failed." }
    & python (Join-Path $PSScriptRoot "heavenly_altar/verify_native.py")
    if ($LASTEXITCODE -ne 0) { Die "Heavenly Altar model or shared placement validation failed." }
    & python (Join-Path $PSScriptRoot "teleporter/verify_native.py")
    if ($LASTEXITCODE -ne 0) { Die "Teleporter model or shared placement validation failed." }
    & python (Join-Path $PSScriptRoot "art_cohesion/verify_surfaces.py")
    if ($LASTEXITCODE -ne 0) { Die "Cybercity shared material bake or native bindings failed." }
    & node (Join-Path $PSScriptRoot "art_cohesion/verify_geometry.js")
    if ($LASTEXITCODE -ne 0) { Die "Crown material bay changed the original floor/wall solid volume." }
    & node (Join-Path $PSScriptRoot "art_cohesion/verify_crown.js")
    if ($LASTEXITCODE -ne 0) { Die "Crown material coverage is incomplete or its architecture changed shape." }
    & python (Join-Path $PSScriptRoot "partner_shop/verify_native.py")
    if ($LASTEXITCODE -ne 0) { Die "Item shop native model validation failed." }
    & node (Join-Path $PSScriptRoot "partner_shop/test_shop.js")
    if ($LASTEXITCODE -ne 0) { Die "Item shop power, animation or placement contract failed." }
    & node (Join-Path $PSScriptRoot "partner_shop/test_spin.js")
    if ($LASTEXITCODE -ne 0) { Die "Item shop BLACK MARKET SPIN contract failed (odds, items, reel lockstep, untargetable lock; docs/188)." }
    & python -B (Join-Path $PSScriptRoot "black_market_vo/pick.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Black Market dealer's voice is stale (a wav, alias row or the generated length table drifted) - run: python tools/black_market_vo/pick.py (docs/198)." }
    & python -B (Join-Path $PSScriptRoot "near_miss/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The near-miss / hot-streak sounds are stale or missing (a wav, an alias row or the zone config) - run: python tools/near_miss/make_sounds.py (docs/201)." }
    & node (Join-Path $PSScriptRoot "test_hot_streak.js")
    if ($LASTEXITCODE -ne 0) { Die "THE HOT STREAK / THE REACH contract failed (streak rules, the heat table in three places, heat-blind guarantees, reach odds + beats; docs/201)." }
    & node (Join-Path $PSScriptRoot "test_ability_fx.js")
    if ($LASTEXITCODE -ne 0) { Die "THE ABILITY FEEDBACK / THE KILL FEEL gate failed (generated effects stale, server/client lockstep, wiring, strings, aliases, art, kill-feel logic; docs/203 + docs/206) - see test_ability_fx.js output." }
    & python -B (Join-Path $PSScriptRoot "ability_fx/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The ability sounds are stale or missing (a wav, its sha, an alias row or the zone config) - run: python tools/ability_fx/make_sounds.py pick (docs/206)." }
    # W2C (2026-10-05): tier sting, near-miss set, companion loops, world ambience, power, Necromancer foley, bolt impacts.
    & python -B (Join-Path $PSScriptRoot "sfx/w2c_sounds/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The wave-2 sounds are stale or unwired (tier sting, near-miss set, companions, world ambience, power, Necromancer foley, bolt impacts: a wav sha, an alias table, a GDT block, the zone config, the generated ambience anchors / bolt effects, or the script that plays one) - run: python tools/sfx/w2c_sounds/make_sounds.py pick." }
    & node (Join-Path $PSScriptRoot "sfx/w2c_sounds/test_amb.js")
    if ($LASTEXITCODE -ne 0) { Die "THE WORLD AMBIENCE contract failed (_tod_amb.csc: the room kinds, the wind / far-city levels by height, the room-tone anchors' reach, the stoppable bed lanes) - see test_amb.js output; after a zone change run python tools/sfx/w2c_sounds/gen_amb_data.py." }
    & node (Join-Path $PSScriptRoot "test_cyber_zombie_spawns.js")
    if ($LASTEXITCODE -ne 0) { Die "Cyber zombie spawn selection failed." }
    & node (Join-Path $PSScriptRoot "test_cyber_elites.js")
    if ($LASTEXITCODE -ne 0) { Die "Normal-round elite director validation failed." }
    & python (Join-Path $PSScriptRoot "keeper/install_keeper.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Keeper boss assets are stale - re-run tools/keeper/install_keeper.py." }
    # (keeper/test_keeper.js retired 2026-10-05 with the Keeper boss: its whole subject - the boss wave, the soul
    # lines, his clientfields - is gone. install_keeper.py --check above stays: it pins the Keeper SOURCES the
    # Dealer's installer derives from. tools/test_retired_systems.js pins the retirement itself.)
    & python (Join-Path $PSScriptRoot "dealer_boss/install.py") --check
    if ($LASTEXITCODE -ne 0) { Die "THE DEALER boss assets are stale - re-run tools/dealer_boss/export_native.py + install.py (docs/199)." }
    & node (Join-Path $PSScriptRoot "dealer_boss/test_dealer.js")
    if ($LASTEXITCODE -ne 0) { Die "THE DEALER boss contract failed - see test_dealer.js output." }
    # W2B (2026-10-05): THE DEALER's own combat sounds + fight barks, the authored arena / house cues, his effects.
    & python -B (Join-Path $PSScriptRoot "dealer_sfx/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "THE DEALER's sounds are stale or missing (a wav, its sha, tod_dealer.csv or an authored arena / house cue) - run: python tools/dealer_sfx/make_sounds.py pick (docs/199 s5)." }
    & python -B (Join-Path $PSScriptRoot "dealer_sfx/wire_szc.py") --check
    if ($LASTEXITCODE -ne 0) { Die "tod_dealer.csv is not loaded by the sound zone config - run: python tools/dealer_sfx/wire_szc.py (docs/199 s5)." }
    & python -B (Join-Path $PSScriptRoot "dealer_fx/gen_fx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "THE DEALER's effects are stale or invalid - run: python tools/dealer_fx/gen_fx.py (docs/199 s5)." }
    # Dealer weapon pass: lifecycle/footprint, native clips and authored sound/FX pins.
    & node (Join-Path $PSScriptRoot "dealer_combat/test_combat.js")
    if ($LASTEXITCODE -ne 0) { Die "Dealer weapon lifecycle / fairness contract failed." }
    & python -B (Join-Path $PSScriptRoot "dealer_combat/check_assets.py")
    if ($LASTEXITCODE -ne 0) { Die "Dealer gun animation sources or native registration are stale." }
    & python -B (Join-Path $PSScriptRoot "dealer_combat/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Dealer weapon sound cues are stale or invalid." }
    & python -B (Join-Path $PSScriptRoot "dealer_combat/gen_fx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Dealer weapon effects are stale or invalid." }
    # THE RETIREMENT PIN (W2E, 2026-10-05): every parked / switched-off Map One system (the Panzer, the Rogue
    # Protector boss, the Apothicon Fury, the hellhound director, the armored sprinter, the Keeper boss, the crown
    # finale, the eight parked cards) stays retired whole - no module, zone line, alias row, image, GDT block or
    # call comes back half-way. Negative controls inside.
    & node (Join-Path $PSScriptRoot "test_retired_systems.js")
    if ($LASTEXITCODE -ne 0) { Die "A retired Map One system came back (or half came back) - see test_retired_systems.js output. Retire it whole or restore it whole." }
    & node (Join-Path $PSScriptRoot "crown_alarm/test_alarm.js")
    if ($LASTEXITCODE -ne 0) { Die "Crown alarm mounts or lifecycle validation failed." }
    # THE SKY FLEET (docs/192). The lane check re-tests the COMMITTED lanes against the LIVE map, so it only
    # fails when a ship would really fly into geometry (an unrelated map edit only prints a regenerate note).
    & node (Join-Path $PSScriptRoot "sky_ships/gen_lanes.js") --check
    if ($LASTEXITCODE -ne 0) { Die "Sky fleet lane is blocked by the live map - run: node tools/sky_ships/gen_lanes.js (docs/192)." }
    & python -B (Join-Path $PSScriptRoot "sky_ships/gen_fx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Sky fleet effects are stale - run: python tools/sky_ships/gen_fx.py (docs/192)." }
    & python -B (Join-Path $PSScriptRoot "sky_ships/make_textures.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Sky fleet textures are stale - run: python tools/sky_ships/make_textures.py (docs/192)." }
    & python -B (Join-Path $PSScriptRoot "sky_ships/verify_native.py")
    if ($LASTEXITCODE -ne 0) { Die "Sky fleet models / GDT validation failed (docs/192)." }
    # v2: whole flights through the SHIPPING director (tools/sky_ships/gsc_eval.js): every drawn ship inside the box,
    # on the camera ray, clear of every real solid, smooth; appears / vanishes small; the first-jump salute in frame.
    & node (Join-Path $PSScriptRoot "sky_ships/test_sky_ships.js")
    if ($LASTEXITCODE -ne 0) { Die "Sky fleet flight / lockstep / lifecycle contract failed (docs/192)." }
    & python -B (Join-Path $PSScriptRoot "necro_staff/verify.py")
    if ($LASTEXITCODE -ne 0) { Die "Necromancer staff models, grip, animation or tier binding failed." }
    & node (Join-Path $PSScriptRoot "necro_staff/test_runtime.js")
    if ($LASTEXITCODE -ne 0) { Die "Necromancer staff casting or pulse lifecycle failed." }
    & node (Join-Path $PSScriptRoot "necromancer/test_visibility.js")
    if ($LASTEXITCODE -ne 0) { Die "Necromancer held summon or pulse visibility validation failed." }
    & node (Join-Path $PSScriptRoot "necromancer/test_bind_guard.js")
    if ($LASTEXITCODE -ne 0) { Die "Necromancer bind shield (a bound zombie is the binder's) failed - see test_bind_guard.js." }
    & node (Join-Path $PSScriptRoot "test_fall_seal_cue.js")
    if ($LASTEXITCODE -ne 0) { Die "The crown seal cue is out of earshot again - see test_fall_seal_cue.js." }
    & node (Join-Path $PSScriptRoot "cyber_sword/test_state.js")
    if ($LASTEXITCODE -ne 0) { Die "Cyber Sword state / client cleanup failed - see cyber_sword/test_state.js." }
    & node (Join-Path $PSScriptRoot "breacher/test_c4_consistency.js")
    if ($LASTEXITCODE -ne 0) { Die "C4 effect selection or playback diagnostics validation failed." }
    & node (Join-Path $PSScriptRoot "breacher/test_fusion_air.js")
    if ($LASTEXITCODE -ne 0) { Die "Breacher Fusion launch (jump-only, the burst push) or air steering validation failed." }
    & node (Join-Path $PSScriptRoot "warrior/test_bash.js")
    if ($LASTEXITCODE -ne 0) { Die "Warrior Bash or corpse callback-order validation failed." }
    & node (Join-Path $PSScriptRoot "warrior/test_gs_dive.js")
    if ($LASTEXITCODE -ne 0) { Die "Warrior Cyber Smash air slam (dive to the floor) validation failed." }
    & python -B (Join-Path $PSScriptRoot "warrior/verify_hook.py")
    if ($LASTEXITCODE -ne 0) { Die "Warrior left-hook motion or punch animation binding failed." }
    & python -B (Join-Path $PSScriptRoot "archer_assets/verify_fire_bow.py")
    if ($LASTEXITCODE -ne 0) { Die "Fire Bow original material, texture or model validation failed." }
    & python (Join-Path $PSScriptRoot "crown_alarm/verify_native.py")
    if ($LASTEXITCODE -ne 0) { Die "Crown alarm model/material validation failed." }
    & python (Join-Path $PSScriptRoot "cyber_elites/verify_assets.py")
    if ($LASTEXITCODE -ne 0) { Die "Charcoal / robotic Doppelgast / default Mangler assets failed." }
}
if (-not $DryRun) {
    & node (Join-Path $PSScriptRoot "test_starter_weapons.js")
    if ($LASTEXITCODE -ne 0) { Die "Starter weapon validation failed." }
    & python (Join-Path $PSScriptRoot "test_expected_roster.py")
    if ($LASTEXITCODE -ne 0) { Die "Expected roster / native audio validation failed." }
    # docs/157: the Breacher's private Apex quality models/materials must match
    # what the installer would write (a stale GDT = the old weak-texture setup).
    & python (Join-Path $PSScriptRoot "install_breacher_apex.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Breacher Apex quality GDT is stale - run python tools/install_breacher_apex.py." }
    & python (Join-Path $PSScriptRoot "partner/verify_assets.py")
    if ($LASTEXITCODE -ne 0) { Die "Partner model source validation failed." }
    # W2A (2026-10-05): the companions' authored maps (Protector gold, Talon / Cerberus / R.A.P.S. gaps) are generated.
    & python (Join-Path $PSScriptRoot "companion_maps/compose.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Companion authored maps are stale or unwired - run python tools/companion_maps/compose.py, then python tools/partner/install_assets.py (W2A)." }
    & node (Join-Path $PSScriptRoot "partner/test_partners.js")
    if ($LASTEXITCODE -ne 0) { Die "Partner build/equip state tests failed." }
    # THE CLASS TERMINAL (2026-10-01): the crown's tester class switch - who may open it, where it
    # stands (clear of every crown trigger, riser and pier), the sleeping-card rule, the takeover,
    # the wiring - the shipping functions run through the GSC interpreter, with negative controls.
    & node (Join-Path $PSScriptRoot "test_class_terminal.js")
    if ($LASTEXITCODE -ne 0) { Die "Class terminal gate failed (refusals / placement / sleeping cards / takeover / wiring) - see test_class_terminal.js output." }
    # docs/160 §9: the Doppelghast's aitype/model/clips live at the tools root
    # (Hellbound's GDTs), its AI tables + audio table in this repo — prove all
    # of it before the linker links a spawner that is not there.
    & node (Join-Path $PSScriptRoot "test_doppelghast.js")
    if ($LASTEXITCODE -ne 0) { Die "Doppelghast preflight failed (tools-root GDTs / AI tables / zone / audio)." }
    & node (Join-Path $PSScriptRoot "test_broken_tower.js")
    if ($LASTEXITCODE -ne 0) { Die "Broken tower drop geometry / zone activation / landing protection failed." }
    & node (Join-Path $PSScriptRoot "test_tower_transit.js")
    if ($LASTEXITCODE -ne 0) { Die "Top transit bay routes / arrivals / crown return failed." }
    # THE PURSUIT (docs/200, 2026-10-02): the walk model (all 24 real drops, doors, regions) run through the
    # GSC interpreter, the spawn filter, reachable targeting, THE HUNT's lanes/destinations, THE RECALL's
    # verdict, lockstep with gen_tower_map.js, the wiring, and 8 mutants that must each be caught.
    & node (Join-Path $PSScriptRoot "test_pursuit.js")
    if ($LASTEXITCODE -ne 0) { Die "Pursuit gate failed (walk model / spawn filter / targeting / hunt / recall / wiring) - see test_pursuit.js output." }
    # THE AMBUSH + THE TRICKLE (docs/204, 2026-10-03): the spawn director's shipping GSC run through the
    # interpreter (share, direction, legality on the real generated data, the pick end to end), the
    # pacing against map 1's, lockstep with THE HUNT, the wiring, and mutants that must each be caught.
    & node (Join-Path $PSScriptRoot "test_ambush.js")
    if ($LASTEXITCODE -ne 0) { Die "Ambush gate failed (spawn share / direction / legality / pacing / wiring) - see test_ambush.js output." }
    # THE RAMP (2026-10-04, the first real playthrough: "Game should ramp up"): the zombies-at-once cap grows
    # from a third of the party cap on round 1 to all of it on round 30 (rampage 15), the trickle eases from
    # x1.6 to x1.0 on the same rounds; the shipping GSC evaluated for every party size, round and breaker state.
    & node (Join-Path $PSScriptRoot "test_spawn_ramp.js")
    if ($LASTEXITCODE -ne 0) { Die "Spawn ramp gate failed (the cap / trickle ramp, its one writer, its lockstep) - see test_spawn_ramp.js output." }
    # THE BATTLE ARENA v2 (docs/185, 2026-10-03): the jump TIMED from the script (use -> jump = the transit
    # pads' 0.8 s; the v1 fixture must time out at the 6.6 s the user's log measured), the spawn director's
    # shipping GSC on the generated room, the waves, the fall guard, the room data, and mutants that must be caught.
    & node (Join-Path $PSScriptRoot "test_battle_arena.js")
    if ($LASTEXITCODE -ne 0) { Die "Battle Arena gate failed (jump timing / director / waves / room) - see test_battle_arena.js output." }
    # THE BATTLE ARENA v2.1 cues (docs/185 v2.1): the wave horn, the clear sting, the level fanfare and the gate cue
    # are GENERATED (tools/battle_arena/make_sounds.py); a stale wav / alias row / zone-config entry fails here.
    & python -B (Join-Path $PSScriptRoot "battle_arena/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Battle Arena cues are stale or missing (a wav, an alias row or the zone config) - run: python tools/battle_arena/make_sounds.py (docs/185 v2.1)." }
    # THE BATTLE ARENA v2.2 (docs/185 v2.2): the round badge's ARENA twin (BATTLE ARENA in the pill, a LEVEL caption in
    # the window) is GENERATED from the shipped round badge (tools/battle_arena/make_badge.py); a stale PNG, a missing
    # GDT block, zone line or Lua registration fails here.
    & python -B (Join-Path $PSScriptRoot "battle_arena/make_badge.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Battle Arena badge is stale or unwired - run: python tools/battle_arena/make_badge.py (docs/185 v2.2)." }
    # THE DEALER'S HOUSE (docs/207): the GENERATED reel art (the cursed tile / banner / mask icon), the GENERATED house
    # cues, and the house gate (the two rooms, the flow, the reel protocol, the HUD flags - all LOCKSTEP).
    & python -B (Join-Path $PSScriptRoot "dealer_house/make_spin_art.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The cursed spin art is stale or unwired - run: python tools/dealer_house/make_spin_art.py (docs/207)." }
    & python -B (Join-Path $PSScriptRoot "partner_shop/make_gift_art.py") --check
    if ($LASTEXITCODE -ne 0) { Die "THE DEALER'S GIFT spin art is stale or unwired - run: python tools/partner_shop/make_gift_art.py (docs/209)." }
    & python -B (Join-Path $PSScriptRoot "dealer_house/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Dealer's House cues are stale or missing - run: python tools/dealer_house/make_sounds.py (docs/207)." }
    # PK03 THE END-OF-RUN MUSIC (2026-10-04): the loss cue and the Dealer's victory cue are GENERATED
    # (tools/sfx/end_of_run_music/make_sounds.py); a stale wav, an alias row, the stock game_over hand-off or the
    # TOD_HOUSE_VICTORY_SECS lockstep fails here.
    & python -B (Join-Path $PSScriptRoot "sfx/end_of_run_music/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The end-of-run music is stale or unwired (a wav, its sha, an alias row, the game_over hand-off or TOD_HOUSE_VICTORY_SECS) - run: python tools/sfx/end_of_run_music/make_sounds.py pick." }
    # ASSET BATCH 1 (2026-10-04, self-serve art - tools/artgen/README.md): every generated image / effect is gated
    # byte-exact against its generator, with its wiring (GDT + zone + Lua/GSC).
    & python -B (Join-Path $PSScriptRoot "artgen/packs/pk01_card_text_rebake.py") --check
    if ($LASTEXITCODE -ne 0) { Die "PK01 tier-gate strips are stale or unwired - run: python tools/artgen/packs/pk01_card_text_rebake.py" }
    # W3F (wave 3, 2026-10-05): the tier floor-gate strips in the LUCK badge's grammar (pk01 owns the files).
    & python -B (Join-Path $PSScriptRoot "artgen/packs/w3f_library.py") --check
    if ($LASTEXITCODE -ne 0) { Die "W3F tier-gate strips are stale - run: python tools/artgen/packs/pk01_card_text_rebake.py --install" }
    & python -B (Join-Path $PSScriptRoot "artgen/packs/gun_bay_icons.py") --check
    if ($LASTEXITCODE -ne 0) { Die "PK06 gun-bay icons are stale or unwired - run: python tools/artgen/packs/gun_bay_icons.py" }
    # W2G PK08 THE COMPANION STATUS PLATE (2026-10-05): the plate + state-ring art are GENERATED; the widget is zoned (an unzoned pcall-require fails silently), built in tod_upgrade.lua's veiled HudOnly, and its CP layout is in step with the art.
    & python -B (Join-Path $PSScriptRoot "artgen/packs/w2g_companion_plate.py") --check
    if ($LASTEXITCODE -ne 0) { Die "PK08 companion status plate is stale or unwired (art bytes, GDT, zone image / rawfile lines, the HudOnly build or the CP layout) - run: python tools/artgen/packs/w2g_companion_plate.py --install" }
    & python -B (Join-Path $PSScriptRoot "artgen/packs/pk07_prompt_icons.py") --check
    if ($LASTEXITCODE -ne 0) { Die "PK07 prompt icons are stale or unwired - run: python tools/artgen/packs/pk07_prompt_icons.py" }
    & python -B (Join-Path $PSScriptRoot "artgen/packs/pk09_loss_banner.py") --check
    if ($LASTEXITCODE -ne 0) { Die "PK09 GAME OVER banner is stale or unwired - run: python tools/artgen/packs/pk09_loss_banner.py" }
    # R2 CARD SUBJECTS (tmp/redesign/R2-card-subjects): the Breacher tier-3 / Necromancer tier-2 and tier-3 card art,
    # drawn from the game's own models (the Peacekeeper, the Soul Staff, the Crown of the Damned).
    & python -B (Join-Path $PSScriptRoot "artgen/packs/r2_card_subjects.py") --check
    if ($LASTEXITCODE -ne 0) { Die "R2 card subjects are stale - run: python tools/artgen/packs/r2_card_subjects.py --install" }
    # R6 THE CLASS DRAFT CARDS (wave 3, 2026-10-05): all four cards one set - every word in the map's typeface, the four
    # art windows one recipe with the tier-1 weapon drawn from its game model (R2's render + stylize); the words and
    # banner accents are checked against tod_class_select.lua CLASSES. (PK01 / R2 no longer write these cards.)
    & python -B (Join-Path $PSScriptRoot "artgen/packs/r6_class_cards.py") --check
    if ($LASTEXITCODE -ne 0) { Die "R6 class draft cards are stale or unwired (a card's bytes, its GDT / zone / class-select registration, or a class name / weapon / role / accent in tod_class_select.lua that the cards no longer match) - run: python tools/artgen/packs/r6_class_cards.py --install" }
    # R5 (wave 3, lead, 2026-10-05): the eight card illustrations that still drew Map One's weapons (the gold
    # sword / glove, a wooden pump gun, a sci-fi crossbow) redrawn from the real models with R2's render + stylize.
    & python -B (Join-Path $PSScriptRoot "artgen/packs/r5_tier_subjects.py") --check
    if ($LASTEXITCODE -ne 0) { Die "R5 card subjects (tier + in-use cards drawn from the real weapons) are stale - run: python tools/artgen/packs/r5_tier_subjects.py --install" }
    # R1 (redesign wave 1): the five weapon icons drawn from the guns' own models (Mozambique, Peacekeeper, 870,
    # riot shield, crossbow) and the four companion portraits; R3: the synthwave pause / scoreboard / card chrome.
    & python -B (Join-Path $PSScriptRoot "artgen/packs/r1_gun_icons.py") --check
    if ($LASTEXITCODE -ne 0) { Die "R1 weapon icons are stale or unwired - run: python tools/artgen/packs/r1_gun_icons.py" }
    & python -B (Join-Path $PSScriptRoot "artgen/packs/r1_comp_portraits.py") --check
    if ($LASTEXITCODE -ne 0) { Die "R1 companion portraits are stale - run: python tools/artgen/packs/r1_comp_portraits.py" }
    # RT (2026-10-05, the red return): the UI art has ONE theme switch, tools/artgen/synthwave.py THEME ('fallen' = the
    # red Fallen UI, 'synthwave' = docs/184). R3 also pins the pause menu / scoreboard / THE PULL code tints (CODE_TINTS).
    & python -B (Join-Path $PSScriptRoot "artgen/packs/r3_synthwave_system.py") --check
    if ($LASTEXITCODE -ne 0) { Die "R3 pause / scoreboard / card-panel chrome is stale or unwired, or a menu tint is not the THEME's (tools/artgen/synthwave.py) - run: python tools/artgen/packs/r3_synthwave_system.py --install" }
    # W3E (wave 3, 2026-10-05): WEAPON not GUN, and the eleven wording rules of the wording pass.
    & python -B (Join-Path $PSScriptRoot "wording/wording_pass.py") --check
    if ($LASTEXITCODE -ne 0) { Die "W3E wording is stale (the banner, a reworded line, or a player-facing GUN) - run: python tools/wording/wording_pass.py --check and read it" }
    # R4: the rest of the chrome in the R3 design system - HUD V2 plates, prompt-card chassis + icons, luck badges,
    # the nine perk shields, the power-up tokens, the PaP badge, and the round number's tint (the THEME's accent).
    & python -B (Join-Path $PSScriptRoot "artgen/packs/r4_synthwave_hud.py") --check
    if ($LASTEXITCODE -ne 0) { Die "R4 HUD / prompt cards / luck badges / perks / power-ups are stale or unwired, or the round number / arena icon is not the THEME's accent (tools/artgen/synthwave.py) - run: python tools/artgen/packs/r4_synthwave_hud.py --install" }
    # W3C THE CLASS EMBLEM PACK (2026-10-05, docs/212): the four HUD medallions + the four deal-panel class plates,
    # one construction, the class accents read from tod_class_select.lua.
    & python -B (Join-Path $PSScriptRoot "artgen/packs/w3c_class_pack.py") --check
    if ($LASTEXITCODE -ne 0) { Die "W3C class emblems (HUD medallions / deal-panel class plates) are stale, unwired, or a class accent moved in tod_class_select.lua - run: python tools/artgen/packs/w3c_class_pack.py --install" }
    # R10 (wave 3, 2026-10-05, docs/217): the upgrade card chrome (body, frames, crests, back, pill) and the reel's
    # EPIC / LEGENDARY art in the synthwave library - rarity steps up with light, not ornament.
    & python -B (Join-Path $PSScriptRoot "artgen/packs/r10_card_chrome.py") --check
    if ($LASTEXITCODE -ne 0) { Die "R10 card chrome / reel rarity art is stale, unwired or moved - run: python tools/artgen/packs/r10_card_chrome.py --install (docs/217)" }
    # RT (2026-10-05, docs/218): the Black Market reel's chrome by THEME (re-lit from its parked delivery, docs/218_ref)
    # and TodSpinReel.lua's theme tints (P3.THEME + EMPTY_RIM).
    & python -B (Join-Path $PSScriptRoot "artgen/packs/bm_chrome.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Black Market chrome is stale, or TodSpinReel.lua's reel tints are not the THEME's (tools/artgen/synthwave.py) - run: python tools/artgen/packs/bm_chrome.py --install" }
    & python -B (Join-Path $PSScriptRoot "fxgen/horde_eyes/make_fx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "PK04 horde eye-glow effects are stale - run: python tools/fxgen/horde_eyes/make_fx.py" }
    & node (Join-Path $PSScriptRoot "fxgen/horde_eyes/test_eye_glow.js")
    if ($LASTEXITCODE -ne 0) { Die "PK04 horde eye-glow wiring failed (tools/fxgen/horde_eyes/test_eye_glow.js)." }
    # PK26 THE ELITES' EFFECTS (2026-10-05): the Doppelghast's death charge / blast (its hurt zone drawn on the floor),
    # juke smear and claw glow, the Mangler's death break-up, the charge whine + the restored BO6 Mangler death wavs.
    & python -B (Join-Path $PSScriptRoot "fxgen/elites/make_fx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "PK26 elite effects are stale or invalid - run: python tools/fxgen/elites/make_fx.py" }
    & python -B (Join-Path $PSScriptRoot "fxgen/elites/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "PK26 elite sounds are stale - run: python tools/fxgen/elites/make_sounds.py pick" }
    & node (Join-Path $PSScriptRoot "fxgen/elites/test_elite_fx.js")
    if ($LASTEXITCODE -ne 0) { Die "PK26 elite effects wiring failed (tools/fxgen/elites/test_elite_fx.js)." }
    # THE WUNDERSTRAHL (docs/219, 2026-10-05): the laser power-up gun - the weapon file + zone, the model / clips, the
    # beam + effects + flame table, the sounds, the HUD icons, and the shared slot / damage / wiring contract.
    & python -B (Join-Path $PSScriptRoot "wunderstrahl/install.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl weapon file / zone package is stale or broken - run: python tools/wunderstrahl/install.py" }
    & python -B (Join-Path $PSScriptRoot "wunderstrahl/model/install_art.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl model / clip GDT is stale or a referenced file moved - see tools/wunderstrahl/model/install_art.py." }
    & python -B (Join-Path $PSScriptRoot "wunderstrahl/fx/make_fx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl beam / effects are stale or invalid - run: python tools/wunderstrahl/fx/make_fx.py" }
    & python -B (Join-Path $PSScriptRoot "wunderstrahl/fx/make_fx.py") --selftest
    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl effect validators missed a planted fault (tools/wunderstrahl/fx/make_fx.py --selftest)." }
    & python -B (Join-Path $PSScriptRoot "wunderstrahl/sound/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl sounds are stale - see tools/wunderstrahl/sound/make_sounds.py." }
    & python -B (Join-Path $PSScriptRoot "artgen/packs/ws_wunderstrahl_icons.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl HUD icons are stale or unwired - run: python tools/artgen/packs/ws_wunderstrahl_icons.py --install" }
    & node (Join-Path $PSScriptRoot "wunderstrahl/test_wunderstrahl.js")
    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl contract failed (shared slot / window / damage / lockstep / wiring) - see tools/wunderstrahl/test_wunderstrahl.js." }
    & python -B (Join-Path $PSScriptRoot "sfx/silent_sounds/check_wiring.py") --check
    if ($LASTEXITCODE -ne 0) { Die "PK02 a played sound alias is undefined or mis-wired (tools/sfx/silent_sounds/check_wiring.py)." }
    # W2F (2026-10-05): the original rips - the Mangler's voice, the Death Perception / PhD machine music.
    & python -B (Join-Path $PSScriptRoot "original_rips/make_original_rips.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The original rips (the Mangler's voice, the Death Perception / PhD machine music) are stale or unwired - see the FAIL lines; regenerate with python tools/original_rips/make_original_rips.py build (W2F)." }
    & node (Join-Path $PSScriptRoot "original_rips/test_original_rips.js")
    if ($LASTEXITCODE -ne 0) { Die "The Mangler's voice rules or the machine-music wiring failed (tools/original_rips/test_original_rips.js)." }
    & node (Join-Path $PSScriptRoot "test_dealer_house.js")
    if ($LASTEXITCODE -ne 0) { Die "THE DEALER'S HOUSE gate failed (rooms / flow / reel / HUD lockstep) - see test_dealer_house.js output (docs/207)." }
    # docs/174: ELITE HEALTH BARS - the 22 bar materials in lockstep across the
    # module #precache list, source_data/tod_hud_bars.gdt, the zone and the PNGs;
    # every stamped tod_boss_kind has a height row; one init thread in the entry.
    & node (Join-Path $PSScriptRoot "test_elite_hp.js")
    if ($LASTEXITCODE -ne 0) { Die "Elite health bar lockstep (precache / GDT / zone / PNGs / kinds) failed." }
    # docs/163: the JUMP PAD — generated anchors vs the .map structs, both ends
    # inside a live zone volume, the scripted arc swept clear of every brush,
    # and every guard the flight relies on (incl. _tod_fall's seal rules).
    & node (Join-Path $PSScriptRoot "test_archer_equipment.js")
    if ($LASTEXITCODE -ne 0) { Die "Archer equipment decisions/integration gate failed." }
    # docs/218: THE AUTOMATIC BOW (auto-release at full draw, QUICK DRAW x3 on 3^(Lv/9), flat arrows, the crossbow
    # repeater) + THE GRAPPLE'S INVISIBLE WALL - the shipping pure GSC run verbatim, every emitted Archer form vs the script.
    & node (Join-Path $PSScriptRoot "test_archer_autobow.js")
    if ($LASTEXITCODE -ne 0) { Die "Archer automatic bow / grapple wall gate failed (docs/218: weapon forms vs _tod_archer_bow, QUICK DRAW tables, Lua rows, the wall)." }
    & node (Join-Path $PSScriptRoot "test_tod_native_api.js")
    if ($LASTEXITCODE -ne 0) { Die "Engine API evidence gate failed (map-wide server/client availability or argument count)." }
    & node (Join-Path $PSScriptRoot "test_archer_art.js")
    if ($LASTEXITCODE -ne 0) { Die "Archer native art cleanup gate failed." }
    & node (Join-Path $PSScriptRoot "test_retriever_native.js")
    if ($LASTEXITCODE -ne 0) { Die "Retriever native behavior/integration gate failed." }
    # docs/163 s9: THE DE JUMP PAD's assets (Der Eisendrache's jumpsphere from the T7 pack): every installed file at its
    # recorded hash and the GDT self-consistent (each material the models name defined, each texture defined or stock).
    & python -B (Join-Path $PSScriptRoot "jumppad/install_de_jumppad.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The DE jump pad assets are stale or inconsistent - re-run: python tools/jumppad/install_de_jumppad.py (docs/163 s9)." }
    & node (Join-Path $PSScriptRoot "test_jumppad.js")
    if ($LASTEXITCODE -ne 0) { Die "Jump pad gate failed (anchors / zone volumes / arc clearance / guards) - see test_jumppad.js output." }
    # docs/208 - MAP 1'S MIGRATION. NIKOLAI'S PROPS (the Ammo Box V6, the TOWER OF DOOM CYBERCITY sign, the Grid
    # Terminal power switch + its dial / screens): every shipped file at map 1's built hash, every model zoned +
    # precached + synced.
    & python -B (Join-Path $PSScriptRoot "fan_props/verify.py")
    if ($LASTEXITCODE -ne 0) { Die "Nikolai's props are stale or unwired - see tools/fan_props/verify.py (docs/208)." }
    # THE FLOOR NUMBERS (docs/208): the digit atlas + its five district materials are the tool's output, and the ink
    # crops and district colours in gen_tower_map.js match it.
    & python -B (Join-Path $PSScriptRoot "floor_numbers/make_assets.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Floor-number art is stale or out of lockstep - re-run: python tools/floor_numbers/make_assets.py (docs/208)." }
    # THE CYBER TEDDY (docs/208): the song hunt's bear at map 1's hashes; its lift / standoff / extents one chain
    # (the GSC, tools/haven_layout.js, the generated haven anchors); the melee lane wired.
    & python -B (Join-Path $PSScriptRoot "cyber_teddy/verify.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Cyber Teddy is stale or out of lockstep - see tools/cyber_teddy/verify.py (docs/208)." }
    # THE CYBER RAMPAGE INDUCER (docs/208): model / clips / GDT / animtree at map 1's hashes, both clips seamless from
    # the bind pose, and the zone, the script, both generated trigger lifts and the body clip + cap in lockstep.
    & python -B (Join-Path $PSScriptRoot "inducer_cyber/verify.py")
    if ($LASTEXITCODE -ne 0) { Die "The cyber Rampage Inducer is stale or out of lockstep - see tools/inducer_cyber/verify.py (docs/208)." }
    # ITS STINGS (map 1's v19.68x): both wavs the tool's output, both aliases on their own wav, the switch plays both,
    # and no purchase cha-ching on the flip.
    & python -B (Join-Path $PSScriptRoot "rampage_sfx/build_rampage_sfx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The Rampage ON / OFF stings are stale or unwired - see tools/rampage_sfx/build_rampage_sfx.py (docs/208)." }
    # THE PACKED GUNS AIM DOWN DRAWN SIGHTS (docs/208, map 1's v19.22): no optic on a Breacher gun, and every packed
    # form's sight tags are its base form's (the packed 870 aimed onto hidden irons until this pass).
    & node (Join-Path $PSScriptRoot "test_no_optics.js")
    if ($LASTEXITCODE -ne 0) { Die "A weapon form aims down a hidden sight or carries an optic - see tools/test_no_optics.js (docs/208)." }
    # WIDOW'S WINE'S POWERED PANEL (docs/208, map 1's v19.43): its custom shader definition ships in both trees.
    foreach ($tsd in @('techsetdefs_stable', 'techsetdefs_stable_toolsgfx')) {
        $tsdFile = Join-Path $RepoRoot ("share\raw\{0}\geometry_advanced\lit_emissive_scroll_3layer_advanced_fullspec.techsetdef" -f $tsd)
        if (-not (Test-Path $tsdFile)) { Die "Widow's Wine's powered-panel shader definition is missing: $tsdFile (docs/208)." }
    }
    # THE FIRST JUMP'S CRASH (docs/196 s4): its effects and sounds are GENERATED; the scene (beats, framing,
    # sky clearance, wiring) is re-proved against the live scripts, map, fleet manifest and sky sign.
    & python -B (Join-Path $PSScriptRoot "jump_title/gen_fx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "First-jump crash effects are stale or invalid - run: python tools/jump_title/gen_fx.py (docs/196)." }
    & python -B (Join-Path $PSScriptRoot "jump_title/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "First-jump crash sounds are missing or the wrong shape - run: python tools/jump_title/make_sounds.py (docs/196)." }
    & python -B (Join-Path $PSScriptRoot "jump_title/make_sign_card.py") --check
    if ($LASTEXITCODE -ne 0) { Die "The first jump's LIT SIGN CARD is stale (model / texture / GDT / receipt) - run: python tools/jump_title/make_sign_card.py (docs/196 s6)." }
    & node (Join-Path $PSScriptRoot "jump_title/test_jump_title.js")
    if ($LASTEXITCODE -ne 0) { Die "First-jump crash scene contract failed (beats / framing / sky clearance / wiring) - see test_jump_title.js output (docs/196)." }
    # THE LUCKY SOURCES (docs/197): the Lucky Clover drop, the Lucky Meteor and the Golden Zombie. Their models,
    # effects and sounds are GENERATED (tools/lucky/*); the scripts' contracts (the user's numbers, the view-ray and
    # flight math run through gsc_eval, every lockstep, the negative controls) are re-proved on every build.
    & python -B (Join-Path $PSScriptRoot "lucky/verify_native.py")
    if ($LASTEXITCODE -ne 0) { Die "Lucky models failed validation - see tools/lucky/verify_native.py output (docs/197)." }
    & python -B (Join-Path $PSScriptRoot "lucky/make_golden.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Golden Zombie models are stale - run: python tools/lucky/make_golden.py (docs/197)." }
    & python -B (Join-Path $PSScriptRoot "lucky/make_fx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Lucky effects are stale or invalid - run: python tools/lucky/make_fx.py (docs/197)." }
    & python -B (Join-Path $PSScriptRoot "lucky/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Lucky sounds are stale - run: python tools/lucky/make_sounds.py (docs/197)." }
    & node (Join-Path $PSScriptRoot "lucky/test_lucky.js")
    if ($LASTEXITCODE -ne 0) { Die "Lucky sources contract failed - see tools/lucky/test_lucky.js output (docs/197)." }
    # THE HAVENS (docs/202): the safe zones. The dome model, its effects and sounds are GENERATED (tools/haven/*);
    # the gate runs the SHIPPING _tod_haven.gsc through gsc_eval (membership + hysteresis, the 33% damage cut and
    # its tell, the crossing flow, the 33% slow on and off), checks every lockstep and wiring, and 10 mutants.
    & python -B (Join-Path $PSScriptRoot "haven/make_dome.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Haven dome model / texture / GDT are stale - run: python tools/haven/make_dome.py (docs/202)." }
    & python -B (Join-Path $PSScriptRoot "haven/make_fx.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Haven effects are stale or invalid - run: python tools/haven/make_fx.py (docs/202)." }
    & python -B (Join-Path $PSScriptRoot "haven/make_sounds.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Haven sounds are stale - run: python tools/haven/make_sounds.py (docs/202)." }
    & node (Join-Path $PSScriptRoot "haven/test_haven.js")
    if ($LASTEXITCODE -ne 0) { Die "Haven (safe zone) contract failed - see tools/haven/test_haven.js output (docs/202)." }
    # BEGIN THE WAR DAMAGE PASS (docs/205): the merged models are fresh against their layout and kit, every effect is real (no stub,
    # no _pcloud), every decal is a plain decal never zoned bare, the zone / entries / sound config / sync are wired,
    # the client effect list is in lockstep with layout.js; phase 2: the torn conduits + conductor twins, the generated
    # effects + sounds are fresh, the power-wave + sign-bearing constants are in lockstep; negative controls
    # (tools/war_damage/test_war_damage.js).
    & node (Join-Path $PSScriptRoot "war_damage/test_war_damage.js")
    if ($LASTEXITCODE -ne 0) { Die "War damage contract failed - see tools/war_damage/test_war_damage.js output (docs/205)." }
    # END THE WAR DAMAGE PASS
    # BEGIN DEALER PRESENCE SOURCE GATE: reviewed native wall panels.
    & python -B (Join-Path $PSScriptRoot "dealer_presence/verify.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Dealer wall panels failed source/material/preview validation - see tools/dealer_presence/verify.py." }
    # END DEALER PRESENCE SOURCE GATE
}
if (-not $DryRun) {
    $aOut = & node (Join-Path $PSScriptRoot 'lint_tod_arity.js') 2>&1 | Out-String
    Write-Host $aOut
    if ($LASTEXITCODE -ne 0) {
        Die "GSC arity lint FAILED - a call does not match its function. Fix it before building."
    }
}

# ===========================================================================
# DAMAGE-CALLBACK GUARD (v18.59, 2026-09-09). Runs on EVERY build including
# -GscOnly: it reads one GSC file and nothing else.
#
# upgrade_damage_cb returns -1 to mean "I changed nothing", and stock then
# applies the RAW damage. So every multiplier applied above that guard must
# also be TESTED by it. Separate multipliers have been added above the guard
# and left out of the test before -- sprinter armour, the slasher sidearm lane
# (both v16.3) and script-paid PACK II/III (v18.59). Each one silently did
# nothing for exactly the players carrying no other upgrade, while the
# crosshair still showed the multiplied number.
#
# The test runs the SHIPPING condition text, not a copy, and carries a negative
# control that strips the terms back out and requires each case to regress.
# ===========================================================================
Step "damage-callback guard test"
if (-not $DryRun) {
    $dgOut = & node (Join-Path $PSScriptRoot 'test_upgrade_damage_guard.js') 2>&1 | Out-String
    Write-Host $dgOut
    if ($LASTEXITCODE -ne 0) {
        Die "damage-callback guard test FAILED - a multiplier applied in upgrade_damage_cb is not tested by its -1 fast path, so it is being discarded for players with no other upgrade. Fix the guard; do NOT build past this."
    }
}

Step "elite pause restore test"
if (-not $DryRun) {
    $epOut = & node (Join-Path $PSScriptRoot 'test_elite_pause_restore.js') 2>&1 | Out-String
    Write-Host $epOut
    if ($LASTEXITCODE -ne 0) {
        Die "elite pause restore FAILED - a short world pause can leave elites frozen. Fix the restore before building."
    }
}

Step "rampage lever + seal test"
if (-not $DryRun) {
    $rlOut = & node (Join-Path $PSScriptRoot 'test_rampage_levers.js') 2>&1 | Out-String
    Write-Host $rlOut
    if ($LASTEXITCODE -ne 0) {
        Die "rampage lever test FAILED - a lever lost its off-state identity, or the retired round-9 seal came back (v19.0: RAMPAGE toggles all match). Fix it before building."
    }
    # POWER SCALE (2026-09-25): map 1 at one tenth - the damage front door, the horde
    # curve, the elite / Panzer-part numbers, the marks and the crosshair encoding.
    $psOut = & node (Join-Path $PSScriptRoot 'test_power_scale.js') 2>&1 | Out-String
    Write-Host $psOut
    if ($LASTEXITCODE -ne 0) {
        Die "power scale test FAILED - map 1 / 10 drifted: a health base, the damage front door, an exempt mark or the crosshair encoding moved. Fix it before building."
    }
    # (test_king_rampage.js left with the Endless Spire and its Warden King, 2026-09-29.)
}

Step "riot shield card refill test"
# (test_panzer_flame_fx.js retired 2026-10-05 with the Panzer: its whole subject, the mechz flame visual state, is gone.)
if (-not $DryRun) {
    $rsOut = & node (Join-Path $PSScriptRoot 'test_riotshield_card_refill.js') 2>&1 | Out-String
    Write-Host $rsOut
    if ($LASTEXITCODE -ne 0) {
        Die "riot shield card test FAILED - a RIOT SHIELD card must END a recharge and hand the shield back (v18.99c), and a routine reconcile must NOT. Fix it before building."
    }
}

# =========================================================================
# LUA STRUCTURE LINT (2026-08-31). Runs on EVERY build, -GscOnly included:
# Lua rides in ui/ as zoned rawfiles, so it ships on the fast path too.
#
# WHY IT IS A GATE AND NOT AN ADVISORY: nothing else in this pipeline reads
# Lua before the linker packs it. tod_upgrade.lua alone draws the upgrade
# panel, the damage numbers, the tower gauge, the luck bar, the finale
# banner and the rampage seal - one dropped `end` takes all six off the
# screen at once, in game, with a completely green build behind it.
# It is a block/bracket balancer, not a parser - see the file header for
# exactly what it does and does not prove.
# =========================================================================
# =========================================================================
# ARMORY DRIFT CHECK (2026-09-01) — a WARNING, never a gate.
#
# docs/armory.html is the rebalance workbench the user actually designs from,
# and it is STATIC: every number is transcribed by hand, never read at view
# time. So it silently rots on every balance edit, and a wrong number there
# is a wrong INPUT TO A DESIGN DECISION rather than a cosmetic docs bug.
#
# WHY THIS IS WIRED IN AT ALL: both verifiers already existed and neither was
# ever run automatically. On 2026-09-01 the page drifted TWICE IN ONE SESSION
# from the same author — four domains retuned without the page moving, then a
# fifth reworked after the page had just been fixed. Relying on remembering
# is what failed; this is the durable version.
#
# WARNING, NOT A GATE, deliberately: a stale DOC must never block shipping a
# correct .ff. It prints and moves on. Die() here would be the tail wagging
# the dog.
#
#   verify_armory_constants.js — the tune: strings vs the #defines, PLUS (added
#                                2026-09-09) every TOD_* identifier the page
#                                names anywhere, including in prose, and every
#                                domain ladder's length. Four DELETED defines
#                                had accumulated in note: prose while this
#                                reported green, because unresolved names were
#                                printed as "check by hand" and still exited 0.
#   verify_armory_domains.js   — max / band / scope / class / guns / bonusMax
#                                per row, plus the hand-maintained header and
#                                tile counts, vs the shipping GSC
#   verify_armory_render.js    — the page actually DRAWS: syntax, boot under a
#                                fake DOM, every builder runs, and every tab's
#                                panel comes out non-empty. The page has more
#                                tabs than builder functions, so "every builder
#                                ran" was never the same claim.
# None can check PROSE. A sentence can become false with no number moving;
# that still needs a human pass.
# =========================================================================
Step "Armory drift check (advisory)"
if (-not $DryRun) {
    $armC = & node (Join-Path $PSScriptRoot 'verify_armory_constants.js') 2>&1 | Out-String
    $armCode = $LASTEXITCODE
    $armD = & node (Join-Path $PSScriptRoot 'verify_armory_domains.js') 2>&1 | Out-String
    $armDCode = $LASTEXITCODE
    $armR = & node (Join-Path $PSScriptRoot 'verify_armory_render.js') 2>&1 | Out-String
    $armRCode = $LASTEXITCODE
    if ($armCode -ne 0 -or $armDCode -ne 0 -or $armRCode -ne 0) {
        Write-Host $armC
        Write-Host $armD
        Write-Host $armR
        Write-Host "[build] WARN: docs/armory.html has drifted from the code (advisory - build continues)."
        Write-Host "[build]       The user balances off that page; refresh + republish it before it misleads a design call."
    } else {
        Write-Host "  armory: constants + domain fields match the shipping GSC, and every tab renders"
    }
}

Step "Lua structure lint (ui/**/*.lua)"
if (-not $DryRun) {
    $luaOut = & node (Join-Path $PSScriptRoot 'lint_tod_lua.js') 2>&1 | Out-String
    Write-Host $luaOut
    if ($LASTEXITCODE -ne 0) {
        Die "Lua structure lint FAILED - an unbalanced block, bracket or string in ui/. The menu would fail to load in game."
    }
}

# UI RUNTIME HARNESSES (2026-09-26, every build incl. -GscOnly). The user's pause-menu
# "UI Error 95573" was a Lua-only change: DataSources.X( controller ) called a datasource TABLE.
# These run the REAL menus under Lua 5.1 with an engine-shaped ListHelper, fire every button
# action, and carry negative controls (the build-15b settings call must still fail).
Step "UI runtime harnesses (pause menu + UI lifetimes, Lua 5.1)"
if (-not $DryRun) {
    $uiOut = & python -B (Join-Path $PSScriptRoot 'run_lua_harness.py') 'tools/test_pause_menu_runtime.lua' 'tools/test_ui_lifetimes.lua' 'tools/test_card_pull.lua' 'tools/test_spin_reel.lua' 'tools/test_jump_cine.lua' 'tools/test_class_terminal_ui.lua' 'tools/test_haven_hud.lua' 'tools/test_arena_hud.lua' 'tools/test_arena_badge.lua' 'tools/test_ability_feedback.lua' 'tools/test_health_tint.lua' 'tools/test_tier_gate_strip.lua' 'tools/test_companion_plate.lua' 'tools/test_round_counter_v2.lua' 'tools/test_keycap_resolve.lua' 'tools/test_toast.lua' 'tools/wunderfizz/test_ui.lua' 2>&1 | Out-String
    Write-Host $uiOut
    if ($LASTEXITCODE -ne 0) {
        Die "UI runtime harness FAILED - a pause-menu / HUD Lua path errors under the real call shapes. That is a UI Error box in game."
    }
}

# THE CARD ART LIST IS IN STEP (docs/187/190). tools/card_pull/install_card_art.py keeps the
# card-v2 / THE PULL images, their GDT blocks, the zone's GENERATED block and the Lua manifest
# TodCardArt.lua in step; --check fails if any of them drifted (a PNG dropped in without
# running the installer, a hand edit of the manifest). The Lua only draws what the manifest
# lists, so a stale manifest is a feature that silently falls back - worth a hard stop.
Step "card art manifest (card_pull --check)"
if (-not $DryRun) {
    $caOut = & python -B (Join-Path $PSScriptRoot 'card_pull\install_card_art.py') --check 2>&1 | Out-String
    Write-Host $caOut
    if ($LASTEXITCODE -ne 0) {
        Die "card art manifest is STALE - run: python tools/card_pull/install_card_art.py  (then rebuild)"
    }
}

# THE WHITE GLYPH ICONS ARE GENERATED (PK05, docs/184e): the 13 upgrade-row icons, the AI COMPANION well and
# the SOUL PULSE row redraw come from tools/artgen/packs/pk05_glyph_icons.py (its two HUD tile twins are
# w3b_ability_colour.py's, in colour). --check re-renders all 15 in memory and fails on any byte that
# differs from source_data/tod_ui_images/_images/ (a hand-edited or stale PNG). lint_tod_assets GATE A
# proves the names are zoned.
Step "white glyph icons (pk05 --check)"
if (-not $DryRun) {
    $g5Out = & python -B (Join-Path $PSScriptRoot 'artgen\packs\pk05_glyph_icons.py') --check 2>&1 | Out-String
    Write-Host $g5Out
    if ($LASTEXITCODE -ne 0) {
        Die "PK05 white glyph icons are STALE - run: python tools/artgen/packs/pk05_glyph_icons.py --install  (then a FULL build)"
    }
}

# THE ABILITY TILE GLYPHS ARE GENERATED IN COLOUR (W3B, 2026-10-05): the 12 i_tod_h2_ab_* glyphs AetheriumLoadout
# draws, from pinned white masters (art/synthwave_hud/ability_icons_white_src) + PK05's two Necromancer drawings,
# through R4's neon_glyph. --check also fails on PK05 claiming a tile, the retired V1 cloak key / SUMMON tile coming
# back (zone, GDT, _images, a Lua literal), a tint on the ability icon in AetheriumLoadout.lua (it would multiply the
# colour away), or a tod_class_select.lua class accent the tiles were not re-baked for.
Step "ability tile glyphs in colour (w3b --check)"
if (-not $DryRun) {
    $w3bOut = & python -B (Join-Path $PSScriptRoot 'artgen\packs\w3b_ability_colour.py') --check 2>&1 | Out-String
    Write-Host $w3bOut
    if ($LASTEXITCODE -ne 0) {
        Die "W3B ability tile glyphs are STALE or unwired - run: python -B tools/artgen/packs/w3b_ability_colour.py --install  (then a FULL build)"
    }
}

# THE TYPEFACE IS PINNED (the 2026-09-29 legibility revision, docs/172 top note; user: "I don't want ...
# in our future to go back to the old one"). tools/typeface/typeface.py --check fails when a font master
# changed without a deliberate re-pin (the retired face coming back), when the glyph metrics, the menus'
# TTF or the specimen were not rebuilt from the pinned masters, or when a live file names the retired
# archive folder (its name lives only in typeface.py, which is the one file allowed to say it).
Step "typeface pinned (typeface --check)"
if (-not $DryRun) {
    $tfOut = & python -B (Join-Path $PSScriptRoot 'typeface\typeface.py') --check 2>&1 | Out-String
    Write-Host $tfOut
    if ($LASTEXITCODE -ne 0) {
        Die "typeface check FAILED - a font master, a file built from it, or a reference to the retired face moved (tools/typeface/typeface.py)"
    }
}

# THE MENUS FIT (2026-09-28, user: "make sure pause and scoreboard menu descriptions up to date
# ... simple enough"; "Spend some time designing these menus correctly cause its how players get
# all their info"). Renders the real pause menu + scoreboard for every class with the shipped art and
# the map font, and fails on any text line wider than its box: the engine never wraps or shrinks a
# UIText, so an overflow here is text running off a row in game. PNGs land in tmp/ui_mockup/.
Step "menu text fits (pause menu + scoreboard, every class)"
if (-not $DryRun) {
    $mOut = & python -B (Join-Path $PSScriptRoot 'ui_mockup/render_menus.py') --check 2>&1 | Out-String
    Write-Host $mOut
    if ($LASTEXITCODE -ne 0) {
        Die "Menu text overflow - a pause-menu or scoreboard line is wider than its box (listed above; PNGs in tmp/ui_mockup/). Shorten the DETAIL / DOMAIN text."
    }
    # The published Armory page (docs/tod2_armory.html) must still RUN: one bracket slip in a data
    # row blanked the whole artifact on 2026-09-28 and no check covered this page.
    & node (Join-Path $PSScriptRoot 'verify_tod2_armory.js')
    if ($LASTEXITCODE -ne 0) { Die "docs/tod2_armory.html does not run (script error or an empty tab) - fix it before it is republished." }
}

# GENERATED FX ARE CURRENT (2026-09-26, every build). Each map-owned effect below is a
# scaled / trimmed copy of a stock donor written by its generator; a hand edit or a stale
# output ships silently otherwise (the Retriever's lava-skin spheres were a donor detail).
Step "generated fx current (retriever / soul pulse / breacher tiers / cluster glow)"
if (-not $DryRun) {
    $fxGens = @(
        @('python', '-B', (Join-Path $PSScriptRoot 'archer_assets\make_ret_fire_fx.py'), '--check'),
        @('python', '-B', (Join-Path $PSScriptRoot 'necromancer\make_soul_fx.py'), '--check'),
        @('node', (Join-Path $PSScriptRoot 'breacher\make_tier_fx.js'), '--check'),
        @('node', (Join-Path $PSScriptRoot 'breacher\make_cluster_glow.js'), '--check')
    )
    foreach ($g in $fxGens) {
        $gOut = & $g[0] $g[1..($g.Count - 1)] 2>&1 | Out-String
        Write-Host $gOut.Trim()
        if ($LASTEXITCODE -ne 0) { Die "generated fx STALE or hand-edited: $($g[-2]) - re-run that generator (never hand-edit its output)." }
    }
}

# SOUND-CONTEXT LINT (2026-09-09). Every build, -GscOnly included - alias csvs
# are bank inputs on every build. A row with a ContextType/ContextValue is
# SILENT in this map (nothing here ever sets a sound context); a class
# weapon's reload/first-raise foley shipped four builds that way. tools/lint_tod_sound_context.js
Step "sound-context lint (no context-gated alias rows)"
if (-not $DryRun) {
    $sndCtxOut = & node (Join-Path $PSScriptRoot 'lint_tod_sound_context.js') 2>&1 | Out-String
    Write-Host $sndCtxOut
    if ($LASTEXITCODE -ne 0) {
        Die "sound-context lint FAILED - an alias row is gated on a sound context this map never sets and would be silent. See the rows above."
    }
}

# =========================================================================
# CURSOR-HINT LINT (2026-08-31). Every build, -GscOnly included - a reworded
# hint IS a GSC-only change, and it is the change that skips every other gate.
#
# TWO THINGS, BOTH OF WHICH HAVE SHIPPED BROKEN:
#   * ROUTING. The Aetherium prompt kit picks which card to draw by
#     PATTERN-MATCHING THE HINT TEXT, so wording decides what the player
#     sees. Every priced non-door interactable in the map drew the WALL BUY
#     card - hardcoded description "Wall Weapon" - for months (found by the
#     user, 2026-08-31). The lint reads the router's own TOD_NOUNS table out
#     of the Lua, so GSC copy and the router cannot drift apart silently.
#   * THE TRIGGERSTRING 250 CAP. SetHintString mints one PERMANENT engine
#     slot per DISTINCT string, never freed, and overflow fatals blaming
#     whoever registers NEXT. This counts DISTINCT STRINGS - the only count
#     that proves anything (v14.3's "fix" proved its loop had run instead).
#
# tools/lint_tod_hints_selftest.js breaks the map seven ways and requires a
# catch on each plus a clean control - run it whenever this lint is edited.
# =========================================================================
Step "cursor-hint lint (prompt routing + the 250 triggerstring cap)"
if (-not $DryRun) {
    $hintOut = & node (Join-Path $PSScriptRoot 'lint_tod_hints.js') 2>&1 | Out-String
    Write-Host $hintOut
    if ($LASTEXITCODE -ne 0) {
        Die "cursor-hint lint FAILED - a prompt would draw the wrong card, or the distinct-string budget is blown. Neither shows up at build time in game; fix it here."
    }
}

# =========================================================================
# 1a-3. UI ART LINT - nothing missing, nothing dead. Runs on EVERY build
#     including -GscOnly, because both failure modes are pure zone/Lua edits.
#       * MISSING: the Lua names an image with no `image,` line. The linker
#         says nothing (Lua is an opaque rawfile) and the game draws a WHITE
#         SQUARE. Hard fail, no baseline.
#       * DEAD: the zone line outlives the thing that drew it. Cards are
#         `uncompressed` 768x1152, so one dead card is 3.4 MB of LOAD RAM -
#         four retired domains were quietly shipping 12 of them until v16.86
#         (40.5 MB). Gated on REGRESSION against
#         tools/lint_tod_assets.baseline.json, whose "why" block says which
#         of the current numbers are accepted and why.
#     THE RULE: a card slug and its zone lines are ONE unit - retire both or
#     neither. tools/lint_tod_assets_selftest.js breaks the map eight ways
#     (including two shapes that must NOT fire) - run it whenever the lint is
#     edited. It cannot see materials or GSC-only image references; see its
#     header for what a pass does and does not prove.
# =========================================================================
Step "UI art lint (missing art / dead art)"
if (-not $DryRun) {
    $artOut = & node (Join-Path $PSScriptRoot 'lint_tod_assets.js') 2>&1 | Out-String
    Write-Host $artOut
    if ($LASTEXITCODE -ne 0) {
        Die "UI art lint FAILED - either the Lua names an image the zone does not carry (white square in game, silent at build), or dead art regressed against the baseline. Fix the art; never raise the baseline to hide it."
    }
    # every fx path <= 63 chars (2026-09-26: a 64-char child effect is truncated at
    # runtime and access-violates the game the first time its parent plays)
    $fxOut = & node (Join-Path $PSScriptRoot 'lint_tod_fx_paths.js') 2>&1 | Out-String
    Write-Host $fxOut
    if ($LASTEXITCODE -ne 0) {
        Die "FX path lint FAILED - an effect path (zone line or a child inside an .efx) is over 63 characters; the engine truncates it and crashes. Shorten the name."
    }
}

# The two compile command lines are part of the geometry reuse key (geom_key.js),
# so they are defined once here for both the FULL and the -GscOnly branch.
$cod2Args = @('-platform', 'pc', '-navmesh', '-navvolume', '-loadFrom', (Q $MapSrc), (Q $Bsp))
$radArgs  = @('-ledSilent', '+medium', '+forceclean', '+recompute', (Q $MapSrc))
$GeomKey  = Join-Path $PSScriptRoot 'geom_key.js'
# (quotes stripped: Windows PowerShell 5.1 mangles embedded quotes in native args)
$geomCli  = @('--tools', $Tools, '--map', $MapName, '--args', ((($cod2Args -join ' ') + ' | ' + ($radArgs -join ' ')) -replace '"', ''))

if (-not $GscOnly) {
    # =======================================================================
    # 1b. GEOMETRY LINT - holes and misplaced walls, BEFORE 20 minutes of
    #     cod2map + bake are spent on a .map with a hole in it. Static
    #     worldspawn only; see the header of lint_tod_geometry.js for what it
    #     cannot see. Gates on REGRESSION against tools/lint_tod_geometry.baseline.json,
    #     which currently stands at zero of everything.
    # =======================================================================
    Step "geometry lint (holes / misplaced walls)"
    if (-not $DryRun) {
        $convexOut = & node (Join-Path $PSScriptRoot 'test_crown_convex.js') 2>&1 | Out-String
        Write-Host $convexOut
        if ($LASTEXITCODE -ne 0) { Die "crown convex geometry FAILED - emitted solids must be closed and collision sampling must agree with their planes." }
        $lintOut = & node (Join-Path $PSScriptRoot 'lint_tod_geometry.js') 2>&1 | Out-String
        Write-Host $lintOut
        if ($LASTEXITCODE -ne 0) {
            Die "geometry lint FAILED - the .map has a new hole, a new invisible wall, or the road is severed. Fix the generator, not the baseline."
        }
    }

    # (1c, the HALL BUNKER LINT for the spire's trial halls, left with the Endless Spire 2026-09-29.)

    # =======================================================================
    # 2-3. GEOMETRY + LIGHTING REUSE (2026-09-29, user: "Computer is freezing up
    #    while building"). The LED bake alone peaks at ~15.8 GB private memory on
    #    this 15.6 GB machine, so every full build paged the whole desktop out.
    #    Most full builds change no geometry at all (card art, weapons, sounds are
    #    "full builds" by the GDT rule). tools/geom_key.js hashes everything
    #    cod2map + the bake read - the .map, its prefabs, every GDT asset the map
    #    names followed through to its image/EXR files, the sky, the exes, the
    #    command lines - and the compiled outputs themselves. When all of it is
    #    byte-identical to the last full build, that build's BSP + navmesh + LED
    #    are linked as they stand: exactly the -GscOnly situation, proven here
    #    for months, but with the proof that nothing geometric changed.
    #    The record is cleared BEFORE any recompile and written only after cod2map
    #    AND a fresh bake both succeed, so a build that dies half-way can never
    #    leave a record pointing at mismatched files. -ForceBake / -Publish always
    #    compile + bake. `node tools/geom_key.js selftest` proves the key catches
    #    each kind of change (build-gated below).
    # =======================================================================
    $reuseGeom = $false
    $geomKeyOk = $false
    if (-not $DryRun) {
        Step "geometry + lighting reuse check (geom_key.js)"
        & node $GeomKey selftest | Out-Null
        if ($LASTEXITCODE -ne 0) { Die "geom_key.js selftest FAILED - the reuse check cannot be trusted; run: node tools/geom_key.js selftest" }
        & node $GeomKey check @geomCli --write-pending
        $gk = $LASTEXITCODE
        $geomKeyOk = ($gk -eq 0 -or $gk -eq 3)
        if ($gk -eq 0) {
            if ($ForceBake)   { Info "-ForceBake: compiling + baking anyway" }
            elseif ($Publish) { Info "-Publish: a publish always compiles + bakes fresh" }
            else              { $reuseGeom = $true }
        } elseif ($gk -ne 3) {
            Warn "geom_key.js check failed (exit $gk) - compiling + baking to be safe"
        }
    }

    if ($reuseGeom) {
        Step "cod2map64 + Radiant LED: SKIPPED (nothing they read has changed)"
        $ledFile = Join-Path $Tools ("share\raw\maps\zm\{0}.led" -f $MapName)
        Info ("reusing BSP {0:N1} MB @ {1}" -f ((Get-Item $Bsp).Length / 1MB), (Get-Item $Bsp).LastWriteTime)
        Info ("reusing LED {0:N0} bytes @ {1}" -f (Get-Item -LiteralPath $ledFile).Length, (Get-Item -LiteralPath $ledFile).LastWriteTime)
        # the reused mesh passed this gate when it was built; re-run it anyway so a gate
        # made stricter since then still judges the mesh this build ships (it is cheap)
        Step "navmesh connectivity gate (lint_tod_navmesh.js) - the reused mesh"
        if (Test-Path $NavHkt) {
            $navLint = & node (Join-Path $PSScriptRoot 'lint_tod_navmesh.js') $NavHkt 2>&1 | Out-String
            Write-Host $navLint
            if ($LASTEXITCODE -ne 0) {
                Die "navmesh gate FAILED on the reused mesh (see the SEAM / ISLAND rows above). Rebuild it: .\tools\build_map.ps1 -ForceBake"
            }
        } else { Die "the reused build has no navmesh at $NavHkt - run a full build with -ForceBake" }
    } else {
    if (-not $DryRun) { & node $GeomKey clear @geomCli }

    Step "cod2map64 (BSP + navmesh + navvolume)  [cwd = bin]"
    $bspDir = Split-Path $Bsp -Parent
    if (-not (Test-Path $bspDir) -and -not $DryRun) { New-Item -ItemType Directory -Path $bspDir -Force | Out-Null }

    $r = Invoke-BuildExe $Cod2 $cod2Args 'cod2map64' $Bin

    if (-not $DryRun) {
        # KEEP THE cod2map TRANSCRIPT (2026-09-03). Invoke-BuildExe captures
        # stdout/stderr to two temp files, reads them into $r.Out/$r.Err and
        # DELETES both in its finally block -- so on a SUCCESSFUL build the
        # entire cod2map output was thrown away and nothing reached disk. That
        # is why the tower's navmesh failure (zero seeds above the base arena,
        # everything past ~floor 17 compiled with no mesh) left no trace to
        # read afterwards: the diagnosis had to be rebuilt from the .map and
        # the Havok config instead of from the log that had already said it.
        # A build that only prints on FAILURE cannot explain a build that
        # SUCCEEDS and ships broken. *.log is gitignored.
        $c2log = Join-Path $PSScriptRoot 'cod2map_last.log'
        try {
            @($r.Out, $r.Err) | Set-Content $c2log -Encoding utf8 -ErrorAction Stop
            Info "cod2map transcript -> $c2log"
        } catch { Warn "could not write $c2log ($($_.Exception.Message))" }

        # NAVMESH DIAGNOSTICS. Havok AI keeps a navmesh region if it passes
        # EITHER of two independent tests -- area >= threshold, OR within
        # pruning.minDistanceToSeedPoints (14) of a seed point -- and when
        # every region fails BOTH it silently keeps only the largest and
        # discards the rest. Its own string says so verbatim: "All regions are
        # below the area threshold and too far from a seed point. Keeping the
        # largest region." That is how 50 floors of tower shipped with mesh on
        # the bottom ~17 and none above, on a build that reported success.
        #
        # 'Could not drop node' is the one to read after any seed change: it is
        # cod2map failing to anchor a seed onto walkable mesh AND NAMING THE
        # COORDINATE, so it validates each of the 149 tower seeds by position.
        # It turns "the mesh got bigger, probably good" into "here is the exact
        # seed that is not anchored". Full builds only -- -GscOnly never runs
        # cod2map, so an empty log there means nothing ran, not nothing wrong.
        $navWarn = @($r.Out, $r.Err) -split "`r?`n" | Where-Object { $_ -match 'Keeping the largest region|below the area threshold|too far from a seed|Could not drop node|too many edges or faces|ran out of memory|No regions found|Empty nav mesh|Removed degenerate navmesh face|NavVolume generation is skipped' }
        if ($navWarn) { Warn ("cod2map NAVMESH:`n  " + ($navWarn -join "`n  ")) }

        if ($r.Out -match 'Unable to load navigation mesh generation settings' -or $r.Err -match 'Unable to load navigation mesh generation settings') {
            Write-Host $r.Out
            Die "cod2map64 could not load navmesh settings (cwd was not bin?) - navmesh is STALE; refusing to continue"
        }
        if ($r.Code -ne 0) { Write-Host $r.Out; Write-Host $r.Err; Die "cod2map64 exited $($r.Code)" }
        if (-not (Test-Path $Bsp)) { Die "cod2map64 produced no .d3dbsp at $Bsp" }
        Info ("BSP written: {0:N1} MB @ {1}" -f ((Get-Item $Bsp).Length / 1MB), (Get-Item $Bsp).LastWriteTime)
        if (Test-Path $NavHkt) { Info ("navmesh.hkt updated @ {0}" -f (Get-Item $NavHkt).LastWriteTime) }
        else { Warn "no _navmesh.hkt found at $NavHkt (ground zombies may not path)" }

        # NAVMESH CONNECTIVITY GATE (2026-09-04). lint_tod_navmesh.js decodes the
        # .hkt cod2map just wrote (faces, edges, vertices) and requires every
        # tower floor to sit in ONE connected component.
        # The day it was written the shipped mesh was 18 islands, cut inside the
        # E flight of laps 17/19/33/39/43 on BOTH towers - "random spots where
        # zombies won't attack you", floor 42-44 being the live report. The .hkt
        # BYTE SIZE, the seed count and cod2map's transcript all read clean on
        # that mesh; only reading the faces showed it. A seam is a shipped bug
        # that no play-test below it can see, so this is a hard stop.
        Step "navmesh connectivity gate (lint_tod_navmesh.js)"
        if (Test-Path $NavHkt) {
            $navLint = & node (Join-Path $PSScriptRoot 'lint_tod_navmesh.js') $NavHkt 2>&1 | Out-String
            Write-Host $navLint
            if ($LASTEXITCODE -ne 0) {
                Die "navmesh gate FAILED - the mesh cod2map wrote is not one connected walk per tower (see the SEAM / ISLAND rows above). Zombies cannot cross a seam and a player standing on one cannot be targeted. Fix the geometry (tools/gen_tower_map.js RAMP_LIFT block explains the known cause); never ship past this."
            }
        }
    }

    # =======================================================================
    # 3. Radiant LED lighting recompute - THE BAKE GATE. If it hangs on the
    #    brush.cpp:1860 modal, the geometry re-hit the lightmap-atlas ceiling:
    #    REVERT/FIX before testing (use tools\_bake_test.ps1 to bisect).
    # =======================================================================
    if (-not $SkipLED) {
        Step "Radiant LED (lighting recompute)"
        $ledStarted = Get-Date
        $r = Invoke-BuildExe $Radiant $radArgs 'Radiant LED' $Bin
        if (-not $DryRun) {
            if ($r.Code -ne 0) { Write-Host $r.Out; Write-Host $r.Err; Die "Radiant LED exited $($r.Code); refusing to package a failed bake." }
            $ledFile = Join-Path $Tools ("share\raw\maps\zm\{0}.led" -f $MapName)
            if (-not (Test-Path -LiteralPath $ledFile) -or (Get-Item -LiteralPath $ledFile).LastWriteTime -lt $ledStarted -or (Get-Item -LiteralPath $ledFile).Length -lt 1MB) {
                Die 'Radiant produced no fresh valid-sized LED; refusing stale or missing lighting.'
            }
            Info ("fresh LED: {0:N0} bytes" -f (Get-Item -LiteralPath $ledFile).Length)
            # record the inputs this cod2map + bake saw, so the next full build
            # with identical inputs can skip both (see the REUSE block above)
            if ($geomKeyOk) {
                & node $GeomKey stamp @geomCli
                if ($LASTEXITCODE -ne 0) { Warn "geom_key.js could not record this build; the next full build will compile + bake again" }
            }
        }
    } else {
        Warn "-SkipLED: lighting NOT recomputed (RED FLAG - never use this to hide a broken bake)"
    }
    } # end of the compile + bake path (the REUSE branch above skips all of it)
} else {
    Warn "-GscOnly: skipping cod2map64 + LED (reusing the last BSP + navmesh). Invalid if any brush/entity/material moved."
    # Say so when that is actually the case (2026-09-29). Advisory: the -GscOnly
    # the user asked for still links, but the log now names what moved.
    if (-not $DryRun) {
        $gkOut = & node $GeomKey check @geomCli | Out-String
        if ($LASTEXITCODE -eq 0) { Info "geometry + lighting: current (identical inputs to the last full build)" }
        else {
            Write-Host $gkOut
            Warn "-GscOnly: the map / its materials / the sky are NOT confirmed identical to the last FULL build (see above). This links the OLD compiled map + lighting; run a full build if any of it matters."
        }
    }
}

# ===========================================================================
# 3b. sweep orphaned build lock-temp files (*~lk) - an interrupted build
#     leaves multi-GB orphans that would ship into the Workshop upload.
# ===========================================================================
if (-not $DryRun -and (Test-Path $FfDir)) {
    Step "sweep stale build locks (*~lk)"
    $locks = @(Get-ChildItem -Path $FfDir -Recurse -File -ErrorAction SilentlyContinue |
               Where-Object { $_.Name.EndsWith('~lk') })
    if ($locks.Count -gt 0) {
        foreach ($f in $locks) {
            try {
                Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop
                Info ("  removed {0} ({1:N1} MB)" -f $f.Name, ($f.Length / 1MB))
            } catch {
                Warn ("  could NOT remove {0} - a build may be running? ({1})" -f $f.Name, $_.Exception.Message)
            }
        }
    } else {
        Info "no stale *~lk files (folder clean)"
    }
}

# ===========================================================================
# 3c. -CleanPak: retire the incrementally-grown xpak so the linker writes a
#     fresh one (2026-09-03, docs/86). The linker only APPENDS to the pack:
#     every full build leaves the previous build's reflection probes / probe
#     volumes / sun-shadow tree behind, every replaced asset leaves a hole,
#     and the Workshop upload ships all of it (measured 9.5 GB, ~5.3 GB of
#     it history; 47 shadow trees under one name). The pack is MOVED OUT of
#     zone\ (the upload ships the whole folder, so a rename inside it would
#     upload too), restored if the link fails to write a fresh one, and
#     deleted on BUILD OK. Same volume, so the move is instant.
# ===========================================================================
# A clean pack must include all languages: their image payloads also append.
if ($CleanPak -and $GscOnly) { Die "-CleanPak needs a FULL build (drop -GscOnly)" }
if ($CleanPak -and -not $AllLanguages) {
    $AllLanguages = $true
    Info "-CleanPak: rebuilding all language packs as well as the main pack"
}
$languagesToBuild = @()
if ($AllLanguages) {
    $languagesToBuild = @(Get-ChildItem (Join-Path $Tools 'zone_source') -Directory |
        Where-Object { $_.Name.ToLower() -notin @('all','english') } |
        Sort-Object Name | ForEach-Object { $_.Name })
    if ($languagesToBuild.Count -lt 6) { Die "Incomplete installed language set" }
    foreach ($language in $languagesToBuild) { $null = Get-TodLanguagePrefix $language }
}
if ($CleanPak -and -not $DryRun) {
    Step "clean all packs (rollback retained through the last language)"
    $script:TodPakTransaction = Start-TodCleanPaks $FfDir $MapName $languagesToBuild
    Info "previous compiled files protected outside zone: $($script:TodPakTransaction.HoldDir)"
}

# ===========================================================================
# 4. linker - compile GSC + pack the .ff
# ===========================================================================
# STALE OCCLUSION CACHE (2026-09-28; the test map paid for it 2026-09-06, KB
# section 1). The linker's UmbraConvert builds the occlusion tome from TILES
# cached per map name under share\assetconvert\umbra\cod2map\<map>\ and never
# invalidates them, and it also caches the FINISHED tome per BSP under
# share\assetconvert\umbra\linker\<map>___default___<hash>\. This map linked
# "UmbraConvert: computing 0 tiles" on every full build since 09-23: every
# tile came from the first builds' cache. The Battle Arena room (added 09-27 at
# -8000,-8000, empty space in that cache) was culled whole - floor, walls and
# ceiling invisible from inside, collision intact. Clear both, every FULL
# build (and -GscOnly -FreshOcclusion); the tile directory must EXIST (empty)
# or UmbraConvert computes nothing. The post-link check below makes a
# "computing 0 tiles" link a hard failure.
$umbraFresh = (-not $GscOnly) -or $FreshOcclusion
if ($umbraFresh -and -not $DryRun) {
    Step "clear the Umbra occlusion caches (tiles + finished tomes)"
    $umbraRoot  = Join-Path $Tools 'share\assetconvert\umbra'
    $umbraTiles = Join-Path $umbraRoot ("cod2map\{0}" -f $MapName)
    $umbraGone  = @()
    if (Test-Path $umbraTiles) { $umbraGone += $umbraTiles }
    # the finished tomes are FILES (~6.6 MB each, one per BSP hash), not folders
    $umbraTomes = @(Get-ChildItem (Join-Path $umbraRoot 'linker') -File -Filter ("{0}___*" -f $MapName) -ErrorAction SilentlyContinue)
    foreach ($t in $umbraTomes) {
        try { Remove-Item -LiteralPath $t.FullName -Force -ErrorAction Stop }
        catch { Die "could not delete the cached Umbra tome '$($t.FullName)' ($($_.Exception.Message)) - is a linker still running?" }
    }
    Info ("deleted {0} cached Umbra tome(s)" -f $umbraTomes.Count)
    foreach ($d in $umbraGone) {
        # Rename this map's private cache first, so deletion cannot leave a
        # half cache for the linker. Resolve and guard both paths before moving.
        $d = [IO.Path]::GetFullPath($d)
        $stale = [IO.Path]::GetFullPath("$d.stale_$(Get-Date -Format yyyyMMddHHmmss)")
        Assert-Tod2WritePath $d -Tree
        Assert-Tod2WritePath $stale -Tree
        try { Rename-Item -LiteralPath $d -NewName (Split-Path $stale -Leaf) -ErrorAction Stop }
        catch { Die "could not rename the Umbra cache '$d' ($($_.Exception.Message)) - a process holds a handle inside it (an Explorer window, an ls/find still enumerating it). Close it and rebuild; nothing was deleted." }
        Assert-Tod2WritePath $stale -Tree
        try { Remove-Item -LiteralPath $stale -Recurse -Force -ErrorAction Stop }
        catch { Warn "could not fully delete the guarded stale cache '$stale' ($($_.Exception.Message))" }
        if (Test-Path $stale) { Warn "could not fully delete $stale (renamed aside; harmless)" }
    }
    New-Item -ItemType Directory -Force $umbraTiles | Out-Null
    Info ("cleared {0} Umbra tile cache dir(s)" -f $umbraGone.Count)
}

Step "linker (compile GSC + pack .ff)"
$ffBefore = $null
if (Test-Path $FfDir) { $ffBefore = Get-ChildItem $FfDir -Filter "$MapName.ff" -ErrorAction SilentlyContinue | Select-Object -First 1 }

$linkArgs = @('-language', 'english', '-modsource', $MapName)

# AUTO-RETRY THE FLAKY SOUND STEP (2026-08-24). The wav converter inside the
# linker intermittently null-refs ("Object reference not set to an instance of
# an object") on one or two RANDOM skye_ports wavs and, when it does, ABORTS
# all-language bank emission while still exiting 0. Investigated and ruled out:
# the wavs are intact (normal attributes, exclusive-read succeeds, no lock) and
# Defender was idle across the failures - so it is a concurrency fault inside
# the tool, not the data and not this machine. It clears on a re-run, so the
# build now retries the LINKER ALONE (~1 min) rather than making a human re-run
# the whole thing (~4 min). sound\zone is cleared between attempts so a retry
# cannot inherit a half-written bank. Observed failure rate is roughly 1 in 2,
# so 3 attempts is ~7/8 to succeed; a persistent failure still Dies at the
# BANK-PRESENCE GUARD below.
$maxLinkTries = 3
$SndZoneEarly = Join-Path $Tools ("usermaps\{0}\sound\zone" -f $MapName)
for ($try = 1; $try -le $maxLinkTries; $try++) {
    if ($try -gt 1) {
        Warn ("sound bank missing after linker attempt {0} - clearing sound\zone, retrying linker ({1} of {2})." -f ($try - 1), $try, $maxLinkTries)
        if (Test-Path $SndZoneEarly) { Remove-Item $SndZoneEarly -Recurse -Force -ErrorAction SilentlyContinue }
    }
    $r = Invoke-BuildExe $Linker $linkArgs 'linker' $Bin
    if ($DryRun) { break }
    if ($try -eq 1) { $umbraFirstOut = "$($r.Out)`n$($r.Err)" }   # a retry legitimately reuses attempt 1's tiles
    $sabsNow = @(Get-ChildItem $SndZoneEarly -Recurse -Filter "*.all.sabs" -File -ErrorAction SilentlyContinue | Sort-Object Length -Descending)
    if ($sabsNow.Count -gt 0 -and $sabsNow[0].Length -ge 50MB) {
        if ($try -gt 1) { Info ("sound bank recovered on linker attempt {0}." -f $try) }
        break
    }
}

if (-not $DryRun -and $umbraFresh) {
    # The occlusion tome must have been BUILT FRESH from the cleared cache.
    # NOTE (measured 2026-09-28): this linker ALWAYS prints "computing 0 tiles" -
    # the tiles are computed in its "fetching tiles" phase. The staleness tell
    # is "UmbraConvert: N tiles loaded from cache": the stale builds loaded
    # 2129 / 2557, the first fresh one (tmp/shop_spin/gsc2.log) loaded 0 of
    # 13146 and built an 871-tile tome.
    $umbraCache = [regex]::Match($umbraFirstOut, 'UmbraConvert: (\d+) tiles loaded from cache')
    $umbraTome  = [regex]::Match($umbraFirstOut, 'created tome with (\d+) tiles')
    if (-not $umbraCache.Success -or -not $umbraTome.Success) {
        Die "OCCLUSION: the linker printed no 'created tome' / 'tiles loaded from cache' line after the Umbra caches were cleared - the tome was not rebuilt; parts of the map may be culled invisible."
    }
    $umbraN = [int]$umbraCache.Groups[1].Value
    if ($umbraN -gt 0) {
        Die "OCCLUSION: $umbraN tiles loaded from the Umbra cache that was just cleared - the occlusion tome is stale; parts of the map (the Battle Arena first) render invisible."
    }
    Info ("occlusion tome rebuilt fresh: {0} tiles, 0 from cache" -f $umbraTome.Groups[1].Value)
}

if (-not $DryRun) {
    $allOut   = "$($r.Out)`n$($r.Err)"
    $errLines = @($allOut -split "\r?\n" |
        ForEach-Object { ($_ -replace '\^\d', '').Trim() } |
        Where-Object { $_ -match 'ERROR:' -or $_ -match 'no file for filespec' -or $_ -match 'Unresolved external' })

    # SUCCESS ORACLE = a FRESH .ff was written (see header).
    $ffAfter = $null
    if (Test-Path $FfDir) {
        $ffAfter = Get-ChildItem $FfDir -Filter "$MapName.ff" -ErrorAction SilentlyContinue | Select-Object -First 1
    }
    $freshFf = $ffAfter -and ( (-not $ffBefore) -or ($ffAfter.LastWriteTime -gt $ffBefore.LastWriteTime) )

    if (-not $freshFf) {
        if ($errLines.Count -gt 0) {
            Write-Host "[build] linker errors (aborted before packing the .ff):" -ForegroundColor Red
            $errLines | Select-Object -First 25 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        } else {
            ($allOut -split "\r?\n" | Select-Object -Last 20) | ForEach-Object { Write-Host "  $_" }
        }
        Die "linker did not produce a fresh .ff (exit $($r.Code))"
    }

    $unexpected = @($errLines | Where-Object { $l = $_; -not ($WaivedLinkerErrors | Where-Object { $l -match [regex]::Escape($_) }) })
    $waived     = @($errLines | Where-Object { $l = $_;     ($WaivedLinkerErrors | Where-Object { $l -match [regex]::Escape($_) }) })

    if ($waived.Count -gt 0) {
        Info "$($waived.Count) known-waived asset warning(s) (non-fatal, default-substituted):"
        $waived | Sort-Object -Unique | ForEach-Object { Write-Host "    - $_" -ForegroundColor DarkGray }
    }
    if ($unexpected.Count -gt 0) {
        Warn "$($unexpected.Count) UNEXPECTED linker error(s):"
        $unexpected | Select-Object -First 25 | ForEach-Object { Write-Host "    ! $_" -ForegroundColor Yellow }
        Die 'Unexpected English linker errors; a fresh fastfile alone is not a complete build.'
    }

    # POISONED-BUILD GUARD (2026-08-21 black-screen incident). The start-of-run
    # game check is not enough: if BlackOps3 is LAUNCHED MID-BUILD the game
    # file-locks the sound banks, the linker logs "being used by another
    # process" for the alias bank, KEEPS GOING, and still emits a .ff that
    # "links OK" - with corrupt banks that hang the next load on a black
    # screen. Worse, that linker can outlive a later clean rebuild and
    # overwrite it (the tell is the UmbraDebug 0x000000b7 rename error: two
    # linkers alive). So: any bank lock, or the game appearing during the run,
    # is a HARD FAIL with the ritual spelled out. Never remove this.
    $bankLocked = ($allOut -match 'being used by another process')
    $gameNow    = Get-Process BlackOps3 -ErrorAction SilentlyContinue
    # the watchdog's verdict: did the game appear at ANY point during the build?
    $gameSeen = $false
    if (Test-Path $GameSeenFlag) {
        $gameSeen = $true
        $seenAt = Get-Content $GameSeenFlag -ErrorAction SilentlyContinue | Select-Object -First 1
        Remove-Item $GameSeenFlag -Force -ErrorAction SilentlyContinue
    }
    if ($bankLocked -or $gameNow -or $gameSeen) {
        if ($gameNow)    { Warn "BlackOps3 (pid $($gameNow.Id)) appeared DURING the build." }
        if ($gameSeen -and -not $gameNow) { Warn ("the watchdog saw BlackOps3 running MID-BUILD (first seen {0}) - even though it is closed now." -f $seenAt) }
        if ($bankLocked) { Warn "the linker could not write the sound alias bank (file locked by the game)." }
        Warn "This .ff is POISONED even though the linker reported success. Ritual:"
        Warn "  1) close the game   2) confirm no linker_modtools.exe is still running (tasklist)"
        Warn "  3) delete usermaps\zm_tod2_cybercity\sound\zone\ entirely   4) rebuild"
        Die "sound banks were regenerated while the game was up - do NOT test this build"
    }

    # BANK-PRESENCE GUARD (2026-08-24). An intermittent wav-converter null-ref
    # ("Object reference not set to an instance of an object", 2 random wavs per
    # occurrence, source files intact on disk) can ABORT the whole all-language
    # bank emission and STILL report success: the 11:14 build said "BUILD OK",
    # wrote a fresh .ff, and left sound\zone holding only .sz stubs with NO
    # .all.sabs anywhere - the black-screen-on-boot class. "BUILD OK" is
    # therefore not enough: the bank must EXIST at plausible size. Known-good
    # .all.sabs is ~105 MB; 50 MB is a generous floor that still catches a stub
    # or a partial write. It may sit in sound\zone or under CachedBanks\all -
    # the recursive search covers both. Recovery = the ritual above (delete
    # sound\zone, confirm the game is closed, one full rebuild).
    $SndZone = Join-Path $Tools ("usermaps\{0}\sound\zone" -f $MapName)
    $allSabs = @(Get-ChildItem $SndZone -Recurse -Filter "*.all.sabs" -File -ErrorAction SilentlyContinue | Sort-Object Length -Descending)
    if ($allSabs.Count -eq 0 -or $allSabs[0].Length -lt 50MB) {
        Warn "the all-language sound bank (.all.sabs) is MISSING or truncated under sound\zone."
        Warn "The intermittent wav-converter fault aborted bank emission - the map would load with NO custom audio (music, gun sounds, VO all missing)."
        Warn ("This persisted across {0} linker attempts, so it is NOT the usual transient fault - investigate before retrying." -f $maxLinkTries)
        Die "no usable .all.sabs bank - do NOT test this build"
    }
    Info ("sound bank: {0} ({1:N1} MB)" -f $allSabs[0].Name, ($allSabs[0].Length / 1MB))

    Info ("English link verified: {0} ({1:N1} MB); checking remaining languages before BUILD OK" -f $ffAfter.Name, ($ffAfter.Length / 1MB))
}

if (-not $DryRun) {
    Step "cyber zombie compiled geometry coverage"
    $cyberLedger = Join-Path $Tools ("usermaps\{0}\zone_source\all\assetinfo\{0}_xmodel.csv" -f $MapName)
    if (-not (Test-Path $cyberLedger)) {
        $cyberLedger = Join-Path $Tools ("usermaps\{0}\zone_source\english\assetinfo\{0}_xmodel.csv" -f $MapName)
    }
    & python (Join-Path $PSScriptRoot 'verify_cyber_zombie.py') --compiled-ledger $cyberLedger
    if ($LASTEXITCODE -ne 0) { Die "Cyber zombie compiled geometry is missing or incomplete." }
    & python (Join-Path $PSScriptRoot 'verify_cyber_roster.py') --compiled-ledger $cyberLedger
    if ($LASTEXITCODE -ne 0) { Die "Cyber roster compiled geometry is missing or incomplete." }
    & python (Join-Path $PSScriptRoot 'cyber_elites/verify_assets.py') --compiled-ledger $cyberLedger
    if ($LASTEXITCODE -ne 0) { Die "Charcoal / robotic Doppelgast / default Mangler compiled geometry is missing or incomplete." }
    & python (Join-Path $PSScriptRoot 'crown_alarm/verify_native.py') --compiled-ledger $cyberLedger
    if ($LASTEXITCODE -ne 0) { Die "Crown alarm compiled geometry is missing or incomplete." }
    & python (Join-Path $PSScriptRoot 'heavenly_altar/verify_native.py') --compiled-ledger $cyberLedger
    if ($LASTEXITCODE -ne 0) { Die "Heavenly Altar compiled geometry is missing or incomplete." }
    & python (Join-Path $PSScriptRoot 'teleporter/verify_native.py') --compiled-ledger $cyberLedger
    if ($LASTEXITCODE -ne 0) { Die "Teleporter compiled geometry is missing or incomplete." }
    & python (Join-Path $PSScriptRoot 'partner_shop/verify_native.py') --compiled-ledger $cyberLedger
    if ($LASTEXITCODE -ne 0) { Die "Item shop compiled geometry is missing or incomplete." }
    & python -B (Join-Path $PSScriptRoot 'sky_ships/verify_native.py') --compiled-ledger $cyberLedger
    if ($LASTEXITCODE -ne 0) { Die "Sky fleet compiled models or effects are missing or incomplete (docs/192)." }
    $partnerLedger = $cyberLedger -replace '_xmodel\.csv$', '.csv'
    & python (Join-Path $PSScriptRoot 'partner/verify_assets.py') --ledger $partnerLedger
    if ($LASTEXITCODE -ne 0) { Die "Partner native assets are missing or lost geometry during conversion." }
    & node (Join-Path $PSScriptRoot 'jump_title/test_jump_title.js') --ledger $partnerLedger
    if ($LASTEXITCODE -ne 0) { Die "First-jump crash effects or its client script are missing from the fastfile (docs/196)." }
    & python -B (Join-Path $PSScriptRoot 'lucky/verify_native.py') --compiled-ledger $cyberLedger
    if ($LASTEXITCODE -ne 0) { Die "Lucky models / effects / materials are missing or lost geometry in the compiled assets (docs/197)." }
    & node (Join-Path $PSScriptRoot 'lucky/test_lucky.js') --ledger $partnerLedger
    if ($LASTEXITCODE -ne 0) { Die "Lucky models or effects are missing from the linker ledger (docs/197)." }
    # 2026-10-05 (the 17:33 user log): "zoned + in the ledger" is not "precached" - server FX / models resolve
    # through the linked bgcache table, and an empty-name #precache silently drops the rest of its file's list.
    # Reads THIS build's fresh .ff ($ffAfter): a $variable argument keeps run_build_gates.py from running it
    # pre-build against the previous build's .ff.
    & python -B (Join-Path $PSScriptRoot 'verify_bgcache.py') --ff $ffAfter.FullName
    if ($LASTEXITCODE -ne 0) { Die "A #precache did not reach the linked precache table (tools/verify_bgcache.py): its PlayFX / SetModel will fail at runtime." }
    & node (Join-Path $PSScriptRoot 'haven/test_haven.js') --ledger $partnerLedger
    if ($LASTEXITCODE -ne 0) { Die "Haven dome / effects / tint / script / widget are missing from the linker ledger (docs/202)." }
    # BEGIN THE WAR DAMAGE PASS (docs/205): both scripts, every effect, every decal material and every merged model with all its triangles;
    # phase 2: the server half, the sky director, the conductor twins with all their triangles, the tod/war effects.
    & node (Join-Path $PSScriptRoot 'war_damage/test_war_damage.js') --ledger $partnerLedger
    if ($LASTEXITCODE -ne 0) { Die "War damage models / effects / scripts are missing or lost triangles in the compiled assets (docs/205)." }
    # END THE WAR DAMAGE PASS
    # THE DE JUMP PAD (docs/163 s9): every model + LOD whole, every material COMPLETE, every shipped texture, and no
    # linker usage / techset complaint naming a pad material or model. The 15:32 link of 2026-10-03 listed all 49 pad
    # materials and 12 were EMPTY (one texture with the wrong usage: the linker said so in red, the build said OK, the
    # machine drew flat gray) - a name in the ledger is not a working material.
    & python -B (Join-Path $PSScriptRoot 'jumppad/install_de_jumppad.py') --compiled-ledger $cyberLedger --linker-log (Join-Path $RepoRoot 'tmp\native_build\linker_last.log')
    if ($LASTEXITCODE -ne 0) { Die "The DE jump pad compiled incomplete: an empty material, a missing texture or a linker usage complaint (docs/163 s9)." }
    # docs/208 - MAP 1'S MIGRATION, COMPILED: Nikolai's props, the Cyber Teddy and the cyber inducer linked whole (every
    # model with map 1's triangle count, every material COMPLETE - a ledger row that is only its name draws flat gray -
    # every image), and no linker usage / techset complaint naming one of them.
    & python -B (Join-Path $PSScriptRoot 'fan_props/verify.py') --compiled-ledger $cyberLedger --linker-log (Join-Path $RepoRoot 'tmp\native_build\linker_last.log')
    if ($LASTEXITCODE -ne 0) { Die "Nikolai's props compiled incomplete: an empty material, a missing image or a linker complaint (docs/208)." }
    & python -B (Join-Path $PSScriptRoot 'cyber_teddy/verify.py') --compiled-ledger $cyberLedger --linker-log (Join-Path $RepoRoot 'tmp\native_build\linker_last.log')
    if ($LASTEXITCODE -ne 0) { Die "The Cyber Teddy compiled incomplete (docs/208)." }
    & python -B (Join-Path $PSScriptRoot 'inducer_cyber/verify.py') --compiled-ledger $cyberLedger
    if ($LASTEXITCODE -ne 0) { Die "The cyber Rampage Inducer compiled incomplete: a model, clip, material or image is missing (docs/208)." }
    # NO MATERIAL MAY LINK AGAINST A MISSING SHADER (docs/208; map 1's 2026-09-23 gate). The linker does not fail on a
    # material whose materialType has no techsetdef: it builds it on missing_techsetdef_geometry, logs nothing in the
    # errorlog, and the surface renders as the engine's grey stand-in - how Widow's Wine's powered panel shipped blank
    # (TOD II's 2026-10-02 / 10-03 ledgers: exactly that one row). The asset ledger is the only record. Baseline ZERO:
    # never waive a row here, install the material type's techsetdef (repo share\raw\techsetdefs_stable*, synced).
    $missingTechset = @(Select-String -Path $partnerLedger -Pattern 'missing_techsetdef' -SimpleMatch)
    if ($missingTechset.Count -gt 0) {
        foreach ($mt in $missingTechset) { Info ("  " + $mt.Line) }
        Die ("{0} ledger row(s) name a material built against a MISSING techsetdef (grey stand-in in game). Install the material type's techsetdef under share\raw\techsetdefs_stable and _toolsgfx (docs/208)." -f $missingTechset.Count)
    }
    Info "no material linked against a missing techsetdef"
    # Read this build's actual completed FF definitions, LODs, texture tables, glass mip alpha and animation notes.
    & python -B (Join-Path $PSScriptRoot 'wunderfizz/verify_compiled_assets.py') --ff $ffAfter.FullName
    if ($LASTEXITCODE -ne 0) { Die "BO6 Wunderfizz native model/material/image/animation gate failed." }
    & python -B (Join-Path $PSScriptRoot 'wunderfizz/verify_audio.py') --native $ffAfter.FullName
    if ($LASTEXITCODE -ne 0) { Die "BO6 Wunderfizz native sound aliases or loaded bank failed." }

    # THE PERK MACHINES (docs/208): the four purchase clips (and the five kept pack clips), their three cue effects,
    # the animtree and the module are in the fastfile, and the four replaced donor clips are not.
    & python -B (Join-Path $PSScriptRoot 'verify_perk_machine_presentation.py') --ledger $partnerLedger
    if ($LASTEXITCODE -ne 0) { Die "Perk machine purchase clips / cue effects / animtree / script are missing from the linker ledger (docs/208)." }
}

# ===========================================================================
# 4b. optional: link the NON-ENGLISH language fastfiles  (-AllLanguages)
# ===========================================================================
# WHY (Workshop report 2026-08-26: "ERROR: Could not find zone
# 'fr_zm_tod2_cybercity'"): the game loads a per-language fastfile named
# <prefix>_<map>.ff, and this script only ever linked -language english — so
# every non-English client failed at map load with exactly that error. The
# language ff is tiny (~230 KB of localized strings; our .str files are
# English-only, so other languages fall back to English text — the standard
# Workshop-map arrangement). One linker pass per language, SEQUENTIAL: the
# one-linker-at-a-time rule holds inside a single build too.
# Verification requires the exact expected language prefix and fresh fastfile.
# Clean builds additionally validate every corresponding pack before commit.
if ($AllLanguages -and -not $DryRun) {
    Step "language fastfiles (-AllLanguages)"
    # LANGUAGE SET IS DERIVED, NOT LISTED (2026-09-04, Workshop report
    # "Could not find zone 'ea_zm_tod2_cybercity'"): the hand list here missed
    # 'englisharabic' (prefix ea_, the English/Arabic SKU) and 'polish' (po_),
    # so every client in those languages failed at map load - the SAME bug as
    # the 2026-08-26 French report, one language over. The engine has NO
    # fallback to en_: the per-language ff is resolved before any map script
    # runs, so the only failsafe is to ship one ff per language the linker
    # knows. The linker's language tokens are exactly the folder names under
    # <tools>\zone_source\ (all, english, englisharabic, french, german,
    # italian, japanese, polish, portuguese, russian, simplifiedchinese,
    # spanish, traditionalchinese) - proven 2026-09-04: every one of them
    # ⚠️ THE JAPANESE NOTE BELOW IS HISTORY FOR THE SPRINTER (2026-09-16). The
    # cyber roster replaced every regular appearance and its own derived models
    # ship japaneseUnsafe 0 (install_cyber_roster.py::block, user's call), so a
    # Japanese client now gets the same horde as everyone else. The two stock
    # exclusions in Test-TodExpectedLanguageExclusion are unrelated and stand.
    # linked a fresh <xx>_ ff (the 2026-09-03 "Chinese tokens rejected" was
    # the UNDERSCORED spelling 'simplified_chinese'; the folder spelling works).
    # Excluded: only 'all' and 'english' (the main pass). EVERY other folder
    # ships - user 2026-09-04: "Can we make it so that all possible languages
    # are supported? All prefixes are supported?" Japanese included: its zone
    # drops the japaneseUnsafe sprinter body (docs/86 §8), so a Japanese client
    # plays in English text and may see a placeholder sprinter model - untested,
    # but a guaranteed "Could not find zone 'ja_...'" at launch is strictly
    # worse. A NEW folder requires its verified prefix in clean_paks.ps1;
    # unknown prefixes and failed language passes stop the build.
    $langs = $languagesToBuild
    Info ("languages: {0}" -f ($langs -join ' '))
    foreach ($lang in $langs) {
        # The mid-build game-launch hazard applies to every pass, not just the
        # English one (a launched game file-locks the banks and poisons output).
        if (Get-Process BlackOps3 -ErrorAction SilentlyContinue) {
            Die ("BlackOps3 appeared before the '{0}' language pass - close the game and re-run; do NOT ship a build the game overlapped" -f $lang)
        }
        $prefix = Get-TodLanguagePrefix $lang
        $languageFf = Join-Path $FfDir "${prefix}_$MapName.ff"
        $languageStarted = Get-Date
        $rl = Invoke-BuildExe $Linker @('-language', $lang, '-modsource', $MapName) "linker[$lang]" $Bin
        $languageOut = "$($rl.Out)`n$($rl.Err)"
        $languageErrors = @($languageOut -split "\r?\n" |
            ForEach-Object { ($_ -replace '\^\d', '').Trim() } |
            Where-Object { $_ -match 'ERROR:|no file for filespec|Unresolved external' } |
            Where-Object { -not (Test-TodExpectedLanguageExclusion $Tools $lang $_) } |
            Where-Object { $line = $_; -not ($WaivedLinkerErrors | Where-Object { $line -match [regex]::Escape($_) }) })
        if ($languageErrors.Count -gt 0) { Die ("{0}: unexpected linker errors: {1}" -f $lang, ($languageErrors -join ' | ')) }
        if ($languageOut -match 'being used by another process' -or (Get-Process BlackOps3 -ErrorAction SilentlyContinue) -or (Test-Path $GameSeenFlag)) {
            Die "$lang overlapped the game or a locked sound bank"
        }
        $fresh = Get-Item -LiteralPath $languageFf -ErrorAction SilentlyContinue
        if (-not $fresh -or $fresh.LastWriteTime -le $languageStarted -or $fresh.Length -lt 128) {
            Die ("{0}: no fresh {1} (exit {2})" -f $lang, (Split-Path $languageFf -Leaf), $rl.Code)
        }
        Info ("{0}: {1} ({2:N0} KB)" -f $lang, $fresh.Name, ($fresh.Length / 1KB))
    }
    # The extra passes re-enter the shared sound pipeline, and the flaky wav
    # converter (see the retry note above section 4) can strand a stub bank on
    # any of them while still exiting 0 - re-assert the bank guard so a late
    # pass cannot silently undo a build the English pass already verified.
    $allSabsL = @(Get-ChildItem $SndZone -Recurse -Filter "*.all.sabs" -File -ErrorAction SilentlyContinue | Sort-Object Length -Descending)
    if ($allSabsL.Count -eq 0 -or $allSabsL[0].Length -lt 50MB) {
        Die "the .all.sabs bank is MISSING/truncated after the language passes - do NOT ship; delete sound\zone and rebuild"
    }
    Info ("sound bank still healthy after language passes: {0} ({1:N1} MB)" -f $allSabsL[0].Name, ($allSabsL[0].Length / 1MB))
}

if (-not $DryRun) {
    if ((Get-Process BlackOps3 -ErrorAction SilentlyContinue) -or (Test-Path $GameSeenFlag)) { Die "The game appeared during the build" }
    if ($GameWatchJob) { Stop-Job $GameWatchJob -ErrorAction SilentlyContinue; Remove-Job $GameWatchJob -Force -ErrorAction SilentlyContinue }
    $payload = @(Get-ChildItem -LiteralPath $FfDir -Recurse -File)
    $payloadBytes = ($payload | Measure-Object -Property Length -Sum).Sum
    $payloadReport = [pscustomobject]@{
        when=(Get-Date -Format o); clean=[bool]$CleanPak; allLanguages=[bool]$AllLanguages
        bytes=$payloadBytes
        files=@($payload | ForEach-Object { [pscustomobject]@{ path=$_.FullName.Substring($FfDir.Length+1); bytes=$_.Length; written=$_.LastWriteTime.ToString('o') } })
    }
    $payloadReport | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Tools "usermaps\$MapName\last_payload.json") -Encoding UTF8
    if ($Publish -or $CleanPak) {
        $briefOut = & node (Join-Path $PSScriptRoot 'xpak_report.js') --brief (Join-Path $FfDir "$MapName.xpak") 2>&1
        if ($LASTEXITCODE -notin @(0,2)) { Die "Pack report failed: $briefOut" }
        Info "pack attribution (advisory, binary units): $briefOut"
    }
    if ($script:TodPakTransaction) { Complete-TodCleanPaks $script:TodPakTransaction }
    Step "BUILD OK"
    Info ("fastfile: {0} ({1:N0} bytes)" -f $ffAfter.FullName, $ffAfter.Length)
    Info ("complete upload payload: {0:N0} bytes = {1:N3} GB (decimal), {2} files" -f $payloadBytes, ($payloadBytes / 1e9), $payload.Count)
    Write-Host "[build] READY TO TEST -> .\tools\run_game.ps1 (or PLAY_NORMAL.bat)" -ForegroundColor Green
}

# ===========================================================================
# 4c. publish ledger: stamp the pending row with THIS .ff's write time so the
#     upload can be matched to the build to the second (patch-notes system).
# ===========================================================================
if ($Publish -and -not $DryRun -and -not $SkipNotesGate) {
    $pn = Join-Path $PSScriptRoot 'patch_notes.js'
    & node $pn built --ff (Join-Path $FfDir "$MapName.ff")
    if ($LASTEXITCODE -ne 0) { Warn "patch_notes.js built did not stamp the ledger - run it by hand: node tools/patch_notes.js built" }
    Write-Host "[build] AFTER UPLOADING: node tools/patch_notes.js uploaded   (records the Steam time; paste the BBCode block as the change note)" -ForegroundColor Green
}

# ===========================================================================
# 5. optional launch
# ===========================================================================
if ($Run -and -not $DryRun) {
    Step "launching game (run_game.ps1)"
    & (Join-Path $PSScriptRoot 'run_game.ps1')
}

exit 0
