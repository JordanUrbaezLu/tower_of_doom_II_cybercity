"""Execute through Blender MCP (tools/lucky/mcp_call.py). PREVIEW ONLY: the Golden Zombie in its gold twin textures
(tools/lucky/make_golden.py), beside the ordinary charcoal horde zombie in its own, in the same light.

Reads the horde's real body + head XMODEL_BIN (model_export/tod_cyber_elites, bind pose) and paints each material slot
with the image make_golden.py baked for it (gold) or the donor's colour image (charcoal). Nothing here is exported.
Writes art/lucky/golden_preview.png. The studio's saved lucky.blend is not touched (a fresh scene is used and discarded).
"""
import bpy, pathlib, sys
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
OUT = ROOT / 'art/lucky'
BINS = ROOT / 'model_export/tod_cyber_elites'
GOLD = ROOT / 'model_export/tod_lucky/golden'
CHAR = ROOT / 'model_export/tod_cyber_elites/images'
CH = 'tod_charcoal_mtl_c_zom_dlc3_rus_sentinel_zombie_'

scene = bpy.data.scenes.new('Golden zombie preview')
# (the render op takes the scene by name: no window switch, which an MCP call may not have)
scene.render.engine = 'CYCLES'; scene.cycles.samples = 48; scene.cycles.use_denoising = True
scene.render.resolution_x = 1400; scene.render.resolution_y = 1000
scene.view_settings.view_transform = 'AgX'
scene.world = bpy.data.worlds.new('preview world'); scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.09, .1, .12, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .6

def image(path):
    im = bpy.data.images.load(str(path), check_existing=True); return im

def mat(name, color_png, spec_png=None, glow_png=None, metal=0.0, rough=.55, glow=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = image(color_png); nt.links.new(t.outputs['Color'], bs.inputs['Base Color'])
    if spec_png:   # BO3 spec/gloss metal: coloured spec -> read it as the metal's colour
        s = nt.nodes.new('ShaderNodeTexImage'); s.image = image(spec_png); nt.links.new(s.outputs['Color'], bs.inputs['Base Color'])
    bs.inputs['Metallic'].default_value = metal; bs.inputs['Roughness'].default_value = rough
    if glow_png and glow:
        e = nt.nodes.new('ShaderNodeTexImage'); e.image = image(glow_png)
        nt.links.new(e.outputs['Color'], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = glow
    return m

gold = {CH + k: mat('gold ' + k, GOLD / ('i_tod_golden_mtl_%s_c.png' % k), GOLD / ('i_tod_golden_mtl_%s_s.png' % k),
                    GOLD / ('i_tod_golden_mtl_%s_e.png' % k), metal=.85, rough=.32, glow=.6) for k in ('arms', 'body', 'legs')}
char = {CH + k: mat('charcoal ' + k, CHAR / ('i_tod_charcoal_mtl_c_zom_dlc3_rus_sentinel_zombie_%s.png' % k)) for k in ('arms', 'body', 'legs')}
eye_gold = bpy.data.materials.new('gold eyes'); eye_gold.use_nodes = True
eg = eye_gold.node_tree.nodes['Principled BSDF']; eg.inputs['Emission Color'].default_value = (1, .76, .18, 1); eg.inputs['Emission Strength'].default_value = 8
eye_red = bpy.data.materials.new('red eyes'); eye_red.use_nodes = True
er = eye_red.node_tree.nodes['Principled BSDF']; er.inputs['Emission Color'].default_value = (1, 0, 0, 1); er.inputs['Emission Strength'].default_value = 8

def load(bin_name, x, skins, eyes):
    m = xmodel.Model(); m.LoadFile_Bin(str(BINS / bin_name), split_meshes=False)
    for k, mesh in enumerate(m.meshes):
        verts = [tuple(v.offset) for v in mesh.verts]
        faces = [tuple(fv.vertex for fv in f.indices) for f in mesh.faces]
        me = bpy.data.meshes.new(bin_name + str(k)); me.from_pydata(verts, [], faces); me.update()
        uvl = me.uv_layers.new(name='UV')
        li = 0
        for f in mesh.faces:
            for fv in f.indices:
                uvl.data[li].uv = (fv.uv[0], 1 - fv.uv[1]); li += 1
        names = [m.materials[i].name for i in range(len(m.materials))]
        for n in names:
            me.materials.append(skins.get(n) or (eyes if 'eye' in n else skins.get(CH + 'body')))
        for p, f in zip(me.polygons, mesh.faces):
            p.material_index = f.material_id; p.use_smooth = True
        ob = bpy.data.objects.new(bin_name + str(k), me); scene.collection.objects.link(ob); ob.location = (0, x, 0)
for bin_name in ('tod_charcoal_c_zom_dlc3_zombie_sentinel_body.XMODEL_BIN', 'tod_charcoal_c_zom_dlc4_zombie_charred_head.XMODEL_BIN'):
    load(bin_name, -22, gold, eye_gold)
    load(bin_name, 22, char, eye_red)

def area(name, loc, power, size, color):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.size = size; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 0, 40)) - o.location).to_track_quat('-Z', 'Y').to_euler()
area('key', (120, -60, 110), 90000, 80, (1, .97, .92)); area('rim', (-90, 90, 90), 60000, 70, (.75, .85, 1))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (150, -30, 58); cam.rotation_euler = (Vector((0, 0, 38)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 110
scene.render.filepath = str(OUT / 'golden_preview.png'); bpy.ops.render.render(write_still=True, scene=scene.name)
print('GOLDEN_PREVIEW', str(OUT / 'golden_preview.png'))
bpy.data.scenes.remove(scene)
