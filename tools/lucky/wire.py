"""Wire THE LUCKY SOURCES (docs/197) into the shared build files, or check that they are wired.

WHY A SCRIPT: the wiring touches four files every session shares (tools/build_map.ps1, the zone, both entry scripts).
On 2026-09-29 a peer's full build started 18 seconds after the lucky build checks landed in build_map.ps1, while the
effects and sounds were still being generated, and it stopped at them (docs/197's build note). The rule since: wire LAST,
in one step, right before a build, only when every lucky asset exists and every lucky check passes on its own.

  python tools/lucky/wire.py           insert the wiring (idempotent: a file already wired is left alone)
  python tools/lucky/wire.py --check   exit 1 unless all four files are wired
  python tools/lucky/wire.py --unwire  take it back out (the 2026-09-29 incident's undo)
"""
import argparse, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if os.environ.get('TOD_LUCKY_WIRE_ROOT'):   # tests only: work on copies, never the live files a build may be reading
    ROOT = pathlib.Path(os.environ['TOD_LUCKY_WIRE_ROOT'])


def load(rel):
    raw = (ROOT / rel).read_bytes()
    bom = raw[:3] == b'\xef\xbb\xbf'
    s = raw.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in s else '\n'
    return s, nl, bom


def save(rel, s, bom):
    (ROOT / rel).write_bytes((b'\xef\xbb\xbf' if bom else b'') + s.encode('utf-8'))


def insert_after(s, anchor, lines, nl):
    assert s.count(anchor) == 1, 'anchor not unique: ' + anchor[:80]
    i = s.index(anchor) + len(anchor)
    return s[:i] + nl.join(lines) + nl + s[i:]


def cut(s, start, end_incl):
    i = s.index(start)
    j = s.index(end_incl, i) + len(end_incl)
    if s[j:j + 2] == '\r\n': j += 2
    elif s[j:j + 1] == '\n': j += 1
    return s[:i] + s[j:]


PRE_GATES = [
    '    # THE LUCKY SOURCES (docs/197): the Lucky Clover drop, the Lucky Meteor and the Golden Zombie. Their models,',
    "    # effects and sounds are GENERATED (tools/lucky/*); the scripts' contracts (the user's numbers, the view-ray and",
    '    # flight math run through gsc_eval, every lockstep, the negative controls) are re-proved on every build.',
    '    & python -B (Join-Path $PSScriptRoot "lucky/verify_native.py")',
    '    if ($LASTEXITCODE -ne 0) { Die "Lucky models failed validation - see tools/lucky/verify_native.py output (docs/197)." }',
    '    & python -B (Join-Path $PSScriptRoot "lucky/make_golden.py") --check',
    '    if ($LASTEXITCODE -ne 0) { Die "Golden Zombie models are stale - run: python tools/lucky/make_golden.py (docs/197)." }',
    '    & python -B (Join-Path $PSScriptRoot "lucky/make_fx.py") --check',
    '    if ($LASTEXITCODE -ne 0) { Die "Lucky effects are stale or invalid - run: python tools/lucky/make_fx.py (docs/197)." }',
    '    & python -B (Join-Path $PSScriptRoot "lucky/make_sounds.py") --check',
    '    if ($LASTEXITCODE -ne 0) { Die "Lucky sounds are stale - run: python tools/lucky/make_sounds.py (docs/197)." }',
    '    & node (Join-Path $PSScriptRoot "lucky/test_lucky.js")',
    '    if ($LASTEXITCODE -ne 0) { Die "Lucky sources contract failed - see tools/lucky/test_lucky.js output (docs/197)." }',
]
POST_GATES = [
    "    & python -B (Join-Path $PSScriptRoot 'lucky/verify_native.py') --compiled-ledger $cyberLedger",
    '    if ($LASTEXITCODE -ne 0) { Die "Lucky models / effects / materials are missing or lost geometry in the compiled assets (docs/197)." }',
    "    & node (Join-Path $PSScriptRoot 'lucky/test_lucky.js') --ledger $partnerLedger",
    '    if ($LASTEXITCODE -ne 0) { Die "Lucky models or effects are missing from the linker ledger (docs/197)." }',
]
ZONE = [
    '// THE LUCKY SOURCES (docs/197, 2026-09-29): the Lucky Clover drop (in the drops\' own stock material), the Lucky',
    '// Meteor (a real server target in the sky) and the Golden Zombie (the horde\'s mesh in gold twins). Models from',
    '// tools/lucky/01_author.py (Blender MCP) + tools/lucky/make_golden.py; effects from tools/lucky/make_fx.py. XMODEL',
    '// LINES ONLY: their materials ride in as mc/<name> (a bare material, line for a model material failed build 11).',
    'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_lucky.gsc',
    'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_lucky.csc',
    'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_golden_zombie.gsc',
    'xmodel,tod_luck_clover',
    'xmodel,tod_luck_meteor',
    'xmodel,tod_golden_zombie_body',
    'xmodel,tod_golden_zombie_head',
    'fx,tod/luck/fx_luck_meteor_trail',
    'fx,tod/luck/fx_luck_meteor_burst',
    'fx,tod/luck/fx_luck_meteor_frag',
    'fx,tod/luck/fx_luck_clover_trail',
    'fx,tod/luck/fx_luck_clover_land',
    'fx,tod/luck/fx_luck_golden_aura',
    'fx,tod/luck/fx_luck_golden_burst',
]
ENTRY_USING = [
    '#using scripts\\zm\\zm_tod2_cybercity\\_tod_lucky;          // THE LUCKY CLOVER drop + THE LUCKY METEOR (docs/197)',
    '#using scripts\\zm\\zm_tod2_cybercity\\_tod_golden_zombie;  // THE GOLDEN ZOMBIE (docs/197)',
]
ENTRY_INIT = [
    '',
    '\t// THE LUCKY SOURCES (docs/197, 2026-09-29): the Lucky Meteor\'s director + the shot watchers (the Lucky',
    '\t// Clover power-up registers itself in _tod_lucky\'s REGISTER_SYSTEM), and the Golden Zombie\'s 1% spawn roll.',
    '\tlevel thread tod_lucky::init();',
    '\tlevel thread tod_golden_zombie::init();',
]
CSC_USING = ['#using scripts\\zm\\zm_tod2_cybercity\\_tod_lucky;   // THE LUCKY CLOVER\'s client half: include + add (docs/197)']

FILES = {
    'tools/build_map.ps1': [
        ('    if ($LASTEXITCODE -ne 0) { Die "First-jump crash scene contract failed (beats / framing / sky clearance / wiring) - see test_jump_title.js output (docs/196)." }', PRE_GATES,
         ('    # THE LUCKY SOURCES (docs/197)', 'see tools/lucky/test_lucky.js output (docs/197)." }')),
        ('    if ($LASTEXITCODE -ne 0) { Die "First-jump crash effects or its client script are missing from the fastfile (docs/196)." }', POST_GATES,
         ("    & python -B (Join-Path $PSScriptRoot 'lucky/verify_native.py') --compiled-ledger", 'missing from the linker ledger (docs/197)." }')),
    ],
    'zone_source/zm_tod2_cybercity.zone': [
        ('scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_powerups.csc', ZONE,
         ('// THE LUCKY SOURCES (docs/197, 2026-09-29)', 'fx,tod/luck/fx_luck_golden_burst')),
    ],
    'scripts/zm/zm_tod2_cybercity.gsc': [
        ('#using scripts\\zm\\zm_tod2_cybercity\\_tod_luck;', ENTRY_USING,
         ('#using scripts\\zm\\zm_tod2_cybercity\\_tod_lucky;', '// THE GOLDEN ZOMBIE (docs/197)')),
        ('\tlevel thread tod_luck::init();', ENTRY_INIT,
         ("\t// THE LUCKY SOURCES (docs/197, 2026-09-29)", 'level thread tod_golden_zombie::init();')),
    ],
    'scripts/zm/zm_tod2_cybercity.csc': [
        ('#using scripts\\zm\\zm_tod2_cybercity\\_tod_powerups;', CSC_USING,
         ('#using scripts\\zm\\zm_tod2_cybercity\\_tod_lucky;', 'include + add (docs/197)')),
    ],
}


def wired(rel):
    s, _, _ = load(rel)
    return all(block[0] in s for _, _, block in FILES[rel])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--check', action='store_true'); ap.add_argument('--unwire', action='store_true')
    a = ap.parse_args()
    if a.check:
        bad = [rel for rel in FILES if not wired(rel)]
        for rel in bad: print('NOT WIRED', rel)
        print('LUCKY WIRING', 'OK' if not bad else 'MISSING'); sys.exit(1 if bad else 0)
    for rel, edits in FILES.items():
        s, nl, bom = load(rel)
        for anchor, lines, (start, end) in edits:
            if a.unwire:
                if start in s: s = cut(s, start, end)
            elif start not in s:
                assert s.count(anchor) == 1, rel + ': anchor not unique: ' + anchor[:80]
                i = s.index(anchor) + len(anchor)
                if lines[0] == '':
                    # the block continues from the anchor's own line end (it starts with a line break)
                    s = s[:i] + nl.join(lines) + s[i:]
                else:
                    # a block of whole lines after the anchor's line
                    j = i + (2 if s[i:i + 2] == '\r\n' else 1)
                    s = s[:j] + nl.join(lines) + nl + s[j:]
        save(rel, s, bom)
        print(('unwired ' if a.unwire else 'wired ') + rel)


if __name__ == '__main__':
    main()
