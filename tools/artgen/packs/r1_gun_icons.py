"""r1_gun_icons.py - R1: every LIVE gun-bay icon, TRACED from a render of the weapon the game actually loads (2026-10-04).

WHY (tmp/design_review/findings.md). The user, after browsing the Art Atlas: "mozambique isnt even mozambique". The gun bay
(AetheriumLoadout.lua, "i_tod_hud_gun_" .. category, drawn 96 x 44 canvas units = 144 x 66 px at 1080p) showed generic
blocks drawn from memory. Every icon here is TRACED from the model's own render (tools/artgen/packs/r1_truth_render.py ->
art/generated/R1-truth-renders/<job>_side*.png), so its outline IS that weapon's outline.

THE LIVE SET (what Map 2 can put in a player's hands; scripts/zm/zm_tod2_cybercity/_tod_classes.gsc register_gun + the
level weapons; every other i_tod_hud_gun_* cell is a Map 1 leftover - see the R1 LAND.md list):
  ARCHER       bow (Bow), crossbow (R1 Shadowhunter), firebow (Fire Bow)
  BREACHER     mozambique, rem870 (Remington 870 MCS), peacekeeper, shield (the Riot Shield card)
  WARRIOR      fist (One Inch Punch), gauntlet (Gauntlet of Siegfried), greatsword (Cyber Sword)
  NECROMANCER  skull (Skull of Nan Sapwe), soulstaff (Soul Staff), crownstaff (Crown of the Damned)
  EVERYONE     mr6 (pistol_standard: the pre-draft start weapon and the last-stand pistol), gift (the Death Machine
               powerup = the Gift of Death, xmas_gun), blade (knife / bowie / Widow's Wine knife / bare-fist fallback)

THE STYLE IS THE SHIPPED ONE, MEASURED (PK06 gun_bay_icons.py): exactly three colours and binary alpha - NAVY #0A1020
outline, SHADE #62779C, LIGHT #E8EEF6 - a heavy outer outline, part lines inside, the darker / downward-facing half of
each form in SHADE, pointing RIGHT. Built at 4x and majority-voted down per 4 x 4 block (ties navy > shade > light >
clear), so the output holds only those three colours, like every neighbour, and is deterministic for --check.

HOW A RENDER BECOMES AN ICON (trace(), every number a per-icon knob in ICONS):
  1 crop the coverage, fit it into the icon's box (aspect kept), premultiplied resampling of every pass
  2 silhouette = coverage > 0.5; specks and pin-holes dropped
  3 THICK parts get the heavy outline (out_r px outside, in_w px inside); THIN parts (thinner than thin_r: a bow string,
    a sight post, a wire) are drawn as a navy line of their own, so a string never swells into a 10 px bar
  4 part lines: normal creases sharper than crease_deg, depth steps (one part in front of another) and MATERIAL
    boundaries (a jump in the median-smoothed albedo), kept only if longer than line_min px, drawn line_w px wide
  5 tones, the shipped grammar (light from above): the lower `band` of every vertical run of fill between lines is
    SHADE, and a part whose material is truly dark is SHADE whole; a small majority filter keeps the edges clean
  6 4x4 majority vote -> 288 x 132, three colours, binary alpha

NO MESH, SO A DIFFERENT TRUTH (said, not hidden):
  mr6    the MR6 (pistol_standard) has no mesh in any tools root - only its texture atlas. Drawn as vectors from that atlas
         (the grip, slide and frame panels) in the same three tones.
  blade  the knife / bowie have no mesh either. Traced from the BOWIE's own UV islands: the blade side and the handle
         side are flat projections in its colour atlases (weapons_t7/zmb_knife_bowie), composed into the side view.
  fist   the One Inch Punch has no weapon model (tod_punch_none_view is empty); the fist is the player's own hand, whose
         mesh (Nero Blackstone's viewhands, core_common) has no source. Traced from a real viewhands mesh (the Archer's
         BO2 hands) posed by linear-blend skinning with the punch's OWN animation, vm_zom_1inchpunch_idle frame 0.

USAGE
  python tools/artgen/packs/r1_gun_icons.py                write art/generated/R1-truth-icons-portraits/ + _review_guns.png
  python tools/artgen/packs/r1_gun_icons.py --stage DIR    also write the PNGs under DIR/source_data/tod_ui_images/_images/
  python tools/artgen/packs/r1_gun_icons.py --check [--root DIR]
                                                           BUILD GATE: regenerate, fail on any byte that differs from the
                                                           installed PNG, on an off-style pixel, or on a missing GDT/zone line
Never hand-edit an output PNG: change this file (or the render) and re-run.
"""
import argparse, hashlib, json, math, os, re, sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402

try:
    import resvg_py
except ImportError:  # pragma: no cover
    resvg_py = None

ROOT = artgen.ROOT
PACK = 'R1-truth-icons-portraits'
RENDERS = os.path.join(ROOT, 'art', 'generated', 'R1-truth-renders')
W, H, SS = 288, 132, 4
NAVY, SHADE, LIGHT = (10, 16, 32), (98, 119, 156), (232, 238, 246)
PAL = [NAVY, SHADE, LIGHT]          # class 1..3 (0 = clear)
BOWIE = os.path.join(r'C:\BO3Tools\TOD2Cybercity', 'model_export', 'weapons_t7', 'zmb_knife_bowie')
MR6_ATLAS = os.path.join(r'C:\BO3Tools\TOD2Cybercity', 'model_export', 'weapons_t7', 'mr6', 'mtl_wpn_t7_pistol_mr6_c.tif')

# -------------------------------------------------------------------------------------------- the icons
D = dict(box=(8, 14, 280, 118), band=0.42, dark_z=-9.0, alb_step=99.0, crease_deg=52.0, depth_step=0.05,
         line_min=10.0, line_w=2.6, out_r=4.6, in_w=1.6, thin_r=1.4, thin_line=1.3, smooth=1.6, alb_med=4.0, rot=0.0,
         flip=False, keep_lines=True, crop=(0.0, 0.0, 1.0, 1.0), vstretch=1.0, islands=1.0, design=(), view='side')
# islands: keep only connected parts at least this fraction of the biggest one (1.0 = keep everything)
# dark_z / alb_step are OFF by default (-9 / 99): on a textured model they speckled the fill; an icon opts in.
# design: the identity details a designer adds ON TOP of the traced outline, read off that model's render with
#   --debug (its beauty under a 10 px grid in icon coordinates), each CLIPPED to the traced fill so the silhouette stays
#   the model's: ('shade'|'light'|'navy', [(x, y), ...]) polygons and ('line', [(x, y), ...], width[, colour]) strokes
#   (navy unless a colour is named). A kind ending in '!' ('line!', 'light!') may paint OUTSIDE the traced fill - for a
#   thin part (an arrow shaft) the trace can only draw as a hairline.
# band: the lower fraction of every vertical run of fill that is SHADE (light from above, the shipped grammar).
# dark_z: a part whose smoothed albedo is this many standard deviations below the icon's mean is SHADE whole.
# alb_step: a jump this big (in the same z units) in the smoothed albedo is a MATERIAL boundary -> a part line.
# crop: the part of the render's coverage box kept (fractions x0, y0, x1, y1) - a staff's head end, not its whole pole.
# vstretch: a long gun's height is exaggerated by this much before the fit (true proportions put the 870 at 50 of 132 px:
#   a hairline at the bay's 144 x 66); every outline and part stays the model's, only the aspect moves.
# rot: the picture is turned (degrees, counter-clockwise) before the fit - a bow sits on the diagonal so it fills the cell.
# alb_med: the albedo's lightness is median-filtered over this radius (px) before the tones are picked, so texture grunge
#   never speckles the fill; part-sized light / dark areas survive.
def rr(x0, y0, x1, y1, r=3.0, n=5):
    """A rounded rectangle as a polygon (icon px), for a design detail."""
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90.0 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def el(cx, cy, rx, ry, n=28, a0=0.0, a1=360.0):
    """An ellipse (or an arc band's points) as a polygon (icon px)."""
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + (0 if a1 - a0 >= 360 else 1))]


def skull_face(cx, cy, s):
    """The staff skull's face as the model carries it: rolled 90 degrees on the staff (its crown points along the shaft,
    to the right), so the two sockets stack vertically on the right with their glowing eyes, the nasal cavity between
    them points at the crown, and the open jaw's two rows of teeth stand vertically on the left. Measured from the
    render (r1_truth_render soulstaff_fb / crownstaff_fb) at --debug; s scales it for the tier-3 skull in its halo."""
    X = lambda dx: cx + dx * s   # noqa: E731
    Y = lambda dy: cy + dy * s   # noqa: E731
    d = [('light', el(cx, cy, 44 * s, 40 * s)), ('shade', [(X(-50), Y(18)), (X(50), Y(18)), (X(50), Y(50)), (X(-50), Y(50))])]
    for sy in (-21, 20):
        d.append(('navy', el(X(18), Y(sy), 9.5 * s, 9 * s)))
        d.append(('light', el(X(20), Y(sy), 3.4 * s, 3.4 * s, 12)))
    d.append(('navy', [(X(4), Y(-7)), (X(13), Y(-1)), (X(4), Y(6))]))
    d.append(('navy', [(X(-28), Y(-20)), (X(-4), Y(-20)), (X(-4), Y(20)), (X(-28), Y(20))]))
    for col in ((-11, -5), (-27, -21)):
        for i in range(4):
            y0 = -18 + i * 9.5
            d.append(('light', [(X(col[0]), Y(y0)), (X(col[1]), Y(y0)), (X(col[1]), Y(y0 + 7.5)), (X(col[0]), Y(y0 + 7.5))]))
    return tuple(d)


def outlined(kind, pts, w=4.6):
    """A part drawn outside the traced fill with the set's own navy outline: the outline stroke, then the fill."""
    return (('line!', list(pts) + [pts[0]], w), (kind + '!', list(pts)))


def xbow_design():
    """The crossbow's identity parts over its trace (icon px, read off --debug crossbow)."""
    arc = [(187, 9), (200, 16), (211, 29), (218, 46), (221, 63), (218, 81), (210, 97), (199, 110), (187, 120)]
    d = [('navy', [(0, 0), (288, 0), (288, 132), (0, 132)])]          # the trace is the silhouette; its specks go
    d += [('line!', [(186, 11), (134, 62)], 3.6), ('line!', [(186, 119), (134, 68)], 3.6),         # the cables
         ('line!', [(186, 11), (134, 62)], 1.4, 'shade'), ('line!', [(186, 119), (134, 68)], 1.4, 'shade')]
    d += [('line!', arc, 13.0), ('line!', arc, 7.4, 'light'), ('line!', arc[2:7], 2.2, 'shade')]   # the prod
    d += list(outlined('light', [(44, 64), (98, 63), (112, 66), (152, 66), (152, 74), (112, 74), (98, 82), (44, 83)]))
    d += [('shade', [(44, 77), (100, 77), (112, 74), (152, 74), (152, 75), (112, 75), (98, 82), (44, 83)])]   # the stock
    d += [('line!', [(70, 64), (70, 82)], 2.2)]                                                    # the butt pad seam
    d += list(outlined('light', [(150, 60), (234, 60), (234, 70), (150, 70)]))                     # the rail
    d += [('shade!', [(150, 66), (234, 66), (234, 70), (150, 70)])]
    d += list(outlined('light', [(232, 57), (252, 64), (232, 72)], 4.0))                           # the bolt's head
    for cy in (9, 121):                                                                           # the cams
        d += [('navy!', el(187, cy, 8.0, 8.0)), ('light!', el(187, cy, 4.2, 4.2, 16)), ('navy!', el(187, cy, 1.6, 1.6, 8))]
    return tuple(d)


ICONS = {
    # the Apex Mozambique: black frame, the olive barrel block with its slot and two round windows (measured from the
    # albedo in icon space: dark blobs in the block at x 184-190 / 207-220 / 233-246, y 44-59)
    'mozambique':  dict(src='mozambique', box=(30, 10, 274, 124), dark_z=-0.25,
                        design=(('navy', rr(184, 46, 190, 58, 2.5)), ('navy', rr(207, 44, 220, 59, 4.5)),
                                ('navy', rr(233, 44, 246, 59, 4.5)))),
    # the Remington 870 MCS (BO2 port): breaching muzzle, barrel over the magazine tube, the grooved pump, the railed
    # receiver, pistol grip, the bare buffer tube behind; the two loose shells parked under it are dropped
    'rem870':      dict(src='rem870', box=(6, 20, 282, 114), vstretch=1.45, islands=0.03,
                        design=(('line', [(152, 50), (258, 50)], 2.4),
                                ('line', [(186, 52), (186, 62)], 2.4), ('line', [(196, 52), (196, 62)], 2.4),
                                ('line', [(206, 52), (206, 62)], 2.4), ('line', [(216, 52), (216, 62)], 2.4))),
    'peacekeeper': dict(src='peacekeeper', box=(6, 16, 282, 118), vstretch=1.3),
    # the Riot Shield (Lv1-8: the reskinned SoE rocket shield = Logical's yaw shield): the vision window up top, the
    # handle slot, the V-chevron armour plates below, the lower plates in SHADE
    'shield':      dict(src='shield', box=(70, 6, 218, 126), band=0.0, keep_lines=False,
                        design=(('shade', [(100, 78), (145, 101), (190, 78), (190, 128), (100, 128)]),
                                ('line', [(112, 79), (145, 100), (178, 79)], 3.2),
                                ('line', [(118, 23), (172, 23), (172, 40), (118, 40), (118, 23)], 3.0),
                                ('navy', rr(128, 64, 162, 70, 2.5)),
                                ('line', [(145, 101), (145, 124)], 3.0))),
    # the Bow (Der Eisendrache's base bow): the spiked recurve limbs with their wing arcs, the string, the arrow nocked
    # through the grip; its loose rocks and gem shards are dropped. The arrow's shaft is a hairline in the trace, so
    # it is drawn on its own line (nock to head) the width the bay can show.
    'bow':         dict(src='bow', box=(30, 4, 270, 128), vstretch=0.50, islands=0.08, thin_r=1.0,
                        design=(('line!', [(78, 62), (190, 62)], 6.4), ('line!', [(80, 62), (188, 62)], 2.6, 'light'))),
    # the R1 Shadowhunter from above and in front (r1_truth_render crossbow_hi, view "high"): the prod and its string
    # spread wide, the rail, the stock - from the plain side the prod is edge-on and it read as a rifle. That view
    # looks back along the bow, so it is mirrored to point right like every cell. W3 LEAD (2026-10-05): the trace alone
    # read as a faint navy smear in the bay (mean lightness 52 against the set's 85-140: its rail, riser and prod are
    # thin black parts), so the parts that make it a crossbow are drawn over it in the set's weight, each with its own
    # navy outline - the walnut stock and forend, the rail, the prod and its cams, the cables, the bolt's head past the
    # riser. Every coordinate is read off the trace (--debug crossbow).
    'crossbow':    dict(src='crossbow_hi', view='high', flip=True, box=(6, 4, 282, 128), islands=0.02,
                        design=xbow_design()),
    # the Fire Bow (tod_fire_bow_rune_view = DE's rune bow): the same limbs, but its wing arcs burn in BANDS (the lava
    # stripes of the model) - the read that tells it from the plain Bow
    'firebow':     dict(src='firebow', box=(30, 4, 270, 128), vstretch=0.50, islands=0.08, thin_r=1.0,
                        design=(('line!', [(78, 62), (190, 62)], 6.4), ('line!', [(80, 62), (188, 62)], 2.6, 'light'),
                                ('line', [(66, 18), (95, 20), (115, 27), (125, 37)], 2.4),
                                ('line', [(70, 25), (95, 27), (110, 32), (118, 41)], 2.4),
                                ('line', [(66, 106), (95, 104), (115, 97), (125, 87)], 2.4),
                                ('line', [(70, 99), (95, 97), (110, 92), (118, 83)], 2.4))),
    # the Gauntlet of Siegfried: the armoured forearm with its whelp dragon perched on it; the bracer's two seams
    'gauntlet':    dict(src='gauntlet', box=(6, 6, 282, 126), crease_deg=60.0, line_min=16.0,
                        design=(('line', [(150, 80), (150, 120)], 3.0), ('line', [(172, 80), (172, 120)], 3.0))),
    # the Cyber Sword (tod_cyber_sword): long blade flaring at the guard, the dark power spine of five circuit cells
    # with lit traces, the winged cross-guard with its reactor gem, the wrapped grip, the faceted pommel
    'greatsword':  dict(src='greatsword', box=(2, 22, 286, 110), vstretch=1.5, band=0.26, keep_lines=False,
                        design=(('shade', [(98, 59), (246, 60), (262, 66.5), (246, 73), (98, 74)]),
                                ('line', [(98, 59), (246, 60), (262, 66.5), (246, 73), (98, 74), (98, 59)], 2.2),
                                ('line', [(104, 70), (116, 70), (121, 63), (128, 63)], 1.8, 'light'),
                                ('line', [(134, 70), (146, 70), (151, 63), (158, 63)], 1.8, 'light'),
                                ('line', [(164, 70), (176, 70), (181, 63), (188, 63)], 1.8, 'light'),
                                ('line', [(194, 70), (206, 70), (211, 63), (218, 63)], 1.8, 'light'),
                                ('line', [(224, 70), (236, 70), (241, 63), (248, 63)], 1.8, 'light'),
                                ('navy', el(75, 66, 6.5, 7.5)),
                                ('light', [(75, 61), (78.5, 66), (75, 71), (71.5, 66)]))),
    # the Skull of Nan Sapwe (the Keeper's head): crested skull, its face turned right - an eye socket, the ribbed
    # cheek, the fangs of the jaw (texture creases are noise here: lines off, the design carries the read)
    'skull':       dict(src='skull', box=(46, 2, 242, 130), keep_lines=False, band=0.38,
                        design=(('navy', [(156, 50), (171, 47), (175, 58), (163, 64), (155, 59)]),
                                ('line', [(118, 72), (146, 70)], 2.6), ('line', [(116, 82), (144, 80)], 2.6),
                                ('line', [(114, 92), (142, 90)], 2.6),
                                ('navy', [(148, 74), (186, 76), (184, 86), (150, 92)]),
                                ('light', [(156, 76), (160, 84), (164, 76)]), ('light', [(168, 77), (172, 85), (176, 77)]))),
    # the Necromancer's staffs, rolled about their axis so the skull faces the camera and the crown's halo opens
    # (r1_truth_render jobs *_fb); the head end and a length of the wrapped shaft
    'soulstaff':   dict(src='soulstaff_fb', box=(2, 8, 286, 124), crop=(0.66, 0.0, 1.0, 1.0), crease_deg=62.0,
                        line_min=14.0, design=skull_face(240, 66, 1.0)),
    'crownstaff':  dict(src='crownstaff_fb', box=(2, 2, 286, 130), crop=(0.40, 0.0, 1.0, 1.0), crease_deg=62.0,
                        line_min=14.0, design=skull_face(175, 66, 0.52)),
    # the Gift of Death (xmas_gun, the Death Machine powerup's gun): its tinsel garland is left out of the render (noise
    # at bay size - r1_truth_render gift_bare); what stays is the gun - the ammo drum, the receiver, the long barrel -
    # wrapped in ribbon bands with two ornament baubles hung on it, placed where the model has them
    'gift':        dict(src='gift_bare', box=(10, 8, 278, 124), design=(
        ('shade', [(126, 52), (278, 52), (278, 77), (126, 77)]),
        ('light', [(132, 50), (142, 50), (138, 79), (128, 79)]), ('light', [(172, 50), (184, 50), (180, 79), (168, 79)]),
        ('light', [(200, 50), (212, 50), (208, 79), (196, 79)]), ('light', [(227, 50), (238, 50), (234, 79), (223, 79)]),
        ('light', [(245, 50), (255, 50), (251, 79), (241, 79)]),
        ('line', [(132, 50), (128, 79)], 1.8), ('line', [(142, 50), (138, 79)], 1.8),
        ('line', [(172, 50), (168, 79)], 1.8), ('line', [(184, 50), (180, 79)], 1.8),
        ('line', [(200, 50), (196, 79)], 1.8), ('line', [(212, 50), (208, 79)], 1.8),
        ('line', [(227, 50), (223, 79)], 1.8), ('line', [(238, 50), (234, 79)], 1.8),
        ('line', [(245, 50), (241, 79)], 1.8), ('line', [(255, 50), (251, 79)], 1.8),
        ('navy', el(155, 62, 7.5, 7.5)), ('light', el(155, 62, 4.8, 4.8)),
        ('navy', el(220, 61, 7.5, 7.5)), ('light', el(220, 61, 4.8, 4.8)))),
    # the One Inch Punch: no weapon model (the fist is the player's own hand, whose mesh has no source here) - so a real
    # viewhands mesh posed with the punch's OWN idle animation (r1_truth_render fist_r270: the right arm, forearm
    # level), mirrored to strike right, cropped to the forearm and the fist
    'fist':        dict(src='fisth_r270', flip=True, box=(30, 6, 258, 126), keep_lines=False, band=0.40,
                        design=(('light', el(121, 35, 12, 10)), ('line', el(121, 35, 12, 10) + [el(121, 35, 12, 10)[0]], 2.6),
                                ('light', el(149, 36, 12, 10)), ('line', el(149, 36, 12, 10) + [el(149, 36, 12, 10)[0]], 2.6),
                                ('light', el(176, 39, 10, 9.5)), ('line', el(176, 39, 10, 9.5) + [el(176, 39, 10, 9.5)[0]], 2.6),
                                ('light', el(196, 41, 9, 9)), ('line', el(196, 41, 9, 9) + [el(196, 41, 9, 9)[0]], 2.6),
                                ('line', [(112, 60), (128, 66), (146, 64)], 2.4), ('line', [(150, 66), (168, 70), (186, 68)], 2.4),
                                ('line', [(104, 74), (98, 96)], 2.4))),
    'blade':       dict(src=None, box=(20, 26, 268, 106)),           # the bowie, from its UV islands (bowie_passes)
    'mr6':         dict(src=None, box=(70, 22, 218, 122)),           # vectors from the atlas (mr6_svg)
}
# SHIPPED (reviewed 2026-10-04 on contact sheets): only these five beat the icons they replace (the user's
# wrong-subject list: the Mozambique, Peacekeeper, 870, riot shield, plus a truer crossbow). The traces of the
# bow / fire bow / fist / gauntlet / skull came out as unreadable blobs and stay the shipped drawings until
# redone; soulstaff / crownstaff / greatsword stay PK06's (gun_bay_icons.py gates them); blade / gift / mr6
# are Map 1 leftovers no live class carries (the Map 1 purge decides them). --check gates only SHIPPED.
SHIPPED = ('mozambique', 'peacekeeper', 'rem870', 'shield', 'crossbow', 'blade', 'gift', 'mr6')   # blade / gift / mr6: live (knives + fists, Gift of Death, the last-stand MR6), were Map 1 copies
NAMES = ['i_tod_hud_gun_' + k for k in ICONS if k in SHIPPED]


def P(name):
    p = dict(D)
    p.update(ICONS[name])
    return p

# -------------------------------------------------------------------------------------------- passes


def _rgba(path):
    return np.asarray(Image.open(path).convert('RGBA')).astype(np.float32) / 255.0


def _grey(path):
    im = Image.open(path)
    if im.mode in ('I;16', 'I;16B', 'I'):
        return np.asarray(im).astype(np.float32) / 65535.0
    return np.asarray(im.convert('L')).astype(np.float32) / 255.0


def load_passes(job, view='side'):
    base = os.path.join(RENDERS, '%s_%s' % (job, view))
    alb = _rgba(base + '_albedo.png')
    nor = _rgba(base + '_normal.png')
    dep = _grey(base + '_depth.png')
    a = alb[..., 3]
    n = nor[..., :3] * 2.0 - 1.0
    return {'a': a, 'rgb': alb[..., :3], 'n': n, 'd': dep}


def crop_fit(ps, box, rot=0.0, flip=False, crop=(0.0, 0.0, 1.0, 1.0), vstretch=1.0):
    """Crop to the coverage, rotate / flip in the picture plane, fit into `box` (output px) at SS. Returns canvas-sized
    passes (H*SS x W*SS) with premultiplied resampling (edges never mix with the background)."""
    a = ps['a']
    chans = {'a': a[..., None], 'rgb': ps['rgb'], 'n': ps['n'], 'd': ps['d'][..., None]}
    if flip:
        chans = {k: v[:, ::-1].copy() for k, v in chans.items()}
        chans['n'][..., 0] *= -1
    if rot:
        th = math.radians(rot)
        out = {}
        for k, v in chans.items():
            out[k] = np.stack([ndi.rotate(v[..., c], rot, reshape=True, order=1, mode='constant', cval=0.0)
                               for c in range(v.shape[2])], -1)
        nx, ny = out['n'][..., 0].copy(), out['n'][..., 1].copy()
        # image rows go DOWN while the normal's y goes UP: a CCW picture rotation turns (x, y) by +rot
        out['n'][..., 0] = nx * math.cos(th) - ny * math.sin(th)
        out['n'][..., 1] = nx * math.sin(th) + ny * math.cos(th)
        chans = out
    a = chans['a'][..., 0]
    ys, xs = np.where(a > 0.08)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    cw, ch = x1 - x0, y1 - y0
    x0, x1 = x0 + int(crop[0] * cw), x0 + int(math.ceil(crop[2] * cw))
    y0, y1 = y0 + int(crop[1] * ch), y0 + int(math.ceil(crop[3] * ch))
    if crop != (0.0, 0.0, 1.0, 1.0):     # re-tighten to what the crop left covered
        sub = a[y0:y1, x0:x1] > 0.08
        ys, xs = np.where(sub)
        y0, y1, x0, x1 = y0 + ys.min(), y0 + ys.max() + 1, x0 + xs.min(), x0 + xs.max() + 1
    bw, bh = (box[2] - box[0]) * SS, (box[3] - box[1]) * SS
    s = min(bw / (x1 - x0), bh / ((y1 - y0) * vstretch))
    nw, nh = max(1, int(round((x1 - x0) * s))), max(1, int(round((y1 - y0) * s * vstretch)))
    ox = int(round(box[0] * SS + (bw - nw) / 2.0))
    oy = int(round(box[1] * SS + (bh - nh) / 2.0))
    ac = a[y0:y1, x0:x1]

    def rs(arr):
        return np.asarray(Image.fromarray(arr.astype(np.float32), 'F').resize((nw, nh), Image.BOX))

    A = rs(ac)
    out = {'a': np.zeros((H * SS, W * SS), np.float32)}
    out['a'][oy:oy + nh, ox:ox + nw] = A
    for k in ('rgb', 'n', 'd'):
        v = chans[k][y0:y1, x0:x1]
        ch = v.shape[2]
        big = np.zeros((H * SS, W * SS, ch), np.float32)
        for c in range(ch):
            r = rs(v[..., c] * ac) / np.maximum(A, 1e-4)
            big[oy:oy + nh, ox:ox + nw, c] = r
        out[k] = big if ch > 1 else big[..., 0]
    nn = np.linalg.norm(out['n'], axis=-1, keepdims=True)
    out['n'] = out['n'] / np.maximum(nn, 1e-4)
    out['scale'] = s
    return out

# -------------------------------------------------------------------------------------------- the trace


def disk_dilate(m, r):
    if r <= 0:
        return m.copy()
    return ndi.distance_transform_edt(~m) <= r


def disk_erode(m, r):
    if r <= 0:
        return m.copy()
    return ndi.distance_transform_edt(m) > r


def drop_small(m, min_px):
    lab, n = ndi.label(m, structure=np.ones((3, 3)))
    if n == 0:
        return m
    sizes = ndi.sum(m, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool)
    keep[1:] = sizes >= min_px
    return keep[lab]


def fill_pinholes(m, max_px):
    lab, n = ndi.label(~m)
    if n == 0:
        return m
    sizes = ndi.sum(~m, lab, range(1, n + 1))
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    fill = np.zeros(n + 1, bool)
    for i in range(1, n + 1):
        fill[i] = sizes[i - 1] <= max_px and i not in border
    return m | fill[lab]


def lightness(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def trace(c, p):
    """Canvas passes -> class map at SS (0 clear, 1 navy, 2 shade, 3 light)."""
    k = SS
    M = c['a'] > 0.5
    M = drop_small(M, (1.6 * k) ** 2)
    if p['islands'] < 1.0:          # detached extras (the DE bows' loose rocks and gem shards) go
        lab, nl = ndi.label(M, structure=np.ones((3, 3)))
        if nl > 1:
            sizes = ndi.sum(M, lab, range(1, nl + 1))
            keep = np.zeros(nl + 1, bool)
            keep[1:] = sizes >= p['islands'] * sizes.max()
            M = keep[lab]
    M = fill_pinholes(M, (1.4 * k) ** 2)
    # THICK = what survives an opening of radius thin_r; the rest is thin (strings, posts, wires)
    thick = M & disk_dilate(disk_erode(M, p['thin_r'] * k), p['thin_r'] * k + 0.5)
    thick = drop_small(thick, (2.0 * k) ** 2)
    thin = M & ~thick
    fill = disk_erode(thick, p['in_w'] * k)
    fill = drop_small(fill, (1.2 * k) ** 2)
    navy = (disk_dilate(thick, p['out_r'] * k) & ~fill) | disk_dilate(thin, p['thin_line'] * k)

    # the albedo's lightness, median-smoothed (texture grunge never reaches the tones or the lines)
    L = lightness(c['rgb'])
    L = np.where(thick, L, L[thick].mean() if thick.any() else 0.0)
    mr = max(1, int(round(p['alb_med'] * k / 2.0)))
    half = np.asarray(Image.fromarray(L.astype(np.float32), 'F').resize((W * k // 2, H * k // 2), Image.BOX))
    half = ndi.median_filter(half, size=2 * mr + 1)
    L = np.asarray(Image.fromarray(half, 'F').resize((W * k, H * k), Image.BILINEAR))
    Lz = (L - L[fill].mean()) / (L[fill].std() + 1e-4) if fill.any() else L * 0

    # part lines: normal creases + depth steps + MATERIAL boundaries (a strong step in the smoothed albedo), inside the
    # fill only, short fragments dropped
    E = np.zeros_like(M)
    if p['keep_lines'] and fill.any():
        n = c['n']
        cosd = math.cos(math.radians(p['crease_deg']))
        E[:, 1:] |= (n[:, 1:] * n[:, :-1]).sum(-1) < cosd
        E[1:] |= (n[1:] * n[:-1]).sum(-1) < cosd
        d = c['d']
        E[:, 1:] |= np.abs(d[:, 1:] - d[:, :-1]) > p['depth_step']
        E[1:] |= np.abs(d[1:] - d[:-1]) > p['depth_step']
        g = max(1, int(round(0.6 * k)))
        E[:, g:] |= np.abs(Lz[:, g:] - Lz[:, :-g]) > p['alb_step']
        E[g:] |= np.abs(Lz[g:] - Lz[:-g]) > p['alb_step']
        E &= disk_erode(fill, 0.8 * k)
        E = drop_small(E, p['line_min'] * k)
        E = disk_dilate(E, p['line_w'] * k / 2.0)

    # tones, the shipped grammar: light from above - in every vertical run of fill between lines, the LOWER band is
    # SHADE; a part whose material is truly dark (smoothed albedo below dark_z) is SHADE whole
    sh = np.zeros_like(M)
    if fill.any():
        free = fill & ~E
        ys = np.arange(free.shape[0])[:, None]
        # run starts / ends per column via cumulative tricks: label vertical runs
        lab, nrun = ndi.label(free, structure=np.array([[0, 1, 0], [0, 1, 0], [0, 1, 0]]))
        if nrun:
            idx = np.arange(1, nrun + 1)
            top = ndi.minimum(np.broadcast_to(ys, free.shape), lab, idx)
            bot = ndi.maximum(np.broadcast_to(ys, free.shape), lab, idx)
            tt = np.zeros(nrun + 1)
            bb = np.zeros(nrun + 1)
            tt[1:], bb[1:] = top, bot
            T, B = tt[lab], bb[lab]
            frac = (ys - T) / np.maximum(B - T, 1)
            sh |= free & (frac > 1.0 - p['band'])
        sh |= fill & (Lz < p['dark_z'])
        r = max(1, int(round(p['smooth'] * k)))
        num = ndi.uniform_filter(sh.astype(np.float32), size=2 * r + 1)
        den = ndi.uniform_filter(fill.astype(np.float32), size=2 * r + 1)
        sh = (num / np.maximum(den, 1e-4) > 0.5) & fill
    cls = np.zeros(M.shape, np.uint8)
    cls[navy] = 1
    cls[fill & ~sh] = 3
    cls[fill & sh] = 2
    cls[E & fill] = 1
    for item in p['design']:
        lay = Image.new('L', (W * k, H * k), 0)
        dr = ImageDraw.Draw(lay)
        free = item[0].endswith('!')               # '!' = may paint outside the traced fill (a thin part's body)
        kind = item[0].rstrip('!')
        if kind == 'line':
            pts = [(x * k, y * k) for x, y in item[1]]
            dr.line(pts, fill=255, width=max(1, int(round(item[2] * k))), joint='curve')
            for x, y in pts[:1] + pts[-1:]:
                r = item[2] * k / 2.0
                dr.ellipse([x - r, y - r, x + r, y + r], fill=255)
            q = {'navy': 1, 'shade': 2, 'light': 3}[item[3] if len(item) > 3 else 'navy']
        else:
            dr.polygon([(x * k, y * k) for x, y in item[1]], fill=255)
            q = {'navy': 1, 'shade': 2, 'light': 3}[kind]
        m = np.asarray(lay) > 127
        if not free:
            m &= fill
        cls[m] = q
    return cls


def downvote(cls):
    """4x4 majority vote -> the three-colour icon (PK06's rule: ties navy > shade > light > clear)."""
    b = cls.reshape(H, SS, W, SS).transpose(0, 2, 1, 3).reshape(H, W, SS * SS)
    counts = np.stack([(b == q).sum(-1) for q in range(4)], -1).astype(np.float64)
    counts += np.array([0.0, 0.3, 0.2, 0.1])
    win = counts.argmax(-1)
    out = np.zeros((H, W, 4), np.uint8)
    for q, col in enumerate(PAL, 1):
        out[win == q] = col + (255,)
    return Image.fromarray(out, 'RGBA')

# -------------------------------------------------------------------------------- the three without a mesh


import gun_bay_icons as g6   # noqa: E402  (PK06's Part / compose / 3-tone render: one outline weight for the set)


def mr6_svg():
    """THE MR6 (pistol_standard), drawn as vectors: no mesh exists in any tools root, only its colour atlas
    (weapons_t7/mr6/mtl_wpn_t7_pistol_mr6_c.tif). From that atlas: the boxy slide with its rear serrations cut as
    bold diagonals (the "////" panels), the <.40 RBK> ammo readout on the slide's flank (a dark window with a lit
    tick), the dust-cover frame squared off under the muzzle with its rail notches, the squared trigger guard, and the
    stippled grip with the finger grooves its front-strap island carries, flared at the magwell. Muzzle right."""
    CY = g6.CY
    parts = []
    # GRIP (behind the slide): back strap raked ~14 deg, finger grooves on the front strap, a flared magwell foot
    grip = [(84, 60), (124, 60), (126, 70), (121, 76), (124, 84), (118, 90), (121, 98), (115, 104), (117, 112),
            (112, 120), (78, 120), (74, 114), (78, 104), (80, 86), (82, 70)]
    stip = g6.fillp(g6.path([(88, 74), (110, 74), (106, 110), (84, 110)]), g6.SHADE)
    stip += g6.line([(90, 80), (104, 80)], 2.6, cap='butt') + g6.line([(88, 92), (102, 92)], 2.6, cap='butt')
    parts.append(g6.Part(g6.path(grip), g6.path(g6.rect(60, 100, 140, 140)), stip))
    # FRAME / dust cover under the muzzle, with three rail notches, and the squared trigger guard below it
    frame = [(118, 58), (214, 58), (216, 62), (216, 74), (152, 74), (150, 94), (144, 98), (122, 98), (118, 92)]
    fdet = ''.join(g6.line([(x, 66), (x, 74)], 2.8, cap='butt') for x in (172, 186, 200))
    parts.append(g6.Part(g6.path(frame), g6.below(68), fdet,
                         over=g6.fillp(g6.path([(126, 76), (144, 76), (142, 90), (128, 90)]), g6.NAVY)
                         + g6.line([(134, 76), (132, 84), (136, 88)], 3.0)))
    # SLIDE: chamfered nose and rear, sights, the diagonal serrations, the readout window
    slide = [(72, 40), (76, 34), (204, 34), (212, 38), (216, 46), (216, 58), (72, 58)]
    sdet = ''
    for x in (82, 92, 102):
        sdet += g6.fillp(g6.path([(x, 56), (x + 4, 56), (x + 12, 36), (x + 8, 36)]), g6.SHADE)
    sdet += g6.fillp(g6.path(g6.rect(128, 41, 176, 52)), g6.NAVY)
    sdet += g6.fillp(g6.path([(134, 44), (140, 46.5), (134, 49)]), g6.LIGHT)          # the readout's lit "<"
    sdet += g6.fillp(g6.path(g6.rect(146, 44.5, 166, 48.5)), g6.LIGHT)
    sdet += g6.line([(190, 36), (190, 56)], 3.0, cap='butt')                               # the slide's nose seam
    parts.append(g6.Part(g6.path(slide), g6.below(51), sdet,
                         over=g6.fillp(g6.path(g6.rect(76, 29, 84, 34)), g6.NAVY)
                         + g6.fillp(g6.path(g6.rect(202, 30, 208, 34)), g6.NAVY)))
    return g6.compose(parts)


def bowie_svg():
    """THE KNIFE (the blade cell: knife / bowie / Widow's Wine knife / bare-fist fallback): no knife mesh exists in any
    tools root. Traced from the BOWIE's own UV islands (weapons_t7/zmb_knife_bowie): the metal atlas's long island is
    the blade's flat - a straight spine, the edge's grind sweeping UP to a point level with the spine, two rounded
    fullers under the spine and jimping notches at the ricasso; the plastic atlas's island is the handle's flat - a
    riveted slab bellied under the fingers; a brass cross-guard between them. Tip right."""
    CY = g6.CY
    parts = []
    # HANDLE (left): riveted slab, finger belly underneath, a capped pommel
    handle = [(30, 56), (96, 54), (96, 82), (84, 84), (76, 80), (66, 84), (56, 80), (44, 84), (32, 82), (26, 76),
              (26, 62)]
    hdet = ''.join(g6.dot(x, 66, 2.8) for x in (42, 62, 82))
    parts.append(g6.Part(g6.path(handle), g6.below(72), hdet))
    pommel = [(16, 60), (28, 54), (32, 56), (32, 82), (28, 86), (16, 80)]
    parts.append(g6.Part(g6.path(pommel), g6.below(72)))
    # BLADE: spine straight, edge swept up to the point; fullers + jimping
    blade = [(104, 50), (250, 50), (270, 50), (258, 60), (238, 70), (204, 77), (150, 80), (104, 80)]
    bdet = g6.fillp(g6.path([(116, 54), (178, 54), (182, 57), (178, 60), (116, 60), (112, 57)]), g6.NAVY)
    bdet += g6.fillp(g6.path([(192, 54), (214, 54), (218, 57), (214, 60), (192, 60), (188, 57)]), g6.NAVY)
    bdet += ''.join(g6.line([(x, 76), (x, 82)], 2.6, cap='butt') for x in (110, 116, 122))
    # the grind: the lower bevel along the edge in SHADE
    grind = g6.fillp(g6.path([(128, 70), (204, 68), (236, 62), (262, 54), (270, 50), (258, 60), (238, 70), (204, 77),
                              (150, 80), (128, 80)]), g6.SHADE)
    parts.append(g6.Part(g6.path(blade), None, grind + bdet))
    # GUARD (brass, double quillon, over both)
    guard = [(96, 40), (104, 40), (106, 50), (104, 82), (106, 92), (96, 92), (94, 82), (96, 50)]
    parts.append(g6.Part(g6.path(guard), g6.below(68)))
    return g6.compose(parts)


VECTOR = {'mr6': mr6_svg, 'blade': bowie_svg}


def build_one(name):
    p = P(name)
    if name in VECTOR:
        return g6.render(VECTOR[name]())
    c = crop_fit(load_passes(p['src'], p['view']), p['box'], p['rot'], p['flip'], tuple(p['crop']), p['vstretch'])
    return downvote(trace(c, p))


def debug_sheet(names, out):
    """A design aid (not shipped): each icon's beauty render fitted with the icon's own crop / fit, under a 10 px grid in
    ICON coordinates, beside the icon - so an identity detail can be placed where the model has it."""
    rows = []
    for name in names:
        p = P(name)
        if p['src'] is None:
            continue
        ps = load_passes(p['src'], p['view'])
        beauty = np.asarray(Image.open(os.path.join(RENDERS, '%s_%s.png' % (p['src'], p['view']))).convert('RGBA')).astype(np.float32) / 255
        ps2 = dict(ps, rgb=beauty[..., :3])
        c = crop_fit(ps2, p['box'], p['rot'], p['flip'], tuple(p['crop']), p['vstretch'])
        img = np.clip(c['rgb'] * 255 * 1.6, 0, 255).astype(np.uint8)
        im = Image.fromarray(img, 'RGB').resize((W * 3, H * 3), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        for gx in range(0, W, 10):
            d.line([(gx * 3, 0), (gx * 3, H * 3)], fill=(60, 60, 80) if gx % 50 else (140, 60, 60))
        for gy in range(0, H, 10):
            d.line([(0, gy * 3), (W * 3, gy * 3)], fill=(60, 60, 80) if gy % 50 else (140, 60, 60))
        ic = build_one(name).resize((W * 3, H * 3), Image.NEAREST)
        bg = Image.new('RGBA', ic.size, (28, 30, 38, 255))
        bg.alpha_composite(ic)
        rows.append((name, im.convert('RGBA'), bg))
    sheet = Image.new('RGBA', (W * 6 + 30, (H * 3 + 30) * len(rows)), (16, 16, 22, 255))
    d = ImageDraw.Draw(sheet)
    for i, (name, a, b) in enumerate(rows):
        y = i * (H * 3 + 30)
        d.text((6, y + 4), name + '  (grid 10 px, red every 50)', fill=(220, 220, 230, 255))
        sheet.alpha_composite(a, (0, y + 24))
        sheet.alpha_composite(b, (W * 3 + 30, y + 24))
    sheet.save(out)
    return out


def build(only=None):
    out = {}
    for name in ICONS:
        if name not in SHIPPED or (only and name not in only):
            continue
        try:
            out['i_tod_hud_gun_' + name] = build_one(name)
        except NotImplementedError:
            pass
    return out

# -------------------------------------------------------------------------------------------- review


def onscreen(icon):
    """The icon where the player sees it: the gun plate at 1080p, the icon in the 96 x 44 bay -> 144 x 66 px."""
    plate = Image.open(artgen.shipped('i_tod_h2_gun_plate')).convert('RGBA')
    pw, ph = 396, 108
    bg = Image.new('RGBA', (pw, ph), (18, 18, 24, 255))
    bg.alpha_composite(plate.resize((pw, ph), Image.LANCZOS))
    bg.alpha_composite(icon.resize((144, 66), Image.BILINEAR), (9, 39))
    return bg


def review(images, out_dir, fname='_review_guns.png'):
    font = artgen.ttf(16)
    rows = []
    for name, im in images.items():
        short = name.replace('i_tod_hud_gun_', '')
        src = P(short)['src']
        beauty = os.path.join(RENDERS, '%s_%s.png' % (src, P(short)['view'])) if src else None
        a = onscreen(im)
        b = onscreen(Image.open(artgen.shipped(name)).convert('RGBA'))
        rows.append((name, im, Image.open(artgen.shipped(name)).convert('RGBA'), a, b, beauty))
    rh = 132 + 40
    sheet = Image.new('RGBA', (288 * 2 + 396 * 2 + 300 + 70, rh * len(rows) + 40), (28, 30, 38, 255))
    d = ImageDraw.Draw(sheet)
    d.text((12, 10), 'NEW | SHIPPED (full size 288x132)  |  NEW | SHIPPED on the gun plate at 1080p (icon 144x66)  |  the truth render',
           fill=(220, 225, 235, 255), font=font)
    y = 40
    for name, im, old, a, b, beauty in rows:
        d.text((12, y), name, fill=(170, 180, 200, 255), font=font)
        sheet.alpha_composite(im, (10, y + 20))
        sheet.alpha_composite(old, (10 + 288 + 10, y + 20))
        sheet.alpha_composite(a, (10 + 576 + 30, y + 20 + 12))
        sheet.alpha_composite(b, (10 + 576 + 30 + 396 + 10, y + 20 + 12))
        if beauty and os.path.exists(beauty):
            th = Image.open(beauty).convert('RGBA')
            th.thumbnail((290, 130))
            bg = Image.new('RGBA', th.size, (60, 64, 78, 255))
            bg.alpha_composite(th)
            sheet.alpha_composite(bg, (sheet.width - 300, y + 20))
        y += rh
    out = os.path.join(out_dir, fname)
    sheet.save(out)
    return out

# -------------------------------------------------------------------------------------------- check


def _read(p):
    with open(p, 'rb') as f:
        return f.read()


MANIFEST = os.path.join(ROOT, 'art', 'generated', PACK, '_manifest_guns.json')


def renders_present():
    for name in ICONS:
        p = P(name)
        if p['src'] and not os.path.exists(os.path.join(RENDERS, '%s_%s_albedo.png' % (p['src'], p['view']))):
            return False
    return True


def check(root):
    """Regenerate from the truth renders and compare bytes. If the renders are not in this checkout (they are a 50 MB
    input), fall back to the md5s the generator recorded in _manifest_guns.json - still a byte gate, never a pass."""
    fails = []
    if renders_present():
        images = build()
        mode = 'regenerated from the truth renders'
    else:
        images = {}
        rec = json.load(open(MANIFEST))
        for name, md5 in rec.items():
            if name not in NAMES:
                continue   # a draft the review rejected: never installed, never checked
            pth = os.path.join(root, 'source_data', 'tod_ui_images', '_images', name + '.png')
            images[name] = Image.open(pth).convert('RGBA') if os.path.exists(pth) else None
            if images[name] is not None and hashlib.md5(_read(pth)).hexdigest() != md5:
                fails.append('%s: installed PNG is not the recorded generator output (%s)' % (name, MANIFEST))
        mode = 'renders absent: installed bytes vs %s' % os.path.relpath(MANIFEST, ROOT)
    if sorted(images) != sorted(NAMES):   # only the SHIPPED icons; the rest were drafts the review rejected
        fails.append('built %s, expected the shipped set %s' % (sorted(images), sorted(NAMES)))
    for name, im in images.items():
        p = os.path.join(root, 'source_data', 'tod_ui_images', '_images', name + '.png')
        if im is None or not os.path.exists(p):
            fails.append('%s: not installed (%s)' % (name, p))
            continue
        elif mode.startswith('regenerated') and _read(p) != artgen.png_bytes(im):
            fails.append('%s: installed PNG differs from the generator (re-stage; never hand-edit)' % name)
        a = np.array(im)
        cols = {tuple(int(v) for v in q) for q in a[a[..., 3] > 0][:, :3]}
        if im.size != (W, H) or not cols <= set(PAL) or not set(np.unique(a[..., 3])) <= {0, 255}:
            fails.append('%s: off-style (size %s, colours %s)' % (name, im.size, sorted(cols)))
    gdt = _read(os.path.join(root, 'source_data', 'tod_ui_images.gdt')).decode('utf-8', 'replace')
    zone = _read(os.path.join(root, 'zone_source', 'zm_tod2_cybercity.zone')).decode('utf-8', 'replace')
    zl = set(l.strip() for l in zone.splitlines())
    for name in NAMES:
        if '"%s" ( "image.gdf" )' % name not in gdt:
            fails.append('%s: no image.gdf block' % name)
        if 'image,' + name not in zl:
            fails.append('%s: no zone image line (the bay builds the name at runtime: a WHITE SQUARE)' % name)
    if fails:
        print('R1 GUN ICONS FAILED (%d):' % len(fails))
        for f in fails:
            print('  * ' + f)
        return 1
    print('R1 GUN ICONS OK %d (%s; 3-tone style; GDT + zone wired)' % (len(images), mode))
    return 0


def main():
    ap = argparse.ArgumentParser(description='R1 truth-traced gun-bay icons')
    ap.add_argument('--stage', default=None, help='also write <DIR>/source_data/tod_ui_images/_images/*.png')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--only', default=None)
    ap.add_argument('--debug', default=None, help='write a design-aid sheet for these icons (comma list) and stop')
    a = ap.parse_args()
    if a.check:
        sys.exit(check(a.root))
    if a.debug:
        print('debug ->', debug_sheet(a.debug.split(','), os.path.join(ROOT, 'tmp', 'redesign', PACK, 'work', 'debug_icons.png')))
        return
    only = set(a.only.split(',')) if a.only else None
    images = build(only)
    out_dir = artgen.stage_dir(PACK)
    rec = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    for name, im in images.items():
        md5 = artgen.save_png(im, os.path.join(out_dir, name + '.png'))
        rec[name] = md5
        print('%s.png  md5 %s' % (name, md5))
        if a.stage:
            artgen.save_png(im, os.path.join(a.stage, 'source_data', 'tod_ui_images', '_images', name + '.png'))
    with open(MANIFEST, 'w') as f:
        json.dump(dict(sorted(rec.items())), f, indent=1)
    print('review ->', review(images, out_dir))


if __name__ == '__main__':
    main()
