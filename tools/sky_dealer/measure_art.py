"""Read-only registration/brightness audit of the Imagegen dealer-crest edit.

This measures existing images; it never edits, crops or writes image pixels.
Imagegen changed texture pixels outside the crest: exact pixel preservation is
not claimed. Spatial registration, text brightness and measured FX anchors are.
"""
import ast
import json
import numpy as np
from PIL import Image
from scipy.ndimage import sobel
from pass_config import ROOT, REVIEW, sha

paths = [ROOT/'art/sky3d/sign/v10_cyber_hero.png', ROOT/'art/sky3d/sign/v12_dealer.png']
arrays = [np.asarray(Image.open(p), dtype=float) for p in paths]
assert all(a.shape == (1024, 1536, 4) for a in arrays)
a, b = arrays
ga, gb = (z[:,:,:3].mean(2) for z in arrays)
ea, eb = (np.hypot(sobel(z, 0), sobel(z, 1)) for z in (ga,gb))
regions = {}
for name, box in {'title':(350,297,1187,522), 'subtitle':(438,529,1094,581),
                  'left_frame':(50,280,310,770), 'right_frame':(1220,280,1490,770)}.items():
    x0,y0,x1,y1 = box
    aa = ea[y0:y1,x0:x1].ravel()
    candidates = []
    for dy in range(-5,6):
        for dx in range(-5,6):
            bb = eb[y0+dy:y1+dy,x0+dx:x1+dx].ravel()
            candidates.append((float(np.corrcoef(aa,bb)[0,1]), dx, dy))
    correlation, dx, dy = max(candidates)
    ratio = float(gb[y0:y1,x0:x1].mean()/ga[y0:y1,x0:x1].mean())
    assert (dx,dy) == (0,0), (name, dx, dy)
    assert correlation > .80 and .95 < ratio < 1.05, (name,correlation,ratio)
    regions[name] = dict(rect=list(box), best_shift_px=[dx,dy], edge_correlation=correlation,
                         mean_source_brightness_ratio=ratio)
values = {}
for node in ast.parse((ROOT/'tools/sky3d/cyber_hero_title.py').read_text(encoding='utf-8')).body:
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id in {'FEATURE_PIXELS','TITLE_CENTER_PX'}:
                values[target.id] = ast.literal_eval(node.value)
anchors = {}
for name, box in {'ring':(756,113,780,143),'eye_l':(718,184,759,220),'eye_r':(774,184,815,220)}.items():
    x0,y0,x1,y1 = box
    z = b[y0:y1,x0:x1,:3]
    yy,xx = np.indices(z.shape[:2])
    weights = np.maximum(0,z.min(2)-150)
    measured = [float((xx*weights).sum()/weights.sum()+x0), float((yy*weights).sum()/weights.sum()+y0)]
    contract = [c+d for c,d in zip(values['TITLE_CENTER_PX'],values['FEATURE_PIXELS'][name])]
    error = max(abs(c-m) for c,m in zip(contract,measured))
    assert error < .06, (name,error)
    anchors[name] = dict(rect=list(box), measured=measured,contract=contract,max_error_px=error,
                         method='centroid weighted by max(0,min(R,G,B)-150), bright near-white tube cores')
changed = np.any(a != b,axis=2)
result = dict(status='pass',before=str(paths[0].relative_to(ROOT)),after=str(paths[1].relative_to(ROOT)),
              hashes=[sha(p) for p in paths], size=[1536,1024],rgba=True,
              alpha_zero_pixels=[int((z[:,:,3]==0).sum()) for z in arrays],
              changed_pixels=int(changed.sum()),exact_pixel_preservation=False,
              registration=regions,features=anchors,title_center_px=values['TITLE_CENTER_PX'],
              note='Original painting retained as historical source. New Imagegen edit keeps measured placement and brightness; texture pixels differ.')
(REVIEW/'art_measurements.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('DEALER ART REGISTERED: text/frame shift 0px; FX core error < .06px')
