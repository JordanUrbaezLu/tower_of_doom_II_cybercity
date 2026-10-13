"""R6 - THE FOUR CLASS DRAFT CARDS AS ONE SET (2026-10-05, the one-library pass, wave 3).

User 2026-10-05: "Lets also make them look like they come from same pack ... necromancer doesnt look like a
consistent design to the others ... Whole entire asset library should look like one library."

WHAT IT OWNS (four same-name drop-ins, 768x1152; every GDT block, zone line and Lua registration already exists):
  i_tod_card_class_necromancer / _assault / _heavy / _slasher
      The CLASS DRAFT cards - the first screen of every match (tod_class_select.lua USE_CLASS_CARD_ART) and the
      crown CLASS TERMINAL. Class ids 1-4: NECROMANCER, ARCHER, BREACHER, WARRIOR.
  Until this pass PK01 wrote the Archer / Breacher / Warrior cards (with R2 drawing the Breacher's art window) and
  the Necromancer card was a hand-installed drop (docs/179). ONE OWNER PER FILE: this generator writes and
  --checks all four; pk01_card_text_rebake.py keeps only the tier-gate strips and r2_card_subjects.py only its
  three layered tier-card illustrations.

WHAT WAS WRONG (measured on the shipped files; tmp/wave3/R6-class-cards/LAND.md):
  1. Every word - TIER 1, the art-window title, the class banner, the weapon name - was set in the RETIRED typeface
     whose S is a 5 ("5KULL OF NAN 5APWE", "5OUL REAPER", "CLO5E RANGE TANK"). CLAUDE.md: never restore it.
  2. The four art windows used four techniques: a flat cartoon skull on a bright green disc with a cyan beam that
     ran out over the window frame (Necromancer), thin line art (Archer), the real Mozambique (R2, Breacher) and a
     flat gold cartoon fist (Warrior). Their window lighting differed too (a dark title band and an equaliser stack
     on two cards, a different wash on each).
  3. The four name boxes were built three ways (brackets only; brackets + a full inner frame; brackets + a top
     line), and the four cards set their words at four sizes and spacings.

THE SET (one recipe, only the class hue and the words change):
  * THE CHASSIS is kept - frame, warning stripes, scratched steel, the red (Breacher: amber) alarm rail, the class-hue
    rail, the header's top line, the banner bar, the brackets, the pips (docs/171 Theme B, the user's pick): every
    pixel outside the four word slots and the art window is the shipped card's own byte, and inside a slot the
    chassis the old words covered is rebuilt from the card's own clean rows and columns (below).
  * THE ART WINDOW is rebuilt for all four from one recipe, measured on the shipped cards: the window's dark
    glass (5.5, 5.3, 7.0), the ALARM wash from the top left in the left rail's colour and the CLASS wash from the
    bottom right in the class hue (two elliptical Gaussians fitted to the Archer + Breacher windows at 0.9 / 1.2
    levels rms; their geometry is shared), the 40 px scanlines, the shared crack and hairline scratches (the
    window's own detail, lifted from the Archer and Breacher windows where they hold no art), then the class's
    TIER-1 WEAPON drawn FROM THE GAME'S OWN MODEL with R2's technique (tools/artgen/packs/r2_card_subjects.py:
    an orthographic z-buffer of the xmodel_bin -> k-means flat regions coloured by art-directed probes -> three
    light bands, the navy outline, a pale class-hue rim) in a class-hue glow:
        NECROMANCER  the Skull of Nan Sapwe (wpn_t7_zmb_dlc2_keeper_head_view - the weapon tod_necro_skull draws),
                     three-quarter view: the carved head, its tribal markings, the open fanged jaw
        ARCHER       the Bow (wpn_t7_zmb_bow_base_view with cc_bow_d0s0_zm's hideTags applied: the four upgraded
                     arrowheads, the storm crystals and the rune rocks are hidden in game, and the 'no_e' wing
                     shells are a transparent alpha-test material), arrow nocked, the limbs' red ember eyes lit
        BREACHER     the Mozambique (vm_apex_mozambique: R2's view and R2's MOZ_STYLE, fitted to the shared box and
                     glowing in the Breacher's hue like the others)
        WARRIOR      the One Inch Punch: the gloved fist itself - the Archer's BO2 viewhands posed by the punch's
                     own wind-up (vm_zom_1inchpunch_charge, its clenched last frame) by linear-blend skinning, the
                     hand alone, seen from the palm side (the fingerless glove, the four fingers curled into it),
                     knuckles leading to the right like every other weapon on the row
    Every subject is fitted to the same box at the same centre, so the four read at one size.
  * THE WORDS are re-set in the map's typeface (the glyph-sheet cells TodGlyphRow draws in game, placed with the
    GENERATED TodGlyphMetrics.lua through artgen), one size per slot on every card:
        TIER 1        cap 54, the cell's white face, class-hue glow
        title         cap 35, white face, class-hue glow (inside the window); two lines when it cannot fit one
        class banner  cap 43, the face recoloured to the class accent (bevel + navy outline kept), class-hue glow
        weapon name   cap 58, white face, class-hue glow; two lines when it cannot fit one
    The glow model per slot is the shipped cards' own: two Gaussians of the glyph coverage, fitted per slot on the
    Archer and Breacher (header 0.40 @ 3 px + 0.25 @ 10 px; banner 0.50 @ 3 + 0.22 @ 8; name 0.36 @ 4 + 0.40 @ 10;
    the title takes the header's, a touch tighter), in each card's own glow hue (measured off its chassis: the
    Necromancer's neon green is purer than its accent).
  * THE OLD WORDS ARE REMOVED, NOT COVERED: the header and banner interiors are horizontal (flat fill, a top line,
    the banner's bar), so each interior row is rebuilt from the card's own columns the words never reached; the
    rows between the banner word and its bar carry the bar's glow, modelled from the bar's own core rows (three
    Gaussians, fitted on the rows below the bar and the columns no word reached); the name box is rebuilt whole from
    PK01's pinned name-box chassis (FLAT + the shared hairlines) + the four corner brackets - their strokes (one shape
    on every card) and PK01's bracket-glow template in each card's own glow colour (so all four boxes are built one
    way: the Necromancer's inner frame and the Warrior's top line go); the glow that spilled past a box onto the shared
    steel is taken back off by a per-pixel decomposition over the four cards (steel + glow x hue). The
    Necromancer's old beam, which ran out over the window frame onto the steel, is replaced by the steel and rail
    glow the other cards carry there.

USAGE
  python -B tools/artgen/packs/r6_class_cards.py                 # art/generated/R6-class-cards/ + _review.png
  python -B tools/artgen/packs/r6_class_cards.py --stage DIR     # also write the PNGs under DIR/source_data/tod_ui_images/_images/
  python -B tools/artgen/packs/r6_class_cards.py --install       # LANDING ONLY: write into source_data/tod_ui_images/_images/
  python -B tools/artgen/packs/r6_class_cards.py --check [--root DIR]
        BUILD GATE: regenerate in memory; fail on any byte that differs from the installed PNGs (or DIR's), on a
        source that is not the pinned one, and on any wiring break (GDT blocks, zone lines, the class-select
        registration, and the card words / accents against tod_class_select.lua's CLASSES table).
  python -B tools/artgen/packs/r6_class_cards.py --render        # re-rasterise the four models into the cache
        (needs PyCoD + the BO3 model bins; the cache under art/generated/R6-class-cards/src/ is the generator's
        input from then on, so --check needs neither)

SOURCES are the four shipped cards as they stood before this pass, copied to art/rebake_src/R6/ and pinned by
sha256 (never the installed file this overwrites). Deterministic: no randomness, no clock. Never hand-edit an
output; change this file and re-run it.
"""
import argparse, glob, hashlib, json, os, re, sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import artgen  # noqa: E402
import r2_card_subjects as r2  # noqa: E402  (the render + stylize library: raster, interp, stylize, down, rot, Z_UP)
import pk01_card_text_rebake as pk01  # noqa: E402  (the pinned name-box chassis, the bracket template, recolour)

PACK = 'R6-class-cards'
ROOT = artgen.ROOT
OUT = os.path.join(ROOT, 'art', 'generated', PACK)
SRC = os.path.join(OUT, 'src')                      # the render cache (albedo / normal / depth / mat / truth)
PIN_DIR = os.path.join(ROOT, 'art', 'rebake_src', 'R6')
IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images')
GDT_REL = os.path.join('source_data', 'tod_ui_images.gdt')
ZONE_REL = os.path.join('zone_source', 'zm_tod2_cybercity.zone')
CLS_LUA_REL = os.path.join('ui', 'uieditor', 'menus', 'hud', 'tod_class_select.lua')
BO3 = 'C:/BO3Tools/TOD2Cybercity/model_export'
W, H = 768, 1152

SOURCES = {   # the shipped cards as they stood before this pass (art/rebake_src/R6/)
    'i_tod_card_class_necromancer': 'fff13f1c62f5d5bd803913c06a91d21984764bdc29a692f45aaecd3ab54c7e37',
    'i_tod_card_class_assault':     'cff7ccb1325a9a48a66ea4648751098105b7052dbe335b64968f51f2c33ba69e',
    'i_tod_card_class_heavy':       '01ad3fab98a623b31b3b6b92d9f1f1a7672cf44909c4c8a3a2f21d9efc8f2e7d',
    'i_tod_card_class_slasher':     'c622470b366f4c9c2c95eae04a7fee1f6f8252342f4d80f4d07833c92b3f7a1e',
}
NAMES = ['i_tod_card_class_necromancer', 'i_tod_card_class_assault', 'i_tod_card_class_heavy', 'i_tod_card_class_slasher']

# id = tod_class_select.lua's class id (the draft order); face = its CLASSES[].accent x 255 (the banner word's fill,
# LOCKSTEP - --check reads the Lua); glow = the card's own glow hue, measured off its chassis (the header line's and
# the brackets' glow, the old words' fitted glow: all one direction per card); alarm = its left rail's colour.
# title = the role line in the art window, one tuple entry per line (one line at the shared cap; two when it cannot
# fit one - the name slot's rule). The words are the user's (2026-10-06: "Archer -> Agile Hunter / Breacher ->
# Explosive + Close Range Expert / Warrior -> Master of Arms"; the Necromancer's SOUL REAPER was kept).
CLASSES = {
    'i_tod_card_class_necromancer': dict(id=1, face=(140, 255, 115), glow=(0.10, 1.00, 0.00), alarm=(38.0, 5.0, 5.0),
                                         title=('SOUL REAPER',), banner='NECROMANCER', name=('SKULL OF', 'NAN SAPWE'),
                                         subject='skull'),
    'i_tod_card_class_assault':     dict(id=2, face=(255, 191, 64), glow=(1.00, 0.75, 0.25), alarm=(38.0, 5.0, 5.0),
                                         title=('AGILE HUNTER',), banner='ARCHER', name=('BOW',), subject='bow'),
    'i_tod_card_class_heavy':       dict(id=3, face=(255, 89, 77), glow=(1.00, 0.35, 0.30), alarm=(35.0, 24.0, 4.5),
                                         title=('EXPLOSIVE +', 'CLOSE RANGE EXPERT'), banner='BREACHER',
                                         name=('MOZAMBIQUE',), subject='moz'),
    'i_tod_card_class_slasher':     dict(id=4, face=(191, 115, 255), glow=(0.75, 0.45, 1.00), alarm=(38.0, 5.0, 5.0),
                                         title=('MASTER OF ARMS',), banner='WARRIOR', name=('ONE INCH', 'PUNCH'),
                                         subject='fist'),
}
LUM = np.array([0.299, 0.587, 0.114])


def sha256_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_source(name):
    p = os.path.join(PIN_DIR, name + '.png')
    if not os.path.isfile(p):
        raise SystemExit('R6: missing source %s (the shipped card as it stood before this pass)' % p)
    got = sha256_file(p)
    if got != SOURCES[name]:
        raise SystemExit('R6: source %s is not the pinned file (sha256 %s, found %s) - the generator re-bakes from the '
                         'pre-pass cards only' % (p, SOURCES[name], got))
    return np.asarray(Image.open(p).convert('RGBA'), dtype=np.float64)


def lum(a):
    return a[..., :3] @ LUM


def gauss(a, s):
    return ndi.gaussian_filter(a, s, mode='constant')

# ============================================================================================ THE SUBJECTS
# Each subject is rasterised into a 1136x936 canvas (the art window at 2x, placed at card (100, 172) like R2's
# Mozambique) and auto-fitted: its projected bounds are scaled to fit FIT_BOX and centred on FIT_AT, so all four
# share one size and one centre. view = (yaw, pitch, roll) after base Z_UP (model x -> screen right, z -> up).

CANVAS = (1136, 936)
WIN = (100, 172)                                  # the canvas's origin on the card (card px)
FIT_AT = (568, 548)                               # 2x canvas: card (384, 446), the window's centre below its title
FIT_BOX = (800, 584)                              # 2x canvas: 400 x 292 card px
KH = BO3 + '/black_ops_3/wpn_t7_zmb_dlc2_keeper_head/'
BW = BO3 + '/black_ops_3/wpn_t7_zmb_bow/'
HANDS = os.path.join(ROOT, 'model_export', 'tod_archer')
BOW_HIDE_TAGS = (   # cc_bow_d0s0_zm "hideTags" (source_data/tod_weapon_twins.gdt): what the base Bow never shows
    'tag_storm_crystal_lower_animate', 'tag_storm_crystal_upper_animate', 'tag_clip_storm', 'tag_clip_rune',
    'tag_clip_demon', 'tag_clip_wolf', 'tag_rune_rock_upper_2_animate', 'tag_rune_rock_upper_1_animate',
    'tag_rune_rock_lower_2_animate', 'tag_rune_rock_lower_1_animate')
SUBJECTS = {
    'skull': dict(model=KH + 'wpn_t7_zmb_dlc2_keeper_head_view.xmodel_bin',
                  tex={0: KH + '_images/i_wpn_t7_zmb_dlc2_keeper_mouth_c.png', 1: KH + '_images/i_wpn_t7_zmb_dlc2_keeper_head_c.png'},
                  view=(-70, 12, -6), fill=1.12),
    # material 12 (mtl_wpn_t7_zmb_bow_no_e) is lit_alphatest over $whitetransparent_color: invisible in game - dropped;
    # material 5 (base_e) is the limbs' emissive ember eyes (colorTint 0.61 0.07 0.04, scaleRGB 200)
    'bow': dict(model=BW + 'wpn_t7_zmb_bow_base_view.xmodel_bin', hide_tags=BOW_HIDE_TAGS, drop_mats=(12,),
                tex={0: BW + '_images/i_wpn_t7_zmb_bow_missile_c.png', 4: BW + '_images/i_wpn_t7_zmb_bow_base_handle_c.png',
                     5: BW + '_images/i_wpn_t7_zmb_bow_base_e_c.png', 6: BW + '_images/i_wpn_t7_zmb_bow_bone_c.png',
                     7: BW + '_images/i_wpn_t7_zmb_bow_base_c.png',
                     10: BW + '_images/i_wpn_t7_zmb_bow_base_missile_fletching_c.png'},
                view=(-30, 10, 36), fill=1.12),
    'moz': dict(r2.SUBJECTS['moz'], fill=0.92),
    # the One Inch Punch has no weapon model (the fist is the player's own hand): the Archer's BO2 viewhands posed by
    # the punch's OWN wind-up (its charge clip's last frame: the fist clenched), the right hand alone (wrist + finger
    # + palm bones), the forearm turned onto +X then rolled 270 degrees about it so the curled fingers face the viewer
    # and the knuckles lead to the right (r1_truth_render's fisth_r270 job, the same posing)
    'fist': dict(model=os.path.join(HANDS, 'tod_archer_bo2_hands.xmodel_bin'),
                 anim=os.path.join(ROOT, 'xanim_export', 'tod_warrior', 'vm_zom_1inchpunch_charge.XANIM_BIN'),
                 frame=20, side='_ri', bones=('wrist', 'index', 'mid', 'ring', 'pinky', 'thumb', 'palm'), xrot=270,
                 tex={0: os.path.join(HANDS, '_images', 'i_tod_archer_hands_0_col.png'),
                      1: os.path.join(HANDS, '_images', 'i_tod_archer_hands_1_col.png')},
                 view=(-20, 6, 8), fill=0.86),
}
SUBJECT_ORDER = ['skull', 'bow', 'moz', 'fist']


def _pycod():
    cands = sorted(glob.glob(os.path.join(os.environ.get('APPDATA', ''), 'Blender Foundation', 'Blender', '*',
                                          'scripts', 'addons', 'BetterBetterBlenderCOD')))
    if not cands:
        raise SystemExit('R6 --render: PyCoD (BetterBetterBlenderCOD) not found under %APPDATA%/Blender Foundation')
    sys.path.insert(0, cands[-1])
    from PyCoD import xmodel, xanim
    return xmodel, xanim


def load_plain(path, hide_tags=(), drop_mats=()):
    """every face of an xmodel_bin, less the faces a weapon's hideTags hide (a face goes when any corner's dominant
    bone is a hidden tag or hangs under one) and whole dropped materials"""
    xmodel, _ = _pycod()
    m = xmodel.Model()
    m.LoadFile_Bin(path)
    names = [b.name for b in m.bones]
    hidden = set()
    for i in range(len(m.bones)):
        p = i
        while p >= 0:
            if names[p] in hide_tags:
                hidden.add(i)
                break
            p = m.bones[p].parent
    P, N, U, M = [], [], [], []
    for mesh in m.meshes:
        vp = np.array([v.offset for v in mesh.verts], np.float64)
        top = [max(v.weights, key=lambda bw: bw[1])[0] if v.weights else 0 for v in mesh.verts]
        for f in mesh.faces:
            idx = [fv.vertex for fv in f.indices]
            if f.material_id in drop_mats or any(top[i] in hidden for i in idx):
                continue
            P.append(vp[idx])
            N.append([fv.normal for fv in f.indices])
            U.append([fv.uv for fv in f.indices])
            M.append(f.material_id)
    return np.array(P), np.array(N, np.float64), np.array(U, np.float64), np.array(M)


def _m4(off, mat):
    M = np.eye(4)
    M[:3, :3] = np.array(mat, np.float64).T          # PyCoD stores the axes as ROWS
    M[:3, 3] = off
    return M


def _rot_x(deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _rotation_between(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1.0 / (1.0 + c))


def load_posed(s):
    """linear-blend skinning of a viewhands model by one frame of an xanim (both store model-space transforms; a bone
    the clip does not drive rides its parent rigidly). Keeps the faces whose corners all belong to the chosen bones of
    one side; the forearm (elbow -> wrist) is turned onto +X about the wrist, then rolled s['xrot'] about it."""
    xmodel, xanim = _pycod()
    mdl = xmodel.Model()
    mdl.LoadFile_Bin(s['model'], split_meshes=False)
    a = xanim.Anim()
    a.LoadFile_Bin(s['anim'])
    idx = {p.name: i for i, p in enumerate(a.parts)}
    bind = [_m4(b.offset, b.matrix) for b in mdl.bones]
    pose = [None] * len(mdl.bones)
    for i, b in enumerate(mdl.bones):
        if b.name in idx:
            fp = a.frames[s['frame']].parts[idx[b.name]]
            pose[i] = _m4(fp.offset, fp.matrix)
        elif b.parent >= 0 and pose[b.parent] is not None:
            pose[i] = pose[b.parent] @ np.linalg.inv(bind[b.parent]) @ bind[i]
        else:
            pose[i] = bind[i]
    skin = [pose[i] @ np.linalg.inv(bind[i]) for i in range(len(bind))]
    names = [b.name for b in mdl.bones]
    src = mdl.meshes[0]
    pos, rots, keep = [], [], []
    for v in src.verts:
        acc, R = np.zeros(3), np.zeros((3, 3))
        for bi, w in v.weights:
            acc += w * (skin[bi] @ np.r_[v.offset, 1.0])[:3]
            R += w * skin[bi][:3, :3]
        pos.append(acc)
        rots.append(R)
        bn = names[max(v.weights, key=lambda bw: bw[1])[0]]
        keep.append((s['side'] + '_') in (bn + '_') and any(o in bn for o in s['bones']))
    elbow = pose[names.index('j_elbow' + s['side'])][:3, 3]
    wrist = pose[names.index('j_wrist' + s['side'])][:3, 3]
    Rp = _rot_x(s['xrot']) @ _rotation_between(wrist - elbow, np.array([1.0, 0.0, 0.0]))
    P, N, U, M = [], [], [], []
    for f in src.faces:
        vi = [f.indices[k].vertex for k in range(3)]
        if not all(keep[q] for q in vi):
            continue
        P.append([Rp @ (pos[q] - wrist) for q in vi])
        nn = []
        for k, q in enumerate(vi):
            n = Rp @ (rots[q] @ np.array(f.indices[k].normal))
            nn.append(n / (np.linalg.norm(n) + 1e-12))
        N.append(nn)
        U.append([f.indices[k].uv for k in range(3)])
        M.append(f.material_id)
    return np.array(P), np.array(N), np.array(U, np.float64), np.array(M)


def render_subject(name):
    """rasterise one subject into SRC in R2's buffer format (r2.load_buffers reads it once r2.SRC = SRC)"""
    s = SUBJECTS[name]
    if 'anim' in s:
        P, N, U, M = load_posed(s)
    else:
        P, N, U, M = load_plain(s['model'], s.get('hide_tags', ()), s.get('drop_mats', ()))
    R = r2.rot(*s['view'])
    base = s.get('base', r2.Z_UP)                   # R2's Mozambique carries base None: its own axes
    if base is not None:
        R = R @ np.array(base, float)
    S = P.reshape(-1, 3) @ R.T
    lo, hi = S.min(0), S.max(0)
    scale = min(FIT_BOX[0] / (hi[0] - lo[0]), FIT_BOX[1] / (hi[1] - lo[1])) * s.get('fill', 1.0)
    centre = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0.0])
    anchor = R.T @ centre                           # r2.raster maps anchor @ R.T onto `at`
    Wc, Hc = CANVAS
    tid, dep, XY = r2.raster(P, Wc, Hc, R, scale, anchor, FIT_AT)
    m = tid >= 0
    uv = r2.interp(tid, XY, U)
    n = r2.interp(tid, XY, N) @ R.T
    n /= (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9)
    mat = np.where(m, M[np.maximum(tid, 0)], 0)
    alb = np.zeros((Hc, Wc, 3))
    for mi, t in s['tex'].items():
        sel = m & (mat == mi)
        if not sel.any():
            continue
        if isinstance(t, tuple):
            alb[sel] = t
            continue
        T = np.asarray(Image.open(t).convert('RGB')).astype(np.float32) / 255
        u, v = np.mod(uv[..., 0], 1.0), np.mod(uv[..., 1], 1.0)
        c = T[(v * (T.shape[0] - 1)).astype(int), (u * (T.shape[1] - 1)).astype(int)]
        alb[sel] = c[sel]
    d = np.where(m, dep, 0)
    dlo, dhi = float(d[m].min()), float(d[m].max())
    dq = np.where(m, np.rint((d - dlo) / max(dhi - dlo, 1e-9) * 65000) + 100, 0).astype(np.uint16)
    os.makedirs(SRC, exist_ok=True)
    A = np.dstack([np.clip(alb, 0, 1) * 255, m * 255.0]).astype(np.uint8)
    artgen.save_png(Image.fromarray(A, 'RGBA'), os.path.join(SRC, name + '_albedo.png'), allow_any_size=True)
    nq = np.where(m[..., None], np.clip(np.rint(n * 127.5 + 127.5), 0, 255), 0).astype(np.uint8)
    Image.fromarray(nq, 'RGB').save(os.path.join(SRC, name + '_normal.png'), optimize=False, compress_level=9)
    Image.fromarray(dq).save(os.path.join(SRC, name + '_depth.png'), optimize=False, compress_level=9)
    Image.fromarray(mat.astype(np.uint8), 'L').save(os.path.join(SRC, name + '_mat.png'), optimize=False, compress_level=9)
    Ld = np.array([-0.3, 0.6, 0.75])
    Ld /= np.linalg.norm(Ld)
    sh = np.clip((n * Ld).sum(-1), 0, 1) * 0.75 + 0.35
    tr = np.where(m[..., None], np.clip(alb * sh[..., None] * 1.6, 0, 1), np.array([0.16, 0.17, 0.2]))
    artgen.save_png(Image.fromarray((tr * 255).astype(np.uint8), 'RGB').convert('RGBA'),
                    os.path.join(SRC, name + '_truth.png'), allow_any_size=True)
    meta = dict(model=os.path.basename(s['model']), model_sha256=r2.sha256(s['model']), view=list(s['view']),
                scale=round(float(scale), 6), anchor=[round(float(v), 6) for v in anchor], at=list(FIT_AT),
                canvas=list(CANVAS), depth_units=(dhi - dlo) / 65000.0, triangles=int(len(P)))
    if 'anim' in s:
        meta.update(anim=os.path.basename(s['anim']), anim_sha256=r2.sha256(s['anim']), frame=s['frame'], xrot=s['xrot'])
    return meta

# --------------------------------------------------------------------------------------------- the styles
# R2's stylize (r2_card_subjects.stylize) with one set of line weights for all four - the Mozambique's (R2's
# MOZ_STYLE: outline 5, inner line 1, rim 3 at 2x) - and a pale class-hue rim on each subject's top edges.

LINES = dict(outline_w=5, inner_w=1, rim_w=3, mult=(0.74, 1.0, 1.32), hl_add=0.06)

STYLES = {
    # the Keeper's head: carved wood in one brown (the light bands carry its form), its own black tribal markings
    # drawn crisp over the face (overlays), the ivory fangs, the dark mouth
    'skull': dict(LINES, med=9, maj=15, min_area=900, light=(-0.35, 0.72, 0.6), normal_blur=4.0, normal_blur_mats=(1,),
                  groups=[dict(mats=(1,), k=7, maj=15, probes=[
                      ((8, 8, 8), None),                                                   # the markings: overlaid
                      ((27, 21, 17), (90, 58, 42)),                                        # the deep crevices
                      ((58, 43, 33), (140, 94, 64)), ((71, 48, 37), (140, 94, 64)),        # the wood: ONE brown, its
                      ((84, 57, 43), (140, 94, 64)), ((90, 63, 46), (140, 94, 64)),        # grain would read as camo
                      ((102, 73, 52), (140, 94, 64))]),
                          dict(mats=(0,), k=5, maj=9, probes=[
                      ((57, 39, 27), (88, 46, 40)), ((70, 51, 37), (88, 46, 40)),          # the gums / mouth
                      ((87, 77, 57), (230, 216, 180)), ((105, 94, 74), (230, 216, 180)),   # the fangs: ivory
                      ((125, 116, 92), (230, 216, 180))])],
                  overlays=[dict(mats=(1,), max_l=0.06, rgb=(34, 26, 28), med=3, min_px=30)]),
    # the Bow: the black iron of its limbs in one tone, the weathered bone between in two, the red-brown grip wrap,
    # the dark arrow and its deep-red fletching, the string; the base_e ember eyes self-lit
    'bow': dict(LINES, med=5, maj=11, min_area=220, light=(-0.35, 0.72, 0.6), crease_cos=0.5,
                groups=[dict(mats=(7,), k=3, maj=11, probes=[
                    ((16, 16, 15), (64, 66, 84)), ((22, 22, 21), (64, 66, 84)), ((29, 27, 25), (64, 66, 84))]),
                        dict(mats=(6,), k=5, maj=11, probes=[
                    ((40, 29, 20), (78, 62, 46)), ((61, 45, 27), (122, 100, 70)), ((71, 55, 35), (122, 100, 70)),
                    ((80, 64, 42), (150, 128, 92)), ((92, 79, 59), (150, 128, 92))]),
                        dict(mats=(4,), k=3, maj=7, probes=[
                    ((54, 22, 14), (150, 62, 46)), ((9, 4, 2), (90, 38, 32)), ((61, 36, 25), (150, 62, 46))]),
                        dict(mats=(0, 10), k=4, maj=5, probes=[
                    ((4, 4, 4), (44, 46, 60)), ((14, 13, 13), (44, 46, 60)), ((50, 38, 28), (96, 80, 66)),
                    ((47, 4, 2), (168, 44, 40))])],
                emit={5: ((255, 120, 70), True)}, keep_mats=(5, 4, 0, 10),
                min_area_by={(168, 44, 40): 30, (96, 80, 66): 60}),
    'moz': r2.MOZ_STYLE,
    # the clenched fist: the black knit glove in one tone (the light bands carry its form), the steel rims of the
    # knuckle guards, the bare curled fingers, thumb and wrist in one skin tone; the blood grime is absorbed
    'fist': dict(LINES, med=7, maj=13, min_area=500, light=(-0.35, 0.72, 0.6), t1=0.02, normal_blur=4.0,
                 groups=[dict(mats=(0,), k=8, maj=13, probes=[
                     ((25, 18, 18), (68, 70, 90)), ((26, 24, 24), (68, 70, 90)), ((30, 27, 28), (68, 70, 90)),
                     ((35, 34, 36), (68, 70, 90)), ((43, 26, 27), (68, 70, 90)), ((59, 43, 43), None),
                     ((103, 69, 67), (214, 148, 126)), ((138, 94, 92), (214, 148, 126))]),
                         dict(mats=(1,), k=4, maj=7, probes=[
                     ((21, 21, 21), (44, 46, 60)), ((36, 36, 36), (82, 86, 106)), ((53, 51, 51), (130, 136, 156)),
                     ((83, 75, 73), (184, 190, 208))])],
                 min_area_by={(184, 190, 208): 30, (130, 136, 156): 40}),
}


def bind_cache():
    """point R2's buffer reader at this pack's cache"""
    r2.SRC = SRC


def light_mult(buf, st):
    """r2.stylize's three light bands as the multiplier it applies (shadow / base / lit top facet)"""
    n, m = buf['n'], buf['m']
    Ld = np.array(st.get('light', (-0.35, 0.75, 0.55)), float)
    Ld /= np.linalg.norm(Ld)
    ndl = (n * Ld).sum(-1)
    band = np.where(ndl < st.get('t1', 0.12), 0, np.where(ndl < st.get('t2', 0.66), 1, 2))
    band = np.where(n[..., 1] > st.get('top_y', 0.42), 2, band)
    band = np.where(n[..., 1] < st.get('bot_y', -0.45), 0, band)
    band = ndi.median_filter(np.where(m, band, 1), size=7)
    return np.array(st.get('mult', (0.70, 1.0, 1.20)))[band]


def overlays(arr, buf, st):
    """painted detail too fine for the flat regions (the median and the majority filters erase it): the Skull's
    tribal markings - its own colour map's near-black strokes, read off the unsmoothed albedo - drawn over the flat
    wood in the light band of the surface under them"""
    if not st.get('overlays'):
        return arr
    mm = light_mult(buf, st)
    L = buf['alb'] @ LUM
    for ov in st['overlays']:
        sel = buf['m'] & np.isin(buf['mat'], ov['mats'])
        mk = ndi.median_filter((L < ov['max_l']) & sel, size=ov.get('med', 3))
        lab, k = ndi.label(mk)
        if k:
            sizes = ndi.sum(mk, lab, range(1, k + 1))
            mk = np.isin(lab, np.nonzero(sizes >= ov.get('min_px', 24))[0] + 1)
        mk &= ~ndi.binary_dilation(~buf['m'], iterations=ov.get('inset', 3))
        rgb = np.array(ov['rgb'], float)[None, None, :] / 255.0 * mm[..., None]
        arr[..., :3] = np.where(mk[..., None], rgb, arr[..., :3])
    return arr


def subject(name, rim):
    bind_cache()
    st = dict(STYLES[name])
    if name != 'moz':
        st['rim'] = rim
    buf = r2.load_buffers(name)
    if st.get('normal_blur'):                       # sculpted, noisy surfaces (the carved head, the knit glove): smooth
        nb = np.stack([ndi.gaussian_filter(buf['n'][..., k], st['normal_blur']) for k in range(3)], -1)   # the
        sel = buf['m'] & np.isin(buf['mat'], st.get('normal_blur_mats', np.unique(buf['mat'])))
        buf['n'] = np.where(sel[..., None], nb / (np.linalg.norm(nb, axis=-1, keepdims=True) + 1e-9), buf['n'])
    arr = overlays(r2.stylize(buf, st), buf, st)      # normals so the light bands follow the form, not the grain
    emit = np.zeros(buf['m'].shape)
    for mi in st.get('emit', {}):
        emit = np.maximum(emit, (buf['mat'] == mi) & buf['m'])
    return r2.down(arr), emit

# =============================================================================================== THE WINDOW

WIN_Y = (175, 637)                                 # the window interior: rows 175..636, x 103..664 (frame 172-174 /
WIN_X = (103, 665)                                 # 637-640, x 100-102 / 665-668)
WIN_BASE = np.array([5.47, 5.34, 7.03])            # the glass, far from both washes
WASH_A = (195.05, 307.57, 69.85, 102.65)           # the alarm wash: centre x, y, sigma x, y (fitted, card px)
WASH_B = (570.28, 520.43, 68.07, 83.31)            # the class wash
WASH_B_PEAK = 29.5                                 # the class wash's brightest channel (Archer 29.5, Breacher 28.9)
SCAN_PERIOD, SCAN_PHASE = 40, 2                    # rows y = 2 mod 40, 202..602
SCAN_RGB = np.array([15.0, 15.0, 18.5])
SCAN_SIDE = 1.0                                    # the rows either side
SUBJ_GLOW = ((16.0, 1.5, 0.55, 0.75, 0.00, 5),     # (sigma, gain, strength, hue scale, white mix, alpha grown by px):
             (4.0, 1.6, 0.50, 1.00, 0.12, 0))     # R2's two glows (the Mozambique's 190,104,30 / 255,150,52 = its
                                                  # orange x 0.75 / x 1.0); the wide one round the silhouette grown 5 px,
                                                  # so a thin subject (the Bow) carries as full a halo as a solid one
TITLE_CAP = 35.0                                   # the title's cap (its white fill centred on row 233)
TITLE_MAX_W = WIN_X[1] - WIN_X[0] - 2 * 24         # a title line's widest (card px): the window less a 24 px margin


def window_mask():
    """(interior mask, boundary ring) for the window: the area the frame encloses, read off the Archer (the frame is
    shared). The ring = the interior's outer 2 px (the frame's anti-aliasing and its inner shadow line)."""
    a = load_source('i_tod_card_class_assault')
    L = lum(a)
    ring = np.zeros(L.shape, bool)
    ring[168:645, 96:673] = L[168:645, 96:673] > 50
    ring &= ~np.pad(np.ones((WIN_Y[1] - WIN_Y[0] - 8, WIN_X[1] - WIN_X[0] - 8), bool),
                    ((WIN_Y[0] + 4, H - WIN_Y[1] + 4), (WIN_X[0] + 4, W - WIN_X[1] + 4)))
    inside = ndi.binary_fill_holes(ring) & ~ring
    inner = ndi.binary_erosion(inside, iterations=2)
    return inside, inside & ~inner


def wash(cx, cy, sx, sy):
    ys, xs = np.mgrid[0:H, 0:W]
    return np.exp(-0.5 * (((xs - cx) / sx) ** 2 + ((ys - cy) / sy) ** 2))


def window_lighting(cls):
    c = CLASSES[cls]
    hue = np.array(c['glow'])
    bg = (WIN_BASE[None, None, :] + wash(*WASH_A)[..., None] * np.array(c['alarm'])[None, None, :]
          + wash(*WASH_B)[..., None] * (hue / hue.max() * WASH_B_PEAK)[None, None, :])
    return bg


_DETAIL = None


def window_detail():
    """the window's shared fine detail - the crack in the top-right corner and the hairline scratches - as a signed
    layer: the high-pass (minus an 11 px median) of the Archer's and the Breacher's windows, each where it holds no
    art and no title (they share the chassis; the two cover each other's art), scanlines taken out."""
    global _DETAIL
    if _DETAIL is not None:
        return _DETAIL
    out = np.zeros((H, W, 3))
    got = np.zeros((H, W), bool)
    for name, art, title in (('i_tod_card_class_assault', (170, 640, 262, 560), (230, 540, 198, 268)),
                             ('i_tod_card_class_heavy', (190, 602, 322, 552), (140, 625, 198, 268))):
        a = load_source(name)[..., :3]
        hp = a - np.stack([ndi.median_filter(a[..., k], size=11) for k in range(3)], -1)
        for y in range(WIN_Y[0], WIN_Y[1]):
            if (y - SCAN_PHASE) % SCAN_PERIOD in (SCAN_PERIOD - 1, 0, 1):
                hp[y] -= np.median(hp[y, WIN_X[0]:WIN_X[1]], axis=0)
        clean = np.ones((H, W), bool)
        for x0, x1, y0, y1 in (art, title):
            clean[y0:y1, x0:x1] = False
        clean = ndi.binary_erosion(clean, iterations=6)
        take = clean & ~got
        out[take] = hp[take]
        got |= take
    inside, ring = window_mask()
    out[~(inside & ~ring)] = 0.0
    out[np.abs(out).max(-1) < 1.0] = 0.0               # flat glass: nothing
    _DETAIL = out
    return out


def scanlines():
    s = np.zeros((H, W, 3))
    for y in range(WIN_Y[0], WIN_Y[1]):
        k = (y - SCAN_PHASE) % SCAN_PERIOD
        if k == 0:
            s[y, WIN_X[0]:WIN_X[1]] = SCAN_RGB
        elif k in (1, SCAN_PERIOD - 1):
            s[y, WIN_X[0]:WIN_X[1]] = SCAN_SIDE
    return s


def lerp_glow(base, alpha, rgb, sigma, gain, strength):
    g = np.clip(gauss(alpha, sigma) * gain, 0, 1) * strength
    return base * (1 - g[..., None]) + np.asarray(rgb, float)[None, None, :] * g[..., None]


def build_window(card, cls, subj_img, emit):
    """the art window, rebuilt: glass + washes + scanlines + the shared detail, the subject's class-hue glow, the
    subject, its emissive bloom; written inside the frame (the frame's 2 px ring keeps its own light: the Archer's
    ring minus the Archer's glass, over the new glass)."""
    c = CLASSES[cls]
    hue = np.array(c['glow'])
    hue = hue / hue.max()
    inside, ring = window_mask()
    bg = window_lighting(cls) + scanlines() + window_detail()
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    lay.paste(subj_img, WIN)
    lay = np.asarray(lay, dtype=np.float64)
    a = lay[..., 3] / 255.0
    for sigma, gain, strength, scale, wmix, grow in SUBJ_GLOW:
        rgb = (hue * (1 - wmix) + wmix) * 255.0 * scale
        aa = ndi.grey_dilation(a, footprint=pk01.disc(grow)) if grow else a
        bg = lerp_glow(bg, aa, rgb, sigma, gain, strength)
    out = bg * (1 - a[..., None]) + lay[..., :3] * a[..., None]
    if emit.any():                                  # self-lit parts bloom a little (R5's neon_glow idiom)
        e = np.asarray(Image.fromarray((emit * 255).astype(np.uint8)).resize(subj_img.size, Image.LANCZOS),
                       dtype=np.float64) / 255.0
        E = np.zeros((H, W))
        E[WIN[1]:WIN[1] + e.shape[0], WIN[0]:WIN[0] + e.shape[1]] = e
        out = lerp_glow(out, E, (255, 110, 64), 3.0, 3.0, 0.55)
    # the frame's ring: the Archer's light there over the Archer's glass, moved onto this glass
    arch = load_source('i_tod_card_class_assault')[..., :3]
    arch_bg = window_lighting('i_tod_card_class_assault') + scanlines()
    ring_px = np.clip(arch + (bg - arch_bg), 0, 255)
    res = card.copy()
    m = inside & ~ring
    res[m, :3] = out[m]
    res[ring, :3] = ring_px[ring]
    return res, inside

# ================================================================================================ THE WORDS

SS = 4


def text_layer(lines, cap, cy, cx=383.5, face=None, leading=0.24, track=0.0):
    """the words in the map's typeface as straight RGBA float (H, W, 4) at card size (drawn at 4x, box-filtered
    premultiplied): each line centred on cx; the block's white fill centred on row cy (fill = 0.875 cap, measured).
    face: recolour the glyph fill (pk01.recolour: the bevel and the navy outline stay)."""
    M = artgen.metrics()
    n = len(lines)
    pitch = cap * (1.0 + leading)
    fill_h = 0.875 * cap
    top_fill = cy - (fill_h + (n - 1) * pitch) / 2.0
    cells = []                                       # (glyph cell at 4x, its 4x position)
    for i, text in enumerate(lines):
        baseline = top_fill + i * pitch + fill_h + 0.02 * cap
        total = artgen.text_width(text, cap) + track * cap * (len(text) - 1)
        pen = cx - total / 2.0
        first = True
        for ch in text:
            if ch == ' ':
                pen += M['letters']['cw'] * (cap / M['letters']['cap']) * artgen.TOD_SPACE_ADV + track * cap
                first = False
                continue
            sname, key, imgname = artgen._glyph(ch)
            S = M[sname]
            s = cap / S['cap']
            adv, gx = S['g'][key]
            if not first:
                pen += cap * (artgen.TOD_TRACK + track)
            left, topy = pen - gx * s, baseline - S['baseline'] * s
            cw, chh = int(round(S['cw'] * s * SS)), int(round(S['ch'] * s * SS))
            cell = artgen._cell(imgname).resize((cw, chh), Image.LANCZOS)
            if face is not None:
                cell = pk01.recolour(cell, face)
            cells.append((cell, int(round(left * SS)), int(round(topy * SS))))
            pen += adv * s
            first = False
    # draw on the words' own box (aligned to whole card pixels, so the 4x box filter lands exactly where a full-card
    # layer's would), then place it on the card
    X0 = max(0, min(x for _, x, _ in cells) // SS - 1)
    Y0 = max(0, min(y for _, _, y in cells) // SS - 1)
    X1 = min(W, -(-max(x + c.width for c, x, _ in cells) // SS) + 1)
    Y1 = min(H, -(-max(y + c.height for c, _, y in cells) // SS) + 1)
    layer = Image.new('RGBA', ((X1 - X0) * SS, (Y1 - Y0) * SS), (0, 0, 0, 0))
    for cell, x, y in cells:
        layer.alpha_composite(cell, (x - X0 * SS, y - Y0 * SS))
    a = np.asarray(layer, dtype=np.float64)
    pre = np.dstack([a[..., :3] * a[..., 3:4] / 255.0, a[..., 3:4] / 255.0])
    pre = pre.reshape(Y1 - Y0, SS, X1 - X0, SS, 4).mean(axis=(1, 3))
    al = pre[..., 3]
    rgb = np.where(al[..., None] > 1e-6, pre[..., :3] / np.maximum(al, 1e-6)[..., None], 0.0)
    out = np.zeros((H, W, 4))
    out[Y0:Y1, X0:X1] = np.dstack([rgb, al])
    return out


# (sigma, amplitude) pairs: amplitude x 255 x the card's glow hue, added over the background (the shipped cards' own
# fitted glow per slot)
GLOW = {'header': ((3.0, 0.40), (10.0, 0.25)), 'title': ((3.0, 0.40), (9.0, 0.22)),
        'banner': ((3.0, 0.50), (8.0, 0.22)), 'name': ((4.0, 0.36), (10.0, 0.40))}
SLOTS = {   # cap, fill centre row
    'header': (54.0, 111.0),
    'title': (TITLE_CAP, 233.0),
    'banner': (43.0, 695.5),
    'name': (58.0, 854.5),
}


def put_words(img, lay, slot, cls, clip=None):
    hue = np.array(CLASSES[cls]['glow'])
    hue = hue / hue.max()
    a = lay[..., 3]
    g = np.zeros((H, W, 3))
    for sigma, amp in GLOW[slot]:
        g += gauss(a, sigma)[..., None] * (amp * 255.0 * hue)[None, None, :]
    g *= (1.0 - a)[..., None]
    if clip is not None:
        g *= clip[..., None]
    out = img[..., :3] + g
    out = out * (1 - a[..., None]) + lay[..., :3] * a[..., None]
    res = img.copy()
    res[..., :3] = out
    return res

# ======================================================================================= THE OLD WORDS, REMOVED


def row_rebuild(card, rows, cols_dirty, cols_clean):
    """rows y0..y1 of an interior that is constant along x: each row's median over the clean columns, written over
    the dirty columns"""
    out = card.copy()
    cc = np.concatenate([np.arange(a, b) for a, b in cols_clean])
    for y in range(rows[0], rows[1]):
        v = np.median(card[y, cc, :3], axis=0)
        out[y, cols_dirty[0]:cols_dirty[1], :3] = v
    return out


def text_zone(card_rgb, box, white=True, face=None, reach=30):
    """the old words' silhouette in a box (white fill, or the accent fill) and its glow zone (reach px)"""
    x0, y0, x1, y1 = box
    sub = card_rgb[y0:y1, x0:x1]
    if white:
        fill = sub.min(-1) > 200
    else:
        fill = np.abs(sub - np.asarray(face, float) * 0.92).max(-1) < 40
    fill = ndi.binary_opening(fill, iterations=1)
    m = np.zeros(card_rgb.shape[:2], bool)
    m[y0:y1, x0:x1] = fill
    z = np.zeros_like(m)
    if m.any():                                      # dilated on the box + its reach (the rest stays empty)
        a0, a1, b0, b1 = max(0, y0 - reach), min(H, y1 + reach), max(0, x0 - reach), min(W, x1 + reach)
        z[a0:a1, b0:b1] = ndi.binary_dilation(m[a0:a1, b0:b1], structure=pk01.disc(reach))
    return m, z


def despill(cards, region, dirty):
    """take the old words' glow off the shared steel in `region`. Every card there = steel S + g_c x hue_c (the steel
    and the frame are one chassis; the glow is the card's hue). Per pixel, least squares over the cards (S: 3 unknowns,
    one g per card), then g_c's per-row level outside the dirty columns (the chassis's own light: a top line's glow)
    is kept and only the excess - the words' spill - is removed."""
    names = list(cards)
    ys, xs = np.nonzero(region)                      # worked on the region's box; everything else is untouched
    r0, r1, c0, c1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    region, dirty = region[r0:r1, c0:c1], dirty[r0:r1, c0:c1]
    P = np.stack([cards[n][r0:r1, c0:c1, :3] for n in names])
    Hh = np.stack([np.array(CLASSES[n]['glow']) / np.linalg.norm(CLASSES[n]['glow']) for n in names])
    S = P.min(0)
    for _ in range(12):
        g = np.clip(((P - S[None]) * Hh[:, None, None, :]).sum(-1), 0, None)
        S = (P - g[..., None] * Hh[:, None, None, :]).mean(0)
    out = {}
    for i, n in enumerate(names):
        base = np.zeros(g.shape[1:])
        ys = np.nonzero(region.any(1))[0]
        for y in ys:
            clean = region[y] & ~dirty[y]
            base[y] = np.median(g[i, y, clean]) if clean.any() else 0.0
        t = np.clip(g[i] - base, 0, None) * (region & dirty)
        res = cards[n].copy()
        res[r0:r1, c0:c1, :3] = P[i] - t[..., None] * Hh[i][None, None, :]
        out[n] = res
    return out


# ---- the header -------------------------------------------------------------------------------------------------
HDR_BOX = (71, 149)                       # the box rows rebuilt row by row (frame 72-74 + its top line 75-77, the
HDR_DIRTY = (232, 536)                    # interior, the shadow 144 and the frame 145-148); the words' columns
HDR_CLEAN = [(150, 232), (536, 625)]      # the screws sit at x ~113 / ~655, outside these
HDR_SPILL = (52, 172)                     # rows of steel round the box the words' glow reached


def clear_header(cards):
    out = {n: row_rebuild(c, HDR_BOX, HDR_DIRTY, HDR_CLEAN) for n, c in cards.items()}
    region = np.zeros((H, W), bool)
    region[HDR_SPILL[0]:HDR_BOX[0], 150:625] = True
    region[HDR_BOX[1]:HDR_SPILL[1], 150:625] = True
    dirty = np.zeros((H, W), bool)
    dirty[:, HDR_DIRTY[0]:HDR_DIRTY[1]] = True
    return despill(out, region, dirty)


# ---- the banner -------------------------------------------------------------------------------------------------
BAN_IN = (665, 733, 153, 615)             # interior rows / cols (frame 662-664 / 733-736, x 150-152 / 615-618)
BAN_TEXT_ROWS = (665, 690)                # rows above the bar's reach: rebuilt row by row (flat + the frame's shading)
BAN_GLOW_ROWS = (690, 727)                # down to the bar: the flat interior + the bar's glow, modelled
BAN_CORE = (727, 730)                     # the bar's core rows (its pieces' bright centres); rows 730-731 its glow below
BAN_SPILL = (641, 665)                    # steel + the frame top above the box
BAR_SIGMAS = ((1.5, 2.0, 3.0), (4.0, 5.0, 6.0), (9.0, 12.0, 16.0))
BAR_MARGIN = 56                           # px: 3.5 x the widest bar-glow sigma
FEATHER_X = 18.0                          # px past the words' columns over which the modelled rows fade into the card's own


def bar_glow(card, flat, clean_cols):
    """the banner bar's glow as three Gaussians of its own core rows (each channel its own three gains, non-negative
    least squares), fitted on the rows just below the bar (every column: no word reaches there) and on the rows above
    it in the columns no word reached. Worked on the box plus a margin past the widest sigma's reach (the core is zero
    outside the box, so the crop changes nothing). Returns the modelled glow (H, W, 3) and the fit's rms."""
    from scipy.optimize import nnls
    y0, y1, x0, x1 = BAN_IN
    m = BAR_MARGIN
    cy0, cy1, cx0, cx1 = y0 - m, y1 + m, x0 - m, x1 + m
    crop = card[cy0:cy1, cx0:cx1, :3]
    Q = np.zeros(crop.shape)
    Q[BAN_CORE[0] - cy0:BAN_CORE[1] - cy0, x0 + 2 - cx0:x1 - 2 - cx0] = np.clip(
        crop[BAN_CORE[0] - cy0:BAN_CORE[1] - cy0, x0 + 2 - cx0:x1 - 2 - cx0] - flat, 0, None)
    fit = np.zeros(crop.shape[:2], bool)
    fit[BAN_CORE[1] - cy0:BAN_CORE[1] + 2 - cy0, x0 + 6 - cx0:x1 - 6 - cx0] = True
    for a, b in clean_cols:
        fit[BAN_GLOW_ROWS[0] - cy0:BAN_CORE[0] - 1 - cy0, a - cx0:b - cx0] = True
    T = crop - flat
    gq = {}
    for sg in sorted(set(v for row in BAR_SIGMAS for v in row)):
        gq[sg] = [gauss(Q[..., k], sg) for k in range(3)]
    best = None
    for s1 in BAR_SIGMAS[0]:
        for s2 in BAR_SIGMAS[1]:
            for s3 in BAR_SIGMAS[2]:
                Gc = np.zeros(crop.shape)
                err = 0.0
                for k in range(3):
                    gs = [gq[sg][k] for sg in (s1, s2, s3)]
                    co, r = nnls(np.stack([g[fit] for g in gs], 1), T[..., k][fit])
                    Gc[..., k] = sum(c * g for c, g in zip(co, gs))
                    err += r * r
                if best is None or err < best[0]:
                    best = (err, Gc)
    err, Gc = best
    G = np.zeros((H, W, 3))
    G[cy0:cy1, cx0:cx1] = Gc
    return G, float(np.sqrt(err / (3 * fit.sum())))


def clear_banner(cards):
    out = {}
    rms = {}
    for n, card in cards.items():
        c = CLASSES[n]
        _, zone = text_zone(card[..., :3], (BAN_IN[2], BAN_IN[0], BAN_IN[3], 720), white=False,
                            face=c['face'], reach=26)
        cols = np.nonzero(zone.any(0))[0]
        dx0, dx1 = int(cols.min()), int(cols.max()) + 1
        clean = [(BAN_IN[2] + 2, max(BAN_IN[2] + 4, dx0)), (min(BAN_IN[3] - 4, dx1), BAN_IN[3] - 2)]
        res = row_rebuild(card, (BAN_IN[0], BAN_TEXT_ROWS[1]), (dx0, dx1), clean)
        cc = np.r_[clean[0][0]:clean[0][1], clean[1][0]:clean[1][1]]
        flat = np.median(card[680:688, cc, :3].reshape(-1, 3), axis=0)
        G, rms[n] = bar_glow(card, flat, clean)
        model = flat + G
        xs = np.arange(W)
        out_d = np.maximum(dx0 - xs, xs - (dx1 - 1)).clip(0, None)     # 0 inside the words' columns
        wx = np.clip(1.0 - out_d / FEATHER_X, 0, 1)                   # the model fades out over clean columns
        wx[(xs < BAN_IN[2]) | (xs >= BAN_IN[3])] = 0.0
        ys = slice(BAN_GLOW_ROWS[0], BAN_GLOW_ROWS[1])
        res[ys, :, :3] = model[ys] * wx[None, :, None] + card[ys, :, :3] * (1 - wx[None, :, None])
        out[n] = res
    region = np.zeros((H, W), bool)
    region[BAN_SPILL[0]:BAN_SPILL[1], 140:628] = True
    dirty = np.zeros((H, W), bool)
    dirty[:, 170:600] = True
    clear_banner.rms = rms
    return despill(out, region, dirty)


# ---- the name box -------------------------------------------------------------------------------------------------
NB = (pk01.Y0, pk01.Y1, pk01.X0, pk01.X1)  # rows 763..945, x 104..663: the box inside its frame (PK01's chassis crop)
ARM_ROWS = ((782, 800), (910, 928))        # the brackets' vertical arms, clear of every horizontal line


def clear_namebox(cards):
    """the whole interior rebuilt one way for every card: PK01's pinned chassis (FLAT + the shared hairlines) + the
    four corner brackets - this card's own stroke pixels inside PK01's stroke mask (the strokes are one shape on every
    card; the Necromancer's inner frame and the Warrior's top line run outside it and go) and PK01's bracket-glow
    template scaled per channel to this card's glow, fitted on its vertical arms (clear of every horizontal line)"""
    y0, y1, x0, x1 = NB
    chassis = pk01.load_chassis()
    strokes, zone, lumT = pk01.bracket_template()
    keep = ndi.binary_dilation(strokes, iterations=1)   # PK01's: the strokes are one shape on every card
    arms = np.zeros(keep.shape, bool)
    for a, b in ARM_ROWS:
        arms[a - y0:b - y0] = True
    glow_px = zone & ~keep & arms
    out = {}
    for n, card in cards.items():
        win = card[y0:y1, x0:x1, :3]
        D = win - chassis
        t = lumT[glow_px]
        kc = np.array([float(np.sum(D[..., k][glow_px] * t) / np.sum(t * t)) for k in range(3)])
        bg = chassis + lumT[..., None] * kc[None, None, :]
        bg[keep] = win[keep]                          # the strokes: this card's own pixels
        res = card.copy()
        res[y0:y1, x0:x1, :3] = np.clip(bg, 0, 255)
        out[n] = res
    return out


# ---- the necromancer's beam, out over the window frame ------------------------------------------------------------
BEAM = (322, 462, 665, 693)                # rows / cols where the old beam crossed the frame and the steel


def repair_beam(cards):
    """those pixels from the cards that are clean there: necro = Archer + M (Warrior - Archer), the 3x3 map M fitted on
    the rows above and below (the difference between two cards there is only the rail's glow in two hues)"""
    n = 'i_tod_card_class_necromancer'
    a = cards['i_tod_card_class_assault'][..., :3]
    w = cards['i_tod_card_class_slasher'][..., :3]
    c = cards[n][..., :3]
    y0, y1, x0, x1 = BEAM
    fit = np.zeros((H, W), bool)
    fit[250:y0 - 4, x0:x1] = True
    fit[y1 + 4:560, x0:x1] = True
    X = np.concatenate([(w - a)[fit], np.ones((fit.sum(), 1))], 1)
    Y = (c - a)[fit]
    M, *_ = np.linalg.lstsq(X, Y, rcond=None)
    pred = a + np.concatenate([(w - a), np.ones((H, W, 1))], -1) @ M
    res = cards[n].copy()
    res[y0:y1, x0:x1, :3] = np.clip(pred[y0:y1, x0:x1], 0, 255)
    out = dict(cards)
    out[n] = res
    return out, float(np.sqrt(((X @ M - Y) ** 2).mean()))

# ============================================================================================= THE CARDS


def build_all():
    src = {n: load_source(n) for n in NAMES}
    cards, info = repair_beam(src)
    cards = clear_header(cards)
    cards = clear_banner(cards)
    cards = clear_namebox(cards)
    out, meta = {}, {}
    build_all.cleared = cards                       # the review's evidence: every slot with its old words removed
    build_all.subjects = {}
    for n in NAMES:
        c = CLASSES[n]
        hue = np.array(c['glow']) / max(c['glow'])
        rim = tuple(int(round(v)) for v in (hue * 0.55 + 0.45) * 255)
        subj, emit = subject(c['subject'], rim)
        build_all.subjects[n] = subj
        card, inside = build_window(cards[n], n, subj, emit)
        cap, cy = SLOTS['header']
        card = put_words(card, text_layer(['TIER 1'], cap, cy), 'header', n)
        cap, cy = SLOTS['title']
        for line in c['title']:                     # a line the window would clip fails here, never silently
            if artgen.text_width(line, cap) > TITLE_MAX_W:
                raise SystemExit('R6: title line %r is %.0f px at cap %.0f; the window holds %d - break it in two'
                                 % (line, artgen.text_width(line, cap), cap, TITLE_MAX_W))
        card = put_words(card, text_layer(list(c['title']), cap, cy), 'title', n, clip=inside.astype(float))
        cap, cy = SLOTS['banner']
        card = put_words(card, text_layer([c['banner']], cap, cy, face=c['face']), 'banner', n)
        cap, cy = SLOTS['name']
        nb = np.zeros((H, W))
        nb[NB[0]:NB[1], NB[2]:NB[3]] = 1.0
        card = put_words(card, text_layer(list(c['name']), cap, cy), 'name', n, clip=nb)
        rgb = np.clip(np.round(card[..., :3]), 0, 255)
        out[n] = Image.fromarray(np.dstack([rgb, src[n][..., 3]]).astype(np.uint8), 'RGBA')
        meta[n] = dict(subject=c['subject'], words=['TIER 1', ' / '.join(c['title']), c['banner'], ' / '.join(c['name'])])
    meta['beam_fit_rms'] = round(info, 2)
    meta['bar_fit_rms'] = {n.replace('i_tod_card_class_', ''): round(v, 2) for n, v in clear_banner.rms.items()}
    return out, meta

# ============================================================================================== review


def onscreen_draft(cards, scale=1.5):
    """the draft row as tod_class_select.lua lays it out (CARD_W 210, CARD_PITCH 298, CCARD_Y0 210, 1.5 card
    heights; a 1280x720 canvas) at 1080p (x1.5), on the in-game sky dimmed like R3's draft mock"""
    Wc, Hc = int(1280 * scale), int(720 * scale)
    sky = os.path.join(ROOT, 'docs', 'sky_preview', 'evil_ingame_city.png')
    canvas = (Image.open(sky).convert('RGBA').resize((Wc, Hc), Image.LANCZOS) if os.path.exists(sky)
              else Image.new('RGBA', (Wc, Hc), (20, 16, 30, 255)))
    canvas.alpha_composite(Image.new('RGBA', (Wc, Hc), (6, 4, 12, 150)))
    x0 = (1280 - (3 * 298 + 210)) // 2
    for i, im in enumerate(cards):
        r = im.resize((int(round(210 * scale)), int(round(315 * scale))), Image.LANCZOS)
        canvas.alpha_composite(r, (int(round((x0 + i * 298) * scale)), int(round(210 * scale))))
    return canvas


def _stretch(a, top=40.0):
    """contrast-stretched view: 0..top levels -> the full scale (a remnant a few levels deep shows plainly)"""
    return Image.fromarray((np.clip(a[..., :3] / top, 0, 1) ** 0.7 * 255).astype(np.uint8)).convert('RGBA')


def review(imgs, out_dir):
    """_review.png: shipped vs new (whole cards, then each card at 1:1), the slots with the old words removed shown
    contrast-stretched, the four models (the plain render each subject is drawn from, and the drawing), and the draft
    row at 1080p as tod_class_select.lua lays it out, shipped and new"""
    src = [Image.fromarray(load_source(n).astype(np.uint8), 'RGBA') for n in NAMES]
    new = [imgs[n] for n in NAMES]
    rows = [('THE FOUR CARDS - shipped, class ids 1-4 (Necromancer, Archer, Breacher, Warrior)', src, 460),
            ('THE FOUR CARDS - this pass: one window recipe, one typeface, one size per slot, each class its own hue', new, 460)]
    for i, n in enumerate(NAMES):
        rows.append(('%s AT 1:1 - shipped | new' % n, [src[i].crop((60, 40, 708, 660)), new[i].crop((60, 40, 708, 660))], 620))
        rows.append(('', [src[i].crop((60, 640, 708, 1000)), new[i].crop((60, 640, 708, 1000))], 360))
    cl = getattr(build_all, 'cleared', None)
    if cl:
        for box, h, what in (((96, 50, 672, 172), 122, 'header'), ((130, 630, 640, 760), 130, 'banner'),
                             ((96, 750, 672, 960), 210, 'name box')):
            rows.append(('THE OLD WORDS REMOVED - the %s of each card after the clearing pass, before the new words, '
                         'contrast-stretched 0..40 levels -> full scale' % what,
                         [_stretch(cl[n]).crop(box) for n in NAMES], h))
    truth = [Image.open(os.path.join(SRC, CLASSES[n]['subject'] + '_truth.png')).convert('RGBA') for n in NAMES]
    subj = []
    for n in NAMES:
        bgi = Image.new('RGBA', build_all.subjects[n].size, (12, 12, 16, 255)) if hasattr(build_all, 'subjects') else None
        if bgi is not None:
            bgi.alpha_composite(build_all.subjects[n])
            subj.append(bgi)
    rows.append(('THE MODELS - the plain render of each game model (R2 z-buffer, its own colour maps) ...', truth, 300))
    if subj:
        rows.append(('... and the card drawing made from it (R2 stylize: flat regions, light bands, navy outline, class rim)', subj, 300))
    old_d, new_d = onscreen_draft(src), onscreen_draft(new)
    old_d.save(os.path.join(out_dir, '_onscreen_draft_old_1080p.png'))
    new_d.save(os.path.join(out_dir, '_onscreen_draft_new_1080p.png'))
    rows.append(('THE DRAFT ROW AT 1080p (CARD_W 210 x 1.5 = 315 px wide, pitch 298) - shipped', [old_d], 540))
    rows.append(('... this pass', [new_d], 540))
    sheets = []
    for label, items, hgt in rows:
        p = os.path.join(out_dir, '_row.png')
        artgen.contact_sheet([(label, items)], p, height=hgt, label_h=26 if label else 4)
        sheets.append(Image.open(p).convert('RGBA'))
        os.remove(p)
    Wd = max(s.width for s in sheets)
    sheet = Image.new('RGBA', (Wd, sum(s.height for s in sheets)), (28, 30, 38, 255))
    y = 0
    for s in sheets:
        sheet.alpha_composite(s, (0, y))
        y += s.height
    p = os.path.join(out_dir, '_review.png')
    sheet.save(p)
    side = Image.new('RGBA', (4 * 768 + 5 * 16, 1152 + 32), (28, 30, 38, 255))
    for i, im in enumerate(new):
        side.alpha_composite(im, (16 + i * (768 + 16), 16))
    side.save(os.path.join(out_dir, '_set_side_by_side.png'))
    return p

# ============================================================================================== wiring


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
        elif '"baseImage" "source_data/tod_ui_images/_images/%s.png"' % n not in m.group(1):
            bad.append('GDT: %s does not point at its PNG' % n)
    zone = _read(root, ZONE_REL).splitlines()
    for n in NAMES:
        if 'image,' + n not in zone:
            bad.append('zone: no "image,%s" line in %s' % (n, ZONE_REL))
    lua = _read(root, CLS_LUA_REL)
    if not re.search(r'^local USE_CLASS_CARD_ART = true\b', lua, re.M):
        bad.append('%s: USE_CLASS_CARD_ART is not true - the draft would not draw these cards' % CLS_LUA_REL)
    for n in NAMES:
        cid = CLASSES[n]['id']
        if not re.search(r'\[%d\] = RegisterImage\( "%s" \)' % (cid, n), lua):
            bad.append('%s no longer registers %s as class %d' % (CLS_LUA_REL, n, cid))
        m = re.search(r'\[%d\] = \{ name = "([^"]*)",\s*gun = "([^"]*)",\s*role = "([^"]*)",.*?accent = \{ ([\d.]+), ([\d.]+), '
                      r'([\d.]+) \}' % cid, lua, re.S)
        c = CLASSES[n]
        if not m:
            bad.append('%s: no CLASSES[%d] entry to check %s against' % (CLS_LUA_REL, cid, n))
            continue
        if m.group(1) != c['banner'] or m.group(2) != ' '.join(c['name']) or m.group(3) != ' '.join(c['title']):
            bad.append('%s CLASSES[%d] says %s / %s / %s; the card bakes %s / %s / %s - re-bake the card'
                       % (CLS_LUA_REL, cid, m.group(1), m.group(2), m.group(3), c['banner'], ' '.join(c['name']),
                          ' '.join(c['title'])))
        acc = [float(v) * 255.0 for v in m.group(4, 5, 6)]
        if max(abs(a - f) for a, f in zip(acc, c['face'])) > 0.6:     # x 255, to the nearest level
            bad.append('%s CLASSES[%d].accent is %s x 255; the banner word is baked in %s'
                       % (CLS_LUA_REL, cid, m.group(4, 5, 6), c['face']))
    return bad

# ================================================================================================ main


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--render', nargs='*', help='re-rasterise the models (all, or the named subjects) into the cache')
    ap.add_argument('--install', action='store_true', help='LANDING ONLY: write into source_data/tod_ui_images/_images/')
    ap.add_argument('--stage', help='also write the PNGs under DIR/source_data/tod_ui_images/_images/')
    ap.add_argument('--check', action='store_true', help='fail on any byte that differs from the installed PNGs, or a wiring break')
    ap.add_argument('--root', help='with --check: read DIR/... instead of the repo')
    a = ap.parse_args()
    if a.render is not None:
        mp = os.path.join(SRC, 'render.json')
        meta = json.load(open(mp, encoding='utf-8')) if os.path.isfile(mp) else {}
        for n in (a.render or SUBJECT_ORDER):
            meta[n] = render_subject(n)
            print('rendered', n, meta[n]['triangles'], 'triangles, scale', meta[n]['scale'])
        os.makedirs(SRC, exist_ok=True)
        with open(mp, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(meta, f, indent=1, sort_keys=True)
            f.write('\n')
        return
    imgs, info = build_all()
    if a.check:
        root = a.root or ROOT
        bad = []
        for n in NAMES:
            p = os.path.join(root, IMG_REL, n + '.png')
            if not os.path.isfile(p):
                bad.append('MISSING %s' % p)
            elif open(p, 'rb').read() != artgen.png_bytes(imgs[n]):
                bad.append('STALE %s (re-run tools/artgen/packs/r6_class_cards.py --install; never hand-edit it)' % p)
        bad += check_wiring(root)
        if bad:
            for b in bad:
                print('R6 CLASS CARDS: ' + b)
            sys.exit(1)
        print('R6 CLASS CARDS OK (%d cards byte-exact; GDT + zone + draft registration + words / accents = '
              'tod_class_select.lua CLASSES)' % len(NAMES))
        return
    os.makedirs(OUT, exist_ok=True)
    for n in NAMES:
        md5 = artgen.save_png(imgs[n], os.path.join(OUT, n + '.png'))
        print('%-30s %s  %s' % (n, md5, info.get(n, '')))
    print('beam repair fit rms %.2f levels; banner bar glow fit rms %s levels' % (info['beam_fit_rms'], info['bar_fit_rms']))
    for root in ([a.stage] if a.stage else []) + ([ROOT] if a.install else []):
        for n in NAMES:
            artgen.save_png(imgs[n], os.path.join(root, IMG_REL, n + '.png'))
    print('review ->', review(imgs, OUT))


if __name__ == '__main__':
    main()
