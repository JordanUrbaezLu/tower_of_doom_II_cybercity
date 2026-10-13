"""MCP diagnostic (read-only): radial rays from the beam axis outward, every 3 degrees, at x stations through the
emitter zone; prints the nearest hit radius per angle sector (the claws, rails and cage) against the source meshes."""
import bpy, importlib, sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
importlib.reload(common)
from mathutils import Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'dg2_reference.blend'))
scene = bpy.context.scene; deps = bpy.context.evaluated_depsgraph_get()
trees = [BVHTree.FromObject(ob, deps) for ob in scene.objects if ob.type == 'MESH' and ob.name.startswith('DG-2 view')]
AXZ = 3.1414
for x in [35.6, 36.0, 36.1, 36.4, 36.7, 37.0, 37.5, 37.8, 38.1, 38.4, 38.6, 38.9, 39.2, 39.5, 40.0]:
    row = []
    minr = 9.9
    for k in range(120):
        a = 2 * math.pi * k / 120
        d = Vector((0, math.cos(a), math.sin(a)))
        o = Vector((x, 0.0, AXZ)) + d * 0.62     # start outside the central rod (r <= 0.57)
        best = None
        for t in trees:
            h = t.ray_cast(o, d, 6.0)
            if h[0] is not None and (best is None or h[3] < best):
                best = h[3]
        r = .62 + best if best is not None else 9.9
        row.append(r); minr = min(minr, r)
    sectors = []
    for s in range(0, 120, 6):
        sectors.append('%3d:%4.2f' % (s * 3, min(row[s:s + 6])))
    print('x %.1f  min %.2f  | %s' % (x, minr, ' '.join(sectors)))
print('WS_DIAG_CLAWS_DONE')
