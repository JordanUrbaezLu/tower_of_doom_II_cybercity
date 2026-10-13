#!/usr/bin/env python
"""
build_tod_ttf.py - turn the map's bitmap typeface into a real TTF.

WHY (user 2026-09-25): "the pause menu and leaderboard menu descriptions and text
dont use our font." The HUD and prompt cards draw the face as one pooled UIImage
PER GLYPH (TodGlyphRow / TodGlyphText). The pause menu carries up to 18 upgrade rows
of 40-54 character descriptions and is rebuilt on every pause, so the same approach
would add ~2,000 UI elements per open (11x what the menu makes today) on a map whose
known crash is UI element-pool exhaustion (docs/133, docs/142). A TTF costs ZERO
elements: the menus keep their UIText elements and only swap setTTF. Custom TTFs are
proven in this map (orbitron / ltromatic, zoned `ttf,fonts/...`).

WHAT IT BUILDS: fonts/tod_tower1.ttf from the SAME sheets the HUD slices
(source_data/tod_ui_images/_sheets/i_tod_hud_letters.png + i_tod_hud_digits.png).
Only the steel-white FACE is traced (the dark outline and the offset shadow are two
tones a TTF cannot hold); UIText colours it at runtime exactly as it colours orbitron.
  - A-Z traced; a-z map to the same glyphs (the face is caps-only by design)
  - 0-9 / + traced from the digit sheet, scaled so its face cap = the letters'
  - - ' . traced from the letter sheet
  - % , : ; ( ) [ ] ! ? " _ = < > * # $ & @ ~ | { } ^ ` \\ built from rectangles in the
    face's own stroke weight (the sheets do not carry them; descriptions need them)
VERTICAL METRICS COPY ORBITRON (upm 1000, ascent 1011, descent 243, cap 720 before the
fit) so text sits where it sat in every existing box.
THE FIT: HORIZONTAL_FIT narrows advances+outlines so the longest real description is no
wider than orbitron drew it; the lines keep their boxes. Printed on every run.

Re-run after any re-slice of the sheets:  python tools/build_tod_ttf.py
Needs: pip install fonttools pillow (build-time only; nothing ships but the .ttf).
"""
import os, sys
from PIL import Image
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEETS = os.path.join(REPO, "source_data", "tod_ui_images", "_sheets")
OUT = os.path.join(REPO, "fonts", "tod_tower1.ttf")
FAMILY = "TOD Tower1"

UPM, ASC, DESC = 1000, 1011, -243
CAP = 720                 # orbitron's cap height; the face's cap is scaled onto it
HORIZONTAL_FIT = 0.91     # x scale; see THE FIT above (checked against orbitron below). 0.94 until the
                          # 2026-09-29 legibility redraw: its thinner outline left a WIDER steel face in the same
                          # ink box, so every menu line grew 3.3% (one Breacher row overflowed its box); 0.91 puts
                          # the real menu text back on its old width (tools/ui_mockup/render_menus.py --check)
TRACK = 0.10              # side bearing each side, fraction of CAP

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["-", "'", None, "."]   # cell 28 = coin
DIGITS = list("0123456789") + ["/", "+", None]                         # digit "-" unused


def face_mask(img):
    """True where the pixel is the steel-white FACE (not outline, shadow or coin)."""
    w, h = img.size
    px = img.load()
    m = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            # face #E8EEF6: bright AND cool/neutral (blue >= red) - excludes the gold coin
            if r + g + b > 3 * 175 and b >= r - 8:
                m[y][x] = True
    return m


def trace(mask):
    """Pixel-exact outline of a boolean mask -> list of closed orthogonal polygons
    (y-down, fill on the right; from_mask reverses them into TrueType clockwise)."""
    h = len(mask)
    w = len(mask[0]) if h else 0
    fill = lambda x, y: 0 <= x < w and 0 <= y < h and mask[y][x]
    # boundary edges with the filled pixel on the RIGHT (y-down); a vertex can start two
    # edges where two pixels touch diagonally, hence a multimap
    out = {}
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            if not fill(x, y - 1): out.setdefault((x, y), []).append((x + 1, y))
            if not fill(x + 1, y): out.setdefault((x + 1, y), []).append((x + 1, y + 1))
            if not fill(x, y + 1): out.setdefault((x + 1, y + 1), []).append((x, y + 1))
            if not fill(x - 1, y): out.setdefault((x, y + 1), []).append((x, y))
    polys = []
    while out:
        start = next(iter(out))
        poly = [start]
        cur = start
        while True:
            nxts = out[cur]
            nxt = nxts.pop()
            if not nxts:
                del out[cur]
            if nxt == start:
                break
            poly.append(nxt)
            cur = nxt
            if cur not in out:
                break
        # drop collinear points
        simp = []
        n = len(poly)
        for i in range(n):
            a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
            if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
                simp.append(b)
        if len(simp) >= 3:
            polys.append(simp)
    return polys


def cells(path, cw, ch, cols, chars):
    img = Image.open(path).convert("RGBA")
    res = {}
    for i, c in enumerate(chars):
        if c is None:
            continue
        x0, y0 = (i % cols) * cw, (i // cols) * ch
        res[c] = face_mask(img.crop((x0, y0, x0 + cw, y0 + ch)))
    return res


def bbox(mask):
    ys = [y for y, row in enumerate(mask) if any(row)]
    xs = [x for row in mask for x, v in enumerate(row) if v]
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1) if xs else None


def main():
    let = cells(os.path.join(SHEETS, "i_tod_hud_letters.png"), 80, 112, 15, LETTERS)
    dig = cells(os.path.join(SHEETS, "i_tod_hud_digits.png"), 128, 160, 13, DIGITS)

    def cap_base(set_, sample):
        tops, bots = [], []
        for c in sample:
            b = bbox(set_[c])
            tops.append(b[1]); bots.append(b[3])
        tops.sort(); bots.sort()
        return tops[len(tops) // 2], bots[len(bots) // 2]

    lt, lb = cap_base(let, "EFHILTNMZ")
    dt, db = cap_base(dig, "1234579")
    lscale = CAP / float(lb - lt)
    dscale = CAP / float(db - dt)
    stem_px = (bbox(let["I"])[2] - bbox(let["I"])[0])
    STEM = stem_px * lscale * 0.62            # the I carries serifs; its stem is ~62% of its width
    print("letters: face cap %dpx base y%d  digits: face cap %dpx base y%d  stem ~%.0f units" % (lb - lt, lb, db - dt, db, STEM))

    glyphs = {}   # name -> (polys in font units y-up, advance)
    side = TRACK * CAP

    def from_mask(mask, scale, base):
        b = bbox(mask)
        polys = trace(mask)
        fp = []
        for p in polys:
            # the y flip mirrors the winding; reverse so every contour is TrueType clockwise,
            # matching the constructed pieces (the $ bar overlaps the S and must ADD)
            fp.append([((x - b[0]) * scale * HORIZONTAL_FIT + side, (base - y) * scale) for (x, y) in reversed(p)])
        adv = (b[2] - b[0]) * scale * HORIZONTAL_FIT + 2 * side
        return fp, adv

    for c, m in let.items():
        glyphs[c] = from_mask(m, lscale, lb)
    for c, m in dig.items():
        glyphs[c] = from_mask(m, dscale, db)

    # ---- constructed punctuation, in the face's stroke weight -------------------
    S = STEM * HORIZONTAL_FIT
    H = STEM                              # vertical stroke thickness
    def R(x0, y0, x1, y1):                # rectangle, y-up, CW for TrueType
        return [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]
    def P(*pts):                          # polygon given CW-in-y-up
        return list(pts)
    def mk(polys, width):
        return ([[(x + side, y) for (x, y) in p] for p in polys], width + 2 * side)
    dot = S
    glyphs[":"] = mk([R(0, 0, dot, H), R(0, CAP * 0.5, dot, CAP * 0.5 + H)], dot)
    glyphs[","] = mk([R(0, 0, dot, H), P((0, -H * 0.9), (dot * 0.45, 0), (dot, 0), (dot * 0.35, -H * 0.9))], dot)
    glyphs[";"] = mk(glyphs[","][0] and [R(0, 0, dot, H), P((0, -H * 0.9), (dot * 0.45, 0), (dot, 0), (dot * 0.35, -H * 0.9)),
                                         R(0, CAP * 0.5, dot, CAP * 0.5 + H)], dot)
    glyphs["!"] = mk([R(0, 0, dot, H), R(0, H * 1.8, dot, CAP)], dot)
    bw = S * 2.2
    glyphs["("] = mk([R(0, -H * 0.5, S, CAP + H * 0.5), R(S, CAP + H * 0.5 - H, bw, CAP + H * 0.5), R(S, -H * 0.5, bw, -H * 0.5 + H)], bw)
    glyphs[")"] = mk([R(bw - S, -H * 0.5, bw, CAP + H * 0.5), R(0, CAP + H * 0.5 - H, bw - S, CAP + H * 0.5), R(0, -H * 0.5, bw - S, -H * 0.5 + H)], bw)
    glyphs["["] = glyphs["("]; glyphs["]"] = glyphs[")"]
    glyphs["{"] = glyphs["("]; glyphs["}"] = glyphs[")"]
    qw = S * 3.2
    glyphs["?"] = mk([R(0, CAP - H, qw, CAP), R(qw - S, CAP * 0.5, qw, CAP), R(qw * 0.35, CAP * 0.5 - H * 0.2, qw, CAP * 0.5 + H * 0.8),
                      R(qw * 0.35, H * 1.8, qw * 0.35 + S, CAP * 0.5), R(qw * 0.35, 0, qw * 0.35 + S, H)], qw)
    glyphs['"'] = mk([R(0, CAP - H * 1.8, S * 0.8, CAP), R(S * 1.6, CAP - H * 1.8, S * 2.4, CAP)], S * 2.4)
    uw = CAP * 0.62
    glyphs["_"] = mk([R(0, -H * 1.2, uw, -H * 0.2)], uw)
    ew = CAP * 0.6
    glyphs["="] = mk([R(0, CAP * 0.22, ew, CAP * 0.22 + H), R(0, CAP * 0.55, ew, CAP * 0.55 + H)], ew)
    cw_ = CAP * 0.55
    glyphs["<"] = mk([P((0, CAP * 0.45), (cw_, CAP * 0.85), (cw_, CAP * 0.85 - H * 1.4), (S * 1.6, CAP * 0.45), (cw_, CAP * 0.05 + H * 1.4), (cw_, CAP * 0.05))], cw_)
    glyphs[">"] = mk([P((cw_, CAP * 0.45), (0, CAP * 0.05), (0, CAP * 0.05 + H * 1.4), (cw_ - S * 1.6, CAP * 0.45), (0, CAP * 0.85 - H * 1.4), (0, CAP * 0.85))], cw_)
    # % = two RINGS either side of the digit sheet's slash: the classic o/o. SQUARE BLOCKS
    # READ AS "7." (the block at the cap line is a 7's bar, the one on the baseline a full
    # stop: the 2026-09-29 proof read "HEALTH 85%" as "HEALTH 857."), and so did round
    # dots; hollow squares were the same "7." (the first build). Six designs were set at
    # 13-32 px in the 2026-09-29 legibility pass and only rings read as a percent at every
    # size. Octagons match the face's squared curves; the wall is half a stem so the hole
    # stays open at the large sizes and the ring reads as a round mark at the small ones.
    dd = CAP * 0.38                        # ring diameter
    wall = S * 0.50
    gap = S * 0.25
    def octa(cx, cy, d, cw=True):
        r = d / 2.0
        k = 0.4142 * r                     # tan(22.5): a regular octagon
        pts = [(cx - k, cy - r), (cx - r, cy - k), (cx - r, cy + k), (cx - k, cy + r),
               (cx + k, cy + r), (cx + r, cy + k), (cx + r, cy - k), (cx + k, cy - r)]
        return pts if cw else list(reversed(pts))
    def ring(cx, cy):
        return [octa(cx, cy, dd), octa(cx, cy, dd - 2 * wall, False)]   # outer CW, hole CCW
    sl_polys, sl_adv = glyphs["/"]
    pw = sl_adv - 2 * side
    sx = dd * 0.55 + gap                   # the slash starts under the top ring's right half
    pct = ring(dd / 2, CAP - dd / 2) + [[(x - side + sx, y) for (x, y) in p] for p in sl_polys] + ring(sx + pw + gap - dd * 0.05, dd / 2)
    glyphs["%"] = mk(pct, sx + pw + gap + dd * 0.45)
    # composites reuse traced glyphs
    def reuse(src, extra=(), extra_w=None):
        polys, adv = glyphs[src]
        return (polys + [[(x + side, y) for (x, y) in p] for p in extra], adv if extra_w is None else extra_w)
    sp, sadv = glyphs["S"]
    sw = sadv - 2 * side
    glyphs["$"] = reuse("S", [R(sw / 2 - S * 0.3, -H * 0.8, sw / 2 + S * 0.3, CAP + H * 0.8)])
    glyphs["&"] = glyphs["+"]          # no ampersand in the face (its cell is the coin); reads as "and"
    glyphs["*"] = mk([R(0, CAP * 0.55, S * 2.4, CAP * 0.55 + H * 0.7), R(S * 0.85, CAP * 0.35, S * 1.55, CAP * 0.9)], S * 2.4)
    glyphs["#"] = mk([R(S * 0.6, 0, S * 1.3, CAP * 0.8), R(S * 2.1, 0, S * 2.8, CAP * 0.8), R(0, CAP * 0.2, S * 3.4, CAP * 0.2 + H * 0.7), R(0, CAP * 0.52, S * 3.4, CAP * 0.52 + H * 0.7)], S * 3.4)
    glyphs["@"] = glyphs["O"]
    glyphs["|"] = mk([R(0, -H * 0.5, S * 0.7, CAP + H * 0.5)], S * 0.7)
    glyphs["\\"] = mk([[(x, y) for (x, y) in p] for p in [[(sl_adv - 2 * side - px, py) for (px, py) in reversed(q)] for q in [[(x - side, y) for (x, y) in p] for p in sl_polys]]], sl_adv - 2 * side)
    glyphs["~"] = glyphs["-"]; glyphs["^"] = glyphs["'"]; glyphs["`"] = glyphs["'"]

    # ---- assemble ---------------------------------------------------------------
    order = [".notdef", "space"]
    cmap = {32: "space"}
    names = {}
    for c in sorted(glyphs):
        n = "g%04X" % ord(c)
        names[c] = n
        order.append(n)
        cmap[ord(c)] = n
        if "A" <= c <= "Z":
            cmap[ord(c.lower())] = n
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    glyf, metrics = {}, {}
    def build(polys):
        pen = TTGlyphPen(None)
        for p in polys:
            pts = [(round(x), round(y)) for (x, y) in p]
            pen.moveTo(pts[0])
            for q in pts[1:]:
                pen.lineTo(q)
            pen.closePath()
        return pen.glyph()
    glyf[".notdef"] = TTGlyphPen(None).glyph(); metrics[".notdef"] = (int(CAP * 0.4), 0)
    glyf["space"] = TTGlyphPen(None).glyph(); metrics["space"] = (int(CAP * 0.38), 0)
    for c, n in names.items():
        polys, adv = glyphs[c]
        glyf[n] = build(polys)
        metrics[n] = (int(round(adv)), 0)
    fb.setupGlyf(glyf)
    for n in metrics:
        g = glyf[n]
        g.recalcBounds(fb.font["glyf"]) if hasattr(g, "recalcBounds") else None
        lsb = getattr(g, "xMin", 0) or 0
        metrics[n] = (metrics[n][0], lsb)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC, descent=DESC)
    fb.setupNameTable({"familyName": FAMILY, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=ASC, sTypoDescender=DESC, usWinAscent=ASC, usWinDescent=-DESC, sCapHeight=CAP, sxHeight=CAP)
    fb.setupPost()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fb.save(OUT)

    # ---- THE FIT: compare against orbitron on the longest real strings ----------
    ours, orb = TTFont(OUT), TTFont(os.path.join(REPO, "fonts", "orbitron.ttf"))
    def width(font, s):
        cm, hm = font.getBestCmap(), font["hmtx"]
        return sum(hm[cm[ord(ch)]][0] if ord(ch) in cm else 0 for ch in s)
    worst = 0
    for s in ["the zombie you hit moves 36% slower", "burns 10%/s, slows 37.5%, lasts 4.0s",
              "Katana only; swing within 0.4s of sprinting", "Switch To Third Person", "SUPPRESSING FIRE"]:
        r = width(ours, s) / float(width(orb, s))
        worst = max(worst, r)
        print("  %-46s ours/orbitron width %.2f" % (s, r))
    print("glyphs %d, cmap %d -> %s  (worst width ratio %.2f)" % (len(order), len(cmap), OUT, worst))
    missing = [chr(c) for c in range(32, 127) if c not in cmap]
    print("printable ASCII not covered:", "".join(missing) or "none")


if __name__ == "__main__":
    main()
