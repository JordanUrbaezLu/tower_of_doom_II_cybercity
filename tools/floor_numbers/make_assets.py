#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# tools/floor_numbers/make_assets.py - THE FLOOR NUMBERS' art and materials
# (2026-10-04, docs/208; user: "Map one made some changes to adding numbers to
# each floor. Lets add that too but we go down instead of up so we should add in
# a spot that makes more sense as players go down").
#
# Ported from map 1's tools/gen_tod_refresh_assets.py (v19.69, the floor-number
# half only - map 1's lit risers / dark soffits do not apply: this tower wears
# the crown kit and the blackout). Two differences from map 1:
#   * the digits are THIS map's own HUD face (the 2026-09-29 legibility face,
#     source_data/tod_ui_images/_sheets/i_tod_hud_digits.png), not map 1's;
#   * the tints are THIS map's district colours (gen_tower_map.js DISTRICTS
#     `light`, the same colours the havens and the power wave use) - --check
#     reads them back out of the generator and fails on any drift.
#
# Writes (and with --check, re-derives in memory and FAILS if disk differs):
#   source_data/tod_floornum/_images/i_tod_floornum.png   the atlas: the ten
#       digits' white FILL only (outline and 3-D extrusion stripped), 10 cells of
#       192 x 256 in a 2048 x 256 RGBA strip (alpha = the glyph + a faint glow
#       skirt). Power-of-two and a multiple of 4 both ways (compressed images).
#   source_data/tod_floornum.gdt   one image block + five materials
#       tod_floornum_<blue|green|orange|yellow|red>: CLONES of the DOGCANARY
#       chalk-mesh decal arrow_power_coldwar1 (lit_emissive_scroll_transparent,
#       usage decal - the recipe this map's POWER decals already ship) with this
#       atlas, the district tint and ONE brightness knob (FLOORNUM_SCALE).
# World materials ride in through the compiled BSP: NO zone line. A .map change
# (the decals) is a FULL build.
#
# Usage: python tools/floor_numbers/make_assets.py           (write)
#        python tools/floor_numbers/make_assets.py --check   (build gate)
# -----------------------------------------------------------------------------
import argparse
import io
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# The PRIVATE Tower II tools root (docs/154): the decal donor GDT is read from it, never written.
MODTOOLS = os.environ.get('TOD2_MODTOOLS', r'C:\BO3Tools\TOD2Cybercity')
IMG_DIR = os.path.join(REPO, 'source_data', 'tod_floornum', '_images')
IMG_NAME = 'i_tod_floornum.png'
GDT_OUT = os.path.join(REPO, 'source_data', 'tod_floornum.gdt')
GENERATOR = os.path.join(REPO, 'tools', 'gen_tower_map.js')
DIGITS_SHEET = os.path.join(REPO, 'source_data', 'tod_ui_images', '_sheets', 'i_tod_hud_digits.png')
DECAL_GDT = os.path.join(MODTOOLS, 'model_export', 'codimages', 'arrow_coldwar_dogcanary', 'arrow_power_coldwar_dogcanary.gdt')
TEMPLATE_DECAL = (DECAL_GDT, 'arrow_power_coldwar1')
TEMPLATE_DECAL_IMG = (DECAL_GDT, 'i_arrow_power_coldwar1_c1')
IMAGE_ASSET = 'i_tod_floornum_c'

# THE DISTRICTS, LOCKSTEP with gen_tower_map.js DISTRICTS[].light (checked by --check).
DISTRICT_TINT = {
    'blue':   (0.35, 0.55, 1.0),
    'green':  (0.35, 1.0, 0.6),
    'orange': (1.0, 0.6, 0.25),
    'yellow': (1.0, 0.85, 0.35),
    'red':    (1.0, 0.3, 0.3),
}
# A numeral reads paler than a stripe of the same hue: lift each tint 30% toward
# white (map 1's rule), so a "4" is legible on its own district's rail colour.
TINT_LIFT = 0.30
# THE ONE BRIGHTNESS KNOB. Map 1 ran 8 on its glowing vertigo tower; this tower is
# the darker crown kit under powered stair pools, so the same digit at 8 would read
# as a lamp. 6 = a lit sign, not a floodlight (the v17.82 / v18.97 glare calls).
FLOORNUM_SCALE = 6.0

# --- the atlas ------------------------------------------------------------------
CELL_W, CELL_H, ATLAS_W, ATLAS_H = 192, 256, 2048, 256
SHEET_CW, SHEET_CH = 128, 160          # slice_hud_sheets.js digits: cw 128, ch 160, 13 columns (0-9 / + -)
GLYPH_SCALE = 1.18                     # map 1's: the glyph fills ~74% of the cell height
PAD = 18                               # past the ink, so the halo blur is never cut at the ink's box


def floornum_image():
    sheet = np.asarray(Image.open(DIGITS_SHEET).convert('RGBA')).astype(np.float32) / 255.0
    if sheet.shape[1] < 10 * SHEET_CW or sheet.shape[0] < SHEET_CH:
        sys.exit(f'{DIGITS_SHEET}: {sheet.shape[1]}x{sheet.shape[0]} is not the 13 x {SHEET_CW} x {SHEET_CH} digit sheet')
    atlas = np.zeros((ATLAS_H, ATLAS_W, 4), np.float32)
    for d in range(10):
        cell = sheet[:SHEET_CH, d * SHEET_CW:(d + 1) * SHEET_CW]
        r, g, b, a = cell[..., 0], cell[..., 1], cell[..., 2], cell[..., 3]
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        sat = cell[..., :3].max(axis=2) - cell[..., :3].min(axis=2)
        # The face's FILL is near-white and unsaturated; its 3-D extrusion is a
        # saturated blue and its outline near-black - keep the fill only.
        fill = np.clip((lum - 0.62) / 0.18, 0, 1) * np.clip((0.30 - sat) / 0.12, 0, 1) * a
        im = Image.fromarray((fill * 255).astype(np.uint8), 'L')
        im = im.resize((int(SHEET_CW * GLYPH_SCALE), int(SHEET_CH * GLYPH_SCALE)), Image.LANCZOS)
        bbox = im.getbbox()
        if not bbox:
            sys.exit(f'digit {d}: no fill survived the extraction (the sheet changed colour?)')
        im = im.crop(bbox)
        padded = Image.new('L', (im.width + 2 * PAD, im.height + 2 * PAD), 0)
        padded.paste(im, (PAD, PAD))
        im = padded
        if im.width > CELL_W or im.height > CELL_H:
            sys.exit(f'digit {d}: {im.width}x{im.height} does not fit its {CELL_W}x{CELL_H} cell')
        halo = im.filter(ImageFilter.GaussianBlur(8))
        g_np = np.asarray(im).astype(np.float32) / 255.0
        h_np = np.asarray(halo).astype(np.float32) / 255.0
        x0 = d * CELL_W + (CELL_W - im.width) // 2
        y0 = (CELL_H - im.height) // 2
        alpha = np.maximum(g_np, h_np * 0.28)                 # the glyph + a faint glow skirt
        lum_out = np.clip(g_np * 1.0 + h_np * 0.55, 0, 1)
        atlas[y0:y0 + im.height, x0:x0 + im.width, 3] = alpha
        for c in range(3):
            atlas[y0:y0 + im.height, x0:x0 + im.width, c] = lum_out
    return Image.fromarray((np.clip(atlas, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA')


def measure_ink(atlas_png_bytes, thresh=40):
    """Per-digit ink columns [x0, x1] inside its cell and the ink rows [top, bottom]."""
    a = np.asarray(Image.open(io.BytesIO(atlas_png_bytes)))[..., 3]
    cols, top, bot = [], CELL_H, 0
    for d in range(10):
        c = a[:, d * CELL_W:(d + 1) * CELL_W]
        xs = np.where(c.max(axis=0) > thresh)[0]
        ys = np.where(c.max(axis=1) > thresh)[0]
        cols.append([int(xs.min()), int(xs.max())])
        top, bot = min(top, int(ys.min())), max(bot, int(ys.max()))
    return cols, [top, bot]


# --- GDT ----------------------------------------------------------------------------
def block(path, name):
    if not os.path.exists(path):
        sys.exit(f'decal donor GDT missing: {path} (the private tools root, docs/154)')
    text = open(path, encoding='utf-8', errors='replace').read().replace('\r\n', '\n')
    m = re.search(r'(\t"' + re.escape(name) + r'" \( "(?:material|image)\.gdf" \)\n)[ \t]*\{\n(.*?\n\t\})', text, re.S)
    if not m:
        sys.exit(f'template block {name} not found in {path}')
    return m.group(1) + '\t{\n' + m.group(2)


def setkv(blk, key, val):
    pat = re.compile(r'(\n\t\t"' + re.escape(key) + r'" )"[^"]*"')
    if not pat.search(blk):
        sys.exit(f'template has no "{key}"')
    return pat.sub(lambda m: m.group(1) + f'"{val}"', blk, count=1)


def rename(blk, old, new):
    return blk.replace(f'\t"{old}" (', f'\t"{new}" (', 1)


def fmt_tint(t):
    return ' '.join(f'{v:.6g}' for v in t) + ' 1'


def gdt_text():
    # gdtdb refuses a // comment ANYWHERE in a GDT: before the opening brace (memory
    # npot-image-needs-nomipmaps) AND inside it ("Adding KVP to unnamed entity" /
    # "Unknown token", the 2026-10-04 FULL build). The file carries NO note at all;
    # this generator and --check are the record that it is generated.
    out = ['{']
    img = block(*TEMPLATE_DECAL_IMG)
    img = rename(img, TEMPLATE_DECAL_IMG[1], IMAGE_ASSET)
    img = setkv(img, 'baseImage', f'source_data/tod_floornum/_images/{IMG_NAME}')
    out.append(img)
    mat_d = block(*TEMPLATE_DECAL)
    for hue, tint in DISTRICT_TINT.items():
        nt = tuple((1 - TINT_LIFT) * c + TINT_LIFT for c in tint)
        m = rename(mat_d, TEMPLATE_DECAL[1], f'tod_floornum_{hue}')
        m = setkv(m, 'colorMap', IMAGE_ASSET)
        m = setkv(m, 'colorMap00', IMAGE_ASSET)
        m = setkv(m, 'colorTint1', fmt_tint(nt))
        m = setkv(m, 'scaleRGB', f'{FLOORNUM_SCALE:.1f}')
        # The donor technique compiles USE_EMISSIVE_FLICKER and the arrow ships
        # flickerMin 0 / flickerMax 1 (a neon flicker on the POWER signs). A floor
        # number holds steady: a [1, 1] range is constant whatever the lookup does.
        m = setkv(m, 'flickerMin', '1')
        out.append(m)
    out.append('}')
    return '\n'.join(out) + '\n'


def png_bytes(im):
    b = io.BytesIO()
    im.save(b, 'PNG', optimize=False, compress_level=9)
    return b.getvalue()


# --- the generator lockstep ----------------------------------------------------------
def check_generator(atlas_png_bytes):
    """gen_tower_map.js crops each digit out of its atlas cell with FLOORNUM_INK /
    FLOORNUM_ROWS. A crop that cuts the ink prints a clipped numeral on fifty
    landings with no other warning, so measure the ink here. The district tints
    must be the generator's DISTRICTS lights."""
    g = open(GENERATOR, encoding='utf-8').read()
    errs = []
    m = re.search(r'const FLOORNUM_INK = (\[\[.*?\]\]);', g)
    r = re.search(r'const FLOORNUM_ROWS = \[(\d+), (\d+)\];', g)
    c = re.search(r'const FLOORNUM_CELL = (\d+), FLOORNUM_ATLAS = (\d+), FLOORNUM_CELL_H = (\d+);', g)
    if not (m and r and c):
        return ['gen_tower_map.js FLOORNUM_INK / FLOORNUM_ROWS / FLOORNUM_CELL not found']
    ink = json.loads(m.group(1))
    rows = (int(r.group(1)), int(r.group(2)))
    cell, atlas_w, cell_h = (int(v) for v in c.groups())
    if (cell, atlas_w, cell_h) != (CELL_W, ATLAS_W, CELL_H):
        errs.append(f'atlas geometry {cell}/{atlas_w}/{cell_h} != {CELL_W}/{ATLAS_W}/{CELL_H}')
    cols, (top, bot) = measure_ink(atlas_png_bytes)
    for d in range(10):
        x0, x1 = ink[d]
        if cols[d][0] < x0 + 6 or cols[d][1] > x1 - 6:
            errs.append(f'digit {d}: ink x {cols[d][0]}..{cols[d][1]} not inside crop {x0}..{x1} with 6 px to spare')
    if top < rows[0] + 6 or bot > rows[1] - 6:
        errs.append(f'ink rows {top}..{bot} not inside crop {rows[0]}..{rows[1]} with 6 px to spare')
    dm = re.search(r'const DISTRICTS = \[(.*?)\];', g, re.S)   # NOT the pre-facelift PALETTE (its yellow is another colour)
    if not dm:
        return errs + ['gen_tower_map.js DISTRICTS not found']
    for key, tint in DISTRICT_TINT.items():
        mm = re.search(r"\{ key: '" + key + r"',\s*light: '([\d. ]+)'", dm.group(1))
        if not mm:
            errs.append(f'DISTRICTS has no {key} row')
            continue
        gen = tuple(float(v) for v in mm.group(1).split())
        if any(abs(a - b) > 1e-6 for a, b in zip(gen, tint)):
            errs.append(f'district {key}: generator light {gen} != tint {tint}')
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--measure', action='store_true', help='print the atlas ink (to set FLOORNUM_INK / FLOORNUM_ROWS)')
    a = ap.parse_args()
    atlas = png_bytes(floornum_image())
    if a.measure:
        cols, rows = measure_ink(atlas)
        print('ink columns per digit:', json.dumps(cols))
        print('ink rows:', rows)
        print('suggested FLOORNUM_INK (14 px margin):', json.dumps([[x0 - 14, x1 + 14] for x0, x1 in cols]))
        print('suggested FLOORNUM_ROWS:', [rows[0] - 14, rows[1] + 14])
        return
    files = {
        os.path.join(IMG_DIR, IMG_NAME): atlas,
        GDT_OUT: gdt_text().encode('utf-8'),
    }
    errs = check_generator(atlas)
    for e in errs:
        print('  LOCKSTEP:', e)
    bad = []
    for p, data in files.items():
        if a.check:
            if not os.path.exists(p) or open(p, 'rb').read() != data:
                bad.append(os.path.relpath(p, REPO))
        else:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if not os.path.exists(p) or open(p, 'rb').read() != data:
                open(p, 'wb').write(data)
                print('wrote', os.path.relpath(p, REPO), len(data), 'B')
            else:
                print('unchanged', os.path.relpath(p, REPO))
    if errs:
        print('floor_numbers/make_assets FAILED - the generator and the atlas disagree (see LOCKSTEP above)')
        sys.exit(1)
    if a.check:
        if bad:
            print('floor_numbers/make_assets --check FAILED - stale or missing: ' + ', '.join(bad))
            sys.exit(1)
        print(f'FLOOR NUMBERS ASSETS OK ({len(files)} files: the digit atlas, tod_floornum.gdt; crops + district tints lockstep)')


if __name__ == '__main__':
    main()
