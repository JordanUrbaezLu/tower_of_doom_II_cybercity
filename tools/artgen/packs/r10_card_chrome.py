"""r10_card_chrome.py - THE CARD CHROME AND THE REEL'S RARITY IN THE SYNTHWAVE LIBRARY (2026-10-05, wave 3, R10).

User 2026-10-05: "Whole entire asset library should look like one library." The W3F audit (tmp/wave3/W3F-library-audit,
findings F03 + F06) found the two families that still spoke collectible-card-game metal while every other Map 2
surface speaks the R3/R4 synthwave language (tools/artgen/synthwave.py, packs/r3_synthwave_system.py,
packs/r4_synthwave_hud.py: chamfered black-glass plates, ONE neon tube in a hue, white-hot glyphs with one hue accent,
a soft halo, our typeface):

  F03  the layered upgrade card (THE PULL, every card deal): polished silver / blue / violet / gold rims, a GLOSSY
       BRIGHT header pill, baroque filigree and a winged crown, glossy 3D gem crests, a soft-rendered grey back.
  F06  the Black Market reel: gold baroque scrolls on the LEGENDARY tile (and so on the CURSED tile cut from it),
       lightning squiggles on the EPIC tile and wisps on the EPIC stamp.

RARITY IS ESCALATED WITH LIGHT, NEVER ORNAMENT (one rule for both families):
  COMMON     one tube                                        (white / silver)
  RARE       + bracket corners (the second tube at the four corners only)      (blue)
  EPIC       a double tube all the way round + a few sparks                    (violet)
  LEGENDARY  double tube + brackets + a neon crown + embers + a stronger halo  (gold)
The hues are tod_upgrade.lua RARITY[].col to the byte (the game tints the glow, the ladder and the band ground with
them); --check re-reads them and fails if they drift.

WHAT THIS DRAWS (same names, same sizes: a drop-in, no GDT / zone / Lua wiring):
  i_tod_card2_body                 768 x 1152  the chamfered dark-glass card plate: the window hole, the octagon crest
                                               socket, the band slot, the text panel, the pip tray (rarity-neutral)
  i_tod_card2_frame_<rarity> x 4   768 x 1152  the bezel + rim tube(s), the dark-glass header with its label well, the
                                               window tube round the socket, the band ring, the rarity's light
  i_tod_card2_crest_<rarity> x 4   144 x 144   white-hot neon tokens: round gem / diamond / star / crown
  i_tod_card2_back                 768 x 1152  the spire as neon line-art on black glass, NEUTRAL (the game glows it in
                                               the rung's colour), TOWER OF DOOM II in our typeface
  i_tod_spin_tile_epic             560 x 416   the shipped tile, its two lightning squiggles taken out, sparks added
  i_tod_spin_tile_legendary        560 x 416   the shipped tile, its four gold scrolls taken out, bracket corners,
                                               the stamp's diamond studs beside the word, embers
  i_tod_spin_banner_epic           1600 x 208  the shipped stamp, its side wisps taken out, sparks on its ends
The two reel tiles and the stamp are cut from the PREVIOUS SHIPPED art, parked read-only in docs/217_ref/_prev_shipped/
(the generator's only inputs besides the library), so --check regenerates them byte-exact after the landing.
i_tod_spin_tile_cursed is NOT drawn here: tools/dealer_house/make_spin_art.py derives it from the legendary tile (its
own gate), so the landing re-runs that script. The legendary stamp has no ornament (its glints are light already) and
is unchanged, so the CURSED stamp and THE DEALER'S GIFT art (tools/partner_shop/make_gift_art.py) are untouched.

GEOMETRY IS NOT TASTE. Every opening keeps the shipped position and size (docs/191 layout, TodPull.lua V2 x 768/234):
the art window hole (96,176)-(672,624), the crest socket centred (640,576) holding the 144 crest, the band slot
(168,656)-(600,724) inside its ring, the title label (80.4,50.9)-(687.6,129.6), the text panel and the pip tray.
--check measures the generated openings against the PARKED shipped frames/body and fails on a drift > OPEN_TOL px.
The title label and the rarity band are LUI quads of i_tod_pull_pill tinted rarity x 0.34 under white text; the pill
is chamfered TL / BR in the staged tools/card_pull/install_card_art.py (fx_pill), and the frame's label well carries
the SAME chamfer (LOCKSTEP: PILL_CUT_* below, checked against the installed pill).

  python tools/artgen/packs/r10_card_chrome.py                      # -> art/generated/R10-card-chrome/ + _review*.png
  python tools/artgen/packs/r10_card_chrome.py --stage DIR          # + DIR/source_data/tod_ui_images/_images/
  python tools/artgen/packs/r10_card_chrome.py --install            # LANDING ONLY: write into source_data/.../_images
  python tools/artgen/packs/r10_card_chrome.py --check [--root DIR] # regenerate in memory: fail on any byte != DIR's
                                                                    # files, a moved opening, a drifted hue, an unwired
                                                                    # name or a pill whose chamfer left the well's
  python tools/artgen/packs/r10_card_chrome.py --selftest           # negative controls: a shifted frame, the rounded
                                                                    # pill, a tinted back, the bright plates - all caught

Deterministic: seeded rng only, no timestamps. Never hand-edit a generated PNG.
"""
import argparse, hashlib, importlib.util, io, math, os, re, sys


def _repo():
    """the repo root: the nearest parent holding the library (works from tools/artgen/packs and from a stage tree)"""
    p = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isfile(os.path.join(p, 'tools', 'artgen', 'synthwave.py')) and \
                os.path.isfile(os.path.join(p, 'tools', 'artgen', 'packs', 'r4_synthwave_hud.py')):
            return p
        up = os.path.dirname(p)
        if up == p:
            raise SystemExit('r10: cannot find the repo (tools/artgen/synthwave.py) above %s' % __file__)
        p = up


REPO = _repo()
sys.path.insert(0, os.path.join(REPO, 'tools', 'artgen'))
import artgen  # noqa: E402
from synthwave import (PAL, LOOK, THEME, Svg, chamfer, poly_d, line_d, inset, mix, hexs, hexrgb, put_text, text_width,  # noqa: E402
                       grain, scratches, embers, glow_of, _paste, clip_to)
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
from scipy import ndimage, sparse  # noqa: E402
from scipy.sparse.linalg import spsolve  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, 'tools', 'artgen', 'packs', name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


r4 = _load('r4_synthwave_hud')      # the library: neon_glyph, coverage, layered, bevel, sparkle, octagon

PACK = 'R10-card-chrome'
IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')
OUT = os.path.join(REPO, 'art', 'generated', PACK)
PARK_REL = os.path.join('docs', '217_ref', '_prev_shipped')
UPG_LUA = os.path.join('ui', 'uieditor', 'menus', 'hud', 'tod_upgrade.lua')
PULL_LUA = os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodPull.lua')

W, H = 768, 1152
RARITIES = ['common', 'rare', 'epic', 'legendary']
# tod_upgrade.lua RARITY[r].col (LOCKSTEP - --check re-reads the Lua): the tube hues
RARITY_COL = {'common': (0.914, 0.933, 0.961), 'rare': (0.227, 0.659, 1.0), 'epic': (0.710, 0.361, 1.0),
              'legendary': (1.0, 0.761, 0.239)}


def _hex(c):
    return '#%02X%02X%02X' % tuple(int(round(v * 255)) for v in c)


HUE = {r: _hex(c) for r, c in RARITY_COL.items()}
CORE = {r: mix(HUE[r], '#FFFFFF', 0.78) for r in RARITIES}
NEUTRAL_TUBE = '#E9ECF2'           # the back's light (the game tints it per rung)

# ===================================================================================== the card geometry
CUT_BIG, CUT_SMALL = 60, 24
OUTLINE = chamfer(0, 0, W, H, tl=CUT_BIG, tr=CUT_SMALL, br=CUT_BIG, bl=CUT_SMALL)   # body, frames, back: ONE silhouette
BEZEL_W = 28
BEZEL_IN = inset(OUTLINE, BEZEL_W)
RIM = inset(OUTLINE, 11.0)          # the rim tube's centre line
RIM_W = 6.0
RIM2 = inset(OUTLINE, 21.0)         # the second tube (EPIC / LEGENDARY all round, RARE at the corners = the brackets)
RIM2_W = 3.2
BRACKET_LEG = 84.0

# the title: TodPull V2.titleLabel {24.5, 15.5, 209.5, 39.5} x 768/234 -> the LUI label quad; the frame's well is that
# quad with the pill's chamfer (PILL_CUT canvas px at the label's size), the plate round it parallel at 17.5 px
CARD_K = 768.0 / 234.0
LABEL = (24.5 * CARD_K, 15.5 * CARD_K, 209.5 * CARD_K, 39.5 * CARD_K)          # (80.4, 50.9, 687.6, 129.6)
PILL_CUT = 22.0
LABEL_WELL = chamfer(LABEL[0], LABEL[1], LABEL[2], LABEL[3], tl=PILL_CUT, br=PILL_CUT)
HEADER = chamfer(62, 34, 706, 148, tl=32, br=32)
# the pill sprite (install_card_art.py fx_pill, 432 x 68) cut so the LABEL quad shows PILL_CUT at 45 degrees
PILL_W, PILL_H = 432, 68
PILL_CUT_V = PILL_CUT * PILL_H / (LABEL[3] - LABEL[1])     # 19.0 sprite px down the side
PILL_CUT_H = PILL_CUT * PILL_W / (LABEL[2] - LABEL[0])     # 15.7 sprite px along the top

# the art window (docs/191; TodPull V2.art {29,54,205,190} x 768/234 = 95.2..672.8 x 177.2..623.6)
WIN = (96, 176, 672, 624)
WIN_HOLE = chamfer(96, 176, 672, 624, tl=22, tr=8, bl=8)
WIN_TUBE = inset(WIN_HOLE, -4.5)
WIN_W = 4.0
# the crest socket: TodPull V2.crest {173,153,217,197} -> centred (640, 574.4), 144 wide; docs/191 (640, 576)
SOCK_C = (640.0, 576.0)
# its lower-left cut is deeper: that corner faces the band ring's top-right, and the two tubes keep 12.7 px between their
# centre lines there (the shipped ring and socket ring touched)
SOCK_WELL = chamfer(SOCK_C[0] - 76, SOCK_C[1] - 76, SOCK_C[0] + 76, SOCK_C[1] + 76, tl=30, tr=30, br=30, bl=52)
SOCK_TUBE = chamfer(SOCK_C[0] - 80, SOCK_C[1] - 80, SOCK_C[0] + 80, SOCK_C[1] + 80, tl=34, tr=34, br=34, bl=56)
# the band: docs/191 slot (168,656)-(600,724); the LUI pill sits at V2.band +-2 = (174,663)-(594,719); the ring on the
# shipped ring's centre line (158..609 x 646..733, 10 px), cut parallel to the pill's chamfer
BAND_SLOT = chamfer(168, 656, 600, 724, tl=18, br=18)
BAND_RING = chamfer(162.5, 650.5, 604.5, 728.5, tl=22, tr=12, br=22)     # tr: clears the socket (and the pill's corner)
BAND_W = 4.5
TEXT_SLOT = chamfer(88, 752, 680, 972, tl=18, br=18)
PIP_SLOT = chamfer(184, 996, 584, 1068, tl=14, br=14)
OPEN_TOL = 2.5                      # px: the openings may not move more than this from the shipped art


# ========================================================================================= helpers
def png_bytes(im):
    return artgen.png_bytes(im)


def corner_run(poly, i0, i1, leg):
    """the polyline along `poly` (clockwise) round the corner made of vertices i0..i1 (one vertex for a square corner,
    two for a chamfer), `leg` px along each neighbouring edge (a pair = (incoming edge, outgoing edge))"""
    leg_in, leg_out = (leg, leg) if not isinstance(leg, tuple) else leg
    n = len(poly)
    a, b = poly[i0 % n], poly[i1 % n]
    p, q = poly[(i0 - 1) % n], poly[(i1 + 1) % n]

    def toward(u, v, d):
        L = math.hypot(v[0] - u[0], v[1] - u[1]) or 1.0
        return (u[0] + (v[0] - u[0]) * d / L, u[1] + (v[1] - u[1]) * d / L)
    pts = [toward(a, p, leg_in)] + [poly[k % n] for k in range(i0, i1 + 1)] + [toward(b, q, leg_out)]
    return pts


CORNERS = [(0, 1), (2, 3), (4, 5), (6, 7)]   # OUTLINE's corners as vertex pairs (TL, TR, BR, BL - all chamfered)


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _inside(pt, poly):
    s = [_cross(poly[i], poly[(i + 1) % len(poly)], pt) for i in range(len(poly))]
    return all(v >= -1e-9 for v in s) or all(v <= 1e-9 for v in s)


def _seg_x(p, q, a, b):
    d = (q[0] - p[0]) * (b[1] - a[1]) - (q[1] - p[1]) * (b[0] - a[0])
    if abs(d) < 1e-12:
        return None
    t = ((a[0] - p[0]) * (b[1] - a[1]) - (a[1] - p[1]) * (b[0] - a[0])) / d
    u = ((a[0] - p[0]) * (q[1] - p[1]) - (a[1] - p[1]) * (q[0] - p[0])) / d
    if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
        return t, u, (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    return None


def union_outline(A, B):
    """the outline of the union of two CONVEX clockwise polygons that cross twice (the window and its crest socket)"""
    polys = [A, B]
    start = next(i for i, v in enumerate(A) if not _inside(v, B))
    cur, i, pos = 0, start, A[start]
    out = [pos]
    for _ in range(64):
        P, Q = polys[cur], polys[1 - cur]
        nxt = P[(i + 1) % len(P)]
        best = None
        for j in range(len(Q)):
            h = _seg_x(pos, nxt, Q[j], Q[(j + 1) % len(Q)])
            if h and h[0] > 1e-6 and (best is None or h[0] < best[0][0]):
                best = (h, j)
        if best is not None:
            (t, u, X), j = best
            out.append(X)
            cur, i, pos = 1 - cur, j, X
            continue
        i = (i + 1) % len(P)
        pos = nxt
        if cur == 0 and i == start:
            return out
        out.append(pos)
    raise SystemExit('r10: union_outline did not close')


def evenodd(*polys):
    return ' '.join(poly_d(p) for p in polys)


def sparkle(s, cx, cy, r, color):
    """R4's spark (a 4-point glint: hue glow + white-hot star) with a thin cross flare"""
    r4.sparkle(s, cx, cy, r, color)


# ============================================================================================ BODY
def body():
    """The card plate (rarity-neutral): black-violet glass, the window cut through it, the octagon socket well, the
    band slot, text panel and pip tray recessed into it, two etched rules, faint wear. The frame brings the colour."""
    def base(s):
        g = s.lin([(0, 'card_glass_hi', 1), (0.45, 'card_glass_mid', 1), (1, 'card_glass_lo', 1)])
        s.path(evenodd(OUTLINE, WIN_HOLE), fill='url(#%s)' % g, extra='fill-rule="evenodd"')
        # a diagonal glass sheen across the upper body (the R3 plate's sheen, wider)
        sh = s.lin([(0, '#FFFFFF', 0.045), (0.35, '#FFFFFF', 0.0), (1, '#FFFFFF', 0.0)], 0, 0, W * 0.6, H * 0.6, user=True)
        s.path(evenodd(OUTLINE, WIN_HOLE), fill='url(#%s)' % sh, extra='fill-rule="evenodd"')
        # wear on the glass first, so the recessed slots below stay clean under the game's text
        scratches(s, (40, 640, W - 40, 1120), 22, seed=1017, opacity=0.045)
        scratches(s, (40, 60, W - 40, 170), 8, seed=1018, opacity=0.035)
        # the window's dark inner bevel (the illustration sits a step below the glass)
        s.path(poly_d(inset(WIN_HOLE, -3.0)), stroke='deep', sw=6.0, opacity=0.95)
        s.path(poly_d(inset(WIN_HOLE, -7.5)), stroke='steel', sw=1.2, opacity=0.55)
        # the crest socket: a void well over the window corner, a steel lip
        s.path(poly_d(SOCK_WELL), fill='url(#%s)' % s.lin([(0, 'card_socket', 1), (1, 'deep', 1)]))
        s.steel(inset(SOCK_WELL, 3.0), 1.4, 'steel_hi', 0.55)
        s.path(poly_d(inset(SOCK_WELL, 10)), stroke='#000000', sw=8, opacity=0.35, filt=s.blur(5, (560, 496, 720, 656)))
        # the three slots: recessed void with a steel lip and a lit top bevel
        for shape in (BAND_SLOT, TEXT_SLOT, PIP_SLOT):
            s.path(poly_d(shape), fill='url(#%s)' % s.lin([(0, 'void', 1), (1, 'card_slot_lo', 1)]))
            s.steel(shape, 1.6, 'steel', 0.85)
            r4.bevel(s, shape, k=2.6, opacity=0.35)
        # the text panel's inner hairline (the docs/191 'thin line border')
        s.steel(inset(TEXT_SLOT, 7), 1.0, 'steel', 0.45)
        # two etched rules between the slots (the shipped body's dividers), fading at their ends
        for y in (741.0, 984.0):
            gr = s.lin([(0, 'steel', 0.0), (0.18, 'steel', 0.7), (0.82, 'steel', 0.7), (1, 'steel', 0.0)],
                       36, 0, W - 36, 0, user=True)
            s.path(line_d((36, y), (W - 36, y)), stroke='url(#%s)' % gr, sw=1.2)
        # the side columns: a short circuit trace each side of the text panel (quiet machining)
        for x, d in ((52.0, 1), (W - 52.0, -1)):
            s.path(line_d((x, 790), (x, 900), (x + d * 14, 914)), stroke='steel', sw=1.3, opacity=0.5)
            s.circle(x + d * 14, 918, 3.0, stroke='steel', sw=1.3, opacity=0.5)
    im = r4.layered(W, H, base, None, grain_amp=0.028, seed=1010)
    return im


# =========================================================================================== FRAMES
CROWN_GAP = (270.0, 498.0)          # LEGENDARY: the rim tubes part here for the crown
# the sparks on the rim tube's two small-cut corners: the middle of each cut on the RIM line
SPARK_TR = ((RIM[2][0] + RIM[3][0]) / 2.0, (RIM[2][1] + RIM[3][1]) / 2.0)
SPARK_BL = ((RIM[6][0] + RIM[7][0]) / 2.0, (RIM[6][1] + RIM[7][1]) / 2.0)


def crown_pts(cx, base, w, h):
    """the neon crown motif: three tall points (ball tips) and two valleys over a straight base"""
    hw = w / 2.0
    return [(cx - hw, base), (cx - hw - 6, base - h * 0.80), (cx - hw * 0.46, base - h * 0.36), (cx, base - h),
            (cx + hw * 0.46, base - h * 0.36), (cx + hw + 6, base - h * 0.80), (cx + hw, base)]


def open_run(poly, gap):
    """the closed polyline `poly` as an OPEN path that skips the top edge between x gap[0]..gap[1] (clockwise from the
    gap's right end round to its left end); poly's top edge is the edge from vertex 1 to vertex 2"""
    a, b = poly[1], poly[2]
    y = a[1]
    return [(gap[1], y)] + poly[2:] + poly[:2] + [(gap[0], y)]


def frame(rar):
    hue, core = HUE[rar], CORE[rar]
    lv = RARITIES.index(rar)
    legendary = rar == 'legendary'

    def base(s):
        # the bezel: darker steel glass than the body, its hue a whisper at the top
        g = s.lin([(0, mix(hue, 'bezel_hi', 0.88), 1), (0.5, 'bezel_mid', 1), (1, 'bezel_lo', 1)])
        s.path(evenodd(OUTLINE, BEZEL_IN), fill='url(#%s)' % g, extra='fill-rule="evenodd"')
        s.steel(inset(OUTLINE, 0.8), 1.6, 'steel', 0.9)
        s.steel(BEZEL_IN, 1.6, 'steel_hi', 0.7)
        # the header: dark glass (never a bright pill) - the game lays its white title on the label well
        s.plate(HEADER, fill=mix(hue, 'card_socket', 0.90), top=mix(hue, 'header', 0.80), sheen=0.05)
        s.steel(HEADER, 1.4, 'steel', 0.9)
        s.path(poly_d(LABEL_WELL), fill='url(#%s)' % s.lin([(0, mix(hue, 'void', 0.78), 1), (1, mix(hue, 'void', 0.86), 1)]))
        s.steel(inset(LABEL_WELL, -2.2), 1.2, 'steel_hi', 0.6)
        r4.bevel(s, HEADER, k=3.0, opacity=0.5)
        scratches(s, (40, 6, W - 40, 26), 5, seed=1100 + lv, opacity=0.05, length=(20, 60))

    def top(s):
        glow = (0.80, 0.90, 1.00, 1.40)[lv]
        spread = (1.0, 1.0, 1.05, 1.30)[lv]
        if legendary:
            # THE STRONGER HALO: the rim's light washing in over the bezel and the plate's edge
            s.path(poly_d(RIM), stroke=hue, sw=34, opacity=0.20, filt=s.blur(16))
        # the rim: one tube; EPIC / LEGENDARY a second all the way round; RARE the second at the corners (brackets)
        if legendary:
            s.tube(poly_d(open_run(RIM, CROWN_GAP), close=False), hue, RIM_W, glow=glow, spread=spread)
            s.tube(poly_d(open_run(RIM2, (CROWN_GAP[0] + 10, CROWN_GAP[1] - 10)), close=False), hue, RIM2_W, glow=0.8)
        else:
            s.tube(poly_d(RIM), hue, RIM_W, glow=glow, spread=spread)
        if rar == 'epic':
            s.tube(poly_d(RIM2), hue, RIM2_W, glow=0.8)
        if rar in ('rare', 'legendary'):
            for i0, i1 in CORNERS:
                s.tube(poly_d(corner_run(RIM2, i0, i1, BRACKET_LEG), close=False), hue,
                       RIM2_W + (2.6 if legendary else 2.0), glow=1.0)
        # the header plate's tube, the window + socket tube, the band ring
        s.tube(poly_d(inset(HEADER, 2.0)), hue, 4.0, glow=0.75)
        s.tube(poly_d(union_outline(WIN_TUBE, SOCK_TUBE)), hue, WIN_W, glow=0.5)
        s.tube(poly_d(BAND_RING), hue, BAND_W, glow=0.6)
        if rar == 'epic':
            # the sparks sit ON the tubes, inside the silhouette (the frame is clipped to it below)
            for (x, y, r) in (SPARK_TR + (15.0,), SPARK_BL + (15.0,), (21.0, 430.0, 15.0), (747.0, 820.0, 15.0),
                              (706.0, 34.0, 16.0)):
                sparkle(s, x, y, r, hue)
        if legendary:
            cp = crown_pts(384.0, 45.0, 170.0, 41.0)
            s.path(poly_d(cp), fill=mix(hue, 'card_socket', 0.75))
            s.tube(poly_d(cp), hue, 4.2, glow=1.3)
            for x, y in (cp[1], cp[3], cp[5]):
                s.circle(x, y, 7.5, fill=hue, opacity=0.7, filt=s.blur(4, (x - 10, y - 10, x + 10, y + 10)))
                s.circle(x, y, 4.2, fill=core)
            gem = [(384, 21), (394, 31), (384, 41), (374, 31)]
            s.path(poly_d(gem), fill=core)
            s.tube(poly_d(gem), hue, 2.0, glow=0.9)
            for (x, y, r) in (SPARK_TR + (17.0,), SPARK_BL + (17.0,), (62.0, 148.0, 17.0), (706.0, 34.0, 17.0)):
                sparkle(s, x, y, r, hue)

    im = r4.layered(W, H, base, top, grain_amp=0.025, seed=1200 + lv)
    if legendary:
        gold, pale = HUE[rar], mix(HUE[rar], '#FFFFFF', 0.55)
        for i, box in enumerate(((6, 260, 70, 1120), (W - 70, 260, W - 6, 1120), (90, 1074, W - 90, 1136))):
            im = embers(im, box, 24 if i < 2 else 18, seed=1290 + i, colors=(gold, pale, gold), size=(1.2, 3.0),
                        alpha=(80, 230))
    # ONE SILHOUETTE: the tubes' glow stops at the card's edge on every side - the cut corners too (the canvas edge
    # already stops it on the straight sides); the game's own card glow (TodPull fx glow) is the light outside
    return clip_to(im, OUTLINE)


# =========================================================================================== CRESTS
CS = 432                             # drawn 3x, resized to 144


def _F(d):
    return '<path d="%s" fill="#fff"/>' % d


def _ST(d, w):
    return ('<path d="%s" fill="none" stroke="#fff" stroke-width="%.2f" stroke-linecap="round" '
            'stroke-linejoin="round"/>' % (d, w))


def _poly(pts):
    return _F(poly_d(pts))


def _ngon(cx, cy, r, n, rot=0.0):
    return [(cx + r * math.cos(rot + 2 * math.pi * k / n), cy + r * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]


def crest_parts(rar):
    """(white ink, hue accent, cut) svg bodies on a 432 canvas, centre (216, 216); the glyph stays inside r ~ 150"""
    c = CS / 2.0
    if rar == 'common':
        # a round brilliant from above: the girdle, the octagon TABLE in steel, the eight STAR facets round it (the
        # classic brilliant pattern: table, star, girdle) as cut lines
        girdle = _ngon(c, c, 134, 32, 0.0)
        table = _ngon(c, c, 60, 8, math.pi / 8)
        star = []
        for k in range(8):
            star.append(table[k])
            ang = math.pi / 8 + (k + 0.5) * math.pi / 4
            star.append((c + 112 * math.cos(ang), c + 112 * math.sin(ang)))
        white = _poly(girdle)
        acc = _poly(table)
        cuts = _ST(poly_d(table), 7) + _ST(poly_d(star), 6)
        for k in range(8):
            ang = math.pi / 8 + k * math.pi / 4
            cuts += _ST(line_d(table[k], (c + 134 * math.cos(ang), c + 134 * math.sin(ang))), 5)
        return white, acc, cuts
    if rar == 'rare':
        # the classic diamond: a crown over a pavilion; the left facets white, the right in the hue
        tl, tr, gl, gr, cul = (c - 82, c - 92), (c + 82, c - 92), (c - 142, c - 30), (c + 142, c - 30), (c, c + 146)
        tm = (c, c - 92)
        gm = (c, c - 30)
        white = _poly([tl, tm, gm, (c - 50, c - 30), gl]) + _poly([gl, (c - 50, c - 30), cul]) + \
            _poly([(c - 50, c - 30), gm, cul])
        acc = _poly([tm, tr, gr, (c + 50, c - 30), gm]) + _poly([gm, (c + 50, c - 30), cul]) + \
            _poly([(c + 50, c - 30), gr, cul])
        cuts = _ST(line_d(gl, gr), 7) + _ST(line_d((c - 50, c - 30), cul), 6) + _ST(line_d((c + 50, c - 30), cul), 6) + \
            _ST(line_d(tl, (c - 50, c - 30)), 6) + _ST(line_d(tr, (c + 50, c - 30)), 6) + _ST(line_d(tm, gm), 5)
        return white, acc, cuts
    if rar == 'epic':
        # an eight-point star: four long points, four short; every point split - one face white, one in the hue
        white, acc = [], []
        for k in range(8):
            ang = -math.pi / 2 + k * math.pi / 4
            R = 154 if k % 2 == 0 else 102
            tip = (c + R * math.cos(ang), c + R * math.sin(ang))
            l = (c + 48 * math.cos(ang - math.pi / 8), c + 48 * math.sin(ang - math.pi / 8))
            r_ = (c + 48 * math.cos(ang + math.pi / 8), c + 48 * math.sin(ang + math.pi / 8))
            white.append(_poly([(c, c), l, tip]))
            acc.append(_poly([(c, c), tip, r_]))
        core_ = _poly(_ngon(c, c, 26, 8, math.pi / 8))
        return ''.join(white) + core_, ''.join(acc), ''
    # legendary: a crown - three points with balls, the band in the hue, a gem cut into the band
    base_y, top_y = c + 92, c - 112
    pts = [(c - 124, base_y), (c - 136, c - 74), (c - 66, c - 10), (c, top_y), (c + 66, c - 10), (c + 136, c - 74),
           (c + 124, base_y)]
    white = _poly(pts) + ''.join('<circle cx="%.1f" cy="%.1f" r="21" fill="#fff"/>' % (x, y)
                                 for x, y in (pts[1], pts[3], pts[5]))
    band = [(c - 126, base_y - 46), (c + 126, base_y - 46), (c + 124, base_y + 8), (c - 124, base_y + 8)]
    acc = _poly(band)
    gem = [(c, base_y - 66), (c + 26, base_y - 19), (c, base_y + 28), (c - 26, base_y - 19)]
    cuts = _poly(gem) + _ST(line_d((c - 126, base_y - 46), (c + 126, base_y - 46)), 6)
    return white, acc, cuts


CREST_SCALE = 1.12                   # the glyphs fill the socket like the shipped gems did (their halo stays inside)


def _grow(body):
    return '<g transform="translate(%d,%d) scale(%.3f) translate(%d,%d)">%s</g>' % (CS // 2, CS // 2, CREST_SCALE,
                                                                                  -CS // 2, -CS // 2, body)


def crest(rar):
    white, acc, cut = (_grow(b) if b else b for b in crest_parts(rar))
    wc, ac = r4.coverage(CS, CS, white), r4.coverage(CS, CS, acc)
    cc = r4.coverage(CS, CS, cut) if cut else None
    ac = ac * (1.0 - (cc if cc is not None else 0))
    if rar == 'legendary':
        # the crown: white-hot points, the band in gold; the gem cut through the band then set back in white-hot
        # inside a dark ring (the cut's own margin), so the jewel reads as a light, not a painted bead
        wc = wc * (1.0 - ac)
        gem_d = poly_d([(216, 255), (236, 290), (216, 325), (196, 290)])
        gem = r4.coverage(CS, CS, _grow(_F(gem_d)))
        im = r4.neon_glyph(wc + gem, ac, HUE[rar], sigma=19.0, k=0.95, cut_cov=np.clip(cc - gem, 0, 1), acc_lift=0.10)
    else:
        acc_lift = {'common': 0.0, 'rare': 0.12, 'epic': 0.15}[rar]
        acc_col = {'common': '#A9B4CC', 'rare': None, 'epic': None}[rar]
        im = r4.neon_glyph(wc, ac, HUE[rar], acc=acc_col, sigma=19.0, k=0.95 if rar != 'common' else 0.85,
                           cut_cov=cc, acc_lift=acc_lift)
    return im.resize((144, 144), Image.LANCZOS)


# ============================================================================================= BACK
def back():
    """face-down: the spire as neon line-art on black glass, the crown above its tip, the halo ring crossing it;
    TOWER OF DOOM II in our typeface. Behind the spire, by theme (LOOK grid): synthwave = the outrun sun cut by its
    slits over a perspective grid floor and a lit horizon; fallen = the red era's back (docs/217_ref, RT review
    2026-10-05): dark scratched glass, a faint two-hairline steel ring where the sun was, the dark city, no floor.
    STRICTLY NEUTRAL (black / steel / white): the game washes it in the rung's colour (TodPull BackTint), so the
    tubes are white and the glow carries the colour."""
    cx = W / 2.0
    hz = 820.0                                     # the horizon

    def base(s):
        g = s.lin([(0, '#101014', 1), (0.6, '#09090C', 1), (1, '#050507', 1)])
        s.path(poly_d(OUTLINE), fill='url(#%s)' % g)
        sh = s.lin([(0, '#FFFFFF', 0.05), (0.35, '#FFFFFF', 0.0), (1, '#FFFFFF', 0.0)], 0, 0, W * 0.6, H * 0.6, user=True)
        s.path(poly_d(OUTLINE), fill='url(#%s)' % sh)
        s.path(evenodd(OUTLINE, BEZEL_IN), fill='#121216', extra='fill-rule="evenodd"')
        s.steel(inset(OUTLINE, 0.8), 1.6, '#4A4A54', 0.9)
        s.steel(BEZEL_IN, 1.6, '#6A6A76', 0.6)
        if LOOK['grid']:
            # the sun: a disc of light behind the spire, cut by the synthwave's horizontal slits
            sun = s.lin([(0, '#6E6E7C', 0.85), (0.55, '#3C3C46', 0.75), (1, '#1C1C22', 0.6)], 0, 330, 0, 790, user=True)
            s.circle(cx, 560, 230, fill='url(#%s)' % sun)
            s.circle(cx, 560, 300, fill='url(#%s)' % s.rad([(0.70, '#8A8A96', 0.10), (1, '#8A8A96', 0.0)]))
            for k in range(8):
                y = 590 + k * 26
                s.rect(cx - 260, y, 520, 3 + k * 1.6, '#09090C', opacity=0.95)
            # the grid floor: perspective lines to the vanishing point, rungs closing toward the horizon
            vp = (cx, hz - 40)
            for k in range(-9, 10):
                x = cx + k * 96
                gr = s.lin([(0, '#8A8A96', 0.0), (1, '#8A8A96', 0.5)], 0, hz, 0, H - 30, user=True)
                ex = vp[0] + (x - vp[0]) * (H - 30 - vp[1]) / (hz - vp[1])
                s.path(line_d((vp[0] + (x - vp[0]) * 0.02, hz), (ex, H - 30)), stroke='url(#%s)' % gr, sw=1.4)
            y, step = hz + 6, 7.0
            while y < H - 30:
                a = min(0.55, 0.12 + (y - hz) / 500.0)
                s.path(line_d((30, y), (W - 30, y)), stroke='#8A8A96', sw=1.2, opacity=a)
                y += step
                step *= 1.32
            s.rect(30, hz - 1.0, W - 60, 2.0, '#B8B8C4', opacity=0.5)
        else:
            # the red era's back: no sun, no floor. Where the sun was, a faint steel ring of two hairlines and a
            # breath of light inside it (neutral: BackTint colours it), so the spire still stands in front of something
            s.circle(cx, 560, 300, fill='url(#%s)' % s.rad([(0.55, '#8A8A96', 0.05), (1, '#8A8A96', 0.0)]))
            for r_, a_, w_ in ((232, 0.18, 1.6), (246, 0.10, 1.2)):
                s.circle(cx, 560, r_, stroke='#8A93A8', sw=w_, opacity=a_)
        # the city on the horizon (R3's skyline, neutral: no lit roofs)
        rng = np.random.default_rng(1404)
        x = 36.0
        while x < W - 36:
            w_ = float(rng.uniform(22, 54))
            h_ = float(rng.uniform(16, 70))
            if abs(x + w_ / 2 - cx) > 120:
                s.path(poly_d([(x, hz), (x, hz - h_ + 5), (x + 5, hz - h_), (x + w_, hz - h_), (x + w_, hz)]),
                       fill='#0A0A0D', opacity=0.95)
                s.path(line_d((x, hz - h_ + 5), (x + 5, hz - h_), (x + w_, hz - h_)), stroke='#5A5A66', sw=1.2,
                       opacity=0.55)
            x += w_ + float(rng.uniform(-4, 6))
        scratches(s, (40, 60, W - 40, H - 60), 26, seed=1401, color='#9A9AA6', opacity=0.05)
        if not LOOK['grid']:
            # the red era's glass is visibly scratched (LOOK scratch_k): a second, longer neutral set
            scratches(s, (40, 60, W - 40, H - 60), 34, seed=1402, color='#9A9AA6', opacity=0.04 * LOOK['scratch_k'],
                      length=(50, 190))

    # THE SPIRE: five stepped tiers narrowing to a needle (the map's tower), a dark glass body under a white tube
    tiers = [(150, 830, 740), (120, 740, 640), (92, 640, 540), (66, 540, 440), (42, 440, 350)]
    spire = []
    for hw, y0, y1 in tiers:
        spire.append((hw, y0, y1))

    def outline_pts():
        left, right = [], []
        for i, (hw, y0, y1) in enumerate(tiers):
            left += [(cx - hw, y0), (cx - hw, y1 + 10), (cx - hw + 10, y1)]
            right += [(cx + hw, y0), (cx + hw, y1 + 10), (cx + hw - 10, y1)]
        tip = [(cx - 16, 350), (cx - 8, 300), (cx, 200), (cx + 8, 300), (cx + 16, 350)]
        return left + tip + right[::-1]

    def top(s):
        pts = outline_pts()
        # the halo ring's FAR half first: the spire's glass hides it where it passes behind
        ry, rx, yc = 34.0, 190.0, 600.0
        far = 'M%.1f,%.1f A%.1f,%.1f 0 0 1 %.1f,%.1f' % (cx - rx, yc, rx, ry, cx + rx, yc)
        s.path(far, stroke='#C8C8D2', sw=2.6, opacity=0.45)
        s.path(poly_d(pts), fill='url(#%s)' % s.lin([(0, '#16161C', 1), (1, '#0B0B0F', 1)]))
        # the tier lines and the window slits (each tier lit a little brighter toward the top)
        for i, (hw, y0, y1) in enumerate(tiers):
            s.path(line_d((cx - hw + 10, y1), (cx + hw - 10, y1)), stroke=NEUTRAL_TUBE, sw=2.0, opacity=0.8)
            for k in range(-2, 3):
                x = cx + k * hw * 0.36
                s.path(line_d((x, y1 + 18), (x, y0 - 14)), stroke='#9A9AA8', sw=2.2, opacity=0.35 + 0.08 * i)
        s.tube(poly_d(pts), NEUTRAL_TUBE, 4.4, glow=1.0, spread=1.1)
        s.tube(line_d((cx, 200), (cx, 150)), NEUTRAL_TUBE, 2.6, glow=0.9)
        # the halo ring crossing the spire at its waist (behind it on the far side: drawn in two arcs)
        near = 'M%.1f,%.1f A%.1f,%.1f 0 0 0 %.1f,%.1f' % (cx - rx, yc, rx, ry, cx + rx, yc)
        s.tube(near, NEUTRAL_TUBE, 3.6, glow=0.9)
        # the crown floating over the needle
        cp = crown_pts(cx, 128.0, 76.0, 40.0)
        s.tube(poly_d(cp), NEUTRAL_TUBE, 3.6, glow=1.1)
        for x, y in (cp[1], cp[3], cp[5]):
            s.circle(x, y, 4.2, fill='#FFFFFF')
        # the rim tube + corner brackets (neutral)
        s.tube(poly_d(RIM), NEUTRAL_TUBE, 5.0, glow=0.7)
        for i0, i1 in CORNERS:
            s.tube(poly_d(corner_run(RIM2, i0, i1, BRACKET_LEG), close=False), '#C8C8D2', 3.2, glow=0.6)
        # rules either side of the title
        for a, b in ((52, 132), (W - 132, W - 52)):
            s.path(line_d((a, 1088), (b, 1088)), stroke='#9A9AA8', sw=1.6, opacity=0.7)
        for x in (132, W - 132):
            s.path(poly_d([(x, 1082), (x + 6, 1088), (x, 1094), (x - 6, 1088)]), fill='#E9ECF2')

    im = r4.layered(W, H, base, top, grain_amp=0.03, seed=1400)
    put_text(im, 'TOWER OF DOOM II', cap=30, baseline=1103, cx=W / 2.0, rgb='#F2F4F8', track=0.30, glow='#C8C8D2',
             glow_k=0.55)
    return im


# ============================================================================== THE REEL (from the parked art)
def park_dir(root=None):
    for r in ([root] if root else []) + [REPO]:
        d = os.path.join(r, PARK_REL)
        if os.path.isdir(d):
            return d
    raise SystemExit('r10: the parked shipped art (%s) is missing - it is this generator\'s source' % PARK_REL)


def parked(name, root=None):
    return Image.open(os.path.join(park_dir(root), name + '.png')).convert('RGBA')


def harmonic_fill(img, mask):
    """inpaint `mask` (bool) with the harmonic (Laplace) interpolation of the pixels round it, on PREMULTIPLIED RGBA:
    smooth glass fields and soft glows close over a removed ornament with no seam (the fields here carry no texture
    finer than their gradients)"""
    a = np.asarray(img).astype(np.float64)
    al = a[..., 3:4] / 255.0
    pm = np.concatenate([a[..., :3] * al, a[..., 3:4]], axis=2)
    h, w = mask.shape
    idx = -np.ones((h, w), dtype=np.int64)
    ys, xs = np.where(mask)
    idx[ys, xs] = np.arange(len(ys))
    n = len(ys)
    rows, cols, vals = [], [], []
    rhs = np.zeros((n, 4))
    for k in range(n):
        y, x = ys[k], xs[k]
        nb = 0
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            yy, xx = y + dy, x + dx
            if not (0 <= yy < h and 0 <= xx < w):
                continue
            nb += 1
            j = idx[yy, xx]
            if j >= 0:
                rows.append(k); cols.append(j); vals.append(-1.0)
            else:
                rhs[k] += pm[yy, xx]
        rows.append(k); cols.append(k); vals.append(float(nb))
    A = sparse.csr_matrix((vals, (rows, cols)), shape=(n, n))
    sol = spsolve(A.tocsc(), rhs)
    sol = np.atleast_2d(sol)
    out = pm.copy()
    out[ys, xs] = sol
    alpha = np.clip(out[..., 3], 0, 255)
    with np.errstate(invalid='ignore', divide='ignore'):
        rgb = np.where(alpha[..., None] > 1e-6, out[..., :3] / np.maximum(alpha[..., None], 1e-6) * 255.0, 0)
    res = np.dstack([np.clip(rgb, 0, 255), alpha])
    return Image.fromarray(np.clip(np.rint(res), 0, 255).astype(np.uint8), 'RGBA')


def ornament_mask(img, box, field_sigma=9.0, thresh=16.0, grow=7, keep=None):
    """the ornament inside `box`: pixels brighter (or more opaque) than the smooth field round them, grown by its
    glow; `keep` = a bool mask never touched (the frame lines)"""
    a = np.asarray(img).astype(np.float64)
    lum = (a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11) * a[..., 3] / 255.0
    x0, y0, x1, y1 = box
    sub = lum[y0:y1, x0:x1]
    field = ndimage.median_filter(sub, size=int(field_sigma * 2 + 1))
    m = (sub - field) > thresh
    m = ndimage.binary_dilation(m, iterations=grow)
    out = np.zeros(lum.shape, bool)
    out[y0:y1, x0:x1] = m
    if keep is not None:
        out &= ~keep
    return out


def region(shape, fn):
    """a bool mask of the pixel centres where fn(x, y) holds"""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64) + 0.5
    return fn(xx, yy)


def column_fill(img, mask, side=None):
    """every masked pixel takes the mean of its column's nearest unmasked pixels above and below (a VERTICAL frame
    line runs through the masked rows unbroken - the harmonic fill would soften it); side 'down' / 'up' copies from
    that side only (beside a chamfer, where the other side is the diagonal)"""
    a = np.asarray(img).astype(np.float64).copy()
    h, w = mask.shape
    for x in np.where(mask.any(axis=0))[0]:
        col = mask[:, x]
        for y in np.where(col)[0]:
            up = y
            while up >= 0 and col[up]:
                up -= 1
            dn = y
            while dn < h and col[dn]:
                dn += 1
            ks = {'down': (dn,), 'up': (up,)}.get(side, (up, dn))
            src = [a[k, x] for k in ks if 0 <= k < h]
            a[y, x] = np.mean(src, axis=0)
    return Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8), 'RGBA')


def detect(img, allowed, thresh=14.0, size=17, grow=5):
    """the ornament inside `allowed`: premultiplied luminance above its own median field, grown by its glow"""
    a = np.asarray(img).astype(np.float64)
    lum = (a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11) * a[..., 3] / 255.0
    ys, xs = np.where(allowed)
    y0, y1, x0, x1 = max(0, ys.min() - size), ys.max() + size + 1, max(0, xs.min() - size), xs.max() + size + 1
    sub = lum[y0:y1, x0:x1]
    field = ndimage.median_filter(sub, size=size, mode='nearest')
    m = np.zeros(lum.shape, bool)
    m[y0:y1, x0:x1] = (sub - field) > thresh
    m &= allowed
    m = ndimage.binary_dilation(m, iterations=grow) & allowed
    return m


def tile_layer(size, fn, ss=2):
    s = Svg(size[0], size[1])
    fn(s)
    return s.render(ss=ss)


# THE LEGENDARY TILE (560 x 416): its four gold scrolls stood inside the frame's thin inner line, whose centre runs
# chamfer(25.5, 25.5, 534, 391, tl=20, br=20) (measured on the shipped tile). Each scroll's region keeps 3 px clear of
# that line; make_spin_art.py samples the field at x 68..77 / 482..491 on rows 323..394 and reads the word's gold ink
# on x 68..490, so nothing new is drawn in x 62..496 below row 320 (the CURSED tile stays a clean cut of this one).
LEG_LINE = chamfer(25.5, 25.5, 534, 391, tl=20, br=20)
LEG_SCROLLS = [
    lambda x, y: (x > 29) & (y > 29) & (x + y > 75) & (x < 110) & (y < 108),           # top left
    lambda x, y: (x < 530.5) & (y > 29) & (x > 450) & (y < 108),                         # top right
    lambda x, y: (x > 29) & (y < 387.5) & (x < 70) & (y > 336),                          # bottom left
    lambda x, y: (x < 530.5) & (y < 387.5) & (x + y < 900.5) & (x > 486) & (y > 336),    # bottom right
]


def reel_tile_legendary(root=None):
    src = parked('i_tod_spin_tile_legendary', root)
    gold = '#FFC23D'
    out = src
    for fn in LEG_SCROLLS:
        allowed = region((416, 560), fn)
        m = detect(out, allowed, thresh=10.0, size=19, grow=6)
        out = harmonic_fill(out, m)

    def light(s):
        # the brackets: the inner line's four corners lit again as short neon Ls, a stroke inside the line
        br = inset(LEG_LINE, 8.0)
        # (incoming, outgoing) legs; the bottom legs stop short of x 62 / 497 (make_spin_art's field columns)
        for i0, i1, leg in ((0, 1, (34.0, 34.0)), (2, 2, (40.0, 40.0)), (3, 4, (34.0, 4.0)), (5, 5, (18.0, 28.0))):
            s.tube(poly_d(corner_run(br, i0, i1, leg), close=False), gold, 3.2, glow=1.0)
        # THE STAMP'S GLINTS on the frame's corners (the legendary banner's language), small
        for x, y, r in ((14.0, 52.0, 13.0), (546.0, 300.0, 11.0), (300.0, 13.0, 10.0)):
            r4.sparkle(s, x, y, r, gold)
    out = out.copy()
    out.alpha_composite(tile_layer((560, 416), light))
    pale = mix(gold, '#FFFFFF', 0.55)
    out = embers(out, (34, 34, 166, 236), 7, seed=1501, colors=(gold, pale), size=(1.0, 2.2), alpha=(70, 200))
    out = embers(out, (396, 34, 526, 236), 7, seed=1502, colors=(gold, pale), size=(1.0, 2.2), alpha=(70, 200))
    return out


# THE EPIC TILE (560 x 416): two lightning squiggles on the field, either side of the window; the inner line's centre
# runs at x 24 / 535.5. The tile already carries the EPIC grammar (a double line and corner brackets): the squiggles go,
# a few sparks come in their place.
EPIC_SQUIGGLES = [
    lambda x, y: (x > 27.5) & (x < 134) & (y > 128) & (y < 174),
    lambda x, y: (x > 428) & (x < 532.5) & (y > 74) & (y < 120),
]


def reel_tile_epic(root=None):
    src = parked('i_tod_spin_tile_epic', root)
    violet = '#B55CFF'
    out = src
    for fn in EPIC_SQUIGGLES:
        m = detect(out, region((416, 560), fn), thresh=5.0, size=21, grow=9)
        out = harmonic_fill(out, m)

    def light(s):
        for x, y, r in ((24.0, 150.0, 15.0), (536.0, 96.0, 15.0), (412.0, 14.0, 11.0), (150.0, 401.0, 11.0)):
            r4.sparkle(s, x, y, r, violet)
    out = out.copy()
    out.alpha_composite(tile_layer((560, 416), light))
    return out


# THE EPIC STAMP (1600 x 208): electric wisps fan out from both ends over the side flare, and three short nubs cross
# the double end-line at y 52 / 104 / 155 into the plate (to x 150 / 1450). The wisps go (harmonic fill over the flare,
# which stays: it is light), the nubs go (the end lines re-run down their own columns), sparks sit on the ends.
BAN_W, BAN_H = 1600, 208
BAN_NUB_Y = (52.0, 104.0, 155.0)
BAN_WISP_Y = (75.0, 128.0)


def reel_banner_epic(root=None):
    src = parked('i_tod_spin_banner_epic', root)
    violet = '#B55CFF'
    out = src
    shape = (BAN_H, BAN_W)
    # 1. the wisps on the side flares (outside the end lines) and the nubs' outer stubs
    for side, fn in ((0, lambda x, y: (x < 119) & (y > 18) & (y < 192)), (1, lambda x, y: (x > 1481) & (y > 18) & (y < 192))):
        allowed = region(shape, fn)
        m = detect(out, allowed, thresh=5.0, size=21, grow=5)
        for y0 in BAN_NUB_Y:
            m |= allowed & region(shape, lambda x, y: (np.abs(y - y0) < 11) & ((x > 94) & (x < 1506)))
        for y0 in BAN_WISP_Y:                     # the wisps between the nubs root on the tube's own glow
            m |= allowed & region(shape, lambda x, y: (np.abs(y - y0) < 8) & ((x > 98) & (x < 1502)))
        out = harmonic_fill(out, m)
    # 2. the nubs: the end lines AND the glow they throw into the plate are vertically uniform there (the rails beside
    # the word start at x 155 / 1445; the nubs end at 149 / 1451), so every column re-runs from its own clean rows - beside a chamfer from the
    # straight side only (the left end is chamfered at the top, the right at the bottom)
    for y0 in BAN_NUB_Y:
        for xa, xb, side in ((116.5, 153, 'down' if y0 < 80 else None), (1447, 1483.5, 'up' if y0 > 130 else None)):
            band = region(shape, lambda x, y: (x > xa) & (x < xb) & (np.abs(y - y0) < 10.5))
            out = column_fill(out, band, side)

    def light(s):
        for x, y, r in ((129.0, 104.0, 22.0), (1471.0, 104.0, 22.0), (129.0, 40.0, 11.0), (1471.0, 168.0, 11.0)):
            r4.sparkle(s, x, y, r, violet)
    out = out.copy()
    out.alpha_composite(tile_layer((BAN_W, BAN_H), light))
    return out

# ============================================================================== THE PULL's STAMP (i_tod_pull_banner)
STAMP_W, STAMP_H = 1024, 192
# TodPull.lua Banner stretches it to 340 x (bigCap + 52) canvas (x 0.33, y ~0.43): the cut is drawn 48 x 36 in art so
# it lands near 45 degrees on screen, the pill's TL / BR grammar (PILL_CUT); the plate spans the art's width (no tails)
STAMP = [(40, 64), (88, 28), (984, 28), (984, 128), (936, 164), (40, 164)]
STAMP_NAME = 'i_tod_pull_banner'


def pull_banner(root=None):
    """THE PULL's reveal stamp: the rarity word ('LEGENDARY') and its gain ('+4 LEVELS') sit on it over the card
    (TodPull.lua Banner, tinted by the rarity). THEME 'synthwave' keeps the delivered 2026-09-29 ribbon (a light rounded
    plate with folded tails and diamond studs, dark ink on it) - its exact bytes, parked. THEME 'fallen' draws it in the
    R10 grammar: dark neutral glass, chamfered TL / BR like the label pill, ONE near-white rim tube (the Tint makes it
    the rarity's light) and a faint steel hairline inside - no tails, no studs (RT review 2026-10-05: it was the one
    ornament left in THE PULL). TodPull.lua writes the word in the rarity's colour on it (r3 CODE_TINTS pins that).
    Returns (RGBA, bytes)."""
    if THEME == 'synthwave':
        p = os.path.join(park_dir(root), STAMP_NAME + '.png')
        return Image.open(p).convert('RGBA'), open(p, 'rb').read()

    def base(s):
        g = s.lin([(0, '#16161B', 0.94), (0.5, '#0C0C10', 0.94), (1, '#060608', 0.95)])
        s.path(poly_d(STAMP), fill='url(#%s)' % g)
        sh = s.lin([(0, '#FFFFFF', 0.07), (0.3, '#FFFFFF', 0.0), (1, '#FFFFFF', 0.0)], 0, 28, 0, 164, user=True)
        s.path(poly_d(STAMP), fill='url(#%s)' % sh)
        s.steel(inset(STAMP, 11), 1.6, '#5A5A66', 0.7)
        scratches(s, (120, 40, 900, 150), 10, seed=1501, color='#9A9AA6', opacity=0.035, length=(40, 140))

    def top(s):
        s.tube(poly_d(STAMP), NEUTRAL_TUBE, 5.0, glow=0.7, spread=0.6)

    im = r4.layered(STAMP_W, STAMP_H, base, top, grain_amp=0.02, seed=1500)
    return im, png_bytes(im)


def stamp_problems(im, theme=None):
    """THE FALLEN STAMP IS ONE PLATE OF NEUTRAL LIGHT: nothing past the plate's ends (the ribbon's tails reached the
    canvas edge), and no saturated pixel (the Tint colours it). theme None reads THEME (synthwave: the delivered
    ribbon is the design, nothing to check)."""
    if (theme or THEME) == 'synthwave':
        return []
    a = np.asarray(im.convert('RGBA')).astype(np.float64)
    out = []
    ends = max(a[:, :24, 3].max(), a[:, -24:, 3].max())
    if ends > 40:
        out.append('%s: art reaches the canvas ends (alpha %d) - tails or studs past the plate' % (STAMP_NAME, ends))
    rgb = a[..., :3]
    hi, lo = rgb.max(-1), rgb.min(-1)
    sat = ((a[..., 3] > 128) & (hi > 50) & ((hi - lo) > 0.25 * hi)).sum()
    if sat:
        out.append('%s: %d saturated pixels - the stamp must stay neutral (the game tints it)' % (STAMP_NAME, sat))
    return out

# ============================================================================================ BUILD
CARD = ['i_tod_card2_body'] + ['i_tod_card2_frame_' + r for r in RARITIES] + ['i_tod_card2_crest_' + r for r in RARITIES] + \
    ['i_tod_card2_back']
REEL = ['i_tod_spin_tile_epic', 'i_tod_spin_tile_legendary', 'i_tod_spin_banner_epic']
PULL = [STAMP_NAME]                 # THE PULL's reveal stamp (RT 2026-10-05)
SIZES = {'i_tod_card2_body': (W, H), 'i_tod_card2_back': (W, H), 'i_tod_spin_tile_epic': (560, 416),
         'i_tod_spin_tile_legendary': (560, 416), 'i_tod_spin_banner_epic': (BAN_W, BAN_H),
         STAMP_NAME: (STAMP_W, STAMP_H)}
for _r in RARITIES:
    SIZES['i_tod_card2_frame_' + _r] = (W, H)
    SIZES['i_tod_card2_crest_' + _r] = (144, 144)
RETIRED = 'i_tod_card_back'          # the old back (docs/189): retired whole with this pass


def build_all(root=None, only=None):
    """every deliverable -> (RGBA image, the exact bytes the landing installs)"""
    fns = {'i_tod_card2_body': body, 'i_tod_card2_back': back,
           'i_tod_spin_tile_epic': lambda: reel_tile_epic(root),
           'i_tod_spin_tile_legendary': lambda: reel_tile_legendary(root),
           'i_tod_spin_banner_epic': lambda: reel_banner_epic(root)}
    for r in RARITIES:
        fns['i_tod_card2_frame_' + r] = (lambda rr: (lambda: frame(rr)))(r)
        fns['i_tod_card2_crest_' + r] = (lambda rr: (lambda: crest(rr)))(r)
    out = {}
    for name in CARD + REEL:
        if only and name not in only:
            continue
        im = fns[name]().convert('RGBA')
        if im.size != SIZES[name]:
            raise SystemExit('r10: %s came out %s, must be %s' % (name, im.size, SIZES[name]))
        if im.width % 4 or im.height % 4:
            raise SystemExit('r10: %s %s is not a multiple of 4' % (name, im.size))
        out[name] = (im, png_bytes(im))
    if not only or STAMP_NAME in only:
        out[STAMP_NAME] = pull_banner(root)          # (synthwave: the parked ribbon's own bytes)
    return out

# ======================================================================================== the gates
def _rd(root, rel):
    for r in ([root] if root else []) + [REPO]:
        p = os.path.join(r, rel)
        if os.path.isfile(p):
            return open(p, encoding='utf-8', errors='replace').read()
    raise SystemExit('r10: cannot read %s' % rel)


def lockstep_problems(root=None):
    """the hues are tod_upgrade.lua's RARITY colours; the label well is TodPull.lua's V2.titleLabel; the art window and
    the crest socket sit where TodPull.lua's V2.art / V2.crest put the illustration and the crest"""
    out = []
    lua = _rd(root, UPG_LUA)
    for i, r in enumerate(RARITIES):
        m = re.search(r'\[%d\]\s*=\s*\{\s*tag\s*=\s*"[A-Z]+",\s*col\s*=\s*\{\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)\s*\}' % (i + 1), lua)
        if not m:
            out.append('tod_upgrade.lua: RARITY[%d] not found' % (i + 1))
        elif tuple(float(v) for v in m.groups()) != RARITY_COL[r]:
            out.append('tod_upgrade.lua RARITY[%d].col is %s, the art is drawn in %s - regenerate with the new hue'
                       % (i + 1, m.groups(), RARITY_COL[r]))
    pull = _rd(root, PULL_LUA)

    def v2(key):
        m = re.search(r'\b%s\s*=\s*\{\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)\s*\}' % key, pull)
        return tuple(float(v) * CARD_K for v in m.groups()) if m else None
    lab, art, cre = v2('titleLabel'), v2('art'), v2('crest')
    if lab is None or max(abs(a - b) for a, b in zip(lab, LABEL)) > 0.01:
        out.append('TodPull.lua V2.titleLabel moved (%s): the frame\'s label well is %s' % (lab, LABEL))
    if art is None or max(abs(a - b) for a, b in zip(art, WIN)) > 1.5:
        out.append('TodPull.lua V2.art moved (%s): the window is %s' % (art, WIN))
    if cre is None or abs((cre[0] + cre[2]) / 2 - SOCK_C[0]) > 2.0 or abs((cre[1] + cre[3]) / 2 - SOCK_C[1]) > 2.0:
        out.append('TodPull.lua V2.crest moved (%s): the socket is centred %s' % (cre, SOCK_C))
    return out


def pill_problems(root=None):
    """i_tod_pull_pill (install_card_art.py fx_pill) must carry the label well's chamfer: cut at top-left and
    bottom-right by PILL_CUT_H x PILL_CUT_V, square at the other two corners"""
    p = None
    for r in ([root] if root else []) + [REPO]:
        q = os.path.join(r, IMG_REL, 'i_tod_pull_pill.png')
        if os.path.isfile(q):
            p = q
            break
    if not p:
        return ['i_tod_pull_pill.png is missing']
    a = np.asarray(Image.open(p).convert('RGBA'))[..., 3].astype(int)
    if a.shape != (PILL_H, PILL_W):
        return ['i_tod_pull_pill is %s, expected %dx%d' % (a.shape[::-1], PILL_W, PILL_H)]
    c = 1 + PILL_CUT_H * 0.35                              # a point inside each cut triangle, and one just past it
    inside_cut = [a[int(1 + PILL_CUT_V * 0.35), int(c)], a[int(PILL_H - 2 - PILL_CUT_V * 0.35), int(PILL_W - 1 - c)]]
    past_cut = [a[int(1 + PILL_CUT_V + 3), 4], a[3, int(1 + PILL_CUT_H + 3)],
                a[int(PILL_H - 2 - PILL_CUT_V - 3), PILL_W - 5], a[PILL_H - 4, int(PILL_W - 2 - PILL_CUT_H - 3)]]
    square = [a[3, PILL_W - 4], a[PILL_H - 4, 3]]
    if max(inside_cut) > 24 or min(past_cut) < 200 or min(square) < 200:
        return ['i_tod_pull_pill is not cut like the label well (TL/BR cut %.1f x %.1f, TR/BL square): run the staged '
                'tools/card_pull/install_card_art.py (fx_pill) - inside cut %s, past cut %s, square corners %s'
                % (PILL_CUT_H, PILL_CUT_V, inside_cut, past_cut, square)]
    return []


def _probe(a, cx, cy, dx, dy, th=128):
    x, y = cx, cy
    while 0 <= x < a.shape[1] and 0 <= y < a.shape[0] and a[y, x] <= th:
        x += dx
        y += dy
    inner = x if dx else y
    while 0 <= x < a.shape[1] and 0 <= y < a.shape[0] and a[y, x] > th:
        x += dx
        y += dy
    return inner, (x - dx if dx else y - dy)


def openings(frame_im, body_im):
    """the openings the game draws into, measured: the art window tube's inner edges, the crest socket ring's outer
    edges, the band ring's inner edges (frame alpha > 128 walking out from each opening's centre) and the body's
    window hole"""
    a = np.asarray(frame_im)[..., 3].astype(int)
    o = {}
    o['window'] = tuple(_probe(a, 384, 400, dx, dy)[0] for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    o['socket'] = (_probe(a, 640, 576, 1, 0)[1], _probe(a, 640, 576, 0, 1)[1])
    o['band'] = tuple(_probe(a, 384, 690, dx, dy)[0] for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    b = np.asarray(body_im)[..., 3]
    lab, _ = ndimage.label(b < 16)
    ys, xs = np.where(lab == lab[400, 384])
    o['hole'] = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return o


def opening_problems(built, root=None):
    out = []
    body_new = built['i_tod_card2_body'][0]
    body_old = parked('i_tod_card2_body', root)
    for r in RARITIES:
        n = 'i_tod_card2_frame_' + r
        want = openings(parked(n, root), body_old)
        got = openings(built[n][0], body_new)
        for k in want:
            d = max(abs(a - b) for a, b in zip(want[k], got[k]))
            if d > OPEN_TOL:
                out.append('%s: the %s opening moved %s -> %s (more than %.1f px from the shipped art)'
                           % (n, k, want[k], got[k], OPEN_TOL))
    return out


def _installer(root=None):
    for r in ([root] if root else []) + [REPO]:
        p = os.path.join(r, 'tools', 'card_pull', 'install_card_art.py')
        if os.path.isfile(p):
            spec = importlib.util.spec_from_file_location('install_card_art_r10', p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise SystemExit('r10: tools/card_pull/install_card_art.py not found')


def layout_problems(built, root=None):
    """the installer's own keep-clear / see-through / neutral-back rules, on the generated layers"""
    ica = _installer(root)
    out = []
    for name in ['i_tod_card2_body', 'i_tod_card2_back'] + ['i_tod_card2_frame_' + r for r in RARITIES]:
        out += ica.layout_warnings(name, built[name][0])
    return out


def back_problems(im, grid=None):
    """THE FALLEN BACK HAS NO OUTRUN SUN (RT review 2026-10-05). grid=None reads LOOK['grid'] (True = synthwave:
    the sun is the design, nothing to check). Measured left of the spire inside where the disc sat (x 202..230,
    y 575..715): the slit rows are DIPS of the row luminance below its +-12-row median. The disc is a lift of the
    disc's upper left (x 170..230, y 400..540: clear of the halo ring and the spire's glow) over the same rows outside
    it (x 40..80); measured 2026-10-05: synthwave +63, fallen +5."""
    if (LOOK['grid'] if grid is None else grid):
        return []
    a = np.asarray(im.convert('RGBA')).astype(np.float64)
    L = a[..., :3].mean(-1) * a[..., 3] / 255.0
    rows = L[575:716, 202:231].mean(1)
    out = []
    dips, run = 0, 0
    for i in range(len(rows)):
        med = float(np.median(rows[max(0, i - 12):i + 13]))
        if rows[i] < med - 8.0:
            run += 1
        else:
            dips += run > 0
            run = 0
    dips += run > 0
    if dips >= 3:
        out.append('i_tod_card2_back: %d dark slit rows behind the spire - the synthwave sun on the FALLEN back' % dips)
    lift = float(np.median(L[400:540, 170:230])) - float(np.median(L[400:540, 40:80]))
    if lift > 15.0:
        out.append('i_tod_card2_back: a bright disc behind the spire (+%.0f) - the synthwave sun on the FALLEN back' % lift)
    return out


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lum(rgb):
    return 0.2126 * _lin(rgb[0]) + 0.7152 * _lin(rgb[1]) + 0.0722 * _lin(rgb[2])


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def contrast_report(built):
    """WHITE CARD TEXT MUST READ (TodPull TEXT_WHITE on GROUND_DIM 0.34). The title sits on the LUI label (the pill
    tinted rarity x 0.34; its lower half shades to 215/255) - and, if that label ever failed to draw, on this frame's
    own well. The rarity word sits on the band pill over the body's band slot. Every ground must clear 7:1 against
    white (WCAG AAA)."""
    rows, bad = [], []
    body_im = built['i_tod_card2_body'][0]
    for r in RARITIES:
        col = RARITY_COL[r]
        lab_top = tuple(255 * v * 0.34 for v in col)
        lab_bot = tuple(255 * v * 0.34 * 215 / 255.0 for v in col)
        comp = body_im.copy()
        comp.alpha_composite(built['i_tod_card2_frame_' + r][0])
        a = np.asarray(comp).astype(np.float64)
        well_rgb = tuple(np.median(a[60:120, 120:640, :3].reshape(-1, 3), axis=0))
        band_rgb = tuple(np.median(a[668:714, 200:560, :3].reshape(-1, 3), axis=0))
        c = [contrast((255, 255, 255), x) for x in (lab_top, lab_bot, well_rgb, band_rgb)]
        rows.append((r, c))
        if min(c) < 7.0:
            bad.append('%s: white text contrast %.1f:1 < 7:1' % (r, min(c)))
    return rows, bad


def wiring_problems(root=None):
    """every output is a same-name drop-in (its GDT block and zone line already exist); the old back is retired whole"""
    import glob
    out = []
    r0 = root or REPO
    gdt = _rd(root, os.path.join('source_data', 'tod_ui_images.gdt'))
    zones = glob.glob(os.path.join(r0, 'zone_source', '*.zone')) or glob.glob(os.path.join(REPO, 'zone_source', '*.zone'))
    zone = ''.join(open(z, encoding='utf-8', errors='replace').read() for z in zones)
    for name in CARD + REEL + PULL:
        if not re.search(r'"%s"\s*\(\s*"image\.gdf"' % re.escape(name), gdt):
            out.append('%s: no GDT block in source_data/tod_ui_images.gdt' % name)
        if not re.search(r'^\s*image,%s\s*$' % re.escape(name), zone, re.M):
            out.append('%s: no zone image line' % name)
    # THE OLD BACK, RETIRED WHOLE: no GDT block, no zone line, no manifest row, no PNG in _images
    if re.search(r'"%s"\s*\(\s*"image\.gdf"' % RETIRED, gdt):
        out.append('%s: its GDT block is still in source_data/tod_ui_images.gdt (retired whole, docs/217)' % RETIRED)
    if re.search(r'^\s*image,%s\s*$' % RETIRED, zone, re.M):
        out.append('%s: still zoned (run the staged install_card_art.py)' % RETIRED)
    man = _rd(root, os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodCardArt.lua'))
    if RETIRED in man:
        out.append('%s: still in the TodCardArt.lua manifest (run the staged install_card_art.py)' % RETIRED)
    if os.path.isfile(os.path.join(r0, IMG_REL, RETIRED + '.png')):
        out.append('%s.png is still in _images (move it to archive/map1_carryover/)' % RETIRED)
    return out

# =========================================================================================== review
REVIEW_ART = {'common': 'i_tod_card2_art_luck', 'rare': 'i_tod_card2_art_bounty', 'epic': 'i_tod_card2_art_deadeye',
              'legendary': 'i_tod_card2_art_grapple'}
REVIEW_TEXT = {'common': ('LUCK', 'LUCK BAR FILLS FASTER', 'BETTER CARDS SOONER'),
               'rare': ('BOUNTY', 'MORE POINTS PER KILL', 'UP TO DOUBLE AT LV9'),
               'epic': ('DEADEYE', 'YOUR BOWS HIT HARDER', 'FATTER ARROWS'),
               'legendary': ('GRAPPLE', 'PULL YOURSELF IN', 'FASTER AT LV9')}


def _tint(im, rgb):
    a = np.asarray(im).astype(np.float64)
    a[..., :3] *= np.array(rgb)[None, None, :]
    return Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8), 'RGBA')


def stacked_card(get, r, pill):
    """the card as TodPull.lua stacks it: illustration -> body -> frame -> crest -> title label (pill x rarity x 0.34)
    -> white title; band pill + white rarity word; two lines of text - all in our typeface"""
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    art = Image.open(artgen.shipped(REVIEW_ART[r])).convert('RGBA').resize(
        (int(round(176 * CARD_K)), int(round(136 * CARD_K))), Image.LANCZOS)
    c.alpha_composite(art, (int(round(29 * CARD_K)), int(round(54 * CARD_K))))
    c.alpha_composite(get('i_tod_card2_body'))
    c.alpha_composite(get('i_tod_card2_frame_' + r))
    cr = get('i_tod_card2_crest_' + r).resize((int(round(44 * CARD_K)), int(round(44 * CARD_K))), Image.LANCZOS)
    c.alpha_composite(cr, (int(round(173 * CARD_K)), int(round(153 * CARD_K))))
    dim = tuple(v * 0.34 for v in RARITY_COL[r])
    lw, lh = int(round(LABEL[2] - LABEL[0])), int(round(LABEL[3] - LABEL[1]))
    c.alpha_composite(_tint(pill.resize((lw, lh), Image.LANCZOS), dim), (int(round(LABEL[0])), int(round(LABEL[1]))))
    c.alpha_composite(_tint(pill.resize((int(round(128 * CARD_K)), int(round(17 * CARD_K))), Image.LANCZOS), dim),
                      (int(round(53 * CARD_K)), int(round(202 * CARD_K))))
    t, l1, l2 = REVIEW_TEXT[r]
    artgen.typeset(c, t, 16 * CARD_K, (LABEL[1] + LABEL[3]) / 2 + 8 * CARD_K, cx=W / 2.0)
    artgen.typeset(c, ['COMMON', 'RARE', 'EPIC', 'LEGENDARY'][RARITIES.index(r)] + ' +%d' % (RARITIES.index(r) + 1),
                   12 * CARD_K, 216.5 * CARD_K, cx=W / 2.0)
    artgen.typeset(c, l1, 12.5 * CARD_K, 258 * CARD_K, cx=W / 2.0)
    artgen.typeset(c, l2, 11.9 * CARD_K, 276 * CARD_K, cx=W / 2.0, rgb=(189, 204, 237))
    return c


def _label(im, text, x, y, size=26, fill=(230, 226, 245)):
    ImageDraw.Draw(im).text((x, y), text, fill=fill, font=artgen.ttf(size))


def review(built, root=None, out_dir=OUT):
    """_review.png: OLD | NEW at 1:1 - each rarity's card stacked as the game stacks it, the bare body, the back.
    _review_parts.png: the crests (1:1, 2x, the ladder's 27 px), the pill, the reel tiles / stamp OLD | NEW (1:1 and the
    reel's 1080p sizes)."""
    pill_new = None
    for rr in ([root] if root else []) + [REPO]:
        q = os.path.join(rr, IMG_REL, 'i_tod_pull_pill.png')
        if os.path.isfile(q):
            pill_new = Image.open(q).convert('RGBA')
            break
    pill_old = parked('i_tod_pull_pill', root)
    new = lambda n: built[n][0] if n in built else Image.open(artgen.shipped(n)).convert('RGBA')
    old = lambda n: parked(n, root)
    bg = (24, 18, 36, 255)
    G = 40
    rows = [('THE PULL card, %s: OLD (shipped) | NEW (R10), 1:1 - the layers stacked as TodPull.lua stacks them' % r.upper(),
             stacked_card(old, r, pill_old), stacked_card(new, r, pill_new)) for r in RARITIES]
    rows.append(('i_tod_card2_body bare (the window, the crest socket, the slots): OLD | NEW', old('i_tod_card2_body'),
                 new('i_tod_card2_body')))
    rows.append(('i_tod_card2_back: OLD | NEW (neutral - the game glows it in the rung colour)', old('i_tod_card2_back'),
                 new('i_tod_card2_back')))
    sheet = Image.new('RGBA', (W * 2 + G * 3, len(rows) * (H + 60) + G), bg)
    y = G + 20
    for title, a, b in rows:
        _label(sheet, title, G, y - 40, 24)
        sheet.alpha_composite(a, (G, y))
        sheet.alpha_composite(b, (W + G * 2, y))
        y += H + 60
    p1 = os.path.join(out_dir, '_review.png')
    sheet.convert('RGB').save(p1)
    # the parts
    Wp = 2 * 1600 + 3 * G
    sheet = Image.new('RGBA', (Wp, 3400), bg)
    y = G + 30
    _label(sheet, 'CRESTS: OLD | NEW at 1:1 (144), at 2x, and at the ladder\'s 27 px (OLD then NEW)', G, y - 40, 24)
    for i, r in enumerate(RARITIES):
        x = G + i * 760
        o, n = old('i_tod_card2_crest_' + r), new('i_tod_card2_crest_' + r)
        sheet.alpha_composite(o, (x, y))
        sheet.alpha_composite(n, (x + 160, y))
        sheet.alpha_composite(o.resize((288, 288), Image.LANCZOS), (x, y + 160))
        sheet.alpha_composite(n.resize((288, 288), Image.LANCZOS), (x + 300, y + 160))
        sheet.alpha_composite(o.resize((27, 27), Image.LANCZOS), (x + 330, y + 40))
        sheet.alpha_composite(n.resize((27, 27), Image.LANCZOS), (x + 370, y + 40))
    y += 500
    _label(sheet, 'i_tod_pull_pill (the title label + rarity band, tinted rarity x 0.34 by the game): OLD | NEW', G, y - 40, 24)
    for i, p in enumerate((pill_old, pill_new)):
        sheet.alpha_composite(_tint(p, tuple(v * 0.34 for v in RARITY_COL['legendary'])), (G + i * 480, y))
    y += 140
    _label(sheet, 'THE REEL: OLD | NEW at 1:1, and at the reel\'s 1080p 210 x 156 (OLD over NEW). The CURSED tile is '
                  'tools/dealer_house/make_spin_art.py\'s own cut of the new LEGENDARY tile.', G, y - 40, 24)
    cursed_new = None
    for rr in ([root] if root else []) + [REPO]:
        q = os.path.join(rr, IMG_REL, 'i_tod_spin_tile_cursed.png')
        if rr != REPO and os.path.isfile(q):
            cursed_new = Image.open(q).convert('RGBA')
            break
    pairs = [(old('i_tod_spin_tile_epic'), new('i_tod_spin_tile_epic')),
             (old('i_tod_spin_tile_legendary'), new('i_tod_spin_tile_legendary'))]
    if cursed_new is not None:
        pairs.append((old('i_tod_spin_tile_cursed'), cursed_new))
    for i, (o, nw) in enumerate(pairs):
        x = G + (i % 2) * 1620
        yy = y + (i // 2) * 460
        sheet.alpha_composite(o, (x, yy))
        sheet.alpha_composite(nw, (x + 580, yy))
        sheet.alpha_composite(o.resize((210, 156), Image.LANCZOS), (x + 1160, yy))
        sheet.alpha_composite(nw.resize((210, 156), Image.LANCZOS), (x + 1160, yy + 180))
    y += 460 * ((len(pairs) + 1) // 2) + 40
    _label(sheet, 'i_tod_spin_banner_epic: OLD / NEW at 1:1, then at the reel\'s 1080p 780 x 102', G, y - 40, 24)
    o, nw = old('i_tod_spin_banner_epic'), new('i_tod_spin_banner_epic')
    sheet.alpha_composite(o, (G, y))
    sheet.alpha_composite(nw, (G, y + 220))
    sheet.alpha_composite(o.resize((780, 102), Image.LANCZOS), (G + 1640, y))
    sheet.alpha_composite(nw.resize((780, 102), Image.LANCZOS), (G + 1640, y + 120))
    y += 460
    sheet = sheet.crop((0, 0, Wp, y + G))
    p2 = os.path.join(out_dir, '_review_parts.png')
    sheet.convert('RGB').save(p2)
    return p1, p2

def selftest(root=None):
    """NEGATIVE CONTROLS: every gate must catch its own failure (the shipped art is the fixture)"""
    fails = []
    body_old = parked('i_tod_card2_body', root)
    fr = parked('i_tod_card2_frame_rare', root)
    built = {'i_tod_card2_body': (body_old, b'')}
    for r in RARITIES:
        built['i_tod_card2_frame_' + r] = (parked('i_tod_card2_frame_' + r, root), b'')
    if opening_problems(built, root):
        fails.append('the shipped frames do not pass their own opening probe')
    moved = Image.fromarray(np.roll(np.asarray(fr), 5, axis=1), 'RGBA')
    built['i_tod_card2_frame_rare'] = (moved, b'')
    if not opening_problems(built, root):
        fails.append('a frame shifted 5 px passed the opening probe')
    import tempfile
    tmpd = tempfile.mkdtemp(prefix='r10_selftest_')          # writes nothing under the repo
    os.makedirs(os.path.join(tmpd, IMG_REL), exist_ok=True)
    parked('i_tod_pull_pill', root).save(os.path.join(tmpd, IMG_REL, 'i_tod_pull_pill.png'))
    if not pill_problems(tmpd):
        fails.append('the old ROUNDED pill passed the chamfer check')
    ica = _installer(root)
    tinted = Image.fromarray(np.clip(np.asarray(back()).astype(int) * np.array([1.0, 0.55, 0.2, 1.0]), 0, 255).astype(np.uint8), 'RGBA')
    if not ica.layout_warnings('i_tod_card2_back', tinted):
        fails.append('a gold-tinted back passed the installer\'s neutral-back rule')
    bright = {'i_tod_card2_body': (body_old, b'')}
    for r in RARITIES:
        bright['i_tod_card2_frame_' + r] = (parked('i_tod_card2_frame_' + r, root), b'')
    if not contrast_report(bright)[1]:
        fails.append('the shipped BRIGHT title plates passed the 7:1 bare-well contrast floor')
    was = LOOK['grid']
    LOOK['grid'] = True                                      # the synthwave back (sun + slits + floor) ...
    try:
        sun_back = back()
    finally:
        LOOK['grid'] = was
    if not back_problems(sun_back, grid=False):              # ... must fail the FALLEN rule
        fails.append('a back with the outrun sun and its slit rows passed the fallen no-sun rule')
    if back_problems(back(), grid=False) and not was:
        fails.append('this theme\'s fallen back fails its own no-sun rule')
    if not stamp_problems(parked(STAMP_NAME, root), theme='fallen'):
        fails.append('the delivered ribbon (tails + studs) passed the fallen stamp rule')
    if THEME != 'synthwave' and stamp_problems(pull_banner(root)[0]):
        fails.append('this theme\'s stamp fails its own rule: %s' % stamp_problems(pull_banner(root)[0])[0])
    for f in fails:
        print('R10 SELFTEST FAIL: ' + f)
    if fails:
        sys.exit(1)
    print('R10 SELFTEST OK: a 5 px shifted frame, the rounded pill, a tinted back, the bright shipped plates, a sun on '
          'the fallen back and the ribbon stamp under the fallen rule are all caught')

# ============================================================================================= main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--stage', help='also write DIR/source_data/tod_ui_images/_images/')
    ap.add_argument('--install', action='store_true', help='LANDING ONLY: write into source_data/tod_ui_images/_images')
    ap.add_argument('--check', action='store_true', help='regenerate in memory; fail on any difference (the build gate)')
    ap.add_argument('--root', help='the tree --check reads and the parked sources are found in (default: the repo)')
    ap.add_argument('--only', help='comma list of names (iteration only; never with --check)')
    ap.add_argument('--no-review', action='store_true')
    ap.add_argument('--selftest', action='store_true', help='negative controls: each gate must catch its failure')
    a = ap.parse_args()
    root = os.path.abspath(a.root) if a.root else None
    if a.selftest:
        selftest(root)
        return
    if a.check:
        built = build_all(root)
        bad = []
        img_dir = os.path.join(root or REPO, IMG_REL)
        for name, (im, data) in built.items():
            p = os.path.join(img_dir, name + '.png')
            if not os.path.isfile(p):
                bad.append('MISSING %s' % p)
            elif open(p, 'rb').read() != data:
                bad.append('STALE %s (re-run the generator; never hand-edit it)' % p)
        bad += lockstep_problems(root) + pill_problems(root) + opening_problems(built, root) + layout_problems(built, root)
        bad += contrast_report(built)[1] + wiring_problems(root) + back_problems(built['i_tod_card2_back'][0])
        bad += stamp_problems(built[STAMP_NAME][0])
        for msg in bad:
            print('R10 CARD CHROME: %s' % msg)
        if bad:
            sys.exit(1)
        print('R10 CARD CHROME OK %d images + openings, hues, label/pill chamfer, keep-clear, contrast, wiring (%s)'
              % (len(built), root or 'repo'))
        return
    only = a.only.split(',') if a.only else None
    built = build_all(root, only)
    os.makedirs(OUT, exist_ok=True)
    for name, (im, data) in built.items():
        with open(os.path.join(OUT, name + '.png'), 'wb') as fh:
            fh.write(data)
        print('%-34s %s' % (name, hashlib.md5(data).hexdigest()))
    if only:
        return
    for msg in lockstep_problems(root) + opening_problems(built, root) + layout_problems(built, root):
        print('  PROBLEM: ' + msg)
    rows, bad = contrast_report(built)
    for r, c in rows:
        print('  contrast %-10s white on label top %.1f / label foot %.1f / bare well %.1f / band slot %.1f' % ((r,) + tuple(c)))
    for msg in bad:
        print('  PROBLEM: ' + msg)
    if a.stage:
        d = os.path.join(os.path.abspath(a.stage), IMG_REL)
        os.makedirs(d, exist_ok=True)
        for name, (im, data) in built.items():
            with open(os.path.join(d, name + '.png'), 'wb') as fh:
                fh.write(data)
        print('staged %d images -> %s' % (len(built), d))
    if a.install:
        for name, (im, data) in built.items():
            with open(os.path.join(REPO, IMG_REL, name + '.png'), 'wb') as fh:
                fh.write(data)
        print('installed %d images into %s' % (len(built), os.path.join(REPO, IMG_REL)))
    if not a.no_review:
        for p in review(built, root):
            print('review ->', p)


if __name__ == '__main__':
    main()


