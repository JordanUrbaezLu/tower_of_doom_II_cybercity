"""Run through Blender MCP: enlarge high fixtures, retaining their mounting feet.

The editable derivative and all six native LODs use the same deformation.
Existing hall masters, textures and exported geometry remain untouched.
"""
import bpy, json, pathlib, sys, hashlib
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = ROOT / 'art/crown_alarm'
OUT = ART / 'visibility_review'
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
profile = json.loads((ROOT / 'tools/crown_alarm/light_profile.json').read_text())
assert profile['high_fixture_scale'] == 2 and profile['high_rotor_height'] == 48

def deform(v):
    x, y, z = v
    # Original bolted foot through z=4; the motor flares into the doubled lens.
    scale = 1 + max(0, min(1, (z - 4) / 8))
    return Vector((x * scale, y * scale, z if z <= 4 else 2*z - 4))

bpy.ops.wm.open_mainfile(filepath=str(ART / 'crown_alarm.blend'))
scene = bpy.data.scenes['Crown alarm - authored native asset']
bpy.context.window_manager.windows[0].scene = scene
scene.frame_set(1)
bpy.context.view_layer.update()
for obj in list(scene.objects):
    if obj.type != 'MESH' or 'alarm_group' not in obj:
        continue
    world = obj.matrix_world.copy()
    obj.parent = None
    obj.matrix_world.identity()
    for vert in obj.data.vertices:
        vert.co = deform(world @ vert.co)
    obj.data.update()
rotor = next(o for o in scene.objects if o.name.startswith('ROTATING REFLECTOR'))
rotor.animation_data_clear()
rotor.location = (0, 0, 48)
rotor.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
for obj in list(scene.objects):
    if obj.get('alarm_group') == 'rotor':
        world = obj.matrix_world.copy()
        obj.parent = rotor
        obj.matrix_world = world
lamp = bpy.data.materials['mtl_tod_alarm_lamp_on'].node_tree.nodes['Principled BSDF']
lamp.inputs['Emission Strength'].default_value = profile['lamp_emission'] * profile['high_lamp_multiplier']
scene['preview_limit'] = 'High crown derivative, doubled lens/reflector with original mounting foot; Blender shading is not native BO3 verification.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'high_fixture.blend'))

manifest_path = ART / 'manifest.json'
manifest = json.loads(manifest_path.read_text())
targets = {'tod_crown_alarm_housing': 'tod_crown_alarm_housing_high',
           'tod_crown_alarm_rotor_off': 'tod_crown_alarm_rotor_high_off'}
manifest['models'] = [r for r in manifest['models'] if r['asset'] not in targets.values()]
records = []
for row in manifest['models']:
    if row['asset'] not in targets:
        continue
    model = xmodel.Model()
    model.LoadFile_Bin(str(ROOT / row['file']), split_meshes=True)
    is_rotor = 'rotor' in row['asset']
    points = []
    for mesh in model.meshes:
        for vertex in mesh.verts:
            point = Vector(vertex.offset)
            if is_rotor:
                point.z += 26
            point = deform(point)
            if is_rotor:
                point.z -= 48
            vertex.offset = tuple(point)
            points.append(point)
        # Most pieces undergo a uniform transform. Recompute face normals only
        # on the flared motor section; UVs, weights and winding stay intact.
        if not is_rotor:
            for face in mesh.faces:
                ps = [Vector(mesh.verts[c.vertex].offset) for c in face.indices]
                normal = (ps[2]-ps[0]).cross(ps[1]-ps[0]).normalized()
                for corner in face.indices:
                    corner.normal = tuple(normal)
    target = targets[row['asset']]
    path = ROOT / 'model_export/tod_crown_alarm' / (target + '_lod' + str(row['lod']) + '.xmodel_bin')
    model.WriteFile_Bin(str(path), version=7)
    records.append(dict(row, asset=target, file=path.relative_to(ROOT).as_posix(),
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        bounds=[[min(p[i] for p in points) for i in range(3)],
                                [max(p[i] for p in points) for i in range(3)]]))
manifest['models'].extend(records)
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print('HIGH_VISIBILITY_AUTHORED', len(records), 'native LODs; original foot, 2x upper fixtures')
