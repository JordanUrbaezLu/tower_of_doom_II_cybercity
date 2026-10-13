"""Publish the reviewed binding follow-up without replacing the original capture.

The first opacity candidate is already installed. Capture its exact live hashes,
then require them unchanged before publishing the corrected, rendered source
set. No sync/build/game/native cache changes are made by this installer.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'tmp/alarm_lens_repair'
CANDIDATE = WORK / 'binding_candidate'
STAGE = WORK / 'staged'
CAPTURE = WORK / 'binding_live_before.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def load_gate(path=None):
    path = path or ROOT / 'tools/crown_alarm/lens_repair_gate.py'
    spec = importlib.util.spec_from_file_location('lens_publish_gate', path)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    # Isolated candidates have a deeper filesystem location. Give their
    # reviewed validation functions the actual workspace/capture explicitly.
    gate.ROOT, gate.WORK = ROOT, WORK
    gate.BASE, gate.STAGE = WORK / 'baseline', STAGE
    return gate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', action='store_true')
    args = parser.parse_args()
    sources = json.loads((CANDIDATE / 'candidate_sources.json').read_text())['files']
    baseline = json.loads((WORK / 'baseline_hashes.json').read_text())
    if args.capture:
        assert not CAPTURE.exists(), 'Never replace the follow-up capture'
        # Native protected inputs are already covered by the original gate.
        live = {rel: sha(ROOT / rel) for rel in baseline}
        for rel, pins in sources.items():
            assert sha(ROOT / rel) == pins['baseline_sha256'], 'Live helper changed: ' + rel
            backup = WORK / 'binding_sources_before' / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, backup)
            live[rel] = pins['baseline_sha256']
        CAPTURE.write_text(json.dumps({'captured_at': datetime.datetime.now().astimezone().isoformat(),
                                      'files': live}, indent=2) + '\n')
        print('LENS_BINDING_FOLLOWUP_CAPTURED', len(live), 'live files; original baseline retained')
        return
    gate = load_gate()
    gate.require_idle()
    live = json.loads(CAPTURE.read_text())['files']
    for rel, digest in live.items():
        assert sha(ROOT / rel) == digest, 'Live captured input changed; refuse overwrite: ' + rel
    receipt = json.loads((STAGE / 'art/crown_alarm/lens_review/authoring.json').read_text())
    assert receipt['specColorMap'] == '$black_specular' and receipt['native_specular_mask'] == 0
    for name in ('before_off.png', 'before_on.png', 'after_off.png', 'after_on.png', 'distance_off.png', 'distance_on.png'):
        assert sha(STAGE / 'art/crown_alarm/lens_review' / name) == receipt['renders'][name], 'Incomplete render: ' + name
    preview = json.loads((STAGE / 'art/crown_alarm/lens_review/preview.json').read_text())
    assert preview['complete_authoring_receipt_verified'] is True
    assert preview['authoring_receipt_sha256'] == sha(STAGE / 'art/crown_alarm/lens_review/authoring.json'), 'Stale preview receipt'
    assert preview['native_preview_sha256'] == sha(STAGE / 'art/crown_alarm/lens_review/native_preview.blend'), 'Stale native preview'
    assert preview['native_specular_mask'] == 0
    assert sha(STAGE / 'art/crown_alarm/lens_review/rotation_on_bloom.png') == preview['bloom_rotation_render_sha256']
    for rel, pins in sources.items():
        assert sha(CANDIDATE / rel) == pins['candidate_sha256'], 'Reviewed candidate changed: ' + rel
    # Validate the candidate gate without first replacing its live copy.
    gate = load_gate(CANDIDATE / 'tools/crown_alarm/lens_repair_gate.py')
    report, _, files = gate.verify(STAGE)
    for rel, digest in live.items():
        assert sha(ROOT / rel) == digest, 'Source changed during validation: ' + rel
    gate.require_idle()
    # Review/master first; maps/GDT/package next; the native manifest is last.
    files.sort(key=lambda rel: (0 if rel.startswith(gate.REVIEW) or rel in gate.MASTERS else
                               1 if rel == gate.LENS else 2 if rel == gate.GDT else
                               3 if rel == gate.PACKAGE else 4, rel))
    installed, rollback = [], []
    native_changes = {gate.LENS, gate.GDT, gate.PACKAGE, gate.MANIFEST, *gate.MASTERS}
    backup_root = WORK / 'binding_publication_backup'
    try:
        for rel in [*sources, *files]:
            source = CANDIDATE / rel if rel in sources else STAGE / rel
            dest = ROOT / rel
            if dest.exists() and sha(source) == sha(dest):
                continue
            gate.require_idle()
            if rel in sources or rel in native_changes:
                backup = backup_root / rel
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dest, backup)
                rollback.append((rel, sha(source), backup))
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            assert sha(source) == sha(dest)
            installed.append({'path': rel, 'sha256': sha(dest)})
        gate.verify(ROOT)
    except BaseException:
        # Restore only files still equal to this transaction's candidate;
        # another session's later edit is never overwritten by rollback.
        for rel, candidate_hash, backup in reversed(rollback):
            dest = ROOT / rel
            assert sha(dest) == candidate_hash, 'Peer edit prevents safe rollback: ' + rel
            shutil.copy2(backup, dest)
        raise
    proof = {'installed_at': datetime.datetime.now().astimezone().isoformat(),
             'prior_live_capture_sha256': sha(CAPTURE), 'original_baseline_retained': True,
             'reviewed_sources': sources, 'installed': installed, 'validation': report,
             'native_playtested': False, 'guarded_full_build_required': True}
    for path in (WORK / 'binding_installation.json', ROOT / 'art/crown_alarm/lens_review/binding_installation.json'):
        path.write_text(json.dumps(proof, indent=2) + '\n')
    print('LENS_BINDING_FOLLOWUP_INSTALLED', len(installed), 'reviewed assets; original capture unchanged')


if __name__ == '__main__':
    main()
