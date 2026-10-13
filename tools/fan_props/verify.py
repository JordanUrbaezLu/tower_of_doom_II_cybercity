#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# tools/fan_props/verify.py - THE FAN PROPS GATE (TOD II, docs/208).
#
# Nikolai's props, ported from map 1 as its BUILT outputs (map 1's
# tools/fan_props/* rebuild them from his Meshy pack in Blender; this map ships
# the result): the AMMO BOX V6 on every crate, the TOWER OF DOOM CYBERCITY
# sign over the plaza (+ its OFF / DIM power twins), the GRID TERMINAL V5 that
# is the crown's power switch (+ its dial and five screen frames).
#
#   --check   (every build, pre-link) every file == tools/fan_props/manifest.json
#             (sha256), the GDT == the manifest's, every block's file is in the
#             manifest, every model is zoned AND precached by a script, the sync
#             copies model_export\tod_fan_props.
#   --compiled-ledger <map>_xmodel.csv [--linker-log <transcript>]   (post-link)
#             every model compiled with its one LOD and exactly map 1's triangle
#             count (the same binaries), every material COMPLETE (a ledger row that
#             is only its name = an EMPTY material = flat gray: the jump pad's
#             2026-10-03 lesson), every image in the assets, and no linker usage /
#             techset complaint naming one of these materials or models.
# Never hand-edit the shipped files: re-run the migration kit's builder.
# -----------------------------------------------------------------------------
import csv
import hashlib
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
MAN = REPO / 'tools' / 'fan_props' / 'manifest.json'
LINKER_COMPLAINTS = ('mismatched usage', "doesn't expose", 'no techset')
EMPTY_MATERIAL_SLACK = 64        # install_de_jumppad.py's measure: an empty row is len(name) + 2


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check():
    man = json.loads(MAN.read_text(encoding='utf-8'))
    bad = []
    for rel, info in man['files'].items():
        p = REPO / rel
        if not p.exists():
            bad.append('missing ' + rel)
        elif sha(p) != info['sha256']:
            bad.append('changed since the manifest: ' + rel)
    gdt = REPO / man['gdt']
    if not gdt.exists():
        bad.append('missing ' + man['gdt'])
        gtext = ''
    else:
        if hashlib.sha256(gdt.read_bytes()).hexdigest() != man['gdt_sha256']:
            bad.append(man['gdt'] + ' differs from the manifest (re-run the builder; never hand-edit)')
        gtext = gdt.read_text(encoding='utf-8')
    for ref in re.findall(r'"(?:baseImage|filename)" "([^"]+)"', gtext):
        r = ref.replace('\\\\', '\\').replace('\\', '/')
        if r.startswith('$') or not r:
            continue
        if not r.startswith('model_export/') and r.endswith('.xmodel_bin'):
            r = 'model_export/' + r
        if r not in man['files']:
            bad.append('the GDT names %s, which the manifest does not ship' % r)
    zone = (REPO / 'zone_source' / 'zm_tod2_cybercity.zone').read_text(encoding='utf-8')
    scripts = '\n'.join(p.read_text(encoding='utf-8', errors='replace') for p in (REPO / 'scripts').rglob('*.gsc'))
    for m in man['models']:
        if not re.search(r'^xmodel,' + re.escape(m) + r'\s*$', zone, re.M):
            bad.append('model %s is not zoned (xmodel,%s)' % (m, m))
        if '#precache( "model", "%s" )' % m not in scripts:
            bad.append('model %s is not precached by any script' % m)
    sync = (REPO / 'tools' / 'sync_to_modtools.ps1').read_text(encoding='utf-8')
    if 'model_export\\tod_fan_props' not in sync:
        bad.append('tools/sync_to_modtools.ps1 does not copy model_export\\tod_fan_props')
    if bad:
        raise SystemExit('fan_props --check FAILED:\n  ' + '\n  '.join(bad))
    mb = sum(v['bytes'] for v in man['files'].values()) / 1e6
    print('FAN PROPS OK: %d files (%.1f MB) == the manifest, %d models zoned + precached, %d materials, %d images, synced'
          % (len(man['files']), mb, len(man['models']), len(man['materials']), len(man['images'])))


def compiled(ledger, linker_log=None):
    man = json.loads(MAN.read_text(encoding='utf-8'))
    bad = []
    with open(ledger, encoding='utf-8-sig', newline='') as f:
        rows = {r['name']: r for r in csv.DictReader(f)}
    for name, info in man['models'].items():
        row = rows.get(name)
        if row is None:
            bad.append(name + ' missing from the compiled xmodel ledger')
        elif int(row['lodCount']) != 1:
            bad.append('%s compiled with %s LODs, shipped 1' % (name, row['lodCount']))
        elif int(row['tris0']) != info['tris']:
            bad.append('%s compiled %s triangles, map 1 compiled the same binary to %d' % (name, row['tris0'], info['tris']))
    assets = pathlib.Path(str(ledger).replace('_xmodel.csv', '.csv'))
    with open(assets, encoding='utf-8-sig', newline='') as f:
        arows = list(csv.DictReader(f))
    have = {(r['type'], r['name']) for r in arows}
    resident = {(r['type'], r['name']): int(r['resident'] or 0) for r in arows}
    for mt in man['materials']:
        key = ('material', 'mc/' + mt) if ('material', 'mc/' + mt) in have else ('material', mt)
        if key not in have:
            bad.append('material %s missing from the compiled assets' % mt)
        elif resident[key] <= len(key[1]) + EMPTY_MATERIAL_SLACK:
            bad.append('material %s compiled EMPTY (ledger row %d bytes = the name only: it draws flat gray)' % (mt, resident[key]))
    for im in man['images']:
        if ('image', im) not in have:
            bad.append('image %s missing from the compiled assets' % im)
    if linker_log is not None:
        lp = pathlib.Path(linker_log)
        if not lp.exists():
            bad.append('no linker transcript at %s' % lp)
        else:
            ours = set(man['materials']) | set(man['models'])
            n = 0
            for line in lp.read_text(encoding='utf-8-sig', errors='replace').replace('\0', '').splitlines():
                if any(c in line for c in LINKER_COMPLAINTS) and set(re.findall(r'[\w/]+', line.replace('mc/', ''))) & ours:
                    n += 1
                    if n <= 12:
                        bad.append('linker: ' + line.replace('^1', '').strip()[:220])
    if bad:
        raise SystemExit('fan_props --compiled-ledger FAILED:\n  ' + '\n  '.join(bad))
    print('FAN PROPS LEDGER OK: %d models (1 LOD, map 1\'s triangle counts), %d materials complete, %d images%s'
          % (len(man['models']), len(man['materials']), len(man['images']),
             '' if linker_log is None else '; no linker usage / techset complaint names a prop'))


if __name__ == '__main__':
    if '--compiled-ledger' in sys.argv:
        log = sys.argv[sys.argv.index('--linker-log') + 1] if '--linker-log' in sys.argv else None
        compiled(sys.argv[sys.argv.index('--compiled-ledger') + 1], log)
    else:
        check()
