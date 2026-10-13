"""bm_chrome.py - THE BLACK MARKET SCREEN's chrome, by THEME (RT 2026-10-05, the red return; docs/218).

THE GAP. The Black Market reel's six chrome pieces were briefed (docs/190) and delivered (2026-09-29) in the docs/184
synthwave palette - docs/188: "placeholder colours follow the synthwave theme (magenta frame/title, cyan
rules/needle/focus)". They are THEME CHROME, not the Dealer's identity (black / oxblood / red neon, docs/195): after the
red return they were the one magenta / cyan screen left, opening on every 2500-point spin. Nothing generated them, so
the shipped synthwave set is PARKED (docs/218_ref/_prev_shipped) and this tool derives each theme from it:

  THEME 'synthwave'  the parked bytes, exactly (reverting the theme restores the delivered art to the byte)
  THEME 'fallen'     each pixel re-lit by hue family, alpha untouched (the art's shapes, cut-outs and halos stay):
                     magenta (the frame light, the BLACK MARKET title) -> the Fallen red; cyan rails / rules ->
                     unlit steel; cyan FOCUS (the needle, the slot ring) -> the red; violet secondaries -> steel;
                     the SCRAP plate's cyan -> the info ice blue; the violet-black glass -> neutral charcoal.

  i_tod_spin_frame          2160 x 872   the machine (frame tube, title, rails, vents)
  i_tod_spin_glass          2000 x 224   the reel window's glass
  i_tod_spin_needle           96 x 560   the needle
  i_tod_spin_socket_focus    832 x 320   the focused slot's ring
  i_tod_spin_portrait_frame  288 x 288   the dealer / companion window frames
  i_tod_spin_scrap           800 x 288   the SCRAP slot plate

KEPT (content, never re-lit): the dealer and companion portraits, the item icons, the rarity tiles / banners / stamps,
the socket and chip (already neutral), the CURSED red, the Gift's cyan. The reel's CODE tints follow the theme too:
TodSpinReel.lua P3.THEME (focus / info / title / rails / caption) and EMPTY_RIM; --check pins them per THEME
(LUA_TINTS, with a planted-other-theme control). The companion's cyan (P3.GIFT.col, fx.comp, the FOR YOUR line) is
identity and stays.

  python tools/artgen/packs/bm_chrome.py                    # -> art/generated/BM-chrome/ (+ _review.png)
  python tools/artgen/packs/bm_chrome.py --install [--root DIR]
  python tools/artgen/packs/bm_chrome.py --check [--root DIR]      # BUILD GATE: bytes, alpha = parked, no synthwave hue
                                                                   # left under fallen, Lua tints = THEME, wiring
  python tools/artgen/packs/bm_chrome.py --selftest [--root DIR]   # negative controls (each rule must fire)

Deterministic (pure per-pixel arithmetic). Never hand-edit a generated PNG.
"""
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402
from synthwave import THEME, THEMES, hexrgb  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = artgen.ROOT
PACK = 'BM-chrome'
PARK_REL = os.path.join('docs', '218_ref', '_prev_shipped')
IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')
LUA_REL = os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodSpinReel.lua')

# the synthwave keys the delivered art was lit with (docs/184 PAL), as (hue deg, sat, val)
KEYS = {'magenta': '#FF2BD1', 'cyan': '#1FE5FF', 'violet': '#7A46FF'}
WIDTH = 40.0                       # a pixel belongs to a family by hue within this many degrees (soft)
# per image: family -> the synthwave.PAL ROLE it is re-lit to under the fallen theme
MAP = {
    'i_tod_spin_frame':          {'magenta': 'magenta', 'cyan': 'accent2', 'violet': 'violet'},
    'i_tod_spin_glass':          {'magenta': 'magenta', 'cyan': 'accent2', 'violet': 'violet'},
    'i_tod_spin_needle':         {'magenta': 'magenta', 'cyan': 'cyan', 'violet': 'violet'},
    'i_tod_spin_socket_focus':   {'magenta': 'magenta', 'cyan': 'cyan', 'violet': 'violet'},
    'i_tod_spin_portrait_frame': {'magenta': 'magenta', 'cyan': 'accent2', 'violet': 'violet'},
    'i_tod_spin_scrap':          {'magenta': 'magenta', 'cyan': 'infotext', 'violet': 'violet'},
}
NAMES = list(MAP)

# THE CODE HALF: TodSpinReel.lua's theme lines, per THEME (present), the other theme's (absent)
LUA_TINTS = {
    'fallen': ['THEME = { focus = { 0.95, 0.13, 0.23 }, info = { 0.62, 0.82, 1.0 }, title = { 0.95, 0.13, 0.23 },',
               'railTop = { 1, 0.36, 0.46 }, railLow = { 0.66, 0.70, 0.80 }, caption = { 0.66, 0.70, 0.80 } },',
               'local EMPTY_RIM = { 0.42, 0.46, 0.54 }'],
    'synthwave': ['THEME = { focus = { 0.12, 0.9, 1 }, info = { 0.12, 0.9, 1 }, title = { 1, 0.17, 0.82 },',
                  'railTop = { 1, 0.62, 1 }, railLow = { 0.6, 1, 1 }, caption = { 0.72, 0.74, 0.88 } },',
                  'local EMPTY_RIM = { 0.42, 0.40, 0.50 }'],
}


def rgb_to_hsv(rgb):
    """rgb float [0,1] (..., 3) -> h deg [0,360), s, v"""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn
    s = np.where(mx > 1e-9, d / np.maximum(mx, 1e-9), 0.0)
    dd = np.maximum(d, 1e-9)
    h = np.where(mx == r, ((g - b) / dd) % 6.0, np.where(mx == g, (b - r) / dd + 2.0, (r - g) / dd + 4.0)) * 60.0
    h = np.where(d > 1e-9, h, 0.0) % 360.0
    return h, s, mx


def hsv_to_rgb(h, s, v):
    h = (h % 360.0) / 60.0
    i = np.floor(h)
    f = h - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    i = i.astype(int) % 6
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1)


def _hsv_of(hexc):
    h, s, v = rgb_to_hsv(np.array(hexrgb(hexc), float)[None, :] / 255.0)
    return float(h[0]), float(s[0]), float(v[0])


def _hue_dist(h, k):
    d = np.abs(h - k) % 360.0
    return np.minimum(d, 360.0 - d)


def relight(im, fams, pal=None):
    """Re-light an RGBA image by hue family. Each pixel's weight in a family falls off with its hue's distance from the
    family key (WIDTH) and with low saturation; its share is re-drawn in the target role's hue with the saturation and
    value scaled as the key -> target (so a halo stays a halo and a dim edge stays dim), a target's core never whiter
    than half its saturation. What no family claims (greys, whites, near-blacks) keeps its luma and takes the Fallen
    neutral cast (R ~ G, B a touch up: synthwave._neutral's). Alpha is never touched. pal: resolve the target roles
    in that palette (default: the THEME's)."""
    a = np.asarray(im.convert('RGBA')).astype(np.float64)
    rgb = a[..., :3] / 255.0
    h, s, v = rgb_to_hsv(rgb)
    out = np.zeros_like(rgb)
    wsum = np.zeros(h.shape)
    parts = []
    for fam, key in KEYS.items():
        kh, ks, kv = _hsv_of(key)
        w = np.clip(1.0 - _hue_dist(h, kh) / WIDTH, 0.0, 1.0) * np.clip(s / 0.12, 0.0, 1.0)
        th, ts, tv = _hsv_of(pal[fams[fam]] if pal else fams[fam])
        ns = ts * (0.5 + 0.5 * np.clip(s / ks, 0.0, 1.0))
        nv = np.clip(v * tv / kv, 0.0, 1.0)
        parts.append((w, hsv_to_rgb(np.full(h.shape, th), ns, nv)))
        wsum += w
    k = np.where(wsum > 1.0, 1.0 / np.maximum(wsum, 1e-9), 1.0)
    rest = 1.0 - np.clip(wsum * k, 0.0, 1.0)
    for w, col in parts:
        out += (w * k)[..., None] * col
    L = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    neutral = np.stack([L, np.clip(L - 1 / 255.0, 0, 1), np.clip(L + 7 / 255.0 * (1.0 - L), 0, 1)], -1)
    out += rest[..., None] * neutral
    res = np.dstack([np.clip(np.round(out * 255.0), 0, 255), a[..., 3]]).astype(np.uint8)
    res[res[..., 3] == 0] = 0
    return Image.fromarray(res, 'RGBA')


def park_dir(root=None):
    for r in ([root] if root else []) + [ROOT]:
        d = os.path.join(r, PARK_REL)
        if os.path.isdir(d):
            return d
    raise SystemExit('bm_chrome: the parked delivered art (%s) is missing - it is this generator\'s source' % PARK_REL)


def build(root=None):
    """{name: exact PNG bytes} for THEME."""
    d = park_dir(root)
    out = {}
    for name in NAMES:
        src = os.path.join(d, name + '.png')
        if THEME == 'synthwave':
            with open(src, 'rb') as fh:
                out[name] = fh.read()
        else:
            out[name] = artgen.png_bytes(relight(Image.open(src), MAP[name]))
    return out


def synth_hue_left(im):
    """pixels still lit in a synthwave key hue (magenta / cyan / violet: saturated, bright, visible)"""
    a = np.asarray(im.convert('RGBA')).astype(np.float64)
    h, s, v = rgb_to_hsv(a[..., :3] / 255.0)
    vis = (a[..., 3] > 40) & (v > 0.3)
    n = 0
    for key, (tol, smin) in (('magenta', (20, 0.5)), ('cyan', (15, 0.6)), ('violet', (15, 0.5))):
        kh = _hsv_of(KEYS[key])[0]
        n += int(((_hue_dist(h, kh) < tol) & (s > smin) & vis).sum())
    return n


def lua_problems(src, theme=None):
    theme = theme or THEME
    out = []
    for nd in LUA_TINTS[theme]:
        if nd not in src:
            out.append('%s: the %s reel tint is missing: %s' % (LUA_REL, theme, nd))
    for other, needles in LUA_TINTS.items():
        if other != theme:
            for nd in needles:
                if nd in src and nd not in LUA_TINTS[theme]:
                    out.append('%s still paints the %s theme: %s' % (LUA_REL, other, nd))
    return out


def problems(root, built=None):
    root = root or ROOT
    built = built or build(root)
    out = []
    park = park_dir(root)
    import io, glob, re
    for name, data in built.items():
        p = os.path.join(root, IMG_REL, name + '.png')
        if not os.path.isfile(p):
            out.append('%s: not installed (%s)' % (name, p))
            continue
        if open(p, 'rb').read() != data:
            out.append('%s: installed PNG differs from the generator (re-run --install; never hand-edit)' % name)
        im = Image.open(io.BytesIO(data)).convert('RGBA')
        ref = Image.open(os.path.join(park, name + '.png')).convert('RGBA')
        if im.size != ref.size or not np.array_equal(np.asarray(im)[..., 3], np.asarray(ref)[..., 3]):
            out.append('%s: its alpha / size is not the delivered art\'s (the shapes must not move)' % name)
        if THEME != 'synthwave':
            n = synth_hue_left(im)
            if n:
                out.append('%s: %d pixels still lit magenta / cyan / violet under the %s theme' % (name, n, THEME))
    lua = open(os.path.join(root, LUA_REL), encoding='utf-8', errors='replace').read()
    out += lua_problems(lua)
    for name in NAMES:
        if '"%s"' % name not in lua:
            out.append('TodSpinReel.lua does not name "%s"' % name)
    gdt = open(os.path.join(root, 'source_data', 'tod_ui_images.gdt'), encoding='utf-8', errors='replace').read()
    zone = ''.join(open(z, encoding='utf-8', errors='replace').read()
                   for z in glob.glob(os.path.join(root, 'zone_source', '*.zone')))
    for name in NAMES:
        if not re.search(r'"%s"\s*\(\s*"image\.gdf"' % re.escape(name), gdt):
            out.append('%s: no GDT block in source_data/tod_ui_images.gdt' % name)
        if not re.search(r'^\s*image,%s\s*$' % re.escape(name), zone, re.M):
            out.append('%s: no zone image line' % name)
    return out


def selftest(root=None):
    """NEGATIVE CONTROLS: the delivered synthwave frame fails the fallen hue rule, a re-lit frame passes it, a planted
    other-theme Lua line and a missing one are caught, and the clean tree passes."""
    fails = []
    park = park_dir(root)
    syn = Image.open(os.path.join(park, 'i_tod_spin_frame.png'))
    if not synth_hue_left(syn):
        fails.append('the delivered magenta / cyan frame passed the no-synthwave-hue rule')
    if synth_hue_left(relight(syn, MAP['i_tod_spin_frame'], THEMES['fallen']['PAL'])):
        fails.append('the re-lit frame still carries a synthwave hue')
    lua = open(os.path.join(root or ROOT, LUA_REL), encoding='utf-8', errors='replace').read()
    if lua_problems(lua):
        fails.append('the clean TodSpinReel.lua fails its own tint rule: %s' % lua_problems(lua)[0])
    other = [t for t in LUA_TINTS if t != THEME][0]
    for i, nd in enumerate(LUA_TINTS[THEME]):
        if not lua_problems(lua.replace(nd, LUA_TINTS[other][i])):
            fails.append('the %s line %r planted in TodSpinReel.lua was NOT caught' % (other, LUA_TINTS[other][i]))
    if problems(root):
        fails.append('the clean tree fails --check: %s' % problems(root)[0])
    for f in fails:
        print('BM CHROME SELFTEST FAIL: ' + f)
    if fails:
        return 1
    print('BM CHROME SELFTEST OK: the delivered synthwave frame and %d planted %s tint lines are caught; the re-lit '
          'frame and the clean tree pass' % (len(LUA_TINTS[THEME]), other))
    return 0


def review(built, out_dir):
    import io
    park = park_dir()
    rows = []
    for name in NAMES:
        a = Image.open(os.path.join(park, name + '.png')).convert('RGBA')
        b = Image.open(io.BytesIO(built[name])).convert('RGBA')
        k = min(1.0, 900.0 / a.width)
        cells = []
        for im in (a, b):
            im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
            bg = Image.new('RGBA', im.size, (38, 40, 46, 255))
            bg.alpha_composite(im)
            cells.append(bg)
        rows.append(cells)
    W = max(r[0].width + r[1].width for r in rows) + 30
    H = sum(r[0].height for r in rows) + 10 * len(rows) + 10
    sheet = Image.new('RGB', (W, H), (16, 16, 20))
    y = 10
    for a, b in rows:
        sheet.paste(a.convert('RGB'), (10, y))
        sheet.paste(b.convert('RGB'), (20 + a.width, y))
        y += a.height + 10
    p = os.path.join(out_dir, '_review.png')
    sheet.save(p)
    return p


def main():
    ap = argparse.ArgumentParser(description='THE BLACK MARKET screen chrome by THEME')
    ap.add_argument('--install', action='store_true', help='write the PNGs into <root>/source_data/tod_ui_images/_images/')
    ap.add_argument('--check', action='store_true', help='build gate')
    ap.add_argument('--selftest', action='store_true', help='negative controls')
    ap.add_argument('--root', default=None, help='the tree to check / install into (default: the repo)')
    o = ap.parse_args()
    root = os.path.abspath(o.root) if o.root else None
    if o.selftest:
        sys.exit(selftest(root))
    built = build(root)
    if o.check:
        bad = problems(root, built)
        for m in bad:
            print('BM CHROME: ' + m)
        if bad:
            sys.exit(1)
        print('BM CHROME OK %d images (theme %s; alpha = the delivered art%s) + TodSpinReel.lua tints + wiring'
              % (len(built), THEME, '' if THEME == 'synthwave' else '; no synthwave hue left'))
        return
    if o.install:
        d = os.path.join(root or ROOT, IMG_REL)
        for name, data in built.items():
            with open(os.path.join(d, name + '.png'), 'wb') as fh:
                fh.write(data)
        print('installed %d images into %s (theme %s)' % (len(built), d, THEME))
        return
    out_dir = artgen.stage_dir(PACK)
    os.makedirs(out_dir, exist_ok=True)
    for name, data in built.items():
        with open(os.path.join(out_dir, name + '.png'), 'wb') as fh:
            fh.write(data)
    print('review ->', review(built, out_dir))


if __name__ == '__main__':
    main()
