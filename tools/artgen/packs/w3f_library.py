"""w3f_library.py - THE ONE-LIBRARY AUDIT's fixes (wave 3, package W3F, 2026-10-05).

User 2026-10-05: "Whole entire asset library should look like one library." Every shipped image was judged against
the Map 2 synthwave language (tools/artgen/synthwave.py, R3 / R4: dark-glass chamfered plates, a steel hairline, ONE
neon tube whose colour says its state, white-hot glyphs with one hued accent and a soft halo, every letter in the map's
own glyph cells). The ranked findings, with a contact sheet each, are tmp/wave3/W3F-library-audit/LAND.md and
art/generated/W3F-library-audit/findings/. This pack draws the clear outliers that need no design call:

  i_tod_tier_gate_2 / _3 (420 x 90, uncompressed; drawn 280 x 60 canvas units = 1:1 at 1080p)
      The CLASS TIER floor-gate strip of the upgrade deal panel (tod_upgrade.lua TierGateImg: the left gutter under the
      CLASS plate, or stamped across a floor-locked tier card's illustration). It was the LAST Map 1 pill in the deal
      panel - a silver rim, a round medallion with gold chevrons, grey type - between R4's synthwave LUCK badges and
      BETTER CARDS legend. Redrawn as their sibling: the same plate silhouette and icon well (r4 LB / LB_WELL), the same
      glass, steel hairline, bevel and halo, the same text slot (cap 25 on baseline 56, centred on x 247 inside 306 px),
      the descent's two DOWN chevrons as a neon glyph in the well (the leading one carries the accent), and the strip's
      words - TIER 2 AT FLOOR 40 / TIER 3 AT FLOOR 20 - with the floor number in neon as LUCK's percentage is.
      AMBER is the tier hue: it is already the class tier's colour everywhere else (the pause / scoreboard header's
      "TIER 2 OF 3 / NEXT: PAP + FLOOR 20", R3's amber reset mark "RESETS WHEN YOUR CLASS TIER GOES UP" - synthwave.py
      PAL: amber = the reset / warning badge only), and it says "not yet" without the DEAD tube's "refused".
      The two strips share one set of token slots (each token centred in the wider of its two widths), so swapping
      tier 2 for tier 3 moves no word (docs/73's runtime contract, kept from PK01).
      ONE OWNER PER FILE: tools/artgen/packs/pk01_card_text_rebake.py still writes and --checks these two files (its
      build gate, its wiring and descent-arithmetic checks); it now takes their pixels from tier_gate() here, as it
      takes the Breacher card's window from r2_card_subjects.

  i_tod_spin_tile_gift / i_tod_spin_banner_gift - owned by tools/partner_shop/make_gift_art.py (its build gate); W3F
      stages that generator's re-lettering (COMPANION / ON THE HOUSE set like COMMON .. LEGENDARY / CURSED). This pack
      only renders their review.

  python tools/artgen/packs/w3f_library.py                    # art/generated/W3F-library-audit/ + _review.png
  python tools/artgen/packs/w3f_library.py --stage DIR        # also write the PNGs under DIR/source_data/tod_ui_images/_images/
  python tools/artgen/packs/w3f_library.py --check [--root DIR]
        regenerate the tier strips in memory; fail on any byte != the installed PNGs (or DIR's), on a size change, on
        the two strips' words drifting apart, or on a GDT block that is not "uncompressed" (420 x 90: 90 is not a
        multiple of 4). (pk01 --check covers the same bytes plus the panel wiring; this is the pack's own proof.)

Deterministic: no randomness, no clock. Never hand-edit a generated PNG; change this file and re-run it.
"""
import argparse, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import artgen  # noqa: E402
from synthwave import (Svg, chamfer, poly_d, inset, mix, put_text, neon_word, text_width, _paste)  # noqa: E402
import r4_synthwave_hud as r4  # noqa: E402  (the deal panel's own grammar: layered, bevel, neon_glyph, coverage, LB)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

PACK = 'W3F-library-audit'
ROOT = artgen.ROOT
IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')
GDT_REL = os.path.join('source_data', 'tod_ui_images.gdt')
OUT = os.path.join(ROOT, 'art', 'generated', PACK)

# ============================================================================== the tier floor-gate strips
GATE_NAMES = ['i_tod_tier_gate_2', 'i_tod_tier_gate_3']
GATE_SIZE = (420, 90)
HUE = 'amber'
TG = r4.LB              # chamfer(4, 8, 416, 82, tl=14, br=14): the LUCK badge's plate
TG_WELL = r4.LB_WELL    # chamfer(13, 15, 79, 75, tl=9, br=9): its icon well
TEXT_CX, TEXT_W, TEXT_BASE, TEXT_CAP = 247, 306, 56, 25.0     # r4.luck_badge's text slot, measured there
AT_SCALE = 0.75         # "AT" set small and lavender (docs/73's legibility treatment, kept by PK01)
# the descent's requirement: the floor the player stands on when the tier clears (50 - 10 / 50 - 30). pk01's
# check_wiring proves these against TIER_FLOOR_TO_TIER, TOD_TIER*_FLOOR and TOD_GAUGE_LAPS; read them from there.
GATE_TOKENS = None


def tokens(t):
    global GATE_TOKENS
    if GATE_TOKENS is None:
        import pk01_card_text_rebake as pk01
        GATE_TOKENS = {k: list(v) for k, v in pk01.GATE_TOKENS.items()}
    return GATE_TOKENS[t]


def chevron_down(cx, cy, w, h, t):
    """A down-pointing chevron band: apex at the bottom, arms rising to (cx +- w, cy - h/2), t thick (vertical)."""
    return [(cx - w, cy - h / 2), (cx, cy + h / 2), (cx + w, cy - h / 2), (cx + w, cy - h / 2 - t), (cx, cy + h / 2 - t),
            (cx - w, cy - h / 2 - t)]


def chevrons_cov(W, H):
    """(white coverage, accent coverage): the trailing (upper) chevron white-hot, the LEADING (lower) one the accent -
    the descent's arrow, pointing down into the tower."""
    cx, w, h, t = 46.0, 19.5, 14.0, 8.0          # spans ~39 x 38 of the 66 x 60 well, as the LUCK clover does
    up = '<path d="%s" fill="#fff"/>' % poly_d(chevron_down(cx, 40.0, w, h, t))
    lo = '<path d="%s" fill="#fff"/>' % poly_d(chevron_down(cx, 56.0, w, h, t))
    return r4.coverage(W, H, up), r4.coverage(W, H, lo)


def _layout(cap):
    """[(token, colour, glow, cap, slot width)] for both tiers on ONE set of slots, and the row's total width."""
    gap = text_width('A A', cap) - text_width('AA', cap)          # the typeface's own word space at this cap
    two, three = tokens(2), tokens(3)
    spec = [('white', None, 1.0), ('white', None, 1.0), ('lav', None, AT_SCALE), ('white', None, 1.0), (HUE, HUE, 1.0)]
    slots, total = [], 0.0
    for i, (col, glow, k) in enumerate(spec):
        c = cap * k
        wd = max(text_width(two[i], c), text_width(three[i], c))
        slots.append((col, glow, c, wd))
        total += wd + (gap if i < len(spec) - 1 else 0.0)
    return slots, gap, total


def gate_cap():
    cap = TEXT_CAP
    while _layout(cap)[2] > TEXT_W and cap > 14:
        cap -= 0.25
    return cap


def tier_gate(t):
    """TIER t AT FLOOR n, 420 x 90, in the deal panel's LUCK-badge grammar (r4.luck_badge), amber."""
    W, H = GATE_SIZE

    def base(s):
        s.plate(TG, 'tier_fill', top='tier_top')
        s.glow_fill(inset(TG, 8), HUE, 0.07, 16)
        s.path(poly_d(TG_WELL), fill='url(#%s)' % s.rad([(0, mix(HUE, 'void', 0.84), 1), (1, 'deep', 1)]))
        s.steel(TG, 1.8)
        r4.bevel(s, TG, 2.4)

    def top(s):
        s.tube(poly_d(TG), HUE, 2.6, glow=0.8, spread=0.42)
        s.tube(poly_d(TG_WELL), 'accent2', 1.6, glow=0.4, spread=0.4)    # the luck badges' rule: the well is accent2

    im = r4.layered(W, H, base, top, seed=540 + t, base_alpha=0.95)
    wc, ac = chevrons_cov(W, H)
    im.alpha_composite(r4.neon_glyph(wc, ac, HUE, sigma=3.0, k=0.7))
    cap = gate_cap()
    slots, gap, total = _layout(cap)
    words = tokens(t)
    pen = TEXT_CX - total / 2.0
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for i, (col, glow, c, wd) in enumerate(slots):
        cx = pen + wd / 2.0                                   # centred in its slot: 2 / 3 and 40 / 20 swap in place
        if glow:
            neon_word(layer, words[i], c, TEXT_BASE, glow, cx=cx)
        else:
            put_text(layer, words[i], c, TEXT_BASE, col, cx=cx)
        pen += wd + gap
    im.alpha_composite(layer)
    return im


def build():
    """{name: RGBA} - the tier strips (the gift art is make_gift_art.py's)."""
    out = {}
    for t, n in zip((2, 3), GATE_NAMES):
        im = tier_gate(t).convert('RGBA')
        if im.size != GATE_SIZE:
            raise SystemExit('w3f: %s came out %s, not %s' % (n, im.size, GATE_SIZE))
        out[n] = im
    return out


def gate_problems(root, imgs):
    bad = []
    for n, im in imgs.items():
        p = os.path.join(root, IMG_REL, n + '.png')
        if not os.path.isfile(p):
            bad.append('MISSING %s' % p)
            continue
        if open(p, 'rb').read() != artgen.png_bytes(im):
            bad.append('STALE %s (run: python tools/artgen/packs/pk01_card_text_rebake.py --install - pk01 owns the file)' % p)
    two, three = tokens(2), tokens(3)
    if [w for i, w in enumerate(two) if i not in (1, 4)] != [w for i, w in enumerate(three) if i not in (1, 4)]:
        bad.append('the two strips no longer share their words (only the tier digit and the floor may differ): %s / %s' % (two, three))
    try:
        gdt = open(os.path.join(root, GDT_REL), encoding='utf-8', errors='replace').read()
    except OSError:
        gdt = ''
    for n in GATE_NAMES:
        m = re.search(r'"%s" \( "image\.gdf" \)\s*\{(.*?)\n\t\}' % re.escape(n), gdt, re.S)
        if not m or '"compressionMethod" "uncompressed"' not in m.group(1):
            bad.append('GDT: %s must stay "uncompressed" (420 x 90: 90 is not a multiple of 4)' % n)
    return bad

# ===================================================================================== review
REVIEW_BG = (24, 20, 34, 255)


def _old(rel_name, base_dir):
    p = os.path.join(base_dir, IMG_REL, rel_name + '.png') if base_dir else None
    if not p or not os.path.isfile(p):
        p = os.path.join(ROOT, IMG_REL, rel_name + '.png')
    return Image.open(p).convert('RGBA')


def _label_row(label, items, height, gap=14):
    from PIL import ImageDraw, ImageFont
    f = ImageFont.truetype(artgen.TTF, 18)
    ims = [it if it.height == height else it.resize((max(1, int(it.width * height / it.height)), height), Image.LANCZOS)
           for it in items]
    W = sum(i.width for i in ims) + gap * (len(ims) + 1)
    row = Image.new('RGBA', (max(W, 600), height + 40), REVIEW_BG)
    ImageDraw.Draw(row).text((gap, 8), label, fill=(225, 220, 240, 255), font=f)
    x = gap
    for i in ims:
        row.alpha_composite(i, (x, 34))
        x += i.width + gap
    return row


def _stack(rows, out):
    W = max(r.width for r in rows)
    sheet = Image.new('RGBA', (W, sum(r.height for r in rows)), REVIEW_BG)
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height
    sheet.save(out)
    return out


def _zoom(im, box, k):
    c = im.crop(box)
    return c.resize((c.width * k, c.height * k), Image.NEAREST)


def gate_panel_rows(old, new):
    """The strip in the REAL upgrade panel (pk01.panel_frames: the real tod_upgrade.lua + TodPull under the timed LUI
    mock), OLD vs NEW: an Archer floor-blocked for tier 2 on an ordinary deal (the gutter, 1080p), and an Archer whose
    right card is the locked TIER 3 card (the stamp across its illustration, settled)."""
    import pk01_card_text_rebake as pk01
    lua = os.path.join(ROOT, pk01.UPG_LUA_REL)
    rows = []
    shots = {}
    for tag, imgs in (('old', old), ('new', new)):
        try:
            gut, = pk01.panel_frames(lua, imgs, 2, 10, (3, 1, 2), [1.2], 1.5)
            st, = pk01.panel_frames(lua, imgs, 2, 30, (24, 1, 3), [1.2], 1.5)
        except Exception as ex:      # lupa missing or a mock break: the strips-only rows still stand
            print('w3f: panel render skipped (%s)' % ex)
            return rows, shots
        shots[tag] = (gut, st)
    for tag in ('old', 'new'):
        gut, st = shots[tag]
        gut.save(os.path.join(OUT, '_screen_deal_gutter_%s.png' % tag))
        st.save(os.path.join(OUT, '_screen_deal_stamp_%s.png' % tag))
    crop = lambda fr, box: fr.crop(tuple(int(round(v * 1.5)) for v in box))
    rows.append(_label_row('THE REAL DEAL PANEL at 1080p (1:1) - the gutter under CLASS: OLD | NEW, then the luck badges '
                           'they sit with', [crop(shots['old'][0], (25, 125, 405, 300)), crop(shots['new'][0], (25, 125, 405, 300)),
                                             crop(shots['new'][0], (930, 130, 1250, 290))], 262))
    rows.append(_label_row('... the stamp across a floor-locked TIER 3 card (settled): OLD | NEW',
                           [crop(shots['old'][1], (600, 216, 980, 606)), crop(shots['new'][1], (600, 216, 980, 606))], 585))
    rows.append(_label_row('... the whole panel at half size: OLD | NEW (gutter case)',
                           [shots['old'][0].resize((960, 540), Image.LANCZOS), shots['new'][0].resize((960, 540), Image.LANCZOS)], 540))
    return rows, shots


def gift_rows(stage_img, base_dir):
    """THE DEALER'S GIFT lettering: OLD vs NEW beside the siblings, at art size and in the spin screen."""
    rows = []
    names = ('i_tod_spin_banner_gift', 'i_tod_spin_tile_gift')
    if not stage_img or not all(os.path.isfile(os.path.join(stage_img, n + '.png')) for n in names):
        print('w3f: gift review skipped - no staged gift art (run the staged make_gift_art.py into the stage tree first)')
        return rows
    new = {n: Image.open(os.path.join(stage_img, n + '.png')).convert('RGBA') for n in names}
    old = {n: _old(n, base_dir) for n in names}
    sib = lambda n: _old(n, None)
    rows.append(_label_row('BLACK MARKET STAMPS at art size / 2: LEGENDARY | RARE (siblings) | ON THE HOUSE OLD | NEW',
                           [sib('i_tod_spin_banner_legendary'), sib('i_tod_spin_banner_rare'), old[names[0]], new[names[0]]], 104))
    foot = lambda im: im.crop((0, 290, 560, 416))
    rows.append(_label_row('REEL TILE FEET at art size (1:1): RARE | LEGENDARY | COMMON (siblings) | COMPANION OLD | NEW',
                           [foot(sib('i_tod_spin_tile_rare')), foot(sib('i_tod_spin_tile_legendary')), foot(sib('i_tod_spin_tile_common')),
                            foot(old[names[1]]), foot(new[names[1]])], 126))
    ctx = spin_context(old, new)
    if ctx:
        rows.append(_label_row('THE GIFT IN THE BLACK MARKET (the real TodSpinReel.lua under the timed mock, 1080p): the reel '
                               'and stamp, OLD | NEW', [ctx['old'], ctx['new']], 450))
        leg = spin_legendary()
        if leg is not None:
            rows.append(_label_row('... and a LEGENDARY landing on the same screen for comparison (unchanged)', [leg], 450))
    return rows


def _spin_frame(imgs, gift, t_frac=None):
    """One frame of the real reel (tools/ui_mockup/render_spin.py's driver) with `imgs` overriding the shipped art."""
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'ui_mockup'))
    import render_spin as rs
    import render_pull as rp
    rp.SCALE = 1
    rp._cache.clear()
    if hasattr(rp, '_sized'):
        rp._sized.clear()
    rp._cache.update(imgs)
    here = os.getcwd()
    try:
        if gift is not None:
            ev, end = rs.gift_schedule(4242, gift, 80)
        else:
            ev, end = rs.schedule(4242, 5, 3, 80, [0, 0, 0], 0, False, 1)
        L, reel = rs.runtime()
        g = L.globals()
        bg = rp.backdrop()
        land = [e[0] for e in ev if e[1] == 'tod_spin_land'][0]
        at = land + 1.2
        for et, name, args in ev:
            if et > at:
                break
            g.ADVANCE(max(0, et * 1000 - g.NOW))
            g.NOTIFY(name, L.table(*args))
        g.ADVANCE(max(0, at * 1000 - g.NOW))
        fr = rp.draw([dict(x) for x in g.DUMP(reel).values()], bg)
    finally:
        os.chdir(here)
    return fr


def spin_context(old, new):
    try:
        res = {}
        for tag, imgs in (('old', old), ('new', new)):
            fr = _spin_frame(imgs, 1)
            fr.convert('RGB').save(os.path.join(OUT, '_screen_gift_%s.png' % tag))
            res[tag] = fr.crop((380, 120, 900, 440)).resize((780, 480), Image.LANCZOS)
        return res
    except Exception as ex:
        print('w3f: spin render skipped (%s)' % ex)
        return None


def spin_legendary():
    try:
        fr = _spin_frame({}, None)
        return fr.crop((380, 120, 900, 440)).resize((780, 480), Image.LANCZOS)
    except Exception as ex:
        print('w3f: legendary spin render skipped (%s)' % ex)
        return None


def review(imgs, base_dir, stage_img):
    old = {n: _old(n, base_dir) for n in GATE_NAMES}
    rows = []
    rows.append(_label_row('TIER GATE STRIPS 420 x 90 (= 1:1 at 1080p): OLD tier 2 | NEW tier 2 | OLD tier 3 | NEW tier 3',
                           [old[GATE_NAMES[0]], imgs[GATE_NAMES[0]], old[GATE_NAMES[1]], imgs[GATE_NAMES[1]]], 90))
    small = [im.resize((280, 60), Image.LANCZOS) for im in (old[GATE_NAMES[0]], imgs[GATE_NAMES[0]], old[GATE_NAMES[1]], imgs[GATE_NAMES[1]])]
    rows.append(_label_row('... at 280 x 60 (1:1 at 720p)', small, 60))
    rows.append(_label_row('NEW beside its deal-panel siblings (R4 LUCK badge 40 / 100, BETTER CARDS), 1:1',
                           [imgs[GATE_NAMES[0]], _old('i_tod_badge_luck_40', None), _old('i_tod_badge_luck_100', None),
                            _old('i_tod_luck_legend', None)], 90))
    rows.append(_label_row('ZOOM x3: the NEW well and the swap-in-place words (tier 2 over tier 3)',
                           [_zoom(imgs[GATE_NAMES[0]], (0, 0, 210, 90), 3), _zoom(imgs[GATE_NAMES[1]], (0, 0, 210, 90), 3)], 270))
    rows.append(_label_row('ZOOM x3: the right half, tier 2 | tier 3',
                           [_zoom(imgs[GATE_NAMES[0]], (210, 0, 420, 90), 3), _zoom(imgs[GATE_NAMES[1]], (210, 0, 420, 90), 3)], 270))
    prow, _ = gate_panel_rows(old, imgs)
    rows += prow
    rows += gift_rows(stage_img, base_dir)
    return _stack(rows, os.path.join(OUT, '_review.png'))

# ======================================================================================= main


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--stage', help='also write the PNGs under DIR/source_data/tod_ui_images/_images/')
    ap.add_argument('--check', action='store_true', help='fail on any byte != the installed PNGs (or --root DIR)')
    ap.add_argument('--root', help='with --check: read DIR/... instead of the repo')
    ap.add_argument('--base', help='review: the dir holding the untouched OLD files (DIR/source_data/...); default the repo')
    ap.add_argument('--gift', help='review: the dir holding the staged NEW gift art (an _images folder)')
    ap.add_argument('--no-review', action='store_true')
    a = ap.parse_args()
    imgs = build()
    if a.check:
        bad = gate_problems(a.root or ROOT, imgs)
        if bad:
            for b in bad:
                print('W3F LIBRARY: ' + b)
            sys.exit(1)
        print('W3F LIBRARY OK (%d tier strips byte-exact, shared words, uncompressed GDT blocks)' % len(imgs))
        return
    os.makedirs(OUT, exist_ok=True)
    for n, im in imgs.items():
        md5 = artgen.save_png(im, os.path.join(OUT, n + '.png'), allow_any_size=True)
        print('%-22s %s  cap %.2f' % (n, md5, gate_cap()))
        if a.stage:
            artgen.save_png(im, os.path.join(a.stage, IMG_REL, n + '.png'), allow_any_size=True)
    if not a.no_review:
        print('review ->', review(imgs, a.base, a.gift))


if __name__ == '__main__':
    main()
