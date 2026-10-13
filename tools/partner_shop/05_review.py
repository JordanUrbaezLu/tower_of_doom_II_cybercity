"""Current scene review with the live studio's real lights."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/partner_shop'
scene=bpy.context.scene
assert scene.get('tod2_shop_studio')
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    has_gpu=False
    for device in prefs.devices:
        device.use=device.type!='CPU';has_gpu |= device.use
    if has_gpu:scene.cycles.device='GPU'
except Exception:pass
scene.camera=bpy.data.objects['01 HERO - three-quarter']
scene.render.resolution_x=1440;scene.render.resolution_y=1200
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.shading.type='RENDERED';s.overlay.show_overlays=False;s.clip_end=5000
            s.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
            s.region_3d.view_location=(0,-2,61);s.region_3d.view_distance=305
scene.render.filepath=str(OUT/'hero.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['02 PLAYER - service window']
scene.render.resolution_x=1440;scene.render.resolution_y=1100
scene.render.filepath=str(OUT/'player_view.png')
bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['01 HERO - three-quarter']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print(json.dumps({'review':str(OUT/'hero.png'),'objects':len(scene.objects)}))
