"""THE HAVEN DOME (docs/202) — the safe zones' force field, generated. TWO SKINS and THE FLOOR SIGNS since v3;
THE WHOLE HALL, THE DARKNESS and THE BARRIER since v4; THE BREACHED CORRUPTED MESH + ITS CRACKED-PANE ATLAS since v5
(user 2026-10-04: "I like the two states of the dome to be quite different" - see DARK_* below).

User 2026-10-02: "some kind of aura like maybe like a dome or like a force field
that animates when you walk in and walk out".
User 2026-10-03 (v3): "the dome should be evil at first ... You must kill them and
then the area turns into a safe zone ... two distinct states." And tweak #5: a big
glowing floor number per haven in the map's typeface and the district's colour.

The field is a GOLDBERG dome: the dual of a subdivided icosahedron, so every
cell is a true hexagon (a pentagon at the apex) on a sphere — a hex lattice with
no texture stretching anywhere. Each cell is a fan of triangles whose UV runs
from u = 0 at the cell centre to u = 1 at its rim, so ONE small strip texture
draws every cell's glowing edge (adjacent cells meet edge to edge, so each lattice
line is lit from both sides) over a faint teal haze. Cells the floor plane cuts
are clipped there, which draws the field's glowing contact line on the floor.

Geometry (from tools/haven_layout.js): the field sphere has radius DOME_S and its
centre sits DOME_C from the floor (v4: BELOW it - a low dome as wide as the hall,
passing under the galleries), so the floor ring is exactly DOME_R. Two shells
(outward and inward winding) so the lattice reads from outside AND from inside. No
collision: players and zombies walk through it (the bullet barrier is a separate
brush shell in the map, tools/haven_layout.js barrierBrushes).

v4 (user 2026-10-03: "Safe zone should be the entire area ... bullets cannot go in or
outside the dome. Until its a safe zone ... Going inside will make your screen dark
like you are being taken over by the darkness. Not crazy but for sure noticable and
sligtly annoying"):
  * THE BARRIER MATERIAL tod_haven_barrier: the stock weapon clip (no impact) copied
    whole from the tools' own clip GDT, plus missile clip (arrows, grenades) and no
    penetration (a sniper round must not punch through it). Nonsolid to bodies.
  * THE DARKNESS i_tod_haven_darkness: the screen's dark veil inside a corrupted field
    (TodHaven.lua tints it near-black and breathes it): a dim centre, heavy edges,
    smoky tendrils creeping in from them.

Material (the jump title's lit sign card recipe, proven in this map):
lit_emissive_transparent, colorMap alpha = coverage, colorTint 0 0 0 1 (no lit
diffuse), colorMap00 = the same image (the glow), scaleRGB = brightness. FIVE
models share one mesh through skinOverride: the SAFE field (idle, a PULSE twin for
the heartbeat and the crossing echo, a FLASH twin for a crossing) and the
CORRUPTED field (a crimson strip texture: the dark idle and its flash twin for the
wake and a guardian's death). The corrupted state has no heartbeat.

THE FLOOR SIGNS (tweak #5): ONE quad (tools/jump_title/make_sign_card.py's
recipe: a card facing +X, wound for BO3's front face) wearing one of EIGHT
materials: FLOOR 10 / 20 / 30 / 40 in the district's colour (safe) and in the
corrupted red (dark, with glitch slices). The textures are composed from the map's
own glyph sheets (source_data/tod_ui_images/_sheets, the typeface every HUD text
uses) and recoloured by luminance so the face, the 3D extrusion and the outline
keep their relationship; a soft glow and a fine scanline make it a hologram.
_tod_haven.gsc hangs it on the hall's S wall (tools/haven_layout.js SIGN).

    python -B tools/haven/make_dome.py          # write the assets (and source_data/tod_haven.gdt once wired)
    python -B tools/haven/make_dome.py --check  # verify they match a fresh render (build gate)

Re-run it; never hand-edit the outputs.
"""
import argparse, hashlib, io, json, math, os, pathlib, subprocess, sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(os.environ['APPDATA']) / 'Blender Foundation' / 'Blender' / '4.2' / 'scripts' / 'addons' / 'BetterBetterBlenderCOD'))
from PyCoD import xmodel  # noqa: E402

EXP = ROOT / 'model_export' / 'tod_haven'
IMG = EXP / '_images'
# THE GDT IS STAGED until the haven is wired (tools/haven/wire.py copies it into
# source_data right before the build): gdtdb converts every GDT in source_data on
# EVERY build, so a peer's build must never meet a half-installed asset.
GDT_STAGED = ROOT / 'art' / 'haven' / 'tod_haven.gdt'
GDT = ROOT / 'source_data' / 'tod_haven.gdt'
MANIFEST = ROOT / 'art' / 'haven' / 'manifest.json'
SHEETS = ROOT / 'source_data' / 'tod_ui_images' / '_sheets'
# THE BARRIER's donor: the tools' own clip GDT (read-only; the private root's art_assets is a junction to the install)
CLIP_GDT = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity\art_assets\t6_legacy\texture_assets\clip.gdt')
CLIP_DONOR = 'clip_weapon_noimpact'
BARRIER_MATERIAL = 'tod_haven_barrier'
BARRIER_OVERRIDES = {'missileClip': '1', 'noPenetrate': '1'}   # + arrows / grenades, + no bullet penetration

# the field's numbers come from the layout module (one source)
LAYOUT = json.loads(subprocess.check_output(
    ['node', '-e', "const H=require('./tools/haven_layout.js');console.log(JSON.stringify({R:H.DOME_R,C:H.DOME_C,S:H.DOME_S,TOP:H.DOME_TOP,SIGN:H.SIGN,MAT:H.BARRIER.mat}))"],
    cwd=ROOT, text=True))
R, CZ, S = LAYOUT['R'], LAYOUT['C'], LAYOUT['S']
if LAYOUT['MAT'] != 'tod_haven_barrier':
    raise SystemExit('haven: tools/haven_layout.js BARRIER.mat must be tod_haven_barrier (the material written here)')
SIGN_W_U, SIGN_H_U = LAYOUT['SIGN']['w'], LAYOUT['SIGN']['h']   # the card's size in world units (2:1, like its texture)

LODS = [(10, 0), (6, 3200)]         # (Goldberg frequency, switch-in distance); v4's sphere is ~1.5x v3's, so ~1.4x the cells
LIT_FRACTION = 0.11                  # cells with a brighter fill (breaks the uniform lattice)
# the field texture's alpha profile across a cell, centre (u 0) -> border (u 1)
FIELD_CLEAR, FIELD_LIT, FIELD_CORE = 0.018, 0.06, 0.13   # cell interiors: ordinary / lit / the apex + base skirt
FIELD_HALO_U, FIELD_HALO_A = 0.78, 0.10                  # a faint halo rises from here to the line
FIELD_LINE_U, FIELD_LINE_FULL_U, FIELD_LINE_A = 0.95, 0.99, 0.85   # the thin bright lattice line
SEED = 20261002
BRIGHT = {'mtl_tod_haven_field': 4.0, 'mtl_tod_haven_field_pulse': 7.0, 'mtl_tod_haven_field_flash': 13.0}
# v5: the corrupted skin's three brightnesses - its idle, the DIM dip of its flicker, its flash
DARK_BRIGHT = {'mtl_tod_haven_field_dark': 3.5, 'mtl_tod_haven_field_dark_dim': 1.4, 'mtl_tod_haven_field_dark_flash': 10.0}
TINT1 = '0.85 1 1 1'                 # the safe field's emissive tint (white-cyan; the texture carries the hue)
TINT1_DARK = '1 0.9 0.9 1'           # the corrupted field's (the texture carries the red)

# v5 THE CORRUPTED FIELD IS A DIFFERENT OBJECT (user 2026-10-04: "I like the two states of the dome to be quite
# different"). v3/v4 drew it as the safe lattice in red. Now it is a BREACHED dome on its own mesh: a share of its
# cells are MISSING (ragged holes with glowing edges - a shield that is failing), and every surviving cell wears a
# CRACKED pane from a 2D atlas (DARK_TILES variants): a dark smoky pane that darkens the hall behind it, black-red
# veins branching in from the rim, a fat ragged crimson seam that bulges at the corners. The safe field keeps the
# clean thin radial lattice (field_texture), so the two never read as a recolour of each other.
DARK_MESH_SEED = 20261005
DARK_HOLE_FRACTION = 0.11            # cells breached (never the apex, a pentagon or a cell the floor cuts)
DARK_TEX = 512                       # the atlas (POT, mips on): DARK_TILES tiles of DARK_TEX / 2
DARK_TILES = 4
DARK_SEAM_IN, DARK_SEAM_RAG = 0.395, 0.04     # the seam band's inner edge (tile units: a corner sits at 0.48) and its raggedness
DARK_SEAM_A = (0.42, 0.80)                    # its alpha at the ragged inner edge -> at the corners (LOOK FROM INSIDE: a flat 0.78
                                              # over the band read as a red wall; the glow is the hot lip, not the opacity)   # the seam's inner edge (tile radius, corners at 0.48) and how far the rag wobbles
DARK_PANE_A, DARK_PANE_EDGE_A = 0.085, 0.16  # the pane's alpha at the centre / toward the seam (a dark pane: it dims the hall)
DARK_VEINS = (3, 6)                   # veins per tile (min, max)
DARK_PALETTE = dict(pane=(0.22, 0.015, 0.02), vein=(0.42, 0.03, 0.03), vein_core=(0.95, 0.12, 0.08),
                    seam=(0.80, 0.08, 0.06), seam_hot=(1.00, 0.38, 0.22))
# the two strips' colours (linear-ish, authored by eye against the dome renders)
PALETTES = {
    'safe': dict(haze=(0.08, 0.50, 0.70), glow=(0.40, 0.92, 1.00), core=(0.88, 1.00, 1.00), clear=FIELD_CLEAR),
    'dark': dict(haze=(0.38, 0.03, 0.04), glow=(1.00, 0.16, 0.10), core=(1.00, 0.55, 0.40), clear=0.028),
}

# texture bands (v, top-down): 0 = cell, 1 = lit cell, 2 = core (the apex cell + the base band)
TEX_W, TEX_H, BAND = 256, 128, 32
BANDS = {'cell': 0, 'lit': 1, 'core': 2}

# THE SIGNS
SIGN_W, SIGN_H = 1024, 512           # POT (mips on; the card is seen from 150 to 500 units), 2:1 like the card
SIGN_FLOORS = (10, 20, 30, 40)
SIGN_COLORS = {10: (0.35, 0.55, 1.0), 20: (0.35, 1.0, 0.6), 30: (1.0, 0.6, 0.25), 40: (1.0, 0.85, 0.35)}   # gen_tower_map.js DISTRICTS light colours
SIGN_DARK = (1.0, 0.16, 0.10)        # the corrupted red (make_fx.py DARK_HOT's family)
SIGN_BRIGHT, SIGN_DARK_BRIGHT = 5.0, 3.5   # scaleRGB: the one brightness knob per state
SIGN_SEED = 20261003
LET_CW, LET_CH, LET_BASE, LET_CAP = 80, 112, 104, 90       # TodGlyphMetrics.lua (the sheets' cells)
DIG_CW, DIG_CH, DIG_BASE, DIG_CAP = 128, 160, 152, 138


def band_v(name):
    return (BANDS[name] * BAND + BAND / 2) / TEX_H


# ---------------------------------------------------------------------------
# THE TEXTURE: one strip, u = centre -> rim (one per state)
# ---------------------------------------------------------------------------
def field_texture(palette):
    pal = PALETTES[palette]
    u = (np.arange(TEX_W) + 0.5) / TEX_W
    img = np.zeros((TEX_H, TEX_W, 4), np.float64)
    haze = np.array(pal['haze'])
    glow = np.array(pal['glow'])
    core = np.array(pal['core'])
    # SEE-THROUGH FIRST (the 2026-10-02 review): a player inside must see the horde
    # coming, so a cell is nearly clear, a faint halo hugs its rim and the lattice is a
    # THIN bright line (u = 1 is the cell border; two cells share it, so the drawn line
    # is twice the band). The first cut (interior .045, a halo to .42 from u .60, a
    # solid line from u .905) read from inside as a glowing wall: ~40% of every cell
    # glowed. The corrupted strip is a touch denser (a smoky field) but still clear.
    for name, interior in (('cell', pal['clear']), ('lit', FIELD_LIT), ('core', FIELD_CORE)):
        ramp = np.clip((u - FIELD_HALO_U) / (FIELD_LINE_U - FIELD_HALO_U), 0, 1) ** 2
        t = np.clip((u - FIELD_LINE_U) / (FIELD_LINE_FULL_U - FIELD_LINE_U), 0, 1)
        line = t * t * (3 - 2 * t)
        a = interior + (max(FIELD_HALO_A, interior) - interior) * ramp
        a = a + (FIELD_LINE_A - a) * line
        rgb = haze[None, :] * (1 - ramp[:, None]) + glow[None, :] * ramp[:, None]
        rgb = rgb * (1 - line[:, None]) + core[None, :] * line[:, None]
        if name == 'core':
            rgb = rgb * 0.6 + core[None, :] * 0.4
        b = BANDS[name]
        img[b * BAND:(b + 1) * BAND, :, :3] = rgb[None, :, :]
        img[b * BAND:(b + 1) * BAND, :, 3] = a[None, :]
    # band 3 mirrors band 0 (padding for the mips)
    img[3 * BAND:, :, :] = img[0:BAND, :, :]
    return Image.fromarray(np.clip(np.round(img * 255), 0, 255).astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------------------
# v5 THE CRACKED PANE: a 2D atlas for the corrupted dome's cells
# ---------------------------------------------------------------------------
# Each corrupted cell is UV-mapped onto one tile: its centre at the tile's centre, its
# corners on a circle of radius 0.48 (tile units: half the tile = 0.5). A fan triangle maps
# linearly, so an edge's midpoint lands at radius 0.48 * cos 30 = 0.416 (a pentagon's at
# 0.388): the seam band from DARK_SEAM_IN outward covers the whole geometric rim, wider at
# the corners (corroded joints), its inner edge ragged with angular noise. Veins are
# random walks from the seam inward, drawn dark with a hot core; the pane is a dark smoke.
# RGB = the glow (colorMap00) AND the diffuse (tinted black by the material), alpha = the
# coverage - so a dark vein with real alpha DIMS the hall behind it (the material blends
# a black diffuse over it) while the seam adds light.
def _seg_dist(px, py, ax, ay, bx, by):
    """distance from each pixel to the segment a-b (numpy arrays px, py)"""
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy + 1e-9
    t = np.clip(((px - ax) * vx + (py - ay) * vy) / L2, 0, 1)
    return np.hypot(px - (ax + t * vx), py - (ay + t * vy))


def dark_cell_tile(rng, n):
    """one DARK_TEX/2 x DARK_TEX/2 RGBA tile (float 0..1)"""
    T = DARK_TEX // 2
    ys, xs = np.mgrid[0:T, 0:T].astype(np.float64)
    nx = (xs + 0.5) / T - 0.5
    ny = (ys + 0.5) / T - 0.5
    r = np.hypot(nx, ny)
    ang = (np.arctan2(ny, nx) + np.pi) / (2 * np.pi)             # 0..1 round the cell
    pal = {k: np.array(v) for k, v in DARK_PALETTE.items()}
    rgb = np.zeros((T, T, 3)); a = np.zeros((T, T))
    # the pane: a dark smoke, denser toward the seam, with slow mottling
    mottle = smooth_noise(rng, T, T, 5, 5)
    pane_a = DARK_PANE_A + (DARK_PANE_EDGE_A - DARK_PANE_A) * smoothstep(0.12, 0.42, r)
    pane_a *= 0.75 + 0.5 * mottle
    rgb += pal['pane'][None, None, :] * (0.6 + 0.8 * mottle[..., None])
    a = np.maximum(a, pane_a)
    # the seam: a ragged inner edge (two octaves of angular noise, wrapped), full to the tile's edge
    wob = np.zeros(T * 4)
    for k, (cells, w) in enumerate(((7, 0.65), (19, 0.35))):
        g = rng.random(cells); g = np.concatenate([g, g[:1]])
        xi = np.linspace(0, cells, T * 4, endpoint=False)
        i0 = np.floor(xi).astype(int); f = xi - i0
        f = f * f * (3 - 2 * f)
        wob += w * (g[i0] * (1 - f) + g[i0 + 1] * f)
    seam_in = DARK_SEAM_IN + DARK_SEAM_RAG * (wob[np.clip((ang * T * 4).astype(int), 0, T * 4 - 1)] - 0.5) * 2
    seam = smoothstep(seam_in - 0.012, seam_in + 0.03, r)
    # the seam's alpha grades from DARK_SEAM_A[0] at its ragged inner edge to DARK_SEAM_A[1] at the corners; a HOT LIP
    # (the molten edge of the crust) runs along the inner edge and cools into the dark crust outward
    seam_a = DARK_SEAM_A[0] + (DARK_SEAM_A[1] - DARK_SEAM_A[0]) * smoothstep(seam_in + 0.01, 0.49, r)
    lip = smoothstep(seam_in - 0.012, seam_in + 0.008, r) * (1 - smoothstep(seam_in + 0.012, seam_in + 0.045, r))
    seam_rgb = pal['seam'][None, None, :] * (1 - lip[..., None]) + pal['seam_hot'][None, None, :] * lip[..., None]
    rgb = rgb * (1 - seam[..., None]) + seam_rgb * seam[..., None]
    a = np.maximum(a, seam_a * seam)
    # the veins: random walks from the seam inward, each a chain of short segments
    nv = int(rng.integers(DARK_VEINS[0], DARK_VEINS[1] + 1))
    vein = np.zeros((T, T)); hot = np.zeros((T, T))
    for v in range(nv):
        th = rng.uniform(0, 2 * np.pi)
        rad = seam_in.mean() + 0.02
        px, py = 0.5 + rad * math.cos(th), 0.5 + rad * math.sin(th)
        steps = int(rng.integers(4, 9)); heading = th + math.pi + rng.uniform(-0.5, 0.5)
        width = rng.uniform(0.010, 0.016)
        for s in range(steps):
            ln = rng.uniform(0.035, 0.075)
            qx, qy = px + ln * math.cos(heading), py + ln * math.sin(heading)
            d = _seg_dist(nx + 0.5, ny + 0.5, px, py, qx, qy)
            taper = 1.0 - 0.75 * s / steps
            vein = np.maximum(vein, smoothstep(width * taper, 0.0, d))
            hot = np.maximum(hot, smoothstep(width * taper * 0.45, 0.0, d) * (0.9 - 0.5 * s / steps))
            if rng.random() < 0.3:                                     # a fork
                bh = heading + rng.choice([-1, 1]) * rng.uniform(0.6, 1.2)
                bl = ln * rng.uniform(0.5, 0.9)
                d2 = _seg_dist(nx + 0.5, ny + 0.5, qx, qy, qx + bl * math.cos(bh), qy + bl * math.sin(bh))
                vein = np.maximum(vein, smoothstep(width * taper * 0.7, 0.0, d2))
            px, py = qx, qy
            heading += rng.uniform(-0.7, 0.7)
            if math.hypot(px - 0.5, py - 0.5) < 0.06:
                break
    vein *= smoothstep(0.52, 0.42, r)                                  # veins stop at the seam
    hot *= smoothstep(0.52, 0.42, r)
    rgb = rgb * (1 - vein[..., None]) + pal['vein'][None, None, :] * vein[..., None]
    rgb = rgb * (1 - hot[..., None]) + pal['vein_core'][None, None, :] * hot[..., None]
    a = np.maximum(a, 0.62 * vein)
    # hot spots where the veins meet the seam
    meet = vein * smoothstep(seam_in - 0.06, seam_in + 0.01, r)
    rgb = rgb * (1 - meet[..., None]) + pal['seam_hot'][None, None, :] * meet[..., None]
    a = np.maximum(a, 0.85 * meet)
    # everything past the corner radius is padding the fan never reaches: keep the seam colour there (mips)
    out = r > 0.5
    rgb[out] = pal['seam']; a[out] = DARK_SEAM_A[1]
    return np.concatenate([rgb, a[..., None]], axis=2)


def dark_cell_atlas():
    rng = np.random.default_rng(DARK_MESH_SEED)
    T = DARK_TEX // 2
    img = np.zeros((DARK_TEX, DARK_TEX, 4), np.float64)
    for k in range(DARK_TILES):
        ty, tx = divmod(k, 2)
        img[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T] = dark_cell_tile(rng, k)
    return Image.fromarray(np.clip(np.round(img * 255), 0, 255).astype(np.uint8), 'RGBA')


def dark_tile_uv(k, theta, rho):
    """the atlas UV of a cell point at angle theta (rad) and normalised radius rho (1 = a corner) on tile k"""
    ty, tx = divmod(k, 2)
    u = (tx + 0.5 + 0.48 * rho * math.cos(theta)) / 2
    v = (ty + 0.5 + 0.48 * rho * math.sin(theta)) / 2
    return (round(u, 5), round(v, 5))


# ---------------------------------------------------------------------------
# THE SCREEN VIGNETTE: the field's tint at the edges of the player's screen
# ---------------------------------------------------------------------------
# White RGB (TodHaven.lua tints it with setRGB, so one image serves the steady
# cyan tint, the corrupted red tint AND the white-cyan crossing flash); the shape
# lives in alpha: a rounded-rectangle edge glow, the dome's own hex lattice threaded
# through it (a few cells filled, like the dome's LIT_FRACTION), and a fine scanline.
# The centre of the screen stays clear, so the effect frames the fight instead of
# covering it. 1280x720 = the HUD's virtual canvas 1:1, both sides multiples of 4
# (BC7), NPOT so no mips (the docs/196 rule).
VIG_W, VIG_H = 1280, 720
VIG_HEX = 46.0          # hex cell size in px (centre to corner)
VIG_LINE = 1.7          # lattice line half-width in px
VIG_LIT = 0.09          # fraction of edge cells with a faint fill


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def vignette_texture():
    ys, xs = np.mgrid[0:VIG_H, 0:VIG_W].astype(np.float64)
    nx = (xs + 0.5 - VIG_W / 2) / (VIG_W / 2)
    ny = (ys + 0.5 - VIG_H / 2) / (VIG_H / 2)
    d = (np.abs(nx) ** 3.2 + np.abs(ny) ** 3.2) ** (1 / 3.2)
    base = smoothstep(0.58, 1.12, d) ** 1.6 * 0.55
    band = smoothstep(0.66, 1.05, d)
    # pointy-top hex lattice: axial coordinates, cube-round to the cell, then the
    # distance to the cell's edge from the hexagon's own inradius
    size = VIG_HEX
    cx = (math.sqrt(3) / 3 * xs - 1 / 3 * ys) / size
    cz = (2 / 3 * ys) / size
    cy = -cx - cz
    rx, ry, rz = np.round(cx), np.round(cy), np.round(cz)
    dx, dy, dz = np.abs(rx - cx), np.abs(ry - cy), np.abs(rz - cz)
    fx = (dx > dy) & (dx > dz)
    fy = (~fx) & (dy > dz)
    rx = np.where(fx, -ry - rz, rx)
    rz = np.where(~fx & ~fy, -rx - ry, rz)
    ccx = size * math.sqrt(3) * (rx + rz / 2)
    ccy = size * 1.5 * rz
    px, py = np.abs(xs - ccx), np.abs(ys - ccy)
    inr = size * math.sqrt(3) / 2
    hexd = np.maximum(px, px * 0.5 + py * math.sqrt(3) / 2)
    edge = inr - hexd                     # px inside the cell's edge (0 on the line)
    line = np.clip(1 - np.abs(edge) / VIG_LINE, 0, 1) ** 1.3
    glow = np.exp(-np.clip(edge, 0, None) / 7.0) * 0.35
    lattice = (line * 0.45 + glow * 0.16) * band
    keys = rx.astype(np.int64) * 100003 + rz.astype(np.int64)
    uniq = np.unique(keys)
    rng = np.random.default_rng(SEED)
    lit = uniq[rng.random(uniq.size) < VIG_LIT]
    fill = np.where(np.isin(keys, lit), 0.10, 0.0) * band
    a = np.clip(base + lattice + fill, 0, 0.95)
    a = a * np.where((ys.astype(np.int64) % 3) == 0, 0.80, 1.0)
    img = np.zeros((VIG_H, VIG_W, 4), np.float64)
    img[..., :3] = 1.0
    img[..., 3] = a
    return Image.fromarray(np.clip(np.round(img * 255), 0, 255).astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------------------
# THE DARKNESS (v4): the corrupted field taking over your screen
# ---------------------------------------------------------------------------
# White RGB again (TodHaven.lua tints it near-black and breathes its alpha); the shape
# lives in alpha: a dim centre you can still fight through (DARK_CENTRE), heavy edges
# (DARK_EDGE) and smoky tendrils creeping in from them (smooth value noise in polar
# coordinates, so the smoke streams toward the centre). 1280x720 = the HUD canvas 1:1,
# multiples of 4 (BC7), NPOT so no mips.
DARK_CENTRE, DARK_EDGE, DARK_MAX = 0.17, 0.80, 0.93
DARK_SEED = 20261004


def smooth_noise(rng, h, w, gh, gw):
    """value noise: a gh x gw random grid, bicubic-upsampled to h x w (0..1)."""
    g = rng.random((gh, gw)).astype(np.float32)
    return np.array(Image.fromarray(g, 'F').resize((w, h), Image.BICUBIC)).astype(np.float64)


def dark_texture():
    rng = np.random.default_rng(DARK_SEED)
    ys, xs = np.mgrid[0:VIG_H, 0:VIG_W].astype(np.float64)
    nx = (xs + 0.5 - VIG_W / 2) / (VIG_W / 2)
    ny = (ys + 0.5 - VIG_H / 2) / (VIG_H / 2)
    d = (np.abs(nx) ** 2.6 + np.abs(ny) ** 2.6) ** (1 / 2.6)
    # the smoke: three octaves of noise on (angle, radius) - an angular period that wraps
    ang = (np.arctan2(ny * VIG_H, nx * VIG_W) + np.pi) / (2 * np.pi)          # 0..1 round the screen
    smoke = np.zeros_like(d)
    for k, (ga, gr, wgt) in enumerate(((24, 6, 0.55), (60, 12, 0.30), (140, 24, 0.15))):
        grid = smooth_noise(rng, 256, 512, gr, ga)                               # rows = radius, cols = angle
        grid = np.concatenate([grid, grid[:, :1]], axis=1)                       # wrap the angle seam
        ci = np.clip(ang * 512, 0, 511.999)
        ri = np.clip(d / 1.6 * 255 + 30 * k, 0, 255.999)
        c0, r0 = ci.astype(int), ri.astype(int)
        smoke += wgt * grid[r0, c0]
    # the reach of the dark: it creeps further in where the smoke is thick
    reach = 0.42 - 0.22 * (smoke - 0.5)
    body = smoothstep(reach, reach + 0.72, d) ** 1.35
    a = DARK_CENTRE + (DARK_EDGE - DARK_CENTRE) * body
    a += 0.16 * smoothstep(0.55, 1.10, d) * (smoke - 0.45)                       # wisps over the edge band
    a = np.clip(a, 0, DARK_MAX)
    img = np.zeros((VIG_H, VIG_W, 4), np.float64)
    img[..., :3] = 1.0
    img[..., 3] = a
    return Image.fromarray(np.clip(np.round(img * 255), 0, 255).astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------------------
# THE BARRIER MATERIAL (v4): the stock weapon clip + missile clip + no penetration
# ---------------------------------------------------------------------------
def barrier_material_block():
    """the donor's whole block from the tools' clip GDT, renamed, with BARRIER_OVERRIDES. Refuses a donor
    whose collision flags are not the weapon clip's (bullets only, nonsolid to players and AI)."""
    import re
    text = CLIP_GDT.read_text(encoding='utf-8', errors='replace')
    m = re.search(r'\n\t"' + CLIP_DONOR + r'" \( "material\.gdf" \)\s*\{\n(.*?)\n\t\}', text, re.S)
    if not m:
        raise SystemExit('haven barrier: the donor %s is missing from %s' % (CLIP_DONOR, CLIP_GDT))
    rows = re.findall(r'^\t\t"(\w+)" "([^"]*)"$', m.group(1), re.M)
    d = dict(rows)
    want = {'bulletClip': '1', 'nonSolid': '1', 'playerClip': '0', 'aiClip': '0', 'vehicleClip': '0', 'noDraw': '1',
            'noImpact': '1', 'materialType': 'tools_blend', 'usage': 'clip', 'missileClip': '0', 'noPenetrate': '0'}
    bad = {k: d.get(k) for k, v in want.items() if d.get(k) != v}
    if bad or len(rows) < 800:
        raise SystemExit('haven barrier: the donor %s changed shape: %r (%d fields)' % (CLIP_DONOR, bad, len(rows)))
    out = dict(rows)
    out.update(BARRIER_OVERRIDES)
    return out


# ---------------------------------------------------------------------------
# THE FLOOR SIGNS: FLOOR N from the glyph sheets, recoloured, glowing, scanned
# ---------------------------------------------------------------------------
_SHEET = {}


def sheet(name):
    if name not in _SHEET:
        _SHEET[name] = np.array(Image.open(SHEETS / (name + '.png')).convert('RGBA')).astype(np.float64) / 255
    return _SHEET[name]


def glyph(ch):
    """-> (the glyph's RGBA cell trimmed to its ink columns, its baseline, its cap height) from the sheets."""
    if ch.isdigit():
        d = sheet('i_tod_hud_digits')
        g = d[0:DIG_CH, int(ch) * DIG_CW:(int(ch) + 1) * DIG_CW]; base, cap = DIG_BASE, DIG_CAP
    else:
        i = ord(ch) - 97
        d = sheet('i_tod_hud_letters')
        g = d[(i // 15) * LET_CH:(i // 15 + 1) * LET_CH, (i % 15) * LET_CW:(i % 15 + 1) * LET_CW]; base, cap = LET_BASE, LET_CAP
    cols = np.where(g[..., 3].max(axis=0) > 0.1)[0]
    return g[:, cols.min():cols.max() + 1], base, cap


def resize_rgba(g, scale):
    """premultiplied LANCZOS resize of a float RGBA array (no dark fringes)."""
    h, w = g.shape[:2]
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    pre = g.copy(); pre[..., :3] *= pre[..., 3:4]
    chans = [np.array(Image.fromarray(pre[..., c].astype(np.float32), 'F').resize((nw, nh), Image.LANCZOS)) for c in range(4)]
    out = np.stack(chans, axis=-1).astype(np.float64)
    a = out[..., 3:4]
    out[..., :3] = np.where(a > 1e-4, out[..., :3] / np.maximum(a, 1e-4), 0)
    return np.clip(out, 0, 1)


def place(canvas, g, x, y):
    h, w = g.shape[:2]
    H, W = canvas.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    x1, y1 = min(W, x0 + w), min(H, y0 + h)
    if x0 < 0 or y0 < 0 or x1 <= x0 or y1 <= y0:
        raise ValueError('sign glyph off the canvas')
    src = g[:y1 - y0, :x1 - x0]
    dst = canvas[y0:y1, x0:x1]
    a = src[..., 3:4]
    dst[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a)
    dst[..., 3:4] = a + dst[..., 3:4] * (1 - a)


def word(canvas, text, cap_px, baseline_y, gap_px, cx=SIGN_W / 2):
    glyphs = [glyph(c) for c in text]
    scale = cap_px / glyphs[0][2]
    sized = [(resize_rgba(g, scale), base * scale) for g, base, cap in glyphs]
    total = sum(s.shape[1] for s, _ in sized) + gap_px * (len(sized) - 1)
    x = cx - total / 2
    for s, base in sized:
        place(canvas, s, x, baseline_y - base)
        x += s.shape[1] + gap_px


def recolour(canvas, tint, dark):
    """The sheets' pale face / blue-grey extrusion / navy outline -> the tint by luminance, so the 3D read survives."""
    rgb, a = canvas[..., :3], canvas[..., 3]
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    k = (0.06 + 0.94 * lum ** 1.35) if dark else (0.10 + 0.90 * lum ** 1.15)
    out = np.zeros_like(canvas)
    out[..., :3] = np.array(tint)[None, None, :] * k[..., None]
    out[..., 3] = a
    return out


def rule(canvas, tint, y0, y1, x0, x1, alpha):
    xs = np.arange(x0, x1)
    fade = np.clip(np.minimum(xs - x0, x1 - 1 - xs) / 60.0, 0, 1)
    canvas[y0:y1, x0:x1, :3] = np.array(tint)[None, None, :]
    canvas[y0:y1, x0:x1, 3] = np.maximum(canvas[y0:y1, x0:x1, 3], (alpha * fade)[None, :])


def finish(canvas, tint, dark, rng):
    """a soft glow under the glyphs, a fine scanline; the corrupted sign gets glitch slices (an unstable lamp)."""
    a8 = Image.fromarray((canvas[..., 3] * 255).astype(np.uint8), 'L')
    glow = np.array(a8.filter(ImageFilter.GaussianBlur(12))).astype(np.float64) / 255 * (0.4 if dark else 0.55)
    a = canvas[..., 3]
    rgb = canvas[..., :3] * a[..., None] + np.array(tint)[None, None, :] * (glow * (1 - a))[..., None]
    alpha = np.maximum(a, glow * 0.75)
    rgb = np.where(alpha[..., None] > 1e-4, rgb / np.maximum(alpha[..., None], 1e-4), 0)
    out = np.concatenate([rgb, alpha[..., None]], axis=-1)
    ys = np.arange(SIGN_H)[:, None]
    out[..., 3] *= np.where(ys % 4 == 0, 0.86, 1.0)
    if dark:
        for _ in range(6):
            y0 = int(rng.integers(40, SIGN_H - 30)); h = int(rng.integers(5, 14)); dx = int(rng.integers(5, 16)) * (1 if rng.random() < 0.5 else -1)
            out[y0:y0 + h] = np.roll(out[y0:y0 + h], dx, axis=1)
            out[y0:y0 + h, :, 3] *= float(rng.uniform(0.55, 0.9))
    return np.clip(out, 0, 1)


def sign_texture(floor, dark):
    rng = np.random.default_rng(SIGN_SEED + floor + (100 if dark else 0))
    canvas = np.zeros((SIGN_H, SIGN_W, 4))
    word(canvas, 'floor', 76, 124, 7)
    word(canvas, str(floor), 290, 470, 14)
    tint = SIGN_DARK if dark else SIGN_COLORS[floor]
    canvas = recolour(canvas, tint, dark)
    rule(canvas, tint, 138, 142, 262, 762, 0.85)
    img = finish(canvas, tint, dark, rng)
    return Image.fromarray(np.clip(np.round(img * 255), 0, 255).astype(np.uint8), 'RGBA')


def sign_image_name(floor, dark):
    return 'i_tod_haven_sign_%d%s' % (floor, '_dark' if dark else '')


def sign_material_name(floor, dark):
    return 'mtl_tod_haven_sign_%d%s' % (floor, '_dark' if dark else '')


def sign_model_name(floor, dark):
    return 'tod_haven_sign_%d%s' % (floor, '_dark' if dark else '')


SIGN_BASE_MATERIAL = sign_material_name(40, False)   # the one material in the exported quad; the others ride skinOverride


def build_sign_model():
    """the card as a PyCoD model: one bone, one material, two triangles wound for BO3's front face (+X)."""
    m = xmodel.Model('tod_haven_sign')
    bone = xmodel.Bone('tag_origin'); bone.offset = (0, 0, 0); bone.matrix = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    m.bones = [bone]
    m.materials = [xmodel.Material(SIGN_BASE_MATERIAL, 'Phong', {})]
    mesh = xmodel.Mesh('sign_card')
    hw, hh = SIGN_W_U / 2, SIGN_H_U / 2
    # corners: top-left, top-right, bottom-right, bottom-left (in the camera's view; +Y = its right, +Z = up)
    corners = [(0.0, -hw, hh), (0.0, hw, hh), (0.0, hw, -hh), (0.0, -hw, -hh)]
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    mesh.verts = [xmodel.Vertex(c, [(0, 1.0)]) for c in corners]
    # Seen from +X (the camera), with +Y to the right and +Z up, top-left -> top-right -> bottom-right runs CLOCKWISE:
    # that is BO3's front face (tools/jump_title/make_sign_card.py, the lit sign card).
    for tri in ((0, 1, 2), (0, 2, 3)):
        f = xmodel.Face(0, 0)
        f.indices = [xmodel.FaceVertex(i, (1.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0), uvs[i]) for i in tri]
        mesh.faces.append(f)
    m.meshes.append(mesh)
    return m


# ---------------------------------------------------------------------------
# THE GOLDBERG DOME
# ---------------------------------------------------------------------------
def icosahedron():
    t = (1 + 5 ** 0.5) / 2
    v = np.array([[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t],
                  [0, -1, -t], [0, 1, -t], [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], float)
    f = [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2],
         [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5],
         [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]]
    v /= np.linalg.norm(v, axis=1)[:, None]
    # rotate so vertex 0 points straight up: the apex is a pentagon cell centre
    a = v[0]; z = np.array([0, 0, 1.0])
    axis = np.cross(a, z); s = np.linalg.norm(axis); c = float(np.dot(a, z))
    axis /= s
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    Rm = np.eye(3) + K * s + K @ K * (1 - c)
    return (Rm @ v.T).T, f


def geodesic(freq):
    v0, faces = icosahedron()
    verts, index, tris = [], {}, []

    def vid(p):
        key = tuple(np.round(p / np.linalg.norm(p), 9))
        if key not in index:
            index[key] = len(verts); verts.append(np.array(key))
        return index[key]

    for a, b, c in faces:
        A, B, C = v0[a], v0[b], v0[c]
        grid = {}
        for i in range(freq + 1):
            for j in range(freq + 1 - i):
                k = freq - i - j
                grid[(i, j)] = vid((A * i + B * j + C * k) / freq)
        for i in range(freq):
            for j in range(freq - i):
                tris.append((grid[(i, j)], grid[(i + 1, j)], grid[(i, j + 1)]))
                if i + j < freq - 1:
                    tris.append((grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]))
    return np.array(verts), tris


def goldberg(freq):
    """-> list of cells: (centre unit vector, [corner unit vectors in CCW order])."""
    verts, tris = geodesic(freq)
    cent = []
    around = [[] for _ in verts]
    for ti, (a, b, c) in enumerate(tris):
        m = verts[a] + verts[b] + verts[c]; m /= np.linalg.norm(m)
        cent.append(m)
        for x in (a, b, c):
            around[x].append(ti)
    cells = []
    for vi, ts in enumerate(around):
        n = verts[vi]
        e1 = np.cross(n, [0, 0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0, 0]); e1 /= np.linalg.norm(e1)
        e2 = np.cross(n, e1)
        pts = [cent[t] for t in ts]
        pts.sort(key=lambda p: math.atan2(np.dot(p - n, e2), np.dot(p - n, e1)))
        cells.append((n, pts))
    return cells


def clip_floor(poly, zmin):
    """Sutherland-Hodgman against z >= zmin; poly = list of 3D points."""
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        pin, qin = p[2] >= zmin, q[2] >= zmin
        if pin:
            out.append(p)
        if pin != qin:
            t = (zmin - p[2]) / (q[2] - p[2])
            out.append(p + (q - p) * t)
    return out


def dome_mesh(freq, dark=False):
    """-> (triangles, holes). The SAFE mesh: every cell a radial-strip fan. The CORRUPTED mesh (v5, dark=True):
    DARK_HOLE_FRACTION of the whole cells breached (skipped), the rest mapped onto the cracked-pane atlas."""
    rng = np.random.default_rng((DARK_MESH_SEED if dark else SEED) + freq)
    cells = goldberg(freq)
    world = lambda u: np.array([u[0] * S, u[1] * S, u[2] * S + CZ])
    tris = []          # (p0, p1, p2, uv0, uv1, uv2)
    holes = 0
    apex = max(range(len(cells)), key=lambda i: cells[i][0][2])
    for ci, (n, corners) in enumerate(cells):
        poly = [world(c) for c in corners]
        if max(p[2] for p in poly) <= 0.5:
            continue
        clipped = clip_floor(poly, 0.0)
        if len(clipped) < 3:
            continue
        centre = world(n)
        whole = min(p[2] for p in poly) > 0.5
        if centre[2] < 0.5:                       # a cell the floor cuts: fan from the clipped centroid
            centre = np.mean(clipped, axis=0)
            centre[2] = max(centre[2], 0.5)
        if dark:
            # a breach: a whole hexagon off the floor, never the apex (the crown must read) - the hole's
            # neighbours still draw their seams, so every breach has a ragged glowing edge
            if whole and ci != apex and len(corners) == 6 and rng.random() < DARK_HOLE_FRACTION:
                holes += 1
                continue
            tile = int(rng.integers(DARK_TILES))
            e1 = np.cross(n, [0, 0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0, 0]); e1 /= np.linalg.norm(e1)
            e2 = np.cross(n, e1)
            cmax = max(np.linalg.norm(p - centre) for p in poly) + 1e-6
            uv_of = lambda p: dark_tile_uv(tile, math.atan2(float(np.dot(p - centre, e2)), float(np.dot(p - centre, e1))),
                                          min(1.0, float(np.linalg.norm(p - centre)) / cmax))
            uvc = dark_tile_uv(tile, 0.0, 0.0)
            for i in range(len(clipped)):
                a, b = clipped[i], clipped[(i + 1) % len(clipped)]
                if np.linalg.norm(np.cross(a - centre, b - centre)) < 1e-3:
                    continue
                tris.append((centre, a, b, uvc, uv_of(a), uv_of(b)))
            continue
        band = 'core' if ci == apex else ('lit' if rng.random() < LIT_FRACTION else 'cell')
        v = band_v(band)
        for i in range(len(clipped)):
            a, b = clipped[i], clipped[(i + 1) % len(clipped)]
            if np.linalg.norm(np.cross(a - centre, b - centre)) < 1e-3:
                continue
            tris.append((centre, a, b, (0.02, v), (1.0, v - 0.04), (1.0, v + 0.04)))
    # the base band: a short bright skirt at the floor ring (0 .. 7 units), u = 1 at the floor
    # (the corrupted skirt wears the atlas's seam band: tile 0, the corner radius at the floor, 90% of it at its top)
    seg = 64
    vb = band_v('core')
    for i in range(seg):
        t0, t1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        p0 = np.array([R * math.cos(t0), R * math.sin(t0), 0.25]); p1 = np.array([R * math.cos(t1), R * math.sin(t1), 0.25])
        q0 = np.array([R * math.cos(t0) * 0.995, R * math.sin(t0) * 0.995, 7.0]); q1 = np.array([R * math.cos(t1) * 0.995, R * math.sin(t1) * 0.995, 7.0])
        if dark:
            f0, f1 = dark_tile_uv(0, t0, 1.0), dark_tile_uv(0, t1, 1.0)
            g0, g1 = dark_tile_uv(0, t0, 0.9), dark_tile_uv(0, t1, 0.9)
            tris.append((p0, p1, q1, f0, f1, g1))
            tris.append((p0, q1, q0, f0, g1, g0))
            continue
        tris.append((p0, p1, q1, (1.0, vb), (1.0, vb), (0.55, vb)))
        tris.append((p0, q1, q0, (1.0, vb), (0.55, vb), (0.55, vb)))
    return tris, holes


def build_model(freq, dark=False):
    tris, holes = dome_mesh(freq, dark)
    m = xmodel.Model('tod_haven_dome_dark' if dark else 'tod_haven_dome')
    bone = xmodel.Bone('tag_origin'); bone.offset = (0, 0, 0); bone.matrix = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    m.bones = [bone]
    m.materials = [xmodel.Material('mtl_tod_haven_field_dark' if dark else 'mtl_tod_haven_field', 'Phong', {})]
    for shell, flip in (('outer', False), ('inner', True)):
        mesh = xmodel.Mesh('field_' + shell)
        for (p0, p1, p2, t0, t1, t2) in tris:
            nrm = np.cross(p1 - p0, p2 - p0)
            ln = np.linalg.norm(nrm)
            if ln < 1e-6:
                continue
            nrm = nrm / ln
            # outward = away from the sphere centre
            mid = (p0 + p1 + p2) / 3 - np.array([0, 0, CZ])
            if np.dot(nrm, mid) < 0:
                p1, p2, t1, t2 = p2, p1, t2, t1
                nrm = -nrm
            if flip:
                p1, p2, t1, t2 = p2, p1, t2, t1
                nrm = -nrm
            base = len(mesh.verts)
            for p in (p0, p1, p2):
                mesh.verts.append(xmodel.Vertex(tuple(round(float(x), 4) for x in p), [(0, 1.0)]))
            f = xmodel.Face(len(m.meshes), 0)
            # PyCoD winding: the corner order the shipping exporters use ([0, 2, 1])
            f.indices = [xmodel.FaceVertex(base + k, tuple(round(float(x), 5) for x in nrm), (1, 1, 1, 1), uv)
                         for k, uv in ((0, t0), (2, t2), (1, t1))]
            mesh.faces.append(f)
        m.meshes.append(mesh)
    return m, sum(len(x.faces) for x in m.meshes), holes


# ---------------------------------------------------------------------------
# outputs
# ---------------------------------------------------------------------------
def block(name, kind, fields):
    return '\t"' + name + '" ( "' + kind + '.gdf" )\n\t{\n' + ''.join(
        '\t\t"' + k + '" "' + str(v) + '"\n' for k, v in fields.items()) + '\t}\n'


def emissive_card(image, scale, tint1):
    """the lit sign card recipe: alpha = visibility, no lit diffuse, the image as the glow"""
    return dict(
        surfaceType='<none>', template='material.template', materialCategory='Geometry',
        materialType='lit_emissive_transparent', colorMap=image, colorTint='0 0 0 1',
        normalMap='$identitynormalmap', colorMap00=image, colorTint1=tint1, scaleRGB=scale,
        emissiveIncompetence='1', emissiveFalloff='0', glossRangeMin='0', glossRangeMax='8', specAmount='0',
        reflectionProbeAmount='0', textureAtlasRowCount='1', textureAtlasColumnCount='1', usage='<not in editor>')


def gdt_text():
    out = ['{\n']
    for img in ('i_tod_haven_field', 'i_tod_haven_field_dark'):
        out.append(block(img, 'image', dict(
            baseImage='model_export/tod_haven/_images/' + img + '.png', imageType='Texture', type='image',
            semantic='diffuseMap', coreSemantic='sRGB3chAlpha', streamable='1', compressionMethod='compressed high color')))
    for name, scale in BRIGHT.items():
        out.append(block(name, 'material', emissive_card('i_tod_haven_field', scale, TINT1)))
    for name, scale in DARK_BRIGHT.items():
        out.append(block(name, 'material', emissive_card('i_tod_haven_field_dark', scale, TINT1_DARK)))
    base = dict(filename='tod_haven/tod_haven_dome_lod0.xmodel_bin', mediumLod='tod_haven/tod_haven_dome_lod1.xmodel_bin',
                mediumLodDist=str(LODS[1][1]), type='rigid', scale='1', CollisionMap='', BulletCollisionLOD='None',
                physicsPreset='', cullOutDiameter='0', noCastShadow='1', materials='')
    out.append(block('tod_haven_dome', 'xmodel', base))
    for suffix in ('pulse', 'flash'):
        f = dict(base); f['skinOverride'] = 'mtl_tod_haven_field mtl_tod_haven_field_' + suffix
        out.append(block('tod_haven_dome_' + suffix, 'xmodel', f))
    # v5: the CORRUPTED dome is its own breached mesh (its base material baked in); its dim + flash twins ride skinOverride
    dark_base = dict(base, filename='tod_haven/tod_haven_dome_dark_lod0.xmodel_bin', mediumLod='tod_haven/tod_haven_dome_dark_lod1.xmodel_bin')
    out.append(block('tod_haven_dome_dark', 'xmodel', dark_base))
    for suffix in ('dark_dim', 'dark_flash'):
        f = dict(dark_base); f['skinOverride'] = 'mtl_tod_haven_field_dark mtl_tod_haven_field_' + suffix
        out.append(block('tod_haven_dome_' + suffix, 'xmodel', f))
    # THE FLOOR SIGNS: eight images, eight materials, one quad, eight models
    for dark in (False, True):
        for floor in SIGN_FLOORS:
            out.append(block(sign_image_name(floor, dark), 'image', dict(
                baseImage='model_export/tod_haven/_images/' + sign_image_name(floor, dark) + '.png', imageType='Texture', type='image',
                semantic='diffuseMap', coreSemantic='sRGB3chAlpha', streamable='1', clampU='1', clampV='1',
                compressionMethod='compressed high color')))
    for dark in (False, True):
        for floor in SIGN_FLOORS:
            out.append(block(sign_material_name(floor, dark), 'material',
                             emissive_card(sign_image_name(floor, dark), SIGN_DARK_BRIGHT if dark else SIGN_BRIGHT, '1 1 1 1')))
    sign_base = dict(filename='tod_haven/tod_haven_sign.xmodel_bin', type='rigid', scale='1', CollisionMap='', BulletCollisionLOD='None',
                     physicsPreset='', cullOutDiameter='0', noCastShadow='1', materials='')
    for dark in (False, True):
        for floor in SIGN_FLOORS:
            f = dict(sign_base)
            mat = sign_material_name(floor, dark)
            if mat != SIGN_BASE_MATERIAL:
                f['skinOverride'] = SIGN_BASE_MATERIAL + ' ' + mat
            out.append(block(sign_model_name(floor, dark), 'xmodel', f))
    out.append(block('i_tod_haven_vignette', 'image', dict(
        baseImage='model_export/tod_haven/_images/i_tod_haven_vignette.png', imageType='Texture', type='image',
        semantic='diffuseMap', coreSemantic='sRGB3chAlpha', colorSRGB='1', streamable='1', noMipMaps='1', noPicMip='1',
        clampU='1', clampV='1', compressionMethod='compressed high color')))
    # v4: the darkness veil (the HUD, like the vignette) and the barrier's tools material (the map's brushes)
    out.append(block('i_tod_haven_darkness', 'image', dict(
        baseImage='model_export/tod_haven/_images/i_tod_haven_darkness.png', imageType='Texture', type='image',
        semantic='diffuseMap', coreSemantic='sRGB3chAlpha', colorSRGB='1', streamable='1', noMipMaps='1', noPicMip='1',
        clampU='1', clampV='1', compressionMethod='compressed high color')))
    out.append(block(BARRIER_MATERIAL, 'material', barrier_material_block()))
    out.append('}\n')
    return ''.join(out)


def png_bytes(img):
    buf = io.BytesIO(); img.save(buf, 'PNG', optimize=False); return buf.getvalue()


def render():
    files = {}
    files[IMG / 'i_tod_haven_field.png'] = png_bytes(field_texture('safe'))
    files[IMG / 'i_tod_haven_field_dark.png'] = png_bytes(dark_cell_atlas())   # v5: the cracked-pane atlas (was the red strip)
    files[IMG / 'i_tod_haven_vignette.png'] = png_bytes(vignette_texture())
    files[IMG / 'i_tod_haven_darkness.png'] = png_bytes(dark_texture())
    for dark in (False, True):
        for floor in SIGN_FLOORS:
            files[IMG / (sign_image_name(floor, dark) + '.png')] = png_bytes(sign_texture(floor, dark))
    tris, dark_tris, dark_holes = {}, {}, {}
    EXP.mkdir(parents=True, exist_ok=True)
    for lod, (freq, _) in enumerate(LODS):
        model, n, _ = build_model(freq)
        tmp = EXP / f'.tmp_lod{lod}.xmodel_bin'
        model.WriteFile_Bin(str(tmp), version=7)
        files[EXP / f'tod_haven_dome_lod{lod}.xmodel_bin'] = tmp.read_bytes(); tmp.unlink()
        tris[lod] = n
        model, n, holes = build_model(freq, dark=True)                        # v5: the breached corrupted mesh
        tmp = EXP / f'.tmp_dark_lod{lod}.xmodel_bin'
        model.WriteFile_Bin(str(tmp), version=7)
        files[EXP / f'tod_haven_dome_dark_lod{lod}.xmodel_bin'] = tmp.read_bytes(); tmp.unlink()
        dark_tris[lod] = n; dark_holes[lod] = holes
    tmp = EXP / '.tmp_sign.xmodel_bin'
    build_sign_model().WriteFile_Bin(str(tmp), version=7)
    files[EXP / 'tod_haven_sign.xmodel_bin'] = tmp.read_bytes(); tmp.unlink()
    files[GDT_STAGED] = gdt_text().encode('utf-8')
    if GDT.exists():                       # wired (tools/haven/wire.py ran): the live GDT is the staged one
        files[GDT] = files[GDT_STAGED]
    manifest = dict(asset='tod_haven_dome', field=dict(R=R, centre_above_floor=CZ, sphere_r=round(S, 4), top=round(LAYOUT['TOP'], 3)),
                    lods=[dict(lod=i, frequency=f, switch=d, triangles=tris[i]) for i, (f, d) in enumerate(LODS)],
                    dark_lods=[dict(lod=i, frequency=f, switch=d, triangles=dark_tris[i], holes=dark_holes[i]) for i, (f, d) in enumerate(LODS)],
                    dark=dict(hole_fraction=DARK_HOLE_FRACTION, tiles=DARK_TILES, texture=[DARK_TEX, DARK_TEX], seam_in=DARK_SEAM_IN),
                    materials=dict(BRIGHT, **DARK_BRIGHT), texture=[TEX_W, TEX_H],
                    states=dict(safe=['tod_haven_dome', 'tod_haven_dome_pulse', 'tod_haven_dome_flash'],
                                corrupted=['tod_haven_dome_dark', 'tod_haven_dome_dark_dim', 'tod_haven_dome_dark_flash']),
                    signs=dict(card=[SIGN_W_U, SIGN_H_U], texture=[SIGN_W, SIGN_H], scale_rgb=dict(safe=SIGN_BRIGHT, dark=SIGN_DARK_BRIGHT),
                               models=[sign_model_name(f, d) for d in (False, True) for f in SIGN_FLOORS]),
                    darkness=dict(image='i_tod_haven_darkness', size=[VIG_W, VIG_H], centre=DARK_CENTRE, edge=DARK_EDGE, max=DARK_MAX),
                    barrier=dict(material=BARRIER_MATERIAL, donor=CLIP_DONOR, overrides=BARRIER_OVERRIDES),
                    sha256={p.relative_to(ROOT).as_posix(): hashlib.sha256(b).hexdigest() for p, b in files.items()})
    files[MANIFEST] = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    return files, manifest


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--check', action='store_true'); a = ap.parse_args()
    files, manifest = render()
    if a.check:
        bad = [p for p, b in files.items() if not p.exists() or p.read_bytes() != b]
        if GDT.exists() and GDT.read_bytes() != files[GDT_STAGED]:
            bad.append(GDT)
        for p in bad:
            print('STALE', p.relative_to(ROOT))
        print('HAVEN DOME --check:', 'OK' if not bad else f'{len(bad)} stale')
        sys.exit(1 if bad else 0)
    for p, b in files.items():
        p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b)
        print('wrote', p.relative_to(ROOT), len(b), 'B')
    print('HAVEN DOME:', json.dumps(manifest['lods']), 'dark:', json.dumps(manifest['dark_lods']), 'signs:', len(manifest['signs']['models']))


if __name__ == '__main__':
    main()
