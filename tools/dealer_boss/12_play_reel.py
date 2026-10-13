"""12: PLAY THE REEL - the Dealer's AUTHORED clips (author_clips.py: levitation + the two-hand scythe hold baked in)
back to back in the live studio; raw Keeper clips may be named too (Protector clips are lifted live for an A/B).

Builds one action ("DEALER REEL") from the real XANIM_BINs with a timeline marker naming each
clip, assigns it to the rig and starts viewport playback (root motion removed, so he performs in
place). Scrub the timeline or press space in the window to pause. Nothing is exported.
Globals: PLAYLIST (clip names), LOOP_WEAPON ('scythe' | 'dg2' | 'dingo' | 'none').
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
import importlib.util
spec = importlib.util.spec_from_file_location('dealer_anim_preview', str(Path(__file__).with_name('anim_preview.py')))
ap = importlib.util.module_from_spec(spec); spec.loader.exec_module(ap)

PLAYLIST = globals().get('PLAYLIST', [
    'tod_dealer_f_intro', 'tod_dealer_f_idle', 'tod_dealer_f_idle_scan_1', 'tod_dealer_f_walk', 'tod_dealer_f_run', 'tod_dealer_f_sprint',
    'tod_dealer_f_idle_attack_left', 'tod_dealer_f_idle_attack_right', 'tod_dealer_f_idle_attack_up', 'tod_dealer_f_idle_attack_combo',
    'tod_dealer_f_bamf_out', 'tod_dealer_f_bamf_in', 'tod_dealer_f_revive_loop',
    'tod_dealer_g_ens_idle', 'tod_dealer_g_ens_run_v1', 'tod_dealer_g_ens_sprint_v1', 'tod_dealer_g_ens_attack_v1', 'tod_dealer_g_ens_attack_v2',
    'tod_dealer_g_zod_attack_v4', 'tod_dealer_g_ens_run_attack_v1', 'tod_dealer_g_ens_dth_v1'])
weapon = globals().get('LOOP_WEAPON', 'scythe')
FLOAT_LIFT = float(globals().get('FLOAT_LIFT', 14.0))
FLOATS = lambda clip: 'prtctr' in clip          # raw Protector clips get the lift live; authored tod_dealer_* clips carry it baked
LIFT_SKIP = {'tag_origin', 'tag_sync', 'tag_aim'}

# ------------------------------------------------------------------ per-frame pose bases, straight from the clips
bones = RIG.data.bones
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
for pb in RIG.pose.bones:
    pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
if RIG.animation_data:
    RIG.animation_data.action = None

tracks = {n: {'loc': [], 'rot': []} for n in order}
markers = []
frame = 1
for clip in PLAYLIST:
    try:
        path = ap.find_clip(clip)
    except FileNotFoundError:
        print('MISSING', clip); continue
    a, parts, _bones, _rest, _rest_inv, _order = ap._prep(RIG, path)
    root_i = parts.index('tag_origin') if 'tag_origin' in parts else -1
    lift = Vector((0, 0, FLOAT_LIFT)) if FLOATS(clip) else Vector()
    state = 'S1 float ' if (FLOATS(clip) or '_f_' in clip) else 'S2 ground '
    markers.append((frame, state + clip.replace('ai_zm_dlc4_', '').replace('ai_zombie_', '').replace('tod_dealer_', '')))
    for fr in a.frames:
        root_off = Vector(fr.parts[root_i].offset) if root_i >= 0 else Vector()
        world = {pname: ap.part_matrix(fr.parts[pi], root_off - (lift if pname not in LIFT_SKIP else Vector())) for pi, pname in enumerate(parts)}
        for bn in order:
            if bn in world:
                P = world[bn]; parent = bones[bn].parent
                if parent and parent.name in world:
                    basis = rest_inv[bn] @ rest[parent.name] @ world[parent.name].inverted() @ P
                else:
                    basis = rest_inv[bn] @ P
            else:
                basis = Matrix.Identity(4)
            loc = basis.to_translation(); q = basis.to_quaternion()
            prev = tracks[bn]['rot'][-1][1] if tracks[bn]['rot'] else None
            if prev is not None and prev.dot(q) < 0:
                q = -q            # keep the quaternion track continuous (no 360-degree whips between frames)
            tracks[bn]['loc'].append((frame, loc)); tracks[bn]['rot'].append((frame, q))
        frame += 1
    # a short hold on the last frame so the cuts read
    frame += 6
    for bn in order:
        f, l = tracks[bn]['loc'][-1]; tracks[bn]['loc'].append((frame - 1, l))
        f, q = tracks[bn]['rot'][-1]; tracks[bn]['rot'].append((frame - 1, q))
total = frame

# ------------------------------------------------------------------ one action, fcurves filled in bulk
old = bpy.data.actions.get('DEALER REEL')
if old:
    bpy.data.actions.remove(old)
act = bpy.data.actions.new('DEALER REEL')
for bn in order:
    loc = tracks[bn]['loc']; rot = tracks[bn]['rot']
    if not loc:
        continue
    for ch, data, n in (('location', loc, 3), ('rotation_quaternion', rot, 4)):
        for i in range(n):
            fc = act.fcurves.new('pose.bones["%s"].%s' % (bn, ch), index=i, action_group=bn)
            fc.keyframe_points.add(len(data))
            flat = []
            for f, v in data:
                flat += [f, v[i]]
            fc.keyframe_points.foreach_set('co', flat)
            fc.update()
RIG.animation_data_create(); RIG.animation_data.action = act
scene.frame_start = 1; scene.frame_end = total; scene.render.fps = 30
for m in list(scene.timeline_markers):
    scene.timeline_markers.remove(m)
for f, name in markers:
    scene.timeline_markers.new(name, frame=f)
scene.frame_set(1)

# ------------------------------------------------------------------ the stage for watching
for c in bpy.data.collections:
    if c.name.startswith('DEALER | 91'):
        c.hide_viewport = True
    if c.name.startswith('DEALER | 06'):
        # the scythe through state one, the machine gun through state two (keyed on the markers)
        spans = [(f, (markers[i + 1][0] if i + 1 < len(markers) else total)) for i, (f, name) in enumerate(markers)]
        states = [m[1].startswith('S1') for m in markers]
        for ob in c.objects:
            ob.animation_data_clear()
            want = ob.get('weapon')
            if want not in ('scythe', 'dingo'):
                ob.hide_viewport = True; ob.hide_render = True; continue
            for (f0, f1), s1 in zip(spans, states):
                hid = (want == 'scythe') != s1
                ob.hide_viewport = hid; ob.hide_render = hid
                ob.keyframe_insert('hide_viewport', frame=f0); ob.keyframe_insert('hide_render', frame=f0)
RIG.hide_viewport = True   # the stick skeleton would draw through the coat
cam = bpy.data.objects.get('CAM 01 | hero three-quarter')
win = bpy.context.window_manager.windows[0]
for area in win.screen.areas:
    if area.type == 'VIEW_3D':
        s = area.spaces.active; s.shading.type = 'MATERIAL'; s.overlay.show_overlays = False
        if cam:
            s.region_3d.view_rotation = cam.rotation_euler.to_quaternion()
            s.region_3d.view_location = (0, 0, 42); s.region_3d.view_distance = 165
        with bpy.context.temp_override(window=win, screen=win.screen, area=area, region=next(r for r in area.regions if r.type == 'WINDOW')):
            if not win.screen.is_animation_playing:
                bpy.ops.screen.animation_play()
        break
print(json.dumps({'stage': 'reel', 'clips': [m[1] for m in markers], 'frames': total, 'seconds': round(total / 30.0, 1), 'weapon': weapon}))
