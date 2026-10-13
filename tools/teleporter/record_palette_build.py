"""Read-only audit of the lead's finished teleporter color build."""
import argparse,csv,hashlib,json,sqlite3,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];MT=Path('C:/BO3Tools/TOD2Cybercity')
DEP=MT/'usermaps/zm_tod2_cybercity';OUT=ROOT/'art/teleporter/status_colors'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--build-log',required=True);args=p.parse_args()
# Existing receipt checks build log/freshness, installed hashes, accepted
# fullspec settings, packed materials/images and all compiled body LODs.
subprocess.run([sys.executable,'-B',str(ROOT/'tools/teleporter/record_surface_build.py'),'--build-log',args.build_log],cwd=ROOT,check=True)
subprocess.run([sys.executable,'-B',str(ROOT/'tools/teleporter/verify_palette.py')],cwd=ROOT,check=True)
record=json.loads((ROOT/'art/teleporter/surface_repair/deployment.json').read_text())
ff=DEP/'zone/zm_tod2_cybercity.ff'
assert record['ff_sha256']==sha(ff),'Another build replaced the FF during the audit'
assert ff.stat().st_mtime>(ROOT/'art/teleporter/teleporter_cyber.blend').stat().st_mtime
fx=[]
for src in (ROOT/'share/raw/fx/tod/teleporter').glob('*.efx'):
    rel=src.relative_to(ROOT);dst=MT/rel
    assert dst.exists() and sha(src)==sha(dst),(rel,'effect source/deployed mismatch')
    assert dst.stat().st_mtime<=ff.stat().st_mtime,(rel,'synced after FF')
    record['inputs'][rel.as_posix()]=sha(src);fx.append('tod/teleporter/'+src.stem)
ledger=DEP/'zone_source/all/assetinfo/zm_tod2_cybercity.csv'
with ledger.open(encoding='utf-8-sig',newline='') as f:names={r['name'] for r in csv.DictReader(f)}
assert set(fx)<=names,sorted(set(fx)-names)
db=sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro',uri=True)
db.execute('pragma writable_schema=ON');db.row_factory=sqlite3.Row
palette=json.loads((ROOT/'tools/teleporter/state_palette.json').read_text())
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
for band,strength in enumerate((5.5,2.3,.75)):
    name='mtl_tod_tp_charge_'+str(band)
    row=db.execute('select _name,colorTint1,scaleRGB,waterRoughness from material where _name=?',(name,)).fetchone()
    assert row,name
    rgb=[linear(float(v)) for v in row['colorTint1'].split()[:3]]
    assert all(abs(a-b)<1e-5 for a,b in zip(rgb,palette['pending_linear'])),(name,rgb)
    assert row['scaleRGB']==strength and row['waterRoughness']==0
    record['materials'][name]=dict(row)
db.close()
record.update(palette=palette,packed_status_effects=sorted(fx),user_accepted_metal_finish=True,
    new_status_colors_user_verified=False,native_visual_verified=False,game_launched=False)
(OUT/'deployment.json').write_text(json.dumps(record,indent=2)+'\n')
print('TELEPORTER_COLORS_DEPLOYED: green ready, yellow pending, no-power off; USER COLOR TEST PENDING')
