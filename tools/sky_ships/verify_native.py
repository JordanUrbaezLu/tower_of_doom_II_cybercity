"""THE SKY FLEET native gate (docs/192).

  python tools/sky_ships/verify_native.py                                    source checks (every build)
  python tools/sky_ships/verify_native.py --compiled-ledger <..._xmodel.csv> + the linker's own ledgers

Source: the installed GDT is byte-identical to the staged export; every model file hashes to its manifest
entry and has exactly the manifest's triangle count with finite normals/UVs; a ship's bones are tag_origin + one
tag_eng_<i> per exported nozzle (child of tag_origin, AT the nozzle, turned aft: the flames play on them), a rock's
are tag_origin alone; every material in the GDT points at images that exist, the rock materials are rock surfaces
(dim spec); every material stays under one BO3 surface's vertex budget. Compiled: all fifteen models (four hulls +
four colour variants, five rocks + two vein colours) are in the xmodel ledger with that exact triangle count (nothing
lost in conversion), and EVERY sky effect gen_fx.py makes (flames, glints, rifts, stars, fireballs + their children,
the lights, the jump title's gunship engines) + every sky material are in the asset ledger. A successful link alone
proves none of that.
"""
import argparse, csv, hashlib, json, math, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/cyber_elites'))
from inspect_assets import xmodel

p = argparse.ArgumentParser()
p.add_argument('--compiled-ledger', type=pathlib.Path)
args = p.parse_args()
from verify_surface_detail import verify as verify_surface_detail
verify_surface_detail()
sha = lambda f: hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
AFT = [(-1, 0, 0), (0, -1, 0), (0, 0, 1)]                                  # a flame tag's +X points aft (06_export.py)

m = json.loads((ROOT / 'art/sky_ships/manifest.json').read_text(encoding='utf-8'))
staged = ROOT / m['gdt']
installed = ROOT / 'source_data/tod_sky_ships.gdt'
assert installed.exists(), 'source_data/tod_sky_ships.gdt missing: run python tools/sky_ships/install.py'
assert sha(installed) == sha(staged) == m['gdt_sha256'], 'installed GDT differs from the export (re-run 06_export.py + install.py)'
gdt = installed.read_text(encoding='utf-8')
blocks = {name: (kind, dict(re.findall(r'"([^"\n]+)" "([^"\n]*)"', body)))
          for name, kind, body in re.findall(r'"([^"\n]+)" \( "([^"\n]+)\.gdf" \)\s*\{(.*?)\n\t\}', gdt, re.S)}
for name, h in m['images'].items():
    assert sha(ROOT / 'model_export/tod_sky_ships/_images' / (name + '.png')) == h, 'texture changed since export: ' + name
for name, (kind, f) in blocks.items():
    if kind == 'material':
        for key in ('colorMap', 'colorMap00', 'normalMap', 'specColorMap', 'cosinePowerMap'):
            img = f[key]
            assert img in blocks and (ROOT / blocks[img][1]['baseImage']).exists(), (name, key, img)
    if kind == 'image':
        assert blocks[name][1]['baseImage'].startswith('model_export/tod_sky_ships/_images/'), name
models = {}
for r in m['ships']:
    path = ROOT / r['file']
    assert sha(path) == r['sha256'], 'model changed since export: ' + r['file']
    mod = xmodel.Model()
    mod.LoadFile_Bin(str(path), split_meshes=True)
    want = ['tag_origin'] + ['tag_eng_%d' % i for i in range(len(r['nozzles']))]
    assert [b.name for b in mod.bones] == want, (r['file'], [b.name for b in mod.bones], want)
    for i, (x, y, z, rad) in enumerate(r['nozzles']):
        b = mod.bones[i + 1]
        assert b.parent == 0 and all(abs(a - c) < 0.01 for a, c in zip(b.offset, (x, y, z))), (r['file'], b.name, b.offset)
        assert all(abs(a - c) < 1e-4 for row, want_row in zip(b.matrix, AFT) for a, c in zip(row, want_row)), (r['file'], b.name, b.matrix)
    tris = sum(len(mesh.faces) for mesh in mod.meshes)
    assert tris == r['triangles'], (r['file'], tris, r['triangles'])
    for i, mesh in enumerate(mod.meshes):
        for f in mesh.faces:
            assert mod.materials[f.material_id].name in blocks, (r['file'], mod.materials[f.material_id].name)
            assert all(all(math.isfinite(v) for v in c.normal + c.uv) for c in f.indices), r['file']
    for name in r['models']:
        kind, f = blocks[name]
        assert kind == 'xmodel' and f['filename'] == 'tod_sky_ships/' + path.name and f['noCastShadow'] == '1', name
        models[name] = tris

for r in m['rocks']:
    path = ROOT / r['file']
    assert sha(path) == r['sha256'], 'model changed since export: ' + r['file']
    mod = xmodel.Model()
    mod.LoadFile_Bin(str(path), split_meshes=True)
    assert [b.name for b in mod.bones] == ['tag_origin'], r['file']
    tris = sum(len(mesh.faces) for mesh in mod.meshes)
    assert tris == r['triangles'], (r['file'], tris, r['triangles'])
    for mesh in mod.meshes:
        for f in mesh.faces:
            assert mod.materials[f.material_id].name in blocks, (r['file'], mod.materials[f.material_id].name)
            assert all(all(math.isfinite(v) for v in c.normal + c.uv) for c in f.indices), r['file']
    assert max(r['surface_verts'].values()) <= 60000, (r['rock'], 'a material exceeds one surface')
    assert 0 < r['radius'] < 2000, (r['rock'], r['radius'])
    for name in r['models']:
        kind, f = blocks[name]
        assert kind == 'xmodel' and f['filename'] == 'tod_sky_ships/' + path.name and f['noCastShadow'] == '1', name
        models[name] = tris
for name in ('mtl_tod_sky_rock', 'mtl_tod_sky_rock2'):
    kind, f = blocks[name]
    assert kind == 'material' and f['surfaceType'] == 'rock' and f['colorMap'].startswith('i_tod_sky_rock'), (name, f.get('surfaceType'))
    assert f['normalMap'] == 'i_tod_sky_rock_n' and float(f['specAmount']) <= 0.25, (name, f['normalMap'], f['specAmount'])
fx = sorted('tod/sky/' + e.stem for e in (ROOT / 'share/raw/fx/tod/sky').glob('fx_sky_*.efx'))
assert len(fx) >= 60 and 'tod/sky/fx_sky_eng_gunship' in fx, 'the sky effects are not generated (python tools/sky_ships/gen_fx.py)'
for s in m['ships']:
    assert max(s['surface_verts'].values()) <= 60000, (s['ship'], 'a material exceeds one surface', s['surface_verts'])
    assert s['lights'], s['ship'] + ' exports no blinking-light anchors'
assert len(models) == 15, 'expected 15 sky models (8 ships, 7 rocks), got ' + str(sorted(models))
report = dict(models=len(models), triangles=models, fx=fx, native_compiled_checked=False, native_playtested=False)
if args.compiled_ledger:
    with args.compiled_ledger.open(encoding='utf-8-sig', newline='') as fh:
        ledger = {row['name']: row for row in csv.DictReader(fh)}
    for name, tris in models.items():
        assert name in ledger, 'sky ship not compiled: ' + name
        row = ledger[name]
        assert int(row['lodCount']) == 1 and int(row['tris0']) == tris, (name, row['lodCount'], row['tris0'], tris)
    assets_path = args.compiled_ledger.with_name(args.compiled_ledger.name.replace('_xmodel.csv', '.csv'))
    with assets_path.open(encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.DictReader(fh))
    have = {(r['type'], r['name']) for r in rows}
    for name in fx:
        assert ('fx', name) in have, 'sky effect not in the compiled assets: ' + name
    mats = [n for n, (k, _) in blocks.items() if k == 'material']
    missing = [n for n in mats if ('material', 'mc/' + n) not in have and ('material', n) not in have]
    assert not missing, 'sky materials not compiled: ' + ', '.join(missing)
    missing_images=[name for name in m['images'] if ('image',name) not in have]
    assert not missing_images,'sky images not compiled: '+', '.join(missing_images)
    report['native_compiled_checked'] = True
out = ROOT / 'art/sky_ships' / ('compiled_validation.json' if args.compiled_ledger else 'source_validation.json')
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('SKY FLEET NATIVE OK', 'compiled' if args.compiled_ledger else 'source', json.dumps(models))
