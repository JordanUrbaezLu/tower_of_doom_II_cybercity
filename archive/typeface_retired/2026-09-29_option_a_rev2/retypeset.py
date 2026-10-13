"""retypeset.py - the ONE-TIME redraw that made the 2026-09-29 legibility revision of the map typeface.

Kept for history in archive/typeface_retired/2026-09-29_option_a_rev2/ beside the sheets it read. The live
sheets it produced ARE the masters now (source_data/tod_ui_images/_sheets); never re-run it onto them.
Settings used (the defaults below): --thin 1.25 --thin-digits-k 1.5 --round 3 --inner 1.5 --ext-letters 3
--ext-digits 5 --outline 4.5 --s-stroke 12.8; the S redrawn (draw_S), the 5 kept square.

The typeface (docs/172 option A) is built as: a light FACE (#E8EEF6), a hard EXTRUSION down-right
(#62779C, 5 px letters / 8 px digits), and a dark OUTLINE (#0A1020, ~5 px) around both. Measured on
the capital I at mid-height: 5 outline + 15 face + 5 extrusion + 6 outline = 31 px of stroke for a
15 px face, and the extrusion also falls INSIDE every counter (O, B, 8, A ...), shrinking the holes
that make letters readable at small sizes.

This rebuilds every glyph from its FACE SHAPE alone, so the letterforms (their design) are kept:
  1. extract the face mask (the light pixels) at 4x resolution
  2. thin the stroke (erode by `thin` px), keeping the glyph's size (rescaled back to its old ink box)
  3. round it a little (open = round convex corners, close = round inner corners), per glyph extra
  4. re-render the same construction: outline around (face + extrusion), extrusion, face; same colours
The gold money coin ($) is copied untouched.

  python retypeset.py --variant NAME [--thin 1.25 --round 3 --inner 2 --ext-letters 3 --ext-digits 5 --outline 4.5]
Writes out/<variant>/i_tod_hud_letters.png + i_tod_hud_digits.png (same canvas / cells / baselines).
"""
import argparse, os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
# ARCHIVED (2026-09-29): this drew the live typeface ONCE, from the retired sheets beside it.
# It reads only this folder and writes only out/ here; the live masters are never touched.
SHEETS = HERE
FACE = np.array([232, 238, 246], float)
OUTLINE = np.array([10, 16, 32], float)
EXTR = np.array([98, 119, 156], float)
UP = 4   # work at 4x for smooth, round morphology

SETS = {
    'letters': dict(file='i_tod_hud_letters.png', cw=80, ch=112, cols=15, rows=2,
                    chars=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + ['-', "'", '$', '.'], ext=5),
    'digits': dict(file='i_tod_hud_digits.png', cw=128, ch=160, cols=13, rows=1,
                   chars=list('0123456789') + ['/', '+', '-'], ext=8),
}
# per-glyph extra rounding (px at 1x) on the OUTER corners: S must stop reading as 5
EXTRA_ROUND = {('letters', 'S'): 3.5, ('digits', '5'): -1.5}


def disk(r):
    r = max(0.0, r)
    n = int(np.ceil(r))
    y, x = np.mgrid[-n:n + 1, -n:n + 1]
    return (x * x + y * y) <= r * r + 1e-6


def sdf(mask):
    """signed distance (px): + inside, - outside, from a boolean mask."""
    inside = ndimage.distance_transform_edt(mask)
    outside = ndimage.distance_transform_edt(~mask)
    return inside - outside


def fillet_path(pts, radii, steps=24):
    """a polyline with each inner corner replaced by a circular-ish (quadratic) fillet of radius r."""
    out = [np.array(pts[0], float)]
    for i in range(1, len(pts) - 1):
        a, b, c = (np.array(pts[j], float) for j in (i - 1, i, i + 1))
        r = radii[i]
        u, v = (a - b), (c - b)
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        r = min(r, lu * 0.49, lv * 0.49)
        p0, p1 = b + u / lu * r, b + v / lv * r
        for k in range(steps + 1):
            t = k / steps
            out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p1)
    out.append(np.array(pts[-1], float))
    return np.array(out)


def stroke_mask(path, w, shape, flat_ends=True):
    """face mask (UP x) of a stroke of width w (1x px) along `path` (1x px), flat end caps."""
    H, W = shape
    yy, xx = np.mgrid[0:H, 0:W]
    P = np.dstack([(xx + 0.5) / UP, (yy + 0.5) / UP])
    d = np.full((H, W), 1e9)
    for a, b in zip(path[:-1], path[1:]):
        ab = b - a
        L2 = float(ab @ ab) or 1e-9
        t = np.clip(((P - a) @ ab) / L2, 0, 1)
        q = a + t[..., None] * ab
        d = np.minimum(d, np.linalg.norm(P - q, axis=2))
    m = d <= w / 2
    if flat_ends:
        for end, nxt in ((path[0], path[1]), (path[-1], path[-2])):
            dirv = (nxt - end) / np.linalg.norm(nxt - end)
            near = np.linalg.norm(P - end, axis=2) <= w / 2 + 1.5
            behind = ((P - end) @ dirv) < 0
            m &= ~(near & behind)
    return m


def draw_S(box, w, shape):
    """THE S, redrawn (it was the digit 5's shape: a square top-left corner and a straight stem, the
    two read the same at every in-game size). One stroke of the letters' weight in the old S's box:
    all four bends rounded about one stroke wide, short hooked ends. The 5 keeps its square corner."""
    x0, y0, x1, y1 = box
    h = w / 2
    xl, xr = x0 + h, x1 - h
    yt, yb = y0 + h, y1 - h
    ym = (y0 + y1) / 2
    hook = 0.17 * (y1 - y0)
    pts = [(xr, yt + hook), (xr, yt), (xl, yt), (xl, ym), (xr, ym), (xr, yb), (xl, yb), (xl, yb - hook)]
    R = 1.0 * w
    radii = [0, 0.5 * w, R, R, R, R, 0.5 * w, 0]
    return stroke_mask(fillet_path(pts, radii), w, shape)


def face_mask(cell):
    """AA coverage of the light face in an RGBA cell -> boolean mask at UP x."""
    rgb = cell[..., :3].astype(float)
    a = cell[..., 3].astype(float) / 255.0
    L = rgb.mean(axis=2)
    # the face is the only light colour; its edge meets outline (L~19) or extrusion (L~124):
    # threshold between face (239) and the extrusion (124) so an extrusion pixel is never face
    cov = np.clip((L - 150.0) / (239.0 - 150.0), 0, 1) * (a > 0.5)
    big = np.array(Image.fromarray((cov * 255).astype(np.uint8)).resize(
        (cell.shape[1] * UP, cell.shape[0] * UP), Image.BILINEAR)).astype(float) / 255.0
    return big > 0.5


def render(face_big, ext_px, outline_px, h, w):
    """draw outline(face + extrusion), extrusion, face at UP x, return RGBA uint8 at 1x."""
    ext = int(round(ext_px * UP))
    solid = face_big.copy()
    for t in range(1, ext + 1):   # the hard extrusion: the face swept down-right (no wrap)
        sh = np.zeros_like(face_big)
        sh[t:, t:] = face_big[:-t, :-t]
        solid |= sh
    d_solid = sdf(solid)
    d_face = sdf(face_big)
    ol = outline_px * UP
    # coverage with a 1-px (at 1x) smooth edge
    def cov(d):
        return np.clip(d / UP + 0.5, 0, 1)
    c_out = cov(d_solid + ol)            # outline silhouette
    c_ext = cov(d_solid)                 # extrusion region (under the face)
    c_face = cov(d_face)
    rgb = np.zeros(face_big.shape + (3,), float)
    alpha = c_out
    rgb[:] = OUTLINE
    rgb = rgb * (1 - c_ext[..., None]) + EXTR * c_ext[..., None]
    rgb = rgb * (1 - c_face[..., None]) + FACE * c_face[..., None]
    out = np.dstack([rgb, alpha[..., None] * 255.0])
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')
    # premultiplied-ish downsample: average colour weighted by alpha
    small = img.resize((w, h), Image.LANCZOS)
    return np.array(small)


def rebuild(setname, cfg, args):
    src = np.array(Image.open(os.path.join(SHEETS, cfg['file'])).convert('RGBA'))
    out = np.zeros_like(src)
    report = {}
    for i, ch in enumerate(cfg['chars']):
        c, r = i % cfg['cols'], i // cfg['cols']
        x0, y0 = c * cfg['cw'], r * cfg['ch']
        cell = src[y0:y0 + cfg['ch'], x0:x0 + cfg['cw']]
        if ch == '$' or cell[..., 3].max() == 0:
            out[y0:y0 + cfg['ch'], x0:x0 + cfg['cw']] = cell   # the gold coin stays as drawn
            continue
        face = face_mask(cell)
        if not face.any():
            out[y0:y0 + cfg['ch'], x0:x0 + cfg['cw']] = cell
            continue
        ys, xs = np.nonzero(face)
        box = (xs.min(), ys.min(), xs.max(), ys.max())
        # THE INK BOX IS KEPT, NOT THE FACE BOX: the game sizes and places a glyph by its measured ink
        # (face + outline + extrusion; tools/slice_hud_sheets.js cap / baseline). A lighter outline and
        # extrusion would shrink that ink (the letters' cap 89 -> 87, the numerals' 137 -> 127) and every
        # line would draw a little bigger. So the new face fills the old ink box minus the NEW outline
        # and extrusion: the same cap, baseline and advances, a face about 4 % larger, a lighter stroke.
        ext_new = args.ext_letters if setname == 'letters' else args.ext_digits
        ink = cell[..., 3] > 24
        iys, ixs = np.nonzero(ink)
        ol_new = args.outline
        tx0, ty0 = (ixs.min() + ol_new) * UP, (iys.min() + ol_new) * UP
        tx1, ty1 = (ixs.max() + 1 - ol_new - ext_new) * UP - 1, (iys.max() + 1 - ol_new - ext_new) * UP - 1
        box = (int(round(tx0)), int(round(ty0)), int(round(tx1)), int(round(ty1)))
        # 1. ROUND FIRST, while the stroke is still full width (15 px letters / 23 px digits), so a
        #    rounding radius can never erase a stroke: open = round the convex corners, close = the
        #    inner corners. S gets a little more (it read as 5 at small sizes); 5 keeps its corners.
        f1 = face
        rr = (args.round + EXTRA_ROUND.get((setname, ch), 0.0)) * UP
        if rr > 0:
            f1 = sdf(sdf(f1) > rr) > -rr
        ri = args.inner * UP
        if ri > 0:
            f1 = sdf(sdf(f1) > -ri) > ri
        # 2. THIN, then scale back onto the old ink box: the same size, a lighter stroke
        thin = args.thin * (args.thin_digits_k if setname == 'digits' else 1.0) * UP
        f2 = sdf(f1) > thin
        if f2.any():
            ys2, xs2 = np.nonzero(f2)
            b2 = (xs2.min(), ys2.min(), xs2.max(), ys2.max())
            sx = (box[2] - box[0] + 1) / max(1, (b2[2] - b2[0] + 1))
            sy = (box[3] - box[1] + 1) / max(1, (b2[3] - b2[1] + 1))
            yy, xx = np.mgrid[0:face.shape[0], 0:face.shape[1]]
            srcx = b2[0] + (xx - box[0]) / sx
            srcy = b2[1] + (yy - box[1]) / sy
            f3 = ndimage.map_coordinates(sdf(f2), [srcy, srcx], order=1, mode='constant', cval=-50) > 0
        else:
            f3 = f1
        if (setname, ch) == ('letters', 'S'):
            # the S is REDRAWN, not filtered (draw_S): same box, the new stroke weight
            fb = (box[0] / UP, box[1] / UP, (box[2] + 1) / UP, (box[3] + 1) / UP)
            f3 = draw_S(fb, args.s_stroke, face.shape)
        ext = args.ext_letters if setname == 'letters' else args.ext_digits
        cellnew = render(f3, ext, args.outline, cfg['ch'], cfg['cw'])
        out[y0:y0 + cfg['ch'], x0:x0 + cfg['cw']] = cellnew
        report[ch] = dict(face_px_old=int(face.sum() / UP / UP), face_px_new=int(f3.sum() / UP / UP))
    return out, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', required=True)
    ap.add_argument('--thin', type=float, default=1.25)        # px per side at 1x (letters)
    ap.add_argument('--thin-digits-k', type=float, default=1.5)  # digits are 1.5x the letters' stroke
    ap.add_argument('--round', type=float, default=3.0)
    ap.add_argument('--inner', type=float, default=1.5)
    ap.add_argument('--ext-letters', type=float, default=3.0)
    ap.add_argument('--ext-digits', type=float, default=5.0)
    ap.add_argument('--outline', type=float, default=4.5)
    ap.add_argument('--s-stroke', type=float, default=12.8)   # the redrawn S = the thinned letters' stroke
    args = ap.parse_args()
    od = os.path.join(HERE, 'out', args.variant)
    os.makedirs(od, exist_ok=True)
    rep = {}
    for setname, cfg in SETS.items():
        img, r = rebuild(setname, cfg, args)
        Image.fromarray(img, 'RGBA').save(os.path.join(od, cfg['file']))
        rep[setname] = r
    json.dump({'args': vars(args), 'glyphs': rep}, open(os.path.join(od, 'report.json'), 'w'), indent=1)
    print('wrote', od)


if __name__ == '__main__':
    main()
