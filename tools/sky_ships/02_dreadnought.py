"""THE SKY FLEET - the DREADNOUGHT (docs/192). ~11,300 units bow to stern.

Silhouette you can name at a glance: a long ARROWHEAD hull, a stepped COMMAND TOWER at the stern, two huge side
ENGINE PODS and a triple main engine. v2 (user 2026-09-29: "they actually need a lot more detail") layers it the
way AAA capital ships are: two-tone raised armour plating over the whole hull, a tiered dorsal CITADEL with lit
window rows, masts and dishes, heavy triple turret batteries along the sloped flanks, point-defence turrets on the
waist, belly turrets, sensor domes, three lit HANGAR BAYS with chevrons, the registration TOD-01 and the crown
emblem on the belly (players see it from below), finned engine pods on truss pylons, flanged nozzles, greeble
fields and running lights. Bow along +X, port +Y, up +Z; origin = the hull's centre (tag_origin).
"""
import bpy, sys, importlib, pathlib, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib, detail_lib
importlib.reload(sky_lib)
importlib.reload(detail_lib)
from sky_lib import Part, mat, ship_collection, loft, tube, band, quad_facing, light_box, lerp, frame, exhaust
from detail_lib import (abox, obox, frustum_box, cyl, dome, dish, turret, mast, vent_bank, fin_bank, truss, nozzle,
                        plates_on_loft, block_field, light_row, deco_quad, basis)
from sky_data import DECO_CELLS

KEY = 'dreadnought'
col = ship_collection(KEY, (0, 0, 0))
ACCENT = 'neon_red'          # variant B swaps this for neon_cyan (skinOverride in the export)
rng = np.random.default_rng(1920)

# ---- the hull: stations along x (x, waist half-width w, deck half-width d, top t, waist z m, keel b, ridge)
S = [
    (5000,   30,  15,  40,  0,  -40,  0),     # the bow point
    (3800,  520, 170, 190,  0, -190, 30),
    (2200, 1050, 360, 330, 10, -310, 60),
    (400,  1420, 500, 420, 20, -400, 80),
    (-1600, 1620, 580, 480, 30, -450, 90),
    (-3400, 1650, 620, 500, 30, -470, 90),
    (-4700, 1560, 600, 480, 30, -450, 80),
    (-5000, 1480, 570, 450, 30, -420, 70),    # the stern plate
]

def ring(x, w, d, t, m, b, r):
    return [(x, 0, t + r), (x, d, t), (x, w, m), (x, 0.72 * w, 0.55 * b), (x, 0.28 * w, b),
            (x, -0.28 * w, b), (x, -0.72 * w, 0.55 * b), (x, -w, m), (x, -d, t)]

def station(x):
    if x >= S[0][0]:
        return S[0][1:]
    if x <= S[-1][0]:
        return S[-1][1:]
    for a, b in zip(S[:-1], S[1:]):
        if b[0] <= x <= a[0]:
            t = (a[0] - x) / (a[0] - b[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(1, 7))

def top_z(x, y):
    w, d, t, m, b, r = station(x)
    ay = abs(y)
    if ay <= d:
        return t + r * (1 - ay / d)
    if ay <= w:
        return t + (m - t) * (ay - d) / (w - d)
    return None

def top_n(x, y):
    """Outward normal of the dorsal surface at (x, y) (the ridge gable or the sloped flank)."""
    w, d, t, m, b, r = station(x)
    sg = 1 if y >= 0 else -1
    if abs(y) <= d:
        return Vector((0, sg * r, d)).normalized()
    return Vector((0, sg * (t - m), w - d)).normalized()

def bottom_z(x, y):
    w, d, t, m, b, r = station(x)
    ay = abs(y)
    if ay <= 0.28 * w:
        return b
    if ay <= 0.72 * w:
        return b + (0.55 * b - b) * (ay - 0.28 * w) / (0.44 * w)
    if ay <= w:
        return 0.55 * b + (m - 0.55 * b) * (ay - 0.72 * w) / (0.28 * w)
    return None

rings = [ring(*s) for s in S]
hull = Part(col, 'dreadnought hull', mat('hull'))
loft(hull, rings)
hull.finish(box_uv_scale=1536)

# ---- zones the plating leaves to other structures ------------------------------------------------------
BAYS = [(800, 1900), (-900, 300), (-2600, -1400)]              # belly hangar bays (x0, x1), |y| < 330
def on_citadel(c):
    return c.z > 0 and abs(c.y) < 320 and -3300 < c.x < 2700
def on_tower(c):
    return c.z > 0 and abs(c.y) < 620 and -4600 < c.x < -2300
def in_bay(c):
    return c.z < 0 and abs(c.y) < 360 and any(x0 - 30 < c.x < x1 + 30 for x0, x1 in BAYS)

plates = Part(col, 'dreadnought armour plates', mat('hull'))
plates2 = Part(col, 'dreadnought armour plates light', mat('hull2'))
n_pl = plates_on_loft(plates, rings, rng, nu=8, nv=3, hmin=10, hmax=34, inset=16, skip=0.05, merge=0.5,
                      keep=lambda c: not (on_citadel(c) or on_tower(c) or in_bay(c)), alt=(plates2, 0.22))

tips = []                                                          # mast tips (each gets a running light)

# ---- the dorsal CITADEL: tiered superstructure riding the ridge -----------------------------------------
sup = Part(col, 'dreadnought citadel', mat('hull2'))
win = Part(col, 'dreadnought windows', mat('windows'))
seg_x = [2700, 2000, 1300, 600, -100, -800, -1500, -2200, -2900, -3300]
for x0, x1 in zip(seg_x[:-1], seg_x[1:]):
    zc = top_z((x0 + x1) / 2, 0)
    hw = 280 if x0 < 2600 else 200
    frustum_box(sup, ((x0 + x1) / 2, 0, zc + 60), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), (abs(x1 - x0) / 2 + 2, hw, 90), (abs(x1 - x0) / 2 + 2, hw - 40))
TIER2 = [(1900, 800), (300, -900), (-1500, -2700)]
for x0, x1 in TIER2:
    zb = top_z((x0 + x1) / 2, 0) + 150
    frustum_box(sup, ((x0 + x1) / 2, 0, zb + 70), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), (abs(x1 - x0) / 2, 190, 70), (abs(x1 - x0) / 2 - 60, 150))
    frustum_box(sup, ((x0 + x1) / 2 - 150, 0, zb + 175), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), (abs(x1 - x0) / 4, 120, 35), (abs(x1 - x0) / 4 - 30, 95))
    for sg in (1, -1):                                             # a lit window row down each side of tier 2
        y = sg * 186
        quad_facing(win, [(x0 - 40, y, zb + 30), (x1 + 40, y, zb + 30), (x1 + 40, y, zb + 100), (x0 - 40, y, zb + 100)], (0, sg, 0),
                    [(0, 0.78), (abs(x1 - x0) / 700, 0.78), (abs(x1 - x0) / 700, 0.95), (0, 0.95)])
    # masts, dishes and a dome on each tier
    xm = (x0 + x1) / 2 + 180
    tips.append(mast(sup, (xm, 0, zb + 210), 520, 22, bars=3, bar_len=240))
    dish(sup, ((x0 + x1) / 2 - 330, 110, zb + 250), (0.3, 0.5, 0.8), 110, 40)
    dome(sup, ((x0 + x1) / 2 - 330, -110, zb + 212), (0, 0, 1), 75)
for sg in (1, -1):                                                 # window rows along tier 1's sides
    for x0, x1 in zip(seg_x[1:-2], seg_x[2:-1]):
        zc = top_z((x0 + x1) / 2, 0)
        y = sg * 268
        quad_facing(win, [(x0 - 10, y, zc + 20), (x1 + 10, y, zc + 20), (x1 + 10, y, zc + 110), (x0 - 10, y, zc + 110)], (0, sg, 0.25),
                    [(0, 0.55), (abs(x1 - x0) / 700, 0.55), (abs(x1 - x0) / 700, 0.95), (0, 0.95)])
dome(sup, (2350, 0, top_z(2350, 0) + 140), (0, 0, 1), 120)
dome(sup, (-3150, 0, top_z(-3150, 0) + 140), (0, 0, 1), 95)

# ---- turret batteries ------------------------------------------------------------------------------------
guns = Part(col, 'dreadnought turrets', mat('hull2'))
heavy = []
for x in (2700, 1850, 1000, 150, -700, -1550, -2400):
    for sg in (1, -1):
        w, d, t, m, b, r = station(x)
        y = sg * (d + 0.32 * (w - d))
        heavy.append((x, y))
        turret(guns, (x, y, top_z(x, y)), 210, yaw_deg=0, up=top_n(x, y), barrels=3, barrel_len=2.4, barrel_r=0.1)
for x in range(3400, -4700, -800):                                 # point defence along the waist
    for sg in (1, -1):
        w, d, t, m, b, r = station(x)
        y = sg * (w - 90)
        turret(guns, (x, y, top_z(x, y)), 58, yaw_deg=90 * sg, up=top_n(x, y), barrels=2, barrel_len=2.0)
for x in (2300, 600, -1100, -3000):                                # belly turrets, hanging
    for sg in (1, -1):
        w = station(x)[0]
        y = sg * 0.5 * w
        turret(guns, (x, y, bottom_z(x, y)), 140, yaw_deg=0, up=(0, sg * 0.35, -1), barrels=2, barrel_r=0.1)

# ---- the COMMAND TOWER (lighter armour so it stands out) ---------------------------------------------------
tower = Part(col, 'dreadnought command tower', mat('hull2'))
X = (1, 0, 0); Y = (0, 1, 0); Z = (0, 0, 1)
frustum_box(tower, (-3450, 0, 685), (X, Y, Z), (1050, 560, 215), (900, 440))
frustum_box(tower, (-3550, 0, 1050), (X, Y, Z), (650, 400, 150), (560, 340))
abox(tower, -4000, -3300, -760, 760, 1200, 1380)                    # the bridge wing (a T from the front)
abox(tower, -3950, -3350, -560, 560, 1380, 1470)                    # its roof deck
frustum_box(tower, (-3640, 0, 1540), (X, Y, Z), (180, 180, 70), (120, 120))
for sg in (1, -1):
    vent_bank(tower, (-4300, sg * 505, 520), (1, 0, 0), (0, sg, 0.45), 14, 70, 40, 150, 26)
    obox(tower, (-2950, sg * 470, 900), (X, Y, Z), (160, 60, 120))  # tower sponsons, each carrying a dish
    dish(tower, (-2950, sg * 505, 1085), (0.3, sg * 0.6, 0.75), 150, 55)
tips.append(mast(tower, (-3740, 0, 1610), 780, 34, bars=4, bar_len=460))
for (mx, my) in ((-3450, 360), (-3450, -360), (-3880, 360), (-3880, -360)):
    tips.append(mast(tower, (mx, my, 1470), 320 + 40 * (my > 0), 16, bars=2, bar_len=150))
bridge = Part(col, 'dreadnought bridge windows', mat('windows'))
quad_facing(bridge, [(-3296, -700, 1235), (-3296, 700, 1235), (-3296, 700, 1345), (-3296, -700, 1345)], (1, 0, 0), [(0, 0), (2, 0), (2, 1), (0, 1)])
quad_facing(bridge, [(-4004, -700, 1235), (-4004, 700, 1235), (-4004, 700, 1345), (-4004, -700, 1345)], (-1, 0, 0), [(0, 0), (2, 0), (2, 1), (0, 1)])
for sg in (1, -1):
    quad_facing(bridge, [(-3980, sg * 764, 1235), (-3320, sg * 764, 1235), (-3320, sg * 764, 1345), (-3980, sg * 764, 1345)], (0, sg, 0), [(0, 0), (1, 0), (1, 1), (0, 1)])
    quad_facing(bridge, [(-4250, sg * 452, 760), (-2800, sg * 452, 760), (-2800, sg * 452, 860), (-4250, sg * 452, 860)], (0, sg, 0.3), [(0, 0), (2, 0), (2, 1), (0, 1)])
    quad_facing(bridge, [(-4050, sg * 356, 1000), (-3100, sg * 356, 1000), (-3100, sg * 356, 1090), (-4050, sg * 356, 1090)], (0, sg, 0.2), [(0, 0), (1.4, 0), (1.4, 1), (0, 1)])

# ---- the engine pods on truss pylons, finned, plated ---------------------------------------------------------
POD_Y, POD_Z, POD_R = 2150, -80, 430
pods = Part(col, 'dreadnought engine pods', mat('hull'))
podp = Part(col, 'dreadnought pod plates', mat('hull2'))
pyl = Part(col, 'dreadnought pylons', mat('hull2'))
bells = Part(col, 'dreadnought engine bells', mat('drive_metal'))
eng = Part(col, 'dreadnought engines', mat('engine_cyan'))
nozzles = []
for sg in (1, -1):
    y = sg * POD_Y
    cyl(pods, (-5300, y, POD_Z), (-1900, y, POD_Z), POD_R, POD_R, sides=24, caps=(True, False))
    cyl(pods, (-1900, y, POD_Z), (-1250, y, POD_Z), POD_R, 230, sides=24, caps=(False, True))
    cyl(pods, (-1250, y, POD_Z), (-1150, y, POD_Z), 230, 150, sides=24, caps=(False, True))       # the intake cone
    pr = []
    for x, rr in ((-5250, 432), (-4400, 432), (-3500, 432), (-2600, 432), (-1920, 432)):
        pr.append([(x, y + rr * math.cos(2 * math.pi * i / 16), POD_Z + rr * math.sin(2 * math.pi * i / 16)) for i in range(16)])
    plates_on_loft(podp, pr, rng, nu=3, nv=1, hmin=8, hmax=24, inset=14, skip=0.08, merge=0.4, axis=(y, POD_Z))
    for k in range(14):                                            # radiator fins around the pod's waist
        a = 2 * math.pi * k / 14
        rad = Vector((0, math.cos(a), math.sin(a)))
        c = Vector((-3050, y, POD_Z)) + rad * (POD_R + 70)
        f, l, u = basis(Vector((1, 0, 0)), rad)
        obox(pods, c, (f, l, u), (420, 10, 75))
    for x in (-4100, -2900):                                       # truss pylons + a solid spar
        truss(pyl, (x, sg * 1480, -40), (x, sg * (POD_Y - POD_R + 30), POD_Z), 170, 130)
        obox(pyl, (x - 260, sg * (1480 + POD_Y - POD_R) / 2, -60), (X, Y, Z), (60, abs(POD_Y - POD_R - 1480) / 2 + 40, 40))
    nozzles.append(tuple(nozzle(bells, eng, (-5300, y, POD_Z), POD_R - 20, 300)) + (POD_R - 20,))
for yy in (-760, 0, 760):
    nozzles.append(tuple(nozzle(bells, eng, (-4990, yy, 0), 300, 270)) + (300,))
frustum_box(bells, (-4960, 0, 0), (X, Y, Z), (40, 1180, 380), (40, 1180))      # the stern engine frame
pods.finish(box_uv_scale=1536, recalc=False)
podp.finish(box_uv_scale=1536, recalc=False)
pyl.finish(box_uv_scale=1536, recalc=False)
bells.finish(box_uv_scale=1536, recalc=False)
eng.finish(recalc=False)
spikes = Part(col, 'dreadnought exhaust', mat('neon_cyan'))
for (x, y, z, r) in nozzles:
    exhaust(spikes, x - 4, y, z, r * 0.55, r * 1.9)
spikes.finish()

# ---- the belly: three lit hangar bays, registration, crown emblem, blisters ----------------------------------------
frame_p = Part(col, 'dreadnought hangar frames', mat('hull2'))
hang = Part(col, 'dreadnought hangar glow', mat('hangar'))
deco = Part(col, 'dreadnought markings', mat('deco'))
for x0, x1 in BAYS:
    zb = min(bottom_z(x0, 0), bottom_z(x1, 0))
    for (a, b, c, d2) in ((x0 - 40, x1 + 40, 330, 400), (x0 - 40, x1 + 40, -400, -330)):
        abox(frame_p, a, b, c, d2, zb - 90, zb + 60)
    abox(frame_p, x0 - 40, x0 + 30, -330, 330, zb - 90, zb + 60)
    abox(frame_p, x1 - 30, x1 + 40, -330, 330, zb - 90, zb + 60)
    quad_facing(hang, [(x0 + 30, -330, zb - 40), (x1 - 30, -330, zb - 40), (x1 - 30, 330, zb - 40), (x0 + 30, 330, zb - 40)], (0, 0, -1))
    for sg in (1, -1):                                             # chevron strips along each long edge
        deco_quad(deco, ((x0 + x1) / 2, sg * 365, zb - 92), (1, 0, 0), (0, -1, 0), (x1 - x0) * 0.9, 60, DECO_CELLS['chevrons'])
def belly_mark(x0, x1, y, h, cell):
    # a marking that follows the keel's slope (the belly descends toward the stern), 4 units proud of it
    z0, z1 = bottom_z(x0, y) - 4, bottom_z(x1, y) - 4
    right = Vector((x1 - x0, 0, z1 - z0))
    deco_quad(deco, ((x0 + x1) / 2, y, (z0 + z1) / 2), right, (0, -1, 0), right.length, h, cell)

belly_mark(2700, 3800, 0, 292, DECO_CELLS['tod01'])
belly_mark(2170, 2690, 0, 520, DECO_CELLS['crown'])
for sg in (1, -1):
    belly_mark(-4050, -3150, sg * 560, 60, DECO_CELLS['arrows'])
for x, yf in ((2000, 0.5), (-500, 0.55), (-3300, 0.5)):
    for sg in (1, -1):
        w = station(x)[0]
        y = sg * yf * w
        dome(frame_p, (x - 350, y, bottom_z(x - 350, y)), (0, 0, -1), 90)

# ---- flanks: waist ribs, vent banks, greebles ---------------------------------------------------------------------
grb = Part(col, 'dreadnought greebles', mat('hull2'))
for x in range(3300, -4800, -450):                                 # strakes along the upper waist
    for sg in (1, -1):
        w, d, t, m, b, r = station(x)
        y = sg * (w - 60)
        n = top_n(x, y)
        f, l, u = basis(Vector((1, 0, 0)), n)
        obox(grb, Vector((x, y, top_z(x, y))) + n * 18, (f, l, u), (34, 55, 26))
for x0 in (2400, 600, -1200, -3000):
    for sg in (1, -1):
        w, d, t, m, b, r = station(x0)
        y = sg * (d + 0.72 * (w - d))
        vent_bank(grb, (x0, y, top_z(x0, y)), (1, 0, 0), top_n(x0, y), 10, 60, 34, 170, 22)

def deck_sample():
    x = rng.uniform(-4400, 3600)
    w, d, t, m, b, r = station(x)
    y = rng.uniform(-w + 120, w - 120)
    if abs(y) < 330 and -3300 < x < 2750:
        return None                                                # the citadel
    if -4650 < x < -2250 and abs(y) < 650:
        return None                                                # the tower
    if any(abs(x - hx) < 260 and abs(y - hy) < 260 for hx, hy in heavy):
        return None
    z = top_z(x, y)
    if z is None:
        return None
    return ((x, y, z), top_n(x, y))

def belly_sample():
    x = rng.uniform(-4500, 3000)
    w = station(x)[0]
    y = rng.uniform(-w + 150, w - 150)
    if abs(y) < 420 and any(x0 - 80 < x < x1 + 80 for x0, x1 in BAYS):
        return None
    if 1900 < x < 3900 and abs(y) < 330:
        return None                                                # the markings
    z = bottom_z(x, y)
    if z is None:
        return None
    return ((x, y, z), (0, 0, -1))

block_field(grb, rng, 520, deck_sample, (40, 170), (18, 80))
kb = Part(col, 'dreadnought keel blade', mat('hull2'))
zk0, zk1 = bottom_z(-3600, 0), bottom_z(-4950, 0)
for x0, x1, d0, d1 in ((-3600, -4300, 20, 260), (-4300, -4950, 260, 380)):
    za, zb2 = bottom_z(x0, 0), bottom_z(x1, 0)
    pts_lo = [(x0, -45, za - d0), (x1, -45, zb2 - d1), (x1, 45, zb2 - d1), (x0, 45, za - d0)]
    pts_hi = [(x0, -45, za + 20), (x1, -45, zb2 + 20), (x1, 45, zb2 + 20), (x0, 45, za + 20)]
    ctr = Vector(((x0 + x1) / 2, 0, (za + zb2) / 2 - (d0 + d1) / 4))
    from detail_lib import _face
    _face(kb, pts_lo, ctr)
    for i in range(4):
        j = (i + 1) % 4
        _face(kb, [pts_lo[i], pts_lo[j], pts_hi[j], pts_hi[i]], ctr)
block_field(grb, rng, 260, belly_sample, (50, 190), (16, 60))

# ---- neon: the arrowhead outline (both waist edges), the keel edges, the dorsal ridge, the pods -------------------
neon = Part(col, 'dreadnought neon', mat(ACCENT))
for idx in (2, 7):
    tube(neon, [r[idx] for r in rings], 70)
for idx in (4, 5):
    tube(neon, [r[idx] for r in rings[1:7]], 55)
for sg in (1, -1):
    ring_pts = [(-1905, sg * POD_Y + (POD_R + 25) * math.cos(a), POD_Z + (POD_R + 25) * math.sin(a))
                for a in [i * 2 * math.pi / 24 for i in range(25)]]
    tube(neon, ring_pts, 60)
    tube(neon, [(-5250, sg * POD_Y, POD_Z + POD_R + 20), (-1950, sg * POD_Y, POD_Z + POD_R + 20)], 55)
    tube(neon, [(-5250, sg * POD_Y, POD_Z - POD_R - 20), (-1950, sg * POD_Y, POD_Z - POD_R - 20)], 55)
    for x0, x1 in TIER2:                                           # the citadel's eaves
        zb = top_z((x0 + x1) / 2, 0) + 150
        tube(neon, [(x0, sg * 196, zb + 4), (x1, sg * 196, zb + 4)], 30)
neon.finish()

# ---- windows: the long flank rows (lower flanks face the players below) ----------------------------------------------------
for a_idx, b_idx in ((2, 3), (7, 6), (2, 1), (7, 8)):
    s0, s1 = (0.14, 0.62) if b_idx in (3, 6) else (0.18, 0.58)
    ra = [lerp(r[a_idx], r[b_idx], s0) for r in rings[2:7]]
    rb = [lerp(r[a_idx], r[b_idx], s1) for r in rings[2:7]]
    band(win, ra, rb, 8, period=1400)
win.finish(recalc=False)
bridge.finish(recalc=False)

# ---- running lights (steady) - red to port, green to starboard, white along the waist ----------------------------------------
navr = Part(col, 'dreadnought nav red', mat('nav_red'))
light_box(navr, (-1600, 1705, 30), 170)
navr.finish()
navg = Part(col, 'dreadnought nav green', mat('nav_green'))
light_box(navg, (-1600, -1705, 30), 170)
navg.finish()
navw = Part(col, 'dreadnought running lights', mat('neon_white'))
light_box(navw, (4930, 0, 0), 130)
for x in range(3000, -4700, -700):
    for sg in (1, -1):
        w, d, t, m, b, r = station(x)
        light_box(navw, (x, sg * (w + 8), m - 70), 50)
for tip in tips:
    light_box(navw, tuple(tip), 70)
light_box(navw, (-4950, 0, bottom_z(-4950, 0) - 385), 80)          # the keel blade's tip
navw.finish()
belly = Part(col, 'dreadnought belly lights', mat('glass'))            # warm amber lights scattered under the hull
n_bl = 0
while n_bl < 70:
    x = rng.uniform(-4300, 3400)
    w = station(x)[0]
    y = rng.uniform(-0.9 * w, 0.9 * w)
    if abs(y) < 430 and any(x0 - 100 < x < x1 + 100 for x0, x1 in BAYS):
        continue
    if 2100 < x < 3900 and abs(y) < 330:
        continue
    light_box(belly, (x, y, bottom_z(x, y) - 14), 34)
    n_bl += 1
belly.finish()

for p in (plates, plates2, sup, guns, tower, frame_p, grb, kb):
    p.finish(box_uv_scale=1536, recalc=False)
deco.finish(recalc=False)
hang.finish(recalc=False)

# ================================================================================================================
# v3 DETAIL (user 2026-09-29 15:40: "one more detailed pass and enhancement ... add more detail to each of the
# spaceships"; "make sure we focus on quality and detail of each")
# ================================================================================================================
def flank_pt(x, f, sg):
    """A point on the LOWER flank (waist -> the lower chine) at fraction f, and that flank's outward normal."""
    w, d, t, m, b, r = station(x)
    p2 = Vector((x, sg * w, m))
    p3 = Vector((x, sg * 0.72 * w, 0.55 * b))
    tv = p3 - p2
    n = Vector((0, -tv.z * sg, tv.y * sg)).normalized()
    if n.y * sg < 0:
        n = -n
    return p2.lerp(p3, f), n

def upper_pt(x, f, sg):
    """A point on the UPPER flank (deck edge -> waist) at fraction f, and its outward normal."""
    w, d, t, m, b, r = station(x)
    p1 = Vector((x, sg * d, t))
    p2 = Vector((x, sg * w, m))
    return p1.lerp(p2, f), top_n(x, sg * (d + f * (w - d)))

# THE FLANK TRENCHES: a recessed channel down each lower flank - two walls, glowing cyan light strips inside,
# structural ribs across it every 350 units (the "Death Star trench" read, lit for the city below)
trench = Part(col, 'dreadnought trenches', mat('hull2'))
tlight = Part(col, 'dreadnought trench lights', mat('neon_cyan'))
v3h = Part(col, 'dreadnought detail v3', mat('hull'))                  # vanes, pipes
v3h2 = Part(col, 'dreadnought detail v3 light', mat('hull2'))          # radar arrays, clamps
v3win = Part(col, 'dreadnought windows v3', mat('windows'))
v3nav = Part(col, 'dreadnought running lights v3', mat('neon_white'))
v3deco = Part(col, 'dreadnought markings v3', mat('deco'))
v3bell = Part(col, 'dreadnought aux bells', mat('drive_metal'))
v3eng = Part(col, 'dreadnought aux engines', mat('engine_cyan'))
v3spk = Part(col, 'dreadnought aux exhaust', mat('neon_cyan'))
for sg in (1, -1):
    xs = list(range(3400, -4601, -200))
    for x0, x1 in zip(xs[:-1], xs[1:]):
        for f, h in ((0.26, 58), (0.44, 58)):                      # the two walls
            a, n = flank_pt(x0, f, sg)
            b2, _ = flank_pt(x1, f, sg)
            fwd = (b2 - a).normalized()
            side = n.cross(fwd).normalized()
            obox(trench, (a + b2) / 2 + n * (h / 2 - 4), (fwd, side, n), ((b2 - a).length / 2 + 3, 9, h / 2))
        a, n = flank_pt(x0, 0.35, sg)                               # the glowing strip on the trench floor
        b2, _ = flank_pt(x1, 0.35, sg)
        fwd = (b2 - a).normalized()
        side = n.cross(fwd).normalized()
        obox(tlight, (a + b2) / 2 + n * 6, (fwd, side, n), ((b2 - a).length / 2 + 2, 26, 4))
    for x in range(3200, -4500, -350):                              # ribs across the trench
        a, n = flank_pt(x, 0.35, sg)
        c, _ = flank_pt(x, 0.26, sg)
        e, _ = flank_pt(x, 0.44, sg)
        across = (e - c).normalized()
        fwd = n.cross(across).normalized()
        obox(trench, a + n * 30, (fwd, across, n), (20, (e - c).length / 2 + 14, 32))

# CYBER LIGHT LINES along the upper flanks (they trace the hull's curve - the shape reads at night)
for sg in (1, -1):
    tube(tlight, [tuple(upper_pt(x, 0.5, sg)[0] + upper_pt(x, 0.5, sg)[1] * 12) for x in range(3000, -4401, -400)], 22)
    tube(tlight, [tuple(upper_pt(x, 0.82, sg)[0] + upper_pt(x, 0.82, sg)[1] * 12) for x in range(2600, -4401, -400)], 18)

# THE FORWARD BRIDGE: a second, smaller superstructure ahead of the citadel, windows all round, an antenna crown
fb = Part(col, 'dreadnought forward bridge', mat('hull2'))
zr = top_z(3100, 0)
frustum_box(fb, (3100, 0, zr + 90), (X, Y, Z), (260, 170, 110), (200, 120))
frustum_box(fb, (3060, 0, zr + 250), (X, Y, Z), (150, 105, 55), (120, 80))
for sg in (1, -1):
    quad_facing(v3win, [(2880, sg * 161, zr + 110), (3320, sg * 161, zr + 110), (3320, sg * 161, zr + 170), (2880, sg * 161, zr + 170)], (0, sg, 0.1),
                [(0, 0.78), (0.6, 0.78), (0.6, 0.95), (0, 0.95)])
quad_facing(v3win, [(3292, -120, zr + 110), (3292, 120, zr + 110), (3292, 120, zr + 170), (3292, -120, zr + 170)], (1, 0, 0.1),
            [(0, 0.78), (0.3, 0.78), (0.3, 0.95), (0, 0.95)])
fb_tip = mast(fb, (3000, 0, zr + 305), 380, 14, bars=3, bar_len=150)
light_box(v3nav, tuple(fb_tip), 60)
dish(fb, (3180, 0, zr + 330), (0.8, 0, 0.6), 70, 25)

# THE PROW: a raised keel ridge down the bow and two angled armour ridges (the bow reads sharp from the side)
prow = Part(col, 'dreadnought prow', mat('hull2'))
for x0, x1 in zip(range(4800, 3100, -300), range(4500, 2800, -300)):
    za, zb2 = top_z(x0, 0), top_z(x1, 0)
    obox(prow, ((x0 + x1) / 2, 0, (za + zb2) / 2 + 30), ((1, 0, (za - zb2) / 300), (0, 1, 0), (0, 0, 1)), (152, 18, 34))
    for sg in (1, -1):
        wa = station(x0)[1] * 0.6
        pa, na = Vector((x0, sg * wa, top_z(x0, sg * wa))), top_n(x0, sg * wa)
        pb = Vector((x1, sg * station(x1)[1] * 0.6, top_z(x1, sg * station(x1)[1] * 0.6)))
        fwd = (pb - pa).normalized()
        side = na.cross(fwd).normalized()
        obox(prow, (pa + pb) / 2 + na * 16, (fwd, side, na), ((pb - pa).length / 2 + 4, 14, 18))

# RADAR ARRAYS in the gaps between the citadel's tiers: rows of canted panels on masts
for xa, xb in ((760, 340), (-940, -1460)):
    zc = top_z((xa + xb) / 2, 0) + 150
    for xx in range(int(xb) + 40, int(xa) - 20, 70):
        for sg in (1, -1):
            n = Vector((0.25, sg * 0.35, 0.9)).normalized()
            f, l, u = basis(Vector((1, 0, 0)), n)
            obox(v3h2, (xx, sg * 110, zc + 40), (f, l, u), (26, 60, 4))
            obox(v3h2, (xx, sg * 110, zc + 18), (X, Y, Z), (6, 6, 22))

# POD INTAKES: radial vanes inside each intake cone + a ring of lights round its rim
for sg in (1, -1):
    y = sg * POD_Y
    for k in range(12):
        a = 2 * math.pi * k / 12
        rad = Vector((0, math.cos(a), math.sin(a)))
        c = Vector((-1250, y, POD_Z)) + rad * 175
        f, l, u = basis(Vector((1, 0, 0)), rad)
        obox(v3h, c, (f, l, u), (70, 5, 55))
    for k in range(10):
        a = 2 * math.pi * k / 10 + 0.3
        light_box(v3nav, (-1880, y + (POD_R + 38) * math.cos(a), POD_Z + (POD_R + 38) * math.sin(a)), 34)

# AUXILIARY THRUSTERS round the stern: eight small drives (they fire too - the director gives each a flame)
for (yy, zz, rr) in ((1120, 250, 95), (-1120, 250, 95), (1120, -250, 95), (-1120, -250, 95),
                     (380, 300, 80), (-380, 300, 80), (380, -300, 80), (-380, -300, 80)):
    ex = nozzle(v3bell, v3eng, (-5000, yy, zz), rr, 120)
    exhaust(v3spk, ex.x - 4, yy, zz, rr * 0.55, rr * 1.9)
    nozzles.append(tuple(ex) + (rr,))

# PIPE RUNS along the lower flanks and DOCKING CLAMPS down the keel
for sg in (1, -1):
    pts = [flank_pt(x, 0.62, sg) for x in range(2200, -4201, -400)]
    for (p0, n0), (p1, n1) in zip(pts[:-1], pts[1:]):
        cyl(v3h, p0 + n0 * 30, p1 + n1 * 30, 24, 24, sides=8)
        cyl(v3h, p0 + n0 * 30 + Vector((0, 0, -60)), p1 + n1 * 30 + Vector((0, 0, -60)), 16, 16, sides=8)
for x in (2400, 540, -1150, -3000, -3900):
    for sg in (1, -1):
        zb = bottom_z(x, sg * 380)
        abox(v3h2, x - 70, x + 70, sg * 350, sg * 420, zb - 90, zb + 20)

# TOD-01 on both bow flanks (the side view carries the name too)
for sg in (1, -1):
    p, n = upper_pt(2750, 0.45, sg)
    right = Vector((-sg, 0, 0))                                    # reads left to right for a viewer on that side
    deco_quad(v3deco, p + n * 8, right, n.cross(right), 900, 239, DECO_CELLS['tod01'])

for p in (trench, fb, prow, v3h, v3h2, v3bell):
    p.finish(box_uv_scale=1536, recalc=False)
for p in (tlight, v3win, v3deco, v3eng):
    p.finish(recalc=False)
v3nav.finish()
v3spk.finish()

# ---- blinking light anchors for the director (strobes 's' white, beacons 'b' red): [x, y, z, kind]
LIGHTS = [[4960, 0, 0, 's'], [-5650, POD_Y, POD_Z, 's'], [-5650, -POD_Y, POD_Z, 's'],
          [round(tips[0].x), 0, round(tips[0].z) + 60, 'b'], [-3400, 1720, 30, 's'], [-3400, -1720, 30, 's'],
          [-300, 0, round(bottom_z(-300, 0)) - 40, 'b'], [600, 0, round(top_z(600, 0)) + 420, 'b']]
col['accent'] = ACCENT
col['length'] = 11300
col['nozzles'] = json.dumps([[round(v, 1) for v in n] for n in nozzles])
col['lights'] = json.dumps(LIGHTS)
col['wing'] = json.dumps([])
objs = [o for o in col.objects]
frame(objs)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
print('SKY_SHIP_BUILT', KEY, 'parts', len(objs), 'tris', tris, 'plates', n_pl)
