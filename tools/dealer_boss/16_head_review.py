"""16: head close-ups of BOTH mask states (EEVEE): three cameras aimed at the POSED head bone along the face's
bind direction (the master is usually left in a levitating pose, so the fixed studio cameras miss the head).
-> $TOD_REVIEW_OUT or art/dealer_boss/review/head/ as head_state<1|2>_<front|quarter|low>.png"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
import os
OUTDIR = Path(os.environ.get('TOD_REVIEW_OUT') or (ART / 'review' / 'head')); OUTDIR.mkdir(parents=True, exist_ok=True)
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 32
scene.render.resolution_x = 1400; scene.render.resolution_y = 1100; scene.render.resolution_percentage = 100
scene.render.film_transparent = False
coll('91').hide_render = True; coll('00').hide_render = True
def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    ob = bpy.data.objects.new(name, cd); scene.collection.objects.link(ob)
    ob.location = loc
    d = (Vector(target) - Vector(loc)).normalized()
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob
# the master may be left in a posed/levitating frame: aim at the POSED head bone, along its own forward axis
pb = RIG.pose.bones['j_head']
hm = RIG.matrix_world @ pb.matrix
hp = hm.to_translation()
rest = RIG.data.bones['j_head'].matrix_local.to_3x3()   # bind: the face looks down world +X
R = hm.to_3x3() @ rest.inverted()
fwd = (R @ Vector((1, 0, 0))).normalized(); left = (R @ Vector((0, 1, 0))).normalized(); up = (R @ Vector((0, 0, 1))).normalized()
tgt = hp + fwd * 7 + up * 1.5
print('HEAD', list(hp), 'fwd', list(fwd))
cams = {'front': cam('REV front', tgt + fwd * 40 - left * 4 + up * 1.5, tgt, 60),
        'quarter': cam('REV quarter', tgt + fwd * 30 + left * 24 + up * 6, tgt, 55),
        'low': cam('REV low', tgt + fwd * 36 - left * 20 - up * 10, tgt, 55)}
for state in (1, 2):
    review_state(state)
    for k, c in cams.items():
        scene.camera = c
        scene.render.filepath = str(OUTDIR / ('head_state%d_%s.png' % (state, k)))
        bpy.ops.render.render(write_still=True)
review_state(1)
print(json.dumps({'done': sorted(p.name for p in OUTDIR.glob('head_*.png'))}))
