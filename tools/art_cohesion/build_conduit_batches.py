"""Assemble the Blender-authored wire meshes at verified map transforms.

One nonsolid off/on host per region, two explicit LODs. Reuse the authored
medium mesh rather than multiply invisible screw-head geometry. The distant
LOD omits retaining clips; its shell and wires retain the validated geometry.
"""
import pathlib,sys,json,hashlib,math,copy
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
ART=ROOT/'art/cybercity_materials/color_restoration';EXP=ROOT/'model_export/tod_surface'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
layout=json.loads((ART/'conduit_mounts.json').read_text());blocks=[];records=[]
def rotate(v,angles):
    p,y,r=map(math.radians,angles);x0,y0,z0=v
    a=(x0,y0*math.cos(r)-z0*math.sin(r),y0*math.sin(r)+z0*math.cos(r))
    b=(a[0]*math.cos(p)+a[2]*math.sin(p),a[1],-a[0]*math.sin(p)+a[2]*math.cos(p))
    return (b[0]*math.cos(y)-b[1]*math.sin(y),b[0]*math.sin(y)+b[1]*math.cos(y),b[2])
def block(name,kind,fields):
    return '"'+name+'" ( "'+kind+'.gdf" )\n{\n'+''.join('    "'+k+'" "'+str(v)+'"\n' for k,v in fields.items())+'}\n'
sources={}
for lod in (1,):
    p=EXP/f'tod_power_conduit_off_lod{lod}.xmodel_bin';m=xmodel.Model();m.LoadFile_Bin(str(p),split_meshes=True);sources[lod]=m
for group in layout['groups']:
    members=[r for r in layout['rows'] if r['group']==group['kind']]
    for lod in (0,1):
        src=sources[1];model=xmodel.Model(group['model']);model.bones=copy.deepcopy(src.bones)
        keep=[i for i,m in enumerate(src.materials) if not (lod and m.name.endswith('_steel'))]
        ids={old:new for new,old in enumerate(keep)};model.materials=[copy.copy(src.materials[i]) for i in keep]
        # Merge by material: four surfaces per regional model, not 22 per channel.
        meshes={i:xmodel.Mesh('channel_'+str(ids[i])) for i in keep}
        for row in members:
            for old in src.meshes:
                mat=old.faces[0].material_id
                if mat not in ids:continue
                mesh=meshes[mat];base=len(mesh.verts)
                for vert in old.verts:
                    v=rotate(tuple(a*b for a,b in zip(vert.offset,row['scale'])),row['angles'])
                    pos=tuple(v[i]+row['org'][i]-group['org'][i] for i in range(3))
                    mesh.verts.append(xmodel.Vertex(pos,[(0,1.)]))
                for face in old.faces:
                    f=copy.copy(face);f.mesh_id=ids[mat];f.material_id=ids[mat];f.indices=[copy.copy(v) for v in face.indices]
                    for fv in f.indices:
                        fv.vertex+=base
                        n=rotate(tuple(a/b for a,b in zip(fv.normal,row['scale'])),row['angles']);length=math.sqrt(sum(a*a for a in n));fv.normal=tuple(a/length for a in n)
                    mesh.faces.append(f)
        model.meshes=list(meshes.values());assert all(len(m.verts)<65536 for m in model.meshes)
        for state in ('off','on'):
            out=copy.copy(model);out.materials=[copy.copy(m) for m in model.materials];out.name=group['model']+'_'+state
            if state=='on':
                for mat in out.materials:
                    if mat.name.endswith('wire_off'):mat.name='mtl_tod_conduit_wire_on'
            p=EXP/(out.name+f'_lod{lod}.xmodel_bin');out.WriteFile_Bin(str(p),version=7)
            pts=[v.offset for m in out.meshes for v in m.verts]
            records.append(dict(asset=out.name,lod=lod,file=p.relative_to(ROOT).as_posix(),sha256=sha(p),triangles=sum(len(m.faces) for m in out.meshes),bounds=[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]))
    for state in ('off','on'):
        asset=group['model']+'_'+state
        blocks.append(block(asset,'xmodel',dict(filename=f'tod_surface/{asset}_lod0.xmodel_bin',mediumLod=f'tod_surface/{asset}_lod1.xmodel_bin',mediumLodDist=1600,type='rigid',scale=1,CollisionMap='',BulletCollisionLOD='None',physicsPreset='',cullOutDiameter=0,materials='')))
(ROOT/'source_data/tod_conduit_batches.gdt').write_text('{\n'+''.join(blocks)+'}\n')
(ART/'conduit_batches.json').write_text(json.dumps(dict(layout_sha256=hashlib.sha256(json.dumps({k:layout[k] for k in ('rows','groups')},sort_keys=True).encode()).hexdigest(),sources={str(k):sha(EXP/f'tod_power_conduit_off_lod{k}.xmodel_bin') for k in sources},channels=len(layout['rows']),hosts=len(layout['groups']),models=records,native_visual_verified=False),indent=2)+'\n')
print('CONDUIT_BATCHES_EXPORTED',len(layout['rows']),'inlays,',len(layout['groups']),'hosts,',len(records),'native LODs')
