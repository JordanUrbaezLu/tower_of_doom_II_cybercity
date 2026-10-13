"""Execute through Blender MCP. Author/export the alarm, then save its studio."""
import bpy, math, json, pathlib, sys, re, hashlib
import numpy as np
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
OUT=ROOT/'art/crown_alarm'; OUT.mkdir(parents=True,exist_ok=True)
EXP=ROOT/'model_export/tod_crown_alarm'; EXP.mkdir(parents=True,exist_ok=True)
TEX=EXP/'_images'; TEX.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
for im in list(bpy.data.images):
    if im.name.startswith('i_tod_alarm_'):bpy.data.images.remove(im)
scene=bpy.context.scene; scene.name='Crown alarm - authored native asset'
scene.render.engine='CYCLES'; scene.cycles.samples=40; scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.fps=24
scene.view_settings.view_transform='AgX'
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.13,.15,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.25
blocks=[];textures={};mats={};parts=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def block(name,kind,fields):
    blocks.append('\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v)+'"\n' for k,v in fields.items())+'\t}\n')
def texture(label,color,rough,metal,alpha=1):
    # Shared Cybercity family: charcoal cast metal, brushed steel, rubber.
    # Deterministic patina textures exported from the same Blender images.
    n=512;rng=np.random.default_rng(47);y,x=np.mgrid[:n,:n]
    grain=rng.normal(0,.025,(n,n));brush=np.sin(y*.47)*.035
    scratch=np.zeros((n,n))
    for i in range(85):
        a,b=rng.integers(0,n,2);length=int(rng.integers(8,90))
        scratch[a,min(b,n-1):min(b+length,n)]=rng.uniform(.04,.14)
    noise=grain+brush+scratch if metal else grain*.3
    images={}
    for suffix in ['c','g','s','n']:
        a=np.ones((n,n,4),dtype=np.float32)
        if suffix=='c':
            a[:,:,:3]=np.clip(np.array(color)[None,None,:]*(1+noise[:,:,None]),0,1);a[:,:,3]=alpha
        elif suffix=='g':a[:,:,:3]=np.clip(1-rough+noise[:,:,None]*.3,0,1)
        elif suffix=='s':a[:,:,:3]=.6 if metal else .035
        else:
            a[:,:,0]=.5+grain*.15;a[:,:,1]=.5+brush*.08;a[:,:,2]=1
        name='i_tod_alarm_'+label+'_'+suffix
        im=bpy.data.images.new(name,width=n,height=n,alpha=True)
        if suffix in ['g','n']:im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(a.ravel());im.filepath_raw=str(TEX/(name+'.png'));im.file_format='PNG';im.save();im.pack()
        images[suffix]=im;textures[name+'.png']=sha(TEX/(name+'.png'))
        f=dict(baseImage='model_export/tod_crown_alarm/_images/'+name+'.png',imageType='Texture',type='image',semantic={'c':'diffuseMap','g':'glossMap','s':'specularMap','n':'normalMap'}[suffix],streamable=1,compressionMethod='compressed high color' if suffix in ['c','s'] else 'compressed')
        if suffix in ['c','s']:f['coreSemantic']='sRGB3chAlpha'
        block(name,'image',f)
    return images
def material(label,color,rough=.4,metal=0,alpha=1,emission=0):
    images=texture(label,color,rough,metal,alpha)
    name='mtl_tod_alarm_'+label;m=bpy.data.materials.new(name);m.use_nodes=True;m.use_fake_user=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=images['c'];m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if emission:
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=emission
    if alpha<1:
        # Transparent colored shell: physically separate rotor remains visible.
        bs.inputs['Alpha'].default_value=alpha;bs.inputs['Coat Weight'].default_value=.08
        m.surface_render_method='DITHERED'
    fields=dict(surfaceType='glass' if alpha<1 else 'metal',template='material.template',materialCategory='Geometry Advanced',materialType='lit_emissive_transparent' if alpha<1 else 'lit_emissive_advanced_fullspec',colorMap=images['c'].name,normalMap=images['n'].name,cosinePowerMap=images['g'].name,specColorMap=images['s'].name,specMapEnable=1,specColorTint='1 1 1 1',colorMap00=images['c'].name,colorTint='1 1 1 1',colorTint1='1 1 1 1',scaleRGB=emission,emissiveIncompetence=1,emissiveFalloff=0,normalHeightScale=1,glossRangeMin=0,glossRangeMax=8,specAmount=.5,reflectionProbeAmount=.3,textureAtlasRowCount=1,textureAtlasColumnCount=1,usage='<not in editor>')
    if alpha<1:fields.update(noCastShadow=1,noReceiveDynamicShadow=1)
    # Reserve the native sRGB dielectric tint for the lens's valid scalar
    # specular binding; the historical invalid material has no native F0.
    if label=='lens':
        fields['specColorTint']='.220916 .220916 .220916 1'
        # Advanced transparency requires a scalar nonmetal mask, not this
        # source's unbound RGB specular atlas. Keep zero self-emission.
        fields['specColorMap']='$black_specular'
    block(name,'material',fields);mats[label]=m;return m
material('cast',(.025,.028,.032),.48,1)
material('steel',(.32,.34,.36),.24,1)
material('rubber',(.012,.014,.016),.8)
material('reflector',(.65,.66,.68),.12,1)
material('lens',(.42,0,0),.22,0,.10)
material('lamp_off',(.12,0,0),.24)
light_profile=json.loads((ROOT/'tools/crown_alarm/light_profile.json').read_text())
material('lamp_on',(1,0,0),.22,0,1,light_profile['lamp_emission'])

def finish(ob,name,mat,group,bevel=0):
    ob.name=name;ob['alarm_group']=group;ob.data.materials.append(mats[mat])
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    if bevel:
        mod=ob.modifiers.new('Manufactured edge bevel','BEVEL');mod.width=bevel;mod.segments=2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if ob.type=='MESH':
        for p in ob.data.polygons:p.use_smooth=True
        mod=ob.modifiers.new('Weighted metal normals','WEIGHTED_NORMAL');mod.keep_sharp=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
    parts.append(ob);return ob
def cylinder(name,rad,depth,z,mat='cast',group='housing',xy=(0,0),verts=48,bevel=.16):
    bpy.ops.object.select_all(action='DESELECT');bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=rad,depth=depth,location=(xy[0],xy[1],z))
    return finish(bpy.context.object,name,mat,group,bevel)
def box(name,loc,scale,mat='cast',group='housing',bevel=.15):
    bpy.ops.object.select_all(action='DESELECT');bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=bpy.context.object;ob.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(ob,name,mat,group,bevel)
def lathe(name,profile,mat,group='housing',steps=64):
    vs=[];fs=[]
    for r,z in profile:
        for i in range(steps):
            a=math.tau*i/steps;vs.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(len(profile)-1):
        for i in range(steps):
            a=j*steps+i;b=j*steps+(i+1)%steps;fs.append((a,b,b+steps,a+steps))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT');return finish(ob,name,mat,group)

cylinder('cast foot - mounting flange',26,3,1.5)
cylinder('isolator gasket',23.5,1.4,3.7,'rubber')
cylinder('motor housing',22,5.8,7.3)
cylinder('lower machined retaining ring',23,1.4,10.9,'steel')
cylinder('lens seat seal',21.3,1,12.1,'rubber')
lathe('single ruby polycarbonate dome',[(20,12.5),(20.4,15),(20.2,34),(19.6,38),(18,41),(14,44),(8,46),(.1,46.5)],'lens')
for z in [14,16,18,20,22,24,26,28,30,32,34,36,38]:
    # Molded Fresnel ridges are geometry, retained even without a normal map.
    rad=20.35 if z<35 else 19.9
    lathe('lens optical rib '+str(z),[(rad,z-.20),(rad+.22,z),(rad,z+.20)],'lens',steps=48)
cylinder('top metal cap',9,2,46.4,'cast')
cylinder('cap crown - machined highlight',7.9,1.1,47.8,'steel')
for i in range(4):
    a=math.tau*(i+.5)/4;x=23*math.cos(a);y=23*math.sin(a)
    cylinder('flange socket bolt '+str(i),1.5,1.1,3.5,'steel',xy=(x,y),verts=6,bevel=.08)
    cylinder('black bolt socket '+str(i),.65,.1,4.08,'rubber',xy=(x,y),verts=6,bevel=0)
    a=math.tau*i/4;x=21*math.cos(a);y=21*math.sin(a)
    o=box('protective vertical strut '+str(i),(x,y,25),(1.35,2.2,25),'cast');o.rotation_euler[2]=a
    # Bent shoulder terminates on top cap; clean gap for the reflector sweep.
    start=Vector((x,y,37));end=Vector((8*math.cos(a),8*math.sin(a),46.2));d=end-start
    o=box('protective shoulder '+str(i),(start+end)/2,(1.35,2.2,d.length),'cast');o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
for i in range(16):
    a=math.tau*i/16
    o=box('motor heat sink flute '+str(i),(22*math.cos(a),22*math.sin(a),7),(1,1.1,3.5),'rubber',bevel=.05);o.rotation_euler[2]=a
# Cable gland and short armored lead terminate in the base, never float.
o=cylinder('rear cable gland',2.4,5,5,'steel',xy=(0,24),verts=12);o.rotation_euler[0]=math.pi/2
o=cylinder('rear cable plug',1.5,4,5,'rubber',xy=(0,27),verts=12);o.rotation_euler[0]=math.pi/2
# Rotor exports around its bearing: origin (0,0,26) in housing coordinates.
cylinder('motor spindle',2.5,11,18,'steel','rotor')
cylinder('rotor bearing',5,2,22,'cast','rotor')
box('rotor bracket',(0,0,24),(9,3,3),'steel','rotor')
reflector=lathe('spun parabolic reflector',[(.8,-9),(4,-8),(8,-6),(11,-2),(13,3),(13.3,4),(12.8,4.5)],'reflector','rotor',48)
# Lathe axis Z -> X, then move to lens center. The cup opens in +X.
reflector.rotation_euler[1]=math.pi/2;reflector.location.z=28
back=lathe('dark motor-driven reflector back',[(.8,-9.3),(4,-8.3),(8,-6.3),(11,-2.3),(13,2.7)],'cast','rotor',48)
back.rotation_euler[1]=math.pi/2;back.location.z=28
lamp=cylinder('red emitter tube',2.8,13,28,'lamp_off','rotor',xy=(2,0),verts=24)
cylinder('lamp lower socket',3.1,1.7,21,'steel','rotor',xy=(2,0),verts=24)
cylinder('lamp upper contact',2.9,1,35,'steel','rotor',xy=(2,0),verts=24)
ring=lathe('rotating red optic perimeter',[(11.9,4.05),(12.4,4.1),(12.7,4.2)],'lamp_off','rotor',48)
ring.rotation_euler[1]=math.pi/2;ring.location.z=28

# Explicit three LODs, generated from the authored geometry. Lens keeps its
# silhouette; insignificant bolts/vents/ribs drop at distance.
records=[]
for asset,group in [('tod_crown_alarm_housing','housing'),('tod_crown_alarm_rotor_off','rotor'),('tod_crown_alarm_rotor_on','rotor')]:
    for lod in range(3):
        mod=xmodel.Model(asset);bone=xmodel.Bone('tag_origin');bone.offset=(0,0,0);bone.matrix=[(1,0,0),(0,1,0),(0,0,1)];mod.bones=[bone]
        ids={};tri_count=0;pts=[]
        for source in parts:
            if source['alarm_group']!=group:continue
            if lod and any(s in source.name for s in ['socket','flute','optical rib']):continue
            ob=source.copy();ob.data=source.data.copy();scene.collection.objects.link(ob)
            bpy.context.view_layer.objects.active=ob
            if lod:
                d=ob.modifiers.new('Native LOD reduction','DECIMATE');d.ratio=.48 if lod==1 else .22
                bpy.ops.object.modifier_apply(modifier=d.name)
            me=ob.data;me.calc_loop_triangles();me.update();nm=ob.matrix_world.to_3x3().inverted().transposed()
            matname=me.materials[0].name
            if asset.endswith('_on') and matname.endswith('lamp_off'):matname='mtl_tod_alarm_lamp_on'
            if matname not in ids:ids[matname]=len(mod.materials);mod.materials.append(xmodel.Material(matname,'Phong',{}))
            mesh=xmodel.Mesh(source.name);pivot=Vector((0,0,26 if group=='rotor' else 0))
            mesh.verts=[xmodel.Vertex(tuple(ob.matrix_world@v.co-pivot),[(0,1.)]) for v in me.vertices]
            for v in mesh.verts:pts.append(v.offset)
            uv=me.uv_layers.active.data
            for tri in me.loop_triangles:
                # Filter converter-sized slivers after decimation, not good faces.
                p=[Vector(mesh.verts[v].offset) for v in tri.vertices];longest=max((p[1]-p[0]).length,(p[2]-p[0]).length,(p[2]-p[1]).length)
                if longest<.001 or (p[1]-p[0]).cross(p[2]-p[0]).length/longest**2<.0006:continue
                f=xmodel.Face(len(mod.meshes),ids[matname]);f.indices=[]
                for corner in [0,2,1]:
                    li=tri.loops[corner];normal=(nm@me.corner_normals[li].vector).normalized();u=uv[li].uv
                    f.indices.append(xmodel.FaceVertex(tri.vertices[corner],tuple(normal),(1,1,1,1),(u.x,1-u.y)))
                mesh.faces.append(f)
            mod.meshes.append(mesh);tri_count+=len(mesh.faces)
            bpy.data.objects.remove(ob,do_unlink=True)
        path=EXP/(asset+'_lod'+str(lod)+'.xmodel_bin');mod.WriteFile_Bin(str(path),version=7)
        records.append(dict(asset=asset,lod=lod,triangles=tri_count,meshes=len(mod.meshes),file=path.relative_to(ROOT).as_posix(),sha256=sha(path),bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]))
    block(asset,'xmodel',dict(filename='tod_crown_alarm/'+asset+'_lod0.xmodel_bin',mediumLod='tod_crown_alarm/'+asset+'_lod1.xmodel_bin',lowLod='tod_crown_alarm/'+asset+'_lod2.xmodel_bin',mediumLodDist=400,lowLodDist=1100,type='rigid',scale=1,CollisionMap='',BulletCollisionLOD='None',physicsPreset='',cullOutDiameter=0,materials=''))
(ROOT/'source_data/tod_crown_alarm.gdt').write_text('{\n'+''.join(blocks)+'}\n')

# Rotation lives on an actual pivot, matching the native script_model.
rotor=bpy.data.objects.new('ROTATING REFLECTOR - one revolution per 1.5 seconds',None);scene.collection.objects.link(rotor);rotor.location=(0,0,26)
bpy.context.view_layer.update()
for ob in parts:
    if ob['alarm_group']=='rotor':
        mw=ob.matrix_world.copy();ob.parent=rotor;ob.matrix_world=mw
rotor.rotation_euler[2]=0;rotor.keyframe_insert(data_path='rotation_euler',frame=1)
rotor.rotation_euler[2]=math.tau;rotor.keyframe_insert(data_path='rotation_euler',frame=37)
for fc in rotor.animation_data.action.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
    fc.modifiers.new('CYCLES')
scene.frame_start=1;scene.frame_end=36
def area(name,loc,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,24))-o.location).to_track_quat('-Z','Y').to_euler()
area('neutral studio key',(30,-50,100),180000,65,(1,1,1))
area('neutral rim',(-50,30,60),220000,48,(.85,.9,1))
area('front softbox',(60,-100,40),110000,40,(1,1,1))
# Floor is preview-only and is never exported.
bpy.ops.mesh.primitive_plane_add(size=1500,location=(0,0,-.15));floor=bpy.context.object;floor.name='PREVIEW floor'
m=bpy.data.materials.new('PREVIEW charcoal floor');m.diffuse_color=(.022,.025,.03,1);floor.data.materials.append(m)
d=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',d);scene.collection.objects.link(cam)
cam.location=(86,-104,74);cam.rotation_euler=(Vector((0,0,23))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=86;scene.camera=cam
scene.frame_set(1);scene.render.filepath=str(OUT/'off.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'crown_alarm.blend'))
manifest=dict(authoring='Blender MCP execute_blender_code',models=records,textures=textures,pivot_z=26,height=48.35,width=52,turn_seconds=1.5,fixture_count=30,preview_native_verified=False)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('ALARM_AUTHORED',json.dumps({'models':len(records),'lod0_triangles':sum(r['triangles'] for r in records if r['lod']==0),'parts':len(parts),'blend':str(OUT/'crown_alarm.blend')}))
