"""MCP step 02: the BEFORE renders - the untouched DG-2 from the matched review views (art/wunderstrahl/review/).

Set RENDER_SET before sending (a one-line prepend) to split the work under the 180 s MCP answer window:
  RENDER_SET = 'main'   -> quarter_left, quarter_right, profile_left
  RENDER_SET = 'detail' -> lens_close, lens_front, top, first_person
"""
import bpy, importlib, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, blendlib, views, review
for m in (common, blendlib, views, review):
    importlib.reload(m)

RENDER_SET = globals().get('RENDER_SET', 'main')
bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'dg2_reference.blend'))
scene = bpy.context.scene
device = blendlib.setup_render(scene, samples=96, glare=True)
common.REVIEW.mkdir(parents=True, exist_ok=True)
for ob in scene.objects:
    if ob.type == 'EMPTY':
        ob.hide_render = True
names = {'main': ['quarter_left', 'quarter_right', 'profile_left'],
         'detail': ['lens_close', 'lens_front', 'top']}[RENDER_SET]
# The review views show the gun as players see it: posed by idle frame 0 with tag_weapon held at its bind place, the
# reload bracket left out (the bind pose floats it under the gun; every non-reload clip parks it behind the camera).
# The blend's own bind-pose meshes stay untouched (this step never saves the blend).
view = common.load_model(common.SRC_VIEW)
mats = {m.name: bpy.data.materials['DG-2 original | ' + m.name] for m in view.materials}
idle = common.load_anim(common.SRC_XANIM / 'vm_dg2_idle.xanim_bin')
src = [ob for ob in scene.objects if ob.type == 'MESH']
for ob in src:
    ob.hide_render = True
posed = blendlib.collection('REVIEW | DG-2 posed (idle frame 0, tag_weapon held)')
for ob in list(posed.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
skin = blendlib.hold_bone(view, blendlib.pose_from_clip(view, idle, 0))
clip_bone = [b.name for b in view.bones].index('tag_clip')   # the reload bracket: parked behind the camera in play
for i, xm in enumerate(view.meshes):
    blendlib.mesh_from_xmesh('Posed DG-2 %02d' % i, view, xm, mats, posed, skin=skin, skip_bones=[clip_bone])
review.render_set(scene, names, 'before', common.REVIEW)

if RENDER_SET == 'detail':
    posed.hide_render = True

    def build(skin_for, coll):
        sk = skin_for(view)
        for i, xm in enumerate(view.meshes):
            blendlib.mesh_from_xmesh('FP DG-2 %02d' % i, view, xm, mats, coll, skin=sk)
    coll = review.first_person(build, common.SRC_XANIM / 'vm_dg2_idle.xanim_bin', 'REVIEW | first person (idle frame 0)')
    blendlib.studio(scene, (30, -14, -10), scale=.8)
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    cam = blendlib.camera('Review | first_person', (0, 0, 0), (100, 0, 0), lens=blendlib.fp_lens())
    t = time.time()
    blendlib.render(scene, cam, common.REVIEW / 'before_first_person.png', 96)
    print('WS_RENDERED before first_person', round(time.time() - t, 1), 's', flush=True)
print('WS_02_REFERENCE', RENDER_SET, 'device', device, flush=True)
