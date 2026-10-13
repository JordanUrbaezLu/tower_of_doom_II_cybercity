"""Render one rig with ready/off/recharge states; never edit source masters."""
import bpy,pathlib,math
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/cybercity_materials'
bpy.ops.wm.open_mainfile(filepath=str(ART/'native_comparison.blend'));scene=bpy.context.scene
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.threads_mode='FIXED';scene.render.threads=4
def material(name):return bpy.data.materials['Native approximation | '+name]
def state(on,recharge=False):
    for ob in scene.objects:
        tag=ob.get('review_group','')
        if tag=='teleporter':ob.data.materials[0]=material('mtl_tod_teleporter' if on and not recharge else 'mtl_tod_tp_off')
        if tag=='recharge':ob.hide_render=not recharge
        if tag in ('shop_vendor','shop_mask'):ob.hide_render=not on
        if tag.startswith('shop_'):
            for i,m in enumerate(ob.data.materials):
                if 'mtl_tod_shop_glow' in m.name:ob.data.materials[i]=material('mtl_tod_shop_glow' if on else 'mtl_tod_shop_glow_off')
def render(name):scene.render.filepath=str(ART/(name+'.png'));bpy.ops.render.render(write_still=True);print('SHARED_REVIEW_RENDER',name,flush=True)
for name,on,recharge in [('comparison_ready',True,False),('comparison_off',False,False),('comparison_recharge',True,True)]:state(on,recharge);render(name)
state(True)
scene.camera.location=(-20,-500,185);target=Vector((-205,10,75));scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=370
scene.render.resolution_x=1200;scene.render.resolution_y=1100;render('bay_detail')
