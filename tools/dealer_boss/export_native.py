"""Bake the Dealer master into native BO3 character assets (background Blender 4.2).

  "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe" -b art/dealer_boss/dealer_boss.blend --python tools/dealer_boss/export_native.py

THREE MODELS come out of one master:
  tod_dealer_lod0.xmodel_bin           the MASKED Dealer (state one): body / head / hands groups,
                                       each baked to its own atlas (colour, tangent normal, fullspec,
                                       gloss, emissive) and skinned to the Keeper skeleton
  tod_dealer_cracked_lod0.xmodel_bin   state two (user 2026-10-02): the same groups with the state-one
                                       mask faces removed and the CRACKED mask's faces kept (10_state2_mask.py:
                                       one eye dead, chips, fissures, the torn grin); same bake, same atlases
  tod_dealer_scythe_lod0.xmodel_bin    his scythe, a rigid model whose origin is the grip (attached
                                       to tag_weapon_right in script), its own 1024 atlas
Seven decimated LODs are written for each as reference; the GDT uses converter-generated
LODs from LOD0 the way the skinned cyber roster ships. Every binary is round-trip read and
asserted. Outputs stay in the repo (model_export/tod_dealer/ and art/dealer_boss/engine_kit/).
"""
import bpy, bmesh, sys, json, hashlib, math, time
from pathlib import Path
from mathutils import Vector, Matrix
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools/dealer_boss'))
sys.path.insert(0, str(Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
import cyber_material_bake as BAKE
from PyCoD import xmodel
from process_guard import check
check(strict=True)

ART = ROOT / 'art/dealer_boss'; KIT = ART / 'engine_kit'; OUT = ROOT / 'model_export/tod_dealer'; IMG = OUT / '_images'
for p in (KIT, OUT, IMG):
    p.mkdir(parents=True, exist_ok=True)
DONOR = ROOT / 'model_export/tod_keeper/c_zom_dlc4_keeper_fb.XMODEL_BIN'
MASTER = Path(bpy.data.filepath)
assert MASTER.name == 'dealer_boss.blend', MASTER
master_sha = hashlib.sha256(MASTER.read_bytes()).hexdigest()
scene = bpy.context.scene
assert scene.get('tod2_dealer_boss_studio'), 'not the Dealer master'
t0 = time.time()

GROUPS = {'body': ['01', '04'], 'head': ['02'], 'hands': ['03']}
ATLAS = {'body': 4096, 'head': 2048, 'hands': 2048, 'scythe': 1024}
LOD_RATIOS = (1.0, 0.55, 0.28, 0.14, 0.075, 0.04, 0.022)
LOD0_BUDGET = {'body': 60000, 'head': 50000, 'hands': 17000, 'scythe': 9000}   # the mask's wires and the nails stay crisp (the head carries BOTH masks until the per-state drop)
MAX_WEIGHTS = 4
EMISSION_SCALE = 6.0
BAKE.EMISSION_SCALE = EMISSION_SCALE
MASK_PREFIX = 'Mask |'
WEAPON_COLL = 'DEALER | 06 WEAPONS'

scene.render.engine = 'CYCLES'; scene.cycles.samples = 12
scene.render.threads_mode = 'FIXED'; scene.render.threads = 8
try:
    pref = bpy.context.preferences.addons['cycles'].preferences
    pref.compute_device_type = 'OPTIX'; pref.get_devices()
    for d in pref.devices:
        d.use = d.type == 'OPTIX'
    scene.cycles.device = 'GPU'
except Exception:
    scene.cycles.device = 'CPU'
scene.render.bake.margin = 6; scene.render.bake.use_selected_to_active = False; scene.render.bake.normal_g = 'NEG_Y'

rig = bpy.data.objects['DEALER_RIG | Keeper animation skeleton']
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
donor = xmodel.Model(); donor.LoadFile_Bin(str(DONOR), split_meshes=True)
BONE_INDEX = {b.name: i for i, b in enumerate(donor.bones)}
BONE_INDEX_LC = {b.name.lower(): i for i, b in enumerate(donor.bones)}
# Blender orders armature.bones by hierarchy, not creation: compare the sets (weights are mapped by NAME to donor indices)
assert {b.name for b in rig.data.bones} == {b.name for b in donor.bones}, 'studio rig differs from the donor skeleton'
skel = json.loads((ART / 'skeleton.json').read_text())
tagb = next(b for b in skel['bones'] if b['name'] == 'tag_weapon_right')
TAG_MAT = Matrix.Identity(4)
for r in range(3):
    for c in range(3):
        TAG_MAT[r][c] = tagb['matrix'][c][r]
    TAG_MAT[r][3] = tagb['offset'][r]


def coll_key(c):
    return c.name[9:11] if c.name.startswith('DEALER | ') else ''


def group_of(ob):
    for c in ob.users_collection:
        k = coll_key(c)
        for g, keys in GROUPS.items():
            if k in keys:
                return g
    return None


def select(ob):
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob


def flatten(src, deps):
    """A new object holding src's evaluated mesh (every modifier applied) with its vertex-group names."""
    ev = src.evaluated_get(deps)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=deps)
    ob = bpy.data.objects.new('native ' + src.name, me); scene.collection.objects.link(ob)
    ob.matrix_world = src.matrix_world.copy()
    for vg in src.vertex_groups:
        ob.vertex_groups.new(name=vg.name)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(me); bm.free(); me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    return ob


# ------------------------------------------------------------------ 1. flatten every part
# the review state hides one of the two masks and the stock weapon previews: a hidden object
# is not evaluated (no modifiers applied), so everything is unhidden before the depsgraph is read
def unhide_layer(lc):
    lc.exclude = False; lc.hide_viewport = False
    for c in lc.children:
        unhide_layer(c)
unhide_layer(bpy.context.view_layer.layer_collection)
for c in bpy.data.collections:
    c.hide_viewport = False; c.hide_render = False
for ob in bpy.data.objects:
    ob.hide_viewport = False; ob.hide_render = False; ob.hide_set(False)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
parts = {g: [] for g in GROUPS}
scythe = []
for src in list(scene.objects):
    if src.type != 'MESH':
        continue
    colls = [c.name for c in src.users_collection]
    assert not any('STATE2' in n for n in colls), 'a retired STATE2 collection is still in the master: run 10_state2_mask.py'
    if any(n.startswith(WEAPON_COLL) for n in colls):
        if src.get('scythe_part'):
            ob = flatten(src, deps); scythe.append(ob)
        continue
    if not src.get('dealer_part'):
        continue
    g = group_of(src)
    if g is None:
        continue
    ob = flatten(src, deps)
    # remember which STATE each face belongs to (0 both, 1 the masked Dealer only, 2 the cracked mask only) so each
    # variant drops the other state's faces after the one shared bake
    state = 2 if src.get('state2_only') else (1 if (src.get('state1_only') or src.name.startswith(MASK_PREFIX)) else 0)
    attr = ob.data.attributes.new('dealer_state', 'INT', 'FACE')
    attr.data.foreach_set('value', [state] * len(ob.data.polygons))
    parts[g].append(ob)
keep = {o for objs in parts.values() for o in objs} | set(scythe)
for ob in list(scene.objects):
    if ob not in keep and ob != rig:
        bpy.data.objects.remove(ob, do_unlink=True)


def join(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    ob = bpy.context.object; ob.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob


def tri_count(ob):
    ob.data.calc_loop_triangles(); return len(ob.data.loop_triangles)


def decimate(ob, ratio):
    if ratio >= 0.999:
        return
    select(ob)
    mod = ob.modifiers.new('LOD', 'DECIMATE'); mod.ratio = ratio; mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)


def bake(ob, group, size):
    select(ob)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0015, margin_method='FRACTION', area_weight=0.3)
    bpy.ops.object.mode_set(mode='OBJECT')
    mats = [m for m in ob.data.materials if m]
    images = {}
    for suffix in ('n', 'c', 's', 'g', 'e'):
        im = bpy.data.images.new('i_tod_dealer_%s_%s' % (group, suffix), width=size, height=size, alpha=False)
        im.colorspace_settings.name = 'Non-Color' if suffix in ('n', 'g') else 'sRGB'
        for m in mats:
            node = m.node_tree.nodes.new('ShaderNodeTexImage'); node.image = im; m.node_tree.nodes.active = node
            if suffix != 'n':
                BAKE.wire_channel(m, suffix)
        bpy.ops.object.bake(type='NORMAL' if suffix == 'n' else 'EMIT', normal_space='TANGENT')
        im.filepath_raw = str(IMG / (im.name + '.png')); im.file_format = 'PNG'; im.save()
        images[suffix] = im.name + '.png'
        print('DEALER_BAKED', group, suffix, size, round(time.time() - t0), flush=True)
    return images


def weights_of(ob):
    out = []
    root = BONE_INDEX['j_mainroot']
    name_by_gid = {vg.index: vg.name for vg in ob.vertex_groups}
    for v in ob.data.vertices:
        ws = []
        for ge in v.groups:
            n = name_by_gid.get(ge.group)
            if n is None or ge.weight <= 0.0005:
                continue
            bi = BONE_INDEX.get(n, BONE_INDEX_LC.get(n.lower()))
            if bi is None:
                continue
            ws.append((bi, ge.weight))
        ws.sort(key=lambda t: -t[1]); ws = ws[:MAX_WEIGHTS]
        tot = sum(w for _, w in ws)
        out.append([(root, 1.0)] if tot <= 0 else [(bi, w / tot) for bi, w in ws])
    return out


def sliver(a, b, c, min_edge=0.002, min_alt=0.001):
    e = (math.dist(a, b), math.dist(b, c), math.dist(c, a))
    u = [b[i] - a[i] for i in range(3)]; v = [c[i] - a[i] for i in range(3)]
    cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    h = math.sqrt(sum(x * x for x in cross)) / max(max(e), 1e-20)
    return min(e) < min_edge or h < min_alt


def mesh_to_xmodel(ob, mesh_name, model, mesh_id, material_ids, transform=None, rigid_bone=None, drop_state=0):
    """material_ids: slot index -> model material index. rigid_bone: weight everything to it (scythe).
    drop_state: faces tagged with this dealer_state (1 or 2) are left out of the binary."""
    me = ob.data; me.calc_loop_triangles()
    ws = weights_of(ob) if rigid_bone is None else None
    M = transform if transform is not None else ob.matrix_world
    nm = M.to_3x3().inverted().transposed()
    mask_attr = me.attributes.get('dealer_state') if drop_state else None
    mesh = xmodel.Mesh(mesh_name)
    mesh.verts = [xmodel.Vertex(tuple(M @ v.co), ws[v.index] if ws else [(rigid_bone, 1.0)]) for v in me.vertices]
    uv_layer = me.uv_layers.active.data
    slivers = 0; fallbacks = 0; dropped = 0
    for tri in me.loop_triangles:
        if mask_attr is not None and mask_attr.data[tri.polygon_index].value == drop_state:
            dropped += 1; continue
        if tri.area < 1e-9:
            slivers += 1; continue
        pos = [tuple(M @ me.vertices[me.loops[li].vertex_index].co) for li in tri.loops]
        if sliver(*pos):
            slivers += 1; continue
        corners = []
        for li in (tri.loops[0], tri.loops[2], tri.loops[1]):
            n = (nm @ me.corner_normals[li].vector).normalized()
            if n.length_squared < 0.9:
                n = (nm @ tri.normal).normalized(); fallbacks += 1
            assert n.length_squared > 0.9, 'zero normal'
            uv = uv_layer[li].uv
            corners.append(xmodel.FaceVertex(me.loops[li].vertex_index, tuple(n), (1, 1, 1, 1), (uv[0], 1 - uv[1])))
        f = xmodel.Face(mesh_id, material_ids[me.polygons[tri.polygon_index].material_index]); f.indices = corners
        mesh.faces.append(f)
    # the loader keeps only vertices a face uses: compact them here so what is written is what reads back
    # (each variant drops the other state's mask faces and would otherwise carry their orphaned vertices)
    used = sorted({c.vertex for f in mesh.faces for c in f.indices})
    remap = {v: i for i, v in enumerate(used)}
    mesh.verts = [mesh.verts[v] for v in used]
    for f in mesh.faces:
        for c in f.indices:
            c.vertex = remap[c.vertex]
    model.meshes.append(mesh)
    return {'faces': len(mesh.faces), 'verts': len(mesh.verts), 'slivers': slivers, 'normal_fallbacks': fallbacks, 'state_faces_dropped': dropped}


def write_model(path, model):
    # a Model built in memory has no version until told: write the donor's (7)
    model.WriteFile_Bin(str(path), version=getattr(donor, 'version', None) or 7)
    chk = xmodel.Model(); chk.LoadFile_Bin(str(path), split_meshes=True)
    assert [(b.name, b.parent) for b in chk.bones] == [(b.name, b.parent) for b in model.bones]
    assert len(chk.meshes) == len(model.meshes)
    assert sum(len(m.faces) for m in chk.meshes) == sum(len(m.faces) for m in model.meshes)
    for a, b in zip(model.meshes, chk.meshes):
        assert len(a.verts) == len(b.verts), (a.name, len(a.verts), len(b.verts))
        assert len(a.faces) == len(b.faces), (a.name, len(a.faces), len(b.faces))
        # the loader may re-order vertices: compare as position multisets (float32 storage -> 1e-2 rounding)
        key = lambda v: tuple(round(x, 2) for x in v.offset)
        wrote = sorted(key(v) for v in a.verts); read = sorted(key(v) for v in b.verts)
        assert wrote == read, (a.name, 'vertex positions changed through the binary')
        assert sorted(len(v.weights) for v in a.verts) == sorted(len(v.weights) for v in b.verts), (a.name, 'weight counts changed')
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ------------------------------------------------------------------ 2. join, unwrap, bake per group
joined = {}; images = {}
for g in GROUPS:
    assert parts[g], 'group %s has no parts' % g
    ob = join(parts[g], 'Dealer native ' + g)
    n0 = tri_count(ob)
    if n0 > LOD0_BUDGET[g]:
        decimate(ob, LOD0_BUDGET[g] / n0)
    joined[g] = ob
    print('DEALER_GROUP', g, 'tris', n0, '->', tri_count(ob), flush=True)
    images[g] = bake(ob, g, ATLAS[g])
scythe_ob = None
if scythe:
    scythe_ob = join(scythe, 'Dealer native scythe')
    n0 = tri_count(scythe_ob)
    if n0 > LOD0_BUDGET['scythe']:
        decimate(scythe_ob, LOD0_BUDGET['scythe'] / n0)
    images['scythe'] = bake(scythe_ob, 'scythe', ATLAS['scythe'])
MATERIALS = {g: 'mtl_tod_dealer_' + g for g in GROUPS}
records = []


def character_model(lod, ratio, cracked):
    """cracked False = the masked Dealer (state one: drop the state-2 faces); True = the cracked mask (drop state-1)."""
    model = xmodel.Model(); model.bones = donor.bones
    mat_index = {}
    for g in GROUPS:
        mat_index[MATERIALS[g]] = len(model.materials); model.materials.append(xmodel.Material(MATERIALS[g], 'Phong', {}))
    counts = {}
    mesh_id = 0
    for g in GROUPS:
        src = joined[g]
        ob = src.copy(); ob.data = src.data.copy(); scene.collection.objects.link(ob)
        decimate(ob, ratio)
        counts[g] = mesh_to_xmodel(ob, 'tod_dealer_' + g, model, mesh_id, {i: mat_index[MATERIALS[g]] for i in range(max(1, len(ob.data.materials)))}, drop_state=(1 if cracked else 2))
        bpy.data.objects.remove(ob, do_unlink=True); mesh_id += 1
    return model, counts


for lod, ratio in enumerate(LOD_RATIOS):
    for cracked in (False, True):
        model, counts = character_model(lod, ratio, cracked)
        dst = OUT / ('tod_dealer%s_lod%d.xmodel_bin' % ('_cracked' if cracked else '', lod))
        sha = write_model(dst, model)
        records.append({'model': 'tod_dealer_cracked' if cracked else 'tod_dealer', 'lod': lod, 'ratio': ratio,
                        'file': str(dst.relative_to(ROOT)).replace('\\', '/'), 'sha256': sha, 'meshes': counts,
                        'triangles_total': sum(c['faces'] for c in counts.values()), 'materials': [m.name for m in model.materials]})
        print('DEALER_LOD', dst.name, records[-1]['triangles_total'], flush=True)
    if scythe_ob is not None:
        model = xmodel.Model()
        b = xmodel.Bone('tag_origin', -1); b.offset = (0.0, 0.0, 0.0); b.matrix = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        model.bones = [b]
        model.materials.append(xmodel.Material('mtl_tod_dealer_scythe', 'Phong', {}))
        ob = scythe_ob.copy(); ob.data = scythe_ob.data.copy(); scene.collection.objects.link(ob)
        decimate(ob, ratio)
        # the scythe was authored in the tag frame: bring it back to its local frame (origin = grip)
        counts = {'scythe': mesh_to_xmodel(ob, 'tod_dealer_scythe', model, 0, {i: 0 for i in range(max(1, len(ob.data.materials)))}, transform=TAG_MAT.inverted() @ ob.matrix_world, rigid_bone=0)}
        bpy.data.objects.remove(ob, do_unlink=True)
        dst = OUT / ('tod_dealer_scythe_lod%d.xmodel_bin' % lod)
        sha = write_model(dst, model)
        records.append({'model': 'tod_dealer_scythe', 'lod': lod, 'ratio': ratio, 'file': str(dst.relative_to(ROOT)).replace('\\', '/'), 'sha256': sha,
                        'meshes': counts, 'triangles_total': counts['scythe']['faces'], 'materials': ['mtl_tod_dealer_scythe']})

manifest = {
    'master': str(MASTER.relative_to(ROOT)).replace('\\', '/'), 'master_sha256': master_sha, 'stage': scene.get('dealer_stage'),
    'donor': str(DONOR.relative_to(ROOT)).replace('\\', '/'), 'donor_sha256': hashlib.sha256(DONOR.read_bytes()).hexdigest(),
    'bones': len(donor.bones), 'bone_names': [b.name for b in donor.bones],
    'groups': {g: {'material': MATERIALS[g], 'atlas': ATLAS[g], 'images': images[g]} for g in GROUPS},
    'scythe': {'material': 'mtl_tod_dealer_scythe', 'atlas': ATLAS['scythe'], 'images': images.get('scythe')} if scythe_ob else None,
    'states': {'masked': 'tod_dealer', 'cracked': 'tod_dealer_cracked'}, 'emission_scale': EMISSION_SCALE, 'max_weights': MAX_WEIGHTS, 'lods': records,
    'textures': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(IMG.glob('*.png'))},
    'seconds': round(time.time() - t0, 1),
}
(KIT / 'export_manifest.json').write_text(json.dumps(manifest, indent=1))
print('DEALER_EXPORT_OK', json.dumps({'models': sorted({r['model'] for r in records}), 'lod0': {r['model']: r['triangles_total'] for r in records if r['lod'] == 0}, 'seconds': manifest['seconds']}), flush=True)
