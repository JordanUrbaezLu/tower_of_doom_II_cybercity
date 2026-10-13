"""THE WUNDERSTRAHL'S BEAM - the review sheets. NOT a gate and NOT the engine's renderer: a schematic particle simulation of
the generated .efx files and beam fields, at a game-like camera, so a reviewer can judge layout, timing, footprint, colour
and the read of the helix - not the final native look (bloom, HDR, the real textures' filtering and the engine's own
beam / beamEffect placement are approximated; see the notes printed on each sheet).

  python tools/wunderstrahl/fx/preview.py [--fx-root DIR] [--out DIR]

  --fx-root  where the .efx + the GDT live (default tmp/wunderstrahl/stage, then the repo)
  --out      default art/wunderstrahl/fx_review

Writes:
  beam_diagram.png    the beam's anatomy: core + double helix + orbs + sheath, side and end-on, 1p and 3p, with the numbers
  view_1p.png         what the shooter sees: the beam from the lens to a wall 600 u away (four moments of a held beam)
  view_3p.png         a teammate's side view 420 u from the beam: ignition -> full swirl -> the wall burn
  contact_sheet.png   every effect at three moments, close up
  textures.png        the generated textures on dark and on checker
  anim_1p.gif / anim_3p.gif   one second of a held beam at steady state (30 fps): the spin, the orbs, the sparks
The simulation reads every number from the files: spawn counts / delays / loops, lives, origins and sphere / cylinder
offsets, local + world velocity graphs (curve A/B mixed per particle), gravity (% of 800 u/s^2), size / colour / alpha
graphs, the near-camera fade. Emissive sprites are additive Gaussians (sigma = size / 3), lit ones alpha-blended dark,
'line' sprites strokes along their graph velocity (size0 wide, size1 long), tails strokes along their motion. The aura
instances ride the beam the way docs/219 assumes the engine moves them: born at the lens every distance / speed seconds,
carried outward at beamEffectSpeed, retired at the beam's end.
"""
import argparse
import math
import pathlib
import sys

sys.dont_write_bytecode = True
import numpy as np                                                    # noqa: E402
from PIL import Image, ImageDraw, ImageFont                            # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools' / 'sky_ships'))
import efx_lib as E                                                   # noqa: E402
import importlib.util                                                 # noqa: E402

spec = importlib.util.spec_from_file_location('ws_make_fx_preview', pathlib.Path(__file__).resolve().parent / 'make_fx.py')
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

BG = np.array((0.035, 0.038, 0.05))
EMISSIVE_HINTS = ('_em', 'phosphorous', 'incandescent', 'orb', 'core_hot', 'spark', 'mtl_tod2_ws', 'flame', 'ring')


def font(sz):
    for f in ('C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/arial.ttf'):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


# ---- curves ---------------------------------------------------------------------------------------------------------------
def curve_at(rows, t):
    t = min(1.0, max(0.0, t))
    for a, b in zip(rows, rows[1:]):
        if a[0] <= t <= b[0]:
            k = 0.0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
            return [a[i] + (b[i] - a[i]) * k for i in range(1, len(a))]
    return list(rows[-1][1:])


def graph_at(e, key, t, mix):
    g = e.graph(key)
    a, b = curve_at(g.curves[0], t), curve_at(g.curves[1], t)
    return [g.scale * (x + (y - x) * mix) for x, y in zip(a, b)]


# ---- camera ---------------------------------------------------------------------------------------------------------------
class Cam:
    def __init__(self, pos, target, w, h, fov=80.0):
        self.p = np.array(pos, float)
        f = np.array(target, float) - self.p
        self.f = f / np.linalg.norm(f)
        r = np.cross(self.f, [0, 0, 1.0])
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.r, self.f)
        self.w, self.h = w, h
        self.fpx = (w / 2) / math.tan(math.radians(fov / 2))

    def project(self, q):
        d = np.asarray(q, float) - self.p
        z = d @ self.f
        if z < 1:
            return None
        return (self.w / 2 + (d @ self.r) / z * self.fpx, self.h / 2 - (d @ self.u) / z * self.fpx, z)


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.buf = np.tile(BG, (h, w, 1)).astype(np.float64)

    def splat(self, x, y, sigma, rgb, a, additive=True):
        sigma = max(0.6, sigma)
        r = int(math.ceil(sigma * 3))
        x0, x1 = max(0, int(x) - r), min(self.w, int(x) + r + 1)
        y0, y1 = max(0, int(y) - r), min(self.h, int(y) + r + 1)
        if x0 >= x1 or y0 >= y1:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sigma * sigma)) * a
        if additive:
            self.buf[y0:y1, x0:x1] += g[..., None] * np.asarray(rgb)
        else:
            self.buf[y0:y1, x0:x1] = self.buf[y0:y1, x0:x1] * (1 - g[..., None]) + g[..., None] * np.asarray(rgb)

    def segment_field(self, p0, p1, sigma):
        """(y0, y1, x0, x1, g): a Gaussian of the distance to the segment p0-p1 over its bounding box."""
        sigma = max(0.6, sigma)
        r = sigma * 3
        x0, x1 = max(0, int(min(p0[0], p1[0]) - r)), min(self.w, int(max(p0[0], p1[0]) + r) + 1)
        y0, y1 = max(0, int(min(p0[1], p1[1]) - r)), min(self.h, int(max(p0[1], p1[1]) + r) + 1)
        if x0 >= x1 or y0 >= y1:
            return None
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ll = dx * dx + dy * dy
        if ll < 1e-9:
            d2 = (xx - p0[0]) ** 2 + (yy - p0[1]) ** 2
        else:
            t = np.clip(((xx - p0[0]) * dx + (yy - p0[1]) * dy) / ll, 0, 1)
            d2 = (xx - p0[0] - t * dx) ** 2 + (yy - p0[1] - t * dy) ** 2
        return y0, y1, x0, x1, np.exp(-d2 / (2 * sigma * sigma))

    def stroke(self, p0, p1, width, rgb, a, additive=True):
        f = self.segment_field(p0, p1, width / 2.2)
        if f is None:
            return
        y0, y1, x0, x1, g = f
        g = g * a
        if additive:
            self.buf[y0:y1, x0:x1] += g[..., None] * np.asarray(rgb)
        else:
            self.buf[y0:y1, x0:x1] = self.buf[y0:y1, x0:x1] * (1 - g[..., None]) + g[..., None] * np.asarray(rgb)

    def textured(self, c, ax, half_len, half_wid, tex, tint, a):
        """An additive quad wearing `tex` (premultiplied RGB): centre c, unit axis ax along its length (texture U)."""
        ax = np.asarray(ax, float)
        ax = ax / (np.linalg.norm(ax) + 1e-9)
        ay = np.array([-ax[1], ax[0]])
        ext = abs(ax[0]) * half_len + abs(ay[0]) * half_wid, abs(ax[1]) * half_len + abs(ay[1]) * half_wid
        x0, x1 = max(0, int(c[0] - ext[0]) - 1), min(self.w, int(c[0] + ext[0]) + 2)
        y0, y1 = max(0, int(c[1] - ext[1]) - 1), min(self.h, int(c[1] + ext[1]) + 2)
        if x0 >= x1 or y0 >= y1:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
        s = ((xx - c[0]) * ax[0] + (yy - c[1]) * ax[1]) / max(half_len, 0.5)
        t = ((xx - c[0]) * ay[0] + (yy - c[1]) * ay[1]) / max(half_wid, 0.5)
        inside = (np.abs(s) <= 1) & (np.abs(t) <= 1)
        th, tw = tex.shape[:2]
        u = np.clip((s + 1) / 2 * (tw - 1), 0, tw - 1)
        v = np.clip((t + 1) / 2 * (th - 1), 0, th - 1)
        i0, j0 = np.floor(v).astype(int), np.floor(u).astype(int)
        i1, j1 = np.minimum(i0 + 1, th - 1), np.minimum(j0 + 1, tw - 1)
        fv, fu = (v - i0)[..., None], (u - j0)[..., None]
        smp = (tex[i0, j0] * (1 - fu) * (1 - fv) + tex[i0, j1] * fu * (1 - fv) + tex[i1, j0] * (1 - fu) * fv
               + tex[i1, j1] * fu * fv)
        add = smp[..., :3] * np.asarray(tint) * a * inside[..., None]
        self.buf[y0:y1, x0:x1] += add * 1.6      # the material's HDR gain, roughly (preview only)

    def image(self):
        x = self.buf
        x = x / (1 + 0.35 * x)                      # soft tone curve: bright cores roll off instead of clipping flat
        x = np.clip(x * 1.25, 0, 1) ** (1 / 1.15)
        return Image.fromarray((x * 255).astype(np.uint8))


# ---- the particle simulation ---------------------------------------------------------------------------------------------
def spawn_times(e, t_now, rng):
    d0, dr = e.nums('spawnDelayMsec')
    d = d0 + dr * rng.random()
    if 'looping' in e.flags('editorFlags'):
        interval, count = e.nums('spawnLooping')
        pb, pr = e.nums('spawnLoopingSpawnCount')
        out, k, t = [], 0, d
        while t <= t_now and (count <= 0 or k < count):
            out += [t] * max(1, int(pb + pr * rng.random()))
            k += 1
            t = d + k * max(1, interval)
        return out
    n0, nr = e.nums('spawnOneShot')
    return [d] * int(n0 + nr * rng.random())


def kind_of(e):
    t, mats = e.visual
    m = (mats[0] if mats else '').lower()
    if t == 'dynamicLight2':
        return 'light'
    if t == 'line':
        return 'line'
    if t == 'tail':
        return 'tail'
    if t == 'rotatedSprite':
        return 'disc'
    if '_lit' in m:
        return 'lit'
    return 'glow'


def simulate(fx, t_ms, origin, axes, seed=7, origin_at=None):
    """-> particles at effect time t_ms: (kind, pos, dir, size0, size1, rgb, alpha, fade). axes rows = local X/Y/Z in world.
    origin_at(ms) -> the carrier's origin at that time (runRelToEffect follows it; world-run particles stay)."""
    out = []
    axes = np.asarray(axes, float)
    for ei, e in enumerate(fx.elements):
        rng = np.random.default_rng(seed * 1000 + ei)
        kind = kind_of(e)
        if kind == 'light':
            continue
        life0, lifer = e.nums('lifeSpanMsec')
        flags = e.flags('flags')
        run_world = 'runRelToWorld' in flags
        for ts in spawn_times(e, t_ms, rng):
            life = life0 + lifer * rng.random()
            age = t_ms - ts
            if age < 0 or age >= life or life <= 0:
                continue
            tau = age / life
            mix = rng.random()                       # one per graph below; velocity gets one per axis (the engine's
            vmix_l, vmix_w = rng.random(3), rng.random(3)   # "random pick between curve A and B per particle, per axis")
            sp = np.array([e.nums('spawnOrg' + a)[0] + e.nums('spawnOrg' + a)[1] * rng.random() for a in 'XYZ'])
            if 'spawnOffsetSphere' in flags:
                r0, rr = e.nums('spawnOffsetRadius')
                v = rng.normal(size=3)
                sp += v / (np.linalg.norm(v) + 1e-9) * (r0 + rr * rng.random())
            elif 'spawnOffsetCylinder' in flags:
                r0, rr = e.nums('spawnOffsetRadius')
                ang = rng.random() * 2 * math.pi
                sp += np.array([0, math.cos(ang), math.sin(ang)]) * (r0 + rr * rng.random())
            # integrate the velocity graphs (local + world) and gravity
            steps = 16
            pos_l = np.zeros(3)
            pos_w = np.zeros(3)
            dt = age / 1000.0 / steps
            lv = wv = None
            for k in range(steps):
                tk = (k + 0.5) / steps * tau
                lv = np.array([graph_at(e, 'velGraph0' + a, tk, vmix_l[i])[0] for i, a in enumerate('XYZ')])
                wv = np.array([graph_at(e, 'velGraph1' + a, tk, vmix_w[i])[0] for i, a in enumerate('XYZ')])
                pos_l += lv * dt
                pos_w += wv * dt
            lv = np.array([graph_at(e, 'velGraph0' + a, tau, vmix_l[i])[0] for i, a in enumerate('XYZ')])
            wv = np.array([graph_at(e, 'velGraph1' + a, tau, vmix_w[i])[0] for i, a in enumerate('XYZ')])
            g0, gr = e.nums('gravity')
            grav = (g0 + gr * rng.random()) / 100.0 * 800.0
            pos_w[2] -= 0.5 * grav * (age / 1000.0) ** 2
            if run_world and origin_at is not None:
                o = np.asarray(origin_at(ts), float)
            else:
                o = np.asarray(origin_at(t_ms) if origin_at else origin, float)
            pos = o + (sp + pos_l) @ axes + pos_w
            direction = (lv @ axes) + wv
            size0 = graph_at(e, 'sizeGraph0', tau, mix)[0]
            size1 = graph_at(e, 'sizeGraph1', tau, mix)[0]
            rgb = graph_at(e, 'colorGraph', tau, mix)
            a = graph_at(e, 'alphaGraph', tau, mix)[0]
            fade = e.nums('fadeOutRange')
            out.append((kind, pos, direction, size0, size1, rgb, a, fade, e.visual[1][0] if e.visual[1] else ''))
    return out


_TEX = {}


def tex_of(mat):
    """Our generated materials' textures (premultiplied, 0..1) for the textured quads; None for stock materials."""
    names = {M.MAT_STRAND: M.IMG_STRAND, M.MAT_ORB: M.IMG_ORB, M.MAT_BURN: M.IMG_BURN}
    if mat not in names:
        return None
    if mat not in _TEX:
        _TEX[mat] = np.asarray(Image.open(M.tex_path(names[mat])).convert('RGBA')).astype(np.float64) / 255.0
    return _TEX[mat]


def draw_particles(cv, cam, parts, bright=1.0):
    order = sorted(parts, key=lambda p: -np.dot(p[1] - cam.p, cam.f))      # far first
    for kind, pos, d, s0, s1, rgb, a, fade, mat in order:
        q = cam.project(pos)
        if q is None:
            continue
        x, y, z = q
        if fade[1] > 0:
            a *= min(1.0, max(0.0, (z - fade[0]) / fade[1]))
        if a <= 0.004:
            continue
        px = s0 * cam.fpx / z
        col = np.asarray(rgb) * bright
        tex = tex_of(mat)
        if tex is not None:                      # size read as the sprite's full width (see the README)
            if kind == 'line':
                n = np.linalg.norm(d)
                if n > 1e-6:
                    dn = d / n
                    p0 = cam.project(pos - dn * s1 * 0.5)
                    p1 = cam.project(pos + dn * s1 * 0.5)
                    if p0 is not None and p1 is not None:
                        axis = (p1[0] - p0[0], p1[1] - p0[1])
                        cv.textured(((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), axis,
                                    max(0.6, math.hypot(*axis) / 2), max(0.6, px / 2), tex, col, a)
                continue
            cv.textured((x, y), (1, 0), max(0.6, px / 2), max(0.6, px / 2), tex, col, a)
            continue
        if kind == 'lit':
            cv.splat(x, y, px / 3, col * 0.35, min(1.0, a * 0.9), additive=False)
        elif kind in ('line', 'tail'):
            n = np.linalg.norm(d)
            if n < 1e-6:
                cv.splat(x, y, px / 3, col, a)
                continue
            dn = d / n
            length = s1 if kind == 'line' else max(s0 * 2.0, n * 0.035)
            p0 = cam.project(pos - dn * length * 0.5)
            p1 = cam.project(pos + dn * length * 0.5)
            if p0 is None or p1 is None:
                continue
            cv.stroke(p0, p1, max(1.0, px), col, a)
        else:
            cv.splat(x, y, px / 3, col, a)


def draw_core(cv, cam, start, fwd, length, f, scale=1.0):
    """The beam (a camera-facing ribbon), approximated: a tapered line from the lens (startWidth -> endWidth over
    maxLength), three layers (white-hot centre, yellow body, a faint bloom) standing in for the core texture's profile,
    each MAX-blended along the polyline so its density never stacks. It reads the widths and colours only: the material's
    scaleRGB brightness, any view falloff and the scrolling texture are NOT modelled, so the core's brightness here says
    nothing about the native one."""
    sw, ew = float(f['startWidth']), float(f['endWidth'])
    sc = [float(x) for x in f['startColor'].split()]
    ec = [float(x) for x in f['endColor'].split()]
    maxl = float(f['maxLength'])
    fwd = np.asarray(fwd, float) / np.linalg.norm(fwd)
    pts = []
    s = 0.0
    while True:
        p = np.asarray(start) + fwd * s
        q = cam.project(p)
        if q is not None:
            k = s / maxl
            pts.append((q, sw + (ew - sw) * k, np.array([sc[i] + (ec[i] - sc[i]) * k for i in range(3)]),
                        sc[3] + (ec[3] - sc[3]) * k))
        if s >= length:
            break
        s = min(length, s + max(0.5, (np.dot(p - cam.p, cam.f)) * 0.02))
    for frac, sig_k, gain, white in ((1.0, 0.32, 1.0, True), (1.0, 0.8, 0.45, False), (1.0, 2.6, 0.07, False)):
        layer = np.zeros((cv.h, cv.w))
        tint = np.zeros((cv.h, cv.w, 3))
        for (q0, w0, c0, a0), (q1, w1, c1, a1) in zip(pts, pts[1:]):
            px = max(0.8, (w0 * cam.fpx / q0[2] + w1 * cam.fpx / q1[2]) * 0.5)
            fld = cv.segment_field(q0[:2], q1[:2], px * sig_k)
            if fld is None:
                continue
            y0, y1, x0, x1, g = fld
            g = g * (a0 + a1) * 0.5
            better = g > layer[y0:y1, x0:x1]
            layer[y0:y1, x0:x1] = np.where(better, g, layer[y0:y1, x0:x1])
            col = np.array((1.0, 0.98, 0.9)) if white else (c0 + c1) * 0.5
            tint[y0:y1, x0:x1][better] = col
        cv.buf += layer[..., None] * tint * gain * scale


def aura_instances(key, t_ms, length):
    """(birth ms, distance) of every live aura instance at beam time t_ms: born at the lens every D / speed, carried out."""
    v = M.AURA[key]
    D = M.aura_dist(key)
    period = D / v['speed'] * 1000.0
    out = []
    n = int(math.floor(t_ms / period))            # births at fixed times n x period from the trigger (a conveyor)
    while n >= 0:
        birth = n * period
        dist = (t_ms - birth) / 1000.0 * v['speed']
        if dist > length:
            break
        out.append((birth, dist))
        n -= 1
    return out


def beam_axes(fwd):
    f = np.asarray(fwd, float)
    f = f / np.linalg.norm(f)
    up = np.array([0, 0, 1.0])
    y = np.cross(up, f)
    y = y / np.linalg.norm(y)
    z = np.cross(f, y)
    return np.array([f, y, z])


# ---- loading ------------------------------------------------------------------------------------------------------------------
def load_set(fx_root):
    fxs = {}
    for n in M.NAMES:
        p = fx_root / M.FX_REL / (n + '.efx')
        if not p.exists():
            p = ROOT / M.FX_REL / (n + '.efx')
        fxs[n] = E.load(p)
    gp = fx_root / M.GDT_REL
    if not gp.exists():
        gp = ROOT / M.GDT_REL
    text = gp.read_text(encoding='utf-8')
    beams = {}
    for m in M.BLOCK_RE.finditer(text):
        if m.group(2) == 'beam.gdf':
            beams[m.group(1)] = dict(M.parse_fields(m.group(0)))
    return fxs, beams


def label(img, lines, xy=(14, 10), sz=17, fill=(235, 228, 205)):
    d = ImageDraw.Draw(img)
    f = font(sz)
    x, y = xy
    for ln in lines:
        d.text((x + 1, y + 1), ln, font=f, fill=(0, 0, 0))
        d.text((x, y), ln, font=f, fill=fill)
        y += sz + 5
    return img


# ---- the sheets ------------------------------------------------------------------------------------------------------------
def render_beam_scene(fxs, beams, key, cam, start, fwd, wall_at, t_ms, w, h, show_origin=True, normal=None):
    cv = Canvas(w, h)
    f = beams[M.BEAM_1P if key == '1p' else M.BEAM_3P]
    length = min(float(f['maxLength']), wall_at, t_ms / 1000.0 * M.BEAM_LAUNCH_SPEED)
    axes = beam_axes(fwd)
    start = np.asarray(start, float)
    fwd_n = axes[0]
    # the wall burn (blockedEffect) - played while the beam is stopped; +X out of the wall
    if length >= wall_at - 1e-6:
        reach_ms = wall_at / M.BEAM_LAUNCH_SPEED * 1000.0
        nrm = np.asarray(normal if normal is not None else -fwd_n, float)
        imp_axes = beam_axes(nrm)
        hit = start + fwd_n * wall_at
        draw_particles(cv, cam, simulate(fxs['fx_ws_impact'], max(0.0, t_ms - reach_ms), hit, imp_axes,
                                         origin_at=lambda ms: hit))
    draw_core(cv, cam, start, fwd_n, length, f, scale=1.0 if key == '1p' else 1.2)
    aura = fxs['fx_ws_aura_' + key]
    for birth, dist in aura_instances(key, t_ms, length):
        o = start + fwd_n * dist
        spd = M.AURA[key]['speed']
        draw_particles(cv, cam, simulate(aura, t_ms - birth, o, axes, seed=int(birth) % 997,
                                         origin_at=lambda ms, b=birth: start + fwd_n * (ms / 1000.0 * spd)))
    if show_origin:
        draw_particles(cv, cam, simulate(fxs['fx_ws_origin_' + key], t_ms, start, axes, origin_at=lambda ms: start))
    return cv


def view_1p(fxs, beams, out):
    """Rendered at a true 1920 x 1080 frame (80 deg FOV), then the region round the beam is cropped and shown 1.5x, so a
    pixel of the crop is a 1080p screen pixel enlarged - the size a player actually sees."""
    W, H = 1920, 1080
    eye = np.array([0.0, 0.0, 64.0])
    cam = Cam(eye, eye + np.array([100.0, 0, 0]), W, H, fov=80)
    muzzle = eye + np.array([42.0, -8.0, -6.0])          # tag_flash in view space: 42 forward, 8 right, 6 down (approx.)
    target = eye + np.array([600.0, 0, 0])
    fwd = target - muzzle
    crop = (W // 2 - 260, H // 2 - 150, W // 2 + 420, H // 2 + 280)    # 680 x 430 round the lens -> the crosshair
    zoom = 1.5
    pw, ph = int((crop[2] - crop[0]) * zoom), int((crop[3] - crop[1]) * zoom)
    panels = []
    for t in (90, 400, 1100, 2400):
        cv = render_beam_scene(fxs, beams, '1p', cam, muzzle, fwd, np.linalg.norm(fwd), t, W, H)
        img = cv.image().crop(crop).resize((pw, ph), Image.LANCZOS)
        d = ImageDraw.Draw(img)
        cx, cy = (W // 2 - crop[0]) * zoom, (H // 2 - crop[1]) * zoom
        d.line([(cx - 9, cy), (cx - 4, cy)], fill=(200, 200, 200))
        d.line([(cx + 4, cy), (cx + 9, cy)], fill=(200, 200, 200))
        label(img, ['1p  t = %d ms after the trigger' % t,
                    'wall %d u away; launch %d u/s; + = the crosshair' % (int(np.linalg.norm(fwd)), M.BEAM_LAUNCH_SPEED)], sz=16)
        panels.append(img)
    sheet = Image.new('RGB', (pw * 2, ph * 2 + 70), (12, 12, 16))
    for i, p in enumerate(panels):
        sheet.paste(p, ((i % 2) * pw, 70 + (i // 2) * ph))
    label(sheet, ['THE WUNDERSTRAHL - what the shooter sees (schematic simulation of the generated files; not the engine)',
                  '1080p frame, 80 deg FOV, lens 42 u ahead / 8 right / 6 down, cropped round the beam and shown 1.5x; the swirl '
                  'corkscrews out at %d u/s and lives %d u' % (M.AURA['1p']['speed'], M.AURA['1p']['reach'])], sz=19)
    sheet.save(out / 'view_1p.png')


def view_3p(fxs, beams, out):
    w, h = 1600, 420
    shooter = np.array([0.0, 0.0, 56.0])
    fwd = np.array([1.0, 0, 0])
    wall = 820.0
    cam = Cam((410.0, -470.0, 90.0), (410.0, 0.0, 56.0), w, h, fov=90)
    panels = []
    for t in (180, 900, 2600):
        cv = render_beam_scene(fxs, beams, '3p', cam, shooter, fwd, wall, t, w, h, normal=(-1, 0, 0))
        img = cv.image()
        label(img, ['3p (a teammate 470 u to the side)  t = %d ms' % t], sz=17)
        panels.append(img)
    sheet = Image.new('RGB', (w, h * 3 + 60), (12, 12, 16))
    for i, p in enumerate(panels):
        sheet.paste(p, (0, 60 + i * h))
    label(sheet, ['THE WUNDERSTRAHL - a teammate\'s view: ignition -> the full golden swirl -> the burn-through at a wall 820 u out',
                  '3p helix r %g pitch %g, %d turns per instance (beamEffectDistance %g), %d u/s = %.1f turns/s apparent spin'
                  % (M.AURA['3p']['r'], M.AURA['3p']['pitch'], M.AURA['3p']['turns'], M.aura_dist('3p'), M.AURA['3p']['speed'],
                     M.AURA['3p']['speed'] / M.AURA['3p']['pitch'])], sz=18)
    sheet.save(out / 'view_3p.png')


def animations(fxs, beams, out, frames=30, fps=30):
    """anim_1p.gif / anim_3p.gif: one second of a held beam at steady state (the helix sliding out = spinning, the orbs
    spiralling, the sparks), so the MOTION can be judged - a still cannot show either."""
    # 1p: the true 1080p frame, cropped round the beam, as view_1p
    W, H = 1920, 1080
    eye = np.array([0.0, 0.0, 64.0])
    cam = Cam(eye, eye + np.array([100.0, 0, 0]), W, H, fov=80)
    muzzle = eye + np.array([42.0, -8.0, -6.0])
    fwd = eye + np.array([600.0, 0, 0]) - muzzle
    crop = (W // 2 - 140, H // 2 - 80, W // 2 + 300, H // 2 + 200)
    imgs = []
    for i in range(frames):
        t = 3000 + i * 1000.0 / fps
        cv = render_beam_scene(fxs, beams, '1p', cam, muzzle, fwd, np.linalg.norm(fwd), t, W, H)
        imgs.append(cv.image().crop(crop).resize(((crop[2] - crop[0]) * 2, (crop[3] - crop[1]) * 2), Image.LANCZOS))
    imgs[0].save(out / 'anim_1p.gif', save_all=True, append_images=imgs[1:], duration=int(1000 / fps), loop=0)
    # 3p: a teammate 220 u to the side of the swirl's first stretch (a 1080p frame, 80 deg FOV, cropped round the beam)
    w, h = 1920, 1080
    shooter = np.array([0.0, 0.0, 56.0])
    cam3 = Cam((170.0, -220.0, 66.0), (170.0, 0.0, 56.0), w, h, fov=80)
    imgs = []
    for i in range(frames):
        t = 3000 + i * 1000.0 / fps
        cv = render_beam_scene(fxs, beams, '3p', cam3, shooter, np.array([1.0, 0, 0]), 820.0, t, w, h, normal=(-1, 0, 0))
        imgs.append(cv.image().crop((0, 470, 1920, 640)))
    imgs[0].save(out / 'anim_3p.gif', save_all=True, append_images=imgs[1:], duration=int(1000 / fps), loop=0)


def contact_sheet(fxs, out):
    rows = [
        ('fx_ws_origin_1p', (0, 0, 0), (-26, -14, 6), (6, 0, 0), (120, 400, 900), 'looping at the lens (1p): hot point, halo, 6 orbiting sparks, outflow motes'),
        ('fx_ws_origin_3p', (0, 0, 0), (-50, -30, 14), (10, 0, 0), (120, 400, 900), 'looping at the lens (3p)'),
        ('fx_ws_impact', (0, 0, 0), (110, -80, 40), (20, 0, 0), (150, 700, 1600), 'blockedEffect, looping; local X = out of the wall (the wall is the YZ plane); the burn disc lies still on it'),
        ('fx_ws_tip', (0, 0, 0), (-60, -40, 10), (0, 0, 0), (120, 500, 1200), 'targetEffect: the beam\'s end in open air'),
        ('fx_ws_lens_cool', (0, 0, 0), (-18, -10, 4), (2, 0, 2), (60, 300, 800), 'deathEffect at the lens after the release'),
        ('fx_ws_zombie_burn', (0, 0, 50), (-90, -60, 20), (0, 0, 8), (40, 160, 380), 'script, <= ~3/s per zombie: flash, sparks, embers, flame licks, soot'),
        ('fx_ws_disintegrate', (0, 0, 50), (-210, -150, 60), (0, 0, 15), (60, 300, 1100), 'script, the kill: flash + ring, ember burst, orbs, ash puff, a small light (fx_ws_disintegrate_nl: the same, no light)'),
    ]
    w, h = 420, 260
    sheet = Image.new('RGB', (w * 3 + 380, h * len(rows) + 60), (12, 12, 16))
    label(sheet, ['THE WUNDERSTRAHL - every effect at three moments (schematic simulation; sizes in true units at the stated camera)'], sz=19)
    for r, (name, org, campos, look, times, note) in enumerate(rows):
        axes = np.eye(3)
        if name == 'fx_ws_impact':
            axes = beam_axes((-1, 0, 0))        # the wall faces -X: local X = (-1, 0, 0) toward the camera side
            campos = (-110, -80, 40)
            look = (-20, 0, 0)
        cam = Cam(np.array(campos, float) + np.array(org, float), np.array(look, float) + np.array(org, float), w, h, fov=60)
        for c, t in enumerate(times):
            cv = Canvas(w, h)
            draw_particles(cv, cam, simulate(fxs[name], t, org, axes, origin_at=lambda ms, o=org: o))
            img = cv.image()
            label(img, ['%d ms' % t], sz=15)
            sheet.paste(img, (c * w, 60 + r * h))
        d = ImageDraw.Draw(sheet)
        d.text((w * 3 + 12, 60 + r * h + 12), name, font=font(18), fill=(255, 220, 140))
        y = 60 + r * h + 40
        for chunk in _wrap(note, 36):
            d.text((w * 3 + 12, y), chunk, font=font(14), fill=(220, 220, 220))
            y += 20
        fx = fxs[name]
        peak = sum(M.peak_particles(e) for e in fx.elements if e.visual[0] != 'dynamicLight2')
        lights = sum(1 for e in fx.elements if e.visual[0] == 'dynamicLight2')
        d.text((w * 3 + 12, y + 6), '%d elements, peak ~%d particles, %d light' % (len(fx.elements), peak, lights),
               font=font(14), fill=(160, 200, 255))
    sheet.save(out / 'contact_sheet.png')


def _wrap(s, n):
    words, line, out = s.split(), '', []
    for w in words:
        if len(line) + len(w) + 1 > n:
            out.append(line)
            line = w
        else:
            line = (line + ' ' + w).strip()
    if line:
        out.append(line)
    return out


def beam_diagram(out):
    W, H = 1600, 1230
    img = Image.new('RGB', (W, H), (14, 14, 19))
    d = ImageDraw.Draw(img)
    f18, f15, f22 = font(18), font(15), font(24)
    d.text((24, 14), 'THE WUNDERSTRAHL BEAM - anatomy (schematic; numbers from tools/wunderstrahl/fx/make_fx.py)', font=f22, fill=(255, 225, 150))
    y0 = 70
    for key in ('1p', '3p'):
        v = M.AURA[key]
        c = M.CORE[key]
        D = M.aura_dist(key)
        R, P = v['r'], v['pitch']
        scale = 600.0 / (2 * D)
        cx0, cy = 60, y0 + 190
        fo = ('falloff %d-%d deg' % M.FALLOFF) if c['falloff'] else 'no falloff'
        d.text((24, y0), '%s beam   core %g -> %g u wide (%s, scroll %.1f UV/s, %s)   helix r %g, pitch %g, '
               'a major + a minor strand 180 deg apart, %d turns per instance = beamEffectDistance %g, out at %d u/s (%.1f turns/s)'
               % (key, c['start_w'], c['end_w'], M.BEAM_SHAPE, M.CORE_SCROLL_U, fo, R, P, v['turns'], D, v['speed'],
                  v['speed'] / P), font=f15, fill=(230, 230, 230))
        d.text((24, y0 + 22), 'side view: two instances back to back (the thin vertical lines are the instance seams: the helix runs '
               'on unbroken across them); %d segments / turn,' % v['segs'], font=f15, fill=(200, 200, 200))
        d.text((24, y0 + 42), 'an orb per strand per turn (drawn where it starts; it slips back along its strand at %d u/s), %d sheath '
               'glows, motes on a shell' % (v['slip'], v['sheath_n']), font=f15, fill=(200, 200, 200))
        # the core
        for k in range(14, 0, -1):
            a = int(10 + 18 * (14 - k) / 14)
            d.line([(cx0, cy), (cx0 + 2 * D * scale, cy)], fill=(a * 5 if a * 5 < 255 else 255, int(a * 3.6), int(a * 1.2)), width=k * 2)
        d.line([(cx0, cy), (cx0 + 2 * D * scale, cy)], fill=(255, 250, 225), width=3)
        # sheath
        for inst in range(2):
            for k in range(v['sheath_n']):
                x = cx0 + (inst * D + D * (k + 0.5) / v['sheath_n']) * scale
                rr = v['sheath_size'] / 2 * scale
                d.ellipse([x - rr, cy - rr, x + rr, cy + rr], outline=(120, 95, 40))
        # the strands (back half dim, front half bright)
        for inst in range(2):
            d.line([(cx0 + inst * D * scale, cy - 140), (cx0 + inst * D * scale, cy + 140)], fill=(90, 90, 110), width=1)
            for s in (0, 1):
                pts = []
                for i in range(0, 241):
                    t = i / 240.0
                    x = t * D
                    ph = 2 * math.pi * x / P + math.pi * s
                    pts.append((cx0 + (inst * D + x) * scale, cy - R * math.cos(ph) * scale, math.sin(ph)))
                for a, b in zip(pts, pts[1:]):
                    front = (a[2] + b[2]) / 2 > 0
                    if s == 0:     # the major strand: gold
                        d.line([a[:2], b[:2]], fill=(255, 190, 70) if front else (120, 85, 30), width=4 if front else 2)
                    else:          # the minor strand: thinner, dimmer, pale lemon
                        d.line([a[:2], b[:2]], fill=(228, 214, 140) if front else (100, 93, 56), width=2 if front else 1)
                for k in range(v['turns']):
                    segs = v['segs']                 # make_fx.aura()'s starting segment for this orb
                    j = (k * segs + (k * 3 * segs) // 8 + (segs // 4 if s else 0)) % (v['turns'] * segs)
                    pos, _ = M.helix_point(v, s, j)
                    x = cx0 + (inst * D + pos[0]) * scale
                    y = cy - pos[1] * scale
                    rr = v['ball'] / 2 * scale
                    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 245, 210), outline=(255, 150, 40))
        d.text((cx0, cy + 150), '0', font=f15, fill=(180, 180, 180))
        d.text((cx0 + D * scale - 10, cy + 150), '%g u' % D, font=f15, fill=(180, 180, 180))
        d.text((cx0 + 2 * D * scale - 20, cy + 150), '%g u' % (2 * D), font=f15, fill=(180, 180, 180))
        d.text((cx0 + 2 * D * scale + 20, cy - 8), '-> outward (+X, the beam)', font=f15, fill=(200, 200, 200))
        # end-on
        ex, ey, es = 1240, cy, 34.0 if key == '1p' else 22.0
        d.ellipse([ex - v['sheath_size'] / 2 * es, ey - v['sheath_size'] / 2 * es, ex + v['sheath_size'] / 2 * es,
                   ey + v['sheath_size'] / 2 * es], outline=(120, 95, 40))
        d.ellipse([ex - R * es, ey - R * es, ex + R * es, ey + R * es], outline=(150, 110, 45), width=2)
        cw = c['start_w'] * es / 2
        d.ellipse([ex - cw, ey - cw, ex + cw, ey + cw], fill=(255, 250, 225))
        for s in (0, 1):
            for j in range(v['segs']):
                pos, tan = M.helix_point(v, s, j)
                x, y = ex + pos[1] * es, ey - pos[2] * es
                seg = (math.hypot(P, 2 * math.pi * R) / v['segs'] * v['overlap'])
                dx, dy = tan[1] * seg * es / 2, -tan[2] * seg * es / 2
                d.line([(x - dx, y - dy), (x + dx, y + dy)], fill=(255, 190, 70), width=4)
        d.text((ex - 120, ey + R * es + 16), 'end-on (looking down the beam): the strands\' segments', font=f15, fill=(200, 200, 200))
        d.text((ex - 120, ey + R * es + 36), 'tangent to the circle of radius %g; the core %g u at the lens' % (R, c['start_w']),
               font=f15, fill=(200, 200, 200))
        y0 += 520
    notes = [
        'How it moves: every beamEffect instance carries exactly %d full turns, so the instances spawned every beamEffectDistance tile one'
        % M.AURA['1p']['turns'],
        'continuous double helix; the whole helix slides outward at beamEffectSpeed, and a helix sliding along its axis reads as spinning.',
        'Each orb slips back along its strand (a point FIXED on a sliding helix only moves straight ahead), so in the world it spirals',
        'outward at speed + slip. Past the swirl reach the instances are empty and the beam is the core alone.',
        'Assumed engine behaviour (to verify in the first playtest): instances are born at the lens and retired at the beam\'s end.',
    ]
    for i, n in enumerate(notes):
        d.text((24, H - 20 - 22 * len(notes) + i * 22), n, font=f15, fill=(230, 210, 170))
    img.save(out / 'beam_diagram.png')


def textures_sheet(out):
    names = list(M.TEXTURES)
    wide = (M.IMG_CORE, M.IMG_CORE_ADD)
    tiles = []
    for n in names:
        im = Image.open(M.tex_path(n)).convert('RGBA')
        target = (512, 128) if n in wide else (256, 256)
        im = im.resize(target, Image.BILINEAR if n in wide else Image.NEAREST)
        dark = Image.new('RGBA', im.size, (10, 10, 14, 255))
        dark.alpha_composite(im)
        chk = Image.new('RGBA', im.size, (0, 0, 0, 255))
        cd = ImageDraw.Draw(chk)
        for yy in range(0, im.size[1], 16):
            for xx in range(0, im.size[0], 16):
                if (xx // 16 + yy // 16) % 2:
                    cd.rectangle([xx, yy, xx + 15, yy + 15], fill=(90, 90, 96, 255))
        chk.alpha_composite(im)
        tiles.append((n, dark, chk))
    W = 40 + 2 * (512 + 30)
    H = 70 + sum(t[1].size[1] + 60 for t in tiles)
    sheet = Image.new('RGB', (W, H), (14, 14, 19))
    d = ImageDraw.Draw(sheet)
    d.text((20, 16), 'THE WUNDERSTRAHL - the generated textures (left: on dark; right: alpha over checker)', font=font(20), fill=(255, 225, 150))
    y = 70
    for n, dark, chk in tiles:
        im0 = Image.open(M.tex_path(n))
        d.text((20, y), '%s  (%dx%d RGBA; %s)' % (n, im0.size[0], im0.size[1],
                                                {M.IMG_CORE: 'beam core: U along the beam; across it a soft profile, white-hot axis, clear edges',
                                                 M.IMG_CORE_ADD: 'the core premultiplied, for the additive flame-table material',
                                                 M.IMG_STRAND: 'strand segment: a rounded-square plateau, stretched by the line sprite',
                                                 M.IMG_ORB: 'orb: white core, yellow glow, amber halo, faint shell',
                                                 M.IMG_BURN: 'burn-through: molten pool, curling veins, ember glaze, hot specks'}[n]),
               font=font(15), fill=(220, 220, 220))
        sheet.paste(dark.convert('RGB'), (20, y + 26))
        sheet.paste(chk.convert('RGB'), (20 + 512 + 30, y + 26))
        y += dark.size[1] + 60
    sheet.save(out / 'textures.png')


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--fx-root', default=str(ROOT / 'tmp' / 'wunderstrahl' / 'stage'))
    ap.add_argument('--out', default=str(ROOT / 'art' / 'wunderstrahl' / 'fx_review'))
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fxs, beams = load_set(pathlib.Path(a.fx_root))
    beam_diagram(out)
    textures_sheet(out)
    contact_sheet(fxs, out)
    view_1p(fxs, beams, out)
    view_3p(fxs, beams, out)
    animations(fxs, beams, out)
    print('WS FX PREVIEW: beam_diagram, textures, contact_sheet, view_1p, view_3p, anim_1p.gif, anim_3p.gif -> %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
