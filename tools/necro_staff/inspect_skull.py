"""MCP: inspect the native skull donor before choosing its reusable anatomy."""
import bpy, sys, pathlib, json
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import asset,native_path,xmodel
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1000;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Neutral');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.09,.09,1)
scene.view_settings.view_transform='AgX'
path=native_path('model_export',asset('xmodel','rune_prison_death_skull')['filename'])
model=xmodel.Model();model.LoadFile_Bin(str(path),split_meshes=True)
material=bpy.data.materials.new('Original BO3 skull');material.use_nodes=True
n=material.node_tree.nodes;l=material.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.7
for suffix,slot in [('c','Base Color'),('n','Normal')]:
    im=bpy.data.images.load(str(path.parent/'_images'/f'i_mtl_p7_skulls_bones_set_{suffix}.png'))
    tex=n.new('ShaderNodeTexImage');tex.image=im
    if suffix=='n':
        im.colorspace_settings.name='Non-Color'
        nm=n.new('ShaderNodeNormalMap');l.new(tex.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs[0],bs.inputs[slot])
    else:l.new(tex.outputs['Color'],bs.inputs[slot])
points=[]
for mesh in model.meshes:
    vertices=[v.offset for v in mesh.verts];points+=vertices
    faces=[tuple(i.vertex for i in reversed(f.indices)) for f in mesh.faces]
    data=bpy.data.meshes.new(mesh.name);data.from_pydata(vertices,[],faces);data.materials.append(material)
    uv=data.uv_layers.new()
    for poly,face in zip(data.polygons,mesh.faces):
        poly.use_smooth=True
        for li,ix in zip(poly.loop_indices,reversed(face.indices)):
            u=ix.uvs[0] if hasattr(ix,'uvs') else ix.uv
            uv.data[li].uv=(u[0],1-u[1])
    obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj)
low=Vector(tuple(min(v[i] for v in points) for i in range(3)));high=Vector(tuple(max(v[i] for v in points) for i in range(3)))
center=(low+high)/2;size=max(high-low)
camdata=bpy.data.cameras.new('Review');cam=bpy.data.objects.new('Review',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=size*1.35
for pos,power in [((1,-1,1.5),1100),((-1,1,1),700)]:
    d=bpy.data.lights.new('Softbox','AREA');d.energy=power*size**2/10;d.shape='DISK';d.size=size*1.3
    o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=center+Vector(pos)*size;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
out=ROOT/'art/necro_staff'
for name,loc in [('skull_front',(1,0,.2)),('skull_side',(0,-1,.2)),('skull_threequarter',(1,-1,.25))]:
    cam.location=center+Vector(loc)*size*3;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'skull_donor.blend'))
print(json.dumps({'bounds':[list(low),list(high)],'triangles':sum(len(s.faces) for s in model.meshes)}))
