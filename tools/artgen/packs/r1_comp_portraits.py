"""r1_comp_portraits.py - the four AI COMPANION portraits, drawn as FLAT VECTOR art (W3D, 2026-10-05).

WHY (user 2026-10-05, item 4): "The AI companion images dont look that good. A bit too realistic ... these look veery
different from other assets. WHole entire asset library should look like one library". The R1 portraits (2026-10-04)
were TRACED from Cycles renders of the real robots and cel-shaded: their texture grunge, render normals and traced
outlines read as rendered 3D beside the Dealer, whose portraits (i_tod_spin_dealer_*) and the whole R3 / R4 synthwave
library are flat vector shapes. These four are now HAND-PLACED SVG shapes in the Dealer's language, keeping each robot's
REAL silhouette and parts (proportions taken from art/generated/R1-truth-renders/ and the W2A world models):

  CIVIL PROTECTOR  the SoE Civil Protector rig in its GOLD finish (PROTECTOR_FINISH, LOCKSTEP the world model):
                   tall helmet with the visor slit and the ear disc, ribbed neck, the two great pauldrons, the barrel
                   chest and its crest, the dark ribbed sleeves; head and chest behind the counter like the Dealer
  TALON            the BO3 attack drone: the long fuselage, the two side pods with their ducted LIFT FANS, the twin
                   swept fins, the tail stabilisers, the chin gun - hovering, the fans lit
  R.A.P.S.         Nikolai's rolling drum: the domed hub with its red star and sensor eye, the spiked rims, the
                   tread drum behind with its lit seams, the shell's green
  CERBERUS         the AMWS tracked gun platform: the armoured skirts and road wheels, the turret, the big ammo drum
                   and its feed belt, the rotary gun, the geodesic sensor dome

THE LANGUAGE (measured off i_tod_spin_dealer_*, the portrait in the frame beside it, and tools/artgen/synthwave.py):
  * a heavy near-black silhouette ink (OUT, ~2.6 px), thin ink between parts (IN, ~1.1 px)
  * flat fills, three or four tones per material (hi / base / lo / deep) from ONE key light (upper left), no texture
  * a thin RIM LIGHT of the set's colour just inside the silhouette on the edges that face the side lights
  * the robot's LIGHTS are the one neon accent: the companion's CYAN (the Dealer's are his red), a white-hot core,
    a soft halo of the hue (the R4 neon_glyph recipe: white-hot ink, one hue, a soft hue halo)
  * the SAME SET as the Dealer: the wall, two shelves, the tube lights, the neon bars and the counter, re-hued to the
    companion's cyan (TodSpinReel P3.GIFT / the HUD companion bar), so the pair reads red | cyan
  Red is the HUD's ENEMY colour (elites / bosses), so every companion light is cyan - the in-world Protector visor
  and the R.A.P.S. core glow red / orange; the portrait says ALLY. The R.A.P.S. keeps its painted red STAR (a marking,
  not a light).

OUTPUTS (TodSpinReel.lua ART.comp / ART.gift.icon, TodCompanionPlate.lua IMG.comp, LOCKSTEP names):
  i_tod_spin_comp_<c>       240 x 192  the portrait (the reel's portrait window, the pause / scoreboard AI COMPANION row)
  i_tod_spin_ico_comp_<c>   208 x 208  the gift tile's window + the companion plate: made by tools/partner_shop/
                                       make_gift_art.py's OWN make_icon() + encode() from the new portrait (its centre
                                       192 x 192), so that generator's build gate (--check) stays byte-exact
Each subject sits inside the portrait's centre 192 x 192 square (x 24..216), because that square IS the icon, and
clear of the icon's two chamfered corners.

PROTECTOR_FINISH: the in-game rig is the SoE Civil Protector in gold (tools/partner/install_assets.py, LOCKSTEP; read by
tools/partner/verify_assets.py with a regex - keep the line's form). "blue" draws the old blue enamel.

USAGE
  python tools/artgen/packs/r1_comp_portraits.py               write art/generated/W3D-companion-art/: both sets + _review.png
                                                               (OLD = installed vs NEW at 1080p: the reel's portrait frames
                                                               beside the Dealer, the icon, the gift tile, the companion plate,
                                                               the gift reel, the pause / scoreboard rows - drawn by the
                                                               shipping Lua under tools/ui_mockup; --no-review skips it)
  python tools/artgen/packs/r1_comp_portraits.py --stage DIR   also write both sets under DIR/source_data/tod_ui_images/_images/
  python tools/artgen/packs/r1_comp_portraits.py --check [--root DIR]
                                                               BUILD GATE: regenerate in memory; fail on any byte that differs
                                                               from the installed portraits (the icons are make_gift_art.py's)
  python tools/artgen/packs/r1_comp_portraits.py --selftest [--root DIR]
                                                               --check's negative controls: a changed pixel, a missing file, a
                                                               wrong size and an out-of-square pose must each be caught
Deterministic (no randomness, no timestamps; pure code - no external render inputs). Never hand-edit an output PNG.
Each subject is also refused if it leaves the icon square (ICON_X), so a pose edit cannot get cut by make_gift_art.
"""
import argparse, math, os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402

ROOT = artgen.ROOT
PACK = 'W3D-companion-art'
W, H, SS = 240, 192, 4
WS, HS = W * SS, H * SS
COMPANIONS = ['protector', 'talon', 'raps', 'cerberus']   # P3.COMPANIONS order (TodSpinReel / _tod_partners)
PROTECTOR_FINISH = 'gold'

CYAN = (31, 230, 255)            # TodSpinReel P3.GIFT.col { 0.12, 0.9, 1 } = synthwave PAL cyan
CYAN_HEX = '#1FE5FF'
CORE_HEX = '#E8FDFF'             # synthwave CORE['cyan']: the white-hot middle of a cyan tube
INK = (7, 6, 12)                 # the Dealer's outline
INK_HEX = '#07060C'
OUT = 3.1                        # px: the silhouette ink (the Dealer's measures 3: median near-black run)
IN = 1.2                         # px: ink between parts
# the Dealer's set, measured from i_tod_spin_dealer_idle and re-hued to the companion's cyan
WALL_TOP, WALL_LOW = (8, 26, 34), (4, 13, 18)
SHELF_LINE, SHELF_BAND = (24, 78, 92), (9, 31, 39)
COUNTER_LINE, COUNTER_TOP, COUNTER_LOW, COUNTER_FOOT = (150, 246, 255), (44, 112, 128), (20, 52, 60), (10, 25, 31)
COUNTER_Y = 165.2                # the counter's bright line (165.2 .. 166.8): a subject behind the counter stops here

# THE MATERIALS: flat tone steps (hi = faces the key light, base, lo = turned away, deep = underneath)
MAT = {
    'gold':  dict(hi='#EDC35A', base='#C98F2E', lo='#8A5A1B', deep='#553610', glint='#FFF1C2'),
    'blue':  dict(hi='#6F9BD6', base='#3F6BA8', lo='#284A7A', deep='#172C4A', glint='#E2F0FF'),
    'gun':   dict(hi='#6D7789', base='#4A5363', lo='#303743', deep='#1E222B', glint='#C9D3E2'),
    'dark':  dict(hi='#3C404C', base='#282B34', lo='#1A1C23', deep='#111217', glint='#6A7080'),
    'steel': dict(hi='#CBD4DB', base='#9AA5AF', lo='#66707A', deep='#3F464E', glint='#F2F7FA'),
    'shell': dict(hi='#88A890', base='#62806C', lo='#43594C', deep='#2A3930', glint='#D4E6D8'),
    'star':  dict(hi='#CC523F', base='#A0332A', lo='#70211C', deep='#4A1512', glint='#F2B0A0'),
    'tread': dict(hi='#58647C', base='#3C465A', lo='#293143', deep='#1A1F2B', glint='#A8B4CC'),
}
LIGHT = np.array([-0.55, 0.80, 0.35])          # world key light (x right, y up, z toward the viewer): upper left front
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def mix(a, b, t):
    a, b = a.lstrip('#'), b.lstrip('#')
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return '#%02X%02X%02X' % tuple(int(round(ca[i] + (cb[i] - ca[i]) * t)) for i in range(3))

# ============================================================================================ the set


def background():
    """The Dealer's set at SS, re-hued: wall gradient + centre glow, panel seams, two shelves, tube lights, neon bars,
    the counter. RGBA (WS x HS)."""
    y = (np.arange(HS) / SS)[:, None]
    x = (np.arange(WS) / SS)[None, :]
    t = np.clip(y / 150.0, 0, 1)
    wall = np.array(WALL_TOP)[None, None] * (1 - t[..., None]) + np.array(WALL_LOW)[None, None] * t[..., None]
    wall = np.broadcast_to(wall, (HS, WS, 3)).copy()
    glow = np.exp(-(((x - 120) / 70.0) ** 2 + ((y - 70) / 80.0) ** 2))
    wall += glow[..., None] * np.array([6, 22, 26])[None, None]
    for sx in (48, 112, 176):                                   # the panel seams
        m = np.abs(x - sx) < 0.75
        wall[np.broadcast_to(m, (HS, WS))] *= 0.78
    for sy in (44, 106):                                        # the shelves: a lit lip, a band under it
        lip = np.abs(y - sy) < 0.8
        band = (y > sy + 1) & (y < sy + 7)
        wall[np.broadcast_to(band, (HS, WS))] = np.array(SHELF_BAND)
        wall[np.broadcast_to(lip, (HS, WS))] = np.array(SHELF_LINE)
    face = (y >= 167) & (y < 188)                               # the counter: lit face fading to 186, the dark foot
    ft = np.clip((y - 167) / 20.0, 0, 1)
    cface = np.array(COUNTER_TOP)[None, None] * (1 - ft[..., None]) + np.array(COUNTER_LOW)[None, None] * ft[..., None]
    wall = np.where(np.broadcast_to(face[..., None], (HS, WS, 3)), np.broadcast_to(cface, (HS, WS, 3)), wall)
    wall[np.broadcast_to(y >= 188, (HS, WS))] = np.array(COUNTER_FOOT)
    up = np.clip(1 - np.abs(y - 163) / 8.0, 0, 1) * (y < 166)  # the counter's light on the wall just above it
    wall += up[..., None] * np.array([4, 24, 28])[None, None]
    img = Image.fromarray(np.clip(wall, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    neon = Image.new('RGBA', (WS, HS), (0, 0, 0, 0))
    d = ImageDraw.Draw(neon)
    S = SS
    bars = [(18, 30, 56), (96, 19, 144), (180, 30, 222), (30, 92, 50), (190, 92, 214)]
    for x0, yy, x1 in bars:
        d.rounded_rectangle([x0 * S, (yy - 1.3) * S, x1 * S, (yy + 1.3) * S], radius=1.3 * S, fill=CYAN + (255,))
    tubes = [(26, 15, 42, 45), (16, 73, 32, 103), (208, 73, 224, 103)]
    caps = Image.new('RGBA', (WS, HS), (0, 0, 0, 0))
    dc = ImageDraw.Draw(caps)
    for x0, y0, x1, y1 in tubes:
        d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=2 * S, fill=CYAN + (255,))
        dc.rounded_rectangle([(x0 - 1) * S, (y0 - 2) * S, (x1 + 1) * S, (y0 + 2.5) * S], radius=1.5 * S, fill=(6, 10, 14, 255))
        dc.rounded_rectangle([(x0 - 1) * S, (y1 - 2.5) * S, (x1 + 1) * S, (y1 + 2) * S], radius=1.5 * S, fill=(6, 10, 14, 255))
        dc.rectangle([(x1 - 3.5) * S, (y0 + 3) * S, (x1 - 1.5) * S, (y1 - 3) * S], fill=(205, 252, 255, 160))   # glass highlight
    d.rectangle([0, 165.2 * S, WS, 166.8 * S], fill=COUNTER_LINE + (255,))
    halo = neon.filter(ImageFilter.GaussianBlur(4.0 * S))
    img = Image.alpha_composite(img, halo)
    img = Image.alpha_composite(img, _scale_alpha(neon.filter(ImageFilter.GaussianBlur(1.6 * S)), 0.8))
    img = Image.alpha_composite(img, neon)
    img = Image.alpha_composite(img, caps)
    return img


def _scale_alpha(im, f):
    r, g, b, a = im.split()
    return Image.merge('RGBA', (r, g, b, a.point(lambda v: int(v * f))))

# ============================================================================================ the vector kit


def P(pts, close=True):
    s = 'M%.2f,%.2f' % pts[0] + ''.join(' L%.2f,%.2f' % p for p in pts[1:])
    return s + (' Z' if close else '')


def ellipse_pts(cx, cy, rx, ry, rot=0.0, n=72, a0=0.0, a1=360.0):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for i in range(n + (0 if (a1 - a0) >= 360 else 1)):
        a = math.radians(a0 + (a1 - a0) * i / float(n))
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def E(cx, cy, rx, ry, rot=0.0, n=72):
    return P(ellipse_pts(cx, cy, rx, ry, rot, n))


def bez(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / float(n)
        u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def ribbon(pts, w0, w1=None):
    """A band of width w0 (-> w1) along a polyline, as a closed polygon (belts, tubes, ribs)."""
    w1 = w0 if w1 is None else w1
    n = len(pts)
    left, right = [], []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        w = (w0 + (w1 - w0) * i / float(max(1, n - 1))) / 2.0
        left.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
        right.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    return left + right[::-1]


def hull(pts):
    """2D convex hull (monotone chain), clockwise in screen space."""
    p = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
    if len(p) <= 2:
        return p

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


class Part:
    """One silhouette piece: a fill, its clipped children (tone shades, detail lines, lights), a thin ink edge."""

    def __init__(self, d, fill, edge):
        self.d, self.fill, self.edge, self.kids = d, fill, edge, []

    def shade(self, d, fill, op=1.0):
        self.kids.append(('shade', d, fill, op))
        return self

    def line(self, d, color=INK_HEX, w=0.8, op=1.0, cap='round'):
        self.kids.append(('line', d, color, w, op, cap))
        return self

    def glow(self, d, w=None, hue=CYAN_HEX, core=CORE_HEX):
        """A LIGHT: w None = a lit shape (hot core fill, hue edge); w = a lit stroke (hue, white-hot core)."""
        self.kids.append(('glow', d, w, hue, core))
        return self


class Fig:
    def __init__(self, offset=(0.0, 0.0)):
        self.parts = []
        self.offset = offset            # a hand-placed figure's final nudge in the frame (clip paths move with it)

    def part(self, d, fill, edge=IN):
        p = Part(d, fill, edge)
        self.parts.append(p)
        return p

    def svg(self, mode):
        """mode: 'col' the colour art, 'ink' the heavy silhouette, 'cov' the fill union, 'glow' the visible lights
        (lights white, everything else black, in the same order so a part in front hides a light behind it)."""
        defs, body = [], []

        def pth(d, fill='none', stroke='none', sw=0.0, op=1.0, cap='round', join='round', extra=''):
            body.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%.2f" opacity="%.3f" stroke-linecap="%s" '
                        'stroke-linejoin="%s"%s/>' % (d, fill, stroke, sw, op, cap, join, extra))
        for i, p in enumerate(self.parts):
            if mode == 'ink':
                pth(p.d, INK_HEX, INK_HEX, 2 * OUT)
                continue
            if mode == 'cov':
                pth(p.d, '#FFFFFF')
                continue
            base = p.fill if mode == 'col' else '#000000'
            pth(p.d, base, base, 0.3)
            cid = 'k%d' % i
            defs.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, p.d))
            body.append('<g clip-path="url(#%s)">' % cid)
            for k in p.kids:
                if k[0] == 'shade' and mode == 'col':
                    pth(k[1], k[2], k[2], 0.35, op=k[3])
                elif k[0] == 'line' and mode == 'col':
                    pth(k[1], 'none', k[2], k[3], op=k[4], cap=k[5])
                elif k[0] == 'glow':
                    _, d, w, hue, core = k
                    if mode == 'col':
                        if w is None:
                            pth(d, mix(hue, core, 0.55), hue, 1.0)
                        else:
                            pth(d, 'none', hue, w)
                            if core:
                                pth(d, 'none', core, max(0.5, w * 0.42))
                    else:
                        if w is None:
                            pth(d, '#FFFFFF', '#FFFFFF', 1.0)
                        else:
                            pth(d, 'none', '#FFFFFF', w)
            body.append('</g>')
            if p.edge:
                pth(p.d, 'none', INK_HEX if mode == 'col' else '#000000', p.edge)
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><defs>%s</defs>'
                '<g transform="translate(%.2f,%.2f)">%s</g></svg>'
                % (WS, HS, W, H, ''.join(defs), self.offset[0], self.offset[1], ''.join(body)))

    def raster(self, mode):
        return artgen.render_svg(self.svg(mode), WS, HS, ss=1)

# ---------------------------------------------------------------------------- a parallel camera for the machines


class Cam:
    """World x right, y up, z toward the viewer; yaw turns the subject about y, pitch tilts the view down onto it.
    Every projected point is remembered, so a subject can be measured and fitted to its box."""

    def __init__(self, yaw, pitch, scale=1.0, ox=0.0, oy=0.0):
        self.cy, self.sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        self.cp, self.sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        self.scale, self.ox, self.oy = scale, ox, oy
        self.seen = []

    def rot(self, v):
        x, y, z = v
        x1, z1 = x * self.cy + z * self.sy, -x * self.sy + z * self.cy
        return (x1, y * self.cp - z1 * self.sp, y * self.sp + z1 * self.cp)

    def p(self, v):
        x, y, _ = self.rot(v)
        q = (self.ox + x * self.scale, self.oy - y * self.scale)
        self.seen.append(q)
        return q

    def ps(self, vs):
        return [self.p(v) for v in vs]


def _newell(f):
    n = np.zeros(3)
    for i in range(len(f)):
        a, b = np.array(f[i], float), np.array(f[(i + 1) % len(f)], float)
        n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
    L = np.linalg.norm(n)
    return n / L if L > 1e-9 else n


def tone(n, mat):
    d = float(np.dot(n, LIGHT))
    m = MAT[mat]
    if d > 0.62:
        return m['hi']
    if d > -0.08:
        return m['base']
    if d > -0.72:
        return m['lo']
    return m['deep']


def solid(fig, cam, faces, mat, ridge=True, edge=IN):
    """A CONVEX solid as one part: its projected outline (the hull) inked, each visible face a flat tone by the key
    light, the ridge between a lit top and the face below it caught by a thin light line (the glass bevel of R3)."""
    allv = [v for f in faces for v in f]
    cen = np.mean(np.array(allv, float), axis=0)
    vis = []
    for f in faces:
        n = _newell(f)
        if np.dot(n, np.mean(np.array(f, float), axis=0) - cen) < 0:
            n = -n
        if cam.rot(n)[2] > 1e-4:
            vis.append((f, n))
    part = fig.part(P(hull(cam.ps(allv))), MAT[mat]['base'], edge)
    tones = []
    for f, n in vis:
        t = tone(n, mat)
        tones.append(t)
        part.shade(P(cam.ps(f)), t)
    if ridge:
        hi = MAT[mat]['hi']
        for i, (f, n) in enumerate(vis):
            if tones[i] != hi:
                continue
            fk = [tuple(round(c, 3) for c in v) for v in f]
            for j, (g, m) in enumerate(vis):
                if j == i or tones[j] == hi:
                    continue
                gk = set(tuple(round(c, 3) for c in v) for v in g)
                for a in range(len(fk)):
                    u, v = fk[a], fk[(a + 1) % len(fk)]
                    if u in gk and v in gk:
                        part.line(P(cam.ps([u, v]), close=False), mix(hi, '#FFFFFF', 0.5), 0.75, 0.75)
    return part


def prism(bottom, top):
    n = len(bottom)
    return [list(bottom), list(top)] + [[bottom[i], bottom[(i + 1) % n], top[(i + 1) % n], top[i]] for i in range(n)]


def slab(plan, y0, y1, top_plan=None):
    """A prism standing on plan (x, z points) from y0 to y1; top_plan narrows / shifts the top (sloped armour)."""
    tp = top_plan or plan
    return prism([(x, y0, z) for x, z in plan], [(x, y1, z) for x, z in tp])


def box(x0, x1, y0, y1, z0, z1):
    return slab([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)


def ring3(c, axis, r, n=28, a0=0.0):
    out = []
    for i in range(n):
        a = math.radians(a0 + 360.0 * i / n)
        u, v = r * math.cos(a), r * math.sin(a)
        if axis == 'x':
            out.append((c[0], c[1] + u, c[2] + v))
        elif axis == 'y':
            out.append((c[0] + u, c[1], c[2] + v))
        else:
            out.append((c[0] + u, c[1] + v, c[2]))
    return out


def cyl(c, axis, r, h, n=28, r1=None):
    """A cylinder (or a cone frustum with r1) centred on c along axis, length h."""
    r1 = r if r1 is None else r1
    k = {'x': 0, 'y': 1, 'z': 2}[axis]
    c0, c1 = list(c), list(c)
    c0[k] -= h / 2.0
    c1[k] += h / 2.0
    return prism(ring3(tuple(c0), axis, r, n), ring3(tuple(c1), axis, r1, n))


def extrude_x(poly_zy, x0, x1):
    """A flat plate (a fin): a polygon in (z, y) given thickness along x."""
    return prism([(x0, y, z) for z, y in poly_zy], [(x1, y, z) for z, y in poly_zy])


def fit_cam(build, yaw, pitch, box_, align='center'):
    """Measure the subject with a unit camera, then scale + place it in box_ = (x0, y0, x1, y1) (screen px)."""
    probe = Cam(yaw, pitch)
    build(Fig(), probe)
    xs, ys = [p[0] for p in probe.seen], [p[1] for p in probe.seen]
    bw, bh = max(xs) - min(xs), max(ys) - min(ys)
    x0, y0, x1, y1 = box_
    s = min((x1 - x0) / bw, (y1 - y0) / bh)
    ox = (x0 + x1) / 2.0 - (min(xs) + max(xs)) / 2.0 * s
    oy = (y1 - max(ys) * s) if align == 'bottom' else ((y0 + y1) / 2.0 - (min(ys) + max(ys)) / 2.0 * s)
    cam = Cam(yaw, pitch, s, ox, oy)
    fig = Fig()
    build(fig, cam)
    return fig, cam

# ============================================================================================ the four companions


def _rot(pts, ang, c):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in pts]


def _sleeve(fig, x0, x1, y0, y1, D, lean=0.0):
    """A dark ribbed hose sleeve (the Protector's arms): rounded bands, each rib a lit upper lip and a dark crease."""
    arm = fig.part(P([(x0, y0), (x1, y0 + lean), (x1 + 2, y1), (x0 + 2, y1)]), D['base'])
    w = x1 - x0
    arm.shade(P([(x0 + w * 0.62, y0 - 2), (x1 + 4, y0 - 2), (x1 + 4, y1 + 2), (x0 + w * 0.64, y1 + 2)]), D['lo'])
    yy = y0 + 8
    while yy < y1 - 2:
        sag = 2.4
        arm.line(P(bez((x0 - 2, yy), (x0 + w * 0.3, yy + sag), (x0 + w * 0.7, yy + sag), (x1 + 3, yy + lean * 0.2), 10),
                   close=False), D['deep'], 1.8)
        arm.line(P(bez((x0 - 2, yy - 2.6), (x0 + w * 0.3, yy - 0.3), (x0 + w * 0.6, yy - 0.3), (x1 - w * 0.3, yy - 1.2), 10),
                   close=False), D['hi'], 1.0, 0.85)
        yy += 9
    return arm


def protector(fig):
    """THE CIVIL PROTECTOR, head and chest behind the counter, three-quarter to the viewer's left (the R1 truth
    render's pose): the tall helmet turned and tipped a little, the visor slit lit, the two great pauldrons."""
    M = MAT['gold' if PROTECTOR_FINISH == 'gold' else 'blue']
    D = MAT['dark']
    # the far (viewer-left) arm under the small pauldron, then the far pauldron
    _sleeve(fig, 50, 74, 112, 168, D)
    pa = fig.part(E(70, 100, 26, 24, -14, 60), M['base'])
    pa.shade(E(62, 91, 22, 17, -14), M['hi'])
    pa.shade(E(86, 114, 22, 15, -14, 40), M['lo'])
    pa.line(P(ellipse_pts(70, 100, 25, 23, -14, 30, 70, 175), close=False), M['deep'], 1.0, 0.8)
    pa.shade(P(ribbon(ellipse_pts(70, 100, 20, 18, -14, 18, 205, 255), 2.4)), M['glint'], 0.85)
    # the waist: dark ribbed bands from under the chest plate to the counter
    waist = fig.part(P([(96, 138), (152, 138), (150, 170), (98, 170)]), D['base'])
    waist.shade(P([(132, 136), (156, 136), (154, 172), (134, 172)]), D['lo'])
    for yy in (150, 159, 168):
        waist.line(P(bez((94, yy), (110, yy + 2.5), (138, yy + 2.5), (156, yy), 10), close=False), D['deep'], 1.8)
        waist.line(P(bez((94, yy - 2.6), (110, yy - 0.3), (128, yy - 0.3), (140, yy - 1.4), 10), close=False), D['hi'], 1.0, 0.8)
    # the chest: a barrel plate - two pectoral plates on a centre ridge over an abdominal plate
    torso = bez((80, 92), (82, 78), (100, 72), (122, 72)) + bez((122, 72), (146, 72), (166, 78), (170, 92)) + \
        bez((170, 92), (171, 114), (164, 136), (152, 150)) + bez((152, 150), (140, 156), (108, 156), (96, 150)) + \
        bez((96, 150), (86, 138), (79, 114), (80, 92))
    ch = fig.part(P(torso), M['base'])
    pec_l = bez((84, 90), (90, 80), (108, 76), (121, 76)) + [(121, 116)] + bez((121, 116), (108, 124), (94, 122), (86, 114))
    ch.shade(P(pec_l), M['hi'])
    ch.shade(P([(152, 74), (176, 86), (176, 160), (146, 160), (156, 120)]), M['lo'])               # the side turning away
    ch.shade(P(bez((84, 124), (100, 132), (140, 132), (168, 120)) + [(168, 160), (84, 160)]), M['lo'], 0.6)  # under the pecs
    ch.line(P(bez((121, 75), (122, 96), (121, 112), (121, 118)), close=False), M['deep'], 1.2)               # the centre ridge
    ch.line(P(bez((86, 114), (96, 123), (110, 124), (121, 117)), close=False), M['deep'], 1.1)               # the pec plates
    ch.line(P(bez((122, 117), (134, 124), (150, 122), (162, 110)), close=False), M['deep'], 1.1)
    ch.line(P(bez((87, 112), (96, 120), (110, 121), (120, 115)), close=False), M['glint'], 0.8, 0.55)
    ch.line(P(bez((96, 138), (110, 143), (138, 143), (152, 136)), close=False), M['deep'], 1.0)              # the abdomen seam
    ch.shade(P(ribbon(bez((90, 88), (96, 81), (106, 78), (116, 78), 10), 2.4)), M['glint'], 0.75)              # the pec's polish
    # the crest: a shield on the near pec, a darker inset with a lit chevron
    crest = [(130, 96), (146, 94), (146, 106), (138, 114), (130, 106)]
    ch.shade(P(crest), M['lo'])
    ch.line(P(crest), M['deep'], 0.9)
    ch.line(P([(133, 100), (138, 104), (143, 99)], close=False), M['glint'], 1.1, 0.9)
    # the collar lights (the W2A model's shoulder-socket lights, in the companion's cyan)
    ch.glow(E(97, 84, 2.4, 2.0))
    ch.glow(E(104, 81.5, 2.4, 2.0))
    ch.glow(E(152, 84, 2.2, 2.0))
    # the gorget round the neck
    gor = fig.part(E(122, 80, 26, 8.5, -4, 48), M['lo'])
    gor.shade(E(118, 77.5, 22, 5.5, -4, 40), M['base'])
    # the ribbed neck
    neck = fig.part(P([(109, 58), (133, 58), (135, 80), (107, 80)]), D['base'])
    neck.shade(P([(124, 56), (140, 56), (140, 82), (126, 82)]), D['lo'])
    for yy in (65, 70, 75):
        neck.line(P(bez((104, yy), (114, yy + 1.6), (128, yy + 1.6), (140, yy), 8), close=False), D['deep'], 1.6)
        neck.line(P(bez((104, yy - 2.2), (114, yy - 0.8), (124, yy - 0.8), (132, yy - 1.6), 8), close=False), D['hi'], 0.9, 0.9)
    # the helmet, turned to the viewer's left and tipped back a little (rotated about the neck)
    pivot, tip = (120, 66), -6.0

    def T(pts):
        return _rot(pts, tip, pivot)
    head = bez((96, 60), (94, 46), (92, 34), (93, 25)) + bez((93, 25), (94, 10), (106, 4), (119, 4)) + \
        bez((119, 4), (134, 4), (144, 12), (144, 27)) + bez((144, 27), (144, 42), (143, 54), (140, 62)) + \
        bez((140, 62), (137, 67), (128, 69), (118, 69)) + bez((118, 69), (106, 69), (98, 66), (96, 60))
    hd = fig.part(P(T(head)), M['base'])
    hd.shade(P(T(bez((93, 29), (94, 12), (106, 4), (119, 4)) + [(126, 4), (126, 70), (96, 70)])), M['hi'])
    hd.shade(P(T([(132, 2), (150, 2), (150, 72), (132, 72)])), M['lo'])
    hd.shade(P(T([(90, 56), (132, 52), (132, 72), (90, 72)])), M['lo'], 0.45)                         # under the jaw
    hd.shade(P(T(ribbon(bez((98, 22), (99, 12), (106, 7), (116, 6), 10), 2.6))), M['glint'], 0.9)    # the dome's polish
    # the brow ridge and the visor: a dark recess, ONE long slit lit across it
    hd.line(P(T(bez((93, 21), (106, 19), (120, 18.5), (132, 19))), close=False), M['deep'], 1.1)
    vb = T([(93, 25), (132, 23), (132, 37), (94, 38)])
    hd.shade(P(vb), D['base'])
    hd.shade(P(T([(93, 33), (132, 31), (132, 37), (94, 38)])), D['lo'])
    hd.line(P(vb), D['deep'], 1.0)
    hd.glow(P(T([(97, 28.8), (129, 27.6), (129, 31.6), (97, 32.8)])))
    hd.line(P(T([(113, 26.5), (113, 34.5)]), close=False), D['deep'], 1.4, cap='butt')
    # the jaw vents below it
    for yy in (48, 54):
        hd.line(P(T([(104, yy), (122, yy - 0.4)]), close=False), M['lo'], 1.6)
    # the face-to-side turn and the ear disc on the side plane
    hd.line(P(T(bez((131, 8), (132, 30), (132, 50), (130, 66))), close=False), M['deep'], 1.0, 0.8)
    ec = T([(138, 40)])[0]
    ear = fig.part(E(ec[0], ec[1], 7.5, 9, tip, 40), M['base'])
    ear.shade(E(ec[0] - 1.5, ec[1] - 1.5, 5, 6.2, tip, 32), M['hi'])
    ear.shade(E(ec[0], ec[1], 2.6, 3.2, tip, 20), M['deep'])
    # the crest knob on top
    knob = fig.part(P(T(bez((112, 6), (112, 0), (126, 0), (126, 6)) + [(126, 7), (112, 7)])), M['base'])
    knob.shade(P(T([(110, -2), (118, -2), (118, 8), (110, 8)])), M['hi'])
    # the near (viewer-right) arm and the great pauldron over it
    _sleeve(fig, 172, 202, 128, 168, D)
    big = bez((150, 96), (150, 76), (170, 70), (186, 74)) + bez((186, 74), (204, 78), (214, 96), (212, 118)) + \
        bez((212, 118), (211, 132), (204, 140), (194, 140)) + [(156, 132)] + bez((156, 132), (150, 122), (148, 108), (150, 96))
    pb = fig.part(P(big), M['base'])
    pb.shade(P(bez((150, 100), (150, 78), (170, 72), (186, 76)) + [(200, 84), (172, 104), (152, 118)]), M['hi'])
    pb.shade(P([(198, 80), (220, 92), (220, 146), (186, 146), (194, 116)]), M['lo'])
    pb.shade(P(ribbon(bez((156, 92), (160, 80), (172, 75), (186, 77), 12), 3.0)), M['glint'], 0.9)
    rimp = bez((152, 122), (172, 119), (194, 121), (210, 128)) + [(206, 140), (194, 141)] + bez((194, 141), (180, 133), (166, 131), (156, 132))
    pb.shade(P(rimp), M['lo'])                                                                         # the rim plate
    pb.line(P(bez((152, 122), (172, 119), (194, 121), (210, 128)), close=False), M['deep'], 1.2)
    pb.line(P(bez((154, 125), (172, 122), (192, 124), (207, 131)), close=False), M['base'], 0.9, 0.9)
    pb.shade(E(201, 102, 6, 6.6, 0, 32), D['base'])                                                  # the shoulder bolt
    pb.shade(E(200, 101, 3.4, 3.8, 0, 24), D['hi'])
    pb.line(E(201, 102, 6, 6.6, 0, 32), D['deep'], 0.9)
    return fig


def talon(fig, cam):
    """THE TALON: fuselage, two side pods with ducted lift fans, twin swept fins, tail stabilisers, chin gun."""
    pod_r = [(24, -36), (32, -44), (80, -44), (88, -30), (88, 30), (74, 44), (32, 44), (24, 36)]
    fin = [(-42, 14), (-6, 14), (-28, 52), (-40, 52)]             # the twin swept dorsal fins' profile (z, y)
    tail_up = [(-12, 14), (-44, 14), (-68, 52), (-54, 52)]        # the pods' outer tail fins: up on the far pod,
    tail_dn = [(-12, 0), (-44, 0), (-68, -38), (-54, -38)]        # down on the near one (the drone's X tail)

    def pod(sg):
        plan = pod_r if sg > 0 else [(-x, z) for x, z in reversed(pod_r)]
        return solid(fig, cam, slab(plan, 0, 14, [(x * 0.97, z * 0.96) for x, z in plan]), 'gun')
    # far side first: the left pod's tail fin, the pod and its dorsal fin
    solid(fig, cam, extrude_x(tail_up, -86, -82), 'gun')
    pl = pod(-1)
    _fan(pl, cam, (-56, 14, 0))
    solid(fig, cam, extrude_x(fin, -29, -25), 'gun')
    # the body: struts, the fuselage with its spine, the nose sensor
    solid(fig, cam, box(-30, 30, 4, 12, -10, 10), 'dark')
    fus_plan = [(-17, -52), (17, -52), (17, 30), (10, 54), (-10, 54), (-17, 30)]
    fus = solid(fig, cam, slab(fus_plan, 0, 20, [(x * 0.85, z * 0.96) for x, z in fus_plan]), 'gun')
    fus.glow(P(cam.ps([(-7, 11, 55.4), (7, 11, 55.4), (7, 15, 54.6), (-7, 15, 54.6)])))
    spine = [(-9, -34), (9, -34), (9, 18), (0, 34), (-9, 18)]
    solid(fig, cam, slab(spine, 20, 28, [(x * 0.7, z * 0.92) for x, z in spine]), 'gun')
    # the chin gun: a housing and twin barrels
    solid(fig, cam, box(-9, 9, -12, 0, 26, 50), 'dark')
    for bx in (-4.5, 4.5):
        solid(fig, cam, cyl((bx, -6, 58), 'z', 2.8, 18, 14), 'steel')
    # near side: the right pod's tail fin hanging under it, the pod (its fan, its running lights) and its dorsal fin
    solid(fig, cam, extrude_x(tail_dn, 82, 86), 'gun')
    pr = pod(1)
    _fan(pr, cam, (56, 14, 0))
    pr.glow(P(cam.ps([(36, 7, 44.6), (70, 7, 44.6)]), close=False), w=1.6)
    pr.glow(P(cam.ps([(88.5, 7, -22), (88.5, 7, 22)]), close=False), w=1.6)
    solid(fig, cam, extrude_x(fin, 25, 29), 'gun')
    return fig


def _fan(part, cam, c):
    """A ducted lift fan sunk in a pod's top: the duct's lip, the dark well, the blades and hub lit cyan."""
    D = MAT['dark']
    part.shade(P(cam.ps(ring3(c, 'y', 25, 40))), MAT['gun']['lo'])
    part.shade(P(cam.ps(ring3((c[0], c[1] + 0.1, c[2]), 'y', 21, 40))), D['deep'])
    part.glow(P(cam.ps(ring3(c, 'y', 18, 40))), w=1.3)
    for i in range(10):
        a = math.radians(i * 36 + 8)
        b = math.radians(i * 36 + 26)
        part.glow(P(cam.ps([(c[0] + 5 * math.cos(a), c[1], c[2] + 5 * math.sin(a)),
                            (c[0] + 16 * math.cos(b), c[1], c[2] + 16 * math.sin(b))]), close=False), w=1.4)
    part.shade(P(cam.ps(ring3(c, 'y', 5.5, 20))), MAT['gun']['hi'])
    part.line(P(cam.ps(ring3(c, 'y', 25, 40))), INK_HEX, 0.9)


def raps(fig):
    """THE R.A.P.S.: the domed hub (red star, sensor eye), the spiked rims, the tread drum behind it."""
    Sh, Tr, St, Rd = MAT['shell'], MAT['tread'], MAT['steel'], MAT['star']
    fc, bc = (104, 94), (144, 84)        # the front hub's centre, the back rim's centre
    rx, ry, rot = 50, 60, -8

    def spikes(c, r_in, r_out, n, a_off, width_deg):
        """n hooked steel blades round a rim: each a lit half and a shadow half (the upper left ones face the key)."""
        for i in range(n):
            a = a_off + 360.0 * i / n
            p0 = ellipse_pts(c[0], c[1], rx * r_in, ry * r_in, rot, 1, a - width_deg, a - width_deg)[0]
            p1 = ellipse_pts(c[0], c[1], rx * r_in, ry * r_in, rot, 1, a + width_deg, a + width_deg)[0]
            tip = ellipse_pts(c[0], c[1], rx * r_out, ry * r_out, rot, 1, a + 9, a + 9)[0]   # hooked: the blades lean
            mid = ellipse_pts(c[0], c[1], rx * r_in, ry * r_in, rot, 1, a, a)[0]
            sp = fig.part(P([p0, tip, p1]), St['base'])
            lit = math.cos(math.radians(a + 135)) > -0.2
            sp.shade(P([p0, tip, mid]), St['hi'] if lit else St['base'])
            sp.shade(P([mid, tip, p1]), St['lo'] if lit else St['deep'])
    # the back rim's spikes (behind everything), then the tread drum
    spikes(bc, 0.98, 1.28, 14, 8, 9)
    drum_pts = ellipse_pts(fc[0], fc[1], rx * 1.02, ry * 1.02, rot, 72) + ellipse_pts(bc[0], bc[1], rx * 1.02, ry * 1.02, rot, 72)
    dr = fig.part(P(hull(drum_pts)), Tr['base'])
    dr.shade(P(hull(ellipse_pts(bc[0] + 6, bc[1] + 10, rx, ry, rot, 48) + ellipse_pts(fc[0] + 30, fc[1] + 30, rx, ry, rot, 48))),
             Tr['lo'])
    dr.shade(P(hull(ellipse_pts(bc[0] - 4, bc[1] - 30, rx * 0.7, ry * 0.4, rot, 32) + ellipse_pts(fc[0], fc[1] - 40, rx * 0.6, ry * 0.4, rot, 32))),
             Tr['hi'])
    # the drum's tread seams, lit (the in-world drum's glowing seams, in the companion's cyan)
    for k in range(-3, 4):
        a = 90 + k * 26
        p_f = ellipse_pts(fc[0], fc[1], rx * 1.02, ry * 1.02, rot, 1, a - 180, a - 180)[0]
        p_b = ellipse_pts(bc[0], bc[1], rx * 1.02, ry * 1.02, rot, 1, a - 180, a - 180)[0]
        m = ((p_f[0] + p_b[0]) / 2 + 3, (p_f[1] + p_b[1]) / 2)
        dr.glow(P([p_f, m, p_b], close=False), w=1.2)
    # the back rim: the shell's band along the drum's far edge
    br = fig.part(P(ellipse_pts(bc[0], bc[1], rx * 1.06, ry * 1.06, rot, 48, -84, 96)
                    + ellipse_pts(bc[0] - 3, bc[1], rx * 0.96, ry * 0.96, rot, 48, 96, -84)), Sh['lo'])
    br.shade(P(ellipse_pts(bc[0], bc[1], rx * 1.1, ry * 1.1, rot, 20, -100, -40) + [bc]), Sh['base'])
    # the middle ring (a raised band round the drum, between hub and back rim)
    mc = ((fc[0] * 0.55 + bc[0] * 0.45), (fc[1] * 0.55 + bc[1] * 0.45))
    mr = fig.part(P(ellipse_pts(mc[0], mc[1], rx * 1.08, ry * 1.08, rot, 72, -70, 110)
                    + ellipse_pts(mc[0] - 4, mc[1] + 1, rx * 1.0, ry * 1.0, rot, 72, 110, -70)), Sh['base'])
    mr.shade(P(ellipse_pts(mc[0], mc[1], rx * 1.1, ry * 1.1, rot, 30, -110, -20) + [(mc[0], mc[1])]), Sh['hi'])
    # the front rim's spikes, then the hub (the rim ring, the dome, the star, the eye)
    spikes(fc, 0.98, 1.31, 16, 0, 9)
    rim = fig.part(E(fc[0], fc[1], rx * 1.06, ry * 1.06, rot), Sh['lo'])
    rim.shade(P(ellipse_pts(fc[0], fc[1], rx * 1.08, ry * 1.08, rot, 40, 150, 290) + [fc]), Sh['base'])
    hub = fig.part(E(fc[0], fc[1], rx * 0.94, ry * 0.94, rot), Sh['base'])
    hub.shade(E(fc[0] - 10, fc[1] - 12, rx * 0.84, ry * 0.84, rot), Sh['hi'])
    # the red star (a marking painted across the dome), squashed with the hub's ellipse
    star = []
    for i in range(10):
        a = math.radians(-90 + 36 * i)
        r = 1.0 if i % 2 == 0 else 0.42
        x, y = r * rx * 0.92 * math.cos(a), r * ry * 0.92 * math.sin(a)
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        star.append((fc[0] + x * c - y * s, fc[1] + x * s + y * c))
    hub.shade(P(star), Rd['base'])
    hub.shade(E(fc[0] + 16, fc[1] + 18, rx * 0.86, ry * 0.86, rot), '#000000', 0.26)      # the dome turning away
    hub.shade(P(ribbon(ellipse_pts(fc[0], fc[1], rx * 0.82, ry * 0.82, rot, 16, 196, 250), 3.0)), Sh['glint'], 0.6)
    for bp in ((fc[0] + 2, fc[1] - 44), (fc[0] - 2, fc[1] + 44)):                                    # the two bolts
        hub.shade(E(bp[0], bp[1], 3.2, 3.2), St['base'])
        hub.shade(E(bp[0] - 0.6, bp[1] - 0.6, 1.8, 1.8), St['hi'])
    hub.line(E(fc[0], fc[1], rx * 0.94, ry * 0.94, rot), Sh['deep'], 1.0)
    # the sensor eye: a pale bezel ring, the dark lens, the lit iris
    eye = fig.part(E(fc[0], fc[1], 17, 19, rot), St['hi'])
    eye.shade(E(fc[0] + 1.5, fc[1] + 2, 17, 19, rot), St['base'])
    eye.shade(E(fc[0], fc[1], 12.5, 14, rot), MAT['dark']['deep'])
    eye.glow(E(fc[0], fc[1], 6.5, 7.2, rot))
    eye.shade(E(fc[0] - 3.2, fc[1] - 3.6, 1.8, 1.8), '#FFFFFF', 0.95)
    return fig


def cerberus(fig, cam):
    """THE CERBERUS: armoured skirts on road wheels, the turret, the ammo drum + feed belt, the rotary gun, the dome."""
    # far skirt (behind the hull), the chassis
    skirt = [(-80, -54), (72, -54), (86, -44), (86, -34), (-86, -34), (-86, -46)]
    solid(fig, cam, slab(skirt, 12, 38, [(x * 0.92, z) for x, z in skirt]), 'gun')
    solid(fig, cam, box(-62, 62, 16, 44, -36, 36), 'dark')
    # the rear ammo box and the turret body (its top chamfered back)
    rb = solid(fig, cam, box(-58, -28, 80, 100, -34, -6), 'dark')
    for i in range(3):
        rb.shade(E(*cam.p((-50 + i * 9, 100, -20)), 2.2, 1.4), MAT['dark']['deep'])
    tb = [(-52, -38), (34, -38), (40, -30), (40, 30), (34, 38), (-52, 38)]
    tur = solid(fig, cam, slab(tb, 40, 90, [(x * 0.88 - 2, z * 0.84) for x, z in tb]), 'gun')
    tur.glow(P(cam.ps([(36.4, 80, -22), (36.4, 80, -6)]), close=False), w=1.8)                     # the vision slit

    def zface(x, y):                       # a point on the turret's near (+z) face, which leans back 6 over its height
        return (x, y, 38 - 6 * (y - 40) / 50.0 + 0.3)
    panel = [zface(8, 76), zface(30, 76), zface(30, 50), zface(8, 50)]
    tur.shade(P(cam.ps(panel)), MAT['gun']['lo'])                                                    # the access panel
    tur.line(P(cam.ps(panel)), MAT['gun']['deep'], 0.9)
    tur.line(P(cam.ps([zface(9, 75.2), zface(29, 75.2)]), close=False), MAT['gun']['hi'], 0.8, 0.8)
    for py in (56, 62, 68):
        tur.line(P(cam.ps([zface(12, py), zface(26, py)]), close=False), MAT['gun']['deep'], 1.0)
    # the geodesic sensor dome (a faceted half sphere)
    dome = []
    rings = [(0, 20), (30, 17.3), (58, 10.6), (90, 0)]
    cx, cy0, cz = -16, 89, -4
    for (a0, r0), (a1, r1) in zip(rings[:-1], rings[1:]):
        h0, h1 = 20 * math.sin(math.radians(a0)), 20 * math.sin(math.radians(a1))
        n = 8
        for i in range(n):
            t0, t1 = 2 * math.pi * i / n + (0.39 if a0 else 0), 2 * math.pi * (i + 1) / n + (0.39 if a0 else 0)
            f = [(cx + r0 * math.cos(t0), cy0 + h0, cz + r0 * math.sin(t0)), (cx + r0 * math.cos(t1), cy0 + h0, cz + r0 * math.sin(t1))]
            if r1 > 0.01:
                f += [(cx + r1 * math.cos(t1), cy0 + h1, cz + r1 * math.sin(t1)), (cx + r1 * math.cos(t0), cy0 + h1, cz + r1 * math.sin(t0))]
            else:
                f += [(cx, cy0 + h1, cz)]
            dome.append(f)
    dome.append([(cx + 20 * math.cos(2 * math.pi * i / 8), cy0, cz + 20 * math.sin(2 * math.pi * i / 8)) for i in range(8)])
    dp = solid(fig, cam, dome, 'dark')
    band = [(cx + 19.4 * math.cos(math.radians(a)), cy0 + 5, cz + 19.4 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
    dp.glow(P(cam.ps(band), close=False), w=2.0)                                                    # the sensor ring
    # the gun: a housing on the turret's front, three barrels, the muzzle collar
    solid(fig, cam, box(36, 62, 52, 74, -2, 22), 'dark')
    for i in range(3):
        a = math.radians(90 + 120 * i)
        solid(fig, cam, cyl((92, 63 + 5 * math.sin(a), 10 + 5 * math.cos(a)), 'x', 2.6, 60, 12), 'steel')
    solid(fig, cam, cyl((80, 63, 10), 'x', 8.5, 5, 16), 'dark')                                     # the barrel clamp
    mz = solid(fig, cam, cyl((116, 63, 10), 'x', 9, 8, 16), 'gun')
    mz.glow(P(cam.ps(ring3((120.2, 63, 10), 'x', 3.2, 12))))
    # the AMMO DRUM on the near side: steel, two dark straps, its cap; the feed belt arching to the gun
    drum = solid(fig, cam, cyl((-14, 66, 48), 'y', 22, 52, 24), 'steel')
    for yy in (50, 80):                    # the two straps: dark bands round the near half
        lo_ = ring3((-14, yy - 2.6, 48), 'y', 22.4, 24)[0:13]
        hi_ = ring3((-14, yy + 2.6, 48), 'y', 22.4, 24)[0:13]
        drum.shade(P(cam.ps(lo_ + hi_[::-1])), MAT['gun']['lo'])
        drum.line(P(cam.ps(hi_), close=False), MAT['steel']['hi'], 0.8, 0.7)
    drum.shade(P(cam.ps(ring3((-14, 92.2, 48), 'y', 10, 16))), MAT['steel']['base'])                # the cap's hub
    drum.line(P(cam.ps(ring3((-14, 92.2, 48), 'y', 10, 16))), MAT['steel']['deep'], 0.9)
    belt = [cam.p(v) for v in [(-6, 92, 52), (10, 112, 50), (34, 104, 38), (48, 72, 18)]]
    bpts = bez(belt[0], belt[1], belt[2], belt[3], 20)
    bl = fig.part(P(ribbon(bpts, 9.5)), MAT['steel']['base'])
    bl.shade(P(ribbon([(x - 1.4, y - 1.4) for x, y in bpts], 4)), MAT['steel']['hi'])
    for i in range(1, 20, 2):
        bl.shade(E(bpts[i][0], bpts[i][1], 1.1, 1.1), MAT['dark']['base'])
    # the near skirt (its bolts, its seams, its running lights) over the road wheels
    for wx in (-58, -20, 20, 58):
        w = solid(fig, cam, cyl((wx, 10, 50), 'z', 10, 10, 18), 'dark')
        w.shade(P(cam.ps(ring3((wx, 10, 55.2), 'z', 4, 12))), MAT['steel']['lo'])
    skirt_n = [(-86, 34), (86, 34), (86, 44), (72, 56), (-80, 56), (-86, 46)]
    sk = solid(fig, cam, slab(skirt_n, 12, 38, [(x * 0.92, z - 4) for x, z in skirt_n]), 'gun')
    for sx in (-28, 28):
        sk.line(P(cam.ps([(sx, 12, 56.1), (sx, 38, 52.1)]), close=False), MAT['gun']['deep'], 1.1)
    for bx in (-70, -44, -12, 12, 44, 66):
        q = cam.p((bx, 32, 53))
        sk.shade(P([(q[0] - 1.4, q[1] - 1.2), (q[0] + 1.4, q[1] - 1.2), (q[0] + 1.4, q[1] + 1.2), (q[0] - 1.4, q[1] + 1.2)]),
                 MAT['dark']['deep'])
    sk.glow(P(cam.ps([(-64, 22, 56.2), (-36, 22, 56.2)]), close=False), w=1.8)
    sk.glow(P(cam.ps([(36, 22, 56.2), (64, 22, 56.2)]), close=False), w=1.8)
    return fig


SUBJECTS = {
    # name: (build, camera (yaw, pitch) or None for a hand-placed figure, fit box, how it meets the counter)
    'protector': (protector, None, None, 'behind'),
    'talon': (talon, (-36, 26), (29, 22, 211, 146), 'hover'),
    'raps': (raps, None, None, 'sit'),
    'cerberus': (cerberus, (-28, 22), (29, 16, 211, 166), 'sit'),
}
OFFSET = {'protector': (-6.0, 9.0)}   # centre the bust in the icon square, its crest knob 10 px under the top edge
                                      # (docs/195's portrait template: nothing important within 10 px of an edge)
ICON_X = (24, 216)        # make_gift_art cuts the portrait's centre 192 x 192 into the icon: the subject stays inside it

# ============================================================================================ the composite


def _shift(F, dx, dy):
    """F sampled at (x + dx, y + dy) (integer px), 0 outside."""
    out = np.zeros_like(F)
    h, w = F.shape
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    out[ys0:ys1, xs0:xs1] = F[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def compose(name, fig):
    mode = SUBJECTS[name][3]
    bg = np.asarray(background()).astype(np.float32) / 255.0
    ink = np.asarray(fig.raster('ink')).astype(np.float32) / 255.0
    col = np.asarray(fig.raster('col')).astype(np.float32) / 255.0
    cov = np.asarray(fig.raster('cov')).astype(np.float32)[..., 3] / 255.0
    gm = np.asarray(fig.raster('glow')).astype(np.float32) / 255.0
    lit = gm[..., 0] * gm[..., 3]
    A = ink[..., 3]
    xs = np.where((A > 0.02).any(axis=0))[0]
    if xs.min() / SS < ICON_X[0] or (xs.max() + 1) / SS > ICON_X[1]:
        raise SystemExit('r1_comp_portraits: %s spans x %.1f..%.1f - outside the icon square %d..%d (make_gift_art would '
                         'cut it)' % (name, xs.min() / SS, (xs.max() + 1) / SS, ICON_X[0], ICON_X[1]))
    if mode == 'behind':                         # head and chest behind the counter, like the Dealer
        cut = int(round(COUNTER_Y * SS))
        for arr in (ink, col):
            arr[cut:, :, 3] = 0
        cov[cut:] = 0
        lit[cut:] = 0
        A = ink[..., 3]
    out = bg[..., :3].copy()
    # a soft shadow of the figure on the wall (down-right of the key light), and under a seated machine its contact
    sh = ndi.gaussian_filter(_shift(A, -3 * SS, -4 * SS), 5 * SS) * 0.43
    if mode == 'sit':
        ys, xs = np.where(A > 0.5)
        x0, x1 = xs.min() / SS, xs.max() / SS
        yy = (np.arange(HS) / SS)[:, None]
        xx = (np.arange(WS) / SS)[None, :]
        cx, rx = (x0 + x1) / 2.0, (x1 - x0) / 2.0 * 0.92
        sh = np.maximum(sh, np.clip(1 - ((xx - cx) / rx) ** 2 - ((yy - 166) / 3.2) ** 2, 0, 1) ** 0.6 * 0.75)
    if mode == 'hover':                          # the lift fans' downwash: a faint cyan haze under the drone
        ys, xs = np.where(A > 0.5)
        x0, x1, yb = xs.min() / SS, xs.max() / SS, ys.max() / SS
        yy = (np.arange(HS) / SS)[:, None]
        xx = (np.arange(WS) / SS)[None, :]
        cx, rx = (x0 + x1) / 2.0, (x1 - x0) / 2.0 * 0.62
        haze = np.clip(1 - ((xx - cx) / rx) ** 2 - ((yy - (yb + 6)) / 9.0) ** 2, 0, 1)
        haze = ndi.gaussian_filter(haze, 4 * SS) * 0.5
        out = 1 - (1 - out) * (1 - haze[..., None] * np.array(CYAN, np.float32)[None, None] / 255.0)
    out *= (1 - sh[..., None])
    # the figure: the heavy ink, then the colour art
    out = out * (1 - A[..., None]) + ink[..., :3] * A[..., None]
    ca = col[..., 3]
    out = out * (1 - ca[..., None]) + col[..., :3] * ca[..., None]
    # the rim light: just inside the silhouette on the edges that face the set's side tubes (strong left, faint right)
    cyan = np.array(CYAN, np.float32) / 255.0
    rim_l = cov * (1 - _shift(cov, -6, -3)) * (1 - lit)
    rim_r = cov * (1 - _shift(cov, 5, -2)) * (1 - lit)
    rim = np.clip(rim_l * 0.85 + rim_r * 0.32, 0, 1)
    out = out * (1 - rim[..., None]) + (out * 0.25 + cyan * 0.75) * rim[..., None]
    # the lights' halo (a screen of the hue: the white-hot cores stay white)
    halo = np.clip(ndi.gaussian_filter(lit, 2.6 * SS) * 1.1 + ndi.gaussian_filter(lit, 0.9 * SS) * 0.7, 0, 1)
    out = 1 - (1 - out) * (1 - halo[..., None] * cyan[None, None] * 0.9)
    # the Dealer's vignette
    y = (np.arange(HS) / HS)[:, None] - 0.5
    x = (np.arange(WS) / WS)[None, :] - 0.5
    v = np.clip(1 - 0.55 * (x ** 2 + y ** 2) * 2.2, 0.55, 1)
    out *= v[..., None]
    rgba = np.dstack([np.clip(out * 255.0, 0, 255), np.full((HS, WS), 255.0)]).astype(np.uint8)
    im = Image.fromarray(rgba, 'RGBA').resize((W, H), Image.LANCZOS)
    a = np.asarray(im).copy()
    a[..., 3] = 255
    return Image.fromarray(a, 'RGBA')


def figure(name):
    build, camv, box_, _ = SUBJECTS[name]
    if camv is None:
        return build(Fig(OFFSET.get(name, (0.0, 0.0))))
    fig, _ = fit_cam(build, camv[0], camv[1], box_, align='bottom' if SUBJECTS[name][3] == 'sit' else 'center')
    return fig


def portrait(name):
    return compose(name, figure(name))


def build():
    return {name: portrait(name) for name in COMPANIONS}

# ============================================================================================ the icons


def gift_module():
    """tools/partner_shop/make_gift_art.py, imported so its OWN make_icon cuts the gift-tile icons (byte parity)."""
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'partner_shop'))
    import make_gift_art
    return make_gift_art


def icons_from(portraits, tmpdir):
    mga = gift_module()
    old = mga.IMG
    os.makedirs(tmpdir, exist_ok=True)
    try:
        for name, im in portraits.items():
            with open(os.path.join(tmpdir, 'i_tod_spin_comp_%s.png' % name), 'wb') as f:
                f.write(artgen.png_bytes(im))
        mga.IMG = tmpdir
        return {name: mga.make_icon(name) for name in portraits}, mga
    finally:
        mga.IMG = old

# ============================================================================================ review
# OLD = the installed images, NEW = this generator's; every screen is drawn by the SHIPPING Lua under the
# tools/ui_mockup mocks at 1080p (1.5 px a canvas unit). Layout and colour proof, not the engine's shader.
K = 1.5
LABEL = (226, 230, 240, 255)
DIM = (150, 158, 176, 255)


def _mock(name):
    import importlib
    d = os.path.join(ROOT, 'tools', 'ui_mockup')
    if d not in sys.path:
        sys.path.insert(0, d)
    return importlib.import_module(name)


def _shipped_img(name):
    return Image.open(artgen.shipped(name)).convert('RGBA')


def _framed(pic):
    """A portrait in the reel's portrait frame at 1080p: the 144-unit frame (216 px), the 120 x 96 window at +12, +10."""
    f = _shipped_img('i_tod_spin_portrait_frame').resize((216, 216), Image.LANCZOS)
    out = Image.new('RGBA', (216, 216), (16, 16, 22, 255))
    out.alpha_composite(pic.resize((180, 144), Image.LANCZOS), (18, 15))
    out.alpha_composite(f)
    return out


def _gift_tile(icon):
    """The gift tile as the reel composites it (the icon in the window at art 176, 32), at 1080p (140 x 104 units)."""
    t = _shipped_img('i_tod_spin_tile_gift')
    t.alpha_composite(icon, (176, 32))
    return t.resize((int(140 * K), int(104 * K)), Image.LANCZOS)


def _spin_frames(newdir, comp):
    """The DEALER'S GIFT reel (render_spin's gift schedule), two moments: mid-spin (the companion tiles) and the
    landing (the portrait in the right window). -> [(label, RGBA 1080p crop of the panel)]."""
    rp, rs = _mock('render_pull'), _mock('render_spin')
    cwd = os.getcwd()
    rp.ART_DIR, rp.SCALE = newdir, K
    rp._cache.clear()
    rp._sized.clear()
    try:
        L, reel = rs.runtime()
        g = L.globals()
        ev, end = rs.gift_schedule(4242, comp, 80)
        bg = Image.new('RGBA', (int(1280 * K), int(720 * K)), (14, 12, 26, 255))
        if os.path.exists(rp.BACKDROP):
            bg = Image.open(rp.BACKDROP).convert('RGBA').resize(bg.size, Image.LANCZOS)
        shots, evi = [], 0
        for t in (end * 0.42, end * 0.80):
            while evi < len(ev) and ev[evi][0] <= t + 1e-6:
                et, nm, args = ev[evi]
                g.ADVANCE(max(0, et * 1000 - g.NOW))
                g.NOTIFY(nm, L.table(*args))
                evi += 1
            g.ADVANCE(max(0, t * 1000 - g.NOW))
            shots.append(rp.draw([dict(x) for x in g.DUMP(reel).values()], bg))
        return shots
    finally:
        rp.ART_DIR = None
        rp._cache.clear()
        rp._sized.clear()
        os.chdir(cwd)


def _plate_frames(newdir):
    """The companion status plate (render_companion_plate: the shipping TodCompanionPlate.lua) in four states."""
    rp, rcp = _mock('render_pull'), _mock('render_companion_plate')
    import tempfile
    cwd = os.getcwd()
    rp.ART_DIR = newdir
    rp._cache.clear()
    rp._sized.clear()
    out = {}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            import contextlib, io as _io
            with contextlib.redirect_stdout(_io.StringIO()):
                rcp.render(tmp)
            for st in ('online', 'damaged', 'destroyed', 'deploying'):
                im = Image.open(os.path.join(tmp, 'hud_plate_%s.png' % st)).convert('RGBA')
                out[st] = im.crop((1488, 770, 1800, 862)).copy()
        return out
    finally:
        rp.ART_DIR = None
        rp._cache.clear()
        rp._sized.clear()
        os.chdir(cwd)


def _menu_rows(newdir):
    """The pause menu and scoreboard AI COMPANION rows (render_menus: the shipping AetheriumStartMenu.lua /
    AetheriumScoreboard.lua), one held companion per class, cropped round the row at 1080p."""
    rm = _mock('render_menus')
    import tempfile
    cwd = os.getcwd()
    dirs = list(rm.IMG_DIRS)
    if newdir:
        rm.IMG_DIRS.insert(0, newdir)
    rm._img_cache.clear()
    rows = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for cls in (1, 3, 4, 2):
                key, cards = rm.CLASSES[cls]
                for kind in ('pause', 'scoreboard'):
                    L = rm.lua_runtime()
                    if kind == 'pause':
                        items = rm.pause_items(L, cls, {**cards, **rm.SHARED, 24: (2, 3)}, companion=rm.COMPANION[cls])
                    else:
                        items = rm.scoreboard_items(L, cls, {**cards, **rm.SHARED, 24: (2, 3)}, companion=rm.COMPANION[cls])
                    p = os.path.join(tmp, '%s_%s.png' % (kind, key))
                    rm.draw(items, p)
                    port = [it for it in items if isinstance(it.get('img'), str) and it['img'].startswith('i_tod_spin_comp_')]
                    if not port:
                        continue
                    pt = port[0]
                    cx, cy = (pt['x0'] + pt['x1']) / 2.0, (pt['y0'] + pt['y1']) / 2.0
                    row = [it for it in items if isinstance(it.get('img'), str) and it['img'] and it['x0'] <= cx <= it['x1']
                           and it['y0'] <= cy <= it['y1'] and 120 < (it['x1'] - it['x0']) < 700]
                    if row:
                        r = max(row, key=lambda it: it['x1'] - it['x0'])
                        box = (r['x0'] - 4, r['y0'] - 4, r['x1'] + 4, r['y1'] + 4)
                    else:
                        box = (pt['x0'] - 20, pt['y0'] - 12, pt['x0'] + 300, pt['y1'] + 12)
                    im = Image.open(p).convert('RGBA')
                    s = rm.SCALE
                    crop = im.crop(tuple(int(round(v * s)) for v in box))
                    crop = crop.resize((max(1, int(crop.width * K / s)), max(1, int(crop.height * K / s))), Image.LANCZOS)
                    rows.append(('%s %s' % (kind, key), crop))
        return rows
    finally:
        rm.IMG_DIRS[:] = dirs
        rm._img_cache.clear()
        os.chdir(cwd)


def review(ports, icons, out_dir, encode):
    """art/generated/W3D-companion-art/_review.png: OLD (installed) vs NEW at the real on-screen sizes."""
    import tempfile
    font, small = artgen.ttf(20), artgen.ttf(15)
    with tempfile.TemporaryDirectory() as newdir:
        for n in COMPANIONS:
            artgen.save_png(ports[n], os.path.join(newdir, 'i_tod_spin_comp_%s.png' % n))
            with open(os.path.join(newdir, 'i_tod_spin_ico_comp_%s.png' % n), 'wb') as f:
                f.write(encode(icons[n]))
        spins = {tag: {c: _spin_frames(d, i) for i, c in enumerate(COMPANIONS)} for tag, d in (('OLD', None), ('NEW', newdir))}
        plates = {tag: _plate_frames(d) for tag, d in (('OLD', None), ('NEW', newdir))}
        menus = {tag: _menu_rows(d) for tag, d in (('OLD', None), ('NEW', newdir))}
    old_p = {n: _shipped_img('i_tod_spin_comp_' + n) for n in COMPANIONS}
    old_i = {n: _shipped_img('i_tod_spin_ico_comp_' + n) for n in COMPANIONS}
    dealer = _shipped_img('i_tod_spin_dealer_idle')
    Wd = 2000
    sheet = Image.new('RGBA', (Wd, 12000), (22, 24, 32, 255))
    d = ImageDraw.Draw(sheet)
    y = 14
    d.text((14, y), 'AI COMPANION ART  -  OLD: shipped, traced from renders  -  NEW: flat vector in the Dealer\'s language', fill=LABEL, font=font)
    y += 30
    d.text((14, y), 'Real on-screen sizes at 1080p unless marked. Screens are drawn by the shipping Lua under tools/ui_mockup.', fill=DIM, font=small)
    y += 34
    # 1 the portraits: the Dealer's frame beside OLD and NEW, then 1:1 and a 2x zoom
    d.text((14, y), '1  THE PORTRAIT WINDOW - Black Market reel, 1080p: the Dealer | OLD | NEW   -   then OLD 1:1 | NEW 1:1 | NEW 2x zoom',
           fill=LABEL, font=font)
    y += 30
    for n in COMPANIONS:
        d.text((14, y), n.upper(), fill=DIM, font=small)
        yy = y + 20
        sheet.alpha_composite(_framed(dealer), (14, yy))
        sheet.alpha_composite(_framed(old_p[n]), (244, yy))
        sheet.alpha_composite(_framed(ports[n]), (474, yy))
        sheet.alpha_composite(old_p[n], (720, yy))
        sheet.alpha_composite(ports[n], (974, yy))
        sheet.alpha_composite(ports[n].resize((480, 384), Image.LANCZOS), (1230, yy))
        y = yy + 396
    # 2 the icons: the 208 window art, the gift tile and the companion plate
    d.text((14, y), '2  THE ICON i_tod_spin_ico_comp_*: art 208 OLD | NEW   -   the gift tile at 1080p OLD | NEW   -   '
                    'the companion plate at 1080p x1.5 OLD | NEW', fill=LABEL, font=font)
    y += 30
    states = ['damaged', 'online', 'destroyed', 'deploying']     # render_companion_plate's states: comp 1, 2, 3, 4
    for i, n in enumerate(COMPANIONS):
        d.text((14, y), n.upper(), fill=DIM, font=small)
        yy = y + 20
        sheet.alpha_composite(old_i[n], (14, yy))
        sheet.alpha_composite(icons[n], (232, yy))
        sheet.alpha_composite(_gift_tile(old_i[n]), (456, yy))
        sheet.alpha_composite(_gift_tile(icons[n]), (676, yy))
        po, pn = plates['OLD'].get(states[i]), plates['NEW'].get(states[i])
        for j, pl in enumerate((po, pn)):
            if pl is not None:
                z = pl.resize((int(pl.width * 1.5), int(pl.height * 1.5)), Image.LANCZOS)
                sheet.alpha_composite(z, (900 + j * (z.width + 16), yy))
                d.text((900 + j * (z.width + 16), yy + z.height + 2), ('OLD' if j == 0 else 'NEW') + ' - plate x1.5',
                       fill=DIM, font=small)
        y = yy + 222
    # 3 the gift reel at 1080p, 1:1: mid-spin once (the reel tiles + the four companion chips), then each landing
    reel = (int(130 * K), int(112 * K), int(1160 * K), int(520 * K))
    land = (int(130 * K), int(140 * K), int(1160 * K), int(440 * K))
    d.text((14, y), '3  THE DEALER\'S GIFT REEL at 1080p, 1:1 - render_spin --gift: mid-spin, then each companion landed. '
                    'OLD above NEW', fill=LABEL, font=font)
    y += 30
    for tag in ('OLD', 'NEW'):
        d.text((14, y), tag + ' - mid-spin', fill=DIM, font=small)
        im = spins[tag]['protector'][0].crop(reel)
        sheet.alpha_composite(im, (14, y + 20))
        y += im.height + 30
    for n in COMPANIONS:
        for tag in ('OLD', 'NEW'):
            d.text((14, y), '%s - %s landed' % (tag, n.upper()), fill=DIM, font=small)
            im = spins[tag][n][1].crop(land)
            sheet.alpha_composite(im, (14, y + 20))
            y += im.height + 30
    # 4 the pause / scoreboard rows
    d.text((14, y), '4  THE AI COMPANION ROW at 1080p - pause menu + scoreboard: OLD | NEW', fill=LABEL, font=font)
    y += 30
    mo, mn = dict(menus['OLD']), dict(menus['NEW'])
    for k in [k for k, _ in menus['NEW']]:
        if k not in mo:
            continue
        d.text((14, y), k.upper(), fill=DIM, font=small)
        yy = y + 20
        sheet.alpha_composite(mo[k], (14, yy))
        sheet.alpha_composite(mn[k], (14 + mo[k].width + 24, yy))
        y = yy + max(mo[k].height, mn[k].height) + 10
    sheet = sheet.crop((0, 0, Wd, y + 20))
    path = os.path.join(out_dir, '_review.png')
    sheet.save(path)
    return path

# ============================================================================================ check


def check(root):
    """Regenerate (pure code) and compare bytes with the installed portraits."""
    fails = []
    ports = build()
    for name in COMPANIONS:
        p = os.path.join(root, 'source_data', 'tod_ui_images', '_images', 'i_tod_spin_comp_%s.png' % name)
        if not os.path.exists(p):
            fails.append('%s: not installed' % p)
            continue
        data = open(p, 'rb').read()
        if data != artgen.png_bytes(ports[name]):
            fails.append('i_tod_spin_comp_%s.png differs from the generator (re-stage; never hand-edit)' % name)
        if Image.open(p).size != (W, H):
            fails.append('i_tod_spin_comp_%s is not %dx%d' % (name, W, H))
    if fails:
        print('COMPANION PORTRAITS FAILED (%d):' % len(fails))
        for f in fails:
            print('  * ' + f)
        return 1
    print('COMPANION PORTRAITS OK %d (flat vector, regenerated in memory; the gift icons are make_gift_art.py --check)'
          % len(COMPANIONS))
    return 0


def selftest(root):
    """--check's negative controls: a clean copy of root's portraits must PASS; a changed pixel, a missing file and a
    wrong size must each FAIL; a subject pushed out of the icon square must be refused. Writes only to a temp dir."""
    import contextlib, io as _io, shutil, tempfile
    src = os.path.join(root, 'source_data', 'tod_ui_images', '_images')
    results = []

    def run(label, t, want):
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            got = check(t)
        results.append((label, got == want, 'exit %d, wanted %d' % (got, want)))

    def tree():
        t = tempfile.mkdtemp(prefix='w3d_selftest_')
        d = os.path.join(t, 'source_data', 'tod_ui_images', '_images')
        os.makedirs(d)
        for n in COMPANIONS:
            shutil.copy2(os.path.join(src, 'i_tod_spin_comp_%s.png' % n), d)
        return t, d
    t, d = tree()
    try:
        run('clean copy passes', t, 0)
        p = os.path.join(d, 'i_tod_spin_comp_raps.png')
        im = Image.open(p).convert('RGBA')
        px = im.load()
        r, g, b, a = px[120, 96]
        px[120, 96] = ((r + 1) % 256, g, b, a)
        im.save(p)
        run('one changed pixel fails', t, 1)
        os.remove(p)
        run('a missing portrait fails', t, 1)
        Image.new('RGBA', (W, H + 4), (0, 0, 0, 255)).save(p)
        run('a wrong size fails', t, 1)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    keep = SUBJECTS['talon']
    try:
        SUBJECTS['talon'] = (keep[0], keep[1], (4, keep[2][1], 236, keep[2][3]), keep[3])
        try:
            portrait('talon')
            results.append(('a subject outside the icon square is refused', False, 'it was drawn'))
        except SystemExit as e:
            results.append(('a subject outside the icon square is refused', 'outside the icon square' in str(e), str(e)[:60]))
    finally:
        SUBJECTS['talon'] = keep
    bad = [r for r in results if not r[1]]
    for label, ok, why in results:
        print('  %s %s%s' % ('ok  ' if ok else 'FAIL', label, '' if ok else ' (%s)' % why))
    print('COMPANION PORTRAITS SELFTEST %s (%d/%d)' % ('OK' if not bad else 'FAILED', len(results) - len(bad), len(results)))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description='the four AI companion portraits, flat vector (W3D)')
    ap.add_argument('--stage', default=None)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--no-review', action='store_true', help='skip the OLD vs NEW review sheet (it drives the Lua mocks)')
    ap.add_argument('--selftest', action='store_true', help="--check's negative controls (temp dir only)")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest(a.root))
    if a.check:
        sys.exit(check(a.root))
    ports = build()
    out_dir = artgen.stage_dir(PACK)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:          # make_gift_art reads the portraits from a folder: a scratch one
        icons, mga = icons_from(ports, tmp)
    for name in COMPANIONS:
        md5 = artgen.save_png(ports[name], os.path.join(out_dir, 'i_tod_spin_comp_%s.png' % name))
        with open(os.path.join(out_dir, 'i_tod_spin_ico_comp_%s.png' % name), 'wb') as f:
            f.write(mga.encode(icons[name]))           # make_gift_art's own encoding: its --check compares these bytes
        print('i_tod_spin_comp_%s.png md5 %s' % (name, md5))
        if a.stage:
            dst = os.path.join(a.stage, 'source_data', 'tod_ui_images', '_images')
            artgen.save_png(ports[name], os.path.join(dst, 'i_tod_spin_comp_%s.png' % name))
            with open(os.path.join(dst, 'i_tod_spin_ico_comp_%s.png' % name), 'wb') as f:
                f.write(mga.encode(icons[name]))
    if not a.no_review:
        print('review ->', review(ports, icons, out_dir, mga.encode))


if __name__ == '__main__':
    main()
