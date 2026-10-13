import bpy
from mathutils import Vector
s=bpy.data.scenes['BO2 native first person'];s.frame_set(1)
print('camera',s.camera.matrix_world[:])
for ob in s.objects:
    if ob.type=='MESH' and not ob.hide_render:
        dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg)
        pts=[v.co for v in ev.data.vertices]
        print(ob.name,'bounds',[(min(p[i] for p in pts),max(p[i] for p in pts)) for i in range(3)],'keys',[(k.name,k.value) for k in ob.data.shape_keys.key_blocks if k.value])
from pathlib import Path
root=Path(__file__).resolve().parents[2]
for clip,frame in [('throw',5),('flourish',30)]:
    for ob in s.objects:
        if ob.type=='MESH':ob.hide_render=not ob.name.startswith(clip+' ');ob.hide_viewport=ob.hide_render
    s.frame_set(frame);s.render.filepath=str(root/'art/archer_assets/preview'/('bo2_'+clip+'.png'))
    bpy.ops.render.render(write_still=True,scene=s.name)
