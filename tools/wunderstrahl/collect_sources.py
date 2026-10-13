"""THE WUNDERSTRAHL's sources (docs/219, 2026-10-05): the BO3 Wunderwaffe DG-2 kit, read from the T7 Assets V2.8 dump
already on this PC (~/Downloads/T7 Assets V2.8.rar, read with 7-Zip; nothing downloaded, the dump never written).

  python tools/wunderstrahl/collect_sources.py            extract (cached) into tmp/wunderstrahl/src/, write the manifest
  python tools/wunderstrahl/collect_sources.py --verify   re-hash the cached files against tools/wunderstrahl/sources.json
  python tools/wunderstrahl/collect_sources.py --manifest hash the cache already extracted (extracts nothing)

WHAT IT TAKES (the DG-2 of The Giant, as the dump's _midgetblaster port ships it):
  model_export/.../wpn_t7_zmb_dg2_view/   the first-person model (12 bones, tag_flash 41 0 3.14) + its skeleton + textures
  model_export/.../wpn_t7_zmb_dg2_world/  the third-person model, LOD0..7 + textures
  xanim_export/.../vm_dg2_*               the 26 first-person clips (renamed tod2_ws_vm_* by tools/wunderstrahl/model/)
  source_data/.../t7_base_dg2.gdt         the port's GDT (a field reference only; nothing ships from it)
  sound_assets/.../dg2/                   the DG-2's hum, flux, bounce and impact (layered by tools/wunderstrahl/sound/)
  texture_assets/.../menu_mp_weapons_dg2  the stock menu icon (a reference for the HUD icons)
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
ARCHIVE = pathlib.Path.home() / 'Downloads' / 'T7 Assets V2.8.rar'
SEVEN_ZIP = r'C:\Program Files\7-Zip\7z.exe'
OUT = ROOT / 'tmp' / 'wunderstrahl' / 'src'
MANIFEST = pathlib.Path(__file__).resolve().parent / 'sources.json'
PREFIX = 'T7 Assets V2.8'
MEMBERS = [
    'model_export/_midgetblaster/weapons/t7/wpn_t7_zmb_dg2_view/*',
    'model_export/_midgetblaster/weapons/t7/wpn_t7_zmb_dg2_world/*',
    'xanim_export/_midgetblaster/black_ops_3/vm_dg2_*',
    'source_data/_midgetblaster/t7_base_dg2.gdt',
    'sound_assets/wpn/energy/dg2/*',
    'sound_assets/zmb/zmb_blops/wpn/energy/dg2/*',
    'texture_assets/_midgetblaster/t7_ui/menu_mp_weapons_dg2.png',
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def files():
    base = OUT / PREFIX
    return sorted(p for p in base.rglob('*') if p.is_file()) if base.exists() else []


def extract():
    if not ARCHIVE.exists():
        sys.exit('WUNDERSTRAHL SOURCES: %s is not on this PC' % ARCHIVE)
    OUT.mkdir(parents=True, exist_ok=True)
    args = [SEVEN_ZIP, 'x', '-y', str(ARCHIVE)] + [PREFIX + '/' + m for m in MEMBERS] + ['-r']
    r = subprocess.run(args, cwd=str(OUT), capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('WUNDERSTRAHL SOURCES: 7-Zip failed: ' + r.stderr[-400:])
    return write_manifest()


def write_manifest():
    rows = {str(p.relative_to(OUT / PREFIX)).replace(os.sep, '/'): sha(p) for p in files()}
    if not rows:
        sys.exit('WUNDERSTRAHL SOURCES: nothing cached under %s - run collect_sources.py' % OUT)
    MANIFEST.write_text(json.dumps({'archive': ARCHIVE.name, 'prefix': PREFIX, 'files': rows}, indent=1, sort_keys=True) + '\n',
                        encoding='utf-8')
    print('WUNDERSTRAHL SOURCES: %d files -> %s, manifest %s' % (len(rows), OUT.relative_to(ROOT), MANIFEST.relative_to(ROOT)))
    return 0


def verify():
    if not MANIFEST.exists():
        sys.exit('WUNDERSTRAHL SOURCES: no manifest - run collect_sources.py')
    want = json.loads(MANIFEST.read_text(encoding='utf-8'))['files']
    bad = []
    for rel, h in sorted(want.items()):
        p = OUT / PREFIX / rel
        if not p.exists():
            bad.append('missing ' + rel)
        elif sha(p) != h:
            bad.append('changed ' + rel)
    if bad:
        print('WUNDERSTRAHL SOURCES DRIFT:\n  ' + '\n  '.join(bad))
        return 1
    print('WUNDERSTRAHL SOURCES OK: %d files match the manifest' % len(want))
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--manifest', action='store_true', help='hash the cache already extracted; extract nothing')
    a = ap.parse_args()
    sys.exit(verify() if a.verify else write_manifest() if a.manifest else extract())
