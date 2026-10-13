"""MCP-authored matched previews from emitted map faces and actual GDT fields.

No shop or sky master is opened. Native lights/probes are approximations; the
wall coordinates, player cameras, art, native maps, UVs and gloss ranges are real.
"""
from pathlib import Path
import bpy,json,sys,math,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/dealer_presence'
sys.path.insert(0,str(Path(__file__).parent));from process_guard import check
check()
sys.path.insert(0,str(ROOT/'tools'))
from art_cohesion.native_preview import fullspec,fields,DESCRIPTION
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
for material in list(bpy.data.materials):bpy.data.materials.remove(material)
for image in list(bpy.data.images):
    if image.type!='RENDER_RESULT':bpy.data.images.remove(image)
sc=bpy.context.scene
kit=json.loads((ROOT/'tools/art_cohesion/crown_materials.json').read_text())['materials']
data=json.loads((ART/'geometry.json').read_text());contexts=json.loads((ART/'context.json').read_text())
mats={}
def metal(name):
    if name not in mats:mats[name]=fullspec(ROOT/'source_data/tod_surface.gdt',name,ROOT/'model_export/tod_surface/_images')
    return mats[name]
install=json.loads((ART/'install.json').read_text())
GDT=ROOT/install['gdt'];IMAGE=ROOT/install['installed_image']
if not GDT.exists():GDT=ROOT/'tmp/dealer_presence/staging/final_candidate/tod_dealer_presence.gdt'
if not IMAGE.exists():IMAGE=ROOT/'tmp/dealer_presence/staging/final_candidate/i_tod_dealer_surveillance.png'
assert hashlib.sha256(GDT.read_bytes()).hexdigest()==install['gdt_sha256'],'Staged material differs from native candidate'
assert hashlib.sha256(IMAGE.read_bytes()).hexdigest()==install['installed_image_sha256'],'Staged image differs from native candidate'
f=fields(GDT,'mtl_tod_dealer_surveillance')
sc['native_material_scaleRGB']=float(f['scaleRGB']);sc['source_image_unmodified']=True
photo=bpy.data.materials.new('Native static surveillance screen');photo.use_nodes=True
n,l=photo.node_tree.nodes,photo.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled')
tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(IMAGE));tex.interpolation='Linear'
tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
c=float(f['colorTint'].split()[0]);c=((c+.055)/1.055)**2.4;tint.inputs[2].default_value=(c,c,c,1)
l.new(tex.outputs['Color'],tint.inputs[1]);l.new(tint.outputs[0],p.inputs['Base Color']);l.new(tex.outputs['Color'],p.inputs['Emission Color'])
p.inputs['Emission Strength'].default_value=float(f['scaleRGB']);p.inputs['Roughness'].default_value=.58;p.inputs['Specular IOR Level'].default_value=float(f['specAmount'])
l.new(p.outputs[0],out.inputs[0]);mats['mtl_tod_dealer_surveillance']=photo
scale=.0254
def mesh(label,verts,faces,materials,uvs):
    me=bpy.data.meshes.new(label);me.from_pydata([tuple(v*scale for v in q) for q in verts],[],faces);me.update()
    slots=[]
    for mat in materials:
        if mat not in slots:slots.append(mat);me.materials.append(mats[mat] if mat in mats else metal(mat))
    uv=me.uv_layers.new()
    for poly,mat,coord in zip(me.polygons,materials,uvs):
        poly.material_index=slots.index(mat)
        for li,t in zip(poly.loop_indices,coord):uv.data[li].uv=t
    ob=bpy.data.objects.new(label,me);sc.collection.objects.link(ob);return ob
world=bpy.data.worlds.new('Bounded neutral review environment');world.use_nodes=True;sc.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.11,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
sun=bpy.data.lights.new('Preview only soft fill','SUN');sun.energy=1.1;sun.angle=.8
so=bpy.data.objects.new(sun.name,sun);sc.collection.objects.link(so);so.rotation_euler=(.5,-.4,-.7)
keydata=bpy.data.lights.new('Preview only neutral material inspection softbox','AREA');keydata.energy=700;keydata.shape='DISK';keydata.size=3
key=bpy.data.objects.new(keydata.name,keydata);sc.collection.objects.link(key)
camd=bpy.data.cameras.new('Player eye, 60 native units above local floor');cam=bpy.data.objects.new(camd.name,camd);sc.collection.objects.link(cam);sc.camera=cam
camd.type='PERSP';camd.lens=25;camd.clip_start=.01;camd.clip_end=1000
sc.render.engine='BLENDER_EEVEE_NEXT';sc.render.resolution_x=1280;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=0
sc['preview_limit']=DESCRIPTION+'; actual emitted local walls and native panel geometry; neutral review lighting, no stock props or BO3 probes.'
for context in contexts:
    objects=[]
    for row in context['solids']:
        verts=[];faces=[];names=[];uvs=[]
        for face in row['faces']:
            if len(face['vertices'])<3:continue
            start=len(verts);verts.extend(face['vertices']);faces.append(list(range(start,len(verts))));names.append(face['mat'])
            size=kit[face['mat'].removeprefix('tod_cc_')]['size'];axis=max(range(3),key=lambda i:abs(face['n'][i]))
            uvs.append([((v[1] if axis==0 else v[0])/size,(v[1] if axis==2 else v[2])/size) for v in face['vertices']])
        if faces:objects.append(mesh(row['label'],verts,faces,names,uvs))
    for q in data['quads']:
        if q['id']==context['id']:objects.append(mesh(q['part'],q['verts'],[[0,1,2,3]],[q['material']],[q['uv']]))
    target=Vector(context['centre'])*scale;cam.location=Vector(context['camera'])*scale;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    key.location=cam.location+Vector((0,0,1.2));key.rotation_euler=(target-key.location).to_track_quat('-Z','Y').to_euler()
    for state in ['before','after']:
        for ob in objects:
            if ob.name.split('.')[0] in {q['part'] for q in data['quads']}:ob.hide_render=state=='before'
        sc.render.filepath=str(ART/(context['id']+'_'+state+'.png'));check();bpy.ops.render.render(write_still=True)
    if context['id']=='floor20_service':
        for ob in objects:ob.hide_render=False
        cam.location=target+Vector(context['normal'])*scale*185;cam.location.z+=scale*8;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camd.lens=45
        key.location=cam.location+Vector((-1,0,1.2));key.rotation_euler=(target-key.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=str(ART/'native_material_detail.png');check();bpy.ops.render.render(write_still=True);camd.lens=25
        bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'dealer_panel_review.blend'))
    for ob in objects:bpy.data.objects.remove(ob,do_unlink=True)
sc['native_material_scaleRGB']=float(f['scaleRGB']);sc['source_image_unmodified']=True
receipt={'schema':1,'engine':'Blender EEVEE','preview_limit':sc['preview_limit'],'source_image_sha256':hashlib.sha256(IMAGE.read_bytes()).hexdigest(),'geometry_sha256':hashlib.sha256((ART/'geometry.json').read_bytes()).hexdigest(),'gdt_sha256':hashlib.sha256(GDT.read_bytes()).hexdigest(),'preview_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'layout_script_sha256':hashlib.sha256((ROOT/'tools/dealer_presence/layout.js').read_bytes()).hexdigest(),'native_playtested':False,'review_image_path':IMAGE.relative_to(ROOT).as_posix(),'review_gdt_path':GDT.relative_to(ROOT).as_posix(),'review_lighting':'Neutral inspection softbox is preview-only and shared by each before/after pair; native screen emission remains .65.'}
receipt['images']={name:hashlib.sha256((ART/name).read_bytes()).hexdigest() for name in [context['id']+'_'+state+'.png' for context in contexts for state in ('before','after')]+['native_material_detail.png']}
receipt['context_sha256']=hashlib.sha256((ART/'context.json').read_bytes()).hexdigest()
review_inputs={ROOT/'tools/art_cohesion/native_preview.py',ROOT/'source_data/tod_surface.gdt',ROOT/'tools/art_cohesion/crown_materials.json'}
review_inputs.update(Path(bpy.path.abspath(im.filepath)) for im in bpy.data.images if im.filepath and Path(bpy.path.abspath(im.filepath)).is_file() and Path(bpy.path.abspath(im.filepath))!=IMAGE)
receipt['native_preview_sources']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(review_inputs)}
(ART/'preview.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('DEALER_PRESENCE_PREVIEW_COMPLETE',flush=True)
