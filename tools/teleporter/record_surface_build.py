"""Read-only native audit after Archer's cleared build; never launches BO3."""
import argparse, csv, datetime, hashlib, json, sqlite3, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; MT=Path('C:/BO3Tools/TOD2Cybercity')
DEP=MT/'usermaps/zm_tod2_cybercity'; OUT=ROOT/'art/teleporter/surface_repair'
sys.path.insert(0,str(ROOT/'tools'))
from art_cohesion.profiles import PROFILES
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser(); p.add_argument('--build-log'); p.add_argument('--inspect-current',action='store_true'); args=p.parse_args()
assert args.inspect_current or args.build_log,'Supply --build-log after the cleared build, or --inspect-current for a baseline'
db=sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro',uri=True)
db.execute('pragma writable_schema=ON'); db.row_factory=sqlite3.Row
keys=['_name','materialType','waterRoughness','glossRangeMin','glossRangeMax','specAmount','specColorTint','reflectionProbeAmount','colorMap00','scaleRGB']
materials={}
for name in ['mtl_tod_teleporter','mtl_tod_tp_off']:
    row=db.execute('select '+','.join(keys)+' from material where _name=?',(name,)).fetchone()
    assert row,name; materials[name]=dict(row)
db.close()
ff=DEP/'zone/zm_tod2_cybercity.ff'
record=dict(materials=materials,ff_time=datetime.datetime.fromtimestamp(ff.stat().st_mtime).isoformat(),ff_bytes=ff.stat().st_size,
            native_visual_verified=False,game_launched=False)
if args.inspect_current:
    path=OUT/'deployed_before.json'
    assert not path.exists(),'Preserve the original native baseline'
    path.write_text(json.dumps(record,indent=2)+'\n'); print(json.dumps(record,indent=2)); raise SystemExit
log=ROOT/args.build_log; raw=log.read_bytes(); text=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
assert '[build] === BUILD OK ===' in text,'Guarded build must succeed first'
assert abs(ff.stat().st_mtime-log.stat().st_mtime)<180,'Log does not belong to deployed FF'
for name,fields in materials.items():
    for key,value in PROFILES['teleporter'].items(): assert fields[key]==value,(name,key,fields[key],value)
    assert fields['colorMap00']==('i_tod_teleporter_e' if name.endswith('_off') else 'i_tod_teleporter_ready_e')
    assert fields['scaleRGB']==(0 if name.endswith('_off') else 6)
inputs=[p for p in (ROOT/'model_export/tod_teleporter').rglob('*') if p.is_file()]
inputs += [ROOT/'source_data'/n for n in ['tod_teleporter.gdt','tod_teleporter_states.gdt']]
inputs += [ROOT/'scripts/zm/zm_tod2_cybercity/_tod_teleport.gsc',ROOT/'zone_source/tod_teleporter_states.zpkg']
checked={}
for src in inputs:
    rel=src.relative_to(ROOT); dst=(DEP if rel.parts[0] in ('scripts','zone_source') else MT)/rel
    assert dst.exists() and sha(src)==sha(dst),(rel,'source/deployed mismatch')
    assert dst.stat().st_mtime<=ff.stat().st_mtime,(rel,'synced after FF')
    checked[rel.as_posix()]=sha(src)
ledger=DEP/'zone_source/all/assetinfo/zm_tod2_cybercity.csv'
assert abs(ledger.stat().st_mtime-ff.stat().st_mtime)<180,'Stale asset ledger'
with ledger.open(encoding='utf-8-sig',newline='') as f: names={r['name'] for r in csv.DictReader(f)}
required={'tod_teleporter','tod_teleporter_off','tod_tp_recharge','mc/mtl_tod_teleporter','mc/mtl_tod_tp_off'}
required.update(p.stem for p in (ROOT/'model_export/tod_teleporter/_images').glob('*.png'))
required.update('mc/mtl_tod_tp_charge_'+str(i) for i in range(3))
assert not required-names,sorted(required-names)
model_ledger=ledger.with_name(ledger.stem+'_xmodel.csv')
assert abs(model_ledger.stat().st_mtime-ff.stat().st_mtime)<180,'Stale xmodel ledger'
subprocess.run([sys.executable,'-B',str(ROOT/'tools/teleporter/verify_native.py'),'--compiled-ledger',str(model_ledger)],check=True,cwd=ROOT)
record.update(build_log=args.build_log,build_log_sha256=sha(log),ff_sha256=sha(ff),inputs=checked,packed_assets=sorted(required),native_built=True)
(OUT/'deployment.json').write_text(json.dumps(record,indent=2)+'\n')
print('TELEPORTER_SURFACE_DEPLOYED: depth=0, gloss=0..6, shared seven body LODs and recharge; USER VISUAL TEST PENDING')
