"""R2 - CARD SUBJECT FIXES (2026-10-04, tmp/design_review/findings.md "Wrong subject").

User, browsing the Art Atlas: "mozambique isnt even mozambique ... dozens more". Four card images showed the
wrong thing; each is redrawn here FROM THE GAME'S OWN MODEL (render it, then stylize), in the look of the
card it sits in:

  i_tod_card2_art_tier_heavy_3        576x448  layered-card illustration (TodCardArt.lua, tier 3 of the BREACHER)
      was a sci-fi energy rifle. Now the APEX PEACEKEEPER the player is actually handed: tod_bra_pk_view =
      vm_apex_peacekeeper (+ i_apex_peacekeeper_skin32_c, tools/install_breacher_apex.py SKINS['pk']) -
      lever loop, teal grip wrap, tan cheek pad, blue-grey receiver, the double shroud with its 14 shell holders.
  i_tod_card2_art_tier_necromancer_2  576x448  was the summons (two soul hounds) - now the SOUL STAFF
      (tod_necro_staff2_world: the iron shaft, the ferrule and the skull with its white soul-lit eyes).
  i_tod_card2_art_tier_necromancer_3  576x448  was a stone golem - now the CROWN OF THE DAMNED
      (tod_necro_staff3_world: the skull inside the notched iron ring, twelve radiating blades, the long top blade).
      Every other class's tier card shows its NEW WEAPON; these two now do as well.
  i_tod_card_class_heavy              NO LONGER WRITTEN HERE (R6, 2026-10-05): tools/artgen/packs/r6_class_cards.py owns all
      four class draft cards and draws the Mozambique with this pack's render + stylize and MOZ_STYLE; the paragraph
      below and paint_class_heavy_window() are the record.
  i_tod_card_class_heavy              768x1152 the class-draft card: ONLY its art window changes (every other pixel
      is the card as PK01 left it). The generic three-tube block is replaced by the real MOZAMBIQUE
      (tod_bra_moz_view = vm_apex_mozambique + i_apex_mozambique_c): the triple-bore muzzle, the tan shroud with
      its three ports, the black frame and grip, the red details - in the class card's own flat look (thin
      outline, 2-3 tones, a pale-red top edge, the Breacher's orange glow behind it).

HOW (every step deterministic; no randomness, no clock):
  1. --render (needs PyCoD + the BO3 model bins; run once, or when a view changes): each model is rasterised
     by a small orthographic z-buffer (numpy) into CACHED BUFFERS under art/generated/R2-card-subjects/src/:
     <s>_albedo.png (the true texture colour, alpha = coverage), <s>_normal.png, <s>_depth.png (16 bit),
     <s>_mat.png (material index), and <s>_truth.png (a plain lit render - the reference the review shows).
     The cache is the generator's input from then on, so --check needs neither Blender's PyCoD nor the
     ignored Apex library nor C:\\BO3Tools.
  2. STYLIZE (the card look, from the buffers): the albedo is median-smoothed and clustered (k-means in an
     opponent colour space, fixed initialisation) into flat regions; each region takes the ART-DIRECTED colour
     of the nearest probe in the subject's table (wear and grime clusters are absorbed into what surrounds
     them); three light bands from the true normals (shadow / base / lit top facet); a dark navy line where
     depth jumps, a softer line on creases and between regions; a thin warm rim on top edges; the thick
     #0a0c19 outline round the silhouette. Drawn at 2x, downsampled premultiplied.
  3. COMPOSE:
     * card2 art: the layered card's own BACKGROUND TEMPLATE (navy gradient, 9-row scanlines, edge vignette,
       the moon) - derived ONCE by --derive-bg from the 32 shipped card2 illustrations that stay (per-pixel
       mode of the cards sharing the moon side, then row-constant clean-up; donors pinned in src/bg_donors.json),
       a faint lighter blob behind the subject (the family's), a soft halo, the family's square pips and
       four-point sparkles at the family's positions, then the subject.
     * the class card: the old gun AND its glow are lifted out of the window (the window's 40-px hairlines
       are taken off, the hole is filled harmonically from its rim, the hairlines go back across), then the
       Mozambique and a new orange glow are drawn in. The base card is PK01's output, pinned by sha256
       (src/i_tod_card_class_heavy_base.png); PK01's generator applies paint_class_heavy_window() on top of
       its own name-box work, so the file keeps ONE owner (see tmp/redesign/R2-card-subjects/LAND.md).

  python -B tools/artgen/packs/r2_card_subjects.py               write the 4 PNGs + _review.png to art/generated/R2-card-subjects/
  python -B tools/artgen/packs/r2_card_subjects.py --stage DIR   also write them under DIR/source_data/tod_ui_images/_images/
  python -B tools/artgen/packs/r2_card_subjects.py --install     also write them into source_data/tod_ui_images/_images/
  python -B tools/artgen/packs/r2_card_subjects.py --check       fail on any byte that differs from the installed PNGs
  python -B tools/artgen/packs/r2_card_subjects.py --render      re-rasterise the four models into src/ (PyCoD + model bins)
  python -B tools/artgen/packs/r2_card_subjects.py --derive-bg   rebuild the two background templates from the donors
"""
import argparse, glob, hashlib, json, os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402

PACK = 'R2-card-subjects'
ROOT = artgen.ROOT
OUT = os.path.join(ROOT, 'art', 'generated', PACK)
SRC = os.path.join(OUT, 'src')
IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')
BO3 = 'C:/BO3Tools/TOD2Cybercity/model_export/apex'
STAFF = os.path.join(ROOT, 'model_export', 'tod_necro_staff')
SS = 2                                            # every subject is drawn 2x and downsampled
LINE = (10, 12, 25)                               # the card2 family's outline navy (#0a0c19 .. #0a0e21)

CARD2 = ['i_tod_card2_art_tier_heavy_3', 'i_tod_card2_art_tier_necromancer_2', 'i_tod_card2_art_tier_necromancer_3']
CLASS = 'i_tod_card_class_heavy'
NAMES = CARD2                                     # CLASS is R6's since 2026-10-05 (r6_class_cards.py)
CLASS_BASE = os.path.join(SRC, CLASS + '_base.png')
CLASS_BASE_SHA = 'ab0dc1a0d3ca90c2c01764d113f4841711e4d960871cad7801f1c9a04477826f'   # PK01's output, 2026-10-04

# --------------------------------------------------------------------------------------------- subjects
# view: (yaw, pitch, roll) degrees; 'up' maps the model's long axis; scale = px per model unit at 2x;
# anchor = model point -> 2x canvas pixel.
Z_UP = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]        # staff models: z is up, the skull looks down -y
SUBJECTS = {
    'pk': dict(
        model=BO3 + '/vm_apex_peacekeeper.XMODEL_BIN',
        tex={0: BO3 + '/i_apex_peacekeeper_skin32_c.tif', 1: BO3 + '/i_apex_peacekeeper_skin32_c.tif',
             2: BO3 + '/i_apex_peacekeeper_skin32_c.tif'},
        base=None, view=(90, 8, 14), canvas=(1152, 896), scale=26.6, anchor=(0.0, 1.24, 3.93), at=(576, 468)),
    'staff2': dict(
        model=STAFF + '/tod_necro_staff2_world_lod0.XMODEL_BIN',
        tex={0: STAFF + '/i_tod_necro_leather_c.png', 1: STAFF + '/i_tod_necro_forge_c.png', 2: (0.24, 0.21, 0.17),
             3: STAFF + '/i_tod_necro_iron_c.png', 4: STAFF + '/i_tod_necro_bone_c.png',
             5: STAFF + '/i_tod_necro_staff_soul_c.png'},
        base=Z_UP, view=(0, 6, -30), canvas=(1152, 896), scale=36.0, anchor=(0.0, 0.0, 32.4), at=(690, 310)),
    'staff3': dict(
        model=STAFF + '/tod_necro_staff3_world_lod0.XMODEL_BIN',
        tex={0: STAFF + '/i_tod_necro_leather_c.png', 1: STAFF + '/i_tod_necro_forge_c.png', 2: (0.24, 0.21, 0.17),
             3: STAFF + '/i_tod_necro_iron_c.png', 4: STAFF + '/i_tod_necro_bone_c.png',
             5: STAFF + '/i_tod_necro_staff_soul_c.png'},
        base=Z_UP, view=(0, 3, -20), canvas=(1152, 896), scale=24.0, anchor=(0.0, 0.0, 32.4), at=(600, 540)),
    'moz': dict(
        model=BO3 + '/vm_apex_mozambique.XMODEL_BIN',
        tex={0: BO3 + '/i_apex_mozambique_c.tif', 1: BO3 + '/i_apex_mozambique_c.tif', 2: (0.9, 0.15, 0.15)},
        base=None, view=(58, 6, 0), canvas=(1136, 936), scale=52.0, anchor=(0.0, 1.27, 4.88), at=(568, 556)),
}

# ------------------------------------------------------------------------------------------ the render (--render)

def _pycod():
    cands = sorted(glob.glob(os.path.join(os.environ.get('APPDATA', ''), 'Blender Foundation', 'Blender', '*',
                                          'scripts', 'addons', 'BetterBetterBlenderCOD')))
    if not cands:
        raise SystemExit('R2 --render: PyCoD (BetterBetterBlenderCOD) not found under %APPDATA%/Blender Foundation')
    sys.path.insert(0, cands[-1])
    from PyCoD import xmodel
    return xmodel


def rot(yaw=0.0, pitch=0.0, roll=0.0):
    """model -> view: yaw about up (Y), then pitch about X, then roll about the view axis. View: x right, y up,
    z toward the viewer (orthographic)."""
    a, b, c = np.radians([yaw, pitch, roll])
    ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    rz = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return rz @ rx @ ry


def load_model(path):
    xm = _pycod()
    m = xm.Model()
    m.LoadFile_Bin(path)
    P, N, U, M = [], [], [], []
    for mesh in m.meshes:
        vp = np.array([v.offset for v in mesh.verts], np.float64)
        for f in mesh.faces:
            idx = [fv.vertex for fv in f.indices]
            P.append(vp[idx])
            N.append([fv.normal for fv in f.indices])
            U.append([fv.uv for fv in f.indices])
            M.append(f.material_id)
    return np.array(P), np.array(N, np.float64), np.array(U, np.float64), np.array(M)


def raster(P, W, H, R, scale, anchor, at):
    """z-buffer every triangle; returns the per-pixel triangle id, depth and the screen-space corners."""
    S = (P.reshape(-1, 3) @ R.T).reshape(-1, 3, 3)
    a = np.asarray(anchor, float) @ R.T
    X = (S[..., 0] - a[0]) * scale + at[0]
    Y = (a[1] - S[..., 1]) * scale + at[1]
    Z = S[..., 2]
    tid = np.full((H, W), -1, np.int32)
    dep = np.full((H, W), -np.inf)
    for t in range(len(S)):
        x, y, z = X[t], Y[t], Z[t]
        x0, x1 = max(int(np.floor(x.min())), 0), min(int(np.ceil(x.max())), W - 1)
        y0, y1 = max(int(np.floor(y.min())), 0), min(int(np.ceil(y.max())), H - 1)
        if x1 < x0 or y1 < y0:
            continue
        area = (x[1] - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (y[1] - y[0])
        if abs(area) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((x[1] - gx) * (y[2] - gy) - (x[2] - gx) * (y[1] - gy)) / area
        w1 = ((x[2] - gx) * (y[0] - gy) - (x[0] - gx) * (y[2] - gy)) / area
        w2 = 1 - w0 - w1
        ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not ins.any():
            continue
        zz = w0 * z[0] + w1 * z[1] + w2 * z[2]
        sub, st = dep[y0:y1 + 1, x0:x1 + 1], tid[y0:y1 + 1, x0:x1 + 1]
        upd = ins & (zz > sub)
        sub[upd] = zz[upd]
        st[upd] = t
    return tid, dep, (X, Y)


def interp(tid, XY, attr):
    X, Y = XY
    H, W = tid.shape
    ys, xs = np.nonzero(tid >= 0)
    t = tid[ys, xs]
    gx, gy = xs + 0.5, ys + 0.5
    x, y = X[t], Y[t]
    area = (x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0]) - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0])
    w0 = ((x[:, 1] - gx) * (y[:, 2] - gy) - (x[:, 2] - gx) * (y[:, 1] - gy)) / area
    w1 = ((x[:, 2] - gx) * (y[:, 0] - gy) - (x[:, 0] - gx) * (y[:, 2] - gy)) / area
    w2 = 1 - w0 - w1
    a = attr[t]
    out = np.zeros((H, W, attr.shape[2]))
    out[ys, xs] = w0[:, None] * a[:, 0] + w1[:, None] * a[:, 1] + w2[:, None] * a[:, 2]
    return out


def render_subject(name):
    s = SUBJECTS[name]
    P, N, U, M = load_model(s['model'])
    R = rot(*s['view'])
    if s['base'] is not None:
        R = R @ np.array(s['base'], float)
    W, H = s['canvas']
    tid, dep, XY = raster(P, W, H, R, s['scale'], s['anchor'], s['at'])
    m = tid >= 0
    uv = interp(tid, XY, U)
    n = interp(tid, XY, N) @ R.T
    n /= (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9)
    mat = np.where(m, M[np.maximum(tid, 0)], 0)
    alb = np.zeros((H, W, 3))
    for mi, t in s['tex'].items():
        sel = m & (mat == mi)
        if not sel.any():
            continue
        if isinstance(t, tuple):
            alb[sel] = t
            continue
        T = np.asarray(Image.open(t).convert('RGB')).astype(np.float32) / 255
        u = np.mod(uv[..., 0], 1.0)
        v = np.mod(uv[..., 1], 1.0)
        c = T[(v * (T.shape[0] - 1)).astype(int), (u * (T.shape[1] - 1)).astype(int)]
        alb[sel] = c[sel]
    d = np.where(m, dep, 0)
    lo, hi = float(d[m].min()), float(d[m].max())
    dq = np.where(m, np.rint((d - lo) / max(hi - lo, 1e-9) * 65000) + 100, 0).astype(np.uint16)
    os.makedirs(SRC, exist_ok=True)
    A = np.dstack([np.clip(alb, 0, 1) * 255, m * 255.0]).astype(np.uint8)
    artgen.save_png(Image.fromarray(A, 'RGBA'), os.path.join(SRC, name + '_albedo.png'), allow_any_size=True)
    nq = np.where(m[..., None], np.clip(np.rint(n * 127.5 + 127.5), 0, 255), 0).astype(np.uint8)
    Image.fromarray(nq, 'RGB').save(os.path.join(SRC, name + '_normal.png'), optimize=False, compress_level=9)
    Image.fromarray(dq).save(os.path.join(SRC, name + '_depth.png'), optimize=False, compress_level=9)
    Image.fromarray(mat.astype(np.uint8), 'L').save(os.path.join(SRC, name + '_mat.png'), optimize=False, compress_level=9)
    # the plain lit render: what the model looks like before the card look is applied
    Ld = np.array([-0.3, 0.6, 0.75]); Ld /= np.linalg.norm(Ld)
    sh = np.clip((n * Ld).sum(-1), 0, 1) * 0.75 + 0.35
    tr = np.where(m[..., None], np.clip(alb * sh[..., None] * 1.6, 0, 1), np.array([0.16, 0.17, 0.2]))
    artgen.save_png(Image.fromarray((tr * 255).astype(np.uint8), 'RGB').convert('RGBA'),
                    os.path.join(SRC, name + '_truth.png'), allow_any_size=True)
    meta = dict(model=os.path.basename(s['model']), model_sha256=sha256(s['model']), view=list(s['view']),
                scale=s['scale'], anchor=list(s['anchor']), at=list(s['at']), canvas=list(s['canvas']),
                depth_units=(hi - lo) / 65000.0, triangles=int(len(P)))
    return meta


def sha256(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_buffers(name):
    a = np.asarray(Image.open(os.path.join(SRC, name + '_albedo.png')).convert('RGBA')).astype(np.float64) / 255
    n = np.asarray(Image.open(os.path.join(SRC, name + '_normal.png')).convert('RGB')).astype(np.float64)
    d = np.asarray(Image.open(os.path.join(SRC, name + '_depth.png'))).astype(np.float64)
    mat = np.asarray(Image.open(os.path.join(SRC, name + '_mat.png'))).astype(np.int64)
    meta = json.load(open(os.path.join(SRC, 'render.json'), encoding='utf-8'))[name]
    m = a[..., 3] > 0.5
    n = (n - 127.5) / 127.5
    n /= (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9)
    dep = np.where(m, (d - 100) * meta['depth_units'], -1e9)
    return dict(m=m, alb=a[..., :3], n=n, dep=dep, mat=mat)

# --------------------------------------------------------------------------------------------- stylize

def _opp(X):
    L = X @ np.array([0.3, 0.59, 0.11])
    return np.stack([L, (X[..., 0] - X[..., 1]) * 6, ((X[..., 0] + X[..., 1]) / 2 - X[..., 2]) * 6], -1)


def _kmeans(X, k, iters=24):
    lum = X[:, 0]
    order = np.argsort(lum, kind='stable')
    C = np.stack([X[order[int((i + 0.5) / k * len(X))]] for i in range(k)])
    for _ in range(iters):
        lab = ((X[:, None, :] - C[None]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            if (lab == j).any():
                C[j] = X[lab == j].mean(0)
    return C


def _majority(L, m, k, size):
    best = np.zeros(L.shape)
    arg = np.full(L.shape, -1)
    for j in range(k):
        f = ndi.uniform_filter(((L == j) & m).astype(np.float64), size)
        upd = f > best
        best[upd] = f[upd]
        arg[upd] = j
    return np.where(m, arg, -1)


def _disk(r):
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= r * r + 0.5


def _fill_holes(L, m, hole, k):
    for _ in range(200):
        h = m & hole
        if not h.any():
            break
        best = np.zeros(L.shape)
        arg = np.full(L.shape, -1)
        for j in range(k):
            f = ndi.uniform_filter(((L == j) & ~hole).astype(np.float64), 5)
            upd = f > best
            best[upd] = f[upd]
            arg[upd] = j
        fill = h & (arg >= 0)
        L[fill] = arg[fill]
        hole = hole & ~fill
    return L


def _cluster(sm, sel, k, probes):
    """k-means over the selected pixels; every cluster takes the target of its nearest probe (None = absorb)"""
    F = _opp(sm)
    C = _kmeans(F[sel][::5], k)
    lab = np.full(sel.shape, -1)
    lab[sel] = ((F[sel][:, None, :] - C[None]) ** 2).sum(-1).argmin(1)
    out = []
    for j in range(k):
        cj = lab == j
        if not cj.any():
            out.append(None)
            continue
        c = sm[cj].mean(0)
        best = min(probes, key=lambda p: float(((_opp(np.array(p[0], float) / 255) - _opp(c)) ** 2).sum()))
        out.append(best[1])
    return lab, out


def regions(buf, st):
    """flat colour regions: smoothed albedo -> k-means (per material group) -> art-directed targets -> wear
    absorbed -> merged by colour -> small islands absorbed."""
    m, alb, mat = buf['m'], buf['alb'], buf['mat']
    med = st.get('med', 9)
    sm = np.stack([ndi.median_filter(alb[..., c], size=med) for c in range(3)], -1)
    uniq = []
    L2 = np.full(m.shape, -1)
    over = st.get('mat_colour', {})
    groups = st.get('groups') or [dict(mats=None, k=st['k'], probes=st['probes'], maj=st.get('maj', 15))]
    claimed = np.zeros(m.shape, bool)
    for mi, t in over.items():
        claimed |= m & (mat == mi)
    for g in groups:
        sel = m & ~claimed if g['mats'] is None else m & np.isin(mat, g['mats'])
        if not sel.any():
            continue
        lab, targets = _cluster(sm, sel, g['k'], g['probes'])
        lab = _majority(lab, sel, g['k'], g.get('maj', 15))
        for j, t in enumerate(targets):
            if t is None:
                continue
            if t not in uniq:
                uniq.append(t)
            L2[sel & (lab == j)] = uniq.index(t)
        claimed |= sel
    for mi, t in over.items():                    # whole materials painted one colour (iron, forged blades, leather)
        if t not in uniq:
            uniq.append(t)
        L2[m & (mat == mi)] = uniq.index(t)
    K = len(uniq)
    L2 = _fill_holes(L2, m, m & (L2 < 0), K)
    L2 = _majority(L2, m, K, st.get('maj2', 9))
    minA = st.get('min_area', 1400)
    by = st.get('min_area_by', {})
    keep = st.get('keep_mats', ())
    for _ in range(3):
        small_any = np.zeros(m.shape, bool)
        for j in range(K):
            lab, nl = ndi.label(L2 == j)
            if nl == 0:
                continue
            sizes = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, nl + 1))
            small = np.isin(lab, np.nonzero(sizes < by.get(uniq[j], minA))[0] + 1)
            if keep:
                small &= ~np.isin(mat, keep)
            small_any |= small
        if not small_any.any():
            break
        L2 = _fill_holes(L2, m, small_any, K)
    return L2, uniq


def stylize(buf, st):
    m, n = buf['m'], buf['n']
    H, W = m.shape
    L, targets = regions(buf, st)
    base = np.zeros((H, W, 3))
    for j, t in enumerate(targets):
        base[L == j] = np.array(t, float) / 255
    Ld = np.array(st.get('light', (-0.35, 0.75, 0.55)), float)
    Ld /= np.linalg.norm(Ld)
    ndl = (n * Ld).sum(-1)
    band = np.where(ndl < st.get('t1', 0.12), 0, np.where(ndl < st.get('t2', 0.66), 1, 2))
    band = np.where(n[..., 1] > st.get('top_y', 0.42), 2, band)
    band = np.where(n[..., 1] < st.get('bot_y', -0.45), 0, band)
    band = np.where(m, band, 1)
    band = ndi.median_filter(band, size=7)
    mult = np.array(st.get('mult', (0.70, 1.0, 1.20)))
    mm = mult[band]
    for mi, mt in st.get('mult_by_mat', {}).items():
        sel = buf['mat'] == mi
        mm = np.where(sel, np.array(mt)[band], mm)
    col = base * mm[..., None]
    hl = (band == 2)[..., None]
    col = np.where(hl, col * 0.88 + np.array(st.get('hl_tint', (0.32, 0.36, 0.42))) * 0.12 + st.get('hl_add', 0.02), col)
    for mi, (rgb, glow) in st.get('emit', {}).items():           # self-lit parts keep their own colour
        sel = m & (buf['mat'] == mi)
        col[sel] = np.array(rgb, float) / 255
    # lines
    Lb = np.where(m, L, -1)
    edge = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0)):
        b2 = np.roll(np.roll(Lb, -dy, 0), -dx, 1)
        edge |= (Lb != b2) & (Lb >= 0) & (b2 >= 0)
    edge = ndi.binary_dilation(edge, _disk(st.get('panel_w', 1))) & m
    D = buf['dep']
    dz = np.full((H, W), float(st.get('dz', 0.6)))
    for mi, v in st.get('dz_by_mat', {}).items():
        dz[buf['mat'] == mi] = v
    far = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        D2 = np.roll(np.roll(D, -dy, 0), -dx, 1)
        m2 = np.roll(np.roll(m, -dy, 0), -dx, 1)
        jump = m & m2 & (np.abs(D - D2) > np.maximum(dz, np.roll(np.roll(dz, -dy, 0), -dx, 1)))
        far |= jump & (D < D2)
        far |= np.roll(np.roll(jump & (D2 < D), dy, 0), dx, 1)
    crease = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0)):
        n2 = np.roll(np.roll(n, -dy, 0), -dx, 1)
        m2 = np.roll(np.roll(m, -dy, 0), -dx, 1)
        crease |= m & m2 & ((n * n2).sum(-1) < st.get('crease_cos', 0.45))
    for mi in st.get('no_crease_mats', ()):
        crease &= buf['mat'] != mi
    inner = ndi.binary_dilation(far, _disk(st.get('inner_w', 2))) & m
    crease = ndi.binary_dilation(crease, _disk(1)) & m
    line = np.array(st.get('line', LINE), float) / 255
    col = np.where(edge[..., None], col * 0.58, col)
    col = np.where(crease[..., None], col * 0.66, col)
    col = np.where(inner[..., None], line, col)
    rw = st.get('rim_w', 4)
    if rw:
        up = np.zeros((H, W), bool)
        for k in range(1, rw + 1):
            up |= ~np.roll(m, k, 0)
        rim = m & up & (n[..., 1] > -0.2) & ~inner
        col = np.where(rim[..., None], np.array(st.get('rim', (244, 164, 84)), float) / 255, col)
    ow = st.get('outline_w', 9)
    om = ndi.binary_dilation(m, _disk(ow)) if ow else m
    rgb = np.where(m[..., None], col, line)
    return np.dstack([np.clip(rgb, 0, 1), om.astype(np.float64)])


def down(arr, ss=SS):
    """premultiplied LANCZOS downsample of a float RGBA array -> 8-bit PIL RGBA"""
    pm = arr.copy()
    pm[..., :3] *= pm[..., 3:]
    big = Image.fromarray(np.clip(np.rint(pm * 255), 0, 255).astype(np.uint8), 'RGBA')
    W, H = big.size
    sm = np.asarray(big.resize((W // ss, H // ss), Image.LANCZOS)).astype(np.float64) / 255
    al = sm[..., 3:]
    rgb = np.where(al > 1e-4, sm[..., :3] / np.maximum(al, 1e-4), 0)
    return Image.fromarray(np.clip(np.rint(np.dstack([rgb, al]) * 255), 0, 255).astype(np.uint8), 'RGBA')

# --------------------------------------------------------------------------------- the card2 background

BG_DONOR_FILE = os.path.join(SRC, 'bg_donors.json')


def moon_side(a):
    """the two card2 background templates differ only by the moon's corner: L (top-left) or R (top-right)"""
    return 'L' if a[28, 120, 1] >= 60 else 'R'


def derive_bg():
    names = sorted(os.path.basename(p)[:-4] for p in glob.glob(artgen.shipped('i_tod_card2_art_*')))
    names = [n for n in names if n not in CARD2]
    donors = {}
    groups = {'L': [], 'R': []}
    for n in names:
        p = artgen.shipped(n)
        donors[n] = sha256(p)
        a = np.asarray(Image.open(p).convert('RGB')).astype(np.int64)
        groups[moon_side(a)].append(a)
    for side, arrs in groups.items():
        G = np.stack(arrs)
        key = (G[..., 0] << 16) | (G[..., 1] << 8) | G[..., 2]
        srt = np.sort(key, axis=0)
        best = srt[0].copy()
        bestc = np.ones(best.shape, np.int64)
        run = np.ones(best.shape, np.int64)
        for k in range(1, len(arrs)):
            run = np.where(srt[k] == srt[k - 1], run + 1, 1)
            upd = run > bestc
            bestc = np.where(upd, run, bestc)
            best = np.where(upd, srt[k], best)
        T = np.stack([(best >> 16) & 255, (best >> 8) & 255, best & 255], -1)
        artgen.save_png(Image.fromarray(clean_template(T, side).astype(np.uint8), 'RGB').convert('RGBA'),
                        os.path.join(SRC, 'card2_bg_%s.png' % side))
    with open(BG_DONOR_FILE, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(note='--derive-bg donors: every shipped card2 illustration except the three this pack '
                            'replaces, as shipped on 2026-10-04 (sha256)', donors=donors), f, indent=1, sort_keys=True)
        f.write('\n')
    print('card2 background templates <- %d donors (L %d / R %d)' % (len(names), len(groups['L']), len(groups['R'])))


def clean_template(T, side):
    """the mode keeps whatever 2+ cards share, so outline navy and a few subject colours survive in the middle:
    the background is ROW-CONSTANT between the vignette edges (x 96..480) except under the moon, so every pixel
    there is set back to its row's value; the edge columns follow a per-column vignette ratio."""
    T = T.astype(np.int64)
    H, W, _ = T.shape
    key = (T[..., 0] << 16) | (T[..., 1] << 8) | T[..., 2]
    C = np.zeros((H, 3), np.int64)
    for y in range(H):
        strip = np.concatenate([key[y, 98:112], key[y, 464:478]])
        vals, cnt = np.unique(strip, return_counts=True)
        k = vals[cnt.argmax()]
        C[y] = [(k >> 16) & 255, (k >> 8) & 255, k & 255]
    moon = np.zeros((H, W), bool)
    if side == 'L':
        moon[:122, :262] = True
    else:
        moon[:122, 314:] = True
    out = T.copy()
    band = np.zeros((H, W), bool)
    band[:, 96:481] = True
    fix = band & ~moon & (np.abs(T - C[:, None, :]).max(-1) > 2)
    out[fix] = np.broadcast_to(C[:, None, :], T.shape)[fix]
    rows = np.r_[124:180, 330:446]
    Cf = np.maximum(C, 1).astype(np.float64)
    V = np.median(T[rows].astype(np.float64) / Cf[rows][:, None, :], axis=0)
    P = np.clip(np.rint(Cf[:, None, :] * V[None, :, :]), 0, 255).astype(np.int64)
    fix2 = ~band & ~moon & (np.abs(T - P).max(-1) > 5)
    out[fix2] = P[fix2]
    return out


DARK = (4, 6, 14)


def pip(img, x, y, core, rgb):
    """the family's square pip: 2 px navy border, a 1 px darkened ring, the colour core"""
    d = ImageDraw.Draw(img)
    tot = core + 6
    c = np.array(rgb, float)
    d.rectangle([x, y, x + tot - 1, y + tot - 1], fill=DARK + (255,))
    d.rectangle([x + 2, y + 2, x + tot - 3, y + tot - 3], fill=tuple(int(v * 0.53) for v in c) + (255,))
    for px, py in ((x + 2, y + 2), (x + tot - 3, y + 2), (x + 2, y + tot - 3), (x + tot - 3, y + tot - 3)):
        d.point((px, py), fill=tuple(int(v * 0.23) for v in c) + (255,))
    d.rectangle([x + 3, y + 3, x + 2 + core, y + 2 + core], fill=tuple(rgb) + (255,))


def sparkle(img, cx, cy, rv, rh, ss=4):
    W, H = img.size
    lay = Image.new('L', (W * ss, H * ss), 0)
    d = ImageDraw.Draw(lay)
    X, Y, w = cx * ss, cy * ss, 2.2 * ss
    d.polygon([(X, Y - rv * ss), (X + w, Y), (X, Y + rv * ss), (X - w, Y)], fill=255)
    d.polygon([(X - rh * ss, Y), (X, Y - w * 0.9), (X + rh * ss, Y), (X, Y + w * 0.9)], fill=255)
    lay = lay.resize((W, H), Image.LANCZOS)
    glow = np.asarray(lay.filter(ImageFilter.GaussianBlur(1.6))).astype(np.float64) * 0.6
    a = np.maximum(np.asarray(lay).astype(np.float64), glow)[..., None] / 255
    base = np.asarray(img).astype(np.float64)
    base[..., :3] = base[..., :3] * (1 - a) + 255 * a
    return Image.fromarray(np.rint(base).astype(np.uint8), 'RGBA')


def blobs(img, shapes, delta=(9, 16, 12), ss=4):
    """the family's faint lighter shapes behind the subject (+9 / +16 / +12, a soft edge)"""
    W, H = img.size
    lay = Image.new('L', (W * ss, H * ss), 0)
    d = ImageDraw.Draw(lay)
    for sh in shapes:
        if sh[0] in ('e', '-e'):
            d.ellipse([v * ss for v in sh[1:]], fill=255 if sh[0] == 'e' else 0)
        else:
            d.polygon([(x * ss, y * ss) for x, y in sh[1]], fill=255)
    lay = lay.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.0))
    a = np.asarray(lay).astype(np.float64)[..., None] / 255
    base = np.asarray(img).astype(np.float64)
    base[..., :3] = np.clip(base[..., :3] + np.array(delta, float) * a, 0, 255)
    return Image.fromarray(np.rint(base).astype(np.uint8), 'RGBA')


def glow(img, alpha_src, rgb, strength, radius, gain=1.6):
    a = np.asarray(alpha_src).astype(np.float64) / 255 if not isinstance(alpha_src, np.ndarray) else alpha_src
    g = np.clip(ndi.gaussian_filter(a, radius) * gain, 0, 1) * strength
    base = np.asarray(img).astype(np.float64)
    base[..., :3] = base[..., :3] * (1 - g[..., None]) + np.array(rgb, float) * g[..., None]
    return Image.fromarray(np.rint(base).astype(np.uint8), 'RGBA')

# --------------------------------------------------------------------------------------------- the styles

PK_STYLE = dict(
    k=12, med=9, maj=15, rim=(244, 164, 84), min_area_by={(178, 188, 204): 200},
    probes=[((12, 11, 11), (54, 56, 70)),         # the blued lever loop and trigger (small grime spots are absorbed)
            ((40, 37, 35), (74, 74, 88)),         # the stock's polymer and the shroud's dark metal
            ((43, 44, 43), (74, 74, 88)),
            ((39, 35, 33), (74, 74, 88)),
            ((52, 58, 62), (112, 136, 160)),      # the blue-grey receiver
            ((46, 62, 53), (58, 160, 140)),       # the teal grip wrap
            ((68, 72, 77), (178, 188, 204)),      # bare steel: the shell holders, the lever plate, the sight
            ((72, 64, 50), (206, 172, 112)),      # the tan cheek pad, the loop grip and the tube sleeve
            ((55, 49, 39), (74, 74, 88)),         # the lever's blued metal
            ((46, 52, 42), None)])

STAFF_STYLE = dict(
    med=7, rim=(150, 255, 170), rim_w=3, min_area=900,
    groups=[dict(mats=(4,), k=6, maj=9, probes=[      # the skull: the bone texture's own painted sockets and shading
        ((15, 10, 4), (44, 32, 34)), ((38, 29, 17), (44, 32, 34)),     # sockets, nose, the gaps between the teeth
        ((80, 73, 57), (232, 220, 190)), ((84, 74, 56), (232, 220, 190)),   # the bone is ONE ivory: the light
        ((103, 92, 71), (232, 220, 190)), ((141, 131, 109), (232, 220, 190))])],   # bands carry its form
    min_area_by={(44, 32, 34): 120},
    dz_by_mat={4: 1.4, 2: 1.4}, mult_by_mat={4: (0.84, 1.0, 1.06), 2: (1.0, 1.0, 1.0)},
    mat_colour={2: (44, 32, 34),                               # the skull's crevices: as dark as its sockets
                1: (98, 104, 128), 3: (80, 86, 108), 0: (126, 96, 72)},   # forged blades, the iron, the leather
    emit={5: ((255, 255, 255), True)},                        # the soul-lit eyes
    keep_mats=(5,), crease_cos=0.30, no_crease_mats=(4,))

MOZ_STYLE = dict(
    k=9, med=7, maj=13, outline_w=5, inner_w=1, rim=(214, 128, 124), rim_w=3, min_area=500,
    mult=(0.74, 1.0, 1.32), hl_add=0.07,
    probes=[((12, 12, 12), (40, 42, 50)),         # the black frame
            ((30, 30, 30), (52, 54, 64)),
            ((120, 108, 70), (196, 172, 116)),    # the tan shroud
            ((90, 80, 55), (196, 172, 116)),
            ((60, 58, 48), (104, 100, 84)),       # the grip panel
            ((140, 30, 30), (204, 52, 52))],      # the red details
    light=(0.45, 0.7, 0.55))

# --------------------------------------------------------------------------------------------- build

def subject_img(name, style):
    return down(stylize(load_buffers(name), style))


def card_pk():
    bg = Image.open(os.path.join(SRC, 'card2_bg_R.png')).convert('RGBA')
    subj = subject_img('pk', PK_STYLE)
    bg = blobs(bg, [('e', 90, 250, 260, 400), ('e', 170, 300, 330, 430), ('-e', 120, 330, 230, 450),
                    ('p', [(380, 340), (470, 300), (560, 330), (520, 420), (420, 430)])])
    bg = glow(bg, subj.split()[3], (150, 200, 255), 0.22, 10)
    for x, y, c, col in [(292, 28, 8, (69, 230, 255)), (322, 402, 8, (69, 230, 255)), (541, 243, 6, (255, 225, 29)),
                         (53, 397, 6, (255, 225, 29)), (53, 37, 6, (255, 255, 255))]:
        pip(bg, x, y, c, col)
    bg = sparkle(bg, 250, 80, 10, 8)
    bg = sparkle(bg, 520, 110, 7, 5)
    bg.alpha_composite(subj)
    return bg


def eye_glow(img, name, rgb, strength, radius):
    mat = np.asarray(Image.open(os.path.join(SRC, name + '_mat.png'))).astype(np.int64)
    alb = np.asarray(Image.open(os.path.join(SRC, name + '_albedo.png')).convert('RGBA'))[..., 3] > 127
    eyes = ((mat == 5) & alb).astype(np.float64)
    eyes = np.asarray(Image.fromarray((eyes * 255).astype(np.uint8)).resize(img.size, Image.LANCZOS)).astype(np.float64) / 255
    out = glow(img, eyes, rgb, strength, radius, gain=8.0)
    core = np.clip(eyes * 1.4, 0, 1)[..., None]                 # the eye itself stays white-hot over its glow
    base = np.asarray(out).astype(np.float64)
    base[..., :3] = base[..., :3] * (1 - core) + 255 * core
    return Image.fromarray(np.rint(base).astype(np.uint8), 'RGBA')


def card_staff(name, side, blob_shapes, pips, sparks, halo_r):
    bg = Image.open(os.path.join(SRC, 'card2_bg_%s.png' % side)).convert('RGBA')
    subj = subject_img(name, STAFF_STYLE)
    bg = blobs(bg, blob_shapes)
    bg = glow(bg, subj.split()[3], (120, 255, 150), 0.30, halo_r)
    for x, y, c, col in pips:
        pip(bg, x, y, c, col)
    for cx, cy, rv, rh in sparks:
        bg = sparkle(bg, cx, cy, rv, rh)
    bg.alpha_composite(subj)
    bg = eye_glow(bg, name, (150, 255, 180), 0.55, 7)
    return bg


def card_staff2():
    return card_staff('staff2', 'R',
                      [('e', 230, 120, 470, 330), ('-e', 300, 170, 430, 300), ('e', 60, 300, 230, 420)],
                      [(292, 28, 8, (69, 230, 255)), (322, 402, 8, (69, 230, 255)), (541, 243, 6, (255, 225, 29)),
                       (53, 397, 6, (255, 225, 29)), (53, 37, 6, (255, 255, 255))],
                      [(250, 80, 10, 8), (520, 110, 7, 5), (110, 190, 7, 5)], 14)


def card_staff3():
    return card_staff('staff3', 'L',
                      [('e', 330, 260, 560, 440), ('-e', 380, 300, 520, 450), ('e', 40, 160, 160, 300)],
                      [(292, 28, 8, (69, 230, 255)), (322, 402, 8, (69, 230, 255)), (541, 243, 6, (255, 225, 29)),
                       (53, 397, 6, (255, 225, 29)), (531, 33, 6, (255, 255, 255))],
                      [(70, 95, 9, 7), (520, 150, 7, 5)], 16)

# ---------------------------------------------------------------------------------- the class card window

WIN = (100, 172)                                   # the 2x canvas's origin on the card (card px)
WIN_HOLE = (186, 336, 590, 566, 60)                # the old gun + its glow, a rounded rect (card px)


def harmonic_fill(img, hole):
    import scipy.sparse as sp
    import scipy.sparse.linalg as spl
    H, W = hole.shape
    ys, xs = np.nonzero(hole)
    n = len(ys)
    idx = -np.ones((H, W), int)
    idx[ys, xs] = np.arange(n)
    rows, cols, vals = [], [], []
    B = np.zeros((n, img.shape[2]))
    for k, (y, x) in enumerate(zip(ys, xs)):
        cnt = 0
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            yy, xx = y + dy, x + dx
            if not (0 <= yy < H and 0 <= xx < W):
                continue
            cnt += 1
            if hole[yy, xx]:
                rows.append(k); cols.append(idx[yy, xx]); vals.append(-1.0)
            else:
                B[k] += img[yy, xx]
        rows.append(k); cols.append(k); vals.append(float(cnt))
    A = sp.csr_matrix((vals, (rows, cols)), shape=(n, n))
    solve = spl.factorized(A.tocsc())
    out = img.copy()
    for c in range(img.shape[2]):
        out[ys, xs, c] = solve(B[:, c])
    return out


def erase_window(card, hole, win=(104, 176, 664, 638), period=40, phase=2):
    """lift the old art out of the window: take the 40-px hairlines off, fill the hole from its rim, put the
    hairlines back across it (their per-row profile read beside the hole). Pixels outside `hole` keep their byte."""
    a = np.asarray(card).astype(np.float64)
    rgb = a[..., :3].copy()
    x0, y0, x1, y1 = win
    lines = [y for y in range(y0 + 3, y1 - 3) if (y - phase) % period == 0]
    base = rgb.copy()
    prof = {}
    for y in lines:
        for yy in (y - 1, y, y + 1):
            t = (yy - (y - 2)) / 4.0
            ip = rgb[y - 2] * (1 - t) + rgb[y + 2] * t
            prof[yy] = rgb[yy] - ip
            base[yy, x0:x1] = ip[x0:x1]
    filled = harmonic_fill(base, hole)
    out = filled.copy()
    for yy, p in prof.items():
        hx = np.nonzero(hole[yy])[0]
        if len(hx) == 0:
            continue
        Lp = p[max(x0, hx.min() - 24):hx.min() - 2].mean(0)
        Rp = p[hx.max() + 3:min(x1, hx.max() + 25)].mean(0)
        t = ((hx - hx.min()) / max(1, hx.max() - hx.min()))[:, None]
        out[yy, hx] = filled[yy, hx] + Lp * (1 - t) + Rp * t
    res = a.copy()
    res[..., :3] = np.where(hole[..., None], out, rgb)
    return np.clip(np.rint(res), 0, 255).astype(np.uint8)


def paint_class_heavy_window(card):
    """THE ENTRY POINT PK01 CALLS: the Mozambique drawn into the class card's art window. Only pixels inside the
    old gun's hole and the new gun's glow change."""
    card = card.convert('RGBA')
    W, H = card.size
    x0, y0, x1, y1, r = WIN_HOLE
    hm = Image.new('L', (W, H), 0)
    ImageDraw.Draw(hm).rounded_rectangle([x0, y0, x1, y1], radius=r, fill=255)
    hole = np.asarray(hm) > 0
    out = Image.fromarray(erase_window(card, hole), 'RGBA')
    subj = subject_img('moz', MOZ_STYLE)            # 568 x 468, the window at 1x
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    lay.paste(subj, WIN)
    a = np.asarray(lay.split()[3]).astype(np.float64) / 255
    g1 = np.clip(ndi.gaussian_filter(a, 16) * 1.5, 0, 1) * 0.55        # the Breacher's orange glow, as before
    g2 = np.clip(ndi.gaussian_filter(a, 4) * 1.6, 0, 1) * 0.50
    base = np.asarray(out).astype(np.float64)
    for g, rgb in ((g1, (190, 104, 30)), (g2, (255, 150, 52))):
        base[..., :3] = base[..., :3] * (1 - g[..., None]) + np.array(rgb, float) * g[..., None]
    out = Image.fromarray(np.rint(base).astype(np.uint8), 'RGBA')
    out.alpha_composite(lay)
    # the card's own alpha (rounded corners) is kept byte for byte
    out.putalpha(card.split()[3])
    return out


def load_class_base():
    if not os.path.isfile(CLASS_BASE):
        raise SystemExit('R2: missing %s (copy the shipped %s.png there; it is PK01\'s output)' % (CLASS_BASE, CLASS))
    got = sha256(CLASS_BASE)
    if got != CLASS_BASE_SHA:
        raise SystemExit('R2: %s is not the pinned PK01 output (sha256 %s)' % (CLASS_BASE, got))
    return Image.open(CLASS_BASE).convert('RGBA')


def build_all():
    return {
        'i_tod_card2_art_tier_heavy_3': card_pk(),
        'i_tod_card2_art_tier_necromancer_2': card_staff2(),
        'i_tod_card2_art_tier_necromancer_3': card_staff3(),
    }

# --------------------------------------------------------------------------------------------- review

def review(imgs):
    """_review.png: each new image beside the one it replaces and the model it is drawn from, then all of them at
    their on-screen size (1080p: a card2 illustration 263x205 inside its 351x527 card; the class card 315x472)."""
    rows = []
    sub = {'i_tod_card2_art_tier_heavy_3': 'pk', 'i_tod_card2_art_tier_necromancer_2': 'staff2',
           'i_tod_card2_art_tier_necromancer_3': 'staff3'}
    for n in CARD2:
        old = Image.open(os.path.join(SRC, n + '_was.png')).convert('RGBA') if os.path.isfile(os.path.join(SRC, n + '_was.png')) \
            else Image.open(artgen.shipped(n)).convert('RGBA')
        truth = Image.open(os.path.join(SRC, sub[n] + '_truth.png')).convert('RGBA')
        rows.append(('%s   was | now | the model (render)' % n, [old, imgs[n], truth]))
    has_cls = CLASS in imgs                       # False since R6 took the class card
    if has_cls:
        was = Image.open(CLASS_BASE).convert('RGBA')
        rows.append(('%s art window   was | now | the model (render)' % CLASS,
                     [was.crop((100, 172, 668, 640)), imgs[CLASS].crop((100, 172, 668, 640)),
                      Image.open(os.path.join(SRC, 'moz_truth.png')).convert('RGBA')]))
    p1 = os.path.join(OUT, '_review_big.png')
    artgen.contact_sheet(rows, p1, height=300)
    # on-screen sizes, on the panel's dark ground: the card2 art at 263x205, the class card at 315x472
    small = [imgs[n].resize((263, 205), Image.LANCZOS) for n in CARD2]
    if has_cls:
        cls = imgs[CLASS].resize((315, 472), Image.LANCZOS)
        oldcls = was.resize((315, 472), Image.LANCZOS)
    oldsmall = [(Image.open(os.path.join(SRC, n + '_was.png')) if os.path.isfile(os.path.join(SRC, n + '_was.png'))
                 else Image.open(artgen.shipped(n))).convert('RGBA').resize((263, 205), Image.LANCZOS) for n in CARD2]
    big = Image.open(p1).convert('RGBA')
    Wd = max(big.width, 12 + 3 * (263 + 12) + 2 * (315 + 12))
    sheet = Image.new('RGBA', (Wd, big.height + 30 + 205 * 2 + 36 + 12), (20, 22, 30, 255))
    sheet.alpha_composite(big, (0, 0))
    d = ImageDraw.Draw(sheet)
    y = big.height + 8
    d.text((12, y), 'ON SCREEN (1080p): card2 art 263x205 (top was, bottom now) | class card 315x472 (was, now)',
           fill=(220, 225, 235, 255), font=artgen.ttf(16))
    y += 26
    for i in range(3):
        sheet.alpha_composite(oldsmall[i], (12 + i * 275, y))
        sheet.alpha_composite(small[i], (12 + i * 275, y + 205 + 8))
    xo = 12 + 3 * 275
    if has_cls:
        sheet.alpha_composite(oldcls.crop((0, 0, 315, 205 * 2 + 8)), (xo, y))
        sheet.alpha_composite(cls.crop((0, 0, 315, 205 * 2 + 8)), (xo + 327, y))
    sheet = _review_cursed(sheet)
    out = os.path.join(OUT, '_review.png')
    sheet.save(out)
    os.remove(p1)
    return out


CURSED = ['i_tod_spin_tile_cursed', 'i_tod_spin_banner_cursed', 'i_tod_spin_ico_cursed']
CURSED_DIR = os.path.join(OUT, 'cursed', IMG_REL)        # the staged tools/dealer_house/make_spin_art.py --out art/generated/R2-card-subjects/cursed


def _review_cursed(sheet):
    """THE CURSED REEL SET (the staged make_spin_art.py's output, when present): was | now at full size, then the
    tile (with the mask in its window) at 210x156 and the stamp at 780x102 - the reel's 1080p sizes (TILE_W/H 140x104,
    the cursed banner BANNER_X0-60..X1+60 x Y0-8..Y1+8 = 520x68 canvas units)."""
    if not all(os.path.isfile(os.path.join(CURSED_DIR, n + '.png')) for n in CURSED):
        return sheet
    was_dir = os.path.join(ROOT, 'tmp', 'redesign', PACK, 'base', IMG_REL)
    if not os.path.isdir(was_dir):
        was_dir = os.path.join(ROOT, IMG_REL)

    def tile(d):
        t = Image.open(os.path.join(d, 'i_tod_spin_tile_cursed.png')).convert('RGBA').copy()
        t.alpha_composite(Image.open(os.path.join(d, 'i_tod_spin_ico_cursed.png')).convert('RGBA'), (176, 32))
        return t
    wt, nt = tile(was_dir), tile(CURSED_DIR)
    wb = Image.open(os.path.join(was_dir, 'i_tod_spin_banner_cursed.png')).convert('RGBA')
    nb = Image.open(os.path.join(CURSED_DIR, 'i_tod_spin_banner_cursed.png')).convert('RGBA')
    leg = Image.open(artgen.shipped('i_tod_spin_tile_legendary')).convert('RGBA')
    legb = Image.open(artgen.shipped('i_tod_spin_banner_legendary')).convert('RGBA')
    H = 30 + 416 + 20 + 208 * 3 + 40 + 30 + 156 + 20 + 102 * 2 + 30
    W = max(sheet.width, 12 + 570 * 3)
    out = Image.new('RGBA', (W, sheet.height + H), (20, 22, 30, 255))
    out.alpha_composite(sheet, (0, 0))
    d = ImageDraw.Draw(out)
    f = artgen.ttf(16)
    y = sheet.height + 8
    d.text((12, y), 'THE CURSED REEL SET (tools/dealer_house/make_spin_art.py, staged): legendary ref | was | now '
                    '(the tile with the mask icon in its window)', fill=(220, 225, 235, 255), font=f)
    y += 24
    out.alpha_composite(leg, (12, y))
    out.alpha_composite(wt, (12 + 570, y))
    out.alpha_composite(nt, (12 + 1140, y))
    y += 416 + 20
    for im in (legb, wb, nb):
        out.alpha_composite(im, (12, y))
        y += 208
    y += 16
    d = ImageDraw.Draw(out)
    d.text((12, y), 'ON SCREEN (1080p): tile 210x156, was | now;  stamp 780x102, was / now', fill=(220, 225, 235, 255), font=f)
    y += 26
    out.alpha_composite(wt.resize((210, 156), Image.LANCZOS), (12, y))
    out.alpha_composite(nt.resize((210, 156), Image.LANCZOS), (240, y))
    y += 156 + 20
    out.alpha_composite(wb.resize((780, 102), Image.LANCZOS), (12, y))
    out.alpha_composite(nb.resize((780, 102), Image.LANCZOS), (12, y + 106))
    return out

# --------------------------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--render', action='store_true')
    ap.add_argument('--derive-bg', action='store_true')
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--stage', help='also write the PNGs under DIR/source_data/tod_ui_images/_images/')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--root', help='with --check: read DIR/... instead of the repo')
    a = ap.parse_args()
    if a.render:
        meta = {}
        for n in SUBJECTS:
            meta[n] = render_subject(n)
            print('rendered', n, meta[n]['triangles'], 'triangles')
        with open(os.path.join(SRC, 'render.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(meta, f, indent=1, sort_keys=True)
            f.write('\n')
        return
    if a.derive_bg:
        derive_bg()
        return
    imgs = build_all()
    if a.check:
        root = a.root or ROOT
        bad = []
        for n in NAMES:
            p = os.path.join(root, IMG_REL, n + '.png')
            if not os.path.isfile(p):
                bad.append('MISSING %s' % p)
            elif open(p, 'rb').read() != artgen.png_bytes(imgs[n]):
                bad.append('STALE %s (re-run tools/artgen/packs/r2_card_subjects.py --install; never hand-edit it)' % p)
        if bad:
            for b in bad:
                print('R2 CARD SUBJECTS: ' + b)
            sys.exit(1)
        print('R2 CARD SUBJECTS OK (%d images byte-exact)' % len(NAMES))
        return
    for n, im in imgs.items():
        md5 = artgen.save_png(im, os.path.join(OUT, n + '.png'))
        print('%-38s %dx%d  %s' % (n, im.width, im.height, md5))
    for root in ([a.stage] if a.stage else []) + ([ROOT] if a.install else []):
        for n, im in imgs.items():
            artgen.save_png(im, os.path.join(root, IMG_REL, n + '.png'))
    print('review ->', review(imgs))


if __name__ == '__main__':
    main()
