"""MCP art review: stock axe silhouette, physical cable phases, editable preview."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/archer_assets';OUT=ROOT/'model_export/tod_archer/_images'
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
bpy.ops.wm.open_mainfile(filepath=str(ART/'archer_equipment.blend'))
scene=bpy.context.scene
for ob in bpy.data.objects:
    if ob.type in ('MESH','ARMATURE'):ob.hide_render=True
source=ROOT/'source_library/archer_equipment/t7_axe_reference/wpn_t7_loot_axe_world_LOD0.XMODEL_BIN'
m=xmodel.Model();m.LoadFile_Bin(str(source));verts=[];faces=[]
for mesh in m.meshes:
    start=len(verts);verts.extend([v.offset for v in mesh.verts])
    faces.extend([(start+f.indices[0].vertex,start+f.indices[2].vertex,start+f.indices[1].vertex) for f in mesh.faces])
data=bpy.data.meshes.new('Stock axe reference geometry');data.from_pydata(verts,[],faces);data.update()
axe=bpy.data.objects.new('STOCK AXE | original MOTD model still missing',data);scene.collection.objects.link(axe)
axe['source']=source.relative_to(ROOT).as_posix();axe['original_retriever']=False
white=bpy.data.materials.get('HUD white silhouette');scene.view_layers[0].material_override=white
center=sum((Vector(v) for v in verts),Vector())/len(verts)
camera=scene.camera;camera.location=center+Vector((8,-80,10));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=45
scene.render.resolution_x=512;scene.render.resolution_y=512
scene.render.filepath=str(OUT/'i_tod_archer_axe_hud.png');bpy.ops.render.render(write_still=True)
scene.view_layers[0].material_override=None;axe.hide_render=True

# A dedicated native-scale presentation scene shares the exact imported hook.
preview=bpy.data.scenes.new('Cable phases | visual reference, not engine validation')
bpy.context.window_manager.windows[0].scene=preview;preview.world=scene.world.copy()
preview.world.node_tree.nodes['Background'].inputs[0].default_value=(.065,.075,.09,1)
preview.world.node_tree.nodes['Background'].inputs[1].default_value=.8
src=next(o for o in bpy.data.collections['SOURCE | hook'].objects if o.type=='MESH')
hook=src.copy();hook.data=src.data.copy();hook.parent=None;hook.modifiers.clear();preview.collection.objects.link(hook)
hook.hide_render=False;hook.location=(164.5,0,72);hook.rotation_euler=(0,0,0)
rope_mat=bpy.data.materials.new('Braided cable preview');rope_mat.use_nodes=True
n=rope_mat.node_tree.nodes;l=rope_mat.node_tree.links;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=.65
tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/'i_tod_archer_cable.png'));l.new(tex.outputs['Color'],p.inputs['Base Color'])
curve=bpy.data.curves.new('Taut tether','CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=.15;curve.bevel_resolution=2
line=curve.splines.new('POLY');line.points.add(1);line.points[0].co=(0,-8,48,1);line.points[1].co=(164.5,0,72,1)
rope=bpy.data.objects.new('Native cable | .3 unit diameter',curve);preview.collection.objects.link(rope);rope.data.materials.append(rope_mat)
for frame,start in [(1,0),(5,0),(40,95),(48,115),(56,115)]:
    line.points[0].co=(start,-8,48,1);line.points[0].keyframe_insert(data_path='co',frame=frame)
for ob in (hook,rope):
    for frame,hidden in [(1,True),(4,True),(5,False),(48,False),(49,True),(56,True)]:ob.hide_render=hidden;ob.keyframe_insert(data_path='hide_render',frame=frame)
wallmat=bpy.data.materials.new('Preview neutral wall');wallmat.diffuse_color=(.21,.23,.27,1)
for name,verts,faces in [('Wall',[(180,-75,0),(180,75,0),(180,75,125),(180,-75,125)],[(0,1,2,3)]),('Floor',[(-30,-75,0),(180,-75,0),(180,75,0),(-30,75,0)],[(0,1,2,3)])]:
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);ob=bpy.data.objects.new(name,mesh);preview.collection.objects.link(ob);ob.data.materials.append(wallmat)
lamp=bpy.data.lights.new('Area key','AREA');lamp.energy=700000;lamp.size=150;ob=bpy.data.objects.new('Area key',lamp);preview.collection.objects.link(ob);ob.location=(80,-60,180);ob.rotation_euler=(Vector((100,0,45))-ob.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('64 unit camera');ob=bpy.data.objects.new('64 unit camera',cam);preview.collection.objects.link(ob);ob.location=(-20,-130,64);ob.rotation_euler=(Vector((120,0,60))-ob.location).to_track_quat('-Z','Y').to_euler();cam.lens=45;preview.camera=ob
preview.render.engine='CYCLES';preview.cycles.samples=8;preview.cycles.device=scene.cycles.device;preview.render.threads_mode='FIXED';preview.render.threads=8
preview.render.resolution_x=672;preview.render.resolution_y=448;preview.render.resolution_percentage=100;preview.render.fps=24;preview.frame_start=1;preview.frame_end=56
preview.render.image_settings.file_format='PNG';preview.render.image_settings.color_mode='RGBA'
preview['note']='Apex hook and physical cable at BO3 scale. No launcher/hand animation. User native review pending.'
preview.frame_set(24)
preview.render.filepath=str(ART/'preview/cable_native_scale.png');bpy.ops.render.render(write_still=True,scene=preview.name)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'archer_equipment.blend'))
print('ARCHER_PRESENTATION_SAVED stock_axe_icon=1 cable_frames=56 native_tested=0')
