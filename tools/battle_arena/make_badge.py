"""make_badge.py - THE BATTLE ARENA's round badge (docs/185 v2.2): the HUD's ROUND badge, re-lettered.

User 2026-10-03: "in the Battle Arena we should replace the round HUD with Battle Arena / Level 1 etc
... since rounds dont count in there and its a static difficulty of progression". The HUD V2 round
badge (i_tod_h2_round_badge / _rampage, the user's 2026-09-26 drop; tod_upgrade.lua's status plate)
therefore gets an ARENA TWIN that the plate swaps in while the party fights in the arena:
    the pill reads   BATTLE ARENA   (where the round badge's pill reads ROUND)
    the window reads LEVEL          (a caption along its top; the level number is drawn under it
                                     at runtime by the plate's own Round2Row, exactly as the round is)
Both twins are GENERATED from the shipped round badges, never painted by hand: the pill is redrawn
wider in the badge's OWN colours (sampled from the source pixels), the words are typeset from the
map's glyph sheets (TodGlyphMetrics.lua + i_tod_hud_l*.png, the same cells TodGlyphRow draws in game,
supersampled 4x), and every other pixel is the source's. Re-run after a redrawn round badge.

  python tools/battle_arena/make_badge.py           # writes the two PNGs + art/battle_arena/review/badge_review.png
  python tools/battle_arena/make_badge.py --check   # regenerates in memory; fails on any byte of difference, a
                                                    # missing GDT block, zone line or Lua registration (a build gate)
"""
import io, os, re, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IMG = os.path.join(ROOT, 'source_data', 'tod_ui_images', '_images')
METRICS = os.path.join(ROOT, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodGlyphMetrics.lua')
REVIEW = os.path.join(ROOT, 'art', 'battle_arena', 'review', 'badge_review.png')

# the arena twin -> the round badge it is cut from
TWINS = {
    'i_tod_h2_arena_badge': 'i_tod_h2_round_badge',
    'i_tod_h2_arena_badge_rampage': 'i_tod_h2_round_badge_rampage',
}

# THE GEOMETRY, in the badge's own 192x192 art pixels (0.375 canvas units each). Measured from the
# shipped round badge: the ROUND pill spans x 54..137 / y 24..47 with ~4 px chamfered corners inside a
# body band that runs x 23..169; the number window's interior is x 38..153 / y 57..124. The arena pill
# keeps the pill's rows and chamfer and grows sideways to hold two words at the typeface's cap 11
# (= 4.1 canvas units: the same lettering height as the sheets' LUCK / ROUND captions, 6 px at 1080p).
PILL = dict(x0=36, y0=24, x1=156, y1=47, chamfer=4)
PILL_TEXT = dict(text='BATTLE ARENA', cap=11, cx=96.0, baseline=40)
WINDOW_TEXT = dict(text='LEVEL', cap=11, cx=95.5, baseline=71)   # the caption along the window's top; the
                                                                 # number sits under it: tod_upgrade.lua
                                                                 # TOD_ARENA_NUM_CAP / _BASE (lockstep: art y 86..120)
# where each colour is sampled from the SOURCE badge (free of letters): the pill's fill, its outline,
# the dark line inside the outline, and the letters themselves
SAMPLE = dict(fill=[(x, y) for x in range(57, 62) for y in range(27, 45)],
              outline=[(x, y) for x in (55, 56) for y in range(27, 45)],
              inner=[(57, y) for y in range(28, 44)],
              letters=[(x, y) for x in range(63, 128) for y in range(29, 42)])

TOD_SPACE_ADV, TOD_TRACK = 0.30, 0.055   # LOCKSTEP TodGlyphRow.lua
SS = 4                                   # supersampling for the typesetting


def metrics():
    """The letters set of the GENERATED metrics: cw / ch / baseline / cap and g[c] = (adv, x)."""
    t = open(METRICS, encoding='utf-8').read()
    m = re.search(r'letters = \{\s*cw = (\d+), ch = (\d+), baseline = (\d+), cap = (\d+),\s*g = \{(.*?)\n\t\t\},', t, re.S)
    if not m:
        raise SystemExit('make_badge: TodGlyphMetrics.lua: no letters set')
    cw, ch, base, cap = (int(v) for v in m.group(1, 2, 3, 4))
    g = {}
    for c, adv, x in re.findall(r'\["(.)"\] = \{ adv = (\d+), x = (\d+)', m.group(5)):
        g[c] = (int(adv), int(x))
    return dict(cw=cw, ch=ch, baseline=base, cap=cap, g=g)


def median_rgb(px, pts, pick=None):
    vals = [px[x, y][:3] for x, y in pts if px[x, y][3] > 200 and (pick is None or pick(px[x, y]))]
    if not vals:
        raise SystemExit('make_badge: a colour sample found no pixels')
    vals.sort(key=lambda c: c[0] + c[1] + c[2])
    return vals[len(vals) // 2]


def octagon(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


_cells = {}


def cell(c):
    if c not in _cells:
        _cells[c] = Image.open(os.path.join(IMG, 'i_tod_hud_l' + c.lower() + '.png')).convert('RGBA')
    return _cells[c]


def typeset(layer, M, text, cap, cx, baseline, rgb):
    """TodGlyphRow.set's walk (measure, then place each CELL so its ink starts at the pen and the set's
    baseline lands on baselineY), centred on cx, drawn SS times larger onto `layer`."""
    s = cap / M['cap']
    total, first = 0.0, True
    for c in text:
        if c == ' ':
            total += M['cw'] * s * TOD_SPACE_ADV
        else:
            if c.lower() not in M['g']:
                raise SystemExit('make_badge: no glyph for %r' % c)
            if not first:
                total += cap * TOD_TRACK
            total += M['g'][c.lower()][0] * s
        first = False
    pen, first = cx - total / 2, True
    for c in text:
        if c == ' ':
            pen += M['cw'] * s * TOD_SPACE_ADV
            first = False
            continue
        adv, gx = M['g'][c.lower()]
        if not first:
            pen += cap * TOD_TRACK
        left, top = pen - gx * s, baseline - M['baseline'] * s
        w, h = M['cw'] * s * SS, M['ch'] * s * SS
        im = cell(c).resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
        r, g, b, a = im.split()
        r = r.point(lambda v: v * rgb[0] // 255)
        g = g.point(lambda v: v * rgb[1] // 255)
        b = b.point(lambda v: v * rgb[2] // 255)
        im = Image.merge('RGBA', (r, g, b, a))
        layer.alpha_composite(im, (int(round(left * SS)), int(round(top * SS))))
        pen += adv * s
        first = False
    return total


def make(src_name, M):
    src = Image.open(os.path.join(IMG, src_name + '.png')).convert('RGBA')
    if src.size != (192, 192):
        raise SystemExit('make_badge: %s is %s, not 192x192' % (src_name, src.size))
    px = src.load()
    fill = median_rgb(px, SAMPLE['fill'])
    outline = median_rgb(px, SAMPLE['outline'])
    inner = median_rgb(px, SAMPLE['inner'])
    letters = median_rgb(px, SAMPLE['letters'], lambda p: p[0] > 150 and p[1] > 150 and p[2] > 150)
    out = src.copy()
    d = ImageDraw.Draw(out)
    P = PILL
    d.polygon(octagon(P['x0'], P['y0'], P['x1'], P['y1'], P['chamfer']), fill=outline + (255,))
    d.polygon(octagon(P['x0'] + 2, P['y0'] + 2, P['x1'] - 2, P['y1'] - 2, P['chamfer'] - 1), fill=inner + (255,))
    d.polygon(octagon(P['x0'] + 3, P['y0'] + 3, P['x1'] - 3, P['y1'] - 3, P['chamfer'] - 2), fill=fill + (255,))
    layer = Image.new('RGBA', (192 * SS, 192 * SS), (0, 0, 0, 0))
    w1 = typeset(layer, M, PILL_TEXT['text'], PILL_TEXT['cap'], PILL_TEXT['cx'], PILL_TEXT['baseline'], letters)
    w2 = typeset(layer, M, WINDOW_TEXT['text'], WINDOW_TEXT['cap'], WINDOW_TEXT['cx'], WINDOW_TEXT['baseline'], letters)
    if w1 > (P['x1'] - P['x0']) - 2 * (P['chamfer'] + 6):
        raise SystemExit('make_badge: BATTLE ARENA (%.1f px) does not fit the pill' % w1)
    out.alpha_composite(layer.resize((192, 192), Image.LANCZOS))
    return out, dict(fill=fill, outline=outline, inner=inner, letters=letters, pill_text_w=round(w1, 1), window_text_w=round(w2, 1))


def encode(im):
    b = io.BytesIO()
    im.save(b, format='PNG', optimize=False)
    return b.getvalue()


def wiring_problems():
    out = []
    gdt = open(os.path.join(ROOT, 'source_data', 'tod_ui_images.gdt'), encoding='utf-8', errors='replace').read()
    zone = open(os.path.join(ROOT, 'zone_source', 'zm_tod2_cybercity.zone'), encoding='utf-8', errors='replace').read()
    lua = open(os.path.join(ROOT, 'ui', 'uieditor', 'menus', 'hud', 'tod_upgrade.lua'), encoding='utf-8', errors='replace').read()
    for name in TWINS:
        if ('"%s" ( "image.gdf" )' % name) not in gdt or ('"baseImage" "source_data/tod_ui_images/_images/%s.png"' % name) not in gdt:
            out.append('GDT: no image block for %s' % name)
        if not re.search(r'^image,%s\r?$' % re.escape(name), zone, re.M):
            out.append('zone: no image line for %s' % name)
        if ('RegisterImage( "%s" )' % name) not in lua:
            out.append('tod_upgrade.lua does not register %s' % name)
    return out


def main():
    check = '--check' in sys.argv
    M = metrics()
    bad = []
    made = {}
    for name, src in TWINS.items():
        im, info = make(src, M)
        made[name] = (im, info)
        path = os.path.join(IMG, name + '.png')
        if check:
            if not os.path.exists(path):
                bad.append('%s.png is missing' % name)
            elif open(path, 'rb').read() != encode(im):
                bad.append('%s.png differs from what the generator makes' % name)
        else:
            open(path, 'wb').write(encode(im))
            print('wrote', path, info)
    if check:
        bad += wiring_problems()
        if bad:
            for b in bad:
                print('ARENA BADGE STALE:', b)
            print('  run: python tools/battle_arena/make_badge.py  (and wire the GDT / zone / Lua)')
            sys.exit(1)
        print('ARENA BADGE OK: %d badges match the generator; GDT + zone + Lua wired' % len(TWINS))
        return
    # the review strip: round badge beside its arena twin, both variants, enlarged
    strip = Image.new('RGBA', (4 * 192 * 2 + 5 * 12, 192 * 2 + 24), (34, 34, 38, 255))
    x = 12
    for name, src in TWINS.items():
        for n, im in ((src, Image.open(os.path.join(IMG, src + '.png')).convert('RGBA')), (name, made[name][0])):
            strip.paste(im.resize((384, 384), Image.NEAREST), (x, 12))
            x += 384 + 12
    os.makedirs(os.path.dirname(REVIEW), exist_ok=True)
    strip.save(REVIEW)
    print('wrote', REVIEW)


if __name__ == '__main__':
    main()
