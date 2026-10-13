"""MCP: preview actual exported staff and viewhands with native frame transforms."""
import bpy,pathlib,sys,json,math
from mathutils import Vector,Matrix
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import xmodel,asset,native_path
from PyCoD import xanim
ART=ROOT/'art/necro_staff'
bpy.ops.wm.open_mainfile(filepath=str(ART/'staff_review.blend'))
scene=bpy.context.scene
for ob in list(scene.objects):
    if ob.type=='MESH':bpy.data.objects.remove(ob,do_unlink=True)
scene.render.resolution_x=1280;scene.render.resolution_y=720
def mat(p):
    m=Matrix(p.matrix).transposed().to_4x4();m.translation=p.offset;return m
def load(p):
    a=xanim.Anim();a.LoadFile_Bin(str(p));return a
anims=json.loads((ART/'animations.json').read_text())
cases=[('idle',anims['slots']['idleAnim'],0),('channel',anims['slots']['holdFireLoopAnim'],16),('summon',anims['slots']['adsUpAnim'],-1),('raise',anims['slots']['raiseAnim'],10)]
handpath=native_path('model_export',asset('xmodel','c_t7_mp_warrior_viewarms1')['filename'])
handmat=bpy.data.materials.new('Viewhands neutral rig check');handmat.diffuse_color=(.22,.15,.10,1)
cam=scene.camera;cam.data.type='PERSP';cam.data.lens=20;cam.data.sensor_width=36;cam.data.clip_start=.05;cam.location=(0,0,0);cam.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler()
for ob in scene.objects:
    if ob.type=='LIGHT':ob.data.energy*=.12
# Neutral camera-side fill for judging the baked surface and hand contact.
# This belongs only to the review scene, never to the weapon or map lighting.
fill=bpy.data.lights.new('Pose review camera-side softbox','AREA');fill.energy=45000;fill.size=28
lamp=bpy.data.objects.new(fill.name,fill);scene.collection.objects.link(lamp);lamp.location=(0,-25,28)
lamp.rotation_euler=(Vector((35,-10,5))-lamp.location).to_track_quat('-Z','Y').to_euler()
for tier in [2,3]:
    for label,clipname,fi in cases:
        for ob in list(scene.objects):
            if ob.type=='MESH':bpy.data.objects.remove(ob,do_unlink=True)
        clip=load(ROOT/'xanim_export/tod_necro_staff'/(clipname+'.XANIM_BIN'));idx={p.name:i for i,p in enumerate(clip.parts)};frame=clip.frames[fi]
        if len(clip.parts)<20:
            # Native movement/ADS clips are additive layers, not full poses.
            layer={p.name:mat(frame.parts[i]) for i,p in enumerate(clip.parts)}
            clip=load(ROOT/'xanim_export/tod_necro_staff'/(anims['slots']['idleAnim']+'.XANIM_BIN'));idx={p.name:i for i,p in enumerate(clip.parts)};frame=clip.frames[0]
        for path,hands in [(ROOT/f'model_export/tod_necro_staff/tod_necro_staff{tier}_view_lod0.XMODEL_BIN',False),(handpath,True)]:
            model=xmodel.Model();model.LoadFile_Bin(str(path),split_meshes=True)
            poses=[]
            for b in model.bones:
                if b.name.lower() in idx:p=mat(frame.parts[idx[b.name.lower()]])
                elif b.parent>=0:p=poses[b.parent]@mat(model.bones[b.parent]).inverted()@mat(b)
                else:p=mat(b)
                poses.append(p)
            transforms=[p@mat(b).inverted() for p,b in zip(poses,model.bones)]
            for mesh in model.meshes:
                vertices=[]
                for v in mesh.verts:
                    pos=Vector((0,0,0))
                    for bi,w in v.weights:pos+=(transforms[bi]@Vector(v.offset))*w
                    vertices.append(tuple(pos if v.weights else Vector(v.offset)))
                faces=[tuple(i.vertex for i in reversed(f.indices)) for f in mesh.faces]
                data=bpy.data.meshes.new(mesh.name);data.from_pydata(vertices,[],faces)
                for material in model.materials:data.materials.append(handmat if hands else bpy.data.materials[material.name])
                uv=data.uv_layers.new()
                for poly,f in zip(data.polygons,mesh.faces):
                    poly.material_index=f.material_id;poly.use_smooth=True
                    for li,i in zip(poly.loop_indices,reversed(f.indices)):uv.data[li].uv=(i.uv[0],1-i.uv[1])
                ob=bpy.data.objects.new(mesh.name,data);scene.collection.objects.link(ob)
        scene.render.filepath=str(ART/f'tier{tier}_vm_{label}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'first_person_review.blend'))
print('NECRO_STAFF_NATIVE_POSE_REVIEW',len(cases)*2,'views')
