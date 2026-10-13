"""Emit this map's sword, preserving the donor's complete animation skeleton."""
import copy,json
from common import *
manifest=json.loads((KIT/'source_manifest.json').read_text())
assert sha(ROOT/manifest['master'])==manifest['master_sha256']
donor=load(DONOR);records=[]
for lod in range(7):
    data=json.loads((KIT/f'solid_lod{lod}.json').read_text())
    model=xmodel.Model('tod_cyber_sword');model.bones=copy.deepcopy(donor.bones)
    model.materials=[xmodel.Material('mtl_tod_cyber_sword','Phong',{})]
    assert model.bones[0].name=='tag_weapon'
    for start in range(0,len(data['faces']),18000):
        faces=data['faces'][start:start+18000];used=sorted({c['v'] for f in faces for c in f});indices={v:i for i,v in enumerate(used)}
        mesh=xmodel.Mesh('sword_'+str(start//18000));mesh.verts=[xmodel.Vertex(data['verts'][i],[(0,1.)]) for i in used]
        assert len(mesh.verts)<65535
        for corners in faces:
            face=xmodel.Face(len(model.meshes),0)
            face.indices=[xmodel.FaceVertex(indices[c['v']],tuple(c['n']),(1,1,1,1),tuple(c['uv'])) for c in corners]
            mesh.faces.append(face)
        model.meshes.append(mesh)
    path=OUT/f'tod_cyber_sword_lod{lod}.xmodel_bin';model.WriteFile_Bin(str(path),version=7)
    records.append(dict(lod=lod,file=path.relative_to(ROOT).as_posix(),sha256=sha(path),triangles=len(data['faces'])))
base=parse(ROOT/'donor_gdt/hellbound/hb_gold_sword.gdt')
charged=parse(Path('C:/BO3Tools/TOD2Cybercity/source_data/hb_gold_sword_charged.gdt'))
blocks=[]
for file,digest in manifest['textures'].items():
    assert sha(OUT/'_images'/file)==digest
    name=Path(file).stem;suffix=name.rsplit('_',1)[-1]
    f=dict(baseImage='model_export\\\\tod_warrior\\\\cyber_sword\\\\_images\\\\'+file,imageType='Texture',type='image',
           semantic={'c':'diffuseMap','n':'normalMap','s':'specularMap','g':'glossMap','e':'diffuseMap'}[suffix],
           streamable=1,compressionMethod='compressed' if suffix in ('n','g') else 'compressed high color')
    if suffix in ('c','s','e'):f['coreSemantic']='sRGB3chAlpha'
    blocks.append(block(name,'image.gdf',f))
mat=dict(surfaceType='metal',template='material.template',materialCategory='Geometry Advanced',
         materialType='lit_emissive_script_advanced_fullspec',colorMap='i_tod_cyber_sword_c',normalMap='i_tod_cyber_sword_n',
         specColorMap='i_tod_cyber_sword_s',cosinePowerMap='i_tod_cyber_sword_g',colorMap00='i_tod_cyber_sword_e',
         specMapEnable=1,colorTint='1 1 1 1',specColorTint='1 1 1 1',colorTint1='1 1 1 1',
         scaleRGB=12,emissiveIncompetence=1,emissiveFalloff=0,waterRoughness=0,cg00_x=0,cg00_y=0,
         normalHeightScale=1,glossRangeMin=0,glossRangeMax=8,specAmount=.6,reflectionProbeAmount=.35,
         textureAtlasRowCount=1,textureAtlasColumnCount=1,usage='<not in editor>')
blocks.append(block('mtl_tod_cyber_sword','material.gdf',mat))
for name,strength in [('cast',12),('world',0)]:
    f={**mat,'materialType':'lit_emissive_advanced_fullspec','scaleRGB':strength}
    blocks.append(block('mtl_tod_cyber_sword_'+name,'material.gdf',f))
for usage in ('view','world','cast_view','cast_world'):
    f=dict(base['hb_gold_sword_'+('view' if 'view' in usage else 'world')][1])
    for lod,key in enumerate(('filename','mediumLod','lowLod','lowestLod','lod4File','lod5File','lod6File')):
        f[key]='tod_warrior\\\\cyber_sword\\\\tod_cyber_sword_lod'+str(lod)+'.xmodel_bin'
    for key,val in zip(('highLodDist','mediumLodDist','lowLodDist','lowestLodDist','lod4Dist','lod5Dist','lod6Dist'),(0,180,350,600,950,1400,2100)):f[key]=val
    f['skinOverride']=''
    if usage!='view':f['skinOverride']='mtl_tod_cyber_sword mtl_tod_cyber_sword_'+('cast' if usage.startswith('cast') else 'world')
    blocks.append(block('tod_cyber_sword_'+usage,'xmodel.gdf',f))
cast=dict(charged['hb_gold_sword_cast_zm'][1])
cast.update(gunModel='tod_cyber_sword_cast_view',worldModel='tod_cyber_sword_cast_world',displayName='Cyber Sword')
blocks.append(block('tod_cyber_sword_cast_zm','bulletweapon.gdf',cast))
bash=dict(parse(ROOT/'donor_gdt/hellbound/hb_warrior_bash.gdt')['hb_warrior_bash_gold_zm'][1])
bash.update(gunModel='tod_cyber_sword_view',worldModel='tod_cyber_sword_world',displayName='Cyber Sword')
blocks.append(block('tod_cyber_sword_bash_zm','bulletweapon.gdf',bash))
gdt=ROOT/'source_data/tod_cyber_sword.gdt';gdt.write_text('{\n'+''.join(blocks)+'}\n')
(KIT/'install_manifest.json').write_text(json.dumps({**manifest,'donor_skeleton_sha256':sha(DONOR),'bones':[b.name for b in donor.bones],
    'models':records,'gdt_sha256':sha(gdt),'native_playtested':False},indent=2)+'\n')
print('CYBER_SWORD_INSTALLED',[(r['lod'],r['triangles']) for r in records])
