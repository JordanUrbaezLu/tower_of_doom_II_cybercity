import bpy,pathlib,sys,json
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'art/cybercity_materials/color_restoration'
sys.path.insert(0,str(ROOT/'tools/art_cohesion'))
from crown_views import VIEWS
for state in ['before','restored']:
    bpy.ops.wm.open_mainfile(filepath=str(OUT/('crown_'+state+'.blend')))
    scene=next(s for s in bpy.data.scenes if s.name.startswith('Actual crown'))
    bpy.context.window_manager.windows[0].scene=scene
    try:
        p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
        for d in p.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
    except Exception:pass
    for name,loc,target,kind,value,w,h in VIEWS:
        if name not in ['crown_interior','crown_from_tower']:continue
        cam=scene.camera;cam.location=Vector(loc)-Vector((0,8608,19392));cam.rotation_euler=(Vector(target)-Vector((0,8608,19392))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type=kind
        if kind=='ORTHO':cam.data.ortho_scale=value
        else:cam.data.lens=value
        scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.filepath=str(OUT/(name+'_'+state+'.png'));bpy.ops.render.render(write_still=True)
        print('COLOR_RENDER',state,name,flush=True)
