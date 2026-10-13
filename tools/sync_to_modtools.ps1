# =============================================================================
# sync_to_modtools.ps1 - Mirror the repo's authoring trees into the BO3
# Mod Tools install. Ported from abandoned_cyber_city_zombies (proven).
#
#   .\tools\sync_to_modtools.ps1            forward sync (repo -> Mod Tools)
#   .\tools\sync_to_modtools.ps1 -DryRun    print only
#   .\tools\sync_to_modtools.ps1 -Reverse   pull Mod Tools edits back (after
#                                           editing the map in Radiant)
#
# Layout facts:
#   repo\scripts\*      -> usermaps\zm_tod2_cybercity\scripts\*      (MIRROR)
#   repo\zone_source\*  -> usermaps\zm_tod2_cybercity\zone_source\*  (MIRROR)
#   repo\sound\*        -> usermaps\zm_tod2_cybercity\sound\*        (MIRROR)
#   repo\ui\*           -> usermaps\zm_tod2_cybercity\ui\*           (MIRROR)
#   repo\zone\*         -> usermaps\zm_tod2_cybercity\zone\*         (COPY, no
#       delete: Launcher writes workshop.json + publish artifacts here)
#   repo\map_source\zm\zm_tod2_cybercity.map -> <tools>\map_source\zm\  (single
#       file COPY - Radiant map sources live in the TOOLS root map_source, not
#       usermaps; never mirror that folder, it holds _prefabs + other maps)
# =============================================================================

[CmdletBinding()]
param(
    [string]$ModToolsRoot = "",
    [switch]$DryRun,
    [switch]$Reverse
)

$ErrorActionPreference = "Stop"

$MapName = "zm_tod2_cybercity"

function Write-Info($msg) {
    Write-Host "[sync] $msg"
}

. (Join-Path $PSScriptRoot 'tod2_workspace.ps1')
function Resolve-ModToolsRoot { Resolve-Tod2Root $ModToolsRoot }

function Ensure-Dir($path) {
    Assert-Tod2WritePath $path -Repository:$Reverse
    if (-not (Test-Path $path)) {
        if ($DryRun) {
            Write-Info "DRY: would mkdir $path"
        } else {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
    }
}

# Mirror = destination becomes an exact copy (robocopy /MIR; deletes extras).
# Copy   = overwrite-copy only; destination-only files survive.
function Copy-Tree($src, $dst, $label, $mirror) {
    Assert-Tod2WritePath $dst -Repository:$Reverse -Tree
    if (-not (Test-Path $src)) {
        Write-Info "skip ($label): $src does not exist"
        return
    }

    Ensure-Dir (Split-Path $dst -Parent)

    if ($DryRun) {
        Write-Info "DRY: ${label}: $src -> $dst (mirror=$mirror)"
        return
    }

    Write-Info "${label}: $src -> $dst (mirror=$mirror)"

    $args = @("`"$src`"", "`"$dst`"")
    if ($mirror) { $args += "/MIR" } else { $args += "/E" }
    $args += @("/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:2", "/W:1")

    $rc = Start-Process robocopy -NoNewWindow -Wait -PassThru -ArgumentList $args

    # robocopy: 0 = no change, 1 = copied, 2 = extras, 3 = both; >= 8 = failure.
    if ($rc.ExitCode -ge 8) {
        throw "robocopy failed ($label) with exit code $($rc.ExitCode)"
    }
}

function Copy-One($src, $dst, $label) {
    Assert-Tod2WritePath $dst -Repository:$Reverse
    if (-not (Test-Path $src)) {
        Write-Info "skip ($label): $src does not exist"
        return
    }

    Ensure-Dir (Split-Path $dst -Parent)

    if ($DryRun) {
        Write-Info "DRY: ${label}: $src -> $dst"
        return
    }

    Write-Info "${label}: $src -> $dst"
    Copy-Item -Path $src -Destination $dst -Force
}

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ModTools = Resolve-ModToolsRoot
$MapRoot  = Join-Path $ModTools "usermaps\$MapName"

Write-Info "repo     = $RepoRoot"
Write-Info "modtools = $ModTools"
Write-Info "target   = $MapRoot"
Write-Info "mode     = $(if ($Reverse) {'REVERSE (modtools -> repo)'} else {'FORWARD (repo -> modtools)'})"
if ($DryRun) { Write-Info "DRY RUN - no files will be written" }

if (-not $Reverse) { Ensure-Dir $MapRoot }
# Only add Tower II's uniquely named child; never repoint game/usermaps.
if (-not $Reverse -and -not $DryRun) { Connect-Tod2GameFolder }

$mappings = @(
    @{ Label = "scripts";      RepoRel = "scripts";      ModRel = "scripts";      Mirror = $true  },
    @{ Label = "zone_source";  RepoRel = "zone_source";  ModRel = "zone_source";  Mirror = $true  },
    @{ Label = "sound";        RepoRel = "sound";        ModRel = "sound";        Mirror = $true  },
    @{ Label = "ui";           RepoRel = "ui";           ModRel = "ui";           Mirror = $true  },
    # Aetherium HUD kit: custom TTF fonts (zone `ttf,` lines) + kill-feed strings
    @{ Label = "fonts";            RepoRel = "fonts";            ModRel = "fonts";            Mirror = $true  },
    @{ Label = "localizedstrings"; RepoRel = "localizedstrings"; ModRel = "localizedstrings"; Mirror = $true  },
    # Keep installed third-party animation trees alongside this map's tree.
    @{ Label = "animtrees";    RepoRel = "animtrees";    ModRel = "animtrees";    Mirror = $false },
    # docs/160: AI anim mapping / selector tables (the Doppelghast's
    # hb_doppelghast_dev.ai_am / .ai_ast, named by its aitype GDT). COPY, not
    # mirror, like animtrees — Hellbound's sync carries the same mapping.
    @{ Label = "animtables";   RepoRel = "animtables";   ModRel = "animtables";   Mirror = $false },
    # Map-name vision (rawfile,vision/zm_tod2_cybercity.vision). The engine sets
    # every client's base vision BY MAP NAME (visionset_mgr_shared.csc
    # finalize_initialization -> GetDvarString("mapname")); with no such file in
    # the .ff the renderer showed its warm-orange fallback — the 2026-08-26
    # "permanent orange tint" report. COPY, not mirror (map 1's rule).
    @{ Label = "vision";       RepoRel = "vision";       ModRel = "vision";       Mirror = $false },
    # Custom level weapon table (stock rows + the class guns). COPY, not mirror.
    @{ Label = "gamedata";     RepoRel = "gamedata";     ModRel = "gamedata";     Mirror = $false },
    @{ Label = "zone";         RepoRel = "zone";         ModRel = "zone";         Mirror = $false }
)

foreach ($m in $mappings) {
    $repoPath = Join-Path $RepoRoot $m.RepoRel
    $modPath  = Join-Path $MapRoot  $m.ModRel

    if ($Reverse) {
        # Never mirror on reverse - the repo has files the tools side lacks.
        Copy-Tree $modPath $repoPath $m.Label $false
    } else {
        Copy-Tree $repoPath $modPath $m.Label $m.Mirror
    }
}

# Radiant map source: single file into the TOOLS root map_source\zm\.
$repoMap = Join-Path $RepoRoot "map_source\zm\$MapName.map"
$modMap  = Join-Path $ModTools "map_source\zm\$MapName.map"

if ($Reverse) {
    Copy-One $modMap $repoMap "map_source"
} else {
    Copy-One $repoMap $modMap "map_source"
}

# Custom prefabs (if this map ever authors its own under map_source\_prefabs\tod).
$repoPrefabs = Join-Path $RepoRoot "map_source\_prefabs\tod"
$modPrefabs  = Join-Path $ModTools "map_source\_prefabs\tod"

if ($Reverse) {
    Copy-Tree $modPrefabs $repoPrefabs "map_source\_prefabs\tod" $false
} else {
    Copy-Tree $repoPrefabs $modPrefabs "map_source\_prefabs\tod" $false
}

# Custom FX sources (repo share\raw\fx\...) land in the TOOLS share tree the
# linker reads. COPY (never mirror) — the tools share tree holds stock + other
# packs. Currently: the acc/light perk-glow recolours ported from map 1.
if (-not $Reverse) {
    Copy-Tree (Join-Path $RepoRoot "share\raw\fx") (Join-Path $ModTools "share\raw\fx") "share\raw\fx" $false
    Copy-Tree (Join-Path $RepoRoot "share\raw\collmaps") (Join-Path $ModTools "share\raw\collmaps") "native custom model collision sources" $false
    # CUSTOM SHADER DEFINITIONS (docs/208; map 1's v19.43): the SAT Widow's Wine machine's powered
    # panel material is authored on lit_emissive_scroll_3layer_advanced_fullspec, a techsetdef the
    # pack's CODE archive ships and this install never had. Without it the linker builds that
    # material against missing_techsetdef_geometry and the whole front panel renders as the engine's
    # grey stand-in once the machine is powered. The def is a stock lit_emissive_scroll_3layer_advanced
    # + the fullspec additions and names only stock shader sources. COPY (never mirror): these trees
    # hold every stock def. build_map.ps1 fails the link if any material still lands on a missing techset.
    Copy-Tree (Join-Path $RepoRoot "share\raw\techsetdefs_stable") (Join-Path $ModTools "share\raw\techsetdefs_stable") "custom techsetdefs" $false
    Copy-Tree (Join-Path $RepoRoot "share\raw\techsetdefs_stable_toolsgfx") (Join-Path $ModTools "share\raw\techsetdefs_stable_toolsgfx") "custom techsetdefs (toolsgfx)" $false
}

# GDT assets (repo source_data\...) land at the TOOLS ROOT source_data\ — the
# usermap tree is NOT scanned for GDTs. COPY (never mirror) — the tools
# source_data holds stock + every other pack's GDTs. NOTE: after a GDT
# changes, gdtdb /update must run before the linker or it errors "unable to
# locate asset in gdtdb" (build_map.ps1 runs it when repo GDTs are newer).
if (-not $Reverse) {
    Copy-Tree (Join-Path $RepoRoot "source_data") (Join-Path $ModTools "source_data") "source_data (GDTs)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_cyber_zombie") (Join-Path $ModTools "model_export\tod_cyber_zombie") "cyber zombie models and textures" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_heavenly_altar") (Join-Path $ModTools "model_export\tod_heavenly_altar") "Heavenly Altar models and baked textures" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_teleporter") (Join-Path $ModTools "model_export\tod_teleporter") "enhanced teleporter models and baked textures" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_partner") (Join-Path $ModTools "model_export\tod_partner") "four buildable partner models" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_shop") (Join-Path $ModTools "model_export\tod_shop") "item shop models and baked textures" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_dealer_presence") (Join-Path $ModTools "model_export\tod_dealer_presence") "Dealer surveillance portrait texture" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_surface") (Join-Path $ModTools "model_export\tod_surface") "shared Cybercity surface textures" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_archer") (Join-Path $ModTools "model_export\tod_archer") "Archer equipment models and textures" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_cyber_elites") (Join-Path $ModTools "model_export\tod_cyber_elites") "charcoal red horde and robotic Doppelgast" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_alarm_button") (Join-Path $ModTools "model_export\tod_alarm_button") "the alarm button stand + cap models and textures" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_sky_ships") (Join-Path $ModTools "model_export\tod_sky_ships") "THE SKY FLEET ship models and textures (docs/192)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_jump_title") (Join-Path $ModTools "model_export\tod_jump_title") "THE LIT SIGN CARD the first jump shows over the dull sky sign (docs/196 s6)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_lucky") (Join-Path $ModTools "model_export\tod_lucky") "THE LUCKY SOURCES: the Lucky Clover + Lucky Meteor models and textures, the Golden Zombie's gold images (docs/197)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_crown_alarm") (Join-Path $ModTools "model_export\tod_crown_alarm") "physical red crown alarm models and textures" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_dealer") (Join-Path $ModTools "model_export\tod_dealer") "THE DEALER boss: body, cracked-mask body, scythe, weapons, atlases (docs/199)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_haven") (Join-Path $ModTools "model_export\tod_haven") "THE HAVENS: the safe zones' force-field dome + field + screen tint images (docs/202)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_jumppad") (Join-Path $ModTools "model_export\tod_jumppad") "THE DE JUMP PAD: Der Eisendrache's jumpsphere machine, deck and landing pad + textures (docs/163 s9)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_cyber_teddy") (Join-Path $ModTools "model_export\tod_cyber_teddy") "THE CYBER TEDDY: the song hunt's bear, map 1's v19.64 model + textures (docs/208)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_fan_props") (Join-Path $ModTools "model_export\tod_fan_props") "NIKOLAI'S PROPS: the Ammo Box V6, the TOWER OF DOOM CYBERCITY sign, the Grid Terminal power switch + its dial / screens (docs/208)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_war_damage") (Join-Path $ModTools "model_export\tod_war_damage") "THE WAR DAMAGE PASS: the merged rubble / rebar / iron / scorch-decal models + the torn conduits conductor twins (docs/205)" $false
    Copy-Tree (Join-Path $RepoRoot "sound_assets\tod\war") (Join-Path $ModTools "sound_assets\tod\war") "THE WAR DAMAGE PASS phase 2: the war generated sounds (docs/205 s7)" $false   # model_export\tod_war_damage: one tag cuts both rows
    Copy-Tree (Join-Path $RepoRoot "xanim_export\tod_dealer") (Join-Path $ModTools "xanim_export\tod_dealer") "THE DEALER boss: his authored clips (docs/199)" $false
    Copy-Tree (Join-Path $RepoRoot "xanim_export\tod_archer") (Join-Path $ModTools "xanim_export\tod_archer") "Archer native first-person animations" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_baseball_bat") (Join-Path $ModTools "model_export\tod_baseball_bat") "baseball bat models" $false
    Copy-Tree (Join-Path $RepoRoot "xanim_export\tod_baseball_bat") (Join-Path $ModTools "xanim_export\tod_baseball_bat") "baseball bat animations" $false
    # docs/208 (map 1's v19.32): the Double Tap / Wisp Tea purchase clips and their conversion skeletons. MAP-OWNED
    # tod2_perk_machines, not map 1's tod_perk_machines: that model folder in the private root is a junction into the
    # shared install (map 1's deployed copy) and Assert-Tod2WritePath refuses a write through it.
    Copy-Tree (Join-Path $RepoRoot "model_export\tod2_perk_machines") (Join-Path $ModTools "model_export\tod2_perk_machines") "perk machine purchase clip skeletons (Double Tap cowboy, Wisp Tea)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod2_bo6_wunderfizz") (Join-Path $ModTools "model_export\tod2_bo6_wunderfizz") "original BO6 Wunderfizz fourteen LODs and texture maps" $false
    Copy-Tree (Join-Path $RepoRoot "xanim_export\tod2_bo6_wunderfizz") (Join-Path $ModTools "xanim_export\tod2_bo6_wunderfizz") "original BO6 Wunderfizz activation" $false
    Copy-Tree (Join-Path $RepoRoot "xanim_export\tod2_perk_machines") (Join-Path $ModTools "xanim_export\tod2_perk_machines") "perk machine purchase clips (Double Tap volley, Wisp Tea activation)" $false
    # Warrior tier 1 (One Inch Punch): first-person clips + the empty view model, installed by tools/warrior/install_punch.py
    Copy-Tree (Join-Path $RepoRoot "xanim_export\tod_warrior") (Join-Path $ModTools "xanim_export\tod_warrior") "Warrior punch animations" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_warrior") (Join-Path $ModTools "model_export\tod_warrior") "Warrior punch view model" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_necro_staff") (Join-Path $ModTools "model_export\tod_necro_staff") "Necromancer staff models and maps" $false
    Copy-Tree (Join-Path $RepoRoot "xanim_export\tod_necro_staff") (Join-Path $ModTools "xanim_export\tod_necro_staff") "Necromancer staff casting animations" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_wunderstrahl") (Join-Path $ModTools "model_export\tod_wunderstrahl") "THE WUNDERSTRAHL: the laser gun's view / world / pickup models + baked textures (docs/219)" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_wunderstrahl_fx") (Join-Path $ModTools "model_export\tod_wunderstrahl_fx") "THE WUNDERSTRAHL: the beam + effect textures (docs/219)" $false
    Copy-Tree (Join-Path $RepoRoot "xanim_export\tod_wunderstrahl") (Join-Path $ModTools "xanim_export\tod_wunderstrahl") "THE WUNDERSTRAHL: the DG-2 first-person clips, renamed (docs/219)" $false
    # v18.99h: the BO6 RAMPAGE INDUCER (the real one - an Aetherium essence
    # container plus its four crystal shards), written by
    # tools/bo6_extraction/install_inducer_bo3.py.
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_bo6_inducer") (Join-Path $ModTools "model_export\tod_bo6_inducer") "BO6 rampage inducer model (unzoned rollback since docs/208)" $false
    # docs/208: THE CYBER INDUCER (map 1's v19.68m) - its model + nine images and its two looping clips.
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_inducer_cyber") (Join-Path $ModTools "model_export\tod_inducer_cyber") "cyber rampage inducer model" $false
    Copy-Tree (Join-Path $RepoRoot "xanim_export\tod_inducer_cyber") (Join-Path $ModTools "xanim_export\tod_inducer_cyber") "cyber rampage inducer loops" $false
    # docs/157: the Breacher's Apex guns. Only the private black emission mask
    # lives here (tools/install_breacher_apex.py); the Apex meshes and textures
    # are read in place from the read-only model_export\apex input.
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_breacher_apex") (Join-Path $ModTools "model_export\tod_breacher_apex") "Breacher Apex emission mask" $false
    # 2026-09-25: Fuse's Knuckle Cluster (the Breacher CLUSTER tactical), written by
    # tools/apex_weapons/import_fuse_cluster.py from the installed Apex.
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_fuse_cluster") (Join-Path $ModTools "model_export\tod_fuse_cluster") "Fuse Knuckle Cluster models" $false
    # 2026-09-26: the Necromancer thrall's white eye texture (tools/necromancer/make_helper_models.py)
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_necro") (Join-Path $ModTools "model_export\tod_necro") "Necromancer helper eye texture" $false
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_fire_bow") (Join-Path $ModTools "model_export\tod_fire_bow") "Fire Bow original lava texture" $false
    # 2026-09-28: THE KEEPER (docs/186), written by tools/keeper/install_keeper.py from the T7 pack.
    # His state machine + behavior tree go to the tools share tree beside stock's (zm_zombie.ai_asm lives there);
    # his anim mapping / selector tables ride the usermap animtables mapping like the Mangler's.
    Copy-Tree (Join-Path $RepoRoot "model_export\tod_keeper") (Join-Path $ModTools "model_export\tod_keeper") "Keeper boss model and textures" $false
    Copy-Tree (Join-Path $RepoRoot "xanim_export\tod_keeper") (Join-Path $ModTools "xanim_export\tod_keeper") "Keeper boss animations" $false
    Copy-Tree (Join-Path $RepoRoot "share\raw\animstatemachines") (Join-Path $ModTools "share\raw\animstatemachines") "share\raw\animstatemachines" $false
    Copy-Tree (Join-Path $RepoRoot "share\raw\behavior") (Join-Path $ModTools "share\raw\behavior") "share\raw\behavior" $false
}

# Sound alias CSVs also have to land in share\raw\sound\aliases\ (the linker's
# sound-bank build reads THAT path, not the usermap copy - map 1 lesson). COPY
# (never mirror) so stock sources survive.
if (-not $Reverse) {
    $aliasSrc = Join-Path $RepoRoot "sound\aliases"
    $aliasDst = Join-Path $ModTools "share\raw\sound\aliases"
    if (Test-Path $aliasSrc) {
        Ensure-Dir $aliasDst
        Get-ChildItem $aliasSrc -Filter *.csv | ForEach-Object {
            Copy-One $_.FullName (Join-Path $aliasDst $_.Name) "sound-alias->share\raw"
        }
    }
}

# Wav sources (repo sound_assets\...) land at the TOOLS ROOT sound_assets\ -
# alias FileSpec paths resolve against that tree at sound-bank build. COPY
# (never mirror) - the tools tree holds map 1's + the packs' wavs too.
# *.wav ONLY: a non-wav file in that tree (a README) crashed the bank builder
# with "Object reference not set" (2026-08-19).
if (-not $Reverse) {
    $wavSrc = Join-Path $RepoRoot "sound_assets"
    $wavDstRoot = Join-Path $ModTools "sound_assets"
    if (Test-Path $wavSrc) {
        Get-ChildItem $wavSrc -Recurse -Filter *.wav | ForEach-Object {
            $rel = $_.FullName.Substring($wavSrc.Length + 1)
            $dst = Join-Path $wavDstRoot $rel
            Ensure-Dir (Split-Path $dst -Parent)
            Copy-One $_.FullName $dst "sound_assets (wav)"
        }
    }
}

Write-Info "done"
