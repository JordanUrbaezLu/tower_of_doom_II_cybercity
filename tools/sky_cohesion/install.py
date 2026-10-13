"""Install the reviewed final sky bytes and preserve exact provenance."""
import datetime
import hashlib
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGE = ROOT / 'tmp/sky_cohesion'
REVIEW = ROOT / 'art/sky3d/cohesion_review'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

def main():
    if (REVIEW / 'build_inputs.json').exists():
        raise RuntimeError('A build snapshot already exists; audit it before reinstalling')
    entries = []
    pairs = [
        (STAGE / 'finished_8192.exr', ROOT / 'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'),
        (STAGE / 'cohesion.blend', ROOT / 'art/sky3d/tod2_sky.blend'),
    ]
    for src, dst in pairs:
        assert src.is_file(), src
        backup = STAGE / ('before_' + dst.name)
        if dst.exists() and not backup.exists():
            shutil.copy2(dst, backup)
        shutil.copyfile(src, dst)
        assert sha(src) == sha(dst), dst
        entries.append({'source': str(src), 'installed': str(dst), 'sha256': sha(dst), 'bytes': dst.stat().st_size})
    pngs = sorted((REVIEW / 'final').glob('cohesion_*.png'))
    assert len(pngs) == 22, len(pngs)
    for src in pngs:
        dst = ROOT / 'docs/sky_preview' / src.name.replace('cohesion_', 'sky3d_', 1)
        shutil.copyfile(src, dst)
        assert sha(src) == sha(dst), dst
    stats = json.loads((REVIEW / 'final/cohesion_stats.json').read_text())
    stats['staged_asset'] = stats['asset']
    stats['asset'] = str(pairs[0][1])
    stats['install_receipt'] = str(REVIEW / 'install.json')
    (ROOT / 'docs/sky_preview/sky3d_stats.json').write_text(json.dumps(stats, indent=2) + '\n', encoding='utf-8')
    receipt = {'installed_at': datetime.datetime.now().astimezone().isoformat(), 'files': entries,
               'preview_count': len(pngs), 'stage_stats': str(REVIEW / 'final/cohesion_stats.json')}
    (REVIEW / 'install.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
