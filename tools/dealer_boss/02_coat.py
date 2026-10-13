"""02: the Dealer's body - a floor-length heavy coat OPEN at the front from the
belt down (lining and striding legs show), a standing collar, a draped shoulder
mantle, deep sleeves with turned cuffs, trousers, a belt, buckled boots.

Every piece is skinned the moment it exists, so the studio can scrub a Keeper
clip on the rig and the coat already swings with the legs.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
if globals().get('REBUILD_MATERIALS', False) or bpy.data.materials.get('DEALER / heavy black wool coat') is None:
    purge_materials()      # only when the library changed (then run 03..05 again): later steps reuse what it authors
M = library()
body = coll('01')
for ob in list(body.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
random.seed(7)

SPINE = ['j_mainroot', 'j_spinelower', 'j_spineupper', 'j_spine4', 'j_neck', 'j_neck2']
ROBE = [n for n in BONE_LIST if n.startswith('j_robe_')]
wool = M['heavy black wool coat']; lining = M['oxblood satin lining']; leather = M['worn black leather']

# ---------------------------------------------------------------- legs (trousers tucked into the boots)
for side in ('le', 'ri'):
    s = 1 if side == 'le' else -1
    hip, kn, an = bone_pos('j_hip_' + side), bone_pos('j_knee_' + side), bone_pos('j_ankle_' + side)
    pts = [hip + Vector((0, s * 0.3, 1.5)), hip.lerp(kn, 0.3), hip.lerp(kn, 0.7), kn, kn.lerp(an, 0.4), an + Vector((0, 0, 3.0))]
    leg = tube('Legs | trouser ' + side, pts, [(4.3, 4.0), (4.1, 3.8), (3.7, 3.5), (3.4, 3.3), (3.1, 3.0), (2.9, 2.8)], M['dark trouser cloth'], body, segments=20, noise_amt=0.12, seed=5 * s)
    subdivide(leg, 1)
    skin(leg, ['j_hip_' + side, 'j_knee_' + side, 'j_ankle_' + side], chain_blend=True)

# ---------------------------------------------------------------- the coat body
# rings bottom -> top: (cx, cy, cz, rx front-back, ry side-side)
rings = [(-1.9, 0, 2.6, 15.4, 16.0), (-1.9, 0, 8, 14.2, 14.8), (-1.8, 0, 15, 12.6, 13.2), (-1.7, 0, 22, 11.0, 11.6),
         (-1.5, 0, 29, 9.6, 10.2), (-1.4, 0, 35, 8.7, 9.4), (-1.3, 0, 40, 8.0, 8.9), (-1.2, 0, 44.5, 7.4, 8.3),
         (-1.1, 0, 49, 7.5, 8.9), (-1.0, 0, 53.5, 7.9, 9.7), (-1.0, 0, 57, 8.1, 10.2), (-1.1, 0, 60, 7.6, 9.3),
         (-0.7, 0, 62.5, 6.0, 6.4), (-0.5, 0, 65.6, 5.3, 5.5)]
def torso_profile(a, j):
    return 1.0 + 0.035 * math.cos(a) * (1 if j > 6 else -0.5) - 0.04 * math.cos(2 * a) * (j / 13.0)
coat = loft('Coat | heavy wool body', rings, wool, body, segments=80, folds=0.95, fold_scale=1.0, cap_top=True, profile=torso_profile, seed=3)
# THE OPENING: the front parts from the belt down, wider toward the hem (legs and lining show)
def keep_coat(c):
    if c.z > 43.5:
        return True
    half = math.radians(2 + 22 * (43.5 - c.z) / 41.0)
    return abs(math.atan2(c.y, c.x + 1.7)) > half
cut_faces(coat, keep_coat)
# the hem is torn and drags
for v in coat.data.vertices:
    if v.co.z < 3.0:
        a = math.atan2(v.co.y, v.co.x + 1.9)
        v.co.z += 1.9 * max(0.0, math.sin(5 * a + 0.7)) ** 2 + 0.6 * max(0.0, math.sin(13 * a)) - 0.2
displace_noise(coat, 0.55, 0.05, seed=4, mask=lambda p: 1.0 if p.z < 56 else 0.2)
displace_noise(coat, 0.18, 0.22, seed=12, mask=lambda p: 1.0 if p.z < 60 else 0.3)
sol = solidify(coat, 0.45); sol.material_offset = 1; coat.data.materials.append(lining)
subdivide(coat, 1).render_levels = 2
skin(coat, SPINE + ROBE, sigma=5.5, k=3)

# the left front panel overlaps the opening's top (double-breasted) and swings open at its corner
panel_rings = [(cx + 0.5, cy, cz, rx + 0.55, ry + 0.45) for (cx, cy, cz, rx, ry) in rings[2:10]]
panel = loft('Coat | left front panel', panel_rings, wool, body, segments=80, folds=0.6, seed=9)
def keep_panel(c):
    ang = math.degrees(math.atan2(c.y, c.x + 1.6))
    lo = -4 - 16 * max(0.0, (44 - c.z) / 30.0)   # its free edge swings across the opening toward the hem
    return lo < ang < 34
cut_faces(panel, keep_panel)
for v in panel.data.vertices:
    ang = math.atan2(v.co.y, v.co.x + 1.6)
    k = max(0.0, (0.15 - ang)) * max(0.0, (30 - v.co.z) / 30.0)   # the corner lifts away from the body
    v.co.x += k * 2.4; v.co.y -= k * 0.6
displace_noise(panel, 0.3, 0.07, seed=19)
sol = solidify(panel, 0.4); sol.material_offset = 1; panel.data.materials.append(lining)
subdivide(panel, 1)
skin(panel, SPINE + ROBE, sigma=5.5, k=3)

# the placket: a stitched edge strip with flat brass toggles, on the panel's leading edge
plk = []
for z in (22, 28, 34, 40, 46, 52, 57):
    j = min(range(len(rings)), key=lambda i: abs(rings[i][2] - z))
    cx, cy, cz, rx, ry = rings[j]
    a = math.radians(8 + 2 * max(0.0, (44 - z) / 10.0))
    plk.append((cx + (rx + 1.05) * math.cos(a), cy + (ry + 1.05) * math.sin(a), z))
seam = tube('Coat | front placket seam', plk, [(0.35, 1.0)] * len(plk), wool, body, segments=10)
skin(seam, SPINE + ROBE, sigma=6, k=3)
for i, (x, y, z) in enumerate(plk[1:-1]):
    t = box('Coat | brass toggle %d' % i, (x + 0.25, y + 0.1, z), (0.28, 1.5, 0.42), M['aged brass fittings'], body, bevel=0.1)
    skin(t, SPINE + ROBE, sigma=6, k=3)
    lp = tube('Coat | toggle loop %d' % i, [(x, y - 1.3, z), (x + 0.35, y - 2.1, z + 0.1), (x, y - 2.9, z)], [0.14, 0.14, 0.14], M['red stitch thread'], body, segments=8)
    skin(lp, SPINE + ROBE, sigma=6, k=3)

# ---------------------------------------------------------------- the mantle (a draped shoulder cape, longer at the back)
# a shoulder cape hangs from the shoulder line: its hem is barely wider than the shoulders and sleeves
cowl_rings = [(-1.4, 0, 51.5, 9.9, 13.4), (-1.4, 0, 54.0, 9.7, 13.1), (-1.3, 0, 56.5, 9.4, 12.6), (-1.2, 0, 58.8, 8.9, 11.6),
              (-0.9, 0, 61.2, 7.6, 8.6), (-0.6, 0, 63.6, 6.3, 6.6), (-0.4, 0, 66.4, 5.9, 6.0)]
def cowl_profile(a, j):
    # flatter across the chest and back, fuller over the shoulder points
    return 1.0 - 0.07 * math.cos(2 * a) * (1 - j / 7.0) + 0.03 * abs(math.sin(a)) ** 3 * (1 - j / 7.0)
cowl = loft('Coat | shoulder mantle', cowl_rings, wool, body, segments=96, folds=1.25, fold_scale=1.35, profile=cowl_profile, seed=5)
for v in cowl.data.vertices:
    a = math.atan2(v.co.y, v.co.x + 1.4)
    low = max(0.0, (59.0 - v.co.z) / 7.5)          # 0 at the shoulder line, 1 at the hem
    v.co.z -= 5.0 * low * (1 - math.cos(a)) / 2    # the back hangs longer than the front
    v.co.z += low * (0.9 * max(0.0, math.sin(7 * a + 1.3)) ** 2 + 0.4 * max(0.0, math.sin(19 * a)))   # torn hem
    v.co.z -= 2.2 * low * abs(math.sin(a)) ** 3    # drapes down over the shoulder points
    v.co.z -= 1.2 * low * max(0.0, math.cos(a)) ** 2   # and a little longer at the front centre
displace_noise(cowl, 0.3, 0.09, seed=6)
sol = solidify(cowl, 0.5); sol.material_offset = 1; cowl.data.materials.append(lining)
subdivide(cowl, 1).render_levels = 2
# the cape hangs from the shoulder LINE (clavicles + upper spine), never from the arm bones:
# weighted to the shoulders it rose with the arms and read as puffed sleeves (pose check 2026-09-30)
skin(cowl, ['j_spine4', 'j_spineupper', 'j_clavicle_le', 'j_clavicle_ri', 'j_neck'], sigma=7.0, k=3)
for s in (-1, 1):
    pts = [(-0.6, s * 2.2, 66.2), (0.3, s * 5.6, 62.0), (1.3, s * 9.4, 57.5), (1.9, s * 13.0, 52.5)]
    sm = tube('Coat | mantle seam %d' % s, pts, [0.14] * 4, M['red stitch thread'], body, segments=8)
    skin(sm, ['j_spine4', 'j_clavicle_le', 'j_clavicle_ri'], sigma=6)

# ---------------------------------------------------------------- sleeves (deep, the hands emerge from shadow)
for side in ('le', 'ri'):
    s = 1 if side == 'le' else -1
    sh, el, wr = bone_pos('j_shoulder_' + side), bone_pos('j_elbow_' + side), bone_pos('j_wrist_' + side)
    top = Vector((-1.4, s * 5.0, 62.0))
    pts = [top, sh + Vector((0, s * 0.6, 0.4)), sh.lerp(el, 0.35) + Vector((-0.4, s * 0.5, 0)), sh.lerp(el, 0.7), el + Vector((-0.3, 0, 0)),
           el.lerp(wr, 0.35), el.lerp(wr, 0.7), wr + Vector((0, 0, 0.8)), wr + Vector((0.5, s * 0.2, -1.4)), wr + Vector((0.9, s * 0.3, -2.6))]
    radii = [(3.0, 3.0), (4.9, 4.6), (4.7, 4.4), (4.3, 4.1), (4.0, 3.9), (3.9, 3.8), (4.0, 4.0), (4.3, 4.2), (4.7, 4.6), (5.0, 4.9)]
    sl = tube('Coat | sleeve ' + side, pts, radii, wool, body, segments=28, noise_amt=0.3, seed=3 * s)
    displace_noise(sl, 0.22, 0.2, seed=8 + s)
    sol = solidify(sl, 0.35); sol.material_offset = 1; sl.data.materials.append(lining)   # the lining shows inside the open cuff
    subdivide(sl, 1)
    skin(sl, ['j_shoulder_' + side, 'j_elbow_' + side, 'j_wrist_' + side], chain_blend=True)
    # the turned-back cuff: a wool band folded up over the sleeve end; the lining shows only on its inside
    c0, c1 = wr + Vector((0.55, s * 0.2, -0.9)), wr + Vector((0.9, s * 0.3, -2.9))
    cuff = tube('Coat | turned cuff ' + side, [c0, c0.lerp(c1, 0.5), c1], [(4.75, 4.6), (4.95, 4.8), (5.1, 4.95)], wool, body, segments=28, noise_amt=0.12)
    sol = solidify(cuff, 0.32); sol.material_offset = 1; cuff.data.materials.append(lining)
    stitch = tube('Coat | cuff stitch ' + side, [wr + Vector((0.6 + 4.95 * math.cos(a), s * 0.2 + 4.8 * math.sin(a), -1.5)) for a in [i * math.tau / 32 for i in range(33)]], [0.08] * 33, M['red stitch thread'], body, segments=6)
    skin(stitch, ['j_wrist_' + side], override=lambda p, b='j_wrist_' + side: {b: 1.0})
    skin(cuff, ['j_wrist_' + side], override=lambda p, b='j_wrist_' + side: {b: 1.0})
    st = el.lerp(wr, 0.5)
    strap = tube('Coat | forearm strap ' + side, [st + Vector((0, 0, 0.55)), st - Vector((0, 0, 0.55))], [(4.35, 4.25), (4.3, 4.2)], leather, body, segments=28)
    skin(strap, ['j_elbow_' + side, 'j_wrist_' + side], chain_blend=True)
    bk = box('Coat | strap buckle ' + side, st + Vector((4.1, s * 1.2, 0)), (0.3, 0.9, 0.7), M['blackened steel'], body, bevel=0.08)
    skin(bk, ['j_elbow_' + side, 'j_wrist_' + side], chain_blend=True)

# ---------------------------------------------------------------- the belt
belt_pts = []
for i in range(40):
    a = i * math.tau / 40
    belt_pts.append((-1.2 + 8.3 * math.cos(a), 9.1 * math.sin(a), 44.4 - 0.5 * math.cos(a)))
belt_pts.append(belt_pts[0])
belt = tube('Belt | wide leather belt', belt_pts, [(0.4, 1.7)] * 41, leather, body, segments=12)
skin(belt, ['j_mainroot', 'j_spinelower'], sigma=6)
buckle = box('Belt | heavy buckle', (7.5, 0.6, 44.4), (0.45, 2.1, 1.9), M['blackened steel'], body, bevel=0.14)
skin(buckle, ['j_mainroot', 'j_spinelower'], sigma=6)
tongue = box('Belt | buckle tongue', (7.95, 0.6, 44.4), (0.15, 1.3, 0.2), M['aged brass fittings'], body)
skin(tongue, ['j_mainroot'], override=lambda p: {'j_mainroot': 1.0})
end = tube('Belt | hanging strap end', [(7.2, -2.8, 44.2), (7.8, -3.6, 41.0), (7.6, -3.9, 37.5)], [(0.35, 1.3), (0.3, 1.25), (0.3, 1.1)], leather, body, segments=10)
skin(end, ['j_mainroot'], override=lambda p: {'j_mainroot': 1.0})

# ---------------------------------------------------------------- boots
for side in ('le', 'ri'):
    s = 1 if side == 'le' else -1
    kn, an, ba = bone_pos('j_knee_' + side), bone_pos('j_ankle_' + side), bone_pos('j_ball_' + side)
    shaft = tube('Boot | shaft ' + side, [kn + Vector((0, 0, -3)), kn.lerp(an, 0.5), an + Vector((0, 0, 1.0)), an + Vector((0.3, 0, -1.2))],
                 [(3.5, 3.3), (3.3, 3.2), (3.4, 3.2), (3.7, 3.3)], M['worn black boot leather'], body, segments=22, noise_amt=0.15)
    subdivide(shaft, 1)
    skin(shaft, ['j_knee_' + side, 'j_ankle_' + side], chain_blend=True)
    foot_pts = [an + Vector((-3.4, 0, -2.0)), an + Vector((-1.0, 0, -2.6)), ba + Vector((-2.0, 0, 0.9)), ba + Vector((1.0, 0, 0.5)), ba + Vector((3.8, 0, 0.3))]
    foot = tube('Boot | foot ' + side, foot_pts, [(2.5, 2.9), (2.9, 3.1), (2.5, 3.1), (2.1, 2.8), (0.9, 2.0)], M['worn black boot leather'], body, segments=20, cap_start=True, cap_end=True)
    subdivide(foot, 1)
    skin(foot, ['j_ankle_' + side, 'j_ball_' + side], chain_blend=True)
    sole = box('Boot | sole ' + side, (ba.x - 1.5, ba.y, 0.55), (6.4, 3.1, 0.55), M['black rubber sole'], body, bevel=0.2)
    skin(sole, ['j_ankle_' + side, 'j_ball_' + side], sigma=4)
    for i, z in enumerate((7.5, 11.5)):
        bk = box('Boot | buckle strap %s %d' % (side, i), an + Vector((3.1, 0, z - 4.5)), (0.3, 1.1, 0.5), M['blackened steel'], body, bevel=0.08)
        skin(bk, ['j_knee_' + side, 'j_ankle_' + side], chain_blend=True)
        band = tube('Boot | strap band %s %d' % (side, i), [an + Vector((0.1, 0, z - 4.0)), an + Vector((0.1, 0, z - 5.0))], [(3.55, 3.35), (3.55, 3.35)], leather, body, segments=22)
        skin(band, ['j_knee_' + side, 'j_ankle_' + side], chain_blend=True)

view_hero()
save('02_coat')
print(json.dumps({'stage': '02_coat', 'body_objects': len(body.objects), 'skinned': sum(1 for o in body.objects if o.get('skinned'))}))
