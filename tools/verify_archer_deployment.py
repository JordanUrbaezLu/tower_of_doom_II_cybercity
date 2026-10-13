"""Read-only deployment audit; records evidence in this repository's docs."""
from pathlib import Path
import csv
import datetime
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path('C:/BO3Tools/TOD2Cybercity')
DEP = TOOLS / 'usermaps/zm_tod2_cybercity'
FF = DEP / 'zone/zm_tod2_cybercity.ff'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    failures = []
    stamp = FF.stat().st_mtime
    checked = {}
    for directory in ('scripts', 'ui', 'zone_source', 'gamedata', 'sound'):
        for src in (ROOT / directory).rglob('*'):
            if not src.is_file() or any(x in ('all', 'english', 'loc', 'zone', '__pycache__') for x in src.relative_to(ROOT / directory).parts):
                continue
            rel = src.relative_to(ROOT)
            dest = DEP / rel
            digest = sha(src)
            checked[rel.as_posix()] = digest
            if not dest.is_file() or sha(dest) != digest:
                failures.append('deployment mismatch: ' + rel.as_posix())
            elif dest.stat().st_mtime > stamp or src.stat().st_mtime > stamp:
                failures.append('input newer than fastfile: ' + rel.as_posix())
    names = set()
    for lang in ('all', 'english'):
        ledger = DEP / f'zone_source/{lang}/assetinfo/zm_tod2_cybercity.csv'
        for row in csv.DictReader(ledger.open(encoding='utf-8-sig', newline='')):
            names.add(row['name'])
    required = ['tod_archer_retriever_world', 'tod_archer_hook', 'tod_archer_cable',
                'tod_archer_retriever', 'tod_archer_retriever_flourish', 'tod_archer_grapple_view',
                'tod_archer_bo2_hands', 'tod_archer_retriever_view', 'tod_archer_grapple_hands',
                'tod_archer_hold', 'tod_archer_throw', 'tod_archer_flourish', 'tod_archer_flourish_idle',
                'tod_archer_grapple_raise', 'tod_archer_grapple_idle', 'tod_archer_grapple_lower',
                'i_tod_archer_axe_hud',
                'tod/archer/fx_tod_archer_trail', 'tod/archer/fx_tod_archer_impact',
                'tod/archer/fx_tod_archer_charge', 'tod/archer/fx_tod_archer_trail_charged',
                'i_tod_retriever_ember_atlas', 'scripts/zm/zm_tod2_cybercity/_tod_retriever.gsc',
                'i_tod_archer_charge_ring', 'ei/mtl_tod_archer_charge_ring',
                'mc/mtl_tod_archer_launcher',
                'scripts/zm/zm_tod2_cybercity/_tod_archer.gsc',
                'scripts/zm/zm_tod2_cybercity/_tod_archer.csc']
    for name in required:
        if name not in names:
            failures.append('asset absent from ledger: ' + name)
    linker_log = ROOT/'tmp/native_build/linker_last.log'
    if not linker_log.is_file() or linker_log.stat().st_mtime < stamp:
        failures.append('missing current linker transcript')
    else:
        # BO3 reports some missing render materials without an ERROR: prefix.
        # An asset-list entry alone therefore does not establish it can render.
        for line in linker_log.read_text(encoding='utf-8-sig', errors='replace').splitlines():
            if re.search(r'\^[13].*tod_(?:archer|retriever)', line):
                failures.append('Archer linker diagnostic: ' + line)
    model_rows = {}
    for lang in ('all', 'english'):
        ledger = DEP / f'zone_source/{lang}/assetinfo/zm_tod2_cybercity_xmodel.csv'
        for row in csv.DictReader(ledger.open(encoding='utf-8-sig', newline='')):
            model_rows[row['name']] = row
    compiled_models = {}
    motion = json.loads((ROOT/'art/archer_assets/engine_kit/native_motion.json').read_text())
    for name, expected in {'tod_archer_hook': [662], 'tod_archer_retriever_world': [1361, 250, 23],
                           'tod_archer_retriever_view':[motion['view_triangles']],
                           'tod_archer_bo2_hands':[motion['hand_triangles']],
                           'tod_archer_grapple_hands':[motion['hand_triangles']],
                           'tod_archer_grapple_view':[2200]}.items():
        row = model_rows.get(name)
        actual = [] if row is None else [int(row['tris'+str(i)]) for i in reversed(range(int(row['lodCount'])))]
        compiled_models[name] = actual
        if actual != expected:
            failures.append(f'compiled geometry mismatch: {name}: expected {expected}, got {actual}')
    map_rel = Path('map_source/zm/zm_tod2_cybercity.map')
    if sha(ROOT/map_rel) != sha(TOOLS/map_rel):
        failures.append('compiled map source differs from repository')
    if (ROOT/map_rel).stat().st_mtime > stamp:
        failures.append('map source newer than fastfile')
    aliases = {r['Name'] for r in csv.DictReader((DEP / 'sound/zone/zm_tod2_cybercity.all.alias.sz').open(encoding='utf-8-sig', newline=''))}
    expected_audio = ['tod_archer_axe_'+x for x in ('hit','throw','spin','return','catch','ready','first_raise')] + ['tod_archer_hook_'+x for x in ('fire','attach','pull','release','ready')]
    for name in expected_audio:
        if name not in aliases:
            failures.append('audio absent from bank: ' + name)
    entry = (DEP / 'scripts/zm/zm_tod2_cybercity.gsc').read_text(encoding='utf-8')
    dev_and_god = 'level.tod_dev = true;' in entry and 'level.tod_god = true;' in entry
    if not dev_and_god:
        failures.append('dev/god are not enabled')
    banks = {str(p.relative_to(DEP/'zone')):p.stat().st_size for p in (DEP/'zone/snd').rglob('*') if p.is_file()}
    if not any(n.endswith('.all.sabs') and size > 50*1024*1024 for n,size in banks.items()):
        failures.append('missing or truncated streaming bank')
    # Native art is synced at the private tools root, not inside the usermap.
    install = json.loads((ROOT/'art/archer_assets/engine_kit/install_manifest.json').read_text())
    native = ['source_data/tod_archer.gdt'] + list(install['textures']) + list(install.get('additional_gdts',{}))
    native += [r['file'] for r in install['models']] + [r['file'] for r in install['audio']]
    native += [r['file'] for r in install['animations']] + list(install['conversion_models'])
    native += [p.relative_to(ROOT).as_posix() for p in (ROOT/'share/raw/fx/tod/archer').glob('*.efx')]
    for relative in native:
        src,dest = ROOT/relative,TOOLS/relative
        checked[relative] = sha(src)
        if not dest.is_file() or sha(dest) != checked[relative]:
            failures.append('native art deployment mismatch: '+relative)
        elif src.stat().st_mtime > stamp or dest.stat().st_mtime > stamp:
            failures.append('native art newer than fastfile: '+relative)
    report = {
        'ff_bytes': FF.stat().st_size,
        'ff_local_time': datetime.datetime.fromtimestamp(stamp).isoformat(),
        'ff_sha256': sha(FF),
        'checked_deployed_inputs': len(checked),
        'input_sha256': checked,
        'required_assets': required,
        'compiled_model_triangles': compiled_models,
        'map_sha256': sha(ROOT/map_rel),
        'audio_aliases': expected_audio,
        'banks': banks,
        'failures': failures,
        'dev_and_god': dev_and_god,
        'native_playtest': 'not performed; user tests',
    }
    out = ROOT/'docs/archer_equipment_evidence/build.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'input_sha256'}, indent=2))
    raise SystemExit(1 if failures else 0)

if __name__ == '__main__':
    main()
