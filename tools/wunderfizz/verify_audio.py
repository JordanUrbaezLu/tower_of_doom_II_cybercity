"""Verify frozen BO6 PCM/alias source and this map's completed native sound build."""
from __future__ import annotations
import argparse, csv, hashlib, json, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path('C:/BO3Tools/TOD2Cybercity')
MAP = 'zm_tod2_cybercity'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def verify(root, manifest, integration=True):
    for item in manifest['files']:
        p = root / item['path']
        assert sha(p) == item['sha256'], ('BO6 PCM drift', item['path'])
        with wave.open(str(p), 'rb') as audio:
            assert (audio.getframerate(), audio.getsampwidth(), audio.getnchannels(), audio.getnframes()) == (
                item['sample_rate'], 2, item['channels'], item['frames']), item['path']
    alias = root / manifest['alias_subset']['path']
    assert sha(alias) == manifest['alias_subset']['sha256'], 'Original native alias rows changed'
    rows = list(csv.DictReader(alias.open(encoding='utf-8-sig', newline='')))
    assert len(rows) == 7
    assert rows == manifest['alias_subset']['native_rows'], 'Native sound semantics changed'
    assert {r['Name'] for r in rows} == set(manifest['alias_subset']['names'])
    assert sum(r['Looping'] == 'looping' for r in rows) == 1
    assert rows[0]['Secondary'] == 'evt_wunderfizz_activate_electricity'
    assert all(r['PanType'] == '3d' and r['Storage'] == 'loaded' for r in rows)
    if integration:
        szc = json.loads((root / f'sound/zoneconfig/{MAP}.szc').read_text(encoding='utf-8-sig'))
        assert sum(s == manifest['integration']['source'] for s in szc['Sources']) == 1, 'Sound source missing/duplicated'
    return rows

def native(ff, manifest, rows):
    dep = TOOLS / 'usermaps' / MAP
    assert ff.resolve() == (dep / 'zone' / (MAP + '.ff')).resolve(), 'Only the owned map may be audited'
    assert ff.is_file()
    for item in manifest['files']:
        assert sha(TOOLS / item['path']) == item['sha256'], ('Unsynced PCM', item['path'])
    alias = dep / 'sound/zone' / (MAP + '.all.alias.sz')
    assert alias.is_file() and alias.stat().st_mtime <= ff.stat().st_mtime, 'Native alias table missing/newer than FF'
    # Cached banks may be reused when only gameplay or image inputs change.
    # Their freshness must cover the actual audio inputs, not a later snapshot
    # of unrelated code. Exact PCM and native alias fields remain mandatory.
    audio_inputs = [ROOT / item['path'] for item in manifest['files']]
    audio_inputs += [ROOT / manifest['alias_subset']['path'], ROOT / f'sound/zoneconfig/{MAP}.szc']
    audio_source_time = max(path.stat().st_mtime for path in audio_inputs)
    assert alias.stat().st_mtime >= audio_source_time, 'Native alias table predates an audio input'
    built = list(csv.DictReader(alias.open(encoding='utf-8-sig', newline='')))
    selected = [r for r in built if r['Name'] in manifest['alias_subset']['names']]
    assert len(selected) == 7, ('Native machine aliases missing/duplicated', len(selected))
    for expected in rows:
        matches = [r for r in selected if r['Name'] == expected['Name'] and
                   r['FileSpec'].replace('\\', '/').lower() == expected['FileSpec'].replace('\\', '/').lower()]
        assert len(matches) == 1, ('Native sound FileSpec drift', expected['Name'])
        for key in ('Looping', 'Secondary', 'PanType', 'Storage', 'LimitCount', 'EntityLimitCount'):
            # The sound compiler canonicalizes native enum names to uppercase.
            assert matches[0][key].strip().lower() == expected[key].strip().lower(), ('Native sound field drift', expected['Name'], key)
    banks = [p for p in (dep / 'zone/snd').rglob('*.all.sabl') if p.is_file()]
    assert banks and all(p.stat().st_size > 1024 * 1024 and p.stat().st_mtime <= ff.stat().st_mtime for p in banks), 'Loaded sound bank missing/truncated/newer than FF'
    assert all(p.stat().st_mtime >= audio_source_time for p in banks), 'Loaded sound bank predates an audio input'
    report = dict(ff_sha256=sha(ff), ff_bytes=ff.stat().st_size, aliases=selected,
                  audio_source_latest_time=audio_source_time,
                  freshness_basis='Exact audio inputs; unchanged native banks may be reused for a gameplay/image relink.',
                  loaded_banks=[dict(path=str(p.relative_to(dep)), bytes=p.stat().st_size, sha256=sha(p)) for p in banks],
                  proof='Source PCM parity, generated native alias fields and complete loaded bank. Native audibility is pending user playtest.',
                  game_launched=False)
    out = ROOT / 'art/wunderfizz/native_audio.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--manifest', type=Path, default=ROOT / 'art/wunderfizz/audio_manifest.json')
    p.add_argument('--no-integration', action='store_true')
    p.add_argument('--native', type=Path)
    args = p.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    rows = verify(args.root, manifest, not args.no_integration)
    if args.native:
        native(args.native, manifest, rows)
    print('BO6 WUNDERFIZZ AUDIO PASS: 7 original PCM files, native loop/3D/Secondary/limit fields' + ('; native alias table and loaded bank' if args.native else ''))

if __name__ == '__main__':
    main()
