"""00: load the saved Dealer master into a fresh studio window (after a restart)."""
import pathlib, json
import bpy
ROOT = pathlib.Path(__file__).resolve().parents[2]
master = ROOT / 'art/dealer_boss/dealer_boss.blend'
bpy.ops.wm.open_mainfile(filepath=str(master))
scene = bpy.context.scene
scene['tod2_dealer_boss_studio'] = True
cam = bpy.data.objects.get('CAM 01 | hero three-quarter')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            s = area.spaces.active; s.shading.type = 'MATERIAL'; s.clip_end = 5000
            if cam:
                s.region_3d.view_rotation = cam.rotation_euler.to_quaternion()
                s.region_3d.view_location = (0, 0, 42); s.region_3d.view_distance = 170
print(json.dumps({'opened': str(master), 'stage': scene.get('dealer_stage'), 'objects': len(scene.objects)}))
