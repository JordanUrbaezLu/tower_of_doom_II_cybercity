"""Author real panel geometry and reusable materials through Blender MCP."""
import bpy, math, pathlib, json, sys
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/cybercity_materials';ART.mkdir(parents=True,exist_ok=True)
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
scene=bpy.context.scene;scene.unit_settings.system='NONE';scene['units']='Native BO3 units; 128-unit tile / 1024 texels'
scene['authoring']='Blender MCP, shared realistic Cybercity surface kit'
def material(name,color,metal,rough,emit=0):
    m=bpy.data.materials.new('CC | '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    n,l=m.node_tree.nodes,m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
    if not emit:
        geom=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.32;noise.inputs['Detail'].default_value=2
        l.new(geom.outputs['Position'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(v*.84 for v in color),1);ramp.color_ramp.elements[1].color=(*(v*1.08 for v in color),1)
        l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
        rr=n.new('ShaderNodeMapRange');rr.inputs['To Min'].default_value=rough-.035;rr.inputs['To Max'].default_value=rough+.035;l.new(noise.outputs['Fac'],rr.inputs['Value']);l.new(rr.outputs[0],p.inputs['Roughness'])
        micro=n.new('ShaderNodeTexNoise');micro.inputs['Scale'].default_value=7;l.new(geom.outputs['Position'],micro.inputs['Vector'])
        bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.008;bump.inputs['Strength'].default_value=.18;l.new(micro.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    m.asset_mark();m.asset_data.description='Cybercity realistic shared kit. Native satin profile; inspect in BO3 before approval.'
    m['cc_finish']='architecture';return m
paint=material('graphite coated steel',(.035,.043,.054),.3,.57)
alloy=material('satin gunmetal',(.135,.155,.175),.78,.47)
tread=material('worked deck steel',(.062,.071,.084),.62,.62)
rubber=material('gasket and recess',(.012,.016,.021),0,.78)
copper=material('aged copper contacts',(.25,.105,.044),.8,.46)
oxide=material('oxblood panel marking',(.095,.016,.022),.15,.6)
red=material('recessed red guide',(.65,.012,.022),.1,.45,.4)
amber=material('service warning paint',(.33,.19,.049),.1,.63)
materials=[paint,alloy,tread,rubber,copper,oxide,red,amber]
col=None;offset=0
def finish(ob,name,mat,bevel=.12):
    ob.name=name;ob.location.x+=offset
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob);ob.data.materials.append(mat);ob['cc_tile']=col.name
    if bevel:
        b=ob.modifiers.new('Manufactured edge','BEVEL');b.width=bevel;b.segments=3
        n=ob.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');n.keep_sharp=True
    return ob
def box(name,loc,dims,mat,bevel=.12):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,bevel)
def bolt(x,y):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=1.65,depth=.17,location=(x,y,.27));finish(bpy.context.object,'Recessed captive washer',rubber,.08)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=1.03,depth=.25,location=(x,y,.39));finish(bpy.context.object,'Satin hex head',alloy,.11)
    box('Driver slot',(x,y,.535),(1.2,.26,.04),rubber,.02)
def wear(x,y,length=2.0):box('Localized edge scuff',(x,y,.31),(length,.12,.025),alloy,.025)
for idx,kind in enumerate(('floor','wall','ceiling','trim')):
    offset=idx*160;col=bpy.data.collections.new('CC_TILE_'+kind);scene.collection.children.link(col)
    col['cc_kind']=kind;col['cc_offset']=offset
    box('Recessed backing',(64,64,-.45),(128,128,.9),rubber,0)
    if kind=='floor':
        for x,y in ((32,32),(96,32),(32,96),(96,96)):
            box('Replaceable floor plate',(x,y,.12),(62.4,62.4,.24),tread,.24)
            for dx in (-26,26):
                for dy in (-26,26):bolt(x+dx,y+dy)
            for j in range(6):
                for side in (-1,1):
                    o=box('Shallow traction rib',(x+side*11,y-17+j*6.7,.32),(14,1.25,.18),paint,.28);o.rotation_euler.z=side*math.radians(25)
            wear(x-18,y-30,4.3);wear(x+11,y+30,2.7)
        for y in (11,75):box('Small copper service index',(63.6,y,.07),(.45,9,.1),copper,.04)
    elif kind=='wall':
        for x,width in ((45,87),(111,26)):
            box('Folded wall cassette',(x,64,.1),(width,124,.2),paint,.24)
            for y in (9,119):
                for xx in ((7,83) if width>30 else (105,118)):bolt(xx,y)
        box('Inset access panel',(44,63,.25),(70,75,.18),rubber,.45)
        box('Satin service hatch',(44,63,.37),(66,71,.16),paint,.4)
        for y in (31,95):
            for x in (15,73):bolt(x,y)
        for y in range(41,88,7):box('Vent slot',(46,y,.465),(41,2.0,.04),rubber,.35)
        box('Protected guide bedding',(95,64,.11),(4,128,.2),rubber,.2)
        box('Dim red optical core',(95,64,.26),(.6,128,.08),red,.07)
        for y in range(14,126,27):box('Guide retaining clip',(95,y,.35),(6,1.4,.22),alloy,.15)
        box('Oxblood serial plaque',(39,111,.27),(37,5.2,.09),oxide,.17)
        for x in (20,25,29,38,46,55):box('Etched serial stroke',(x,111,.325),(.55,2.2,.02),alloy,.015)
        wear(30,98,5);wear(57,27,3)
    elif kind=='ceiling':
        box('Ceiling carrier',(64,64,.11),(125,125,.22),paint,.3)
        for x in (10,118):
            box('Satin service rail',(x,64,.33),(5,128,.25),alloy,.3)
            for y in (10,64,118):bolt(x,y)
        for y in (31,96):
            box('Fan shadow well',(64,y,.29),(81,46,.18),rubber,.5)
            for j in range(7):box('Vent louvre',(64,y-18+j*6,.49),(74,2.9,.35),paint,.38)
        for y in (60,68):box('Central reinforcing bead',(64,y,.37),(83,2.1,.26),alloy,.25)
        box('Warning index',(64,64,.36),(9,4,.17),amber,.12)
    else:
        for y in (16,48,80,112):
            box('Trim carrier',(64,y,.1),(128,30,.2),paint,.24)
            for yy in (y-11,y+11):box('Satin bevel rail',(64,yy,.36),(128,2.2,.35),alloy,.3)
            box('Inset longitudinal seam',(64,y,.22),(128,2,.12),rubber,.1)
            for x in (16,112):bolt(x,y)
            for x in range(35,99,8):box('Machined index notch',(x,y+.1,.315),(1.0,5,.035),oxide,.05)
    low_col=bpy.data.collections.get('CC_RECEIVERS')
    if not low_col:low_col=bpy.data.collections.new('CC_RECEIVERS');scene.collection.children.link(low_col)
    bpy.ops.mesh.primitive_plane_add(size=128,location=(offset+64,64,0));receiver=bpy.context.object;receiver.name='CC receiver '+kind
    for c in list(receiver.users_collection):c.objects.unlink(receiver)
    low_col.objects.link(receiver);receiver['cc_kind']=kind;receiver.hide_render=True;receiver.hide_set(True)
stage=bpy.data.collections.new('CC_REVIEW');scene.collection.children.link(stage)
def light(name,loc,energy,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);stage.objects.link(o);o.location=loc;o.rotation_euler=(Vector((300,64,0))-o.location).to_track_quat('-Z','Y').to_euler()
light('Neutral broad key',(180,-90,250),1250000,220,(1,.94,.87))
light('Soft fill',(450,190,180),650000,200,(.7,.82,1))
cam=bpy.data.objects.new('Surface kit camera',bpy.data.cameras.new('Surface kit camera'));stage.objects.link(cam);scene.camera=cam
cam.location=(310,-360,520);cam.rotation_euler=(Vector((304,64,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=680;cam.data.clip_end=2000
scene.world.color=(.045,.045,.045);scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=1600;scene.render.resolution_y=760;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
for win in bpy.context.window_manager.windows:
    for area in win.screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'cybercity_material_library.blend'))
(ART/'library.json').write_text(json.dumps({'version':1,'direction':'realistic manufactured dark cybercity','tile_units':128,'tile_texels':1024,'materials':[m.name for m in materials],'tiles':['floor','wall','ceiling','trim'],'source':'Blender MCP authored geometry, no painted substitute','native_visual_approved':False},indent=2))
print('CC_KIT_AUTHORED',len(bpy.data.objects),'objects',len(materials),'reusable material assets')
