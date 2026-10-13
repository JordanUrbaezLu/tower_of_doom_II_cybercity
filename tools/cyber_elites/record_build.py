"""Read-only deployment audit; writes evidence into this repo after a full build."""
import pathlib,json,hashlib,datetime,csv,argparse
from inspect_assets import ROOT,MT,asset
MAP='zm_tod2_cybercity';DEPLOY=MT/'usermaps'/MAP
parser=argparse.ArgumentParser();parser.add_argument('--build-log',default='tmp/cyber_elites_full_build.log');parser.add_argument('--output',default='art/cyber_elites/deployment.json');args=parser.parse_args()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
ff=DEPLOY/'zone'/f'{MAP}.ff';stamp=ff.stat().st_mtime
log=ROOT/args.build_log;raw=log.read_bytes();text=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
assert '[build] === BUILD OK ===' in text,'Guarded build must succeed first'
assert abs(stamp-log.stat().st_mtime)<180,'Build log does not belong to the deployed FF'
pairs=[]
for folder in ['scripts','ui','zone_source','sound','animtables']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file():pairs.append((p,DEPLOY/p.relative_to(ROOT)))
for folder in ['model_export/tod_cyber_elites','share/raw/fx/hb/mangler']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file():pairs.append((p,MT/p.relative_to(ROOT)))
for rel in ['source_data/tod_cyber_elites.gdt','map_source/zm/'+MAP+'.map']:
    pairs.append((ROOT/rel,MT/rel))
for table in ['hb_mangler.csv','hb_bo6_mangler.csv']:
    path=ROOT/'sound/aliases'/table;pairs.append((path,MT/'share/raw/sound/aliases'/table))
    with path.open(newline='') as f:
        for row in csv.DictReader(f):
            rel=pathlib.Path('sound_assets')/row['FileSpec'].replace('\\','/')
            pairs.append((ROOT/rel,MT/rel))
matched=[]
for source,target in pairs:
    assert target.exists() and sha(source)==sha(target),(source,target,'deployment drift')
    assert target.stat().st_mtime<=stamp,(target,'synced after FF')
    matched.append(dict(file=source.relative_to(ROOT).as_posix(),sha256=sha(source)))
ledger=next(DEPLOY.glob('zone_source/*/assetinfo/'+MAP+'_xmodel.csv'))
with ledger.open(encoding='utf-8-sig',newline='') as f:rows={r['name']:r for r in csv.DictReader(f)}
manifest=json.loads((ROOT/'art/cyber_elites/manifest.json').read_text())
models={r['name']:rows[r['name']] for r in manifest['models']};models['hb_bo6_mangler']=rows['hb_bo6_mangler']
with ledger.with_name(MAP+'.csv').open(encoding='utf-8-sig',newline='') as f:
    assets=list(csv.DictReader(f))
animation_evidence=[r for r in assets if r['name'] in ['hb_mangler.ai_am','hb_mangler_cannon']]
assert len(animation_evidence)==2
table=(DEPLOY/'animtables/hb_mangler.ai_am').read_text()
assert 'anim_zombie_mangler_cannon,hb_mangler_cannon' in table
banks=[dict(file=p.relative_to(DEPLOY/'zone').as_posix(),bytes=p.stat().st_size,time=datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat()) for p in (DEPLOY/'zone/snd').rglob('*'+MAP+'*.sab*')]
assert len([b for b in banks if '/all/' in b['file'] and b['bytes']>100000000])==2
eyes=asset('material','tod_charcoal_mtl_char_rus_zombie_eyes')
assert eyes['colorTint']=='1 0 0 1' and eyes['colorTint1']=='1 0 0 1'
data=dict(ff_bytes=ff.stat().st_size,ff_sha256=sha(ff),ff_time=datetime.datetime.fromtimestamp(stamp).isoformat(),
          build_log=str(log.relative_to(ROOT)),build_log_sha256=sha(log),inputs_matched=len(matched),inputs=matched,
          compiled_models=models,sound_banks=banks,mangler_animation_evidence=animation_evidence,charcoal_eyes={k:eyes[k] for k in ['materialType','colorMap','colorMap00','colorTint','colorTint1','scaleRGB']},
          source_palette_verified=True,game_launched=False,native_visual_verified=False,native_gameplay_verified=False)
(ROOT/args.output).write_text(json.dumps(data,indent=2))
print(json.dumps({k:v for k,v in data.items() if k not in ['inputs','compiled_models']},indent=2))
