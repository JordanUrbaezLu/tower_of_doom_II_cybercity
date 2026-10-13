"""MCP: leave the editable Cyber Sword open for the user."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/cyber_sword/cyber_sword.blend'))
scene=bpy.context.scene;scene.frame_set(60);scene.update_tag();bpy.context.view_layer.update()
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.region_3d.view_camera_zoom=-15
            area.spaces.active.region_3d.view_camera_offset=(0,0)
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.overlay.show_overlays=False
print('CYBER_SWORD_OPEN: editable master; frame 1 charging, frame 60 ready; timeline includes glow transition')
