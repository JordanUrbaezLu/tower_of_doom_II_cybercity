"""Read-only source/deployment audit; optional evidence writes stay in this repo."""
from pathlib import Path
import argparse, datetime, hashlib, json
ROOT=Path(__file__).resolve().parents[2]
TOOLS=Path('C:/BO3Tools/TOD2Cybercity')
MAP='zm_tod2_cybercity'
DEPLOY=TOOLS/'usermaps'/MAP
GAME=Path('C:/Program Files (x86)/Steam/steamapps/common/Call of Duty Black Ops III')
p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
binding=json.loads((TOOLS/'.tod2-workspace.json').read_text(encoding='utf-8-sig'))
assert binding['map']==MAP and Path(binding['repository']).resolve()==ROOT.resolve()
files=['scripts/zm/'+MAP+'.gsc','scripts/zm/archetype_zod_companion.gsc','scripts/zm/zm_zod_robot.gsc',
       'zone_source/'+MAP+'.zone','zone_source/tod_partners.zpkg',
       'ui/uieditor/widgets/HUD/ZM_CursorHint/ZMCursorHintNew.lua']
files+=['scripts/zm/'+MAP+'/'+name for name in ['_tod_partners.gsc','_tod_main.gsc','_tod_bosses.gsc',
    '_tod_boss_fx.csc','_tod_upgrades.gsc','_tod_luck.gsc',
    '_tod_corpse_cleanup.gsc','_tod_breather_data.gsc',
    '_tod_door_data.gsc','_tod_doors.gsc','_tod_perk_scatter.gsc']]
files+=['source_data/tod_partners.gdt','map_source/zm/'+MAP+'.map']
files+=[str(f.relative_to(ROOT)).replace('\\','/') for f in (ROOT/'model_export/tod_partner').iterdir() if f.is_file()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
ff=DEPLOY/'zone'/(MAP+'.ff');stamp=ff.stat().st_mtime
for rel in files:
    src=ROOT/rel
    dst=(TOOLS if rel.startswith(('source_data/','model_export/','map_source/')) else DEPLOY)/rel
    assert dst.resolve().is_relative_to(TOOLS.resolve()),('outside private root',dst)
    assert dst.exists() and sha(src)==sha(dst),('deployed source differs',rel)
    assert max(src.stat().st_mtime,dst.stat().st_mtime)<=stamp,('source newer than packaged FF',rel)
    rows.append({'path':rel,'sha256':sha(src)})
game_ff=GAME/'usermaps'/MAP/'zone'/(MAP+'.ff')
assert game_ff.resolve()==ff.resolve(),('game resolves elsewhere',game_ff.resolve())
assert ff.stat().st_size>100_000_000
report={'checked_at':datetime.datetime.now().astimezone().isoformat(),
        'map':MAP,'private_root':str(TOOLS),'sources':rows,
        'fastfile':{'path':str(ff),'bytes':ff.stat().st_size,'sha256':sha(ff),
                    'modified':datetime.datetime.fromtimestamp(ff.stat().st_mtime).astimezone().isoformat()},
        'native_game_launched':False,'native_visual_and_gameplay_acceptance':'pending user playtest'}
if args.record:
    dest=ROOT/'tmp/partner_build/deployment.json';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+'\n')
print('PARTNER_DEPLOYMENT_PASS:',len(rows),'matching sources; playable FF resolves to the private Tower II build;',ff.stat().st_size,'bytes')
