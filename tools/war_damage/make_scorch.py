"""THE WAR DAMAGE PASS, phase 2 build B (docs/205 s7b): THE SCORCHED TILES, GENERATED - never hand-edit the PNGs.

  python tools/war_damage/make_scorch.py           write model_export/tod_surface/_images/i_tod_cc_<floor|wall|armor>_scorch_{c,n,g,s,e}.png
                                                   + art/war_damage/scorch_manifest.json (the shas install_surfaces.py asserts)
  python tools/war_damage/make_scorch.py --check   FAIL if any written file differs from a fresh render
  python tools/war_damage/make_scorch.py --preview art/war_damage/review/scorch_tiles.png   a before/after strip

Three new tile kinds for the surface kit (floor / wall / armor: the armor tile carries the bronze and oxblood walls) (tools/art_cohesion/surface_definition.py reads them through the roles in
crown_materials.json): the kit's own FLOOR and WALL tiles (art/cybercity_materials, 1024 texels = 128 units) burned.
Soot is a field of soft blotches with a dark core that fades over the tile, streaked down the wall / across the
floor, with charred flecks (blistered coating) inside the darkest areas, so the tile still reads as the same panel
underneath. Per map:
  c  colour: darkened by the soot (down to ~12 % in the core), desaturated where it is darkest; the flecks near black
  g  gloss: soot is matte (gloss x 0.25 under the darkest soot, the flecks lower still)
  s  specular: dimmed with the soot (x 0.3)
  n  normal: fine crackle in the burnt areas (blistered paint), the panel's own relief kept
  e  emissive: black (the kit's e maps are black: world emission is off)
Seeded numpy, so a fresh render is byte-identical; the tile stays seamless (every field is built periodic).
"""
import hashlib, json, pathlib, sys

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
IMAGES = ROOT / 'model_export/tod_surface/_images'
MANIFEST = ROOT / 'art/war_damage/scorch_manifest.json'
KINDS = {'floor': 'floor_scorch', 'wall': 'wall_scorch', 'armor': 'armor_scorch'}   # the armor tile: the bronze / oxblood walls
N = 1024
SEED = 20261003


def periodic_noise(rng, n, cells, octaves=4, gain=0.5):
    """Value noise, periodic in both axes (the tile stays seamless), 0..1. `cells` must divide n."""
    assert n % cells == 0, (n, cells)
    acc = np.zeros((n, n))
    amp, total = 1.0, 0.0
    for o in range(octaves):
        c = cells * (2 ** o)
        grid = rng.random((c, c))
        big = np.kron(grid, np.ones((n // c, n // c)))                 # nearest, then smoothed below
        # smooth with a periodic box blur (two passes) so cells blend into soft blotches
        k = max(2, n // c // 2)
        for _ in range(2):
            big = sum(np.roll(big, s, axis=0) for s in range(-k, k + 1)) / (2 * k + 1)
            big = sum(np.roll(big, s, axis=1) for s in range(-k, k + 1)) / (2 * k + 1)
        acc += amp * big
        total += amp
        amp *= gain
    acc /= total
    acc = (acc - acc.min()) / (acc.max() - acc.min() + 1e-9)
    return acc


def soot_field(rng, kind):
    """0..1 soot density: several dark cores that fade, streaked (down a wall, across a floor), a thin grime over
    the rest of the tile so it reads dirtier everywhere, plus a fine grain. Built periodic: the tile stays seamless."""
    big = periodic_noise(rng, N, 4, octaves=3)                         # the big patches (cell counts divide 1024)
    mid = periodic_noise(rng, N, 8, octaves=3)                         # smaller patches breaking the big ones up
    grain = periodic_noise(rng, N, 32, octaves=3, gain=0.6)            # the fine texture of the soot
    cores = np.clip((big - 0.42) / 0.45, 0, 1) ** 1.5 * 0.7 + np.clip((mid - 0.55) / 0.35, 0, 1) ** 1.3 * 0.6
    cores = np.clip(cores, 0, 1) * (0.7 + 0.3 * grain)
    # streaks: smear the cores along the fall direction (down a wall; across a floor, a diagonal drift)
    streak = cores.copy()
    length = 140 if kind != 'floor' else 48
    for i in range(1, length):
        w = (1 - i / length) ** 1.6 * 0.45
        shifted = np.roll(cores, i, axis=0) if kind != 'floor' else np.roll(np.roll(cores, i, axis=0), i // 2, axis=1)
        streak = np.maximum(streak, shifted * w)
    field = np.clip(0.8 * cores + 0.55 * streak, 0, 1)
    # a soft envelope so the tile is not evenly dirty (a quarter of it stays near-clean), and a thin grime under all of it
    envelope = periodic_noise(rng, N, 2, octaves=2)
    field = field * np.clip((envelope - 0.15) / 0.55, 0, 1)
    grime = 0.12 * periodic_noise(rng, N, 8, octaves=3, gain=0.55) * np.clip((envelope - 0.05) / 0.6, 0, 1)
    return np.clip(field + grime, 0, 1)


def flecks(rng, soot):
    """Blistered coating: small charred flecks inside the darkest soot (0..1 mask)."""
    f = periodic_noise(rng, N, 64, octaves=2, gain=0.5)
    mask = (f > 0.68).astype(float) * np.clip((soot - 0.45) / 0.3, 0, 1)
    return mask


def load(name):
    return np.asarray(Image.open(IMAGES / (name + '.png')).convert('RGBA')).astype(np.float64) / 255.0


def save_png(path, arr):
    Image.fromarray(np.clip(np.round(arr * 255), 0, 255).astype(np.uint8), 'RGBA').save(path, optimize=False, compress_level=6)


def render(kind, rng):
    soot = soot_field(rng, kind)
    fl = flecks(rng, soot)
    out = {}
    src = {sfx: load(f'i_tod_cc_{kind}_{sfx}') for sfx in 'cngse'}
    # colour: darken, desaturate where darkest; flecks near black with a faint warm rim
    c = src['c'].copy()
    dark = 1 - 0.88 * soot
    rgb = c[..., :3] * dark[..., None]
    lum = rgb.mean(axis=2, keepdims=True)
    rgb = rgb * (1 - 0.6 * soot[..., None]) + lum * (0.6 * soot[..., None])
    rgb = rgb * (1 - 0.85 * fl[..., None]) + np.array([0.05, 0.03, 0.02]) * fl[..., None]
    c[..., :3] = rgb
    out['c'] = c
    # gloss / specular: soot is matte and dull
    g = src['g'].copy(); g[..., :3] *= (1 - 0.75 * soot - 0.2 * fl)[..., None]; out['g'] = g
    s = src['s'].copy(); s[..., :3] *= (1 - 0.7 * soot - 0.2 * fl)[..., None]; out['s'] = s
    # normal: fine crackle where it burned (DirectX negative Y like the kit); the panel's own relief kept
    n = src['n'].copy()
    crack = periodic_noise(rng, N, 128, octaves=2, gain=0.5)
    dx = np.roll(crack, -1, axis=1) - np.roll(crack, 1, axis=1)
    dy = np.roll(crack, -1, axis=0) - np.roll(crack, 1, axis=0)
    amt = (0.35 * soot + 0.5 * fl)
    n[..., 0] = np.clip(n[..., 0] + dx * 2.2 * amt, 0, 1)
    n[..., 1] = np.clip(n[..., 1] - dy * 2.2 * amt, 0, 1)
    out['n'] = n
    out['e'] = src['e'].copy()                                           # black: world emission stays off
    return out, soot


def build():
    files, stats = {}, {}
    for i, (kind, tag) in enumerate(KINDS.items()):
        rng = np.random.default_rng(SEED + i)
        maps, soot = render(kind, rng)
        for sfx, arr in maps.items():
            files[f'i_tod_cc_{tag}_{sfx}.png'] = arr
        stats[tag] = {'soot_mean': round(float(soot.mean()), 4), 'soot_over_half': round(float((soot > 0.5).mean()), 4)}
    return files, stats


def to_bytes(arr):
    import io
    buf = io.BytesIO()
    Image.fromarray(np.clip(np.round(arr * 255), 0, 255).astype(np.uint8), 'RGBA').save(buf, format='PNG', optimize=False, compress_level=6)
    return buf.getvalue()


def main(argv):
    files, stats = build()
    blobs = {name: to_bytes(arr) for name, arr in files.items()}
    if '--preview' in argv:
        out = pathlib.Path(argv[argv.index('--preview') + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        tiles = []
        for kind, tag in KINDS.items():
            before = Image.open(IMAGES / f'i_tod_cc_{kind}_c.png').convert('RGB').resize((512, 512))
            after = Image.fromarray(np.clip(np.round(files[f'i_tod_cc_{tag}_c.png'] * 255), 0, 255).astype(np.uint8), 'RGBA').convert('RGB').resize((512, 512))
            gloss = Image.fromarray(np.clip(np.round(files[f'i_tod_cc_{tag}_g.png'] * 255), 0, 255).astype(np.uint8), 'RGBA').convert('RGB').resize((512, 512))
            tiles.append((before, after, gloss))
        strip = Image.new('RGB', (512 * 3, 512 * len(tiles)), (0, 0, 0))
        for r, row in enumerate(tiles):
            for cidx, im in enumerate(row):
                strip.paste(im, (cidx * 512, r * 512))
        strip.save(out)
        print('SCORCH PREVIEW ->', out, stats)
        return 0
    # install_surfaces.py / verify_surfaces.py take this as a third source library: its `master` is this generator
    manifest = {'master': 'tools/war_damage/make_scorch.py', 'master_sha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                'seed': SEED, 'tile_units': 128, 'tile_texels': N,
                'textures': {name: hashlib.sha256(b).hexdigest() for name, b in blobs.items()}, 'stats': stats}
    text = json.dumps(manifest, indent=1) + '\n'
    if '--check' in argv:
        bad = [name for name, b in blobs.items() if not (IMAGES / name).exists() or (IMAGES / name).read_bytes() != b]
        if not MANIFEST.exists() or MANIFEST.read_text(encoding='utf-8') != text:
            bad.append(MANIFEST.name)
        if bad:
            print('SCORCH TILES STALE:', ', '.join(bad), '- run python tools/war_damage/make_scorch.py')
            return 1
        print('SCORCH TILES OK', len(blobs))
        return 0
    for name, b in blobs.items():
        (IMAGES / name).write_bytes(b)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(text, encoding='utf-8', newline='\n')
    print('SCORCH TILES WRITTEN:', len(blobs), 'maps ->', IMAGES, stats)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
