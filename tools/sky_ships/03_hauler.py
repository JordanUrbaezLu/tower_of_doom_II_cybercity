"""THE SKY FLEET - the HAULER (docs/192). ~6,400 units bow to stern.

Silhouette you can name at a glance: a CARGO TRAIN. A wedge cockpit with a lit visor, a long spine carrying
eighteen coloured CONTAINERS in two tiers, and a square ENGINE BLOCK with four drives. v2 (user 2026-09-29: "a lot
more detail"): plated cockpit with bridge windows, masts and a sensor dome; a truss spine with clamps; corrugated,
framed containers with corner lights and markings; a finned, vented engine block with four flanged drives and RCS
thruster pods; and THE BILLBOARD - three of the sky's own neon ads on a framed screen hung under the cargo, facing
the city below (Cybercity's haulers sell while they haul), plus portrait screens on the engine block's flanks.
"""
import bpy, sys, importlib, pathlib, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib, detail_lib
importlib.reload(sky_lib)
importlib.reload(detail_lib)
from sky_lib import Part, mat, ship_collection, loft, tube, band, quad_facing, light_box, frame, exhaust, aim_camera
from detail_lib import (abox, obox, frustum_box, cyl, dome, dish, mast, vent_bank, fin_bank, truss, nozzle,
                        plates_on_loft, deco_quad, ad_panel, basis)
from sky_data import DECO_CELLS

KEY = 'hauler'
OFFSET = (0, 16000, 0)
col = ship_collection(KEY, OFFSET)
ACCENT = 'neon_amber'        # variant B: neon_teal (+ its own ad wall, mtl_tod_sky_ads_b)
rng = np.random.default_rng(1930)
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

# ---- the cockpit: stations (x, half-width w, top t, bottom b)
S = [(3000, 60, 60, -60), (2700, 380, 260, -220), (2200, 560, 360, -320), (1700, 600, 380, -340)]
def ring(x, w, t, b):
    return [(x, 0, t), (x, 0.7 * w, t), (x, w, 0.3 * t), (x, w, 0.6 * b), (x, 0.6 * w, b),
            (x, -0.6 * w, b), (x, -w, 0.6 * b), (x, -w, 0.3 * t), (x, -0.7 * w, t)]
rings = [ring(*s) for s in S]
cock = Part(col, 'hauler cockpit', mat('hull'))
loft(cock, rings)
cock.finish(box_uv_scale=1024)
cpl = Part(col, 'hauler cockpit plates', mat('hull2'))
plates_on_loft(cpl, rings, rng, nu=4, nv=2, hmin=8, hmax=22, inset=12, skip=0.06, merge=0.35,
               keep=lambda c: not (c.x > 2250 and c.z > 120 and abs(c.y) < 520))     # the visor stays glass

def ring_at(x):
    for (xa, *pa), (xb, *pb) in zip(S[:-1], S[1:]):
        if xb <= x <= xa:
            t = (xa - x) / (xa - xb)
            return ring(x, *[pa[i] + (pb[i] - pa[i]) * t for i in range(3)])
visor = Part(col, 'hauler visor', mat('glass'))
ra, rb = ring_at(2640), ring_at(2330)
band(visor, [ra[i] for i in (3, 2, 1, 0, 8, 7, 6)], [rb[i] for i in (3, 2, 1, 0, 8, 7, 6)], 6, outward=None)
visor.finish(recalc=False)
win = Part(col, 'hauler windows', mat('windows'))
for sg in (1, -1):                                                 # bridge windows down the cockpit sides
    quad_facing(win, [(2150, sg * 566, 20), (1760, sg * 606, 20), (1760, sg * 606, 110), (2150, sg * 566, 110)], (0, sg, 0),
                [(0, 0.78), (0.8, 0.78), (0.8, 0.95), (0, 0.95)])
    quad_facing(win, [(2150, sg * 566, -150), (1760, sg * 606, -150), (1760, sg * 606, -80), (2150, sg * 566, -80)], (0, sg, 0),
                [(0, 0.55), (0.8, 0.55), (0.8, 0.7), (0, 0.7)])

# ---- the spine: a solid core beam, a truss above and below between the stacks, container clamps -----------------------------
spine = Part(col, 'hauler spine', mat('hull2'))
abox(spine, -2480, 1720, -130, 130, -170, 130)
truss(spine, (-2440, 0, 200), (1680, 0, 200), 170, 210)
truss(spine, (-2440, 0, -260), (1680, 0, -260), 170, 210)
for cx in (1250, 430, -390, -1210, -2030):
    for sg in (1, -1):
        abox(spine, cx - 70, cx + 70, sg * 125, sg * 240, -60, 60)                  # clamps
        abox(spine, cx - 50, cx + 50, sg * 125, sg * 240, -300, -220)
tips = [mast(spine, (2050, 120, 360), 420, 16, bars=2, bar_len=160), mast(spine, (2050, -120, 360), 300, 14, bars=2, bar_len=120),
        mast(spine, (-2700, 0, 430), 520, 20, bars=3, bar_len=220)]
dome(spine, (2900, 0, -40), (1, 0, -0.4), 70)

# ---- containers: framed, corrugated, lit corners, markings -------------------------------------------------------------------
COLORS = ['cargo_orange', 'cargo_teal', 'cargo_white', 'cargo_red', 'cargo_yellow']
parts = {c: Part(col, 'hauler containers ' + c.split('_')[1], mat(c)) for c in COLORS}
cframe = Part(col, 'hauler container frames', mat('hull2'))
deco = Part(col, 'hauler markings', mat('deco'))
lamps = Part(col, 'hauler corner lights', mat('glass'))
pattern = [0, 1, 3, 2, 4, 1, 0, 4, 3, 2, 1, 3, 0, 2, 4, 3, 1, 0, 4, 2]
skip = {7, 16}                                                     # two empty slots: the load is lived-in
k = 0
for cx in (1250, 430, -390, -1210, -2030):
    for (y0, y1) in ((230, 830), (-830, -230)):
        for (z0, z1) in ((-370, -40), (-20, 310)):
            if k not in skip:
                x0, x1 = cx - 390, cx + 390
                abox(parts[COLORS[pattern[k]]], x0, x1, y0, y1, z0, z1)
                out = 1 if y0 > 0 else -1
                yo = y1 if out > 0 else y0
                for (ya, za) in ((y0, z0), (y0, z1), (y1, z0), (y1, z1)):          # frame: the four long edges
                    abox(cframe, x0 - 6, x1 + 6, ya - 12, ya + 12, za - 12, za + 12)
                for xe in (x0, x1):                                                # frame: both end rings
                    abox(cframe, xe - 12, xe + 12, y0 - 12, y1 + 12, z0 - 12, z0 + 12)
                    abox(cframe, xe - 12, xe + 12, y0 - 12, y1 + 12, z1 - 12, z1 + 12)
                    abox(cframe, xe - 12, xe + 12, y0 - 12, y0 + 12, z0, z1)
                    abox(cframe, xe - 12, xe + 12, y1 - 12, y1 + 12, z0, z1)
                for xr in range(int(x0) + 60, int(x1) - 30, 65):                  # corrugation ribs on the outer face
                    abox(cframe, xr - 7, xr + 7, yo - 6 if out < 0 else yo - 4, yo + 4 if out < 0 else yo + 6, z0 + 14, z1 - 14)
                if k % 3 == 0:
                    deco_quad(deco, (cx, yo + out * 8, (z0 + z1) / 2), (-out, 0, 0), (0, 0, 1), 560, 150, DECO_CELLS['haul07'])
                elif k % 3 == 1:
                    deco_quad(deco, (cx, yo + out * 8, (z0 + z1) / 2), (-out, 0, 0), (0, 0, 1), 220, 220, DECO_CELLS['crown'])
                if z1 > 0:
                    light_box(lamps, (x0 + 20, yo + out * 10, z1 + 10), 30)
                    light_box(lamps, (x1 - 20, yo + out * 10, z1 + 10), 30)
            k += 1
for p in parts.values():
    p.finish(box_uv_scale=1024, recalc=False)

# ---- THE BILLBOARD: three ads on a framed screen under the cargo, facing the city -----------------------------------------------
bb = Part(col, 'hauler billboard frame', mat('hull2'))
ads = Part(col, 'hauler billboard', mat('ads'))
ZS = -520                                                          # the screen plane
abox(bb, -2020, 1560, -600, -540, ZS - 10, ZS + 50)
abox(bb, -2020, 1560, 540, 600, ZS - 10, ZS + 50)
for xe in (-2020, 1500):
    abox(bb, xe, xe + 60, -600, 600, ZS - 10, ZS + 50)
for xs in (-1500, -250, 1000):                                     # struts up to the spine
    for sg in (1, -1):
        obox(bb, (xs, sg * 180, (ZS + 50 - 170) / 2), (X, Y, Z), (40, 30, (-170 - (ZS + 50)) / 2))
AD_A = [0, 4, 3]                                                   # OBEY  VOID  RISE (variant B's atlas reorders them)
for i, xc in enumerate((-1330, -230, 870)):
    abox(bb, xc - 530, xc - 520, -540, 540, ZS - 6, ZS + 40)       # panel dividers
    ad_panel(ads, (xc + 20, 0, ZS - 2), (1, 0, 0), (0, -1, 0), 1040, 1060, AD_A[i])
ad_panel(ads, (-2725, 664, 0), (-1, 0, 0), (0, 0, 1), 470, 700, 7)  # portrait screens on the engine block
ad_panel(ads, (-2725, -664, 0), (1, 0, 0), (0, 0, 1), 470, 700, 2)

# ---- the engine block: plated, vented, finned radiators, four flanged drives, RCS pods --------------------------------------------
blk = Part(col, 'hauler engine block', mat('hull'))
abox(blk, -3000, -2450, -660, 660, -430, 430)
for sg in (1, -1):
    fin_bank(blk, (-2720, 0, sg * 430), (0, 1, 0), (0, 0, sg), 12, 105, 440, 95, 16)
    for sz in (1, -1):                                             # RCS thruster pods on the block's corners
        c = Vector((-2560, sg * 700, sz * 470))
        cyl(blk, c - Vector((0, sg * 60, 0)), c + Vector((0, sg * 60, 0)), 70, 70, sides=10)
bells = Part(col, 'hauler engine bells', mat('drive_metal'))
eng = Part(col, 'hauler engines', mat('engine_amber'))
nozzles = []
for yy in (-330, 330):
    for zz in (-215, 215):
        nozzles.append(tuple(nozzle(bells, eng, (-3000, yy, zz), 180, 200)) + (180,))
for sg in (1, -1):
    for sz in (1, -1):
        nozzle(bells, eng, (-2560, sg * 760, sz * 470), 55, 60, axis=(0, sg, 0), sides=10)
blk.finish(box_uv_scale=1024, recalc=False)
bells.finish(box_uv_scale=1024, recalc=False)
eng.finish(recalc=False)
spikes = Part(col, 'hauler exhaust', mat('neon_amber'))
for (x, y, z, r) in nozzles:
    exhaust(spikes, x - 4, y, z, r * 0.55, r * 1.9)
spikes.finish()

# ---- amber running lines: keel, cockpit waist, engine block edges, the billboard's rim ---------------------------------------------
neon = Part(col, 'hauler neon', mat(ACCENT))
for sg in (1, -1):
    tube(neon, [(-2480, sg * 150, -178), (1720, sg * 150, -178)], 50)
    tube(neon, [r[2 if sg > 0 else 7] for r in rings], 55)
    tube(neon, [(-2040, sg * 612, ZS - 14), (1580, sg * 612, ZS - 14)], 50)
for yy in (-670, 670):
    for zz in (-440, 440):
        tube(neon, [(-3010, yy, zz), (-2440, yy, zz)], 55)
neon.finish()

# ---- running lights + mast tips ----------------------------------------------------------------------------------------------------
navr = Part(col, 'hauler nav red', mat('nav_red'))
light_box(navr, (2000, 640, 0), 140)
navr.finish()
navg = Part(col, 'hauler nav green', mat('nav_green'))
light_box(navg, (2000, -640, 0), 140)
navg.finish()
navw = Part(col, 'hauler running lights', mat('neon_white'))
light_box(navw, (2960, 0, 0), 100)
for tip in tips:
    light_box(navw, tuple(tip), 60)
for x in range(1500, -2400, -500):
    light_box(navw, (x, 0, -300), 40)
navw.finish()
for sg in (1, -1):
    deco_quad(deco, (2000, sg * 598, 230), (-sg, 0, 0), (0, 0, 1), 700, 186, DECO_CELLS['haul07'])
for p in (cpl, spine, cframe, bb):
    p.finish(box_uv_scale=1024, recalc=False)
deco.finish(recalc=False)
lamps.finish()
win.finish(recalc=False)
ads.finish(recalc=False)

# ================================================================================================================
# v3 DETAIL (user 2026-09-29 15:40: "one more detailed pass ... focus on quality and detail of each")
# ================================================================================================================
v3h = Part(col, 'hauler detail v3', mat('hull'))
v3h2 = Part(col, 'hauler detail v3 light', mat('hull2'))
v3win = Part(col, 'hauler windows v3', mat('windows'))
bulbs = Part(col, 'hauler marquee bulbs', mat('glass'))
v3nav = Part(col, 'hauler running lights v3', mat('neon_white'))
# THE BRIDGE TOWER on the cockpit's back: a lit wheelhouse, a comms dish, a beacon mast
frustum_box(v3h2, (1880, 0, 470), (X, Y, Z), (230, 200, 90), (180, 150))
frustum_box(v3h2, (1860, 0, 600), (X, Y, Z), (130, 110, 40), (100, 85))
for sg in (1, -1):
    quad_facing(v3win, [(1680, sg * 177, 480), (2080, sg * 177, 480), (2080, sg * 177, 540), (1680, sg * 177, 540)], (0, sg, 0.15),
                [(0, 0.78), (0.6, 0.78), (0.6, 0.95), (0, 0.95)])
quad_facing(v3win, [(2092, -150, 480), (2092, 150, 480), (2092, 150, 540), (2092, -150, 540)], (1, 0, 0.1), [(0, 0.78), (0.3, 0.78), (0.3, 0.95), (0, 0.95)])
dish(v3h2, (1760, 110, 690), (-0.3, 0.4, 0.85), 80, 26)
bt = mast(v3h2, (1900, -60, 640), 260, 12, bars=2, bar_len=110)
light_box(v3nav, tuple(bt), 40)
# TWIN FUEL TANKS along the spine top, banded, on saddles
for yy in (-95, 95):
    cyl(v3h, (1450, yy, 395), (-2250, yy, 395), 88, 88, sides=16, caps=(True, True))
    for xb in range(1300, -2200, -420):
        cyl(v3h2, (xb + 18, yy, 395), (xb - 18, yy, 395), 96, 96, sides=16)
        abox(v3h2, xb - 25, xb + 25, yy - 70, yy + 70, 290, 330)
# TWO GANTRY CRANES straddling the cargo
for xc in (820, -1640):
    for sg in (1, -1):
        abox(v3h2, xc - 34, xc + 34, sg * 850, sg * 910, -380, 560)
    abox(v3h2, xc - 40, xc + 40, -910, 910, 540, 600)
    abox(v3h2, xc - 70, xc + 70, 280, 420, 470, 540)                  # the trolley
    cyl(v3h2, (xc, 350, 470), (xc, 350, 330), 8, 8, sides=6)           # the hoist line
    abox(v3h2, xc - 40, xc + 40, 320, 380, 300, 330)                   # the hook block
    for sg in (1, -1):
        light_box(v3nav, (xc, sg * 912, 604), 30)
# LOCK BARS on every container's end doors (the aft face of each container)
for cx in (1250, 430, -390, -1210, -2030):
    for (y0, y1) in ((230, 830), (-830, -230)):
        for (z0, z1) in ((-370, -40), (-20, 310)):
            for yb in (y0 + 90, y0 + 200, y1 - 200, y1 - 90):
                abox(v3h2, cx - 398, cx - 390, yb - 7, yb + 7, z0 + 25, z1 - 25)
# MARQUEE BULBS framing every ad screen (a Vegas billboard in the sky)
for xc in (-1310, -210, 890):
    for i in range(14):
        xx = xc - 520 + i * 80
        for yy in (-548, 548):
            light_box(bulbs, (xx, yy, ZS - 18), 26)
    for i in range(13):
        yy = -520 + i * 80
        for xx in (xc - 540, xc + 540):
            light_box(bulbs, (xx, yy, ZS - 18), 26)
for sg in (1, -1):                                                     # round the engine-block portrait screens
    for i in range(9):
        zz = -350 + i * 87
        for xx in (-2966, -2484):
            light_box(bulbs, (xx, sg * 668, zz), 24)
    for i in range(6):
        xx = -2960 + i * 94
        for zz in (-368, 368):
            light_box(bulbs, (xx, sg * 668, zz), 24)
for p in (v3h, v3h2):
    p.finish(box_uv_scale=1024, recalc=False)
v3win.finish(recalc=False)
bulbs.finish()
v3nav.finish()

LIGHTS = [[2980, 0, 0, 's'], [-3000, 0, 520, 's'], [round(tips[2].x), 0, round(tips[2].z) + 40, 'b'], [0, 0, -560, 'b'],
          [1560, 640, ZS, 's'], [1560, -640, ZS, 's']]
col['accent'] = ACCENT
col['length'] = 6420
col['nozzles'] = json.dumps([[round(v, 1) for v in n] for n in nozzles])
col['lights'] = json.dumps(LIGHTS)
objs = [o for o in col.objects]
frame(objs)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
print('SKY_SHIP_BUILT', KEY, 'parts', len(objs), 'tris', tris)
