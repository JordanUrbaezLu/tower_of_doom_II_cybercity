"""MCP: matched upward-looking comparison at player height on crown geometry."""
import bpy, pathlib, json, math
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = ROOT / 'art/crown_alarm'
OUT = ART / 'visibility_review'
profile = json.loads((ROOT / 'tools/crown_alarm/light_profile.json').read_text())
mounts = json.loads((ART / 'mounts.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ART / 'high_crown_review/high_4x.blend'))
scene = next(s for s in bpy.data.scenes if s.name.startswith('Actual crown'))
bpy.context.window_manager.windows[0].scene = scene
scene.frame_set(1)
bpy.context.view_layer.update()
origin = Vector((0, 8608, 19392))
scene.camera.location = Vector((100, 8010, 19464)) - origin
scene.camera.rotation_euler = (Vector((-1200, 7700, 23200)) - origin - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera.data.lens = 20
scene.render.resolution_x = 1100
scene.render.resolution_y = 850
scene.render.resolution_percentage = 100
scene.cycles.samples = 16
scene.cycles.use_denoising = True
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == 'OPTIX'
scene.cycles.device = 'GPU'
scene['preview_limit'] = 'Matched Blender geometry/relative emission comparison from player height. Approximate red spill; not native BO3 shading, exposure, culling or performance proof.'
scene.render.filepath = str(OUT / 'before.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'before.blend'))
bpy.ops.render.render(write_still=True)

parts = []
for obj in scene.objects:
    if obj.type != 'MESH' or ' | ' not in obj.name:
        continue
    head = obj.name.split(' | ')[0].split()
    if len(head) != 2 or head[1] not in ('point', 'apex'):
        continue
    mount = mounts[int(head[0])]
    parts.append((obj, mount, [obj.matrix_world @ v.co for v in obj.data.vertices]))
for obj, mount, points in parts:
    anchor = Vector(mount['org']) - origin
    obj.data = obj.data.copy()
    obj.parent = None
    obj.matrix_world.identity()
    for vert, point in zip(obj.data.vertices, points):
        p = (point-anchor)/mount['scale']
        s = 1+max(0,min(1,(p.z-4)/8))
        vert.co = anchor + Vector((p.x*s,p.y*s,p.z if p.z<=4 else 2*p.z-4))*mount['scale']
    obj.data.update()
bpy.data.materials['mtl_tod_alarm_lamp_high_on'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = profile['lamp_emission']*profile['high_lamp_multiplier']
for i, mount in enumerate(mounts):
    if mount['kind'] not in ('point','apex'):
        continue
    data = bpy.data.lights.new('High red spill '+str(i),'POINT')
    data.color = (1,0,0)
    data.energy = profile['high_intensity']*200 # existing review convention only
    data.use_shadow = False
    data.use_custom_distance = True
    data.cutoff_distance = profile['high_radius']
    obj = bpy.data.objects.new(data.name,data)
    scene.collection.objects.link(obj)
    obj.location = Vector(mount['org'])-origin+Vector((0,0,48*mount['scale']))
scene.render.filepath = str(OUT / 'after.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'after.blend'))
bpy.ops.render.render(write_still=True)
print('HIGH_VISIBILITY_REVIEW_RENDERED', len(parts), 'high fixture parts; 17 red lights')
