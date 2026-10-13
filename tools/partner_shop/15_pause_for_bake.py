"""Keep Blender open while releasing the shop's live render workload for Radiant."""
import bpy
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.shading.type='SOLID'
bpy.context.scene.render.engine='BLENDER_WORKBENCH'
print('Shop window remains open; rendered animation paused for native lighting bake.')
