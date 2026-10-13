"""THE SKY FLEET asteroid review (docs/192 s10): every rock under the studio's inspection light (moon key + cool rim +
violet city fill), three angles each, plus one sheet of all five at the size a player sees them. Eevee previews for
judging SHAPE and DETAIL, not the in-game look.

Writes art/sky_ships/review/rock_<n>_<view>.png and art/sky_ships/review/rocks_lineup.png.
"""
import bpy, sys, importlib, pathlib, math
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib
importlib.reload(sky_lib)

scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = 1200, 900
scene.render.image_settings.file_format = 'PNG'
try:
    scene.eevee.taa_render_samples = 32
except Exception:
    pass
out = sky_lib.ART / 'review'
out.mkdir(parents=True, exist_ok=True)
cam = bpy.data.objects.get('REVIEW CAM')
if cam is None:
    cam = bpy.data.objects.new('REVIEW CAM', bpy.data.cameras.new('REVIEW CAM'))
    scene.collection.objects.link(cam)
    cam['sky_group'] = 'studio'
cam.data.lens_unit = 'FOV'
cam.data.clip_start = 20
cam.data.clip_end = 2.0e6
scene.camera = cam

rocks = {c['rock']: c for c in bpy.data.collections if c.name.startswith('ROCK ')}
ships = [c for c in bpy.data.collections if c.name.startswith('SHIP ')]
for c in ships:
    c.hide_render = True
VIEWS = [('a', (0.55, -0.7, 0.45), 34), ('b', (-0.7, -0.4, -0.55), 34), ('c', (0.1, 0.95, 0.3), 34)]
done = []
for key, col in sorted(rocks.items()):
    for k2, c2 in rocks.items():
        c2.hide_render = k2 != key
    centre = Vector(col['offset'])
    rad = max(v.co.length for o in col.objects for v in o.data.vertices)
    for view, d, fov in VIEWS:
        dv = Vector(d).normalized()
        cam.data.angle = math.radians(fov)
        dist = rad * 1.25 / math.tan(math.radians(fov) / 2)
        cam.location = centre + dv * dist
        cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(out / ('rock_%s_%s.png' % (key, view)))
        bpy.ops.render.render(write_still=True)
        done.append('rock_%s_%s.png' % (key, view))
# the lineup: all five side by side
for c2 in rocks.values():
    c2.hide_render = False
xs = [Vector(c['offset']) for c in rocks.values()]
mid = sum(xs, Vector()) / len(xs)
cam.data.angle = math.radians(40)
cam.location = mid + Vector((0, -9000, 1800))
cam.rotation_euler = (mid - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.resolution_x, scene.render.resolution_y = 1800, 700
scene.render.filepath = str(out / 'rocks_lineup.png')
bpy.ops.render.render(write_still=True)
done.append('rocks_lineup.png')
for c in ships:
    c.hide_render = False
print('SKY_ROCK_REVIEW', done)
