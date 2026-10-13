"""THE WUNDERSTRAHL'S BEAM AND ITS EFFECTS (docs/219), GENERATED - never hand-edit the outputs; change the tables below.

  python tools/wunderstrahl/fx/make_fx.py                         write everything under the repo (the default out-root)
  python tools/wunderstrahl/fx/make_fx.py --out-root DIR          write the .efx + the GDT under DIR instead (a stage in repo
                                                                  layout, e.g. tmp/wunderstrahl/stage); the textures always go
                                                                  to the repo's model_export/tod_wunderstrahl_fx, which the GDT
                                                                  names by its repo-relative path and which MUST be synced to
                                                                  the tools (a Copy-Tree line in sync_to_modtools.ps1, added by
                                                                  tools/wunderstrahl/wire.py)
  python tools/wunderstrahl/fx/make_fx.py --check [--out-root DIR] regenerate in memory, validate, FAIL (exit 1) if a written
                                                                  output differs, is missing, or a stray fx_ws_*.efx / texture
                                                                  sits there
  python tools/wunderstrahl/fx/make_fx.py --selftest              the validators against planted faults (exit 1 if one is missed)
  python tools/wunderstrahl/fx/make_fx.py --vendor [--force]      re-extract the donors from the private tools root (refuses if a
                                                                  stock file's sha256 moved since it was vendored)

WHAT IT WRITES
  share/raw/fx/tod/wunderstrahl/fx_ws_*.efx    the ten effects below
  source_data/tod2_wunderstrahl_fx.gdt         the two beams (tod2_ws_beam_1p / _3p), the flame table (tod2_ws_flametable),
                                               six effect materials (mtl_tod2_wsfx_*) and their five images (i_tod2_wsfx_*)
  model_export/tod_wunderstrahl_fx/*.png       the five generated textures (power of two, RGBA, deterministic math)

HOW THE ENGINE DRAWS IT (read off the stock beams in t7_beams.gdt and their effects; the Purifier = flamethrower_beam,
the Gauntlet of Siegfried = flamethrower_beam_dragon_gauntlet, the Genesis skull = dlc4_skull_turret_beam):
  * The weapon (gasweapon.gdf) draws flameBeamFirstPerson from the viewmodel's tag_flash and flameBeamThirdPerson from the
    world model's while the trigger is held. The beam wears `material` from startWidth at the lens to endWidth at maxLength,
    coloured startColor -> endColor, with uvMode "repeating horizontal" (U runs along the beam, repeating every
    textureRepeatLength units). Its beamShape is a RIBBON - the stock laser recipe: Gorod Krovi's laser trap
    (dlc3_laser_robot_trap) and the twenty i1024 lightning beams are ribbons wearing a texture with a soft profile across
    V (bright axis, clear edges), and a
    ribbon must face the camera round its axis (stock turret beams read from every side). The polygon shapes (triangle ..
    octagon, beam.awi) are closed tubes whose V mapping round the tube is not documented, so a profiled texture could band
    or stripe on them (the Purifier's hexagon wears one under its flames).
  * originEffect LOOPS at the origin while the beam lives (the Purifier's begin_1p loops forever: count 0); targetEffect loops
    at the target (our virtual target, BEAM_RANGE ahead, i.e. the beam's end in open air); blockedEffect loops where the beam
    is stopped, with blockedEffectSound as its loop; deathEffect is a one-shot at the origin once the beam has retracted.
    Their local frame: +X = the tag's forward at the origin; at the blocked / target end +X points back OUT of the surface
    (the Purifier's blocked effect spreads its flames in local Y/Z just off X = 0.5..5 and lights at X = 20).
  * beamEffect is played every beamEffectDistance units along the beam and carried outward at beamEffectSpeed units/s:
    its local +X is the beam's forward (the Purifier's emitter flies its flames along +X at velGraph0X 750 x 0.5). Stock
    beam effects end on their own (the Purifier's emitter: finite loops ~1 s = maxLength / speed) or loop forever (the
    waterfall's, the monolith coil's) - so the engine retires an instance at the beam's end. We author ONE instance as a
    one-shot timeline of particles that ride it (runRelToEffect).

THE LOOK (docs/219 + the user's words: "a laser down the middle, and then kind of swirls that swirl around that laser, with
little balls on the swirls ... like an aura beam"; yellow core, golden aura):
  CORE      the beam: a camera-facing ribbon wearing mtl_tod2_wsfx_core_1p / _3p (effect_lit_scroll_emissive_blend_nocull,
            the stock beams' family): a core texture with a soft profile ACROSS the beam (a white-hot axis, a warm body, a
            faint halo, clear at the edges) and faint filaments and a shimmer in the body that scroll outward along U, tinted
            a saturated yellow by startColor -> endColor (deeper gold far out; under HDR the axis burns white, the glow stays
            yellow). No view falloff (the shooter sees the 1p beam edge-on, where falloff would dim it to its floor).
            1p 0.8 -> 9 u wide, 3p 1.4 -> 14. BEAM_SHAPE is one switch: a closed shape gets the uniform tube texture and the
            3p falloff back, and the gate checks the texture that shape needs.
  AURA      fx_ws_aura_1p / _3p, the beamEffect: a gold DOUBLE HELIX round the core - a bright gold MAJOR strand and a
            thinner, dimmer, pale-lemon MINOR one 180 deg behind it - made of short glowing strand segments ('line' sprites oriented along the
            helix tangent by a tiny velocity, the trick the sky fleet's flame rays use), little white-yellow ORBS (the orb
            texture's amber halo) spiralling along the strands, a soft yellow sheath on the axis and twinkling motes. Each
            instance carries exactly `turns` full turns and beamEffectDistance = turns x pitch, so the chained instances
            tile into one continuous helix that slides outward at beamEffectSpeed - a helix translating along its axis reads
            as SPINNING (1p ~8 turns/s, 3p ~7.6). The two strands differ so the pattern repeats only every full pitch: a
            30 fps frame moves it <= STROBE_MAX of that (two equal strands would repeat every half pitch and strobe). Each
            orb SLIPS back along its strand (a point fixed on a sliding helix only moves straight ahead), so it spirals
            outward in the world and never outruns its carrier past a wall. The swirl lives `reach` units (alpha over the
            instance's age = its distance from the lens): it fades in off the lens, holds, fades out; past it the beam is
            the core alone (the helix is sub-pixel there anyway). 1p is tighter and fades near the camera (the 1p rule).
  ORIGIN    fx_ws_origin_1p / _3p (looping at tag_flash): a hot point, a soft halo, six gold sparks orbiting the lens (a
            slow ring), motes streaming out along the beam, one warm light (1p small and soft: everything <= ONE_P_MAX).
  IMPACT    fx_ws_impact (blockedEffect): a molten white-yellow core flickering on the wall, a still burn disc flat on the
            surface (the generated burn texture; IMPACT_DISC_FLAT False makes it a camera-facing glow), a glow, molten sparks
            and blinking droplets spraying off it, orbs splashing out, a thin lit smoke wisp, one flickering light.
  TIP       fx_ws_tip (targetEffect, the beam's end in open air at BEAM_RANGE): the core fizzling into a soft flare and a few
            motes - no wall splash and no light in mid-air. (docs/219's brief said impact for both: an impact on nothing reads
            as an invisible wall. TARGET_EFFECT below is the one-line switch back.)
  LENS      fx_ws_lens_cool (deathEffect): a fading glow, a dimming hot point, a heat wisp and three or four cinders at the
            lens (true one-shots: the engine plays it and nothing deletes it).
  ZOMBIE    fx_ws_zombie_burn (script, <= ~3/s per zombie): a hot flash, yellow sparks, embers, two flame licks, a soot puff.
  DEATH     fx_ws_disintegrate (script, at the torso): a yellow flash + pop + shock ring, an ember burst, orbs scattering, a
            dark lit ash puff, one small light flash. fx_ws_disintegrate_nl is the same without the light, for the script
            to play once kills come faster than lights should (a beam through a crowd).
  Every particle effect is ORIENTATION-FREE where the script plays it (zombie burn / disintegrate: sphere spawns, world
  velocities, world gravity), so any carrier angles work. The script plays those on a tod_ability_fx::burst_at carrier
  (a tag_origin host the server deletes after TOD_WS_BURN/DIE_LIFE), so they are authored for the server's LOOPING
  lane: every element loops once per ONCE_LOOP_MS - one round inside the carrier, stopped by its delete
  (KILL_FX_LOOPING; set it False for a client lane, where a looping effect loops until killed).

THE FLAME TABLE tod2_ws_flametable (the engine's flame STREAM, which a gas weapon also draws): made effectively INVISIBLE
  (fire / drips / smoke brightness 0, smoke max alpha 0, the longest chunk intervals and the smallest sizes the ranges
  allow, the fire window empty) and every material slot on mtl_tod2_wsfx_stream - the laser core's image in an ADDITIVE
  material, so anything that does draw reads as a thin yellow thread, never as fire, and a brightness of 0 adds nothing
  (the blend core material at brightness 0 would draw black). Its sound fields stay EMPTY (the weapon's loopFire* lane
  owns the audio). Its streamPrimaryLight is the warm yellow light that travels with the (invisible) stream:
  STREAM_LIGHT_RADIUS + flutter. NO STOCK BEAM WEAPON PAIRS ITS BEAM WITH AN AUTHORED FLAME TABLE: the Dragon Gauntlet's
  (wpn_t7_zmb_dlc3_gauntlet_dragon.gdt) names "default_laser", which the asset lists know only as a LASER asset, and the
  Panzer's (mechz_spiki.gdt, a native build in Map One) leaves both flameTable fields EMPTY. Empty is the proven path for
  the first build; this table is the option.

THE BUILDER is the sky fleet's through the lucky set's helpers (imported READ-ONLY, as tools/fxgen/elites/make_fx.py does).
Every element is a stock element (a sky-fleet template or a DONOR element vendored into donor/ with the stock file's sha256)
with every visible number rewritten here; the strand segments, the orbs and the burn disc wear our generated materials (the
beams and the flame table wear the rest). Lights are the map's one recipe (the
perk glow's light_small: white def, hue on colorGraph, shadowless, every lighting state, radius <= 400, at most two alive).
The beam and flame-table blocks start from vendored stock blocks (every field gdtdb expects) and every field is range-checked
against the vendored beam.awi / flametable.awi.

LOCKSTEP: BEAM_RANGE = _tod_wunderstrahl.gsc TOD_WS_RANGE and BEAM_LAUNCH_SPEED = TOD_WS_LAUNCH_SPEED (both read by
tools/wunderstrahl/test_wunderstrahl.js from the module-level lines below; keep each on its own line).

RULES THE WRITTEN FILES PASS (problems_of): effect paths <= 63 chars; no gfx_debug_missing_fx; no model / runner / child
effect / element sound; whole-ms times; only LOOPING effects loop forever and a one-shot ends within its stated length;
alphas 0..1; sizes >= 0; lights shadowless, all four states, radius 1..400, <= 2 alive; a particle budget per effect and an
estimate for a whole 2400-unit beam; THE 1P RULE (in an effect that can play at a face every sprite wider than NEAR_MAX
fades near the camera; in the 1p origin / lens effects nothing is wider than ONE_P_MAX across, reading a size as a radius
(SIZE_TO_WIDTH) until a native look settles it; in the 1p aura anything wider fades near the camera); a no-light (_nl)
variant carries no light; THE TILING (every strand segment / orb sits on its helix inside [0, distance) and distance =
turns x pitch = the beam's beamEffectDistance) and THE STROBE (a 30 fps frame moves the helix <= STROBE_MAX of its
period); the beam LOCKSTEP fields; the GDT grammar (opening brace, no // line); names <= 63 and unique per type against
every GDT in the repo, the private root and the stage; explicit surfaceType; images power of two; the core texture a
ribbon profile (clear edges, bright axis) that tiles along U; the 1p core without view falloff; the flame table
invisible + silent + additive + its light inside the map's light rules; the kill effects (KILL_FX_LOOPING) loop on
every element, once per ONCE_LOOP_MS, so a carrier sees exactly one round. --selftest plants faults, one per major rule
(the rest are exercised by the live files on every run), and each must be caught BY ITS OWN RULE (the problem must
carry the rule's words).
"""
import argparse
import hashlib
import importlib.util
import json
import math
import pathlib
import re
import sys

sys.dont_write_bytecode = True

import numpy as np                                                    # noqa: E402
from PIL import Image                                                 # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
LUCKY = ROOT / 'tools/lucky/make_fx.py'
DONOR_DIR = HERE / 'donor'
PROVENANCE = DONOR_DIR / 'provenance.json'
PRIVATE = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity')
FX_REL = 'share/raw/fx/tod/wunderstrahl'
PREFIX = 'tod/wunderstrahl/'
GDT_REL = 'source_data/tod2_wunderstrahl_fx.gdt'
TEX_REL = 'model_export/tod_wunderstrahl_fx'
MAX_PATH = 63
MAX_NAME = 63

# ---- LOCKSTEP with the script (test_wunderstrahl.js reads these two lines by regex) -------------------------------------
BEAM_RANGE = 2400
BEAM_LAUNCH_SPEED = 6000
BEAM_RETRACT_SPEED = 10000     # the release: back in the lens within ~0.24 s from the full range ("snaps off")
IMPACT_LOOP_SOUND = 'tod_ws_impact_loop'   # the sound track's alias: the burn-through sizzle while the beam is blocked

# ---- the names (images / materials carry their own "wsfx" prefix: the art track's GDT owns mtl_tod2_ws_* / i_tod2_ws_*) ---
BEAM_1P, BEAM_3P, FLAMETABLE = 'tod2_ws_beam_1p', 'tod2_ws_beam_3p', 'tod2_ws_flametable'
IMG_CORE, IMG_STRAND, IMG_ORB, IMG_BURN = 'i_tod2_wsfx_core', 'i_tod2_wsfx_strand', 'i_tod2_wsfx_orb', 'i_tod2_wsfx_burn'
IMG_CORE_ADD = 'i_tod2_wsfx_core_add'   # the core premultiplied, for the additive stream material
MAT_CORE_1P, MAT_CORE_3P = 'mtl_tod2_wsfx_core_1p', 'mtl_tod2_wsfx_core_3p'
MAT_STRAND, MAT_ORB, MAT_BURN = 'mtl_tod2_wsfx_strand', 'mtl_tod2_wsfx_orb', 'mtl_tod2_wsfx_burn'
MAT_STREAM = 'mtl_tod2_wsfx_stream'   # the flame table's slots: the core image premultiplied, ADDITIVE (brightness 0 adds
                                      # nothing; a blend material at brightness 0 would draw black)
TARGET_EFFECT = 'fx_ws_tip'    # the beam's end in open air (docs/219 said fx_ws_impact: see THE LOOK / TIP above)
IMPACT_DISC_FLAT = True        # the burn disc lies flat on the wall (blockedEffect +X = the surface normal, as the Purifier's
                               # blocked flames splash along the surface); False = a camera-facing burn glow instead, the
                               # safe choice if the first look shows the disc standing out of the wall on grazing hits
KILL_FX_LOOPING = True         # the script's kill effects (zombie burn, disintegrate) ride tod_ability_fx::burst_at - a
                               # tag_origin host the SERVER plays them on and deletes after TOD_WS_BURN/DIE_LIFE. CLAUDE.md:
                               # "server one-shot effects render nothing: use a looping FX on a host"; docs/162's proven lane
                               # is a looping FX on a host. So every element LOOPS, once per ONCE_LOOP_MS, forever: inside
                               # its carrier it fires exactly once (a burst), and the host's delete stops it. False = true
                               # one-shots, for a CLIENT lane (clientfield -> CSC PlayFX: a looping effect there loops until
                               # it is killed)
ONCE_LOOP_MS = 5000            # the kill effects' loop interval: longer than any carrier (+ 1 s), so it never comes round

# ---- budgets / the 1p rule ----------------------------------------------------------------------------------------------
PARTICLE_BUDGET = 64           # peak live particles in ONE effect instance
BEAM_BUDGET = 480              # peak live particles of one beam at full range (every aura instance + origin + impact)
NEAR_MAX = 32                  # the widest sprite that may reach a player's camera unfaded (CLAUDE.md 1p rule)
ONE_P_MAX = 4.0                # the widest sprite (u ACROSS) in the effects that sit ~40 u from the shooter's eye
SIZE_TO_WIDTH = 2.0            # the 1p checks read a size as a RADIUS until a native look settles it (one stock box says
                               # size = width, the elites' preview says radius): the cautious reading
EPS_VEL = 0.08                 # the tiny velocity that orients a strand segment along its helix (u/s; drifts <= 0.25 u)

# ---- colour (linear RGB) ------------------------------------------------------------------------------------------------
WHITE_HOT = (1.0, 0.97, 0.86)
CORE_YELLOW = (1.0, 0.86, 0.36)
GOLD = (1.0, 0.68, 0.16)
GOLD_HOT = (1.0, 0.88, 0.52)
MINOR_TINT = (1.0, 0.94, 0.62)   # the minor strand: pale lemon (a HUE apart from the major's gold, not only dimmer, so the
                                 # two still read apart where HDR saturates both)
AMBER = (1.0, 0.54, 0.12)
ORB_TINT = (1.0, 0.95, 0.80)
MOTE = (1.0, 0.92, 0.62)
SHEATH = (1.0, 0.80, 0.30)
MOLTEN = (1.0, 0.60, 0.16)
EMBER = (1.0, 0.42, 0.10)
BURN_TINT = (1.0, 0.78, 0.40)
IMPACT_GLOW = (1.0, 0.70, 0.26)
FLAME_YELLOW = (1.0, 0.84, 0.46)
SMOKE = (0.26, 0.24, 0.22)       # LIT materials: they read as dark wisps, lit by the effect's own light
SOOT = (0.12, 0.11, 0.10)
ASH = (0.17, 0.16, 0.15)
HEAT_SMOKE = (0.34, 0.32, 0.30)
LIGHT_GOLD = (1.0, 0.80, 0.34)   # the lights' hue (on colorGraph; the light def stays white)
IMPACT_LIGHT = (1.0, 0.70, 0.28)
FLUTTER = [(0, 0), (0.1, 1), (0.3, 0.86), (0.5, 1), (0.7, 0.9), (0.9, 1), (1, 0)]      # crossfade ends kept (every 450 / 500)
FLICKER = [(0, 0), (0.1, 1), (0.22, 0.72), (0.36, 0.98), (0.5, 0.8), (0.64, 1), (0.78, 0.76), (0.9, 1), (1, 0)]
FLAT1 = [(0, 1), (1, 1)]

# ---- THE AURA (the beamEffect) per beam ---------------------------------------------------------------------------------
#   r / pitch: the helix (u); turns: full turns one instance carries (= beamEffectDistance / pitch); segs: strand segments per
#   turn (1p 8: the shooter looks almost down the beam, where 6 straight segments read as a hexagon); speed: beamEffectSpeed
#   (u/s); reach: how far out the swirl lives (u); width: strand thickness; overlap: segment length / its share of the arc;
#   ball: orb sprite (u, halo included); slip: the orbs' axial speed RELATIVE to their instance (u/s, negative = back toward
#   the lens): they slide along their strand, so in the world they spiral outward at speed + slip turning 2 pi slip / pitch
#   rad/s (a point FIXED on a translating helix only moves straight ahead; slipping back also keeps every orb behind its
#   carrier, so none outruns it past a wall); sheath_*: the soft glow on the axis; mote_*: the twinkles; near / sheath_near:
#   the near-camera fade (start, width); fade_in / fade_out: the reach profile (fractions of the swirl's life); alpha: the
#   strands' peak opacity (1p lower: looking down the beam the loops overlap in perspective right beside the crosshair);
#   minor: the second strand's (width, alpha) factors - a MAJOR and a MINOR strand, not two equal ones: two equal strands
#   repeat every half pitch, and at 30 fps the helix moves half of that a frame (they just swap: a strobe); told apart, the
#   pattern repeats only every full pitch, so its motion reads down to 30 fps (and it is richer: a twisted pair)
AURA = {
    '1p': dict(r=2.6, pitch=18.0, turns=2, segs=8, speed=150, reach=280, width=0.5, overlap=1.35, ball=2.0, slip=-40,
               sheath_n=4, sheath_size=11.0, sheath_alpha=0.045, mote_ms=70, mote_size=0.3, alpha=0.6, minor=(0.6, 0.55),
               near=(30, 40), sheath_near=(44, 80), fade_in=0.10, fade_out=0.70),
    '3p': dict(r=4.6, pitch=34.0, turns=2, segs=6, speed=260, reach=600, width=1.0, overlap=1.5, ball=3.6, slip=-60,
               sheath_n=6, sheath_size=16.0, sheath_alpha=0.08, mote_ms=80, mote_size=0.55, alpha=0.9, minor=(0.6, 0.55),
               near=(24, 40), sheath_near=(30, 60), fade_in=0.06, fade_out=0.72),
}
STROBE_FPS = 30                # the lowest frame rate the helix's motion must read at
STROBE_MAX = 0.32              # the most of the pattern's period it may move in one frame
MINOR_TOLD_APART = 0.7         # a minor strand at <= this alpha factor reads as a different strand
ORB_SAMPLES_PER_TURN = 8       # the orbs' orbit curve (piecewise-linear velocity: a full turn sums to zero, no drift)
# ---- THE ORIGIN per beam (sizes in u; the light: radius, intensity) -------------------------------------------------------
ORIGIN = {
    '1p': dict(core=1.0, halo=1.9, halo_alpha=0.2, ring_r=1.5, ring_x=0.9, spark=0.26, spin_hz=2.2, wisp=0.2,
               wisp_speed=150, light_r=100, light_i=150),
    '3p': dict(core=2.2, halo=7.0, halo_alpha=0.26, ring_r=3.0, ring_x=1.6, spark=0.5, spin_hz=2.0, wisp=0.4,
               wisp_speed=240, light_r=160, light_i=300),
}
# ---- THE CORE per beam ------------------------------------------------------------------------------------------------------
#   start_w / end_w: the beam's width at the lens / at maxLength (the texture's profile lights ~45 % of it: the white-hot
#   line ~20 %, the halo out to ~70 %); scale_rgb: the core's brightness - stock beam materials run from 16 (Gorod
#   Krovi's laser trap dlc3_laser_robot_trap, the same profile texture) to 1024 (the lightning beams); 48 / 72 is ~4x the strands
#   (MAT_STRAND 12), so the core is the hottest thing in the beam while the gold swirl keeps its colour;
#   falloff: view-angle falloff, off on both (the stock laser recipe; the texture's profile softens the edges) - and never
#   on the 1p beam: the shooter looks almost DOWN it, where the ribbon is at a grazing angle (77-84 deg from the lens out),
#   so falloff would dim the whole 1p core to its floor
BEAM_SHAPE = 'ribbon'          # the stock laser recipe (see HOW THE ENGINE DRAWS IT)
CORE = {
    '1p': dict(material=MAT_CORE_1P, start_w=0.8, end_w=9.0, repeat=128, scale_rgb=48, falloff=False),
    '3p': dict(material=MAT_CORE_3P, start_w=1.4, end_w=14.0, repeat=192, scale_rgb=72, falloff=BEAM_SHAPE != 'ribbon'),
}                              # (a closed shape's uniform texture wants the falloff for a soft rim; a ribbon's profile has it)
CORE_START_COLOR = (1.0, 0.80, 0.10, 1.0)     # at the lens: a saturated yellow (blue kept low: at scaleRGB 48 / 72 the
                                               # axis still burns white under HDR, the glow round it stays yellow - the
                                               # user's yellow core; lower blue further before cutting brightness)
CORE_END_COLOR = (1.0, 0.68, 0.06, 0.85)      # at maxLength: deeper gold, a little thinner in alpha
CORE_SCROLL_U = -4.5                           # UV/s along the beam (negative = outward if U grows from the lens; flip if
                                               # the shimmer flows into the gun in game)
FALLOFF = (30, 85)                             # view-angle falloff: full below 30 deg, down to FALLOFF_FLOOR at 85 deg
FALLOFF_FLOOR = 0.45
PARTICLE_SCALE_RGB = {MAT_STRAND: 12, MAT_ORB: 16, MAT_BURN: 14, MAT_STREAM: 8}   # the particle materials' brightness knobs

# ---- THE FLAME TABLE's light ----------------------------------------------------------------------------------------------
STREAM_LIGHT_RADIUS = 300
STREAM_LIGHT_FLUTTER = 30
STREAM_LIGHT_RGB = (0.85, 0.62, 0.16)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = load(LUCKY, 'lucky_fx_lib_wunderstrahl')   # the lucky set's helpers + the sky builder (read-only)
S, E = L.S, L.E
spread, xyz, in_world, near_fade, steady = L.spread, L.xyz, L.in_world, L.near_fade, L.steady


def r3(v):
    return round(v, 3)


def r4(v):
    return round(v, 4)


def mix(a, b, k):
    return tuple(r3(a[i] + (b[i] - a[i]) * k) for i in range(3))


# =========================================================================================================================
# THE DONORS (stock; --vendor re-extracts them, provenance.json pins every byte)
# =========================================================================================================================
# efx elements: key -> (stock effect, (visual type, first material))
FX_DONORS = {
    'spark_tail': ('dlc3/stalingrad/fx_raz_dest_weak_point_exp', ('tail', 'gfx_spark_blink_anim_em')),
    'flame':      ('dlc3/stalingrad/fx_raz_dest_weak_point_exp', ('billboardSprite', 'gfx_fire_flame_base_2_anim_em')),
}
# GDT blocks: key -> (private-root relative GDT, asset name, gdf)
BLOCK_DONORS = {
    'beam':       ('source_data/t7_beams.gdt', 'flamethrower_beam', 'beam.gdf'),
    'flametable': ('source_data/zeroy/waw_flamethrower.gdt', 'flame_firstperson', 'flametable.gdf'),
}
# whole files: key -> private-root relative path
FILE_DONORS = {
    'beam.awi': 'deffiles/beam.awi',
    'flametable.awi': 'deffiles/flametable.awi',
}
# the material types we use must exist as techsets in the tools (checked at --vendor, recorded in provenance)
MATERIAL_TYPES = ('effect_lit_scroll_emissive_blend_nocull', 'effect_lit_emissive_add')
TECHSET_DIR = 'share/raw/techsetdefs_stable/effect'


def fx_donor_file(stock):
    return DONOR_DIR / (stock.replace('/', '__') + '.efx')


def block_donor_file(key):
    gdt, name, _ = BLOCK_DONORS[key]
    return DONOR_DIR / ('%s__%s.gdtblock' % (pathlib.Path(gdt).stem, name))


def file_donor_file(key):
    return DONOR_DIR / key


BLOCK_RE = re.compile(r'^\t"([^"]+)" \( "([^"]+)" \)[ \t]*\n\t\{\n(.*?)\n\t\}', re.S | re.M)
FIELD_RE = re.compile(r'^\t\t"([^"]+)" "(.*)"[ \t]*$')


def extract_block(text, name, gdf):
    text = text.replace('\r\n', '\n')
    for m in BLOCK_RE.finditer(text):
        if m.group(1) == name and m.group(2) == gdf:
            return m.group(0) + '\n'
    raise SystemExit('WS FX: block %s (%s) not found' % (name, gdf))


def parse_fields(block_text):
    return [FIELD_RE.match(line).groups() for line in block_text.split('\n') if FIELD_RE.match(line)]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def vendor(force=False):
    DONOR_DIR.mkdir(parents=True, exist_ok=True)
    old = json.loads(PROVENANCE.read_text(encoding='utf-8')) if PROVENANCE.exists() else {}
    prov = {'efx': {}, 'blocks': {}, 'files': {}, 'techsets': {}}

    def guard(kind, key, src_sha):
        if key in old.get(kind, {}) and old[kind][key]['source_sha256'] != src_sha and not force:
            sys.exit('WS FX: the stock %s changed since it was vendored (%s -> %s); review it, then --vendor --force'
                     % (key, old[kind][key]['source_sha256'][:12], src_sha[:12]))

    by_stock = {}
    for key, (stock, want) in FX_DONORS.items():
        by_stock.setdefault(stock, []).append((key, want))
    for stock, wants in sorted(by_stock.items()):
        raw = (PRIVATE / 'share/raw/fx' / (stock + '.efx')).read_bytes()
        guard('efx', stock, sha(raw))
        text = raw.decode('utf-8')
        if 'gfx_debug_missing_fx' in text:
            sys.exit('WS FX: donor %s is a stub (gfx_debug_missing_fx)' % stock)
        fx = E.parse(text)
        take = []
        for key, want in wants:
            idx = next((i for i, e in enumerate(fx.elements) if e.visual[0] == want[0] and e.visual[1] and e.visual[1][0] == want[1]), None)
            if idx is None:
                sys.exit('WS FX: %s has no %s %s element' % (stock, want[0], want[1]))
            take.append((idx, key))
        take.sort()
        body = E.Effect(fx.version, list(fx.header), [fx.elements[i] for i, _ in take]).text()
        fx_donor_file(stock).write_bytes(body.encode('utf-8'))
        prov['efx'][stock] = {'source_sha256': sha(raw), 'vendored_sha256': sha(body.encode('utf-8')),
                              'elements': {key: i for i, key in take}}
    for key, (gdt, name, gdf) in sorted(BLOCK_DONORS.items()):
        raw = (PRIVATE / gdt).read_bytes()
        guard('blocks', key, sha(raw))
        block = extract_block(raw.decode('utf-8', errors='strict'), name, gdf)
        if 'gfx_debug_missing_fx' in block:
            sys.exit('WS FX: donor block %s names a stub' % name)
        block_donor_file(key).write_bytes(block.encode('utf-8'))
        prov['blocks'][key] = {'source': gdt, 'asset': name, 'source_sha256': sha(raw),
                               'vendored_sha256': sha(block.encode('utf-8'))}
    for key, rel in sorted(FILE_DONORS.items()):
        raw = (PRIVATE / rel).read_bytes()
        guard('files', key, sha(raw))
        file_donor_file(key).write_bytes(raw)
        prov['files'][key] = {'source': rel, 'source_sha256': sha(raw), 'vendored_sha256': sha(raw)}
    for mt in MATERIAL_TYPES:
        p = PRIVATE / TECHSET_DIR / (mt + '.techsetdef')
        if not p.exists():
            sys.exit('WS FX: the material type %s has no techset in the tools (%s)' % (mt, p))
        prov['techsets'][mt] = {'source': '%s/%s.techsetdef' % (TECHSET_DIR, mt), 'source_sha256': sha(p.read_bytes())}
    PROVENANCE.write_text(json.dumps(prov, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print('WS FX DONORS VENDORED: %d efx, %d GDT blocks, %d files, %d techsets -> %s'
          % (len(prov['efx']), len(prov['blocks']), len(prov['files']), len(prov['techsets']), DONOR_DIR.relative_to(ROOT)))
    return 0


def donor_problems():
    if not PROVENANCE.exists():
        return ['donor/provenance.json missing - run --vendor']
    prov = json.loads(PROVENANCE.read_text(encoding='utf-8'))
    bad = []
    for stock in sorted({s for s, _ in FX_DONORS.values()}):
        p = fx_donor_file(stock)
        rec = prov.get('efx', {}).get(stock)
        if rec is None or not p.exists():
            bad.append('donor %s missing - run --vendor' % stock)
        elif sha(p.read_bytes()) != rec['vendored_sha256']:
            bad.append('donor %s changed since it was vendored' % stock)
    for key in sorted(BLOCK_DONORS):
        p = block_donor_file(key)
        rec = prov.get('blocks', {}).get(key)
        if rec is None or not p.exists():
            bad.append('donor block %s missing - run --vendor' % key)
        elif sha(p.read_bytes()) != rec['vendored_sha256']:
            bad.append('donor block %s changed since it was vendored' % key)
    for key in sorted(FILE_DONORS):
        p = file_donor_file(key)
        rec = prov.get('files', {}).get(key)
        if rec is None or not p.exists():
            bad.append('donor file %s missing - run --vendor' % key)
        elif sha(p.read_bytes()) != rec['vendored_sha256']:
            bad.append('donor file %s changed since it was vendored' % key)
    for mt in MATERIAL_TYPES:
        if mt not in prov.get('techsets', {}):
            bad.append('material type %s was never verified against the tools - run --vendor' % mt)
    return bad


def register_donors():
    for key, (stock, want) in FX_DONORS.items():
        fx = E.load(fx_donor_file(stock))
        idx = next(i for i, e in enumerate(fx.elements) if e.visual[0] == want[0] and e.visual[1][0] == want[1])
        S.TPL[key] = (str(fx_donor_file(stock)), idx)
        S.EXPECT[key] = want


# =========================================================================================================================
# THE TEXTURES (deterministic math, no RNG: the same pixels on any machine)
# =========================================================================================================================
def _hash2(ix, iy, seed):
    """An integer hash of lattice points -> [0, 1) (exact on every platform)."""
    h = (ix.astype(np.uint64) * np.uint64(374761393) + iy.astype(np.uint64) * np.uint64(668265263)
         + np.uint64(seed) * np.uint64(2246822519)) & np.uint64(0xFFFFFFFF)
    h = ((h ^ (h >> np.uint64(13))) * np.uint64(1274126177)) & np.uint64(0xFFFFFFFF)
    h = h ^ (h >> np.uint64(16))
    return (h & np.uint64(0xFFFFFF)).astype(np.float64) / float(0x1000000)


def _value_noise(u, v, nu, nv, seed):
    """Periodic value noise on the unit square: nu x nv cells, wrapping in both axes."""
    x, y = u * nu, v * nv
    x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = x - x0, y - y0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def h(ix, iy):
        return _hash2(np.mod(ix, nu), np.mod(iy, nv), seed)
    a, b = h(x0, y0), h(x0 + 1, y0)
    c, d = h(x0, y0 + 1), h(x0 + 1, y0 + 1)
    return (a + (b - a) * sx) * (1 - sy) + (c + (d - c) * sx) * sy


def _grid(w, h):
    u = (np.arange(w) + 0.5) / w
    v = (np.arange(h) + 0.5) / h
    return np.meshgrid(u, v)


def _radial(n):
    c = (np.arange(n) + 0.5) / n * 2 - 1
    x, y = np.meshgrid(c, c)
    return np.sqrt(x * x + y * y), np.arctan2(y, x)


def _smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _to_rgba(rgb, alpha):
    out = np.zeros(alpha.shape + (4,), np.uint8)
    out[..., :3] = np.clip(np.rint(np.clip(rgb, 0, 1) * 255), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.rint(np.clip(alpha, 0, 1) * 255), 0, 255).astype(np.uint8)
    return out


def tex_core():
    """The core texture for BEAM_SHAPE: a profile across a ribbon, or uniform across a closed tube."""
    return tex_core_ribbon() if BEAM_SHAPE == 'ribbon' else tex_core_tube()


def tex_core_tube():
    """THE CORE FOR A CLOSED SHAPE (256 along x 32 across): warm white, uniform across V (any wrap of V round the tube reads
    the same), fine longitudinal filaments and a soft shimmer the material scrolls outward. Straight alpha."""
    u, v = _grid(256, 32)
    lum = np.ones_like(u)
    for vc, amp, n, ph in ((0.16, 0.10, 3, 0.1), (0.43, -0.07, 2, 0.6), (0.69, 0.09, 4, 0.3), (0.88, -0.06, 3, 0.8)):
        dv = np.minimum(np.abs(v - vc), 1 - np.abs(v - vc))          # periodic across the tube
        lum += amp * np.exp(-(dv / 0.05) ** 2) * (0.7 + 0.3 * np.cos(2 * np.pi * (u * n + ph)))
    lum += 0.09 * (_value_noise(u, v, 16, 4, 11) - 0.5) + 0.05 * (_value_noise(u, v, 48, 8, 23) - 0.5)
    lum = np.clip(lum, 0.72, 1.16) / 1.16
    base = np.array((1.0, 0.95, 0.80))
    hot = np.array((1.0, 1.0, 0.96))
    k = np.clip((lum - 0.86) / 0.14, 0, 1)[..., None]
    rgb = (base * (1 - k) + hot * k) * (0.82 + 0.18 * lum[..., None])
    alpha = 0.88 + 0.06 * (lum - 0.85)
    return _to_rgba(rgb, alpha)


def tex_core_add():
    """The core texture PREMULTIPLIED (RGB x alpha) for the additive stream material: clear where the core is clear,
    whether the additive pass reads alpha or not (the other additive textures here follow the same convention)."""
    a = tex_core().astype(np.float64) / 255.0
    return _to_rgba(a[..., :3] * a[..., 3:4], a[..., 3])


def tex_core_ribbon():
    """THE CORE (256 along the beam x 64 across): a soft PROFILE ACROSS the ribbon - a white-hot axis (V = 0.5), a warm
    body, a faint halo, clear at both edges - the stock laser texture's shape (fxt_trail_laser, worn by Gorod Krovi's
    ribbon laser trap: 0 at V < 0.15 / > 0.85, 1 on the axis), so the camera-facing ribbon reads as one glowing line with soft
    edges from any side (a texture uniform across V would draw a hard-edged bar). Along U: a steady axis and, in the body,
    faint filaments and a shimmer that the material scrolls outward. Straight alpha (the blend material)."""
    u, v = _grid(256, 64)
    d = np.abs(v - 0.5)                                                # distance from the axis, 0 .. 0.5
    hot = np.exp(-(d / 0.055) ** 2)
    body = np.exp(-(d / 0.15) ** 2)
    halo = 0.30 * np.exp(-(d / 0.27) ** 2)
    shimmer = 1 + 0.10 * (_value_noise(u, v, 16, 4, 11) - 0.5) + 0.06 * (_value_noise(u, v, 48, 8, 23) - 0.5)
    for dc, amp, n, ph in ((0.07, 0.10, 3, 0.1), (-0.09, 0.08, 2, 0.6), (0.11, 0.07, 4, 0.3), (-0.05, 0.06, 5, 0.8)):
        shimmer += amp * np.exp(-((v - 0.5 - dc) / 0.018) ** 2) * (0.5 + 0.5 * np.cos(2 * np.pi * (u * n + ph)))
    taper = 1 - _smoothstep(0.36, 0.5, d)                              # exactly clear at the card's edges
    body_s, halo_s = body * shimmer, halo * shimmer
    alpha = np.clip(0.50 * hot + 0.55 * body_s + halo_s, 0, None)
    alpha = np.clip(alpha / alpha.max(), 0, 1) * taper
    w = np.stack([hot, body_s, halo_s], -1) + 1e-9
    cols = np.array(((1.0, 1.0, 0.97), (1.0, 0.95, 0.80), (1.0, 0.88, 0.62)))
    rgb = (w[..., :, None] * cols).sum(-2) / w.sum(-1, keepdims=True)  # the colour of whichever layer dominates
    rgb = rgb * (0.78 + 0.22 * np.clip(alpha / 0.6, 0, 1))[..., None]  # straight colour: still bright where alpha is low
    return _to_rgba(rgb, alpha)


def tex_strand():
    """THE STRAND SEGMENT (64 x 64): a soft ROUNDED SQUARE (a superellipse, symmetric in both axes, so a 'line' sprite
    stretched along either texture axis shows it the same) with a bright plateau over ~70 % of each axis - stretched into a
    segment, the glow fills most of its length, so overlapping segments join into one continuous strand (a radial dot
    would fill ~35 % and the strand would read as beads). Hot white-gold in the middle, gold to the edges. Additive:
    RGB premultiplied, alpha = I."""
    c = (np.arange(64) + 0.5) / 64 * 2 - 1
    x, y = np.meshgrid(c, c)
    d = (np.abs(x) ** 4 + np.abs(y) ** 4) ** 0.25
    i = (1 - _smoothstep(0.42, 0.98, d)) ** 1.3
    k = (1 - _smoothstep(0.15, 0.80, d))[..., None]
    col = np.array((1.0, 0.64, 0.15)) * (1 - k) + np.array((1.0, 0.94, 0.76)) * k
    return _to_rgba(col * i[..., None], i)


def tex_orb():
    """THE ORB (128 x 128): a white-hot core, a yellow inner glow, an amber halo with a faint energy shell. The bright part
    fills ~45 % of the sprite (a tighter core read no wider than a strand: the balls vanished into the swirl)."""
    rho, _ = _radial(128)
    layers = [
        (np.exp(-(rho / 0.13) ** 2), (1.0, 0.99, 0.94)),
        (0.75 * np.exp(-(rho / 0.26) ** 2), (1.0, 0.86, 0.45)),
        (0.30 * np.exp(-(rho / 0.50) ** 2), (1.0, 0.55, 0.12)),
        (0.10 * np.exp(-((rho - 0.64) / 0.035) ** 2), (1.0, 0.70, 0.30)),
    ]
    edge = 1 - _smoothstep(0.88, 1.0, rho)
    rgb = sum(i[..., None] * np.array(c) for i, c in layers) * edge[..., None]
    alpha = np.clip(sum(i for i, _ in layers) * edge, 0, 1)
    return _to_rgba(rgb, alpha)


def tex_burn():
    """THE BURN-THROUGH (128 x 128): an irregular molten pool (its edge wobbles in angle AND in fine noise, so no two sides
    match), white-hot at the heart, orange-gold to the lip; a few uneven glowing veins wandering out of it (curved, different
    lengths and strengths, one forked), a dull ember-red glaze round it and a scatter of hot specks. Additive."""
    rho, th = _radial(128)
    u = (th + np.pi) / (2 * np.pi)                                       # angle as 0..1 (periodic)
    rag = 1 + 0.22 * (_value_noise(u, rho, 7, 1, 41) - 0.5) + 0.10 * (_value_noise(u, rho, 19, 1, 43) - 0.5)
    for k, (a, p) in enumerate(((0.05, 0.3), (0.03, 1.7), (0.02, 4.1)), start=2):
        rag += a * np.cos(k * th + p)
    heart = np.exp(-(rho / 0.11) ** 2)
    pool = np.clip(1 - (rho / (0.34 * rag)) ** 2, 0, 1) ** 0.6
    glaze = 0.32 * np.clip(1 - (rho / (0.62 * rag)) ** 2, 0, 1) ** 1.5
    veins = np.zeros_like(rho)
    for ang, length, width, gain, bend in ((0.35, 0.80, 0.030, 0.55, 0.9), (1.55, 0.58, 0.024, 0.35, -1.3),
                                           (2.45, 0.70, 0.028, 0.45, 0.6), (3.55, 0.52, 0.020, 0.30, -0.8),
                                           (4.55, 0.76, 0.032, 0.50, 1.2), (5.45, 0.60, 0.022, 0.32, -0.5),
                                           (4.80, 0.50, 0.018, 0.28, -2.0)):       # the last one forks off the fifth
        a_r = ang + bend * np.clip(rho - 0.2, 0, 1) ** 1.5                # a vein curls as it runs out
        d = np.abs(np.angle(np.exp(1j * (th - a_r)))) * np.maximum(rho, 0.05)
        along = np.clip((rho - 0.22) / 0.08, 0, 1) * np.clip((length - rho) / (0.35 * length), 0, 1)
        veins = np.maximum(veins, gain * along * np.exp(-(d / width) ** 2))
    specks = np.clip((_value_noise(u, rho, 64, 24, 47) - 0.86) / 0.14, 0, 1) ** 2 * \
        np.exp(-((rho - 0.5) / 0.18) ** 2) * 0.6
    edge = 1 - _smoothstep(0.86, 1.0, rho)
    layers = [(heart, (1.0, 0.98, 0.86)), (0.9 * pool, (1.0, 0.66, 0.18)), (glaze, (0.85, 0.24, 0.05)),
              (veins, (1.0, 0.52, 0.10)), (specks, (1.0, 0.75, 0.30))]
    rgb = sum(i[..., None] * np.array(c) for i, c in layers) * edge[..., None]
    alpha = np.clip(sum(i for i, _ in layers) * edge, 0, 1)
    return _to_rgba(rgb, alpha)


TEXTURES = {IMG_CORE: tex_core, IMG_CORE_ADD: tex_core_add, IMG_STRAND: tex_strand, IMG_ORB: tex_orb, IMG_BURN: tex_burn}


def tex_path(name):
    return ROOT / TEX_REL / (name + '.png')


# =========================================================================================================================
# ELEMENT HELPERS
# =========================================================================================================================
def el(tkey, name, **kw):
    """The lucky set's el(), minus the water-only / team-only draw flags and element sounds some stock elements carry."""
    e = L.el(tkey, name, **kw)
    if e.has('extraFlags'):
        e.set_flags('extraFlags', remove=('overwaterOnly', 'underwaterOnly', 'teamFriendly', 'teamEnemy'))
    for key in ('elemSpawnSound', 'elemFollowSound'):
        if e.has(key):
            e.get(key).body = []
    return e


def custom(e, material):
    """Wear one of our generated materials (a single image: the first atlas frame, no flipbook)."""
    for it in reversed(e.items):
        if isinstance(it, E.Block) and it.key not in ('elemSpawnSound', 'elemFollowSound'):
            it.body = ['\t\t"%s"' % material]
            break
    for key, val in (('atlasBehavior', 'startFixed'), ('atlasIndex', '0'), ('atlasFps', '0')):
        if e.has(key):
            e.set(key, val)
    return e


def pitch(e, deg):
    """A rotated sprite's facing: pitch 0 faces local X (the surface normal in the impact frame)."""
    e.set('spawnAnglePitch', [deg, 0])
    return e


def zfeather(e, v):
    if e.has('zFeather'):
        e.set('zFeather', v)
    return e


def orbit_samples(turns, per_turn):
    return max(2, int(math.ceil(abs(turns) * per_turn)))


def orbit_speed(rho, turns, life_s, per_turn):
    """The graph scale for `turns` orbits of radius rho in life_s. The engine interpolates the velocity LINEARLY between
    samples dphi apart, which travels (dphi / 2) / tan(dphi / 2) of each arc (0.948 at 8 a turn): scaled up by the
    inverse, every sample point lands back on the circle (measured: 6 % inside without it)."""
    n = orbit_samples(turns, per_turn)
    half = abs(2 * math.pi * turns / n) / 2
    return rho * 2 * math.pi * turns / life_s * (math.tan(half) / half)


def orbit(e, rho, phi0, turns, per_turn=12):
    """Circular motion round local X: `turns` orbits of radius rho over the particle's life, starting at phase phi0."""
    life_s = e.nums('lifeSpanMsec')[0] / 1000.0
    n = orbit_samples(turns, per_turn)
    ys, zs = [], []
    for i in range(n + 1):
        tau = i / n
        ph = phi0 + 2 * math.pi * turns * tau
        ys.append((r4(tau), r4(-math.sin(ph))))
        zs.append((r4(tau), r4(math.cos(ph))))
    speed = r3(orbit_speed(rho, turns, life_s, per_turn))
    S.graph(e, 'velGraph0Y', speed, ys)
    S.graph(e, 'velGraph0Z', speed, zs)
    e.set_flags('editorFlags', add=('useRandVel0',))
    return e


def light_el(name, color, radius, intensity, life, curve=None, every=None, delay=0, org=(0, 0, 0)):
    """One dynamic light (tools/fxgen/elites/make_fx.py light_el): looping (every = interval; two crossfading through their
    overlap) or one-shot (every None: a single light of `life` ms whose intensity is `curve`)."""
    donor = E.load(S.GLOW_DONOR)
    e = [x for x in donor.elements if x.name == 'light_small'][0].copy()
    e.name = name
    e.set_flags('flags', remove=('spawnFrustumCull',))
    e.set('spawnRange', (0, L.LIGHT_RANGE))
    e.set('spawnOrgX', (org[0], 0))
    e.set('spawnOrgY', (org[1], 0))
    e.set('spawnOrgZ', (org[2], 0))
    e.set('spawnDelayMsec', (delay, 0))
    e.set('lifeSpanMsec', (life, 0))
    if every is None:
        e.set_flags('editorFlags', remove=('looping',))
        e.set('spawnLooping', (1, 0))
        e.set('spawnOneShot', (1, 0))
        if curve is None:
            curve = [(0, 0), (0.1, 1), (0.5, 0.6), (1, 0)]
    else:
        e.set('editorFlags', 'looping')
        e.set('spawnLooping', (every, 0))
        if curve is None:
            fade = (life - every) / life
            curve = [(0, 0), (fade, 1), (1 - fade, 1), (1, 0)]
    S.graph(e, 'lightIntensityGraph', intensity, curve)
    S.graph(e, 'lightRadiusGraph', radius, [(0, 1), (1, 1)])
    S.graph(e, 'colorGraph', 1.0, [(0,) + tuple(color), (1,) + tuple(color)])
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
    e.lucky_template = 'light'
    return e


# =========================================================================================================================
# THE AURA (beamEffect: one instance; local X = the beam's forward; it rides outward at the beam's beamEffectSpeed)
# =========================================================================================================================
def aura_dist(key):
    v = AURA[key]
    return v['turns'] * v['pitch']


def aura_life(key):
    """The strands' life (ms): the instance's age when it reaches the swirl's reach."""
    v = AURA[key]
    return int(round(v['reach'] / float(v['speed']) * 1000))


def orb_life(key):
    """An orb's life (ms): it travels at speed + slip in the world, so this maps its own life onto the whole reach."""
    v = AURA[key]
    return int(round(v['reach'] / float(v['speed'] + v['slip']) * 1000))


def helix_point(v, s, j):
    """Strand s (0 / 1, 180 deg apart), sample j (segment centres, segs per turn): position + unit tangent (local frame)."""
    R, P, segs = v['r'], v['pitch'], v['segs']
    th = 2 * math.pi * (j + 0.5) / segs
    ph = th + math.pi * s
    pos = (P * (j + 0.5) / segs, R * math.cos(ph), R * math.sin(ph))
    t = (P / (2 * math.pi), -R * math.sin(ph), R * math.cos(ph))
    n = math.sqrt(sum(c * c for c in t))
    return pos, tuple(c / n for c in t)


def aura(key):
    v = AURA[key]
    T = aura_life(key)
    D = aura_dist(key)
    prof = [(0, 0), (v['fade_in'], 1), (v['fade_out'], 1), (1, 0)]
    arc = math.hypot(v['pitch'], 2 * math.pi * v['r'])
    seg_len = r3(arc / v['segs'] * v['overlap'])
    n = v['turns'] * v['segs']
    els = []
    # the two gold strands: centred segments, each oriented along its helix by a tiny velocity; a hot pulse every 4th
    # segment (phase-shifted between the strands) so the energy reads as flowing while the helix spins outward
    for s in (0, 1):
        wk, ak = (1.0, 1.0) if s == 0 else v['minor']             # the major strand, then the thinner, dimmer minor one
        for j in range(n):
            pos, tan = helix_point(v, s, j)
            hot = 0.5 + 0.5 * math.cos(2 * math.pi * (j / 4.0 + 0.5 * s))
            e = el('ray_thin', 'strand_%d_%02d' % (s, j), oneshot=(1, 0), life=(T, 0), org=tuple(r3(c) for c in pos),
                   size=(r3(v['width'] * wk), [(0, 0.75), (0.3, 1.0), (1, 1.15)]), size1=(seg_len, FLAT1),
                   vel={ax: (r4(EPS_VEL * c), FLAT1) for ax, c in zip('XYZ', tan)},
                   color=mix(GOLD, GOLD_HOT, 0.5 * hot) if s == 0 else mix(MINOR_TINT, WHITE_HOT, 0.3 * hot),
                   alpha=[(t, r3(a * v['alpha'] * ak * (0.80 + 0.20 * hot))) for t, a in prof],
                   run='effect', pivot=(0, 0))
            near_fade(custom(e, MAT_STRAND), *v['near'])
            els.append(e)
    # the little orbs riding the strands: one per strand per turn, each starting ON its strand and SLIPPING back along it
    # (axial `slip` relative to the instance, orbiting at 2 pi slip / pitch so it stays on the strand: in the world a true
    # spiral outward), starting a turn and three-eighths apart so successive orbs sit round the beam, each twinkling on
    # its own phase (the twinkle is folded into the reach profile)
    T_orb = orb_life(key)
    life_s = T_orb / 1000.0
    turns_life = v['slip'] * life_s / v['pitch']
    for s in (0, 1):
        for k in range(v['turns']):
            j = (k * v['segs'] + (k * 3 * v['segs']) // 8 + (v['segs'] // 4 if s else 0)) % (v['turns'] * v['segs'])
            pos, _ = helix_point(v, s, j)
            ph = math.atan2(pos[2], pos[1])
            cyc = 3.2 * life_s
            ph0 = 0.31 * (2 * k + s)
            rows = []
            for i in range(33):
                t = i / 32.0
                base = float(np.interp(t, [p[0] for p in prof], [p[1] for p in prof]))
                rows.append((r4(t), r3(base * (0.72 + 0.28 * math.cos(2 * math.pi * (cyc * t + ph0))))))
            e = el('orb', 'orb_%d_%d' % (s, k), oneshot=(1, 0), life=(T_orb, 0), org=tuple(r3(c) for c in pos),
                   size=(v['ball'], [(0, 0.8), (0.25, 1.0), (1, 1.1)]), vel={'X': (v['slip'], FLAT1)},
                   color=ORB_TINT, alpha=rows, run='effect')
            orbit(e, v['r'], ph, turns_life, ORB_SAMPLES_PER_TURN)
            near_fade(custom(e, MAT_ORB), *v['near'])
            els.append(e)
    # the soft yellow sheath on the axis (overlapping glows: a volumetric halo round the core where the swirl lives)
    for k in range(v['sheath_n']):
        x = D * (k + 0.5) / v['sheath_n']
        e = el('glow', 'sheath_%d' % k, oneshot=(1, 0), life=(T, 0), org=(r3(x), 0, 0),
               size=(v['sheath_size'], [(0, 0.7), (0.3, 1.0), (1, 1.08)]), color=SHEATH,
               alpha=[(t, r3(a * v['sheath_alpha'])) for t, a in prof], run='effect')
        near_fade(e, *v['sheath_near'])
        els.append(e)
    # the twinkling motes: energy dust on a shell round the helix, only while the swirl is at full strength
    start = int(round(v['fade_in'] * T))
    count = max(1, int((int(round(0.85 * T)) - start) // v['mote_ms']))
    e = el('incand', 'motes', loop=(v['mote_ms'], count), life=(300, 80), delay=(start, 0), org=(0, 0, 0),
           org_rand=(r3(D), 0, 0), offset='cylinder', off_r=(r3(v['r'] - 0.7), 1.4),
           size=(v['mote_size'], [(0, 0.4), (0.2, 1.0), (1, 0.3)]), vel=xyz(spread(8)),
           color=[(0,) + MOTE, (1,) + GOLD], alpha=[(0, 0), (0.15, 1), (0.4, 0.45), (0.6, 0.95), (1, 0)], run='effect')
    e.set('spawnOffsetCylindricalAxis', 0)
    near_fade(e, *v['near'])
    els.append(e)
    return els


def aura_1p():
    return aura('1p')


def aura_3p():
    return aura('3p')


# =========================================================================================================================
# THE ORIGIN (looping at tag_flash; local X = the barrel's forward)
# =========================================================================================================================
def origin(key):
    o = ORIGIN[key]
    period = int(round(1000.0 / o['spin_hz']))
    els = [
        el('core_hot', 'hot', loop=(60, 0), life=(120, 0), org=(0.5, 0, 0),
           size=(o['core'], [(0, 0.9), (1, 1.05)], [(0, 0.75), (1, 0.9)]), color=WHITE_HOT, alpha=steady(0.85)),
        el('glow', 'halo', loop=(90, 0), life=(180, 0), org=(0.7, 0, 0), size=(o['halo'], [(0, 0.95), (1, 1.05)]),
           color=CORE_YELLOW, alpha=steady(o['halo_alpha'])),
    ]
    # six gold sparks orbiting the lens: each loops once per orbit with a two-orbit life (two in-step copies, triangle
    # alphas summing to a steady 0.9), so the ring turns smoothly forever
    for k in range(6):
        ph = 2 * math.pi * k / 6
        e = el('incand', 'ring_%d' % k, loop=(period, 0), life=(2 * period, 0),
               org=(o['ring_x'], r3(o['ring_r'] * math.cos(ph)), r3(o['ring_r'] * math.sin(ph))),
               size=(o['spark'], FLAT1), color=GOLD_HOT, alpha=steady(0.9))
        els.append(orbit(e, o['ring_r'], ph, 2))
    els.append(el('incand', 'stream', loop=(55, 0), life=(220, 40), org=(0.8, 0, 0), offset='sphere', off_r=(0.2, 0.3),
                  size=(o['wisp'], [(0, 1), (1, 0.3)]),
                  vel={'X': (o['wisp_speed'], [(0, 0.6), (1, 1.0)], [(0, 0.9), (1, 1.3)]), 'Y': spread(10), 'Z': spread(10)},
                  color=[(0,) + WHITE_HOT, (1,) + GOLD], alpha=[(0, 0), (0.15, 0.9), (1, 0)]))
    els.append(light_el('light', LIGHT_GOLD, radius=o['light_r'], intensity=o['light_i'], life=500, every=450,
                        curve=FLUTTER, org=(2, 0, 0)))
    return els


def origin_1p():
    return origin('1p')


def origin_3p():
    return origin('3p')


# =========================================================================================================================
# THE IMPACT (blockedEffect, looping; local X = out of the surface)
# =========================================================================================================================
def burn_disc():
    """The burn-through on the wall: our burn texture, one fixed orientation (a fresh random rotation on every 100 ms
    respawn would shuffle its veins 10 x a second). Flat on the surface (zFeather 0: it sits 0.5 u off the wall and a
    feather would fade it out) or, with IMPACT_DISC_FLAT False, a camera-facing glow with a soft feather."""
    if IMPACT_DISC_FLAT:
        e = pitch(custom(el('disc', 'burn', loop=(100, 0), life=(200, 0), org=(0.5, 0, 0), size=(12, [(0, 0.96), (1, 1.04)]),
                            color=BURN_TINT, alpha=steady(0.75), spin=((0, 0), (0, 0))), MAT_BURN), 0)
        zfeather(e, 0)
    else:
        e = custom(el('orb', 'burn', loop=(100, 0), life=(200, 0), org=(2.0, 0, 0), size=(12, [(0, 0.96), (1, 1.04)]),
                      color=BURN_TINT, alpha=steady(0.7), spin=((0, 0), (0, 0))), MAT_BURN)
        zfeather(e, 6)
    return near_fade(e, 12, 24)


def impact():
    return [
        near_fade(el('core_hot', 'molten', loop=(40, 0), life=(80, 0), org=(1.2, 0, 0),
                     size=(5.5, [(0, 0.9), (1, 1.05)], [(0, 0.7), (1, 0.85)]), color=WHITE_HOT, alpha=steady(0.9)), 12, 24),
        burn_disc(),
        near_fade(el('glow', 'halo', loop=(90, 0), life=(180, 0), org=(3, 0, 0), size=(24, [(0, 0.95), (1, 1.05)]),
                     color=IMPACT_GLOW, alpha=steady(0.22)), 20, 40),
        el('spark', 'sparks', loop=(40, 0), count=(1, 1), life=(260, 200), org=(1, 0, 0), run='world', offset='sphere',
           off_r=(0.5, 1.0), size=(0.45, [(0, 1), (1, 0.6)]), size1=(7, [(0, 1), (1, 0.35)]),
           vel={'X': (560, [(0, 0.4), (1, 0.25)], [(0, 1), (1, 0.6)]), 'Y': spread(380, 0.6), 'Z': spread(380, 0.6)},
           color=[(0,) + WHITE_HOT, (0.4,) + MOLTEN, (1,) + EMBER], alpha=[(0, 1), (0.6, 0.8), (1, 0)], grav=(55, 15)),
        el('spark_tail', 'droplets', loop=(70, 0), life=(520, 250), org=(1, 0, 0), run='world', size=(1.3, [(0, 1), (1, 0.5)]),
           vel={'X': (300, [(0, 0.4), (1, 0.2)], [(0, 1), (1, 0.6)]), 'Y': spread(240, 0.5), 'Z': spread(240, 0.5)},
           color=[(0,) + WHITE_HOT, (0.5,) + MOLTEN, (1,) + EMBER], alpha=[(0, 1), (0.7, 0.85), (1, 0)], grav=(88, 15)),
        custom(el('orb', 'splash', loop=(110, 0), life=(460, 240), org=(1.5, 0, 0), run='world',
                  size=(1.3, [(0, 1), (1, 0.5)], [(0, 0.75), (1, 0.4)]),
                  vel={'X': (220, [(0, 0.4), (1, 0.25)], [(0, 1), (1, 0.6)]), 'Y': spread(170, 0.6), 'Z': spread(170, 0.6)},
                  color=[(0,) + ORB_TINT, (1,) + GOLD], alpha=[(0, 1), (0.7, 0.8), (1, 0)], grav=(35, 10)), MAT_ORB),
        near_fade(in_world(el('smoke', 'wisp', loop=(150, 0), life=(1100, 300), org=(4, 0, 0), run='world', offset='sphere',
                              off_r=(1.5, 2.5), size=(5, [(0, 0.8), (1, 3.2)]), vel={'X': (18, [(0, 1), (1, 0.3)])},
                              color=SMOKE, alpha=[(0, 0), (0.15, 0.16), (1, 0)]),
                           X=spread(6), Y=spread(6), Z=(34, [(0, 0.6), (1, 0.4)], [(0, 1), (1, 0.7)])), 16, 32),
        light_el('light', IMPACT_LIGHT, radius=210, intensity=450, life=500, every=450, org=(8, 0, 0), curve=FLICKER),
    ]


# =========================================================================================================================
# THE TIP (targetEffect, looping: the beam's end in open air)
# =========================================================================================================================
def tip():
    return [
        el('glow', 'flare', loop=(90, 0), life=(180, 0), size=(9, [(0, 0.95), (1, 1.05)]), color=CORE_YELLOW,
           alpha=steady(0.34)),
        el('core_hot', 'point', loop=(40, 0), life=(80, 0), size=(2.6, [(0, 0.9), (1, 1.05)], [(0, 0.7), (1, 0.85)]),
           color=WHITE_HOT, alpha=steady(0.8)),
        el('incand', 'fizzle', loop=(60, 0), life=(320, 120), run='world', offset='sphere', off_r=(1, 2),
           size=(0.45, [(0, 1), (1, 0.3)]), vel=xyz(spread(70, 0.4)), color=[(0,) + GOLD_HOT, (1,) + GOLD],
           alpha=[(0, 0.9), (1, 0)]),
    ]


# =========================================================================================================================
# THE LENS COOL-DOWN (deathEffect, one-shot at the lens; 1p-safe)
# =========================================================================================================================
def lens_cool():
    return [
        el('glow', 'glow', oneshot=(1, 0), life=(450, 0), org=(0.6, 0, 0), size=(1.9, [(0, 1), (1, 0.55)]),
           color=[(0,) + CORE_YELLOW, (1,) + AMBER], alpha=[(0, 0.4), (0.25, 0.26), (1, 0)]),
        el('core_hot', 'ember', oneshot=(1, 0), life=(280, 0), org=(0.4, 0, 0), size=(0.9, [(0, 1), (1, 0.4)]),
           color=[(0,) + WHITE_HOT, (1,) + AMBER], alpha=[(0, 0.75), (1, 0)]),
        in_world(el('smoke', 'heat', oneshot=(2, 0), life=(800, 150), delay=(40, 100), org=(1.0, 0, 0), run='world',
                    offset='sphere', off_r=(0.2, 0.4), size=(0.9, [(0, 1), (1, 2.2)]), color=HEAT_SMOKE,
                    alpha=[(0, 0), (0.25, 0.11), (1, 0)]),
                 X=spread(3), Y=spread(3), Z=(18, [(0, 0.7), (1, 0.5)], [(0, 1), (1, 0.8)])),
        in_world(el('incand', 'cinders', oneshot=(3, 1), life=(460, 160), delay=(30, 140), org=(0.8, 0, 0), run='world',
                    offset='sphere', off_r=(0.2, 0.5), size=(0.22, [(0, 1), (1, 0.3)]), color=[(0,) + GOLD, (1,) + EMBER],
                    alpha=[(0, 0.9), (1, 0)], grav=(-2, 2)),
                 X=spread(10), Y=spread(10), Z=(12, [(0, 0.3), (1, 0.5)], [(0, 1), (1, 0.8)])),
    ]


# =========================================================================================================================
# THE ZOMBIE HIT + THE DISINTEGRATION (script bursts on a dying carrier; orientation-free: sphere spawns, world velocities)
# =========================================================================================================================
def burst(n, r=0):
    """A kill effect's spawn: n (+ up to r) particles once - a loop that fires once inside its carrier (KILL_FX_LOOPING),
    or a true one-shot."""
    if KILL_FX_LOOPING:
        return {'loop': (ONCE_LOOP_MS, 0), 'count': (n, r)}
    return {'oneshot': (n, r)}


def zombie_burn():
    return [
        near_fade(el('core_hot', 'flash', **burst(1), life=(100, 0), size=(5, [(0, 1), (1, 1.5)]), color=WHITE_HOT,
                     alpha=[(0, 0.9), (1, 0)]), 20, 30),
        in_world(el('spark', 'sparks', **burst(12, 4), life=(220, 160), run='world', offset='sphere', off_r=(1, 2),
                    size=(0.45, [(0, 1), (1, 0.6)]), size1=(6, [(0, 1), (1, 0.35)]),
                    color=[(0,) + WHITE_HOT, (0.4,) + GOLD, (1,) + EMBER], alpha=[(0, 1), (0.6, 0.8), (1, 0)], grav=(50, 15)),
                 X=spread(360, 0.5), Y=spread(360, 0.5), Z=(380, [(0, 0.2), (1, 0.1)], [(0, 1), (1, 0.5)])),
        in_world(el('incand', 'embers', **burst(7, 3), life=(320, 180), run='world', offset='sphere', off_r=(1.5, 2.5),
                    size=(0.8, [(0, 1), (1, 0.25)]), color=[(0,) + MOLTEN, (1,) + EMBER], alpha=[(0, 1), (0.6, 0.7), (1, 0)],
                    grav=(15, 10)),
                 X=spread(120, 0.5), Y=spread(120, 0.5), Z=(160, [(0, 0.35), (1, 0.2)], [(0, 1), (1, 0.6)])),
        near_fade(in_world(el('flame', 'licks', **burst(2, 1), life=(220, 80), run='world', offset='sphere', off_r=(1, 2),
                              size=(3.5, [(0, 0.7), (0.4, 1), (1, 0.8)]), color=FLAME_YELLOW,
                              alpha=[(0, 0.85), (0.6, 0.5), (1, 0)]),
                           Z=(40, [(0, 1), (1, 0.6)])), 20, 30),
        near_fade(in_world(el('smoke', 'puff', **burst(2, 1), life=(420, 100), delay=(30, 40), run='world', offset='sphere',
                              off_r=(1, 2), size=(5, [(0, 0.8), (1, 2.6)]), color=SOOT, alpha=[(0, 0.22), (1, 0)]),
                           X=spread(10), Y=spread(10), Z=(30, [(0, 0.8), (1, 0.5)])), 20, 40),
    ]


DIE_LIGHT = dict(radius=180, intensity=420, life=220)   # the kill's light flash (small and short: a beam through a crowd
                                                        # can kill several a second; past a few the script plays _nl)


def disintegrate(light=True):
    els = [
        near_fade(el('glow', 'flash', **burst(1), life=(170, 0), size=(34, [(0, 0.8), (0.3, 1), (1, 1.2)]),
                     color=CORE_YELLOW, alpha=[(0, 0.85), (0.4, 0.5), (1, 0)]), 40, 70),
        near_fade(el('core_hot', 'pop', **burst(1), life=(140, 0), size=(16, [(0, 1), (1, 0.55)]), color=WHITE_HOT,
                     alpha=[(0, 1), (1, 0)]), 30, 50),
        near_fade(el('ring', 'shock', **burst(1), life=(260, 0), size=(48, [(0, 0.15), (0.4, 0.75), (1, 1)]),
                     color=CORE_YELLOW, alpha=[(0, 0.6), (0.5, 0.35), (1, 0)]), 32, 60),
        in_world(el('incand', 'embers', **burst(22, 6), life=(650, 300), run='world', offset='sphere', off_r=(3, 6),
                    size=(1.0, [(0, 1), (0.6, 0.7), (1, 0.25)]), color=[(0,) + WHITE_HOT, (0.35,) + MOLTEN, (1,) + EMBER],
                    alpha=[(0, 1), (0.6, 0.75), (1, 0)], grav=(38, 15)),
                 X=spread(520, 0.4), Y=spread(520, 0.4), Z=(420, [(0, 0.3), (1, 0.15)], [(0, 1), (1, 0.5)])),
        custom(in_world(el('orb', 'orbs', **burst(7, 2), life=(650, 250), run='world', offset='sphere', off_r=(2, 4),
                           size=(1.6, [(0, 1), (1, 0.4)]), color=[(0,) + ORB_TINT, (1,) + GOLD],
                           alpha=[(0, 1), (0.7, 0.8), (1, 0)], grav=(25, 10)),
                        X=spread(340, 0.5), Y=spread(340, 0.5), Z=(260, [(0, 0.3), (1, 0.2)], [(0, 1), (1, 0.6)])), MAT_ORB),
        near_fade(in_world(el('smoke', 'ash', **burst(6, 2), life=(1300, 350), delay=(30, 60), run='world', offset='sphere',
                              off_r=(6, 10), size=(16, [(0, 0.6), (0.3, 1), (1, 2.4)]), color=ASH,
                              alpha=[(0, 0.4), (0.4, 0.28), (1, 0)]),
                           X=spread(40, 0.3), Y=spread(40, 0.3), Z=(60, [(0, 0.35), (1, 0.15)], [(0, 1), (1, 0.4)])), 32, 64),
    ]
    if light:
        els.append(light_el('light', IMPACT_LIGHT, curve=[(0, 0), (0.08, 1), (0.45, 0.4), (1, 0)],
                            every=ONCE_LOOP_MS if KILL_FX_LOOPING else None, **DIE_LIGHT))
    return els


def disintegrate_nl():
    """The same disintegration without its light: the script's choice once kills come faster than the lights should."""
    return disintegrate(light=False)


# ---- the table: name -> (builder, LOOPING?, bounding box lo, hi, can play at a face?, strict 1p?, max length ms) -------------
def _box(lo, hi):
    return (tuple(lo), tuple(hi))


def aura_box(key, side):
    """The instance's box: its D-long piece of helix, plus the orbs slipping back behind it (|slip| x life) - outside the
    box an orb would be culled whenever the instance's own box left the view."""
    v = AURA[key]
    back = abs(v['slip']) * orb_life(key) / 1000.0
    return _box((-(back + 10), -side, -side), (aura_dist(key) + 10, side, side))


EFFECTS = {
    'fx_ws_origin_1p':    (origin_1p, True, *_box((-8, -12, -12), (64, 12, 12)), True, True, None),
    'fx_ws_origin_3p':    (origin_3p, True, *_box((-12, -20, -20), (104, 20, 20)), True, False, None),
    'fx_ws_aura_1p':      (aura_1p, False, *aura_box('1p', 12), True, False, max(aura_life('1p'), orb_life('1p')) + 400),
    'fx_ws_aura_3p':      (aura_3p, False, *aura_box('3p', 18), True, False, max(aura_life('3p'), orb_life('3p')) + 400),
    'fx_ws_impact':       (impact, True, *_box((-80, -600, -600), (600, 600, 600)), True, False, None),
    'fx_ws_tip':          (tip, True, *_box((-80, -80, -80), (80, 80, 80)), False, False, None),
    'fx_ws_lens_cool':    (lens_cool, False, *_box((-20, -30, -30), (40, 30, 60)), True, True, 1200),
    'fx_ws_zombie_burn':  (zombie_burn, False, *_box((-180, -180, -180), (180, 180, 220)), True, False, 600),
    'fx_ws_disintegrate': (disintegrate, False, *_box((-420, -420, -420), (420, 420, 460)), True, False, 2200),
    'fx_ws_disintegrate_nl': (disintegrate_nl, False, *_box((-420, -420, -420), (420, 420, 460)), True, False, 2200),
}
NAMES = list(EFFECTS)
STRICT_1P_AURA = 'fx_ws_aura_1p'
# the script's bursts on a dying carrier: with KILL_FX_LOOPING every element loops once per ONCE_LOOP_MS (see the switch)
ONCE_EFFECTS = {'fx_ws_zombie_burn', 'fx_ws_disintegrate', 'fx_ws_disintegrate_nl'} if KILL_FX_LOOPING else set()

# ---- LOCKSTEP (optional): the script plays the two one-shots on a tod_ability_fx::burst_at carrier that lives this long;
# when the script is in the tree (the --out-root stage first, then the repo) each effect must end inside its carrier
SCRIPT_REL = 'scripts/zm/zm_tod2_cybercity/_tod_wunderstrahl.gsc'
CARRIERS = {'fx_ws_zombie_burn': 'TOD_WS_BURN_LIFE', 'fx_ws_disintegrate': 'TOD_WS_DIE_LIFE',
            'fx_ws_disintegrate_nl': 'TOD_WS_DIE_LIFE'}
CARRIER_MARGIN_MS = 50         # one server frame of slack


def carrier_limits(out_root):
    """{effect: ms} from the script's carrier lives, or {} when the script (or a define) is not in the tree yet."""
    for base in (out_root, ROOT):
        p = base / SCRIPT_REL
        if p.exists():
            text = p.read_text(encoding='utf-8', errors='replace')
            out = {}
            for fx, define in CARRIERS.items():
                m = re.search(r'#define\s+%s\s+([\d.]+)' % define, text)
                if m:
                    out[fx] = int(round(float(m.group(1)) * 1000)) - CARRIER_MARGIN_MS
            return out
    return {}


def apply_carriers(meta, limits):
    for fx, ms in limits.items():
        if fx in meta:
            meta[fx]['limit'] = ms if meta[fx]['limit'] is None else min(meta[fx]['limit'], ms)


def build_fx():
    register_donors()
    out, meta = {}, {}
    for name, (fn, looping, lo, hi, face, strict, limit) in EFFECTS.items():
        out[name] = S.effect(fn(), lo, hi)
        meta[name] = dict(looping=looping, face=face, strict=strict, limit=limit, once=name in ONCE_EFFECTS)
    return out, meta


# =========================================================================================================================
# THE GDT (the beams, the flame table, the materials, the images)
# =========================================================================================================================
def fx_ref(name):
    return 'tod\\\\wunderstrahl\\\\%s.efx' % name           # the stock GDT spelling: tod\\wunderstrahl\\<name>.efx


def color4(c):
    return ' '.join(E.fmt(x) for x in c)


def beam_fields(key):
    c, a = CORE[key], AURA[key]
    over = {
        'material': c['material'], 'beamShape': BEAM_SHAPE, 'beamShapeRotation': '0', 'beamShapeHorizontalScale': '1',
        'beamShapeVerticalScale': '1', 'curveType': 'smooth', 'numSegments': '24', 'uvMode': 'repeating horizontal',
        'textureRepeatLength': str(c['repeat']), 'msecAnimLoopTime': '1000',
        'startWidth': E.fmt(c['start_w']), 'endWidth': E.fmt(c['end_w']),
        'startColor': color4(CORE_START_COLOR), 'endColor': color4(CORE_END_COLOR),
        'maxLength': str(BEAM_RANGE), 'useVirtualTarget': '1', 'virtualTargetDistance': str(BEAM_RANGE),
        'virtualTargetMass': '0', 'dieIfTooLong': '0', 'beamAffectedByGravity': '0', 'beamGravity': '0',
        'beamInitialSpeed': '0', 'collisionMode': 'nodes', 'collisionMask': 'shot and not body', 'dieIfBlocked': '0',
        'launchSpeed': str(BEAM_LAUNCH_SPEED), 'leadoutDistance': '0', 'leadinDistance': '0', 'breakAngle': '0',
        'retractSpeed': str(BEAM_RETRACT_SPEED), 'reverseRetract': '0',
        'originEffect': fx_ref('fx_ws_origin_' + key), 'beamEffect': fx_ref('fx_ws_aura_' + key),
        'beamEffectDistance': E.fmt(aura_dist(key)), 'beamEffectSpeed': str(a['speed']),
        'targetEffect': fx_ref(TARGET_EFFECT), 'blockedEffect': fx_ref('fx_ws_impact'),
        'blockedEffectSound': IMPACT_LOOP_SOUND, 'unblockedEffectSound': '', 'deathEffect': fx_ref('fx_ws_lens_cool'),
        'drawPerpendicularCard': '0', 'perpendicularMaterial': '',
        'slackStartTimeMsec': '0', 'slackEaseInTimeMsec': '0', 'slackDurationMsec': '0', 'slackEaseOutTimeMsec': '0',
        'slackLoopMode': 'Loop Slack', 'slackMinSlack': '0',
    }
    # a rigid, straight laser: every wave off
    for wave in ('sine', 'sawtooth', 'square', 'triangle'):
        for f in ('AmplitudeX', 'AmplitudeY', 'WeightStart', 'WeightMid', 'WeightEnd'):
            over[wave + f] = '0'
    return over


FLAMETABLE_MATERIAL_SLOTS = ('fire', 'smoke', 'drips', 'streamFuel', 'streamFuel2', 'streamFlames', 'streamFlames2')
FLAMETABLE_SOUNDS = ('flameOffLoopSound', 'flameIgniteSound', 'flameOnLoopSound', 'flameCooldownSound')


def flametable_fields():
    over = {'name': FLAMETABLE, 'heat': ''}
    for slot in FLAMETABLE_MATERIAL_SLOTS:
        over[slot] = MAT_STREAM                      # the laser core's image, additive: anything that does draw reads as a
                                                     # thin yellow thread, and brightness 0 adds nothing (never a black quad)
    for snd in FLAMETABLE_SOUNDS:
        over[snd] = ''                               # the weapon's loopFire* lane owns the audio (no doubled loop)
    fv = {
        # the stream: tiny, straight, sparse, short - it exists only to carry the light
        'streamChunkGravityStart': 0, 'streamChunkGravityEnd': 0, 'streamChunkStartSize': 1, 'streamChunkEndSize': 1,
        'streamChunkStartSizeRand': 0, 'streamChunkEndSizeRand': 0, 'streamChunkMaxSize': 1,
        'streamChunkSizeSpeedScale': 0, 'streamChunkSizeAgeScale': 0, 'streamChunkDistScalar': 10,
        'streamChunkDistSwayScale': 1, 'streamChunkDistSwayVelMax': 24, 'streamChunkSpeed': 2000, 'streamChunkDecel': 0,
        'streamChunkVelocityAddScale': 1, 'streamChunkDuration': 0.5, 'streamChunkDurationScaleMaxVel': 500,
        'streamChunkDurationVelScalar': 0, 'streamChunkSpawnFireIntervalStart': 5, 'streamChunkSpawnFireIntervalEnd': 5,
        'streamChunkSpawnFireMinLifeFrac': 1, 'streamChunkSpawnFireMaxLifeFrac': 0.1,      # an empty fire window
        'streamChunkFireMinLifeFrac': 0, 'streamChunkFireMinLifeFracStart': 0, 'streamChunkFireMinLifeFracEnd': 0,
        'streamChunkDripsMinLifeFrac': 0, 'streamChunkDripsMinLifeFracStart': 0, 'streamChunkDripsMinLifeFracEnd': 1,
        'streamChunkRotationRange': 0, 'streamSizeRandSinWave': 0.1, 'streamSizeRandCosWave': 0.1,
        'streamDripsChunkInterval': 1, 'streamDripsChunkMinFrac': 1, 'streamDripsChunkRandFrac': 0,
        'streamSmokeChunkInterval': 1, 'streamSmokeChunkMinFrac': 1, 'streamSmokeChunkRandFrac': 0,
        'streamChunkCullMinLife': 0, 'streamChunkCullMaxLife': 1, 'streamChunkCullDistSizeFrac': 3,
        'streamFuelSizeStart': 0.1, 'streamFuelSizeEnd': 0.1, 'streamFuelLength': 0.01, 'streamFuelNumSegments': 1,
        'streamFuelAnimLoopTime': 1, 'streamFlameSizeStart': 0.1, 'streamFlameSizeEnd': 0.1, 'streamFlameLength': 0.01,
        'streamFlameNumSegments': 1, 'streamFlameAnimLoopTime': 1,
        # the light that travels with the stream
        'streamPrimaryLightRadius': STREAM_LIGHT_RADIUS, 'streamPrimaryLightRadiusFlutter': STREAM_LIGHT_FLUTTER,
        'streamPrimaryLightR': STREAM_LIGHT_RGB[0], 'streamPrimaryLightG': STREAM_LIGHT_RGB[1],
        'streamPrimaryLightB': STREAM_LIGHT_RGB[2], 'streamPrimaryLightFlutterR': 0.05,
        'streamPrimaryLightFlutterG': 0.04, 'streamPrimaryLightFlutterB': 0.02,
        # fire / drips / smoke: dark, minimal, motionless
        'fireLife': 0.1, 'fireLifeRand': 0, 'fireSpeedScale': 0, 'fireSpeedScaleRand': 0, 'fireVelocityAddZ': 0,
        'fireVelocityAddZRand': 0, 'fireVelocityAddSideways': 0, 'fireGravity': 0, 'fireGravityEnd': 0,
        'fireMaxRotVel': 0, 'fireFriction': 0, 'fireEndSizeAdd': 0, 'fireStartSizeScale': 0.1, 'fireEndSizeScale': 0,
        'fireBrightness': 0,
        'dripsLife': 0.1, 'dripsLifeRand': 0, 'dripsSpeedScale': 0, 'dripsSpeedScaleRand': 0, 'dripsVelocityAddZ': 0,
        'dripsVelocityAddZRand': 0, 'dripsVelocityAddSideways': 0, 'dripsGravity': 0, 'dripsGravityEnd': 0,
        'dripsMaxRotVel': 0, 'dripsFriction': 0, 'dripsEndSizeAdd': 0, 'dripsStartSizeScale': 0.1,
        'dripsEndSizeScale': 0, 'dripsBrightness': 0,
        'smokeLife': 0.1, 'smokeLifeRand': 0.1, 'smokeSpeedScale': 0, 'smokeVelocityAddZ': 0, 'smokeGravity': 0,
        'smokeGravityEnd': 0, 'smokeMaxRotation': 0, 'smokeMaxRotVel': 0, 'smokeFriction': 0, 'smokeEndSizeAdd': 0,
        'smokeStartSizeAdd': 0, 'smokeOriginSizeOfsZScale': 0, 'smokeOriginOfsZ': 0, 'smokeFadein': 0,
        'smokeFadeout': 1, 'smokeMaxAlpha': 0, 'smokeBrightness': 0, 'smokeOriginOffset': 0,
        'collisionSpeedScale': 0.5, 'collisionVolumeScale': 0.25,
    }
    for k, v in fv.items():
        over['flameVar_' + k] = E.fmt(float(v))
    return over


def core_material(key):
    c = CORE[key]
    return [
        ('materialCategory', 'Effect'), ('materialType', 'effect_lit_scroll_emissive_blend_nocull'),
        ('template', 'material.template'), ('surfaceType', '<none>'), ('colorMap', IMG_CORE), ('colorTint', '1 1 1 1'),
        ('scaleRGB', str(c['scale_rgb'])), ('useOldHDRScale', '0'), ('alphaRevealMap', '$white_reveal'),
        ('flickerLookupMap', '$white_reveal'), ('colorDetailScaleX', '1'), ('colorDetailScaleY', '1'),
        ('detailScaleX', '1'), ('detailScaleY', '1'), ('gSharedU_Scale00', '1'), ('gSharedV_Scale00', '1'),
        ('gUVScroll00_Angle', E.fmt(CORE_SCROLL_U)), ('gUVScroll01_Angle', '0'), ('gUVScroll02_Angle', '0'),
        ('gUVScroll03_Angle', '0'), ('uScroll', '0'), ('vScroll', '0'), ('uScroll1', '0'), ('vScroll1', '0'),
        ('uvScrollAngle', '0'), ('uvRotationRate', '0'), ('uvScrollAngle1', '0'), ('uvRotationRate1', '0'),
        ('falloff', '1' if c['falloff'] else '0'), ('falloffBeginAngle', str(FALLOFF[0])), ('falloffEndAngle', str(FALLOFF[1])),
        ('falloffBeginColor', '1 1 1 1'), ('falloffEndColor', color4((FALLOFF_FLOOR,) * 4)),
        ('distFalloff', '0'), ('zFeatherOverride', '0'), ('textureAtlasRowCount', '1'), ('textureAtlasColumnCount', '1'),
        ('cullFace', 'None'), ('usage', '<not in editor>'),
    ]


def particle_material(name, image):
    return [
        ('materialCategory', 'Effect'), ('materialType', 'effect_lit_emissive_add'), ('template', 'material.template'),
        ('surfaceType', '<none>'), ('colorMap', image), ('colorTint', '1 1 1 1'),
        ('scaleRGB', str(PARTICLE_SCALE_RGB[name])), ('useOldHDRScale', '0'), ('alphaRevealMap', '$white_reveal'),
        ('falloff', '0'), ('distFalloff', '0'), ('textureAtlasRowCount', '1'), ('textureAtlasColumnCount', '1'),
        ('cullFace', 'None'), ('usage', '<not in editor>'),
    ]


def image_fields(name):
    return [
        ('baseImage', '%s/%s.png' % (TEX_REL, name)), ('imageType', 'Texture'), ('semantic', 'effectMap'),
        ('coreSemantic', 'sRGB3chAlpha'), ('streamable', '0'), ('compressionMethod', 'compressed high color'),
    ]


def from_template(key, over):
    fields = parse_fields(block_donor_file(key).read_text(encoding='utf-8'))
    have = {k for k, _ in fields}
    missing = sorted(set(over) - have)
    if missing:
        raise SystemExit('WS FX: %s overrides name fields the stock template lacks: %s' % (key, ', '.join(missing)))
    return [(k, over.get(k, v)) for k, v in fields]


def gdt_blocks():
    blocks = []
    for img in (IMG_CORE, IMG_CORE_ADD, IMG_STRAND, IMG_ORB, IMG_BURN):
        blocks.append((img, 'image.gdf', image_fields(img)))
    blocks.append((MAT_CORE_1P, 'material.gdf', core_material('1p')))
    blocks.append((MAT_CORE_3P, 'material.gdf', core_material('3p')))
    blocks.append((MAT_STRAND, 'material.gdf', particle_material(MAT_STRAND, IMG_STRAND)))
    blocks.append((MAT_ORB, 'material.gdf', particle_material(MAT_ORB, IMG_ORB)))
    blocks.append((MAT_BURN, 'material.gdf', particle_material(MAT_BURN, IMG_BURN)))
    blocks.append((MAT_STREAM, 'material.gdf', particle_material(MAT_STREAM, IMG_CORE_ADD)))
    blocks.append((BEAM_1P, 'beam.gdf', from_template('beam', beam_fields('1p'))))
    blocks.append((BEAM_3P, 'beam.gdf', from_template('beam', beam_fields('3p'))))
    blocks.append((FLAMETABLE, 'flametable.gdf', from_template('flametable', flametable_fields())))
    return blocks


def emit_gdt(blocks):
    out = ['{']
    for name, gdf, fields in blocks:
        out.append('\t"%s" ( "%s" )' % (name, gdf))
        out.append('\t{')
        for k, v in fields:
            out.append('\t\t"%s" "%s"' % (k, v))
        out.append('\t}')
    out.append('}')
    return '\n'.join(out) + '\n'


# =========================================================================================================================
# VALIDATION - the effects
# =========================================================================================================================
def _whole(vals):
    return all(abs(v - round(v)) < 1e-9 for v in vals)


def alive_at(e, age):
    """Particles of element e alive at effect time `age` ms (max counts; one-shots and finite / forever loops)."""
    d0 = sum(e.nums('spawnDelayMsec'))
    life = sum(e.nums('lifeSpanMsec'))
    if 'looping' in e.flags('editorFlags'):
        interval, count = e.nums('spawnLooping')
        per = max(1, int(sum(e.nums('spawnLoopingSpawnCount'))))
        interval = max(1.0, interval)
        n = 0
        k_hi = math.floor((age - d0) / interval) if age >= d0 else -1
        k_lo = math.ceil((age - life - d0) / interval) if age - life >= d0 else 0
        if count > 0:
            k_hi = min(k_hi, int(count) - 1)
        if k_hi >= k_lo:
            n = (k_hi - k_lo + 1) * per
        return n
    if d0 <= age < d0 + life:
        return int(sum(e.nums('spawnOneShot')))
    return 0


def peak_particles(e):
    life = sum(e.nums('lifeSpanMsec'))
    if 'looping' in e.flags('editorFlags'):
        interval, count = e.nums('spawnLooping')
        per = max(1, int(sum(e.nums('spawnLoopingSpawnCount'))))
        alive = math.ceil(life / max(1.0, interval))
        if count > 0:
            alive = min(alive, count)
        return int(alive * per)
    return int(sum(e.nums('spawnOneShot')))


def end_ms(e):
    delay = sum(e.nums('spawnDelayMsec'))
    life = sum(e.nums('lifeSpanMsec'))
    if 'looping' in e.flags('editorFlags'):
        interval, count = e.nums('spawnLooping')
        if count <= 0:
            return math.inf
        return delay + interval * count + life
    return delay + life


def widest(e):
    g0 = e.graph('sizeGraph0')
    w = g0.scale * max(row[1] for c in g0.curves for row in c)
    if 'nonUniformScale' in e.flags('flags'):
        g1 = e.graph('sizeGraph1')
        w = max(w, g1.scale * max(row[1] for c in g1.curves for row in c))
    return w


GENERATED_MATERIALS = (MAT_CORE_1P, MAT_CORE_3P, MAT_STRAND, MAT_ORB, MAT_BURN)


def allowed_materials():
    ok = set(GENERATED_MATERIALS)
    for want in S.EXPECT.values():
        ok.add(want[1])
    for _, want in FX_DONORS.values():
        ok.add(want[1])
    ok.add('gfx_fire_flame_base_1_anim_em')      # the flame donor's second flipbook (the elites' Mangler ships it)
    ok.update(('gfx_fog_slow_lg_anim_lit', 'gfx_fog_slow_md_anim_lit'))   # the smoke template's other two sizes
    return ok


def validate_fx(name, text, meta):
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
    if not any(ln.strip().startswith('efFlags') and 'efUseBoundingBox' in ln for ln in fx.header):
        bad.append(name + ': no bounding box')
    okmat = allowed_materials()
    seen, total, last = set(), 0, 0
    for e in fx.elements:
        en = name + '/' + e.name
        if e.name in seen:
            bad.append(en + ': a second element with this name')
        seen.add(e.name)
        t, mats = e.visual
        if t == 'model':
            bad.append(en + ': a model element')
        elif t == 'runner' or 'playAttached' in e.flags('editorFlags') or any(
                e.has(k) and e.get(k).strip().strip('"') for k in ('attachment', 'fxOnDeath', 'fxOnImpact', 'emission')):
            bad.append(en + ': names a child effect (this set has none)')
        elif t in L.LIGHTS:
            body = ' '.join(m.strip() for m in mats)
            if 'shadowUpdate Never' not in body or 'PRIMARY_NOSHADOWMAP 1' not in body:
                bad.append(en + ': a light that casts shadows')
            if not all(('lightingstate%d 1' % k) in body for k in (1, 2, 3, 4)):
                bad.append(en + ': a light missing from a lighting state')
            ig, rg = e.graph('lightIntensityGraph'), e.graph('lightRadiusGraph')
            peak_r = rg.scale * max(row[1] for cc in rg.curves for row in cc)
            peak_i = ig.scale * max(row[1] for cc in ig.curves for row in cc)
            if not (0 < peak_i and 0 < peak_r <= L.LIGHT_RADIUS_MAX):
                bad.append('%s: light intensity %s / radius %s (radius 1..%d)' % (en, peak_i, peak_r, L.LIGHT_RADIUS_MAX))
            if peak_particles(e) > 2:
                bad.append('%s: %d lights alive at once (at most two, crossfading)' % (en, peak_particles(e)))
            for cc in ig.curves:
                ts = [row[0] for row in cc]
                if ts[0] != 0 or ts[-1] != 1 or any(b <= a for a, b in zip(ts, ts[1:])):
                    bad.append(en + ': the light curve is not 0..1 strictly increasing in time')
                    break
        elif t not in L.VISUAL or not mats:
            bad.append(en + ': draws nothing')
        if t not in L.LIGHTS:
            for m in mats:
                if m not in okmat:
                    bad.append('%s: material %s is neither ours nor a proven template material' % (en, m))
        if 'gfx_debug_missing_fx' in mats:
            bad.append(en + ': a stub material')
        for key in ('lifeSpanMsec', 'spawnDelayMsec', 'spawnLooping'):
            if not _whole(e.nums(key)):
                bad.append(en + ': fractional ' + key)
        edf = e.flags('editorFlags')
        if meta.get('once'):
            # a burst on a dying carrier: every element loops (the server's looping lane), once per ONCE_LOOP_MS, forever
            if 'looping' not in edf:
                bad.append(en + ': a one-shot element in a carrier-looped kill effect (every element loops, so the server '
                                'lane keeps the effect; KILL_FX_LOOPING)')
            else:
                interval, count = e.nums('spawnLooping')
                room = (meta['limit'] or 0) + 1000
                if count != 0 or interval < max(ONCE_LOOP_MS, room):
                    bad.append('%s: loops every %s ms for %s loops - it would respawn before its carrier dies (want every '
                               '>= %d ms, forever)' % (en, interval, count, max(ONCE_LOOP_MS, room)))
        elif 'looping' in edf:
            interval, count = e.nums('spawnLooping')
            if interval < 1 or count < 0:
                bad.append('%s: looping every %s ms for %s loops' % (en, interval, count))
            if count == 0 and not meta['looping']:
                bad.append(en + ': loops forever inside a ONE-SHOT timeline (it would never end)')
        for key in ('elemSpawnSound', 'elemFollowSound'):
            if e.has(key) and any(line.strip() for line in e.get(key).body):
                bad.append(en + ': names a sound (' + key + ')')
        if t not in L.LIGHTS and e.nums('spawnRange')[1] < S.FAR:
            bad.append(en + ': spawn range under %d' % S.FAR)
        if any(e.nums('fadeInRange')):
            bad.append(en + ': a far fade-in range')
        fl = e.flags('flags')
        if 'spawnFrustumCull' in fl or 'useCollision' in fl or 'isMatureContent' in fl:
            bad.append(en + ': frustum-culled / collides / mature-only')
        if e.has('extraFlags') and any(f in e.flags('extraFlags') for f in ('overwaterOnly', 'underwaterOnly', 'teamFriendly', 'teamEnemy')):
            bad.append(en + ': draws only over/under water or for one team')
        for it in e.items:
            if isinstance(it, E.Graph):
                if not math.isfinite(it.scale) or any(not math.isfinite(v) for cc in it.curves for row in cc for v in row):
                    bad.append('%s: %s is not finite' % (en, it.key))
                if it.key == 'alphaGraph' and any(not (0 <= row[1] * it.scale <= 1) for cc in it.curves for row in cc):
                    bad.append(en + ': alpha outside 0..1')
                if it.key in ('sizeGraph0', 'sizeGraph1') and any(row[1] * it.scale < 0 for cc in it.curves for row in cc):
                    bad.append('%s: negative %s' % (en, it.key))
                if len(it.curves[0]) > 64:
                    bad.append('%s: %s has %d points (stock tops out near 81; keep <= 64)' % (en, it.key, len(it.curves[0])))
        # THE 1P RULE (the strict checks read a size as a radius: SIZE_TO_WIDTH x the size is the width across)
        sprite = t in ('billboardSprite', 'orientedSprite', 'rotatedSprite', 'line', 'tail')
        if sprite:
            w = widest(e)
            across = r3(w * SIZE_TO_WIDTH)
            start, width = e.nums('fadeOutRange')
            if meta['face'] and w > NEAR_MAX and (start < 24 or width <= 0):
                bad.append('%s: a %g-unit sprite with no near-camera fade (the 1p rule)' % (en, w))
            if meta['strict'] and across > ONE_P_MAX:
                bad.append('%s: a sprite up to %g u across in an effect at the shooter\'s eye (> %g, the 1p rule)'
                           % (en, across, ONE_P_MAX))
            if name == STRICT_1P_AURA and across > ONE_P_MAX and (start < 30 or width <= 0):
                bad.append('%s: a sprite up to %g u across in the 1p aura with no near-camera fade from 30 u' % (en, across))
        if name.endswith('_nl') and t in L.LIGHTS:
            bad.append(en + ': a light in a no-light (_nl) variant')
        total += peak_particles(e)
        if meta.get('once'):                     # only the first round lands inside the carrier
            last = max(last, sum(e.nums('spawnDelayMsec')) + sum(e.nums('lifeSpanMsec')))
        else:
            last = max(last, end_ms(e))
    if total > PARTICLE_BUDGET:
        bad.append('%s: ~%d live particles at peak (budget %d)' % (name, total, PARTICLE_BUDGET))
    if not meta['looping'] and meta['limit'] is not None and last > meta['limit']:
        bad.append('%s: the timeline runs %s ms, past its %d ms' % (name, last, meta['limit']))
    return bad


def tiling_problems(fx_texts):
    """THE TILING: every strand segment / orb on its helix inside [0, distance); distance = turns x pitch."""
    bad = []
    for key in AURA:
        v, name = AURA[key], 'fx_ws_aura_' + key
        D = aura_dist(key)
        fx = E.parse(fx_texts[name])
        strands = [e for e in fx.elements if e.name.startswith('strand_')]
        orbs = [e for e in fx.elements if e.name.startswith('orb_')]
        if len(strands) != 2 * v['turns'] * v['segs'] or len(orbs) != 2 * v['turns']:
            bad.append('%s: %d strand segments / %d orbs (want %d / %d)' % (name, len(strands), len(orbs),
                                                                          2 * v['turns'] * v['segs'], 2 * v['turns']))
        for e in strands + orbs:
            x, y, z = (e.nums('spawnOrg' + a)[0] for a in 'XYZ')
            rnd = [e.nums('spawnOrg' + a)[1] for a in 'XYZ']
            s = int(e.name.split('_')[1])
            if any(rnd) or not (0 <= x < D):
                bad.append('%s/%s: off the instance [0, %g) or randomised (x %g)' % (name, e.name, D, x))
                continue
            if abs(math.hypot(y, z) - v['r']) > 0.01:
                bad.append('%s/%s: radius %.3f, not the helix\'s %g' % (name, e.name, math.hypot(y, z), v['r']))
            want = 2 * math.pi * x / v['pitch'] + math.pi * s
            got = math.atan2(z, y)
            if abs(math.atan2(math.sin(got - want), math.cos(got - want))) > 0.01:
                bad.append('%s/%s: off its strand\'s phase' % (name, e.name))
            if e.name.startswith('strand_'):
                tv = [e.graph('velGraph0' + a).scale for a in 'XYZ']
                n = math.sqrt(sum(c * c for c in tv))
                tw = (v['pitch'] / (2 * math.pi), -v['r'] * math.sin(want), v['r'] * math.cos(want))
                tn = math.sqrt(sum(c * c for c in tw))
                if n <= 0 or n > 1.0 or sum(a * b for a, b in zip(tv, tw)) / (n * tn) < 0.999:
                    bad.append('%s/%s: not oriented along its helix (or its velocity moves it)' % (name, e.name))
                if 'runRelToEffect' not in e.flags('flags'):
                    bad.append('%s/%s: does not ride the instance (runRelToEffect)' % (name, e.name))
            else:
                # an orb slips back along its strand: axial = slip, orbit speed = r x 2 pi slip / pitch from its own phase
                ux = e.graph('velGraph0X')
                gy, gz = e.graph('velGraph0Y'), e.graph('velGraph0Z')
                life_s = e.nums('lifeSpanMsec')[0] / 1000.0
                want_w = orbit_speed(v['r'], v['slip'] * life_s / v['pitch'], life_s, ORB_SAMPLES_PER_TURN)
                y0, z0 = gy.curves[0][0][1], gz.curves[0][0][1]          # (-sin, cos) of the orbit's starting phase
                d = math.atan2(-y0, z0) - got
                start_ok = abs(math.atan2(math.sin(d), math.cos(d))) < 0.02
                if abs(ux.scale - v['slip']) > 1e-6 or abs(gy.scale - want_w) > 0.01 or abs(gz.scale - want_w) > 0.01 or not start_ok:
                    bad.append('%s/%s: does not slide along its strand (axial %g, orbit %g / %g, want %g / %g)'
                               % (name, e.name, ux.scale, gy.scale, gz.scale, v['slip'], want_w))
                if not (v['slip'] < 0 < v['speed'] + v['slip']):
                    bad.append('%s: slip %g must be back toward the lens yet keep the orbs moving out' % (name, v['slip']))
        # (the instance length = turns x pitch by construction; the beam's beamEffectDistance is checked against it in
        # beam_problems, the guard that keeps the chained instances tiling)
        # THE STROBE: the pattern repeats every full pitch only while the minor strand reads as a different strand
        major = [e for e in strands if e.name.startswith('strand_0_')]
        minor = [e for e in strands if e.name.startswith('strand_1_')]
        a_major = max(e.graph('alphaGraph').scale * max(r[1] for c in e.graph('alphaGraph').curves for r in c) for e in major)
        a_minor = max(e.graph('alphaGraph').scale * max(r[1] for c in e.graph('alphaGraph').curves for r in c) for e in minor)
        period = v['pitch'] if a_minor <= MINOR_TOLD_APART * a_major else v['pitch'] / 2
        per_frame = v['speed'] / float(STROBE_FPS)
        if per_frame > STROBE_MAX * period:
            bad.append('%s: %.1f u per %d fps frame is > %g of the pattern period %.1f (a wagon-wheel strobe; the strands '
                       'are %s)' % (name, per_frame, STROBE_FPS, STROBE_MAX, period,
                                     'told apart' if period == v['pitch'] else 'alike, so the period is half the pitch'))
    return bad


def beam_estimate(fx_texts, key, blocked=True):
    """Peak particles of one beam at the full range: aura instances at i x distance (age = i x distance / speed), the
    origin, and the impact (or the tip)."""
    v = AURA[key]
    aura_fx = E.parse(fx_texts['fx_ws_aura_' + key])
    D = aura_dist(key)
    total = 0
    for i in range(int(BEAM_RANGE // D) + 1):
        age = i * D / v['speed'] * 1000.0
        total += sum(alive_at(e, age) for e in aura_fx.elements if e.visual[0] not in L.LIGHTS)
    for other in ('fx_ws_origin_' + key, 'fx_ws_impact' if blocked else TARGET_EFFECT):
        total += sum(peak_particles(e) for e in E.parse(fx_texts[other]).elements if e.visual[0] not in L.LIGHTS)
    return total


def fx_problems(fx, meta):
    bad = []
    for n in NAMES:
        bad += validate_fx(n, fx[n], meta[n])
    bad += tiling_problems(fx)
    for key in AURA:
        est = beam_estimate(fx, key)
        if est > BEAM_BUDGET:
            bad.append('beam %s: ~%d live particles at the full range (budget %d)' % (key, est, BEAM_BUDGET))
    return bad


# =========================================================================================================================
# VALIDATION - the GDT, the textures, the names
# =========================================================================================================================
def awi_fields(text):
    """The asset editor's field list: name -> ('float' | 'int', lo, hi) | ('combo', options) | ('bool',) | ('any',)."""
    out = {}
    for m in re.finditer(r'AddEntry_(Float|Int)\(\s*"(\w+)"\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', text):
        out[m.group(2)] = (m.group(1).lower(), float(m.group(4)), float(m.group(5)))
    for m in re.finditer(r'AddEntry_Combo\(\s*"(\w+)"\s*,\s*"([^"]*)"\s*\)', text):
        out[m.group(1)] = ('combo', [o.strip() for o in m.group(2).split('|')])
    for m in re.finditer(r'AddEntry_CheckBox\(\s*"(\w+)"', text):
        out[m.group(1)] = ('bool',)
    for m in re.finditer(r'AddEntry_(?:Path|String|AssetCombo|Color)\(\s*"(\w+)"', text):
        out[m.group(1)] = ('any',)
    for m in re.finditer(r'AddEntry_Vector([234])\(([^)]*)\)', text):
        parts = [p.strip() for p in m.group(2).split(',')]
        n = int(m.group(1))
        names = [p.strip('"') for p in parts[:n]]
        lo, hi = float(parts[-2]), float(parts[-1])
        for nm in names:
            out[nm] = ('float', lo, hi)
    return out


def check_against_awi(label, fields, awi_text):
    bad = []
    spec = awi_fields(awi_text)
    have = dict(fields)
    for nm, sp in spec.items():
        if nm not in have:
            bad.append('%s: field %s missing (the asset editor defines it)' % (label, nm))
            continue
        val = have[nm]
        if sp[0] in ('float', 'int'):
            try:
                x = float(val)
            except ValueError:
                bad.append('%s: %s = %r is not a number' % (label, nm, val))
                continue
            if not (sp[1] - 1e-9 <= x <= sp[2] + 1e-9):
                bad.append('%s: %s = %s outside its range %g..%g' % (label, nm, val, sp[1], sp[2]))
            if sp[0] == 'int' and abs(x - round(x)) > 1e-9:
                bad.append('%s: %s = %s is not an integer' % (label, nm, val))
        elif sp[0] == 'combo' and val not in sp[1]:
            bad.append('%s: %s = %r is not one of %s' % (label, nm, val, sp[1]))
        elif sp[0] == 'bool' and val not in ('0', '1'):
            bad.append('%s: %s = %r is not 0 / 1' % (label, nm, val))
    return bad


GDT_HEAD_RE = re.compile(r'^\s*"([^"]+)"\s*\(\s*"([^"]+)"\s*\)', re.M)


def foreign_names(out_root=None, skip_name='tod2_wunderstrahl_fx.gdt'):
    """(name, gdf) of every asset in every GDT of the repo, the private root and the stage (out_root: the peer tracks'
    staged GDTs land beside ours, e.g. the Wunderstrahl art's mtl_tod2_ws_* / i_tod2_ws_*), except our own file's copies."""
    seen = {}
    bases = [ROOT / 'source_data', PRIVATE / 'source_data']
    if out_root is not None and (pathlib.Path(out_root) / 'source_data').resolve() != (ROOT / 'source_data').resolve():
        bases.append(pathlib.Path(out_root) / 'source_data')
    for base in bases:
        if not base.exists():
            continue
        for p in base.rglob('*.gdt'):
            if p.name.lower() == skip_name:
                continue
            try:
                text = p.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            for m in GDT_HEAD_RE.finditer(text):
                seen.setdefault((m.group(1).lower(), m.group(2).lower()), str(p))
    return seen


def gdt_problems(gdt_text, fx_names, foreign, textures):
    bad = []
    if not gdt_text.startswith('{'):
        bad.append('GDT: the file must start with { (gdtdb refuses anything before it)')
    for i, line in enumerate(gdt_text.split('\n'), 1):
        if line.strip().startswith('//'):
            bad.append('GDT:%d: a // line (gdtdb reads it as an unknown token)' % i)
    blocks = [(m.group(1), m.group(2), parse_fields(m.group(0))) for m in BLOCK_RE.finditer(gdt_text)]
    names = [(n, g) for n, g, _ in blocks]
    if len(set(names)) != len(names):
        bad.append('GDT: an asset defined twice')
    if not gdt_text.rstrip().endswith('}') or gdt_text.count('{') != gdt_text.count('}'):
        bad.append('GDT: unbalanced braces')
    want = {(IMG_CORE, 'image.gdf'), (IMG_CORE_ADD, 'image.gdf'), (IMG_STRAND, 'image.gdf'), (IMG_ORB, 'image.gdf'),
            (IMG_BURN, 'image.gdf'),
            (MAT_CORE_1P, 'material.gdf'), (MAT_CORE_3P, 'material.gdf'), (MAT_STRAND, 'material.gdf'),
            (MAT_ORB, 'material.gdf'), (MAT_BURN, 'material.gdf'), (MAT_STREAM, 'material.gdf'), (BEAM_1P, 'beam.gdf'),
            (BEAM_3P, 'beam.gdf'), (FLAMETABLE, 'flametable.gdf')}
    if set(names) != want:
        bad.append('GDT: assets %s, want %s' % (sorted(names), sorted(want)))
    images = {n for n, g in names if g == 'image.gdf'}
    materials = {n: dict(fl).get('materialType') for n, g, fl in blocks if g == 'material.gdf'}   # name -> material type
    awi = {k: file_donor_file(k).read_text(encoding='utf-8', errors='replace') for k in FILE_DONORS if file_donor_file(k).exists()}
    for name, gdf, fields in blocks:
        f = dict(fields)
        if len(name) > MAX_NAME:
            bad.append('GDT: %s is %d chars (> %d: silently replaced by a default)' % (name, len(name), MAX_NAME))
        hit = foreign.get((name.lower(), gdf.lower()))
        if hit:
            bad.append('GDT: %s (%s) is already defined in %s (gdtdb refuses a duplicate asset)' % (name, gdf, hit))
        for k, val in fields:
            if '"' in val or '\n' in val:
                bad.append('GDT: %s %s carries a quote / newline' % (name, k))
        if gdf == 'image.gdf':
            path = f.get('baseImage', '')
            tex = textures.get(name)
            if path != '%s/%s.png' % (TEX_REL, name) or tex is None:
                bad.append('GDT: image %s names %s (no generated texture)' % (name, path))
            else:
                h, w = tex.shape[:2]
                if any(d & (d - 1) or d % 4 for d in (w, h)):
                    bad.append('GDT: image %s is %dx%d (power of two and multiple of 4 required)' % (name, w, h))
            if f.get('semantic') != 'effectMap' or f.get('compressionMethod') != 'compressed high color':
                bad.append('GDT: image %s must be an effectMap, compressed high color' % name)
        elif gdf == 'material.gdf':
            if not f.get('surfaceType'):
                bad.append('GDT: material %s has no explicit surfaceType (the linker refuses it)' % name)
            if f.get('materialType') not in MATERIAL_TYPES:
                bad.append('GDT: material %s type %s is not one of %s' % (name, f.get('materialType'), MATERIAL_TYPES))
            if f.get('colorMap') not in images:
                bad.append('GDT: material %s colorMap %s is not an image in this GDT' % (name, f.get('colorMap')))
            if f.get('cullFace') != 'None':
                bad.append('GDT: material %s is not two-sided (cullFace None)' % name)
            if name == MAT_CORE_1P and f.get('falloff') != '0':
                bad.append('GDT: material %s uses view falloff (the shooter looks down the 1p beam at 77-84 deg: falloff '
                           'would dim the whole core to its floor)' % name)
        elif gdf == 'beam.gdf':
            bad += beam_problems(name, f, fx_names, materials)
            if 'beam.awi' in awi:
                bad += check_against_awi('GDT ' + name, fields, awi['beam.awi'])
        elif gdf == 'flametable.gdf':
            bad += flametable_problems(name, f, materials)
            if 'flametable.awi' in awi:
                bad += check_against_awi('GDT ' + name, fields, awi['flametable.awi'])
    return bad


BEAM_LOCKSTEP = {
    'useVirtualTarget': '1', 'virtualTargetMass': '0', 'dieIfTooLong': '0', 'collisionMode': 'nodes',
    'collisionMask': 'shot and not body', 'dieIfBlocked': '0', 'beamAffectedByGravity': '0', 'beamGravity': '0',
    'blockedEffectSound': IMPACT_LOOP_SOUND, 'beamShape': BEAM_SHAPE,
}


def beam_problems(name, f, fx_names, materials):
    bad = []
    for k, want in BEAM_LOCKSTEP.items():
        if f.get(k) != want:
            bad.append('GDT %s: %s = %r (LOCKSTEP wants %r)' % (name, k, f.get(k), want))
    try:
        if float(f.get('virtualTargetDistance', 'nan')) != BEAM_RANGE:
            bad.append('GDT %s: virtualTargetDistance %s != BEAM_RANGE %d (the script\'s TOD_WS_RANGE)' % (name, f.get('virtualTargetDistance'), BEAM_RANGE))
        if float(f.get('maxLength', 'nan')) < BEAM_RANGE:
            bad.append('GDT %s: maxLength %s < BEAM_RANGE %d' % (name, f.get('maxLength'), BEAM_RANGE))
        if float(f.get('launchSpeed', 'nan')) != BEAM_LAUNCH_SPEED:
            bad.append('GDT %s: launchSpeed %s != BEAM_LAUNCH_SPEED %d (the script\'s TOD_WS_LAUNCH_SPEED)' % (name, f.get('launchSpeed'), BEAM_LAUNCH_SPEED))
        if float(f.get('retractSpeed', 'nan')) != BEAM_RETRACT_SPEED:
            bad.append('GDT %s: retractSpeed %s != %d (the instant release)' % (name, f.get('retractSpeed'), BEAM_RETRACT_SPEED))
        for wave in ('sine', 'sawtooth', 'square', 'triangle'):
            if float(f.get(wave + 'AmplitudeX', '1')) or float(f.get(wave + 'AmplitudeY', '1')):
                bad.append('GDT %s: a %s wave bends the laser' % (name, wave))
    except ValueError as ex:
        bad.append('GDT %s: a LOCKSTEP field is not a number (%s)' % (name, ex))
    if f.get('material') not in materials:
        bad.append('GDT %s: material %s is not in this GDT' % (name, f.get('material')))
    for k in ('originEffect', 'beamEffect', 'targetEffect', 'blockedEffect', 'deathEffect'):
        m = re.fullmatch(r'tod\\\\wunderstrahl\\\\(\w+)\.efx', f.get(k, ''))
        if not m or m.group(1) not in fx_names:
            bad.append('GDT %s: %s %r is not one of the generated effects' % (name, k, f.get(k)))
    key = '1p' if name == BEAM_1P else '3p'
    try:
        if abs(float(f.get('beamEffectDistance', 'nan')) - aura_dist(key)) > 1e-6:
            bad.append('GDT %s: beamEffectDistance %s != the aura\'s %g (turns x pitch: the helix would not tile)'
                       % (name, f.get('beamEffectDistance'), aura_dist(key)))
        if abs(float(f.get('beamEffectSpeed', 'nan')) - AURA[key]['speed']) > 1e-6:
            bad.append('GDT %s: beamEffectSpeed %s != the aura\'s %g' % (name, f.get('beamEffectSpeed'), AURA[key]['speed']))
    except ValueError:
        bad.append('GDT %s: beamEffectDistance / Speed not a number' % name)
    return bad


def flametable_problems(name, f, materials):
    bad = []
    if f.get('name') != FLAMETABLE:
        bad.append('GDT %s: its table name is %r' % (name, f.get('name')))
    for slot in FLAMETABLE_MATERIAL_SLOTS:
        if f.get(slot) != MAT_STREAM or f.get(slot) not in materials:
            bad.append('GDT %s: material slot %s = %r (every slot draws the laser core, additive: %s)'
                       % (name, slot, f.get(slot), MAT_STREAM))
        elif materials[f.get(slot)] != 'effect_lit_emissive_add':
            bad.append('GDT %s: material slot %s wears a %s material (additive only: brightness 0 must add nothing, '
                       'never draw a black quad)' % (name, slot, materials[f.get(slot)]))
    if f.get('heat', '') not in ('', MAT_STREAM):
        bad.append('GDT %s: heat = %r (empty, or the stream material)' % (name, f.get('heat')))
    for snd in FLAMETABLE_SOUNDS:
        if f.get(snd, '') != '':
            bad.append('GDT %s: sound %s = %r (the weapon owns the audio; a doubled loop)' % (name, snd, f.get(snd)))
    try:
        for k in ('flameVar_fireBrightness', 'flameVar_dripsBrightness', 'flameVar_smokeBrightness', 'flameVar_smokeMaxAlpha'):
            if float(f.get(k, '1')) != 0:
                bad.append('GDT %s: %s = %s (the stream must be invisible)' % (name, k, f.get(k)))
        r = float(f.get('flameVar_streamPrimaryLightRadius', 'nan')) + float(f.get('flameVar_streamPrimaryLightRadiusFlutter', 'nan'))
        if not (0 < r <= L.LIGHT_RADIUS_MAX):
            bad.append('GDT %s: the stream light reaches %s u (1..%d)' % (name, r, L.LIGHT_RADIUS_MAX))
        if float(f.get('flameVar_streamFuelLength', '1e9')) > 0.01 or float(f.get('flameVar_streamFlameLength', '1e9')) > 0.01:
            bad.append('GDT %s: a visible fuel / flame stream' % name)
    except ValueError as ex:
        bad.append('GDT %s: a field is not a number (%s)' % (name, ex))
    return bad


def build_textures():
    return {name: fn() for name, fn in TEXTURES.items()}


def texture_problems(textures):
    bad = []
    for name, arr in textures.items():
        h, w = arr.shape[:2]
        if arr.dtype != np.uint8 or arr.ndim != 3 or arr.shape[2] != 4:
            bad.append('texture %s is not RGBA8' % name)
        if any(d & (d - 1) or d % 4 for d in (w, h)):
            bad.append('texture %s is %dx%d (power of two, multiple of 4)' % (name, w, h))
        if arr[..., 3].max() == 0:
            bad.append('texture %s is fully transparent' % name)
    core = textures.get(IMG_CORE)
    if core is not None and core.ndim == 3:
        a = core[..., 3].astype(np.float64) / 255.0
        if BEAM_SHAPE == 'ribbon':
            rim = max(1, int(round(0.08 * a.shape[0])))                    # the outer 8 % of rows on each side
            edge = max(a[:rim].max(), a[-rim:].max())
            axis = a[a.shape[0] // 2 - 1:a.shape[0] // 2 + 1].mean()
            if edge > 0.05 or axis < 0.8:
                bad.append('texture %s: not a ribbon profile (outer rows alpha up to %.2f, want ~0; axis %.2f, want >= 0.8): '
                           'a camera-facing ribbon would show hard edges' % (IMG_CORE, edge, axis))
        elif a.min() < 0.6:
            bad.append('texture %s: not uniform across V (alpha down to %.2f) for the closed %s shape: its V wraps round the '
                       'tube, so a profile would band or stripe' % (IMG_CORE, a.min(), BEAM_SHAPE))
        c = core.astype(np.float64)
        seam = np.abs(c[:, 0] - c[:, -1]).max()
        step = np.abs(np.diff(c, axis=1)).max()
        if seam > 1.5 * step + 2:
            bad.append('texture %s: a seam where U repeats (%.0f vs %.0f between neighbours): the scroll would show it'
                       % (IMG_CORE, seam, step))
    return bad


def problems_of(fx, meta, gdt_text, textures, foreign):
    bad = donor_problems()
    bad += fx_problems(fx, meta)
    bad += texture_problems(textures)
    bad += gdt_problems(gdt_text, set(fx), foreign, textures)
    return bad


# =========================================================================================================================
# THE SELFTEST - one planted fault per rule; each must be caught
# =========================================================================================================================
def selftest(fx, meta, gdt_text, textures, foreign):
    """Every planted fault must be caught BY ITS OWN RULE: a problem carrying the rule's words, not just any problem."""
    misses = []

    def need(label, problems, expect):
        if not any(expect in p for p in problems):
            misses.append('%s (wanted a problem saying "%s"; got %s)' % (label, expect, problems[:2] if problems else 'none'))

    def fx_caught(label, name, text, expect, m=None):
        need(label, validate_fx(name, text, m or meta[name]), expect)

    def gdt_caught(label, text, expect, fgn=None, tex=None):
        need(label, gdt_problems(text, set(fx), foreign if fgn is None else fgn, textures if tex is None else tex), expect)

    def sub_block(text, block, pattern, repl):
        """Replace inside one asset block only."""
        m = re.search(r'\t"%s" \( "[^"]+" \)\n\t\{\n.*?\n\t\}' % re.escape(block), text, re.S)
        part = re.sub(pattern, repl, m.group(0), count=1)
        return text[:m.start()] + part + text[m.end():]

    o1, imp, aura1, lens = fx['fx_ws_origin_1p'], fx['fx_ws_impact'], fx['fx_ws_aura_1p'], fx['fx_ws_lens_cool']
    die = fx['fx_ws_disintegrate']
    fx_caught('a stub material', 'fx_ws_impact', imp.replace('gfx_spark_single_em', 'gfx_debug_missing_fx'), 'stub')
    fx_caught('a path over 63 characters', 'fx_ws_impact_' + 'x' * 40, imp, 'chars (> 63', meta['fx_ws_impact'])
    fx_caught('a forever loop in a one-shot timeline', 'fx_ws_lens_cool',
              re.sub(r'(name "glow";\n\teditorFlags )', r'\1looping ', lens, count=1).replace('spawnLooping 1 0;', 'spawnLooping 90 0;', 1),
              'loops forever inside a ONE-SHOT')
    fx_caught('a shadowed light', 'fx_ws_impact', imp.replace('PRIMARY_NOSHADOWMAP 1', 'PRIMARY_NOSHADOWMAP 0'), 'casts shadows')
    fx_caught('a light missing a lighting state', 'fx_ws_impact', imp.replace('lightingstate3 1', 'lightingstate3 0'),
              'missing from a lighting state')
    fx_caught('a light radius over 400', 'fx_ws_impact', re.sub(r'(lightRadiusGraph )[\d.]+', r'\g<1>520', imp), 'radius 1..400')
    fx_caught('a light in a no-light variant', 'fx_ws_disintegrate_nl', die, 'no-light (_nl)', meta['fx_ws_disintegrate_nl'])
    fx_caught('a big flash with no near fade', 'fx_ws_disintegrate',
              re.sub(r'(name "flash";[\s\S]*?fadeOutRange )[\d.]+ [\d.]+', r'\g<1>0 0', die), 'no near-camera fade (the 1p rule)')
    fx_caught('a big sprite at the shooter\'s eye', 'fx_ws_origin_1p',
              re.sub(r'(name "halo";[\s\S]*?sizeGraph0 )[\d.]+', r'\g<1>9', o1), 'at the shooter\'s eye')
    fx_caught('a sprite only too big if a size is a radius', 'fx_ws_origin_1p',     # 2.5 x 1.05 fits 4 u as a width only
              re.sub(r'(name "halo";[\s\S]*?sizeGraph0 )[\d.]+', r'\g<1>2.5', o1), 'at the shooter\'s eye')
    fx_caught('a 1p aura sheath with no near fade', 'fx_ws_aura_1p',
              re.sub(r'(name "sheath_0";[\s\S]*?fadeOutRange )[\d.]+ [\d.]+', r'\g<1>0 0', aura1), 'in the 1p aura with no near-camera fade')
    fx_caught('a particle budget blown', 'fx_ws_impact', imp.replace('spawnLoopingSpawnCount 1 1;', 'spawnLoopingSpawnCount 9 0;', 1),
              'live particles at peak (budget')
    fx_caught('a child effect', 'fx_ws_tip',
              re.sub(r'attachment ""', 'attachment "tod/wunderstrahl/fx_ws_impact"', fx['fx_ws_tip'], count=1), 'names a child effect')
    fx_caught('a fractional lifetime', 'fx_ws_tip', re.sub(r'(name "flare";[\s\S]*?lifeSpanMsec )\d+', r'\g<1>180.5', fx['fx_ws_tip']),
              'fractional lifeSpanMsec')
    fx_caught('an unproven stock material', 'fx_ws_tip', fx['fx_ws_tip'].replace('gfx_light_phosphorous_em', 'gfx_unproven_em'),
              'neither ours nor a proven template material')
    short = dict(meta['fx_ws_disintegrate'])
    apply_carriers({'fx_ws_disintegrate': short}, {'fx_ws_disintegrate': 1000 - CARRIER_MARGIN_MS})
    fx_caught('a one-shot outliving its script carrier', 'fx_ws_disintegrate', die, 'past its', short)
    if KILL_FX_LOOPING:
        fx_caught('a kill-effect loop that comes round inside its carrier', 'fx_ws_disintegrate',
                  re.sub(r'(name "embers";[\s\S]*?spawnLooping )[\d.]+ [\d.]+', r'\g<1>600 0', die), 'would respawn before its carrier')
        fx_caught('a one-shot element in a carrier-looped kill effect', 'fx_ws_zombie_burn',
                  re.sub(r'(name "flash";\n\teditorFlags )looping ', r'\1', fx['fx_ws_zombie_burn'], count=1),
                  'a one-shot element in a carrier-looped')
    fx_caught('three or more lights alive at once', 'fx_ws_impact',
              re.sub(r'(name "light";[\s\S]*?spawnLooping )[\d.]+', r'\g<1>150', imp), 'lights alive at once')
    fx_caught('an element that names a sound', 'fx_ws_tip',
              fx['fx_ws_tip'].replace('\telemSpawnSound\n\t{\n\t};', '\telemSpawnSound\n\t{\n\t\t"weap_flamethrower_fireloop"\n\t};', 1),
              'names a sound')
    # the tiling
    broken = dict(fx)
    broken['fx_ws_aura_1p'] = re.sub(r'(name "strand_0_03";[\s\S]*?spawnOrgY )-?[\d.]+', r'\g<1>0.5', aura1)
    need('a strand segment off its helix', tiling_problems(broken), 'not the helix\'s')
    broken['fx_ws_aura_1p'] = re.sub(r'(name "strand_1_05";[\s\S]*?spawnOrgX )-?[\d.]+', r'\g<1>40', aura1)
    need('a strand segment outside its instance', tiling_problems(broken), 'off the instance')
    broken = dict(fx)
    broken['fx_ws_aura_1p'] = re.sub(r'(name "strand_0_02";[\s\S]*?velGraph0X )-?[\d.]+', r'\g<1>3', aura1)
    need('a strand segment that drifts / points off its helix', tiling_problems(broken), 'not oriented along its helix')
    broken['fx_ws_aura_1p'] = re.sub(r'(name "orb_1_1";[\s\S]*?velGraph0Y )-?[\d.]+', r'\g<1>-30', aura1)
    need('an orb that orbits off its strand', tiling_problems(broken), 'does not slide along its strand')
    saved = AURA['3p']['minor']
    AURA['3p']['minor'] = (1.0, 1.0)                           # two equal strands: the period halves -> a 30 fps strobe
    try:
        broken = dict(fx)
        broken['fx_ws_aura_3p'] = S.effect(aura('3p'), *aura_box('3p', 18))
    finally:
        AURA['3p']['minor'] = saved
    need('two equal strands that strobe at 30 fps', tiling_problems(broken), 'wagon-wheel strobe')
    # the beam budget: an overage that ONE instance still carries inside its own budget, so only the whole-beam rule sees it
    broken = dict(fx)
    broken['fx_ws_aura_1p'] = re.sub(r'(name "motes";[\s\S]*?spawnLoopingSpawnCount )\d+ \d+', r'\g<1>3 0', aura1)
    own = validate_fx('fx_ws_aura_1p', broken['fx_ws_aura_1p'], meta['fx_ws_aura_1p'])
    if own:
        misses.append('a whole beam over its budget (the planted overage trips the per-effect rules too: %s)' % own[:2])
    need('a whole beam over its budget', fx_problems(broken, meta), 'beam 1p:')
    # the GDT
    gdt_caught('a // line in the GDT', gdt_text.replace('\t"%s" ( "beam.gdf" )' % BEAM_1P, '\t// note\n\t"%s" ( "beam.gdf" )' % BEAM_1P, 1),
               'a // line')
    gdt_caught('a GDT not starting with a brace', '\n' + gdt_text, 'must start with {')
    gdt_caught('the beam range out of step', sub_block(gdt_text, BEAM_1P, r'"virtualTargetDistance" "\d+"', '"virtualTargetDistance" "2000"'),
               'virtualTargetDistance 2000 != BEAM_RANGE')
    gdt_caught('the launch speed out of step', sub_block(gdt_text, BEAM_3P, r'"launchSpeed" "\d+"', '"launchSpeed" "1750"'),
               'launchSpeed 1750 != BEAM_LAUNCH_SPEED')
    gdt_caught('a beam that stops at zombies', sub_block(gdt_text, BEAM_1P, r'"collisionMask" "[^"]*"', '"collisionMask" "shot"'),
               'collisionMask')
    gdt_caught('a beam with no impact sizzle', sub_block(gdt_text, BEAM_1P, r'"blockedEffectSound" "[^"]*"', '"blockedEffectSound" ""'),
               'blockedEffectSound')
    gdt_caught('a beam effect that is not generated',
               sub_block(gdt_text, BEAM_3P, r'"blockedEffect" "[^"]*"', r'"blockedEffect" "weapon\\\\\\\\fx_hero_flamethrower_blocked.efx"'),
               'is not one of the generated effects')
    gdt_caught('an aura distance that does not tile', sub_block(gdt_text, BEAM_1P, r'"beamEffectDistance" "[^"]*"', '"beamEffectDistance" "25"'),
               'would not tile')
    gdt_caught('a material with no surfaceType', sub_block(gdt_text, MAT_ORB, r'\t\t"surfaceType" "[^"]*"\n', ''), 'no explicit surfaceType')
    gdt_caught('a material name over 63 characters', gdt_text.replace('"%s"' % MAT_BURN, '"%s"' % (MAT_BURN + '_' + 'x' * 50)),
               'chars (> 63')
    gdt_caught('a beam field out of its editor range', sub_block(gdt_text, BEAM_1P, r'"numSegments" "\d+"', '"numSegments" "500"'),
               'numSegments = 500 outside its range')
    gdt_caught('a 1p core with view falloff', sub_block(gdt_text, MAT_CORE_1P, r'"falloff" "0"', '"falloff" "1"'), 'uses view falloff')
    other = 'hexagon' if BEAM_SHAPE != 'hexagon' else 'ribbon'
    gdt_caught('a beam shape out of step with its core texture',
               sub_block(gdt_text, BEAM_1P, r'"beamShape" "[^"]*"', '"beamShape" "%s"' % other), 'beamShape')
    gdt_caught('a slow release', sub_block(gdt_text, BEAM_3P, r'"retractSpeed" "\d+"', '"retractSpeed" "2000"'), 'the instant release')
    gdt_caught('an aura carried at the wrong speed', sub_block(gdt_text, BEAM_1P, r'"beamEffectSpeed" "[^"]*"', '"beamEffectSpeed" "200"'),
               'beamEffectSpeed')
    gdt_caught('a wave that bends the laser', sub_block(gdt_text, BEAM_1P, r'"sineAmplitudeX" "[^"]*"', '"sineAmplitudeX" "3"'),
               'bends the laser')
    gdt_caught('a visible flame-table smoke',
               sub_block(gdt_text, FLAMETABLE, r'"flameVar_smokeMaxAlpha" "[^"]*"', '"flameVar_smokeMaxAlpha" "0.35"'), 'must be invisible')
    gdt_caught('a flame-table sound',
               sub_block(gdt_text, FLAMETABLE, r'"flameOnLoopSound" "[^"]*"', '"flameOnLoopSound" "weap_flamethrower_fireloop"'),
               'the weapon owns the audio')
    gdt_caught('a flame-table light past 400',
               sub_block(gdt_text, FLAMETABLE, r'"flameVar_streamPrimaryLightRadius" "[^"]*"', '"flameVar_streamPrimaryLightRadius" "750"'),
               'the stream light reaches')
    gdt_caught('a flame-table fire material', sub_block(gdt_text, FLAMETABLE, r'"fire" "[^"]*"', '"fire" "gfx_fire_flame_base_1_anim_em"'),
               'material slot fire')
    gdt_caught('a flame-table slot on a blend material',
               sub_block(gdt_text, MAT_STREAM, r'"materialType" "[^"]*"', '"materialType" "effect_lit_scroll_emissive_blend_nocull"'),
               'additive only')
    fake = dict(foreign)
    fake[(MAT_STRAND.lower(), 'material.gdf')] = 'planted/other.gdt'
    gdt_caught('a name another GDT already defines', gdt_text, 'already defined in', fgn=fake)
    bad_tex = dict(textures)
    bad_tex[IMG_ORB] = np.zeros((100, 128, 4), np.uint8) + 9
    gdt_caught('an image that is not a power of two', gdt_text, 'power of two and multiple of 4', tex=bad_tex)
    wrong = dict(textures)
    if BEAM_SHAPE == 'ribbon':
        wrong[IMG_CORE] = np.full(textures[IMG_CORE].shape, 230, np.uint8)  # uniform across V: a hard-edged ribbon
        need('a core texture with hard edges on a ribbon', texture_problems(wrong), 'not a ribbon profile')
        wrong[IMG_CORE] = textures[IMG_CORE].copy()
        wrong[IMG_CORE][2, :, 3] = 255                                      # clear at the very edge, a hard line just inside
        need('a core texture hard just inside its edge', texture_problems(wrong), 'not a ribbon profile')
    else:
        wrong[IMG_CORE] = tex_core_ribbon()                                 # a profile on a closed tube: bands / stripes
        need('a profiled core texture on a closed shape', texture_problems(wrong), 'not uniform across V')
    ramp = dict(textures)
    ramp[IMG_CORE] = textures[IMG_CORE].copy()
    ramp[IMG_CORE][..., :3] = (ramp[IMG_CORE][..., :3] * np.linspace(1.0, 0.5, ramp[IMG_CORE].shape[1])[None, :, None]).astype(np.uint8)
    need('a core texture that does not tile along U', texture_problems(ramp), 'a seam where U repeats')
    return misses


# =========================================================================================================================
# MAIN
# =========================================================================================================================
def build_all():
    fx, meta = build_fx()
    gdt = emit_gdt(gdt_blocks())
    textures = build_textures()
    return fx, meta, gdt, textures


def summary_lines(fx):
    lines = []
    for n in NAMES:
        parsed = E.parse(fx[n])
        peak = sum(peak_particles(e) for e in parsed.elements if e.visual[0] not in L.LIGHTS)
        lights = sum(1 for e in parsed.elements if e.visual[0] in L.LIGHTS)
        lines.append('  %s%-20s %2d elements, peak ~%2d particles, %d light, sha %s'
                     % (PREFIX, n, len(parsed.elements), peak, lights, sha(fx[n].encode('utf-8'))[:10]))
    for key in AURA:
        lines.append('  beam %s at the full %d u: ~%d particles blocked / ~%d in open air (budget %d); the swirl lives %d u '
                     '(%d ms), %d instances carry it, %.1f turns/s'
                     % (key, BEAM_RANGE, beam_estimate(fx, key, True), beam_estimate(fx, key, False), BEAM_BUDGET,
                        AURA[key]['reach'], aura_life(key), math.ceil(AURA[key]['reach'] / aura_dist(key)),
                        AURA[key]['speed'] / AURA[key]['pitch']))
    return lines


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--vendor', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--out-root', default=str(ROOT))
    a = ap.parse_args(argv)
    if a.vendor:
        return vendor(a.force)
    out_root = pathlib.Path(a.out_root).resolve()
    if donor_problems():
        print('WS FX INVALID:\n  ' + '\n  '.join(donor_problems()))
        return 1
    fx, meta, gdt, textures = build_all()
    carriers = carrier_limits(out_root)
    apply_carriers(meta, carriers)
    foreign = foreign_names(out_root)
    bad = problems_of(fx, meta, gdt, textures, foreign)
    if bad:
        print('WS FX INVALID:\n  ' + '\n  '.join(bad))
        return 1
    if a.selftest:
        misses = selftest(fx, meta, gdt, textures, foreign)
        if misses:
            print('WS FX SELFTEST MISSED: ' + ', '.join(misses))
            return 1
        print('WS FX SELFTEST OK: every planted fault caught')
        return 0
    fx_dir = out_root / FX_REL
    gdt_path = out_root / GDT_REL
    if a.check:
        stale = []
        for n in NAMES:
            p = fx_dir / (n + '.efx')
            if not p.exists():
                stale.append(n + ' missing')
            elif p.read_bytes() != fx[n].encode('utf-8'):
                stale.append(n + ' differs')
        if fx_dir.exists():
            stale += ['stray ' + p.name for p in sorted(fx_dir.glob('*.efx')) if p.stem not in fx]
        if not gdt_path.exists():
            stale.append(GDT_REL + ' missing')
        elif gdt_path.read_bytes() != gdt.encode('utf-8'):
            stale.append(GDT_REL + ' differs')
        for name, arr in textures.items():
            p = tex_path(name)
            if not p.exists():
                stale.append(p.name + ' missing')
                continue
            got = np.asarray(Image.open(p).convert('RGBA'))
            if got.shape != arr.shape or int(np.abs(got.astype(int) - arr.astype(int)).max()) > 1:
                stale.append(p.name + ' differs')
        if (ROOT / TEX_REL).exists():
            stale += ['stray ' + p.name for p in sorted((ROOT / TEX_REL).glob('*.png')) if p.stem not in textures]
        if stale:
            print('WS FX STALE: ' + ', '.join(stale) + ' - run python tools/wunderstrahl/fx/make_fx.py'
                  + ('' if out_root == ROOT else ' --out-root ' + a.out_root))
            return 1
        print('WS FX OK: %d effects, the GDT (%d assets), %d textures' % (len(fx), len(BLOCK_RE.findall(gdt)), len(textures)))
        return 0
    fx_dir.mkdir(parents=True, exist_ok=True)
    for old in sorted(fx_dir.glob('fx_ws_*.efx')):
        if old.stem not in fx:
            old.unlink()
            print('WS FX RETIRED', old.name)
    for n in NAMES:
        (fx_dir / (n + '.efx')).write_bytes(fx[n].encode('utf-8'))
    gdt_path.parent.mkdir(parents=True, exist_ok=True)
    gdt_path.write_bytes(gdt.encode('utf-8'))
    (ROOT / TEX_REL).mkdir(parents=True, exist_ok=True)
    for old in sorted((ROOT / TEX_REL).glob('*.png')):          # this folder holds only the generated textures
        if old.stem not in textures:
            old.unlink()
            print('WS FX RETIRED', old.name)
    for name, arr in textures.items():
        Image.fromarray(arr).save(tex_path(name), optimize=False, compress_level=9)
    print('\n'.join(summary_lines(fx)))
    print('  carriers (%s): %s' % (SCRIPT_REL, ', '.join('%s ends within %d ms' % (k, v) for k, v in sorted(carriers.items()))
                                   if carriers else 'the script is not in the tree yet - the static limits apply'))
    print('WS FX WRITTEN: %d effects -> %s; %s; %d textures -> %s'
          % (len(fx), fx_dir, gdt_path, len(textures), ROOT / TEX_REL))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
