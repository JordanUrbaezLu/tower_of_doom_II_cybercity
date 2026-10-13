#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# tools/cyber_teddy/verify.py - THE CYBER TEDDY GATE (TOD II, docs/208).
#
# The song hunt's three bears (_tod_secret.gsc) wear a fan's CYBER TEDDY,
# `tod_cyber_teddy`, ported from map 1 as its BUILT outputs (map 1's
# tools/cyber_teddy/build_cyber_teddy.py makes them in Blender from the fan's
# FBX; this map ships the result byte for byte, pinned by
# art/cyber_teddy/manifest.json - map 1's own manifest, copied whole).
#
#   --check   (every build, pre-link) every shipped file == the manifest (sha256),
#             the source FBX == its md5, the size numbers are ONE chain: the GSC's
#             TOD_SECRET_LIFT / _HALF_DEPTH, tools/haven_layout.js BEAR_LIFT /
#             BEAR_HALF / BEAR_EXT and the GENERATED haven bear anchors all equal
#             the manifest's lift / half_depth / bounds; the model is precached,
#             zoned and synced and the stock bear is retired whole; the melee lane
#             is wired.
#   --compiled-ledger <map>_xmodel.csv [--linker-log <transcript>]   (post-link)
#             the model compiled with its one LOD and exactly map 1's triangle
#             count (the same binary: 9,919), its material COMPLETE (a ledger row
#             that is only its name = an EMPTY material = flat gray, the jump pad's
#             2026-10-03 lesson), both images packed, and no linker usage /
#             techset complaint naming one of them.
# Never hand-edit the shipped files: rebuild in map 1's tool (pointed at THIS
# tree and the private tools root) and copy its manifest with them.
# -----------------------------------------------------------------------------
import csv
import hashlib
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
MAN = REPO / 'art' / 'cyber_teddy' / 'manifest.json'
MODEL, MATERIAL = 'tod_cyber_teddy', 'mtl_tod_cyber_teddy'
IMAGES = ('i_tod_cyber_teddy_c', 'i_tod_cyber_teddy_e')
SECRET = REPO / 'scripts' / 'zm' / 'zm_tod2_cybercity' / '_tod_secret.gsc'
DATA = REPO / 'scripts' / 'zm' / 'zm_tod2_cybercity' / '_tod_breather_data.gsc'
HAVEN = REPO / 'tools' / 'haven_layout.js'
LINKER_COMPLAINTS = ('mismatched usage', "doesn't expose", 'no techset')
EMPTY_MATERIAL_SLACK = 64        # install_de_jumppad.py's measure: an empty row is len(name) + 2


def h(p, algo):
    return hashlib.new(algo, p.read_bytes()).hexdigest()


def define(text, name):
    m = re.search(r'^#define\s+' + name + r'\s+("?)([^"\s]+)\1', text, re.M)
    return None if m is None else m.group(2)


def js_const(text, name):
    m = re.search(r'\b' + name + r'\s*=\s*(\[[^\]]*\]|-?[\d.]+)', text)
    return None if m is None else json.loads(m.group(1))


def close(a, b):
    return a is not None and b is not None and abs(float(a) - float(b)) < 1e-6


def check():
    man = json.loads(MAN.read_text(encoding='utf-8'))
    bad = []
    for rel, want in man['files'].items():
        p = REPO / rel
        if not p.exists():
            bad.append('missing ' + rel)
        elif h(p, 'sha256') != want:
            bad.append('changed since the manifest: ' + rel + ' (rebuild in the tool; never hand-edit)')
    src = REPO / man['source']
    if not src.exists():
        bad.append('missing the source FBX ' + man['source'])
    elif h(src, 'md5') != man['source_md5']:
        bad.append('the source FBX is not the one the binary was built from: ' + man['source'])
    lift, half = man['lift'], man['half_depth']
    ext = [man['bounds'][1][0], man['bounds'][1][1]]
    if half < man['bounds'][1][1]:
        bad.append('the manifest half_depth %s is less than the back extent %s: the bear would sink into its wall' % (half, man['bounds'][1][1]))
    # the GSC: the model, the revision, the size chain, the melee lane
    s = SECRET.read_text(encoding='utf-8')
    if define(s, 'TOD_SECRET_MODEL') != MODEL:
        bad.append('_tod_secret.gsc TOD_SECRET_MODEL is %s, not %s' % (define(s, 'TOD_SECRET_MODEL'), MODEL))
    if define(s, 'TOD_SECRET_REVISION') != man['revision']:
        bad.append('_tod_secret.gsc TOD_SECRET_REVISION != the manifest revision %s' % man['revision'])
    if not close(define(s, 'TOD_SECRET_LIFT'), lift) or not close(define(s, 'TOD_SECRET_HALF_DEPTH'), half):
        bad.append('_tod_secret.gsc LIFT / HALF_DEPTH (%s / %s) != the manifest (%s / %s)'
                   % (define(s, 'TOD_SECRET_LIFT'), define(s, 'TOD_SECRET_HALF_DEPTH'), lift, half))
    if '#precache( "model", "%s" );' % MODEL not in s:
        bad.append('_tod_secret.gsc does not precache ' + MODEL)
    if 'p7_zm_teddybear' in re.sub(r'//[^\n]*', '', s):
        bad.append('_tod_secret.gsc still names the stock p7_zm_teddybear outside a comment')
    if define(s, 'TOD_SECRET_MELEE_REACH') is None or 'self thread melee_watch( note );' not in s or 'function melee_hits_bear()' not in s:
        bad.append('_tod_secret.gsc: the melee lane (TOD_SECRET_MELEE_REACH, melee_watch, melee_hits_bear) is not wired')
    # the haven layout + its GENERATED anchors
    hv = HAVEN.read_text(encoding='utf-8')
    if not close(js_const(hv, 'BEAR_LIFT'), lift) or not close(js_const(hv, 'BEAR_HALF'), half):
        bad.append('tools/haven_layout.js BEAR_LIFT / BEAR_HALF (%s / %s) != the manifest (%s / %s)'
                   % (js_const(hv, 'BEAR_LIFT'), js_const(hv, 'BEAR_HALF'), lift, half))
    be = js_const(hv, 'BEAR_EXT')
    if not (isinstance(be, list) and len(be) == 2 and close(be[0], ext[0]) and close(be[1], ext[1])):
        bad.append('tools/haven_layout.js BEAR_EXT %s != the manifest half extents %s' % (be, ext))
    d = DATA.read_text(encoding='utf-8')
    m = re.search(r'function secret_bear_org\( i, z \) \{ if \( i == 1 \) return \( (-?[\d.]+), (-?[\d.]+), z \+ ([\d.]+) \); return \( (-?[\d.]+), (-?[\d.]+), z \+ ([\d.]+) \); \}', d)
    if m is None:
        bad.append('_tod_breather_data.gsc has no generated secret_bear_org')
    elif not close(m.group(3), lift) or not close(m.group(6), lift):
        bad.append('the generated haven bear anchors carry lift %s / %s, not %s: re-run node tools/gen_tower_map.js' % (m.group(3), m.group(6), lift))
    # zone / sync
    zone = (REPO / 'zone_source' / 'zm_tod2_cybercity.zone').read_text(encoding='utf-8')
    if not re.search(r'^xmodel,' + MODEL + r'\s*$', zone, re.M):
        bad.append('the zone does not carry xmodel,' + MODEL)
    if re.search(r'^xmodel,p7_zm_teddybear\s*$', zone, re.M):
        bad.append('the zone still carries the retired xmodel,p7_zm_teddybear')
    sync = (REPO / 'tools' / 'sync_to_modtools.ps1').read_text(encoding='utf-8')
    if 'model_export\\tod_cyber_teddy' not in sync:
        bad.append('tools/sync_to_modtools.ps1 does not copy model_export\\tod_cyber_teddy')
    gdt = (REPO / 'source_data' / 'tod_cyber_teddy.gdt').read_text(encoding='utf-8') if (REPO / 'source_data' / 'tod_cyber_teddy.gdt').exists() else ''
    for need, why in (('"%s" ( "xmodel.gdf" )' % MODEL, 'the model block'),
                      ('"BulletCollisionLOD" "None"', 'no bullet collision (the hunt hits by view ray and melee reach)'),
                      ('"materialType" "lit_emissive_plus"', 'the glow material'),
                      ('"colorMap00" "%s"' % IMAGES[1], 'the glow map bound')):
        if need not in gdt:
            bad.append('source_data/tod_cyber_teddy.gdt lacks %s (%s)' % (need, why))
    if bad:
        raise SystemExit('cyber_teddy --check FAILED:\n  ' + '\n  '.join(bad))
    print('CYBER TEDDY OK: %d files == the manifest (rev %s), lift %s / half_depth %s / extents %s one chain (GSC, haven layout, generated anchors), zoned + precached + synced, the stock bear retired, the melee lane wired'
          % (len(man['files']), man['revision'], lift, half, ext))


def compiled(ledger, linker_log=None):
    man = json.loads(MAN.read_text(encoding='utf-8'))
    bad = []
    with open(ledger, encoding='utf-8-sig', newline='') as f:
        row = {r['name']: r for r in csv.DictReader(f)}.get(MODEL)
    if row is None:
        bad.append(MODEL + ' missing from the compiled xmodel ledger')
    elif int(row['lodCount']) != 1 or int(row['tris0']) != man['tris']:
        bad.append('%s compiled %s LOD(s) / %s triangles; map 1 compiled the same binary to 1 / %d'
                   % (MODEL, row['lodCount'], row['tris0'], man['tris']))
    assets = pathlib.Path(str(ledger).replace('_xmodel.csv', '.csv'))
    with open(assets, encoding='utf-8-sig', newline='') as f:
        arows = list(csv.DictReader(f))
    have = {(r['type'], r['name']): int(r['resident'] or 0) for r in arows}
    key = ('material', 'mc/' + MATERIAL) if ('material', 'mc/' + MATERIAL) in have else ('material', MATERIAL)
    if key not in have:
        bad.append('material %s missing from the compiled assets' % MATERIAL)
    elif have[key] <= len(key[1]) + EMPTY_MATERIAL_SLACK:
        bad.append('material %s compiled EMPTY (ledger row %d bytes = the name only: it draws flat gray)' % (MATERIAL, have[key]))
    for im in IMAGES:
        if ('image', im) not in have:
            bad.append('image %s missing from the compiled assets' % im)
    if linker_log is not None:
        lp = pathlib.Path(linker_log)
        if not lp.exists():
            bad.append('no linker transcript at %s' % lp)
        else:
            ours = {MODEL, MATERIAL} | set(IMAGES)
            for line in lp.read_text(encoding='utf-8-sig', errors='replace').replace('\0', '').splitlines():
                if any(c in line for c in LINKER_COMPLAINTS) and set(re.findall(r'[\w/]+', line.replace('mc/', ''))) & ours:
                    bad.append('linker: ' + line.replace('^1', '').strip()[:220])
    if bad:
        raise SystemExit('cyber_teddy --compiled-ledger FAILED:\n  ' + '\n  '.join(bad[:16]))
    print('CYBER TEDDY LEDGER OK: %s 1 LOD / %d triangles (map 1\'s), %s complete, %d images%s'
          % (MODEL, man['tris'], MATERIAL, len(IMAGES), '' if linker_log is None else '; no linker usage / techset complaint names it'))


if __name__ == '__main__':
    if '--compiled-ledger' in sys.argv:
        log = sys.argv[sys.argv.index('--linker-log') + 1] if '--linker-log' in sys.argv else None
        compiled(sys.argv[sys.argv.index('--compiled-ledger') + 1], log)
    else:
        check()
