"""Blender MCP: preserve Alcatraz's hand rig and bake decoded T6 local keys to T7.

The offhand uses its original hand model, avoiding an approximate T7 retarget.
All transforms are inches; XANIM_EXPORT stores evaluated world-space matrices.
"""
import bpy, sys, json, copy, math, hashlib, subprocess
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/archer_assets'))
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel,xanim
from read_t6_anim import read
from install_native import block
SRC=ROOT/'source_library/archer_equipment/bo2_motd/20260925_050624_055906_dump/dump/so_zclassic_zm_prison'
RET=ROOT/'source_library/archer_equipment/retriever'
OUT=ROOT/'model_export/tod_archer';ANIM=ROOT/'xanim_export/tod_archer';ANIM.mkdir(exist_ok=True,parents=True)
ART=ROOT/'art/archer_assets';blocks=[];records=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def mat(b):
    m=Matrix(b.matrix).transposed().to_4x4();m.translation=b.offset;return m

def store(b,m):
    b.offset=tuple(m.translation);b.matrix=[tuple(r) for r in m.to_3x3().transposed()]

def keys(values,f,rotation=False):
    if not values:return None
    lo=next((k for k in reversed(values) if k[0]<=f),values[0]);hi=next((k for k in values if k[0]>=f),values[-1])
    t=0 if lo[0]==hi[0] else (f-lo[0])/(hi[0]-lo[0])
    if rotation:
        q=lambda k:Quaternion((k[1][3],*k[1][:3])).normalized()
        return q(lo).slerp(q(hi),t)
    return Vector(lo[1]).lerp(Vector(hi[1]),t)

hands=xmodel.Model();hands.LoadFile_Bin(str(SRC/'model_export/c_zom_arlington_coat_viewhands_lod0.xmodel_bin'))
weapon=xmodel.Model();weapon.LoadFile_Bin(str(RET/'model_export/t6_wpn_zmb_tomahawk_view_lod0.xmodel_bin'))
for material in weapon.materials:
    material.name='mtl_tod_retriever_'+('blade' if material.name.endswith('_blade') else 'fringe' if '_alpha' in material.name else 'body')
viewpath=OUT/'tod_archer_retriever_view.xmodel_bin';weapon.WriteFile_Bin(str(viewpath),version=7)
blocks.append(block('tod_archer_retriever_view','xmodel',{'filename':'tod_archer/'+viewpath.name,'type':'animated','scale':1,'BulletCollisionLOD':'None','CollisionMap':''}))
materials=[]
for index,material in enumerate(hands.materials):
    d=json.loads((SRC/'materials'/(material.name+'.json')).read_text());name='mtl_tod_archer_hands_'+str(index);material.name=name
    bm=bpy.data.materials.get(name) or bpy.data.materials.new(name);bm.use_nodes=True
    p=bm.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.65
    fields={'materialCategory':'Geometry','materialType':'lit','surfaceType':'cloth','template':'material.template','colorTint':'1 1 1 1','specMapEnable':1,'normalHeightScale':1,'usage':'<not in editor>'}
    for slot,semantic in [('col','colorMap'),('nml','normalMap'),('spc','specularMap')]:
        t=next(t for t in d['textures'] if t['semantic']==semantic)
        source=SRC/'images'/(t['image']+'.dds')
        if not source.exists():source=next((ROOT/'source_library/archer_equipment/bo2_motd').rglob(t['image']+'.dds'))
        asset_name='i_tod_archer_hands_'+str(index)+'_'+slot
        im=bpy.data.images.load(str(source),check_existing=False);im.name=asset_name
        if slot!='col':im.colorspace_settings.name='Non-Color'
        pixels=np.asarray(im.pixels[:],dtype=np.float32).reshape(-1,4)
        if slot=='nml':
            pixels[:,2]=np.sqrt(np.maximum(0,1-(pixels[:,0]*2-1)**2-(pixels[:,1]*2-1)**2))*.5+.5;pixels[:,3]=1
            im.pixels.foreach_set(pixels.ravel())
        target=OUT/'_images'/(asset_name+'.png');im.filepath_raw=str(target);im.file_format='PNG';im.save()
        fields[{'col':'colorMap','nml':'normalMap','spc':'specColorMap'}[slot]]=asset_name
        imagefields={'baseImage':target.relative_to(ROOT).as_posix(),'imageType':'Texture','semantic':{'col':'diffuseMap','nml':'normalMap','spc':'specularMap'}[slot],'streamable':1,'compressionMethod':'compressed high color' if slot!='nml' else 'compressed'}
        if slot!='nml':imagefields['coreSemantic']='sRGB3chAlpha'
        blocks.append(block(asset_name,'image',imagefields))
        if slot=='col':
            tex=bm.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;bm.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
            if index==1:bm.node_tree.links.new(tex.outputs['Alpha'],p.inputs['Alpha'])
        records.append({'source':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source),'file':target.relative_to(ROOT).as_posix(),'size':list(im.size)})
    if index==1:fields.update({'materialType':'lit_alphatest','alphaTest':'GE128'})
    blocks.append(block(name,'material',fields));materials.append(bm)
handpath=OUT/'tod_archer_bo2_hands.xmodel_bin';hands.WriteFile_Bin(str(handpath),version=7)
blocks.append(block('tod_archer_bo2_hands','xmodel',{'filename':'tod_archer/'+handpath.name,'type':'animated','scale':1,'BulletCollisionLOD':'None','CollisionMap':''}))

scene=bpy.data.scenes.get('BO2 native first person')
if scene:
    for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.scenes.remove(scene)
scene=bpy.data.scenes.new('BO2 native first person');bpy.context.window_manager.windows[0].scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('First person review');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.08,.10,.13,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
camdata=bpy.data.cameras.new('Native view +X');cam=bpy.data.objects.new('Native view +X',camdata);scene.collection.objects.link(cam)
cam.location=(0,0,0);cam.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler();camdata.lens=20;camdata.clip_start=.01;scene.camera=cam
for pos,power in [((15,0,22),10000),((3,-22,8),6000)]:
    light=bpy.data.lights.new('View light','AREA');light.energy=power;light.size=20
    ob=bpy.data.objects.new('View light',light);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((15,0,-5))-ob.location).to_track_quat('-Z','Y').to_euler()
animation_records=[]
clips=[('hold','viewmodel_hatchet_idle','tag_knife_attach'),('throw','viewmodel_hatchet_throw','tag_knife_attach'),('flourish','viewmodel_zomb_tomahawk_first_raise','tag_weapon'),('flourish_idle','viewmodel_zomb_tomahawk_idle','tag_weapon')]
for clip,source_name,attachment in clips:
    source=next(RET.rglob(source_name));a=read(source)
    combined=copy.deepcopy(hands);n=len(combined.bones);parent=next(i for i,b in enumerate(hands.bones) if b.name==attachment)
    attach=mat(hands.bones[parent])
    for bone in weapon.bones:
        b=copy.deepcopy(bone);b.parent=parent if bone.parent<0 else n+bone.parent;store(b,attach@mat(bone));combined.bones.append(b)
    # Conversion model only: native rendered gun and hands are independent DObjs.
    conversion=OUT/('tod_archer_'+clip+'_rig.xmodel_bin');combined.WriteFile_Bin(str(conversion),version=7)
    bind=[mat(b) for b in combined.bones]
    local=[bind[b.parent].inverted()@bind[i] if b.parent>=0 else bind[i] for i,b in enumerate(combined.bones)]
    output=xanim.Anim();output.framerate=a['fps'];output.parts=[xanim.PartInfo(b.name) for b in combined.bones]
    poses=[]
    for f in range(a['frames']):
        world=[];frame=xanim.Frame(f)
        for i,b in enumerate(combined.bones):
            l=local[i].copy();track=a['tracks'].get(b.name)
            if track:
                pos=keys(track['pos'],f);rot=keys(track['rot'],f,True)
                if i>=n:
                    # CoD viewmodel j_gun descendants use bind-relative keys;
                    # hand tracks are absolute local transforms (Greyhound's
                    # CoDXAnimTranslator documents this per-game distinction).
                    delta=rot.to_matrix().to_4x4() if rot else Matrix.Identity(4)
                    if pos is not None:delta.translation=pos
                    l=local[i]@delta
                else:
                    if rot:l=rot.to_matrix().to_4x4();l.translation=local[i].translation
                    if pos is not None:l.translation=pos
            w=world[b.parent]@l if b.parent>=0 else l;world.append(w)
            frame.parts.append(xanim.FramePart(tuple(w.translation),[tuple(r) for r in w.to_3x3().transposed()]))
        poses.append(world);output.frames.append(frame)
    path=ANIM/('tod_archer_'+clip+'.xanim_bin');output.WriteFile_Bin(str(path))
    fields={'filename':'tod_archer/'+path.name,'model':'tod_archer/'+conversion.name,'type':'absolute','looping':int(clip in ('hold','flourish_idle')),'useBones':0,'leftHandGripIK':0,'translationError':.025,'angleError':.05}
    for ni,note in enumerate(a['notes']):
        # T7's executable sound action lives in GDT, not an inert T6 sndnt#
        # marker. PyCoD's old embedded-note binary token is rejected by T7.
        alias=note['name'].replace('sndnt#zmb_tomahawk_first_raise','tod_archer_axe_first_raise')
        fields.update({f'customnote{ni}action':'2D Sound',f'customnote{ni}actionparam1':alias,f'customnote{ni}actionparam2':'',f'customnote{ni}frame':note['frame'],f'customnote{ni}useexistingnote':''})
    if a['notes']:
        raw=path.with_suffix('.XANIM_EXPORT');output.WriteFile_Raw(str(raw))
        raw.write_text(raw.read_text().split('NOTETRACKS')[0]+'NUMKEYS 0\n')
        result=subprocess.run(['C:/BO3Tools/TOD2Cybercity/bin/export2bin.exe',raw.name],cwd=ANIM,capture_output=True,text=True,timeout=120)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    blocks.append(block('tod_archer_'+clip,'xanim',fields))
    animation_records.append({'asset':'tod_archer_'+clip,'source':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source),'frames':a['frames'],'fps':a['fps'],'bones':len(combined.bones),'attachment':attachment,'file':path.relative_to(ROOT).as_posix(),'sha256':sha(path)})
    # Skin the source meshes using the same evaluated poses used by XANIM.
    for original,base,mats in [(hands,0,materials),(weapon,n,[bpy.data.materials.get(m.name) for m in weapon.materials])]:
        for mi,mesh in enumerate(original.meshes):
            points=[tuple(v.offset) for v in mesh.verts]
            if base:points=[tuple(attach@Vector(p)) for p in points]
            faces=[tuple(f.indices[j].vertex for j in (0,2,1)) for f in mesh.faces]
            data=bpy.data.meshes.new(clip+' mesh');data.from_pydata(points,[],faces);data.update()
            uv=data.uv_layers.new()
            for poly,face in zip(data.polygons,mesh.faces):
                for loop,j in zip(poly.loop_indices,(0,2,1)):uv.data[loop].uv=(face.indices[j].uv[0],1-face.indices[j].uv[1])
            ob=bpy.data.objects.new(clip+' '+str(base)+' '+str(mi),data);scene.collection.objects.link(ob)
            for material in mats:
                data.materials.append(material)
            for poly,face in zip(data.polygons,mesh.faces):poly.material_index=face.material_id
            for poly in data.polygons:poly.use_smooth=True
            ob.shape_key_add(name='Bind')
            for f,pose in enumerate(poses):
                key=ob.shape_key_add(name='Frame '+str(f));key.value=0
                for vi,v in enumerate(mesh.verts):
                    point=Vector(points[vi]);value=Vector((0,0,0))
                    for bone,weight in v.weights:value+=(pose[base+bone]@bind[base+bone].inverted()@point)*weight
                    key.data[vi].co=value
                key.value=1;key.keyframe_insert(data_path='value',frame=f+1)
                if f>0:key.value=0;key.keyframe_insert(data_path='value',frame=f)
                key.value=0;key.keyframe_insert(data_path='value',frame=f+2)
            ob.hide_render=clip!='hold';ob.hide_viewport=clip!='hold'
    scene.frame_set(1)
scene.frame_start=1;scene.frame_end=48
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ART/'preview/bo2_hold.png')
bpy.ops.render.render(write_still=True,scene=scene.name)
gdt=ROOT/'source_data/tod_archer_motion.gdt';gdt.write_text('{\n'+''.join(blocks)+'}\n')
(ART/'engine_kit/native_motion.json').write_text(json.dumps({'hands_source':str(SRC.relative_to(ROOT)),'hand_triangles':sum(len(m.faces) for m in hands.meshes),'view_triangles':sum(len(m.faces) for m in weapon.meshes),'textures':records,'animations':animation_records},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'archer_equipment.blend'))
print('NATIVE_BO2_MOTION',[(r['asset'],r['frames'],r['fps']) for r in animation_records])
