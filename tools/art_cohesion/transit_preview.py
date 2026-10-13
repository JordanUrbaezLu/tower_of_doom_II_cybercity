"""THE DEPARTURE HALL review renders (docs/196): the actual emitted map solids +
the shipped teleporter binary, lit by Blender stand-ins for the map's OWN powered
lights (positions, colours and radii read from the .map), under the game's sky.
A preview, not a native bake: BO3's light units, exposure, probes and FX differ.

Blender -b --factory-startup -P tools/art_cohesion/transit_preview.py -- \
    [--sky <sky.exr>] [--sky-gain 568] [--out docs/tower_design/transit] [--tag hall] [--views a,b] [--samples 48]
The inventory comes from tools/art_cohesion/inventory_transit.js (tmp/transit_bay/inventory.json).
The sky is mapped the way the game maps it: the image's centre column = +Y, +X = image right.
"""
import bpy, json, pathlib, sys, math
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[2]
ASSETS = pathlib.Path(__import__('os').environ.get('TOD_ASSET_ROOT', str(ROOT)))   # textures / models (the repo)
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
from art_cohesion.native_preview import fullspec

A = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None):
    return A[A.index(k) + 1] if k in A and A.index(k) + 1 < len(A) else d
SKY = arg('--sky')
SKY_GAIN = float(arg('--sky-gain', '568'))      # finish_sky's in-game display mapping: x10 (sky_intensity_factor) / 0.0176
OUT = pathlib.Path(arg('--out', str(ROOT / 'docs/tower_design/transit')))
TAG = arg('--tag', 'hall')
ONLY = set(arg('--views', '').split(',')) - {''}
SAMPLES = int(arg('--samples', '48'))
OUT.mkdir(parents=True, exist_ok=True)

data = json.loads((ROOT / 'tmp/transit_bay/inventory.json').read_text())
kit = json.loads((ROOT / 'tools/art_cohesion/crown_materials.json').read_text())['materials']
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
scene = bpy.context.scene
scale = .0254
mats = {name: fullspec(ASSETS / 'source_data/tod_surface.gdt', name, ASSETS / 'model_export/tod_surface/_images')
        for name in {f['mat'] for r in data['rows'] for f in r['faces']}}
groups = {'top': [], 'base': []}
for row in data['rows']:
    verts = []; faces = []; uvs = []; ids = []; slots = []
    for f in row['faces']:
        name = f['mat']; size = kit[name.removeprefix('tod_cc_')]['size']
        if name not in slots:
            slots.append(name)
        axis = max(range(3), key=lambda i: abs(f['n'][i])); idx = []
        for p in f['vertices']:
            idx.append(len(verts)); verts.append(tuple(v * scale for v in p))
            uvs.append(((p[1] if axis == 0 else p[0]) / size, (p[1] if axis == 2 else p[2]) / size))
        faces.append(idx); ids.append(slots.index(name))
    me = bpy.data.meshes.new(row['label']); me.from_pydata(verts, [], faces); me.update()
    for name in slots:
        me.materials.append(mats[name])
    uv = me.uv_layers.new()
    for p, mi in zip(me.polygons, ids):
        p.material_index = mi
        for li in p.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    ob = bpy.data.objects.new(row['label'], me); scene.collection.objects.link(ob); groups[row['area']].append(ob)

# the shipped teleporter deck on every pad
pad_mat = fullspec(ASSETS / 'source_data/tod_teleporter.gdt', 'mtl_tod_teleporter', ASSETS / 'model_export/tod_teleporter/_images')
model = xmodel.Model(); model.LoadFile_Bin(str(ASSETS / 'model_export/tod_teleporter/tod_teleporter_lod0.xmodel_bin'), split_meshes=True)
pad_meshes = []
for source in model.meshes:
    me = bpy.data.meshes.new('Shipped teleporter mesh ' + source.name)
    me.from_pydata([tuple(v * scale for v in p.offset) for p in source.verts], [], [[f.indices[i].vertex for i in (0, 2, 1)] for f in source.faces]); me.update(); me.materials.append(pad_mat)
    uv = me.uv_layers.new(); normals = []
    for p, f in zip(me.polygons, source.faces):
        p.use_smooth = True
        for li, i in zip(p.loop_indices, (0, 2, 1)):
            c = f.indices[i]; uv.data[li].uv = (c.uv[0], 1 - c.uv[1]); normals.append(c.normal)
    me.normals_split_custom_set(normals); pad_meshes.append(me)
for r in data['routes']:
    if not (r['id'].startswith('top_to_') or r['id'] == 'base_to_crown'):
        continue
    area = 'top' if r['id'].startswith('top_to_') else 'base'
    for me in pad_meshes:
        ob = bpy.data.objects.new('Pad ' + r['id'], me); scene.collection.objects.link(ob)
        ob.location = Vector((r['src'][0], r['src'][1], 0)) * scale; groups[area].append(ob)

# THE WORLD: the game's sky for camera rays (its in-game display gain), a dim
# neutral night fill for everything it lights.
world = bpy.data.worlds.new('Sky'); world.use_nodes = True; scene.world = world
nt = world.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputWorld')
fill = nt.nodes.new('ShaderNodeBackground'); fill.inputs[0].default_value = (.20, .23, .34, 1); fill.inputs[1].default_value = .35
if SKY:
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(-90))   # Blender's equirect centre faces +X (Cycles: u = 0.5 - atan2(y,x)/2pi); the game's faces +Y
    env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(SKY)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    sky = nt.nodes.new('ShaderNodeBackground'); nt.links.new(env.outputs['Color'], sky.inputs['Color']); sky.inputs[1].default_value = SKY_GAIN
    lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0]); nt.links.new(fill.outputs[0], mix.inputs[1]); nt.links.new(sky.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], outn.inputs['Surface'])
else:
    nt.links.new(fill.outputs[0], outn.inputs['Surface'])

# the map's own powered lights as Blender point lights (colour + a radius-scaled power)
for L in data.get('lights', []):
    d = bpy.data.lights.new('Map light ' + L['name'], 'POINT')
    d.color = tuple(max(0.0, min(1.0, c)) for c in L['color'][:3])
    d.energy = 2.2 * (L['radius'] * scale) ** 2 * 40 * (2 ** (L['stops'] - 8.5))
    d.shadow_soft_size = 0.3; d.use_custom_distance = True; d.cutoff_distance = L['radius'] * scale * 1.3
    ob = bpy.data.objects.new(d.name, d); scene.collection.objects.link(ob)
    ob.location = Vector(L['org']) * scale; groups['top'].append(ob)
# a soft moon key so the exterior reads (the game's sun is dim and red-tinted)
sun = bpy.data.lights.new('Moon key', 'SUN'); sun.energy = .6; sun.color = (1, .78, .74); sun.angle = .2
ob = bpy.data.objects.new(sun.name, sun); scene.collection.objects.link(ob); ob.rotation_euler = (math.radians(55), 0, math.radians(140))

camd = bpy.data.cameras.new('Review camera'); cam = bpy.data.objects.new(camd.name, camd); scene.collection.objects.link(cam); scene.camera = cam
scene.render.engine = 'CYCLES'; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for dev in prefs.devices:
        dev.use = dev.type == 'OPTIX'
    scene.cycles.device = 'GPU'
except Exception:
    pass
scene.render.resolution_x = 1600; scene.render.resolution_y = 900; scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'; scene.view_settings.exposure = 0.0; scene.render.image_settings.file_format = 'PNG'

# name, area, camera (x,y,z) in map units (z above the hall floor), target, ortho size (0 = perspective), lens (mm), hidden label prefixes
VIEWS = [
    ('entrance', 'top', (-470, 360, 62), (-1640, 360, 150), 0, 16, ()),        # standing in the door: down the axis to the window + the sign
    ('crossing_n', 'top', (-1080, 250, 62), (-1080, 900, 140), 0, 16, ()),     # from the crossing into gate 10
    ('crossing_s', 'top', (-1080, 470, 62), (-1080, -200, 140), 0, 16, ()),    # into gate 30
    ('apse', 'top', (-1290, 470, 62), (-1640, 300, 160), 0, 16, ()),           # gate 20 and the window
    ('up', 'top', (-1000, 420, 60), (-1080, 360, 520), 0, 14, ()),             # looking up through the oculus
    ('aerial', 'top', (400, 1400, 1500), (-1000, 360, 60), 0, 20, ()),         # the jump approach: the hall beside the terrace
    ('under', 'top', (-500, -700, -1100), (-1080, 360, -100), 0, 20, ()),      # from below (the spiral's view up)
    ('plan', 'top', (-1060, 360, 2600), (-1060, 360.1, 0), 1500, 20, ()),      # the plan, straight down
    ('facade', 'top', (-150, 330, 70), (-500, 360, 180), 0, 18, ()),           # the front door, from the terrace
    ('landing', 'top', (60, 1080, 170), (-900, 300, 150), 0, 18, ()),           # stepping off the jump pad's landing deck
]
for name, area, pos, target, ortho, lens, hide in VIEWS:
    if ONLY and name not in ONLY:
        continue
    for group, objects in groups.items():
        for ob in objects:
            ob.hide_render = group != area
    cam.location = Vector(pos) * scale
    cam.rotation_euler = (Vector(target) * scale - cam.location).to_track_quat('-Z', 'Y').to_euler()
    camd.type = 'ORTHO' if ortho else 'PERSP'; camd.ortho_scale = (ortho or 1950) * scale; camd.lens = lens; camd.clip_end = 4000
    scene.render.filepath = str(OUT / f'{TAG}_{name}.png'); bpy.ops.render.render(write_still=True)
    print('RENDERED', name, flush=True)
scene['preview_limit'] = 'Actual emitted map solids, shipped pad mesh, the map lights as Blender stand-ins, the game sky; not a native bake.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'tmp/transit_bay/transit_review.blend'))
print('TRANSIT_PREVIEW_DONE', len(data['rows']), 'solids', len(data.get('lights', [])), 'lights', flush=True)
