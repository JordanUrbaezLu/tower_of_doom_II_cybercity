"""Prove a fresh build contains the snapshotted scripts, UI and teleporter kit."""
import sys,json,hashlib,datetime,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];MT=Path('C:/BO3Tools/TOD2Cybercity');DEP=MT/'usermaps/zm_tod2_cybercity';OUT=ROOT/'tmp/teleporter_fx_20260922';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
    for directory in ('scripts','ui','zone_source','model_export/tod_teleporter','share/raw/fx/tod/teleporter','sound','vision'):
        for p in (ROOT/directory).rglob('*'):
            if p.is_file() and not any(x in ('all','english','loc','__pycache__') for x in p.relative_to(ROOT/directory).parts):yield p
    yield ROOT/'source_data/tod_teleporter.gdt'
    yield ROOT/'source_data/tod_materials.gdt'
    yield ROOT/'map_source/zm/zm_tod2_cybercity.map'
    yield ROOT/'source_data/tod_skybox.gdt'
    yield ROOT/'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'
snap=OUT/'input_snapshot.json'
if '--snapshot' in sys.argv:
    snap.write_text(json.dumps({p.relative_to(ROOT).as_posix():sha(p) for p in inputs()},indent=2));print('TELEPORTER_SNAPSHOT',snap);raise SystemExit
m=json.loads((ROOT/'art/teleporter/engine_kit/install_manifest.json').read_text());snapshot=json.loads(snap.read_text());ff=DEP/'zone/zm_tod2_cybercity.ff';stamp=ff.stat().st_mtime;assert stamp>snap.stat().st_mtime
bad=[];newer=[]
assert set(snapshot)=={p.relative_to(ROOT).as_posix() for p in inputs()}
for name,digest in snapshot.items():
    rel=Path(name);target=(MT if rel.parts[0] in ('source_data','model_export','share','map_source') else DEP)/rel
    if sha(ROOT/rel)!=digest:bad.append('source_changed:'+name)
    if not target.exists() or sha(target)!=digest:bad.append('deployed_mismatch:'+name)
    if target.exists() and target.stat().st_mtime>stamp:newer.append(name)
names=set()
for lang in ('all','english'):
    path=DEP/'zone_source'/lang/'assetinfo/zm_tod2_cybercity.csv';assert path.stat().st_mtime>snap.stat().st_mtime
    with path.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):names.add(row['name'].removeprefix('mc/') if row['type']=='material' else row['name'])
missing=sorted({m['asset'],'mtl_tod_teleporter',*(Path(n).stem for n in m['textures']),*(f'tod/teleporter/{n}' for n in ('fx_tod_tp_ready','fx_tod_tp_charge_field','fx_tod_tp_release_field'))}-names)
banks={p.name:p.stat().st_size for p in (DEP/'zone/snd/all').glob('*') if p.is_file()}
report={'ff_bytes':ff.stat().st_size,'ff_local_time':datetime.datetime.fromtimestamp(stamp).isoformat(),'snapshot_inputs':len(snapshot),'differences':bad,'deployed_inputs_newer_than_ff':newer,'missing_assets':missing,'sound_banks':banks,'placements':9,'game_launched':False,'native_visual_verified':False}
(OUT/'deployment_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not bad and not newer and not missing
