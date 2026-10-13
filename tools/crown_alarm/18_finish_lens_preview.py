"""MCP: finish the exported-model preview and inspect rotation with bloom."""
import bpy, hashlib, json, math, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = ROOT / 'tmp/alarm_lens_repair/staged/art/crown_alarm'
REVIEW = ART / 'lens_review'
authored = json.loads((REVIEW / 'authoring.json').read_text())
for name in ('before_off.png', 'before_on.png', 'after_off.png', 'after_on.png', 'distance_off.png', 'distance_on.png'):
    assert hashlib.sha256((REVIEW / name).read_bytes()).hexdigest() == authored['renders'][name], 'Incomplete render set: ' + name
assert hashlib.sha256((REVIEW / 'native_preview.blend').read_bytes()).hexdigest() == authored['pre_finish_preview_sha256'], 'Stale primary-review native scene'
sys.path.insert(0, str(ROOT / 'tools/crown_alarm'))
from surface_realism import xmodel
bpy.ops.wm.open_mainfile(filepath=str(REVIEW / 'native_preview.blend'))
scene = bpy.context.scene
lens = bpy.data.materials['mtl_tod_alarm_lens']
assert lens['preview_specular_mask'] == 0, 'Preview needs the verified stock black scalar mask'
assert all(abs(value - .04) < 1e-7 for value in lens['native_f0']), 'Preview has stale specular optics'
for ob in scene.objects:
    if ob.type == 'MESH' and 'alarm_group' in ob:
        ob.hide_render = True
        ob.hide_viewport = True
model = xmodel.Model()
model.LoadFile_Bin(str(ROOT / 'model_export/tod_crown_alarm/tod_crown_alarm_rotor_off_lod0.xmodel_bin'), split_meshes=True)
names = {'EXPORTED ' + p.name for p in model.meshes}
rotor = bpy.data.objects.new('NATIVE ROTOR - 1.5 seconds per revolution', None)
scene.collection.objects.link(rotor)
rotor.location = (0, 0, 26)
bpy.context.view_layer.update()
native = [ob for ob in scene.objects if ob.type == 'MESH' and ob.name.startswith('EXPORTED ')]
for ob in native:
    if ob.name in names:
        world = ob.matrix_world.copy()
        ob.parent = rotor
        ob.matrix_world = world
for frame, angle in [(1, 0), (37, math.tau)]:
    rotor.rotation_euler.z = angle
    rotor.keyframe_insert(data_path='rotation_euler', frame=frame)
for curve in rotor.animation_data.action.fcurves:
    for key in curve.keyframe_points:
        key.interpolation = 'LINEAR'
    curve.modifiers.new('CYCLES')
scene.frame_start = 1
scene.frame_end = 36
scene.frame_set(10)
for ob in native:
    for slot in ob.material_slots:
        if slot.material.name == 'mtl_tod_alarm_lamp_off':
            slot.material = bpy.data.materials['mtl_tod_alarm_lamp_on']
scene.use_nodes = True
nodes = scene.node_tree.nodes
nodes.clear()
render = nodes.new('CompositorNodeRLayers')
glow = nodes.new('CompositorNodeGlare')
glow.glare_type = 'FOG_GLOW'
glow.threshold = 2
glow.size = 6
glow.quality = 'HIGH'
output = nodes.new('CompositorNodeComposite')
scene.node_tree.links.new(render.outputs['Image'], glow.inputs['Image'])
scene.node_tree.links.new(glow.outputs['Image'], output.inputs['Image'])
scene.render.filepath = str(REVIEW / 'rotation_on_bloom.png')
bpy.ops.render.render(write_still=True)
# Default preview exposes the inside with bloom disabled; F12 can render it,
# and the timeline turns the actual exported rotor with the native cadence.
scene.use_nodes = False
scene.frame_set(1)
for ob in native:
    for slot in ob.material_slots:
        if slot.material.name == 'mtl_tod_alarm_lamp_on':
            slot.material = bpy.data.materials['mtl_tod_alarm_lamp_off']
window = bpy.context.window_manager.windows[0]
area = max(window.screen.areas, key=lambda a: a.width * a.height)
area.type = 'VIEW_3D'
area.spaces.active.shading.type = 'RENDERED'
area.spaces.active.shading.use_scene_lights_render = True
area.spaces.active.shading.use_scene_world_render = True
area.spaces.active.region_3d.view_perspective = 'CAMERA'
scene.cycles.preview_samples = 16
scene['preview_limit'] = 'Imported native meshes and maps; approximate Blender BRDF/bloom. Native appearance and performance await user playtest.'
bpy.ops.wm.save_as_mainfile(filepath=str(REVIEW / 'native_preview.blend'))
receipt = {'actual_native_geometry': True, 'source_meshes_hidden_in_render_and_viewport': True,
           'complete_authoring_receipt_verified': True,
           'authoring_receipt_sha256': hashlib.sha256((REVIEW / 'authoring.json').read_bytes()).hexdigest(),
           'pre_finish_preview_sha256': authored['pre_finish_preview_sha256'],
           'native_preview_sha256': hashlib.sha256((REVIEW / 'native_preview.blend').read_bytes()).hexdigest(),
           'native_specular_mask': 0, 'native_f0': [.04, .04, .04],
           'default_state': 'off, bloom disabled', 'shading': 'RENDERED', 'rotation_seconds': 1.5,
           'bloom_rotation_render_sha256': hashlib.sha256((REVIEW / 'rotation_on_bloom.png').read_bytes()).hexdigest(),
           'native_playtested': False}
(REVIEW / 'preview.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('LENS_PREVIEW_READY', json.dumps(receipt))
