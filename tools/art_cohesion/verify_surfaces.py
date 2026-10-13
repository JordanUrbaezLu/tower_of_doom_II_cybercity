"""Cheap build gate: bake provenance, image dimensions, native profile and bindings."""
import hashlib,json,pathlib,struct,subprocess,sys
from profiles import PROFILES
from native_preview import fields
from surface_definition import DEFINITIONS,definition
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/cybercity_materials'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((ART/'install_manifest.json').read_text());gdt=ROOT/'source_data/tod_surface.gdt'
assert sha(gdt)==m['gdt_sha256'] and sha(ROOT/m['master'])==m['master_sha256']
assert len(m['textures'])==45 and m['tile_units']==128   # 30 kit maps + the 15 scorched tiles (docs/205 s7b)
for src in m['sources']:
    assert sha(ROOT/src['master'])==src['master_sha256']
    for name,digest in src['textures'].items():assert m['textures'][name]==digest
for name,digest in m['textures'].items():
    p=ROOT/'model_export/tod_surface/_images'/name;assert sha(p)==digest,name
    data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',data[16:24])==(1024,1024)
    f=fields(gdt,p.stem,'image');suffix=p.stem.rsplit('_',1)[1]
    assert f['semantic']=={'c':'diffuseMap','n':'normalMap','s':'specularMap','g':'glossMap','e':'diffuseMap'}[suffix]
    assert (f.get('coreSemantic')=='sRGB3chAlpha')==(suffix in 'cse'),name
for role,d in DEFINITIONS.items():
    f=fields(gdt,'tod_cc_'+role)
    for key,val in definition(role).items():
        assert (f[key]==val if isinstance(val,str) else float(f[key])==val),(role,key)
    assert f['materialType']=='lit_emissive_advanced_fullspec'
maptext=(ROOT/'map_source/zm/zm_tod2_cybercity.map').read_text(encoding='utf-8-sig')
for kind in ('floor','wall','gold','gold_panel','brass','ceramic','ruby','sapphire','emerald','gold_deck','door'):assert ' tod_cc_'+kind+' ' in maptext
assert ' tod_cc_tower_red_floor_scorched ' in maptext and ' tod_cc_oxblood_scorched ' in maptext,'the breaks wear no scorched twins (docs/205 s7b)'
assert all(float(fields(gdt,'tod_cc_'+role)['scaleRGB'])==0 for role in DEFINITIONS)
print('CYBERCITY_SURFACES_PASS: three source libraries, 45 maps, all native color roles and blackout-compatible zero emission')
subprocess.run(['node',str(ROOT/'tools/art_cohesion/test_conduits.js')],cwd=ROOT,check=True)
subprocess.run([sys.executable,'-B',str(ROOT/'tools/art_cohesion/verify_conduits.py')],cwd=ROOT,check=True)
subprocess.run(['node',str(ROOT/'tools/art_cohesion/verify_tower_design.js')],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
print('WHOLE_TOWER_COVERAGE_PASS: all world and entity surfaces audited; only trial signs exempt')
