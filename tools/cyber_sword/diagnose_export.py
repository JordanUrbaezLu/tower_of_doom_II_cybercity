import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/cyber_sword'
bpy.ops.wm.open_mainfile(filepath=str(ART/'native_bake.blend'))
scene=bpy.context.scene;ob=scene.objects[scene['native_kit_object']];me=ob.data;me.calc_loop_triangles()
print('UV_LAYERS',[(u.name,u.active_render) for u in me.uv_layers],me.uv_layers.active.name,flush=True)
norm=Matrix([scene['native_anchor_matrix'][i:i+4] for i in range(0,16,4)]).to_3x3()
data=json.loads((ART/'engine_kit/binary_roundtrip.json').read_text())
# Render the actual binary positions/UVs with clean face-derived normals, to isolate shading.
bpy.ops.wm.open_mainfile(filepath=str(ART/'native_preview.blend'))
scene=bpy.context.scene;ob=scene.objects['Cyber Sword | actual exported mesh and maps']
ob.data.normals_split_custom_set([(0,0,0)]*len(ob.data.loops))
for p in ob.data.polygons:p.use_smooth=False
mat=ob.data.materials[0]
for n in mat.node_tree.nodes:
    if n.type=='NORMAL_MAP':
        for link in list(n.inputs['Color'].links):mat.node_tree.links.remove(link)
        n.inputs['Color'].default_value=(.5,.5,1,1)
scene.cycles.samples=12;scene.render.filepath=str(ART/'flat_diagnostic.png');bpy.ops.render.render(write_still=True)
