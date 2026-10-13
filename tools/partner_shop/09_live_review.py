"""Leave the user's visible studio running the authored sign animation."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
scene=bpy.context.scene;assert scene.get('tod2_shop_studio')
# Eevee uses the same scene lights/materials and makes timeline playback practical.
try:
    scene.render.engine='BLENDER_EEVEE'
except TypeError:
    scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.fps=30;scene.sync_mode='FRAME_DROP';scene.frame_set(1)
hero=bpy.data.objects['01 HERO - three-quarter'];scene.camera=hero
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.shading.type='RENDERED';s.shading.use_scene_world_render=True;s.shading.use_scene_lights_render=True
            s.overlay.show_overlays=False;s.clip_end=5000
            s.region_3d.view_rotation=hero.rotation_euler.to_quaternion();s.region_3d.view_location=(0,-2,61);s.region_3d.view_distance=305
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/partner_shop/partner_shop.blend'))
if bpy.context.screen and not bpy.context.screen.is_animation_playing:
    bpy.ops.screen.animation_play()
print(json.dumps({'engine':scene.render.engine,'playing':bool(bpy.context.screen and bpy.context.screen.is_animation_playing),'master':bpy.data.filepath}))
