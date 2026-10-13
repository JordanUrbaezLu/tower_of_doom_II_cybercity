"""MCP placement review: actual current crown solids and all native mount transforms."""
import bpy,json,pathlib,sys,math,hashlib
from mathutils import Vector,Matrix
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/crown_alarm'
sys.path.insert(0,str(ROOT/'tools'))
from art_cohesion.native_preview import fullspec
source=bpy.context.scene;source.frame_set(1);bpy.context.view_layer.update()
parts=[(o.name,o.data,o.matrix_world.copy(),o['alarm_group']) for o in source.objects if o.type=='MESH' and 'alarm_group' in o]
assert len(parts)==64
scene=bpy.data.scenes.new('Actual crown - alarm placement review');bpy.context.window.scene=scene
origin=Vector((0,8608,19392));inventory=json.loads((ROOT/'art/cybercity_materials/crown_inventory.json').read_text())
kit=json.loads((ROOT/'tools/art_cohesion/crown_materials.json').read_text())['materials']
mats={name:fullspec(ROOT/'source_data/tod_surface.gdt','tod_cc_'+name,ROOT/'model_export/tod_surface/_images') for name in kit}
for row in inventory['rows']:
    vs=[];faces=[];uvs=[];ids=[];slots=[]
    for face in row['faces']:
        role=face['mat'].removeprefix('tod_cc_')
        if role not in slots:slots.append(role)
        axis=max(range(3),key=lambda i:abs(face['n'][i]));size=kit[role]['size'];indices=[]
        for p in face['vertices']:
            indices.append(len(vs));vs.append(tuple(Vector(p)-origin));uvs.append(((p[1] if axis==0 else p[0])/size,(p[1] if axis==2 else p[2])/size))
        faces.append(indices);ids.append(slots.index(role))
    me=bpy.data.meshes.new(row['label']);me.from_pydata(vs,[],faces);me.update()
    for role in slots:me.materials.append(mats[role])
    uv=me.uv_layers.new()
    for poly,mi in zip(me.polygons,ids):
        poly.material_index=mi
        for li in poly.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
    ob=bpy.data.objects.new(row['label'],me);scene.collection.objects.link(ob)
mounts=json.loads((ART/'mounts.json').read_text())
native_parts=[]
for name,me,mw,group in parts:
    copy=me.copy()
    for i,mat in enumerate(copy.materials):
        if mat.name=='mtl_tod_alarm_lamp_off':copy.materials[i]=bpy.data.materials['mtl_tod_alarm_lamp_on']
    native_parts.append((name,copy,mw,group))
for i,m in enumerate(mounts):
    pitch,yaw,roll=m['angles'];transform=Matrix.Translation(Vector(m['org'])-origin)@Matrix.Rotation(math.radians(yaw),4,'Z')@Matrix.Rotation(math.radians(pitch),4,'Y')@Matrix.Scale(m['scale'],4)
    for name,me,mw,group in native_parts:
        ob=bpy.data.objects.new(str(i)+' '+m['kind']+' | '+name,me);scene.collection.objects.link(ob);ob.matrix_world=transform@mw
scene.world=bpy.data.worlds.new('Neutral placement review');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.17,.2,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
d=bpy.data.lights.new('Neutral architecture review sun','SUN');d.energy=2;d.angle=.18;ob=bpy.data.objects.new(d.name,d);scene.collection.objects.link(ob);ob.rotation_euler=(.5,-.3,-.4)
d=bpy.data.lights.new('Neutral hall fill','AREA');d.energy=16000000;d.size=1100;ob=bpy.data.objects.new(d.name,d);scene.collection.objects.link(ob);ob.location=(0,-350,750)
d=bpy.data.cameras.new('Mount inspection');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam;d.clip_end=100000
cam.location=Vector((100,8050,19464))-origin;cam.rotation_euler=(Vector((0,8650,19740))-origin-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=22
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
scene.render.filepath=str(ART/'hall_mounts.png');scene['preview_limit']='Current native architecture/mounts; neutral Blender illumination; runtime spotlight, sky and gameplay props omitted.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'mount_review.blend'))
print('CROWN_ALARM_MOUNTS_REVIEW',len(mounts),'fixtures',len(inventory['rows']),'current architectural pieces')
