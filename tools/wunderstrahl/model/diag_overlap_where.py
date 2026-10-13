"""MCP diagnostic (read-only): where (x, y, z) a given emitter part intersects the DG-2 pipe mesh. PART='Conduit left'."""
import bpy, importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
importlib.reload(common)
from mathutils.bvhtree import BVHTree

PART = globals().get('PART', 'Conduit left')
bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'wunderstrahl.blend'))
scene = bpy.context.scene; deps = bpy.context.evaluated_depsgraph_get()
ob = scene.objects[PART]
src = next(o for o in scene.objects if o.type == 'MESH' and o.name.startswith('WS view') and ' pipe' in o.name)
ta = BVHTree.FromObject(ob, deps); tb = BVHTree.FromObject(src, deps)
ma = ob.evaluated_get(deps).to_mesh(); mb = src.evaluated_get(deps).to_mesh()
ma.calc_loop_triangles(); mb.calc_loop_triangles()
for ia, ib in ta.overlap(tb)[:60]:
    ca = sum((ma.vertices[v].co for v in ma.loop_triangles[ia].vertices), start=ma.vertices[0].co * 0) / 3
    cb = sum((mb.vertices[v].co for v in mb.loop_triangles[ib].vertices), start=mb.vertices[0].co * 0) / 3
    print('part tri at (%.2f %.2f %.2f)  source tri at (%.2f %.2f %.2f)' % (*ca, *cb))
