"""R5 - THE TIER CARDS THAT STILL SHOWED THE WRONG WEAPON (lead, 2026-10-05, the library-consistency pass).

User: "make the WHOLE asset library look like one library". Walking the layered tier cards against the models the
game hands out found four still drawn for Map One's classes (the old Slasher's gold sword and gold spiked glove, a
wooden pump gun, a sci-fi crossbow). Each is redrawn here FROM THE GAME'S OWN MODEL with R2's render + stylize
(tools/artgen/packs/r2_card_subjects.py: an orthographic z-buffer of the xmodel_bin, k-means flat regions coloured
by art-directed probes, three light bands, the navy outline) and composed on the same card2 background template,
pips and sparkles, so it sits in its row exactly like R2's Peacekeeper and staff cards:

  i_tod_card2_art_tier_heavy_2     was a wooden-stock pump shotgun - now the REMINGTON 870 MCS the Breacher is
                                   handed (vm_t6_remington870mcs: breaching muzzle, the mag tube under the barrel,
                                   the pump, the railed receiver, pistol grip, the bare buffer tube; the two loose
                                   shells the model parks under it are dropped)
  i_tod_card2_art_tier_slasher_2   was a gold spiked glove - now the GAUNTLET OF SIEGFRIED (the dragon gauntlet's
                                   view model: the armoured black fist and bracer with the red whelp riding it,
                                   wings spread)
  i_tod_card2_art_tier_slasher_3   was a gold broadsword - now the CYBER SWORD (tod_cyber_sword: black blade, the
                                   cyan circuit traces and violet cells of its spine, the winged guard and its blue
                                   reactor gem, the wrapped grip, the faceted pommel)
  i_tod_card2_art_tier_assault_2   was a black sci-fi crossbow with a scope - now the crossbow the Archer is handed
                                   (wpn_t9_crossbow_view: walnut thumbhole stock, black rail and riser, the wide prod
                                   and its cables), seen from above so the prod reads
The same walk found four more card illustrations drawing those weapons in use; each keeps its card's idea and
its family's hand-drawn effects (redrawn here as SVG: the navy-outlined starburst, beads, speed lines, impact star):
  i_tod_card2_art_arms_specialist  the Warrior's core card: was the gold sword in a black glove - now the Cyber Sword
                                   swung through two violet reach trails
  i_tod_card2_art_bash             was the gold glove dashing - now the Cyber Sword dashing on speed lines
  i_tod_card2_art_demon_slayer     was the gold sword across a red demon - the same demon (redrawn), the Cyber Sword
  i_tod_card2_art_buckshot         the Breacher's core card: was the wooden pump gun firing - now the 870 MCS firing,
                                   the starburst at its muzzle and the pellet cloud fanning out

  python -B r5_tier_subjects.py --render [name ...]   rasterise the models into art/generated/R5-tier-subjects/src/
  python -B r5_tier_subjects.py                       write the 8 PNGs + _review.png to art/generated/R5-tier-subjects/
  python -B r5_tier_subjects.py --stage DIR           also write them under DIR/source_data/tod_ui_images/_images/
  python -B r5_tier_subjects.py --install             also write them into source_data/tod_ui_images/_images/
  python -B r5_tier_subjects.py --check [--root DIR]  BUILD GATE: fail on any byte that differs from the installed PNG
The cached buffers in src/ are the generator's input, so --check needs neither PyCoD nor C:\\BO3Tools.
"""
import argparse, json, math, os, sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import artgen  # noqa: E402
import r2_card_subjects as r2  # noqa: E402

PACK = 'R5-tier-subjects'
ROOT = artgen.ROOT
OUT = os.path.join(ROOT, 'art', 'generated', PACK)
SRC = os.path.join(OUT, 'src')
R2_SRC = r2.SRC                                     # the card2 background templates (card2_bg_L/R.png) live there
IMG_REL = r2.IMG_REL
BO3 = 'C:/BO3Tools/TOD2Cybercity/model_export'
Z_UP = r2.Z_UP                                      # model x forward / z up -> view x right / y up, the right side out

T6 = BO3 + '/skye_ports/t6_remington870mcs/images/~-gmtl_t6_wpn_shotty_870mcs_col.tiff'
GT = BO3 + '/black_ops_3/wpn_t7_zmb_dlc3_gauntlet_dragon/_images/i_wpn_t7_zmb_dlc3_gauntlet_dragon_'
DR = BO3 + '/black_ops_3/c_zom_dlc3_dragon/_images/i_c_zom_dlc3_dragon_'
XB = BO3 + '/hb/crossbow/t9_wpn_ports/t9_crossbow/images/i_wpn_t9_special_crossbow_'


def _no_loose_shells(P, M):
    """the 870's view model parks two loose red shells under the receiver for the reload; they are not the gun"""
    c = P.mean(1)
    return ~((M == 3) & (c[:, 2] < 0.6))


SUBJECTS = {
    'rem870': dict(
        model=BO3 + '/skye_ports/t6_remington870mcs/vm_t6_remington870mcs.xmodel_bin',
        tex={0: (0.85, 0.95, 0.85), 1: (0.3, 0.8, 0.3), 2: BO3 + '/skye_ports/t6_wepcommon/shotgun_shells/green/~-gshells_green_c.tiff',
             3: BO3 + '/skye_ports/t6_wepcommon/shotgun_shells/red/~-gshells_red_c.tiff', 4: T6, 5: T6, 6: T6, 7: T6},
        keep=_no_loose_shells,
        base=Z_UP, view=(22, 10, 13), canvas=(1152, 896), scale=32.5, anchor=(8.0, 0.0, 0.4), at=(592, 446)),
    'gauntlet': dict(
        model=BO3 + '/black_ops_3/wpn_t7_zmb_dlc3_gauntlet_dragon/wpn_t7_zmb_dlc3_gauntlet_dragon_view.xmodel_bin',
        tex={0: GT + 'glo_c.png', 1: (0.30, 0.34, 0.40), 2: GT + '01_c.png', 3: GT + '02_c.png', 4: GT + '03_c.png',
             5: DR + 'wings_03_2_c.png', 6: DR + 'head_01_2_c.png', 7: DR + 'head_02_2_c.png', 8: DR + 'neck_01_2_c.png',
             9: DR + 'neck_02_2_c.png', 10: DR + 'back_2_c.png', 11: DR + 'chest_2_c.png', 12: DR + 'legs_2_c.png',
             13: DR + 'tail_01_2_c.png', 14: DR + 'tail_02_2_c.png', 15: DR + 'wings_01_2_c.png', 16: DR + 'wings_02_2_c.png',
             17: GT + 'glo_c.png', 18: GT + 'glo_c.png'},
        base=Z_UP, view=(-28, 34, 6), canvas=(1152, 896), scale=31.0, anchor=(-6.6, -3.3, 5.4), at=(566, 466)),
    'cybersword': dict(
        model=os.path.join(ROOT, 'model_export', 'tod_warrior', 'cyber_sword', 'tod_cyber_sword_lod0.xmodel_bin'),
        tex={0: os.path.join(ROOT, 'model_export', 'tod_warrior', 'cyber_sword', '_images', 'i_tod_cyber_sword_c.png')},
        base=Z_UP, view=(0, 0, -52), canvas=(1152, 896), scale=20.5, anchor=(0.0, 0.0, 17.3), at=(580, 452)),
    'crossbow': dict(
        model=BO3 + '/hb/crossbow/t9_wpn_ports/t9_crossbow/wpn_t9_crossbow_view.XMODEL_BIN',
        tex={0: XB + 'front_c.png', 1: XB + 'middle_c.png', 2: XB + 'bow_c.png', 3: XB + 'stock_c.png',
             4: XB + 'chin_pad_c.png', 5: XB + 'top_c.png', 6: (0.2, 0.2, 0.2), 7: XB + 'stock_c.png',
             8: XB + 'middle_c.png', 9: (0.15, 0.15, 0.15), 10: (0.15, 0.15, 0.15), 11: XB + 'bow_c.png'},
        base=Z_UP, view=(18, 44, 14), canvas=(1152, 896), scale=30.0, anchor=(6.3, 0.0, 1.7), at=(566, 456)),
}

SWORD = SUBJECTS['cybersword']
# the same models posed for the class cards that show them in use (the card art's own composition kept: a blade
# swung through an arc, a blade dashing, a blade across a demon, a shotgun firing)
SUBJECTS.update({
    'sword_arms': dict(SWORD, view=(0, 0, -28), scale=16.8, anchor=(0.0, 0.0, 17.3), at=(600, 452)),
    'sword_bash': dict(SWORD, view=(0, 0, -84), scale=15.4, anchor=(0.0, 0.0, 17.3), at=(700, 456)),
    'sword_demon': dict(SWORD, view=(0, 0, -50), scale=18.6, anchor=(0.0, 0.0, 17.3), at=(560, 470)),
    'rem870_buck': dict(SUBJECTS['rem870'], view=(12, 8, 5), scale=27.0, anchor=(25.6, 0.0, 3.2), at=(712, 424)),
})

NAMES = {'i_tod_card2_art_tier_heavy_2': 'rem870', 'i_tod_card2_art_tier_slasher_2': 'gauntlet',
         'i_tod_card2_art_tier_slasher_3': 'cybersword', 'i_tod_card2_art_tier_assault_2': 'crossbow',
         'i_tod_card2_art_arms_specialist': 'sword_arms', 'i_tod_card2_art_bash': 'sword_bash',
         'i_tod_card2_art_demon_slayer': 'sword_demon', 'i_tod_card2_art_buckshot': 'rem870_buck'}


def _bind():
    """point R2's renderer and buffer reader at this pack's cache"""
    r2.SRC = SRC
    r2.SUBJECTS.update(SUBJECTS)


def render(name):
    _bind()
    s = SUBJECTS[name]
    orig = r2.load_model

    def filtered(path):
        P, N, U, M = orig(path)
        if s.get('keep'):
            k = s['keep'](P, M)
            return P[k], N[k], U[k], M[k]
        return P, N, U, M
    r2.load_model = filtered
    try:
        meta = r2.render_subject(name)
    finally:
        r2.load_model = orig
    meta.pop('keep', None)
    return meta

# --------------------------------------------------------------------------------------------- the styles
# probes: (the albedo colour a k-means cluster sits nearest, the flat colour it is painted) - None = absorbed

GUNMETAL = (58, 62, 80)                            # the library's black-metal pair: the R2 Peacekeeper's dark parts
STEEL = (122, 132, 158)

STYLES = {
    # one texture for the whole gun: its near-black finish splits into a body tone, a darker shadow tone and the
    # lighter worn steel of the rail, the pump grooves and the muzzle teeth; the side-saddle shells stay red
    'rem870': dict(
        med=11, rim=(196, 210, 236), rim_w=3, min_area=1600, mult=(0.72, 1.0, 1.28), hl_add=0.05,
        groups=[dict(mats=(4, 5, 6, 7), k=6, maj=17, probes=[
            ((27, 27, 27), (44, 47, 62)), ((33, 32, 33), GUNMETAL), ((39, 36, 35), GUNMETAL),
            ((44, 44, 44), GUNMETAL), ((63, 62, 63), (92, 100, 124)), ((67, 67, 65), (92, 100, 124))])],
        mat_colour={3: (204, 52, 52), 2: (90, 170, 96), 0: (220, 255, 226), 1: (120, 255, 140)},
        keep_mats=(0, 1, 3), min_area_by={(204, 52, 52): 60}, light=(-0.3, 0.75, 0.6)),
    # the black dragon gauntlet and the red whelp: the dragon reads in three reds (scales, the darker spine and
    # bones, the pale wing membrane), the gauntlet as black steel, the bronze rivet band, the olive bracer plate
    # and the brown leather sleeve; the gold glow inserts stay lit
    'gauntlet': dict(
        med=7, rim=(255, 176, 132), rim_w=3, min_area=700, mult=(0.70, 1.0, 1.24), hl_add=0.04,
        groups=[dict(mats=(2,), k=5, maj=11, probes=[
                    ((33, 31, 28), (48, 50, 64)), ((64, 59, 49), (104, 112, 100)), ((80, 60, 49), (182, 124, 74)),
                    ((61, 46, 38), (182, 124, 74)), ((31, 54, 70), (64, 150, 210))])],
        mat_colour={3: (52, 54, 68), 4: (128, 84, 60), 17: (196, 44, 44), 1: (120, 150, 172),
                    5: (214, 88, 82), 15: (214, 88, 82), 16: (214, 88, 82),               # the wing membranes
                    6: (178, 42, 50), 7: (178, 42, 50), 8: (178, 42, 50), 9: (178, 42, 50),   # head, neck,
                    10: (150, 34, 44), 11: (196, 64, 62), 12: (178, 42, 50),                  # the darker back,
                    13: (178, 42, 50), 14: (178, 42, 50)},                                    # the paler chest
        emit={0: ((255, 206, 96), True), 18: ((255, 206, 96), True)},
        keep_mats=(0, 17, 18), light=(-0.35, 0.75, 0.55)),
    # the Cyber Sword: the black blade in three dark slate tones (its bevel planes) - its circuit traces, violet
    # cells and reactor gem are painted on top, lit, from the texture itself (neon)
    'cybersword': dict(
        med=5, rim=(130, 236, 255), rim_w=3, min_area=400, mult=(0.72, 1.0, 1.30), hl_add=0.05,
        groups=[dict(mats=(0,), k=6, maj=9, probes=[
            ((12, 19, 24), (44, 46, 60)), ((17, 25, 34), (58, 62, 80)), ((23, 29, 37), (58, 62, 80)),
            ((27, 33, 37), (78, 84, 106)), ((17, 31, 38), (78, 84, 106)), ((14, 81, 201), (40, 110, 230)),
            ((0, 0, 0), (34, 36, 48))])],
        neon=(('cyan', (110, 240, 255), 1), ('violet', (190, 110, 255), 1), ('gem', (90, 170, 255), 0)),
        crease_cos=0.55, light=(-0.35, 0.7, 0.6)),
    # the crossbow: walnut thumbhole stock (two browns), the grey cheek pad, the black rail, riser and prod in
    # gunmetal with lighter edges, the yellow fletching of the bolts in the quiver
    'crossbow': dict(
        med=7, rim=(244, 198, 140), rim_w=3, min_area=900, mult=(0.72, 1.0, 1.26), hl_add=0.05,
        groups=[dict(mats=(3, 7), k=4, maj=9, probes=[
                    ((87, 53, 34), (168, 104, 60)), ((98, 55, 28), (168, 104, 60)), ((60, 40, 25), (124, 74, 42)),
                    ((35, 35, 35), (48, 50, 64))]),
                dict(mats=(0, 1, 2, 5, 6, 8, 9, 10, 11), k=6, maj=9, probes=[
                    ((2, 2, 2), (40, 43, 58)), ((35, 35, 35), GUNMETAL), ((39, 39, 39), GUNMETAL),
                    ((56, 56, 56), (90, 98, 122)), ((111, 106, 102), STEEL), ((129, 103, 20), (236, 196, 64)),
                    ((47, 43, 27), GUNMETAL)])],
        mat_colour={4: (96, 100, 116)}, min_area_by={(236, 196, 64): 40}, light=(-0.3, 0.75, 0.6)),
}


STYLES['sword_arms'] = STYLES['sword_bash'] = STYLES['sword_demon'] = STYLES['cybersword']
STYLES['rem870_buck'] = STYLES['rem870']


def _neon_masks(alb):
    """the sword's self-lit parts, read straight off its colour texture (measured: traces #0DB4DA, cells #741DDA,
    the gem #0E5DC4)"""
    r, g, b = alb[..., 0], alb[..., 1], alb[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    sat = mx - np.minimum(np.minimum(r, g), b)
    lit = (sat > 0.24) & (mx > 0.35)
    return {'cyan': lit & (g > 0.45) & (b > 0.55) & (r < 0.25),
            'violet': lit & (r > 0.28) & (b > 0.55) & (g < 0.25),
            'gem': lit & (b > 0.55) & (g > 0.2) & (g <= 0.45) & (r < 0.2)}


def stylized(name):
    _bind()
    buf = r2.load_buffers(name)
    st = STYLES[name]
    out = r2.stylize(buf, st)
    neon = np.zeros(buf['m'].shape)
    if st.get('neon'):
        masks = _neon_masks(buf['alb'])
        for key, rgb, dil in st['neon']:
            mk = masks[key] & buf['m']
            if dil:
                mk = ndi.binary_dilation(mk, r2._disk(dil)) & buf['m']
            out[..., :3][mk] = np.array(rgb, float) / 255
            neon = np.maximum(neon, mk)
    return out, neon


def card(name, side, blob_shapes, halo, pips, sparks, neon_glow=None, under=(), over=()):
    """the card2 illustration: background template, the family's faint blob, the subject's halo, pips and sparkles,
    `under` effect layers, the subject, the neon bloom, then `over` effect layers (all RGBA 576x448)"""
    bg = Image.open(os.path.join(R2_SRC, 'card2_bg_%s.png' % side)).convert('RGBA')
    arr, neon = stylized(name)
    subj = r2.down(arr)
    bg = r2.blobs(bg, blob_shapes)
    rgb, strength, radius = halo
    bg = r2.glow(bg, subj.split()[3], rgb, strength, radius)
    for x, y, c, col in pips:
        r2.pip(bg, x, y, c, col)
    for cx, cy, rv, rh in sparks:
        bg = r2.sparkle(bg, cx, cy, rv, rh)
    for lay in under:
        bg.alpha_composite(lay)
    bg.alpha_composite(subj)
    if neon_glow and neon.any():                    # the lit traces bloom a little over the blade, like an emissive
        n1 = np.asarray(Image.fromarray((neon * 255).astype(np.uint8)).resize(bg.size, Image.LANCZOS)).astype(np.float64) / 255
        bg = r2.glow(bg, n1, neon_glow[0], neon_glow[1], neon_glow[2], gain=3.0)
    for lay in over:
        bg.alpha_composite(lay)
    return bg

# ------------------------------------------------------------------------------------- the card2 effects
# Drawn the way the family's hand-drawn effects are (measured off the cards they replace): flat fills, the #0a0c19
# navy outline ~4 px, a light core. SVG at 4x, LANCZOS down; no randomness.

NAVY = '#0A0C19'


def _svg(body, defs=''):
    return artgen.render_svg(artgen.svg_doc(576, 448, body, defs), 576, 448, ss=4)


def _pts(pp):
    return ' '.join('%.1f,%.1f' % (x, y) for x, y in pp)


def _star(cx, cy, r0, r1, n, rot=0.0, jag=()):
    out = []
    for i in range(2 * n):
        r = r1 if i % 2 == 0 else r0
        if jag and i % 2 == 0:
            r *= jag[(i // 2) % len(jag)]
        a = math.radians(rot + 180.0 * i / n)
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def fx_muzzle(cx, cy):
    """BUCKSHOT's blast: the family's orange starburst at the muzzle and the pellet cloud fanning out right, each
    pellet a gold bead with a highlight and a short warm trail (the old card's language, redrawn)."""
    pellets = [(462, 128, 11), (486, 152, 10), (450, 176, 12), (500, 200, 11), (470, 222, 12), (520, 240, 10),
               (440, 246, 11), (496, 272, 12), (530, 170, 9), (452, 296, 10), (540, 300, 9), (424, 200, 10)]
    b = []
    for x, y, r in pellets:                          # trails first: a tapered warm streak back toward the muzzle
        dx, dy = cx - x, cy - y
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        tail = (x + ux * 40, y + uy * 40)
        side = (-uy * r * 0.72, ux * r * 0.72)
        b.append('<polygon points="%s" fill="#FFB04A" fill-opacity="0.42"/>'
                 % _pts([(x + side[0], y + side[1]), tail, (x - side[0], y - side[1])]))
    for x, y, r in pellets:
        b.append('<circle cx="%d" cy="%d" r="%.1f" fill="#FFD66E" stroke="%s" stroke-width="3.6"/>' % (x, y, r, NAVY))
        b.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#FFF4C4"/>' % (x - r * 0.3, y - r * 0.3, r * 0.38))
    outer = _star(cx, cy, 34, 62, 11, rot=-8, jag=(1.0, 0.82, 0.94, 0.76, 1.0, 0.88))
    mid = _star(cx, cy, 24, 44, 11, rot=8, jag=(1.0, 0.86, 0.95))
    b.append('<polygon points="%s" fill="#FF9628" stroke="%s" stroke-width="4.5" stroke-linejoin="round"/>' % (_pts(outer), NAVY))
    b.append('<polygon points="%s" fill="#FFC446"/>' % _pts(mid))
    b.append('<circle cx="%d" cy="%d" r="17" fill="#FFF4C4"/>' % (cx, cy))
    return _svg(''.join(b))


def fx_speed(lines, rgb='#B09CEC'):
    """BASH's dash: the family's rounded speed lines trailing the blade"""
    b = []
    for x0, y0, x1, w in lines:
        b.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%.1f" stroke-linecap="round" '
                 'stroke-opacity="0.9"/>' % (x0, y0, x1, y0, rgb, w))
    return _svg(''.join(b))


def fx_impact(cx, cy, r=26):
    """the family's white impact star (the one at the tip of a hit)"""
    st = _star(cx, cy, r * 0.42, r, 8, rot=-10)
    return _svg('<polygon points="%s" fill="#FFF8E6" stroke="%s" stroke-width="4" stroke-linejoin="round"/>'
                '<circle cx="%d" cy="%d" r="%.1f" fill="#FFE07A"/>' % (_pts(st), NAVY, cx, cy, r * 0.28))


def fx_swing(px, py, r, a_blade, a_end, width=46.0, rgb='#B09CEC'):
    """ARMS SPECIALIST's reach: the swing trail the blade's upper half leaves, an arc about the guard (px, py) that
    is widest where the blade is and tapers to nothing behind it, with a pale leading edge (the cleave card's arc,
    in the Warrior's violet)"""
    n = 48
    outer, inner, edge = [], [], []
    for i in range(n + 1):
        t = i / n                                   # 0 at the blade, 1 at the trail's end
        a = math.radians(a_blade + (a_end - a_blade) * t)
        w = width * (1.0 - t) ** 1.4
        outer.append((px + r * math.cos(a), py + r * math.sin(a)))
        inner.append((px + (r - w) * math.cos(a), py + (r - w) * math.sin(a)))
        if t < 0.75:
            edge.append((px + (r - 3) * math.cos(a), py + (r - 3) * math.sin(a)))
    poly = outer + inner[::-1]
    return _svg('<polygon points="%s" fill="%s" fill-opacity="0.82" stroke="%s" stroke-width="4" stroke-linejoin="round"/>'
                '<polyline points="%s" fill="none" stroke="#F1ECFF" stroke-width="3.2" stroke-linecap="round"/>'
                % (_pts(poly), rgb, NAVY, _pts(edge)))


def fx_demon(cx, cy, s=1.0):
    """DEMON SLAYER's demon, redrawn after the card it replaces (the elite the card is about): the red horned head
    with ivory horns, glowing yellow eyes under a heavy brow, the fanged maw"""
    def P(pp):
        return _pts([(cx + x * s, cy + y * s) for x, y in pp])
    head = [(-96, -40), (-80, -82), (-40, -104), (0, -110), (40, -104), (80, -82), (96, -40), (92, 10), (70, 52),
            (46, 86), (14, 100), (-14, 100), (-46, 86), (-70, 52), (-92, 10)]
    hornL = [(-70, -78), (-112, -120), (-122, -168), (-108, -200), (-104, -160), (-86, -128), (-46, -100)]
    hornR = [(-x, y) for x, y in hornL]
    shadeL = [(-96, -40), (-92, 10), (-70, 52), (-46, 86), (-14, 100), (-30, 60), (-60, 20), (-78, -20)]
    browL = [(-76, -36), (-14, -10), (-18, 4), (-74, -18)]
    browR = [(-x, y) for x, y in browL]
    eyeL = [(-64, -18), (-22, -2), (-30, 16), (-58, 10)]
    eyeR = [(-x, y) for x, y in eyeL]
    maw = [(-52, 38), (52, 38), (40, 76), (-40, 76)]
    fangs = [[(-40, 38), (-28, 38), (-34, 58)], [(-12, 38), (0, 38), (-6, 60)], [(16, 38), (28, 38), (22, 58)],
             [(-24, 76), (-14, 76), (-19, 60)], [(8, 76), (18, 76), (13, 60)]]
    b = ['<defs><radialGradient id="eg"><stop offset="0" stop-color="#FFE47A" stop-opacity="0.9"/>'
         '<stop offset="1" stop-color="#FFB020" stop-opacity="0"/></radialGradient></defs>']
    for h in (hornL, hornR):
        b.append('<polygon points="%s" fill="#F2EAD6" stroke="%s" stroke-width="4.5" stroke-linejoin="round"/>' % (P(h), NAVY))
    b.append('<polygon points="%s" fill="#D63A38" stroke="%s" stroke-width="5" stroke-linejoin="round"/>' % (P(head), NAVY))
    b.append('<polygon points="%s" fill="#A9262E"/>' % P(shadeL))
    for e in (eyeL, eyeR):
        ex = sum(x for x, _ in e) / 4.0
        ey = sum(y for _, y in e) / 4.0
        b.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="url(#eg)"/>' % (cx + ex * s, cy + ey * s, 34 * s))
        b.append('<polygon points="%s" fill="#FFD84E" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>' % (P(e), NAVY))
    for br in (browL, browR):
        b.append('<polygon points="%s" fill="%s"/>' % (P(br), NAVY))
    b.append('<polygon points="%s" fill="#1A0E18" stroke="%s" stroke-width="3" stroke-linejoin="round"/>' % (P(maw), NAVY))
    for f in fangs:
        b.append('<polygon points="%s" fill="#FFF6E6"/>' % P(f))
    return _svg(''.join(b))


PIPS_R = [(292, 28, 8, (69, 230, 255)), (322, 402, 8, (69, 230, 255)), (541, 243, 6, (255, 225, 29)),
          (53, 397, 6, (255, 225, 29)), (53, 37, 6, (255, 255, 255))]
PIPS_L = [(292, 28, 8, (69, 230, 255)), (322, 402, 8, (69, 230, 255)), (541, 243, 6, (255, 225, 29)),
          (53, 397, 6, (255, 225, 29)), (531, 33, 6, (255, 255, 255))]


BLOBS_L = [('e', 330, 260, 560, 440), ('-e', 380, 300, 520, 450), ('e', 40, 160, 160, 300)]


def build_all():
    cyan = ((90, 220, 255), 0.30, 12)
    neon = ((120, 230, 255), 0.45, 3)
    return {
        'i_tod_card2_art_tier_heavy_2': card('rem870', 'L', BLOBS_L, ((150, 200, 255), 0.22, 10), PIPS_L,
                                             [(70, 95, 9, 7), (500, 380, 7, 5)]),
        'i_tod_card2_art_tier_slasher_2': card('gauntlet', 'L', BLOBS_L, ((255, 120, 90), 0.26, 12), PIPS_L,
                                               [(70, 95, 9, 7), (110, 380, 7, 5)]),
        'i_tod_card2_art_tier_slasher_3': card('cybersword', 'L', BLOBS_L, cyan, PIPS_L,
                                               [(70, 95, 9, 7), (480, 330, 7, 5)], neon_glow=neon),
        'i_tod_card2_art_tier_assault_2': card('crossbow', 'L', BLOBS_L, ((255, 196, 120), 0.22, 10), PIPS_L,
                                               [(70, 95, 9, 7), (480, 380, 7, 5)]),
        # the Warrior's core card: the blade swung through a long violet arc (reach and weight)
        'i_tod_card2_art_arms_specialist': card('sword_arms', 'L', BLOBS_L, cyan, PIPS_L, [(70, 95, 9, 7), (500, 380, 7, 5)],
                                                neon_glow=neon, under=[fx_swing(232, 354, 330, -64, -128), fx_swing(232, 354, 250, -66, -120, 30.0)],
                                                over=[fx_impact(452, 74, 24)]),
        # BASH: the blade dashing right on the family's speed lines, the hit at its tip
        'i_tod_card2_art_bash': card('sword_bash', 'L', BLOBS_L, cyan, PIPS_L, [(70, 95, 9, 7), (120, 380, 7, 5)],
                                     neon_glow=neon,
                                     under=[fx_speed([(40, 186, 170, 9), (24, 222, 150, 11), (52, 258, 190, 9),
                                                      (70, 292, 140, 7)])],
                                     over=[fx_impact(532, 214, 26)]),
        # DEMON SLAYER: the blade across the demon (the elite the card is about)
        'i_tod_card2_art_demon_slayer': card('sword_demon', 'L', BLOBS_L, cyan, PIPS_L, [(70, 95, 9, 7), (500, 380, 7, 5)],
                                             neon_glow=neon, under=[fx_demon(272, 236, 1.0)],
                                             over=[fx_impact(352, 168, 24)]),
        # BUCKSHOT: the 870 the Breacher carries, firing - the family's starburst and pellet cloud
        'i_tod_card2_art_buckshot': card('rem870_buck', 'L', BLOBS_L, ((150, 200, 255), 0.22, 10), PIPS_L,
                                         [(70, 95, 9, 7), (120, 380, 7, 5)], over=[fx_muzzle(372, 212)]),
    }

# --------------------------------------------------------------------------------------------- review


def review(imgs):
    rows = []
    for n, s in NAMES.items():
        if n not in imgs:
            continue
        was = os.path.join(SRC, n + '_was.png')
        old = Image.open(was if os.path.isfile(was) else artgen.shipped(n)).convert('RGBA')
        truth = Image.open(os.path.join(SRC, s + '_truth.png')).convert('RGBA')
        rows.append(('%s   was | now | the model (render)' % n, [old, imgs[n], truth]))
    p = os.path.join(OUT, '_review.png')
    if rows:
        artgen.contact_sheet(rows, p, height=300)
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--render', nargs='*')
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--stage')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--root')
    a = ap.parse_args()
    os.makedirs(SRC, exist_ok=True)
    if a.render is not None:
        mp = os.path.join(SRC, 'render.json')
        meta = json.load(open(mp, encoding='utf-8')) if os.path.isfile(mp) else {}
        for n in (a.render or list(SUBJECTS)):
            meta[n] = render(n)
            print('rendered', n, meta[n]['triangles'], 'triangles')
        with open(mp, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(meta, f, indent=1, sort_keys=True)
            f.write('\n')
        return
    imgs = build_all()
    if a.check:
        root = a.root or ROOT
        bad = []
        for n in NAMES:
            p = os.path.join(root, IMG_REL, n + '.png')
            if not os.path.isfile(p):
                bad.append('MISSING %s' % p)
            elif open(p, 'rb').read() != artgen.png_bytes(imgs[n]):
                bad.append('STALE %s (re-run tools/artgen/packs/r5_tier_subjects.py --install; never hand-edit it)' % p)
        if bad:
            for b in bad:
                print('R5 TIER SUBJECTS: ' + b)
            sys.exit(1)
        print('R5 TIER SUBJECTS OK (%d images byte-exact)' % len(NAMES))
        return
    for n in NAMES:
        was = os.path.join(SRC, n + '_was.png')
        if not os.path.isfile(was):
            Image.open(artgen.shipped(n)).save(was)
    for n, im in imgs.items():
        md5 = artgen.save_png(im, os.path.join(OUT, n + '.png'))
        print('%-36s %dx%d  %s' % (n, im.width, im.height, md5))
    for root in ([a.stage] if a.stage else []) + ([ROOT] if a.install else []):
        for n, im in imgs.items():
            artgen.save_png(im, os.path.join(root, IMG_REL, n + '.png'))
    print('review ->', review(imgs))


if __name__ == '__main__':
    main()
