"""Read-only native audit for the color restoration and power-controlled wires."""
import pathlib,json,hashlib,csv,datetime,argparse,sys,subprocess
from native_preview import fields
ROOT=pathlib.Path(__file__).resolve().parents[2];MT=pathlib.Path('C:/BO3Tools/TOD2Cybercity');MAP='zm_tod2_cybercity';DEP=MT/'usermaps'/MAP;ART=ROOT/'art/cybercity_materials/color_restoration'
p=argparse.ArgumentParser();p.add_argument('--build-log',required=True);p.add_argument('--followup-log');p.add_argument('--full-inputs');args=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
log=ROOT/args.build_log;raw=log.read_bytes();text=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
assert '[build] === BUILD OK ===' in text
assert 'FULL geometry' in text,'Material colors need a fresh LED bake'
finish=log
if args.followup_log:
 assert args.full_inputs,'A script follow-up needs the preserved FULL-build input snapshot'
 captured=json.loads((ROOT/args.full_inputs).read_text(encoding='utf-8-sig'))['inputs']
 for name,digest in captured.items():
  if not name.startswith(('scripts/','ui/','zone_source/')):assert sha(ROOT/name)==digest,('art changed after FULL build',name)
 finish=ROOT/args.followup_log;raw=finish.read_bytes();followup=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
 assert '[build] === BUILD OK ===' in followup and 'GSC-ONLY' in followup
ff=DEP/'zone'/(MAP+'.ff');stamp=ff.stat().st_mtime;assert abs(stamp-finish.stat().st_mtime)<180
pairs=[]
for folder in ['scripts','ui','zone_source','sound','animtables']:
 for src in (ROOT/folder).rglob('*'):
  if src.is_file():pairs.append((src,DEP/src.relative_to(ROOT)))
for folder in ['model_export/tod_surface']:
 for src in (ROOT/folder).rglob('*'):
  if src.is_file():pairs.append((src,MT/src.relative_to(ROOT)))
for rel in ['source_data/tod_surface.gdt','source_data/tod_power_conduits.gdt','source_data/tod_conduit_batches.gdt','map_source/zm/'+MAP+'.map']:
 pairs.append((ROOT/rel,MT/rel))
for src,dst in pairs:
 assert dst.exists() and sha(src)==sha(dst),('deployment differs',str(src))
 assert dst.stat().st_mtime<=stamp,('synced after FF',str(dst))
ledger=next(DEP.glob('zone_source/*/assetinfo/'+MAP+'.csv'))
with ledger.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
assets={(r['type'],r['name']) for r in rows}
world=json.loads((ROOT/'docs/tower_design/source_validation.json').read_text())
world_materials=[n for n in world['material_faces'] if n.startswith('tod_cc_')]+['tod_cc_door']
for name in world_materials:assert ('material','wc/'+name) in assets,name
for name in ['tod_power_conduit_off','tod_power_conduit_on']:assert ('xmodel',name) in assets,name
for name in ['shell','steel','rubber','wire_off','wire_on']:
 assert ('material','mc/mtl_tod_conduit_'+name) in assets,name
 for suffix in ['c','n','g','s']:assert ('image','i_tod_conduit_'+name+'_'+suffix) in assets,(name,suffix)
subprocess.run([sys.executable,'-B',str(ROOT/'tools/art_cohesion/verify_conduits.py'),'--compiled-ledger',str(ledger.with_name(MAP+'_xmodel.csv'))],check=True)
sys.path.insert(0,str(ROOT/'tools/cyber_elites'));from inspect_assets import asset
from surface_definition import DEFINITIONS,definition
for name in DEFINITIONS:
 native=asset('material','tod_cc_'+name)
 for key,value in definition(name).items():assert (native[key]==value if isinstance(value,str) else float(native[key])==value),(name,key)
for name in ['wire_on','wire_off']:
 assert float(asset('material','mtl_tod_conduit_'+name)['scaleRGB'])==(8 if name=='wire_on' else 0)
layout=json.loads((ART/'conduit_mounts.json').read_text())
data=dict(ff_bytes=ff.stat().st_size,ff_sha256=sha(ff),ff_time=datetime.datetime.fromtimestamp(stamp).isoformat(),build_log=args.build_log,script_followup_log=args.followup_log,inputs_matched=len(pairs),conduit_fixtures=len(layout['rows']),conduit_hosts=len(layout['groups']),conduit_models=2+2*len(layout['groups']),conduit_lods=6+4*len(layout['groups']),conduit_images=20,world_materials=len(set(world_materials)),game_launched=False,native_visual_verified=False)
(ART/'deployment.json').write_text(json.dumps(data,indent=2));print('COLOR_POWER_DEPLOYMENT_PASS',json.dumps(data))
