"""Wire THE WAR DAMAGE PASS (docs/205) into the shared build files, or check that they are wired.

WHY A SCRIPT (the lucky pass's rule, docs/197): the wiring touches files every session shares - tools/build_map.ps1,
tools/sync_to_modtools.ps1, the zone, the client entry script and the sound zone config. A gate or a zone line that
lands before its assets stops a peer's build, so it all goes in in ONE step, right before our own build, and only
once every war-damage file is in the repo and test_war_damage.js passes on its own.

  python tools/war_damage/wire.py           insert (idempotent; a wired block is REPLACED, so a changed layout
                                            re-wires its model list)
  python tools/war_damage/wire.py --check   exit 1 unless every file is wired and the zone block is current
  python tools/war_damage/wire.py --unwire  take it all back out
TOD_WAR_WIRE_ROOT=<dir> works on a copy (tests and dry runs; never the live files a build may be reading).
"""
import argparse, json, os, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if os.environ.get('TOD_WAR_WIRE_ROOT'):
    ROOT = pathlib.Path(os.environ['TOD_WAR_WIRE_ROOT'])

ZONE_BEGIN, ZONE_END = '// BEGIN THE WAR DAMAGE PASS (docs/205)', '// END THE WAR DAMAGE PASS'
PS_BEGIN, PS_END = '    # BEGIN THE WAR DAMAGE PASS (docs/205)', '    # END THE WAR DAMAGE PASS'
CSC_TAG = '// THE WAR DAMAGE PASS (docs/205)'
SYNC_TAG = 'model_export\\tod_war_damage'
SZC_NAME = '"Name": "tod_war",'


def load(rel):
    raw = (ROOT / rel).read_bytes()
    bom = raw[:3] == b'\xef\xbb\xbf'
    s = raw.decode('utf-8-sig')
    return s, ('\r\n' if '\r\n' in s else '\n'), bom


def save(rel, s, bom):
    (ROOT / rel).write_bytes((b'\xef\xbb\xbf' if bom else b'') + s.encode('utf-8'))


def cut_block(s, begin, end):
    """Remove the whole lines from `begin`'s line through `end`'s line (inclusive)."""
    if begin not in s:
        return s
    i = s.rfind('\n', 0, s.index(begin)) + 1
    j = s.index(end, i)
    j = s.find('\n', j)
    return s[:i] + s[(len(s) if j < 0 else j + 1):]


def after_line(s, anchor, text):
    """Insert `text` (whole lines, already ending in a line break) after the line holding `anchor`."""
    assert s.count(anchor) == 1, 'anchor not unique (%d): %s' % (s.count(anchor), anchor[:90])
    j = s.find('\n', s.index(anchor))
    return s[:j + 1] + text + s[j + 1:]


def zone_lines(zone_without_block):
    layout = json.loads((ROOT / 'art/war_damage/layout.json').read_text())
    have = {l.strip() for l in zone_without_block.splitlines()}
    fx = [f for f in list(layout['fx_map'].values()) + [layout['fire_light']] if 'fx,' + f not in have]
    sky = [l.strip() for l in (ROOT / 'scripts/zm/zm_tod2_cybercity/_tod_war_sky.csc').read_text(encoding='utf-8').splitlines()]
    sky_fx = [l.split('"')[3] for l in sky if l.startswith('#precache( "client_fx"')]
    fx += [f for f in sky_fx if 'fx,' + f not in have and f not in fx]
    conductors = sorted({c['model'] + st for c in layout['conductors'] for st in ('_off', '_on')})
    return [
        ZONE_BEGIN + ': the tower after the war. CLIENT ONLY - _tod_war_damage.csc spawns',
        '// one merged model per break / per five ordinary floors (Treyarch\'s own rubble, slabs, rebar, iron, cables,',
        '// glass and burn / blast / crack decal cards, placed by tools/war_damage/layout.js, merged by build_clusters.py;',
        '// source_data/tod_war_damage.gdt) and plays the effects in a window round each player. XMODEL LINES ONLY: the',
        '// stock materials ride in with the models (a bare model material line failed build 11). The fire-on-rubble',
        '// effects already zoned elsewhere are not repeated here. Phase 2 (docs/205 s7): the torn conduits\' two-state',
        '// conductor models (source_data/tod_war_conductors.gdt), the one-bit power signal (_tod_war_damage.gsc), the',
        '// war in the sky (_tod_war_sky.csc) and the generated tod/war effects (make_fx.py). Wired by tools/war_damage/wire.py.',
        'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_war_damage.gsc',
        'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_war_damage.csc',
        'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_war_damage_data.csc',
        'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_war_sky.csc',
    ] + ['xmodel,' + c['name'] for c in layout['clusters']] + ['xmodel,' + m for m in conductors] + ['fx,' + f for f in fx] + [ZONE_END]


PS_PRE = [
    PS_BEGIN + ': the merged models are fresh against their layout and kit, every effect is real (no stub,',
    '    # no _pcloud), every decal is a plain decal never zoned bare, the zone / entries / sound config / sync are wired,',
    '    # the client effect list is in lockstep with layout.js; phase 2: the torn conduits + conductor twins, the generated',
    '    # effects + sounds are fresh, the power-wave + sign-bearing constants are in lockstep; negative controls',
    '    # (tools/war_damage/test_war_damage.js).',
    '    & node (Join-Path $PSScriptRoot "war_damage/test_war_damage.js")',
    '    if ($LASTEXITCODE -ne 0) { Die "War damage contract failed - see tools/war_damage/test_war_damage.js output (docs/205)." }',
    PS_END,
]
PS_POST = [
    PS_BEGIN + ': both scripts, every effect, every decal material and every merged model with all its triangles;',
    '    # phase 2: the server half, the sky director, the conductor twins with all their triangles, the tod/war effects.',
    "    & node (Join-Path $PSScriptRoot 'war_damage/test_war_damage.js') --ledger $partnerLedger",
    '    if ($LASTEXITCODE -ne 0) { Die "War damage models / effects / scripts are missing or lost triangles in the compiled assets (docs/205)." }',
    PS_END,
]
PS_PRE_ANCHOR = 'Haven (safe zone) contract failed - see tools/haven/test_haven.js output (docs/202)." }'
PS_POST_ANCHOR = 'Haven dome / effects / tint / script / widget are missing from the linker ledger (docs/202)." }'
ZONE_ANCHOR = 'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_perk_lights.csc'   # R5: _tod_hoop.csc left with the Map 1 purge
CSC_ANCHOR = '#using scripts\\zm\\zm_tod2_cybercity\\_tod_jump_title;'
CSC_LINE = ('#using scripts\\zm\\zm_tod2_cybercity\\_tod_war_damage;   ' + CSC_TAG + ': client-only war damage models + effects; one world clientfield (the power) from _tod_war_damage.gsc'
            + '\n' + '#using scripts\\zm\\zm_tod2_cybercity\\_tod_war_sky;      ' + CSC_TAG + ' phase 2: the war in the sky, client-only (far flashes, tracers, a stricken ship)')
GSC_TAG = '// THE WAR DAMAGE PASS (docs/205) phase 2'
GSC_USING_ANCHOR = '#using scripts\\zm\\zm_tod2_cybercity\\_tod_golden_zombie;'
GSC_USING_LINE = '#using scripts\\zm\\zm_tod2_cybercity\\_tod_war_damage;     ' + GSC_TAG + ': the one-bit power signal the war damage clients replay the power wave from'
GSC_INIT_ANCHOR = 'level thread tod_golden_zombie::init();'
GSC_INIT_LINE = '\tlevel thread tod_war_damage::init();   ' + GSC_TAG
SYNC_ANCHOR = 'model_export\\tod_haven") (Join-Path'
SYNC_LINE = ('    Copy-Tree (Join-Path $RepoRoot "model_export\\tod_war_damage") (Join-Path $ModTools "model_export\\tod_war_damage") "THE WAR DAMAGE PASS: the merged rubble / rebar / iron / scorch-decal models + the torn conduits conductor twins (docs/205)" $false'
             + '\n' + '    Copy-Tree (Join-Path $RepoRoot "sound_assets\\tod\\war") (Join-Path $ModTools "sound_assets\\tod\\war") "THE WAR DAMAGE PASS phase 2: the war generated sounds (docs/205 s7)" $false   # model_export\\tod_war_damage: one tag cuts both rows')
SZC_ANCHOR = '"Sources": ['


def szc_entry(nl):
    return nl.join(['        {', '            "Type": "ALIAS",', '            ' + SZC_NAME, '            "Filename": "tod_war.csv",',
                    '            "Specs": []', '        },']) + nl


def cut_szc(s):
    if SZC_NAME not in s:
        return s
    k = s.index(SZC_NAME)
    i = s.rfind('{', 0, k); i = s.rfind('\n', 0, i) + 1
    j = s.index('},', k); j = s.find('\n', j)
    return s[:i] + s[j + 1:]


def cut_line(s, tag):
    """Remove every line carrying `tag` (the client entry and the sync carry two each)."""
    while tag in s:
        i = s.rfind('\n', 0, s.index(tag)) + 1
        j = s.find('\n', i)
        s = s[:i] + s[(len(s) if j < 0 else j + 1):]
    return s


def wire(rel, s, nl):
    if rel == 'tools/build_map.ps1':
        s = cut_block(cut_block(s, PS_BEGIN + ': the merged', PS_END), PS_BEGIN + ': both scripts', PS_END)
        s = after_line(s, PS_PRE_ANCHOR, nl.join(PS_PRE) + nl)
        return after_line(s, PS_POST_ANCHOR, nl.join(PS_POST) + nl)
    if rel == 'zone_source/zm_tod2_cybercity.zone':
        s = cut_block(s, ZONE_BEGIN, ZONE_END)
        return after_line(s, ZONE_ANCHOR, nl.join(zone_lines(s)) + nl)
    if rel == 'scripts/zm/zm_tod2_cybercity.csc':
        return after_line(cut_line(s, CSC_TAG), CSC_ANCHOR, CSC_LINE.replace('\n', nl) + nl)
    if rel == 'scripts/zm/zm_tod2_cybercity.gsc':
        s = cut_line(s, GSC_TAG)
        s = after_line(s, GSC_USING_ANCHOR, GSC_USING_LINE + nl)
        return after_line(s, GSC_INIT_ANCHOR, GSC_INIT_LINE + nl)
    if rel == 'tools/sync_to_modtools.ps1':
        return after_line(cut_line(s, SYNC_TAG), SYNC_ANCHOR, SYNC_LINE.replace('\n', nl) + nl)
    if rel == 'sound/zoneconfig/zm_tod2_cybercity.szc':
        return after_line(cut_szc(s), SZC_ANCHOR, szc_entry(nl))
    raise KeyError(rel)


def unwire(rel, s):
    if rel == 'tools/build_map.ps1':
        return cut_block(cut_block(s, PS_BEGIN + ': the merged', PS_END), PS_BEGIN + ': both scripts', PS_END)
    if rel == 'zone_source/zm_tod2_cybercity.zone':
        return cut_block(s, ZONE_BEGIN, ZONE_END)
    if rel == 'scripts/zm/zm_tod2_cybercity.csc':
        return cut_line(s, CSC_TAG)
    if rel == 'scripts/zm/zm_tod2_cybercity.gsc':
        return cut_line(s, GSC_TAG)
    if rel == 'tools/sync_to_modtools.ps1':
        return cut_line(s, SYNC_TAG)
    return cut_szc(s)


FILES = ['tools/build_map.ps1', 'zone_source/zm_tod2_cybercity.zone', 'scripts/zm/zm_tod2_cybercity.csc',
         'scripts/zm/zm_tod2_cybercity.gsc', 'tools/sync_to_modtools.ps1', 'sound/zoneconfig/zm_tod2_cybercity.szc']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--unwire', action='store_true')
    a = ap.parse_args()
    bad = []
    for rel in FILES:
        s, nl, bom = load(rel)
        if a.check:
            # wired AND current: re-wiring a wired file must change nothing
            if s != wire(rel, s, nl):
                bad.append(rel)
            continue
        t = unwire(rel, s) if a.unwire else wire(rel, s, nl)
        if t != s:
            save(rel, t, bom)
        print(('unwired ' if a.unwire else 'wired ') + rel + ('' if t != s else ' (unchanged)'))
    if a.check:
        for rel in bad:
            print('NOT WIRED / STALE', rel)
        print('WAR DAMAGE WIRING', 'OK' if not bad else 'MISSING')
        sys.exit(1 if bad else 0)
    if not a.unwire:
        json.loads(load('sound/zoneconfig/zm_tod2_cybercity.szc')[0])   # still valid JSON


if __name__ == '__main__':
    main()
