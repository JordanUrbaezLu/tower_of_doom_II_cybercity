"""Native export helpers (Blender + PyCoD). Corner normals come from Blender's own split-normal evaluation (the same
evaluation the NORMAL bake used), so the shipped tangent frame matches the baked atlas.

Native conventions (proven by tools/cyber_sword/06_bake_native.py + install_native.py): a native face lists its
corners in the reverse of Blender's order (0, 2, 1); native uv v is measured from the top (1 - Blender v).
Triangles that the xmesh converter would drop (repeated corners, an edge under MIN_EDGE, an altitude under
MIN_ALT - CLAUDE.md "the converter drops zero-area and needle triangles") are dropped HERE and counted, so the
exported triangle count is the compiled count.
"""
import copy, math
import bpy
import common

MIN_EDGE = 0.001
MIN_ALT = 0.0005


def needle(a, b, c):
    e = (math.dist(a, b), math.dist(b, c), math.dist(c, a))
    if min(e) < MIN_EDGE:
        return True
    u = [b[i] - a[i] for i in range(3)]; v = [c[i] - a[i] for i in range(3)]
    cr = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return math.sqrt(sum(x * x for x in cr)) / max(max(e), 1e-12) < MIN_ALT


def part_triangles(part, pack):
    """-> (verts [(x,y,z)], tris [[{v, n, uv}] * 3], dropped) for one emitter part in native conventions."""
    import emitter
    me = bpy.data.meshes.new('ws_export_tmp')
    try:
        me.from_pydata([tuple(v) for v in part.verts], [], [f[0] for f in part.faces])
        uv = me.uv_layers.new(name='UVMap')
        for poly, (ids, zone, uvs, key) in zip(me.polygons, part.faces):
            poly.use_smooth = not part.flat
            t = pack[key]
            for li, (u, v) in zip(poly.loop_indices, uvs):
                uv.data[li].uv = emitter.island_uv(t, u, v)
        if not part.flat:
            me.set_sharp_from_angle(angle=math.radians(part.smooth_angle))
        me.calc_loop_triangles()
        verts = [tuple(v.co) for v in me.vertices]
        tris = []; dropped = 0
        cn = me.corner_normals
        for tri in me.loop_triangles:
            a, b, c = (verts[me.loops[li].vertex_index] for li in tri.loops)
            if needle(a, b, c):
                dropped += 1; continue
            corners = []
            for li in (tri.loops[0], tri.loops[2], tri.loops[1]):
                n = cn[li].vector.normalized()
                if part.flat:
                    n = tri.normal.normalized()
                w = uv.data[li].uv
                corners.append(dict(v=me.loops[li].vertex_index, n=(n.x, n.y, n.z), uv=(w.x, 1.0 - w.y)))
            tris.append(corners)
        return verts, tris, dropped
    finally:
        bpy.data.meshes.remove(me)


def native_mesh(xmodel, name, verts, tris, material_id, mesh_id, bone=0, transform=None):
    """PyCoD mesh from (verts, tris); unused vertices compacted; every vertex rigid to `bone`."""
    used = sorted({c['v'] for t in tris for c in t})
    remap = {v: i for i, v in enumerate(used)}
    mesh = xmodel.Mesh(name)
    for v in used:
        p = verts[v] if transform is None else transform(verts[v])
        mesh.verts.append(xmodel.Vertex(tuple(p), [(bone, 1.0)]))
    for t in tris:
        f = xmodel.Face(mesh_id, material_id)
        f.indices = [xmodel.FaceVertex(remap[c['v']], tuple(c['n']), (1.0, 1.0, 1.0, 1.0), tuple(c['uv'])) for c in t]
        mesh.faces.append(f)
    return mesh


def source_mesh(xmodel, src_model, xm, mesh_id, material_ids, drop_face=None, bone_override=None, transform=None,
                material_override=None):
    """Copy a native source mesh exactly (positions, weights, corner normals/uvs/colours), remapping materials,
    optionally dropping faces (`drop_face(face, positions) -> True`) and needles; vertices compacted.
    Returns (mesh or None, stats)."""
    P = [v.offset for v in xm.verts]
    keep = []; stats = dict(degenerate=0, needle=0, removed=0)
    for f in xm.faces:
        ids = [c.vertex for c in f.indices]
        if len(set(ids)) < 3:
            stats['degenerate'] += 1; continue
        if drop_face is not None and drop_face(f, P):
            stats['removed'] += 1; continue
        if needle(P[ids[0]], P[ids[1]], P[ids[2]]):
            stats['needle'] += 1; continue
        keep.append(f)
    if not keep:
        return None, stats
    used = sorted({c.vertex for f in keep for c in f.indices})
    remap = {v: i for i, v in enumerate(used)}
    mesh = xmodel.Mesh(xm.name)
    for v in used:
        src = xm.verts[v]
        p = src.offset if transform is None else tuple(transform(src.offset))
        w = [(bone_override, 1.0)] if bone_override is not None else list(src.weights)
        mesh.verts.append(xmodel.Vertex(tuple(p), w))
    for f in keep:
        mat = material_override if material_override is not None else material_ids[src_model.materials[f.material_id].name]
        nf = xmodel.Face(mesh_id, mat)
        nf.indices = [xmodel.FaceVertex(remap[c.vertex], tuple(c.normal), tuple(c.color) if c.color else (1, 1, 1, 1),
                                        tuple(c.uv)) for c in f.indices]
        mesh.faces.append(nf)
    stats['triangles'] = len(keep)
    return mesh, stats


TIP_X, TIP_R = 39.62, 0.45


def tip_face(f, P):
    """The DG-2's pointed rod tip (x > 39.62, within 0.45 of the beam axis - enclosed by the lens housing cup, whose
    bore is >= 0.82 there, and the focusing crystal in front of it): the crystal replaces it. The LOD2 tip's vertices
    sit at radius 0.36-0.39."""
    return all(P[c.vertex][0] > TIP_X and math.hypot(P[c.vertex][1], P[c.vertex][2] - 3.1414) < TIP_R for c in f.indices)
