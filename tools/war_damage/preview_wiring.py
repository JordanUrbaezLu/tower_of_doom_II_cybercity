"""THE WAR DAMAGE PASS, phase 2 (docs/205 s7): a review render of the blast's wiring.

Background Blender only. The two torn conduit bodies (build_conduit_torn.py) with their conductor twins (a: ON, b: OFF),
a fray cable at b's torn mouth, and the dangling LED fixture, all on a plain wall in the orientation layout.js uses
(the strip's local +X up the wall, +Z out of it; the fixture hanging from its top bracket, tilted). Neutral studio
light: this checks the SHAPES and the frame (the conductors sit inside the body they were torn with), not BO3's look.

Usage: blender --factory-startup -b --python tools/war_damage/preview_wiring.py -- <out dir>
Writes <out dir>/wiring_front.png and wiring_side.png.
"""
import bpy, json, math, pathlib, sys
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel  # noqa: E402

OUT = pathlib.Path(sys.argv[sys.argv.index('--') + 1]); OUT.mkdir(parents=True, exist_ok=True)
S = 0.0254
KIT = json.loads((ROOT / 'art/war_damage/kit.json').read_text())
STOCK = pathlib.Path(KIT['stock_root'])
COLOURS = {
    'mtl_tod_conduit_shell': (0.18, 0.19, 0.21, 1), 'mtl_tod_conduit_steel': (0.55, 0.56, 0.58, 1), 'mtl_tod_conduit_rubber': (0.03, 0.03, 0.03, 1),
    'mtl_tod_conduit_wire_off': (0.02, 0.10, 0.12, 1), 'mtl_tod_conduit_wire_on': (0.2, 0.9, 1.0, 1),
    'mtl_p7_light_fixture_led_ceiling_01_dmg': (0.6, 0.6, 0.62, 1), 'mtl_p7_light_fixture_led_ceiling_01_bulbs': (0.95, 0.98, 1.0, 1),
    't7_plastic_panel_cables': (0.25, 0.25, 0.27, 1), 'mtl_p7_wires_electrical_rubber': (0.05, 0.05, 0.05, 1),
}
EMIT = {'mtl_tod_conduit_wire_on': 6.0, 'mtl_p7_light_fixture_led_ceiling_01_bulbs': 1.5}


def rotate(v, angles):                                   # layout.js rotate(): roll about X, pitch about Y, yaw about Z
    p, y, r = [math.radians(a) for a in angles]
    x0, y0, z0 = v
    a = (x0, y0 * math.cos(r) - z0 * math.sin(r), y0 * math.sin(r) + z0 * math.cos(r))
    b = (a[0] * math.cos(p) + a[2] * math.sin(p), a[1], -a[0] * math.sin(p) + a[2] * math.cos(p))
    return (b[0] * math.cos(y) - b[1] * math.sin(y), b[0] * math.sin(y) + b[1] * math.cos(y), b[2])


def material(name):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = COLOURS.get(name, (0.5, 0.5, 0.5, 1))
    bsdf.inputs['Roughness'].default_value = 0.45 if 'steel' in name or 'shell' in name else 0.7
    if 'steel' in name or 'shell' in name:
        bsdf.inputs['Metallic'].default_value = 0.8
    if name in EMIT:
        bsdf.inputs['Emission Color'].default_value = COLOURS[name]
        bsdf.inputs['Emission Strength'].default_value = EMIT[name]
    return m


def place(path, org, angles, scale=(1, 1, 1), label='x'):
    src = xmodel.Model(); src.LoadFile_Bin(str(path), split_meshes=True)
    for mi, m in enumerate(src.meshes):
        if not m.faces:
            continue
        name = src.materials[m.faces[0].material_id].name
        verts = [tuple((Vector(rotate((v.offset[0] * scale[0], v.offset[1] * scale[1], v.offset[2] * scale[2]), angles)) + Vector(org)) * S) for v in m.verts]
        faces = [[fv.vertex for fv in f.indices] for f in m.faces]
        mesh = bpy.data.meshes.new(f'{label} {name}'); mesh.from_pydata(verts, [], faces); mesh.update()
        mesh.materials.append(material(name))
        ob = bpy.data.objects.new(f'{label} {name}', mesh); bpy.context.scene.collection.objects.link(ob)


for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
scene = bpy.context.scene
# the wall: x = 0 plane facing +X, 300 x 260 units; a floor 170 below
bpy.ops.mesh.primitive_plane_size = None if False else None
wall = bpy.data.meshes.new('wall'); wall.from_pydata([tuple(Vector(p) * S) for p in [(0, -150, -170), (0, 150, -170), (0, 150, 90), (0, -150, 90)]], [], [[0, 1, 2, 3]]); wall.update()
wall.materials.append(material('wall')); bpy.data.materials['wall'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.12, 0.13, 0.17, 1)
scene.collection.objects.link(bpy.data.objects.new('wall', wall))

torn = json.loads((ROOT / 'art/war_damage/conduit_torn.json').read_text())
EXP = ROOT / 'model_export/tod_war_damage'
ANG = (-90, 180, 0)                                       # local +X up the wall, +Z out of it (layout.js tornConduit)
assert all(abs(a - b) < 1e-6 for a, b in zip(rotate((1, 0, 0), ANG), (0, 0, 1))) and all(abs(a - b) < 1e-6 for a, b in zip(rotate((0, 0, 1), ANG), (1, 0, 0)))
place(EXP / 'kit/tod_war_conduit_torn_a_lod0.xmodel_bin', (0.3, 70, 0), ANG, label='body a')
place(EXP / 'tod_war_conductor_a_on_lod0.xmodel_bin', (0.3, 70, 0), ANG, label='conductors a on')
place(EXP / 'kit/tod_war_conduit_torn_b_lod0.xmodel_bin', (0.3, -10, 0), ANG, label='body b')
place(EXP / 'tod_war_conductor_b_off_lod0.xmodel_bin', (0.3, -10, 0), ANG, label='conductors b off')
mouth = Vector((0.3, -10, 0)) + Vector(rotate(torn['variants']['b']['free_end'], ANG))
place(STOCK / KIT['props']['p7_wires_electrical_rubber_04']['lods']['0'], (mouth.x - 2, mouth.y, mouth.z + 1), (0, 110, -90), (0.6, 0.5, 0.6), label='fray')
phi = -22.0
down = (0, math.sin(math.radians(phi)), -math.cos(math.radians(phi)))
FIX = (-phi, 90, -90)
assert all(abs(a - b) < 1e-6 for a, b in zip(rotate((0, 0, 1), FIX), (-1, 0, 0))) and all(abs(a - b) < 1e-6 for a, b in zip(rotate((0, 1, 0), FIX), down))
top = Vector((0.4, -100, 60))
place(STOCK / KIT['props']['p7_light_fixture_led_ceiling_01_dmg']['lods']['0'], tuple(top + Vector(down) * 30.3), FIX, label='fixture')

world = bpy.data.worlds.new('review'); world.use_nodes = True; scene.world = world
world.node_tree.nodes['Background'].inputs[0].default_value = (.3, .35, .45, 1); world.node_tree.nodes['Background'].inputs[1].default_value = .7
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 2.5; sun.angle = .3
so = bpy.data.objects.new('sun', sun); scene.collection.objects.link(so); so.rotation_euler = (.9, .3, .6)
cd = bpy.data.cameras.new('cam'); cd.lens = 40; cam = bpy.data.objects.new('cam', cd); scene.collection.objects.link(cam); scene.camera = cam
scene.render.engine = 'CYCLES'; scene.cycles.samples = 48; scene.cycles.use_denoising = True
try:
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'OPTIX'; scene.cycles.device = 'GPU'
except Exception as e:
    print('WIRING_PREVIEW CPU render:', e)
scene.render.resolution_x, scene.render.resolution_y = 1280, 800
scene.view_settings.view_transform = 'AgX'; scene.render.image_settings.file_format = 'PNG'
for name, pos, target in [('front', (210, -10, 20), (10, -15, 5)), ('side', (120, 160, 50), (10, -20, 0))]:
    cam.location = Vector(pos) * S
    d = Vector(target) * S - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(OUT / f'wiring_{name}.png'); bpy.ops.render.render(write_still=True)
print('WIRING_PREVIEW done ->', OUT)
