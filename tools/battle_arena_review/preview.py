"""THE BATTLE ARENA review (docs/185 v2, THE CRUCIBLE): the room in Blender, before the native build.

What is REAL here: every brush face of the arena as the generator emitted it
(tools/battle_arena_review/review_scene.js), the map's own kit materials and maps (the
shared APPROXIMATE fullspec view, tools/art_cohesion/native_preview.py), the map's
light entities at their origins and colours, the layout's spawn points / arrivals,
and player-eye cameras 60 units over each floor. What is NOT: BO3's lighting bake,
probes, exposure, bloom and the effects; the teleporter on the dais is a labelled
disc. The look in game is the user's call; this is the design review.

    "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe" --background --factory-startup --python tools/battle_arena_review/preview.py

Env: TOD_ARENA_REVIEW_DIR (default art/battle_arena/review), TOD_KIT_ROOT (the repo whose
source_data/tod_surface.gdt + model_export/tod_surface/_images hold the kit; default this repo).
Writes {arrival,pit,ring,undercroft,overview,plan}.png + preview.json in the review dir.
The plan is a SECTION: the near clip cuts the room 330 over the pit (above the dais).
Held while the game or any native compiler runs (tools/dealer_presence/process_guard.py).
"""
from pathlib import Path
import bpy, json, sys, math, os, hashlib
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
KIT_ROOT = Path(os.environ.get('TOD_KIT_ROOT', str(ROOT)))
OUT = Path(os.environ.get('TOD_ARENA_REVIEW_DIR', str(ROOT / 'art/battle_arena/review')))
sys.path.insert(0, str(ROOT / 'tools/dealer_presence'))
from process_guard import check
check()
sys.path.insert(0, str(ROOT / 'tools'))
from art_cohesion.native_preview import fullspec, DESCRIPTION

SCALE = .0254
S = json.loads((OUT / 'scene.json').read_text())
kit = json.loads((ROOT / 'tools/art_cohesion/crown_materials.json').read_text())['materials']
CX, CY, CZ = S['centre']

for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
sc = bpy.context.scene

mats = {}
def kit_mat(name):
    if name not in mats:
        if name.startswith('tod_cc_'):
            mats[name] = fullspec(KIT_ROOT / 'source_data/tod_surface.gdt', name, KIT_ROOT / 'model_export/tod_surface/_images')
        else:
            m = bpy.data.materials.new('Unmapped ' + name); m.use_nodes = True
            m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.05, .05, .06, 1)
            mats[name] = m
    return mats[name]

def flat(name, rgb, emit=0.0, rough=.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough
    if emit:
        p.inputs['Emission Color'].default_value = (*rgb, 1); p.inputs['Emission Strength'].default_value = emit
    return m

def build_world():
    verts, faces, slot_of, uvs, face_mat = [], [], {}, [], []
    for b in S['brushes']:
        for f in b['faces']:
            start = len(verts)
            verts.extend(f['v']); faces.append(list(range(start, len(verts))))
            mat = f['mat']
            if mat not in slot_of: slot_of[mat] = len(slot_of)
            face_mat.append(slot_of[mat])
            size = kit.get(mat.removeprefix('tod_cc_'), {}).get('size', 256)
            axis = max(range(3), key=lambda i: abs(f['n'][i]))
            uvs.append([((v[1] if axis == 0 else v[0]) / size, (v[1] if axis == 2 else v[2]) / size) for v in f['v']])
    me = bpy.data.meshes.new('battle arena world')
    me.from_pydata([tuple(c * SCALE for c in v) for v in verts], [], faces); me.update()
    for mat in slot_of: me.materials.append(kit_mat(mat))
    uv = me.uv_layers.new()
    for poly, s, coord in zip(me.polygons, face_mat, uvs):
        poly.material_index = s
        for li, t in zip(poly.loop_indices, coord): uv.data[li].uv = t
    ob = bpy.data.objects.new(me.name, me); sc.collection.objects.link(ob)
    return ob

KIND = {'gate': (1, .12, .1), 'pit': (1, .55, .1), 'undercroft': (.7, .2, 1), 'ring': (.1, .85, 1), 'landing': (1, .9, .15)}
def build_markers(plan_only):
    obs = []
    for s in S['spawns']:
        rgb = KIND[s['kind']]
        bpy.ops.mesh.primitive_cylinder_add(radius=22 * SCALE, depth=6 * SCALE, location=tuple(v * SCALE for v in (s['org'][0], s['org'][1], s['org'][2] + 4)))
        ob = bpy.context.active_object; ob.name = 'spawn ' + s['kind']
        ob.data.materials.append(flat('Spawn ' + s['kind'], rgb, emit=1.6)); obs.append(ob)
    for a in S['arrivals']:
        bpy.ops.mesh.primitive_cylinder_add(radius=18 * SCALE, depth=6 * SCALE, location=tuple(v * SCALE for v in (a[0], a[1], a[2] + 4)))
        ob = bpy.context.active_object; ob.name = 'arrival'
        ob.data.materials.append(flat('Arrival', (.15, 1, .35), emit=1.6)); obs.append(ob)
    for ob in obs: ob.hide_render = not plan_only
    return obs

def build_teleporter():
    bpy.ops.mesh.primitive_cylinder_add(radius=84 * SCALE, depth=10 * SCALE, location=(CX * SCALE, CY * SCALE, (S['dais_z'] + 5) * SCALE))
    ob = bpy.context.active_object; ob.name = 'placeholder TELEPORTER (tod_teleporter)'
    ob.data.materials.append(flat('Placeholder teleporter', (.2, .9, 1), emit=1.2))
    return ob

def build_lights():
    for L in S['lights']:
        d = bpy.data.lights.new(L['name'], 'POINT')
        d.color = L['color'][:3]
        d.energy = (2 ** (L['stops'] - 8.0)) * (L['radius'] * SCALE) ** 2 * 9
        d.shadow_soft_size = .25
        d.use_custom_distance = True; d.cutoff_distance = L['radius'] * SCALE * 1.4
        o = bpy.data.objects.new(L['name'], d); sc.collection.objects.link(o)
        o.location = tuple(v * SCALE for v in L['origin'])
    world = bpy.data.worlds.new('Night review sky'); world.use_nodes = True; sc.world = world
    bg = world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (.012, .014, .03, 1); bg.inputs[1].default_value = 1.0
    # a soft fill so the review reads (BO3's bake bounces light; Eevee's point lights alone do not)
    fill = bpy.data.lights.new('Review fill (stands in for the bake bounce)', 'SUN'); fill.energy = .25; fill.color = (.85, .8, 1); fill.angle = 1.2
    fo = bpy.data.objects.new(fill.name, fill); sc.collection.objects.link(fo); fo.rotation_euler = (math.radians(35), 0, math.radians(40))

world_ob = build_world()
tele = build_teleporter()
markers = build_markers(plan_only=True)
build_lights()

camd = bpy.data.cameras.new('Player eye'); cam = bpy.data.objects.new(camd.name, camd); sc.collection.objects.link(cam); sc.camera = cam
camd.lens = 16; camd.clip_start = .01; camd.clip_end = 2000
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1600, 900, 100
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = .9
try:
    sc.eevee.use_bloom = True
except AttributeError:
    pass
sc.eevee.taa_render_samples = 48

def look(eye, target):
    e = Vector(tuple(v * SCALE for v in eye)); t = Vector(tuple(v * SCALE for v in target))
    cam.location = e
    cam.rotation_euler = (t - e).to_track_quat('-Z', 'Y').to_euler()

def P(dx, dy, z):   # room-relative -> world
    return (CX + dx, CY + dy, CZ + z)

VIEWS = [
    # name, eye, target, what the player sees
    ('arrival', P(-110, -110, S['dais_z'] + 60), P(-640, -520, 40), 'where the party lands: the dais, a spoke down to the ring, the pit below'),
    ('pit', P(330, -470, 60), P(-120, 150, 260), 'in the pit: the dais on its pillars, the spokes overhead, the ring all round'),
    ('ring', P(-736, 736, S['ring_z'] + 60), P(400, -400, 120), 'the ring\'s NW corner: the running track, a pinwheel stair, the gates below'),
    ('undercroft', P(-40, -300, 60), P(60, 260, 70), 'under the dais: close quarters, the pillars, the spokes\' piers'),
    ('overview', P(-700, -690, 520), P(150, 160, 40), 'from the ceiling corner: the whole crucible'),
]
records = []
for name, eye, target, what in VIEWS:
    look(eye, target)
    camd.type = 'PERSP'; camd.lens = 16; camd.clip_start = .01
    for ob in markers: ob.hide_render = True
    sc.render.filepath = str(OUT / f'{name}.png')
    bpy.ops.render.render(write_still=True)
    records.append({'view': name, 'eye': eye, 'target': target, 'what': what})

# THE PLAN: an orthographic section from above, cut 330 over the pit (the dais and
# everything below it show; the ceiling does not), every spawn point marked by kind.
for ob in markers: ob.hide_render = False
camd.type = 'ORTHO'; camd.ortho_scale = (S['half'] + 140) * 2 * SCALE
cam.location = Vector((CX * SCALE, CY * SCALE, (CZ + 1200) * SCALE)); cam.rotation_euler = (0, 0, 0)
camd.clip_start = (1200 - 330) * SCALE
sc.render.resolution_x, sc.render.resolution_y = 1400, 1400
sc.render.filepath = str(OUT / 'plan.png')
bpy.ops.render.render(write_still=True)
records.append({'view': 'plan', 'cut_z': CZ + 330, 'markers': {k: list(v) for k, v in KIND.items()}, 'arrival': [.15, 1, .35]})

(OUT / 'preview.json').write_text(json.dumps({
    'preview_limit': DESCRIPTION, 'scene_sha256': hashlib.sha256((OUT / 'scene.json').read_bytes()).hexdigest(),
    'map': S['map'], 'views': records}, indent=2) + '\n')
print('BATTLE ARENA REVIEW: rendered', [r['view'] for r in records], '->', OUT)
