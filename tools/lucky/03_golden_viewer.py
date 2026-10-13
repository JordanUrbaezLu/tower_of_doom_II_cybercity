"""Execute through Blender MCP (tools/lucky/mcp_call.py). A LIVE VIEWER for the user: the Golden Zombie as the game
builds it - the horde's real body + head XMODEL_BIN (model_export/tod_cyber_elites, bind pose) painted with the gold
twin images tools/lucky/make_golden.py bakes (albedo, metallic spec, the self-glow map) and gold eyes - in the open
Blender window, the 3D viewport set to RENDERED (EEVEE) with a bloom (compositor Glare) so the golden glow shows.
Orbit with the middle mouse. Nothing is exported; the scene is its own ('Golden Zombie viewer').

The in-game sparkle aura is a particle effect (tod/luck/fx_luck_golden_aura) that Blender cannot play; the viewer shows
the model and its own glow. Emission here ~ the game's colorMap00 x scaleRGB (make_golden.py GLOW x GLOW_SCALE).
"""
import bpy, pathlib, sys
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
BINS = ROOT / 'model_export/tod_cyber_elites'
GOLD = ROOT / 'model_export/tod_lucky/golden'
CH = 'tod_charcoal_mtl_c_zom_dlc3_rus_sentinel_zombie_'
GLOW_STRENGTH = 1.1      # the viewer's stand-in for GLOW_SCALE on the baked glow map = GLOW_SCALE / 2 (make_golden.py:
                         # 2.2 since 2026-09-30; the 6.0 in-game glow, shown here at 3.0, was "way too intense")

old = bpy.data.scenes.get('Golden Zombie viewer')
if old: bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new('Golden Zombie viewer')
bpy.context.window_manager.windows[0].scene = scene   # the window shows this scene (no active-window context over MCP)
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.view_settings.view_transform = 'AgX'
scene.world = bpy.data.worlds.new('golden viewer world'); scene.world.use_nodes = True
bg = scene.world.node_tree.nodes['Background']; bg.inputs[0].default_value = (.015, .017, .022, 1); bg.inputs[1].default_value = 1.0

def image(path):
    return bpy.data.images.load(str(path), check_existing=True)

def gold_mat(k):
    m = bpy.data.materials.new('golden ' + k); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    c = nt.nodes.new('ShaderNodeTexImage'); c.image = image(GOLD / ('i_tod_golden_mtl_%s_s.png' % k))   # the metal's colour = its spec
    nt.links.new(c.outputs['Color'], bs.inputs['Base Color'])
    e = nt.nodes.new('ShaderNodeTexImage'); e.image = image(GOLD / ('i_tod_golden_mtl_%s_e.png' % k))
    nt.links.new(e.outputs['Color'], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = GLOW_STRENGTH
    bs.inputs['Metallic'].default_value = .9; bs.inputs['Roughness'].default_value = .3
    return m

gold = {CH + k: gold_mat(k) for k in ('arms', 'body', 'legs')}
eyes = bpy.data.materials.new('golden eyes'); eyes.use_nodes = True
eb = eyes.node_tree.nodes['Principled BSDF']; eb.inputs['Base Color'].default_value = (1, .76, .18, 1)
eb.inputs['Emission Color'].default_value = (1, .76, .18, 1); eb.inputs['Emission Strength'].default_value = 25

for bin_name in ('tod_charcoal_c_zom_dlc3_zombie_sentinel_body.XMODEL_BIN', 'tod_charcoal_c_zom_dlc4_zombie_charred_head.XMODEL_BIN'):
    m = xmodel.Model(); m.LoadFile_Bin(str(BINS / bin_name), split_meshes=False)
    for k, mesh in enumerate(m.meshes):
        verts = [tuple(v.offset) for v in mesh.verts]
        faces = [tuple(fv.vertex for fv in f.indices) for f in mesh.faces]
        me = bpy.data.meshes.new('golden zombie ' + bin_name[:20] + str(k)); me.from_pydata(verts, [], faces); me.update()
        uvl = me.uv_layers.new(name='UV'); li = 0
        for f in mesh.faces:
            for fv in f.indices:
                uvl.data[li].uv = (fv.uv[0], 1 - fv.uv[1]); li += 1
        for mm in m.materials:
            me.materials.append(gold.get(mm.name) or (eyes if 'eye' in mm.name else gold[CH + 'body']))
        for p, f in zip(me.polygons, mesh.faces):
            p.material_index = f.material_id; p.use_smooth = True
        ob = bpy.data.objects.new('Golden Zombie', me); scene.collection.objects.link(ob)

def area(name, loc, power, size, color):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.size = size; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 0, 40)) - o.location).to_track_quat('-Z', 'Y').to_euler()
area('key', (120, -70, 120), 60000, 90, (1, .95, .88)); area('rim', (-100, 90, 90), 45000, 80, (.7, .8, 1))
fme = bpy.data.meshes.new('floor'); fme.from_pydata([(-300, -300, 0), (300, -300, 0), (300, 300, 0), (-300, 300, 0)], [], [(0, 1, 2, 3)])
floor = bpy.data.objects.new('floor', fme); scene.collection.objects.link(floor)
fm = bpy.data.materials.new('dark floor'); fm.use_nodes = True
fb = fm.node_tree.nodes['Principled BSDF']; fb.inputs['Base Color'].default_value = (.03, .032, .04, 1); fb.inputs['Roughness'].default_value = .35
floor.data.materials.append(fm)

# THE GLOW: a compositor Glare (fog glow) the RENDERED viewport shows live
scene.use_nodes = True
nt = scene.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
rl = nt.nodes.new('CompositorNodeRLayers'); gl = nt.nodes.new('CompositorNodeGlare'); co = nt.nodes.new('CompositorNodeComposite')
try:
    gl.glare_type = 'BLOOM'          # 4.2's bloom (the viewport compositor draws it)
except TypeError:
    gl.glare_type = 'FOG_GLOW'
gl.quality = 'HIGH'; gl.threshold = .6
if hasattr(gl, 'size'): gl.size = 8
nt.links.new(rl.outputs['Image'], gl.inputs['Image']); nt.links.new(gl.outputs['Image'], co.inputs['Image'])

# the viewport: rendered, the compositor on, framed on the zombie from its front-right
eye = Vector((130, -60, 70)); aim = Vector((0, 0, 38))
for window in bpy.context.window_manager.windows:
    for a in window.screen.areas:
        if a.type == 'VIEW_3D':
            sp = a.spaces.active
            sp.shading.type = 'RENDERED'
            sp.shading.use_compositor = 'ALWAYS'
            sp.overlay.show_floor = False; sp.overlay.show_axis_x = False; sp.overlay.show_axis_y = False
            r = sp.region_3d
            r.view_perspective = 'PERSP'
            r.view_location = aim
            r.view_rotation = (aim - eye).to_track_quat('-Z', 'Y')
            r.view_distance = (eye - aim).length
            sp.clip_end = 10000
print('GOLDEN_VIEWER ready: scene "Golden Zombie viewer", viewport RENDERED with bloom')
