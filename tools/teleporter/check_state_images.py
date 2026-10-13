"""Prove hue replacement retains the glow mask and dark glass edits no metal."""
from PIL import Image, ImageChops
import hashlib, json
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'art/teleporter'
IMG = ROOT / 'model_export/tod_teleporter/_images'
def rgb(path):
    return Image.open(path).convert('RGB')
def peak(im):
    r, g, b = im.split()
    return ImageChops.lighter(r, ImageChops.lighter(g, b))
old_e = peak(rgb(IMG / 'i_tod_teleporter_e.png'))
ready = rgb(IMG / 'i_tod_teleporter_ready_e.png')
new_e = peak(ready)
assert ImageChops.difference(old_e, new_e).getbbox() is None
pixels = np.asarray(ready)
lit = pixels.max(axis=2) >= 16
assert lit.any() and np.all(pixels[:,:,1][lit] > pixels[:,:,0][lit])
assert np.all(pixels[:,:,1][lit] > pixels[:,:,2][lit]), 'Ready strips must be green, never pink'
assert np.all(pixels[:,:,0] <= pixels[:,:,1]) and np.all(pixels[:,:,2] <= pixels[:,:,1])
old_c = rgb(ART / 'checkpoints/i_tod_teleporter_original_c.png')
new_c = rgb(IMG / 'i_tod_teleporter_c.png')
diff = peak(ImageChops.difference(old_c, new_c))
non_glass = old_e.point(lambda x: 255 if x == 0 else 0)
assert ImageChops.multiply(diff, non_glass).getbbox() is None
assert diff.getbbox() is not None
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
result = {
    'pixels_checked': old_e.width * old_e.height,
    'emission_peak_and_zero_mask_identical': True,
    'ready_hue': 'green',
    'nonzero_emission_pixels': int(np.count_nonzero(pixels.max(axis=2))),
    'non_glowing_diffuse_pixels_identical': True,
    'changed_glass_pixels': old_e.width * old_e.height - diff.histogram()[0],
    'ready_emission_sha256': sha(IMG / 'i_tod_teleporter_ready_e.png'),
    'state_diffuse_sha256': sha(IMG / 'i_tod_teleporter_c.png'),
    'native_visual_verified': False,
}
(ART / 'engine_kit/state_image_validation.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
