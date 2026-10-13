"""companion_maps/test_negative_controls.py - prove the companion gates FAIL on the failures they exist for (W2A).

RUN  python tools/companion_maps/test_negative_controls.py [--root TREE] [--pre-w2a TREE]
TREE holds model_export/tod_partner/, source_data/tod_partners.gdt, zone_source/tod_partners.zpkg and
art/companion_maps/ (the repo after landing, or a scratch overlay). Every case copies that tree to a temp folder,
breaks ONE thing and runs the real gate on the copy: tools/partner/verify_assets.py --root and
tools/companion_maps/compose.py --check. The clean copy must PASS both; every broken copy must FAIL with the expected
message. --pre-w2a additionally runs verify_assets on a tree holding the shipped pre-W2A outputs (blue enamel swatch,
35 missing maps, the R.A.P.S. rust shell dropped), which must FAIL. Writes only inside its temp folder.
"""
from pathlib import Path
import argparse, json, re, shutil, subprocess, sys, tempfile

REPO = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser()
ap.add_argument('--root', type=Path, default=REPO)
ap.add_argument('--pre-w2a', type=Path, default=None)
A = ap.parse_args()
PORTRAIT = 'tools/artgen/packs/r1_comp_portraits.py'   # the HUD portrait's PROTECTOR_FINISH (LOCKSTEP)
VERIFY = REPO / 'tools/partner/verify_assets.py'
COMPOSE = REPO / 'tools/companion_maps/compose.py'
if (A.root / 'tools/partner/verify_assets.py').exists():
    VERIFY = A.root / 'tools/partner/verify_assets.py'
if (A.root / 'tools/companion_maps/compose.py').exists():
    COMPOSE = A.root / 'tools/companion_maps/compose.py'


def copy_tree(dst):
    for rel in ('model_export/tod_partner', 'art/companion_maps'):
        shutil.copytree(A.root / rel, dst / rel)
    for rel in ('source_data/tod_partners.gdt', 'zone_source/tod_partners.zpkg', PORTRAIT):
        src = A.root / rel if (A.root / rel).exists() else REPO / rel
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst / rel)


def run_verify(t):
    r = subprocess.run([sys.executable, str(VERIFY), '--root', str(t)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def run_compose(t):
    am = t / 'art/companion_maps'
    r = subprocess.run([sys.executable, str(COMPOSE), '--check', '--out', str(am / 'authored'), '--bakes', str(am / 'bakes'),
                        '--gdt', str(t / 'source_data/tod_partners.gdt'),
                        '--images', str(t / 'model_export/tod_partner/_images'),
                        '--manifest', str(t / 'model_export/tod_partner/manifest.json')], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def gdt_path(t):
    return t / 'source_data/tod_partners.gdt'


def edit_gdt(t, fn):
    p = gdt_path(t)
    s = p.read_text(encoding='utf-8')
    s2 = fn(s)
    assert s2 != s, 'mutation did not apply'
    p.write_text(s2, encoding='utf-8', newline='')


def edit_manifest(t, fn):
    p = t / 'model_export/tod_partner/manifest.json'
    m = json.loads(p.read_text())
    fn(m)
    p.write_text(json.dumps(m, indent=2) + '\n')


def block_field(s, name, key, value):
    """Set key in the GDT block `name` (block found by its header)."""
    i = s.index('\t"%s" (' % name)
    j = s.index('\t}', i)
    body = s[i:j]
    if '\t\t"%s" "' % key in body:
        body2 = re.sub(r'(\t\t"%s" ")[^"]*(")' % re.escape(key), r'\g<1>' + value + r'\g<2>', body, count=1)
    else:
        body2 = body + '\t\t"%s" "%s"\n' % (key, value)
    return s[:i] + body2 + s[j:]


def first_authored(t, suffix):
    man = json.loads((t / 'model_export/tod_partner/manifest.json').read_text())
    for n, src in sorted(man['images'].items()):
        if 'companion_maps/authored/' in src['from'] and src['original'].endswith(suffix):
            return n, src
    raise SystemExit('no authored %s map in the tree' % suffix)


def gold_material(t):
    man = json.loads((t / 'model_export/tod_partner/manifest.json').read_text())
    return [e['material'] for e in man['materials']['protector'] if e['original'].endswith('_upper_gold')][0]


def m_enamel(t):
    edit_gdt(t, lambda s: s.replace('{\n', '{\n\t"mtl_tod_partner_enamel" ( "material.gdf" )\n\t{\n\t\t"materialType" "lit"\n\t}\n', 1))


def m_flat(t):
    n, src = first_authored(t, '_o')
    from PIL import Image
    p = t / 'model_export/tod_partner/_images' / (n + '.png')
    Image.new('RGB', Image.open(p).size, (128, 128, 128)).save(p)


def m_missing(t):
    edit_manifest(t, lambda m: m.__setitem__('not_in_pack', {'i_veh_t7_drone_amws_armored_hull_n': ['x.normalMap']}))


def m_gold(t):
    g = gold_material(t)
    edit_gdt(t, lambda s: block_field(s, g, 'specColorTint', '0.078 0.380 0.565 1.000000'))


def m_semantic(t):
    n, src = first_authored(t, '_n')
    edit_gdt(t, lambda s: block_field(s, n, 'semantic', 'diffuseMap'))


def m_raps(t):
    def f(m):
        for e in m['materials']['raps']:
            if 'rust_spots' in e['original']:
                e.clear()
                e.update({'original': 'mtl_t7_veh_dlc_decal_rust_spots_01', 'triangles': 2110,
                          'result': 'DROPPED (no definition or art in the pack)'})
    edit_manifest(t, f)


def m_dropped_hull(t):
    def f(m):
        m['materials']['cerberus'].append({'original': 'mtl_veh_t7_drone_amws_armored_hull_mp_dark_color',
                                           'triangles': 1608, 'result': 'DROPPED (no definition or art in the pack)'})
    edit_manifest(t, f)


def m_portrait(t):
    p = t / PORTRAIT
    s = p.read_text(encoding='utf-8')
    s2 = re.sub(r"^PROTECTOR_FINISH\s*=\s*'gold'", "PROTECTOR_FINISH = 'blue'", s, count=1, flags=re.M)
    assert s2 != s
    p.write_text(s2, encoding='utf-8', newline='')


def c_pixel(t):
    p = sorted((t / 'art/companion_maps/authored').glob('*_tile_r.png'))[0]
    from PIL import Image
    im = Image.open(p)
    im.load()
    px = im.getpixel((7, 7))
    im.putpixel((7, 7), (px + 1) % 256 if isinstance(px, int) else tuple((c + 1) % 256 for c in px))
    im.save(p)


def c_installed(t):
    n, src = first_authored(t, '_tile_r')
    p = t / 'model_export/tod_partner/_images' / (n + '.png')
    from PIL import Image
    im = Image.open(p).convert('L')
    im.putpixel((3, 3), (im.getpixel((3, 3)) + 9) % 256)
    im.save(p)


def c_unwired(t):
    n, src = first_authored(t, '_g')
    def f(s):
        i = s.index('\t"%s" ( "image.gdf" )' % n)
        j = s.index('\t}\n', i) + 3
        return s[:i] + s[j:]
    edit_gdt(t, f)


CASES = [  # name, mutate, gate, expected text in the failure
    ('retired blue enamel swatch material back', m_enamel, run_verify, 'enamel'),
    ('a flat swatch in place of an authored map', m_flat, run_verify, 'flat swatch'),
    ('a map no source holds', m_missing, run_verify, 'no source holds'),
    ('the Protector shell loses the donor gold', m_gold, run_verify, 'not the donor gold finish'),
    ('a normal map declared diffuseMap', m_semantic, run_verify, 'slot semantic mismatch'),
    ('the R.A.P.S. rust shell dropped again', m_raps, run_verify, 'R.A.P.S. dropped'),
    ('a real armour material dropped', m_dropped_hull, run_verify, 'non-decal material was dropped'),
    ('the HUD portrait shows another Protector finish', m_portrait, run_verify, 'portrait / world Protector finish'),
    ('an authored map edited by hand', c_pixel, run_compose, 'differs from its recipe'),
    ('an installed copy is not the authored pixels', c_installed, run_compose, 'not the authored pixels'),
    ('an authored map with no GDT block', c_unwired, run_compose, 'no GDT image block'),
]


def main():
    fails = 0
    with tempfile.TemporaryDirectory(prefix='w2a_negctl_') as tmp:
        clean = Path(tmp) / 'clean'
        copy_tree(clean)
        for gate in (run_verify, run_compose):
            rc, out = gate(clean)
            ok = rc == 0
            fails += not ok
            print('%s  clean tree passes %s' % ('ok  ' if ok else 'FAIL', gate.__name__), '' if ok else out[-600:])
        for i, (label, mutate, gate, expect) in enumerate(CASES):
            t = Path(tmp) / ('case%02d' % i)
            copy_tree(t)
            mutate(t)
            rc, out = gate(t)
            ok = rc != 0 and expect in out
            fails += not ok
            print('%s  %-48s -> %s' % ('ok  ' if ok else 'FAIL', label, 'caught' if ok else ('NOT CAUGHT rc=%d' % rc)))
            if not ok:
                print(out[-800:])
            shutil.rmtree(t, ignore_errors=True)
    if A.pre_w2a:
        pre = A.pre_w2a
        if not (pre / 'zone_source/tod_partners.zpkg').exists():     # a base snapshot carries only what it changed
            pre = Path(tempfile.mkdtemp(prefix='w2a_pre_'))
            for rel in ('model_export/tod_partner', ):
                shutil.copytree(A.pre_w2a / rel, pre / rel)
            for rel in ('source_data/tod_partners.gdt', 'zone_source/tod_partners.zpkg'):
                (pre / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(A.pre_w2a / rel if (A.pre_w2a / rel).exists() else A.root / rel, pre / rel)
        rc, out = run_verify(pre)
        ok = rc != 0 and 'no source holds' in out
        fails += not ok
        print('%s  the shipped pre-W2A outputs fail verify_assets' % ('ok  ' if ok else 'FAIL'))
    if fails:
        print('COMPANION_NEGCTL_FAIL: %d case(s)' % fails)
        sys.exit(1)
    print('COMPANION_NEGCTL_PASS: clean tree passes both gates; %d broken trees are each caught' % len(CASES))


if __name__ == '__main__':
    main()
