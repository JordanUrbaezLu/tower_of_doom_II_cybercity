"""Exercise real accumulator geometry: bounds, elevation and RNG independence."""
import ast
import json
import math
import pathlib
import random
import sys
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/sky3d'))
from cyber_architecture import build_cyber_block, ARCHETYPES
from cyber_coverage import modernize_lot

tree = ast.parse((ROOT / 'tools/sky3d/build_city.py').read_text(encoding='utf-8'))
acc_node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Acc')
namespace = {'math': math}
exec(compile(ast.Module(body=[acc_node], type_ignores=[]), 'actual_sky_accumulator', 'exec'), namespace)
Acc = namespace['Acc']
old = json.loads((ROOT / 'tmp/sky_simplify/raw_4096.composition.json').read_text())
lots = [p for p in old['buildings'] if p['kept'] and modernize_lot(p['spire'], p['h'], p['distance'])]
seen = set()
vertices = 0
for i, p in enumerate(lots):
    angle = i * 0.713
    kw = {k:p[k] for k in ('cx','cy','w','d','h','seed','distance')}
    kw.update(ang=angle, pal=(i % 19)/19, far=p['distance']>11000, source_spire=p['spire'])
    def build(z):
        city = SimpleNamespace(cyber=Acc('wall'), cyber_roof=Acc('roof'), neon=Acc('glow'))
        state = random.getstate()
        result = build_cyber_block(city, **kw, base_z=z)
        assert state == random.getstate(), 'Global RNG changed'
        return city, result
    city, result = build(0)
    raised, again = build(713.0)
    seen.add(result['archetype_name'])
    for name in ('cyber','cyber_roof','neon'):
        a,b = getattr(city,name),getattr(raised,name)
        assert a.f == b.f and a.uv == b.uv and a.col == b.col, 'Translation changed topology/materials'
        for v,q in zip(a.v,b.v):
            x,y,z=v
            assert all(math.isfinite(c) for c in v)
            dx,dy=x-p['cx'],y-p['cy']
            lx=dx*math.cos(angle)+dy*math.sin(angle)
            ly=-dx*math.sin(angle)+dy*math.cos(angle)
            assert abs(lx)<=p['w']/2+1e-6 and abs(ly)<=p['d']/2+1e-6, ('lot overflow',i,name,v)
            assert -1e-6<=z<=p['h']+1e-6, ('height overflow',i,z,p['h'])
            assert abs(q[0]-x)<1e-7 and abs(q[1]-y)<1e-7 and abs(q[2]-z-713)<1e-7
        vertices += len(a.v)
assert seen == set(ARCHETYPES)
assert modernize_lot(True,399.9,6999.9)
assert not modernize_lot(True,400,6999)
assert not modernize_lot(True,399,7000)
for h,d in ((0,1),(1,-1),(float('nan'),1),(1,float('inf'))):
    try: modernize_lot(True,h,d)
    except ValueError: pass
    else: raise AssertionError('Invalid coverage accepted')
receipt={'status':'pass','ordinary_lots':len(lots),'vertices_checked':vertices,
         'archetypes':sorted(seen),'bounds':'original local w/d/h','elevated_translation_m':713,
         'global_rng_unchanged':True,'native_visual_verified':False}
out=ROOT/'art/sky3d/middle_ground_review/architecture_check.json'
out.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
