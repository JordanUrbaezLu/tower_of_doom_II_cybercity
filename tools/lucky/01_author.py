"""Execute through Blender MCP (tools/lucky/mcp_call.py). Author/export THE LUCKY SOURCES' models (docs/197), then
save the studio (art/lucky/lucky.blend).

User 2026-09-29: "Build this, lucky meteor and lucky die drop. It should be a lucky clover model and act just like
regular drops that have the white glow" + "This model should be consistent with other drops like pap and perk bottle
and zombie blood so it seems like it comes from this game" + "why would you make it gold. The others arent gold".

Two native models, one bone each (tag_origin, identity), pivot = the model's visual centre:
  tod_luck_clover   THE POWER-UP: an upright four-leaf clover (~19 x 20 units, 4 deep - the PaP drop is 17 x 22, Zombie
                    Blood 10 x 18): one solid cast piece - pillowy heart leaves, raised veins, a domed hub, a curled stem -
                    in the drops' OWN stock material mtl_x2icon_gold (the PaP drop and Zombie Blood both wear it), so it
                    is lit exactly like them in game. Three LODs. Stock powerup_setup spawns it at the drop point + 40
                    and spins/bobs it; the Lucky Meteor's falling fragment is the same model.
  tod_luck_meteor   THE LUCKY METEOR (sky scenery, not a drop): a dark basalt rock (~METEOR_R radius) split by glowing gold
                    cracks, with emerald crystals breaking out of it. ONE LOD: only ever seen 3,500-6,500 units away.
                    Its lumps must stay inside _tod_lucky.gsc TOD_METEOR_HIT_R (tools/lucky/verify_native.py).
The previews include a LINE-UP: the clover between the real PaP drop and Zombie Blood models (read from their XMODEL_BIN,
preview only, never exported), all three in the same preview material and light - the "which one doesn't belong" test.
Units: BO3 inches (1 Blender unit). Front = -Y. source_data/tod_lucky.gdt is GENERATED here: never hand-edit.
"""
import bpy, bmesh, math, json, pathlib, sys, hashlib, random
import numpy as np
from mathutils import Vector, Matrix, noise
from mathutils.bvhtree import BVHTree
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
OUT = ROOT / 'art/lucky'; OUT.mkdir(parents=True, exist_ok=True)
EXP = ROOT / 'model_export/tod_lucky'; EXP.mkdir(parents=True, exist_ok=True)
TEX = EXP / '_images'; TEX.mkdir(exist_ok=True)

LEAF_LEN = 9.8        # the leaves' lobes reach this far from the hub
LEAF_LIFT = 0.8       # a leaf's point sits this far out (the hub covers the meeting)
LEAF_T = 2.6          # a leaf's thickness: chunky like the other drops (Zombie Blood is 4.5 deep), so the clover
                      # never thins to a line as it spins
LEAF_BEVEL = .8       # the big rounded edge: a cast, pillowy icon, not a cut-out
CUP = 0.011           # each leaf cups toward the viewer by CUP * (distance across)^2
CLEAN_EPS = 0.004     # a triangle with an edge under this is degenerate (the converter drops it): the exporter's backstop
LEAF_CUT = 2.0        # the leaf outline is clipped below this distance from the centre (inside the hub, radius 2.6)
LEAF_MIN_STEP = 0.06  # outline points closer than this to their neighbour are dropped before the prism is built
METEOR_R = 135       # the rock's base radius: its lumps reach ~1.25x this, which must stay inside _tod_lucky.gsc
                      # TOD_METEOR_HIT_R (a shot on the rock always counts) - tools/lucky/verify_native.py checks it
SEED = 20260929
random.seed(SEED)

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
for im in list(bpy.data.images):
    if im.name.startswith('i_tod_luck_'): bpy.data.images.remove(im)
for c in list(bpy.data.curves): bpy.data.curves.remove(c)
scene = bpy.context.scene; scene.name = 'The lucky sources - authored native assets'
scene.render.engine = 'CYCLES'; scene.cycles.samples = 32; scene.cycles.use_denoising = True
scene.render.resolution_x = 1000; scene.render.resolution_y = 1000; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.02, .025, .035, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .25

blocks = []; textures = {}; mats = {}; parts = []
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def block(name, kind, fields):
    blocks.append('\t"' + name + '" ( "' + kind + '.gdf" )\n\t{\n' + ''.join('\t\t"' + k + '" "' + str(v) + '"\n' for k, v in fields.items()) + '\t}\n')

def save_image(name, a, linear):
    n = a.shape[0]
    im = bpy.data.images.new(name, width=n, height=n, alpha=True)
    if linear: im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(a.astype(np.float32).ravel()); im.filepath_raw = str(TEX / (name + '.png')); im.file_format = 'PNG'; im.save(); im.pack()
    textures[name + '.png'] = sha(TEX / (name + '.png'))
    return im

def image_block(name, semantic, srgb):
    f = dict(baseImage='model_export/tod_lucky/_images/' + name + '.png', imageType='Texture', type='image', semantic=semantic, streamable=1,
             compressionMethod='compressed high color' if srgb else 'compressed')
    if srgb: f['coreSemantic'] = 'sRGB3chAlpha'
    block(name, 'image', f)

# ONE shared flat normal map (the detail is geometry + emission; a flat map has no green-channel convention to get wrong)
FLAT_N = 'i_tod_luck_flat_n'
a = np.ones((64, 64, 4)); a[:, :, 0] = .5; a[:, :, 1] = .5; a[:, :, 2] = 1
save_image(FLAT_N, a, True); image_block(FLAT_N, 'normalMap', False)

def texture(label, color, rough, metal, seed, n, pattern):
    rng = np.random.default_rng(seed); y, x = np.mgrid[:n, :n]
    if pattern == 'brushed':
        v = rng.normal(0, .02, (n, n)) + np.sin(y * .61) * .012   # a faint brush, never visible banding
    elif pattern == 'basalt':
        v = rng.normal(0, .06, (n, n))
        for k in range(6):   # large soft blotches + pale speckles: the rock reads as stone at distance
            cx, cy, r = rng.integers(0, n, 2).tolist() + [int(rng.integers(n // 8, n // 3))]
            v += .10 * np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2.0 * r * r)))
        v += (rng.random((n, n)) > .985) * .35
    elif pattern == 'leaf':
        v = rng.normal(0, .025, (n, n)) + .05 * np.sin(x * .09 + np.sin(y * .05) * 2.0)
    else:
        v = rng.normal(0, .015, (n, n))
    out = {}
    c = np.ones((n, n, 4)); c[:, :, :3] = np.clip(np.array(color)[None, None, :] * (1 + v[:, :, None]), 0, 1)
    g = np.ones((n, n, 4)); g[:, :, :3] = np.clip(1 - rough + v[:, :, None] * .25, 0, 1)
    s = np.ones((n, n, 4)); s[:, :, :3] = (np.array(color) * .9 if metal else np.array((.04, .04, .04)))[None, None, :]
    for suffix, arr, lin in [('c', c, False), ('g', g, True), ('s', s, False)]:
        name = 'i_tod_luck_' + label + '_' + suffix
        out[suffix] = save_image(name, arr, lin)
        image_block(name, {'c': 'diffuseMap', 'g': 'glossMap', 's': 'specularMap'}[suffix], suffix != 'g')
    return out

def material(label, color, rough=.4, metal=0, emission=0.0, seed=7, n=256, pattern='plain', surface='plastic'):
    images = texture(label, color, rough, metal, seed, n, pattern)
    name = 'mtl_tod_luck_' + label; m = bpy.data.materials.new(name); m.use_nodes = True; m.use_fake_user = True
    bs = m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Metallic'].default_value = metal; bs.inputs['Roughness'].default_value = rough
    tex = m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = images['c']; m.node_tree.links.new(tex.outputs['Color'], bs.inputs['Base Color'])
    if emission:
        m.node_tree.links.new(tex.outputs['Color'], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = emission * .25
    fields = dict(surfaceType=surface, template='material.template', materialCategory='Geometry Advanced', materialType='lit_emissive_advanced_fullspec',
                  colorMap=images['c'].name, normalMap=FLAT_N, cosinePowerMap=images['g'].name, specColorMap=images['s'].name, specMapEnable=1,
                  specColorTint='1 1 1 1', colorMap00=images['c'].name, colorTint='1 1 1 1', colorTint1='1 1 1 1', scaleRGB=emission,
                  emissiveIncompetence=1, emissiveFalloff=0, normalHeightScale=1, glossRangeMin=0, glossRangeMax=8 if metal else 6,
                  specAmount=.6 if metal else .35, reflectionProbeAmount=.35 if metal else .15, textureAtlasRowCount=1, textureAtlasColumnCount=1,
                  usage='<not in editor>')
    block(name, 'material', fields); mats[label] = m; return m

# ---- the palette ----
# THE CLOVER IS A DROP, SO IT WEARS THE DROPS' OWN MATERIAL (user 2026-09-29: "This model should be consistent with
# other drops like pap and perk bottle and zombie blood so it seems like it comes from this game ... why would you make
# it gold. The others arent gold"). The PaP drop (ZoekMeMaar, skinOverride lambert1 -> mtl_x2icon_gold) and Zombie Blood
# (NSZ, a BO2 power-up port whose ONLY material is mtl_x2icon_gold) share one STOCK material: black colour map,
# reflections only (model_export/t5_props_zombie.gdt). The clover names it too, so it is lit exactly like them in game,
# whatever that looks like: consistent by construction. No GDT block: the material is stock (gdt.db). The Blender
# material below is a PREVIEW stand-in only (dark polished metal), never exported as a definition.
DROP_MTL = 'mtl_x2icon_gold'
m = bpy.data.materials.new(DROP_MTL); m.use_nodes = True; m.use_fake_user = True
bs = m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value = (0, 0, 0, 1)
bs.inputs['Metallic'].default_value = 1.0; bs.inputs['Roughness'].default_value = .22
mats['drop'] = m
# the meteor is sky scenery, not a drop: its own look (scaleRGB: distance eats emission in this map - the crown alarm
# lamps needed 36 -> 144 to read from ~10,000 units, sky_lib.py)
material('rock',    (.050, .044, .054), .88, 0, .8, seed=36, n=512, pattern='basalt', surface='rock')
material('rockvein', (1.0, .60, .12), .40, 0, 72,  seed=37, n=64)
material('crystal', (.14, 1.0, .48),  .10, 0, 36,  seed=38, n=64, surface='glass')

def finish(ob, name, mat, group, bevel=0, bevel_seg=2, smooth=True, uv=True):
    ob.name = name; ob['lucky_group'] = group
    ob.data.materials.clear(); ob.data.materials.append(mats[mat])
    bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    if bevel:
        mod = ob.modifiers.new('Edge bevel', 'BEVEL'); mod.width = bevel; mod.segments = bevel_seg; mod.limit_method = 'ANGLE'
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # (NO merge / dissolve here: at 0.004 it collapsed two leaves' whole faces into hollow rings - seen in the render. The
    # needles are prevented at their source instead: leaf_outline clips the heart's cusp.)
    for p in ob.data.polygons: p.use_smooth = smooth
    mod = ob.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL'); mod.keep_sharp = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    if uv:
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(island_margin=.03); bpy.ops.object.mode_set(mode='OBJECT')
    parts.append(ob); return ob

def mesh_object(name, verts, faces):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.validate()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    return ob

# =============================================================================
# THE CLOVER
# =============================================================================
def heart(n=64):
    # The classic heart curve, its point moved to the origin and its lobes toward +y (y 0 .. ~29, x -16 .. 16).
    pts = []
    for i in range(n):
        t = math.tau * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x, y + 17))
    return pts

def leaf_frame(ang):
    d = Vector((math.cos(ang), 0, math.sin(ang))); p = Vector((-math.sin(ang), 0, math.cos(ang)))
    return d, p

def leaf_point(u, v, ang, y):
    # (u across, v outward) in the leaf's plane -> world; the leaf cups toward -Y (the viewer) with distance across
    d, p = leaf_frame(ang)
    w = d * v + p * u
    return (w.x, y - CUP * u * u, w.z)

def leaf_outline(shrink):
    # The heart, scaled into place, with its RAZOR-SHARP POINT CUT OFF where the hub hides it (v < LEAF_CUT). The
    # classic curve's point is a cusp (x ~ t^3 against y ~ t^2): its last outline points sit a hair apart and the bevel
    # turned them into 72 needle triangles the converter dropped (FULL build 20:38). Clipped (one straight edge across the
    # leaf, inside the hub) and with near-duplicate neighbours removed, there is no needle left to make.
    s = (LEAF_LEN - LEAF_LIFT) / 29.0; cy = 14.5
    pts = [((x * shrink) * s, (cy + (y - cy) * shrink) * s + LEAF_LIFT) for x, y in heart(96)]
    out = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        if a[1] >= LEAF_CUT: out.append(a)
        if (a[1] >= LEAF_CUT) != (b[1] >= LEAF_CUT):
            t = (LEAF_CUT - a[1]) / (b[1] - a[1]); out.append((a[0] + (b[0] - a[0]) * t, LEAF_CUT))
    clean = [out[0]]
    for q in out[1:]:
        if math.hypot(q[0] - clean[-1][0], q[1] - clean[-1][1]) >= LEAF_MIN_STEP: clean.append(q)
    if math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) < LEAF_MIN_STEP: clean.pop()
    return clean

def leaf_prism(name, ang, thick, shrink, mat, bevel, bevel_seg=2):
    outline = leaf_outline(shrink)
    n = len(outline)
    verts = [leaf_point(u, v, ang, -thick / 2) for u, v in outline] + [leaf_point(u, v, ang, thick / 2) for u, v in outline]
    faces = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return finish(mesh_object(name, verts, faces), name, mat, 'clover', bevel, bevel_seg)

def ribbon(name, pts, width, height, ang, face_y, mat):
    # a thin raised vein following pts (leaf-plane (u, v) pairs) on the face at face_y (+/-); cupped like its leaf
    verts = []; faces = []
    sgn = 1 if face_y > 0 else -1
    for i, (u, v) in enumerate(pts):
        if i < len(pts) - 1: du, dv = pts[i + 1][0] - u, pts[i + 1][1] - v
        else: du, dv = u - pts[i - 1][0], v - pts[i - 1][1]
        l = math.hypot(du, dv) or 1; nu, nv = -dv / l, du / l
        taper = 1 - .75 * i / (len(pts) - 1)
        for k, (ou, ov) in enumerate([(nu * width * taper, nv * width * taper), (-nu * width * taper, -nv * width * taper)]):
            base = leaf_point(u + ou, v + ov, ang, face_y)
            verts.append(base); verts.append((base[0], base[1] + sgn * height, base[2]))
    m = len(pts)
    for i in range(m - 1):
        a0, a1, b0, b1 = 4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3
        c0, c1, d0, d1 = 4 * (i + 1), 4 * (i + 1) + 1, 4 * (i + 1) + 2, 4 * (i + 1) + 3
        faces += [(a1, c1, d1, b1), (a0, b0, d0, c0), (a1, a0, c0, c1), (b1, d1, d0, b0)]
    faces += [(0, 1, 3, 2), (4 * (m - 1), 4 * (m - 1) + 2, 4 * (m - 1) + 3, 4 * (m - 1) + 1)]
    return finish(mesh_object(name, verts, faces), name, mat, 'clover', 0, uv=True)

for i, deg in enumerate([45, 135, 225, 315]):
    ang = math.radians(deg)
    leaf_prism('clover leaf ' + str(i), ang, LEAF_T, 1.0, 'drop', LEAF_BEVEL, 3)
    face = LEAF_T / 2 - .05
    mid = [(0, LEAF_LIFT + 1.4 + (LEAF_LEN * .78 - LEAF_LIFT - 1.4) * k / 9) for k in range(10)]
    for side in (-1, 1):
        ribbon('clover vein %d %s' % (i, 'front' if side < 0 else 'back'), mid, .42, .42, ang, side * face, 'drop')
        for lobe in (-1, 1):   # a side vein into each lobe: raised ridges that catch the reflections
            sv = [(lobe * 3.4 * k / 5, LEAF_LEN * .38 + 2.8 * k / 5) for k in range(6)]
            ribbon('clover lobe vein %d %d %s' % (i, lobe, 'front' if side < 0 else 'back'), sv, .30, .32, ang, side * face, 'drop')

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=2.6, depth=LEAF_T + 1.4, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
finish(bpy.context.object, 'clover hub', 'drop', 'clover', .55, bevel_seg=3)

cu = bpy.data.curves.new('clover stem', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = .85; cu.bevel_resolution = 3; cu.resolution_u = 10
sp = cu.splines.new('BEZIER'); sp.bezier_points.add(3)
for bp, co in zip(sp.bezier_points, [(0, 0, -1.2), (.6, 0, -5.5), (2.4, 0, -9.6), (4.6, 0, -10.6)]):
    bp.co = co; bp.handle_left_type = bp.handle_right_type = 'AUTO'
so = bpy.data.objects.new('clover stem', cu); scene.collection.objects.link(so)
bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = so; so.select_set(True)
bpy.ops.object.convert(target='MESH')
finish(bpy.context.object, 'clover stem', 'drop', 'clover', 0)

# =============================================================================
# THE METEOR
# =============================================================================
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=METEOR_R, location=(0, 0, 0))
rock = bpy.context.object
craters = [(Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized(), random.uniform(.25, .45), random.uniform(.08, .16)) for _ in range(6)]
for v in rock.data.vertices:
    n = v.co.normalized()
    r = 1 + .16 * noise.fractal(n * 1.6 + Vector((3.1, 7.7, 1.3)), .55, 2.1, 5) + .05 * noise.fractal(n * 6.0, .5, 2.0, 3)
    for c, size, depth in craters:   # bowls with a lip: the rock reads as a real body, not a potato
        ang = n.angle(c)
        if ang < size: r -= depth * (1 - (ang / size) ** 2)
        elif ang < size * 1.35: r += depth * .35 * (1 - (ang - size) / (size * .35))
    v.co = n * METEOR_R * r
rock.scale = (1.12, .92, .98); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
dec = rock.modifiers.new('Native budget', 'DECIMATE'); dec.ratio = 2800.0 / len(rock.data.polygons)
bpy.ops.object.modifier_apply(modifier=dec.name)
finish(rock, 'meteor basalt body', 'rock', 'meteor', 0)

# glowing cracks: tubes laid along wandering paths ON the surface (ray cast from outside), sunk into the rock
bm = bmesh.new(); bm.from_mesh(rock.data); bvh = BVHTree.FromBMesh(bm)
def surface(d):
    hit = bvh.ray_cast(d * METEOR_R * 3, -d)
    return hit[0] if hit[0] is not None else d * METEOR_R
def tube(name, pts, radii, mat, sides=6):
    verts = []; faces = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.orthogonal().normalized(); b = t.cross(a).normalized()
        for k in range(sides):
            th = math.tau * k / sides
            verts.append(tuple(p + (a * math.cos(th) + b * math.sin(th)) * radii[i]))
    for i in range(len(pts) - 1):
        for k in range(sides):
            faces.append((i * sides + k, i * sides + (k + 1) % sides, (i + 1) * sides + (k + 1) % sides, (i + 1) * sides + k))
    faces.append(tuple(range(sides))[::-1]); faces.append(tuple(range((len(pts) - 1) * sides, len(pts) * sides)))
    return finish(mesh_object(name, verts, faces), name, mat, 'meteor', 0, smooth=True)
def crack(name, start, heading, steps, step_deg, width):
    d = start.normalized(); h = heading.normalized(); pts = []; radii = []
    for i in range(steps):
        s = surface(d); pts.append(s - d * width * .35)
        radii.append(width * (.45 + .55 * math.sin(math.pi * i / (steps - 1))))
        axis = d.cross(h).normalized()
        d = (Matrix.Rotation(math.radians(step_deg), 3, axis) @ d).normalized()
        h = (Matrix.Rotation(math.radians(random.uniform(-22, 22)), 3, d) @ h)
        h = (h - d * h.dot(d)).normalized()   # keep the heading on the surface
    return tube(name, pts, radii, 'rockvein')
for i in range(6):
    st = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized()
    crack('meteor gold crack ' + str(i), st, st.orthogonal(), 22, random.uniform(4.0, 6.0), random.uniform(4.5, 7.5))
    for j in range(2):   # branches off each crack
        br = (st + Vector((random.uniform(-.4, .4), random.uniform(-.4, .4), random.uniform(-.4, .4)))).normalized()
        crack('meteor gold crack %d branch %d' % (i, j), br, br.orthogonal(), 9, random.uniform(3.5, 5.0), random.uniform(2.5, 4.0))
# emerald crystals breaking out (the clover's colour: the luck inside the rock)
for i in range(7):
    d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized(); s = surface(d)
    for j in range(3):
        tilt = (d + Vector((random.uniform(-.35, .35), random.uniform(-.35, .35), random.uniform(-.35, .35)))).normalized()
        length = random.uniform(26, 48); rad = random.uniform(5, 9)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=rad, radius2=rad * .22, depth=length, location=(0, 0, 0))
        cr = bpy.context.object
        cr.rotation_mode = 'QUATERNION'; cr.rotation_quaternion = tilt.to_track_quat('Z', 'Y')
        cr.location = s + tilt * (length * .5 - length * .32)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        finish(cr, 'meteor emerald crystal %d %d' % (i, j), 'crystal', 'meteor', 0, smooth=False)
bm.free()

# =============================================================================
# EXPORT
# =============================================================================
records = []
ASSETS = [('tod_luck_clover', 'clover', 1.0, (1, .5, .25)), ('tod_luck_meteor', 'meteor', 1.0, (1,))]
for asset, group, scale, ratios in ASSETS:
    for lod, ratio in enumerate(ratios):
        mod = xmodel.Model(asset); bone = xmodel.Bone('tag_origin'); bone.offset = (0, 0, 0); bone.matrix = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]; mod.bones = [bone]
        ids = {}; tri_count = 0; pts = []; dropped = 0
        for source in parts:
            if source['lucky_group'] != group: continue
            if 'lobe vein' in source.name and lod >= 2: continue   # too small to read there
            ob = source.copy(); ob.data = source.data.copy(); scene.collection.objects.link(ob)
            bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = ob; ob.select_set(True)
            if ratio < 1:
                d = ob.modifiers.new('Native LOD reduction', 'DECIMATE'); d.ratio = ratio
                bpy.ops.object.modifier_apply(modifier=d.name)
            me = ob.data; me.calc_loop_triangles(); me.update(); nm = ob.matrix_world.to_3x3().inverted().transposed()
            matname = me.materials[0].name
            if matname not in ids: ids[matname] = len(mod.materials); mod.materials.append(xmodel.Material(matname, 'Phong', {}))
            mesh = xmodel.Mesh(source.name)
            mesh.verts = [xmodel.Vertex(tuple((ob.matrix_world @ v.co) * scale), [(0, 1.)]) for v in me.vertices]
            for v in mesh.verts: pts.append(v.offset)
            uv = me.uv_layers.active.data
            for tri in me.loop_triangles:
                p = [Vector(mesh.verts[v].offset) for v in tri.vertices]
                edges = ((p[1] - p[0]).length, (p[2] - p[0]).length, (p[2] - p[1]).length); longest = max(edges)
                # the backstop: a needle (an edge under CLEAN_EPS) or a sliver is what the converter drops - drop it here so
                # the exported count IS the compiled count (verify_native compares them)
                if min(edges) < CLEAN_EPS or longest < .001 or (p[1] - p[0]).cross(p[2] - p[0]).length / longest ** 2 < .0006:
                    dropped += 1; continue
                f = xmodel.Face(len(mod.meshes), ids[matname]); f.indices = []
                for corner in [0, 2, 1]:
                    li = tri.loops[corner]; normal = (nm @ me.corner_normals[li].vector).normalized(); u = uv[li].uv
                    f.indices.append(xmodel.FaceVertex(tri.vertices[corner], tuple(normal), (1, 1, 1, 1), (u.x, 1 - u.y)))
                mesh.faces.append(f)
            if mesh.faces: mod.meshes.append(mesh); tri_count += len(mesh.faces)
            bpy.data.objects.remove(ob, do_unlink=True)
        suffix = '_lod' + str(lod) if len(ratios) > 1 else ''
        path = EXP / (asset + suffix + '.xmodel_bin'); mod.WriteFile_Bin(str(path), version=7)
        records.append(dict(asset=asset, lod=lod, lods=len(ratios), triangles=tri_count, dropped_needles=dropped, meshes=len(mod.meshes), materials=[m.name for m in mod.materials],
                            file=path.relative_to(ROOT).as_posix(), sha256=sha(path),
                            bounds=[[min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]]))
    f = dict(filename='tod_lucky/' + asset + ('_lod0' if len(ratios) > 1 else '') + '.xmodel_bin')
    if len(ratios) > 1:
        f['mediumLod'] = 'tod_lucky/' + asset + '_lod1.xmodel_bin'
        f['mediumLodDist'] = 380
    if len(ratios) > 2:
        f['lowLod'] = 'tod_lucky/' + asset + '_lod2.xmodel_bin'; f['lowLodDist'] = 1000
    f.update(type='rigid', scale=1, CollisionMap='', BulletCollisionLOD='None', physicsPreset='', cullOutDiameter=0, materials='')
    if group == 'meteor': f['noCastShadow'] = 1
    block(asset, 'xmodel', f)
gdt = ROOT / 'source_data/tod_lucky.gdt'
gdt.write_text('{\n' + ''.join(blocks) + '}\n')

# =============================================================================
# PREVIEWS (lights + cameras are never exported)
# =============================================================================
def area(name, loc, power, size, color, aim):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.shape = 'DISK'; d.size = size; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = (Vector(aim) - o.location).to_track_quat('-Z', 'Y').to_euler()
    return o
cam = bpy.data.objects.new('Review camera', bpy.data.cameras.new('Review camera')); scene.collection.objects.link(cam); scene.camera = cam
def shot(file, loc, aim, ortho, lights, show):
    for ob in parts: ob.hide_render = ob['lucky_group'] not in show
    for o in lights: o.hide_render = False
    cam.location = loc; cam.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    scene.render.filepath = str(OUT / file); bpy.ops.render.render(write_still=True)
    for o in lights: o.hide_render = True
    return str(OUT / file)
# THE LINE-UP REFERENCES: the real PaP drop and Zombie Blood, read back from their shipped XMODEL_BIN (preview only)
refs = []
def import_bin(path, name, x):
    m = xmodel.Model(); m.LoadFile_Bin(str(path), split_meshes=False)
    for k, mesh in enumerate(m.meshes):
        verts = [tuple(v.offset) for v in mesh.verts]
        faces = [tuple(fv.vertex for fv in f.indices) for f in mesh.faces]
        me = bpy.data.meshes.new(name + str(k)); me.from_pydata(verts, [], faces); me.update(); me.validate()
        ob = bpy.data.objects.new('REFERENCE ' + name + ' ' + str(k), me); scene.collection.objects.link(ob)
        ob.location = (x, 0, 0); ob.data.materials.append(mats['drop'])
        for p in ob.data.polygons: p.use_smooth = True
        refs.append(ob)
TOOLS_ROOT = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity')
import_bin(TOOLS_ROOT / 'model_export/_ZoekMeMaar/powerups/pack_a_punch.XMODEL_BIN', 'pap drop', -27)
import_bin(TOOLS_ROOT / 'model_export/_NSZ/powerups/zombie_blood.XMODEL_BIN', 'zombie blood', 24)
def world(color, strength):
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = color
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = strength
def shot2(file, loc, aim, ortho, lights, show, show_refs):
    for r in refs: r.hide_render = not show_refs
    return shot(file, loc, aim, ortho, lights, show)
cl = [area('clover key', (18, -40, 26), 16000, 22, (1, .97, .92), (0, 0, 0)), area('clover rim', (-28, 30, 10), 10000, 18, (.75, .9, 1), (0, 0, 0))]
ll = [area('line-up key', (30, -90, 50), 60000, 60, (1, .97, .92), (0, 0, 0)), area('line-up rim', (-60, 60, 20), 30000, 50, (.75, .9, 1), (0, 0, 0))]
ml = [area('meteor key', (500, -700, 400), 4e6, 400, (1, .95, .9), (0, 0, 0)), area('meteor rim', (-700, 500, 200), 2.5e6, 400, (.7, .8, 1), (0, 0, 0))]
for o in cl + ll + ml: o.hide_render = True
world((.30, .33, .38, 1), .9)   # the drops are pure reflection: give them something to reflect (BO3's probes do in game)
renders = {
    'clover_front': shot2('clover_front.png', (0, -60, -1), (0, 0, -1), 27, cl, ['clover'], False),
    'clover_34': shot2('clover_34.png', (38, -46, 14), (0, 0, -1), 27, cl, ['clover'], False),
    'lineup_front': shot2('lineup_front.png', (0, -140, 0), (0, 0, 0), 80, ll, ['clover'], True),
    'lineup_34': shot2('lineup_34.png', (70, -120, 30), (0, 0, 0), 80, ll, ['clover'], True),
}
world((.02, .025, .035, 1), .25)
renders['meteor'] = shot2('meteor.png', (520, -620, 240), (0, 0, 0), 420, ml, ['meteor'], False)
for r in refs: bpy.data.objects.remove(r, do_unlink=True)   # the references never stay in the studio file
for ob in parts: ob.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'lucky.blend'))
manifest = dict(authoring='Blender MCP execute_blender_code (tools/lucky/mcp_call.py, port 9888)', models=records, textures=textures, gdt_sha256=sha(gdt),
                meteor_radius=METEOR_R, drop_material=DROP_MTL, renders=renders, preview_native_verified=False)
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print('LUCKY_AUTHORED', json.dumps({'models': len(records), 'triangles': {r['asset'] + ('_lod%d' % r['lod']): r['triangles'] for r in records},
                                   'bounds': {r['asset']: r['bounds'] for r in records if r['lod'] == 0}, 'parts': len(parts), 'renders': renders}))
