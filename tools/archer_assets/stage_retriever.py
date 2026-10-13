"""Through Blender MCP: bind original MOTD art and render native-scale previews."""
import bpy, sys, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/archer_assets'
SOURCE=ROOT/'source_library/archer_equipment/retriever';OUT=ROOT/'model_export/tod_archer/_images'
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel

old=bpy.data.scenes.get('Original MOTD Retriever | source review')
if old:
    for obj in list(old.objects):bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.scenes.remove(old)
for image in list(bpy.data.images):
    if image.name.startswith('i_tod_retriever_'):bpy.data.images.remove(image,do_unlink=True)
for material in list(bpy.data.materials):
    if material.name.startswith('mtl_tod_retriever_'):bpy.data.materials.remove(material,do_unlink=True)
scene=bpy.data.scenes.new('Original MOTD Retriever | source review')
bpy.context.window_manager.windows[0].scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.device='GPU'
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
except Exception:scene.cycles.device='CPU'
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
scene.world=bpy.data.worlds.new('Retriever studio ambient');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.15,.19,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
records=[];mats=[]
bindings=[('body','mtl_t6_wpn_zmb_tomahawk'),('blade','mtl_t6_wpn_zmb_tomahawk_blade'),('fringe','mtl_t6_wpn_zmb_tomahawk_alpha_world')]
for key,original in bindings:
    data=json.loads((SOURCE/'materials/mc'/(original+'.json')).read_text())
    maps={}
    for suffix, names in [('col',('colorMap','Color_Map','Diffuse_Map')),('nml',('normalMap','Normal_Map')),('spc',('specularMap','SpecularAndGloss'))]:
        t=next(t for t in data['textures'] if t.get('name') in names)
        path=SOURCE/'images'/(t['image']+'.dds')
        image=bpy.data.images.load(str(path),check_existing=False)
        if suffix!='col':image.colorspace_settings.name='Non-Color'
        values=np.array(image.pixels[:],dtype=np.float32).reshape(-1,4)
        if suffix=='nml':
            x=values[:,0]*2-1;y=values[:,1]*2-1
            values[:,2]=np.sqrt(np.maximum(0,1-x*x-y*y))*.5+.5;values[:,3]=1
            image.pixels.foreach_set(values.ravel())
        name='i_tod_retriever_'+key+'_'+suffix;target=OUT/(name+'.png')
        image.name=name;image.filepath_raw=str(target);image.file_format='PNG';image.save()
        maps[suffix]=image
        records.append({'material':key,'slot':suffix,'source':path.relative_to(ROOT).as_posix(),'file':target.relative_to(ROOT).as_posix(),'size':list(image.size)})
        if suffix=='spc':
            gloss=bpy.data.images.new('i_tod_retriever_'+key+'_gls',width=image.size[0],height=image.size[1],alpha=True)
            gloss.colorspace_settings.name='Non-Color';g=np.ones_like(values);g[:,:3]=values[:,3:4]
            gloss.pixels.foreach_set(g.ravel());gloss.filepath_raw=str(OUT/(gloss.name+'.png'));gloss.file_format='PNG';gloss.save();maps['gls']=gloss
    mat=bpy.data.materials.new('mtl_tod_retriever_'+key);mat.use_nodes=True
    n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Metallic'].default_value=.55 if key=='blade' else .12;p.inputs['Roughness'].default_value=.5
    for suffix in ('col','nml','spc','gls'):
        tex=n.new('ShaderNodeTexImage');tex.image=maps[suffix]
        if suffix=='col':l.new(tex.outputs['Color'],p.inputs['Base Color'])
        elif suffix=='nml':
            # T6/BO3 use DirectX tangent normals; flip only for this preview.
            sep=n.new('ShaderNodeSeparateXYZ');inv=n.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1
            comb=n.new('ShaderNodeCombineXYZ');normal=n.new('ShaderNodeNormalMap')
            l.new(tex.outputs['Color'],sep.inputs[0]);l.new(sep.outputs['X'],comb.inputs['X']);l.new(sep.outputs['Y'],inv.inputs[1]);l.new(inv.outputs[0],comb.inputs['Y']);l.new(sep.outputs['Z'],comb.inputs['Z']);l.new(comb.outputs[0],normal.inputs['Color']);l.new(normal.outputs[0],p.inputs['Normal'])
        elif suffix=='gls':
            inv=n.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;l.new(tex.outputs['Color'],inv.inputs[1]);l.new(inv.outputs[0],p.inputs['Roughness'])
    mats.append(mat)

source=SOURCE/'model_export/t6_wpn_zmb_tomahawk_world_lod0.xmodel_bin'
m=xmodel.Model();m.LoadFile_Bin(str(source));points=[];triangles=0
for idx,part in enumerate(m.meshes):
    verts=[v.offset for v in part.verts];points.extend(verts)
    faces=[tuple(f.indices[j].vertex for j in (0,2,1)) for f in part.faces]
    mesh=bpy.data.meshes.new('MOTD '+part.name);mesh.from_pydata(verts,[],faces);mesh.update();triangles+=len(faces)
    uv=mesh.uv_layers.new(name='UVMap')
    for poly,face in zip(mesh.polygons,part.faces):
        for loop,j in zip(poly.loop_indices,(0,2,1)):
            uv.data[loop].uv=(face.indices[j].uv[0],1-face.indices[j].uv[1])
    ob=bpy.data.objects.new('ORIGINAL RETRIEVER | '+bindings[idx][0],mesh);scene.collection.objects.link(ob);ob.data.materials.append(mats[idx])
    for poly in mesh.polygons:poly.use_smooth=True
bounds=[tuple(min(p[i] for p in points) for i in range(3)),tuple(max(p[i] for p in points) for i in range(3))]
center=(Vector(bounds[0])+Vector(bounds[1]))*.5
span=max(bounds[1][i]-bounds[0][i] for i in range(3))
camera=bpy.data.cameras.new('Retriever review camera');cam=bpy.data.objects.new('Retriever review camera',camera);scene.collection.objects.link(cam);scene.camera=cam
camera.type='ORTHO';camera.ortho_scale=span*1.35;cam.location=center+Vector((10,-80,12));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
for name,pos,power,size in [('Key',(-30,-35,55),70000,45),('Fill',(35,-15,15),35000,30),('Rim',(10,25,40),65000,30)]:
    lamp=bpy.data.lights.new(name,'AREA');lamp.energy=power;lamp.size=size;ob=bpy.data.objects.new(name,lamp);scene.collection.objects.link(ob);ob.location=center+Vector(pos);ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(ART/'preview/retriever_original.png');bpy.ops.render.render(write_still=True,scene=scene.name)
white=bpy.data.materials.get('HUD white silhouette');scene.view_layers[0].material_override=white
scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.filepath=str(OUT/'i_tod_archer_axe_hud.png');bpy.ops.render.render(write_still=True,scene=scene.name)
scene.view_layers[0].material_override=None
for im in bpy.data.images:
    if im.source=='FILE' and im.has_data:
        try:im.pack()
        except Exception:pass
(ART/'engine_kit/retriever_source.json').write_text(json.dumps({'source_model':source.relative_to(ROOT).as_posix(),'triangles':triangles,'bounds':bounds,'textures':records,'first_person_animation_fitted':False},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'archer_equipment.blend'))
print('RETRIEVER_STAGED',triangles,'triangles; original textures; HUD updated; native playtest pending')
