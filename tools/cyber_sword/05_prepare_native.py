"""MCP: prepare the authored sword for native channel bakes and fixed LODs."""
import bpy,bmesh,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/cyber_sword';KIT=ART/'engine_kit';KIT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ART/'cyber_sword.blend'))
scene=bpy.data.scenes['Cyber Sword | charge studio']
for win in bpy.context.window_manager.windows:win.scene=scene
scene.frame_set(60);scene.update_tag();bpy.context.view_layer.update()
guide=scene.objects['Citadel attachment guide'];anchor=guide.matrix_world.inverted().copy()
parts=[o for o in scene.objects if o.get('cyber_sword_part')]
for ob in parts:
    if ob.type=='CURVE':ob.data.resolution_u=3;ob.data.bevel_resolution=min(1,ob.data.bevel_resolution)
deps=bpy.context.evaluated_depsgraph_get()
evaluated=[(o,bpy.data.meshes.new_from_object(o.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)) for o in parts]
for ob in list(scene.objects):
    if ob.type in ('MESH','CURVE','FONT'):ob.hide_set(True)
new=[]
for source,mesh in evaluated:
    ob=bpy.data.objects.new('Bake | '+source.name,mesh);scene.collection.objects.link(ob);ob.matrix_world=source.matrix_world
    new.append(ob)
layer=scene.view_layers[0];layer.update();layer.objects.active=new[0]
for ob in layer.objects:ob.select_set(False,view_layer=layer)
for ob in new:ob.hide_set(False,view_layer=layer);ob.select_set(True,view_layer=layer)
kit=new[0]
with bpy.context.temp_override(window=bpy.context.window_manager.windows[0],scene=scene,view_layer=layer,active_object=kit,object=kit,selected_objects=new,selected_editable_objects=new):
    bpy.ops.object.join()
kit.name='Cyber Sword | native bake'
with bpy.context.temp_override(window=bpy.context.window_manager.windows[0],scene=scene,view_layer=layer,active_object=kit,object=kit,selected_objects=[kit],selected_editable_objects=[kit]):
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bm=bmesh.new();bm.from_mesh(kit.data)
bad=[f for f in bm.faces if f.calc_area()<1e-14]
bmesh.ops.delete(bm,geom=bad,context='FACES_ONLY');bm.to_mesh(kit.data);bm.free();kit.data.update()
kit.data.calc_loop_triangles();before=len(kit.data.loop_triangles)
mod=kit.modifiers.new('Native view budget','DECIMATE');mod.ratio=min(1,49000/before);mod.use_collapse_triangulate=True
with bpy.context.temp_override(window=bpy.context.window_manager.windows[0],scene=scene,view_layer=layer,active_object=kit,object=kit,selected_objects=[kit],selected_editable_objects=[kit]):
    bpy.ops.object.modifier_apply(modifier=mod.name)
    triangulate=kit.modifiers.new('Native triangle topology','TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=triangulate.name)
    # Collapsing the donor's weighted custom normals can flip long edge faces.
    # Rebuild them on the final geometry before baking or exporting any normals.
    kit.data.normals_split_custom_set([(0,0,0)]*len(kit.data.loops))
    kit.data.set_sharp_from_angle(angle=math.radians(45))
    normal=kit.modifiers.new('Final machined normals','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=50
    bpy.ops.object.modifier_apply(modifier=normal.name)
    # The cutting planes are deliberately flat. Do not smooth a thin edge into
    # its opposite face; that creates triangular dark patches after export.
    normals=[n.vector.copy() for n in kit.data.corner_normals]
    for face in kit.data.polygons:
        cutting_plane=(anchor@face.center/.0254).z+1.1>5
        for li in face.loop_indices:
            if cutting_plane or normals[li].dot(face.normal)<.2:normals[li]=face.normal.copy()
    kit.data.normals_split_custom_set(normals)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.0025,margin_method='FRACTION',area_weight=1)
    bpy.ops.object.mode_set(mode='OBJECT')
kit.data.calc_loop_triangles()
scene['native_anchor_matrix']=[x for row in anchor for x in row]
scene['native_kit_object']=kit.name
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.render.bake.margin=4
scene.render.bake.normal_g='NEG_Y';scene.render.bake.use_selected_to_active=False
for ob in scene.objects:
    if ob!=kit and ob.type in ('MESH','CURVE','FONT'):ob.hide_render=True
kit.hide_render=False
data=dict(evaluated_triangles=before,view_triangles=len(kit.data.loop_triangles),removed_collapsed_faces=len(bad),
          atlas_size=4096,bake_margin=4,uv_island_margin=.0025,source_parts=len(parts),anchor_matrix=[list(row) for row in anchor])
(KIT/'preparation.json').write_text(json.dumps(data,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'native_bake.blend'))
print('CYBER_SWORD_BAKE_PREPARED',json.dumps(data),flush=True)
