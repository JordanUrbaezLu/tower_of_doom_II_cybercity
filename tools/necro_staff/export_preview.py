"""MCP: export the exact authored meshes and review their first-person fit."""
import bpy, pathlib,sys,json,math,copy,hashlib
from mathutils import Vector,Matrix
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import xmodel,asset,native_path
from PyCoD import xanim
ART=ROOT/'art/necro_staff';OUT=ROOT/'model_export/tod_necro_staff'
bpy.ops.wm.open_mainfile(filepath=str(ART/'staff_master.blend'))
scene=bpy.context.scene
window=bpy.context.window_manager.windows[0];window.scene=scene
area=next(a for a in window.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
IDENT=((1,0,0),(0,1,0),(0,0,1))
# Canonical Z shaft -> native X shaft; skull's front (-Y) -> top (+Z).
VIEW=Matrix(((0,0,1),(-1,0,0),(0,-1,0)))
tags={'tag_flash':(0,-3.9,32),'tag_fx_mouth':(0,-3.9,31.4),'tag_fx_left':(-1.5,-2.7,33.6),'tag_fx_right':(1.5,-2.7,33.6)}
def viewpoint(p):
    # Rigid axis conversion: never bend the neck to frame the first-person head.
    return VIEW@Vector(p)
parts=[o for o in scene.objects if o.type=='MESH' and 'tier' in o]
gdt=(OUT/'materials.gdtpart').read_text();records=[]
def block(name,kind,f):
    return '\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v).replace('/','\\\\')+'"\n' for k,v in f.items())+'\t}\n'
with bpy.context.temp_override(window=window,area=area,region=region):
    for tier in [2,3]:
        for form in ['view','world']:
            trans=VIEW if form=='view' else Matrix.Identity(3)
            for lod in range(3):
                name=f'tod_necro_staff{tier}_{form}';mod=xmodel.Model(name)
                for n,p in [('tag_weapon',(0,0,0)),*tags.items()]:
                    b=xmodel.Bone(n);b.parent=-1 if n=='tag_weapon' else 0;b.offset=tuple(viewpoint(p) if form=='view' else Vector(p));b.matrix=IDENT;mod.bones.append(b)
                ids={};meshes={}
                for src in parts:
                    if src['tier']!=tier:continue
                    if lod==2 and any(s in src.name for s in ['Fine grip','Pierced halo link','Temple inlay','Shaft engraved','Finial recessed']):continue
                    ob=src.copy();ob.data=src.data.copy();scene.collection.objects.link(ob)
                    if lod:
                        bpy.context.view_layer.objects.active=ob
                        d=ob.modifiers.new('Native distance reduction','DECIMATE');d.ratio=.52 if lod==1 else .22
                        with bpy.context.temp_override(object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.modifier_apply(modifier=d.name)
                    me=ob.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
                    mat=me.materials[0].name
                    if mat not in ids:ids[mat]=len(mod.materials);mod.materials.append(xmodel.Material(mat,'Phong',{}))
                    if mat not in meshes or len(meshes[mat].verts)+len(me.vertices)>28000:
                        mesh=xmodel.Mesh(mat+'_'+str(len(mod.meshes)));mod.meshes.append(mesh);meshes[mat]=mesh
                    mesh=meshes[mat];offset=len(mesh.verts);mi=mod.meshes.index(mesh)
                    mesh.verts.extend(xmodel.Vertex(tuple(viewpoint(ob.matrix_world@v.co) if form=='view' else ob.matrix_world@v.co),[(0,1.)]) for v in me.vertices)
                    nm=trans@ob.matrix_world.to_3x3().inverted().transposed()
                    for tri in me.loop_triangles:
                        p=[Vector(mesh.verts[offset+v].offset) for v in tri.vertices];length=max((p[1]-p[0]).length,(p[2]-p[0]).length,(p[2]-p[1]).length)
                        if length<.001 or (p[1]-p[0]).cross(p[2]-p[0]).length/length**2<.0006:continue
                        f=xmodel.Face(mi,ids[mat]);f.indices=[]
                        for corner in [0,2,1]:
                            li=tri.loops[corner];u=uv[li].uv
                            normal=(nm@me.corner_normals[li].vector).normalized()
                            # Boolean cuts can leave an undefined custom split
                            # normal on a valid triangle. BO3 rejects a zero
                            # normal; retain that face with its geometric normal.
                            if normal.length_squared < .5:
                                normal=(nm@tri.normal).normalized()
                            assert normal.length_squared > .99,(src.name,tri.index,li,'invalid export normal')
                            f.indices.append(xmodel.FaceVertex(offset+tri.vertices[corner],tuple(normal),(1,1,1,1),(u.x,1-u.y)))
                        mesh.faces.append(f)
                    bpy.data.objects.remove(ob,do_unlink=True)
                file=OUT/(name+f'_lod{lod}.XMODEL_BIN');mod.WriteFile_Bin(str(file),version=7)
                records.append({'asset':name,'lod':lod,'triangles':sum(len(m.faces) for m in mod.meshes),'vertices':sum(len(m.verts) for m in mod.meshes),'file':file.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
            gdt+=block(name,'xmodel',dict(filename='tod_necro_staff/'+name+'_lod0.XMODEL_BIN',mediumLod='tod_necro_staff/'+name+'_lod1.XMODEL_BIN',lowLod='tod_necro_staff/'+name+'_lod2.XMODEL_BIN',mediumLodDist=500,lowLodDist=1200,type='animated',scale=1,CollisionMap='',BulletCollisionLOD='None',physicsPreset='',cullOutDiameter=0,materials=''))
    (ROOT/'source_data/tod_necro_staff_art.gdt').write_text('{\n'+gdt+'}\n')
    (ART/'models.json').write_text(json.dumps({'models':records,'view_transform':[list(r) for r in VIEW],'tags_canonical':tags,'view_tags':{k:list(viewpoint(v)) for k,v in tags.items()},'native_visual_verified':False},indent=2))

# Shader/material review. These are source previews, not a native screenshot.
scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_percentage=100
camdata=bpy.data.cameras.new('Staff review');cam=bpy.data.objects.new('Staff review',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=101
for pos,energy,size in [((30,-30,60),100000,40),((-22,-10,24),65000,35),((10,20,45),130000,30)]:
    d=bpy.data.lights.new('Neutral review softbox','AREA');d.energy=energy;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,20))-o.location).to_track_quat('-Z','Y').to_euler()
for tier in [2,3]:
    for ob in parts:ob.hide_render=ob['tier']!=tier
    for name,loc,target,scale in [('full',(18,-100,27),(0,0,8),101),('head',(18,-90,43),(0,0,35),36)]:
        cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=scale
        scene.render.filepath=str(ART/f'tier{tier}_{name}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'staff_review.blend'))
print('NECRO_STAFF_EXPORTED',json.dumps(records))
