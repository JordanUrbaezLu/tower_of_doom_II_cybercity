"""Snapshot exact build inputs, then prove deployment and packed asset coverage."""
import sys,json,hashlib,csv,datetime,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];MT=Path('C:/BO3Tools/TOD2Cybercity');DEP=MT/'usermaps/zm_tod2_cybercity';OUT=ROOT/'tmp/partner_shop_build';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
    for d in ('scripts','ui','zone_source','sound','model_export/tod_shop','model_export/tod_teleporter','share/raw/fx/tod/shop','share/raw/fx/tod/teleporter','sound_assets/tod/shop'):
        for p in (ROOT/d).rglob('*'):
            if p.is_file() and not any(x in ('all','english','loc','__pycache__') for x in p.relative_to(ROOT/d).parts):yield p
    for p in ('source_data/tod_shop.gdt','source_data/tod_teleporter.gdt','source_data/tod_teleporter_states.gdt','source_data/tod_materials.gdt','source_data/tod_skybox.gdt','source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr','map_source/zm/zm_tod2_cybercity.map'):yield ROOT/p
snap=OUT/'input_snapshot.json'
if '--snapshot' in sys.argv:
    snap.write_text(json.dumps({p.relative_to(ROOT).as_posix():sha(p) for p in inputs()},indent=2));print('SHOP_BUILD_SNAPSHOT',snap);raise SystemExit
snapshot=json.loads(snap.read_text());ff=DEP/'zone/zm_tod2_cybercity.ff';stamp=ff.stat().st_mtime;assert stamp>snap.stat().st_mtime
bad=[];newer=[]
assert set(snapshot)=={p.relative_to(ROOT).as_posix() for p in inputs()}
for name,digest in snapshot.items():
    p=Path(name);target=(MT if p.parts[0] in ('source_data','model_export','share','sound_assets','map_source') else DEP)/p
    if sha(ROOT/p)!=digest:bad.append('source_changed:'+name)
    if not target.exists() or sha(target)!=digest:bad.append('deployed_mismatch:'+name)
    if target.exists() and target.stat().st_mtime>stamp:newer.append(name)
names=set()
for lang in ('all','english'):
    p=DEP/'zone_source'/lang/'assetinfo/zm_tod2_cybercity.csv';assert p.stat().st_mtime>snap.stat().st_mtime
    with p.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):names.add(r['name'].removeprefix('mc/').removeprefix('wc/') if r['type']=='material' else r['name'])
m=json.loads((ROOT/'art/partner_shop/engine_kit/install_manifest.json').read_text())
expected={r['asset'] for r in m['models']}|{'mtl_tod_shop_'+g for g in ('body','vendor','glow','glow_off')}|{Path(n).stem for n in m['textures']}|{'tod/shop/fx_tod_shop_spark','zombie/fx_wonder_fizz_lightning_all'}
tp=json.loads((ROOT/'art/teleporter/engine_kit/install_manifest.json').read_text())
expected|={'tod_teleporter','tod_teleporter_off','tod_tp_recharge','mtl_tod_teleporter','mtl_tod_tp_off'}|{'mtl_tod_tp_charge_'+str(i) for i in range(3)}|{Path(n).stem for n in tp['textures']}
expected|={'tod/teleporter/'+n for n in ('fx_tod_tp_ready','fx_tod_tp_charge_field','fx_tod_tp_release_field')}
expected.update(re.findall(r'\)\s+(tod_dark_\w+)\s', (ROOT/'map_source/zm/zm_tod2_cybercity.map').read_text()))
missing=sorted(expected-names);banks={str(p.relative_to(DEP/'zone')):p.stat().st_size for p in (DEP/'zone/snd').rglob('*') if p.is_file()}
alias_file=DEP/'sound/zone/zm_tod2_cybercity.all.alias.sz';assert alias_file.stat().st_mtime>snap.stat().st_mtime
with alias_file.open(encoding='utf-8-sig',newline='') as f:aliases={r['Name']:r for r in csv.DictReader(f)}
sound_assets=set((DEP/'sound/zone/zm_tod2_cybercity.all.assets.sz').read_text().splitlines());audio=[]
for i in range(1,4):
    name='tod_shop_spark_'+str(i);r=aliases[name]
    for key,value in {'PanType':'3d','Storage':'loaded','StartDelay':'0','PitchMin':'0','PitchMax':'0','StopOnEntDeath':'true','Pauseable':'true','Bus':'bus_fx'}.items():assert r[key].lower()==value,(name,key,r[key])
    assert r['FileTarget'] in sound_assets
    audio.append({'alias':name,'asset':r['FileTarget'],'pitch_offset':0,'start_delay':0,'positional':True})
report={'ff_bytes':ff.stat().st_size,'ff_time':datetime.datetime.fromtimestamp(stamp).isoformat(),'inputs':len(snapshot),'differences':bad,'deployed_inputs_newer_than_ff':newer,'missing_assets':missing,'banks':banks,'audio':audio,'game_launched':False,'native_visual_verified':False}
(OUT/'deployment.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert not bad and not newer and not missing
