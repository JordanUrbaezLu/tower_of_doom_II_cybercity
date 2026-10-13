"""THE WUNDERSTRAHL art GDT (docs/219): writes <out-root>/source_data/tod2_wunderstrahl_art.gdt from the model
track's records. Plain Python (no Blender). The main session lands the staged file (default stage:
tmp/wunderstrahl/stage, repo layout) together with the rest of the pass.

  python tools/wunderstrahl/model/install_art.py            write the staged GDT + art/wunderstrahl/record.json
  python tools/wunderstrahl/model/install_art.py --check    regenerate in memory; fail if the staged GDT differs or
                                                            any referenced file is missing or no longer matches the
                                                            sha256 its record pinned (models, maps, clips, skeleton)
  --out-root <dir>                                          stage root (default tmp/wunderstrahl/stage)

Blocks: image (one per map; colour/emissive/specular sRGB 'compressed high color', gloss/normal linear 'compressed'),
material (materials.py registry - explicit surfaceType on every block, the Cyber Sword's proven fullspec types, the
crown alarm's proven transparent glass recipe), xmodel (tod2_ws_view, tod2_ws_world with seven LODs, tod2_ws_pickup
with two; japaneseUnsafe 0), xanim (the 28 tod2_ws_vm_* clips on tod2_ws_skeleton; every community note stripped;
2D sound notes: tod_ws_raise at frame 0 of first_raise / pullout / pullout_quick, tod_ws_putaway at frame 0 of
putaway / putaway_quick - the ignition sound is the weapon's own startFireSoundPlayer, so the fire clips carry none).
GDT rules: the file starts with a brace, no line starts with //, one asset per name + type, no '.001' names,
names <= 63 characters, CRLF like this repo's other GDTs. The xanim 'model' field is a file path: no skeleton asset.
"""
import argparse, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, materials

GDT_NAME = 'tod2_wunderstrahl_art.gdt'
WORLD_DISTS = (0, 180, 350, 600, 950, 1400, 2100)     # the Cyber Sword's proven world-LOD distances
PICKUP_DIST = 380                                       # the Lucky Clover drop's proven LOD1 distance
RAISE = {'first_raise': 'tod_ws_raise', 'pullout': 'tod_ws_raise', 'pullout_quick': 'tod_ws_raise',
         'putaway': 'tod_ws_putaway', 'putaway_quick': 'tod_ws_putaway'}
BS = '\\\\'   # a GDT path separator: two backslash characters in the file


def gpath(*parts):
    return BS.join(parts)


def image_block(name):
    suffix = name.rsplit('_', 1)[-1]
    semantic, compression, srgb = materials.SUFFIX_IMAGE[suffix]
    f = dict(baseImage=gpath('model_export', 'tod_wunderstrahl', '_images', name + '.png'), imageType='Texture',
             type='image', semantic=semantic, streamable=1, compressionMethod=compression)
    if srgb:
        f['coreSemantic'] = 'sRGB3chAlpha'
    return common.gdt_block(name, 'image.gdf', f)


def material_block(name):
    m = materials.MATERIALS[name]; mp = m['maps']
    mtype = materials.MATERIAL_TYPE[m['kind']]
    f = dict(surfaceType=m['surface'], template='material.template', materialCategory='Geometry Advanced',
             materialType=mtype, colorMap=mp['c'], normalMap=mp['n'], specColorMap=mp['s'], cosinePowerMap=mp['g'])
    if m['kind'] == 'emissive':
        f['colorMap00'] = mp['e']
    elif m['kind'] == 'glass':
        f['colorMap00'] = mp['c']
    f.update(specMapEnable=1, colorTint='1 1 1 1', specColorTint=m.get('spec_tint', '1 1 1 1'), colorTint1='1 1 1 1',
             scaleRGB=m.get('scale', 0), emissiveIncompetence=1, emissiveFalloff=m.get('falloff', 0),
             waterRoughness=0, normalHeightScale=1, glossRangeMin=m['gloss'][0], glossRangeMax=m['gloss'][1],
             specAmount=m['spec_amount'], reflectionProbeAmount=m['probe'], textureAtlasRowCount=1,
             textureAtlasColumnCount=1, usage='<not in editor>')
    if m['kind'] == 'glass':
        f.update(noCastShadow=1, noReceiveDynamicShadow=1)
    return common.gdt_block(name, 'material.gdf', f)


XMODEL_COMMON = dict(arabicUnsafe=0, germanUnsafe=0, japaneseUnsafe=0, BulletCollisionLOD='None', BulletCollisionFile='',
                     CollisionMap='', physicsPreset='', cullOutDiameter=0, cullOutOffsetCP=1, cullOutOffsetMP=1,
                     dropLOD='Auto', materials='', scale=1, skinOverride='', ShadowLOD='Auto', LodColorPriority=0.008,
                     lodNormalPriority=1.54, lodPositionPriority=12, LodUvPriority=3.5, lodPresets='performance',
                     notInEditor=0, doNotUse=0)


def xmodel_blocks():
    out = []
    f = dict(XMODEL_COMMON, filename=gpath('tod_wunderstrahl', 'tod2_ws_view_LOD0.XMODEL_BIN'), type='animated',
             usage_view=1, usage_weapon=1, highLodDist=0)
    out.append(common.gdt_block('tod2_ws_view', 'xmodel.gdf', f))
    f = dict(XMODEL_COMMON, type='animated', usage_view=0, usage_weapon=1)
    keys = ('filename', 'mediumLod', 'lowLod', 'lowestLod', 'lod4File', 'lod5File', 'lod6File')
    dists = ('highLodDist', 'mediumLodDist', 'lowLodDist', 'lowestLodDist', 'lod4Dist', 'lod5Dist', 'lod6Dist')
    for lod, (k, dk) in enumerate(zip(keys, dists)):
        f[k] = gpath('tod_wunderstrahl', 'tod2_ws_world_LOD%d.XMODEL_BIN' % lod); f[dk] = WORLD_DISTS[lod]
    out.append(common.gdt_block('tod2_ws_world', 'xmodel.gdf', f))
    f = dict(XMODEL_COMMON, type='rigid', filename=gpath('tod_wunderstrahl', 'tod2_ws_pickup_LOD0.XMODEL_BIN'),
             mediumLod=gpath('tod_wunderstrahl', 'tod2_ws_pickup_LOD1.XMODEL_BIN'), mediumLodDist=PICKUP_DIST)
    out.append(common.gdt_block('tod2_ws_pickup', 'xmodel.gdf', f))
    return out


def xanim_blocks():
    src = common.parse_gdt(common.SRC_GDT)
    out = []
    for suffix in common.CLIP_SUFFIXES:
        kind, cf = src['vm_dg2_' + suffix]
        assert kind == 'xanim.gdf'
        f = dict(filename=gpath('tod_wunderstrahl', 'tod2_ws_vm_%s.xanim_bin' % suffix),
                 model=gpath('tod_wunderstrahl', 'tod2_ws_skeleton.XMODEL_BIN'),
                 type=cf.get('type', 'relative'), looping=cf.get('looping', '0'), useBones=cf.get('useBones', '0'))
        for k in ('loopsync', 'leftHandGripIK', 'ignoreSpineBones', 'translationError', 'angleError', 'useNtExportFile'):
            if cf.get(k):
                f[k] = cf[k]
        # every community note is dropped (they named stock wpn_tesla_* aliases this map does not ship)
        if suffix in RAISE:
            f.update(customnote0action='2D Sound', customnote0actionparam1=RAISE[suffix], customnote0actionparam2='',
                     customnote0frame=0, customnote0useexistingnote='')
        out.append(common.gdt_block('tod2_ws_vm_' + suffix, 'xanim.gdf', f))
    return out


def generate():
    blocks = [image_block(n) for n in materials.images()]
    blocks += [material_block(n) for n in sorted(materials.MATERIALS)]
    blocks += xmodel_blocks() + xanim_blocks()
    text = '{\n' + ''.join(blocks) + '}\n'
    return text.replace('\r\n', '\n').replace('\n', '\r\n')


def lint(text):
    problems = []
    if not text.startswith('{'):
        problems.append('GDT must start with a brace')
    for i, line in enumerate(text.split('\r\n'), 1):
        if line.lstrip().startswith('//'):
            problems.append('line %d starts with //' % i)
    seen = set()
    for m in common.GDT_BLOCK.finditer(text):
        key = (m.group(1), m.group(2))
        if key in seen:
            problems.append('duplicate asset %s' % (key,))
        seen.add(key)
        if len(m.group(1)) > 63:
            problems.append('name over 63 characters: ' + m.group(1))
        if re.search(r'\.\d{3}$', m.group(1)):
            problems.append('Blender suffix in name: ' + m.group(1))
    parsed = common.parse_gdt_text(text)
    for name, (kind, f) in parsed.items():
        if kind == 'material.gdf':
            if not f.get('surfaceType') or f['surfaceType'] in ('<none>', '<error>'):
                problems.append('material without surfaceType: ' + name)
            mtype = f['materialType']
            for slot in ('colorMap', 'normalMap', 'specColorMap', 'cosinePowerMap', 'colorMap00'):
                img = f.get(slot)
                if not img or img.startswith('$'):
                    continue
                if img not in parsed:
                    problems.append('%s %s -> %s has no image block' % (name, slot, img)); continue
                want = materials.SLOT_USAGE.get((mtype, slot))
                if want and parsed[img][1].get('semantic') != want:
                    problems.append('%s %s -> %s is %s; the techset reads %s' % (name, slot, img, parsed[img][1].get('semantic'), want))
        if kind == 'xanim.gdf':
            notes = {k: v for k, v in f.items() if 'note' in k and v}
            acts = [v for k, v in notes.items() if k.endswith('action')]
            if any(a != '2D Sound' for a in acts):
                problems.append('non-2D note on ' + name)
            for k, v in notes.items():
                if k.endswith('actionparam1') and v not in ('tod_ws_raise', 'tod_ws_putaway'):
                    problems.append('unexpected note alias %s on %s' % (v, name))
    return problems


def referenced_files(text):
    out = []
    for name, (kind, f) in common.parse_gdt_text(text).items():
        if kind == 'image.gdf':
            out.append(common.ROOT / f['baseImage'].replace('\\\\', '/'))
        if kind == 'xmodel.gdf':
            for k in ('filename', 'mediumLod', 'lowLod', 'lowestLod', 'lod4File', 'lod5File', 'lod6File'):
                if f.get(k):
                    out.append(common.OUT.parent / f[k].replace('\\\\', '/'))
        if kind == 'xanim.gdf':
            out.append(common.XOUT.parent / f['filename'].replace('\\\\', '/'))
            out.append(common.OUT.parent / f['model'].replace('\\\\', '/'))
    return out


def pinned_hashes():
    """Every output file the model track pinned when it wrote it."""
    pins = {}
    surf = common.read_json(common.ART / 'surfaces.json')
    for n, h in surf['textures'].items():
        pins[common.IMG / n] = h
    bake = common.read_json(common.KIT / 'bake.json')
    for n, h in bake['textures'].items():
        pins[common.IMG / n] = h
    models = common.read_json(common.KIT / 'models.json')
    for recs in models['models'].values():
        for r in recs:
            pins[common.ROOT / r['file']] = r['sha256']
    for c in models['clips']:
        pins[common.ROOT / c['file']] = c['sha256']
    return pins


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--out-root', default=str(common.STAGE))
    args = ap.parse_args()
    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = common.ROOT / out_root
    gdt = out_root / 'source_data' / GDT_NAME
    text = generate()
    problems = lint(text)
    pins = pinned_hashes()
    files = referenced_files(text)
    for p in files:
        if not p.is_file():
            problems.append('missing referenced file ' + str(p))
        elif p in pins and common.sha(p) != pins[p]:
            problems.append('changed since recorded: ' + common.rel(p))
        elif p not in pins:
            problems.append('referenced file has no pinned hash: ' + common.rel(p))
    if args.check:
        if not gdt.is_file():
            problems.append('staged GDT missing: ' + str(gdt))
        elif gdt.read_bytes() != text.encode('latin1'):
            problems.append('staged GDT differs from a fresh generation: ' + str(gdt))
        if problems:
            print('WUNDERSTRAHL_ART_CHECK_FAIL'); [print('  ' + p) for p in problems]; raise SystemExit(1)
        print('WUNDERSTRAHL_ART_CHECK_OK %d blocks, %d referenced files pinned' % (len(common.parse_gdt_text(text)), len(files)))
        return
    if problems:
        print('WUNDERSTRAHL_ART_INSTALL_FAIL'); [print('  ' + p) for p in problems]; raise SystemExit(1)
    gdt.parent.mkdir(parents=True, exist_ok=True)
    gdt.write_bytes(text.encode('latin1'))
    # the track's input/output receipt
    inv = common.read_json(common.ART / 'source_inventory.json')
    record = dict(
        feature='THE WUNDERSTRAHL (docs/219) - model track', native_built=False, native_playtested=False,
        inputs=inv['inputs'],
        outputs={common.rel(p): common.sha(p) for p in sorted(set(files) | {gdt}) if p.is_file()},
        masters={common.rel(p): common.sha(p) for p in sorted(common.ART.glob('*.blend'))},
        review={common.rel(p): common.sha(p) for p in sorted(common.REVIEW.glob('*.png'))},
        records={common.rel(p): common.sha(p) for p in [common.ART / 'surfaces.json', common.ART / 'design.json',
                 common.KIT / 'atlas.json', common.KIT / 'bake.json', common.KIT / 'models.json']},
        tools={common.rel(p): common.sha(p) for p in sorted(common.TOOL.glob('*.py')) + sorted(common.TOOL.glob('*.ps1')) +
               sorted(common.TOOL.glob('*.sh'))},
        vendor_addon=dict(file='tmp/wunderstrahl/vendor/addon.py', sha256=common.sha(common.ROOT / 'tmp/wunderstrahl/vendor/addon.py')),
        staged_gdt=common.rel(gdt))
    common.write_json(common.ART / 'record.json', record)
    print('WUNDERSTRAHL_ART_INSTALLED %s (%d blocks); record art/wunderstrahl/record.json' % (common.rel(gdt), len(common.parse_gdt_text(text))))


if __name__ == '__main__':
    main()
