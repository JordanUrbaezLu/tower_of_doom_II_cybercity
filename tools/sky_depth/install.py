"""Install the reviewed final sky bytes and preserve exact provenance."""
import datetime
import ast
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGE = ROOT / 'tmp/sky_depth'
REVIEW = ROOT / 'art/sky3d/depth_review'
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.modules.pop('pass_config', None)  # fresh pass paths even in the reused MCP studio
from pass_config import source_hashes
from finish_profile import check_stats
from quality_profile import PROFILE_PATH as QUALITY_PROFILE_PATH, load_quality, expected_quality

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
    stats = json.loads((REVIEW / 'final/depth_stats.json').read_text(encoding='utf-8'))
    title = json.loads((STAGE / 'raw_8192.title.json').read_text(encoding='utf-8'))
    author = json.loads((STAGE / 'author.json').read_text(encoding='utf-8'))
    quality = load_quality()
    for name, receipt in (('author', author), ('render', render)):
        assert receipt['quality_profile'] == quality, name + ' quality configuration changed'
        assert receipt['quality_profile_sha256'] == sha(QUALITY_PROFILE_PATH), name + ' quality profile hash changed'
        assert receipt['render_quality'] == expected_quality(quality), name + ' actual production quality differs'
    assert author.get('options', {}).get('sign_state') == 'dull', 'Master must be authored in the dull state'
    assert author['source_hashes'] == source_hashes(), 'Authoring sources changed'
    assert author['blend_sha256'] == render['blend_sha256'], 'Render belongs to a different master'
    crop_review_path = REVIEW / 'crops/review.json'
    crop_review = json.loads(crop_review_path.read_text(encoding='utf-8'))
    assert (crop_review['status'] == 'accepted'
            and crop_review['profile_sha256'] == sha(QUALITY_PROFILE_PATH)
            and crop_review['candidate_master_sha256'] == author['blend_sha256']
            and crop_review['reviewed_cases'] == ['before', 'after_old', 'after']
            and bool(crop_review['note'].strip())), 'Actual master and quality profile require accepted visual crop review before install'
    assert title.get('sign_state') == 'dull', 'Shipping sky must contain the dull before-jump sign'
    assert render['width'] == 8192 and render['samples'] == 160, 'Production render must be 8192 pixels at 160 samples'
    assert render['source_hashes'] == source_hashes(), 'Geometry source changed since rendering'
    assert sha(pathlib.Path(__file__).with_name('render_saved.py')) == render['renderer_sha256'], 'Renderer changed since rendering'
    assert sha(STAGE / 'raw_8192.title.json') == render['title_report_sha256'], 'Final title report differs from render receipt'
    for name, expected in render['art_inputs'].items():
        assert sha(pathlib.Path(name)) == expected, 'Image source changed since rendering: ' + name
    for key in ('raw', 'mask'):
        assert sha(pathlib.Path(render[key])) == render[key + '_sha256'] == finish[key + '_sha256'], key
    assert sha(STAGE / 'depth.blend') == render['blend_sha256'], 'Master changed since rendering'
    assert pathlib.Path(stats['asset']).resolve() == STAGE / 'finished_8192.exr'
    assert stats['size'] == [8192, 4096]
    profile = check_stats(stats, finish)
    assert sha(STAGE / 'finished_8192.exr') == finish['asset_sha256'], 'Finished asset differs from receipt'
    assert sha(REVIEW / 'final/depth_stats.json') == finish['stats_sha256'], 'Finish stats differ from receipt'
    assert sha(ROOT / 'tools/sky3d/finish_sky.py') == finish['finish_source_sha256'], 'Finish source changed'
    pngs = sorted((REVIEW / 'final').glob('depth_*.png'))
    tree = ast.parse((ROOT / 'tools/sky3d/finish_sky.py').read_text(encoding='utf-8'))
    views = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                 and isinstance(n.value, ast.List) and any(isinstance(t, ast.Name) and t.id == 'VIEWS' for t in n.targets))
    expected = {'depth_sky_equirect.png'} | {'depth_ingame_' + v[0] + '.png' for v in views}
    assert {p.name for p in pngs} == expected, 'Final pass must include the complete current VIEWS table'
    assert all(p.stat().st_mtime_ns >= pathlib.Path(render['raw']).stat().st_mtime_ns for p in pngs), 'Stale preview image'
    entries = []
    pairs = [
        (STAGE / 'finished_8192.exr', ROOT / 'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'),
        (STAGE / 'depth.blend', ROOT / 'art/sky3d/tod2_sky.blend'),
    ]
    # Preserve the previously installed sky's exact bytes in the new pass.
    # Previous review folders and the approved v10 concept are read-only history.
    backups = []
    before = REVIEW / 'before'
    before.mkdir(parents=True, exist_ok=True)
    old = [dst for _, dst in pairs] + [ROOT / 'docs/sky_preview/sky3d_stats.json',
                                       ROOT / 'art/sky3d/dealer_preview.blend']
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
        dst = ROOT / 'docs/sky_preview' / src.name.replace('depth_', 'sky3d_', 1)
        shutil.copyfile(src, dst)
        assert sha(src) == sha(dst), dst
    stats['staged_asset'] = stats['asset']
    stats['asset'] = str(pairs[0][1])
    stats['install_receipt'] = str(REVIEW / 'install.json')
    (ROOT / 'docs/sky_preview/sky3d_stats.json').write_text(json.dumps(stats, indent=2) + '\n', encoding='utf-8')
    receipt = {'installed_at': datetime.datetime.now().astimezone().isoformat(), 'files': entries,
               'preserved_previous_sky':backups,
               'preview_count': len(pngs), 'stage_stats': str(REVIEW / 'final/depth_stats.json'),
               'finish_profile': profile, 'quality_profile': quality,
               'quality_profile_sha256': sha(QUALITY_PROFILE_PATH),
               'crop_review': str(crop_review_path), 'crop_review_sha256': sha(crop_review_path),
               'measured_city_score': stats['score_city'], 'measured_whole_score': stats['score']}
    (REVIEW / 'install.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
