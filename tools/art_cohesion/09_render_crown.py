import bpy,pathlib,sys
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/cybercity_materials'
bpy.ops.wm.open_mainfile(filepath=str(ART/'crown_complete.blend'));scene=bpy.context.scene;origin=Vector((0,8608,19392))
try:
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
    for d in p.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.threads_mode='FIXED';scene.render.threads=4
sys.path.insert(0,str(ROOT/'tools/art_cohesion'))
from crown_views import VIEWS as views
selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for name,loc,target,kind,value,w,h in views:
    if selected and name not in selected:continue
    cam=scene.camera;cam.location=Vector(loc)-origin;cam.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler();cam.data.type=kind
    if kind=='ORTHO':cam.data.ortho_scale=value
    else:cam.data.lens=value
    scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.filepath=str(ART/(name+'.png'));bpy.ops.render.render(write_still=True);print('CROWN_REVIEW_RENDER',name,flush=True)
