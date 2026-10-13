"""THE WAR DAMAGE PASS, phase 2 (docs/205 s7): THE TORN CONDUITS.

Built from the authored power-conduit channel (model_export/tod_surface/tod_power_conduit_off_lod{0,1}.xmodel_bin,
tools/art_cohesion/12_author_conduit.py): local X runs along the channel (-48..48), Y across (+-9), Z out of the wall.
Two variants, a and b. The first HINGE units stay bolted to the wall; past the hinge the armored strip curls off the
wall (each point turns about the hinge line by an angle that grows with its distance past it, so the strip arcs) and
twists about its own axis; the free end's connector block and sockets are torn away (an open mouth: the conductors
show). The whole assembly tears together - the channel bed, its lips, the clips, the cables - so it reads as one
armored strip peeling off the wall (the first cut left the bed flat and only the lips and cables bent: thin legs).

  BODY        model_export/tod_war_damage/kit/tod_war_conduit_torn_<a|b>_lod{0,1,2}.xmodel_bin
              shell + steel + rubber + the groove, NOT the conductors. A kit prop (role conduit_torn, root repo):
              build_clusters.py merges it into each break's cluster like a stock prop.
  CONDUCTORS  model_export/tod_war_damage/tod_war_conductor_<a|b>_<off|on>_lod{0,1}.xmodel_bin
              + source_data/tod_war_conductors.gdt: the two cyan conductors alone, bent with the body, as a SEPARATE
              two-state client model (off = mtl_tod_conduit_wire_off, on = mtl_tod_conduit_wire_on, the stock
              conduits' own twins): _tod_war_damage.csc swaps _off -> _on as the power wave passes the floor.
  art/war_damage/kit_war.json     the kit entries (bounds, LOD files, triangles) layout.js / build_clusters.py read
  art/war_damage/conduit_torn.json the free end (where the fray cables hang and the arc sparks play), the shas

Usage: python tools/war_damage/build_conduit_torn.py [--check]
"""
import copy, hashlib, json, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel  # noqa: E402

SRC = ROOT / 'model_export/tod_surface'
KIT_DIR = ROOT / 'model_export/tod_war_damage/kit'
EXP = ROOT / 'model_export/tod_war_damage'
GDT = ROOT / 'source_data/tod_war_conductors.gdt'
KIT_JSON = ROOT / 'art/war_damage/kit_war.json'
REC = ROOT / 'art/war_damage/conduit_torn.json'
WIRE = {'off': 'mtl_tod_conduit_wire_off', 'on': 'mtl_tod_conduit_wire_on'}

# variant -> hinge x (the strip is bolted from -48 to here), curl (deg, at the free end), twist (deg), buckle (units).
# Placed with local +X UP the wall (layout.js): past 90 degrees the torn end has curled out of the wall and flopped
# back DOWN under its own weight (b); a stiffer tear stands out of the wall, twisted (a).
VARIANTS = {
    'a': dict(hinge=-8.0, curl=84.0, twist=30.0, buckle=0.0),
    'b': dict(hinge=-20.0, curl=126.0, twist=-34.0, buckle=0.7),
}
END_X = 48.0
MOUTH_X = 43.5          # the free end's connector block + sockets sit past this: torn away
AXIS_Z = 1.2            # the strip's centreline height (the twist's axis)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def rot_y(v, t):        # about +Y: +X turns toward +Z
    c, s = math.cos(t), math.sin(t)
    return (v[0] * c - v[2] * s, v[1], v[0] * s + v[2] * c)


def rot_x(v, t):        # about +X
    c, s = math.cos(t), math.sin(t)
    return (v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c)


def tear(var, p, n, lip=False):
    """-> (position, normal) of a local point after the tear. Points before the hinge are untouched."""
    x, y, z = p
    if x <= var['hinge']:
        return tuple(p), tuple(n)
    s = (x - var['hinge']) / (END_X - var['hinge'])
    s = min(1.0, max(0.0, s))
    theta = math.radians(var['curl']) * s ** 1.5
    phi = math.radians(var['twist']) * s * s
    # twist about the strip's own axis (y = 0, z = AXIS_Z)
    q = rot_x((0.0, y, z - AXIS_Z), phi)
    y2, z2 = q[1], q[2] + AXIS_Z
    if lip and var['buckle']:
        z2 += var['buckle'] * math.sin(s * math.pi * 3) * s
    # curl about the hinge line (x = hinge, z = 0, along Y)
    dx = x - var['hinge']
    px = var['hinge'] + dx * math.cos(theta) - z2 * math.sin(theta)
    pz = dx * math.sin(theta) + z2 * math.cos(theta)
    nn = rot_y(rot_x(tuple(n), phi), theta)
    ln = math.sqrt(sum(c * c for c in nn)) or 1.0
    return (px, y2, pz), tuple(c / ln for c in nn)


def free_end(var):
    """The torn mouth's centre and the strip's tangent there (local)."""
    p, _ = tear(var, (END_X, 0.0, AXIS_Z), (0.0, 0.0, 1.0))
    q, _ = tear(var, (END_X - 1.0, 0.0, AXIS_Z), (0.0, 0.0, 1.0))
    d = tuple(a - b for a, b in zip(p, q))
    ln = math.sqrt(sum(c * c for c in d)) or 1.0
    return [round(c, 3) for c in p], [round(c / ln, 4) for c in d]


def load(lod):
    m = xmodel.Model()
    m.LoadFile_Bin(str(SRC / f'tod_power_conduit_off_lod{lod}.xmodel_bin'), split_meshes=True)
    return m


def mesh_x_range(mesh):
    xs = [v.offset[0] for v in mesh.verts]
    return min(xs), max(xs)


def build(src, var, want):
    """-> a Model holding the source's meshes selected by `want(mesh, material)`, torn by `var`."""
    out = xmodel.Model('torn')
    out.bones = copy.deepcopy(src.bones)
    mats, mat_ids, meshes = [], {}, []
    for mesh in src.meshes:
        if not mesh.faces:
            continue
        mat = src.materials[mesh.faces[0].material_id]
        lo, hi = mesh_x_range(mesh)
        if lo > MOUTH_X:                                   # the free end's connector block / sockets: torn away
            continue
        if not want(mesh, mat):
            continue
        lip = 'channel lip' in mesh.name
        if mat.name not in mat_ids:
            mat_ids[mat.name] = len(mats)
            mats.append(copy.copy(mat))
        mid = mat_ids[mat.name]
        nm = xmodel.Mesh(mesh.name)
        for v in mesh.verts:
            p = tear(var, v.offset, (0, 0, 1))[0]
            nm.verts.append(xmodel.Vertex(p, [(0, 1.0)]))
        for face in mesh.faces:
            nf = xmodel.Face(mid, mid)
            idx = []
            for fv in face.indices:
                v = mesh.verts[fv.vertex]
                n = tear(var, v.offset, fv.normal, lip)[1]
                idx.append(xmodel.FaceVertex(fv.vertex, n, fv.color, fv.uv))
            nf.indices = idx
            nm.faces.append(nf)
        meshes.append(nm)
    out.materials = mats
    out.meshes = meshes
    return out


def bounds(model):
    pts = [v.offset for m in model.meshes for v in m.verts]
    return [[round(min(p[i] for p in pts), 3) for i in range(3)], [round(max(p[i] for p in pts), 3) for i in range(3)]]


def tris(model):
    return sum(len(m.faces) for m in model.meshes)


def main():
    check = '--check' in sys.argv
    src = {lod: load(lod) for lod in (0, 1)}
    kit, rec, gdt = {}, {'variants': {}, 'models': []}, []
    is_conductor = lambda mesh, mat: mesh.name.startswith('Fine cyan conductor')
    staged = {}                                            # path -> bytes (written at the end, or compared in --check)
    for name, var in VARIANTS.items():
        files = {}
        for lod in (0, 1, 2):
            body = build(src[min(lod, 1)], var, lambda mesh, mat: not is_conductor(mesh, mat))
            body.name = f'tod_war_conduit_torn_{name}'
            p = KIT_DIR / f'tod_war_conduit_torn_{name}_lod{lod}.xmodel_bin'
            staged[p] = body
            files[str(lod)] = p
        kit[f'tod_war_conduit_torn_{name}'] = dict(
            root='repo', role='conduit_torn', bones=1, materials=[m.name for m in staged[files['0']].materials],
            triangles=tris(staged[files['0']]), min=bounds(staged[files['0']])[0], max=bounds(staged[files['0']])[1],
            lods={k: p.relative_to(ROOT).as_posix() for k, p in files.items()},
            lod_triangles={k: tris(staged[p]) for k, p in files.items()})
        for state in ('off', 'on'):
            for lod in (0, 1):
                cond = build(src[lod], var, is_conductor)
                cond.name = f'tod_war_conductor_{name}_{state}'
                for m in cond.materials:
                    if m.name == WIRE['off']:
                        m.name = WIRE[state]
                p = EXP / f'{cond.name}_lod{lod}.xmodel_bin'
                staged[p] = cond
            asset = f'tod_war_conductor_{name}_{state}'
            gdt.append('"' + asset + '" ( "xmodel.gdf" )\n{\n' + ''.join(f'    "{k}" "{v}"\n' for k, v in {
                'filename': f'tod_war_damage/{asset}_lod0.xmodel_bin', 'highLodDist': 700,
                'mediumLod': f'tod_war_damage/{asset}_lod1.xmodel_bin', 'mediumLodDist': 0,
                'type': 'rigid', 'scale': 1, 'CollisionMap': '', 'BulletCollisionLOD': 'None',
                'physicsPreset': '', 'cullOutDiameter': 0, 'materials': ''}.items()) + '}\n')
        end, tangent = free_end(var)
        rec['variants'][name] = dict(params=var, free_end=end, free_dir=tangent, body_bounds=bounds(staged[files['0']]))
    gdt_text = '{\n' + ''.join(gdt) + '}\n'
    # write (or compare)
    KIT_DIR.mkdir(parents=True, exist_ok=True)
    stale = []
    for p, model in staged.items():
        tmp = p.with_suffix('.tmp')
        model.WriteFile_Bin(str(tmp), version=7)
        data = tmp.read_bytes()
        tmp.unlink()
        if check:
            if not p.exists() or p.read_bytes() != data:
                stale.append(p.name)
        else:
            p.write_bytes(data)
        rec['models'].append(dict(file=p.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(data).hexdigest(), triangles=tris(model), materials=[m.name for m in model.materials]))
    if check:
        if not GDT.exists() or GDT.read_text(encoding='utf-8') != gdt_text:
            stale.append(GDT.name)
        if not KIT_JSON.exists() or json.loads(KIT_JSON.read_text()) != json.loads(json.dumps(kit)):
            stale.append(KIT_JSON.name)
        if stale:
            print('TORN CONDUITS STALE:', ', '.join(stale), '- run python tools/war_damage/build_conduit_torn.py')
            sys.exit(1)
        print('TORN CONDUITS OK:', len(staged), 'models, 4 conductor twins, free ends', {k: v['free_end'] for k, v in rec['variants'].items()})
        return
    GDT.write_text(gdt_text, encoding='utf-8')
    KIT_JSON.write_text(json.dumps(kit, indent=1) + '\n', encoding='utf-8')
    rec['source'] = {f'lod{l}': sha(SRC / f'tod_power_conduit_off_lod{l}.xmodel_bin') for l in (0, 1)}
    rec['gdt_sha256'] = sha(GDT)
    REC.write_text(json.dumps(rec, indent=1) + '\n', encoding='utf-8')
    for name, var in VARIANTS.items():
        k = kit[f'tod_war_conduit_torn_{name}']
        print(f"{name}: body tris lod0/1/2 = {k['lod_triangles']['0']}/{k['lod_triangles']['1']}/{k['lod_triangles']['2']}  bounds {k['min']} .. {k['max']}  free end {rec['variants'][name]['free_end']} dir {rec['variants'][name]['free_dir']}")
    print('TORN CONDUITS written:', len(staged), 'models')


if __name__ == '__main__':
    main()
