"""Run through Blender MCP. Original assembly is preserved; model at game scale."""
import bpy, bmesh, sys, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'art/teleporter'
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
sources=json.loads((OUT/'original_sources.json').read_text())
for ob in list(bpy.context.scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
for col in list(bpy.data.collections):
    if col.name.startswith(('01 ORIGINAL','02 ENHANCED','03 REVIEW')):bpy.data.collections.remove(col)
scene=bpy.context.scene
original=bpy.data.collections.new('01 ORIGINAL | preserved nine-piece assembly');scene.collection.children.link(original)
design=bpy.data.collections.new('02 ENHANCED | native-size teleporter');scene.collection.children.link(design)
stage=bpy.data.collections.new('03 REVIEW | lights and camera');scene.collection.children.link(stage)
def move(ob,col):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob);return ob
def mat(name,color,metal=.7,rough=.4,emit=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    ns=m.node_tree.nodes;l=m.node_tree.links;p=ns.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
    if not emit:
        tex=ns.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=14;tex.inputs['Detail'].default_value=3
        ramp=ns.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(v*.65 for v in color),1);ramp.color_ramp.elements[1].color=(*(min(1,v*1.22) for v in color),1)
        l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
        rr=ns.new('ShaderNodeMapRange');rr.inputs['To Min'].default_value=max(.15,rough-.1);rr.inputs['To Max'].default_value=min(.85,rough+.17);l.new(tex.outputs['Fac'],rr.inputs[0]);l.new(rr.outputs[0],p.inputs['Roughness'])
        fine=ns.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=170;fine.inputs['Detail'].default_value=2
        bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.2;bump.inputs['Distance'].default_value=.025;l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return m
steel=mat('TP | graphite anodized titanium',(.105,.14,.19),.8,.36)
edge=mat('TP | brushed exposed alloy',(.29,.35,.42),.88,.29)
dark=mat('TP | recess and rubber seals',(.012,.02,.03),.25,.64)
bronze=mat('TP | warm copper contacts',(.33,.145,.065),.82,.34)
panel=mat('TP | ceramic reactor plates',(.027,.047,.077),.48,.3)
cyan=mat('TP | recessed cyan emitters',(.012,.52,.95),.25,.27,3.2)
violet=mat('TP | violet induction emitters',(.22,.015,.82),.3,.25,3.8)
white=mat('TP | core light',(.15,.7,1),.2,.24,5.5)
ink=mat('TP | service markings',(.42,.55,.63),.25,.5)
def finish(ob,name,material,bevel=0):
    ob.name=name;move(ob,design);ob.data.materials.append(material);ob['teleporter_design']=True
    if bevel:
        mod=ob.modifiers.new('Machined edge radius','BEVEL');mod.width=bevel;mod.segments=3
        mod=ob.modifiers.new('Weighted machined normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=40
    return ob
def ring(name,ri,ro,z0,z1,material,start=0,end=math.tau,steps=128,bevel=0):
    steps=max(2,int(steps*(end-start)/math.tau));verts=[]
    for i in range(steps+1):
        a=start+(end-start)*i/steps
        for r,z in ((ri,z0),(ro,z0),(ri,z1),(ro,z1)):verts.append((r*math.cos(a),r*math.sin(a),z))
    faces=[]
    for i in range(steps):
        a=4*i;b=a+4
        faces.extend([(a+2,a+3,b+3,b+2),(a,b,b+1,a+1),(a+1,b+1,b+3,a+3),(a,a+2,b+2,b)])
    faces.extend([(0,1,3,2),(steps*4,steps*4+2,steps*4+3,steps*4+1)])
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);design.objects.link(ob)
    finish(ob,name,material,bevel)
    for p in me.polygons:p.use_smooth=(p.index%4 in (2,3) and p.index<steps*4)
    return ob
def cyl(name,r,depth,z,material,xy=(0,0),vertices=64,bevel=.15):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=(*xy,z));return finish(bpy.context.object,name,material,bevel)
def box(name,loc,size,material,angle=0,bevel=.15):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.rotation_euler.z=angle;return finish(ob,name,material,bevel)
def xy(r,a):return (r*math.cos(a),r*math.sin(a))
def label(text,r,a,z,size):
    bpy.ops.object.text_add(location=(*xy(r,a),z));ob=bpy.context.object;ob.data.body=text;ob.data.size=size;ob.data.align_x='CENTER';ob.data.extrude=.005;ob.rotation_euler.z=a-math.pi/2
    bpy.ops.object.convert(target='MESH');finish(bpy.context.object,'Etched | '+text,ink)
# Import native geometry at EXACT runtime transforms. Preserve separately.
assembly=[('p7_zm_der_teleporter',a) for a in (0,90,180,270)]+[('p7_zm_der_teleporter_pad_glass',180)]+[('p7_zm_der_teleporter_pad_wires_blue',a) for a in (90,270)]+[('p7_zm_der_teleporter_pad_wires_red',a) for a in (0,180)]
for asset,yaw in assembly:
    model=xmodel.Model();model.LoadFile_Bin(sources['models'][asset]['path'],split_meshes=False);src=model.meshes[0]
    me=bpy.data.meshes.new(asset);me.from_pydata([v.offset for v in src.verts],[],[[f.indices[i].vertex for i in (0,2,1)] for f in src.faces]);me.update()
    ob=bpy.data.objects.new('Original | '+asset+' | '+str(yaw),me);original.objects.link(ob);ob.scale=(2.5,)*3;ob.location.z=-52;ob.rotation_euler.z=math.radians(yaw)
    me.materials.append(steel);ob['source_sha256']=sources['models'][asset]['sha256']
    # Retain the donor's lower casting beneath the new deck, cut at z=1.
    if asset=='p7_zm_der_teleporter':
        part=ob.copy();part.data=me.copy();design.objects.link(part);part.name='Donor lower casting | '+str(yaw);part['teleporter_design']=True
        bm=bmesh.new();bm.from_mesh(part.data)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.0001,plane_co=(0,0,21.2),plane_no=(0,0,1),clear_outer=True,clear_inner=False)
        bm.to_mesh(part.data);bm.free();part.data.update()
original.hide_render=True;original.hide_viewport=True
ring('Lower structural skirt',66,77,-1,3,steel,bevel=.5)
ring('Lower machined edge',75.5,77.5,1,2.4,edge,bevel=.2)
ring('Perimeter shadow seam',65,76.8,3,4.4,dark,bevel=.1)
ring('Perimeter armor carrier',59,76.6,4.4,7,steel,bevel=.4)
ring('Cyan light channel bedding',71.7,74.4,7,8,dark,bevel=.15)
ring('Continuous outer cyan guide',72.6,73.5,8,8.2,cyan,bevel=.12)
ring('Inner emitter channel bedding',48.5,53,3.8,6,dark,bevel=.3)
ring('Reactor chamber bed',18,49.5,2,4.1,dark,bevel=.3)
cyl('Reactor floor',20,2,3.4,panel,bevel=.4)
for i in range(16):
    a=i*math.tau/16;gap=.015
    ring('Outer replaceable armor %02d'%i,63,71.6,6.7,9,edge if i%4==0 else steel,a+gap,a+math.tau/16-gap,128,.3)
    ring('Outer bumper panel %02d'%i,74.4,76.8,6.5,8.3,steel,a+gap,a+math.tau/16-gap,128,.22)
    ring('Landing plate %02d'%i,53,62.5,4.8,7.8,steel if i%2 else edge,a+gap,a+math.tau/16-gap,128,.3)
    ring('Violet field annulus %02d'%i,50.1,51.1,5.9,6.2,violet if i%4 in (0,1) else cyan,a+.025,a+math.tau/16-.025,160,.1)
    mid=a+math.pi/16
    for r in (65.1,69.8):
        cyl('Captive washer',1.14,.17,9.08,dark,xy(r,mid),24,.06)
        cyl('Hex socket bolt',.75,.3,9.27,edge,xy(r,mid),6,.1)
        cyl('Recessed socket',.32,.035,9.44,dark,xy(r,mid),6,.02)
    if i%4==0:label('T O D  /  TRANSIT',67.5,mid,9.42,1.1)
    # Shallow side cassettes with protected luminous status slits.
    p=xy(77.05,mid);box('Side service cassette',(*p,4.55),(1.3,9.4,2.35),dark,mid,.2)
    p=xy(77.76,mid);box('Side status lens',(*p,4.6),(.15,5.2,.42),cyan if i%4 else violet,mid,.08)
for i in range(12):
    a=i*math.tau/12;gap=.035
    ring('Inset radial reactor panel %02d'%i,22,47.5,3.9,5.1,panel,a+gap,a+math.tau/12-gap,144,.3)
    mid=a+math.pi/12
    p=xy(38,mid);box('Induction cartridge',(*p,5.35),(15,5.0,.8),dark,mid,.22)
    for j in range(8):
        p=xy(32.1+j*1.65,mid);box('Copper cooling lamella',(*p,5.9),(.63,4,.7),bronze,mid,.11)
    p=xy(38,mid);box('Cartridge emissive sightline',(*p,6.4),(11.8,.38,.18),violet,mid,.08)
    # Thin flush conductor traces, grounded with dark backing.
    p=xy(35,a);box('Radial flux groove',(*p,5.3),(25,1.7,.45),dark,a,.16)
    p=xy(35,a);box('Radial flux conductor',(*p,5.57),(23,.5,.18),cyan,a,.07)
    ring('Inner circuit arcs',25.5,26,5.15,5.27,cyan,a+.045,a+math.tau/12-.08,192,.04)
    ring('Outer circuit arcs',46.1,46.6,5.15,5.27,violet,a+.045,a+math.tau/12-.08,192,.04)
    cyl('Panel lock',.66,.18,5.24,edge,xy(29,mid),8,.08)
ring('Central reactor steel bezel',18.5,21.8,3.5,6.2,edge,bevel=.4)
ring('Central isolation seal',16.8,18.5,4.5,6.3,dark,bevel=.12)
ring('Central violet emitter ring',16.9,17.65,6.32,6.55,violet,steps=128,bevel=.1)
cyl('Solid smoked ceramic core',16.6,1.3,5.25,panel,vertices=96,bevel=.4)
for i in range(8):
    a=i*math.tau/8
    ring('Iris metal sector',6.3,15.7,5.95,6.5,steel,a+.035,a+.70,128,.15)
    ring('Core charged trace',11.4,11.8,6.53,6.65,cyan,a+.08,a+.60,160,.04)
ring('Luminous core aperture',4.5,6,6.25,6.65,white,steps=96,bevel=.1)
cyl('Aperture dark center',4.35,.6,6.12,dark,vertices=64,bevel=.2)
for i in range(3):
    a=i*math.tau/3;p=xy(2.3,a);box('Core energy node',(*p,6.5),(1.8,.45,.1),white,a,.06)
for i in range(4):
    a=(i*4+1.5)*math.tau/16;label('CAUTION  /  FIELD ARRAY',57.9,a,8.17,1.12)
    for j in range(4):
        p=xy(60.3,a+(j-1.5)*.025);box('Warning hatch',(*p,8.13),(1.5,.45,.08),bronze,a+.4,.02)
# Honest standalone review stage: no screenshot-derived background.
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-13.1));ground=bpy.context.object;ground.name='Review ground';move(ground,stage);ground.data.materials.append(mat('Stage | charcoal',(.018,.024,.039),.3,.34))
def light(name,loc,color,power,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);stage.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,0))-ob.location).to_track_quat('-Z','Y').to_euler()
light('Large neutral key',(-80,-85,155),(.7,.83,1),230000,120)
light('Soft neutral fill',(60,-10,100),(1,.86,.73),100000,80)
light('Violet rim',(-30,105,75),(.37,.12,1),140000,90)
light('Cyan rim',(95,55,50),(.06,.6,1),100000,70)
data=bpy.data.cameras.new('Teleporter review');cam=bpy.data.objects.new('Teleporter review',data);stage.objects.link(cam);scene.camera=cam
cam.location=(152,-198,143);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=196
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world.color=(.1,.1,.1);scene.view_settings.view_transform='AgX'
scene.render.use_compositing=False
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.overlay.show_overlays=False;s.clip_end=5000;s.shading.type='MATERIAL';s.region_3d.view_location=(0,0,0);s.region_3d.view_distance=230;s.region_3d.view_rotation=cam.rotation_euler.to_quaternion();s.region_3d.view_perspective='PERSP'
scene['mcp_port']=9879;scene['native_scale']='1 Blender unit = 1 game unit; origin is floor; no runtime scale or sink'
scene['design']='Original lower casting retained. New layered alloy deck, copper inductors and recessed cyan/violet emitters.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'teleporter_cyber.blend'))
print('TELEPORTER_AUTHORED',len([o for o in design.objects]),'parts; original assembly preserved')
