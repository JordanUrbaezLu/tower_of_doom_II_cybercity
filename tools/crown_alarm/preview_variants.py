"""Apply the native exterior-only lamp variant to the Blender review instances."""
def high_material(profile):
    import bpy
    name = 'mtl_tod_alarm_lamp_high_on'
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials['mtl_tod_alarm_lamp_on'].copy()
        mat.name = name
    mat.use_fake_user = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = profile['lamp_emission'] * profile['high_lamp_multiplier']
    return mat

def apply_high_lamps(scene, profile):
    mat = high_material(profile)
    changed = 0
    for obj in scene.objects:
        if obj.type != 'MESH' or ' | ' not in obj.name:
            continue
        mount = obj.name.split(' | ', 1)[0].split()
        if len(mount) != 2 or mount[1] not in ('point', 'apex'):
            continue
        if not any(slot.material and slot.material.name == 'mtl_tod_alarm_lamp_on' for slot in obj.material_slots):
            continue
        # Mount instances share mesh data. Copy only the emissive pieces so the
        # skin change cannot also brighten any hall instance of that mesh.
        obj.data = obj.data.copy()
        for slot in obj.material_slots:
            if slot.material and slot.material.name == 'mtl_tod_alarm_lamp_on':
                slot.material = mat
                changed += 1
    return changed
