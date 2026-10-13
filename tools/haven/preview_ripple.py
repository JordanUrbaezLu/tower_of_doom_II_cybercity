"""THE ROUNDED RIPPLE review (docs/202 v2): the crossing effects on the real dome, before the native build.

Opens art/haven/review/haven_review.blend (tools/haven/preview.py: the real emitted hall faces, the shipping dome,
the floor's lights) and places the crossing ripple exactly where the GENERATED effects put it: it reads
share/raw/fx/tod/haven/fx_tod_haven_cross.efx and fx_tod_haven_push.efx (each `ripple_ring_N` element's plane x,
radius, bead count, delay, life, size and alpha curves) and lays the beads on a crossing point the way
_tod_haven.gsc does (field_point 48 / 40 up, the carrier's X along the outward normal). Each bead is drawn as a small
emissive sphere at the bead's alpha at time t; bead angles are seeded-random like the engine's cylinder spawn.

What is NOT real: BO3's sprite blending, bloom and exposure, the streak sparks and the crackle (left out), and the
sprites themselves (soft billboards in game). It answers one question: does the ripple lie on the dome's curve?

    "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe" --background --factory-startup --python tools/haven/preview_ripple.py

Writes art/haven/review/ripple_<view>_<ms>.png + ripple.json. Held while the game or any native compiler runs.
"""
from pathlib import Path
import bpy, json, sys, math, random, hashlib
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/haven/review'
sys.path.insert(0, str(ROOT / 'tools/dealer_presence'))
from process_guard import check
check()
sys.path.insert(0, str(ROOT / 'tools/sky_ships'))
import efx_lib as E

SCALE = .0254
scene_data = json.loads((OUT / 'scene.json').read_text())
CX, CY, Z = scene_data['dome']['centre']
SR, ZC = scene_data['dome']['S'], scene_data['dome']['C']

bpy.ops.wm.open_mainfile(filepath=str(OUT / 'haven_review.blend'))
sc = bpy.context.scene
cam = sc.camera


def curve_at(rows, t):
    t = min(max(t, 0.0), 1.0)
    for (t0, v0), (t1, v1) in zip(rows, rows[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * ((t - t0) / max(t1 - t0, 1e-6))
    return rows[-1][1]


def rings_of(fx_name):
    fx = E.parse((ROOT / 'share/raw/fx/tod/haven' / (fx_name + '.efx')).read_text())
    out = []
    for e in fx.elements:
        if not e.name.startswith('ripple_ring'):
            continue
        size = e.graph('sizeGraph0'); alpha = e.graph('alphaGraph'); color = e.graph('colorGraph')
        out.append({'name': e.name, 'x': e.nums('spawnOrgX')[0], 'r': e.nums('spawnOffsetRadius')[0],
                    'n': int(e.nums('spawnOneShot')[0]), 'delay': e.nums('spawnDelayMsec')[0], 'life': e.nums('lifeSpanMsec')[0],
                    'size': (size.scale, [tuple(r) for r in size.curves[0]]), 'alpha': [tuple(r) for r in alpha.curves[0]],
                    'rgb': [tuple(r) for r in color.curves[0]]})
    return out


def crossing(az_deg, up):
    """_tod_haven.gsc field_point(): the field point `up` over the floor toward azimuth az, and its outward normal."""
    d = Vector((math.cos(math.radians(az_deg)), math.sin(math.radians(az_deg)), 0))
    dz = up - ZC
    r = math.sqrt(max(SR * SR - dz * dz, 1))
    p = Vector((CX, CY, Z + up)) + d * r
    n = (p - Vector((CX, CY, Z + ZC))).normalized()
    y = Vector((0, 0, 1)).cross(n).normalized()
    return p, n, y, n.cross(y)


bead_mat = {}


def material(rgb, strength):
    key = (tuple(round(c, 3) for c in rgb), round(strength, 2))
    if key not in bead_mat:
        m = bpy.data.materials.new('ripple bead %s' % (key,)); m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear()
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*rgb, 1); em.inputs['Strength'].default_value = strength
        o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], o.inputs[0])
        bead_mat[key] = m
    return bead_mat[key]


def place(rings, p, n, y, z, t_ms, seed, tag):
    coll = bpy.data.collections.new('ripple ' + tag); sc.collection.children.link(coll)
    rnd = random.Random(seed)
    lit = 0
    for ring in rings:
        u = (t_ms - ring['delay']) / ring['life']
        angles = [rnd.uniform(0, 2 * math.pi) for _ in range(ring['n'])]   # the engine's cylinder spawn: random yaw
        if not 0 <= u <= 1:
            continue
        a = curve_at(ring['alpha'], u)
        if a <= 0.02:
            continue
        size = ring['size'][0] * curve_at(ring['size'][1], u)
        rgb = tuple(curve_at([(r[0], r[1 + k]) for r in ring['rgb']], u) for k in range(3))
        for b in angles:
            pos = p + n * ring['x'] + (y * math.cos(b) + z * math.sin(b)) * ring['r']
            bpy.ops.mesh.primitive_uv_sphere_add(radius=size * 0.25 * SCALE, segments=12, ring_count=6, location=pos * SCALE)
            ob = bpy.context.active_object
            ob.data.materials.append(material(rgb, 8 * a))
            for c in ob.users_collection: c.objects.unlink(ob)
            coll.objects.link(ob)
            lit += 1
    return coll, lit


def look(eye, target, lens):
    cam.data.lens = lens
    cam.location = Vector(eye) * SCALE
    cam.rotation_euler = (Vector(target) * SCALE - cam.location).to_track_quat('-Z', 'Y').to_euler()


cross_rings, push_rings = rings_of('fx_tod_haven_cross'), rings_of('fx_tod_haven_push')
SHOTS = [
    # (file stem, rings, crossing azimuth, height, camera eye, lens, times ms)
    # a crossing on the field's NORTH side (the open side: the perk pads stand back in the north loggia)
    ('front', cross_rings, 90, 48, (32, 410, Z + 60), 20, (120, 260)),           # from the north loggia, face on
    ('graze', cross_rings, 90, 48, (-150, 330, Z + 70), 24, (120, 260)),         # from the north-west: along the curve
    ('inside', cross_rings, 90, 48, (32, 120, Z + 60), 16, (120, 260)),          # inside the field, looking at the crossing
    ('push', push_rings, 110, 40, (-60, 405, Z + 50), 22, (110,)),               # a zombie forcing in, north-north-west
]
renders = {}
for stem, rings, az, up, eye, lens, times in SHOTS:
    p, n, y, z = crossing(az, up)
    for t in times:
        coll, lit = place(rings, p, n, y, z, t, seed=7 + az, tag='%s %d' % (stem, t))
        look(eye, tuple(p), lens)
        name = 'ripple_%s_%d.png' % (stem, t)
        sc.render.filepath = str(OUT / name); check(); bpy.ops.render.render(write_still=True)
        renders[name] = {'beads': lit, 'sha256': hashlib.sha256((OUT / name).read_bytes()).hexdigest()}
        for ob in list(coll.objects): bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(coll)

receipt = {'schema': 1, 'engine': 'Blender EEVEE (4.2)', 'scene': 'haven_review.blend (tools/haven/preview.py)',
           'cross_efx_sha256': hashlib.sha256((ROOT / 'share/raw/fx/tod/haven/fx_tod_haven_cross.efx').read_bytes()).hexdigest(),
           'push_efx_sha256': hashlib.sha256((ROOT / 'share/raw/fx/tod/haven/fx_tod_haven_push.efx').read_bytes()).hexdigest(),
           'limit': 'beads drawn as emissive spheres at their alpha; no sprite blending, bloom, exposure, streaks or crackle',
           'images': renders}
(OUT / 'ripple.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('RIPPLE_PREVIEW_COMPLETE', json.dumps({k: v['beads'] for k, v in renders.items()}), flush=True)
