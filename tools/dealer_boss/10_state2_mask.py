"""10: STATE TWO - THE CRACKED MASK (user 2026-10-02: the dealer is his own entity, nothing of
Richtofen; "at half health his mask will be cracked and one eye glow will be missing and his
smile more menacing").

The mask does not come off: the same graphite shell is rebuilt with a CHIP torn out of its
right temple and another out of the grin's right corner (the black void shows through), black
fissures running from the chips across the brow, cheek and nose, a few red leaks where the
neon wiring is cut, the RIGHT X eye DEAD (dark red glass tubes, no glow - the stroke that was
already failing in state one finally dies), the LEFT eye burning harder, and THE GRIN torn
wider: both corners pulled up the cheeks, a sagging lower seam, a black gape between them
and seventeen long uneven fangs. Every object here is tagged state2_only; the state-one
mask stays tagged state1_only; the void is in BOTH states. The exporter writes the two
variants from one head bake (export_native.py), the fight swaps the body at half health
(_tod_dealer_finale.gsc mask_crack).

Also deletes the retired Richtofen state-two collection and its donor materials from the
master if an older master still carries them.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
M = library()
# library() reuses an existing master's materials untouched: make sure the two state-two finishes exist
material('red neon wire dead', (0.075, 0.006, 0.008), 0, 0.55, atlas='head')
material('mask crack black', (0.0035, 0.003, 0.004), 0, 0.72, atlas='head')
M = MATS
head = coll('02')

# ---------------------------------------------------------------- retire the Richtofen state (older masters)
for c in list(bpy.data.collections):
    if c.name.startswith('DEALER | 05 STATE2'):
        for ob in list(c.objects):
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
        bpy.data.collections.remove(c)
for m in list(bpy.data.materials):
    if m.name.startswith('DONOR / ') and ('richtofen' in m.name or m.name.endswith('mtl_c_gen_insidemouth_teeth') or m.name.endswith('mtl_c_gen_eye_blue')):
        bpy.data.materials.remove(m)
for im in list(bpy.data.images):
    if 'richtofen' in im.name.lower():
        bpy.data.images.remove(im)
# the void is in both states now (it used to hide behind Richtofen's face); an older Mask2 set is rebuilt
for ob in list(head.objects):
    if ob.name.startswith('Head | black void') and 'state1_only' in ob:
        del ob['state1_only']
    if ob.get('state2_only'):
        me = ob.data; bpy.data.objects.remove(ob, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)

# ---------------------------------------------------------------- the same mask space as 03_head.py
MASK_Z = 71.4
MASK_X0 = -2.4
MASK_SCALE = 1.04
def face_y(x, z):
    return -8.05 - 2.05 * math.sqrt(max(0.04, 1 - (x / 6.0) ** 2 - ((z - 71.1) / 8.25) ** 2))
def to_bo3(xs, ys, zs):
    return Vector((MASK_X0 - ys * MASK_SCALE, -xs * MASK_SCALE, MASK_Z + (zs - 71.1) * MASK_SCALE))

def inside(poly, x, z):
    """point in polygon (shop xz)"""
    n = len(poly); hit = False
    for i in range(n):
        x1, z1 = poly[i]; x2, z2 = poly[(i + 1) % n]
        if (z1 > z) != (z2 > z):
            xi = x1 + (z - z1) * (x2 - x1) / (z2 - z1)
            if x < xi:
                hit = not hit
    return hit

# THE CHIPS (shop xz polygons): the right temple above the dead eye, and the grin's torn right corner
# (the shell's half-width at the eye line is only ~4.4: the chips sit INSIDE it and eat the dead eye's outer arms)
CHIP_TEMPLE = [(3.0, 76.6), (3.7, 77.2), (4.4, 76.4), (4.8, 75.3), (4.6, 74.2), (4.2, 73.3), (3.5, 73.6), (3.7, 74.4), (3.1, 75.0), (3.4, 75.9)]
CHIP_GRIN = [(3.6, 68.9), (4.3, 69.4), (4.75, 70.6), (4.3, 71.4), (3.85, 70.9), (3.5, 70.1)]
CHIPS = (CHIP_TEMPLE, CHIP_GRIN)
def chipped(x, z):
    return any(inside(c, x, z) for c in CHIPS)

# ---------------------------------------------------------------- the cracked shell
verts = []; faces = []; N = 96; xz = []
for j in range(25):
    r = 0.015 + 0.985 * j / 24
    for i in range(N):
        a = i * math.tau / N
        zs = 71.1 + 8.15 * r * math.cos(a)
        xs = 5.65 * (0.80 + 0.20 * max(0, math.cos(a))) * r * math.sin(a)
        verts.append(to_bo3(xs, face_y(xs, zs), zs)); xz.append((xs, zs))
def quad_ok(q):
    cx = sum(xz[k][0] for k in q) / 4; cz = sum(xz[k][1] for k in q) / 4
    return not chipped(cx, cz)
for j in range(24):
    for i in range(N):
        q = (j * N + i, j * N + (i + 1) % N, (j + 1) * N + (i + 1) % N, (j + 1) * N + i)
        if quad_ok(q):
            faces.append(q)
faces.append(tuple(range(N - 1, -1, -1)))
shell = mesh('Mask2 | cracked graphite shell', verts, faces, M['graphite molded mask'], head)
solidify(shell, 0.26, offset=1)
displace_noise(shell, 0.05, 0.9, seed=21)
fixed_bone(shell, 'j_head')
dropped = 24 * N - (len(faces) - 1)

led = M['red neon wire']; weak = M['red neon wire weak']; dead = M['red neon wire dead']; crackmat = M['mask crack black']
maskmat = M['graphite molded mask']; void = M['mask void black']
def wire(name, xz_, r=0.11, mat=led, depth=None):
    if depth is None:
        depth = 0.60 if any(t in name for t in ('grin', 'tooth', 'fang', 'corner', 'jaw', 'stitch')) else 0.28
    pts = [to_bo3(x, face_y(x, z) - depth, z) for x, z in xz_]
    ob = tube('Mask2 | ' + name, pts, [r] * len(pts), mat, head, segments=10)
    fixed_bone(ob, 'j_head'); return ob
def plate(name, xz_, depth=0.35, thick=0.22, mat=None):
    pts = [to_bo3(x, face_y(x, z) - depth, z) for x, z in xz_]
    ob = mesh('Mask2 | ' + name, pts, [tuple(range(len(pts)))], mat or maskmat, head, smooth=False, bevel=0.06)
    solidify(ob, thick); fixed_bone(ob, 'j_head'); return ob

# ---------------------------------------------------------------- the eyes: the LEFT burns harder, the RIGHT is dead
wire('slanted X long -1', [(-4.0, 76.0), (-2.65, 74.75), (-1.2, 73.6)], 0.17)
wire('slanted X cut -1', [(-4.0, 73.9), (-2.65, 74.75), (-1.5, 75.45)], 0.13)
wire('dead X long 1', [(2.95, 75.05), (2.65, 74.75), (1.2, 73.6)], 0.15, dead)
wire('dead X cut 1', [(3.3, 74.35), (2.65, 74.75), (1.5, 75.45)], 0.11, dead)
# the torn wire ends at the temple break still carry a dying glow
wire('torn wire end 1', [(2.95, 75.05), (3.3, 75.4)], 0.07, weak)
wire('torn wire end 2', [(3.3, 74.35), (3.6, 74.1)], 0.06, weak)

# ---------------------------------------------------------------- the plates: the right brow and cheek broken short
plate('overhanging brow -1', [(-0.85, 75.8), (-4.55, 77.6), (-4.35, 76.5), (-1.05, 75.0)], 0.47, 0.3)
plate('overhanging brow 1 broken', [(0.85, 75.8), (3.1, 76.9), (2.75, 76.45), (3.0, 75.95), (1.05, 75.0)], 0.47, 0.3)
plate('hollow cheek -1', [(-1.45, 70.5), (-4.5, 72.8), (-4.8, 70.0), (-3.3, 67.5), (-2.1, 68.3)], 0.33, 0.25)
plate('hollow cheek 1 broken', [(1.45, 70.5), (3.7, 72.3), (3.9, 71.5), (3.6, 70.6), (3.45, 69.6), (3.3, 67.5), (2.1, 68.3)], 0.33, 0.25)
plate('split nose bridge', [(-0.65, 75.5), (0, 77.1), (0.6, 75.5), (0.95, 71.1), (0, 70.1), (-0.85, 71.25)], 0.5, 0.35)

# ---------------------------------------------------------------- the fissures (black, barely proud) + the red leaks beside the worst
CRACKS = {
    'fissure brow': [(3.05, 76.3), (2.6, 75.8), (2.2, 76.1), (1.4, 76.0), (0.9, 76.8), (0.2, 77.5), (-0.5, 77.95)],
    'fissure cheek': [(4.0, 73.2), (3.8, 72.4), (4.1, 71.6), (3.75, 70.95)],
    'fissure cheek branch': [(3.8, 72.4), (3.1, 72.0), (2.6, 71.2), (2.3, 70.3), (2.45, 69.4)],
    'fissure nose branch': [(1.4, 76.0), (1.1, 74.9), (1.5, 74.1), (1.2, 73.3)],
    'fissure jaw': [(3.7, 68.85), (3.4, 68.0), (3.6, 67.1), (3.3, 66.3)],
    'fissure left brow': [(-3.2, 77.2), (-2.4, 76.4), (-2.6, 75.6), (-1.9, 75.0), (-2.1, 74.2)],
    'fissure left temple': [(-5.3, 73.4), (-4.7, 73.9), (-4.9, 74.6)],
}
for name, pts in CRACKS.items():
    wire(name, pts, 0.055 if ('branch' in name or 'left' in name) else 0.07, crackmat, depth=0.06)
wire('leak brow', [(3.0, 76.25), (2.6, 75.75), (2.25, 76.05)], 0.03, weak, depth=0.1)
wire('leak cheek', [(3.95, 73.15), (3.82, 72.45), (4.05, 71.7)], 0.03, weak, depth=0.1)
wire('left scar', [(-4.35, 72.6), (-4.0, 71.7), (-4.3, 71.15)], 0.052, weak)

# ---------------------------------------------------------------- THE GRIN, torn wider
UPPER = [(-5.1, 71.6), (-4.6, 70.0), (-3.7, 68.5), (-2.5, 67.9), (-1.3, 66.9), (-0.2, 67.2), (1.0, 66.7), (2.3, 67.6), (3.3, 68.2), (3.9, 69.0)]
LOWER = [(-4.9, 71.3), (-4.3, 69.3), (-3.5, 67.0), (-2.4, 65.9), (-1.2, 65.3), (0.0, 65.5), (1.2, 65.2), (2.3, 65.9), (3.2, 66.9), (3.8, 68.2)]
def interp(poly, x):
    for (x1, z1), (x2, z2) in zip(poly, poly[1:]):
        if min(x1, x2) <= x <= max(x1, x2) and x1 != x2:
            return z1 + (z2 - z1) * (x - x1) / (x2 - x1)
    return poly[0][1] if x < poly[0][0] else poly[-1][1]
# the black gape between the two seams
gape = [to_bo3(x, face_y(x, z) - 0.42, z) for x, z in UPPER] + [to_bo3(x, face_y(x, z) - 0.42, z) for x, z in reversed(LOWER)]
g = mesh('Mask2 | grin black gape', gape, [tuple(range(len(gape)))], void, head, smooth=False)
fixed_bone(g, 'j_head')
wire('grin seam torn', UPPER, 0.16)
wire('lower jaw seam', LOWER, 0.11)
# seventeen fangs: thirteen hang from the upper seam, four rise from the lower
xs_up = [-4.45, -3.9, -3.3, -2.7, -2.1, -1.5, -0.9, -0.3, 0.35, 1.0, 1.65, 2.35, 3.05]
hs_up = [1.7, 2.6, 1.9, 3.1, 2.2, 3.4, 2.0, 2.9, 2.4, 3.3, 2.1, 2.8, 2.3]
for i, (x, h) in enumerate(zip(xs_up, hs_up)):
    z = interp(UPPER, x)
    wire('fang %d' % i, [(x - 0.18, z + 0.6), (x + 0.03, z - h), (x + 0.32, z + 0.3)], 0.065 if i % 2 else 0.085)
for i, (x, h) in enumerate([(-3.1, 1.6), (-1.6, 2.2), (0.55, 1.9), (2.4, 1.5)]):
    z = interp(LOWER, x)
    wire('lower fang %d' % i, [(x - 0.2, z - 0.55), (x + 0.02, z + h), (x + 0.3, z - 0.3)], 0.07)
# the stitches across the seam: whole on the left, torn and dangling on the right
for i, x in enumerate([-4.75, -4.1, -3.35, -2.7, -2.0]):
    z = interp(UPPER, x)
    wire('grin stitch %d' % i, [(x - 0.12, z + 0.5), (x + 0.12, z - 0.5)], 0.05)
wire('grin stitch torn 0', [(2.7, interp(UPPER, 2.7) + 0.5), (2.55, interp(UPPER, 2.7) - 0.9), (2.3, interp(UPPER, 2.7) - 1.6)], 0.045, weak)
wire('grin stitch torn 1', [(3.45, interp(UPPER, 3.45) + 0.4), (3.3, interp(UPPER, 3.45) - 0.7)], 0.045, weak)

# ---------------------------------------------------------------- rivets and straps: the right strap snapped and hanging
for s in (-1, 1):
    rv = sphere('Mask2 | temple rivet %d' % s, to_bo3(s * 5.6, face_y(s * 5.6, 72.0) - 0.1, 72.0), 0.42, M['blackened steel'], head, rings=8, segments=12)
    fixed_bone(rv, 'j_head')
strap = tube('Mask2 | temple strap -1', [to_bo3(-5.7, face_y(-5.7, 72.0), 72.0), to_bo3(-6.3, -6.0, 72.4), to_bo3(-6.0, -2.5, 72.8)], [0.5, 0.5, 0.45], M['worn black leather'], head, segments=10, squash=0.5)
fixed_bone(strap, 'j_head')
strap = tube('Mask2 | temple strap 1 snapped', [to_bo3(5.7, face_y(5.7, 72.0), 72.0), to_bo3(6.25, -7.0, 71.3), to_bo3(6.1, -6.4, 69.6), to_bo3(5.8, -6.9, 68.2)], [0.5, 0.48, 0.42, 0.3], M['worn black leather'], head, segments=10, squash=0.5)
fixed_bone(strap, 'j_head')

for ob in head.objects:
    if ob.name.startswith('Mask2 |'):
        ob['state2_only'] = True
        ob['dealer_part'] = True
n2 = sum(1 for ob in head.objects if ob.get('state2_only'))
n1 = sum(1 for ob in head.objects if ob.get('state1_only'))
review_state(int(globals().get('SHOW_STATE', 1)))
view_hero()
save('10_state2_mask')
print(json.dumps({'stage': '10_state2_mask', 'state2_objects': n2, 'state1_objects': n1, 'shell_quads_chipped': dropped,
                  'richtofen_collections': [c.name for c in bpy.data.collections if 'STATE2' in c.name],
                  'donor_materials': sorted(m.name for m in bpy.data.materials if m.name.startswith('DONOR / '))}))
