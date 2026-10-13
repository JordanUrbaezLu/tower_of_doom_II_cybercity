"""THE WAR DAMAGE PASS, phase 2 (docs/205 s7): the GENERATED effects - never hand-edit the .efx.

  python tools/war_damage/make_fx.py           write share/raw/fx/tod/war/*.efx (+ art/war_damage/fx_tables.json)
  python tools/war_damage/make_fx.py --check   FAIL if any written effect differs from a fresh generation

Composed from the sky fleet's element templates (tools/sky_ships/gen_fx.py mk(): stock BO3 materials and element
types, every number explicit) the way the lucky pass does (tools/lucky/make_fx.py), plus the perk glow's dynamic
light element for the real lights.

THE BROKEN LIGHTS (on the dangling fixtures beside every blast crater; _tod_war_damage.csc plays one LOOPING per fixture
once the power is back, with a budgeted dynamic light):
  fx_war_tube_flicker_a   a nervous stutter: on, off, on-on, off ... (loop 2.4 s)
  fx_war_tube_flicker_b   a dying buzz: long dark, a slow warm-up, a burst, dark (loop 3.1 s)
  fx_war_tube_flicker_c   nearly dead: black, then it catches for a moment, twice (loop 4.0 s)
  Each: three cool-white glow points along the tube (effect +X runs along it) whose alpha follows the SAME curve as the
  light's intensity, and a cold dynamic light (radius TUBE_LIGHT_RADIUS, peak TUBE_LIGHT_PEAK). The flicker lives in the
  curves (docs/162 ch 04): one looping element per part, life = the loop, so the pattern repeats seamlessly.
THE LIVE CONDUCTORS (the torn conduits' free ends, powered):
  fx_war_arc              a cyan-white arc that flickers at the torn mouth, blue sparks dripping off it, a faint halo
THE WAR IN THE SKY (_tod_war_sky.csc, far over the horizon, drawn inside the sealed sky box):
  fx_war_sky_flash_s/m/l  a far detonation: a hot core that snaps on and dies, a wider warm halo lingering, a smoke knot
  fx_war_sky_tracer_c/o   one tracer round (cyan plasma / orange) flying along +X: a bright runner with a short streak
  fx_war_sky_hit          a tracer landing: a small flash + sparks
  fx_war_sky_wreck_s/l    LOOPING on a stricken ship's tag_origin: fire and sparks pouring off it, black smoke left
                          in the world behind it (two sizes: the drawn stand-in is small / large)
  fx_war_sky_impact       the wreck hitting the city: a big flash, a fireball, a rising smoke column, embers
"""
import importlib.util, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKY_GEN = ROOT / 'tools/sky_ships/gen_fx.py'
OUT = ROOT / 'share/raw/fx/tod/war'
TABLES = ROOT / 'art/war_damage/fx_tables.json'
PREFIX = 'tod/war/'
MAX_PATH = 63


def load_sky_builder():
    spec = importlib.util.spec_from_file_location('sky_gen_fx_lib', SKY_GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    S = load_sky_builder()
except Exception as ex:
    print('WAR FX: cannot load the sky fleet element builder (%s): %s: %s' % (SKY_GEN.relative_to(ROOT), type(ex).__name__, ex))
    sys.exit(1)
E = S.E

# ---- colour (linear RGB) -------------------------------------------------------------------------------------------------
TUBE = (0.80, 0.92, 1.0)               # a cold LED tube
TUBE_HOT = (0.95, 0.98, 1.0)
ARC = (0.72, 0.95, 1.0)                # the conductors' cyan-white arc
ARC_BLUE = (0.35, 0.70, 1.0)
FLASH_CORE = (1.0, 0.96, 0.86)
FLASH_WARM = (1.0, 0.62, 0.28)
FLASH_RED = (0.85, 0.28, 0.08)
SMOKE_DARK = (0.16, 0.15, 0.15)
TRACER_C = (0.55, 0.92, 1.0)
TRACER_O = (1.0, 0.70, 0.30)
FIRE = (1.0, 0.58, 0.18)
EMBER = (1.0, 0.45, 0.12)

# ---- the lights (THE KNOBS if a broken tube reads too bright / dim in game) -------------------------------------------------
TUBE_LIGHT_PEAK = 380                  # the perk glow's donor light: 512; the stair route pools are ~630
TUBE_LIGHT_RADIUS = 220
LIGHT_RANGE = 3000

# ---- the flicker patterns: (t 0..1, level 0..1) over the loop; held steps (two rows at the same level) ----------------------
LOOPS = {'a': 2400, 'b': 3100, 'c': 4000}
PATTERN = {
    'a': [(0, 0.9), (0.06, 0.9), (0.07, 0), (0.15, 0), (0.16, 1.0), (0.21, 1.0), (0.22, 0.15), (0.26, 0.15), (0.27, 0.95), (0.33, 0.95),
          (0.34, 0), (0.46, 0), (0.47, 0.8), (0.49, 0.8), (0.5, 0), (0.55, 0), (0.56, 1.0), (0.7, 1.0), (0.71, 0.1), (0.74, 0.1),
          (0.75, 0.85), (0.84, 0.85), (0.85, 0), (0.93, 0), (0.94, 0.9), (1, 0.9)],
    'b': [(0, 0), (0.3, 0), (0.31, 0.12), (0.45, 0.35), (0.55, 0.55), (0.56, 1.0), (0.6, 1.0), (0.61, 0.3), (0.64, 0.3), (0.65, 0.9),
          (0.72, 0.9), (0.73, 0.05), (0.8, 0.05), (0.81, 0.6), (0.83, 0.6), (0.84, 0), (1, 0)],
    'c': [(0, 0), (0.42, 0), (0.43, 0.7), (0.46, 0.7), (0.47, 0), (0.49, 0), (0.5, 1.0), (0.52, 1.0), (0.53, 0.2), (0.56, 0.2),
          (0.57, 0), (0.78, 0), (0.79, 0.5), (0.8, 0.5), (0.81, 0), (1, 0)],
}
TUBE_POINTS = (-18, 0, 18)             # along the effect's +X = along the tube (the fixture is ~56 long)


def el(tkey, name, **kw):
    return S.mk(tkey, name, **kw)


def box(half):
    return (-half, -half, -half), (half, half, half)


def in_world(e, **axes):
    for ax, v in axes.items():
        S.graph(e, 'velGraph1' + ax, v[0], v[1], v[2] if len(v) > 2 else None)
    e.set_flags('editorFlags', add=('useRandVel1',))
    return e


def spread(v, decay=1.0):
    return (2 * v, [(0, -0.5), (1, -0.5 * decay)], [(0, 0.5), (1, 0.5 * decay)])


def near_fade(e, start, width):
    e.set('fadeOutRange', [start, width])
    return e


def light(name, peak, radius, rgb, loop_ms, curve):
    """The perk glow's dynamic light element (tools/lucky/make_fx.py golden_light()), looping every loop_ms with its
    intensity following `curve` (t, level) - the flicker IS the curve."""
    donor = E.load(S.GLOW_DONOR)
    e = [x for x in donor.elements if x.name == 'light_small'][0].copy()
    e.name = name
    e.set('editorFlags', 'looping')
    e.set_flags('flags', remove=('spawnFrustumCull',))
    e.set('spawnRange', (0, LIGHT_RANGE))
    e.set('spawnLooping', (loop_ms, 0))
    e.set('lifeSpanMsec', (loop_ms, 0))
    e.set('spawnOrgZ', (0, 0))
    S.graph(e, 'lightIntensityGraph', peak, curve)
    S.graph(e, 'lightRadiusGraph', radius, [(0, 1), (1, 1)])
    S.graph(e, 'colorGraph', 1.0, [(0,) + rgb, (1,) + rgb])
    S.graph(e, 'alphaGraph', 1.0, [(0, 1), (1, 1)])
    for it in e.items:
        if isinstance(it, E.Block) and it.key == 'dynamicLight2':
            body = []
            for line in it.body:
                key = line.strip().split(' ')[0]
                tabs = line[:len(line) - len(line.lstrip())]
                if key == '_color':
                    line = tabs + '_color 1 1 1'
                elif key == 'radius':
                    line = tabs + 'radius %d' % radius
                body.append(line)
            it.body = body
    return e


# =========================================================================================================================
# THE BROKEN TUBES
# =========================================================================================================================
def tube_flicker(kind):
    loop, pat = LOOPS[kind], PATTERN[kind]
    els = []
    for i, x in enumerate(TUBE_POINTS):
        # the tube's glow follows the light's curve exactly (alpha = level); a hot core inside it
        els.append(el('glow', 'tube_%d' % i, loop=(loop, 0), life=(loop, 0), org=(x, 0, 0), size=(22, [(0, 1), (1, 1)]),
                      color=TUBE, alpha=[(t, 0.85 * v) for t, v in pat]))
        els.append(el('core_hot', 'core_%d' % i, loop=(loop, 0), life=(loop, 0), org=(x, 0, 0), size=(9, [(0, 1), (1, 1)]),
                      color=TUBE_HOT, alpha=[(t, 0.9 * v) for t, v in pat]))
    els.append(light('light', TUBE_LIGHT_PEAK, TUBE_LIGHT_RADIUS, TUBE, loop, pat))
    if kind == 'b':
        # the dying tube spits a spark at its broken end as it bursts on (the pattern's 0.56 step)
        els.append(in_world(el('spark', 'end_spark', loop=(loop, 0), life=(260, 80), delay=(int(loop * 0.56), 0), count=(3, 2),
                               org=(22, 0, -1), size=(0.6, [(0, 1), (1, 0.4)]), size1=(5, [(0, 1), (1, 0.4)]),
                               vel={'X': spread(40), 'Y': spread(40)}, color=TUBE_HOT, alpha=[(0, 1), (1, 0)], run='world'),
                            Z=(-90, [(0, 0), (1, 1)])))
    return els


# =========================================================================================================================
# THE LIVE CONDUCTORS' ARC
# =========================================================================================================================
def arc():
    flick = [(0, 0), (0.1, 1), (0.25, 0.3), (0.4, 1), (0.5, 0), (0.62, 0.7), (0.78, 0.2), (0.86, 1), (1, 0)]
    return [
        el('arc', 'arc', loop=(140, 60), life=(170, 50), org=(0, 0, 0), org_rand=(2, 2, 2), size=(7, [(0, 0.6), (0.5, 1), (1, 0.7)], [(0, 0.5), (0.5, 0.9), (1, 0.6)]),
           color=ARC, alpha=flick, spin=((0, 360), (-200, 200))),
        el('glow', 'halo', loop=(90, 0), life=(180, 0), size=(14, [(0, 1), (1, 1)]), color=ARC_BLUE,
           alpha=[(0, 0.15), (0.3, 0.45), (0.6, 0.2), (1, 0.05)]),
        in_world(el('spark', 'drip', loop=(220, 120), life=(520, 180), count=(2, 2), size=(0.45, [(0, 1), (1, 0.3)]), size1=(3, [(0, 1), (1, 0.3)]),
                    vel={'X': spread(26), 'Y': spread(26), 'Z': spread(16)}, color=ARC_BLUE, alpha=[(0, 1), (0.8, 0.7), (1, 0)], run='world'),
                 Z=(-260, [(0, 0), (1, 1)])),
    ]


# =========================================================================================================================
# THE WAR IN THE SKY
# =========================================================================================================================
FLASH = {'s': 700, 'm': 1500, 'l': 3000}     # the hot core's size (units) at the drawn point (~9,000-11,500 u away)


def sky_flash(size):
    L = int(900 + size * 0.25)
    return [
        near_fade(el('core_hot', 'core', oneshot=(1, 0), life=(int(L * 0.45), 0), size=(size, [(0, 0.3), (0.08, 1), (1, 0.55)]),
                     color=FLASH_CORE, alpha=[(0, 1), (0.2, 1), (1, 0)]), 400, 600),
        near_fade(el('glow', 'halo', oneshot=(1, 0), life=(L, 0), size=(size * 2.2, [(0, 0.5), (0.15, 1), (1, 1.3)]),
                     color=FLASH_WARM, alpha=[(0, 0.9), (0.3, 0.55), (1, 0)]), 400, 600),
        near_fade(el('glow', 'ember', oneshot=(1, 0), life=(int(L * 1.6), 0), size=(size * 1.2, [(0, 0.8), (1, 1.6)]),
                     color=FLASH_RED, alpha=[(0, 0.5), (0.5, 0.25), (1, 0)]), 400, 600),
        in_world(el('smoke', 'knot', oneshot=(3, 1), life=(int(L * 4), int(L)), offset='sphere', off_r=(size * 0.25, size * 0.15),
                    size=(size * 0.8, [(0, 0.6), (1, 2.0)]), color=SMOKE_DARK, alpha=[(0, 0), (0.15, 0.55), (1, 0)]),
                 Z=(size * 0.12, [(0, 1), (1, 0.4)])),
    ]


TRACER = (4200, 380)                         # speed (u/s), life (ms): ~1,600 u of flight, a dash of ~8 degrees at 11,000 u


def sky_tracer(col):
    v, L = TRACER
    return [
        el('runner', 'round', oneshot=(1, 0), life=(L, 0), size=(34, [(0, 0.7), (0.15, 1), (1, 0.8)]), vel={'X': (v, [(0, 1), (1, 1)])},
           color=(1.0, 1.0, 1.0), alpha=[(0, 0), (0.1, 1), (0.8, 1), (1, 0)], run='spawn'),
        el('orb', 'glow', oneshot=(1, 0), life=(L, 0), size=(90, [(0, 0.8), (1, 1)]), vel={'X': (v, [(0, 1), (1, 1)])},
           color=col, alpha=[(0, 0), (0.1, 0.6), (0.8, 0.5), (1, 0)], run='spawn'),
        el('ray_thin', 'streak', oneshot=(1, 0), life=(L, 0), size=(18, [(0, 1), (1, 1)]), size1=(420, [(0, 0.3), (0.3, 1), (1, 1)]),
           vel={'X': (v, [(0, 1), (1, 1)])}, color=col, alpha=[(0, 0), (0.15, 0.7), (0.85, 0.6), (1, 0)], run='spawn'),
    ]


def sky_hit():
    return [
        el('core_hot', 'flash', oneshot=(1, 0), life=(220, 0), size=(260, [(0, 0.5), (0.2, 1), (1, 0.6)]), color=FLASH_CORE, alpha=[(0, 1), (1, 0)]),
        el('glow', 'halo', oneshot=(1, 0), life=(520, 0), size=(640, [(0, 0.6), (0.3, 1), (1, 1.2)]), color=FLASH_WARM, alpha=[(0, 0.8), (1, 0)]),
        el('incand', 'sparks', oneshot=(8, 4), life=(600, 250), size=(26, [(0, 1), (1, 0.2)]),
           vel={'X': spread(500), 'Y': spread(500), 'Z': spread(500)}, color=EMBER, alpha=[(0, 1), (1, 0)], run='spawn'),
    ]


WRECK = {'s': 1.0, 'l': 2.4}                 # the two trail sizes (x): the drawn stand-in is ~1,000 / ~2,500 u long


def sky_wreck(k):
    return [
        # fire pouring off the hull (effect-relative: it rides the ship), its tail blown back along the flight (-X)
        el('fire', 'fire', loop=(60, 20), life=(520, 160), count=(2, 1), org=(-200 * k, 0, 0), org_rand=(260 * k, 120 * k, 80 * k),
           size=(70 * k, [(0, 0.6), (0.4, 1), (1, 0.4)]), size1=(200 * k, [(0, 0.6), (1, 1)]), vel={'X': (-900 * k, [(0, 1), (1, 1)])},
           color=FIRE, alpha=[(0, 0), (0.15, 0.95), (0.7, 0.6), (1, 0)]),
        el('glow', 'heat_glow', loop=(90, 0), life=(300, 0), org=(-100 * k, 0, 0), org_rand=(150 * k, 80 * k, 60 * k),
           size=(260 * k, [(0, 0.8), (1, 1.2)]), color=EMBER, alpha=[(0, 0.5), (1, 0)]),
        # sparks and embers stripped off into the world
        in_world(el('spark', 'sparks', loop=(70, 30), life=(900, 300), count=(3, 2), org=(-150 * k, 0, 0), org_rand=(220 * k, 100 * k, 60 * k),
                    size=(1.2 * k, [(0, 1), (1, 0.4)]), size1=(14 * k, [(0, 1), (1, 0.4)]), vel={'X': spread(120 * k), 'Y': spread(120 * k), 'Z': spread(60 * k)},
                    color=EMBER, alpha=[(0, 1), (1, 0)], run='world'),
                 Z=(-600, [(0, 0), (1, 1)])),
        # black smoke left behind in the world (fade in: it is not born at full size in the ship)
        in_world(el('smoke', 'smoke', loop=(110, 30), life=(3800, 900), count=(1, 1), org=(-240 * k, 0, 0), org_rand=(160 * k, 80 * k, 60 * k),
                    size=(110 * k, [(0, 0.4), (1, 2.6)]), color=SMOKE_DARK, alpha=[(0, 0), (0.12, 0.6), (0.8, 0.35), (1, 0)], run='world',
                    spin=((0, 360), (-20, 20))),
                 Z=(40 * k, [(0, 1), (1, 1)])),
    ]


def sky_impact():
    return [
        near_fade(el('core_hot', 'flash', oneshot=(1, 0), life=(380, 0), size=(2600, [(0, 0.3), (0.1, 1), (1, 0.6)]), color=FLASH_CORE, alpha=[(0, 1), (0.3, 0.9), (1, 0)]), 400, 600),
        near_fade(el('glow', 'fireball', oneshot=(1, 0), life=(1600, 0), size=(3600, [(0, 0.4), (0.25, 1), (1, 1.5)]), color=FLASH_WARM, alpha=[(0, 1), (0.4, 0.5), (1, 0)]), 400, 600),
        near_fade(el('glow', 'afterglow', oneshot=(1, 0), life=(3200, 0), size=(2400, [(0, 0.8), (1, 1.8)]), color=FLASH_RED, alpha=[(0, 0.6), (0.5, 0.3), (1, 0)]), 400, 600),
        in_world(el('smoke', 'column', oneshot=(6, 2), life=(7000, 2000), delay=(200, 300), offset='sphere', off_r=(500, 300),
                    size=(900, [(0, 0.5), (1, 2.6)]), color=SMOKE_DARK, alpha=[(0, 0), (0.1, 0.6), (0.8, 0.35), (1, 0)], spin=((0, 360), (-12, 12))),
                 Z=(380, [(0, 1), (1, 0.5)])),
        in_world(el('incand', 'embers', oneshot=(14, 6), life=(1800, 600), size=(60, [(0, 1), (1, 0.2)]),
                    vel={'X': spread(1100), 'Y': spread(1100)}, color=EMBER, alpha=[(0, 1), (0.7, 0.8), (1, 0)], run='world'),
                 Z=(1400, [(0, 0.8), (1, -0.6)], [(0, 1.2), (1, -0.4)])),
    ]


# =========================================================================================================================
def build():
    out = {}
    for kind in LOOPS:
        out['fx_war_tube_flicker_' + kind] = S.effect(tube_flicker(kind), (-40, -40, -40), (40, 40, 40))
    out['fx_war_arc'] = S.effect(arc(), (-40, -40, -60), (40, 40, 40))
    for tag, size in FLASH.items():
        b = size * 3
        out['fx_war_sky_flash_' + tag] = S.effect(sky_flash(size), (-b, -b, -b), (b, b, b))
    out['fx_war_sky_tracer_c'] = S.effect(sky_tracer(TRACER_C), (-300, -300, -300), (TRACER[0] * TRACER[1] / 1000.0 + 300, 300, 300))
    out['fx_war_sky_tracer_o'] = S.effect(sky_tracer(TRACER_O), (-300, -300, -300), (TRACER[0] * TRACER[1] / 1000.0 + 300, 300, 300))
    out['fx_war_sky_hit'] = S.effect(sky_hit(), *box(1200))
    for tag, k in WRECK.items():
        w = 4000 * k                                                    # the world-space smoke stays behind the falling ship
        out['fx_war_sky_wreck_' + tag] = S.effect(sky_wreck(k), (-w - 600 * k, -500 * k, -500 * k), (600 * k, 500 * k, 500 * k))
    out['fx_war_sky_impact'] = S.effect(sky_impact(), (-4000, -4000, -1000), (4000, 4000, 9000))
    return out


def tables():
    return {'loops_ms': LOOPS, 'tube_light': {'peak': TUBE_LIGHT_PEAK, 'radius': TUBE_LIGHT_RADIUS}, 'flash_sizes': FLASH,
            'tracer': {'speed': TRACER[0], 'life_ms': TRACER[1]}, 'wreck_sizes': WRECK, 'tube_points': list(TUBE_POINTS)}


def main(argv):
    fx = build()
    tab = json.dumps(tables(), indent=1, sort_keys=True) + '\n'
    for n in fx:
        assert len(PREFIX + n) < MAX_PATH, n
    for n, t in fx.items():
        assert 'gfx_debug_missing_fx' not in t and '_pcloud' not in t, n
        for child in __import__('re').findall(r'"(tod/[^"]+)"', t):
            assert child.split('/')[-1] in fx and child.startswith(PREFIX), (n, child)
    if '--check' in argv:
        bad = [n for n, t in fx.items() if not (OUT / (n + '.efx')).exists() or (OUT / (n + '.efx')).read_bytes() != t.encode('utf-8')]
        stray = [p.stem for p in OUT.glob('*.efx') if p.stem not in fx] if OUT.exists() else []
        if not TABLES.exists() or TABLES.read_text(encoding='utf-8') != tab:
            bad.append('fx_tables.json')
        if bad or stray:
            print('WAR FX STALE:', ', '.join(bad + ['stray ' + s for s in stray]), '- run python tools/war_damage/make_fx.py')
            return 1
        print('WAR FX OK', len(fx))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob('*.efx'):
        if old.stem not in fx:
            old.unlink()
            print('WAR FX RETIRED', old.name)
    for n, t in fx.items():
        (OUT / (n + '.efx')).write_bytes(t.encode('utf-8'))
    TABLES.write_text(tab, encoding='utf-8', newline='\n')
    for n, t in fx.items():
        print('%-28s %2d elements %6d B' % (n, t.count('\n{'), len(t)))
    print('WAR FX WRITTEN: %d effects -> %s' % (len(fx), OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
