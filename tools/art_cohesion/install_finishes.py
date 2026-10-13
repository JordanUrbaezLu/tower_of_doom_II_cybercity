"""Update only native finish fields; preserve all geometry, images and power states."""
import pathlib,json,hashlib,re
from profiles import PROFILES,VERSION
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'art/cybercity_materials';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
targets=[('tod_teleporter.gdt','mtl_tod_teleporter','teleporter','art/teleporter/engine_kit/install_manifest.json'),('tod_teleporter_states.gdt','mtl_tod_tp_off','teleporter','art/teleporter/engine_kit/states_manifest.json'),('tod_heavenly_altar.gdt','mtl_tod_altar','altar','art/heavenly_altar/engine_kit/install_manifest.json')]
before={};changes=[]
for file,name,role,manifest in targets:
    p=ROOT/'source_data'/file;text=p.read_text();pattern=r'("'+name+r'"\s*\(\s*"material.gdf"\s*\)\s*\{)(.*?)(\n\s*\})'
    match=re.search(pattern,text,re.S);assert match,name
    fields=dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"',match.group(2)))
    before[name]={k:fields[k] for k in PROFILES[role]};body=match.group(2)
    for k,v in PROFILES[role].items():
        body,n=re.subn(r'("'+k+r'")\s+"[^"\n]*"',lambda m:m.group(1)+' "'+str(v)+'"',body);assert n==1,k
    replacement=match.group(1)+body+match.group(3);text=text[:match.start()]+replacement+text[match.end():];p.write_text(text)
    mp=ROOT/manifest;m=json.loads(mp.read_text());m['gdt_sha256']=sha(p);m['finish_profile']=VERSION;m['native_playtested']=False;mp.write_text(json.dumps(m,indent=2)+'\n')
    changes.append({'material':name,'before':before[name],'after':PROFILES[role],'gdt_sha256':sha(p)})
checkpoint=OUT/'finish_before.json'
if not checkpoint.exists():checkpoint.write_text(json.dumps(before,indent=2))
(OUT/'finish_changes.json').write_text(json.dumps({'version':VERSION,'materials':changes,'geometry_changed':False,'images_changed':False,'native_playtested':False},indent=2))
print('NATIVE_FINISHES_INSTALLED',VERSION,'teleporter ready/off + altar; geometry and color/state maps retained')
