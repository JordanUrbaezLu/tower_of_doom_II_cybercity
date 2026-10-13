"""MCP authoring: shared graphite material and true foreground holdout for the native title.

This is a Blender material bake from the immutable approved painting and authored
city geometry. Pixel coordinates/alpha are never painted or manipulated in Python.
The isolated render scene is written without changing the editable sky master.
"""
import json
import math
import pathlib
import sys
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pass_config import STAGE, REVIEW, sha, source_hashes
sys.path.insert(0, str(ROOT / 'tools/sky3d'))
import cyber_hero_title as title

author = json.loads((STAGE / 'author.json').read_text(encoding='utf-8'))
assert author['source_hashes'] == source_hashes(), 'Regenerate sky master before native card bake'
source_scene = bpy.context.scene
gate_obj = next(o for o in source_scene.objects if o.name.startswith(title.PREFIX + 'authored_gate'))
report = json.loads((STAGE / 'raw_4096.title.json').read_text(encoding='utf-8'))
assert report['sign_state'] == 'dull'
old = bpy.data.scenes.get('Native sign material bake')
if old:
    bpy.data.scenes.remove(old)
sc = bpy.data.scenes.new('Native sign material bake')
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64
sc.cycles.use_denoising = False
sc.cycles.transparent_max_bounces = 64
sc.render.resolution_x, sc.render.resolution_y = title.IMAGE_SIZE
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.color_depth = '8'
sc.render.image_settings.compression = 30
sc.render.filepath = str(STAGE / 'native_card_finished.png')
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0
sc.view_settings.gamma = 1
sc.display_settings.display_device = 'sRGB'
sc.world = bpy.data.worlds.new('Native card transparent black world')
sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0

image = next(n.image for n in gate_obj.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE')
material = title._material(image, dict(sat=1.0, sign_state='lit'), 'unused_native_card')
material.name = 'Native sign shared graphite / source alpha'
nodes, links = material.node_tree.nodes, material.node_tree.links
emission = nodes['Authored metal relief and local glow']
finished_colour = nodes['Shared city metal finish / unchanged title lights'].outputs['Color']
# Native scaleRGB=16 is the requested bright tube level. Prelit frame metal is
# reflected light, so giving it the same gain destroys its graphite relief in
# the established preview bracket. Protect lettering and colored channels with
# the shared lettering mask; bright saturated tube cores keep full strength.
# Colored spill on metal remains reflected light, not another glowing tube.
frame_scale = nodes.new('ShaderNodeVectorMath')
frame_scale.name = 'Native reflected frame response'
frame_scale.operation = 'SCALE'
frame_scale.inputs['Scale'].default_value = 0.06
links.new(finished_colour, frame_scale.inputs[0])
chroma = nodes.new('ShaderNodeMapRange')
chroma.clamp = True
chroma.interpolation_type = 'SMOOTHSTEP'
chroma.inputs['From Min'].default_value = 0.35
chroma.inputs['From Max'].default_value = 0.75
links.new(nodes['Relative chroma'].outputs[0], chroma.inputs['Value'])
tube = nodes.new('ShaderNodeMath'); tube.operation = 'MULTIPLY'
links.new(chroma.outputs['Result'], tube.inputs[0])
links.new(nodes['Smooth neon highlight gate'].outputs['Result'], tube.inputs[1])
reflected = nodes.new('ShaderNodeMath'); reflected.operation = 'SUBTRACT'
reflected.inputs[0].default_value = 1
links.new(tube.outputs[0], reflected.inputs[1])
frame_mask = nodes.new('ShaderNodeMath'); frame_mask.operation = 'MULTIPLY'
links.new(nodes['Architectural frame'].outputs[0], frame_mask.inputs[0])
links.new(reflected.outputs[0], frame_mask.inputs[1])
frame_mix = nodes.new('ShaderNodeMixRGB')
frame_mix.name = 'Native frame versus protected title lights'
links.new(frame_mask.outputs[0], frame_mix.inputs[0])
links.new(finished_colour, frame_mix.inputs[1])
links.new(frame_scale.outputs['Vector'], frame_mix.inputs[2])
links.new(frame_mix.outputs['Color'], emission.inputs['Color'])
for link in list(emission.inputs['Strength'].links):
    links.remove(link)
emission.inputs['Strength'].default_value = 1.0
card = gate_obj.copy()
card.data = gate_obj.data.copy()
card.data.materials.clear()
card.data.materials.append(material)
sc.collection.objects.link(card)

holdout = bpy.data.materials.new('Native card foreground architecture holdout')
holdout.use_nodes = True
holdout.node_tree.nodes.clear()
h = holdout.node_tree.nodes.new('ShaderNodeHoldout')
o = holdout.node_tree.nodes.new('ShaderNodeOutputMaterial')
holdout.node_tree.links.new(h.outputs[0], o.inputs['Surface'])
solid_names = {'city_facades', 'city_roofs', 'city_struct', 'city_neon', 'city_crystal',
               'city_cyber_armour', 'city_cyber_decks', 'city_screens', 'city_trails',
               'city_ribbons', 'ground', 'water', 'podium_canal', 'origin_island'}
occluders = []
for ob in source_scene.objects:
    if ob.type != 'MESH' or ob.hide_render:
        continue
    if ob.name not in solid_names and not ob.name.startswith('sky3d_cyber_station'):
        continue
    dup = ob.copy()
    # Material slots belong to this OBJECT, leaving the shared sky mesh untouched.
    sc.collection.objects.link(dup)
    for slot in dup.material_slots:
        slot.link = 'OBJECT'
        slot.material = holdout
    occluders.append(ob.name)

camera_data = bpy.data.cameras.new('Exact approved sign pixel projection')
camera = bpy.data.objects.new('Exact approved sign pixel projection', camera_data)
sc.collection.objects.link(camera)
sc.camera = camera
camera.location = (0, 0, 220)
el = math.radians(report['title_anchor_deg'][1])
direction = Vector((0, math.cos(el), math.sin(el)))
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
camera_data.sensor_fit = 'HORIZONTAL'
camera_data.sensor_width = 36
camera_data.lens = 36 / (2 * math.tan(math.radians(report['reference_width_deg'] / 2)))
camera_data.shift_x = 0
camera_data.shift_y = (title.TITLE_CENTER_PX[1] - title.IMAGE_SIZE[1] / 2) / title.REFERENCE_WIDTH
camera_data.clip_start, camera_data.clip_end = 0.1, 30000
camera.matrix_world = camera.matrix_basis.copy()
right, up = Vector((1, 0, 0)), Vector((0, -math.sin(el), math.cos(el)))
center = camera.location + direction * report['distance_m']
scale = report['metres_per_pixel']
projected = []
for u, v in ((0, 0), (1536, 0), (1536, 1024), (0, 1024), title.TITLE_CENTER_PX):
    point = center + right * ((u - title.TITLE_CENTER_PX[0]) * scale) + up * ((title.TITLE_CENTER_PX[1] - v) * scale)
    ndc = world_to_camera_view(sc, camera, point)
    observed = [ndc.x * 1536, (1 - ndc.y) * 1024]
    assert max(abs(observed[0] - u), abs(observed[1] - v)) < 0.002, (u, v, observed)
    projected.append(dict(source=[u, v], projected=observed))

blend = STAGE / 'native_card_bake.blend'
bpy.data.libraries.write(str(blend), {sc}, path_remap='ABSOLUTE', fake_user=True, compress=True)
receipt = dict(schema=1, author='real upstream Blender MCP', source_png=title.SOURCE_IMAGE,
               source_png_sha256=sha(ROOT / title.SOURCE_IMAGE), sky_source_hashes=source_hashes(),
               sky_master_sha256=author['blend_sha256'], authoring_script_sha256=sha(pathlib.Path(__file__)),
               blend=str(blend.relative_to(ROOT)), blend_sha256=sha(blend),
               output='tmp/sky_consistency/native_card_finished.png',
               material='shared frame compression 2; lettering/colored light protected; native scale supplied by GDT',
               native_frame_response=0.06,
               native_frame_note='Reflected graphite and colored spill use .06; shared lettering region and bright saturated tube cores keep native16. Native visual calibration unverified.',
               colour_encoding='Blender Standard / sRGB, RGBA8, straight alpha PNG',
               occluders=occluders, occlusion='true scene-depth holdout from the same panorama eye',
               camera=dict(horizontal_fov=65, shift_y=camera_data.shift_y, pixel_contract=projected),
               native_visual_verified=False)
(STAGE / 'native_card_author.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print('NATIVE_CARD_MATERIAL_AUTHORED', len(occluders), str(blend))
