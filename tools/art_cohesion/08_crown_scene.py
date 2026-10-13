"""Bring the COMPLETE generated crown geometry into Blender MCP for art review."""
import bpy,json,pathlib,sys,math,re,hashlib
from mathutils import Vector,Matrix
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/cybercity_materials'
sys.path.insert(0,str(ROOT/'tools'));from art_cohesion.native_preview import fullspec,DESCRIPTION
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
scene=bpy.context.scene;origin=Vector((0,8608,19392))
kit=json.loads((ROOT/'tools/art_cohesion/crown_materials.json').read_text())['materials']
mats={name:fullspec(ROOT/'source_data/tod_surface.gdt','tod_cc_'+name,ROOT/'model_export/tod_surface/_images') for name in kit}
inventory=json.loads((ART/'crown_inventory.json').read_text())
col=bpy.data.collections.new('Complete native crown architecture');scene.collection.children.link(col)
for r in inventory['rows']:
    verts=[];faces=[];uvs=[];matids=[];slots=[]
    for face in r['faces']:
        role=face['mat'].removeprefix('tod_cc_');assert role in mats
        if role not in slots:slots.append(role)
        axis=max(range(3),key=lambda i:abs(face['n'][i]));size=kit[role]['size']
        indices=[]
        for p in face['vertices']:
            indices.append(len(verts));verts.append(tuple(Vector(p)-origin))
            u=p[1] if axis==0 else p[0];v=p[1] if axis==2 else p[2]
            uvs.append((u/size,v/size))
        faces.append(indices);matids.append(slots.index(role))
    mesh=bpy.data.meshes.new(r['label']);mesh.from_pydata(verts,[],faces);mesh.update()
    for role in slots:mesh.materials.append(mats[role])
    layer=mesh.uv_layers.new()
    for poly,mi in zip(mesh.polygons,matids):
        poly.material_index=mi
        for li in poly.loop_indices:layer.data[li].uv=uvs[mesh.loops[li].vertex_index]
    ob=bpy.data.objects.new(r['label'],mesh);col.objects.link(ob);ob['native_architecture']=True
    # Zero extra bevel/displacement: the preview proves the actual emitted shape.

# Load the actual exported hero meshes from our verified comparison scene.
with bpy.data.libraries.load(str(ART/'native_comparison.blend'),link=False) as (src,dst):dst.objects=src.objects
props=[o for o in dst.objects if o and o.type=='MESH' and o.get('review_group','').startswith(('shop_','teleporter','altar'))]
prop_mats={}
for file,folder,names in [('tod_shop.gdt','tod_shop',['mtl_tod_shop_'+x for x in ('body','vendor','glow','glow_off')]),('tod_teleporter.gdt','tod_teleporter',['mtl_tod_teleporter']),('tod_heavenly_altar.gdt','tod_heavenly_altar',['mtl_tod_altar'])]:
    for name in names:prop_mats[name]=fullspec(ROOT/'source_data'/file,name,ROOT/'model_export'/folder/'_images')
propscol=bpy.data.collections.new('Preserved native detailed props');scene.collection.children.link(propscol)
for src in props:
    tag=src['review_group'];src.hide_render=False
    for i,mat in enumerate(src.data.materials):
        native=mat.name.split(' | ')[-1].split('.')[0]
        if native in prop_mats:src.data.materials[i]=prop_mats[native]
    if tag.startswith('shop_'):
        pivot=src.location-Vector((-200,0,0))
        for index,pos in enumerate([(-644,8328,19392),(-500,6560,19392)]):
            ob=src.copy();ob.data=src.data.copy();propscol.objects.link(ob);ob.name=('Active crown shop' if index==0 else 'Off balcony shop')+' | '+tag
            ob.matrix_world=Matrix.Translation(Vector(pos)-origin)@Matrix.Rotation(math.radians(90),4,'Z')@Matrix.Translation(pivot)
            if index==1:
                if tag in ('shop_vendor','shop_mask'):ob.hide_render=True
                for i,m in enumerate(ob.data.materials):
                    if 'mtl_tod_shop_glow' in m.name:ob.data.materials[i]=prop_mats['mtl_tod_shop_glow_off']
    elif tag=='teleporter':
        ob=src.copy();propscol.objects.link(ob);ob.location=Vector((0,8608,19408))-origin
    elif tag=='altar':
        ob=src.copy();propscol.objects.link(ob);ob.matrix_world=Matrix.Translation(Vector((-664,8608,19392))-origin)@Matrix.Rotation(math.radians(90),4,'Z')

world=bpy.data.worlds.new('Crown review studio');world.use_nodes=True;scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.21,.24,.30,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65
d=bpy.data.lights.new('Review sun — not a native lighting change','SUN');d.energy=3;d.angle=.12;sun=bpy.data.objects.new(d.name,d);scene.collection.objects.link(sun);sun.rotation_euler=(math.radians(28),math.radians(-24),math.radians(-30))
for name,pos,power,size in [('Crown soft fill',(4500,4700,26000),400000000,7000),('Interior review fill',(0,8550,20300),20000000,1200)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob);ob.location=Vector(pos)-origin;ob.rotation_euler=(Vector((0,8608,19392))-Vector(pos)).to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('Crown inspection camera');cam=bpy.data.objects.new(camdata.name,camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.clip_end=100000
cam.location=Vector((7000,1100,23200))-origin;target=Vector((0,8608,21300))-origin;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=19000
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
scene['preview_limit']=DESCRIPTION+'; actual map solids and source meshes, neutral review lighting; native lighting/gameplay not reproduced'
scene['stock_props']='Stock perk machines, ammo crate, power lever and runtime FX are retained in game but omitted from this architecture review'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.clip_end=100000
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'crown_complete.blend'))
(ART/'crown_review_manifest.json').write_text(json.dumps({'map_sha256':hashlib.sha256((ROOT/'map_source/zm/zm_tod2_cybercity.map').read_bytes()).hexdigest(),'source_world_brushes':inventory['brushes'],'preview_limit':scene['preview_limit'],'stock_props':scene['stock_props']},indent=2))
print('COMPLETE_CROWN_MCP_SCENE_SAVED',inventory['brushes'],'native solids; actual hero prop placements',flush=True)
