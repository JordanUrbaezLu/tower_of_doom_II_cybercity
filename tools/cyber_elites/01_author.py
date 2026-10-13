"""Run in the dedicated Blender MCP studio. Native donor rig/UVs remain intact."""
import sys, pathlib, json, copy, re, hashlib, math
import bpy
import numpy as np
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import asset, native_path, xmodel, MT
OUT=ROOT/'art/cyber_elites'; OUT.mkdir(parents=True,exist_ok=True)
EXPORT=ROOT/'model_export/tod_cyber_elites'; EXPORT.mkdir(parents=True,exist_ok=True)
TEX=EXPORT/'images'; TEX.mkdir(exist_ok=True)
blocks=[]; records=[]; texture_records=[]
def block(name,kind,fields):
    def val(v):
        if isinstance(v,float) and v.is_integer(): return str(int(v))
        return str(v).replace('"','\\"').replace('\r','\\r').replace('\n','\\n')
    blocks.append('\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+val(v)+'"\n' for k,v in fields.items() if v is not None)+'\t}\n')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def image_path(name): return native_path('',asset('image',name)['baseImage'])
def recolor(name,outname,mode):
    source=image_path(name); im=bpy.data.images.load(str(source),check_existing=False)
    a=np.empty(len(im.pixels),dtype=np.float32); im.pixels.foreach_get(a); a=a.reshape((-1,4))
    y=a[:,:3] @ np.array([.2126,.7152,.0722],dtype=np.float32)
    if mode=='black': a[:,:3]=(0.001+np.sqrt(y)*.008)[:,None]
    elif mode=='red':
        a[:,0]=np.max(a[:,:3],axis=1); a[:,1:3]=0
    else: a[:,:3]=y[:,None]
    im.pixels.foreach_set(a.ravel()); im.filepath_raw=str(TEX/(outname+'.png')); im.file_format='PNG'; im.save()
    fields=asset('image',name); fields['baseImage']='model_export/tod_cyber_elites/images/'+outname+'.png'
    block(outname,'image',fields)
    texture_records.append(dict(source=str(source),source_sha256=digest(source),output=str(pathlib.Path(im.filepath_raw).relative_to(ROOT)),mode=mode,sha256=digest(pathlib.Path(im.filepath_raw))))
    return im

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for stale in list(bpy.data.materials): bpy.data.materials.remove(stale)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=10
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.10,.10,.10,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
materials={}
def preview_mat(name,fields,image=None,red=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=.62
    tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=image or bpy.data.images.load(str(image_path(fields['colorMap'])),check_existing=True)
    tint=m.node_tree.nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
    tint.inputs[2].default_value=tuple(float(x) for x in fields.get('colorTint','1 1 1 1').split())
    m.node_tree.links.new(tx.outputs['Color'],tint.inputs[1]);m.node_tree.links.new(tint.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Specular IOR Level'].default_value=.15
    if fields.get('normalMap') and not fields['normalMap'].startswith('$'):
        nt=m.node_tree.nodes.new('ShaderNodeTexImage');nt.image=bpy.data.images.load(str(image_path(fields['normalMap'])),check_existing=True);nt.image.colorspace_settings.name='Non-Color'
        n=m.node_tree.nodes.new('ShaderNodeNormalMap');m.node_tree.links.new(nt.outputs['Color'],n.inputs['Color']);m.node_tree.links.new(n.outputs['Normal'],bs.inputs['Normal'])
    if red:
        m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=5
    materials[name]=m;return m

# Clone every Hellbound charcoal body, head and gib asset under this map's names.
donor_gdt=ROOT.parent/'tower_of_doom_II_hellbound/source_data/hb_charred.gdt'
entries=re.findall(r'\t"([^"\n]+)" \( "([^"\n]+)\.gdf" \)',donor_gdt.read_text())
mapping={name:name.replace('hb_charred','tod_charcoal') for name,kind in entries}
char_models={}
for old,kind in entries:
    name=mapping[old]; fields=asset(kind,old)
    fields={k:mapping.get(v,v) if isinstance(v,str) else v for k,v in fields.items()}
    # The donor swaps these three retained-body / detached-piece references.
    # Keep every source mesh, but bind each to its actual anatomical role.
    if kind=='character':
        fields['legDmg2']='tod_charcoal_c_zom_dlc3_zombie_sentinel_g_rlegoff'
    if kind=='gibcharacterdef':
        fields['leftarm_gibmodel']='tod_charcoal_c_zom_dlc3_zombie_sentinel_s_larmspawn'
        fields['leftleg_gibmodel']='tod_charcoal_c_zom_dlc3_zombie_sentinel_s_llegspawn'
    if kind=='material':
        red='eyes' in old; image_name='i_'+name
        im=recolor(fields['colorMap'],image_name,'red' if red else 'gray')
        fields['colorMap']=image_name
        if red:
            fields.update(colorMap00=image_name,colorTint='1 0 0 1',colorTint1='1 0 0 1',scaleRGB=16)
        else: fields.update(colorTint='0.45 0.45 0.45 1',specColorTint='0.12 0.12 0.12 1')
        preview_mat(name,fields,im,red)
    if kind=='xmodel':
        source=native_path('model_export',fields['filename']);model=xmodel.Model();model.LoadFile_Bin(str(source),split_meshes=True)
        for m in model.materials: m.name=mapping[m.name]
        dst=EXPORT/(name+'.XMODEL_BIN');model.WriteFile_Bin(str(dst))
        check=xmodel.Model();check.LoadFile_Bin(str(dst),split_meshes=True)
        assert [(b.name,b.parent,b.offset,b.matrix) for b in model.bones]==[(b.name,b.parent,b.offset,b.matrix) for b in check.bones]
        assert [[(v.offset,v.weights) for v in m.verts] for m in check.meshes]==[[(v.offset,v.weights) for v in m.verts] for m in model.meshes]
        assert sum(len(m.faces) for m in check.meshes)==sum(len(m.faces) for m in model.meshes)
        fields['filename']='tod_cyber_elites/'+dst.name
        char_models[name]=model
        records.append(dict(name=name,source=str(source),source_sha256=digest(source),output=str(dst.relative_to(ROOT)),sha256=digest(dst),faces=sum(len(m.faces) for m in model.meshes)))
    block(name,kind,fields)

source=native_path('model_export',asset('xmodel','hb_bo6_doppelghast')['filename'])
donor=xmodel.Model();donor.LoadFile_Bin(str(source),split_meshes=True)
model=copy.deepcopy(donor)
for i,m in enumerate(model.materials):
    fields=asset('material',m.name)
    if i<3:
        name='mtl_tod_doppelgast_black_'+str(i);imname='i_tod_doppelgast_black_'+str(i)
        im=recolor(fields['colorMap'],imname,'black');fields['colorMap']=imname
        fields['colorTint']='1 1 1 1';fields['specColorTint']='0.08 0.08 0.08 1'
        block(name,'material',fields);m.name=name;preview_mat(name,fields,im)
    else: preview_mat(m.name,fields)

# Delete the donor's organic legs. The hip cuffs bridge the cut to machinery.
lower=model.meshes[1]; kept=[f for f in lower.faces if all(lower.verts[c.vertex].offset[2]>=51.0 for c in f.indices)]
used=sorted({c.vertex for f in kept for c in f.indices});remap={v:i for i,v in enumerate(used)}
lower.verts=[lower.verts[i] for i in used];lower.faces=kept
for f in kept:
    for c in f.indices:c.vertex=remap[c.vertex]

arm=bpy.data.armatures.new('Hellbound_original_skeleton');rig=bpy.data.objects.new('Doppelgast_original_animation_rig',arm);scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for b in model.bones:
    eb=arm.edit_bones.new(b.name);eb.head=b.offset;eb.tail=Vector(b.offset)+Vector(b.matrix[1]);eb.align_roll(Vector(b.matrix[2]))
    if b.parent>=0:eb.parent=arm.edit_bones[model.bones[b.parent].name]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
def import_model(mod,label,offset=(0,0,0),parent=None):
    objects=[]
    for mi,sm in enumerate(mod.meshes):
        me=bpy.data.meshes.new(label+str(mi));me.from_pydata([v.offset for v in sm.verts],[],[[f.indices[k].vertex for k in (0,2,1)] for f in sm.faces]);me.update()
        ob=bpy.data.objects.new(me.name,me);scene.collection.objects.link(ob);ob.location=offset
        for m in mod.materials:me.materials.append(materials[m.name])
        uv=me.uv_layers.new(name='Native_UV');normals=[]
        for poly,f in zip(me.polygons,sm.faces):
            poly.material_index=f.material_id;poly.use_smooth=True
            for li,k in zip(poly.loop_indices,(0,2,1)):
                c=f.indices[k];uv.data[li].uv=(c.uv[0],1-c.uv[1]);normals.append(c.normal)
        me.normals_split_custom_set(normals)
        if parent:
            for b in mod.bones:ob.vertex_groups.new(name=b.name)
            for vi,v in enumerate(sm.verts):
                for bi,w in v.weights:ob.vertex_groups[bi].add([vi],w,'REPLACE')
            ob.parent=parent;ob.modifiers.new('Native weights','ARMATURE').object=parent
        objects.append(ob)
    return objects
import_model(model,'Doppelgast_black_',parent=rig)

kit=[];bones={b.name:i for i,b in enumerate(model.bones)}
for name,color,rough,spec in [('shell',.022,.42,.30),('piston',.052,.28,.60),('rubber',.008,.83,.06)]:
    matname='mtl_tod_doppelgast_robot_'+name
    fields=asset('material',donor.materials[0].name)
    fields.update(colorMap='$white',normalMap='$identitynormalmap',cosinePowerMap='$black_color',occlusionMap='$white_ao',colorTint=f'{color} {color} {color} 1',specColorTint=f'{spec} {spec} {spec} 1')
    block(matname,'material',fields)
    bm=bpy.data.materials.new(matname);bm.use_nodes=True;bs=bm.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(color,color,color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=.7 if name!='rubber' else .05
    materials[matname]=bm;model.materials.append(xmodel.Material(matname,'Phong',{}))
def finish(ob,name,bone,mat,bevel=.12):
    ob.name=name;ob.data.materials.append(materials['mtl_tod_doppelgast_robot_'+mat]);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        be=ob.modifiers.new('Machined edge radius','BEVEL');be.width=bevel;be.segments=2;bpy.ops.object.modifier_apply(modifier=be.name)
        wn=ob.modifiers.new('Machined normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=wn.name)
    ob['native_bone']=bone;ob.vertex_groups.new(name=bone).add(list(range(len(ob.data.vertices))),1,'REPLACE')
    ob.parent=rig;ob.modifiers.new('Original animation attachment','ARMATURE').object=rig;kit.append(ob);return ob
def cyl(name,a,b,r,bone,mat='shell',vertices=16):
    a,b=Vector(a),Vector(b);bpy.ops.object.select_all(action='DESELECT');bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=(b-a).length,location=(a+b)/2)
    ob=bpy.context.object;ob.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return finish(ob,name,bone,mat,min(.1,r*.12))
def box(name,pos,dims,bone,mat='shell',direction=None):
    bpy.ops.object.select_all(action='DESELECT');bpy.ops.mesh.primitive_cube_add(size=1,location=pos);ob=bpy.context.object;ob.dimensions=dims
    if direction is not None:ob.rotation_euler=Vector(direction).to_track_quat('Z','Y').to_euler()
    return finish(ob,name,bone,mat,.17)
for side,sign in [('le',1),('ri',-1)]:
    def pos(j):return Vector(model.bones[bones['j_'+j+'_'+side]].offset)
    hip,knee,ankle,ball,toe=[pos(j) for j in ['hip','knee','ankle','ball','toeend']]
    hb,kb,ab,fb=['j_'+j+'_'+side for j in ['hip','knee','ankle','ball']]
    outward=Vector((0,sign,0))
    for label,p,r,width,bone in [('hip',hip,4.25,7,hb),('knee',knee,3.8,7,kb),('ankle',ankle,2.7,6,ab)]:
        cyl(side+' '+label+' hinge',p-outward*width/2,p+outward*width/2,r,bone)
        for s in [-1,1]:
            center=p+outward*s*(width/2+.3);cyl(side+' '+label+' recessed hub',center-outward*.2,center+outward*.2,r*.62,bone,'rubber')
            cyl(side+' '+label+' axle cap',center-outward*.22,center+outward*.24,r*.32,bone,'piston',8)
            for angle in [0,math.pi/2,math.pi,math.pi*1.5]:
                q=center+Vector((math.cos(angle)*r*.8,0,math.sin(angle)*r*.8));cyl(side+' fastener',q-outward*.1,q+outward*.12,.22,bone,'piston',6)
    for label,a,b,bone,width in [('thigh',hip,knee,hb,5.8),('shin',knee,ankle,kb,4.7),('metatarsal',ankle,ball,ab,3.6)]:
        delta=b-a;mid=(a+b)/2
        box(side+' '+label+' structural spine',mid,(width*.65,width*.8,delta.length*.85),bone,'rubber',delta)
        for s in [-1,1]:
            off=outward*s*width*.43
            cyl(side+' '+label+' actuator barrel',a+delta*.15+off,a+delta*.59+off,.68,bone)
            cyl(side+' '+label+' exposed piston',a+delta*.55+off,b-delta*.12+off,.33,bone,'piston')
        box(side+' '+label+' armor plate',mid+Vector((1.3,0,0)),(2.6,width,delta.length*.58),bone,'shell',delta)
        for t in [.3,.42,.54,.66]:
            box(side+' '+label+' inset rib',a+delta*t+Vector((2.7,0,0)),(.35,width*.74,.38),bone,'rubber',delta)
    box(side+' articulated heel',ball+Vector((-1.5,0,.1)),(5.4,5.8,2.6),fb)
    for spread in [-1,0,1]:
        end=toe+Vector((2.8,spread*1.8,.1));start=ball+Vector((.6,spread*1.8,.1))
        box(side+' toe sole', (start+end)/2,(2.0,1.6,(end-start).length),fb,'rubber',end-start)
        box(side+' armored toe', (start+end)/2+Vector((0,0,.8)),(1.8,1.4,(end-start).length*.85),fb,'shell',end-start)

# Export the actual Blender-authored mesh with rigid weights to original joints.
robot=xmodel.Mesh('Blender_robotic_legs');mid={m.name:i for i,m in enumerate(model.materials)}
for ob in kit:
    me=ob.data;me.calc_loop_triangles();base=len(robot.verts);normal_matrix=ob.matrix_world.to_3x3().inverted().transposed()
    robot.verts.extend(xmodel.Vertex(tuple(ob.matrix_world@v.co),[(bones[ob['native_bone']],1.0)]) for v in me.vertices)
    for tri in me.loop_triangles:
        f=xmodel.Face(len(model.meshes),mid[me.materials[tri.material_index].name]);f.indices=[]
        for k in (0,2,1):
            li=tri.loops[k];vi=me.loops[li].vertex_index;n=(normal_matrix@me.corner_normals[li].vector).normalized()
            f.indices.append(xmodel.FaceVertex(base+vi,tuple(n),(1,1,1,1),(.5,.5)))
        robot.faces.append(f)
model.meshes.append(robot)
dst=EXPORT/'tod_doppelgast_black_robot.XMODEL_BIN';model.WriteFile_Bin(str(dst))
check=xmodel.Model();check.LoadFile_Bin(str(dst),split_meshes=True)
assert [(b.name,b.parent,b.offset,b.matrix) for b in donor.bones]==[(b.name,b.parent,b.offset,b.matrix) for b in check.bones]
assert sum(len(m.faces) for m in check.meshes)==sum(len(m.faces) for m in model.meshes)
assert all(f.mesh_id==i for i,m in enumerate(check.meshes) for f in m.faces)
fields=asset('xmodel','hb_bo6_doppelghast');fields['filename']='tod_cyber_elites/'+dst.name;block('tod_doppelgast_black_robot','xmodel',fields)
records.append(dict(name='tod_doppelgast_black_robot',source=str(source),source_sha256=digest(source),output=str(dst.relative_to(ROOT)),sha256=digest(dst),faces=sum(len(m.faces) for m in model.meshes),robot_faces=len(robot.faces),original_bones=len(model.bones),robot_parts=len(kit),organic_leg_cut_z=51,eyes_preserved=True))
(ROOT/'source_data/tod_cyber_elites.gdt').write_text('{\n'+''.join(blocks)+'}\n')
(OUT/'manifest.json').write_text(json.dumps(dict(models=records,textures=texture_records,gdt_sha256=digest(ROOT/'source_data/tod_cyber_elites.gdt'),native_verified=False),indent=2))

# Review both charcoal head and body alongside the full rigged Doppelgast.
for name in ['tod_charcoal_c_zom_dlc3_zombie_sentinel_body','tod_charcoal_c_zom_dlc4_zombie_charred_head']:
    import_model(char_models[name],'Charcoal_'+name,offset=(0,-96,0))
floor=bpy.data.materials.new('Studio neutral gray');floor.diffuse_color=(.06,.06,.06,1)
bpy.ops.mesh.primitive_plane_add(size=1200,location=(0,0,-1));bpy.context.object.data.materials.append(floor);bpy.context.object.name='Studio floor (not exported)'
for label,loc,power,size in [('Key',(140,-130,170),1500000,110),('Fill',(70,150,110),1100000,90),('Rim',(-95,30,150),1800000,90)]:
    light=bpy.data.lights.new(label,'AREA');light.energy=power;light.shape='DISK';light.size=size
    ob=bpy.data.objects.new(label,light);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,-25,50))-ob.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.cameras.new('Review camera');ob=bpy.data.objects.new('Review camera',camera);scene.collection.objects.link(ob);scene.camera=ob
ob.location=(225,-185,115);ob.rotation_euler=(Vector((-2,-35,53))-ob.location).to_track_quat('-Z','Y').to_euler();camera.type='ORTHO';camera.ortho_scale=190
scene.render.filepath=str(OUT/'roster_');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'cyber_elites.blend'))
print(json.dumps(dict(status='AUTHORED',models=len(records),robot_parts=len(kit),robot_faces=len(robot.faces),blend=str(OUT/'cyber_elites.blend'))))

# Keep regenerated legs on the reviewed real-texture/UV path (2026-09-26).
repair=ROOT/'tools/cyber_elites/04_robot_materials.py'
exec(compile(repair.read_text(),str(repair),'exec'))
