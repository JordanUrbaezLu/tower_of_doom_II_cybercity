"""Render local MCP-authored matched states and motion. Never invokes BO3."""
import bpy, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/crown_alarm/intensity_review'
for state in ['before', 'stronger']:
    bpy.ops.wm.open_mainfile(filepath=str(OUT / (state + '.blend')))
    scene = next(s for s in bpy.data.scenes if s.name.startswith('Actual crown'))
    bpy.context.window_manager.windows[0].scene = scene
    p = bpy.context.preferences.addons['cycles'].preferences
    p.compute_device_type = 'OPTIX'
    p.get_devices()
    for d in p.devices:
        d.use = d.type == 'OPTIX'
    scene.cycles.device = 'GPU'
    scene.render.filepath = str(OUT / (state + '.png'))
    bpy.ops.render.render(write_still=True)
    print('ALARM_REVIEW_RENDER', state, flush=True)
    if state == 'stronger':
        scene.render.resolution_x = 680
        scene.render.resolution_y = 425
        scene.cycles.samples = 12
        frames = OUT / 'frames'
        frames.mkdir(exist_ok=True)
        for frame in range(1, 37, 2):
            scene.frame_set(frame)
            scene.render.filepath = str(frames / (str(frame).zfill(3) + '.png'))
            bpy.ops.render.render(write_still=True)
        print('ALARM_REVIEW_MOTION_FRAMES', 18, flush=True)
