"""Audit a successful owned FULL build: source parity, native asset ledger and audio build.

No game launch; no decoded runtime particles/animation playback or audibility claim.
"""
import argparse
import csv
import hashlib
import json
import pathlib
import re
import time

ROOT=pathlib.Path(__file__).resolve().parents[2]
TOOLS=pathlib.Path('C:/BO3Tools/TOD2Cybercity')
MAP='zm_tod2_cybercity'
DEP=TOOLS/'usermaps'/MAP


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--log',type=pathlib.Path,required=True)
    args=ap.parse_args()
    raw=args.log.read_bytes()
    log=raw.decode('utf-16') if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else raw.decode('utf-8-sig',errors='replace')
    assert '[build] === BUILD OK ===' in log and '[build] mode = FULL geometry' in log,'Guarded FULL build did not pass'
    ff=DEP/'zone'/f'{MAP}.ff'
    # Bind by input generation and an independently decoded FF receipt. Wall-clock
    # gaps (suspend/session delay) must not substitute for actual artifact identity.
    inputs_path=ROOT/'art/dealer_combat/delivery_inputs.json'
    captured=inputs_path.stat().st_mtime_ns
    assert captured<ff.stat().st_mtime_ns<=args.log.stat().st_mtime_ns,'FF is not newer than this input generation'
    assert f'[build] fastfile: {ff} ({ff.stat().st_size:,} bytes)' in log,'Build log names a different delivery'
    receipt=json.loads((ROOT/'art/crown_alarm/lens_review/compiled_material.json').read_text())
    assert pathlib.Path(receipt['fastfile']).resolve()==ff.resolve(),'Compiled receipt belongs to a different map'
    ff_sha=sha(ff)
    assert receipt['fastfile_sha256']==ff_sha and receipt['fastfile_size']==ff.stat().st_size,'Current FF differs from the decoded post-link receipt'
    landed=json.loads(inputs_path.read_text(encoding='utf-8'))
    parity={}
    for rel,want in landed['files'].items():
        assert sha(ROOT/rel)==want,('Input edited after build snapshot',rel)
        frozen=ROOT/landed['frozen_root']/rel
        assert sha(frozen)==want,('Frozen build input changed',rel)
        if rel.startswith('tools/') or rel.endswith('sound_assets/tod/dealer_combat/manifest.json'):continue
        target=(DEP if rel.split('/')[0] in ('scripts','animtables','zone_source','sound') else TOOLS)/rel
        assert target.is_file() and sha(target)==want,('Deployment parity',rel,str(target))
        assert target.stat().st_mtime_ns<=ff.stat().st_mtime_ns,('Source synced after FF',rel)
        parity[rel]=want
    ledger=DEP/'zone_source/all/assetinfo'/f'{MAP}.csv'
    assert captured<ledger.stat().st_mtime_ns<=ff.stat().st_mtime_ns+5*10**9,'Ledger is outside this FF generation'
    rows=list(csv.DictReader(ledger.open(encoding='utf-8-sig',newline='')))
    assets={(r['type'],re.sub(r'#[0-9a-fA-F]+$','',r['name']).lower().replace('\\','/')) for r in rows}
    needed=[('scriptparsetree',f'scripts/zm/{MAP}/'+n+'.gsc') for n in ('_tod_dealer_finale','_tod_house','_tod_bosses')]
    needed += [('xanim','tod_dealer_c_'+k) for k in ('shock','burst')]
    needed += [('fx','tod/dealer_combat/fx_dc_'+k) for k in ('warning','charge','shock','muzzle','tracer')]
    for asset in needed:assert asset in assets,('Not linked',asset)
    alias=DEP/'sound/zone'/f'{MAP}.all.alias.sz'
    native=list(csv.DictReader(alias.open(encoding='utf-8-sig',newline='')))
    expected=list(csv.DictReader((ROOT/'sound/aliases/tod_dealer_combat.csv').open(encoding='utf-8-sig',newline='')))
    selected=[]
    for row in expected:
        matches=[r for r in native if r['Name']==row['Name']]
        assert len(matches)==1,('Native alias missing/duplicate',row['Name'])
        actual=matches[0]
        for field in ('FileSpec','Storage','PanType','Looping','Pauseable','StopOnEntDeath','LimitCount','EntityLimitCount'):
            norm=lambda value:value.lower().replace('\\','/')
            if field in ('Pauseable','StopOnEntDeath'):
                norm=lambda value:value.lower() in ('yes','true','1')
            assert norm(actual[field])==norm(row[field]),(row['Name'],field)
        selected.append(actual)
    inputs=[ROOT/'sound/aliases/tod_dealer_combat.csv',ROOT/f'sound/zoneconfig/{MAP}.szc']
    inputs+=list((ROOT/'sound_assets/tod/dealer_combat').glob('*.wav'))
    audio_latest=max(p.stat().st_mtime_ns for p in inputs)
    assert audio_latest<=alias.stat().st_mtime_ns<=ff.stat().st_mtime_ns,'Audio alias build freshness'
    bankassets=DEP/'sound/zone'/f'{MAP}.all.assets.sz'
    index=bankassets.read_text().lower()
    for row in expected:assert row['Name'].lower()+'.' in index,('Audio missing from compiled bank asset index',row['Name'])
    banks=list((DEP/'zone/snd').rglob('*.all.sabl'))
    assert banks and all(p.stat().st_size>1024*1024 and audio_latest<=p.stat().st_mtime_ns<=ff.stat().st_mtime_ns for p in banks),'Loaded bank freshness'
    review=json.loads((ROOT/'art/dealer_combat/review/review.json').read_text())
    report=dict(verified_ns=time.time_ns(),ff=dict(path=str(ff),bytes=ff.stat().st_size,sha256=ff_sha,mtime_ns=ff.stat().st_mtime_ns),
        artifact_binding='Fresh after frozen input snapshot; exact log path/size and decoded post-link receipt SHA256 match.',
        mode='guarded FULL',log=str(args.log),geometry_reused='[geom_key] REUSE:' in log,
        input_snapshot=str(inputs_path.relative_to(ROOT)),input_snapshot_sha256=sha(inputs_path),
        source_parity=parity,linked_assets=needed,compiled_aliases=selected,
        loaded_banks=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in banks],
        review_clip_pins={k:v['clip_sha256'] for k,v in review['poses'].items()},
        independent_review='Code, exact-binary poses and warning art passed separate agent review.',
        native_visual_verified=False,native_performance_verified=False,native_audio_played=False,game_launched=False)
    (ROOT/'art/dealer_combat/build.json').write_text(json.dumps(report,indent=2)+'\n')
    print('DEALER COMBAT NATIVE PASS:',len(needed),'linked assets;',len(parity),'matching deployed inputs; four native sound aliases/bank entries; user fight unplayed')


if __name__=='__main__':main()
