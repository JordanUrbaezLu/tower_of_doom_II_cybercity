"""MCP diagnostic (read-only): triangle-level intersections between every level-0 emitter part and the DG-2 meshes
(BVH overlap), so intended seating (ring 1 around the copper cage ring and claw roots, glands on the cap ridge,
standoffs on what they grip, ferrules into ring 1) can be told apart from accidental clipping."""
import bpy, importlib, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
importlib.reload(common)
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'wunderstrahl.blend'))
scene = bpy.context.scene; deps = bpy.context.evaluated_depsgraph_get()
src = [(ob.name, BVHTree.FromObject(ob, deps)) for ob in scene.objects if ob.type == 'MESH' and ob.name.startswith('WS view')]
parts = [ob for ob in scene.objects if ob.get('ws_part')]
report = {}
for ob in sorted(parts, key=lambda o: o.name):
    t = BVHTree.FromObject(ob, deps)
    hits = {}
    for name, s in src:
        pairs = t.overlap(s)
        if pairs:
            hits[name.split('|')[1].strip()] = len(pairs)
    if hits:
        report[ob.name] = hits
# emitter parts against each other (only the unexpected ones matter; tie rods/nuts/bosses seat into rings by design)
for k, v in sorted(report.items()):
    print('%-38s %s' % (k, json.dumps(v)))
common.write_json(common.SCRATCH / 'overlap_report.json', report)
print('WS_DIAG_OVERLAP parts with contacts:', len(report), 'of', len(parts))
