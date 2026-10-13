"""Wire THE HAVENS (docs/202, the safe zones) into the shared build, in ONE step, right before a build.

WHY A SCRIPT (the lucky set's rule, docs/197): the wiring touches files every session shares (the zone, the entry
scripts, the HUD, the sync, build_map.ps1) and a regenerated map. A peer build that syncs a half-wired tree either
fails a gate or links a half feature, so everything lands together, the moment before this session's own build.

  python tools/haven/wire.py           wire it (idempotent: an edit already in place is left alone)
  python tools/haven/wire.py --check   exit 1 unless every edit is in place

ORDER (wire mode):
  1. the module + HUD widget move from art/haven/staged/ into scripts/ and ui/
  2. node tools/gen_tower_map.js (the map + its generated data, with the havens)
  3. the staged GDT -> source_data/tod_haven.gdt
  4. the shared text edits (zone, szc, _tod_main, AetheriumHud, sync, build_map, the consumers that read the
     moved anchors: perk pads, lounge FX, the teddy bears, the hunt filter + its gate's interpreter)
  5. the power-wire inlays re-cut onto the new floors (conduit_layout.js + build_conduit_batches.py)
  6. the Dealer panel's surroundings re-read (dealer_presence/inventory.js); its matched Blender review
     (dealer_presence/preview.py) must be re-rendered next, on an idle machine - this script says so
Then: run the gates, build FULL (a map change bakes).
"""
import argparse, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGED = ROOT / 'art/haven/staged'
S = 'scripts/zm/zm_tod2_cybercity/'


def load(rel):
    raw = (ROOT / rel).read_bytes()
    bom = raw[:3] == b'\xef\xbb\xbf'
    s = raw.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in s else '\n'
    return s, nl, bom


def save(rel, s, bom):
    (ROOT / rel).write_bytes((b'\xef\xbb\xbf' if bom else b'') + s.encode('utf-8'))


def L(nl, *lines):
    return nl.join(lines) + nl


# ---------------------------------------------------------------------------
# the edits: (file, marker proving it is in place, apply(s, nl) -> s)
# ---------------------------------------------------------------------------
def after(anchor_spec, block_fn):
    def apply(s, nl):
        anchor = anchor_spec(nl) if callable(anchor_spec) else anchor_spec
        assert s.count(anchor) == 1, 'anchor not unique / missing: ' + anchor[:90]
        i = s.index(anchor) + len(anchor)
        # land after the anchor's own line end
        if not anchor.endswith(('\n', '\r\n')):
            j = s.index('\n', i) + 1
        else:
            j = i
        return s[:j] + block_fn(nl) + s[j:]
    return apply


def replace(old_fn, new_fn):
    def apply(s, nl):
        old = old_fn(nl)
        assert s.count(old) == 1, 'replace target not unique / missing: ' + old[:90]
        return s.replace(old, new_fn(nl))
    return apply


ZONE_BLOCK = lambda nl: L(nl,
    '// THE HAVENS (docs/202, 2026-10-02): the safe zones on floors 10/20/30/40 - the force-field dome (three',
    '// skins of one generated mesh: tools/haven/make_dome.py), its four effects (tools/haven/make_fx.py), the',
    '// screen tint (i_tod_haven_vignette) and the HUD widget. XMODEL LINES ONLY for the dome (its materials ride',
    '// in through the models; a bare model material line failed build 11).',
    'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_haven.gsc',
    'xmodel,tod_haven_dome',
    'xmodel,tod_haven_dome_pulse',
    'xmodel,tod_haven_dome_flash',
    'fx,tod/haven/fx_tod_haven_ambient',
    'fx,tod/haven/fx_tod_haven_cross',
    'fx,tod/haven/fx_tod_haven_push',
    'fx,tod/haven/fx_tod_haven_boot',
    'image,i_tod_haven_vignette',
    'rawfile,ui/uieditor/widgets/HUD/AetheriumWidgets/TodHaven.lua   // the safe zones\' screen tint (docs/202; AetheriumHud pcall-requires it)')

SZC_BLOCK = lambda nl: L(nl,
    '        {',
    '            "Type": "ALIAS",',
    '            "Name": "tod_haven",',
    '            "Filename": "tod_haven.csv",',
    '            "Specs": []',
    '        },')

HUD_MOUNT = lambda nl: L(nl,
    '',
    '	-- THE HAVENS\' SCREEN EFFECT (docs/202): the safe zones\' field tinting the screen\'s',
    '	-- edges while you stand inside one, a flash as you cross, a flicker when a hit is',
    '	-- cut. FIRST child, so every readout draws over it; hidden with the rest of the HUD',
    '	-- (TodHudApply). pcall\'d like every optional require: no rawfile = no tint, never an error.',
    '	pcall( require, "ui.uieditor.widgets.HUD.AetheriumWidgets.TodHaven" )',
    '	if CoD.TodHaven then',
    '		self.TodHaven = CoD.TodHaven.new( self, controller )',
    '		self:addElement( self.TodHaven )',
    '	end')

PRE_GATES = lambda nl: L(nl,
    '    # THE HAVENS (docs/202): the safe zones. The dome model, its effects and sounds are GENERATED (tools/haven/*);',
    '    # the gate runs the SHIPPING _tod_haven.gsc through gsc_eval (membership + hysteresis, the 33% damage cut and',
    '    # its tell, the crossing flow, the 33% slow on and off), checks every lockstep and wiring, and 10 mutants.',
    '    & python -B (Join-Path $PSScriptRoot "haven/make_dome.py") --check',
    '    if ($LASTEXITCODE -ne 0) { Die "Haven dome model / texture / GDT are stale - run: python tools/haven/make_dome.py (docs/202)." }',
    '    & python -B (Join-Path $PSScriptRoot "haven/make_fx.py") --check',
    '    if ($LASTEXITCODE -ne 0) { Die "Haven effects are stale or invalid - run: python tools/haven/make_fx.py (docs/202)." }',
    '    & python -B (Join-Path $PSScriptRoot "haven/make_sounds.py") --check',
    '    if ($LASTEXITCODE -ne 0) { Die "Haven sounds are stale - run: python tools/haven/make_sounds.py (docs/202)." }',
    '    & node (Join-Path $PSScriptRoot "haven/test_haven.js")',
    '    if ($LASTEXITCODE -ne 0) { Die "Haven (safe zone) contract failed - see tools/haven/test_haven.js output (docs/202)." }')

POST_GATES = lambda nl: L(nl,
    "    & node (Join-Path $PSScriptRoot 'haven/test_haven.js') --ledger $partnerLedger",
    '    if ($LASTEXITCODE -ne 0) { Die "Haven dome / effects / tint / script / widget are missing from the linker ledger (docs/202)." }')

SYNC_ROW = lambda nl: L(nl,
    '    Copy-Tree (Join-Path $RepoRoot "model_export\\tod_haven") (Join-Path $ModTools "model_export\\tod_haven") "THE HAVENS: the safe zones\' force-field dome + field + screen tint images (docs/202)" $false')

PERK_OLD = lambda nl: L(nl,
    '	// v9.37: the breathers grew (gen_tower_map.js BR_DEPTH 576 / BR_EAST 384 \u2014',
    '	// floor x[-800,-256] y[-992,-416]); the pads keep backing the far S rail',
    '	// (y = -(PX+BR_DEPTH) + 33 = -959, was -783). x unchanged.',
    '	pads[ pads.size ] = make_pad( "floor 10 breather (east)",  ( -360, -970,  3648 ), 90,      ( 0,  1, 0 ), undefined, false );',
    '	pads[ pads.size ] = make_pad( "floor 10 breather (west)",  ( -536, -970,  3648 ), 90,      ( 0,  1, 0 ), undefined, false );',
    '	pads[ pads.size ] = make_pad( "floor 20 breather (east)",  ( -360, -970,  7488 ), 90,      ( 0,  1, 0 ), undefined, false );',
    '	pads[ pads.size ] = make_pad( "floor 20 breather (west)",  ( -536, -970,  7488 ), 90,      ( 0,  1, 0 ), undefined, false );',
    '	pads[ pads.size ] = make_pad( "floor 30 breather (east)",  ( -360, -970, 11328 ), 90,      ( 0,  1, 0 ), undefined, false );',
    '	pads[ pads.size ] = make_pad( "floor 30 breather (west)",  ( -536, -970, 11328 ), 90,      ( 0,  1, 0 ), undefined, false );',
    '	pads[ pads.size ] = make_pad( "floor 40 breather (east)",  ( -360, -970, 15168 ), 90,      ( 0,  1, 0 ), undefined, false );',
    '	pads[ pads.size ] = make_pad( "floor 40 breather (west)",  ( -536, -970, 15168 ), 90,      ( 0,  1, 0 ), undefined, false );')

PERK_NEW = lambda nl: L(nl,
    '	// THE HAVENS (docs/202): each rest stop\'s two perk pads stand inside its safe-zone',
    '	// field, backs to the dome, facing its centre - GENERATED from tools/haven_layout.js',
    '	// (the same file that cuts the dome), so the pads and the field can never drift.',
    '	// yaw = the facing angle for these t10 machines (the play-tested Quick Revive pad:',
    '	// yaw 269.999, front ( 0, -1, 0 )).',
    '	zs = tod_breather_data::breather_zs();',
    '	for ( i = 0; i < zs.size; i++ )',
    '	{',
    '		fl = 1 + int( zs[ i ] / 384 );',
    '		pads[ pads.size ] = make_pad( "floor " + fl + " safe zone (south)", tod_breather_data::haven_perk_org( 0, zs[ i ] ), tod_breather_data::haven_perk_yaw( 0 ), tod_breather_data::haven_perk_front( 0 ), undefined, false );',
    '		pads[ pads.size ] = make_pad( "floor " + fl + " safe zone (north)", tod_breather_data::haven_perk_org( 1, zs[ i ] ), tod_breather_data::haven_perk_yaw( 1 ), tod_breather_data::haven_perk_front( 1 ), undefined, false );',
    '	}')

ATMO_OLD = lambda nl: L(nl,
    '		// Room centre (-528,-704): the motes fall from just under the cap',
    '		// band (z+260 of a 296 wall), the haze sits at chest height. The pad',
    '		// point is the porter\'s own anchor; the vent sits at the foot of the',
    '		// gate\'s east post (even frame x[-804,-784] y[-1060,-1012]).',
    '		lounge_fx_at( "tod_lounge_motes", ( -528, -704, z + 260 ) );',
    '		lounge_fx_at( "tod_lounge_haze", ( -528, -704, z + 100 ) );',
    '		pad = tod_breather_data::tp_pad_org( z );',
    '		lounge_fx_at( "tod_lounge_fog",   ( pad[ 0 ], pad[ 1 ], z + 4 ) );',
    '		lounge_fx_at( "tod_lounge_vent",  ( -794, -1036, z + 8 ) );')

ATMO_NEW = lambda nl: L(nl,
    '		// THE HAVENS (docs/202): the rest stop is a safe-zone dome now, and the',
    '		// field\'s own looping effect (_tod_haven) is the life inside it. The',
    '		// stock loops keep the approach: motes falling through the open',
    '		// threshold, fog curling over the teleporter pad, a soft vent beside the',
    '		// threshold\'s south-east gate post. Anchors GENERATED (haven_layout.js).',
    '		lounge_fx_at( "tod_lounge_motes", tod_breather_data::haven_motes_org( z ) );',
    '		pad = tod_breather_data::tp_pad_org( z );',
    '		lounge_fx_at( "tod_lounge_fog",   ( pad[ 0 ], pad[ 1 ], z + 4 ) );',
    '		lounge_fx_at( "tod_lounge_vent",  tod_breather_data::haven_vent_org( z ) );')

SECRET_OLD = lambda nl: L(nl,
    '	// #1 FLOOR 10 (user: "against a wall standing on the floor"): on the lounge',
    '	// floor, back to the outer long wall\'s sill (inner face x=-800, the even',
    '	// frame\'s mirror of \'wall E\'), in the north bay (y between mullion b at',
    '	// -814 and the N wall at -992), facing EAST into the room.',
    '	spots[ 1 ] = spot( ( -800 + TOD_SECRET_HALF_DEPTH, -900, zs[ 0 ] + TOD_SECRET_LIFT ), ( 0, 90, 0 ), "floor 10 lounge floor" );',
    '	// #2 FLOOR 20: standing on the second gantry hoop\'s lintel (top = floor +',
    '	// 240), facing the room (+Y).',
    '	spots[ 2 ] = spot( ( -704, -1222, zs[ 1 ] + TOD_SECRET_HOOP_TOP + TOD_SECRET_LIFT ), ( 0, 180, 0 ), "floor 20 spur hoop" );')

SECRET_NEW = lambda nl: L(nl,
    '	// #1 FLOOR 10 + #2 FLOOR 20 - THE HAVENS (docs/202) rebuilt the rest stops,',
    '	// so both bears ride GENERATED anchors (tools/haven_layout.js BEARS; the lift',
    '	// and the 6u wall standoff are already in them): floor 10 on the teleporter',
    '	// pad\'s platform, back to its east rail, facing west; floor 20 standing on',
    '	// the spur gate\'s lintel (240 up), facing the landing.',
    '	spots[ 1 ] = spot( tod_breather_data::secret_bear_org( 1, zs[ 0 ] ), ( 0, tod_breather_data::secret_bear_yaw( 1 ), 0 ), "floor 10 haven pad" );',
    '	spots[ 2 ] = spot( tod_breather_data::secret_bear_org( 2, zs[ 1 ] ), ( 0, tod_breather_data::secret_bear_yaw( 2 ), 0 ), "floor 20 haven spur gate" );')

STRAY_ANCHOR = lambda nl: L(nl, '	if ( too_close( org ) )', '		return false;')
STRAY_HOOK = lambda nl: L(nl,
    '	// THE HAVENS (docs/202): never raise a zombie INSIDE a safe-zone field \u2014 the',
    '	// horde has to walk in through it (and its slow). Guarded pointer: the haven',
    '	// module owns the field and is never imported here.',
    '	if ( isdefined( level.tod_haven_inside_fn ) && [[ level.tod_haven_inside_fn ]]( org ) )',
    '		return false;')


def edits():
    return [
        ('zone_source/zm_tod2_cybercity.zone', 'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_haven.gsc',
         after('rawfile,ui/uieditor/widgets/HUD/AetheriumWidgets/TodJumpCine.lua', ZONE_BLOCK)),
        ('sound/zoneconfig/zm_tod2_cybercity.szc', '"Filename": "tod_haven.csv"',
         after('    "Sources": [', SZC_BLOCK)),
        (S + '_tod_main.gsc', '#using scripts\\zm\\zm_tod2_cybercity\\_tod_haven;',
         after('#using scripts\\zm\\zm_tod2_cybercity\\_tod_arena;', lambda nl: L(nl,
             '#using scripts\\zm\\zm_tod2_cybercity\\_tod_haven;   // THE HAVENS (docs/202): the safe zones\' force-field domes (33% slower enemies, 33% less damage)'))),
        (S + '_tod_main.gsc', '\ttod_haven::init();',
         after('\ttod_arena::init();', lambda nl: L(nl,
             '\ttod_haven::init();         // docs/202: the safe zones (the domes boot with the power wave)'))),
        ('ui/uieditor/menus/HUD/AetheriumHud.lua', 'self.TodHaven = CoD.TodHaven.new( self, controller )',
         after('\tself.anyChildUsesUpdateState = true', HUD_MOUNT)),
        ('ui/uieditor/menus/HUD/AetheriumHud.lua', 'self.AetheriumRoundCounter, self.TodHaven }',
         replace(lambda nl: 'self.AetheriumRoundCounter }', lambda nl: 'self.AetheriumRoundCounter, self.TodHaven }')),
        ('tools/sync_to_modtools.ps1', 'model_export\\tod_haven"',
         after('Copy-Tree (Join-Path $RepoRoot "model_export\\tod_dealer")', SYNC_ROW)),
        ('tools/build_map.ps1', 'haven/test_haven.js")',
         after('if ($LASTEXITCODE -ne 0) { Die "Lucky sources contract failed - see tools/lucky/test_lucky.js output (docs/197)." }', PRE_GATES)),
        ('tools/build_map.ps1', "'tools/test_haven_hud.lua'",
         replace(lambda nl: "'tools/test_class_terminal_ui.lua' 2>&1", lambda nl: "'tools/test_class_terminal_ui.lua' 'tools/test_haven_hud.lua' 2>&1")),
        ('tools/build_map.ps1', "haven/test_haven.js') --ledger",
         after('if ($LASTEXITCODE -ne 0) { Die "Lucky models or effects are missing from the linker ledger (docs/197)." }', POST_GATES)),
        (S + '_tod_perk_scatter.gsc', 'tod_breather_data::haven_perk_org( 0, zs[ i ] )', replace(PERK_OLD, PERK_NEW)),
        (S + '_tod_atmosphere.gsc', 'tod_breather_data::haven_motes_org( z )', replace(ATMO_OLD, ATMO_NEW)),
        (S + '_tod_secret.gsc', 'tod_breather_data::secret_bear_org( 1, zs[ 0 ] )', replace(SECRET_OLD, SECRET_NEW)),
        (S + '_tod_stray.gsc', '[[ level.tod_haven_inside_fn ]]( org )', after(STRAY_ANCHOR, STRAY_HOOK)),
        ('tools/test_pursuit.js', 'haven_inside_stub',
         replace(lambda nl: "          .replace(/(\\w+) laststand::player_is_in_laststand\\(\\)/g, 'laststand_of( $1 )');",
                 lambda nl: "          .replace(/(\\w+) laststand::player_is_in_laststand\\(\\)/g, 'laststand_of( $1 )')" + nl +
                            "          .replace(/\\[\\[ level\\.tod_haven_inside_fn \\]\\]\\( org \\)/g, 'haven_inside_stub( org )');   // docs/202: the haven filter's pointer call")),
        # the marker is the builtin's KEY, not its body: the pursuit session (-92, its owner) later made the stub
        # answer from env.havenAt to prove the guard refuses a spot inside a field; any registration counts as wired.
        ('tools/test_pursuit.js', 'haven_inside_stub:',
         after("      'tod_door_data::get_drop_info': lap => drops.get(lap),", lambda nl: L(nl,
             "      haven_inside_stub: () => false,   // docs/202: no haven field holds these test points"))),
        ('tools/test_ui_lifetimes.lua', "'AetheriumPowerupNotification','TodHaven'}",
         replace(lambda nl: "'AetheriumPowerupNotification'}", lambda nl: "'AetheriumPowerupNotification','TodHaven'}")),
        ('tools/test_ui_lifetimes.lua', 'HUD owner lifetimes passed: 160 widget lifetimes',
         replace(lambda nl: 'HUD owner lifetimes passed: 140 widget lifetimes', lambda nl: 'HUD owner lifetimes passed: 160 widget lifetimes')),
    ]


def check_only():
    bad = []
    for rel, marker, _ in edits():
        s, nl, bom = load(rel)
        if marker not in s:
            bad.append(f'{rel}: missing {marker!r}')
    for rel in (S + '_tod_haven.gsc', 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodHaven.lua', 'source_data/tod_haven.gdt'):
        if not (ROOT / rel).exists():
            bad.append(f'{rel}: missing')
    data = (ROOT / (S + '_tod_breather_data.gsc')).read_text(encoding='utf-8')
    if 'function haven_center(' not in data:
        bad.append('the generated breather data has no haven functions (run node tools/gen_tower_map.js)')
    for b in bad:
        print('NOT WIRED', b)
    print('HAVEN WIRE --check:', 'OK' if not bad else f'{len(bad)} missing')
    return 1 if bad else 0


def run(cmd):
    print('>>', ' '.join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def wire():
    # 1. the module + the widget leave the staging folder
    for name, dest in (('_tod_haven.gsc', S + '_tod_haven.gsc'), ('TodHaven.lua', 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodHaven.lua')):
        src, dst = STAGED / name, ROOT / dest
        if src.exists() and not dst.exists():
            shutil.move(str(src), str(dst)); print('moved', name, '->', dest)
        assert dst.exists(), dest
    # 2. the map + generated data
    run(['node', 'tools/gen_tower_map.js'])
    # 3. the GDT
    shutil.copyfile(ROOT / 'art/haven/tod_haven.gdt', ROOT / 'source_data/tod_haven.gdt'); print('copied art/haven/tod_haven.gdt -> source_data/')
    # 4. the text edits
    for rel, marker, apply in edits():
        s, nl, bom = load(rel)
        if marker in s:
            print('already wired:', rel, '|', marker[:60]); continue
        s2 = apply(s, nl)
        assert marker in s2, f'{rel}: the edit did not produce its marker'
        save(rel, s2, bom); print('wired:', rel, '|', marker[:60])
    # 5. the power-wire inlays on the new floors
    run(['node', 'tools/art_cohesion/conduit_layout.js'])
    run([sys.executable, '-B', 'tools/art_cohesion/build_conduit_batches.py'])
    # 6. the Dealer panel's surroundings
    run(['node', 'tools/dealer_presence/inventory.js'])
    print('NEXT: re-render the Dealer panel\'s matched review on an idle machine:')
    print('  "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe" --background --factory-startup --python tools/dealer_presence/preview.py')
    print('then run the gates and build FULL.')
    return check_only()


def dry():
    """Apply every text edit IN MEMORY and report: proves each anchor matches exactly, writes nothing."""
    bad = 0
    for rel, marker, apply in edits():
        s, nl, bom = load(rel)
        if marker in s:
            print('already wired:', rel, '|', marker[:60]); continue
        try:
            s2 = apply(s, nl)
            ok = marker in s2
            print(('ok   ' if ok else 'FAIL ') + rel + ' | ' + marker[:60]); bad += 0 if ok else 1
        except AssertionError as e:
            print('FAIL ' + rel + ' | ' + str(e)); bad += 1
    print('HAVEN WIRE --dry:', 'OK' if not bad else f'{bad} edit(s) would fail')
    return 1 if bad else 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--check', action='store_true'); ap.add_argument('--dry', action='store_true'); a = ap.parse_args()
    sys.exit(check_only() if a.check else dry() if a.dry else wire())
