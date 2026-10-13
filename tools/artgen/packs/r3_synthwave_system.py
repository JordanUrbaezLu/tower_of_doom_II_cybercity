"""r3_synthwave_system.py - THE MAP 2 SYNTHWAVE DESIGN SYSTEM, pass R3 (2026-10-04).

Fulfils docs/184a (pause menu, 20 files) + docs/184b (scoreboard, 8 files) + the Map 1 CARD PANEL
CHROME that still shipped byte-identical to Map 1 (tmp/design_review/findings.md, 16 files), all
under their EXISTING names and sizes, so the install is a file swap. The design rules live in
tools/artgen/synthwave.py (code) and tmp/redesign/R3-synthwave-system/STYLE.md (words).

GEOMETRY IS NOT TASTE. Every empty area, gap and band below is copied from the art the Lua was
laid out against (the red set, docs/180/181, and the Map 1 plates whose pixels tod_upgrade.lua /
tod_class_select.lua / TodKeycap.lua MEASURED): e.g. i_tod_hold_plate keeps its key gap at
x169..286 (centre 227.5) and its lettering band centred on y 33.5; i_tod_key_blank_wide keeps its
bright face at x29..354, y19..148 because TodKeycap centres the key name at 43.5% of the cap.

  python tools/artgen/packs/r3_synthwave_system.py            # -> art/generated/R3-synthwave-system/ + reviews
  python tools/artgen/packs/r3_synthwave_system.py --stage    # + copy into tmp/redesign/R3-synthwave-system/stage/
  python tools/artgen/packs/r3_synthwave_system.py --install  # copy into source_data/tod_ui_images/_images (LANDING ONLY)
  python tools/artgen/packs/r3_synthwave_system.py --check    # regenerate in memory; fail on any byte != installed
  python tools/artgen/packs/r3_synthwave_system.py --check --against stage   # ... != the staged copies
"""
import argparse, math, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402
from synthwave import (PAL, LOOK, THEME, Svg, chamfer, poly_d, line_d, inset, mix, hexs, hexrgb, put_text, neon_word, d_box,  # noqa: E402
                       text_width, grain, scratches, embers, specks, fade_alpha, clip_to, glow_of, over, _paste)
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

PACK = 'R3-synthwave-system'
ROOT = artgen.ROOT
STAGE_ROOT = os.path.join(ROOT, 'tmp', 'redesign', PACK, 'stage')
STAGE_IMG = os.path.join(STAGE_ROOT, 'source_data', 'tod_ui_images', '_images')
BASE_IMG = os.path.join(ROOT, 'tmp', 'redesign', PACK, 'base', 'source_data', 'tod_ui_images', '_images')

INK = hexrgb('ink')         # dark ink for letters on a pale keycap (matches TodKeycap INK 0.10/0.13/0.20 in spirit)


def layered(w, h, base_fn, top_fn=None, grain_amp=0.03, seed=7):
    """Render a piece as BASE (plates, hairlines, scratches; grained) + TOP (tubes, rules, icons)."""
    b = Svg(w, h)
    base_fn(b)
    im = b.render()
    if grain_amp:
        im = grain(im, grain_amp, seed)
    if top_fn:
        t = Svg(w, h)
        top_fn(t)
        im.alpha_composite(t.render())
    return im

# =============================================================================== shared motifs

def skull(s, x, y, k, outline='skull_line', eyes='magenta', crack='magenta', opacity=1.0):
    """THE HOLOGRAM ZOMBIE: a Map 2 skull drawn as a neon wireframe - dark glass bone, violet tube
    contour, scan lines, angry sockets with slit magenta eyes, a split jaw of broken fangs, cracks.
    Box 300 x 330 at scale k, origin (x, y)."""
    T = lambda px, py: (x + px * k, y + py * k)

    def C(cmds):
        out = []
        for c in cmds:
            if isinstance(c, str):
                out.append(c)
            else:
                out.append('%.2f,%.2f' % T(*c))
        return ' '.join(out)
    d_head = C(['M', (150, 6), 'C', (214, 6), (268, 40), (280, 104), 'C', (286, 132), (280, 150), (270, 162),
                'C', (264, 172), (270, 182), (280, 192), 'C', (286, 202), (278, 216), (262, 224), 'L', (246, 232),
                'C', (240, 246), (236, 256), (226, 262), 'L', (74, 262), 'C', (64, 256), (60, 246), (54, 232),
                'L', (38, 224), 'C', (22, 216), (14, 202), (20, 192), 'C', (30, 182), (36, 172), (30, 162),
                'C', (20, 150), (14, 132), (20, 104), 'C', (32, 40), (86, 6), (150, 6), 'Z'])
    d_jaw = C(['M', (76, 276), 'L', (224, 276), 'C', (228, 294), (222, 308), (206, 316), 'L', (184, 326), 'L', (116, 326),
               'L', (94, 316), 'C', (78, 308), (72, 294), (76, 276), 'Z'])
    g = s.rad([(0, 'skull_hi', 0.95 * opacity), (0.6, 'plate_top', 0.92 * opacity), (1, 'plate', 0.9 * opacity)], 0.5, 0.40, 0.62)
    for d in (d_head, d_jaw):
        s.path(d, fill='url(#%s)' % g)
    cid = '%sclip%d' % (s.pre, len(s._ids))
    s._ids[('clip', cid)] = cid
    s.defs.append('<clipPath id="%s"><path d="%s"/><path d="%s"/></clipPath>' % (cid, d_head, d_jaw))
    lines = ''.join('<path d="%s" stroke="%s" stroke-width="%.2f" opacity="%.3f" fill="none"/>' % (
        line_d(T(0, yy), T(300, yy + 5)), hexs(outline), 1.1 * k, 0.24 * opacity) for yy in range(20, 330, 14))
    s.add('<g clip-path="url(#%s)">%s</g>' % (cid, lines))
    P = lambda pts: poly_d([T(*p) for p in pts])
    ls = [(56, 128), (136, 150), (132, 188), (110, 200), (78, 196), (60, 176)]
    rs = [(300 - a, b) for a, b in ls]
    nose = [(150, 200), (134, 234), (150, 226), (166, 234)]
    for p in (ls, rs):
        s.path(P(p), fill='void', opacity=opacity)
        s.path(P(p), fill=eyes, opacity=0.16 * opacity, filt=s.blur(6 * k, d_box(P(p))))
        s.path(P(p), stroke=outline, sw=1.8 * k, opacity=0.8 * opacity)
    s.path(P(nose), fill='void', opacity=opacity)
    s.path(P(nose), stroke=outline, sw=1.6 * k, opacity=0.7 * opacity)
    # fangs: upper hang from 262, lower rise from 276 - they cross the gap like a snarl
    for i, tx in enumerate(range(80, 214, 13)):
        L = 18 + (10 if i % 3 == 1 else 0) - (5 if i % 4 == 3 else 0)
        tri = [(tx, 260), (tx + 11, 260), (tx + 5.5, 260 + L)]
        s.path(P(tri), fill='fang_hi', opacity=0.6 * opacity)
        s.path(P(tri), stroke='plate', sw=1.1 * k, opacity=0.9 * opacity)
    for i, tx in enumerate(range(88, 206, 13)):
        L = 12 + (8 if i % 3 == 0 else 0)
        tri = [(tx, 280), (tx + 10, 280), (tx + 5, 280 - L)]
        s.path(P(tri), fill='fang_lo', opacity=0.5 * opacity)
        s.path(P(tri), stroke='plate', sw=1.0 * k, opacity=0.9 * opacity)
    for c in ([(150, 6), (142, 44), (158, 70), (146, 108)], [(142, 44), (118, 58), (108, 90)],
              [(266, 92), (238, 110), (234, 138)], [(40, 196), (58, 212)]):
        s.tube(poly_d([T(*p) for p in c], False), crack, 1.4 * k, glow=0.5 * opacity, core=False)
    s.tube(d_head, outline, 2.4 * k, glow=0.6 * opacity)
    s.tube(d_jaw, outline, 2.0 * k, glow=0.5 * opacity)
    # slit eyes, angled down toward the nose (angry)
    for ex, rot in ((98, 14), (202, -14)):
        cx, cy = T(ex, 172)
        s.circle(cx, cy, 42 * k, fill=eyes, opacity=0.38 * opacity, filt=s.blur(18 * k, (cx - 42 * k, cy - 42 * k, cx + 42 * k, cy + 42 * k)))
        s.add('<ellipse cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f" transform="rotate(%d %.2f %.2f)" fill="%s" opacity="%.3f" filter="url(#%s)"/>'
              % (cx, cy, 22 * k, 11 * k, rot, cx, cy, hexs(eyes), 0.9 * opacity, s.blur(4 * k, (cx - 22 * k, cy - 22 * k, cx + 22 * k, cy + 22 * k))))
        s.add('<ellipse cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f" transform="rotate(%d %.2f %.2f)" fill="%s" opacity="%.3f"/>'
              % (cx, cy, 10 * k, 4.2 * k, rot, cx, cy, hexs('hot_core'), opacity))


def skyline(s, box, seed, neon_x=None, alpha=0.85):
    """The cyber city at the bottom of a panel: black towers, lit roofline tubes only inside the
    neon_x spans (never behind a text slot), and THE TOWER rising in the middle of the span."""
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    x = x0
    roofs = []
    while x < x1:
        w = float(rng.uniform(26, 70))
        h = float(rng.uniform(0.25, 0.85)) * (y1 - y0)
        roofs.append((x, w, h))
        x += w + float(rng.uniform(-6, 4))
    for bx, w, h in roofs:
        top = y1 - h
        pts = [(bx, y1), (bx, top + 6), (bx + 6, top), (bx + w, top), (bx + w, y1)]
        s.path(poly_d(pts), fill='deep', opacity=alpha)
        lit = neon_x and any(a <= bx and bx + w <= b for a, b in neon_x)
        if lit and rng.random() < 0.75:
            col = ['magenta', 'cyan', 'violet'][int(rng.integers(0, 3))]
            if LOOK['skyline_lit']:
                s.tube(line_d((bx, top + 6), (bx + 6, top), (bx + w, top)), col, 1.6, glow=0.45)
        # a few lit windows (the fallen city is dark: unlit roofs, no windows - THE TOWER's tip alone is red)
        for _ in range(int(rng.integers(0, 4))):
            wx = bx + float(rng.uniform(4, max(5, w - 8)))
            wy = top + float(rng.uniform(10, max(11, h - 6)))
            if wy < y1 - 4:
                col = ['violet', 'window'][int(rng.integers(0, 2))]
                if LOOK['skyline_lit']:
                    s.rect(wx, wy, 3, 2, col, opacity=0.35)
    if neon_x:
        a, b = neon_x[0]
        cx = (a + b) / 2.0
        H = (y1 - y0) * 1.0
        tw = 34
        spire = [(cx - tw / 2, y1), (cx - tw / 2, y1 - H * 0.72), (cx - 8, y1 - H * 0.86), (cx, y0 - 6),
                 (cx + 8, y1 - H * 0.86), (cx + tw / 2, y1 - H * 0.72), (cx + tw / 2, y1)]
        s.path(poly_d(spire), fill='deep', opacity=0.95)
        if LOOK['skyline_lit']:
            s.tube(poly_d(spire[:-1] + [spire[-1]], False), 'magenta', 1.6, glow=0.6)
        else:
            s.steel(spire[:-1] + [spire[-1]], 1.2, opacity=0.7, close=False)
        s.circle(cx, y0 - 6, 2.5, fill='hot_core', filt=None)
        s.circle(cx, y0 - 6, 7, fill='magenta', opacity=0.5, filt=s.blur(4))


def bevel(s, shape, k=2.2):
    """The glass edge catching light: a steel_hi hairline just inside the TOP edge of a tile."""
    ins = inset(shape, k)
    top = min(p[1] for p in ins)
    run = [p for p in ins if abs(p[1] - top) < 0.5]
    if len(run) >= 2:
        s.path(line_d(run[0], run[-1]), stroke='steel_hi', sw=1.2, opacity=0.55)


def frame_light(s, pts, runs, w, glow, spread=1.0):
    """A BIG panel's frame light. Synthwave: the whole outline is one lit magenta tube. Fallen (LOOK panel_runs,
    docs/180-181): the outline is an unlit 2 px STEEL line with a faint sheen, and the red lights only the sides the
    red era lit (`runs`: vertex-index paths into pts, measured off tmp/redesign/R3-synthwave-system/base)."""
    if not LOOK['panel_runs']:
        s.tube(poly_d(pts), 'magenta', w, glow=glow, spread=spread)
        return
    d = poly_d(pts)
    s.path(d, stroke='steel', sw=w * 2.4, opacity=0.10, filt=s.blur(w * 1.1, d_box(d, w * 3)))
    s.path(d, stroke='steel', sw=w * 0.72, join='miter')
    n = len(pts)
    for run in runs:
        s.tube(poly_d([pts[i % n] for i in run], False), 'magenta', w, glow=glow, spread=spread)


def circuit(s, pts, color='violet', opacity=0.5):
    """A thin circuit trace with a node at its end (panel-corner decoration)."""
    s.path(line_d(*pts), stroke=color, sw=1.4, opacity=opacity)
    s.circle(pts[-1][0], pts[-1][1], 3.2, fill='none', stroke=color, sw=1.4, opacity=opacity)


def tagline(im, text, cap, base, cx, sh, n=3, track=0.5, gap=None):
    """'/// TEXT ///': the text centred on cx, the neon slash groups placed off its MEASURED ends."""
    (x0, x1), _ = put_text(im, text, cap, base, 'lav', cx=cx, track=track)
    gap = gap if gap is not None else sh * 0.45
    w = (n - 1) * gap + sh * 0.42
    t = Svg(im.width, im.height)
    t.slashes(x0 - sh * 0.9 - w, base + sh * 0.12, sh, n, 'cyan', max(1.6, sh * 0.13), gap=gap, glow=0.6)
    t.slashes(x1 + sh * 0.9, base + sh * 0.12, sh, n, 'cyan', max(1.6, sh * 0.13), gap=gap, glow=0.6)
    im.alpha_composite(t.render())


def tag_group(im, left, right, box, cap, base, track=0.3):
    """'LEFT // RIGHT' centred in box=(x0, x1), shrunk until it fits with 18 px of air each side."""
    x0, x1 = box
    sl = cap * 1.6
    while True:
        wl, wr = text_width(left, cap, track), text_width(right, cap, track)
        tot = wl + wr + sl + cap * 1.4
        if tot <= (x1 - x0) - 36 or cap <= 8:
            break
        cap -= 0.25
        sl = cap * 1.6
    x = (x0 + x1) / 2 - tot / 2
    put_text(im, left, cap, base, 'lav', x=x, track=track)
    t = Svg(im.width, im.height)
    t.slashes(x + wl + cap * 0.7, base + 2, cap * 1.25, 2, 'cyan', 2.0, gap=cap * 0.55, glow=0.6)
    im.alpha_composite(t.render())
    put_text(im, right, cap, base, 'lav', x=x + wl + cap * 0.7 + sl + cap * 0.0, track=track)


def card_fan(s, cx, cy, k):
    """THE UPGRADE CARDS icon: three Map 2 cards fanned (pale faces, ink outline, a magenta star)."""
    for ang, dx, face in ((-20, -18, 'card_a'), (-4, -2, 'card_b'), (14, 16, 'card_c')):
        w, h = 46 * k, 66 * k
        pts = chamfer(-w / 2, -h / 2, w / 2, h / 2, tl=6 * k, br=6 * k)
        a = math.radians(ang)
        rot = [(cx + dx * k + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
        s.path(poly_d(rot), fill=face, stroke='glass', sw=3.2 * k)
        last = rot
    # magenta star on the front card
    fx = sum(p[0] for p in last) / len(last)
    fy = sum(p[1] for p in last) / len(last)
    star = []
    for i in range(10):
        r = (13 if i % 2 == 0 else 5.5) * k
        a = math.radians(-90 + i * 36 + 14)
        star.append((fx + r * math.cos(a), fy + r * math.sin(a)))
    s.path(poly_d(star), fill='magenta', filt=None)
    s.path(poly_d(star), fill='magenta', opacity=0.5, filt=s.blur(4 * k))


def hash_sign(s, cx, base, cap, color='infotext'):
    """'#' - our typeface has none (docs/184b): two slanted bars crossed by two flat bars, in the
    glyph's own ink-outline-plus-face weight."""
    h = cap
    w = cap * 0.82
    bars = [line_d((cx - w * 0.18 + h * 0.08, base - h), (cx - w * 0.18 - h * 0.08, base)),
            line_d((cx + w * 0.18 + h * 0.08, base - h), (cx + w * 0.18 - h * 0.08, base)),
            line_d((cx - w * 0.5, base - h * 0.66), (cx + w * 0.5, base - h * 0.66)),
            line_d((cx - w * 0.5, base - h * 0.32), (cx + w * 0.5, base - h * 0.32))]
    for d in bars:
        s.path(d, stroke='glass', sw=cap * 0.30)
    for d in bars:
        s.path(d, stroke=color, sw=cap * 0.15)


def pad_a(s, texts, cx, cy, r, cap=None):
    """The pad A button: dark glass disc, NEON-GREEN tube ring (the one off-palette hue: the
    controller's own identity colour, so a pad player reads it at a glance), white A."""
    s.circle(cx, cy, r, fill='url(#%s)' % s.rad([(0, 'pad_well', 1), (1, 'plate', 1)]))
    s.tube('M%.2f,%.2f a%.2f,%.2f 0 1,0 %.2f,0 a%.2f,%.2f 0 1,0 %.2f,0' % (cx - r, cy, r, r, 2 * r, r, r, -2 * r),
           'pad_a', max(1.4, r * 0.11), glow=0.7, spread=0.6)
    cap = cap or r * 1.05
    texts.append(lambda im, cx=cx, cy=cy, cap=cap: put_text(im, 'A', cap, cy + cap / 2, 'white', cx=cx))


def dpad(s, cx, cy, size, lit=None, arrows=True):
    """The d-pad: a dark glass cross; `lit` = 'left' | 'right' | 'both' lights that arm cyan."""
    a = size * 0.19          # half arm width
    L = size * 0.5           # arm reach
    cross = [(cx - a, cy - L), (cx + a, cy - L), (cx + a, cy - a), (cx + L, cy - a), (cx + L, cy + a), (cx + a, cy + a),
             (cx + a, cy + L), (cx - a, cy + L), (cx - a, cy + a), (cx - L, cy + a), (cx - L, cy - a), (cx - a, cy - a)]
    s.path(poly_d(cross), fill='url(#%s)' % s.lin([(0, 'dpad_hi', 1), (1, 'dpad_lo', 1)]), stroke='glass', sw=size * 0.06)
    s.path(poly_d(cross), stroke='steel', sw=size * 0.022)
    sides = {'left': -1, 'right': 1}
    for side, sx in sides.items():
        on = lit in (side, 'both')
        arm = [(cx + sx * a * 1.05, cy - a * 0.92), (cx + sx * L * 0.96, cy - a * 0.92), (cx + sx * L * 0.96, cy + a * 0.92), (cx + sx * a * 1.05, cy + a * 0.92)]
        if on:
            s.path(poly_d(arm), fill='url(#%s)' % s.lin([(0, 'dpad_lit_hi', 1), (1, 'dpad_lit_lo', 1)]))
            s.tube(poly_d(arm), 'cyan', size * 0.025, glow=0.8, spread=0.7)
        if arrows:
            tx = cx + sx * (a + (L - a) * 0.55)
            tri = [(tx + sx * a * 0.42, cy), (tx - sx * a * 0.38, cy - a * 0.55), (tx - sx * a * 0.38, cy + a * 0.55)]
            s.path(poly_d(tri), fill='#FFFFFF' if on else 'steel', stroke='glass' if on else 'none', sw=size * 0.02)
    s.circle(cx, cy, a * 0.32, fill='void', stroke='steel', sw=size * 0.012)


def sparkle(s, cx, cy, r, color='cyan'):
    st = [(cx, cy - r), (cx + r * 0.22, cy - r * 0.22), (cx + r, cy), (cx + r * 0.22, cy + r * 0.22), (cx, cy + r),
          (cx - r * 0.22, cy + r * 0.22), (cx - r, cy), (cx - r * 0.22, cy - r * 0.22)]
    s.path(poly_d(st), fill=color, opacity=0.6, filt=s.blur(r * 0.4))
    s.path(poly_d(st), fill='spark')

# ============================================================================== PAUSE MENU (184a)

def pm_backdrop():
    return backdrop(kind='pm')


def sb_backdrop():
    return backdrop(kind='sb')


def backdrop(kind):
    """Full-screen overlay: a violet-black vignette, magenta / violet haze in the corners, a faint
    magenta horizon grid at the bottom edges (backdrops ONLY), embers; transparent in the middle."""
    W, H = 1920, 1080
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
    r = np.sqrt((nx * 0.92) ** 2 + (ny * 1.0) ** 2)
    a = ((r - 0.58) / 0.62).clip(0, 1) ** 1.35 * 168
    base = np.zeros((H, W, 4), np.float32)
    base[:, :, :3] = hexrgb('void')
    base[:, :, 3] = a
    im = Image.fromarray(base.clip(0, 255).astype(np.uint8), 'RGBA')

    s = Svg(W, H)
    for (cx, cy, rr, col, op) in ((-60, -40, 560, 'haze_hot', 0.30), (W + 80, -80, 600, 'haze_cool', 0.36),
                                  (W + 60, H + 40, 600, 'haze_hot', 0.30), (-80, H + 60, 640, 'haze_cool', 0.34),
                                  (W * 0.62, -120, 420, 'haze_hot', 0.14)):
        s.circle(cx, cy, rr, fill='url(#%s)' % s.rad([(0, col, min(1.0, op * LOOK['haze_k'])), (1, col, 0)]))
    im.alpha_composite(s.render(ss=1))

    # horizon grid (synthwave only - the red era had none): vanishing point at the screen centre line,
    # fading to nothing in the middle
    if LOOK['grid']:
        g = Svg(W, H)
        hy = 790
        for i in range(-24, 25):
            g.path(line_d((W / 2 + i * 22, hy), (W / 2 + i * 260, H + 40)), stroke='grid', sw=1.6, opacity=0.55)
        k = 0
        while True:
            y = hy + 6 * (1.32 ** k) - 6
            if y > H:
                break
            g.path(line_d((0, y), (W, y)), stroke='grid', sw=1.4, opacity=0.5)
            k += 1
        grid = g.render(ss=1)
        m = (((np.abs(nx) - 0.42) / 0.5).clip(0, 1) * ((yy - hy) / (H - hy)).clip(0, 1) ** 0.8 * 0.42)
        ga = np.asarray(grid.split()[3]).astype(np.float32) * m
        grid.putalpha(Image.fromarray(ga.clip(0, 255).astype(np.uint8)))
        im.alpha_composite(grid)

    # embers only in the outer ring
    rng_boxes = ((0, 0, 360, H), (W - 360, 0, W, H), (0, 0, W, 120), (0, H - 140, W, H))
    for i, b in enumerate(rng_boxes):
        if LOOK['bd_embers']:
            n, cols, size, alpha = LOOK['bd_embers']
            im = embers(im, b, n, 300 + i + (50 if kind == 'sb' else 0), colors=cols, size=size, alpha=alpha)
        else:
            im = embers(im, b, 16, 300 + i + (50 if kind == 'sb' else 0), size=(1.4, 3.6), alpha=(110, 230))

    if kind == 'pm':
        # top-right: THE DEAD / NEVER REST, small and wide, cyan underline (above the right panel)
        (x0, x1), _ = put_text(im, 'THE DEAD', 17, 50, 'lav', right=1846, track=0.62)
        (x0, x1), _ = put_text(im, 'NEVER REST', 17, 78, 'lav', right=1846, track=0.62)
        t = Svg(W, H)
        t.tube(line_d((1846 - 78, 92), (1846, 92)), 'cyan', 2.2, glow=0.7)
        t.tube(line_d((58, 1046), (130, 1046)), 'cyan', 2.0, glow=0.6)
        im.alpha_composite(t.render(ss=1))
        put_text(im, 'A HIGHER ROUND AWAITS...', 15, 1068, 'lav', x=58, track=0.45)
    else:
        sign(im, 1438, 26)
        t = Svg(W, H)
        t.tube(line_d((58, 1012), (150, 1012)), 'cyan', 2.2, glow=0.6)
        t.slashes(1716, 1068, 74, 1, 'cyan', 2.6, glow=0.7, lean=0.25)
        im.alpha_composite(t.render(ss=1))
        put_text(im, 'A HIGHER ROUND AWAITS...', 17, 1040, 'lav', x=58, track=0.5)
        for i, w in enumerate(('SURVIVE', 'UPGRADE', 'DOMINATE')):
            put_text(im, w, 15, 1020 + i * 24, 'lav', right=1886, track=0.5)
    return im


def sign(im, x, y):
    """THE DEAD / NEVER REST as a real neon sign: a dark bolted plate, two lines of magenta tube
    lettering, tilted like it is hung off the tower (scoreboard backdrop, docs/184b)."""
    W, H = 300, 170
    s = Svg(W, H)
    pl = chamfer(10, 10, W - 10, H - 10, tl=14, br=14)
    s.glow_fill(pl, 'magenta', 0.18, 14)
    s.plate(pl, 'plate')
    s.steel(pl, 2.2)
    for bx, by in ((22, 22), (W - 22, 22), (22, H - 22), (W - 22, H - 22)):
        s.circle(bx, by, 3.6, fill='header', stroke='steel_hi', sw=1.2)
    p = s.render()
    neon_word(p, 'THE DEAD', 38, 74, 'magenta', cx=W / 2, track=0.08, glow_r=7, glow_k=1.3)
    neon_word(p, 'NEVER REST', 38, 130, 'magenta', cx=W / 2, track=0.08, glow_r=7, glow_k=1.3)
    big = Image.new('RGBA', (W + 60, H + 60), (0, 0, 0, 0))
    big.alpha_composite(p, (30, 30))
    big = big.rotate(5, resample=Image.BICUBIC, expand=False)
    _paste(im, big, x - 30, y - 30)


PL_OUT = [(8, 112), (170, 26), (300, 26), (322, 8), (1434, 8), (1460, 34), (1460, 1162), (1430, 1192), (40, 1192), (8, 1160)]


def pm_panel_left():
    W, H = 1468, 1196
    HB = [(306, 40), (330, 16), (1426, 16), (1426, 176), (306, 176)]
    RB = chamfer(788, 26, 934, 134, tl=10, br=10)
    IF = chamfer(64, 192, 1452, 1072, tl=24, tr=10, br=24, bl=10)
    TAG = chamfer(1036, 1104, 1446, 1180, tl=14, br=8)
    texts = []

    def base(s):
        s.plate(PL_OUT, 'panel', top='plate_top')
        s.path(poly_d(HB), fill='url(#%s)' % s.lin([(0, 'header_top', 1), (1, PAL['header'], 1)]))
        s.steel(HB, 1.6, opacity=0.8)
        s.path(poly_d(IF), fill='inner')
        s.steel(IF, 2.0)
        s.steel([(88, 312), (1430, 312)], 1.6, close=False, opacity=0.8)
        s.plate(RB, 'plate')
        s.plate(TAG, 'plate', sheen=0)
        s.steel(TAG, 1.6)
        scratches(s, (80, 330, 1440, 1060), 46, 11, opacity=0.045)
        scratches(s, (330, 20, 1420, 170), 10, 12, opacity=0.04)
        # the cyber city in the bottom band: dark everywhere, lit only between the two text slots
        skyline(s, (14, 1096, 1454, 1190), 23, neon_x=[(700, 1022)])
        circuit(s, [(1452, 1000), (1440, 1000), (1440, 940), (1428, 928)], 'violet', 0.45)
        circuit(s, [(64, 760), (52, 760), (52, 700), (40, 688)], 'violet', 0.35)

    def top(s):
        frame_light(s, PL_OUT, [(8, 9, 10, 11), (4, 5, 6, 7)], 3.2, 0.95)
        s.steel(inset(PL_OUT, 9), 1.2, color='steel_hi', opacity=0.35)
        s.tube(line_d((318, 142), (1408, 142)), 'hrule', 2.0, glow=0.55)
        s.tube(poly_d(RB), 'violet', 2.2, glow=0.45)
        s.tube(line_d((1038, 1104), (1432, 1104)), 'violet', 1.8, glow=0.4)
        # YOUR UPGRADES rule + the // before the stacked words
        s.tube(line_d((712, 268), (1104, 268)), 'cyan', 3.0, glow=0.7)
        s.slashes(1150, 302, 58, 2, 'cyan', 3.0, gap=20, glow=0.75)
        s.bracket(72, 1064, 1, -1, 26, 'cyan', 2.0, glow=0.5)
        s.bracket(1444, 200, -1, 1, 26, 'cyan', 2.0, glow=0.5)

    im = layered(W, H, base, top, seed=101)
    put_text(im, 'TOWER OF DOOM II', 40, 72, 'white', x=318, track=0.04)
    put_text(im, 'ROUND BASED ZOMBIES', 17, 106, 'lav', x=320, track=0.42)
    tagline(im, 'FIGHT. UPGRADE. SURVIVE. REPEAT.', 12.5, 166, 622, 16)
    put_text(im, 'ROUND', 15, 52, 'lav', cx=861, track=0.25)
    (a, b), _ = put_text(im, 'YOUR', 58, 286, 'white', x=118, track=0.03)
    neon_word(im, 'UPGRADES', 58, 286, 'magenta', x=b + 26, track=0.03)
    for i, w in enumerate(('STRONGER', 'DEADLIER', 'FURTHER')):
        put_text(im, w, 15.5, 250 + i * 25, 'lav', x=1222, track=0.36, oblique=0.2)
    tag_group(im, 'ZOMBIES MODE', 'TOWER OF DOOM II', (1036, 1446), 14.5, 1150)
    im = specks(im, (12, 1000, 120, 1190), 10, 31, size=(0.8, 2.0), alpha=(40, 130))
    im = specks(im, (1380, 14, 1458, 120), 7, 32, size=(0.8, 2.0), alpha=(40, 130))
    return im


PR_OUT = [(8, 40), (40, 8), (596, 8), (618, 28), (860, 28), (888, 56), (888, 1168), (858, 1198), (38, 1198), (8, 1168)]


def pm_panel_right():
    W, H = 896, 1208

    def base(s):
        s.plate(PR_OUT, 'panel', top='plate_top')
        scratches(s, (30, 240, 870, 1180), 34, 21, opacity=0.045)
        circuit(s, [(14, 1120), (30, 1120), (30, 1060), (44, 1046)], 'violet', 0.4)
        circuit(s, [(882, 1120), (866, 1120), (866, 1070), (852, 1056)], 'violet', 0.4)

    def top(s):
        frame_light(s, PR_OUT, [(0, 1, 2), (6, 7, 8, 9)], 3.2, 0.95)
        s.steel(inset(PR_OUT, 9), 1.2, color='steel_hi', opacity=0.35)

    im = layered(W, H, base, None, seed=102)
    # the hologram skull, top-right, fading into the panel
    sk = Svg(W, H)
    skull(sk, 572, 18, 1.0, opacity=0.9)
    face = sk.render()
    face = fade_alpha(face, (0, 0, W, 336), 'bottom', 130)
    face = fade_alpha(face, (560, 0, W, H), 'left', 90)
    im.alpha_composite(clip_to(face, PR_OUT))
    t = Svg(W, H)
    top(t)
    t.tube(line_d((60, 226), (836, 226)), 'hrule', 2.0, glow=0.6)
    t.bracket(22, 1184, 1, -1, 22, 'cyan', 2.0, glow=0.5)
    im.alpha_composite(t.render())
    im = specks(im, (16, 14, 140, 120), 8, 33, size=(0.8, 2.0), alpha=(40, 130))
    im = specks(im, (760, 1100, 884, 1196), 8, 34, size=(0.8, 2.0), alpha=(40, 130))
    return im


def pm_footer_flavor():
    W, H = 800, 40
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    (a, b), _ = put_text(im, 'DEATH FUNDS A BRIGHTER TOMORROW', 19, 31, 'lav', x=6, track=0.42, fit=700)
    t = Svg(W, H)
    t.slashes(b + 16, 34, 24, 1, 'cyan', 3.0, glow=0.7, lean=0.36)
    im.alpha_composite(t.render())
    return im


def reset_badge(s, cx, cy, h):
    """The reset warning: an amber triangle, a dark cracked chevron through it, no letter."""
    tri = [(cx, cy - h * 0.5), (cx + h * 0.56, cy + h * 0.42), (cx - h * 0.56, cy + h * 0.42)]
    # the amber reset mark is a WARNING sign, not chrome: its colours are its own in every theme (literals)
    s.path(poly_d(tri), fill='#FF8A3D', opacity=0.55, filt=s.blur(h * 0.12))
    s.path(poly_d(tri), fill='url(#%s)' % s.lin([(0, '#FFD27A', 1), (1, '#FF8A3D', 1)]), stroke='#1A0E06', sw=h * 0.08, join='round')
    crack = [(cx - h * 0.02, cy - h * 0.26), (cx + h * 0.1, cy - h * 0.02), (cx - h * 0.08, cy + h * 0.06), (cx + h * 0.06, cy + h * 0.3)]
    s.path(poly_d(crack, False), stroke='#1A0E06', sw=h * 0.09, join='miter')


def pm_legend_reset():
    W, H = 800, 40
    s = Svg(W, H)
    reset_badge(s, 24, 21, 32)
    im = s.render()
    put_text(im, 'RESETS WHEN YOUR CLASS TIER GOES UP', 18, 30, 'lav', x=54, track=0.38, fit=730)
    return im


def pm_title(word, sub):
    W, H = 1024, 248
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if LOOK['title_glow']:
        (a, b), _ = put_text(im, word, 92, 150, 'white', x=26, track=0.02, glow='violet', glow_r=14, glow_k=0.45)
    else:
        put_text(im, word, 92, 154, 'title_shadow', x=30, track=0.02)
        (a, b), _ = put_text(im, word, 92, 150, 'white', x=26, track=0.02)
    t = Svg(W, H)
    t.slashes(b + 26, 150, 84, 2, 'cyan', 6.0, gap=30, glow=0.9)
    im.alpha_composite(t.render())
    put_text(im, sub, 20, 214, 'lav', x=30, track=0.95)
    return im


def row_card(W, H, card, well, violet, seed):
    def base(s):
        s.plate(card, 'plate', top='row_top')
        if violet:
            s.glow_fill(inset(card, 10), 'dark_twin', 0.16 * LOOK['twin_wash'], 26)
        s.path(poly_d(well), fill='url(#%s)' % s.rad([(0, mix('dark_twin' if violet else 'cyan', 'void', 0.82), 1), (1, 'void', 1)]))
        s.steel(card, 1.8, opacity=0.9)
        bevel(s, card)
        scratches(s, (W * 0.55, 8, W - 12, H - 8), 6, seed, opacity=0.05, length=(20, 60))

    def top(s):
        if violet:
            s.tube(poly_d(card), 'dark_twin', 2.4, glow=0.85, spread=0.6)
        else:
            # the content card's accent run: violet along the top + the right chamfer
            run = [card[1], card[2], card[3], card[4]] if len(card) > 4 else card[:2]
            s.tube(poly_d(run, False), 'violet', 2.0, glow=0.4, spread=0.6)
        s.tube(poly_d(well), 'dark_twin' if violet else 'cyan', 2.4, glow=0.75, spread=0.6)

    im = layered(W, H, base, top, seed=seed)
    # a few glitch specks in the bottom-right corner (the red set's splatter, in neon)
    return specks(im, (W - 70, H - 40, W - 14, H - 8), 4, seed + 1, colors=('violet', 'magenta'), size=(0.6, 1.4), alpha=(50, 120))


def pm_row(violet=False):
    W, H = 1024, 200
    card = chamfer(4, 6, 1020, 194, tl=10, tr=20, br=20, bl=10)
    well = chamfer(14, 18, 178, 182, tl=14, br=14)
    return row_card(W, H, card, well, violet, 41 if violet else 40)


def pip(kind):
    W = H = 64
    s = Svg(W, H)
    sq = chamfer(13, 13, 51, 51, tl=7, br=7)
    if kind == 'off':
        s.path(poly_d(sq), fill='void', stroke='pip_ring', sw=3.2)
    else:
        col = 'dark_twin' if kind == 'violet' else 'cyan'
        hot = 'pip_hot_twin' if kind == 'violet' else 'pip_hot'
        s.path(poly_d(sq), fill=col, opacity=0.6, filt=s.blur(7))
        s.path(poly_d(sq), fill='url(#%s)' % s.rad([(0, hot, 1), (0.45, mix(col, hot, 0.45), 1), (1, col, 1)], 0.42, 0.38, 0.7))
        s.path(poly_d(sq), stroke=mix(col, '#000000', 0.35), sw=2.0)
    return s.render(ss=4)


def pm_reset_mark():
    s = Svg(64, 64)
    reset_badge(s, 32, 33, 50)
    return s.render(ss=4)


def tile_btn(W, H, shape, focus, seed, divider=None, chevron=None):
    def base(s):
        if focus:
            s.plate(shape, 'focus_fill', top='focus_top')
            s.glow_fill(inset(shape, 6), 'cyan', 0.05 * LOOK['wash_k'], 18)
        else:
            s.plate(shape, 'plate', top='row_top')
        s.steel(shape, 1.8, opacity=0.9)
        bevel(s, shape)
        scratches(s, (12, 10, W - 12, H - 10), 5, seed, opacity=0.035, length=(20, 70))

    def top(s):
        if focus:
            s.tube(poly_d(shape), 'cyan', 3.0, glow=1.0, spread=0.55)
        else:
            ys = [p[1] for p in shape]
            yb = max(ys)
            s.tube(line_d((shape[0][0] + 26, yb), (W - 60, yb)), 'idle_edge', 1.6, glow=0.3, spread=0.5)
        if divider:
            x, y0, y1 = divider
            if focus:
                s.tube(line_d((x, y0), (x, y1)), 'cyan', 1.6, glow=0.4, spread=0.5)
            else:
                s.path(line_d((x, y0), (x, y1)), stroke='steel', sw=1.8)
        if chevron:
            cx, cy, ch = chevron
            if focus:
                s.chevron(cx, cy, ch, '#FFFFFF', 4.2)
                s.chevron(cx, cy, ch, 'cyan', 7, )
                s.chevron(cx, cy, ch, '#FFFFFF', 3.4)
            else:
                s.chevron(cx, cy, ch, 'lav', 3.6)

    return layered(W, H, base, top, seed=seed)


def pm_btn(focus=False):
    return tile_btn(1024, 112, chamfer(8, 8, 1016, 104, tl=14, br=18), focus, 50 + focus, divider=(180, 24, 88), chevron=(962, 56, 34))


def pm_iconbtn(focus=False):
    return tile_btn(324, 192, chamfer(8, 8, 316, 184, tl=16, br=16), focus, 52 + focus)


def pm_timebar():
    W, H = 1024, 100
    bar = chamfer(6, 6, 1018, 94, tl=12, br=16)

    def base(s):
        s.plate(bar, 'plate', top='row_top')
        s.steel(bar, 1.8, opacity=0.9)
        scratches(s, (20, 10, 560, 90), 5, 61, opacity=0.035)

    def top(s):
        s.tube(line_d((32, 34), (32, 66)), 'cyan', 2.6, glow=0.7)
        s.bracket(1010, 86, -1, -1, 22, 'magenta', 2.2, glow=0.6)

    im = layered(W, H, base, top, seed=60)
    put_text(im, 'GAME TIME', 26, 62, 'lav', x=54, track=0.58)
    return im


def pm_legend_box():
    W, H = 1024, 216
    box = chamfer(6, 6, 1018, 208, tl=18, br=18)

    def base(s):
        s.plate(box, 'plate', top='row_top')
        s.steel(box, 1.8, opacity=0.9)
        s.path(line_d((808, 28), (808, 188)), stroke='steel', sw=1.8)
        scratches(s, (180, 14, 800, 200), 6, 71, opacity=0.035)

    def top(s):
        s.tube(line_d((6, 64), (6, 24), (24, 6), (230, 6)), 'magenta', 2.8, glow=0.8, spread=0.55)
        s.tube(line_d((1018, 146), (1018, 190), (1000, 208), (796, 208)), 'magenta', 2.8, glow=0.8, spread=0.55)
        card_fan(s, 92, 108, 1.28)

    im = layered(W, H, base, top, seed=70)
    put_text(im, 'UPGRADE CARDS', 28, 80, 'infotext', x=186, track=0.12, glow='info_glow', glow_r=5, glow_k=0.35)
    for i, w in enumerate(('SAME', 'MAP', 'DIFFERENT', 'NIGHTMARE')):
        put_text(im, w, 14, 62 + i * 36, 'lav', x=834, track=0.34)
    return im

# ============================================================================== SCOREBOARD (184b)

ST_OUT = [(8, 88), (90, 8), (978, 8), (1004, 34), (1004, 112), (1028, 136), (1506, 136), (1530, 160), (1530, 492), (1504, 518), (34, 518), (8, 492)]


def sb_panel_top():
    W, H = 1536, 520
    HB = [(196, 14), (986, 14), (996, 24), (996, 112), (196, 112)]
    RB = chamfer(536, 16, 642, 96, tl=8, br=8)
    IF = chamfer(32, 140, 1506, 506, tl=16, tr=10, br=16, bl=10)

    def base(s):
        s.plate(ST_OUT, 'panel', top='plate_top')
        s.path(poly_d(HB), fill='url(#%s)' % s.lin([(0, 'header_top', 1), (1, PAL['header'], 1)]))
        s.steel(HB, 1.4, opacity=0.8)
        s.path(poly_d(IF), fill='inner')
        s.steel(IF, 1.8)
        s.path(line_d((1188, 152), (1188, 494)), stroke='steel', sw=1.6)
        s.plate(RB, 'plate')
        scratches(s, (70, 196, 1176, 496), 30, 81, opacity=0.045)
        circuit(s, [(1506, 300), (1494, 300), (1494, 250), (1482, 238)], 'violet', 0.4)

    im = layered(W, H, base, None, seed=80)
    sk = Svg(W, H)
    skull(sk, 1262, 150, 0.82, opacity=0.75)
    face = sk.render()
    face = fade_alpha(face, (0, 0, W, 502), 'bottom', 90)
    face = fade_alpha(face, (1200, 0, W, H), 'left', 80)
    im.alpha_composite(clip_to(face, inset(IF, 2)))

    t = Svg(W, H)
    frame_light(t, ST_OUT, [(2, 3, 4), (6, 7, 8, 9, 10, 11)], 3.0, 0.95, spread=0.8)
    t.steel(inset(ST_OUT, 8), 1.1, color='steel_hi', opacity=0.35)
    t.tube(line_d((204, 90), (984, 90)), 'hrule', 1.8, glow=0.5)
    t.tube(poly_d(RB), 'violet', 2.0, glow=0.45)
    t.tube(line_d((1216, 486), (1316, 486)), 'cyan', 2.2, glow=0.6)
    t.bracket(40, 498, 1, -1, 20, 'cyan', 1.8, glow=0.5)
    im.alpha_composite(t.render())
    put_text(im, 'TOWER OF DOOM II', 26, 48, 'white', x=206, track=0.04)
    put_text(im, 'ROUND BASED ZOMBIES', 12, 74, 'lav', x=207, track=0.42)
    tagline(im, 'FIGHT. UPGRADE. SURVIVE. REPEAT.', 9.5, 107, 394, 11)
    put_text(im, 'ROUND', 12, 36, 'lav', cx=589, track=0.25)
    (a, b), _ = put_text(im, 'YOUR', 34, 184, 'white', x=86, track=0.03)
    (a, b2), _ = neon_word(im, 'UPGRADES', 34, 184, 'magenta', x=b + 16, track=0.03)
    t = Svg(W, H)
    t.tube(line_d((b2 + 30, 172), (1160, 172)), 'cyan', 2.6, glow=0.7)
    im.alpha_composite(t.render())
    for i, w in enumerate(('MORE', 'ZOMBIES', 'HIGHER', 'STAKES')):
        put_text(im, w, 14, 400 + i * 24, 'lav', x=1216, track=0.36)
    im = specks(im, (1440, 150, 1526, 260), 8, 35, size=(0.8, 2.0), alpha=(40, 130))
    return im


def sb_panel_bottom():
    W, H = 1540, 280
    out = chamfer(8, 8, 1532, 272, tl=22, tr=10, br=22, bl=10)
    HS = chamfer(28, 78, 1512, 118, tl=8, br=8)

    def base(s):
        s.plate(out, 'panel', top='plate_top')
        s.path(poly_d(HS), fill='url(#%s)' % s.lin([(0, 'header_top', 1), (1, PAL['header'], 1)]))
        s.steel(HS, 1.6)
        scratches(s, (30, 124, 1510, 268), 22, 91, opacity=0.04)

    def top(s):
        frame_light(s, out, [(6, 7, 0, 1), (3, 4, 5)], 3.0, 0.95, spread=0.7)
        s.steel(inset(out, 8), 1.1, color='steel_hi', opacity=0.35)
        s.tube(line_d((36, 78), (220, 78)), 'cyan', 1.6, glow=0.4)

    im = layered(W, H, base, top, seed=90)
    (a, b), _ = put_text(im, 'MATCH', 38, 62, 'white', x=52, track=0.03)
    (a, b2), _ = neon_word(im, 'SCOREBOARD', 38, 62, 'magenta', x=b + 18, track=0.03)
    tag = 'DEATH FUNDS A BRIGHTER TOMORROW.'
    tw = text_width(tag, 13, 0.32)
    t = Svg(W, H)
    t.tube(line_d((b2 + 30, 50), (890, 50)), 'cyan', 2.6, glow=0.7)
    t.slashes(1490 - tw - 40, 62, 16, 2, 'cyan', 2.2, gap=8, glow=0.6)
    for cx in (90,):
        hash_sign(t, cx, 104, 13)
    im.alpha_composite(t.render(ss=4))
    put_text(im, tag, 13, 60, 'lav', right=1490, track=0.32)
    for word, cx in (('NAME', 277), ('TOTAL POINTS', 598), ('ELIMINATIONS', 803), ('CRITICAL KILLS', 1023), ('DOWNS', 1224), ('REVIVES', 1407)):
        put_text(im, word, 13, 104, 'infotext', cx=cx, track=0.3)
    im = specks(im, (1496, 10, 1530, 76) if LOOK['splatter'] else (1440, 12, 1528, 70), 6, 36, size=(0.8, 2.0), alpha=(40, 130))
    im = specks(im, (12, 200, 90, 270), 6, 37, size=(0.8, 2.0), alpha=(40, 130))
    return im


def sb_row(violet=False):
    W, H = 1024, 112
    card = chamfer(3, 4, 1021, 108, tl=8, tr=14, br=14, bl=8)
    well = chamfer(10, 10, 102, 102, tl=10, br=10)
    return row_card(W, H, card, well, violet, 43 if violet else 42)


def sb_player_row(local=False):
    W, H = 1536, 52
    bar = chamfer(22, 5, 1514, 47, tl=8, br=12)

    def base(s):
        if local:
            s.plate(bar, 'local_fill', top='local_top')
            s.glow_fill(inset(bar, 6), 'magenta', 0.08 * LOOK['wash_k'], 14)
        else:
            s.plate(bar, 'plate', top='row_idle_top')
        s.steel(bar, 1.5, opacity=0.85)

    def top(s):
        if local:
            s.tube(poly_d(bar), 'magenta', 2.2, glow=0.9, spread=0.45)

    return layered(W, H, base, top, seed=95 + local)


def sb_points():
    W, H = 480, 104
    plate = chamfer(6, 6, 474, 98, tl=14, br=14)

    def base(s):
        s.plate(plate, 'plate', top='row_top')
        s.steel(plate, 1.6)

    def top(s):
        s.tube(poly_d(plate), 'magenta', 2.6, glow=0.85, spread=0.5)
        s.path(line_d((96, 50), (168, 50)), stroke='steel', sw=1.4, opacity=0.8)

    im = layered(W, H, base, top, seed=97)
    # the points glyph IS the typeface's '$' cell (i_tod_hud_lmoney: the barred Z the HUD prints points with)
    put_text(im, '$', 80, 87, 'gold', cx=54, glow='gold', glow_r=7, glow_k=0.6)
    put_text(im, 'POINTS', 14, 40, 'white', x=98, track=0.22)
    return im

# ====================================================================== CARD PANEL CHROME (Map 1 copies)

def banner(kind):
    """The deal / draft banner (900x140, drawn 600x93): a dark glass chamfered plate, magenta frame
    tube, the headline in white + one NEON word, the subline between two cyan rules."""
    W, H = 900, 140
    pl = chamfer(12, 10, 888, 130, tl=26, tr=10, br=26, bl=10)

    def base(s):
        s.glow_fill(pl, 'magenta', 0.12, 12)
        s.plate(pl, 'header', top='banner_top')
        s.steel(inset(pl, 9), 1.2, color='steel_hi', opacity=0.45)
        scratches(s, (30, 16, 870, 124), 8, 111 if kind == 'class' else 112, opacity=0.035)

    def top(s):
        s.tube(poly_d(pl), 'magenta', 3.4, glow=1.0, spread=0.5)

    im = layered(W, H, base, top, seed=110)
    if kind == 'class':
        # W3E 2026-10-05 (user: "should say Weapon not gun ... Only one class has guns"): WEAPON, and
        # UPGRADES for UPGRADE PATHS so the line fits the 640 band at its full 15 cap (the GUN line was
        # already squeezed to 14.75). LOCKSTEP tod_class_select.lua's no-art SubTitle;
        # tools/wording/wording_pass.py --check pins both.
        a_txt, b_txt, sub, sub_rgb = 'CHOOSE YOUR', 'CLASS', 'YOUR WEAPON AND UPGRADES - PERMANENT FOR THIS RUN', 'lav'
        sub_cap = 15
    else:
        a_txt, b_txt, sub, sub_rgb = 'UPGRADE', 'AVAILABLE', 'CHOOSE ONE', 'infotext'
        sub_cap = 18
    cap = 50
    gap = 18
    wa, wb = text_width(a_txt, cap, 0.03), text_width(b_txt, cap, 0.03)
    x0 = 450 - (wa + gap + wb) / 2
    put_text(im, a_txt, cap, 78, 'white', x=x0, track=0.03)
    neon_word(im, b_txt, cap, 78, 'magenta', x=x0 + wa + gap, track=0.03, glow_r=8)
    (sa, sb_), _ = put_text(im, sub, sub_cap, 113, sub_rgb, cx=450, track=0.3 if kind == 'up' else 0.2, fit=640)
    t = Svg(W, H)
    t.tube(line_d((40, 107), (sa - 18, 107)), 'cyan', 2.0, glow=0.6)
    t.tube(line_d((sb_ + 18, 107), (860, 107)), 'cyan', 2.0, glow=0.6)
    if kind == 'up':
        for cx in (96, 804):
            for k, yy in enumerate((52, 72)):
                t.tube(line_d((cx - 16, yy + 10), (cx, yy - 6), (cx + 16, yy + 10)), 'cyan', 3.2, glow=0.8 - 0.3 * k)
    else:
        for cx in (70, 830):
            t.tube(poly_d([(cx, 46), (cx + 12, 58), (cx, 70), (cx - 12, 58)]), 'cyan', 2.4, glow=0.7)
    im.alpha_composite(t.render())
    return im


def title_plate():
    W, H = 1024, 128
    hexp = [(16, 64), (62, 20), (962, 20), (1008, 64), (962, 108), (62, 108)]

    def base(s):
        s.plate(hexp, 'plate', top='title_top')
        s.steel(inset(hexp, 8), 1.2, color='steel', opacity=0.8)

    def top(s):
        s.tube(poly_d(hexp), 'violet', 3.0, glow=0.75, spread=0.6)
        for cx in (84, 940):
            s.tube(poly_d([(cx, 56), (cx + 8, 64), (cx, 72), (cx - 8, 64)]), 'cyan', 2.0, glow=0.7)

    return layered(W, H, base, top, seed=120)


HP = chamfer(9, 7, 451, 63, tl=12, br=12)     # the hint-plate chassis, 460 x 70 (uncompressed in the GDT)


def hint_chassis(state='idle'):
    W, H = 460, 70

    def base(s):
        if state == 'locked':
            s.plate(HP, 'lockin_fill', top='lockin_top')
            s.glow_fill(inset(HP, 8), 'cyan', 0.12 * LOOK['wash_k'] ** 0.5, 12)
        else:
            s.plate(HP, 'plate', top='plate_top')
        s.steel(HP, 1.6, opacity=0.9)

    def top(s):
        if state == 'locked':
            s.tube(poly_d(HP), 'cyan', 2.6, glow=1.0, spread=0.38)
        else:
            s.tube(line_d((HP[0][0] + 20, 63), (430, 63)), 'idle_edge', 1.6, glow=0.35, spread=0.4)
            s.tube(line_d((30, 7), (HP[2][0] - 4, 7)), 'violet', 1.2, glow=0.0)

    return layered(W, H, base, top, grain_amp=0.02, seed=130)


def hint_frame():
    return hint_chassis()


def hold_plate():
    """HOLD [ gap ] TO LOCK. The gap is the Lua's: x169..286, centre 227.5, ink centred on y 33.5
    (tod_upgrade.lua / tod_class_select.lua PLATE_GAP_CX / _W / PLATE_INK_CY)."""
    im = hint_chassis()
    put_text(im, 'HOLD', 24, 45.5, 'white', right=165, track=0.06)
    put_text(im, 'TO LOCK', 24, 45.5, 'white', x=290, track=0.06)
    return im


def hint_locked():
    im = hint_chassis('locked')
    put_text(im, 'LOCKED IN', 30, 49, 'white', cx=230, track=0.08, glow='cyan', glow_r=6, glow_k=0.8)
    if LOOK['sparkles']:
        t = Svg(460, 70)
        sparkle(t, 428, 16, 7)
        sparkle(t, 32, 56, 5.5)
        im.alpha_composite(t.render(ss=4))
    return im


def key_blank_wide():
    """The pale keycap TodKeycap writes a key name into. Its BRIGHT FACE stays at x29..354,
    y19..148 (TodKeycap FACE_X 0.076 / FACE_CY 0.435 were measured off it), dark ink reads on it."""
    W, H = 384, 192
    s = Svg(W, H)
    body = chamfer(22, 12, 362, 188, tl=18, tr=18, br=18, bl=18)
    s.path(poly_d(body), fill='violet', opacity=0.28, filt=s.blur(6))
    s.path(poly_d(body), fill='glass')
    lip = chamfer(26, 60, 358, 184, br=16, bl=16)
    s.path(poly_d(lip), fill='url(#%s)' % s.lin([(0, 'steel_hi', 1), (1, 'key_lip_lo', 1)]))
    face = chamfer(29, 19, 355, 148, tl=14, tr=14, br=14, bl=14)
    s.path(poly_d(face), fill='url(#%s)' % s.lin([(0, 'key_face_hi', 1), (0.7, 'key_face_mid', 1), (1, 'key_face_lo', 1)]))
    s.path(line_d((44, 24), (340, 24)), stroke='#FFFFFF', sw=3, opacity=0.8)
    s.tube(line_d((40, 152), (344, 152)), 'accent2', 2.2, glow=0.55, spread=0.5)
    return s.render(ss=4)


def timer_track():
    W, H = 460, 24
    s = Svg(W, H)
    tr = chamfer(3, 4, 457, 20, tl=6, tr=6, br=6, bl=6)
    s.path(poly_d(tr), fill='url(#%s)' % s.lin([(0, 'deep', 1), (0.5, 'glass', 1), (1, 'deep', 1)]))
    s.tube(poly_d(tr), 'violet', 1.6, glow=0.55, spread=0.35)
    s.path(line_d((10, 7), (450, 7)), stroke='steel', sw=1.0, opacity=0.6)
    return s.render(ss=4)


def timer_fill():
    """A white-hot cyan tube. Its core stays near-WHITE on purpose: the draft clock multiplies the
    fill by (1.0, 0.25, 0.30) in its last seconds (tod_class_select.lua TIME_DANGER), and only a
    bright core turns that into a readable warning colour."""
    W, H = 460, 24
    s = Svg(W, H)
    bar = chamfer(9, 8, 451, 16, tl=3, tr=3, br=3, bl=3)
    s.path(poly_d(bar), fill='timer', opacity=0.55, filt=s.blur(2.2))
    s.path(poly_d(bar), fill='url(#%s)' % s.lin([(0, 'timer_lo', 1), (0.42, 'timer_hot', 1), (0.62, 'timer_mid', 1), (1, 'timer_edge', 1)]))
    return s.render(ss=4)


def pad_button_a():
    s = Svg(256, 256)
    texts = []
    pad_a(s, texts, 128, 128, 88, cap=104)
    im = s.render(ss=2)
    for f in texts:
        f(im)
    return im


def pad_dpad(side):
    s = Svg(256, 256)
    dpad(s, 128, 128, 214, lit=side, arrows=True)
    return s.render(ss=2)

# =================================================================================== the manifest

IMAGES = [
    # 184a pause menu (20)
    ('i_tod_pm_backdrop', pm_backdrop),
    ('i_tod_pm_panel_left', pm_panel_left),
    ('i_tod_pm_panel_right', pm_panel_right),
    ('i_tod_pm_footer_flavor', pm_footer_flavor),
    ('i_tod_pm_legend_reset', pm_legend_reset),
    ('i_tod_pm_title_pause', lambda: pm_title('PAUSE MENU', 'GAME NOT OVER YET')),
    ('i_tod_pm_title_gameover', lambda: pm_title('GAME OVER', 'RESTART OR WALK AWAY')),
    ('i_tod_pm_title_settings', lambda: pm_title('SETTINGS', 'TUNE YOUR NIGHTMARE')),
    ('i_tod_pm_row', lambda: pm_row(False)),
    ('i_tod_pm_row_violet', lambda: pm_row(True)),
    ('i_tod_pm_pip_on', lambda: pip('on')),
    ('i_tod_pm_pip_off', lambda: pip('off')),
    ('i_tod_pm_pip_on_violet', lambda: pip('violet')),
    ('i_tod_pm_reset_mark', pm_reset_mark),
    ('i_tod_pm_iconbtn', lambda: pm_iconbtn(False)),
    ('i_tod_pm_iconbtn_focus', lambda: pm_iconbtn(True)),
    ('i_tod_pm_timebar', pm_timebar),
    ('i_tod_pm_btn', lambda: pm_btn(False)),
    ('i_tod_pm_btn_focus', lambda: pm_btn(True)),
    ('i_tod_pm_legend_box', pm_legend_box),
    # 184b scoreboard (8)
    ('i_tod_sb_backdrop', sb_backdrop),
    ('i_tod_sb_panel_top', sb_panel_top),
    ('i_tod_sb_panel_bottom', sb_panel_bottom),
    ('i_tod_sb_row', lambda: sb_row(False)),
    ('i_tod_sb_row_violet', lambda: sb_row(True)),
    ('i_tod_sb_player_row', lambda: sb_player_row(False)),
    ('i_tod_sb_player_row_local', lambda: sb_player_row(True)),
    ('i_tod_sb_points', sb_points),
    # card panel chrome, the Map 1 copies (16)
    ('i_tod_banner_choose_class', lambda: banner('class')),
    ('i_tod_banner_upgrade', lambda: banner('up')),
    ('i_tod_title_plate', title_plate),
    ('i_tod_hint_frame', hint_frame),
    ('i_tod_hint_locked', hint_locked),
    ('i_tod_hold_plate', hold_plate),
    ('i_tod_key_blank_wide', key_blank_wide),
    ('i_tod_timer_fill', timer_fill),
    ('i_tod_timer_track', timer_track),
    ('i_tod_pad_button_a', pad_button_a),
    ('i_tod_pad_dpad_left', lambda: pad_dpad('left')),
    ('i_tod_pad_dpad_right', lambda: pad_dpad('right')),
]

# The three 460x70 hint plates are UNCOMPRESSED in tod_ui_images.gdt, so the converter's
# multiple-of-4 rule does not bind them; they keep 460x70 because the Lua derives its plate
# geometry from 460/70 (PLATE_ASPECT) - a different height would stretch every glyph gap.
UNCOMPRESSED_ANY_SIZE = {'i_tod_hint_frame', 'i_tod_hint_locked', 'i_tod_hold_plate'}

# on-screen size at 1080p (canvas units x 1.5), read off the Lua rects (for the review sheet)
ONSCREEN = {
    'i_tod_pm_backdrop': (960, 540), 'i_tod_sb_backdrop': (960, 540),        # shown at HALF; the screens sheet is real size
    'i_tod_pm_panel_left': (1197, 975), 'i_tod_pm_panel_right': (648, 874),
    'i_tod_pm_footer_flavor': (489, 24), 'i_tod_pm_legend_reset': (489, 24),
    'i_tod_pm_title_pause': (370, 90), 'i_tod_pm_title_gameover': (370, 90), 'i_tod_pm_title_settings': (370, 90),
    'i_tod_pm_row': (514, 100), 'i_tod_pm_row_violet': (514, 100),
    'i_tod_pm_pip_on': (14, 14), 'i_tod_pm_pip_off': (14, 14), 'i_tod_pm_pip_on_violet': (14, 14), 'i_tod_pm_reset_mark': (26, 26),
    'i_tod_pm_iconbtn': (117, 69), 'i_tod_pm_iconbtn_focus': (117, 69), 'i_tod_pm_timebar': (558, 54),
    'i_tod_pm_btn': (558, 61), 'i_tod_pm_btn_focus': (558, 61), 'i_tod_pm_legend_box': (630, 133),
    'i_tod_sb_panel_top': (1760, 596), 'i_tod_sb_panel_bottom': (1768, 321), 'i_tod_sb_row': (590, 65), 'i_tod_sb_row_violet': (590, 65),
    'i_tod_sb_player_row': (1760, 60), 'i_tod_sb_player_row_local': (1760, 60), 'i_tod_sb_points': (354, 77),
    'i_tod_banner_choose_class': (900, 140), 'i_tod_banner_upgrade': (900, 140), 'i_tod_title_plate': (900, 69),
    'i_tod_hint_frame': (333, 51), 'i_tod_hint_locked': (333, 51),
    'i_tod_hold_plate': (333, 51),
    'i_tod_key_blank_wide': (86, 43), 'i_tod_timer_fill': (420, 21), 'i_tod_timer_track': (420, 21),
    'i_tod_pad_button_a': (42, 42), 'i_tod_pad_dpad_left': (72, 72), 'i_tod_pad_dpad_right': (72, 72),
}


# THE CODE HALF OF THE THEME (docs/184 "Code tints"; RT 2026-10-05): the pause menu + scoreboard paint their live
# numbers / held-row icons / focus glyph in the theme's accent, so the Lua carries the theme too. Each theme's lines
# must be PRESENT and the other theme's ABSENT (the synthwave pass forbade the red lines; the red return requires them
# and forbids the magenta ones - the old contract survives as the synthwave half and as tint_selftest's control).
_SM = os.path.join('ui', 'uieditor', 'menus', 'StartMenu', 'AetheriumStartMenu.lua')
_SB = os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'AetheriumScoreboard.lua')
_PL = os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodPull.lua')      # THE PULL's unlit pips
CODE_TINTS = {
    'fallen': {
        _SM: ['local PM_RED    = { 0.95, 0.13, 0.23 }', 'RoundNumber:setRGB( 0.98, 0.11, 0.22 )',
              'GameTimeValue:setRGB( 0.98, 0.11, 0.22 )', 'focused and PM_RED or PM_IDLE'],
        _SB: ['or { 0.95, 0.13, 0.23 } ) )', 'round_number:setRGB( 0.98, 0.11, 0.22 )'],
        _PL: ['and { 0.80, 0.84, 0.94 } or { 0.20, 0.21, 0.26 } )', 'pull.bigRow.setRGB( col[ 1 ], col[ 2 ], col[ 3 ] )'],
    },
    'synthwave': {
        _SM: ['local PM_RED    = { 1.00, 0.17, 0.82 }', 'RoundNumber:setRGB( 1.00, 0.17, 0.82 )',
              'GameTimeValue:setRGB( 1.00, 0.17, 0.82 )', 'focused and { 0.12, 0.90, 1.00 } or PM_IDLE'],
        _SB: ['or { 1.00, 0.17, 0.82 } ) )', 'round_number:setRGB( 1.00, 0.17, 0.82 )'],
        _PL: ['and { 0.80, 0.84, 0.94 } or { 0.14, 0.17, 0.30 } )',
              'pull.bigRow.setRGB( pull.bannerImg and 0.06 or col[ 1 ], pull.bannerImg and 0.06 or col[ 2 ], pull.bannerImg and 0.10 or col[ 3 ] )'],
    },
}


def tint_problems(src_by_rel, theme=None):
    """{rel: source} -> the code-tint breaks for `theme` (default THEME): a line of this theme missing, or a line of
    the other theme still there."""
    theme = theme or THEME
    out = []
    for rel, needles in CODE_TINTS[theme].items():
        src = src_by_rel[rel]
        for nd in needles:
            if nd not in src:
                out.append('%s: the %s tint is missing: %s' % (rel, theme, nd))
        for other, table in CODE_TINTS.items():
            if other != theme:
                for nd in table[rel]:
                    if nd in src:
                        out.append('%s still paints the %s theme: %s' % (rel, other, nd))
    return out


def tint_selftest(src_by_rel):
    """NEGATIVE CONTROLS for tint_problems: the clean sources pass; the OTHER theme's lines (the pre-RT gate's own
    fixture: a red line under synthwave, a magenta line under fallen) and a missing line each fail."""
    bad = []
    if tint_problems(src_by_rel):
        return bad
    other = [t for t in CODE_TINTS if t != THEME][0]
    for rel, needles in CODE_TINTS[THEME].items():
        for i, nd in enumerate(needles):
            planted = dict(src_by_rel)
            planted[rel] = src_by_rel[rel].replace(nd, CODE_TINTS[other][rel][i])
            if not tint_problems(planted):
                bad.append('the %s line %r planted in %s was NOT caught' % (other, CODE_TINTS[other][rel][i], rel))
    return bad


def wiring_problems(lua_root):
    """Every image is a same-name drop-in, so its GDT block and zone line must already exist; the
    two menus must carry the THEME's code tints (CODE_TINTS)."""
    import glob, re
    out = []
    gdt = open(os.path.join(ROOT, 'source_data', 'tod_ui_images.gdt'), encoding='utf-8', errors='replace').read()
    zone = ''.join(open(z, encoding='utf-8', errors='replace').read() for z in glob.glob(os.path.join(ROOT, 'zone_source', '*.zone')))
    for name, _ in IMAGES:
        if not re.search(r'"%s"\s*\(\s*"image\.gdf"' % re.escape(name), gdt):
            out.append('%s: no GDT block in source_data/tod_ui_images.gdt' % name)
        if not re.search(r'^\s*image,%s\s*$' % re.escape(name), zone, re.M):
            out.append('%s: no zone image line' % name)
    srcs = {}
    for rel in CODE_TINTS[THEME]:
        p = os.path.join(lua_root, rel)
        if not os.path.exists(p):
            p = os.path.join(ROOT, rel)
        srcs[rel] = open(p, encoding='utf-8', errors='replace').read()
    out += tint_problems(srcs)
    out += ['tint gate blind: ' + m for m in tint_selftest(srcs)]
    return out


def build_all():
    out = {}
    for name, fn in IMAGES:
        im = fn().convert('RGBA')
        ref = Image.open(artgen.shipped(name))
        if im.size != ref.size:
            raise SystemExit('r3: %s is %s, the shipped image is %s - a drop-in keeps its size' % (name, im.size, ref.size))
        if name not in UNCOMPRESSED_ANY_SIZE and (im.width % 4 or im.height % 4):
            raise SystemExit('r3: %s %s is not a multiple of 4' % (name, im.size))
        out[name] = im
    return out

# ========================================================================================= review

def _onscreen(im, size):
    return im.resize(size, Image.LANCZOS)


def review_sheet(images, out_path, old_dir):
    """Each image beside what it replaces, BOTH at the size the game draws them at 1080p (the two
    backdrops at half: their real-size view is the screens sheet)."""
    from PIL import ImageFont
    bg = (16, 12, 26, 255)
    pad, lab = 18, 30
    font = ImageFont.truetype(artgen.TTF, 20)
    rows = []
    for name, _ in IMAGES:
        w, h = ONSCREEN[name]
        new = _onscreen(images[name], (w, h))
        old = _onscreen(Image.open(os.path.join(old_dir, name + '.png')).convert('RGBA'), (w, h))
        rows.append((name, old, new, w, h))
    W = max(2 * w + 3 * pad + 120 for _, _, _, w, _ in rows)
    H = sum(h + lab + pad * 2 for _, _, _, _, h in rows) + pad
    sheet = Image.new('RGBA', (W, H), bg)
    d = ImageDraw.Draw(sheet)
    y = pad
    for name, old, new, w, h in rows:
        note = '  (shown at HALF size)' if 'backdrop' in name else ''
        d.text((pad, y), '%s   %dx%d on screen at 1080p   OLD (left)  ->  NEW (right)%s' % (name, w, h, note), fill=(225, 220, 240, 255), font=font)
        y += lab
        # a mid-grey world patch under each so transparency and glow read
        for i, im in enumerate((old, new)):
            x = pad + i * (w + pad + 60)
            sheet.paste((44, 52, 64, 255), (x, y, x + w, y + h))
            sheet.alpha_composite(im, (x, y))
        d.text((pad + w + 14, y + h // 2 - 10), '->', fill=(31, 229, 255, 255), font=font)
        y += h + pad
    sheet.convert('RGB').save(out_path, optimize=True)
    return out_path


def _lua(lua_root, rel):
    p = os.path.join(lua_root, rel)
    if not os.path.exists(p):
        p = os.path.join(ROOT, rel)
    return open(p, encoding='utf-8', errors='replace').read()


def _pause_items(R, L, lua_root, cls, owned, companion):
    """render_menus.pause_items, but reading AetheriumStartMenu.lua from lua_root (the stage)."""
    g = L.globals()
    R.load_companion(L, companion)
    g.CoD.TodClass = cls
    g.CoD.TodClassTier = 2
    g.CoD.TodOwned = R.owned_table(L, owned)
    g.DataSources = L.table()
    L.execute(_lua(lua_root, os.path.join('ui', 'uieditor', 'menus', 'StartMenu', 'AetheriumStartMenu.lua')))
    menu = g.LUI.createMenu.StartMenu_Main(0)
    return [dict(x) for x in L.globals().DUMP(menu).values()]


def _scoreboard_items(R, L, lua_root, cls, owned, companion):
    g = L.globals()
    R.load_companion(L, companion)
    g.CoD.TodClass = cls
    g.CoD.TodOwned = R.owned_table(L, owned)
    L.execute(_lua(lua_root, os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'AetheriumScoreboard.lua')))
    root = g.LUI.UIElement.new()
    sb = g.CoD.AetheriumScoreboard.new(root, 0)
    root.addElement(root, sb)
    cps = sb.clipsPerState
    st = cps['Visible'] if cps else None
    if st and st.DefaultClip:
        st.DefaultClip()
    return [dict(x) for x in L.globals().DUMP(root).values()]


def render_screens(stage_dir, out_dir):
    """The real menus through the real Lua (tools/ui_mockup): pause + scoreboard OLD vs NEW, and
    the upgrade deal panel (render_pull) OLD vs NEW. Returns the png paths written."""
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'ui_mockup'))
    import render_menus as R
    shipped_dirs = list(R.IMG_DIRS)
    paths = []
    for tag, dirs in (('old', shipped_dirs), ('new', [stage_dir] + shipped_dirs)):
        R.IMG_DIRS[:] = dirs
        R._img_cache.clear()
        key, cards = R.CLASSES[2]
        lua_root = STAGE_ROOT if tag == 'new' else ROOT
        L = R.lua_runtime()
        items = _pause_items(R, L, lua_root, 2, {**cards, **R.SHARED, 24: (2, 3)}, R.COMPANION[2])
        p = os.path.join(out_dir, '_screen_pause_%s.png' % tag)
        R.draw(items, p)
        L = R.lua_runtime()
        items = _scoreboard_items(R, L, lua_root, 2, {**cards, **R.SHARED, 24: (2, 3)}, R.COMPANION[2])
        q = os.path.join(out_dir, '_screen_scoreboard_%s.png' % tag)
        R.draw(items, q)
        paths += [p, q]
    R.IMG_DIRS[:] = shipped_dirs
    os.chdir(ROOT)
    return paths


def pull_screens(stage_dir):
    """The upgrade deal panel (banner, hold plate, keycap / pad A, timers) via render_pull."""
    py = sys.executable
    tool = os.path.join(ROOT, 'tools', 'ui_mockup', 'render_pull.py')
    res = {}
    for tag, extra in (('r3_old', []), ('r3_new', ['--art-dir', stage_dir])):
        r = subprocess.run([py, tool, '--name', tag, '--fps', '6'] + extra, cwd=ROOT, capture_output=True, text=True)
        res[tag] = os.path.join(ROOT, 'tmp', 'ui_mockup', 'pull', tag)
        if r.returncode:
            print('render_pull %s failed:\n%s' % (tag, r.stderr[-2000:]))
    return res


def class_select_mock(get, out_path):
    """A hand-placed class-draft composite (no renderer exists for tod_class_select.lua): the
    banner at 104..197, four card slots, hold plates with the keycap / A, the switch glyphs, the
    draft clock - at the Lua's rects, on the in-game sky."""
    S = 1.5
    W, H = int(1280 * S), int(720 * S)
    sky = os.path.join(ROOT, 'docs', 'sky_preview', 'evil_ingame_city.png')
    canvas = Image.open(sky).convert('RGBA').resize((W, H), Image.LANCZOS) if os.path.exists(sky) else Image.new('RGBA', (W, H), (20, 16, 30, 255))
    dim = Image.new('RGBA', (W, H), (6, 4, 12, 150))
    canvas.alpha_composite(dim)

    def place(name, l, r, t, b):
        im = get(name).resize((int(round((r - l) * S)), int(round((b - t) * S))), Image.LANCZOS)
        canvas.alpha_composite(im, (int(round(l * S)), int(round(t * S))))

    place('i_tod_banner_choose_class', 340, 940, 104, 197)
    cards = ['i_tod_card_class_necromancer', 'i_tod_card_class_assault', 'i_tod_card_class_heavy', 'i_tod_card_class_slasher']
    for i, cn in enumerate(cards):
        x0 = 88 + i * 298
        p = artgen.shipped(cn)
        if os.path.exists(p):
            im = Image.open(p).convert('RGBA').resize((int(210 * S), int(315 * S)), Image.LANCZOS)
            canvas.alpha_composite(im, (int(x0 * S), int(210 * S)))
        pw, ph = 223, 34
        px = x0 + (210 - pw) / 2
        if i == 1:
            place('i_tod_hint_locked', px, px + pw, 529, 529 + ph)
        else:
            place('i_tod_hold_plate', px, px + pw, 529, 529 + ph)
            gcx = px + pw * 227.5 / 460
            gcy = 529 + ph * 33.5 / 70
            if i == 0:
                s = 14
                place('i_tod_pad_button_a', gcx - s, gcx + s, gcy - s, gcy + s)
            else:
                w = math.floor((pw * 118 / 460 - 2) / 2) * 2
                place('i_tod_key_blank_wide', gcx - w / 2, gcx + w / 2, gcy - w / 4, gcy + w / 4)
                put_text(canvas, 'SPACE', 8.5 * S, (gcy - w / 4 + w / 2 * 0.435) * S + 4.25 * S, INK, cx=gcx * S, track=0.04)
        place('i_tod_timer_track', x0 + 10, x0 + 200, 567, 577)
        place('i_tod_timer_fill', x0 + 10, x0 + 10 + 190 * (0.25 + 0.2 * i), 567, 577)
    place('i_tod_pad_dpad_left', 640 - 104, 640 - 56, 642, 690)
    place('i_tod_pad_dpad_right', 640 + 56, 640 + 104, 642, 690)
    put_text(canvas, 'SWITCH', 12 * S, 672 * S, 'lav', cx=640 * S, track=0.2)
    place('i_tod_timer_track', 500, 780, 620, 634)
    place('i_tod_timer_fill', 500, 640, 620, 634)
    canvas.convert('RGB').save(out_path, optimize=True)
    return out_path


def right_panel_mock(get, out_path, tint_focus, tint_time):
    """The pause menu's RIGHT panel assembled at the Lua's rects (AetheriumStartMenu.lua RArt,
    TodPmButton / TodPmIconButton insets, ButtonList spacing 4.7, SmallButtonList 18.6 * RS) -
    render_menus draws neither list, so this is where the buttons are seen in place."""
    S = 1.5
    RX, RY, RS = 830, 62, 0.482
    RA = lambda ax, ay: (RX + ax * RS, RY + ay * RS)
    W, H = int(1280 * S), int(720 * S)
    sky = os.path.join(ROOT, 'docs', 'sky_preview', 'evil_ingame_city.png')
    canvas = Image.open(sky).convert('RGBA').resize((W, H), Image.LANCZOS) if os.path.exists(sky) else Image.new('RGBA', (W, H), (20, 16, 30, 255))
    font = artgen.ttf

    def place(name, l, r, tp, b, rgb=None):
        im = get(name).resize((max(1, int(round((r - l) * S))), max(1, int(round((b - tp) * S)))), Image.LANCZOS)
        if rgb:
            ch = im.split()
            im = Image.merge('RGBA', [ch[i].point(lambda v, k=rgb[i]: int(v * k)) for i in range(3)] + [ch[3]])
        canvas.alpha_composite(im, (int(round(l * S)), int(round(tp * S))))

    def ttf_text(txt, l, tp, h, rgb, right=None):
        f = font(int(round(h * S)))
        d = ImageDraw.Draw(canvas)
        if right is not None:
            l = right - f.getlength(txt) / S
        d.text((l * S, tp * S), txt, font=f, fill=tuple(int(c * 255) for c in rgb) + (255,))

    place('i_tod_pm_backdrop', 0, 1280, 0, 720)
    a, b = RA(0, 0)
    c, d = RA(896, 1208)
    place('i_tod_pm_panel_right', a, c, b, d)
    a, b = RA(84, 56)
    c, d = RA(596, 180)
    place('i_tod_pm_title_pause', a, c, b, d)
    ix, iy = RA(98, 242)
    for k, g in enumerate(('graphics', 'audio', 'controls', 'settings')):
        x = ix + k * (78 + 18.6 * RS)
        place('i_tod_pm_iconbtn_focus' if k == 1 else 'i_tod_pm_iconbtn', x, x + 78, iy, iy + 46.2)
        place('i_tod_pm_gly_' + g, x + 25.5, x + 52.5, iy + 9.6, iy + 36.6, (0.93, 0.95, 1.0))
    a, b = RA(68, 376)
    c, d = RA(840, 451.4)
    place('i_tod_pm_timebar', a, c, b, d)
    vx0, vy0 = RA(502, 394)
    vx1, vy1 = RA(812, 432)
    ttf_text('0:03:29', vx0, vy0, vy1 - vy0, tint_time, right=vx1)
    lx, ly = RA(68, 474)
    items = (('RETURN TO GAME', 'return'), ('RESTART LEVEL', 'restart'), ('SWITCH TO THIRD PERSON', 'camera'),
             ('GAME SETTINGS', 'settings'), ('LEAVE GAME', 'leave'))
    bw, bh = 1024 * 0.3633, 112 * 0.3633
    for k, (label, g) in enumerate(items):
        y = ly + k * (bh + 4.7)
        foc = k == 0
        place('i_tod_pm_btn_focus' if foc else 'i_tod_pm_btn', lx, lx + bw, y, y + bh)
        place('i_tod_pm_gly_' + g, lx + 22.7, lx + 42.7, y + 10.3, y + 30.3, tint_focus if foc else (0.59, 0.64, 0.78))
        ttf_text(label, lx + 72, y + 13, 14.7, (1, 1, 1) if foc else (0.91, 0.93, 0.98))
    a, b = RA(22, 1024)
    c, d = RA(894, 1208)
    place('i_tod_pm_legend_box', a, c, b, d)
    cy = RY + 1171.5 * RS
    x = 918.6
    for k, (img, word) in enumerate((('i_tod_key_blank_wide', None), ('i_tod_key_blank_wide', 'SWITCH'), ('i_tod_key_blank_wide', 'LOCK'))):
        place(img, x, x + 44, cy - 11, cy + 11)
        put_text(canvas, ('Q', 'G', 'SPACE')[k], 9 * S if k < 2 else 6.5 * S, (cy - 11 + 22 * 0.435) * S + 4.5 * S * (1 if k < 2 else 0.72), INK, cx=(x + 22) * S, track=0.04)
        x += 44 + (2 if k == 0 else 5)
        if word:
            ttf_text(word, x, cy - 6.5, 13, (0.86, 0.9, 0.95))
            x += 46 + 10
    canvas.convert('RGB').save(out_path, optimize=True)
    return out_path


def screens_sheet(paths, out_path):
    from PIL import ImageFont
    font = ImageFont.truetype(artgen.TTF, 28)
    ims = [(os.path.basename(p), Image.open(p).convert('RGB')) for p in paths if os.path.exists(p)]
    w = 1920
    rows = []
    for i in range(0, len(ims), 2):
        pair = ims[i:i + 2]
        rows.append([(n, im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)) for n, im in pair])
    H = sum(max(im.height for _, im in r) + 50 for r in rows)
    sheet = Image.new('RGB', (w * 2 + 30, H), (16, 12, 26))
    d = ImageDraw.Draw(sheet)
    y = 0
    for r in rows:
        for j, (n, im) in enumerate(r):
            d.text((10 + j * (w + 30), y + 8), n, fill=(225, 220, 240), font=font)
            sheet.paste(im, (j * (w + 30), y + 46))
        y += max(im.height for _, im in r) + 50
    sheet.save(out_path, optimize=True)
    return out_path

# =========================================================================================== main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', action='store_true', help='also copy into tmp/redesign/%s/stage/' % PACK)
    ap.add_argument('--install', action='store_true', help='copy into source_data/tod_ui_images/_images (landing only)')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--against', choices=('installed', 'stage'), default='installed')
    ap.add_argument('--no-review', action='store_true')
    a = ap.parse_args()

    images = build_all()
    if a.check:
        where = artgen.IMG if a.against == 'installed' else STAGE_IMG
        bad = []
        for name, im in images.items():
            p = os.path.join(where, name + '.png')
            if not os.path.exists(p) or open(p, 'rb').read() != artgen.png_bytes(im):
                bad.append(name)
        if bad:
            print('R3 SYNTHWAVE CHECK FAILED: %d of %d differ from %s:' % (len(bad), len(images), where))
            for n in bad:
                print('   ', n)
            sys.exit(1)
        problems = wiring_problems(STAGE_ROOT if a.against == 'stage' else ROOT)
        if problems:
            print('R3 SYNTHWAVE WIRING FAILED:')
            for w in problems:
                print('   ', w)
            sys.exit(1)
        print('R3 SYNTHWAVE OK %d images + wiring (%s, theme %s)' % (len(images), a.against, THEME))
        return

    out = artgen.stage_dir(PACK)
    for name, im in images.items():
        artgen.save_png(im, os.path.join(out, name + '.png'), allow_any_size=name in UNCOMPRESSED_ANY_SIZE)
    print('wrote %d images -> %s' % (len(images), out))
    if a.stage or a.install:
        dest = artgen.IMG if a.install else STAGE_IMG
        os.makedirs(dest, exist_ok=True)
        for name in images:
            shutil.copyfile(os.path.join(out, name + '.png'), os.path.join(dest, name + '.png'))
        print('copied %d -> %s' % (len(images), dest))
    if not a.no_review:
        old_dir = BASE_IMG if os.path.isdir(BASE_IMG) else artgen.IMG
        review_sheet(images, os.path.join(out, '_review.png'), old_dir)
        print('review ->', os.path.join(out, '_review.png'))
        paths = render_screens(out, out)
        pull = pull_screens(out)
        for tag, d in pull.items():
            fr = sorted(f for f in os.listdir(d) if f.startswith('frame_')) if os.path.isdir(d) else []
            if fr:
                shutil.copyfile(os.path.join(d, fr[-1]), os.path.join(out, '_screen_deal_%s.png' % tag[3:]))
                paths.append(os.path.join(out, '_screen_deal_%s.png' % tag[3:]))
        oldget = lambda n: Image.open(os.path.join(old_dir, n + '.png')).convert('RGBA')
        oldget_all = lambda n: Image.open(os.path.join(old_dir if os.path.exists(os.path.join(old_dir, n + '.png')) else artgen.IMG, n + '.png')).convert('RGBA')
        newget = lambda n: images[n] if n in images else Image.open(artgen.shipped(n)).convert('RGBA')
        paths.append(class_select_mock(oldget, os.path.join(out, '_screen_draft_old.png')))
        paths.append(class_select_mock(newget, os.path.join(out, '_screen_draft_new.png')))
        paths.append(right_panel_mock(oldget_all, os.path.join(out, '_screen_rightpanel_old.png'), (0.95, 0.13, 0.23), (0.98, 0.11, 0.22)))
        paths.append(right_panel_mock(newget, os.path.join(out, '_screen_rightpanel_new.png'), (0.12, 0.90, 1.00), (1.00, 0.17, 0.82)))
        order = ['pause', 'rightpanel', 'scoreboard', 'deal', 'draft']
        paths = sorted(paths, key=lambda p: (next((i for i, k in enumerate(order) if k in p), 9), 'new' in p))
        screens_sheet(paths, os.path.join(out, '_review_screens.png'))
        print('screens ->', os.path.join(out, '_review_screens.png'))


if __name__ == '__main__':
    main()
