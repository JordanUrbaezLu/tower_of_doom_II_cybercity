"""Set an explicit surface glow depth and satin finish; never sync or build."""
import hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art/teleporter/surface_repair'; OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools'))
from art_cohesion.profiles import PROFILES
from art_cohesion.native_preview import fields
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
targets=[('tod_teleporter.gdt','mtl_tod_teleporter','install_manifest.json'),
         ('tod_teleporter_states.gdt','mtl_tod_tp_off','states_manifest.json')]
inputs=list((ROOT/'model_export/tod_teleporter').rglob('*.png'))+list((ROOT/'model_export/tod_teleporter').glob('*.xmodel_bin'))
inputs += [ROOT/'scripts/zm/zm_tod2_cybercity/_tod_teleport.gsc',ROOT/'art/teleporter/teleporter_cyber.blend']
unchanged={p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
checkpoint=OUT/'before.json'
if not checkpoint.exists():
    before={name:fields(ROOT/'source_data'/file,name) for file,name,_ in targets}
    checkpoint.write_text(json.dumps(dict(materials=before,unchanged_inputs=unchanged),indent=2)+'\n')
previous=json.loads(checkpoint.read_text())
for file,name,manifest in targets:
    path=ROOT/'source_data'/file; text=path.read_text()
    pattern=r'("'+re.escape(name)+r'"\s*\(\s*"material.gdf"\s*\)\s*\{)(.*?)(\n\s*\})'
    match=re.search(pattern,text,re.S); assert match,name
    body=match[2]
    for key,value in PROFILES['teleporter'].items():
        body,count=re.subn(r'("'+key+r'")\s+"[^"\r\n]*"',lambda m:m[1]+' "'+str(value)+'"',body)
        if not count: body+='\n\t\t"'+key+'" "'+str(value)+'"'
        assert count<=1,(name,key)
    text=text[:match.start()]+match[1]+body+match[3]+text[match.end():]
    path.write_text(text)
    after=fields(path,name)
    assert {k:v for k,v in after.items() if k not in PROFILES['teleporter']} == {k:v for k,v in previous['materials'][name].items() if k not in PROFILES['teleporter']}
    p=ROOT/'art/teleporter/engine_kit'/manifest; data=json.loads(p.read_text())
    data.update(gdt_sha256=sha(path),surface_profile='teleporter-surface-2',native_playtested=False)
    p.write_text(json.dumps(data,indent=2)+'\n')
assert unchanged=={p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
assert previous['unchanged_inputs']==unchanged,'Geometry, images, master or state script drifted during this repair'
report=dict(profile='teleporter-surface-2',materials={name:fields(ROOT/'source_data'/file,name) for file,name,_ in targets},
            unchanged_inputs=unchanged,source_gdt_hashes={file:sha(ROOT/'source_data'/file) for file,_,_ in targets},
            native_built=False,native_visual_verified=False,
            diagnosis='Native default layerDepth=0.1 conflicts with surface-aligned atlas emission. Screenshot cause inferred; user retest required.')
(OUT/'source_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('TELEPORTER_SURFACE_READY depth=0 gloss=0..6; '+str(len(unchanged))+' unchanged inputs; NOT BUILT')
