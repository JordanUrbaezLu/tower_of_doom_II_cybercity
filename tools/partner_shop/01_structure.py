"""First authored pass, executed in the dedicated live Blender MCP studio.

Coordinates are BO3 inches: floor Z=0; customer approaches from -Y.
Only this studio's named collections may be replaced on subsequent runs.
"""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/partner_shop'
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.name = 'TOD2 | THE BROKER | Shop art study'
if not scene.get('tod2_shop_studio'):
    if set(o.name for o in scene.objects) != {'Cube', 'Camera', 'Light'}:
        raise RuntimeError('Refusing to replace a non-shop scene')
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
scene['tod2_shop_studio'] = True
for col in list(bpy.data.collections):
    if col.name.startswith('SHOP |'):
        for ob in list(col.objects): bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(col)
def collection(name):
    c = bpy.data.collections.new('SHOP | ' + name)
    scene.collection.children.link(c)
    return c
shell = collection('01 HUT - always present')
detail = collection('02 HARDWARE - always present')
stock = collection('03 INVENTORY - always present')
vendor = collection('04 MERCHANT - active only')
active = collection('05 ACTIVE lamps')
stage = collection('90 STUDIO - exclude from export')
anchors = collection('91 SOCKETS - metadata only')

def material(name, color, metal=0, rough=.5, emission=0, grain=True):
    name = 'SHOP / ' + name
    if globals().get('PRESERVE_SHOP_MATERIALS',False) and bpy.data.materials.get(name):
        return bpy.data.materials[name]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; m.diffuse_color = (*color, 1)
    n = m.node_tree.nodes; n.clear(); l = m.node_tree.links
    out = n.new('ShaderNodeOutputMaterial'); p = n.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value = (*color,1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    p.inputs['Emission Color'].default_value = (*color,1)
    p.inputs['Emission Strength'].default_value = emission
    l.new(p.outputs['BSDF'],out.inputs['Surface'])
    if grain and not emission:
        tex = n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = 8
        tex.inputs['Detail'].default_value = 3; tex.inputs['Roughness'].default_value = .75
        ramp = n.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position=.22
        ramp.color_ramp.elements[0].color=(*(v*.65 for v in color),1)
        ramp.color_ramp.elements[1].position=.8
        ramp.color_ramp.elements[1].color=(*(min(1,v*1.28) for v in color),1)
        l.new(tex.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],p.inputs['Base Color'])
        fine=n.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value=185
        bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.22
        bump.inputs['Distance'].default_value=.027
        l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return m

iron=material('weathered charcoal enamel',(.043,.052,.065),.68,.42)
black=material('oiled recess metal',(.008,.012,.018),.35,.55)
steel=material('edge-worn machined steel',(.20,.235,.265),.83,.36)
brass=material('aged warm brass',(.25,.13,.048),.78,.4)
copper=material('oxidized copper fittings',(.18,.062,.031),.7,.45)
paint=material('desaturated plum enamel',(.083,.043,.075),.52,.4)
rubber=material('rubber and cable jackets',(.014,.018,.021),.02,.72)
cloth=material('black heavy woven coat',(.009,.011,.014),0,.89)
clothEdge=material('worn black cloth bindings',(.023,.026,.032),0,.83)
skin=material('merchant weathered skin',(.23,.13,.095),0,.71)
ink=material('ivory stencilled markings',(.54,.56,.49),.1,.66)
violet=material('violet discharge glass',(.31,.027,.64),.2,.27,2.5,False)
cyan=material('muted cyan phosphor',(.025,.38,.47),.15,.3,1.7,False)
amber=material('amber instrument lamps',(.66,.21,.038),.2,.3,2.1,False)
warm=material('warm service window tube',(.65,.47,.26),0,.35,3,False)

def finish(ob,name,mat,col=shell,bevel=0,smooth=False):
    ob.name=name
    for c in list(ob.users_collection): c.objects.unlink(ob)
    col.objects.link(ob)
    if mat: ob.data.materials.append(mat)
    if bevel:
        mod=ob.modifiers.new('Worked edge radius','BEVEL');mod.width=bevel;mod.segments=3
        mod=ob.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    if smooth and ob.type=='MESH':
        for p in ob.data.polygons:p.use_smooth=True
    ob['shop_part']=col.name
    return ob
def box(name,loc,size,mat=iron,col=shell,bevel=.3,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rot:o.rotation_euler=rot
    return finish(o,name,mat,col,bevel)
def mesh(name,verts,faces,mat,col=shell,bevel=0,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob)
    return finish(ob,name,mat,col,bevel,smooth)
def cylinder(name,loc,r,depth,mat,col=detail,axis=(0,0,1),vertices=40,bevel=.12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc)
    ob=bpy.context.object;ob.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    return finish(ob,name,mat,col,bevel,True)
def sphere(name,loc,size,mat,col=detail):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=loc)
    ob=bpy.context.object;ob.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(ob,name,mat,col,0,True)
def tube(name,pts,r,mat,col=detail,cyclic=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=10
    cu.bevel_depth=r;cu.bevel_resolution=3
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
    for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    sp.use_cyclic_u=cyclic
    ob=bpy.data.objects.new(name,cu);col.objects.link(ob);ob.data.materials.append(mat)
    return ob
def beam(name,a,b,r,mat,col=detail,vertices=24):
    a,b=Vector(a),Vector(b)
    return cylinder(name,(a+b)/2,r,(b-a).length,mat,col,b-a,vertices)
def text(body,loc,size,mat=ink,col=detail,align='CENTER',rot=(math.pi/2,0,0),depth=.015):
    cu=bpy.data.curves.new('Marking '+body,'FONT');cu.body=body;cu.align_x=align
    cu.size=size;cu.extrude=depth;cu.bevel_depth=.006
    ob=bpy.data.objects.new('Marking | '+body,cu);col.objects.link(ob)
    ob.location=loc;ob.rotation_euler=rot;cu.materials.append(mat)
    return ob
def bolt(loc,axis=(0,-1,0),r=.52):
    cylinder('Captive hex head',loc,r,.32,steel,axis=axis,vertices=6,bevel=.045)
def plate(name,x,y,z,w,h,mat=iron):
    box(name,(x,y,z),(w,1.3,h),mat,detail,.55)
    for dx in (-w/2+1.5,w/2-1.5):
        for dz in (-h/2+1.5,h/2-1.5):bolt((x+dx,y-.82,z+dz))
def light(name,loc,color,power,size,target):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);stage.objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
def camera(name,loc,target,lens=48):
    data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);stage.objects.link(ob)
    ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    data.lens=lens;data.clip_end=5000;return ob

# Raised skid foundation, octagonal corner cuts, anchored floor; no climbable porch.
box('Continuous sealed undercarriage',(0,0,3),(146,101,6),black,bevel=2)
box('Armored plinth',(0,0,7),(142,98,5),iron,bevel=2)
box('Exposed floor lip',(0,0,10),(137,94,2.5),steel,bevel=1)
box('Interior rubber deck',(0,1,11.4),(129,87,1),rubber,bevel=.3)
for x in (-61,61):
    for y in (-39,39):
        box('Corner leveling foot',(x,y,2),(20,20,4),iron,bevel=1.2)
        cylinder('Foot anchor bolt',(x,y,4.2),1.7,.6,steel,vertices=6)
for x in (-64,64):
    box('Deep side wall',(x,3,51),(5,85,79),iron,bevel=1)
    for y in (-37,41):
        box('Structural column',(x,y,53),(9,9,86),iron,bevel=1)
        box('Column brass shoe',(x,y,16),(10,10,8),brass,bevel=.5)
        box('Column top collar',(x,y,90),(10,10,7),steel,bevel=.5)
box('Rear insulated wall',(0,44,51),(129,5,79),iron,bevel=1)
box('Rear inside dark liner',(0,40.8,54),(117,1.6,66),black,bevel=.5)
box('Counter armored bulkhead',(0,-36,26),(119,7,28),iron,bevel=1)
for x in (-40,0,40):
    plate('Recessed kick panel',x,-40.2,26,36,23,paint if x==0 else iron)
    for z in (20,23,26,29,32):box('Kick-panel louver',(x,-41.2,z),(27,.75,.6),black,detail,.1)
box('Counter rubber shadow line',(0,-39,42),(127,29,2),rubber,bevel=.8)
box('Deep worn steel service counter',(0,-40,44),(130,30,3),steel,bevel=1.1)
box('Counter front brass nosing',(0,-55.1,43.6),(128,1.3,2.4),brass,bevel=.45)
box('Transaction work mat',(0,-38,45.7),(49,22,.55),rubber,detail,.6)
for x in (-59,59):
    box('Window upright seal',(x,-40.7,67),(2.1,2.2,44),rubber,bevel=.3)
    box('Window steel reveal',(x-1 if x<0 else x+1,-42.5,67),(1,1,42),steel,bevel=.15)
    box('Violet jamb inset',(x,-44,70),(.5,.35,25),violet,active,.1)

# Faceted shallow pitched hut roof: a recognizable canopy, gutters and real underside.
xs=[-77,-62,0,62,77]; zs=[94,100,111,100,94]
verts=[(x,y,z) for y in (-56,53) for x,z in zip(xs,zs)]
faces=[(i,i+1,i+6,i+5) for i in range(4)]
roof=mesh('Folded standing-seam roof',verts,faces,iron,shell)
sol=roof.modifiers.new('Roof sheet thickness','SOLIDIFY');sol.thickness=1.4
be=roof.modifiers.new('Roof soft folds','BEVEL');be.width=.35;be.segments=3
for y in (-55,52):
    tube('Heavy shaped roof fascia',[(x,y,z) for x,z in zip(xs,zs)],1.8,black,shell)
    tube('Weathered fascia edge',[(x,y-.4,z+1.1) for x,z in zip(xs,zs)],.45,brass)
for y in range(-45,53,12):
    tube('Raised roof sheet seam',[(x,y,z+.9) for x,z in zip(xs,zs)],.38,steel)
for x in (-76,76):
    box('Rain gutter',(x,-1,93.5),(3.2,111,3),black,bevel=.6)
    tube('Gutter copper drain',[(x,45,94),(x+1,48,87),(x+1,48,19),(x+5,44,13)],.85,copper)
box('Service-window header',(0,-39,91),(120,12,8),iron,bevel=.8)
cylinder('Rolled security shutter',(0,-35.5,92),3.2,113,steel,axis=(1,0,0),bevel=.3)
for x in range(-54,55,6):cylinder('Shutter roll collar',(x,-35.5,92),3.35,.45,black,axis=(1,0,0))
box('Under-canopy lamp housing',(0,-45,90),(85,4,2),black,detail,.5)
box('Under-canopy warm tube',(0,-45,88.9),(78,1.1,.55),warm,active,.25)

# Raised sign; a replaceable identity panel, separate from fine service labels.
plate('Main sign carrier',0,-54,104,89,18,black)
box('Sign inset face',(0,-55,104),(84,.9,14),paint,detail,.8)
text('THE BROKER',(0,-55.65,101.3),7.7,ink)
text('PARTNER  /  UPGRADES',(0,-42,36.5),2.15,ink)
for x in (-43,43):box('Sign violet pilot',(x,-55.9,104),(.6,.3,10),violet,active,.15)

# Usable inner shelf framing; vendor center deliberately kept open.
for z in (31,55,78):
    box('Rear inventory shelf',(0,31,z),(111,19,2),iron,stock,.5)
    box('Shelf brass lip',(0,21.8,z+.5),(109,.7,2),brass,stock,.12)
for x in (-54,54):
    box('Shelf rack support',(x,34,49),(2,3,70),steel,stock,.3)
    for z in (32,56,79):
        beam('Shelf triangular bracket',(x,24,z),(x,38,z-8),.5,brass,stock)

# Side machinery bay is integrated with the hut, not floating decoration.
box('Power cabinet',(72,13,44),(14,40,54),black,detail,1.2)
box('Cabinet plum cover',(80,13,44),(1.5,35,48),paint,detail,.7)
for y in (-1,27):
    for z in (24,64):bolt((81,y,z),(1,0,0),.7)
for z in range(29,58,4):box('Side cabinet cooling fin',(82,13,z),(2,25,1.1),steel,detail,.2)
box('Left electrical chase',(-69,0,48),(6,57,66),black,detail,.8)
for y in (-18,-10):
    tube('Left exposed brass riser',[(-74,y,18),(-74,y,72),(-71,y,82),(-64,y,84)],.9,brass)

# Runtime contract: a persistent hut plus a separately spawned merchant.
for name,loc in [('tag_origin',(0,0,0)),('tag_vendor',(0,0,11.9)),('tag_shop_beacon',(0,4,116)),('tag_use',(0,-89,44))]:
    ob=bpy.data.objects.new(name,None);anchors.objects.link(ob);ob.location=loc;ob.empty_display_size=3
scene['shop_front']='-Y';scene['shop_units']='1 Blender unit = 1 BO3 inch'
scene['shop_active_contract']='Persistent hut; separate merchant shown only at the active location. Stock Wunderfizz beacon is a runtime FX, not exported Blender geometry.'
scene['shop_beacon_candidate']='zombie/fx_wonder_fizz_lightning_all'

# Neutral studio lighting makes charcoal materials readable while keeping the recess dark.
box('Studio floor',(0,0,-1.2),(1800,1800,2),material('studio ground',(.025,.031,.044),.1,.62),stage,.0)
light('Studio cool broad key',(40,-150,190),(.66,.78,1),450000,160,(0,0,50))
light('Studio left soft fill',(-170,-65,95),(.73,.66,.82),220000,140,(0,0,53))
light('Studio rear violet rim',(40,115,155),(.45,.22,1),420000,95,(0,0,55))
light('Window practical',(0,-40,84),(1,.72,.42),14000,65,(0,5,51))
hero=camera('01 HERO - three-quarter',(198,-288,144),(0,0,55),49)
camera('02 PLAYER - service window',(0,-234,66),(0,0,64),44)
camera('03 REAR - service hardware',(-186,245,135),(0,0,51),49)
scene.camera=hero
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
# Eevee keeps the interactive viewport and review renders responsive.
scene.render.engine='CYCLES'
scene.render.resolution_x=1440;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.world.color=(.08,.08,.08)
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.12,.15,.21,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.32
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.render.image_settings.file_format='PNG'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.clip_end=5000;s.shading.type='MATERIAL'
            s.shading.use_scene_world=False;s.overlay.show_overlays=False
            s.region_3d.view_distance=260;s.region_3d.view_location=(0,0,52)
            s.region_3d.view_rotation=hero.rotation_euler.to_quaternion()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print(json.dumps({'stage':'structure','objects':len(scene.objects),'master':str(OUT/'partner_shop.blend')}))
