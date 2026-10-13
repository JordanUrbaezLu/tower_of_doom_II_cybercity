"""Actual Blender MCP: staged hero-detail pass, safe beside a native build.

The frozen input and staged outputs live under art, never in live build inputs.
"""
import bpy, pathlib, shutil, math, json, re
import numpy as np
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'art/necro_staff'; STAGE=BASE/'detail_pass'; OUT=STAGE/'models'
STAGE.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
if not (STAGE/'input.blend').exists():
    shutil.copyfile(BASE/'staff_master.blend',STAGE/'input.blend')
    shutil.copytree(ROOT/'model_export/tod_necro_staff',STAGE/'input_maps',dirs_exist_ok=True)
shutil.copytree(STAGE/'input_maps',OUT,dirs_exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(STAGE/'input.blend'))
scene=bpy.context.scene;window=bpy.context.window_manager.windows[0];window.scene=scene
area=next(a for a in window.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
for im in bpy.data.images:
    p=pathlib.Path(bpy.path.abspath(im.filepath))
    if (OUT/p.name).exists():im.filepath=str(OUT/p.name);im.reload()
gdt=(OUT/'materials.gdtpart').read_text()
def block(name,kind,fields):
    return '\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v)+'"\n' for k,v in fields.items())+'\t}\n'
def fields(name):
    body=re.search(r'"'+re.escape(name)+r'"\s*\([^)]*\)\s*\{([^}]+)',gdt).group(1)
    return dict(re.findall(r'"([^"\n]+)"\s*"([^"\n]*)"',body))
def image(name,data,semantic):
    global gdt
    if data.ndim==2:data=np.repeat(data[:,:,None],3,axis=2)
    h,w=data.shape[:2];data=np.concatenate([data,np.ones((h,w,1))],axis=2).astype(np.float32)
    im=bpy.data.images.new(name,width=w,height=h,alpha=True)
    im.colorspace_settings.name='sRGB' if semantic=='diffuseMap' else 'Non-Color'
    im.pixels.foreach_set(data.ravel());im.filepath_raw=str(OUT/(name+'.png'));im.file_format='PNG';im.save()
    gdt+=block(name,'image',dict(baseImage='model_export/tod_necro_staff/'+name+'.png',imageType='Texture',semantic=semantic,streamable=0,compressionMethod='compressed high color' if semantic=='diffuseMap' else 'compressed',coreSemantic='sRGB3chAlpha' if semantic=='diffuseMap' else ''))
    return im
# Dark leather has a genuinely different albedo, gloss and tangent response.
N=2048;yy,xx=np.mgrid[0:N,0:N].astype(np.float32)/N;rng=np.random.default_rng(9273)
grain=rng.random((N,N),dtype=np.float32)
creases=np.exp(-(np.sin(xx*math.pi*37+.6*np.sin(yy*math.pi*19))/.18)**2)
height=.00015*grain-.0015*creases
dy,dx=np.gradient(height,1/N);normal=np.stack([-dx*.16,dy*.16,np.ones_like(xx)],axis=2);normal/=np.linalg.norm(normal,axis=2,keepdims=True)
value=.025+.013*grain-.015*creases
maps={'c':image('i_tod_necro_leather_c',np.stack([value*1.1,value*.82,value*.66],axis=2),'diffuseMap'),
      'n':image('i_tod_necro_leather_n',normal*.5+.5,'normalMap'),
      'g':image('i_tod_necro_leather_g',.20+.13*grain-.12*creases,'glossMap'),
      's':image('i_tod_necro_leather_s',np.full((N,N,3),.025),'specularMap')}
f=fields('mtl_tod_necro_staff_bone');f.update(colorMap=maps['c'].name,normalMap=maps['n'].name,cosinePowerMap=maps['g'].name,specColorMap=maps['s'].name,colorMap00=maps['c'].name,scaleRGB=0)
gdt+=block('mtl_tod_necro_staff_leather','material',f)
leather=bpy.data.materials.new('mtl_tod_necro_staff_leather');leather.use_nodes=True
n=leather.node_tree.nodes;l=leather.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.72
tex=n.new('ShaderNodeTexImage');tex.image=maps['c'];l.new(tex.outputs['Color'],bs.inputs['Base Color'])
tex=n.new('ShaderNodeTexImage');tex.image=maps['n']
sep=n.new('ShaderNodeSeparateXYZ');com=n.new('ShaderNodeCombineXYZ');sub=n.new('ShaderNodeMath');sub.operation='SUBTRACT';sub.inputs[0].default_value=1
l.new(tex.outputs[0],sep.inputs[0]);l.new(sep.outputs[0],com.inputs[0]);l.new(sep.outputs[1],sub.inputs[1]);l.new(sub.outputs[0],com.inputs[1]);l.new(sep.outputs[2],com.inputs[2])
nm=n.new('ShaderNodeNormalMap');l.new(com.outputs[0],nm.inputs['Color']);l.new(nm.outputs[0],bs.inputs['Normal'])
iron=bpy.data.materials['mtl_tod_necro_staff_forge']
# A muted crevice material for very fine natural sutures; no glowing cracks.
f=fields('mtl_tod_necro_staff_bone');f['colorTint']='0.24 0.21 0.17 1'
gdt+=block('mtl_tod_necro_staff_crevice','material',f)
crevice=bpy.data.materials['mtl_tod_necro_staff_bone'].copy();crevice.name='mtl_tod_necro_staff_crevice'
bs=crevice.node_tree.nodes.get('Principled BSDF');socket=bs.inputs['Base Color'].links[0].from_socket
mix=crevice.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.047,.036,.025,1)
crevice.node_tree.links.new(socket,mix.inputs[1]);crevice.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
def finish(ob,name,tier,mat):
    ob.name=name;ob['tier']=tier;ob.data.materials.clear();ob.data.materials.append(mat)
    for other in scene.objects:other.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active=ob
    for p in ob.data.polygons:p.use_smooth=True
    with bpy.context.temp_override(window=window,area=area,region=region,object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
    return ob
def tubes(name,paths,radius,tier,mat):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=radius;d.bevel_resolution=1;d.use_fill_caps=True
    for coords in paths:
        if len(coords)<2:continue
        s=d.splines.new('POLY');s.points.add(len(coords)-1)
        for p,c in zip(s.points,coords):p.co=(*c,1)
    ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob)
    for other in scene.objects:other.select_set(False)
    ob.select_set(True);bpy.context.view_layer.objects.active=ob
    with bpy.context.temp_override(window=window,area=area,region=region,object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.convert(target='MESH')
    return finish(ob,name,tier,mat)
def stud(name,pos,radius,tier):
    with bpy.context.temp_override(window=window,area=area,region=region):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=radius,location=pos)
    return finish(bpy.context.view_layer.objects.active,name,tier,iron)
def projected(ob,coords,inset=0):
    out=[]
    for x,z in coords:
        hit,loc,n,idx=ob.ray_cast(Vector((x,-20,z)),Vector((0,1,0)))
        if hit:out.append(tuple(loc+n*inset))
    return out
for ob in list(scene.objects):
    if ob.name.startswith(('Fine grip ring','Incised forehead spiral','Cranial suture inlay')):bpy.data.objects.remove(ob,do_unlink=True)
for tier in [2,3]:
    for center in [-11.4,0]:
        # Spaced spiral ribbons retain the same hand-contact radius. A small
        # seam avoids coplanar overlap and the resulting saw-toothed artifacts.
        verts=[];faces=[];steps=320
        for i in range(steps+1):
            t=i/steps;a=t*math.pi*2*12;z=center-2.1+t*4.2
            for dz in [-.15,.15]:verts.append((.875*math.cos(a),.875*math.sin(a),z+dz))
        for i in range(steps):faces.append((2*i,2*i+1,2*i+3,2*i+2))
        d=bpy.data.meshes.new('Spiral hide wrap');d.from_pydata(verts,[],faces)
        ob=bpy.data.objects.new('Leather grip T'+str(tier),d);scene.collection.objects.link(ob);finish(ob,ob.name,tier,leather)
        # Continuous ribbon coordinates, replacing the generic projection.
        uv=ob.data.uv_layers.active.data
        for poly in ob.data.polygons:
            for li in poly.loop_indices:
                vi=ob.data.loops[li].vertex_index;uv[li].uv=(vi%2,vi//2/steps*6)
        mod=ob.modifiers.new('Hide thickness','SOLIDIFY');mod.thickness=.035
        with bpy.context.temp_override(window=window,area=area,region=region,object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.modifier_apply(modifier=mod.name)
        for i in range(8):
            z=center-1.8+i*.5;tubes('Grip stitches T'+str(tier),[[(-.16,-.92,z-.08),(.16,-.92,z+.08)]],.026,tier,iron)
    for a in np.linspace(0,math.pi*2,8 if tier==3 else 6,endpoint=False):stud('Socket fastening T'+str(tier),(1.03*math.cos(a),1.03*math.sin(a),27.2),.10,tier)
    skull=next(o for o in scene.objects if o.name.startswith('Carved human skull') and o['tier']==tier)
    # Anatomical sutures follow the skull surface; avoid the eyes and teeth.
    paths=[]
    paths.append(projected(skull,[(.055*math.sin(i*2.1),34.8+i*.085) for i in range(32)],-.008))
    for side in [-1,1]:
        paths.append(projected(skull,[(side*(.2+i*.09),36.2+.18*math.sin(i*.9)) for i in range(24)],-.009))
    tubes('Fine cranial sutures T'+str(tier),paths,.026,tier,crevice)
    if tier==3:
        for side in [-1,1]:
            coords=[]
            for t in np.linspace(0,math.pi*3.3,100):
                r=.12+.075*t;coords.append((side*(1.05+r*math.cos(t)),35.4+r*math.sin(t)))
            tubes('Ritual skull inlay', [projected(skull,coords,-.009)],.044,tier,crevice)
        for a in np.linspace(0,math.pi*2,16,endpoint=False):stud('Halo rivet',(6.05*math.cos(a),.45,33+6.05*math.sin(a)),.12,tier)
# Actual recessed channels on the blades, with their own bevelled cut edges.
cut_count=0
for ob in list(scene.objects):
    if not ob.name.startswith(('Radial forged spike','Long central spear','Split upper shard','Forked neck')):continue
    points=np.array([(v.co.x,v.co.z) for v in ob.data.vertices]);center=points.mean(axis=0)
    eigen,axes=np.linalg.eigh(np.cov((points-center).T));axis=axes[:,np.argmax(eigen)];side=np.array([-axis[1],axis[0]])
    projections=(points-center)@axis;lo,hi=projections.min(),projections.max();width=np.max(abs((points-center)@side))
    paths=[]
    for sign in [-1,1]:
        coords=[]
        for t in np.linspace(.22,.79,38):
            p=center+axis*(lo+(hi-lo)*t)+side*sign*width*(.13+.18*math.sin((t-.22)/.57*math.pi))
            coords.append(tuple(p))
        path=projected(ob,coords,.012)
        if len(path)>3:paths.append(path)
    if not paths:continue
    cutter=tubes('Temporary engraving cutter',paths,.055,3,iron)
    mod=ob.modifiers.new('Recessed blade engraving','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    with bpy.context.temp_override(window=window,area=area,region=region,object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True);cut_count+=1
    mod=ob.modifiers.new('Engraving edge bevel','BEVEL');mod.width=.014;mod.segments=2
    with bpy.context.temp_override(window=window,area=area,region=region,object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.modifier_apply(modifier=mod.name)
    mod=ob.modifiers.new('Weighted forged normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    with bpy.context.temp_override(window=window,area=area,region=region,object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.modifier_apply(modifier=mod.name)
scene['detail_pass_version']='hero_detail_3'
(OUT/'materials.gdtpart').write_text(gdt)
bpy.ops.wm.save_as_mainfile(filepath=str(STAGE/'staff_master.blend'))
(STAGE/'detail.json').write_text(json.dumps(dict(recessed_blades=cut_count,leather_grips=4,material_images=19,skull_detail='surface-fitted sutures and tier-3 ritual inlay',native_visual_verified=False),indent=2))
print('HERO DETAIL STAGED',cut_count,'recessed blades; four leather wraps; rivets, sutures and ritual inlay')
