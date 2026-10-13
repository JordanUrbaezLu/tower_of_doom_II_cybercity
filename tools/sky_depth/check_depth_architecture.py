"""Compare v13 detail geometry with the preserved v12 source, without Blender.

Uses all 1,189 retained ordinary lot dimensions/positions/seeds. The composition
receipt does not retain lot angle/palette, so those are deterministic audit
samples, explicitly not an exact replay of the production city. The render-time
composition/clearance audit remains required for the actual authored scene.
"""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys
from types import SimpleNamespace
from pass_config import resolve_sky_source


ROOT = Path(__file__).resolve().parents[2]
BEFORE = ROOT / 'art/sky3d/depth_review/baseline_sources/cyber_architecture.py'
CURRENT = resolve_sky_source('cyber_architecture')
LOTS = ROOT / 'art/sky3d/consistency_review/before/composition.json'
OUT = ROOT / 'art/sky3d/depth_review/architecture_check.json'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old, new = load('depth_baseline', BEFORE), load('depth_current', CURRENT)
tree = ast.parse((ROOT / 'tools/sky3d/build_city.py').read_text(encoding='utf-8'))
acc_node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Acc')
namespace = {'math': math}
exec(compile(ast.Module(body=[acc_node], type_ignores=[]), 'actual_sky_accumulator', 'exec'), namespace)
Acc = namespace['Acc']
sys.path.insert(0, str(ROOT / 'tools/sky3d'))
from cyber_coverage import modernize_lot

lots = [p for p in json.loads(LOTS.read_text())['buildings']
        if p['kept'] and modernize_lot(p['spire'], p['h'], p['distance'])]
assert len(lots) == 1189
outer_before, outer_after, bay_records = [], [], []


def watch_lofts(module, target):
    original = module._armoured_loft
    def wrapped(*args, **kwargs):
        target.append(args[2:7])  # Exact original fp0/z0/fp1/z1/finish.
        return original(*args, **kwargs)
    module._armoured_loft = wrapped


watch_lofts(old, outer_before)
watch_lofts(new, outer_after)
original_bay = new._inset_service_bay


def capture_bay(acc, pts, uvs, col, bay):
    scratch = Acc('isolated service bay')
    original_bay(scratch, pts, uvs, col, bay)
    assert len(scratch.f) == 9, 'Recess must have 4 surrounding faces, 4 bevels, and a back'
    # The inset back must be physically behind the old face, never a flat decal.
    ab = [pts[1][j]-pts[0][j] for j in range(3)]
    ad = [pts[3][j]-pts[0][j] for j in range(3)]
    n = (ab[1]*ad[2]-ab[2]*ad[1], ab[2]*ad[0]-ab[0]*ad[2], ab[0]*ad[1]-ab[1]*ad[0])
    length = math.sqrt(sum(v*v for v in n))
    n = [v/length for v in n]
    back = [scratch.v[i] for i in scratch.f[-1]]
    for p in back:
        signed = sum((p[j]-pts[0][j])*n[j] for j in range(3))
        assert abs(signed+bay['depth']) < 1e-6, ('recess not inside surface', signed, bay)
    for face in scratch.f:
        vs = [scratch.v[i] for i in face]
        e0 = [vs[1][j]-vs[0][j] for j in range(3)]
        e1 = [vs[2][j]-vs[0][j] for j in range(3)]
        face_normal = (e0[1]*e1[2]-e0[2]*e1[1],
                       e0[2]*e1[0]-e0[0]*e1[2], e0[0]*e1[1]-e0[1]*e1[0])
        area2 = sum(v*v for v in face_normal)
        assert area2 > 1e-12, 'Degenerate recess face'
        assert sum(face_normal[j]*n[j] for j in range(3)) > 0, 'Inverted recess face'
        assert vs != pts, 'Original full face still covers the recess'
    # A geometric probe straight through the opening must reach the back first.
    # Other masses/buildings can still occlude a real bay in the final render.
    def sub(a,b): return [a[j]-b[j] for j in range(3)]
    def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    def dot(a,b): return sum(a[j]*b[j] for j in range(3))
    centre = [sum(p[j] for p in back)/4 for j in range(3)]
    origin = [centre[j]+n[j]*(bay['depth']+1) for j in range(3)]
    direction = [-v for v in n]
    hits=[]
    for face in scratch.f:
        for indices in ((face[0],face[1],face[2]), (face[0],face[2],face[3])):
            a,b,c=[scratch.v[k] for k in indices]
            e1,e2=sub(b,a),sub(c,a)
            h=cross(direction,e2)
            determinant=dot(e1,h)
            if abs(determinant)<1e-9: continue
            inv=1/determinant
            s=sub(origin,a)
            u=inv*dot(s,h)
            if not -1e-7<=u<=1+1e-7: continue
            q=cross(s,e1)
            v=inv*dot(direction,q)
            if v < -1e-7 or u+v > 1+1e-7: continue
            t=inv*dot(e2,q)
            if t>=0: hits.append(t)
    assert hits and abs(min(hits)-bay['depth']-1)<1e-6, ('Covered recess mouth',hits,bay)
    def elevation(p):
        return math.atan2(p[2]-220.0, math.hypot(p[0],p[1]))
    width = min(new._projected_edge_pixels(back[0],back[1]),
                new._projected_edge_pixels(back[3],back[2]))
    height = min(abs(elevation(back[3])-elevation(back[0])),
                 abs(elevation(back[2])-elevation(back[1]))) * 8192/(2*math.pi)
    bay_records.append(dict(width_px=width, height_px=height, depth_m=bay['depth']))
    return original_bay(acc, pts, uvs, col, bay)


new._inset_service_bay = capture_bay
counts, old_faces, new_faces, near_exact, lots_with_bays = Counter(), 0, 0, 0, 0
min_px, max_px = [math.inf, math.inf], [0.0,0.0]
total_bays = 0
for i, p in enumerate(lots):
    angle = i * .713
    kw = {k:p[k] for k in ('cx','cy','w','d','h','seed','distance')}
    kw.update(ang=angle, pal=(i%19)/19, far=p['distance']>11000, source_spire=p['spire'])
    def build(module, height=0):
        city = SimpleNamespace(cyber=Acc('wall'), cyber_roof=Acc('roof'), neon=Acc('glow'))
        state = random.getstate()
        result = module.build_cyber_block(city, **kw, base_z=height)
        assert state == random.getstate(), 'Global RNG changed'
        return city,result
    outer_before.clear()
    outer_after.clear()
    bay_records.clear()
    baseline, expected = build(old)
    new.reset_depth_detail_report()
    current, result = build(new)
    actual_report = new.depth_detail_report()
    assert actual_report['build_calls']==1 and actual_report['service_bays']==len(bay_records)
    assert actual_report['calls'][0]['ang']==angle and actual_report['calls'][0]['distance']==p['distance']
    assert outer_before == outer_after, ('Structural silhouette changed',i)
    assert {k:v for k,v in expected.items() if k!='version'} == {
        k:v for k,v in result.items() if k!='version'}, ('Returned host geometry changed',i)
    counts[result['archetype_name']] += 1
    total_bays += len(bay_records)
    lots_with_bays += bool(bay_records)
    for r in bay_records:
        assert min(r['width_px'],r['height_px']) >= 2.0, ('Subpixel service back',i,r)
        for j,k in enumerate(('width_px','height_px')):
            min_px[j],max_px[j] = min(min_px[j],r[k]),max(max_px[j],r[k])
    for name in ('cyber_roof','neon'):
        a,b = getattr(baseline,name),getattr(current,name)
        assert (a.v,a.f,a.uv,a.col)==(b.v,b.f,b.uv,b.col), (name+' changed',i)
    if p['distance'] < new.DEPTH_DETAIL_START:
        a,b = baseline.cyber,current.cyber
        assert (a.v,a.f,a.uv,a.col)==(b.v,b.f,b.uv,b.col), ('Close architecture changed',i)
        near_exact += 1
    outer_after.clear()
    raised,again = build(new,713)
    for name in ('cyber','cyber_roof','neon'):
        a,b = getattr(current,name),getattr(raised,name)
        assert (a.f,a.uv,a.col)==(b.f,b.uv,b.col), ('Elevated topology/materials changed',i)
        assert len(a.v)==len(b.v)
        for v,q in zip(a.v,b.v):
            x,y,z=v
            assert all(math.isfinite(c) for c in v)
            dx,dy=x-p['cx'],y-p['cy']
            lx=dx*math.cos(angle)+dy*math.sin(angle)
            ly=-dx*math.sin(angle)+dy*math.cos(angle)
            assert abs(lx)<=p['w']/2+1e-6 and abs(ly)<=p['d']/2+1e-6, ('Lot overflow',i,name,v)
            assert -1e-6<=z<=p['h']+1e-6, ('Height overflow',i,z,p['h'])
            assert abs(q[0]-x)<1e-7 and abs(q[1]-y)<1e-7 and abs(q[2]-z-713)<1e-7
    old_faces += sum(len(getattr(baseline,n).f) for n in ('cyber','cyber_roof','neon'))
    new_faces += sum(len(getattr(current,n).f) for n in ('cyber','cyber_roof','neon'))

assert set(counts)==set(new.ARCHETYPES)
assert lots_with_bays > 250, ('Too little outer-city detail coverage',lots_with_bays)
assert new_faces < old_faces*1.15, 'Unbounded geometry growth'
receipt = dict(status='pass', version=new.ARCHITECTURE_VERSION,
    candidate_source=CURRENT.relative_to(ROOT).as_posix(),
    sampled_lots=len(lots), pose_sampling='real lot positions/dimensions/seeds; deterministic test angles/palettes',
    exact_structural_mass_lofts=True, exact_neon_geometry_uv_colors=True,
    exact_roof_geometry=True, exact_close_lots=near_exact, global_rng_unchanged=True,
    exact_elevated_translation_m=713, archetypes=dict(counts),
    inset_winding_and_opening_probe='pass: geometric ray reaches inset back without original-wall lid',
    in_memory_actual_build_collector='verified; root author wrapper must capture actual production calls',
    lots_with_resolved_service_bays=lots_with_bays, resolved_service_bays=total_bays,
    inset_back_pixels_at_8192=dict(min_width=min_px[0],min_height=min_px[1],max_width=max_px[0],max_height=max_px[1]),
    faces_before=old_faces,faces_after=new_faces,face_growth_percent=(new_faces/old_faces-1)*100,
    bounds='original local w/d/h; no outer bulk moved',
    limitations='Unoccluded angular size only, before lighting/denoise. Render-time scene/layout/clearance and matched visual review still required.',
    native_visual_verified=False)
receipt['source_hashes'] = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (BEFORE,CURRENT,LOTS,Path(__file__),ROOT/'tools/sky3d/build_city.py',
              ROOT/'tools/sky3d/cyber_coverage.py',Path(__file__).with_name('pass_config.py'))}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
