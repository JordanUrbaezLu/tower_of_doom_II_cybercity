"""Build map-owned native assets from the baked MCP-authored teleporter."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/teleporter';STAGE=ART/'engine_kit';OUT=ROOT/'model_export/tod_teleporter'
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((STAGE/'source_manifest.json').read_text());assert sha(ROOT/m['master'])==m['master_sha256']
records=[]
for lod in range(7):
    data=json.loads((STAGE/('solid_lod'+str(lod)+'.json')).read_text());model=xmodel.Model('tod_teleporter')
    root=xmodel.Bone('tag_origin');root.offset=(0,0,0);root.matrix=[(1,0,0),(0,1,0),(0,0,1)];model.bones=[root];model.materials=[xmodel.Material('mtl_tod_teleporter','Phong',{})]
    for start in range(0,len(data['faces']),18000):
        faces=data['faces'][start:start+18000];used=sorted({c['v'] for f in faces for c in f});indices={v:i for i,v in enumerate(used)}
        mesh=xmodel.Mesh('solid_'+str(start//18000));mesh.verts=[xmodel.Vertex(data['verts'][i],[(0,1.)]) for i in used];assert len(mesh.verts)<65535
        for corners in faces:
            f=xmodel.Face(len(model.meshes),0);f.indices=[xmodel.FaceVertex(indices[c['v']],tuple(c['n']),(1,1,1,1),tuple(c['uv'])) for c in corners];mesh.faces.append(f)
        model.meshes.append(mesh)
    p=OUT/('tod_teleporter_lod'+str(lod)+'.xmodel_bin');model.WriteFile_Bin(str(p),version=7)
    records.append({'lod':lod,'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'triangles':len(data['faces'])})
def block(name,kind,fields):
    def val(v):
        if isinstance(v,float) and v.is_integer():v=int(v)
        return str(v).replace('"','\\"').replace('\n','\\n')
    return '\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+val(v)+'"\n' for k,v in fields.items())+'\t}\n'
fields=json.loads((ART/'original_sources.json').read_text())['models']['p7_zm_der_teleporter']['fields']
for i,key in enumerate(('filename','mediumLod','lowLod','lowestLod','lod4File','lod5File','lod6File')):fields[key]='tod_teleporter\\\\tod_teleporter_lod'+str(i)+'.xmodel_bin'
fields.update({'skinOverride':'','scale':1,'CollisionMap':'','BulletCollisionLOD':'None','BulletCollisionFile':'','physicsPreset':'','highLodDist':0,'mediumLodDist':300,'lowLodDist':550,'lowestLodDist':850,'lod4Dist':1250,'lod5Dist':1800,'lod6Dist':2600,'lod7File':'','lod7Dist':0,'type':'rigid','arabicUnsafe':0,'japaneseUnsafe':0,'germanUnsafe':0})
for key in list(fields):
    if key.startswith('autogen') and not key.endswith('Percent'):fields[key]=0
blocks=[block('tod_teleporter','xmodel',fields)]
for file,digest in m['textures'].items():
    assert sha(OUT/'_images'/file)==digest
    name=Path(file).stem;suffix=name.rsplit('_',1)[-1]
    f={'baseImage':'model_export\\\\tod_teleporter\\\\_images\\\\'+file,'imageType':'Texture','type':'image','semantic':{'c':'diffuseMap','n':'normalMap','s':'specularMap','g':'glossMap','e':'diffuseMap'}[suffix],'streamable':1,'compressionMethod':'compressed' if suffix in ('n','g') else 'compressed high color'}
    if suffix in ('c','s','e'):f['coreSemantic']='sRGB3chAlpha'
    blocks.append(block(name,'image',f))
material={'surfaceType':'metal','template':'material.template','materialCategory':'Geometry Advanced','materialType':'lit_emissive_advanced_fullspec','colorMap':'i_tod_teleporter_c','normalMap':'i_tod_teleporter_n','cosinePowerMap':'i_tod_teleporter_g','specColorMap':'i_tod_teleporter_s','specMapEnable':1,'specColorTint':'.65 .65 .65 1','colorMap00':'i_tod_teleporter_e','colorTint':'1 1 1 1','colorTint1':'1 1 1 1','scaleRGB':6,'emissiveIncompetence':1,'emissiveFalloff':0,'normalHeightScale':1,'glossRangeMin':0,'glossRangeMax':13,'specAmount':.6,'reflectionProbeAmount':.35,'textureAtlasRowCount':1,'textureAtlasColumnCount':1,'usage':'<not in editor>'}
sys.path.insert(0,str(ROOT/'tools'))
from art_cohesion.profiles import apply as apply_finish
apply_finish(material,'teleporter')
blocks.append(block('mtl_tod_teleporter','material',material))
gdt=ROOT/'source_data/tod_teleporter.gdt';gdt.write_text('{\n'+''.join(blocks)+'}\n')
manifest={**m,'asset':'tod_teleporter','gdt_sha256':sha(gdt),'models':records,'native_playtested':False,'placements':9,'collision':'None; existing walk-through pad contract','original_lower_casting_retained':True}
(STAGE/'install_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('TELEPORTER_INSTALLED',[(r['lod'],r['triangles']) for r in records])
