"""Preservation and pose validation in the actual live Blender session."""
import sys,importlib,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import equipment;importlib.reload(equipment)
from equipment import *
assert json.loads(scene['donor_signatures'])=={o.name:signature(o) for o in base}
parts=[o for o in scene.objects if 'attachment_bone' in o]
for ob in parts:
    assert ob.get('equipment_revision')==6
    assert ob.get('attachment_bone') in rig.data.bones
    assert all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in ob.data.vertices),ob.name
    assert all(all(math.isfinite(x) for x in v.co) for v in ob.data.vertices)
    title=ob.name.split(' |')[0]
    coll=bpy.data.collections.get('Equipment / '+title)
    if coll is None:coll=bpy.data.collections.new('Equipment / '+title);scene.collection.children.link(coll)
    for old in list(ob.users_collection):old.objects.unlink(ob)
    coll.objects.link(ob)
for pb in rig.pose.bones:pb.rotation_euler=(0,0,0)
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
neutral={};tris=0
for ob in parts:
    ev=ob.evaluated_get(deps);me=ev.to_mesh();tris+=sum(len(p.vertices)-2 for p in me.polygons)
    neutral[ob.name]=[(i,ev.matrix_world@me.vertices[i].co) for i in range(0,len(me.vertices),max(1,len(me.vertices)//24))];ev.to_mesh_clear()
checks=[]
for name,angles in [('head_turn',{'j_head':(0,0,30)}),('left_arm',{'j_shoulder_le':(20,0,15),'j_elbow_le':(45,10,0),'j_wrist_le':(15,0,0),'j_mid_le_2':(25,0,0)}),('right_arm',{'j_shoulder_ri':(15,0,20),'j_elbow_ri':(40,10,0)}),('knees',{'j_hip_le':(20,0,0),'j_knee_le':(45,0,0),'j_knee_ri':(35,0,0)})]:
    for pb in rig.pose.bones:pb.rotation_euler=(0,0,0)
    for bn,deg in angles.items():rig.pose.bones[bn].rotation_euler=[math.radians(d) for d in deg]
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();worst=0
    for ob in parts:
        bn=ob['attachment_bone'];xf=rig.matrix_world@rig.pose.bones[bn].matrix@rig.data.bones[bn].matrix_local.inverted()@rig.matrix_world.inverted()
        ev=ob.evaluated_get(deps);me=ev.to_mesh()
        for i,co in neutral[ob.name]:
            error=(ev.matrix_world@me.vertices[i].co-xf@co).length
            if error>worst:worst=error;worst_object=ob.name
        ev.to_mesh_clear()
    assert worst<.003,(name,worst,worst_object);checks.append({'pose':name,'maximum_attachment_error':worst})
for pb in rig.pose.bones:pb.rotation_euler=(0,0,0)
bpy.context.view_layer.update()
# Keep the exact concept available beside the live modeling viewport.
win=bpy.context.window;screen=win.screen
ref=bpy.data.images.get('CyberZombie'+str(REFERENCE)+'.png')
editor=next((a for a in screen.areas if a.type=='IMAGE_EDITOR'),None)
if editor is None:
    area=max((a for a in screen.areas if a.type=='VIEW_3D'),key=lambda a:a.width*a.height)
    with bpy.context.temp_override(window=win,area=area):bpy.ops.screen.area_split(direction='VERTICAL',factor=.7)
    editor=max((a for a in screen.areas if a.type=='VIEW_3D'),key=lambda a:a.x);editor.type='IMAGE_EDITOR'
editor.spaces.active.image=ref
region=next(r for r in editor.regions if r.type=='WINDOW')
with bpy.context.temp_override(window=win,area=editor,region=region):bpy.ops.image.view_all(fit_view=True)
camera((30,-126,62),(0,-.5,37),86)
save(scene['cyber_authoring_stage'])
report={'reference':REFERENCE,'assignment':'armored sprinter only' if REFERENCE==3 else 'regular zombies only','authoring_transport':scene['authoring_transport'],
 'equipment_objects':len(parts),'evaluated_equipment_triangles':tris,'attachment_bones':dict(collections.Counter(o['attachment_bone'] for o in parts)),
 'stock_geometry_and_weights_unchanged':True,'donor_signatures':json.loads(scene['donor_signatures']),'pose_checks':checks,
 'master_sha256':hashlib.sha256((OUT/('reference_'+WORD+'.blend')).read_bytes()).hexdigest(),'magenta_emission_strength':magenta.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value,
 'native_exported':False,'native_playtested':False,'limitations':['Equipment reconstructed from reference images and adapted to original donor proportions.','Pose checks verify attachment motion, not full animation collision clearance.']}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('STUDY_VALIDATED',json.dumps(report))
