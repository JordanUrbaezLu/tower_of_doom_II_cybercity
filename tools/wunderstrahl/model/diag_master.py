"""MCP diagnostic: render the authoring master (procedural emitter previews + step-03 surfaces) to
tmp/wunderstrahl/scratch for design iteration. Saves nothing else. VIEWS='a,b' picks views (default a set)."""
import bpy, importlib, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, blendlib, views
for m in (common, blendlib, views):
    importlib.reload(m)
from mathutils import Matrix

bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'wunderstrahl.blend'))
scene = bpy.context.scene
blendlib.setup_render(scene, samples=int(globals().get('SAMPLES', '64')), glare=globals().get('GLARE', '1') == '1')
names = globals().get('VIEWS', 'quarter_left,lens_close,lens_front,profile_left').split(',')
tag = globals().get('TAG', 'master')
for name in names:
    if name == 'first_person':
        continue
    loc, tgt, lens, ortho, res = views.VIEWS[name]
    scene.render.resolution_x, scene.render.resolution_y = res
    cam = bpy.data.objects.get('Review | ' + name) or blendlib.camera('Review | ' + name, loc, tgt, lens=lens or 50, ortho=ortho)
    t = time.time(); blendlib.render(scene, cam, common.SCRATCH / ('%s_%s.png' % (tag, name)))
    print('WS_DIAG_RENDER', name, round(time.time() - t, 1), flush=True)
if 'first_person' in names:
    # quick first-person check: every Wunderstrahl object moved rigidly by tag_weapon's idle-frame pose
    view = common.load_model(common.SRC_VIEW)
    clip = common.load_anim(common.SRC_XANIM / 'vm_dg2_idle.xanim_bin')
    skin = blendlib.pose_from_clip(view, clip, 0)
    for ob in scene.objects:
        if ob.type == 'MESH' and (ob.name.startswith('WS view') or ob.get('ws_part')):
            ob.matrix_world = skin[0] @ ob.matrix_world
    blendlib.studio(scene, (30, -14, -10), scale=.8)
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    cam = blendlib.camera('Review | first_person', (0, 0, 0), (100, 0, 0), lens=blendlib.fp_lens())
    blendlib.render(scene, cam, common.SCRATCH / ('%s_first_person.png' % tag))
    print('WS_DIAG_RENDER first_person', flush=True)
