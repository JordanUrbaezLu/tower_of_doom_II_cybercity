"""THE FIRST JUMP'S CRASH - a storyboard of the scene without the game (docs/196 §4).

  python tools/jump_title/render_storyboard.py [--out DIR]     (default docs/196_ref/)

A PREVIEW, not the engine. The sky is the finished panorama (docs/sky_preview/sky3d_sky_equirect.png) sampled
through the engine's MEASURED sky mapping (docs/196 §3: the centre column faces yaw -(the SSI's sun azimuth + the
material's skyRotation), both read from the GDT); the camera and the ships come
from the LIVE scene (storyboard_data.js: _tod_jumppad.gsc + _tod_jump_title.csc); the gunship is session 9c's
side render (art/sky_ships/review/v2_gunship_side.png) laid along each ship's projected axis; the blaze is
painted from gen_fx.py's own table (the same features, sizes, colours and alpha curves the effect is built
from); the warp, the burn, the white-out, the fireball and the wreckage are painted stand-ins. It shows WHERE
everything is and WHEN; how the effects really look is the playtest's.
Writes crash_storyboard.png (the contact sheet) and crash_frame_<n>.png (1280 x 720, letterboxed, cg_fov 65).
"""
import json, math, os, pathlib, re, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import gen_fx  # noqa: E402  (the blaze table, the sign's features, SIGN_DIST)

SKY = REPO / 'docs/sky_preview/sky3d_sky_equirect.png'
SKY_GDT = REPO / 'source_data/tod_skybox.gdt'
SHIP_SPRITE = REPO / 'art/sky_ships/review/v2_gunship_side.png'
W, H, BAR = 1280, 720, 86
CG_FOV = 65.0
TX = math.tan(math.radians(CG_FOV / 2)) * (16 / 9) / (4 / 3)   # hor+ (scene_geometry.frustum)
TY = math.tan(math.radians(CG_FOV / 2)) * 0.75


def basis(pitch, yaw):
    p, y = math.radians(pitch), math.radians(yaw)
    F = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), -math.sin(p)])
    R = np.array([math.sin(y), -math.cos(y), 0.0])
    U = np.cross(R, F)
    return F, R, U


def project(q, eye, cam):
    F, R, U = cam
    d = np.asarray(q, float) - np.asarray(eye, float)
    z = d @ F
    if z <= 1:
        return None
    return (W / 2 + (d @ R) / z / TX * W / 2, H / 2 - (d @ U) / z / TY * H / 2, z)


def sky_rotation():
    """-> the sky's total turn: the live SSI's sun azimuth + the material's skyRotation (docs/196 §3, measured in
    game 2026-09-29; the shader below then puts the image's centre column at yaw -turn)."""
    t = SKY_GDT.read_text(encoding='utf-8')
    part = t.split('"mtl_skybox_tod_cybercity" ( "material.gdf" )')[1]
    rot = float(re.search(r'"skyRotation" "(-?[\d.]+)"', part).group(1))
    ssi = t.split('"tod_ssi_cybercity" ( "ssi.gdf" )')[1]
    ssi = ssi[:ssi.index('\n\t}')]
    yaw = float(re.search(r'"yaw" "(-?[\d.]+)"', ssi).group(1))
    pitch = float(re.search(r'"pitch" "(-?[\d.]+)"', ssi).group(1))
    sun = yaw if math.cos(math.radians(pitch)) < 0 else yaw + 180
    return (sun + rot) % 360


def render_sky(sky, cam, rot):
    F, R, U = cam
    sx = (np.arange(W) + 0.5) / W * 2 - 1
    sy = 1 - (np.arange(H) + 0.5) / H * 2
    gx, gy = np.meshgrid(sx * TX, sy * TY)
    d = F[None, None, :] + gx[..., None] * R[None, None, :] + gy[..., None] * U[None, None, :]
    d /= np.linalg.norm(d, axis=2, keepdims=True)
    s, c = math.sin(math.radians(rot)), math.cos(math.radians(rot))   # the shader: x' = x*s.y - y*s.x, y' = x*s.x + y*s.y
    xp = d[..., 0] * c - d[..., 1] * s
    yp = d[..., 0] * s + d[..., 1] * c
    u = (0.5 - np.arctan2(yp, xp) / (2 * math.pi)) % 1.0
    v = np.arccos(np.clip(d[..., 2], -1, 1)) / math.pi
    sh, sw = sky.shape[:2]
    px = np.clip((u * sw).astype(int), 0, sw - 1)
    py = np.clip((v * sh).astype(int), 0, sh - 1)
    return sky[py, px].copy(), d


def add_glow(img, x, y, r, rgb, a):
    """additive soft glow (the glow billboard's falloff), radius r px."""
    if a <= 0 or r < 1:
        return
    x0, x1 = max(0, int(x - r)), min(W, int(x + r) + 1)
    y0, y1 = max(0, int(y - r)), min(H, int(y + r) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    q = np.clip(1 - np.hypot(xx - x, yy - y) / r, 0, 1) ** 2
    img[y0:y1, x0:x1] += q[..., None] * np.asarray(rgb) * a


def curve(pts, x):
    x = min(max(x, 0.0), 1.0)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (0 if x1 == x0 else (x - x0) / (x1 - x0))
    return pts[-1][1]


def ship_sprite():
    im = np.asarray(Image.open(SHIP_SPRITE).convert('RGB'), float) / 255
    lum = im.max(axis=2)
    alpha = np.clip((lum - 0.02) / 0.06, 0, 1)
    ys, xs = np.nonzero(alpha > 0.05)
    im, alpha = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1], alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    rgba = np.dstack([im, alpha])
    a = Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA')
    g = rgba.copy()                                    # variant B: the magenta neon turned green
    mag = (im[..., 0] > im[..., 1] + 0.1) & (im[..., 2] > im[..., 1] + 0.1)
    g[mag, 0], g[mag, 1], g[mag, 2] = im[mag, 1], np.maximum(im[mag, 0], im[mag, 2]), im[mag, 1]
    b = Image.fromarray((g * 255).astype(np.uint8), 'RGBA')
    return {'A': a, 'B': b}


def paste_ship(canvas, sprite, ship, eye, cam):
    pt, pb = project(ship['tail'], eye, cam), project(ship['bow'], eye, cam)
    if not pt or not pb:
        return None
    dx, dy = pb[0] - pt[0], pb[1] - pt[1]
    length = math.hypot(dx, dy)
    if length < 4:
        return None
    spr = sprite
    if dx < 0:                                          # its bow points left on screen: mirror, keep it upright
        spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        dx, dy = -dx, -dy
    k = length / spr.width
    spr = spr.resize((max(1, int(spr.width * k)), max(1, int(spr.height * k))), Image.LANCZOS)
    spr = spr.rotate(-math.degrees(math.atan2(dy, dx)), resample=Image.BICUBIC, expand=True)
    cx, cy = (pt[0] + pb[0]) / 2, (pt[1] + pb[1]) / 2
    canvas.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)))
    return pt, pb


def blaze_points(eye, t0, t, data):
    """the blaze's glows on screen: gen_fx.BLAZE laid out on the sign host (camera + bearing x SIGN_DIST)."""
    el, yaw = math.radians(data['sign']['el']), math.radians(data['sign']['yaw'])
    bearing = np.array([math.cos(el) * math.cos(yaw), math.cos(el) * math.sin(yaw), math.sin(el)])
    hy = math.radians(data['sign']['yaw'] + 180)
    left = np.array([-math.sin(hy), math.cos(hy), 0.0])                  # the host's local +Y (its left)
    fwd = np.array([math.cos(el) * math.cos(hy), math.cos(el) * math.sin(hy), -math.sin(el)])
    up = np.cross(fwd, left)                                             # the host's local +Z
    host = np.asarray(eye) + bearing * gen_fx.SIGN_DIST
    life = (t - t0) / (gen_fx.BLAZE_LIFE / 1000.0)
    out = []
    for name, feature, size, size_end, rgb, alpha in gen_fx.BLAZE:
        oy, oz = gen_fx.sign_offset(feature)
        out.append((host + left * oy + up * oz, size + (size_end - size) * min(max(life, 0), 1), rgb, curve(alpha, life)))
    return out


def frame(data, f, sky, rot, sprites, font):
    S, B, FL = data['scene'], data['beats'], data['flash']
    t, eye = f['t'], f['eye']
    cam = basis(f['view']['pitch'], f['view']['yaw'])
    img, dirs = render_sky(sky, cam, rot)
    # THE DULL SIGN (docs/196 s6): the sky panorama used here still carries the LIT bake unless it was re-rendered
    # with --sign-state dull; until the lit card holds (gen_fx.BLAZE_AT) the sign's cone is dimmed to stand in for
    # the dull bake (a preview stand-in, not an effect: nothing dims the sign in game, the bake IS dull)
    if t < gen_fx.BLAZE_AT:
        el, yaw = math.radians(data['sign']['el']), math.radians(data['sign']['yaw'])
        sd = np.array([math.cos(el) * math.cos(yaw), math.cos(el) * math.sin(yaw), math.sin(el)])
        ang = np.degrees(np.arccos(np.clip(dirs @ sd, -1, 1)))
        dim = 0.22 + 0.78 * np.clip((ang - 24) / 12, 0, 1)
        img *= dim[..., None]
    # THE BLAZE (additive, the effect's own table; it starts when the lit card holds)
    if t >= gen_fx.BLAZE_AT:
        for q, size, rgb, a in blaze_points(eye, gen_fx.BLAZE_AT, t, data):
            p = project(q, eye, cam)
            if p:
                add_glow(img, p[0], p[1], size / 2 / p[2] / TX * W / 2, rgb, a * 0.9)
    # THE FIREBALL + smoke + the reactor blasts + the wreckage (stand-ins at the effects' scale)
    if t >= B['IMPACT']:
        age = t - B['IMPACT']
        p = project(S['CRASH'], eye, cam)
        if p:
            px_u = 1 / p[2] / TX * W / 2
            smoke = np.clip(1 - age / 3.2, 0, 1) * 0.55
            add_glow(img, p[0], p[1], 3600 * px_u, (-0.25, -0.24, -0.22), smoke)          # dark smoke (subtractive)
            # the fireball's light (gen_fx jt_fireball: 9,000 -> 12,500 u, 0.8 -> 0.62 at 0.4 -> 0 over 2.3 s)
            fb = age / 2.3
            if fb < 1:
                add_glow(img, p[0], p[1], (9000 + 3500 * fb) * px_u, (1.0, 0.42, 0.1),
                         curve([(0, 0.0), (0.05, 0.8), (0.4, 0.62), (1, 0.0)], fb) * 0.8)
            add_glow(img, p[0], p[1], 2400 * px_u * min(1, 0.4 + age), (1.0, 0.55, 0.18), max(0, 1.3 - age * 0.45))
            add_glow(img, p[0], p[1], 1000 * px_u, (1.0, 0.9, 0.7), max(0, 1.0 - age * 0.5))
        for k, key in enumerate(('WRECK_A', 'WRECK_B')):
            for n in range(6):
                ta = age - 0.5 - n * 0.12
                if ta <= 0:
                    continue
                side = -1 if k == 0 else 1
                w = np.asarray(S[key]) + np.array([0, side * 450 * ta * (0.6 + 0.15 * n), -700 * ta - 110 * ta * ta])
                pw = project(w, eye, cam)
                if pw:
                    add_glow(img, pw[0], pw[1], 380 / pw[2] / TX * W / 2, (1.0, 0.5, 0.15), max(0, 1 - ta / 4))
            if age >= 0.28 + 0.22 * k:
                pw = project(S[key], eye, cam)
                if pw:
                    add_glow(img, pw[0], pw[1], 1500 / pw[2] / TX * W / 2, (1.0, 0.6, 0.25), max(0, 1.1 - (age - 0.3) * 0.5))
    canvas = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), 'RGB').convert('RGBA')
    # THE SHIPS, their warp flashes and burns
    for sh in f['ships']:
        placed = paste_ship(canvas, sprites[sh['variant']], sh, eye, cam)
        if not placed:
            continue
        pt, pb = placed
        glow = np.asarray(canvas, float)[..., :3] / 255
        po = project(sh['origin'], eye, cam)
        if sh['warp'] < 0.9 and po:
            k = 1 - sh['warp'] / 0.9
            add_glow(glow, po[0], po[1], 2600 / po[2] / TX * W / 2, (0.55, 0.8, 1.0), 1.3 * k)
            add_glow(glow, po[0], po[1], 900 / po[2] / TX * W / 2, (1.0, 1.0, 1.0), 1.2 * k)
        if sh['burn'] is not None:
            add_glow(glow, pt[0], pt[1], 520 / pt[2] / TX * W / 2, (0.35, 0.85, 1.0), 1.0)
            add_glow(glow, pt[0], pt[1], 200 / pt[2] / TX * W / 2, (1.0, 1.0, 1.0), 1.0)
        canvas = Image.fromarray((np.clip(glow, 0, 1) * 255).astype(np.uint8), 'RGB').convert('RGBA')
    # THE WHITE-OUT (TodJumpCine: in, full hold, out through orange)
    rgb = np.asarray(canvas, float)[..., :3] / 255
    if t >= B['IMPACT']:
        a, age = 0.0, (t - B['IMPACT']) * 1000
        hot, burn = np.array([1.0, 0.97, 0.9]), np.array([1.0, 0.55, 0.22])
        if age < FL['IN']:
            a, col = age / FL['IN'], hot
        elif age < FL['IN'] + FL['HOLD']:
            a, col = 1.0, hot
        else:
            k = min(1.0, (age - FL['IN'] - FL['HOLD']) / FL['OUT'])
            a, col = 1 - k, hot + (burn - hot) * k
        rgb = rgb * (1 - a) + col * a
    canvas = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W, BAR], fill=(0, 0, 0))
    d.rectangle([0, H - BAR, W, H], fill=(0, 0, 0))
    d.text((24, 26), 't = %.2f s' % t, fill=(255, 255, 255), font=font)
    d.text((170, 26), f['label'], fill=(220, 220, 220), font=font)
    d.text((24, H - BAR + 26), 'storyboard preview - sky panorama + live scene geometry; effects are stand-ins', fill=(140, 140, 150), font=font)
    return canvas


def main():
    out_dir = REPO / 'docs/196_ref'
    if '--out' in sys.argv:
        out_dir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(subprocess.run(['node', str(HERE / 'storyboard_data.js')], capture_output=True, text=True, check=True).stdout)
    sky = np.asarray(Image.open(SKY).convert('RGB'), float) / 255
    rot = sky_rotation()
    sprites = ship_sprite()
    try:
        font = ImageFont.truetype(r'C:\Windows\Fonts\ARIALNB.TTF', 30)
    except OSError:
        font = ImageFont.load_default()
    frames = [frame(data, f, sky, rot, sprites, font) for f in data['frames']]
    for i, im in enumerate(frames):
        im.save(out_dir / ('crash_frame_%d.png' % (i + 1)))
    cols, tw, th = 2, W // 2, H // 2
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw, rows * th), (8, 8, 12))
    for i, im in enumerate(frames):
        sheet.paste(im.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    sheet.save(out_dir / 'crash_storyboard.png')
    print('CRASH STORYBOARD', len(frames), 'frames ->', out_dir / 'crash_storyboard.png', '(skyRotation %g)' % rot)


if __name__ == '__main__':
    main()
