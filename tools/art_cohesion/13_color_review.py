"""MCP builds two matched views of the current map, preserving the alarm studio."""
import bpy,pathlib,sys,re,json,hashlib
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'art/cybercity_materials/color_restoration'
sys.path.insert(0,str(ROOT/'tools/art_cohesion'))
from native_preview import fullspec,DESCRIPTION
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/crown_alarm/mount_review.blend'))
scene=next(s for s in bpy.data.scenes if s.name.startswith('Actual crown'))
bpy.context.window_manager.windows[0].scene=scene
rows=[]
for ob in scene.objects:
    if ob.type!='MESH':continue
    for i,mat in enumerate(ob.data.materials):
        m=re.search(r'tod_cc_([a-z_]+)',mat.name)
        if m:rows.append((ob,i,m[1]))
assert len(set(ob.name for ob,_,_ in rows))==846
scene['preview_limit']=DESCRIPTION+'; identical current geometry, cameras, lighting, exposure; runtime light, sky and gameplay props omitted'
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.camera.location=Vector((100,8200,19464))-Vector((0,8608,19392))
scene.camera.rotation_euler=(Vector((-620,8550,19480))-Vector((0,8608,19392))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.type='PERSP';scene.camera.data.lens=22
for state,file in [('before',OUT/'before_tod_surface.gdt'),('restored',ROOT/'source_data/tod_surface.gdt')]:
    roles={role:fullspec(file,'tod_cc_'+role,ROOT/'model_export/tod_surface/_images') for role in {r[2] for r in rows}}
    for ob,i,role in rows:ob.data.materials[i]=roles[role]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/('crown_'+state+'.blend')))
print('COLOR_REVIEW_SCENES',len(set(ob.name for ob,_,_ in rows)),'current solids; same 30 physical alarms; before/restored native material tints')
