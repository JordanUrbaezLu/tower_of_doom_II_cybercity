"""Shared helpers for every Dealer boss authoring step (exec'd into the live studio).

Geometry: lofts, tubes along bone chains, boxes, spheres - all in BO3 model
space (inches, +X forward, +Y left, +Z up). Materials: one procedural library
with wear, every material tagged with the native atlas it bakes into. Skinning:
nearest-bone-segment weights so each part follows the Keeper skeleton exactly
where the donor's own skin would.
"""
import bpy, bmesh, math, json, random, os
from pathlib import Path
from mathutils import Vector, Matrix, noise

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'art/dealer_boss'
scene = bpy.context.scene
if not scene.get('tod2_dealer_boss_studio'):
    raise RuntimeError('Not the Dealer boss studio')
RIG = bpy.data.objects['DEALER_RIG | Keeper animation skeleton']
SKEL = json.loads((ART / 'skeleton.json').read_text())
BONES = {b['name']: b for b in SKEL['bones']}
BONE_LIST = [b['name'] for b in SKEL['bones']]
CHILDREN = {}
for b in SKEL['bones']:
    if b['parent'] >= 0:
        CHILDREN.setdefault(SKEL['bones'][b['parent']]['name'], []).append(b['name'])


def bone_pos(name):
    return Vector(BONES[name]['offset'])


def coll(key):
    for c in bpy.data.collections:
        if c.name.startswith('DEALER | ' + key):
            return c
    raise KeyError(key)


# ------------------------------------------------------------------ materials
# atlas: which native material/atlas the part bakes into ('body', 'head', 'hands')
MATS = {}


def purge_materials():
    """Drop every authored Dealer material (the first body step calls it; later steps reuse)."""
    for m in list(bpy.data.materials):
        if m.name.startswith('DEALER / '):
            bpy.data.materials.remove(m)
    MATS.clear()


def material(name, color, metallic=0.0, rough=0.6, emit=0.0, emit_color=None, atlas='body', **extra):
    if name in MATS:
        return MATS[name]
    existing = bpy.data.materials.get('DEALER / ' + name)
    if existing is not None:
        MATS[name] = existing
        return existing
    m = bpy.data.materials.new('DEALER / ' + name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = rough
    p.inputs['Emission Color'].default_value = (*(emit_color or color), 1)
    p.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = (*color, 1)
    m['atlas'] = atlas
    for k, v in extra.items():
        m[k] = v
    MATS[name] = m
    return m


def wear_nodes(m, scale=28.0, strength=0.35, edge_color=(0.16, 0.15, 0.14), weave=0.0, bump=0.08, seed=0, lo=0.56, hi=0.86):
    """Procedural surface: fine weave/grain normal, edge wear lighten, dirt darkening in recesses."""
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    base = p.inputs['Base Color'].default_value[:]
    coord = nt.nodes.new('ShaderNodeTexCoord')
    # a per-material generated texture space keyed on object coordinates (bakes stably)
    grain = nt.nodes.new('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value = scale; grain.inputs['Detail'].default_value = 6; grain.inputs['Roughness'].default_value = 0.62
    grain.noise_dimensions = '4D'; grain.inputs['W'].default_value = seed * 0.37
    nt.links.new(coord.outputs['Object'], grain.inputs['Vector'])
    dirt = nt.nodes.new('ShaderNodeTexNoise'); dirt.inputs['Scale'].default_value = scale * 0.11; dirt.inputs['Detail'].default_value = 3
    dirt.noise_dimensions = '4D'; dirt.inputs['W'].default_value = seed * 0.37 + 11
    nt.links.new(coord.outputs['Object'], dirt.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = lo; ramp.color_ramp.elements[1].position = hi
    ramp.color_ramp.elements[0].color = (*base[:3], 1)
    ramp.color_ramp.elements[1].color = (*[base[i] * (1 - strength) + edge_color[i] * strength for i in range(3)], 1)
    nt.links.new(grain.outputs['Fac'], ramp.inputs['Fac'])
    darken = nt.nodes.new('ShaderNodeMixRGB'); darken.blend_type = 'MULTIPLY'; darken.inputs[0].default_value = 0.55
    nt.links.new(ramp.outputs['Color'], darken.inputs[1])
    dramp = nt.nodes.new('ShaderNodeValToRGB'); dramp.color_ramp.elements[0].color = (0.55, 0.52, 0.5, 1); dramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(dirt.outputs['Fac'], dramp.inputs['Fac'])
    nt.links.new(dramp.outputs['Color'], darken.inputs[2])
    nt.links.new(darken.outputs['Color'], p.inputs['Base Color'])
    # roughness breakup
    rmix = nt.nodes.new('ShaderNodeMath'); rmix.operation = 'MULTIPLY_ADD'
    rmix.inputs[1].default_value = 0.22; rmix.inputs[2].default_value = p.inputs['Roughness'].default_value - 0.11
    nt.links.new(grain.outputs['Fac'], rmix.inputs[0])
    nt.links.new(rmix.outputs[0], p.inputs['Roughness'])
    # normal: grain bump (+ optional woven cloth)
    bmp = nt.nodes.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = bump
    if weave:
        wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'DIAGONAL'; wv.inputs['Scale'].default_value = weave; wv.inputs['Distortion'].default_value = 0.6; wv.inputs['Detail'].default_value = 2
        nt.links.new(coord.outputs['Object'], wv.inputs['Vector'])
        add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
        nt.links.new(grain.outputs['Fac'], add.inputs[0]); nt.links.new(wv.outputs['Fac'], add.inputs[1])
        nt.links.new(add.outputs[0], bmp.inputs['Height'])
    else:
        nt.links.new(grain.outputs['Fac'], bmp.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], p.inputs['Normal'])
    return m


def library():
    """The Dealer's finishes. Called by every step; idempotent (existing materials are reused untouched)."""
    if MATS:
        return MATS
    if bpy.data.materials.get('DEALER / heavy black wool coat') is not None:
        for m in bpy.data.materials:
            if m.name.startswith('DEALER / '):
                MATS[m.name[9:]] = m
        return MATS
    cloth = wear_nodes(material('heavy black wool coat', (0.009, 0.0085, 0.010), 0, 0.93, atlas='body'), 34, 0.16, (0.09, 0.085, 0.08), weave=180, bump=0.12, seed=1)
    wear_nodes(material('hood black wool', (0.0085, 0.008, 0.0095), 0, 0.94, atlas='head'), 30, 0.14, (0.085, 0.08, 0.075), weave=160, bump=0.12, seed=2)
    wear_nodes(material('dark trouser cloth', (0.012, 0.011, 0.012), 0, 0.9, atlas='body'), 40, 0.14, (0.08, 0.075, 0.07), weave=200, bump=0.1, seed=14)
    wear_nodes(material('oxblood satin lining', (0.075, 0.005, 0.010), 0, 0.42, atlas='body'), 60, 0.16, (0.18, 0.04, 0.05), bump=0.03, seed=3)
    wear_nodes(material('worn black leather', (0.014, 0.012, 0.012), 0, 0.5, atlas='body'), 40, 0.24, (0.14, 0.12, 0.10), bump=0.10, seed=4)
    wear_nodes(material('glove black leather', (0.013, 0.011, 0.012), 0, 0.48, atlas='hands'), 48, 0.22, (0.14, 0.12, 0.10), bump=0.10, seed=5)
    wear_nodes(material('graphite molded mask', (0.028, 0.03, 0.034), 0.15, 0.36, atlas='head'), 24, 0.26, (0.11, 0.115, 0.12), bump=0.06, seed=6, lo=0.5, hi=0.9)
    material('mask void black', (0.002, 0.002, 0.003), 0, 0.9, atlas='head')
    material('red neon wire', (0.55, 0.012, 0.02), 0, 0.3, emit=9.0, emit_color=(1.0, 0.03, 0.04), atlas='head', emissive=True)
    material('red neon wire weak', (0.3, 0.01, 0.015), 0, 0.3, emit=1.6, emit_color=(1.0, 0.05, 0.05), atlas='head', emissive=True)
    # STATE TWO (the cracked mask, 10_state2_mask.py): a dead neon tube (no glow, dark red glass) and the black fissures
    material('red neon wire dead', (0.075, 0.006, 0.008), 0, 0.55, atlas='head')
    material('mask crack black', (0.0035, 0.003, 0.004), 0, 0.72, atlas='head')
    wear_nodes(material('lacquered red nails', (0.38, 0.004, 0.012), 0.05, 0.12, emit=0.9, emit_color=(1.0, 0.02, 0.03), atlas='hands', emissive=True), 90, 0.25, (0.55, 0.08, 0.08), bump=0.03, seed=7)
    wear_nodes(material('aged brass fittings', (0.42, 0.28, 0.12), 0.95, 0.46, atlas='body'), 70, 0.4, (0.22, 0.15, 0.07), bump=0.05, seed=8)
    wear_nodes(material('blackened steel', (0.07, 0.072, 0.078), 0.9, 0.44, atlas='body'), 60, 0.4, (0.25, 0.25, 0.26), bump=0.05, seed=9)
    material('dark glass vial', (0.03, 0.02, 0.025), 0.0, 0.08, atlas='body')
    material('red essence', (0.5, 0.01, 0.02), 0, 0.2, emit=2.4, emit_color=(1.0, 0.05, 0.06), atlas='body', emissive=True)
    # the mask's stitched-grin signature carried onto the clothes: every seam is a faint red neon thread
    material('red stitch thread', (0.45, 0.02, 0.03), 0, 0.6, emit=1.1, emit_color=(1.0, 0.05, 0.05), atlas='body', emissive=True)
    wear_nodes(material('worn black boot leather', (0.013, 0.012, 0.012), 0, 0.5, atlas='body'), 36, 0.3, (0.16, 0.14, 0.12), bump=0.12, seed=11)
    wear_nodes(material('black rubber sole', (0.012, 0.012, 0.013), 0, 0.82, atlas='body'), 50, 0.2, (0.1, 0.1, 0.1), bump=0.15, seed=12)
    wear_nodes(material('tarnished silver coin', (0.5, 0.5, 0.48), 0.95, 0.35, atlas='body'), 150, 0.3, (0.25, 0.25, 0.24), bump=0.04, seed=13)
    return MATS


# ------------------------------------------------------------------ geometry
def mesh(name, verts, faces, mat, collection, smooth=True, bevel=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    for poly in me.polygons:
        poly.use_smooth = smooth
    if bevel:
        b = ob.modifiers.new('Edge bevel', 'BEVEL'); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    ob['dealer_part'] = True
    return ob


def loft(name, rings, mat, collection, segments=64, folds=0.0, fold_scale=1.0, cap_top=False, cap_bottom=False, profile=None, seed=0, twist=0.0):
    """rings: list of (cx, cy, cz, rx, ry) ellipses stacked bottom->top (or any order along the part).
    profile(theta, j) -> radial multiplier shapes a ring (chest flattening, back rounding...).
    folds: cloth drape ridges running along the loft (vertical pleats)."""
    verts = []
    n = len(rings)
    for j, (cx, cy, cz, rx, ry) in enumerate(rings):
        for i in range(segments):
            a = i * math.tau / segments + twist * j
            f = 1.0
            if profile:
                f *= profile(a, j)
            r_add = 0.0
            if folds:
                r_add = folds * (0.55 * math.sin(9 * a * fold_scale + 0.31 * j + seed) + 0.3 * math.sin(17 * a * fold_scale - 0.17 * j + seed * 2) + 0.15 * math.cos(5 * a * fold_scale + seed))
                r_add *= min(1.0, j / max(1, n * 0.25))  # pleats grow away from the first ring
            x = cx + (rx * f + r_add) * math.cos(a)
            y = cy + (ry * f + r_add * 0.8) * math.sin(a)
            verts.append((x, y, cz))
    faces = [(j * segments + i, j * segments + (i + 1) % segments, (j + 1) * segments + (i + 1) % segments, (j + 1) * segments + i)
             for j in range(n - 1) for i in range(segments)]
    if cap_bottom:
        faces.append(tuple(range(segments - 1, -1, -1)))
    if cap_top:
        faces.append(tuple((n - 1) * segments + i for i in range(segments)))
    return mesh(name, verts, faces, mat, collection)


def frame_along(points):
    """Orthonormal frames (t, n, b) along a polyline, parallel-transported."""
    pts = [Vector(p) for p in points]
    tangents = []
    for i in range(len(pts)):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == len(pts) - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i - 1])
        tangents.append(t.normalized())
    frames = []
    up = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
    n = (up - tangents[0] * up.dot(tangents[0])).normalized()
    for t in tangents:
        n = (n - t * n.dot(t)).normalized()
        b = t.cross(n).normalized()
        frames.append((t, n, b))
    return pts, frames


def tube(name, points, radii, mat, collection, segments=24, cap_start=False, cap_end=False, squash=1.0, noise_amt=0.0, seed=0):
    """A tube along a polyline. radii: per point (float) or per point (rx, ry)."""
    pts, frames = frame_along(points)
    verts = []
    for j, (p, (t, n, b)) in enumerate(zip(pts, frames)):
        r = radii[j] if j < len(radii) else radii[-1]
        rx, ry = (r, r * squash) if not isinstance(r, (tuple, list)) else r
        for i in range(segments):
            a = i * math.tau / segments
            d = 0.0
            if noise_amt:
                d = noise_amt * noise.noise(Vector((math.cos(a) * 1.7 + seed, math.sin(a) * 1.7, j * 0.6)))
            verts.append(p + n * ((rx + d) * math.cos(a)) + b * ((ry + d) * math.sin(a)))
    faces = [(j * segments + i, j * segments + (i + 1) % segments, (j + 1) * segments + (i + 1) % segments, (j + 1) * segments + i)
             for j in range(len(pts) - 1) for i in range(segments)]
    if cap_start:
        faces.append(tuple(range(segments - 1, -1, -1)))
    if cap_end:
        faces.append(tuple((len(pts) - 1) * segments + i for i in range(segments)))
    return mesh(name, verts, faces, mat, collection)


def box(name, center, size, mat, collection, bevel=0.0, rot=None):
    cx, cy, cz = center; sx, sy, sz = size
    corners = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz), (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    R = Matrix.Identity(3) if rot is None else Matrix(rot).to_3x3() if not isinstance(rot, Matrix) else rot.to_3x3()
    verts = [Vector(center) + R @ Vector(c) for c in corners]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh(name, verts, faces, mat, collection, smooth=False, bevel=bevel)


def sphere(name, center, radius, mat, collection, rings=16, segments=24):
    rx, ry, rz = (radius, radius, radius) if not isinstance(radius, (tuple, list)) else radius
    verts = []; cx, cy, cz = center
    for j in range(1, rings):
        ph = math.pi * j / rings
        for i in range(segments):
            th = i * math.tau / segments
            verts.append((cx + rx * math.sin(ph) * math.cos(th), cy + ry * math.sin(ph) * math.sin(th), cz + rz * math.cos(ph)))
    top = len(verts); verts.append((cx, cy, cz + rz)); bot = len(verts); verts.append((cx, cy, cz - rz))
    faces = []
    for j in range(rings - 2):
        for i in range(segments):
            faces.append((j * segments + i, (j + 1) * segments + i, (j + 1) * segments + (i + 1) % segments, j * segments + (i + 1) % segments))
    for i in range(segments):
        faces.append((top, (i + 1) % segments, i))
        faces.append((bot, (rings - 2) * segments + i, (rings - 2) * segments + (i + 1) % segments))
    return mesh(name, verts, faces, mat, collection)


def cut_faces(ob, keep):
    """Delete every face whose centre fails keep(center) and drop the verts it strands."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for f in list(bm.faces):
        if not keep(f.calc_center_median()):
            bm.faces.remove(f)
    for v in list(bm.verts):
        if not v.link_faces:
            bm.verts.remove(v)
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    return ob


def displace_noise(ob, amount, scale, seed=0, along_normal=True, mask=None):
    """Organic breakup (cloth folds, worn surfaces): move verts by layered noise."""
    me = ob.data
    me.calc_normals_split() if hasattr(me, 'calc_normals_split') else None
    vnorm = [v.normal.copy() for v in me.vertices]
    for v, nrm in zip(me.vertices, vnorm):
        p = v.co
        d = (noise.noise(Vector((p.x, p.y, p.z)) * scale + Vector((seed, seed * 0.3, 0))) * 0.7 +
             noise.noise(Vector((p.x, p.y, p.z)) * scale * 2.3 + Vector((seed * 2, 0, seed))) * 0.3)
        k = mask(p) if mask else 1.0
        v.co = p + (nrm if along_normal else Vector((0, 0, 1))) * (d * amount * k)
    me.update()


def subdivide(ob, levels=1):
    s = ob.modifiers.new('Drape smoothing', 'SUBSURF'); s.levels = levels; s.render_levels = levels
    return s


def solidify(ob, thickness, offset=-1):
    s = ob.modifiers.new('Shell thickness', 'SOLIDIFY'); s.thickness = thickness; s.offset = offset; s.use_even_offset = True
    return s


def mirror_y(points):
    return [(p[0], -p[1], p[2]) for p in points]


# ------------------------------------------------------------------ skinning
def segments_for(bones):
    """Bone segments (name, head, tail) for the named bones; a leaf uses its bind axis."""
    segs = []
    for n in bones:
        h = bone_pos(n)
        kids = [k for k in CHILDREN.get(n, []) if k in BONES and not k.startswith('tag_')]
        if kids:
            t = sum((bone_pos(k) for k in kids), Vector()) / len(kids)
        else:
            t = h + Vector(BONES[n]['matrix'][1]) * 2.0
        if (t - h).length < 0.5:
            t = h + Vector(BONES[n]['matrix'][1]) * 2.0
        segs.append((n, h, t))
    return segs


def seg_dist(p, h, t):
    d = t - h
    L2 = d.length_squared
    u = 0.0 if L2 < 1e-9 else max(0.0, min(1.0, (p - h).dot(d) / L2))
    return (p - (h + d * u)).length, u


def skin(ob, bones, sigma=6.0, k=3, chain_blend=None, override=None):
    """Weight every vertex of ob to the nearest k bone segments among `bones`
    (Gaussian falloff, normalized). chain_blend: for a single ordered chain, blend
    linearly between consecutive bones by projection instead (sleeves, fingers).
    override(p) -> {bone: weight} replaces the weights for vertices where it returns a dict."""
    me = ob.data
    for vg in list(ob.vertex_groups):
        ob.vertex_groups.remove(vg)
    groups = {}
    def grp(n):
        if n not in groups:
            groups[n] = ob.vertex_groups.new(name=n)
        return groups[n]
    segs = segments_for(bones)
    M = ob.matrix_world
    for v in me.vertices:
        p = M @ v.co
        w = override(p) if override else None
        if not w:
            if chain_blend:
                w = {}
                # project onto the chain polyline; blend between the segment's two bones
                best = None
                for i, (n, h, t) in enumerate(segs):
                    d, u = seg_dist(p, h, t)
                    if best is None or d < best[0]:
                        best = (d, i, u)
                d, i, u = best
                n = segs[i][0]
                nxt = segs[i + 1][0] if i + 1 < len(segs) else None
                prv = segs[i - 1][0] if i > 0 else None
                # soft knee: within the last third of a segment start blending to the next bone
                if nxt and u > 0.66:
                    f = (u - 0.66) / 0.34 * 0.5
                    w = {n: 1 - f, nxt: f}
                elif prv and u < 0.0:
                    w = {n: 1.0}
                else:
                    w = {n: 1.0}
            else:
                ds = sorted(((seg_dist(p, h, t)[0], n) for n, h, t in segs))[:k]
                w = {n: math.exp(-(d / sigma) ** 2) for d, n in ds}
                tot = sum(w.values()) or 1.0
                w = {n: x / tot for n, x in w.items() if x / tot > 0.02}
                tot = sum(w.values()) or 1.0
                w = {n: x / tot for n, x in w.items()}
        for n, x in w.items():
            grp(n).add([v.index], x, 'REPLACE')
    if not any(m.type == 'ARMATURE' for m in ob.modifiers):
        ob.parent = RIG
        ob.modifiers.new('Keeper skeleton', 'ARMATURE').object = RIG
    ob['skinned'] = True
    return ob


def fixed_bone(ob, bone):
    return skin(ob, [bone], override=lambda p: {bone: 1.0})


def review_state(n):
    """Show one of the Dealer's two states in the studio: 1 = the masked Dealer, 2 = the CRACKED mask
    (objects tagged state1_only / state2_only; everything else is in both). The exporter unhides all."""
    for ob in scene.objects:
        if ob.get('state1_only') or ob.get('state2_only'):
            hide = bool(ob.get('state1_only')) if n == 2 else bool(ob.get('state2_only'))
            ob.hide_viewport = hide; ob.hide_render = hide; ob.hide_set(hide)


def view_hero():
    cam = bpy.data.objects.get('CAM 01 | hero three-quarter')
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                s = area.spaces.active
                s.shading.type = 'MATERIAL'
                if cam:
                    s.region_3d.view_rotation = cam.rotation_euler.to_quaternion()
                    s.region_3d.view_location = (0, 0, 40); s.region_3d.view_distance = 190


def save(stage):
    scene['dealer_stage'] = stage
    bpy.context.view_layer.update()
    # TOD_DEALER_MASTER_OUT: author on a STAGED copy while a peer build's gates still read the shipped master's sha
    bpy.ops.wm.save_as_mainfile(filepath=os.environ.get('TOD_DEALER_MASTER_OUT') or str(ART / 'dealer_boss.blend'))
