"""MCP step 07: review renders FROM THE EXPORTED BINARIES and the shipped maps (art/wunderstrahl/review/).

Every mesh is read back from model_export/tod_wunderstrahl/*.XMODEL_BIN; every material is the approximate native
preview of materials.py (the registry the staged GDT is generated from) on the actual _images PNGs, the emitter on
its baked atlas. RENDER_SET picks a batch (each fits the 180 s MCP answer window):
  views   quarter_left, quarter_right, profile_left, top, lens_close, lens_front (+ saves native_preview.blend);
          the view rig posed by idle frame 0 with tag_weapon held at its bind place (no floating clip part)
  fp      first person (view rig posed by the REAL idle clip, review viewhands) + no-bloom checks
  ads     aiming down the sights: idle + the last frame of the REAL ads_base_up clip, ~65 degree ADS field of view
  world   the third-person model at play distance + the seven-LOD lineup
  pickup  the gold drop alone + beside the stock Death Machine and Zombie Blood drops (same stand-in material)
Previews only: not BO3 lighting, probes, exposure or bloom. The native look is the user's playtest.
"""
import bpy, importlib, math, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, blendlib, materials, views, review
for m in (common, blendlib, materials, views, review):
    importlib.reload(m)
from mathutils import Vector, Matrix

RENDER_SET = globals().get('RENDER_SET', 'views')
SAMPLES = int(globals().get('SAMPLES', '96'))
OUTDIR = common.REVIEW
IMG = common.IMG
scene = blendlib.clear_scene()
scene.name = 'Wunderstrahl | native round-trip preview'
device = blendlib.setup_render(scene, samples=SAMPLES, glare=True)


def mp(name):
    return None if name is None or name.startswith('$') else IMG / (name + '.png')


def preview(name):
    m = materials.MATERIALS[name]; maps = m['maps']
    if m['kind'] == 'glass':
        return blendlib.fullspec('WS native | ' + name, mp(maps['c']), None, mp(maps['g']), mp(maps['n']), m['gloss'],
                                 spec_const=(.22, .22, .22), alpha=(1.0, 0.0))
    return blendlib.fullspec('WS native | ' + name, mp(maps['c']), mp(maps['s']), mp(maps['g']), mp(maps['n']), m['gloss'],
                             mp(maps.get('e')) if m['kind'] == 'emissive' else None, m.get('scale', 0) * materials.PREVIEW_EMIT,
                             e_falloff=m.get('falloff', 0.0))


MATS = {n: preview(n) for n in materials.MATERIALS}
GOLD = blendlib.flat_material('Drop stand-in (stock mtl_x2icon_gold is used in game)', (242, 178, 72), rough=.24, metal=1.0)
MATS[common.DROP_MATERIAL] = GOLD


def build(path, coll, prefix, skin=None, offset=None, mats=None, skip_bones=None):
    model = common.load_model(path)
    if skin is not None and len(skin) != len(model.bones):
        raise ValueError('skin has %d transforms for %d bones' % (len(skin), len(model.bones)))
    lookup = mats or MATS
    obs = []
    for i, xm in enumerate(model.meshes):
        ob = blendlib.mesh_from_xmesh('%s %02d' % (prefix, i), model, xm, lookup, coll, skin=skin, skip_bones=skip_bones)
        if offset is not None:
            ob.location = offset
        obs.append(ob)
    return model, obs


def frame_render(name, path=None, samples=None):
    loc, tgt, lens, ortho, res = views.VIEWS[name]
    scene.render.resolution_x, scene.render.resolution_y = res
    cam = blendlib.camera('Review | ' + name, loc, tgt, lens=lens or 50, ortho=ortho)
    t = time.time()
    blendlib.render(scene, cam, path or OUTDIR / ('wunderstrahl_%s.png' % name), samples)
    print('WS_RENDERED', name, round(time.time() - t, 1), 's', flush=True)


OUTDIR.mkdir(parents=True, exist_ok=True)
if RENDER_SET == 'views':
    # Posed by idle frame 0 with tag_weapon held; the DG-2's reload bracket (tag_clip) is left out of these
    # gun-alone views: every clip but the reload parks it behind the camera, where no player sees it.
    coll = blendlib.collection('NATIVE | tod2_ws_view_LOD0 (exported binary, idle frame 0, tag_weapon held)')
    vm = common.load_model(common.OUT / 'tod2_ws_view_LOD0.XMODEL_BIN')
    idle = common.load_anim(common.XOUT / 'tod2_ws_vm_idle.xanim_bin')
    build(common.OUT / 'tod2_ws_view_LOD0.XMODEL_BIN', coll, 'tod2_ws_view',
          skin=blendlib.hold_bone(vm, blendlib.pose_from_clip(vm, idle, 0)),
          skip_bones=[[b.name for b in vm.bones].index('tag_clip')])
    blendlib.studio(scene, views.CENTRE)
    for name in ('quarter_left', 'quarter_right', 'profile_left', 'top', 'lens_close', 'lens_front'):
        frame_render(name)
    for name in ('quarter_left', 'lens_close'):
        blendlib.set_glare(scene, False)
        frame_render(name, OUTDIR / ('wunderstrahl_%s_nobloom.png' % name))
        blendlib.set_glare(scene, True)
    scene['preview_limit'] = 'Exported binary + shipped maps; approximate fullspec preview, not BO3 lighting'
    bpy.ops.wm.save_as_mainfile(filepath=str(common.ART / 'native_preview.blend'))
elif RENDER_SET in ('fp', 'ads'):
    view = common.load_model(common.OUT / 'tod2_ws_view_LOD0.XMODEL_BIN')

    def builder(skin_for, coll):
        skin = skin_for(view)
        for i, xm in enumerate(view.meshes):
            blendlib.mesh_from_xmesh('FP tod2_ws_view %02d' % i, view, xm, MATS, coll, skin=skin)
    ads = RENDER_SET == 'ads'
    review.first_person(builder, common.XOUT / 'tod2_ws_vm_idle.xanim_bin',
                        'REVIEW | ' + ('aim down sights (idle + ads_base_up end)' if ads else 'first person (idle frame 0)'),
                        ads_clip_path=(common.XOUT / 'tod2_ws_vm_ads_base_up.xanim_bin') if ads else None)
    blendlib.studio(scene, (30, -14, -10) if not ads else (24, 0, -5), scale=.8)
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    cam = blendlib.camera('Review | ' + RENDER_SET, (0, 0, 0), (100, 0, 0), lens=blendlib.fp_lens(hfov=65.0 if ads else blendlib.FP_HFOV))
    if ads:
        blendlib.render(scene, cam, OUTDIR / 'wunderstrahl_ads.png')
        print('WS_RENDERED ads', flush=True)
    else:
        blendlib.render(scene, cam, OUTDIR / 'wunderstrahl_first_person.png')
        blendlib.set_glare(scene, False)
        blendlib.render(scene, cam, OUTDIR / 'wunderstrahl_first_person_nobloom.png')
        print('WS_RENDERED first_person (+ no bloom)', flush=True)
elif RENDER_SET == 'world':
    coll = blendlib.collection('NATIVE | tod2_ws_world LOD0')
    build(common.OUT / 'tod2_ws_world_LOD0.XMODEL_BIN', coll, 'tod2_ws_world_LOD0')
    blendlib.studio(scene, views.CENTRE)
    loc, tgt, lens, ortho, res = views.WORLD_VIEW
    scene.render.resolution_x, scene.render.resolution_y = res
    cam = blendlib.camera('Review | world', loc, tgt, lens=lens)
    blendlib.render(scene, cam, OUTDIR / 'wunderstrahl_world.png')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    line = blendlib.collection('NATIVE | world LOD lineup')
    for lod in range(7):
        build(common.OUT / ('tod2_ws_world_LOD%d.XMODEL_BIN' % lod), line, 'LOD%d' % lod, offset=(0, 0, -lod * 13.0))
    blendlib.studio(scene, (15, 0, -39), scale=1.6)
    scene.render.resolution_x, scene.render.resolution_y = 1000, 1700
    cam = blendlib.camera('Review | lod lineup', (14.8, 210.0, -38.0), (14.8, 0.0, -38.0), ortho=100.0)
    blendlib.render(scene, cam, OUTDIR / 'wunderstrahl_world_lods.png')
    print('WS_RENDERED world + lods', flush=True)
elif RENDER_SET == 'pickup':
    coll = blendlib.collection('NATIVE | tod2_ws_pickup')
    build(common.OUT / 'tod2_ws_pickup_LOD0.XMODEL_BIN', coll, 'tod2_ws_pickup')
    blendlib.studio(scene, (0, 0, 0), scale=.7)
    w = scene.world.node_tree.nodes['Background']; w.inputs[0].default_value = (.05, .05, .055, 1); w.inputs[1].default_value = 1.2
    scene.render.resolution_x, scene.render.resolution_y = 1400, 1000
    cam = blendlib.camera('Review | pickup', (38.0, 62.0, 22.0), (0, 0, 0), lens=55)
    blendlib.render(scene, cam, OUTDIR / 'wunderstrahl_pickup.png')
    MT = Path('C:/BO3Tools/TOD2Cybercity/model_export')
    refs = [(MT / 'props_zombie/pickups/zombie_pickup_minigun.XMODEL_BIN', 'Death Machine drop (stock)', -56.0),
            (MT / '_NSZ/powerups/zombie_blood.XMODEL_BIN', 'Zombie Blood drop', 44.0)]
    gold_all = {}
    for path, label, dx in refs:
        if path.exists():
            model = common.load_model(path)
            gold_all = {m.name: GOLD for m in model.materials}
            rc = blendlib.collection('REFERENCE | ' + label)
            for i, xm in enumerate(model.meshes):
                ob = blendlib.mesh_from_xmesh('%s %02d' % (label, i), model, xm, gold_all, rc)
                ob.location = (dx, 0, 0)
    blendlib.studio(scene, (0, 0, 0), scale=1.4)
    w = scene.world.node_tree.nodes['Background']; w.inputs[0].default_value = (.05, .05, .055, 1); w.inputs[1].default_value = 1.2
    scene.render.resolution_x, scene.render.resolution_y = 1800, 800
    cam = blendlib.camera('Review | drop lineup', (-6.0, 190.0, 34.0), (-6.0, 0.0, 0.0), lens=50)
    blendlib.render(scene, cam, OUTDIR / 'wunderstrahl_pickup_lineup.png')
    print('WS_RENDERED pickup + lineup', flush=True)
print('WS_07_RENDER', RENDER_SET, 'device', device, flush=True)
