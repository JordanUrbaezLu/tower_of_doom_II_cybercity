"""THE ELITES' EFFECTS + THE HAVEN MOTES - the review sheet (PK26 / PK43). NOT a gate and NOT the engine's renderer:
a schematic particle simulation of the .efx files themselves, at the real on-screen size, OLD (what ships today) beside
NEW (this pass), so a reviewer can judge timing, footprint, colour and read, not the final look.

  python tools/fxgen/elites/preview.py [--efx-root DIR] [--out DIR]

Every number comes from the effects: spawn counts / delays / finite and forever loops, lives, spawn origins + sphere and
cylinder offsets (axis 0 = local X), local and world velocities (a random mix of curve A and B per particle, per axis),
runRelToOffset (velocity X along the offset's own direction), gravity (% of 800 u/s^2), size / colour / alpha graphs,
near-camera fades, lights (a pool on the floor: intensity x (1 - d / r)^2). Approximations, stated: an emissive sprite is
an additive Gaussian of sigma = size / 3 cut at the size (SIZE READ AS A RADIUS, the PK04 preview's reading); a LIT sprite (smoke, steam, motes) is alpha-blended in
its colour times the light reaching it (an ambient of AMBIENT plus the effect's own lights); a line / tail is a stroke
along its velocity; a trail is the emitter's path over the particle's life; a rotatedSprite in the impact frame is a
ring flat on the floor; an arc is a short jagged stroke; textures and flipbooks are not drawn. The carriers move the way
the scripts move them: the juke along the shipping juke root path (_tod_doppelghast_motion.gsh, side 0), the claw along
the measured claw bone in stn_melee_01 (its XANIM_EXPORT, from the private tools root), the charge with a torso that
sinks as the body falls (frame 61 ragdoll), everything else at rest. The camera: 1920 x 1080, 65 deg horizontal FOV, eye
height 60; each strip is a crop of that frame (640 x 360 .. 960 x 540), so a pixel here is a pixel in game.

Writes <out>/_review.png and one strip per effect (strip_<name>.png).
"""
import argparse
import math
import pathlib
import re
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools' / 'sky_ships'))
import efx_lib as E  # noqa: E402

PRIVATE = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity')
W, H = 1920, 1080
CROP = (640, 360)
FOV = 65.0
AMBIENT = 0.10
OUT_DEFAULT = ROOT / 'art' / 'generated' / 'W2D-elite-haven-fx'
UP_FRAME = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)   # rows: where local X / Y / Z point in the world (angles -90 0 0)
ID_FRAME = np.eye(3)
EMISSIVE_HINTS = ('_em', 'phosphorous', 'incandescent', 'orb_hot', 'core_hot', 'trail_laser', 'shockwave', 'spark', 'elec_arc', 'lightning',
                  'debris_clumps_em', 'flame', 'debug')


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


# ---- the camera -----------------------------------------------------------------------------------------------------------
class Cam:
    def __init__(self, pos, target):
        self.p = np.array(pos, float)
        f = np.array(target, float) - self.p
        self.f = f / np.linalg.norm(f)
        r = np.cross(self.f, [0, 0, 1.0])
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.r, self.f)
        self.fpx = (W / 2) / math.tan(math.radians(FOV / 2))

    def project(self, q):
        d = np.asarray(q, float) - self.p
        z = d @ self.f
        if z < 1:
            return None
        return (W / 2 + (d @ self.r) / z * self.fpx, H / 2 - (d @ self.u) / z * self.fpx, z)


# ---- the particle simulation ------------------------------------------------------------------------------------------------
def rand_dir(rng):
    v = rng.normal(size=3)
    return v / (np.linalg.norm(v) + 1e-9)


def kind_of(e):
    t, mats = e.visual
    m = (mats[0] if mats else '').lower()
    if t == 'dynamicLight2':
        return 'light'
    if t in ('line', 'tail'):
        return 'line'
    if t == 'trail':
        return 'trail_lit' if '_lit' in m else 'trail'
    if t == 'rotatedSprite':
        return 'floor_ring'
    if 'elec_arc' in m or 'lightning' in m:
        return 'arc'
    if '_lit' in m or 'smk_puff' in m or 'fog_slow' in m:
        return 'lit'
    return 'glow'


def spawn_times(e, t_now, rng):
    """[(spawn ms)] for every particle alive or ever spawned up to t_now (ms, effect clock)"""
    d0, dr = e.nums('spawnDelayMsec')
    if 'looping' in e.flags('editorFlags'):
        interval, count = e.nums('spawnLooping')
        pb, pr = e.nums('spawnLoopingSpawnCount')
        per = max(1, int(pb + pr * 0.5))
        out, k, t = [], 0, d0
        while t <= t_now and (count <= 0 or k < count):
            out += [t] * per
            k += 1
            t = d0 + k * max(1, interval)
        return out
    n0, nr = e.nums('spawnOneShot')
    n = int(n0 + nr * rng.random())
    return [d0 + dr * rng.random() for _ in range(n)]


def simulate(fx, t_ms, path, frame, rng_seed=7):
    """-> [(kind, element, world pos, vel dir, size, size1, rgb, alpha, age frac, extra)] at effect time t_ms.
    path(ms) -> the carrier's world origin at that effect time; frame = local->world rows."""
    out = []
    for ei, e in enumerate(fx.elements):
        rng = np.random.default_rng(rng_seed * 1000 + ei)
        if e.visual[0] in ('model', 'runner', 'decal', 'lensFlare', 'cloud', None):
            continue                     # meshes / children / decals / flares / point clouds are not drawn here
        kind = kind_of(e)
        life0, lifer = e.nums('lifeSpanMsec')
        fl = e.flags('flags')
        run = 'world' if 'runRelToWorld' in fl else 'spawn' if 'runRelToSpawn' in fl else 'offset' if 'runRelToOffset' in fl else 'effect'
        ox, oxr = e.nums('spawnOrgX'); oy, oyr = e.nums('spawnOrgY'); oz, ozr = e.nums('spawnOrgZ')
        r0, rr = e.nums('spawnOffsetRadius')
        h0, hr = e.nums('spawnOffsetHeight') if e.has('spawnOffsetHeight') else (0, 0)
        g0, gr = e.nums('gravity')
        for ts in spawn_times(e, t_ms, rng):
            life = life0 + lifer * rng.random()
            age = t_ms - ts
            if age < 0 or age > life or life <= 0:
                continue
            frac = age / life
            local = np.array([ox + oxr * rng.random(), oy + oyr * rng.random(), oz + ozr * rng.random()])
            odir = np.array([1.0, 0, 0])
            if 'spawnOffsetSphere' in fl:
                odir = rand_dir(rng)
                local = local + odir * (r0 + rr * rng.random())
            elif 'spawnOffsetCylinder' in fl:
                a = rng.random() * 2 * math.pi
                odir = np.array([0, math.cos(a), math.sin(a)])
                local = local + odir * (r0 + rr * rng.random()) + np.array([h0 + hr * rng.random(), 0, 0])
            mix = rng.random(); mixv = [rng.random() for _ in range(6)]
            # integrate the velocity over the age
            steps = max(1, int(age / 16))
            dt = age / 1000.0 / steps
            disp_local = np.zeros(3); disp_world = np.zeros(3); v_last = np.zeros(3)
            for s in range(steps):
                tt = (s + 0.5) / steps * frac
                v0 = np.array([graph_at(e, 'velGraph0' + ax, tt, mixv[i])[0] for i, ax in enumerate('XYZ')])
                v1 = np.array([graph_at(e, 'velGraph1' + ax, tt, mixv[3 + i])[0] for i, ax in enumerate('XYZ')])
                if run == 'offset':
                    basis = np.array(odir) if 'spawnOffsetSphere' in fl or 'spawnOffsetCylinder' in fl else np.array([1.0, 0, 0])
                    v0 = basis * v0[0]
                disp_local += v0 * dt
                disp_world += v1 * dt
                v_last = v0 @ frame + v1
            grav = (g0 + gr * mix) / 100.0 * 800.0
            disp_world += np.array([0, 0, -0.5 * grav * (age / 1000.0) ** 2])
            anchor = path(ts) if run in ('world', 'spawn') else path(t_ms)
            pos = anchor + (local + disp_local) @ frame + disp_world
            size = graph_at(e, 'sizeGraph0', frac, mix)[0]
            size1 = graph_at(e, 'sizeGraph1', frac, mix)[0]
            col = graph_at(e, 'colorGraph', frac, 0)
            alpha = graph_at(e, 'alphaGraph', frac, mix)[0]
            extra = None
            if kind in ('trail', 'trail_lit'):
                extra = [path(ts + (age * k / 12.0)) for k in range(13)]
            if kind == 'light':
                extra = (graph_at(e, 'lightIntensityGraph', frac, 0)[0], graph_at(e, 'lightRadiusGraph', frac, 0)[0])
            fade = e.nums('fadeOutRange') if e.has('fadeOutRange') else (0, 0)
            out.append((kind, e.name, pos, v_last, size, size1, col, max(0.0, min(1.0, alpha)), frac, extra, fade))
    return out


# ---- drawing ----------------------------------------------------------------------------------------------------------------
def splat(img, cx, cy, rad, rgb, a, mode='add'):
    rad = max(0.6, rad)
    x0, x1 = int(max(0, cx - rad)), int(min(W, cx + rad + 1))
    y0, y1 = int(max(0, cy - rad)), int(min(H, cy + rad + 1))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sig = rad / 3.0
    r2 = (xx - cx) ** 2 + (yy - cy) ** 2
    g = np.exp(-r2 / (2 * sig * sig)) * (r2 <= rad * rad) * a
    if mode == 'add':
        img[y0:y1, x0:x1] += g[..., None] * np.array(rgb)
    else:
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - g[..., None]) + g[..., None] * np.array(rgb)


def stroke(img, p0, p1, width, rgb, a):
    n = int(max(2, math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / max(0.7, width * 0.6)))
    for i in range(n + 1):
        k = i / n
        splat(img, p0[0] + (p1[0] - p0[0]) * k, p0[1] + (p1[1] - p0[1]) * k, max(0.8, width), rgb, a / max(1.0, n / 6.0))


def light_at(parts, q):
    tot = np.zeros(3)
    for kind, name, pos, v, size, s1, col, alpha, frac, extra, fade in parts:
        if kind != 'light':
            continue
        inten, rad = extra
        d = np.linalg.norm(np.asarray(q) - pos)
        if d < rad:
            tot += np.array(col[:3]) * (inten / 600.0) * (1 - d / rad) ** 2
    return tot


def render(cam, parts, scene):
    img = np.zeros((H, W, 3))
    # the floor (a dark plane with a faint grid), lit by the effect's lights
    floor_z = scene.get('floor_z', 0.0)
    ys, xs = np.mgrid[0:H:4, 0:W:4]
    dirs = (cam.f[None, None, :] + ((xs - W / 2) / cam.fpx)[..., None] * cam.r[None, None, :] - ((ys - H / 2) / cam.fpx)[..., None] * cam.u[None, None, :])
    t = (floor_z - cam.p[2]) / np.where(np.abs(dirs[..., 2]) < 1e-6, -1e-6, dirs[..., 2])
    hit = cam.p[None, None, :] + dirs * t[..., None]
    valid = t > 0
    base = np.full(hit.shape[:2] + (3,), 0.035)
    grid = ((np.abs((hit[..., 0] % 64) - 32) > 30.5) | (np.abs((hit[..., 1] % 64) - 32) > 30.5))
    base[grid] = 0.06
    lights = [p for p in parts if p[0] == 'light']
    for kind, name, pos, v, size, s1, col, alpha, frac, extra, fade in lights:
        inten, rad = extra
        d = np.linalg.norm(hit - pos[None, None, :], axis=2)
        k = np.clip(1 - d / rad, 0, 1) ** 2 * (inten / 600.0)
        base += k[..., None] * np.array(col[:3]) * 0.8
    base[~valid] = 0.0
    img[:] = np.kron(base, np.ones((4, 4, 1)))[:H, :W]
    # the reference marks: the hurt radius, the body
    for mark in scene.get('marks', []):
        if mark[0] == 'circle':
            c, r, rgb = mark[1], mark[2], mark[3]
            pts = [cam.project((c[0] + r * math.cos(a), c[1] + r * math.sin(a), c[2])) for a in np.linspace(0, 2 * math.pi, 90)]
            for i, (pa, pb) in enumerate(zip(pts, pts[1:])):
                if pa and pb and i % 2 == 0:
                    stroke(img, pa, pb, 0.9, rgb, 0.9)
    for cap in scene.get('bodies', []):
        a, b, rad = np.array(cap[0], float), np.array(cap[1], float), cap[2]
        for k in np.linspace(0, 1, 24):
            q = cam.project(a + (b - a) * k)
            if q:
                splat(img, q[0], q[1], rad / q[2] * cam.fpx * 1.2, (-0.03, -0.03, -0.03), 1.0, mode='add')
                splat(img, q[0], q[1], rad / q[2] * cam.fpx, (0.012, 0.012, 0.014), 0.95, mode='blend')
    # far to near
    order = sorted(parts, key=lambda p: -np.linalg.norm(p[2] - cam.p))
    for kind, name, pos, v, size, s1, col, alpha, frac, extra, fade in order:
        if kind == 'light' or alpha <= 0.002:
            continue
        q = cam.project(pos)
        if not q:
            continue
        dist = q[2]
        if fade[1] > 0:
            alpha *= min(1.0, max(0.0, (dist - fade[0]) / fade[1]))
        rgb = np.array(col[:3])
        rpx = size / dist * cam.fpx
        if kind == 'glow':
            splat(img, q[0], q[1], rpx, rgb * 1.6, alpha)
        elif kind == 'lit':
            lit = AMBIENT + light_at(parts, pos)
            splat(img, q[0], q[1], rpx, np.clip(rgb * lit * 2.2, 0, 1), alpha * 0.85, mode='blend')
        elif kind == 'arc':
            rng = np.random.default_rng(int(abs(pos[0] * 13 + pos[1] * 7 + pos[2] * 3)) % 99991)
            pts = [q]
            for i in range(4):
                pts.append((pts[-1][0] + rng.normal() * rpx * 0.5, pts[-1][1] + rng.normal() * rpx * 0.5, dist))
            for pa, pb in zip(pts, pts[1:]):
                stroke(img, pa, pb, max(0.7, rpx * 0.08), rgb * 1.8, alpha)
        elif kind == 'line':
            vn = np.linalg.norm(v)
            length = s1 if s1 > size * 1.5 else max(4.0, vn * 0.03)
            tail = pos - (v / vn if vn > 1e-6 else np.array([0, 0, 1.0])) * length
            qt = cam.project(tail)
            if qt:
                stroke(img, qt, q, max(0.7, size / dist * cam.fpx), rgb * 1.8, alpha)
        elif kind in ('trail', 'trail_lit'):
            pts = [cam.project(p) for p in extra]
            pts = [p for p in pts if p]
            for i, (pa, pb) in enumerate(zip(pts, pts[1:])):
                k = 1 - i / max(1, len(pts) - 1)
                w = max(0.7, size * (0.3 + 0.7 * k) / dist * cam.fpx)
                if kind == 'trail':
                    stroke(img, pa, pb, w, rgb * 1.5, alpha * k)
                else:
                    lit = AMBIENT + light_at(parts, pos)
                    stroke(img, pa, pb, w, np.clip(rgb * lit * 2.2, 0, 1) - 0.02, alpha * k * 0.6)
        elif kind == 'floor_ring':
            pts = [cam.project((pos[0] + size * math.cos(a), pos[1] + size * math.sin(a), pos[2])) for a in np.linspace(0, 2 * math.pi, 72)]
            for pa, pb in zip(pts, pts[1:]):
                if pa and pb:
                    stroke(img, pa, pb, 1.4, rgb * 1.6, alpha * 0.8)
    return img


def tonemap(img):
    x = np.clip(img, 0, None)
    y = x / (1 + x * 0.6)
    return (np.clip(y ** (1 / 1.25), 0, 1) * 255).astype(np.uint8)


def crop(arr, center, size=None):
    cw, ch = size or CROP
    cx, cy = int(center[0]), int(center[1])
    x0 = int(min(max(0, cx - cw // 2), W - cw))
    y0 = int(min(max(0, cy - ch // 2), H - ch))
    return arr[y0:y0 + ch, x0:x0 + cw]


# ---- the motion of the carriers --------------------------------------------------------------------------------------------
def juke_path():
    txt = (ROOT / 'scripts/zm/zm_tod2_cybercity/_tod_doppelghast_motion.gsh').read_text()
    side0 = txt.split('if ( side == 0 )')[1].split('else')[0]
    pts = [tuple(float(v) for v in m.groups()) for m in re.finditer(r'path\[\d+\] = \((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\);', side0)]
    return pts


def claw_path():
    p = PRIVATE / 'xanim_export/hb/doppelghast/hb_doppelghast_stn_melee_01.XANIM_EXPORT'
    if not p.exists():
        return None
    frames, cur, part = {}, None, None
    want = None
    for line in open(p, encoding='latin-1'):
        line = line.strip()
        if line.startswith('NOTETRACKS'):
            break
        m = re.match(r'PART (\d+) "(.+)"', line)
        if m:
            if m.group(2) == 'bone_9f4f9c2253737e9b':
                want = int(m.group(1))
            continue
        m = re.match(r'FRAME (\d+)', line)
        if m:
            cur = int(m.group(1)); continue
        m = re.match(r'PART (\d+)$', line)
        if m:
            part = int(m.group(1)); continue
        m = re.match(r'OFFSET (\S+) (\S+) (\S+)', line)
        if m and part == want and cur is not None:
            frames[cur] = tuple(float(v) for v in m.groups())
    return [frames[k] for k in sorted(frames)]


def lerp_path(pts, ms, fps=30.0, origin=(0, 0, 0)):
    f = ms / 1000.0 * fps
    i = int(min(len(pts) - 2, max(0, math.floor(f))))
    k = min(1.0, max(0.0, f - i))
    a, b = np.array(pts[i]), np.array(pts[min(len(pts) - 1, i + 1)])
    return np.array(origin) + a + (b - a) * k


# ---- the sheet ----------------------------------------------------------------------------------------------------------------
def load_fx(path):
    return E.parse(pathlib.Path(path).read_text(encoding='latin-1'))


def strip(title, sub, frames, label_old, label_new):
    """frames = [(t label, old array or None, new array)] -> a PIL image"""
    pad, th = 8, 28
    n = len(frames)
    cw, ch = frames[0][2].shape[1], frames[0][2].shape[0]
    img = Image.new('RGB', (pad + n * (cw + pad), th * 2 + 2 * (ch + 22) + pad * 2), (14, 14, 18))
    d = ImageDraw.Draw(img)
    d.text((pad, 4), title, fill=(235, 235, 240), font=font(20))
    d.text((pad, 30), sub, fill=(160, 160, 170), font=font(14))
    for i, (tl, old, new) in enumerate(frames):
        x = pad + i * (cw + pad)
        for row, (arr, lab) in enumerate(((old, label_old), (new, label_new))):
            y = th * 2 + row * (ch + 22)
            d.text((x, y), '%s  %s' % (lab, tl), fill=(200, 120, 120) if row == 0 else (120, 220, 160), font=font(14))
            if arr is None:
                d.rectangle([x, y + 18, x + cw - 1, y + 18 + ch - 1], fill=(6, 6, 8))
                d.text((x + 12, y + 30), 'nothing plays', fill=(110, 110, 120), font=font(16))
            else:
                img.paste(Image.fromarray(arr), (x, y + 18))
    return img


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--efx-root', default=str(ROOT))
    ap.add_argument('--out', default=str(OUT_DEFAULT))
    a = ap.parse_args(argv)
    efx = pathlib.Path(a.efx_root) / 'share/raw/fx'
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stock = PRIVATE / 'share/raw/fx'
    strips = []

    # 1. THE DEATH CHARGE: the corpse falls (torso 48 -> 14 by frame 61), the carrier follows it; OLD = the neck spray only
    charge = load_fx(efx / 'tod/elites/fx_tod_doppel_death_charge.efx')
    spray = load_fx(stock / 'blood/fx_blood_neck_spray_zmb.efx')
    torso = lambda ms: np.array([0.0, 0.0, 48 - 34 * min(1.0, max(0.0, (ms + 100) / 2030.0))])
    cam = Cam((-210, -150, 60), (0, 0, 26))
    frames = []
    for t in (300, 1200, 2000, 2550, 2850):
        body_z = torso(t)[2]
        sc = dict(bodies=[((0, 0, 4), (0, 0, max(8, body_z + 6)), 12), ((0, 0, body_z), (-30, 10, 8), 9)])
        new = render(cam, simulate(charge, t, torso, UP_FRAME), sc)
        old_parts = simulate(spray, t, lambda ms: np.array([0, 0, 52.0]), ID_FRAME) if t < 1100 else []
        old = render(cam, old_parts, sc)
        c = cam.project((0, 0, 26))
        frames.append(('+%.2f s after the death' % ((t + 100) / 1000.0), crop(tonemap(old), c), crop(tonemap(new), c)))
    strips.append(('doppel_death_charge', strip('DOPPELGHAST DEATH CHARGE  (the 2.9 s before the blast that hurts)',
                                                 'OLD: a blood spray, then nothing until the blast.  NEW: a red core swelling to white, an accelerating heartbeat, sparks rushing in, arcs, soot, a throbbing red light (+ the rising whine).',
                                                 frames, 'OLD', 'NEW')))

    # 2. THE DEATH BLAST: on the floor, the 128 hurt radius marked (dashed); OLD = the stock gore burst
    blast = load_fx(efx / 'tod/elites/fx_tod_doppel_death_blast.efx')
    gore = load_fx(stock / 'blood/fx_blood_impact_exp_body_lg_zmb.efx')
    cam = Cam((-470, -360, 180), (0, 0, 0))
    sc = dict(bodies=[((0, 0, 8), (-30, 10, 8), 10)], marks=[('circle', (0, 0, 0.5), 128, (0.25, 0.25, 0.3))])
    frames = []
    for t in (60, 160, 300, 600, 1300):
        new = render(cam, simulate(blast, t, lambda ms: np.zeros(3), UP_FRAME) + simulate(gore, t, lambda ms: np.array([0, 0, 14.0]), ID_FRAME, 9), sc)
        old = render(cam, simulate(gore, t, lambda ms: np.array([0, 0, 14.0]), ID_FRAME, 9), sc)
        c = cam.project((0, 0, 10))
        frames.append(('+%.2f s' % (t / 1000.0), crop(tonemap(old), c, (960, 540)), crop(tonemap(new), c, (960, 540))))
    strips.append(('doppel_death_blast', strip('DOPPELGHAST DEATH BLAST  (dashed circle = the 128-unit damage radius)',
                                                'OLD: the stock gore burst alone.  NEW: + a flash, needles, embers, a red light, and the hurt zone drawn on the floor (a wave that stops on the radius, its edge glowing).',
                                                frames, 'OLD', 'NEW')))

    # 3. THE JUKE: the carrier rides j_spine4 (54 up) along the shipping juke path; a camera 300 u away
    juke = load_fx(efx / 'tod/elites/fx_tod_doppel_juke.efx')
    jp = juke_path()
    jpath = lambda ms: lerp_path(jp, ms + 50, origin=(0, 0, 54))
    cam = Cam((320, -90, 60), (40, 40, 40))
    frames = []
    for t in (400, 550, 700, 900, 1150):
        b = jpath(t)
        sc = dict(bodies=[((b[0], b[1], 4), (b[0], b[1], 70), 11)])
        new = render(cam, simulate(juke, t, jpath, ID_FRAME), sc)
        old = render(cam, [], sc)
        c = cam.project((40, 40, 40))
        frames.append(('+%.2f s into the juke' % (t / 1000.0), crop(tonemap(old), c, (800, 450)), crop(tonemap(new), c, (800, 450))))
    strips.append(('doppel_juke', strip('DOPPELGHAST JUKE  (from 300 units: the dodge is refused closer than 250)',
                                         'OLD: a plain sidestep.  NEW: a charcoal smear ribbon, soot afterimages, a faint red core and red sparks along the dodge.',
                                         frames, 'OLD', 'NEW')))

    # 4. THE CLAW: the carrier rides the measured claw bone through stn_melee_01; a camera where the target stands
    claw = load_fx(efx / 'tod/elites/fx_tod_doppel_claw.efx')
    cp_ = claw_path()
    if cp_:
        cpath = lambda ms: lerp_path(cp_, ms + 50)
        cam = Cam((150, -190, 70), (20, 0, 55))
        frames = []
        for t in (250, 400, 470, 560, 700):
            sc = dict(bodies=[((0, 0, 4), (0, 0, 74), 13)])
            new = render(cam, simulate(claw, t, cpath, ID_FRAME), sc)
            old = render(cam, [], sc)
            c = cam.project((20, 0, 55))
            frames.append(('+%.2f s into the swipe' % (t / 1000.0), crop(tonemap(old), c, (800, 450)), crop(tonemap(new), c, (800, 450))))
        strips.append(('doppel_claw', strip('DOPPELGHAST CLAW  (a 3/4 view from ~240 units; the hit lands at +0.60 s)',
                                             'OLD: no visual windup.  NEW: a red-hot claw with a ribbon tracing the swipe and a few sparks, for the clip\'s own effect window (0.75 s).',
                                             frames, 'OLD', 'NEW')))

    # 5. THE MANGLER: at the end of its death clip, at the torso lying on the floor
    mang = load_fx(efx / 'tod/elites/fx_tod_mangler_death.efx')
    cam = Cam((-360, -260, 110), (0, 0, 20))
    frames = []
    for t in (60, 200, 500, 1100, 2000):
        sc_old = dict(bodies=[((0, 0, 8), (-40, 15, 8), 13), ((10, 0, 8), (40, -10, 8), 9)])
        sc_new = dict(bodies=[] if t > 100 else sc_old['bodies'])
        new = render(cam, simulate(mang, t, lambda ms: np.array([0, 0, 8.0]), UP_FRAME), sc_new)
        old = render(cam, [], sc_old if t < 800 else dict())
        c = cam.project((0, 0, 20))
        frames.append(('+%.2f s after the clip' % (t / 1000.0), crop(tonemap(old), c, (800, 450)), crop(tonemap(new), c, (800, 450))))
    strips.append(('mangler_death', strip('MANGLER DEATH  (the 2.2 s clip ends; the body used to vanish at 3.0 s)',
                                           'OLD: the body lies still, then pops out of existence.  NEW: it breaks up - a flash, fire, scrap, spark tails, venting steam, arcs, sputter, smoke, a smouldering light - and hides under the flash.',
                                           frames, 'OLD', 'NEW')))

    # 6. THE HAVEN MOTES (steady state), lit by a district light 200 u away; OLD = the stub
    motes_path = efx / 'tod/haven/fx_tod_haven_motes.efx'
    if motes_path.exists():
        motes = load_fx(motes_path)
        stub = load_fx(stock / 'env/light/fx_light_god_rays_dust_motes.efx')
        cam = Cam((-420, 0, 64), (0, 0, 200))
        district = ('light', 'district', np.array([0, -120, 300.0]), np.zeros(3), 0, 0, [0.35, 0.65, 1.0], 1.0, 0.0, (900.0, 420.0), (0, 0))
        frames = []
        for t, lab in ((20000, 'steady state'), (26000, '+6 s')):
            parts = simulate(motes, t, lambda ms: np.array([0, 0, 260.0]), ID_FRAME) + [district]
            new = render(cam, parts, dict())
            stub_parts = [p[:6] + ((1.0, 0.0, 1.0),) + p[7:] for p in simulate(stub, t, lambda ms: np.array([0, 0, 260.0]), ID_FRAME)] + [district]
            old = render(cam, stub_parts, dict())
            c = cam.project((0, 0, 200))
            frames.append((lab, crop(tonemap(old), c, (720, 900)), crop(tonemap(new), c, (720, 900))))
        strips.append(('haven_motes', strip('HAVEN / DEPARTURE HALL MOTES  (anchor 260 over the floor, lit blue by a district light)',
                                             'OLD: the zoned env/light/fx_light_god_rays_dust_motes is the Treyarch stub - one gfx_debug_missing_fx placeholder sprite (magenta here): at best a debug sprite, never motes.  NEW: a soft column of lit dust motes drifting down.',
                                             frames, 'OLD', 'NEW')))

    for name, im in strips:
        im.save(out / ('strip_%s.png' % name))
    wmax = max(im.size[0] for _, im in strips)
    sheet = Image.new('RGB', (wmax, sum(im.size[1] for _, im in strips) + 8 * len(strips)), (8, 8, 10))
    y = 0
    for _, im in strips:
        sheet.paste(im, (0, y))
        y += im.size[1] + 8
    sheet.save(out / '_review.png')
    print('review sheet:', out / '_review.png', sheet.size)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
