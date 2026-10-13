"""Pure-numpy texture authoring helpers for the Wunderstrahl surfaces (no bpy; Blender's bundled numpy runs it).

Image convention everywhere here: arrays are row 0 = TOP of the image, float32 0..1, RGB(A) last axis - the same
orientation as a PNG on disk and as native UV v (measured from the top). Colour maps are sRGB-encoded values.
"""
import math
import numpy as np


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def srgb_to_linear(c):
    c = np.asarray(c, dtype=np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, dtype=np.float32), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1.0 / 2.4) - 0.055)


def rgb(*v):
    """sRGB 0-255 triple -> float array."""
    return np.array(v, dtype=np.float32) / 255.0


def lerp(a, b, t):
    if np.ndim(t) == 2 and np.ndim(a) >= 1 and np.shape(a)[-1:] == (3,):
        t = t[..., None]
    return a + (b - a) * t


def box_blur(a, r):
    """Separable box blur with edge clamping (r in pixels)."""
    if r < 1:
        return a
    out = a.astype(np.float32)
    for axis in (0, 1):
        pad = [(0, 0)] * out.ndim
        pad[axis] = (r + 1, r)
        p = np.pad(out, pad, mode='edge')
        c = np.cumsum(p, axis=axis, dtype=np.float64)
        n = out.shape[axis]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(c, np.arange(0, n), axis=axis)
        out = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return out


def blur(a, r):
    """Gaussian-like blur: three box passes."""
    r = int(max(0, r))
    if r == 0:
        return a.astype(np.float32)
    k = max(1, int(round(r / 1.73)))
    for _ in range(3):
        a = box_blur(a, k)
    return a


def resize(a, h, w):
    """Bilinear resize (pixel-centre aligned)."""
    H, W = a.shape[:2]
    if (H, W) == (h, w):
        return a.astype(np.float32)
    ys = (np.arange(h) + 0.5) * H / h - 0.5
    xs = (np.arange(w) + 0.5) * W / w - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, H - 1); y1 = np.clip(y0 + 1, 0, H - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, W - 1); x1 = np.clip(x0 + 1, 0, W - 1)
    fy = np.clip(ys - y0, 0, 1); fx = np.clip(xs - x0, 0, 1)
    if a.ndim == 3:
        fy = fy[:, None, None]; fx = fx[None, :, None]
    else:
        fy = fy[:, None]; fx = fx[None, :]
    top = a[y0][:, x0] * (1 - fx) + a[y0][:, x1] * fx
    bot = a[y1][:, x0] * (1 - fx) + a[y1][:, x1] * fx
    return (top * (1 - fy) + bot * fy).astype(np.float32)


def value_noise(h, w, cells, seed, octaves=1):
    """Tileable-free smooth value noise in 0..1 (deterministic)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; total = 0.0
    for o in range(octaves):
        c = max(2, int(cells * (2 ** o)))
        grid = rng.random((c + 1, c + 1), dtype=np.float32)
        out += amp * resize(grid, h, w); total += amp; amp *= 0.5
    return out / total


def components(mesh):
    """3D-connected parts of a native mesh (shared vertex indices): list of face-index lists."""
    parent = list(range(len(mesh.verts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for f in mesh.faces:
        a, b, c = [x.vertex for x in f.indices]
        ra, rb, rc = find(a), find(b), find(c)
        parent[ra] = rb; parent[rc] = rb
    groups = {}
    for fi, f in enumerate(mesh.faces):
        groups.setdefault(find(f.indices[0].vertex), []).append(fi)
    return list(groups.values())


def rasterize(meshes, w, h, weld_label_offset=0):
    """Rasterise native meshes' UV triangles. Returns label (int32, -1 = empty texel; one id per 3D part across all
    given meshes), pos (h,w,3) and nrm (h,w,3) interpolated in native gun space, and per-part info dicts."""
    label = np.full((h, w), -1, np.int32)
    pos = np.zeros((h, w, 3), np.float32)
    nrm = np.zeros((h, w, 3), np.float32)
    info = []
    pid = weld_label_offset
    for mesh in meshes:
        P = np.array([v.offset for v in mesh.verts], np.float64)
        for faces in components(mesh):
            area = 0.0
            lo = np.full(3, 1e9); hi = np.full(3, -1e9)
            for fi in faces:
                f = mesh.faces[fi]
                A, B, C = [P[c.vertex] for c in f.indices]
                area += 0.5 * np.linalg.norm(np.cross(B - A, C - A))
                lo = np.minimum(lo, np.minimum(A, np.minimum(B, C))); hi = np.maximum(hi, np.maximum(A, np.maximum(B, C)))
                uv = np.array([c.uv for c in f.indices], np.float64)
                px = uv[:, 0] * w - 0.5; py = uv[:, 1] * h - 0.5
                x0 = max(int(math.floor(px.min())), 0); x1 = min(int(math.ceil(px.max())), w - 1)
                y0 = max(int(math.floor(py.min())), 0); y1 = min(int(math.ceil(py.max())), h - 1)
                if x1 < x0 or y1 < y0:
                    continue
                gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
                d = (py[1] - py[2]) * (px[0] - px[2]) + (px[2] - px[1]) * (py[0] - py[2])
                if abs(d) < 1e-12:
                    continue
                l0 = ((py[1] - py[2]) * (gx - px[2]) + (px[2] - px[1]) * (gy - py[2])) / d
                l1 = ((py[2] - py[0]) * (gx - px[2]) + (px[0] - px[2]) * (gy - py[2])) / d
                l2 = 1.0 - l0 - l1
                eps = -0.02
                inside = (l0 >= eps) & (l1 >= eps) & (l2 >= eps)
                if not inside.any():
                    continue
                yy = gy[inside]; xx = gx[inside]
                b0 = l0[inside][:, None]; b1 = l1[inside][:, None]; b2 = l2[inside][:, None]
                label[yy, xx] = pid
                pos[yy, xx] = (b0 * A + b1 * B + b2 * C).astype(np.float32)
                N = [np.array(c.normal, np.float64) for c in f.indices]
                n = b0 * N[0] + b1 * N[1] + b2 * N[2]
                n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
                nrm[yy, xx] = n.astype(np.float32)
            info.append(dict(id=pid, faces=len(faces), area=area, lo=lo.tolist(), hi=hi.tolist(),
                             diag=float(np.linalg.norm(hi - lo)), mesh=mesh.name))
            pid += 1
    return label, pos, nrm, info


def dilate(label, arrays, iters=6):
    """Grow labelled texels into empty neighbours (padding for mips/bilinear): nearest-of-4 each pass."""
    label = label.copy(); arrays = [a.copy() for a in arrays]
    for _ in range(iters):
        empty = label < 0
        if not empty.any():
            break
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            src = np.roll(label, (dy, dx), axis=(0, 1))
            take = empty & (src >= 0) & (label < 0)
            if take.any():
                label[take] = src[take]
                for a in arrays:
                    a[take] = np.roll(a, (dy, dx), axis=(0, 1))[take]
    return label, arrays


def normal_vectors(nmap):
    """DirectX tangent normal map (sRGB-free 0..1 RGB) -> unit vectors (x, y_dx, z)."""
    n = nmap[..., :3] * 2.0 - 1.0
    n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-6)
    return n


def curvature(nmap, scale=1.0):
    """Signed curvature from a DirectX tangent normal map: + on convex edges, - in creases (orientation-free)."""
    n = normal_vectors(nmap)
    dnx = np.gradient(n[..., 0], axis=1)
    dny = np.gradient(n[..., 1], axis=0)
    return (dnx + dny) * scale


def luminance(c):
    return c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722


def norm01(a, mask=None, lo_pct=2, hi_pct=98):
    vals = a[mask] if mask is not None and mask.any() else a.ravel()
    lo, hi = np.percentile(vals, lo_pct), np.percentile(vals, hi_pct)
    return np.clip((a - lo) / max(hi - lo, 1e-6), 0, 1)
