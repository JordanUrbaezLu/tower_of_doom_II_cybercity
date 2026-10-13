"""Execute through Blender MCP (tools/alarm_button/mcp_call.py). Author/export THE ALARM BUTTON, then save its studio.

User 2026-09-28: "remove [the alarm switch] and replace [it] with a red button on top of a stand in the centre of
the crown. Then players will press the button" + "use blender mcp for red button".

Three native models, one bone each (tag_origin), three LODs each:
  tod_alarm_button_stand   the waist-high stand: cast base plate + bolts, flared column with steel bands, round
                           console with a yellow/black hazard collar and a steel bezel. Origin = the floor.
  tod_alarm_button_cap_on  the red mushroom button, GLOWING (emissive) - armed, waiting for a press.
  tod_alarm_button_cap_off the same mesh, dark red - pressed. Cap origin = the bezel top (CAP_Z above the floor),
                           so the script spawns it at stand origin + (0,0,CAP_Z) and presses it with MoveZ.
Units are BO3 inches. Keep CAP_Z / STAND_R / CONSOLE_Z in LOCKSTEP with _tod_fall.gsc TOD_FALL_BUTTON_* and the
generator's alarm button clip (tools/gen_tower_map.js).
"""
import bpy, math, json, pathlib, sys, hashlib
import numpy as np
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
OUT=ROOT/'art/alarm_button'; OUT.mkdir(parents=True,exist_ok=True)
EXP=ROOT/'model_export/tod_alarm_button'; EXP.mkdir(parents=True,exist_ok=True)
TEX=EXP/'_images'; TEX.mkdir(exist_ok=True)
CAP_Z=38.2        # bezel top = the cap's pivot
CONSOLE_Z=37.0    # console top surface
STAND_R=12.0      # base plate radius (the clip box is +-10)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
for im in list(bpy.data.images):
    if im.name.startswith('i_tod_abtn_'):bpy.data.images.remove(im)
scene=bpy.context.scene; scene.name='Alarm button - authored native asset'
scene.render.engine='CYCLES'; scene.cycles.samples=48; scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.05,.055,.07,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.2
blocks=[];textures={};mats={};parts=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def block(name,kind,fields):
    blocks.append('\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v)+'"\n' for k,v in fields.items())+'\t}\n')
def texture(label,color,rough,metal,seed):
    # The crown alarm's recipe: deterministic patina maps (grain, brushing, scratches), 512 square (a multiple of 4).
    n=512;rng=np.random.default_rng(seed);y,x=np.mgrid[:n,:n]
    grain=rng.normal(0,.025,(n,n));brush=np.sin(y*.47)*.035
    scratch=np.zeros((n,n))
    for i in range(70):
        a,b=rng.integers(0,n,2);length=int(rng.integers(8,80))
        scratch[a,min(b,n-1):min(b+length,n)]=rng.uniform(.04,.12)
    noise=grain+brush+scratch if metal else grain*.35
    images={}
    for suffix in ['c','g','s','n']:
        a=np.ones((n,n,4),dtype=np.float32)
        if suffix=='c':a[:,:,:3]=np.clip(np.array(color)[None,None,:]*(1+noise[:,:,None]),0,1)
        elif suffix=='g':a[:,:,:3]=np.clip(1-rough+noise[:,:,None]*.3,0,1)
        elif suffix=='s':a[:,:,:3]=.6 if metal else .04
        else:
            a[:,:,0]=.5+grain*.15;a[:,:,1]=.5+brush*.08;a[:,:,2]=1
        name='i_tod_abtn_'+label+'_'+suffix
        im=bpy.data.images.new(name,width=n,height=n,alpha=True)
        if suffix in ['g','n']:im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(a.ravel());im.filepath_raw=str(TEX/(name+'.png'));im.file_format='PNG';im.save();im.pack()
        images[suffix]=im;textures[name+'.png']=sha(TEX/(name+'.png'))
        f=dict(baseImage='model_export/tod_alarm_button/_images/'+name+'.png',imageType='Texture',type='image',semantic={'c':'diffuseMap','g':'glossMap','s':'specularMap','n':'normalMap'}[suffix],streamable=1,compressionMethod='compressed high color' if suffix in ['c','s'] else 'compressed')
        if suffix in ['c','s']:f['coreSemantic']='sRGB3chAlpha'
        block(name,'image',f)
    return images
def material(label,color,rough=.4,metal=0,emission=0,seed=7):
    images=texture(label,color,rough,metal,seed)
    name='mtl_tod_abtn_'+label;m=bpy.data.materials.new(name);m.use_nodes=True;m.use_fake_user=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=images['c'];m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if emission:
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=emission*.25
    fields=dict(surfaceType='metal' if metal else 'plastic',template='material.template',materialCategory='Geometry Advanced',materialType='lit_emissive_advanced_fullspec',colorMap=images['c'].name,normalMap=images['n'].name,cosinePowerMap=images['g'].name,specColorMap=images['s'].name,specMapEnable=1,specColorTint='1 1 1 1',colorMap00=images['c'].name,colorTint='1 1 1 1',colorTint1='1 1 1 1',scaleRGB=emission,emissiveIncompetence=1,emissiveFalloff=0,normalHeightScale=1,glossRangeMin=0,glossRangeMax=8,specAmount=.5,reflectionProbeAmount=.3,textureAtlasRowCount=1,textureAtlasColumnCount=1,usage='<not in editor>')
    block(name,'material',fields);mats[label]=m;return m
material('cast',(.03,.033,.038),.5,1,seed=11)
material('steel',(.34,.36,.38),.24,1,seed=12)
material('rubber',(.012,.013,.015),.82,seed=13)
material('hazard',(.86,.58,.02),.45,seed=14)
material('red_off',(.22,.01,.01),.3,seed=15)
material('red_on',(1,.03,.02),.25,0,20,seed=16)

def finish(ob,name,mat,group,bevel=0):
    ob.name=name;ob['btn_group']=group;ob.data.materials.append(mats[mat])
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    if bevel:
        mod=ob.modifiers.new('Manufactured edge bevel','BEVEL');mod.width=bevel;mod.segments=2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in ob.data.polygons:p.use_smooth=True
    mod=ob.modifiers.new('Weighted metal normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
    parts.append(ob);return ob
def cylinder(name,rad,depth,z,mat='cast',group='stand',xy=(0,0),verts=48,bevel=.2):
    bpy.ops.object.select_all(action='DESELECT');bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=rad,depth=depth,location=(xy[0],xy[1],z))
    return finish(bpy.context.object,name,mat,group,bevel)
def lathe(name,profile,mat,group='stand',steps=64):
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
def wedge(name,r0,r1,a0,a1,z0,z1,mat,steps=6):
    # One closed annular sector (the hazard collar's stripes are real geometry, not a texture).
    vs=[];fs=[]
    for i in range(steps+1):
        a=a0+(a1-a0)*i/steps;c,s=math.cos(a),math.sin(a)
        vs+= [(r0*c,r0*s,z0),(r1*c,r1*s,z0),(r1*c,r1*s,z1),(r0*c,r0*s,z1)]
    for i in range(steps):
        b=i*4;n=b+4
        fs+= [(b+3,b+2,n+2,n+3),(b+1,b+2,n+2,n+1)[::-1],(b,b+3,n+3,n),(b,n,n+1,b+1)]
    fs+= [(0,1,2,3),(steps*4+3,steps*4+2,steps*4+1,steps*4)]
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.validate()
    ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT');return finish(ob,name,mat,'stand')

# ---- THE STAND ----
cylinder('base rubber foot',STAND_R+.4,.6,.3,'rubber',bevel=.1)
cylinder('cast base plate',STAND_R,2.2,1.7,'cast',bevel=.35)
cylinder('base plate steel lip',STAND_R-1.6,.5,3.05,'steel',bevel=.1)
for i in range(6):
    a=math.tau*(i+.5)/6;x=(STAND_R-2.3)*math.cos(a);y=(STAND_R-2.3)*math.sin(a)
    cylinder('anchor bolt '+str(i),.9,.9,3.2,'steel',xy=(x,y),verts=6,bevel=.08)
lathe('flared cast column',[(6.4,3.0),(5.9,5.5),(5.2,9),(4.9,14),(4.8,29),(5.3,32),(6.6,34),(8.2,35.4)],'cast')
cylinder('lower steel band',5.35,1.0,8.2,'steel',bevel=.1)
cylinder('upper steel band',5.05,1.0,28.0,'steel',bevel=.1)
cylinder('round console',9.0,1.8,CONSOLE_Z-.9,'cast',bevel=.35)
lathe('console steel rim',[(8.9,CONSOLE_Z-.2),(9.35,CONSOLE_Z),(9.35,CONSOLE_Z+.3),(8.8,CONSOLE_Z+.45)],'steel')
for i in range(16):
    a0=math.tau*i/16;a1=math.tau*(i+1)/16
    wedge('hazard collar stripe '+str(i),4.7,8.4,a0,a1,CONSOLE_Z,CONSOLE_Z+.3,'hazard' if i%2==0 else 'rubber')
lathe('steel button bezel',[(4.8,CONSOLE_Z),(4.7,CONSOLE_Z+.6),(4.2,CAP_Z),(3.3,CAP_Z),(3.1,CONSOLE_Z+.5)],'steel')
for i in range(4):
    a=math.tau*(i+.5)/4
    cylinder('bezel screw '+str(i),.35,.3,CONSOLE_Z+.5,'rubber',xy=(4.45*math.cos(a),4.45*math.sin(a)),verts=8,bevel=0)

# ---- THE CAP (a mushroom-head emergency button; the red plunger rides in the bezel) ----
cylinder('red plunger',2.9,1.8,CAP_Z+.5,'red_off','cap',verts=48,bevel=.15)
lathe('red mushroom head',[(2.8,CAP_Z+1.2),(4.0,CAP_Z+1.4),(4.15,CAP_Z+2.0),(3.95,CAP_Z+2.75),(3.3,CAP_Z+3.35),(2.3,CAP_Z+3.75),(1.1,CAP_Z+3.92),(.05,CAP_Z+3.95)],'red_off','cap',64)

records=[]
for asset,group,pivot in [('tod_alarm_button_stand','stand',0),('tod_alarm_button_cap_on','cap',CAP_Z),('tod_alarm_button_cap_off','cap',CAP_Z)]:
    for lod in range(3):
        mod=xmodel.Model(asset);bone=xmodel.Bone('tag_origin');bone.offset=(0,0,0);bone.matrix=[(1,0,0),(0,1,0),(0,0,1)];mod.bones=[bone]
        ids={};tri_count=0;pts=[]
        for source in parts:
            if source['btn_group']!=group:continue
            if lod and any(s in source.name for s in ['bolt','screw','cable','lip']):continue
            ob=source.copy();ob.data=source.data.copy();scene.collection.objects.link(ob)
            bpy.context.view_layer.objects.active=ob
            if lod:
                d=ob.modifiers.new('Native LOD reduction','DECIMATE');d.ratio=.5 if lod==1 else .25
                bpy.ops.object.modifier_apply(modifier=d.name)
            me=ob.data;me.calc_loop_triangles();me.update();nm=ob.matrix_world.to_3x3().inverted().transposed()
            matname=me.materials[0].name
            if asset.endswith('_on') and matname.endswith('red_off'):matname='mtl_tod_abtn_red_on'
            if matname not in ids:ids[matname]=len(mod.materials);mod.materials.append(xmodel.Material(matname,'Phong',{}))
            mesh=xmodel.Mesh(source.name);pv=Vector((0,0,pivot))
            mesh.verts=[xmodel.Vertex(tuple(ob.matrix_world@v.co-pv),[(0,1.)]) for v in me.vertices]
            for v in mesh.verts:pts.append(v.offset)
            uv=me.uv_layers.active.data
            for tri in me.loop_triangles:
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
    block(asset,'xmodel',dict(filename='tod_alarm_button/'+asset+'_lod0.xmodel_bin',mediumLod='tod_alarm_button/'+asset+'_lod1.xmodel_bin',lowLod='tod_alarm_button/'+asset+'_lod2.xmodel_bin',mediumLodDist=400,lowLodDist=1100,type='rigid',scale=1,CollisionMap='',BulletCollisionLOD='None',physicsPreset='',cullOutDiameter=0,materials=''))
gdt=ROOT/'source_data/tod_alarm_button.gdt'
gdt.write_text('{\n'+''.join(blocks)+'}\n')

# ---- preview (floor + lights + camera are never exported) ----
def area(name,loc,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,30))-o.location).to_track_quat('-Z','Y').to_euler()
area('neutral studio key',(40,-60,110),160000,60,(1,1,1))
area('cool rim',(-60,40,70),140000,45,(.8,.88,1))
bpy.ops.mesh.primitive_plane_add(size=1500,location=(0,0,-.05));floor=bpy.context.object;floor.name='PREVIEW floor'
m=bpy.data.materials.new('PREVIEW dais floor');m.diffuse_color=(.03,.03,.04,1);floor.data.materials.append(m)
d=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',d);scene.collection.objects.link(cam)
cam.location=(52,-70,66);cam.rotation_euler=(Vector((0,0,24))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=54;scene.camera=cam
renders={}
for state in ['on','off']:
    for ob in parts:
        if ob['btn_group']=='cap':ob.data.materials[0]=mats['red_on' if state=='on' else 'red_off']
    scene.render.filepath=str(OUT/(state+'.png'));bpy.ops.render.render(write_still=True);renders[state]=str(OUT/(state+'.png'))
for ob in parts:
    if ob['btn_group']=='cap':ob.data.materials[0]=mats['red_on']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'alarm_button.blend'))
manifest=dict(authoring='Blender MCP execute_blender_code (tools/alarm_button/mcp_call.py, port 9887)',models=records,textures=textures,gdt_sha256=sha(gdt),cap_z=CAP_Z,console_z=CONSOLE_Z,stand_radius=STAND_R,height=CAP_Z+3.95,renders=renders,preview_native_verified=False)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('ALARM_BUTTON_AUTHORED',json.dumps({'models':len(records),'lod0_triangles':{r['asset']:r['triangles'] for r in records if r['lod']==0},'parts':len(parts),'blend':str(OUT/'alarm_button.blend')}))
