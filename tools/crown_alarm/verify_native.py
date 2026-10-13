"""Validate real image bindings, exported meshes and optional native LOD coverage."""
import pathlib,sys,json,hashlib,re,csv,argparse,math,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import xmodel
p=argparse.ArgumentParser();p.add_argument('--compiled-ledger',type=pathlib.Path);args=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((ROOT/'art/crown_alarm/manifest.json').read_text())
profile=json.loads((ROOT/'tools/crown_alarm/light_profile.json').read_text())
assert m['light_profile']==profile
assert m['gdt_sha256']==sha(ROOT/'source_data/tod_crown_alarm.gdt')
assert m['spotlight_sha256']==sha(ROOT/'share/raw/fx/tod/crown_alarm/fx_tod_alarm_sweep.efx')
assert m['high_light_sha256']==sha(ROOT/'share/raw/fx/tod/crown_alarm/fx_tod_alarm_high.efx')
gdt=(ROOT/'source_data/tod_crown_alarm.gdt').read_text()
blocks={name:(kind,dict(re.findall(r'"([^"\n]+)" "([^"\n]*)"',body))) for name,kind,body in re.findall(r'"([^"\n]+)" \( "([^"\n]+).gdf" \)\s*\{(.*?)\n\t\}',gdt,re.S)}
if m.get('lens_repair'):
    assert m['lens_repair'].get('revision')=='2026-10-01 clear glass' and m['lens_repair'].get('native_playtested') is False
    assert blocks['mtl_tod_alarm_lens'][1]['specColorTint']=='.220916 .220916 .220916 1','Clear glass requires its native dielectric tint'
    assert blocks['mtl_tod_alarm_lens'][1]['specColorMap']=='$black_specular','Glass requires a valid scalar nonmetal mask'
    package=(ROOT/'zone_source/tod_crown_alarm.zpkg').read_text().splitlines()
    assert package.count('material,mc/mtl_tod_alarm_lens')==1,'Glass must pack a complete model material, not just a reference'
assert float(blocks['mtl_tod_alarm_lamp_on'][1]['scaleRGB'])==profile['lamp_emission']
high=dict(blocks['mtl_tod_alarm_lamp_on'][1],scaleRGB=str(profile['lamp_emission']*profile['high_lamp_multiplier']))
assert blocks['mtl_tod_alarm_lamp_high_on'][1]==high,'Only high lamp emission may differ'
for name,h in m['textures'].items():assert sha(ROOT/'model_export/tod_crown_alarm/_images'/name)==h
for name,(kind,f) in blocks.items():
    if kind=='material':
        assert f['scaleRGB']=='0' or name in ('mtl_tod_alarm_lamp_on','mtl_tod_alarm_lamp_high_on')
        for key in ['colorMap','colorMap00','normalMap','specColorMap','cosinePowerMap']:
            if name=='mtl_tod_alarm_lens' and key=='specColorMap' and m.get('lens_repair'):
                assert f[key]=='$black_specular','Only the repaired lens may use this stock scalar binding'
                continue
            assert f[key] in blocks and (ROOT/blocks[f[key]][1]['baseImage']).exists(),(name,key)
ledger={}
if args.compiled_ledger:
    with args.compiled_ledger.open(encoding='utf-8-sig',newline='') as f:ledger={r['name']:r for r in csv.DictReader(f)}
    # Linker can print MatchToken/Unknown editor elem yet report success.
    # Require the actual FX asset, not just an orphan lightdescription child.
    asset_ledger=args.compiled_ledger.with_name(args.compiled_ledger.name.replace('_xmodel.csv','.csv'))
    with asset_ledger.open(encoding='utf-8-sig',newline='') as f:
        assetrows=list(csv.DictReader(f))
        fxrow=next((r for r in assetrows if r['name']=='tod/crown_alarm/fx_tod_alarm_sweep'),None)
    assert fxrow and fxrow['type']=='fx','Crown alarm spotlight missing from compiled assets'
    assert any(r['type']=='fx' and r['name']=='tod/crown_alarm/fx_tod_alarm_high' for r in assetrows),'High crown spill missing from compiled assets'
    assert any(r['type']=='material' and r['name']=='mc/mtl_tod_alarm_lamp_high_on' for r in assetrows),'High crown lamp material missing from compiled assets'
counts={}
for r in m['models']:
    path=ROOT/r['file'];assert sha(path)==r['sha256'];model=xmodel.Model();model.LoadFile_Bin(str(path),split_meshes=True)
    assert len(model.bones)==1 and model.bones[0].name=='tag_origin'
    count=sum(len(mesh.faces) for mesh in model.meshes);assert count==r['triangles'];counts.setdefault(r['asset'],[]).append(count)
    for i,mesh in enumerate(model.meshes):
        assert all(v.weights==[(0,1.)] for v in mesh.verts)
        for f in mesh.faces:
            assert f.mesh_id==i and model.materials[f.material_id].name in blocks
            assert all(all(math.isfinite(v) for v in c.normal+c.uv) for c in f.indices)
    if ledger:
        row=ledger[r['asset']];assert int(row['lodCount'])==3
        native=int(row['tris'+str(2-r['lod'])]);assert native==count,(r['asset'],r['lod'],count,native)
for name,c in counts.items():assert all(a>b>0 for a,b in zip(c,c[1:])),(name,c)
for variant in m['variants']:
    source=blocks[variant['source_asset']][1]
    target=blocks[variant['asset']][1]
    assert target==dict(source,skinOverride=variant['skin_override']),'High variant must retain every mesh/LOD setting'
    counts[variant['asset']]=list(counts[variant['source_asset']])
    if ledger:
        row=ledger[variant['asset']];assert int(row['lodCount'])==3
        for lod,count in enumerate(counts[variant['asset']]):
            assert int(row['tris'+str(2-lod)])==count,(variant['asset'],lod)
data=dict(models=len(counts),lod_files=len(m['models']),compiled_lods=sum(len(c) for c in counts.values()),triangles=counts,textures=len(m['textures']),light_profile=profile,native_compiled_checked=bool(ledger),compiled_spotlight_checked=bool(ledger),native_playtested=False)
(ROOT/'art/crown_alarm'/('compiled_validation.json' if ledger else 'source_validation.json')).write_text(json.dumps(data,indent=2))
print('CROWN_ALARM_NATIVE_PASS',json.dumps(data))
if args.compiled_ledger:
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/art_cohesion/verify_conduits.py'),'--compiled-ledger',str(args.compiled_ledger)],cwd=ROOT,check=True)
    if m.get('lens_repair'):
        # A material ledger row can name only a missing/reference asset.
        # Require the real linked glass definition and alpha-preserving mips.
        subprocess.run([sys.executable,'-B',str(ROOT/'tools/crown_alarm/verify_lens_material.py')],cwd=ROOT,check=True)
        subprocess.run([sys.executable,'-B',str(ROOT/'tools/crown_alarm/verify_lens_conversion.py')],cwd=ROOT,check=True)
