"""09: prove the skinning - pose the Dealer with real Keeper clips and render.

For each (clip, frame) the rig takes the clip's pose, the hero and front cameras
render to art/dealer_boss/review/pose_<clip>_f<frame>_<cam>.png, then the rig
returns to the bind pose and the clip's action is removed (nothing is exported).
Globals: POSES = [('ai_zm_dlc4_keeper_prtctr_walk', 40), ...]
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
import importlib.util
spec = importlib.util.spec_from_file_location('dealer_anim_preview', str(Path(__file__).with_name('anim_preview.py')))
ap = importlib.util.module_from_spec(spec); spec.loader.exec_module(ap)
OUTDIR = ART / 'review'; OUTDIR.mkdir(exist_ok=True)
poses = globals().get('POSES', [('ai_zm_dlc4_keeper_prtctr_walk', 40), ('ai_zm_dlc4_keeper_prtctr_sprint', 20),
                                ('ai_zm_dlc4_enslaved_keeper_attack_v1', 25), ('ai_zm_dlc4_keeper_prtctr_idle_attack_up', 30)])
cams = globals().get('CAMS', ['01', '02'])
try:
    scene.eevee.taa_render_samples = 24
except Exception:
    pass
ghost = coll('91'); rigc = coll('00')
ghost.hide_render = True; rigc.hide_render = True
out = []
for clip, frame in poses:
    try:
        path = ap.find_clip(clip)
    except FileNotFoundError:
        out.append('MISSING ' + clip); continue
    ap.pose_frame(RIG, path, frame)
    bpy.context.view_layer.update()
    for ob in scene.objects:
        if ob.type == 'CAMERA' and ob.name.startswith('CAM ') and ob.name[4:6] in cams:
            scene.camera = ob
            scene.render.filepath = str(OUTDIR / ('pose_%s_f%d_cam%s.png' % (clip.replace('ai_zm_dlc4_', ''), frame, ob.name[4:6])))
            bpy.ops.render.render(write_still=True)
            out.append(scene.render.filepath)
    ap.rest_pose(RIG)
scene.frame_set(1)
scene.camera = bpy.data.objects['CAM 01 | hero three-quarter']
print(json.dumps({'stage': 'pose_check', 'renders': out}))
