"""A separate six-second close view makes valve travel and right-side discharges legible."""
import bpy,runpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/partner_shop'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'partner_shop.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene['shop_powered']=1
scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.use_persistent_data=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.fps=10
cam=bpy.data.objects['05 SIGN - flicker review'];cam.data.type='PERSP';cam.data.lens=70
cam.location=(143,-133,89);cam.rotation_euler=(Vector((79,-27,58))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
folder=OUT/'pressure_frames';folder.mkdir(exist_ok=True)
for i in range(60):
    scene.frame_set(1+i*3);scene.render.filepath=str(folder/('%04d.png'%(i+1)));bpy.ops.render.render(write_still=True)
    if i%10==9:print('PRESSURE_FRAME',i+1,flush=True)
print('PRESSURE_PREVIEW_COMPLETE',flush=True)
runpy.run_path(str(ROOT/'tools/partner_shop/render_native.py'),run_name='__main__')
