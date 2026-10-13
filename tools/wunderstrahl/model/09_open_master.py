"""MCP step 09: leave the editable Wunderstrahl master open in the visible studio for the user to inspect.

Opens art/wunderstrahl/wunderstrahl.blend (DG-2 meshes re-surfaced + the procedural emitter parts), frames the
emitter close-up camera and switches every 3D view to Material Preview. Saves nothing.
CAMERA='lens_close' (default) | quarter_left | quarter_right | profile_left | top | lens_front
"""
import bpy, importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, blendlib
importlib.reload(common); importlib.reload(blendlib)

bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'wunderstrahl.blend'))
cam = bpy.data.objects.get('Review | ' + globals().get('CAMERA', 'lens_close'))
blendlib.show_in_viewport(cam, 'MATERIAL')
for win in bpy.context.window_manager.windows:
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.overlay.show_overlays = False
            area.spaces.active.region_3d.view_camera_zoom = 0
print('WS_09_OPEN master', common.rel(common.ART / 'wunderstrahl.blend'), 'camera', cam.name if cam else None, flush=True)
