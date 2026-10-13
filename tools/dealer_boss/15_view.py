"""15: turn the studio viewport. Globals: AZ (deg, 0 = from +X / in front of him, 90 = his left side), EL (deg up), DIST, TARGET (x,y,z)."""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
import math as _m
az = _m.radians(float(globals().get('AZ', 35))); el = _m.radians(float(globals().get('EL', 12)))
dist = float(globals().get('DIST', 230)); target = Vector(globals().get('TARGET', (0, 0, 52)))
eye = target + Vector((_m.cos(el) * _m.cos(az), _m.cos(el) * _m.sin(az), _m.sin(el))) * dist
rot = (target - eye).to_track_quat('-Z', 'Y')
win = bpy.context.window_manager.windows[0]
for area in win.screen.areas:
    if area.type == 'VIEW_3D':
        r3 = area.spaces.active.region_3d
        r3.view_rotation = rot; r3.view_location = target; r3.view_distance = dist; r3.view_perspective = 'PERSP'
        break
print(json.dumps({'az': round(_m.degrees(az)), 'el': round(_m.degrees(el)), 'dist': dist, 'frame': scene.frame_current}))
