"""Check our authored assets stayed isolated, even during a separate Map One build."""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / 'tmp/tod2_isolation'
SHARED = Path('C:/Program Files (x86)/Steam/steamapps/common/Call of Duty Black Ops III 455130')
PRIVATE = Path('C:/BO3Tools/TOD2Cybercity')
before = json.loads((OUT / 'map_one_shared_before.json').read_text())
prefixes = ('source_data/', 'model_export/tod_teleporter/', 'share/raw/fx/',
            'map_source/zm/zm_tower_of_doom.map')
checked = 0
changed = []
for relative, old in before.items():
    if not relative.startswith(prefixes):
        continue
    checked += 1
    p = SHARED / relative
    now = [p.stat().st_size, p.stat().st_mtime_ns] if p.exists() else None
    if old != now:
        changed.append(relative)
assert not changed, ('Protected shared art sources changed; investigate ownership', changed)
assert not (SHARED / 'share/raw/fx/tod/teleporter').exists(), 'Tower II FX leaked into shared sources'
assert not (SHARED / 'map_source/zm/zm_tod2_cybercity.map').exists(), 'Tower II map leaked into shared source tree'
legacy_script = SHARED / 'usermaps/zm_tower_of_doom/scripts/zm/zm_tower_of_doom/_tod_teleport.gsc'
assert 'SetModel( "tod_teleporter" )' not in legacy_script.read_text(encoding='utf-8-sig')
assert 'fx_tod_tp_ready' not in legacy_script.read_text(encoding='utf-8-sig')
ledger = SHARED / 'usermaps/zm_tower_of_doom/zone_source/all/assetinfo/zm_tower_of_doom.csv'
with ledger.open(encoding='utf-8-sig', newline='') as f:
    foreign = [r for r in csv.DictReader(f) if 'zm_tod2_cybercity' in r['name']
               or r['name'].startswith('tod/teleporter/')
               or (r['type'] == 'xmodel' and r['name'] == 'tod_teleporter')]
assert not foreign, ('Tower II-only assets in Map One ledger', foreign)
link = SHARED / 'usermaps/zm_tod2_cybercity'
assert link.is_junction() and link.resolve() == (PRIVATE / 'usermaps/zm_tod2_cybercity').resolve()
report = {
    'protected_art_sources_checked': checked,
    'protected_art_source_metadata_changes': changed,
    'tower_ii_assets_in_map_one_ledger': foreign,
    'game_entry_resolves_to_private_workspace': str(link.resolve()),
    'concurrent_map_one_build_observed': any(
        '-modsource zm_tower_of_doom' in row.get('CommandLine', '')
        for row in json.loads((OUT / 'concurrent_build_processes.json').read_text(encoding='utf-8-sig'))),
    'whole_shared_install_unchanged_claimed': False,
    'note': 'A separate Map One build changed its own scripts/output/database. See concurrent_build_processes.json and the unfiltered metadata audit; do not revert its work.',
}
(OUT / 'separation_verification.json').write_text(json.dumps(report, indent=2) + '\n')
print('TOD II SEPARATION PASS:', json.dumps(report))
