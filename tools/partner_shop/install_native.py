"""Produce private map-owned xmodels/GDT from baked Blender components."""
import json,sys,hashlib,re,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/partner_shop';KIT=ART/'engine_kit';OUT=ROOT/'model_export/tod_shop'
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
sys.path.insert(0,str(ROOT/'tools'))
from cyber_reference_one.native_geometry import clean
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((KIT/'source_manifest.json').read_text());assert sha(ROOT/m['master'])==m['master_sha256']
def block(name,kind,fields):
    return '\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v)+'"\n' for k,v in fields.items())+'\t}\n'
source=(ROOT/'source_data/tod_teleporter.gdt').read_text();fields=dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"',source.split('\n\t}',1)[0]))
blocks=[];records=[];groups=list(m['groups']);offgroups=[g for g in groups if g not in ('vendor','mask','arc','spark')]
for group in groups+['off']:
    asset='tod_shop_'+group;material_names=[]
    for lod in range(7):
        sourcegroups=offgroups if group=='off' else [group];model=xmodel.Model(asset)
        bone=xmodel.Bone('tag_origin');bone.offset=(0,0,0);bone.matrix=[(1,0,0),(0,1,0),(0,0,1)];model.bones=[bone]
        matids={};total=0
        for g in sourcegroups:
            d=json.loads((KIT/(g+'_lod'+str(lod)+'.json')).read_text());mat=m['groups'][g]
            if group=='off' and mat=='mtl_tod_shop_glow':mat='mtl_tod_shop_glow_off'
            if mat not in matids:matids[mat]=len(model.materials);model.materials.append(xmodel.Material(mat,'Phong',{}))
            pivot=m['pivots'].get(g,[0,0,0]) if group=='off' else [0,0,0]
            # Bound every reduced LOD to its own original component silhouette.
            original=json.loads((KIT/(g+'_lod0.json')).read_text());bounds=[[min(v[i] for v in original['verts']) for i in range(3)],[max(v[i] for v in original['verts']) for i in range(3)]]
            d['verts']=[tuple(max(bounds[0][i],min(bounds[1][i],v[i]))+pivot[i] for i in range(3)) for v in d['verts']]
            # Reduction and silhouette clamping can leave converter-sized slivers.
            # Clean the final positions before recording expected native coverage.
            clean(d,min_altitude=.001)
            if d['native_slivers_removed']:print('SHOP_SLIVERS',group,g,lod,d['native_slivers_removed'])
            if g=='steady' and lod>0:
                # Native converter log identifies the long, near-collinear
                # neon frame face as "Degenerate triangle (pre-bone)". Its
                # absolute area is valid; normalized area is only .00032455.
                # This guard removes that single face in LOD2, retaining the
                # small lettering and close-up art. See native_triangle.log.
                kept=[]
                for face in d['faces']:
                    a,b,c=[d['verts'][v['v']] for v in face]
                    u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
                    cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                    longest=max(math.dist(a,b),math.dist(b,c),math.dist(c,a))
                    if math.sqrt(sum(x*x for x in cross))/longest**2>=.0005:kept.append(face)
                if len(kept)!=len(d['faces']):print('SHOP_NEON_ANGLE',group,g,lod,len(d['faces'])-len(kept))
                d['faces']=kept
            if m['groups'][g]=='mtl_tod_shop_glow':
                # Flat palette swatches need no parameterized UV shape. Restore
                # a stable triangle after decimation: half-float native packing
                # otherwise merges two corners in the steady LOD2 details.
                for face in d['faces']:
                    u=int(sum(c['uv'][0] for c in face)/3*8)/8
                    v=int(sum(c['uv'][1] for c in face)/3*8)/8
                    for c,offset in zip(face,((.35,.35),(.65,.35),(.35,.65))):c['uv']=[u+offset[0]/8,v+offset[1]/8]
            for start in range(0,len(d['faces']),12000):
                faces=d['faces'][start:start+12000];used=sorted({c['v'] for f in faces for c in f});remap={v:i for i,v in enumerate(used)}
                mesh=xmodel.Mesh(g+'_'+str(start//12000));mesh.verts=[xmodel.Vertex(d['verts'][v],[(0,1.)]) for v in used]
                for face in faces:
                    f=xmodel.Face(len(model.meshes),matids[mat]);f.indices=[xmodel.FaceVertex(remap[c['v']],tuple(c['n']),(1,1,1,1),tuple(c['uv'])) for c in face];mesh.faces.append(f)
                model.meshes.append(mesh)
            total+=len(d['faces'])
        file=OUT/(asset+'_lod'+str(lod)+'.xmodel_bin');model.WriteFile_Bin(str(file),version=7)
        records.append({'asset':asset,'group':group,'lod':lod,'triangles':total,'file':file.relative_to(ROOT).as_posix(),'sha256':sha(file)})
    f=dict(fields)
    for i,key in enumerate(('filename','mediumLod','lowLod','lowestLod','lod4File','lod5File','lod6File')):f[key]='tod_shop\\\\'+asset+'_lod'+str(i)+'.xmodel_bin'
    f.update({'skinOverride':'','scale':1,'CollisionMap':'','BulletCollisionLOD':'None','BulletCollisionFile':'','physicsPreset':'','mediumLodDist':220,'lowLodDist':420,'lowestLodDist':700,'lod4Dist':1100,'lod5Dist':1600,'lod6Dist':2400,'type':'rigid'})
    blocks.append(block(asset,'xmodel',f))
for file,digest in m['textures'].items():
    assert sha(OUT/'_images'/file)==digest
    name=Path(file).stem;suffix=name[-1]
    f={'baseImage':'model_export\\\\tod_shop\\\\_images\\\\'+file,'imageType':'Texture','type':'image','semantic':{'c':'diffuseMap','n':'normalMap','s':'specularMap','g':'glossMap','e':'diffuseMap'}[suffix],'streamable':1,'compressionMethod':'compressed' if suffix in ('n','g') else 'compressed high color'}
    if suffix in ('c','s','e'):f['coreSemantic']='sRGB3chAlpha'
    blocks.append(block(name,'image',f))
for group in ('body','vendor','glow','glow_off'):
    prefix='i_tod_shop_'+('glow' if group=='glow_off' else group)
    f={'surfaceType':'cloth' if group=='vendor' else 'metal','template':'material.template','materialCategory':'Geometry Advanced','materialType':'lit_emissive_advanced_fullspec','colorMap':prefix+'_c','normalMap':prefix+'_n','cosinePowerMap':prefix+'_g','specColorMap':prefix+'_s','specMapEnable':1,'specColorTint':'.5 .5 .5 1','colorMap00':prefix+'_e','colorTint':'1 1 1 1','colorTint1':'1 1 1 1','scaleRGB':0 if group=='glow_off' else 6,'emissiveIncompetence':1,'emissiveFalloff':0,'normalHeightScale':1,'glossRangeMin':0,'glossRangeMax':8,'specAmount':.45,'reflectionProbeAmount':.2,'textureAtlasRowCount':1,'textureAtlasColumnCount':1,'usage':'<not in editor>'}
    blocks.append(block('mtl_tod_shop_'+group,'material',f))
gdt=ROOT/'source_data/tod_shop.gdt';gdt.write_text('{\n'+''.join(blocks)+'}\n')
zone=['// MCP-authored Black Market hut (the item shop until 2026-09-29): native power states and client electrical timeline.','scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_shop.gsc','scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_shop.csc','scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_shop_timing.csc','fx,tod/shop/fx_tod_shop_spark','fx,zombie/fx_wonder_fizz_lightning_all']
zone+=['xmodel,tod_shop_'+g for g in groups+['off']]
(ROOT/'zone_source/tod_shop.zpkg').write_text('\n'.join(zone)+'\n')
(KIT/'install_manifest.json').write_text(json.dumps({**m,'models':records,'gdt_sha256':sha(gdt),'native_playtested':False},indent=2))
print('SHOP_INSTALLED',len(groups)+1,'models;',len(records),'LOD files')
