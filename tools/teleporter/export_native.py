"""Bake the MCP master to a single native material and seven distance LODs."""
import bpy,bmesh,sys,json,hashlib,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/teleporter';STAGE=ART/'engine_kit';OUT=ROOT/'model_export/tod_teleporter';IMG=OUT/'_images'
for p in (STAGE,OUT,IMG):p.mkdir(parents=True,exist_ok=True)
MASTER=ART/'teleporter_cyber.blend';digest=hashlib.sha256(MASTER.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(MASTER));scene=bpy.context.scene
sys.path.insert(0,str(ROOT/'tools'));import cyber_material_bake as BAKE
BAKE.EMISSION_SCALE=6
parts=[o for o in scene.objects if o.get('teleporter_design')]
for ob in list(scene.objects):
    if ob not in parts and ob.type=='MESH':bpy.data.objects.remove(ob,do_unlink=True)
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.threads_mode='FIXED';scene.render.threads=12
scene.render.bake.margin=8;scene.render.bake.use_selected_to_active=False;scene.render.bake.normal_g='NEG_Y'
deps=bpy.context.evaluated_depsgraph_get()
evaluated=[(o,bpy.data.meshes.new_from_object(o.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)) for o in parts]
for ob,me in evaluated:
    ob.data=me
    for mod in list(ob.modifiers):ob.modifiers.remove(mod)
    attr=me.attributes.new('tp_generated','FLOAT_VECTOR','POINT')
    lo=[min(v.co[i] for v in me.vertices) for i in range(3)];hi=[max(v.co[i] for v in me.vertices) for i in range(3)]
    attr.data.foreach_set('vector',[(v.co[i]-lo[i])/(hi[i]-lo[i]) if hi[i]-lo[i]>1e-8 else .5 for v in me.vertices for i in range(3)])
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
for material in {m for o in parts for m in o.data.materials if m}:
    ns=material.node_tree.nodes;l=material.node_tree.links;a=ns.new('ShaderNodeAttribute');a.attribute_name='tp_generated'
    for node in list(ns):
        if node.type=='TEX_NOISE' and not node.inputs['Vector'].is_linked:l.new(a.outputs['Vector'],node.inputs['Vector'])
bpy.ops.object.select_all(action='DESELECT')
for ob in parts:ob.hide_set(False);ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();kit=bpy.context.object;kit.name='Teleporter native mesh'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
kit.data.calc_loop_triangles();before=len(kit.data.loop_triangles);print('TELEPORTER_EVALUATED_TRIS',before,flush=True)
mod=kit.modifiers.new('Native close-range triangle budget','DECIMATE');mod.ratio=min(1,52000/before);mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
print('TELEPORTER_CLOSE_REDUCTION',len(kit.data.polygons),flush=True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.002,margin_method='FRACTION',area_weight=.5);bpy.ops.object.mode_set(mode='OBJECT')
mats=list(kit.data.materials);images={}
for suffix in ('n','c','s','g','e'):
    im=bpy.data.images.new('i_tod_teleporter_'+suffix,width=2048,height=2048,alpha=False);im.colorspace_settings.name='Non-Color' if suffix in ('n','g') else 'sRGB'
    for material in mats:
        node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;material.node_tree.nodes.active=node
        if suffix!='n':BAKE.wire_channel(material,suffix)
    bpy.ops.object.bake(type='NORMAL' if suffix=='n' else 'EMIT',normal_space='TANGENT')
    im.filepath_raw=str(IMG/(im.name+'.png'));im.file_format='PNG';im.save();images[suffix]=im;print('TELEPORTER_BAKED',suffix,flush=True)
def geometry(ob):
    me=ob.data;me.calc_loop_triangles();data={'bone':'tag_origin','material':'mtl_tod_teleporter','verts':[list(v.co) for v in me.vertices],'faces':[]}
    for tri in me.loop_triangles:
        if tri.area<1e-9:continue
        corners=[]
        for li in (tri.loops[0],tri.loops[2],tri.loops[1]):
            n=me.corner_normals[li].vector.normalized()
            if n.length_squared<.9:n=tri.normal.normalized()
            uv=me.uv_layers.active.data[li].uv;corners.append({'v':me.loops[li].vertex_index,'n':list(n),'uv':[uv[0],1-uv[1]]})
        data['faces'].append(corners)
    from cyber_reference_one.native_geometry import clean
    clean(data,min_altitude=.001)
    (STAGE/'solid_lod0.json').write_text(json.dumps(data,separators=(',',':')))
    return len(data['faces'])
count=geometry(kit)
# Exported-channel approximation uses the real native gloss range.
# Run the native installer before the final preview if its GDT has changed.
from art_cohesion.native_preview import fullspec
m=fullspec(ROOT/'source_data/tod_teleporter.gdt','mtl_tod_teleporter',IMG)
kit.data.materials.clear();kit.data.materials.append(m)
for poly in kit.data.polygons:poly.material_index=0
scene.cycles.samples=32
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'teleporter_native.blend'))
(STAGE/'lod_counts.json').write_text(json.dumps({'0':{'solid':count}},indent=2))
runpy.run_path(str(ROOT/'tools/cyber_reference_one/reduce_game_lods.py'),run_name='__main__',init_globals={'CYBER_LOD_SOURCE':STAGE,'CYBER_LOD_OUTPUT':STAGE,'CYBER_LOD_AREA_FLOORS':{'solid':(0,.05,.3,1,3,7,14)}})
runpy.run_path(str(ROOT/'tools/teleporter/constrain_lods.py'),run_name='__main__')
manifest={'master':'art/teleporter/teleporter_cyber.blend','master_sha256':digest,'atlas_size':2048,'emission_scale':6,'groups':{'solid':'mtl_tod_teleporter'},'normal_convention':'DirectX -Y','textures':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in IMG.glob('*.png')},'lod_counts':json.loads((STAGE/'lod_counts.json').read_text())}
(STAGE/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('TELEPORTER_EXPORT_OK',manifest['lod_counts'],flush=True)
