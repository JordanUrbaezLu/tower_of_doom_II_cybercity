import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/cyber_sword'
bpy.ops.wm.open_mainfile(filepath=str(ART/'native_bake.blend'))
scene=bpy.context.scene;scene.cycles.samples=16
scene.render.filepath=str(ART/'bake_mesh_diagnostic.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.open_mainfile(filepath=str(ART/'cyber_sword.blend'))
deps=bpy.context.evaluated_depsgraph_get();rows=[]
for ob in bpy.context.scene.objects:
    if not ob.get('cyber_sword_part'):continue
    me=bpy.data.meshes.new_from_object(ob.evaluated_get(deps),depsgraph=deps);me.calc_loop_triangles()
    rows.append((ob.name,len(me.loop_triangles)));bpy.data.meshes.remove(me)
(ART/'part_triangles.json').write_text(json.dumps(sorted(rows,key=lambda row:-row[1]),indent=2))
