"""Render the Black Market Spin screen from the INSTALLED art, placed exactly where
TodSpinReel.lua puts it (the same layout numbers), at the moment a spin lands.

A layout proof, not a native render: flat alpha compositing, the map TTF for the
game-written text, and the game's own setRGB tints. Run after any art or layout
change:  python tools/partner_shop/render_spin_screen.py [out.png]
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMG = os.path.join(ROOT, 'source_data', 'tod_ui_images', '_images')
FONT = os.path.join(ROOT, 'fonts', 'tod_tower1.ttf')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs', '190_ref', 'installed_screen_1280x720.png')

S = 2   # render at 2x the 1280x720 canvas for legibility
RAR = [(233, 238, 245), (58, 168, 255), (181, 92, 255), (255, 194, 61)]
L = dict(PANEL=(100, 112, 1180, 548), REEL=(140, 160, 1140, 272), LUCK=(960, 118, 1160, 146),
         NEEDLE=(628, 146, 652, 286), TILE_W=140, TILE_H=104, PITCH=150, T_ICON=(44, 8, 96, 60),
         T_NAME=(6, 64, 134, 80), BANNER=(440, 286, 840, 338), NAME=(342, 370), FX=(374, 392),
         STATUS=(396, 414), BOX_W=200, BOX_H=72, BOX_GAP=16, BOX_Y0=432, S_ICON=(10, 14, 58, 62),
         S_LABEL=(64, 6, 194, 20), S_NAME=(64, 24, 194, 44), S_RAR=(64, 48, 194, 64))
BOX_X0 = 640 - (4 * L['BOX_W'] + 3 * L['BOX_GAP']) // 2


def load(n):
    return Image.open(os.path.join(IMG, n + '.png')).convert('RGBA')


def tint(im, rgb):
    r, g, b, a = im.split()
    r = r.point(lambda v: v * rgb[0] // 255); g = g.point(lambda v: v * rgb[1] // 255); b = b.point(lambda v: v * rgb[2] // 255)
    return Image.merge('RGBA', (r, g, b, a))


def put(canvas, im, box, rgb=None, alpha=1.0):
    x0, y0, x1, y1 = [int(v * S) for v in box]
    im = im.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    if rgb: im = tint(im, rgb)
    if alpha < 1:
        a = im.getchannel('A').point(lambda v: int(v * alpha)); im.putalpha(a)
    canvas.alpha_composite(im, (x0, y0))


def text(d, box, s, rgb, align='center', frac=0.8):
    x0, y0, x1, y1 = [v * S for v in box]
    f = ImageFont.truetype(FONT, max(8, int((y1 - y0) * frac)))
    w = d.textlength(s, font=f)
    while w > (x1 - x0) and f.size > 8:
        f = ImageFont.truetype(FONT, f.size - 1); w = d.textlength(s, font=f)
    x = {'center': (x0 + x1 - w) / 2, 'left': x0, 'right': x1 - w}[align]
    d.text((x, y0 + (y1 - y0 - f.size) / 2), s, fill=rgb, font=f)


def main():
    c = Image.new('RGBA', (1280 * S, 720 * S), (10, 8, 18, 255))
    d = ImageDraw.Draw(c)
    for i in range(0, 1280, 90):   # a dark world behind
        d.rectangle([(i + 10) * S, (300 + (i * 37) % 200) * S, (i + 60) * S, 720 * S], fill=(16, 12, 30), outline=(70, 36, 110))
    rx0, ry0, rx1, ry1 = L['REEL']
    d.rectangle([rx0 * S, ry0 * S, rx1 * S, ry1 * S], fill=(5, 4, 9))
    names = ['OVERCLOCK', 'ARC CHAIN', 'SALVAGE', 'PLATING', 'NANO REPAIR', 'LONG SIGHT', 'LUCKY CHARM']
    icons = ['overclock', 'arc', 'salvage', 'plating', 'nano', 'sight', 'lucky']
    rars = [0, 1, 0, 2, 3, 0, 1]
    tiles = ['common', 'rare', 'epic', 'legendary']
    strip = Image.new('RGBA', c.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(strip)
    x0 = 640 - L['TILE_W'] // 2 - 3 * L['PITCH']
    for k in range(7):
        tx = x0 + k * L['PITCH']; ty = ry0 + 4
        put(strip, load('i_tod_spin_tile_' + tiles[rars[k]]), (tx, ty, tx + L['TILE_W'], ty + L['TILE_H']))
        ic = L['T_ICON']
        put(strip, load('i_tod_spin_ico_' + icons[k]), (tx + ic[0], ty + ic[1], tx + ic[2], ty + ic[3]), RAR[rars[k]])
        nm = L['T_NAME']
        text(sd, (tx + nm[0], ty + nm[1], tx + nm[2], ty + nm[3]), names[k], (240, 240, 250))
    mask = Image.new('L', c.size, 0); ImageDraw.Draw(mask).rectangle([rx0 * S, ry0 * S, rx1 * S, ry1 * S], fill=255)
    clipped = Image.new('RGBA', c.size, (0, 0, 0, 0)); clipped.paste(strip, (0, 0), mask)
    c.alpha_composite(clipped)
    put(c, load('i_tod_spin_frame'), L['PANEL'])
    put(c, load('i_tod_spin_glass'), L['REEL'])
    put(c, load('i_tod_spin_needle'), L['NEEDLE'])
    text(d, (L['LUCK'][0] + 8, L['LUCK'][1] + 5, L['LUCK'][2] - 8, L['LUCK'][3] - 5), 'LUCK 80', (31, 229, 255))
    put(c, load('i_tod_spin_banner_epic'), L['BANNER'])
    text(d, (340, L['NAME'][0], 940, L['NAME'][1]), 'PLATING', (255, 255, 255))
    text(d, (240, L['FX'][0], 1040, L['FX'][1]), 'HEALTH X1.8', (216, 230, 255))
    text(d, (340, L['STATUS'][0], 940, L['STATUS'][1]), 'SOCKETED IN SLOT 1', (31, 229, 255))
    slots = [('plating', 2, 'PLATING'), ('arc', 1, 'ARC CHAIN'), (None, None, 'EMPTY')]
    for b in range(4):
        bx = BOX_X0 + b * (L['BOX_W'] + L['BOX_GAP']); by = L['BOX_Y0']
        if b == 3:
            put(c, load('i_tod_spin_scrap'), (bx, by, bx + L['BOX_W'], by + L['BOX_H'])); continue
        ico, rar, nm = slots[b]
        put(c, load('i_tod_spin_socket'), (bx, by, bx + L['BOX_W'], by + L['BOX_H']), RAR[rar] if ico else (107, 102, 128))
        if ico:
            si = L['S_ICON']; put(c, load('i_tod_spin_ico_' + ico), (bx + si[0], by + si[1], bx + si[2], by + si[3]), RAR[rar])
        sl, sn, sr = L['S_LABEL'], L['S_NAME'], L['S_RAR']
        text(d, (bx + sl[0], by + sl[1], bx + sl[2], by + sl[3]), 'SLOT %d' % (b + 1), (153, 158, 179), 'left')
        text(d, (bx + sn[0], by + sn[1], bx + sn[2], by + sn[3]), nm, (255, 255, 255) if ico else (140, 143, 158), 'left')
        if ico:
            text(d, (bx + sr[0], by + sr[1], bx + sr[2], by + sr[3]), ['COMMON', 'RARE', 'EPIC', 'LEGENDARY'][rar], RAR[rar], 'left')
    put(c, load('i_tod_spin_socket_focus'), (BOX_X0 - 4, L['BOX_Y0'] - 4, BOX_X0 + L['BOX_W'] + 4, L['BOX_Y0'] + L['BOX_H'] + 4))
    for i, (ico, rar) in enumerate([('plating', 2), ('arc', 1), (None, None)]):
        r = 1280 - 42 - (2 - i) * 32; b = 720 - 236
        put(c, load('i_tod_spin_chip'), (r - 28, b - 28, r, b), RAR[rar] if ico else (107, 102, 128), 1.0 if ico else 0.35)
        if ico: put(c, load('i_tod_spin_ico_' + ico), (r - 24, b - 24, r - 4, b - 4), RAR[rar])
    c.convert('RGB').save(OUT)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
