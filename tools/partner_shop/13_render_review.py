"""Background review rendering; leaves the interactive master untouched."""
import bpy,json,sys,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/partner_shop'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'partner_shop.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
def render(cam,file,w=1280,h=1080,frame=1,power=1):
    scene['shop_powered']=power;scene.update_tag()
    for m in bpy.data.materials:
        if m.get('shop_emissive'):m.node_tree.update_tag()
    for ob in scene.objects:ob.update_tag()
    scene.frame_set(frame);scene.camera=cam;scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.filepath=str(OUT/file)
    bpy.ops.render.render(write_still=True);print('REVIEW_RENDER',file,flush=True)
hero=bpy.data.objects['01 HERO - three-quarter']
render(hero,'hero.png');render(hero,'powered_off.png',power=0)
render(bpy.data.objects['02 PLAYER - service window'],'player_view.png')
render(bpy.data.objects['04 MERCHANT - close view'],'merchant.png',1000,1000)
render(bpy.data.objects['03 REAR - service hardware'],'rear.png')
cam=bpy.data.objects['05 SIGN - flicker review'];cam.data.type='PERSP';cam.data.lens=52
cam.location=(-190,-140,90);cam.rotation_euler=(Vector((-61,-8,57))-cam.location).to_track_quat('-Z','Y').to_euler()
render(cam,'left_detail.png',1100,1100,31)
cam.location=(143,-133,89);cam.rotation_euler=(Vector((79,-27,58))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=70
render(cam,'pressure_detail.png',1000,1000,45)
render(cam,'pressure_sparks.png',1000,1000,31)
if '--stills-only' in sys.argv:raise SystemExit(0)
# EEVEE preview preserves continuously changing mask/canister/pressure motion.
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=960;scene.render.resolution_y=800
if hasattr(scene,'eevee'):scene.eevee.taa_render_samples=16
scene.camera=hero;scene['shop_powered']=1;scene.render.fps=30
folder=OUT/'electrical_frames';folder.mkdir(exist_ok=True)
for f in range(1,181):
    scene.frame_set(f);scene.render.filepath=str(folder/('%04d.png'%f));bpy.ops.render.render(write_still=True)
    if f%15==0:print('ELECTRICAL_FRAME',f,flush=True)
print('REVIEW_COMPLETE',flush=True)
