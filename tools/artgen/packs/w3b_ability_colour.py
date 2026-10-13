"""w3b_ability_colour.py - THE ABILITY TILE GLYPHS IN COLOUR (W3B, 2026-10-05).

User 2026-10-05: "For the ability icons we can add some color to give it more personality. To the ones that
make sense to add color" + "Whole entire asset library should look like one library".

WHAT IT MAKES. The twelve HUD V2 tile glyphs AetheriumLoadout.lua draws (128 x 128, same names, same size):

  ARCHER       i_tod_h2_ab_hook        GRAPPLE         the HOOK (its flukes) takes the Archer's gold; shank + line steel
               i_tod_h2_ab_axe         HELL'S RETRIEVER the axe HEAD burns fire orange (the card's burning axe)
  WARRIOR      i_tod_h2_ab_bash        BASH            the leading BLADE + its two speed streaks: the Warrior's violet
               i_tod_h2_ab_smash       CYBER SMASH     the SHOCKWAVE ring takes the Warrior's violet (the card's portal)
  BREACHER     i_tod_h2_ab_cluster     CLUSTER         the four BOMBLETS burn fire orange (the card's lit bomblets)
               i_tod_h2_ab_c4          STICKY C4       the ARMED LIGHT in the Breacher's red (the card's red light / button)
  NECROMANCER  i_tod_h2_ab_cloak       INVISIBILITY    the DISSOLVING STREAKS are the spectral grey-blue of the vanishing
               i_tod_h2_ab_soul_bomb   SOUL PULSE      the SKULL is the Necromancer's green (his medallion's skull)
  stock        i_tod_h2_ab_frag        frag            the PIN + LEVER fire orange (shown only to a kit-less player)
               i_tod_h2_ab_monkey      cymbal monkey   the CYMBALS brass gold
               i_tod_h2_ab_spider      Widow's Wine    WHITE SILK: the perk row's Widow's shield is white silk (R4), so the
                                                       web grenade stays white-hot with the silk's lilac halo
               i_tod_h2_ab_spider_phd  Widow's + PhD   the BLAST takes PhD Flopper's violet, as the perk row does - buying
                                                       PhD reads as a change of colour, not of shape

THE LANGUAGE IS R4's, IMPORTED, NEVER COPIED: every glyph goes through r4_synthwave_hud.neon_glyph - the
white-hot ink, ONE accent part in a hue that says what it is, and a soft halo of that hue (tmp/redesign/
R3-synthwave-system/STYLE.md; the perk shields, power-up tokens and prompt icons are drawn the same way). The
hues come from the class identities - Archer gold, Breacher red, Warrior violet, Necromancer green, the LIVE
tod_class_select.lua CLASSES[].accent that W3C's class medallions / plates are baked from too (--check fails if
it moves) - and the HUD palette (synthwave.PAL sunset = fire); Widow's / PhD are R4's own PERK_HUE.

THE SHAPES DO NOT MOVE. Each glyph's WHITE CORE is recovered from its pinned white master: the shipped art
is core + gain * gauss(core, sigma) * (1 - core) (alpha only, RGB 255), so a fixed-point deconvolution gives
the core back (reconstruction error over the inked pixels: max 0.023, mean <= 0.006 of full alpha - --measure
prints it; the new solid core matches the master's at IoU >= 0.97, which --check asserts). The masters are the
white files as shipped on 2026-10-05, kept in art/synthwave_hud/ability_icons_white_src/ and pinned by md5
below (a generator must not read its own output - R4's red prompt-icon sources set the precedent). The
Necromancer's two (cloak, soul pulse) are PK05's own vector drawings, imported: PK05 still draws their
white pause-menu twins (i_tod_pm_ico_cloak / _soulbomb), so the tile and its row icon stay one drawing.

WHY THE PAUSE-MENU / SCOREBOARD ROW ICONS STAY WHITE (i_tod_pm_ico_grapple / retriever / bash / gravsmash /
cluster / c4 / cloak / soulbomb, the same drawings): AetheriumStartMenu.lua / AetheriumScoreboard.lua TINT
the row glyph by STATE - magenta = a held card, violet = a dark card, grey-blue = the idle companion row -
and that tint is a MULTIPLY (a coloured glyph x magenta goes muddy: green x (1, .17, .82) is navy). The rows
are a list of 40+ cards that all speak that one state code; the HUD tile is a BUTTON, and its glyph is the
only place an ability's own colour belongs. The shapes stay identical, so the tile still points at its row.

THE HUD NEVER TINTS THESE GLYPHS (read before colouring, AetheriumLoadout.lua makeOffhandSlot): the icon is
setRGB( 1, 1, 1 ) once and only its ALPHA moves - 1 ready, 0.35 / 0.40 charging or empty, 0.2 locked;
TodAbilityFeedback.lua draws its flash / cast / refused / recharge pieces as separate slab overlays and never
touches the icon. So the coloured art reads exactly as authored in every state, and no Lua changes. --check
asserts that contract (a future non-white icon tint would multiply the colour away).

  python -B tools/artgen/packs/w3b_ability_colour.py              # -> art/generated/W3B-ability-colour/ + _review*.png
  python -B tools/artgen/packs/w3b_ability_colour.py --stage      # + tmp/wave3/W3B-ability-colour/stage/ (+ base/)
  python -B tools/artgen/packs/w3b_ability_colour.py --install    # LANDING ONLY: copy into source_data/tod_ui_images/_images
  python -B tools/artgen/packs/w3b_ability_colour.py --check      # regenerate in memory; fail on any byte != installed, a
                                                                 # drifted master, a missing GDT block / zone line, PK05 still
                                                                 # claiming a tile, a non-white icon tint in the loadout, or a
                                                                 # class accent that moved in tod_class_select.lua
  python -B tools/artgen/packs/w3b_ability_colour.py --check --against stage
  python -B tools/artgen/packs/w3b_ability_colour.py --selftest   # break the contract six ways; each must be caught
  python -B tools/artgen/packs/w3b_ability_colour.py --measure    # core recovery error + halo profile, old vs new

Deterministic: no randomness, no timestamps. Never hand-edit a generated PNG; change this file and re-run.
"""
import argparse, hashlib, io, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import artgen  # noqa: E402
from synthwave import PAL  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from scipy import ndimage  # noqa: E402
import r4_synthwave_hud as r4  # noqa: E402  (neon_glyph, coverage, PERK_HUE - the R4 language, imported)
import pk05_glyph_icons as pk05  # noqa: E402  (the Necromancer's two vector drawings)

PACK = 'W3B-ability-colour'
ROOT = artgen.ROOT
WAVE = os.path.join(ROOT, 'tmp', 'wave3', PACK)
STAGE_ROOT = os.path.join(WAVE, 'stage')
BASE_ROOT = os.path.join(WAVE, 'base')
IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')
SRC_REL = os.path.join('art', 'synthwave_hud', 'ability_icons_white_src')
PK05_REL = os.path.join('tools', 'artgen', 'packs', 'pk05_glyph_icons.py')
LOADOUT_REL = os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'AetheriumLoadout.lua')
FEEDBACK_REL = os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodAbilityFeedback.lua')
OUT = os.path.join(ROOT, 'art', 'generated', PACK)
S = 128

# ------------------------------------------------------------------------------------------------ masters
# The white masters as shipped on 2026-10-05 (docs/182 HUD V2 drop + the docs/97 spiders), copied byte for
# byte into art/synthwave_hud/ability_icons_white_src/. A master that moved is a NEW drawing: re-pin it on
# purpose, never to make --check green.
SRC_MD5 = {
    'i_tod_h2_ab_hook': 'e58ebcf8090da23e24029ff666f58600',
    'i_tod_h2_ab_axe': '97e84495ccab7771c1b462a698860b83',
    'i_tod_h2_ab_bash': 'd8ee3680a49b0b3e507d840a6fe5f48e',
    'i_tod_h2_ab_smash': 'aea482b6b2924647adf44378ee6b472c',
    'i_tod_h2_ab_cluster': 'ee5341b8d65013941fd4426a4c6809b8',
    'i_tod_h2_ab_c4': 'cd95a65a0f59e1fe18fe069434120663',
    'i_tod_h2_ab_frag': 'ffbd082df8aab7c19aafda29c9d96a84',
    'i_tod_h2_ab_monkey': '7cf8315641eabcb72a7f418cf6862b7c',
    'i_tod_h2_ab_spider': '9b6fb1390e3ccb439b35ecd85d8f5a5b',
    'i_tod_h2_ab_spider_phd': '196bbc28811a63135144cfa0b61073f1',
}
# The shipped white glow these masters carry, FITTED (--measure): alpha = C + GAIN * gauss(C, SIGMA) * (1 - C).
DECON_SIGMA, DECON_GAIN, DECON_ITERS = 4.5, 0.55, 40

# --------------------------------------------------------------------------------------------- the hues
# By MEANING, then by class. The class identities are the LIVE ones: tod_class_select.lua CLASSES[id].accent, the
# tint of each class's role / weapon text in the draft - the same source W3C's class medallions / plates are baked
# from, so a tile and its class's medallion wear one colour. Baked here as constants (deterministic bytes) and
# --check fails if the Lua moves (re-run the generator then).
CLASS_ACCENT = {          # class -> (class id, accent) LOCKSTEP tod_class_select.lua CLASSES
    'NECROMANCER': (1, (0.55, 1.00, 0.45)),
    'ARCHER': (2, (1.00, 0.75, 0.25)),
    'BREACHER': (3, (1.00, 0.35, 0.30)),
    'WARRIOR': (4, (0.75, 0.45, 1.00)),
}
SELECT_LUA_REL = os.path.join('ui', 'uieditor', 'menus', 'hud', 'tod_class_select.lua')


def _hex(rgb):
    return '#%02X%02X%02X' % tuple(int(round(v * 255)) for v in rgb)


ARCHER_GOLD = _hex(CLASS_ACCENT['ARCHER'][1])        # #FFBF40 - GRAPPLE's hook
BREACHER_RED = _hex(CLASS_ACCENT['BREACHER'][1])     # #FF594D - the C4's armed light (the card's red light / button)
WARRIOR_VIOLET = _hex(CLASS_ACCENT['WARRIOR'][1])    # #BF73FF - BASH's blade + streaks, CYBER SMASH's shockwave
NECRO_GREEN = _hex(CLASS_ACCENT['NECROMANCER'][1])   # #8CFF73 - SOUL PULSE's skull (his medallion's skull, the V1 accent)
FIRE = PAL['id_sunset']          # #FF8A3D - fire: the Retriever's burning head, the cluster's lit bomblets, a frag's pin
                                 # (RT: an IDENTITY role - the same orange in every UI theme)
SPECTRAL = '#7FB2FF'             # the cloak's vanishing: a grey-blue soul, cooler than the cyan FOCUS colour
BRASS = PAL['id_gold']           # #F5D742 - the monkey's brass cymbals (identity role, every theme)
WIDOWS_SILK = r4.PERK_HUE['widows']   # #E8E0FF - R4's Widow's Wine shield (white silk)
PHD_VIOLET = r4.PERK_HUE['phd']       # #9A6BFF - R4's PhD Flopper shield

# The compositor (r4.neon_glyph) at 128. Fitted to the shipped white glow by --measure (the mean alpha 2/4/6/8/10 px
# from the core over all twelve): OLD 62.9 / 34.5 / 19.1 / 9.0 / 3.3, NEW 78.3 / 34.5 / 18.2 / 9.2 / 4.2 - the same
# soft reach, with R4's brighter neon rim in the first 2 px (the tight 0.35-sigma term every R4 glyph carries).
SIGMA, K, ACC_LIFT = 5.5, 0.62, 0.16

# Selectors (128-px space): ('comp', x, y) = the core component nearest (x, y), with its anti-aliased fringe;
# ('poly', [...]) / ('ellipse', cx, cy, rx, ry) = a region (anti-aliased) - used only where the accent part is
# joined to the white ink, and every seam is placed across the narrowest joint (zoom sheets in LAND.md).
# GRAPPLE: the hook that bites - the flukes, a separate part (the grapple's LINE was the first choice, but it is
# 3.5 px at 128 = 1 px on the 36 px tile, under R4's own stroke floor for a colour carrier; at 1080p it read as a
# hairline). The shank, ring and line stay steel-white.
HOOK_FLUKES = [('comp', 64, 95)]
# BASH: the dash's energy - the leading blade (the cone right of the body's slot, joined to it only by the slot's
# thin top and bottom rims, cut at x 61 in the middle of the slot) and the two speed streaks.
BASH_ENERGY = [('poly', [(61, 30), (128, 30), (128, 87), (61, 87)]), ('comp', 50, 34), ('comp', 54, 90)]
# RETRIEVER: the head is a flag on the handle's top end, sharing its upper edge; the seam is the cut ACROSS the
# handle (perpendicular to it) through the notch where the head's lower edge meets the handle (79, 63): the
# half-plane x - y > 16, kept right of x 60 so the return arc's arrowhead (x <= 40) stays white.
AXE_HEAD = [('poly', [(60, 0), (128, 0), (128, 112), (60, 44)])]

GLYPHS = [
    # name, source, halo hue, accent ink, accent selectors, class, ability, what is coloured
    ('i_tod_h2_ab_hook', 'png', ARCHER_GOLD, ARCHER_GOLD, HOOK_FLUKES, 'ARCHER', 'GRAPPLE', 'the hook, Archer gold'),
    ('i_tod_h2_ab_axe', 'png', FIRE, FIRE, AXE_HEAD, 'ARCHER', "HELL'S RETRIEVER", 'the burning head, fire orange'),
    ('i_tod_h2_ab_bash', 'png', WARRIOR_VIOLET, WARRIOR_VIOLET, BASH_ENERGY,
     'WARRIOR', 'BASH', 'the blade and its streaks, Warrior violet'),
    ('i_tod_h2_ab_smash', 'png', WARRIOR_VIOLET, WARRIOR_VIOLET, [('comp', 64, 96)], 'WARRIOR', 'CYBER SMASH',
     'the shockwave ring, Warrior violet'),
    ('i_tod_h2_ab_cluster', 'png', FIRE, FIRE, [('comp', 35, 35), ('comp', 91, 35), ('comp', 35, 91), ('comp', 91, 91)],
     'BREACHER', 'CLUSTER', 'the four bomblets, fire orange'),
    ('i_tod_h2_ab_c4', 'png', BREACHER_RED, BREACHER_RED, [('comp', 79.5, 71.5)], 'BREACHER', 'STICKY C4',
     'the armed light, Breacher red'),
    ('i_tod_h2_ab_cloak', 'pk05:cloak', SPECTRAL, SPECTRAL, [('comp', 81, 80), ('comp', 92.5, 78), ('comp', 100.5, 80),
                                                             ('comp', 108.5, 82)],
     'NECROMANCER', 'INVISIBILITY CLOAK', 'the dissolving streaks, spectral grey-blue'),
    ('i_tod_h2_ab_soul_bomb', 'pk05:soul_pulse', NECRO_GREEN, NECRO_GREEN, [('comp', 64, 64)], 'NECROMANCER',
     'SOUL PULSE', 'the skull, Necromancer green'),
    ('i_tod_h2_ab_frag', 'png', FIRE, FIRE, [('comp', 88, 20)], 'STOCK', 'FRAG', 'the pin and lever, fire orange'),
    ('i_tod_h2_ab_monkey', 'png', BRASS, BRASS, [('ellipse', 20.5, 62.5, 17.2, 10.6), ('ellipse', 107.5, 62.5, 17.2, 10.6)],
     'STOCK', 'CYMBAL MONKEY', 'the cymbals, brass gold'),
    ('i_tod_h2_ab_spider', 'png', WIDOWS_SILK, WIDOWS_SILK, [('comp', 63.5, 69.5)], 'STOCK', "WIDOW'S WINE",
     "white silk (the perk row's Widow's shield)"),
    ('i_tod_h2_ab_spider_phd', 'png', PHD_VIOLET, PHD_VIOLET, [('comp', 103, 25)], 'STOCK', "WIDOW'S + PHD",
     "the blast, PhD Flopper's violet"),
]
NAMES = [g[0] for g in GLYPHS]
SPEC = {g[0]: g for g in GLYPHS}
PK05_SOURCES = {'pk05:cloak': pk05.ico_cloak, 'pk05:soul_pulse': pk05.ico_soul_pulse}


class W3BError(SystemExit):
    pass

# ================================================================================================ build

def src_dir():
    """The pinned white masters: the repo copy once landed; before the landing, the staged copy."""
    repo = os.path.join(ROOT, SRC_REL)
    if all(os.path.isfile(os.path.join(repo, n + '.png')) for n in SRC_MD5):
        return repo
    return os.path.join(STAGE_ROOT, SRC_REL)


def read_master(name, d=None):
    p = os.path.join(d or src_dir(), name + '.png')
    if not os.path.isfile(p):
        raise W3BError('w3b: the white master %s is missing (%s)' % (name, SRC_REL))
    data = open(p, 'rb').read()
    md5 = hashlib.md5(data).hexdigest()
    if md5 != SRC_MD5[name]:
        raise W3BError('w3b: %s is not the pinned white master (md5 %s, pinned %s) - a new drawing is re-pinned on '
                       'purpose, never to make --check green' % (p, md5, SRC_MD5[name]))
    return Image.open(io.BytesIO(data)).convert('RGBA')


def recover_core(alpha):
    """alpha (0..1) = C + GAIN * gauss(C, SIGMA) * (1 - C)  ->  C, by fixed-point iteration from the solid core."""
    A = np.asarray(alpha, dtype=np.float64)
    C = (A >= 0.995).astype(np.float64)
    for _ in range(DECON_ITERS):
        G = np.clip(DECON_GAIN * ndimage.gaussian_filter(C, DECON_SIGMA, mode='constant'), 0.0, 1.0)
        C = np.clip((A - G) / np.maximum(1.0 - G, 1e-6), 0.0, 1.0)
    C[C < 0.02] = 0.0
    return C


def white_core(name, d=None):
    """The glyph's white ink coverage (128 x 128, 0..1) and, for a PNG master, the master itself."""
    src = SPEC[name][1]
    if src in PK05_SOURCES:
        return np.clip(pk05._raster(pk05.fit(PK05_SOURCES[src]()))[..., 0], 0.0, 1.0), None
    m = read_master(name, d)
    return recover_core(np.asarray(m, dtype=np.float64)[..., 3] / 255.0), m


def accent_mask(C, sels):
    """0..1 per pixel: how much of the ink there is the accent part (see the selector note above)."""
    R = np.zeros_like(C)
    core = C > 0.5
    lab, _ = ndimage.label(core)
    # every inked pixel goes with the component of its NEAREST core pixel (the anti-aliased fringe follows its shape)
    _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
    owner = lab[iy, ix]
    ys, xs = np.nonzero(core)
    for sel in sels:
        kind = sel[0]
        if kind == 'comp':
            k = int(np.argmin((xs - sel[1]) ** 2 + (ys - sel[2]) ** 2))
            R = np.maximum(R, (owner == lab[ys[k], xs[k]]).astype(np.float64))
        elif kind == 'poly':
            d = 'M' + ' L'.join('%.3f,%.3f' % p for p in sel[1]) + ' Z'
            R = np.maximum(R, r4.coverage(S, S, '<path d="%s" fill="#fff"/>' % d))
        elif kind == 'ellipse':
            R = np.maximum(R, r4.coverage(S, S, '<ellipse cx="%.3f" cy="%.3f" rx="%.3f" ry="%.3f" fill="#fff"/>' % sel[1:]))
        else:
            raise W3BError('w3b: unknown selector %r' % (sel,))
    return np.clip(R, 0.0, 1.0)


def split(name, d=None):
    """(white coverage, accent coverage, core C) such that neon_glyph's ink S = accent + white*(1-accent) == C:
    the glyph's silhouette is exactly the master's, only its colour is divided."""
    C, _ = white_core(name, d)
    R = accent_mask(C, SPEC[name][4])
    acc = C * R
    with np.errstate(invalid='ignore', divide='ignore'):
        white = np.where(acc < 1.0 - 1e-9, C * (1.0 - R) / np.maximum(1.0 - acc, 1e-9), 0.0)
    return np.clip(white, 0.0, 1.0), acc, C


def glyph(name, d=None):
    _, _, hue, acc_ink, _, _, _, _ = SPEC[name]
    white, acc, _ = split(name, d)
    im = r4.neon_glyph(white, acc, hue, acc=acc_ink, sigma=SIGMA, k=K, acc_lift=ACC_LIFT)
    if im.size != (S, S):
        raise W3BError('w3b: %s is %s - a drop-in keeps 128 x 128' % (name, im.size))
    return im


def build_all(d=None):
    """{name: (RGBA image, the exact PNG bytes the landing installs)}."""
    out = {}
    for name in NAMES:
        im = glyph(name, d)
        out[name] = (im, artgen.png_bytes(im))
    return out

# ================================================================================================ check

def _read(root, rel):
    p = os.path.join(root, rel)
    if not os.path.exists(p):
        p = os.path.join(ROOT, rel)
    return open(p, encoding='utf-8', errors='replace').read()


def pk05_claims(src_text):
    """The tile / V1-key names PK05's tables still generate (two generators must never own one file)."""
    return sorted(set(re.findall(r"^\s*\('(i_tod_(?:h2_ab|hud_off)_\w+)'", src_text, re.M)))


def tint_problems(loadout_text, feedback_text):
    """The colour contract: the HUD multiplies nothing over these glyphs."""
    out = []
    for args in re.findall(r'\.icon:setRGB\(\s*([^)]*?)\s*\)', loadout_text):
        if re.sub(r'\s+', '', args) != '1,1,1':
            out.append('AetheriumLoadout.lua tints an ability icon (setRGB( %s )): a tint multiplies the coloured glyph '
                       '- keep the icon white and move any state colour onto the tile' % args)
    if re.search(r'\.icon\b', feedback_text):
        out.append('TodAbilityFeedback.lua touches an ability icon: its pulses must stay separate overlays')
    return out


def shape_problems(name, im, d=None):
    """The shape kept: the new solid core (alpha >= 250) against the master's, as an IoU."""
    src = SPEC[name][1]
    if src in PK05_SOURCES:
        ref = pk05.white_glyph(pk05.fit(PK05_SOURCES[src]()))
    else:
        ref = read_master(name, d)
    a = np.asarray(im)[..., 3] >= 250
    b = np.asarray(ref)[..., 3] >= 250
    iou = (a & b).sum() / float(max(1, (a | b).sum()))
    return [] if iou >= 0.97 else ['%s: the white core moved (IoU %.3f < 0.97 against its master)' % (name, iou)]


def lua_accents(src):
    """{class id: (r, g, b)} from tod_class_select.lua's CLASSES table."""
    out = {}
    for cid, body in re.findall(r'\[(\d)\]\s*=\s*\{\s*name\s*=\s*"[A-Z]+".*?accent\s*=\s*\{([^}]*)\}', src, re.S):
        out[int(cid)] = tuple(float(v) for v in body.split(','))
    return out


def accent_problems(select_text):
    got = lua_accents(select_text)
    out = []
    for cls, (cid, acc) in sorted(CLASS_ACCENT.items()):
        g = got.get(cid)
        if g is None or len(g) != 3 or any(abs(x - y) > 1e-6 for x, y in zip(g, acc)):
            out.append('tod_class_select.lua accent for %s (class %d) is %s, the tiles are baked in %s - update CLASS_ACCENT '
                       'and re-run the generator' % (cls, cid, g, acc))
    return out


# RETIRED WHOLE with this pack (W3B, 2026-10-05; tmp/wave3/W3F-library-audit F07 handed both to the ability-icon
# owner): the V1 kit cloak glyph (never drawn while USE_HUD_V2 - AetheriumLoadout named it only so its H2_AB row could
# remap it to i_tod_h2_ab_cloak; CLASS_KITS[3] now names the tile directly) and the SUMMON tile (the Necromancer's
# tactical became the CLOAK on 2026-09-27; nothing has drawn it since). Their PNGs move to
# archive/retired_20261005_ability_glyphs/; --check keeps them out of the zone, the GDT, _images and every Lua literal.
RETIRED = ['i_tod_hud_off_cloak', 'i_tod_h2_ab_summon']
GDT_REL = os.path.join('source_data', 'tod_ui_images.gdt')
ZONE_REL = os.path.join('zone_source', 'zm_tod2_cybercity.zone')


def gdt_has(gdt, name):
    return re.search(r'"%s"\s*\(\s*"image\.gdf"' % re.escape(name), gdt) is not None


def zone_has(zone, name):
    return re.search(r'^\s*image,%s\s*$' % re.escape(name), zone, re.M) is not None


def ui_literals(root, name):
    """Lua files under <root>/ui (else the repo's) that name `name` as a string literal."""
    hits = []
    for dp, _, files in os.walk(os.path.join(ROOT, 'ui')):
        for f in sorted(files):
            if not f.endswith('.lua'):
                continue
            rel = os.path.relpath(os.path.join(dp, f), ROOT)
            if '"%s"' % name in _read(root, rel):             # a staged copy overrides the repo file
                hits.append(rel.replace(os.sep, '/'))
    return hits


def wiring_problems(root, pending=None):
    """root = the repo (installed) or the stage tree (a staged file overrides its repo copy). Files the landing must
    change BY HAND - the zone (WIRING) and the two retired PNGs (moved to archive/) - are reported into `pending`
    instead of failing when root is the stage tree."""
    out = []
    stage_mode = os.path.normcase(os.path.abspath(root)) != os.path.normcase(os.path.abspath(ROOT))
    gdt = _read(root, GDT_REL)
    zone = _read(ROOT, ZONE_REL)
    for name in NAMES:
        if not gdt_has(gdt, name):
            out.append('%s: no GDT block in source_data/tod_ui_images.gdt' % name)
        if not zone_has(zone, name):
            out.append('%s: no zone image line' % name)
    for name in RETIRED:
        if gdt_has(gdt, name):
            out.append('%s is retired: its GDT block is still in source_data/tod_ui_images.gdt' % name)
        for rel in ui_literals(root, name):
            out.append('%s is retired: %s still names it' % (name, rel))
        late = []
        if zone_has(zone, name):
            late.append('%s is retired: zone line "image,%s" (WIRING: remove it)' % (name, name))
        if os.path.isfile(os.path.join(artgen.IMG, name + '.png')):
            late.append('%s is retired: %s/%s.png is still in _images (move it to archive/retired_20261005_ability_glyphs/)'
                        % (name, IMG_REL.replace(os.sep, '/'), name))
        if stage_mode and pending is not None:
            pending.extend(late)
        else:
            out.extend(late)
    both = sorted(set(pk05_claims(_read(root, PK05_REL))) & (set(NAMES) | set(RETIRED)))
    if both:
        out.append('pk05_glyph_icons.py still generates %s - W3B owns the coloured tiles and retired the V1 key '
                   '(apply the staged PK05 edit)' % ', '.join(both))
    out += tint_problems(_read(root, LOADOUT_REL), _read(root, FEEDBACK_REL))
    out += accent_problems(_read(root, SELECT_LUA_REL))
    return out


def check(img_dir, root, built=None, pending=None):
    built = built or build_all()
    bad = []
    for name, (im, data) in built.items():
        p = os.path.join(img_dir, name + '.png')
        if not os.path.isfile(p):
            bad.append('MISSING %s' % p)
        elif open(p, 'rb').read() != data:
            bad.append('STALE %s (re-run the generator; never hand-edit it)' % p)
        bad += shape_problems(name, im)
    return bad + wiring_problems(root, pending)

# ================================================================================================ stage
# The generator stages what it GENERATES (the 12 glyphs) and seeds the pinned masters. The hand edits that land with
# it - PK05 handing over the two tiles and the V1 key, the GDT losing the two retired blocks, AetheriumLoadout naming
# the cloak tile directly - are staged by hand in the same tree (tmp/wave3/W3B-ability-colour/LAND.md lists them),
# and --check --against stage reads them there.


def seed_masters():
    """Before the landing the masters live only in the stage tree: seed them from the repo's white files while
    those are still the pinned ones (never during --check: a gate writes nothing)."""
    if src_dir() == os.path.join(ROOT, SRC_REL):
        return
    src_s = os.path.join(STAGE_ROOT, SRC_REL)
    os.makedirs(src_s, exist_ok=True)
    for name, md5 in SRC_MD5.items():
        dst = os.path.join(src_s, name + '.png')
        if os.path.isfile(dst) and hashlib.md5(open(dst, 'rb').read()).hexdigest() == md5:
            continue
        for cand in (os.path.join(ROOT, SRC_REL, name + '.png'), os.path.join(artgen.IMG, name + '.png')):
            if os.path.isfile(cand) and hashlib.md5(open(cand, 'rb').read()).hexdigest() == md5:
                shutil.copy2(cand, dst)
                break
        else:
            raise W3BError('w3b: no copy of the pinned white master %s exists to stage' % name)


def stage(built):
    """Write the 12 glyphs into the landing kit (+ a base/ copy of each file they replace, kept from the first
    --stage so base/ is always the repo BEFORE this pack)."""
    img_s, img_b = os.path.join(STAGE_ROOT, IMG_REL), os.path.join(BASE_ROOT, IMG_REL)
    os.makedirs(img_s, exist_ok=True)
    os.makedirs(img_b, exist_ok=True)
    for name, (im, data) in built.items():
        with open(os.path.join(img_s, name + '.png'), 'wb') as fh:
            fh.write(data)
        repo = os.path.join(artgen.IMG, name + '.png')
        base = os.path.join(img_b, name + '.png')
        if os.path.isfile(repo) and not os.path.isfile(base):
            shutil.copy2(repo, base)
    return STAGE_ROOT

# ================================================================================================ selftest

def selftest():
    """Break the contract six ways (each must be caught) and prove the clean state passes."""
    import tempfile
    ok, fails = 0, []

    def expect(cond, msg):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fails.append(msg)

    built = build_all()
    tmp = tempfile.mkdtemp(prefix='w3b_selftest_')
    try:
        # 1. a stale byte in one installed glyph
        for name, (_, data) in built.items():
            with open(os.path.join(tmp, name + '.png'), 'wb') as fh:
                fh.write(data)
        expect(not any(m.startswith(('STALE', 'MISSING')) for m in check(tmp, STAGE_ROOT, built)), 'clean images report stale')
        im = built['i_tod_h2_ab_c4'][0].copy()
        im.putpixel((79, 71), (255, 255, 255, 255))
        with open(os.path.join(tmp, 'i_tod_h2_ab_c4.png'), 'wb') as fh:
            fh.write(artgen.png_bytes(im))
        expect(any(m.startswith('STALE') and 'i_tod_h2_ab_c4' in m for m in check(tmp, STAGE_ROOT, built)),
               'a hand-edited glyph was NOT caught')
        # 2. a master that drifted
        mdir = os.path.join(tmp, 'masters')
        os.makedirs(mdir)
        for n in SRC_MD5:
            shutil.copy2(os.path.join(src_dir(), n + '.png'), mdir)
        m = Image.open(os.path.join(mdir, 'i_tod_h2_ab_hook.png')).convert('RGBA')
        m.putpixel((5, 120), (255, 255, 255, 40))
        m.save(os.path.join(mdir, 'i_tod_h2_ab_hook.png'))
        try:
            glyph('i_tod_h2_ab_hook', mdir)
            expect(False, 'a drifted master was NOT caught')
        except W3BError:
            expect(True, '')
        # 3. PK05 still claiming a tile (the pre-landing PK05 is exactly that file; synthesise it after the landing)
        pk_now = open(os.path.join(ROOT, PK05_REL), encoding='utf-8').read()
        if not pk05_claims(pk_now):
            pk_now = pk_now.replace("ICONS = [\n", "ICONS = [\n    ('i_tod_h2_ab_cloak', ico_cloak, 'x', []),\n", 1)
        expect(set(pk05_claims(pk_now)) & set(NAMES), 'PK05 claiming a tile was NOT caught')
        staged = os.path.join(STAGE_ROOT, PK05_REL)
        if os.path.isfile(staged):
            expect(not pk05_claims(open(staged, encoding='utf-8').read()), 'the staged PK05 still claims a tile')
        # 4. a state tint on the icon
        lo = _read(STAGE_ROOT, LOADOUT_REL)
        fb = _read(STAGE_ROOT, FEEDBACK_REL)
        expect(not tint_problems(lo, fb), 'the shipping loadout already fails the tint contract: %s' % tint_problems(lo, fb))
        bad_lo = lo.replace('slot.icon:setRGB( 1, 1, 1 )', 'slot.icon:setRGB( 0.6, 0.8, 1 )', 1)
        expect(bad_lo != lo and tint_problems(bad_lo, fb), 'a tinted ability icon was NOT caught')
        expect(tint_problems(lo, fb + '\nslot.icon:setAlpha( 0 )\n'), 'the feedback widget touching an icon was NOT caught')
        # 4a. a retired glyph named again (a white square in game: its zone line is gone)
        troot = os.path.join(tmp, 'root')
        os.makedirs(os.path.dirname(os.path.join(troot, LOADOUT_REL)))
        with open(os.path.join(troot, LOADOUT_REL), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(lo + '\nlocal TOD_RETIRED_PROBE = "i_tod_hud_off_cloak"\n')
        for rel in (PK05_REL, GDT_REL):
            src = os.path.join(STAGE_ROOT, rel)
            if os.path.isfile(src):
                os.makedirs(os.path.dirname(os.path.join(troot, rel)), exist_ok=True)
                shutil.copy2(src, os.path.join(troot, rel))
        expect(any('i_tod_hud_off_cloak is retired' in m and 'AetheriumLoadout.lua' in m
                   for m in wiring_problems(troot, [])), 'a retired glyph named in the Lua was NOT caught')
        # 4b. a class accent that moved in the draft (the tiles would wear a stale class colour)
        sel = _read(STAGE_ROOT, SELECT_LUA_REL)
        expect(not accent_problems(sel), 'the shipping class accents already fail: %s' % accent_problems(sel))
        moved = sel.replace('accent = { 0.75, 0.45, 1.00 }', 'accent = { 0.70, 0.45, 1.00 }', 1)
        expect(moved != sel and accent_problems(moved), 'a moved class accent was NOT caught')
        # 5. every coloured glyph carries colour; the silk one stays (near) white; every shape is kept
        for name, (im, _) in built.items():
            a = np.asarray(im).astype(int)
            ink = a[..., 3] >= 250
            sat = (a[..., :3].max(-1) - a[..., :3].min(-1))[ink]
            coloured = int((sat > 90).sum())
            if SPEC[name][2] == WIDOWS_SILK:
                expect(coloured < 0.01 * ink.sum(), '%s (white silk) carries a saturated accent' % name)
            else:
                # at least a 7 px dot at 128 (2 px on the 36 px tile): the C4's armed light is the smallest, ~80 px
                expect(coloured >= 40, '%s has no visible accent (%d saturated ink px)' % (name, coloured))
            expect(not shape_problems(name, im), '%s: %s' % (name, shape_problems(name, im)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        for f in fails:
            print('W3B SELFTEST FAIL: ' + f)
        return 1
    print('W3B SELFTEST OK %d checks (a stale glyph, a drifted master, PK05 double ownership, an icon tint, a retired glyph named again, a moved class accent - each caught; '
          'every glyph coloured where it should be and its shape kept)' % ok)
    return 0

# ================================================================================================ measure

def measure():
    print('%-24s %-10s %-10s %-34s %-34s %s' % ('glyph', 'recov max', 'mean', 'glow OLD (2/4/6/8/10 px)', 'glow NEW', 'accent'))
    for name in NAMES:
        C, m = white_core(name)
        old = Image.open(os.path.join(artgen.IMG, name + '.png')) if os.path.isfile(os.path.join(artgen.IMG, name + '.png')) else None
        if m is not None:
            A = np.asarray(m, dtype=np.float64)[..., 3] / 255.0
            G = np.clip(DECON_GAIN * ndimage.gaussian_filter(C, DECON_SIGMA, mode='constant'), 0, 1)
            err = np.abs(C + G * (1 - C) - A)
            e1, e2 = '%.4f' % err.max(), '%.5f' % err[(A > 0.01)].mean()
        else:
            e1, e2 = 'vector', '-'
        im = glyph(name)
        _, acc, _ = split(name)
        share = acc.sum() / max(1e-9, C.sum())
        print('%-24s %-10s %-10s %-34s %-34s %4.1f%% of the ink' % (name, e1, e2, pk05.glow_profile(old) if old else '-',
                                                                    pk05.glow_profile(im), share * 100))
    return 0

# ================================================================================================ review
UI_MOCK = os.path.join(ROOT, 'tools', 'ui_mockup')
WIDGETS = os.path.join(ROOT, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets')
LABEL_TTF = os.path.join(ROOT, 'fonts', 'ltromatic.ttf')     # AetheriumLoadout's archerLabels setTTF
KQ = 1.5                                                      # the 1280 canvas -> 1080p
# The states each kit's server really sends (LOCKSTEP the GSC hud_send contracts quoted in AetheriumLoadout's
# CLASS_KITS): [(lethal, tactical) ...] replayed in order - a CHARGING row starts from a fuller value so the
# recharge frame shows real progress (TodAbilityFeedback infers the total from the first value after a cast).
KIT_STATES = [
    ('ARCHER', 0, [('READY', [(2000, 0)]),
                   ('CHARGING', [(2000, 0), (12, 10), (5, 4)]),
                   ('LOCKED / ACTIVE', [(-2, -1)])]),
    ('WARRIOR', 1, [('READY', [(0, 0)]),
                    ('CHARGING', [(0, 0), (20, 8), (9, 3)]),
                    ('LOCKED / ACTIVE', [(-2, -1)])]),
    ('BREACHER', 2, [('READY', [(2, 3)]),
                     ('EMPTY', [(2, 3), (0, 0)]),
                     ('LOCKED', [(-1, -1)])]),
    ('NECROMANCER', 3, [('READY', [(0, 0)]),
                        ('CHARGING', [(0, 0), (40, 30), (17, 12)]),
                        ('LOCKED / ACTIVE', [(-1, -2)])]),
]
# kit-less (the stock offhands): (label, perks) - the lethal swaps to the web grenade with Widow's, its PhD form with both
STOCK_STATES = [('FRAG + MONKEY', ()), ("WIDOW'S WINE", ('widows_wine',)), ("WIDOW'S + PHD", ('widows_wine', 'electric_cherry'))]
CROP = (1094, 556, 1272, 684)                                 # canvas units: the two tiles, the PaP slot, the gun plate


def _lua_loadout(new=False):
    """The REAL loadout under the timed mock. new = the landing's AetheriumLoadout.lua (the staged copy before the
    landing - it names the cloak tile directly), else the repo's."""
    import lupa.lua51 as lua51
    L = lua51.LuaRuntime(unpack_returned_tuples=True)
    L.execute(open(os.path.join(UI_MOCK, 'mock_lui_anim.lua'), encoding='utf-8').read())
    L.execute('LUI.UIImage.GetCachedMaterial = function( s ) return s end; CoD.PowerUps = {}; CoD.AetheriumWeapons = {}; '
              'Enum.UIVisibilityBit.BIT_SCOREBOARD_OPEN = 1')
    for f in ('TodUIOwnership', 'TodHealthTint', 'TodGlyphMetrics', 'TodGlyphRow', 'TodGlyphText', 'TodAbilityFeedback',
              'AetheriumPerkItem', 'AetheriumPerksContainer', 'AetheriumLoadout'):
        p = os.path.join(WIDGETS, f + '.lua')
        if new and f == 'AetheriumLoadout' and os.path.isfile(os.path.join(STAGE_ROOT, LOADOUT_REL)):
            p = os.path.join(STAGE_ROOT, LOADOUT_REL)
        L.execute(open(p, encoding='utf-8').read())
    L.execute(open(os.path.join(ROOT, 'ui', 'uieditor', 'widgets', 'HUD', 'Mappings', 'AetheriumPerks.lua'), encoding='utf-8').read())
    w = L.eval('CoD.AetheriumLoadout.new( {}, 0 )')
    g = L.globals()
    g.PUSH('currentWeapon.ammoInClip', 24)
    g.PUSH('currentWeapon.ammoStock', 120)
    return L, w, g


def kit_items(kit, seq, new=False):
    L, w, g = _lua_loadout(new)
    for lethal, tac in seq:
        g.NOTIFY('tod_archer_abil', L.table(1, lethal, tac, kit))
        g.ADVANCE(2500)
    return [dict(x) for x in g.DUMP(w).values()]


def stock_items(perks, new=False):
    L, w, g = _lua_loadout(new)
    g.NOTIFY('tod_archer_abil', L.table(1, 0, 0, 0))
    g.ADVANCE(100)
    g.NOTIFY('tod_archer_abil', L.table(0, 0, 0))
    g.ADVANCE(100)
    g.PUSH('currentPrimaryOffhand.primaryOffhandCount', 2)
    g.PUSH('currentSecondaryOffhand.secondaryOffhandCount', 1)
    for p in perks:
        g.PUSH('hudItems.perks.' + p, 1)
    g.ADVANCE(2500)
    return [dict(x) for x in g.DUMP(w).values()]


def render_items(items, art_dir, landed=False):
    """The dump drawn at 1080p (render_pull.draw for the images, the labels in the label TTF at their 0.7 scale)."""
    sys.path.insert(0, UI_MOCK)
    import render_pull as rp
    from PIL import ImageFont
    rp.SCALE = KQ
    rp.ART_DIR = art_dir
    rp._cache.clear()
    rp._sized.clear()
    canvas = rp.draw([it for it in items if it['img']], rp.backdrop())
    # the archerLabels: a 20-unit box at setScale( 0.7 ), em = box x 0.8 (render_pull's UIText convention)
    size = int(round(20 * 0.7 * KQ * 0.8))
    font = ImageFont.truetype(LABEL_TTF, size)
    d = ImageDraw.Draw(canvas)
    for it in items:
        if it['img'] or not it.get('text'):
            continue
        s = it['text']
        cx, cy = (it['x0'] + it['x1']) / 2 * KQ, (it['y0'] + it['y1']) / 2 * KQ
        tw = d.textlength(s, font=font)
        col = tuple(int(255 * max(0.0, min(1.0, c))) for c in (it['r'], it['g'], it['b'])) + (int(255 * max(0.0, min(1.0, it['a']))),)
        layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((cx - tw / 2, cy - size * 0.62), s, fill=col, font=font)
        canvas.alpha_composite(layer)
    missing = {it['img'] for it in items if it['img'] and it['img'] != '$white' and rp.find_image(it['img']) is None}
    if landed:                        # the landed state: a retired glyph is gone from _images even if the repo still has it
        missing |= {it['img'] for it in items if it['img'] in RETIRED}
    return canvas.crop(tuple(int(round(v * KQ)) for v in CROP)), missing


def review(built, out_dir):
    """_review.png: every class's two tiles at 1080p (1:1) in each state, OLD above NEW, drawn by the REAL
    AetheriumLoadout.lua + TodAbilityFeedback.lua under the timed LUI mock, + a 3x zoom of each NEW ready pair;
    then the kit-less stock offhands; then the pause-menu row twins (unchanged, magenta-tinted by state)."""
    font = artgen.ttf(22)
    small = artgen.ttf(17)
    rows, missing = [], set()
    # OLD = the files this pack replaces (base/, kept from the first --stage), so the sheet stays honest after the landing
    old_dir = os.path.join(BASE_ROOT, IMG_REL) if os.path.isdir(os.path.join(BASE_ROOT, IMG_REL)) else None
    for cls, kit, states in KIT_STATES:
        cells = []
        for label, seq in states:
            o, m1 = render_items(kit_items(kit, seq), old_dir)
            n, m2 = render_items(kit_items(kit, seq, True), out_dir, True)
            missing |= set(m1) | set(m2)
            cells.append((label, o, n))
        rows.append((cls, cells))
    stock = []
    for label, perks in STOCK_STATES:
        o, m1 = render_items(stock_items(perks), old_dir)
        n, m2 = render_items(stock_items(perks, True), out_dir, True)
        missing |= set(m1) | set(m2)
        stock.append((label, o, n))
    rows.append(('STOCK - NO CLASS KIT', stock))
    cw, ch = rows[0][1][0][1].size
    zw = int((1262 - 1162) * KQ * 3)
    zh = int((602 - 566) * KQ * 3)
    pad, lab = 18, 30
    W = pad + 3 * (cw + pad) + zw + pad * 2
    H = 70 + sum(lab + 2 * ch + 26 + pad for _ in rows) + 330
    sheet = Image.new('RGBA', (W, H), (16, 12, 26, 255))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), 'W3B ABILITY GLYPHS IN COLOUR - 1080P 1 TO 1 - OLD ABOVE NEW - DRAWN BY THE SHIPPING AETHERIUMLOADOUT LUA',
           fill=(235, 230, 245, 255), font=font)
    d.text((pad, 42), 'RIGHT - THE NEW READY PAIR AT 3X.  LABELS APPROXIMATE THE GAME TTF.  NOTHING ELSE ON THE HUD CHANGES.',
           fill=(160, 160, 190, 255), font=small)
    y = 70
    for title, cells in rows:
        d.text((pad, y), title, fill=(255, 210, 90, 255), font=font)
        y += lab
        for i, (label, o, n) in enumerate(cells):
            x = pad + i * (cw + pad)
            sheet.alpha_composite(o, (x, y))
            sheet.alpha_composite(n, (x, y + ch + 4))
            d.text((x + 4, y + 2 * ch + 6), label, fill=(200, 205, 220, 255), font=small)
            d.text((x + 6, y + 4), 'OLD', fill=(255, 255, 255, 200), font=small)
            d.text((x + 6, y + ch + 8), 'NEW', fill=(31, 229, 255, 255), font=small)
        zx = pad + 3 * (cw + pad) + pad
        # the zoom: the first NEW cell, tiles only (canvas 1162..1262 x 566..602 inside CROP)
        n0 = cells[0][2]
        box = tuple(int(round((v - c) * KQ)) for v, c in zip((1162, 566, 1262, 602), (CROP[0], CROP[1], CROP[0], CROP[1])))
        sheet.alpha_composite(n0.crop(box).resize((zw, zh), Image.LANCZOS), (zx, y + (2 * ch - zh) // 2))
        y += 2 * ch + 26 + pad
    # the row twins: what the pause menu draws for the same abilities (tinted by state, unchanged) beside the tile glyph
    d.text((pad, y), 'PAUSE MENU ROW TWINS - UNCHANGED WHITE GLYPHS TINTED BY STATE - BESIDE THE NEW TILE GLYPH',
           fill=(255, 210, 90, 255), font=font)
    y += lab + 6
    twins = [('i_tod_pm_ico_grapple', 'i_tod_h2_ab_hook'), ('i_tod_pm_ico_retriever', 'i_tod_h2_ab_axe'),
             ('i_tod_pm_ico_bash', 'i_tod_h2_ab_bash'), ('i_tod_pm_ico_gravsmash', 'i_tod_h2_ab_smash'),
             ('i_tod_pm_ico_cluster', 'i_tod_h2_ab_cluster'), ('i_tod_pm_ico_c4', 'i_tod_h2_ab_c4'),
             ('i_tod_pm_ico_cloak', 'i_tod_h2_ab_cloak'), ('i_tod_pm_ico_soulbomb', 'i_tod_h2_ab_soul_bomb')]
    tile = Image.open(artgen.shipped('i_tod_h2_tile_ready')).convert('RGBA')
    row = Image.open(artgen.shipped('i_tod_pm_row')).convert('RGBA')
    pm = (1.00, 0.17, 0.82)                                     # LOCKSTEP AetheriumStartMenu.lua PM_RED (magenta)
    x = pad
    for pmn, abn in twins:
        p_h = 67 * KQ
        rw = int(round(67 * 1024 / 200.0 * KQ))
        r_ = row.resize((rw, int(round(p_h))), Image.LANCZOS).crop((0, 0, 150, int(round(p_h))))
        sheet.alpha_composite(r_, (x, y))
        g = 40 * 67 / 63.0 * KQ
        ic = np.asarray(Image.open(artgen.shipped(pmn)).convert('RGBA')).astype(np.float64)
        ic[..., :3] *= np.array(pm)[None, None, :]
        ic = Image.fromarray(np.clip(ic, 0, 255).astype(np.uint8), 'RGBA').resize((int(g), int(g)), Image.LANCZOS)
        cx, cy = x + 96 * p_h / 200.0, y + 100 * p_h / 200.0
        sheet.alpha_composite(ic, (int(cx - g / 2), int(cy - g / 2)))
        tw, th, gg = int(46 * KQ), int(32 * KQ), int(24 * KQ)
        tx, ty = x + 160, y + int((p_h - th) / 2)
        sheet.alpha_composite(tile.resize((tw, th), Image.LANCZOS), (tx, ty))
        sheet.alpha_composite(built[abn][0].resize((gg, gg), Image.LANCZOS), (tx + int(5 * KQ), ty + int(4 * KQ)))
        d.text((x, y + int(p_h) + 6), SPEC[abn][6], fill=(200, 205, 220, 255), font=small)
        x += 160 + tw + 40
        if x > W - 300:
            x = pad
            y += int(p_h) + 40
    y += int(67 * KQ) + 40
    sheet = sheet.crop((0, 0, W, min(H, y + 10)))
    path = os.path.join(out_dir, '_review.png')
    sheet.convert('RGB').save(path, optimize=True)
    return path, sorted(missing)


def glyph_sheet(built, out_dir):
    """_review_glyphs.png: each glyph OLD | NEW at 128 on the ready tile's glass, then at its real 36 px on the
    READY / CHARGING / LOCKED tiles (the alphas AetheriumLoadout sets), and the accent mask (what is coloured)."""
    font = artgen.ttf(18)
    tile_r = Image.open(artgen.shipped('i_tod_h2_tile_ready')).convert('RGBA')
    tile = Image.open(artgen.shipped('i_tod_h2_tile')).convert('RGBA')
    cellh = 150
    W = 1500
    sheet = Image.new('RGBA', (W, 40 + len(NAMES) * cellh), (16, 12, 26, 255))
    d = ImageDraw.Draw(sheet)
    d.text((14, 10), 'EACH GLYPH - OLD AND NEW AT 128 - THE NEW ONE AT 36 PX IN READY / CHARGING / LOCKED - WHAT IS COLOURED',
           fill=(235, 230, 245, 255), font=font)
    glass = tile_r.crop((40, 20, 144, 108)).resize((136, 136), Image.LANCZOS)
    for i, name in enumerate(NAMES):
        y = 40 + i * cellh
        old = Image.open(os.path.join(BASE_ROOT, IMG_REL, name + '.png')).convert('RGBA') \
            if os.path.isfile(os.path.join(BASE_ROOT, IMG_REL, name + '.png')) else Image.open(artgen.shipped(name)).convert('RGBA')
        x = 14
        for im in (old, built[name][0]):
            bg = glass.copy()
            bg.alpha_composite(im, (4, 4))
            sheet.alpha_composite(bg, (x, y))
            x += 146
        tw, th, gg = int(46 * KQ), int(32 * KQ), int(24 * KQ)
        for t_img, t_a, i_a in ((tile_r, 1.0, 1.0), (tile, 0.4, 0.35), (tile, 0.4, 0.2)):
            for im in (old, built[name][0]):
                t = t_img.resize((tw, th), Image.LANCZOS)
                t.putalpha(t.split()[3].point(lambda v, k=t_a: int(v * k)))
                bg = Image.new('RGBA', (tw, th), (30, 24, 40, 255))
                bg.alpha_composite(t)
                gi = im.resize((gg, gg), Image.LANCZOS)
                gi.putalpha(gi.split()[3].point(lambda v, k=i_a: int(v * k)))
                bg.alpha_composite(gi, (int(5 * KQ), int(4 * KQ)))
                sheet.alpha_composite(bg, (x, y + 20))
                x += tw + 6
            x += 18
        _, acc, C = split(name)
        mk = np.zeros((S, S, 4), np.uint8)
        mk[..., 0] = mk[..., 1] = mk[..., 2] = 255
        mk[..., 3] = np.clip(np.round(C * 90), 0, 255).astype(np.uint8)
        hue = np.array(r4.hexrgb(SPEC[name][2]))
        mk[acc > 0.02, :3] = hue
        mk[..., 3] = np.maximum(mk[..., 3], np.clip(np.round(acc * 255), 0, 255).astype(np.uint8))
        sheet.alpha_composite(Image.fromarray(mk, 'RGBA'), (x, y))
        d.text((x + 140, y + 20), name.replace('i_tod_h2_ab_', '').upper().replace('_', ' '), fill=(255, 210, 90, 255), font=font)
        d.text((x + 140, y + 48), SPEC[name][5] + ' - ' + SPEC[name][6], fill=(200, 205, 220, 255), font=font)
        d.text((x + 140, y + 76), SPEC[name][7].upper().replace(',', ' -').replace('(', '').replace(')', ''),
               fill=tuple(int(v) for v in hue) + (255,), font=font)
    path = os.path.join(out_dir, '_review_glyphs.png')
    sheet.convert('RGB').save(path, optimize=True)
    return path

# ================================================================================================== main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--stage', action='store_true', help='also write tmp/wave3/%s/stage/ (+ base/)' % PACK)
    ap.add_argument('--install', action='store_true', help='LANDING ONLY: copy into source_data/tod_ui_images/_images')
    ap.add_argument('--check', action='store_true', help='fail on any byte / master / wiring / tint-contract problem')
    ap.add_argument('--against', choices=('installed', 'stage'), default='installed')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--measure', action='store_true')
    ap.add_argument('--no-review', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.measure:
        return measure()
    if a.check:
        against_stage = a.against == 'stage'
        img_dir = os.path.join(STAGE_ROOT, IMG_REL) if against_stage else artgen.IMG
        root = STAGE_ROOT if against_stage else ROOT
        pending = []
        try:
            bad = check(img_dir, root, pending=pending)
        except W3BError as e:
            bad = [str(e)]
        for m in bad:
            print('W3B ABILITY GLYPHS: ' + m)
        for m in pending:
            print('W3B ABILITY GLYPHS: (landing step, not staged) ' + m)
        if bad:
            print('W3B ABILITY GLYPHS --check FAILED: %d problem(s) (re-run: python -B tools/artgen/packs/w3b_ability_colour.py --install)' % len(bad))
            return 1
        print('W3B ABILITY GLYPHS OK %d glyphs + masters + wiring + tint contract (%s)' % (len(NAMES), 'stage' if against_stage else 'installed'))
        return 0
    seed_masters()
    built = build_all()
    os.makedirs(OUT, exist_ok=True)
    for name, (im, data) in built.items():
        with open(os.path.join(OUT, name + '.png'), 'wb') as fh:
            fh.write(data)
        print('%-26s %s' % (name, hashlib.md5(data).hexdigest()))
    if a.stage:
        print('staged ->', stage(built))
    if a.install:
        for name, (im, data) in built.items():
            with open(os.path.join(artgen.IMG, name + '.png'), 'wb') as fh:
                fh.write(data)
        print('installed %d glyphs into %s' % (len(built), artgen.IMG))
    if not a.no_review:
        print('glyphs ->', glyph_sheet(built, OUT))
        path, missing = review(built, OUT)
        print('review ->', path)
        if missing:
            print('W3B review: MISSING images (white squares in game): ' + ', '.join(missing))
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
