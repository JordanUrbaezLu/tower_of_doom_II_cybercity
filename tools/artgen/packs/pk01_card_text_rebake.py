"""PK01 - re-bake the class-draft cards and the tier-gate strips (2026-10-04,
tmp/asset_prod/packs/PK01-card-text-rebake.json).

WHAT IT MAKES (two same-name drop-ins; every GDT block and zone line already exists):

  i_tod_card_class_assault / _heavy / _slasher - NO LONGER THIS PACK'S (R6, 2026-10-05): all four class draft cards
      are written and --checked by tools/artgen/packs/r6_class_cards.py (one owner per file), which re-sets every word
      in the map's typeface and redraws the four art windows one way. The card re-bake below (rebake_card and its
      machinery) stays as the record, and R6 imports its pinned name-box chassis and bracket template. Its old job:
      the lower name box carried a divider rule and a SIDEARM under the primary (BOW / MAGNUM, MOZAMBIQUE / MR6,
      ONE INCH PUNCH / AMP63); the rule and the sidearm were erased and the name re-centred.

  i_tod_tier_gate_2 / _3 (420x90, drawn 280x60; "uncompressed" in the GDT, so 90 need not divide by 4)
      The CLASS TIER floor-gate badge on the upgrade panel (the gutter badge, and the stamp across a tier
      card locked by floor). The shipped strips read TIER 2 AT FLOOR 10 / TIER 3 AT FLOOR 30 under an UP
      chevron: the CLIMB's numbers. Tower II descends - the requirement is 10 / 30 floors of progress,
      shown as the floor the player stands on when it clears, 50 - need = 40 / 20 (tod_upgrade.lua
      tierFloorShown, _tod_gauge.gsc tier_floor_display) - so the art was switched off
      (USE_TIER_GATE_ART = not TIER_DESCENT) and a bare engine-font line stood in. Here they read
      TIER 2 AT FLOOR 40 / TIER 3 AT FLOOR 20 with the chevrons pointing DOWN.
      SINCE W3F (2026-10-05, the one-library audit) the strips' PIXELS come from tools/artgen/packs/w3f_library.py
      tier_gate(): the deal panel's synthwave LUCK-badge grammar in amber, the same tokens, the same shared slots.
      This pack still OWNS the two files (writes, --checks bytes, wiring and the descent arithmetic); the
      Map 1 pill re-bake below (strip_chassis / build_gate) is kept as the record and is no longer drawn.

THE CARDS ARE MOVED, NOT RE-SET. Every word on these cards (header, art-window title, class banner,
name) is in the RETIRED typeface - its S is a 5: "5KULL", "CLO5E". Re-setting only the name in today's
face would put two faces on one card and break the four-card draft row, and the retired face must never
be drawn again (CLAUDE.md 2026-09-29). So the name's own pixels are lifted off the box and put back
down lower; nothing is re-typeset. (A whole-card re-bake in the current face is a separate pass.)
How the lift works, per card (every number was measured; LAND.md has the evidence):

  1. THE BOX BACKGROUND = the shared CHASSIS + this card's class elements.
     * The chassis - a flat (8, 8, 10) crossed by six faint neutral hairlines (each a bright 1 px core
       with a faint dark edge) and a slightly lit top row - is the same on all 18 cards built on this
       frame (6 class + 12 tier; max difference 3 levels away from their text).
       art/rebake_src/PK01/i_tod_card_chassis_namebox.png is built ONCE by --derive-chassis from those
       cards (each pinned by sha256 in DONORS): per pixel, the median of the cards whose text, rules,
       brackets and inner lines are all > DONOR_CLEAR px away (the darker view where only two are).
       Where every card has text (the centre band) it is the flat fill + the two hairlines that cross
       it (SCRATCHES, traced on the Archer card where they show). A pasted name panel is its own clean
       block (PLAIN_RECT: the Warrior's shows none of the hairlines), so none are drawn back into it.
     * The corner brackets' glow is one shape on every card (the Breacher's = the Archer's x 0.686 in
       luminance, 3.4 levels worst residual). Its template is the Archer card's: at each pixel the
       darkest of its four mirrored corner readings (the box is symmetric about x 383.5 / y 854.5;
       the one hairline crossing a bracket's glow and the rule's end halo are each in one corner
       only), scaled per channel to this card on its own bottom brackets.
     * An opaque inner top line (the Warrior's, violet) glows a few rows down, uniformly across x: a
       per-row profile read on the columns its name never reaches.
     Bracket strokes and the inner line itself are opaque and never rewritten.
  2. THE RULE'S HALO is subtracted from the name's glow tail where the two overlap - measured per
     channel on the card's own clean columns, or (the Breacher, whose name spans the box) the Archer's
     red shape x the card's own ratios read below its rule.
  3. THE NAME: its glyph silhouette (fill + bevel + navy outline) is opaque and carried byte for byte.
     Its glow is the card's own data (card - background - halo) wherever the data holds the whole
     glow, and a fitted model - two Gaussians of the silhouette, per channel, non-negative least
     squares (RMSE 2.1-3.4 levels) - where it does not: inside a bracket's glow zone (the data there
     carries that zone's hairline), on a hairline, under the frame and an opaque inner line, and past
     a paste's clip (the Warrior's glow stops dead at row 878, where its name panel was pasted over
     the rule's halo). The two are feathered over FEATHER px. The new glow is drawn round the MOVED
     silhouette, so it is whole where the source's was hidden.
  4. The rule, the sidearm and every glow they cast become background (inside a bracket zone the old
     name glow is taken back off the card itself, so the zone's hairline stays); the name goes back
     down DY rows lower, DY centring its white fill where the Necromancer's is (rows 806..899, centre
     852.5). Every pixel no old or new content touches keeps the source's byte.

THE STRIPS ARE RE-SET IN THE MAP TYPEFACE. The shipped strips were set in Anton by the docs/73 drop's
own generator; since 2026-09-25 every letter and number on map art uses the map's own typography. The
line is drawn from the glyph-sheet cells TodGlyphRow draws in game, placed with the GENERATED
TodGlyphMetrics.lua (artgen.metrics / artgen._glyph), condensed by the map's own menu fit 0.91 (the TTF
menus' horizontal fit), at the largest cap that fits the docs/73 text zone: 28.25 px at 420, its white
fill ~24 px, sized to match the text of the CLASS badge stacked directly above it in the same gutter
(that badge is still baked in the retired face; the two read alike only because this line has no S).
docs/73 asked for a 40-44 px cap, which assumed Anton's narrow caps - the map face is wider, so this
pass supersedes that number for it. The docs/73 legibility treatment stays:
TIER / FLOOR in the cell's own white, AT at 0.75 of the cap in light grey #C8D0DC, the floor number in
the chevron's amber #FFC84D (the fill is recoloured; the cell's blue-grey bevel and navy outline stay,
the CLASS badge's own treatment), a thick near-black outer stroke and a soft dark drop shadow, nothing
glowing behind the letters. The chassis outside the text zone is the shipped strip's byte for byte;
inside it the old type is removed row by row (each interior row back to its own mode colour, so the
pill's faint scan lines survive - the docs/73 generator's own method); the chevron pair is mirrored
about the disc's centre (rows y -> 89 - y inside radius DISC_R of DISC_C, a circle that holds only the
flat pale fill and the chevrons) so it points DOWN, its bright leading chevron now the lower one. The
pair shares one set of token slots, so the two strips differ only in their digit glyphs and swap on
screen without the line moving (docs/73's runtime contract). Both are built on gate_2's chassis.

USAGE
  python -B tools/artgen/packs/pk01_card_text_rebake.py              # art/generated/PK01-card-text-rebake/ + _review.png
        [--lua FILE]   the tod_upgrade.lua the review's panel renders run (the real menu + THE PULL under
                       tools/ui_mockup's timed LUI mock); default the repo's - before the landing pass the merged
                       file, the repo one draws no strip yet (the renders are skipped, with the reason, if so)
  python -B tools/artgen/packs/pk01_card_text_rebake.py --stage DIR  # also write the PNGs under DIR/source_data/tod_ui_images/_images/
  python -B tools/artgen/packs/pk01_card_text_rebake.py --install    # copy into source_data/tod_ui_images/_images/ (the landing)
  python -B tools/artgen/packs/pk01_card_text_rebake.py --check [--root DIR]
        regenerate in memory and fail on any byte that differs from the installed PNGs (or the ones under
        DIR), on a source that is not the pinned one, and on any break in the wiring (the GDT blocks and
        their compression, the zone lines, the class-draft registration, USE_TIER_GATE_ART on, the
        strips registered, and the descent arithmetic that makes the baked 40 / 20 true).
  python -B tools/artgen/packs/pk01_card_text_rebake.py --derive-chassis
        rebuild art/rebake_src/PK01/i_tod_card_chassis_namebox.png from the 18 DONORS (each must still
        be the pinned file). Only needed to re-derive the chassis; the normal run never reads a donor.

SOURCES are the shipped PNGs as they stood before this pass, copied to art/rebake_src/PK01/ and pinned
by sha256 (the generator reads only those, never the installed file it overwrites). Deterministic: no
randomness, no timestamps. Never hand-edit an output; change this file and re-run it.
"""
import argparse, hashlib, os, re, sys, warnings

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402

PACK = 'PK01-card-text-rebake'
ROOT = artgen.ROOT
SRC_DIR = os.path.join(ROOT, 'art', 'rebake_src', 'PK01')
IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')
GDT_REL = os.path.join('source_data', 'tod_ui_images.gdt')
ZONE_REL = os.path.join('zone_source', 'zm_tod2_cybercity.zone')
UPG_LUA_REL = os.path.join('ui', 'uieditor', 'menus', 'hud', 'tod_upgrade.lua')
CLS_LUA_REL = os.path.join('ui', 'uieditor', 'menus', 'hud', 'tod_class_select.lua')
UPG_GSC_REL = os.path.join('scripts', 'zm', 'zm_tod2_cybercity', '_tod_upgrades.gsc')
GAUGE_GSC_REL = os.path.join('scripts', 'zm', 'zm_tod2_cybercity', '_tod_gauge.gsc')

SOURCES = {   # the shipped files as they stood before this pass (art/rebake_src/PK01/)
    'i_tod_card_class_assault': '29b4c59fc8665f29bb75ae4f24f7ebb9abb9fd29af03ee1248b043f7ef9e6a18',
    'i_tod_card_class_heavy':   '4346814b2e4e83f1169a1abdcfdaa6f9c5e312241a10a71bd0b4906b89f7d55d',
    'i_tod_card_class_slasher': '72d33f32151467e9e9aec7b4f04d3ced7c7662a70d4e22415c509baca2224743',
    'i_tod_tier_gate_2':        '52b9c506c5a0a4c4a2396b1d7d8d1f41d699dd574ed2a0107b7d74234539128b',
    'i_tod_tier_gate_3':        'aba60d3301d64a590a82ae82d57ef01a431c11d366ee8d63911c893fdc2a3dc4',
}
CHASSIS_NAME = 'i_tod_card_chassis_namebox'      # derived; its sha256 is pinned below once derived
CHASSIS_PIN = os.path.join(SRC_DIR, CHASSIS_NAME + '.sha256')
DONORS = {   # --derive-chassis only: every card on this frame, as shipped on 2026-10-04
    'i_tod_card_class_mage':         'source_data/tod_ui_images/_images|6a133c5d58f6ff9d7c5a7775f5abb2ec053d0a07aa8478fb6ff6274a1921c033',
    'i_tod_card_class_necromancer':  'source_data/tod_ui_images/_images|fff13f1c62f5d5bd803913c06a91d21984764bdc29a692f45aaecd3ab54c7e37',
    'i_tod_card_class_skirmisher':   'source_data/tod_ui_images/_images|eae205b576e49c7091a891ac7637c4fe89d32fd80f6c65d481faaa0c114a6147',
    'i_tod_card_tier_assault_2':     'source_data/tod_ui_images/_images|1a2b81b0a8835c97e5a67ee5e198945581b19a2d1e64a38c8914af80d53e49fe',
    'i_tod_card_tier_assault_3':     'source_data/tod_ui_images/_images|5e6b9f548a0115ae09f5f2705482fbf184e13fb144c4c78467b115495220f598',
    'i_tod_card_tier_heavy_2':       'source_data/tod_ui_images/_images|e2a1c825c8e4eba00b1dd6bde83b8dfddafdbbbdd380ee7b22b4d897e6b380bb',
    'i_tod_card_tier_heavy_3':       'source_data/tod_ui_images/_images|28a884d98066f852391477c15e24b3993ca067600cbeb0259704ffab084ff507',
    'i_tod_card_tier_mage_2':        'source_data/tod_ui_images/_images|642dfe065ec50f024aa92827946e33862cded4931013a842567b08bc6237130d',
    'i_tod_card_tier_mage_3':        'source_data/tod_ui_images/_images|337749f6f910d8c8703986fedf3aa499e17ac2ba3bd74a2d142412887b567b95',
    'i_tod_card_tier_necromancer_2': 'source_data/tod_ui_images/_images|4c6e1717e9212250ed0918e100dadeae43f3cb4234db2c49eda45e5a45fb106a',
    'i_tod_card_tier_necromancer_3': 'source_data/tod_ui_images/_images|ffc1168696553a3390c87df0b1a6c10b1df8e792580c92c9a8bf979f4d228e73',
    'i_tod_card_tier_skirmisher_2':  'source_data/tod_ui_images/_images|cd5c9814b0d94dcece9c914682da3fb72b55b9bd8e4354b80bb19a00d8d35036',
    'i_tod_card_tier_skirmisher_3':  'source_data/tod_ui_images/_images|6e601711142b7cab9ffa31faca47a9a245930cde9827640064398bb7b63381eb',
    'i_tod_card_tier_slasher_2':     'source_data/tod_ui_images/_images|47fa22608aa736758afec8e40de2bfeff3f7e9621b767fe089a240808925c2b9',
    'i_tod_card_tier_slasher_3':     'source_data/tod_ui_images/_images|e4d9db223a47b3e0f5498d49a13f2502bf86ee8c0c190f891391b19c8d4094e7',
    'i_tod_card_class_assault':      'art/rebake_src/PK01|' + SOURCES['i_tod_card_class_assault'],
    'i_tod_card_class_heavy':        'art/rebake_src/PK01|' + SOURCES['i_tod_card_class_heavy'],
    'i_tod_card_class_slasher':      'art/rebake_src/PK01|' + SOURCES['i_tod_card_class_slasher'],
}
CARD_NAMES = []    # R6 (r6_class_cards.py) owns the four class draft cards since 2026-10-05
GATE_NAMES = ['i_tod_tier_gate_2', 'i_tod_tier_gate_3']
NAMES = CARD_NAMES + GATE_NAMES
LUM = np.array([0.299, 0.587, 0.114])


def sha256_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_pinned(path, sha, what):
    if not os.path.isfile(path):
        raise SystemExit('PK01: missing %s %s' % (what, path))
    got = sha256_file(path)
    if got != sha:
        raise SystemExit('PK01: %s %s is not the pinned file (sha256 %s, found %s) - the generator re-bakes '
                         'from the pre-pass files only' % (what, path, sha, got))
    return Image.open(path).convert('RGBA')


def load_source(name):
    return load_pinned(os.path.join(SRC_DIR, name + '.png'), SOURCES[name], 'source')


def lum(rgb):
    return rgb @ LUM


def disc(r):
    rr = np.arange(-r, r + 1)
    return (rr[:, None] ** 2 + rr[None, :] ** 2) <= r * r


def runs(rows):
    out, s, p = [], None, None
    for r in rows:
        if s is None:
            s = p = r
        elif r == p + 1:
            p = r
        else:
            out.append((s, p))
            s = p = r
    if s is not None:
        out.append((s, p))
    return out

# =========================================================================================== THE CARDS

FLAT = np.array([8.0, 8.0, 10.0])         # the name box's fill (every clean pixel of the 18 cards)
Y0, Y1, X0, X1 = 763, 946, 104, 664       # the box interior (the frame is rows 758-762 / 946-950)
INTERIOR = (764, 946, 106, 662)           # where text / rules / lines can live (rows, cols; exclusive)
NECRO_FILL_CENTRE = 852.5                 # i_tod_card_class_necromancer: white fill rows 806..899
CORE_LUM = 40.0                           # names / rules / sidearms / brackets sit far above this; scratches below 25
GLOW_R = 24                               # px: the reach of a name's glow (at 0 by 20-22 px from its nearest core pixel)
RULE_REACH = 26                           # px: the rule's halo, above and below it and past its rounded ends
BRACKET_REACH = 14                        # px: a bracket's glow (1 level by 14 px)
DONOR_CLEAR = 30                          # px: a donor pixel counts for the chassis this far from that donor's text
MIRROR_X, MIRROR_Y = 767, 1709            # x' = 767 - x, y' = 1709 - y: the box's symmetry (brackets at
                                          # x 106-144 / 623-661, rows 766-804 / 905-943)

# Three of the chassis hairlines cross the band every card's text covers, so the donors cannot see all
# of them there: modelled where no donor shows them (x0, y0, x1, y1, peak delta). Traced where they show
# clear of a name's glow (centroid fits): A 798.63 + 0.2463 (x - 498) over x 498..554 (774.76 at its start
# on i_tod_card_tier_mage_2), B 839.36 + 0.0408 (x - 486) over x 488..588, both on the Archer source; C
# 869.00 - 0.1391 (x - 400) over x 353..468 on the Breacher source, just above its rule (the Archer shows
# the same line from x 354 until BOW's glow hides it at ~430; both start at x ~354, two rows above the rule).
# 1 px neutral lines (C's core +8.5 / +9.5 / +8.5 RGB), profiles integrating to ~1.2 x the peak; C's
# peak is the least-squares fit of this layer on the Breacher (8.85, residual 3.5 levels rms). Without C
# the line was read as part of the name's glow and rode down with it (review 2026-10-04: the Archer's
# copy 33 rows low at x 352..427, the Breacher's 31).
SCRATCHES = [
    (401.5, 774.86, 556.0, 812.92, 11.0),   # A
    (487.5, 839.42, 589.0, 843.56, 4.5),    # B
    (353.0, 875.54, 468.0, 859.54, 8.85),   # C
]
SCRATCH_W = 1.15

CLEAN_COLS = {   # columns each name never reaches (per-row background + the inner line's glow profile)
    'i_tod_card_class_assault': [(175, 262), (505, 595)],
    'i_tod_card_class_heavy':   [],                       # MOZAMBIQUE spans the whole box
    'i_tod_card_class_slasher': [(175, 235), (535, 595)],
}
BELOW_CLEAN_COLS = {   # columns clear of the sidearm (the halo's channel ratios, below the rule)
    'i_tod_card_class_assault': [(170, 280), (485, 600)],
    'i_tod_card_class_heavy':   [(170, 300), (460, 600)],
    'i_tod_card_class_slasher': [(170, 300), (465, 600)],
}
HALO_ROWS = 22                             # rows above the rule its halo reaches
INNER_LINE_ROWS = (763, 790)               # where an inner top line and its glow live (the Warrior's: 770-772)


def scratch_layer(h, w, oy, ox, which=SCRATCHES):
    """The hairlines as an (h, w) neutral delta field for the window at (oy, ox)."""
    ss = 8
    out = np.zeros((h, w))
    for x0, y0, x1, y1, peak in which:
        layer = Image.new('L', (w * ss, h * ss), 0)
        ImageDraw.Draw(layer).line([((x0 - ox) * ss, (y0 - oy + 0.5) * ss), ((x1 - ox) * ss, (y1 - oy + 0.5) * ss)],
                                   fill=255, width=int(round(SCRATCH_W * ss)))
        cov = np.asarray(layer, dtype=np.float64).reshape(h, ss, w, ss).mean(axis=(1, 3)) / 255.0
        out = np.maximum(out, cov * peak)
    return out


def bracket_strokes_full():
    """The four corner L brackets as a full-card mask (identical on every card of this frame), read on
    the Archer card, whose corners no text reaches."""
    rgb = np.asarray(load_source('i_tod_card_class_assault'), dtype=np.float64)[..., :3]
    core = lum(rgb - FLAT) > CORE_LUM
    win = np.zeros(core.shape, bool)
    for ya, yb in ((764, 806), (903, 947)):
        for xa, xb in ((104, 160), (608, 664)):
            win[ya:yb, xa:xb] = True
    m = core & win
    lab, k = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, k + 1))
    keep = [i + 1 for i, s in enumerate(sizes) if s >= 100]
    if len(keep) != 4:
        raise SystemExit('PK01: expected the four corner brackets on the Archer card, found %d' % len(keep))
    return np.isin(lab, keep)


def class_line_rows(L):
    """Rows of a uniform full-width class line (the Necromancer's / Warrior's inner lines): bright and
    flat across x - a name's row is never flat."""
    out = []
    for y in range(INTERIOR[0], INTERIOR[1]):
        row = L[y, 200:560]
        if np.median(row) > 12.0 and np.percentile(row, 90) - np.percentile(row, 10) < 12.0:
            out.append(y)
    return out


def derive_chassis():
    """The shared name-box background over the donor cards whose text, rules, class lines and brackets
    are all more than DONOR_CLEAR px from the pixel (see the comment below for the statistic). RGBA crop
    (Y0..Y1, X0..X1): alpha 255 where at least two donors saw it, 0 elsewhere (the centre band, rebuilt
    from FLAT + SCRATCHES)."""
    warnings.simplefilter('ignore')
    strokes = bracket_strokes_full()
    bz = ndi.binary_dilation(strokes, structure=disc(16))
    interior = np.zeros(strokes.shape, bool)
    interior[INTERIOR[0]:INTERIOR[1], INTERIOR[2]:INTERIOR[3]] = True
    stack, valid = [], []
    for name, spec in sorted(DONORS.items()):
        folder, sha = spec.split('|')
        im = load_pinned(os.path.join(ROOT, folder, name + '.png'), sha, 'donor')
        a = np.asarray(im, dtype=np.float64)[..., :3]
        L = lum(a - FLAT)
        core = (L > CORE_LUM) & ~strokes & interior
        for y in class_line_rows(L):
            core[y, INTERIOR[2]:INTERIOR[3]] = True
        v = ~ndi.binary_dilation(core, structure=disc(DONOR_CLEAR)) & ~bz
        stack.append(a[Y0:Y1, X0:X1])
        valid.append(v[Y0:Y1, X0:X1])
    stack, valid = np.stack(stack), np.stack(valid)
    # the per-pixel MEDIAN over the donors that saw the pixel where three or more did, the darker of the
    # two where only two did: a lone donor's far glow can only ADD light, so with two the darker view is the
    # chassis; with three or more the median also outvotes a donor whose pasted name panel hides a hairline
    # (a minimum there keeps a hairline's dark edge without its bright core)
    Ls = np.where(valid, lum(stack - FLAT), np.inf)
    pick = np.argmin(Ls, axis=0)
    darker = np.take_along_axis(stack, pick[None, ..., None], axis=0)[0]
    med = np.nanmedian(np.where(valid[..., None], stack, np.nan), axis=0)
    cnt = valid.sum(axis=0)
    ok = cnt >= 2
    rgb = np.where((cnt >= 3)[..., None], np.nan_to_num(med, nan=0.0), np.where(ok[..., None], darker, 0.0))
    out = np.dstack([np.clip(np.round(rgb), 0, 255), np.where(ok, 255, 0)]).astype(np.uint8)
    out[~ok] = 0
    return Image.fromarray(out, 'RGBA'), int((~ok).sum())


def load_chassis():
    p = os.path.join(SRC_DIR, CHASSIS_NAME + '.png')
    if not os.path.isfile(CHASSIS_PIN):
        raise SystemExit('PK01: no chassis pin %s - run --derive-chassis first' % CHASSIS_PIN)
    pin = open(CHASSIS_PIN, encoding='ascii').read().split()[0]
    im = load_pinned(p, pin, 'chassis')
    a = np.asarray(im, dtype=np.float64)
    rgb, ok = a[..., :3], a[..., 3] > 127
    h, w = rgb.shape[:2]
    model = FLAT[None, None, :] + scratch_layer(h, w, Y0, X0)[..., None]
    return np.where(ok[..., None], rgb, model)


_TEMPLATE = None


def bracket_template():
    """(strokes, zone, lumT) over the crop: the Archer card's bracket stroke cores, the glow zone round
    them, and the bracket GLOW TEMPLATE - at every pixel the darkest of the Archer card's four mirrored
    corner readings (luminance over the fill). The brackets are mirror images of each other, while the
    one hairline that crosses a bracket's glow (top-left) and the rule's halo (bottom corners) are each
    in one corner only, so the minimum is the glow alone."""
    global _TEMPLATE
    if _TEMPLATE is None:
        full = bracket_strokes_full()
        strokes = full[Y0:Y1, X0:X1]
        a = np.asarray(load_source('i_tod_card_class_assault'), dtype=np.float64)[..., :3]
        La = lum(a - FLAT)
        ys, xs = np.mgrid[Y0:Y1, X0:X1]
        reads = []
        for my in (False, True):
            for mx in (False, True):
                yy = (MIRROR_Y - ys) if my else ys
                xx = (MIRROR_X - xs) if mx else xs
                reads.append(La[yy, xx])
        lumT = np.clip(np.min(np.stack(reads), axis=0), 0.0, None)
        zone = ndi.binary_dilation(strokes, structure=disc(BRACKET_REACH))
        lumT[~zone] = 0.0
        lumT[ndi.binary_dilation(strokes, iterations=1)] = 0.0
        _TEMPLATE = (strokes, zone, lumT)
    return _TEMPLATE


def rule_rows(rgb):
    """The divider rule: the run in 860..900 whose median over x 200..560 is far above the fill."""
    rows = [y for y in range(860, 900) if np.median(lum(rgb[y, 200:560] - FLAT)) > 90.0]
    r = runs(rows)
    if len(r) != 1 or r[0][1] - r[0][0] > 4:
        raise SystemExit('PK01: expected one divider rule 1-5 rows tall, found %s' % r)
    return r[0]


def halo_shape():
    """The rule's halo above its top row: red channel over the fill, by distance 1..HALO_ROWS - measured
    on the Archer card's columns clear of BOW (the shape is the same on every card's rule)."""
    rgb = np.asarray(load_source('i_tod_card_class_assault'), dtype=np.float64)[..., :3]
    top, _ = rule_rows(rgb)
    cols = np.concatenate([np.arange(a, b) for a, b in CLEAN_COLS['i_tod_card_class_assault']])
    s = np.zeros(HALO_ROWS + 1)
    for d in range(1, HALO_ROWS + 1):
        s[d] = max(0.0, float(np.median(rgb[top - d, cols, 0] - FLAT[0])))
    return s


def halo_xfalloff():
    """The halo's reach across x: 1 over the rule's body, falling off past its rounded ends - the row 6
    above the Archer card's rule, normalised by its body (uniform under BOW, where the name glows)."""
    a = np.asarray(load_source('i_tod_card_class_assault'), dtype=np.float64)[..., :3]
    t, _ = rule_rows(a)
    row = np.clip(a[t - 6, :, 0] - FLAT[0], 0.0, None)
    body = float(np.median(row[180:260]))
    f = np.clip(row / max(body, 1e-6), 0.0, 1.0)
    f[262:505] = 1.0
    return f


def halo_ratios(rgb, name, bottom):
    """G/R and B/R of this card's rule halo, read below the rule (distance 2..6), clear of the sidearm."""
    cols = np.concatenate([np.arange(a, b) for a, b in BELOW_CLEAN_COLS[name]])
    rs = []
    for d in range(2, 7):
        m = np.median(rgb[bottom + d, cols] - FLAT, axis=0)
        if m[0] > 4:
            rs.append(m / m[0])
    return np.clip(np.median(np.array(rs), axis=0), 0.0, 1.5)


def bracket_colour(rgb, lumT, keep):
    """Per-channel scale of the bracket glow template for this card: least squares on its BOTTOM
    brackets' glow (rows >= 912, where no text, rule or sidearm reaches)."""
    D = rgb[Y0:Y1, X0:X1] - FLAT
    m = (lumT > 0.5) & ~keep
    m[:912 - Y0] = False
    t = lumT[m]
    return np.array([float(np.sum(D[..., c][m] * t) / np.sum(t * t)) for c in range(3)])


GLOW_SIGMAS = ((1.5, 2.0, 2.5, 3.0, 4.0), (5.0, 6.0, 7.0, 8.0, 10.0, 12.0))
GLOW_FIT_DIST = (2.0, 22.0)               # px from the glyph silhouette: the glow model is fitted out here
GLOW_TAPER = (24.0, 30.0)                 # the model glow fades to 0 between these distances (data: 0 by 22)
BZ_MARGIN = 12                            # px past a bracket's glow zone still treated as the zone (the top-left
                                          # hairline runs from the arm's tip at x 145 to x 164, the zone ends at 158)
CLIP_BOTTOM = {   # a name panel pasted over its own glow: the first row the paste hid the glow from
    'i_tod_card_class_slasher': 878,      # (the glow above it is whole; it ducks under the opaque inner line)
}
PLAIN_RECT = {   # x0, y0, x1, y1: a pasted name panel's clean block - the card's own background there has
    # none of the chassis hairlines (the Warrior's: A and B are absent at x 520-590, where no glow hides
    # them, as everywhere else in it), so none are drawn back into it
    'i_tod_card_class_slasher': (240, 774, 604, 879),
}
FEATHER = 4.0                             # px over which the name layer passes from the data to the model
SOFT_G = (15.0, 30.0)                     # in a bracket zone: below the first, the background is the card minus
                                          # the model glow (keeps that zone's hairline); above the second, the model


def glow_eval(sil, s1, s2, co):
    s = sil.astype(np.float64)
    g1, g2 = ndi.gaussian_filter(s, s1), ndi.gaussian_filter(s, s2)
    return np.stack([co[c][0] * g1 + co[c][1] * g2 for c in range(3)], axis=-1)


def fit_glow(sil, target, fitmask):
    """The name's glow as two Gaussians of its glyph silhouette, per channel, by non-negative least squares
    over `fitmask`; the sigmas from a small grid. Returns (s1, s2, coefficients, rmse)."""
    from scipy.optimize import nnls
    s = sil.astype(np.float64)
    best = None
    for s1 in GLOW_SIGMAS[0]:
        g1 = ndi.gaussian_filter(s, s1)
        for s2 in GLOW_SIGMAS[1]:
            g2 = ndi.gaussian_filter(s, s2)
            X = np.stack([g1[fitmask], g2[fitmask]], axis=1)
            co, err = [], 0.0
            for c in range(3):
                k, r = nnls(X, target[..., c][fitmask])
                co.append(k)
                err += r * r
            if best is None or err < best[0]:
                best = (err, s1, s2, co)
    err, s1, s2, co = best
    return s1, s2, co, float(np.sqrt(err / (3 * fitmask.sum())))


def rebake_card(name, chassis):
    src = load_source(name)
    arr = np.asarray(src, dtype=np.float64)
    rgb, alpha = arr[..., :3], arr[..., 3]
    win = rgb[Y0:Y1, X0:X1].copy()
    h, w = win.shape[:2]
    top, bottom = rule_rows(rgb)
    a_strokes, bzone, lumT = bracket_template()
    chassis = chassis.copy()
    pr = PLAIN_RECT.get(name)
    if pr:
        chassis[pr[1] - Y0:pr[3] - Y0, pr[0] - X0:pr[2] - X0] = FLAT
    Lw = lum(win - FLAT)
    Lraw = lum(win)

    # ---- 1. what never moves: this card's own bracket strokes (its colour shifts their AA edge a pixel
    #         against the Archer's) and an inner line; the background model round everything else -------
    strokes = (Lw > 20.0) & ndi.binary_dilation(a_strokes, iterations=3)
    keep = ndi.binary_dilation(strokes, iterations=1)
    kc = bracket_colour(rgb, lumT, keep)
    BGexp = chassis + lumT[..., None] * kc[None, None, :]
    line_rows = [y for y in class_line_rows(lum(rgb - FLAT)) if INNER_LINE_ROWS[0] <= y < INNER_LINE_ROWS[1]]
    if line_rows:
        cc = np.concatenate([np.arange(a, b) for a, b in CLEAN_COLS[name]])
        for y in range(INNER_LINE_ROWS[0], INNER_LINE_ROWS[1]):
            prof = np.median(rgb[y, cc] - chassis[y - Y0, cc - X0], axis=0)
            BGexp[y - Y0] += np.where(bzone[y - Y0][:, None], 0.0, prof[None, :])
        for y in line_rows:
            keep[y - Y0, :] = True                      # the line is opaque, drawn over everything
    D = win - BGexp

    # ---- 2. the rule's halo above it (measured per channel on this card's own clean columns where it has
    #         them - the Warrior's stops dead at row 878, where its name panel was pasted over it; the
    #         Breacher's name spans the box, so its halo is the Archer's red shape x its own channel ratios)
    H = np.zeros_like(D)
    fx = halo_xfalloff()[X0:X1]
    if CLEAN_COLS[name]:
        cc = np.concatenate([np.arange(a, b) for a, b in CLEAN_COLS[name]])
        prof = [np.clip(np.median(rgb[top - d, cc] - chassis[top - d - Y0, cc - X0], axis=0), 0.0, None)
                for d in range(HALO_ROWS + 1)]
    else:
        S = halo_shape()
        ratio = halo_ratios(rgb, name, bottom)
        prof = [S[d] * ratio for d in range(HALO_ROWS + 1)]
    for d in range(1, HALO_ROWS + 1):
        yy = top - d - Y0
        if 0 <= yy < h:
            H[yy] = fx[:, None] * prof[d][None, :]

    # ---- 3. the name: its glyph silhouette (fill + bevel + navy outline - opaque, carried exactly) ----
    interior = np.zeros((h, w), bool)
    interior[INTERIOR[0] - Y0:INTERIOR[1] - Y0, INTERIOR[2] - X0:INTERIOR[3] - X0] = True
    name_rows = np.zeros(h, bool)
    name_rows[:top - Y0] = True
    zone_old = name_rows[:, None] & interior
    bright = (Lraw > 100.0) & zone_old & ~keep
    lab, k = ndi.label(bright)
    near_keep = ndi.binary_dilation(keep, iterations=2)
    good = [i + 1 for i in range(k) if ndi.sum(bright, lab, i + 1) >= 20 and not np.any(near_keep[lab == i + 1])]
    fill = np.isin(lab, good)
    navy = (Lraw < 40.0) & ((win[..., 2] - win[..., 0]) > 10.0) & ndi.binary_dilation(fill, iterations=6)
    sil = ndi.binary_fill_holes(fill | navy)
    body = ndi.binary_dilation(sil, iterations=1) & ~keep
    dist = ndi.distance_transform_edt(~sil)

    # the glow model, fitted on the data where it is whole: out from the silhouette, clear of the brackets,
    # the box's ends, the hairlines and the rule's halo (or, on the Warrior, inside its paste)
    scr = ndi.binary_dilation(np.abs(lum(chassis - FLAT)) > 1.5, iterations=2)
    fitm = (dist >= GLOW_FIT_DIST[0]) & (dist <= GLOW_FIT_DIST[1]) & zone_old & ~bzone & ~scr & ~keep
    fitm[:, :160 - X0] = False
    fitm[:, 608 - X0:] = False
    # rows where the data does not hold the whole glow: under an opaque inner line, past a paste's clip
    occ = np.zeros(h, bool)
    occ[:INTERIOR[0] + 2 - Y0] = True                    # the box frame (and its shading): no glow drawn there
    if line_rows:                                        # an opaque inner line: the glow under and above it is
        occ[:max(line_rows) + 1 - Y0] = True             # hidden or clipped by the frame - the model draws it
    cb = CLIP_BOTTOM.get(name)
    if cb:
        occ[cb - Y0:] = True
    else:
        fitm[top - HALO_ROWS - 2 - Y0:] = False
    drow = ndi.distance_transform_edt(~occ)
    fitm &= (drow > FEATHER)[:, None]
    s1, s2, co, rmse = fit_glow(sil, D - H, fitm)
    sig = (s1, s2)
    taper = lambda d: np.clip((GLOW_TAPER[1] - d) / (GLOW_TAPER[1] - GLOW_TAPER[0]), 0.0, 1.0)[..., None]
    G = glow_eval(sil, s1, s2, co) * taper(dist)        # the old name's glow (to take back off a bracket zone)
    G[~zone_old] = 0.0

    # the move: the name's white fill centred where the Necromancer's is
    fwhite = (win[..., 0] > 225) & (win[..., 1] > 225) & (win[..., 2] > 225) & fill
    fr = np.where(fwhite.any(axis=1))[0]
    centre = (fr.min() + fr.max()) / 2.0 + Y0
    dy = int(np.floor(NECRO_FILL_CENTRE - centre + 0.5))
    if dy <= 0:
        raise SystemExit('PK01: %s would move up (dy %d)' % (name, dy))

    # the name layer to put down: the data's own glow (card - background - halo) out to GLOW_R from
    # the silhouette, the model where the data cannot be trusted - in a bracket's glow zone (it carries
    # that zone's hairline) and, on a pasted name, beyond the paste's clip - and nothing past GLOW_TAPER
    m_name = (dist <= GLOW_TAPER[1]) & zone_old
    data = np.where((dist <= GLOW_R)[..., None], np.clip(D - H, 0.0, None), 0.0)   # glow only ever adds light
    bzwide = ndi.binary_dilation(bzone, structure=disc(BZ_MARGIN))
    scr0 = np.abs(lum(chassis - FLAT)) > 1.5
    wt = (np.clip(drow / FEATHER, 0.0, 1.0)[:, None]
          * np.clip(ndi.distance_transform_edt(~bzwide) / FEATHER, 0.0, 1.0)
          * np.clip(ndi.distance_transform_edt(~scr0) / 3.0, 0.0, 1.0))
    ramp = np.ones(h)                                   # the data's last rows above the rule (the halo's edge)
    for kk in range(1, 6):
        yy = top - kk - Y0
        if 0 <= yy < h:
            ramp[yy] = (kk - 1) / 5.0
    data *= (m_name * ramp[:, None])[..., None]

    # ---- 4. compose ---------------------------------------------------------------------------------
    core = (Lw > CORE_LUM) & interior & ~keep
    m_old = ndi.binary_dilation(core, structure=disc(GLOW_R)) | m_name
    rcols = np.where(lum(rgb[top, :] - FLAT) > CORE_LUM)[0]
    rcols = rcols[(rcols > 140) & (rcols < 630)]
    ra, rb = int(rcols.min()), int(rcols.max())
    rulez = np.zeros((h, w), bool)
    rulez[max(0, top - RULE_REACH - Y0):bottom + RULE_REACH + 1 - Y0,
          max(0, ra - RULE_REACH - X0):rb + RULE_REACH + 1 - X0] = True
    below = ~name_rows[:, None] & ndi.binary_dilation(core & ~name_rows[:, None], structure=disc(GLOW_R))
    other = (rulez | below) & interior                  # the rule, the sidearm and their glows: model only
    m_old = (m_old | other) & interior

    def down(a):
        out = np.zeros_like(a)
        out[dy:] = a[:h - dy]
        return out

    # the new glow: the data carried down where it is whole, and the model drawn round the MOVED silhouette
    # everywhere else - so the glow is whole wherever the source's was hidden (under the frame and the inner
    # line, past a paste's clip, in a bracket zone, on a hairline)
    sil_new = down(sil)
    dist_new = ndi.distance_transform_edt(~sil_new)
    G_new = glow_eval(sil_new, s1, s2, co) * taper(dist_new)
    w_new = down(wt * (m_name * ramp[:, None]))
    Ts = w_new[..., None] * down(data) + (1.0 - w_new[..., None]) * G_new
    Ms = (dist_new <= GLOW_TAPER[1]) & interior
    Bs, Ws = down(body), down(win)
    Ts[Bs] = 0.0
    touched = (m_old | Ms) & ~keep
    BG = BGexp.copy()
    # where only the name's glow lay over a bracket's glow (and its hairline), take just that glow back off
    soft = bzwide & ~other & ~body
    take = np.clip(np.minimum(G, np.clip(win - BGexp, 0.0, None)), 0.0, None)
    sw = (np.clip((SOFT_G[1] - lum(G)) / (SOFT_G[1] - SOFT_G[0]), 0.0, 1.0)
          * np.clip(ndi.distance_transform_edt(bzwide) / 3.0, 0.0, 1.0))
    rec = BGexp + sw[..., None] * ((win - take) - BGexp)
    BG[soft] = rec[soft]
    out = win.copy()
    out[touched] = BG[touched]
    put = Ms & ~keep
    out[put] += Ts[put]
    put = Bs & ~keep
    out[put] = Ws[put]
    out = np.clip(np.round(out), 0, 255)

    res = rgb.copy()
    res[Y0:Y1, X0:X1] = out
    img = Image.fromarray(np.dstack([res, alpha]).astype(np.uint8), 'RGBA')
    info = dict(dy=dy, rule=(top, bottom), fill=(int(fr.min() + Y0), int(fr.max() + Y0)),
                bracket_rgb=tuple(round(float(v), 3) for v in kc), glow_rmse=round(rmse, 2), glow_sigmas=sig,
                touched=int(touched.sum()))
    return img, info


# ========================================================================================== THE STRIPS

GW, GH = 420, 90
DISC_C = (45.5, 44.5)                     # the emblem disc's centre (its grey ring at rows 15-16 / 73-74, x 16-17 / 74-75)
DISC_R = 27.5                             # inside the grey ring: only the flat pale fill and the chevrons
MARGIN_X = (82, 97)                       # the interior's left margin, between the disc and the type: the
                                          # scan-line colour of each row (the right margin x 385 agrees)
TEXT_X = (95.0, 389.0)                    # the docs/73 text zone: clear of the disc, ~12 px off the right keyline
TEXT_CY = 44.5                            # the interior's centre row
COND = 0.91                               # the map's own horizontal fit for this face (the TTF menus' fit)
AT_SCALE = 0.75                           # docs/73: AT at three quarters of the cap
WHITE = None                              # the cell's own white
GREY = (200, 208, 220)                    # #C8D0DC
AMBER = (255, 200, 77)                    # #FFC84D - the chevron's amber
OUTER = (4, 6, 15)                        # the near-black outer stroke and shadow
OUTER_W = 1.4                             # px of extra dark stroke round each glyph (docs/73: ~3 px of outline in all)
SHADOW = (1.5, 2.0, 1.6, 0.55)            # dx, dy, blur sigma, alpha
GATE_TOKENS = {   # tier -> the five token texts; the floor is TIER_LAPS - need (50 - 10 = 40, 50 - 30 = 20)
    2: ('TIER', '2', 'AT', 'FLOOR', '40'),
    3: ('TIER', '3', 'AT', 'FLOOR', '20'),
}
TOKEN_STYLE = [(1.0, WHITE), (1.0, WHITE), (AT_SCALE, GREY), (1.0, WHITE), (1.0, AMBER)]
GATE_FLOOR_NEED = {2: 10, 3: 30}          # LOCKSTEP tod_upgrade.lua TIER_FLOOR_TO_TIER / _tod_upgrades.gsc TOD_TIER2/3_FLOOR
GATE_LAPS = 50                            # LOCKSTEP tod_upgrade.lua TIER_LAPS / _tod_gauge.gsc TOD_GAUGE_LAPS


def strip_chassis():
    """The shipped gate_2 strip with its old type removed (each interior row back to its own colour - the
    docs/73 generator's method, with the colour read in the margin) and its chevrons turned down. Returns
    (rgba int array, interior mask)."""
    base = np.asarray(load_source('i_tod_tier_gate_2'), dtype=np.int32)
    other = np.asarray(load_source('i_tod_tier_gate_3'), dtype=np.int32)
    diff = np.abs(base - other).max(axis=2)
    ys, xs = np.where(diff > 0)
    if xs.min() < 100:
        raise SystemExit('PK01: the shipped gate strips differ outside their text (x %d) - one chassis cannot serve both' % xs.min())
    steel = (base[..., 0] > 60) & (base[..., 2] - base[..., 0] >= 20) & (base[..., 3] > 200)
    steel[22:69, 96:396] = False                     # the old type lives here; the stroke never does
    ring = ndi.binary_closing(steel, iterations=2)
    inside = ndi.binary_fill_holes(ring) & ~ring
    interior = ndi.binary_erosion(inside, iterations=4)
    interior[:, :78] = False                         # never the disc side
    chassis = base.copy()
    zone = interior.copy()
    zone[:, :92] = False
    for y in range(GH):
        xs = np.where(interior[y])[0]
        xs = xs[(xs >= MARGIN_X[0]) & (xs <= MARGIN_X[1])]   # the row's colour, read where no type ever was (the
        if len(xs) == 0:                                    # big white letters would win a mode over the row)
            continue
        vals, counts = np.unique(base[y, xs], axis=0, return_counts=True)
        mode = vals[counts.argmax()]
        zx = np.where(zone[y])[0]
        off = zx[np.abs(base[y, zx] - mode).max(axis=1) > 3]
        chassis[y, off] = mode
    # the chevrons, mirrored about the disc's centre row
    yy, xx = np.mgrid[0:GH, 0:GW]
    inr = (xx - DISC_C[0]) ** 2 + (yy - DISC_C[1]) ** 2 <= DISC_R ** 2
    my = (2 * DISC_C[1] - yy).astype(int)
    flipped = chassis.copy()
    flipped[inr] = chassis[my[inr], xx[inr]]
    return flipped, interior


def _token_width(text, cap):
    M = artgen.metrics()
    w, first = 0.0, True
    for c in text:
        sname, key, _ = artgen._glyph(c)
        S = M[sname]
        if not first:
            w += cap * artgen.TOD_TRACK
        w += S['g'][key][0] * (cap / S['cap'])
        first = False
    return w


def gate_layout(cap):
    """Token slots shared by both strips: each slot as wide as its widest variant; the gap between
    tokens is TodGlyphRow's (a space + one tracking step at the main cap). Returns (slots, total) with
    slots = [(x_start, slot_width)], in unscaled px (multiply by COND for the screen)."""
    M = artgen.metrics()
    gap = M['letters']['cw'] * (cap / M['letters']['cap']) * artgen.TOD_SPACE_ADV + cap * artgen.TOD_TRACK
    widths = []
    for i, (scale, _) in enumerate(TOKEN_STYLE):
        widths.append(max(_token_width(GATE_TOKENS[t][i], cap * scale) for t in GATE_TOKENS))
    total = sum(widths) + gap * (len(widths) - 1)
    slots, x = [], 0.0
    for wd in widths:
        slots.append((x, wd))
        x += wd + gap
    return slots, total


def gate_cap():
    cap = 44.0
    while cap > 10 and gate_layout(cap)[1] * COND > TEXT_X[1] - TEXT_X[0]:
        cap -= 0.25
    return cap


def recolour(cell, target):
    """Replace a glyph cell's white fill with `target`, keeping its blue-grey bevel and navy outline."""
    if target is None:
        return cell
    a = np.asarray(cell, dtype=np.float64)
    rgb, al = a[..., :3], a[..., 3]
    L = lum(rgb)
    t = np.clip((L - 170.0) / (226.0 - 170.0), 0.0, 1.0)[..., None]
    shade = np.clip(L / 237.0, 0.0, 1.1)[..., None]
    new = rgb * (1.0 - t) + np.asarray(target, dtype=np.float64)[None, None, :] * shade * t
    return Image.fromarray(np.dstack([np.clip(np.round(new), 0, 255), al]).astype(np.uint8), 'RGBA')


def gate_text(tier, cap):
    """The strip's line as an RGBA layer (GW x GH): glyph cells (condensed by COND), the outer dark
    stroke and the drop shadow. Drawn at 4x and box-filtered down."""
    ss = 4
    M = artgen.metrics()
    slots, total = gate_layout(cap)
    x_line = (TEXT_X[0] + TEXT_X[1]) / 2.0 - total * COND / 2.0
    baseline = TEXT_CY + cap / 2.0
    glyphs = Image.new('RGBA', (GW * ss, GH * ss), (0, 0, 0, 0))
    for i, (scale, colour) in enumerate(TOKEN_STYLE):
        text = GATE_TOKENS[tier][i]
        c = cap * scale
        sx0, swd = slots[i]
        twd = _token_width(text, c)
        pen = x_line + (sx0 + (swd - twd) / 2.0) * COND    # a narrower variant sits centred in its slot
        first = True
        for ch in text:
            sname, key, imgname = artgen._glyph(ch)
            S = M[sname]
            s = c / S['cap']
            adv, gx = S['g'][key]
            if not first:
                pen += c * artgen.TOD_TRACK * COND
            left = pen - gx * s * COND
            topy = baseline - S['baseline'] * s
            cw, chh = int(round(S['cw'] * s * COND * ss)), int(round(S['ch'] * s * ss))
            cell = recolour(artgen._cell(imgname).resize((cw, chh), Image.LANCZOS), colour)
            glyphs.alpha_composite(cell, (int(round(left * ss)), int(round(topy * ss))))
            pen += adv * s * COND
            first = False
    ga = np.asarray(glyphs, dtype=np.float64)[..., 3] / 255.0
    # the outer stroke: the glyphs' coverage grown by OUTER_W
    r = int(round(OUTER_W * ss))
    grown = ndi.grey_dilation(ga, footprint=disc(r))
    # the shadow: the grown shape, offset and softened
    sh = Image.fromarray(np.clip(grown * 255.0, 0, 255).astype(np.uint8), 'L')
    sh = sh.filter(ImageFilter.GaussianBlur(SHADOW[2] * ss))
    sha = np.asarray(sh, dtype=np.float64) / 255.0 * SHADOW[3]
    sha = ndi.shift(sha, (SHADOW[1] * ss, SHADOW[0] * ss), order=1, mode='constant')
    layer = np.zeros((GH * ss, GW * ss, 4))

    def over(rgb, a):
        nonlocal layer
        a = np.clip(a, 0.0, 1.0)
        la = layer[..., 3]
        out_a = a + la * (1.0 - a)
        with np.errstate(invalid='ignore', divide='ignore'):
            col = (np.asarray(rgb, dtype=np.float64) * a[..., None] + layer[..., :3] * (la * (1.0 - a))[..., None]) / np.maximum(out_a, 1e-9)[..., None]
        layer = np.dstack([np.where(out_a[..., None] > 0, col, 0.0), out_a])

    over(np.broadcast_to(np.asarray(OUTER, dtype=np.float64), (GH * ss, GW * ss, 3)), sha)
    over(np.broadcast_to(np.asarray(OUTER, dtype=np.float64), (GH * ss, GW * ss, 3)), grown)
    g = np.asarray(glyphs, dtype=np.float64)
    over(g[..., :3], g[..., 3] / 255.0)
    # box-filter down (premultiplied)
    pre = np.dstack([layer[..., :3] * layer[..., 3:4], layer[..., 3:4]])
    pre = pre.reshape(GH, ss, GW, ss, 4).mean(axis=(1, 3))
    return pre                                          # premultiplied float RGBA (0..255 rgb, 0..1 a)


def build_gate(tier, chassis, interior, cap):
    pre = gate_text(tier, cap)
    clip = ndi.binary_erosion(interior, iterations=1).astype(np.float64)
    pre = pre * clip[..., None]
    a = pre[..., 3]
    base = chassis.astype(np.float64)
    rgb = pre[..., :3] + base[..., :3] * (1.0 - a)[..., None]
    out = base.copy()
    out[..., :3] = rgb
    out = np.clip(np.round(out), 0, 255).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')

# ============================================================================================ build


def build_all():
    chassis = load_chassis()
    imgs, info = {}, {}
    for n in CARD_NAMES:
        imgs[n], info[n] = rebake_card(n, chassis)
    sch, interior = strip_chassis()
    cap = gate_cap()
    for t in (2, 3):
        n = 'i_tod_tier_gate_%d' % t
        import w3f_library   # W3F: the synthwave strip (one owner per file: this pack writes and checks it)
        imgs[n] = w3f_library.tier_gate(t)
        info[n] = dict(cap=cap, text=' '.join(GATE_TOKENS[t]))
    return imgs, info


def save(im, path, name):
    return artgen.save_png(im, path, allow_any_size=name in GATE_NAMES)   # the strips are uncompressed (checked)


def png(im):
    return artgen.png_bytes(im)

# =========================================================================================== review


def _dark(size, col=(14, 16, 24, 255)):
    return Image.new('RGBA', size, col)


def onscreen_draft(cards, scale=1.5):
    """The class draft row as tod_class_select.lua lays it out with four classes: CARD_W 210 canvas
    units, 1.5 card heights, at 1080p (x1.5). Order: Necromancer, Archer, Breacher, Warrior (class ids 1-4)."""
    cw, chh, pitch = 210, 315, 222
    W = int(round((pitch * 3 + cw + 40) * scale))
    H = int(round((chh + 40) * scale))
    bg = _dark((W, H))
    for i, im in enumerate(cards):
        r = im.resize((int(round(cw * scale)), int(round(chh * scale))), Image.LANCZOS)
        bg.alpha_composite(r, (int(round((20 + i * pitch) * scale)), int(round(20 * scale))))
    return bg


PANEL_CARD_A = (4, 2, 2)                  # an ordinary left card for the panel renders: LUCK, RARE, level 2 held
GUTTER_BOX = (25, 125, 405, 425)          # canvas rects cropped from the panel renders: the left gutter (the CLASS
STAMP_BOX = (600, 216, 980, 606)          # badge + the strip under it) and card B with the stamp across it


def panel_frames(lua_path, imgs, cls, need, card_b, shots, scale):
    """THE REAL UPGRADE PANEL, not a composite: `lua_path` (a tod_upgrade.lua) with the installed TodPull +
    GENERATED TodCardArt manifest under tools/ui_mockup's TIMED LUI mock (render_pull.py's machinery: the
    server's own reveal schedule pushed into the models, tweens interpolated, their handlers fired on time),
    drawn with the installed art - the images in `imgs` win, so this pass's strips are what is drawn.
    CoD.TodClass = cls (a live class draws THE PULL's layered v2 cards), CoD.TodTierNeed = need, card B =
    (domain, rarity, level field). Returns one frame per entry of `shots` (seconds after focus opens), at
    `scale` x the 1280x720 canvas. An approximation (linear tweens, no blend modes) - it answers layout,
    layering and colour, which is what these renders are for."""
    import lupa.lua51 as lua51
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'ui_mockup'))
    import render_pull as rp
    rp.SCALE = scale
    rp._cache.clear()
    rp._sized.clear()
    rp._cache.update(imgs)
    L = lua51.LuaRuntime(unpack_returned_tuples=True)
    here = os.getcwd()
    os.chdir(ROOT)
    try:
        L.execute(open(os.path.join(ROOT, 'tools', 'ui_mockup', 'mock_lui_anim.lua'), encoding='utf-8').read())
        L.execute('CoD.TodClass = %d' % cls)
        wd = os.path.join(ROOT, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets')
        for f in ('TodUIOwnership', 'TodHudVeil', 'TodCardArt', 'TodGlyphMetrics', 'TodGlyphRow', 'TodPull'):
            L.execute(open(os.path.join(wd, f + '.lua'), encoding='utf-8').read())
        L.execute(open(lua_path, encoding='utf-8', errors='replace').read())
        menu = L.eval('LUI.createMenu.tod_upgrade( 0 )')
    finally:
        os.chdir(here)
    L.execute('CoD.TodTierNeed = %d' % need)
    g = L.globals()
    ev, focus_t = rp.schedule(PANEL_CARD_A, card_b)
    for et, f, v in ev:
        g.ADVANCE(max(0, et * 1000 - g.NOW))
        g.PUSH(f, v)
    size = (int(round(1280 * scale)), int(round(720 * scale)))   # render_pull.backdrop() wants an int SCALE
    if os.path.exists(rp.BACKDROP):
        bg = Image.open(rp.BACKDROP).convert('RGBA').resize(size, Image.LANCZOS)
    else:
        bg = Image.new('RGBA', size, (14, 12, 26, 255))
    frames = []
    for dt in shots:
        g.ADVANCE(max(0, (focus_t + dt) * 1000 - g.NOW))
        frames.append(rp.draw([dict(x) for x in g.DUMP(menu).values()], bg))
    return frames


def crop(frame, box, scale):
    return frame.crop(tuple(int(round(v * scale)) for v in box))


def panel_renders(lua_path, imgs, out_dir):
    """The strip in the real panel: (rows for the review sheet, or None with a reason). Needs a tod_upgrade.lua
    with the strips switched on - before the landing, pass the merged file with --lua."""
    try:
        src = open(lua_path, encoding='utf-8', errors='replace').read()
    except OSError:
        return None, 'no %s' % lua_path
    if not re.search(r'^local USE_TIER_GATE_ART = true\b', src, re.M):
        return None, '%s draws no strip (USE_TIER_GATE_ART is not true) - pass --lua <the landed / merged file>' % lua_path
    try:
        import lupa.lua51  # noqa: F401
    except ImportError:
        return None, 'lupa is not installed'
    # the gutter: an Archer floor-blocked for tier 2 on an ordinary deal (1080p), a Breacher for tier 3 (720p)
    gut1, = panel_frames(lua_path, imgs, 2, 10, (3, 1, 2), [1.2], 1.5)
    gut2, = panel_frames(lua_path, imgs, 3, 30, (3, 1, 2), [1.2], 1.0)
    # the stamp: an Archer whose right card is the locked TIER 3 card (the tier code (2-1)*2 + (3-2) = 3; a locked
    # card reveals as a COMMON), the moment focus opens (THE PULL's NEW TIER banner would still hold there) and settled
    land, st = panel_frames(lua_path, imgs, 2, 30, (24, 1, 3), [0.04, 1.2], 1.5)
    gut1.save(os.path.join(out_dir, '_onscreen_panel_gutter_1080p.png'))
    st.save(os.path.join(out_dir, '_onscreen_panel_stamp_1080p.png'))
    g1, g2 = crop(gut1, GUTTER_BOX, 1.5), crop(gut2, GUTTER_BOX, 1.0)
    s0, s1 = crop(land, STAMP_BOX, 1.5), crop(st, STAMP_BOX, 1.5)
    g1.save(os.path.join(out_dir, '_onscreen_gutter_1080p.png'))
    s1.save(os.path.join(out_dir, '_onscreen_stamp_1080p.png'))
    s0.save(os.path.join(out_dir, '_onscreen_stamp_landing_1080p.png'))
    rows = [('THE REAL PANEL (live-class layered cards): gutter 1080p Archer | gutter 720p Breacher | '
             'locked TIER 3 card + stamp as it lands | settled', [g1, g2, s0, s1], 420)]
    return rows, None


def review(imgs, out_dir, lua_path):
    src = {n: load_source(n) for n in NAMES}
    rows = []    # the class draft cards' review is r6_class_cards.py's (art/generated/R6-class-cards/_review.png)
    rows.append(('TIER GATE STRIPS 420x90 (= their size at 1080p) - shipped tier 2 | new tier 2 | shipped tier 3 | new tier 3',
                 [src['i_tod_tier_gate_2'], imgs['i_tod_tier_gate_2'], src['i_tod_tier_gate_3'], imgs['i_tod_tier_gate_3']], 90))
    small = [im.resize((280, 60), Image.LANCZOS) for im in (src['i_tod_tier_gate_2'], imgs['i_tod_tier_gate_2'],
                                                             src['i_tod_tier_gate_3'], imgs['i_tod_tier_gate_3'])]
    rows.append(('... at 280x60 (their size at 720p), 1:1', small, 60))
    prow, why = panel_renders(lua_path, imgs, out_dir)
    if prow:
        rows += prow
    else:
        print('PK01: panel renders skipped - %s' % why)
    sheets = []
    for label, items, hgt in rows:
        p = os.path.join(out_dir, '_row.png')
        artgen.contact_sheet([(label, items)], p, height=hgt, label_h=26 if label else 4)
        sheets.append(Image.open(p).convert('RGBA'))
        os.remove(p)
    Wd = max(s.width for s in sheets)
    out = Image.new('RGBA', (Wd, sum(s.height for s in sheets)), (28, 30, 38, 255))
    y = 0
    for s in sheets:
        out.alpha_composite(s, (0, y))
        y += s.height
    p = os.path.join(out_dir, '_review.png')
    out.save(p)
    return p

# =========================================================================================== wiring


def _read(root, rel):
    try:
        return open(os.path.join(root, rel), encoding='utf-8', errors='replace').read()
    except OSError:
        return ''


def check_wiring(root):
    bad = []
    gdt = _read(root, GDT_REL)
    for n in NAMES:
        m = re.search(r'"%s" \( "image\.gdf" \)\s*\{(.*?)\n\t\}' % re.escape(n), gdt, re.S)
        if not m:
            bad.append('GDT: no "%s" image block in %s' % (n, GDT_REL))
            continue
        blk = m.group(1)
        if '"baseImage" "source_data/tod_ui_images/_images/%s.png"' % n not in blk:
            bad.append('GDT: %s does not point at its PNG' % n)
        if n in GATE_NAMES and '"compressionMethod" "uncompressed"' not in blk:
            bad.append('GDT: %s must stay "uncompressed" - it is 420x90 and 90 is not a multiple of 4' % n)
    zone = _read(root, ZONE_REL).splitlines()
    for n in NAMES:
        if 'image,' + n not in zone:
            bad.append('zone: no "image,%s" line in %s' % (n, ZONE_REL))
    cls = _read(root, CLS_LUA_REL)
    for n in CARD_NAMES:
        if 'RegisterImage( "%s" )' % n not in cls:
            bad.append('%s no longer registers %s - the draft would not draw it' % (CLS_LUA_REL, n))
    upg = _read(root, UPG_LUA_REL)
    if not re.search(r'^local USE_TIER_GATE_ART = true\b', upg, re.M):
        bad.append('%s: USE_TIER_GATE_ART is not `true` - the re-baked strips would never draw' % UPG_LUA_REL)
    for t in (2, 3):
        if 'RegisterImage( "i_tod_tier_gate_%d" )' % t not in upg:
            bad.append('%s no longer registers i_tod_tier_gate_%d' % (UPG_LUA_REL, t))
    m = re.search(r'local TIER_FLOOR_TO_TIER = \{ \[(\d+)\] = 2, \[(\d+)\] = 3 \}', upg)
    if not m or (int(m.group(1)), int(m.group(2))) != (GATE_FLOOR_NEED[2], GATE_FLOOR_NEED[3]):
        bad.append('%s: TIER_FLOOR_TO_TIER is not { [%d] = 2, [%d] = 3 }' % (UPG_LUA_REL, GATE_FLOOR_NEED[2], GATE_FLOOR_NEED[3]))
    if not re.search(r'local TIER_DESCENT = true', upg) or not re.search(r'local TIER_LAPS = %d\b' % GATE_LAPS, upg):
        bad.append('%s: TIER_DESCENT / TIER_LAPS no longer say the descent of %d floors the strips bake' % (UPG_LUA_REL, GATE_LAPS))
    gsc = _read(root, UPG_GSC_REL)
    for t, need in GATE_FLOOR_NEED.items():
        if not re.search(r'#define\s+TOD_TIER%d_FLOOR\s+%d\b' % (t, need), gsc):
            bad.append('%s: TOD_TIER%d_FLOOR is not %d - the strip bakes FLOOR %d' % (UPG_GSC_REL, t, need, GATE_LAPS - need))
    gauge = _read(root, GAUGE_GSC_REL)
    if not re.search(r'#define\s+TOD_GAUGE_LAPS\s+%d\b' % GATE_LAPS, gauge) or not re.search(r'#define\s+TOD_GAUGE_DESCENT\s+1\b', gauge):
        bad.append('%s: TOD_GAUGE_LAPS %d / TOD_GAUGE_DESCENT 1 changed - the baked floors are 50 - need' % (GAUGE_GSC_REL, GATE_LAPS))
    for t in (2, 3):
        if GATE_TOKENS[t][4] != str(GATE_LAPS - GATE_FLOOR_NEED[t]):
            bad.append('GATE_TOKENS[%d] bakes %s, the descent shows %d' % (t, GATE_TOKENS[t][4], GATE_LAPS - GATE_FLOOR_NEED[t]))
    return bad

# ============================================================================================= main


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--install', action='store_true', help='copy into source_data/tod_ui_images/_images/')
    ap.add_argument('--stage', help='also write the PNGs under DIR/source_data/tod_ui_images/_images/')
    ap.add_argument('--check', action='store_true', help='fail on any byte that differs from the installed PNGs, or a wiring break')
    ap.add_argument('--root', help='with --check: read DIR/... instead of the repo')
    ap.add_argument('--derive-chassis', action='store_true', help='rebuild the pinned name-box chassis from the 18 donors')
    ap.add_argument('--lua', help='review only: the tod_upgrade.lua the panel renders run (default: the repo file; '
                                  'before the landing, the merged file - the repo one draws no strip yet)')
    a = ap.parse_args()

    if a.derive_chassis:
        im, holes = derive_chassis()
        p = os.path.join(SRC_DIR, CHASSIS_NAME + '.png')
        artgen.save_png(im, p, allow_any_size=True)
        sha = sha256_file(p)
        with open(CHASSIS_PIN, 'w', encoding='ascii', newline='\n') as f:
            f.write('%s  %s.png\n' % (sha, CHASSIS_NAME))
        print('chassis -> %s (%dx%d, %d px with no donor -> FLAT + hairlines), sha256 %s' % (p, im.width, im.height, holes, sha))
        return

    imgs, info = build_all()
    if a.check:
        root = a.root or ROOT
        bad = []
        for n in NAMES:
            p = os.path.join(root, IMG_REL, n + '.png')
            if not os.path.isfile(p):
                bad.append('MISSING %s' % p)
            elif open(p, 'rb').read() != png(imgs[n]):
                bad.append('STALE %s (re-run tools/artgen/packs/pk01_card_text_rebake.py --install; never hand-edit it)' % p)
        bad += check_wiring(root)
        if bad:
            for b in bad:
                print('PK01 CARD TEXT REBAKE: ' + b)
            sys.exit(1)
        print('PK01 CARD TEXT REBAKE OK (%d images byte-exact; GDT + zone + draft registration + USE_TIER_GATE_ART + descent floors 40 / 20)' % len(NAMES))
        return

    out_dir = artgen.stage_dir(PACK)
    for n in NAMES:
        md5 = save(imgs[n], os.path.join(out_dir, n + '.png'), n)
        print('%-26s %s  %s' % (n, md5, info.get(n, '')))
    for root in ([a.stage] if a.stage else []) + ([ROOT] if a.install else []):
        for n in NAMES:
            save(imgs[n], os.path.join(root, IMG_REL, n + '.png'), n)
    print('review ->', review(imgs, out_dir, os.path.abspath(a.lua) if a.lua else os.path.join(ROOT, UPG_LUA_REL)))


if __name__ == '__main__':
    main()
