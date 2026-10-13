"""view.py - rebuild a player's view: the .map's brushes ray-cast per pixel + the sky panorama (docs/196 §3).

The library under fit.py. BO3 angles (pitch + = DOWN, yaw 0 = +X, 90 = +Y), a hor+
pinhole camera with the horizontal field of view given directly. Geometry is flat-shaded by material family
(gold / red / cyan / green / grey) - it is for SILHOUETTES, not looks.

The sky is sampled through the MEASURED engine rule: the image's centre column faces world yaw `centre`, image
right = the viewer's right, row 0 = up. For this map centre = -(SSI sun azimuth + skyRotation) - roll.
"""
import json, math, pathlib
import numpy as np
from PIL import Image

REPO = pathlib.Path(__file__).resolve().parents[3]
SKIP = {'clip', 'clip_player', 'sky', 'caulk', 'nodraw'}


def mat_color(m):
    if 'gold' in m or 'brass' in m or 'bronze' in m:
        return (0.45, 0.33, 0.12)
    if 'ruby' in m or 'red' in m or 'oxblood' in m:
        return (0.30, 0.06, 0.06)
    if 'cyan' in m or 'sapphire' in m:
        return (0.05, 0.25, 0.30)
    if 'emerald' in m or 'green' in m:
        return (0.05, 0.30, 0.10)
    return (0.18, 0.18, 0.20)


def load_brushes(path):
    B = [b for b in json.loads(pathlib.Path(path).read_text()) if not any(m in SKIP for m in b['m'])]
    K = max(len(b['p']) for b in B)
    n = np.zeros((len(B), K, 3), np.float32)
    d = np.ones((len(B), K), np.float32)          # padding planes: n = 0, d = 1 -> always satisfied
    col = np.zeros((len(B), K, 3), np.float32)
    for i, b in enumerate(B):
        for k, (p, m) in enumerate(zip(b['p'], b['m'])):
            n[i, k] = p[:3]
            d[i, k] = p[3]
            col[i, k] = mat_color(m)
    lo = np.array([b['lo'] for b in B], np.float32)
    hi = np.array([b['hi'] for b in B], np.float32)
    return n, d, col, lo, hi


def rays(W, H, yaw, pitch, hfov):
    tx = math.tan(math.radians(hfov / 2))
    ty = tx * H / W
    p, y = math.radians(pitch), math.radians(yaw)
    F = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), -math.sin(p)])
    R = np.array([math.sin(y), -math.cos(y), 0.0])
    U = np.cross(R, F)
    sx = (np.arange(W) + 0.5) / W * 2 - 1
    sy = 1 - (np.arange(H) + 0.5) / H * 2
    gx, gy = np.meshgrid(sx * tx, sy * ty)
    D = F[None, None] + gx[..., None] * R[None, None] + gy[..., None] * U[None, None]
    return D / np.linalg.norm(D, axis=2, keepdims=True)


def cast(E, D, br, tile=16):
    """-> (hit distance per pixel, inf = sky; flat colour per pixel). Convex slab test per brush, with the
    brushes culled per screen tile by their bounding spheres (~300x faster than testing all of them)."""
    n, d, col, lo, hi = br
    H, W = D.shape[:2]
    E = np.asarray(E, np.float32)
    num = d - np.einsum('bkc,c->bk', n, E)
    cen = (lo + hi) / 2
    rad = np.linalg.norm(hi - lo, axis=1) / 2
    rel = cen - E
    dist = np.linalg.norm(rel, axis=1)
    reln = rel / np.maximum(dist, 1e-3)[:, None]
    halfang = np.where(dist <= rad, np.pi, np.arcsin(np.clip(rad / np.maximum(dist, 1e-3), 0, 1)))
    T = np.full((H, W), np.inf, np.float32)
    C = np.zeros((H, W, 3), np.float32)
    light = np.array([0.3, -0.5, 0.8], np.float32)
    for y0 in range(0, H, tile):
        for x0 in range(0, W, tile):
            blk = D[y0:y0 + tile, x0:x0 + tile]
            h_, w_ = blk.shape[:2]
            dd = blk.reshape(-1, 3).astype(np.float32)
            mid = dd.mean(0)
            mid /= np.linalg.norm(mid)
            spread = np.arccos(np.clip(dd @ mid, -1, 1)).max()
            sel = np.nonzero(np.arccos(np.clip(reln @ mid, -1, 1)) - halfang <= spread + 1e-3)[0]
            if not len(sel):
                continue
            nn_, nm = n[sel], num[sel]
            den = np.einsum('rc,bkc->rbk', dd, nn_)
            with np.errstate(divide='ignore', invalid='ignore'):
                t = nm[None] / den
            ent = np.where(den < -1e-7, t, -np.inf)
            ext = np.where(den > 1e-7, t, np.inf)
            bad = ((np.abs(den) <= 1e-7) & (nm[None] < 0)).any(2)
            te, tx_ = ent.max(2), ext.min(2)
            te = np.where((te < tx_) & (tx_ > 0) & ~bad & (te > 0.5), te, np.inf)
            bi = te.argmin(1)
            r = np.arange(len(dd))
            ki = ent[r, bi].argmax(1)
            shade = 0.55 + 0.45 * np.abs(nn_[bi, ki] @ light)
            T[y0:y0 + h_, x0:x0 + w_] = te[r, bi].reshape(h_, w_)
            C[y0:y0 + h_, x0:x0 + w_] = (col[sel[bi], ki] * shade[:, None]).reshape(h_, w_, 3)
    return T, C


def sky_sample(sky, D, centre_yaw):
    """the panorama through the engine rule: the centre column (u 0.5) faces world yaw `centre_yaw`."""
    off = math.radians(centre_yaw)
    x, y, z = D[..., 0], D[..., 1], D[..., 2]
    xp = x * math.cos(off) + y * math.sin(off)
    yp = -x * math.sin(off) + y * math.cos(off)
    u = (0.5 - np.arctan2(yp, xp) / (2 * math.pi)) % 1.0
    v = np.arccos(np.clip(z, -1, 1)) / math.pi
    sh, sw = sky.shape[:2]
    return sky[np.clip((v * sh).astype(int), 0, sh - 1), np.clip((u * sw).astype(int), 0, sw - 1)]


def render(eye, yaw, pitch, hfov, W, H, br, sky, centre_yaw):
    D = rays(W, H, yaw, pitch, hfov)
    t, c = cast(eye, D, br)
    img = sky_sample(sky, D, centre_yaw).copy()
    geo = np.isfinite(t)
    img[geo] = c[geo]
    return (np.clip(img, 0, 1) * 255).astype(np.uint8), geo


def load_sky(path=None):
    p = pathlib.Path(path) if path else REPO / 'docs/sky_preview/sky3d_sky_equirect.png'
    return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
