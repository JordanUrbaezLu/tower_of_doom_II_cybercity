"""Compare actual v10 authoring output with the retained v9 layout.

Run after author.py. Reads JSON only; never imports Blender or changes geometry.
Every historical lot field and megatower record must stay identical. The new
architecture label must cover all ordinary blocks and the intended smaller
near/middle spires, while taller landmark spires remain intact.
"""
import argparse
from collections import Counter
import datetime
import json
import pathlib
import sys

from pass_config import ROOT, STAGE, REVIEW, sha


def audit(before, after):
    errors = []

    def check(ok, message):
        if not ok:
            errors.append(message)

    old, new = before['buildings'], after['buildings']
    check(len(old) == len(new) == 1792, 'Ordinary lot count changed')
    changed_lots = []
    for i, (a, b) in enumerate(zip(old, new)):
        changed = [key for key, value in a.items() if b.get(key) != value]
        if changed:
            changed_lots.append({'index': i, 'changed_fields': changed})
    check(not changed_lots, 'Original lot placement, dimensions, seed or keep/drop decisions changed')
    check(before['megatowers'] == after['megatowers'], 'Megatower records or hero selection changed')
    for key in ('visible_buildings', 'station_keepout', 'celestial_counts', 'retired_body_objects'):
        check(before[key] == after[key], key + ' changed')
    check(after['visible_buildings'] == 1222, 'Moderate skyline reduction no longer totals 1222 groups')

    kept = [lot for lot in new if lot['kept']]
    modern, preserved = [], []
    for i, lot in enumerate(kept):
        wanted = not lot['spire'] or (lot['h'] < 400 and lot['distance'] < 7000)
        label = lot.get('architecture')
        check(isinstance(label, str) and bool(label), 'Missing architecture label at retained lot ' + str(i))
        got = isinstance(label, str) and label != 'preserved_spire'
        check(got == wanted, 'Coverage mismatch at retained lot ' + str(i))
        (modern if got else preserved).append(lot)
    expanded = [lot for lot in modern if lot['spire']]
    check(len(kept) == 1189 and len(modern) == 624 and len(expanded) == 357,
          'Expected 624 modern ordinary lots, including 357 newly covered smaller spires, of 1189 retained')
    heroes = [m for m in after['megatowers'] if m['hero'] and m['kept']]
    check(len(heroes) == 8, 'All eight preferred hero megatowers must remain')

    secondary = {}
    check(before['secondary'].keys() == after['secondary'].keys(), 'Secondary feature groups changed')
    for name, current in after['secondary'].items():
        previous = before['secondary'].get(name, {})
        old_ids, new_ids = set(previous.get('kept_ids', [])), set(current['kept_ids'])
        check(current['before'] == previous.get('before'), name + ' candidate count changed')
        check(current['after'] == len(new_ids) <= previous.get('after', -1), name + ' exceeds the reduced count')
        if name != 'floating_sigils':
            check(old_ids == new_ids, name + ' shifted despite retained host/layout contracts')
        hidden = current.get('hidden_host_ids')
        check(isinstance(hidden, list), name + ' lacks the authoring hidden_host_ids record')
        if isinstance(hidden, list):
            check(not new_ids.intersection(hidden), name + ' retained a feature on a retired host')
        secondary[name] = {'before_v10': previous.get('after'), 'after_v10': current['after'],
                           'retired_kept_ids': sorted(old_ids-new_ids),
                           'newly_selected_ids': sorted(new_ids-old_ids),
                           'hidden_host_ids': hidden,
                           'historically_visible_now_host_hidden': sorted(old_ids.intersection(hidden or []))}

    return {'status': 'pass' if not errors else 'failed', 'errors': errors,
            'changed_original_lots': changed_lots,
            'ordinary_candidates': len(new), 'ordinary_retained': len(kept),
            'modern_ordinary': len(modern), 'preserved_spires': len(preserved),
            'expanded_smaller_spires': len(expanded),
            'modern_archetypes': dict(sorted(Counter(x.get('architecture') for x in modern).items())),
            'modern_by_band': dict(sorted(Counter(x['band'] for x in modern).items())),
            'expanded_by_band': dict(sorted(Counter(x['band'] for x in expanded).items())),
            'retained_by_band': dict(sorted(Counter(x['band'] for x in kept).items())),
            'retained_megatowers': sum(x['kept'] for x in after['megatowers']),
            'retained_hero_megatowers': len(heroes), 'visible_buildings': after['visible_buildings'],
            'secondary': secondary, 'native_visual_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=pathlib.Path, default=ROOT/'tmp/sky_simplify/raw_4096.composition.json')
    parser.add_argument('--after', type=pathlib.Path, default=STAGE/'raw_4096.composition.json')
    args = parser.parse_args()
    result = audit(json.loads(args.before.read_text(encoding='utf-8')),
                   json.loads(args.after.read_text(encoding='utf-8')))
    result.update(checked_at=datetime.datetime.now().astimezone().isoformat(),
                  before={'path':str(args.before.resolve()), 'sha256':sha(args.before)},
                  after={'path':str(args.after.resolve()), 'sha256':sha(args.after)})
    REVIEW.mkdir(parents=True, exist_ok=True)
    path = REVIEW/'composition_audit.json'
    path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
