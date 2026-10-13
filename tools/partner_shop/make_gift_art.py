"""THE DEALER'S GIFT's reel art (docs/209), GENERATED from the shipped Black Market spin art - never paint these by hand.

  python -B tools/partner_shop/make_gift_art.py           write the six PNGs into source_data/tod_ui_images/_images/
  python -B tools/partner_shop/make_gift_art.py --check   FAIL (exit 1) on any byte of difference, or if a GDT block,
                                                          a zone image line or TodSpinReel.lua's registration is missing
  python -B tools/partner_shop/make_gift_art.py --review  also write art/dealer_gift/review/gift_art.png

THE SIX IMAGES (TodSpinReel.lua ART.gift, LOCKSTEP):
  i_tod_spin_tile_gift            560 x 416  the RARE tile (the clean frame: seven of these share the reel with the
                                             robots' portraits) with its blue turned to the companion's cyan (the
                                             HUD's companion bar), its foot word re-set as COMPANION from the map's
                                             glyph sheets exactly as TodGlyphRow lays letters out in game
  i_tod_spin_banner_gift          1600 x 208 the LEGENDARY banner in cyan, its word re-set as ON THE HOUSE

THE WORDS ARE SET LIKE THEIR SIBLINGS' (W3F library audit, 2026-10-05). The first cut set COMPANION / ON THE HOUSE at
the face's own tight tracking in one flat pale cyan with a soft blur behind, so on the reel they read as a different
stamp from COMMON / RARE / EPIC / LEGENDARY / CURSED (measured: sibling letters 116 px tall on the banner with 58 px
gaps, 42 px on the tile with 18 px gaps; the gift's 106 / 22 and 37 / 8). Now each word is set the way
tools/dealer_house/make_spin_art.py sets CURSED: the cells' own dark outline and bevel, the white face multiplied by a
neon gradient over the cap (hot at the top, deep at the foot - here cyan), a glow of the companion's cyan under it,
and the bright face sized and placed on the sibling word's measured face box (the LEGENDARY tile / banner word, read
off the shipped art - never typed in), with the widest tracking that fits that word's measured span.
  i_tod_spin_ico_comp_<name> x 4  208 x 208  each companion's docs/195 portrait (i_tod_spin_comp_<name>, 240 x 192) cut
                                             square for the tile's window: the centre 192 x 192, scaled to the window,
                                             the window's two chamfered corners cut, a thin cyan rim inside the cut

Every output is RGBA 8-bit at the size the reel's slot maps expect (tools/partner_shop/gen_spin_art_refs.py: a tile's
icon window is 52 x 52 canvas units = 208 x 208 px at the tile art's 4 px a unit). The GDT blocks are compressed high
color, sRGB3chAlpha, noMipMaps + noPicMip like every spin image; every size is a multiple of 4 (the BC7 rule).
"""
import io, os, re, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMG = os.path.join(ROOT, 'source_data', 'tod_ui_images', '_images')
METRICS = os.path.join(ROOT, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodGlyphMetrics.lua')
REVIEW = os.path.join(ROOT, 'art', 'dealer_gift', 'review', 'gift_art.png')
SS = 4
TOD_SPACE_ADV, TOD_TRACK = 0.30, 0.055   # TodGlyphRow.set's space advance and tracking (fractions of the cell / cap)

COMPANIONS = ['protector', 'talon', 'raps', 'cerberus']   # P3.COMPANIONS order (_tod_partners define order)
OUTPUTS = {'i_tod_spin_tile_gift': (560, 416), 'i_tod_spin_banner_gift': (1600, 208)}
for _c in COMPANIONS:
    OUTPUTS['i_tod_spin_ico_comp_' + _c] = (208, 208)

CYAN = (31, 230, 255)        # the companion's cyan: TodSpinReel P3.GIFT.col { 0.12, 0.9, 1 }
CYAN_HOT = (196, 252, 255)   # the lettering
PALE = (214, 250, 255)       # the gold art's pale highlights, in cyan
# the words' neon fill, top to bottom of the cap (make_spin_art NEON_TOP / _MID / _BOT, in the companion's cyan). The
# siblings' letters are a BRIGHT hue, nearly flat over the cap (measured: RARE (130, 199, 254) -> (89, 181, 253),
# LEGENDARY (252, 206, 105) with a (255, 223, 152) light band), so the cyan stays light all the way down - a deep
# foot read as a different, heavier stamp on the cyan plate
NEON_TOP, NEON_MID, NEON_BOT = (225, 253, 255), (130, 240, 255), (70, 220, 252)
TRACK_MAX = {'tile': 0.30, 'banner': 0.42}   # make_spin_art's CURSED tile / stamp tracking: the widest a word is set
TRACK_MIN = 0.22                              # below this a word shrinks instead: ON THE HOUSE is three words in one
                                              # stamp's span, and at the face's own tracking it read as one block
WINDOW_CUT = 12              # px: the icon's two chamfered corners (the tile window's are 16 at its frame line)


# ---------------------------------------------------------------------------- the glyph sheets (make_badge.py's reader)
def metrics():
    t = open(METRICS, encoding='utf-8').read()
    m = re.search(r'letters = \{\s*cw = (\d+), ch = (\d+), baseline = (\d+), cap = (\d+),\s*g = \{(.*?)\n\t\t\},', t, re.S)
    if not m:
        raise SystemExit('make_gift_art: TodGlyphMetrics.lua: no letters set')
    cw, ch, base, cap = (int(v) for v in m.group(1, 2, 3, 4))
    g = {}
    for c, adv, x in re.findall(r'\["(.)"\] = \{ adv = (\d+), x = (\d+)', m.group(5)):
        g[c] = (int(adv), int(x))
    return dict(cw=cw, ch=ch, baseline=base, cap=cap, g=g)


def cell(c):
    return Image.open(os.path.join(IMG, 'i_tod_hud_l%s.png' % c.lower())).convert('RGBA')


def measure(M, text, cap, track=TOD_TRACK):
    s = cap / M['cap']
    total, first = 0.0, True
    for c in text:
        if c == ' ':
            total += M['cw'] * s * TOD_SPACE_ADV
        else:
            if c.lower() not in M['g']:
                raise SystemExit('make_gift_art: no glyph for %r' % c)
            if not first:
                total += cap * track
            total += M['g'][c.lower()][0] * s
        first = False
    return total


def typeset(layer, M, text, cap, cx, baseline, rgb, track=TOD_TRACK):
    """TodGlyphRow.set's walk, centred on cx, drawn SS times larger onto `layer`. `track` is the gap between letters
    as a fraction of the cap (TodGlyphRow's own 0.055 unless widened, make_spin_art's typeset)."""
    s = cap / M['cap']
    pen, first = cx - measure(M, text, cap, track) / 2, True
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


# ---------------------------------------------------------------------------- recolour
def to_cyan(src):
    """every saturated pixel's hue turned to the companion's cyan (scaled by its own brightness: the bevels keep their
    shading), the pale highlights to a pale cyan-white; the dark plates are left as they are"""
    a = np.asarray(src.convert('RGBA')).astype(np.float32)
    rgb = a[..., :3] / 255.0
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lum = 0.3 * rgb[..., 0] + 0.59 * rgb[..., 1] + 0.11 * rgb[..., 2]
    cyan = np.array(CYAN, dtype=np.float32) / 255.0
    pale = np.array(PALE, dtype=np.float32) / 255.0
    tinted = cyan[None, None, :] * (mx / max(cyan.max(), 1e-6))[..., None]
    ispale = (sat < 0.25) & (lum > 0.72)
    out = np.where((sat >= 0.25)[..., None], np.clip(tinted, 0, 1), rgb)
    out = np.where(ispale[..., None], pale[None, None, :] * (lum / 0.95)[..., None], out)
    a[..., :3] = np.clip(out * 255.0, 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def gold_ink(px):
    r_, g_, b_ = px[..., 0], px[..., 1], px[..., 2]
    return (px[..., 3] > 200) & (r_ > 150) & (g_ > 110) & (r_ - b_ > 70) & (g_ - b_ > 40)


def blue_ink(px):
    r_, b_ = px[..., 0], px[..., 2]
    return (px[..., 3] > 200) & (b_ > 180) & (b_ - r_ > 60)


def word_box(px, y_lo, y_hi, x_lo, x_hi, rule=gold_ink):
    """a baked word's ink (by `rule`) inside a region -> (x0, y0, x1, y1) or None"""
    ink = rule(px)
    ink[:y_lo] = False
    ink[y_hi:] = False
    ink[:, :x_lo] = False
    ink[:, x_hi:] = False
    rows, cols = np.where(ink.any(axis=1))[0], np.where(ink.any(axis=0))[0]
    if not len(rows) or not len(cols):
        return None
    return int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max())


def row_fill(img, region, x0, x1):
    """paint `region` (a bool mask) with the image's OWN plate, row by row: each row takes the median of that row's
    PLATE pixels between x0 and x1 - the background showing between the old word's letters (their bright faces and
    dark outlines left out: 60 < r + g + b < 330). The plate's own vertical gradient carries through, no seam shows,
    and nothing from the end ornaments (their glints throw a light streak across the rows beside them) is sampled."""
    o = np.asarray(img).copy()
    h, w = o.shape[:2]
    for y in np.where(region.any(axis=1))[0]:
        s = o[y, max(0, x0):min(w, x1 + 1), :3].astype(np.int32)
        lum = s.sum(axis=1)
        plate = s[(lum > 60) & (lum < 330)]
        if not len(plate):
            continue
        xs = np.where(region[y])[0]
        o[y, xs, :3] = np.median(plate, axis=0).astype(np.uint8)
        o[y, xs, 3] = 255
    return Image.fromarray(o, 'RGBA')


# ---------------------------------------------------------------------------- the neon word (make_spin_art's method)
def face_rows(im):
    """the BRIGHT FACE of set letters (opaque, brightest channel > 170: the fill and the light bevel - the dark
    outline, the plate and the soft glow are left out): (y0, y1, x0, x1) inclusive, or None. A row holding one
    unbroken lit run longer than 35 % of the width is a frame line or a rule, not lettering (a letter's widest bar is
    one letter wide); the letters are the longest run of rows between."""
    a = np.asarray(im)
    m = (a[..., 3] > 240) & (a[..., :3].max(axis=2) > 170)
    pad = np.zeros((m.shape[0], 1), bool)
    e = np.diff(np.hstack([pad, m, pad]).astype(np.int8), axis=1)
    longest = np.zeros(m.shape[0])
    for y in np.where(m.any(axis=1))[0]:
        starts, ends = np.where(e[y] == 1)[0], np.where(e[y] == -1)[0]
        longest[y] = (ends - starts).max()
    ok = m.any(axis=1) & (longest <= 0.35 * m.shape[1])
    best, run = (0, -1), None
    for y in range(len(ok) + 1):
        if y < len(ok) and ok[y]:
            run = y if run is None else run
        elif run is not None:
            if y - 1 - run > best[1] - best[0]:
                best = (run, y - 1)
            run = None
    if best[1] < best[0]:
        return None
    cols = np.where(m[best[0]:best[1] + 1].any(axis=0))[0]
    return best[0], best[1], int(cols.min()), int(cols.max())


def fit_word(M, text, face, room, track_max):
    """the cap, baseline and tracking that put `text`'s bright face on the sibling word's face rows `face` (y0, y1,
    inclusive) and its width inside `room` px: the face height and its foot below the baseline are read off a probe
    render of the same word (the cells' bevel sits under the baseline), the tracking is the widest that fits (never
    under TRACK_MIN; past that the cap shrinks and the foot stays on the sibling's)"""
    probe, base0 = 100.0, 170.0
    lay = Image.new('RGBA', (int(measure(M, text, probe, track_max) + 80) * SS, 260 * SS), (0, 0, 0, 0))
    typeset(lay, M, text, probe, lay.width / SS / 2.0, base0, (255, 255, 255), track_max)
    fy0, fy1, _, _ = face_rows(lay.resize((lay.width // SS, lay.height // SS), Image.LANCZOS))
    ratio, foot = (fy1 - fy0 + 1) / probe, (fy1 + 1) - base0
    cap = (face[1] - face[0] + 1) / ratio
    track = track_max
    while measure(M, text, cap, track) > room and track > TRACK_MIN + 1e-9:
        track = round(track - 0.005, 3)
    while measure(M, text, cap, track) > room:
        cap -= 0.25
    baseline = face[1] + 1 - foot * cap / probe
    return cap, baseline, track


def neon_word(size, M, text, cap, cx, baseline, track, glow_r, glow_a):
    """`text` as the stamps set their word (make_spin_art.neon_word, in cyan): the cells' own dark outline and bevel,
    the white face multiplied by a neon gradient over the cap (light at the top, deep at the foot), a cyan glow
    under it. Returns (word, glow)."""
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
    glow = Image.new('RGBA', (w, h), CYAN + (0,))
    glow.putalpha(word.split()[3].filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * glow_a))))
    return word, glow


# ---------------------------------------------------------------------------- the six images
def make_tile(M):
    src = Image.open(os.path.join(IMG, 'i_tod_spin_tile_rare.png')).convert('RGBA')
    if src.size != OUTPUTS['i_tod_spin_tile_gift']:
        raise SystemExit('make_gift_art: the rare tile is %s' % (src.size,))
    w, h = src.size
    out = to_cyan(src)
    # the baked rarity word (RARE, centred in the lower band; the frame's bottom-right chamfer is clear of x < w - 60)
    # -> the band's own plate painted over it row by row, COMPANION set in its place at its cap height and baseline
    box = word_box(np.asarray(src).astype(np.int32), int(h * 0.62), int(h * 0.94), 40, w - 60, blue_ink)
    if box is None:
        raise SystemExit('make_gift_art: no baked rarity word on the rare tile')
    x0, y0, x1, y1 = box
    region = np.zeros((h, w), dtype=bool)
    region[y0 - 8:y1 + 9, x0 - 16:x1 + 17] = True
    out = row_fill(out, region, x0, x1)
    # COMPANION's bright face on RARE's face rows, as wide as the widest sibling word on a tile allows (LEGENDARY,
    # between the legendary tile's corner scrolls, x 68..490)
    fy0, fy1, _, _ = face_rows(src.crop((x0, y0, x1 + 1, y1 + 1)))
    leg = np.asarray(Image.open(os.path.join(IMG, 'i_tod_spin_tile_legendary.png')).convert('RGBA')).astype(np.int32)
    lbox = word_box(leg, y0 + fy0, y0 + fy1 + 1, 68, 491)     # its letters' rows only: the band's gold line is under them
    if lbox is None:
        raise SystemExit('make_gift_art: no baked rarity word on the legendary tile')
    cap, baseline, track = fit_word(M, 'COMPANION', (y0 + fy0, y0 + fy1), float(lbox[2] - lbox[0] + 1), TRACK_MAX['tile'])
    word, glow = neon_word((w, h), M, 'COMPANION', cap, w / 2.0, baseline, track, 4.5, 1.25)
    out.alpha_composite(glow)
    out.alpha_composite(word)
    return out


def make_banner(M):
    src = Image.open(os.path.join(IMG, 'i_tod_spin_banner_legendary.png')).convert('RGBA')
    if src.size != OUTPUTS['i_tod_spin_banner_gift']:
        raise SystemExit('make_gift_art: the legendary banner is %s' % (src.size,))
    w, h = src.size
    out = to_cyan(src)
    px = np.asarray(src).astype(np.int32)
    # the word LEGENDARY: its ink inside the plate, clear of the end ornaments (the diamonds and glints)
    box = word_box(px, 20, h - 20, 220, w - 220)
    if box is None:
        raise SystemExit('make_gift_art: no word on the legendary banner')
    x0, y0, x1, y1 = box
    # the plate under the word: the solid silhouette eroded clear of its rim, filled row by row with the plate's own
    # gradient sampled between the old word's letters (row_fill)
    solid = src.split()[3].point(lambda v: 255 if v > 128 else 0)
    inner = np.asarray(solid.filter(ImageFilter.MinFilter(25))) > 0
    region = inner.copy()   # the whole plate inside its rim: the end diamonds sit on the rim, outside it
    out = row_fill(out, region, x0, x1)
    # ON THE HOUSE's bright face on LEGENDARY's face rows, inside LEGENDARY's face span, at the widest tracking that fits
    fy0, fy1, fx0, fx1 = face_rows(src.crop((x0, y0, x1 + 1, y1 + 1)))
    cap, baseline, track = fit_word(M, 'ON THE HOUSE', (y0 + fy0, y0 + fy1), float(fx1 - fx0 + 1), TRACK_MAX['banner'])
    word, glow = neon_word((w, h), M, 'ON THE HOUSE', cap, w / 2.0, baseline, track, 9.0, 1.6)
    out.alpha_composite(glow)
    out.alpha_composite(word)
    return out


def window_mask(size, cut):
    m = Image.new('L', (size * SS, size * SS), 0)
    S, c = size * SS, cut * SS
    ImageDraw.Draw(m).polygon([(c, 0), (S, 0), (S, S - c), (S - c, S), (0, S), (0, c)], fill=255)
    return m.resize((size, size), Image.LANCZOS)


def make_icon(name):
    size = OUTPUTS['i_tod_spin_ico_comp_' + name][0]
    src = Image.open(os.path.join(IMG, 'i_tod_spin_comp_%s.png' % name)).convert('RGBA')
    if src.size != (240, 192):
        raise SystemExit('make_gift_art: i_tod_spin_comp_%s is %s, not 240 x 192' % (name, src.size))
    side = min(src.size)
    left = (src.size[0] - side) // 2
    sq = src.crop((left, 0, left + side, side)).resize((size, size), Image.LANCZOS)
    mask = window_mask(size, WINDOW_CUT)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out.paste(sq, (0, 0), mask)
    # a thin cyan rim just inside the cut (it reads as the window's own glass edge). NOTE: never MaxFilter(1) - on
    # this machine's Pillow a size-1 rank filter is a hard "int divide by zero" crash (exit 127, no traceback)
    inner = mask.filter(ImageFilter.MinFilter(5))
    line = Image.fromarray(np.clip(np.asarray(mask).astype(np.int16) - np.asarray(inner).astype(np.int16), 0, 255).astype(np.uint8), 'L')
    out.alpha_composite(Image.composite(Image.new('RGBA', (size, size), CYAN + (255,)), Image.new('RGBA', (size, size), (0, 0, 0, 0)),
                                        line.point(lambda v: v * 170 // 255)))
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
    M = metrics()
    made = {'i_tod_spin_tile_gift': make_tile(M), 'i_tod_spin_banner_gift': make_banner(M)}
    for c in COMPANIONS:
        made['i_tod_spin_ico_comp_' + c] = make_icon(c)
    bad = []
    for name, im in made.items():
        if im.size != OUTPUTS[name]:
            raise SystemExit('make_gift_art: %s came out %s' % (name, im.size))
        if any(v % 4 for v in im.size):
            raise SystemExit('make_gift_art: %s is not a multiple of 4' % name)
        path = os.path.join(IMG, name + '.png')
        if check:
            if not os.path.exists(path):
                bad.append('%s.png is missing' % name)
            elif open(path, 'rb').read() != encode(im):
                bad.append('%s.png differs from what the generator makes' % name)
        else:
            open(path, 'wb').write(encode(im))
            print('wrote', os.path.relpath(path, ROOT), im.size)
    if check:
        bad += wiring_problems()
        if bad:
            print('GIFT SPIN ART STALE: ' + '; '.join(bad) + ' - run: python -B tools/partner_shop/make_gift_art.py')
            sys.exit(1)
        print('GIFT SPIN ART OK: %d images match the generator; GDT + zone + Lua wired' % len(made))
        return
    if '--review' in sys.argv:
        os.makedirs(os.path.dirname(REVIEW), exist_ok=True)
        tile = made['i_tod_spin_tile_gift']
        sheet = Image.new('RGBA', (1640, 416 + 208 + 260 + 60), (24, 24, 32, 255))
        # the tile with each companion in its window, at art size, as the reel composites them
        for i, c in enumerate(COMPANIONS):
            t = tile.copy()
            t.alpha_composite(made['i_tod_spin_ico_comp_' + c], (176, 32))
            sheet.alpha_composite(t.resize((390, 290), Image.LANCZOS), (20 + i * 405, 20))
        sheet.alpha_composite(made['i_tod_spin_banner_gift'], (20, 340))
        leg = Image.open(os.path.join(IMG, 'i_tod_spin_banner_legendary.png')).convert('RGBA')
        sheet.alpha_composite(leg.resize((800, 104), Image.LANCZOS), (20, 580))
        sheet.save(REVIEW)
        print('review:', os.path.relpath(REVIEW, ROOT))


if __name__ == '__main__':
    main()
