"""synthwave.py - THE MAP 2 UI DESIGN SYSTEM, as code (2026-10-04 R3; THEMED 2026-10-05 RT).

One toolkit for every Map 2 UI surface (docs/180-184): the palette, the frame grammar
(chamfered dark-glass plates, a steel hairline, ONE lit line per container whose colour says
its state), the glow recipe and the typography (the map's own glyph sheets via artgen, with
tracking, tints, glows and an oblique). The module keeps its R3 name because eleven packs
import it; it now draws TWO themes:

  THEME = 'fallen'     THE RED "FALLEN" UI (docs/171 Theme B, docs/180-183; user 2026-10-05:
                       "id rather the red theme please"): neutral charcoal glass, grey scratched
                       steel, RED as the one accent, white text, an ice-blue info colour.
  THEME = 'synthwave'  the neon synthwave UI (docs/184, 2026-10-04 .. 10-05): violet-black glass,
                       magenta frame light, cyan focus, violet secondaries. Kept byte-identical:
                       set THEME back to 'synthwave' and every pack re-renders the shipped
                       synthwave bytes (the RT-impl landing proved it on all ~140 images).

ONE SWITCH. A pack names ROLES ('magenta' = frame light / ready / the headline accent word,
'cyan' = focus / rules / lit pips, 'accent2' = a second lit colour on a framed piece, ...),
never a theme's hex; THEMES below maps every role to a colour per theme. The rule for the
helpers: a ROLE name is theme chrome (it follows THEME), a literal '#RRGGBB' is content
(a class / rarity / perk / power-up hue) and never moves. The written rules are
tmp/redesign/R3-synthwave-system/STYLE.md (synthwave) and docs/180-183 + tmp/redtheme/RT-impl
(fallen); this file is the executable copy, so a pack that imports it cannot drift.

  from synthwave import *            # (tools/artgen on sys.path)
  s = Svg(1024, 112)
  s.plate(chamfer(8, 8, 1016, 104, tl=14, br=18), fill='plate')
  s.tube(poly_d(chamfer(...)), 'cyan', 3)          # a LIT tube: glow + body + white-hot core
  im = s.render()                                  # RGBA, artgen.render_svg (ss=2)
  put_text(im, 'GAME TIME', cap=26, baseline=62, x=50, rgb='lav', track=0.45)

Everything is deterministic (seeded rng only), so a pack's --check can gate the bytes.
"""
import math, os, sys

import numpy as np
from PIL import Image, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import artgen  # noqa: E402

# ===================================================================================== THE SWITCH
THEME = 'fallen'          # 'fallen' (the red UI, the default since 2026-10-05) | 'synthwave' (docs/184)

# ------------------------------------------------------------------------------------- palette
# Roles, not colours: pick by what it MEANS. Every role has a value in BOTH themes; the synthwave
# column is the R3/R4/W-wave shipped value to the byte (a role added in the RT pass for a literal a
# pack used to type carries that literal there). The fallen column is MEASURED off the red-era art
# (tmp/redesign/R3|R4/base, docs/180-183; art/generated/RT-palette/_reference.png + fallen.json);
# a dark the red era never drew is the synthwave dark at the SAME luma with the red era's neutral
# cast (R ~ G, B + 7: _neutral below), so no purple survives.
_SW = {
    # --- the core roles (docs/184)
    'void':     '#07040D',   # the deepest black: backdrop vignette, wells' inner dark
    'plate':    '#0C0716',   # row cards, buttons, small plates
    'panel':    '#140C24',   # big panels' body
    'header':   '#1F1336',   # header bands, column strips
    'steel':    '#4A3A70',   # every hairline frame (UNLIT tube)
    'steel_hi': '#6E5AA0',   # the frame's top bevel / lit edge of steel
    'dead':     '#2E2448',   # a DEAD tube (locked / refused)
    'magenta':  '#FF2BD1',   # FRAME LIGHT (containers), READY / ACTIVE, headline accent words
    'cyan':     '#1FE5FF',   # FOCUS, rules, lit pips, info text
    'violet':   '#7A46FF',   # secondary frames (content cards)
    'sunset':   '#FF8A3D',   # RAMPAGE inner line only
    'amber':    '#FFB020',   # the reset / warning badge only
    'gold':     '#F5D742',   # POINTS only
    'lav':      '#B8AED8',   # secondary text (lavender-grey)
    'white':    '#F4F0FF',   # primary text tint (the glyph face is already near-white)
    'infotext': '#8FF3FF',   # light cyan for info headings (UPGRADE CARDS, column titles)
    'pad_a':    '#2BFF88',   # the ONE off-palette hue: the pad A button's identity colour
    # --- RT roles: jobs one synthwave colour did that the red era split
    'accent2':  '#1FE5FF',   # a SECOND lit colour on a framed piece (a window, a tick, a well)
    'idle_edge': '#7A46FF',  # an IDLE button / tile's bottom-edge run
    'dark_twin': '#7A46FF',  # the dark-card twins (violet row / pip)
    'dead_red': '#2E2448',   # a refused card's rule (fallen: a broken dim red light)
    'timer':    '#1FE5FF',   # a lit timer fill (its danger multiply must turn it red)
    'pap_frame': '#7A46FF',  # the Pack-a-Punch ability tile's frame
    'luck_lo':  '#1FE5FF',   # the deal panel's luck badge hue, 10..30 %
    'luck_mid': '#7A46FF',   # ... 40..60 %
    'luck_hi':  '#FF2BD1',   # ... 70..100 %
    'haze_hot': '#FF2BD1',   # backdrop corner haze (the hot pair)
    'haze_cool': '#7A46FF',  # backdrop corner haze (the cool pair)
    'grid':     '#FF2BD1',   # the backdrops' horizon grid (synthwave only)
    'window':   '#FF2BD1',   # skyline windows (the second of the two window colours)
    'ember_core': '#FFF0FF',  # the hot dot inside a themed ember
    'hot_core': '#FFE8FA',   # a lit eye / beacon tip's centre
    'spark':    '#F4FFFF',   # a sparkle's white star
    'tab_outline': '#3FC9E8',  # the round badge's ROUND tab outline (make_badge samples it)
    'ink':      '#18122C',   # dark letters on a pale keycap
    'info_glow': '#1FE5FF',  # the halo under an info heading (UPGRADE CARDS)
    'pip_hot':  '#FFFFFF',   # a lit pip's bright centre
    'glyph_ink': '#0A0614',  # the dark outline of a DRAWN glyph ('%') matching the typeface's own
    'clover':   '#FF2BD1',   # the luck plate's clover halo
    'tick':     '#1FE5FF',   # the right-edge tick of the gun / luck plates and the health frame's start
    'well_alt': '#7A46FF',   # the second well colour of the luck badges (a cyan badge's well)
    'crown':    '#FF2BD1',   # the descent gauge's crown glyph (the party's start)
    'dead_red_core': '#3E3364',  # the core of the refused card's rule
    'dead_frag': '#4A3A70',  # the refused card's broken fragment of light
    # --- RT roles: the darks the packs typed as literals (synthwave value = that literal)
    'plate_lift': '#3A2A66', 'plate_top': '#1A1030', 'row_top': '#170E2C', 'header_top': '#271A44',
    'inner': '#100A1E', 'glass': '#120A22', 'deep': '#05030A', 'token': '#0E0818',
    'focus_fill': '#180B30', 'focus_top': '#26134C', 'ready_fill': '#1A0A2A', 'ready_top': '#2A1240',
    'ramp_fill': '#120A20', 'ramp_top': '#22123A', 'badge_fill': '#110A20', 'badge_top': '#22123A',
    'local_fill': '#1C0D38', 'local_top': '#2A1452', 'row_idle_top': '#150D28',
    'socket_fill': '#0A0614', 'socket_top': '#160D28', 'ring_band': '#0E081C',
    'off_fill': '#0A0716', 'off_edge': '#5A4A86', 'pip_ring': '#5A4A86', 'dead_core': '#3E3364',
    'channel_top': '#030207', 'channel_lo': '#0B0716', 'pocket': '#08050F', 'track_mid': '#0A0614',
    'locked_fill': '#0A0A16', 'locked_top': '#13152A', 'locked_band': '#1C1A30', 'locked_band2': '#141426',
    'locked_well': '#0E0A1A', 'title_top': '#1E1438', 'banner_top': '#2C1C52',
    'lockin_fill': '#0F1830', 'lockin_top': '#182A48', 'tier_fill': '#120B1C', 'tier_top': '#22142E',
    'port_well': '#120B22',
    'skull_hi': '#3A2466', 'fang_hi': '#D8CEF4', 'fang_lo': '#C4B8E6',
    'card_a': '#BDB2E2', 'card_b': '#D6CCF2', 'card_c': '#F0EAFF',
    'pad_well': '#2A1A48', 'dpad_hi': '#2A1C48', 'dpad_lo': '#0E0A1C', 'dpad_lit_hi': '#9FF6FF', 'dpad_lit_lo': '#13A9C9',
    'key_lip_lo': '#2E2350', 'key_face_hi': '#FCFAFF', 'key_face_mid': '#EAE3FA', 'key_face_lo': '#D6CCF0',
    'timer_lo': '#BFF8FF', 'timer_hot': '#F6FEFF', 'timer_mid': '#E2FBFF', 'timer_edge': '#36D8F5',
    'seg_glow': '#7FEBFF', 'seg_a': '#E8FDFF', 'seg_hot': '#FFFFFF', 'seg_c': '#E2FBFF', 'seg_d': '#B4F3FF', 'seg_rim': '#A6F2FF',
    'you_hi': '#FFD9F6', 'you_mid': '#FF7BE3', 'down_rim': '#FF6FE0', 'down_core': '#FFE0FA',
    # r10 card chrome
    'card_glass_hi': '#171029', 'card_glass_mid': '#100A1D', 'card_glass_lo': '#0A0613', 'card_socket': '#120B20',
    'card_slot_lo': '#0B0714', 'bezel_hi': '#1B1330', 'bezel_mid': '#140E24', 'bezel_lo': '#0D0918',
    # pk09 GAME OVER banner
    'go_outline': '#10081E', 'go_bevel': '#801276', 'go_fill_top': '#FFD6F6', 'go_stair_hi': '#180E2C',
    'go_stair_lo': '#22143E', 'go_scan': '#2C1E4C', 'go_shard': '#1E1236', 'go_plate_top': '#21153C',
    'go_plate_scan': '#2E2052', 'go_sheen': '#5A3C96', 'go_core': '#FFE8FA', 'go_info_core': '#E2FCFF',
    'go_fringe': '#1FE5FF', 'go_bloom': '#7A46FF', 'go_spark': '#1FE5FF', 'go_spark_core': '#E2FCFF',
    'go_crack_shadow': '#040208', 'go_seam': '#221A3A', 'go_ends': '#140E22',
    # --- RT review round (2026-10-05): jobs the first pass left on a shared role
    'hrule':    '#1FE5FF',   # a header band's bottom rule (fallen: an unlit steel line, as the red era drew it)
    'skull_line': '#7A46FF', # the hologram skull's contour (fallen: dim steel, so its red eyes carry it)
    'toast_edge': '#FF2BD1', # the power-up toast's edge light (fallen: GOLD, docs/182 table E)
    'pip_hot_twin': '#FFFFFF',  # a lit DARK-TWIN pip's centre (fallen: a pale violet, never the red pip's pink)
    'luck_lo_ink': '#1FE5FF', 'luck_mid_ink': '#7A46FF', 'luck_hi_ink': '#FF2BD1',  # the luck badge's number
    # the power-up tokens' hues. Synthwave = the id_* hue each shipped with. Fallen = the red library's own
    # content colours (bone, blood, brass, wood, the HUD's PaP gold, ice, the red era's violet)
    'pu_insta': '#FF2BD1', 'pu_blood': '#FF2BD1', 'pu_ammo': '#1FE5FF', 'pu_carpenter': '#1FE5FF',
    'pu_pap': '#7A46FF', 'pu_timewarp': '#7A46FF', 'pu_gift': '#7A46FF',
    'title_shadow': '#3A3F4C',  # the pause titles' hard offset extrusion (drawn by the fallen theme only)
    'ramp_word': '#FF84E4',  # the round badge's RAMPAGE face (synthwave = neon_word's: magenta 0.42 toward white)
    'pu_insta_eye': '#FF2BD1',  # Insta-Kill's slit eyes (synthwave = the token's own hue)
}
_SW_CORE = {'magenta': '#FFD9F6', 'cyan': '#E8FDFF', 'violet': '#E4D8FF', 'sunset': '#FFE6CF',
            'amber': '#FFF0C8', 'gold': '#FFF6CC', 'steel': '#7E6CB0', 'pad_a': '#E2FFEE',
            'dead': '#3C3060',
            # the RT roles keep the core of the colour they stood for
            'accent2': '#E8FDFF', 'idle_edge': '#E4D8FF', 'dark_twin': '#E4D8FF', 'dead_red': '#3C3060',
            'timer': '#E8FDFF', 'pap_frame': '#E4D8FF', 'luck_lo': '#E8FDFF', 'luck_mid': '#E4D8FF',
            'luck_hi': '#FFD9F6', 'tick': '#E8FDFF', 'well_alt': '#E4D8FF', 'clover': '#FFD9F6',
            'hrule': '#E8FDFF', 'skull_line': '#E4D8FF', 'toast_edge': '#FFD9F6',
            'pu_insta': '#FFD9F6', 'pu_blood': '#FFD9F6', 'pu_ammo': '#E8FDFF', 'pu_carpenter': '#E8FDFF',
            'pu_pap': '#E4D8FF', 'pu_timewarp': '#E4D8FF', 'pu_gift': '#E4D8FF'}

# THE FALLEN COLUMN. Measured values (evidence: art/generated/RT-palette/fallen.json); every dark not
# listed is _neutral(synthwave value).
_FA_SET = {
    'void': '#07060A', 'plate': '#0F0E15', 'panel': '#121119', 'header': '#1C1B26',
    'steel': '#6B7589', 'steel_hi': '#8A93A8', 'dead': '#575F75',
    'magenta': '#F2203A', 'cyan': '#F2203A', 'violet': '#94A1BA', 'sunset': '#A02232',
    'amber': '#FFB020', 'gold': '#F5D742', 'lav': '#A0A8BF', 'white': '#F0F3FA', 'infotext': '#9DD0FF',
    'pad_a': '#2BFF88',
    'accent2': '#8A93A8', 'idle_edge': '#86D4FC', 'dark_twin': '#B45CFF', 'dead_red': '#7A1422',
    'timer': '#9DD0FF', 'pap_frame': '#F2D84A',
    # the luck badge steps up in LIGHT, in the one accent: unlit steel 10..30, a dim red line 40..60, full red 70..100
    'luck_lo': '#8A93A8', 'luck_mid': '#B21A30', 'luck_hi': '#F2203A',
    'luck_lo_ink': '#F0F3FA', 'luck_mid_ink': '#F2203A', 'luck_hi_ink': '#F2203A',
    'haze_hot': '#C21C40', 'haze_cool': '#4A1A5C', 'grid': '#F2203A', 'window': '#F2203A',
    'hrule': '#6B7589', 'skull_line': '#6B7589', 'toast_edge': '#F5D742', 'pip_hot_twin': '#D9C6FF',
    'pu_insta': '#D6D9E2', 'pu_blood': '#E0283C', 'pu_ammo': '#E8B33A', 'pu_carpenter': '#E08A3A',
    'pu_pap': '#F2D84A', 'pu_timewarp': '#9DD0FF', 'pu_gift': '#B45CFF', 'title_shadow': '#3A3F4C',
    'ramp_word': '#FF8292', 'pu_insta_eye': '#F2203A',
    'ember_core': '#FF8E9E', 'hot_core': '#FFB3BE', 'spark': '#FFE3E7', 'tab_outline': '#D4DAE8',
    'ink': '#101016', 'info_glow': '#4A90E7', 'pip_hot': '#F26A7B',
    'clover': '#A9B1C3', 'tick': '#F2203A', 'well_alt': '#8A93A8', 'crown': '#F0C040',
    'dead_red_core': '#9C3144', 'dead_frag': '#9C3144',
    'plate_lift': '#2B2A31', 'plate_top': '#191A24', 'row_top': '#16151D', 'header_top': '#22212D',
    'glass': '#121119', 'deep': '#050409',
    'focus_fill': '#22070E', 'focus_top': '#2C0912', 'ready_fill': '#22060E', 'ready_top': '#3A0B14',
    'ramp_fill': '#1A0A10', 'ramp_top': '#2E0710', 'local_fill': '#22070E', 'local_top': '#2C0912',
    'off_fill': '#0B0A11', 'off_edge': '#6A7288', 'pip_ring': '#818A9E', 'dead_core': '#5E667B',
    'locked_fill': '#0B0D13', 'locked_top': '#14161E', 'locked_band': '#1A1C25', 'locked_band2': '#12141B',
    'locked_well': '#0B0D13', 'lockin_fill': '#22070E', 'lockin_top': '#2C0912',
    'skull_hi': '#2E2D36', 'fang_hi': '#D6D9E2', 'fang_lo': '#B9BDC8',
    'card_a': '#B4B9C6', 'card_b': '#CFD3DC', 'card_c': '#EDF0F5',
    'pad_well': '#24232C', 'dpad_hi': '#25242D', 'dpad_lo': '#0D0D13', 'dpad_lit_hi': '#FF8E9E', 'dpad_lit_lo': '#B0182E',
    'key_lip_lo': '#3A3E4A', 'key_face_hi': '#EBEFF7', 'key_face_mid': '#E0E5EF', 'key_face_lo': '#D3DAE7',
    'timer_lo': '#C9E5FF', 'timer_hot': '#F6FAFF', 'timer_mid': '#E3F0FF', 'timer_edge': '#6FB4F2',
    'seg_glow': '#FFB020', 'seg_a': '#FFDA62', 'seg_hot': '#FFE88E', 'seg_c': '#FFD24E', 'seg_d': '#FFC838', 'seg_rim': '#F8C030',
    'you_hi': '#FF8E9E', 'you_mid': '#F84A62', 'down_rim': '#F84A62', 'down_core': '#FF9AA8',
    'go_outline': '#0D0C12', 'go_bevel': '#7A1422', 'go_fill_top': '#FF8E9E', 'go_core': '#FF9AAA',
    'go_info_core': '#B9C0CF', 'go_fringe': '#7A1422', 'go_bloom': '#6A1222', 'go_spark': '#FF5C76',
    'go_spark_core': '#FFB3BE',
}
_FA_CORE = {'magenta': '#FF8E9E', 'cyan': '#FF8E9E', 'violet': '#AEB8CC', 'sunset': '#B83446',
            'amber': '#FFF0C8', 'gold': '#FFF6CC', 'steel': '#8A93A8', 'pad_a': '#E2FFEE', 'dead': '#5E667B',
            'accent2': '#A9B1C3', 'idle_edge': '#A8E2FF', 'dark_twin': '#D2B4FF', 'dead_red': '#9C3144',
            'timer': '#E3F0FF', 'pap_frame': '#FFF3B8', 'luck_lo': '#A9B1C3', 'luck_mid': '#E2606F',
            'luck_hi': '#FF8E9E', 'tick': '#FF8E9E', 'well_alt': '#A9B1C3', 'clover': '#C8CEDB',
            'hrule': '#7A8398', 'skull_line': '#8A93A8', 'toast_edge': '#FFF6CC',
            'pu_insta': '#F4F6FA', 'pu_blood': '#FF9AA6', 'pu_ammo': '#FFE7A8', 'pu_carpenter': '#FFD2A6',
            'pu_pap': '#FFF3B8', 'pu_timewarp': '#E3F0FF', 'pu_gift': '#E4C8FF'}


# IDENTITY roles: content hues that must NOT follow the theme (a power-up's colour is the power-up), named so a
# pack can still say what they are. Same value + same core in every theme.
_ID = {'id_magenta': '#FF2BD1', 'id_cyan': '#1FE5FF', 'id_violet': '#7A46FF', 'id_sunset': '#FF8A3D',
       'id_gold': '#F5D742'}
_ID_CORE = {'id_magenta': '#FFD9F6', 'id_cyan': '#E8FDFF', 'id_violet': '#E4D8FF', 'id_sunset': '#FFE6CF',
            'id_gold': '#FFF6CC'}


def _neutral(c):
    """A synthwave dark at the same luma with the red era's neutral cast (#121119: R ~ G, B + 7)."""
    c = c.lstrip('#')
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b
    x = int(round(L + 0.2))
    return '#%02X%02X%02X' % (max(0, min(255, x)), max(0, min(255, x - 1)), max(0, min(255, x + 7)))


THEMES = {
    'synthwave': dict(PAL=dict(_SW, **_ID), CORE=dict(_SW_CORE, **_ID_CORE), LOOK=dict(
        word_face=0.42,        # a headline accent word: the glyph face mixed this far toward white
        word_glow_k=1.0,       # ... and its halo's strength
        wash_k=1.0,            # the inner light wash of a FOCUSED / READY plate: opacity multiplier
        twin_wash=1.0,         # the dark-card twins' violet body wash: opacity multiplier
        scratch_k=1.0,         # role-coloured scratches: opacity multiplier
        glow_k={}, glow_cap={},  # per-ROLE tube glow multiplier / ceiling
        embers=('magenta', 'violet', 'cyan'),
        grid=True,             # the backdrops' horizon grid
        skyline_lit=True,      # lit roofline tubes + windows in the panels' skyline
        splatter=False,        # the red era's blood splatter in panel corners
        sparkles=True,         # glints on LOCKED IN / luck 100
        hud_alpha_k=1.0,       # HUD V2 plates' opacity multiplier (r4 layered(hud=True))
        panel_runs=False,      # big panels: the frame light runs the WHOLE outline (fallen: steel + the red era's lit sides)
        title_glow=True,       # the pause titles' halo (fallen: crisp white over a hard dark offset)
        bd_embers=None,        # the pause / scoreboard backdrop embers (n per box, colours, size, alpha); None = the R3 set
        ember_glow=False,      # embers' halos blurred PREMULTIPLIED (a light, not a dark dot with a lit heart)
        haze_k=1.0,            # the backdrops' corner haze strength
        fringe=True)),         # the GAME OVER title's chromatic fringe
    'fallen': dict(PAL=dict({r: _FA_SET.get(r, _neutral(v)) for r, v in _SW.items()}, **_ID),
                   CORE=dict(_FA_CORE, **_ID_CORE), LOOK=dict(
        word_face=0.06, word_glow_k=0.8, scratch_k=2.6, wash_k=0.8, twin_wash=0.35,
        # the red light is a tight bright line, not a white-hot neon tube (look_notes 4): red <= 0.9,
        # steel secondaries <= 0.3, the second lit colour unlit (a bright steel line, no halo)
        glow_k={}, glow_cap={'magenta': 0.9, 'cyan': 0.9, 'tick': 0.9, 'violet': 0.3, 'accent2': 0.0, 'well_alt': 0.0,
                             'idle_edge': 0.45,
                             'pap_frame': 0.6, 'luck_lo': 0.0, 'luck_mid': 0.45, 'dead_red': 0.25,
                             'hrule': 0.0, 'skull_line': 0.2},
        embers=('magenta', 'dead_red', 'magenta'),
        grid=False, skyline_lit=False, splatter=True, sparkles=False, fringe=False,
        # the red era's HUD plates were ~85 % opaque (docs/182 s3; measured alpha 217): 0.92 x the R4 0.92 alphas
        hud_alpha_k=0.92, panel_runs=True, title_glow=False, ember_glow=True, haze_k=1.45,
        # the red era's backdrop embers: ~100 glowing red specks in the outer ring (measured median 23-28 px)
        bd_embers=(25, ('magenta', 'magenta', 'sunset'), (1.6, 4.2), (150, 245)))),
}
if THEME not in THEMES:
    raise SystemExit('synthwave.py: THEME %r is not one of %s' % (THEME, sorted(THEMES)))
FALLEN = THEME == 'fallen'
PAL = THEMES[THEME]['PAL']
# the hot CORE of each tube colour (a glass tube is brightest down its middle)
CORE = THEMES[THEME]['CORE']
LOOK = THEMES[THEME]['LOOK']


def themed_colours(theme):
    """{role: hex} of a theme (review sheets compare the two)."""
    return dict(THEMES[theme]['PAL'])


def hexrgb(c):
    c = PAL.get(c, c)
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def hexs(c):
    return '#%02X%02X%02X' % hexrgb(c)


def mix(a, b, t):
    a, b = hexrgb(a), hexrgb(b)
    return '#%02X%02X%02X' % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

# ------------------------------------------------------------------------------------ geometry

def chamfer(x0, y0, x1, y1, tl=0, tr=0, br=0, bl=0):
    """A rectangle with 45-degree cut corners (the frame grammar's only corner)."""
    p = []
    p += [(x0, y0 + tl), (x0 + tl, y0)] if tl else [(x0, y0)]
    p += [(x1 - tr, y0), (x1, y0 + tr)] if tr else [(x1, y0)]
    p += [(x1, y1 - br), (x1 - br, y1)] if br else [(x1, y1)]
    p += [(x0 + bl, y1), (x0, y1 - bl)] if bl else [(x0, y1)]
    return p


def poly_d(pts, close=True):
    d = 'M%.2f,%.2f ' % pts[0] + ' '.join('L%.2f,%.2f' % p for p in pts[1:])
    return d + (' Z' if close else '')


def line_d(*pts):
    return poly_d(list(pts), close=False)


def inset(pts, k):
    """Offset a CONVEX polygon (clockwise in screen space) inward by k: each edge moves k
    along its inward normal and adjacent edges are re-intersected."""
    n = len(pts)
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L          # inward for a clockwise (y-down) polygon
        lines.append(((x0 + nx * k, y0 + ny * k), (dx, dy)))
    out = []
    for i in range(n):
        (p, d), (q, e) = lines[i - 1], lines[i]
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-9:
            out.append(q)
            continue
        t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
        out.append((p[0] + d[0] * t, p[1] + d[1] * t))
    return out

def d_box(d, pad=0.0):
    """Bounding box of every coordinate in an SVG path string (control points included - a
    superset, which is all a filter region needs)."""
    import re
    v = [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', d)]
    xs, ys = v[0::2], v[1::2]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)

# ----------------------------------------------------------------------------------------- svg

class Svg:
    """Accumulates an SVG body + defs (blur filters, gradients) with stable ids."""

    _seq = 0

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.defs, self.body, self._ids = [], [], {}
        Svg._seq += 1
        self.pre = 's%d_' % Svg._seq      # ids unique across Svg objects (bodies may be merged)

    def _id(self, key, make):
        if key not in self._ids:
            self._ids[key] = '%sd%d' % (self.pre, len(self._ids))
            self.defs.append(make(self._ids[key]))
        return self._ids[key]

    def blur(self, sigma, box=None):
        """A Gaussian blur in USER SPACE (a thin line's bbox has no height, so the default 10%
        objectBoundingBox region would clip its glow to nothing). box = (x0, y0, x1, y1) of the
        blurred shape: the region is that box + 3.2 sigma, which keeps big canvases fast (a
        whole-canvas region per tube cost minutes on the 1468 x 1196 panel). None = whole canvas."""
        sigma = round(sigma, 2)
        if box is None:
            reg = (-50, -50, self.w + 100, self.h + 100)
        else:
            m = sigma * 3.2 + 2
            x0, y0 = max(-50, int(math.floor(box[0] - m))), max(-50, int(math.floor(box[1] - m)))
            x1, y1 = min(self.w + 50, int(math.ceil(box[2] + m))), min(self.h + 50, int(math.ceil(box[3] + m)))
            reg = (x0, y0, max(1, x1 - x0), max(1, y1 - y0))
        return self._id(('blur', sigma, reg), lambda i: (
            '<filter id="%s" filterUnits="userSpaceOnUse" x="%d" y="%d" width="%d" height="%d">'
            '<feGaussianBlur stdDeviation="%.2f"/></filter>' % ((i,) + reg + (sigma,))))

    def lin(self, stops, x1=0, y1=0, x2=0, y2=1, user=False):
        """stops = [(offset 0..1, colour, opacity)]. Default: top -> bottom of the shape."""
        key = ('lin', tuple(stops), x1, y1, x2, y2, user)
        units = ' gradientUnits="userSpaceOnUse"' if user else ''

        def make(i):
            s = ''.join('<stop offset="%.3f" stop-color="%s" stop-opacity="%.3f"/>' % (o, hexs(c), a) for o, c, a in stops)
            return '<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s"%s>%s</linearGradient>' % (i, x1, y1, x2, y2, units, s)
        return self._id(key, make)

    def rad(self, stops, cx=0.5, cy=0.5, r=0.5, user=False):
        key = ('rad', tuple(stops), cx, cy, r, user)
        units = ' gradientUnits="userSpaceOnUse"' if user else ''

        def make(i):
            s = ''.join('<stop offset="%.3f" stop-color="%s" stop-opacity="%.3f"/>' % (o, hexs(c), a) for o, c, a in stops)
            return '<radialGradient id="%s" cx="%s" cy="%s" r="%s"%s>%s</radialGradient>' % (i, cx, cy, r, units, s)
        return self._id(key, make)

    def add(self, s):
        self.body.append(s)

    # -- primitives ---------------------------------------------------------------------------
    def path(self, d, fill='none', stroke='none', sw=0, opacity=1.0, filt=None, join='miter', cap='butt', extra=''):
        f = fill if (fill == 'none' or fill.startswith('url(')) else hexs(fill)
        s = stroke if (stroke == 'none' or stroke.startswith('url(')) else hexs(stroke)
        fl = ' filter="url(#%s)"' % filt if filt else ''
        self.add('<path d="%s" fill="%s" stroke="%s" stroke-width="%.2f" opacity="%.3f" '
                 'stroke-linejoin="%s" stroke-linecap="%s"%s %s/>' % (d, f, s, sw, opacity, join, cap, fl, extra))

    def rect(self, x, y, w, h, fill, opacity=1.0, filt=None):
        self.path(poly_d([(x, y), (x + w, y), (x + w, y + h), (x, y + h)]), fill=fill, opacity=opacity, filt=filt)

    def circle(self, cx, cy, r, fill='none', stroke='none', sw=0, opacity=1.0, filt=None):
        f = fill if (fill == 'none' or fill.startswith('url(')) else hexs(fill)
        s = stroke if (stroke == 'none' or stroke.startswith('url(')) else hexs(stroke)
        fl = ' filter="url(#%s)"' % filt if filt else ''
        self.add('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" stroke-width="%.2f" opacity="%.3f"%s/>'
                 % (cx, cy, r, f, s, sw, opacity, fl))

    # -- the frame grammar --------------------------------------------------------------------
    def plate(self, pts, fill='plate', top=None, sheen=0.05):
        """Dark glass: a vertical gradient (a touch lighter at the top) + a faint top sheen."""
        top = top or mix(fill, 'plate_lift', 0.18)
        g = self.lin([(0, top, 1), (0.55, fill, 1), (1, mix(fill, '#000000', 0.25), 1)])
        d = poly_d(pts)
        self.path(d, fill='url(#%s)' % g)
        if sheen:
            ys = [p[1] for p in pts]
            y0, y1 = min(ys), max(ys)
            sh = self.lin([(0, '#FFFFFF', sheen), (0.22, '#FFFFFF', 0), (1, '#FFFFFF', 0)],
                          0, y0, 0, y1, user=True)
            self.path(d, fill='url(#%s)' % sh)

    def steel(self, pts, w=2.0, color='steel', opacity=1.0, close=True):
        """The UNLIT hairline every frame carries."""
        self.path(poly_d(pts, close), stroke=color, sw=w, opacity=opacity)

    def tube(self, d, color, w=3.0, glow=1.0, core=True, spread=1.0):
        """A LIT neon tube: wide soft glow, tight glow, the coloured glass, a white-hot core.
        glow scales the halo's strength; spread scales its reach. A ROLE colour's halo also obeys the
        theme (LOOK glow_k / glow_cap: the fallen red is a tight line, its steel secondaries all but
        unlit); a literal hex (a class / rarity / perk hue) is drawn as asked."""
        if isinstance(color, str) and not color.startswith('#'):
            glow = glow * LOOK['glow_k'].get(color, 1.0)
            if color in LOOK['glow_cap']:
                glow = min(glow, LOOK['glow_cap'][color])
        c = hexs(color)
        if glow > 0:
            bx = d_box(d, w * 2.0 * spread)
            self.path(d, stroke=c, sw=w * 4.0 * spread, opacity=0.30 * glow, filt=self.blur(w * 2.6 * spread, bx), join='round', cap='round')
            self.path(d, stroke=c, sw=w * 1.8, opacity=0.65 * glow, filt=self.blur(w * 0.9, bx), join='round', cap='round')
        self.path(d, stroke=c, sw=w, join='miter', cap='butt')
        if core:
            self.path(d, stroke=CORE.get(color, mix(color, '#FFFFFF', 0.8)), sw=max(0.8, w * 0.36), opacity=0.95, join='miter')

    def dead_tube(self, d, w=2.0, color='dead', core='dead_core'):
        """A DEAD tube: unlit glass, no glow (locked / refused / idle-off). color / core: a role pair
        (the refused card's rule is 'dead_red' / 'dead_red_core': a broken dim red light in the fallen theme)."""
        self.path(d, stroke=color, sw=w)
        self.path(d, stroke=core, sw=max(0.6, w * 0.3), opacity=0.8)

    def glow_fill(self, pts, color, opacity=0.25, sigma=10):
        """A soft wash of light inside (or around) a shape."""
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        self.path(poly_d(pts), fill=color, opacity=opacity, filt=self.blur(sigma, (min(xs), min(ys), max(xs), max(ys))))

    def bracket(self, x, y, dx, dy, length, color, w=2.0, glow=0.6):
        """A corner bracket: an L of neon at (x, y) opening toward (dx, dy) (+-1)."""
        self.tube(line_d((x + dx * length, y), (x, y), (x, y + dy * length)), color, w, glow=glow)

    def chevron(self, cx, cy, h, color, w=3.0, glow=0.0, double=False, pointing=1):
        """A '>' chevron (pointing=-1 for '<'); double draws '>>'."""
        hw = h * 0.42 * pointing
        xs = [cx - hw * 0.5] + ([cx - hw * 0.5 + h * 0.42 * pointing] if double else [])
        for x in xs:
            d = line_d((x - hw * 0.5, cy - h / 2), (x + hw * 0.5, cy), (x - hw * 0.5, cy + h / 2))
            if glow:
                self.tube(d, color, w, glow=glow)
            else:
                self.path(d, stroke=color, sw=w, join='miter')

    def slashes(self, x, base, h, n, color, w=3.0, gap=None, glow=0.8, lean=0.42):
        """Neon slashes ('//' '///') as thin cyan tube strokes - our typeface's '/' is a
        digit glyph, and the theme draws every rule-slash as a neon line."""
        gap = gap if gap is not None else h * 0.32
        x0 = x
        for i in range(n):
            d = line_d((x0 + h * lean, base - h), (x0, base))
            self.tube(d, color, w, glow=glow)
            x0 += gap
        return x0 + h * lean

    def render(self, ss=2):
        svg = artgen.svg_doc(self.w, self.h, ''.join(self.body), ''.join(self.defs))
        return artgen.render_svg(svg, self.w, self.h, ss=ss)

# ---------------------------------------------------------------------------------- typography

def _rgb(c):
    return hexrgb(c) if isinstance(c, str) else tuple(c)


def text_img(text, cap, rgb='white', track=0.0, ss=4):
    """Set `text` in the map's typeface (artgen's glyph cells, TodGlyphRow's metrics), cap height
    `cap` px, with EXTRA tracking `track` (fraction of cap, added to the face's own 0.055).
    Returns (RGBA image, pen0_x, baseline_y, advance_width) - pen0/baseline are positions inside
    the returned image of the pen start and the baseline."""
    M = artgen.metrics()
    rgb = _rgb(rgb)
    items, pen, first = [], 0.0, True
    for c in text:
        if c == ' ':
            pen += M['letters']['cw'] * (cap / M['letters']['cap']) * artgen.TOD_SPACE_ADV + cap * track * 0.5
            first = False
            continue
        sname, key, name = artgen._glyph(c)
        S = M[sname]
        s = cap / S['cap']
        adv, gx = S['g'][key]
        if not first:
            pen += cap * (artgen.TOD_TRACK + track)
        items.append((name, pen - gx * s, S, s))
        pen += adv * s
        first = False
    if not items:
        return Image.new('RGBA', (4, 4), (0, 0, 0, 0)), 0, 0, pen
    asc = max(S['baseline'] * s for _, _, S, s in items)
    desc = max((S['ch'] - S['baseline']) * s for _, _, S, s in items)
    left = min(l for _, l, _, _ in items)
    right = max(l + S['cw'] * s for _, l, S, s in items)
    pad = 2
    W = int(math.ceil(right - left)) + pad * 2
    H = int(math.ceil(asc + desc)) + pad * 2
    ox, base = -left + pad, asc + pad
    layer = Image.new('RGBA', (W * ss, H * ss), (0, 0, 0, 0))
    for name, l, S, s in items:
        w, h = S['cw'] * s * ss, S['ch'] * s * ss
        im = artgen._cell(name).resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
        r, g, b, a = im.split()
        r = r.point(lambda v, k=rgb[0]: v * k // 255)
        g = g.point(lambda v, k=rgb[1]: v * k // 255)
        b = b.point(lambda v, k=rgb[2]: v * k // 255)
        layer.alpha_composite(Image.merge('RGBA', (r, g, b, a)),
                              (int(round((l + ox) * ss)), int(round((base - S['baseline'] * s) * ss))))
    return layer.resize((W, H), Image.LANCZOS), ox, base, pen


def text_width(text, cap, track=0.0):
    return text_img(text, cap, track=track)[3]


def glow_of(img, color, radius, strength=1.0, spread=0):
    """A coloured halo from an image's alpha (for neon words and badges)."""
    a = img.split()[3]
    if spread:
        a = a.filter(ImageFilter.MaxFilter(spread * 2 + 1))
    a = a.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        a = a.point(lambda v: min(255, int(v * strength)))
    c = hexrgb(color)
    return Image.merge('RGBA', (Image.new('L', img.size, c[0]), Image.new('L', img.size, c[1]),
                                Image.new('L', img.size, c[2]), a))


def put_text(canvas, text, cap, baseline, rgb='white', x=None, cx=None, right=None, track=0.0,
             glow=None, glow_r=None, glow_k=1.0, oblique=0.0, fit=None, opacity=1.0):
    """Composite `text` onto RGBA `canvas`. Anchor: x (left), cx (centre) or right (right edge of
    the advance), baseline y. glow = a palette colour for a neon halo. oblique = shear (0.18 reads
    as the target's italic). fit = shrink the cap until the advance fits. Returns (x0, x1) of the
    advance on the canvas and the cap used."""
    if fit is not None:
        while cap > 6 and text_width(text, cap, track) > fit:
            cap -= 0.25
    img, ox, base, adv = text_img(text, cap, rgb, track)
    if oblique:
        # lean right (oblique > 0): x_src = x_dst + oblique * (y - base), so a glyph's top moves
        # right by oblique * (base - y) and its descender left; pad both sides accordingly.
        H = img.height
        lpad = int(math.ceil(oblique * (H - base))) + 1
        rpad = int(math.ceil(oblique * base)) + 1
        wide = Image.new('RGBA', (img.width + lpad + rpad, H), (0, 0, 0, 0))
        wide.alpha_composite(img, (lpad, 0))
        img = wide.transform(wide.size, Image.AFFINE, (1, oblique, -oblique * base, 0, 1, 0), resample=Image.BICUBIC)
        ox += lpad
    if opacity < 1.0:
        a = img.split()[3].point(lambda v: int(v * opacity))
        img.putalpha(a)
    if cx is not None:
        pen0 = cx - adv / 2.0
    elif right is not None:
        pen0 = right - adv
    else:
        pen0 = x
    px, py = int(round(pen0 - ox)), int(round(baseline - base))
    if glow:
        gr = glow_r if glow_r is not None else max(2.0, cap * 0.22)
        pad = int(gr * 3)
        big = Image.new('RGBA', (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
        big.alpha_composite(img, (pad, pad))
        halo = glow_of(big, glow, gr, 1.6 * glow_k)
        _paste(canvas, halo, px - pad, py - pad)
        halo2 = glow_of(big, glow, gr * 0.35, 1.2 * glow_k)
        _paste(canvas, halo2, px - pad, py - pad)
    _paste(canvas, img, px, py)
    return (pen0, pen0 + adv), cap


def _paste(canvas, img, x, y):
    """alpha_composite that tolerates negative / overhanging offsets."""
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(canvas.width, x + img.width), min(canvas.height, y + img.height)
    if x1 <= x0 or y1 <= y0:
        return
    crop = img.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    canvas.alpha_composite(crop, (x0, y0))


def neon_word(canvas, text, cap, baseline, color='magenta', **kw):
    """A headline word in NEON: the glyph face tinted to the tube's hot core, a glow of the tube
    colour under it (the style's 'UPGRADES' treatment). The theme sets how hot the face is (LOOK
    word_face: synthwave mixes it 0.42 toward white; the fallen word is SOLID red, the red era's
    #F11F39 face, its halo a little softer) - the same glyph cells either way."""
    face = mix(color, '#FFFFFF', LOOK['word_face'])
    return put_text(canvas, text, cap, baseline, rgb=face, glow=color, glow_r=kw.pop('glow_r', cap * 0.2),
                    glow_k=kw.pop('glow_k', 1.0) * LOOK['word_glow_k'], **kw)

# ------------------------------------------------------------------------------------ textures

def grain(img, amp=0.035, seed=1, mask=None):
    """A faint luminance grain over the opaque pixels (glass is never perfectly flat)."""
    a = np.asarray(img).astype(np.float32)
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, a.shape[:2]).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32)
    n = (n - 128) / 40.0
    k = 1.0 + amp * n
    if mask is not None:
        m = np.asarray(mask).astype(np.float32) / 255.0
        k = 1.0 + (k - 1.0) * m
    a[:, :, :3] = (a[:, :, :3] * k[:, :, None]).clip(0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def scratches(s, box, n, seed, color='lav', opacity=0.05, length=(30, 120)):
    """Faint seeded hairline scratches inside box=(x0, y0, x1, y1), drawn into Svg s. Role-coloured
    scratches are theme chrome: the fallen steel is visibly scratched (LOOK scratch_k)."""
    if isinstance(color, str) and not color.startswith('#'):
        opacity = opacity * LOOK['scratch_k']
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        a = rng.uniform(-0.6, 0.6) + (math.pi * 0.5 if rng.random() < 0.3 else 0)
        L = rng.uniform(*length)
        s.path(line_d((x, y), (x + math.cos(a) * L, y + math.sin(a) * L)), stroke=color, sw=1.0,
               opacity=opacity * rng.uniform(0.5, 1.0))


def embers(img, box, n, seed, colors=None, size=(1.0, 3.2), alpha=(60, 200)):
    """Seeded glowing specks (the red set's ember spray; synthwave's neon cousin). colors=None takes the
    theme's (LOOK embers). Role-coloured embers get the theme's hot dot (ember_core: never white-hot in
    the fallen red); literal-hex embers (a rarity's gold) keep the original pale core."""
    colors = colors if colors is not None else LOOK['embers']
    themed = all(isinstance(c, str) and not c.startswith('#') for c in colors)
    core_rgb = hexrgb('ember_core') if themed else (255, 240, 255)
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    px = layer.load()
    pts = []
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(*size)
        c = hexrgb(colors[int(rng.integers(0, len(colors)))])
        a = int(rng.uniform(*alpha))
        pts.append((x, y, r, c, a))
    from PIL import ImageDraw
    d = ImageDraw.Draw(layer)
    for x, y, r, c, a in pts:
        d.ellipse((x - r, y - r, x + r, y + r), fill=c + (a,))
    if LOOK['ember_glow'] and themed:          # theme embers only: a literal-hex ember (a rarity's gold) is content
        halo, wide = _blur_premul(layer, 3.5), _blur_premul(layer, 9)
    else:
        halo = layer.filter(ImageFilter.GaussianBlur(3.5))
        wide = layer.filter(ImageFilter.GaussianBlur(9))
    out = img.copy()
    out.alpha_composite(wide)
    out.alpha_composite(halo)
    out.alpha_composite(halo)
    core = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(core)
    for x, y, r, c, a in pts:
        rr = max(0.6, r * 0.45)
        d2.ellipse((x - rr, y - rr, x + rr, y + rr), fill=core_rgb + (min(255, a + 40),))
    out.alpha_composite(core.filter(ImageFilter.GaussianBlur(0.5)))
    return out


def _blur_premul(layer, r):
    """A Gaussian blur of an RGBA layer on PREMULTIPLIED colour: the halo keeps the light's own colour instead of
    fading through the transparent pixels' black (PIL blurs each channel on its own)."""
    a = np.asarray(layer).astype(np.float32)
    al = a[..., 3:4] / 255.0
    pm = np.concatenate([a[..., :3] * al, a[..., 3:4]], -1)
    chans = [np.asarray(Image.fromarray(np.clip(pm[..., i], 0, 255).astype(np.uint8), 'L').filter(ImageFilter.GaussianBlur(r)),
                        np.float32) for i in range(4)]
    A = chans[3]
    rgb = np.stack([np.where(A > 0, chans[i] * 255.0 / np.maximum(A, 1e-6), 0.0) for i in range(3)], -1)
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), A]).astype(np.uint8), 'RGBA')


def splatter(img, box, n, seed, alpha=(110, 225)):
    """The red era's SPLATTER (docs/180: "sparse red splatter in one or two corners"): seeded dark-red
    paint specks, no glow - a main drop with a few satellites, coloured between dead_red and a lit red.
    Fallen chrome draws it where synthwave scattered glowing embers (LOOK splatter)."""
    from PIL import ImageDraw
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    ss = 4
    layer = Image.new('RGBA', (img.width * ss, img.height * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lo, hi = np.array(hexrgb('dead_red'), float), np.array(hexrgb('magenta'), float)
    # one impact point in the box, the drops falling off it (sigma a third of the box), the biggest nearest it
    cx, cy = rng.uniform(x0 + (x1 - x0) * 0.25, x1 - (x1 - x0) * 0.25), rng.uniform(y0 + (y1 - y0) * 0.25, y1 - (y1 - y0) * 0.25)
    sx, sy = (x1 - x0) / 3.2, (y1 - y0) / 3.2
    for _ in range(n * 5):
        x, y = float(rng.normal(cx, sx)), float(rng.normal(cy, sy))
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            continue            # a drop outside the box is not drawn (clamping it stacked drops along the box's edge)
        near = math.exp(-(((x - cx) / (sx * 1.2)) ** 2 + ((y - cy) / (sy * 1.2)) ** 2))
        r = rng.uniform(0.6, 1.4) + 4.4 * near * near * rng.uniform(0.4, 1.0)
        t = rng.uniform(0.3, 1.0)
        c = tuple(int(round(v)) for v in lo + (hi - lo) * t)
        a = int(rng.uniform(*alpha))
        d.ellipse(((x - r) * ss, (y - r * 0.8) * ss, (x + r) * ss, (y + r * 0.8) * ss), fill=c + (a,))
        for _k in range(int(rng.integers(0, 4))):
            ang, dist = rng.uniform(0, 2 * math.pi), rng.uniform(r * 1.4, r * 4.0)
            rr = rng.uniform(0.3, 0.8)
            qx, qy = x + math.cos(ang) * dist, y + math.sin(ang) * dist
            d.ellipse(((qx - rr) * ss, (qy - rr) * ss, (qx + rr) * ss, (qy + rr) * ss), fill=c + (int(a * 0.8),))
    out = img.copy()
    out.alpha_composite(layer.resize(img.size, Image.LANCZOS))
    return out


def specks(img, box, n, seed, colors=None, size=(1.0, 3.2), alpha=(60, 200)):
    """A theme's corner specks: the fallen red SPLATTER, or synthwave's glowing embers (same call site,
    same box; synthwave bytes unchanged)."""
    if LOOK['splatter']:
        return splatter(img, box, n, seed + 7000)
    return embers(img, box, n, seed, colors=colors, size=size, alpha=alpha)


def fade_alpha(img, box, edge='bottom', length=60):
    """Multiply alpha by a linear ramp inside box toward `edge` (for faces / skylines)."""
    a = np.asarray(img.split()[3]).astype(np.float32)
    H, W = a.shape
    x0, y0, x1, y1 = box
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    if edge == 'bottom':
        k = ((y1 - yy) / length).clip(0, 1)
    elif edge == 'top':
        k = ((yy - y0) / length).clip(0, 1)
    elif edge == 'left':
        k = ((xx - x0) / length).clip(0, 1)
    else:
        k = ((x1 - xx) / length).clip(0, 1)
    out = img.copy()
    out.putalpha(Image.fromarray((a * k).clip(0, 255).astype(np.uint8)))
    return out


def clip_to(img, pts, size=None):
    """Keep only the part of img inside polygon pts (anti-aliased)."""
    from PIL import ImageDraw
    W, H = size or img.size
    ss = 4
    m = Image.new('L', (W * ss, H * ss), 0)
    ImageDraw.Draw(m).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    m = m.resize((W, H), Image.LANCZOS)
    out = img.copy()
    out.putalpha(ImageChops.multiply(img.split()[3], m))
    return out


def over(*layers):
    base = layers[0].copy()
    for l in layers[1:]:
        base.alpha_composite(l)
    return base
