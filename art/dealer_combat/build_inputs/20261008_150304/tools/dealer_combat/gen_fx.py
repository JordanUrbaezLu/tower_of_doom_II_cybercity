"""Dealer weapon warnings and impacts. Deterministic native composition, existing sprite family.

No modification to the shipping Dealer/sky generators. --root stages a complete set;
--check validates bytes, bounded particles, lights and all native dependencies.
"""
import argparse
import csv
import importlib.util
import math
import pathlib
import sys

sys.dont_write_bytecode = True
REPO = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('dealer_weapon_fx', REPO / 'tools/dealer_fx/gen_fx.py')
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)
S, L = D.S, D.L
PREFIX = 'tod/dealer_combat/'
L.PREFIX = PREFIX
OUT = pathlib.Path('share/raw/fx/tod/dealer_combat')
RED = (1.0, 0.055, 0.035)
GOLD = (1.0, 0.45, 0.10)


def bead(name, org, impact=False):
    return D.el('spark_omni', name, loop=(160, 0), life=(160, 0), org=org,
                size=(6 if impact else 3.0, [(0, .65), (.45, 1), (1, .65)]),
                color=RED, alpha=[(0, .75), (.5, .9), (1, .75)])


def warning():
    # Real footprint: radius 100. Upright floor ring, no billboard disc at the eye.
    els = [bead('rim_%02d' % i, (100 * math.cos(i*math.tau/24), 100 * math.sin(i*math.tau/24), 3)) for i in range(24)]
    els += [D.el('spark_blink', 'failure', loop=(180, 0), life=(240, 0), org=(-18, -18, 5), org_rand=(36, 36, 15),
                 size=(3, [(0, .4), (.4, 1), (1, 0)]), color=RED, alpha=[(0, 0), (.25, .7), (1, 0)])]
    return els


def charge():
    return [D.el('arc', 'coil_arcs', loop=(120, 0), life=(200, 0), size=(22, [(0, .5), (.5, 1), (1, .2)]),
                 color=GOLD, alpha=[(0, 0), (.2, .55), (1, 0)]),
            D.el('spark_omni', 'coil_heart', loop=(180, 0), life=(180, 0), size=(7, [(0, .5), (.6, 1), (1, .5)]),
                 color=GOLD, alpha=[(0, .5), (1, .8)]),
            D.light('coil_light', GOLD, 100, 45, every=180, life=180,
                    curve=[(0, 0), (.08, 1), (.92, 1), (1, 0)])]


def shock():
    els = [bead('edge_%02d' % i, (100*math.cos(i*math.tau/24), 100*math.sin(i*math.tau/24), 3), True) for i in range(24)]
    els += [D.el('arc', 'ground_arc', loop=(90, 0), life=(170, 0), org=(0, 0, 8),
                 size=(90, [(0, .6), (.4, 1), (1, .3)]), color=GOLD, alpha=[(0, 0), (.12, .55), (1, 0)]),
            D.el('spark', 'discharge', loop=(100, 0), life=(220, 80), count=(4, 0),
                 org=(-20, -20, 4), org_rand=(40, 40, 14), offset='sphere', off_r=(10, 30),
                 vel={'Z': (120, [(0, 1), (1, .1)])}, size=(1.3, [(0, 1), (1, .2)]),
                 color=GOLD, alpha=[(0, .8), (1, 0)])]
    return els


def muzzle():
    return [D.el('spark_omni', 'flash', loop=(90, 0), life=(90, 0),
                 size=(12, [(0, .7), (.2, 1), (1, .1)]), color=GOLD, alpha=[(0, .8), (1, 0)]),
            D.el('spark', 'hot_flecks', loop=(100, 0), life=(160, 20), count=(2, 0),
                 vel={'X': (90, [(0, 1), (1, .2)])}, size=(1, [(0, 1), (1, .1)]),
                 color=GOLD, alpha=[(0, .8), (1, 0)])]


def tracer():
    # Carrier moves down the traced path. No long ribbon, child FX, light or camera flare.
    return [D.el('spark_omni', 'slug', loop=(30, 0), life=(40, 0),
                 size=(3, [(0, 1), (1, .3)]), color=GOLD, alpha=[(0, .9), (1, 0)]),
            D.el('spark', 'streak', loop=(30, 0), life=(65, 0), run='spawn',
                 size=(.9, [(0, 1), (1, .1)]), size1=(12, [(0, 1), (1, .4)]),
                 color=GOLD, alpha=[(0, .7), (1, 0)])]


BUILDERS = {'warning': warning, 'charge': charge, 'shock': shock, 'muzzle': muzzle, 'tracer': tracer}


def build():
    D.register_templates()
    return {name: S.effect(fn(), (-160, -160, -160), (160, 160, 160)) for name, fn in BUILDERS.items()}


def curve_errors(name, text):
    bad=[]
    for element in D.E.parse(text).elements:
        for graph in element.items:
            if not isinstance(graph,D.E.Graph):continue
            for curve in graph.curves:
                times=[row[0] for row in curve]
                if not times or not all(0<=t<=1 for t in times) or any(a>=b for a,b in zip(times,times[1:])):
                    bad.append(name+'/'+element.name+'/'+graph.key+': curve times must strictly increase in 0..1')
    return bad


def check_native(ledger):
    rows=list(csv.DictReader(ledger.open(encoding='utf-8-sig',newline='')))
    for name in BUILDERS:
        path=PREFIX+'fx_dc_'+name
        matches=[r for r in rows if r['type']=='fx' and r['name']==path]
        assert len(matches)==1 and int(matches[0]['resident'])>0,('Missing/incomplete compiled Dealer effect',path)
    errors=ledger.with_suffix('.errorlog')
    assert errors.is_file(),'Missing linker error log: '+str(errors)
    assert PREFIX not in errors.read_text(encoding='utf-8-sig',errors='replace'),'Linker rejected a Dealer combat effect; inspect '+str(errors)
    print('DEALER COMBAT COMPILED FX OK: all five definitions resident; no linker complaint names this effect set')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=pathlib.Path, default=REPO)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--compiled-ledger', type=pathlib.Path)
    a = ap.parse_args()
    fx = build()
    names = ['fx_dc_' + n for n in fx]
    out = a.root / OUT
    bad = []
    for name, raw in fx.items():
        stem = 'fx_dc_' + name
        bad += L.validate(stem, raw, names)
        bad += curve_errors(stem,raw)
        p = out / (stem + '.efx')
        if a.check:
            if not p.exists() or p.read_text(encoding='utf-8') != raw:
                bad.append(str(p) + ' differs from the generator')
        else:
            out.mkdir(parents=True, exist_ok=True)
            p.write_text(raw, encoding='utf-8', newline='\n')
    if a.check and out.exists():
        bad += [p.name + ' stray effect' for p in out.glob('*.efx') if p.stem not in names]
    if bad:
        raise SystemExit('\n'.join(bad))
    if a.check:
        for invalid in (0,-.1):
            mutant=D.E.parse(fx['charge'])
            mutant.elements[-1].graph('lightIntensityGraph').curves[0][1][0]=invalid
            assert curve_errors('regression',mutant.text()),'Curve validator missed repeated/reversed timing'
    if a.compiled_ledger:check_native(a.compiled_ledger)
    print('DEALER COMBAT FX OK: 5 effects; strictly increasing curves; one small charge light; warnings/impacts/tracers unlit')


if __name__ == '__main__':
    main()
