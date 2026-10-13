"""08: review renders from every studio camera (EEVEE, fast) -> art/dealer_boss/review/.

Optional globals before exec: CAMS = ['01', '04'] (subset), SAMPLES = 32, TAG = 'pass2', STATE = 2 (the cracked mask; 1 = masked).
The Keeper ghost and the rig are hidden for renders; the viewport is left as the user had it.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
OUTDIR = ART / 'review'; OUTDIR.mkdir(exist_ok=True)
cams = globals().get('CAMS', ['01', '02', '03', '04', '05', '06'])
tag = globals().get('TAG', scene.get('dealer_stage', 'review'))
state = int(globals().get('STATE', 1))
review_state(state)
if state == 2 and 'TAG' not in globals():
    tag += '_state2'
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
try:
    scene.eevee.taa_render_samples = int(globals().get('SAMPLES', 32))
    scene.eevee.use_raytracing = True
except Exception:
    pass
scene.render.film_transparent = False
ghost = coll('91'); rigc = coll('00')
ghost_hidden, rig_hidden = ghost.hide_render, rigc.hide_render
ghost.hide_render = True; rigc.hide_render = True
out = {}
for ob in scene.objects:
    if ob.type == 'CAMERA' and ob.name.startswith('CAM ') and ob.name[4:6] in cams:
        scene.camera = ob
        name = 'cam%s_%s_%s.png' % (ob.name[4:6], ob.name.split('| ')[1].replace(' ', '_'), tag)
        scene.render.filepath = str(OUTDIR / name)
        bpy.ops.render.render(write_still=True)
        out[ob.name] = scene.render.filepath
ghost.hide_render = ghost_hidden; rigc.hide_render = rig_hidden
review_state(1)
scene.camera = bpy.data.objects['CAM 01 | hero three-quarter']
print(json.dumps({'stage': 'review', 'tag': tag, 'renders': out}))
