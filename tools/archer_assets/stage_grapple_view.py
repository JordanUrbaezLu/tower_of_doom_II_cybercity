"""Blender MCP: fit the recovered grapple part to an authored wrist housing.

Uses the same Alcatraz arm rig as the Retriever; the grapple presentation is
custom (BO2 has no Pathfinder grapple). Native BO3 item raises/holds/lowers it.
"""
import bpy,sys,json,copy,math
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/archer_assets'))
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel,xanim
from install_native import block
OUT=ROOT/'model_export/tod_archer';ANIM=ROOT/'xanim_export/tod_archer';blocks=[]
def matrix(b):
    m=Matrix(b.matrix).transposed().to_4x4();m.translation=b.offset;return m
def store(b,m):
    b.offset=tuple(m.translation);b.matrix=[tuple(r) for r in m.to_3x3().transposed()]
hands=xmodel.Model();hands.LoadFile_Bin(str(OUT/'tod_archer_bo2_hands.xmodel_bin'))
wrist=next(i for i,b in enumerate(hands.bones) if b.name=='j_wrist_le')
bone=xmodel.Bone('tag_grapple');bone.parent=wrist;store(bone,matrix(hands.bones[wrist]));hands.bones.append(bone)
handpath=OUT/'tod_archer_grapple_hands.xmodel_bin';hands.WriteFile_Bin(str(handpath),version=7)
blocks.append(block('tod_archer_grapple_hands','xmodel',{'filename':'tod_archer/'+handpath.name,'type':'animated','scale':1,'BulletCollisionLOD':'None','CollisionMap':''}))
old=bpy.data.scenes.get('Grapple first person')
if old:
    for ob in list(old.objects):bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.scenes.remove(old)
scene=bpy.data.scenes.new('Grapple first person');bpy.context.window_manager.windows[0].scene=scene
mat=bpy.data.materials.get('mtl_tod_archer_launcher') or bpy.data.materials.new('mtl_tod_archer_launcher');mat.use_nodes=True
p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.04,.065,.075,1);p.inputs['Metallic'].default_value=.85;p.inputs['Roughness'].default_value=.3
# Housing dimensions are inches and deliberately sit above the wrist skin.
bpy.ops.mesh.primitive_cube_add(size=1,location=(.3,1.65,0));housing=bpy.context.object;housing.name='Grapple wrist housing'
housing.dimensions=(4.2,1.25,2.4);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bevel=housing.modifiers.new('Machined edges','BEVEL');bevel.width=.14;bevel.segments=3
bpy.context.view_layer.objects.active=housing;bpy.ops.object.modifier_apply(modifier=bevel.name);housing.data.materials.append(mat)
source=json.loads((ROOT/'art/archer_assets/engine_kit/pathfinder_prop.json').read_text())
# Source Z points down the length of this component; mount it along wrist +X.
transform=Matrix.Rotation(math.pi/2,4,'Y');transform.translation=(1.6,1.65,0)
verts=[tuple(transform@Vector(v)) for v in source['verts']]
faces=[tuple(c['v'] for c in f) for f in source['faces']]
mesh=bpy.data.meshes.new('Recovered Pathfinder grapple head');mesh.from_pydata(verts,[],faces);mesh.update()
uv=mesh.uv_layers.new()
for poly,face in zip(mesh.polygons,source['faces']):
    for loop,corner in zip(poly.loop_indices,face):uv.data[loop].uv=(corner['uv'][0],1-corner['uv'][1])
tip=bpy.data.objects.new('Recovered Pathfinder grapple head',mesh);scene.collection.objects.link(tip)
tip.data.materials.append(bpy.data.materials.get('pathfinder_prop') or bpy.data.materials.get('mtl_tod_archer_pathfinder_prop') or mat)
native=xmodel.Model();root=xmodel.Bone('tag_grapple_model');root.parent=-1;store(root,Matrix.Identity(4));native.bones=[root]
native.materials=[xmodel.Material('mtl_tod_archer_launcher','Phong',{}),xmodel.Material('mtl_tod_archer_pathfinder_prop','Phong',{})]
for index,ob in enumerate((housing,tip)):
    data=ob.data;data.calc_loop_triangles();part=xmodel.Mesh(ob.name)
    part.verts=[xmodel.Vertex(tuple(ob.matrix_world@v.co),[(0,1)]) for v in data.vertices]
    for tri in data.loop_triangles:
        face=xmodel.Face(index,index);corners=[]
        for loop in tri.loops:
            vi=data.loops[loop].vertex_index;normal=ob.matrix_world.to_3x3()@data.vertices[vi].normal
            uvcoord=data.uv_layers.active.data[loop].uv if data.uv_layers.active else (0,0)
            corners.append(xmodel.FaceVertex(vi,tuple(normal),(1,1,1,1),(uvcoord[0],1-uvcoord[1])))
        face.indices=corners;part.faces.append(face)
    native.meshes.append(part)
viewpath=OUT/'tod_archer_grapple_view.xmodel_bin';native.WriteFile_Bin(str(viewpath),version=7)
blocks.append(block('tod_archer_grapple_view','xmodel',{'filename':'tod_archer/'+viewpath.name,'type':'animated','scale':1,'BulletCollisionLOD':'None','CollisionMap':''}))
blocks.append(block('mtl_tod_archer_launcher','material',{'materialCategory':'Geometry','materialType':'lit','template':'material.template','colorMap':'$white_diffuse','colorTint':'.12 .18 .2 1','normalMap':'$identitynormalmap','specColorMap':'$white_specular','specMapEnable':1,'specAmount':.8,'glossRangeMin':5,'glossRangeMax':8,'surfaceType':'metal','usage':'<not in editor>'}))
motion=xanim.Anim();motion.LoadFile_Bin(str(ANIM/'tod_archer_throw.xanim_bin'))
rig=copy.deepcopy(hands);b=copy.deepcopy(root);b.parent=len(hands.bones)-1;store(b,matrix(hands.bones[-1]));rig.bones.append(b)
rigpath=OUT/'tod_archer_grapple_rig.xmodel_bin';rig.WriteFile_Bin(str(rigpath),version=7)
lookup={p.name:i for i,p in enumerate(motion.parts)}
for name,frames in [('raise',range(5)),('idle',[4]),('lower',range(4,-1,-1))]:
    output=xanim.Anim();output.framerate=30;output.parts=[xanim.PartInfo(b.name) for b in rig.bones]
    for fi,source_frame in enumerate(frames):
        frame=xanim.Frame(fi);source=motion.frames[source_frame]
        for b in rig.bones:
            part=source.parts[lookup[b.name if b.name in lookup else 'j_wrist_le']]
            frame.parts.append(copy.deepcopy(part))
        output.frames.append(frame)
    file=ANIM/('tod_archer_grapple_'+name+'.xanim_bin');output.WriteFile_Bin(str(file))
    blocks.append(block('tod_archer_grapple_'+name,'xanim',{'filename':'tod_archer/'+file.name,'model':'tod_archer/'+rigpath.name,'type':'absolute','looping':int(name=='idle'),'useBones':0,'leftHandGripIK':0}))
weapon={'displayName':'Grapple','weaponType':'grenade','weaponClass':'grenade','inventoryType':'item','playerAnimType':'hatchet','offhandSlot':'None','offhandClass':'None','gunModel':'tod_archer_grapple_view','handModel':'tod_archer_grapple_hands','worldModel':'tod_archer_hook','viewmodelTag':'tag_grapple','idleAnim':'tod_archer_grapple_idle','emptyIdleAnim':'tod_archer_grapple_idle','firstRaiseAnim':'tod_archer_grapple_raise','raiseAnim':'tod_archer_grapple_raise','quickRaiseAnim':'tod_archer_grapple_raise','emptyRaiseAnim':'tod_archer_grapple_raise','dropAnim':'tod_archer_grapple_lower','quickDropAnim':'tod_archer_grapple_lower','emptyDropAnim':'tod_archer_grapple_lower','firstRaiseTime':.167,'raiseTime':.167,'quickRaiseTime':.167,'emptyRaiseTime':.167,'dropTime':.167,'quickDropTime':.167,'emptyDropTime':.167,'isHoldUseGrenade':1,'clipSize':0,'startAmmo':0,'maxAmmo':0,'damage':0,'dontTakeClipOnlyWeaponIfEmpty':1,'adsSupported':0}
blocks.append(block('tod_archer_grapple_view','grenadeweapon',weapon))
(ROOT/'source_data/tod_archer_grapple_view.gdt').write_text('{\n'+''.join(blocks)+'}\n')
# Native view preview: same evaluated hand pose and attachment used above.
source_scene=bpy.data.scenes['BO2 native first person'];source_scene.frame_set(5)
for ob in source_scene.objects:
    if ob.type=='MESH' and ob.name.startswith('throw 0 '):
        copied=ob.copy();copied.data=ob.data.copy();scene.collection.objects.link(copied);copied.hide_render=False;copied.hide_viewport=False
        for poly in copied.data.polygons:poly.use_smooth=True
wp=motion.frames[4].parts[lookup['j_wrist_le']];mount=Matrix(wp.matrix).transposed().to_4x4();mount.translation=wp.offset
housing.matrix_world=mount@housing.matrix_world;tip.matrix_world=mount@tip.matrix_world
cam=source_scene.camera.copy();cam.data=source_scene.camera.data.copy();scene.collection.objects.link(cam);scene.camera=cam
for ob in source_scene.objects:
    if ob.type=='LIGHT':scene.collection.objects.link(ob)
scene.world=source_scene.world;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100;scene.frame_set(5)
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'art/archer_assets/preview/grapple_first_person.png')
bpy.ops.render.render(write_still=True,scene=scene.name)
(ROOT/'art/archer_assets/engine_kit/grapple_view.json').write_text(json.dumps({'source_component':'original Apex pathfinder_grapplehook','housing':'Blender authored wrist mount','triangles':sum(len(m.faces) for m in native.meshes),'hand_pose':'BO2 arm motion fitted to wrist mount','runtime':'native BO3 inventory item, not a camera-linked world prop','animations':['raise','idle','lower'],'native_tested':False},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/archer_assets/archer_equipment.blend'))
print('GRAPPLE_NATIVE_VIEW',sum(len(m.faces) for m in native.meshes),'triangles')
