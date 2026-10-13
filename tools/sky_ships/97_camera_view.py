"""Studio helper: look through the PLAYER VIEW camera (the in-game framing) in every 3D view."""
import bpy
for win in bpy.context.window_manager.windows:
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            sp = area.spaces.active
            sp.shading.type = 'RENDERED'
            sp.region_3d.view_perspective = 'CAMERA'
            sp.overlay.show_overlays = False
print('SKY_CAMERA_VIEW')
