"""pk07_prompt_icons.py - prompt-card icons for the BLACK MARKET and the BATTLE ARENA (2026-10-04).

WHY. Every interaction prompt in the map draws one 256x256 icon in the card's well, picked by
CoD.TodPromptCard.IconFor() from the ICONS table in TodPromptCard.lua (first match on the whole
lowercased hint line wins). The Black Market (the spin, THE DEALER'S GIFT - the first Black Market
use of every run - and the House's last roll) and the floor-40 Battle Arena chamber had no row, so
they fell back to i_tod_prompt_icon_generic: a pointing hand. Every other object in the map has its
own icon. This generator draws the two missing ones in the shipped set's own style.

THE STYLE IS MEASURED, NOT EYEBALLED (the shipped docs/183 set: rampage / alarm / crate / power /
crown / teleporter / pap / generic):
  * solid glyph ink is pure white (255,255,255); the one accent is (242,32,58);
  * cut-outs are TRANSPARENT (the grey you see inside the skull's eye sockets is the glow over the
    dark well, not a fill);
  * the glow is one Gaussian of the solid coverage, sigma 9 px, strength 0.65, clamped - fitted by
    least squares over eight shipped icons (RMSE 0.0095 in alpha, i.e. ~2.4/255); white parts glow
    white, red parts glow red;
  * the glyph's solid box spans ~72-87% of the canvas, centred.

THE TWO GLYPHS
  i_tod_prompt_icon_black_market  THE DEALER (docs/dealer_identity.md): a deep hood around his long
                                  angular faceted mask, red X eyes (one stroke a touch weaker, as
                                  on the shop model) and an uneven red stitched grin.
  i_tod_prompt_icon_arena         THE BATTLE ARENA: two crossed blades standing in the arena ring;
                                  the ring is a perspective ellipse (the set's floor grammar, as on
                                  the teleporter and extract icons) and the MAGENTA accent (R4: the arena's
                                  lit pit edge, the arena badge's red edge light). The blades cut
                                  dark gaps in the ring's far side only, so they stand INSIDE it.
                                  No gate notches: at 44-66 px a notch in a 16 px band is 2 px of
                                  noise (reviewed 2026-10-04).

  i_tod_prompt_icon_terminal      GATED (TOD_TESTER_KIT 0 in _tod_tester.gsh): a console with swap
                                  arrows for the crown's CLASS TERMINAL. Drawn ONLY with --terminal,
                                  never by default, never installed or checked by default.

USAGE
  python tools/artgen/packs/pk07_prompt_icons.py              # art/generated/PK07-prompt-icons-new/ + _review.png
  python tools/artgen/packs/pk07_prompt_icons.py --stage DIR  # also write the PNGs under DIR/source_data/tod_ui_images/_images/
  python tools/artgen/packs/pk07_prompt_icons.py --install    # copy into source_data/tod_ui_images/_images/ (the landing)
  python tools/artgen/packs/pk07_prompt_icons.py --check [--root DIR]
                                                              # regenerate in memory, fail on any byte that differs
                                                              # from the installed files (or those under DIR), AND on
                                                              # broken wiring: no GDT block / zone line / ICONS row, the
                                                              # arena row above "power required", or a row whose phrase
                                                              # no live hint carries any more (a renamed hint would
                                                              # silently fall back to the hand). The build gate.
  --terminal  also draw the gated class-terminal icon (to art/generated/<pack>/gated/, plus --stage / --install if given)

Deterministic: no randomness, no timestamps; resvg + numpy + scipy only. Never hand-edit the PNGs.
"""
import argparse, os, sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402
from synthwave import THEME  # noqa: E402  (the UI theme switch: the arena icon's accent follows it)

PACK = 'PK07-prompt-icons-new'
W = H = 256
SS = 4                                   # supersample for the solid shapes

WHITE = (255, 255, 255)
RED = (242, 32, 58)                      # the shipped accent, measured
RED_GLOW = (250, 48, 72)                 # red parts glow a hair lighter than their fill (fitted 255/40..90/65..109)
# R4 (2026-10-04, tools/artgen/packs/r4_synthwave_hud.py): the synthwave accent - no red in the Map 2 UI art
# (tmp/redesign/R3-synthwave-system/STYLE.md). The arena icon wears it; the DEALER keeps his red X eyes and
# grin, his identity (docs/dealer_identity.md), as his Black Market portraits do.
MAGENTA = (255, 43, 209)
MAGENTA_GLOW = (255, 64, 214)
# RT (2026-10-05, the red return - user: "id rather the red theme please"): the arena accent is the THEME's - the Fallen
# red (the docs/183 set's own accent, measured above) or the synthwave magenta. The Dealer's X eyes stay RED in both.
ARENA_ACCENT, ARENA_GLOW = (MAGENTA, MAGENTA_GLOW) if THEME == 'synthwave' else (RED, RED_GLOW)
GLOW_SIGMA = 9.0                         # fitted, see the module docstring
GLOW_K = 0.65

IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')

# ----------------------------------------------------------------------------------------- compositor

def coverage(svg_body, defs=''):
    """Render a WHITE-filled svg body and return its coverage (float 0..1) at W x H."""
    im = artgen.render_svg(artgen.svg_doc(W, H, svg_body, defs), W, H, ss=SS)
    return np.clip(np.asarray(im, dtype=np.float64)[..., 3] / 255.0, 0.0, 1.0)


def compose(white_cov, red_cov, accent=RED, accent_glow=RED_GLOW):
    """The shipped look: red over white solid ink, over one Gaussian glow of the visible ink."""
    cR = red_cov
    cW = white_cov * (1.0 - cR)                     # white visible where red does not cover it
    S = np.clip(cR + cW, 0.0, 1.0)                  # solid coverage
    gW = ndimage.gaussian_filter(cW, GLOW_SIGMA, mode='constant')
    gR = ndimage.gaussian_filter(cR, GLOW_SIGMA, mode='constant')
    gsum = gW + gR
    gA = np.clip(GLOW_K * gsum, 0.0, 1.0)
    with np.errstate(invalid='ignore', divide='ignore'):
        wR = np.where(gsum > 1e-9, gR / gsum, 0.0)
    glow_rgb = np.stack([(1 - wR) * WHITE[c] + wR * accent_glow[c] for c in range(3)], -1)
    with np.errstate(invalid='ignore', divide='ignore'):
        rS = np.where(S > 1e-9, cR / S, 0.0)
    solid_rgb = np.stack([(1 - rS) * WHITE[c] + rS * accent[c] for c in range(3)], -1)
    outA = S + gA * (1.0 - S)
    with np.errstate(invalid='ignore', divide='ignore'):
        rgb = np.where(outA[..., None] > 1e-9,
                       (solid_rgb * S[..., None] + glow_rgb * (gA * (1.0 - S))[..., None]) / outA[..., None],
                       0.0)
    out = np.dstack([rgb, outA * 255.0])
    out = np.clip(np.round(out), 0, 255).astype(np.uint8)
    out[out[..., 3] == 0] = 0                       # clean transparent pixels (deterministic, no stray RGB)
    return Image.fromarray(out, 'RGBA')

# ------------------------------------------------------------------------------------------- helpers

def pts(p):
    return ' '.join('%.2f,%.2f' % xy for xy in p)


def poly(p, extra=''):
    return '<polygon points="%s" fill="#fff" %s/>' % (pts(p), extra)


def line(x1, y1, x2, y2, w, cap='butt', color='#fff'):
    return ('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f" stroke-linecap="%s"/>'
            % (x1, y1, x2, y2, color, w, cap))


def rot(p, deg, cx=0.0, cy=0.0):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in p]


def knock(cov, *cutters):
    """Remove every cutter coverage from cov."""
    out = cov.copy()
    for c in cutters:
        out = out * (1.0 - c)
    return np.clip(out, 0.0, 1.0)

# ---------------------------------------------------------------------------------- THE BLACK MARKET

# The Dealer's hood: a ROUNDED cowl (the shop model and the shipped dealer portraits: a deep domed
# hood, never a peak - a white pointed hood is the one silhouette this must never read as), falling
# to the shoulders. Its face opening is the mask grown by GAP_HOOD all round (rendered as the mask
# stroked with round joins), so the dark shadow between hood and mask is one even width.
HOOD_OUTER = ('M 34 232 C 38 212 48 200 62 192 C 54 168 50 142 51 118 C 53 62 88 22 128 20 '
              'C 168 22 203 62 205 118 C 206 142 202 168 194 192 C 208 200 218 212 222 232 Z')
GAP_HOOD = 11.0

# The mask: long, angular, faceted - a flat brow, hard cheekbones, a long pointed chin.
MASK = [(128, 56), (166, 68), (178, 104), (176, 148), (158, 190), (128, 216), (98, 190), (80, 148), (78, 104), (90, 68)]


def black_market():
    opening = coverage('<polygon points="%s" fill="#fff" stroke="#fff" stroke-width="%.1f" stroke-linejoin="round"/>'
                       % (pts(MASK), GAP_HOOD * 2))
    # the hood's front drapes fall onto the shoulders: two thin dark folds part them from the cloak
    drapes = coverage('<path d="M 62 191 Q 84 204 94 236" fill="none" stroke="#fff" stroke-width="5"/>'
                      '<path d="M 194 191 Q 172 204 162 236" fill="none" stroke="#fff" stroke-width="5"/>')
    hood = knock(coverage('<path d="%s" fill="#fff"/>' % HOOD_OUTER), opening, drapes)
    mask = coverage(poly(MASK))
    # the faceted nose: a short bridge between the eyes ending in the nose's point, cut as a thin
    # dark line (transparent). NOT a full brow-to-chin line: that reads as the boss's CRACKED mask
    # (docs/199 state two), and the shop Dealer's mask is whole.
    facets = coverage(line(128, 100, 128, 126, 4.0) +
                      '<polygon points="128,122 120,140 136,140" fill="#fff"/>')
    mask = knock(mask, facets)
    # red X eyes, slanted down toward the nose (menace); the right eye's rising stroke is a touch weaker
    def x_eye(cx, cy, s, w1, w2, tilt):
        a = line(*sum(rot([(-s, -s), (s, s)], tilt, cx, cy), ()), w1)
        b = line(*sum(rot([(-s, s), (s, -s)], tilt, cx, cy), ()), w2)
        return a + b
    eyes = coverage(x_eye(108, 106, 13.0, 11.5, 11.5, 8) + x_eye(148, 106, 13.0, 11.5, 9.0, -8))
    # the stitched grin: an uneven, lopsided seam - lower on his right (our left), higher on his left -
    # with stitches crossing it
    seam = [(92, 150), (103, 160), (116, 166), (130, 168), (143, 163), (155, 155), (166, 143)]
    d = 'M ' + ' L '.join('%.1f %.1f' % p for p in seam)
    grin = '<path d="%s" fill="none" stroke="#fff" stroke-width="8.5" stroke-linejoin="round" stroke-linecap="round"/>' % d
    stitches = ''
    for i in (1, 2, 3, 4, 5):
        (x0, y0), (x1, y1) = seam[i - 1], seam[i + 1]
        px, py = seam[i]
        tx, ty = x1 - x0, y1 - y0
        n = (tx * tx + ty * ty) ** 0.5
        nx, ny = -ty / n, tx / n                      # the seam's normal
        L = 11.0 if i % 2 else 9.0                    # uneven stitches
        stitches += line(px - nx * L, py - ny * L, px + nx * L, py + ny * L, 5.5, 'round')
    red = np.clip(eyes + coverage(grin + stitches), 0.0, 1.0)
    white = np.clip(hood + mask, 0.0, 1.0)
    return compose(white, red)

# ---------------------------------------------------------------------------------- THE BATTLE ARENA

# Two crossed blades standing in the arena ring. The ring is a perspective ELLIPSE, the set's own
# grammar for "an object standing on a floor" (the teleporter's pad, the extraction ring), and it is
# the red accent: the arena pit's lit edge (the arena badge's red edge light). A full red CIRCLE round
# crossed blades was tried and dropped: at 66 px it reads as a "no weapons" sign.
SWORD_TILT = 38.0                                     # each blade leans this far off vertical
SWORD_CROSS = 70.0                                    # guard -> crossing distance along the blade
CROSS_Y = 98.0                                        # where the blades cross
RING = (128.0, 196.0, 98.0, 29.0, 16.0)              # the arena ring: cx, cy, rx, ry, band
GAP = 8.0                                             # the dark knock-out gap round a blade


def sword(cx, cy, deg):
    """A straight blade pointing UP before rotation, its crossguard at the origin, rotated `deg`
    about the origin and placed at (cx, cy). Returns (svg, [polygons]) - the polygons drive the
    knock-out gaps."""
    blade = [(0, -150), (12, -128), (12, -13), (-12, -13), (-12, -128)]
    guard = [(-38, -13), (38, -13), (31, 3), (-31, 3)]
    grip = [(-7, 3), (7, 3), (7, 34), (-7, 34)]
    pommel = [(0, 30), (12, 42), (0, 54), (-12, 42)]
    shapes = [rot(p, deg, cx, cy) for p in (blade, guard, grip, pommel)]
    return ''.join(poly(p) for p in shapes), shapes


def halo(shapes, g):
    """Coverage of `shapes` grown by g on every side (the dark gap one shape cuts in what is behind)."""
    return coverage(''.join('<polygon points="%s" fill="#fff" stroke="#fff" stroke-width="%.1f" stroke-linejoin="round"/>'
                            % (pts(p), 2 * g) for p in shapes))


def arena():
    t = np.radians(SWORD_TILT)
    gx, gy = SWORD_CROSS * np.sin(t), CROSS_Y + SWORD_CROSS * np.cos(t)
    sa_svg, sa = sword(128 - gx, gy, SWORD_TILT)      # hilt low-left, point high-right
    sb_svg, sb = sword(128 + gx, gy, -SWORD_TILT)     # its mirror, crossing OVER it
    A = knock(coverage(sa_svg), halo(sb, GAP))
    B = coverage(sb_svg)
    cx, cy, rx, ry, band = RING
    ring = coverage('<ellipse cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f" fill="none" stroke="#fff" stroke-width="%.2f"/>'
                    % (cx, cy, rx, ry, band))
    ring = knock(ring, halo(sa + sb, GAP))            # the blades stand in front of the ring's far side
    return compose(np.clip(A + B, 0.0, 1.0), ring, ARENA_ACCENT, ARENA_GLOW)

# ------------------------------------------------------------------------- THE CLASS TERMINAL (gated)

def terminal():
    # a console: a screen on a stand, two swap arrows on the screen (red), a keyboard deck below
    screen = coverage('<path d="M 44 40 H 212 Q 222 40 222 50 V 158 Q 222 168 212 168 H 44 Q 34 168 34 158 V 50 Q 34 40 44 40 Z '
                      'M 56 60 V 148 H 200 V 60 Z" fill="#fff" fill-rule="evenodd"/>')
    stand = coverage(poly([(112, 168), (144, 168), (150, 194), (106, 194)]) +
                     poly([(54, 194), (202, 194), (218, 228), (38, 228)]))
    keys = coverage(''.join('<rect x="%d" y="%d" width="16" height="8" fill="#fff"/>' % (62 + i * 24, 204) for i in range(6)) +
                    '<rect x="78" y="216" width="100" height="6" fill="#fff"/>')
    stand = knock(stand, keys)
    arrows = coverage(line(82, 92, 160, 92, 10) + poly([(156, 78), (178, 92), (156, 106)]) +
                      line(174, 120, 96, 120, 10) + poly([(100, 106), (78, 120), (100, 134)]))
    return compose(np.clip(screen + stand, 0, 1), arrows)

# ---------------------------------------------------------------------------------------- the set

def deliverables(with_terminal=False):
    out = [('i_tod_prompt_icon_black_market', black_market),
           ('i_tod_prompt_icon_arena', arena)]
    if with_terminal:
        out.append(('i_tod_prompt_icon_terminal', terminal))
    return out


def build(with_terminal=False):
    return [(name, fn()) for name, fn in deliverables(with_terminal)]

# ---------------------------------------------------------------------------------------- review

CHASSIS = artgen.shipped('i_tod_prompt_chassis')
INK_GOLD = (228, 225, 108)


def card(icon, title, d1, d2, verb, price=None, chassis=CHASSIS):
    """The prompt card at chassis scale (924 x 304, 4 px per canvas unit), laid out like
    TodPromptCard.lua BOX: icon 60..236 x 68..244, title 304..904 x 17..63 (cap 0.8 h), detail
    lines centred in the body band, the footer and price on the footer band."""
    c = Image.open(chassis).convert('RGBA')
    c.alpha_composite(icon.resize((176, 176), Image.LANCZOS), (60, 68))
    U = 4.0
    titleT, titleB = (448.3 - 444) * U, (459.7 - 444) * U
    cap = (titleB - titleT) * 0.8
    artgen.typeset(c, title, cap, titleB - (titleB - titleT - cap) / 2, x=(620 - 544) * U, fit_width=(770 - 620) * U)
    bodyT, bodyB, descH, pitch = (462.1 - 444) * U, (500.6 - 444) * U, 8.4 * U, 12.05 * U
    block = (pitch + descH) if d2 else descH
    t = bodyT + (bodyB - bodyT - block) / 2
    for i, d in enumerate([d1, d2] if d2 else [d1]):
        top = t + i * pitch
        artgen.typeset(c, d, descH * 0.8, top + descH * 0.9, x=(620 - 544) * U, fit_width=(767 - 620) * U)
    footT, footB = (503.8 - 444) * U, (513.2 - 444) * U
    fr = (723 if price else 771) - 544
    if verb:                                          # no key in the hint = no footer (a status line)
        artgen.typeset(c, verb, (footB - footT) * 0.8, footB - (footB - footT) * 0.1, x=(620 - 544) * U, fit_width=(fr - 76) * U)
    if price:
        pT, pB = (502.86 - 444) * U, (513.26 - 444) * U
        pc = (pB - pT) * 0.8
        w = artgen.text_width(price, pc)
        artgen.typeset(c, price, pc, pB - (pB - pT) * 0.1, rgb=INK_GOLD, x=(771 - 544) * U - w)
    return c


def true_size_strip(cards, scale, h=256, bg=(28, 30, 38, 255)):
    """The cards at a real on-screen size (1080p: 1.5 px per canvas unit = 346 x 114) on one strip."""
    out = Image.new('RGBA', (16 + sum(int(924 * scale / 4) + 16 for _ in cards), h), bg)
    x = 16
    for cimg in cards:
        w, hh = int(round(924 * scale / 4)), int(round(304 * scale / 4))
        out.alpha_composite(cimg.resize((w, hh), Image.LANCZOS), (x, (h - hh) // 2))
        x += w + 16
    return out


def icon_strip(icons, size, h=256, bg=(10, 11, 14, 255)):
    """Icons at true on-screen size inside a dark well colour, the whole family side by side."""
    out = Image.new('RGBA', (16 + len(icons) * (size + 24), h), (28, 30, 38, 255))
    x = 16
    for im in icons:
        well = Image.new('RGBA', (size + 16, size + 16), bg)
        well.alpha_composite(im.resize((size, size), Image.LANCZOS), (8, 8))
        out.alpha_composite(well, (x, (h - size - 16) // 2))
        x += size + 24
    return out


def review(built, out_dir):
    def ref(name):
        # W2E (2026-10-05): the crown / extract icons retired with the Map One ending; the review still shows them
        # as the family reference, read from the archive (the --check path never calls review).
        p = artgen.shipped(name)
        if not os.path.isfile(p):
            p = os.path.join(artgen.ROOT, 'archive', 'map1_carryover', os.path.relpath(p, artgen.ROOT))
        return p
    bm = dict(built)['i_tod_prompt_icon_black_market']
    ar = dict(built)['i_tod_prompt_icon_arena']
    power = Image.open(ref('i_tod_prompt_icon_power')).convert('RGBA')
    # the live hints, parsed the way PromptDefault.lua parses them (title - d1 / d2, [Cost: N] -> price)
    cards = [
        card(bm, 'BLACK MARKET', 'A FREE AI COMPANION', 'NO POINTS OR LUCK - ON THE HOUSE', 'HOLD F TO TAKE'),
        card(bm, 'BLACK MARKET', 'SPIN FOR A COMPANION ITEM', 'YOUR LUCK SETS THE ODDS', 'HOLD F TO BUY', '$2500'),
        card(ar, 'BATTLE ARENA', 'ENTER THE ARENA - FREE', None, 'HOLD F TO USE'),
        card(power, 'BATTLE ARENA', 'POWER REQUIRED', None, None, chassis=ref('i_tod_prompt_chassis_locked')),
    ]
    family = [ref('i_tod_prompt_icon_%s' % n) for n in ('rampage', 'alarm', 'crate', 'crown', 'teleporter', 'power', 'generic')]
    fam_ims = [Image.open(p).convert('RGBA') for p in family]
    rows = [
        ('NEW  i_tod_prompt_icon_black_market  |  style refs: rampage, alarm, crate  |  likeness ref: i_tod_spin_ico_cursed, i_tod_spin_dealer_idle',
         [bm, ref('i_tod_prompt_icon_rampage'), ref('i_tod_prompt_icon_alarm'), ref('i_tod_prompt_icon_crate'),
          ref('i_tod_spin_ico_cursed'), ref('i_tod_spin_dealer_idle')]),
        ('NEW  i_tod_prompt_icon_arena  |  style refs: teleporter, extract (the ellipse floor), crown  |  subject ref: i_tod_h2_arena_badge',
         [ar, ref('i_tod_prompt_icon_teleporter'), ref('i_tod_prompt_icon_extract'), ref('i_tod_prompt_icon_crown'),
          ref('i_tod_h2_arena_badge')]),
    ]
    for name, im in built:
        if name.endswith('_terminal'):
            rows.append(('GATED, NOT STAGED: i_tod_prompt_icon_terminal (TOD_TESTER_KIT)', [im, ref('i_tod_prompt_icon_generic')]))
    rows += [
        ('IN THE CARD (chassis scale): gift / spin / arena ready / arena unpowered keeps the POWER icon', [cards[0], cards[1]]),
        ('', [cards[2], cards[3]]),
        ('TRUE SIZE, 1080p (346 x 114 card, 66 px icon)', [true_size_strip(cards, 1.5)]),
        ('THE FAMILY AT 66 PX (1080p), in a dark well: NEW black market, NEW arena, then the shipped set',
         [icon_strip([bm, ar] + fam_ims, 66, h=120)]),
        ('THE FAMILY AT 44 PX (720p)', [icon_strip([bm, ar] + fam_ims, 44, h=80)]),
    ]
    # contact_sheet scales each row to one height; give each row its own sheet and stack them
    sheets = []
    for label, items in rows:
        hgt = items[0].height if isinstance(items[0], Image.Image) and label.startswith(('TRUE', 'THE FAMILY')) else 256
        p = os.path.join(out_dir, '_row.png')
        artgen.contact_sheet([(label, items)], p, height=hgt)
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
    for i, cimg in enumerate(cards):
        cimg.save(os.path.join(out_dir, '_card_%d.png' % i))
    return p

# ----------------------------------------------------------------------------------------- wiring

LUA_REL = os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'ZM_CursorHint', 'Prompts', 'TodPromptCard.lua')
GDT_REL = os.path.join('source_data', 'tod_ui_images.gdt')
ZONE_REL = os.path.join('zone_source', 'zm_tod2_cybercity.zone')
SCRIPTS = os.path.join('scripts', 'zm', 'zm_tod2_cybercity')

# Each live icon: its ICONS phrase and the scripts whose hints must still carry that phrase.
ROWS = {
    'i_tod_prompt_icon_black_market': ('black market', ['_tod_shop.gsc', '_tod_house.gsc']),
    'i_tod_prompt_icon_arena':        ('battle arena', ['_tod_arena.gsc']),
}
POWER_ROW = 'power required'      # the arena row must sit BELOW it (first match wins): unpowered = power icon


def _read(root, rel):
    """Read rel under root, or under the repo when root does not carry it (a stage holds only what it changes)."""
    for base in ([root] if root else []) + [artgen.ROOT]:
        p = os.path.join(base, rel)
        if os.path.isfile(p):
            return open(p, encoding='utf-8', errors='replace').read()
    raise SystemExit('PK07 PROMPT ICONS: cannot read %s' % rel)


def wiring_problems(root=None):
    import re
    out = []
    gdt, zone, lua = _read(root, GDT_REL), _read(root, ZONE_REL), _read(root, LUA_REL)
    lua_code = re.sub(r'--[^\n]*', '', lua)
    icons = re.search(r'CoD\.TodPromptCard\.ICONS\s*=\s*\{(.*?)\n\}', lua_code, re.S)
    rows = re.findall(r'\{\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\}', icons.group(1)) if icons else []
    if not rows:
        out.append('TodPromptCard.lua: no CoD.TodPromptCard.ICONS table found')
    phrases = [p for p, _ in rows]
    for name, (phrase, scripts) in ROWS.items():
        m = re.search(r'"%s" \( "image\.gdf" \)\s*\{(.*?)\}' % re.escape(name), gdt, re.S)
        if not m:
            out.append('GDT: no image block for %s' % name)
        else:
            blk = m.group(1)
            if '"baseImage" "source_data/tod_ui_images/_images/%s.png"' % name not in blk:
                out.append('GDT: %s baseImage does not point at its PNG' % name)
            if '"compressionMethod" "compressed high color"' not in blk:
                out.append('GDT: %s is not "compressed high color" (its neighbours are)' % name)
        if not re.search(r'^image,%s\r?$' % re.escape(name), zone, re.M):
            out.append('zone: no image line for %s' % name)
        if (phrase, name) not in rows:
            out.append('TodPromptCard.lua ICONS: no { "%s", "%s" } row' % (phrase, name))
        # every live hint carrying the phrase must resolve to this icon through the SHIPPING first-match
        # walk (IconFor), except the unpowered arena, which keeps the power icon
        hints = []
        for s in scripts:
            for l in _read(root, os.path.join(SCRIPTS, s)).splitlines():
                if 'SetHintString' in l or '_HINT_' in l:
                    hints += [h.lower() for h in re.findall(r'"([^"]*)"', l.split('//')[0])]
        live = [h for h in hints if phrase in h]
        if not live:
            out.append('no live hint in %s carries "%s" any more - the row is dead (re-key it)' % ('/'.join(scripts), phrase))
        for h in live:
            got = next((img for p, img in rows if p in h), 'i_tod_prompt_icon_generic')
            want = 'i_tod_prompt_icon_power' if POWER_ROW in h else name
            if got != want:
                why = ('no row matches it: the generic hand' if got == 'i_tod_prompt_icon_generic'
                       else 'an earlier ICONS row claims it')
                out.append('hint "%s" draws %s, not %s (%s)' % (h[:70], got, want, why))
    if 'battle arena' in phrases and POWER_ROW in phrases and phrases.index('battle arena') < phrases.index(POWER_ROW):
        out.append('TodPromptCard.lua ICONS: "battle arena" sits ABOVE "%s" - the unpowered chamber loses the power icon' % POWER_ROW)
    return out

# ------------------------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--install', action='store_true', help='copy into source_data/tod_ui_images/_images/')
    ap.add_argument('--stage', help='also write the PNGs under DIR/source_data/tod_ui_images/_images/')
    ap.add_argument('--check', action='store_true', help='fail on any byte that differs from the installed files')
    ap.add_argument('--root', help='with --check: compare against DIR/source_data/... instead of the repo')
    ap.add_argument('--terminal', action='store_true', help='also draw the GATED class-terminal icon')
    a = ap.parse_args()

    built = build(a.terminal)
    if a.check:
        base = os.path.join(a.root, IMG_REL) if a.root else artgen.IMG
        bad = 0
        for name, im in built:
            p = os.path.join(base, name + '.png')
            want = artgen.png_bytes(im)
            if not os.path.isfile(p):
                print('PK07 PROMPT ICONS: MISSING %s' % p)
                bad += 1
            elif open(p, 'rb').read() != want:
                print('PK07 PROMPT ICONS: STALE %s (re-run the generator; never hand-edit it)' % p)
                bad += 1
        for msg in wiring_problems(a.root):
            print('PK07 PROMPT ICONS: %s' % msg)
            bad += 1
        if bad:
            sys.exit(1)
        print('PK07 PROMPT ICONS OK %d: bytes match the generator; GDT + zone + ICONS rows wired, live hints carry the phrases'
              % len(built))
        return

    out_dir = artgen.stage_dir(PACK)
    for name, im in built:
        # the GATED terminal goes to gated/ (the Art Atlas lists art/generated/<pack>/*.png only, so a
        # gated icon never shows as "in production")
        sub = os.path.join(out_dir, 'gated') if name.endswith('_terminal') else out_dir
        md5 = artgen.save_png(im, os.path.join(sub, name + '.png'))
        print('%-36s %s' % (name, md5))
        for root in ([a.stage] if a.stage else []) + ([artgen.ROOT] if a.install else []):
            artgen.save_png(im, os.path.join(root, IMG_REL, name + '.png'))
    print('review ->', review(built, out_dir))


if __name__ == '__main__':
    main()
