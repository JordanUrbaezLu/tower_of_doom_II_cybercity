"""Refresh the editable original wire source to the native emission setting."""
import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'art/cybercity_materials/color_restoration'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'power_conduits.blend'))
material=bpy.data.materials['mtl_tod_conduit_wire_on']
material.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=8
scene=bpy.context.scene
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.filepath=str(OUT/'conduits_off_on.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'power_conduits.blend'))
print('POWER_CONDUIT_SOURCE_REVIEW_UPDATED emission=8 geometry unchanged')
