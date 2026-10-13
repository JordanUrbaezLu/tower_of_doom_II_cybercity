"""r4_synthwave_hud.py - THE REST OF THE MAP 2 CHROME in the R3 synthwave design system (2026-10-04).

R3 (tools/artgen/packs/r3_synthwave_system.py + tools/artgen/synthwave.py, the rules in
tmp/redesign/R3-synthwave-system/STYLE.md) redrew the pause menu, the scoreboard and the card-panel
chrome. R4 redraws everything else on the Map 2 HUD that still wore the red "Fallen" HUD V2 look or a
byte-identical Map 1 design (tmp/design_review/findings.md, tmp/asset_audit/map1_identity.json):

  HUD V2 chrome (docs/184c)  i_tod_h2_round_badge(+_rampage), the luck plate (+_rampage), luck segments,
                             gun plate, ability / PaP tiles, the health frame, medallion ring, perk
                             socket, points glyph, power-up toast, descent gauge rail + markers. The two
                             ARENA badges are cut from the new round badge by the shipped generator
                             tools/battle_arena/make_badge.py (imported, never copied), so its build gate
                             keeps passing unchanged.
  Prompt cards (docs/184d)   the three chassis (normal / wide / locked) redrawn; the 13 docs/183 icons keep
                             their glyphs and swap the red accent for MAGENTA (recoloured from the shipped
                             red set, kept as sources in art/synthwave_hud/prompt_icons_red_src/); the two
                             PK07 icons stay PK07's (a staged two-line edit gives the arena icon a magenta
                             accent; the Dealer keeps his red X eyes - docs/dealer_identity.md).
  Deal panel                 the luck badges i_tod_badge_luck_10..100 and i_tod_luck_legend (Map 1 pills).
  Kit slab                   i_tod_hud_health_fill, under its hard contract (column-uniform, alpha 255,
                             near-neutral white: AetheriumPlayerInfo.lua v16.97 notes).
  Content icons              the 9 sold perks (canonical symbol kept, Map 2 frame + finish), the 11 power-ups
                             (subject kept, Map 2 token) and the Pack-a-Punch glyph i_tod_hud_pap_1.

Every image is a SAME-NAME, SAME-SIZE drop-in (already zoned, already in the GDT), so the landing is a file
swap plus ONE code tint (tod_upgrade.lua Round2Row: the round number red -> magenta, docs/184 "Code tints").

GEOMETRY IS NOT TASTE: every empty area is copied from the Lua that draws into it (the numbers are quoted
beside each piece).

  python tools/artgen/packs/r4_synthwave_hud.py              # -> art/generated/R4-synthwave-hud/ + reviews
  python tools/artgen/packs/r4_synthwave_hud.py --stage      # + tmp/redesign/R4-synthwave-hud/stage/ (+ base/)
  python tools/artgen/packs/r4_synthwave_hud.py --install    # LANDING ONLY: copy into source_data/tod_ui_images/_images
  python tools/artgen/packs/r4_synthwave_hud.py --check      # regenerate in memory; fail on any byte != installed,
                                                             # a missing GDT block / zone line, or a red Round2Row
  python tools/artgen/packs/r4_synthwave_hud.py --check --against stage
  python tools/artgen/packs/r4_synthwave_hud.py --fit-report     # W3A: perk / power-up safe-inset numbers per slot
  python tools/artgen/packs/r4_synthwave_hud.py --fit-selftest   # W3A: the safe-inset gate's negative controls

Deterministic: seeded rng only, no timestamps. Never hand-edit a generated PNG.
"""
import argparse, hashlib, importlib.util, math, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402
from synthwave import (PAL, LOOK, THEME, Svg, chamfer, poly_d, line_d, inset, mix, hexs, hexrgb, put_text, neon_word,  # noqa: E402
                       text_width, text_img, grain, scratches, embers, glow_of, _paste)
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
from scipy import ndimage  # noqa: E402

PACK = 'R4-synthwave-hud'
ROOT = artgen.ROOT
RED_ROOT = os.path.join(ROOT, 'tmp', 'redesign', PACK)
STAGE_ROOT = os.path.join(RED_ROOT, 'stage')
BASE_ROOT = os.path.join(RED_ROOT, 'base')
IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')
STAGE_IMG = os.path.join(STAGE_ROOT, IMG_REL)
BASE_IMG = os.path.join(BASE_ROOT, IMG_REL)
OUT = os.path.join(ROOT, 'art', 'generated', PACK)
ICON_SRC = os.path.join(ROOT, 'art', 'synthwave_hud', 'prompt_icons_red_src')
UPG_REL = os.path.join('ui', 'uieditor', 'menus', 'hud', 'tod_upgrade.lua')
PK07_REL = os.path.join('tools', 'artgen', 'packs', 'pk07_prompt_icons.py')

MAGENTA_RGB = hexrgb('magenta')
# the luck accent of the DEAL PANEL badges climbs cool -> hot with the bar (10..30 cyan, 40..60 violet,
# 70..100 magenta; 100 adds the "confirmed" sparkles)

# ================================================================================== shared helpers

def layered(w, h, base_fn, top_fn=None, grain_amp=0.03, seed=7, base_alpha=1.0, ss=2, hud=False):
    """BASE (plates, hairlines, scratches; grained) + TOP (tubes, rules, glyphs). base_alpha < 1 lets the
    world show faintly through a HUD plate (docs/184c: plates ~85-90% opaque). hud=True marks an in-world HUD V2
    plate: its base_alpha also takes the theme's LOOK hud_alpha_k (fallen 0.92: the red era's plates were ~85 %
    opaque, docs/182 s3, measured alpha 217; synthwave 1.0)."""
    if hud:
        base_alpha = base_alpha * LOOK['hud_alpha_k']
    b = Svg(w, h)
    base_fn(b)
    im = b.render(ss=ss)
    if grain_amp:
        im = grain(im, grain_amp, seed)
    if base_alpha < 1.0:
        a = im.split()[3].point(lambda v: int(round(v * base_alpha)))
        im.putalpha(a)
    if top_fn:
        t = Svg(w, h)
        top_fn(t)
        im.alpha_composite(t.render(ss=ss))
    return im


def bevel(s, shape, k=2.2, opacity=0.55):
    """The glass edge catching light: a steel_hi hairline just inside the TOP edge (R3's bevel)."""
    ins = inset(shape, k)
    top = min(p[1] for p in ins)
    run = [p for p in ins if abs(p[1] - top) < 0.5]
    if len(run) >= 2:
        s.path(line_d(run[0], run[-1]), stroke='steel_hi', sw=1.2, opacity=opacity)


def sparkle(s, cx, cy, r, color='cyan'):
    d = 'M%.2f,%.2f L%.2f,%.2f L%.2f,%.2f L%.2f,%.2f Z' % (cx, cy - r, cx + r * 0.22, cy, cx, cy + r, cx - r * 0.22, cy)
    d2 = 'M%.2f,%.2f L%.2f,%.2f L%.2f,%.2f L%.2f,%.2f Z' % (cx - r, cy, cx, cy - r * 0.22, cx + r, cy, cx, cy + r * 0.22)
    s.path(d + ' ' + d2, fill=color, opacity=0.6, filt=s.blur(r * 0.35, (cx - r, cy - r, cx + r, cy + r)))
    s.path(d + ' ' + d2, fill='#FFFFFF')


def pts_d(p):
    return poly_d(p)


def rot(pts, ang, cx, cy):
    c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(cx + (x - cx) * c - (y - cy) * s_, cy + (x - cx) * s_ + (y - cy) * c) for x, y in pts]


def octagon(x0, y0, x1, y1, c):
    return chamfer(x0, y0, x1, y1, tl=c, tr=c, br=c, bl=c)

# ------------------------------------------------------------------------- the glyph compositor
# Every content glyph in R4 (perk symbols, power-up subjects, the PaP chevrons, the clovers) is drawn as
# COVERAGE (white-filled svg shapes rendered by resvg) and composited here as a neon sign: white-hot ink,
# the accent parts in their neon colour, and a soft halo of the glyph's own hue around the whole thing.

def coverage(w, h, body, ss=4):
    if not body:
        return np.zeros((h, w))
    im = artgen.render_svg(artgen.svg_doc(w, h, body), w, h, ss=ss)
    return np.clip(np.asarray(im, dtype=np.float64)[..., 3] / 255.0, 0.0, 1.0)


def neon_glyph(white_cov, acc_cov, hue, acc=None, sigma=7.0, k=0.85, ink=(255, 250, 255), acc_lift=0.18,
               cut_cov=None):
    """white_cov / acc_cov: float coverage maps. hue = the halo colour; acc = the accent ink colour
    (default: the hue). cut_cov: coverage punched out of the ink (eye sockets, gaps) - transparent there,
    so the glass behind shows. Returns RGBA."""
    acc = acc or hue
    hr, ar = np.array(hexrgb(hue), float), np.array(hexrgb(mix(acc, '#FFFFFF', acc_lift)), float)
    cA = acc_cov
    cW = white_cov * (1.0 - cA)
    S = np.clip(cA + cW, 0.0, 1.0)
    if cut_cov is not None:
        S = S * (1.0 - cut_cov)
        cA = cA * (1.0 - cut_cov)
        cW = cW * (1.0 - cut_cov)
    g = ndimage.gaussian_filter(S, sigma, mode='constant')
    g2 = ndimage.gaussian_filter(S, sigma * 0.35, mode='constant')
    gA = np.clip(k * (0.75 * g + 0.55 * g2), 0.0, 1.0)
    with np.errstate(invalid='ignore', divide='ignore'):
        rA = np.where(S > 1e-9, cA / np.maximum(S, 1e-9), 0.0)
    ink_rgb = np.array(ink, float)
    solid = (1 - rA)[..., None] * ink_rgb + rA[..., None] * ar
    outA = S + gA * (1.0 - S)
    with np.errstate(invalid='ignore', divide='ignore'):
        rgb = np.where(outA[..., None] > 1e-9,
                       (solid * S[..., None] + hr * (gA * (1.0 - S))[..., None]) / np.maximum(outA, 1e-9)[..., None], 0.0)
    out = np.dstack([rgb, outA * 255.0])
    out = np.clip(np.round(out), 0, 255).astype(np.uint8)
    out[out[..., 3] == 0] = 0
    return Image.fromarray(out, 'RGBA')


def percent_mark(cap):
    """'%' does not exist in our typeface (A-Z 0-9 - ' . $ + / only), so it is DRAWN in the glyph weight:
    two oblique rings and a bar, a white face inside the face's dark outline (R3 drew '#' the same way).
    Returns (RGBA, advance) for cap height `cap`; the ink box is [0, adv] x [-cap, 0] around (pad, base)."""
    adv = cap * 0.86
    pad = int(cap * 0.4) + 2
    W, H = int(adv + pad * 2), int(cap + pad * 2)
    by = pad + cap
    rr = cap * 0.2
    sw = cap * 0.13
    x0 = pad

    def shapes(c, extra):
        return ('<ellipse cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f" fill="none" stroke="%s" stroke-width="%.2f"/>'
                % (x0 + rr + sw * 0.6, by - cap + rr + sw * 0.6, rr, rr, c, sw + extra)
                + '<ellipse cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f" fill="none" stroke="%s" stroke-width="%.2f"/>'
                % (x0 + adv - rr - sw * 0.6, by - rr - sw * 0.6, rr, rr, c, sw + extra)
                + '<path d="M%.2f,%.2f L%.2f,%.2f" stroke="%s" stroke-width="%.2f" stroke-linecap="square"/>'
                % (x0 + adv * 0.80, by - cap + sw * 0.4, x0 + adv * 0.20, by - sw * 0.4, c, sw * 1.1 + extra))
    # the face's dark outline (the glyph cells' outline ~0.11 cap wide), then the white face
    im = artgen.render_svg(artgen.svg_doc(W, H, shapes(hexs('glyph_ink'), cap * 0.11) + shapes('#FFFFFF', 0.0)), W, H, ss=4)
    return im, adv, pad, by


def put_text_pct(canvas, parts, cap, baseline, cx=None, x=None, track=0.0):
    """Lay a row of (text, colour, glow) parts and the literal '%' (drawn), centred on cx or from x."""
    items = []
    total = 0.0
    gap = text_width('A A', cap, track) - text_width('AA', cap, track)      # the typeface's own word space
    for i, (t, col, glow) in enumerate(parts):
        if t == '%':
            im, adv, pad, by = percent_mark(cap)
            items.append(('pct', col, glow, adv, (im, pad, by)))
            total += adv
        else:
            w = text_width(t, cap, track)
            items.append(('t', col, glow, w, t))
            total += w
        if i < len(parts) - 1:
            nxt = parts[i + 1][0]
            total += (cap * 0.10 if nxt == '%' else gap)
    pen = (cx - total / 2.0) if cx is not None else x
    for i, (kind, col, glow, w, data) in enumerate(items):
        if kind == 'pct':
            im, pad, by = data
            # tint the white face, keep the dark outline
            a = np.asarray(im).astype(np.float64)
            neon = glow and hexs(col) == hexs(glow)
            c = np.array(hexrgb(mix(col, '#FFFFFF', LOOK['word_face']) if neon else col), float)   # neon_word's face
            lum = a[..., :3].mean(-1, keepdims=True) / 255.0
            a[..., :3] = lum * c
            tinted = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
            px, py = int(round(pen - pad)), int(round(baseline - by))
            if glow:
                big = Image.new('RGBA', (tinted.width + 40, tinted.height + 40), (0, 0, 0, 0))
                big.alpha_composite(tinted, (20, 20))
                _paste(canvas, glow_of(big, glow, cap * 0.2, 1.6 * LOOK['word_glow_k']), px - 20, py - 20)
                _paste(canvas, glow_of(big, glow, cap * 0.07, 1.2 * LOOK['word_glow_k']), px - 20, py - 20)
            _paste(canvas, tinted, px, py)
        else:
            if glow and hexs(col) != hexs(glow):
                put_text(canvas, data, cap, baseline, col, x=pen, track=track, glow=glow, glow_r=cap * 0.2,
                         glow_k=LOOK['word_glow_k'])
            elif glow:
                neon_word(canvas, data, cap, baseline, glow, x=pen, track=track)
            else:
                put_text(canvas, data, cap, baseline, col, x=pen, track=track)
        pen += w
        if i < len(items) - 1:
            nxt = items[i + 1][0]
            pen += (cap * 0.10 if nxt == 'pct' else gap)
    return total

# ============================================================================ A. HUD V2 CHROME (docs/184c)
# tod_upgrade.lua: Badge2 canvas 16..88 x 10..82 (192 art = 2.667 px/unit); the window x 38..153, y 60..123
# stays EMPTY (Round2Row writes the round there, cap 17 at baseline 53 -> art rows ~70..115).
RB_OUT = [(26, 12), (166, 12), (184, 30), (184, 112), (96, 180), (8, 112), (8, 30)]
RB_WIN = octagon(34, 56, 158, 128, 10)
# The ROUND tab is built EXACTLY like tools/battle_arena/make_badge.py builds its pill (outline octagon,
# a 1 px dark line 2 in, the fill 3 in), so the arena twin's wider BATTLE ARENA pill matches it. Its
# columns line up with make_badge's colour samples: outline x 55..56, dark line x 57, fill x 58.., the
# letters x 63..127 (brighter than 150 in every channel).
RB_TAB = (55, 24, 137, 47, 4)
TAB_OUTLINE, TAB_INNER, TAB_FILL = 'tab_outline', 'void', 'header'   # roles (make_badge samples the result)


def _tab(s):
    x0, y0, x1, y1, c = RB_TAB
    s.path(poly_d(octagon(x0, y0, x1, y1, c)), fill=TAB_OUTLINE)
    s.path(poly_d(octagon(x0 + 2, y0 + 2, x1 - 2, y1 - 2, c - 1)), fill=TAB_INNER)
    s.path(poly_d(octagon(x0 + 3, y0 + 3, x1 - 3, y1 - 3, c - 2)), fill=TAB_FILL)


def round_badge(rampage=False):
    W = H = 192

    def base(s):
        s.plate(RB_OUT, 'ramp_fill' if rampage else 'plate', top='ramp_top' if rampage else 'plate_top')
        if rampage:
            s.glow_fill(inset(RB_OUT, 12), 'magenta', 0.10, 14)
        s.steel(RB_OUT, 1.8)
        bevel(s, RB_OUT)
        s.path(poly_d(inset(RB_OUT, 6)), stroke='steel_hi', sw=1.0, opacity=0.30)
        s.path(poly_d(RB_WIN), fill='url(#%s)' % s.lin([(0, 'glass', 1), (0.35, 'void', 1), (1, 'deep', 1)]))
        s.steel(RB_WIN, 1.6)
        # two short ledger lines either side of the tab (the badge's own rhythm)
        for x0, x1 in ((24, 46), (146, 168)):
            s.path(line_d((x0, 36), (x1, 36)), stroke='steel', sw=1.4, opacity=0.9)

    def top(s):
        if rampage:
            s.tube(poly_d(RB_OUT), 'magenta', 2.8, glow=1.0, spread=0.55)
            inner = inset(RB_OUT, 7.5)
            # the sunset line runs round the top and the shoulders; it breaks across the V so the RAMPAGE
            # tag under the window has its own room
            run = [(inner[6][0], 120), inner[6], inner[0], inner[1], inner[2], (inner[2][0], 120)]
            s.tube(line_d(*run), 'sunset', 1.6, glow=0.55, spread=0.45)
        else:
            run = [(184, 62), (184, 112), (96, 180), (8, 112), (8, 62)]
            s.tube(line_d(*run), 'magenta', 2.6, glow=0.9, spread=0.55)
            # the descent: one down-chevron at the badge's foot
            s.tube(line_d((86, 145), (96, 155), (106, 145)), 'magenta', 2.2, glow=0.7, spread=0.5)
        s.tube(poly_d(RB_WIN), 'accent2', 1.4, glow=0.45, spread=0.4)
        _tab(s)

    im = layered(W, H, base, top, seed=301 + rampage, base_alpha=0.94, ss=4, hud=True)
    put_text(im, 'ROUND', 13, 41, 'white', cx=96, track=0.30)
    if rampage:
        put_text(im, 'RAMPAGE', 11.5, 145, 'ramp_word', cx=96, track=0.18, glow='magenta', glow_r=2.4,
                 glow_k=0.9 * LOOK['word_glow_k'])
        im = embers(im, (20, 132, 172, 168), 7, 307, colors=('magenta', 'sunset'), size=(0.5, 1.2), alpha=(50, 140))
        im = embers(im, (16, 16, 176, 52), 4, 308, colors=('magenta', 'sunset'), size=(0.5, 1.1), alpha=(40, 110))
    return im


def make_badge_module():
    spec = importlib.util.spec_from_file_location('tod_make_badge', os.path.join(ROOT, 'tools', 'battle_arena', 'make_badge.py'))
    mb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mb)
    return mb


def arena_badges(round_imgs):
    """The ARENA twins, made by the SHIPPED generator (tools/battle_arena/make_badge.py, imported - never
    copied) from the NEW round badges. Its build gate regenerates them the same way from the installed round
    badges, so after the landing it passes untouched. Returns {name: (RGBA, the exact bytes it writes)}."""
    import io
    mb = make_badge_module()
    tmp = tempfile.mkdtemp(prefix='r4_arena_')
    try:
        for f in os.listdir(artgen.IMG):
            if f.startswith('i_tod_hud_l') and f.endswith('.png'):
                shutil.copy2(os.path.join(artgen.IMG, f), tmp)
        for name, im in round_imgs.items():
            with open(os.path.join(tmp, name + '.png'), 'wb') as fh:
                fh.write(artgen.png_bytes(im))
        mb.IMG = tmp
        mb._cells.clear()
        M = mb.metrics()
        out = {}
        for twin, src in mb.TWINS.items():
            im, _info = mb.make(src, M)
            data = mb.encode(im)
            out[twin] = (Image.open(io.BytesIO(data)).convert('RGBA'), data)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# The LUCK plate (tod_upgrade.lua Status2: canvas 94..330 x 16..76, 944 x 240 art = 4 px/unit). The channel
# x 64..904, y 132..204 stays EMPTY: ten segments land at art x 68..900, y 144..192.
LP_OUT = chamfer(4, 4, 940, 236, tl=30, br=30)
LP_CH = chamfer(62, 130, 906, 206, tl=8, br=8)


def clover_cov(w, h, cx, cy, r):
    """A four-leaf clover (the luck glyph): four heart-leaves round a hub and a curled stem. Returns
    (ink coverage, cut coverage: the hairline gaps between the leaves so four leaves read at 30 px)."""
    return coverage(w, h, clover_body(cx, cy, r)), coverage(w, h, clover_cut(cx, cy, r))


def heart_pts(n=48):
    """The classic heart curve, lobes up (-y), point down (+y), roughly unit size."""
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        out.append((x / 17.0, (y + 2.5) / 17.0))
    return out


def clover_body(cx, cy, r, stem=True):
    """Four hearts with their points on the hub, at the diagonals, and a curled stem."""
    hp = heart_pts()
    parts = []
    for ang in (45, 135, 225, 315):
        a = math.radians(ang)
        # the heart's point (+y in its frame) faces the hub: rotate its "up" (-y) to the outward direction
        rr = r * 0.50
        ox, oy = cx + math.cos(a) * r * 0.50, cy + math.sin(a) * r * 0.50
        th = a + math.pi / 2          # maps local -y (up) onto the outward direction
        c, s_ = math.cos(th), math.sin(th)
        p = [(ox + (x * c - y * s_) * rr, oy + (x * s_ + y * c) * rr) for x, y in hp]
        parts.append('<path d="%s" fill="#fff"/>' % poly_d(p))
    parts.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="#fff"/>' % (cx, cy, r * 0.12))
    if stem:
        parts.append('<path d="M%.2f,%.2f Q%.2f,%.2f %.2f,%.2f" fill="none" stroke="#fff" stroke-width="%.2f" stroke-linecap="round"/>'
                     % (cx + r * 0.1, cy + r * 0.2, cx + r * 0.32, cy + r * 0.8, cx + r * 0.78, cy + r * 1.0, r * 0.14))
    return ''.join(parts)


def clover_cut(cx, cy, r):
    """Hairline gaps between the four leaves (a diagonal-free cross through the hub)."""
    return ('<path d="M%.2f,%.2f L%.2f,%.2f M%.2f,%.2f L%.2f,%.2f" stroke="#fff" stroke-width="%.2f"/>'
            % (cx - r * 1.2, cy, cx - r * 0.16, cy, cx + r * 0.16, cy, cx + r * 1.2, cy, r * 0.09)
            + '<path d="M%.2f,%.2f L%.2f,%.2f M%.2f,%.2f L%.2f,%.2f" stroke="#fff" stroke-width="%.2f"/>'
            % (cx, cy - r * 1.2, cx, cy - r * 0.16, cx, cy + r * 0.16, cx, cy + r * 0.62, r * 0.09))


def luck_plate(rampage=False):
    W, H = 944, 240

    def base(s):
        s.plate(LP_OUT, 'ramp_fill' if rampage else 'plate', top='ramp_top' if rampage else 'plate_top')
        if rampage:
            s.glow_fill(inset(LP_OUT, 14), 'magenta', 0.06, 26)
        s.steel(LP_OUT, 2.0)
        bevel(s, LP_OUT, 3.0)
        s.path(poly_d(LP_CH), fill='url(#%s)' % s.lin([(0, 'channel_top', 1), (0.25, 'void', 1), (1, 'channel_lo', 1)]))
        s.steel(LP_CH, 1.8)
        s.path(line_d((72, 133.5), (896, 133.5)), stroke='#000000', sw=2.0, opacity=0.6)   # the recess's lip
        scratches(s, (300, 20, 920, 110), 7, 311 + rampage, opacity=0.04, length=(30, 120))

    def top(s):
        if rampage:
            s.tube(poly_d(LP_OUT), 'magenta', 3.2, glow=1.0, spread=0.6)
            s.tube(poly_d(inset(LP_OUT, 11)), 'sunset', 1.8, glow=0.5, spread=0.5)
        else:
            s.tube(line_d((4, 92), (4, 34), (34, 4), (720, 4)), 'magenta', 3.0, glow=0.9, spread=0.6)
            s.tube(line_d((940, 64), (940, 112)), 'tick', 2.4, glow=0.6, spread=0.5)
        s.tube(line_d((62, 146), (62, 190)), 'accent2', 2.2, glow=0.55, spread=0.45)   # the channel's start tick

    im = layered(W, H, base, top, seed=310 + rampage, base_alpha=0.92, hud=True)
    cw, cut = clover_cov(W, H, 86, 70, 40)
    im.alpha_composite(neon_glyph(cw, np.zeros_like(cw), 'clover', sigma=6, k=0.7, cut_cov=cut))
    put_text(im, 'LUCK', 36, 88, 'white', x=140, track=0.16)
    if rampage:
        neon_word(im, 'RAMPAGE', 24, 66, 'magenta', right=904, track=0.20, glow_r=4.5, glow_k=0.85)
        im = embers(im, (300, 24, 930, 118), 16, 317, colors=('magenta', 'sunset', 'magenta'), size=(0.8, 2.0), alpha=(60, 170))
        im = embers(im, (40, 212, 930, 230), 8, 318, colors=('magenta', 'sunset'), size=(0.7, 1.6), alpha=(50, 140))
    return im


# One luck SEGMENT (76 x 48, drawn 19 x 12 canvas). Lit = a lit pip (STYLE section 5): white-hot glass with
# cyan edges - the core stays near-WHITE because ON FIRE multiplies the lit segments by (1, 0.62, 0.30)
# (tod_upgrade.lua drawLuckV2), and only a bright core turns that into a readable orange.
LS = [(18, 7), (72, 7), (58, 41), (4, 41)]


def luck_seg(lit):
    s = Svg(76, 48)
    if lit:
        # pale cyan, not saturated: under the ON FIRE tint a saturated cyan rim and halo go GREEN; this pale
        # cyan goes tan-orange with the core (measured in the review, see LAND.md)
        s.path(poly_d(LS), fill='seg_glow', opacity=0.7, filt=s.blur(3.0, (4, 7, 72, 41)))
        g = s.lin([(0, 'seg_a', 1), (0.45, 'seg_hot', 1), (0.8, 'seg_c', 1), (1, 'seg_d', 1)])
        s.path(poly_d(LS), fill='url(#%s)' % g)
        s.path(poly_d(LS), stroke='seg_rim', sw=2.4)
        s.path(line_d((22, 12), (66, 12)), stroke='#FFFFFF', sw=2.0, opacity=0.9)
    else:
        s.path(poly_d(LS), fill='off_fill', opacity=0.96)
        s.path(poly_d(LS), stroke='off_edge', sw=2.4)
        s.path(line_d((21, 11), (68, 11)), stroke='dead', sw=1.2)
    return s.render(ss=4)


# The GUN PLATE (AetheriumLoadout.lua: canvas 998..1262 x 606..678 + HUD_DX 4; 1056 x 288 art = 4 px/unit).
# EMPTY: the name rows (right edge art 1016, baselines art 36 / 92 - two-line names reach above the plate),
# the gun bay (gun_icon canvas 1004..1100 x 632..676 = art 24..408 x 104..280: the well sits under it),
# the clip (right art 752, cap 108 at baseline 260) and the reserve (right art 1008, cap 68 at baseline 256).
GP_OUT = chamfer(4, 4, 1052, 284, tl=26, br=26)
GP_WELL = chamfer(20, 100, 410, 278, tl=12, br=12)


def gun_plate():
    W, H = 1056, 288

    def base(s):
        s.plate(GP_OUT, 'plate', top='plate_top')
        s.steel(GP_OUT, 2.0)
        bevel(s, GP_OUT, 3.0)
        s.path(poly_d(GP_WELL), fill='url(#%s)' % s.rad([(0, 'inner', 1), (1, 'deep', 1)], 0.5, 0.45, 0.75))
        s.steel(GP_WELL, 1.6, opacity=0.9)
        s.path(line_d((34, 101.5), (398, 101.5)), stroke='#000000', sw=2.0, opacity=0.5)
        scratches(s, (440, 120, 1030, 270), 6, 321, opacity=0.035, length=(30, 120))

    def top(s):
        s.tube(line_d((4, 88), (4, 30), (30, 4), (660, 4)), 'magenta', 3.0, glow=0.9, spread=0.6)
        s.tube(line_d((1052, 132), (1052, 200)), 'tick', 2.6, glow=0.6, spread=0.5)
        # the clip / reserve slash (the theme draws every slash as a cyan neon stroke): between the clip's right
        # edge (art 752) and the reserve's widest left edge (~art 818)
        s.slashes(772, 252, 54, 1, 'accent2', w=3.2, glow=0.6)
        s.path(poly_d(GP_WELL), stroke='violet', sw=1.2, opacity=0.6)

    return layered(W, H, base, top, seed=320, base_alpha=0.90, hud=True)


# ABILITY TILES (AetheriumLoadout.lua slot.tile: 46 x 32 canvas; 184 x 128 art = 4 px/unit). The icon
# (x0+5..x0+29 -> art 20..116, y 16..112) and the charge count sit in the EMPTY centre.
TL = chamfer(5, 5, 179, 123, tl=16, br=16)


def tile(kind):
    W, H = 184, 128

    def base(s):
        if kind == 'ready':
            s.plate(TL, 'ready_fill', top='ready_top')
            s.glow_fill(inset(TL, 8), 'magenta', 0.07 * LOOK['wash_k'], 14)
        else:
            s.plate(TL, 'plate', top='plate_top')
        s.steel(TL, 1.8)
        bevel(s, TL)
        scratches(s, (14, 12, 170, 116), 3, 330 + len(kind), opacity=0.035, length=(14, 40))

    def top(s):
        if kind == 'ready':
            s.tube(poly_d(TL), 'magenta', 3.0, glow=1.0, spread=0.42)
        elif kind == 'pap':
            s.tube(poly_d(TL), 'pap_frame', 2.4, glow=0.75, spread=0.42)
        else:
            s.tube(line_d((26, 123), (150, 123)), 'idle_edge', 1.6, glow=0.3, spread=0.45)

    return layered(W, H, base, top, seed=330, base_alpha=0.92, ss=4, hud=True)


# PERK SOCKET (AetheriumPerkItem.lua: 32 x 32 canvas, the perk drawn inset 3 -> art 12..116).
PS = chamfer(4, 4, 124, 124, tl=12, br=12)


def perk_socket():
    def base(s):
        s.plate(PS, 'socket_fill', top='socket_top')
        s.steel(PS, 1.8)
        bevel(s, PS, 2.0)

    def top(s):
        s.tube(line_d((124, 96), (124, 112), (112, 124), (96, 124)), 'magenta', 2.0, glow=0.7, spread=0.45)

    return layered(128, 128, base, top, seed=340, base_alpha=0.92, ss=4, hud=True)


# MEDALLION RING (AetheriumPlayerInfo.lua: ring 24..80 x 620..676, the medallion 28.5..75.5 = art 20.6..235.4:
# the whole inside is transparent).
MR_O = octagon(6, 6, 250, 250, 66)
MR_I = octagon(20, 20, 236, 236, 60)


def medallion_ring():
    W = H = 256

    def base(s):
        d = poly_d(MR_O) + ' ' + poly_d(list(reversed(MR_I)))
        s.add('<path d="%s" fill="%s" fill-rule="evenodd"/>' % (d, hexs('ring_band')))
        s.steel(MR_O, 2.0)
        s.steel(MR_I, 1.6, opacity=0.9)
        s.path(poly_d(inset(MR_O, 7)), stroke='steel_hi', sw=1.0, opacity=0.3)

    def top(s):
        # Lead review 2026-10-05: no RED run on the class ring (user, the same day: "I dont want that red fill" on the
        # class icons). In the Fallen theme the long run is lit STEEL like the short one; synthwave keeps its magenta.
        long_run = 'magenta' if THEME == 'synthwave' else 'accent2'
        s.tube(line_d((6, 96), (6, 184), (72, 250), (160, 250)), long_run, 3.0, glow=0.95, spread=0.5)
        s.tube(line_d((150, 6), (184, 6), (250, 72), (250, 92)), 'accent2', 2.2, glow=0.6, spread=0.45)

    return layered(W, H, base, top, seed=350, base_alpha=0.94, ss=4, hud=True)


def points_glyph():
    """The points glyph: our typeface's '$' cell (the barred Z the HUD prints points with), gold, alone."""
    im = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    put_text(im, '$', 98, 112, 'gold', cx=64, glow='gold', glow_r=6, glow_k=0.6)
    return im


# The power-up TOAST (AetheriumPowerupNotification.lua: canvas 534..746 x 512..561, 848 x 196 art = 4 px/unit;
# the icon 537..580 x 515..558 -> art 12..184 x 12..184 and the name 586..740 x 528..545 -> art 208..824).
TO_OUT = chamfer(4, 4, 844, 192, tl=24, br=24)
TO_WELL = octagon(12, 12, 184, 184, 26)


def toast():
    W, H = 848, 196

    def base(s):
        s.plate(TO_OUT, 'plate', top='plate_top')
        s.steel(TO_OUT, 2.0)
        bevel(s, TO_OUT, 3.0)
        s.path(poly_d(TO_WELL), fill='url(#%s)' % s.rad([(0, 'glass', 1), (1, 'deep', 1)]))
        s.steel(TO_WELL, 1.6)
        scratches(s, (300, 20, 830, 180), 5, 361, opacity=0.035, length=(30, 120))

    def top(s):
        s.tube(line_d((4, 80), (4, 28), (28, 4), (620, 4)), 'toast_edge', 3.0, glow=0.9, spread=0.6)
        s.tube(line_d((844, 120), (844, 168), (820, 192), (700, 192)), 'violet', 2.0, glow=0.4, spread=0.5)
        s.tube(poly_d(TO_WELL), 'accent2', 2.0, glow=0.6, spread=0.45)

    return layered(W, H, base, top, seed=360, base_alpha=0.92, hud=True)


# THE HEALTH FRAME (AetheriumPlayerInfo.lua: the frame and its fill share one rect, 90..220 x 645..657). The WHITE
# fill is theme-neutral and NOT redrawn (docs/184c): i_tod_h2_hp_fill's white strip is art x 6..537, y 6..41, so the
# frame's line runs just outside it and its 15 cells divide it exactly. (i_tod_h2_shield_frame is drawn by nothing -
# the shield bar is its fill alone - and R5 purges it, so R4 does not redraw it.)
def hp_frame():
    W, H = 544, 48
    s = Svg(W, H)
    out = chamfer(3.5, 3.5, 540.5, 44.5, tl=4, br=4)
    s.path(poly_d(chamfer(2, 2, 542, 46, tl=5, br=5)), stroke='void', sw=3.2, opacity=0.85)
    s.steel(out, 2.2)
    s.path(line_d((10, 5.2), (534, 5.2)), stroke='steel_hi', sw=1.0, opacity=0.6)
    x0, x1 = 6.0, 538.0
    for k in range(1, 15):
        x = x0 + (x1 - x0) * k / 15.0
        s.path(line_d((x, 6), (x, 42)), stroke='void', sw=2.6, opacity=0.95)
        s.path(line_d((x, 7), (x, 41)), stroke='steel', sw=0.8, opacity=0.7)
    s.tube(line_d((3.5, 12), (3.5, 36)), 'tick', 2.6, glow=0.6, spread=0.35)
    return s.render(ss=4)


# THE DESCENT GAUGE (tod_upgrade.lua V2: Rail canvas 1232..1264 x 110..560, 64 x 900 art = 2 px/unit; the track
# G2_T0..G2_T1 = art y 76..824 stays dark - the 25 segments land at art x 18..46, hubs 12..52).
GT_TRACK = chamfer(10, 74, 54, 826, tl=5, tr=5, br=5, bl=5)
GT_TOP = chamfer(4, 4, 60, 68, tl=10, tr=10)
GT_BOT = chamfer(4, 832, 60, 896, bl=10, br=10)


def crown_body(cx, cy, w):
    """A crown glyph (the start: the party spawns in the crown) as svg fill."""
    h = w * 0.62
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    p = [(x0, y1 - h * 0.22), (x0, y0 + h * 0.18), (x0 + w * 0.25, y0 + h * 0.52), (cx, y0), (x1 - w * 0.25, y0 + h * 0.52),
         (x1, y0 + h * 0.18), (x1, y1 - h * 0.22)]
    band = chamfer(x0, y1 - h * 0.16, x1, y1)
    pts = ''.join('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="#fff"/>' % (x, y - w * 0.02, w * 0.075)
                  for x, y in ((x0, y0 + h * 0.18), (cx, y0), (x1, y0 + h * 0.18)))
    return '<path d="%s" fill="#fff"/>' % poly_d(p) + '<path d="%s" fill="#fff"/>' % poly_d(band) + pts


def gauge_tower():
    W, H = 64, 900

    def base(s):
        s.plate(GT_TOP, 'plate', top='plate_top', sheen=0.04)
        s.plate(GT_BOT, 'plate', top='plate_top', sheen=0.04)
        s.path(poly_d(GT_TRACK), fill='url(#%s)' % s.lin([(0, 'void', 1), (0.5, 'track_mid', 1), (1, 'void', 1)], 0, 0, 1, 0))
        s.steel(GT_TOP, 1.8)
        s.steel(GT_BOT, 1.8)
        s.steel(GT_TRACK, 1.6)
        for y0, y1 in ((68, 74), (826, 832)):
            s.path(line_d((26, y0), (26, y1)), stroke='steel', sw=1.6)
            s.path(line_d((38, y0), (38, y1)), stroke='steel', sw=1.6)
        # the etched "descend" chevron under the crown (faint: the top segments draw over it)
        s.path(line_d((22, 84), (32, 92), (42, 84)), stroke='steel_hi', sw=1.6, opacity=0.5)

    def top(s):
        s.tube(line_d((54, 110), (54, 790)), 'violet', 1.2, glow=0.3, spread=0.4)
        s.tube(line_d((10, 878), (54, 878)), 'accent2', 2.6, glow=0.7, spread=0.45)   # THE GROUND: where the party is going
        s.tube(poly_d(GT_TOP), 'magenta', 1.8, glow=0.6, spread=0.4)

    im = layered(W, H, base, top, seed=370, base_alpha=0.92, ss=4, hud=True)
    cv = coverage(W, H, crown_body(32, 38, 40))
    im.alpha_composite(neon_glyph(cv, np.zeros_like(cv), 'crown', sigma=2.6, k=0.9))
    g = coverage(W, H, ''.join('<rect x="%.1f" y="854" width="8" height="18" fill="#fff"/>' % x for x in (18, 28, 38))
                 + '<rect x="14" y="846" width="36" height="5" fill="#fff"/>')
    im.alpha_composite(neon_glyph(g, np.zeros_like(g), 'accent2', sigma=2.0, k=0.5))
    return im


SG = chamfer(1.5, 3.5, 38.5, 20.5, tl=4, tr=4, br=4, bl=4)


def gauge_seg_off():
    s = Svg(40, 24)
    s.path(poly_d(SG), fill='off_fill', opacity=0.95)
    s.path(poly_d(SG), stroke='off_edge', sw=1.8)
    return s.render(ss=4)


def gauge_you():
    s = Svg(48, 48)
    p = [(10, 7), (25, 7), (41, 24), (25, 41), (10, 41), (25, 24)]
    s.path(poly_d(p), fill='magenta', opacity=0.8, filt=s.blur(3.2, (10, 7, 41, 41)))
    s.path(poly_d(p), fill='url(#%s)' % s.lin([(0, 'you_hi', 1), (0.5, 'you_mid', 1), (1, 'magenta', 1)], 0, 0, 1, 0))
    s.path(poly_d(p), stroke='magenta', sw=1.6)
    s.path(line_d((14, 10), (24, 10), (37, 24)), stroke='#FFFFFF', sw=1.6, opacity=0.9)
    return s.render(ss=4)


def gauge_down():
    s = Svg(48, 48)
    s.circle(24, 24, 15, fill='none', stroke='magenta', sw=7, opacity=0.6, filt=s.blur(3.0, (9, 9, 39, 39)))
    s.circle(24, 24, 15, fill='none', stroke='down_rim', sw=3.6)
    s.circle(24, 24, 15, fill='none', stroke='down_core', sw=1.2)
    cross = 'M24,15 L24,33 M15,24 L33,24'
    s.path(cross, stroke='magenta', sw=7.5, opacity=0.6, filt=s.blur(2.5, (15, 15, 33, 33)))
    s.path(cross, stroke='down_rim', sw=5.0)
    s.path(cross, stroke='#FFFFFF', sw=1.8)
    return s.render(ss=4)

# ======================================================================== B. PROMPT CARDS (docs/184d)
# TodPromptCard.lua BOX, 4 px per canvas unit on the 924 x 304 card (docs/183_prompt_ref/slot_map_924x304.png):
#   icon well x 8..284 y 4..296 (the icon 60..236 x 68..244)   title x 304..904 y 17..63
#   underline x 284..916 y 66..72                               body x 304..892 y 72..226
#   divider x 288..912 y 226..228   footer x 304..716 y 228..290   price x 732..908 y 228..290
# Title band, body, footer and price stay FLAT and DARK. The wide card is the same card 276 px longer: the
# well keeps x 8..284, every right-hand position moves right by 276 (TodPromptCard.SetWide, WIDE_DX 69 units).

def chassis(kind='normal'):
    dx = 276 if kind == 'wide' else 0
    W, H = 924 + dx, 304
    locked = kind == 'locked'
    out = chamfer(3, 3, 921 + dx, 301, tl=22, br=22)
    well = chamfer(12, 12, 280, 292, tl=16, br=16)
    band = chamfer(294, 10, 910 + dx, 64, tl=0, br=8)
    pocket = chamfer(726 + dx, 236, 912 + dx, 288, tl=8, br=8)

    def base(s):
        if locked:
            s.plate(out, 'locked_fill', top='locked_top', sheen=0.03)
        else:
            s.plate(out, 'plate', top='row_top', sheen=0.04)
        s.path(poly_d(band), fill='url(#%s)' % s.lin([(0, 'locked_band' if locked else 'header_top', 1), (1, 'locked_band2' if locked else 'header', 1)]))
        s.path(poly_d(well), fill='url(#%s)' % s.rad([(0, 'locked_well' if locked else 'glass', 1), (1, 'deep', 1)], 0.5, 0.45, 0.7))
        s.path(poly_d(pocket), fill='pocket', opacity=0.85)
        s.steel(out, 2.0)
        bevel(s, out, 3.0, opacity=0.4 if locked else 0.55)
        s.steel(well, 1.6)
        s.path(poly_d(pocket), stroke='steel', sw=1.2, opacity=0.55)
        s.path(line_d((288, 227), (912 + dx, 227)), stroke='steel', sw=2.0, opacity=0.95)   # the divider
        # (no scratches, no grain on a card: every right-hand area carries game text)

    def top(s):
        if locked:
            s.dead_tube(poly_d(out), 2.4)
            s.dead_tube(poly_d(well), 1.8)
            s.dead_tube(line_d((288, 69), (916 + dx, 69)), 2.4, 'dead_red', 'dead_red_core')
            # one broken fragment of the old light, cold and unlit, so the card reads REFUSED not "off"
            s.path(line_d((25, 3), (150, 3)), stroke='dead_frag', sw=2.0, opacity=0.9)
        else:
            s.tube(poly_d(out), 'magenta', 2.8, glow=0.85, spread=0.38)
            s.tube(poly_d(well), 'accent2', 2.2, glow=0.6, spread=0.4)
            s.tube(line_d((288, 69), (916 + dx, 69)), 'cyan', 3.0, glow=0.7, spread=0.45)

    return layered(W, H, base, top, grain_amp=0.0, seed=400 + dx + locked, base_alpha=0.95)


# The docs/183 icons: white glyphs with ONE accent. Their red accent (242,32,58) becomes MAGENTA; every
# pixel of those icons lies on the white..red line (measured: max error 11/255), so the swap is exact:
# t = how far toward the accent a pixel is, re-mixed toward magenta. Sources: the shipped red set, kept in
# art/synthwave_hud/prompt_icons_red_src/ (pinned below - a generator must not read its own output). The crown and
# extract icons left this set 2026-10-05 (W2E): only the retired Map One ending's hints drew them; their red sources
# and their magenta builds are in archive/map1_carryover/.
ICON_SRC_MD5 = {
    'i_tod_prompt_icon_alarm': '8b4f2338cb405bcdcef8c37d219165bb',
    'i_tod_prompt_icon_altar': '911a974ec8accb848f72df962c8fd057',
    'i_tod_prompt_icon_crate': 'b8ed89ea54a6a611d4b90087843c1e31',
    'i_tod_prompt_icon_door': '41143560c4ca7d1ff3b56a6a64014637',
    'i_tod_prompt_icon_generic': '5a9fc1736c3028b8fc877bbd36ddb3d3',
    'i_tod_prompt_icon_pap': '5b4eaa55f87c700bf0810f44e3744fc3',
    'i_tod_prompt_icon_partner_bench': '6c3a595537d695dcb119540bbd81d539',
    'i_tod_prompt_icon_perk': 'b08d3ad8b7b1d9f2fbb1fe4397b7c5b2',
    'i_tod_prompt_icon_power': '528cb9392b1ca6d0d8ebbce5e35a8f90',
    'i_tod_prompt_icon_rampage': '3033a4ff4a2398123ee1695f052b65bd',
    'i_tod_prompt_icon_teleporter': '312c1d7ca4ab20d84cd50cd32e453970',
}
SRC_RED = np.array((242, 32, 58), float)
ICON_ACCENT = np.array(hexrgb('magenta'), float)    # the theme's frame light (fallen: the source red itself)


def recolor_icon(name):
    p = os.path.join(ICON_SRC, name + '.png')
    data = open(p, 'rb').read()
    if hashlib.md5(data).hexdigest() != ICON_SRC_MD5[name]:
        raise SystemExit('r4: %s is not the pinned red source (art/synthwave_hud/prompt_icons_red_src)' % p)
    a = np.asarray(Image.open(p).convert('RGBA')).astype(np.float64)
    tg = (255.0 - a[..., 1]) / (255.0 - SRC_RED[1])
    tb = (255.0 - a[..., 2]) / (255.0 - SRC_RED[2])
    t = np.clip((tg + tb) * 0.5, 0.0, 1.0)[..., None]
    rgb = (1.0 - t) * 255.0 + t * ICON_ACCENT
    out = np.dstack([rgb, a[..., 3]])
    out = np.clip(np.round(out), 0, 255).astype(np.uint8)
    out[out[..., 3] == 0] = 0
    return Image.fromarray(out, 'RGBA')


# PK07 owns i_tod_prompt_icon_black_market + _arena (its own --check gate). R4's one-time staged edit (a magenta
# accent for the arena ring) LANDED 2026-10-04; since the RT pass (2026-10-05) PK07 reads synthwave.THEME for that
# accent itself (PK07_THEME_LINES, wiring_problems). The Dealer keeps his red X eyes + grin in every theme.


def pk07_module(path):
    spec = importlib.util.spec_from_file_location('tod_pk07_%d' % (abs(hash(path)) % 100000), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pk07_icons(staged_path):
    m = pk07_module(staged_path)
    return {n: im for n, im in m.build(False)}

# ======================================================================== C. DEAL PANEL LUCK BADGES
# tod_upgrade.lua LuckBadge + LuckLegend: 950..1230 x 150..210 / 214..274 = 280 x 60 canvas = the 420 x 90 art at
# 1:1 on a 1080p screen (uncompressed in the GDT, so 90 tall is fine). Baked per 10 % of the DEAL's luck.
LB = chamfer(4, 8, 416, 82, tl=14, br=14)
LB_WELL = chamfer(13, 15, 79, 75, tl=9, br=9)


def badge_hue(pct):
    return 'luck_lo' if pct <= 30 else ('luck_mid' if pct <= 60 else 'luck_hi')


def luck_badge(pct):
    W, H = 420, 90
    hue = badge_hue(pct)

    def base(s):
        s.plate(LB, 'badge_fill' if pct < 100 else 'ready_fill', top='badge_top')
        s.glow_fill(inset(LB, 8), hue, 0.05 + 0.04 * (pct / 100.0), 16)
        s.path(poly_d(LB_WELL), fill='url(#%s)' % s.rad([(0, mix(hue, 'void', 0.82), 1), (1, 'deep', 1)]))
        s.steel(LB, 1.8)
        bevel(s, LB, 2.4)

    def top(s):
        s.tube(poly_d(LB), hue, 2.6, glow=0.6 + 0.4 * (pct / 100.0), spread=0.42)
        s.tube(poly_d(LB_WELL), 'accent2' if hue != 'luck_lo' else 'well_alt', 1.6, glow=0.4, spread=0.4)
        if pct >= 100 and LOOK['sparkles']:
            for x, y, r in ((404, 16, 6.5), (20, 76, 5), (300, 13, 4)):
                sparkle(s, x, y, r, 'cyan')

    im = layered(W, H, base, top, seed=500 + pct, base_alpha=0.95)
    cb = coverage(W, H, clover_body(46, 43, 21))
    im.alpha_composite(neon_glyph(cb, np.zeros_like(cb), hue, sigma=3.0, k=0.7, cut_cov=coverage(W, H, clover_cut(46, 43, 21))))
    cap = 25.0
    parts = [('LUCK', 'white', None), (str(pct), hue + '_ink', hue), ('%', hue + '_ink', hue), ('BOOSTED', 'white', None)]
    while cap > 14:
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        tot = put_text_pct(layer, parts, cap, 56, cx=247)
        if tot <= 306:
            break
        cap -= 0.5
    im.alpha_composite(layer)
    if pct >= 100:
        im = embers(im, (100, 12, 400, 30), 5, 599, colors=('magenta', 'cyan'), size=(0.6, 1.4), alpha=(60, 150))
    return im


def luck_legend():
    W, H = 420, 90
    pl = chamfer(4, 12, 416, 78, tl=12, br=12)

    def base(s):
        s.plate(pl, 'plate', top='plate_top')
        s.steel(pl, 1.6)
        bevel(s, pl, 2.2)

    def top(s):
        s.tube(line_d((30, 78), (380, 78)), 'idle_edge', 1.6, glow=0.35, spread=0.4)
        for i, y in enumerate((52, 40)):
            s.tube(line_d((40, y + 4), (50, y - 6), (60, y + 4)), 'cyan', 2.6, glow=0.6, spread=0.45)
            s.tube(line_d((360, y + 4), (370, y - 6), (380, y + 4)), 'cyan', 2.6, glow=0.6, spread=0.45)

    im = layered(W, H, base, top, seed=520, base_alpha=0.95)
    put_text(im, 'BETTER CARDS', 24, 56, 'white', cx=210, track=0.16, fit=270)
    return im

# ==================================================================== D. THE KIT SLAB (health fill)
# i_tod_hud_health_fill, 1016 x 80: a HARD CONTRACT (AetheriumPlayerInfo.lua v16.97, TodAbilityFeedback.lua,
# TodTeleportFeedback.lua, AetheriumLoadout.lua TOD_SLAB): every column identical (uie_wipe_normal cuts it at any
# x), alpha 255 everywhere (tinted near-black it is a solid slab), near-neutral white with max saturation 16/255
# (the state machine TINTS it). Map 1's profile was a top highlight over a grey ramp; Map 2's is a NEON GLASS
# TUBE in cross-section: a white-hot core band across the middle, a lavender-cool body, a dark lower lip.
# RT: the profile is the theme's (synthwave: a lavender-cool tube; fallen: the same profile in the red era's cool steel
# white, R ~ G < B by 6 - both within the saturation-16 contract).
SLAB_KEYS = {
    'synthwave': [(0, (255, 255, 255)), (3, (246, 244, 252)), (10, (232, 228, 244)), (21, (252, 251, 255)),
                  (26, (255, 255, 255)), (35, (255, 255, 255)), (48, (228, 224, 240)), (66, (214, 210, 226)),
                  (73, (192, 188, 204)), (79, (172, 168, 184))],
    'fallen': [(0, (255, 255, 255)), (3, (244, 246, 251)), (10, (229, 232, 240)), (21, (250, 252, 255)),
               (26, (255, 255, 255)), (35, (255, 255, 255)), (48, (225, 228, 236)), (66, (211, 214, 222)),
               (73, (189, 192, 200)), (79, (169, 172, 180))],
}[THEME]


def health_fill():
    W, H = 1016, 80
    col = np.zeros((H, 3))
    for y in range(H):
        for (y0, c0), (y1, c1) in zip(SLAB_KEYS, SLAB_KEYS[1:]):
            if y0 <= y <= y1:
                t = 0.0 if y1 == y0 else (y - y0) / float(y1 - y0)
                col[y] = [c0[i] + (c1[i] - c0[i]) * t for i in range(3)]
                break
    col = np.round(col).astype(np.uint8)
    a = np.zeros((H, W, 4), np.uint8)
    a[..., :3] = col[:, None, :]
    a[..., 3] = 255
    return Image.fromarray(a, 'RGBA')


def slab_contract(im):
    a = np.asarray(im)
    if not (a == a[:, :1, :]).all():
        return 'not column-uniform'
    if (a[..., 3] != 255).any():
        return 'alpha is not 255 everywhere'
    sat = int((a[..., :3].max(-1).astype(int) - a[..., :3].min(-1).astype(int)).max())
    if sat > 16:
        return 'max saturation %d > 16' % sat
    return None

# =================================================================== E. CONTENT ICONS - shared svg bits
def F(d):
    return '<path d="%s" fill="#fff"/>' % d


def ST(d, w, cap='round', join='round'):
    return '<path d="%s" fill="none" stroke="#fff" stroke-width="%.2f" stroke-linecap="%s" stroke-linejoin="%s"/>' % (d, w, cap, join)


def CI(cx, cy, r):
    return '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="#fff"/>' % (cx, cy, r)


def RING(cx, cy, r, w):
    return '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="none" stroke="#fff" stroke-width="%.2f"/>' % (cx, cy, r, w)


def EL(cx, cy, rx, ry, ang=0.0):
    return '<ellipse cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f" transform="rotate(%.2f %.2f %.2f)" fill="#fff"/>' % (cx, cy, rx, ry, ang, cx, cy)


def P(pts):
    return F(poly_d(pts))


def arc_d(cx, cy, r, a0, a1):
    """An svg arc path from angle a0 to a1 (degrees, screen space: 0 = +x, 90 = +y), sweeping positively."""
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return 'M%.2f,%.2f A%.2f,%.2f 0 %d,1 %.2f,%.2f' % (x0, y0, r, r, large, x1, y1)


def halo_of(cov, px):
    """Coverage grown by px (a separation ring around a shape that crosses another)."""
    k = int(round(px))
    grown = ndimage.grey_dilation(cov, size=(2 * k + 1, 2 * k + 1))
    return np.clip(grown - cov, 0.0, 1.0)

# ================================================================= E0. THE SAFE INSET (W3A, 2026-10-05)
# User 2026-10-05: "Small tweak on perk icons since they go out of the given space and overflow on some". Measured on
# the shipped set (tmp/wave3/W3A-perk-fit/LAND.md): every perk's tube halo ran OFF its 256 canvas (border alpha
# 64/255 - a lit square edge round each icon in its socket), and six symbols ran over their own shield: Stamin-Up's
# swirl 25 px past the tube's centreline, Wisp Tea's saucer 13, Death Perception's eye 4.5, Revive's arc 3, Speed
# Cola's lines and Double Tap's ring ON the tube. The power-up tokens had the same cut halo (30/255); Time Warp's
# arrows sat on the token's tube and Carpenter's boards and Free PaP's bolt crossed its inner hairline.
# ONE RULE for every icon that lives in a shield or a token, asserted by fit_problems() on every build_all():
#   1. THE FRAME keeps its shape, scaled about the canvas centre so its tube centreline sits MARGIN px inside the
#      canvas: the tube's halo fades out INSIDE the image (border alpha <= HALO_EDGE_MAX), so the icon has the same
#      clear margin in every slot it is drawn in - the HUD socket, the prompt card's well, the toast's well;
#   2. THE SYMBOL is drawn at ONE scale shared by its whole set (the row reads as one family) and placed as near
#      to where it was designed as it can be while its ink stays inside the SAFE polygon (the frame inset SAFE px,
#      clear of the inner hairline and the tube);
#   3. NO INK STROKE is drawn thinner than MIN_SW art px (the thinnest stroke the set shipped with, 1.4 px at the
#      HUD's 39 px), so a smaller symbol keeps its weight. Cut strokes (the dark gaps) scale normally.
HALO_EDGE_MAX = 4            # alpha /255 allowed on the outermost pixel ring of a shield / token (shipped: 64 / 30)
FIT_SEARCH = 40.0            # how far (art px) the fit may move a symbol off its designed position
FIT_STEP = 0.5


def scale_pts(pts, f, c=128.0):
    return [(c + (x - c) * f, c + (y - c) * f) for x, y in pts]


def halfplanes(pts):
    """(n_x, n_y, h) for each edge of a convex clockwise (y-down) polygon: p is inside iff n.p >= h for all."""
    out = []
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        out.append((nx, ny, nx * x0 + ny * y0))
    return np.array(out, dtype=np.float64)


def clearance(pts, W, H):
    """Per-pixel signed distance (art px, + inside) of each pixel CENTRE from the convex polygon's edges."""
    Y, X = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
    hp = halfplanes(pts)
    d = np.full((H, W), np.inf)
    for nx, ny, h in hp:
        d = np.minimum(d, X * nx + Y * ny - h)
    return d


def bump_strokes(svg, s, min_sw):
    """Rule 3: inside a <g> scaled by s every stroke renders s times thinner, so an ink stroke thinner than
    min_sw / s is widened to it (renders exactly min_sw art px)."""
    if not svg or not min_sw:
        return svg
    floor = min_sw / s

    def rep(m):
        w = float(m.group(1))
        return 'stroke-width="%.2f"' % (w if w >= floor else floor)
    return re.sub(r'stroke-width="([0-9.]+)"', rep, svg)


def place_svg(svg, fit):
    """The symbol's svg in its DESIGN frame, drawn at the fitted scale + position."""
    if not svg:
        return svg
    s = fit['s']
    tx, ty = fit['cx'] - s * fit['bx'], fit['cy'] - s * fit['by']
    return '<g transform="matrix(%.4f 0 0 %.4f %.3f %.3f)">%s</g>' % (s, s, tx, ty, svg)


def fit_symbol(ink_cov, safe, s, frame_f, c=128.0):
    """Place a symbol whose ink (coverage in its DESIGN frame, strokes already bumped for s) is drawn at scale s:
    its ink-bbox centre (bx, by) goes to the grid point nearest its designed position (scaled about the canvas
    centre with its frame, by frame_f) that keeps the ink's convex hull inside the convex SAFE polygon. The safe
    test is exact for a convex region: the ink fits iff every hull vertex does. Also reports s_max, the largest
    scale the symbol could take there (how much room is left). Raises if no position fits."""
    from scipy.spatial import ConvexHull
    ys, xs = np.nonzero(ink_cov > 0.5)
    corners = np.concatenate([np.stack([xs + dx, ys + dy], 1) for dx, dy in ((0, 0), (1, 0), (1, 1), (0, 1))]).astype(np.float64)
    hull = corners[ConvexHull(corners).vertices]
    bx = (hull[:, 0].min() + hull[:, 0].max()) / 2.0
    by = (hull[:, 1].min() + hull[:, 1].max()) / 2.0
    U = hull - [bx, by]
    hx, hy = c + (bx - c) * frame_f, c + (by - c) * frame_f
    hx, hy = round(hx * 2) / 2.0, round(hy * 2) / 2.0           # on the search grid, so the result is exact
    g = np.arange(-FIT_SEARCH, FIT_SEARCH + 1e-9, FIT_STEP)
    CX, CY = np.meshgrid(hx + g, hy + g)
    C = np.stack([CX.ravel(), CY.ravel()], 1)
    hp = halfplanes(safe)
    nC = C @ hp[:, :2].T - hp[:, 2]                              # >= 0: the centre itself is inside edge e
    nU = U @ hp[:, :2].T
    smax = np.full(len(C), np.inf)
    for e in range(len(hp)):
        neg = nU[:, e] < 0
        if neg.any():
            smax = np.minimum(smax, (nC[:, e][:, None] / (-nU[neg, e][None, :])).min(1))
    smax[(nC < 0).any(1)] = -1.0
    ok = smax >= s
    if not ok.any():
        raise SystemExit('r4: a symbol does not fit its frame at scale %.3f (best %.3f) - tighten its ornaments' % (s, smax.max()))
    d = np.hypot(C[:, 0] - hx, C[:, 1] - hy)
    d[~ok] = np.inf
    i = int(np.argmin(d))
    return dict(s=s, cx=float(C[i, 0]), cy=float(C[i, 1]), bx=float(bx), by=float(by), s_max=float(smax.max()),
                moved=float(d[i]))


def border_alpha(im):
    a = np.asarray(im)[..., 3]
    return int(max(a[0, :].max(), a[-1, :].max(), a[:, 0].max(), a[:, -1].max()))


FIT_LOG = {}                 # name -> the measured numbers (fit_problems / --fit-report)


def fit_problems(name, im, placed_ink, safe):
    """Rules 1 + 2 measured on what was actually drawn: the border ring's alpha, and the placed ink's worst
    clearance from the SAFE polygon (pixels with coverage > 0.5; -0.5 px allows the antialiased rim)."""
    out = []
    b = border_alpha(im)
    if b > HALO_EDGE_MAX:
        out.append('%s: the frame halo is cut by the canvas edge (border alpha %d > %d)' % (name, b, HALO_EDGE_MAX))
    worst = None
    if placed_ink is not None and (placed_ink > 0.5).any():
        H, W = placed_ink.shape
        worst = float(clearance(safe, W, H)[placed_ink > 0.5].min())
        if worst < -0.5:
            out.append('%s: the symbol ink crosses its safe area by %.1f px' % (name, -worst))
    FIT_LOG[name] = dict(border=b, clear=worst)
    return out

# =========================================================================== E1. THE NINE PERK SHIELDS
# The HUD draws each perk 26 x 26 canvas inside its socket (39 px at 1080p) and the prompt card shows it in the
# icon well (44 canvas, 66 px). Map 1 shipped flat coloured pentagons. Map 2: a black-glass CHAMFERED SHIELD
# (the round badge's pointed shape), a neon tube in the perk's identity hue, the CANONICAL SYMBOL as a white-hot
# neon glyph haloed in that hue, one accent part in the hue. The hue is the perk's own colour moved onto the
# city's neon (Widow's Wine's red/black -> a white silk tube with a magenta hourglass); strokes >= 16 art px so
# every symbol survives 39 px. JUGGERNOG STAYS RED (review 2026-10-04): in magenta its bullet read as a slash
# through the cross at HUD size, and red is the one perk colour every player reads at a glance. #FF3048 is a neon
# red, clear of Insta-Kill / Zombie Blood's magenta and Death Perception's orange.
# W3A (2026-10-05, section E0): the symbols below stay drawn in this 256 DESIGN frame (PK_SHAPE); perk_icon()
# draws the frame at PK_F and every symbol at PK_SYM inside PK_SAFE.
PK_SHAPE = [(48, 12), (208, 12), (244, 48), (244, 156), (128, 244), (12, 156), (12, 48)]
PK_MARGIN = 23               # tube centreline -> canvas edge (was 12: the halo was cut at 64/255)
PK_F = (128.0 - PK_MARGIN) / 116.0
PK_OUT = scale_pts(PK_SHAPE, PK_F)
PK_TUBE_W, PK_GLOW, PK_SPREAD = 8.0, 0.85, 0.30      # was 9 / 0.85 / 0.42: a tighter halo, same neon
PK_HAIR = 13                 # the inner hairline (was 16 in the bigger frame)
PK_SAFE_IN = 15              # the symbols' ink stays this far inside the tube centreline (11 px clear of the tube)
PK_SAFE = inset(PK_OUT, PK_SAFE_IN)
PK_SYM = 0.82                # ONE scale for all nine symbols (of their design size)
PK_MIN_SW = 9.0              # rule 3: the thinnest ink stroke the set shipped with (Widow's legs, the wisps)
PERK_HUE = {
    'jugg': '#FF3048', 'speed': '#2BFF88', 'revive': '#1FE5FF', 'staminup': '#FFB020', 'widows': '#E8E0FF',
    'deathperception': '#FF8A3D', 'doubletap': '#F5D742', 'phd': '#9A6BFF', 'wisptea': '#3D7BFF',
}


def pistol(cx, cy, ang, k=1.0):
    """A pistol side silhouette, muzzle toward +x before rotation, its slide centred on (cx, cy): slide with
    sights, a barrel step, an angled grip and a trigger guard. Returns the rotated polygons."""
    polys = [
        [(-58, -16), (-56, -21), (-47, -21), (-45, -16), (48, -16), (50, -21), (55, -21), (57, -16), (58, -16),
         (58, -11), (68, -11), (68, 2), (58, 2), (58, 5), (-58, 5)],                       # slide + sights + barrel
        [(-58, 5), (-27, 5), (-17, 52), (-45, 58)],                                       # grip
        [(-27, 5), (-2, 5), (-2, 9), (-8, 22), (-22, 24), (-24, 18), (-12, 16), (-8, 10), (-25, 10)],   # guard
    ]
    out = []
    for poly in polys:
        q = [(cx + x * k, cy + y * k) for x, y in poly]
        out.append(rot(q, ang, cx, cy))
    return out


def pistol_cuts(cx, cy, k=1.0):
    """The slide's rear serrations (read at 66 px in the prompt card's well)."""
    return ''.join(ST('M%.1f,%.1f L%.1f,%.1f' % (cx + x * k, cy - 12 * k, cx + x * k, cy + 1 * k), 3.2 * k, cap='butt')
                   for x in (-48, -41, -34))


def pistols_svg(polys):
    return ''.join(P(q) for q in polys)


def perk_symbol(key, W=256, H=256):
    """(white_svg, accent_svg, cut_svg or None, extra) for one perk."""
    if key == 'jugg':
        cross = [(106, 46), (150, 46), (150, 90), (194, 90), (194, 134), (150, 134), (150, 188), (106, 188), (106, 134),
                 (62, 134), (62, 90), (106, 90)]
        # the bullet across it, lower-left to upper-right
        ax, ay, bx, by = 84, 170, 170, 84
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        w = 15
        tipx, tipy = bx + ux * 20, by + uy * 20
        bul = [(ax + nx * w, ay + ny * w), (bx + nx * w, by + ny * w), (tipx, tipy), (bx - nx * w, by - ny * w), (ax - nx * w, ay - ny * w)]
        rim = [(ax - ux * 10 + nx * (w + 3), ay - uy * 10 + ny * (w + 3)), (ax + nx * (w + 3), ay + ny * (w + 3)),
               (ax - nx * (w + 3), ay - ny * (w + 3)), (ax - ux * 10 - nx * (w + 3), ay - uy * 10 - ny * (w + 3))]
        return P(cross), P(bul) + P(rim), None, dict(sep=P(bul) + P(rim))
    if key == 'speed':
        palm = [(96, 116), (170, 112), (174, 160), (156, 192), (110, 192), (92, 166)]
        fingers = ''.join(ST('M%d,%d L%d,%d' % f, 20) for f in ((106, 122, 98, 66), (126, 116, 124, 54), (146, 116, 152, 58), (164, 124, 180, 80)))
        thumb = ST('M100,152 L72,124', 20)
        lines = ''.join(ST('M%d,%d L%d,%d' % l, 10) for l in ((26, 86, 72, 86), (20, 112, 60, 112), (30, 138, 58, 138)))
        return P(palm) + fingers + thumb, lines, None, {}
    if key == 'revive':
        fig = (CI(140, 66, 18) + P([(116, 92), (164, 92), (156, 150), (124, 150)])
               + ST('M128,150 L120,198', 20) + ST('M150,150 L158,198', 20)
               + ST('M118,100 L96,132', 16) + ST('M162,100 L184,126', 16))
        # W3A: the arc's radius 86 -> 78 about (126, 128) - it ran 3 px over the shield's left tube
        arc = ST(arc_d(126, 128, 78, 115, 250), 12, cap='butt')
        a = math.radians(250)
        ex, ey = 126 + 78 * math.cos(a), 128 + 78 * math.sin(a)
        head = P([(ex + 24, ey + 4), (ex - 6, ey - 20), (ex - 10, ey + 18)])
        return fig, arc + head, None, {}
    if key == 'staminup':
        fig = (CI(158, 60, 17) + ST('M148,84 L120,134', 26)
               + ST('M142,96 L168,114 L188,98', 16) + ST('M136,98 L110,104 L96,124', 16)
               + ST('M122,132 L150,156 L144,194', 18) + ST('M118,136 L94,158 L64,150', 18))
        # W3A: the speed streaks were 168 wide across the shield's V (25 px over its tube); now 124 / 80 wide
        swirl = ST('M70,204 Q130,218 194,198', 10) + ST('M84,186 Q122,196 164,184', 8)
        return fig, swirl, None, {}
    if key == 'widows':
        legs = ''
        for sx in (-1, 1):
            for pts in (((110, 84), (72, 56), (60, 28)), ((108, 92), (64, 80), (38, 92)),
                        ((108, 102), (66, 114), (44, 142)), ((110, 110), (80, 142), (72, 180))):
                q = [(128 + (x - 128) * sx, y) for x, y in pts]
                legs += ST('M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f' % (q[0] + q[1] + q[2]), 9)
        body = EL(128, 148, 32, 42) + EL(128, 92, 22, 20) + CI(128, 70, 11)
        glass = P([(114, 124), (142, 124), (128, 146)]) + P([(128, 146), (114, 170), (142, 170)])
        return body + legs, glass, None, {}
    if key == 'deathperception':
        eye = ST('M38,120 Q128,34 218,120 Q128,206 38,120 Z', 14)
        iris = CI(128, 120, 36)
        pupil = EL(128, 120, 9, 27)
        rays = ''.join(ST('M%.1f,%.1f L%.1f,%.1f' % (128 + 76 * math.cos(math.radians(a)), 112 + 76 * math.sin(math.radians(a)),
                                                    128 + 100 * math.cos(math.radians(a)), 112 + 100 * math.sin(math.radians(a))), 10)
                       for a in (-150, -120, -90, -60, -30))
        return eye + iris, rays, pupil, {}
    if key == 'doubletap':
        # TWO pistols (Map 1's crossed pair read as a knot at 39 px): side views, muzzles right, one above
        # the other, over the target ring - "two guns" survives any size
        a = pistol(144, 82, 0, 0.9)
        b = pistol(122, 146, 0, 0.9)
        # W3A: the target ring r 92 -> 84 and its ticks r 80..104 -> 72..96 (it sat ON the shield's tube)
        ring = RING(128, 120, 84, 8) + ST('M128,24 L128,48 M128,192 L128,216 M32,120 L56,120 M200,120 L224,120', 8, cap='butt')
        return (pistols_svg(a) + pistols_svg(b), ring, pistol_cuts(144, 82, 0.9) + pistol_cuts(122, 146, 0.9),
                dict(over=pistols_svg(b)))
    if key == 'phd':
        blades = ''
        for c in (-90, 30, 150):
            a0, a1 = math.radians(c - 30), math.radians(c + 30)
            r0, r1 = 28, 72
            blades += F('M%.2f,%.2f L%.2f,%.2f A%d,%d 0 0,1 %.2f,%.2f L%.2f,%.2f A%d,%d 0 0,0 %.2f,%.2f Z' % (
                128 + r0 * math.cos(a0), 120 + r0 * math.sin(a0), 128 + r1 * math.cos(a0), 120 + r1 * math.sin(a0), r1, r1,
                128 + r1 * math.cos(a1), 120 + r1 * math.sin(a1), 128 + r0 * math.cos(a1), 120 + r0 * math.sin(a1), r0, r0,
                128 + r0 * math.cos(a0), 120 + r0 * math.sin(a0)))
        arcs = ''.join(ST(arc_d(128, 120, 92, c - 24, c + 24), 10, cap='butt') for c in (-30, 90, 210))
        return blades + CI(128, 120, 16), arcs, None, {}
    if key == 'wisptea':
        # W3A: the saucer 160 -> 116 wide (it ran 13 px past the tube across the shield's V) and the wisps rise
        # 0.8 as high (the tallest symbol in the set: it could not fit the frame at the set's scale)
        cup = F('M68,124 L188,124 Q184,184 152,190 L104,190 Q72,184 68,124 Z') + F('M70,196 L186,196 L177,209 L79,209 Z')
        handle = RING(190, 148, 17, 10)

        def wy(d):                    # the wisps' y scaled 0.8 toward their foot at y 114
            return re.sub(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)',
                          lambda m: '%s,%.1f' % (m.group(1), 114 + (float(m.group(2)) - 114) * 0.8), d)
        wisps = (ST(wy('M102,114 C 86,94 120,86 104,62 C 96,50 106,40 112,34'), 9)
                 + ST(wy('M130,114 C 114,90 148,80 130,52 C 122,40 132,30 138,24'), 9)
                 + ST(wy('M158,114 C 172,94 142,84 158,62'), 9))
        return cup + handle, wisps, None, {}
    raise KeyError(key)


def perk_fit(key):
    """Section E0 rules 2 + 3 for one perk: (white, accent, cut, extra) placed in the PK_F frame, and the fit."""
    white, acc, cut, extra = perk_symbol(key)
    white, acc = bump_strokes(white, PK_SYM, PK_MIN_SW), bump_strokes(acc, PK_SYM, PK_MIN_SW)
    extra = {k: (bump_strokes(v, PK_SYM, PK_MIN_SW) if isinstance(v, str) else v) for k, v in extra.items()}
    fit = fit_symbol(coverage(256, 256, white + acc), PK_SAFE, PK_SYM, PK_F)
    extra = {k: (place_svg(v, fit) if isinstance(v, str) else v) for k, v in extra.items()}
    return place_svg(white, fit), place_svg(acc, fit), (place_svg(cut, fit) if cut else None), extra, fit


def perk_icon(key, problems=None):
    W = H = 256
    hue = PERK_HUE[key]

    def base(s):
        s.plate(PK_OUT, 'token', top=mix(hue, 'token', 0.80))
        s.path(poly_d(PK_OUT), fill='url(#%s)' % s.rad([(0, hue, 0.16), (1, hue, 0.0)], 0.5, 0.18, 0.6))
        s.steel(PK_OUT, 2.0)
        s.path(poly_d(inset(PK_OUT, PK_HAIR)), stroke=mix(hue, 'steel', 0.55), sw=2.0, opacity=0.55)

    def top(s):
        s.tube(poly_d(PK_OUT), hue, PK_TUBE_W, glow=PK_GLOW, spread=PK_SPREAD)

    im = layered(W, H, base, top, grain_amp=0.02, seed=600 + len(key), base_alpha=1.0)
    white, acc, cut, extra, fit = perk_fit(key)
    wc, ac = coverage(W, H, white), coverage(W, H, acc)
    ink = np.clip(wc + ac, 0, 1)
    cc = coverage(W, H, cut) if cut else None
    if extra.get('sep'):                        # a dark gap round the accent where it crosses the white ink
        sep = halo_of(coverage(W, H, extra['sep']), 6)
        wc = wc * (1.0 - sep)
    if extra.get('over'):                       # the second pistol crosses OVER the first
        oc = coverage(W, H, extra['over'])
        first = np.clip(wc - oc, 0, 1)
        wc = np.clip(first * (1.0 - halo_of(oc, 6)) + oc, 0, 1)
    im.alpha_composite(neon_glyph(wc, ac, hue, sigma=7.0, k=0.8, cut_cov=cc, acc_lift=0.22))
    found = fit_problems('i_tod_perk_' + key, im, ink, PK_SAFE)
    FIT_LOG['i_tod_perk_' + key].update(s_max=fit['s_max'], moved=fit['moved'])
    if problems is not None:
        problems.extend(found)
    elif found:
        raise SystemExit('r4: ' + '; '.join(found))
    return im

# ========================================================================= E2. THE ELEVEN POWER-UP TOKENS
# AetheriumPowerupsContainer.lua draws each at 49 x 49 canvas (73 px at 1080p) with no plate of its own, and the
# toast shows one in its octagonal well. Map 1 shipped glossy cartoon objects. Map 2: an octagonal black-glass
# TOKEN with a neon tube in the power-up's hue and the SAME SUBJECT as a white-hot neon glyph (one accent part
# in the hue). Drawn at 256; the three 128 x 128 files are the same art downsampled.
# W3A (2026-10-05, section E0): the subjects stay drawn in the 256 DESIGN frame (PU_SHAPE); powerup_icon() draws
# the token at PU_F and every subject at PU_SYM inside PU_SAFE. The toast draws the token EXACTLY over its own
# cyan well tube (AetheriumPowerupNotification.lua icon 537..580 = TO_WELL), so the token's halo no longer runs
# into that tube either.
PU_SHAPE = octagon(16, 16, 240, 240, 54)
PU_MARGIN = 23               # tube centreline -> canvas edge (was 16: the halo was cut at 30/255)
PU_F = (128.0 - PU_MARGIN) / 112.0
PU_OUT = scale_pts(PU_SHAPE, PU_F)
PU_TUBE_W, PU_GLOW, PU_SPREAD = 8.0, 0.85, 0.30      # was 8 / 0.85 / 0.42
PU_HAIR = 13                 # the inner hairline (was 14)
PU_SAFE_IN = 15              # the subjects' ink stays this far inside the tube centreline
PU_SAFE = inset(PU_OUT, PU_SAFE_IN)
PU_SYM = 0.88                # ONE scale for all eleven subjects (of their design size)
PU_MIN_SW = 9.0              # rule 3: the thinnest ink stroke the set shipped with (Time Warp's glass and arrows)
# RT (2026-10-05): each power-up's hue is its IDENTITY (like PERK_HUE): synthwave.py's id_* roles keep the hex it shipped with in every theme, so the
# switch never recolours a power-up; only its token's glass and hairline follow the theme.
PU = {   # name: (size, hue)
    'i_tod_pu2_insta': (256, 'pu_insta'), 'i_tod_pu2_double_points': (256, 'id_gold'), 'i_tod_pu2_fire_sale': (128, 'id_sunset'),
    'i_tod_pu2_gift_of_death': (256, 'pu_gift'), 'i_tod_pu2_max_ammo': (256, 'pu_ammo'), 'i_tod_pu2_carpenter': (128, 'pu_carpenter'),
    'i_tod_pu2_nuke': (256, 'id_sunset'), 'i_tod_pu2_timewarp': (256, 'pu_timewarp'), 'i_tod_pu2_infinite_ammo': (256, 'pu_ammo'),
    'i_tod_pu2_zombie_blood': (256, 'pu_blood'), 'i_tod_pu2_free_pap': (128, 'pu_pap'),
}
# RT review (2026-10-05): the hues above that R4 took from its own synthwave palette (magenta / cyan / violet) are THEME
# roles (pu_*): the red era drew Zombie Blood red, the ammo brass, Carpenter wood, Free PaP gold, Time Warp cold and
# Insta-Kill a white skull. Double Points (gold), Fire Sale and the Nuke (fire) are the same in every theme (id_*).
PU_ACC = {'i_tod_pu2_insta': 'pu_insta_eye'}      # an accent ink that is not the token's hue (Insta-Kill's eyes)


def skull_parts(cx, cy, k=1.0, angry=True):
    """A bold skull: (white, cut, accent) svg bodies. Map 2's zombie face: angry sockets, magenta slit eyes."""
    T = lambda x, y: (cx + x * k, cy + y * k)
    white = (CI(*T(0, -20), 54 * k) + P([T(-34, 14), T(34, 14), T(30, 58), T(-30, 58)])
             + P([T(-50, -10), T(50, -10), T(40, 26), T(-40, 26)]))
    sock = [T(-40, -18), T(-8, -6), T(-12, 16), T(-36, 12)]
    sockR = [(2 * cx - x, y) for x, y in sock]
    nose = [T(0, 18), T(-8, 32), T(8, 32)]
    teeth = ''.join(ST('M%.1f,%.1f L%.1f,%.1f' % (T(x, 38) + T(x, 60)), 5 * k, cap='butt') for x in (-16, 0, 16))
    cut = P(sock) + P(sockR) + P(nose) + teeth
    slitL = [T(-34, -10), T(-14, -3), T(-16, 3), T(-34, 0)]
    slitR = [(2 * cx - x, y) for x, y in slitL]
    acc = P(slitL) + P(slitR) if angry else ''
    return white, cut, acc


def powerup_symbol(name):
    """(white, accent, cut, extra) in the 256 token."""
    if name == 'i_tod_pu2_insta':
        w, c, a = skull_parts(128, 130, 1.25)
        return w, a, c, {}
    if name == 'i_tod_pu2_double_points':
        return '', '', None, dict(text='X2')
    if name == 'i_tod_pu2_fire_sale':
        tag = rot([(62, 108), (150, 108), (192, 138), (150, 168), (62, 168)], -18, 128, 138)
        hole = CI(*rot([(160, 138)], -18, 128, 138)[0], 10)
        stripe = ST(poly_d(rot([(78, 128), (132, 128)], -18, 128, 138), close=False), 8, cap='butt') + \
            ST(poly_d(rot([(78, 148), (120, 148)], -18, 128, 138), close=False), 8, cap='butt')
        flames = ''.join(F('M%.1f,%.1f C %.1f,%.1f %.1f,%.1f %.1f,%.1f C %.1f,%.1f %.1f,%.1f %.1f,%.1f Z' % (
            x, y, x - 14, y - 16, x - 4, y - 30 - h, x, y - 40 - h, x + 6, y - 28 - h, x + 16, y - 14, x, y))
            for x, y, h in ((96, 104, 2), (130, 90, 12), (164, 104, 0)))
        return P(tag), flames, hole + stripe, {}
    if name == 'i_tod_pu2_gift_of_death':
        box = P(chamfer(72, 118, 184, 196, bl=6, br=6)) + P(chamfer(62, 96, 194, 120))
        bow = EL(104, 82, 26, 13, -24) + EL(152, 82, 26, 13, 24) + CI(128, 90, 10)
        ribbon = P([(120, 96), (136, 96), (136, 120), (120, 120)])
        sk = CI(128, 150, 20) + P([(116, 160), (140, 160), (136, 182), (120, 182)])
        eyes = CI(120, 150, 6) + CI(136, 150, 6)
        return box, bow + ribbon, None, dict(skull=sk, eyes=eyes)
    if name == 'i_tod_pu2_max_ammo':
        crate = P(chamfer(64, 126, 192, 196, tl=6, tr=6))
        slats = ST('M72,150 L184,150 M72,172 L184,172', 6, cap='butt')
        bullets, tips = '', ''
        for x in (94, 128, 162):
            bullets += P([(x - 13, 124), (x + 13, 124), (x + 13, 84), (x - 13, 84)])
            tips += F('M%d,84 L%d,84 Q%d,58 %d,52 Q%d,58 %d,84 Z' % (x - 13, x + 13, x + 12, x, x - 12, x - 13))
        return crate + bullets, tips, slats + ST('M%d,124 L%d,124' % (68, 188), 6, cap='butt'), {}
    if name == 'i_tod_pu2_carpenter':
        boards = P(rot([(56, 150), (200, 150), (200, 176), (56, 176)], -12, 128, 163)) + \
            P(rot([(70, 182), (196, 182), (196, 204), (70, 204)], 8, 133, 193))
        # a claw hammer: a long handle and a broad head with its claw split (reads as a hammer at 73 px)
        hammer = P(rot([(119, 72), (137, 72), (139, 182), (117, 182)], 32, 128, 116)) + \
            P(rot([(76, 44), (96, 38), (182, 38), (182, 78), (96, 78), (76, 72)], 32, 128, 116))
        claw = ST(poly_d(rot([(70, 58), (98, 58)], 32, 128, 116), close=False), 7, cap='butt')
        return hammer, boards, claw, dict(gap_acc=hammer)
    if name == 'i_tod_pu2_nuke':
        cap = CI(96, 96, 30) + CI(128, 80, 36) + CI(160, 96, 30) + P(chamfer(66, 92, 190, 122, bl=10, br=10))
        stem = P([(114, 120), (142, 120), (148, 178), (108, 178)])
        base = EL(128, 188, 64, 14)
        ring = ST('M100,148 L156,148', 8, cap='butt')
        return cap + stem, base, ring, {}
    if name == 'i_tod_pu2_timewarp':
        frame = P(chamfer(80, 58, 176, 72, tl=4, tr=4)) + P(chamfer(80, 184, 176, 198, bl=4, br=4))
        glass = ST('M92,72 L164,72 L128,128 L164,184 L92,184 L128,128 Z', 9, join='miter')
        sand = P([(112, 184), (144, 184), (128, 160)]) + P([(108, 84), (148, 84), (128, 112)])
        # W3A: the turn arrows r 96 -> 90 (they ran onto the token's tube; 90 still clears the hourglass corners)
        arcs = ST(arc_d(128, 128, 90, 200, 262), 9, cap='butt') + ST(arc_d(128, 128, 90, 20, 82), 9, cap='butt')
        a1 = math.radians(262)
        a2 = math.radians(82)
        h1 = (128 + 90 * math.cos(a1), 128 + 90 * math.sin(a1))
        h2 = (128 + 90 * math.cos(a2), 128 + 90 * math.sin(a2))
        heads = P([(h1[0] + 18, h1[1] + 2), (h1[0] - 4, h1[1] - 14), (h1[0] - 4, h1[1] + 16)]) + \
            P([(h2[0] - 18, h2[1] - 2), (h2[0] + 4, h2[1] + 14), (h2[0] + 4, h2[1] - 16)])
        return frame + glass, sand + arcs + heads, None, {}
    if name == 'i_tod_pu2_infinite_ammo':
        inf = ST('M128,112 C 104,76 56,80 56,112 C 56,144 104,148 128,112 C 152,76 200,80 200,112 C 200,144 152,148 128,112 Z', 20)
        bullet = P([(84, 166), (150, 166), (150, 190), (84, 190)]) + F('M150,166 Q176,168 188,178 Q176,188 150,190 Z')
        rim = P([(76, 162), (86, 162), (86, 194), (76, 194)])
        return inf + rim, bullet, None, {}
    if name == 'i_tod_pu2_zombie_blood':
        drop = F('M128,48 C 150,92 190,122 190,156 A62,62 0 0,1 66,156 C 66,122 106,92 128,48 Z')
        eye = F('M92,158 Q128,124 164,158 Q128,192 92,158 Z')
        pupil = CI(128, 158, 11)
        return eye, drop, pupil, dict(eye_over_drop=True)
    if name == 'i_tod_pu2_free_pap':
        wrench = (P(rot([(118, 92), (138, 92), (138, 200), (118, 200)], -40, 128, 146))
                  + CI(*rot([(128, 86)], -40, 128, 146)[0], 32))
        jaw = P(rot([(116, 50), (140, 50), (140, 88), (116, 88)], -40, 128, 146))
        bolt = P([(176, 52), (150, 116), (172, 116), (150, 186), (204, 100), (180, 100), (204, 52)])
        return wrench, bolt, jaw, dict(gap_white=bolt)
    raise KeyError(name)


PU_TEXT = dict(cap=104, baseline=176, cx=128, track=0.04, glow_r=10)     # Double Points' X2, in the design frame


def text_face_cov(text, cap, baseline, cx, track, W=256, H=256):
    """The typeface's FACE (no glow) as coverage - what the fit and the gate measure for a lettered subject."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    put_text(layer, text, cap, baseline, 'white', cx=cx, track=track)
    return np.asarray(layer, dtype=np.float64)[..., 3] / 255.0


def powerup_fit(name):
    """Section E0 rules 2 + 3 for one power-up: (white, accent, cut, extra) placed in the PU_F frame, and the fit.
    A lettered subject (extra['text']) is fitted on its typeface face and drawn by neon_word at the fitted cap."""
    white, acc, cut, extra = powerup_symbol(name)
    if extra.get('text'):
        t = PU_TEXT
        fit = fit_symbol(text_face_cov(extra['text'], t['cap'], t['baseline'], t['cx'], t['track']), PU_SAFE, PU_SYM, PU_F)
        s = fit['s']
        extra = dict(extra, text_at=dict(cap=t['cap'] * s, baseline=fit['cy'] + s * (t['baseline'] - fit['by']),
                                         cx=fit['cx'] + s * (t['cx'] - fit['bx']), track=t['track'], glow_r=t['glow_r'] * s))
        return white, acc, cut, extra, fit
    white, acc = bump_strokes(white, PU_SYM, PU_MIN_SW), bump_strokes(acc, PU_SYM, PU_MIN_SW)
    fit = fit_symbol(coverage(256, 256, white + acc), PU_SAFE, PU_SYM, PU_F)
    extra = {k: (place_svg(v, fit) if isinstance(v, str) else v) for k, v in extra.items()}
    return place_svg(white, fit), place_svg(acc, fit), (place_svg(cut, fit) if cut else None), extra, fit


def powerup_icon(name, problems=None):
    size, hue = PU[name]
    W = H = 256

    def base(s):
        s.plate(PU_OUT, 'token', top=mix(hue, 'token', 0.82))
        s.path(poly_d(PU_OUT), fill='url(#%s)' % s.rad([(0, hue, 0.14), (1, hue, 0.0)], 0.5, 0.3, 0.6))
        s.steel(PU_OUT, 2.0)
        s.path(poly_d(inset(PU_OUT, PU_HAIR)), stroke=mix(hue, 'steel', 0.55), sw=2.0, opacity=0.5)

    def top(s):
        s.tube(poly_d(PU_OUT), hue, PU_TUBE_W, glow=PU_GLOW, spread=PU_SPREAD)

    im = layered(W, H, base, top, grain_amp=0.02, seed=700 + len(name), base_alpha=0.94)
    white, acc, cut, extra, fit = powerup_fit(name)
    if extra.get('text'):
        t = extra['text_at']
        neon_word(im, extra['text'], t['cap'], t['baseline'], hue, cx=t['cx'], track=t['track'], glow_r=t['glow_r'], glow_k=0.9)
        ink = text_face_cov(extra['text'], t['cap'], t['baseline'], t['cx'], t['track'])
    else:
        wc, ac = coverage(W, H, white), coverage(W, H, acc)
        ink = np.clip(wc + ac, 0, 1)
        cc = coverage(W, H, cut) if cut else None
        if extra.get('gap_acc'):                # a dark gap in the ACCENT round a white part crossing it
            ac = ac * (1.0 - halo_of(coverage(W, H, extra['gap_acc']), 6))
        if extra.get('gap_white'):              # a dark gap in the WHITE ink round an accent part crossing it
            wc = wc * (1.0 - halo_of(coverage(W, H, extra['gap_white']), 6))
        if extra.get('skull'):                  # the gift's skull: a dark skull cut into the box, white eye-less sockets
            sk = coverage(W, H, extra['skull'])
            eyes = coverage(W, H, extra['eyes'])
            cc = np.clip(sk - eyes, 0, 1)
            acc_eyes = eyes
            ac = np.clip(ac + acc_eyes, 0, 1)
            wc = wc * (1.0 - sk)
        if extra.get('eye_over_drop'):          # the eye sits ON the drop: white over the accent
            ac = ac * (1.0 - wc)
        im.alpha_composite(neon_glyph(wc, ac, hue, acc=PU_ACC.get(name), sigma=7.0, k=0.8, cut_cov=cc, acc_lift=0.22))
    found = fit_problems(name, im, ink, PU_SAFE)              # the symbol, measured on the 256 drawing
    if size != 256:
        im = im.resize((size, size), Image.LANCZOS)
        b = border_alpha(im)                                  # ... and the halo, on the file that ships
        FIT_LOG[name]['border'] = max(FIT_LOG[name]['border'], b)
        if b > HALO_EDGE_MAX:
            found.append('%s: the frame halo is cut by the canvas edge (border alpha %d > %d)' % (name, b, HALO_EDGE_MAX))
    FIT_LOG[name].update(s_max=fit['s_max'], moved=fit['moved'])
    if problems is not None:
        problems.extend(found)
    elif found:
        raise SystemExit('r4: ' + '; '.join(found))
    return im

# =========================================================================== E3. THE PACK-A-PUNCH GLYPH
# AetheriumLoadout.lua draws i_tod_hud_pap_1 at 26 x 26 canvas (39 px) inside i_tod_h2_tile_pap (violet). Only tier 1
# is ever sent now (_tod_classes pap_tier_set; i_tod_hud_pap_2 / _3 are dead and R5 purges them). docs/131's rules
# stand: saturated ink, a strong silhouette, NO numeral (the game draws the level digit beside it). Map 1's flat
# cyan chevron becomes a neon GLASS chevron: cyan, white-hot along its leading edge, haloed.
PAP_HUE = '#1FE5FF'


def chevron_pts(cx, cy, w, h, t):
    return [(cx - w, cy + h / 2), (cx, cy - h / 2), (cx + w, cy + h / 2), (cx + w, cy + h / 2 + t), (cx, cy - h / 2 + t),
            (cx - w, cy + h / 2 + t)]


def pap_icon():
    W = H = 128
    hue = PAP_HUE
    s = Svg(W, H)
    w, h, t = 46, 40, 24
    p = chevron_pts(64, 52, w, h, t)
    s.path(poly_d(p), fill=hue, opacity=0.75, filt=s.blur(4.5, (18, 32, 110, 96)))
    s.path(poly_d(p), fill='url(#%s)' % s.lin([(0, mix(hue, '#FFFFFF', 0.75), 1), (0.5, mix(hue, '#FFFFFF', 0.25), 1), (1, hue, 1)]))
    s.path(poly_d(p), stroke=mix(hue, '#000000', 0.25), sw=2.0)
    s.path(line_d(p[0], p[1], p[2]), stroke='#FFFFFF', sw=2.4, opacity=0.95)
    return s.render(ss=4)


# ===================================================================================== the manifest
PERK_KEYS = ['jugg', 'speed', 'revive', 'staminup', 'widows', 'deathperception', 'doubletap', 'phd', 'wisptea']
ICON13 = sorted(ICON_SRC_MD5)
PK07_NAMES = ['i_tod_prompt_icon_black_market', 'i_tod_prompt_icon_arena']
ARENA = ['i_tod_h2_arena_badge', 'i_tod_h2_arena_badge_rampage']

# (name, builder, on-screen size at 1080p = the Lua's canvas rect x 1.5, section)
IMAGES = [
    ('i_tod_h2_round_badge', lambda: round_badge(False), (108, 108), 'HUD'),
    ('i_tod_h2_round_badge_rampage', lambda: round_badge(True), (108, 108), 'HUD'),
    ('i_tod_h2_arena_badge', None, (108, 108), 'HUD'),            # made by make_badge.py from the two above
    ('i_tod_h2_arena_badge_rampage', None, (108, 108), 'HUD'),
    ('i_tod_h2_luck_plate', lambda: luck_plate(False), (354, 90), 'HUD'),
    ('i_tod_h2_luck_plate_rampage', lambda: luck_plate(True), (354, 90), 'HUD'),
    ('i_tod_h2_luck_on', lambda: luck_seg(True), (29, 18), 'HUD'),
    ('i_tod_h2_luck_off', lambda: luck_seg(False), (29, 18), 'HUD'),
    ('i_tod_h2_gun_plate', gun_plate, (396, 108), 'HUD'),
    ('i_tod_h2_tile', lambda: tile('normal'), (69, 48), 'HUD'),
    ('i_tod_h2_tile_ready', lambda: tile('ready'), (69, 48), 'HUD'),
    ('i_tod_h2_tile_pap', lambda: tile('pap'), (69, 48), 'HUD'),
    ('i_tod_h2_hp_frame', hp_frame, (195, 18), 'HUD'),
    ('i_tod_h2_medallion_ring', medallion_ring, (84, 84), 'HUD'),
    ('i_tod_h2_perk_socket', perk_socket, (48, 48), 'HUD'),
    ('i_tod_h2_points', points_glyph, (24, 24), 'HUD'),
    ('i_tod_h2_toast', toast, (318, 74), 'HUD'),
    ('i_tod_h2_gauge_tower', gauge_tower, (48, 675), 'HUD'),
    ('i_tod_h2_gauge_seg_off', gauge_seg_off, (21, 13), 'HUD'),
    ('i_tod_h2_gauge_you', gauge_you, (18, 18), 'HUD'),
    ('i_tod_h2_gauge_down', gauge_down, (18, 18), 'HUD'),
    ('i_tod_prompt_chassis', lambda: chassis('normal'), (346, 114), 'PROMPT'),
    ('i_tod_prompt_chassis_wide', lambda: chassis('wide'), (450, 114), 'PROMPT'),
    ('i_tod_prompt_chassis_locked', lambda: chassis('locked'), (346, 114), 'PROMPT'),
] + [(n, (lambda n=n: recolor_icon(n)), (66, 66), 'PROMPT') for n in ICON13] + [
    (n, None, (66, 66), 'PROMPT') for n in PK07_NAMES                       # made by the (staged) PK07 generator
] + [('i_tod_badge_luck_%d' % p, (lambda p=p: luck_badge(p)), (420, 90), 'DEAL') for p in range(10, 101, 10)] + [
    ('i_tod_luck_legend', luck_legend, (420, 90), 'DEAL'),
    ('i_tod_hud_health_fill', health_fill, (390, 30), 'SLAB'),
] + [('i_tod_perk_%s' % k, (lambda k=k: perk_icon(k)), (39, 39), 'PERKS') for k in PERK_KEYS] + [
    (n, (lambda n=n: powerup_icon(n)), (73, 73), 'POWER-UPS') for n in PU
] + [('i_tod_hud_pap_1', pap_icon, (39, 39), 'PAP')]      # 2 / 3 are dead (only tier 1 is sent) - R5 purges them

# uncompressed in the GDT (the deal panel's 420 x 90 plates), so the multiple-of-4 rule does not bind them
UNCOMPRESSED_ANY_SIZE = {'i_tod_badge_luck_%d' % p for p in range(10, 101, 10)} | {'i_tod_luck_legend'}

# THE CODE HALF (docs/184 "Code tints"; RT 2026-10-05): the round number on the badge is painted in the THEME's accent -
# the Fallen red or the synthwave magenta. The theme's line must be in tod_upgrade.lua and the other theme's must not
# (R4's original gate, "the round still paints red", is the synthwave half and the negative control below).
ROUND2_TINT = {'fallen': 'Round2Row.setRGB( 0.98, 0.11, 0.22 )', 'synthwave': 'Round2Row.setRGB( 1.00, 0.17, 0.82 )'}
# PK07's arena icon takes the theme's accent from synthwave.THEME (the Dealer's red X eyes never change)
PK07_THEME_LINES = ["ARENA_ACCENT, ARENA_GLOW = (MAGENTA, MAGENTA_GLOW) if THEME == 'synthwave' else (RED, RED_GLOW)",
                    'ring, ARENA_ACCENT, ARENA_GLOW)', 'from synthwave import THEME']


def round2_problems(src, theme=None):
    theme = theme or THEME
    out = []
    if ROUND2_TINT[theme] not in src:
        out.append('tod_upgrade.lua: the %s Round2Row tint is missing (%s)' % (theme, ROUND2_TINT[theme]))
    for other, line in ROUND2_TINT.items():
        if other != theme and line in src:
            out.append('tod_upgrade.lua still paints the round number in the %s theme (%s)' % (other, line))
    return out


def round2_selftest(src):
    """the negative control: the other theme's tint planted in place of this theme's must be caught"""
    if round2_problems(src):
        return []
    other = [t for t in ROUND2_TINT if t != THEME][0]
    planted = src.replace(ROUND2_TINT[THEME], ROUND2_TINT[other])
    return [] if round2_problems(planted) else ['the %s Round2Row tint planted in tod_upgrade.lua was NOT caught' % other]


def build_all(pk07_path):
    """Every deliverable -> (RGBA image, the exact bytes the landing installs)."""
    out = {}
    for name, fn, _, _ in IMAGES:
        if fn is None:
            continue
        im = fn().convert('RGBA')
        ref = Image.open(artgen.shipped(name))       # RT: the shipped size (was BASE_IMG: tmp/ is gitignored)
        if im.size != ref.size:
            raise SystemExit('r4: %s is %s, the shipped image is %s - a drop-in keeps its size' % (name, im.size, ref.size))
        if name not in UNCOMPRESSED_ANY_SIZE and (im.width % 4 or im.height % 4):
            raise SystemExit('r4: %s %s is not a multiple of 4' % (name, im.size))
        out[name] = (im, artgen.png_bytes(im))
    bad = slab_contract(out['i_tod_hud_health_fill'][0])
    if bad:
        raise SystemExit('r4: i_tod_hud_health_fill breaks the slab contract: %s' % bad)
    for name, (im, data) in arena_badges({n: out[n][0] for n in ('i_tod_h2_round_badge', 'i_tod_h2_round_badge_rampage')}).items():
        out[name] = (im, data)
    pk = pk07_icons(pk07_path)
    for name in PK07_NAMES:
        out[name] = (pk[name], artgen.png_bytes(pk[name]))
    return out

# ================================================================= the safe-inset report + negative controls (W3A)
# Every slot that draws a shield / token, from the Lua that draws it (canvas units, 1.5 px each at 1080p):
#   (label, which set, the slot's inner edge = the frame line the icon must stay inside, the icon's draw box)
FIT_SLOTS = [
    ('HUD perk socket (AetheriumPerkItem.lua: socket 0..32, perk 3..29)', 'perk', (1.225, 1.225, 30.775, 30.775), (3, 3, 29, 29)),
    ('prompt card well (TodPromptCard.lua BOX.icon 559..603 x 461..505)', 'perk', (547.275, 447.275, 613.725, 516.725), (559, 461, 603, 505)),
    ('power-up row (AetheriumPowerupItem.lua 49 x 49, no plate)', 'pu', (0, 0, 49, 49), (0, 0, 49, 49)),
    ('power-up toast well (AetheriumPowerupNotification.lua 537..580 x 515..558)', 'pu', (537.25, 515.25, 579.75, 557.75), (537, 515, 580, 558)),
    ('PaP tile (AetheriumLoadout.lua tile PAP_X+0..46 x 568..600, glyph +4..30 x 571..597)', 'pap', (1.55, 1.55, 44.45, 30.45), (4, 3, 30, 29)),
]


def fit_report(built):
    """The numbers behind section E0, from the images build_all() just drew: per icon the border alpha, the
    symbol's clearance from its safe polygon and the room left (s_max / the set's scale); per slot the clear
    margin between the slot's frame line and the icon's frame (alpha >= 128) and its halo (alpha >= 8), in px at
    1080p, worst over the set."""
    print('safe inset: perks frame %.3f, symbols %.2f in %d px; power-ups frame %.3f, subjects %.2f in %d px; '
          'halo edge <= %d' % (PK_F, PK_SYM, PK_SAFE_IN, PU_F, PU_SYM, PU_SAFE_IN, HALO_EDGE_MAX))
    for name in sorted(FIT_LOG):
        if name.startswith('selftest'):
            continue
        r = FIT_LOG[name]
        print('  %-28s border %d  clearance %5.1f px  room %.3f' % (
            name, r['border'], r['clear'] if r['clear'] is not None else float('nan'),
            r['s_max'] / (PK_SYM if 'perk' in name else PU_SYM)))
    sets = {'perk': ['i_tod_perk_' + k for k in PERK_KEYS], 'pu': list(PU), 'pap': ['i_tod_hud_pap_1']}
    for label, which, (fx0, fy0, fx1, fy1), (bx0, by0, bx1, by1) in FIT_SLOTS:
        worst = {}
        for n in sets[which]:
            a = np.asarray(built[n][0])[..., 3]
            sx, sy = (bx1 - bx0) / a.shape[1], (by1 - by0) / a.shape[0]
            for thr in (128, 8):
                ys, xs = np.nonzero(a >= thr)
                ex = (bx0 + xs.min() * sx, by0 + ys.min() * sy, bx0 + (xs.max() + 1) * sx, by0 + (ys.max() + 1) * sy)
                m = min(ex[0] - fx0, ex[1] - fy0, fx1 - ex[2], fy1 - ex[3])
                worst[thr] = m if thr not in worst else min(worst[thr], m)
        print('  %-86s frame %4.1f px  halo %4.1f px' % (label, worst[128] * 1.5, worst[8] * 1.5))


def fit_selftest():
    """Negative controls for the gate. Returns the failures (empty = every control fired / held)."""
    bad = []
    blank = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    # 1. the SHIPPED frames (margin 12 / 16 with the 0.42 halo) cut their halo at the canvas edge; ours do not
    for label, shape, w, spread, must_cut in (('shipped perk frame', PK_SHAPE, 9.0, 0.42, True),
                                              ('shipped power-up frame', PU_SHAPE, 8.0, 0.42, True),
                                              ('perk frame', PK_OUT, PK_TUBE_W, PK_SPREAD, False),
                                              ('power-up frame', PU_OUT, PU_TUBE_W, PU_SPREAD, False)):
        s = Svg(256, 256)
        s.tube(poly_d(shape), '#FF3048', w, glow=0.85, spread=spread)
        found = fit_problems('selftest ' + label, s.render(ss=4), None, PK_SAFE)
        print('  %-26s border %3d -> %s' % (label, FIT_LOG['selftest ' + label]['border'], 'CUT' if found else 'clear'))
        if bool(found) != must_cut:
            bad.append('%s: expected %s' % (label, 'a cut halo' if must_cut else 'a clear edge'))
    # 2. the pixel gate agrees with the hull solver: a symbol drawn 4% past the set's scale, at the position the
    #    solver chose, must be caught wherever the solver says even the best position has no such room
    for k in PERK_KEYS:
        white, acc, cut, extra, fit = perk_fit(k)
        big = dict(fit, s=fit['s'] * 1.04)
        w0, a0, _, _ = perk_symbol(k)
        ink = coverage(256, 256, place_svg(bump_strokes(w0, PK_SYM, PK_MIN_SW) + bump_strokes(a0, PK_SYM, PK_MIN_SW), big))
        found = fit_problems('selftest ' + k, blank, ink, PK_SAFE)
        if fit['s_max'] < big['s'] - 0.005 and not found:
            bad.append('%s at 1.04x: the solver has no room (%.3f) but the pixel gate passed it' % (k, fit['s_max']))
        print('  %-26s at 1.04x: room %.3f -> %s' % (k, fit['s_max'] / big['s'], 'CAUGHT' if found else 'fits'))
    # 3. the solver refuses a scale it cannot place
    try:
        w0, a0, _, _ = perk_symbol('staminup')
        fit_symbol(coverage(256, 256, w0 + a0), PK_SAFE, 1.0, PK_F)
        bad.append('fit_symbol placed Stamin-Up at its design size (1.0) inside the safe area')
    except SystemExit as e:
        print('  fit_symbol at 1.0 refused: %s' % e)
    return bad

# =========================================================================================== review
WORLD = os.path.join(ROOT, 'docs', '184_synthwave_ref', 'world_city_ingame.png')


def _world_patch(w, h, seed):
    wd = Image.open(WORLD).convert('RGBA')
    x = (seed * 211) % max(1, wd.width - w)
    y = 120 + (seed * 97) % max(1, wd.height - h - 240)
    if w > wd.width or h > wd.height:
        return wd.resize((w, h), Image.LANCZOS)
    return wd.crop((x, y, x + w, y + h))


def review_sheet(images, out_path):
    """Each image beside what it replaces, BOTH at the size the game draws them at 1080p, each over a patch of
    the real game world (docs/184_synthwave_ref/world_city_ingame.png); small pieces add a 3x NEW detail."""
    from PIL import ImageFont
    font = ImageFont.truetype(artgen.TTF, 20)
    small = ImageFont.truetype(artgen.TTF, 16)
    pad, lab = 16, 28
    rows = []
    for name, _, (w, h), sec in IMAGES:
        old = Image.open(os.path.join(BASE_IMG, name + '.png')).convert('RGBA').resize((w, h), Image.LANCZOS)
        new = images[name][0].resize((w, h), Image.LANCZOS)
        zoom = None
        if h <= 120 and w <= 460:
            z = 3 if h <= 60 else 2
            zoom = images[name][0].resize((w * z, h * z), Image.LANCZOS)
        rows.append((name, sec, old, new, zoom, w, h))
    W = max(pad * 2 + 2 * w + 80 + (zoom.width if zoom else 0) for _, _, _, _, zoom, w, _ in rows)
    H = pad
    for r in rows:
        H += lab + max(r[6], r[4].height if r[4] else 0) + pad
    sheet = Image.new('RGBA', (W, H), (16, 12, 26, 255))
    d = ImageDraw.Draw(sheet)
    y = pad
    for i, (name, sec, old, new, zoom, w, h) in enumerate(rows):
        d.text((pad, y), '[%s] %s   %dx%d on screen at 1080p   OLD -> NEW%s' % (sec, name, w, h, '   (+ NEW at %dx)' % (zoom.width // w) if zoom else ''),
               fill=(225, 220, 240, 255), font=font)
        y += lab
        x = pad
        for im in (old, new):
            sheet.alpha_composite(_world_patch(w, h, i * 3 + (im is new)), (x, y))
            sheet.alpha_composite(im, (x, y))
            x += w + 40
        if zoom:
            sheet.alpha_composite(_world_patch(zoom.width, zoom.height, i * 3 + 2), (x, y))
            sheet.alpha_composite(zoom, (x, y))
        d.text((pad + w + 8, y + h // 2 - 9), '->', fill=(31, 229, 255, 255), font=small)
        y += max(h, zoom.height if zoom else 0) + pad
    sheet.convert('RGB').save(out_path, optimize=True)
    return out_path


def _get_old(name):
    return Image.open(os.path.join(BASE_IMG, name + '.png')).convert('RGBA')


def _repo(name):
    """A shipped image R4 does not redraw (the white gauge segments, the boss marker, the fills)."""
    return Image.open(os.path.join(artgen.IMG, name + '.png')).convert('RGBA')


def _tint(im, rgb):
    a = np.asarray(im).astype(np.float64)
    a[..., :3] *= np.array(rgb, float)[None, None, :]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def hud_screen(get, round_rgb, out_path):
    """The HUD V2 assembled over the in-game city at 1080p, every piece at its Lua rect x 1.5: badge + luck
    plate (6 of 10 lit), the descent gauge (floor 41: 9 floors lit from the crown, a teammate down, a boss), the
    gun plate, two ability tiles (one READY) + the PaP tile, the perk row, the player readout, the power-up row
    and a toast. Live numbers are typeset in the game's face as the Lua would (colours from the Lua)."""
    sc = Image.open(WORLD).convert('RGBA')
    K = 1.5

    def place(im, l, t, r, b):
        sc.alpha_composite(im.resize((int(round((r - l) * K)), int(round((b - t) * K))), Image.LANCZOS), (int(round(l * K)), int(round(t * K))))

    # top-left: the luck plate, the round badge, the segments, the round number
    place(get('i_tod_h2_luck_plate'), 94, 16, 330, 76)
    place(get('i_tod_h2_round_badge'), 16, 10, 88, 82)
    for i in range(1, 11):
        x = 110 + (i - 1) * 21 + 1
        place(get('i_tod_h2_luck_on' if i <= 6 else 'i_tod_h2_luck_off'), x, 52, x + 19, 64)
    cap = 17 * K
    put_text(sc, '12', cap, 53 * K, round_rgb, cx=52 * K)
    # the descent gauge
    place(get('i_tod_h2_gauge_tower'), 1232, 110, 1264, 560)
    dist = [(0.25, 0.85, 0.91), (0.31, 0.86, 0.47), (1.00, 0.59, 0.16), (0.96, 0.77, 0.26), (0.94, 0.32, 0.29)]
    seg, hub, off = _repo('i_tod_h2_gauge_seg'), _repo('i_tod_h2_gauge_seg_hub'), get('i_tod_h2_gauge_seg_off')
    f = 17
    for i in range(1, 26):
        y = 522 - (i - 0.5) * (522 - 148) / 25.0
        ishub = (i % 5 == 0) and i < 25
        w = 14 * (1.4 if ishub else 1.0)
        if i == 21:
            im = _tint(seg, (1.0, 0.18, 0.22))
        elif i >= f:
            im = _tint(hub if ishub else seg, dist[min(4, (i - 1) // 5)])
        else:
            im = _tint(hub, (0.22, 0.22, 0.28)) if ishub else off
        place(im, 1248 - w / 2, y - 4.2, 1248 + w / 2, y + 4.2)
        if i == 21:
            place(get('i_tod_h2_gauge_down'), 1207, y - 6, 1219, y + 6)
        if i == f:
            place(get('i_tod_h2_gauge_you'), 1220, y - 6, 1232, y + 6)
        if i == 13:
            place(_tint(_repo('i_tod_h2_gauge_boss'), (1.0, 0.45, 0.2)), 1194, y - 6, 1206, y + 6)
    # the gun plate + gun + name + ammo
    place(get('i_tod_h2_gun_plate'), 1002, 606, 1266, 678)
    gun = os.path.join(artgen.IMG, 'i_tod_hud_gun_mozambique.png')
    if os.path.exists(gun):
        place(Image.open(gun).convert('RGBA'), 1008, 632, 1104, 676)
    put_text(sc, 'MOZAMBIQUE', 17 * K * 0.8, 629 * K, 'white', right=1256 * K)
    put_text(sc, '32', 27 * K * 0.8, 671 * K, 'white', right=1190 * K)
    put_text(sc, '128', 17 * K * 0.8, 670 * K, 'lav', right=1254 * K)
    # ability tiles (tactical READY) + the PaP tile
    for i, (x0, ready, ab) in enumerate(((1160, True, 'i_tod_h2_ab_hook'), (1210, False, 'i_tod_h2_ab_axe'))):
        place(get('i_tod_h2_tile_ready' if ready else 'i_tod_h2_tile'), x0 + 4, 568, x0 + 50, 600)
        ap = os.path.join(artgen.IMG, ab + '.png')
        if os.path.exists(ap):
            place(Image.open(ap).convert('RGBA'), x0 + 9, 572, x0 + 33, 596)
        put_text(sc, '2', 9 * K, 597 * K, 'white', right=(x0 + 46) * K)
    place(get('i_tod_h2_tile_pap'), 1110, 568, 1156, 600)
    place(get('i_tod_hud_pap_1'), 1114, 571, 1140, 597)
    put_text(sc, '1', 9 * K, 597 * K, 'white', right=1152 * K)
    # the perk row (bottom centre)
    keys = ['jugg', 'speed', 'revive', 'staminup', 'widows', 'deathperception', 'doubletap', 'phd', 'wisptea']
    x0 = 640 - len(keys) * 32 / 2.0
    for i, k in enumerate(keys):
        place(get('i_tod_h2_perk_socket'), x0 + i * 32, 662, x0 + i * 32 + 32, 694)
        place(get('i_tod_perk_' + k), x0 + i * 32 + 3, 665, x0 + i * 32 + 29, 691)
    # the player readout (bottom-left)
    med = os.path.join(artgen.IMG, 'i_tod_class_medallion_heavy.png')
    if os.path.exists(med):
        place(Image.open(med).convert('RGBA'), 28.5, 624.5, 75.5, 671.5)
    place(get('i_tod_h2_medallion_ring'), 24, 620, 80, 676)
    fill = _repo('i_tod_h2_hp_fill')
    place(_tint(fill, (0.06, 0.06, 0.08)), 90, 645, 220, 657)
    hp = fill.crop((0, 0, int(544 * 0.8), 48))
    sc.alpha_composite(hp.resize((int(130 * 0.8 * K), int(12 * K)), Image.LANCZOS), (int(90 * K), int(645 * K)))
    place(get('i_tod_h2_hp_frame'), 90, 645, 220, 657)
    sf = _tint(_repo('i_tod_h2_shield_fill'), (0.4, 0.7, 1.0))
    sc.alpha_composite(sf.crop((0, 0, int(544 * 0.6), 24)).resize((int(130 * 0.6 * K), int(6 * K)), Image.LANCZOS), (int(90 * K), int(636 * K)))
    put_text(sc, 'JORDAN', 11 * K, 632 * K, 'white', x=90 * K)
    place(get('i_tod_h2_points'), 90, 662, 106, 678)
    put_text(sc, '4250', 13 * K, 676 * K, 'white', x=110 * K)
    # the power-up row + a toast
    pus = ['i_tod_pu2_insta', 'i_tod_pu2_double_points', 'i_tod_pu2_max_ammo', 'i_tod_pu2_zombie_blood']
    for i, n in enumerate(pus):
        x = 640 - 132 + i * 66
        place(get(n), x, 597, x + 49, 646)
    place(get('i_tod_h2_toast'), 534, 512, 746, 561)
    place(get('i_tod_pu2_nuke'), 537, 515, 580, 558)
    put_text(sc, 'NUKE', 13 * K, 542 * K, 'white', cx=663 * K, track=0.2)
    sc.convert('RGB').save(out_path)
    return out_path


def prompt_screen(get, out_path):
    """Prompt cards at 2x their 1080p size over the world: a door, a perk (the perk's own logo in the well),
    a refusal (the locked chassis) and the wide Quick Revive card - text laid as TodPromptCard.lua lays it."""
    sc = _world_patch(1500, 820, 5).copy()
    U = 4.0
    cards = [
        ('i_tod_prompt_chassis', 'i_tod_prompt_icon_door', 'OPEN DOOR', 'TO FLOOR 41', '', 'TO OPEN', '$1500'),
        ('i_tod_prompt_chassis', 'i_tod_perk_jugg', 'JUGGERNOG', 'TAKE MORE HITS', '', 'TO BUY', '$2500'),
        ('i_tod_prompt_chassis_locked', 'i_tod_prompt_icon_power', 'POWER REQUIRED', 'TURN ON THE POWER', 'IN THE POWER ROOM', '', ''),
        ('i_tod_prompt_chassis_wide', 'i_tod_perk_revive', 'QUICK REVIVE', 'SOLO $500 - REVIVE YOURSELF', 'CO-OP $1500 - FASTER REVIVES', 'TO BUY', '$500'),
        ('i_tod_prompt_chassis', 'i_tod_prompt_icon_arena', 'BATTLE ARENA', 'LEVEL 3 OF 10', 'THREE WAVES', 'TO ENTER', ''),
        ('i_tod_prompt_chassis', 'i_tod_prompt_icon_black_market', 'BLACK MARKET', 'A FREE AI COMPANION', 'ON THE HOUSE', 'TO TAKE', ''),
    ]
    x, y = 20, 20
    for ch, icon, title, d1, d2, verb, price in cards:
        c = get(ch).copy()
        wide = c.width > 924
        dx = 276 if wide else 0
        ic = get(icon).resize((176, 176), Image.LANCZOS)
        c.alpha_composite(ic, (60, 68))
        tT, tB = (448.3 - 444) * U, (459.7 - 444) * U
        cap = (tB - tT) * 0.8
        put_text(c, title, cap, tB - (tB - tT - cap) / 2, 'white', x=(620 - 544) * U + dx, fit=(770 - 620) * U)
        bodyT, bodyB, dh, pitch = (462.1 - 444) * U, (500.6 - 444) * U, 8.4 * U, 12.05 * U
        dcap = dh * 0.8
        lines = [l for l in (d1, d2) if l]
        block = (pitch + dh) if len(lines) == 2 else dh
        top = bodyT + ((bodyB - bodyT) - block) / 2
        for j, l in enumerate(lines):
            put_text(c, l, dcap, top + j * pitch + dh - (dh - dcap) / 2, 'lav', x=(620 - 544) * U + dx, fit=(767 - 620) * U + dx)
        if verb:
            fcap = 9.4 * U * 0.8
            put_text(c, 'HOLD F ' + verb, fcap, (512.6 - 444) * U, 'white', x=(620 - 544) * U + dx)
        if price:
            put_text(c, price, 10.4 * U * 0.8, (512.9 - 444) * U, (228, 225, 108), right=(771 - 544) * U + dx)
        k = 2 * 1.5 / U
        c = c.resize((int(c.width * k), int(c.height * k)), Image.LANCZOS)
        if x + c.width > sc.width - 20:
            x, y = 20, y + c.height + 20
        sc.alpha_composite(c, (x, y))
        x += c.width + 20
    sc.convert('RGB').save(out_path)
    return out_path


def deal_screens(stage_dir, out_dir):
    """The upgrade deal panel through tools/ui_mockup/render_pull.py: OLD = the repo today, NEW = an art dir
    holding R3's staged chrome (if staged) + R4's luck badges / legend. Returns {tag: last frame path}."""
    import subprocess
    py = sys.executable
    tool = os.path.join(ROOT, 'tools', 'ui_mockup', 'render_pull.py')
    merged = tempfile.mkdtemp(prefix='r4_deal_')
    r3 = os.path.join(ROOT, 'tmp', 'redesign', 'R3-synthwave-system', 'stage', IMG_REL)
    for src in (r3, stage_dir):
        if os.path.isdir(src):
            for f in os.listdir(src):
                if f.endswith('.png'):
                    shutil.copy2(os.path.join(src, f), merged)
    res = {}
    for tag, extra in (('r4_old', []), ('r4_new', ['--art-dir', merged])):
        r = subprocess.run([py, tool, '--name', tag, '--fps', '6'] + extra, cwd=ROOT, capture_output=True, text=True)
        folder = os.path.join(ROOT, 'tmp', 'ui_mockup', 'pull', tag)
        frames = sorted(f for f in os.listdir(folder) if f.startswith('frame_')) if os.path.isdir(folder) else []
        if r.returncode or not frames:
            print('render_pull %s failed:\n%s' % (tag, (r.stderr or '')[-1500:]))
            continue
        dst = os.path.join(out_dir, '_screen_deal_%s.png' % tag.split('_')[1])
        shutil.copy2(os.path.join(folder, frames[-1]), dst)
        res[tag] = dst
    shutil.rmtree(merged, ignore_errors=True)
    return res


def screens_sheet(pairs, out_path):
    """OLD above NEW for each screen, each at half size, labelled."""
    from PIL import ImageFont
    font = ImageFont.truetype(artgen.TTF, 26)
    ims = []
    for label, old, new in pairs:
        a, b = Image.open(old).convert('RGB'), Image.open(new).convert('RGB')
        w = 1280
        a = a.resize((w, int(a.height * w / a.width)), Image.LANCZOS)
        b = b.resize((w, int(b.height * w / b.width)), Image.LANCZOS)
        ims.append((label, a, b))
    W = 2 * 1280 + 3 * 20
    H = sum(max(a.height, b.height) + 60 for _, a, b in ims) + 20
    sheet = Image.new('RGB', (W, H), (16, 12, 26))
    d = ImageDraw.Draw(sheet)
    y = 20
    for label, a, b in ims:
        d.text((20, y), label + '   OLD (left)   NEW (right)', fill=(225, 220, 240), font=font)
        y += 40
        sheet.paste(a, (20, y))
        sheet.paste(b, (40 + 1280, y))
        y += max(a.height, b.height) + 20
    sheet.save(out_path, optimize=True)
    return out_path

# ============================================================================================ wiring
def wiring_problems(root):
    """Every image is a same-name drop-in: its GDT block and zone line must already exist (they do today, and
    nothing in R4 adds one). The round number must be painted in the THEME's accent (ROUND2_TINT), PK07 must take its
    arena accent from synthwave.THEME, and make_badge.py must still derive the arena twins from the round badges."""
    import glob
    out = []
    gdt = open(os.path.join(ROOT, 'source_data', 'tod_ui_images.gdt'), encoding='utf-8', errors='replace').read()
    zone = ''.join(open(z, encoding='utf-8', errors='replace').read() for z in glob.glob(os.path.join(ROOT, 'zone_source', '*.zone')))
    for name, _, _, _ in IMAGES:
        if not re.search(r'"%s"\s*\(\s*"image\.gdf"' % re.escape(name), gdt):
            out.append('%s: no GDT block in source_data/tod_ui_images.gdt' % name)
        if not re.search(r'^\s*image,%s\s*$' % re.escape(name), zone, re.M):
            out.append('%s: no zone image line' % name)
    lua = os.path.join(root, UPG_REL)
    if not os.path.exists(lua):
        lua = os.path.join(ROOT, UPG_REL)
    src = open(lua, encoding='utf-8', errors='replace').read()
    out += round2_problems(src)
    out += ['round tint gate blind: ' + m for m in round2_selftest(src)]
    pk = os.path.join(root, PK07_REL)
    if not os.path.exists(pk):
        pk = os.path.join(ROOT, PK07_REL)
    pks = open(pk, encoding='utf-8').read()
    for line in PK07_THEME_LINES:
        if line not in pks:
            out.append('pk07_prompt_icons.py: the arena icon does not take the theme accent (missing: %s)' % line)
    return out

# ============================================================================================== main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--stage', action='store_true', help='also write tmp/redesign/%s/stage/ (+ base/)' % PACK)
    ap.add_argument('--install', action='store_true', help='LANDING ONLY: copy into source_data/tod_ui_images/_images')
    ap.add_argument('--check', action='store_true', help='fail on any byte that differs from the installed (or staged) files')
    ap.add_argument('--against', choices=('installed', 'stage'), default='installed')
    ap.add_argument('--no-screens', action='store_true', help='skip the screen composites (faster)')
    ap.add_argument('--fit-report', action='store_true', help='print the safe-inset numbers (section E0) and exit')
    ap.add_argument('--fit-selftest', action='store_true', help='run the safe-inset gate\'s negative controls and exit')
    a = ap.parse_args()

    if a.fit_report or a.fit_selftest:
        if a.fit_report:
            built = {'i_tod_perk_' + k: (perk_icon(k),) for k in PERK_KEYS}
            built.update({n: (powerup_icon(n),) for n in PU})
            built['i_tod_hud_pap_1'] = (pap_icon(),)
            fit_report(built)
        if a.fit_selftest:
            bad = fit_selftest()
            for msg in bad:
                print('R4 FIT SELFTEST: %s' % msg)
            if bad:
                sys.exit(1)
            print('R4 FIT SELFTEST OK (every negative control fired)')
        return

    staged_pk07 = os.path.join(STAGE_ROOT, PK07_REL)
    if a.check:
        against_stage = a.against == 'stage'
        root = STAGE_ROOT if against_stage else ROOT
        pk07_path = staged_pk07 if against_stage else os.path.join(ROOT, PK07_REL)
        built = build_all(pk07_path)
        img_dir = STAGE_IMG if against_stage else artgen.IMG
        bad = 0
        for name, (im, data) in built.items():
            if name in PK07_NAMES and not against_stage:
                continue                     # installed: PK07's own --check gates its two icons
            p = os.path.join(img_dir, name + '.png')
            if not os.path.isfile(p):
                print('R4 SYNTHWAVE HUD: MISSING %s' % p)
                bad += 1
            elif open(p, 'rb').read() != data:
                print('R4 SYNTHWAVE HUD: STALE %s (re-run the generator; never hand-edit it)' % p)
                bad += 1
        for msg in wiring_problems(root):
            print('R4 SYNTHWAVE HUD: %s' % msg)
            bad += 1
        if bad:
            sys.exit(1)
        print('R4 SYNTHWAVE HUD OK %d images + wiring (%s)' % (len(built) - (0 if against_stage else len(PK07_NAMES)),
                                                               'stage' if against_stage else 'installed'))
        return

    # PK07's two icons come from PK07's own generator (R4's staged two-constant edit landed 2026-10-04; since the RT
    # pass the arena accent follows synthwave.THEME there)
    pk07_path = os.path.join(ROOT, PK07_REL)

    built = build_all(pk07_path)
    os.makedirs(OUT, exist_ok=True)
    for name, (im, data) in built.items():
        with open(os.path.join(OUT, name + '.png'), 'wb') as fh:
            fh.write(data)
        print('%-40s %s' % (name, hashlib.md5(data).hexdigest()))
    if a.stage:
        os.makedirs(STAGE_IMG, exist_ok=True)
        for name, (im, data) in built.items():
            with open(os.path.join(STAGE_IMG, name + '.png'), 'wb') as fh:
                fh.write(data)
        # (the Round2Row code tint is ROUND2_TINT[THEME]: --check fails until tod_upgrade.lua carries it)
        print('staged ->', STAGE_ROOT)
    if a.install:
        for name, (im, data) in built.items():
            if name in PK07_NAMES:
                continue                     # PK07 installs its own (after its staged edit lands)
            with open(os.path.join(artgen.IMG, name + '.png'), 'wb') as fh:
                fh.write(data)
        print('installed %d images into %s' % (len(built) - len(PK07_NAMES), artgen.IMG))

    print('review ->', review_sheet(built, os.path.join(OUT, '_review.png')))
    # THE HOT STREAK's ON FIRE tint (tod_upgrade.lua drawLuckV2 multiplies lit segments by 1, 0.62, 0.30): the lit
    # segment must turn a clean ORANGE, not green. Lit / ON FIRE / unlit, 4x.
    on, off = built['i_tod_h2_luck_on'][0], built['i_tod_h2_luck_off'][0]
    fire = _tint(on, (1.0, 0.62, 0.30))
    strip = Image.new('RGBA', (76 * 3 + 16, 48), (30, 26, 40, 255))
    for i, im in enumerate((on, fire, off)):
        strip.alpha_composite(im, (i * 84, 0))
    strip.resize((strip.width * 4, strip.height * 4), Image.NEAREST).convert('RGB').save(os.path.join(OUT, '_review_luck_onfire.png'))
    if not a.no_screens:
        new_get = lambda n: built[n][0] if n in built else Image.open(os.path.join(artgen.IMG, n + '.png')).convert('RGBA')
        old_get = lambda n: _get_old(n) if os.path.exists(os.path.join(BASE_IMG, n + '.png')) else Image.open(os.path.join(artgen.IMG, n + '.png')).convert('RGBA')
        hud_o = hud_screen(old_get, (250, 28, 56), os.path.join(OUT, '_screen_hud_old.png'))
        hud_n = hud_screen(new_get, MAGENTA_RGB, os.path.join(OUT, '_screen_hud_new.png'))   # MAGENTA_RGB = the theme's accent
        pr_o = prompt_screen(old_get, os.path.join(OUT, '_screen_prompt_old.png'))
        pr_n = prompt_screen(new_get, os.path.join(OUT, '_screen_prompt_new.png'))
        pairs = [('HUD V2 at 1080p over the city', hud_o, hud_n), ('Prompt cards (2x)', pr_o, pr_n)]
        stage_img = STAGE_IMG if a.stage else OUT
        deal = deal_screens(stage_img, OUT)
        if 'r4_old' in deal and 'r4_new' in deal:
            pairs.append(('Upgrade deal panel (luck badge + legend; NEW also carries R3\'s staged chrome)', deal['r4_old'], deal['r4_new']))
        print('screens ->', screens_sheet(pairs, os.path.join(OUT, '_review_screens.png')))


if __name__ == '__main__':
    main()
