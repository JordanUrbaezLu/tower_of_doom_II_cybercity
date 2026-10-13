"""Shared helpers for THE SKY FLEET authoring scripts (docs/192).

Run inside the dedicated Blender studio through tools/sky_ships/mcp_call.py (port 9890). Units are BO3 units
(inches). A ship is built around ITS OWN origin in mesh space (bow along +X, port side +Y, up +Z) and the
object is only translated (object.location = the studio offset), so the export reads mesh coordinates as-is.

Readability rules (user 2026-09-29, "minor details are not needed but high level detail should be 100% so its
very obvious from far away"): silhouettes first; emissive lines 40-80 units wide on the big ships; brightness
ladder engines > neon > windows > hull. v2 (user 2026-09-29 13:10, "they actually need a lot more detail. I
underestimated how much detail we should be adding"): the silhouettes stay and gain the layers AAA capital
ships carry - raised armour plating, superstructure tiers, turret batteries, antenna masts, dishes, vent and
radiator banks, trusses, detailed nozzles, dense window rows, running lights, markings (tools/sky_ships/
detail_lib.py). Textures come from make_textures.py (system Python), loaded here by name.
"""
import bpy, bmesh, math, json, hashlib, pathlib
import numpy as np
from mathutils import Vector, Euler

ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = ROOT / 'art/sky_ships'
EXP = ROOT / 'model_export/tod_sky_ships'
TEX = EXP / '_images'
for d in (ART, EXP, TEX):
    d.mkdir(parents=True, exist_ok=True)

# ---- palette (linear RGB) -------------------------------------------------------------------------
from sky_data import GLOW, CARGO, DECO_CELLS, AD_ORDER   # one source, shared with make_textures.py
# Emissive strength = BO3 scaleRGB (colour map x scaleRGB). Tuned by eye in the native game later: ONE table.
# First pass 14/36/7/28/12/1.6/9 was studio-bright but DISTANCE eats emission in this map: the crown alarm
# lamps needed 36 -> 144 to read from ~10,000 units (user playtests 2026-09-26). The fleet flies 5-20k out.
EMIT = {'neon': 48.0, 'engine': 110.0, 'window': 18.0, 'nav': 70.0, 'hangar': 32.0, 'container': 3.5, 'glass': 24.0,
        'deco': 20.0, 'ads': 9.0, 'rock': 0.6}         # rock: a faint self-light, the night side never goes black


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


# ---- images ---------------------------------------------------------------------------------------
def save_image(name, arr, noncolor=False):
    """arr: float32 HxWx4 in 0..1. Writes model_export/tod_sky_ships/_images/<name>.png and returns the bpy image."""
    h, w = arr.shape[:2]
    assert h % 4 == 0 and w % 4 == 0, name + ': compressed images must be multiples of 4'
    im = bpy.data.images.get(name)
    if im is not None and (im.size[0] != w or im.size[1] != h):
        bpy.data.images.remove(im)
        im = None
    if im is None:
        im = bpy.data.images.new(name, width=w, height=h, alpha=True)
    if noncolor:
        im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(np.ascontiguousarray(arr[::-1]).ravel().astype(np.float32))   # Blender rows go bottom-up
    path = TEX / (name + '.png')
    im.filepath_raw = str(path)
    im.file_format = 'PNG'
    im.save()
    return im


def solid(rgb, n=64):
    a = np.ones((n, n, 4), dtype=np.float32)
    a[:, :, :3] = rgb
    return a


def load_image(name):
    """A texture written by make_textures.py (model_export/tod_sky_ships/_images/<name>.png), by name."""
    path = TEX / (name + '.png')
    assert path.exists(), name + ' missing: run python tools/sky_ships/make_textures.py first'
    im = bpy.data.images.get(name)
    if im is not None:
        im.filepath = str(path)
        im.reload()
    else:
        im = bpy.data.images.load(str(path))
        im.name = name
    if name.endswith('_n') or name.endswith('_g'):
        im.colorspace_settings.name = 'Non-Color'
    return im


# ---- materials ------------------------------------------------------------------------------------
def make_material(label, color_img, kind, emit=0.0, rough=0.5, metal=0.0, maps=None, viewport_rgb=None, surface=None):
    """A Blender material for the viewport + its native BO3 definition (stored on the material as JSON).

    kind: 'hull' (lit metal, no glow) or 'glow' (emissive: BO3 emission = colour map x scaleRGB)."""
    name = 'mtl_tod_sky_' + label
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_fake_user = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bs.outputs['BSDF'], out.inputs['Surface'])
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = color_img
    nt.links.new(tex.outputs['Color'], bs.inputs['Base Color'])
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Roughness'].default_value = rough
    if emit > 0:
        nt.links.new(tex.outputs['Color'], bs.inputs['Emission Color'])
        bs.inputs['Emission Strength'].default_value = emit * 0.18   # studio view only; native = scaleRGB
    maps = maps or {}
    nname = maps.get('n')
    if nname and nname != 'i_tod_sky_flat_n' and bpy.data.images.get(nname) is not None:
        ntex = nt.nodes.new('ShaderNodeTexImage')
        ntex.image = bpy.data.images[nname]
        nmap = nt.nodes.new('ShaderNodeNormalMap')
        nmap.inputs['Strength'].default_value = 1.0
        nt.links.new(ntex.outputs['Color'], nmap.inputs['Color'])
        nt.links.new(nmap.outputs['Normal'], bs.inputs['Normal'])
    m['bo3'] = json.dumps(dict(
        kind=kind, colorMap=color_img.name, normalMap=maps.get('n', 'i_tod_sky_flat_n'),
        cosinePowerMap=maps.get('g', 'i_tod_sky_flat_g'), specColorMap=maps.get('s', 'i_tod_sky_flat_s'),
        scaleRGB=emit, surfaceType=surface or ('metal' if metal else 'plastic')))
    if viewport_rgb:
        m.diffuse_color = (*viewport_rgb, 1)
    return m


def mat(label):
    m = bpy.data.materials.get('mtl_tod_sky_' + label)
    assert m is not None, 'material not authored yet: ' + label + ' (run 01_studio.py)'
    return m


# ---- scene ----------------------------------------------------------------------------------------
def ship_collection(key, offset):
    """A fresh collection for one ship; its objects are translated to `offset` in the studio."""
    name = 'SHIP ' + key
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
    col['ship'] = key
    col['offset'] = list(offset)
    return col


class Part:
    """Accumulates one bmesh per (part name); finish() makes the object."""

    def __init__(self, col, name, material, group='hull', lod1=True):
        self.col, self.name, self.material, self.group, self.lod1 = col, name, material, group, lod1
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')

    def quad(self, pts, uvs=None):
        vs = [self.bm.verts.new(tuple(p)) for p in pts]
        f = self.bm.faces.new(vs)
        if uvs:
            for loop, uv in zip(f.loops, uvs):
                loop[self.uv].uv = uv
        return f

    def finish(self, box_uv_scale=None, recalc=True):
        bm = self.bm
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.05)
        if recalc:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if box_uv_scale:
            for f in bm.faces:
                n = f.normal
                ax = max(range(3), key=lambda i: abs(n[i]))
                a, b = [(1, 2), (0, 2), (0, 1)][ax]
                for loop in f.loops:
                    co = loop.vert.co
                    loop[self.uv].uv = (co[a] / box_uv_scale, co[b] / box_uv_scale)
        me = bpy.data.meshes.new(self.name)
        smooth = any(f.smooth for f in bm.faces)                 # detail_lib marks round parts (cylinders, domes)
        bm.to_mesh(me)
        bm.free()
        if smooth:
            me.set_sharp_from_angle(angle=math.radians(38))       # round stays round, every hard edge stays hard
        me.materials.append(self.material)
        ob = bpy.data.objects.new(self.name, me)
        self.col.objects.link(ob)
        ob.location = Vector(self.col['offset'])
        ob['sky_group'] = self.group
        ob['lod1'] = bool(self.lod1)
        return ob


# ---- shapes (all in ship space) -------------------------------------------------------------------
def loft(part, rings, cap_start=True, cap_end=True):
    """Skin consecutive rings (lists of 3D points, same count, going around the x axis)."""
    bm = part.bm
    vv = [[bm.verts.new(tuple(p)) for p in ring] for ring in rings]
    n = len(rings[0])
    for r in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([vv[r][i], vv[r][j], vv[r + 1][j], vv[r + 1][i]])
    if cap_start:
        bm.faces.new(list(reversed(vv[0])))
    if cap_end:
        bm.faces.new(vv[-1])
    return vv


def prism(part, profile, z0, z1):
    """Extrude a 2D (x, y) polygon between two heights."""
    return loft(part, [[(x, y, z0) for x, y in profile], [(x, y, z1) for x, y in profile]])


def box(part, x0, x1, y0, y1, z0, z1):
    return prism(part, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def tapered_box(part, lo, hi):
    """lo/hi = (x0, x1, y0, y1, z) for the bottom and top rectangles."""
    a = [(lo[0], lo[2], lo[4]), (lo[1], lo[2], lo[4]), (lo[1], lo[3], lo[4]), (lo[0], lo[3], lo[4])]
    b = [(hi[0], hi[2], hi[4]), (hi[1], hi[2], hi[4]), (hi[1], hi[3], hi[4]), (hi[0], hi[3], hi[4])]
    return loft(part, [a, b])


def cylinder_x(part, x0, x1, y, z, r0, r1, sides=16, caps=(True, True)):
    """A (possibly tapered) cylinder along x from x0 (radius r0) to x1 (radius r1)."""
    ring = lambda x, r: [(x, y + r * math.cos(2 * math.pi * i / sides), z + r * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
    return loft(part, [ring(x0, r0), ring(x1, r1)], cap_start=caps[0], cap_end=caps[1])


def disc_x(part, x, y, z, r, facing=-1, sides=24):
    """A flat disc in the YZ plane at x, facing -x (the stern) or +x."""
    pts = [(x, y + r * math.cos(2 * math.pi * i / sides), z + r * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
    if facing > 0:
        pts.reverse()
    bm = part.bm
    vs = [bm.verts.new(p) for p in pts]
    c = bm.verts.new((x, y, z))
    for i in range(sides):
        bm.faces.new([c, vs[(i + 1) % sides], vs[i]])


def exhaust(part, x, y, z, r, length, sides=16):
    """A hot exhaust spike behind a nozzle (opaque emissive, tapering to a point): the engines must read
    from the side and from below, not only from behind. The in-game engine FX add the soft glow + trail."""
    cylinder_x(part, x, x - length, y, z, r, r * 0.08, sides=sides, caps=(True, True))


def bar_x(part, x0, x1, a, b):
    """A bar along x whose rectangular section changes from a=(y0, y1, z0, z1) at x0 to b at x1."""
    ring = lambda x, r: [(x, r[0], r[2]), (x, r[1], r[2]), (x, r[1], r[3]), (x, r[0], r[3])]
    return loft(part, [ring(x0, a), ring(x1, b)])


def slab(part, planform, z0, z1):
    """A flat plate (wing) from an (x, y) planform polygon between two heights."""
    return prism(part, planform, z0, z1)


def fin(part, profile_xz, y, half_t, cant=0.0):
    """A vertical fin from an (x, z) profile at station y, half thickness half_t, canted outward by `cant`
    units per unit of height (sign follows y)."""
    sgn = 1 if y >= 0 else -1
    def ring(dy):
        return [(x, y + dy + sgn * cant * z, z) for x, z in profile_xz]
    bm = part.bm
    a = [bm.verts.new(p) for p in ring(-half_t)]
    b = [bm.verts.new(p) for p in ring(half_t)]
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([a[i], a[j], b[j], b[i]])
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)


def aim_camera(offset, dist, rise_deg=27.0, side=-0.25):
    """Point the PLAYER VIEW camera (hfov 80.7, the in-game framing) at a ship from below and to the side."""
    cam = bpy.data.objects.get('PLAYER VIEW')
    if cam is None:
        return
    o = Vector(offset)
    h = dist * math.cos(math.radians(rise_deg))
    u = dist * math.sin(math.radians(rise_deg))
    cam.location = o + Vector((side * h, -h, -u))
    cam.rotation_euler = (o - cam.location).to_track_quat('-Z', 'Y').to_euler()


def tube(part, pts, width, height=None, up=(0, 0, 1)):
    """A square-section beam along a polyline (neon lines). Joints overlap; ends are capped."""
    height = height or width
    up = Vector(up)
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts[:-1], pts[1:]):
        d = (b - a)
        if d.length < 1e-3:
            continue
        d.normalize()
        side = d.cross(up)
        if side.length < 1e-3:
            side = d.cross(Vector((0, 1, 0)))
        side.normalize()
        nup = side.cross(d).normalized()
        ext = d * (width * 0.5)          # overlap the joints a little so bends stay closed
        a2, b2 = a - ext, b + ext
        ring = lambda p: [p + side * (width / 2) + nup * (height / 2), p - side * (width / 2) + nup * (height / 2),
                          p - side * (width / 2) - nup * (height / 2), p + side * (width / 2) - nup * (height / 2)]
        loft(part, [ring(a2), ring(b2)])


def band(part, rail_a, rail_b, push, period=None, outward=None):
    """A flat single-sided strip lying between two rails (lists of points at the same stations), pushed
    out along the local face normal by `push` so it sits proud of the hull. Each quad faces AWAY from the
    x axis (the ship's spine), or along `outward` when given. UV u runs along the strip in `period`
    units (a tiling window texture), v across it."""
    bm = part.bm
    A = [Vector(p) for p in rail_a]
    B = [Vector(p) for p in rail_b]
    dist = 0.0
    for i in range(len(A) - 1):
        a0, a1, b0, b1 = A[i], A[i + 1], B[i], B[i + 1]
        n = (a1 - a0).cross(b0 - a0)
        if n.length < 1e-6:
            continue
        n.normalize()
        c = (a0 + a1 + b0 + b1) / 4
        ref = Vector(outward) if outward else Vector((0, c.y, c.z))
        flip = n.dot(ref) < 0
        if flip:
            n = -n
        off = n * push
        seg = (a1 - a0).length
        u0 = dist / period if period else 0
        u1 = (dist + seg) / period if period else 1
        dist += seg
        pts = [a0 + off, a1 + off, b1 + off, b0 + off]
        uvs = [(u0, 0), (u1, 0), (u1, 1), (u0, 1)]
        if flip:
            pts.reverse()
            uvs.reverse()
        f = bm.faces.new([bm.verts.new(tuple(p)) for p in pts])
        for loop, uv in zip(f.loops, uvs):
            loop[part.uv].uv = uv


def quad_facing(part, pts, normal, uvs=None):
    """One single-sided quad whose winding is fixed so it faces `normal`."""
    P = [Vector(p) for p in pts]
    n = (P[1] - P[0]).cross(P[2] - P[0])
    uvs = list(uvs or [(0, 0), (1, 0), (1, 1), (0, 1)])
    if n.dot(Vector(normal)) < 0:
        P.reverse()
        uvs.reverse()
    f = part.bm.faces.new([part.bm.verts.new(tuple(p)) for p in P])
    for loop, uv in zip(f.loops, uvs):
        loop[part.uv].uv = uv


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def light_box(part, c, s):
    """A small emissive block (running light). s = edge length."""
    box(part, c[0] - s / 2, c[0] + s / 2, c[1] - s / 2, c[1] + s / 2, c[2] - s / 2, c[2] + s / 2)


# ---- studio view ----------------------------------------------------------------------------------
def frame(objs, shading='RENDERED', from_below=True):
    """Frame these objects in every 3D view so the user watching the studio sees the new ship."""
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            sp = area.spaces.active
            sp.clip_start = 20
            sp.clip_end = 2.0e6
            sp.shading.type = shading
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            if region is None:
                continue
            with bpy.context.temp_override(window=win, area=area, region=region):
                bpy.context.view_layer.update()
                for o in list(bpy.context.view_layer.objects):
                    if o is not None:
                        o.select_set(False)
                for o in objs:
                    o.select_set(True)
                if objs:
                    bpy.context.view_layer.objects.active = objs[0]
                    bpy.ops.view3d.view_selected()
                    if from_below:                       # players mostly see the fleet from below
                        r3d = sp.region_3d
                        r3d.view_rotation = Euler((math.radians(118), 0, math.radians(35)), 'XYZ').to_quaternion()
                        r3d.view_distance *= 0.8
                for o in objs:
                    o.select_set(False)                  # no orange selection outline over the ship
