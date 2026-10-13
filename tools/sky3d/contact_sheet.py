"""
tools/sky3d/contact_sheet.py — stitch the sky previews into two review images (docs/166)

  blender -b --factory-startup -P tools/sky3d/contact_sheet.py -- [--dir docs/sky_preview] [--tag sky3d] [--old evil]
      [--views moon,city,skyline_r,harbour,down_r,nadir] [--cols 3]

Writes <dir>/<tag>_contact.png (a grid of the in-game views, each tile 640x360) and
<dir>/<tag>_before_after.png (the OLD drawn sky's moon view beside the NEW one, 1920x1080).
"""
import bpy, os, sys
import numpy as np

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(k, d):
    return ARGS[ARGS.index(k) + 1] if k in ARGS and ARGS.index(k) + 1 < len(ARGS) else d


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
D = arg('--dir', os.path.join(REPO, 'docs', 'sky_preview'))
TAG = arg('--tag', 'sky3d')
OLD = arg('--old', 'evil')


def load(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    a = np.empty(w * h * im.channels, np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(h, w, im.channels)[::-1, :, :3]
    bpy.data.images.remove(im)
    return a


def shrink(a, k):
    h, w = a.shape[:2]
    return a[: (h // k) * k, : (w // k) * k].reshape(h // k, k, w // k, k, 3).mean((1, 3))


def save(path, a):
    h, w = a.shape[:2]
    im = bpy.data.images.new('sheet', w, h, alpha=False)
    px = np.empty((h, w, 4), np.float32)
    px[..., :3] = a[::-1]
    px[..., 3] = 1.0
    im.pixels.foreach_set(px.ravel())
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)
    print('wrote', path)


views = arg('--views', 'moon,city,skyline_r,harbour,down_r,nadir').split(',')
cols = int(arg('--cols', '3'))
rows = (len(views) + cols - 1) // cols
tiles = [shrink(load(os.path.join(D, f'{TAG}_ingame_{v}.png')), 3) for v in views]
th, tw = tiles[0].shape[:2]
sheet = np.zeros((th * rows, tw * cols, 3), np.float32)
for i, t in enumerate(tiles):
    r, c = divmod(i, cols)
    sheet[r * th:(r + 1) * th, c * tw:(c + 1) * tw] = t[:th, :tw]
save(os.path.join(D, f'{TAG}_contact.png'), sheet)

old = os.path.join(D, f'{OLD}_ingame_moon.png')
if os.path.exists(old):
    a, b = shrink(load(old), 2), shrink(load(os.path.join(D, f'{TAG}_ingame_moon.png')), 2)
    h = min(a.shape[0], b.shape[0])
    ba = np.concatenate([a[:h], np.zeros((h, 8, 3), np.float32), b[:h]], axis=1)
    save(os.path.join(D, f'{TAG}_before_after.png'), ba)
