"""MCP diagnostic (read-only): every emitter level - part and triangle counts, reach, the far-LOD claws, the face
winding of the new parts (outward vs inward) and the level-0 atlas density."""
import sys, math, pathlib, importlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import emitter
importlib.reload(emitter)
from mathutils import Vector
for lv in range(8):
    parts = emitter.build(lv)
    claws = emitter.far_claws(lv)
    tris = sum(len(ids) - 2 for p in parts for ids, z, u, k in p.faces)
    ctris = sum(len(ids) - 2 for p in claws for ids, z, u, k in p.faces)
    rmax = max(math.hypot(v.y, v.z - emitter.AXZ) for p in parts for v in p.verts)
    xmax = max(v.x for p in parts for v in p.verts)
    print('level', lv, 'parts', len(parts), 'tris', tris, 'far claws', len(claws), ctris, 'rmax %.3f xmax %.3f' % (rmax, xmax))


def face_normal(p, ids):
    a, b, c = p.verts[ids[0]], p.verts[ids[1]], p.verts[ids[2]]
    return (b - a).cross(c - a)


for p in emitter.build(0):
    if not (p.name.startswith(('Focusing crystal', 'Claw ferrule 0', 'Hub bolt 0', 'Tie nut 0-0', 'Focusing ring spoke 0'))):
        continue
    if p.name.startswith('Focusing crystal'):
        out = inw = 0
        cen_all = sum(p.verts, Vector()) / len(p.verts)
        for ids, z, u, k in p.faces:
            c = sum((p.verts[i] for i in ids), Vector()) / len(ids)
            n = face_normal(p, ids)
            (out := out + 1) if n.dot(c - Vector((c.x, 0, emitter.AXZ)) + Vector((c.x - cen_all.x, 0, 0))) > 0 else (inw := inw + 1)
        us = [uv[0] for ids, z, uvs, k in p.faces for uv in uvs]
        print('%-22s faces %4d (tris %d) out %d in %d  u %.3f..%.3f island %s' % (p.name, len(p.faces), sum(len(f[0]) - 2 for f in p.faces), out, inw, min(us), max(us), p.islands))
    else:
        print('%-22s faces %4d islands %s' % (p.name, len(p.faces), {k: tuple(round(x, 3) for x in v) for k, v in p.islands.items()}))
isl = {k: v for p in emitter.build(0) for k, v in p.islands.items()}
pack, s = emitter.shelf_pack(isl, margin_px=10, size=2048)
print('islands', len(isl), 'px/inch', round(s * 2048, 1))
