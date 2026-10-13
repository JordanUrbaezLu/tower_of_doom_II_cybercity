"""MCP: native-map close-ups of the final bone, metal and leather surfaces."""
import bpy,pathlib,json
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/necro_staff'
bpy.ops.wm.open_mainfile(filepath=str(ART/'staff_review.blend'))
scene=bpy.context.scene;camera=scene.camera
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
for ob in scene.objects:
    if ob.type=='MESH' and 'tier' in ob:ob.hide_render=ob['tier']!=3
camera.data.type='ORTHO'
for name,location,target,scale in [('bone',(6,-36,38),(0,-1,33.5),11),('blade',(5,-30,48),(0,0,46),17),('grip',(4,-20,2),(0,0,-.1),6.5)]:
    camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.filepath=str(ART/('detail_'+name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'surface_detail_review.blend'))
print('NATIVE MAP MACROS: bone, forged blade and leather grip')
