"""Show the authored pad in a lit live MCP viewport and save the review state."""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.preview_samples=16
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.shading.type='MATERIAL';s.shading.use_scene_lights=True;s.shading.use_scene_world=True;s.overlay.show_overlays=False
            s.region_3d.view_location=(0,0,0);s.region_3d.view_distance=225;s.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
# Keep the hashed master unchanged after native baking. This review-only file
# is for live inspection and can be discarded without affecting the export.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/teleporter/teleporter_review.blend'))
print('TELEPORTER_LIVE_REVIEW_READY')
