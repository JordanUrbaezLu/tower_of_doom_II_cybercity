"""Vendor the selected donor sound banks into this map, with usable contexts."""
import csv
import io
import json
import shutil
from pathlib import Path
from prepare_expected_roster import ROOT, TOOLS, SIBLING, write

if __name__ == '__main__':
    # R5 (2026-10-04): the R-99 and heirloom banks left with the Map 1 purge; the two sword banks keep only the
    # aliases a Map 2 weapon plays, so a re-run cannot re-vendor the archived rows.
    sources = [('hb_crossbow.csv', None), ('hb_citadel_swords.csv', None), ('hb_gold_sword.csv', None)]
    keep = {'hb_citadel_swords.csv': {'hb_citadel_swing', 'hb_citadel_raise', 'hb_citadel_hit', 'hb_citadel_surface_hit',
                                      'hb_caliburn_idle', 'hb_caliburn_ready'},
            'hb_gold_sword.csv': {'hb_gold_sword_smash'}}
    fields = next(csv.reader((ROOT / 'sound/aliases/tod_ports.csv').open(encoding='utf-8-sig')))
    rows, copied = [], set()
    for filename, prefix in sources:
        for row in csv.DictReader((SIBLING / 'sound/aliases' / filename).open(encoding='utf-8-sig')):
            if prefix and not row['Name'].startswith(prefix):
                continue
            if filename in keep and row.get('Name') not in keep[filename]:
                continue
            if not row.get('Name') or row['Name'].startswith('#'):
                continue
            if row.get('ContextType') == 'water' and row.get('ContextValue') == 'under':
                continue
            for i in ('', '1', '2', '3'):
                row['ContextType' + i] = ''
                row['ContextValue' + i] = ''
            for col in ('FileSpec', 'FileSpecSustain', 'FileSpecRelease'):
                if not row.get(col):
                    continue
                relative = Path(row[col].replace('\\', '/'))
                target = ROOT / 'sound_assets' / relative
                assert target.resolve().is_relative_to((ROOT / 'sound_assets').resolve())
                source = SIBLING / 'sound_assets' / relative
                if not source.is_file():
                    source = TOOLS / 'sound_assets' / relative
                if not source.is_file():
                    raise FileNotFoundError(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists() or target.read_bytes() != source.read_bytes():
                    shutil.copy2(source, target)
                copied.add(relative.as_posix())
            rows.append(row)
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    write('sound/aliases/tod_expected_roster.csv', out.getvalue())
    path = ROOT / 'sound/zoneconfig/zm_tod2_cybercity.szc'
    szc = json.loads(path.read_text())
    for name in ('tod_expected_roster', 'elemental_bow_sounds'):
        if not any(s.get('Name') == name for s in szc['Sources']):
            szc['Sources'].append(dict(Type='ALIAS', Name=name, Filename=name + '.csv', Specs=[]))
    write(path.relative_to(ROOT), json.dumps(szc, indent=1) + '\n')
    print(f'Vendored {len(rows)} alias rows and {len(copied)} sound files; stock bow bank registered.')
