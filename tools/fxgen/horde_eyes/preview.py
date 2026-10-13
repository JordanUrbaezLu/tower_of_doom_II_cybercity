"""THE HORDE'S EYES (PK04) - the review sheet. NOT a gate and NOT the engine's renderer: a schematic.

  python tools/fxgen/horde_eyes/preview.py [--efx-root DIR] [--out DIR]

Draws the four eye effects that matter side by side on the REAL charred-head mesh the horde wears
(model_export/tod_cyber_elites/tod_charcoal_c_zom_dlc4_zombie_charred_head.XMODEL_BIN, read with PyCoD from the
BetterBetterBlenderCOD add-on) so a reviewer can compare their footprint and colour, not judge the final look:

  STOCK ORANGE   zombie/fx_glow_eye_orange  - what every zombie wears today (the gap)
  STOCK RED      zombie/fx_glow_eye_red     - the brief's wiring-only option
  PK04 RED       tod/cyber/fx_tod_charcoal_eye_glow_red  - the horde (this pack)
  PK04 GOLD      tod/cyber/fx_tod_golden_eye_glow        - the golden zombie (this pack), on a gold-tinted head

Every number comes from each .efx itself (offsets, sizes, colours, alphas, zFeather, the near / far fades at the
stated camera distance); each element is placed on j_eyeball_le with the head's own bone frame (local X = the zombie's
left, local -Y = out of the face, Z = up; measured). Sprites are additive glows (the stock texture is not on disk: a
Gaussian with sigma = size / 3, cut at the size, SIZE READ AS A RADIUS), depth-tested against the mesh with their
zFeather; the cones (the
orange's "line" elements) are drawn as tapered wedges along their velocity, length = size0, end width = size1 - an
approximation. The eye material is drawn flat in its tint (the HDR-16 bloom is not simulated). Rows: front close-up,
a three-quarter view, and the front view at ~10 m (downsampled to the pixels it really covers at 1080p / 65 deg).

Writes art/generated/PK04-horde-red-eye-glow/_review.png (+ the four columns as preview_<name>.png).
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
HERE = pathlib.Path(__file__).resolve().parent
PYCOD = pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'
HEAD = ROOT / 'model_export/tod_cyber_elites/tod_charcoal_c_zom_dlc4_zombie_charred_head.XMODEL_BIN'
PACK = 'PK04-horde-red-eye-glow'

EYE_L = np.array([4.024, 1.092, 66.332])          # j_eyeball_le bind position (PyCoD, the charred head)
# the bone frame, rows = local axes in world (PyCoD): X = world +Y (the zombie's left), Y = world -X (into the head)
AX = np.array([[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])


def load_head():
    sys.path.insert(0, str(PYCOD))
    try:
        from PyCoD import xmodel
    except ImportError:
        raise SystemExit('preview: PyCoD not found under %s (the BetterBetterBlenderCOD add-on)' % PYCOD)
    m = xmodel.Model()
    m.LoadFile_Bin(str(HEAD))
    tris = []
    for me in m.meshes:
        v = np.array([x.offset for x in me.verts])
        for f in me.faces:
            tris.append((v[[i.vertex for i in f.indices]], f.material_id))
    return tris


# ---- .efx elements (only what the preview needs) -------------------------------------------------------------------
def blocks(text):
    out, depth, start = [], 0, None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                out.append(text[start:i + 1])
    return out


def vals(b, key):
    m = re.search(r'\n\t' + key + r' ([^\n;]*);', b)
    return [float(x) for x in m.group(1).split()] if m else None


def graph_first(b, key):
    m = re.search(r'\n\t' + key + r' ([^\n]*)\n\t\{\n(.*?)\n\t\};', b, re.S)
    rows = [[float(x) for x in ln.split()] for ln in m.group(2).split('\n') if ln.strip() and re.fullmatch(r'-?[0-9.]+', ln.split()[0])]
    return float(m.group(1)), rows[0][1:]


def elements(path):
    text = pathlib.Path(path).read_bytes().decode('latin-1').replace('\r\n', '\n')
    out = []
    for b in blocks(text):
        kind = 'line' if re.search(r'\n\tline\n\t\{', b) else 'sprite'
        s0, _ = graph_first(b, 'sizeGraph0')
        s1, _ = graph_first(b, 'sizeGraph1')
        _, col = graph_first(b, 'colorGraph')
        _, al = graph_first(b, 'alphaGraph')
        vy, vyc = graph_first(b, 'velGraph0Y')
        vz, vzc = graph_first(b, 'velGraph0Z')
        out.append(dict(kind=kind, org=np.array([vals(b, 'spawnOrgX')[0], vals(b, 'spawnOrgY')[0], vals(b, 'spawnOrgZ')[0]]),
                        s0=s0, s1=s1, col=np.array(col[:3]), alpha=al[0], zf=vals(b, 'zFeather')[0],
                        spawn=vals(b, 'spawnRange'), fin=vals(b, 'fadeInRange'), fout=vals(b, 'fadeOutRange'),
                        vel=np.array([0.0, vy * vyc[0], vz * vzc[0]])))
    return out


def dist_fade(e, d):
    s0, sw = e['spawn']
    if d < s0 or d > s0 + sw:
        return 0.0
    f = 1.0
    fi0, fiw = e['fin']
    if fiw > 0 and d > fi0:
        f *= max(0.0, 1 - (d - fi0) / fiw)
    fo0, fow = e['fout']
    if fow > 0 and d < fo0 + fow:
        f *= max(0.0, (d - fo0) / fow)
    return f


# ---- the renderer ----------------------------------------------------------------------------------------------------
def camera(az_deg, el_deg=4.0):
    a, e = math.radians(az_deg), math.radians(el_deg)
    back = np.array([math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)])   # from target toward camera
    up0 = np.array([0.0, 0.0, 1.0])
    right = np.cross(-back, up0)
    right /= np.linalg.norm(right)
    up = np.cross(right, -back)
    return right, up, back


def render(tris, effect, az, eye_rgb, body_rgb, px=480, half=6.4, cam_dist=150.0):
    right, up, back = camera(az)
    centre = np.array([3.0, 0.0, 65.6])
    lin = np.zeros((px, px, 3))
    depth = np.full((px, px), -1e9)
    scale = px / (2 * half)

    def to_px(p):
        q = p - centre
        return (q @ right) * scale + px / 2, px / 2 - (q @ up) * scale, q @ back

    light = np.array([0.55, 0.35, 0.75])
    light /= np.linalg.norm(light)
    for tri, mat in tris:
        p = np.array([to_px(v) for v in tri])
        n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        if np.linalg.norm(n) == 0:
            continue
        n /= np.linalg.norm(n)
        if n @ back < 0:
            n = -n
        x0, x1 = int(max(0, math.floor(p[:, 0].min()))), int(min(px - 1, math.ceil(p[:, 0].max())))
        y0, y1 = int(max(0, math.floor(p[:, 1].min()))), int(min(px - 1, math.ceil(p[:, 1].max())))
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax, ay, az_), (bx, by, bz), (cx, cy, cz) = p
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        z = w0 * az_ + w1 * bz + w2 * cz
        sub = depth[y0:y1 + 1, x0:x1 + 1]
        win = inside & (z > sub)
        if not win.any():
            continue
        sub[win] = z[win]
        if mat == 1:
            c = np.array(eye_rgb)
        else:
            c = np.array(body_rgb) * (0.25 + 0.75 * max(0.0, float(n @ light)))
        lin[y0:y1 + 1, x0:x1 + 1][win] = c

    base = lin.copy()
    glow = np.zeros_like(lin)
    yy, xx = np.mgrid[0:px, 0:px] + 0.5
    for e in effect or []:
        f = dist_fade(e, cam_dist)
        if f <= 0:
            continue
        world = EYE_L + e['org'] @ AX
        sx, sy, sz = to_px(world)
        col = e['col'] * e['alpha'] * f
        zf = max(e['zf'], 0.05)
        vis = np.clip((sz - depth) / zf, 0, 1)
        vis[depth < -1e8] = 1.0
        if e['kind'] == 'sprite':
            r = np.hypot(xx - sx, yy - sy)
            t = np.exp(-4.5 * (r / (e['s0'] * scale)) ** 2) * (r < e['s0'] * scale)   # a glow sprite: Gaussian, sigma = size / 3
            glow += t[..., None] * col * vis[..., None]
        else:
            d = e['vel'] @ AX
            if np.linalg.norm(d) == 0:
                continue
            d = d / np.linalg.norm(d)
            tip = world + d * e['s0']
            tx, ty, tz = to_px(tip)
            vx, vy = tx - sx, ty - sy
            L2 = vx * vx + vy * vy
            if L2 < 1e-6:            # pointing straight at the camera: a small disc
                r = np.hypot(xx - sx, yy - sy)
                t = np.clip(1 - (r / (0.35 * e['s1'] * scale)) ** 2, 0, 1) ** 2
            else:
                u = np.clip(((xx - sx) * vx + (yy - sy) * vy) / L2, 0, 1)
                proj_x, proj_y = sx + u * vx, sy + u * vy
                perp = np.hypot(xx - proj_x, yy - proj_y)
                width = (0.08 + 0.5 * u) * e['s1'] * scale
                t = np.clip(1 - perp / np.maximum(width, 1e-3), 0, 1) * (1 - u) * (((xx - sx) * vx + (yy - sy) * vy) >= 0)
            glow += t[..., None] * col * vis[..., None]
    out = base + glow
    out = 1 - np.exp(-1.6 * out)                    # soft HDR shoulder
    out = np.clip(out ** (1 / 2.2), 0, 1)
    return Image.fromarray((out * 255).astype(np.uint8), 'RGB')


def label(im, text, sub=None):
    W = im.width
    canvas = Image.new('RGB', (W, im.height + 44), (18, 19, 24))
    canvas.paste(im, (0, 44))
    d = ImageDraw.Draw(canvas)
    try:
        f = ImageFont.truetype(str(ROOT / 'fonts/tod_tower1.ttf'), 20)
        fs = ImageFont.truetype('arial.ttf', 12)
    except Exception:
        f = fs = ImageFont.load_default()
    d.text((8, 4), text, fill=(225, 228, 236), font=f)
    if sub:
        d.text((8, 27), sub, fill=(150, 156, 170), font=fs)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--efx-root', default=str(ROOT), help='where share/raw/fx/tod/cyber lives (a stage before landing)')
    ap.add_argument('--out', default=str(ROOT / 'art/generated' / PACK))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cyber = pathlib.Path(a.efx_root) / 'share/raw/fx/tod/cyber'
    cols = [
        ('STOCK ORANGE', 'ships today: zombie/fx_glow_eye_orange', HERE / 'donor/fx_glow_eye_orange.efx', (1.0, 0.0, 0.0), (0.11, 0.11, 0.12)),
        ('STOCK RED', 'wiring-only option: zombie/fx_glow_eye_red', HERE / 'donor/fx_glow_eye_red.efx', (1.0, 0.0, 0.0), (0.11, 0.11, 0.12)),
        ('PK04 RED', 'horde: fx_tod_charcoal_eye_glow_red', cyber / 'fx_tod_charcoal_eye_glow_red.efx', (1.0, 0.0, 0.0), (0.11, 0.11, 0.12)),
        ('PK04 GOLD', 'golden zombie: fx_tod_golden_eye_glow', cyber / 'fx_tod_golden_eye_glow.efx', (1.0, 0.76, 0.18), (0.32, 0.25, 0.10)),
        ('NO PARTICLES', 'the eye material alone (reference)', None, (1.0, 0.0, 0.0), (0.11, 0.11, 0.12)),
    ]
    tris = load_head()
    tiles = []
    for name, sub, path, eye, body in cols:
        eff = elements(path) if path else None
        front = render(tris, eff, 0.0, eye, body)
        three = render(tris, eff, 38.0, eye, body)
        # ~10 m: a 13-unit-tall window at 400 u covers 2*400*tan(32.5 deg) = 510 u over 1080 px -> 27 px
        far = render(tris, eff, 0.0, eye, body, cam_dist=400.0).resize((28, 28), Image.LANCZOS).resize((480, 480), Image.NEAREST)
        col = Image.new('RGB', (480, 3 * 480 + 3 * 44 + 16), (18, 19, 24))
        y = 0
        for im, t in ((front, 'front, 150 u'), (three, 'three-quarter, 150 u'), (far, 'front at ~10 m (28 px, enlarged)')):
            col.paste(label(im, name if y == 0 else '', t), (0, y))
            y += im.height + 44 + 8
        col.save(out / ('preview_' + name.lower().replace(' ', '_') + '.png'))
        tiles.append(col)
    W = sum(t.width for t in tiles) + 12 * (len(tiles) + 1)
    H = tiles[0].height + 12 * 2 + 64
    sheet = Image.new('RGB', (W - W % 4 + (4 if W % 4 else 0), H - H % 4 + (4 if H % 4 else 0)), (12, 13, 17))
    d = ImageDraw.Draw(sheet)
    try:
        fs = ImageFont.truetype('arial.ttf', 15)
    except Exception:
        fs = ImageFont.load_default()
    d.text((12, 10), 'PK04 THE HORDE\'S EYES - SCHEMATIC review (not the engine renderer): each .efx\'s own numbers on the real '
           'charred-head mesh; additive Gaussian sprites, size read as a radius, cones approximated, no HDR bloom.', fill=(205, 210, 220), font=fs)
    d.text((12, 32), 'Judge the FOOTPRINT and HUE against the stock orange (today) and the stock red (the wiring-only option); '
           'the in-game look is the user\'s playtest.', fill=(150, 156, 170), font=fs)
    x = 12
    for t in tiles:
        sheet.paste(t, (x, 64))
        x += t.width + 12
    sheet.save(out / '_review.png')
    print('wrote %s (%dx%d) + %d previews' % (out / '_review.png', sheet.width, sheet.height, len(tiles)))


if __name__ == '__main__':
    main()
