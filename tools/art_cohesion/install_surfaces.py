"""Install the Blender-authored kit as private, world-capable BO3 materials."""
import hashlib,json,pathlib
from profiles import apply,VERSION
from surface_definition import DEFINITIONS,definition
ROOT=pathlib.Path(__file__).resolve().parents[2]
ART=ROOT/'art/cybercity_materials'
manifest=json.loads((ART/'bake_manifest.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/manifest['master'])==manifest['master_sha256']
crown=json.loads((ART/'crown_bake_manifest.json').read_text())
assert sha(ROOT/crown['master'])==crown['master_sha256']
scorch=json.loads((ROOT/'art/war_damage/scorch_manifest.json').read_text())   # THE WAR DAMAGE PASS phase 2 (docs/205 s7b): the burned tiles
assert sha(ROOT/scorch['master'])==scorch['master_sha256']
manifest['sources']=[{k:m[k] for k in ('master','master_sha256','textures')} for m in (manifest,crown,scorch)]
manifest['textures']={**manifest['textures'],**crown['textures'],**scorch['textures']}
blocks=[]
def entry(name,kind,fields):
    blocks.append('\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v)+'"\n' for k,v in fields.items())+'\t}\n')
for kind in ('floor','wall','ceiling','trim','armor','crystal','floor_scorch','wall_scorch','armor_scorch'):
    prefix='i_tod_cc_'+kind
    for suffix,semantic in [('c','diffuseMap'),('n','normalMap'),('s','specularMap'),('g','glossMap'),('e','diffuseMap')]:
        name=prefix+'_'+suffix;p=ROOT/'model_export/tod_surface/_images'/(name+'.png')
        assert sha(p)==manifest['textures'][p.name],p
        fields={'baseImage':'model_export\\\\tod_surface\\\\_images\\\\'+p.name,'imageType':'Texture','type':'image','semantic':semantic,'streamable':1,'compressionMethod':'compressed' if suffix in 'ng' else 'compressed high color'}
        if suffix not in 'ng':fields['coreSemantic']='sRGB3chAlpha'
        entry(name,'image',fields)
for role in DEFINITIONS:entry('tod_cc_'+role,'material',definition(role))
dest=ROOT/'source_data/tod_surface.gdt';dest.write_text('{\n'+''.join(blocks)+'}\n')
manifest.update(gdt_sha256=sha(dest),finish_profile=VERSION,native_visual_approved=False)
(ART/'install_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('CYBERCITY_SURFACES_INSTALLED',len(DEFINITIONS),'materials,',len(manifest['textures']),'maps, complete crown + the scorched tiles; world emission off')
