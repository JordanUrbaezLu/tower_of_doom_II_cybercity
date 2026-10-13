"""THE HAVEN effects (docs/202), GENERATED - never hand-edit the .efx.

  python -B tools/haven/make_fx.py            write share/raw/fx/tod/haven/fx_tod_haven_*.efx
  python -B tools/haven/make_fx.py --check    regenerate in memory, validate, FAIL if a written effect differs

THE FOURTEEN EFFECTS (effect path = tod/haven/<name>; _tod_haven.gsc names the first thirteen, _tod_atmosphere the
motes). TWO STATES (docs/202 v3, user
2026-10-03: "the dome should be evil at first ... You must kill them and then the area turns into a safe zone ...
two distinct states"): the CORRUPTED set plays while the haven's guardians live, the SAFE set once they are dead.
  fx_tod_haven_ambient  SAFE, LOOPING on a tag_origin carrier at the dome centre (angles 0: local X/Y/Z = world x/y/z):
                        the emitter gems on the pylon collars glowing and sparking, glints twinkling across the
                        field, slow energy motes rising inside, and the ceiling PROJECTOR over the teleporter
                        glowing and shedding motes down into the field (docs/202 v2, THE HEART: the field stands
                        in the tower's opened core, so there is no platform underside to light).
  fx_tod_haven_corrupt  CORRUPTED, LOOPING at the dome centre: the same anchors gone bad - the gems smoulder red,
                        dark embers drift up through the field, a sooty haze crawls over its floor, red arcs crawl
                        the lattice, the projector drips red, and a dark heart glows at the centre. The evil state
                        has NO field feedback of its own (no ripple, no slow, no tint): this loop IS its presence.
  fx_tod_haven_cross    SAFE, ONE-SHOT where a PLAYER crosses the field, on ANY side (the carrier sits ON the field
                        sphere and faces OUT along its normal): THE ROUNDED RIPPLE - a small flash where they cross,
                        then rings of light running outward OVER THE DOME'S CURVE (each ring a circle on the sphere),
                        sparks streaking along the surface and a crackle. Everything near the crosser's camera fades
                        out, so the player who crosses never gets a flash in the face (the screen effect is theirs).
  fx_tod_haven_push     SAFE, ONE-SHOT where a ZOMBIE pushes through: the same rounded ripple in the field's hostile
                        red, tighter, with sparks thrown off the field and a crackle of cyan arcs.
  fx_tod_haven_boot     ONE-SHOT when the haven powers up with the tower (it boots CORRUPTED): a flash on the heart,
                        light racing up the field, bursts at the emitter gems, sparkles shed over the dome.
  fx_tod_haven_wake     CORRUPTED, ONE-SHOT when the guardians rise (a player came near): a red shock ring over the
                        floor, a dark flash, embers blown out of the heart, every gem flaring red.
  fx_tod_haven_guard_down CORRUPTED, ONE-SHOT when a guardian dies: a crimson crack across the dome - a red flash at
                        the heart, arcs snapping over the field, sparks thrown.
  fx_tod_haven_cleanse  THE TRANSITION, ONE-SHOT when the last guardian falls: a white-cyan purge - a big flash at the
                        heart, a cyan shock ring, light racing up to the crown, sparkles washing over the whole dome,
                        the gems flashing cyan and a column of light up to the projector.
  fx_tod_haven_slowed   SAFE, LOOPING on a small carrier linked to an ENEMY inside the field (_tod_haven's slow
                        carriers, chest height): thin cyan arcs crawling round the body and frost sparks sifting
                        off it - the 33% slow made visible on the one it slows (user 2026-10-03, tweak #1).
  fx_tod_haven_deflect  CORRUPTED, ONE-SHOT where a bullet stops on the barrier (docs/202 v4, user 2026-10-03:
                        "bullets cannot go in or outside the dome. Until its a safe zone"): a small crimson ripple
                        ON the field (the rounded rule, local X = the outward normal), a hot point and sparks
                        thrown back - the wall answering the shot.
  fx_tod_haven_fury     CORRUPTED, LOOPING at the dome centre WHILE THE GUARDIANS LIVE (v5; the wake swaps it in for the
                        corrupt loop): the frenzy - the gems blaze, every glint site crawls with arcs, embers pour up, the
                        heart throbs fast and bright, a vortex of soot turns round it, and its red light pulses with it.
  fx_tod_haven_convulse THE PURIFICATION's first beat (v5), ONE-SHOT at the dome centre for the convulsion: an ACCELERATING
                        STROBE on the heart (one flash per step of _tod_haven.gsc's purge_strobe_steps(); the dome's own
                        skin strobe and the sound's clicks ride the same list), arcs snapping over the whole sphere in two
                        thickening waves, lightning cracks late, embers blown out of the heart, the heart swelling toward
                        the collapse, a soot vortex drawn into it, every gem flaring.
  fx_tod_haven_collapse ITS SECOND BEAT, ONE-SHOT: the field IMPLODES - beads on the whole sphere rush INWARD along their
                        own normals and turn white as they converge, a white-hot flash + a real light flash at the heart,
                        a shock ring, a column up to the projector, white sparks thrown up, the last soot blown out along
                        the floor. The script hides the dome for the void; the bloom (fx_tod_haven_cleanse) follows.
  fx_tod_haven_motes    THE FOURTEENTH (PK43, 2026-10-05), LOOPING at a fixed point (_tod_atmosphere::lounge_fx's server
                        PlayFX, level._effect[ "tod_lounge_motes" ]): the four haven thresholds (haven_motes_org, 260 over
                        the floor) and the departure hall's oculus (tower_transit_layout.js FX, 430 over its floor). A soft
                        column of LIT dust motes drifting down - stock's own lit mote (dirt/fx_dust_motes_200x200, vendored
                        in fx_donors/), so they take whatever light falls on them (the district colour, the haven's heart,
                        the power) and glow with no light of their own. It replaces env/light/fx_light_god_rays_dust_motes,
                        which the map zoned and which is Treyarch's gfx_debug_missing_fx PLACEHOLDER in the tools root
                        (zoning it packed the stub over the real effect: the shaft never drew). Spheres stacked down a
                        vertical span + world velocities only, so it reads the same however the point effect is turned.

v5 THE LIGHTS (user 2026-10-04: "the two states of the dome to be quite different"): the corrupt / fury / ambient loops
carry a REAL dynamic light at the heart (heart_light(): the golden zombie's recipe, tools/lucky/make_fx.py golden_light() -
the stock perk glow's light_small, white in its def with the hue on colorGraph, shadowless, in every lighting state, two
crossfading so the throb curve IS what you see) - a slow red throb dormant, a fast one in the fight, a steady cyan once
safe; the collapse adds a one-shot white flash of it. CORRUPT_LIGHT / FURY_LIGHT / SAFE_LIGHT are the knobs. THE
PURIFICATION's clock is the module's: CONVULSE_MS and the strobe schedule are READ out of _tod_haven.gsc (make_sounds.py
reads the same), so the effects, the sounds and the dome's own strobe agree to the millisecond.

v4 THE WHOLE HALL: the field is a low dome as wide as the hall (its sphere's centre BELOW the floor), so the glints
sit on rings of HEIGHT above the floor (never under it), the volumes inside it are scaled to it, the emitter gems
are the three corner posts' collars, and the big one-shots grow with the dome.

THE BUILDER IS THE SKY FLEET'S, through the lucky set's helpers and its validate() (imported READ-ONLY; the same
engine rules hold: effects cannot scale, gravity is % of world gravity, fadeOutRange is the NEAR-camera fade, a
looping count of 0 = forever, the 63-character path rule).

THE ROUNDED RULE (user 2026-10-03, docs/202 v2): the field is a sphere and is crossed from any side, so the crossing
feedback lies ON it. Every sprite template here is a camera-facing billboard: one big sprite reads as a flat plate
hung on a ball (the first cut's 110-190 unit flash / ring / ripple stood 13-21 units off the curve at their rims).
So the ripple is built from SMALL sprites placed on the sphere: a circle on a sphere is flat, so one ring is one
cylinder spawn around the carrier's X axis (spawnOffsetCylindricalAxis 0 = the outward normal, the stock dust
impact rings' setting) in the plane x = -SR (1 - cos a), radius SR sin a. field_shape_problems() gates it: no sprite
in the crossing effects wider than FLAT_MAX, every ring on the sphere, and a negative control so the gate cannot go
quietly dead.
"""
import hashlib
import importlib.util
import json
import math
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[2]
LUCKY = ROOT / 'tools/lucky/make_fx.py'
OUT = ROOT / 'share/raw/fx/tod/haven'
PREFIX = 'tod/haven/'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = load(LUCKY, 'lucky_fx_lib')          # the lucky set's helpers + validate(); it loads the sky builder itself
S, E = L.S, L.E
spread, xyz, in_world, near_fade, steady, box = L.spread, L.xyz, L.in_world, L.near_fade, L.steady, L.box

# PK43: THE MOTES' DONOR - stock dirt/fx_dust_motes_200x200 (its one element: the lit mote gfx_dust_mote_01_lit), copied
# verbatim from the private tools root with LF line endings (the repo's eol=lf); its sha is pinned so a hand edit fails.
MOTE_DONOR = ROOT / 'tools/haven/fx_donors/dirt__fx_dust_motes_200x200.efx'
MOTE_DONOR_SHA = '289c712d7bbaf70fa954be453ffb663eed3c84733376eeaba60a4cdd3dae6e3e'   # sha256 of the LF text
S.TPL['mote'] = (str(MOTE_DONOR), 0)       # the sky builder's template(): DON / <an absolute path> is that path
S.EXPECT['mote'] = ('billboardSprite', 'gfx_dust_mote_01_lit')


def el(tkey, name, **kw):
    """The lucky set's el(), plus two cleanups some sky-fleet templates need here: no water-only draw flags (the
    ripple / spark donors carry one) and no element sounds (the arc donor names one) - the scripts own every sound."""
    e = L.el(tkey, name, **kw)
    if e.has('extraFlags'):
        e.set_flags('extraFlags', remove=('overwaterOnly', 'underwaterOnly'))
    for key in ('elemSpawnSound', 'elemFollowSound'):
        if e.has(key):
            e.get(key).body = []
    return e

H = json.loads(subprocess.check_output(
    ['node', '-e', "const H=require('./tools/haven_layout.js');console.log(JSON.stringify({R:H.DOME_R,C:H.DOME_C,S:H.DOME_S,"
     "TOP:H.DOME_TOP,CX:H.C,VOID:H.VOID_H,FINS:H.FINS.map(f=>({tag:f.tag,g:[f.gem[0]-H.C[0]-f.d[0]*8,f.gem[1]-H.C[1]-f.d[1]*8,f.gem[2]]}))}))"],
    cwd=ROOT, text=True))
R, CZ, SR, TOP = H['R'], H['C'], H['S'], H['TOP']
VOID = H['VOID']                        # the hall's ceiling above the floor (the projector hangs from it)
PROJ_TIP = VOID - 64                    # the projector pyramid's tip (tools/haven_layout.js geometry)

# v5 THE PURIFICATION's clock is the module's (LOCKSTEP by construction with make_sounds.py and the dome's own strobe):
# the convulsion's length and its strobe schedule are read out of _tod_haven.gsc (the staged copy before the wire step)
GSC = next(p for p in (ROOT / 'scripts/zm/zm_tod2_cybercity/_tod_haven.gsc', ROOT / 'art/haven/staged/_tod_haven.gsc') if p.exists()).read_text(encoding='utf-8')


def gsc_define(name):
    return float(re.search(r'#define\s+%s\s+(-?[\d.]+)' % name, GSC).group(1))


CONVULSE_MS = int(round(gsc_define('TOD_HAVEN_PURGE_CONVULSE_SECS') * 1000))
STROBE_MS = [int(v) for v in re.search(r'function purge_strobe_steps\(\)\s*\{\s*return array\(([^)]*)\);', GSC).group(1).split(',')]
assert STROBE_MS == sorted(STROBE_MS) and STROBE_MS[-1] < CONVULSE_MS, 'the strobe schedule must climb and end inside the convulsion'

# ---- colour (linear RGB) -------------------------------------------------------------------------------------------------
FIELD = (0.35, 0.92, 1.0)              # the field's cyan
FIELD_HOT = (0.86, 1.0, 1.0)           # its white-hot lattice line
GEM = (0.30, 0.78, 1.0)
HOSTILE = (1.0, 0.42, 0.22)            # the field fighting a zombie
EMBER = (1.0, 0.68, 0.32)
# THE CORRUPTED STATE (docs/202 v3): the same field, evil - crimson lattice, blood-red gems, sooty haze
DARK = (0.62, 0.05, 0.06)              # the corrupted field's deep red
DARK_HOT = (1.0, 0.22, 0.12)           # its hot lattice / the gems gone red
DARK_EMBER = (1.0, 0.45, 0.16)         # embers rising through it
SOOT = (0.30, 0.04, 0.03)              # the haze over its floor
# THE PURIFICATION (docs/202 v5): the corruption burns out white, then the field's cyan
PURGE_HOT = (1.0, 0.96, 0.88)          # white-hot
PURGE = (0.60, 0.96, 1.0)              # the bloom's pale cyan
# THE LIGHTS (v5): a real dynamic light at the heart, per state (heart_light below)
LIGHT_RANGE = L.LIGHT_RANGE            # a light exists where someone can see what it lights (the lucky set's rule)
DARK_LIGHT = (1.0, 0.16, 0.08)         # the corrupted heart's red (deeper than DARK_HOT: it reads red on grey stone)
FIELD_LIGHT = (0.30, 0.80, 1.0)        # the safe heart's cyan
PURGE_LIGHT = (0.85, 0.97, 1.0)        # the collapse's flash
# the knobs: radius (the validator caps it at 400) and intensity (the donor perk glow: 512; the golden zombie's 300 at
# 140 u read too intense ON A BODY - these sit at a dome's heart, 300 u from its rim); the throb curve is one life, two
# lights crossfading through (life - every) at each end, so the curve's end knots carry the trough
CORRUPT_LIGHT = dict(radius=300, intensity=360, every=2600, life=2700, curve=[(0, 0), (0.037, 0.35), (0.5, 1.0), (0.963, 0.35), (1, 0)])
FURY_LIGHT = dict(radius=320, intensity=440, every=1100, life=1200, curve=[(0, 0), (0.083, 0.4), (0.5, 1.0), (0.917, 0.4), (1, 0)])
SAFE_LIGHT = dict(radius=300, intensity=220, every=450, life=500)


def r3(v):
    return round(v, 3)


def heart_light(name, color, radius, intensity, every=450, life=500, curve=None, org_z=60, oneshot=False, delay=0):
    """A REAL dynamic light at the heart (the golden zombie's recipe, tools/lucky/make_fx.py golden_light(): the stock
    perk glow's light_small, white in its def with the hue on colorGraph, shadowless, in every lighting state). Looping:
    one light every `every` ms living `life` ms, two crossfading through their overlap (the ramps sum flat, so `curve`
    [(t, fraction)] over one life IS the throb you see). One-shot: a flash of `life` ms after `delay`."""
    donor = E.load(S.GLOW_DONOR)
    e = [x for x in donor.elements if x.name == 'light_small'][0].copy()
    e.name = name
    e.set_flags('flags', remove=('spawnFrustumCull',))        # its glow on a wall in view counts even if the heart is not
    e.set('spawnRange', (0, LIGHT_RANGE))
    e.set('spawnOrgZ', (org_z, 0))                             # the donor lifted it 40 over a machine; the heart sits here
    e.set('spawnDelayMsec', (delay, 0))
    e.set('lifeSpanMsec', (life, 0))
    if oneshot:
        e.set_flags('editorFlags', remove=('looping',))
        e.set('spawnLooping', (1, 0))
        e.set('spawnOneShot', (1, 0))
        if curve is None:
            curve = [(0, 0), (0.12, 1), (0.55, 0.65), (1, 0)]
    else:
        e.set('editorFlags', 'looping')                        # no random size / intensity / velocity: one steady light
        e.set('spawnLooping', (every, 0))
        if curve is None:
            fade = (life - every) / life
            curve = [(0, 0), (fade, 1), (1 - fade, 1), (1, 0)]
    S.graph(e, 'lightIntensityGraph', intensity, curve)
    S.graph(e, 'lightRadiusGraph', radius, [(0, 1), (1, 1)])
    S.graph(e, 'colorGraph', 1.0, [(0,) + tuple(color), (1,) + tuple(color)])
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
                    line = tabs + 'radius %d' % radius
                body.append(line)
            it.body = body
    return e


def field_point(theta, phi):
    """A point ON the field sphere (theta = azimuth, phi = elevation above the sphere centre), local to the floor centre."""
    x = SR * math.cos(phi) * math.cos(theta)
    y = SR * math.cos(phi) * math.sin(theta)
    z = CZ + SR * math.sin(phi)
    return (r3(x), r3(y), r3(z))


def elev(z):
    """the field sphere's elevation (from its centre) at height z above the floor"""
    return math.asin(max(-1.0, min(1.0, (z - CZ) / SR)))


# 19 glint sites spread over the field (deterministic): three rings at heights above the floor + the crown
GLINTS = [field_point(math.radians(a), elev(z)) for z, n, a0 in ((40, 8, 15), (140, 6, 52), (230, 4, 100)) for a in [a0 + i * 360 / n for i in range(n)]]
GLINTS.append((0.0, 0.0, r3(TOP - 4)))
SCALE = R / 220.0                      # v4: the field is this much wider than v3's (the volumes inside it follow)


# =========================================================================================================================
# THE AMBIENT FIELD (looping, the dome centre)
# =========================================================================================================================
def ambient():
    els = []
    for f in H['FINS']:
        g = tuple(r3(v) for v in f['g'])
        els.append(el('orb', 'gem_' + f['tag'], loop=(120, 0), life=(240, 0), run='effect', org=g,
                      size=(44, [(0, 0.95), (1, 1.05)]), color=GEM, alpha=steady(0.55)))
        els.append(el('incand', 'gem_spark_' + f['tag'], loop=(650, 0), life=(420, 200), run='effect', org=g, offset='sphere',
                      off_r=(6, 10), size=(6, [(0, 0.3), (0.3, 1.2), (1, 0)]), color=FIELD_HOT,
                      alpha=[(0, 0), (0.2, 1), (0.5, 0.4), (0.7, 0.9), (1, 0)]))
    for i, p in enumerate(GLINTS):
        els.append(el('incand', 'glint_%02d' % i, loop=(1100 + 70 * (i % 7), 0), life=(260, 140), run='effect', org=p,
                      offset='sphere', off_r=(0, 26), size=(7, [(0, 0.2), (0.35, 1.3), (1, 0)]), color=FIELD_HOT,
                      alpha=[(0, 0), (0.25, 1), (0.5, 0.35), (0.75, 0.8), (1, 0)]))
    els += [
        # energy motes rising slowly inside the field, kept above the deck (z 10..230) and off the rim
        in_world(el('incand', 'motes', loop=(110, 0), life=(3000, 900), run='world', org=(0, 0, 110), offset='sphere',
                    off_r=(20, 180), size=(5, [(0, 0.4), (0.2, 1), (0.8, 0.9), (1, 0.2)]), color=FIELD,
                    alpha=[(0, 0), (0.15, 0.7), (0.6, 0.45), (1, 0)]),
                 X=spread(6), Y=spread(6), Z=(26, [(0, 0.45), (1, 0.7)], [(0, 0.8), (1, 1)])),
        # the PROJECTOR on the ceiling over the teleporter: its tip glows and sheds motes that drift down
        # into the field's crown (seen from the hall, the loggia and the galleries)
        el('orb', 'projector', loop=(150, 0), life=(300, 0), run='effect', org=(0, 0, r3(PROJ_TIP - 6)),
           size=(70, [(0, 0.96), (1, 1.04)]), color=GEM, alpha=steady(0.55)),
        in_world(el('incand', 'projector_motes', loop=(160, 0), life=(2600, 700), run='world', org=(0, 0, r3(PROJ_TIP - 14)),
                    offset='sphere', off_r=(4, 24), size=(5, [(0, 1), (0.7, 0.8), (1, 0.2)]), color=FIELD,
                    alpha=[(0, 0.8), (0.7, 0.5), (1, 0)]),
                 X=spread(8), Y=spread(8), Z=(110, [(0, -0.5), (1, -0.7)], [(0, -1), (1, -1)])),
        # v5: the heart's steady cyan light on the floor and the machines round it
        heart_light('heart_light', FIELD_LIGHT, **SAFE_LIGHT),
    ]
    return els


# =========================================================================================================================
# THE ROUNDED RIPPLE - the crossing feedback lies ON the field sphere (see THE ROUNDED RULE above)
# =========================================================================================================================
FLAT_MAX = 48                          # the widest single sprite a crossing effect may carry (<= ~5 u off the curve even
                                       # if a size is a half-width); the rounded shape is carried by placement, not size


def ring_on_field(a_deg):
    """The circle on the field sphere at angular radius a around the crossing point, in the carrier's frame (local X =
    the outward normal, the carrier ON the sphere, so the sphere's centre is local (-SR, 0, 0)): (its plane's x, its radius)."""
    a = math.radians(a_deg)
    return r3(-SR * (1 - math.cos(a))), r3(SR * math.sin(a))


def ripple(prefix, rings, hot, cool, fade=(24, 48)):
    """One element per ring: `count` soft beads spawned around the normal ON the sphere, firing `delay` ms after the
    crossing - successive rings read as one wave running outward over the dome's curve."""
    els = []
    for i, (a_deg, count, delay, size, peak) in enumerate(rings):
        x, rad = ring_on_field(a_deg)
        e = el('glow', '%s_ring_%d' % (prefix, i + 1), oneshot=(count, 0), life=(230, 40), delay=(delay, 20), org=(x, 0, 0),
               offset='cylinder', off_r=(rad, 0), size=(size, [(0, 0.6), (0.25, 1), (1, 0.75)]),
               color=[(0,) + hot, (1,) + cool], alpha=[(0, 0), (0.15, peak), (0.55, r3(0.55 * peak)), (1, 0)])
        e.set('spawnOffsetCylindricalAxis', 0)
        els.append(near_fade(e, *fade))
    return els


def along_field(e):
    """Velocity in the spawn OFFSET's frame (the stock dust impact rings' runRelToOffset): X = outward from the normal,
    so a particle spawned round the crossing point runs out along the field, not off it."""
    e.set_flags('flags', add=('runRelToOffset',), remove=('runRelToEffect', 'runRelToWorld', 'runRelToSpawn'))
    e.set('spawnOffsetCylindricalAxis', 0)
    return e


# =========================================================================================================================
# A PLAYER CROSSES (one-shot, any side of the field; local X = the outward normal at the crossing point)
# =========================================================================================================================
CROSS_RINGS = [                        # (angle deg, beads, delay ms, bead size, peak alpha): 16 / 36 / 59 / 86 / 115 u out
    (4, 10, 0, 16, 0.95),
    (9, 18, 45, 20, 0.85),
    (15, 28, 95, 24, 0.72),
    (22, 44, 150, 28, 0.56),
    (30, 56, 210, 32, 0.4),
]


def cross():
    return ripple('ripple', CROSS_RINGS, FIELD_HOT, FIELD) + [
        # where they crossed: a small hot point, a soft flash and a short shimmer in the field
        near_fade(el('incand', 'core', oneshot=(1, 0), life=(160, 0), size=(18, [(0, 0.6), (0.3, 1), (1, 0.4)]),
                     color=FIELD_HOT, alpha=[(0, 1), (1, 0)]), 24, 40),
        near_fade(el('glow', 'flash', oneshot=(1, 0), life=(200, 0), size=(44, [(0, 0.6), (0.3, 1), (1, 1.05)]),
                     color=FIELD_HOT, alpha=[(0, 0.7), (1, 0)]), 36, 60),
        near_fade(el('ripple', 'shimmer', oneshot=(1, 0), life=(320, 0), size=(48, [(0, 0.3), (1, 1)]),
                     color=(1, 1, 1), alpha=[(0, 0.6), (1, 0)]), 36, 60),
        # sparks streaking out ALONG the field from the crossing point (~40 u of travel: under 4 u off the curve)
        near_fade(along_field(el('spark', 'streaks', oneshot=(16, 0), life=(180, 60), offset='cylinder', off_r=(4, 6),
                                 size=(2.2, [(0, 1), (1, 0.6)]), size1=(18, [(0, 1), (1, 0.3)]),
                                 vel={'X': (300, [(0, 1.0), (1, 0.35)])},
                                 color=[(0,) + FIELD_HOT, (1,) + FIELD], alpha=[(0, 1), (0.5, 0.7), (1, 0)])), 24, 40),
        # a brief crackle in the field round the point
        near_fade(el('arc', 'crackle', oneshot=(3, 0), life=(110, 60), delay=(0, 90), org=(-1, 0, 0), offset='cylinder',
                     off_r=(18, 22), size=(26, [(0, 0.7), (1, 1)]), color=FIELD, alpha=[(0, 0.85), (0.5, 0.5), (1, 0)]), 24, 40),
    ]


# =========================================================================================================================
# A ZOMBIE PUSHES THROUGH (one-shot; local X = the outward normal): the field fights it
# =========================================================================================================================
PUSH_RINGS = [                         # tighter and hostile: 16 / 40 / 67 u out
    (4, 8, 0, 14, 0.9),
    (10, 18, 50, 18, 0.75),
    (17, 28, 105, 22, 0.55),
]


def push():
    return ripple('ripple', PUSH_RINGS, (1.0, 0.9, 0.6), HOSTILE) + [
        near_fade(el('glow', 'flash', oneshot=(1, 0), life=(170, 0), size=(40, [(0, 0.6), (0.3, 1), (1, 1.05)]),
                     color=HOSTILE, alpha=[(0, 0.7), (1, 0)]), 30, 60),
        # sparks THROWN OFF the field (they leave it on purpose, and fall)
        el('spark', 'sparks', oneshot=(10, 4), life=(320, 160), run='spawn', size=(12, [(0, 1), (1, 0.4)]),
           vel={'X': spread(160), 'Y': spread(320, 0.5), 'Z': (300, [(0, -0.2), (1, -0.6)], [(0, 0.9), (1, 0.3)])},
           color=[(0, 1.0, 0.9, 0.6), (0.4,) + EMBER, (1,) + HOSTILE], alpha=[(0, 1), (0.7, 0.8), (1, 0)], grav=(45, 20)),
        el('arc', 'arcs', oneshot=(2, 1), life=(180, 80), org=(-1, 0, 0), offset='cylinder', off_r=(14, 18),
           size=(30, [(0, 0.7), (1, 1)]), color=FIELD, alpha=[(0, 0.9), (0.5, 0.6), (1, 0)]),
    ]


def field_shape_problems(name, els):
    """THE ROUNDED RULE, checked on the built elements: no sprite wider than FLAT_MAX, every cylinder spawn (a ring)
    ON the field sphere around the normal, and at least three rings."""
    bad, rings = [], 0
    for e in els:
        g = e.graph('sizeGraph0')
        widest = g.scale * max(row[1] for c in g.curves for row in c)
        if widest > FLAT_MAX + 1e-6:
            bad.append('%s/%s: a %g-unit sprite (> FLAT_MAX %d): a flat plate on a round field' % (name, e.name, widest, FLAT_MAX))
        if 'spawnOffsetCylinder' in e.flags('flags') and e.name.startswith('ripple_ring'):
            rings += 1
            x = e.nums('spawnOrgX')[0]
            rad, rad_rand = e.nums('spawnOffsetRadius')
            h, h_rand = e.nums('spawnOffsetHeight')
            axis = e.nums('spawnOffsetCylindricalAxis')[0]
            off = math.hypot(SR + x, rad) - SR
            if abs(off) > 0.5 or rad_rand or h or h_rand or axis != 0:
                bad.append('%s/%s: the ring is %.1f u off the field (x %g, r %g+%g, h %g+%g, axis %g)' % (name, e.name, off, x, rad, rad_rand, h, h_rand, axis))
    if rings < 3:
        bad.append('%s: %d rings on the field (the rounded ripple needs >= 3)' % (name, rings))
    return bad


def shape_gate_selftest():
    """The gate must still catch what it exists for: the first cut's 150-unit flat ring, and a ring off the sphere."""
    flat = el('ring', 'ring', oneshot=(1, 0), life=(460, 0), size=(150, [(0, 0.12), (1, 1)]), color=FIELD_HOT)
    off = el('glow', 'ripple_ring_9', oneshot=(8, 0), life=(200, 0), org=(0, 0, 0), offset='cylinder', off_r=(60, 0),
             size=(16, [(0, 1), (1, 1)]), color=FIELD)
    good = ripple('ripple', CROSS_RINGS, FIELD_HOT, FIELD)
    misses = []
    if not field_shape_problems('selftest', good + [flat]):
        misses.append('a 150-unit flat ring passed')
    if not field_shape_problems('selftest', good + [off]):
        misses.append('a ring 7.8 u off the sphere passed')
    if field_shape_problems('selftest', good):
        misses.append('the shipping rings failed')
    return misses


# =========================================================================================================================
# THE HAVEN POWERS UP (one-shot at the dome centre, angles 0)
# =========================================================================================================================
def boot():
    els = [
        el('glow', 'flash', oneshot=(1, 0), life=(380, 0), org=(0, 0, 20), size=(r3(300 * SCALE), [(0, 0.5), (0.3, 1), (1, 1.1)]),
           color=FIELD_HOT, alpha=[(0, 1), (0.4, 0.6), (1, 0)]),
        el('shock_elec', 'shock', oneshot=(1, 0), life=(520, 0), org=(0, 0, 30), size=(r3(420 * SCALE), [(0, 0.3), (1, 1)]),
           color=FIELD, alpha=[(0, 0.8), (1, 0)]),
        # light racing up the field to its crown
        in_world(el('glow', 'rise', oneshot=(10, 0), life=(620, 0), run='world', org=(0, 0, 10),
                    size=(60, [(0, 1), (1, 0.4)]), color=FIELD_HOT, alpha=[(0, 1), (1, 0)]),
                 Z=(500, [(0, 0.9), (1, 0.2)], [(0, 1.0), (1, 0.3)])),
        el('incand', 'sparkles', oneshot=(54, 10), life=(700, 300), run='world', org=(0, 0, 130), offset='sphere',
           off_r=(160, 60), size=(8, [(0, 1), (0.5, 0.7), (1, 0)]), vel=xyz(spread(120, 0.4)), color=FIELD_HOT,
           alpha=[(0, 1), (0.3, 0.5), (0.6, 0.9), (1, 0)], grav=(8, 8)),
    ]
    for f in H['FINS']:
        g = tuple(r3(v) for v in f['g'])
        els.append(el('glow', 'gem_flash_' + f['tag'], oneshot=(1, 0), life=(300, 0), org=g, size=(120, [(0, 0.6), (0.3, 1), (1, 1.1)]),
                      color=GEM, alpha=[(0, 1), (1, 0)]))
        els.append(el('incand', 'gem_burst_' + f['tag'], oneshot=(8, 3), life=(480, 200), run='spawn', org=g,
                      size=(7, [(0, 1), (1, 0)]), vel=xyz(spread(260, 0.4)), color=FIELD_HOT,
                      alpha=[(0, 1), (0.6, 0.7), (1, 0)], grav=(25, 10)))
    return els


# =========================================================================================================================
# THE CORRUPTED STATE (docs/202 v3): the field before its guardians are dead
# =========================================================================================================================
def corrupt():
    """Looping at the dome centre (angles 0). The safe ambient's anchors, gone bad: no cyan anywhere."""
    els = []
    for f in H['FINS']:
        g = tuple(r3(v) for v in f['g'])
        # the gems smoulder: a dim red orb that breathes, with a slow red spark now and then
        els.append(el('orb', 'gem_' + f['tag'], loop=(120, 0), life=(240, 0), run='effect', org=g,
                      size=(40, [(0, 0.9), (1, 1.1)]), color=DARK_HOT, alpha=steady(0.4)))
        els.append(el('incand', 'gem_spark_' + f['tag'], loop=(900, 0), life=(520, 200), run='effect', org=g, offset='sphere',
                      off_r=(6, 10), size=(6, [(0, 0.3), (0.3, 1.1), (1, 0)]), color=DARK_EMBER,
                      alpha=[(0, 0), (0.2, 1), (0.5, 0.3), (0.7, 0.8), (1, 0)]))
    # red arcs crawling the lattice at the glint sites (fewer, slower than the safe glints)
    for i, p in enumerate(GLINTS[::2]):
        els.append(el('arc', 'crawl_%02d' % i, loop=(1500 + 110 * (i % 5), 0), life=(170, 90), run='effect', org=p,
                      offset='sphere', off_r=(0, 22), size=(26, [(0, 0.6), (0.5, 1), (1, 0.7)]), color=DARK_HOT,
                      alpha=[(0, 0), (0.2, 0.85), (0.5, 0.35), (0.8, 0.7), (1, 0)]))
    els += [
        # the dark heart: a deep red glow low in the field, slowly throbbing
        el('glow', 'heart', loop=(180, 0), life=(2600, 0), run='effect', org=(0, 0, 58),
           size=(170, [(0, 0.86), (0.5, 1.0), (1, 0.86)]), color=DARK, alpha=[(0, 0), (0.5, 0.16), (1, 0)]),
        # embers drifting UP through the field (z 20..230), flickering
        in_world(el('incand', 'embers', loop=(120, 0), life=(3200, 1000), run='world', org=(0, 0, 70), offset='sphere',
                    off_r=(20, 200), size=(4, [(0, 0.5), (0.2, 1), (0.8, 0.9), (1, 0.2)]), color=[(0,) + DARK_EMBER, (1,) + DARK_HOT],
                    alpha=[(0, 0), (0.1, 0.9), (0.4, 0.45), (0.6, 0.85), (1, 0)]),
                 X=spread(7), Y=spread(7), Z=(24, [(0, 0.4), (1, 0.7)], [(0, 0.8), (1, 1)])),
        # a sooty haze crawling over the field's floor
        in_world(el('smoke', 'haze', loop=(300, 0), life=(3000, 800), run='world', org=(0, 0, 14), offset='cylinder',
                    off_r=(60, 250), off_h=(0, 10), size=(120, [(0, 0.6), (0.5, 1), (1, 1.2)]), color=SOOT,
                    alpha=[(0, 0), (0.3, 0.16), (0.7, 0.12), (1, 0)]),
                 X=spread(5), Y=spread(5), Z=(8, [(0, 0.5), (1, 0.8)], [(0, 0.8), (1, 1)])),
        # the PROJECTOR gone red, dripping embers DOWN into the field's crown
        el('orb', 'projector', loop=(150, 0), life=(300, 0), run='effect', org=(0, 0, r3(PROJ_TIP - 6)),
           size=(64, [(0, 0.96), (1, 1.04)]), color=DARK_HOT, alpha=steady(0.45)),
        in_world(el('incand', 'projector_drip', loop=(220, 0), life=(2600, 700), run='world', org=(0, 0, r3(PROJ_TIP - 14)),
                    offset='sphere', off_r=(4, 24), size=(4, [(0, 1), (0.7, 0.8), (1, 0.2)]), color=DARK_EMBER,
                    alpha=[(0, 0.8), (0.7, 0.5), (1, 0)]),
                 X=spread(8), Y=spread(8), Z=(110, [(0, -0.5), (1, -0.7)], [(0, -1), (1, -1)])),
        # v5: the heart's red light, a slow throb on the hall (a real light: the machines and the walls take it)
        heart_light('heart_light', DARK_LIGHT, **CORRUPT_LIGHT),
    ]
    return els


def fury():
    """Looping at the dome centre WHILE THE GUARDIANS LIVE (v5): the corrupt field in a frenzy - the gems blaze, every
    glint site crawls with arcs, embers pour up, the heart throbs fast and bright, a vortex of soot turns round it, the
    red light pulses with it. The wake swaps it in for the corrupt loop; the purification's bloom swaps in the safe one."""
    els = []
    for f in H['FINS']:
        g = tuple(r3(v) for v in f['g'])
        els.append(el('orb', 'gem_' + f['tag'], loop=(90, 0), life=(360, 0), run='effect', org=g,
                      size=(46, [(0, 0.8), (0.5, 1.2), (1, 0.8)]), color=DARK_HOT, alpha=steady(0.6)))
        els.append(el('incand', 'gem_spark_' + f['tag'], loop=(380, 0), life=(420, 180), run='effect', org=g, offset='sphere',
                      off_r=(6, 12), size=(7, [(0, 0.3), (0.3, 1.2), (1, 0)]), color=DARK_EMBER,
                      alpha=[(0, 0), (0.2, 1), (0.5, 0.4), (0.7, 0.9), (1, 0)]))
    for i, p in enumerate(GLINTS):
        els.append(el('arc', 'crawl_%02d' % i, loop=(640 + 50 * (i % 5), 0), life=(190, 90), run='effect', org=p,
                      offset='sphere', off_r=(0, 24), size=(30, [(0, 0.6), (0.5, 1), (1, 0.7)]), color=DARK_HOT,
                      alpha=[(0, 0), (0.2, 0.95), (0.5, 0.4), (0.8, 0.8), (1, 0)]))
    els += [
        el('glow', 'heart', loop=(110, 0), life=(1100, 0), run='effect', org=(0, 0, 58),
           size=(190, [(0, 0.8), (0.5, 1.05), (1, 0.8)]), color=DARK, alpha=[(0, 0), (0.5, 0.28), (1, 0)]),
        el('swirl', 'vortex', loop=(420, 0), life=(1700, 0), run='effect', org=(0, 0, 36),
           size=(230, [(0, 0.7), (1, 1.15)]), color=SOOT, alpha=[(0, 0), (0.3, 0.3), (0.7, 0.26), (1, 0)], spin=((0, 360), (70, 110))),
        in_world(el('incand', 'embers', loop=(60, 0), life=(2400, 800), run='world', org=(0, 0, 60), offset='sphere',
                    off_r=(20, 210), size=(5, [(0, 0.5), (0.2, 1), (0.8, 0.9), (1, 0.2)]), color=[(0,) + DARK_EMBER, (1,) + DARK_HOT],
                    alpha=[(0, 0), (0.1, 0.95), (0.4, 0.5), (0.6, 0.9), (1, 0)]),
                 X=spread(12), Y=spread(12), Z=(42, [(0, 0.5), (1, 0.8)], [(0, 0.85), (1, 1)])),
        in_world(el('smoke', 'haze', loop=(220, 0), life=(2600, 700), run='world', org=(0, 0, 14), offset='cylinder',
                    off_r=(60, 250), off_h=(0, 10), size=(130, [(0, 0.6), (0.5, 1), (1, 1.25)]), color=SOOT,
                    alpha=[(0, 0), (0.3, 0.22), (0.7, 0.16), (1, 0)]),
                 X=spread(9), Y=spread(9), Z=(12, [(0, 0.5), (1, 0.8)], [(0, 0.8), (1, 1)])),
        el('orb', 'projector', loop=(150, 0), life=(300, 0), run='effect', org=(0, 0, r3(PROJ_TIP - 6)),
           size=(70, [(0, 0.9), (1, 1.1)]), color=DARK_HOT, alpha=steady(0.55)),
        in_world(el('incand', 'projector_drip', loop=(120, 0), life=(2400, 600), run='world', org=(0, 0, r3(PROJ_TIP - 14)),
                    offset='sphere', off_r=(4, 24), size=(5, [(0, 1), (0.7, 0.8), (1, 0.2)]), color=DARK_EMBER,
                    alpha=[(0, 0.9), (0.7, 0.5), (1, 0)]),
                 X=spread(10), Y=spread(10), Z=(130, [(0, -0.5), (1, -0.7)], [(0, -1), (1, -1)])),
        heart_light('heart_light', DARK_LIGHT, **FURY_LIGHT),
    ]
    return els


# =========================================================================================================================
# THE PURIFICATION (docs/202 v5): the convulsion, then the collapse (the bloom is cleanse() below)
# =========================================================================================================================
def inward(e):
    """Velocity in the spawn OFFSET's frame on a SPHERE offset: local X = outward from the sphere's centre through the
    spawn point, so a negative X runs the particle home - the implosion. (Stock's own usage: blood/fx_blood_impact_exp_
    robot_lg.efx and destruct/fx_dest_building_xlg_twins_sgen.efx spawn on a sphere with runRelToOffset and ONLY a
    positive X velocity, 2,400-2,500 u/s - an explosion flying outward.)"""
    e.set_flags('flags', add=('runRelToOffset',), remove=('runRelToEffect', 'runRelToWorld', 'runRelToSpawn'))
    return e


def convulse():
    """One-shot at the dome centre for the convulsion's CONVULSE_MS: an ACCELERATING STROBE on the heart (one flash per
    step of the module's purge_strobe_steps(), whitening toward the end), arcs snapping over the whole sphere in two
    thickening waves, lightning cracks late, embers blown out of the heart, the heart swelling toward the collapse, a soot
    vortex drawn into it, every gem flaring at random."""
    n = len(STROBE_MS)
    els = []
    for i, ms in enumerate(STROBE_MS):
        k = i / max(1, n - 1)
        col = tuple(r3(DARK_HOT[j] + (PURGE_HOT[j] - DARK_HOT[j]) * k * 0.6) for j in range(3))
        els.append(el('glow', 'strobe_%02d' % i, oneshot=(1, 0), life=(130, 0), delay=(ms, 0), org=(0, 0, 44),
                      size=(r3((220 + 120 * k) * SCALE), [(0, 0.6), (0.3, 1), (1, 1.1)]), color=col, alpha=[(0, 0.95), (1, 0)]))
    els += [
        el('arc', 'arcs_a', oneshot=(16, 4), life=(200, 90), delay=(0, CONVULSE_MS // 2), org=(0, 0, r3(CZ)), offset='sphere',
           off_r=(r3(SR - 4), 4), size=(44, [(0, 0.7), (1, 1)]), color=DARK_HOT, alpha=[(0, 0.95), (0.5, 0.6), (1, 0)]),
        el('arc', 'arcs_b', oneshot=(26, 6), life=(200, 90), delay=(CONVULSE_MS // 2, CONVULSE_MS // 2), org=(0, 0, r3(CZ)), offset='sphere',
           off_r=(r3(SR - 4), 4), size=(50, [(0, 0.7), (1, 1)]), color=[(0,) + DARK_HOT, (1,) + PURGE_HOT], alpha=[(0, 1), (0.5, 0.65), (1, 0)]),
        el('lightning', 'cracks', oneshot=(10, 3), life=(160, 80), delay=(CONVULSE_MS * 2 // 3, CONVULSE_MS // 3), org=(0, 0, r3(CZ)),
           offset='sphere', off_r=(r3(SR - 2), 2), size=(70, [(0, 0.8), (1, 1.1)]), color=PURGE_HOT, alpha=[(0, 1), (1, 0)]),
        el('incand', 'embers', oneshot=(40, 8), life=(900, 400), delay=(0, CONVULSE_MS - 300), run='world', org=(0, 0, 50), offset='sphere',
           off_r=(10, 30), size=(7, [(0, 1), (0.6, 0.7), (1, 0)]), vel=xyz(spread(260, 0.4)), color=[(0,) + DARK_EMBER, (1,) + DARK_HOT],
           alpha=[(0, 1), (0.3, 0.6), (0.6, 0.9), (1, 0)], grav=(20, 10)),
        el('glow', 'heart_swell', oneshot=(1, 0), life=(CONVULSE_MS, 0), org=(0, 0, 58), size=(170, [(0, 0.9), (0.6, 1.4), (1, 2.0)]),
           color=[(0,) + DARK, (0.7,) + DARK_HOT, (1,) + PURGE_HOT], alpha=[(0, 0.2), (0.6, 0.45), (0.9, 0.7), (1, 0.9)]),
        el('swirl', 'vortex', oneshot=(1, 0), life=(CONVULSE_MS, 0), org=(0, 0, 40), size=(300, [(0, 1), (0.7, 0.6), (1, 0.15)]),
           color=SOOT, alpha=[(0, 0), (0.2, 0.4), (0.9, 0.35), (1, 0)], spin=((0, 360), (120, 200))),
    ]
    for f in H['FINS']:
        g = tuple(r3(v) for v in f['g'])
        els.append(el('glow', 'gem_flare_' + f['tag'], oneshot=(3, 1), life=(240, 60), delay=(100, CONVULSE_MS - 400), org=g,
                      size=(120, [(0, 0.6), (0.3, 1), (1, 1.1)]), color=DARK_HOT, alpha=[(0, 1), (1, 0)]))
    return els


def collapse():
    """One-shot at the dome centre, THE COLLAPSE: the corrupted field IMPLODES - beads spawned on the whole sphere rush
    inward along their own normals and turn white as they converge; a white-hot flash and a real light flash at the heart,
    a shock ring, a column up to the projector, white sparks thrown up, the last soot blown out along the floor. (About
    four in ten of the beads spawn under the floor, hidden; hence the count.)"""
    return [
        inward(el('glow', 'implode', oneshot=(100, 8), life=(360, 60), org=(0, 0, r3(CZ)), offset='sphere', off_r=(r3(SR - 6), 6),
                  size=(16, [(0, 0.8), (0.7, 1), (1, 0.5)]), vel={'X': (-980, [(0, 1.0), (1, 0.55)])},
                  color=[(0,) + DARK_HOT, (0.6, 1.0, 0.6, 0.45), (1,) + PURGE_HOT], alpha=[(0, 0), (0.08, 1), (0.8, 0.9), (1, 0)])),
        el('glow', 'flash', oneshot=(1, 0), life=(420, 0), org=(0, 0, 44), size=(r3(380 * SCALE), [(0, 0.3), (0.2, 1), (1, 1.25)]),
           color=PURGE_HOT, alpha=[(0, 0), (0.1, 1), (0.45, 0.75), (1, 0)]),
        el('shock_elec', 'shock', oneshot=(1, 0), life=(560, 0), delay=(60, 0), org=(0, 0, 30), size=(r3(500 * SCALE), [(0, 0.2), (1, 1)]),
           color=PURGE, alpha=[(0, 0.95), (1, 0)]),
        el('glow', 'column', oneshot=(1, 0), life=(700, 0), delay=(80, 0), org=(0, 0, r3((TOP + PROJ_TIP) / 2)),
           size=(110, [(0, 0.2), (0.3, 1), (1, 0.5)]), color=PURGE_HOT, alpha=[(0, 0), (0.3, 0.8), (1, 0)]),
        el('incand', 'sparks', oneshot=(36, 8), life=(700, 300), delay=(120, 60), run='world', org=(0, 0, 50), offset='sphere', off_r=(10, 30),
           size=(7, [(0, 1), (0.6, 0.7), (1, 0)]), vel={'X': spread(300, 0.5), 'Y': spread(300, 0.5), 'Z': (480, [(0, 0.45), (1, 0.1)], [(0, 1), (1, 0.4)])},
           color=[(0,) + PURGE_HOT, (1,) + PURGE], alpha=[(0, 1), (0.6, 0.7), (1, 0)], grav=(60, 15)),
        in_world(el('smoke', 'soot_out', oneshot=(14, 2), life=(900, 300), delay=(100, 40), run='world', org=(0, 0, 20), offset='cylinder',
                    off_r=(30, 30), off_h=(0, 10), size=(90, [(0, 0.5), (1, 1.4)]), color=SOOT, alpha=[(0, 0.35), (1, 0)]),
                 X=spread(380, 0.3), Y=spread(380, 0.3), Z=(10, [(0, 0.5), (1, 0.2)], [(0, 1), (1, 0.4)])),
        heart_light('flash_light', PURGE_LIGHT, radius=400, intensity=650, life=520, oneshot=True),
    ]


def wake():
    """One-shot at the dome centre: the guardians rise - the corrupted field convulses."""
    els = [
        el('shock_elec', 'shock', oneshot=(1, 0), life=(560, 0), org=(0, 0, 24), size=(r3(440 * SCALE), [(0, 0.25), (1, 1)]),
           color=DARK_HOT, alpha=[(0, 0.9), (1, 0)]),
        el('glow', 'flash', oneshot=(1, 0), life=(420, 0), org=(0, 0, 40), size=(r3(300 * SCALE), [(0, 0.5), (0.3, 1), (1, 1.15)]),
           color=DARK_HOT, alpha=[(0, 0.95), (0.4, 0.5), (1, 0)]),
        el('glow', 'heart_swell', oneshot=(1, 0), life=(900, 0), org=(0, 0, 58), size=(160, [(0, 0.8), (0.4, 1.3), (1, 1.6)]),
           color=DARK, alpha=[(0, 0.5), (0.5, 0.3), (1, 0)]),
        # embers blown out of the heart, falling back
        el('incand', 'embers', oneshot=(44, 8), life=(900, 400), run='world', org=(0, 0, 50), offset='sphere', off_r=(10, 30),
           size=(7, [(0, 1), (0.6, 0.7), (1, 0)]), vel=xyz(spread(220, 0.4)), color=[(0,) + DARK_EMBER, (1,) + DARK_HOT],
           alpha=[(0, 1), (0.3, 0.6), (0.6, 0.9), (1, 0)], grav=(20, 10)),
        # arcs snapping across the dome
        # (the sphere's centre is under the floor: about four in ten of these spawn under it, hidden; hence the count)
        el('arc', 'arcs', oneshot=(14, 4), life=(200, 90), delay=(0, 220), org=(0, 0, r3(CZ)), offset='sphere', off_r=(r3(SR - 4), 4),
           size=(44, [(0, 0.7), (1, 1)]), color=DARK_HOT, alpha=[(0, 0.95), (0.5, 0.6), (1, 0)]),
    ]
    for f in H['FINS']:
        g = tuple(r3(v) for v in f['g'])
        els.append(el('glow', 'gem_flare_' + f['tag'], oneshot=(1, 0), life=(360, 0), org=g, size=(120, [(0, 0.6), (0.3, 1), (1, 1.1)]),
                      color=DARK_HOT, alpha=[(0, 1), (1, 0)]))
    return els


def guard_down():
    """One-shot at the dome centre: a guardian fell - a crimson crack over the field."""
    return [
        el('glow', 'flash', oneshot=(1, 0), life=(300, 0), org=(0, 0, 50), size=(r3(220 * SCALE), [(0, 0.6), (0.3, 1), (1, 1.1)]),
           color=DARK_HOT, alpha=[(0, 0.85), (1, 0)]),
        el('arc', 'cracks', oneshot=(12, 3), life=(220, 100), delay=(0, 160), org=(0, 0, r3(CZ)), offset='sphere', off_r=(r3(SR - 4), 4),
           size=(44, [(0, 0.6), (1, 1)]), color=DARK_HOT, alpha=[(0, 1), (0.5, 0.6), (1, 0)]),
        el('incand', 'sparks', oneshot=(24, 6), life=(700, 300), run='world', org=(0, 0, 60), offset='sphere', off_r=(20, 40),
           size=(6, [(0, 1), (1, 0)]), vel=xyz(spread(260, 0.4)), color=DARK_EMBER, alpha=[(0, 1), (0.6, 0.7), (1, 0)], grav=(28, 10)),
    ]


def cleanse():
    """One-shot at the dome centre, THE BLOOM (v5: the purification's third beat, after the convulsion and the collapse):
    the field comes back white-cyan - a big flash at the heart, a cyan shock ring, light racing up to the crown, a column
    to the projector, sparkles washing over the whole dome, the gems flashing cyan, the last red embers dying as they fall."""
    els = [
        el('glow', 'flash', oneshot=(1, 0), life=(520, 0), org=(0, 0, 40), size=(r3(360 * SCALE), [(0, 0.4), (0.25, 1), (1, 1.2)]),
           color=FIELD_HOT, alpha=[(0, 1), (0.35, 0.7), (1, 0)]),
        el('shock_elec', 'shock', oneshot=(1, 0), life=(640, 0), org=(0, 0, 30), size=(r3(480 * SCALE), [(0, 0.25), (1, 1)]),
           color=FIELD, alpha=[(0, 0.9), (1, 0)]),
        # light racing up the field to its crown, then a column up to the projector
        in_world(el('glow', 'rise', oneshot=(14, 0), life=(700, 0), run='world', org=(0, 0, 10),
                    size=(70, [(0, 1), (1, 0.4)]), color=FIELD_HOT, alpha=[(0, 1), (1, 0)]),
                 Z=(520, [(0, 0.9), (1, 0.2)], [(0, 1.0), (1, 0.3)])),
        el('glow', 'column', oneshot=(1, 0), life=(900, 0), delay=(300, 0), org=(0, 0, r3((TOP + PROJ_TIP) / 2)),
           size=(90, [(0, 0.3), (0.3, 1), (1, 0.6)]), color=FIELD_HOT, alpha=[(0, 0), (0.3, 0.7), (1, 0)]),
        # sparkles washing over the whole dome (spawned on the sphere, drifting up)
        in_world(el('incand', 'wash', oneshot=(86, 12), life=(900, 400), delay=(0, 300), run='world', org=(0, 0, r3(CZ)),
                    offset='sphere', off_r=(r3(SR - 10), 12), size=(8, [(0, 1), (0.5, 0.7), (1, 0)]), color=FIELD_HOT,
                    alpha=[(0, 1), (0.3, 0.5), (0.6, 0.9), (1, 0)]),
                 Z=(40, [(0, 1), (1, 0.4)], [(0, 1), (1, 0.6)])),
        # the last of the corruption blown out: red embers die as they fall
        el('incand', 'last_embers', oneshot=(30, 6), life=(800, 300), run='world', org=(0, 0, 50), offset='sphere', off_r=(10, 40),
           size=(6, [(0, 1), (1, 0)]), vel=xyz(spread(280, 0.4)), color=[(0,) + DARK_HOT, (1, 0.3, 0.05, 0.02)],
           alpha=[(0, 1), (0.5, 0.6), (1, 0)], grav=(30, 10)),
    ]
    for f in H['FINS']:
        g = tuple(r3(v) for v in f['g'])
        els.append(el('glow', 'gem_flash_' + f['tag'], oneshot=(1, 0), life=(380, 0), delay=(120, 0), org=g,
                      size=(140, [(0, 0.5), (0.3, 1), (1, 1.1)]), color=GEM, alpha=[(0, 1), (1, 0)]))
        els.append(el('incand', 'gem_burst_' + f['tag'], oneshot=(10, 3), life=(520, 200), delay=(120, 0), run='spawn', org=g,
                      size=(7, [(0, 1), (1, 0)]), vel=xyz(spread(280, 0.4)), color=FIELD_HOT,
                      alpha=[(0, 1), (0.6, 0.7), (1, 0)], grav=(25, 10)))
    return els


# =========================================================================================================================
# THE SLOW, VISIBLE (user 2026-10-03, tweak #1): looping on a carrier LINKED to an enemy inside a safe field
# =========================================================================================================================
def slowed():
    """The carrier rides ~36 up the body (chest height); the cylinder spawns round the carrier's Z (the default axis)."""
    return [
        # thin cyan arcs crawling round the body
        el('arc', 'arcs', loop=(150, 0), life=(130, 50), offset='cylinder', off_r=(13, 7), off_h=(0, 36),
           size=(20, [(0, 0.7), (0.5, 1), (1, 0.6)]), color=FIELD, alpha=[(0, 0), (0.2, 0.9), (0.6, 0.4), (1, 0)]),
        # frost sparks sifting off the body, down
        in_world(el('incand', 'frost', loop=(95, 0), life=(520, 200), run='world', offset='sphere', off_r=(12, 12),
                    size=(3, [(0, 0.6), (0.3, 1), (1, 0)]), color=FIELD_HOT, alpha=[(0, 0), (0.2, 0.9), (0.6, 0.5), (1, 0)]),
                 X=spread(10), Y=spread(10), Z=(44, [(0, -0.4), (1, -0.9)], [(0, -0.7), (1, -1)])),
        # a faint glow at the chest so the body reads lit even between arcs
        el('glow', 'chest', loop=(200, 0), life=(400, 0), size=(26, [(0, 0.9), (1, 1.1)]), color=FIELD, alpha=steady(0.2)),
    ]


# =========================================================================================================================
# A BULLET STOPS ON THE BARRIER (one-shot; local X = the outward normal at the hit) - docs/202 v4
# =========================================================================================================================
DEFLECT_RINGS = [                      # small and hot: 12 / 30 / 53 u out
    (2, 6, 0, 10, 0.95),
    (5, 12, 35, 13, 0.8),
    (9, 18, 80, 16, 0.55),
]


def deflect():
    return ripple('ripple', DEFLECT_RINGS, (1.0, 0.75, 0.55), DARK_HOT, fade=(16, 32)) + [
        near_fade(el('incand', 'core', oneshot=(1, 0), life=(140, 0), size=(14, [(0, 0.6), (0.3, 1), (1, 0.4)]),
                     color=(1.0, 0.6, 0.4), alpha=[(0, 1), (1, 0)]), 16, 32),
        near_fade(el('glow', 'flash', oneshot=(1, 0), life=(180, 0), size=(34, [(0, 0.6), (0.3, 1), (1, 1.05)]),
                     color=DARK_HOT, alpha=[(0, 0.75), (1, 0)]), 24, 48),
        # sparks thrown back off the wall (they leave it on purpose, and fall)
        el('spark', 'sparks', oneshot=(8, 3), life=(260, 120), run='spawn', size=(9, [(0, 1), (1, 0.4)]),
           vel={'X': spread(140), 'Y': spread(260, 0.5), 'Z': (240, [(0, -0.2), (1, -0.6)], [(0, 0.9), (1, 0.3)])},
           color=[(0, 1.0, 0.75, 0.5), (0.4,) + DARK_EMBER, (1,) + DARK_HOT], alpha=[(0, 1), (0.7, 0.8), (1, 0)], grav=(40, 20)),
    ]


# =========================================================================================================================
# THE FALLING MOTES (PK43): looping at a fixed point - the haven thresholds and the departure hall's oculus
# =========================================================================================================================
def motes():
    """A soft column of lit dust motes drifting down from the anchor: fine dust spread through ~240 units under it (and
    ~150 round it), a few brighter flecks, each falling 10-22 u/s with a faint sideways drift over 3.5-6.5 s. The lit
    material takes the room's light, so the column is faint and wears the district's colour; no light of its own."""
    return [
        in_world(el('mote', 'dust', loop=(45, 0), life=(5000, 1500), run='world', org=(0, 0, -240), org_rand=(0, 0, 240),
                    offset='sphere', off_r=(0, 150), size=(1.4, [(0, 0.8), (0.5, 1.0), (1, 0.8)]), color=(0.95, 0.95, 1.0),
                    alpha=[(0, 0), (0.12, 0.8), (0.4, 0.55), (0.6, 0.85), (0.88, 0.6), (1, 0)]),
                 X=spread(5), Y=spread(5), Z=(22, [(0, -0.45), (1, -0.45)], [(0, -1), (1, -1)])),
        in_world(el('mote', 'flecks', loop=(300, 0), life=(5500, 1000), run='world', org=(0, 0, -220), org_rand=(0, 0, 220),
                    offset='sphere', off_r=(10, 130), size=(2.2, [(0, 0.7), (0.5, 1.0), (1, 0.7)]), color=(1.0, 1.0, 1.0),
                    alpha=[(0, 0), (0.15, 0.55), (0.5, 0.25), (0.7, 0.6), (1, 0)]),
                 X=spread(4), Y=spread(4), Z=(16, [(0, -0.5), (1, -0.5)], [(0, -1), (1, -1)])),
    ]


def mote_donor_problems():
    """The vendored mote donor is the pinned bytes, and still the one lit-mote element (never a stub)."""
    if not MOTE_DONOR.exists():
        return ['the mote donor %s is missing' % MOTE_DONOR.relative_to(ROOT)]
    text = MOTE_DONOR.read_bytes().replace(b'\r\n', b'\n')
    bad = []
    if hashlib.sha256(text).hexdigest() != MOTE_DONOR_SHA:
        bad.append('the mote donor changed since it was vendored (sha256 pinned in MOTE_DONOR_SHA)')
    if b'gfx_debug_missing_fx' in text:
        bad.append('the mote donor is a stub')
    return bad


EFFECTS = [
    ('fx_tod_haven_ambient', ambient, 420),
    ('fx_tod_haven_corrupt', corrupt, 420),
    ('fx_tod_haven_cross', cross, 280),
    ('fx_tod_haven_push', push, 260),
    ('fx_tod_haven_boot', boot, 460),
    ('fx_tod_haven_wake', wake, 460),
    ('fx_tod_haven_guard_down', guard_down, 320),
    ('fx_tod_haven_cleanse', cleanse, 480),
    ('fx_tod_haven_slowed', slowed, 80),
    ('fx_tod_haven_deflect', deflect, 120),
    ('fx_tod_haven_fury', fury, 420),
    ('fx_tod_haven_convulse', convulse, 460),
    ('fx_tod_haven_collapse', collapse, 480),
    ('fx_tod_haven_motes', motes, 420),        # PK43: down ~240 + a 150 sphere under the anchor, and their 6.5 s of fall
]
NAMES = [row[0] for row in EFFECTS]
# they reach the projector
TALL = ('fx_tod_haven_ambient', 'fx_tod_haven_corrupt', 'fx_tod_haven_boot', 'fx_tod_haven_cleanse', 'fx_tod_haven_fury', 'fx_tod_haven_convulse', 'fx_tod_haven_collapse')


def build():
    out = {}
    for name, fn, half in EFFECTS:
        els = fn()
        lo, hi = box(half)
        if name in TALL:                                                   # the projector hangs from the hall's ceiling
            lo = (lo[0], lo[1], min(lo[2], -20)); hi = (hi[0], hi[1], max(hi[2], int(TOP) + 60, int(VOID) + 20))
        out[name] = S.effect(els, lo, hi)
    return out


def main(argv):
    fx = build()
    L.PREFIX = PREFIX                    # validate() checks paths / children against OUR prefix
    names = set(fx)
    problems = [p for n in NAMES for p in L.validate(n, fx[n], names)]
    for n, fn in (('fx_tod_haven_cross', cross), ('fx_tod_haven_push', push), ('fx_tod_haven_deflect', deflect)):
        problems += field_shape_problems(n, fn())
    problems += ['shape gate self-test: ' + m for m in shape_gate_selftest()]
    problems += mote_donor_problems()
    if problems:
        print('HAVEN FX INVALID:\n  ' + '\n  '.join(problems))
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
            print('HAVEN FX STALE: ' + ', '.join(bad) + ' - run python -B tools/haven/make_fx.py')
            return 1
        print('HAVEN FX OK: %d effects' % len(fx))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for n in NAMES:
        (OUT / (n + '.efx')).write_bytes(fx[n].encode('utf-8'))
        parsed = E.parse(fx[n])
        peak = sum(L.peak_particles(e) for e in parsed.elements)
        print('wrote %s%s  (%d elements, peak ~%d particles)' % (PREFIX, n, len(parsed.elements), peak))
    print('HAVEN FX WRITTEN: %d effects -> %s' % (len(fx), OUT.relative_to(ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
