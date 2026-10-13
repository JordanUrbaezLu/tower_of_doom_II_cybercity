"""Pose the Dealer with a real Keeper clip inside the studio (review only, never exported).

pose_frame(rig, path, frame)      - one frame, no keyframes (fast; the pose check uses it)
load_action(rig, path, name, step) - the whole clip as an action for scrubbing in the studio

The XANIM_BIN stores every part's absolute model-space transform per frame.
Delta clips carry their root motion on tag_origin; posing subtracts it so the
character stays on the stage the way the engine keeps an actor on its origin.
Blender's pose basis for bone b with rest matrix R and parent pose P_p is
B = R^-1 * R_p * P_p^-1 * P, so a clip converts with no scene updates.
"""
import sys, pathlib, glob, os
import bpy
from mathutils import Matrix, Vector
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xanim

CLIP_DIRS = [ROOT / 'xanim_export/tod_keeper', ROOT / 'xanim_export/tod_dealer',
             pathlib.Path(os.path.expandvars(r'%TEMP%\tod_dealer_clips\T7 Assets V2.8\xanim_export\_midgetblaster\black_ops_3'))]


def find_clip(name):
    for d in CLIP_DIRS:
        for ext in ('.xanim_bin', '.XANIM_BIN'):
            p = d / (name + ext)
            if p.exists():
                return p
        hits = glob.glob(str(d / '**' / (name + '.*')), recursive=True)
        if hits:
            return pathlib.Path(hits[0])
    raise FileNotFoundError(name)


def part_matrix(part, root_offset=None):
    m = Matrix.Identity(4)
    X, Y, Z = (Vector(part.matrix[i]) for i in range(3))
    off = Vector(part.offset) - (root_offset or Vector())
    for r in range(3):
        m[r][0], m[r][1], m[r][2] = X[r], Y[r], Z[r]
        m[r][3] = off[r]
    return m


def _prep(rig, path):
    a = xanim.Anim(); a.LoadFile_Bin(str(path))
    parts = [p.name for p in a.parts]
    bones = rig.data.bones
    rest = {b.name: b.matrix_local.copy() for b in bones}
    rest_inv = {n: m.inverted() for n, m in rest.items()}
    order = []
    def walk(b):
        order.append(b.name)
        for c in b.children:
            walk(c)
    for b in bones:
        if b.parent is None:
            walk(b)
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    return a, parts, bones, rest, rest_inv, order


def _apply_frame(rig, fr, parts, bones, rest, rest_inv, order, key_frame=None):
    root_i = parts.index('tag_origin') if 'tag_origin' in parts else -1
    root_off = Vector(fr.parts[root_i].offset) if root_i >= 0 else Vector()
    world = {pname: part_matrix(fr.parts[pi], root_off) for pi, pname in enumerate(parts)}
    for bn in order:
        if bn not in world:
            continue
        P = world[bn]
        parent = bones[bn].parent
        if parent and parent.name in world:
            basis = rest_inv[bn] @ rest[parent.name] @ world[parent.name].inverted() @ P
        else:
            basis = rest_inv[bn] @ P
        pb = rig.pose.bones[bn]
        pb.matrix_basis = basis
        if key_frame is not None:
            pb.keyframe_insert('location', frame=key_frame, group=bn)
            pb.keyframe_insert('rotation_quaternion', frame=key_frame, group=bn)


def pose_frame(rig, path, frame):
    a, parts, bones, rest, rest_inv, order = _prep(rig, path)
    frame = max(0, min(len(a.frames) - 1, int(frame)))
    if rig.animation_data:
        rig.animation_data.action = None
    _apply_frame(rig, a.frames[frame], parts, bones, rest, rest_inv, order)
    return len(a.frames)


def load_action(rig, path, name=None, frame_step=2):
    a, parts, bones, rest, rest_inv, order = _prep(rig, path)
    name = name or pathlib.Path(path).stem
    act = bpy.data.actions.new(name)
    rig.animation_data_create(); rig.animation_data.action = act
    nfr = len(a.frames)
    for fi in range(0, nfr, frame_step):
        _apply_frame(rig, a.frames[fi], parts, bones, rest, rest_inv, order, key_frame=fi + 1)
    bpy.context.scene.frame_start = 1; bpy.context.scene.frame_end = nfr
    bpy.context.scene.render.fps = a.framerate or 30
    act['clip'] = str(path); act['frames'] = nfr
    return act


def rest_pose(rig):
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    if rig.animation_data:
        rig.animation_data.action = None


if 'CLIP' in globals():
    rig = bpy.data.objects['DEALER_RIG | Keeper animation skeleton']
    clip = globals()['CLIP']
    if globals().get('SCRUB'):
        act = load_action(rig, find_clip(clip), clip)
        bpy.context.scene.frame_set(int(globals().get('FRAME', 1)))
        print('LOADED', clip, act['frames'], 'frames; scrub the timeline in the studio')
    else:
        n = pose_frame(rig, find_clip(clip), int(globals().get('FRAME', 1)))
        print('POSED', clip, 'frame', globals().get('FRAME', 1), 'of', n)
