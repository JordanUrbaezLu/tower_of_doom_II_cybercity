"""Stop playback and drop the studio viewport to SOLID so a background bake has the GPU."""
import bpy
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.shading.type='SOLID';area.tag_redraw()
print('STUDIO_QUIET')
