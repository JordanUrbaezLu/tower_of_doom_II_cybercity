"""
tools/sky3d/cut_title_gate.py — THE TITLE GATE texture: the user's reference painting cut out of its background (docs/166 §9)

User, 2026-09-29, with the reference image: "We really need to improve the cybercity 2 sign in the skybox. Looks so bland and
plain. It should look like a very bright neon sign with cyber designs all over it ... Please follow the reference exactly.
Dont stop until its indistinguishable." The sky is seen from one point, so the painting itself on one card in the 3-D scene
(build_city.py make_title_gate) IS indistinguishable from the reference; this tool makes that card's texture.

INPUTS (art/sky3d/sign/)
  tod2_title_gate_reference.png     the user's image (1448 x 1086), display-referred sRGB
  tod2_title_gate_dis5k_1024.png    BiRefNet-DIS5K masks (tools/sky3d/segment_title_gate.py): 1024 = the whole gate with soft
  tod2_title_gate_dis5k_2048.png    edges; 2048 = a crisp upper silhouette that drops the pillar bodies
OUTPUTS (art/sky3d/sign/)
  tod2_title_gate.png               RGBA 8-bit: the gate's own colours (edge colours decontaminated) + straight alpha
  tod2_title_gate_glow.png          RGB 8-bit: the neon's glow into the sky around the gate (additive, display units)
  tod2_title_gate.json              the texture's geometry for build_city.py (padding, the text box centre, the reference width)
  docs/sky_preview/gate_*.png       checks: the cut over green, over a night sky, and beside the reference

THE RECIPE (every number below is in REFERENCE pixels, x right / y down, measured on gridded zooms of the reference):
  1. alpha = the 2048 mask (crisp orbs, rings, crest spikes, railing bars, sign edges);
  2. inside the pillar zones below the banner tops, the union with the 1024 mask (the pillar bodies and lattice columns);
  3. the pillars below y 700 are solid (both masks lose them; that band sits at/below the horizon, mostly behind buildings);
  4. REMOVED: the roller-coaster loop behind the left railing and the fence / lamps / city under the arch (below y 800);
     (the reference's moon is already outside the 2048 mask, and the crest spikes that cross it are kept whole);
  5. the base fades out over y 900..960 (fog and floor in the reference);
  6. the central spire runs off the top of the reference: its tip is painted (a taper and the neon line fading into it);
  7. edge colours: pymatting's foreground estimate (if installed) so a half-covered edge is the gate's colour, not the
     reference's purple sky; without pymatting the reference colour is used (a slightly darker fringe);
  8. glow: the painted glow outside the silhouette is cut away with the sky, so it is rebuilt: the gate's COLOURED neon
     blurred, its weight fitted to glow profiles measured on the reference (GLOW_FIT), plus the spire's aura lifted from the
     reference (AURA); shipped as a separate additive texture;
  9. alpha snapped: near-opaque is opaque (a 254/255 card leaks the neon city through the dark art behind it).

RUN   python tools/sky3d/cut_title_gate.py [--no-glow] [--no-fg]      (numpy, scipy, pillow; pymatting optional)
"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SIGN = os.path.join(REPO, 'art', 'sky3d', 'sign')
PREV = os.path.join(REPO, 'docs', 'sky_preview')
ARGS = sys.argv[1:]

PAD_T, PAD_X = 128, 48                                  # canvas grown on top (the spire tip) and both sides (the glow)
BOX_PX = (724.0, 395.0)                                 # the text box centre (reference px) — build_city.py aims GATE['box_el'] here

# ---- 2. where the 1024 mask is trusted too (the pillar complexes under the banner tops)
PILLAR_ZONES = [[(0, 330), (440, 330), (440, 1000), (0, 1000)],
                [(1010, 330), (1448, 330), (1448, 1000), (1010, 1000)]]
# ---- 3. the pillars' solid lower bodies
SOLID = [[(15, 700), (252, 700), (252, 1000), (0, 1000), (0, 770)],
         [(1196, 700), (1425, 700), (1448, 770), (1448, 1000), (1196, 1000)]]
# ---- 4. removed
COASTER = [(292, 100), (457, 100), (457, 236), (400, 247), (340, 258), (300, 270), (292, 272)]   # the loop + its lift support, above the top rail, left of the spike post
BALUSTER = [(346, 222), (362, 222), (362, 262), (346, 262)]                                         # ... except the railing post inside it
UNDER_ARCH = [(335, 800), (1100, 800), (1100, 1086), (335, 1086)]                                   # the fence, gate leaves, lamps, city
# (the reference's MOON needs no removal: the 2048 mask already leaves it out and keeps the crest spikes that cross it, lit
#  edges and all. A colour model of the moon, tried first, read those spikes' grey-lavender faces as moon and half-erased them.)
# ---- 5. the base
FADE = (900.0, 960.0)
# ---- 6. the spire tip: the central block spans x 700..742 at the reference's top edge; its neon line runs at x 719..725
SPIRE = dict(x0=700.0, x1=742.0, tip=(721.5, -104.0), shoulder=-22.0, line=(719.5, 724.5), line_top=-78.0,
             solid=[(701, 0), (741, 0), (741, 90), (701, 90)])          # the central block is opaque (DIS thinned its white-hot neon line to 0.9)
# ---- 7b. white-hot neon next to the gate is opaque (DIS gives the thinnest bright tubes partial alpha: the orb rings' tips
#          measured 0.18..0.76); never under the arch, where the reference's city and ferris wheel glow through the lattice
HOT = dict(v0=0.82, v1=0.94, reach=3, arch=[(250, 570), (1200, 570), (1200, 1086), (250, 1086)])
# ---- 8. glow. MEASURED on the reference (display rgb; the sky beside each at the end): the neon glows are TIGHT and in the
#      tube's colour, not white — the left orb ring's tip x 280 y 150 -> 4 px out (89,11,190), 8 px (57,19,128), 12 px
#      (47,22,96), 16 px (41,22,78), sky (36,25,68); the right ring's tip x 1166 -> 4 px (80,3,160), 8 px (49,4,96), 12 px
#      (37,7,64), sky (22,10,37); the left beacon's top y 40 -> 5 px up (118,16,71), 10 px (75,14,60), 15 px (58,16,57), sky
#      (37,19,53). GLOW_FIT holds those points (x, y, rgb, sky rgb); the two blur weights are fitted to them (least squares).
GLOW_SIG = (2.0, 5.0)
GLOW_FIT = [(284, 150, (89, 11, 190), (36, 25, 68)), (288, 150, (57, 19, 128), (36, 25, 68)), (292, 150, (47, 22, 96), (36, 25, 68)),
            (296, 150, (41, 22, 78), (36, 25, 68)), (1162, 150, (80, 3, 160), (22, 10, 37)), (1158, 150, (49, 4, 96), (22, 10, 37)),
            (1154, 150, (37, 7, 64), (22, 10, 37)), (226, 35, (118, 16, 71), (37, 19, 53)), (226, 30, (75, 14, 60), (37, 19, 53)),
            (226, 25, (58, 16, 57), (37, 19, 53))]
# ---- 8b. THE SPIRE'S AURA: the one wide glow in the reference — a saturated magenta-violet haze round the spire's neon line
#      (measured y 40: 26 px right of the line (163,26,212), 38 px (131,38,188), 53 px (67,27,118), 68 px (53,32,108), 88 px
#      (40,29,87), sky (31,24,62)). It is LIFTED from the reference's right side (clean sky) minus that sky, and mirrored onto
#      the left side (where the reference's moon sits under it); above the reference's top edge it fades with the painted tip.
AURA = dict(axis=722.0, x1=890.0, y1=135.0, sky_cols=(895, 955), fade_up=48.0)


def log(*a):
    print('[gate]', *a, flush=True)


def poly_cov(shape, polys, ss=4):
    """anti-aliased coverage of polygons (reference px) on a canvas of `shape` (h, w)"""
    h, w = shape
    img = Image.new('L', (w * ss, h * ss), 0)
    d = ImageDraw.Draw(img)
    for p in polys:
        d.polygon([(x * ss, y * ss) for x, y in p], fill=255)
    return np.asarray(img.resize((w, h), Image.BOX)).astype(np.float32) / 255.0


def main():
    ref = np.asarray(Image.open(os.path.join(SIGN, 'tod2_title_gate_reference.png')).convert('RGB')).astype(np.float32) / 255.0
    H, W = ref.shape[:2]
    m1 = np.asarray(Image.open(os.path.join(SIGN, 'tod2_title_gate_dis5k_1024.png')).convert('L')).astype(np.float32) / 255.0
    m2 = np.asarray(Image.open(os.path.join(SIGN, 'tod2_title_gate_dis5k_2048.png')).convert('L')).astype(np.float32) / 255.0
    log(f'reference {W}x{H}; masks 1024 mean {m1.mean():.3f}, 2048 mean {m2.mean():.3f}')

    # 1-3
    a = m2.copy()
    zone = ndi.gaussian_filter(poly_cov((H, W), PILLAR_ZONES), 4.0)
    a = np.maximum(a, m1 * zone)
    a = np.maximum(a, poly_cov((H, W), SOLID))

    # 4. removals
    bg = np.clip(poly_cov((H, W), [COASTER]) - poly_cov((H, W), [BALUSTER]), 0, 1)
    bg = np.maximum(bg, poly_cov((H, W), [UNDER_ARCH]))
    a *= 1.0 - bg
    # clean-up: drop islands that are not part of the gate (stray specks, haze)
    lab, n = ndi.label(a > 0.35)
    if n:
        sizes = ndi.sum(np.ones_like(a), lab, index=np.arange(1, n + 1))
        keep = np.zeros(n + 1, bool)
        keep[1:] = sizes >= 40
        keep[0] = False
        big = keep[lab]
        near = ndi.binary_dilation(big, iterations=2)
        a = np.where(near, a, 0.0)
        log(f'islands: {n} components, {int((~keep[1:]).sum())} dropped (< 40 px)')
    a[a < 0.03] = 0.0

    # 6a. the spire's central block is opaque; 7b. white-hot neon beside the gate is opaque (outside the arch)
    a = np.maximum(a, poly_cov((H, W), [SPIRE['solid']]))
    mxr = ref.max(2)
    near = ndi.binary_dilation(a > 0.5, iterations=HOT['reach'])
    hot = near * np.clip((mxr - HOT['v0']) / (HOT['v1'] - HOT['v0']), 0, 1) * (1.0 - poly_cov((H, W), [HOT['arch']]))
    log(f'white-hot neon made opaque: {int(((hot > 0.5) & (a < 0.5)).sum())} px')
    a = np.maximum(a, hot)

    # 5. the base
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    fade = np.clip((FADE[1] - yy) / (FADE[1] - FADE[0]), 0, 1)
    a *= fade

    # 7. edge colours
    F = ref.copy()
    if '--no-fg' not in ARGS:
        try:
            from pymatting import estimate_foreground_ml
            F = np.clip(estimate_foreground_ml(ref.astype(np.float64), a.astype(np.float64)), 0, 1).astype(np.float32)
            log('edge colours: pymatting foreground estimate')
        except Exception as e:
            log(f'edge colours: reference as-is (pymatting unavailable: {e.__class__.__name__})')

    # canvas: pad top + sides
    Hc, Wc = H + PAD_T, W + 2 * PAD_X
    A = np.zeros((Hc, Wc), np.float32)
    C = np.zeros((Hc, Wc, 3), np.float32)
    A[PAD_T:, PAD_X:PAD_X + W] = a
    C[PAD_T:, PAD_X:PAD_X + W] = F

    # 6. the spire tip, painted in canvas coords (reference y + PAD_T, x + PAD_X)
    ox, oy = PAD_X, PAD_T
    x0, x1 = SPIRE['x0'], SPIRE['x1']
    tipx, tipy = SPIRE['tip']
    sh = SPIRE['shoulder']
    body = [(x0, 0.5), (x1, 0.5), (x1 - 2.0, sh), (tipx + 1.2, tipy), (tipx - 1.2, tipy), (x0 + 2.0, sh)]
    cov = poly_cov((Hc, Wc), [[(x + ox, y + oy) for x, y in body]])
    # the tip carries the block's own panel detail: every tip pixel samples the block band y 22..64 (below the aura's purple),
    # its column stretched from the taper back to the block's full width (so the neon line stays centred), the band repeated
    def edges(y):                                                         # the body polygon's left / right edge at reference row y (< 0)
        if y >= sh:
            f = y / sh
            return x0 + 2.0 * f, x1 - 2.0 * f
        f = (y - sh) / (tipy - sh)
        return x0 + 2.0 + (tipx - 1.2 - x0 - 2.0) * f, x1 - 2.0 + (tipx + 1.2 - x1 + 2.0) * f
    cols = np.zeros((Hc, Wc, 3), np.float32)
    band0, band1 = 22, 64
    for cy in range(0, oy + 1):
        y = cy - oy
        if y >= 0 or y < tipy:
            continue
        xl, xr = edges(float(y))
        for cxp in range(int(math.floor(xl + ox)) - 1, int(math.ceil(xr + ox)) + 2):
            xr_ref = cxp - ox
            fx = np.clip((xr_ref - xl) / max(xr - xl, 1e-3), 0, 1)
            xs_ = int(np.clip(round(x0 + fx * (x1 - x0)), x0, x1))
            c_band = ref[band0 + ((-y) % (band1 - band0)), xs_]
            wj = np.clip((-y - 1) / 13.0, 0, 1)                                  # the first 14 rows continue the block's own top rows (mirrored)
            cols[cy, cxp] = ref[min(-y - 1, 13), xs_] * (1 - wj) + c_band * wj
    xs = np.arange(Wc) - ox
    yr = np.arange(Hc)[:, None] - oy
    shade = np.clip(1.0 + yr / 420.0, 0.72, 1.0)[..., None]               # a little darker toward the tip
    cols *= shade
    lx0, lx1 = SPIRE['line']                                             # the neon line: the reference line's own cross-section (x 714..730,
    lc = int(round((lx0 + lx1) / 2))                                      # rows 5..60) laid up the tip, fading out toward line_top
    prof = ref[5:60, lc - 8:lc + 9].mean(0)                                # (17, 3)
    lfade = np.clip((yr - SPIRE['line_top']) / 26.0, 0, 1)                 # (Hc, 1)
    for k in range(17):
        cxp = lc - 8 + k + ox
        wlat = 1.0 if abs(k - 8) <= 3 else 0.5 * (1.0 - (abs(k - 8) - 3) / 6.0)
        wcol = (lfade[:, 0] * wlat)[:, None]
        cols[:, cxp] = cols[:, cxp] * (1 - wcol) + prof[k][None, :] * wcol
    tipm = (cov > 0) & (yr < 0)                                        # strictly above the reference: its own top row stays
    A = np.where(tipm, np.maximum(A, cov), A)
    C = np.where(tipm[..., None], cols, C)
    log(f'spire tip: {int(tipm.sum())} px painted to y {tipy:.0f} (reference px)')

    # 8. glow: the COLOURED neon of the gate (a white-hot core's halo is its tube's colour) blurred at GLOW_SIG, the weights
    #    fitted to the reference's measured profiles (GLOW_FIT); 8b. plus the spire's aura lifted from the reference
    G = np.zeros_like(C)
    if '--no-glow' not in ARGS:
        from scipy.optimize import nnls
        mx = C.max(2)
        mn = C.min(2)
        sat = (mx - mn) / np.maximum(mx, 1e-4)
        linC = np.power(C, 2.2)
        srcw = A * np.clip((mx - 0.78) / 0.14, 0, 1) * np.clip((sat - 0.45) / 0.25, 0, 1)   # neon tubes only (a red-lit surface is ~0.6..0.78)
        S = linC * srcw[..., None]
        basis = [np.stack([ndi.gaussian_filter(S[..., k], s) for k in range(3)], -1) for s in GLOW_SIG]
        rows, rhs = [], []
        for x, y, c, sky in GLOW_FIT:
            t = (np.array(c) / 255.0) ** 2.2 - (np.array(sky) / 255.0) ** 2.2
            for k in range(3):
                rows.append([b[y + PAD_T, x + PAD_X, k] for b in basis])
                rhs.append(t[k])
        w, res = nnls(np.array(rows), np.array(rhs))
        glow_lin = sum(wi * b for wi, b in zip(w, basis))
        pred = np.array(rows) @ w
        log(f'glow: weights {np.round(w, 3).tolist()} for sigma {GLOW_SIG}; fit rms {np.sqrt(np.mean((pred - np.array(rhs)) ** 2)):.4f} '
            f'(targets {np.round(np.array(rhs).reshape(-1, 3)[:, 2], 3).tolist()} blue)')
        # the aura
        ref_lin = np.power(ref, 2.2)
        c0, c1 = AURA['sky_cols']
        sky_row = np.median(ref_lin[:, c0:c1], axis=1)                                   # the sky beside the aura, per row
        exc = np.maximum(ref_lin - sky_row[:, None, :], 0.0)
        ax, ax1, ay1 = AURA['axis'], AURA['x1'], AURA['y1']
        region = np.zeros((H, W), np.float32)
        region[0:int(ay1), int(ax):int(ax1)] = 1.0
        valid = region * (a < 0.3)
        num = np.stack([ndi.gaussian_filter(exc[..., k] * valid, 6.0) for k in range(3)], -1)
        den = ndi.gaussian_filter(valid, 6.0)[..., None]
        filled = np.where(valid[..., None] > 0, exc, num / np.maximum(den, 1e-4)) * region[..., None]
        aura = np.zeros((Hc, Wc, 3), np.float32)
        xs_ref = np.arange(Wc) - PAD_X
        for cx in range(Wc):
            xr = xs_ref[cx]
            xm = xr if xr >= ax else 2 * ax - xr
            xi = int(round(xm))
            if not (int(ax) <= xi < int(ax1)):
                continue
            span = (ax1 - ax)
            fx = np.clip((span - abs(xr - ax)) / (0.25 * span), 0, 1)                     # fade toward the region's outer edge
            aura[PAD_T:, cx] = filled[:, xi] * fx
        fy = np.clip((ay1 - (np.arange(Hc) - PAD_T)) / (0.3 * ay1), 0, 1)[:, None, None]
        aura *= fy
        up = np.exp(np.minimum(np.arange(Hc) - PAD_T, 0) / AURA['fade_up'])                # above the reference's top row
        aura[:PAD_T] = aura[PAD_T][None] * up[:PAD_T, None, None]
        log(f'aura: peak {aura.max():.3f} (linear), mirrored about x {ax:.0f}')
        G_lin = glow_lin + aura                                         # the (1 - alpha) cover is applied after the snap (9.)

    # 9. snap: the masks top out at 254/255, and the city behind is neon at ~100x the banners' own light — a 0.4 % leak drew a
    #    green tower THROUGH both banners in the first render. Near-opaque is opaque, near-clear is clear; edges keep their ramp.
    A = np.clip((A - 0.03) / (0.95 - 0.03), 0, 1)
    if '--no-glow' not in ARGS:
        G = np.power(np.clip(G_lin * (1.0 - A)[..., None], 0, 1), 1 / 2.2)   # glow only where the sky shows (it is added light, never on the gate)
    log(f'alpha snapped: {int((A >= 1).sum())} px opaque, {int(((A > 0) & (A < 1)).sum())} px edge')

    # outputs
    rgba = np.dstack([np.clip(C, 0, 1), np.clip(A, 0, 1)])
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(SIGN, 'tod2_title_gate.png'))
    Image.fromarray((np.clip(G, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(SIGN, 'tod2_title_gate_glow.png'))
    meta = dict(size=[Wc, Hc], ref_size=[W, H], pad_top=PAD_T, pad_x=PAD_X, box_px=[BOX_PX[0] + PAD_X, BOX_PX[1] + PAD_T],
                ref_width_px=W, note='docs/166 §9; build_city.py make_title_gate reads this')
    with open(os.path.join(SIGN, 'tod2_title_gate.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    log(f'wrote tod2_title_gate.png {Wc}x{Hc} (+ glow, json)')

    # checks
    os.makedirs(PREV, exist_ok=True)
    green = np.array([0.0, 1.0, 0.2], np.float32)
    over_g = C * A[..., None] + green * (1 - A[..., None])
    sky = np.zeros_like(C)
    sky[:] = np.array([0.11, 0.07, 0.24], np.float32)                   # the reference's own night purple (measured: 28..47, 17..25, 56..90)
    sky *= np.linspace(0.8, 1.25, Hc)[:, None, None]
    lin_over = np.power(C, 2.2) * A[..., None] + np.power(sky, 2.2) * (1 - A[..., None]) + np.power(G, 2.2)
    over_s = np.power(np.clip(lin_over, 0, 1), 1 / 2.2)
    refc = np.zeros_like(C)
    refc[PAD_T:, PAD_X:PAD_X + W] = ref
    pair = np.concatenate([refc, over_s], 1)
    Image.fromarray((np.clip(over_g, 0, 1) * 255).astype(np.uint8)).save(os.path.join(PREV, 'gate_cut_green.png'))
    Image.fromarray((np.clip(pair, 0, 1) * 255).astype(np.uint8)).save(os.path.join(PREV, 'gate_cut_vs_reference.png'))
    log('checks -> docs/sky_preview/gate_cut_green.png, gate_cut_vs_reference.png')


if __name__ == '__main__':
    main()
