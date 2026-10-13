"""Prove the depth pass preserves the accepted Dealer painting and FX anchors.

Only existing image pixels are measured. This writes JSON, never image pixels.
The separate derived native bake may change its visibility alpha to match the
actual updated foreground, while the source painting remains byte-identical.
"""
import ast
import json
import numpy as np
from PIL import Image
from pass_config import ROOT, REVIEW, sha

SOURCE = ROOT/'art/sky3d/sign/v12_dealer.png'
BASELINE = ROOT/'art/sky3d/dealer_review/art_measurements.json'
ACCEPTED_SOURCE_SHA256 = 'e22016bec6747396b71b4aa20aff1ff472f696f28704ced746191d277a995a17'
previous = json.loads(BASELINE.read_text(encoding='utf-8'))
assert sha(SOURCE) == previous['hashes'][-1] == ACCEPTED_SOURCE_SHA256, 'Accepted Dealer painting changed'
with Image.open(SOURCE) as image:
    assert image.mode == 'RGBA' and image.size == (1536, 1024)
    pixels = np.asarray(image, dtype=float)
values = {}
for node in ast.parse((ROOT/'tools/sky3d/cyber_hero_title.py').read_text(encoding='utf-8')).body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in {'FEATURE_PIXELS', 'TITLE_CENTER_PX'}:
                values[target.id] = ast.literal_eval(node.value)
assert list(values['TITLE_CENTER_PX']) == previous['title_center_px'] == [768.0, 435.0]
anchors = {}
for name, old in previous['features'].items():
    x0, y0, x1, y1 = old['rect']
    z = pixels[y0:y1, x0:x1, :3]
    yy, xx = np.indices(z.shape[:2])
    weights = np.maximum(0, z.min(2)-150)
    assert weights.sum() > 0, name
    measured = [float((xx*weights).sum()/weights.sum()+x0), float((yy*weights).sum()/weights.sum()+y0)]
    contract = [c+d for c,d in zip(values['TITLE_CENTER_PX'], values['FEATURE_PIXELS'][name])]
    assert contract == old['contract'], 'Cinematic feature moved: '+name
    error = max(abs(c-m) for c,m in zip(contract, measured))
    assert error < .06, (name, error)
    anchors[name] = dict(rect=old['rect'], measured=measured, contract=contract,
                         max_error_px=error, method=old['method'])
result = dict(status='pass', pass_name='sky_depth_v13', source=SOURCE.relative_to(ROOT).as_posix(),
              source_sha256=sha(SOURCE), baseline_receipt=BASELINE.relative_to(ROOT).as_posix(),
              baseline_receipt_sha256=sha(BASELINE), size=[1536,1024], rgba=True,
              alpha_zero_pixels=int((pixels[:,:,3]==0).sum()), exact_source_preservation=True,
              features=anchors, title_center_px=values['TITLE_CENTER_PX'],
              note='Accepted v12 source bytes and cinematic features retained. The v13 native material/visibility bake is proved separately.')
(REVIEW/'art_measurements.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print('DEPTH ART PRESERVED: source bytes identical; FX core error < .06px')
