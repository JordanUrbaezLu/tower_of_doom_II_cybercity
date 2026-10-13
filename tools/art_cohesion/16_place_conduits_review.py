"""MCP view of actual powered surface-detail transforms, including wall normals."""
import bpy,pathlib,json,sys,math
from mathutils import Matrix,Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'art/cybercity_materials/color_restoration'
sys.path.insert(0,str(ROOT/'tools/art_cohesion'));from native_preview import fullspec
bpy.ops.wm.open_mainfile(filepath=str(OUT/'crown_restored.blend'))
scene=next(s for s in bpy.data.scenes if s.name.startswith('Actual crown'));bpy.context.window_manager.windows[0].scene=scene
with bpy.data.libraries.load(str(OUT/'power_conduits.blend'),link=False) as (src,dst):dst.objects=src.objects
sources=[o for o in dst.objects if o and o.type=='MESH' and o.get('conduit_state')=='off'];assert len(sources)==22
native={k:fullspec(ROOT/'source_data/tod_power_conduits.gdt','mtl_tod_conduit_'+k,ROOT/'model_export/tod_surface/_images') for k in ['shell','steel','rubber','wire_on']}
origin=Vector((0,8608,19392));rows=json.loads((OUT/'conduit_mounts.json').read_text())['rows']
for i,row in enumerate(rows):
    pitch,yaw,roll=map(math.radians,row['angles'])
    t=Matrix.Translation(Vector(row['org'])-origin)@Matrix.Rotation(yaw,4,'Z')@Matrix.Rotation(pitch,4,'Y')@Matrix.Rotation(roll,4,'X')@Matrix.Diagonal(Vector((*row.get('scale',[1,1,1]),1)))@Matrix.Translation(Vector((0,15,0)))
    for src in sources:
        ob=src.copy();ob.data=src.data.copy();scene.collection.objects.link(ob);ob.name=f'Power conduit {i} | '+src.name;ob.matrix_world=t@src.matrix_world
        for j,mat in enumerate(ob.data.materials):
            kind=mat.name.removeprefix('mtl_tod_conduit_').split('.')[0]
            ob.data.materials[j]=native['wire_on' if kind=='wire_off' else kind]
scene.camera.location=Vector((-470,8390,19494))-origin;target=Vector((-705,8144,19460))-origin
scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.type='PERSP';scene.camera.data.lens=25
scene.render.resolution_x=1440;scene.render.resolution_y=1000;scene.render.filepath=str(OUT/'conduit_placement.png')
scene['preview_limit']='Actual emitted crown solids, generated conduit mounts and native material approximation; neutral Blender lighting; native game unverified'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'powered_crown_review.blend'))
print('CONDUIT_PLACEMENT_REVIEW:',len(rows),'runtime transforms; 22 native source parts per fixture; no map geometry or source model changes')
