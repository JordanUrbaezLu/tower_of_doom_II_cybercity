"""PK05 - THE WHITE GLYPH ICON SET (2026-10-04, tmp/asset_prod/packs/PK05-white-glyph-icons.json).

WHAT IT MAKES. Fifteen 128x128 RGBA icons in the WHITE GLYPH style (the pause menu V2 row icons
i_tod_pm_ico_*): a flat white silhouette with negative-space cuts and a soft white outer glow, tinted at
runtime (magenta / violet / idle grey-blue in the pause + scoreboard rows).

W3B (2026-10-05): the two HUD V2 tile twins this pack drew (i_tod_h2_ab_cloak, i_tod_h2_ab_soul_bomb) are
drawn IN COLOUR from these same drawings by tools/artgen/packs/w3b_ability_colour.py, whose --check gates
them; the V1 kit key i_tod_hud_off_cloak (never drawn while USE_HUD_V2) was retired whole - PNG in
archive/retired_20261005_ability_glyphs/, its zone line, GDT block and H2_AB remap row gone.

  13 live upgrade cards that fell to i_tod_pm_ico_generic in the pause menu + scoreboard:
    i_tod_pm_ico_sprint (29) deadeye (6) quickdraw (35) piercing (26)          - Archer
    i_tod_pm_ico_adrenaline (25) fusion (36)                                    - Breacher
    i_tod_pm_ico_vitality (37) armsspecialist (7) cleave (48) demonslayer (12) - Warrior
    i_tod_pm_ico_reapersreach (5) summonermaster (19) cloak (9)                - Necromancer
  the empty AI COMPANION well: i_tod_pm_ico_companion
  the Necromancer's Invisibility Cloak row icon: i_tod_pm_ico_cloak
  the SOUL PULSE redraw (the retired lit-fuse bomb is gone): i_tod_pm_ico_soulbomb

THE STYLE IS MEASURED, NOT GUESSED (the shipped pm_ico_grapple / bash / c4 / luck / riotshield and, then,
h2_ab_summon - retired 2026-10-05, pm_ico_summonpower stands in): RGB 255 wherever alpha > 0, (0,0,0,0)
elsewhere; the core is alpha 255; the glow is a Gaussian of the core (sigma GLOW_SIGMA px at 128) times
GLOW_GAIN, composited under it. --measure prints the glow profile (mean alpha 2/4/6/8/10 px from the core
edge) of the references beside ours.

EVERY GLYPH IS FITTED, NOT PLACED BY HAND: each drawing is rendered once, its core bounding box
measured, and the whole drawing scaled + centred so its longest side is FIT_BOX px (the shipped
icons measure 81..111) inside a 128 canvas. That keeps the glow (about 12 px) off the canvas edge -
a glyph touching the edge shows a hard cut where its glow is clipped - and gives the set one visual
weight.

THE SIZE THEY ARE READ AT (AetheriumStartMenu.lua / AetheriumScoreboard.lua / AetheriumLoadout.lua):
the pause row glyph is 40 x RS (67/63) = 42.5 canvas units = 64 px at 1080p; the scoreboard row 24 x
(43/38) = 27.2 units = 41 px; the HUD V2 ability tile 24 units = 36 px. So every drawing is a few
bold shapes and every cut is wide enough to survive 41 px. _context.png shows them at those sizes.

    python -B tools/artgen/packs/pk05_glyph_icons.py                 # write art/generated/PK05-white-glyph-icons/ + _review.png + _context.png
    python -B tools/artgen/packs/pk05_glyph_icons.py --install [--out-root DIR]
                                                                     # also copy the PNGs into <root>/source_data/tod_ui_images/_images/
    python -B tools/artgen/packs/pk05_glyph_icons.py --check [--out-root DIR]
                                                                     # regenerate in memory, fail on any byte that differs (build gate)
    python -B tools/artgen/packs/pk05_glyph_icons.py --measure       # glow profile + coverage of each icon vs the references

Deterministic: no randomness, no timestamps. Never hand-edit an output; change this file and re-run.
"""
import argparse, math, os, sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402

PACK = 'PK05-white-glyph-icons'
S = 128                      # every icon is 128 x 128
SS = 8                       # rendered at 1024 and box-averaged down (exact coverage, no Lanczos ringing)
GLOW_SIGMA = 5.0             # px at 128 (fitted to the shipped icons' glow profile)
GLOW_GAIN = 0.66
FIT_BOX = 102                # the fitted glyph's longest side (px at 128)

W = '#ffffff'                # positive
K = '#000000'                # cut (the luminance mask makes black = transparent)

# ===================================================================================== primitives

def rect(x, y, w, h, fill=W, rx=0):
    return '<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s"/>' % (x, y, w, h, rx, fill)


def circle(cx, cy, r, fill=W):
    return '<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (cx, cy, r, fill)


def ellipse(cx, cy, rx, ry, fill=W, rot=0):
    t = ' transform="rotate(%g %g %g)"' % (rot, cx, cy) if rot else ''
    return '<ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="%s"%s/>' % (cx, cy, rx, ry, fill, t)


def path(d, fill=W, extra=''):
    return '<path d="%s" fill="%s"%s/>' % (d, fill, extra)


def cut_outline(d, w):
    """The same path stroked in K: a cut gap of w/2 round a shape drawn over others."""
    return path(d, K, ' stroke="%s" stroke-width="%g" stroke-linejoin="round"' % (K, w))


def poly(pts, fill=W):
    return '<polygon points="%s" fill="%s"/>' % (' '.join('%g,%g' % p for p in pts), fill)


def line(x1, y1, x2, y2, w, color=W, cap='round'):
    return ('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g" stroke-linecap="%s"/>'
            % (x1, y1, x2, y2, color, w, cap))


def stroke_path(d, w, color=W, cap='round', join='round'):
    return ('<path d="%s" fill="none" stroke="%s" stroke-width="%g" stroke-linecap="%s" stroke-linejoin="%s"/>'
            % (d, color, w, cap, join))


def ring(cx, cy, r, w, color=W):
    return '<circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" stroke-width="%g"/>' % (cx, cy, r, color, w)


def arc(cx, cy, r, a0, a1, w, color=W, cap='round'):
    """An arc of radius r from angle a0 to a1 (degrees, 0 = +x, clockwise on screen)."""
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return stroke_path('M%g,%g A%g,%g 0 %d 1 %g,%g' % (x0, y0, r, r, large, x1, y1), w, color, cap)


def group(body, tf):
    return '<g transform="%s">%s</g>' % (tf, body)


def star(cx, cy, n, r_out, r_in, rot=-90, jitter=None):
    """n-point star polygon; jitter = list of n outer-radius multipliers (an irregular blast)."""
    pts = []
    for i in range(n * 2):
        a = math.radians(rot + i * 180.0 / n)
        r = r_out * (jitter[i // 2] if jitter else 1.0) if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def bez(p0, p1, p2, p3, t):
    u = 1.0 - t
    return tuple(u * u * u * a + 3 * u * u * t * b + 3 * u * t * t * c + t * t * t * d for a, b, c, d in zip(p0, p1, p2, p3))


def heart_d(cx, cy, w, h):
    """A heart: two lobes and a point, w wide and h tall, centred on (cx, cy)."""
    x0, y0 = cx - w / 2.0, cy - h / 2.0
    lob = w * 0.5
    return ('M{cx},{yb} C{l1x},{l1y} {x0},{m} {x0},{t} '
            'C{x0},{yt} {lc},{y0} {lx},{y0} C{lr},{y0} {cx},{dip0} {cx},{dip} '
            'C{cx},{dip0} {rl},{y0} {rx},{y0} C{rc},{y0} {x1},{yt} {x1},{t} '
            'C{x1},{m} {r1x},{l1y} {cx},{yb} Z').format(
        cx=cx, yb=y0 + h, x0=x0, x1=x0 + w, y0=y0,
        l1x=cx - w * 0.16, l1y=y0 + h * 0.82, m=y0 + h * 0.56, t=y0 + h * 0.30, yt=y0 + h * 0.10,
        lc=x0 + lob * 0.18, lx=x0 + lob * 0.50, lr=x0 + lob * 0.86, dip0=y0 + h * 0.04, dip=y0 + h * 0.20,
        rl=x0 + w - lob * 0.86, rx=x0 + w - lob * 0.50, rc=x0 + w - lob * 0.18, r1x=cx + w * 0.16)


def skull(cx, cy, s=1.0):
    """A front skull, cranium centre (cx, cy); s = 1 -> 40 wide, 46 tall. Eyes / nose / teeth are cuts."""
    def p(x, y):
        return cx + x * s, cy + y * s
    b = [circle(cx, cy, 20 * s)]
    jx, jy = p(-13, 6)
    b.append(rect(jx, jy, 26 * s, 20 * s, W, 5 * s))
    # cheek notches (the jaw is narrower than the cranium)
    b.append(path('M%g,%g Q%g,%g %g,%g L%g,%g Z' % (p(-20, 4) + p(-16, 14) + p(-13, 16) + p(-13, 10)), K))
    b.append(path('M%g,%g Q%g,%g %g,%g L%g,%g Z' % (p(20, 4) + p(16, 14) + p(13, 16) + p(13, 10)), K))
    ex, ey = p(-8, 3)
    b.append(ellipse(ex, ey, 6.2 * s, 6.8 * s, K))
    ex, ey = p(8, 3)
    b.append(ellipse(ex, ey, 6.2 * s, 6.8 * s, K))
    b.append(poly([p(0, 9.5), p(-3.4, 15), p(3.4, 15)], K))
    for tx in (-6.5, 0, 6.5):
        x, y = p(tx, 18.5)
        b.append(rect(x - 1.3 * s, y, 2.6 * s, 8.5 * s, K))
    return ''.join(b)


def horned_skull(cx, cy, s=1.0):
    """The skull with two crescent horns sweeping up and out of the temples."""
    b = []
    for sgn in (-1, 1):
        def q(x, y):
            return cx + sgn * x * s, cy + y * s
        b.append(path('M%g,%g Q%g,%g %g,%g Q%g,%g %g,%g Z' % (q(-17, -12) + q(-36, -18) + q(-40, -50) + q(-24, -30) + q(-7, -19))))
    b.append(skull(cx, cy, s))
    return ''.join(b)


def zhead(cx, cy, r, eyes_dy=-6):
    """A dead zombie head: a disc with two X eyes cut out of it (the card art's X-eyed heads)."""
    b = [circle(cx, cy, r)]
    for ex in (cx - r * 0.4, cx + r * 0.4):
        ey = cy + eyes_dy * r / 17.0
        d = r * 0.17
        w = 3.4 * r / 17.0
        b.append(line(ex - d, ey - d, ex + d, ey + d, w, K, 'butt'))
        b.append(line(ex - d, ey + d, ex + d, ey - d, w, K, 'butt'))
    return ''.join(b)


def sword(blade_w=12, tip=-60, guard_y=10, guard_w=40):
    """An upright sword in a local frame, tip up at y=tip: blade, crossguard, grip, pommel."""
    hw = blade_w / 2.0
    return (poly([(-hw, guard_y), (-hw, tip + 12), (0, tip), (hw, tip + 12), (hw, guard_y)]) +
            rect(-guard_w / 2.0, guard_y, guard_w, 8, W, 3.5) + rect(-4.5, guard_y + 8, 9, 17, W) +
            circle(0, guard_y + 30, 6.5))


def sword_cut(blade_w=12, tip=-60, guard_y=10, guard_w=40, g=4.5):
    """The cut gap round sword(): drawn first so the sword stands clear of what it crosses."""
    hw = blade_w / 2.0 + g
    return (poly([(-hw, guard_y), (-hw, tip + 10), (0, tip - g * 1.4), (hw, tip + 10), (hw, guard_y)], K) +
            rect(-guard_w / 2.0 - g, guard_y - g, guard_w + 2 * g, 8 + 2 * g, K, 6) +
            rect(-4.5 - g, guard_y + 8, 9 + 2 * g, 17, K) + circle(0, guard_y + 30, 6.5 + g, K))


def arrow_local(L, shaft=6.5, gap=4.0):
    """A right-pointing arrow in a local frame from x=0 (fletching) to x=L+15 (tip), with its own
    cut gap drawn first so it reads clear of anything under it."""
    cut = (line(12, 0, L, 0, shaft + 2 * gap, K, 'butt') +
           poly([(L - 6, -11 - gap * 1.2), (L + 15 + gap * 1.5, 0), (L - 6, 11 + gap * 1.2)], K))
    body = (line(16, 0, L, 0, shaft, W, 'butt') + poly([(L - 4, -11), (L + 15, 0), (L - 4, 11)]) +
            poly([(0, -9), (13, -9), (19, 0), (13, 9), (0, 9), (6, 0)]))
    return cut + body

# ===================================================================================== the icons

def ico_soul_pulse():
    """SOUL PULSE: a skull at the centre of the pulse it throws - a solid ring and a wider ring
    breaking up as it expands (i_tod_card2_art_soul_pulse's flat white ring). No fuse, no bomb."""
    b = [skull(64, 59, 0.95)]
    b.append(ring(64, 64, 36.5, 6.5))
    for i in range(4):
        a0 = -90 + 45 + i * 90 - 30
        b.append(arc(64, 64, 52, a0 + 4, a0 + 56, 5.0))
    return ''.join(b)


CLOAK_FIG = ('M52,12 C40,12 32,24 31,38 C30,48 27,56 24,66 L16,114 Q50,108 86,114 '
             'L80,66 C77,56 74,48 73,38 C72,24 64,12 52,12 Z')


def ico_cloak():
    """INVISIBILITY CLOAK: a hooded figure whose right side dissolves into vertical streaks
    (i_tod_card2_art_cloak). The face is a void with two eye glints."""
    b = [path(CLOAK_FIG)]
    b.append(ellipse(52, 40, 11.5, 14.5, K))                                  # the face void
    b.append(path('M41.5,40 Q52,30 62.5,40 L62.5,44 Q52,36 41.5,44 Z', K))   # the hood's brow
    b.append(ellipse(47.2, 43, 3.0, 2.2, W, -12))                             # eye glints
    b.append(ellipse(56.8, 43, 3.0, 2.2, W, 12))
    # the dissolve: vertical cuts through the right of the figure, then streaks beyond it
    for x, top in ((64, 54), (72, 50)):
        b.append(rect(x, top, 3.6, 70, K))
    for x, y0, y1, w in ((84, 46, 104, 5.0), (93, 54, 100, 4.4), (101, 62, 96, 3.8), (109, 72, 90, 3.2)):
        b.append(line(x, y0, x, y1, w))
    return ''.join(b)


def ico_companion():
    """THE AI COMPANION's empty well: a robot head - antenna, visor with two eyes, ear bolts, grille."""
    b = [line(64, 36, 64, 22, 5.5), circle(64, 17, 7)]
    b.append(rect(28, 34, 72, 64, W, 16))
    b.append(rect(17, 52, 14, 28, W, 4))
    b.append(rect(97, 52, 14, 28, W, 4))
    b.append(rect(17, 63, 14, 6, K))            # ear seams
    b.append(rect(97, 63, 14, 6, K))
    b.append(rect(36, 47, 56, 25, K, 12.5))     # visor
    b.append(rect(46, 53, 13, 13, W, 4))         # eyes
    b.append(rect(69, 53, 13, 13, W, 4))
    for x in (46, 57, 68, 79):                   # grille
        b.append(rect(x, 80, 6.5, 9, K, 1.5))
    return ''.join(b)


def ico_sprint():
    """SPRINT: a running boot leaning into the stride, three speed lines behind it
    (i_tod_card2_art_sprint)."""
    boot = ('M46,16 L76,16 Q81,16 81,21 L80,50 C90,52 104,56 112,64 Q118,70 116,78 L114,84 '
            'L42,84 L38,24 Q38,16 46,16 Z')
    sole = 'M40,90 L116,90 Q118,100 108,102 L46,102 Q38,102 39,94 Z'
    inner = (path(boot) + path(sole) + rect(36, 26, 48, 5.5, K) +
             line(66, 47, 81, 40, 4.6, K, 'butt') + line(66, 57, 81, 50, 4.6, K, 'butt') +
             rect(58, 95, 5, 9, K) + rect(76, 95, 5, 9, K) + rect(94, 95, 5, 9, K))
    b = [group(inner, 'rotate(-10 78 60)')]
    for y, x0, x1 in ((42, 12, 30), (60, 6, 32), (78, 14, 34)):
        b.append(line(x0, y, x1, y, 6.5))
    return ''.join(b)


def ico_deadeye():
    """DEADEYE: a drawn bow - limbs bulging toward the target, the string pulled back into a V at
    the nock - its arrow aimed into a reticle with an eye in it (i_tod_card2_art_deadeye)."""
    b = [stroke_path('M34,12 C55,26 59,46 59,64 C59,82 55,102 34,116', 11),
         stroke_path('M34,14 L15,64 L34,114', 4.6, W, 'round', 'miter'),
         rect(54, 53, 11, 22, W, 3.5),                                         # grip
         line(15, 64, 74, 64, 8, W, 'butt'),                                   # shaft
         poly([(71, 53), (89, 64), (71, 75)]),                                 # head
         poly([(12, 55), (25, 55), (31, 64), (25, 73), (12, 73), (18, 64)])]   # fletching
    cx, cy, R = 112, 64, 19
    b.append(ring(cx, cy, R, 8))
    for dx, dy in ((0, -1), (0, 1), (1, 0)):
        b.append(line(cx + dx * (R + 3), cy + dy * (R + 3), cx + dx * (R + 12), cy + dy * (R + 12), 8, W, 'butt'))
    b.append(path('M%g,%g Q%g,%g %g,%g Q%g,%g %g,%g Z' % (cx - 13, cy, cx, cy - 12, cx + 13, cy, cx, cy + 12, cx - 13, cy)))
    b.append(circle(cx, cy, 5.2, K))                                           # pupil
    b.append(circle(cx - 1.6, cy - 1.6, 1.9, W))                               # its glint
    return ''.join(b)


def ico_quickdraw():
    """QUICK DRAW: a fast arrow across a stopwatch (i_tod_card2_art_quick_draw)."""
    cx, cy = 70, 56
    b = [circle(cx, cy, 34), circle(cx, cy, 26, K),
         rect(cx - 7, 13, 14, 8, W, 2), rect(cx - 3.5, 18, 7, 6, W),                          # crown
         group(rect(-4, -38, 8, 9, W, 2), 'translate(%g,%g) rotate(45)' % (cx, cy)),            # side button
         line(cx, cy, cx + 13, cy - 13, 5.5), circle(cx, cy, 5)]                                 # the hand
    for a in range(0, 360, 90):                                                                  # quarter ticks
        b.append(circle(cx + 20 * math.cos(math.radians(a)), cy + 20 * math.sin(math.radians(a)), 2.4))
    ay = 98                                                  # the arrow, in front, with a cut gap round it
    b.append(line(14, ay, 104, ay, 15, K, 'butt'))
    b.append(poly([(98, ay - 14), (122, ay), (98, ay + 14)], K))
    b.append(line(26, ay, 104, ay, 6, W, 'butt'))
    b.append(poly([(100, ay - 9.5), (118, ay), (100, ay + 9.5)]))
    b.append(poly([(14, ay - 8), (26, ay - 8), (32, ay), (26, ay + 8), (14, ay + 8), (20, ay)]))
    return ''.join(b)


def ico_piercing():
    """PIERCING: one arrow driven through three X-eyed zombie heads on a rising diagonal
    (i_tod_card2_art_piercing). The arrow runs below the heads' centres so their eyes stay clear,
    and a sliver of every head shows on its far side - through them, not in front."""
    r = 19
    cs = [(30, 96), (64, 64), (98, 32)]
    b = [zhead(x, y, r, -8.5) for x, y in cs]
    d0 = math.hypot(34, 32)
    dx, dy = 34 / d0, -32 / d0
    nx, ny = -dy, dx
    off = 8.5
    sx, sy = cs[0][0] - 28 * dx + off * nx, cs[0][1] - 28 * dy + off * ny
    ex, ey = cs[2][0] + 20 * dx + off * nx, cs[2][1] + 20 * dy + off * ny
    ang = math.degrees(math.atan2(ey - sy, ex - sx))
    b.append(group(arrow_local(math.hypot(ex - sx, ey - sy)), 'translate(%g,%g) rotate(%g)' % (sx, sy, ang)))
    return ''.join(b)


def chevron(x, y0, h, depth, t):
    """A solid right-pointing chevron, top-left at (x, y0), h tall, tip depth px, arm thickness t."""
    m = y0 + h / 2.0
    return poly([(x, y0), (x + t, y0), (x + t + depth, m), (x + t, y0 + h), (x, y0 + h), (x + depth, m)])


def ico_adrenaline():
    """ADRENALINE: three speed chevrons charging out of an explosion (i_tod_card2_art_adrenaline)."""
    jit = [1.0, 0.78, 0.95, 0.72, 1.0, 0.8, 0.92, 0.75, 0.98]
    b = [poly(star(32, 66, 9, 27, 13, -90, jit)), circle(32, 66, 7, K)]
    for x in (46, 67, 88):
        b.append(chevron(x - 2, 34, 64, 22, 14))
    return ''.join(b)


def ico_fusion():
    """EXPLOSIVE FUSION: a blast with a healing cross cut through it (i_tod_card2_art_explosive_fusion:
    your own explosions heal you)."""
    jit = [1.0, 0.86, 0.97, 0.84, 1.0, 0.88, 0.95, 0.85, 1.0, 0.87]
    return (poly(star(64, 72, 10, 50, 33, -90, jit)) +
            rect(55, 48, 18, 48, K, 3) + rect(40, 63, 48, 18, K, 3))


def ico_vitality():
    """VITALITY: a heart with a healing cross cut through it (i_tod_card2_art_vitality)."""
    return path(heart_d(64, 66, 100, 90)) + rect(56, 40, 16, 46, K, 3) + rect(41, 55, 46, 16, K, 3)


def ico_armsspecialist():
    """ARMS SPECIALIST: a spiked cyber gauntlet's fist round a sword's grip, the blade up-right
    (i_tod_card2_art_arms_specialist). Drawn upright in a local frame, turned 45 degrees."""
    tf = 'translate(60,62) rotate(45)'
    blade = sword(blade_w=14, tip=-70, guard_y=4, guard_w=46)
    fist = (rect(-26, 8, 48, 34, K, 10) +                                     # cut gap round the fist
            rect(-18, 12, 36, 26, W, 6) + rect(-18, 19, 24, 3, K) + rect(-18, 26.5, 24, 3, K) +   # fingers
            rect(8, 12, 10, 26, W, 4) + rect(6.5, 12, 2.6, 26, K) +           # thumb
            poly([(-18, 12), (-27, 16), (-18, 20)]) + poly([(-18, 21), (-27, 25), (-18, 29)]) +
            poly([(-18, 30), (-27, 34), (-18, 38)]) +                         # knuckle spikes
            rect(-13, 38, 26, 22, W, 3) + rect(-13, 46, 26, 3.2, K))          # armoured cuff
    return group(blade, tf) + group(fist, tf)


def ico_cleave():
    """CLEAVE: one swing's blade trail slicing through three X-eyed heads at once
    (i_tod_card2_art_cleave). The trail is asymmetric - a thin tail low-left swelling to a sharp
    leading edge up-right - so it reads as MOTION (a symmetric arc read as a crown / a hill). It
    crosses each head below its eyes: the eyes stay whole above it, a chin shows below it."""
    O = ((6, 100), (26, 44), (86, 12), (124, 36))      # outer edge, tail -> leading tip
    I = ((124, 36), (92, 28), (36, 54), (6, 100))      # inner edge, back to the tail
    b = []
    for t in (0.31, 0.57, 0.83):
        po, pi = bez(*O, t), bez(*I[::-1], t)
        b.append(zhead((po[0] + pi[0]) / 2, (po[1] + pi[1]) / 2 - 5, 18, -7))
    d = 'M%g,%g C%g,%g %g,%g %g,%g C%g,%g %g,%g %g,%g Z' % (O[0] + O[1] + O[2] + O[3] + I[1] + I[2] + I[3])
    b.append(cut_outline(d, 10))
    b.append(path(d))
    return ''.join(b)


def ico_demonslayer():
    """DEMON SLAYER: a horned demon skull with a sword driven across it, through the jaw so the
    eyes stay clear (i_tod_card2_art_demon_slayer). The horns keep it apart from BOUNTY's plain skull."""
    tf = 'translate(67,92) rotate(54) scale(1.12)'
    return horned_skull(64, 56, 1.06) + group(sword_cut(), tf) + group(sword(), tf)


def ico_reapersreach():
    """REAPER'S REACH: the skull on its staff throwing a long beam that widens and forks at its end
    (i_tod_card2_art_reapers_reach)."""
    L = 70
    beam = (poly([(0, -6.5), (L - 10, -15), (L - 10, 15), (0, 6.5)]) +
            line(L - 12, -11, L + 6, -22, 7) + line(L - 12, 0, L + 11, 0, 7) + line(L - 12, 11, L + 6, 22, 7))
    return (line(25, 104, 10, 126, 9) + skull(32, 78, 1.05) +
            group(beam, 'translate(60,66) rotate(-40)'))


def ico_summonermaster():
    """SUMMONER MASTER: a summoned hand rising out of its ring, reaching up to a heart
    (i_tod_card2_art_summoner_master: your helpers' kills raise your max health)."""
    b = [stroke_path('M16,106 A48,12 0 0 1 112,106', 6.5)]                        # ring, back arc
    # the hand: forearm, palm, four fingers up (cuts between them), thumb out to the left
    b.append(rect(55, 84, 18, 28, W, 2) + rect(46, 62, 36, 28, W, 8) +
             rect(46, 46, 8, 22, W, 4) + rect(55.5, 42, 8, 26, W, 4) +
             rect(65, 43, 8, 25, W, 4) + rect(74.5, 48, 7.5, 20, W, 3.75) +
             path('M47,74 L38,62 Q35,57 39,55 Q43,53 46,58 L52,66 Z'))
    for x in (54.1, 63.6, 73.1):
        b.append(rect(x, 44, 1.6, 22, K))
    b.append(stroke_path('M16,106 A48,12 0 0 0 112,106', 13, K))                 # ring, front arc
    b.append(stroke_path('M16,106 A48,12 0 0 0 112,106', 6.5))
    b.append(path(heart_d(64, 18, 44, 36)))
    return ''.join(b)

# ===================================================================================== rendering

ICONS = [
    # (output name, builder, review note, shipped references it must match)
    ('i_tod_pm_ico_sprint', ico_sprint, 'SPRINT 29 (Archer)', ['i_tod_card2_art_sprint', 'i_tod_pm_ico_grapple']),
    ('i_tod_pm_ico_deadeye', ico_deadeye, 'DEADEYE 6 (Archer)', ['i_tod_card2_art_deadeye', 'i_tod_pm_ico_grapple']),
    ('i_tod_pm_ico_quickdraw', ico_quickdraw, 'QUICK DRAW 35 (Archer)', ['i_tod_card2_art_quick_draw', 'i_tod_pm_ico_retriever']),
    ('i_tod_pm_ico_piercing', ico_piercing, 'PIERCING 26 (Archer)', ['i_tod_card2_art_piercing', 'i_tod_pm_ico_grapple']),
    ('i_tod_pm_ico_adrenaline', ico_adrenaline, 'ADRENALINE 25 (Breacher)', ['i_tod_card2_art_adrenaline', 'i_tod_pm_ico_c4']),
    ('i_tod_pm_ico_fusion', ico_fusion, 'EXPLOSIVE FUSION 36 (Breacher)', ['i_tod_card2_art_explosive_fusion', 'i_tod_pm_ico_cluster']),
    ('i_tod_pm_ico_vitality', ico_vitality, 'VITALITY 37 (Warrior)', ['i_tod_card2_art_vitality', 'i_tod_pm_ico_bash']),
    ('i_tod_pm_ico_armsspecialist', ico_armsspecialist, 'ARMS SPECIALIST 7 (Warrior)', ['i_tod_card2_art_arms_specialist', 'i_tod_pm_ico_bash']),
    ('i_tod_pm_ico_cleave', ico_cleave, 'CLEAVE 48 (Warrior)', ['i_tod_card2_art_cleave', 'i_tod_pm_ico_gravsmash']),
    ('i_tod_pm_ico_demonslayer', ico_demonslayer, 'DEMON SLAYER 12 (Warrior)', ['i_tod_card2_art_demon_slayer', 'i_tod_pm_ico_bounty']),
    ('i_tod_pm_ico_reapersreach', ico_reapersreach, "REAPER'S REACH 5 (Necromancer)", ['i_tod_card2_art_reapers_reach', 'i_tod_pm_ico_soulbeam']),
    ('i_tod_pm_ico_summonermaster', ico_summonermaster, 'SUMMONER MASTER 19 (Necromancer)', ['i_tod_card2_art_summoner_master', 'i_tod_pm_ico_summonpower']),
    ('i_tod_pm_ico_cloak', ico_cloak, 'INVISIBILITY CLOAK 9 (Necromancer)', ['i_tod_card2_art_cloak', 'i_tod_pm_ico_summonpower']),
    ('i_tod_pm_ico_companion', ico_companion, 'AI COMPANION empty well', ['i_tod_pm_ico_generic', 'i_tod_pm_ico_c4']),
    ('i_tod_pm_ico_soulbomb', ico_soul_pulse, 'SOUL PULSE 59 (redraw; ref 2 = the old bomb)', ['i_tod_card2_art_soul_pulse', 'i_tod_pm_ico_soulbomb']),
]
# (W3B 2026-10-05: the HUD tile twins i_tod_h2_ab_cloak / _soul_bomb are tools/artgen/packs/w3b_ability_colour.py's,
# coloured from ico_cloak / ico_soul_pulse above; the V1 key i_tod_hud_off_cloak and its v1_* renderer are retired.)
NAMES = [n for n, _, _, _ in ICONS]


def _raster(body, defs=''):
    """The SVG at SS x, box-averaged to 128: float premultiplied RGBA in 0..1."""
    big = artgen.render_svg(artgen.svg_doc(S, S, body, defs), S * SS, S * SS, ss=1)
    a = np.asarray(big, dtype=np.float64) / 255.0
    rgb, al = a[..., :3], a[..., 3:4]
    pre = np.concatenate([rgb * al, al], axis=-1)
    return pre.reshape(S, SS, S, SS, 4).mean(axis=(1, 3))


def fit(body, box=FIT_BOX):
    """Scale + centre the drawing so its core's longest side is `box` px, centred on (64, 64).
    Measured at half scale (the 128 canvas then covers -64..192) so a drawing authored past the
    canvas edge is measured whole, not clipped."""
    core = _raster(group(body, 'translate(32,32) scale(0.5)'))[..., 0] > 0.25
    ys, xs = np.where(core)
    x0, x1, y0, y1 = ((v - 32) * 2.0 for v in (xs.min(), xs.max() + 1, ys.min(), ys.max() + 1))
    s = box / float(max(x1 - x0, y1 - y0))
    return group(body, 'translate(64,64) scale(%.5f) translate(%.3f,%.3f)' % (s, -(x0 + x1) / 2.0, -(y0 + y1) / 2.0))


def _gauss1d(sigma):
    r = int(math.ceil(sigma * 3.5))
    x = np.arange(-r, r + 1, dtype=np.float64)
    k = np.exp(-(x * x) / (2.0 * sigma * sigma))
    return k / k.sum(), r


def _blur(a, sigma):
    k, r = _gauss1d(sigma)
    p = np.pad(a, r, mode='constant')
    t = np.zeros_like(p)
    for i, w in enumerate(k):
        t[:, r:-r] += w * p[:, i:i + p.shape[1] - 2 * r]
    out = np.zeros_like(p)
    for i, w in enumerate(k):
        out[r:-r, :] += w * t[i:i + p.shape[0] - 2 * r, :]
    return out[r:-r, r:-r]


def white_glyph(body):
    """Core alpha = the luminance of the drawing (white positive, black cuts); the glow under it."""
    core = np.clip(_raster(body)[..., 0], 0.0, 1.0)     # premultiplied red = white coverage
    glow = np.clip(_blur(core, GLOW_SIGMA) * GLOW_GAIN, 0.0, 1.0)
    alpha = core + glow * (1.0 - core)
    a8 = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    out = np.zeros((S, S, 4), np.uint8)
    out[..., :3] = np.where(a8[..., None] > 0, 255, 0).astype(np.uint8)
    out[..., 3] = a8
    return Image.fromarray(out, 'RGBA')


def build_all():
    out, cache = {}, {}
    for name, fn, _, _ in ICONS:
        if fn not in cache:
            cache[fn] = white_glyph(fit(fn()))
        out[name] = cache[fn]
    return out

# ===================================================================================== review

def _tint(im, rgb, alpha=1.0):
    a = np.asarray(im.convert('RGBA')).astype(np.float64)
    for i in range(3):
        a[..., i] *= rgb[i]
    a[..., 3] *= alpha
    return Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8), 'RGBA')


def _paste(bg, im, x, y, w, h, alpha=1.0):
    """Composite `im` into the box (x, y, w, h) of `bg` - float box, LANCZOS-resized (the engine
    samples the 128 icon down with no mips: noMipMaps 1)."""
    t = im.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
    if alpha < 1.0:
        t = _tint(t, (1, 1, 1), alpha)
    bg.alpha_composite(t, (int(round(x)), int(round(y))))


# The lists a player actually reads: each class's rows in the order the server deals them -
# AI COMPANION first, the class's six cards, the three shared cards, the CLASS TIER row.
# (name, icon, tint key) - icon None = a shipped icon picked by name.
CLASS_ROWS = {
    'ARCHER': [('GRAPPLE', 'i_tod_pm_ico_grapple'), ("HELL'S RETRIEVER", 'i_tod_pm_ico_retriever'),
               ('DEADEYE', 'i_tod_pm_ico_deadeye'), ('SPRINT', 'i_tod_pm_ico_sprint'),
               ('QUICK DRAW', 'i_tod_pm_ico_quickdraw'), ('PIERCING', 'i_tod_pm_ico_piercing')],
    'BREACHER': [('BUCKSHOT', 'i_tod_pm_ico_pellets'), ('STICKY C4', 'i_tod_pm_ico_c4'),
                 ('CLUSTER', 'i_tod_pm_ico_cluster'), ('ADRENALINE', 'i_tod_pm_ico_adrenaline'),
                 ('EXPLOSIVE FUSION', 'i_tod_pm_ico_fusion'), ('RIOT SHIELD', 'i_tod_pm_ico_riotshield')],
    'WARRIOR': [('BASH', 'i_tod_pm_ico_bash'), ('CYBER SMASH', 'i_tod_pm_ico_gravsmash'),
                ('ARMS SPECIALIST', 'i_tod_pm_ico_armsspecialist'), ('VITALITY', 'i_tod_pm_ico_vitality'),
                ('CLEAVE', 'i_tod_pm_ico_cleave'), ('DEMON SLAYER', 'i_tod_pm_ico_demonslayer')],
    'NECROMANCER': [('SOUL PULSE', 'i_tod_pm_ico_soulbomb'), ('SUMMONING POWER', 'i_tod_pm_ico_summonpower'),
                    ('SOUL SUCK', 'i_tod_pm_ico_soulbeam'), ("REAPER'S REACH", 'i_tod_pm_ico_reapersreach'),
                    ('SUMMONER MASTER', 'i_tod_pm_ico_summonermaster'), ('INVISIBILITY CLOAK', 'i_tod_pm_ico_cloak')],
}
SHARED_ROWS = [('DMG REDUCTION', 'i_tod_pm_ico_dr'), ('LUCK', 'i_tod_pm_ico_luck'),
               ('BOUNTY', 'i_tod_pm_ico_bounty'), ('CLASS TIER', 'i_tod_pm_ico_tier')]
PM_RED, PM_IDLE = (0.95, 0.13, 0.23), (0.59, 0.64, 0.78)     # LOCKSTEP AetheriumStartMenu.lua PM_RED / PM_IDLE
K1080 = 1.5                                                    # the 1280 canvas -> 1080p


def _icon(imgs, name):
    return imgs[name] if name in imgs else Image.open(artgen.shipped(name)).convert('RGBA')


def _rows_for(cls):
    return [('AI COMPANION', 'i_tod_pm_ico_companion', True)] + \
           [(n, i, False) for n, i in CLASS_ROWS[cls] + SHARED_ROWS]


def context_sheet(imgs, out_path):
    """The icons where the player reads them, at their REAL 1080p pixel size, beside the shipped
    icons they share a list with:
      top    - the pause menu V2 rows (AetheriumStartMenu.lua: ROW_H 67, the well centre at art
               (96, 100) of 1024x200, the glyph 40 x 67/63 canvas units square = 64 px), one column per class;
      middle - the scoreboard V2 rows (AetheriumScoreboard.lua: ROW_H 43 of 1024x112, the well at
               (56, 56), the glyph 24 x 43/38 = 41 px);
      bottom - the Necromancer's two HUD V2 ability tiles (AetheriumLoadout.lua: a 46 x 32 tile, the
               glyph 24 units = 36 px at +5, +4) in each state: ready (the red tile), cooling, locked."""
    row_art = Image.open(artgen.shipped('i_tod_pm_row')).convert('RGBA')
    sb_art = Image.open(artgen.shipped('i_tod_sb_row')).convert('RGBA')
    tile, tile_ready = (Image.open(artgen.shipped(n)).convert('RGBA') for n in ('i_tod_h2_tile', 'i_tod_h2_tile_ready'))
    f_name = artgen.ttf(22)
    f_sb = artgen.ttf(17)
    f_head = artgen.ttf(20)
    pad, colgap = 24, 28
    # pause rows: 67 canvas tall = 100.5 px; draw the left 300 px of the 514-px row
    p_h = 67 * K1080
    p_w = 67 * 1024 / 200.0 * K1080
    p_crop = 300
    p_pitch = 83 * K1080 * 0.82                              # a little tighter than the menu's 83 pitch, same row size
    p_glyph = 40 * 67 / 63.0 * K1080
    # scoreboard rows: 43 canvas tall = 64.5 px
    s_h = 43 * K1080
    s_w = 43 * 1024 / 112.0 * K1080
    s_crop = 260
    s_glyph = 24 * 43 / 38.0 * K1080
    classes = list(CLASS_ROWS)
    n_rows = len(_rows_for(classes[0]))
    colw = max(p_crop, s_crop)
    Wd = pad * 2 + len(classes) * colw + (len(classes) - 1) * colgap
    hud_h = 120
    Hd = int(pad + 40 + n_rows * p_pitch + 50 + 40 + n_rows * (s_h + 6) + 50 + hud_h)
    sheet = Image.new('RGBA', (int(Wd), Hd), (8, 9, 13, 255))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 8), 'PK05 IN CONTEXT - 1:1 PIXELS AT 1080P. PAUSE MENU ROWS (GLYPH 64 PX)', fill=(235, 235, 240, 255), font=f_head)
    y0 = pad + 32
    for ci, cls in enumerate(classes):
        x = pad + ci * (colw + colgap)
        d.text((x, y0 - 2), cls, fill=(255, 210, 90, 255), font=f_head)
        for ri, (nm, icon, partner) in enumerate(_rows_for(cls)):
            y = y0 + 26 + ri * p_pitch
            row = row_art.resize((int(round(p_w)), int(round(p_h))), Image.LANCZOS).crop((0, 0, p_crop, int(round(p_h))))
            if partner:
                row = _tint(row, (1, 1, 1), 0.6)
            sheet.alpha_composite(row, (int(x), int(y)))
            cx, cy = x + 96 * p_h / 200.0, y + 100 * p_h / 200.0
            _paste(sheet, _tint(_icon(imgs, icon), PM_IDLE if partner else PM_RED), cx - p_glyph / 2, cy - p_glyph / 2, p_glyph, p_glyph)
            new = icon in imgs
            d.text((x + 70 * 67 / 63.0 * K1080, y + 12), nm, fill=(255, 255, 255, 255) if new else (165, 170, 185, 255), font=f_name)
    y1 = int(y0 + 26 + n_rows * p_pitch + 24)
    d.text((pad, y1), 'SCOREBOARD ROWS (GLYPH 41 PX). WHITE NAME = A PK05 ICON, GREY = ALREADY SHIPPED', fill=(235, 235, 240, 255), font=f_head)
    for ci, cls in enumerate(classes):
        x = pad + ci * (colw + colgap)
        for ri, (nm, icon, partner) in enumerate(_rows_for(cls)):
            y = y1 + 34 + ri * (s_h + 6)
            row = sb_art.resize((int(round(s_w)), int(round(s_h))), Image.LANCZOS).crop((0, 0, s_crop, int(round(s_h))))
            if partner:
                row = _tint(row, (1, 1, 1), 0.6)
            sheet.alpha_composite(row, (int(x), int(y)))
            cx, cy = x + 56 * s_h / 112.0, y + 56 * s_h / 112.0
            _paste(sheet, _tint(_icon(imgs, icon), PM_IDLE if partner else PM_RED), cx - s_glyph / 2, cy - s_glyph / 2, s_glyph, s_glyph)
            new = icon in imgs
            d.text((x + s_h + 4, y + 20), nm, fill=(255, 255, 255, 255) if new else (165, 170, 185, 255), font=f_sb)
    y2 = int(y1 + 34 + n_rows * (s_h + 6) + 24)
    d.text((pad, y2), 'NECROMANCER HUD V2 ABILITY TILES (GLYPH 36 PX): READY / COOLING / LOCKED', fill=(235, 235, 240, 255), font=f_head)
    tw, th, g = 46 * K1080, 32 * K1080, 24 * K1080
    x = pad
    for name, label in (('i_tod_h2_ab_cloak', 'CLOAK (TACTICAL)'), ('i_tod_h2_ab_soul_bomb', 'SOUL PULSE (LETHAL)')):
        d.text((x, y2 + 34), label, fill=(200, 205, 215, 255), font=f_sb)
        for si, (t_img, t_a, i_a) in enumerate(((tile_ready, 1.0, 1.0), (tile, 0.4, 0.35), (tile, 0.4, 0.2))):
            tx, ty = x + si * (tw + 18), y2 + 64
            _paste(sheet, t_img, tx, ty, tw, th, t_a)
            _paste(sheet, _icon(imgs, name), tx + 5 * K1080, ty + 4 * K1080, g, g, i_a)   # the shipped (W3B colour) tile
        x += 3 * (tw + 18) + 60
    # the same tiles, shipped neighbours for comparison (Warrior bash / smash)
    d.text((x, y2 + 34), 'SHIPPED: BASH / SMASH / C4 (READY)', fill=(165, 170, 185, 255), font=f_sb)
    for si, name in enumerate(('i_tod_h2_ab_bash', 'i_tod_h2_ab_smash', 'i_tod_h2_ab_c4')):
        tx, ty = x + si * (tw + 18), y2 + 64
        _paste(sheet, tile_ready, tx, ty, tw, th)
        _paste(sheet, Image.open(artgen.shipped(name)).convert('RGBA'), tx + 5 * K1080, ty + 4 * K1080, g, g)
    sheet.save(out_path)


def zoom_sheet(imgs, out_path):
    """Every new white glyph at 128 / 64 / 41 / 36 px on the HUD navy, the tinted sizes red as the rows
    tint them, then shown x2 so a reviewer can see the pixels."""
    names = [n for n, _, _, _ in ICONS]
    cell = 128 + 64 + 41 + 36 + 4 * 10 + 10
    sheet = Image.new('RGBA', (cell * 3 + 20, ((len(names) + 2) // 3) * 150 + 10), (0, 0, 0, 255))
    for i, n in enumerate(names):
        x0, y0 = 10 + (i % 3) * cell, 10 + (i // 3) * 150
        x = x0
        for sz in (128, 64, 41, 36):
            bg = Image.new('RGBA', (sz, sz), (20, 24, 34, 255))
            im = _tint(imgs[n], PM_RED) if sz in (64, 41) else imgs[n]
            bg.alpha_composite(im.resize((sz, sz), Image.LANCZOS))
            sheet.paste(bg, (x, y0))
            x += sz + 10
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(out_path)


def review_sheet(imgs, out_path):
    rows = []
    for name, _, note, refs in ICONS:
        items = [imgs[name]] + [artgen.shipped(r) for r in refs if os.path.exists(artgen.shipped(r))]
        rows.append(('%s - %s' % (name.replace('i_tod_', ''), note), items))
    # each row: the new glyph, its card illustration, then the shipped glyph(s) it must sit beside
    artgen.contact_sheet(rows, out_path, height=160)

# ===================================================================================== measure

def glow_profile(im):
    from scipy import ndimage
    al = np.asarray(im.convert('RGBA')).astype(np.float64)[..., 3]
    dist = ndimage.distance_transform_edt(~(al >= 250))
    return [round(float(al[(dist > r - 0.5) & (dist <= r + 0.5)].mean()), 1) for r in (2, 4, 6, 8, 10)]


def stats(im):
    al = np.asarray(im.convert('RGBA'))[..., 3]
    ys, xs = np.where(al >= 250)
    return 'core%%=%4.1f ink%%=%4.1f core box x %3d..%3d y %3d..%3d edge alpha max %3d' % (
        (al >= 250).mean() * 100, (al > 8).mean() * 100, xs.min(), xs.max(), ys.min(), ys.max(),
        max(al[0].max(), al[-1].max(), al[:, 0].max(), al[:, -1].max()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--measure', action='store_true')
    ap.add_argument('--out-root', default=artgen.ROOT, help='root that holds source_data/ (default: the repo)')
    a = ap.parse_args()
    imgs = build_all()
    dest = os.path.join(a.out_root, 'source_data', 'tod_ui_images', '_images')
    if a.check:
        bad = 0
        for n in NAMES:
            p = os.path.join(dest, n + '.png')
            want = artgen.png_bytes(imgs[n])
            have = open(p, 'rb').read() if os.path.exists(p) else None
            if have != want:
                print('PK05 GLYPHS STALE: %s %s' % (n, 'missing' if have is None else 'differs from a fresh render'))
                bad += 1
        if bad:
            print('PK05 GLYPHS --check FAILED: %d of %d (re-run tools/artgen/packs/pk05_glyph_icons.py --install)' % (bad, len(NAMES)))
            return 1
        print('PK05 GLYPHS OK %d' % len(NAMES))
        return 0
    if a.measure:
        for r in ('i_tod_pm_ico_grapple', 'i_tod_pm_ico_c4', 'i_tod_pm_ico_bounty', 'i_tod_pm_ico_summonpower'):
            im = Image.open(artgen.shipped(r))
            print('ref %-28s glow %-34s %s' % (r, glow_profile(im), stats(im)))
        for n in NAMES:
            print('new %-28s glow %-34s %s' % (n, glow_profile(imgs[n]), stats(imgs[n])))
        return 0
    stage = artgen.stage_dir(PACK)
    for n in NAMES:
        artgen.save_png(imgs[n], os.path.join(stage, n + '.png'))
    review_sheet(imgs, os.path.join(stage, '_review.png'))
    context_sheet(imgs, os.path.join(stage, '_context.png'))
    zoom_sheet(imgs, os.path.join(stage, '_zoom.png'))
    print('PK05 GLYPHS wrote %d -> %s (+ _review.png, _context.png, _zoom.png)' % (len(NAMES), stage))
    if a.install:
        os.makedirs(dest, exist_ok=True)
        for n in NAMES:
            artgen.save_png(imgs[n], os.path.join(dest, n + '.png'))
        print('PK05 GLYPHS installed %d -> %s' % (len(NAMES), dest))
    return 0


if __name__ == '__main__':
    sys.exit(main())
