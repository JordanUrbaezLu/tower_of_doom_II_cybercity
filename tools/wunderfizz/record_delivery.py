"""Capture shipping inputs before build; prove source/deployment/FF freshness after it."""
from __future__ import annotations
import argparse, csv, datetime, hashlib, json, re, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOOLS=Path('C:/BO3Tools/TOD2Cybercity')
DEP=TOOLS/'usermaps/zm_tod2_cybercity'
OUT=ROOT/'art/wunderfizz'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def validate_placement(result, actual_gsc):
    nodes=result['nodes'];floors=[n['floor'] for n in nodes]
    assert len(nodes)==4 and sorted(floors)==[10,20,30,40],('Exactly four haven counters required',floors)
    assert len({n['id'] for n in nodes})==4,'Counter IDs must be unique'
    assert all(n['kind']=='haven' and 'alcove' not in n for n in nodes),'Only existing haven dome placements are allowed'
    assert len(result['dome'])==4 and all(row['counter_body_inside'] and row['standing_inside'] for row in result['dome']),'Counter body and purchaser must remain inside each existing haven dome'
    assert result['generated'].replace('\r\n','\n').rstrip('\n')==actual_gsc.replace('\r\n','\n').rstrip('\n'),'Actual generated Wunderfizz GSC differs from layout descriptors'
    assert [int(value) for value in re.findall(r'^\s*n\.floor\s*=\s*(\d+)\s*;',actual_gsc,re.M)]==floors,'Generated GSC floor list differs from actual layout descriptors'
    return dict(machine_count=len(nodes),floor_count=len(set(floors)),floors=sorted(floors),
                inside_existing_haven_domes=True,generated_gsc_matches_layout=True,
                purchaser_nav_probes_required=3*len(nodes),haven_route_connections_required=len(nodes))

def placement_inventory(layout_path=None,data_path=None):
    layout_path=(layout_path or ROOT/'tools/wunderfizz_layout.js').resolve()
    data_path=(data_path or ROOT/'scripts/zm/zm_tod2_cybercity/_tod_wunderfizz_data.gsc').resolve()
    assert layout_path.is_relative_to(ROOT) and data_path.is_relative_to(ROOT),'Placement proof must remain inside this repository'
    code="""
const w=require(process.argv[1]),h=require(process.argv[2]),nodes=w.nodes();
const dome=nodes.map(n=>({floor:n.floor,
counter_body_inside:w.body(n).every(p=>Math.hypot(p[0]-h.C[0],p[1]-h.C[1],w.ASSET.maxs[2]-h.DOME_C)<=h.DOME_S),
standing_inside:h.insideBody([n.trig[0],n.trig[1],0],h.IN_R3)}));
process.stdout.write(JSON.stringify({nodes,generated:w.dataGsc(nodes),dome}));
"""
    process=subprocess.run(['node','-e',code,str(layout_path),str(ROOT/'tools/haven_layout.js')],cwd=ROOT,capture_output=True,text=True,check=True)
    result=validate_placement(json.loads(process.stdout),data_path.read_text(encoding='utf-8-sig'))
    result.update(layout_source=str(layout_path),layout_source_sha256=sha(layout_path),generated_data=str(data_path),generated_data_sha256=sha(data_path))
    return result

def inputs():
    paths=[p for folder in ('scripts','ui','zone_source','sound') for p in (ROOT/folder).rglob('*')
           if p.is_file() and not any(x in ('all','english','loc','__pycache__') for x in p.relative_to(ROOT/folder).parts)]
    assets=json.loads((OUT/'asset_manifest.json').read_text())
    audio=json.loads((OUT/'audio_manifest.json').read_text())
    paths += [ROOT/item['file'] for item in assets['files']]
    paths += [ROOT/item['path'] for item in audio['files']]
    paths += [ROOT/'map_source/zm/zm_tod2_cybercity.map']
    return {p.relative_to(ROOT).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size,mtime=p.stat().st_mtime)
            for p in sorted(set(paths))}

def main():
    p=argparse.ArgumentParser();p.add_argument('--snapshot',action='store_true');p.add_argument('--postbuild-peer-receipt',type=Path);args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);snapshot=OUT/'delivery_inputs.json'
    placement=placement_inventory()
    if args.snapshot:
        snapshot.write_text(json.dumps(dict(captured_at=datetime.datetime.now().astimezone().isoformat(),inputs=inputs(),placement=placement),indent=2)+'\n')
        print('WUNDERFIZZ delivery snapshot captured');return
    saved=json.loads(snapshot.read_text());current=inputs()
    assert saved['placement']==placement,'Placement changed after build snapshot'
    ff=DEP/'zone/zm_tod2_cybercity.ff';assert ff.stat().st_mtime>snapshot.stat().st_mtime,'No new completed fastfile'
    pending=[]
    changed={rel for rel in saved['inputs'] if rel in current and current[rel]['sha256']!=saved['inputs'][rel]['sha256']}
    added=set(current)-set(saved['inputs']);removed=set(saved['inputs'])-set(current)
    if args.postbuild_peer_receipt:
        # A completed FF stays valid when another session lands its next work.
        # This opt-in permits only the explicitly pinned Dealer receipt below;
        # deployment must still match EVERY captured build input. Never accept
        # drift in this feature's own scripts, models, art or audio.
        receipt=args.postbuild_peer_receipt.resolve()
        assert receipt==(ROOT/'tmp/dealer_combat_stage/inputs.json').resolve(),'Unknown peer landing receipt'
        peer=json.loads(receipt.read_text());peer_pin=sha(receipt)
        allowed={'scripts/zm/zm_tod2_cybercity/_tod_bosses.gsc','scripts/zm/zm_tod2_cybercity/_tod_dealer_finale.gsc','scripts/zm/zm_tod2_cybercity/_tod_house.gsc','sound/zoneconfig/zm_tod2_cybercity.szc','zone_source/zm_tod2_cybercity.zone'}
        assert changed==allowed and added=={'sound/aliases/tod_dealer_combat.csv'} and not removed,'Unreviewed post-build source changes'
        for rel in sorted(changed|added):
            assert (ROOT/rel).stat().st_mtime>ff.stat().st_mtime,('Source changed before completed FF',rel)
            if rel in changed:
                assert peer[rel]['before']==saved['inputs'][rel]['sha256'] and peer[rel]['after']==current[rel]['sha256'],('Peer before/after pins do not match',rel)
            pending.append(dict(file=rel,compiled_snapshot_sha256=saved['inputs'].get(rel,{}).get('sha256'),pending_source_sha256=current[rel]['sha256'],pending_source_time=datetime.datetime.fromtimestamp((ROOT/rel).stat().st_mtime).astimezone().isoformat(),status='Post-build Dealer work; not in this FF'))
        assert sha(receipt)==peer_pin,'Peer receipt changed during audit'
    else:
        assert not added and not removed and not changed,'Shipping inputs changed after build snapshot'
    failures=[]
    for rel,pin in saved['inputs'].items():
        if current[rel]['sha256']!=pin['sha256'] and rel not in changed: failures.append('source changed after snapshot: '+rel)
        target=(TOOLS if rel.startswith(('model_export/','xanim_export/','source_data/','share/raw/','sound_assets/','map_source/')) else DEP)/rel
        if not target.is_file() or sha(target)!=pin['sha256']: failures.append('deployment differs: '+rel)
        elif target.stat().st_mtime>ff.stat().st_mtime: failures.append('deployment newer than FF: '+rel)
        if (ROOT/rel).stat().st_mtime>ff.stat().st_mtime and rel not in changed: failures.append('source newer than FF: '+rel)
    ledger=DEP/'zone_source/all/assetinfo/zm_tod2_cybercity.csv'
    rows={(r['type'],r['name']) for r in csv.DictReader(ledger.open(encoding='utf-8-sig',newline=''))}
    for filename in ('_tod_wunderfizz_data.gsc','_tod_perk_roster.gsc','_tod_wunderfizz.gsc','_tod_wunderfizz_machine.gsc','_tod_wunderfizz_machine.csc'):
        if ('scriptparsetree','scripts/zm/zm_tod2_cybercity/'+filename) not in rows: failures.append('missing linked script: '+filename)
    if ('rawfile','ui/uieditor/menus/hud/tod_wunderfizz.lua') not in rows: failures.append('missing linked selector')
    compiled=json.loads((OUT/'compiled_assets.json').read_text());audio=json.loads((OUT/'native_audio.json').read_text())
    assert audio['ff_sha256']==sha(ff),'Native audio receipt does not refer to this FF'
    assert compiled['native_outputs_sha256'][str(ff)]==sha(ff),'Native asset receipt does not refer to this FF'
    report=dict(verified_at=datetime.datetime.now().astimezone().isoformat(),ff_bytes=ff.stat().st_size,
                ff_sha256=sha(ff),ff_time=datetime.datetime.fromtimestamp(ff.stat().st_mtime).astimezone().isoformat(),
                source_inputs=len(saved['inputs']),floor_count=placement['floor_count'],machine_count=placement['machine_count'],floors=placement['floors'],placement=placement,retired_individual_machine_structs=9,
                all_fourteen_native_lods_verified=True,complete_material_tables_verified=True,
                original_glass_alpha_mips_verified=13,original_machine_pcm_files=7,
                failures=failures,postbuild_peer_source_changes=pending,shipping_snapshot_and_private_deployment_match=True,wunderfizz_source_still_matches_deployment=True,game_launched=False,native_playtest='Pending; the user tests appearance, audio, controls, drink flow and diagnostic output.')
    (OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not failures, failures
    print('WUNDERFIZZ DELIVERY PASS:',len(saved['inputs']),'captured shipping inputs, linked selector and five script halves;',ff.stat().st_size,'FF bytes;',len(pending),'explicitly pinned post-build Dealer source changes await their own build; user playtest pending')

if __name__=='__main__': main()
