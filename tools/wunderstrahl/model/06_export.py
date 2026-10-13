"""MCP step 06: write the Wunderstrahl's native models into model_export/tod_wunderstrahl (+ the clips).

  tod2_ws_view_LOD0          the DG-2 view meshes (exact positions, bone weights, corner normals/uvs; materials
                             remapped; the pointed rod tip removed) + the emitter at level 0, rigid to tag_weapon.
                             Bones: EXACTLY the DG-2's 12 (names, parents, rest offsets and matrices copied).
  tod2_ws_world_LOD0..6      the DG-2's own seven nearest world LODs + the emitter at levels 1,3,4,5,6,6,7; at the
                             levels with swept far-LOD claws (5, 6) the DG-2's broken claw fragments are dropped and
                             the claws ride in their own mesh on a copper patch of mtl_tod2_ws_coil.
                             Bones: the DG-2 world rig's 4.
  tod2_ws_pickup_LOD0..1     the gold power-up drop: world LOD2 / LOD3 geometry + the emitter at levels 2 / 6,
                             one material slot (stock mtl_x2icon_gold), centred on the gun's middle and scaled 0.8 so it
                             matches the Death Machine drop it shares a slot with (42 units long), one bone tag_origin.
  tod2_ws_skeleton           the DG-2 animation skeleton, byte-identical copy (the clips' model).
  xanim_export/tod_wunderstrahl/tod2_ws_vm_<suffix>.xanim_bin   the 28 vm_dg2 clips, byte-identical copies.
The emitter UVs come from engine_kit/atlas.json (the layout the atlas was baked against); a level-0 rebuild must
reproduce that layout exactly or the step refuses. Records: art/wunderstrahl/engine_kit/models.json.
"""
import bpy, copy, importlib, math, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, emitter, exportlib, materials
for m in (common, emitter, exportlib, materials):
    importlib.reload(m)
xmodel, xanim = common.pycod()

common.OUT.mkdir(parents=True, exist_ok=True); common.XOUT.mkdir(parents=True, exist_ok=True)
atlas = common.read_json(common.KIT / 'atlas.json')
pack = {k: tuple(v['transform']) for k, v in atlas['islands'].items()}
level0 = {k: tuple(round(x, 4) for x in v) for p in emitter.build(0) for k, v in p.islands.items()}
assert level0 == {k: tuple(v['size_in']) for k, v in atlas['islands'].items()}, 'emitter layout drifted from the baked atlas'

view = common.load_model(common.SRC_VIEW)
worlds = [common.load_model(p) for p in common.SRC_WORLD]
ORDER = ['mtl_tod2_ws_stock', 'mtl_tod2_ws_coil', 'mtl_tod2_ws_body', 'mtl_tod2_ws_glass', 'mtl_tod2_ws_frame',
         'mtl_tod2_ws_glow', 'mtl_tod2_ws_core', 'mtl_tod2_ws_bulb', common.EMITTER_MATERIAL]
WORLD_LEVEL = {0: 1, 1: 3, 2: 4, 3: 5, 4: 6, 5: 6, 6: 7}
# The drop is seen up close (players walk onto it): LOD0 comes from world LOD2, the lowest DG-2 LOD whose claws are
# still whole, with the emitter at level 2; LOD1 (past 380 units) from world LOD3 (it still has the trigger cable
# loop LOD4 drops) + level 6, whose swept claws replace LOD3's broken ones.
PICKUP = [(2, 2), (3, 6)]
# Where the emitter carries the swept far-LOD claws, the DG-2's own broken claws (orphaned hook tips, thin slivers of
# arm - every stock 'pipe' face centred past x 36.35 and over 2.0 from the beam axis; the central rod is inside 0.7)
# are dropped so nothing floats beside them.
CLAW_CUT_X, CLAW_CUT_R = 36.35, 2.0
FAR_CLAW_UV_SCALE = 0.0004    # island inches -> uv on the copper patch: a whole claw spans ~4 texels of aged copper
PICKUP_SCALE = 0.8
_cache = {}


def copper_patch():
    """Native (u, v) inside one DG-2 claw arm's own UV triangle in the coil atlas (aged copper): the face of the top
    claw whose centre lies nearest the middle of its flare (x 37.9, radius 3.8)."""
    pipe = next(xm for xm in view.meshes if view.materials[xm.faces[0].material_id].name == 'mtl_wpn_t7_zmb_dg2_pipe')
    P = [v.offset for v in pipe.verts]
    best = None
    for f in pipe.faces:
        c = [sum(P[x.vertex][i] for x in f.indices) / 3.0 for i in range(3)]
        d = math.dist(c, (37.9, 0.0, 3.1414 + 3.8))
        if best is None or d < best[0]:
            best = (d, tuple(sum(x.uv[i] for x in f.indices) / 3.0 for i in range(2)))
    return best[1]


def far_claw_tris(level):
    """The swept far-LOD claws (emitter.far_claws) in native conventions, mapped onto the copper patch."""
    key = ('claws', level)
    if key not in _cache:
        cu, cv = copper_patch()
        verts, tris, dropped = [], [], 0
        for part in emitter.far_claws(level):
            fake = {k: (cu, 1.0 - cv, FAR_CLAW_UV_SCALE, False) for k in part.islands}
            pv, pt, d = exportlib.part_triangles(part, fake)
            off = len(verts); verts.extend(pv); dropped += d
            tris.extend([[dict(c, v=c['v'] + off) for c in t] for t in pt])
        _cache[key] = (verts, tris, dropped, (cu, cv))
    return _cache[key]


def claw_fragment(f, P):
    c = [sum(P[x.vertex][i] for x in f.indices) / 3.0 for i in range(3)]
    return c[0] > CLAW_CUT_X and math.hypot(c[1], c[2] - 3.1414) > CLAW_CUT_R


def emitter_level(level):
    if level not in _cache:
        verts, tris, dropped = [], [], 0
        for part in emitter.build(level):
            pv, pt, d = exportlib.part_triangles(part, pack)
            off = len(verts); verts.extend(pv); dropped += d
            tris.extend([[dict(c, v=c['v'] + off) for c in t] for t in pt])
        _cache[level] = (verts, tris, dropped)
    return _cache[level]


def build(name, bones, src, level, pickup=False, transform=None):
    model = xmodel.Model(name)
    model.bones = copy.deepcopy(bones)
    used = []
    for xm in src.meshes:
        if pickup and src.materials[xm.faces[0].material_id].name == 'mtl_wpn_t7_zmb_dg2_power':
            continue
        for f in xm.faces:
            new = common.MATERIAL_MAP[src.materials[f.material_id].name]
            if new not in used:
                used.append(new)
    used.append(common.EMITTER_MATERIAL)
    names = [common.DROP_MATERIAL] if pickup else [m for m in ORDER if m in used]
    model.materials = [xmodel.Material(n, 'Phong', {}) for n in names]
    mat_ids = {native: (0 if pickup else names.index(new)) for native, new in common.MATERIAL_MAP.items() if pickup or new in names}
    stats = dict(source={}, emitter_dropped=0)
    far = level in emitter.FAR_CLAW
    for xm in src.meshes:
        native = src.materials[xm.faces[0].material_id].name
        if pickup and native == 'mtl_wpn_t7_zmb_dg2_power':
            stats['source'][xm.name + ' (core, hidden inside the gold tube)'] = dict(skipped=len(xm.faces)); continue
        drop = exportlib.tip_face
        if far and native == 'mtl_wpn_t7_zmb_dg2_pipe':
            drop = lambda f, P: exportlib.tip_face(f, P) or claw_fragment(f, P)
        mesh, st = exportlib.source_mesh(xmodel, src, xm, len(model.meshes), mat_ids, drop_face=drop,
                                         bone_override=0 if pickup else None, transform=transform,
                                         material_override=0 if pickup else None)
        stats['source'][xm.name + ' ' + native.replace('mtl_wpn_t7_zmb_dg2_', '')] = st
        if mesh is not None:
            model.meshes.append(mesh)
    verts, tris, dropped = emitter_level(level)
    stats['emitter_dropped'] = dropped; stats['emitter_level'] = level
    model.meshes.append(exportlib.native_mesh(xmodel, 'ws_emitter_l%d' % level, verts, tris,
                                              0 if pickup else names.index(common.EMITTER_MATERIAL),
                                              len(model.meshes), 0, transform))
    if far:
        cv_, ct_, cd_, patch = far_claw_tris(level)
        model.meshes.append(exportlib.native_mesh(xmodel, 'ws_far_claws_l%d' % level, cv_, ct_,
                                                  0 if pickup else names.index('mtl_tod2_ws_coil'),
                                                  len(model.meshes), 0, transform))
        stats['far_claws'] = dict(triangles=len(ct_), dropped=cd_, copper_uv=[round(x, 5) for x in patch])
    return model, stats


def write(model, filename, stats, source_file):
    path = common.OUT / filename
    model.WriteFile_Bin(str(path), version=7, header_message='Wunderstrahl (Tower of Doom II) - DG-2 remodel, Blender MCP')
    per_mat = {}
    for mesh in model.meshes:
        for f in mesh.faces:
            n = model.materials[f.material_id].name; per_mat[n] = per_mat.get(n, 0) + 1
    rec = dict(file=common.rel(path), sha256=common.sha(path), bones=[b.name for b in model.bones],
               triangles=sum(len(m.faces) for m in model.meshes), materials=[m.name for m in model.materials],
               triangles_per_material=per_mat, meshes=[dict(name=m.name, verts=len(m.verts), faces=len(m.faces)) for m in model.meshes],
               source=common.rel(source_file), source_sha256=common.sha(source_file), stats=stats)
    assert all(len(m.verts) < 65535 for m in model.meshes)
    print('WS_MODEL', filename, rec['triangles'], 'tris', len(model.meshes), 'meshes', flush=True)
    return rec


records = {}
m, st = build('tod2_ws_view', view.bones, view, 0)
records['tod2_ws_view'] = [write(m, 'tod2_ws_view_LOD0.XMODEL_BIN', st, common.SRC_VIEW)]
records['tod2_ws_world'] = []
for lod in range(7):
    m, st = build('tod2_ws_world', worlds[lod].bones, worlds[lod], WORLD_LEVEL[lod])
    records['tod2_ws_world'].append(write(m, 'tod2_ws_world_LOD%d.XMODEL_BIN' % lod, st, common.SRC_WORLD[lod]))
# The drop: centre = the bounding-box middle of pickup LOD0's geometry, shared by both LODs (no pop when they swap).
pts = [v.offset for xm in worlds[PICKUP[0][0]].meshes for v in xm.verts] + emitter_level(PICKUP[0][1])[0]
lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
centre = [(lo[i] + hi[i]) / 2 for i in range(3)]


def to_drop(p):
    return tuple((p[i] - centre[i]) * PICKUP_SCALE for i in range(3))


origin = xmodel.Bone('tag_origin'); origin.offset = (0.0, 0.0, 0.0); origin.matrix = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
records['tod2_ws_pickup'] = []
for i, (wl, el) in enumerate(PICKUP):
    m, st = build('tod2_ws_pickup', [origin], worlds[wl], el, pickup=True, transform=to_drop)
    rec = write(m, 'tod2_ws_pickup_LOD%d.XMODEL_BIN' % i, st, common.SRC_WORLD[wl])
    rec['centre_source'] = centre; rec['scale'] = PICKUP_SCALE
    records['tod2_ws_pickup'].append(rec)
skel = common.OUT / 'tod2_ws_skeleton.XMODEL_BIN'
shutil.copyfile(common.SRC_SKEL, skel)
records['tod2_ws_skeleton'] = [dict(file=common.rel(skel), sha256=common.sha(skel), source=common.rel(common.SRC_SKEL),
                                    source_sha256=common.sha(common.SRC_SKEL), byte_identical=True)]
clips = []
for suffix in common.CLIP_SUFFIXES:
    src = common.SRC_XANIM / ('vm_dg2_%s.xanim_bin' % suffix)
    dst = common.XOUT / ('tod2_ws_vm_%s.xanim_bin' % suffix)
    shutil.copyfile(src, dst)
    assert common.sha(src) == common.sha(dst)
    clips.append(dict(name='tod2_ws_vm_' + suffix, file=common.rel(dst), sha256=common.sha(dst), source=common.rel(src)))
common.write_json(common.KIT / 'models.json', dict(models=records, clips=clips, world_emitter_levels=WORLD_LEVEL,
                  pickup=dict(lods=PICKUP, scale=PICKUP_SCALE, centre=centre, material=common.DROP_MATERIAL),
                  atlas_sha256=common.sha(common.KIT / 'atlas.json'), needle_rule=dict(min_edge=exportlib.MIN_EDGE,
                  min_altitude=exportlib.MIN_ALT), native_playtested=False))
print('WS_06_EXPORTED', sum(len(v) for v in records.values()), 'models', len(clips), 'clips', flush=True)
