"""Install the reviewed final sky bytes and preserve exact provenance."""
import datetime
import ast
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGE = ROOT / 'tmp/sky_middle_ground'
REVIEW = ROOT / 'art/sky3d/middle_ground_review'
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.modules.pop('pass_config', None)  # fresh pass paths even in the reused MCP studio
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
    stats = json.loads((REVIEW / 'final/middle_ground_stats.json').read_text(encoding='utf-8'))
    assert render['width'] == 8192 and render['samples'] == 160, 'Production render must be 8192 pixels at 160 samples'
    assert render['source_hashes'] == source_hashes(), 'Geometry source changed since rendering'
    assert sha(pathlib.Path(__file__).with_name('render_saved.py')) == render['renderer_sha256'], 'Renderer changed since rendering'
    assert sha(STAGE / 'raw_8192.title.json') == render['title_report_sha256'], 'Final title report differs from render receipt'
    for name, expected in render['art_inputs'].items():
        assert sha(pathlib.Path(name)) == expected, 'Image source changed since rendering: ' + name
    for key in ('raw', 'mask'):
        assert sha(pathlib.Path(render[key])) == render[key + '_sha256'] == finish[key + '_sha256'], key
    assert sha(STAGE / 'middle_ground.blend') == render['blend_sha256'], 'Master changed since rendering'
    assert pathlib.Path(stats['asset']).resolve() == STAGE / 'finished_8192.exr'
    assert stats['size'] == [8192, 4096] and stats['hold_city'] and abs(stats['score_city']-.64) < 1e-7
    assert sha(STAGE / 'finished_8192.exr') == finish['asset_sha256'], 'Finished asset differs from receipt'
    assert sha(REVIEW / 'final/middle_ground_stats.json') == finish['stats_sha256'], 'Finish stats differ from receipt'
    assert sha(ROOT / 'tools/sky3d/finish_sky.py') == finish['finish_source_sha256'], 'Finish source changed'
    pngs = sorted((REVIEW / 'final').glob('middle_ground_*.png'))
    tree = ast.parse((ROOT / 'tools/sky3d/finish_sky.py').read_text(encoding='utf-8'))
    views = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                 and isinstance(n.value, ast.List) and any(isinstance(t, ast.Name) and t.id == 'VIEWS' for t in n.targets))
    expected = {'middle_ground_sky_equirect.png'} | {'middle_ground_ingame_' + v[0] + '.png' for v in views}
    assert {p.name for p in pngs} == expected, 'Final pass must include the complete current VIEWS table'
    assert all(p.stat().st_mtime_ns >= pathlib.Path(render['raw']).stat().st_mtime_ns for p in pngs), 'Stale preview image'
    entries = []
    pairs = [
        (STAGE / 'finished_8192.exr', ROOT / 'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'),
        (STAGE / 'middle_ground.blend', ROOT / 'art/sky3d/tod2_sky.blend'),
    ]
    # Preserve the previously installed sky's exact bytes in the new pass.
    # The v8/v9 review directories and the approved v10 concept files are never written here.
    backups = []
    before = REVIEW / 'before'
    before.mkdir(parents=True, exist_ok=True)
    old = [dst for _, dst in pairs] + [ROOT / 'docs/sky_preview/sky3d_stats.json',
                                       ROOT / 'art/sky3d/simplify_preview.blend']
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
        dst = ROOT / 'docs/sky_preview' / src.name.replace('middle_ground_', 'sky3d_', 1)
        shutil.copyfile(src, dst)
        assert sha(src) == sha(dst), dst
    stats['staged_asset'] = stats['asset']
    stats['asset'] = str(pairs[0][1])
    stats['install_receipt'] = str(REVIEW / 'install.json')
    (ROOT / 'docs/sky_preview/sky3d_stats.json').write_text(json.dumps(stats, indent=2) + '\n', encoding='utf-8')
    receipt = {'installed_at': datetime.datetime.now().astimezone().isoformat(), 'files': entries,
               'preserved_previous_sky':backups,
               'preview_count': len(pngs), 'stage_stats': str(REVIEW / 'final/middle_ground_stats.json')}
    (REVIEW / 'install.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
