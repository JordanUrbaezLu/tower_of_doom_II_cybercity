"""MCP diagnostic (read-only): vertical ray stacks over candidate conduit lanes and radial stacks around the emitter
band. For each probe it prints every surface hit (entry/exit pairs), so free corridors can be chosen exactly."""
import bpy, importlib, sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
importlib.reload(common)
from mathutils import Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'dg2_reference.blend'))
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()
trees = [(ob.name.split('|')[1].strip()[3:8], BVHTree.FromObject(ob, deps)) for ob in scene.objects
         if ob.type == 'MESH' and ob.name.startswith('DG-2 view')]


def stack(origin, direction, maxd=12.0):
    """All hits along a ray (re-cast just past each hit)."""
    d = Vector(direction).normalized(); o = Vector(origin); hits = []; travelled = 0.0
    for _ in range(40):
        best = None
        for name, t in trees:
            h = t.ray_cast(o, d, maxd - travelled)
            if h[0] is not None and (best is None or h[3] < best[1]):
                best = (h[0], h[3], name)
        if best is None:
            break
        travelled += best[1] + 1e-3
        hits.append((round(travelled, 2), best[2]))
        o = best[0] + d * 1e-3
        if travelled >= maxd:
            break
    return hits


LANE_Y = float(globals().get('LANE_Y', '0.5'))
print('--- vertical stacks at y=%+.2f (from z=8 down): x -> [z of each hit]' % LANE_Y)
for i in range(0, 81):
    x = 17.0 + i * 0.25
    for sy in (1, -1):
        hs = stack((x, sy * LANE_Y, 8.0), (0, 0, -1), 6.0)
        zs = [round(8.0 - h[0], 2) for h in hs]
        if sy == 1:
            row = 'x %5.2f  +y %-46s' % (x, ' '.join('%.2f%s' % (z, h[1][0]) for z, h in zip(zs, hs)))
        else:
            row += ' -y ' + ' '.join('%.2f%s' % (z, h[1][0]) for z, h in zip(zs, hs))
    print(row)
print('WS_DIAG_LANES_DONE')
