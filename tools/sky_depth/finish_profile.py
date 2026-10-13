"""Read and enforce this pass's exact reviewed baseline gain; no writes."""
import json
import math
import pathlib

from pass_config import ROOT, sha

PROFILE_PATH = pathlib.Path(__file__).with_suffix('.json')


def load_profile():
    profile = json.loads(PROFILE_PATH.read_text(encoding='utf-8'))
    if profile['schema'] != 1 or profile['mode'] != 'fixed_baseline_gain':
        raise ValueError('Unknown depth finish profile')
    baseline = ROOT / profile['baseline_stats']
    if sha(baseline) != profile['baseline_stats_sha256']:
        raise ValueError('Reviewed baseline stats changed')
    original = json.loads(baseline.read_text(encoding='utf-8'))
    gain = profile['fixed_gain']
    if not math.isfinite(gain) or gain <= 0 or gain != original['gain']:
        raise ValueError('Fixed gain must equal the exact reviewed baseline gain')
    if profile['nominal_target_score'] != original['target_score']:
        raise ValueError('Nominal target differs from the baseline metadata')
    return profile


def check_stats(stats, finish=None):
    profile = load_profile()
    if (stats.get('gain_mode') != 'fixed' or stats.get('gain') != profile['fixed_gain']
            or stats.get('fixed_gain') != profile['fixed_gain']):
        raise ValueError('Finish must use the exact fixed baseline gain')
    if stats.get('target_score') != profile['nominal_target_score'] or stats.get('hold_city') is not True:
        raise ValueError('Nominal finish target/sign-mask convention changed')
    if not all(math.isfinite(stats[key]) and stats[key] > 0 for key in ('score_city', 'score')):
        raise ValueError('Measured city/whole-sky score must be finite and positive')
    if finish is not None and finish.get('finish_profile_sha256') != sha(PROFILE_PATH):
        raise ValueError('Finish receipt does not bind the current gain profile')
    return profile
