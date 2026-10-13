"""MCP authoring: mip-safe portrait of the actual exported Dealer, not a new face.

Load only two reduced native meshes and their maps. No shop/sky master changes.
The result is photographed screen content, not a model albedo bake.
"""
from pathlib import Path
import bpy,json,sys,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/dealer_presence';ART.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path(__file__).parent));from process_guard import check
check()
KIT=ROOT/'art/partner_shop/engine_kit';IMG=ROOT/'model_export/tod_shop/_images';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(ROOT/'tools'))
from art_cohesion.native_preview import fullspec
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
sc=bpy.context.scene
sources=[KIT/'vendor_lod0.json',KIT/'mask_lod0.json',KIT/'source_manifest.json',ROOT/'source_data/tod_shop.gdt',ROOT/'tools/art_cohesion/native_preview.py']
triangle_count=0
for group,material in [('vendor','mtl_tod_shop_vendor'),('mask','mtl_tod_shop_glow')]:
    d=json.loads((KIT/(group+'_lod0.json')).read_text());me=bpy.data.meshes.new('Canonical '+group)
    triangle_count+=len(d['faces']);me.from_pydata(d['verts'],[],[[f[i]['v'] for i in (0,2,1)] for f in d['faces']]);me.update();uv=me.uv_layers.new();normals=[]
    for poly,f in zip(me.polygons,d['faces']):
        poly.use_smooth=True
        for li,i in zip(poly.loop_indices,(0,2,1)):uv.data[li].uv=(f[i]['uv'][0],1-f[i]['uv'][1]);normals.append(f[i]['n'])
    me.normals_split_custom_set(normals);me.materials.append(fullspec(ROOT/'source_data/tod_shop.gdt',material,IMG))
    ob=bpy.data.objects.new('Canonical '+group,me);sc.collection.objects.link(ob)
sources.extend(sorted(IMG.glob('i_tod_shop_vendor_*.png')));sources.extend(sorted(IMG.glob('i_tod_shop_glow_*.png')))
world=bpy.data.worlds.new('Oxblood surveillance darkness');world.use_nodes=True;sc.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.025,.012,.014,1);world.node_tree.nodes['Background'].inputs[1].default_value=.3
for name,org,power,color,size in [('soft face',(-22,-35,82),19000,(.85,.9,1),24),('red rim',(25,4,75),13000,(1,.02,.006),16),('low fill',(5,-30,45),1800,(.7,.16,.12),18)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
    ob=bpy.data.objects.new(name,d);sc.collection.objects.link(ob);ob.location=org;ob.rotation_euler=(Vector((0,-4,62))-ob.location).to_track_quat('-Z','Y').to_euler()
camd=bpy.data.cameras.new('Canonical Dealer head and shoulders');cam=bpy.data.objects.new(camd.name,camd);sc.collection.objects.link(cam);sc.camera=cam
camd.type='ORTHO';camd.ortho_scale=41;cam.location=(0,-100,65);cam.rotation_euler=(Vector((0,-3,59))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    sc.cycles.device='GPU'
except Exception:pass
sc.render.resolution_x=1024;sc.render.resolution_y=1024;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.film_transparent=False
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=0
sc.render.filepath=str(ART/'dealer_surveillance_1024.png');check();bpy.ops.render.render(write_still=True)
for im in bpy.data.images:
    if im.source=='FILE':
        try:im.pack()
        except RuntimeError:pass
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'dealer_surveillance.blend'))
receipt={'schema':1,'source':'Actual native vendor and mask geometry + current native maps','sources':{p.relative_to(ROOT).as_posix():sha(p) for p in sources},
 'author_script_sha256':sha(Path(__file__)),'image':'art/dealer_presence/dealer_surveillance_1024.png','image_sha256':sha(Path(sc.render.filepath)),
 'dimensions':[1024,1024],'geometry_triangles':triangle_count,'master_shop_modified':False,'native_playtested':False}
(ART/'portrait.json').write_text(json.dumps(receipt,indent=2)+'\n');print('DEALER_PORTRAIT_AUTHORED_1024',flush=True)
