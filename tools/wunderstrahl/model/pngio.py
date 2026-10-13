"""Deterministic 8-bit PNG writer (zlib level 9, per-image best of the Sub/Up filters) and a Blender-side reader.

Writing our own encoder keeps every generated texture byte-stable run to run, so install_art.py --check can pin
them by sha256. Reading uses Blender's loader when bpy is present (raw stored values, no colour management) and
PIL otherwise (plain-Python verify/install steps)."""
import struct, zlib
import numpy as np


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def write_png(path, a):
    """a: float 0..1 or uint8, shape (h, w) or (h, w, c) with c in 1..4. Row 0 = top of the image."""
    a = np.asarray(a)
    if a.dtype != np.uint8:
        a = np.clip(np.round(a.astype(np.float64) * 255.0), 0, 255).astype(np.uint8)
    if a.ndim == 2:
        a = a[:, :, None]
    h, w, c = a.shape
    ctype = {1: 0, 2: 4, 3: 2, 4: 6}[c]
    rows = a.reshape(h, w * c).astype(np.int16)
    sub = rows.copy(); sub[:, c:] = rows[:, c:] - rows[:, :-c]
    up = rows.copy(); up[1:] = rows[1:] - rows[:-1]
    best = []
    for y in range(h):
        s = np.abs(((sub[y] + 128) % 256) - 128).sum(); u = np.abs(((up[y] + 128) % 256) - 128).sum()
        best.append((1, sub[y]) if s <= u else (2, up[y]))
    raw = b''.join(bytes([kind]) + (row % 256).astype(np.uint8).tobytes() for kind, row in best)
    png = (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, ctype, 0, 0, 0)) +
           _chunk(b'IDAT', zlib.compress(raw, 9)) + _chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
    return path


def read_png(path):
    """-> float32 (h, w, 4), row 0 = top, raw stored values / 255."""
    try:
        import bpy
    except ImportError:
        bpy = None
    if bpy is not None:
        im = bpy.data.images.load(str(path), check_existing=False)
        try:
            w, h = im.size
            buf = np.empty(w * h * 4, np.float32)
            im.pixels.foreach_get(buf)
            return buf.reshape(h, w, 4)[::-1].copy()
        finally:
            bpy.data.images.remove(im)
    from PIL import Image
    im = Image.open(path).convert('RGBA')
    return np.asarray(im).astype(np.float32) / 255.0
