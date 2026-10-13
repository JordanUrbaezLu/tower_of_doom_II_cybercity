"""THE WAR DAMAGE PASS (docs/205), the merge half: one model per cluster.

Reads art/war_damage/layout.json (tools/war_damage/layout.js) and the stock prop
LOD files listed in art/war_damage/kit.json, and merges every cluster's placed
props into ONE rigid model with three LODs, grouped by material (the conduit
batcher's own method, tools/art_cohesion/build_conduit_batches.py):

  LOD0  every prop at its stock LOD0
  LOD1  every prop at its stock LOD1 (LOD0 when it has none); chunks, scrap and
        glass dropped (a few pixels at that distance)
  LOD2  the big shapes only (rubble piles, slabs, beams, columns, cables, rebar
        grids) at their lowest stock LOD up to LOD3

Every vertex keeps its stock UVs, colours and material; positions and normals are
rotated with the same roll -> pitch -> yaw order the layout's checks used. One
root bone, tag_origin. The models have no collision (CollisionMap "", no bullet
collision) and are drawn client-side only (_tod_war_damage.csc).

Writes model_export/tod_war_damage/<cluster>_lod{0,1,2}.xmodel_bin, the GDT
source_data/tod_war_damage.gdt and the record art/war_damage/clusters.json.
TOD_WAR_STAGE=<dir> reads the layout from <dir>/layout.json and writes everything
under <dir> instead (a staged copy, swapped into the repo whole).

Usage: python tools/war_damage/build_clusters.py
"""
import copy, hashlib, json, math, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel  # noqa: E402

STAGE = pathlib.Path(os.environ['TOD_WAR_STAGE']) if os.environ.get('TOD_WAR_STAGE') else None
LAYOUT = (STAGE / 'layout.json') if STAGE else ROOT / 'art/war_damage/layout.json'
KITF = ROOT / 'art/war_damage/kit.json'
EXP = (STAGE / 'model_export/tod_war_damage') if STAGE else ROOT / 'model_export/tod_war_damage'
GDT = (STAGE / 'source_data/tod_war_damage.gdt') if STAGE else ROOT / 'source_data/tod_war_damage.gdt'
REC = (STAGE / 'clusters.json') if STAGE else ROOT / 'art/war_damage/clusters.json'

kitdoc = json.loads(KITF.read_text())
STOCK = pathlib.Path(kitdoc['stock_root'])
KIT = dict(kitdoc['props'])
KIT_WAR = ROOT / 'art/war_damage/kit_war.json'     # phase 2: the torn conduit bodies built in the repo (build_conduit_torn.py)
KIT.update(json.loads(KIT_WAR.read_text()))
layout = json.loads(LAYOUT.read_text())

# Which roles each LOD keeps, and the highest stock LOD it may use.
LOD_ROLES = {
    0: (None, 0),
    1: ({'pile', 'scatter', 'slab', 'rebar', 'rebar_grid', 'rebar_col', 'beam', 'cable', 'fixture', 'conduit_torn'}, 1),
    2: ({'pile', 'slab', 'beam', 'rebar_col', 'cable', 'rebar_grid', 'conduit_torn'}, 3),
}
# LOD switch distances (units, from the model origin). A break cluster spans ~300 units round
# its origin; a five-floor scatter model spans ~1000, so its near LOD reaches further.
LOD_DIST = {'break': (900, 2400), 'scatter': (1700, 3600)}

def rotate(v, angles):
    p, y, r = map(math.radians, angles)
    x0, y0, z0 = v
    a = (x0, y0 * math.cos(r) - z0 * math.sin(r), y0 * math.sin(r) + z0 * math.cos(r))
    b = (a[0] * math.cos(p) + a[2] * math.sin(p), a[1], -a[0] * math.sin(p) + a[2] * math.cos(p))
    return (b[0] * math.cos(y) - b[1] * math.sin(y), b[0] * math.sin(y) + b[1] * math.cos(y), b[2])

_cache = {}
def stock(name, lod_cap):
    """-> (loaded model, lod used): the highest stock LOD <= lod_cap the prop has."""
    lods = sorted(int(k) for k in KIT[name]['lods'])
    lod = max(l for l in lods if l <= lod_cap) if any(l <= lod_cap for l in lods) else lods[0]
    key = (name, lod)
    if key not in _cache:
        m = xmodel.Model()
        base = ROOT if KIT[name].get('root') == 'repo' else STOCK
        m.LoadFile_Bin(str(base / KIT[name]['lods'][str(lod)]), split_meshes=True)
        _cache[key] = m
    return _cache[key], lod

def root_bone():
    b = xmodel.Bone('tag_origin', -1)
    b.offset = (0.0, 0.0, 0.0)
    b.matrix = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
    b.scale = (1.0, 1.0, 1.0)
    return b

def merge(cluster, lod):
    roles, cap = LOD_ROLES[lod]
    model = xmodel.Model(cluster['name'])
    model.bones = [root_bone()]
    mat_index, materials, meshes = {}, [], []
    used, degenerate = [], [0]
    for prop in cluster['props']:
        role = KIT[prop['model']]['role']
        if roles is not None and role not in roles:
            continue
        src, src_lod = stock(prop['model'], cap)
        used.append((prop['model'], src_lod))
        org = [prop['org'][i] - cluster['org'][i] for i in range(3)]
        sc, ang = prop['scale'], prop['angles']
        for mesh in src.meshes:
            if not mesh.faces:
                continue
            mat = src.materials[mesh.faces[0].material_id]
            if mat.name not in mat_index:
                mat_index[mat.name] = len(materials)
                materials.append(copy.copy(mat))
                meshes.append(xmodel.Mesh('war_%d' % len(meshes)))
            mid = mat_index[mat.name]
            target = meshes[mid]
            base = len(target.verts)
            pos = []
            for v in mesh.verts:
                p = rotate((v.offset[0] * sc[0], v.offset[1] * sc[1], v.offset[2] * sc[2]), ang)
                pos.append((p[0] + org[0], p[1] + org[1], p[2] + org[2]))
                target.verts.append(xmodel.Vertex(pos[-1], [(0, 1.0)]))
            for face in mesh.faces:
                # A triangle with two coincident corners has no area. The converter drops it ("Degenerate triangle
                # (pre-bone)": the stock rubber cable's lowest LOD carries 4, so 11 LOD2s compiled 4 short, build
                # 2026-10-03 05:46). Drop it here, counted, so the merged count IS the compiled count.
                vs = [pos[fv.vertex] for fv in face.indices]
                if any(sum((vs[i][k] - vs[j][k]) ** 2 for k in range(3)) < 1e-10 for i, j in ((0, 1), (1, 2), (0, 2))):
                    degenerate[0] += 1
                    continue
                nf = xmodel.Face(mid, mid)
                idx = []
                for fv in face.indices:
                    n = rotate((fv.normal[0] / sc[0], fv.normal[1] / sc[1], fv.normal[2] / sc[2]), ang)
                    ln = math.sqrt(sum(c * c for c in n)) or 1.0
                    idx.append(xmodel.FaceVertex(fv.vertex + base, tuple(c / ln for c in n), fv.color, fv.uv))
                nf.indices = idx
                target.faces.append(nf)
    # THE SCORCH CARDS: stock decal materials (plain lit_decal types) on two-triangle cards
    # lifted off their surface by the layout. Wound the stock way: on every Treyarch mesh the
    # triangle (v1-v0)x(v2-v0) points AGAINST the vertex normal (measured on the glass
    # shards: 1660 of 1660 faces), so a card facing n lists its corners clockwise from n.
    for d in cluster.get('decals', []):
        name = d['decal']
        if name not in mat_index:
            mat_index[name] = len(materials)
            materials.append(xmodel.Material(name, 'Phong', {'color': name + '_c.tif'}))
            meshes.append(xmodel.Mesh('war_%d' % len(meshes)))
        mid = mat_index[name]
        target = meshes[mid]
        base = len(target.verts)
        c = [d['org'][i] - cluster['org'][i] for i in range(3)]
        u, v, n = d['u'], d['v'], tuple(d['n'])
        hw, hh = d['w'] / 2.0, d['h'] / 2.0
        corners = [(-1, -1, 0.0, 0.0), (1, -1, 1.0, 0.0), (1, 1, 1.0, 1.0), (-1, 1, 0.0, 1.0)]   # counter-clockwise seen from n
        for a, b, _, _ in corners:
            target.verts.append(xmodel.Vertex(tuple(c[i] + u[i] * a * hw + v[i] * b * hh for i in range(3)), [(0, 1.0)]))
        for tri in ((0, 2, 1), (0, 3, 2)):                                                       # clockwise from n: faces n
            nf = xmodel.Face(mid, mid)
            nf.indices = [xmodel.FaceVertex(base + k, n, (1.0, 1.0, 1.0, 1.0), (corners[k][2], corners[k][3])) for k in tri]
            target.faces.append(nf)
        used.append((name, 'decal'))
    model.materials = materials
    model.meshes = meshes
    over = [m.name for m in meshes if len(m.verts) >= 65536]
    assert not over, f"{cluster['name']} lod{lod}: a merged mesh passes 65535 vertices: {over}"
    return model, used, degenerate[0]

EXP.mkdir(parents=True, exist_ok=True)
GDT.parent.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
blocks, records = [], []
for cluster in layout['clusters']:
    files = {}
    prev = None
    for lod in (0, 1, 2):
        model, used, dropped = merge(cluster, lod)
        if not any(m.faces for m in model.meshes):   # only small debris here: this LOD repeats the one before it
            model, used, dropped = prev
        prev = (model, used, dropped)
        p = EXP / f"{cluster['name']}_lod{lod}.xmodel_bin"
        model.WriteFile_Bin(str(p), version=7)
        pts = [v.offset for m in model.meshes for v in m.verts]
        records.append(dict(asset=cluster['name'], lod=lod, file=p.relative_to(STAGE or ROOT).as_posix(), sha256=sha(p),
                            triangles=sum(len(m.faces) for m in model.meshes), degenerate_dropped=dropped, materials=[m.name for m in model.materials],
                            props=len(used), bounds=[[round(min(v[i] for v in pts), 1) for i in range(3)], [round(max(v[i] for v in pts), 1) for i in range(3)]]))
        files[lod] = f"tod_war_damage/{p.name}"
    near, mid = LOD_DIST[cluster['kind']]
    fields = {
        'filename': files[0], 'highLodDist': near,
        'mediumLod': files[1], 'mediumLodDist': mid,
        'lowLod': files[2], 'lowLodDist': 0,
        'type': 'rigid', 'scale': 1, 'CollisionMap': '', 'BulletCollisionLOD': 'None',
        'physicsPreset': '', 'cullOutDiameter': 0, 'materials': '',
    }
    blocks.append('"' + cluster['name'] + '" ( "xmodel.gdf" )\n{\n' + ''.join(f'    "{k}" "{v}"\n' for k, v in fields.items()) + '}\n')
    lods = [r for r in records if r['asset'] == cluster['name']]
    print(f"{cluster['name']:24s} props={len(cluster['props']):3d}  tris lod0/1/2 = {lods[0]['triangles']}/{lods[1]['triangles']}/{lods[2]['triangles']}  materials={len(lods[0]['materials'])}")

GDT.write_text('{\n' + ''.join(blocks) + '}\n')
REC.write_text(json.dumps(dict(layout_sha256=sha(LAYOUT), kit_sha256=sha(KITF), kit_war_sha256=sha(KIT_WAR), gdt_sha256=sha(GDT), models=records), indent=1) + '\n')
tot = [sum(r['triangles'] for r in records if r['lod'] == l) for l in (0, 1, 2)]
deg = [sum(r['degenerate_dropped'] for r in records if r['lod'] == l) for l in (0, 1, 2)]
print(f"WAR_DAMAGE_CLUSTERS_EXPORTED {len(layout['clusters'])} models x 3 LODs; total tris lod0/1/2 = {tot[0]}/{tot[1]}/{tot[2]}; "
      f"zero-area stock triangles dropped lod0/1/2 = {deg[0]}/{deg[1]}/{deg[2]}")
