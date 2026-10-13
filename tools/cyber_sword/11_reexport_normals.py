"""Re-export baked geometry after the outward-normal guard; atlas is unchanged."""
import bpy,json,sys
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/cyber_sword';KIT=ART/'engine_kit'
bpy.ops.wm.open_mainfile(filepath=str(ART/'native_baked.blend'))
scene=bpy.context.scene;me=scene.objects[scene['native_kit_object']].data;me.calc_loop_triangles()
anchor=Matrix([scene['native_anchor_matrix'][i:i+4] for i in range(0,16,4)]);rotation=anchor.to_3x3()
data=dict(bone='tag_weapon',material='mtl_tod_cyber_sword',verts=[],faces=[]);fixed=0
for v in me.vertices:
    p=anchor@v.co/.0254;p.z+=1.1;data['verts'].append(list(p))
for tri in me.loop_triangles:
    if tri.area<1e-14:continue
    face=[]
    for li in (tri.loops[0],tri.loops[2],tri.loops[1]):
        local=me.corner_normals[li].vector
        if (anchor@tri.center/.0254).z+1.1>5:local=tri.normal
        if local.dot(tri.normal)<.2:local=tri.normal;fixed+=1
        n=(rotation@local).normalized();uv=me.uv_layers.active.data[li].uv
        face.append(dict(v=me.loops[li].vertex_index,n=list(n),uv=[uv.x,1-uv.y]))
    data['faces'].append(face)
sys.path.insert(0,str(ROOT/'tools'))
from cyber_reference_one.native_geometry import clean
clean(data,min_altitude=.0005)
(KIT/'solid_lod0.json').write_text(json.dumps(data,separators=(',',':')))
print('CYBER_SWORD_OUTWARD_NORMALS',fixed,len(data['faces']),flush=True)
