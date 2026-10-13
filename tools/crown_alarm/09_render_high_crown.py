"""Render the two MCP-authored distant-crown comparison states."""
import bpy, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/crown_alarm/high_crown_review'
for state in ['before', 'high_4x']:
    bpy.ops.wm.open_mainfile(filepath=str(OUT / (state + '.blend')))
    scene = next(s for s in bpy.data.scenes if s.name.startswith('Actual crown'))
    bpy.context.window_manager.windows[0].scene = scene
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    scene.cycles.device = 'GPU'
    scene.render.filepath = str(OUT / (state + '.png'))
    bpy.ops.render.render(write_still=True)
    print('HIGH_CROWN_RENDER', state, flush=True)
