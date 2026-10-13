"""Step 08 (plain Python + PIL): the review contact sheet and matched before/after pairs (art/wunderstrahl/review/).

  contact_sheet.png          every after-render on one page, labelled
  before_after_<view>.png    the untouched DG-2 (left) and the Wunderstrahl (right) from the same camera and studio
  review.json                every review image with its sha256 and what it shows
Review images are documentation, not shipped art (approximate previews; the native look is the user's playtest).
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

R = common.REVIEW
SHEET = [  # (file, label)
    ('wunderstrahl_first_person.png', 'First person - idle pose (review viewhands)'),
    ('wunderstrahl_ads.png', 'Aiming down the sights (real ADS clip, ~65 deg FOV)'),
    ('wunderstrahl_quarter_left.png', '3/4 front left'),
    ('wunderstrahl_quarter_right.png', '3/4 front right'),
    ('wunderstrahl_lens_close.png', 'Emitter close-up: open focusing ring, cut crystal, lips'),
    ('wunderstrahl_lens_front.png', 'Emitter from the front'),
    ('wunderstrahl_profile_left.png', 'Profile (left side)'),
    ('wunderstrahl_top.png', 'Top'),
    ('wunderstrahl_world.png', 'World model (LOD0) at play distance'),
    ('wunderstrahl_world_lods.png', 'World LOD0..LOD6'),
    ('wunderstrahl_pickup.png', 'Gold drop (stand-in for stock mtl_x2icon_gold)'),
    ('wunderstrahl_pickup_lineup.png', 'Drop line-up: Zombie Blood | Wunderstrahl | stock Death Machine drop'),
    ('wunderstrahl_quarter_left_nobloom.png', 'No-bloom check (3/4 left)'),
    ('wunderstrahl_lens_close_nobloom.png', 'No-bloom check (emitter)'),
    ('wunderstrahl_first_person_nobloom.png', 'No-bloom check (first person)'),
]
PAIRS = ['first_person', 'quarter_left', 'quarter_right', 'profile_left', 'top', 'lens_close', 'lens_front']


def font(size):
    for name in ('arial.ttf', 'segoeui.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def label(im, text, size=26):
    d = ImageDraw.Draw(im)
    f = font(size)
    d.rectangle([0, 0, im.width, size + 16], fill=(12, 12, 13))
    d.text((12, 6), text, fill=(236, 232, 224), font=f)
    return im


def fit(im, w, h):
    im = im.convert('RGB'); s = min(w / im.width, h / im.height)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    out = Image.new('RGB', (w, h), (18, 18, 19)); out.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return out


cells = []
for f, text in SHEET:
    p = R / f
    if p.exists():
        cells.append(label(fit(Image.open(p), 800, 500), text, 22))
cols = 3; rows = (len(cells) + cols - 1) // cols
sheet = Image.new('RGB', (cols * 800 + (cols + 1) * 10, rows * 500 + (rows + 1) * 10 + 70), (8, 8, 9))
ImageDraw.Draw(sheet).text((14, 18), 'THE WUNDERSTRAHL - model review (exported binaries + shipped maps; approximate preview, '
                           'native look pending the build and the user\'s playtest)', fill=(255, 214, 64), font=font(30))
for i, c in enumerate(cells):
    sheet.paste(c, (10 + (i % cols) * 810, 80 + (i // cols) * 510))
sheet.save(R / 'contact_sheet.png')
for v in PAIRS:
    a, b = R / ('before_%s.png' % v), R / ('wunderstrahl_%s.png' % v)
    if a.exists() and b.exists():
        A = label(fit(Image.open(a), 1200, 750), 'DG-2 (untouched source)'); B = label(fit(Image.open(b), 1200, 750), 'Wunderstrahl')
        pair = Image.new('RGB', (2410, 750), (8, 8, 9)); pair.paste(A, (0, 0)); pair.paste(B, (1210, 0))
        pair.save(R / ('before_after_%s.png' % v))
rows = {p.name: dict(sha256=common.sha(p), bytes=p.stat().st_size) for p in sorted(R.glob('*.png'))}
common.write_json(R / 'review.json', dict(images=rows, note='Approximate Blender previews (diffuse + Fresnel GGX, Khronos PBR Neutral view '
                  'transform). Not BO3 lighting, probes, tone mapping, exposure or bloom. Gun-alone views are posed by '
                  'idle frame 0 with tag_weapon held and leave out the parked reload bracket.', native_playtested=False))
print('WS_08_SHEET', len(cells), 'cells,', len(PAIRS), 'pairs,', len(rows), 'review images')
