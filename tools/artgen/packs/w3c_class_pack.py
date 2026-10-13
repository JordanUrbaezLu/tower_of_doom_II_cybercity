"""w3c_class_pack.py - THE CLASS EMBLEM PACK: four class emblems drawn ONE way (2026-10-05, wave 3 item 3).

User 2026-10-05: "Class icons can be improved and I dont want that red fill on top left. Lets also make them look
like they come from same pack. Might mean making it from scratch but necromancer doesnt look like a consistent
design to the others."

WHAT WAS WRONG (measured on the shipped files, tmp/wave3/W3C-class-pack/LAND.md):
  - every i_tod_class_medallion_* disc carried a RED / magenta arc baked over its top-left quarter (Map One's
    ring), a round disc nested inside the R4 OCTAGON ring;
  - the Archer / Breacher / Warrior glyphs were thin tinted line art with no white core, the Necromancer a FILLED
    bright-green skull with three crystals breaking out of its own ring - two different packs;
  - the deal panel's i_tod_upg_class_* plates still wore Map One's hazard stripes beside R4's synthwave luck badge.

THE PACK. One construction for all four, the R4 library's own grammar (tools/artgen/packs/r4_synthwave_hud.py,
whose compositor and plate geometry are IMPORTED, never copied, so the pack cannot drift from the library):
  - a black-glass OCTAGON plate whose edge runs parallel to the R4 medallion ring's inner hairline (the HUD draws
    the medallion inside that ring at 84%: AetheriumPlayerInfo.lua 28.5..75.5 inside 24..80), so in the ring the
    glass meets the ring band with no gap, and alone (the teammate rows draw it ringless) it is a whole badge;
  - ONE neon tube in the class's identity hue - the exact accent the class select tints its live text with
    (tod_class_select.lua CLASSES[].accent; --check fails if the two drift);
  - the class SYMBOL as an R4 neon glyph: white-hot ink for the OBJECT, the hue for its ENERGY (the one accent
    part), a soft hue halo. Same stroke weights (34 px primary / 18 px secondary at 512), same glyph budget, the
    ink mass of the four equalised by measurement (printed on every run):
        ARCHER       a drawn recurve bow, the arrow nocked - arrowhead + fletching are the energy
        BREACHER     a shotgun shell - the breaching blast bursting from its crimp is the energy
        WARRIOR      a cyber sword - the slash arc it cuts is the energy
        NECROMANCER  a skull - its eyes and the three soul wisps leaving it are the energy
    No red or magenta arc anywhere on a medallion; nothing outside the octagon - the tube's halo is clipped to the
    glass, and build_all() refuses any image whose outermost pixels carry more than EDGE_ALPHA_MAX alpha.
  - the deal-panel plate (420 x 90, drawn 1:1 at 1080p as the luck badge's mirror) is the R4 luck badge's plate
    (r4.LB, its side edges 4 px in so its halo stays inside the image) with the MEDALLION ITSELF where the luck badge
    has its clover well, and CLASS <NAME> in our typeface in the luck badge's text slot, the name in neon.

Same names, same sizes: a drop-in, no wiring. The landing adds this file's --check to tools/build_map.ps1.

  python tools/artgen/packs/w3c_class_pack.py                 # -> art/generated/W3C-class-pack/ + review sheets
  python tools/artgen/packs/w3c_class_pack.py --stage         # + tmp/wave3/W3C-class-pack/stage/ (+ base/)
  python tools/artgen/packs/w3c_class_pack.py --install       # LANDING ONLY: copy into source_data/tod_ui_images/_images
  python tools/artgen/packs/w3c_class_pack.py --check         # regenerate in memory; fail on any byte != installed, a
                                                              # missing GDT block / zone line, a Lua that stopped drawing
                                                              # these names, or a class accent that moved
  python tools/artgen/packs/w3c_class_pack.py --check --against stage

Deterministic: no randomness at all, no timestamps. Never hand-edit a generated PNG.
"""
import argparse, glob, hashlib, math, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import artgen  # noqa: E402
from synthwave import (Svg, poly_d, line_d, inset, mix, put_text, neon_word, text_width, clip_to)  # noqa: E402
import r4_synthwave_hud as r4  # noqa: E402  (the library: neon_glyph, coverage, layered, bevel, LB / LB_WELL)
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

PACK = 'W3C-class-pack'
ROOT = artgen.ROOT
WAVE = os.path.join(ROOT, 'tmp', 'wave3', PACK)
STAGE_ROOT = os.path.join(WAVE, 'stage')
BASE_ROOT = os.path.join(WAVE, 'base')
IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')
STAGE_IMG = os.path.join(STAGE_ROOT, IMG_REL)
BASE_IMG = os.path.join(BASE_ROOT, IMG_REL)
OUT = os.path.join(ROOT, 'art', 'generated', PACK)
SELECT_LUA = os.path.join('ui', 'uieditor', 'menus', 'hud', 'tod_class_select.lua')
UPG_LUA = os.path.join('ui', 'uieditor', 'menus', 'hud', 'tod_upgrade.lua')
CHARS_LUA = os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'Mappings', 'AetheriumCharacters.lua')

# (file key, the class's name on screen, its class id, its identity hue). The hue is tod_class_select.lua's
# CLASSES[id].accent (the live tint of the class's role and weapon text) to the byte: --check re-reads it.
CLASSES = [
    ('assault', 'ARCHER', 2, (1.00, 0.75, 0.25)),
    ('heavy', 'BREACHER', 3, (1.00, 0.35, 0.30)),
    ('slasher', 'WARRIOR', 4, (0.75, 0.45, 1.00)),
    ('necromancer', 'NECROMANCER', 1, (0.55, 1.00, 0.45)),
]


def hue_hex(acc):
    return '#%02X%02X%02X' % tuple(int(round(v * 255)) for v in acc)


HUE = {k: hue_hex(a) for k, _, _, a in CLASSES}
NAME = {k: n for k, n, _, _ in CLASSES}

# ==================================================================================== the octagon
# AetheriumPlayerInfo.lua: the ring 24..80 x 620..676 (256 art = 4.571 px per canvas unit), the medallion
# 28.5..75.5 -> ring art 20.57..235.43. R4's MR_I = octagon(20, 20, 236, 236, 60) is the ring's inner hairline;
# mapped into the medallion's 512 frame it is the medallion's own edge. The plate runs PARALLEL to it, 3 px in.
M = 512
RING_PX = 256.0 / (80 - 24)                       # ring art px per canvas unit
MED_A0 = (28.5 - 24) * RING_PX                    # 20.57: where the medallion starts in ring art
MED_K = M / ((75.5 - 28.5) * RING_PX)             # medallion px per ring-art px (2.383)


def ring_to_med(v):
    return (v - MED_A0) * MED_K


RING_INNER = r4.octagon(ring_to_med(20), ring_to_med(20), ring_to_med(236), ring_to_med(236), 60 * MED_K)
PLATE = inset(RING_INNER, 6.4)                    # the glass: its straight sides 5 px inside the canvas, so neither
                                                  # its steel hairline nor the resampling filter's reach touches the
                                                  # outermost pixels (in the ring that is a 0.4 px seam, unseen)
TUBE = inset(PLATE, 28.0)                         # the class tube (the HUD reads it ~4 px inside the ring)
INNER = inset(TUBE, 20.0)                         # the faint inner line (the R4 tokens' second line)
TUBE_W = 16.0                                     # 2.2 px at the HUD's 70 px, 1.6 px in a teammate row

# ===================================================================================== svg helpers
def F(d):
    return '<path d="%s" fill="#fff"/>' % d


def ST(d, w, cap='round', join='round'):
    return ('<path d="%s" fill="none" stroke="#fff" stroke-width="%.2f" stroke-linecap="%s" stroke-linejoin="%s"/>'
            % (d, w, cap, join))


def P(pts):
    return F(poly_d(pts))


def CI(cx, cy, r):
    return '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="#fff"/>' % (cx, cy, r)


def EL(cx, cy, rx, ry, ang=0.0):
    return ('<ellipse cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f" transform="rotate(%.2f %.2f %.2f)" fill="#fff"/>'
            % (cx, cy, rx, ry, ang, cx, cy))


def cubic(p0, p1, p2, p3, n=48):
    out = []
    for i in range(n + 1):
        t = i / float(n)
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def ribbon(pts, width):
    """A tapered stroke as ONE filled polygon: pts along the spine, width(t) its width at t in 0..1."""
    n = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(0, i - 1)]
        x1, y1 = pts[min(n - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        h = width(i / float(n - 1)) / 2.0
        left.append((x + nx * h, y + ny * h))
        right.append((x - nx * h, y - ny * h))
    return poly_d(left + right[::-1])


def arc_pts(cx, cy, r, a0, a1, n=48):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / float(n))),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / float(n)))) for i in range(n + 1)]

# ================================================================================ THE FOUR SYMBOLS
# Each is drawn in its own LOCAL frame (origin = the symbol's centre, units = medallion px) and returned as
# dict(white, acc, cut, gap, pupil, place=(dx, dy, rotate, scale)). The same weights everywhere:
W1 = 34.0      # primary stroke / limb (4.7 px at the HUD's 70 px)
W2 = 18.0      # secondary stroke (string, shaft)
WC = 12.0      # a cut (a dark gap that draws a detail)


def sym_archer():
    """A drawn recurve bow, the arrow nocked, pointing up-right. Object = bow + shaft (white); energy = the
    broadhead and the fletching (hue)."""
    A, B = (-46, -172), (-46, 172)
    limb = cubic(A, (74, -132), (74, 132), B, 64)
    taper = lambda t: 18.0 + (W1 + 14 - 18.0) * math.sin(math.pi * t) ** 0.9
    white = F(ribbon(limb, taper))
    # recurve tips: each limb flicks forward at its end
    white += F(ribbon(cubic(A, (-60, -182), (-58, -200), (-36, -212), 16), lambda t: 18.0 - 6.0 * t))
    white += F(ribbon(cubic(B, (-60, 182), (-58, 200), (-36, 212), 16), lambda t: 18.0 - 6.0 * t))
    nock = (-120, 0)
    white += ST(line_d(A, nock, B), 15, cap='round', join='miter')
    white += ST(line_d((-128, 0), (112, 0)), W2 + 4, cap='butt')                   # the shaft
    head = [(100, -40), (192, 0), (100, 40), (120, 0)]
    vane_u = [(-76, -10), (-126, -10), (-154, -46), (-104, -46)]
    vane_d = [(x, -y) for x, y in vane_u]
    acc = P(head) + P(vane_u) + P(vane_d)
    return dict(white=white, acc=acc, cut='', gap=P(vane_u) + P(vane_d), pupil='', place=(20, -22, -45, 0.86))


def sym_breacher():
    """A shotgun shell, crimp up-right. Object = the shell (white, its brass head drawn with cut bands); energy =
    the breaching blast bursting from the crimp + three pellets (hue)."""
    white = P(r4.chamfer(-150, -62, -136, 62, tl=7, bl=7))                         # the rim
    white += P(r4.chamfer(-136, -55, -94, 55))                                     # the brass head
    white += P([(-94, -50), (22, -50), (44, -32), (44, 32), (22, 50), (-94, 50)])   # the hull + its crimp
    cut = (ST(line_d((-94, -70), (-94, 70)), WC, cap='butt')                       # head | hull
           + ST(line_d((-118, -70), (-118, 70)), 8, cap='butt')                    # the head's band
           + ST(line_d((-74, -17), (6, -17)), 9, cap='butt')                       # the hull's two ribs
           + ST(line_d((-74, 17), (6, 17)), 9, cap='butt')
           + ST(line_d((22, -50), (34, 0), (22, 50)), 8, cap='butt', join='miter'))  # the crimp fold
    # the blast: an 11-point starburst, long and short rays alternating (no randomness - the --check gates bytes)
    cx, cy = 118, 0
    pts = []
    n = 11
    for i in range(n * 2):
        a = math.radians(-90 + i * 180.0 / n + 8)
        r = (88 if i % 4 == 0 else 70) if i % 2 == 0 else 36
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    blast = P(pts)
    pellets = CI(200, -58, 13) + CI(214, 2, 13) + CI(194, 60, 13)
    return dict(white=white, acc=blast + pellets, cut=cut, gap=blast, pupil='', place=(-22, 20, -45, 0.98))


def sym_warrior():
    """The Warrior's cyber sword, point up-right. Object = the sword (white core, cut fuller and grip wraps); energy =
    the blade's cutting edge, a lit rim all round the blade (hue). (Review, 2026-10-05: a slash arc beside the
    sword read as a moon, a scythe or a second claw blade at every shape tried - the energy belongs ON the blade.)"""
    blade = [(-40, -36), (132, -36), (200, 0), (132, 36), (-40, 36)]
    guard = [(-72, -92), (-58, -104), (-42, -104), (-42, 104), (-58, 104), (-72, 92)]
    grip = r4.chamfer(-150, -18, -72, 18)
    pommel = [(-152, 0), (-174, -28), (-202, 0), (-174, 28)]
    core = inset(blade, 15.0)
    white = P(core) + P(guard) + P(grip) + P(pommel)
    acc = F(poly_d(blade) + ' ' + poly_d(list(reversed(core))))                 # the edge: blade minus its core
    cut = (ST(line_d((-28, 0), (118, 0)), 10, cap='butt')                          # the fuller
           + ''.join(ST(line_d((x, -24), (x, 24)), 7, cap='butt') for x in (-90, -111, -132)))
    return dict(white=white, acc=acc, cut=cut, gap='', pupil='', place=(3, -3, -45, 0.97))


def sym_necromancer():
    """A skull, front on. Object = the skull (white, cut sockets / nose / teeth); energy = its eyes and the three
    soul wisps leaving it (hue)."""
    white = (CI(0, -26, 92)
             + P([(-82, -18), (82, -18), (70, 48), (-70, 48)])
             + P(r4.chamfer(-54, 40, 54, 98, bl=14, br=14)))
    sock = P([(-70, -14), (-14, -4), (-20, 30), (-62, 26)])
    sockR = P([(70, -14), (14, -4), (20, 30), (62, 26)])
    nose = P([(0, 30), (-11, 52), (11, 52)])
    teeth = ''.join(ST(line_d((x, 62), (x, 104)), 8, cap='butt') for x in (-24, 0, 24)) \
        + ST(line_d((-60, 72), (60, 72)), 6, cap='butt')
    pupils = CI(-40, 10, 13) + CI(40, 10, 13)
    # three SOULS rise off the crown: each a round head trailing a wavy tail that thins to nothing toward the skull
    # (tails, not tongues: rooted flames curling outward read as horns)
    wisp = ''
    for sx, hx, hy, tx, ty in ((0, 0, -222, 2, -136), (-1, -70, -186, -38, -124), (1, 70, -186, 38, -124)):
        w = 22 if sx == 0 else 20
        wig = 26 if sx >= 0 else -26
        spine = cubic((hx, hy), (hx + wig, hy + (ty - hy) * 0.35), (tx - wig, hy + (ty - hy) * 0.7), (tx, ty), 40)
        wisp += F(ribbon(spine, lambda t, w=w: (2 * w) * (1.0 - t) ** 1.1 + 2.0)) + CI(hx, hy, w + 2)
    return dict(white=white, acc=wisp, cut=sock + sockR + nose + teeth, gap=wisp, pupil=pupils, place=(0, 36, 0, 0.9))


SYMBOLS = {'assault': sym_archer, 'heavy': sym_breacher, 'slasher': sym_warrior, 'necromancer': sym_necromancer}


def placed(body, place, X, Y, S):
    """Wrap a local-frame svg body: the symbol's own placement, then the 512 frame into the target canvas."""
    if not body:
        return ''
    dx, dy, ang, k = place
    return ('<g transform="translate(%.3f %.3f) scale(%.5f) translate(%.3f %.3f) rotate(%.3f) scale(%.5f)">%s</g>'
            % (X, Y, S, M / 2.0 + dx, M / 2.0 + dy, ang, k, body))


def glyph_layer(key, W, H, X=0.0, Y=0.0, S=1.0, sigma=14.0, k=0.8):
    """The class symbol as an R4 neon glyph on a W x H canvas, its 512 frame placed at (X, Y) scaled S."""
    s = SYMBOLS[key]()
    pl = s['place']
    wc = r4.coverage(W, H, placed(s['white'], pl, X, Y, S))
    ac = r4.coverage(W, H, placed(s['acc'], pl, X, Y, S))
    cc = r4.coverage(W, H, placed(s['cut'], pl, X, Y, S)) if s['cut'] else np.zeros_like(wc)
    if s['gap']:                                   # a dark gap in the white ink where the energy crosses it
        gpx = max(1.0, 9.0 * S)
        wc = wc * (1.0 - r4.halo_of(r4.coverage(W, H, placed(s['gap'], pl, X, Y, S)), gpx))
    if s['pupil']:                                 # lit eyes inside cut sockets: cut minus pupil, pupil = accent
        pc = r4.coverage(W, H, placed(s['pupil'], pl, X, Y, S))
        cc = np.clip(cc - pc, 0.0, 1.0)
        ac = np.clip(ac + pc, 0.0, 1.0)
        wc = wc * (1.0 - pc)
    return r4.neon_glyph(wc, ac, HUE[key], sigma=sigma * S, k=k, cut_cov=cc, acc_lift=0.22), (wc, ac, cc)

# ===================================================================================== the medallion
def medallion(key):
    hue = HUE[key]

    def base(s):
        s.plate(PLATE, 'token', top=mix(hue, 'token', 0.82))
        s.path(poly_d(PLATE), fill='url(#%s)' % s.rad([(0, hue, 0.15), (1, hue, 0.0)], 0.5, 0.36, 0.6))
        s.steel(PLATE, 3.0)
        r4.bevel(s, PLATE, 4.4, opacity=0.5)
        s.path(poly_d(INNER), stroke=mix(hue, 'steel', 0.55), sw=3.0, opacity=0.5)

    im = r4.layered(M, M, base, None, grain_amp=0.02, seed=900 + len(key), base_alpha=0.97)
    t = Svg(M, M)
    t.tube(poly_d(TUBE), hue, TUBE_W, glow=0.85, spread=0.42)
    # the tube's halo lights the GLASS only: clipped to the plate, so nothing glows past the octagon and the image's
    # outer pixels stay clear (a halo cut by the canvas edge reads as a lit square round the badge in a teammate row,
    # which draws it with no ring over it - the perk icons' "overflow", W3A 2026-10-05)
    im.alpha_composite(clip_to(t.render(), PLATE))
    g, _ = glyph_layer(key, M, M)
    im.alpha_composite(g)
    return im


def ink_mass(key):
    """The symbol's visible ink (white + accent - cuts) as a fraction of the tube's area: the pack's balance."""
    _, (wc, ac, cc) = glyph_layer(key, M, M)
    ink = np.clip(wc + ac, 0, 1) * (1.0 - cc)
    tube_area = r4.coverage(M, M, F(poly_d(TUBE))).sum()
    return float(ink.sum() / tube_area)

# ====================================================================================== the deal plate
# tod_upgrade.lua ClassBadge: 50..330 x 150..210 canvas = the 420 x 90 art at 1:1 on a 1080p screen, the luck badge's
# mirror (LuckBadge 950..1230 at the same height). Its plate is R4's luck-badge plate (r4.LB) to the pixel; the medallion
# sits where the luck badge's clover well sits (r4.LB_WELL x 13..79), 66 px, and the name runs where LUCK n% BOOSTED does.
PL_W, PL_H = 420, 90
PL_MED = (17, 12, 66)                              # x, y, size of the medallion in the plate
PL_TEXT_CX, PL_TEXT_BASE, PL_TEXT_CAP, PL_TEXT_FIT = 247, 56, 25.0, 306     # r4.luck_badge's text slot, by number
PL_WORD_GAP = 2.2
# r4.LB is chamfer(4, 8, 416, 82, tl=14, br=14): its side tubes sit 4 px from the canvas edge, where their halo is cut
# at 57..64/255 (a hard vertical line at 4x). This plate keeps LB's height, cuts and tube, and takes the side edges in
# by 4 px, so every side has the 8 px margin the top and bottom already have (border alpha <= 4/255, W3A's rule).
PL_OUT = r4.chamfer(8, 8, 412, 82, tl=14, br=14)


def class_plate(key, med=None):
    hue = HUE[key]
    LB = PL_OUT

    def base(s):
        s.plate(LB, 'badge_fill', top='badge_top')
        s.steel(LB, 1.8)
        r4.bevel(s, LB, 2.4)

    def top(s):
        s.tube(poly_d(LB), hue, 2.6, glow=0.8, spread=0.36)    # STYLE.md 3: 0.35..0.6 on a 90 px piece; 0.42 left 6/255
                                                               # on the top and bottom rows

    im = r4.layered(PL_W, PL_H, base, None, seed=950 + len(key), base_alpha=0.95)
    # the hue wash inside the glass (the luck badge's glow_fill), clipped to the glass: its sigma-16 blur otherwise
    # bleeds 3/255 past the plate onto the canvas edge
    wash = Svg(PL_W, PL_H)
    wash.glow_fill(inset(LB, 8), hue, 0.07, 16)
    im.alpha_composite(clip_to(wash.render(), LB))
    t = Svg(PL_W, PL_H)
    top(t)
    im.alpha_composite(t.render())
    med = med if med is not None else medallion(key)
    x, y, sz = PL_MED
    im.alpha_composite(med.resize((sz, sz), Image.LANCZOS), (x, y))
    name = NAME[key]
    cap = PL_TEXT_CAP
    # the word space: the face's own space (0.30 of a cell) read as "CLASSBREACHER" once the neon halo spread into
    # it (review 2026-10-05), so this one gap is PL_WORD_GAP face spaces wide
    sp = lambda c: PL_WORD_GAP * (text_width('A A', c) - text_width('AA', c))
    gap = sp(cap)
    while cap > 14 and text_width('CLASS', cap) + gap + text_width(name, cap) > PL_TEXT_FIT:
        cap -= 0.5
        gap = sp(cap)
    wa, wb = text_width('CLASS', cap), text_width(name, cap)
    x0 = PL_TEXT_CX - (wa + gap + wb) / 2.0
    put_text(im, 'CLASS', cap, PL_TEXT_BASE, 'white', x=x0)
    neon_word(im, name, cap, PL_TEXT_BASE, hue, x=x0 + wa + gap)
    return im

# ======================================================================================== the manifest
IMAGES = ([('i_tod_class_medallion_%s' % k, 'MEDALLION', k) for k, _, _, _ in CLASSES]
          + [('i_tod_upg_class_%s' % k, 'PLATE', k) for k, _, _, _ in CLASSES])
SIZES = {'MEDALLION': (512, 512), 'PLATE': (420, 90)}
# the plates are "uncompressed" in the GDT (like r4's 420 x 90 luck badges), so 90 tall is legal; the medallions are
# "compressed high color" and must stay multiples of 4. wiring_problems() asserts both settings.
UNCOMPRESSED_KINDS = {'PLATE'}
GDT_COMPRESSION = {'MEDALLION': 'compressed high color', 'PLATE': 'uncompressed'}


EDGE_ALPHA_MAX = 4      # alpha /255 allowed on an image's outermost pixel ring: no halo is ever cut by the canvas
                        # (the same bound W3A puts on the perk shields and power-up tokens)


def edge_alpha(im):
    a = np.asarray(im)[..., 3]
    return int(max(a[0].max(), a[-1].max(), a[:, 0].max(), a[:, -1].max()))


def build_all():
    out = {}
    meds = {}
    for k, _, _, _ in CLASSES:
        meds[k] = medallion(k)
    for name, kind, k in IMAGES:
        im = meds[k] if kind == 'MEDALLION' else class_plate(k, meds[k])
        if im.size != SIZES[kind]:
            raise SystemExit('w3c: %s is %s, the shipped size is %s' % (name, im.size, SIZES[kind]))
        if kind not in UNCOMPRESSED_KINDS and (im.width % 4 or im.height % 4):
            raise SystemExit('w3c: %s %s is not a multiple of 4' % (name, im.size))
        e = edge_alpha(im)
        if e > EDGE_ALPHA_MAX:
            raise SystemExit('w3c: %s puts alpha %d/255 on its outermost pixels (max %d): a halo is cut by the canvas'
                             % (name, e, EDGE_ALPHA_MAX))
        out[name] = (im, artgen.png_bytes(im))
    return out

# ============================================================================================ wiring
def lua_accents(src):
    """{class id: (r, g, b)} from tod_class_select.lua's CLASSES table."""
    out = {}
    for cid, body in re.findall(r'\[(\d)\]\s*=\s*\{\s*name\s*=\s*"[A-Z]+".*?accent\s*=\s*\{([^}]*)\}', src, re.S):
        out[int(cid)] = tuple(float(v) for v in body.split(','))
    return out


def wiring_problems(root):
    out = []
    gdt = open(os.path.join(ROOT, 'source_data', 'tod_ui_images.gdt'), encoding='utf-8', errors='replace').read()
    zone = ''.join(open(z, encoding='utf-8', errors='replace').read()
                   for z in glob.glob(os.path.join(ROOT, 'zone_source', '*.zone')))
    for name, kind, _ in IMAGES:
        blk = re.search(r'"%s"\s*\(\s*"image\.gdf"\s*\)\s*\{(.*?)\}' % re.escape(name), gdt, re.S)
        if not blk:
            out.append('%s: no GDT block in source_data/tod_ui_images.gdt' % name)
        else:
            cm = re.search(r'"compressionMethod"\s*"([^"]*)"', blk.group(1))
            if not cm or cm.group(1) != GDT_COMPRESSION[kind]:
                out.append('%s: GDT compressionMethod is %r, this art is made for %r'
                           % (name, cm.group(1) if cm else None, GDT_COMPRESSION[kind]))
        if not re.search(r'^\s*image,%s\s*$' % re.escape(name), zone, re.M):
            out.append('%s: no zone image line' % name)

    def lua(rel):
        p = os.path.join(root, rel)
        return open(p if os.path.exists(p) else os.path.join(ROOT, rel), encoding='utf-8', errors='replace').read()
    acc = lua_accents(lua(SELECT_LUA))
    for k, n, cid, a in CLASSES:
        got = acc.get(cid)
        if got is None or any(abs(x - y) > 1e-6 for x, y in zip(got, a)):
            out.append('%s: tod_class_select.lua accent for class %d is %s, the art is baked in %s - re-run the generator'
                       % (n, cid, got, a))
    up, ch = lua(UPG_LUA), lua(CHARS_LUA)
    for k, n, cid, _ in CLASSES:
        if not re.search(r'\[%d\]\s*=\s*RegisterImage\(\s*"i_tod_upg_class_%s"\s*\)' % (cid, k), up):
            out.append('tod_upgrade.lua art.classPlate[%d] no longer draws i_tod_upg_class_%s' % (cid, k))
        if '"i_tod_class_medallion_%s"' % k not in ch:
            out.append('AetheriumCharacters.lua no longer maps a character to i_tod_class_medallion_%s' % k)
    return out

# ============================================================================================= review
WORLD = os.path.join(ROOT, 'docs', '184_synthwave_ref', 'world_city_ingame.png')
K = 1.5          # 1080p px per canvas unit


def _img(name, get):
    return get(name)


def hud_panel(get, out_path, local='heavy', party=('assault', 'slasher', 'necromancer')):
    """The bottom-left of the 1080p HUD over the city: the local player's ring + medallion (AetheriumPlayerInfo.lua,
    ring 24..80 x 620..676, medallion 28.5..75.5 x 624.5..671.5) and three teammate rows (AetheriumPartyPlayers.lua,
    portrait 45..80 x bgTop+8..+43 for bgTop 524 / 481 / 439, no ring), names / bars / points as the Lua lays them."""
    sc = Image.open(WORLD).convert('RGBA')
    ring = Image.open(artgen.shipped('i_tod_h2_medallion_ring')).convert('RGBA')
    fill = Image.open(artgen.shipped('i_tod_h2_hp_fill')).convert('RGBA')
    frame = Image.open(artgen.shipped('i_tod_h2_hp_frame')).convert('RGBA')
    pts = Image.open(artgen.shipped('i_tod_h2_points')).convert('RGBA')

    def place(im, l, t, r, b):
        sc.alpha_composite(im.resize((int(round((r - l) * K)), int(round((b - t) * K))), Image.LANCZOS),
                           (int(round(l * K)), int(round(t * K))))

    def bar(l, t, r, b, frac):
        place(r4._tint(fill, (0.06, 0.06, 0.08)), l, t, r, b)
        w = int(round((r - l) * K * frac))
        sc.alpha_composite(fill.crop((0, 0, int(fill.width * frac), fill.height)).resize((w, int(round((b - t) * K))), Image.LANCZOS),
                           (int(round(l * K)), int(round(t * K))))
        place(frame, l, t, r, b)

    for i, (k, nm) in enumerate(zip(party, ('VIPER', 'ODIN', 'MARA'))):
        top = (524, 481, 439)[i]
        place(get('i_tod_class_medallion_' + k), 45, top + 8, 80, top + 43)
        put_text(sc, nm, 12 * 0.96 * K * 0.8, (top + 18) * K, 'white', x=90 * K)
        bar(90, top + 24, 198, top + 34, (0.9, 0.55, 0.3)[i])
    place(get('i_tod_class_medallion_' + local), 28.5, 624.5, 75.5, 671.5)
    place(ring, 24, 620, 80, 676)
    put_text(sc, 'JORDAN', 11 * K, 632 * K, 'white', x=90 * K)
    bar(90, 645, 220, 657, 0.8)
    place(pts, 90, 662, 106, 678)
    put_text(sc, '4250', 13 * K, 676 * K, 'white', x=110 * K)
    crop = sc.crop((0, 600, 520, 1050))
    crop.convert('RGB').save(out_path)
    return out_path


def review_sheet(built, out_path):
    """OLD vs NEW at the sizes the game draws them (1080p) over the real city, plus the full 512 / 2x zoom."""
    font = ImageFont.truetype(artgen.TTF, 20)
    small = ImageFont.truetype(artgen.TTF, 15)
    old = lambda n: Image.open(os.path.join(BASE_IMG if os.path.isdir(BASE_IMG) and os.path.exists(os.path.join(BASE_IMG, n + '.png')) else artgen.IMG, n + '.png')).convert('RGBA')
    new = lambda n: built[n][0]
    world = Image.open(WORLD).convert('RGBA')

    def patch(w, h, seed):
        x = (seed * 211) % max(1, world.width - w)
        y = 120 + (seed * 97) % max(1, world.height - h - 240)
        return world.crop((x, y, x + w, y + h))
    rows = []
    # row 1: the four medallions, OLD then NEW, at full 512 / 2 = 256
    rows.append(('MEDALLIONS  i_tod_class_medallion_*  (512 art shown at 256)   OLD (top)  NEW (bottom)',
                 [[old('i_tod_class_medallion_' + k).resize((256, 256), Image.LANCZOS) for k, _, _, _ in CLASSES],
                  [new('i_tod_class_medallion_' + k).resize((256, 256), Image.LANCZOS) for k, _, _, _ in CLASSES]]))
    # row 2: at the real HUD sizes: in the ring (70 px) and in a teammate row (52 px)
    ring = Image.open(artgen.shipped('i_tod_h2_medallion_ring')).convert('RGBA')

    def in_ring(m):
        c = Image.new('RGBA', (84, 84), (0, 0, 0, 0))
        c.alpha_composite(m.resize((71, 71), Image.LANCZOS), (6, 6))
        c.alpha_composite(ring.resize((84, 84), Image.LANCZOS))
        return c
    rows.append(('AT 1080p: in the HUD ring (84 px ring, 70 px medallion) and a teammate row (52 px)   OLD | NEW',
                 [[in_ring(old('i_tod_class_medallion_' + k)) for k, _, _, _ in CLASSES]
                  + [old('i_tod_class_medallion_' + k).resize((52, 52), Image.LANCZOS) for k, _, _, _ in CLASSES],
                  [in_ring(new('i_tod_class_medallion_' + k)) for k, _, _, _ in CLASSES]
                  + [new('i_tod_class_medallion_' + k).resize((52, 52), Image.LANCZOS) for k, _, _, _ in CLASSES]]))
    rows.append(('DEAL PANEL PLATES  i_tod_upg_class_*  (420 x 90 = 1:1 at 1080p)   OLD | NEW',
                 [[old('i_tod_upg_class_' + k) for k, _, _, _ in CLASSES[:2]], [new('i_tod_upg_class_' + k) for k, _, _, _ in CLASSES[:2]],
                  [old('i_tod_upg_class_' + k) for k, _, _, _ in CLASSES[2:]], [new('i_tod_upg_class_' + k) for k, _, _, _ in CLASSES[2:]]]))
    z2 = lambda n: new(n).resize((new(n).width * 2, new(n).height * 2), Image.LANCZOS)
    rows.append(('NEW PLATES AT 2x (baked text proofread: CLASS + the class name, our typeface)',
                 [[z2('i_tod_upg_class_' + k) for k, _, _, _ in CLASSES[:2]], [z2('i_tod_upg_class_' + k) for k, _, _, _ in CLASSES[2:]]]))
    pad = 16
    W = max(2 * 840 + 3 * pad, 4 * 256 + 5 * pad)
    H = pad
    for label, lines in rows:
        H += 30 + sum(max(i.height for i in line) + pad for line in lines)
    sheet = Image.new('RGBA', (W, H), (16, 12, 26, 255))
    d = ImageDraw.Draw(sheet)
    y = pad
    seed = 0
    for label, lines in rows:
        d.text((pad, y), label, fill=(225, 220, 240, 255), font=font)
        y += 30
        for line in lines:
            x = pad
            for im in line:
                seed += 1
                sheet.alpha_composite(patch(im.width, im.height, seed), (x, y))
                sheet.alpha_composite(im, (x, y))
                x += im.width + pad
            y += max(i.height for i in line) + pad
    sheet.convert('RGB').save(out_path, optimize=True)
    return out_path


def deal_screens(stage_dir, out_dir):
    """The upgrade deal panel through tools/ui_mockup/render_pull.py, as each class: OLD = the repo today, NEW = the
    staged plates (art dir searched first). Returns [(label, old_frame, new_frame)]."""
    py = sys.executable
    tool = os.path.join(ROOT, 'tools', 'ui_mockup', 'render_pull.py')
    res = []
    for k, n, cid, _ in CLASSES:
        got = {}
        for tag, extra in (('old', []), ('new', ['--art-dir', stage_dir])):
            name = 'w3c_%s_%s' % (tag, k)
            r = subprocess.run([py, tool, '--name', name, '--fps', '4', '--class', str(cid)] + extra,
                               cwd=ROOT, capture_output=True, text=True)
            folder = os.path.join(ROOT, 'tmp', 'ui_mockup', 'pull', name)
            frames = sorted(f for f in os.listdir(folder) if f.startswith('frame_')) if os.path.isdir(folder) else []
            if r.returncode or not frames:
                print('render_pull %s failed:\n%s' % (name, (r.stderr or '')[-1500:]))
                continue
            dst = os.path.join(out_dir, '_screen_deal_%s_%s.png' % (k, tag))
            shutil.copy2(os.path.join(folder, frames[-1]), dst)
            got[tag] = dst
        if len(got) == 2:
            res.append(('Deal panel as the %s (render_pull.py --class %d)' % (n, cid), got['old'], got['new']))
    return res


def screens_sheet(pairs, out_path, w=1280):
    font = ImageFont.truetype(artgen.TTF, 26)
    ims = []
    for label, a, b in pairs:
        a, b = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
        a = a.resize((w, int(a.height * w / a.width)), Image.LANCZOS)
        b = b.resize((w, int(b.height * w / b.width)), Image.LANCZOS)
        ims.append((label, a, b))
    W = 2 * w + 60
    H = sum(max(a.height, b.height) + 60 for _, a, b in ims) + 20
    sheet = Image.new('RGB', (W, H), (16, 12, 26))
    d = ImageDraw.Draw(sheet)
    y = 20
    for label, a, b in ims:
        d.text((20, y), label + '   OLD (left)   NEW (right)', fill=(225, 220, 240), font=font)
        y += 40
        sheet.paste(a, (20, y))
        sheet.paste(b, (40 + w, y))
        y += max(a.height, b.height) + 20
    sheet.save(out_path, optimize=True)
    return out_path

# =============================================================================================== main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--stage', action='store_true', help='also write tmp/wave3/%s/stage/ (+ base/)' % PACK)
    ap.add_argument('--install', action='store_true', help='LANDING ONLY: copy into source_data/tod_ui_images/_images')
    ap.add_argument('--check', action='store_true', help='fail on any byte that differs from the installed (or staged) files')
    ap.add_argument('--against', choices=('installed', 'stage'), default='installed')
    ap.add_argument('--no-screens', action='store_true', help='skip the HUD / deal-panel screen composites')
    a = ap.parse_args()

    if a.check:
        built = build_all()
        stage = a.against == 'stage'
        img_dir = STAGE_IMG if stage else artgen.IMG
        bad = 0
        for name, (im, data) in built.items():
            p = os.path.join(img_dir, name + '.png')
            if not os.path.isfile(p):
                print('W3C CLASS PACK: MISSING %s' % p)
                bad += 1
            elif open(p, 'rb').read() != data:
                print('W3C CLASS PACK: STALE %s (re-run the generator; never hand-edit it)' % p)
                bad += 1
        for msg in wiring_problems(STAGE_ROOT if stage else ROOT):
            print('W3C CLASS PACK: %s' % msg)
            bad += 1
        if bad:
            sys.exit(1)
        print('W3C CLASS PACK OK %d images + wiring (%s)' % (len(built), 'stage' if stage else 'installed'))
        return

    built = build_all()
    os.makedirs(OUT, exist_ok=True)
    for name, (im, data) in built.items():
        with open(os.path.join(OUT, name + '.png'), 'wb') as fh:
            fh.write(data)
        print('%-36s %s' % (name, hashlib.md5(data).hexdigest()))
    for k, n, _, _ in CLASSES:
        print('ink mass %-12s %.3f of the tube area' % (n, ink_mass(k)))
    if a.stage:
        os.makedirs(STAGE_IMG, exist_ok=True)
        os.makedirs(BASE_IMG, exist_ok=True)
        for name, (im, data) in built.items():
            base = os.path.join(BASE_IMG, name + '.png')
            repo = os.path.join(artgen.IMG, name + '.png')
            if not os.path.exists(base):
                shutil.copy2(repo, base)
            with open(os.path.join(STAGE_IMG, name + '.png'), 'wb') as fh:
                fh.write(data)
        print('staged ->', STAGE_ROOT)
    if a.install:
        for name, (im, data) in built.items():
            with open(os.path.join(artgen.IMG, name + '.png'), 'wb') as fh:
                fh.write(data)
        print('installed %d images into %s' % (len(built), artgen.IMG))
    print('review ->', review_sheet(built, os.path.join(OUT, '_review.png')))
    if not a.no_screens:
        newg = lambda n: built[n][0] if n in built else Image.open(artgen.shipped(n)).convert('RGBA')
        oldp = lambda n: os.path.join(BASE_IMG, n + '.png') if os.path.exists(os.path.join(BASE_IMG, n + '.png')) else artgen.shipped(n)
        oldg = lambda n: Image.open(oldp(n)).convert('RGBA')
        pairs = [('HUD bottom-left at 1080p (the ring + 3 teammate rows)',
                  hud_panel(oldg, os.path.join(OUT, '_screen_hud_old.png')),
                  hud_panel(newg, os.path.join(OUT, '_screen_hud_new.png')))]
        art = STAGE_IMG if a.stage else OUT
        pairs += deal_screens(art, OUT)
        print('screens ->', screens_sheet(pairs, os.path.join(OUT, '_review_screens.png')))


if __name__ == '__main__':
    main()
