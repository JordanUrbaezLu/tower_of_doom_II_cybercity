"""r1_truth_render.py - R1: render the ACTUAL in-game models the gun-bay icons and companion portraits are traced from.

WHY (tmp/design_review/findings.md, user 2026-10-04): "mozambique isnt even mozambique, the ai companions dont look correct
at all. Raps looks lazy and talon isnt even the talon shape". The fix is to stop drawing from memory: every R1 image is
traced from a render of the model the game actually loads. This script makes those renders; the PIL generators
(r1_gun_icons.py, r1_comp_portraits.py) read them. It never writes into the game's source trees.

RUN (background Blender 4.2, which carries the PyCoD addon; ~1-3 min a model on the CPU):
  "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe" --background --factory-startup
      --python tools/artgen/packs/r1_truth_render.py -- [--only a,b] [--probe] [--passes]
  --probe   three small axis silhouettes per model (to pick each model's canonical rotation)
  --passes  re-render only the cheap data passes (albedo / normal / depth); keep existing beauty renders

WHAT IT WRITES (art/generated/R1-truth-renders/):
  <job>_<view>.png          the BEAUTY render: real meshes, real colour maps, a three-point studio light, transparent bg
  <job>_<view>_albedo.png   8-bit sRGB base colour, unlit; alpha = coverage    (the passes the generators trace from)
  <job>_<view>_normal.png   8-bit RAW camera-space normal * 0.5 + 0.5; alpha = coverage
  <job>_<view>_depth.png    16-bit GREY RAW view depth, 0 = nearest .. 1 = far (Pillow reads 16-bit grey, not 16-bit RGBA)
  <job>_<view>_matid.png    8-bit RAW: red = 1 + the xmodel material's index (the json's material order), unblended
  Cycles' camera space looks down +Z: a face turned to the camera has normal z < 0; +Y is screen up.
  <job>.json                the source binaries + their sha256, the texture each material resolved to, the camera
Views: "side" = orthographic, the model's canonical +X to screen right, +Z up (a gun's muzzle right, as every gun-bay cell
points); "34" = a three-quarter view; "por" = the companion portrait's view (companions only); "high" = from above and in
front (the crossbow, whose prod is edge-on from the side - this view looks back along it, so its icon is mirrored).
The renders the generators read were downscaled to 1200 px wide and the unused passes pruned (art/generated stays lean):
re-running this script rewrites them at full size - re-run both generators after it, and re-prune (R1 LAND.md).

HOW A MATERIAL'S COLOUR IS FOUND (the game's own chain, read from the GDTs): xmodel material name -> the xmodel block's
skinOverride (the Breacher's Apex guns are re-skinned) -> material block "colorMap" -> image block "baseImage" -> the file,
looked up in the repo, the private tools root and the shared tools root. A material with no resolvable map is drawn grey
and listed under "untextured" in the json - the silhouette is the truth either way.

Safety: refuses to run while BlackOps3 / Radiant / cod2map64 / linker_modtools / gdtdb run (memory: the 16 GB machine).
"""
import bpy, os, re, sys, glob, json, math, hashlib, subprocess
from mathutils import Vector, Matrix, Euler

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
PRIV = r'C:\BO3Tools\TOD2Cybercity'
SHARED = r'C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130'
OUT = os.path.join(REPO, 'art', 'generated', 'R1-truth-renders')
sys.path.insert(0, os.path.expanduser('~/AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel  # noqa: E402

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []

# ------------------------------------------------------------------------------------------------ the jobs
# model: an xmodel ASSET name (resolved through the GDTs, skinOverride honoured) or ('file', path).
# rot: world-axis rotations, applied in order, that turn the loaded mesh so its FRONT (muzzle / blade tip / head) is +X and
#      its top is +Z. Chosen by eye from the --probe silhouettes (art/generated/R1-truth-renders/_probe), recorded here.
# views: which renders. res: the side render's width in px.
J = lambda **k: k  # noqa: E731
JOBS = [
    J(name='mozambique',  model='tod_bra_moz_view',                 rot=(('X', -90), ('Z', 90), ('Y', 180), ('Z', 180)), views=('side', '34')),
    J(name='peacekeeper', model='tod_bra_pk_view',                  rot=(('X', -90), ('Z', 90), ('Y', 180), ('Z', 180)), views=('side', '34')),
    J(name='rem870',      model='vm_t6_remington870mcs',            rot=(('Z', 180),),    views=('side', '34')),
    J(name='bow',         model='wpn_t7_zmb_bow_base_view',         rot=(('Z', 180),),    views=('side', '34')),
    J(name='crossbow',    model='wpn_t9_crossbow_view',             rot=(('Z', 180),),    views=('side', '34')),
    J(name='firebow',     model='tod_fire_bow_rune_view',           rot=(('Z', 180),),    views=('side', '34')),
    J(name='gauntlet',    model='wpn_t7_zmb_dlc3_gauntlet_dragon_view', rot=(('Z', 180),), views=('side', '34')),
    J(name='greatsword',  model='tod_cyber_sword_view',             rot=(('Y', -90),),    views=('side', '34')),
    J(name='skull',       model='wpn_t7_zmb_dlc2_keeper_head_view', rot=(('Z', 180),),    views=('side', '34')),
    J(name='soulstaff',   model='tod_necro_staff2_view',            rot=(('Z', 180),),    views=('side', '34')),
    J(name='crownstaff',  model='tod_necro_staff3_view',            rot=(('Z', 180),),    views=('side', '34')),
    J(name='shield',      model='wpn_t7_zmb_zod_rocket_shield_world', rot=(('Z', 90),),   views=('side', '34')),
    J(name='gift',        model='view_xmas_gun',                    rot=(('Z', 180),),    views=('side', '34'), drop_strays=True),
    J(name='gift_bare',   model='view_xmas_gun',                    rot=(('Z', 180),),    views=('side',), drop_strays=True,
      hide_mats=('tinsel', 'light_string')),
    J(name='knife',       model=('file', os.path.join(PRIV, 'model_export', 't9_wpn_ports', '_melee', 't9_knife_combat',
                                                      'wpn_t9_knife_combat_american_view.XMODEL_BIN')),
                                                                    rot=(('Z', 180),),    views=('side', '34')),
    J(name='protector',   model='tod_partner_protector',            rot=(),               views=('side', '34', 'por')),
    # the SAME rig in its donor finish (the gold SoE Civil Protector; the installer repaints its plates blue enamel)
    J(name='protector_gold', model='c_zom_zod_robot_protector_gold_fb', rot=(),           views=('34', 'por')),
    # the Talon's gun pod is a separate island parked under the hull at its bind position (in game a tag carries it):
    # dropped so the portrait reads as the drone, not as a drone beside a stray part
    J(name='talon',       model='tod_partner_talon',                rot=(),               views=('side', '34', 'por'),
      drop_strays=True),
    J(name='raps',        model='tod_partner_raps',                 rot=(),               views=('side', '34', 'por')),
    J(name='cerberus',    model='tod_partner_cerberus',             rot=(('Z', 180),),    views=('side', '34', 'por')),
    # icon variants: the staffs rolled about their own axis so the skull and the crown's halo face the camera (from the
    # plain side the skull shows its crown and the halo is edge-on); the crossbow from above, so its prod reads
    J(name='soulstaff_fa',  model='tod_necro_staff2_view', rot=(('Z', 180), ('X', 90)),  views=('side',)),
    J(name='soulstaff_fb',  model='tod_necro_staff2_view', rot=(('Z', 180), ('X', -90)), views=('side',)),
    J(name='crownstaff_fa', model='tod_necro_staff3_view', rot=(('Z', 180), ('X', 90)),  views=('side',)),
    J(name='crownstaff_fb', model='tod_necro_staff3_view', rot=(('Z', 180), ('X', -90)), views=('side',)),
    J(name='crossbow_hi',   model='wpn_t9_crossbow_view',  rot=(('Z', 180),),            views=('high',)),
    # THE ONE INCH PUNCH: its weapon model is empty (the fist is the player's own hand; Nero Blackstone's viewhands
    # have no source in any tools root). The nearest real thing: a real viewhands mesh (the Archer's BO2 hands) posed
    # with the punch's OWN animation (vm_zom_1inchpunch_idle, frame 0) by linear-blend skinning - the right arm only,
    # forearm -> fist turned onto +X, four rolls about the forearm to choose the clearest fist.
] + [J(name='fist_r%d' % r, model=('posed', 'model_export/tod_archer/tod_archer_bo2_hands.xmodel_bin',
                                   'xanim_export/tod_warrior/vm_zom_1inchpunch_idle.XANIM_BIN', 0, '_ri'),
       rot=(('X', r),), views=('side',)) for r in (0, 90, 180, 270)] + [
    # the same pose, the HAND alone (wrist + finger bones): the jacket sleeve dwarfed the fist in the icon
    J(name='fisth_r%d' % r, model=('posed', 'model_export/tod_archer/tod_archer_bo2_hands.xmodel_bin',
                                    'xanim_export/tod_warrior/vm_zom_1inchpunch_idle.XANIM_BIN', 0, '_ri',
                                    ('wrist', 'index', 'mid', 'ring', 'pinky', 'thumb', 'palm')),
      rot=(('X', r),), views=('side',)) for r in (0, 90, 180, 270)]
ROT_FILE = os.path.join(OUT, '_rotations.json')   # overrides written after a probe pass, read here (one place to tune)

# ------------------------------------------------------------------------------------------------ GDT index
_IDX = None


def gdt_index():
    global _IDX
    if _IDX:
        return _IDX
    files = []
    for r in (os.path.join(REPO, 'source_data'), os.path.join(PRIV, 'source_data'), os.path.join(PRIV, 'model_export'),
              os.path.join(SHARED, 'source_data')):
        files += sorted(glob.glob(os.path.join(r, '*.gdt')))
    xm, mt, im = {}, {}, {}
    blk = re.compile(r'"([^"]+)" \( "(xmodel|material|image)\.gdf" \)\s*\{(.*?)\n\t\}', re.S)
    for f in files:   # FIRST definition wins: the repo, then the private root, then the shared root (gdtdb's override)
        try:
            t = open(f, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        for m in blk.finditer(t):
            name, kind, body = m.group(1), m.group(2), m.group(3)
            d = dict(re.findall(r'"([A-Za-z0-9_]+)" "([^"]*)"', body))
            d['_gdt'] = f
            tgt = {'xmodel': xm, 'material': mt, 'image': im}[kind]
            tgt.setdefault(name, d)
    _IDX = (xm, mt, im)
    return _IDX


def find_file(rel):
    rel = rel.replace('\\\\', '\\').replace('/', '\\')
    for base in (REPO, os.path.join(REPO, 'model_export'), PRIV, os.path.join(PRIV, 'model_export'), SHARED,
                 os.path.join(SHARED, 'model_export')):
        p = os.path.join(base, rel)
        if os.path.exists(p):
            return p
    return None


def resolve_model(model):
    """-> (path, {xmodel material -> override material})"""
    if isinstance(model, tuple) and model[0] == 'file':
        return model[1], {}
    xm, _, _ = gdt_index()
    d = xm.get(model)
    if not d:
        raise SystemExit('r1_truth_render: no xmodel block for %s' % model)
    p = find_file(d.get('filename', ''))
    if not p:
        raise SystemExit('r1_truth_render: %s -> %s is not on disk' % (model, d.get('filename')))
    over = {}
    for line in d.get('skinOverride', '').replace('\\r\\n', '\n').split('\n'):
        parts = line.split()
        if len(parts) == 2:
            over[parts[0]] = parts[1]
    return p, over


def _tint(s, default=None):
    try:
        v = [float(x) for x in s.split()[:3]]
        return tuple(v) if len(v) == 3 else default
    except (AttributeError, ValueError):
        return default


def resolve_color(matname, model_dir, pycod_images):
    """material -> (colour map file or None, rgb multiplier). The engine's own rules, as the GDT states them:
      * a "$..." built-in colour map: $..black.. is a METAL whose visible colour is its specColorTint (the SoE Civil
        Protector's gold is $color_black_40 under a gold spec tint); $..white.. / $..gray.. carry their colorTint
      * a micro-tile material (lit_micro_tile_*, the T7 drones): colorMap is a tiling micro-detail; the colour IS colorTint
      * otherwise colorMap (an image asset -> its baseImage file) times colorTint
    detailMap / colorMap0N / normal maps are never colour (the first pass took a detail NORMAL map: lavender drones)."""
    _, mt, im = gdt_index()
    m = mt.get(matname)
    if m:
        cmap = m.get('colorMap', '')
        tint = _tint(m.get('colorTint'), (1.0, 1.0, 1.0))
        if max(tint) <= 0.0:
            tint = (1.0, 1.0, 1.0)
        spec = _tint(m.get('specColorTint'))
        mtype = m.get('materialType', '')
        metal = None
        if spec and max(spec) > 0.25:
            metal = spec
        if cmap.startswith('$'):
            if 'black' in cmap:
                return None, (metal or (0.06, 0.06, 0.07))
            if 'gray' in cmap or 'grey' in cmap:
                return None, tuple(0.5 * c for c in tint)
            return None, tint
        if 'micro_tile' in mtype and m.get('colorTint'):
            return None, tint
        if cmap:
            d = im.get(cmap)
            p = find_file(d['baseImage']) if d and d.get('baseImage') else find_file(cmap)
            if p:
                if 'default_black' in os.path.basename(p).lower():
                    return None, (metal or (0.06, 0.06, 0.07))
                return p, tint
    for k in ('color', 'color_map'):   # the binary's own record (PyCoD), relative to the model's folder
        v = (pycod_images or {}).get(k)
        if v:
            for cand in (os.path.join(model_dir, v.replace('\\\\', '\\')), find_file(v)):
                if cand and os.path.exists(cand):
                    return cand, (1.0, 1.0, 1.0)
    return None, None

# ------------------------------------------------------------------------------------------------ scene


def busy():
    try:
        out = subprocess.run(['tasklist'], capture_output=True, text=True).stdout.lower()
    except Exception:
        return None
    for n in ('blackops3.exe', 'radiant_modtools.exe', 'cod2map64.exe', 'linker_modtools.exe', 'gdtdb.exe'):
        if n in out:
            return n
    return None


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = 6
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.resolution_percentage = 100
    return sc


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _m4(off, mat):
    M = Matrix(tuple(tuple(r) for r in mat)).transposed().to_4x4()   # PyCoD stores the axes as ROWS
    M.translation = Vector(off)
    return M


def posed_verts(mdl, anim_path, frame, side, only_bones=None):
    """Linear-blend skinning of a viewhands model by one frame of an xanim (both store model-space transforms). A bone
    the clip does not drive rides its parent rigidly. Returns (positions, keep-face mask, forearm axis)."""
    from PyCoD import xanim
    a = xanim.Anim()
    a.LoadFile_Bin(anim_path)
    idx = {p.name: i for i, p in enumerate(a.parts)}
    bind = [_m4(b.offset, b.matrix) for b in mdl.bones]
    pose = [None] * len(mdl.bones)
    for i, b in enumerate(mdl.bones):
        if b.name in idx:
            fp = a.frames[frame].parts[idx[b.name]]
            pose[i] = _m4(fp.offset, fp.matrix)
        elif b.parent >= 0 and pose[b.parent] is not None:
            pose[i] = pose[b.parent] @ bind[b.parent].inverted() @ bind[i]
        else:
            pose[i] = bind[i]
    skin = [pose[i] @ bind[i].inverted() for i in range(len(bind))]
    src = mdl.meshes[0]
    pos, keepv = [], []
    for v in src.verts:
        acc = Vector((0, 0, 0))
        for bi, w in v.weights:
            acc += w * (skin[bi] @ Vector(v.offset))
        pos.append(tuple(acc))
        top = max(v.weights, key=lambda bw: bw[1])[0]
        bn = mdl.bones[top].name
        keepv.append(side + '_' in bn + '_' and (only_bones is None or any(o in bn for o in only_bones)))
    names = [b.name for b in mdl.bones]
    elbow = pose[names.index('j_elbow' + side)].translation
    wrist = pose[names.index('j_wrist' + side)].translation
    return pos, keepv, (wrist - elbow).normalized(), wrist


def load_model(job):
    if job['model'][0] == 'posed':
        _, mrel, arel, frame, side = job['model'][:5]
        only_bones = job['model'][5] if len(job['model']) > 5 else None
        path = os.path.join(REPO, mrel)
        over = {}
    else:
        path, over = resolve_model(job['model'])
    mdl = xmodel.Model()
    mdl.LoadFile_Bin(path, split_meshes=False)
    src = mdl.meshes[0]
    me = bpy.data.meshes.new(job['name'])
    faces = [[f.indices[i].vertex for i in (0, 2, 1)] for f in src.faces]
    verts = [tuple(v.offset) for v in src.verts]
    pre = Matrix.Identity(4)
    if job['model'][0] == 'posed':
        verts, keepv, axis, wrist = posed_verts(mdl, os.path.join(REPO, arel), frame, side, only_bones)
        faces = [f if all(keepv[q] for q in f) else None for f in faces]
        pre = axis.rotation_difference(Vector((1, 0, 0))).to_matrix().to_4x4() @ Matrix.Translation(-wrist)
    hide = tuple(job.get('hide_mats', ()))
    if hide:      # whole materials left out of the render (the Gift of Death's tinsel garland is noise at icon size)
        faces = [f if f is not None and not any(h in mdl.materials[src.faces[i].material_id].name for h in hide) else None
                 for i, f in enumerate(faces)]
    keep_idx = [i for i, f in enumerate(faces) if f is not None]
    me.from_pydata(verts, [], [faces[i] for i in keep_idx])
    me.update()
    ob = bpy.data.objects.new(job['name'], me)
    bpy.context.scene.collection.objects.link(ob)
    uv = me.uv_layers.new(name='uv')
    for poly, face in zip(me.polygons, [src.faces[i] for i in keep_idx]):
        poly.material_index = face.material_id
        poly.use_smooth = True
        for li, fi in zip(poly.loop_indices, (0, 2, 1)):
            u, v = face.indices[fi].uv
            uv.data[li].uv = (u, 1 - v)
    record = {'binary': os.path.relpath(path, REPO) if path.startswith(REPO) else path, 'sha256': sha(path),
              'triangles': len(src.faces), 'materials': {}, 'untextured': []}
    for m in mdl.materials:
        name = over.get(m.name, m.name)
        tex, rgb = resolve_color(name, os.path.dirname(path), getattr(m, 'images', None))
        if tex is None and rgb is None and name != m.name:
            tex, rgb = resolve_color(m.name, os.path.dirname(path), getattr(m, 'images', None))
        mat = bpy.data.materials.new(name)
        mat['tex'] = tex or ''
        mat['rgb'] = list(rgb) if rgb else [0.42, 0.42, 0.44]
        me.materials.append(mat)
        record['materials'][m.name] = {'resolved_as': name, 'color_map': tex, 'tint': list(rgb) if rgb else None}
        if not tex and rgb is None:
            record['untextured'].append(m.name)
    M = pre
    for axis, deg in job.get('rot', ()):
        M = Matrix.Rotation(math.radians(deg), 4, axis) @ M
    me.transform(M)
    me.update()
    if job['model'][0] == 'posed' or job.get('hide_mats'):   # left-out faces leave loose vertices: they would frame the camera
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(me)
        bm.free()
        me.update()
    if job.get('drop_strays'):
        record['dropped_islands'] = drop_strays(me)
    return ob, record


def drop_strays(me):
    """Delete mesh islands lying wholly outside the largest island's bounds (+15 %): a viewmodel's parked prop (the Gift of
    Death carries a stray cup at its origin that the gun never shows). Returns how many faces went."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    seen, islands = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, isl = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        islands.append(isl)
    def box(fs):
        vs = [v.co for g in fs for v in g.verts]
        return [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]
    def vol(fs):   # the island that matters is the BIGGEST BY SIZE, not by faces (the Talon's dense gun pod outnumbers
        a, b = box(fs)   # the faces of its many-piece hull - picked by face count, the hull was the part dropped)
        return (b[0] - a[0] + 1e-3) * (b[1] - a[1] + 1e-3) * (b[2] - a[2] + 1e-3)
    big = max(islands, key=vol)
    lo, hi = box(big)
    # grow to the union of every island that overlaps the biggest one's box (multi-part assemblies)
    for _ in range(3):
        for isl in islands:
            a, b = box(isl)
            if all(a[i] <= hi[i] and b[i] >= lo[i] for i in range(3)):
                lo = [min(lo[i], a[i]) for i in range(3)]
                hi = [max(hi[i], b[i]) for i in range(3)]
    pad = [(hi[i] - lo[i]) * 0.15 for i in range(3)]
    gone = []
    for isl in islands:
        a, b = box(isl)
        if not all(a[i] <= hi[i] + pad[i] and b[i] >= lo[i] - pad[i] for i in range(3)):
            gone += isl
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    bm.to_mesh(me)
    bm.free()
    me.update()
    return len(gone)


def set_pass(ob, mode, near=0.0, far=1.0):
    """mode: beauty | albedo | normal | depth. Rebuilds every material's node tree."""
    for mat in ob.data.materials:
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        tex = mat.get('tex', '')
        col = None
        if mode in ('beauty', 'albedo'):
            tint = list(mat.get('rgb', [1.0, 1.0, 1.0]))[:3]
            rgbn = nt.nodes.new('ShaderNodeRGB')
            rgbn.outputs[0].default_value = (tint[0], tint[1], tint[2], 1)
            col = rgbn.outputs[0]
            if tex:
                tn = nt.nodes.new('ShaderNodeTexImage')
                img = bpy.data.images.get(os.path.basename(tex)) or bpy.data.images.load(tex, check_existing=True)
                tn.image = img
                mix = nt.nodes.new('ShaderNodeMix')
                mix.data_type = 'RGBA'
                mix.blend_type = 'MULTIPLY'
                mix.inputs['Factor'].default_value = 1.0
                nt.links.new(tn.outputs['Color'], mix.inputs['A'])
                nt.links.new(rgbn.outputs[0], mix.inputs['B'])
                col = mix.outputs['Result']
        if mode == 'beauty':
            b = nt.nodes.new('ShaderNodeBsdfPrincipled')
            nt.links.new(col, b.inputs['Base Color'])
            b.inputs['Roughness'].default_value = 0.55
            b.inputs['Metallic'].default_value = 0.25
            nt.links.new(b.outputs[0], out.inputs['Surface'])
            continue
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Strength'].default_value = 1.0
        if mode == 'albedo':
            nt.links.new(col, em.inputs['Color'])
        elif mode == 'normal':
            g = nt.nodes.new('ShaderNodeNewGeometry')
            vt = nt.nodes.new('ShaderNodeVectorTransform')
            vt.vector_type = 'NORMAL'
            vt.convert_from = 'WORLD'
            vt.convert_to = 'CAMERA'
            nt.links.new(g.outputs['Normal'], vt.inputs['Vector'])
            mul = nt.nodes.new('ShaderNodeVectorMath')
            mul.operation = 'MULTIPLY_ADD'
            mul.inputs[1].default_value = (0.5, 0.5, 0.5)
            mul.inputs[2].default_value = (0.5, 0.5, 0.5)
            nt.links.new(vt.outputs[0], mul.inputs[0])
            nt.links.new(mul.outputs[0], em.inputs['Color'])
        elif mode == 'matid':
            k = list(ob.data.materials).index(mat) + 1
            em.inputs['Color'].default_value = (k / 255.0, 0.0, 0.0, 1.0)
        elif mode == 'depth':
            cd = nt.nodes.new('ShaderNodeCameraData')
            mr = nt.nodes.new('ShaderNodeMapRange')
            mr.inputs['From Min'].default_value = near
            mr.inputs['From Max'].default_value = far
            nt.links.new(cd.outputs['View Z Depth'], mr.inputs['Value'])
            nt.links.new(mr.outputs['Result'], em.inputs['Color'])
        nt.links.new(em.outputs[0], out.inputs['Surface'])


def make_camera(sc, ob, view, res):
    """An orthographic camera framing ob for `view`. Returns (cam, near, far)."""
    vs = [Vector(v.co) for v in ob.data.vertices]
    c = sum(vs, Vector()) / len(vs)
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    mid = (lo + hi) / 2
    if view == 'side':
        d = Vector((0, -1, 0))        # the camera looks along +Y: model +X to the right, +Z up
    elif view == '34':
        d = Vector((0.55, -1.0, -0.42)).normalized()
    elif view == 'por':
        d = Vector((-0.62, -1.0, -0.22)).normalized()
    elif view == 'high':
        d = Vector((0.0, 0.62, -1.0)).normalized()      # from above and in front: the far (+Y) side at the image top
    elif view == 'top':
        d = Vector((0.0, 0.001, -1.0)).normalized()
    else:
        raise SystemExit('unknown view ' + view)
    cam_data = bpy.data.cameras.new('cam')
    cam_data.type = 'ORTHO'
    cam = bpy.data.objects.new('cam', cam_data)
    sc.collection.objects.link(cam)
    rad = (hi - lo).length
    cam.location = mid - d * rad * 2.0
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    inv = cam.matrix_world.inverted()
    pts = [inv @ v for v in vs]
    xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [-p.z for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    cam.location = cam.matrix_world @ Vector((cx, cy, 0))
    pad = 1.06
    aspect = max(w, 1e-6) / max(h, 1e-6)
    resx = res
    resy = max(64, int(round(res / aspect / 4.0)) * 4)
    if resy > res:            # tall subject: cap the height, narrow the width
        resy = res
        resx = max(64, int(round(res * aspect / 4.0)) * 4)
    sc.render.resolution_x, sc.render.resolution_y = resx, resy
    cam_data.ortho_scale = max(w, h) * pad
    cam_data.clip_start = 0.001
    cam_data.clip_end = rad * 10
    sc.camera = cam
    return cam, min(zs) - 0.001 + 0, max(zs) + 0.001, {'dir': list(d), 'ortho_scale': cam_data.ortho_scale,
                                                       'res': [resx, resy]}


def add_lights(sc, ob):
    vs = [Vector(v.co) for v in ob.data.vertices]
    mid = sum(vs, Vector()) / len(vs)
    rad = max((v - mid).length for v in vs)
    for name, off, energy, size in (('key', (-1.0, -1.6, 2.2), 5200, 1.2), ('fill', (2.2, -1.2, 0.6), 1700, 2.0),
                                    ('rim', (0.6, 2.4, 1.6), 3600, 1.0)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy * (rad / 10.0) ** 2
        ld.size = size * rad
        lo = bpy.data.objects.new(name, ld)
        lo.location = mid + Vector(off) * rad
        lo.rotation_euler = (mid - lo.location).to_track_quat('-Z', 'Y').to_euler()
        sc.collection.objects.link(lo)
    w = bpy.data.worlds.new('w')
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    sc.world = w


def render(sc, path, mode):
    vs = sc.view_settings
    if mode == 'beauty':
        sc.display_settings.display_device = 'sRGB'
        vs.view_transform = 'Standard'
        vs.look = 'None'
        sc.cycles.samples = 48
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 6
        sc.render.image_settings.color_depth = '8'
        sc.cycles.filter_width = 1.5
    else:
        vs.view_transform = 'Standard' if mode == 'albedo' else 'Raw'
        sc.cycles.samples = 1 if mode == 'matid' else 8      # an id never blends across a seam
        sc.cycles.use_denoising = False
        sc.cycles.max_bounces = 0
        sc.cycles.filter_width = 0.8
        if mode == 'depth':
            sc.render.image_settings.color_mode = 'BW'
            sc.render.image_settings.color_depth = '16'
        else:
            sc.render.image_settings.color_depth = '8'
    sc.render.film_transparent = mode != 'depth'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    sc.render.image_settings.color_mode = 'RGBA'


def do_job(job, probe=False):
    sc = reset()
    ob, rec = load_model(job)
    rec['rot'] = [list(s) for s in job.get('rot', ())]
    if probe:
        for axis, d in (('X', (1, 0, 0)), ('Y', (0, -1, 0)), ('Z', (0, 0, -1))):
            for o in list(sc.objects):
                if o.type == 'CAMERA':
                    bpy.data.objects.remove(o)
            vs = [Vector(v.co) for v in ob.data.vertices]
            mid = sum(vs, Vector()) / len(vs)
            rad = max((v - mid).length for v in vs)
            cd = bpy.data.cameras.new('c')
            cd.type = 'ORTHO'
            cd.ortho_scale = rad * 2.2
            cam = bpy.data.objects.new('c', cd)
            sc.collection.objects.link(cam)
            dv = Vector(d)
            cam.location = mid - dv * rad * 3
            cam.rotation_euler = dv.to_track_quat('-Z', 'Y').to_euler()
            cd.clip_end = rad * 10
            sc.camera = cam
            sc.render.resolution_x = sc.render.resolution_y = 360
            set_pass(ob, 'normal')
            render(sc, os.path.join(OUT, '_probe', '%s_%s.png' % (job['name'], axis)), 'normal')
        print('R1_PROBE', job['name'], json.dumps(rec['untextured']), flush=True)
        return
    rec['views'] = {}
    add_lights(sc, ob)
    for view in job['views']:
        for o in list(sc.objects):
            if o.type == 'CAMERA':
                bpy.data.objects.remove(o)
        res = 1600 if view in ('side', 'high', 'top') else 1200
        cam, near, far, info = make_camera(sc, ob, view, res)
        rec['views'][view] = info
        base = os.path.join(OUT, '%s_%s' % (job['name'], view))
        if '--passes' not in ARGS or not os.path.exists(base + '.png'):
            set_pass(ob, 'beauty')
            render(sc, base + '.png', 'beauty')
        if True:   # every view carries its data passes
            set_pass(ob, 'albedo')
            render(sc, base + '_albedo.png', 'albedo')
            set_pass(ob, 'normal')
            render(sc, base + '_normal.png', 'normal')
            set_pass(ob, 'depth', near, far)
            render(sc, base + '_depth.png', 'depth')
            set_pass(ob, 'matid')
            render(sc, base + '_matid.png', 'matid')
        print('R1_RENDER', job['name'], view, flush=True)
    rec['type'] = 'Blender (Cycles, CPU) render of the native source binary and its resolved colour maps; not an in-game screenshot'
    with open(os.path.join(OUT, job['name'] + '.json'), 'w') as f:
        json.dump(rec, f, indent=1)


def main():
    b = busy()
    if b:
        raise SystemExit('r1_truth_render: %s is running - not rendering (the 16 GB rule)' % b)
    os.makedirs(os.path.join(OUT, '_probe'), exist_ok=True)
    rots = {}
    if os.path.exists(ROT_FILE):
        rots = json.load(open(ROT_FILE))
    only = None
    if '--only' in ARGS:
        only = set(ARGS[ARGS.index('--only') + 1].split(','))
    for job in JOBS:
        if only and job['name'] not in only:
            continue
        if job['name'] in rots:
            job = dict(job, rot=tuple(tuple(s) for s in rots[job['name']]))
        do_job(job, probe='--probe' in ARGS)


main()
