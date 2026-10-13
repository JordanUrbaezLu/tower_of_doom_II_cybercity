"""Blender MCP: recessed wire channels with explicit native off/on twins."""
import bpy,math,json,pathlib,sys,ast,hashlib,re
import numpy as np
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
OUT=ROOT/'art/cybercity_materials/color_restoration';OUT.mkdir(exist_ok=True)
EXP=ROOT/'model_export/tod_surface';TEX=EXP/'_images'
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
scene=bpy.context.scene;scene.name='Recessed power conduit - off and on'
blocks=[];textures={};mats={};parts=[]
# Reuse the already exported, verified mesh/image helpers, without executing
# the alarm authoring module or touching any alarm art.
src=(ROOT/'tools/crown_alarm/01_author.py').read_text()
tree=ast.parse(src)
helpers=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['sha','block','texture','material','finish','box','cylinder']],type_ignores=[])
code=ast.unparse(helpers).replace('i_tod_alarm_','i_tod_conduit_').replace('mtl_tod_alarm_','mtl_tod_conduit_').replace('model_export/tod_crown_alarm/','model_export/tod_surface/').replace('alarm_group','conduit_group')
exec(compile(code,'conduit_mesh_helpers','exec'))
material('shell',(.026,.035,.052),.58,1)
material('steel',(.12,.16,.20),.45,1)
material('rubber',(.012,.017,.022),.8)
material('wire_off',(.012,.04,.055),.42)
material('wire_on',(.012,.40,.70),.42,0,1,8)
box('Recess shadow carrier',(0,0,.32),(96,18,.64),'rubber',bevel=.20)
for y in [-8.2,8.2]:box('Armored channel lip',(0,y,1.25),(96,1.6,1.9),'shell',bevel=.22)
for x in [-46,46]:
    box('Connector block',(x,0,1.1),(4,14,1.7),'shell',bevel=.22)
    for y in [-5.4,5.4]:cylinder('Captive socket',.85,.4,2,'steel',xy=(x,y),verts=12,bevel=.08)
def cable(name,points,radius,mat):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=radius;curve.bevel_resolution=1;curve.use_fill_caps=True
    spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
    for p,co in zip(spline.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(name,curve);scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target='MESH');finish(bpy.context.object,name,mat,'housing')
for side in [-1,1]:
    route=[(-43,side*4,1.0),(-23,side*4,1.0),(-17,side*2.6,1.0),(17,side*2.6,1.0),(23,side*4,1.0),(43,side*4,1.0)]
    cable('Insulated power cable',route,.62,'rubber')
    cable('Fine cyan conductor',[(x,y,z+.53) for x,y,z in route],.22,'wire_off')
for x in [-32,0,32]:
    box('Protective retaining bridge',(x,0,2.1),(1.7,15.8,.5),'steel',bevel=.14)
    for y in [-7.7,7.7]:cylinder('Bridge socket',.65,.23,2.42,'steel',xy=(x,y),verts=8,bevel=.06)
bpy.context.view_layer.update()
records=[]
for state in ['off','on']:
    asset='tod_power_conduit_'+state
    for lod in range(3):
        model=xmodel.Model(asset);bone=xmodel.Bone('tag_origin');bone.offset=(0,0,0);bone.matrix=[(1,0,0),(0,1,0),(0,0,1)];model.bones=[bone]
        ids={};pts=[]
        for source in parts:
            if lod and 'socket' in source.name.lower():continue
            ob=source.copy();ob.data=source.data.copy();scene.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob
            if lod:
                d=ob.modifiers.new('Distance simplification','DECIMATE');d.ratio=.55 if lod==1 else .3;bpy.ops.object.modifier_apply(modifier=d.name)
            me=ob.data;me.calc_loop_triangles();me.update();nm=ob.matrix_world.to_3x3().inverted().transposed()
            name=me.materials[0].name
            if state=='on' and name.endswith('wire_off'):name='mtl_tod_conduit_wire_on'
            if name not in ids:ids[name]=len(model.materials);model.materials.append(xmodel.Material(name,'Phong',{}))
            mesh=xmodel.Mesh(source.name);mesh.verts=[xmodel.Vertex(tuple(ob.matrix_world@v.co),[(0,1.)]) for v in me.vertices];pts.extend(v.offset for v in mesh.verts)
            uv=me.uv_layers.active.data
            for tri in me.loop_triangles:
                p=[Vector(mesh.verts[v].offset) for v in tri.vertices];longest=max((p[1]-p[0]).length,(p[2]-p[0]).length,(p[2]-p[1]).length)
                if longest<.001 or (p[1]-p[0]).cross(p[2]-p[0]).length/longest**2<.0006:continue
                f=xmodel.Face(len(model.meshes),ids[name]);f.indices=[]
                for corner in [0,2,1]:
                    li=tri.loops[corner];u=uv[li].uv;normal=(nm@me.corner_normals[li].vector).normalized()
                    f.indices.append(xmodel.FaceVertex(tri.vertices[corner],tuple(normal),(1,1,1,1),(u.x,1-u.y)))
                mesh.faces.append(f)
            model.meshes.append(mesh);bpy.data.objects.remove(ob,do_unlink=True)
        path=EXP/(asset+'_lod'+str(lod)+'.xmodel_bin');model.WriteFile_Bin(str(path),version=7)
        records.append(dict(asset=asset,lod=lod,file=path.relative_to(ROOT).as_posix(),sha256=sha(path),triangles=sum(len(m.faces) for m in model.meshes),bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]))
    block(asset,'xmodel',dict(filename='tod_surface/'+asset+'_lod0.xmodel_bin',mediumLod='tod_surface/'+asset+'_lod1.xmodel_bin',lowLod='tod_surface/'+asset+'_lod2.xmodel_bin',mediumLodDist=450,lowLodDist=900,type='rigid',scale=1,CollisionMap='',BulletCollisionLOD='None',physicsPreset='',cullOutDiameter=0,materials=''))
(ROOT/'source_data/tod_power_conduits.gdt').write_text('{\n'+''.join(blocks)+'}\n')
# Real model parts, side-by-side under the same neutral lighting.
for o in parts:o['conduit_state']='off';o.location.y-=15
for src in parts:
    ob=src.copy();ob.data=src.data.copy();scene.collection.objects.link(ob);ob.location.y+=30;ob['conduit_state']='on'
    if ob.data.materials[0].name.endswith('wire_off'):ob.data.materials[0]=mats['wire_on']
world=bpy.data.worlds.new('Neutral conduit review');world.use_nodes=True;scene.world=world;world.node_tree.nodes['Background'].inputs[1].default_value=.3
for name,loc,power,size in [('Broad key',(20,-35,100),85000,100),('Soft fill',(-60,45,60),40000,80)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size;ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,0))-ob.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('Conduit review camera',bpy.data.cameras.new('Conduit review camera'));scene.collection.objects.link(cam);scene.camera=cam
cam.location=(78,-88,130);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=128
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=1440;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
scene.render.filepath=str(OUT/'conduits_off_on.png')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'power_conduits.blend'))
(OUT/'conduit_manifest.json').write_text(json.dumps(dict(models=records,textures=textures,parts=len(parts),bounds='96 x 18 x 2.6 native units',off_emission=0,on_emission=8,native_visual_approved=False),indent=2))
print('CONDUITS_AUTHORED',json.dumps({'parts':len(parts),'models':records,'textures':len(textures)}))
