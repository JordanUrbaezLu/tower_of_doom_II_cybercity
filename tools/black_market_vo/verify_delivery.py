"""Snapshot the dealer delivery, then prove the guarded build consumed it."""
import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path('C:/BO3Tools/TOD2Cybercity')
DEP = TOOLS / 'usermaps/zm_tod2_cybercity'
OUT = ROOT / 'tmp/black_market_vo/clone_delivery'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def inputs():
    paths = [p for d in ('scripts', 'ui', 'zone_source') for p in (ROOT/d).rglob('*')
             if p.is_file() and not any(x in ('all','english','loc','__pycache__') for x in p.relative_to(ROOT/d).parts)]
    paths += [ROOT/'sound/aliases/tod_shop.csv', ROOT/'sound/aliases/tod_ui.csv']
    m = json.loads((ROOT/'art/black_market_vo/manifest.json').read_text())
    paths += [ROOT/'sound_assets/tod/sfx'/f'{name}.wav' for name in m['files']]
    return {p.relative_to(ROOT).as_posix():sha(p) for p in paths}

def main():
    OUT.mkdir(exist_ok=True)
    snap = OUT/'snapshot.json'
    if '--snapshot' in sys.argv:
        snap.write_text(json.dumps({'captured':datetime.now().isoformat(),'inputs':inputs()},indent=2)+'\n')
        print('Dealer delivery snapshot saved')
        return
    captured = json.loads(snap.read_text())
    ff = DEP/'zone/zm_tod2_cybercity.ff'
    assert ff.stat().st_mtime > snap.stat().st_mtime, 'No fresh fastfile'
    failures=[]
    for rel,digest in captured['inputs'].items():
        dest = (TOOLS if rel.startswith('sound_assets/') else DEP)/rel
        if sha(ROOT/rel)!=digest: failures.append('source changed since snapshot: '+rel)
        if not dest.is_file() or sha(dest)!=digest: failures.append('deployment mismatch: '+rel)
        elif dest.stat().st_mtime>ff.stat().st_mtime: failures.append('post-fastfile sync: '+rel)
    # Also check every deployed source, including files outside the snapshot.
    for folder in ('scripts','ui','zone_source'):
        for p in (DEP/folder).rglob('*'):
            if p.is_file() and not any(x in ('all','english','loc') for x in p.relative_to(DEP/folder).parts) and p.stat().st_mtime>ff.stat().st_mtime:
                failures.append('post-fastfile deployment: '+str(p.relative_to(DEP)))
    ledger=DEP/'zone_source/all/assetinfo/zm_tod2_cybercity.csv'
    assert ledger.stat().st_mtime>snap.stat().st_mtime
    names={r['name'] for r in csv.DictReader(ledger.open(encoding='utf-8-sig',newline=''))}
    for n in ('scripts/zm/zm_tod2_cybercity/_tod_shop.gsc','scripts/zm/zm_tod2_cybercity/_tod_shop_vo.gsc','scripts/zm/zm_tod2_cybercity/_tod_dealer_finale.gsc'):
        if n not in names: failures.append('missing linked script: '+n)
    aliasfile=DEP/'sound/zone/zm_tod2_cybercity.all.alias.sz'
    assert aliasfile.stat().st_mtime>snap.stat().st_mtime
    aliases={r['Name'] for r in csv.DictReader(aliasfile.open(encoding='utf-8-sig',newline=''))}
    m=json.loads((ROOT/'art/black_market_vo/manifest.json').read_text())
    for n in m['files']:
        if n not in aliases: failures.append('missing bank alias: '+n)
    banks={str(p.relative_to(DEP/'zone')):p.stat().st_size for p in (DEP/'zone/snd').rglob('*.sab*')}
    if not any(n.endswith('.all.sabs') and size>50*1024*1024 for n,size in banks.items()): failures.append('streamed bank missing/truncated')
    report={'ff_bytes':ff.stat().st_size,'ff_time':datetime.fromtimestamp(ff.stat().st_mtime).isoformat(),'ff_sha256':sha(ff),'input_count':len(captured['inputs']),'voice_id':m['voice'],'dealer_aliases':len(m['files']),'banks':banks,'failures':failures,'native_playtest':'pending; user tests','game_launched':False}
    (OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not failures, failures
    print('DEALER CLONE DELIVERY PASS:',len(captured['inputs']),'inputs;',len(m['files']),'bank aliases;',ff.stat().st_size,'fastfile bytes')

if __name__=='__main__': main()
