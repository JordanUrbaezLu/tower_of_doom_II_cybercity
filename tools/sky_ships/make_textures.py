"""THE SKY FLEET textures, v2 "a lot more detail" (docs/192 s8) - system Python (numpy + PIL), deterministic.

  python tools/sky_ships/make_textures.py            write every texture into model_export/tod_sky_ships/_images
  python tools/sky_ships/make_textures.py --check    FAIL if a written PNG differs from a fresh generation

Run BEFORE 01_studio.py (the studio only loads these PNGs and builds the materials). Every image is a multiple
of 4 on both sides (compressed BC images must be) and tiles seamlessly where it is box-mapped.

  i_tod_sky_plate_c / plate2_c   hull plating (2048): a recursive panel layout on a 16 px grid, each plate its own
                                 tone; seams, bolt rows, recessed insets, vent slots, grilles, hazard plates, grime
  i_tod_sky_plate_n              the same layout as a tangent-space normal map (seams are grooves, insets recess,
                                 vents are slots, bolts are domes)
  i_tod_sky_plate*_g / plate*_s  matching dark/light plating gloss and specular; shared wear masks per layout
  i_tod_sky_win2_c               dense lit windows (1024 x 256), four rows, lived-in (dark, warm, cool, dim)
  i_tod_sky_deco_c               hull markings in the map's typeface (fonts/tod_tower1.ttf): registrations, the
                                 crown emblem, hazard chevrons, docking arrows (1024 x 512)
  i_tod_sky_ads_c / ads2_c       the hauler's billboard wall: 8 of the sky's own neon ads (art/sky3d/billboards);
                                 ads2 is variant B's lineup (the same cells, other ads)
  i_tod_sky_glow_*              uniform color only for manufactured light sources (64 x 64)
  i_tod_sky_cargo_*             worn cargo enamel; mapped substrate chips, scuffs, grain and finish (1024)
  i_tod_sky_drive_*             nonemissive machined/heat-tempered/sooted nozzle alloy (1024)
  i_tod_sky_mineral_*           luminous mineral with dark inclusions and fine fractures (1024)
  i_tod_sky_rock_* / rock2_c     v3: the asteroids' tileable rock (1024): pitted, mottled, two tones (rock_textures.py)
"""
import hashlib, io, pathlib, sys
import numpy as np
import surface_weathering as W
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sky_data import GLOW, CARGO, DECO_CELLS, AD_ORDER, AD_ORDER_B

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'model_export/tod_sky_ships/_images'
FONT = ROOT / 'fonts/tod_tower1.ttf'
ADS = ROOT / 'art/sky3d/billboards'



def srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)


def to_png(arr, linear=True):
    """arr: float HxWx3|4 in 0..1 (linear colour unless linear=False) -> PNG bytes."""
    a = np.array(arr, dtype=np.float64)
    rgb = srgb(a[..., :3]) if linear else np.clip(a[..., :3], 0, 1)
    out = np.concatenate([rgb, a[..., 3:4] if a.shape[-1] == 4 else np.ones(a.shape[:2] + (1,))], axis=-1)
    im = Image.fromarray(np.round(out * 255).astype(np.uint8), 'RGBA')
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=False)
    return buf.getvalue()


def tile_noise(n, scale, seed):
    """Tileable smooth noise in -1..1 (band-limited white noise through an FFT = circular = seamless)."""
    r = np.random.default_rng(seed)
    spec = np.fft.rfft2(r.standard_normal((n, n)))
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.rfftfreq(n)[None, :]
    f = np.sqrt(fx * fx + fy * fy) * n
    spec *= np.exp(-(f / scale) ** 2)
    x = np.fft.irfft2(spec, (n, n))
    return x / (np.abs(x).max() + 1e-9)


def streaks(n, seed):
    """Tileable vertical streaks: fine across x, long along y (grime running down), 0..1."""
    r = np.random.default_rng(seed)
    spec = np.fft.rfft2(r.standard_normal((n, n)))
    fy = np.abs(np.fft.fftfreq(n)[:, None]) * n
    fx = np.fft.rfftfreq(n)[None, :] * n
    spec *= np.exp(-(fx / 220.0) ** 2 - (fy / 5.0) ** 2)
    x = np.fft.irfft2(spec, (n, n))
    x = x / (np.abs(x).max() + 1e-9)
    return np.clip(x, 0, 1) ** 1.5


# ---- the plate layout (shared by the colour, normal, gloss and spec maps) --------------------------------
def plate_layout(n, seed, min_s=48, max_s=448, grid=16):
    r = np.random.default_rng(seed)
    rects = []

    def snap(v):
        return int(v // grid * grid)

    def split(x0, y0, x1, y1, depth):
        w, h = x1 - x0, y1 - y0
        small = w <= max_s and h <= max_s
        if (small and r.random() < 0.28 + 0.12 * depth) or (w < 2 * min_s and h < 2 * min_s):
            rects.append((x0, y0, x1, y1))
            return
        horiz = (w >= h) if r.random() < 0.8 else (w < h)
        if horiz and w >= 2 * min_s:
            s = snap(r.integers(min_s, w - min_s + 1)) or min_s
            split(x0, y0, x0 + s, y1, depth + 1)
            split(x0 + s, y0, x1, y1, depth + 1)
        elif h >= 2 * min_s:
            s = snap(r.integers(min_s, h - min_s + 1)) or min_s
            split(x0, y0, x1, y0 + s, depth + 1)
            split(x0, y0 + s, x1, y1, depth + 1)
        else:
            rects.append((x0, y0, x1, y1))

    split(0, 0, n, n, 0)
    return rects


def plating(n, seed, base, spread):
    """-> (albedo linear HxWx3, height HxW, gloss HxW, spec HxW)."""
    r = np.random.default_rng(seed + 1000)
    rects = plate_layout(n, seed)
    tone = np.ones((n, n))
    height = np.zeros((n, n))
    gloss = np.full((n, n), 0.55)
    spec = np.full((n, n), 0.26)
    hazard = np.zeros((n, n))
    seam = 3
    yy, xx = np.mgrid[0:n, 0:n]
    for (x0, y0, x1, y1) in rects:
        w, h = x1 - x0, y1 - y0
        kind = r.random()
        t = 1 + r.uniform(-spread, spread)
        if kind < 0.05:
            t *= 0.55
        elif kind < 0.09:
            t *= 1.45
        pl = r.uniform(0.35, 1.0)
        sl = (slice(y0, y1), slice(x0, x1))
        tone[sl] = t
        height[sl] = pl
        gloss[sl] = np.clip(0.55 + r.uniform(-0.18, 0.12), 0.2, 0.85)
        spec[sl] = np.clip(0.26 + r.uniform(-0.08, 0.08), 0.1, 0.45)
        # the plate's own detail
        d = r.random()
        if d < 0.34 and w >= 64 and h >= 64:                     # bolt rows along the edges
            step = 32
            for bx in range(x0 + 16, x1 - 8, step):
                for by in (y0 + 9, y1 - 10):
                    height[by - 2:by + 3, bx - 2:bx + 3] = pl + 0.18
                    tone[by - 2:by + 3, bx - 2:bx + 3] = t * 1.25
            for by in range(y0 + 16, y1 - 8, step):
                for bx in (x0 + 9, x1 - 10):
                    height[by - 2:by + 3, bx - 2:bx + 3] = pl + 0.18
                    tone[by - 2:by + 3, bx - 2:bx + 3] = t * 1.25
        elif d < 0.54 and w >= 96 and h >= 96:                   # a recessed inset panel
            m = int(min(w, h) * r.uniform(0.14, 0.24))
            isl = (slice(y0 + m, y1 - m), slice(x0 + m, x1 - m))
            height[isl] = pl - 0.28
            tone[isl] = t * 0.82
            gloss[isl] -= 0.08
        elif d < 0.64 and w >= 96 and h >= 64:                   # vent slots
            m = 14
            for sy in range(y0 + m, y1 - m - 4, 10):
                height[sy:sy + 5, x0 + m:x1 - m] = pl - 0.45
                tone[sy:sy + 5, x0 + m:x1 - m] = t * 0.35
            gloss[y0 + m:y1 - m, x0 + m:x1 - m] = 0.3
        elif d < 0.70 and w >= 96 and h >= 96:                   # a fine grille
            m = 12
            g = np.zeros((h - 2 * m, w - 2 * m), bool)
            g[::8, :] = True
            g[:, ::8] = True
            sub = (slice(y0 + m, y1 - m), slice(x0 + m, x1 - m))
            height[sub] = np.where(g, pl, pl - 0.3)
            tone[sub] = np.where(g, t, t * 0.5)
        elif d < 0.735 and (w <= 96 or h <= 96):                 # a hazard plate (narrow): diagonal stripes
            stripe = (((xx[sl] + yy[sl]) // 22) % 2) == 0
            hazard[sl] = np.where(stripe, 1.0, 0.0)
        # seams on the left / top edge of every plate (the tile edges are shared by construction)
        height[y0:y0 + seam, x0:x1] = 0
        height[y0:y1, x0:x0 + seam] = 0
        tone[y0:y0 + seam, x0:x1] = 0.35
        tone[y0:y1, x0:x0 + seam] = 0.35
        gloss[y0:y0 + seam, x0:x1] = 0.25
        gloss[y0:y1, x0:x0 + seam] = 0.25
        # a worn, lighter lip just inside the seam (catches the moon at distance)
        tone[y0 + seam:y0 + seam + 1, x0 + seam:x1] *= 1.35
        tone[y0 + seam:y1, x0 + seam:x0 + seam + 1] *= 1.35
    grime = 1 + 0.16 * tile_noise(n, 10, seed + 7) + 0.06 * tile_noise(n, 60, seed + 8)
    streak = 1 - 0.12 * np.clip(streaks(n, seed + 9), 0, 1)             # run-off grime down the plates
    albedo = np.array(base)[None, None, :] * (tone * grime * streak)[:, :, None]
    haz = np.array((0.36, 0.26, 0.03))[None, None, :]
    albedo = np.where(hazard[:, :, None] > 0, haz, albedo)
    return W.plating(np.clip(albedo, 0, 1), height, gloss, spec, seed, tile_noise)


def normal_from_height(h, strength):
    hb = (h + np.roll(h, 1, 0) + np.roll(h, -1, 0) + np.roll(h, 1, 1) + np.roll(h, -1, 1)) / 5.0   # 1 px soften, tileable
    dx = (np.roll(hb, -1, 1) - np.roll(hb, 1, 1)) * 0.5
    dy = (np.roll(hb, -1, 0) - np.roll(hb, 1, 0)) * 0.5
    nx, ny, nz = -dx * strength, dy * strength, np.ones_like(hb)      # image rows run down: +v is up
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5, nz / ln * 0.5 + 0.5], axis=-1)


# ---- windows ---------------------------------------------------------------------------------------------
def windows(seed):
    r = np.random.default_rng(seed)
    W, H = 1024, 256
    a = np.zeros((H, W, 3))
    cols, rows = 40, 4
    cw = W // cols
    for row in range(rows):
        y0 = 14 + row * 60
        a[y0 + 48:y0 + 50, :] = (0.10, 0.08, 0.06)                      # a dim deck line under each row
        for c in range(cols):
            p = r.random()
            if p < 0.17:
                continue                                                  # dark
            x0 = c * cw + 5
            x1 = (c + 1) * cw - 5
            warm = np.array((1.0, 0.76, 0.44)) if p < 0.80 else np.array((0.55, 0.84, 1.0))
            lvl = r.uniform(0.55, 1.0) if p < 0.95 else 0.25               # a few dim ones
            ys = np.linspace(1.0, 0.72, 38)[:, None, None]                 # lamp light falls off down the pane
            a[y0:y0 + 38, x0:x1] = warm * lvl * ys
    return a


# ---- markings --------------------------------------------------------------------------------------------
def deco():
    """1024 x 512 atlas, black background (emissive: black does not glow). Cells (u0, v0, u1, v1) in 0..1 are
    listed in DECO_CELLS below; the ship scripts map quads onto them by name."""
    W, H = 1024, 512
    im = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(str(FONT), 150)
    mid = ImageFont.truetype(str(FONT), 96)

    def text_in(box, s, font, fill):
        x0, y0, x1, y1 = box
        bb = d.textbbox((0, 0), s, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        d.text((x0 + (x1 - x0 - tw) / 2 - bb[0], y0 + (y1 - y0 - th) / 2 - bb[1]), s, font=font, fill=fill)

    text_in((0, 0, 640, 170), 'TOD-01', big, (225, 245, 255))            # dreadnought registration
    text_in((0, 170, 640, 300), 'HAUL-07', mid, (255, 214, 150))          # hauler registration
    text_in((0, 300, 640, 420), 'GS-13', mid, (255, 205, 245))            # gunship registration
    # the crown emblem (the tower's crown: a band and five points) in a ring
    cx, cy, R = 832, 150, 128
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(255, 200, 90), width=14)
    band = [(cx - 78, cy + 52), (cx + 78, cy + 52), (cx + 70, cy + 22), (cx - 70, cy + 22)]
    d.polygon(band, fill=(255, 200, 90))
    pts = [(cx - 78, cy + 22), (cx - 88, cy - 52), (cx - 48, cy - 8), (cx - 26, cy - 72), (cx, cy - 16),
           (cx + 26, cy - 72), (cx + 48, cy - 8), (cx + 88, cy - 52), (cx + 78, cy + 22)]
    d.polygon(pts, fill=(255, 200, 90))
    # hazard chevrons (landing bays) and a docking arrow strip
    for i in range(10):
        x = 660 + i * 36
        d.polygon([(x, 300), (x + 18, 300), (x + 36, 360), (x + 18, 360)], fill=(255, 170, 20))
    for i in range(6):
        x = 664 + i * 58
        d.polygon([(x, 390), (x + 30, 420), (x, 450), (x + 12, 450), (x + 42, 420), (x + 12, 390)], fill=(90, 230, 255))
    return np.asarray(im, dtype=np.float64) / 255.0




# ---- the ad wall -----------------------------------------------------------------------------------------


def ads(order=AD_ORDER):
    W, H = 2048, 1024
    im = Image.new('RGB', (W, H), (4, 4, 6))
    for i, name in enumerate(order):
        src = Image.open(ADS / (name + '.png')).convert('RGB')
        src.thumbnail((512, 512), Image.LANCZOS)
        cell = Image.new('RGB', (512, 512), (4, 4, 6))
        cell.paste(src, ((512 - src.width) // 2, (512 - src.height) // 2))
        im.paste(cell, ((i % 4) * 512, (i // 4) * 512))
    return np.asarray(im, dtype=np.float64) / 255.0


def solid(rgb, n=64):
    a = np.ones((n, n, 3))
    a[:, :] = rgb
    return a


def build():
    out = {}
    N = 2048
    c1, h1, g1, s1 = plating(N, 21, (0.062, 0.069, 0.084), 0.22)   # lifted from 0.050: the plating must read under the moon
    c2, h2, g2, s2 = plating(N, 22, (0.165, 0.172, 0.186), 0.16)
    out['i_tod_sky_plate_c'] = to_png(c1)
    out['i_tod_sky_plate2_c'] = to_png(c2)
    out['i_tod_sky_plate_n'] = to_png(normal_from_height(h1, 5.0), linear=False)
    out['i_tod_sky_plate2_n'] = to_png(normal_from_height(h2, 5.0), linear=False)
    g = Image.fromarray(np.round(np.clip(g1, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR)
    out['i_tod_sky_plate_g'] = to_png(np.repeat((np.asarray(g, dtype=np.float64) / 255)[:, :, None], 3, -1), linear=False)
    s = Image.fromarray(np.round(np.clip(s1, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR)
    out['i_tod_sky_plate_s'] = to_png(np.repeat((np.asarray(s, dtype=np.float64) / 255)[:, :, None], 3, -1), linear=False)
    for suffix, channel in (('g', g2), ('s', s2)):
        im = Image.fromarray(np.round(np.clip(channel, 0, 1)*255).astype(np.uint8)).resize((1024,1024), Image.BILINEAR)
        out['i_tod_sky_plate2_'+suffix] = to_png(np.repeat((np.asarray(im,dtype=np.float64)/255)[:,:,None],3,-1), linear=False)
    out['i_tod_sky_win2_c'] = to_png(windows(31))
    out['i_tod_sky_deco_c'] = to_png(deco(), linear=False)
    out['i_tod_sky_ads_c'] = to_png(ads(), linear=False)
    out['i_tod_sky_ads2_c'] = to_png(ads(AD_ORDER_B), linear=False)
    out['i_tod_sky_flat_n'] = to_png(solid((0.5, 0.5, 1.0)), linear=False)
    out['i_tod_sky_flat_g'] = to_png(solid((0.35, 0.35, 0.35)), linear=False)
    out['i_tod_sky_flat_s'] = to_png(solid((0.04, 0.04, 0.04)))
    for k, rgb in GLOW.items():
        out['i_tod_sky_glow_' + k] = to_png(solid(rgb))
    for k, rgb in CARGO.items():
        cc, ch, cg, cs = W.cargo(1024, rgb, tile_noise)
        out['i_tod_sky_' + k] = to_png(cc)
    out['i_tod_sky_cargo_n'] = to_png(normal_from_height(ch, 4.0), linear=False)
    out['i_tod_sky_cargo_g'] = to_png(np.repeat(cg[:,:,None],3,-1), linear=False)
    out['i_tod_sky_cargo_s'] = to_png(np.repeat(cs[:,:,None],3,-1))
    dc, dh, dg, ds = W.drive_metal(1024, tile_noise)
    out['i_tod_sky_drive_c'] = to_png(dc)
    out['i_tod_sky_drive_n'] = to_png(normal_from_height(dh, 4.0), linear=False)
    out['i_tod_sky_drive_g'] = to_png(np.repeat(dg[:,:,None],3,-1), linear=False)
    out['i_tod_sky_drive_s'] = to_png(np.repeat(ds[:,:,None],3,-1))
    mm, mh, mg, ms = W.mineral(1024, tile_noise)
    for key in ('magenta','cyan','amber'):
        out['i_tod_sky_mineral_'+key+'_c'] = to_png(np.array(GLOW[key])[None,None,:]*mm[:,:,None])
    out['i_tod_sky_mineral_n'] = to_png(normal_from_height(mh, 4.0), linear=False)
    out['i_tod_sky_mineral_g'] = to_png(np.repeat(mg[:,:,None],3,-1), linear=False)
    out['i_tod_sky_mineral_s'] = to_png(np.repeat(ms[:,:,None],3,-1))
    import rock_textures                                              # v3: the asteroids' rock (rock_textures.py)
    out.update(rock_textures.rocks())
    return out


def main():
    imgs = build()
    for name, data in imgs.items():
        im = Image.open(io.BytesIO(data))
        assert im.width % 4 == 0 and im.height % 4 == 0, name + ' must be a multiple of 4'
    if '--check' in sys.argv:
        bad = [n for n, b in imgs.items() if not (OUT / (n + '.png')).exists() or (OUT / (n + '.png')).read_bytes() != b]
        if bad:
            print('SKY TEXTURES STALE:', ', '.join(bad), '- run python tools/sky_ships/make_textures.py')
            sys.exit(1)
        print('SKY TEXTURES OK', len(imgs))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in imgs.items():
        (OUT / (name + '.png')).write_bytes(data)
    print('SKY TEXTURES WRITTEN', len(imgs), {n: hashlib.sha256(b).hexdigest()[:10] for n, b in imgs.items() if 'glow' not in n and 'cargo' not in n})


if __name__ == '__main__':
    main()
