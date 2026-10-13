import bpy
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s['teleporter_preview_auto']=1;s.frame_set(100)
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.shading.type='RENDERED';a.spaces.active.overlay.show_overlays=False
if bpy.context.screen and not bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_play()
print('TELEPORTER_PREVIEW_RUNNING; master unchanged')
