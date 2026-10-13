"""Compare consistency-pass authoring output with the approved v10 layout.

Run after author.py. Reads JSON only; never imports Blender or changes geometry.
Every historical placement field and megatower record must stay identical.
Architecture labels must cover all 1,189 ordinary lots, at every distance.
The preferred eight placed hero towers retain their layout and silhouette roles.
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
        # Architecture is the one deliberately revised field; seeds, bounds,
        # placement, spire identity and historical retention remain exact.
        changed = [key for key, value in a.items()
                   if key != 'architecture' and b.get(key) != value]
        if changed:
            changed_lots.append({'index': i, 'changed_fields': changed})
    check(not changed_lots, 'Original lot placement, dimensions, seed or keep/drop decisions changed')
    check(before['megatowers'] == after['megatowers'], 'Megatower records or hero selection changed')
    for key in ('visible_buildings', 'station_keepout', 'celestial_counts', 'retired_body_objects'):
        check(before[key] == after[key], key + ' changed')
    check(after['visible_buildings'] == 1222, 'Moderate skyline reduction no longer totals 1222 groups')

    baseline_kept = [lot for lot in old if lot['kept']]
    baseline_modern = [lot for lot in baseline_kept if lot.get('architecture') != 'preserved_spire']
    check(len(baseline_kept) == 1189 and len(baseline_modern) == 624,
          'Baseline must be the approved v10 layout with 624 modern / 1189 ordinary lots')
    kept = [lot for lot in new if lot['kept']]
    modern, preserved = [], []
    for i, lot in enumerate(kept):
        label = lot.get('architecture')
        check(isinstance(label, str) and bool(label), 'Missing architecture label at retained lot ' + str(i))
        got = label in {'tapered_keel', 'split_crown', 'cantilever_relay', 'offset_slot'}
        check(got, 'Ordinary lot lacks the shared cyber kit at retained lot ' + str(i))
        (modern if got else preserved).append(lot)
    expanded = [b for a, b in zip(old, new) if b['kept'] and a.get('architecture') == 'preserved_spire'
                and b.get('architecture') in {'tapered_keel', 'split_crown', 'cantilever_relay', 'offset_slot'}]
    check(len(kept) == len(modern) == 1189 and len(expanded) == 565 and not preserved,
          'Expected all 1189 ordinary lots modern, including the remaining 565 legacy spires')
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
        else:
            check(new_ids <= old_ids, name + ' selected a new feature while removing obsolete host crowns')
        hidden = current.get('hidden_host_ids')
        check(isinstance(hidden, list), name + ' lacks the authoring hidden_host_ids record')
        if isinstance(hidden, list):
            check(not new_ids.intersection(hidden), name + ' retained a feature on a retired host')
        secondary[name] = {'before_v10': previous.get('after'), 'after_consistency': current['after'],
                           'retired_kept_ids': sorted(old_ids-new_ids),
                           'newly_selected_ids': sorted(new_ids-old_ids),
                           'hidden_host_ids': hidden,
                           'historically_visible_now_host_hidden': sorted(old_ids.intersection(hidden or []))}

    return {'status': 'pass' if not errors else 'failed', 'errors': errors,
            'changed_original_lots': changed_lots,
            'ordinary_candidates': len(new), 'ordinary_retained': len(kept),
            'modern_ordinary': len(modern), 'preserved_spires': len(preserved),
            'newly_modernized_spires': len(expanded),
            'modern_archetypes': dict(sorted(Counter(x.get('architecture') for x in modern).items())),
            'modern_by_band': dict(sorted(Counter(x['band'] for x in modern).items())),
            'expanded_by_band': dict(sorted(Counter(x['band'] for x in expanded).items())),
            'retained_by_band': dict(sorted(Counter(x['band'] for x in kept).items())),
            'retained_megatowers': sum(x['kept'] for x in after['megatowers']),
            'retained_hero_megatowers': len(heroes), 'visible_buildings': after['visible_buildings'],
            'secondary': secondary, 'native_visual_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=pathlib.Path, default=REVIEW/'before/composition.json')
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
