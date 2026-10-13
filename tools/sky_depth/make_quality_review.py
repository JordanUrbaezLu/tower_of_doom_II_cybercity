"""Display actual matched crop outputs at one image pixel per CSS pixel."""
import html
import json
from pass_config import ROOT, REVIEW, STAGE, sha

out = REVIEW / 'crops'
cases = ('before', 'after_old', 'after')
labels = dict(before='Previous geometry / previous sampling',
              after_old='Depth details / previous sampling',
              after='Depth details / candidate sampling')
receipts = {case: json.loads((out/(case+'.json')).read_text(encoding='utf-8')) for case in cases}
for case, receipt in receipts.items():
    assert receipt['case'] == case
    master = REVIEW/'before/tod2_sky.blend' if case == 'before' else STAGE/'depth.blend'
    assert receipt['master_sha256'] == sha(master)
    for info in receipt['images'].values():
        assert sha(ROOT/info['path']) == info['sha256']

parts = ['''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sky depth: matched angular-scale crops</title>
<style>body{background:#090b13;color:#dce1ea;font:16px/1.5 system-ui;margin:30px}
a{color:#dea6ff}.row{display:flex;gap:20px;overflow-x:auto;padding-bottom:16px}
figure{flex:none;margin:0}img{display:block;max-width:none}figcaption{max-width:650px}
p{max-width:1100px}</style></head><body><h1>Sky depth: matched crops</h1>
<p>Each crop uses the same saved camera, 8192-pixel panorama scale, seed and fixed inspection exposure.
Images retain their natural pixel dimensions; scroll horizontally to compare all three cases.
The first comparison isolates geometry/shading. The second isolates sampling.</p>
<p>These are Blender detail inspections with approximate display exposure. They do not include the final
native color finishing, game bloom or game exposure. Final skyline views and the user’s playtest remain separate.</p>''']
for view in ('mid_city','outer_city','roofscape'):
    parts.append('<h2>'+html.escape(view.replace('_',' ').title())+'</h2><div class="row">')
    bounds = receipts['before']['images'][view]['bounds']
    for case in cases:
        receipt = receipts[case]
        info = receipt['images'][view]
        assert info['bounds'] == bounds
        assert receipt['fixed_inspection_exposure'] == receipts['before']['fixed_inspection_exposure']
        filename = html.escape((ROOT/info['path']).name, quote=True)
        quality = receipt['render_quality']
        caption = (labels[case]+f" — filter {quality['filter_width']} px; adaptive threshold "
                   f"{quality['adaptive_threshold']}; minimum {quality['adaptive_min_samples']}, maximum {quality['samples']} samples.")
        parts.append(f'<figure><a href="{filename}"><img src="{filename}" alt="{html.escape(caption, quote=True)}"></a>'
                     f'<figcaption>{html.escape(caption)}</figcaption></figure>')
    parts.append('</div>')
parts.append('<p><a href="../review.html">Full skyline review</a></p></body></html>')
(out/'review.html').write_text('\n'.join(parts),encoding='utf-8')
print('MATCHED CROP GALLERY',out/'review.html')
