"""THE SKY FLEET v2 detail review (docs/192 s8): render every built ship from several angles under INSPECTION light
(a stronger moon key + a cool rim) so the modelling can be judged, plus close-ups of the busiest areas. These are
Eevee previews for judging SHAPE and DETAIL, not the in-game look (the native lighting, bloom and exposure decide
that; 07_review_renders.py / 98_backdrop.py give the in-game framing against our real sky).

Writes art/sky_ships/review/v2_<ship>_<view>.png. tmp/sky_ships/review_only.txt ('hauler,gunship') limits the ships.
"""
import bpy, sys, importlib, pathlib, math, os
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib
importlib.reload(sky_lib)

scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.render.image_settings.file_format = 'PNG'
try:
    scene.eevee.taa_render_samples = 32
except Exception:
    pass
out = sky_lib.ART / 'review'
out.mkdir(parents=True, exist_ok=True)

# inspection light (kept after the run so the studio viewport shows the detail too)
key = bpy.data.objects.get('Moonlight key')
if key is not None:
    key.data.energy = 4.5
rim = bpy.data.objects.get('Inspection rim')
if rim is None:
    d = bpy.data.lights.new('Inspection rim', 'SUN')
    rim = bpy.data.objects.new('Inspection rim', d)
    scene.collection.objects.link(rim)
    rim['sky_group'] = 'studio'
rim.data.energy = 2.0
rim.data.color = (0.55, 0.75, 1.0)
rim.rotation_euler = (math.radians(-60), 0, math.radians(-150))

cam = bpy.data.objects.get('REVIEW CAM')
if cam is None:
    cam = bpy.data.objects.new('REVIEW CAM', bpy.data.cameras.new('REVIEW CAM'))
    scene.collection.objects.link(cam)
    cam['sky_group'] = 'studio'
cam.data.lens_unit = 'FOV'
cam.data.clip_start = 20
cam.data.clip_end = 2.0e6
scene.camera = cam

cols = {c['ship']: c for c in bpy.data.collections if c.name.startswith('SHIP ')}
_only_file = sky_lib.ROOT / 'tmp/sky_ships/review_only.txt'          # the MCP call cannot pass arguments
only = [s for s in (os.environ.get('SKY_REVIEW_ONLY', '') or (_only_file.read_text().strip() if _only_file.exists() else '')).split(',') if s]


def bounds(c):
    lo = Vector((1e9, 1e9, 1e9))
    hi = -lo
    for o in c.objects:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


# (view, direction from target to camera, fov deg, target in SHIP space or None = centre, size factor)
VIEWS = [('below', (0.35, -0.55, -0.75), 50, None, 1.0), ('side', (0.0, -1.0, -0.22), 42, None, 1.0),
         ('top', (-0.45, -0.6, 0.66), 45, None, 1.0)]
CLOSE = {'dreadnought': [('close_trench', (0.2, -0.75, -0.62), 26, (600, -1300, -250), 0.36),
                         ('close_bow', (0.75, -0.55, 0.36), 28, (3300, 0, 250), 0.34),
                         ('close_citadel', (0.35, -0.65, 0.55), 28, (-200, 0, 600), 0.42),
                         ('close_stern', (-0.8, -0.45, 0.2), 32, (-4400, -700, 300), 0.45),
                         ('close_belly', (0.25, -0.5, -0.8), 30, (500, 0, -450), 0.45)],
         'hauler': [('close_mid', (0.3, -0.7, -0.35), 30, (0, 0, 0), 0.5), ('close_stern', (-0.8, -0.5, 0.2), 34, (-2800, 0, 0), 0.55)],
         'gunship': [('close_nose', (0.7, -0.6, -0.3), 34, (700, 0, 0), 0.6)],
         'fighter': []}
done = []
for k, c in cols.items():
    if only and k not in only:
        continue
    for kk, cc in cols.items():
        cc.hide_render = kk != k
    lo, hi = bounds(c)
    size = (hi - lo).length
    ctr = (lo + hi) / 2
    off = Vector(c['offset'])
    for view, d, fov, tgt, frac in VIEWS + CLOSE.get(k, []):
        cam.data.angle = math.radians(fov)
        target = ctr if tgt is None else off + Vector(tgt)
        dist = size * frac * 0.55 / math.tan(math.radians(fov) / 2)
        dv = Vector(d).normalized()
        cam.location = target + dv * dist
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(out / ('v2_' + k + '_' + view + '.png'))
        bpy.ops.render.render(write_still=True)
        done.append(pathlib.Path(scene.render.filepath).name)
for cc in cols.values():
    cc.hide_render = False
print('SKY_DETAIL_REVIEW', done)
