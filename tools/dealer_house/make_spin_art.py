"""THE CURSED ROLL's reel art (docs/207), GENERATED from the shipped Black Market spin art - never paint these by hand.

  python -B tools/dealer_house/make_spin_art.py           write the three PNGs into source_data/tod_ui_images/_images/
  python -B tools/dealer_house/make_spin_art.py --check   FAIL (exit 1) on any byte of difference, or if a GDT block,
                                                          a zone image line or TodSpinReel.lua's registration is missing
  python -B tools/dealer_house/make_spin_art.py --review  also write art/dealer_house/review/spin_cursed.png (the three side by side)
  python -B tools/dealer_house/make_spin_art.py --out DIR write the three PNGs under DIR/source_data/tod_ui_images/_images/
                                                          instead (staging; nothing in the repo is touched)

THE THREE IMAGES (TodSpinReel.lua ART.cursed, LOCKSTEP):
  i_tod_spin_tile_cursed    560 x 416  the LEGENDARY tile's frame turned blood red, its rarity band REBUILT: the whole
                                       label band between the two corner scrolls is cleared row by row (each row back to
                                       its own field colour, read beside the scrolls) BEFORE anything is drawn, so no
                                       stroke of LEGENDARY survives; then CURSED is set there in the map's typeface
                                       (the glyph-sheet cells TodGlyphRow draws), tracked wide like the word it replaces,
                                       filled with a hot-red neon gradient, with a red glow behind it
  i_tod_spin_banner_cursed  1600 x 208 the LEGENDARY stamp's frame, scrolls of light and sparks turned blood red; its
                                       INTERIOR rebuilt: every column between the two side diamonds is cleared to the
                                       field (colour AND alpha - the shipped plate is alpha 243 and its letters 255, so
                                       copying the old alpha carried a ghost LEGENDARY), then CURSED in the map typeface
                                       with the stamp's neon treatment: dark outline, hot gradient fill, a wide red glow
  i_tod_spin_ico_cursed     208 x 208  the Dealer's own face as the spin portraits draw it (i_tod_spin_dealer_*): the
                                       rounded black hood with its red rim light, the dark opening, the shield-shaped
                                       charcoal mask with its pale centre ridge, two red neon X eyes and the wide uneven
                                       stitched grin, glowing (docs/dealer_identity.md); vector, drawn 4x, downsampled

Every output is RGBA 8-bit, the sizes the reel's slot maps expect (tools/partner_shop/gen_spin_art_refs.py). The
GDT blocks are compressed high color, sRGB3chAlpha, noMipMaps + noPicMip like every spin image; all three sizes are
multiples of 4 (the BC7 rule). Deterministic: no randomness, no clock.

Rebuilt 2026-10-04 (tmp/asset_prod/packs/PK15-house-cursed-reel.json; tmp/redesign/R2-card-subjects/LAND.md): the first
cut pasted a dark box over the tile's LEGENDARY (its L and Y showed at both ends), kept the legendary banner's alpha
(its letters stayed as darker ghosts round CURSED) and drew a placeholder mask.
"""
import io, os, re, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _root():
    """the repo root: two levels up, or (a staged copy) the nearest parent that holds the glyph metrics + spin art"""
    r = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    p = r
    while not (os.path.isfile(os.path.join(p, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodGlyphMetrics.lua'))
               and os.path.isfile(os.path.join(p, 'source_data', 'tod_ui_images', '_images', 'i_tod_spin_tile_legendary.png'))):
        up = os.path.dirname(p)
        if up == p:
            return r
        p = up
    return p


ROOT = _root()
IMG = os.path.join(ROOT, 'source_data', 'tod_ui_images', '_images')
METRICS = os.path.join(ROOT, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodGlyphMetrics.lua')
REVIEW = os.path.join(ROOT, 'art', 'dealer_house', 'review', 'spin_cursed.png')
SS = 4
TOD_SPACE_ADV, TOD_TRACK = 0.30, 0.055   # TodGlyphRow.set's space advance and tracking (fractions of the cell / cap)

OUTPUTS = {
    'i_tod_spin_tile_cursed': (560, 416),
    'i_tod_spin_banner_cursed': (1600, 208),
    'i_tod_spin_ico_cursed': (208, 208),
}
RED = (205, 22, 34)          # the curse's red (the Dealer's grin)
RED_HOT = (255, 72, 70)
BONE = (226, 214, 200)
NEON_TOP, NEON_MID, NEON_BOT = (255, 196, 186), (255, 74, 74), (196, 16, 30)   # the letters' fill, top to bottom
GLOW = (255, 34, 44)

# the tile's rarity band (560 x 416): rows 323..393, from under the name band down THROUGH the frame's inner line
# (the old letters' outline and extrusion sit on that line at rows 389..393); the corner scrolls stand at x 28..66 and
# 490..528, so the band is cleared on x 68..490 and each row's field is read on 68..76 and 482..490 (the band field,
# and the line, are flat across a row - the field only gets lighter downward)
TILE_BAND = (68, 323, 491, 394)
TILE_FIELD_L, TILE_FIELD_R = (68, 77), (482, 491)
# the banner's interior (1600 x 208): rows 29..179 inside the inner border, cleared on x 182..1417 - the old word AND
# the two side diamonds (redrawn after); the field is rebuilt from the stamp's own numbers (FIELD_* below), carrying
# the edge flares' glow in from the columns just outside the box so there is no seam
BAN_CLEAR = (182, 29, 1418, 180)
BAN_FIELD = (71, 55, 23)       # the legendary field between its letters (x 700, rows 78..134): flat dark gold
BAN_FIELD_A = 244              # its alpha (the shipped plate is 243..246; its letters were 255 - the ghost)
BAN_DIAMONDS = ((199, 104), (1401, 104))


# ---------------------------------------------------------------------------- the glyph sheets (make_badge.py's reader)
def metrics():
    """The letters set of the GENERATED metrics (tools/battle_arena/make_badge.py's reader): cw / ch / baseline / cap
    and g[c] = (adv, x)."""
    t = open(METRICS, encoding='utf-8').read()
    m = re.search(r'letters = \{\s*cw = (\d+), ch = (\d+), baseline = (\d+), cap = (\d+),\s*g = \{(.*?)\n\t\t\},', t, re.S)
    if not m:
        raise SystemExit('make_spin_art: TodGlyphMetrics.lua: no letters set')
    cw, ch, base, cap = (int(v) for v in m.group(1, 2, 3, 4))
    g = {}
    for c, adv, x in re.findall(r'\["(.)"\] = \{ adv = (\d+), x = (\d+)', m.group(5)):
        g[c] = (int(adv), int(x))
    return dict(cw=cw, ch=ch, baseline=base, cap=cap, g=g)


def cell(c):
    return Image.open(os.path.join(IMG, 'i_tod_hud_l%s.png' % c.lower())).convert('RGBA')


def typeset(layer, M, text, cap, cx, baseline, rgb, track=TOD_TRACK):
    """TodGlyphRow.set's walk (measure, then place each cell so its ink starts at the pen and the set's baseline
    lands on `baseline`), centred on cx, drawn SS times larger onto `layer` (tools/battle_arena/make_badge.py).
    `track` is the gap between letters as a fraction of the cap (TodGlyphRow's own 0.055 unless widened)."""
    s = cap / M['cap']
    total, first = 0.0, True
    for c in text:
        if c == ' ':
            total += M['cw'] * s * TOD_SPACE_ADV
        else:
            if c.lower() not in M['g']:
                raise SystemExit('make_spin_art: no glyph for %r' % c)
            if not first:
                total += cap * track
            total += M['g'][c.lower()][0] * s
        first = False
    pen, first = cx - total / 2, True
    for c in text:
        if c == ' ':
            pen += M['cw'] * s * TOD_SPACE_ADV
            first = False
            continue
        adv, gx = M['g'][c.lower()]
        if not first:
            pen += cap * track
        left, top = pen - gx * s, baseline - M['baseline'] * s
        w, h = M['cw'] * s * SS, M['ch'] * s * SS
        im = cell(c).resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
        r, g, b, a = im.split()
        r = r.point(lambda v: v * rgb[0] // 255)
        g = g.point(lambda v: v * rgb[1] // 255)
        b = b.point(lambda v: v * rgb[2] // 255)
        layer.alpha_composite(Image.merge('RGBA', (r, g, b, a)), (int(round(left * SS)), int(round(top * SS))))
        pen += adv * s
        first = False
    return total


def neon_word(size, M, text, cap, cx, baseline, track, glow_r, glow_a):
    """CURSED as the stamps set their word: the cells' own dark outline and bevel, the white fill multiplied by a
    hot-red neon gradient over the cap (light at the top, deep at the foot), and a red glow under it."""
    w, h = size
    layer = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    typeset(layer, M, text, cap, cx, baseline, (255, 255, 255), track)
    word = layer.resize((w, h), Image.LANCZOS)
    a = np.asarray(word).astype(np.float64)
    top, bot = baseline - cap, baseline
    y = np.clip((np.arange(h)[:, None] - top) / max(bot - top, 1.0), 0, 1)
    t1 = np.clip(y / 0.45, 0, 1)[..., None]
    t2 = np.clip((y - 0.45) / 0.55, 0, 1)[..., None]
    grad = (np.array(NEON_TOP) * (1 - t1) + np.array(NEON_MID) * t1) * (y[..., None] < 0.45) + \
           (np.array(NEON_MID) * (1 - t2) + np.array(NEON_BOT) * t2) * (y[..., None] >= 0.45)
    rgb = a[..., :3] * grad / 255.0
    word = Image.fromarray(np.dstack([np.clip(np.rint(rgb), 0, 255), a[..., 3:]]).astype(np.uint8), 'RGBA')
    glow = Image.new('RGBA', (w, h), GLOW + (0,))
    ga = word.split()[3].filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * glow_a)))
    glow.putalpha(ga)
    return word, glow


# ---------------------------------------------------------------------------- the colour turn
def hue_shift_to_red(src):
    """every saturated pixel's hue turned to the curse's red (the gold frame, bands, sparks), the pale ones to bone"""
    a = np.asarray(src.convert('RGBA')).astype(np.float32)
    rgb = a[..., :3] / 255.0
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lum = 0.3 * rgb[..., 0] + 0.59 * rgb[..., 1] + 0.11 * rgb[..., 2]
    red = np.array(RED, dtype=np.float32) / 255.0
    bone = np.array(BONE, dtype=np.float32) / 255.0
    # saturated -> the red scaled by the pixel's own brightness (keeps the bevel shading); pale and bright -> bone
    tinted = red[None, None, :] * (mx / max(red.max(), 1e-6))[..., None]
    pale = (sat < 0.25) & (lum > 0.72)
    out = np.where((sat >= 0.25)[..., None], np.clip(tinted, 0, 1), rgb)
    out = np.where(pale[..., None], bone[None, None, :] * (lum / 0.95)[..., None], out)
    a[..., :3] = np.clip(out * 255.0, 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def clear_rows(px, box, left, right):
    """every row of `box` (x0, y0, x1, y1) back to its own field: a straight blend from the mean of its `left`
    columns to the mean of its `right` columns - all four channels, so an old word's alpha goes too"""
    x0, y0, x1, y1 = box
    out = px.astype(np.float64).copy()
    xs = np.arange(x0, x1)
    t = ((xs - x0) / max(x1 - 1 - x0, 1))[:, None]
    for y in range(y0, y1):
        L = px[y, left[0]:left[1]].astype(np.float64).mean(0)
        R = px[y, right[0]:right[1]].astype(np.float64).mean(0)
        out[y, x0:x1] = L * (1 - t) + R * t
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def stamp_field(px):
    """the banner interior without its word: BAN_FIELD everywhere, the inner border's glow fading in from the top
    and bottom rows, and the edge flares' glow carried in from the column just outside each side of the box (an
    exponential fade, so the box has no edge). Alpha is the plate's own BAN_FIELD_A - one value, no letters in it."""
    x0, y0, x1, y1 = BAN_CLEAR
    out = px.astype(np.float64).copy()
    ys = np.arange(y0, y1)
    xs = np.arange(x0, x1)
    base = np.array(BAN_FIELD + (BAN_FIELD_A,), np.float64)
    # the border's inner glow: the top / bottom rows of the box are lit by the line just outside it
    top = px[y0 - 1, 160].astype(np.float64)
    bot = px[y1, 160].astype(np.float64)
    gt = np.exp(-(ys - y0) / 3.0)[:, None]
    gb = np.exp(-(y1 - 1 - ys) / 3.0)[:, None]
    col = base[None, :] * (1 - gt - gb).clip(0, 1) + top[None, :] * gt * 0.35 + bot[None, :] * gb * 0.35         + base[None, :] * (gt + gb) * 0.65
    F = np.repeat(col[:, None, :], len(xs), axis=1)
    # the flares' glow from each side, read on the column just outside the box
    L = px[y0:y1, x0 - 1].astype(np.float64)
    R = px[y0:y1, x1].astype(np.float64)
    wl = np.exp(-(xs - x0) / 26.0)[None, :, None]
    wr = np.exp(-(x1 - 1 - xs) / 26.0)[None, :, None]
    F = F * (1 - wl - wr).clip(0, 1) + L[:, None, :] * wl + R[:, None, :] * wr
    out[y0:y1, x0:x1] = F
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def diamonds(im):
    """the stamp's two side diamonds, redrawn in the curse's colours: a glow, a red rim, a hot core"""
    w, h = im.size
    lay = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for cx, cy in BAN_DIAMONDS:
        for r, col in ((9.5, (226, 30, 44, 255)), (6.5, (255, 168, 156, 255))):
            d.polygon([((cx) * SS, (cy - r) * SS), ((cx + r) * SS, cy * SS), (cx * SS, (cy + r) * SS),
                       ((cx - r) * SS, cy * SS)], fill=col)
    lay = lay.resize((w, h), Image.LANCZOS)
    glow = Image.new('RGBA', (w, h), GLOW + (0,))
    glow.putalpha(lay.split()[3].filter(ImageFilter.GaussianBlur(5)).point(lambda v: min(255, int(v * 1.2))))
    out = im.copy()
    out.alpha_composite(glow)
    out.alpha_composite(lay)
    return out


# ---------------------------------------------------------------------------- the three images
def make_tile(M):
    src = Image.open(os.path.join(IMG, 'i_tod_spin_tile_legendary.png')).convert('RGBA')
    if src.size != OUTPUTS['i_tod_spin_tile_cursed']:
        raise SystemExit('make_spin_art: the legendary tile is %s' % (src.size,))
    w, h = src.size
    px = np.asarray(src)
    # the word's own cap height and baseline (its gold ink in the band), so CURSED sits where LEGENDARY sat
    r_, g_, b_ = (px[..., i].astype(np.int32) for i in range(3))
    ink = (px[..., 3] > 200) & (r_ > 150) & (g_ > 110) & (r_ - b_ > 70) & (g_ - b_ > 40)
    x0, y0, x1, y1 = TILE_BAND
    ink[:y0] = False
    ink[y1:] = False
    ink[:, :x0] = False
    ink[:, x1:] = False
    rows = np.where(ink.any(axis=1))[0]
    if not len(rows):
        raise SystemExit('make_spin_art: no baked rarity word found on the legendary tile')
    cap, baseline = float(rows.max() - rows.min() + 1), float(rows.max() + 1)
    clean = Image.fromarray(clear_rows(px, TILE_BAND, TILE_FIELD_L, TILE_FIELD_R), 'RGBA')
    out = hue_shift_to_red(clean)
    word, glow = neon_word((w, h), M, 'CURSED', cap, w / 2.0, baseline, 0.30, 4.5, 1.25)
    out.alpha_composite(glow)
    out.alpha_composite(word)
    return out


def make_banner(M):
    src = Image.open(os.path.join(IMG, 'i_tod_spin_banner_legendary.png')).convert('RGBA')
    if src.size != OUTPUTS['i_tod_spin_banner_cursed']:
        raise SystemExit('make_spin_art: the legendary banner is %s' % (src.size,))
    w, h = src.size
    px = np.asarray(src)
    # the LEGENDARY word's pale fill rows give the stamp's cap height and baseline
    x0, y0, x1, y1 = BAN_CLEAR
    pale = (px[..., 3] > 200) & (px[..., :3].min(axis=2) > 200)
    pale[:, :x0] = False
    pale[:, x1:] = False
    rows = np.where(pale.any(axis=1))[0]
    cap = float(rows.max() - rows.min() + 1) if len(rows) else 96.0
    baseline = float(rows.max() + 1) if len(rows) else h * 0.72
    clean = Image.fromarray(stamp_field(px), 'RGBA')
    out = hue_shift_to_red(clean)
    out = diamonds(out)
    word, glow = neon_word((w, h), M, 'CURSED', cap, w / 2.0, baseline, 0.42, 9.0, 1.6)
    out.alpha_composite(glow)
    out.alpha_composite(word)
    return out


def make_icon():
    """the Dealer's face, as i_tod_spin_dealer_* draw it: hood, opening, shield mask, X eyes, stitched grin"""
    size = OUTPUTS['i_tod_spin_ico_cursed'][0]
    S = size * SS
    u = S / 208.0

    def P(pts):
        return [(x * u, y * u) for x, y in pts]

    def W(v):
        return max(1, int(round(v * u)))

    base = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    # the hood: a tall rounded arch, a little fuller on the left (the portraits' lean), black outline
    hood = [(20, 208), (22, 150), (28, 104), (42, 64), (62, 34), (88, 16), (110, 12), (134, 18), (158, 36),
            (176, 66), (186, 104), (190, 150), (190, 208)]
    d.polygon(P(hood), fill=(10, 8, 11, 255))
    hood_in = [(29, 208), (31, 152), (37, 108), (50, 70), (68, 42), (92, 25), (110, 21), (132, 27), (153, 43),
               (169, 71), (178, 106), (181, 152), (181, 208)]
    d.polygon(P(hood_in), fill=(36, 32, 38, 255))
    # the hood's fold: a slightly lighter crown band
    d.polygon(P([(52, 66), (70, 40), (92, 27), (110, 24), (130, 29), (150, 44), (164, 66), (150, 58), (130, 46),
                 (110, 42), (90, 46), (70, 56)]), fill=(46, 41, 48, 255))
    # the red rim light down the hood's left edge and over its crown (as the portraits light it)
    d.line(P([(33, 196), (34, 150), (40, 108), (52, 72), (70, 44), (92, 27), (110, 22)]), fill=(214, 46, 58, 255),
           width=W(3.2), joint='curve')
    d.line(P([(110, 22), (130, 27), (150, 40), (166, 60), (176, 90)]), fill=(120, 30, 40, 255), width=W(2.0), joint='curve')
    # the opening: a dark oval the face sits back in
    d.ellipse([48 * u, 52 * u, 162 * u, 200 * u], fill=(8, 6, 9, 255))
    d.ellipse([54 * u, 58 * u, 156 * u, 194 * u], fill=(16, 13, 17, 255))
    # the mask: a shield - broad brow, straight cheeks, tapering to a rounded chin; dark outline, charcoal plate
    mask = [(64, 70), (84, 64), (105, 62), (126, 64), (146, 70), (149, 96), (148, 126), (140, 150), (126, 170),
            (112, 182), (104, 185), (96, 182), (82, 170), (68, 150), (60, 126), (59, 96)]
    d.polygon(P(mask), fill=(12, 10, 13, 255))
    inner = [(68, 74), (86, 68), (105, 66), (124, 68), (142, 74), (145, 97), (144, 125), (136, 148), (123, 166),
             (110, 177), (104, 180), (98, 177), (85, 166), (72, 148), (64, 125), (63, 97)]
    d.polygon(P(inner), fill=(62, 56, 62, 255))
    # its lower facets a shade darker (the light comes from above)
    d.polygon(P([(64, 125), (144, 125), (136, 148), (123, 166), (110, 177), (104, 180), (98, 177), (85, 166),
                 (72, 148)]), fill=(52, 47, 53, 255))
    # the pale centre ridge: a band down the brow ending in a point (the arrow the portraits show)
    d.polygon(P([(99, 70), (111, 70), (111, 112), (118, 112), (105, 132), (92, 112), (99, 112)]),
              fill=(88, 82, 90, 255))
    # the brow's top bevel
    d.line(P([(70, 76), (86, 71), (105, 69), (124, 71), (140, 76)]), fill=(96, 90, 98, 255), width=W(2), joint='curve')
    # the neon: X eyes (the left a hair larger) and the stitched grin with its hook at the left corner
    neon = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    n = ImageDraw.Draw(neon)
    core = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    c = ImageDraw.Draw(core)
    for cx, cy, r in ((83, 102, 11.5), (126, 101, 10.5)):
        for sx in (1, -1):
            seg = P([(cx - r, cy - sx * r), (cx + r, cy + sx * r)])
            n.line(seg, fill=(236, 34, 50, 255), width=W(7))
            c.line(seg, fill=(255, 196, 196, 255), width=W(2.4))
    grin = [(62, 118), (66, 127), (74, 136), (86, 144), (100, 148), (114, 147), (128, 141), (139, 132), (147, 121)]
    n.line(P(grin), fill=(236, 34, 50, 255), width=W(6), joint='curve')
    c.line(P(grin), fill=(255, 196, 196, 255), width=W(2.2), joint='curve')
    hook = [(58, 112), (62, 118)]
    n.line(P(hook), fill=(236, 34, 50, 255), width=W(5))
    # the stitches hang off the grin like teeth, close-set and uneven (the portraits draw ten or so)
    gx = np.array([p[0] for p in grin], float)
    gy = np.array([p[1] for p in grin], float)
    for i, x in enumerate(np.linspace(70, 140, 11)):
        y = float(np.interp(x, gx, gy))
        ln = (7, 9, 6, 10, 7, 8, 6, 9, 7, 10, 6)[i]
        seg = P([(x, y + 1.5), (x - 0.6, y + 1.5 + ln)])
        n.line(seg, fill=(236, 34, 50, 255), width=W(3.0))
        c.line(seg, fill=(255, 170, 170, 255), width=W(1.1))
    face = base.resize((size, size), Image.LANCZOS)
    neon_s = neon.resize((size, size), Image.LANCZOS)
    core_s = core.resize((size, size), Image.LANCZOS)
    glow = Image.new('RGBA', (size, size), GLOW + (0,))
    glow.putalpha(neon_s.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v: min(255, int(v * 1.5))))
    halo = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([46, 76, 162, 166], fill=RED + (60,))
    halo = halo.filter(ImageFilter.GaussianBlur(14))
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out.alpha_composite(face)
    # the red light the neon throws on the plate, kept inside the face
    lit = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    lit.alpha_composite(halo)
    la = np.asarray(lit).astype(np.float64)
    fa = np.asarray(face.split()[3]).astype(np.float64) / 255
    la[..., 3] *= fa
    out.alpha_composite(Image.fromarray(np.rint(la).astype(np.uint8), 'RGBA'))
    out.alpha_composite(glow)
    out.alpha_composite(neon_s)
    out.alpha_composite(core_s)
    return out


def encode(im):
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=False)
    return buf.getvalue()


def wiring_problems():
    out = []
    gdt = open(os.path.join(ROOT, 'source_data', 'tod_ui_images.gdt'), encoding='utf-8', errors='replace').read()
    zone = open(os.path.join(ROOT, 'zone_source', 'zm_tod2_cybercity.zone'), encoding='utf-8', errors='replace').read()
    lua = open(os.path.join(ROOT, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodSpinReel.lua'), encoding='utf-8', errors='replace').read()
    for name in OUTPUTS:
        if ('"%s" ( "image.gdf" )' % name) not in gdt or ('"baseImage" "source_data/tod_ui_images/_images/%s.png"' % name) not in gdt:
            out.append('GDT: no image block for %s' % name)
        if not re.search(r'^image,%s\r?$' % re.escape(name), zone, re.M):
            out.append('zone: no image line for %s' % name)
        if ('"%s"' % name) not in lua:
            out.append('TodSpinReel.lua does not name %s' % name)
    return out


def main():
    check = '--check' in sys.argv
    outdir = None
    if '--out' in sys.argv:
        outdir = os.path.join(os.path.abspath(sys.argv[sys.argv.index('--out') + 1]), 'source_data', 'tod_ui_images', '_images')
        os.makedirs(outdir, exist_ok=True)
    M = metrics()
    made = {'i_tod_spin_tile_cursed': make_tile(M), 'i_tod_spin_banner_cursed': make_banner(M), 'i_tod_spin_ico_cursed': make_icon()}
    bad = []
    for name, im in made.items():
        if im.size != OUTPUTS[name]:
            raise SystemExit('make_spin_art: %s came out %s' % (name, im.size))
        if any(v % 4 for v in im.size):
            raise SystemExit('make_spin_art: %s is not a multiple of 4' % name)
        path = os.path.join(outdir or IMG, name + '.png')
        if check:
            if not os.path.exists(path):
                bad.append('%s.png is missing' % name)
            elif open(path, 'rb').read() != encode(im):
                bad.append('%s.png differs from what the generator makes' % name)
        else:
            open(path, 'wb').write(encode(im))
            print('wrote', path, im.size)
    if check:
        bad += wiring_problems()
        if bad:
            print('CURSED SPIN ART STALE: ' + '; '.join(bad) + ' - run: python -B tools/dealer_house/make_spin_art.py')
            sys.exit(1)
        print('CURSED SPIN ART OK: 3 images match the generator; GDT + zone + Lua wired')
        return
    if '--review' in sys.argv:
        os.makedirs(os.path.dirname(REVIEW), exist_ok=True)
        tile, banner, icon = made['i_tod_spin_tile_cursed'], made['i_tod_spin_banner_cursed'], made['i_tod_spin_ico_cursed']
        leg = Image.open(os.path.join(IMG, 'i_tod_spin_tile_legendary.png')).convert('RGBA')
        legb = Image.open(os.path.join(IMG, 'i_tod_spin_banner_legendary.png')).convert('RGBA')
        W = 1640
        sheet = Image.new('RGBA', (W, 416 + 208 * 2 + 240 + 80), (30, 30, 36, 255))
        sheet.alpha_composite(leg, (20, 20)); sheet.alpha_composite(tile, (620, 20))
        sheet.alpha_composite(icon, (1260, 120))
        sheet.alpha_composite(legb, (20, 460)); sheet.alpha_composite(banner, (20, 680))
        sheet.save(REVIEW)
        print('review:', os.path.relpath(REVIEW, ROOT))


if __name__ == '__main__':
    main()
