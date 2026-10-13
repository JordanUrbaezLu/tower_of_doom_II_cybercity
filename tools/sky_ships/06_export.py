"""THE SKY FLEET - export every ship in the studio to native BO3 (docs/192).

Writes, deterministically:
  model_export/tod_sky_ships/tod_sky_<ship>.xmodel_bin     one rigid model per hull (tag_origin + tag_eng_<i> per nozzle)
  model_export/tod_sky_ships/tod_sky_rock_<n>.xmodel_bin   one rigid model per asteroid (tag_origin)
  art/sky_ships/staging/tod_sky_ships.gdt                  images + materials + models + colour variants
  art/sky_ships/manifest.json                              sizes, bounds, engine anchors, hashes (read by
                                                           the lane generator, the FX generator and the gates)
The GDT is STAGED outside source_data on purpose: tools/sky_ships/install.py copies it in when no peer build
is running (a half-written GDT in source_data breaks every build's gdtdb step).

Variant models reuse the same xmodel_bin with a skinOverride on the accent neon, so a second colour costs no
geometry. Ships never cast shadows (noCastShadow): a 10,000-unit hull sweeping a moving shadow over the tower
is a separate design decision, not a side effect.
"""
import bpy, sys, importlib, pathlib, json, math
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib
importlib.reload(sky_lib)
from sky_lib import ROOT, EXP, TEX, ART, sha
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel

STAGE = ART / 'staging'
STAGE.mkdir(parents=True, exist_ok=True)
VARIANTS = {                      # ship -> [(model suffix, [(material, replacement), ...])]
    'dreadnought': [('', []), ('_b', [('neon_red', 'neon_cyan')])],
    'hauler':      [('', []), ('_b', [('neon_amber', 'neon_teal'), ('ads', 'ads_b')])],
    'gunship':     [('', []), ('_b', [('neon_magenta', 'neon_green')])],
    'fighter':     [('', []), ('_b', [('neon_cyan', 'neon_orange')])],
}
SURFACE_VERT_BUDGET = 60000       # BO3 xmodel surfaces index with 16 bits: stay clear of 65,535 per material
blocks = []
def block(name, kind, fields):
    blocks.append('\t"' + name + '" ( "' + kind + '.gdf" )\n\t{\n' + ''.join('\t\t"' + k + '" "' + str(v) + '"\n' for k, v in fields.items()) + '\t}\n')

used_mats, records, rocks = {}, [], []
# v3: every engine nozzle is a TAG (tag_eng_<i>, child of tag_origin) at its exhaust plane, turned 180 deg about Z so
# its +X points AFT: the director plays the flame on it (PlayFXOnTag) and the tag follows the ship's SetScale, so the
# flame sits exactly on the nozzle however far the ship is drawn (docs/192 s10). Rocks carry tag_origin only.
AFT = [(-1, 0, 0), (0, -1, 0), (0, 0, 1)]
for col in sorted((c for c in bpy.data.collections if c.name.startswith(('SHIP ', 'ROCK '))), key=lambda c: c.name):
    is_rock = col.name.startswith('ROCK ')
    key = col['rock'] if is_rock else col['ship']
    asset = ('tod_sky_rock_' if is_rock else 'tod_sky_') + key
    mod = xmodel.Model(asset)
    bone = xmodel.Bone('tag_origin'); bone.offset = (0, 0, 0); bone.matrix = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    mod.bones = [bone]
    nozzles = [] if is_rock else json.loads(col.get('nozzles', '[]'))
    for i, (x, y, z, r) in enumerate(nozzles):
        tag = xmodel.Bone('tag_eng_%d' % i, 0)
        tag.offset = (x, y, z)
        tag.matrix = AFT
        mod.bones.append(tag)
    ids, tris, lo, hi = {}, 0, [1e9] * 3, [-1e9] * 3
    verts_by_mat = {}
    for ob in sorted(col.objects, key=lambda o: o.name):
        if ob.type != 'MESH':
            continue
        me = ob.data
        me.calc_loop_triangles()
        mname = me.materials[0].name
        used_mats[mname] = me.materials[0]
        if mname not in ids:
            ids[mname] = len(mod.materials)
            mod.materials.append(xmodel.Material(mname, 'Phong', {}))
        mesh = xmodel.Mesh(ob.name)
        mesh.verts = [xmodel.Vertex(tuple(v.co), [(0, 1.0)]) for v in me.vertices]
        for v in me.vertices:
            for i in range(3):
                lo[i] = min(lo[i], v.co[i]); hi[i] = max(hi[i], v.co[i])
        uv = me.uv_layers.active.data if me.uv_layers.active else None
        for tri in me.loop_triangles:
            p = [me.vertices[i].co for i in tri.vertices]
            longest = max((p[1] - p[0]).length, (p[2] - p[0]).length, (p[2] - p[1]).length)
            if longest < 0.01 or (p[1] - p[0]).cross(p[2] - p[0]).length / longest ** 2 < 0.0006:
                continue                                           # a sliver: the converter drops these anyway
            f = xmodel.Face(len(mod.meshes), ids[mname]); f.indices = []
            for corner in (0, 2, 1):                               # BO3 winding
                li = tri.loops[corner]
                n = me.corner_normals[li].vector.normalized()
                u = uv[li].uv if uv else Vector((0, 0))
                f.indices.append(xmodel.FaceVertex(tri.vertices[corner], tuple(n), (1, 1, 1, 1), (u.x, 1 - u.y)))
            mesh.faces.append(f)
        mod.meshes.append(mesh)
        tris += len(mesh.faces)
        uniq = verts_by_mat.setdefault(mname, set())
        for fc in mesh.faces:
            for fv in fc.indices:
                uniq.add((ob.name, fv.vertex, tuple(round(c, 4) for c in fv.normal), tuple(round(c, 5) for c in fv.uv)))
    over = {mn: len(u) for mn, u in verts_by_mat.items() if len(u) > SURFACE_VERT_BUDGET}
    assert not over, asset + ': a material carries more vertices than one BO3 surface holds: ' + str(over)
    path = EXP / (asset + '.xmodel_bin')
    mod.WriteFile_Bin(str(path), version=7)
    variants = json.loads(col['variants']) if is_rock else VARIANTS[key]
    for suffix, swaps in variants:
        fields = dict(filename='tod_sky_ships/' + asset + '.xmodel_bin', type='rigid', scale=1, CollisionMap='',
                      BulletCollisionLOD='None', physicsPreset='', cullOutDiameter=0, noCastShadow=1, materials='')
        if swaps:
            fields['skinOverride'] = ''.join('mtl_tod_sky_' + a + ' mtl_tod_sky_' + b + '\\r\\n' for a, b in swaps)
            for a, b in swaps:
                assert 'mtl_tod_sky_' + a in ids, asset + ' has no ' + a + ' to swap'
                used_mats['mtl_tod_sky_' + b] = bpy.data.materials['mtl_tod_sky_' + b]
        block(asset + suffix, 'xmodel', fields)
    if is_rock:
        radius = max((v.co.length for ob in col.objects if ob.type == 'MESH' for v in ob.data.vertices), default=0)
        rocks.append(dict(rock=key, models=[asset + s for s, _ in variants], file=path.relative_to(ROOT).as_posix(),
                          sha256=sha(path), triangles=tris, meshes=len(mod.meshes), materials=[m.name for m in mod.materials],
                          bounds=[[round(v, 1) for v in lo], [round(v, 1) for v in hi]], radius=round(radius, 1),
                          veins=bool(col.get('veins', 0)), surface_verts={mn: len(u) for mn, u in sorted(verts_by_mat.items())}))
        continue
    records.append(dict(ship=key, models=[asset + s for s, _ in VARIANTS[key]], file=path.relative_to(ROOT).as_posix(),
                        sha256=sha(path), triangles=tris, meshes=len(mod.meshes), materials=[m.name for m in mod.materials],
                        bounds=[[round(v, 1) for v in lo], [round(v, 1) for v in hi]],
                        length=round(hi[0] - lo[0], 1), half_width=round(max(abs(lo[1]), abs(hi[1])), 1),
                        nozzles=json.loads(col.get('nozzles', '[]')), lights=json.loads(col.get('lights', '[]')),
                        accent=col.get('accent', ''), surface_verts={mn: len(u) for mn, u in sorted(verts_by_mat.items())}))

# ---- materials + images ------------------------------------------------------------------------------
used_imgs = set()
for name in sorted(used_mats):
    d = json.loads(used_mats[name]['bo3'])
    for k in ('colorMap', 'normalMap', 'cosinePowerMap', 'specColorMap'):
        used_imgs.add(d[k])
    emit = float(d['scaleRGB'])
    block(name, 'material', dict(
        surfaceType=d['surfaceType'], template='material.template', materialCategory='Geometry Advanced',
        materialType='lit_emissive_advanced_fullspec', colorMap=d['colorMap'], normalMap=d['normalMap'],
        cosinePowerMap=d['cosinePowerMap'], specColorMap=d['specColorMap'], specMapEnable=1, specColorTint='1 1 1 1',
        colorMap00=d['colorMap'], colorTint='1 1 1 1', colorTint1='1 1 1 1', scaleRGB=emit, emissiveIncompetence=1,
        emissiveFalloff=0, normalHeightScale=1, glossRangeMin=0, glossRangeMax=8,
        specAmount={'hull': 0.5, 'rock': 0.2}.get(d['kind'], 0.1), reflectionProbeAmount={'hull': 0.3, 'rock': 0.05}.get(d['kind'], 0.0),
        textureAtlasRowCount=1, textureAtlasColumnCount=1, usage='<not in editor>'))
SEM = {'_n': ('normalMap', 'compressed', None), '_g': ('glossMap', 'compressed', None), '_s': ('specularMap', 'compressed high color', 'sRGB3chAlpha')}
images = {}
for name in sorted(used_imgs):
    png = TEX / (name + '.png')
    assert png.exists(), 'missing texture ' + name
    sem, comp, core = SEM.get(name[-2:], ('diffuseMap', 'compressed high color', 'sRGB3chAlpha'))
    f = dict(baseImage='model_export/tod_sky_ships/_images/' + name + '.png', imageType='Texture', type='image',
             semantic=sem, streamable=1, compressionMethod=comp)
    if core:
        f['coreSemantic'] = core
    block(name, 'image', f)
    images[name] = sha(png)

gdt = STAGE / 'tod_sky_ships.gdt'
gdt.write_text('{\n' + ''.join(blocks) + '}\n', encoding='utf-8')
manifest = dict(authoring='Blender MCP execute_blender_code (tools/sky_ships/mcp_call.py, port 9890)',
                ships=records, rocks=rocks, images=images, gdt=gdt.relative_to(ROOT).as_posix(), gdt_sha256=sha(gdt),
                zone_lines=['xmodel,' + m for r in records + rocks for m in r['models']], native_verified=False)
(ART / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ART / 'sky_fleet.blend'))
print('SKY_EXPORTED', json.dumps({r['ship']: dict(tris=r['triangles'], length=r['length'], nozzles=len(r['nozzles'])) for r in records}),
      'rocks', json.dumps({r['rock']: dict(tris=r['triangles'], radius=r['radius'], models=r['models']) for r in rocks}),
      'materials', len(used_mats), 'images', len(images))
