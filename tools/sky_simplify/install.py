"""Install the reviewed final sky bytes and preserve exact provenance."""
import datetime
import ast
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGE = ROOT / 'tmp/sky_simplify'
REVIEW = ROOT / 'art/sky3d/simplify_review'
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pass_config import source_hashes

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

def main():
    if (REVIEW / 'build_inputs.json').exists():
        raise RuntimeError('A build snapshot already exists; audit it before reinstalling')
    render = json.loads((STAGE / 'raw_8192.render.json').read_text(encoding='utf-8'))
    finish = json.loads((REVIEW / 'final/finish.json').read_text(encoding='utf-8'))
    stats = json.loads((REVIEW / 'final/simplify_stats.json').read_text(encoding='utf-8'))
    assert render['source_hashes'] == source_hashes(), 'Geometry source changed since rendering'
    for name, expected in render['art_inputs'].items():
        assert sha(pathlib.Path(name)) == expected, 'Image source changed since rendering: ' + name
    for key in ('raw', 'mask'):
        assert sha(pathlib.Path(render[key])) == render[key + '_sha256'] == finish[key + '_sha256'], key
    assert sha(STAGE / 'simplify.blend') == render['blend_sha256'], 'Master changed since rendering'
    assert pathlib.Path(stats['asset']).resolve() == STAGE / 'finished_8192.exr'
    assert stats['size'] == [8192, 4096] and stats['hold_city'] and abs(stats['score_city']-.64) < 1e-7
    assert sha(STAGE / 'finished_8192.exr') == finish['asset_sha256'], 'Finished asset differs from receipt'
    assert sha(REVIEW / 'final/simplify_stats.json') == finish['stats_sha256'], 'Finish stats differ from receipt'
    assert sha(ROOT / 'tools/sky3d/finish_sky.py') == finish['finish_source_sha256'], 'Finish source changed'
    pngs = sorted((REVIEW / 'final').glob('simplify_*.png'))
    tree = ast.parse((ROOT / 'tools/sky3d/finish_sky.py').read_text(encoding='utf-8'))
    views = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                 and isinstance(n.value, ast.List) and any(isinstance(t, ast.Name) and t.id == 'VIEWS' for t in n.targets))
    expected = {'simplify_sky_equirect.png'} | {'simplify_ingame_' + v[0] + '.png' for v in views}
    assert {p.name for p in pngs} == expected, 'Final pass must include the complete current VIEWS table'
    assert all(p.stat().st_mtime_ns >= pathlib.Path(render['raw']).stat().st_mtime_ns for p in pngs), 'Stale preview image'
    entries = []
    pairs = [
        (STAGE / 'finished_8192.exr', ROOT / 'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'),
        (STAGE / 'simplify.blend', ROOT / 'art/sky3d/tod2_sky.blend'),
    ]
    # Preserve the previously installed sky's exact bytes in the new pass.
    # The v8 cohesion_review directory and its receipts are never written here.
    backups = []
    before = REVIEW / 'before'
    before.mkdir(parents=True, exist_ok=True)
    old = [dst for _, dst in pairs] + [ROOT / 'docs/sky_preview/sky3d_stats.json',
                                       ROOT / 'art/sky3d/sky_preview.blend']
    for dst in old:
        backup = before / dst.name
        if dst.exists() and not backup.exists():
            shutil.copy2(dst, backup)
            assert sha(dst) == sha(backup), backup
        if backup.is_file():
            backups.append({'source':str(dst), 'preserved':str(backup), 'sha256':sha(backup)})
    for src, dst in pairs:
        assert src.is_file(), src
        shutil.copyfile(src, dst)
        assert sha(src) == sha(dst), dst
        entries.append({'source': str(src), 'installed': str(dst), 'sha256': sha(dst), 'bytes': dst.stat().st_size})
    for src in pngs:
        dst = ROOT / 'docs/sky_preview' / src.name.replace('simplify_', 'sky3d_', 1)
        shutil.copyfile(src, dst)
        assert sha(src) == sha(dst), dst
    stats['staged_asset'] = stats['asset']
    stats['asset'] = str(pairs[0][1])
    stats['install_receipt'] = str(REVIEW / 'install.json')
    (ROOT / 'docs/sky_preview/sky3d_stats.json').write_text(json.dumps(stats, indent=2) + '\n', encoding='utf-8')
    receipt = {'installed_at': datetime.datetime.now().astimezone().isoformat(), 'files': entries,
               'preserved_previous_sky':backups,
               'preview_count': len(pngs), 'stage_stats': str(REVIEW / 'final/simplify_stats.json')}
    (REVIEW / 'install.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
