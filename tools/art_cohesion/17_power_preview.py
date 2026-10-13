"""Blender MCP: actual tower geometry and native wire transforms, matched states."""
import bpy,json,pathlib,sys,math
from mathutils import Vector,Matrix
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'art/cybercity_materials/color_restoration'
sys.path.insert(0,str(ROOT/'tools/art_cohesion'));from native_preview import fullspec
sys.path.insert(0,str(pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
# Reuse the actual lower-tower review geometry; its materials come from native GDT.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'tmp/tower_design/material_review.blend'))
scene=bpy.context.scene;scale=.0254
layout=json.loads((OUT/'conduit_mounts.json').read_text())
source=xmodel.Model();source.LoadFile_Bin(str(ROOT/'model_export/tod_surface/tod_power_conduit_off_lod1.xmodel_bin'),split_meshes=True)
native={m.name:fullspec(ROOT/'source_data/tod_power_conduits.gdt',m.name,ROOT/'model_export/tod_surface/_images') for m in source.materials}
lit=fullspec(ROOT/'source_data/tod_power_conduits.gdt','mtl_tod_conduit_wire_on',ROOT/'model_export/tod_surface/_images')
meshes=[]
for src in source.meshes:
    mesh=bpy.data.meshes.new(src.name);verts=[];faces=[];uvs=[]
    for face in src.faces:
        # Native winding is clockwise, Blender is counter-clockwise.
        faceverts=[]
        for fv in reversed(face.indices):
            faceverts.append(len(verts));verts.append(source.meshes[face.mesh_id].verts[fv.vertex].offset);uvs.append((fv.uv[0],1-fv.uv[1]))
        faces.append(faceverts)
    mesh.from_pydata(verts,[],faces);mesh.materials.append(native[source.materials[src.faces[0].material_id].name]);mesh.update();uv=mesh.uv_layers.new()
    for p in mesh.polygons:
        for li in p.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
    meshes.append(mesh)
wires=[];count=0
for row in layout['rows']:
    if row['org'][2]>1536 or abs(row['org'][0])>1500 or abs(row['org'][1])>1500:continue
    count+=1;p,y,r=map(math.radians,row['angles'])
    transform=Matrix.Translation(Vector(row['org'])*scale)@Matrix.Rotation(y,4,'Z')@Matrix.Rotation(p,4,'Y')@Matrix.Rotation(r,4,'X')@Matrix.Diagonal(Vector((*[v*scale for v in row['scale']],1)))
    for mesh in meshes:
        ob=bpy.data.objects.new(row['label']+' | '+mesh.name,mesh);scene.collection.objects.link(ob);ob.matrix_world=transform
        if mesh.materials[0]==native['mtl_tod_conduit_wire_off']:wires.append(ob)
# Match illumination and camera; this demonstrates geometry/material switching,
# not the native baked-lighting or exposure system.
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.25
for ob in scene.objects:
    if ob.type=='LIGHT':ob.data.energy*=.2
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.cycles.samples=32;scene.render.resolution_x=1280;scene.render.resolution_y=960
cam=scene.camera
views=[('tower',(1150,-1550,1200),(0,0,600),1900),('landing',(540,570,320),(336,335,205),0)]
assert len(wires)==2*count,(len(wires),count)
for view,pos,target,ortho in views:
    cam.location=Vector(pos)*scale;cam.rotation_euler=(Vector(target)*scale-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO' if ortho else 'PERSP';cam.data.ortho_scale=(ortho or 1900)*scale;cam.data.lens=27
    for state in ('off','on'):
        for ob in wires:
            ob.material_slots[0].link='OBJECT';ob.material_slots[0].material=lit if state=='on' else native['mtl_tod_conduit_wire_off']
        scene.render.filepath=str(OUT/f'tower_power_{view}_{state}.png');bpy.ops.render.render(write_still=True)
scene['preview_limit']='Actual tower hulls and native wire meshes; same neutral illumination in both states; BO3 lighting and visibility unverified.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'tower_power_review.blend'))
print('TOWER_POWER_PREVIEW',count,'actual lower-tower inlays;',scene['preview_limit'])
