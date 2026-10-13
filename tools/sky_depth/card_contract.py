"""Read generated native sign-card assets and prove their preview/build bindings."""
import csv
import json
import math
import pathlib
import re
import sqlite3
import sys

from pass_config import ROOT, REVIEW, STAGE, sha, source_hashes

RECEIPT = ROOT/'art/jump_title/sign_card.json'
GENERATOR = ROOT/'tools/jump_title/make_sign_card.py'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def blocks(path):
    text = path.read_text(encoding='utf-8-sig')
    return {name: (kind, dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"', body)))
            for name, kind, body in re.findall(r'"([^"\n]+)"\s*\(\s*"(\w+)\.gdf"\s*\)\s*\{([^}]+)\}', text)}


def load_card():
    receipt = json.loads(RECEIPT.read_text(encoding='utf-8'))
    native = {}
    for key, name in receipt['files'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(ROOT), 'Card input escaped this repository')
        require(sha(path) == receipt['sha256'][key], 'Generated card input differs from receipt: '+name)
        native[path.relative_to(ROOT).as_posix()] = path
    gdt = ROOT/receipt['files']['gdt']
    assets = blocks(gdt)
    require(assets[receipt['model']][0] == 'xmodel', 'Card model GDT missing')
    material = assets[receipt['material']][1]
    require(material['materialType'] == 'lit_emissive_transparent', 'Unsupported native card shader')
    require([float(v) for v in material['colorTint'].split()][:3] == [0, 0, 0], 'Preview expects emission-only native card')
    scale = float(material['scaleRGB'])
    require(math.isfinite(scale) and scale > 0 and scale == receipt['scale_rgb'], 'Card emission differs from receipt')
    textures = {}
    for role in ('colorMap', 'colorMap00'):
        name = material[role]
        kind, fields = assets[name]
        require(kind == 'image' and fields['coreSemantic'] == 'sRGB3chAlpha', 'Unexpected native card image binding')
        require(fields.get('noMipMaps') == '1' and fields.get('noPicMip') == '1', 'Native NPOT card requires full-resolution, mip-free images')
        path = (ROOT/fields['baseImage'].replace('\\', '/')).resolve()
        require(path.is_relative_to(ROOT) and path.is_file(), 'Native card texture unavailable')
        native[path.relative_to(ROOT).as_posix()] = path
        textures[role] = {'name': name, 'path': str(path), 'sha256': sha(path), 'fields': fields}
    # Use the actual exported binary, never rebuild a guessed quad from metadata.
    sys.dont_write_bytecode = True
    addon = pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'
    if str(addon) not in sys.path:
        sys.path.insert(0, str(addon))
    from PyCoD import xmodel
    model = xmodel.Model()
    model.LoadFile_Bin(str(ROOT/receipt['files']['model']), split_meshes=True)
    meshes = []
    for mesh in model.meshes:
        vertices = [list(v.offset) for v in mesh.verts]
        require(all(math.isfinite(c) for v in vertices for c in v), 'Nonfinite native card geometry')
        faces = []
        for face in mesh.faces:
            require(model.materials[face.material_id].name == receipt['material'], 'Unexpected card material slot')
            # BO3 clockwise faces -> Blender counterclockwise; V origin flips.
            faces.append({'vertices': [face.indices[i].vertex for i in (0, 2, 1)],
                          'uv': [[face.indices[i].uv[0], 1-face.indices[i].uv[1]] for i in (0, 2, 1)]})
        meshes.append({'name': mesh.name, 'vertices': vertices, 'faces': faces})
    triangles = sum(len(m['faces']) for m in meshes)
    require(triangles > 0, 'Empty native sign card')
    hashes = {name: sha(path) for name, path in native.items()}
    hashes.update({p.relative_to(ROOT).as_posix(): sha(p) for p in (RECEIPT, GENERATOR)})
    return {'receipt': receipt, 'material': material, 'model_fields': assets[receipt['model']][1],
            'textures': textures, 'meshes': meshes, 'triangles': triangles,
            'native_files': sorted(native), 'input_hashes': hashes}


def validate_card_art(card):
    """The card must consume the reviewed shared-frame/visibility material bake."""
    receipt_path = REVIEW/'native_card_art.json'
    art = json.loads(receipt_path.read_text(encoding='utf-8'))
    require((ROOT/art['output']).resolve() == STAGE/'native_card_finished.png', 'Native art output belongs to another pass')
    require((ROOT/art['generated_asset']).resolve() == ROOT/'art/sky3d/sign/v13_native_lit.png', 'Native card must use the v13 bake')
    require((ROOT/card['receipt']['derived_art_receipt']).resolve() == receipt_path, 'Card generator still targets another pass receipt')
    require(card['receipt']['derived_art_receipt_sha256'] == sha(receipt_path), 'Card generator has stale derived-art proof')
    require((ROOT/card['receipt']['native_image_source']).resolve() == ROOT/art['generated_asset'], 'Card generator uses another permanent image')
    require(card['receipt']['native_image_sha256'] == art['output_sha256'], 'Card generator has stale derived image')
    require(art['sky_source_hashes'] == source_hashes(), 'Native card material bake has stale sky inputs')
    author = json.loads((STAGE/'author.json').read_text(encoding='utf-8'))
    require(art['sky_master_sha256'] == author['blend_sha256'], 'Native card material bake belongs to a different sky master')
    inputs = [receipt_path]
    for key in ('output', 'generated_asset', 'blend', 'source_png'):
        path = (ROOT/art[key]).resolve()
        require(path.is_relative_to(ROOT), 'Native card art input escaped this repository')
        require(sha(path) == art[key+'_sha256'], 'Native card art input changed: '+art[key])
        inputs.append(path)
    require(art['generated_asset_sha256'] == art['output_sha256'], 'Permanent native card art differs from reviewed bake')
    for key, name in (('authoring_script_sha256', 'bake_native_card.py'), ('renderer_sha256', 'render_native_card.py')):
        path = pathlib.Path(__file__).with_name(name)
        require(sha(path) == art[key], 'Native card art helper changed: '+name)
        inputs.append(path)
    for texture in card['textures'].values():
        require(texture['sha256'] == art['output_sha256'], 'Native card still uses art other than the reviewed frame/visibility bake')
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}


def verify_native(core, captured_ns):
    card = load_card()
    receipt = card['receipt']
    ff_ns = (core.DEP/'zone'/(core.MAP+'.ff')).stat().st_mtime_ns
    ledger = core.DEP/'zone_source/all/assetinfo'/(core.MAP+'.csv')
    model_ledger = ledger.with_name(core.MAP+'_xmodel.csv')
    for path in (ledger, model_ledger):
        require(captured_ns < path.stat().st_mtime_ns <= ff_ns+5*10**9, 'Card ledger is not from this build')
    with ledger.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    assets = {(row['type'], core.normalized_asset(row['name'])) for row in rows}
    require(('xmodel', receipt['model']) in assets, 'Native sign model missing from asset ledger')
    require(any(('material', name) in assets for name in (receipt['material'], 'mc/'+receipt['material'])), 'Native sign material missing from asset ledger')
    for texture in card['textures'].values():
        require(('image', texture['name']) in assets, 'Native sign image missing from asset ledger: '+texture['name'])
    with model_ledger.open(encoding='utf-8-sig', newline='') as handle:
        models = {core.normalized_asset(row['name']): row for row in csv.DictReader(handle)}
    compiled = models.get(receipt['model'])
    require(compiled and int(compiled['lodCount']) == 1 and int(compiled['tris0']) == card['triangles'], 'Compiled card triangle coverage differs from exported binary')
    bindings = {}
    gdt_assets = blocks(ROOT/receipt['files']['gdt'])
    db = core.MT/'gdtdb/gdt.db'
    with sqlite3.connect(db.as_uri()+'?mode=ro', uri=True) as con:
        # BO3's legacy scriptbundle table exceeds Python SQLite's column limit.
        # Match the core verifier's connection-local compatibility setting;
        # mode=ro continues to prevent database writes.
        con.execute('pragma writable_schema=ON')
        con.row_factory = sqlite3.Row
        checks = [('material', receipt['material'], ('materialType', 'colorMap', 'colorMap00', 'scaleRGB', 'colorTint', 'colorTint1')),
                  ('xmodel', receipt['model'], ('filename', 'scale', 'noCastShadow'))]
        checks += [('image', t['name'], ('baseImage', 'coreSemantic', 'noMipMaps', 'noPicMip')) for t in card['textures'].values()]
        for kind, name, keys in checks:
            row = con.execute('SELECT * FROM '+kind+' WHERE _name=?', (name,)).fetchone()
            require(row is not None, 'Native card database asset missing: '+name)
            source = gdt_assets[name][1]
            for key in keys:
                want, got = source[key], row[key]
                if key in ('colorTint', 'colorTint1'):
                    a, b = [float(v) for v in want.split()], [float(v) for v in str(got).split()]
                    same = len(a) == len(b) and all(math.isclose(x, y, abs_tol=1e-6, rel_tol=0) for x, y in zip(a, b))
                else:
                    same = (math.isclose(float(want), float(got), abs_tol=1e-6, rel_tol=0)
                            if key in ('scaleRGB', 'scale', 'noCastShadow', 'noMipMaps', 'noPicMip') else
                            re.sub(r'\\+', '/', str(want)) == re.sub(r'\\+', '/', str(got)))
                require(same, 'Native card binding differs: '+name+'.'+key)
            bindings[name] = {key: row[key] for key in keys}
    return {'model': receipt['model'], 'source_triangles': card['triangles'], 'compiled_triangles': int(compiled['tris0']),
            'asset_ledger_sha256': sha(ledger), 'model_ledger_sha256': sha(model_ledger),
            'input_hashes': card['input_hashes'], 'native_bindings': bindings, 'native_visual_verified': False}
