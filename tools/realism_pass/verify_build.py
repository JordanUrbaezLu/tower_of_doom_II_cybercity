"""Snapshot this art pass, then prove the guarded build consumed those inputs.
Read-only toward private Mod Tools. No game launch, sync or asset conversion.
"""
import argparse, csv, datetime, hashlib, json, pathlib, re, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[2]
MT=pathlib.Path('C:/BO3Tools/TOD2Cybercity')
MAP='zm_tod2_cybercity';DEP=MT/'usermaps'/MAP
OUT=ROOT/'art/realism_pass';OUT.mkdir(parents=True,exist_ok=True)
SNAP=OUT/'build_inputs.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
SHARED=('scripts','ui','zone_source')
OWNED=('model_export/tod_sky_ships','model_export/tod_crown_alarm','model_export/tod_alarm_button',
       'source_data/tod_sky_detail','share/raw/fx/tod/sky')
GDTS=('source_data/tod_sky_ships.gdt','source_data/tod_crown_alarm.gdt','source_data/tod_alarm_button.gdt','source_data/tod_sky_detail.gdt')

def files():
    for folder in SHARED+OWNED:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file() and not any(v in ('__pycache__','all','english','loc') for v in p.relative_to(ROOT/folder).parts):
                yield p
    for rel in GDTS: yield ROOT/rel

def target(rel):
    return (DEP if pathlib.PurePosixPath(rel).parts[0] in SHARED else MT)/rel

def read_log(path):
    raw=path.read_bytes()
    return raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')

def art_inputs(inputs):
    return {rel:digest for rel,digest in inputs.items() if pathlib.PurePosixPath(rel).parts[0] not in SHARED}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--snapshot',action='store_true');ap.add_argument('--build-log')
    ap.add_argument('--base-full-artifact',help='Preserved full-build receipt required when the final build is a later script-only relink')
    ap.add_argument('--record-built-art',action='store_true',help='Record a completed art build while separately reporting later shared-source work; never waive art changes or deployed-input mismatches')
    args=ap.parse_args()
    if args.snapshot:
        rows={p.relative_to(ROOT).as_posix():sha(p) for p in files()}
        data={'captured_unix':time.time(),'captured_local':datetime.datetime.now().isoformat(),
              'map':MAP,'private_root':str(MT),'inputs':rows}
        SNAP.write_text(json.dumps(data,indent=2))
        print('REALISM INPUT SNAPSHOT',len(rows),'files');return
    assert args.build_log,'--build-log required after the guarded full build'
    snapshot=json.loads(SNAP.read_text())
    log=ROOT/args.build_log;text=read_log(log)
    assert '[build] === BUILD OK ===' in text,'guarded build did not finish successfully'
    base_proof=None
    if '[build] mode = FULL geometry' not in text:
        assert args.base_full_artifact and '[build] mode = GSC-ONLY' in text,'material changes require a full build'
        assert '[build] geometry + lighting: current (identical inputs to the last full build)' in text,'relink reused unverified geometry/lighting'
        base=json.loads((ROOT/args.base_full_artifact).read_text())
        base_log=ROOT/base['log'];base_snapshot=ROOT/base['inputs']
        assert sha(base_log)==base['log_sha256'] and sha(base_snapshot)==base['inputs_sha256'],'full-build proof changed'
        base_text=read_log(base_log);base_inputs=json.loads(base_snapshot.read_text())
        assert '[build] === BUILD OK ===' in base_text and '[build] mode = FULL geometry' in base_text,'missing successful full material build'
        assert base_inputs['captured_unix']<base['ff_unix']<snapshot['captured_unix'],'invalid full-build/relink order'
        assert art_inputs(base_inputs['inputs'])==art_inputs(snapshot['inputs']),'art changed after full build; script-only relink cannot prove it'
        base_proof={'receipt':args.base_full_artifact,'unchanged_art_inputs':len(art_inputs(snapshot['inputs']))}
    ff=DEP/'zone'/(MAP+'.ff');stamp=ff.stat().st_mtime
    assert stamp>snapshot['captured_unix'],'fastfile predates source snapshot'
    assert abs(log.stat().st_mtime-stamp)<1800,'log does not belong to current deployed build'
    now={p.relative_to(ROOT).as_posix():sha(p) for p in files()}
    before=snapshot['inputs']
    changed={rel for rel in now.keys()|before.keys() if now.get(rel)!=before.get(rel)}
    pending=[]
    assert not changed or args.record_built_art,'repo changed during/after build; compare against build_inputs.json'
    for rel in sorted(changed):
        assert pathlib.PurePosixPath(rel).parts[0] in SHARED,'owned art differs from completed build: '+rel
        p=ROOT/rel
        assert p.is_file() and p.stat().st_mtime>stamp,'shared-source difference cannot be proven later than FF: '+rel
        pending.append({'path':rel,'built_sha256':before.get(rel),'current_sha256':now[rel],
                        'changed_local':datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat()})
    for rel,want in before.items():
        dst=target(rel)
        assert dst.is_file() and sha(dst)==want,'deployed input differs: '+rel
        assert dst.stat().st_mtime<=stamp,'source synced after fastfile: '+rel
    for folder in SHARED:
        expected_paths={pathlib.PurePosixPath(rel).relative_to(folder).as_posix() for rel in before if rel.startswith(folder+'/')}
        deployed_paths={p.relative_to(DEP/folder).as_posix() for p in (DEP/folder).rglob('*') if p.is_file()
                        and not any(v in ('all','english','loc') for v in p.relative_to(DEP/folder).parts)}
        assert expected_paths==deployed_paths,'deployed script/UI/zone tree differs from build snapshot: '+folder
    ledger=DEP/'zone_source/all/assetinfo'/(MAP+'.csv')
    with ledger.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    assets={(r['type'],r['name']) for r in rows}
    used=[]
    lens_gdt=(ROOT/'source_data/tod_crown_alarm.gdt').read_text()
    lens=re.search(r'"mtl_tod_alarm_lens"\s*\(\s*"material.gdf"\s*\)\s*\{(.*?)\n\t\}',lens_gdt,re.S)
    assert lens and '"materialType" "lit_emissive_transparent_advanced"' in lens[1], 'unexpected lens shader; re-audit its native texture channels'
    assert any(k=='techset' and n.startswith('mc/lit_emissive_transparent_advanced#') for k,n in assets),'native advanced glass techset missing'
    assert all(('image','i_tod_alarm_lens_'+c) in assets for c in ('c','n','g')),'native glass color/normal/gloss detail missing'
    # Native DXBC uses constant dielectric F0 and omits the RGB specular map.
    # The unused source image stays editable; never exempt the actual gloss map.
    # Disassembly evidence is preserved with art/crown_alarm/realism_review.
    source_only={'i_tod_alarm_lens_s'}
    for rel in GDTS:
        for name,kind in re.findall(r'"([^"\n]+)"\s*\(\s*"(image|material|xmodel)\.gdf"\s*\)',(ROOT/rel).read_text()):
            if kind=='image' and name in source_only: continue
            prefixes=('','mc/','ei/','el/','wc/') if kind=='material' else ('',)
            assert any((kind,p+name) in assets for p in prefixes),'art asset not packed: '+kind+','+name
            used.append([kind,name])
    for p in (ROOT/'share/raw/fx/tod/sky').glob('fx_sky_*.efx'):
        assert ('fx','tod/sky/'+p.stem) in assets,'sky effect not packed: '+p.stem
    model_ledger=ledger.with_name(MAP+'_xmodel.csv')
    with model_ledger.open(encoding='utf-8-sig',newline='') as f: models={r['name']:r for r in csv.DictReader(f)}
    button=json.loads((ROOT/'art/alarm_button/manifest.json').read_text())
    for row in button['models']:
        assert sha(ROOT/row['file'])==row['sha256'], 'button source differs from reviewed export'
        native=models[row['asset']]
        # Native LOD columns run from coarse to fine, opposite source suffixes.
        assert int(native['lodCount'])==3 and int(native['tris'+str(2-row['lod'])])==row['triangles'], ('button native LOD mismatch',row)
    result={'verified_at':datetime.datetime.now().isoformat(),'ff_time':datetime.datetime.fromtimestamp(stamp).isoformat(),'ff_bytes':ff.stat().st_size,'ff_sha256':sha(ff),
            'build_log':args.build_log,'build_log_sha256':sha(log),'matched_inputs':len(before),'packed_art_assets':used,
            'inputs_not_newer_than_ff':True,'game_launched':False,'native_visual_verified':False,
            'art_inputs_match_current':True,'current_source_parity':not pending,'pending_source_changes':pending,'base_full_build':base_proof,
            'source_only_images':sorted(source_only),
            'button_compiled_lods':len(button['models']),
            'known_waived_warning_count':int(re.search(r'\[build\] (\d+) known-waived asset warning',text)[1])}
    (OUT/'build.json').write_text(json.dumps(result,indent=2))
    print('REALISM ART BUILD VERIFIED',len(before),'deployed inputs match original snapshot;',len(used),'art assets packed; FF',result['ff_bytes'],'bytes; native visuals unplayed')
    if pending:print('LATER WORK NOT INCLUDED:',', '.join(r['path'] for r in pending),'; current_source_parity=false')

if __name__=='__main__':main()
