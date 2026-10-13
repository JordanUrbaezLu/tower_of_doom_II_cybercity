"""MCP diagnostic: rebuild the shipped binary and its real atlas bindings."""
import bpy, sys, json
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'art/teleporter/surface_repair'
OUT.mkdir(parents=True, exist_ok=True)
stage=globals().get('SURFACE_STAGE','before')
assert stage in ('before','after')
sys.path.insert(0, str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
sys.path.insert(0, str(ROOT/'tools'))
from PyCoD import xmodel
from art_cohesion.native_preview import fullspec
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/teleporter/teleporter_native.blend'))
scene = bpy.data.scenes[0]
for win in bpy.context.window_manager.windows: win.scene = scene
for ob in list(scene.objects):
    if ob.type == 'MESH': bpy.data.objects.remove(ob, do_unlink=True)
mat = fullspec(ROOT/'source_data/tod_teleporter.gdt', 'mtl_tod_teleporter', ROOT/'model_export/tod_teleporter/_images')
model = xmodel.Model()
model.LoadFile_Bin(str(ROOT/'model_export/tod_teleporter/tod_teleporter_lod0.xmodel_bin'), split_meshes=True)
for source in model.meshes:
    me=bpy.data.meshes.new(source.name)
    me.from_pydata([v.offset for v in source.verts], [], [[f.indices[i].vertex for i in (0,2,1)] for f in source.faces])
    me.update(); me.materials.append(mat)
    uv=me.uv_layers.new(); normals=[]
    for p,f in zip(me.polygons,source.faces):
        p.use_smooth=True
        for li,i in zip(p.loop_indices,(0,2,1)):
            c=f.indices[i]; uv.data[li].uv=(c.uv[0],1-c.uv[1]); normals.append(c.normal)
    me.normals_split_custom_set(normals)
    ob=bpy.data.objects.new('Binary surface | '+source.name,me); scene.collection.objects.link(ob)
scene.camera.location=(100,-220,105)
scene.camera.rotation_euler=(Vector((0,0,0))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.ortho_scale=192
scene.render.engine='CYCLES'; scene.cycles.samples=24
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for device in prefs.devices: device.use=device.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception: pass
scene.render.resolution_x=1200; scene.render.resolution_y=900; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/('binary_'+stage+'.png'))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/('binary_'+stage+'.blend')))
print('NATIVE_SURFACE_DIAGNOSTIC_READY',len(model.meshes),sum(len(m.faces) for m in model.meshes),flush=True)
