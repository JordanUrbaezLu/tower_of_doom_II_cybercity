"""THE SKY FLEET - the GUNSHIP (docs/192). ~3,300 units bow to stern.

Silhouette you can name at a glance: a FORKED bow (two prongs), FORWARD-SWEPT wings, twin canted TAIL FINS and
two drives. v2 (user 2026-09-29: "a lot more detail"): a plated fuselage with side intakes, railgun prongs with
rails and glowing emitters, panelled wings with wingtip pods and under-wing missile racks, a chin ball turret, a
framed canopy, a dorsal sensor mast and dome, a searchlight under the nose, flanged drives and GS-13 markings.
"""
import bpy, sys, importlib, pathlib, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib, detail_lib
importlib.reload(sky_lib)
importlib.reload(detail_lib)
from sky_lib import Part, mat, ship_collection, loft, tube, band, bar_x, slab, fin, light_box, frame, exhaust, quad_facing
from detail_lib import (abox, obox, frustum_box, cyl, dome, mast, vent_bank, nozzle, plates_on_loft, deco_quad, basis, _face)
from sky_data import DECO_CELLS

KEY = 'gunship'
OFFSET = (0, -12000, 0)
col = ship_collection(KEY, OFFSET)
ACCENT = 'neon_magenta'      # variant B: neon_green
rng = np.random.default_rng(1940)
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

# ---- the fuselage: stations (x, half-width w, top t, bottom b)
S = [(1100, 70, 60, -60), (700, 220, 150, -130), (0, 300, 200, -170), (-900, 320, 210, -180), (-1500, 280, 180, -160)]
def ring(x, w, t, b):
    return [(x, 0.35 * w, t), (x, w, 0.2 * t), (x, 0.6 * w, b), (x, -0.6 * w, b), (x, -w, 0.2 * t), (x, -0.35 * w, t)]
rings = [ring(*s) for s in S]
body = Part(col, 'gunship fuselage', mat('hull'))
loft(body, rings)
body.finish(box_uv_scale=768)
bpl = Part(col, 'gunship plates', mat('hull2'))
plates_on_loft(bpl, rings, rng, nu=5, nv=2, hmin=5, hmax=14, inset=9, skip=0.07, merge=0.35,
               keep=lambda c: not (250 < c.x < 700 and c.z > 120))                     # the canopy stays clear

# ---- the fork: two railgun prongs reaching past the nose, rails along them, emitters at the tips -----------------------
prong = Part(col, 'gunship prongs', mat('hull2'))
det = Part(col, 'gunship detail', mat('hull2'))
for sg in (1, -1):
    bar_x(prong, 500, 1560, (sg * 200, sg * 420, -100, 70) if sg > 0 else (sg * 420, sg * 200, -100, 70),
          (sg * 250, sg * 330, -50, 30) if sg > 0 else (sg * 330, sg * 250, -50, 30))
    for zz in (78, -108):                                          # rails above and below each prong
        abox(det, 560, 1500, sg * 250, sg * 370, zz - 8, zz + 8)
    for xr in range(620, 1480, 120):                               # coil rings along the prong
        abox(det, xr - 14, xr + 14, sg * 190 - 12 * sg, sg * 430 + 12 * sg, -110, 80)
prong.finish(box_uv_scale=768)

# ---- forward-swept wings: panels, tip pods, missile racks ---------------------------------------------------------------
wing = Part(col, 'gunship wings', mat('hull'))
wpl = Part(col, 'gunship wing panels', mat('hull2'))
for sg in (1, -1):
    slab(wing, [(-900, sg * 280), (-200, sg * 280), (150, sg * 1150), (-350, sg * 1150)], -80, -20)
    for i in range(4):                                             # raised panels on the wing's top and bottom
        f0, f1 = 0.05 + i * 0.23, 0.05 + i * 0.23 + 0.19
        yy0, yy1 = 280 + (1150 - 280) * f0, 280 + (1150 - 280) * f1
        xl0, xt0 = -200 + 350 * f0, -900 + 550 * f0                # leading / trailing x at f0
        xl1, xt1 = -200 + 350 * f1, -900 + 550 * f1
        for (zb, zt) in ((-20, -12), (-88, -80)):
            pts_b = [(xt0 + 30, sg * yy0, zb), (xl0 - 30, sg * yy0, zb), (xl1 - 30, sg * yy1, zb), (xt1 + 30, sg * yy1, zb)]
            pts_t = [(p[0], p[1], zt) for p in pts_b]
            ctr = Vector(((xt0 + xl1) / 2, sg * (yy0 + yy1) / 2, (zb + zt) / 2))
            _face(wpl, pts_t if zb > -50 else pts_b, ctr)
            _face(wpl, pts_b if zb > -50 else pts_t, ctr)
            for a in range(4):
                b = (a + 1) % 4
                _face(wpl, [pts_b[a], pts_b[b], pts_t[b], pts_t[a]], ctr)
    cyl(det, (-420, sg * 1160, -50), (180, sg * 1160, -50), 55, 55, sides=10)        # wingtip pods
    cyl(det, (180, sg * 1160, -50), (300, sg * 1160, -50), 55, 10, sides=10, caps=(False, True))
    for yy in (560, 820):                                          # under-wing missile racks: a pylon + six tubes
        abox(det, -420, -60, sg * (yy - 30), sg * (yy + 30), -150, -80)
        abox(det, -460, -20, sg * (yy - 70), sg * (yy + 70), -250, -150)
        for (ty, tz) in ((-40, -175), (0, -175), (40, -175), (-40, -225), (0, -225), (40, -225)):
            cyl(det, (-20, sg * yy + ty, tz), (40, sg * yy + ty, tz), 16, 12, sides=6)
wing.finish(box_uv_scale=768)

# ---- twin canted tail fins, with stripes and tip antennas --------------------------------------------------------------
fins = Part(col, 'gunship fins', mat('hull2'))
for sg in (1, -1):
    fin(fins, [(-1500, 170), (-1080, 170), (-1330, 640), (-1540, 640)], sg * 230, 22, cant=0.35)
    y_top = sg * (230 + 0.35 * 640)
    cyl(det, (-1460, y_top, 640), (-1460, y_top + sg * 0.35 * 240, 880), 6, 3, sides=5)   # antenna
fins.finish(box_uv_scale=768)

# ---- the nose: chin ball turret, searchlight, sensor dome + dorsal mast, intakes -------------------------------------------
dome(det, (420, 0, -150), (0, 0, -1), 95)                           # the chin ball turret
for sg in (1, -1):
    cyl(det, (470, sg * 30, -210), (760, sg * 30, -230), 12, 10, sides=6)
dome(det, (-300, 0, 205), (0, 0, 1), 70)
tip = mast(det, (-650, 0, 205), 300, 12, bars=2, bar_len=110)
for sg in (1, -1):                                                 # side intakes ahead of the drives
    obox(det, (-700, sg * 318, 30), (X, Y, Z), (220, 40, 90))
    abox(det, -450, -440, sg * 290, sg * 360, -50, 110)
    vent_bank(det, (-1300, sg * 290, 60), (1, 0, 0), (0, sg, 0.3), 5, 60, 30, 90, 14)
search = Part(col, 'gunship searchlight', mat('neon_white'))
cyl(search, (560, 0, -120), (560, 0, -170), 60, 60, sides=12)

# ---- canopy glass with frame bars ------------------------------------------------------------------------------------------
glass = Part(col, 'gunship canopy', mat('glass'))
band(glass, [(700, 60, 152), (250, 70, 190)], [(700, -60, 152), (250, -70, 190)], 6, outward=(0, 0, 1))
glass.finish(recalc=False)
for xf in (600, 470, 340):
    zf = 152 + (190 - 152) * (700 - xf) / 450
    abox(det, xf - 8, xf + 8, -80, 80, zf - 2, zf + 16)
abox(det, 250, 700, -8, 8, 150, 205)

# ---- drives ----------------------------------------------------------------------------------------------------------------
bells = Part(col, 'gunship engine bells', mat('drive_metal'))
eng = Part(col, 'gunship engines', mat('engine_cyan'))
nozzles = []
for yy in (-200, 200):
    nozzles.append(tuple(nozzle(bells, eng, (-1480, yy, -10), 150, 210)) + (150,))
bells.finish(box_uv_scale=768, recalc=False)
eng.finish(recalc=False)
spikes = Part(col, 'gunship exhaust', mat('neon_cyan'))
for (x, y, z, r) in nozzles:
    exhaust(spikes, x - 4, y, z, r * 0.55, r * 2.0)
spikes.finish()

# ---- neon: prong outer edges, wing leading edges + tips, the dorsal line, the fin leading edges, emitters -------------------
neon = Part(col, 'gunship neon', mat(ACCENT))
for sg in (1, -1):
    tube(neon, [(520, sg * 425, -15), (1560, sg * 335, -10), (1560, sg * 245, -10), (520, sg * 195, -15)], 45)
    tube(neon, [(-200, sg * 285, -50), (150, sg * 1150, -50), (-350, sg * 1150, -50), (-900, sg * 285, -50)], 45)
    tube(neon, [(-1080, sg * (230 + 0.35 * 170), 170), (-1330, sg * (230 + 0.35 * 640), 640)], 40)
    abox(neon, 1560, 1620, sg * 250, sg * 330, -50, 30)            # railgun emitters at the prong tips
tube(neon, [(r[0][0], 0, r[0][2] + 8) for r in rings[1:]], 40)
neon.finish()

# ---- running lights + markings --------------------------------------------------------------------------------------------
navr = Part(col, 'gunship nav red', mat('nav_red'))
light_box(navr, (-100, 1175, -50), 90)
navr.finish()
navg = Part(col, 'gunship nav green', mat('nav_green'))
light_box(navg, (-100, -1175, -50), 90)
navg.finish()
navw = Part(col, 'gunship strobes', mat('neon_white'))
for sg in (1, -1):
    light_box(navw, (-1440, sg * (230 + 0.35 * 660), 660), 70)
light_box(navw, tuple(tip), 40)
navw.finish()
search.finish()
deco = Part(col, 'gunship markings', mat('deco'))
for sg in (1, -1):
    deco_quad(deco, (-250, sg * 306, 40), (-sg, 0, 0), (0, 0, 1), 420, 118, DECO_CELLS['gs13'])
    deco_quad(deco, (-380, sg * 720, -92), (1, 0, 0), (0, -1, 0), 380, 107, DECO_CELLS['gs13'])      # under each wing
deco.finish(recalc=False)
for p in (bpl, det, wpl):
    p.finish(box_uv_scale=768, recalc=False)

# ================================================================================================================
# v3 DETAIL (user 2026-09-29 15:40: "one more detailed pass ... focus on quality and detail of each")
# ================================================================================================================
from detail_lib import turret
v3h = Part(col, 'gunship detail v3', mat('hull2'))
v3n = Part(col, 'gunship shield emitters', mat(ACCENT))
v3d = Part(col, 'gunship markings v3', mat('deco'))
v3nav = Part(col, 'gunship landing lights', mat('neon_white'))
turret(v3h, (-420, 0, 200), 78, yaw_deg=0, up=(0, 0, 1), barrels=2, barrel_len=2.8, barrel_r=0.1)     # dorsal twin cannon
for sg in (1, -1):                                                      # shield emitters on the prongs' inner faces
    cyl(v3n, (900, sg * 188, -15), (900, sg * 170, -15), 46, 46, sides=12)
    cyl(v3n, (1250, sg * 238, -10), (1250, sg * 222, -10), 34, 34, sides=12)
cyl(v3h, (300, 0, -205), (-500, 0, -205), 46, 46, sides=10)            # the belly sensor pod
cyl(v3h, (300, 0, -205), (420, 0, -205), 46, 14, sides=10, caps=(False, True))
for (x, y, z, r) in nozzles:                                            # afterburner petals round each drive
    for k in range(10):
        a = 2 * math.pi * k / 10
        rad = Vector((0, math.cos(a), math.sin(a)))
        c = Vector((x + 20, y, z)) + rad * (r * 1.02)
        f, l, u = basis(Vector((-1, 0, 0)) + rad * 0.35, rad)
        obox(v3h, c, (f, l, u), (46, r * 0.26, 5))
for sg in (1, -1):                                                      # trailing-edge flaps
    for f0 in (0.1, 0.4, 0.7):
        yy = 280 + (1150 - 280) * (f0 + 0.12)
        xt = -900 + 550 * (f0 + 0.12)
        abox(v3h, xt - 60, xt + 10, sg * (yy - 120), sg * (yy + 120), -74, -60)
    fx_ = -1420
    yf = sg * (230 + 0.35 * 420)
    deco_quad(v3d, (fx_, yf + sg * 26, 420), (-sg, 0, 0), (0, sg * -0.33, 1), 230, 64, DECO_CELLS['gs13'])
    light_box(v3nav, (650, sg * 150, -150), 26)                          # landing lights under the chin
light_box(v3nav, (-100, 0, -230), 30)
# GREEBLE FIELDS on the dorsal fuselage and the wing tops (a gunship reads busy up close)
from detail_lib import block_field
def fus_sample():
    x = rng.uniform(-1400, 650)
    for (xa, *pa), (xb, *pb) in zip(S[:-1], S[1:]):
        if xb <= x <= xa:
            f0 = (xa - x) / (xa - xb)
            w, tt, bb = [pa[i] + (pb[i] - pa[i]) * f0 for i in range(3)]
            break
    else:
        return None
    if 250 < x < 700:
        return None                                                     # the canopy
    y = rng.uniform(-0.3 * w, 0.3 * w)
    return ((x, y, tt), (0, 0, 1))
def wing_sample():
    sg = 1 if rng.random() < 0.5 else -1
    f0 = rng.uniform(0.08, 0.9)
    yy = 280 + (1150 - 280) * f0
    xl, xt = -200 + 350 * f0, -900 + 550 * f0
    x = rng.uniform(xt + 40, xl - 60)
    return ((x, sg * yy, -20), (0, 0, 1))
block_field(v3h, rng, 70, fus_sample, (16, 60), (6, 26))
block_field(v3h, rng, 50, wing_sample, (20, 70), (4, 14))
v3h.finish(box_uv_scale=768, recalc=False)
v3n.finish()
v3d.finish(recalc=False)
v3nav.finish()

LIGHTS = [[-100, 1180, -50, 's'], [-100, -1180, -50, 's'], [round(tip.x), 0, round(tip.z) + 30, 'b'], [0, 0, -200, 'b']]
col['accent'] = ACCENT
col['length'] = 3300
col['nozzles'] = json.dumps([[round(v, 1) for v in n] for n in nozzles])
col['lights'] = json.dumps(LIGHTS)
objs = [o for o in col.objects]
frame(objs)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
print('SKY_SHIP_BUILT', KEY, 'parts', len(objs), 'tris', tris)
