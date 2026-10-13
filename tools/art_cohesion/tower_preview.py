"""Standalone Blender material review; deliberately not a BO3 lighting simulation."""
import bpy,json,pathlib,sys,math
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from art_cohesion.native_preview import fullspec,DESCRIPTION
broken='--broken' in sys.argv
OUT=ROOT/('docs/tower_design/broken' if broken else 'docs/tower_design');OUT.mkdir(parents=True,exist_ok=True)
kit=json.loads((ROOT/'tools/art_cohesion/crown_materials.json').read_text())['materials']
rows=json.loads((ROOT/'tmp/tower_design/review_inventory.json').read_text())
# Run in factory-startup background Blender, never overwrite an artist's session.
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
scene=bpy.context.scene;scale=.0254
used={f['mat'] for row in rows for f in row['faces']}
mats={name:fullspec(ROOT/'source_data/tod_surface.gdt',name,ROOT/'model_export/tod_surface/_images') for name in used}
for row in rows:
    verts=[];faces=[];uvs=[];ids=[];slots=[]
    for f in row['faces']:
        name=f['mat'];size=kit[name.removeprefix('tod_cc_')]['size']
        if name not in slots:slots.append(name)
        axis=max(range(3),key=lambda i:abs(f['n'][i]));indices=[]
        for p in f['vertices']:
            indices.append(len(verts));verts.append(tuple(v*scale for v in p))
            uvs.append(((p[1] if axis==0 else p[0])/size,(p[1] if axis==2 else p[2])/size))
        faces.append(indices);ids.append(slots.index(name))
    mesh=bpy.data.meshes.new(row['label']);mesh.from_pydata(verts,[],faces);mesh.update()
    for name in slots:mesh.materials.append(mats[name])
    uv=mesh.uv_layers.new()
    for p,mi in zip(mesh.polygons,ids):
        p.material_index=mi
        for li in p.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
    ob=bpy.data.objects.new(row['label'],mesh);scene.collection.objects.link(ob)
world=bpy.data.worlds.new('Neutral review environment');world.use_nodes=True;scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.3,.4,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.8
d=bpy.data.lights.new('Review sun','SUN');d.energy=3;d.angle=.25
ob=bpy.data.objects.new(d.name,d);scene.collection.objects.link(ob);ob.rotation_euler=(.4,-.6,-.7)
for pos,power,size in [((1000,-1300,1800),80000,25),((500,0,800),12000,10),((-700,800,1300),30000,18)]:
    d=bpy.data.lights.new('Review softbox','AREA');d.energy=power;d.shape='DISK';d.size=size
    ob=bpy.data.objects.new(d.name,d);scene.collection.objects.link(ob);ob.location=Vector(pos)*scale
    ob.rotation_euler=(Vector((0,0,400))*scale-ob.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Architecture review');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
scene['preview_limit']=DESCRIPTION+'; neutral studio lights; lower tower crop; stock props and native lighting omitted'
views=[('tower_materials',(1150,-1550,1200),(0,0,600),1900),('stair_materials',(700,-400,580),(340,50,140),0)]
if broken:views=[('broken_overview',(1150,-1550,1450),(0,0,850),1700),('broken_drop',(1000,-500,1320),(336,80,880),0)]
for name,pos,target,ortho in views:
    cam.location=Vector(pos)*scale;cam.rotation_euler=(Vector(target)*scale-cam.location).to_track_quat('-Z','Y').to_euler()
    d.type='ORTHO' if ortho else 'PERSP';d.ortho_scale=(ortho or 1900)*scale;d.lens=24;d.clip_end=2000
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('tmp/broken_tower/material_review.blend' if broken else 'tmp/tower_design/material_review.blend')))
print('TOWER_MATERIAL_REVIEW_DONE',len(rows),'actual solids;',scene['preview_limit'])
