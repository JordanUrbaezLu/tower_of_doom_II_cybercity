"""Reject stale/missing regional models and check the native compiled geometry."""
import pathlib,json,hashlib,csv,argparse
from native_preview import fields
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/cybercity_materials/color_restoration'
p=argparse.ArgumentParser();p.add_argument('--compiled-ledger',type=pathlib.Path);args=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
layout=json.loads((ART/'conduit_mounts.json').read_text());export=json.loads((ART/'conduit_batches.json').read_text())
assert export['layout_sha256']==hashlib.sha256(json.dumps({k:layout[k] for k in ('rows','groups')},sort_keys=True).encode()).hexdigest(),'Re-export models after moving inlays'
assert len(layout['groups'])<=70 and export['channels']==len(layout['rows'])
assert sum(g['count'] for g in layout['groups'])==len(layout['rows'])
for lod,digest in export['sources'].items():assert sha(ROOT/f'model_export/tod_surface/tod_power_conduit_off_lod{lod}.xmodel_bin')==digest
expected={(g['model']+'_'+s,lod) for g in layout['groups'] for s in ('off','on') for lod in (0,1)}
assert {(r['asset'],r['lod']) for r in export['models']}==expected
models={(r['asset'],r['lod']):r for r in export['models']}
ledger={}
if args.compiled_ledger:
 with args.compiled_ledger.open(encoding='utf-8-sig',newline='') as f:ledger={r['name']:r for r in csv.DictReader(f)}
for g in layout['groups']:
 for lod in (0,1):
  off=models[g['model']+'_off',lod];on=models[g['model']+'_on',lod]
  assert off['bounds']==on['bounds'] and off['triangles']==on['triangles']==g['count']*(610 if lod==0 else 436)
 for state in ('off','on'):
  name=g['model']+'_'+state;f=fields(ROOT/'source_data/tod_conduit_batches.gdt',name,'xmodel')
  assert f['CollisionMap']=='' and f['BulletCollisionLOD']=='None'
  for lod,key in [(0,'filename'),(1,'mediumLod')]:
   r=models[name,lod];assert sha(ROOT/r['file'])==r['sha256'],r['file']
   assert r['file']=='model_export/'+f[key]
   if ledger:
    actual=ledger[name];assert int(actual['lodCount'])==2
    assert int(actual['tris'+str(1-lod)])==r['triangles'],(name,lod)
print('CONDUIT_BATCHES_PASS:',len(layout['rows']),'supported inlays;',len(layout['groups']),'nonsolid hosts; all assets fresh; compiled=',bool(ledger))
