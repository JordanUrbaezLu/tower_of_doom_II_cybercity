"""Blender MCP authoring: preserve the sword, replace finish and blade circuitry."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/cyber_sword'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'original_reference.blend'))
scene=bpy.data.scenes.get('Scene') or bpy.data.scenes[0]
for win in bpy.context.window_manager.windows:win.scene=scene
print('CS_AUTHOR_STAGE opened source',flush=True)
keep={'01 Structure','02 Ornament','03 Grip detail','04 Jewel','05 Fine relief','98 Attachment guide'}
for ob in list(scene.objects):
    if not any(c.name in keep for c in ob.users_collection):bpy.data.objects.remove(ob,do_unlink=True)
print('CS_AUTHOR_STAGE isolated design objects',flush=True)
scene.name='Cyber Sword | charge studio';scene['cyber_charge']=1.0
scene.id_properties_ui('cyber_charge').update(min=0.,max=1.,description='0 charging: dark inlays / 1 Gravity Smash ready: cyan circuitry')
design=bpy.data.collections.new('CYBER | engineered inlays');scene.collection.children.link(design)

def material(name,color,metal=.8,rough=.43,emission=0):
    mat=bpy.data.materials.new('CS | '+name);mat.use_nodes=True
    mat['cyber_role']=name;mat['ready_strength']=emission
    p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Emission Color'].default_value=(*color,1)
    if emission:
        fc=p.inputs['Emission Strength'].driver_add('default_value');driver=fc.driver
        v=driver.variables.new();v.name='charge';v.type='SINGLE_PROP';v.targets[0].id_type='SCENE';v.targets[0].id=scene;v.targets[0].data_path='["cyber_charge"]'
        driver.expression=str(emission)+'*charge'
    else:
        # World-position grain remains stable when the game meshes are joined.
        n=mat.node_tree.nodes;l=mat.node_tree.links;geo=n.new('ShaderNodeNewGeometry')
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=850;noise.inputs['Detail'].default_value=2
        l.new(geo.outputs['Position'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.2;ramp.color_ramp.elements[1].position=.8
        ramp.color_ramp.elements[0].color=(*(x*.7 for x in color),1);ramp.color_ramp.elements[1].color=(*(x*1.2 for x in color),1)
        l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.00007
        l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
    mat.diffuse_color=(*color,1);return mat
shell=material('gunmetal',(.028,.049,.069),.86,.46)
inset=material('carbon ceramic',(.011,.019,.031),.45,.56)
edge=material('titanium edge',(.23,.32,.39),.95,.32)
violet=material('violet hardware',(.095,.026,.18),.8,.4)
rubber=material('rubber grip',(.009,.013,.020),0,.66)
cobalt=material('cobalt trim',(.014,.075,.23),.8,.4)
cyan=material('cyan circuit',(.006,.65,1),.3,.25,12)
purple=material('violet cell',(.25,.018,1),.3,.28,7)
blue=material('blue reactor',(.008,.20,1),.45,.23,9)
removed=[]
for ob in list(scene.objects):
    if ob.name.startswith(('Chinese blade','Blade crown simple')):
        removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True);continue
    if ob.type not in ('MESH','CURVE','FONT'):continue
    ob['cyber_sword_part']=True;ob.hide_render=False;ob.hide_set(False)
    # Original fitted blade borders become the two physical power rails.
    if ob.name.startswith('Blade gold border'):
        ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(cyan)
        ob['cyber_feature']='fitted cyan power rail';continue
    for slot in ob.material_slots:
        name=slot.material.name if slot.material else ''
        if 'Sapphire' in name:slot.material=cyan if 'cyan' in name else (purple if 'violet' in name else blue)
        elif 'Blade edge' in name:slot.material=edge
        elif 'Blade dark' in name or 'Gold dark' in name:slot.material=inset
        elif 'leather' in name.lower():slot.material=rubber
        elif 'raised' in name:slot.material=cobalt
        else:slot.material=shell
    if ob.name.startswith(('Quillon long','Pommel fitted')):
        ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(violet)
print('CS_AUTHOR_STAGE base materials complete',flush=True)

def mesh(name,verts,faces,mat):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();me.materials.append(mat)
    ob=bpy.data.objects.new(name,me);design.objects.link(ob);ob['cyber_sword_part']=True
    return ob
def panel(name,cx,cz,width,height,depth,side,mat,bevel=.0008):
    cut=min(width*.2,.004);xy=[(-width/2,-height/2+cut),(-width/2+cut,-height/2),(width/2-cut,-height/2),(width/2,-height/2+cut),(width/2,height/2-cut),(width/2-cut,height/2),(-width/2+cut,height/2),(-width/2,height/2-cut)]
    verts=[(cx+x,side*(depth+y),cz+z) for y in (-.0007,.0007) for x,z in xy]
    faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    ob=mesh(name,verts,faces,mat)
    import bmesh
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    mod=ob.modifiers.new('Machined chamfer','BEVEL');mod.width=bevel;mod.segments=2
    return ob
def trace(name,points,side,mat,r=.00065,depth=.0078):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1;cu.resolution_u=1
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,(x,z) in zip(sp.points,points):p.co=(x,side*depth,z,1)
    cu.materials.append(mat);ob=bpy.data.objects.new(name,cu);design.objects.link(ob);ob['cyber_sword_part']=True;return ob
for side,label in [(-1,'front'),(1,'back')]:
    panel('Power spine backing '+label,0,.390,.043,.748,.0072,side,inset)
    # Each housing is interrupted by an exposed energy bridge. Narrow enough
    # for the retained cutting edge; both faces receive real geometry.
    for i,z in enumerate((.12,.25,.38,.51,.64)):
        width=.034 if i<2 else .043
        panel('Spine housing '+label+' '+str(i),0,z,width,.089,.0090,side,shell)
        trace('Cyan bus '+label+' '+str(i),[(-.004,z-.039),(-.004,z-.012),(.004,z),(.004,z+.040)],side,cyan,depth=.0106)
        for j in range(3):
            cx=(-1 if i%2 else 1)*(width/2-.0045)
            panel('Violet charge cell '+label+' '+str(i)+' '+str(j),cx,z-.025+j*.019,.004,.009,.0102,side,purple,.0004)
        trace('Branch '+label+' '+str(i),[(.004,z),(.012,z+.012),(.012,z+.043),(.023,z+.054)],side,cyan,r=.0005,depth=.0104)
    trace('Tip feed '+label,[(0,-.092),(0,.069),(-.004,.081)],side,cyan,r=.0006,depth=.0066)
    panel('Spine terminal '+label,0,.735,.034,.061,.0090,side,shell)
    for dx in (-.010,0,.010):trace('Terminal socket '+label+str(dx),[(dx,.719),(dx,.748)],side,blue,r=.0009,depth=.0107)
    # Small armored modules on the existing crossguard.
    for sign in (-1,1):
        panel('Guard capacitor '+label+str(sign),sign*.067,.849,.043,.027,.009,side,shell)
        for j in range(3):
            trace('Guard vent '+label+str(sign)+str(j),[(sign*.067-.011+j*.011,.842),(sign*.067-.011+j*.011,.856)],side,purple,r=.0008,depth=.011)
        trace('Guard feeder '+label+str(sign),[(sign*.020,.849),(sign*.037,.849),(sign*.045,.856)],side,cyan,r=.001,depth=.012)

# Keep the imported guide transform for native rig placement. No weapon motion
# tracks or native donor inputs are edited by the authoring scene.
guide=scene.objects['Citadel attachment guide'];guide.hide_render=True
print('CS_AUTHOR_STAGE mechanical details complete',flush=True)
scene['cyber_sword_brief']='Dark machined body; titanium edge; cyan circuit rails; violet cells; bright only when Gravity Smash is ready or casting.'
scene['native_grip_lift_inches']=1.1
studio=bpy.data.collections.new('CYBER | preview studio');scene.collection.children.link(studio)
def addlight(name,loc,energy,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.55))-o.location).to_track_quat('-Z','Y').to_euler()
addlight('Neutral key',(-1.2,-1.4,.85),45,1.3,(.78,.89,1))
addlight('Soft violet rim',(.7,.8,.6),30,1,(.38,.27,1))
addlight('Long softbox',(.7,-.5,.4),12,.9,(1,1,1))
cam=bpy.data.objects.new('Cyber Sword | full length',bpy.data.cameras.new('Cyber Sword | full length'));studio.objects.link(cam)
cam.location=(.30,-2.5,.54);cam.rotation_euler=(Vector((0,0,.53))-cam.location).to_track_quat('-Z','Y').to_euler();cam.rotation_euler.rotate_axis('Z',math.pi)
cam.data.type='ORTHO';cam.data.ortho_scale=1.53;scene.camera=cam
scene.world=bpy.data.worlds.new('Cyber Sword | neutral dark');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.028,.035,.050,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.render.engine='CYCLES';scene.cycles.samples=32
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=850;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0
scene.render.fps=30;scene.frame_start=1;scene.frame_end=90
for frame,value in [(1,0),(30,0),(42,1),(75,1),(83,0),(90,0)]:
    scene['cyber_charge']=value;scene.keyframe_insert(data_path='["cyber_charge"]',frame=frame)
scene.frame_set(60)
scene.update_tag();bpy.context.view_layer.update()
for win in bpy.context.window_manager.windows:
    for area in win.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL';area.spaces.active.overlay.show_overlays=False
scene.render.filepath=str(OUT/'ready.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'cyber_sword.blend'))
(OUT/'authoring.json').write_text(json.dumps(dict(parts=sum(bool(o.get('cyber_sword_part')) for o in scene.objects),removed_ornaments=removed,
    added_parts=len(design.objects),guide_matrix=[list(row) for row in guide.matrix_world],native_grip_lift_inches=1.1,
    original_source_unchanged=True,native_playtested=False),indent=2))
print('CYBER_SWORD_AUTHORED',len(design.objects),'new engineered details',flush=True)
