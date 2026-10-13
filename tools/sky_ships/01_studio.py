"""THE SKY FLEET studio (docs/192): clear the scene, night-sky viewing, textures + materials.

Run through Blender MCP: <mcp python> tools/sky_ships/mcp_call.py tools/sky_ships/01_studio.py
Every texture is procedural and deterministic: `python tools/sky_ships/make_textures.py` writes them (system
Python, numpy + PIL: the markings use the map's typeface) into model_export/tod_sky_ships/_images; this studio
only loads them by name and builds the materials.
"""
import bpy, sys, importlib, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib
importlib.reload(sky_lib)
from sky_lib import GLOW, EMIT, CARGO, load_image, make_material

# ---- clean slate (this studio only ever holds the fleet) -------------------------------------------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for col in list(bpy.data.collections):
    bpy.data.collections.remove(col)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)
for im in list(bpy.data.images):
    if im.name.startswith('i_tod_sky_'):
        bpy.data.images.remove(im)

scene = bpy.context.scene
scene.name = 'THE SKY FLEET'
scene.unit_settings.system = 'NONE'          # 1 Blender unit = 1 BO3 unit (inch)
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    scene.render.engine = 'BLENDER_EEVEE'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Punchy'

# Night sky: deep indigo, like the Cybercity sky behind the ships.
world = scene.world or bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
bg.inputs[0].default_value = (0.010, 0.012, 0.030, 1)
bg.inputs[1].default_value = 1.0

# Moonlight (cool key from above) + a violet city-glow fill from below: the ships are usually seen
# from below against the night sky, so the fill matters.
def sun(name, rot, energy, color):
    d = bpy.data.lights.new(name, 'SUN')
    d.energy = energy
    d.color = color
    d.angle = 0.05
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.rotation_euler = rot
    o['sky_group'] = 'studio'
sun('Moonlight key', (0.7, 0.15, 0.9), 2.2, (0.72, 0.80, 1.0))
sun('City glow fill (from below)', (3.0, -0.3, -2.2), 0.9, (0.75, 0.45, 1.0))

# Viewport glow so the user watching sees the neon bloom (compositor glare, viewport only).
scene.use_nodes = True
nt = scene.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
rl = nt.nodes.new('CompositorNodeRLayers')
gl = nt.nodes.new('CompositorNodeGlare')
for t in ('BLOOM', 'FOG_GLOW'):
    try:
        gl.glare_type = t
        break
    except Exception:
        pass
gl.threshold = 2.0
gl.size = 6
gl.mix = -0.55                     # a subtle halo: the hull must still read under the neon
comp = nt.nodes.new('CompositorNodeComposite')
nt.links.new(rl.outputs['Image'], gl.inputs['Image'])
nt.links.new(gl.outputs['Image'], comp.inputs['Image'])
for win in bpy.context.window_manager.windows:
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            sp = area.spaces.active
            try:
                sp.shading.use_compositor = 'ALWAYS'
            except Exception:
                pass
            sp.overlay.show_floor = False
            sp.overlay.show_axis_x = False
            sp.overlay.show_axis_y = False

# ---- textures (written by make_textures.py) + materials ---------------------------------------------
for name in ('i_tod_sky_flat_n', 'i_tod_sky_flat_g', 'i_tod_sky_flat_s', 'i_tod_sky_plate_n', 'i_tod_sky_plate2_n',
             'i_tod_sky_plate_g', 'i_tod_sky_plate_s'):
    load_image(name)
for name in ('i_tod_sky_plate2_g','i_tod_sky_plate2_s','i_tod_sky_cargo_n','i_tod_sky_cargo_g','i_tod_sky_cargo_s',
             'i_tod_sky_drive_n','i_tod_sky_drive_g','i_tod_sky_drive_s'):
    load_image(name)
make_material('hull', load_image('i_tod_sky_plate_c'), 'hull', rough=0.45, metal=0.85,
              maps=dict(n='i_tod_sky_plate_n', g='i_tod_sky_plate_g', s='i_tod_sky_plate_s'), viewport_rgb=(0.05, 0.06, 0.08))
make_material('hull2', load_image('i_tod_sky_plate2_c'), 'hull', rough=0.40, metal=0.85,
              maps=dict(n='i_tod_sky_plate2_n', g='i_tod_sky_plate2_g', s='i_tod_sky_plate2_s'), viewport_rgb=(0.16, 0.17, 0.19))
make_material('drive_metal',load_image('i_tod_sky_drive_c'),'hull',rough=.4,metal=1,
              maps=dict(n='i_tod_sky_drive_n',g='i_tod_sky_drive_g',s='i_tod_sky_drive_s'),surface='metal')
make_material('windows', load_image('i_tod_sky_win2_c'), 'glow', emit=EMIT['window'])
make_material('deco', load_image('i_tod_sky_deco_c'), 'glow', emit=EMIT['deco'])
make_material('ads', load_image('i_tod_sky_ads_c'), 'glow', emit=EMIT['ads'])
make_material('ads_b', load_image('i_tod_sky_ads2_c'), 'glow', emit=EMIT['ads'])      # variant B only (skinOverride)
for key, rgb in GLOW.items():
    img = load_image('i_tod_sky_glow_' + key)
    kind = 'engine' if key.startswith('hot_') else 'nav' if key.startswith('nav_') else 'neon'
    make_material(('engine_' if kind == 'engine' else 'nav_' if kind == 'nav' else 'neon_') + key.replace('hot_', '').replace('nav_', ''),
                  img, 'glow', emit=EMIT[kind], viewport_rgb=rgb)
make_material('hangar', bpy.data.images['i_tod_sky_glow_cyan'], 'glow', emit=EMIT['hangar'])
make_material('glass', bpy.data.images['i_tod_sky_glow_amber'], 'glow', emit=EMIT['glass'])
for key, rgb in CARGO.items():
    make_material(key, load_image('i_tod_sky_' + key), 'glow', emit=EMIT['container'], rough=0.5, viewport_rgb=rgb,
                  maps=dict(n='i_tod_sky_cargo_n',g='i_tod_sky_cargo_g',s='i_tod_sky_cargo_s'),surface='metal')

print('SKY_STUDIO_READY', sorted(m.name for m in bpy.data.materials if m.name.startswith('mtl_tod_sky_')))
