"""Render THE SKY FLEET review images (docs/192): every ship against OUR sky from the in-game framing
(the PLAYER VIEW camera: below and to the side, hfov 80.7), plus the fleet line-up. Eevee + the studio's
glare = a preview, NOT a native render: the game's lighting, bloom and exposure decide the final look."""
import bpy, sys, importlib, pathlib, math
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib
importlib.reload(sky_lib)
scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.render.image_settings.file_format = 'PNG'
try:
    scene.eevee.taa_render_samples = 48
except Exception:
    pass
out = sky_lib.ART / 'review'
out.mkdir(parents=True, exist_ok=True)
cols = {c['ship']: c for c in bpy.data.collections if c.name.startswith('SHIP ')}
def show_only(keys):
    for k, c in cols.items():
        c.hide_render = k not in keys
dist = {'dreadnought': 12000, 'hauler': 7500, 'gunship': 4200, 'fighter': 1600}
done = []
for k, c in cols.items():
    show_only([k])
    sky_lib.aim_camera(Vector(c['offset']), dist[k])
    scene.render.filepath = str(out / ('ship_' + k + '.png'))
    bpy.ops.render.render(write_still=True)
    done.append(scene.render.filepath)
show_only(list(cols))
sky_lib.aim_camera(Vector((0, 0, 900)), 16000, rise_deg=24, side=-0.5)
scene.render.filepath = str(out / 'fleet_lineup.png')
bpy.ops.render.render(write_still=True)
done.append(scene.render.filepath)
print('SKY_REVIEW_RENDERS', done)
