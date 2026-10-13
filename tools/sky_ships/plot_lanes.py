"""Plan view of the generated sky lanes over the map's solid brushes at one altitude (a visual check).
   python tools/sky_ships/plot_lanes.py [ship] [z] [out.png]"""
import json, sys, pathlib
from PIL import Image, ImageDraw
ROOT = pathlib.Path(__file__).resolve().parents[2]
ship = sys.argv[1] if len(sys.argv) > 1 else 'dreadnought'
z = float(sys.argv[2]) if len(sys.argv) > 2 else 21000
out = sys.argv[3] if len(sys.argv) > 3 else str(ROOT / 'art/sky_ships' / ('lanes_%s_z%d.png' % (ship, z)))
lanes = json.load(open(ROOT / 'art/sky_ships/lanes.json'))
man = {r['ship']: r for r in json.load(open(ROOT / 'art/sky_ships/manifest.json'))['ships']}
aabbs = json.load(open(ROOT / 'tmp/sky_ships/obstacles.json'))   # written by gen_lanes.js
S, W = 0.03, 24064
img = Image.new('RGB', (int(W * S), int(W * S)), (12, 10, 22))
d = ImageDraw.Draw(img)
P = lambda x, y: ((x + 12032) * S, (12032 - y) * S)
r = man[ship]
zlo, zhi = z + r['bounds'][0][2], z + r['bounds'][1][2]
for lo, hi in aabbs:
    near = hi[2] >= zlo - 1500 and lo[2] <= zhi + 1500
    d.rectangle([P(lo[0], hi[1]), P(hi[0], lo[1])], fill=(200, 60, 60) if near else (60, 55, 80))
for k in lanes['keep_out']:
    d.rectangle([P(k['lo'][0], k['hi'][1]), P(k['hi'][0], k['lo'][1])], outline=(255, 200, 0))
n = 0
for l in lanes['lanes']:
    p = l['per'].get(ship)
    if p and any(lo <= z <= hi for lo, hi in p['bands']):
        d.line([P(*p['a']), P(*p['b'])], fill=(60, 220, 255), width=1); n += 1
d.text((6, 6), '%s lanes valid at origin z=%d: %d  (red = geometry within reach of that altitude)' % (ship, z, n), fill=(255, 255, 255))
img.save(out)
print('PLOT', out, n)
