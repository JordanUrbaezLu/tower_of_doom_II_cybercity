import bpy,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/cyber_sword'
bpy.ops.wm.open_mainfile(filepath=str(ART/'native_bake.blend'))
me=bpy.context.scene.objects['Cyber Sword | native bake'].data;me.calc_loop_triangles();stats=collections.defaultdict(list)
for tri in me.loop_triangles:
    p=me.polygons[tri.polygon_index];dots=[tri.normal.dot(me.corner_normals[li].vector) for li in tri.loops]
    stats[(me.materials[tri.material_index].name,p.use_smooth)].append(min(dots))
print('CORNER_STATS',[(k,len(v),min(v),sum(x<.5 for x in v)) for k,v in stats.items()],flush=True)
