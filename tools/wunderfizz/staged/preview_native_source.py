"""MCP review of actual original BO6 meshes/UVs and original activation poses.

Bounded EEVEE studio uses 1K source-derived preview copies only; all native 4K
art/geometry/animation files remain untouched. Blender BRDF/alpha are approximate.
"""
import bpy,json,math,pathlib,sys,hashlib
import numpy as np
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[3]
STAGE=ROOT/'tmp/wunderfizz/assets/engine_kit'
REVIEW=ROOT/'tmp/wunderfizz/assets/review';REVIEW.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/wunderfizz/staged'))
from stage_bo6_machine import definitions,sha,OFF,ON,ACTIVATE
sys.path.insert(0,str(pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel,xanim
manifest=json.loads((STAGE/'manifest.json').read_text());pins={r['file']:sha(STAGE/r['file']) for r in manifest['files']}
defs={(kind,name):fields for name,kind,fields,block in definitions((STAGE/'source_data/tod2_bo6_wunderfizz.gdt').read_text())}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for old in list(bpy.data.materials):bpy.data.materials.remove(old,do_unlink=True)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=16
scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.13,.13,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
textures={}
def image(name):
    if name not in textures:
        preview=REVIEW/(name+'.png');assert preview.is_file(),'Prepare bounded preview images first'
        textures[name]=bpy.data.images.load(str(preview),check_existing=True)
    return textures[name]
def node_image(mat,name,noncolor=False):
    node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image(name)
    if noncolor:node.image.colorspace_settings.name='Non-Color'
    return node
for (kind,name),fields in defs.items():
    if kind!='material':continue
    mat=bpy.data.materials.new(name);mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;principled=nodes.get('Principled BSDF')
    col=node_image(mat,fields['colorMap'])
    ao=node_image(mat,fields['occMap'],True);multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
    links.new(col.outputs['Color'],multiply.inputs[1]);links.new(ao.outputs['Color'],multiply.inputs[2]);links.new(multiply.outputs[0],principled.inputs['Base Color'])
    if fields.get('specColorMap','').startswith('i_'):
        spec=node_image(mat,fields['specColorMap']);metal=nodes.new('ShaderNodeMapRange');metal.clamp=True;metal.inputs['From Min'].default_value=.04;metal.inputs['From Max'].default_value=1
        links.new(spec.outputs['Color'],metal.inputs['Value']);links.new(metal.outputs['Result'],principled.inputs['Metallic'])
    if 'transparent' in fields['materialType']:
        mat.surface_render_method='DITHERED';links.new(col.outputs['Alpha'],principled.inputs['Alpha'])
    gloss=node_image(mat,fields['cosinePowerMap'],True);invert=nodes.new('ShaderNodeMath');invert.operation='SUBTRACT';invert.inputs[0].default_value=1;links.new(gloss.outputs['Color'],invert.inputs[1]);links.new(invert.outputs[0],principled.inputs['Roughness'])
    normal=node_image(mat,fields['normalMap'],True);nm=nodes.new('ShaderNodeNormalMap');links.new(normal.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],principled.inputs['Normal'])
    if fields.get('colorMap00','').startswith('i_'):
        emission=node_image(mat,fields['colorMap00']);links.new(emission.outputs['Color'],principled.inputs['Emission Color']);principled.inputs['Emission Strength'].default_value=float(fields['scaleRGB'])
    mat['native_materialType']=fields['materialType'];mat['review_limit']='Original albedo/alpha/normals/gloss/emission; approximate Blender BRDF; 1K preview texture copies.'
def area(name,location,energy,size,target=(25,0,45)):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=location;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
area('soft white key',(115,-100,160),180000,120)
area('soft fill',(70,140,100),100000,100)
area('rim',(-90,0,130),150000,90)
bpy.ops.mesh.primitive_plane_add(size=400,location=(25,0,-.25));floor=bpy.context.object;floor.name='Review floor'
fm=bpy.data.materials.new('Review matte floor');fm.diffuse_color=(.055,.055,.065,1);floor.data.materials.append(fm)
camera_data=bpy.data.cameras.new('First-person-scale review camera');camera=bpy.data.objects.new('Review camera',camera_data);scene.collection.objects.link(camera)
camera.location=(185,-128,110);camera.rotation_euler=(Vector((25,0,46))-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=126;scene.camera=camera
anim=xanim.Anim();anim.LoadFile_Bin(str(STAGE/'xanim_export/tod2_bo6_wunderfizz'/f'{ACTIVATE}.xanim_bin'))
part_lookup={p.name:i for i,p in enumerate(anim.parts)}
native=[];records=[]
def matrix(part):
    result=np.eye(4);result[:3,:3]=np.asarray(part.matrix).T;result[:3,3]=part.offset;return result
def import_pose(asset,frame):
    for ob in native:bpy.data.objects.remove(ob,do_unlink=True)
    native.clear()
    model=xmodel.Model();model.LoadFile_Bin(str(STAGE/'model_export/tod2_bo6_wunderfizz/xmodels'/f'{asset}_LOD0.XMODEL_BIN'),split_meshes=True)
    transforms=[matrix(anim.frames[frame].parts[part_lookup[b.name]])@np.linalg.inv(matrix(b)) for b in model.bones]
    for part in model.meshes:
        verts=[]
        for v in part.verts:
            point=np.array((*v.offset,1));posed=sum((transforms[b]@point)[:3]*weight for b,weight in v.weights);verts.append(tuple(posed))
        faces=[tuple(f.indices[i].vertex for i in (0,2,1)) for f in part.faces]
        mesh=bpy.data.meshes.new('Original '+part.name);mesh.from_pydata(verts,[],faces);mesh.update()
        for material in model.materials:mesh.materials.append(bpy.data.materials[material.name])
        uv=mesh.uv_layers.new(name='Original source atlas');normals=[]
        for polygon,face in zip(mesh.polygons,part.faces):
            polygon.use_smooth=True;polygon.material_index=face.material_id
            for loop,corner in zip(polygon.loop_indices,(face.indices[i] for i in (0,2,1))):
                uv.data[loop].uv=(corner.uv[0],1-corner.uv[1]);vertex=part.verts[corner.vertex]
                normal=sum((transforms[b][:3,:3]@np.asarray(corner.normal))*weight for b,weight in vertex.weights);normal=normal/np.linalg.norm(normal);normals.append(tuple(normal))
        mesh.normals_split_custom_set(normals)
        ob=bpy.data.objects.new('SOURCE '+part.name,mesh);scene.collection.objects.link(ob);native.append(ob)
    return sum(len(m.faces) for m in model.meshes)
for name,asset,frame in [('off',OFF,0),('on',ON,0),('activation_frame50',ON,50)]:
    triangles=import_pose(asset,frame);scene.render.filepath=str(REVIEW/(name+'.png'));bpy.ops.render.render(write_still=True)
    records.append({'state':name,'source_model':asset,'source_animation_frame':frame,'triangles':triangles,'file':'tmp/wunderfizz/assets/review/'+name+'.png','sha256':sha(REVIEW/(name+'.png'))})
scene['source_preservation']='Original BO6 native LOD0 geometry/UV/material slots and actual weighted activation frame50. Native assets unchanged; 1K preview copies only.'
scene['native_limit']='Blender EEVEE BRDF/alpha approximation; no native playtest or compiled texture validation claimed.'
bpy.ops.wm.save_as_mainfile(filepath=str(REVIEW/'bo6_source_review.blend'))
assert all(sha(STAGE/path)==digest for path,digest in pins.items()),'MCP preview mutated native inputs'
result={'mcp_port':9912,'render_engine':'BLENDER_EEVEE_NEXT','render_samples':16,'resolution':[768,768],'preview_texture_size':[1024,1024],'original_native_texture_size':[4096,4096],'original_inputs_unchanged':True,'native_visual_verified':False,'native_playtested':False,'original_lod0_triangles':54481,'renders':records,'blend_file':'tmp/wunderfizz/assets/review/bo6_source_review.blend','blend_sha256':sha(REVIEW/'bo6_source_review.blend')}
(REVIEW/'review.json').write_text(json.dumps(result,indent=2)+'\n');print('BO6_NATIVE_SOURCE_PREVIEW',json.dumps(result))
