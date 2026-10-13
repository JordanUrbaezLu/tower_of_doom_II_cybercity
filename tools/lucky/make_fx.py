"""THE LUCKY SOURCES' effects (docs/197), GENERATED - never hand-edit the .efx.

  python tools/lucky/make_fx.py              write share/raw/fx/tod/luck/fx_luck_*.efx (the 7 below) and retire any
                                             fx_luck_*.efx this generator no longer makes
  python tools/lucky/make_fx.py --check      regenerate in memory, validate, and FAIL (exit 1) if any written effect
                                             differs byte for byte, is missing, or a stray .efx sits in the folder
  python tools/lucky/make_fx.py --out DIR    write them somewhere else (a preview; the repo is untouched)

THE SEVEN EFFECTS (effect path = tod/luck/<name>; the scripts' _FX_ defines and the zone's fx, lines name them):
  fx_luck_meteor_trail   LOOPING on the tag_origin host linked to a Lucky Meteor rock (r ~150, ~550 u/s, seen 3,500-
                         6,500 u away): a burning GOLD comet - a long gold ribbon cooling to deep orange with a hot inner
                         core ribbon, gold-orange embers and a few lucky GREEN sparkles left behind, a dark smoke trail,
                         and a gold halo riding the rock.
  fx_luck_meteor_burst   ONE-SHOT where the meteor is shot apart: a big warm flash + a white-hot pop, ~40 gold embers and
                         ~24 green sparks flung in every direction, a smoke puff, a ring shockwave, and 4-6 burning
                         FRAGMENTS (runners) each dragging fx_luck_meteor_frag.
  fx_luck_meteor_frag    LOOPING child of each fragment: a thin gold streak + a few embers.
  fx_luck_clover_trail   LOOPING on the host of the falling Lucky Clover charm (~20 u; ~5,000 u in ~1.6 s, the streak leg
                         peaking near 7,000 u/s): the drop family's pale white-blue with a hint of mint - a thin streak,
                         sparkle embers, a soft halo.
  fx_luck_clover_land    ONE-SHOT on the floor where it lands (seen from 50-2,000 u): a quick white-blue flash, ~18
                         sparkles thrown up and out, an expanding thin ring.
  fx_luck_golden_aura    LOOPING on the host at a GOLDEN ZOMBIE's chest: gold motes left glittering in the air as it moves
                         (drifting UP, never flames), a soft gold body glow, quick twinkles - "made of treasure".
  fx_luck_golden_burst   ONE-SHOT at its chest when it dies: a gold flash, ~34 glinting coins thrown up and out that ARC
                         and FALL within ~1 s, a ring, a few green-gold sparkles floating up.

THE BUILDER IS THE SKY FLEET'S (session 9c): tools/sky_ships/gen_fx.py's template() / mk() / effect() / graph(), imported
READ-ONLY under its own module name (never modified; no bytecode written into its folder). Every element is a stock BO3
element from the sky fleet's VENDORED donor snapshots (art/sky_ships/fx_donors/ + map 1's glow,
share/raw/fx/acc/light/fx_perk_glow_amber.efx) with every visible number rewritten here, so a fresh generation is
byte-identical on any machine. mk() already opens every element for any distance (spawnRange 0..64000, no fade-in
range, no frustum cull, no collision). If the sky session changes mk() or a template, --check reports these effects
stale and one re-run follows it.

UNITS AND ENGINE RULES (read off stock effects, the numbers below depend on them):
  * sizes, offsets and velocities are world units (inches); 1 px ~ 3 u at 5,000 u. A velocity or size graph's value is
    scale x curve (the sky fleet's convention); a random pick between curve A and curve B per particle, per axis.
  * velGraph0 is the effect's LOCAL frame, velGraph1 the WORLD's (stock snow on a camera-attached effect falls with a
    negative velGraph1Z). Every upward drift / fountain here is WORLD velocity, so it stays upward whether the script
    plays the effect at a point or on a tilted bone's tag.
  * gravity is PERCENT OF WORLD GRAVITY (800 u/s^2 at 100): stock brass shell ejects use 100, blood drips 30, sparks
    35-50, floating anomaly debris 1.5-3, rising smoke/heat negative. The coins use 100-115 (they peak within ~0.2-0.6 s
    and are falling by ~1 s); embers and fragments droop at 8-45.
  * spawnLooping is (interval ms, loop COUNT) and COUNT 0 = forever (stock finite loops: 750x5, 400x12 ... ~5 s): every
    looping element here passes 0, and validate() fails a looping element with a count.
  * a TRAIL (laser_trail ribbon) loops at its own life with a short trailSplitDist (the stock pattern: pineapple 750/750
    split 32, bow 300/300 split 50), so the ribbon gets a vertex every few units of travel and tapers smoothly.
  * a LOOPING glow that must read as one steady light (the halos) spawns at half its life with a triangle alpha: two
    overlapping sprites sum to a CONSTANT brightness = the stated alpha (memory fx-overlap-count-before-alpha).
  * fadeOutRange is the NEAR-camera fade (stock teleport / PaP flashes: 100 100 on their big sprites). The two
    player-scale flashes (clover landing at your feet, golden zombie killed at melee range) fade within ~40-120 u so
    they never white out the screen; nothing fades by far distance (fadeInRange 0 0).

RULES THE WRITTEN FILES MUST PASS (validate(): the jump title's checks, tools/jump_title/gen_fx.py, plus ours): a bounding
box (and on a MOVING host a box that reaches back over the world-space particles it leaves behind at the host's top
speed, box_problems(): a box that misses a visible trail gets that trail culled), every element draws a material, no
model elements, a runner only when every child it names is generated here,
whole-millisecond lives / delays / loop intervals, no element sounds, spawnRange >= 64,000, no spawn frustum cull, no
collision, no far fade-in, no water-only / mature-only flags, alphas in 0..1, no gfx_debug_missing_fx stub, every child
path (attachment / fxOnDeath / fxOnImpact / emission) one of these seven, and THE 63-CHARACTER RULE: an effect path
(folder + name, no .efx) over 63 characters is cut at runtime and a parent spawning the cut child access-violates
(memory fx-name-63-char-limit-crashes; tools/lint_tod_fx_paths.js).
"""
import importlib.util
import math
import pathlib
import sys

sys.dont_write_bytecode = True        # the sky fleet's folders are read-only here: never leave a .pyc in them

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKY_GEN = ROOT / 'tools/sky_ships/gen_fx.py'
OUT = ROOT / 'share/raw/fx/tod/luck'
PREFIX = 'tod/luck/'
FAR = 64000
MAX_PATH = 63
PARTICLE_BUDGET = 200                  # peak live particles one effect may reach (its own elements)


def load_sky_builder():
    spec = importlib.util.spec_from_file_location('sky_gen_fx_lib', SKY_GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    S = load_sky_builder()
except Exception as ex:                # the sky session owns that file; say plainly whose file broke
    print('LUCKY FX: cannot load the sky fleet element builder (%s): %s: %s' % (SKY_GEN.relative_to(ROOT), type(ex).__name__, ex))
    sys.exit(1)
E = S.E
assert S.FAR == FAR, 'the sky builder opens elements to %s, not %d' % (S.FAR, FAR)

# ---- colour (linear RGB) -------------------------------------------------------------------------------------------------
GOLD = (1.0, 0.75, 0.25)               # the meteor's gold
GOLD_HOT = (1.0, 0.9, 0.62)
EMBER = (1.0, 0.62, 0.2)
DEEP = (0.85, 0.3, 0.07)               # deep orange: the comet's gold cools to it
LUCK_GREEN = (0.45, 1.0, 0.55)         # the lucky green
SMOKE = (0.3, 0.28, 0.27)              # a LIT smoke material: at night it reads as a dark band
DROP_WHITE = (0.8, 0.92, 1.0)          # the drop family's pale white-blue glow
MINT = (0.72, 1.0, 0.84)
TREASURE = (1.0, 0.82, 0.3)            # the golden zombie's gold

# ---- the hosts' top speeds (u/s): world-space particles are left behind a moving host, so its box must reach back over
# them (box_problems()). Read off the lucky scripts' motion (docs/197); revisit if _tod_lucky.gsc retimes a flight.
METEOR_SPEED = 550                     # TOD_METEOR_FLIGHT_SECS 13 across a ~7,000 u chord (80 deg at 4,500-6,500 u)
CLOVER_PEAK = 7000                     # TOD_CLOVER_STREAK_SECS 1.1 over up to ~6,500 u, easing out its last 30%
FRAG_PEAK = 1600                       # a fragment's fastest start (900 u/s on each axis)
ZOMBIE_SPRINT = 300                    # a sprinting golden zombie


# ---- element helpers -----------------------------------------------------------------------------------------------------
def el(tkey, name, **kw):
    """One element from the sky fleet's template tkey (mk() sets every visible number); remembers its template."""
    e = S.mk(tkey, name, **kw)
    e.lucky_template = tkey
    return e


def spread(v, decay=1.0):
    """A symmetric random velocity: -v..+v per particle at spawn, easing to -v*decay..+v*decay by the end of its life."""
    return (2 * v, [(0, -0.5), (1, -0.5 * decay)], [(0, 0.5), (1, 0.5 * decay)])


def xyz(v):
    return {'X': v, 'Y': v, 'Z': v}


def in_world(e, **axes):
    """WORLD-axis velocity (velGraph1<axis>) = (scale, curveA[, curveB]); upward stays upward on any host orientation."""
    for ax, v in axes.items():
        S.graph(e, 'velGraph1' + ax, v[0], v[1], v[2] if len(v) > 2 else None)
    e.set_flags('editorFlags', add=('useRandVel1',))
    return e


def ribbon(e, split, repeat):
    """A trail's geometry: a vertex every `split` units of travel, the texture repeating every `repeat` units."""
    e.set('trailSplitDist', int(split))
    e.set('trailRepeatDist', int(repeat))
    return e


def near_fade(e, start, width):
    """Fade the sprite out when the camera is within ~start..start+width units of it (stock: big flashes, 100 100)."""
    e.set('fadeOutRange', [start, width])
    return e


def steady(peak):
    """Triangle alpha: looped at half its life, two overlapping sprites sum to a constant `peak`."""
    return [(0, 0), (0.5, peak), (1, 0)]


def box(half):
    return (-half, -half, -half), (half, half, half)


# =========================================================================================================================
# THE LUCKY METEOR (seen 3,500-6,500 u away: at 5,000 u one pixel is ~3 units)
# =========================================================================================================================
def meteor_trail():
    return [
        # the comet's tail: a wide gold ribbon (180-200 u, ~65 px at 5,000 u) tapering and cooling to deep orange,
        # ~770 u long behind a 550 u/s rock, a vertex every 60 u
        ribbon(el('laser_trail', 'streak', loop=(1400, 0), life=(1400, 0), run='world',
                  size=(200, [(0, 1), (0.3, 0.68), (0.7, 0.36), (1, 0.16)], [(0, 0.9), (0.3, 0.6), (0.7, 0.32), (1, 0.14)]),
                  color=[(0,) + GOLD, (0.5, 1.0, 0.5, 0.14), (1,) + DEEP],
                  alpha=[(0, 0.9), (0.35, 0.62), (0.75, 0.24), (1, 0)]), 60, 800),
        # its hot inner core: a thin white-gold ribbon, half as long, so the tail is brightest at the rock
        ribbon(el('laser_trail', 'core', loop=(700, 0), life=(700, 0), run='world',
                  size=(70, [(0, 1), (0.4, 0.55), (1, 0.12)]),
                  color=[(0, 1.0, 0.96, 0.82), (0.5, 1.0, 0.8, 0.4), (1, 1.0, 0.6, 0.2)],
                  alpha=[(0, 0.95), (0.45, 0.5), (1, 0)]), 40, 400),
        # hot embers shed off the rock's surface and left behind, drooping a little
        el('incand', 'embers', loop=(30, 0), life=(700, 400), run='world', offset='sphere', off_r=(55, 25),
           size=(70, [(0, 1), (0.5, 0.62), (1, 0.15)], [(0, 0.72), (0.5, 0.45), (1, 0.1)]), vel=xyz(spread(45)),
           color=[(0, 1.0, 0.86, 0.46), (0.45,) + EMBER, (1,) + DEEP], alpha=[(0, 0.9), (0.6, 0.6), (1, 0)], grav=(8, 8)),
        # a few LUCKY green sparkles twinkling among the embers
        el('incand', 'sparkles', loop=(110, 0), life=(550, 350), run='world', offset='sphere', off_r=(40, 45),
           size=(24, [(0, 0.5), (0.15, 1), (0.6, 0.7), (1, 0)]), vel=xyz(spread(30)),
           color=[(0,) + LUCK_GREEN, (1, 0.3, 0.9, 0.42)], alpha=[(0, 0), (0.1, 1), (0.3, 0.4), (0.5, 1), (0.7, 0.35), (1, 0)]),
        # the dark smoke trail: a puff every 110 u, ~3 overlapping at any point (peak 0.3 each -> ~half opacity)
        el('smoke', 'smoke', loop=(200, 0), life=(2600, 800), run='world', offset='sphere', off_r=(30, 40),
           size=(300, [(0, 0.45), (0.3, 0.9), (1, 1.7)], [(0, 0.4), (0.3, 0.8), (1, 1.5)]), vel=xyz(spread(25)),
           color=SMOKE, alpha=[(0, 0), (0.12, 0.3), (0.55, 0.18), (1, 0)]),
        # the gold halo riding the rock (two overlapping sprites = a steady 0.45)
        el('orb', 'halo', loop=(90, 0), life=(180, 0), run='effect', size=(420, [(0, 0.96), (1, 1.04)]),
           color=GOLD, alpha=steady(0.45)),
    ]


def meteor_burst():
    return [
        el('glow', 'flash', oneshot=(1, 0), life=(380, 0), size=(1400, [(0, 0.55), (0.25, 1), (1, 1.1)]),
           color=(1.0, 0.85, 0.55), alpha=[(0, 1), (0.3, 0.75), (1, 0)]),
        el('core_hot', 'pop', oneshot=(1, 0), life=(220, 0), size=(620, [(0, 1), (1, 0.5)]),
           color=(1.0, 0.97, 0.88), alpha=[(0, 1), (1, 0)]),
        # ~41 gold embers flung every way at up to 900 u/s, slowing, drooping
        el('incand', 'embers', oneshot=(38, 6), life=(700, 400), run='spawn',
           size=(60, [(0, 1), (0.5, 0.65), (1, 0.15)], [(0, 0.7), (0.5, 0.45), (1, 0.1)]), vel=xyz(spread(900, 0.4)),
           color=[(0, 1.0, 0.88, 0.5), (0.35,) + EMBER, (1,) + DEEP], alpha=[(0, 1), (0.6, 0.8), (1, 0)], grav=(25, 20)),
        # ~24 lucky green sparks twinkling out with them
        el('incand', 'sparks_green', oneshot=(22, 4), life=(650, 400), run='spawn',
           size=(30, [(0, 1), (0.5, 0.7), (1, 0)]), vel=xyz(spread(700, 0.4)),
           color=[(0,) + LUCK_GREEN, (1, 0.3, 0.9, 0.42)],
           alpha=[(0, 1), (0.2, 0.5), (0.4, 1), (0.6, 0.45), (0.8, 0.8), (1, 0)], grav=(15, 15)),
        # the smoke left where the rock was
        el('smoke', 'smoke', oneshot=(5, 2), life=(2400, 700), delay=(40, 0), run='spawn', offset='sphere', off_r=(120, 120),
           size=(520, [(0, 0.5), (0.3, 1), (1, 1.9)]), vel=xyz(spread(120, 0.3)),
           color=(0.32, 0.29, 0.27), alpha=[(0, 0), (0.08, 0.3), (0.5, 0.18), (1, 0)]),
        el('ring', 'shockwave', oneshot=(1, 0), life=(620, 0), size=(2400, [(0, 0.08), (0.35, 0.7), (1, 1)]),
           color=(1.0, 0.86, 0.5), alpha=[(0, 0.9), (0.4, 0.55), (1, 0)]),
        # 4-6 burning fragments, each dragging its own gold streak (fx_luck_meteor_frag)
        el('runner', 'fragments', oneshot=(4, 2), life=(1300, 400), run='spawn', size=(55, [(0, 1), (1, 0.45)]),
           vel=xyz(spread(900, 0.6)), color=(1.0, 0.8, 0.4), alpha=[(0, 1), (0.75, 1), (1, 0)], grav=(30, 15),
           attach=PREFIX + 'fx_luck_meteor_frag'),
    ]


def meteor_frag():
    return [
        ribbon(el('laser_trail', 'streak', loop=(500, 0), life=(500, 0), run='world',
                  size=(40, [(0, 1), (0.4, 0.55), (1, 0.15)]), color=[(0, 1.0, 0.85, 0.4), (1,) + DEEP],
                  alpha=[(0, 0.9), (0.5, 0.45), (1, 0)]), 24, 300),
        el('incand', 'embers', loop=(70, 0), life=(350, 200), run='world', offset='sphere', off_r=(6, 8),
           size=(18, [(0, 1), (1, 0.2)]), vel=xyz(spread(30)), color=[(0,) + EMBER, (1,) + DEEP], alpha=[(0, 0.8), (1, 0)]),
    ]


# =========================================================================================================================
# THE LUCKY CLOVER (the drop family's pale white-blue, a hint of mint)
# =========================================================================================================================
def clover_trail():
    return [
        # a thin streak: half a second of the fall (up to ~3,500 u behind the charm at its fastest), a vertex every 48 u
        ribbon(el('laser_trail', 'streak', loop=(500, 0), life=(500, 0), run='world',
                  size=(22, [(0, 1), (0.35, 0.6), (1, 0.12)]),
                  color=[(0, 0.96, 1.0, 0.98), (0.5, 0.78, 1.0, 0.88), (1,) + DROP_WHITE],
                  alpha=[(0, 0.85), (0.4, 0.45), (1, 0)]), 48, 1600),
        el('incand', 'sparkles', loop=(22, 0), life=(380, 220), run='world', offset='sphere', off_r=(4, 10),
           size=(10, [(0, 1), (0.5, 0.6), (1, 0)], [(0, 0.8), (0.5, 0.5), (1, 0)]), vel=xyz(spread(35)),
           color=[(0, 0.9, 1.0, 0.94), (1,) + MINT], alpha=[(0, 1), (0.25, 0.45), (0.5, 0.9), (0.75, 0.35), (1, 0)]),
        el('orb', 'halo', loop=(90, 0), life=(180, 0), run='effect', size=(55, [(0, 0.96), (1, 1.04)]),
           color=DROP_WHITE, alpha=steady(0.5)),
    ]


def clover_land():
    return [
        near_fade(el('glow', 'flash', oneshot=(1, 0), life=(250, 0), org=(0, 0, 16), size=(120, [(0, 0.6), (0.3, 1), (1, 1.1)]),
                     color=DROP_WHITE, alpha=[(0, 0.75), (1, 0)]), 40, 80),
        # ~18 sparkles thrown up (120-320 u/s, WORLD up) and out (+-140), arcing gently back
        in_world(el('incand', 'sparkles', oneshot=(16, 4), life=(520, 300), run='world',
                    size=(9, [(0, 1), (0.5, 0.7), (1, 0)], [(0, 0.75), (0.5, 0.5), (1, 0)]),
                    color=[(0, 0.92, 1.0, 0.96), (1,) + MINT], alpha=[(0, 1), (0.3, 0.6), (0.55, 1), (0.8, 0.5), (1, 0)],
                    grav=(40, 20)),
                 X=spread(140, 0.5), Y=spread(140, 0.5), Z=(320, [(0, 0.375), (1, 0.2)], [(0, 1), (1, 0.55)])),
        el('ring', 'ring', oneshot=(1, 0), life=(420, 0), org=(0, 0, 16), size=(170, [(0, 0.12), (0.4, 0.75), (1, 1)]),
           color=(0.85, 1.0, 0.92), alpha=[(0, 0.85), (1, 0)]),
    ]


# =========================================================================================================================
# THE GOLDEN ZOMBIE (seen from 100-2,500 u)
# =========================================================================================================================
def golden_aura():
    return [
        # gold motes glittering in the air it moves through, drifting gently UP (17-48 u/s, world) - treasure, not fire
        in_world(el('incand', 'motes', loop=(45, 0), life=(900, 400), run='world', offset='sphere', off_r=(8, 18),
                    size=(8, [(0, 0.5), (0.15, 1), (0.6, 0.8), (1, 0.2)], [(0, 0.4), (0.15, 0.75), (0.6, 0.6), (1, 0.15)]),
                    color=[(0,) + TREASURE, (0.6, 1.0, 0.72, 0.26), (1, 0.9, 0.55, 0.18)],
                    alpha=[(0, 0), (0.1, 1), (0.3, 0.55), (0.5, 1), (0.7, 0.5), (1, 0)]),
                 X=spread(12), Y=spread(12), Z=(48, [(0, 0.35), (1, 0.6)], [(0, 0.75), (1, 1)])),
        el('orb', 'glow', loop=(110, 0), life=(220, 0), run='effect', size=(70, [(0, 0.96), (1, 1.04)]),    # 80/0.3, then 120/0.5 at
           color=(1.0, 0.8, 0.35), alpha=steady(0.2)),                                                       # 21:30: "way too intense" (user)
        el('incand', 'twinkles', loop=(70, 0), life=(140, 60), run='effect', offset='sphere', off_r=(6, 20),
           size=(5, [(0, 0.3), (0.35, 1.3), (1, 0)]), color=(1.0, 0.96, 0.75),
           alpha=[(0, 0), (0.2, 1), (0.4, 0.3), (0.6, 1), (1, 0)]),
        golden_light(),                                          # 21:50: the gold it throws on the floor and walls
    ]


# THE GOLDEN LIGHT (user: "It should have a golden glow"): a REAL dynamic light riding the aura host, so a golden zombie
# washes the dark floor and walls around it in gold. Copied from the map's proven perk-glow light (the donor's
# light_small, the same element tools/gen_tod_inducer_fx.py keeps); the hue is its colorGraph with the def's _color
# white - how every light in this map's effects is coloured (the staff glows, Wisp Tea). One light at a time: a new one
# every GOLDEN_LIGHT_EVERY ms living GOLDEN_LIGHT_LIFE ms, the two CROSSFADING through the 50 ms they overlap, so the
# glow is steady (the donor stacked five at once). No shadow map, every lighting state (it glows before the power too).
GOLDEN_LIGHT = (1.0, 0.76, 0.26)       # the light's gold (a touch deeper than TREASURE: it reads gold on grey stone)
GOLDEN_LIGHT_INTENSITY = 300           # THE KNOB if the pool is too bright / too dim in game (the donor perk glow: 512);
                                       # 700 on 2026-09-29 was "way too intense" in game (user, 2026-09-30)
GOLDEN_LIGHT_RADIUS = 140              # how far the gold reaches (u); the host rides the chest, ~50 u up (was 180)
GOLDEN_LIGHT_EVERY, GOLDEN_LIGHT_LIFE = 450, 500
LIGHT_RANGE = 3000                     # a light only needs to exist where someone can see what it lights


def golden_light():
    donor = E.load(S.GLOW_DONOR)
    e = [x for x in donor.elements if x.name == 'light_small'][0].copy()
    e.name = 'light'
    e.set('editorFlags', 'looping')                            # no random size / intensity / velocity: one steady gold
    e.set_flags('flags', remove=('spawnFrustumCull',))         # its glow on a wall in view counts even if it is not
    e.set('spawnRange', (0, LIGHT_RANGE))
    e.set('spawnLooping', (GOLDEN_LIGHT_EVERY, 0))
    e.set('lifeSpanMsec', (GOLDEN_LIGHT_LIFE, 0))
    e.set('spawnOrgZ', (0, 0))                                 # the donor lifted it 40 over a machine; this host IS the chest
    fade = (GOLDEN_LIGHT_LIFE - GOLDEN_LIGHT_EVERY) / GOLDEN_LIGHT_LIFE
    S.graph(e, 'lightIntensityGraph', GOLDEN_LIGHT_INTENSITY, [(0, 0), (fade, 1), (1 - fade, 1), (1, 0)])
    S.graph(e, 'lightRadiusGraph', GOLDEN_LIGHT_RADIUS, [(0, 1), (1, 1)])
    S.graph(e, 'colorGraph', 1.0, [(0,) + GOLDEN_LIGHT, (1,) + GOLDEN_LIGHT])
    S.graph(e, 'alphaGraph', 1.0, [(0, 1), (1, 1)])
    for it in e.items:                                          # the light def: white (the graph owns the hue), our reach
        if isinstance(it, E.Block) and it.key == 'dynamicLight2':
            body = []
            for line in it.body:
                key = line.strip().split(' ')[0]
                tabs = line[:len(line) - len(line.lstrip())]
                if key == '_color':
                    line = tabs + '_color 1 1 1'
                elif key == 'radius':
                    line = tabs + 'radius %d' % GOLDEN_LIGHT_RADIUS
                body.append(line)
            it.body = body
    e.lucky_template = 'light'
    return e


GLINT = [(0, 1), (0.12, 0.55), (0.24, 1), (0.36, 0.5), (0.48, 1), (0.6, 0.55), (0.75, 0.95), (1, 0)]   # a spinning coin


def golden_burst():
    return [
        near_fade(el('glow', 'flash', oneshot=(1, 0), life=(300, 0), size=(260, [(0, 0.6), (0.25, 1), (1, 1.1)]),
                     color=(1.0, 0.85, 0.45), alpha=[(0, 1), (0.35, 0.7), (1, 0)]), 40, 80),
        # ~34 coins: out +-320 u/s and up 150-450 u/s (world), under 100-115% gravity - apex at 0.2-0.6 s, falling by ~1 s
        in_world(el('incand', 'coins', oneshot=(30, 8), life=(850, 250), run='world',
                    size=(9, [(0, 1), (0.7, 0.85), (1, 0.4)], [(0, 0.8), (0.7, 0.7), (1, 0.3)]),
                    color=[(0, 1.0, 0.88, 0.42), (0.5,) + TREASURE, (1, 0.95, 0.62, 0.18)], alpha=GLINT,
                    spin=((0, 360), (-240, 480)), grav=(100, 15)),
                 X=spread(320, 0.8), Y=spread(320, 0.8), Z=(450, [(0, 0.333), (1, 0.3)], [(0, 1), (1, 0.9)])),
        el('ring', 'ring', oneshot=(1, 0), life=(380, 0), size=(190, [(0, 0.12), (0.4, 0.75), (1, 1)]),
           color=(1.0, 0.85, 0.45), alpha=[(0, 0.85), (1, 0)]),
        # a few green-gold sparkles floating up (no gravity: the luck leaving it)
        in_world(el('incand', 'sparkles', oneshot=(8, 3), life=(650, 250), run='world', offset='sphere', off_r=(4, 12),
                    size=(7, [(0, 0.4), (0.2, 1), (1, 0)]), color=[(0, 0.72, 1.0, 0.45), (1, 0.95, 0.9, 0.35)],
                    alpha=[(0, 1), (0.3, 0.5), (0.55, 1), (0.8, 0.45), (1, 0)]),
                 X=spread(90), Y=spread(90), Z=(140, [(0, 0.3), (1, 0.2)], [(0, 1), (1, 0.7)])),
    ]


# ---- the table: name, builder, bounding-box half size, the host's top speed (0 = played at rest) --------------------------
EFFECTS = [
    ('fx_luck_meteor_trail', meteor_trail, 3000, METEOR_SPEED),   # smoke 3.4 s x 550 u/s + a 510 u puff = ~2,400
    ('fx_luck_meteor_burst', meteor_burst, 2500, 0),              # fragments <= ~1,300 u out + their streaks; ring 2,400
    ('fx_luck_meteor_frag', meteor_frag, 1200, FRAG_PEAK),        # 0.55 s of embers behind a 1,600 u/s fragment = ~900
    ('fx_luck_clover_trail', clover_trail, 4500, CLOVER_PEAK),    # 0.6 s of sparkles behind a 7,000 u/s streak = ~4,200
    ('fx_luck_clover_land', clover_land, 300, 0),                 # sparkles rise ~110 u, spread ~130 u
    ('fx_luck_golden_aura', golden_aura, 500, ZOMBIE_SPRINT),     # 1.3 s of motes behind a 300 u/s sprint = ~400
    ('fx_luck_golden_burst', golden_burst, 600, 0),               # coins ~350 u out, ~130 u up, falling ~300 u
]
NAMES = [row[0] for row in EFFECTS]


def build():
    """-> ({name: efx text}, {name: ([(element, template, type)], bounds half, host speed)})"""
    out, meta = {}, {}
    for name, fn, half, speed in EFFECTS:
        els = fn()
        out[name] = S.effect(els, *box(half))
        meta[name] = ([(e.name, e.lucky_template, e.visual[0]) for e in els], half, speed)
    return out, meta


def world_reach(fx, speed):
    """How far back a moving host leaves its world-space particles: top speed x the longest such life + their size."""
    reach = 0.0
    for e in fx.elements:
        if 'runRelToWorld' in e.flags('flags'):
            g = e.graph('sizeGraph0')
            size = g.scale * max(row[1] for c in g.curves for row in c)
            reach = max(reach, speed * sum(e.nums('lifeSpanMsec')) / 1000.0 + size)
    return reach


def box_problems(fx_texts, meta):
    """Every moving effect's box must hold the particles it leaves behind (or the engine culls a visible trail)."""
    bad = []
    for n in NAMES:
        _, half, speed = meta[n]
        if speed:
            reach = world_reach(E.parse(fx_texts[n]), speed)
            if reach > half:
                bad.append('%s: its box +-%d is shorter than the %d u its world-space particles trail behind a %d u/s host'
                           % (n, half, reach, speed))
    return bad


# ---- validation ----------------------------------------------------------------------------------------------------------
VISUAL = ('billboardSprite', 'orientedSprite', 'rotatedSprite', 'line', 'tail', 'trail', 'cloud', 'lensFlare')
LIGHTS = ('dynamicLight2',)            # a dynamic light: its own rules below (near range, no shadow map, one at a time)
LIGHT_RADIUS_MAX = 400
CHILD_KEYS = ('attachment', 'fxOnDeath', 'fxOnImpact', 'emission')


def _whole(vals):
    return all(abs(v - round(v)) < 1e-9 for v in vals)


def peak_particles(e):
    """The most particles this element can have alive at once (looping: ceil(max life / interval) x max per spawn)."""
    life = sum(e.nums('lifeSpanMsec'))
    if 'looping' in e.flags('editorFlags'):
        interval = max(1.0, e.nums('spawnLooping')[0])
        per = sum(e.nums('spawnLoopingSpawnCount'))
        return int(math.ceil(life / interval) * max(1, per))
    return int(sum(e.nums('spawnOneShot')))


def validate(name, text, names):
    """-> the problems in one generated effect (the jump title's validate() checks, plus the lucky set's own)."""
    bad = []
    path = PREFIX + name
    if len(path) > MAX_PATH:
        bad.append('%s: effect path %d chars (> %d: cut at runtime)' % (path, len(path), MAX_PATH))
    if 'gfx_debug_missing_fx' in text:
        bad.append(name + ': a stub element (gfx_debug_missing_fx)')
    try:
        fx = E.parse(text)
    except Exception as ex:
        return bad + ['%s: does not parse (%s)' % (name, ex)]
    head = '\n'.join(fx.header)
    lo = hi = None
    for ln in fx.header:
        if ln.startswith('\tefBoundingBoxMin '):
            lo = [float(v) for v in ln.rstrip(';').split()[1:4]]
        elif ln.startswith('\tefBoundingBoxMax '):
            hi = [float(v) for v in ln.rstrip(';').split()[1:4]]
    if 'efUseBoundingBox' not in head or lo is None or hi is None:
        bad.append(name + ': no bounding box (a sky-scale effect is culled without one)')
    elif not all(a < b for a, b in zip(lo, hi)):
        bad.append(name + ': an empty bounding box %s %s' % (lo, hi))
    if not fx.elements:
        bad.append(name + ': no elements')
    seen, total = set(), 0
    for e in fx.elements:
        en = name + '/' + e.name
        if e.name in seen:
            bad.append(en + ': a second element with this name')
        seen.add(e.name)
        t, mats = e.visual
        if t == 'model':
            bad.append(en + ': a model element (its assets are not zoned)')
        elif t == 'runner':
            if not mats or any(m not in [PREFIX + n for n in names] for m in mats):
                bad.append(en + ': a runner element naming an effect not generated here %s' % mats)
        elif t in LIGHTS:
            body = ' '.join(m.strip() for m in mats)
            if 'shadowUpdate Never' not in body or 'PRIMARY_NOSHADOWMAP 1' not in body:
                bad.append(en + ': a light that casts shadows (the cost of one per frame at a moving zombie)')
            if not all(('lightingstate%d 1' % k) in body for k in (1, 2, 3, 4)):
                bad.append(en + ': a light missing from a lighting state (it would go dark before / after the power)')
            ig, rg = e.graph('lightIntensityGraph'), e.graph('lightRadiusGraph')
            peak_i = ig.scale * max(row[1] for c in ig.curves for row in c)
            peak_r = rg.scale * max(row[1] for c in rg.curves for row in c)
            if not (0 < peak_i and 0 < peak_r <= LIGHT_RADIUS_MAX):
                bad.append('%s: light intensity %s / radius %s (radius must be 1..%d)' % (en, peak_i, peak_r, LIGHT_RADIUS_MAX))
            if peak_particles(e) > 2:
                bad.append('%s: %d lights alive at once (one, crossfading into the next)' % (en, peak_particles(e)))
        elif t not in VISUAL or not mats:
            bad.append(en + ': draws nothing')
        edf, fl = e.flags('editorFlags'), e.flags('flags')
        children = {}
        for key in CHILD_KEYS:
            if e.has(key):
                v = e.get(key).strip().strip('"')
                if v:
                    children[key] = v
        for key, v in children.items():
            if len(v) > MAX_PATH:
                bad.append('%s: %s %s is %d chars (> %d)' % (en, key, v, len(v), MAX_PATH))
            if not v.startswith(PREFIX) or v[len(PREFIX):] not in names:
                bad.append('%s: %s %s is not one of the generated effects' % (en, key, v))
        if 'playAttached' in edf and 'attachment' not in children:
            bad.append(en + ': a runner (playAttached) without an attachment child')
        if 'attachment' in children and 'playAttached' not in edf:
            bad.append(en + ': an attachment child without playAttached')
        for key in ('lifeSpanMsec', 'spawnDelayMsec', 'spawnLooping'):
            if not _whole(e.nums(key)):
                bad.append(en + ': fractional ' + key)
        if 'looping' in edf:
            interval, count = e.nums('spawnLooping')
            if interval < 1 or count != 0:
                bad.append('%s: looping every %s ms for %s loops (the second number is a COUNT: 0 = forever)' % (en, interval, count))
        for key in ('elemSpawnSound', 'elemFollowSound'):
            if e.has(key) and any(line.strip() for line in e.get(key).body):
                bad.append(en + ': still names a sound (' + key + ')')
        if t in LIGHTS:
            if e.nums('spawnRange')[1] < LIGHT_RANGE:
                bad.append(en + ': a light spawn range under %d (it would go out while you can still see its glow)' % LIGHT_RANGE)
        elif e.nums('spawnRange')[1] < FAR:
            bad.append(en + ': spawn range under %d (it would vanish at sky distance)' % FAR)
        if any(e.nums('fadeInRange')):
            bad.append(en + ': a far fade-in range (it would vanish at distance)')
        if 'spawnFrustumCull' in fl:
            bad.append(en + ': frustum-culled at spawn')
        if 'useCollision' in fl:
            bad.append(en + ': collides (these effects never trace)')
        if 'isMatureContent' in fl:
            bad.append(en + ': mature-content only')
        if e.has('extraFlags') and any(f in e.flags('extraFlags') for f in ('overwaterOnly', 'underwaterOnly')):
            bad.append(en + ': draws only over / under water')
        for it in e.items:
            if isinstance(it, E.Graph):
                if not math.isfinite(it.scale) or any(not math.isfinite(v) for c in it.curves for row in c for v in row):
                    bad.append('%s: %s is not finite' % (en, it.key))
                if it.key == 'alphaGraph' and any(not (0 <= row[1] * it.scale <= 1) for c in it.curves for row in c):
                    bad.append(en + ': alpha outside 0..1')
                if it.key in ('sizeGraph0', 'sizeGraph1') and any(row[1] * it.scale < 0 for c in it.curves for row in c):
                    bad.append('%s: negative %s' % (en, it.key))
        total += peak_particles(e)
    if total > PARTICLE_BUDGET:
        bad.append('%s: ~%d live particles at peak (budget %d)' % (name, total, PARTICLE_BUDGET))
    return bad


# ---- main ----------------------------------------------------------------------------------------------------------------
def summary(fx, meta):
    lines = []
    for n in NAMES:
        els, half, _ = meta[n]
        parsed = E.parse(fx[n])
        kind = 'looping' if any('looping' in e.flags('editorFlags') for e in parsed.elements) else 'one-shot'
        peak = sum(peak_particles(e) for e in parsed.elements)
        parts = ' '.join('%s=%s(%s)' % (en, tk, t) for en, tk, t in els)
        lines.append('  %-21s %-8s %d elements, box +-%d, peak ~%d particles: %s' % (n, kind, len(els), half, peak, parts))
    return lines


def main(argv):
    fx, meta = build()
    names = set(fx)
    assert list(fx) == NAMES and len(names) == 7, sorted(fx)
    problems = [p for n in NAMES for p in validate(n, fx[n], names)] + box_problems(fx, meta)
    if problems:
        print('LUCKY FX INVALID:\n  ' + '\n  '.join(problems))
        return 1
    if '--check' in argv:
        bad = []
        for n in NAMES:
            p = OUT / (n + '.efx')
            if not p.exists():
                bad.append(n + ' missing')
            elif p.read_bytes() != fx[n].encode('utf-8'):
                bad.append(n + ' differs')
        if OUT.exists():
            bad += ['stray ' + p.name for p in sorted(OUT.glob('*.efx')) if p.stem not in names]
        if bad:
            print('LUCKY FX STALE: ' + ', '.join(bad) + ' - run python tools/lucky/make_fx.py')
            return 1
        print('LUCKY FX OK: %d effects' % len(fx))
        return 0
    out_dir = pathlib.Path(argv[argv.index('--out') + 1]) if '--out' in argv else OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in sorted(out_dir.glob('fx_luck_*.efx')):       # retire whole: an effect this generator no longer makes
        if old.stem not in names:
            old.unlink()
            print('LUCKY FX RETIRED', old.name)
    for other in sorted(out_dir.glob('*.efx')):
        if other.stem not in names:
            print('LUCKY FX WARNING: %s is not generated here (--check will call it a stray)' % other.name)
    for n in NAMES:
        (out_dir / (n + '.efx')).write_bytes(fx[n].encode('utf-8'))
    print('\n'.join(summary(fx, meta)))
    print('LUCKY FX WRITTEN: %d effects -> %s' % (len(fx), out_dir))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
