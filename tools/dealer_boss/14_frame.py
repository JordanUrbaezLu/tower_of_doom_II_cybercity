"""14: pause the reel on a named clip (timeline marker substring + offset) or resume playback.
Globals: MARKER (substring of a marker name), OFFSET (frames into it, default 30), RESUME (True = play).
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
win = bpy.context.window_manager.windows[0]
with bpy.context.temp_override(window=win, screen=win.screen):
    if win.screen.is_animation_playing:
        bpy.ops.screen.animation_cancel(restore_frame=False)
if globals().get('RESUME'):
    with bpy.context.temp_override(window=win, screen=win.screen):
        bpy.ops.screen.animation_play()
    print(json.dumps({'playing': True}))
else:
    key = globals().get('MARKER', 'walk')
    m = next((m for m in sorted(scene.timeline_markers, key=lambda m: m.frame) if key in m.name), None)
    assert m is not None, 'no marker containing ' + key
    f = m.frame + int(globals().get('OFFSET', 30))
    scene.frame_set(f); bpy.context.view_layer.update()
    print(json.dumps({'marker': m.name, 'frame': f}))
