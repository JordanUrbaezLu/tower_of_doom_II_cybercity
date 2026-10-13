"""THE WUNDERSTRAHL model-track verification (plain Python; no build, no game). Writes art/wunderstrahl/verification.json.

Checks (each one fails loudly):
  rig        view model bones == the DG-2 view rig's 12 exactly (names, parents, rest offsets, matrices); every world
             LOD == the DG-2 world rig's 4; the pickup is one tag_origin bone; tag_flash is (40.9997, 0.0001, 3.1414)
             in view and world; the copied skeleton is byte-identical and its 12 weapon bones sit at the same offsets
             relative to its tag_weapon as the view model's.
  geometry   every face has 3 distinct corners; no needle / zero-area triangle (the converter would drop it);
             finite unit normals; finite UVs; every vertex weight list sums to 1 over valid bones; new emitter
             geometry is rigid to tag_weapon (bone 0); emitter UVs inside the atlas; triangle counts match the
             export record and fall from LOD to LOD; vertex counts per mesh < 65535.
  design     every emitter vertex within 3.2 of the beam axis (y 0, z 3.1414); the crystal's front face at
             x 40.5..41.0; the pointed DG-2 tip is gone; the pickup is centred (bbox middle at the origin) and
             ~42 units long (the Death Machine drop it shares a slot with is 41.9); at EVERY LOD (view, world, drop)
             the side silhouette covers the beam axis from x 18 to the crystal (no gap over GAP_MAX), and no piece
             in front of x 33 hangs in mid-air - every one links, through touching pieces, to something reaching
             back toward the body (orphaned claw tips, adrift slivers, rings round a spine they never touch).
  normals    no texel of the emitter normal map inside the level-0 emitter's UV triangles faces out by less than
             z 0.1 (an inside-out texel; the mean-z test cannot see a handful).
  textures   every material of every model (except the stock drop material) has a complete map set in the
             registry; every map exists, is 8-bit RGBA with power-of-two sides (multiples of 4), matches its pinned
             sha256; normal maps decode to unit-ish vectors facing +Z; emissive maps carry no cyan/blue (blue never
             exceeds red and green where lit); the staged GDT (if present) passes install_art.py --check.
  clips      the 28 tod2_ws_vm_* files are byte-identical to the vm_dg2_* sources.
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, materials

AXZ = 3.1414
GAP_MAX = 0.35        # inches of bare beam axis tolerated between the gun and the emitter at any LOD
FAIL = []


def check(cond, msg):
    if not cond:
        FAIL.append(msg)
    return cond


def needle(a, b, c, min_edge=.001, min_alt=.0005):
    e = (math.dist(a, b), math.dist(b, c), math.dist(c, a))
    if min(e) < min_edge:
        return True
    u = [b[i] - a[i] for i in range(3)]; v = [c[i] - a[i] for i in range(3)]
    cr = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return math.sqrt(sum(x * x for x in cr)) / max(max(e), 1e-12) < min_alt


def bone_rows(m):
    return [(b.name, b.parent, tuple(b.offset), tuple(tuple(r) for r in b.matrix)) for b in m.bones]


def floating_parts(model, back=None, x_region=33.0, voxel=0.12, step=0.06, anchor_x=31.0):
    """Pieces (shared-vertex components, per mesh) in front of x_region that are not linked - through a chain of
    touching pieces - to anything reaching back toward the body (a piece starting behind anchor_x: the spine, the
    conduits, the DG-2's own barrel parts). Catches an orphaned claw tip, a decimation sliver adrift AND a group of
    parts hanging together in mid-air (rings round a spine they never touch). Triangles are point-sampled every
    `step` inches into `voxel` cells; two pieces touch when their cells are neighbours. Only triangles reaching past
    x_region - 3.5 are sampled."""
    cells = {}
    pieces = {}
    for mi, mesh in enumerate(model.meshes):
        P = np.array([v.offset for v in mesh.verts], np.float64)
        if back is not None:
            P = np.array([back(p) for p in P], np.float64)
        parent = list(range(len(P)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]; i = parent[i]
            return i
        T = [[c.vertex for c in f.indices] for f in mesh.faces]
        for a, b, c in T:
            ra, rb, rc = find(a), find(b), find(c)
            parent[ra] = rb; parent[rc] = rb
        for a, b, c in T:
            A, B, C = P[a], P[b], P[c]
            if max(A[0], B[0], C[0]) < x_region - 3.5:
                continue
            key = (mi, find(a))
            n = max(1, int(np.ceil(max(np.linalg.norm(B - A), np.linalg.norm(C - A), np.linalg.norm(C - B)) / step)))
            i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1))
            m = (i + j) <= n
            u = (i[m] / n)[:, None]; v = (j[m] / n)[:, None]
            S = A + (B - A) * u + (C - A) * v
            info = pieces.setdefault(key, dict(xs=[], xmin=1e9, cells=set()))
            info['xs'].append((A[0] + B[0] + C[0]) / 3.0)
            info['xmin'] = min(info['xmin'], A[0], B[0], C[0])
            for cell in map(tuple, np.floor(S / voxel).astype(np.int64)):
                info['cells'].add(cell)
                cells.setdefault(cell, set()).add(key)
    keys = list(pieces)
    idx = {k: i for i, k in enumerate(keys)}
    group = list(range(len(keys)))

    def root(i):
        while group[i] != i:
            group[i] = group[group[i]]; i = group[i]
        return i
    offsets = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)]
    for (cx, cy, cz), owners in cells.items():
        near = set(owners)
        for dx, dy, dz in offsets:
            near |= cells.get((cx + dx, cy + dy, cz + dz), set())
        if len(near) > 1:
            near = [idx[k] for k in near]
            r0 = root(near[0])
            for q in near[1:]:
                group[root(q)] = r0
    anchored = {root(idx[k]) for k, info in pieces.items() if info['xmin'] < anchor_x}
    lonely = []
    for key, info in pieces.items():
        if np.median(info['xs']) >= x_region and root(idx[key]) not in anchored:
            lonely.append(dict(mesh=model.meshes[key[0]].name, x=round(float(np.median(info['xs'])), 3),
                               xmin=round(float(info['xmin']), 3), cells=len(info['cells'])))
    return lonely


def emitter_normals_inside(view_model, normal_png, z_min=0.1):
    """Texels of the emitter normal map INSIDE the level-0 emitter's UV triangles whose tangent normal faces out by
    less than z_min (an inside-out texel would shade backwards; the mean-z test cannot see a handful of them)."""
    import texgen
    mesh = next(m for m in view_model.meshes if m.name.startswith('ws_emitter'))
    im = np.asarray(Image.open(normal_png).convert('RGB')).astype(np.float32) / 255.0
    h, w = im.shape[:2]
    label, _, _, _ = texgen.rasterize([mesh], w, h)
    inside = label >= 0
    z = im[..., 2] * 2 - 1
    bad = inside & (z < z_min)
    return int(bad.sum()), int(inside.sum())


def axial_gap(model, back=None, x0=18.0, x1=40.9, half=0.25, step=0.02):
    """How far the emitter floats free of the gun, measured the way a player sees it: the SIDE silhouette (every
    triangle projected onto the X-Z plane) must cover the beam axis band |z - 3.1414| <= half at every x from x0 to
    the crystal. Returns the longest uncovered run (inches) and where. Thin decimation slivers cover almost nothing,
    so the DG-2's own floating far-LOD fragments do not count as a connection. `back` maps drop space to gun space."""
    xs = np.arange(x0, x1 + 1e-9, step)
    zs = np.linspace(AXZ - half, AXZ + half, 11)
    covered = np.zeros((len(zs), len(xs)), bool)
    for mesh in model.meshes:
        P = np.array([v.offset for v in mesh.verts], np.float64)
        if back is not None:
            P = np.array([back(p) for p in P], np.float64)
        T = np.array([[c.vertex for c in f.indices] for f in mesh.faces], np.int64)
        if not len(T):
            continue
        X = P[T][:, :, 0]; Z = P[T][:, :, 2]
        keep = (X.max(1) >= x0) & (X.min(1) <= x1) & (Z.max(1) >= zs[0]) & (Z.min(1) <= zs[-1])
        for (ax, bx, cx), (az, bz, cz) in zip(X[keep], Z[keep]):
            d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
            if abs(d) < 1e-12:
                continue
            i0 = max(int(np.ceil((min(ax, bx, cx) - x0) / step)), 0); i1 = min(int(np.floor((max(ax, bx, cx) - x0) / step)), len(xs) - 1)
            if i1 < i0:
                continue
            gx, gz = np.meshgrid(xs[i0:i1 + 1], zs)
            l0 = ((bz - cz) * (gx - cx) + (cx - bx) * (gz - cz)) / d
            l1 = ((cz - az) * (gx - cx) + (ax - cx) * (gz - cz)) / d
            inside = (l0 >= -1e-9) & (l1 >= -1e-9) & (1 - l0 - l1 >= -1e-9)
            covered[:, i0:i1 + 1] |= inside
    col = covered.any(axis=0)
    worst = (0.0, None); run_start = None
    for i, c in enumerate(list(col) + [True]):
        if not c and run_start is None:
            run_start = i
        elif c and run_start is not None:
            length = (i - run_start) * step
            if length > worst[0]:
                worst = (round(length, 3), (round(float(xs[run_start]), 3), round(float(xs[min(i, len(xs) - 1)]), 3)))
            run_start = None
    return worst


def geometry(model, label, emitter_mesh_prefix='ws_emitter'):
    out = dict(triangles=0, needles=0, bad_faces=0, bad_normals=0, bad_uvs=0, bad_weights=0, emitter_uv_out=0)
    nb = len(model.bones)
    for mesh in model.meshes:
        check(len(mesh.verts) < 65535, '%s mesh %s has %d verts' % (label, mesh.name, len(mesh.verts)))
        P = [v.offset for v in mesh.verts]
        for v in mesh.verts:
            s = sum(w for _, w in v.weights)
            if not v.weights or abs(s - 1) > 1e-3 or any(not (0 <= b < nb) for b, _ in v.weights):
                out['bad_weights'] += 1
            if not all(math.isfinite(x) for x in v.offset):
                out['bad_weights'] += 1
        is_emitter = mesh.name.startswith(emitter_mesh_prefix)
        if is_emitter:
            check(all(v.weights == [(0, 1.0)] for v in mesh.verts), '%s emitter not rigid to bone 0' % label)
        for f in mesh.faces:
            out['triangles'] += 1
            ids = [c.vertex for c in f.indices]
            if len(set(ids)) < 3:
                out['bad_faces'] += 1; continue
            if needle(P[ids[0]], P[ids[1]], P[ids[2]]):
                out['needles'] += 1
            for c in f.indices:
                n = c.normal
                if not all(math.isfinite(x) for x in n) or abs(sum(x * x for x in n) - 1) > .02:
                    out['bad_normals'] += 1
                if not all(math.isfinite(x) for x in c.uv):
                    out['bad_uvs'] += 1
                if is_emitter and not all(-.001 <= x <= 1.001 for x in c.uv):
                    out['emitter_uv_out'] += 1
    for k in ('needles', 'bad_faces', 'bad_normals', 'bad_uvs', 'bad_weights', 'emitter_uv_out'):
        check(out[k] == 0, '%s: %s = %d' % (label, k, out[k]))
    return out


def main():
    report = dict(models={}, textures={}, clips=0)
    rec = common.read_json(common.KIT / 'models.json')
    src_view = common.load_model(common.SRC_VIEW)
    src_world = common.load_model(common.SRC_WORLD[0])
    # ---- rig + geometry + design ----
    last = None
    for name, recs in rec['models'].items():
        for r in recs:
            path = common.ROOT / r['file']
            check(path.is_file() and common.sha(path) == r['sha256'], 'changed or missing: ' + r['file'])
            if name == 'tod2_ws_skeleton':
                check(common.sha(path) == common.sha(common.SRC_SKEL), 'skeleton is not byte-identical to the DG-2 skeleton')
                skel = common.load_model(path)
                si = {b.name: b for b in skel.bones}
                tw = si['tag_weapon'].offset; vtw = src_view.bones[0].offset
                for b in src_view.bones:
                    d1 = [si[b.name].offset[i] - tw[i] for i in range(3)]; d2 = [b.offset[i] - vtw[i] for i in range(3)]
                    check(max(abs(a - c) for a, c in zip(d1, d2)) < 2e-3, 'skeleton/view mismatch for ' + b.name)
                report['models'][r['file']] = dict(bones=len(skel.bones), byte_identical=True)
                continue
            m = common.load_model(path)
            label = path.name
            if name == 'tod2_ws_view':
                check(bone_rows(m) == bone_rows(src_view), 'view rig differs from the DG-2 view rig')
                check([b.name for b in m.bones] == common.VIEW_BONES, 'view bone names/order changed')
            elif name == 'tod2_ws_world':
                check(bone_rows(m) == bone_rows(src_world), '%s rig differs from the DG-2 world rig' % label)
                check([b.name for b in m.bones] == common.WORLD_BONES, '%s bone set changed' % label)
            else:
                check([b.name for b in m.bones] == ['tag_origin'], '%s must have exactly tag_origin' % label)
            if name in ('tod2_ws_view', 'tod2_ws_world'):
                tf = next(b for b in m.bones if b.name == 'tag_flash').offset
                check(max(abs(a - b) for a, b in zip(tf, common.TAG_FLASH)) < 1e-4, '%s tag_flash moved: %s' % (label, tf))
            g = geometry(m, label)
            check(g['triangles'] == r['triangles'], '%s triangles %d != record %d' % (label, g['triangles'], r['triangles']))
            # no LOD may float the emitter free of the gun (review pass 2: the DG-2's own far LODs drop x 25..36)
            back = None
            if name == 'tod2_ws_pickup':
                ctr, sc = r['centre_source'], r['scale']
                back = lambda p, ctr=ctr, sc=sc: tuple(p[i] / sc + ctr[i] for i in range(3))
            gap, where = axial_gap(m, back)
            g['axial_gap'] = dict(inches=round(gap, 3), at=where)
            check(gap <= GAP_MAX, '%s: the emitter floats %.2f in free of the gun along the beam axis at x %s' % (label, gap, where))
            lonely = floating_parts(m, back)
            g['floating_parts'] = lonely[:8]
            check(not lonely, '%s: %d piece(s) float free in front of x 33 (orphaned fragments): %s' % (label, len(lonely), lonely[:4]))
            em = [v.offset for mesh in m.meshes if mesh.name.startswith('ws_emitter') for v in mesh.verts]
            if name != 'tod2_ws_pickup':
                rmax = max(math.hypot(p[1], p[2] - AXZ) for p in em)
                xmax = max(p[0] for p in em)
                check(rmax <= 3.2, '%s emitter reaches %.3f from the beam axis' % (label, rmax))
                check(40.5 <= xmax <= 41.0, '%s crystal front face at x %.3f' % (label, xmax))
                tip = [v.offset for mesh in m.meshes if not mesh.name.startswith('ws_emitter') for v in mesh.verts
                       if v.offset[0] > 39.62 and math.hypot(v.offset[1], v.offset[2] - AXZ) < .36 and v.offset[0] > 40.2]
                check(not tip, '%s still carries the DG-2 pointed tip (%d verts)' % (label, len(tip)))
                g.update(emitter_max_radius=round(rmax, 4), crystal_front_x=round(xmax, 4))
            else:
                pts = [v.offset for mesh in m.meshes for v in mesh.verts]
                lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
                mid = [(lo[i] + hi[i]) / 2 for i in range(3)]; length = hi[0] - lo[0]
                if label.endswith('LOD0.XMODEL_BIN'):
                    check(max(abs(x) for x in mid) < .05, 'pickup not centred: %s' % mid)
                check(38.0 <= length <= 46.0, 'pickup length %.2f (the Death Machine drop is 41.9)' % length)
                check([x.name for x in m.materials] == [common.DROP_MATERIAL], 'pickup must use only ' + common.DROP_MATERIAL)
                g.update(bbox=[lo, hi], length=round(length, 3))
            for mat in m.materials:
                if mat.name != common.DROP_MATERIAL:
                    check(mat.name in materials.MATERIALS, '%s uses unknown material %s' % (label, mat.name))
            g['materials'] = [x.name for x in m.materials]
            report['models'][r['file']] = g
        tris = [r['triangles'] for r in recs if 'triangles' in r]
        if len(tris) > 1:
            check(all(a > b for a, b in zip(tris, tris[1:])), '%s triangle counts do not fall LOD to LOD: %s' % (name, tris))
    # ---- textures ----
    pins = {}
    for n, h in common.read_json(common.ART / 'surfaces.json')['textures'].items():
        pins[n] = h
    for n, h in common.read_json(common.KIT / 'bake.json')['textures'].items():
        pins[n] = h
    for mname, m in materials.MATERIALS.items():
        need = ['c', 's', 'g', 'n'] + (['e'] if m['kind'] == 'emissive' else [])
        for slot in need:
            check(slot in m['maps'], '%s lacks a %s map' % (mname, slot))
    for img in materials.images():
        p = common.IMG / (img + '.png')
        if not check(p.is_file(), 'missing image ' + img):
            continue
        check(pins.get(p.name) == common.sha(p), 'image %s does not match its pinned sha256' % img)
        im = Image.open(p)
        w, h = im.size
        pow2 = lambda x: x > 0 and (x & (x - 1)) == 0
        check(im.mode == 'RGBA', '%s is %s, not RGBA' % (img, im.mode))
        check(pow2(w) and pow2(h) and w % 4 == 0 and h % 4 == 0, '%s size %dx%d is not power-of-two / multiple of 4' % (img, w, h))
        a = np.asarray(im.convert('RGB')).astype(np.float32) / 255.0
        info = dict(size=[w, h], mode=im.mode)
        suffix = img.rsplit('_', 1)[-1]
        if suffix == 'n':
            n = a * 2 - 1
            ln = np.linalg.norm(n, axis=2)
            info['normal_len_p5_p95'] = [round(float(np.percentile(ln, 5)), 3), round(float(np.percentile(ln, 95)), 3)]
            info['normal_z_mean'] = round(float(n[..., 2].mean()), 3)
            check(info['normal_z_mean'] > .6, '%s does not look like a tangent normal map' % img)
        if suffix == 'e':
            lit = a.max(axis=2) > .08
            if lit.any():
                b_over = (a[..., 2] > np.minimum(a[..., 0], a[..., 1]) + .02) & lit
                info['blue_dominant_lit_fraction'] = round(float(b_over.mean() / max(lit.mean(), 1e-9)), 5)
                check(info['blue_dominant_lit_fraction'] < .001, '%s has cyan/blue emission' % img)
            info['lit_fraction'] = round(float(lit.mean()), 4)
        report['textures'][img] = info
    # ---- emitter normal map: no texel inside the used UVs may face (nearly) into its surface ----
    vm = common.load_model(common.ROOT / rec['models']['tod2_ws_view'][0]['file'])
    bad, inside = emitter_normals_inside(vm, common.IMG / 'i_tod2_ws_emitter_n.png')
    report['emitter_normal_inside_uvs'] = dict(texels=inside, facing_out_under_0_1=bad)
    check(bad == 0, 'i_tod2_ws_emitter_n: %d texels inside the emitter UVs face out by less than z 0.1' % bad)
    # ---- clips ----
    worst = 0.0
    for c in rec['clips']:
        p = common.ROOT / c['file']; src = common.ROOT / c['source']
        check(p.is_file() and common.sha(p) == common.sha(src) == c['sha256'], 'clip not byte-identical: ' + c['file'])
        report['clips'] += 1
        # the beam origin: in every frame tag_flash must sit at the rest offset from tag_weapon (the crystal's face)
        a = common.load_anim(p); idx = {q.name: i for i, q in enumerate(a.parts)}
        if 'tag_flash' in idx and 'tag_weapon' in idx:
            for f in a.frames:
                w = np.eye(4); w[:3, :3] = np.array(f.parts[idx['tag_weapon']].matrix).T; w[:3, 3] = f.parts[idx['tag_weapon']].offset
                fl = np.eye(4); fl[:3, :3] = np.array(f.parts[idx['tag_flash']].matrix).T; fl[:3, 3] = f.parts[idx['tag_flash']].offset
                worst = max(worst, float(np.linalg.norm((np.linalg.inv(w) @ fl)[:3, 3] - np.array(common.TAG_FLASH))))
    report['clip_tag_flash_max_deviation'] = round(worst, 5)
    check(worst < .01, 'tag_flash leaves its rest offset in a clip by %.4f' % worst)
    check(report['clips'] == len(common.CLIP_SUFFIXES) == 28, 'expected 28 clips')
    # ---- staged GDT ----
    r = subprocess.run([sys.executable, '-B', str(common.TOOL / 'install_art.py'), '--check'], capture_output=True, text=True)
    report['install_art_check'] = (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else ''
    check(r.returncode == 0, 'install_art.py --check failed: ' + (r.stdout + r.stderr)[-400:])
    report['result'] = 'PASS' if not FAIL else 'FAIL'
    report['failures'] = FAIL
    report['native_built'] = False
    report['native_playtested'] = False
    report['limits'] = ('Source-level checks only: no linker run, no compiled-ledger triangle comparison, no in-game '
                        'look. Those need the main session\'s FULL build and the user\'s playtest.')
    common.write_json(common.ART / 'verification.json', report)
    if FAIL:
        print('WUNDERSTRAHL_ART_VERIFY_FAIL'); [print('  ' + f) for f in FAIL]; raise SystemExit(1)
    lods = [report['models'][r['file']]['triangles'] for r in rec['models']['tod2_ws_world']]
    print('WUNDERSTRAHL_ART_VERIFY_PASS view %d tris (12 bones), world LODs %s (4 bones), pickup %s, %d maps, %d clips' % (
        report['models'][rec['models']['tod2_ws_view'][0]['file']]['triangles'], lods,
        [report['models'][r['file']]['triangles'] for r in rec['models']['tod2_ws_pickup']], len(report['textures']), report['clips']))


if __name__ == '__main__':
    main()
