"""Shared review rendering for the before (DG-2) and after (Wunderstrahl) passes: same studio, same cameras."""
import bpy, importlib, time
from pathlib import Path
import common, blendlib, views
importlib.reload(views)

MT = Path('C:/BO3Tools/TOD2Cybercity/model_export')
HANDS = MT / 't7_characters/viewmodels/c_t7_mp_warrior_viewhands.XMODEL_BIN'   # read-only, review only


def hide_all_meshes():
    for ob in bpy.context.scene.objects:
        if ob.type in ('MESH', 'CURVE'):
            ob.hide_render = True


def first_person(source_objects_builder, idle_clip_path, coll_name, ads_clip_path=None):
    """Build a posed copy of the weapon via `source_objects_builder(skin_for, coll)` - skin_for(model) returns the
    skinning transforms for that model - plus the review viewhands, in their own collection. The pose is idle frame
    0, or with `ads_clip_path` the ADS pose (idle + the last frame of ads_base_up's torso). Returns the collection."""
    coll = blendlib.collection(coll_name)
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    clip = common.load_anim(idle_clip_path)
    ads = common.load_anim(ads_clip_path) if ads_clip_path else None

    def skin_for(model):
        return blendlib.ads_skin(model, clip, ads) if ads else blendlib.pose_from_clip(model, clip, 0)
    source_objects_builder(skin_for, coll)
    if HANDS.exists():
        hands = common.load_model(HANDS)
        glove = blendlib.flat_material('Review viewhands (neutral glove, not shipped)', (38, 36, 34), rough=.62)
        mats = {m.name: glove for m in hands.materials}
        skin = skin_for(hands)
        for i, xm in enumerate(hands.meshes):
            blendlib.mesh_from_xmesh('Review viewhands %02d' % i, hands, xm, mats, coll, skin=skin)
    return coll


def render_set(scene, names, prefix, out_dir, samples=96, glare=True, centre=None):
    out = []
    blendlib.studio(scene, centre or views.CENTRE)
    for name in names:
        loc, target, lens, ortho, res = views.VIEWS[name]
        scene.render.resolution_x, scene.render.resolution_y = res
        cam = blendlib.camera('Review | ' + name, loc, target, lens=lens or 50, ortho=ortho)
        t = time.time()
        out.append(blendlib.render(scene, cam, Path(out_dir) / ('%s_%s.png' % (prefix, name)), samples))
        print('WS_RENDERED', prefix, name, round(time.time() - t, 1), 's', flush=True)
    return out
