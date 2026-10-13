"""THE WUNDERSTRAHL's shared-file wiring (docs/219, 2026-10-05): every edit outside the feature's own files, in ONE
idempotent pass, run LAST, right before the build (CLAUDE.md "Wire shared files LAST").

  python tools/wunderstrahl/wire.py                 apply every edit not yet applied (each anchor must match exactly once)
  python tools/wunderstrahl/wire.py --check         report applied / missing; exit 1 if any is missing
  python tools/wunderstrahl/wire.py --root DIR      act on a copy (a scratch mirror) instead of the repo

Each edit names a MARKER (its presence means "applied") and an ANCHOR. An insertion takes the line ending of its anchor
line (these files are LF, CRLF, or CRLF with a BOM), so no file's endings change. A missing or doubled anchor stops the
whole pass before anything is written.
"""
import argparse
import pathlib
import re
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]

WS_ON = 'zombie_powerup_tod_wunderstrahl_on'

IMG_BLOCK = '''	"{name}" ( "image.gdf" )
	{{
		"arabicUnsafe" "0"
		"baseImage" "source_data/tod_ui_images/_images/{name}.png"
		"clampU" "0"
		"clampV" "0"
		"colorSRGB" "1"
		"compressionMethod" "compressed high color"
		"coreSemantic" "sRGB3chAlpha"
		"doNotResize" "0"
		"forceStreaming" "0"
		"fromAlpha" "0"
		"imageType" "Texture"
		"mipBase" "1/1"
		"mipMode" "Average"
		"noMipMaps" "1"
		"noPicMip" "1"
		"premulAlpha" "0"
		"semantic" "diffuseMap"
		"streamable" "1"
		"textureAtlasColumnCount" "1"
		"textureAtlasRowCount" "1"
		"type" "image"
	}}'''

# (file, marker, op, anchor, payload)
#   after / before : insert payload lines after / before the ONE line matching the anchor regex
#   sub            : replace the ONE occurrence of the anchor substring (single line) with the payload
#   before_last    : insert payload lines before the file's last non-empty line (a GDT's closing brace)
EDITS = [
    ('scripts/zm/zm_tod2_cybercity.gsc', '_tod_wunderstrahl;', 'after',
     r'^#using scripts\\zm\\zm_tod2_cybercity\\_tod_powerups;$',
     ['#using scripts\\zm\\zm_tod2_cybercity\\_tod_wunderstrahl;   // [tod] THE WUNDERSTRAHL (docs/219): the laser power-up gun - REGISTER_SYSTEM self-init, this #using arms it']),
    ('scripts/zm/zm_tod2_cybercity.csc', '_tod_wunderstrahl;', 'after',
     r'^#using scripts\\zm\\zm_tod2_cybercity\\_tod_powerups;$',
     ['#using scripts\\zm\\zm_tod2_cybercity\\_tod_wunderstrahl;   // [tod] THE WUNDERSTRAHL (docs/219): its tray clientfield (REGISTER_SYSTEM self-init)']),
    ('zone_source/zm_tod2_cybercity.zone', 'include,tod2_wunderstrahl', 'after', r'^include,xmas_gun$',
     ['include,tod2_wunderstrahl']),
    ('zone_source/zm_tod2_cybercity.zone', 'image,i_tod_pu2_wunderstrahl', 'after', r'^image,i_tod_pu2_zombie_blood$',
     ['image,i_tod_pu2_wunderstrahl']),
    ('zone_source/zm_tod2_cybercity.zone', 'image,i_tod_hud_gun_wunderstrahl', 'after', r'^image,i_tod_hud_gun_greatsword$',
     ['image,i_tod_hud_gun_wunderstrahl']),
    # ---- the shared slot ---------------------------------------------------------------------------------------------
    ('scripts/zm/zm_tod2_cybercity/_tod_powerups.gsc', 'TOD_WS_DROP_PCT', 'sub',
     '#define TOD_MINIGUN_DROP_PCT  50   // Death Machine (= the Gift of Death here): same',
     '#define TOD_MINIGUN_DROP_PCT  25   // Death Machine (= the Gift of Death): HALF its slot - THE SHARED SLOT note above'),
    ('scripts/zm/zm_tod2_cybercity/_tod_powerups.gsc', 'THE SHARED SLOT (docs/219, 2026-10-05;', 'after',
     r'^// The DEATH MACHINE is deliberately untouched at 50: only PaP was named\.$',
     ['// THE SHARED SLOT (docs/219, 2026-10-05; user: the Wunderstrahl "shares the Gift of Death drop"): the Death Machine',
      '// slot now hands out the Gift of Death OR the Wunderstrahl, 50/50, so big-weapon drops are no more common. Each',
      '// half is a 25 gate (this define and _tod_wunderstrahl.gsc TOD_WS_DROP_PCT, LOCKSTEP; tools/wunderstrahl/',
      '// test_wunderstrahl.js holds them equal and summing to the old 50), and neither drops while anyone holds either gun.']),
    ('scripts/zm/zm_tod2_cybercity/_tod_powerups.gsc', 'never while anyone holds the Wunderstrahl', 'before',
     r'^\treturn \( RandomInt\( 100 \) < TOD_MINIGUN_DROP_PCT \);$',
     ['\t// THE SHARED SLOT (docs/219): never while anyone holds the Wunderstrahl, the slot\'s other half',
      '\tforeach ( p in GetPlayers() )',
      '\t\tif ( isdefined( p.zombie_vars ) && IS_TRUE( p.zombie_vars[ "' + WS_ON + '" ] ) )',
      '\t\t\treturn false;']),
    ('scripts/zm/zm_tod2_cybercity/_tod_powerups.gsc', 'IS_TRUE( player.zombie_vars[ "' + WS_ON + '" ] )', 'sub',
     'if ( isdefined( player.zombie_vars ) && IS_TRUE( player.zombie_vars[ "zombie_powerup_minigun_on" ] ) )',
     'if ( isdefined( player.zombie_vars ) && ( IS_TRUE( player.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( player.zombie_vars[ "' + WS_ON + '" ] ) ) )'),
    ('scripts/zm/zm_tod2_cybercity/_tod_powerups.gsc', 'IS_TRUE( self.zombie_vars[ "' + WS_ON + '" ] )', 'sub',
     'if ( !( isdefined( self.zombie_vars ) && IS_TRUE( self.zombie_vars[ "zombie_powerup_minigun_on" ] ) ) )',
     'if ( !( isdefined( self.zombie_vars ) && ( IS_TRUE( self.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( self.zombie_vars[ "' + WS_ON + '" ] ) ) ) )'),
    # ---- the power scale: the beam's ticks are already a tenth ---------------------------------------------------------
    ('scripts/zm/zm_tod2_cybercity/_tod_power_scale.gsc', 'return "wunderstrahl";', 'after',
     r'^\t\tif \( IsSubStr\( weapon\.name, "xmas_gun" \) \) return "gift_of_death";$',
     ['\t\tif ( IsSubStr( weapon.name, "wunderstrahl" ) ) return "wunderstrahl";   // docs/219: the beam\'s ticks are fractions of max health']),
    # ---- the guards that already refuse the Gift of Death -------------------------------------------------------------
    ('scripts/zm/zm_tod2_cybercity/_tod_class_terminal.gsc', WS_ON, 'sub',
     'st.death_machine = ( isdefined( self.zombie_vars ) && IS_TRUE( self.zombie_vars[ "zombie_powerup_minigun_on" ] ) );',
     'st.death_machine = ( isdefined( self.zombie_vars ) && ( IS_TRUE( self.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( self.zombie_vars[ "' + WS_ON + '" ] ) ) );   // the Gift of Death or the Wunderstrahl (docs/219)'),
    ('scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc', '|| IS_TRUE( self.zombie_vars[ "' + WS_ON + '" ] )', 'sub',
     '|| ( isdefined( self.zombie_vars ) && IS_TRUE( self.zombie_vars[ "zombie_powerup_minigun_on" ] ) ) )',
     '|| ( isdefined( self.zombie_vars ) && ( IS_TRUE( self.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( self.zombie_vars[ "' + WS_ON + '" ] ) ) ) )'),
    ('scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc', '|| IS_TRUE( player.zombie_vars[ "' + WS_ON + '" ] )', 'sub',
     'if ( isdefined( player.zombie_vars ) && IS_TRUE( player.zombie_vars[ "zombie_powerup_minigun_on" ] ) )',
     'if ( isdefined( player.zombie_vars ) && ( IS_TRUE( player.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( player.zombie_vars[ "' + WS_ON + '" ] ) ) )'),
    # ---- the HUD -------------------------------------------------------------------------------------------------------
    ('ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumPowerupsContainer.lua', 'clientFieldName = "tod_wunderstrahl"', 'after',
     r'^\t\timage = "i_tod_pu2_zombie_blood"$',
     ['\t},',
      '\t-- THE WUNDERSTRAHL (docs/219, 2026-10-05): the laser power-up gun\'s 30 s window. The gsc/csc add_zombie_powerup pair',
      '\t-- carries the "tod_wunderstrahl" clientfield + per-player on/time vars (Zombie Blood\'s contract above).',
      '\t{',
      '\t\tclientFieldName = "tod_wunderstrahl",',
      '\t\tname = "Wunderstrahl",',
      '\t\timage = "i_tod_pu2_wunderstrahl"']),
    ('ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumLoadout.lua', '[ "tod2_wunderstrahl" ]', 'after',
     r'^\t\[ "xmas_gun" \]\s+= "gift",$',
     ['\t[ "tod2_wunderstrahl" ]   = "wunderstrahl",   -- THE WUNDERSTRAHL (docs/219): the laser power-up gun, its own cell']),
    ('ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumLoadout.lua', '[ "WUNDERSTRAHL" ]', 'after',
     r'^\t\[ "X-MASS MURDER" \] = "gift",$',
     ['\t[ "WUNDERSTRAHL" ] = "wunderstrahl",   -- docs/219 (source_data/tod2_wunderstrahl.gdt displayName)']),
    ('ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumLoadout.lua', 'wunderstrahl = true', 'sub',
     'gauntlet = true, greatsword = true }', 'gauntlet = true, greatsword = true, wunderstrahl = true }'),
    ('source_data/tod_ui_images.gdt', '"i_tod_pu2_wunderstrahl" ( "image.gdf" )', 'before_last', None,
     IMG_BLOCK.format(name='i_tod_pu2_wunderstrahl').split('\n') + IMG_BLOCK.format(name='i_tod_hud_gun_wunderstrahl').split('\n')),
    # ---- the sound zone ------------------------------------------------------------------------------------------------
    ('sound/zoneconfig/zm_tod2_cybercity.szc', '"Filename": "tod_wunderstrahl.csv"', 'after',
     r'^            "Filename": "tod_ports\.csv",$',
     ['            "Specs": []',
      '        },',
      '        {',
      '            "Type": "ALIAS",',
      '            "Name": "tod_wunderstrahl",',
      '            "Filename": "tod_wunderstrahl.csv",']),
    # ---- the sync + the build gates ------------------------------------------------------------------------------------
    ('tools/sync_to_modtools.ps1', '"model_export\\tod_wunderstrahl"', 'after',
     r'xanim_export\\tod_necro_staff"\) \(Join-Path \$ModTools "xanim_export\\tod_necro_staff"\)',
     ['    Copy-Tree (Join-Path $RepoRoot "model_export\\tod_wunderstrahl") (Join-Path $ModTools "model_export\\tod_wunderstrahl") "THE WUNDERSTRAHL: the laser gun\'s view / world / pickup models + baked textures (docs/219)" $false',
      '    Copy-Tree (Join-Path $RepoRoot "model_export\\tod_wunderstrahl_fx") (Join-Path $ModTools "model_export\\tod_wunderstrahl_fx") "THE WUNDERSTRAHL: the beam + effect textures (docs/219)" $false',
      '    Copy-Tree (Join-Path $RepoRoot "xanim_export\\tod_wunderstrahl") (Join-Path $ModTools "xanim_export\\tod_wunderstrahl") "THE WUNDERSTRAHL: the DG-2 first-person clips, renamed (docs/219)" $false']),
    ('tools/build_map.ps1', 'wunderstrahl/install.py', 'after',
     r'Die "PK26 elite effects wiring failed \(tools/fxgen/elites/test_elite_fx\.js\)\." \}$',
     ['    # THE WUNDERSTRAHL (docs/219, 2026-10-05): the laser power-up gun - the weapon file + zone, the model / clips, the',
      '    # beam + effects + flame table, the sounds, the HUD icons, and the shared slot / damage / wiring contract.',
      '    & python -B (Join-Path $PSScriptRoot "wunderstrahl/install.py") --check',
      '    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl weapon file / zone package is stale or broken - run: python tools/wunderstrahl/install.py" }',
      '    & python -B (Join-Path $PSScriptRoot "wunderstrahl/model/install_art.py") --check',
      '    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl model / clip GDT is stale or a referenced file moved - see tools/wunderstrahl/model/install_art.py." }',
      '    & python -B (Join-Path $PSScriptRoot "wunderstrahl/fx/make_fx.py") --check',
      '    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl beam / effects are stale or invalid - run: python tools/wunderstrahl/fx/make_fx.py" }',
      '    & python -B (Join-Path $PSScriptRoot "wunderstrahl/fx/make_fx.py") --selftest',
      '    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl effect validators missed a planted fault (tools/wunderstrahl/fx/make_fx.py --selftest)." }',
      '    & python -B (Join-Path $PSScriptRoot "wunderstrahl/sound/make_sounds.py") --check',
      '    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl sounds are stale - see tools/wunderstrahl/sound/make_sounds.py." }',
      '    & python -B (Join-Path $PSScriptRoot "artgen/packs/ws_wunderstrahl_icons.py") --check',
      '    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl HUD icons are stale or unwired - run: python tools/artgen/packs/ws_wunderstrahl_icons.py --install" }',
      '    & node (Join-Path $PSScriptRoot "wunderstrahl/test_wunderstrahl.js")',
      '    if ($LASTEXITCODE -ne 0) { Die "The Wunderstrahl contract failed (shared slot / window / damage / lockstep / wiring) - see tools/wunderstrahl/test_wunderstrahl.js." }']),
]


def split_lines(text):
    """[(body, ending)] keeping each line's own ending ('' for a last line without one)."""
    out = []
    for m in re.finditer(r'([^\r\n]*)(\r\n|\n|$)', text):
        if m.group(0) == '' and m.end() >= len(text):
            break
        out.append((m.group(1), m.group(2)))
    return out


def apply(root, dry):
    pending = []
    by_file = {}
    for e in EDITS:
        by_file.setdefault(e[0], []).append(e)
    plans = {}
    for rel, edits in by_file.items():
        p = root / rel
        raw = p.read_bytes()
        bom = raw.startswith(b'\xef\xbb\xbf')
        text = raw[3:].decode('utf-8') if bom else raw.decode('utf-8')
        for (_, marker, op, anchor, payload) in edits:
            if marker in text:
                continue
            pending.append((rel, marker))
            lines = split_lines(text)
            if op == 'sub':
                n = text.count(anchor)
                if n != 1:
                    raise SystemExit('WIRE: %s: the anchor occurs %d times (want 1): %s' % (rel, n, anchor))
                text = text.replace(anchor, payload)
                continue
            if op == 'before_last':
                idx = max(i for i, (b, _) in enumerate(lines) if b.strip())
                eol = lines[idx - 1][1] or '\n'
                ins = [(l, eol) for l in payload]
                lines = lines[:idx] + ins + lines[idx:]
            else:
                rx = re.compile(anchor)
                hits = [i for i, (b, _) in enumerate(lines) if rx.search(b)]
                if len(hits) != 1:
                    raise SystemExit('WIRE: %s: the anchor matches %d lines (want 1): %s' % (rel, len(hits), anchor))
                i = hits[0]
                eol = lines[i][1] or ('\r\n' if '\r\n' in text else '\n')
                ins = [(l, eol) for l in payload]
                if op == 'after':
                    if not lines[i][1]:
                        lines[i] = (lines[i][0], eol)
                    lines = lines[:i + 1] + ins + lines[i + 1:]
                elif op == 'before':
                    lines = lines[:i] + ins + lines[i:]
                else:
                    raise SystemExit('WIRE: unknown op ' + op)
            text = ''.join(b + e for b, e in lines)
        plans[p] = (bom, text)
    if dry:
        return pending
    for p, (bom, text) in plans.items():
        data = text.encode('utf-8')
        if bom:
            data = b'\xef\xbb\xbf' + data
        if data != p.read_bytes():
            p.write_bytes(data)
    return pending


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--root', default=str(ROOT))
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()
    pending = apply(root, dry=True)
    if a.check:
        for rel, marker in pending:
            print('  MISSING %s  (%s)' % (rel, marker))
        print('WIRE %s: %d of %d edits applied' % ('OK' if not pending else 'INCOMPLETE', len(EDITS) - len(pending), len(EDITS)))
        return 1 if pending else 0
    apply(root, dry=False)
    left = apply(root, dry=True)
    for rel, marker in pending:
        print('  wired %s  (%s)' % (rel, marker))
    if left:
        raise SystemExit('WIRE: %d edit(s) still missing after the pass' % len(left))
    print('WIRE OK: %d edit(s) applied, %d already present' % (len(pending), len(EDITS) - len(pending)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
