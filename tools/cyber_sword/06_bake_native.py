"""Bake real native maps and export geometry. All writes stay in this repo."""
import bpy,bmesh,json,sys,hashlib,runpy
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/cyber_sword';KIT=ART/'engine_kit'
OUT=ROOT/'model_export/tod_warrior/cyber_sword';IMG=OUT/'_images';IMG.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ART/'native_bake.blend'))
scene=bpy.data.scenes['Cyber Sword | charge studio']
for win in bpy.context.window_manager.windows:win.scene=scene
kit=scene.objects[scene['native_kit_object']]
bpy.ops.object.select_all(action='DESELECT');kit.hide_set(False);kit.select_set(True);bpy.context.view_layer.objects.active=kit
scene.frame_set(60);scene.update_tag();bpy.context.view_layer.update()
sys.path.insert(0,str(ROOT/'tools'));import cyber_material_bake as BAKE
BAKE.EMISSION_SCALE=12
mats=list(kit.data.materials);images={}
for suffix in ('n','c','s','g','e'):
    image=bpy.data.images.new('i_tod_cyber_sword_'+suffix,width=4096,height=4096,alpha=False)
    image.colorspace_settings.name='Non-Color' if suffix in ('n','g') else 'sRGB'
    for mat in mats:
        nodes=mat.node_tree.nodes;links=mat.node_tree.links;p=nodes.get('Principled BSDF')
        target=nodes.new('ShaderNodeTexImage');target.image=image;nodes.active=target
        if suffix!='n':
            BAKE.wire_channel(mat,suffix)
            if suffix=='c':
                # Fullspec diffuse excludes the metallic reflection contribution.
                emitter=next(n for n in reversed(list(nodes)) if n.type=='EMISSION')
                source=emitter.inputs['Color'].links[0].from_socket
                mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
                mix.inputs[2].default_value=(1-p.inputs['Metallic'].default_value,)*3+(1,)
                links.new(source,mix.inputs[1]);links.new(mix.outputs[0],emitter.inputs['Color'])
    print('CYBER_SWORD_BAKE_START',suffix,flush=True)
    bpy.ops.object.bake(type='NORMAL' if suffix=='n' else 'EMIT',normal_space='TANGENT')
    image.filepath_raw=str(IMG/(image.name+'.png'));image.file_format='PNG';image.save();images[suffix]=image
    print('CYBER_SWORD_BAKE_DONE',suffix,flush=True)
anchor=Matrix([scene['native_anchor_matrix'][i:i+4] for i in range(0,16,4)]);norm=anchor.to_3x3()
kit.data.calc_loop_triangles();me=kit.data
verts=[]
for v in me.vertices:
    p=anchor@v.co/.0254;p.z+=1.1;verts.append(list(p))
data=dict(bone='tag_weapon',material='mtl_tod_cyber_sword',verts=verts,faces=[])
for tri in me.loop_triangles:
    if tri.area<1e-14:continue
    face=[]
    for li in (tri.loops[0],tri.loops[2],tri.loops[1]):
        uv=me.uv_layers.active.data[li].uv;local=me.corner_normals[li].vector
        if (anchor@tri.center/.0254).z+1.1>5:local=tri.normal
        # A weighted normal must stay in its own triangle's outward hemisphere.
        if local.dot(tri.normal)<.2:local=tri.normal
        n=(norm@local).normalized()
        face.append(dict(v=me.loops[li].vertex_index,n=list(n),uv=[uv.x,1-uv.y]))
    data['faces'].append(face)
from cyber_reference_one.native_geometry import clean
clean(data,min_altitude=.0005)
(KIT/'solid_lod0.json').write_text(json.dumps(data,separators=(',',':')))
(KIT/'lod_counts.json').write_text(json.dumps({'0':{'solid':len(data['faces'])}},indent=2))
# Preserve the bake scene as evidence; native previews are rebuilt from binaries.
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'native_baked.blend'))
manifest=dict(master='art/cyber_sword/cyber_sword.blend',master_sha256=hashlib.sha256((ART/'cyber_sword.blend').read_bytes()).hexdigest(),
              texture_size=4096,emission_scale=12,normal_convention='DirectX -Y',mesh_lift_inches=1.1,
              textures={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in IMG.glob('*.png')},triangles=len(data['faces']))
(KIT/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
print('CYBER_SWORD_NATIVE_BAKED',len(data['faces']),'triangles',flush=True)
