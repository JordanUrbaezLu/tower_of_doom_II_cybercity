"""MCP diagnostic (read-only): ray-probe the untouched DG-2 for the conduit route and emitter clearances.
Prints hits; changes nothing and saves nothing."""
import bpy, importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
importlib.reload(common)
from mathutils import Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'dg2_reference.blend'))
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()
trees = []
for ob in scene.objects:
    if ob.type == 'MESH' and ob.name.startswith('DG-2 view'):
        trees.append((ob.name, BVHTree.FromObject(ob, deps)))


def cast(origin, direction, maxd=60):
    best = None
    for name, t in trees:
        hit = t.ray_cast(Vector(origin), Vector(direction).normalized(), maxd)
        if hit[0] is not None and (best is None or hit[3] < best[3]):
            best = (hit[0], hit[1], name, hit[3])
    return best


print('--- top-down probes (z from 20 down): x, y -> hit z, mesh')
for y in (-1.2, -0.8, -0.4, 0.0, 0.4, 0.8, 1.2):
    row = []
    for x in range(14, 41, 1):
        h = cast((x, y, 20), (0, 0, -1))
        row.append('%d:%s' % (x, ('%.2f%s' % (h[0].z, h[2].split('|')[1].strip()[3:7])) if h else '-'))
    print('y %+.1f  ' % y + ' '.join(row))
print('--- side probes from +Y (y=20 -> -Y) at z: x -> hit y, mesh')
for z in (2.4, 3.0, 3.6, 4.2, 4.8):
    row = []
    for x in range(14, 41, 1):
        h = cast((x, 20, z), (0, -1, 0))
        row.append('%d:%s' % (x, ('%.2f%s' % (h[0].y, h[2].split('|')[1].strip()[3:7])) if h else '-'))
    print('z %.1f  ' % z + ' '.join(row))
print('--- glass tube front end cap: radial probes at x=18.3..19.5 toward the axis')
for x in (18.2, 18.6, 19.0, 19.5, 20.0):
    for ang_y, ang_z in ((0, 1), (0.7, 0.7), (1, 0), (-0.7, 0.7), (-1, 0)):
        o = Vector((x, ang_y * 6, 3.34 + ang_z * 6))
        h = cast(o, Vector((x, 0, 3.34)) - o)
        print('x %.1f dir(%+.1f,%+.1f) -> %s' % (x, ang_y, ang_z, ('(%.2f %.2f %.2f) %s' % (h[0].x, h[0].y, h[0].z, h[2])) if h else '-'))
print('WS_DIAG_SURFACE_DONE')
