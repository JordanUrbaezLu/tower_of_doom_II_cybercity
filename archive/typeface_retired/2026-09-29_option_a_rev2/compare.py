"""compare.py - set real game lines in the OLD and NEW glyph sheets at on-screen sizes.

  python compare.py OLD_DIR NEW_DIR OUT.png [--caps 12,16,22]
A dir holds i_tod_hud_letters.png + i_tod_hud_digits.png. Lines are composed like TodGlyphRow: each
glyph cropped to its ink columns, scaled so the letters' cap = the target, numerals scaled to the
letters' cap (a mixed line), baselines aligned, advance = ink width + a small gap.
"""
import sys, os, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

LET = dict(file='i_tod_hud_letters.png', cw=80, ch=112, cols=15, chars=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + ['-', "'", '$', '.'], base=103, cap=89)
DIG = dict(file='i_tod_hud_digits.png', cw=128, ch=160, cols=13, chars=list('0123456789') + ['/', '+', '-'], base=151, cap=137)
LINES = ["YOUR BLASTS HEAL YOU", "MORE PELLETS AT LV3 / 6 / 9", "HOLLOW, QUICK REBOOT, LUCKY CHARM",
         "SUMMONER MASTER  EXPLOSIVE FUSION", "LEGENDARY +4   EPIC +3   RARE +2", "5S 5S S5  8B B8  0O O0  1I",
         "ABCDEFGHIJKLM NOPQRSTUVWXYZ", "0123456789  32 / 240  +3"]


def load(d):
    out = {}
    for S in (LET, DIG):
        im = np.array(Image.open(os.path.join(d, S['file'])).convert('RGBA'))
        for i, ch in enumerate(S['chars']):
            c, r = i % S['cols'], i // S['cols']
            cell = im[r * S['ch']:(r + 1) * S['ch'], c * S['cw']:(c + 1) * S['cw']]
            a = cell[..., 3] > 24
            if not a.any():
                continue
            xs = np.nonzero(a.any(axis=0))[0]
            out[(S is DIG, ch)] = (cell[:, xs.min():xs.max() + 1], S)
    return out


def pick(ch):
    return ch in '0123456789+/'


def compose(glyphs, text, cap):
    k_l = cap / LET['cap']
    pieces, x = [], 0
    gap = 0.10 * cap
    for ch in text:
        if ch == ' ':
            x += 0.45 * cap
            continue
        if ch == ',':
            ch = '.'
        key = (pick(ch), ch)
        if key not in glyphs:
            key = (not pick(ch), ch)
        if key not in glyphs:
            continue
        cell, S = glyphs[key]
        k = k_l * (LET['cap'] / S['cap']) if S is DIG else k_l
        im = Image.fromarray(cell, 'RGBA')
        w = max(1, int(round(cell.shape[1] * k)))
        h = max(1, int(round(cell.shape[0] * k)))
        im = im.resize((w, h), Image.LANCZOS)
        top = cap * 1.4 - S['base'] * k   # baseline at y = cap * 1.4
        pieces.append((im, x, top))
        x += w + gap
    W = int(x + 4)
    H = int(cap * 1.9)
    canvas = Image.new('RGBA', (max(W, 4), H), (0, 0, 0, 0))
    for im, px, py in pieces:
        canvas.alpha_composite(im, (int(round(px)), int(round(py))))
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('old'); ap.add_argument('new'); ap.add_argument('out')
    ap.add_argument('--caps', default='12,16,24')
    a = ap.parse_args()
    caps = [int(c) for c in a.caps.split(',')]
    G = {'OLD': load(a.old), 'NEW': load(a.new)}
    rows = []
    for cap in caps:
        for line in LINES:
            rows.append((cap, line))
    rendered = []
    for cap, line in rows:
        pair = [compose(G[k], line, cap) for k in ('OLD', 'NEW')]
        rendered.append((cap, line, pair))
    colw = max(max(p[0].width, p[1].width) for _, _, p in rendered) + 30
    H = sum(max(p[0].height, p[1].height) + 6 for _, _, p in rendered) + 60
    bgs = [(12, 16, 32), (60, 30, 90)]
    sheet = Image.new('RGB', (80 + colw * 2, H), (8, 10, 20))
    d = ImageDraw.Draw(sheet)
    d.text((90, 10), 'OLD (shipped)', fill=(200, 200, 200))
    d.text((90 + colw, 10), 'NEW', fill=(200, 255, 200))
    y = 40
    for i, (cap, line, pair) in enumerate(rendered):
        h = max(pair[0].height, pair[1].height) + 6
        bg = bgs[(i // len(LINES)) % 2]
        for j, im in enumerate(pair):
            x0 = 80 + j * colw
            d.rectangle([x0, y, x0 + colw - 10, y + h - 2], fill=bg)
            sheet.paste(im, (x0 + 6, y + 2), im)
        d.text((4, y + h / 3), 'cap %d' % cap, fill=(140, 140, 140))
        y += h
    sheet.save(a.out)
    print('wrote', a.out, sheet.size)


if __name__ == '__main__':
    main()
