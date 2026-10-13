"""THE WAR DAMAGE PASS (docs/205): a before/after review render of one break.

Background Blender only (never an artist's session). The tower is its actual brush
faces with the exported kit materials (tools/art_cohesion/native_preview.py, an
APPROXIMATE fullspec view); the damage is the merged cluster model's real LOD0 with
Treyarch's own colour + normal maps looked up from the stock material GDTs. Neutral
studio light: this checks COMPOSITION and placement, not BO3's lighting.

Usage (from the repo root):
  blender --factory-startup -b --python tools/war_damage/preview_break.py -- <stage dir> <lap>
Writes <stage>/preview/lap<NN>_<view>_{before,after}.png
"""
import bpy, json, math, pathlib, re, sys
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from art_cohesion.native_preview import fullspec  # noqa: E402
from PyCoD import xmodel  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
STAGE, LAP = pathlib.Path(argv[0]), int(argv[1])
OUT = STAGE / 'preview'; OUT.mkdir(parents=True, exist_ok=True)
S = 0.0254
kit_materials = json.loads((ROOT / 'tools/art_cohesion/crown_materials.json').read_text())['materials']
layout = json.loads((STAGE / 'layout.json').read_text())
cluster = next(c for c in layout['clusters'] if c['kind'] == 'break' and LAP in c['laps'])
STOCK_ROOT = pathlib.Path(json.loads((ROOT / 'art/war_damage/kit.json').read_text())['stock_root']).parent
rows = json.loads((STAGE / f'inventory_lap{LAP}.json').read_text())

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
scene = bpy.context.scene

# ---- the tower (exactly tower_preview.py's construction) ----
used = {f['mat'] for row in rows for f in row['faces']}
mats = {name: fullspec(ROOT / 'source_data/tod_surface.gdt', name, ROOT / 'model_export/tod_surface/_images') for name in used}
for row in rows:
    verts, faces, uvs, ids, slots = [], [], [], [], []
    for f in row['faces']:
        name = f['mat']; size = kit_materials[name.removeprefix('tod_cc_')]['size']
        if name not in slots: slots.append(name)
        axis = max(range(3), key=lambda i: abs(f['n'][i])); idx = []
        for p in f['vertices']:
            idx.append(len(verts)); verts.append(tuple(v * S for v in p))
            uvs.append(((p[1] if axis == 0 else p[0]) / size, (p[1] if axis == 2 else p[2]) / size))
        faces.append(idx); ids.append(slots.index(name))
    mesh = bpy.data.meshes.new(row['label']); mesh.from_pydata(verts, [], faces); mesh.update()
    for name in slots: mesh.materials.append(mats[name])
    uv = mesh.uv_layers.new()
    for poly, mi in zip(mesh.polygons, ids):
        poly.material_index = mi
        for li in poly.loop_indices: uv.data[li].uv = uvs[mesh.loops[li].vertex_index]
    scene.collection.objects.link(bpy.data.objects.new(row['label'], mesh))

# ---- stock material lookup: material -> colorMap/normalMap images -> baseImage files ----
_gdt_text = None
def gdt_text():
    global _gdt_text
    if _gdt_text is None:
        parts = []
        for folder in ('model_export', 'source_data', 'texture_assets'):
            for g in (STOCK_ROOT / folder).glob('*.gdt'):
                try: parts.append(g.read_text(encoding='utf-8-sig', errors='ignore'))
                except OSError: pass
        _gdt_text = '\n'.join(parts)
    return _gdt_text
def gdt_fields(name, kind):
    m = re.search(r'"' + re.escape(name) + r'"\s*\(\s*"' + kind + r'\.gdf"\s*\)\s*\{([^}]+)\}', gdt_text())
    return dict(re.findall(r'"([^"\r\n]+)"\s*"([^"\r\n]*)"', m.group(1))) if m else {}
def image_path(asset):
    f = gdt_fields(asset, 'image'); p = f.get('baseImage', '')
    return (STOCK_ROOT / p.replace('\\\\', '/').replace('\\', '/')) if p else None
# The stock "$" colour placeholders are 8x8 16-bit greys (sRGB value / 65535, read off the TIFFs).
PLACEHOLDER = {'$white_diffuse': 65533 / 65535, '$black_color': 0.0, '$color_black_40': 11366 / 65535}
def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def socket(sockets, ident): return next(s for s in sockets if s.identifier == ident)
def stock_material(name):
    mat = bpy.data.materials.new('stock | ' + name); mat.use_nodes = True
    nt, links = mat.node_tree, mat.node_tree.links; bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.62
    f = gdt_fields(name, 'material')
    # The colour: the colorMap, or - when it is a "$" placeholder - the macro colour map the micro-tiled metals carry
    # in colorMap00 (the rebar's rust), else the placeholder's own grey. Then the material's colorTint, as the game does.
    cm = f.get('colorMap', '')
    src = cm if cm and not cm.startswith('$') else (f.get('colorMap00', '') if not f.get('colorMap00', '$').startswith('$') else '')
    col = image_path(src) if src else None
    tint = [float(v) for v in f.get('colorTint', '1 1 1 1').split()[:3]]
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1.0
    socket(mix.inputs, 'B_Color').default_value = (*tint, 1)
    links.new(socket(mix.outputs, 'Result_Color'), bsdf.inputs['Base Color'])
    if col and col.exists():
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(col), check_existing=True)
        if name.startswith('t7_decal'):
            # The decal TIFFs carry their shape in a 4th sample; Blender reads it as associated alpha and divides
            # the colour by it (thin edges blow out WHITE). The game keeps colour and alpha apart: so do we.
            t.image.alpha_mode = 'CHANNEL_PACKED'
        links.new(t.outputs['Color'], socket(mix.inputs, 'A_Color'))
        if 'glass' in name or name.startswith('t7_decal'):
            links.new(t.outputs['Alpha'], bsdf.inputs['Alpha'])
            if hasattr(mat, 'blend_method'): mat.blend_method = 'BLEND'
    else:
        g = lin(PLACEHOLDER.get(cm, 0.5))
        socket(mix.inputs, 'A_Color').default_value = (g, g, g, 1)
        if cm not in PLACEHOLDER: print('WAR_PREVIEW no colour map for', name, '->', cm, col)
    nrm = image_path(f['normalMap']) if f.get('normalMap') else None
    if nrm and nrm.exists():
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(nrm), check_existing=True)
        t.image.colorspace_settings.name = 'Non-Color'
        nm = nt.nodes.new('ShaderNodeNormalMap'); links.new(t.outputs['Color'], nm.inputs['Color']); links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    if 'metal' in name or 'rebar' in name or 'iron' in name:
        bsdf.inputs['Metallic'].default_value = 0.6
    return mat

# ---- the damage: the merged cluster's real LOD0 ----
src = xmodel.Model(); src.LoadFile_Bin(str(STAGE / 'model_export/tod_war_damage' / f"{cluster['name']}_lod0.xmodel_bin"), split_meshes=True)
org = Vector(cluster['org'])
damage = []
for mi, m in enumerate(src.meshes):
    if not m.faces: continue
    name = src.materials[m.faces[0].material_id].name
    verts = [tuple((Vector(v.offset) + org) * S) for v in m.verts]
    faces = [[fv.vertex for fv in f.indices] for f in m.faces]
    mesh = bpy.data.meshes.new(f'damage {name}'); mesh.from_pydata(verts, [], faces); mesh.update()
    mesh.materials.append(stock_material(name))
    uv = mesh.uv_layers.new(); k = 0
    for poly, f in zip(mesh.polygons, m.faces):
        for li, fv in zip(poly.loop_indices, f.indices):
            uv.data[li].uv = (fv.uv[0], 1.0 - fv.uv[1])
    ob = bpy.data.objects.new(f'damage {name}', mesh); scene.collection.objects.link(ob); damage.append(ob)

# ---- light + camera (neutral review studio) ----
world = bpy.data.worlds.new('review'); world.use_nodes = True; scene.world = world
world.node_tree.nodes['Background'].inputs[0].default_value = (.25, .3, .4, 1); world.node_tree.nodes['Background'].inputs[1].default_value = .8
d = bpy.data.lights.new('sun', 'SUN'); d.energy = 3; d.angle = .25
o = bpy.data.objects.new('sun', d); scene.collection.objects.link(o); o.rotation_euler = (.4, -.6, -.7)
b = (LAP - 1) * 384; s = 1 if LAP % 2 else -1
T = lambda x, y, z: Vector((s * x, s * y, z)) * S
for pos, power in [((900, -600, b + 700), 30000), ((500, 300, b + 350), 9000)]:
    a = bpy.data.lights.new('soft', 'AREA'); a.energy = power; a.shape = 'DISK'; a.size = 8
    o = bpy.data.objects.new('soft', a); scene.collection.objects.link(o); o.location = T(*pos)
    o.rotation_euler = (T(336, 0, b) - o.location).to_track_quat('-Z', 'Y').to_euler()
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); scene.collection.objects.link(cam); scene.camera = cam
scene.render.engine = 'CYCLES'; scene.cycles.samples = 32; scene.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for dev in prefs.devices: dev.use = True
    scene.cycles.device = 'GPU'
except Exception as e:
    print('WAR_PREVIEW GPU unavailable, CPU render:', e)
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.view_settings.view_transform = 'AgX'; scene.render.image_settings.file_format = 'PNG'
# The two area lights put ~30 W/m2 on the break: at exposure 0 any albedo over ~0.1 read near-white (the dark decals,
# the rust, the rubber cables) and the deep red tower read pink. Two stops down keeps dark materials dark.
scene.view_settings.exposure = -2.0
views = [
    ('ledge', (336, 380, b + 192 + 64), (336, -40, b + 40), 20),     # on the snapped ledge, looking down the drop
    ('deck', (336, -190, b + 66), (360, 250, b + 160), 20),          # landed on the deck, looking back up
    ('outside', (1050, 380, b + 420), (440, 120, b + 140), 32),      # outside the tower
]
for name, pos, target, lens in views:
    cam.location = T(*pos); cam.rotation_euler = (T(*target) - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens; cd.clip_end = 3000
    for state in ('before', 'after'):
        for ob in damage: ob.hide_render = (state == 'before')
        scene.render.filepath = str(OUT / f'lap{LAP:02d}_{name}_{state}.png'); bpy.ops.render.render(write_still=True)
print('WAR_PREVIEW_DONE lap', LAP, cluster['name'], len(damage), 'damage meshes,', len(rows), 'tower solids')
