"""Snapshot inputs, then verify this roster in the fresh private map build."""
import csv
import datetime
import hashlib
import json
import sys
from inspect_expected_roster import ROOT, TOOLS, OUT, blocks

DEP = TOOLS / 'usermaps/zm_tod2_cybercity'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def inputs():
    for directory in ['scripts','ui','zone_source','gamedata','sound']:
        for p in (ROOT/directory).rglob('*'):
            if p.is_file() and not any(x in ('all','english','loc','zone','__pycache__') for x in p.relative_to(ROOT/directory).parts):
                yield p
    for p in ['source_data/tod_weapon_twins.gdt','source_data/tod_breacher_apex.gdt','map_source/zm/zm_tod2_cybercity.map']:
        yield ROOT/p
    rows=csv.DictReader((ROOT/'sound/aliases/tod_expected_roster.csv').open(newline='',encoding='utf-8-sig'))
    paths={ROOT/'sound_assets'/r[k].replace('\\','/') for r in rows for k in ('FileSpec','FileSpecSustain','FileSpecRelease') if r.get(k)}
    yield from sorted(paths)


snap=OUT/'build_inputs.json'
if '--snapshot' in sys.argv:
    OUT.mkdir(parents=True,exist_ok=True)
    data={p.relative_to(ROOT).as_posix():sha(p) for p in inputs()}
    snap.write_text(json.dumps(data,indent=2))
    print('Roster snapshot:',len(data),'inputs')
    raise SystemExit

snapshot=json.loads(snap.read_text())
ff=DEP/'zone/zm_tod2_cybercity.ff'
stamp=ff.stat().st_mtime
assert stamp>snap.stat().st_mtime,'No fresh fastfile after snapshot'
bad=[]
newer=[]
for name,digest in snapshot.items():
    p=ROOT/name
    root=TOOLS if p.relative_to(ROOT).parts[0] in ('source_data','sound_assets','map_source') else DEP
    target=root/name
    if sha(p)!=digest:bad.append('source_changed:'+name)
    if not target.is_file() or sha(target)!=digest:bad.append('deployed_mismatch:'+name)
    if target.is_file() and target.stat().st_mtime>stamp:newer.append(name)
    if name.startswith('sound/aliases/'):
        alias_target=TOOLS/'share/raw'/name
        if not alias_target.is_file() or sha(alias_target)!=digest:bad.append('bank_alias_mismatch:'+name)

names=set()
for lang in ('all','english'):
    p=DEP/f'zone_source/{lang}/assetinfo/zm_tod2_cybercity.csv'
    assert p.stat().st_mtime>snap.stat().st_mtime
    for r in csv.DictReader(p.open(newline='',encoding='utf-8-sig')):
        names.add(r['name'])
        if r['type']=='weapon': names.add(r['name'].removesuffix('_zm'))
expected=set()
for name,data in blocks(ROOT/'source_data/tod_weapon_twins.gdt').items():
    if not data['type'].endswith('weapon.gdf'):continue
    expected.add(name.removesuffix('_zm'))
    if name.startswith('cc_'):
        for key in ('gunModel','worldModel','projectileModel'):
            value=data['fields'].get(key)
            if value:expected.add(value)
missing=sorted(expected-names)

alias_file=DEP/'sound/zone/zm_tod2_cybercity.all.alias.sz'
assert alias_file.stat().st_mtime>snap.stat().st_mtime
aliases={}
for r in csv.DictReader(alias_file.open(newline='',encoding='utf-8-sig')):
    aliases.setdefault(r['Name'],[]).append(r)
sound_assets=set((DEP/'sound/zone/zm_tod2_cybercity.all.assets.sz').read_text().splitlines())
source=list(csv.DictReader((ROOT/'sound/aliases/tod_expected_roster.csv').open(newline='',encoding='utf-8-sig')))
audio_names={r['Name'] for r in source}
outside_map_audio=set()
for n in ('cc_bow_r0m0_zm','cc_fire_bow_r0m0_zm','cc_peacekeeper_e0','cc_peacekeeper_up_e0'):
    fields=blocks(ROOT/'source_data/tod_weapon_twins.gdt')[n]['fields']
    for k in ('fireSound','fireSoundPlayer','emptyFireSound','emptyFireSoundPlayer','projExplosionSound'):
        value=fields.get(k)
        if not value:continue
        # The unchanged Peacekeeper inherits these generic dry-fire references.
        # They are absent from this map's bank; this audit cannot prove the
        # game's common banks supply them. Keep that boundary in the report.
        if value in ('wpn_generic_dryfire_plr','wpn_generic_dryfire_npc'):
            outside_map_audio.add(value)
        else:audio_names.add(value)
audio_missing=[]
for n in sorted(audio_names):
    if n not in aliases:audio_missing.append(n);continue
    for r in aliases[n]:
        for k in ('FileTarget','FileTargetSustain','FileTargetRelease'):
            if r.get(k) and r[k] not in sound_assets:audio_missing.append(n+':'+k)
banks={str(p.relative_to(DEP/'zone')):p.stat().st_size for p in (DEP/'zone/snd').rglob('*') if p.is_file()}
assert any(n.endswith('.all.sabs') and size>50*1024*1024 for n,size in banks.items()),'Truncated or missing streamed bank'
entry=(DEP/'scripts/zm/zm_tod2_cybercity.gsc').read_text(encoding='utf-8')
assert 'level.tod_dev = true;' in entry and 'level.tod_god = true;' in entry
report={'ff_bytes':ff.stat().st_size,'ff_time':datetime.datetime.fromtimestamp(stamp).isoformat(),
        'input_count':len(snapshot),'source_or_deployed_differences':bad,'deployed_inputs_newer_than_ff':newer,
        'expected_weapon_and_model_assets':len(expected),'missing_assets':missing,
        'expected_audio_aliases':len(audio_names),'missing_audio':audio_missing,
        'inherited_common_audio_not_verified':sorted(outside_map_audio),
        'sound_banks':banks,'dev':True,'god':True,'game_launched':False,'native_playtest_verified':False}
(OUT/'deployment.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
assert not bad and not newer and not missing and not audio_missing
