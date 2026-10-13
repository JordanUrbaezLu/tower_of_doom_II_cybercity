"""Run through Blender MCP: inspect the high-only 4x emission at crown distance."""
import bpy, json, pathlib, sys
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = ROOT / 'art/crown_alarm'
OUT = ART / 'high_crown_review'
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / 'tools/crown_alarm'))
from preview_variants import high_material, apply_high_lamps
profile = json.loads((ROOT / 'tools/crown_alarm/light_profile.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ART / 'crown_alarm.blend'))
scene = bpy.data.scenes['Crown alarm - authored native asset']
bpy.context.window_manager.windows[0].scene = scene
high_material(profile)
scene['alarm_light_profile'] = json.dumps(profile)
bpy.ops.wm.save_as_mainfile(filepath=str(ART / 'crown_alarm.blend'))

bpy.ops.wm.open_mainfile(filepath=str(ART / 'intensity_review/stronger.blend'))
scene = next(s for s in bpy.data.scenes if s.name.startswith('Actual crown'))
bpy.context.window_manager.windows[0].scene = scene
changed = apply_high_lamps(scene, profile)
assert changed == 34, changed  # tube + optic ring on each of 17 high fixtures
high = high_material(profile).node_tree.nodes['Principled BSDF']
hall = bpy.data.materials['mtl_tod_alarm_lamp_on'].node_tree.nodes['Principled BSDF']
assert hall.inputs['Emission Strength'].default_value == profile['lamp_emission']
origin = Vector((0, 8608, 19392))
cam = scene.camera
cam.location = Vector((4500, 3400, 19464)) - origin
cam.rotation_euler = (Vector((0, 9296, 24000)) - origin - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 24
cam.data.clip_end = 100000
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .07
for obj in scene.objects:
    if obj.type == 'LIGHT' and obj.data.type == 'SUN':
        obj.data.energy = .5
scene.render.resolution_x = 1000
scene.render.resolution_y = 1250
scene.render.resolution_percentage = 100
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.use_nodes = True
nodes = scene.node_tree.nodes
nodes.clear()
render = nodes.new('CompositorNodeRLayers')
render.scene = scene
glare = nodes.new('CompositorNodeGlare')
glare.glare_type = 'FOG_GLOW'
glare.quality = 'HIGH'
glare.threshold = 2
glare.size = 6
composite = nodes.new('CompositorNodeComposite')
scene.node_tree.links.new(render.outputs['Image'], glare.inputs['Image'])
scene.node_tree.links.new(glare.outputs['Image'], composite.inputs['Image'])
scene.frame_set(1)
scene['preview_limit'] = 'Blender emission/bloom study on current crown geometry; identical view, phase, fill and exposure. Not native BO3 brightness or bloom calibration.'
for state, strength in [('before', profile['lamp_emission']), ('high_4x', profile['lamp_emission'] * profile['high_lamp_multiplier'])]:
    high.inputs['Emission Strength'].default_value = strength
    scene.render.filepath = str(OUT / (state + '.png'))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (state + '.blend')))
print('HIGH_CROWN_MCP_READY: 17 exterior fixtures x2 emissive pieces; hall unchanged; high emission 36 -> 144')
