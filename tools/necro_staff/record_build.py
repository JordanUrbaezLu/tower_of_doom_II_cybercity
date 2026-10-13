"""Post-build evidence. Read-only toward private tools; writes only this repo."""
import pathlib,sys,json,hashlib,csv,datetime,argparse,sqlite3,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];MT=pathlib.Path('C:/BO3Tools/TOD2Cybercity');MAP='zm_tod2_cybercity';DEP=MT/'usermaps'/MAP
p=argparse.ArgumentParser();p.add_argument('--build-log',required=True);args=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
log=ROOT/args.build_log;raw=log.read_bytes();text=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
assert '[build] === BUILD OK ===' in text,'The guarded build must succeed first'
ff=DEP/'zone'/(MAP+'.ff');stamp=ff.stat().st_mtime
assert abs(stamp-log.stat().st_mtime)<180,'Build log does not belong to the deployed FF'
pairs=[]
for folder in ['scripts','ui','zone_source','sound','animtables','gamedata']:
    for src in (ROOT/folder).rglob('*'):
        if src.is_file():pairs.append((src,DEP/src.relative_to(ROOT)))
for folder in ['model_export/tod_crown_alarm','model_export/tod_cyber_elites','share/raw/fx/tod/crown_alarm','model_export/tod_necro','share/raw/fx/tod/necro','model_export/tod_fire_bow','model_export/tod_warrior','xanim_export/tod_warrior','model_export/tod_necro_staff','xanim_export/tod_necro_staff']:
    for src in (ROOT/folder).rglob('*'):
        if src.is_file():pairs.append((src,MT/src.relative_to(ROOT)))
for rel in ['source_data/tod_necro_staff_art.gdt','source_data/tod_necro_staff_anims.gdt','source_data/tod_necro_staff.gdt','source_data/tod_crown_alarm.gdt','source_data/tod_cyber_elites.gdt','source_data/tod_necro_pulse.gdt','source_data/tod_fire_bow.gdt','source_data/tod_weapon_twins.gdt','source_data/tod_warrior_hook.gdt','source_data/tod_warrior_punch.gdt','map_source/zm/'+MAP+'.map']:
    pairs.append((ROOT/rel,MT/rel))
inputs=[]
for src,dst in pairs:
    assert dst.exists() and sha(src)==sha(dst),(src,'deployment drift')
    assert dst.stat().st_mtime<=stamp,(dst,'synced after FF')
    inputs.append(dict(file=src.relative_to(ROOT).as_posix(),sha256=sha(src)))
ledger=next(DEP.glob('zone_source/*/assetinfo/'+MAP+'.csv'))
subprocess.run([sys.executable,'-B',str(ROOT/'tools/archer_assets/verify_fire_bow.py'),'--ledger',str(ledger)],check=True)
subprocess.run([sys.executable,'-B',str(ROOT/'tools/necro_staff/verify.py'),'--ledger',str(ledger)],check=True)
with ledger.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
names={r['name'].split('|')[0] for r in rows}
assert 'vm_tod_gauntlet_left_hook' in names,'Retargeted Warrior hook not linked'
for name in ['ei/mtl_tod_necro_pulse','i_tod_necro_pulse','tod/necro/fx_necro_mangler_aura_c0']+[f'tod/necro/fx_necro_pulse_ring{i}' for i in range(4)]:
    assert name in names,('Missing Necromancer asset',name)
alarm=[r for r in rows if any(t in r['name'] for t in ['tod_crown_alarm','tod_alarm_','i_tod_robot_','mtl_tod_doppelgast_robot','hb_mangler_cannon','hb_mangler.ai_am'])]
for name in ['tod_crown_alarm_housing','tod_crown_alarm_rotor_off','tod_crown_alarm_rotor_on','tod_crown_alarm_rotor_high_on','tod_crown_alarm_housing_high','tod_crown_alarm_rotor_high_off','mc/mtl_tod_alarm_lamp_high_on','tod/crown_alarm/fx_tod_alarm_sweep','tod/crown_alarm/fx_tod_alarm_high']:
    assert any(r['name']==name for r in alarm+rows),name
for family in ['shell','piston','rubber']:
    for suffix in ['c','n','s','g']:
        assert any(r['type']=='image' and r['name']=='i_tod_robot_'+family+'_'+suffix for r in rows),(family,suffix)
    assert any(r['type']=='material' and r['name']=='mc/mtl_tod_doppelgast_robot_'+family for r in rows),family
assert 'anim_zombie_mangler_cannon,hb_mangler_cannon' in (DEP/'animtables/hb_mangler.ai_am').read_text()
profile=json.loads((ROOT/'tools/crown_alarm/light_profile.json').read_text())
db=sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro',uri=True)
db.execute('pragma writable_schema=ON')
assert db.execute('select scaleRGB from material where _name=?',('mtl_tod_alarm_lamp_on',)).fetchone()[0]==profile['lamp_emission'],'Native lamp intensity is stale'
assert db.execute('select scaleRGB from material where _name=?',('mtl_tod_alarm_lamp_high_on',)).fetchone()[0]==profile['lamp_emission']*profile['high_lamp_multiplier'],'Native high crown intensity is stale'
assert db.execute('select skinOverride from xmodel where _name=?',('tod_crown_alarm_rotor_high_on',)).fetchone()[0]=='mtl_tod_alarm_lamp_off mtl_tod_alarm_lamp_high_on','Native high model skin is stale'
assert db.execute('select materialType,scaleRGB,alphaRevealMap from material where _name=?',('mtl_tod_necro_pulse',)).fetchone()==('effect_lit_emissive_blend',64.0,'$white_reveal'),'Soul Pulse native rendering settings are stale'
resident=db.execute("select _name,streamable from image where _name like 'i_tod_necro_iron_%' or _name like 'i_tod_necro_forge_%' or _name like 'i_tod_necro_bone_%' or _name like 'i_tod_necro_staff_soul_%' or _name like 'i_tod_necro_leather_%'").fetchall()
assert len(resident)==19 and all(not row[1] for row in resident),('Staff texture residency mismatch',resident)
db.close()
data=dict(ff_bytes=ff.stat().st_size,ff_sha256=sha(ff),ff_time=datetime.datetime.fromtimestamp(stamp).isoformat(),build_log=args.build_log,build_log_sha256=sha(log),inputs_matched=len(inputs),inputs=inputs,compiled_assets=alarm,fixture_count=30,light_profile=profile,game_launched=False,native_visual_verified=False)
data['staff_assets']=[r for r in rows if any(t in r['name'] for t in ['tod_necro_staff','tod_vm_necro_staff','tod_necro_pulse2','tod_necro_pulse3','i_tod_necro_iron','i_tod_necro_forge','i_tod_necro_bone','i_tod_necro_leather'])]
data['staff_asset_count']=len(data['staff_assets'])
data['native_bake']={}
for suffix in ['d3dbsp','led']:
    baked=MT/'share/raw/maps/zm'/(MAP+'.'+suffix)
    assert baked.exists() and baked.stat().st_mtime <= stamp,('Invalid bake timestamp',baked)
    data['native_bake'][suffix]=dict(bytes=baked.stat().st_size,sha256=sha(baked),time=datetime.datetime.fromtimestamp(baked.stat().st_mtime).isoformat())
baseline=ROOT/'tmp/necro_staff_build/fresh_bake_before_relink.json'
if baseline.exists() and 'WARN: -GscOnly:' in text:
    for entry in json.loads(baseline.read_text(encoding='utf-8-sig')):
        assert sha(pathlib.Path(entry['path'])).lower()==entry['sha256'].lower(),'Fresh full-build bake changed during relink'
# A checksum failure can leave a bank above the general 50 MB guard while
# dropping sounds. These unchanged audio sources previously built this size.
data['sound_banks']={}
for rel in ['sound/zone/CachedBanks/all/'+MAP+'.all.sabs','zone/snd/all/'+MAP+'.all.sabs']:
    bank=DEP/rel
    assert bank.stat().st_size==209338496,('Incomplete sound bank after checksum retry',bank,bank.stat().st_size)
    data['sound_banks'][rel]=dict(bytes=bank.stat().st_size,sha256=sha(bank))
assert len({v['sha256'] for v in data['sound_banks'].values()})==1,'Cached and deployed sound banks differ'
(ROOT/'art/necro_staff/deployment.json').write_text(json.dumps(data,indent=2))
print(json.dumps({k:v for k,v in data.items() if k not in ['inputs','compiled_assets','staff_assets']},indent=2))
