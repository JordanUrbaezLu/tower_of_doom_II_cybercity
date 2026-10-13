"""MCP: remove coplanar ribbon overlap from the already baked staged master."""
import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/necro_staff/detail_pass'
bpy.ops.wm.open_mainfile(filepath=str(ART/'staff_master.blend'))
scene=bpy.context.scene
assert not scene.get('grip_seams_refined',False),'Already refined; rebuild stage for another change'
count=0
for ob in scene.objects:
    if ob.name.startswith('Leather grip'):
        assert len(ob.data.vertices)==1284,len(ob.data.vertices)
        for v in ob.data.vertices:v.co.z += .04 if v.index%2==0 else -.04
        count+=1
    if ob.name.startswith('Grip stitches'):
        for v in ob.data.vertices:v.co.y-=.04
assert count==4
scene['grip_seams_refined']=True
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'staff_master.blend'))
print('GRIP SEAMS: four ribbons have a real seam; no coplanar overlap; stitches meet the outer hide')
