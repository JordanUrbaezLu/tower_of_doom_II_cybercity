"""THE LUCKY SOURCES' MODELS: source + compiled checks (docs/197). A build gate (tools/build_map.ps1).

  python tools/lucky/verify_native.py                              before the link: the exported models, the GDT
  python tools/lucky/verify_native.py --compiled-ledger <xmodel csv>  after the link: every model compiled whole

SOURCE: art/lucky/manifest.json (written by tools/lucky/01_author.py in the Blender studio) pins the GDT, every model
file and texture by sha256 and every LOD's triangle count; every model is one tag_origin bone, every vertex weighted
to it, finite normals / UVs. THE CONSISTENCY RULE (user 2026-09-29: the clover must look like "it comes from this
game ... consistent with other drops like pap and perk bottle and zombie blood" / "why would you make it gold"): the
clover's faces wear ONLY the drops' own stock material (mtl_x2icon_gold - the PaP drop and Zombie Blood wear it), and
that material is never redefined in our GDT. THE METEOR: its lumps stay inside _tod_lucky.gsc TOD_METEOR_HIT_R (a shot
on the rock always counts). The Golden Zombie twins are checked by tools/lucky/make_golden.py --check.
COMPILED: the linker's xmodel ledger (tris columns run COARSE -> FINE: tris0 is the lowest LOD) holds every LOD of
every model with exactly the exported triangles; the golden twins compiled with their donors' triangles; the asset
ledger holds all seven effects and our materials.
"""
import argparse, csv, hashlib, json, math, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel

DROP_MTL = 'mtl_x2icon_gold'
FX = ['fx_luck_meteor_trail', 'fx_luck_meteor_burst', 'fx_luck_meteor_frag', 'fx_luck_clover_trail', 'fx_luck_clover_land',
      'fx_luck_golden_aura', 'fx_luck_golden_burst']
GOLDEN = {'tod_golden_zombie_body': 'tod_charcoal_c_zom_dlc3_zombie_sentinel_body',
          'tod_golden_zombie_head': 'tod_charcoal_c_zom_dlc4_zombie_charred_head'}
LOD_COUNT = {'tod_luck_clover': 3, 'tod_luck_meteor': 1}

ap = argparse.ArgumentParser(); ap.add_argument('--compiled-ledger', type=pathlib.Path); args = ap.parse_args()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
fails = []
def ok(cond, msg):
    if not cond: fails.append(msg)

m = json.loads((ROOT / 'art/lucky/manifest.json').read_text())
gdt_path = ROOT / 'source_data/tod_lucky.gdt'
ok(m['gdt_sha256'] == sha(gdt_path), 'source_data/tod_lucky.gdt differs from the manifest: re-run tools/lucky/01_author.py in the studio (never hand-edit the GDT)')
ok(m.get('drop_material') == DROP_MTL, 'the manifest does not record the drops\' material ' + DROP_MTL)
gdt = gdt_path.read_text()
blocks = {name: (kind, dict(re.findall(r'"([^"\n]+)" "([^"\n]*)"', body)))
          for name, kind, body in re.findall(r'"([^"\n]+)" \( "([^"\n]+).gdf" \)\s*\{(.*?)\n\t\}', gdt, re.S)}
ok(DROP_MTL not in blocks, DROP_MTL + ' is the STOCK drop material: it must never be redefined in tod_lucky.gdt')
for name, h in m['textures'].items():
    p = ROOT / 'model_export/tod_lucky/_images' / name
    ok(p.exists() and sha(p) == h, 'texture differs from the manifest: ' + name)
for name, (kind, f) in blocks.items():
    if kind == 'material':
        for key in ('colorMap', 'colorMap00', 'normalMap', 'specColorMap', 'cosinePowerMap'):
            ok(f.get(key) in blocks and (ROOT / blocks[f[key]][1]['baseImage']).exists(), 'material %s: %s has no image' % (name, key))
    if kind == 'image':
        from PIL import Image
        with Image.open(ROOT / f['baseImage']) as im:
            ok(im.size[0] % 4 == 0 and im.size[1] % 4 == 0, 'image %s is not a multiple of 4 (a compressed image must be)' % name)

gsc = (ROOT / 'scripts/zm/zm_tod2_cybercity/_tod_lucky.gsc').read_text()
hit_r = float(re.search(r'#define TOD_METEOR_HIT_R\s+([0-9.]+)', gsc).group(1))

counts = {}
for r in m['models']:
    path = ROOT / r['file']
    ok(path.exists() and sha(path) == r['sha256'], 'model file differs from the manifest: ' + r['file'])
    model = xmodel.Model(); model.LoadFile_Bin(str(path), split_meshes=True)
    ok(len(model.bones) == 1 and model.bones[0].name == 'tag_origin', r['asset'] + ': one tag_origin bone')
    count = sum(len(mesh.faces) for mesh in model.meshes)
    ok(count == r['triangles'], '%s lod%d: %d triangles, manifest %d' % (r['asset'], r['lod'], count, r['triangles']))
    counts.setdefault(r['asset'], []).append(count)
    mats = {model.materials[f.material_id].name for mesh in model.meshes for f in mesh.faces}
    far = 0.0
    for i, mesh in enumerate(model.meshes):
        ok(all(v.weights == [(0, 1.)] for v in mesh.verts), r['asset'] + ': every vertex weighted to tag_origin')
        far = max([far] + [math.sqrt(sum(c * c for c in v.offset)) for v in mesh.verts])
        for f in mesh.faces:
            ok(all(all(math.isfinite(x) for x in c.normal + c.uv) for c in f.indices), r['asset'] + ': a non-finite normal / uv')
    if r['asset'] == 'tod_luck_clover':
        ok(mats == {DROP_MTL}, 'THE CONSISTENCY RULE: the clover wears only ' + DROP_MTL + ', found ' + str(sorted(mats)))
    else:
        ok(all(x in blocks for x in mats), r['asset'] + ': a face material is not defined in tod_lucky.gdt: ' + str(sorted(mats)))
    if r['asset'] == 'tod_luck_meteor':
        ok(far <= hit_r, 'the meteor reaches %.0f units from its centre, past TOD_METEOR_HIT_R %.0f: a shot on the rock would miss' % (far, hit_r))
for name, c in counts.items():
    ok(len(c) == LOD_COUNT.get(name, -1), '%s: %d LODs, expected %s' % (name, len(c), LOD_COUNT.get(name)))
    ok(all(a > b > 0 for a, b in zip(c, c[1:])), '%s: LOD triangles must fall LOD to LOD %s' % (name, c))

compiled = False
if args.compiled_ledger:
    compiled = True
    with args.compiled_ledger.open(encoding='utf-8-sig', newline='') as f:
        rows = {r['name']: r for r in csv.DictReader(f)}
    for name, c in counts.items():
        row = rows.get(name)
        ok(row is not None, name + ' missing from the compiled xmodel ledger')
        if row:
            n = len(c)
            ok(int(row['lodCount']) == n, '%s compiled with %s LODs, exported %d' % (name, row['lodCount'], n))
            for lod, want in enumerate(c):   # tris0 is the COARSEST LOD
                got = int(row['tris' + str(n - 1 - lod)])
                ok(got == want, '%s lod%d compiled %d triangles, exported %d' % (name, lod, got, want))
    for twin, donor in GOLDEN.items():
        t, d = rows.get(twin), rows.get(donor)
        ok(t is not None and d is not None, 'golden twin %s or its donor %s missing from the compiled ledger' % (twin, donor))
        if t and d:
            ok(all(t[k] == d[k] for k in t if k.startswith('tris') or k == 'lodCount'), 'golden twin %s compiled different geometry from %s' % (twin, donor))
    assets = args.compiled_ledger.with_name(args.compiled_ledger.name.replace('_xmodel.csv', '.csv'))
    with assets.open(encoding='utf-8-sig', newline='') as f:
        have = {(r['type'], r['name']) for r in csv.DictReader(f)}
    for fx in FX:
        ok(('fx', 'tod/luck/' + fx) in have, 'effect tod/luck/%s missing from the compiled assets' % fx)
    for name, (kind, _) in blocks.items():
        if kind == 'material':
            ok(('material', 'mc/' + name) in have, 'material mc/%s missing from the compiled assets' % name)
    for mat in ('tod_golden_mtl_arms', 'tod_golden_mtl_body', 'tod_golden_mtl_legs', 'tod_golden_mtl_eyes'):
        ok(('material', 'mc/' + mat) in have, 'golden material mc/%s missing from the compiled assets' % mat)
    ok(('material', 'mc/' + DROP_MTL) in have, 'the drops\' material mc/%s missing from the compiled assets' % DROP_MTL)

data = dict(models=len(counts), triangles=counts, textures=len(m['textures']), meteor_hit_r=hit_r, drop_material=DROP_MTL,
            native_compiled_checked=compiled, native_playtested=False)
if fails:
    for f in fails: print('  FAIL  ' + f)
    print('LUCKY MODELS FAIL: %d problem(s)' % len(fails)); sys.exit(1)
(ROOT / 'art/lucky' / ('compiled_validation.json' if compiled else 'source_validation.json')).write_text(json.dumps(data, indent=2))
print('LUCKY MODELS OK' + (' (compiled)' if compiled else ''), json.dumps(data))
