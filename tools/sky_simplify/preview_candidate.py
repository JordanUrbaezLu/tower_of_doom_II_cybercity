"""Show the reviewed 4K candidate while the saved production master renders.

This writes only temporary preview files. The final preview.py uses the installed
8K native sky after review. Run after saving/finalizing the editable master.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
script = (ROOT / 'tools/sky_simplify/preview.py').read_text(encoding='utf-8')
replacements = {
    'docs/sky_preview/sky3d_stats.json': 'art/sky3d/simplify_review/preview4096/simplify_stats.json',
    'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr': 'tmp/sky_simplify/finished_4096.exr',
    'art/sky3d/simplify_preview.blend': 'tmp/sky_simplify/candidate_preview.blend',
    'art/sky3d/simplify_review/preview.json': 'tmp/sky_simplify/candidate_preview.json',
    'Finished native HDR panorama': 'Intermediate 4K candidate HDR panorama',
    'CYBERCITY SKY PREVIEW': 'CYBERCITY 4K CANDIDATE',
}
for source, target in replacements.items():
    assert source in script, source
    script = script.replace(source, target)
exec(compile(script, str(ROOT / 'tools/sky_simplify/preview.py'), 'exec'))
