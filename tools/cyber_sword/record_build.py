"""Read-only receipt after a lead-cleared build; requires the actual compiled sword."""
import argparse,csv,datetime,json,sqlite3,subprocess,sys
from common import *
MT=Path('C:/BO3Tools/TOD2Cybercity');DEP=MT/'usermaps/zm_tod2_cybercity'
parser=argparse.ArgumentParser();parser.add_argument('--build-log',required=True);args=parser.parse_args()
log=ROOT/args.build_log;raw=log.read_bytes();text=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
assert '[build] === BUILD OK ===' in text
ff=DEP/'zone/zm_tod2_cybercity.ff';stamp=ff.stat().st_mtime
assert abs(stamp-log.stat().st_mtime)<180,'build log is not the current FF'
subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('verify_native.py')),'--integrated'],check=True,cwd=ROOT)
inputs=list(OUT.rglob('*.png'))+list(OUT.glob('*.xmodel_bin'))+[ROOT/'source_data/tod_cyber_sword.gdt',ROOT/'source_data/tod_weapon_twins.gdt',ROOT/'zone_source/tod_cyber_sword.zpkg',ROOT/'zone_source/zm_tod2_cybercity.zone',ROOT/'scripts/zm/zm_tod2_cybercity.csc']
inputs.extend(ROOT/'scripts/zm/zm_tod2_cybercity'/name for name in ('_tod_class_kit.gsc','_tod_cyber_sword.gsc','_tod_cyber_sword.csc'))
hashes={}
for src in inputs:
    rel=src.relative_to(ROOT);dst=(DEP if rel.parts[0] in ('scripts','zone_source') else MT)/rel
    assert dst.is_file() and sha(src)==sha(dst),(str(rel),'deployed mismatch')
    assert dst.stat().st_mtime<=stamp,(str(rel),'post-FF sync')
    hashes[rel.as_posix()]=sha(src)
ledger=DEP/'zone_source/all/assetinfo/zm_tod2_cybercity.csv'
assert abs(ledger.stat().st_mtime-stamp)<180
with ledger.open(encoding='utf-8-sig',newline='') as f:names={r['name'] for r in csv.DictReader(f)}
required=set(parse(ROOT/'source_data/tod_cyber_sword.gdt'))
required={('mc/'+n if n.startswith('mtl_') else n) for n in required}
assert not required-names,sorted(required-names)
with ledger.with_name('zm_tod2_cybercity_xmodel.csv').open(encoding='utf-8-sig',newline='') as f:models={r['name']:r for r in csv.DictReader(f)}
counts=json.loads((KIT/'lod_counts.json').read_text())
for name in ('view','world','cast_view','cast_world'):
    row=models['tod_cyber_sword_'+name];assert int(row['lodCount'])==7
    for lod in range(7):
        # Assetinfo lists native LOD slots in reverse order (far -> high).
        expected=counts[str(lod)]['solid'];got=int(row['tris'+str(6-lod)])
        assert 0<=expected-got<=8,(name,lod,expected,got)
db=sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro',uri=True);db.execute('pragma writable_schema=ON')
for name,strength in [('mtl_tod_cyber_sword',12),('mtl_tod_cyber_sword_cast',12),('mtl_tod_cyber_sword_world',0)]:
    row=db.execute('select waterRoughness,scaleRGB,glossRangeMax from material where _name=?',(name,)).fetchone()
    assert row==(0,strength,8),(name,row)
db.close()
(ART/'deployment.json').write_text(json.dumps(dict(build_log=args.build_log,ff_sha256=sha(ff),ff_bytes=ff.stat().st_size,
    recorded=datetime.datetime.now().isoformat(),inputs=hashes,packed_assets=sorted(required),native_built=True,native_playtested=False),indent=2))
print('CYBER_SWORD_DEPLOYED: bindings, seven compiled LODs, native materials, source/deployed hashes; user playtest pending')
