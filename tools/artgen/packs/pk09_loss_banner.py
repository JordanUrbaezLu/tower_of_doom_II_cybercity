"""pk09_loss_banner.py - the GAME OVER banner for the LOSS screen (PK09, 2026-10-04).

WHY. Every run that ends in a loss reached _tod_gameover.gsc lost_game_over (installed as
level.custom_game_over_hud_elem), which drew "GAME OVER  -  FLOOR N" in the stock hudelem font at
fontScale 3. The only end-screen art in the map, i_tod_win_banner ("YOU ESCAPED THE TOWER"), belongs
to the WIN path (_tod_finale escaped_game_over), and the finale is PARKED (TOD_FINALE_PARKED 1), so
the screen players actually reach had no map art at all. This draws its twin.

THE CHASSIS IS THE WIN BANNER'S, MEASURED (i_tod_win_banner.png, 2048x512, drawn by the game at 900x225):
  * the chamfered plate: top edge y 177 from x 255 to 1792, the points at x 207 / 1840 on y 256,
    bottom edge y 335; thin inner rules just inside it;
  * the stair above it: a trapezoid from x 822..1226 on the plate's top edge up to an apex at (1024, 55);
  * the floor grid below it: rungs at y 352 / 375 / 406 / 438 / 471, ending in rings that step out
    from x 240 to 179 (mirrored on the right), and two perspective rails from the plate's bottom;
  * the same soft glow footprint round all of it (alpha > 0 from x ~51 to ~1996).

THE LOSS RESTYLE (docs/184 THE UI THEME IS NEON SYNTHWAVE: no red anywhere; magenta = frame light and
headline words, cyan = rules / focus / info, violet = secondary, steel #4A3A70 = a DEAD tube):
  * dark violet glass plate (#1F1336 -> #140C24 -> #0C0716) inside a MAGENTA neon tube with a
    white-hot core; one stretch of the top tube is DEAD (steel, snapped, a few cyan sparks falling
    from the break) and one stretch of the bottom tube is failing (dim); a hairline crack runs down
    the glass from the break;
  * "GAME OVER" in MAGENTA NEON in the MAP'S TYPEFACE (the glyph-sheet cells TodGlyphRow draws in
    game, via artgen's metrics), tracked out for a title, with a cyan chromatic fringe;
  * THE STAIR IS BROKEN: the climb's lit path is snapped off below the apex, its pieces falling,
    the light at the top OUT; THE GRID IS DEAD: steel rungs with gaps, one rung snapped and
    hanging, the nodes dark but for a few embers;
  * no gold sparkle: a few violet / magenta embers drift down instead;
  * THE FLOOR READOUT: an EMPTY cyan-framed plate hung under the title. The floor number is LIVE
    text (a hudelem in lost_game_over) laid into it - the map's "baked chrome + empty live area"
    rule (docs/184): "FLOOR N" (the deepest floor the party reached on the descent), "UNDERCITY"
    (below the tower) or "THE CROWN" (a wipe before anyone left the crown island) - 9 characters at
    most. Its centre is READOUT_CY, LOCKSTEP with TOD_GO_READOUT_FRAC in _tod_gameover.gsc
    ( (READOUT_CY - 256) / 512 of the banner's drawn height below the banner's centre ); --check
    fails if the two drift.
  * THE EDGES: alpha is exactly 0 on every border (EDGE_X / EDGE_Y window) and the dark floor under
    the grid fades out instead of ending on a straight line - the image is wrap-sampled (clampU/V 0)
    and drawn over the live world, so any glow cut by the canvas would show as a faint rectangle.

USAGE
  python tools/artgen/packs/pk09_loss_banner.py              # art/generated/PK09-loss-banner/ + _review.png
  python tools/artgen/packs/pk09_loss_banner.py --stage DIR  # also write the PNG under DIR/source_data/tod_ui_images/_images/
  python tools/artgen/packs/pk09_loss_banner.py --install    # copy into source_data/tod_ui_images/_images/ (the landing)
  python tools/artgen/packs/pk09_loss_banner.py --check [--root DIR]
        regenerate in memory and fail on any byte that differs from the installed PNG (or the one
        under DIR), and on any break in the wiring: the GDT image + material blocks, the two zone
        lines, the #precache + SetShader in _tod_gameover.gsc and the READOUT lockstep.

Deterministic: no randomness, no timestamps; resvg + numpy + scipy only. Never hand-edit the PNG.
"""
import argparse, os, re, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402
import synthwave as _sw  # noqa: E402  (the UI theme: this banner's palette is synthwave.PAL's roles)

PACK = 'PK09-loss-banner'
NAME = 'i_tod_lose_banner'
MATERIAL = 'tod_lose_banner'
W, H = 2048, 512
SS = 2                                    # supersample for the vector layers (3 = +25 s of --check for edge pixels nobody sees at 900x225)

IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')
GDT_REL = os.path.join('source_data', 'tod_ui_images.gdt')
ZONE_REL = os.path.join('zone_source', 'zm_tod2_cybercity.zone')
GSC_REL = os.path.join('scripts', 'zm', 'zm_tod2_cybercity', '_tod_gameover.gsc')

# ------------------------------------------------------------------------------------- the palette
# THE THEME'S ROLES (tools/artgen/synthwave.py, RT 2026-10-05): this banner used to carry its own copy of the synthwave
# palette, so a theme switch could not reach it. Every colour is now a synthwave.PAL role; with THEME 'synthwave' they
# are the docs/184 values this banner shipped with (byte-identical), with THEME 'fallen' the red Fallen set: a red
# frame tube and a SOLID red title over charcoal glass, steel rules, a deep-red bloom, no chromatic fringe.
_c = _sw.hexrgb
PLATE = _c('plate')          # synthwave #0C0716
PANEL = _c('panel')          # #140C24
HEADER = _c('header')        # #1F1336
STEEL = _c('steel')          # #4A3A70 - the dead tube
MAGENTA = _c('magenta')      # #FF2BD1 - frame light, headline words (fallen: the red)
CYAN = _c('accent2')         # #1FE5FF - rules, the readout plate, info (fallen: bright steel, unlit)
VIOLET = _c('go_bloom')      # #7A46FF - secondary: the blooms, half the embers (fallen: a deep red)
LAVENDER = _c('lav')         # #B8AED8 - secondary text / the crack's glint
CORE = _c('go_core')         # the hot core of a frame-light tube
CYAN_CORE = _c('go_info_core')  # ... of a rule / spark
SPARK = _c('go_spark')       # the live wire's sparks (synthwave cyan, fallen a hot red)
FRINGE = _c('go_fringe')     # the title's chromatic fringe (synthwave only: LOOK fringe)

# ------------------------------------------------------------------- the chassis (measured, see top)
PLATE_HEX = [(255, 177), (1792, 177), (1840, 256), (1794, 335), (254, 335), (207, 256)]
STAIR_L, STAIR_R, STAIR_BASE_Y = 822.0, 1226.0, 177.0
APEX = (1024.0, 55.0)
GRID_Y = [352, 375, 406, 438, 471]
GRID_XL = [240, 225, 210, 194, 179]               # ring centres, left; the right side mirrors about 1023.5
DIAG = [((530, 336), (304, 472)), ((1517, 336), (1743, 472))]

# THE FLOOR READOUT - LOCKSTEP _tod_gameover.gsc TOD_GO_READOUT_FRAC = (READOUT_CY - 256) / 512.
READOUT = (760, 382, 1288, 462)                   # x0, y0, x1, y1 (chamfer 16 at top-left / bottom-right)
READOUT_CY = (READOUT[1] + READOUT[3]) // 2       # 422
READOUT_CHAMFER = 16
GRID_CLEAR = (736, 366, 1312, 478)                # the rungs stop round the readout

# THE TITLE
TITLE = 'GAME OVER'
TITLE_CAP = 104.0                                 # px of cap height (the win banner's is ~80; this is 9 letters, not 21)
TITLE_TRACK = 0.20                                # extra tracking, x cap, on top of TodGlyphRow's own 0.055
TITLE_CY = 256.0                                  # the plate's centre line

# THE DAMAGE (all fixed numbers - deterministic)
DEAD_TOP = (1492, 1668)                           # dead stretch of the top tube (x)
GAP_TOP = (1566, 1586)                            # the snapped gap inside it
DIM_BOTTOM = (330, 478)                           # failing stretch of the bottom tube (x)
DIM_K = 0.42
RULE_Y = (189, 323)
EDGE_X = (22, 110)                                # alpha 0 outside x 22 / 2025, full inside 110 / 1937
EDGE_Y = (3, 16)                                  # ... and y 3 / 508, full inside 16 / 495

# ---------------------------------------------------------------------------------------- helpers

def pts(p):
    return ' '.join('%.2f,%.2f' % xy for xy in p)


def cov(body, defs=''):
    """Coverage (float 0..1, H x W) of a WHITE svg body."""
    im = artgen.render_svg(artgen.svg_doc(W, H, body, defs), W, H, ss=SS)
    return np.clip(np.asarray(im, dtype=np.float64)[..., 3] / 255.0, 0.0, 1.0)


def poly(p, extra=''):
    return '<polygon points="%s" fill="#fff" %s/>' % (pts(p), extra)


def pline(p, w, cap='round', join='round', closed=False):
    tag = 'polygon' if closed else 'polyline'
    return ('<%s points="%s" fill="none" stroke="#fff" stroke-width="%.2f" stroke-linecap="%s" stroke-linejoin="%s"/>'
            % (tag, pts(p), w, cap, join))


def circ(x, y, r, stroke=None):
    if stroke:
        return '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="none" stroke="#fff" stroke-width="%.2f"/>' % (x, y, r, stroke)
    return '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="#fff"/>' % (x, y, r)


def blur(c, sigma):
    return ndimage.gaussian_filter(c, sigma, mode='constant')


def rows_mask(y0, y1):
    m = np.zeros((H, W))
    m[max(0, y0):min(H, y1), :] = 1.0
    return m


def box_mask(x0, y0, x1, y1):
    m = np.zeros((H, W))
    m[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] = 1.0
    return m


def vgrad(y0, y1, c0, c1):
    """An H x W x 3 vertical colour ramp from c0 (at y0) to c1 (at y1)."""
    t = np.clip((np.arange(H, dtype=np.float64) - y0) / float(y1 - y0), 0.0, 1.0)[:, None, None]
    a, b = np.array(c0, dtype=np.float64), np.array(c1, dtype=np.float64)
    return np.broadcast_to(a + (b - a) * t, (H, W, 3))


def rot(p, deg, cx, cy):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in p]


def stair_x(y):
    """The stair's left / right edges at height y (the win banner's trapezoid)."""
    t = (STAIR_BASE_Y - y) / (STAIR_BASE_Y - APEX[1])
    return STAIR_L + (APEX[0] - STAIR_L) * t, STAIR_R - (STAIR_R - APEX[0]) * t


class Canvas:
    """Premultiplied float RGBA, painted back to front."""

    def __init__(self):
        self.rgb = np.zeros((H, W, 3))
        self.a = np.zeros((H, W))

    def paint(self, c, rgb, alpha=1.0):
        a = np.clip(c * alpha, 0.0, 1.0)
        col = np.asarray(rgb, dtype=np.float64)
        if col.ndim == 1:
            col = col[None, None, :]
        self.rgb = col * a[..., None] + self.rgb * (1.0 - a)[..., None]
        self.a = a + self.a * (1.0 - a)

    def glow(self, c, rgb, sigma, k):
        self.paint(np.clip(blur(c, sigma) * k, 0.0, 1.0), rgb)

    def paint_rgba(self, rgb, a):
        self.rgb = rgb * a[..., None] + self.rgb * (1.0 - a)[..., None]
        self.a = a + self.a * (1.0 - a)

    def window(self, m):
        """Scale everything by the mask m (premultiplied, so colour and alpha fall together)."""
        self.rgb = self.rgb * m[..., None]
        self.a = self.a * m

    def image(self):
        a = self.a
        with np.errstate(invalid='ignore', divide='ignore'):
            rgb = np.where(a[..., None] > 1e-9, self.rgb / np.maximum(a, 1e-9)[..., None], 0.0)
        out = np.dstack([rgb, a * 255.0])
        out = np.clip(np.round(out), 0, 255).astype(np.uint8)
        out[out[..., 3] == 0] = 0                 # no stray RGB under zero alpha (deterministic bytes)
        return Image.fromarray(out, 'RGBA')

# ------------------------------------------------------------------------------- the map's typeface

def title_layer(text, cap, cy, track):
    """The title in the glyph-sheet cells (exactly the placement artgen.typeset / TodGlyphRow use),
    with `track` x cap of EXTRA space between characters. Returns (rgba float array, x0, x1)."""
    M = artgen.metrics()
    S = M['letters']
    s = cap / S['cap']
    adv = []
    for c in text:
        if c == ' ':
            adv.append(('space', S['cw'] * s * artgen.TOD_SPACE_ADV))
        else:
            sname, key, img = artgen._glyph(c)
            adv.append((c, M[sname]['g'][key][0] * (cap / M[sname]['cap'])))
    gap = cap * (artgen.TOD_TRACK + track)
    total = sum(a for _, a in adv) + gap * (len(text) - 1)
    pen = W / 2.0 - total / 2.0
    x0 = pen
    baseline = cy + cap / 2.0
    ss = 4
    layer = Image.new('RGBA', (W * ss, H * ss), (0, 0, 0, 0))
    for i, c in enumerate(text):
        if i:
            pen += gap
        if c == ' ':
            pen += adv[i][1]
            continue
        sname, key, img = artgen._glyph(c)
        Sx = M[sname]
        sx = cap / Sx['cap']
        a, gx = Sx['g'][key]
        left, top = pen - gx * sx, baseline - Sx['baseline'] * sx
        cell = artgen._cell(img).resize((int(round(Sx['cw'] * sx * ss)), int(round(Sx['ch'] * sx * ss))), Image.LANCZOS)
        layer.alpha_composite(cell, (int(round(left * ss)), int(round(top * ss))))
        pen += a * sx
    x1 = pen
    layer = layer.resize((W, H), Image.LANCZOS)
    return np.asarray(layer, dtype=np.float64), x0, x1


def neon_title(C, text):
    """GAME OVER in magenta neon: the cells' white fill becomes a hot-core-to-magenta ramp, their
    blue-grey bevel a deep magenta, their dark outline stays dark; a tight magenta halo (the win
    banner's cyan ring, recoloured), a wide bloom and a cyan chromatic fringe."""
    lay, x0, x1 = title_layer(text, TITLE_CAP, TITLE_CY, TITLE_TRACK)
    a = lay[..., 3] / 255.0
    L = (lay[..., 0] * 0.299 + lay[..., 1] * 0.587 + lay[..., 2] * 0.114)
    outline = np.array(_c('go_outline'), dtype=np.float64)
    bevel = np.array(_c('go_bevel'), dtype=np.float64)
    top, bot = TITLE_CY - TITLE_CAP / 2.0, TITLE_CY + TITLE_CAP / 2.0
    fill = vgrad(top + 6, bot - 4, _c('go_fill_top'), MAGENTA)
    t1 = np.clip((L - 24.0) / (150.0 - 24.0), 0.0, 1.0)[..., None]       # outline -> bevel
    t2 = np.clip((L - 170.0) / (226.0 - 170.0), 0.0, 1.0)[..., None]     # bevel -> fill
    rgb = outline + (bevel - outline) * t1
    rgb = rgb + (fill - rgb) * t2
    fillmask = a * np.clip((L - 170.0) / 56.0, 0.0, 1.0)

    C.glow(fillmask, VIOLET, 26.0, 0.55)                                 # wide bloom
    C.glow(a, MAGENTA, 6.0, 1.15)                                        # the halo ring
    ghost = np.zeros_like(a)
    ghost[:, :-6] = fillmask[:, 6:]                                      # 6 px to the LEFT
    if _sw.LOOK['fringe']:
        C.paint(ghost, FRINGE, 0.42)
    C.paint_rgba(rgb, a)
    return x0, x1

# ---------------------------------------------------------------------------------------- the art

def build():
    C = Canvas()

    # ---- 1. THE GLOW FOOTPRINT (the win banner's, in violet / magenta) -------------------------
    C.glow(cov('<rect x="70" y="70" width="1908" height="400" rx="200" fill="#fff"/>'), VIOLET, 60.0, 0.16)
    C.glow(cov('<rect x="160" y="132" width="1728" height="250" rx="125" fill="#fff"/>'), MAGENTA, 42.0, 0.24)
    C.glow(cov(circ(207, 256, 62) + circ(1840, 256, 62)), MAGENTA, 38.0, 0.42)
    C.glow(cov('<ellipse cx="1024" cy="64" rx="46" ry="34" fill="#fff"/>'), VIOLET, 20.0, 0.30)   # the light that went out

    # ---- 2. EMBERS falling where the gold sparkles were ---------------------------------------
    embers = [(318, 118, 3.0, 0.75, MAGENTA), (402, 62, 2.4, 0.5, VIOLET), (590, 142, 2.6, 0.6, MAGENTA),
              (690, 92, 2.0, 0.45, VIOLET), (1352, 128, 2.8, 0.7, MAGENTA), (1470, 70, 2.2, 0.5, VIOLET),
              (1700, 112, 3.0, 0.75, MAGENTA), (1790, 152, 2.2, 0.5, VIOLET), (146, 300, 2.4, 0.5, VIOLET),
              (1908, 232, 2.4, 0.55, MAGENTA), (430, 492, 2.0, 0.4, VIOLET), (1632, 494, 2.2, 0.45, MAGENTA),
              (868, 40, 2.0, 0.4, MAGENTA), (1206, 34, 2.0, 0.4, VIOLET)]
    for x, y, r, k, col in embers:
        trail = cov('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="url(#t)" stroke-width="%.1f" stroke-linecap="round"/>'
                    % (x, y - 22, x, y - 2, r * 0.9),
                    '<linearGradient id="t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                    '<stop offset="1" stop-color="#fff" stop-opacity="0.8"/></linearGradient>')
        C.paint(trail, col, k * 0.6)
        dot = cov(circ(x, y, r))
        C.glow(dot, col, 4.0, 1.2 * k)
        C.paint(dot, CORE, k)

    # ---- 3. THE DEAD GRID ---------------------------------------------------------------------
    # The dark floor the dead grid lies on. It FADES OUT toward the last rung and its sides are soft
    # (review 2026-10-04: a hard-edged fill drew a straight dark band across the whole screen at the
    # banner's foot, the one line in the art that read as "an image ended here").
    floor_fade = np.clip(1.0 - (np.arange(H)[:, None] - 340) / 150.0, 0.0, 1.0) * np.ones((1, W))
    floor_fade = floor_fade * floor_fade * (3.0 - 2.0 * floor_fade)            # smoothstep
    floor_fill = blur(cov(poly([(250, 340), (1797, 340), (1872, 478), (175, 478)])), 10.0)
    C.paint(floor_fill * floor_fade, PLATE, 0.50)
    C.paint(blur(cov(poly([(530, 336), (1517, 336), (1743, 472), (304, 472)])), 6.0) * floor_fade, PANEL, 0.42)

    gx0, gy0, gx1, gy1 = GRID_CLEAR
    clear = 1.0 - box_mask(gx0, gy0, gx1, gy1)

    def mirror(x):
        return 2047 - x

    # rung segments (gaps = the breaks); rung 2's right end is SNAPPED and hangs
    breaks = {0: [(700, 760), (1310, 1352)], 1: [(1180, 1262)], 2: [(1626, 1648)], 3: [(520, 602), (1446, 1478)],
              4: [(860, 902), (1276, 1330)]}
    rungs, rings, chain = [], [], []
    for i, (y, xl) in enumerate(zip(GRID_Y, GRID_XL)):
        xr = mirror(xl)
        segs = [(xl + 9, xr - 9)]
        for b0, b1 in breaks.get(i, []):
            nxt = []
            for s0, s1 in segs:
                if b1 <= s0 or b0 >= s1:
                    nxt.append((s0, s1))
                else:
                    if b0 > s0:
                        nxt.append((s0, b0))
                    if b1 < s1:
                        nxt.append((b1, s1))
            segs = nxt
        if i == 2:
            segs = [s for s in segs if s[1] <= 1626]
            rungs.append(pline([(1648, y + 1), (xr - 6, y + 13)], 3.0, cap='butt'))   # the snapped piece, sagging
            rings.append((xr, y + 14))
        else:
            rings.append((xr, y))
        rings.append((xl, y))
        for s0, s1 in segs:
            rungs.append(pline([(s0, y), (s1, y)], 3.0, cap='butt'))
    for side in (0, 1):
        pr = [r for j, r in enumerate(rings) if j % 2 == (1 if side == 0 else 0)]
        for a_, b_ in zip(pr[:-1], pr[1:]):
            chain.append(pline([a_, b_], 2.0))
    rung_c = cov(''.join(rungs)) * clear
    chain_c = cov(''.join(chain))
    diag_c = cov(''.join(pline([a_, b_], 3.0, cap='butt') for a_, b_ in DIAG))
    ring_c = cov(''.join(circ(x, y, 8.5, stroke=3.0) for x, y in rings))
    C.paint(chain_c, STEEL, 0.8)
    C.paint(diag_c, STEEL, 0.9)
    C.paint(rung_c, STEEL, 0.9)
    C.paint(ring_c, STEEL, 1.0)
    # a last flicker of power on the rails nearest the plate (they fade out as they fall away)
    near = np.clip(1.0 - (np.arange(H)[:, None] - 336) / 60.0, 0.0, 1.0) * np.ones((1, W))
    C.paint(diag_c * near, MAGENTA, 0.55)
    # three nodes still smoulder; the rest are dead rings
    for x, y, col in [(402, 438, MAGENTA), (1612, 471, MAGENTA), (1470, 375, CYAN), (612, 352, VIOLET)]:
        d = cov(circ(x, y, 4.2))
        C.glow(d, col, 6.0, 1.0)
        C.paint(d, col, 1.0)
        C.paint(cov(circ(x, y, 1.6)), CORE, 0.9)

    # ---- 4. THE FLOOR READOUT, hung from the plate --------------------------------------------
    rx0, ry0, rx1, ry1 = READOUT
    ch = READOUT_CHAMFER
    rshape = [(rx0 + ch, ry0), (rx1, ry0), (rx1, ry1 - ch), (rx1 - ch, ry1), (rx0, ry1), (rx0, ry0 + ch)]
    struts = cov(pline([(868, 334), (868, ry0 + 2)], 4.0, cap='butt') + pline([(1180, 334), (1180, ry0 + 2)], 4.0, cap='butt'))
    C.paint(struts, STEEL, 1.0)
    bolts = cov(circ(868, 346, 3.2) + circ(1180, 346, 3.2) + circ(868, ry0 - 6, 3.2) + circ(1180, ry0 - 6, 3.2))
    C.paint(bolts, CYAN, 0.8)
    rfill = cov(poly(rshape))
    C.paint(rfill, vgrad(ry0, ry1, HEADER, PLATE), 0.97)
    scan = np.zeros((H, W))
    scan[ry0 + 3:ry1 - 2:5, :] = 1.0
    C.paint(rfill * scan, _c('go_scan'), 0.25)
    rtube = cov(pline(rshape, 3.6, closed=True))
    C.glow(rtube, CYAN, 7.0, 0.75)
    C.paint(rtube, CYAN, 1.0)
    C.paint(cov(pline(rshape, 1.2, closed=True)), CYAN_CORE, 0.85)
    ticks = []
    for x, d in ((rx0 + 22, 1), (rx1 - 22, -1)):
        ticks.append(pline([(x + 8 * d, ry0 + 14), (x, ry0 + 14), (x, ry1 - 14), (x + 8 * d, ry1 - 14)], 2.0, cap='butt', join='miter'))
    C.paint(cov(''.join(ticks)), CYAN, 0.45)

    # ---- 5. THE BROKEN STAIR ------------------------------------------------------------------
    lx, rxx = stair_x(112)
    jag = [(lx, 112), (952, 103), (973, 118), (996, 98), (1019, 113), (1041, 95), (1064, 110), (1086, 99), (stair_x(104)[1], 104)]
    body = [(STAIR_L, STAIR_BASE_Y)] + jag + [(STAIR_R, STAIR_BASE_Y)]
    sb = cov(poly(body))
    C.glow(sb, MAGENTA, 16.0, 0.22)
    C.paint(sb, vgrad(96, 177, _c('go_stair_hi'), _c('go_stair_lo')), 0.95)
    # perspective steps, denser toward the (missing) top; mostly dead, the bottom two still faintly lit
    steps = [168, 158, 147, 137, 128, 120]
    step_c = []
    for y in steps:
        l, r = stair_x(y)
        top_jag = 0
        step_c.append((y, pline([(l + 5, y), (r - 5, y)], 2.4, cap='butt')))
    allsteps = cov(''.join(s for _, s in step_c)) * cov(poly(body))
    C.paint(allsteps, STEEL, 0.9)
    lit = cov(pline([(stair_x(168)[0] + 5, 168), (1000, 168)], 2.4, cap='butt') +
              pline([(1046, 158), (stair_x(158)[1] - 5, 158)], 2.4, cap='butt'))
    C.paint(lit, MAGENTA, 0.6)
    edges = cov(pline([(STAIR_L, STAIR_BASE_Y), jag[0]], 4.0) + pline([(STAIR_R, STAIR_BASE_Y), jag[-1]], 4.0))
    C.paint(edges, STEEL, 1.0)
    fade = np.clip((np.arange(H)[:, None] - 120.0) / 57.0, 0.0, 1.0) * np.ones((1, W))
    C.glow(edges * fade, MAGENTA, 6.0, 0.8)
    C.paint(edges * fade, MAGENTA, 0.85)
    C.paint(cov(pline(jag, 2.2)), LAVENDER, 0.55)                       # the raw break edge

    # the pieces that broke off: tilted chunks of the stair's top, falling, with trails
    shards = [
        ([(1024, 55), (1004, 88), (1046, 88)], 24, (30, 8)),               # the apex tip
        ([(stair_x(96)[0], 96), (972, 96), (962, 112), (stair_x(112)[0], 112)], -18, (-30, -6)),
        ([(990, 90), (1030, 84), (1036, 100), (994, 104)], 9, (-8, -20)),
        ([(1060, 88), (stair_x(88)[1], 88), (stair_x(102)[1], 102), (1070, 104)], 31, (34, -2)),
    ]
    shard_body, shard_edge, shard_trail = [], [], []
    for p, deg, (dx, dy) in shards:
        cx = sum(x for x, _ in p) / len(p)
        cy = sum(y for _, y in p) / len(p)
        q = [(x + dx, y + dy) for x, y in rot(p, deg, cx, cy)]
        shard_body.append(poly(q))
        shard_edge.append(pline(q, 2.6, closed=True))
        qx = sum(x for x, _ in q) / len(q)
        qy = min(y for _, y in q)
        shard_trail.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="url(#t)" stroke-width="3" stroke-linecap="round"/>'
                           % (qx - 6, qy - 26, qx - 6, qy - 4))
        shard_trail.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="url(#t)" stroke-width="2" stroke-linecap="round"/>'
                           % (qx + 7, qy - 18, qx + 7, qy - 3))
    grad = ('<linearGradient id="t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#fff" stop-opacity="0.7"/></linearGradient>')
    C.paint(cov(''.join(shard_trail), grad), VIOLET, 0.45)
    C.paint(cov(''.join(shard_body)), _c('go_shard'), 0.96)
    C.paint(cov(''.join(shard_edge)), STEEL, 1.0)
    debris = [(978, 74, 4, 20), (1094, 66, 3, -35), (946, 120, 3, 12), (1112, 118, 4, 50), (1012, 40, 3, 0)]
    dc = cov(''.join(poly(rot([(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)], d, x, y)) for x, y, s, d in debris))
    C.paint(dc, STEEL, 0.9)
    sparks = cov(circ(lx + 2, 111, 2.4) + circ(1041, 96, 2.2) + circ(stair_x(104)[1] - 2, 104, 2.4))
    C.glow(sparks, MAGENTA, 5.0, 1.4)
    C.paint(sparks, CORE, 1.0)

    # ---- 6. THE PLATE -------------------------------------------------------------------------
    tube = cov(pline(PLATE_HEX, 8.0, closed=True, join='miter'))
    core = cov(pline(PLATE_HEX, 2.6, closed=True, join='miter'))
    dead = box_mask(DEAD_TOP[0], 160, DEAD_TOP[1], 196)
    gap = box_mask(GAP_TOP[0], 160, GAP_TOP[1], 196)
    dim = box_mask(DIM_BOTTOM[0], 318, DIM_BOTTOM[1], 352)
    litk = (1.0 - dead) * (1.0 - dim) + dim * DIM_K
    tube_lit = tube * (1.0 - gap) * litk
    tube_dead = tube * (1.0 - gap) * dead
    C.glow(tube_lit, MAGENTA, 26.0, 0.55)
    C.glow(tube_lit, MAGENTA, 10.0, 0.95)

    plate = cov(poly(PLATE_HEX))
    C.paint(plate, vgrad(177, 335, _c('go_plate_top'), PLATE), 0.965)
    scan = np.zeros((H, W))
    scan[181:332:6, :] = 1.0
    C.paint(plate * scan, _c('go_plate_scan'), 0.22)
    sheen = cov(poly([(262, 183), (1786, 183), (1806, 214), (238, 214)]))
    C.paint(sheen * np.clip(1.0 - (np.arange(H)[:, None] - 183) / 31.0, 0.0, 1.0), _c('go_sheen'), 0.10)

    # the inner cyan rules (the top one broken where the crack crosses it)
    rules = cov(pline([(300, RULE_Y[0]), (1582, RULE_Y[0])], 2.2, cap='butt') +
                pline([(1612, RULE_Y[0]), (1748, RULE_Y[0])], 2.2, cap='butt') +
                pline([(300, RULE_Y[1]), (1748, RULE_Y[1])], 2.2, cap='butt'))
    C.glow(rules, CYAN, 3.0, 0.5)
    C.paint(rules, CYAN, 0.7)

    # the crack, from the snapped tube down the glass
    crack = [[(1578, 182), (1596, 204), (1588, 228), (1614, 252), (1606, 284), (1631, 316)],
             [(1596, 204), (1632, 214), (1676, 206), (1702, 214)],
             [(1614, 252), (1650, 262), (1668, 280)]]
    cc = cov(''.join(pline(c, 1.7) for c in crack))
    ccs = cov(''.join(pline([(x + 1.5, y + 1.5) for x, y in c], 1.7) for c in crack))
    C.paint(ccs, _c('go_crack_shadow'), 0.7)
    C.paint(cc, LAVENDER, 0.42)

    # flank marks: a cyan lead-in line to three magenta chevrons pointing at the title
    lay_x0, lay_x1 = title_extent()
    flank = []
    chev = []
    for side in (-1, 1):
        inner = (lay_x0 - 44) if side < 0 else (lay_x1 + 44)
        outer = 292 if side < 0 else 1755
        cx_last = inner
        for k in range(3):
            x = inner + side * k * 26
            chev.append((k, pline([(x + side * 14, 244), (x, 256), (x + side * 14, 268)], 4.0, cap='round', join='miter')))
            cx_last = x
        flank.append(pline([(outer, 256), (cx_last + side * 34, 256)], 2.0, cap='butt'))
    C.paint(cov(''.join(flank)), CYAN, 0.38)
    for k in range(3):
        c = cov(''.join(s for kk, s in chev if kk == k))
        C.glow(c, MAGENTA, 4.0, 0.8 * (1.0 - 0.3 * k))
        C.paint(c, MAGENTA, 0.95 - 0.28 * k)

    # ---- 7. THE TUBE --------------------------------------------------------------------------
    C.paint(tube_dead, STEEL, 1.0)
    C.paint(cov(pline(PLATE_HEX, 2.0, closed=True, join='miter')) * dead * (1.0 - gap), _c('go_seam'), 0.9)  # unlit glass seam
    C.paint(tube_lit, MAGENTA, 1.0)
    C.paint(core * (1.0 - gap) * litk, CORE, 0.95)
    ends = cov(circ(GAP_TOP[0] - 1, 177, 4.2) + circ(GAP_TOP[1] + 1, 177, 4.2))
    C.paint(ends, _c('go_ends'), 1.0)                                   # the snapped, burnt tube ends

    # ---- 8. THE TITLE -------------------------------------------------------------------------
    neon_title(C, TITLE)

    # ---- 9. the live wire: cyan sparks falling from the break --------------------------------
    sp = [(1571, 186, 2.6), (1580, 199, 2.2), (1568, 214, 1.8), (1584, 228, 1.5), (1575, 172, 2.0)]
    spark = cov(''.join(circ(x, y, r) for x, y, r in sp))
    streak = cov(''.join('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="url(#t)" stroke-width="%.1f" stroke-linecap="round"/>'
                         % (x, y - 12, x, y - 1, r * 0.9) for x, y, r in sp), grad)
    C.paint(streak, SPARK, 0.5)
    C.glow(spark, SPARK, 4.0, 1.3)
    C.paint(spark, _c('go_spark_core'), 1.0)

    # ---- 10. THE EDGE WINDOW: alpha is exactly 0 on every border, like the win banner's ---------
    # The image is clampU/V 0 (wrap) in the GDT, so a glow that touches one edge is sampled onto the
    # opposite edge by the filter, and on screen a glow cut by the image bounds draws a faint
    # rectangle. The win banner's own alpha starts at x 51 / y 11 and ends at x 1996 / y 496.
    C.window(edge_window())

    return C.image()


def _ramp(n, z0, z1):
    """0 below z0, smoothstep up to 1 at z1 (indices 0..n-1)."""
    t = np.clip((np.arange(n, dtype=np.float64) - z0) / float(z1 - z0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def edge_window():
    x0, x1 = EDGE_X
    y0, y1 = EDGE_Y
    wx = _ramp(W, x0, x1) * _ramp(W, x0, x1)[::-1]
    wy = _ramp(H, y0, y1) * _ramp(H, y0, y1)[::-1]
    return wy[:, None] * wx[None, :]


_EXTENT = None


def title_extent():
    """x0, x1 of the title's advance box (same arithmetic as title_layer, no drawing)."""
    global _EXTENT
    if _EXTENT is None:
        M = artgen.metrics()
        S = M['letters']
        s = TITLE_CAP / S['cap']
        total = 0.0
        for c in TITLE:
            if c == ' ':
                total += S['cw'] * s * artgen.TOD_SPACE_ADV
            else:
                sname, key, _ = artgen._glyph(c)
                total += M[sname]['g'][key][0] * (TITLE_CAP / M[sname]['cap'])
        total += TITLE_CAP * (artgen.TOD_TRACK + TITLE_TRACK) * (len(TITLE) - 1)
        _EXTENT = (W / 2.0 - total / 2.0, W / 2.0 + total / 2.0)
    return _EXTENT

# ------------------------------------------------------------------------------- review + on-screen

GSC_FONT = 'C:/Windows/Fonts/bahnschrift.ttf'      # an APPROXIMATION of the stock hudelem font


def _font(px):
    for f in (GSC_FONT, 'C:/Windows/Fonts/arialbd.ttf'):
        try:
            return ImageFont.truetype(f, px)
        except Exception:
            pass
    return ImageFont.load_default()


def onscreen(banner, floor_text='FLOOR 23', survived_text='YOU SURVIVED 17 ROUNDS', view=(1920, 1080), split=False):
    """The loss screen as lost_game_over lays it out, on a 1280x720 virtual canvas scaled to `view`.
    Banner 900x225 at y -130 (600x150 at -90 in splitscreen); the readout text at
    y + TOD_GO_READOUT_FRAC x banner height; the survived line at +40 (+80 split). The two text lines are
    drawn in an approximation of the stock hudelem font (fontScale 2 ~ a 24-unit line)."""
    vw, vh = view
    k = vh / 720.0
    bg_path = os.path.join(artgen.ROOT, 'docs', '184_synthwave_ref', 'world_city_ingame.png')
    if os.path.isfile(bg_path):
        bg = Image.open(bg_path).convert('RGBA')
        sc = max(vw / bg.width, vh / bg.height)
        bg = bg.resize((int(bg.width * sc + 1), int(bg.height * sc + 1)), Image.LANCZOS)
        bg = bg.crop(((bg.width - vw) // 2, (bg.height - vh) // 2, (bg.width - vw) // 2 + vw, (bg.height - vh) // 2 + vh))
        dark = Image.new('RGBA', bg.size, (0, 0, 0, 120))
        bg.alpha_composite(dark)
    else:
        bg = Image.new('RGBA', view, (14, 10, 24, 255))
    bw, bh, y = (600, 150, -90) if split else (900, 225, -130)
    im = banner.resize((int(round(bw * k)), int(round(bh * k))), Image.LANCZOS)
    cy = vh / 2.0 + y * k
    bg.alpha_composite(im, (int(round(vw / 2.0 - im.width / 2.0)), int(round(cy - im.height / 2.0))))
    d = ImageDraw.Draw(bg)
    fs = 1.5 if split else 2.0
    f = _font(int(round(12 * fs * k * 0.92)))
    ry = cy + (READOUT_CY - 256) / 512.0 * bh * k
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((vw / 2.0 + dx, ry + dy), floor_text, font=f, fill=(31, 229, 255, 70), anchor='mm')
    d.text((vw / 2.0, ry), floor_text, font=f, fill=(219, 247, 255, 255), anchor='mm')
    sy = vh / 2.0 + (80 if split else 40) * k
    d.text((vw / 2.0, sy), survived_text, font=f, fill=(184, 174, 216, 255), anchor='mm')
    return bg


def review(img, out_dir):
    # W2E (2026-10-05): the win banner retired with the Map One ending; the review keeps it as the chassis reference,
    # read from the archive (the --check path never calls review).
    wp = artgen.shipped('i_tod_win_banner')
    if not os.path.isfile(wp):
        wp = os.path.join(artgen.ROOT, 'archive', 'map1_carryover', os.path.relpath(wp, artgen.ROOT))
    win = Image.open(wp).convert('RGBA')
    shot = onscreen(img)
    shot.save(os.path.join(out_dir, '_onscreen_1080p.png'))
    shot2 = onscreen(img, floor_text='UNDERCITY', survived_text='YOU SURVIVED 31 ROUNDS', view=(1280, 720))
    shot2.save(os.path.join(out_dir, '_onscreen_720p_undercity.png'))
    split = onscreen(img, floor_text='THE CROWN', survived_text='YOU SURVIVED 6 ROUNDS', view=(1920, 540), split=True)
    split.save(os.path.join(out_dir, '_onscreen_splitscreen.png'))
    rows = [
        ('SHIPPED REFERENCE  i_tod_win_banner (the chassis: plate, stair, grid, glow footprint)', [win]),
        ('NEW  i_tod_lose_banner  (synthwave: magenta tube, cyan rules, no red; dead stair + grid; GAME OVER in the map typeface)', [img]),
    ]
    sheets = []
    for label, items in rows:
        p = os.path.join(out_dir, '_row.png')
        artgen.contact_sheet([(label, items)], p, height=300)
        sheets.append(Image.open(p).convert('RGBA'))
        os.remove(p)
    p = os.path.join(out_dir, '_row.png')
    artgen.contact_sheet([('ON SCREEN 1080p as lost_game_over draws it (FLOOR line + survived line = stock-font APPROXIMATION)', [shot])], p, height=600)
    sheets.append(Image.open(p).convert('RGBA'))
    os.remove(p)
    artgen.contact_sheet([('720p, the Undercity case  |  splitscreen (600x150), a wipe in the crown hall', [shot2, split])], p, height=300)
    sheets.append(Image.open(p).convert('RGBA'))
    os.remove(p)
    Wd = max(s.width for s in sheets)
    out = Image.new('RGBA', (Wd, sum(s.height for s in sheets)), (28, 30, 38, 255))
    y = 0
    for s in sheets:
        out.alpha_composite(s, (0, y))
        y += s.height
    p = os.path.join(out_dir, '_review.png')
    out.save(p)
    return p

# ------------------------------------------------------------------------------------- the wiring

# THE CODE HALF (RT 2026-10-05): the floor readout and the survived line are live hudelem text laid on this banner, so
# their colours follow the THEME too. LOCKSTEP _tod_gameover.gsc: this theme's lines present, the other theme's absent.
GSC_TINTS = {
    'fallen': ['readout.color = ( 0.94, 0.95, 0.98 );', 'readout.glowColor = ( 0.95, 0.13, 0.23 );',
               'survived.color = ( 0.52, 0.56, 0.67 );'],
    'synthwave': ['readout.color = ( 0.86, 0.97, 1.0 );', 'readout.glowColor = ( 0.12, 0.90, 1.0 );',
                  'survived.color = ( 0.72, 0.68, 0.85 );'],
}


def _gsc_tints(gsc, theme):
    out = ['GSC: %s lacks the %s colour line %s' % (GSC_REL, theme, l) for l in GSC_TINTS[theme] if l not in gsc]
    for other, lines in GSC_TINTS.items():
        if other != theme:
            out += ['GSC: %s still carries the %s colour line %s' % (GSC_REL, other, l) for l in lines if l in gsc]
    return out


def gsc_tint_problems(gsc, theme=None):
    theme = theme or _sw.THEME
    out = _gsc_tints(gsc, theme)
    if not out:      # the negative control: each of the other theme's lines planted in place must be caught
        other = [t for t in GSC_TINTS if t != theme][0]
        for a, b in zip(GSC_TINTS[theme], GSC_TINTS[other]):
            if not _gsc_tints(gsc.replace(a, b), theme):
                out.append('GSC tint gate blind: the %s line %s planted was not caught' % (other, b))
    return out


def check_wiring(root):
    """The lane this art lives in, end to end: GDT image + material, zone lines, precache, SetShader,
    and the READOUT lockstep. Returns a list of problems."""
    bad = []
    try:
        gdt = open(os.path.join(root, GDT_REL), encoding='utf-8', errors='replace').read()
    except OSError:
        gdt = ''
    if not re.search(r'"%s" \( "image\.gdf" \)\s*\{[^}]*"baseImage" "source_data/tod_ui_images/_images/%s\.png"[^}]*'
                     r'"compressionMethod" "compressed high color"' % (NAME, NAME), gdt):
        bad.append('GDT: no "%s" image block (baseImage %s.png, compressed high color) in %s' % (NAME, NAME, GDT_REL))
    m = re.search(r'"%s" \( "material\.gdf" \)\s*\{(.*?)\n\t\}' % MATERIAL, gdt, re.S)
    if not m:
        bad.append('GDT: no "%s" material block in %s' % (MATERIAL, GDT_REL))
    else:
        blk = m.group(1)
        if '"colorMap" "%s"' % NAME not in blk:
            bad.append('GDT: material %s does not wrap colorMap %s' % (MATERIAL, NAME))
        if '"materialType" "2d_blend"' not in blk:
            bad.append('GDT: material %s is not 2d_blend' % MATERIAL)
    try:
        zone = open(os.path.join(root, ZONE_REL), encoding='utf-8', errors='replace').read().splitlines()
    except OSError:
        zone = []
    for want in ('image,' + NAME, 'material,' + MATERIAL):
        if want not in zone:
            bad.append('zone: no "%s" line in %s' % (want, ZONE_REL))
    try:
        gsc = open(os.path.join(root, GSC_REL), encoding='utf-8', errors='replace').read()
    except OSError:
        gsc = ''
    if not re.search(r'#precache\(\s*"material",\s*"%s"\s*\)' % MATERIAL, gsc):
        bad.append('GSC: no #precache( "material", "%s" ) in %s' % (MATERIAL, GSC_REL))
    if not re.search(r'SetShader\(\s*"%s"' % MATERIAL, gsc):
        bad.append('GSC: %s never SetShader()s "%s"' % (GSC_REL, MATERIAL))
    m = re.search(r'#define\s+TOD_GO_READOUT_FRAC\s+([0-9.]+)', gsc)
    want = (READOUT_CY - 256) / 512.0
    if not m:
        bad.append('GSC: no TOD_GO_READOUT_FRAC define in %s (LOCKSTEP READOUT_CY)' % GSC_REL)
    elif abs(float(m.group(1)) - want) > 1e-9:
        bad.append('GSC: TOD_GO_READOUT_FRAC %s != (READOUT_CY %d - 256) / 512 = %.8f - the live floor text would miss the baked readout'
                   % (m.group(1), READOUT_CY, want))
    for tag in ('', '_SPLIT'):
        mw = re.search(r'#define\s+TOD_GO_BANNER%s_W\s+(\d+)' % tag, gsc)
        mh = re.search(r'#define\s+TOD_GO_BANNER%s_H\s+(\d+)' % tag, gsc)
        if not (mw and mh) or int(mw.group(1)) * H != int(mh.group(1)) * W:
            bad.append('GSC: TOD_GO_BANNER%s_W / _H missing or not the art\'s 4:1 aspect (%dx%d)' % (tag, W, H))
    # the live floor text must be placed BY the lockstep fraction, not by a copied number
    if not re.search(r'TOD_GO_READOUT_FRAC\s*\*', gsc):
        bad.append('GSC: %s never places the floor readout with TOD_GO_READOUT_FRAC' % GSC_REL)
    bad += gsc_tint_problems(gsc)
    return bad

# ------------------------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--install', action='store_true', help='copy into source_data/tod_ui_images/_images/')
    ap.add_argument('--stage', help='also write the PNG under DIR/source_data/tod_ui_images/_images/')
    ap.add_argument('--check', action='store_true', help='fail on any byte that differs from the installed PNG, or a break in the wiring')
    ap.add_argument('--root', help='with --check: read DIR/... instead of the repo')
    a = ap.parse_args()

    img = build()
    if a.check:
        root = a.root or artgen.ROOT
        p = os.path.join(root, IMG_REL, NAME + '.png')
        bad = []
        if not os.path.isfile(p):
            bad.append('MISSING %s' % p)
        elif open(p, 'rb').read() != artgen.png_bytes(img):
            bad.append('STALE %s (re-run the generator; never hand-edit it)' % p)
        bad += check_wiring(root)
        if bad:
            for b in bad:
                print('PK09 LOSS BANNER: ' + b)
            sys.exit(1)
        print('PK09 LOSS BANNER OK (%s, GDT + zone + precache + SetShader + readout lockstep)' % NAME)
        return

    out_dir = artgen.stage_dir(PACK)
    md5 = artgen.save_png(img, os.path.join(out_dir, NAME + '.png'))
    print('%-24s %s' % (NAME, md5))
    for root in ([a.stage] if a.stage else []) + ([artgen.ROOT] if a.install else []):
        artgen.save_png(img, os.path.join(root, IMG_REL, NAME + '.png'))
    print('review ->', review(img, out_dir))


if __name__ == '__main__':
    main()
