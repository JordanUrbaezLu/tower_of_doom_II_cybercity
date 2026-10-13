"""04: the Dealer's hands - black leather gloves built along the Keeper's finger
bones, knuckle plates, and LONG SHARP RED NAILS curving past every fingertip.

Each finger is a tube that follows its three bones exactly, so the glove bends
where the skeleton bends; each nail rides its tip bone alone.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
M = library()
hands = coll('03')
for ob in list(hands.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
glove = M['glove black leather']; nail_mat = M['lacquered red nails']

FINGERS = {  # chain of bones per finger (base -> tip) and the nail length past the tip
    'index': (['j_index_%s_1', 'j_index_%s_2', 'j_index_%s_3'], 3.4),
    'mid':   (['j_mid_%s_1', 'j_mid_%s_2', 'j_mid_%s_3'], 3.7),
    'ring':  (['j_ringbase_%s', 'j_ring_%s_1', 'j_ring_%s_2', 'j_ring_%s_3'], 3.2),
    'pinky': (['j_pinkybase_%s', 'j_pinky_%s_1', 'j_pinky_%s_2', 'j_pinky_%s_3'], 2.6),
    'thumb': (['j_thumb_%s_1', 'j_thumb_%s_2', 'j_thumb_%s_3'], 2.9),
}
RADII = {'index': 0.55, 'mid': 0.57, 'ring': 0.52, 'pinky': 0.45, 'thumb': 0.64}

for side in ('le', 'ri'):
    s = 1 if side == 'le' else -1
    wr = bone_pos('j_wrist_' + side)
    # the palm: a flattened loft from the wrist down to the knuckle line
    k_index, k_mid, k_ring, k_pinky = (bone_pos(n % side) for n in ('j_index_%s_1', 'j_mid_%s_1', 'j_ring_%s_1', 'j_pinky_%s_1'))
    knuckle_c = (k_index + k_mid + k_ring + k_pinky) / 4
    palm_axis = (knuckle_c - wr)
    width_axis = (k_pinky - k_index).normalized()
    thick_axis = palm_axis.normalized().cross(width_axis).normalized()
    pts = [wr - palm_axis.normalized() * 0.4, wr + palm_axis * 0.35, wr + palm_axis * 0.7, knuckle_c + palm_axis.normalized() * 0.35]
    # tube() frames a near-vertical path with X as its first axis: radii are (thickness along X, width along Y)
    palm = tube('Glove | palm ' + side, pts, [(1.15, 2.0), (1.25, 2.35), (1.15, 2.6), (1.0, 2.4)], glove, hands, segments=22, cap_start=True, cap_end=True, noise_amt=0.06, seed=s)
    subdivide(palm, 1)
    skin(palm, ['j_wrist_' + side, 'j_index_%s_1' % side, 'j_mid_%s_1' % side, 'j_ringbase_' + side, 'j_pinkybase_' + side, 'j_thumb_%s_1' % side], sigma=2.2, k=3)
    # glove cuff flaring under the sleeve, with a red stitched hem
    cuff = tube('Glove | cuff ' + side, [wr + Vector((0, 0, 2.6)), wr + Vector((0, 0, 1.2)), wr + Vector((0, 0, -0.3))], [(2.5, 2.1), (2.35, 1.9), (2.2, 1.6)], glove, hands, segments=20)
    fixed_bone(cuff, 'j_wrist_' + side)
    hem = tube('Glove | cuff stitch ' + side, [wr + Vector((2.2 * math.cos(a), 1.85 * math.sin(a), 2.0)) for a in [i * math.tau / 24 for i in range(25)]], [0.07] * 25, M['red stitch thread'], hands, segments=6)
    fixed_bone(hem, 'j_wrist_' + side)
    # knuckle plates: four small leather-covered ridges
    for n in ('j_index_%s_1', 'j_mid_%s_1', 'j_ring_%s_1', 'j_pinky_%s_1'):
        kp = bone_pos(n % side)
        kn = sphere('Glove | knuckle ' + (n % side), kp + thick_axis * 0.45, (0.55, 0.5, 0.42), glove, hands, rings=8, segments=12)
        fixed_bone(kn, n % side)
    for finger, (chain, nail_len) in FINGERS.items():
        names = [c % side for c in chain]
        P = [bone_pos(n) for n in names]
        # the tip past the last bone, along the last segment
        d = (P[-1] - P[-2]).normalized()
        tip = P[-1] + d * (1.15 if finger != 'thumb' else 1.0)
        pts = [P[0] - (P[1] - P[0]).normalized() * 0.25] + P + [tip]
        r0 = RADII[finger]
        radii = [r0 * 1.15, r0 * 1.1] + [r0 * (1.0 - 0.12 * i) for i in range(len(P) - 1)] + [r0 * 0.62]
        f = tube('Glove | %s finger %s' % (finger, side), pts, radii, glove, hands, segments=14, cap_end=True, noise_amt=0.03, seed=11)
        subdivide(f, 1)
        skin(f, names, chain_blend=True)
        # finger seam stitching along the back of the finger
        seam = tube('Glove | %s seam %s' % (finger, side), [p + thick_axis * (r0 * 0.9) for p in pts], [0.05] * len(pts), M['red stitch thread'], hands, segments=5)
        skin(seam, names, chain_blend=True)
        # THE NAIL: a long, tapered, slightly curved claw lacquered blood-red
        curve_dir = (-thick_axis) * 0.22       # claws hook toward the palm
        nail_pts = []
        n_seg = 7
        for i in range(n_seg + 1):
            t = i / n_seg
            nail_pts.append(tip - d * 0.55 + d * (nail_len * t) + curve_dir * (nail_len * t * t))
        nail_r = [r0 * 0.5, r0 * 0.48, r0 * 0.42, r0 * 0.34, r0 * 0.25, r0 * 0.16, r0 * 0.08, 0.02]
        nail = tube('Nail | %s %s' % (finger, side), nail_pts, [(r * 0.55, r) for r in nail_r], nail_mat, hands, segments=12, cap_start=True, cap_end=True)
        subdivide(nail, 1)
        fixed_bone(nail, names[-1])
        nail['nail'] = True

view_hero()
save('04_hands')
print(json.dumps({'stage': '04_hands', 'hand_objects': len(hands.objects), 'nails': sum(1 for o in hands.objects if o.get('nail'))}))
