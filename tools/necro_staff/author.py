"""Blender MCP authoring: native skull anatomy, sculpted ironwork, baked maps.

Canonical assembly is Z-up. Native view assets use the approved ice-staff X-axis
grip; world assets retain Z-up. Every review surface is exported, not a render prop.
"""
import bpy, math, sys, pathlib, json, hashlib, copy, shutil
import numpy as np
from mathutils import Vector, Matrix
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import asset,native_path,xmodel
ART=ROOT/'art/necro_staff';OUT=ROOT/'model_export/tod_necro_staff'
bpy.ops.wm.read_factory_settings(use_empty=True)
window=bpy.context.window_manager.windows[0]
area=next(a for a in window.screen.areas if a.type=="VIEW_3D")
region=next(r for r in area.regions if r.type=="WINDOW")
with bpy.context.temp_override(window=window,area=area,region=region):
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.samples=24
    scene.render.resolution_x=1200;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Neutral material review');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.04,.05,1)
    scene.view_settings.view_transform='AgX'
    gdt=[];parts=[];material_ids={};records=[]

    def block(n,k,f):
        gdt.append('\t"'+n+'" ( "'+k+'.gdf" )\n\t{\n'+''.join('\t\t"'+key+'" "'+str(v).replace('/','\\\\')+'"\n' for key,v in f.items())+'\t}\n')

    def save_image(name,arr,semantic):
        h,w=arr.shape[:2]
        if arr.ndim==2:arr=np.repeat(arr[:,:,None],3,axis=2)
        if arr.shape[2]==3:arr=np.concatenate([arr,np.ones((h,w,1),np.float32)],axis=2)
        im=bpy.data.images.new(name,width=w,height=h,alpha=True)
        im.colorspace_settings.name='sRGB' if semantic=='diffuseMap' else 'Non-Color'
        im.pixels.foreach_set(np.ascontiguousarray(arr,np.float32).ravel());im.filepath_raw=str(OUT/(name+'.png'));im.file_format='PNG';im.save()
        block(name,'image',dict(baseImage='model_export/tod_necro_staff/'+name+'.png',semantic=semantic,imageType='Texture',streamable=0,compressionMethod='compressed high color' if semantic=='diffuseMap' else 'compressed',coreSemantic='sRGB3chAlpha' if semantic=='diffuseMap' else '',type='image'))
        return im

    def native_material(name,images,metal=False,glow=0):
        f=dict(surfaceType='metal' if metal else 'flesh',template='material.template',materialCategory='Geometry Advanced',materialType='lit_emissive_advanced_fullspec',colorMap=images['c'].name,normalMap=images['n'].name,
               cosinePowerMap=images['g'].name,specColorMap=images['s'].name,specMapEnable=1,specColorTint='1 1 1 1',colorTint='1 1 1 1',
               colorMap00=images.get('e',images['c']).name,scaleRGB=glow,emissiveIncompetence=1,emissiveFalloff=0,waterRoughness=0,
               glossRangeMin=0,glossRangeMax=8,specAmount=1,reflectionProbeAmount=.65,textureAtlasRowCount=1,textureAtlasColumnCount=1,usage='<not in editor>')
        block(name,'material',f)
        m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
        for key,slot in [('c','Base Color'),('n','Normal'),('g','Roughness')]:
            tex=n.new('ShaderNodeTexImage');tex.image=images[key]
            if key=='n':
                # Native normal images use DirectX green; preview explicitly flips it.
                sep=n.new('ShaderNodeSeparateXYZ');com=n.new('ShaderNodeCombineXYZ');sub=n.new('ShaderNodeMath');sub.operation='SUBTRACT';sub.inputs[0].default_value=1
                l.new(tex.outputs['Color'],sep.inputs[0]);l.new(sep.outputs[0],com.inputs[0]);l.new(sep.outputs[1],sub.inputs[1]);l.new(sub.outputs[0],com.inputs[1]);l.new(sep.outputs[2],com.inputs[2])
                nm=n.new('ShaderNodeNormalMap');l.new(com.outputs[0],nm.inputs['Color']);l.new(nm.outputs[0],bs.inputs[slot])
            elif key=='g':
                # Approximate native 0..8 gloss stops as GGX perceptual roughness.
                mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=8;l.new(tex.outputs[0],mul.inputs[0])
                power=n.new('ShaderNodeMath');power.operation='POWER';power.inputs[0].default_value=2;l.new(mul.outputs[0],power.inputs[1])
                add=n.new('ShaderNodeMath');add.operation='ADD';add.inputs[1].default_value=2;l.new(power.outputs[0],add.inputs[0])
                div=n.new('ShaderNodeMath');div.operation='DIVIDE';div.inputs[0].default_value=2;l.new(add.outputs[0],div.inputs[1])
                root=n.new('ShaderNodeMath');root.operation='POWER';root.inputs[1].default_value=.25;l.new(div.outputs[0],root.inputs[0]);l.new(root.outputs[0],bs.inputs[slot])
            else:l.new(tex.outputs['Color'],bs.inputs[slot])
        bs.inputs['Metallic'].default_value=.9 if metal else 0
        if glow:
            tex=n.new('ShaderNodeTexImage');tex.image=images.get('e',images['c']);l.new(tex.outputs[0],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=glow
        m['preview_limit']='Approximate native maps/gloss; BO3 lighting remains user tested.'
        material_ids[name]=m;return m

    # Detailed iron textures: etched interlace and hammered wear on a reproducible
    # two-dimensional UV tile, including real tangent normals and separate gloss/spec.
    N=2048;y,x=np.mgrid[0:N,0:N].astype(np.float32)/N
    rng=np.random.default_rng(271453)
    grain=rng.random((N,N),dtype=np.float32)
    def noise_grid(k):
        grid=rng.random((k,k),dtype=np.float32)
        xx=x*k;yy=y*k;ix=xx.astype(int);iy=yy.astype(int);fx=xx-ix;fy=yy-iy
        fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
        return (grid[iy%k,ix%k]*(1-fx)+grid[iy%k,(ix+1)%k]*fx)*(1-fy)+(grid[(iy+1)%k,ix%k]*(1-fx)+grid[(iy+1)%k,(ix+1)%k]*fx)*fy
    hammer=noise_grid(37)*.55+noise_grid(133)*.25+noise_grid(511)*.20-.5
    # Chased interlace with broad recesses, polished lips and fine pitting.
    # Features occupy enough texels to survive the native compressed mip chain.
    phase=2*math.pi*y*4
    braid=np.minimum(abs(np.sin(2*math.pi*x*3+phase)),abs(np.sin(2*math.pi*x*3-phase)))
    engrave=np.exp(-(braid/.11)**2)
    lip=np.exp(-((braid-.19)/.07)**2)
    bands=np.exp(-(np.sin(2*math.pi*y*4)/.13)**2)
    pits=np.maximum(0,.28-noise_grid(255))
    h=.004*hammer+.00015*grain-.006*engrave+.0015*lip-.006*pits
    # Derivatives measured in UV space (the old per-pixel gradient was nearly flat).
    dy,dx=np.gradient(h,1/N);normal=np.stack([-dx*.20,dy*.20,np.ones_like(x)],axis=2);normal/=np.linalg.norm(normal,axis=2,keepdims=True)
    iron=.075+.10*hammer+.008*grain-.050*engrave+.11*lip+.025*bands-.05*pits
    color=np.stack([iron*.86,iron*.94,iron],axis=2)
    metal_images={'c':save_image('i_tod_necro_iron_c',np.clip(color,0,1),'diffuseMap'),
     'n':save_image('i_tod_necro_iron_n',normal*.5+.5,'normalMap'),
     'g':save_image('i_tod_necro_iron_g',np.clip(.57+.12*hammer-.27*engrave+.16*lip,0,1),'glossMap'),
     's':save_image('i_tod_necro_iron_s',np.clip(np.repeat((.43+.09*hammer-.30*engrave+.20*lip)[:,:,None],3,axis=2),0,1),'specularMap')}
    ironmat=native_material('mtl_tod_necro_staff_iron',metal_images,True)
    # Broad blade planes have their own forged finish. Do not smear the grip's
    # interlace tile across arbitrary blade islands (it reads as crumpled foil).
    forge=.085+.09*hammer+.018*grain
    fh=.003*hammer+.00010*grain-.004*pits
    fy,fx=np.gradient(fh,1/N)
    fn=np.stack([-fx*.12,fy*.12,np.ones_like(x)],axis=2);fn/=np.linalg.norm(fn,axis=2,keepdims=True)
    forge_images={'c':save_image('i_tod_necro_forge_c',np.stack([forge*.88,forge*.95,forge],axis=2),'diffuseMap'),
     'n':save_image('i_tod_necro_forge_n',fn*.5+.5,'normalMap'),
     'g':save_image('i_tod_necro_forge_g',np.clip(.56+.16*hammer,0,1),'glossMap'),
     's':save_image('i_tod_necro_forge_s',np.clip(np.repeat((.46+.10*hammer)[:,:,None],3,axis=2),0,1),'specularMap')}
    forgemat=native_material('mtl_tod_necro_staff_forge',forge_images,True)
    # Bone anatomy and its original UVs / color / normal are retained from BO3.
    donor=native_path('model_export',asset('xmodel','rune_prison_death_skull')['filename'])
    skull=xmodel.Model();skull.LoadFile_Bin(str(donor),split_meshes=True)
    bone_images={}
    for key,semantic in [('c','diffuseMap'),('n','normalMap')]:
        src=donor.parent/'_images'/f'i_mtl_p7_skulls_bones_set_{key}.png'
        dest=OUT/('i_tod_necro_bone_'+key+'.png');shutil.copyfile(src,dest)
        im=bpy.data.images.load(str(dest));im.colorspace_settings.name='sRGB' if key=='c' else 'Non-Color'
        # Preserve native pixels rather than claim enlarged images add detail.
        im.name='i_tod_necro_bone_'+key
        bone_images[key]=im;block(im.name,'image',dict(baseImage='model_export/tod_necro_staff/'+im.name+'.png',semantic=semantic,imageType='Texture',streamable=0,compressionMethod='compressed high color' if semantic=='diffuseMap' else 'compressed',coreSemantic='sRGB3chAlpha' if semantic=='diffuseMap' else '',type='image'))
    bone_images['g']=save_image('i_tod_necro_bone_g',np.full((256,256),.30,np.float32),'glossMap')
    bone_images['s']=save_image('i_tod_necro_bone_s',np.full((256,256,3),.035,np.float32),'specularMap')
    bonemat=native_material('mtl_tod_necro_staff_bone',bone_images)
    eyeimages={'c':save_image('i_tod_necro_staff_soul_c',np.full((64,64,3),(.50,.63,.64),np.float32),'diffuseMap'),
     'n':save_image('i_tod_necro_staff_soul_n',np.full((64,64,3),(.5,.5,1),np.float32),'normalMap'),
     'g':save_image('i_tod_necro_staff_soul_g',np.full((64,64),.6,np.float32),'glossMap'),
     's':bone_images['s']}
    eyemat=native_material('mtl_tod_necro_staff_soul',eyeimages,False,2)

    def finish(ob,name,mat,tier,bevel=0,uv=True):
        ob.name=name;ob['tier']=tier;ob.data.materials.append(mat)
        bpy.context.view_layer.objects.active=ob;ob.select_set(True)
        if bevel:
            mod=ob.modifiers.new('Forged edge radii','BEVEL');mod.width=bevel;mod.segments=3
            with bpy.context.temp_override(object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.modifier_apply(modifier=mod.name)
        for p in ob.data.polygons:p.use_smooth=True
        if uv:
            with bpy.context.temp_override(object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):
                bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
        parts.append(ob);return ob

    def cyl(name,z,r,length,tier,mat=ironmat):
        bpy.ops.object.select_all(action='DESELECT');bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=length,location=(0,0,z))
        ob=finish(bpy.context.view_layer.objects.active,name,mat,tier,.07)
        # Continuous cylindrical texel layout: no random smart-project patches
        # on the hero shaft. Every 12 units gets one complete carved tile.
        uv=ob.data.uv_layers.active.data
        for poly in ob.data.polygons:
            coords=[ob.data.vertices[ob.data.loops[li].vertex_index].co for li in poly.loop_indices]
            us=[math.atan2(p.y,p.x)/(2*math.pi)+.5 for p in coords]
            if max(us)-min(us)>.5:us=[u+1 if u<.5 else u for u in us]
            for li,p,u in zip(poly.loop_indices,coords,us):
                uv[li].uv=(u,(p.z+z)/12) if abs(poly.normal.z)<.8 else (p.x/(2*r)+.5,p.y/(2*r)+.5)
        return ob

    def line(name,coords,r,tier,mat=ironmat):
        d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=2;d.bevel_depth=r;d.bevel_resolution=2
        s=d.splines.new('POLY');s.points.add(len(coords)-1)
        for p,c in zip(s.points,coords):p.co=(*c,1)
        ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
        with bpy.context.temp_override(object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.convert(target='MESH')
        return finish(bpy.context.view_layer.objects.active,name,mat,tier)

    def blade(name,start,end,width,depth,tier):
        start=Vector(start);end=Vector(end);axis=(end-start).normalized();side=Vector((axis.z,0,-axis.x));front=Vector((0,-1,0))
        vs=[]
        for at,w,d in [(0,width*.46,depth*.55),(.30,width,depth),(.67,width*.52,depth*.55),(.999,.015,.015)]:
            center=start.lerp(end,at)
            vs += [tuple(center+side*w),tuple(center+front*d),tuple(center-side*w),tuple(center-front*d)]
        fs=[(3,2,1,0)]
        for row in range(3):
            for k in range(4):a=row*4+k;b=row*4+(k+1)%4;fs.append((a,b,b+4,a+4))
        fs.append((12,13,14,15));d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob)
        return finish(ob,name,forgemat,tier,.045)

    def ring(name,r,z,tier):
        bpy.ops.object.select_all(action='DESELECT');bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.42,major_segments=96,minor_segments=12,location=(0,.9,z),rotation=(math.pi/2,0,0))
        return finish(bpy.context.view_layer.objects.active,name,forgemat,tier)

    for tier in (2,3):
        # Two actual hand grips: native left at X~0, right at X~-11.4.
        cyl('Forged tapered shaft T'+str(tier),-5,.74,62,tier)
        cyl('Lower pommel T'+str(tier),-36,1.04,2.2,tier)
        cyl('Socket neck T'+str(tier),26.8,1.0,2.2,tier)
        cyl('Skull mounting ferrule T'+str(tier),28.0,1.27,.5,tier)
        for z in [-31,-19,-13,1,15,23]:cyl('Chased collar T'+str(tier),z,.90, .48,tier)
        for center in [-11.4,0]:
            cyl('Grip bed T'+str(tier),center,.82,4.5,tier)
            for z in np.arange(center-2,center+2,.32):cyl('Fine grip ring T'+str(tier),float(z),.865,.10,tier)
        # Engraved spiral ribs are silhouette geometry; the shader adds fine wear.
        for s in [-1,1]:
            coords=[]
            for z in np.linspace(-33,25,240):
                a=z*.5+s*1.57;coords.append((.78*math.cos(a),.78*math.sin(a),float(z)))
            line('Raised shaft interlace T'+str(tier),coords,.055 if tier==2 else .09,tier)
        # Native human skull, centered at Z=33; canonical face points toward -Y.
        for src in skull.meshes:
            # Disconnected mandibular surfaces and lower teeth rotate together.
            parents=list(range(len(src.verts)))
            def find(i):
                while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
                return i
            for face in src.faces:
                a,b,c=[v.vertex for v in face.indices];parents[find(a)]=find(b);parents[find(c)]=find(b)
            groups={}
            for i,v in enumerate(src.verts):groups.setdefault(find(i),[]).append(i)
            jaw={i for ids in groups.values() if max(src.verts[j].offset[2] for j in ids)<3 for i in ids}
            verts=[]
            for i,v in enumerate(src.verts):
                pos=Vector(v.offset)
                if i in jaw:pos=Vector((.8,0,2.93))+Matrix.Rotation(math.radians(-18),3,'Y')@(pos-Vector((.8,0,2.93)))
                verts.append((-pos.y*1.10,-(pos.x-.6)*1.10,28.1+pos.z*1.10))
            faces=[tuple(i.vertex for i in reversed(f.indices)) for f in src.faces]
            data=bpy.data.meshes.new('Human skull');data.from_pydata(verts,[],faces);uv=data.uv_layers.new()
            for p,f in zip(data.polygons,src.faces):
                for li,ix in zip(p.loop_indices,reversed(f.indices)):
                    u=ix.uv;uv.data[li].uv=(u[0],1-u[1])
            ob=bpy.data.objects.new('Carved human skull T'+str(tier),data);scene.collection.objects.link(ob);finish(ob,ob.name,bonemat,tier,uv=False)
            # Subdivision smooths the real anatomy, with the source normal/UV intact.
            bpy.context.view_layer.objects.active=ob;mod=ob.modifiers.new('Anatomical surface refinement','SUBSURF');mod.levels=1
            with bpy.context.temp_override(object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.modifier_apply(modifier=mod.name)
        # Minimal soul cores sit inside the sockets; no external ball or white flash.
        for side in [-1,1]:
            bpy.ops.object.select_all(action='DESELECT');bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=.23,location=(side*1.83,-2.5,34.62))
            finish(bpy.context.view_layer.objects.active,'Recessed soul eye T'+str(tier),eyemat,tier)
        # Bone-carved spirals follow ray-cast forehead contours exactly.
        if tier==3:
            skull_ob=next(o for o in parts if o.name.startswith('Carved human skull') and o['tier']==tier)
            for side in [-1,1]:
                coords=[]
                for t in np.linspace(0,2.7*math.pi,65):
                    r=.14+.082*t;px=side*(.94+r*math.cos(t));pz=35.4+r*math.sin(t)
                    hit,loc,normal,idx=skull_ob.ray_cast(Vector((px,-12,pz)),Vector((0,1,0)))
                    if hit:coords.append(tuple(loc+normal*.012))
                if len(coords)>2:line('Incised forehead spiral',coords,.024,tier,ironmat)
            coords=[]
            for z in np.linspace(35.4,36.85,25):
                px=.10*math.sin(z*23);hit,loc,normal,idx=skull_ob.ray_cast(Vector((px,-12,z)),Vector((0,1,0)))
                if hit:coords.append(tuple(loc+normal*.009))
            if len(coords)>2:line('Cranial suture inlay',coords,.018,tier,ironmat)
        if tier==2:
            # A simple ferrule under the skull, not a halo intersecting its jaw.
            continue
        ring('Outer pierced iron halo',6.05,33.0,tier);ring('Inner chased halo',5.45,33.0,tier)
        for a in np.linspace(0,2*math.pi,32,endpoint=False):
            x0,z0=5.7*math.cos(a),33+5.7*math.sin(a)
            # Pierced filigree links, not a flat ring with painted-on holes.
            coords=[(x0+.23*math.cos(t),.45,z0+.32*math.sin(t)) for t in np.linspace(0,2*math.pi,13)]
            line('Pierced halo link',coords,.095,tier)
        for angle in [0,42,138,180,222,318]:
            a=math.radians(angle);start=(5.9*math.cos(a),.9,33+5.9*math.sin(a));end=(11.2*math.cos(a),.9,33+11.2*math.sin(a))
            blade('Radial forged spike',start,end,1.10,.42,tier)
        blade('Long central spear finial',(0,.9,37.9),(0,.9,54),1.48,.58,tier)
        for side in [-1,1]:blade('Split upper shard',(side*1.3,.9,37),(side*3.25,.9,45.8),.50,.30,tier)
        for side in [-1,1]:blade('Forked neck guard',(side*3,.8,28.5),(side*.72,.0,20.3),.90,.45,tier)
        # Chased scrollwork on the finial ridge and neck echoes the reference motifs.
        for side in [-1,1]:
            line('Finial recessed tracer',[(0,.26,39),(side*.6,.28,41),(side*.38,.43,46),(0,.57,51)],.075,tier)
        for z in [5,9,17,21]:
            line('Shaft engraved chevron',[(-.52,-.61,z+.8),(0,-.81,z),(.52,-.61,z+.8)],.07,tier)

    # Separate canonical masters allow independent tier review and later re-export.
    for tier in [2,3]:
        col=bpy.data.collections.new('Tier '+str(tier)+' export');scene.collection.children.link(col)
        for ob in parts:
            if ob['tier']!=tier:continue
            for old in list(ob.users_collection):old.objects.unlink(ob)
            col.objects.link(ob)
    scene['reference']='Screenshot 2026-09-27 145453.png'
    scene['status']='Authored geometry and native maps; user runtime review pending.'
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'staff_master.blend'))
    (OUT/'materials.gdtpart').write_text(''.join(gdt))
    (ART/'authoring.json').write_text(json.dumps({'parts':len(parts),'skull_source':str(donor),'skull_source_sha256':hashlib.sha256(donor.read_bytes()).hexdigest(),'custom_texture_resolution':2048,'bone_maps':'Original BO3 1024x512 pixels/UVs preserved','native_visual_verified':False},indent=2))
    print('NECRO_STAFF_AUTHORED',len(parts),'mesh parts; custom 2K iron maps and native bone maps; editable master saved')
