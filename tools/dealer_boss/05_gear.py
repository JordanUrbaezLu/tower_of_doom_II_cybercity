"""05: the Dealer's merchandise - what makes him the Black Market's keeper and not
a generic reaper: a leather bandolier of glowing essence vials across the chest,
a locked satchel on the hip, a key ring on a chain, a string of tarnished
tokens, and the ledger chain at his throat.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
M = library()
gear = coll('04')
for ob in list(gear.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
SPINE = ['j_mainroot', 'j_spinelower', 'j_spineupper', 'j_spine4', 'j_clavicle_le', 'j_clavicle_ri']
leather = M['worn black leather']; brass = M['aged brass fittings']; steel = M['blackened steel']

# the coat's surface at height z and angle a (front = 0), from the 02 rings + a clearance
RINGS = [(-1.7, 0, 2.6, 14.6, 15.2), (-1.7, 0, 8, 13.6, 14.1), (-1.6, 0, 15, 12.2, 12.7), (-1.5, 0, 22, 10.8, 11.2),
         (-1.4, 0, 29, 9.5, 10.0), (-1.3, 0, 35, 8.6, 9.3), (-1.2, 0, 40, 8.0, 8.9), (-1.1, 0, 44.5, 7.4, 8.3),
         (-1.0, 0, 49, 7.5, 8.9), (-0.9, 0, 53.5, 7.9, 9.7), (-0.9, 0, 57, 8.1, 10.2), (-1.0, 0, 60, 7.6, 9.3)]
def surf(z, a, out=0.9):
    lo = max(r for r in RINGS if r[2] <= z) if any(r[2] <= z for r in RINGS) else RINGS[0]
    hi = min(r for r in RINGS if r[2] >= z) if any(r[2] >= z for r in RINGS) else RINGS[-1]
    t = 0 if hi[2] == lo[2] else (z - lo[2]) / (hi[2] - lo[2])
    cx = lo[0] + (hi[0] - lo[0]) * t; rx = lo[3] + (hi[3] - lo[3]) * t; ry = lo[4] + (hi[4] - lo[4]) * t
    return Vector((cx + (rx + out) * math.cos(a), (ry + out) * math.sin(a), z))

# ---------------------------------------------------------------- bandolier (right shoulder -> left hip, round the back)
band = []
for i in range(41):
    t = i / 40
    a = math.radians(-75 + 220 * t)          # from the right shoulder front, across the chest, to the left hip
    z = 56.5 - 17 * t
    band.append(surf(z, a, 0.75))
for i in range(41):
    t = i / 40
    a = math.radians(145 + 140 * t)          # round the back, climbing to the right shoulder
    z = 39.5 + 17 * t
    band.append(surf(z, a, 0.75))
band.append(band[0])
bandolier = tube('Gear | bandolier strap', band, [(0.3, 1.35)] * len(band), leather, gear, segments=10)
skin(bandolier, SPINE, sigma=6.5, k=3)
# vials: dark glass with a red essence inside, brass caps, held in stitched loops
for i, t in enumerate((0.47, 0.56, 0.65, 0.74, 0.83)):
    a = math.radians(-75 + 220 * t); z = 56.5 - 17 * t
    c = surf(z, a, 1.6)
    glass = tube('Gear | vial glass %d' % i, [c + Vector((0, 0, -2.0)), c + Vector((0, 0, 1.6))], [(0.9, 0.9), (0.85, 0.85)], M['dark glass vial'], gear, segments=14, cap_start=True)
    ess = tube('Gear | vial essence %d' % i, [c + Vector((0, 0, -1.8)), c + Vector((0, 0, 0.9 + 0.3 * math.sin(i * 1.7)))], [(0.62, 0.62), (0.6, 0.6)], M['red essence'], gear, segments=12, cap_start=True, cap_end=True)
    cap = tube('Gear | vial cap %d' % i, [c + Vector((0, 0, 1.5)), c + Vector((0, 0, 2.4))], [(0.95, 0.95), (0.8, 0.8)], brass, gear, segments=12, cap_end=True)
    loop = tube('Gear | vial loop %d' % i, [surf(z + 0.6, a, 0.7), c + Vector((0, 0, 0.6)) + (c - surf(z, a, 0.7)).normalized() * 0.95, surf(z + 0.6, a + 0.14, 0.7)], [0.16] * 3, M['red stitch thread'], gear, segments=8)
    for ob in (glass, ess, cap, loop):
        skin(ob, SPINE, sigma=6.5, k=3)
# the bandolier's brass buckle at the shoulder
bk = box('Gear | bandolier buckle', surf(54.5, math.radians(-70), 1.0), (0.35, 1.5, 1.3), brass, gear, bevel=0.1)
skin(bk, SPINE, sigma=6.5)

# ---------------------------------------------------------------- the satchel (left hip, under the bandolier's end)
sc = surf(39.5, math.radians(118), 2.3)
sat = box('Gear | locked satchel', sc, (2.1, 4.2, 3.6), leather, gear, bevel=0.35, rot=Matrix.Rotation(math.radians(118), 3, 'Z'))
displace_noise(sat, 0.12, 0.5, seed=41)
skin(sat, ['j_mainroot', 'j_robe_01_le', 'j_robe_back_01_le', 'j_hip_le'], sigma=5)
flap = box('Gear | satchel flap', sc + Vector((0, 0, 2.6)) + Vector((math.cos(math.radians(118)), math.sin(math.radians(118)), 0)) * 0.6, (2.4, 4.4, 1.2), leather, gear, bevel=0.3, rot=Matrix.Rotation(math.radians(118), 3, 'Z'))
skin(flap, ['j_mainroot', 'j_robe_01_le', 'j_hip_le'], sigma=5)
lock = box('Gear | satchel lock plate', sc + Vector((math.cos(math.radians(118)), math.sin(math.radians(118)), 0)) * 2.4 + Vector((0, 0, 0.4)), (0.3, 1.1, 1.3), steel, gear, bevel=0.1, rot=Matrix.Rotation(math.radians(118), 3, 'Z'))
skin(lock, ['j_mainroot', 'j_robe_01_le'], sigma=5)
strap = tube('Gear | satchel strap', [surf(44.0, math.radians(100), 0.6), surf(43.0, math.radians(112), 1.3), sc + Vector((0, 0, 3.6))], [(0.25, 0.9)] * 3, leather, gear, segments=8)
skin(strap, ['j_mainroot', 'j_spinelower'], sigma=5)

# ---------------------------------------------------------------- key ring and chain (right hip)
kc = surf(43.5, math.radians(-105), 0.9)
chain_pts = [kc + Vector((0, 0, 0.3)) + Vector((0.15 * math.sin(i * 1.3), 0.1 * math.cos(i * 1.1), -1.05 * i)) for i in range(7)]
chain = tube('Gear | belt chain', chain_pts, [0.18] * 7, steel, gear, segments=8, noise_amt=0.05)
skin(chain, ['j_mainroot', 'j_hip_ri', 'j_robe_01_ri'], sigma=5)
ring_c = chain_pts[-1] + Vector((0, 0, -1.1))
ring_pts = [ring_c + Vector((1.1 * math.cos(a), 0, 1.1 * math.sin(a))) for a in [i * math.tau / 20 for i in range(21)]]
ring = tube('Gear | key ring', ring_pts, [0.16] * 21, steel, gear, segments=8)
skin(ring, ['j_hip_ri', 'j_robe_01_ri'], sigma=5)
for i, ang in enumerate((-0.4, 0.15, 0.7)):
    kp = ring_c + Vector((1.1 * math.cos(-math.pi / 2 + ang), 0, 1.1 * math.sin(-math.pi / 2 + ang)))
    key = box('Gear | key %d' % i, kp + Vector((0.25 * math.sin(ang), 0, -1.4)), (0.12, 0.28, 1.3), brass, gear, bevel=0.05)
    bit = box('Gear | key bit %d' % i, kp + Vector((0.25 * math.sin(ang), 0.3, -2.4)), (0.12, 0.45, 0.35), brass, gear)
    skin(key, ['j_hip_ri', 'j_robe_01_ri'], sigma=5); skin(bit, ['j_hip_ri', 'j_robe_01_ri'], sigma=5)

# ---------------------------------------------------------------- a string of tokens on the chest (the Black Market's coin)
cord = [surf(58.5, math.radians(10), 0.8) + Vector((0, 0, -0.9 * i)) + Vector((0.2 * math.sin(i), 0.15 * i, 0)) for i in range(5)]
cord_ob = tube('Gear | token cord', cord, [0.09] * 5, M['red stitch thread'], gear, segments=6)
skin(cord_ob, SPINE, sigma=6)
for i in range(3):
    c = cord[-1] + Vector((0.35, 0.0, -0.9 - 1.25 * i))
    coin = tube('Gear | token %d' % i, [c + Vector((-0.12, 0, 0)), c + Vector((0.12, 0, 0))], [(0.75, 0.75), (0.75, 0.75)], M['tarnished silver coin'], gear, segments=18, cap_start=True, cap_end=True)
    skin(coin, SPINE, sigma=6)

# ---------------------------------------------------------------- the ledger chain at the throat
tc = [surf(63.5, math.radians(-40 + 80 * i / 10), 0.5) for i in range(11)]
throat = tube('Gear | throat chain', tc, [0.14] * 11, steel, gear, segments=8, noise_amt=0.03)
skin(throat, ['j_spine4', 'j_neck', 'j_clavicle_le', 'j_clavicle_ri'], sigma=5)
pend = box('Gear | ledger seal pendant', surf(62.2, 0, 0.8), (0.25, 0.9, 1.1), brass, gear, bevel=0.1)
skin(pend, ['j_spine4', 'j_neck'], sigma=5)

view_hero()
save('05_gear')
print(json.dumps({'stage': '05_gear', 'gear_objects': len(gear.objects)}))
