"""THE SKY FLEET - the FIGHTER (docs/192). ~900 units nose to tail; flies in V wings of three to five.

Silhouette you can name at a glance: a DELTA DART. A big triangle of wing, twin canted fins, one fat drive. v2
(user 2026-09-29: "a lot more detail"): a plated body, wing root intakes, panelled wings with two missiles under
each, a framed canopy, fin-top lights, a flanged drive. Small ships read by LIGHT (the engine and the neon delta);
the detail is for the close pass.
"""
import bpy, sys, importlib, pathlib, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib, detail_lib
importlib.reload(sky_lib)
importlib.reload(detail_lib)
from sky_lib import Part, mat, ship_collection, loft, tube, band, slab, fin, light_box, frame, exhaust
from detail_lib import abox, obox, cyl, nozzle, plates_on_loft, _face

KEY = 'fighter'
OFFSET = (0, -21000, 0)
col = ship_collection(KEY, OFFSET)
ACCENT = 'neon_cyan'         # variant B: neon_orange
rng = np.random.default_rng(1950)

S = [(400, 15, 15, -15), (220, 70, 55, -40), (-120, 110, 70, -50), (-400, 95, 60, -45)]
def ring(x, w, t, b):
    return [(x, 0.35 * w, t), (x, w, 0.2 * t), (x, 0.6 * w, b), (x, -0.6 * w, b), (x, -w, 0.2 * t), (x, -0.35 * w, t)]
rings = [ring(*s) for s in S]
body = Part(col, 'fighter body', mat('hull'))
loft(body, rings)
body.finish(box_uv_scale=384)
bpl = Part(col, 'fighter plates', mat('hull2'))
plates_on_loft(bpl, rings, rng, nu=3, nv=1, hmin=2.5, hmax=6, inset=5, skip=0.1, merge=0.3,
               keep=lambda c: not (40 < c.x < 250 and c.z > 40))

wing = Part(col, 'fighter wings', mat('hull'))
det = Part(col, 'fighter detail', mat('hull2'))
for sg in (1, -1):
    slab(wing, [(-390, sg * 80), (140, sg * 80), (-360, sg * 430)], -26, -4)
    for (a, b) in ((0.15, 0.45), (0.5, 0.8)):                      # two raised panels per wing
        y0, y1 = 80 + 350 * a, 80 + 350 * b
        xl0, xl1 = 140 - 500 * a, 140 - 500 * b
        xt = -380
        pts = [(xt + 15, sg * y0, -3), (xl0 - 25, sg * y0, -3), (xl1 - 25, sg * y1, -3), (xt + 15, sg * y1, -3)]
        top = [(p[0], p[1], 1) for p in pts]
        ctr = Vector(((xt + xl0) / 2, sg * (y0 + y1) / 2, -1))
        _face(det, top, ctr)
        for i in range(4):
            j = (i + 1) % 4
            _face(det, [pts[i], pts[j], top[j], top[i]], ctr)
    for yy in (190, 300):                                          # missiles under each wing
        abox(det, -250, -120, sg * (yy - 8), sg * (yy + 8), -40, -26)
        cyl(det, (-300, sg * yy, -52), (-40, sg * yy, -52), 13, 13, sides=8)
        cyl(det, (-40, sg * yy, -52), (10, sg * yy, -52), 13, 1, sides=8, caps=(False, True))
    abox(det, -90, 150, sg * 70, sg * 118, -30, 40)                 # wing-root intakes
wing.finish(box_uv_scale=384)

fins = Part(col, 'fighter fins', mat('hull2'))
for sg in (1, -1):
    fin(fins, [(-400, 50), (-250, 50), (-350, 210), (-410, 210)], sg * 70, 9, cant=0.35)
fins.finish(box_uv_scale=384)

bells = Part(col, 'fighter engine bell', mat('drive_metal'))
eng = Part(col, 'fighter engine', mat('engine_cyan'))
nz = nozzle(bells, eng, (-400, 0, 0), 78, 70, sides=16)
nozzles = [tuple(nz) + (78,)]
bells.finish(box_uv_scale=384, recalc=False)
eng.finish(recalc=False)
spike = Part(col, 'fighter exhaust', mat('neon_cyan'))
exhaust(spike, nz.x - 4, 0, 0, 78 * 0.55, 78 * 2.2)
spike.finish()

neon = Part(col, 'fighter neon', mat(ACCENT))
for sg in (1, -1):
    tube(neon, [(150, sg * 82, -15), (-360, sg * 432, -15), (-392, sg * 82, -15)], 22)
    tube(neon, [(-250, sg * (70 + 0.35 * 50), 50), (-350, sg * (70 + 0.35 * 210), 210)], 18)
neon.finish()

glass = Part(col, 'fighter canopy', mat('neon_white'))
band(glass, [(240, 22, 57), (40, 30, 66)], [(240, -22, 57), (40, -30, 66)], 3, outward=(0, 0, 1))
glass.finish(recalc=False)
for xf in (180, 110):
    zf = 57 + (66 - 57) * (240 - xf) / 200
    abox(det, xf - 4, xf + 4, -32, 32, zf - 1, zf + 7)

navr = Part(col, 'fighter nav red', mat('nav_red'))
light_box(navr, (-362, 440, -15), 36)
navr.finish()
navg = Part(col, 'fighter nav green', mat('nav_green'))
light_box(navg, (-362, -440, -15), 36)
navg.finish()
navw = Part(col, 'fighter fin lights', mat('neon_white'))
for sg in (1, -1):
    light_box(navw, (-405, sg * (70 + 0.35 * 212), 212), 22)
navw.finish()
for p in (bpl, det):
    p.finish(box_uv_scale=384, recalc=False)

# ================================================================================================================
# v3 DETAIL (user 2026-09-29 15:40: "one more detailed pass ... focus on quality and detail of each")
# ================================================================================================================
from detail_lib import basis
from mathutils import Vector
v3h = Part(col, 'fighter detail v3', mat('hull2'))
v3n = Part(col, 'fighter stripe', mat(ACCENT))
for sg in (1, -1):                                                      # canards near the nose
    slab(v3h, [(250, sg * 55), (330, sg * 55), (240, sg * 150)], 6, 12)
    abox(v3h, -60, 150, sg * 116, sg * 122, -28, 38)                     # intake splitter plates
abox(v3h, -380, 40, -14, 14, 60, 84)                                     # the dorsal spine
tube(v3n, [(40, 0, 88), (-380, 0, 88)], 10)                              # the racing stripe along it
cyl(v3h, (400, 0, 0), (470, 0, 0), 6, 2, sides=6)                        # the nose sensor spike
for k in range(10):                                                      # afterburner petals
    a = 2 * math.pi * k / 10
    rad = Vector((0, math.cos(a), math.sin(a)))
    c = Vector((nz.x + 12, 0, 0)) + rad * 80
    f, l, u = basis(Vector((-1, 0, 0)) + rad * 0.35, rad)
    obox(v3h, c, (f, l, u), (22, 18, 2.5))
from detail_lib import block_field
def body_sample():
    x = rng.uniform(-360, 200)
    if 40 < x < 250:
        return None                                                     # the canopy
    return ((x, rng.uniform(-40, 40), 62), (0, 0, 1))
def wing_top():
    sg = 1 if rng.random() < 0.5 else -1
    y = rng.uniform(100, 380)
    xl = 140 - 500 * (y - 80) / 350
    return ((rng.uniform(-370, xl - 30), sg * y, -4), (0, 0, 1))
block_field(v3h, rng, 22, body_sample, (6, 22), (2, 8))
block_field(v3h, rng, 26, wing_top, (8, 28), (1.5, 5))
v3h.finish(box_uv_scale=384, recalc=False)
v3n.finish()

LIGHTS = [[-362, 446, -15, 's'], [-362, -446, -15, 's']]
col['accent'] = ACCENT
col['length'] = 900
col['nozzles'] = json.dumps([[round(v, 1) for v in n] for n in nozzles])
col['lights'] = json.dumps(LIGHTS)
objs = [o for o in col.objects]
frame(objs)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
print('SKY_SHIP_BUILT', KEY, 'parts', len(objs), 'tris', tris)
