"""THE SKY FLEET - the ASTEROIDS (docs/192 s10; user 2026-09-29: "flying asteroids going around space ... more subtle than
the spaceships ... higher up in the atmosphere. But still visible, so players can see the movement ... focus on quality
and detail of each").

Five rocks, each built from a dense icosphere (40,962 vertices) shaped by code and reduced to a game mesh:
  1 BOULDER   a potato-shaped stony asteroid: 30 craters on a power law (bowl + raised rim), lumps, grain
  2 SHARD     an elongated fragment broken off something bigger: five flat FRACTURE faces with sharp edges, few craters
  3 VEINED    a lumpy rock split by GLOWING CRYSTAL VEINS (magenta; variant _b cyan) with crystal clusters
              breaking the surface - the cyber rock
  4 SLAB      a tumbling broken plate, cratered faces, one glowing SEAM across it (cyan; variant _b amber)
  5 RUBBLE    a rubble pile: a contact pair and two pebbles fused into one tumbling clump
Every rock is centred on its origin (they tumble about it) and about 1,000 units across; the director draws them at the
angular size it wants (the size in units never shows). Materials: rock / rock2 (lit, a faint self-light so the dark
side never goes black against the night), the neon glow materials for veins and crystals.

Run through Blender MCP AFTER 01_studio.py (it builds the rock materials here if they are missing):
  <mcp python> tools/sky_ships/mcp_call.py tools/sky_ships/10_asteroids.py
"""
import bpy, bmesh, sys, importlib, pathlib, json, math
import numpy as np
from mathutils import Vector, noise, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib, detail_lib
importlib.reload(sky_lib)
importlib.reload(detail_lib)
from sky_lib import mat, load_image, make_material, EMIT, frame
from detail_lib import cyl, basis

STUDIO_X = 16000                        # where the rocks stand in the studio (beside the fleet)

# ---- materials (the textures come from make_textures.py; before its first run, from rock_textures.py's preview) ----------
STAGE_TEX = sky_lib.ROOT / 'tmp/sky_ships/tex_stage'


def rock_image(name):
    if (sky_lib.TEX / (name + '.png')).exists():
        return load_image(name)
    im = bpy.data.images.get(name)
    if im is None:
        im = bpy.data.images.load(str(STAGE_TEX / (name + '.png')))
        im.name = name
    if name.endswith('_n') or name.endswith('_g'):
        im.colorspace_settings.name = 'Non-Color'
    return im


for name in ('i_tod_sky_rock_n', 'i_tod_sky_rock_g', 'i_tod_sky_rock_s'):
    rock_image(name)
make_material('rock', rock_image('i_tod_sky_rock_c'), 'rock', emit=EMIT['rock'], rough=0.85, metal=0.0,
              maps=dict(n='i_tod_sky_rock_n', g='i_tod_sky_rock_g', s='i_tod_sky_rock_s'), viewport_rgb=(0.1, 0.095, 0.09),
              surface='rock')
make_material('rock2', rock_image('i_tod_sky_rock2_c'), 'rock', emit=EMIT['rock'], rough=0.85, metal=0.0,
              maps=dict(n='i_tod_sky_rock_n', g='i_tod_sky_rock_g', s='i_tod_sky_rock_s'), viewport_rgb=(0.13, 0.1, 0.075),
              surface='rock')
for ch in ('n','g','s'):
    load_image('i_tod_sky_mineral_'+ch)
for color in ('magenta','cyan','amber'):
    make_material('mineral_'+color,load_image('i_tod_sky_mineral_'+color+'_c'),'glow',emit=EMIT['neon'],rough=.45,
                  maps={ch:'i_tod_sky_mineral_'+ch for ch in ('n','g','s')},surface='rock')


def rock_collection(key, variants, veins):
    name = 'ROCK ' + key
    old = bpy.data.collections.get(name)
    if old is not None:
        for ob in list(old.objects):
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
        bpy.data.collections.remove(old)
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    col['rock'] = key
    col['variants'] = json.dumps(variants)
    col['veins'] = 1 if veins else 0
    col['offset'] = [STUDIO_X + 2600 * (int(key) - 1), 0, 0]
    return col


def fib_dirs(n, rng):
    """n well-spread random unit vectors (jittered Fibonacci sphere)."""
    out = []
    for i in range(n):
        z = 1 - 2 * (i + rng.uniform(0.2, 0.8)) / n
        a = i * 2.399963 + rng.uniform(-0.4, 0.4)
        r = math.sqrt(max(0.0, 1 - z * z))
        out.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    rng.shuffle(out)
    return out


def rock_mesh(R, rng, shape=(1, 1, 1), craters=(24, 0.05, 0.32), lumps=0.2, fine=0.02, cuts=0, cut_depth=0.15,
              twist=0.0, subdiv=6):
    """A dense bmesh rock: an icosphere displaced by lumps + power-law craters (bowl and rim) + grain, stretched by
    `shape`, then optionally cut by flat fracture planes."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    n_cr, a_min, a_max = craters
    cdirs = fib_dirs(n_cr, rng)
    crs = []
    for i, c in enumerate(cdirs):
        u = rng.uniform(0, 1) ** 2.4                               # many small, few big
        a = a_min + (a_max - a_min) * u
        crs.append((c, a, 0.85 * a * rng.uniform(0.75, 1.15), 0.3 * a * rng.uniform(0.6, 1.2)))
    off = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    for v in bm.verts:
        d = v.co.normalized()
        h = lumps * noise.fractal(d * 1.3 + off, 0.55, 2.1, 3, noise_basis='PERLIN_ORIGINAL')
        h += 0.35 * lumps * noise.noise(d * 3.1 + off * 0.5)
        for c, a, depth, rim in crs:
            cosang = max(-1.0, min(1.0, d.dot(c)))
            th = math.acos(cosang)
            if th > 1.6 * a:
                continue
            x = th / a
            if x < 1:
                h += depth * (x * x - 1)                          # the bowl
            h += rim * math.exp(-((x - 1.0) / 0.22) ** 2)         # the raised rim
        h += fine * noise.fractal(d * 9.0 + off, 0.6, 2.2, 4, noise_basis='VORONOI_F1')
        h += 0.5 * fine * noise.noise(d * 23.0 + off)
        p = d * (1.0 + h)
        if twist:
            ang = twist * p.z
            p = Vector((p.x * math.cos(ang) - p.y * math.sin(ang), p.x * math.sin(ang) + p.y * math.cos(ang), p.z))
        v.co = Vector((p.x * shape[0], p.y * shape[1], p.z * shape[2])) * R
    # FRACTURES: flat breaks with sharp edges (a shard broken off a bigger body)
    planes = []
    for d in fib_dirs(cuts, rng) if cuts else []:
        far = max(v.co.dot(d) for v in bm.verts)
        planes.append((d, far * (1 - cut_depth * rng.uniform(0.7, 1.3))))
    for v in bm.verts:
        for d, o in planes:
            s = v.co.dot(d)
            if s > o:
                v.co = v.co - d * (s - o) + d * (0.004 * R * noise.noise(v.co * (6.0 / R)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm, planes


def finish_rock(col, name, bm, material, tris, box_uv, sharp_deg=48, group='rock'):
    """bmesh -> object: decimate to `tris`, box-mapped UVs, smooth with sharp creases."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    if len(me.polygons) > tris:
        mod = ob.modifiers.new('decimate', 'DECIMATE')
        mod.ratio = tris / len(me.polygons)
        mod.use_collapse_triangulate = True
        dg = bpy.context.evaluated_depsgraph_get()
        eval_ob = ob.evaluated_get(dg)
        new = bpy.data.meshes.new_from_object(eval_ob)
        ob.modifiers.clear()
        old = ob.data
        ob.data = new
        bpy.data.meshes.remove(old)
        ob.data.name = name
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co[a] / box_uv, loop.vert.co[b] / box_uv)
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    me.set_sharp_from_angle(angle=math.radians(sharp_deg))
    me.materials.clear()
    me.materials.append(material)
    ob.location = Vector(col['offset'])
    ob['sky_group'] = group
    ob['lod1'] = False
    return ob


def surface_point(bvh, d):
    """The rock surface along direction d from its centre (ray cast outward from inside)."""
    hit = bvh.ray_cast(Vector((0, 0, 0)), d.normalized())
    if hit[0] is None:
        hit = bvh.ray_cast(d.normalized() * 1e5, -d.normalized())
    return hit[0], hit[1]


def vein_paths(bvh, rng, n, steps, step_len, R, turn=0.28):
    """Crack paths walked over the surface: a start direction, a heading that drifts, a few forks."""
    paths = []
    for _ in range(n):
        d = Vector((rng.normal(), rng.normal(), rng.normal())).normalized()
        t = d.orthogonal().normalized()
        t.rotate(Matrix.Rotation(rng.uniform(0, 2 * math.pi), 3, d))
        pts = []
        for s in range(steps):
            p, nrm = surface_point(bvh, d)
            if p is None:
                break
            pts.append((p, nrm))
            ang = rng.normal(0, turn)
            t.rotate(Matrix.Rotation(ang, 3, d))
            d = (d + t * (step_len / R)).normalized()
            t = (t - d * t.dot(d)).normalized()
        if len(pts) > 3:
            paths.append(pts)
    return paths


def glow_tube(bm, pts, r0, r1, sunk):
    """A glowing crack: a tapering tube along the surface points, sunk a little so it reads as a fissure."""
    rings = []
    n = len(pts)
    for i, (p, nrm) in enumerate(pts):
        a = pts[min(i + 1, n - 1)][0] - pts[max(i - 1, 0)][0]
        if a.length < 1e-6:
            a = Vector((1, 0, 0))
        a.normalize()
        side = a.cross(nrm).normalized()
        up = side.cross(a).normalized()
        taper = math.sin(math.pi * (i + 0.5) / n) ** 0.6
        r = r0 + (r1 - r0) * taper
        c = p - nrm * sunk
        ring = []
        for k in range(6):
            ang = 2 * math.pi * k / 6
            ring.append(bm.verts.new(c + (side * math.cos(ang) + up * math.sin(ang)) * r))
        rings.append(ring)
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for k in range(6):
            j = (k + 1) % 6
            bm.faces.new([a_[k], a_[j], b_[j], b_[k]])
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def crystal(bm, p, nrm, length, radius, rng):
    """A hexagonal crystal breaking out of the surface, tipped with a point."""
    tilt = Vector((rng.normal(), rng.normal(), rng.normal())) * 0.35
    ax = (nrm + tilt).normalized()
    side = ax.orthogonal().normalized()
    up = ax.cross(side).normalized()
    base = p - ax * length * 0.35
    top = p + ax * length * 0.75
    tip = p + ax * length
    b_ring, t_ring = [], []
    for k in range(6):
        ang = 2 * math.pi * k / 6 + rng.uniform(0, 0.3)
        o = side * math.cos(ang) + up * math.sin(ang)
        b_ring.append(bm.verts.new(base + o * radius))
        t_ring.append(bm.verts.new(top + o * radius * 0.85))
    tv = bm.verts.new(tip)
    for k in range(6):
        j = (k + 1) % 6
        bm.faces.new([b_ring[k], b_ring[j], t_ring[j], t_ring[k]])
        bm.faces.new([t_ring[k], t_ring[j], tv])
    bm.faces.new(list(reversed(b_ring)))


def veins_and_crystals(col, rock_ob, rng, glow_mat, n_veins, steps, n_crystals, R, name, width=(4, 14), turn=0.28):
    me = rock_ob.data
    bm0 = bmesh.new()
    bm0.from_mesh(me)
    bvh = BVHTree.FromBMesh(bm0)
    bm0.free()
    bm = bmesh.new()
    for pts in vein_paths(bvh, rng, n_veins, steps, 0.07 * R, R, turn):
        glow_tube(bm, pts, width[0], width[1], sunk=0.2 * width[1])
    for _ in range(n_crystals):
        d = Vector((rng.normal(), rng.normal(), rng.normal())).normalized()
        p, nrm = surface_point(bvh, d)
        if p is None:
            continue
        cluster = rng.integers(2, 5)
        for c in range(cluster):
            j = Vector((rng.normal(), rng.normal(), rng.normal())) * 0.035 * R
            q, nq = surface_point(bvh, (p + j).normalized())
            if q is None:
                continue
            crystal(bm, q, nq, rng.uniform(0.12, 0.26) * R, rng.uniform(0.03, 0.055) * R, rng)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ve = bpy.data.meshes.new(name)
    bm.to_mesh(ve)
    bm.free()
    for f in ve.polygons:
        f.use_smooth = False
    ve.materials.append(glow_mat)
    uv=ve.uv_layers.new(name='UVMap')
    for f in ve.polygons:
        axis=max(range(3),key=lambda i:abs(f.normal[i]))
        a,b=[(1,2),(0,2),(0,1)][axis]
        for li in f.loop_indices:
            co=ve.vertices[ve.loops[li].vertex_index].co
            uv.data[li].uv=(co[a]/240,co[b]/240)
    ob = bpy.data.objects.new(name, ve)
    col.objects.link(ob)
    ob.location = Vector(col['offset'])
    ob['sky_group'] = 'vein'
    ob['lod1'] = False
    return ob


built = {}

# 1 BOULDER --------------------------------------------------------------------------------------------------------------
rng = np.random.default_rng(1101)
col = rock_collection('1', [['', []]], False)
bm, _ = rock_mesh(470, rng, shape=(1.25, 1.0, 0.86), craters=(32, 0.045, 0.36), lumps=0.2, fine=0.022)
built['1'] = finish_rock(col, 'rock 1 body', bm, mat('rock'), 9000, 520, sharp_deg=62)

# 2 SHARD ----------------------------------------------------------------------------------------------------------------
rng = np.random.default_rng(2202)
col = rock_collection('2', [['', []]], False)
bm, planes = rock_mesh(300, rng, shape=(2.2, 0.95, 0.8), craters=(12, 0.05, 0.22), lumps=0.14, fine=0.018, cuts=5,
                       cut_depth=0.2, twist=0.25)
built['2'] = finish_rock(col, 'rock 2 body', bm, mat('rock2'), 6500, 480, sharp_deg=34)

# 3 VEINED (the cyber rock) --------------------------------------------------------------------------------------------------
rng = np.random.default_rng(3303)
col = rock_collection('3', [['', []], ['_b', [['mineral_magenta', 'mineral_cyan']]]], True)
bm, _ = rock_mesh(430, rng, shape=(1.1, 1.05, 0.95), craters=(18, 0.05, 0.28), lumps=0.26, fine=0.024, cuts=2, cut_depth=0.1)
body = finish_rock(col, 'rock 3 body', bm, mat('rock'), 8000, 520, sharp_deg=62)
veins_and_crystals(col, body, rng, mat('mineral_magenta'), n_veins=7, steps=26, n_crystals=4, R=430, name='rock 3 veins')
built['3'] = body

# 4 SLAB with a glowing seam -------------------------------------------------------------------------------------------------
rng = np.random.default_rng(4404)
col = rock_collection('4', [['', []], ['_b', [['mineral_cyan', 'mineral_amber']]]], True)
bm, _ = rock_mesh(440, rng, shape=(1.3, 1.1, 0.42), craters=(22, 0.04, 0.26), lumps=0.16, fine=0.02, cuts=2, cut_depth=0.12)
body = finish_rock(col, 'rock 4 body', bm, mat('rock2'), 7000, 480, sharp_deg=40)
veins_and_crystals(col, body, rng, mat('mineral_cyan'), n_veins=1, steps=70, n_crystals=3, R=440, name='rock 4 seam', width=(6, 18),
                   turn=0.12)
built['4'] = body

# 5 RUBBLE: a contact pair + two pebbles, fused ------------------------------------------------------------------------------
rng = np.random.default_rng(5505)
col = rock_collection('5', [['', []]], False)
parts = [((-150, 0, 0), 260, (1.1, 0.95, 0.9)), ((170, 40, 30), 210, (1.0, 1.1, 0.85)), ((30, 260, -90), 110, (1.2, 0.9, 0.9)),
         ((-80, -230, 110), 90, (1, 1, 1))]
for i, (c, r, shp) in enumerate(parts):
    bm, _ = rock_mesh(r, rng, shape=shp, craters=(10, 0.06, 0.3), lumps=0.22, fine=0.025, subdiv=5)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(c))
    ob = finish_rock(col, 'rock 5 part %d' % i, bm, mat('rock' if i % 2 == 0 else 'rock2'), [1900, 1500, 700, 600][i], 420)
    if i == 0:
        built['5'] = ob

# ---- report --------------------------------------------------------------------------------------------------------------
report = {}
for key in built:
    col = bpy.data.collections['ROCK ' + key]
    objs = [o for o in col.objects]
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    rad = max(v.co.length for o in objs for v in o.data.vertices)
    report[key] = dict(parts=len(objs), tris=tris, radius=round(rad))
print('SKY_ROCKS_BUILT', json.dumps(report))
