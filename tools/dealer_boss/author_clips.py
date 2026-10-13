"""author_clips.py - THE DEALER'S OWN CLIPS: the Keeper clips re-authored to levitate and to HOLD THE SCYTHE.

User 2026-09-30, watching the reel: "you have to understand the concept of holding a scythe ... a lot of
these positions the scythe doesn't seem smooth and flails around"; "one thing I would like him to do is
levitate. That's his walking animation. And then when he breaks his mask at 50% he will walk around."

The Keeper clips were animated for empty claws, so a scythe pinned to one wrist whips with every twist
of that wrist and the other hand never touches it. This tool bakes the hold INTO the clips, the way a
weapon animation is authored, so the game attaches the scythe as a plain rigid model on tag_weapon_right
and nothing has to aim it at runtime:

  1. THE POLE DIRECTION is a smooth function of the clip: OUTWARD, from a point behind the chest through
     the right hand (a swipe of the arm becomes a sweep of the blade; it never points into the body and
     never flips), or, when the hands are clasped (the glide, the idles), carried across the chest with
     the blade rising over the shoulder. Blended by the hands' distance, then low-passed over time (a
     Gaussian, wrapped on looping clips) so it never flails.
  2. THE RIGHT WRIST is turned (about the wrist joint, the arm untouched) so the weapon tag's -X runs
     along that pole and the blade plane stays upright (world up for a sweep, backward for the upright
     carry, blended).
  3. THE LEFT HAND is put ON the pole: its palm point slides to the nearest point of the shaft within
     the grip range, the hand is turned as the mirror image of the right hand's grip (hand frames built
     from the finger bones, so no rig-convention guesswork), and a two-bone IK bends the left arm to
     reach it, keeping the clip's own elbow plane. The parked tag_weapon_left rides to the palm.
  4. STATE ONE LEVITATES: every part but tag_origin / tag_sync / tag_aim rises FLOAT_LIFT inches; the
     root (and so the navmesh placement and the delta root motion) stays on the ground.

Runs in background Blender (mathutils + the PyCoD addon):
  "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe" -b --python tools/dealer_boss/author_clips.py
Writes xanim_export/tod_dealer/tod_dealer_<set>_<name>.xanim_bin (+ a report JSON beside this tool's
outputs in art/dealer_boss/engine_kit/clips_report.json). install.py registers them; test_dealer.js gates them.
"""
import sys, json, math, pathlib, os
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
sys.path.insert(0, str(ROOT / 'tools' / 'dealer_boss'))
from mathutils import Matrix, Vector, Quaternion
import numpy as np
from PyCoD import xanim
from process_guard import check

OUT_DIR = ROOT / 'xanim_export' / 'tod_dealer'
REPORT = ROOT / 'art' / 'dealer_boss' / 'engine_kit' / 'clips_report.json'
SKELETON = json.loads((ROOT / 'art' / 'dealer_boss' / 'skeleton.json').read_text())
CLIP_DIRS = [ROOT / 'art' / 'dealer_boss' / 'clips_src', ROOT / 'xanim_export' / 'tod_keeper', ROOT / 'xanim_export' / 'tod_dealer']   # the pack's raw Keeper clips (install.py extracts them; gitignored) + the installed Keeper's

FLOAT_LIFT = 14.0            # inches the body rises off its root in state one (the hem clears the floor)
LIFT_SKIP = {'tag_origin', 'tag_sync', 'tag_aim'}
SMOOTH_SIGMA = 3.0           # frames; the pole direction's low-pass (30 fps clips)
GRIP_U = (-12.0, 32.0)       # inches along the shaft from the right hand where the left hand may sit (pommel -16, ferrule -44 -> blade)
CLASP_NEAR, CLASP_FAR = 14.0, 19.0   # palm-to-palm distance: fully the carry below NEAR, fully a sweep above FAR (the Protector's clasped glide measures 11.4..13.3)
BACK_REF = 8.0               # the sweep's pivot sits this far behind the chest: the pole points from there through the right hand
CARRY_DIR = Vector((-0.20, 0.50, 0.84)).normalized()   # the carry: from the right hand up and across the chest to the left, a little back; the blade rises over the left shoulder
CARRY_MID = Vector((0.62, 0.25, 0.74)).normalized()   # the waypoint the blade passes on its way up into the carry
REACH_MARGIN = 0.5           # the left arm never locks straight

# STATE ONE (levitating, the scythe) and STATE TWO (on the ground, the cracked mask; no scythe hold yet -
# the machine-gun hold is the next pass, its clips are copied through with their own names so the
# selector tables can name them)
SETS = {
    'f': {'lift': FLOAT_LIFT, 'hold': 'scythe', 'clips': [
        'ai_zm_dlc4_keeper_prtctr_walk', 'ai_zm_dlc4_keeper_prtctr_run', 'ai_zm_dlc4_keeper_prtctr_sprint',
        'ai_zm_dlc4_keeper_prtctr_idle', 'ai_zm_dlc4_keeper_prtctr_idle_scan_1', 'ai_zm_dlc4_keeper_prtctr_idle_scan_2',
        'ai_zm_dlc4_keeper_prtctr_idle_attack', 'ai_zm_dlc4_keeper_prtctr_idle_attack_combo', 'ai_zm_dlc4_keeper_prtctr_idle_attack_left',
        'ai_zm_dlc4_keeper_prtctr_idle_attack_right', 'ai_zm_dlc4_keeper_prtctr_idle_attack_up',
        'ai_zm_dlc4_keeper_prtctr_walk_attack', 'ai_zm_dlc4_keeper_prtctr_run_attack', 'ai_zm_dlc4_keeper_prtctr_sprint_attack',
        'ai_zm_dlc4_keeper_prtctr_bamf_in', 'ai_zm_dlc4_keeper_prtctr_bamf_out', 'ai_zm_dlc4_keeper_prtctr_intro', 'ai_zm_dlc4_keeper_prtctr_outtro',
        'ai_zm_dlc4_keeper_prtctr_revive_intro', 'ai_zm_dlc4_keeper_prtctr_revive_loop', 'ai_zm_dlc4_keeper_prtctr_revive_outtro',
        'ai_zm_dlc4_keeper_prtctr_ee_idle']},
    'g': {'lift': 0.0, 'hold': None, 'clips': [
        'ai_zm_dlc4_enslaved_keeper_idle', 'ai_zm_dlc4_enslaved_keeper_run_v1', 'ai_zm_dlc4_enslaved_keeper_run_v2',
        'ai_zm_dlc4_enslaved_keeper_sprint_v1', 'ai_zm_dlc4_enslaved_keeper_sprint_v2',
        'ai_zm_dlc4_enslaved_keeper_attack_v1', 'ai_zm_dlc4_enslaved_keeper_attack_v2', 'ai_zm_dlc4_enslaved_keeper_attack_v3', 'ai_zm_dlc4_enslaved_keeper_attack_v4',
        'ai_zm_dlc4_enslaved_keeper_run_attack_v1', 'ai_zm_dlc4_enslaved_keeper_run_attack_v2', 'ai_zm_dlc4_enslaved_keeper_run_attack_v3', 'ai_zm_dlc4_enslaved_keeper_run_attack_v4',
        'ai_zm_dlc4_enslaved_keeper_dth_v1', 'ai_zm_dlc4_enslaved_keeper_dth_v2', 'ai_zm_dlc4_enslaved_keeper_dth_v3', 'ai_zm_dlc4_enslaved_keeper_dth_v4',
        'ai_zombie_zod_keeper_attack_v1', 'ai_zombie_zod_keeper_attack_v2', 'ai_zombie_zod_keeper_attack_v4',
        'ai_zombie_zod_keeper_run_attack_v4', 'ai_zombie_zod_keeper_dth_f_v1', 'ai_zm_dlc4_keeper_cmpn_revive']},
}
LOOPS = ('_walk', '_run', '_sprint', 'prtctr_idle', 'idle_scan', 'revive_loop', 'ee_idle', 'enslaved_keeper_idle')


def short_name(clip):
    s = clip.replace('ai_zm_dlc4_keeper_prtctr_', '').replace('ai_zm_dlc4_enslaved_keeper_', 'ens_').replace('ai_zombie_zod_keeper_', 'zod_').replace('ai_zm_dlc4_keeper_', '')
    return s


def find_clip(name):
    for d in CLIP_DIRS:
        for ext in ('.xanim_bin', '.XANIM_BIN'):
            p = d / (name + ext)
            if p.exists():
                return p
    raise FileNotFoundError(name)


# ------------------------------------------------------------------ the skeleton: bind transforms, hierarchy
BONES = {b['name']: b for b in SKELETON['bones']}
BY_ID = {b['id']: b for b in SKELETON['bones']}
CHILDREN = {}
for b in SKELETON['bones']:
    if b['parent'] >= 0:
        CHILDREN.setdefault(BY_ID[b['parent']]['name'], []).append(b['name'])


def descendants(name):
    out = []
    stack = list(CHILDREN.get(name, []))
    while stack:
        n = stack.pop(); out.append(n); stack.extend(CHILDREN.get(n, []))
    return out


def bind_rot(name):
    m = BONES[name]['matrix']        # three axes (columns)
    M = Matrix.Identity(3)
    for c in range(3):
        for r in range(3):
            M[r][c] = m[c][r]
    return M


def bind_pos(name):
    return Vector(BONES[name]['offset'])


def part_rot(part):
    M = Matrix.Identity(3)
    for c in range(3):
        for r in range(3):
            M[r][c] = part.matrix[c][r]
    return M


def rows_from_rot(M):
    return [tuple(float(M[r][c]) for r in range(3)) for c in range(3)]   # columns back out as the file's rows


def minimal_rotation(a, b):
    """the smallest rotation taking direction a onto direction b (3x3)"""
    a = a.normalized(); b = b.normalized()
    return a.rotation_difference(b).to_matrix()


def hand_frame(wrist, mid, thumb, left):
    """[f, t, p]: fingers, thumb side, out of the palm (p = -f x t for a right hand, +f x t for a left one:
    the two hands are mirror images, so the same (f, t, p) coordinates describe the same grip on either)"""
    f = (mid - wrist).normalized()
    t = thumb - wrist; t = (t - f * t.dot(f)).normalized()
    p = f.cross(t) * (1.0 if left else -1.0)
    M = Matrix.Identity(3)
    for r in range(3):
        M[r][0], M[r][1], M[r][2] = f[r], t[r], p[r]
    return M


MIRROR = Matrix(((1, 0, 0), (0, -1, 0), (0, 0, 1)))

# bind-pose relations (constant)
B_r0, B_l0 = bind_rot('j_wrist_ri'), bind_rot('j_wrist_le')
A_r0, A_l0 = bind_rot('tag_weapon_right'), bind_rot('tag_weapon_left')
Wr0, Wl0 = bind_pos('j_wrist_ri'), bind_pos('j_wrist_le')
H_r0 = hand_frame(Wr0, bind_pos('j_mid_ri_1'), bind_pos('j_thumb_ri_1'), left=False)
H_l0 = hand_frame(Wl0, bind_pos('j_mid_le_1'), bind_pos('j_thumb_le_1'), left=True)
K_r, K_l = B_r0.inverted() @ H_r0, B_l0.inverted() @ H_l0          # hand frame in wrist space
G_r = H_r0.inverted() @ A_r0                                        # the authored grip (the tag frame) in right-hand coordinates
o_r = B_r0.inverted() @ (bind_pos('tag_weapon_right') - Wr0)         # the palm point in wrist space
o_l = B_l0.inverted() @ (bind_pos('tag_weapon_left') - Wl0)
TAGREL_r = B_r0.inverted() @ A_r0                                   # tag rotation in wrist space
TAGREL_l = B_l0.inverted() @ A_l0
RIGHT_HAND = ['j_wrist_ri'] + descendants('j_wrist_ri')
LEFT_ARM = ['j_shoulder_le'] + descendants('j_shoulder_le')
LEFT_ELBOW = ['j_elbow_le'] + descendants('j_elbow_le')
LEFT_HAND = ['j_wrist_le'] + descendants('j_wrist_le')
TWIST_ri = [n for n in descendants('j_elbow_ri') if 'wristtwist' in n and 'crease' not in n]
TWIST_le = [n for n in descendants('j_elbow_le') if 'wristtwist' in n and 'crease' not in n]


def pole_frame(d, upref):
    """the weapon tag frame whose -X runs along d and whose +Z is as close to upref as it can be"""
    x = -d.normalized()
    z = upref - x * upref.dot(x)
    if z.length < 1e-4:
        z = Vector((0, 0, 1)) - x * x.z
    z.normalize()
    y = z.cross(x).normalized()
    F = Matrix.Identity(3)
    for r in range(3):
        F[r][0], F[r][1], F[r][2] = x[r], y[r], z[r]
    return F


def smooth_vectors(vs, sigma, wrap):
    n = len(vs)
    arr = np.array([[v.x, v.y, v.z] for v in vs], dtype=float)
    if n < 3 or sigma <= 0:
        return [Vector(a) for a in arr]
    half = int(math.ceil(sigma * 3))
    ks = np.arange(-half, half + 1)
    w = np.exp(-0.5 * (ks / sigma) ** 2); w /= w.sum()
    out = np.zeros_like(arr)
    for i in range(n):
        acc = np.zeros(3); tot = 0.0
        for k, wk in zip(ks, w):
            j = i + k
            if wrap:
                j %= n
            else:
                j = min(max(j, 0), n - 1)
            acc += wk * arr[j]; tot += wk
        out[i] = acc / tot
    return [Vector(a) for a in out]


def slerp_dir(a, b, t):
    """rotate unit vector a toward unit vector b by the fraction t of the angle between them"""
    a = a.normalized(); b = b.normalized()
    c = max(-1.0, min(1.0, a.dot(b))); ang = math.acos(c)
    if ang < 1e-4:
        return a
    axis = a.cross(b)
    if axis.length < 1e-4:
        axis = Vector((0, 1, 0)) if abs(a.y) < 0.9 else Vector((1, 0, 0))
        axis = (axis - a * axis.dot(a))
    return (Matrix.Rotation(ang * t, 3, axis.normalized()) @ a).normalized()


def smoothstep(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def about(point, R):
    """a 4x4 rotating by R (3x3) about a world point"""
    T = R.to_4x4()
    T.translation = point - R @ point
    return T


class FrameWorld:
    def __init__(self, parts, fr):
        self.rot = {}; self.pos = {}
        for pi, pname in enumerate(parts):
            p = fr.parts[pi]
            self.rot[pname] = part_rot(p); self.pos[pname] = Vector(p.offset)

    def apply(self, names, T):
        R = T.to_3x3()
        for n in names:
            if n in self.rot:
                self.rot[n] = R @ self.rot[n]; self.pos[n] = T @ self.pos[n]


def solve_scythe(clip, parts, frames, stats):
    """returns one FrameWorld per frame with the hold baked in"""
    worlds = [FrameWorld(parts, fr) for fr in frames]
    wrap = any(k in clip for k in LOOPS)
    # 1. the pole direction and the blade-plane up, raw then smoothed
    d_raw, up_raw, clasp = [], [], []
    for w in worlds:
        # both palms from the WRISTS and the bind-pose hand geometry: the Keeper clips animate tag_weapon_right on
        # its own (it wanders up to 20 in from the hand in the combo) and park tag_weapon_left far away
        R0 = w.pos['j_wrist_ri'] + w.rot['j_wrist_ri'] @ o_r
        Pl = w.pos['j_wrist_le'] + w.rot['j_wrist_le'] @ o_l
        C = w.pos['j_spine4']
        fwd = (C - w.pos['tag_weapon_chest']).normalized()          # the torso's facing (that tag sits on the back)
        hd = (Pl - R0).length
        # the blade points OUTWARD: from a point behind the chest through the right hand. It never points into the
        # body and never flips (the first rule, "past whichever hand is farther out", snapped 97 deg in one frame of
        # the combo); the left hand lands wherever it fits along the shaft, pommel side included.
        two = (R0 - (C - fwd * BACK_REF)).normalized()
        wc = 1.0 - smoothstep((hd - CLASP_NEAR) / (CLASP_FAR - CLASP_NEAR))
        d_raw.append(two); clasp.append(wc)
    # the sweep direction and the carry weight are smoothed separately, then joined on the great circle: a
    # vector average of two near-opposite directions passes through zero and snaps when normalized (the combo
    # turned 104 deg in one frame that way); a slerp sweeps the blade up through the front instead
    two_s = [v.normalized() for v in smooth_vectors(d_raw, SMOOTH_SIGMA, wrap)]
    wc_s = [float(v.x) for v in smooth_vectors([Vector((c, 0, 0)) for c in clasp], SMOOTH_SIGMA, wrap)]
    d_s, up_s = [], []
    for two, wc in zip(two_s, wc_s):
        # the raise into the carry goes through a forward-up waypoint: sweep and carry can be near-opposite (a low
        # swing vs. the blade over the shoulder), where a direct great-circle blend has no defined side
        d = slerp_dir(two, CARRY_MID, 2 * wc) if wc < 0.5 else slerp_dir(CARRY_MID, CARRY_DIR, 2 * wc - 1)
        dz = abs(d.z)
        d_s.append(d); up_s.append(Vector((0, 0, 1)) * (1 - dz * dz) + Vector((-1, 0, 0)) * (dz * dz))
    stats['clasp_mean'] = round(float(np.mean(clasp)), 2)
    stats['loop'] = wrap
    us, gaps = [], []
    for w, d, up in zip(worlds, d_s, up_s):
        F = pole_frame(d, up)
        # 2. the right wrist turns about its joint so the tag's -X runs along the pole
        Wr = w.pos['j_wrist_ri']
        B_r_new = F @ TAGREL_r.inverted()
        w.apply(RIGHT_HAND, about(Wr, B_r_new @ w.rot['j_wrist_ri'].inverted()))
        # the tag itself: rigid to the wrist as at bind (the clips may drift it)
        w.rot['tag_weapon_right'] = F; w.pos['tag_weapon_right'] = Wr + B_r_new @ o_r
        R = w.pos['tag_weapon_right']
        # 3. the left hand: orientation = the right grip's mirror image; position on the shaft
        Fm = pole_frame(MIRROR @ d, MIRROR @ up)
        B_l_new = (MIRROR @ Fm @ G_r.inverted()) @ K_l.inverted()
        Sl, El, Wl = w.pos['j_shoulder_le'], w.pos['j_elbow_le'], w.pos['j_wrist_le']
        a, b = (El - Sl).length, (Wl - El).length
        reach = a + b - REACH_MARGIN
        palm_off = B_l_new @ o_l
        Pl = Wl + w.rot['j_wrist_le'] @ o_l
        u = max(GRIP_U[0], min(GRIP_U[1], (Pl - R).dot(d)))
        base = R - palm_off                                           # the wrist line: base + d*u
        if (base + d * u - Sl).length > reach:
            u_star = max(GRIP_U[0], min(GRIP_U[1], (Sl - base).dot(d)))
            # the nearest reachable u between u and u_star (quadratic in u)
            lo, hi = (u, u_star) if u < u_star else (u_star, u)
            best = u_star
            for t in np.linspace(0, 1, 33):
                cand = u + (u_star - u) * t
                if (base + d * cand - Sl).length <= reach:
                    best = cand; break
            u = best
        target = base + d * u
        tv = target - Sl
        if tv.length > reach:
            gaps.append(round(tv.length - reach, 2)); target = Sl + tv.normalized() * reach; tv = target - Sl
        us.append(round(float(u), 1))
        # two-bone IK keeping the clip's elbow plane
        axis_old = (Wl - Sl); axis_new = tv.normalized()
        n_old = (El - Sl) - axis_old.normalized() * (El - Sl).dot(axis_old.normalized()) if axis_old.length > 1e-5 else Vector()
        if n_old.length < 0.5:
            n_old = Vector((-0.4, 0.3, -1.0))
        n_new = minimal_rotation(axis_old, tv) @ n_old if axis_old.length > 1e-5 else n_old
        n_new = n_new - axis_new * n_new.dot(axis_new)
        if n_new.length < 1e-4:
            n_new = Vector((0, 0, -1)) - axis_new * axis_new.z
        n_new.normalize()
        L = tv.length
        cos_t = max(-1.0, min(1.0, (a * a + L * L - b * b) / (2 * a * L)))
        sin_t = math.sqrt(max(0.0, 1 - cos_t * cos_t))
        El_new = Sl + a * (axis_new * cos_t + n_new * sin_t)
        w.apply(LEFT_ARM, about(Sl, minimal_rotation(El - Sl, El_new - Sl)))
        El2, Wl2 = w.pos['j_elbow_le'], w.pos['j_wrist_le']
        w.apply(LEFT_ELBOW, about(El2, minimal_rotation(Wl2 - El2, target - El2)))
        Wl3 = w.pos['j_wrist_le']
        delta = B_l_new @ w.rot['j_wrist_le'].inverted()
        w.apply(LEFT_HAND, about(Wl3, delta))
        w.rot['tag_weapon_left'] = B_l_new @ TAGREL_l; w.pos['tag_weapon_left'] = Wl3 + B_l_new @ o_l
    stats['u_min'], stats['u_max'] = (min(us), max(us)) if us else (None, None)
    stats['reach_gaps'] = len(gaps); stats['reach_gap_max'] = max(gaps) if gaps else 0.0
    return worlds


def twist_helpers(w_before, w_after, twists, elbow, wrist):
    """distribute the wrist's new turn along the forearm twist bones (rotation only, each about itself)"""
    delta = w_after.rot[wrist] @ w_before.rot[wrist].inverted()
    q = delta.to_quaternion()
    E, W = w_after.pos[elbow], w_after.pos[wrist]
    L = (W - E).length
    for n in twists:
        k = 1.0 - min(1.0, max(0.0, (w_after.pos[n] - W).length / L)) if L > 1e-5 else 0.0
        part = Quaternion((1, 0, 0, 0)).slerp(q, k).to_matrix()
        w_after.rot[n] = part @ w_after.rot[n]


def author(set_key, clip):
    spec = SETS[set_key]
    src = find_clip(clip)
    a = xanim.Anim(); a.LoadFile_Bin(str(src))
    parts = [p.name for p in a.parts]
    missing = [n for n in ('tag_weapon_right', 'j_wrist_le', 'j_spine4', 'j_shoulder_le', 'j_elbow_le') if n not in parts]
    assert not missing, '%s lacks %s' % (clip, missing)
    stats = {'source': src.stem, 'source_file': src.name, 'frames': len(a.frames), 'lift': spec['lift'], 'hold': spec['hold']}
    before = [FrameWorld(parts, fr) for fr in a.frames]
    if spec['hold'] == 'scythe':
        worlds = solve_scythe(clip, parts, a.frames, stats)
        for wb, wa in zip(before, worlds):
            twist_helpers(wb, wa, TWIST_ri, 'j_elbow_ri', 'j_wrist_ri')
            twist_helpers(wb, wa, TWIST_le, 'j_elbow_le', 'j_wrist_le')
    else:
        worlds = before
    # both weapon tags rigid to their wrists as at bind (the Keeper clips animate them loose: a bone-attached
    # weapon would float a hand's length from the hand)
    for w in worlds:
        for wrist, tag, o, rel in (('j_wrist_ri', 'tag_weapon_right', o_r, TAGREL_r), ('j_wrist_le', 'tag_weapon_left', o_l, TAGREL_l)):
            w.rot[tag] = w.rot[wrist] @ rel; w.pos[tag] = w.pos[wrist] + w.rot[wrist] @ o
    lift = Vector((0, 0, spec['lift']))
    new_frames = []
    for fr, w in zip(a.frames, worlds):
        nf = xanim.Frame(fr.frame)
        for pname in parts:
            pos = w.pos[pname] + (lift if pname not in LIFT_SKIP else Vector())
            nf.parts.append(xanim.FramePart((pos.x, pos.y, pos.z), rows_from_rot(w.rot[pname])))
        new_frames.append(nf)
    a.frames = new_frames
    out = OUT_DIR / ('tod_dealer_%s_%s.xanim_bin' % (set_key, short_name(clip)))
    a.WriteFile_Bin(str(out), version=getattr(a, 'version', None) or 3)
    # round trip
    chk = xanim.Anim(); chk.LoadFile_Bin(str(out))
    assert len(chk.frames) == len(a.frames) and [p.name for p in chk.parts] == parts, out
    i = parts.index('tag_weapon_right')
    err = max((Vector(chk.frames[f].parts[i].offset) - Vector(a.frames[f].parts[i].offset)).length for f in range(len(a.frames)))
    assert err < 0.05, (out, err)
    import hashlib
    stats['out'] = out.name; stats['sha256'] = hashlib.sha256(out.read_bytes()).hexdigest()
    return out.name, stats


def main():
    check(min_mb=900, strict=False)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {'float_lift': FLOAT_LIFT, 'grip_u': GRIP_U, 'smooth_sigma': SMOOTH_SIGMA, 'clips': {}}
    only = [a for a in sys.argv[sys.argv.index('--') + 1:]] if '--' in sys.argv else []
    for set_key, spec in SETS.items():
        for clip in spec['clips']:
            if only and not any(o in clip for o in only):
                continue
            name, stats = author(set_key, clip)
            report['clips'][name] = stats
            print('authored', name, json.dumps(stats))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=1))
    print('AUTHORED', len(report['clips']), 'clips ->', OUT_DIR)


if __name__ == '__main__':
    main()
