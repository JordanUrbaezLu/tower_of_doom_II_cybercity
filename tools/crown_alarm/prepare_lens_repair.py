"""Snapshot current alarm assets; never edit shipping inputs during review."""
import hashlib, json, pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = ROOT / 'tmp/alarm_lens_repair'
BASE, STAGE = WORK / 'baseline', WORK / 'staged'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def prepare():
    receipt = WORK / 'baseline_hashes.json'
    if receipt.exists():
        hashes = json.loads(receipt.read_text())
        for rel, digest in hashes.items():
            assert sha(ROOT / rel) == digest, 'Live asset changed since snapshot: ' + rel
            assert sha(BASE / rel) == digest, 'Baseline changed: ' + rel
        return
    files = []
    for family in ('crown_alarm', 'alarm_button'):
        files.extend(p for p in (ROOT / 'model_export' / ('tod_' + family)).rglob('*') if p.is_file())
        files += [ROOT / 'source_data' / ('tod_' + family + '.gdt'), ROOT / 'art' / family / 'manifest.json']
    files += [ROOT / 'art/crown_alarm/crown_alarm.blend', ROOT / 'art/crown_alarm/visibility_review/high_fixture.blend',
              ROOT / 'tools/crown_alarm/light_profile.json', ROOT / 'share/raw/fx/tod/crown_alarm/fx_tod_alarm_sweep.efx',
              ROOT / 'share/raw/fx/tod/crown_alarm/fx_tod_alarm_high.efx', ROOT / 'zone_source/tod_crown_alarm.zpkg']
    hashes = {}
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        digest = sha(path)
        for dest in (BASE / rel, STAGE / rel):
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            assert sha(dest) == digest
        assert sha(path) == digest, 'Changed during capture: ' + rel
        hashes[rel] = digest
    receipt.write_text(json.dumps(hashes, indent=2) + '\n')
    print('LENS_BASELINE_CAPTURED', len(hashes))

if __name__ == '__main__':
    prepare()
