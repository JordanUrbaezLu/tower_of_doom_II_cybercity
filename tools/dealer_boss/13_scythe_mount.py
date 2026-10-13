"""13: MOUNT THE SCYTHE the way the game does - a rigid model on tag_weapon_right, nothing else.

The two-hand hold now lives INSIDE the Dealer's authored clips (author_clips.py), so the studio
shows exactly what the engine will: every scythe part bone-parented to the right weapon tag in its
authored local frame (the pole through the tag origin along -X). Wired in the REST pose with the
rig visible, the old grip / aim empties removed; then the reel resumes (FRAME to pause instead).
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
TAG = 'tag_weapon_right'
tagb = BONES[TAG]
tag_mat = Matrix.Identity(4)
for r in range(3):
    for c in range(3):
        tag_mat[r][c] = tagb['matrix'][c][r]
    tag_mat[r][3] = tagb['offset'][r]
cw = next(c for c in bpy.data.collections if c.name.startswith('DEALER | 06'))
parts = [ob for ob in cw.objects if ob.get('scythe_part')]
assert parts, 'no scythe parts: run 11_weapons.py first'
win = bpy.context.window_manager.windows[0]
with bpy.context.temp_override(window=win, screen=win.screen):
    if win.screen.is_animation_playing:
        bpy.ops.screen.animation_cancel(restore_frame=False)
action = RIG.animation_data.action if RIG.animation_data else None
if RIG.animation_data:
    RIG.animation_data.action = None
for pb in RIG.pose.bones:
    pb.matrix_basis.identity()
RIG.hide_viewport = False
bpy.context.view_layer.update()
for name in ('Scythe | two-hand grip', 'Scythe | aim'):
    ob = bpy.data.objects.get(name)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
# every part's mesh was authored in the tag's own frame (11_weapons.py), so its world matrix at rest IS the tag frame
for ob in parts:
    ob.parent = RIG; ob.parent_type = 'BONE'; ob.parent_bone = TAG; ob.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    ob.matrix_world = tag_mat
bpy.context.view_layer.update()
blade = next(o for o in parts if 'hooked blade' in o.name)
bb = [blade.matrix_world @ Vector(c) for c in blade.bound_box]
if action is not None:
    RIG.animation_data.action = action
RIG.hide_viewport = True
frame = globals().get('FRAME')
if frame is not None:
    scene.frame_set(int(frame))
else:
    with bpy.context.temp_override(window=win, screen=win.screen):
        bpy.ops.screen.animation_play()
bpy.context.view_layer.update()
save(scene.get('dealer_stage', '13_scythe_mount'))
print(json.dumps({'stage': '13_scythe_mount', 'parts': len(parts), 'tag_rest': [round(x, 1) for x in tag_mat.translation],
                  'blade_bbox_rest_x': [round(min(v.x for v in bb), 1), round(max(v.x for v in bb), 1)], 'blade_bbox_rest_z': [round(min(v.z for v in bb), 1), round(max(v.z for v in bb), 1)]}))
