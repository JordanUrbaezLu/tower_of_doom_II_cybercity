"""Run through Blender MCP: stronger authored lamps and actual-hall sweep study."""
import bpy, json, math, pathlib, random, sys
from mathutils import Matrix, Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = ROOT / 'art/crown_alarm'
OUT = ART / 'intensity_review'
OUT.mkdir(exist_ok=True)
profile = json.loads((ROOT / 'tools/crown_alarm/light_profile.json').read_text())
sys.path.insert(0, str(ROOT / 'tools/crown_alarm'))
from preview_variants import high_material, apply_high_lamps
bpy.ops.wm.open_mainfile(filepath=str(ART / 'crown_alarm.blend'))
scene = bpy.data.scenes['Crown alarm - authored native asset']
bpy.context.window_manager.windows[0].scene = scene
rotor_names = {o.name for o in scene.objects if o.get('alarm_group') == 'rotor'}
lamp = bpy.data.materials['mtl_tod_alarm_lamp_on'].node_tree.nodes['Principled BSDF']
lamp.inputs['Emission Strength'].default_value = profile['lamp_emission']
scene['alarm_light_profile'] = json.dumps(profile)
high_material(profile)
bpy.ops.wm.save_as_mainfile(filepath=str(ART / 'crown_alarm.blend'))

# Review only: mesh placement/material family are current; lighting is an
# illustration of the native ratios and cone geometry, not a BO3 calibration.
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'art/cybercity_materials/color_restoration/crown_restored.blend'))
scene = next(s for s in bpy.data.scenes if s.name.startswith('Actual crown'))
bpy.context.window_manager.windows[0].scene = scene
origin = Vector((0, 8608, 19392))
mounts = json.loads((ART / 'mounts.json').read_text())
spots = []
# Reproducible illustration only. The game rolls once per fixture each match.
phase_rng = random.Random(260926)
phases = []
for i, mount in enumerate(mounts):
    pitch, yaw, roll = map(math.radians, mount['angles'])
    transform = (Matrix.Translation(Vector(mount['org']) - origin)
                 @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'Y')
                 @ Matrix.Rotation(roll, 4, 'X') @ Matrix.Scale(mount['scale'], 4))
    rotor = bpy.data.objects.new(f'REVIEW rotor {i}', None)
    scene.collection.objects.link(rotor)
    rotor.matrix_world = transform @ Matrix.Translation((0, 0, 26))
    base_angle = rotor.rotation_euler.z
    prefix = f"{i} {mount['kind']} | "
    for obj in list(scene.objects):
        if obj.name.startswith(prefix) and obj.name[len(prefix):] in rotor_names:
            world = obj.matrix_world.copy()
            obj.parent = rotor
            obj.matrix_world = world
    phase = phase_rng.uniform(0, 360)
    base_angle += math.radians(phase)
    rotor['start_phase_degrees'] = phase
    phases.append(dict(id=i, kind=mount['kind'], phase_degrees=phase))
    # Native RotateYaw rotates about world Z; preserve the inverted pendant.
    for frame, angle in [(1, base_angle), (37, base_angle + math.tau)]:
        rotor.rotation_euler.z = angle
        rotor.keyframe_insert(data_path='rotation_euler', frame=frame)
    for curve in rotor.animation_data.action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'
        curve.modifiers.new('CYCLES')
    if mount['kind'] not in ('pillar', 'pendant'):
        continue
    data = bpy.data.lights.new(f'REVIEW red sweep {i}', 'SPOT')
    data.color = (1, 0, 0)
    data.use_custom_distance = True
    data.spot_blend = .25
    data.shadow_soft_size = 2
    data.use_shadow = False
    ob = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(ob)
    ob.parent = rotor
    ob.location = (9, 0, 2)
    ob.rotation_euler = Vector((1, 0, 0)).to_track_quat('-Z', 'Y').to_euler()
    spots.append(data)
assert len(spots) == 13
assert apply_high_lamps(scene, profile) == 34
(OUT / 'phases.json').write_text(json.dumps(dict(preview_seed=260926,
    runtime='Server RandomFloat(360), once per fixture per match', fixtures=phases), indent=2))
for light in scene.objects:
    if light.type != 'LIGHT' or light.data in spots:
        continue
    light.data.energy *= .02
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .035
cam = scene.camera
cam.location = Vector((100, 8010, 19464)) - origin
cam.rotation_euler = (Vector((0, 8660, 19480)) - origin - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 22
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 36
scene.render.resolution_x = 1360
scene.render.resolution_y = 850
scene.render.resolution_percentage = 100
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene['preview_limit'] = ('Actual current geometry and mounts; approximate Blender material/light study. '
                          'Spot energy = native intensity * 200 for illustration only; '
                          'before/after use identical camera, fill, exposure and materials. '
                          'Not a BO3 brightness, probe, culling or performance verification.')
lamp = bpy.data.materials['mtl_tod_alarm_lamp_on'].node_tree.nodes['Principled BSDF']
for state, intensity, radius, fov, emission in [
        ('before', 450, 360, 62, 12),
        ('stronger', profile['intensity'], profile['radius'], profile['fov_degrees'], profile['lamp_emission'])]:
    for spot in spots:
        spot.energy = intensity * 200
        spot.cutoff_distance = radius
        spot.spot_size = math.radians(fov)
    lamp.inputs['Emission Strength'].default_value = emission
    high_material(profile).node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = emission if state == 'before' else emission * profile['high_lamp_multiplier']
    scene.frame_set(1)
    scene['alarm_review_state'] = state
    scene.render.filepath = str(OUT / (state + '.png'))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (state + '.blend')))
print('ALARM_INTENSITY_MCP_REVIEW_READY', len(spots), 'spots; 30 rotating fixtures; matched before/after')
