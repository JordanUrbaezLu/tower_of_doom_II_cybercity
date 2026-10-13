"""A DESIGN PREVIEW of the Dealer's effects (W2B): every generated .efx particle-simulated from its own numbers (spawn timing,
lifetimes, spawn box, local + world velocity graphs, gravity, size / colour / alpha graphs) and drawn as a side view at the
beats that matter, with a 1:1 silhouette of the Dealer for scale, into art/generated/W2B-dealer-av/_review_fx.png.

  python tools/dealer_fx/preview.py [--root DIR]

WHAT IT PROVES AND WHAT IT DOES NOT: it is the AUTHORED motion and timing (does the shadow rise off the coat or fall off it,
does the column hide the moment he appears, do the shards leave the FACE, does the trail stay behind him, does the last
billow cover the delete) checked on the exact numbers the game reads. It is NOT the in-game look: no flipbook, no lighting,
no engine blending - the user's playtest is that.
"""
import argparse
import math
import pathlib
import random
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools/sky_ships'))
import efx_lib as E  # noqa: E402

PX = 1.25                                   # world units per pixel
W, H = 300, 250                             # one frame (375 x 312 units: x -187..187, z -20..292)
OX, OZ = W // 2, H - 16                     # where world (0, 0) lands
BG = (58, 58, 64)                           # a lit grey wall (black smoke must read against it)


def interp(rows, t):
    if not rows:
        return [0.0]
    if t <= rows[0][0]:
        return rows[0][1:]
    for a, b in zip(rows, rows[1:]):
        if t <= b[0]:
            k = (t - a[0]) / max(1e-9, b[0] - a[0])
            return [a[i] + (b[i] - a[i]) * k for i in range(1, len(a))]
    return rows[-1][1:]


def gval(e, key, t, r):
    if not e.has(key):
        return None
    g = e.graph(key)
    a, b = interp(g.curves[0], t), interp(g.curves[-1], t)
    return [g.scale * (x + (y - x) * r) for x, y in zip(a, b)]


class Frame:
    """carrier frame: local axes (X, Y, Z) in world, origin, host velocity (u/s along world x)"""
    def __init__(self, ax, ay, az, origin, speed=0.0):
        self.ax, self.ay, self.az, self.o, self.speed = ax, ay, az, origin, speed

    def pos(self, local, t):
        o = (self.o[0] + self.speed * t, self.o[1], self.o[2])
        return tuple(o[i] + local[0] * self.ax[i] + local[1] * self.ay[i] + local[2] * self.az[i] for i in range(3))

    def vec(self, v):
        return tuple(v[0] * self.ax[i] + v[1] * self.ay[i] + v[2] * self.az[i] for i in range(3))


UPRIGHT = lambda o, s=0.0: Frame((1, 0, 0), (0, 1, 0), (0, 0, 1), o, s)
SPINE = lambda o, s=0.0: Frame((0, 0, 1), (1, 0, 0), (0, 1, 0), o, s)     # j_spine4: +X up the spine, +Y forward, +Z left
FACE = lambda o: Frame((1, 0, 0), (0, 1, 0), (0, 0, 1), o)                # tag_eye: +X out of the face (forward = world +x)


def particles(e, frame, t_end, rng):
    """every particle alive at t_end: (world pos, size, rgb, alpha, emissive)"""
    looping = 'looping' in e.flags('editorFlags')
    life0, liferand = e.nums('lifeSpanMsec')
    d0, drand = e.nums('spawnDelayMsec')
    spawns = []
    if looping:
        iv = max(1.0, e.nums('spawnLooping')[0])
        per = int(e.nums('spawnLoopingSpawnCount')[0]) or 1
        t = d0
        while t <= t_end * 1000:
            spawns += [t] * per
            t += iv
    else:
        n0, nr = e.nums('spawnOneShot')
        n = int(n0 + rng.random() * nr)
        spawns = [d0 + rng.random() * drand for _ in range(n)]
    vis, mats = e.visual
    emissive = bool(mats) and ('_em' in mats[0] or 'light' in mats[0] or 'spark' in mats[0] or 'ember' in mats[0])
    out = []
    org = [e.nums('spawnOrg' + a) for a in 'XYZ']
    grav = e.nums('gravity')
    for ts in spawns:
        life = life0 + rng.random() * liferand
        age = t_end * 1000 - ts
        if age < 0 or age > life:
            continue
        local = [o[0] + rng.random() * o[1] for o in org]
        rv = [rng.random() for _ in range(6)]
        g = (grav[0] + rng.random() * grav[1]) / 100.0 * 800.0
        steps = 12
        p = list(frame.pos(local, ts / 1000.0))
        dt = age / 1000.0 / steps
        for k in range(steps):
            tn = (k + 0.5) / steps * (age / life)
            v0 = [(gval(e, 'velGraph0' + a, tn, rv[i]) or [0])[0] for i, a in enumerate('XYZ')]
            v1 = [(gval(e, 'velGraph1' + a, tn, rv[3 + i]) or [0])[0] for i, a in enumerate('XYZ')]
            vw = frame.vec(v0)
            tt = (k + 0.5) * dt
            for i in range(3):
                p[i] += (vw[i] + v1[i]) * dt
            p[2] -= g * tt * dt
        tn = age / life
        size = (gval(e, 'sizeGraph0', tn, rng.random()) or [8])[0]
        col = gval(e, 'colorGraph', tn, rng.random()) or [1, 1, 1]
        a = (gval(e, 'alphaGraph', tn, rng.random()) or [1])[0]
        out.append((p, size, col, a, emissive))
    return out


def draw(img, parts):
    import numpy as np
    arr = np.asarray(img, dtype=np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W]
    for p, size, col, a, emissive in sorted(parts, key=lambda q: q[4]):    # smoke first, glows over it
        cx, cy = OX + p[0] / PX, OZ - p[2] / PX
        r = max(1.2, size / 2 / PX)
        if cx < -r or cx > W + r or cy < -r or cy > H + r:
            continue
        d2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)
        m = np.clip(1 - d2, 0, 1) ** 1.5 * max(0.0, min(1.0, a))
        c = np.array([max(0.0, min(1.0, v)) for v in col[:3]], dtype=np.float32)
        if emissive:
            arr += m[..., None] * c * 1.4
        else:
            arr = arr * (1 - m[..., None]) + m[..., None] * c
    from PIL import Image
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype('uint8'))


def silhouette(draw_, x0, levitate):
    """the Dealer at 1:1: an 80-unit figure, hood, coat to the floor (state one floats 14 u)"""
    z0 = 14 if levitate else 0
    pts = lambda u: [(OX + x0 + u[i][0] / PX, OZ - (u[i][1] + z0) / PX) for i in range(len(u))]
    coat = [(-14, 4), (14, 4), (10, 56), (8, 64), (-8, 64), (-10, 56)]
    draw_.polygon(pts(coat), outline=(140, 140, 150))
    draw_.ellipse([OX + x0 - 6 / PX * 1.0 - 4, OZ - (78 + z0) / PX, OX + x0 + 4 + 6 / PX, OZ - (64 + z0) / PX], outline=(140, 140, 150))


def scene(path, frame_fn, times, carrier_x=0.0, levitate=False, label=''):
    from PIL import Image, ImageDraw
    fx = E.load(path)
    frames = []
    for t in times:
        rng = random.Random(7)
        img = Image.new('RGB', (W, H), BG)
        d = ImageDraw.Draw(img)
        d.line([(0, OZ), (W, OZ)], fill=(90, 90, 96))
        fr = frame_fn(t)
        silhouette(d, (fr.o[0] + fr.speed * t) / PX, levitate)
        parts = []
        for e in fx.elements:
            if e.visual[0] == 'dynamicLight2':
                continue
            parts += particles(e, fr, t, rng)
        img = draw(img, parts)
        d = ImageDraw.Draw(img)
        lights = [e for e in fx.elements if e.visual[0] == 'dynamicLight2']
        d.text((4, 3), label if t == times[0] else '', fill=(235, 235, 235))
        d.text((4, 15), 't=%.2fs  %d particles%s' % (t, len(parts), '  +light' if lights else ''), fill=(200, 200, 200))
        frames.append(img)
    return frames


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=str(REPO))
    a = ap.parse_args(argv)
    fxdir = pathlib.Path(a.root) / 'share/raw/fx/tod/dealer'
    rows = [
        ('aura (state one, on j_spine4, gliding 85 u/s)', 'fx_tod_dealer_aura', lambda t: SPINE((-60, 0, 70), 85), [0.6, 1.4, 2.2], True),
        ('aura cracked (state two, running 118 u/s)', 'fx_tod_dealer_aura_cracked', lambda t: SPINE((-80, 0, 56), 118), [0.6, 1.4, 2.2], False),
        ('trail (at his feet, gliding 85 u/s)', 'fx_tod_dealer_aura_trail', lambda t: UPRIGHT((-60, 0, 0), 85), [0.6, 1.4, 2.2], True),
        ('arrive (the gate; he appears at t=0)', 'fx_tod_dealer_arrive', lambda t: UPRIGHT((0, 0, 0)), [0.1, 0.35, 0.8, 1.3], True),
        ('mask shatter (tag_eye, +X out of the face)', 'fx_tod_dealer_mask_shatter', lambda t: FACE((4.4, 0, 70)), [0.05, 0.2, 0.5, 0.9], False),
        ('eye dies (the right socket)', 'fx_tod_dealer_eye_die', lambda t: FACE((5, -2.3, 70.4)), [0.05, 0.6, 1.0, 1.6], False),
        ('death (the floor under him)', 'fx_tod_dealer_death', lambda t: UPRIGHT((0, 0, 0)), [0.1, 0.5, 1.0, 1.8], False),
        ('dissolve (the corpse; deleted at 2.0 s)', 'fx_tod_dealer_dissolve', lambda t: UPRIGHT((0, 0, 8)), [0.6, 1.5, 2.1, 3.0], False),
    ]
    from PIL import Image, ImageDraw
    sheet = Image.new('RGB', (4 * W + 10, len(rows) * (H + 6) + 26), (10, 10, 12))
    ImageDraw.Draw(sheet).text((6, 6), 'W2B: the Dealer effects, simulated from the generated .efx numbers (design preview, NOT the in-game look)', fill=(240, 240, 240))
    for r, (label, name, frame_fn, times, lev) in enumerate(rows):
        for c, img in enumerate(scene(fxdir / (name + '.efx'), frame_fn, times, levitate=lev, label=label)):
            sheet.paste(img, (4 + c * (W + 1), 22 + r * (H + 6)))
    out = REPO / 'art/generated/W2B-dealer-av/_review_fx.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print('wrote', out, sheet.size)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
