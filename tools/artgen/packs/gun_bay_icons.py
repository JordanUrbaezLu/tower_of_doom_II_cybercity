"""gun_bay_icons.py - PK06: the HUD gun-bay icons the bay was missing (2026-10-04).

THE GAP (tmp/asset_prod/packs/PK06-gun-bay-icons.json). The Necromancer's tier-2 and tier-3
primaries - tod_necro_staff2 "Soul Staff" and tod_necro_staff3 "Crown of the Damned" (+ their EX
forms) - had no gun-bay picture: AetheriumLoadout.lua resolved neither display name, so a promoted
player kept the tier-1 skull, and after a respawn (curCat nil) the bay drew the MR6 PISTOL for as
long as a staff was held. And the Warrior's tier-3 sword was renamed CYBER SWORD and re-modelled
(dark alloy, glowing circuit spine, winged guard, reactor gem, diamond pommel) while its icon stayed
the plain Gold Battle Sword broadsword.

2026-10-05 (wave 2, W2G): THE TIER-1 SKULL JOINS THE PACK. The shipped i_tod_hud_gun_skull (the
2026-09-26 drop) was a rounded lump with one eye and a grin, which read as a reptile skull. The real
Skull of Nan Sapwe (art/generated/R1-truth-renders/skull_side.png, skull_34.png) is an elongated
crested skull: a long swept hood with tribal glyphs on its crown, one big eye socket, the jaw hanging
OPEN with fangs, and a ribbed back. nan_sapwe() redraws it BY HAND in this pack's style (a same-name
redraw, like the greatsword), side-on with the face pointing right. The staff heads were updated in
the same pass so the Necromancer's three tiers share one language: skull_parts() now hangs the jaw
OPEN (JAW_DROP) over a navy mouth with a canine fang at each corner of both rows, where PK06's first
cut read as a closed grin. The other class icons were judged against their truth renders at the bay's
144 x 66 and KEPT (bow, firebow, fist, gauntlet: each reads as what it is; R1's traced redraws of
them were rejected as noisy blobs); the review sheet shows that judgement.

THE FOUR DELIVERABLES, 288 x 132 RGBA (the gun sheet cell; drawn at 96 x 44 canvas units = 144 x 66
px at 1080p, so every detail here is drawn to survive a 0.5x sample):
  i_tod_hud_gun_skull        REDRAW, same name (2026-10-05): the Skull of Nan Sapwe, see above
  i_tod_hud_gun_soulstaff    the Soul Staff: straight wrapped iron staff, coil bands, a riveted
                             socket ferrule and the open-jawed skull with glowing eyes on it
  i_tod_hud_gun_crownstaff   the Crown of the Damned: the same staff under the spiked halo - a studded
                             ring round the skull, a sunburst of forged blades, the long spear finial
  i_tod_hud_gun_greatsword   REDRAW, same name: the Cyber Sword - long tapered blade with a dark
                             power spine and light circuit traces, flared horns, winged guard with the
                             reactor gem, wrapped grip, diamond pommel. Drawn from the native renders
                             (art/cyber_sword/native_oblique.png, native_hilt.png), never the gold card.

THE STYLE IS MEASURED, NOT GUESSED. The class-weapon neighbours these sit beside (i_tod_hud_gun_skull,
_firebow, _bow, _greatsword, _gauntlet, _fist, _peacekeeper: the 2026-09-26 drops) are EXACTLY three
colours and binary alpha:
  LIGHT #E8EEF6 fill, SHADE #62779C lower band, NAVY #0A1020 outline - a 7 px outer outline, 4 px
  internal part lines, the lower half of every form in SHADE (light from above), hard pixel edges.
This generator reproduces that, not an approximation of it: every part is flat vector, the SVG is
rendered at 4x with crisp (aliased) edges so each sub-pixel is exactly one palette colour, and each
output pixel takes the MAJORITY colour of its 4 x 4 block (ties: navy > shade > light > clear). The
output therefore holds only those three colours and alpha 0/255, like its neighbours, and it is
deterministic, so --check can gate the bytes.

WEIGHT ON THE PLATE. On the dark gun plate the navy outline vanishes; what the eye reads is the
LIGHT + SHADE mass. Measured share of the cell in LIGHT + SHADE: the neighbours skull 31, gauntlet
32, greatsword (the old broadsword) 21, firebow 16, bow 12 %; these icons soulstaff 20, crownstaff
16, greatsword (the Cyber Sword) 16 %. Three first-pass choices failed the 144 x 66 test and were
changed: navy hairline strap seams on the staff (read as "IN|N|N" noise -> bold SHADE stripes, the
shipped staff2's grip language), a NAVY circuit panel on the blade (read as a hole, 10 % fill ->
a SHADE panel in a navy rim) and navy III bars on the guard arms (read as a ladder -> the III stays
on the blade's charge cell only). Poles, blade and heads are drawn chunky (SHAFT_HH, the blade's
half-heights) and fine detail is limited to what survives a 0.5x sample.

THE HEADS FACE THE BAY'S CONVENTION. Every gun cell points RIGHT (muzzles, the sword tip, the bow's
arrow), so the staff heads sit at the right end and the spear finial points right. The staff runs
horizontally (the pack brief). The staff skull is drawn UPRIGHT and front-on - crown up, two glowing
eyes, the open fanged jaw - because a human skull side-on at this size is a lump; the tier-1 Skull of
Nan Sapwe is drawn side-on because its swept crest IS its read. SKULL_UPRIGHT = False draws the staff's
physical mount instead (the crown along the staff axis, the face turned 90 degrees), kept for review.

USAGE
  python tools/artgen/packs/gun_bay_icons.py                 render into art/generated/PK06-gun-bay-icons/
                                                             + _review.png (each beside its references)
  python tools/artgen/packs/gun_bay_icons.py --install [--out-root DIR]
                                                             write the PNGs into <root>/source_data/
                                                             tod_ui_images/_images/ (default root = repo)
  python tools/artgen/packs/gun_bay_icons.py --check [--root DIR]
                                                             BUILD GATE: regenerate in memory, fail on any
                                                             byte that differs from the installed PNG, and
                                                             fail unless each image has its GDT block and
                                                             zone image line and the Lua carries the name
                                                             + stem rows (the image name is built at
                                                             runtime, so lint_tod_assets GATE A is blind)
Never hand-edit an output PNG: change this file and re-run it. Brief + record:
docs/179b_gun_bay_icons_art_prompt.md; landing kit: tmp/asset_prod/PK06-gun-bay-icons/LAND.md.
"""
import argparse, io, math, os, re, sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402

try:
    import resvg_py
except ImportError:  # pragma: no cover
    resvg_py = None

ROOT = artgen.ROOT
PACK = 'PK06-gun-bay-icons'
W, H = 288, 132
CY = 66.0
SS = 4

NAVY, SHADE, LIGHT = '#0A1020', '#62779C', '#E8EEF6'
PAL = [(10, 16, 32), (98, 119, 156), (232, 238, 246)]   # class index 1..3 (0 = clear)
OUT = 5.0      # silhouette stroke beyond each part's edge  -> 5 + 2 = the 7 px outer outline
LINE = 4.0     # each part's own edge line (2 px inside it; two touching parts = a 4 px seam)

SKULL_UPRIGHT = True
EYE_GLOW = 4.0      # the Skull of Nan Sapwe's eye: a glint in the dark socket (0 = the empty socket)
RIB_RIM = 5.0       # the lit top rim of each of its ribs (local units; 7.5 read as stacked plates)
JAW_DROP = 5.0      # how far the staff skulls' mandible hangs open (local units; 0 = PK06's first cut)
CRANIUM_FACETS = 9   # the cranium's crown arc as 9 flat facets: the shipped tier-1 skull (and every
                     # neighbour) is drawn in chunky angular facets, never a smooth circle

NEW_IMAGES = ['i_tod_hud_gun_soulstaff', 'i_tod_hud_gun_crownstaff']
ALL_IMAGES = NEW_IMAGES + ['i_tod_hud_gun_greatsword', 'i_tod_hud_gun_skull']   # same-name redraws
LUA_ROWS = {   # display name (AetheriumLoadout TOD_NAME_CAT key) -> slug
    'SKULL OF NAN SAPWE': 'skull', 'SKULL OF THE DAMNED': 'skull',
    'SOUL STAFF': 'soulstaff', 'SOUL STAFF EX': 'soulstaff',
    'CROWN OF THE DAMNED': 'crownstaff', 'CROWN OF THE DAMNED EX': 'crownstaff',
    'CYBER SWORD': 'greatsword', 'CYBER SWORD EX': 'greatsword',
}
LUA_STEMS = {   # asset stem (TOD_GUN_CAT key) -> slug; the pulse rows are each tier's Soul Pulse cast proxy
    'tod_necro_skull': 'skull',
    'tod_necro_staff2': 'soulstaff', 'tod_necro_staff3': 'crownstaff',
    'tod_necro_pulse2': 'soulstaff', 'tod_necro_pulse3': 'crownstaff',
    'cc_gold_sword': 'greatsword',
}

# ------------------------------------------------------------------------------------ geometry

def fmt(v):
    s = '%.2f' % v
    return s.rstrip('0').rstrip('.') if '.' in s else s


def path(pts, close=True):
    return 'M' + ' L'.join('%s %s' % (fmt(x), fmt(y)) for x, y in pts) + (' Z' if close else '')


def ell(cx, cy, rx, ry, a0=0.0, a1=360.0, n=40):
    """Points on an ellipse from angle a0 to a1 (degrees, screen space: y down)."""
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return out


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def xform(pts, ox, oy, s=1.0, rot=0.0):
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(ox + s * (x * c - y * sn), oy + s * (x * sn + y * c)) for x, y in pts]


def line(pts, w=2.0, col=NAVY, cap='round', join='round'):
    return ('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="%s" '
            'stroke-linejoin="%s"/>' % (path(pts, close=False), col, fmt(w), cap, join))


def fillp(d, col):
    return '<path d="%s" fill="%s" fill-rule="evenodd"/>' % (d, col)


def dot(x, y, r, col=NAVY):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (fmt(x), fmt(y), fmt(r), col)


class Part:
    """One outlined form: LIGHT fill, an optional SHADE region clipped to it, details drawn inside it
    (clipped), then its own 4 px NAVY edge. Every part also feeds the silhouette (the outer outline).
    `over` is drawn after the edge, unclipped (a gem set into a boss). `fill` = NAVY makes a cavity
    (the Skull of Nan Sapwe's open mouth): it still feeds the silhouette, so it reads as a hole in
    the head rather than a gap in the outline."""

    def __init__(self, d, shade=None, details='', over='', fill=LIGHT):
        self.d, self.shade, self.details, self.over, self.fill = d, shade, details, over, fill


def below(y, x0=-50, x1=W + 50, y1=H + 50):
    """A shade region: everything under the line y."""
    return path(rect(x0, y, x1, y1))


def compose(parts):
    defs, sil, body = [], [], []
    for i, p in enumerate(parts):
        defs.append('<clipPath id="c%d"><path d="%s" clip-rule="evenodd"/></clipPath>' % (i, p.d))
        sil.append('<path d="%s" fill="%s" fill-rule="evenodd" stroke="%s" stroke-width="%s" '
                   'stroke-linejoin="round"/>' % (p.d, NAVY, NAVY, fmt(OUT * 2)))
        g = [fillp(p.d, p.fill)]
        inner = (fillp(p.shade, SHADE) if p.shade else '') + p.details
        if inner:
            g.append('<g clip-path="url(#c%d)">%s</g>' % (i, inner))
        g.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>'
                 % (p.d, NAVY, fmt(LINE)))
        g.append(p.over)
        body.append(''.join(g))
    return artgen.svg_doc(W, H, ''.join(sil) + ''.join(body), ''.join(defs))

# ------------------------------------------------------------------------------------- render

def render(svg):
    """SVG -> the shipped 3-tone style: 4x crisp render, 4x4 majority vote, palette + binary alpha."""
    if resvg_py is None:
        raise SystemExit('gun_bay_icons: resvg_py is not installed (pip install --user resvg_py)')
    data = resvg_py.svg_to_bytes(svg_string=svg, width=W * SS, height=H * SS, skip_system_fonts=True,
                                 shape_rendering='crisp_edges')
    a = np.array(Image.open(io.BytesIO(bytes(data))).convert('RGBA')).astype(np.int32)
    rgb = a[..., :3]
    d = np.stack([((rgb - np.array(c)) ** 2).sum(-1) for c in PAL], -1)
    cls = d.argmin(-1) + 1
    cls[a[..., 3] < 128] = 0
    blocks = cls.reshape(H, SS, W, SS).transpose(0, 2, 1, 3).reshape(H, W, SS * SS)
    counts = np.stack([(blocks == k).sum(-1) for k in range(4)], -1).astype(np.float64)
    counts += np.array([0.0, 0.3, 0.2, 0.1])          # ties: navy > shade > light > clear
    win = counts.argmax(-1)
    out = np.zeros((H, W, 4), np.uint8)
    for k, c in enumerate(PAL, 1):
        out[win == k] = c + (255,)
    return Image.fromarray(out, 'RGBA')

# ------------------------------------------------------------------------------- the staff shaft

SHAFT_HH = 13.0     # the pole's half-height: 26 px drawn = 22 px of fill inside the outline, as chunky
                    # as the shipped staffs' poles, so the icon carries its neighbours' weight


def staff_shaft(x_top, x0=6.0):
    """The Necromancer staff's shaft, butt cap at the left, socket end at x_top. From the model
    (art/necro_staff/tier2_full.png, read top -> bottom as right -> left): a collar ring at ~10 %,
    a band at ~26 %, two wire-coil bands at ~51-57 % and ~74-80 %, the butt cap, and a spiral
    leather strap the whole way. Returns parts, back to front."""
    L = x_top - x0

    def X(f):          # fraction down the staff (0 = top) -> x
        return x_top - f * L

    hh = SHAFT_HH
    parts = []
    # the pole + its spiral leather strap. The strap is drawn the way the shipped staff2 draws its
    # grip wrap: bold SHADE diagonal bands, never navy hairlines (a first pass used 2.4 px navy
    # seams; at the 0.5x the bay shows they read as "IN|N|N" noise). The shade band starts BELOW the
    # axis so the lit upper part is the larger one, as on every neighbour.
    strap = ''
    x = X(0.92) + 12
    while x < x_top - 10:
        strap += fillp(path([(x - 5.5, CY - hh - 2), (x + 1.5, CY - hh - 2), (x + 9.5, CY + hh + 2),
                             (x + 2.5, CY + hh + 2)]), SHADE)
        x += 28.0
    parts.append(Part(path(rect(X(1.0) + 6, CY - hh, x_top + 2, CY + hh)), below(CY + 3), strap))

    def band(f0, f1, hb, grooves=0):
        a, b = X(f1), X(f0)
        det = ''
        for i in range(grooves):
            cx = a + (b - a) * (i + 1) / (grooves + 1)
            det += line([(cx, CY - hb - 2), (cx, CY + hb + 2)], 3.0, cap='butt')
        parts.append(Part(path(rect(a, CY - hb, b, CY + hb)), below(CY + 3), det))

    band(0.07, 0.125, 16.5)                # the collar ring under the head (the model's thin band at
    #                                        ~28 % is left out: at 0.5x it read as a second seam)
    band(0.49, 0.59, 17.0)                 # wire coil 1: a raised ring, no inner grooves - the bump is
    band(0.72, 0.82, 17.0)                 # what reads at 0.5x; grooves inside it read as double seams
    # butt cap: a fatter, chamfered foot with one ring groove
    bx0, bx1 = x0, X(0.94)
    cap = [(bx0, CY - 11), (bx0 + 3.5, CY - 16), (bx1, CY - 16), (bx1, CY + 16), (bx0 + 3.5, CY + 16),
           (bx0, CY + 11)]
    parts.append(Part(path(cap), below(CY + 3),
                      line([(bx1 - 5, CY - 18), (bx1 - 5, CY + 18)], 3.0, cap='butt')))
    return parts


def socket_cup(x0, x1, h0, h1, rivets=2):
    """The riveted socket ferrule the head sits in: flares from h0 (staff side) to h1 (head side)."""
    pts = [(x0, CY - h0), (x1, CY - h1), (x1, CY + h1), (x0, CY + h0)]
    det = ''
    for i in range(rivets):
        rx = x0 + (x1 - x0) * (i + 1) / (rivets + 1)
        det += dot(rx, CY - (h0 + (h1 - h0) * (rx - x0) / (x1 - x0)) * 0.5, 2.5)
    return Part(path(pts), below(CY + 3), det)

# -------------------------------------------------------------------------------------- skull

def skull_parts(ox, oy, s, rot=0.0, suture=True, engrave=False):
    """The staff's skull, front-on, in local units (crown up, ~62 wide x 82 tall, centre ~(0,-5)),
    placed at (ox, oy), scaled s, rotated rot degrees. The model's read: a big rounded cranium,
    deep angular sockets with a GLOWING WHITE EYE in each, the nasal cavity, and the jaw hanging
    OPEN (a navy gap between two rows of teeth). Returns [mandible, cranium] (back to front)."""
    T = lambda pts: xform(pts, ox, oy, s, rot)    # noqa: E731
    sw = lambda w: w * max(0.8, min(1.15, s))      # noqa: E731

    crown = ell(0, -15, 33, 31, 160, 380, CRANIUM_FACETS)
    cran = [(-23, 8), (-28, 2), (-31, -4)] + crown[1:-1] + [(31, -4), (28, 2), (23, 8), (18, 11),
                                                           (15.5, 15.5), (-15.5, 15.5), (-18, 11)]
    det = ''
    # the sockets: deep and angular, the brow heavy toward the nose, each with a small glowing eye
    for sgn in (-1, 1):
        sock = [(sgn * 4.0, -13.5), (sgn * 12, -17), (sgn * 21.5, -14.5), (sgn * 23.5, -6.5),
                (sgn * 18.5, 0), (sgn * 8.5, 0), (sgn * 3.8, -6)]
        det += fillp(path(T(sock)), NAVY)
        ex, ey = T([(sgn * 13.8, -7.4)])[0]
        det += dot(ex, ey, 3.3 * s, LIGHT)     # the glowing eye: big enough to survive 0.5x
    # nasal cavity (an inverted heart)
    det += fillp(path(T([(0, -1.0), (2.2, 2.5), (5.0, 8.5), (2.0, 9.0), (0, 7.2), (-2.0, 9.0),
                         (-5.0, 8.5), (-2.2, 2.5)])), NAVY)
    # upper teeth: the seams between them
    for tx in (-10.5, -5.2, 0, 5.2, 10.5):
        det += line(T([(tx, 12), (tx, 17)]), sw(2.6), cap='butt')
    if suture:   # the cranial suture the model carries across the crown
        zz = [(-20, -32), (-16, -36), (-12, -31.5), (-8, -36), (-4, -31.5), (0, -36), (4, -31.5),
              (8, -36), (12, -31.5), (16, -36), (20, -32)]
        det += line(T(zz), sw(2.4))
    if engrave:  # the Crown of the Damned's carved brow spirals (OFF in the icon: at 0.5x two tiny
        #          spirals over the sockets read as a second pair of eyes)
        for sgn in (-1, 1):
            sp = [(sgn * (8.5 + 6.5 * (1 - t / 16.0) * math.cos(t * 0.7 + 1.0)),
                   -27 + 5.5 * (1 - t / 16.0) * math.sin(t * 0.7 + 1.0)) for t in range(0, 17)]
            det += line(T(sp), sw(1.6))
    cranium = Part(path(T(cran)), path(T(rect(-60, 10.0, 60, 60))), det)

    # THE OPEN JAW (2026-10-05, W2G): the model's jaw hangs open and crooked, its canines long. The
    # first PK06 cut sat the mandible 4.5 units under the teeth, which read as a closed grin beside
    # the tier-1 Skull of Nan Sapwe's gaping fanged mouth. Now the same language as tier 1: a navy
    # mouth the width of the teeth rows, the mandible dropped JAW_DROP, and a canine fang at each
    # corner of both rows (fang(): blunt-tipped so the point survives against the navy).
    d = JAW_DROP
    mouth = Part(path(T([(-16.5, 14.0), (16.5, 14.0), (16.0, 22.0 + d), (-16.0, 22.0 + d)])), fill=NAVY)
    canines = []
    for sgn in (-1, 1):   # (x, root y, tip y, width): upper canines hang at the corners, the lower
        #                   pair rise just inside them so the two rows interlock instead of colliding
        for cx, y0, y1, w in ((12.0, 14.5, 21.0 + d * 0.5, 8.0), (7.0, 20.5 + d, 15.0 + d * 0.5, 7.0)):
            x = sgn * cx
            ym = y0 + (y1 - y0) * 0.7
            pts = [(x - w / 2, y0), (x + w / 2, y0), (x + w * 0.38, ym), (x + 1.4, y1), (x - 1.4, y1),
                   (x - w * 0.38, ym)]
            canines.append(Part(path(T(pts))))
    mand = [(-19.5, 20 + d), (19.5, 20 + d), (18.5, 28 + d), (10.5, 35.5 + d), (-10.5, 35.5 + d),
            (-18.5, 28 + d)]
    mdet = ''
    for tx in (-5.2, 0, 5.2):
        mdet += line(T([(tx, 19 + d), (tx, 24.5 + d)]), sw(2.6), cap='butt')
    mandible = Part(path(T(mand)), path(T(rect(-60, 28.0 + d, 60, 60))), mdet)
    return [mouth, canines[1], canines[3], mandible, canines[0], canines[2], cranium]

# ---------------------------------------------------------------------------------- the icons

def soul_staff():
    """Tier 2: the Soul Staff. Straight wrapped staff, riveted socket ferrule, the skull on it."""
    if SKULL_UPRIGHT:
        sx, ss = 240.0, 1.22
        x_top = sx - 31 * ss - 14
        parts = staff_shaft(x_top)
        parts.append(socket_cup(x_top, x_top + 22, 15.0, 18.5))
        parts += skull_parts(sx, CY + 6, ss)
    else:
        sx, ss = 236.0, 1.18
        x_top = sx - 36 * ss - 16
        parts = staff_shaft(x_top)
        parts.append(socket_cup(x_top, x_top + 22, 15.0, 18.5))
        parts += skull_parts(sx, CY, ss, rot=90)
    return compose(parts)


def blade_part(cx, cy, ang, r0, rw, r1, hw, groove=False):
    """One forged leaf blade radiating from (cx, cy) at angle ang (deg, 0 = +x, screen y down): base
    at radius r0 (behind the ring), widest (half-width hw) at rw, tip at r1. Two facets: the one
    facing down-right takes SHADE (light from the top-left). groove = the recessed channel."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    P = lambda r, o: (cx + ux * r + nx * o, cy + uy * r + ny * o)   # noqa: E731
    base, tip = P(r0, 0), P(r1, 0)
    lft, rgt = P(rw, -hw), P(rw, hw)
    side = rgt if (nx * 0.6 + ny * 0.8) > 0 else lft
    det = ''
    if groove:
        det += line([P(rw - (rw - r0) * 0.1, 0), P(r1 - (r1 - rw) * 0.3, 0)], 2.0)
    return Part(path([base, lft, tip, rgt]), path([base, side, tip]), det)


def crown_staff():
    """Tier 3: the Crown of the Damned. The same staff under the spiked halo: a studded ring round the
    skull, a sunburst of forged blades, the long spear finial pointing out along the axis (right),
    and the chased collar."""
    cx = 200.0
    ro, ri = 37.0, 26.0
    x_top = cx - ro - 16
    parts = staff_shaft(x_top)
    # the sunburst, back to front. Angles in the model with the finial UP, rotated so it points right:
    # flanks +-20, upper diagonals +-55, cross +-90, lower diagonals +-125, the long low pair (+-160 on
    # the model, opened to +-152 here: at +-160 only their tips cleared the collar and read as specks).
    rays = [
        (152, 22, 36, 68, 7.4, True), (-152, 22, 36, 68, 7.4, True),
        (125, 24, 42, 58, 7.8, False), (-125, 24, 42, 58, 7.8, False),
        (90, 24, 43, 60, 8.2, False), (-90, 24, 43, 60, 8.2, False),
        (55, 24, 43, 62, 7.8, False), (-55, 24, 43, 62, 7.8, False),
        (20, 20, 42, 72, 7.2, True), (-20, 20, 42, 72, 7.2, True),
    ]
    for ang, r0, rw, r1, hw, g in rays:
        parts.append(blade_part(cx, CY, ang, r0, rw, r1, hw, groove=g))
    parts.append(blade_part(cx, CY, 0, 20, 47, 81, 9.5, groove=True))   # the spear finial
    # the chased collar under the ring: a flared iron sleeve with one groove (a first pass drew the
    # model's diamond cross-hatch in 1.8 px lines; at 0.5x it was a grey smudge)
    c0, c1 = x_top, cx - ro + 8
    gx = c0 + (c1 - c0) * 0.45
    parts.append(Part(path([(c0, CY - 15), (c1, CY - 18), (c1, CY + 18), (c0, CY + 15)]),
                      below(CY + 3), line([(gx, CY - 20), (gx, CY + 20)], 3.0, cap='butt')))
    # the studded ring (an annulus): studs round its middle radius
    ring = path(ell(cx, CY, ro, ro, 0, 360, 80)[:-1]) + ' ' + path(ell(cx, CY, ri, ri, 0, 360, 64)[:-1][::-1])
    studs = ''
    rm = (ro + ri) / 2.0
    for k in range(12):
        a = math.radians(k * 30 + 15)
        studs += dot(cx + rm * math.cos(a), CY + rm * math.sin(a), 2.1)
    parts.append(Part(ring, below(CY + 3), studs))
    # the skull in the halo (no carved spirals: see skull_parts)
    if SKULL_UPRIGHT:
        parts += skull_parts(cx, CY + 4.0, 0.68, suture=False, engrave=False)
    else:
        parts += skull_parts(cx, CY, 0.62, rot=90, suture=False, engrave=False)
    return compose(parts)


def cyber_sword():
    """Tier 3 Warrior: the Cyber Sword, pommel left, tip right (native_oblique.png read sideways).
    Proportions from the model (tip y25 -> pommel y815 in native_oblique): blade ~72 %, grip ~17 %,
    pommel ~6 %. Every part is drawn bolder than the model (the guard +-45 of 132 where the model's
    would be +-24, the blade +-20, the grip +-11) because the bay shows it at 144 x 66 beside the
    chunky fist and gauntlet; a first pass true to the model's slenderness read as a thin, busy
    filigree there. Light from above, as on every neighbour: the lower part of each form is SHADE."""
    parts = []
    # POMMEL: the faceted diamond pommel and its plate - a navy diamond with a light diamond set in it
    pom = [(3.0, CY), (9.5, CY - 15), (21, CY - 17.5), (29, CY - 9), (29, CY + 9), (21, CY + 17.5),
           (9.5, CY + 15)]
    pdet = fillp(path([(9.0, CY), (17.0, CY - 8.5), (25.0, CY), (17.0, CY + 8.5)]), NAVY)
    pdet += fillp(path([(12.8, CY), (17.0, CY - 4.4), (21.2, CY), (17.0, CY + 4.4)]), LIGHT)
    parts.append(Part(path(pom), below(CY + 3), pdet))
    # GRIP: dark leather under crossed cord wraps, a ringed collar at each end
    g0, g1 = 32.0, 70.0
    wrap = ''
    k = g0 - 9
    while k < g1:
        wrap += line([(k, CY - 12.5), (k + 12, CY + 12.5)], 2.8)
        wrap += line([(k + 12, CY - 12.5), (k, CY + 12.5)], 2.8)
        k += 12.0
    parts.append(Part(path(rect(g0 - 1, CY - 11, g1 + 1, CY + 11)), below(CY + 3), wrap))
    for a, b in ((27.0, 34.5), (67.5, 75.0)):
        parts.append(Part(path(rect(a, CY - 14, b, CY + 14)), below(CY + 3)))

    # THE BLADE (drawn before the guard so the guard sits over its root). Its base flares into the two
    # HORNS the model carries (the widest point, swept back toward the guard), then the long edge
    # runs nearly parallel and tapers into the point.
    bx0 = 90.0
    edge_top = [(bx0, CY - 11), (96, CY - 16), (99, CY - 29), (108.5, CY - 22.5), (122, CY - 20.5),
                (190, CY - 19.5), (236, CY - 17), (257, CY - 13), (273, CY - 7), (285, CY)]
    edge_bot = [(x, 2 * CY - y) for x, y in edge_top[::-1]][1:]
    # the dark power spine: a SHADE panel in a NAVY rim, LIGHT circuit traces on it (the model's
    # glowing cyan lines). SHADE, not NAVY: on the dark gun plate a navy panel reads as a HOLE and the
    # blade as two thin edges (a first pass did that: 10 % fill against the shipped sword's 21 %).
    sp0, sp1, tip_sp = 111.0, 240.0, 260.0
    shh = 9.5
    spine = [(sp0, CY - shh), (sp1, CY - shh), (tip_sp, CY), (sp1, CY + shh), (sp0, CY + shh)]
    sdet = (fillp(path(spine), SHADE) + '<path d="%s" fill="none" stroke="%s" stroke-width="3" '
            'stroke-linejoin="round"/>' % (path(spine), NAVY))
    # the "III" charge cell by the guard
    for i in range(3):
        xx = sp0 + 5.5 + i * 4.8
        sdet += line([(xx, CY - 5.0), (xx, CY + 5.0)], 2.6, col=LIGHT, cap='butt')
    # four circuit cells, each a stepped trace ending in a node. The model has five; four keep each
    # trace's step wide enough to read at 0.5x (a five-cell first pass merged into a dotted line).
    cells = 4
    c_a, c_b = sp0 + 21.0, sp1 - 2.0
    cw = (c_b - c_a) / cells
    for i in range(cells):
        x0 = c_a + i * cw
        tr = [(x0 + 2.0, CY + 3.8), (x0 + cw * 0.38, CY + 3.8), (x0 + cw * 0.58, CY - 3.8),
              (x0 + cw - 7.0, CY - 3.8)]
        sdet += line(tr, 3.0, col=LIGHT, cap='butt', join='miter')
        sdet += dot(x0 + cw - 2.8, CY - 3.8, 2.1, LIGHT)
    # the two glow rails run on out of the panel and meet at the point
    sdet += line([(tip_sp - 4, CY - 2.6), (280, CY - 0.5)], 2.4)
    sdet += line([(tip_sp - 4, CY + 2.6), (280, CY + 0.5)], 2.4)
    parts.append(Part(path(edge_top + edge_bot), below(CY + 10.5), sdet))   # the lower bevel in SHADE

    # THE GUARD: the reactor boss at the centre and, each side, one flared arm ending in the winged cross
    # end (three points, a navy diamond inset, a seam where the end plate meets the arm). The model's
    # III charge bars on the arms are left to the blade's III cell: on a 9 px arm at 0.5x they read as
    # a ladder ("H H") in navy and as a dark slot in a cell (both tried).
    gx = 83.0
    for sgn in (-1, 1):
        y = lambda v: CY + sgn * v          # noqa: E731
        arm = [(gx - 7.5, y(12)), (gx + 7.5, y(12)), (gx + 9.5, y(27)), (gx + 12.5, y(33.5)),
               (gx + 15.5, y(41)), (gx + 7, y(39.5)), (gx, y(45.5)), (gx - 7, y(39.5)), (gx - 15.5, y(41)),
               (gx - 12.5, y(33.5)), (gx - 9.5, y(27))]
        adet = fillp(path([(gx, y(40.8)), (gx + 4.3, y(35.4)), (gx, y(30.0)), (gx - 4.3, y(35.4))]), NAVY)
        adet += line([(gx - 12, y(26.0)), (gx + 12, y(26.0))], 2.6, cap='butt')
        parts.append(Part(path(arm), below(CY + 3), adet))
    boss = ell(gx, CY, 14.0, 16.0, 0, 360, 44)[:-1]
    gem = [(gx, CY - 10.0), (gx + 7.0, CY), (gx, CY + 10.0), (gx - 7.0, CY)]
    bdet = fillp(path(ell(gx, CY, 10.2, 12.4, 0, 360, 36)[:-1]), NAVY)
    over = fillp(path(gem), LIGHT) + fillp(path([(gx - 7.0, CY), (gx + 7.0, CY), (gx, CY + 10.0)]), SHADE)
    over += line(gem + [gem[0]], 2.0)
    parts.append(Part(path(boss), below(CY + 3), bdet, over=over))
    return compose(parts)


def fang(x, y0, y1, w, lean=-2.0, tf=None):
    """One fang: root centred on x at y0 (hidden under the jaw that holds it), tip at y1 (below y0 =
    hanging, above = rising), root width w, the tip leaning `lean` (negative = swept back, as the
    model's teeth are). The back strip takes SHADE so a row reads as separate teeth, not one white
    bar. It keeps most of its width until 70 % of the way and ends in a 4-unit blunt point: against a
    navy mouth its own edge line merges with the cavity, so a fang that tapers the whole way shows
    only its root (a first pass: the fangs read as specks at 0.5x). tf maps the points (a design-
    space -> cell transform)."""
    tf = tf or (lambda pts: pts)
    sgn = 1 if y1 > y0 else -1
    tip = (x + lean, y1)
    mid = y0 + sgn * abs(y1 - y0) * 0.7
    pts = [(x - w / 2, y0), (x + w / 2, y0), (x + w * 0.4 + lean * 0.7, mid), (x + lean + 2.0, y1),
           (x + lean - 2.0, y1), (x - w * 0.4 + lean * 0.7, mid)]
    cx = x - w * 0.14
    back = [(x - w - 4, y0 - sgn * 6), (cx, y0 - sgn * 6), (cx + lean * 0.3, mid), tip,
            (x - w - 4, y1 + sgn * 6)]
    return Part(path(tf(pts)), path(tf(back)))


NS_SCALE = 0.9               # design space -> cell: the skull is drawn on a 288 x 132 design grid, then
NS_ORIGIN = (156.0, 66.0)    # scaled about (140, 66) and placed so its 7 px outline clears every edge of
#                              the cell (unscaled, the crest tip and the drool strand were cut flat by it)


def nan_sapwe():
    """Tier 1 Necromancer: the Skull of Nan Sapwe, side-on, the face pointing RIGHT like every bay
    cell. Read from the native render (art/generated/R1-truth-renders/skull_side.png, the face
    turned up ~30 degrees so the crest lies along the cell): a long swept CREST running back to a
    point, the tribal glyphs on its crown, one big eye socket with a glint in it, the jaw hanging
    OPEN with fangs, and the ribbed back - stacked bone knuckles, each with a horn, under the crest.
    The 2026-09-26 drop drew a rounded lump with a grin, which read as a reptile skull. Hand-placed
    vector, not a trace (R1's traces of the same render read as noisy blobs); every detail is sized
    to survive the bay's 0.5x sample. Line weights are in CELL pixels (unscaled), like every icon."""
    ox, oy = NS_ORIGIN

    def M(pts):
        return [(ox + NS_SCALE * (x - 140.0), oy + NS_SCALE * (y - 66.0)) for x, y in pts]

    def P(pts):
        return path(M(pts))

    def shade_below(y):
        return P(rect(-80, y, 400, 220))

    parts = []
    # THE NECK: the column the ribbed back hangs on, wholly in shadow under the hood
    parts.append(Part(P([(116.0, 34.0), (186.0, 38.0), (192.0, 118.0), (132.0, 122.0)]),
                      path(rect(-10, -10, W + 10, H + 10))))
    # THE RIBBED BACK: four bone knuckles on the neck, lowest first, so each one's lower edge laps
    # the one under it (the model's stacked ridges). Each is a faceted half-round with a short horn
    # off its lower back corner, pointing back and down; their backs step right as they descend
    # (the model's serrated back edge) and the lowest drops into the tail spike. They sit in the
    # hood's shadow: SHADE under a lit top rim, so they recede and the face leads. Two first passes
    # failed at 0.5x: LIGHT plates read as a fish's gills, long pointed blades as feathers; a 7.5-unit
    # rim still read as stacked plates, so the rim is RIB_RIM (5) and the rib mass reads as one shadow.
    ribs = [  # (y top, y bottom, back x, root x on the neck)
        (94.0, 117.0, 66.0, 150.0),
        (72.0, 96.0, 48.0, 144.0),
        (50.0, 74.0, 34.0, 138.0),
        (29.0, 52.0, 20.0, 132.0),
    ]
    for i, (y0, y1, tx, rx) in enumerate(ribs):
        r = (y1 - y0) / 2.0
        kx = tx + 10.0 + r                                   # the knuckle's centre
        mid = y0 + r
        knuckle = ell(kx, mid, r + 4.0, r, 270, 140, 5)      # top -> back -> lower back, 5 facets
        horn = [(tx - 2.0, y1 + 2.0)] if i else [(tx - 12.0, 127.0)]
        lobe = [(rx, y0 + 1.0)] + knuckle + horn + [(kx + 2.0, y1), (rx, y1 - 1.0), (rx + 6.0, mid)]
        parts.append(Part(P(lobe), shade_below(y0 + RIB_RIM)))

    # THE MOUTH: the gaping cavity behind both rows of teeth (navy: the hole the soul beam leaves by)
    parts.append(Part(P([(178.0, 64.0), (268.0, 62.0), (266.0, 112.0), (236.0, 110.0), (188.0, 96.0)]),
                      fill=NAVY))
    # THE LOWER JAW, hanging open: its teeth up into the mouth, then the jaw itself over their roots.
    # THREE upper fangs and three lower teeth, set between each other with navy between them: four of
    # each, packed edge to edge, read as a grille (a comb) at 0.5x rather than a fanged maw.
    for tx, ty0, h in ((208.0, 101.5, 12.0), (227.0, 105.5, 13.0), (246.0, 108.5, 12.0)):
        parts.append(fang(tx, ty0, ty0 - h, 12.0, lean=1.5, tf=M))
    jaw = [(166.0, 86.0), (190.0, 96.0), (218.0, 103.0), (246.0, 106.0), (260.0, 110.0), (252.0, 119.0),
           (222.0, 122.0), (190.0, 119.0), (164.0, 104.0)]
    parts.append(Part(P(jaw), shade_below(113.0)))
    # the drool strand off the chin (the model trails long ones; one survives 0.5x, more is noise)
    parts.append(Part(P([(232.0, 117.0), (243.0, 117.0), (237.5, 131.0)])))
    # the upper fangs, front (the model's long front tooth) to back, longest first
    for x, y1, w in ((257.0, 107.0, 15.0), (236.0, 97.0, 14.0), (214.0, 87.0, 12.0)):
        parts.append(fang(x, 66.0, y1, w, tf=M))

    # THE CRANIUM + HOOD: the crest's swept point at the back (left, its highest corner, as on the
    # model), the long crown, the brow, the snout; the underside runs back from the cheek. Two
    # facets: the crown LIGHT, the hood's overhanging under-plate SHADE behind a navy lip.
    cran = [(10.0, 2.0), (54.0, 6.0), (104.0, 8.0), (150.0, 9.0), (186.0, 13.0), (214.0, 21.0),
            (236.0, 32.0), (252.0, 45.0), (263.0, 58.0), (269.0, 68.0), (250.0, 70.0), (226.0, 69.0),
            (204.0, 69.0), (192.0, 72.0), (184.0, 88.0), (168.0, 88.0), (162.0, 62.0), (130.0, 50.0),
            (90.0, 40.0), (50.0, 32.0), (24.0, 24.0)]
    lip = [(12.0, 10.0), (50.0, 17.0), (95.0, 25.0), (140.0, 34.0), (172.0, 43.0), (190.0, 55.0),
           (196.0, 72.0)]
    under = lip + [(196.0, 140.0), (-30.0, 140.0), (-30.0, 10.0)]
    det = line(M(lip), 4.0)                                      # the hood's overhang lip
    # the tribal glyphs on the crown (the model's band): three bold bars that lean with the swept
    # crest, then a hooked key-spiral turned to the brow's slope. Upright bars beside an upright hook
    # read as the letters "IIIG" at 0.5x; leaned and turned they read as carving.
    for gx in (120.0, 131.0, 142.0):
        det += line(M([(gx + 6.0, 12.0), (gx - 2.0, 30.0)]), 4.6, cap='butt')
    key = xform([(-11.0, 9.0), (-11.0, -9.0), (11.0, -9.0), (11.0, 9.0), (-1.0, 9.0), (-1.0, 1.0)],
                169.0, 26.0, 1.0, 18.0)
    det += line(M(key), 4.0, cap='butt', join='miter')
    # the eye socket: big, deep and angular under a heavy brow, a glint in it
    sock = [(192.0, 34.0), (208.0, 24.0), (229.0, 26.0), (242.0, 39.0), (238.0, 53.0), (220.0, 59.0),
            (200.0, 52.0)]
    det += fillp(P(sock), NAVY)
    if EYE_GLOW:
        ex, ey = M([(222.0, 42.0)])[0]
        det += dot(ex, ey, EYE_GLOW, LIGHT)
    # the cheekbone: a strut from under the socket down to the hinge
    det += line(M([(200.0, 61.0), (188.0, 84.0)]), 3.4)
    parts.append(Part(P(cran), P(under), det))
    return compose(parts)


ICONS = {
    'i_tod_hud_gun_skull': nan_sapwe,
    'i_tod_hud_gun_soulstaff': soul_staff,
    'i_tod_hud_gun_crownstaff': crown_staff,
    'i_tod_hud_gun_greatsword': cyber_sword,
}


def build():
    return {name: render(fn()) for name, fn in ICONS.items()}

# ------------------------------------------------------------------------------------- review

REFS = {
    'i_tod_hud_gun_skull': ['i_tod_hud_gun_skull', 'i_tod_hud_gun_firebow'],
    'i_tod_hud_gun_soulstaff': ['i_tod_hud_gun_soulstaff', 'i_tod_hud_gun_firebow'],
    'i_tod_hud_gun_crownstaff': ['i_tod_hud_gun_crownstaff', 'i_tod_hud_gun_firebow'],
    'i_tod_hud_gun_greatsword': ['i_tod_hud_gun_greatsword', 'i_tod_hud_gun_gauntlet'],
}
LABELS = {
    'i_tod_hud_gun_skull': 'REDRAW i_tod_hud_gun_skull (SKULL OF NAN SAPWE)  |  INSTALLED: skull, firebow',
    'i_tod_hud_gun_soulstaff': 'i_tod_hud_gun_soulstaff (SOUL STAFF, open jaw)  |  INSTALLED: soulstaff, firebow',
    'i_tod_hud_gun_crownstaff': 'i_tod_hud_gun_crownstaff (CROWN OF THE DAMNED, open jaw)  |  INSTALLED: crownstaff, firebow',
    'i_tod_hud_gun_greatsword': 'i_tod_hud_gun_greatsword (CYBER SWORD)  |  INSTALLED: greatsword, gauntlet',
}
SOURCES = {   # the model renders each icon was drawn from (shown beside it in the review)
    'i_tod_hud_gun_skull': ['art/generated/R1-truth-renders/skull_side.png',
                            'art/generated/R1-truth-renders/skull_34.png'],
    'i_tod_hud_gun_soulstaff': ['art/necro_staff/tier2_full.png', 'art/necro_staff/tier2_head.png'],
    'i_tod_hud_gun_crownstaff': ['art/necro_staff/tier3_full.png', 'art/necro_staff/tier3_head.png'],
    'i_tod_hud_gun_greatsword': ['art/cyber_sword/native_oblique.png', 'art/cyber_sword/native_hilt.png'],
}
NEIGHBOUR = {   # the INSTALLED cell shown under the new one: the same-name cell it replaces
    'i_tod_hud_gun_skull': 'i_tod_hud_gun_skull',
    'i_tod_hud_gun_soulstaff': 'i_tod_hud_gun_soulstaff',
    'i_tod_hud_gun_crownstaff': 'i_tod_hud_gun_crownstaff',
    'i_tod_hud_gun_greatsword': 'i_tod_hud_gun_greatsword',
}
LADDER = ['i_tod_hud_gun_skull', 'i_tod_hud_gun_soulstaff', 'i_tod_hud_gun_crownstaff']   # tiers 1-3
KEPT = {   # judged against the truth render at 144 x 66 and kept as shipped (the review shows why)
    'i_tod_hud_gun_bow': 'art/generated/R1-truth-renders/bow_side.png',
    'i_tod_hud_gun_firebow': 'art/generated/R1-truth-renders/firebow_side.png',
    'i_tod_hud_gun_fist': 'art/generated/R1-truth-renders/fisth_r270_side.png',
    'i_tod_hud_gun_gauntlet': 'art/generated/R1-truth-renders/gauntlet_side.png',
}


def onscreen(icon):
    """The icon where the player sees it: the gun plate at 1080p (1.5 px per canvas unit; plate at
    canvas x1002 y606, 264 x 72), the icon in the 96 x 44 gun bay at x1008 y632 -> 144 x 66 px."""
    plate = Image.open(artgen.shipped('i_tod_h2_gun_plate')).convert('RGBA')
    pw, ph = 396, 108
    bg = Image.new('RGBA', (pw, ph), (18, 18, 24, 255))
    bg.alpha_composite(plate.resize((pw, ph), Image.LANCZOS))
    bg.alpha_composite(icon.resize((144, 66), Image.BILINEAR), (9, 39))
    return bg


def review(images, out_dir):
    """_review.png: (1) each icon beside the shipped cells it must match, at full size; (2) each at its
    real on-screen size on the gun plate, beside the model render it was drawn from and the shipped
    cell the player sees just before it (the promotion's before/after), plus a 2x zoom of the bay."""
    font = artgen.ttf(16)
    rows = []
    for name, im in images.items():
        rows.append((LABELS[name], [im] + [artgen.shipped(r) for r in REFS[name]]))
    sheet1 = artgen.contact_sheet(rows, os.path.join(out_dir, '_review_part1.png'), height=132)
    s1 = Image.open(sheet1).convert('RGBA')
    os.remove(sheet1)
    blocks = []
    for name, im in images.items():
        a = onscreen(im)
        b = onscreen(Image.open(artgen.shipped(NEIGHBOUR[name])).convert('RGBA'))
        zoom = a.crop((0, 30, 170, 108)).resize((340, 156), Image.NEAREST)
        thumbs = []
        for rel in SOURCES[name]:
            th = Image.open(os.path.join(ROOT, rel)).convert('RGBA')
            th.thumbnail((210, 230))
            thumbs.append(th)
        src = Image.new('RGBA', (sum(th.width for th in thumbs) + 8 * (len(thumbs) - 1),
                                 max(th.height for th in thumbs)), (28, 30, 38, 255))
        sx = 0
        for th in thumbs:
            src.alpha_composite(th, (sx, 0))
            sx += th.width + 8
        blocks.append((name, a, b, zoom, src))
    bw = max(a.width + b.width + z.width + s.width for _, a, b, z, s in blocks) + 60
    bh = sum(max(z.height, s.height, a.height + b.height + 8) + 34 for _, a, b, z, s in blocks) + 40
    part2 = Image.new('RGBA', (bw, bh), (28, 30, 38, 255))
    d = ImageDraw.Draw(part2)
    d.text((12, 8), 'ON THE GUN PLATE AT 1080P (144 x 66): new (top), the installed cell (below) | 2x zoom | model',
           fill=(220, 225, 235, 255), font=font)
    y = 40
    for name, a, b, z, s in blocks:
        d.text((12, y), name, fill=(170, 180, 200, 255), font=font)
        y += 24
        part2.alpha_composite(a, (12, y))
        part2.alpha_composite(b, (12, y + a.height + 8))
        part2.alpha_composite(z, (24 + a.width, y))
        part2.alpha_composite(s, (36 + a.width + z.width, y))
        y += max(z.height, s.height, a.height + b.height + 8) + 10
    # (3) the Necromancer's ladder as the player meets it, tier 1 -> 3, NEW above INSTALLED
    lad = [n for n in LADDER if n in images]
    part3 = Image.new('RGBA', (12 + len(lad) * 408, 300), (28, 30, 38, 255))
    d = ImageDraw.Draw(part3)
    d.text((12, 8), 'THE NECROMANCER LADDER, TIER 1 -> 3, AT 1080P: new (top) | installed (below)',
           fill=(220, 225, 235, 255), font=font)
    for i, name in enumerate(lad):
        part3.alpha_composite(onscreen(images[name]), (12 + i * 408, 40))
        part3.alpha_composite(onscreen(Image.open(artgen.shipped(name)).convert('RGBA')), (12 + i * 408, 160))
    # (4) the class icons judged against their truth renders and KEPT
    kept = [(n, onscreen(Image.open(artgen.shipped(n)).convert('RGBA')), rel) for n, rel in KEPT.items()
            if os.path.exists(os.path.join(ROOT, rel))]
    part4 = Image.new('RGBA', (12 + 2 * 640, 40 + ((len(kept) + 1) // 2) * 262), (28, 30, 38, 255))
    d = ImageDraw.Draw(part4)
    d.text((12, 8), 'JUDGED AND KEPT: the shipped icon at 1080p beside its truth render (each reads as '
           'what it is at 144 x 66)', fill=(220, 225, 235, 255), font=font)
    for i, (name, a, rel) in enumerate(kept):
        x, y = 12 + (i % 2) * 640, 40 + (i // 2) * 262
        d.text((x, y), name, fill=(170, 180, 200, 255), font=font)
        part4.alpha_composite(a, (x, y + 24))
        th = Image.open(os.path.join(ROOT, rel)).convert('RGBA')
        th.thumbnail((220, 230))
        tb = Image.new('RGBA', th.size, (200, 202, 210, 255))
        tb.alpha_composite(th)
        part4.alpha_composite(tb, (x + 404, y + 24))
    parts_ = [s1, part2, part3, part4]
    full = Image.new('RGBA', (max(p.width for p in parts_), sum(p.height for p in parts_)), (28, 30, 38, 255))
    y = 0
    for p in parts_:
        full.alpha_composite(p, (0, y))
        y += p.height
    out = os.path.join(out_dir, '_review.png')
    full.save(out)
    return out

# -------------------------------------------------------------------------------------- check

def _read(p):
    with open(p, 'rb') as f:
        return f.read()


def check(root):
    fails = []
    images = build()
    for name, im in images.items():
        p = os.path.join(root, 'source_data', 'tod_ui_images', '_images', name + '.png')
        if not os.path.exists(p):
            fails.append('%s: not installed (%s)' % (name, p))
        elif _read(p) != artgen.png_bytes(im):
            fails.append('%s: installed PNG differs from the generator (re-run --install; never hand-edit)' % name)
    gdt = _read(os.path.join(root, 'source_data', 'tod_ui_images.gdt')).decode('utf-8', 'replace')
    zone = _read(os.path.join(root, 'zone_source', 'zm_tod2_cybercity.zone')).decode('utf-8', 'replace')
    lua = _read(os.path.join(root, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets',
                             'AetheriumLoadout.lua')).decode('utf-8', 'replace')
    lua_code = re.sub(r'--[^\n]*', '', lua)        # rows in comments do not count
    zlines = set(l.strip() for l in zone.splitlines())
    for name in ALL_IMAGES:
        blk = re.search(r'"%s" \( "image\.gdf" \)\s*\{(.*?)\n\s*\}' % re.escape(name), gdt, re.S)
        if not blk:
            fails.append('%s: no image.gdf block in source_data/tod_ui_images.gdt' % name)
        else:
            b = blk.group(1)
            if '"baseImage" "source_data/tod_ui_images/_images/%s.png"' % name not in b:
                fails.append('%s: GDT block does not point at its PNG' % name)
            if '"compressionMethod" "compressed high color"' not in b:
                fails.append('%s: GDT block is not "compressed high color" (its neighbours are)' % name)
        if 'image,' + name not in zlines:
            fails.append('%s: no "image,%s" line in zone_source/zm_tod2_cybercity.zone - the gun bay '
                         'would draw a WHITE SQUARE (the name is built at runtime; lint GATE A cannot see '
                         'it)' % (name, name))
    for disp, slug in LUA_ROWS.items():
        if not re.search(r'\[\s*"%s"\s*\]\s*=\s*"%s"' % (re.escape(disp), slug), lua_code):
            fails.append('AetheriumLoadout.lua: TOD_NAME_CAT has no [ "%s" ] = "%s" row' % (disp, slug))
    for stem, slug in LUA_STEMS.items():
        if not re.search(r'\[\s*"%s"\s*\]\s*=\s*"%s"' % (stem, slug), lua_code):
            fails.append('AetheriumLoadout.lua: TOD_GUN_CAT has no [ "%s" ] = "%s" row' % (stem, slug))
    for name, im in images.items():   # the style contract: three colours, binary alpha, 288 x 132
        a = np.array(im)
        cols = {tuple(int(v) for v in c) for c in a[a[..., 3] > 0][:, :3]}
        if im.size != (W, H) or not cols <= set(PAL) or not set(np.unique(a[..., 3])) <= {0, 255}:
            fails.append('%s: off-style (size %s, colours %s)' % (name, im.size, sorted(cols)))
    if fails:
        print('GUN BAY ICONS FAILED (%d):' % len(fails))
        for f in fails:
            print('  * ' + f)
        return 1
    print('GUN BAY ICONS OK %d (bytes = generator; 3-tone style; GDT + zone + Lua rows wired)' % len(images))
    return 0


def main():
    ap = argparse.ArgumentParser(description='PK06 HUD gun-bay icons (soul staff, crown staff, cyber sword)')
    ap.add_argument('--install', action='store_true',
                    help='write the PNGs into <out-root>/source_data/tod_ui_images/_images/')
    ap.add_argument('--out-root', default=ROOT, help='install root (default: the repo)')
    ap.add_argument('--check', action='store_true', help='build gate: bytes + style + wiring')
    ap.add_argument('--root', default=ROOT, help='tree --check reads (default: the repo)')
    ap.add_argument('--out', default=None, help='render folder (default art/generated/%s)' % PACK)
    a = ap.parse_args()
    if a.check:
        sys.exit(check(a.root))
    images = build()
    if a.install:
        dst = os.path.join(a.out_root, 'source_data', 'tod_ui_images', '_images')
        for name, im in images.items():
            print('installed %s.png  md5 %s' % (name, artgen.save_png(im, os.path.join(dst, name + '.png'))))
        return
    out_dir = a.out or artgen.stage_dir(PACK)
    os.makedirs(out_dir, exist_ok=True)
    for name, im in images.items():
        md5 = artgen.save_png(im, os.path.join(out_dir, name + '.png'))
        print('%s.png  %dx%d  md5 %s' % (name, im.width, im.height, md5))
    print('review ->', review(images, out_dir))


if __name__ == '__main__':
    main()
