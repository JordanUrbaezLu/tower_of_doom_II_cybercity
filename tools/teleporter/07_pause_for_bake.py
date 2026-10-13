import bpy
s=bpy.context.scene
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.shading.type='SOLID'
s.render.engine='BLENDER_WORKBENCH'
print('TELEPORTER_PREVIEW_PAUSED_FOR_NATIVE_BAKE; master unchanged')
