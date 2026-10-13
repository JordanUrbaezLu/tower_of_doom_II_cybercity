"""Select the reviewed glass preview in the live window, regardless of startup UI."""
import hashlib
import json
import pathlib
import runpy
import sys

import bpy

ROOT = pathlib.Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'art/crown_alarm/lens_review'
receipt = json.loads((REVIEW / 'preview.json').read_text(encoding='utf-8-sig'))
blend = REVIEW / 'native_preview.blend'
assert pathlib.Path(bpy.data.filepath).resolve() == blend.resolve(), 'Wrong preview scene'
assert hashlib.sha256(blend.read_bytes()).hexdigest() == receipt['native_preview_sha256'], 'Preview receipt mismatch'
lens = bpy.data.materials['mtl_tod_alarm_lens']
assert lens['preview_specular_mask'] == 0, 'Stale glass preview'
assert all(abs(v - .04) < 1e-7 for v in lens['native_f0']), 'Stale glass optics'
assert bpy.context.scene.camera is not None, 'Reviewed camera is missing'
bpy.context.scene.cycles.use_preview_denoising = True

def activate():
    views = []
    for window in bpy.context.window_manager.windows:
        area = max(window.screen.areas, key=lambda item: item.width * item.height)
        area.type = 'VIEW_3D'
        for view in window.screen.areas:
            if view.type != 'VIEW_3D':
                continue
            space = view.spaces.active
            space.shading.type = 'RENDERED'
            space.shading.use_scene_lights_render = True
            space.shading.use_scene_world_render = True
            space.overlay.show_overlays = False
            space.region_3d.view_perspective = 'CAMERA'
            space.region_3d.view_camera_zoom = 0
            view.tag_redraw()
            views.append({'shading': space.shading.type, 'scene_lights': True, 'scene_world': True, 'view': 'CAMERA'})
    assert views, 'No visible preview window'
    proof = {'file': bpy.data.filepath, 'sha256': receipt['native_preview_sha256'],
             'engine': bpy.context.scene.render.engine, 'preview_denoising': True, 'views': views}
    (ROOT / 'tmp/alarm_lens_repair/visible_configuration.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print('LENS_VISIBLE_PREVIEW_READY', json.dumps(proof), flush=True)

activate()
# Startup preferences can replace a file's saved screen after the first call.
# Restore the live view once more after window initialization without resaving.
bpy.app.timers.register(activate, first_interval=1.0)

# The launcher owns the visible studio and its resource watcher. A later MCP
# read can execute this same configuration without starting a second server.
if '--alarm-preview' in sys.argv and not hasattr(bpy.types, 'tod2_alarm_mcp'):
    runpy.run_path(str(ROOT / 'tools/crown_alarm/mcp_bootstrap.py'), run_name='__main__')
