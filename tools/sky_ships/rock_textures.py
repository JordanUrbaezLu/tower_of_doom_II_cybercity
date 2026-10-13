"""THE SKY FLEET's asteroid textures (docs/192 s10) - system Python (numpy + PIL), deterministic, tileable.
make_textures.py builds these with the ship textures (and --check gates them); this module only holds the recipe.

  rocks() -> {name: PNG bytes}
    i_tod_sky_rock_c    basalt-grey stony surface (1024): low-frequency tone, crater pits with darker floors and lighter
                        ejecta rims, mineral flecks, fine grain
    i_tod_sky_rock2_c   the same ground in a warm carbonaceous brown (a different rock family, same relief)
    i_tod_sky_rock_n    tangent relief (pits, rims, lumps, grain, broken fractures and mineral inclusions)
    i_tod_sky_rock_g    gloss (rough: 0.12..0.3, a little shine on the fleck minerals)
    i_tod_sky_rock_s    specular (dim: 0.03..0.08)
"""
import numpy as np
import surface_weathering as W
import make_textures as T

N = 1024


def pits(n, rng, count, rmin, rmax):
    """Tileable crater pits: bowl depth, raised rim, ejecta brightening -> (height, floor_dark, rim_light)."""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float64)
    h = np.zeros((n, n))
    floor = np.zeros((n, n))
    rim = np.zeros((n, n))
    for _ in range(count):
        u = rng.uniform(0, 1) ** 2.6
        r = rmin + (rmax - rmin) * u
        cx, cy = rng.uniform(0, n), rng.uniform(0, n)
        dx = (xx - cx + n / 2) % n - n / 2                      # tileable distance (torus)
        dy = (yy - cy + n / 2) % n - n / 2
        d = np.sqrt(dx * dx + dy * dy) / r
        m = d < 1.8
        if not m.any():
            continue
        bowl = np.where(d < 1, (d * d - 1), 0.0)
        ring = np.exp(-((d - 1.0) / 0.2) ** 2)
        depth = 0.55 * rng.uniform(0.7, 1.2)
        h += (bowl * depth + ring * 0.28) * (r / rmax) ** 0.5
        floor = np.maximum(floor, np.where(d < 0.85, (0.85 - d) / 0.85, 0))
        rim = np.maximum(rim, ring * np.where(d > 0.9, 1, 0.4))
    return h, floor, rim


def rocks():
    rng = np.random.default_rng(7707)
    lo = T.tile_noise(N, 6, 7701)
    mid = T.tile_noise(N, 24, 7702)
    fine = T.tile_noise(N, 160, 7703)
    grain = T.tile_noise(N, 420, 7704)
    ph, floor, rim = pits(N, rng, 55, 5, 64)
    height = 0.55 * lo + 0.35 * mid + 0.12 * fine + 0.05 * grain + 0.75 * ph
    # mineral flecks: sparse bright specks
    fl = np.clip((T.tile_noise(N, 380, 7705) - 0.72) * 6.0, 0, 1)
    # mottling: rocky cells of lighter and darker stone (thresholded noise, not circles)
    cells = np.clip((T.tile_noise(N, 40, 7708) + 0.25 * T.tile_noise(N, 120, 7709)) * 2.2, -1, 1)
    tone = (1 + 0.3 * lo + 0.16 * mid + 0.08 * fine + 0.14 * cells) * (1 - 0.3 * floor) * (1 + 0.16 * rim) * (1 + 0.9 * fl)
    tone = np.clip(tone, 0.25, 2.2)
    cracks, shoulders, mineral = W.fractures(N, T.tile_noise)
    # Dark hairline fractures, lifted flaked shoulders, and inclusions respond in all channels.
    height += -0.15*cracks + 0.055*shoulders + 0.034*mineral
    tone *= (1-0.36*cracks)*(1+0.10*shoulders+0.24*mineral)
    out = {}
    warm = 0.5 + 0.5 * T.tile_noise(N, 10, 7706)
    for name, base, tint in (('i_tod_sky_rock_c', (0.092, 0.089, 0.085), (0.98, 1.0, 1.04)),
                             ('i_tod_sky_rock2_c', (0.105, 0.083, 0.063), (1.04, 1.0, 0.94))):
        col = np.array(base)[None, None, :] * tone[:, :, None]
        col = col * (1 + (np.array(tint)[None, None, :] - 1) * warm[:, :, None])
        mineral_tint = np.array((1.15,1.03,0.83) if 'rock2' in name else (0.9,1.02,1.16))
        col *= 1+(mineral_tint-1)*mineral[:,:,None]*0.7
        out[name] = T.to_png(np.clip(col, 0, 1))
    out['i_tod_sky_rock_n'] = T.to_png(T.normal_from_height(height, 7.0), linear=False)
    gloss = np.clip(0.18 + 0.06 * mid + 0.35 * fl - 0.05 * floor + 0.16*mineral - 0.05*cracks, 0.08, 0.6)
    spec = np.clip(0.05 + 0.015 * mid + 0.05 * fl + 0.055*mineral - 0.018*cracks, 0.02, 0.12)
    out['i_tod_sky_rock_g'] = T.to_png(np.repeat(gloss[:, :, None], 3, -1), linear=False)
    out['i_tod_sky_rock_s'] = T.to_png(np.repeat(spec[:, :, None], 3, -1))
    return out


if __name__ == '__main__':                                      # write to a folder for a preview (make_textures owns the real ones)
    import sys, pathlib
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'tmp/sky_ships/tex_stage')
    out.mkdir(parents=True, exist_ok=True)
    for n, b in rocks().items():
        (out / (n + '.png')).write_bytes(b)
    print('ROCK TEXTURES', out, sorted(rocks()))
