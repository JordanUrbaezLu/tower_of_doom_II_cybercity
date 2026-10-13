"""03: the Dealer's head - the deep hood, the void inside it, and THE MASK.

The mask is the shop merchant's own construction (tools/partner_shop/04 + 16),
re-expressed in BO3 model space so the boss and the shopkeeper share one face:
a graphite dome, slanted red X eyes with one weak stroke, overhanging brow
plates, hollow cheek plates, a split nose bridge, a jagged grin seam with nine
uneven teeth, a scar and a torn corner.

The hood is a drooping executioner's cowl: a tall oval opening whose brow
leans out over the mask, cloth that falls past the jaw onto the mantle, and a
peak that sags down behind the skull.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
M = library()
head = coll('02')
for ob in list(head.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

HEAD_BONES = ['j_head', 'j_neck2', 'j_neck', 'j_spine4']
HEAD_C = Vector((1.6, 0, 69.6))
MASK_Z = 71.4
MASK_X0 = -2.4
MASK_SCALE = 1.04
hoodmat = M['hood black wool']; lining = M['oxblood satin lining']

# ---------------------------------------------------------------- the void behind the mask
void = sphere('Head | black void', HEAD_C, (5.6, 5.1, 6.6), M['mask void black'], head, rings=18, segments=28)
fixed_bone(void, 'j_head')
# the void is in BOTH states: state two (10_state2_mask.py) shows it through the chips of the cracked mask
neck = tube('Head | wrapped neck', [Vector((-0.4, 0, 60.5)), Vector((0.2, 0, 63.5)), Vector((1.0, 0, 66.5)), Vector((1.5, 0, 68.5))],
            [(3.6, 3.6), (3.4, 3.4), (3.4, 3.3), (3.8, 3.6)], hoodmat, head, segments=24, noise_amt=0.1)
skin(neck, ['j_spine4', 'j_neck', 'j_neck2', 'j_head'], chain_blend=True)

# ---------------------------------------------------------------- THE MASK
def face_y(x, z):
    return -8.05 - 2.05 * math.sqrt(max(0.04, 1 - (x / 6.0) ** 2 - ((z - 71.1) / 8.25) ** 2))
def to_bo3(xs, ys, zs):
    return Vector((MASK_X0 - ys * MASK_SCALE, -xs * MASK_SCALE, MASK_Z + (zs - 71.1) * MASK_SCALE))

verts = []; faces = []; N = 96
for j in range(25):
    r = 0.015 + 0.985 * j / 24
    for i in range(N):
        a = i * math.tau / N
        zs = 71.1 + 8.15 * r * math.cos(a)
        xs = 5.65 * (0.80 + 0.20 * max(0, math.cos(a))) * r * math.sin(a)
        verts.append(to_bo3(xs, face_y(xs, zs), zs))
for j in range(24):
    for i in range(N):
        faces.append((j * N + i, j * N + (i + 1) % N, (j + 1) * N + (i + 1) % N, (j + 1) * N + i))
faces.append(tuple(range(N - 1, -1, -1)))
mask = mesh('Mask | graphite molded shell', verts, faces, M['graphite molded mask'], head)
solidify(mask, 0.26, offset=1)
displace_noise(mask, 0.05, 0.9, seed=21)
fixed_bone(mask, 'j_head')

led = M['red neon wire']; weak = M['red neon wire weak']; maskmat = M['graphite molded mask']
def wire(name, xz, r=0.11, mat=led):
    depth = 0.60 if any(t in name for t in ('grin', 'tooth', 'corner')) else 0.28
    pts = [to_bo3(x, face_y(x, z) - depth, z) for x, z in xz]
    ob = tube('Mask | ' + name, pts, [r] * len(pts), mat, head, segments=10)
    fixed_bone(ob, 'j_head'); return ob
def plate(name, xz, depth=0.35, thick=0.22):
    pts = [to_bo3(x, face_y(x, z) - depth, z) for x, z in xz]
    ob = mesh('Mask | ' + name, pts, [tuple(range(len(pts)))], maskmat, head, smooth=False, bevel=0.06)
    solidify(ob, thick); fixed_bone(ob, 'j_head'); return ob
for s in (-1, 1):
    wire('slanted X long %d' % s, [(s * 4.0, 76.0), (s * 2.65, 74.75), (s * 1.2, 73.6)], 0.15)
    wire('slanted X cut %d' % s, [(s * 4.0, 73.9), (s * 2.65, 74.75), (s * 1.5, 75.45)], 0.11, weak if s == 1 else led)
    plate('overhanging brow %d' % s, [(s * 0.85, 75.8), (s * 4.55, 77.6), (s * 4.35, 76.5), (s * 1.05, 75.0)], 0.47, 0.3)
    plate('hollow cheek %d' % s, [(s * 1.45, 70.5), (s * 4.5, 72.8), (s * 4.8, 70.0), (s * 3.3, 67.5), (s * 2.1, 68.3)], 0.33, 0.25)
plate('split nose bridge', [(-0.65, 75.5), (0, 77.1), (0.6, 75.5), (0.95, 71.1), (0, 70.1), (-0.85, 71.25)], 0.5, 0.35)
wire('jagged grin seam', [(-4.55, 69.8), (-3.8, 68.7), (-2.6, 68.3), (-1.3, 67.35), (-0.2, 67.65), (1, 67.2), (2.2, 68.0), (3.6, 68.35), (4.55, 70.3)], 0.13)
for i, (x, z, h) in enumerate([(-3.8, 68.7, 1.4), (-2.95, 68.5, 2.1), (-2.05, 67.95, 1.55), (-1.2, 67.35, 2.15), (-0.3, 67.65, 1.25), (0.65, 67.35, 1.85), (1.55, 67.6, 1.4), (2.5, 68.1, 2.35), (3.4, 68.3, 1.45)]):
    wire('uneven tooth %d' % i, [(x - 0.17, z + 0.65), (x + 0.04, z - h), (x + 0.33, z + 0.32)], 0.075 if i % 3 else 0.095)
wire('left scar', [(-4.35, 72.6), (-4.0, 71.7), (-4.3, 71.15)], 0.052, weak)
wire('right torn corner', [(4.3, 69.95), (4.7, 71.0), (4.4, 71.4)], 0.07)
wire('brow fracture', [(-3.2, 77.2), (-2.4, 76.4), (-2.6, 75.6), (-1.9, 75.0)], 0.04, weak)
for s in (-1, 1):
    rv = sphere('Mask | temple rivet %d' % s, to_bo3(s * 5.6, face_y(s * 5.6, 72.0) - 0.1, 72.0), 0.42, M['blackened steel'], head, rings=8, segments=12)
    fixed_bone(rv, 'j_head')
    strap = tube('Mask | temple strap %d' % s, [to_bo3(s * 5.7, face_y(s * 5.7, 72.0), 72.0), to_bo3(s * 6.3, -6.0, 72.4), to_bo3(s * 6.0, -2.5, 72.8)], [0.5, 0.5, 0.45], M['worn black leather'], head, segments=10, squash=0.5)
    fixed_bone(strap, 'j_head')
for ob in head.objects:
    if ob.name.startswith('Mask |'):
        ob['state1_only'] = True   # state two swaps in the CRACKED mask (10_state2_mask.py, tagged state2_only); the export drops the other state's faces

# ---------------------------------------------------------------- THE HOOD
# rows front -> back: (cx, cz, ry, rz, lean) - rings perpendicular to X; lean tilts the ring so its brow leads
rows = [(9.2, 71.6, 6.9, 10.6, 2.6), (7.6, 72.2, 8.1, 11.6, 1.6), (5.0, 72.9, 9.0, 12.4, 0.6), (1.6, 73.5, 9.4, 12.7, 0.0),
        (-2.2, 73.7, 9.1, 12.4, 0.0), (-5.6, 73.2, 8.2, 11.3, 0.0), (-8.2, 72.2, 6.5, 9.0, 0.0), (-10.0, 70.6, 4.4, 6.0, 0.0),
        (-11.4, 68.6, 2.6, 3.4, 0.0), (-12.2, 67.0, 1.0, 1.2, 0.0)]
Nh = 112
verts = []; faces = []
n_rows = len(rows)
for j, (cx, cz, ry, rz, lean) in enumerate(rows):
    for i in range(Nh):
        a = i * math.tau / Nh                     # a=0 is the top of the ring
        c, s_ = math.cos(a), math.sin(a)
        drape = math.sin(math.pi * min(1.0, j / (n_rows - 2)))
        fold = (0.32 * math.sin(9 * a + 0.3 * j) + 0.14 * math.sin(17 * a - 0.2 * j)) * drape
        down = max(0.0, -c)                         # 1 at the bottom of the ring
        # the sides and back fall past the jaw onto the mantle; the opening's chin tucks back under the mask
        rz_eff = rz * (1.0 + 0.45 * down * (0.4 + 0.6 * drape))
        ry_eff = ry * (1.0 + 0.28 * down * drape)
        x = cx + lean * c - (3.2 * down ** 2 if j == 0 else 1.4 * down ** 2 if j == 1 else 0.0)
        y = (ry_eff + fold) * s_
        z = cz + (rz_eff + fold * 0.6) * c + 1.0 * max(0.0, c) ** 8 * drape
        verts.append((x, y, z))
for j in range(n_rows - 1):
    for i in range(Nh):
        faces.append((j * Nh + i, j * Nh + (i + 1) % Nh, (j + 1) * Nh + (i + 1) % Nh, (j + 1) * Nh + i))
faces.append(tuple((n_rows - 1) * Nh + i for i in range(Nh)))   # the peak is closed
hood = mesh('Hood | deep black hood', verts, faces, hoodmat, head)
displace_noise(hood, 0.26, 0.08, seed=31, mask=lambda p: 0.35 if p.x > 7.5 else 1.0)
sol = solidify(hood, 0.36); sol.material_offset = 1; hood.data.materials.append(lining)
subdivide(hood, 1).render_levels = 2
skin(hood, HEAD_BONES, sigma=5.5, k=3)
rim = [verts[i] for i in range(Nh)] + [verts[0]]
binding = tube('Hood | rolled rim binding', rim, [0.3] * len(rim), hoodmat, head, segments=10)
skin(binding, HEAD_BONES, sigma=5.5, k=3)
sm = tube('Hood | crown seam', [(8.6, 0, 82.0), (4.0, 0, 85.2), (-1.5, 0, 85.7), (-6.0, 0, 83.6), (-9.5, 0, 79.2), (-11.6, 0, 71.6)], [0.07] * 6, M['red stitch thread'], head, segments=6)
skin(sm, HEAD_BONES, sigma=5.5, k=3)
for s in (-1, 1):
    ds = tube('Hood | drawstring %d' % s, [(9.2, s * 3.6, 61.0), (9.6, s * 4.1, 57.5), (9.3, s * 3.9, 53.5), (8.9, s * 3.5, 50.0)], [0.13] * 4, M['red stitch thread'], head, segments=8)
    skin(ds, ['j_spine4', 'j_neck'], sigma=6)
    tip = tube('Hood | drawstring tip %d' % s, [(8.9, s * 3.5, 50.3), (8.8, s * 3.4, 49.2)], [0.22, 0.22], M['blackened steel'], head, segments=10, cap_start=True, cap_end=True)
    skin(tip, ['j_spine4'], override=lambda p: {'j_spine4': 1.0})

view_hero()
save('03_head')
print(json.dumps({'stage': '03_head', 'head_objects': len(head.objects), 'mask_face_x': round(to_bo3(0, face_y(0, 71.1), 71.1).x, 2)}))
