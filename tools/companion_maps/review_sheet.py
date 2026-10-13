"""companion_maps/review_sheet.py - the OLD vs NEW review sheet of the four in-world companions (W2A, 2026-10-05).

RUN  python tools/companion_maps/review_sheet.py --renders DIR --out art/generated/W2A-companion-models/_review.png
DIR holds render_review.py's output (<OLD|NEW>_<companion>_<34|close>.png, all one camera / light / exposure per
companion). One row per companion: OLD and NEW three-quarter views, OLD and NEW close studies, then both again at PLAY
DISTANCE (a companion a few metres away is ~150-200 px tall on a 1080p screen). Labels in the map's typeface.
Also writes <out stem>_crops.png: 1:1 crops of the close studies, where the maps' detail lives, and with --bright DIR
(a render_review pass at a higher --exposure) <out stem>_bright.png: the two dark drones' surfaces made readable.
"""
from pathlib import Path
import argparse, sys
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools' / 'artgen'))
import artgen  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--renders', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
ap.add_argument('--bright', type=Path, default=None, help='a second render_review output at a higher --exposure')
A = ap.parse_args()

ROWS = [('protector', 'CIVIL PROTECTOR', 'GOLD FINISH - NO MORE FLAT BLUE SWATCH'),
        ('talon', 'TALON', 'WING GUN MAPS AUTHORED'),
        ('raps', 'R.A.P.S.', 'RUST SPOT SHELL RESTORED'),
        ('cerberus', 'CERBERUS', '34 MISSING MAPS AUTHORED')]
T, P, PAD, HEAD, LAB = 440, 176, 12, 96, 34
BG = (22, 24, 30, 255)
GOLD, CYAN, GREY = (255, 214, 120), (120, 230, 255), (170, 176, 190)


def tile(label, comp, view, size):
    p = A.renders / ('%s_%s_%s.png' % (label, comp, view))
    im = Image.open(p).convert('RGBA')
    return im.resize((size, size), Image.LANCZOS)


def main():
    cols = [('OLD', '34', T), ('NEW', '34', T), ('OLD', 'close', T), ('NEW', 'close', T)]
    w = PAD + sum(c[2] + PAD for c in cols) + P + PAD
    row_h = LAB + T + PAD
    h = HEAD + len(ROWS) * row_h + PAD
    w += (4 - w % 4) % 4
    h += (4 - h % 4) % 4
    sheet = Image.new('RGBA', (w, h), BG)
    artgen.typeset(sheet, 'COMPANIONS IN THE WORLD - OLD VS NEW', 30, 44, rgb=GOLD, x=PAD)
    artgen.typeset(sheet, 'MATCHED CAMERA LIGHT AND EXPOSURE - APPROXIMATE SHADING - NOT THE ENGINE', 15, 76, rgb=GREY,
                   x=PAD)
    for r, (comp, name, note) in enumerate(ROWS):
        y = HEAD + r * row_h
        artgen.typeset(sheet, name, 20, y + 24, rgb=GOLD, x=PAD)
        artgen.typeset(sheet, note, 13, y + 24, rgb=CYAN, x=PAD + artgen.text_width(name, 20) + 18)
        x = PAD
        for label, view, size in cols:
            sheet.paste(tile(label, comp, view, size), (x, y + LAB))
            artgen.typeset(sheet, label + (' CLOSE' if view == 'close' else ''), 13, y + LAB + 20,
                           rgb=(GREY if label == 'OLD' else CYAN), x=x + 8)
            x += size + PAD
        for i, label in enumerate(('OLD', 'NEW')):
            yy = y + LAB + i * (P + 34)
            sheet.paste(tile(label, comp, '34', P), (x, yy))
            artgen.typeset(sheet, label + ' PLAY DISTANCE', 10, yy + 14, rgb=(GREY if label == 'OLD' else CYAN), x=x + 6)
    A.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert('RGB').save(A.out, optimize=True)
    # 1:1 crops of the close studies (the centre half), OLD over NEW per companion
    C = 360
    crops = Image.new('RGBA', (PAD + len(ROWS) * (C + PAD), HEAD + 2 * (C + LAB) + PAD), BG)
    artgen.typeset(crops, 'CLOSE STUDIES AT FULL SIZE - OLD TOP - NEW BOTTOM', 24, 40, rgb=GOLD, x=PAD)
    for i, (comp, name, note) in enumerate(ROWS):
        x = PAD + i * (C + PAD)
        for j, label in enumerate(('OLD', 'NEW')):
            im = Image.open(A.renders / ('%s_%s_close.png' % (label, comp))).convert('RGBA')
            cx, cy = im.width // 2, im.height // 2
            crop = im.crop((cx - C // 2, cy - C // 2, cx + C // 2, cy + C // 2))
            y = HEAD + j * (C + LAB)
            artgen.typeset(crops, name + ' ' + label, 13, y + 22, rgb=(GREY if label == 'OLD' else CYAN), x=x)
            crops.paste(crop, (x, y + LAB - 4))
    crops.convert('RGB').save(A.out.with_name(A.out.stem + '_crops.png'), optimize=True)
    print('review_sheet: wrote', A.out, 'and', A.out.with_name(A.out.stem + '_crops.png'))
    if A.bright:
        # the two DARK drones again at +2.4 stops (same for both trees): their surfaces, not their paint colour
        comps = [r for r in ROWS if (A.bright / ('OLD_%s_34.png' % r[0])).exists()]
        b = Image.new('RGBA', (PAD + 4 * (T + PAD), HEAD + len(comps) * (LAB + T + PAD)), BG)
        artgen.typeset(b, 'THE DARK DRONES AT +2.4 STOPS - SURFACE DETAIL - SAME EXPOSURE BOTH SIDES', 24, 44, rgb=GOLD, x=PAD)
        for r, (comp, name, note) in enumerate(comps):
            y = HEAD + r * (LAB + T + PAD)
            artgen.typeset(b, name, 20, y + 24, rgb=GOLD, x=PAD)
            for c, (label, view) in enumerate([('OLD', '34'), ('NEW', '34'), ('OLD', 'close'), ('NEW', 'close')]):
                x = PAD + c * (T + PAD)
                im = Image.open(A.bright / ('%s_%s_%s.png' % (label, comp, view))).convert('RGBA').resize((T, T), Image.LANCZOS)
                b.paste(im, (x, y + LAB))
                artgen.typeset(b, label + (' CLOSE' if view == 'close' else ''), 13, y + LAB + 20,
                               rgb=(GREY if label == 'OLD' else CYAN), x=x + 8)
        b.convert('RGB').save(A.out.with_name(A.out.stem + '_bright.png'), optimize=True)
        print('review_sheet: wrote', A.out.with_name(A.out.stem + '_bright.png'))


if __name__ == '__main__':
    main()
