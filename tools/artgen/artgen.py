"""artgen.py - the shared toolkit for SELF-GENERATED 2D art (2026-10-04).

WHY THIS EXISTS. Until 2026-10-04 every image the map needed went out as an art-request zip
(tools/make_art_pack.ps1) and came back as a drop the user had made with another Claude model.
User 2026-10-04: "My typical flow regardless is sending to opus or fable anyways so we could just
update the process where we dont need me in the loop anymore." So the brief is still written
(docs/NN_*_art_prompt.md stays the spec and the record), but the session that writes it also
FULFILS it, with a generator script that lives in the repo - the same doctrine as the gift art,
the arena badge and the health-bar art: generated, reproducible, gated with --check, never
hand-painted.

WHAT IT GIVES A GENERATOR
  render_svg(svg, w, h, ss)       flat vector art (the shipped UI style) through resvg_py, drawn
                                  ss times larger and downsampled (clean anti-aliasing)
  svg_doc(w, h, body, defs)       an <svg> wrapper with a w x h viewBox
  typeset(...) / text_width(...)  the MAP'S OWN TYPEFACE: the glyph-sheet cells TodGlyphRow draws in
                                  game (i_tod_hud_l*.png letters, i_tod_hud_d*.png digits), placed with
                                  the GENERATED TodGlyphMetrics.lua, so baked text matches the HUD
  ttf(size)                       fonts/tod_tower1.ttf (the same face as a TTF, no outline) for PIL
  save_png(im, path)              RGBA, deterministic bytes; refuses a size that is not a multiple of 4
                                  (memory compressed-image-multiple-of-4: the converter writes no .iwi)
  png_bytes(im)                   the bytes save_png would write (for --check gates)
  contact_sheet(rows, out)        a review sheet: each new image beside its reference(s), labelled
  palette(path, k)                the k dominant opaque colours of a shipped image (to match style)

  python tools/artgen/artgen.py --selftest   renders a test icon + a text strip into the scratch dir

Requires: Pillow, numpy, resvg_py (pip install --user resvg_py; a wheel exists for every CPython >= 3.10).
"""
import io, os, re, sys, hashlib

from PIL import Image, ImageDraw, ImageFont

try:
    import resvg_py
except ImportError:  # pragma: no cover - reported at first use, not at import
    resvg_py = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IMG = os.path.join(ROOT, 'source_data', 'tod_ui_images', '_images')
METRICS = os.path.join(ROOT, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodGlyphMetrics.lua')
TTF = os.path.join(ROOT, 'fonts', 'tod_tower1.ttf')
STAGE = os.path.join(ROOT, 'art', 'generated')          # where generators write before an install

TOD_SPACE_ADV, TOD_TRACK = 0.30, 0.055                  # LOCKSTEP TodGlyphRow.lua

# --------------------------------------------------------------------------------------------- svg

def svg_doc(w, h, body, defs=''):
    d = '<defs>%s</defs>' % defs if defs else ''
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="%d" height="%d" viewBox="0 0 %d %d">%s%s</svg>' % (w, h, w, h, d, body))


def render_svg(svg, w, h, ss=2):
    """Render `svg` (whose viewBox is w x h) at ss*w x ss*h, then LANCZOS down to w x h. RGBA."""
    if resvg_py is None:
        raise SystemExit('artgen: resvg_py is not installed (pip install --user resvg_py)')
    data = resvg_py.svg_to_bytes(svg_string=svg, width=w * ss, height=h * ss, skip_system_fonts=True,
                                 font_files=[TTF], shape_rendering='geometric_precision')
    im = Image.open(io.BytesIO(bytes(data))).convert('RGBA')
    if im.size != (w * ss, h * ss):
        im = im.resize((w * ss, h * ss), Image.LANCZOS)
    return im.resize((w, h), Image.LANCZOS) if ss != 1 else im

# ------------------------------------------------------------------------------------------ glyphs

_M = None
_cells = {}


def metrics():
    """Both sets of the GENERATED metrics: {'letters': {...}, 'digits': {...}} with cw/ch/baseline/cap/g."""
    global _M
    if _M:
        return _M
    t = open(METRICS, encoding='utf-8').read()
    out = {}
    for name in ('digits', 'letters'):
        m = re.search(name + r' = \{\s*cw = (\d+), ch = (\d+), baseline = (\d+), cap = (\d+),\s*g = \{(.*?)\n\t\t\},', t, re.S)
        if not m:
            raise SystemExit('artgen: TodGlyphMetrics.lua has no %s set' % name)
        cw, ch, base, cap = (int(v) for v in m.group(1, 2, 3, 4))
        g = {}
        for c, adv, x in re.findall(r'\["(.)"\] = \{ adv = (\d+), x = (\d+)', m.group(5)):
            g[c] = (int(adv), int(x))
        out[name] = dict(cw=cw, ch=ch, baseline=base, cap=cap, g=g)
    _M = out
    return out


_LETTER_IMG = {'-': 'i_tod_hud_lhyphen', "'": 'i_tod_hud_lapos', '.': 'i_tod_hud_ldot', '$': 'i_tod_hud_lmoney'}
_DIGIT_IMG = {'/': 'i_tod_hud_dslash', '+': 'i_tod_hud_dplus'}


def _glyph(c, prefer_digit_dash=False):
    """(set name, metrics key, image name) for one character, as TodGlyphRow routes it.
    + and / exist ONLY in the digit set (memory glyph-plus-slash-are-digits); "-" is the letter
    hyphen unless prefer_digit_dash (the wide no-magazine marker)."""
    if '0' <= c <= '9':
        return 'digits', c, 'i_tod_hud_d' + c
    if c in _DIGIT_IMG:
        return 'digits', c, _DIGIT_IMG[c]
    if c == '-' and prefer_digit_dash:
        return 'digits', '-', 'i_tod_hud_ddash'
    u = c.upper()
    if 'A' <= u <= 'Z':
        return 'letters', u.lower(), 'i_tod_hud_l' + u.lower()
    if c in _LETTER_IMG:
        return 'letters', c, _LETTER_IMG[c]
    raise SystemExit('artgen: the typeface has no glyph for %r (A-Z 0-9 - \' . $ + / only)' % c)


def _cell(name):
    if name not in _cells:
        _cells[name] = Image.open(os.path.join(IMG, name + '.png')).convert('RGBA')
    return _cells[name]


def text_width(text, cap):
    """Width of `text` set at cap height `cap` (pixels), TodGlyphRow.set's measure."""
    M = metrics()
    total, first = 0.0, True
    for c in text:
        if c == ' ':
            total += M['letters']['cw'] * (cap / M['letters']['cap']) * TOD_SPACE_ADV
            first = False
            continue
        sname, key, _ = _glyph(c)
        S = M[sname]
        if not first:
            total += cap * TOD_TRACK
        total += S['g'][key][0] * (cap / S['cap'])
        first = False
    return total


def typeset(canvas, text, cap, baseline, rgb=(255, 255, 255), cx=None, x=None, ss=4, fit_width=None):
    """Draw `text` onto RGBA `canvas` in the map's typeface: cap height `cap` px, baseline at y
    `baseline`, centred on cx (or left-aligned at x). `rgb` tints the white glyph fill (the cells'
    dark outline stays dark). fit_width shrinks the cap until the text fits. Returns the cap used."""
    if fit_width is not None:
        while cap > 4 and text_width(text, cap) > fit_width:
            cap -= 0.25
    M = metrics()
    total = text_width(text, cap)
    pen = (cx - total / 2.0) if cx is not None else float(x)
    layer = Image.new('RGBA', (canvas.width * ss, canvas.height * ss), (0, 0, 0, 0))
    first = True
    for c in text:
        if c == ' ':
            pen += M['letters']['cw'] * (cap / M['letters']['cap']) * TOD_SPACE_ADV
            first = False
            continue
        sname, key, imgname = _glyph(c)
        S = M[sname]
        s = cap / S['cap']
        adv, gx = S['g'][key]
        if not first:
            pen += cap * TOD_TRACK
        left, top = pen - gx * s, baseline - S['baseline'] * s
        w, h = S['cw'] * s * ss, S['ch'] * s * ss
        im = _cell(imgname).resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
        r, g, b, a = im.split()
        r = r.point(lambda v, k=rgb[0]: v * k // 255)
        g = g.point(lambda v, k=rgb[1]: v * k // 255)
        b = b.point(lambda v, k=rgb[2]: v * k // 255)
        layer.alpha_composite(Image.merge('RGBA', (r, g, b, a)), (int(round(left * ss)), int(round(top * ss))))
        pen += adv * s
        first = False
    canvas.alpha_composite(layer.resize(canvas.size, Image.LANCZOS))
    return cap


def ttf(size):
    """The map's face as a TTF (no outline / extrusion) for plain PIL text."""
    return ImageFont.truetype(TTF, size)

# ------------------------------------------------------------------------------------------ output

def png_bytes(im):
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    buf = io.BytesIO()
    im.save(buf, format='PNG', optimize=False, compress_level=9)
    return buf.getvalue()


def save_png(im, path, allow_any_size=False):
    """Write deterministically. Compressed images must be a multiple of 4 on both sides."""
    if not allow_any_size and (im.width % 4 or im.height % 4):
        raise SystemExit('artgen: %s is %dx%d - not a multiple of 4 (the converter writes no .iwi)' % (path, im.width, im.height))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    data = png_bytes(im)
    with open(path, 'wb') as f:
        f.write(data)
    return hashlib.md5(data).hexdigest()


def stage_dir(pack):
    d = os.path.join(STAGE, pack)
    os.makedirs(d, exist_ok=True)
    return d


def shipped(name):
    """Path of a shipped UI image by asset name (with or without .png)."""
    if not name.endswith('.png'):
        name += '.png'
    return os.path.join(IMG, name)

# ------------------------------------------------------------------------------------------ review

def palette(path, k=8):
    """The k most common opaque colours of an image (quantized), as (count, '#rrggbb')."""
    im = Image.open(path).convert('RGBA')
    px = [p[:3] for p in im.getdata() if p[3] > 200]
    if not px:
        return []
    q = Image.new('RGB', (len(px), 1))
    q.putdata(px)
    q = q.quantize(colors=k, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    counts = sorted(q.getcolors(), reverse=True)
    return [(n, '#%02x%02x%02x' % tuple(pal[i * 3:i * 3 + 3])) for n, i in counts]


def contact_sheet(rows, out, height=256, bg=(28, 30, 38, 255), pad=12, label_h=26):
    """rows = [(label, [image paths or PIL images ...]), ...]. Each row: the images side by side at
    `height`, labelled. Checkerboard-free dark background (the HUD's own context)."""
    rendered = []
    for label, items in rows:
        ims = []
        for it in items:
            im = Image.open(it).convert('RGBA') if isinstance(it, str) else it.convert('RGBA')
            w = max(1, int(im.width * height / im.height))
            ims.append(im.resize((w, height), Image.LANCZOS))
        rendered.append((label, ims))
    W = max(sum(i.width for i in ims) + pad * (len(ims) + 1) for _, ims in rendered)
    H = sum(height + label_h + pad for _ in rendered) + pad
    sheet = Image.new('RGBA', (W, H), bg)
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype(TTF, 18)
    except Exception:
        f = ImageFont.load_default()
    y = pad
    for label, ims in rendered:
        d.text((pad, y), label, fill=(220, 225, 235, 255), font=f)
        x, y = pad, y + label_h
        for im in ims:
            sheet.alpha_composite(im, (x, y))
            x += im.width + pad
        y += height + pad
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out)
    return out


def _selftest():
    out = os.path.join(os.environ.get('TEMP', '.'), 'artgen_selftest')
    os.makedirs(out, exist_ok=True)
    svg = svg_doc(128, 128, '<rect x="14" y="14" width="100" height="100" rx="18" fill="#62779C" '
                            'stroke="#0A1020" stroke-width="10"/><circle cx="64" cy="64" r="22" fill="#E8EEF6"/>')
    icon = render_svg(svg, 128, 128, ss=4)
    p1 = os.path.join(out, 'icon.png')
    save_png(icon, p1)
    strip = Image.new('RGBA', (512, 96), (12, 16, 32, 255))
    typeset(strip, 'TOWER OF DOOM II +25/50', 40, 66, (255, 210, 90), cx=256, fit_width=490)
    p2 = os.path.join(out, 'text.png')
    save_png(strip, p2)
    contact_sheet([('icon', [p1]), ('text', [p2])], os.path.join(out, 'sheet.png'), height=96)
    print('artgen selftest OK ->', out)


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        _selftest()
    else:
        print(__doc__)
