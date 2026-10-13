"""MCP authoring: two native firearm holds, staged without changing the shipped master/clips.

The exported transforms are the ones reviewed in Blender. Both arms use measured
joint lengths; weapon +X aims forward, the left palm reaches the actual foregrip.
Root and skeleton stay unchanged; only the shock body levitates. No melee notes.
"""
import importlib.util
import json
import math
import pathlib
import hashlib
import sys
from mathutils import Vector, Matrix

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'tmp/dealer_combat_stage/xanim_export/tod_dealer'
OUT.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('dc_clip_math', pathlib.Path(__file__).with_name('author_clips.py'))
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
C.check(strict=False)
from PyCoD import xanim, xmodel


def arm(w, side, palm, orientation):
    shoulder, elbow, wrist = ['j_%s_%s' % (part, side) for part in ('shoulder', 'elbow', 'wrist')]
    tag = 'tag_weapon_' + ('right' if side == 'ri' else 'left')
    rel, offset = (C.TAGREL_r, C.o_r) if side == 'ri' else (C.TAGREL_l, C.o_l)
    B = orientation @ rel.inverted()
    target = palm - B @ offset
    S, E, W = (w.pos[n].copy() for n in (shoulder, elbow, wrist))
    a, b = (E-S).length, (W-E).length
    delta = target-S
    assert .5 < delta.length < a+b-.1, (side, delta.length, a+b)
    axis = delta.normalized()
    # Elbows down and out from the torso; stable through raise/recoil.
    bend = Vector((0, -1 if side == 'ri' else 1, -.7))
    bend = (bend-axis*bend.dot(axis)).normalized()
    cos = max(-1, min(1, (a*a+delta.length**2-b*b)/(2*a*delta.length)))
    Enew = S+a*(axis*cos+bend*math.sqrt(1-cos*cos))
    w.apply([shoulder]+C.descendants(shoulder), C.about(S, C.minimal_rotation(E-S, Enew-S)))
    E2, W2 = w.pos[elbow].copy(), w.pos[wrist].copy()
    w.apply([elbow]+C.descendants(elbow), C.about(E2, C.minimal_rotation(W2-E2, target-E2)))
    w.apply([wrist]+C.descendants(wrist), C.about(w.pos[wrist], B @ w.rot[wrist].inverted()))
    w.rot[tag] = orientation
    w.pos[tag] = w.pos[wrist]+B @ offset
    return (w.pos[tag]-palm).length


don = ROOT / 'art/dealer_boss/donors'
manifest = json.loads((don/'manifest.json').read_text())
models = {}
for key in ('dg2', 'dingo'):
    m = xmodel.Model()
    m.LoadFile_Bin(str(don/manifest['models'][key]['file']))
    flashes = [b for b in m.bones if b.name == 'tag_flash']
    assert len(flashes) == 1, (key, [b.name for b in m.bones])
    models[key] = list(flashes[0].offset)

report = {'weapon_muzzles': models, 'clips': {}}
for kind, source, frames, lift, weapon in (
        ('shock', 'ai_zm_dlc4_keeper_prtctr_idle', 78, 14, 'dg2'),
        ('burst', 'ai_zm_dlc4_enslaved_keeper_idle', 105, 0, 'dingo')):
    a = xanim.Anim(); a.LoadFile_Bin(str(C.find_clip(source)))
    parts = [p.name for p in a.parts]
    original = a.frames
    authored, gaps = [], []
    for fi in range(frames):
        base = original[fi % len(original)]
        w = C.FrameWorld(parts, base)
        before = C.FrameWorld(parts, base)
        t = fi/30
        # Settle the ready hold, tiny breathing, then measured recoil during release.
        raise_k = C.smoothstep(t/.22)
        recoil = 0
        if kind == 'burst' and 1.4 <= t < 1.4+6*.25:
            recoil = 1.0*math.exp(-((t-1.4) % .25)/.05)
        if kind == 'shock' and 1.9 <= t < 2.15:
            recoil = 1.4*math.exp(-(t-1.9)/.07)
        F = C.pole_frame(Vector((-1, 0, .10+recoil*.018)), Vector((0,0,1)))
        chest = w.pos['j_spine4']
        grip = chest+Vector((2-recoil, -2, -5+(1-raise_k)*-2+.3*math.sin(t*2)))
        left = grip+F @ Vector((7, .2, -1))
        gaps.append(arm(w, 'ri', grip, F))
        # Existing bind hand frames define the palm; this puts its palm on the underside.
        Fl = F @ Matrix.Rotation(math.pi, 3, 'X')
        gaps.append(arm(w, 'le', left, Fl))
        C.twist_helpers(before,w,C.TWIST_ri,'j_elbow_ri','j_wrist_ri')
        C.twist_helpers(before,w,C.TWIST_le,'j_elbow_le','j_wrist_le')
        nf = xanim.Frame(fi)
        for p in parts:
            pos = w.pos[p]+(Vector((0,0,lift)) if p not in C.LIFT_SKIP else Vector())
            nf.parts.append(xanim.FramePart(tuple(pos), C.rows_from_rot(w.rot[p])))
        authored.append(nf)
    assert max(gaps)<.05, (kind,max(gaps))
    a.frames = authored; a.notes = []; a.framerate = 30
    name = 'tod_dealer_c_'+kind
    path = OUT/(name+'.xanim_bin')
    a.WriteFile_Bin(str(path), version=3)
    chk = xanim.Anim(); chk.LoadFile_Bin(str(path))
    assert len(chk.frames)==frames and not chk.notes and [p.name for p in chk.parts]==parts
    report['clips'][name] = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        frames=frames, fps=30, lift=lift, source=source, weapon=weapon, hand_gap_max=max(gaps),
        file=path.relative_to(ROOT/'tmp/dealer_combat_stage').as_posix())
(OUT/'combat_clips.json').write_text(json.dumps(report,indent=2))
print('DEALER COMBAT CLIPS STAGED:', json.dumps(report))
