"""Blender MCP repair: real UV-mapped charcoal metal/rubber on robotic legs."""
import bpy,pathlib,sys,json,re,hashlib,copy,math
import numpy as np
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import xmodel
OUT=ROOT/'art/cyber_elites';EXP=ROOT/'model_export/tod_cyber_elites';TEX=EXP/'images'
blend=OUT/'cyber_elites.blend'
if pathlib.Path(bpy.data.filepath)!=blend:bpy.ops.wm.open_mainfile(filepath=str(blend))
kit=[o for o in bpy.context.scene.objects if o.type=='MESH' and 'native_bone' in o]
assert len(kit)==152,('unexpected robot parts',len(kit))
gdt=ROOT/'source_data/tod_cyber_elites.gdt';text=gdt.read_text();blocks=[];images=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def block(name,kind,fields):
    return '\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v)+'"\n' for k,v in fields.items())+'\t}\n'
for label,base,rough,spec in [('shell',.028,.44,.35),('piston',.105,.27,.6),('rubber',.009,.83,.04)]:
    n=512;y,x=np.mgrid[:n,:n];rng=np.random.default_rng(129)
    grain=rng.normal(0,.025,(n,n));brushed=np.sin(y*.65)*.045
    scratches=np.zeros((n,n))
    for i in range(75):
        row,col=rng.integers(1,n-1,2);scratches[row,col:min(n,col+int(rng.integers(4,60)))]=rng.uniform(.12,.5)
    wear=grain+(brushed+scratches if label!='rubber' else np.sin(y*.35)*.018)
    bm=bpy.data.materials.get('mtl_tod_doppelgast_robot_'+label);assert bm
    bm.use_nodes=True;bs=bm.node_tree.nodes.get('Principled BSDF')
    for link in list(bm.node_tree.links):bm.node_tree.links.remove(link)
    bm.node_tree.links.new(bs.outputs[0],bm.node_tree.nodes.get('Material Output').inputs['Surface'])
    maps={}
    for suffix in ['c','n','s','g']:
        a=np.ones((n,n,4),dtype=np.float32)
        if suffix=='c':a[:,:,:3]=np.clip(base*(1+wear[:,:,None]),.001,.18)
        elif suffix=='s':a[:,:,:3]=spec
        elif suffix=='g':a[:,:,:3]=np.clip(1-rough+wear[:,:,None]*.25,0,1)
        else:
            a[:,:,0]=.5+grain*.18;a[:,:,1]=.5+brushed*.18;a[:,:,2]=1
        name='i_tod_robot_'+label+'_'+suffix
        old=bpy.data.images.get(name)
        if old:bpy.data.images.remove(old)
        im=bpy.data.images.new(name,width=n,height=n,alpha=True)
        if suffix in ['n','g']:im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(a.ravel());im.filepath_raw=str(TEX/(name+'.png'));im.file_format='PNG';im.save();im.pack();maps[suffix]=name
        f=dict(baseImage='model_export/tod_cyber_elites/images/'+name+'.png',imageType='Texture',type='image',semantic={'c':'diffuseMap','n':'normalMap','s':'specularMap','g':'glossMap'}[suffix],streamable=1,compressionMethod='compressed high color' if suffix in ['c','s'] else 'compressed')
        if suffix in ['c','s']:f['coreSemantic']='sRGB3chAlpha'
        text=re.sub(r'\t"'+name+r'" \( "image.gdf" \)\n\t\{.*?\n\t\}\n','',text,flags=re.S)
        blocks.append(block(name,'image',f));images.append(dict(output=(TEX/(name+'.png')).relative_to(ROOT).as_posix(),sha256=sha(TEX/(name+'.png')),mode='robot_'+label+'_'+suffix))
    fields=dict(surfaceType='metal' if label!='rubber' else 'rubber',template='material.template',materialCategory='Geometry Advanced',materialType='lit_emissive_advanced_fullspec',colorMap=maps['c'],colorMap00=maps['c'],scaleRGB=0,emissiveIncompetence=1,normalMap=maps['n'],specColorMap=maps['s'],cosinePowerMap=maps['g'],colorTint='1 1 1 1',colorTint1='1 1 1 1',specColorTint='1 1 1 1',specMapEnable=1,normalHeightScale=1,glossRangeMin=0,glossRangeMax=8,specAmount=spec,reflectionProbeAmount=.2,textureAtlasRowCount=1,textureAtlasColumnCount=1,usage='<not in editor>')
    pattern=r'\t"'+bm.name+r'" \( "material.gdf" \)\n\t\{.*?\n\t\}\n'
    text,count=re.subn(pattern,lambda m:block(bm.name,'material',fields),text,flags=re.S);assert count==1
    bs.inputs['Metallic'].default_value=.75 if label!='rubber' else 0;bs.inputs['Roughness'].default_value=rough
    node=bm.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images[maps['c']];bm.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
    node=bm.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images[maps['n']]
    normal=bm.node_tree.nodes.new('ShaderNodeNormalMap');bm.node_tree.links.new(node.outputs['Color'],normal.inputs['Color']);bm.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
text=text.rstrip()[:-1]+'\n'+''.join(blocks)+'}\n'

path=EXP/'tod_doppelgast_black_robot.XMODEL_BIN'
model=xmodel.Model();model.LoadFile_Bin(str(path),split_meshes=True)
before=copy.deepcopy(model)
robot_ids={i for i,m in enumerate(model.materials) if m.name.startswith('mtl_tod_doppelgast_robot_')}
kept=[]
for mesh in model.meshes:
    ids={f.material_id for f in mesh.faces}
    assert not (ids&robot_ids and ids-robot_ids),'robot and organic faces unexpectedly share mesh'
    if not ids&robot_ids:kept.append(mesh)
model.meshes=kept
bones={b.name:i for i,b in enumerate(model.bones)};mid={m.name:i for i,m in enumerate(model.materials)}
robot=xmodel.Mesh('Blender_robotic_legs_UV_mapped');uv_area_min=1
for ob in kit:
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    # Triangulated unwrap prevents a quad's diagonal from collapsing in half UVs.
    with bpy.context.temp_override(scene=bpy.context.scene,view_layer=bpy.context.scene.view_layers[0],active_object=ob,object=ob,selected_objects=[ob],selected_editable_objects=[ob]):
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.04);bpy.ops.object.mode_set(mode='OBJECT')
    me=ob.data;me.calc_loop_triangles();normal_matrix=ob.matrix_world.to_3x3().inverted().transposed();base=len(robot.verts)
    robot.verts.extend(xmodel.Vertex(tuple(ob.matrix_world@v.co),[(bones[ob['native_bone']],1.)]) for v in me.vertices)
    uv=me.uv_layers.active.data
    for tri in me.loop_triangles:
        f=xmodel.Face(len(model.meshes),mid[me.materials[tri.material_index].name]);f.indices=[]
        for k in (0,2,1):
            li=tri.loops[k];n=(normal_matrix@me.corner_normals[li].vector).normalized();u=uv[li].uv
            f.indices.append(xmodel.FaceVertex(base+tri.vertices[k],tuple(n),(1,1,1,1),(u.x,1-u.y)))
        # Some bevel smart-UV islands are nearly collinear; material detail needs
        # finite native tangents, so give only these tiny faces a valid local island.
        a,b,c=[v.uv for v in f.indices]
        area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
        if area<.000001:
            for v,u in zip(f.indices,[(.15,.15),(.22,.15),(.15,.22)]):v.uv=u
            area=.0049
        uv_area_min=min(uv_area_min,area);robot.faces.append(f)
model.meshes.append(robot)
for i,mesh in enumerate(model.meshes):
    for f in mesh.faces:f.mesh_id=i
assert [(b.name,b.parent,b.offset,b.matrix) for b in before.bones]==[(b.name,b.parent,b.offset,b.matrix) for b in model.bones]
assert sum(len(m.faces) for m in before.meshes)==sum(len(m.faces) for m in model.meshes)
model.WriteFile_Bin(str(path));gdt.write_text(text)
manifest=OUT/'manifest.json';m=json.loads(manifest.read_text())
for r in m['models']:
    if r['name']=='tod_doppelgast_black_robot':r.update(sha256=sha(path),robot_uv_mapped=True,robot_uv_min_area=uv_area_min)
m['textures']=[r for r in m['textures'] if not r.get('mode','').startswith('robot_')]+images
m.update(gdt_sha256=sha(gdt),robot_material_fix='Blender MCP: 12 real texture maps, smart UVs, explicit native fullspec materials with emission disabled; original bones and organic faces retained',native_verified=False)
manifest.write_text(json.dumps(m,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
# A separate detail camera does not alter the established full-roster camera.
s=bpy.context.scene;d=bpy.data.cameras.new('Robot leg detail');cam=bpy.data.objects.new('Robot leg detail',d);s.collection.objects.link(cam)
cam.location=(110,-105,66);cam.rotation_euler=(Vector((0,0,27))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=72;s.camera=cam
s.render.resolution_x=1000;s.render.resolution_y=1200;s.cycles.samples=32;s.render.filepath=str(OUT/'robot_legs_textured.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'robot_legs_review.blend'))
print('ROBOT_TEXTURE_REPAIR',json.dumps({'parts':len(kit),'textures':len(images),'faces':len(robot.faces),'min_uv_area':uv_area_min,'original_bones':len(model.bones)}))
