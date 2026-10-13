"""
CURRENT DEFAULT v10 (2026-09-30): the approved imposing cyber middle ground.
The engineered monument carries massive lettering and a mechanical death-mask
crest in worn dark metal. Ordinary near/middle buildings and elevated clusters
share the tall landmarks' cyber architecture. Reduced density/layout stay fixed.
The station has a legible canopy/train silhouette and a reserved sightline.
Low planets, rings/moons and prominent stars remain above architectural crowns.
The historical versions below remain context, not the current art direction.

tools/sky3d/build_city.py — TOWER OF DOOM II: THE RENDERED SKY (v1 2026-09-24, v2 THE CYBER PASS, v4 THE REFERENCE COPY 2026-09-25 [v4d: true reference values; v4e: the black floor; v4f: the spiral disc; v4g: lit area; v4h: storm, origin, black hole, sign; v4i: pure hues, matte bodies, coloured roofs; v4j: balance; v4k: nebula voids; v4l: the disc swirls]; v5 THE BIG CITY 2026-09-25 [fewer, three times bigger, three times the detail; the core bleeds into the grid; the window tint per hue; battlecruisers; twice the sky; the black hole's lensed halo; v5b: aligned core lots, wide panels, a cool palette, dark hulls; v5c: sparse windows, the cruiser under the hole; v5d: the ziggurat and the ring decks capped; v5e: soft fans for tails and jets, dark wings; v5f: a diffuse hull, nested fans; v5g: a small cool bay, faint jets, dim roof cells; v5h: soft-fan plumes]; v6 THE COLOUR PASS 2026-09-25 [the twelve billboards; windows -35 %; the red giant x4; a lush palette; deeper blacks; graded haze; v6b: THE SPIRE CLUSTER - the references' towers; v6c: a few seams not a cage, broad crystals, a crimson giant; v6d: saturated crystals, sparse rows; v6e: slim cores in dense bundles, amber bases; v6f: every line capped to its cell; v6h: the slabs BRIGHT like the references' (measured, not eyeballed)]; docs/166 §8; v7 THE TITLE GATE 2026-09-29; v7b THE HERO SIGN + NO SHIPS 2026-09-29; docs/166 §9)

v4 — THE REFERENCE COPY (user, 2026-09-25: three image-model references in Downloads/sky_refs, "these are what we will use
as a reference ... if we can build something to this level that would be wild"). Measured, the references are: 2..4 % near-black,
25 % saturated colour, 15 % near-white, a darkest tenth that is saturated INDIGO (21,19,35), a space base of (33,43,75), nebula
over half the upper sky in magenta / pink / violet / orange / teal, a WARM ORANGE (207,146,75) city glow at the horizon, cyan /
magenta / violet / green neon at full saturation, dark tower bodies of (23,20,26) that are never black, and blue-violet
(47,52,91) shadows. v3 measured 76..93 % low-saturation mush, 0 % saturated, 0 % bright, a mauve-grey floor. So v4 copies:
  * UNITS: every emitter is authored in W = display white (1.0 = the references' white); the finish maps W to the game's
    display white and the exposure contract's mean; the knee is in W (finish_sky.py --white).
  * THE SKY is SPACE: a saturated indigo floor (no grey anywhere), domain-warped nebula in five hues with dust lanes and
    filaments, three star layers (50k faint, 10k medium, ~70 big stars with four-point flares), brighter round the black hole.
    No cloud sheets.
  * THE CITY: dark bodies with a painted ambient floor + DENSE WARM WINDOWS (the references' orange carpet) + on 55 % of the
    towers full-height translucent NEON PANELS in one saturated hue with a lit circuit grid; lit edges, collars, neon RINGS
    round the crowns, SIGILS (circle / hexagon / diamond emblems) on the faces, spiked crowns, FLOATING PLATFORMS with
    LIGHT-FALLS, glowing highway RIBBONS. Warm sodium streets. Neon palette: cyan, magenta, violet, green, orange, blue, pink,
    gold; red stays reserved for the moon, the sign and THE ORIGIN.
  * THE BODIES: one huge oblique BLACK HOLE (a spiral accretion disc in orange -> magenta -> violet with dust gaps, a photon
    ring, an asteroid debris field), two banded GAS GIANTS with rings, three CRACKED planets with glowing fissures (orange lava,
    cyan energy, green energy), grey moons, a small ringed planet, two SPIRAL GALAXIES, drifting asteroids.
  * THE FOG is warm (the city's light pollution), the HAZE above it is sky-blue; the storm round THE ORIGIN is violet cumulus
    lit from inside. --skip tokens added: sigils,ringsx,platforms,asteroids,galaxies

v5 — THE BIG CITY (user, on the v4 contact sheet, 2026-09-25: "too many buildings ... by making so many they have to be so small
... three times as big ... a colour that's so dominant, the windows ... the sky is a bit empty, double what we have in the sky
and half what we have on the ground ... the spaceships need way more detail, bigger ... the black holes need more detail ... our
major buildings need a lot more detail ... the ground floor looks circular but leads into the background, not an even bleed"):
  * LOTS: pitch 320 / 640 / 1280 m (was 140 / 280 / 560), heights x2..2.5, ~a fifth of the buildings — and three times the
    detail on each: more setback tiers, lit BELTS, buttress FINS, sigils on the face, antenna ARRAYS, lit PLINTHS, second screens.
  * WINDOWS: the tint follows the tower's hue row (cool white, cyan, violet, pink, green, gold); amber is one row of ten plus a
    10 % sprinkle; lit fraction 0.34. The city's colour is its NEON, the windows are its texture.
  * THE CORE: the podium's ring roads continue out to 1.42 km (CORE_ROADS) with twelve radial boulevards; the lots between the
    rings are POLAR (CORE_BANDS: low at the foot, rising outward) and the square districts start at R_CORE — the circle becomes
    the city instead of ending at a wall. THE LOOP monorail rides over the last ring road.
  * SHIPS: battlecruisers 1.5..2x longer (STARSHIPS) with a real silhouette — keel, main hull, dorsal deck, spine, a bridge
    tower with a lit command deck and sensor masts, two nacelles, a stern wall with seven nozzles and long plumes, swept wings
    and a dorsal fin with neon edges, three decks of lit windows a side and two along the belly, a glowing hangar bay, running
    lights, a bow searchlight; twelve fighters, two in escort formation.
  * THE SKY: twice the bodies — five gas giants (three ringed), five cracked planets, seven moons and moonlets, TWO black holes,
    four galaxies (one edge-on), a comet with an ion and a dust tail, an asteroid BELT of ~220 rocks, 90 drifting rocks;
    distant small worlds dimmed and hazed (bd['dim']) so the sky reads deep.
  * THE BLACK HOLE: the LENSED FAR SIDE bent over and under the shadow (mat_lensarc), polar jets, six tidal streams, a finer
    orbital turbulence octave, a stronger Doppler side, 150 debris rocks.
  * MEGATOWERS: mega_detail on every supertall inside 12 km — belts hugging the shaft, one or two RING PLATFORMS (a dark
    annular deck, lit rims, pods and window blocks on top, light-falls under it), buttress fins with lit edges, an antenna array.

v6 — THE COLOUR PASS (user, 2026-09-25, on the v5 build: "the entire skybox ... more colourful, more contrasting, more elegant
... a little bland ... I like the sky now"; "the building may have too many windows, cut the windows by 35 % but keep the
consistency and detail"; "the red giant planet should be about 4x bigger"; the docs/167 billboards delivered):
  * BILLBOARDS: art/sky3d/billboards/ad_01..12.png (the docs/167 drop at 512 px) on 75 % of the ad screens, each screen wearing an
    image of its OWN orientation (screen_mi: wide / tall / square), at E_SCREEN x1.6 so the dark ads read beside the mosaic.
  * WINDOWS: lit fraction 0.26 -> 0.169 (-35 %); the grid, the frames, the lobby rows and the tint rules are unchanged.
  * THE RED GIANT: `ruby` r 2.4 -> 9.6 deg (19 deg across, the biggest body in the sky), crimson / blood-orange bands, a thin
    dark-red ring, two moons, x1.25 brighter (bd['gain']). Red is otherwise still the moon's, the sign's and THE ORIGIN's.
  * COLOUR: jewel-tone nebula (NEB_*: the v4i pink and orange read dusty tan), a deep blue band, NEB_GAIN 1.45, deeper voids
    (SKY_GLOW more violet); the neon weights cover the whole range (magenta / violet up with the cyan), the window-tint rows too;
    half the districts light their streets in neon and three core rings glow magenta / cyan / violet between the amber ones.
  * CONTRAST: BODY_FLOOR x0.7 (deeper near-black bodies), E_PANEL 0.64; the fog's scatter grades warm at the street to
    violet-magenta above FOG_H0; the high haze is violet-blue. finish_sky.py --sat is the grade on top (the mean is re-held).
  * THE SPIRE CLUSTER (v6b; user, on the v6a preview: "our buildings look like New York buildings ... they should really reference
    the ones I sent"): nearly every tower over 90 m is a CLUSTER - a tapered core of 3..5 frustum segments (Acc.loft) ending in a
    lit NEEDLE, 2..5 satellite spires clustered round it, 0..3 giant CRYSTAL slabs (mat_crystal) standing on its faces, neon SEAMS
    up every edge following the taper, a COLLAR at every break, a halo ring on a third of the tall ones, greebles on the lower
    body; the facade (style >= 2) is dark metal with thin light ROWS every four floors and fine vertical GROOVES in the hue, the
    windows dim and few. The low blocks keep the v5 box tiers (the references' foreground has them).

v7 — THE TITLE GATE (user, 2026-09-29, with one reference image: "improve the cybercity 2 sign ... a very bright neon sign with
cyber designs all over it ... follow the reference exactly ... until it's indistinguishable"; docs/166 §9):
  * THE SIGN IS THE REFERENCE: the user's painting cut out of its background (tools/sky3d/cut_title_gate.py, art/sky3d/sign/) on
    ONE emissive card facing the camera, 1 km out, its text box at az 0 el 11 (GATE, make_title_gate); colours decoded so the
    FINISHED sky shows the painting's own pixels; the neon's glow rebuilt as added light. --sign-style gantry = the v2..v6 plate.
  * THE MOON: the visible disc + halo moved to where the reference's moon peeks out behind the crest (MOON_DISC) in the
    reference's pale lavender (MOON_STYLE; --moon-style blood = the red); the moonlight and moon_dir() are unchanged.
  * --region az0,az1,el0,el1 renders one window of the equirect (a cropped border render) for fast sign checks.

v7b — THE HERO SIGN + NO SHIPS (user, 2026-09-29, after seeing v7 in game: "25% bigger and it needs to be way brighter ... the
one thing that sticks out in the skybox"; and: "remove all the spaceships ... we have another agent adding actual models into the
sky"; docs/166 §9.7):
  * THE SIGN 25 % BIGGER (GATE w_deg 52 -> 65; the text box stays at el 11) and authored in W like the rest of the sky (white 1.0,
    was the preview's display white 0.1467), its neon x3 on top (neon / neon_lo / neon_hi), its halo at 3 W (glow); it writes the
    'sign' AOV (Render Layers -> File Output -> <raw>.sign.exr) so finish_sky.py gives it its own knee (2 -> 4 W, the city's stays
    0.7 -> 1 W) and solves the exposure outside it. Camera rays + glossy reflections only (lights=False): it lights nothing.
  * THE MOON follows the gate (moon_disc(): MOON_REF in the texture's pixels, through the card), so it still peeks out behind the
    crest at the new size.
  * THE SHIPS ARE RETIRED: the airships, battlecruisers, fighters and loose aircraft (the sky fleet, docs/192, flies real models
    now). retired() still runs their builders for the random draws and deletes the result, so everything after them (the
    searchlights) stays where v7 put it; --ships brings them back for an A/B. --device cpu renders a test without the GPU.

v7c — NO ASTEROIDS (user, 2026-09-29: "we're going to add actual asteroid models going through the sky so then we need to remove the
static ones"): every static rock is retired the same way — the belt (~220), the drifting rocks (90) and the two black holes' debris
fields (~290). scatter_rocks() builds nothing while their callers still spend the same random draws, so nothing else moves; the black
holes keep their discs, lensed halos, jets and streams. --asteroids = the A/B.

v2 — THE CYBER PASS (user, on the first render: "a lot cleaner, the depth is really nice ... but we lost
the cyber feeling: no extremely high skyscrapers, the sky is dull, the upper half is empty, no planets /
black holes / starships, the red is orange, the colours mesh together ... one super tall building with
thunderclouds around it where all the evil started"). Everything below is additive to v1's city:
  * SUPERTALLS: ~46 procedural megatowers (900..2600 m, seven silhouettes: spire / drum stack / twins with
    skybridges / blade with a giant screen / ziggurat / saucer / wedding cake) at 1.3..11 km, plus 14 far-ring
    megastructures 2.5..6 km tall at 13..24 km — towers now reach 25..45 deg up, not 15.
  * THE ORIGIN: a 4 km black spire on an island in the harbour, crimson veins and collars, a spiked crown
    with a red eye, a RING OF THUNDERCLOUDS (a real volume) lit from inside with lightning bolts.
  * THE SKY: a violet-black zenith over a crimson horizon; two star layers, a milky-way band, crimson +
    violet nebula with dust lanes; a ringed GIANT low over the far shore, a moonlet, RUST and ICE planets;
    GARGANTUA (edge-on black hole, lensed arch, photon ring) and THE MAELSTROM (face-on, spiral disc,
    polar jets) — all real geometry at BODY_D, lit by a fake terminator toward the moon.
  * RAILS: four monorail lines on tall pylons with lit trains and stations (THE SKYRAIL sweeps the right
    half of the sky at 15 deg on 400 m pylons; THE WESTLINE bridges the harbour; THE LOOP circles the
    plaza below the horizon; THE FARLINE behind).
  * SHIPS: two airships with holo billboards, a capital starship with engine glow, four fighters, air lanes.
  * CYBER: holographic panels floating over the roofs, neon on far more towers (edge tubes, collars,
    outlines), searchlight cones and laser bars as geometry, the orbital tether + station, per-district
    street hues (sodium / cool / red / magenta / violet), a saturated window palette (crimson, magenta,
    violet, cyan, gold), crimson fog and clouds (the orange is gone), a thin haze above the fog so the far
    megastructures fade with distance.
  * THE SIGN: "TOWER OF DOOM" crimson, "II" gold, "FALLEN CYBERCITY" cyan (Agency FB) with two flickering
    letters, a backlight panel, a double neon border.
  --skip tokens added: mega,origin,storm,rails,holo,lanes,tether,bodies,ships,beams,lasers,haze

WHAT THIS IS. The map's sky is one 8192x4096 lat-long HDR on the stock dome (docs/104).
Until today that picture was DRAWN by tools/gen_tod_sky.js: boxes, lines, an analytic fog
rule. This script builds the cybercity as REAL 3D GEOMETRY in Blender — thousands of
buildings with setbacks, crowns, screens and neon on a street lattice, elevated ring
highways, a harbour, the title gantry, a blood moon — and lets Cycles do what the
rasteriser never could: real perspective from a camera 220 m up (so the city continues
BELOW the horizon, all the way to the nadir), occlusion, moonlight and shadow, glossy
glass, wet streets, and a physically scattering fog volume that turns every window and
sign into light pollution and fades the far city into haze. The output is a raw LINEAR
equirectangular EXR; tools/sky3d/finish_sky.py turns it into the game asset (exposure
solve, peak knee, previews, seam check) — read that file for the exposure contract.

ORIENTATION (measured 2026-09-24, tools/sky3d test): with the camera at rotation
(90,0,0) the centre column looks along +Y, +X is image RIGHT, the zenith is row 0. The
moon, the sign and the hero skyline stand on +Y = the image's centre column.
⚠️ IN GAME (session 61, 2026-09-29, the engine's sky shader + a screenshot rebuilt from the
.map, docs/196 §3): the centre column faces world yaw -(SSI sun azimuth + skyRotation), image right =
the viewer's right (not mirrored); our SSI sun azimuth is 140. Ship --roll 0 and let the material's
skyRotation (40 = the gate due WEST, where the jump reveal looks) do the turn; test_jumppad checks it.

RUN
  "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe" -b --factory-startup \
      -P tools/sky3d/build_city.py -- [--width 2048] [--samples 64] [--seed 7] [--cam-h 220]
      [--detail 1.0] [--out raw.exr] [--save-blend art/sky3d/tod2_sky.blend] [--no-render]
      [--skip fog,clouds,streets,neon,screens,sign,moon,highways,search,air,water,far,landmarks]
  The one-command wrapper is tools/sky3d/render_sky3d.ps1.

UNITS: metres. Camera at (0, 0, CAM_H). The tower itself is NOT in the picture (the game
world provides it); nothing stands within R_INNER of the camera.
"""
import bpy, math, random, sys, time, os, json
import numpy as np
from mathutils import Vector, Matrix

T0 = time.time()
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(k, d=None):
    if k in ARGS:
        i = ARGS.index(k)
        return ARGS[i + 1] if i + 1 < len(ARGS) else d
    return d


def flag(k):
    return k in ARGS


HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from cyber_architecture import build_cyber_block, make_cyber_material
from cyber_coverage import modernize_lot
from cyber_title import make_cyber_title
from ominous_title import make_ominous_title
from cyber_hero_title import make_cyber_hero_title
from city_composition import plan_lots, key as lot_key, band as distance_band, keep_mega, station_conflict, title_conflict
from sky_simplify import object_is_retired, select_secondary, STAR_GATES, NEBULA_POLICY, QUIET_SECTORS, CELESTIAL_COUNTS
from cyber_station import station_plan, make_cyber_station
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SCRATCH = os.path.join(os.environ.get('TEMP', '/tmp'), 'tod_sky3d')
os.makedirs(SCRATCH, exist_ok=True)

SEED = int(arg('--seed', '7'))
WIDTH = int(arg('--width', '2048'))
HEIGHT = WIDTH // 2
SAMPLES = int(arg('--samples', '64'))
CAM_H = float(arg('--cam-h', '220'))
DETAIL = float(arg('--detail', '1.0'))
OUT = arg('--out', os.path.join(SCRATCH, f'raw_{WIDTH}.exr'))
BLEND = arg('--save-blend', None)
NO_RENDER = flag('--no-render')
SKIP = set((arg('--skip', '') or '').split(',')) - {''}
SCREENS_DIR = arg('--screens-dir', None)              # a folder of PNG/JPG billboards (docs/167); 75 % of the ad screens wear one
SIGN_STYLE = arg('--sign-style', 'cyber_hero')        # approved middle ground; older styles remain historical A-B options
SIGN_STATE = arg('--sign-state', 'lit')              # 2026-09-30 (docs/196 s6): 'dull' bakes the cyber_hero gate UNLIT (the first jump's
                                                      # client card lights it after the crash); 'lit' = the v10 bake, kept for A/B renders
GATE_TEX = arg('--gate-tex', os.path.join(REPO, 'art', 'sky3d', 'sign', 'tod2_title_gate.png'))
MOON_STYLE = arg('--moon-style', 'reference')       # v7: 'reference' = the user's reference's pale lavender moon behind the gate's crest (docs/166 §9); 'blood' = the v4..v6 red moon
REGION = arg('--region', None)                        # v7: 'az0,az1,el0,el1' (deg) renders only that window of the equirect (a cropped border render) for fast sign checks
DEVICE = arg('--device', 'gpu')                       # v7b: 'cpu' renders without the GPU (tests while the game runs); the ship is always 'gpu'
SHIPS = flag('--ships')                               # v7b: the airships, battlecruisers, fighters and loose aircraft are RETIRED (user 2026-09-29: the sky
                                                      # fleet flies real ship models through the map now - no static ships in the picture); --ships = the v7 A/B
ROCKS = flag('--asteroids')                           # v7c: every static ROCK is RETIRED too - the belt, the drifting rocks, the black holes' debris (user
                                                      # 2026-09-29: real asteroid models will fly through the sky); --asteroids = the A/B
RETIRED_ROCKS = [0]


def on(feature):
    return feature not in SKIP


rng = random.Random(SEED)
nprng = np.random.default_rng(SEED)
D2R = math.pi / 180


_LOG_MUTE = []                                        # v7b: retired() mutes the builders it runs only for their random draws


def log(*a):
    if _LOG_MUTE:
        return
    print(f'[sky3d {time.time() - T0:6.1f}s]', *a, flush=True)


# ---------------------------------------------------------------- composition
MOON_EL, MOON_R_DEG, MOON_D = 16.0, 5.5, 30000.0     # the blood moon: dead ahead (+Y), 16 deg up, 11 deg across (docs/150)
MOON_DISC = dict(az=8.0, el=41.0, r=5.1)             # v9: another 2 degrees clears the taller skull crest; moonlight direction stays fixed
                                                      # (its centre and radius measured on the reference, carried through the card's frame); the moonlight
                                                      # and moon_dir() keep MOON_EL at az 0, so no body's shading moves. v7b: the fallback only — the disc is
                                                      # placed through the card by moon_disc() from MOON_REF, so it follows GATE's size and height
MOON_REF = dict(u=690.8, v=268.4, r=134.6)            # v7b: that moon in the gate texture's own pixels (the padded canvas; = reference px 643, 140, r 135)
SIGN_D, SIGN_EL = 1000.0, 11.0                        # the title gantry: 1 km ahead, its centre 11 deg up — the moon rises behind it
# v7 THE TITLE GATE (user 2026-09-29, the reference image: "follow the reference exactly ... until it's indistinguishable"; docs/166 §9).
# The sign IS the user's painting, cut out of its background (tools/sky3d/cut_title_gate.py -> GATE_TEX, RGBA, straight alpha,
# display-referred colours) on ONE emissive card that faces the camera. A skybox is seen from one point, so a flat card at the
# right distance is indistinguishable from modelled geometry, and it is the only way the lettering, the skull and the banners can
# be the reference's own. The card stands in the city 1 km out: the core's buildings in front of it hide its feet, the ones behind
# it show through its arch. Colours: the finish maps W to the display through its gain x display-mult (docs/166 §6.4), so the
# texture's display value 1.0 is emitted at GATE['white'] W and the finish's --sat is divided out first — the finished sky then
# shows the card with the reference's own colours (finish_sky.py's previews decode with a pure 2.2, so the card encodes with it).
# v7b THE HERO SIGN (user 2026-09-29, after seeing v7 in game: "a little bit bigger like 25% bigger and it needs to be way brighter
# ... it should be the one thing that sticks out in the skybox ... not even close to how bright it should be"; docs/166 §9.7).
# v7 emitted the painting's white at 0.1467 W, the PREVIEW's display white; every other emitter in this sky is authored in W, so the
# sign stood 6.8x under the city's neon. Now its white IS W (the city's own unit), its neon (the painting's brightest pixels) is
# pushed `neon` x higher, and the card writes the 'sign' AOV so finish_sky.py lifts it OUT of the city's knee (0.7..1.0 W): the
# sign's neon peaks above everything else in the sky, while the city is finished exactly as before.
GATE = dict(
    box_el=11.0,            # the text box centre's elevation (deg) — the jump-pad reveal camera aims here (session 61's _tod_jumppad.gsc)
    box_uv=(0.5, 0.3637),   # the text box centre in the texture, fractions from the top-left (reference px 724, 395 of 1448 x 1086)
    D=1000.0,               # m from the camera to the card along the view to the box centre
    w_deg=65.0,             # the texture's full width (deg) at the box centre's distance (v7 52; v7b x1.25, user: "25% bigger")
    white=1.0,              # W per display 1.0 of the painting (v7 0.1467 = the preview's display white: 6.8x dimmer than the city's neon)
    neon=3.0,               # v7b: the painting's neon x this on top of `white` (3 W peaks; the city's knee caps its own at 1 W)
    neon_lo=0.55,           # v7b: ... ramped in on the painting's max channel (display) from here
    neon_hi=0.95,           #      to here (the white-hot cores and the saturated tubes: ~20 % of the silhouette)
    glow=3.0,               # v7b: the rebuilt halo (the _glow texture) in W per display 1.0 — it scales with the tubes it belongs to
    mask_glow=2.0,          # v7b: the 'sign' AOV = alpha + this x the glow's max channel (so the strong halo leaves the city's knee too)
    lights=False,           # v7b: False = the card is seen by camera rays only (it lights no fog, no tower, no street); True = a mesh light
    sign_state=SIGN_STATE,  # 2026-09-30: 'lit' / 'dull' (cyber_hero_title.py; the dull bake is the first jump's DARK sign, docs/196 s6)
    sat=1.2)                # the ship's finish --sat: divided out of the card so the finished colours are the reference's
LANE_HALF, LANE_EL, LANE_EL_NEAR = 26.0, 9.5, 5.5     # toward the moon the skyline is capped under 9.5 deg (5.5 in front of the sign, r < 1.4 km) so the moon and sign stand clear
BAY = (-152.0, -98.0)                                 # the harbour: azimuth range (deg; 0 = +Y hero, +90 = +X = image right)
BAY_R = (1300.0, 9000.0)                              # water between these radii; the far shore's city resumes beyond
R_INNER = 380.0                                       # the tower's own plaza: nothing closer
R_CORE = 1430.0                                       # v5 THE CORE: ring roads + radial boulevards + polar lots out to here; the square districts start beyond (docs/166 §7)
LOT_P = (320.0, 640.0, 1280.0)                        # v5: lot pitch per band (v4: 140 / 280 / 560) — a fifth of the buildings at three times the size (user: "too many ... make them three times as big")
CORE_BANDS = [(128.0, 210.0, 26.0), (246.0, 296.0, 42.0), (384.0, 530.0, 90.0), (570.0, 770.0, 160.0), (810.0, 1080.0, 250.0), (1120.0, 1400.0, 300.0)]   # r0, r1, median height: the core's lot rings — low at the foot, rising into the city so the circle BLEEDS into the grid
CORE_ROADS = [(58.0, 9.0, 0.8), (110.0, 10.0, 0.52), (228.0, 12.0, 0.5), (364.0, 14.0, 0.48), (550.0, 16.0, 0.44), (790.0, 16.0, 0.4), (1100.0, 18.0, 0.34), (1420.0, 20.0, 0.28)]   # ring roads: radius, width, brightness relative to a street (v5b/c: dimmer — they were the picture)
CORE_RADIALS, CORE_RADIAL_W = 12, 14.0                # radial boulevards from the forecourt to the last ring road
R_CITY = 26000.0
FOG_R, FOG_TOP, FOG_RATE = 42000.0, 700.0, 0.012      # the fog box (m) and its material step rate (v4d: the box top 1100 -> 700 m so the sky rays leave it fast)
FOG_D0, FOG_H0 = 1.0e-5, 220.0                        # v4g: the references have no veil; this is only the far horizon's warm band (OD 0.2 over 20 km)
HAZE_TOP, HAZE_D = 4500.0, 3.0e-6                     # v4e: a whisper of blue
RINGS = [(2300.0, 26.0, 28.0), (5200.0, 34.0, 34.0)]  # elevated ring highways: radius, deck height, deck width
DOWNTOWN = [(5600.0, 55.0, 2000.0, 2.6), (6800.0, -62.0, 2300.0, 2.2), (9500.0, 152.0, 2600.0, 2.0)]   # r, az, radius, height boost
BODY_D = 40000.0                                      # v2: the planets and black holes stand here — beyond the moon, above the fog, behind the clouds

# ---- v2 THE CYBER PASS (2026-09-25; user: "we lost the cyber feeling ... the height ... planets, black holes, starships ...
#      one super tall building with thunderclouds around it where all the evil started ... the colours are dull, they mesh together")
ORIGIN = dict(az=-140.0, r=4000.0, h=4000.0, storm_z=(1250.0, 2750.0), storm_r=(700.0, 2000.0), storm_d=0.012)   # THE ORIGIN; storm_d = cumulonimbus extinction (1/m; v4h thin enough that the lights inside show through)
MEGA_HERO = [  # az, r, h, kind, hue — the named supertalls; MEGA_N more are rolled around them (v4: red is reserved for the moon / sign / origin; v5: x1.3 taller)
    (118.0, 2600.0, 3000.0, 'spire', 'magenta'), (172.0, 2200.0, 2200.0, 'drum', 'cyan'), (-72.0, 3100.0, 1950.0, 'twins', 'cyan'),
    (52.0, 4200.0, 1400.0, 'ziggurat', 'orange'), (-40.0, 2400.0, 1600.0, 'blade', 'violet'), (95.0, 1700.0, 1150.0, 'saucer', 'gold'),
    (145.0, 3400.0, 2100.0, 'cake', 'green'), (-118.0, 10800.0, 3200.0, 'spire', 'cyan'), (-166.0, 6200.0, 2400.0, 'twins', 'magenta')]
MEGA_N = 38                                           # rolled supertalls (650..2600 m) at 1.3..11.5 km, outside the moon lane and the water
FAR_MEGA_N = 14                                       # far-ring megastructures at 13..24 km, 2.5..6 km tall: the city that keeps going
RAIL_LINES = [  # centre az, centre distance, radius, deck z, hue, trains, stations
    (89.0, 5143.0, 4500.0, 400.0, 'gold', 3, 2),      # THE SKYRAIL: sweeps the right half of the sky (az 28..150) on 400 m pylons; its near point 643 m out at 15.6 deg
    (-95.0, 4000.0, 3200.0, 300.0, 'cyan', 2, 2),     # THE WESTLINE: az -148..-42, bridges the harbour on pylons in the water
    (0.0, 0.0, 1420.0, 150.0, 'magenta', 2, 3),       # THE LOOP: a monorail over the core's last ring road (v5: was r 1000, through the core's towers now)
    (170.0, 7000.0, 4200.0, 260.0, 'violet', 2, 1)]   # THE FARLINE: behind the tower
SHIP_DEFS = [  # az, d, z, hull length, hull neon hue, billboard hue — dirigibles
    (108.0, 2300.0, 1300.0, 700.0, 'magenta', 'cyan'), (-30.0, 5200.0, 2400.0, 1100.0, 'cyan', 'gold'), (165.0, 3200.0, 1700.0, 850.0, 'violet', 'orange')]
STARSHIPS = [  # az, d, z, length, heading offset from broadside (deg) — battlecruisers (v5: 1.5..2x longer, one more; user: "barely tell it's a spaceship ... bigger")
    (72.0, 3800.0, 2400.0, 1300.0, 28.0), (-158.0, 6000.0, 2800.0, 1000.0, -25.0), (104.0, 5000.0, 4100.0, 1400.0, 20.0), (-95.0, 6600.0, 4900.0, 1100.0, -40.0),   # v5c: the first under the black hole, clear of the heroes
    (-45.0, 4500.0, 2600.0, 1100.0, 55.0)]
TETHER = dict(az=100.0, d=14000.0, anchor_h=1600.0, station_el=47.0, top_h=170000.0)   # the orbital tether: an anchor megatower, a cable to the zenith, a wheel station
BODIES = [  # v4 THE REFERENCE COPY: az / el (deg) from the camera, angular radius r (deg); the keys per kind are read by make_bodies
    # gas giants: swirled latitude bands in `cols`, a storm `spot`, a ring (inner, outer, -, colour stops), an atmosphere limb, moons (dx, dy, radius) in R
    dict(kind='gas', name='giant', az=-98.0, el=49.0, r=8.0, tilt=0.38, bands=11,
         cols=[(0.95, 0.55, 0.18), (0.70, 0.15, 0.05), (0.10, 0.45, 0.60), (0.98, 0.80, 0.50)], spot=(0.95, 0.22, 0.06),
         ring=(1.30, 2.40, 0.0, [(0.0, (0.95, 0.80, 0.58)), (0.45, (0.85, 0.70, 0.55)), (0.62, (0.55, 0.35, 0.80)), (1.0, (0.45, 0.30, 0.75))]),
         atmo=(1.0, 0.55, 0.30), moons=[(1.9, 0.55, 0.14), (-2.6, -0.3, 0.09)]),
    dict(kind='gas', name='cool', az=140.0, el=52.0, r=6.0, tilt=0.22, bands=13,
         cols=[(0.12, 0.35, 0.75), (0.90, 0.82, 0.62), (0.92, 0.50, 0.15), (0.15, 0.62, 0.78)], spot=(0.98, 0.92, 0.80),
         ring=(1.35, 1.95, 0.0, [(0.0, (0.90, 0.85, 0.75)), (0.5, (0.75, 0.70, 0.62)), (1.0, (0.60, 0.55, 0.50))]),
         atmo=(0.55, 0.80, 1.0), moons=[(-1.6, 0.7, 0.11)]),
    # cracked planets: dark rock (two colours) split by glowing fissures in `vein`
    dict(kind='cracked', name='ember', az=32.0, el=55.0, r=2.8, rock=((0.30, 0.12, 0.28), (0.55, 0.22, 0.45)), vein=(1.0, 0.45, 0.10), moons=[(1.6, 0.5, 0.16)]),
    dict(kind='cracked', name='brown', az=-60.0, el=44.0, r=6.5, rock=((0.42, 0.26, 0.14), (0.70, 0.48, 0.26)), vein=(0.10, 0.90, 1.0), moons=[(1.7, -0.5, 0.11), (-1.9, 0.6, 0.07)]),
    dict(kind='cracked', name='verdant', az=-137.0, el=52.0, r=2.4, rock=((0.08, 0.16, 0.40), (0.20, 0.32, 0.55)), vein=(0.20, 1.0, 0.40), moons=[]),
    # a small ringed planet
    dict(kind='moon', name='ringlet', az=-150.0, el=40.0, r=1.5, tilt=0.5, cols=((0.22, 0.50, 0.28), (0.55, 0.35, 0.72)),
         ring=(1.4, 2.3, 0.0, [(0.0, (0.70, 0.45, 0.95)), (1.0, (0.50, 0.30, 0.80))]), moons=[]),
    # THE black hole: r = the shadow's radius; the spiral disc runs to disc_out x R, seen obliquely (tilt from face-on), with a debris field,
    # polar jets (`jet` colour), tidal `streams`, and the lensed far side over and under the shadow (v5)
    dict(kind='hole', name='gargantua', az=75.0, el=55.0, r=3.6, tilt=1.05, disc_out=5.5, arms=2, debris=150, streams=8, jet=(0.45, 0.65, 1.0),
         col_hot=(1.0, 0.92, 0.75), col_mid=(1.0, 0.50, 0.18), col_far=(0.85, 0.22, 0.38), col_edge=(0.16, 0.06, 0.40)),
    # spiral galaxies (face-on discs, a little inclined)
    dict(kind='galaxy', name='andromeda', az=-40.0, el=60.0, r=3.6, tilt=0.35, arms=2, core=(0.98, 0.90, 1.0), arm=(0.40, 0.42, 0.98), knot=(0.95, 0.35, 0.65)),
    dict(kind='galaxy', name='whirl', az=170.0, el=70.0, r=2.4, tilt=0.15, arms=2, core=(1.0, 0.95, 0.90), arm=(0.62, 0.35, 0.95), knot=(0.30, 0.85, 1.0)),
    # ---- v5 THE BIG CITY (user: "the sky is a bit empty ... more planets in the distance to show off the depth ... double what we have")
    dict(kind='gas', name='ice', az=130.0, el=64.0, r=3.2, tilt=-0.3, bands=9, cols=[(0.30, 0.75, 0.85), (0.15, 0.35, 0.80), (0.80, 0.92, 1.0), (0.45, 0.30, 0.85)], spot=(0.95, 0.98, 1.0),
         ring=(1.25, 1.75, 0.0, [(0.0, (0.75, 0.90, 1.0)), (1.0, (0.45, 0.55, 0.85))]), atmo=(0.45, 0.85, 1.0), moons=[(1.5, -0.6, 0.10)]),
    # v6 THE RED GIANT (user: "the red giant planet should be about 4x bigger"): r 2.4 -> 9.6 deg = 19 deg across, the biggest body in the
    # sky, high over the moon lane; crimson / blood-orange bands with one pale gold band, a thin dark-red ring, two moons, x1.25 brighter
    dict(kind='gas', name='ruby', az=-20.0, el=47.0, r=9.6, tilt=0.5, bands=9, cols=[(0.55, 0.02, 0.04), (0.95, 0.12, 0.05), (0.30, 0.01, 0.03), (0.85, 0.30, 0.10), (0.70, 0.04, 0.08)], spot=(1.0, 0.45, 0.20),
         ring=(1.22, 1.62, 0.0, [(0.0, (0.80, 0.18, 0.12)), (0.45, (0.50, 0.08, 0.08)), (0.62, (0.25, 0.03, 0.05)), (1.0, (0.45, 0.07, 0.09))]),
         atmo=(1.0, 0.15, 0.08), moons=[(-1.7, 0.4, 0.12), (1.45, -0.55, 0.07)], gain=1.25),   # v6c: crimson, broad bands (v6b read orange)
    dict(kind='gas', name='jade', az=-176.0, el=31.0, r=1.9, tilt=0.15, bands=9, cols=[(0.35, 0.75, 0.40), (0.85, 0.90, 0.70), (0.15, 0.50, 0.35), (0.95, 0.80, 0.45)],
         ring=(1.35, 2.1, 0.0, [(0.0, (0.80, 0.85, 0.70)), (1.0, (0.50, 0.60, 0.45))]), atmo=(0.6, 1.0, 0.7), moons=[]),
    dict(kind='gas', name='dusk', az=18.0, el=64.0, r=1.1, tilt=0.3, bands=7, cols=[(0.30, 0.20, 0.70), (0.70, 0.45, 0.90), (0.20, 0.35, 0.80)], atmo=(0.5, 0.4, 1.0), moons=[], dim=0.6),
    dict(kind='gas', name='far_giant', az=-165.0, el=58.0, r=0.8, tilt=0.4, bands=9, cols=[(0.95, 0.60, 0.30), (0.60, 0.25, 0.10), (0.95, 0.85, 0.60)],
         ring=(1.3, 2.0, 0.0, [(0.0, (0.9, 0.8, 0.6)), (1.0, (0.6, 0.5, 0.4))]), moons=[], dim=0.5),
    dict(kind='cracked', name='obsidian', az=151.0, el=64.0, r=1.7, rock=((0.06, 0.05, 0.10), (0.18, 0.14, 0.24)), vein=(1.0, 0.20, 0.70), moons=[]),
    dict(kind='cracked', name='sulfur', az=-82.0, el=68.0, r=1.4, rock=((0.35, 0.28, 0.10), (0.60, 0.50, 0.20)), vein=(1.0, 0.85, 0.20), moons=[(1.5, 0.3, 0.12)]),
    dict(kind='cracked', name='far_ember', az=52.0, el=72.0, r=0.7, rock=((0.30, 0.12, 0.28), (0.55, 0.22, 0.45)), vein=(1.0, 0.45, 0.10), moons=[], dim=0.55),
    dict(kind='moon', name='grey', az=5.0, el=53.0, r=2.3, tilt=0.2, moons=[]),
    dict(kind='moon', name='dust', az=-118.0, el=25.0, r=0.9, cols=((0.40, 0.30, 0.25), (0.70, 0.58, 0.50)), moons=[]),
    dict(kind='moon', name='far_a', az=160.0, el=48.0, r=0.6, cols=((0.25, 0.28, 0.40), (0.55, 0.60, 0.75)), moons=[], dim=0.6),
    dict(kind='moon', name='far_b', az=30.0, el=80.0, r=0.5, moons=[], dim=0.55),
    dict(kind='moon', name='far_c', az=96.0, el=38.0, r=0.7, cols=((0.45, 0.25, 0.20), (0.75, 0.55, 0.45)), moons=[], dim=0.6),
    dict(kind='hole', name='maelstrom', az=-12.0, el=70.0, r=1.3, tilt=1.25, disc_out=6.0, arms=3, debris=45, streams=5, dim=0.85, jet=(0.85, 0.65, 1.0),
         col_hot=(0.85, 0.95, 1.0), col_mid=(0.35, 0.75, 1.0), col_far=(0.30, 0.30, 0.95), col_edge=(0.15, 0.05, 0.40)),
    dict(kind='galaxy', name='edge', az=120.0, el=78.0, r=2.2, tilt=1.35, arms=2, core=(1.0, 0.92, 0.80), arm=(0.85, 0.60, 0.95), knot=(1.0, 0.45, 0.60)),
    dict(kind='galaxy', name='sombrero', az=-110.0, el=74.0, r=1.5, tilt=0.95, arms=2, core=(1.0, 0.95, 0.85), arm=(0.50, 0.55, 1.0), knot=(0.40, 0.95, 0.90)),
    dict(kind='comet', name='harbinger', az=-72.0, el=57.0, r=0.25, tail=14.0, col=(0.60, 0.90, 1.0))]
ASTEROIDS_DRIFT = 90                                  # loose rocks in the upper sky besides the black holes' debris (v5: 60 -> 90)
ASTEROID_BELT = dict(n=220, az0=40.0, az1=200.0, el0=24.0, bulge=26.0, spread=2.5)   # v5 THE BELT: a band of rocks arcing from az 40 over the right sky to az -160

# emission strengths (linear; only the RATIOS matter — finish_sky.py solves the absolute exposure)
E_WIN, E_NEON, E_SCREEN, E_TRAIL, E_BEACON, E_MOON, E_CLOUD, E_SIGN, E_SODIUM, E_ROAD, E_HALO = 0.70, 0.90, 0.65, 0.85, 1.2, 0.80, 0.02, 1.8, 0.3, 0.32, 0.20   # v4g: windows at the references' (221,140,59)
E_HOLO, E_PLANET, E_RING, E_HOLE, E_JET, E_BEAM, E_LASER, E_BOLT = 1.0, 0.13, 0.085, 0.55, 0.5, 0.40, 0.9, 1.8
# Consistency pass: celestial surfaces retain headroom for bands/craters. These
# are local authored radiances; native exposure and city/sign calibration stay put.
# v4 (docs/166): the units are W = DISPLAY WHITE. A neon tube at 1.0 is the references' white-hot core; a window at 0.9; a
# panel field at 0.42; the space floor at 0.01..0.03; nothing in the picture below the painted ambient BODY_FLOOR. Only the
# RATIOS reach the game — finish_sky.py --white 1.0 maps W to the display and keeps the docs/104 mean contract.
E_SIGIL, E_GALAXY, E_ROCK, E_PANEL, E_PLINE, E_GROUND, E_GGRID, E_RIBBON, E_FALL = 0.9, 0.18, 0.40, 0.45, 0.85, 0.08, 0.15, 0.50, 0.60   # Celestial core detail; city emission remains unchanged.
E_CRYSTAL = 1.10                                   # v6b: the references' giant lit CRYSTAL slabs on the spires (mat_crystal)
PANEL_FRAC = 0.60                                  # v5b: six towers in ten wear neon panels; the rest are dark window towers (the references' dark mass)
BODY_FLOOR = (0.0050, 0.0035, 0.0085)              # v6: x0.7 and bluer — deeper near-black bodies (user: "more contrasting"); v4e (0.007, 0.005, 0.010) = the references' (22,18,26)
BODY_ALBEDO = (0.012, 0.010, 0.018)                # v4i: matte near-black
WIN_AMBER, WIN_GOLD, WIN_COOL = (0.76, 0.30, 0.07), (0.85, 0.50, 0.12), (0.45, 0.60, 0.90)   # v4d: measured (221,140,59)
WIN_ICE, WIN_CYAN, WIN_VIOLET, WIN_PINK, WIN_GREEN = (0.50, 0.70, 1.0), (0.22, 0.80, 0.95), (0.55, 0.35, 0.95), (0.95, 0.35, 0.70), (0.35, 0.95, 0.55)   # v5: the window tint follows the tower's hue row — amber is one row of ten, not the city's colour (user: "a colour that's so dominant")
GROUND_GLOW = (0.55, 0.30, 0.10)
SKY_HORIZON, SKY_MID, SKY_HIGH, SKY_ZENITH = (0.0020, 0.0025, 0.010), (0.0012, 0.0015, 0.006), (0.0008, 0.0008, 0.003), (0.0006, 0.0006, 0.002)   # v4e: the base is the references' VOID (3,2,6); the indigo comes as patches (SKY_GLOW)
NEB_MAGENTA, NEB_PINK, NEB_VIOLET, NEB_ORANGE, NEB_TEAL, NEB_BLUE = (0.50, 0.03, 0.20), (0.62, 0.06, 0.30), (0.16, 0.04, 0.55), (0.80, 0.16, 0.02), (0.02, 0.32, 0.48), (0.04, 0.12, 0.60)   # v6: jewel tones (v4i's pink + orange read dusty tan) and a deep blue band
NEB_GAIN = 1.45                                     # v6: 1.3 -> 1.45 (1.7 was a brown cloudscape)
SKY_GLOW = (0.012, 0.010, 0.072)                   # v4e: the patchy indigo / blue-violet regions (17,23,54)..(28,34,75) round the nebulae
NEB_CORES = [(75.0, 55.0, 1.2), (-40.0, 60.0, 0.7), (170.0, 70.0, 0.5)]   # az, el, gain: the nebula burns brighter round the black hole and the galaxies
FOG_SCATTER, FOG_ABSORB = (0.95, 0.78, 0.60), (0.90, 0.82, 0.78)
FOG_SCATTER_HI = (0.72, 0.42, 1.0)                 # v6: the fog's scatter grades warm at the street to violet-magenta above FOG_H0 (user: "more elegant")
HAZE_SCATTER = (0.42, 0.36, 0.98)                  # v6: violet-blue distance (v4: sky-blue)

PAL = {  # linear RGB, chroma only (the strength is the E_ constant)
    'red': (1.0, 0.05, 0.04), 'crimson': (1.0, 0.02, 0.07), 'ember': (1.0, 0.30, 0.05), 'orange': (1.0, 0.32, 0.08), 'magenta': (1.0, 0.06, 0.65),
    'pink': (1.0, 0.15, 0.50), 'violet': (0.36, 0.06, 1.0), 'blue': (0.20, 0.30, 1.0), 'cyan': (0.04, 0.75, 1.0), 'ice': (0.75, 0.92, 1.0), 'gold': (1.0, 0.70, 0.15),
    'warm': (1.0, 0.72, 0.42), 'cool': (0.72, 0.82, 1.0), 'sodium': (0.95, 0.36, 0.08), 'coolroad': (0.55, 0.68, 0.95), 'redroad': (0.95, 0.14, 0.10),
    'magroad': (0.90, 0.18, 0.50), 'violetroad': (0.50, 0.20, 0.95), 'white': (1.0, 0.95, 0.88), 'beacon': (1.0, 0.04, 0.02), 'tail': (1.0, 0.06, 0.03),
    'head': (1.0, 0.85, 0.65), 'green': (0.03, 1.0, 0.38)}
NEON_W = [('cyan', 20), ('blue', 7), ('magenta', 20), ('violet', 17), ('green', 10), ('orange', 8), ('pink', 9), ('gold', 9)]   # v6: the whole range — magenta and violet up with the cyan (user: "more colourful ... more elegant"); v5b leaned blue / cyan; red is reserved
ROAD_HUES = ['sodium', 'gold', 'magenta', 'cyan', 'sodium', 'magenta', 'gold', 'violet', 'orange', 'sodium', 'violet', 'cyan']   # v6: half the districts light their streets in neon (v4: a warm carpet with accents; the streets the user likes keep their form)
CORE_ROAD_HUES = ['sodium', 'sodium', 'magenta', 'sodium', 'sodium', 'cyan', 'sodium', 'violet']   # v6: the core's ring roads, foot outward — amber with three neon rings
HOLO_W = [('cyan', 26), ('magenta', 22), ('violet', 16), ('green', 14), ('orange', 8), ('pink', 6), ('blue', 8)]   # v4: the sigils' hues

# ---- v3 THE CYBERCITY LANGUAGE (user, 2026-09-25, after two rounds: "Cybercity I, upgraded" / "full spectrum, evil mood" /
#      "rich purple space"). Every tower is a glowing COLOUR FIELD with a lit GRID in its own hue, its edges lit in that hue;
#      3 in 10 are WINDOW towers (v1's lights over a glowing body) for the upgrade's realism; the floor is a neon grid on navy;
#      the sky is purple space with nebula; nothing in the picture is black or grey.
E_FILL, E_GRID, E_BODY = 1.0, 6.0, 0.5   # (v3 names; unused since v4)
GRID_FRAC = PANEL_FRAC           # (v3 name) the share of towers that wear the panel language
#            lo    hi    w   name        window tint (lit cells)   body hue (the colour field, the grid lines, the edges)
PAL_TABLE = [(0.00, 0.10, 4, 'warm', WIN_AMBER, (1.0, 0.32, 0.08)),       # v4d: the panel hue per palette position; v5: the window tint per row; v5b: weights lean blue / cyan
             (0.10, 0.16, 5, 'cool', WIN_ICE, (0.20, 0.30, 1.0)),
             (0.16, 0.26, 8, 'blue', WIN_COOL, (0.20, 0.30, 1.0)),
             (0.26, 0.44, 18, 'cyan', WIN_CYAN, (0.04, 0.75, 1.0)),
             (0.44, 0.58, 16, 'violet', WIN_VIOLET, (0.36, 0.06, 1.0)),
             (0.58, 0.74, 16, 'magenta', WIN_PINK, (1.0, 0.06, 0.65)),
             (0.74, 0.80, 8, 'pink', WIN_PINK, (1.0, 0.15, 0.50)),
             (0.80, 0.92, 8, 'green', WIN_GREEN, (0.03, 1.0, 0.38)),
             (0.92, 0.985, 7, 'gold', WIN_GOLD, (1.0, 0.52, 0.06)),
             (0.985, 1.001, 0, 'crimson', WIN_AMBER, (1.0, 0.03, 0.08))]    # never rolled: THE ORIGIN's hue
PAL_ALIAS = {'red': 'crimson', 'ember': 'gold', 'orange': 'warm', 'ice': 'cool', 'white': 'warm'}


def pal_roll():
    """a building's palette position, weighted toward the saturated cyber hues"""
    lo, hi = wchoice([((lo, hi), w) for lo, hi, w, *_ in PAL_TABLE])
    return rng.uniform(lo, min(hi, 1.0) - 1e-4)


def pal_of(name):
    """the palette position of a named hue (the segment's centre)"""
    name = PAL_ALIAS.get(name, name)
    for lo, hi, _, n, *_ in PAL_TABLE:
        if n == name:
            return (lo + min(hi, 1.0)) / 2
    return 0.7


def body_col(pal):
    for lo, hi, _, _, _, body in PAL_TABLE:
        if lo <= pal < hi:
            return body
    return PAL_TABLE[-1][5]


def body_ramp(t, pal):
    return t.ramp(pal, [(lo, body) for lo, _, _, _, _, body in PAL_TABLE], 'CONSTANT')


def win_ramp(t, pal):
    return t.ramp(pal, [(lo, win) for lo, _, _, _, win, _ in PAL_TABLE], 'CONSTANT')



def moon_dir():
    """unit vector from the camera toward the moon (the light every sky body is shaded by)"""
    return (0.0, math.cos(MOON_EL * D2R), math.sin(MOON_EL * D2R))


def wchoice(pairs):
    t = sum(w for _, w in pairs)
    x = rng.uniform(0, t)
    for k, w in pairs:
        x -= w
        if x <= 0:
            return k
    return pairs[-1][0]


def amin(r, k=1.2):
    """angular minimum size: the width (m) that spans ~k texels of the 8192 ship at distance r.
    Thin emitters below one texel sparkle; this keeps trails, strips and beacons resolvable."""
    return max(0.8, r * (2 * math.pi / 8192) * k)


def polar(r, az_deg):
    return (r * math.sin(az_deg * D2R), r * math.cos(az_deg * D2R))


def az_of(x, y):
    return math.degrees(math.atan2(x, y))


def core_radials():
    """v5 the core's radial boulevards: math angles (rad), CORE_RADIALS of them (v5b: on the lots' sector boundaries — one runs
    under the sign's gantry)"""
    return [2 * math.pi * k / CORE_RADIALS for k in range(CORE_RADIALS)]


def ship_cap(x, y):
    """v5b the tallest a building at (x, y) may be without standing in front of a battlecruiser (the v5a cruiser at az 148 sat
    behind the green cake megatower): inside a cruiser's angular lane and nearer than it, the cap is the ship's belly line"""
    rc, azc = math.hypot(x, y), az_of(x, y)
    cap = 1e9
    for saz, sd, sz, sL, _ in STARSHIPS:
        if rc < sd and abs((azc - saz + 180.0) % 360.0 - 180.0) < math.degrees(math.atan2(sL * 0.6, sd)) + 4.0:
            cap = min(cap, (sz - sL * 0.12) * rc / sd * 0.92)
    return cap


# ---------------------------------------------------------------- mesh accumulator
class Acc:
    """Collects polygons for ONE object/material. Each corner carries a UV (metres) and a
    colour attribute 'bld' the shaders read (per-building seed / style / palette / weight)."""

    def __init__(self, name):
        self.name = name
        self.v, self.f, self.uv, self.col, self.mi = [], [], [], [], []

    def poly(self, pts, uvs, col, mi=0, cols=None):
        b = len(self.v)
        self.v.extend(pts)
        self.f.append(tuple(range(b, b + len(pts))))
        self.uv.extend(uvs)
        self.col.extend(cols if cols else [col] * len(pts))                  # v5e: per-corner colours (soft fans)
        self.mi.append(mi)

    def prism(self, fp, z0, z1, col, cap=True, cap_acc=None, cap_col=None):
        """extrude a CCW footprint [(x,y)...] from z0 to z1: side quads (u = run along the
        perimeter in metres, v = z) + an n-gon cap. Outward normals by construction."""
        n = len(fp)
        u = 0.0
        for i in range(n):
            ax, ay = fp[i]
            bx, by = fp[(i + 1) % n]
            L = math.hypot(bx - ax, by - ay)
            if L < 0.02:
                continue
            self.poly([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)],
                      [(u, z0), (u + L, z0), (u + L, z1), (u, z1)], col)
            u += L
        if cap:
            (cap_acc or self).poly([(x, y, z1) for x, y in fp], [(x, y) for x, y in fp], cap_col or col)

    def loft(self, fp0, z0, fp1, z1, col, cap=True, cap_acc=None, cap_col=None):
        """v6: side quads between two footprints with the same vertex count (a FRUSTUM when fp1 is fp0 scaled - the references'
        tapering spires) + an n-gon cap on fp1; u = run along the lower perimeter (metres), v = z"""
        n = len(fp0)
        u = 0.0
        for i in range(n):
            (ax, ay), (bx, by) = fp0[i], fp0[(i + 1) % n]
            (cx_, cy_), (dx_, dy_) = fp1[i], fp1[(i + 1) % n]
            L = math.hypot(bx - ax, by - ay)
            if L < 0.02:
                continue
            self.poly([(ax, ay, z0), (bx, by, z0), (dx_, dy_, z1), (cx_, cy_, z1)], [(u, z0), (u + L, z0), (u + L, z1), (u, z1)], col)
            u += L
        if cap:
            (cap_acc or self).poly([(x, y, z1) for x, y in fp1], [(x, y) for x, y in fp1], cap_col or col)

    def quad_dir(self, cx, cy, cz, dx, dy, w, L, col, uv_scale=1.0):
        """a flat horizontal quad centred at (cx,cy,cz) running along unit direction (dx,dy), length L, width w"""
        nx, ny = -dy, dx
        hw, hl = w / 2, L / 2
        pts = [(cx - dx * hl - nx * hw, cy - dy * hl - ny * hw, cz), (cx + dx * hl - nx * hw, cy + dy * hl - ny * hw, cz),
               (cx + dx * hl + nx * hw, cy + dy * hl + ny * hw, cz), (cx - dx * hl + nx * hw, cy - dy * hl + ny * hw, cz)]
        self.poly(pts, [(0, 0), (L * uv_scale, 0), (L * uv_scale, w), (0, w)], col)

    def strip(self, ax, ay, bx, by, z, w, h, col):
        """a thin box along the edge a->b (a neon tube / a barrier): footprint w wide, from z to z+h"""
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        if L < 0.05:
            return
        dx, dy = dx / L, dy / L
        nx, ny = -dy * w / 2, dx * w / 2
        fp = [(ax - nx, ay - ny), (bx - nx, by - ny), (bx + nx, by + ny), (ax + nx, ay + ny)]
        self.prism(fp, z, z + h, col)

    def box(self, cx, cy, z0, w, d, h, ang, col):
        self.prism(fp_rect(cx, cy, w, d, ang), z0, z0 + h, col)

    def build(self, mat, smooth=False):
        if not self.f:
            return None
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.v, [], self.f)
        nloops = len(me.loops)
        if nloops != len(self.uv):
            raise RuntimeError(f'{self.name}: loop count {nloops} != corner data {len(self.uv)} (degenerate polygon?)')
        uv = me.uv_layers.new(name='UVMap')
        uv.data.foreach_set('uv', np.asarray(self.uv, dtype=np.float32).ravel())
        ca = me.color_attributes.new('bld', 'FLOAT_COLOR', 'CORNER')
        ca.data.foreach_set('color', np.asarray(self.col, dtype=np.float32).ravel())
        for m_ in (mat if isinstance(mat, (list, tuple)) else [mat]):
            me.materials.append(m_)
        if any(self.mi):
            me.polygons.foreach_set('material_index', np.asarray(self.mi, dtype=np.int32))
        if smooth:
            me.shade_smooth()
        me.update()
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        log(f'  mesh {self.name}: {len(self.f)} faces')
        return ob


# ---------------------------------------------------------------- footprints (CCW)
def rot(px, py, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (px * c - py * s, px * s + py * c)


def fp_poly(cx, cy, pts, ang):
    return [(cx + x, cy + y) for x, y in (rot(px, py, ang) for px, py in pts)]


def fp_rect(cx, cy, w, d, ang):
    return fp_poly(cx, cy, [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)], ang)


def fp_chamfer(cx, cy, w, d, c, ang):
    c = min(c, w * 0.45, d * 0.45)
    return fp_poly(cx, cy, [(-w / 2 + c, -d / 2), (w / 2 - c, -d / 2), (w / 2, -d / 2 + c), (w / 2, d / 2 - c),
                            (w / 2 - c, d / 2), (-w / 2 + c, d / 2), (-w / 2, d / 2 - c), (-w / 2, -d / 2 + c)], ang)


def fp_ellipse(cx, cy, rx, ry, n, ang):
    return fp_poly(cx, cy, [(rx * math.cos(2 * math.pi * i / n), ry * math.sin(2 * math.pi * i / n)) for i in range(n)], ang)


def fp_L(cx, cy, w, d, cw, cd, ang):
    return fp_poly(cx, cy, [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2 - cd), (w / 2 - cw, d / 2 - cd),
                            (w / 2 - cw, d / 2), (-w / 2, d / 2)], ang)


def fp_center(fp):
    return (sum(p[0] for p in fp) / len(fp), sum(p[1] for p in fp) / len(fp))


def fp_scale(fp, s, ox=0.0, oy=0.0):
    cx, cy = fp_center(fp)
    return [(cx + (x - cx) * s + ox, cy + (y - cy) * s + oy) for x, y in fp]


def fp_facing_edge(fp):
    """index of the edge whose outward normal points most toward the camera (the origin)"""
    best, bi = -2, 0
    n = len(fp)
    for i in range(n):
        ax, ay = fp[i]
        bx, by = fp[(i + 1) % n]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        nx, ny = by - ay, -(bx - ax)
        L = math.hypot(nx, ny) or 1
        dm = math.hypot(mx, my) or 1
        dot = (nx * -mx + ny * -my) / (L * dm)
        if dot > best:
            best, bi = dot, i
    return bi


def lognorm(med, sig):
    return med * math.exp(rng.gauss(0, sig))


# ---------------------------------------------------------------- shader helpers
def plug(sock, src):
    """connect a socket to another socket, or set its default value"""
    if hasattr(src, 'is_output'):
        sock.node.id_data.links.new(src, sock)
    elif isinstance(src, (int, float)):
        if sock.type == 'RGBA':
            sock.default_value = (src, src, src, 1.0)
        elif sock.type == 'VECTOR':
            sock.default_value = (src, src, src)
        else:
            sock.default_value = src
    else:
        v = tuple(src)
        if sock.type == 'RGBA':
            sock.default_value = v if len(v) == 4 else (*v, 1.0)
        elif sock.type == 'VECTOR':
            sock.default_value = v[:3]
        else:
            sock.default_value = v[0]


class NT:
    def __init__(self, tree):
        self.t = tree
        self.n = 0

    def node(self, kind, **props):
        n = self.t.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        self.n += 1
        n.location = ((self.n % 12) * 220, -(self.n // 12) * 260)
        return n

    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        plug(n.inputs[0], a)
        if b is not None:
            plug(n.inputs[1], b)
        if c is not None:
            plug(n.inputs[2], c)
        return n.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        n = self.node('ShaderNodeVectorMath', operation=op)
        plug(n.inputs[0], a)
        if b is not None:
            plug(n.inputs[1], b)
        if scale is not None:
            plug(n.inputs[3], scale)
        return n.outputs[0] if op != 'LENGTH' and op != 'DISTANCE' and op != 'DOT_PRODUCT' else n.outputs[1]

    def maprange(self, v, a, b, c, d, clamp=True):
        n = self.node('ShaderNodeMapRange', clamp=clamp)
        plug(n.inputs['Value'], v)
        plug(n.inputs['From Min'], a)
        plug(n.inputs['From Max'], b)
        plug(n.inputs['To Min'], c)
        plug(n.inputs['To Max'], d)
        return n.outputs['Result']

    def mix_rgb(self, fac, a, b):
        n = self.node('ShaderNodeMix', data_type='RGBA', clamp_factor=True)
        plug(n.inputs[0], fac)
        plug(n.inputs[6], a)
        plug(n.inputs[7], b)
        return n.outputs[2]

    def mix_f(self, fac, a, b):
        n = self.node('ShaderNodeMix', data_type='FLOAT', clamp_factor=True)
        plug(n.inputs[0], fac)
        plug(n.inputs[2], a)
        plug(n.inputs[3], b)
        return n.outputs[0]

    def mul_rgb(self, a, b):
        n = self.node('ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
        plug(n.inputs[0], 1.0)
        plug(n.inputs[6], a)
        plug(n.inputs[7], b)
        return n.outputs[2]

    def scale_rgb(self, col, f):
        n = self.node('ShaderNodeVectorMath', operation='SCALE')
        plug(n.inputs[0], col)
        plug(n.inputs[3], f)
        return n.outputs[0]

    def ramp(self, fac, stops, interp='LINEAR'):
        n = self.node('ShaderNodeValToRGB')
        n.color_ramp.interpolation = interp
        els = n.color_ramp.elements
        while len(els) > 1:
            els.remove(els[-1])
        els[0].position = stops[0][0]
        els[0].color = (*stops[0][1], 1.0)
        for p, c in stops[1:]:
            e = els.new(p)
            e.color = (*c, 1.0)
        plug(n.inputs[0], fac)
        return n.outputs['Color']

    def sep(self, vec):
        n = self.node('ShaderNodeSeparateXYZ')
        plug(n.inputs[0], vec)
        return n.outputs['X'], n.outputs['Y'], n.outputs['Z']

    def sep_col(self, col):
        n = self.node('ShaderNodeSeparateColor')
        plug(n.inputs[0], col)
        return n.outputs['Red'], n.outputs['Green'], n.outputs['Blue']

    def comb(self, x, y, z):
        n = self.node('ShaderNodeCombineXYZ')
        plug(n.inputs[0], x)
        plug(n.inputs[1], y)
        plug(n.inputs[2], z)
        return n.outputs[0]

    def brick(self, vec, width, row, mortar, smooth=0.05, offset=0.0):
        """Brick texture as a WINDOW GRID: Fac = the frame (mortar) mask, Color = one uniform
        random per cell (Color1 black -> Color2 white, bias 0). offset 0 = an aligned grid."""
        n = self.node('ShaderNodeTexBrick', offset=offset, offset_frequency=2, squash=1.0, squash_frequency=2)
        plug(n.inputs['Vector'], vec)
        plug(n.inputs['Color1'], (0, 0, 0, 1))
        plug(n.inputs['Color2'], (1, 1, 1, 1))
        plug(n.inputs['Mortar'], (0, 0, 0, 1))
        plug(n.inputs['Scale'], 1.0)
        plug(n.inputs['Mortar Size'], mortar)
        plug(n.inputs['Mortar Smooth'], smooth)
        plug(n.inputs['Bias'], 0.0)
        plug(n.inputs['Brick Width'], width)
        plug(n.inputs['Row Height'], row)
        return n.outputs['Color'], n.outputs['Fac']

    def noise(self, vec, scale, detail=2.0, rough=0.5, dims='3D'):
        n = self.node('ShaderNodeTexNoise', noise_dimensions=dims)
        plug(n.inputs['Vector'], vec)
        plug(n.inputs['Scale'], scale)
        plug(n.inputs['Detail'], detail)
        plug(n.inputs['Roughness'], rough)
        return n.outputs['Fac']

    def attr(self, name='bld'):
        n = self.node('ShaderNodeAttribute', attribute_name=name)
        return n.outputs['Color'], n.outputs['Alpha']

    def uv(self):
        return self.node('ShaderNodeUVMap').outputs['UV']

    def obj_co(self):
        return self.node('ShaderNodeTexCoord').outputs['Object']

    def principled(self, base=None, rough=0.5, metallic=0.0, emis_col=None, emis_str=0.0, alpha=None):
        n = self.node('ShaderNodeBsdfPrincipled')
        if base is not None:
            plug(n.inputs['Base Color'], base)
        plug(n.inputs['Roughness'], rough)
        plug(n.inputs['Metallic'], metallic)
        if emis_col is not None:
            plug(n.inputs['Emission Color'], emis_col)
        plug(n.inputs['Emission Strength'], emis_str)
        if alpha is not None:
            plug(n.inputs['Alpha'], alpha)
        return n.outputs['BSDF']

    def emission(self, col, strength):
        n = self.node('ShaderNodeEmission')
        plug(n.inputs['Color'], col)
        plug(n.inputs['Strength'], strength)
        return n.outputs['Emission']

    def out(self, surface=None, volume=None, world=False):
        n = self.node('ShaderNodeOutputWorld' if world else 'ShaderNodeOutputMaterial')
        if surface is not None:
            self.t.links.new(surface, n.inputs['Surface'])
        if volume is not None:
            self.t.links.new(volume, n.inputs['Volume'])
        return n


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, NT(m.node_tree)


# ---------------------------------------------------------------- materials
def mat_facade():
    """v4 THE REFERENCE COPY: every tower is a DARK body (near-black, never black: the painted ambient BODY_FLOOR) wearing DENSE
    WARM windows (amber / gold, a few cool); a PANEL tower (style < PANEL_FRAC) also wears full-height translucent NEON PANELS in
    its hue on 28..48 % of its columns — a saturated colour field (E_PANEL) with a lit circuit grid (E_PLINE) and hot cells. Line
    widths hold a texel of the 8192 ship. Attribute 'bld' = (seed, style, palette position, lit fraction)."""
    m, t = new_mat('sky3d_facade')
    u, v, _ = t.sep(t.uv())
    col, litfrac = t.attr()
    seed, style, pal = t.sep_col(col)
    wx, wy, wz = t.sep(t.obj_co())
    dist = t.vmath('LENGTH', t.comb(wx, wy, 0.0))
    texel = t.math('MULTIPLY', dist, 2 * math.pi / 8192)
    vec = t.comb(t.math('ADD', u, t.math('MULTIPLY', seed, 173.1)), t.math('ADD', v, t.math('MULTIPLY', seed, 37.7)), 0.0)
    floorH = 3.7
    hue = body_ramp(t, pal)
    # ---- the windows: dense and warm (the references' orange carpet)
    winW = t.maprange(seed, 0.0, 1.0, 1.6, 3.2)
    frame = t.math('MAXIMUM', 0.50, t.math('MULTIPLY', texel, 0.8))         # v4i
    r1, framemask = t.brick(vec, winW, floorH, frame, 0.04)
    r2, _ = t.brick(t.vmath('ADD', vec, (11.3, 5.9, 0.0)), winW, floorH, frame, 0.04)
    r5, _ = t.brick(vec, 27.0, floorH * 3, 0.001, 0.0)
    r1f, _, _ = t.sep_col(r1)
    r2f, _, _ = t.sep_col(r2)
    r5f, _, _ = t.sep_col(r5)
    lit_frac = t.math('MULTIPLY', litfrac, t.maprange(r5f, 0.0, 1.0, 0.4, 1.6), clamp=True)
    thr = t.math('SUBTRACT', 1.0, lit_frac)
    lit = t.math('GREATER_THAN', r1f, thr)
    lobby = t.math('LESS_THAN', v, floorH * 2.2)
    lit = t.math('MAXIMUM', lit, t.math('MULTIPLY', lobby, t.math('GREATER_THAN', r1f, 0.2)))
    lit = t.math('MULTIPLY', lit, t.math('SUBTRACT', 1.0, framemask))
    bright = t.math('DIVIDE', t.math('SUBTRACT', r1f, thr), t.math('MAXIMUM', lit_frac, 0.01), clamp=True)
    bright = t.maprange(bright, 0.0, 1.0, 0.35, 1.0)
    wtint = win_ramp(t, pal)                                                    # v5: the tint follows the tower's hue row (user: "a colour that's so dominant ... the windows")
    wincol = t.mix_rgb(t.math('GREATER_THAN', r2f, 0.55), wtint, WIN_ICE)      # 55 % the row's tint, 35 % cool white, 10 % amber
    wincol = t.mix_rgb(t.math('GREATER_THAN', r2f, 0.90), wincol, WIN_AMBER)
    win_em = t.scale_rgb(wincol, t.math('MULTIPLY', t.math('MULTIPLY', lit, bright), E_WIN))
    # ---- the panels: full-height columns (one brick row) picked by their random
    colW = t.maprange(seed, 0.0, 1.0, 18.0, 48.0)                             # v5b: a 200 m tower wears 4..10 panels, not a barcode (v4: 9..22 m)
    pc, _ = t.brick(t.comb(t.math('ADD', u, t.math('MULTIPLY', seed, 91.0)), 0.5, 0.0), colW, 100000.0, 0.001, 0.0)
    pcf, _, _ = t.sep_col(pc)
    pfrac = t.maprange(style, 0.0, PANEL_FRAC, 0.28, 0.50)   # v4j: strips on a dark body, not a coloured box
    is_panel = t.math('MULTIPLY', t.math('LESS_THAN', style, PANEL_FRAC), t.math('GREATER_THAN', pcf, t.math('SUBTRACT', 1.0, pfrac)))
    gline_w = t.math('MINIMUM', t.math('MULTIPLY', colW, 0.32 * 0.16), t.math('MAXIMUM', 0.35, t.math('MULTIPLY', texel, 1.4)))   # v6f: a line at most 16 % of its cell (at 3 km a texel-wide line was half the panel)
    gcol, gline = t.brick(vec, t.math('MULTIPLY', colW, 0.32), t.math('MULTIPLY', colW, 0.27), gline_w, 0.03)   # v5b: the circuit cells scale with the panel (a third of its width)
    gr, _, _ = t.sep_col(gcol)
    cellb = t.maprange(gr, 0.0, 1.0, 0.50, 1.30)
    hot = t.math('GREATER_THAN', gr, 0.90)
    pfill = t.scale_rgb(hue, t.math('MULTIPLY', t.math('ADD', t.math('MULTIPLY', cellb, E_PANEL), t.math('MULTIPLY', hot, 0.22)), t.math('SUBTRACT', 1.0, gline)))   # v6f: under the knee
    plines = t.scale_rgb(t.mix_rgb(0.04, hue, (1, 1, 1, 1)), t.math('MULTIPLY', gline, E_PLINE))   # v4i: the lines are the hue, brighter — never white
    panel_em = t.vmath('ADD', pfill, plines)
    # ---- v6b THE SPIRE FACADE (the references' towers: dark metal, thin horizontal light ROWS every few floors, fine vertical GROOVES in
    #      the hue, few dim windows; the SEAMS on the edges and the collars are geometry in building()). style >= 2 marks a spire.
    is_spire = t.math('GREATER_THAN', style, 1.5)
    rowH = floorH * 7.0                                                          # v6d: a light row every seven floors (four read as wire)
    rowi = t.math('FLOOR', t.math('DIVIDE', v, rowH))
    rowf = t.math('FRACT', t.math('DIVIDE', v, rowH))
    rgate = t.math('GREATER_THAN', t.noise(t.comb(t.math('MULTIPLY', rowi, 0.37), t.math('MULTIPLY', seed, 53.0), 0.5), 1.0, 1.0), 0.56)
    thick = t.math('DIVIDE', t.math('MAXIMUM', 0.7, t.math('MULTIPLY', texel, 1.3)), rowH)
    band = t.math('MULTIPLY', t.math('LESS_THAN', rowf, thick), rgate)
    grooveW = t.maprange(seed, 0.0, 1.0, 7.0, 15.0)
    gcoord = t.math('DIVIDE', t.math('ADD', u, t.math('MULTIPLY', seed, 17.0)), grooveW)
    gu = t.math('FRACT', gcoord)
    gw = t.math('MINIMUM', 0.12, t.math('DIVIDE', t.math('MAXIMUM', 0.35, t.math('MULTIPLY', texel, 1.2)), grooveW))   # v6f: capped
    ggate = t.math('GREATER_THAN', t.noise(t.comb(t.math('MULTIPLY', t.math('FLOOR', gcoord), 0.41), t.math('MULTIPLY', seed, 29.0), 0.25), 1.0, 1.0), 0.56)
    groove = t.math('MULTIPLY', t.math('LESS_THAN', gu, gw), ggate)
    spire_lines = t.math('MAXIMUM', t.math('MULTIPLY', band, 0.75), t.math('MULTIPLY', groove, 0.25))   # v6c: faint grooves (they read as wire)
    low = t.math('LESS_THAN', v, 26.0)                                            # v6e: the lowest floors dense and AMBER (the references' warm bases)
    spwin = t.math('MAXIMUM', lit, t.math('MULTIPLY', low, t.math('MULTIPLY', t.math('GREATER_THAN', r1f, 0.30), t.math('SUBTRACT', 1.0, framemask))))
    spcol = t.mix_rgb(low, wincol, WIN_AMBER)
    spire_em = t.vmath('ADD', t.scale_rgb(hue, t.math('MULTIPLY', spire_lines, E_PLINE * 0.75)),
                       t.scale_rgb(spcol, t.math('MULTIPLY', t.math('MULTIPLY', spwin, t.math('MAXIMUM', bright, low)), E_WIN * 0.5)))     # the windows: fewer, dimmer, warm at the foot
    lit_em = t.mix_rgb(is_spire, t.mix_rgb(is_panel, win_em, panel_em), spire_em)
    # ---- the body: the painted ambient floor (the references' dark structure is (23,20,26), not black)
    grime = t.maprange(t.noise(t.vmath('SCALE', vec, scale=0.09), 1.0, 3.0), 0.0, 1.0, 0.6, 1.3)
    floor_em = t.scale_rgb(BODY_FLOOR, grime)
    dead = t.maprange(litfrac, 0.02, 0.10, 0.25, 1.0)
    em = t.vmath('ADD', floor_em, t.scale_rgb(lit_em, dead))
    base = t.mix_rgb(is_panel, BODY_ALBEDO, t.scale_rgb(hue, 0.08))
    # Broad weathered coating and fine recess relief survive at different view
    # distances; the body stays matte enough to avoid reflecting neon as white.
    coating = t.noise(t.vmath('SCALE', vec, scale=0.045), 1.0, 3.0)
    rough = t.maprange(coating, 0.0, 1.0, 0.62, 0.86)
    base = t.scale_rgb(base, t.maprange(coating, 0.0, 1.0, 0.74, 1.12))
    surface = t.principled(base, rough, 0.08, em, 1.0)
    relief = t.node('ShaderNodeBump')
    relief.inputs['Strength'].default_value = 0.14
    relief.inputs['Distance'].default_value = 0.035
    t.t.links.new(coating, relief.inputs['Height'])
    t.t.links.new(relief.outputs['Normal'], surface.node.inputs['Normal'])
    t.out(surface)
    return m


def mat_roof():
    """v4: dark tops with the painted ambient, a few lit service cells (warm), a faint tint + edge lines in the tower's hue on
    panel towers (from the crown the player looks DOWN on them; the lit parapets are neon strips in building())"""
    m, t = new_mat('sky3d_roof')
    col, litfrac = t.attr()
    seed, style, pal = t.sep_col(col)
    hue = body_ramp(t, pal)
    x, y, z = t.sep(t.obj_co())
    dist = t.vmath('LENGTH', t.comb(x, y, 0.0))
    lineW = t.math('MAXIMUM', 0.5, t.math('MULTIPLY', dist, 2 * math.pi / 8192 * 0.9))
    gcol, gline = t.brick(t.comb(t.math('ADD', x, t.math('MULTIPLY', seed, 91.0)), t.math('ADD', y, t.math('MULTIPLY', seed, 37.0)), 0.0), 9.0, 9.0, lineW, 0.03)
    gr, _, _ = t.sep_col(gcol)
    is_panel = t.math('LESS_THAN', style, PANEL_FRAC)
    lit = t.math('GREATER_THAN', gr, 0.93)
    dead = t.maprange(litfrac, 0.02, 0.10, 0.25, 1.0)
    warm = t.scale_rgb(win_ramp(t, pal), t.math('MULTIPLY', lit, t.math('MULTIPLY', t.math('SUBTRACT', 1.0, is_panel), 0.30)))   # v5g: a few dim service cells, not tiles   # v5: the roof cells in the tower's window tint
    tint = t.scale_rgb(hue, t.math('MULTIPLY', is_panel, t.math('ADD', 0.03, t.math('MULTIPLY', gline, 0.20))))   # v4k: a dark roof, a faint grid in the tower's hue
    em = t.vmath('ADD', t.scale_rgb(BODY_FLOOR, 0.9), t.scale_rgb(t.vmath('ADD', warm, tint), dead))
    t.out(t.principled(BODY_ALBEDO, 0.5, 0.0, em, 1.0))
    return m


def mat_struct():
    m, t = new_mat('sky3d_struct')
    t.out(t.principled(BODY_ALBEDO, 0.40, 0.30, BODY_FLOOR, 0.8))      # v4: dark steel with the painted ambient — never black
    return m


def mat_neon():
    m, t = new_mat('sky3d_neon')
    col, a = t.attr()
    t.out(t.emission(col, t.math('MULTIPLY', a, E_NEON)))
    return m


def mat_trail():
    m, t = new_mat('sky3d_trail')
    col, a = t.attr()
    dash = t.noise(t.vmath('SCALE', t.obj_co(), scale=0.025), 1.0, 1.0, 0.5, '3D')
    dash = t.maprange(dash, 0.40, 0.56, 0.12, 1.0)
    t.out(t.emission(col, t.math('MULTIPLY', t.math('MULTIPLY', a, dash), E_TRAIL)))
    return m


def mat_screen():
    m, t = new_mat('sky3d_screen')
    col, a = t.attr()
    hue, _, _ = t.sep_col(col)
    uvv = t.uv()
    u, v, _ = t.sep(uvv)
    vec = t.comb(t.math('ADD', u, t.math('MULTIPLY', hue, 91.0)), v, 0.0)
    r1, cellframe = t.brick(vec, 7.5, 4.2, 0.10, 0.02)
    r2, _ = t.brick(t.vmath('ADD', vec, (17.3, 5.1, 0.0)), 7.5, 4.2, 0.10, 0.02)
    r1f, _, _ = t.sep_col(r1)
    r2f, _, _ = t.sep_col(r2)
    pattern = t.ramp(r1f, [(0.0, (0.02, 0.0, 0.01)), (0.22, (0.35, 0.02, 0.04)), (0.45, PAL['crimson']), (0.60, PAL['ember']),
                           (0.72, (1.0, 0.72, 0.52)), (0.82, PAL['magenta']), (0.92, PAL['cyan']), (1.0, (0.9, 0.9, 1.0))])
    big = t.maprange(t.noise(t.vmath('SCALE', vec, scale=0.03), 1.0, 2.0), 0.0, 1.0, 0.45, 1.5)
    scan = t.math('FRACT', t.math('MULTIPLY', v, 0.75))
    scan = t.maprange(scan, 0.0, 1.0, 0.7, 1.0)
    huetint = t.ramp(hue, [(0.0, (1.0, 0.45, 0.45)), (0.35, (1.0, 0.9, 0.9)), (0.65, (0.85, 0.6, 1.0)), (1.0, (0.5, 0.85, 1.0))])
    e = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', a, big), scan), t.math('MULTIPLY', t.maprange(r2f, 0, 1, 0.5, 1.2), E_SCREEN))
    e = t.math('MULTIPLY', e, t.math('SUBTRACT', 1.0, t.math('MULTIPLY', cellframe, 0.5)))
    field = t.ramp(t.noise(t.vmath('SCALE', vec, scale=0.02), 1.0, 2.0), [(0.3, (0.25, 0.01, 0.03)), (0.5, PAL['crimson']), (0.7, PAL['magenta']), (0.85, (0.4, 0.1, 0.9))])
    picture = t.mix_rgb(0.55, t.mul_rgb(pattern, huetint), t.mul_rgb(field, huetint))
    t.out(t.emission(picture, e))
    return m


def mat_screen_image(img):
    """an ad screen wearing an image-model billboard (docs/167): the metre UVs are normalised by the
    screen's own size (attribute G,B), the image is emissive with scanlines and a slow brightness drift"""
    m, t = new_mat('sky3d_screen_' + os.path.splitext(os.path.basename(img.filepath))[0])
    col, a = t.attr()
    hue, sw, sh = t.sep_col(col)
    u, v, _ = t.sep(t.uv())
    uvn = t.comb(t.math('DIVIDE', u, t.math('MAXIMUM', sw, 0.01)), t.math('DIVIDE', v, t.math('MAXIMUM', sh, 0.01)), 0.0)
    tex = t.node('ShaderNodeTexImage', extension='EXTEND', interpolation='Linear')
    tex.image = img
    plug(tex.inputs['Vector'], uvn)
    scan = t.maprange(t.math('FRACT', t.math('MULTIPLY', v, 0.75)), 0.0, 1.0, 0.72, 1.0)
    drift = t.maprange(t.noise(t.vmath('SCALE', t.obj_co(), scale=0.002), 1.0, 1.0), 0.0, 1.0, 0.7, 1.3)
    e = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', a, scan), drift), E_SCREEN * 1.6)   # v6: the ads are half near-black — brighter than the mosaic's field so their glow shapes read
    t.out(t.emission(tex.outputs['Color'], e))
    return m


def load_screen_images():
    if not SCREENS_DIR or not os.path.isdir(SCREENS_DIR):
        return []
    imgs = []
    for fn in sorted(os.listdir(SCREENS_DIR)):
        if fn.lower().endswith(('.png', '.jpg', '.jpeg')):
            im = bpy.data.images.load(os.path.join(SCREENS_DIR, fn))
            im.colorspace_settings.name = 'sRGB'
            imgs.append(im)
    log(f'screens: {len(imgs)} billboard images from {SCREENS_DIR}')
    return imgs


SCREEN_IMGS = load_screen_images()
N_SCREEN_IMG = len(SCREEN_IMGS)
SCREEN_BY_ASPECT = {'wide': [], 'tall': [], 'square': []}                     # v6: material index (1-based) per orientation
for _i, _im in enumerate(SCREEN_IMGS):
    _asp = _im.size[0] / max(1, _im.size[1])
    SCREEN_BY_ASPECT['wide' if _asp > 1.25 else ('tall' if _asp < 0.8 else 'square')].append(_i + 1)


def screen_mi(sw, sh, p=0.75):
    """v6: the material index for an ad screen sw x sh metres — with probability p a docs/167 billboard of the screen's OWN
    orientation (wide / tall / square; the whole set if that pool is empty), else 0 = the procedural mosaic"""
    if not N_SCREEN_IMG or rng.random() >= p:
        return 0
    asp = sw / max(1e-6, sh)
    pool = SCREEN_BY_ASPECT['wide' if asp > 1.25 else ('tall' if asp < 0.8 else 'square')] or list(range(1, N_SCREEN_IMG + 1))
    return rng.choice(pool)


def mat_ground():
    """v4 THE FLOOR: dark wet ground (glossy, so the neon reflects) with a WARM light-pollution glow that grows toward the far
    carpet, and beyond the streets (r > 6.5 km) a faint grid in sodium / gold / magenta / cyan by region"""
    m, t = new_mat('sky3d_ground')
    co = t.obj_co()
    x, y, z = t.sep(co)
    dist = t.vmath('LENGTH', t.comb(x, y, 0.0))
    wet = t.noise(t.vmath('SCALE', co, scale=1.0 / 260.0), 1.0, 4.0)
    rough = t.maprange(wet, 0.35, 0.7, 0.35, 0.06)
    n2 = t.maprange(t.noise(t.vmath('SCALE', co, scale=1.0 / 40.0), 1.0, 5.0), 0.0, 1.0, 0.6, 1.3)
    lineW = t.math('MAXIMUM', 2.5, t.math('MULTIPLY', dist, 2 * math.pi / 8192 * 1.1))
    gcol, gline = t.brick(t.comb(x, y, 0.0), 220.0, 220.0, lineW, 0.02)
    far = t.maprange(dist, 6500.0, 9000.0, 0.0, 1.0)
    glow = t.maprange(dist, 3000.0, 26000.0, 0.3, 1.0)
    fill = t.scale_rgb(GROUND_GLOW, t.math('MULTIPLY', t.math('MULTIPLY', n2, glow), E_GROUND))
    hue = t.ramp(t.noise(t.vmath('SCALE', co, scale=1.0 / 9000.0), 1.0, 2.0), [(0.30, PAL['sodium']), (0.50, PAL['gold']), (0.62, PAL['magenta']), (0.75, PAL['cyan'])])
    em = t.vmath('ADD', fill, t.scale_rgb(hue, t.math('MULTIPLY', t.math('MULTIPLY', gline, far), E_GGRID)))
    t.out(t.principled(t.scale_rgb((0.010, 0.010, 0.020), n2), rough, 0.0, em, 1.0))
    return m


def mat_water():
    m, t = new_mat('sky3d_water')
    co = t.obj_co()
    bump = t.node('ShaderNodeBump')
    plug(bump.inputs['Strength'], 0.3)
    plug(bump.inputs['Distance'], 0.6)
    plug(bump.inputs['Height'], t.noise(t.vmath('SCALE', co, scale=1.0 / 55.0), 1.0, 6.0, 0.62))
    p = t.node('ShaderNodeBsdfPrincipled')
    plug(p.inputs['Base Color'], (0.004, 0.003, 0.004, 1))
    plug(p.inputs['Roughness'], 0.04)
    plug(p.inputs['Metallic'], 0.0)
    plug(p.inputs['Emission Strength'], 0.0)
    t.t.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    t.out(p.outputs['BSDF'])
    return m


def mat_fog():
    """the atmosphere: a scattering volume whose density falls off with height (exp(-z/FOG_H0)) and
    drifts in patches across the city; red-tinted scatter so the light pollution reads ember,
    forward anisotropy so every bright source blooms. A MESH box, not a world volume: a bounded
    volume lets sky rays leave it (a world volume marches every sky ray to volume_max_steps)."""
    m, t = new_mat('sky3d_fog')
    x, y, z = t.sep(t.obj_co())
    fall = t.math('EXPONENT', t.math('MULTIPLY', t.math('MAXIMUM', z, 0.0), -1.0 / FOG_H0))
    patch = t.maprange(t.noise(t.comb(t.math('MULTIPLY', x, 1.0 / 5200.0), t.math('MULTIPLY', y, 1.0 / 5200.0), 0.0), 1.0, 3.0), 0.0, 1.0, 0.6, 1.4)
    dens = t.math('MULTIPLY', t.math('MULTIPLY', fall, patch), FOG_D0)
    sc = t.node('ShaderNodeVolumeScatter')
    hz = t.maprange(z, 0.0, FOG_H0 * 1.6, 0.0, 1.0)                                  # v6: warm at the street, violet-magenta above — a grade, not a veil (v4: warm-neutral)
    plug(sc.inputs['Color'], t.mix_rgb(hz, FOG_SCATTER, FOG_SCATTER_HI))
    plug(sc.inputs['Density'], dens)
    plug(sc.inputs['Anisotropy'], 0.45)
    ab = t.node('ShaderNodeVolumeAbsorption')
    plug(ab.inputs['Color'], (*FOG_ABSORB, 1))
    plug(ab.inputs['Density'], t.math('MULTIPLY', dens, 0.22))
    add = t.node('ShaderNodeAddShader')
    t.t.links.new(sc.outputs[0], add.inputs[0])
    t.t.links.new(ab.outputs[0], add.inputs[1])
    t.out(volume=add.outputs[0])
    m.cycles.volume_step_rate = FOG_RATE
    m.cycles.homogeneous_volume = False
    return m


def make_fog(mat):
    acc = Acc('fog')
    fp = fp_rect(0, 0, 2 * FOG_R, 2 * FOG_R, 0)
    acc.prism(fp, -20.0, FOG_TOP, (0, 0, 0, 1), cap=True)
    acc.poly([(x, y, -20.0) for x, y in reversed(fp)], [(0, 0)] * 4, (0, 0, 0, 1))
    ob = acc.build(mat)
    ob.visible_shadow = False
    log(f'  fog box {2 * FOG_R / 1000:.0f} km, top {FOG_TOP:.0f} m, implied step ~{0.1 * (4 * FOG_R + FOG_TOP + 20) / 3 * FOG_RATE:.0f} m')


def mat_haze():
    """v2: the thin homogeneous haze above the fog (FOG_TOP..HAZE_TOP) — analytic in Cycles, so it costs ~nothing, and it
    is what makes a 5 km megastructure 20 km away fade instead of standing razor-sharp above the fog line"""
    m, t = new_mat('sky3d_haze')
    sc = t.node('ShaderNodeVolumeScatter')
    plug(sc.inputs['Color'], (*HAZE_SCATTER, 1))                    # v4: sky-blue, lit by the indigo sky — the references' blue-violet distance
    plug(sc.inputs['Density'], HAZE_D)
    plug(sc.inputs['Anisotropy'], 0.25)
    t.out(volume=sc.outputs[0])
    m.cycles.homogeneous_volume = True
    m.cycles.volume_step_rate = 4.0
    return m


def make_haze(mat):
    acc = Acc('haze')
    fp = fp_rect(0, 0, 2 * FOG_R, 2 * FOG_R, 0)
    acc.prism(fp, FOG_TOP, HAZE_TOP, (0, 0, 0, 1), cap=True)
    acc.poly([(x, y, FOG_TOP) for x, y in reversed(fp)], [(0, 0)] * 4, (0, 0, 0, 1))
    ob = acc.build(mat)
    ob.visible_shadow = False


def mat_clouds(zc, moon_xy, cover_lo, cover_hi, emis):
    m, t = new_mat(f'sky3d_clouds_{int(zc)}')
    co = t.obj_co()
    x, y, z = t.sep(co)
    xy = t.comb(x, y, 0.0)
    n1 = t.noise(t.vmath('SCALE', xy, scale=1.0 / 7000.0), 1.0, 8.0, 0.62)
    n2 = t.noise(t.vmath('ADD', t.vmath('SCALE', xy, scale=1.0 / 1600.0), (3.1, 7.7, 0)), 1.0, 5.0, 0.55)
    cov = t.math('ADD', t.math('MULTIPLY', n1, 0.72), t.math('MULTIPLY', n2, 0.28))
    alpha = t.maprange(cov, cover_lo, cover_hi, 0.0, 1.0)
    hole = t.maprange(t.vmath('DISTANCE', xy, (moon_xy[0], moon_xy[1], 0.0)), 1800.0, 4800.0, 0.0, 1.0)
    alpha = t.math('MULTIPLY', alpha, hole)
    r = t.vmath('LENGTH', xy)
    glow = t.maprange(r, 3000.0, 24000.0, 1.0, 0.12)
    emis_col = t.ramp(t.maprange(r, 0.0, 26000.0, 0.0, 1.0), [(0.0, (0.90, 0.22, 0.65)), (0.5, (0.62, 0.16, 0.60)), (1.0, (0.30, 0.10, 0.40))])   # v3: magenta -> violet underlight
    bsdf = t.principled((0.025, 0.014, 0.045), 1.0, 0.0, emis_col, t.math('MULTIPLY', t.math('MULTIPLY', glow, emis), t.maprange(cov, cover_lo, 1.0, 0.6, 1.4)))
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    plug(mix.inputs[0], alpha)
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(bsdf, mix.inputs[2])
    t.out(mix.outputs[0])
    return m


def mat_moon():
    m, t = new_mat('sky3d_moon')
    co = t.obj_co()
    crat = t.noise(t.vmath('SCALE', co, scale=1.0 / 900.0), 1.0, 7.0, 0.55)
    crat2 = t.noise(t.vmath('ADD', t.vmath('SCALE', co, scale=1.0 / 300.0), (5, 5, 5)), 1.0, 4.0)
    shade = t.maprange(t.math('ADD', t.math('MULTIPLY', crat, 0.7), t.math('MULTIPLY', crat2, 0.3)), 0.3, 0.75, 0.42, 1.0)
    lw = t.node('ShaderNodeLayerWeight')
    plug(lw.inputs['Blend'], 0.5)
    limb = t.maprange(t.math('POWER', lw.outputs['Facing'], 1.6), 0.0, 1.0, 1.0, 0.25)
    if MOON_STYLE == 'reference':                                   # v7: the reference's moon: pale lavender, mid-bright, cratered
        col = t.ramp(shade, [(0.4, (0.30, 0.26, 0.85)), (0.75, (0.36, 0.31, 0.95)), (1.0, (0.40, 0.36, 1.0))])
        t.out(t.emission(col, t.math('MULTIPLY', t.math('MULTIPLY', shade, limb), 0.075)))
        return m
    col = t.ramp(shade, [(0.4, (0.30, 0.005, 0.006)), (0.75, (0.85, 0.02, 0.015)), (1.0, (1.0, 0.06, 0.03))])   # v4d: BLOOD red in display terms (200,30,20) — green under 0.06 W or it reads orange
    t.out(t.emission(col, t.math('MULTIPLY', t.math('MULTIPLY', shade, limb), E_MOON)))
    return m


def mat_plain(name, col, strength, alpha=None):
    """a flat emitter for primitives (they carry no 'bld' attribute); alpha < 1 mixes it over transparency"""
    m, t = new_mat(name)
    em = t.emission((*col, 1), strength)
    if alpha is None:
        t.out(em)
    else:
        tr = t.node('ShaderNodeBsdfTransparent')
        mix = t.node('ShaderNodeMixShader')
        plug(mix.inputs[0], alpha)
        t.t.links.new(tr.outputs[0], mix.inputs[1])
        t.t.links.new(em, mix.inputs[2])
        t.out(mix.outputs[0])
    return m


def mat_translucent(name, strength):
    """emission from the 'bld' attribute (rgb) mixed over transparency by its alpha: jets, searchlight cones, laser bars"""
    m, t = new_mat(name)
    col, a = t.attr()
    em = t.emission(col, strength)
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    plug(mix.inputs[0], a)
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(em, mix.inputs[2])
    t.out(mix.outputs[0])
    return m


def mat_holo():
    """v2: a holographic panel floating over the roofs — a translucent glyph screen (brick cells 6 m, scanlines) in the panel's
    hue (attribute rgb), its alpha the strength; the city shows through it"""
    m, t = new_mat('sky3d_holo')
    col, a = t.attr()
    u, v, _ = t.sep(t.uv())
    r1, frame = t.brick(t.comb(u, v, 0.0), 6.0, 6.0, 0.7, 0.05)
    r1f, _, _ = t.sep_col(r1)
    glyph = t.math('GREATER_THAN', r1f, 0.48)
    scan = t.maprange(t.math('FRACT', t.math('MULTIPLY', v, 0.5)), 0.0, 1.0, 0.5, 1.0)
    drift = t.maprange(t.noise(t.vmath('SCALE', t.obj_co(), scale=0.004), 1.0, 1.0), 0.0, 1.0, 0.7, 1.3)
    e = t.math('MULTIPLY', t.math('MULTIPLY', t.math('ADD', t.math('MULTIPLY', glyph, 0.85), 0.15), t.math('MULTIPLY', scan, drift)), t.math('MULTIPLY', a, E_HOLO))
    em = t.emission(col, e)
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    plug(mix.inputs[0], 0.6)
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(em, mix.inputs[2])
    t.out(mix.outputs[0])
    return m



def mat_sigil():
    """v4 a glowing EMBLEM on a tower face (the references' circle / hexagon / diamond sigils): attribute (shape, w, h) + alpha =
    palette position -> hue; the metre UVs are normalised to -1..1; ring + spoke, hexagon or diamond line work whose width holds a
    texel of the 8192 ship; a soft glow fill; translucent so the tower shows through"""
    m, t = new_mat('sky3d_sigil')
    col, hp = t.attr()
    shape, sw, sh = t.sep_col(col)
    hue = body_ramp(t, hp)
    u, v, _ = t.sep(t.uv())
    X = t.math('SUBTRACT', t.math('MULTIPLY', t.math('DIVIDE', u, t.math('MAXIMUM', sw, 0.01)), 2.0), 1.0)
    Y = t.math('SUBTRACT', t.math('MULTIPLY', t.math('DIVIDE', v, t.math('MAXIMUM', sh, 0.01)), 2.0), 1.0)
    ax, ay = t.math('ABSOLUTE', X), t.math('ABSOLUTE', Y)
    r = t.vmath('LENGTH', t.comb(X, Y, 0.0))
    wx, wy, wz = t.sep(t.obj_co())
    dist = t.vmath('LENGTH', t.comb(wx, wy, 0.0))
    texel_n = t.math('DIVIDE', t.math('MULTIPLY', dist, 2 * math.pi / 8192 * 2.0), t.math('MAXIMUM', sw, 0.01))
    lw = t.math('MAXIMUM', 0.035, t.math('MULTIPLY', texel_n, 1.2))

    def band(val, centre, w):
        return t.maprange(t.math('ABSOLUTE', t.math('SUBTRACT', val, centre)), w, t.math('MULTIPLY', w, 0.5), 0.0, 1.0)

    def mx(*vals):
        out = vals[0]
        for v_ in vals[1:]:
            out = t.math('MAXIMUM', out, v_)
        return out
    ang = t.math('ARCTAN2', Y, X)
    spokes = t.math('MULTIPLY', t.maprange(t.math('ABSOLUTE', t.math('SINE', t.math('MULTIPLY', ang, 3.0))), t.math('MULTIPLY', lw, 2.0), lw, 0.0, 1.0),
                    t.math('MULTIPLY', t.math('GREATER_THAN', r, 0.30), t.math('LESS_THAN', r, 0.85)))
    circ = mx(band(r, 0.92, lw), band(r, 0.62, t.math('MULTIPLY', lw, 0.8)), band(r, 0.28, lw), spokes)
    hx = t.math('MAXIMUM', t.math('ADD', t.math('MULTIPLY', ax, 0.866), t.math('MULTIPLY', ay, 0.5)), ay)
    hexa = mx(band(hx, 0.90, lw), band(hx, 0.55, t.math('MULTIPLY', lw, 0.8)), t.math('LESS_THAN', r, t.math('MULTIPLY', lw, 2.5)))
    dd = t.math('ADD', ax, ay)
    cross = t.math('MULTIPLY', t.math('MAXIMUM', t.math('LESS_THAN', ax, t.math('MULTIPLY', lw, 0.7)), t.math('LESS_THAN', ay, t.math('MULTIPLY', lw, 0.7))), t.math('LESS_THAN', dd, 0.9))
    diam = mx(band(dd, 0.95, lw), band(dd, 0.50, t.math('MULTIPLY', lw, 0.8)), cross)
    lines = t.mix_f(t.math('LESS_THAN', shape, 0.33), t.mix_f(t.math('LESS_THAN', shape, 0.66), diam, hexa), circ)
    lines = t.math('MULTIPLY', lines, t.math('LESS_THAN', r, 1.0))
    glow = t.math('MULTIPLY', t.math('POWER', t.maprange(r, 1.0, 0.0, 0.0, 1.0), 1.5), 0.14)
    e = t.math('ADD', t.math('MULTIPLY', lines, E_SIGIL), glow)
    alpha = t.math('ADD', lines, t.math('MULTIPLY', glow, 3.0), clamp=True)
    em = t.emission(t.mix_rgb(t.math('MULTIPLY', lines, 0.25), hue, (1, 1, 1, 1)), e)
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    plug(mix.inputs[0], alpha)
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(em, mix.inputs[2])
    t.out(mix.outputs[0])
    return m


def mat_crystal():
    """v6b THE CRYSTAL SLABS (the references' giant lit panels standing on the spires): a saturated FIELD in the tower's hue
    (attribute rgb, alpha = strength) with thin white-hot cracks and a faint circuit grid. v6f: every line is CAPPED at a fraction
    of its cell - at 3 km a texel-wide line covered most of the slab and the field read pastel (the v6c..e "pale panels")"""
    m, t = new_mat('sky3d_crystal')
    col, a = t.attr()
    u, v, _ = t.sep(t.uv())
    vec = t.comb(u, v, 0.0)
    wx, wy, wz = t.sep(t.obj_co())
    dist = t.vmath('LENGTH', t.comb(wx, wy, 0.0))
    texel = t.math('MULTIPLY', dist, 2 * math.pi / 8192)
    vor = t.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature='DISTANCE_TO_EDGE')
    plug(vor.inputs['Vector'], t.vmath('SCALE', t.comb(u, v, t.math('MULTIPLY', wz, 0.001)), scale=1.0 / 11.0))
    plug(vor.inputs['Scale'], 1.0)
    plug(vor.inputs['Randomness'], 1.0)
    lw = t.math('MINIMUM', 0.045, t.math('DIVIDE', t.math('MAXIMUM', 0.45, t.math('MULTIPLY', texel, 1.3)), 11.0))   # a crack: a texel, but never more than 4.5 % of the cell
    crack = t.maprange(vor.outputs['Distance'], lw, t.math('MULTIPLY', lw, 0.3), 0.0, 1.0)
    gline_w = t.math('MINIMUM', 0.6, t.math('MAXIMUM', 0.35, t.math('MULTIPLY', texel, 1.2)))
    gcol, gline = t.brick(vec, 7.0, 4.5, gline_w, 0.03)
    gr, _, _ = t.sep_col(gcol)
    cells = t.maprange(gr, 0.0, 1.0, 0.72, 1.0)
    field = t.math('MULTIPLY', cells, t.maprange(t.noise(t.vmath('SCALE', vec, scale=0.045), 1.0, 2.0), 0.0, 1.0, 0.8, 1.1))
    e = t.math('ADD', t.math('MULTIPLY', field, 0.9), t.math('ADD', t.math('MULTIPLY', crack, 0.5), t.math('MULTIPLY', gline, 0.25)))
    hot = t.mix_rgb(t.math('MULTIPLY', crack, 0.35), col, (1.0, 1.0, 1.0, 1.0))                # only the cracks run white-hot
    t.out(t.emission(hot, t.math('MULTIPLY', e, t.math('MULTIPLY', a, E_CRYSTAL))))
    return m


def mat_lightfall():
    """v4 a LIGHT-FALL (reference 2): a vertical translucent sheet pouring down — bright at the top (UV v = 0), fading along its
    length, streaked, a brighter core; attribute rgb = hue, alpha = strength"""
    m, t = new_mat('sky3d_lightfall')
    col, a = t.attr()
    u, v, _ = t.sep(t.uv())
    fade = t.math('POWER', t.maprange(v, 0.0, 1.0, 1.0, 0.0), 1.6)
    wx, wy, wz = t.sep(t.obj_co())
    n = t.noise(t.comb(t.math('MULTIPLY', u, 6.0), t.math('MULTIPLY', v, 0.8), t.math('MULTIPLY', wx, 0.001)), 1.0, 3.0, 0.5)
    streak = t.maprange(n, 0.35, 0.70, 0.4, 1.4)
    core = t.math('ADD', 0.4, t.math('MULTIPLY', t.math('POWER', t.maprange(t.math('ABSOLUTE', t.math('SUBTRACT', u, 0.5)), 0.5, 0.0, 0.0, 1.0), 1.5), 0.6))
    e = t.math('MULTIPLY', t.math('MULTIPLY', fade, t.math('MULTIPLY', streak, core)), t.math('MULTIPLY', a, E_FALL))
    alpha = t.math('MULTIPLY', t.math('MULTIPLY', fade, core), t.math('MULTIPLY', streak, 0.85), clamp=True)
    em = t.emission(t.mix_rgb(t.math('MULTIPLY', fade, 0.25), col, (1, 1, 1, 1)), e)
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    plug(mix.inputs[0], alpha)
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(em, mix.inputs[2])
    t.out(mix.outputs[0])
    return m


def mat_ribbon():
    """v4 a glowing ROAD RIBBON (the references' sweeping orange / magenta highways): the deck surface itself glows in its hue
    with brighter edge and centre lines and a slow dash along it; UV u = metres along, v = 0..1 across; attribute rgb, alpha"""
    m, t = new_mat('sky3d_ribbon')
    col, a = t.attr()
    u, v, _ = t.sep(t.uv())
    wx, wy, wz = t.sep(t.obj_co())
    dist = t.vmath('LENGTH', t.comb(wx, wy, 0.0))
    lw = t.math('MAXIMUM', 0.05, t.math('MULTIPLY', dist, 2 * math.pi / 8192 * 1.2 / 30.0))

    def band(val, centre, w):
        return t.maprange(t.math('ABSOLUTE', t.math('SUBTRACT', val, centre)), w, t.math('MULTIPLY', w, 0.5), 0.0, 1.0)
    lines = t.math('MAXIMUM', t.math('MAXIMUM', band(v, 0.5, lw), band(v, 0.06, lw)), band(v, 0.94, lw))
    dash = t.maprange(t.noise(t.comb(t.math('MULTIPLY', u, 0.02), 0.0, t.math('MULTIPLY', wy, 0.001)), 1.0, 1.0), 0.40, 0.60, 0.6, 1.3)
    e = t.math('MULTIPLY', a, t.math('ADD', t.math('MULTIPLY', E_RIBBON, t.math('ADD', 0.7, t.math('MULTIPLY', dash, 0.3))), lines))
    t.out(t.emission(t.mix_rgb(t.math('MULTIPLY', lines, 0.55), col, (1, 1, 1, 1)), e))
    return m


def neon_ring(acc, x, y, z, Rr, tube_r, col, n=48, tilt=0.0):
    """a neon RING (a closed loop of tubes) round (x, y) at height z, radius Rr, tilted `tilt` rad about the x axis"""
    pts = []
    for i in range(n + 1):
        a_ = 2 * math.pi * i / n
        px, py, pz = Rr * math.cos(a_), Rr * math.sin(a_), 0.0
        py, pz = py * math.cos(tilt) - pz * math.sin(tilt), py * math.sin(tilt) + pz * math.cos(tilt)
        pts.append((x + px, y + py, z + pz))
    for i in range(n):
        tube(acc, pts[i], pts[i + 1], tube_r, tube_r, col, 6)


def mat_hull():
    m, t = new_mat('sky3d_hull')
    t.out(t.principled((0.018, 0.012, 0.016), 0.28, 0.6, BODY_FLOOR, 0.8))
    return m


def mat_shiphull():
    """v5b a battlecruiser's hull: dark matte steel with a faint sheen and the painted ambient (mat_hull's mirror finish turned the
    nebula into a beige paper plane)"""
    m, t = new_mat('sky3d_shiphull')
    t.out(t.principled((0.012, 0.011, 0.015), 0.85, 0.0, tuple(c * 2.0 for c in BODY_FLOOR), 1.0))   # v5f: diffuse, near-black — a silhouette with lit edges, never a mirror of the city
    return m


def mat_rock():
    m, t = new_mat('sky3d_rock')
    n = t.noise(t.vmath('SCALE', t.obj_co(), scale=0.01), 1.0, 5.0, 0.7)
    t.out(t.principled(t.scale_rgb((0.020, 0.014, 0.014), t.maprange(n, 0.0, 1.0, 0.5, 1.4)), 0.9, 0.0, BODY_FLOOR, 0.7))
    return m


def mat_planet(bd):
    """v4 a GAS GIANT: latitude bands from a colour cycle (bd['cols'], bd['bands'] repeats) whose latitude is warped by two noise
    scales (eddies and storms), a bright storm spot, fine grain, limb darkening, an atmosphere rim; painted mostly lit — the
    references' planets are front-lit with a soft terminator toward the moon. Object coords are the sphere's own (radius R)."""
    m, t = new_mat('sky3d_gas_' + bd['name'])
    R = bd['R']
    geo = t.node('ShaderNodeNewGeometry')
    ndl = t.vmath('DOT_PRODUCT', geo.outputs['Normal'], moon_dir())
    lit = t.maprange(ndl, -0.3, 0.65, 0.18, 1.0)
    p = t.vmath('SCALE', t.obj_co(), scale=1.0 / R)
    px, py, pz = t.sep(p)
    w1 = t.noise(t.vmath('SCALE', p, scale=2.2), 1.0, 5.0, 0.55)
    w2 = t.noise(t.vmath('ADD', t.vmath('SCALE', p, scale=6.5), (3.3, 1.1, 7.7)), 1.0, 4.0, 0.6)
    lat = t.math('ADD', pz, t.math('ADD', t.math('MULTIPLY', t.math('SUBTRACT', w1, 0.5), 0.22), t.math('MULTIPLY', t.math('SUBTRACT', w2, 0.5), 0.07)))
    band_t = t.math('FRACT', t.math('MULTIPLY', t.math('ADD', lat, 1.0), bd['bands'] / 2.0))
    cols = bd['cols']
    n = len(cols)
    stops = []
    for i in range(n):
        stops.append((i / n, cols[i]))
        stops.append(((i + 0.62) / n, cols[i]))
    stops.append((1.0, cols[0]))
    col = t.ramp(band_t, stops)
    var = t.maprange(t.noise(t.vmath('SCALE', p, scale=1.1), 1.0, 2.0), 0.0, 1.0, 0.75, 1.2)
    col = t.scale_rgb(col, var)
    if bd.get('spot'):
        sp = t.math('GREATER_THAN', t.noise(t.comb(t.math('MULTIPLY', px, 1.6), t.math('MULTIPLY', py, 1.6), t.math('MULTIPLY', pz, 5.0)), 1.0, 3.0, 0.5), 0.66)
        col = t.mix_rgb(sp, col, bd['spot'])
    fine = t.maprange(t.noise(t.vmath('SCALE', p, scale=14.0), 1.0, 4.0, 0.6), 0.0, 1.0, 0.85, 1.12)
    lw = t.node('ShaderNodeLayerWeight')
    plug(lw.inputs['Blend'], 0.5)
    facing = lw.outputs['Facing']
    limb = t.maprange(t.math('POWER', facing, 1.4), 0.0, 1.0, 1.0, 0.30)
    body = t.scale_rgb(col, t.math('MULTIPLY', t.math('MULTIPLY', lit, limb), fine))
    if bd.get('atmo'):
        rim = t.math('POWER', t.maprange(facing, 0.0, 0.18, 1.0, 0.0), 2.0)
        body = t.vmath('ADD', body, t.scale_rgb(bd['atmo'], t.math('MULTIPLY', rim, 0.20)))
    dim = bd.get('dim', 1.0)                                                     # v5: distant worlds are dimmer and hazed (depth)
    body = t.mix_rgb((1.0 - dim) * 0.5, body, (0.12, 0.14, 0.35, 1.0))
    t.out(t.emission(body, E_PLANET * dim * bd.get('gain', 1.0)))                # v6: bd['gain'] — the red giant is a hero
    return m


def mat_cracked(bd):
    """v4 a CRACKED planet (the references' lava / energy worlds): dark mottled rock split into plates by Voronoi cell edges at two
    scales; the cracks glow in bd['vein'] with a white-hot core and a wide soft halo, and stay lit on the dark side"""
    m, t = new_mat('sky3d_cracked_' + bd['name'])
    R = bd['R']
    geo = t.node('ShaderNodeNewGeometry')
    ndl = t.vmath('DOT_PRODUCT', geo.outputs['Normal'], moon_dir())
    lit = t.maprange(ndl, -0.3, 0.65, 0.14, 1.0)
    p = t.vmath('SCALE', t.obj_co(), scale=1.0 / R)
    rockA, rockB = bd['rock']
    n = t.noise(t.vmath('SCALE', p, scale=3.0), 1.0, 6.0, 0.65)
    base = t.mix_rgb(t.maprange(n, 0.35, 0.65, 0.0, 1.0), rockA, rockB)
    wn = t.node('ShaderNodeTexNoise', noise_dimensions='3D')
    plug(wn.inputs['Vector'], t.vmath('SCALE', p, scale=1.7))
    plug(wn.inputs['Scale'], 1.0)
    plug(wn.inputs['Detail'], 2.0)
    wq = t.vmath('ADD', p, t.vmath('SCALE', t.vmath('SUBTRACT', wn.outputs['Color'], (0.5, 0.5, 0.5)), scale=0.25))
    v1 = t.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature='DISTANCE_TO_EDGE')
    plug(v1.inputs['Vector'], wq)
    plug(v1.inputs['Scale'], 2.6)
    v2 = t.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature='DISTANCE_TO_EDGE')
    plug(v2.inputs['Vector'], t.vmath('ADD', wq, (4.4, 1.2, 7.1)))
    plug(v2.inputs['Scale'], 6.0)
    c1 = t.math('POWER', t.maprange(v1.outputs['Distance'], 0.0, 0.045, 1.0, 0.0), 1.5)
    c2 = t.math('POWER', t.maprange(v2.outputs['Distance'], 0.0, 0.060, 1.0, 0.0), 1.5)
    crack = t.math('MAXIMUM', c1, t.math('MULTIPLY', c2, 0.7))
    glow = t.math('ADD', t.math('POWER', t.maprange(v1.outputs['Distance'], 0.0, 0.30, 1.0, 0.0), 2.2),
                  t.math('MULTIPLY', t.math('POWER', t.maprange(v2.outputs['Distance'], 0.0, 0.25, 1.0, 0.0), 2.2), 0.5))
    alive = t.maprange(t.noise(t.vmath('ADD', t.vmath('SCALE', p, scale=1.4), (5.5, 2.2, 8.8)), 1.0, 2.0), 0.38, 0.62, 0.15, 1.0)
    vein = bd['vein']
    hotc = tuple(0.55 + 0.45 * c for c in vein)
    lw = t.node('ShaderNodeLayerWeight')
    plug(lw.inputs['Blend'], 0.5)
    facing = lw.outputs['Facing']
    limb = t.maprange(t.math('POWER', facing, 1.3), 0.0, 1.0, 1.0, 0.40)
    body = t.scale_rgb(base, t.math('MULTIPLY', t.math('MULTIPLY', lit, limb), 0.16))
    veins = t.vmath('ADD', t.scale_rgb(hotc, t.math('MULTIPLY', crack, 0.16)), t.scale_rgb(vein, t.math('MULTIPLY', glow, 0.025)))
    em = t.vmath('ADD', body, t.scale_rgb(veins, t.math('MULTIPLY', alive, limb)))
    dim = bd.get('dim', 1.0)                                                     # v5
    em = t.mix_rgb((1.0 - dim) * 0.5, em, (0.12, 0.14, 0.35, 1.0))
    t.out(t.emission(em, dim))
    return m


def mat_moonrock(bd):
    """v4 a grey (or tinted) moon: cratered noise, lit toward the moon direction, limb-darkened"""
    m, t = new_mat('sky3d_moonrock_' + bd['name'])
    R = bd['R']
    geo = t.node('ShaderNodeNewGeometry')
    ndl = t.vmath('DOT_PRODUCT', geo.outputs['Normal'], moon_dir())
    lit = t.maprange(ndl, -0.25, 0.65, 0.20, 1.0)
    p = t.vmath('SCALE', t.obj_co(), scale=1.0 / R)
    crat = t.noise(t.vmath('SCALE', p, scale=4.0), 1.0, 6.0, 0.6)
    crat2 = t.noise(t.vmath('ADD', t.vmath('SCALE', p, scale=12.0), (2.0, 5.0, 1.0)), 1.0, 4.0, 0.5)
    shade = t.maprange(t.math('ADD', t.math('MULTIPLY', crat, 0.7), t.math('MULTIPLY', crat2, 0.3)), 0.3, 0.75, 0.0, 1.0)
    colA, colB = bd.get('cols', ((0.32, 0.30, 0.33), (0.62, 0.60, 0.62)))
    col = t.mix_rgb(shade, colA, colB)
    lw = t.node('ShaderNodeLayerWeight')
    plug(lw.inputs['Blend'], 0.5)
    limb = t.maprange(t.math('POWER', lw.outputs['Facing'], 1.3), 0.0, 1.0, 1.0, 0.35)
    dim = bd.get('dim', 1.0)                                                     # v5
    t.out(t.emission(t.mix_rgb((1.0 - dim) * 0.5, t.scale_rgb(col, t.math('MULTIPLY', lit, limb)), (0.12, 0.14, 0.35, 1.0)), 0.16 * dim))
    return m


def mat_galaxy(bd):
    """v4 a face-on spiral galaxy on a disc of radius R: a white core, a bulge, `arms` log-spiral arms with turbulence and bright
    knots in bd['knot'], translucent toward the edge"""
    m, t = new_mat('sky3d_galaxy_' + bd['name'])
    R = bd['R']
    p = t.obj_co()
    px, py, pz = t.sep(p)
    u = t.math('DIVIDE', t.vmath('LENGTH', t.comb(px, py, 0.0)), R)
    ang = t.math('ARCTAN2', py, px)
    core = t.math('EXPONENT', t.math('MULTIPLY', t.math('POWER', t.math('DIVIDE', u, 0.10), 2.0), -1.0))
    bulge = t.math('EXPONENT', t.math('MULTIPLY', t.math('POWER', t.math('DIVIDE', u, 0.28), 2.0), -1.0))
    ph = t.math('SUBTRACT', t.math('MULTIPLY', ang, bd['arms']), t.math('MULTIPLY', t.math('LOGARITHM', t.math('ADD', u, 0.06), 2.718), 5.0))
    a = t.math('POWER', t.math('ADD', 0.5, t.math('MULTIPLY', t.math('COSINE', ph), 0.5)), 2.2)
    band = t.math('EXPONENT', t.math('MULTIPLY', t.math('POWER', t.math('DIVIDE', t.math('SUBTRACT', u, 0.55), 0.32), 2.0), -1.0))
    turb = t.maprange(t.noise(t.comb(t.math('MULTIPLY', px, 6.0 / R), t.math('MULTIPLY', py, 6.0 / R), 1.7), 1.0, 5.0, 0.6), 0.3, 0.7, 0.4, 1.5)
    armv = t.math('MULTIPLY', t.math('MULTIPLY', band, a), turb)
    knots = t.math('MULTIPLY', t.math('GREATER_THAN', t.noise(t.comb(t.math('MULTIPLY', px, 14.0 / R), t.math('MULTIPLY', py, 14.0 / R), 4.1), 1.0, 3.0), 0.68), armv)
    corecol, armcol, knotcol = bd['core'], bd['arm'], bd['knot']
    em = t.vmath('ADD', t.vmath('ADD', t.scale_rgb(corecol, core), t.scale_rgb(t.mix_rgb(0.5, corecol, armcol), t.math('MULTIPLY', bulge, 0.45))),
                 t.vmath('ADD', t.scale_rgb(armcol, t.math('MULTIPLY', armv, 0.55)), t.scale_rgb(knotcol, t.math('MULTIPLY', knots, 0.6))))
    alpha = t.math('MULTIPLY', t.math('ADD', t.math('ADD', core, t.math('MULTIPLY', bulge, 0.8)), t.math('ADD', t.math('MULTIPLY', armv, 0.9), knots), clamp=True),
                   t.maprange(u, 0.7, 1.0, 1.0, 0.0))
    emn = t.emission(em, E_GALAXY)
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    plug(mix.inputs[0], alpha)
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(emn, mix.inputs[2])
    t.out(mix.outputs[0])
    return m


def mat_asteroid(name, target=None):
    """v4 a rock lit from `target` (the black hole's centre: the disc glows on the rocks' near sides) or, with no target, from the
    moon; a dark mottled body with a warm lit rim and the painted ambient"""
    m, t = new_mat(name)
    geo = t.node('ShaderNodeNewGeometry')
    if target is not None:
        oi = t.node('ShaderNodeObjectInfo')
        ldir = t.vmath('NORMALIZE', t.vmath('SUBTRACT', (target.x, target.y, target.z), oi.outputs['Location']))
        rimcol = (1.0, 0.55, 0.22)
    else:
        ldir = moon_dir()
        rimcol = (0.9, 0.45, 0.35)
    ndl = t.vmath('DOT_PRODUCT', geo.outputs['Normal'], ldir)
    lit = t.maprange(ndl, -0.2, 0.8, 0.0, 1.0)
    n = t.noise(t.vmath('SCALE', t.obj_co(), scale=1.5), 1.0, 4.0, 0.6)
    rock = t.mix_rgb(t.maprange(n, 0.3, 0.7, 0.0, 1.0), (0.030, 0.024, 0.026), (0.075, 0.062, 0.062))
    lw = t.node('ShaderNodeLayerWeight')
    plug(lw.inputs['Blend'], 0.5)
    rim = t.math('POWER', t.maprange(lw.outputs['Facing'], 0.0, 0.35, 1.0, 0.0), 2.5)
    em = t.vmath('ADD', t.vmath('ADD', t.scale_rgb(rock, t.math('MULTIPLY', t.math('ADD', 0.10, t.math('MULTIPLY', lit, 0.9)), E_ROCK * 1.2)),
                                  t.scale_rgb(rimcol, t.math('MULTIPLY', t.math('MULTIPLY', rim, lit), 0.8))), BODY_FLOOR)
    t.out(t.emission(em, 1.0))
    return m


def mat_ring(bd):
    """the ring: density bands by radius (gaps like Saturn's), fine grain, the planet's SHADOW where the ring lies behind the
    planet along the moon direction; the colour is a ramp over the ring's width (bd['ring'][3] = stops); translucent"""
    inner, outer, _, rc = bd['ring']
    R = bd['R']
    m, t = new_mat('sky3d_ring_' + bd['name'])
    p = t.obj_co()
    px, py, pz = t.sep(p)
    rad = t.math('DIVIDE', t.vmath('LENGTH', t.comb(px, py, 0.0)), R)
    u = t.maprange(rad, inner, outer, 0.0, 1.0)
    dens = t.ramp(u, [(0.0, (0, 0, 0)), (0.05, (0.9, 0.9, 0.9)), (0.27, (0.4, 0.4, 0.4)), (0.33, (0.95, 0.95, 0.95)), (0.58, (0.75, 0.75, 0.75)),
                      (0.64, (0.12, 0.12, 0.12)), (0.70, (0.8, 0.8, 0.8)), (0.94, (0.5, 0.5, 0.5)), (1.0, (0, 0, 0))])
    densf, _, _ = t.sep_col(dens)
    fine = t.maprange(t.noise(t.comb(t.math('MULTIPLY', rad, 40.0), 0.0, 0.0), 1.0, 2.0), 0.0, 1.0, 0.6, 1.3)
    alpha = t.math('MULTIPLY', densf, fine, clamp=True)
    # Ring coordinates are local to the inclined planet. Transform the WORLD
    # illumination vector too; mixing spaces drew a rectangular shadow stripe
    # which became conspicuous when the giant was lifted above the skyline.
    light_xform = t.node('ShaderNodeVectorTransform', vector_type='VECTOR',
                         convert_from='WORLD', convert_to='OBJECT')
    plug(light_xform.inputs['Vector'], moon_dir())
    L = t.vmath('NORMALIZE', light_xform.outputs['Vector'])
    dL = t.vmath('DOT_PRODUCT', p, L)
    perp = t.vmath('SUBTRACT', p, t.vmath('SCALE', L, scale=dL))
    shadow = t.math('MULTIPLY', t.maprange(t.vmath('LENGTH', perp), R * .96, R * 1.06, 1.0, 0.0),
                    t.maprange(dL, -R * .04, R * .04, 1.0, 0.0))
    lit = t.math('SUBTRACT', 1.0, t.math('MULTIPLY', shadow, 0.85))
    colr = t.ramp(u, list(rc)) if isinstance(rc, (list, tuple)) and rc and isinstance(rc[0], (list, tuple)) and len(rc[0]) == 2 else rc
    colv = t.scale_rgb(colr, t.math('MULTIPLY', t.maprange(u, 0.0, 1.0, 1.1, 0.75), lit))
    em = t.emission(colv, E_RING * bd.get('dim', 1.0))
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    plug(mix.inputs[0], alpha)
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(em, mix.inputs[2])
    t.out(mix.outputs[0])
    return m


def mat_lensarc(bd):
    """v5 the black hole's LENSED FAR SIDE (the Interstellar halo): the disc's hidden half bent over and under the shadow — an
    annulus in the VIEW plane from 1.05 to 1.9 R, brightest on the axis perpendicular to the disc's long axis (image up / down),
    gone along the long axis where the real disc is; hot at the shadow's edge, cooling outward; streaked along the orbit"""
    R = bd['R']
    m, t = new_mat('sky3d_lensarc_' + bd['name'])
    p = t.obj_co()
    px, py, pz = t.sep(p)
    rad = t.math('DIVIDE', t.vmath('LENGTH', t.comb(px, py, 0.0)), R)
    ang = t.math('ARCTAN2', py, px)
    u = t.maprange(rad, 1.05, 1.9, 0.0, 1.0)
    over = t.math('POWER', t.math('ABSOLUTE', t.math('SINE', ang)), 1.6)
    fall = t.math('POWER', t.maprange(u, 0.0, 1.0, 1.0, 0.0), 2.4)
    streak = t.maprange(t.noise(t.comb(t.math('MULTIPLY', rad, 9.0), t.math('MULTIPLY', ang, 3.0), 0.7), 1.0, 3.0, 0.6), 0.35, 0.65, 0.55, 1.35)
    hot, mid, far, edge = bd['col_hot'], bd['col_mid'], bd['col_far'], bd['col_edge']
    col = t.ramp(u, [(0.0, hot), (0.12, mid), (0.45, far), (1.0, edge)])
    bright = t.math('MULTIPLY', t.math('MULTIPLY', fall, over), streak)
    e = t.math('MULTIPLY', bright, E_HOLE * 1.05 * bd.get('dim', 1.0))
    alpha = t.math('MULTIPLY', bright, 1.6, clamp=True)
    em = t.emission(col, e)
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    plug(mix.inputs[0], alpha)
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(em, mix.inputs[2])
    t.out(mix.outputs[0])
    return m


def mat_disc(bd):
    """v4 the black hole's accretion disc, seen obliquely: `arms` log-spiral arms with turbulence and dark dust lanes, white-hot at
    the inner edge cooling through orange -> magenta -> violet to the edge; Doppler-bright on one side; translucent outward"""
    R = bd['R']
    m, t = new_mat('sky3d_disc_' + bd['name'])
    p = t.obj_co()
    px, py, pz = t.sep(p)
    rad = t.math('DIVIDE', t.vmath('LENGTH', t.comb(px, py, 0.0)), R)
    ang = t.math('ARCTAN2', py, px)
    u = t.maprange(rad, 1.0, bd['disc_out'], 0.0, 1.0)
    ph = t.math('SUBTRACT', t.math('MULTIPLY', ang, bd['arms']), t.math('MULTIPLY', t.math('LOGARITHM', t.math('MAXIMUM', rad, 0.5), 2.718), 4.2))
    arm = t.math('POWER', t.math('ADD', 0.5, t.math('MULTIPLY', t.math('SINE', ph), 0.5)), 1.6)
    lrad = t.math('LOGARITHM', t.math('MAXIMUM', rad, 0.5), 2.718)
    turb = t.maprange(t.noise(t.comb(t.math('MULTIPLY', lrad, 7.0), t.math('MULTIPLY', ang, 2.2), 0.0), 1.0, 3.0, 0.6), 0.35, 0.65, 0.60, 1.35)   # v4l: streaks ALONG the orbit (the references' swirl), never blotches
    lanes = t.maprange(t.noise(t.comb(t.math('MULTIPLY', lrad, 4.0), t.math('MULTIPLY', ang, 0.6), 3.3), 1.0, 2.0, 0.5), 0.42, 0.60, 0.45, 1.0)   # v4l: soft dust lanes that follow the orbit
    turb2 = t.maprange(t.noise(t.comb(t.math('MULTIPLY', lrad, 18.0), t.math('MULTIPLY', ang, 6.0), 1.7), 1.0, 2.0, 0.5), 0.35, 0.65, 0.78, 1.22)   # v5: a finer octave of streaks
    hot, mid, far, edge = bd['col_hot'], bd['col_mid'], bd['col_far'], bd['col_edge']
    col = t.ramp(u, [(0.0, hot), (0.12, hot), (0.32, mid), (0.58, far), (0.82, edge), (1.0, (0.03, 0.02, 0.10))])
    col = t.mix_rgb(t.maprange(t.math('SINE', ang), -1.0, 1.0, 0.0, 0.40), col, (*hot, 1.0))   # v5: the Doppler side runs hotter
    bright = t.math('MULTIPLY', t.math('MULTIPLY', t.math('POWER', t.maprange(u, 0.0, 1.0, 1.0, 0.0), 1.4), t.math('ADD', 0.10, t.math('MULTIPLY', arm, 0.90))),
                    t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', turb, turb2), lanes), t.math('ADD', 1.0, t.math('MULTIPLY', t.math('SINE', ang), 0.60))))   # v5
    rim = t.math('MULTIPLY', t.math('POWER', t.maprange(u, 0.0, 0.10, 1.0, 0.0), 2.0), 0.18)
    e = t.math('ADD', t.math('MULTIPLY', bright, E_HOLE * bd.get('dim', 1.0)), rim)
    alpha = t.math('MULTIPLY', t.maprange(u, 0.60, 1.0, 1.0, 0.0), t.math('ADD', 0.75, t.math('MULTIPLY', t.math('MULTIPLY', arm, turb), 0.25)), clamp=True)
    em = t.emission(col, e)
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    plug(mix.inputs[0], alpha)
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(em, mix.inputs[2])
    t.out(mix.outputs[0])
    return m


def mat_storm():
    """v2 THE STORM: a ring of cumulonimbus round THE ORIGIN — lumpy density from two noise octaves inside a radial band that
    fades to the top and bottom; grey-violet scatter so the red eye and the violet lights inside colour it; a faint self-glow.
    Built in the storm object's LOCAL coords (origin = the ring's centre at mid height)."""
    r0, r1 = ORIGIN['storm_r']
    z0, z1 = ORIGIN['storm_z']
    half = (z1 - z0) / 2
    m, t = new_mat('sky3d_storm')
    p = t.obj_co()
    px, py, pz = t.sep(p)
    rad = t.vmath('LENGTH', t.comb(px, py, 0.0))
    ring = t.math('MULTIPLY', t.maprange(rad, r0 * 0.8, r0 * 1.25, 0.0, 1.0), t.maprange(rad, r1 * 0.7, r1, 1.0, 0.0))
    vert = t.maprange(t.math('ABSOLUTE', pz), half * 0.45, half, 1.0, 0.0)
    # cumulonimbus: big lumps with a hard-ish edge (the threshold), fine detail on the lumps' surfaces
    big = t.noise(t.vmath('ADD', t.vmath('SCALE', p, scale=1.0 / 620.0), (3.3, 8.1, 1.2)), 1.0, 3.0, 0.5)
    fine = t.noise(t.vmath('SCALE', p, scale=1.0 / 170.0), 1.0, 5.0, 0.65)
    lumps = t.math('ADD', t.math('MULTIPLY', big, 0.62), t.math('MULTIPLY', fine, 0.38))
    shape = t.math('MULTIPLY', t.math('MULTIPLY', t.maprange(lumps, 0.47, 0.56, 0.0, 1.0), ring), vert)
    dens = t.math('MULTIPLY', shape, ORIGIN['storm_d'])
    sc = t.node('ShaderNodeVolumeScatter')
    plug(sc.inputs['Color'], (0.85, 0.72, 1.0, 1))                 # v4: violet-white cumulus, coloured by the lights inside
    plug(sc.inputs['Density'], dens)
    plug(sc.inputs['Anisotropy'], 0.3)
    ab = t.node('ShaderNodeVolumeAbsorption')
    plug(ab.inputs['Color'], (0.55, 0.42, 0.70, 1))
    plug(ab.inputs['Density'], t.math('MULTIPLY', dens, 0.25))
    em = t.node('ShaderNodeEmission')
    plug(em.inputs['Color'], (0.62, 0.20, 0.95, 1))
    plug(em.inputs['Strength'], t.math('MULTIPLY', shape, 8.0e-4))       # v4h: W per metre — the cloud glows violet from inside like a lit nebula
    add1 = t.node('ShaderNodeAddShader')
    t.t.links.new(sc.outputs[0], add1.inputs[0])
    t.t.links.new(ab.outputs[0], add1.inputs[1])
    add2 = t.node('ShaderNodeAddShader')
    t.t.links.new(add1.outputs[0], add2.inputs[0])
    t.t.links.new(em.outputs[0], add2.inputs[1])
    t.out(volume=add2.outputs[0])
    m.cycles.volume_step_rate = 0.12
    m.cycles.homogeneous_volume = False
    return m


def mat_sign_face(col, strength):
    m, t = new_mat('sky3d_sign_' + '_'.join(f'{c:.2f}' for c in col))
    t.out(t.emission((*col, 1), strength))
    return m


def world_sky():
    """v4 THE REFERENCE COPY — the sky is SPACE. A saturated indigo floor (the references' darkest tenth is (21,19,35): never
    grey), domain-warped nebula in five hues (magenta / pink / violet / orange / teal) with dust lanes and fine filaments over
    about half of the upper sky, brighter round the black hole and the galaxies; three star layers — ~50k faint, ~10k medium,
    ~70 big stars with four-point flares — sized to hold a texel of the 8192 ship. All in W (display white = 1.0). The planets,
    black hole and galaxies are GEOMETRY (make_bodies)."""
    w = bpy.data.worlds.new('sky3d_world')
    w.use_nodes = True
    w.node_tree.nodes.clear()
    t = NT(w.node_tree)
    d = t.node('ShaderNodeTexCoord').outputs['Generated']          # in a world shader: the unit view direction (z = sin(elevation))
    x, y, z = t.sep(d)
    grad = t.ramp(z, [(0.0, SKY_HORIZON), (0.22, SKY_MID), (0.60, SKY_HIGH), (1.0, SKY_ZENITH)])
    above = t.maprange(z, -0.05, 0.10, 0.0, 1.0)
    # nebula: a domain warp (the noise node's Color output is a 3-vector), filaments + clouds, fine texture, dust lanes
    wn = t.node('ShaderNodeTexNoise', noise_dimensions='3D')
    plug(wn.inputs['Vector'], t.vmath('SCALE', d, scale=1.1))
    plug(wn.inputs['Scale'], 1.0)
    plug(wn.inputs['Detail'], 3.0)
    plug(wn.inputs['Roughness'], 0.5)
    dw = t.vmath('ADD', d, t.vmath('SCALE', t.vmath('SUBTRACT', wn.outputs['Color'], (0.5, 0.5, 0.5)), scale=0.55))
    f1 = t.math('POWER', t.maprange(t.noise(t.vmath('SCALE', dw, scale=2.3), 1.0, 7.0, 0.62), 0.49, 0.78, 0.0, 1.0), 1.9)   # v4k: clouds with black between — the references' zenith is a third void
    f2 = t.math('POWER', t.maprange(t.noise(t.vmath('ADD', t.vmath('SCALE', dw, scale=1.25), (4.2, 1.7, 8.3)), 1.0, 6.0, 0.55), 0.51, 0.80, 0.0, 1.0), 1.8)
    fine = t.maprange(t.noise(t.vmath('ADD', t.vmath('SCALE', d, scale=4.0), (1.3, 6.4, 2.9)), 1.0, 6.0, 0.72), 0.30, 0.72, 0.5, 1.35)
    dust = t.maprange(t.noise(t.vmath('ADD', t.vmath('SCALE', dw, scale=4.6), (9.1, 2.2, 3.3)), 1.0, 5.0, 0.7), 0.47, 0.57, 1.0, 0.10)
    huet = t.noise(t.vmath('ADD', t.vmath('SCALE', d, scale=0.75), (2.2, 9.1, 4.4)), 1.0, 2.0, 0.5)
    nebcol = t.ramp(huet, [(0.28, NEB_MAGENTA), (0.42, NEB_PINK), (0.52, NEB_ORANGE), (0.57, NEB_VIOLET), (0.68, NEB_TEAL), (0.80, NEB_BLUE)])   # v6: jewel tones + a deep blue band (v4k: pink and magenta first, orange narrow)
    amount = t.math('MULTIPLY', t.math('ADD', t.math('MULTIPLY', f1, 0.95), t.math('MULTIPLY', f2, 0.75)), t.math('MULTIPLY', fine, dust))
    boost = 1.0
    for (caz, cel, gain) in NEBULA_POLICY['cores_after']:
        dirv = body_frame(caz, cel)[1]
        dot = t.vmath('DOT_PRODUCT', d, (dirv.x, dirv.y, dirv.z))
        boost = t.math('ADD', boost, t.math('MULTIPLY', t.math('POWER', t.maprange(dot, 0.55, 1.0, 0.0, 1.0), 2.0), gain))
    neb = t.scale_rgb(nebcol, t.math('MULTIPLY', t.math('MULTIPLY', amount, boost), t.math('MULTIPLY', above, NEB_GAIN)))
    glowf = t.math('POWER', t.maprange(t.noise(t.vmath('ADD', t.vmath('SCALE', dw, scale=0.9), (6.6, 3.1, 1.9)), 1.0, 3.0, 0.5), 0.47, 0.78, 0.0, 1.0), 1.5)   # v4k
    glowf = t.math('MULTIPLY', glowf, t.maprange(t.noise(t.vmath('ADD', t.vmath('SCALE', d, scale=3.2), (0.7, 4.4, 8.2)), 1.0, 4.0, 0.6), 0.30, 0.75, 0.45, 1.3))
    neb = t.vmath('ADD', neb, t.scale_rgb(SKY_GLOW, t.math('MULTIPLY', t.math('MULTIPLY', glowf, boost), t.math('MULTIPLY', above, 1.8))))   # v4e: patchy indigo — the voids between stay black
    # Quiet background windows give the title and transit landmarks a silhouette.
    azimuth = t.math('ARCTAN2', x, y)
    elevation = t.math('ARCSINE', z)
    reduction = 0.0
    def smooth_weight(value):
        return t.math('MULTIPLY', t.math('MULTIPLY', value, value),
                      t.math('SUBTRACT', 3.0, t.math('MULTIPLY', 2.0, value)))
    for sector in QUIET_SECTORS:
        delta = t.math('SUBTRACT', azimuth, sector['az'] * D2R)
        delta = t.math('ABSOLUTE', t.math('ARCTAN2', t.math('SINE', delta), t.math('COSINE', delta)))
        horizontal = t.maprange(delta, (sector['half_width'] + sector['feather_az']) * D2R,
                                sector['half_width'] * D2R, 0.0, 1.0)
        below = t.maprange(elevation, (sector['el_min'] - sector['feather_el']) * D2R, sector['el_min'] * D2R, 0.0, 1.0)
        above_sector = t.maprange(elevation, sector['el_max'] * D2R, (sector['el_max'] + sector['feather_el']) * D2R, 1.0, 0.0)
        weight = t.math('MULTIPLY', smooth_weight(horizontal),
                        t.math('MULTIPLY', smooth_weight(below), smooth_weight(above_sector)))
        reduction = t.math('MAXIMUM', reduction, t.math('MULTIPLY', weight, 1.0-sector['nebula_floor']))
    neb = t.scale_rgb(neb, t.math('SUBTRACT', 1.0, reduction))

    def stars(scale, thr, lo, hi, keep, off, flare=0.0):
        """one Voronoi layer: a soft core of radius thr (scaled units) in cells whose red random > keep, brightness lo..hi W by the
        green random, colour by the blue random; flare > 0 adds four-point diffraction arms of that length (scaled units)"""
        vor = t.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature='F1', distance='EUCLIDEAN')
        dv = t.vmath('ADD', d, off)
        plug(vor.inputs['Vector'], dv)
        plug(vor.inputs['Scale'], scale)
        plug(vor.inputs['Randomness'], 1.0)
        core = t.math('POWER', t.maprange(vor.outputs['Distance'], thr, thr * 0.25, 0.0, 1.0), 1.5)
        sr, sg, sb = t.sep_col(vor.outputs['Color'])
        gate = t.math('GREATER_THAN', sr, keep)
        bright = t.maprange(sg, 0.0, 1.0, lo, hi)
        col = t.ramp(sb, [(0.0, (0.72, 0.80, 1.0)), (0.55, (1.0, 0.97, 0.92)), (0.80, (1.0, 0.86, 0.72)), (1.0, (1.0, 0.62, 0.62))])
        e = t.math('MULTIPLY', core, t.math('MULTIPLY', gate, bright))
        if flare > 0:
            offv = t.vmath('SUBTRACT', dv, vor.outputs['Position'])            # Position is in the INPUT space (measured 2026-09-25)
            east = t.vmath('NORMALIZE', t.vmath('CROSS_PRODUCT', (0.0, 0.0, 1.0), d))
            upv = t.vmath('CROSS_PRODUCT', d, east)
            ox = t.vmath('DOT_PRODUCT', offv, east)
            oy = t.vmath('DOT_PRODUCT', offv, upv)
            L = flare / scale

            def arm(a, b):
                along = t.math('EXPONENT', t.math('MULTIPLY', t.math('ABSOLUTE', a), -3.0 / L))
                across = t.math('EXPONENT', t.math('MULTIPLY', t.math('ABSOLUTE', b), -1.0 / (L * 0.09)))
                return t.math('MULTIPLY', along, across)
            fl = t.math('ADD', arm(ox, oy), arm(oy, ox))
            e = t.math('ADD', e, t.math('MULTIPLY', fl, t.math('MULTIPLY', gate, t.math('MULTIPLY', bright, 0.9))))
        return t.scale_rgb(col, e)
    # v8: faint depth begins above the skyline; the prominent star cores/flares
    # occupy the upper sky instead of reading as lamps attached to tower crowns.
    faint = t.scale_rgb(stars(90.0, 0.09, 0.015, 0.065, 0.50, (0.0, 0.0, 0.0)),
                        t.maprange(z, math.sin(15 * D2R), math.sin(32 * D2R), 0.0, 1.0))
    bright = stars(45.0, 0.055, 0.065, 0.15, STAR_GATES['medium']['after_keep'], (2.3, 5.1, 1.7))
    bright = t.scale_rgb(bright, t.maprange(z, math.sin(35 * D2R), math.sin(52 * D2R), 0.0, 1.0))
    flares = t.scale_rgb(stars(6.0, 0.02, 0.18, 0.30, STAR_GATES['large_flares']['after_keep'], (7.7, 3.3, 9.9), flare=0.045),
                         t.maprange(z, math.sin(55 * D2R), math.sin(67 * D2R), 0.0, 1.0))
    st = t.vmath('ADD', t.vmath('ADD', faint, bright), flares)
    total = t.vmath('ADD', t.vmath('ADD', grad, neb), st)
    bg = t.node('ShaderNodeBackground')
    plug(bg.inputs['Color'], total)
    plug(bg.inputs['Strength'], 1.0)
    t.out(surface=bg.outputs[0], world=True)
    return w


# ---------------------------------------------------------------- the city
def feature_record(acc, start, identity, visible=True):
    first_v, first_f = start
    points = acc.v[first_v:]
    samples = [(math.degrees(math.atan2(x, y)),
                math.degrees(math.atan2(z-CAM_H, max(1e-8, math.hypot(x, y)))))
               for x, y, z in points[::max(1, len(points)//80)]]
    return dict(id=identity, first=first_f, last=len(acc.f), samples=samples or [(0, 0)], visible=visible)


def prune_features(acc, kind, features, report):
    keep = select_secondary(kind, [f for f in features if f['visible']])
    remove = {i for f in features if f['id'] not in keep for i in range(f['first'], f['last'])}
    indices = [i for i in range(len(acc.f)) if i not in remove]
    faces = [acc.f[i] for i in indices]
    used = sorted({v for face in faces for v in face})
    remap = {old: new for new, old in enumerate(used)}
    acc.f = [tuple(remap[v] for v in face) for face in faces]
    acc.mi = [acc.mi[i] for i in indices]
    for attr in ('v', 'uv', 'col'):
        setattr(acc, attr, [getattr(acc, attr)[v] for v in used])
    report[kind] = dict(before=len(features), after=len(keep), kept_ids=sorted(keep),
                       hidden_host_ids=sorted(f['id'] for f in features if not f['visible']))


class City:
    def __init__(self):
        self.fac = Acc('city_facades')
        self.roof = Acc('city_roofs')
        self.struct = Acc('city_struct')
        self.neon = Acc('city_neon')
        self.screen = Acc('city_screens')
        self.trail = Acc('city_trails')
        self.holo = Acc('city_holo')                                  # v2: holographic panels (unused since v4)
        self.sigil = Acc('city_sigils')                               # v4: glowing emblems on the towers
        self.fall = Acc('city_falls')                                 # v4: light-falls
        self.ribbon = Acc('city_ribbons')                             # v4: glowing highway / rail decks
        self.crystal = Acc('city_crystal')                            # v6b: the spires' giant lit crystal slabs
        self.cyber = Acc('city_cyber_armour')
        self.cyber_roof = Acc('city_cyber_decks')
        self.cyber_counts = {}
        self.tall = []          # (x, y, h) of tall mid-band buildings: searchlight / holo candidates
        self.mega_tops = []     # v2: (x, y, h) of the supertalls: searchlights, beams, lasers
        self.excl = []          # v2: (x, y, radius) the ordinary lots must stay out of (the supertalls' footprints)
        self.n_bld = 0
        self.kept_lots = None
        self.station_keepout = None
        self.removed_hosts = set()
        self.composition = {'buildings': [], 'megatowers': [], 'secondary': {}}

    def mark_geometry(self):
        return [(acc, {key: len(getattr(acc, key)) for key in ('v', 'f', 'uv', 'col', 'mi')})
                for acc in vars(self).values() if isinstance(acc, Acc)]

    def rewind_geometry(self, marks):
        for acc, fields in marks:
            for key, length in fields.items():
                del getattr(acc, key)[length:]

    def host_visible(self, x, y, h):
        return (x, y, h) not in self.removed_hosts

    def excluded(self, x, y):
        for ex, ey, er in self.excl:
            if math.hypot(x - ex, y - ey) < er:
                return True
        return False

    # ---- layout
    def layout(self):
        seeds = [(0.0, 0.0, 0.0)]
        for _ in range(11):
            r, a = rng.uniform(2500, R_CITY * 0.92), rng.uniform(-180, 180)
            seeds.append((*polar(r, a), rng.uniform(0, math.pi / 2)))
        sx = np.array([s[0] for s in seeds])
        sy = np.array([s[1] for s in seeds])
        self.dist_mult = [1.0] + [rng.choice([0.45, 0.6, 0.8, 1.0, 1.0, 1.25, 1.6]) for _ in seeds[1:]]
        log('district height multipliers: ' + ' '.join(f'{m:.2f}' for m in self.dist_mult))
        lots, streets = [], []
        # ---- v5 THE CORE: polar lots on the rings between the ring roads (podium()), cut by the radial boulevards — low at
        #      the foot, rising outward, so the circular plan bleeds into the grid (user: "not an even bleed ... looks odd")
        n_core = 0
        gap = CORE_RADIAL_W / 2 + 6.0                                             # v5b: the lots' sector grid is a multiple of the boulevards' — a boulevard is always a lot boundary
        for (r0, r1, hmed) in CORE_BANDS:
            depth, rm = r1 - r0, (r0 + r1) / 2
            mper = max(1, int(math.ceil(2 * math.pi * rm / (depth * 1.15) / CORE_RADIALS)))
            n = CORE_RADIALS * mper
            for i in range(n):
                lo, hi = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
                if i % mper == 0:
                    lo += gap / rm
                if (i + 1) % mper == 0:
                    hi -= gap / rm
                if rng.random() < 0.07:
                    continue                                                      # a few empty lots: plazas
                th = (lo + hi) / 2
                arc = (hi - lo) * rm
                cx, cy = rm * math.cos(th), rm * math.sin(th)
                lots.append(dict(cx=cx, cy=cy, P=depth, ang=th + math.pi / 2, r=rm, az=az_of(cx, cy), band=0, dist=0, core=True,
                                 w=arc - 8.0, d=depth - 12.0, hmed=hmed))
                n_core += 1
        # ---- the square districts beyond the core (v5: pitch LOT_P — a fifth of v4's lots at three times the size)
        bands = [(R_CORE, 7000.0, LOT_P[0], 0), (7000.0, 14000.0, LOT_P[1], 1), (14000.0, R_CITY, LOT_P[2], 2)]
        if not on('far'):
            bands = bands[:1]
        for r0, r1, P, band in bands:
            for k, (ox, oy, ang) in enumerate(seeds):
                n = int(math.ceil(r1 / P)) + 2
                i = np.arange(-n, n + 1) * P + P * 0.5
                gx, gy = np.meshgrid(i, i)
                gx, gy = gx.ravel(), gy.ravel()
                c, s = math.cos(ang), math.sin(ang)
                wx = ox + gx * c - gy * s
                wy = oy + gx * s + gy * c
                r = np.hypot(wx, wy)
                m = (r - (P * 0.71 if band == 0 else 0.0) >= r0) & (r < r1)      # v5: the whole lot outside the core's last ring road
                wx, wy, gx, gy, r = wx[m], wy[m], gx[m], gy[m], r[m]
                if not len(wx):
                    continue
                d2 = (wx[:, None] - sx[None, :]) ** 2 + (wy[:, None] - sy[None, :]) ** 2
                m = d2.argmin(1) == k
                wx, wy, gx, gy, r = wx[m], wy[m], gx[m], gy[m], r[m]
                az = np.degrees(np.arctan2(wx, wy))
                land = ~((az > BAY[0]) & (az < BAY[1]) & (r > BAY_R[0]) & (r < BAY_R[1]))
                if not on('water'):
                    land[:] = True
                ringblock = np.zeros_like(land)
                if on('highways'):
                    for rr, _, ww in RINGS:
                        ringblock |= np.abs(r - rr) < (ww / 2 + P * 0.55)
                # built probability: the city thins outward and clumps around its downtowns
                p = np.where(r < 2500, 0.82, np.where(r < 7000, 0.70, np.where(r < 14000, 0.50, 0.30)))
                dens = np.ones_like(r)
                for dr, da, rad, _ in DOWNTOWN:
                    dx, dy = polar(dr, da)
                    dens += 0.5 * np.exp(-((wx - dx) ** 2 + (wy - dy) ** 2) / (2 * rad ** 2))
                p = np.clip(p * dens * (0.75 + 0.5 * nprng.random(len(r))), 0, 1) * DETAIL
                built = land & ~ringblock & (nprng.random(len(r)) < p)
                for j in np.nonzero(built)[0]:
                    lots.append(dict(cx=float(wx[j]), cy=float(wy[j]), P=P, ang=ang, r=float(r[j]), az=float(az[j]), band=band, dist=k))
                if band == 0 and on('streets'):
                    for j in np.nonzero(land & (r < 8000.0))[0]:
                        streets.append((float(gx[j]), float(gy[j]), ox, oy, ang, P, float(r[j]), k))
        log(f'layout: {len(lots)} lots ({n_core} on the core rings), {len(streets)} street cells, {len(seeds)} districts')
        return lots, streets

    def boost(self, x, y):
        b = 1.0
        for dr, da, rad, k in DOWNTOWN:
            dx, dy = polar(dr, da)
            b += (k - 1.0) * math.exp(-((x - dx) ** 2 + (y - dy) ** 2) / (2 * rad ** 2))
        return b

    def lane_cap(self, x, y, h):
        az = az_of(x, y)
        if abs(az) < LANE_HALF:
            d = math.hypot(x, y)
            el = LANE_EL_NEAR if d < SIGN_D * 1.4 else LANE_EL       # in front of the sign nothing may cross its plate
            return min(h, max(12.0, CAM_H + d * math.tan(el * D2R) - 5.0))
        return h

    # ---- one building
    def building(self, lot):
        # Spend exactly the legacy random draws before replacing ordinary blocks
        # and nearer small spires. Tall landmarks and later sky RNG stay put.
        marks = self.mark_geometry()
        tall_start, count_start = len(self.tall), self.n_bld
        self._cyber_params = None
        self._legacy_building(lot)
        keep = self.kept_lots is None or lot_key(lot) in self.kept_lots
        reason = 'retained' if keep else 'depth_reduction'
        if station_conflict(self._building_info, self.station_keepout, CAM_H):
            keep, reason = False, 'station_clearance'
        if on('sign') and SIGN_STYLE in ('ominous', 'cyber_hero') and title_conflict(self._building_info, CAM_H, GATE):
            keep, reason = False, 'title_clearance'
        self.composition['buildings'].append(dict(self._building_info,
            band=distance_band(lot['r']), kept=keep, reason=reason))
        if not keep:
            self.rewind_geometry(marks)
            self.removed_hosts.update(self.tall[tall_start:])
            self.n_bld = count_start
            return
        if self._cyber_params is not None:
            self.rewind_geometry(marks)
            result = build_cyber_block(self, **self._cyber_params)
            style = result['archetype_name']
            self.cyber_counts[style] = self.cyber_counts.get(style, 0) + 1
            self.composition['buildings'][-1]['architecture'] = style
            if self._building_info['spire']:
                # Keep selection/RNG history, retire attachments to the replaced
                # old crowns; a new split crown need not share their mount point.
                self.removed_hosts.update(self.tall[tall_start:])
        else:
            self.composition['buildings'][-1]['architecture'] = 'preserved_spire'

    def _legacy_building(self, lot):
        P, r, band, ang = lot['P'], lot['r'], lot['band'], lot['ang']
        core = lot.get('core', False)
        if core:                                                                   # v5 THE CORE: polar lots, the height from the ring's median
            site_w, site_d = lot['w'], lot['d']
            h = lognorm(lot['hmed'], 0.42)
            if lot['hmed'] > 120 and rng.random() < 0.08:
                h *= rng.uniform(1.5, 2.2)
        else:
            street = P * 0.16                                                      # v5: ~51 m streets between 320 m lots
            site_w = site_d = P - street
            if band == 0:                                                          # v5: fewer, three times bigger (user: "too many buildings ... so small")
                h = lognorm(200, 0.5) if r < 2500 else lognorm(230, 0.62)
            elif band == 1:
                h = lognorm(340, 0.62)
            else:
                h = lognorm(560, 0.6)
            h *= self.boost(lot['cx'], lot['cy']) * self.dist_mult[lot.get('dist', 0)]
            if rng.random() < 0.09:
                h *= rng.uniform(1.5, 2.6)
        h = min(h, 2100.0)
        h = self.lane_cap(lot['cx'], lot['cy'], h)
        h = min(h, ship_cap(lot['cx'], lot['cy']))                               # v5b: never in front of a battlecruiser
        h = max(h, 14.0)
        big = h > 300
        w = site_w * rng.uniform(0.50 if big else 0.62, 0.82 if big else 0.95)
        d = site_d * rng.uniform(0.50 if big else 0.62, 0.82 if big else 0.95)
        ox, oy = rng.uniform(-(site_w - w) / 2, (site_w - w) / 2), rng.uniform(-(site_d - d) / 2, (site_d - d) / 2)
        ox, oy = rot(ox, oy, ang)
        cx, cy = lot['cx'] + ox, lot['cy'] + oy
        kind = rng.random()
        spire = (h >= 90 and rng.random() < 0.85) or (60 <= h < 90 and rng.random() < 0.40)   # v6b THE SPIRE CLUSTER (the references): nearly every tower
        far = band == 2 or r > 11000
        if kind < 0.50:
            fp = fp_rect(cx, cy, w, d, ang)
        elif kind < 0.74:
            fp = fp_chamfer(cx, cy, w, d, min(w, d) * rng.uniform(0.12, 0.3), ang)
        elif kind < 0.86 and min(w, d) > 60:
            fp = fp_L(cx, cy, w, d, w * rng.uniform(0.35, 0.55), d * rng.uniform(0.35, 0.55), ang)
        else:
            n = 12 if r > 9000 else (18 if r > 3000 else 24)
            fp = fp_ellipse(cx, cy, w / 2, d / 2 * rng.uniform(0.75, 1.0), n, ang)
        seed = rng.random()
        style = rng.random()
        if h < 60:
            style = PANEL_FRAC + (1.0 - PANEL_FRAC) * rng.random()               # v5b: the low blocks are dark window boxes, never a coloured crate
        pal = pal_roll()                                                          # the tint ramp in mat_facade / body_ramp
        litfrac = max(0.05, min(0.36, rng.gauss(0.169, 0.065)))                     # v6: -35 % (user: "cut the windows by 35 % but keep the consistency and detail"); v5c 0.26, v5 0.34, v4 0.46
        if rng.random() < 0.04:
            litfrac = rng.uniform(0.02, 0.06)                                     # a few dead towers for depth
        if r > 7000:
            litfrac *= 0.7
        if spire:
            style = 2.0 + rng.random()                                            # v6b: mat_facade's spire branch (light rows + grooves, few windows)
        col = (seed, style, pal, litfrac)
        self._cyber_params = (dict(cx=cx, cy=cy, w=w, d=d, h=h,
            ang=ang, seed=seed, pal=pal, distance=r, far=far, neon=on('neon'), source_spire=spire)
            if modernize_lot(spire, h, r) else None)
        self._building_info = dict(cx=cx, cy=cy, w=w, d=d, h=h, spire=spire,
                                   distance=r, seed=seed)
        bc = body_col(pal)
        a = amin(r)
        tiers = []
        if spire:
            # ---- v6b THE SPIRE CLUSTER: a tapered CORE of frustum segments ending in a NEEDLE, satellite spires clustered round it, CRYSTAL
            #      slabs standing on its faces, neon SEAMS up its edges following the taper, a COLLAR at every break (the references' towers)
            nside = rng.choice([6, 8, 8, 10, 12]) if kind < 0.86 else 16
            rc = min(w, d) * 0.5 * rng.uniform(0.28, 0.45)                           # v6e: SLIM - the references' spires are needles, not drums (v6b 0.55..0.78)
            core_fp = fp_ellipse(cx, cy, rc, rc * rng.uniform(0.85, 1.0), nside, ang + rng.uniform(0, math.pi / nside))
            nseg = 2 if far else rng.choice([3, 3, 4, 4, 5])
            needle_f = rng.uniform(0.12, 0.26)
            shoulder = h * (1.0 - needle_f)
            fr = sorted(rng.uniform(0.18, 0.95) for _ in range(nseg - 1)) + [1.0]
            z = 0.0
            cur = core_fp
            ew = max(0.6, a * 0.9)
            seam_step = 2 if nside <= 8 else 3                                          # v6c: a few seams, not a cage (v6b lit every edge)
            for i, f in enumerate(fr):
                z1 = shoulder * f
                nxt = fp_scale(cur, rng.uniform(0.80, 0.94))
                self.fac.loft(cur, z, nxt, z1, col, cap=(i == nseg - 1), cap_acc=self.roof, cap_col=col)
                tiers.append((cur, z, z1))
                if on('neon') and not far:
                    for k in range(0, nside, seam_step):                                        # the light SEAMS follow the taper
                        tube(self.neon, (*cur[k], z), (*nxt[k], z1), ew, ew, (*bc, 0.50), 4)
                    self.neon.prism(fp_scale(nxt, 1.03), z1 - ew * 0.9, z1 + ew * 0.4, (*bc, 0.45), cap=False)   # the COLLAR
                cur = nxt
                z = z1
            top_fp, ztop0, ztop = cur, tiers[-1][1], shoulder
            tx_, ty_ = fp_center(top_fp)
            self.struct.loft(cur, shoulder, fp_scale(cur, 0.05), h, (0, 0, 0, 1), cap=True)     # the NEEDLE
            if not far:
                tube(self.neon, (tx_, ty_, shoulder + (h - shoulder) * 0.55), (tx_, ty_, h + 1.0), ew * 0.9, ew * 0.5, (*bc, 0.9), 4)   # its upper half lit
                self.neon.box(tx_, ty_, h + 1.0, a * 2.0, a * 2.0, a * 2.0, 0, (*(PAL['beacon'] if rng.random() < 0.5 else PAL['white']), 1.0))
            # the SATELLITES: shorter spires clustered against the core
            nsat = rng.choice([1, 2, 3]) if far else rng.choice([4, 5, 6, 7, 8])       # v6e: a dense BUNDLE (v6b 2..5)
            site_r = min(site_w, site_d) * 0.5 * 0.96
            for _ in range(nsat):
                phi = rng.uniform(0, 2 * math.pi)
                rs = rc * rng.uniform(0.35, 0.80)
                ds = min(rc * rng.uniform(1.0, 2.3), site_r - rs)
                if ds <= rs * 0.5:
                    continue
                sx, sy = cx + ds * math.cos(phi), cy + ds * math.sin(phi)
                hs = h * rng.uniform(0.30, 0.92)                                         # v6e: some nearly as tall as the core
                ns = 6 if rs < 12 else 8
                sfp = fp_ellipse(sx, sy, rs, rs * rng.uniform(0.85, 1.0), ns, phi)
                sh_z = hs * rng.uniform(0.78, 0.88)
                zm = sh_z * rng.uniform(0.4, 0.7)
                mid = fp_scale(sfp, rng.uniform(0.84, 0.94))
                top2 = fp_scale(mid, rng.uniform(0.80, 0.92))
                self.fac.loft(sfp, 0.0, mid, zm, col, cap=False)
                self.fac.loft(mid, zm, top2, sh_z, col, cap=True, cap_acc=self.roof, cap_col=col)
                self.struct.loft(top2, sh_z, fp_scale(top2, 0.06), hs, (0, 0, 0, 1), cap=True)
                if on('neon') and not far:
                    for j in range(0, ns, 3):                                                   # v6c: two or three seams a satellite
                        tube(self.neon, (*sfp[j], 0.0), (*mid[j], zm), ew * 0.8, ew * 0.8, (*bc, 0.42), 4)
                        tube(self.neon, (*mid[j], zm), (*top2[j], sh_z), ew * 0.8, ew * 0.8, (*bc, 0.42), 4)
                    self.neon.prism(fp_scale(top2, 1.04), sh_z - ew * 0.8, sh_z + ew * 0.4, (*bc, 0.45), cap=False)
                    if rng.random() < 0.6:
                        self.neon.box(sx, sy, hs + 0.5, a * 1.6, a * 1.6, a * 1.6, 0, (*PAL['beacon'], 0.8))
            # the CRYSTAL slabs (the references' giant lit panels) standing on the core's faces
            if not far and on('neon') and on('crystal') and h > 120:                   # --skip crystal isolates the slabs
                for _ in range(rng.choice([1, 1, 1, 2, 2, 3]) if h > 150 else rng.choice([0, 1, 1, 2])):   # v6c: nearly every tall spire wears one
                    ci = rng.randrange(nside)
                    (ax, ay), (bx, by) = core_fp[ci], core_fp[(ci + 1) % nside]
                    fx, fy = (ax + bx) / 2, (ay + by) / 2
                    ddx, ddy = fx - cx, fy - cy
                    Ld = math.hypot(ddx, ddy) or 1.0
                    ddx, ddy = ddx / Ld, ddy / Ld
                    cw = rc * rng.uniform(1.0, 2.0)                                               # v6e: wider than the slim core (the references' slabs dwarf their spires)
                    ct = max(1.5, cw * 0.08)
                    z0c = h * rng.uniform(0.06, 0.35)
                    z1c = min(z0c + h * rng.uniform(0.35, 0.70), h * 0.98)
                    off = 0.8 + ct * 0.5                                                          # the face leans in with the taper
                    cfp = fp_rect(fx + ddx * off, fy + ddy * off, cw, ct, math.atan2(by - ay, bx - ax))
                    self.crystal.loft(cfp, z0c, fp_scale(cfp, rng.uniform(0.80, 0.95)), z1c, (*bc, rng.uniform(0.8, 1.1)), cap=True)
            # a halo ring round the core (the references' ringed spires); greebles on the lower body
            if not far and on('ringsx') and h > 300 and rng.random() < 0.32:
                self.ring_at(tx_, ty_, h * rng.uniform(0.45, 0.85), rc * rng.uniform(1.8, 2.8), bc, max(0.8, a * 1.1), rng.uniform(-0.1, 0.1), 0.9)
            if not far and r < 6000:
                for _ in range(rng.randint(2, 6)):
                    gi = rng.randrange(nside)
                    (ax, ay), (bx, by) = core_fp[gi], core_fp[(gi + 1) % nside]
                    tt = rng.uniform(0.2, 0.8)
                    gx, gy = ax + (bx - ax) * tt, ay + (by - ay) * tt
                    gdx, gdy = gx - cx, gy - cy
                    Lg = math.hypot(gdx, gdy) or 1.0
                    gdx, gdy = gdx / Lg, gdy / Lg
                    gang = math.atan2(by - ay, bx - ax)
                    gw_, gd_, gh_ = rng.uniform(3, 9) * (1 + r / 6000), rng.uniform(2, 5) * (1 + r / 6000), rng.uniform(2, 8)
                    zg = h * rng.uniform(0.05, 0.6)
                    self.struct.box(gx + gdx * gd_ * 0.4, gy + gdy * gd_ * 0.4, zg, gw_, gd_, gh_, gang, (0, 0, 0, 1))
                    if rng.random() < 0.5:
                        self.neon.box(gx + gdx * gd_ * 0.9, gy + gdy * gd_ * 0.9, zg + gh_ * 0.5, gw_ * 0.7, max(0.5, a * 0.6), max(0.5, a * 0.6), gang, (*bc, 0.6))
            w = d = rc * 2
        else:
            # ---- the box tiers (v5): the low blocks and a few mid-rise slabs - the references' foreground has them too
            if h < 60 or band == 2:
                ntier = 1
            elif h < 200:
                ntier = rng.choice([1, 1, 2, 2, 3])
            elif h < 600:
                ntier = rng.choice([2, 2, 3, 3, 4])
            else:
                ntier = rng.choice([3, 4, 4, 5, 5, 6])
            z = 0.0
            cur = fp
            fracs = sorted(rng.uniform(0.30, 0.95) for _ in range(ntier - 1)) + [1.0]
            for i, f in enumerate(fracs):
                z1 = h * f
                self.fac.prism(cur, z, z1, col, cap=True, cap_acc=self.roof, cap_col=col)
                tiers.append((cur, z, z1))
                if i < ntier - 1:
                    s = rng.uniform(0.6, 0.88)
                    ex, ey = (1 - s) * w / 2 * 0.85, (1 - s) * d / 2 * 0.85
                    ox2, oy2 = rot(rng.uniform(-ex, ex), rng.uniform(-ey, ey), ang) if kind < 0.86 else (0.0, 0.0)
                    cur = fp_scale(cur, s, ox2, oy2)
                    w, d = w * s, d * s
                z = z1
            top_fp, ztop0, ztop = tiers[-1]
        self.n_bld += 1
        if band == 0 and h > 300 and 1500 < r < 7000:
            tx, ty = fp_center(top_fp)
            self.tall.append((tx, ty, h))
        if band == 2 or r > 11000:
            return
        # ---- details (v5: a fifth of the towers at three times the size — so three times the detail on each)
        a = amin(r)
        tx_, ty_ = fp_center(top_fp)
        R_fp = max(math.hypot(px - tx_, py - ty_) for px, py in top_fp)
        bc = body_col(pal)
        base_fp = tiers[0][0]
        if on('neon') and style < PANEL_FRAC and r < 12000:                      # a PANEL tower: its edges lit full height in its hue, every tier collared
            ew = a * 1.0
            for (tfp, tz0, tz1) in tiers:
                step = 1 if len(tfp) <= 8 else max(1, len(tfp) // 6)
                for (px, py) in tfp[::step]:
                    self.neon.prism(fp_rect(px, py, ew, ew, ang), tz0 + 0.5, tz1 - 0.5, (*bc, 0.7))
                for i in range(len(tfp)):
                    (ax, ay), (bx, by) = tfp[i], tfp[(i + 1) % len(tfp)]
                    self.neon.strip(ax, ay, bx, by, tz1 - ew * 0.5, ew, ew, (*bc, 0.8))
            if h > 200:                                                          # v5: lit BELTS at one to three heights (the references' banded towers)
                for _ in range(rng.randint(1, 3)):
                    zb = rng.uniform(0.15, 0.85) * h
                    tfp = next((f_ for f_, z0_, z1_ in tiers if z0_ <= zb <= z1_), top_fp)
                    for i in range(len(tfp)):
                        (ax, ay), (bx, by) = tfp[i], tfp[(i + 1) % len(tfp)]
                        self.neon.strip(ax, ay, bx, by, zb, ew * 1.3, ew * 1.6, (*bc, 0.9))
            if on('ringsx') and h > 400 and 1200 < r < 9000 and rng.random() < 0.22:   # a neon ring round the crown
                self.ring_at(tx_, ty_, ztop + h * 0.02, R_fp * rng.uniform(1.4, 2.0), bc, max(0.8, a * 1.1), rng.uniform(-0.12, 0.12), 0.9)
            if h > 350 and rng.random() < 0.30:                                    # a spiked crown
                self.spikes_at(tx_, ty_, ztop, h, bc, rng.randint(4, 8), R_fp * 0.5)
            if on('sigils') and h > 250 and rng.random() < 0.22:                 # v5: an emblem on the face toward the tower
                tfp, tz0, tz1 = tiers[rng.randint(0, len(tiers) - 1)]
                self.sigil_on(tfp, tz0, tz1, pal, 0.55, rng.uniform(0.4, 0.75))
            if h > 500 and rng.random() < 0.28:                                  # v5: buttress FINS from the foot, a lit edge each
                nb = len(base_fp)
                for i in rng.sample(range(nb), min(nb, rng.choice([2, 3, 4]))):
                    px, py = base_fp[i]
                    dx_, dy_ = px - tx_, py - ty_
                    L_ = math.hypot(dx_, dy_) or 1.0
                    dx_, dy_ = dx_ / L_, dy_ / L_
                    fl, fh = min(site_w, site_d) * rng.uniform(0.12, 0.25), h * rng.uniform(0.2, 0.4)
                    fin = [(px + dy_ * 3, py - dx_ * 3), (px + dx_ * fl + dy_ * 3, py + dy_ * fl - dx_ * 3),
                           (px + dx_ * fl - dy_ * 3, py + dy_ * fl + dx_ * 3), (px - dy_ * 3, py + dx_ * 3)]
                    self.struct.prism(fin, 0.0, fh, (0, 0, 0, 1), cap=True)
                    tube(self.neon, (px + dx_ * fl, py + dy_ * fl, fh), (px, py, fh + fl * 0.8), max(0.8, a * 0.9), max(0.8, a * 0.9), (*bc, 0.8), 5)
        if on('neon'):
            if not spire and rng.random() < (0.18 if r < 4500 else 0.10):        # a lit parapet edge, or the whole outline (a spire has its collar)
                nc = PAL[wchoice(NEON_W)]
                n = len(top_fp)
                edges = list(range(n)) if rng.random() < 0.35 else rng.sample(range(n), min(n, rng.choice([1, 2, 2])))
                for i in edges:
                    ax, ay = top_fp[i]
                    bx, by = top_fp[(i + 1) % n]
                    self.neon.strip(ax, ay, bx, by, ztop - a * 0.3, a * 1.1, a * 1.1, (*nc, rng.uniform(0.3, 0.7)))
            if not spire and rng.random() < 0.10 and h > 120:                    # vertical corner tubes on the top tier
                nc = PAL[wchoice(NEON_W)]
                for (px, py) in top_fp[:: max(1, len(top_fp) // 4)]:
                    self.neon.prism(fp_rect(px, py, a * 1.2, a * 1.2, ang), ztop0 + 2, ztop - 1, (*nc, 0.8))
            if not spire and rng.random() < 0.08 and h > 220 and len(tiers) > 1:   # collars: the lower tiers' top edges lit (a spire's are geometry)
                nc = PAL[wchoice(NEON_W)]
                for (tfp, tz0, tz1) in tiers[:-1]:
                    for i in range(len(tfp)):
                        ax, ay = tfp[i]
                        bx, by = tfp[(i + 1) % len(tfp)]
                        self.neon.strip(ax, ay, bx, by, tz1 - a * 0.6, a * 1.1, a * 1.1, (*nc, 0.5))
            if not spire and rng.random() < 0.14 and h > 180 and kind < 0.86 and r < 9000:   # a pyramid crown (silhouette variety)
                apex = (tx_, ty_, ztop + h * rng.uniform(0.08, 0.16))
                nc = PAL[wchoice(NEON_W)]
                lit_edges = rng.random() < 0.5
                for i in range(len(top_fp)):
                    (ax, ay), (bx, by) = top_fp[i], top_fp[(i + 1) % len(top_fp)]
                    self.struct.poly([(ax, ay, ztop), (bx, by, ztop), apex], [(0, 0), (1, 0), (0.5, 1)], (0, 0, 0, 1))
                    if lit_edges:
                        tube(self.neon, (ax, ay, ztop), apex, a * 0.6, a * 0.6, (*nc, 0.6), 4)
            if spire and on('sigils') and h > 250 and r < 9000 and rng.random() < 0.30:   # v6b: an emblem on a spire's face
                tfp, tz0, tz1 = tiers[rng.randint(0, len(tiers) - 1)]
                self.sigil_on(tfp, tz0, tz1, pal, 0.5, rng.uniform(0.35, 0.7))
            if not spire and h > 300 and rng.random() < 0.14:                    # v5: an antenna ARRAY on the crown
                for _ in range(rng.randint(3, 6)):
                    ox5, oy5 = rot(rng.uniform(-w * 0.3, w * 0.3), rng.uniform(-d * 0.3, d * 0.3), ang)
                    mh = h * rng.uniform(0.05, 0.16)
                    self.struct.prism(fp_ellipse(tx_ + ox5, ty_ + oy5, max(1.1, a * 0.7), max(1.1, a * 0.7), 6, 0), ztop, ztop + mh, (0, 0, 0, 1))
                    self.neon.box(tx_ + ox5, ty_ + oy5, ztop + mh, a * 2.0, a * 2.0, a * 2.0, 0, (*(PAL['beacon'] if rng.random() < 0.6 else PAL['white']), 0.9))
            elif not spire and rng.random() < (0.45 if h > 200 else 0.14):         # antenna mast + red beacon (a spire has its needle)
                mh = h * rng.uniform(0.07, 0.2)
                self.struct.prism(fp_ellipse(tx_, ty_, max(1.1, a * 0.7), max(1.1, a * 0.7), 6, 0), ztop, ztop + mh, (0, 0, 0, 1))
                if rng.random() < 0.85:
                    bsz = a * 2.2
                    self.neon.box(tx_, ty_, ztop + mh, bsz, bsz, bsz, 0, (*PAL['beacon'], 1.0))
            if h > 300 and not core and rng.random() < 0.45:                     # v5: a lit PLINTH — the foot steps out (a lobby) and glows along its edge
                pf = fp_scale(base_fp, rng.uniform(1.12, 1.3))
                zp = rng.uniform(9.0, 16.0)
                pcol = (seed, 0.99, pal, 0.6)
                self.fac.prism(pf, 0.0, zp, pcol, cap=True, cap_acc=self.roof, cap_col=pcol)
                nc = PAL[wchoice(NEON_W)]
                for i in range(len(pf)):
                    (ax, ay), (bx, by) = pf[i], pf[(i + 1) % len(pf)]
                    self.neon.strip(ax, ay, bx, by, zp - a * 0.5, a * 1.1, a * 1.1, (*nc, 0.6))
        if on('screens') and h > 100 and r < 8500 and rng.random() < (0.30 if 1200 < r < 6000 else 0.15):
            # a giant ad screen on the facade that faces the tower (v5: a second one lower on the tall towers)
            spots = [tiers[-1] if (ztop - ztop0) > 40 else tiers[0]]
            if h > 500 and len(tiers) > 1 and rng.random() < 0.5:
                spots.append(tiers[0])
            for (tfp, tz0, tz1) in spots:
                i = fp_facing_edge(tfp)
                ax, ay = tfp[i]
                bx, by = tfp[(i + 1) % len(tfp)]
                L = math.hypot(bx - ax, by - ay)
                if L > 14:
                    sw = L * rng.uniform(0.6, 0.85)
                    th = tz1 - tz0
                    sh = min(th * rng.uniform(0.28, 0.45), sw * rng.uniform(0.55, 1.1))
                    zc = tz0 + th * rng.uniform(0.45, 0.78)
                    if zc + sh / 2 > tz1 - 2:
                        zc = tz1 - 2 - sh / 2
                    dx, dy = (bx - ax) / L, (by - ay) / L
                    nx, ny = dy, -dx                                                # outward normal (CCW footprint)
                    mx, my = (ax + bx) / 2 + nx * 0.6, (ay + by) / 2 + ny * 0.6
                    hw, hh = sw / 2, sh / 2
                    pts = [(mx - dx * hw, my - dy * hw, zc - hh), (mx + dx * hw, my + dy * hw, zc - hh),
                           (mx + dx * hw, my + dy * hw, zc + hh), (mx - dx * hw, my - dy * hw, zc + hh)]
                    self.screen.poly(pts, [(0, 0), (sw, 0), (sw, sh), (0, sh)], (rng.random(), sw, sh, rng.uniform(0.55, 1.35)), mi=screen_mi(sw, sh))
        if not spire and r < 3200:                                               # rooftop service lights
            for _ in range(rng.randint(1, 3)):
                ox4, oy4 = rot(rng.uniform(-w * 0.35, w * 0.35), rng.uniform(-d * 0.35, d * 0.35), ang)
                lc = PAL['tail'] if rng.random() < 0.45 else PAL['warm']
                self.neon.box(tx_ + ox4, ty_ + oy4, ztop, a * 1.4, a * 1.4, a * 1.4, 0, (*lc, 0.18))
        if not spire and r < 4500 and ztop - ztop0 > 12:                         # rooftop plant (v5: sized to the roof)
            for _ in range(rng.randint(1, 4)):
                bw, bd, bh = w * rng.uniform(0.06, 0.16), d * rng.uniform(0.06, 0.16), rng.uniform(3, 9)
                ox3, oy3 = rot(rng.uniform(-w * 0.28, w * 0.28), rng.uniform(-d * 0.28, d * 0.28), ang)
                self.struct.box(tx_ + ox3, ty_ + oy3, ztop, bw, bd, bh, ang, (0, 0, 0, 1))

    def streets(self, cells):
        for gx, gy, ox, oy, ang, P, r, dist in cells:
            c, s = math.cos(ang), math.sin(ang)
            a = amin(r, 1.5)
            fade = 1.0 if r < 2200 else max(0.45, 1.0 - (r - 2200) / 9000)
            road = ROAD_HUES[dist % len(ROAD_HUES)]                                 # v2: each district lights its streets in its own hue
            for vert in (True, False):
                if vert:
                    p0 = (gx - P / 2, gy - P / 2)
                    p1 = (gx - P / 2, gy + P / 2)
                else:
                    p0 = (gx - P / 2, gy - P / 2)
                    p1 = (gx + P / 2, gy - P / 2)
                lx, ly = p1[0] - p0[0], p1[1] - p0[1]
                L = math.hypot(lx, ly)
                lx, ly = lx / L, ly / L
                nx, ny = -ly, lx
                mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
                for off, colk, alpha in ((5.0, 'tail', 0.9), (-5.0, 'head', 1.0)):   # v5: the streets are 51 m wide now — the lanes sit further apart
                    if rng.random() < 0.85:
                        px, py = mx + nx * off, my + ny * off
                        wx, wy = ox + px * c - py * s, oy + px * s + py * c
                        wdx, wdy = lx * c - ly * s, lx * s + ly * c
                        self.trail.quad_dir(wx, wy, 0.7, wdx, wdy, a, L * rng.uniform(0.55, 1.0), (*PAL[colk], alpha * fade))
                if rng.random() < 0.9:                                              # the lit road surface itself
                    wx, wy = ox + mx * c - my * s, oy + mx * s + my * c
                    wdx, wdy = lx * c - ly * s, lx * s + ly * c
                    self.trail.quad_dir(wx, wy, 0.25, wdx, wdy, 30.0, L, (*PAL[road], E_ROAD / E_TRAIL * 0.6 * fade * rng.uniform(0.6, 1.3)))
                    self.trail.quad_dir(wx, wy, 0.35, wdx, wdy, a * 1.4, L * 1.02, (*PAL[road], 0.9 * fade))     # v3: the grid line itself
                if r < 3800:
                    for off in (13.0, -13.0):
                        px, py = mx + nx * off, my + ny * off
                        wx, wy = ox + px * c - py * s, oy + px * s + py * c
                        wdx, wdy = lx * c - ly * s, lx * s + ly * c
                        self.trail.quad_dir(wx, wy, 8.0, wdx, wdy, a * 0.9, L, (*PAL[road], 0.3 * fade))

    def podium(self):
        """v5 THE CORE (user: the ground floor's circle "leads into the background but it's not an even bleed ... looks odd"):
        the ring roads continue outward to the last ring at R_CORE with twelve radial boulevards between them, at the streets'
        own brightness, so the circular plan BECOMES the city instead of ending at a wall (the lots on the rings are laid in
        layout()); the canal ring stays between the third and fourth ring roads"""
        for ri, (R_, w_, br) in enumerate(CORE_ROADS):
            rhue = PAL[CORE_ROAD_HUES[ri % len(CORE_ROAD_HUES)]]                    # v6
            N = max(48, int(R_ / 9))
            for i in range(N):
                t0, t1 = 2 * math.pi * i / N, 2 * math.pi * (i + 1) / N
                tm = (t0 + t1) / 2
                cx, cy = R_ * math.cos(tm), R_ * math.sin(tm)
                dx, dy = -math.sin(tm), math.cos(tm)
                L = R_ * (t1 - t0)
                a = amin(R_, 1.5)
                self.trail.quad_dir(cx, cy, 0.25, dx, dy, w_, L * 1.02, (*rhue, E_ROAD / E_TRAIL * 0.6 * br))
                self.trail.quad_dir(cx, cy, 0.35, dx, dy, a * 1.4, L * 1.02, (*PAL['gold'], 0.6 * br))          # the grid line itself
                for off, colk in ((w_ * 0.25, 'tail'), (-w_ * 0.25, 'head')):
                    if rng.random() < 0.8:
                        rr = R_ + off
                        self.trail.quad_dir(rr * math.cos(tm), rr * math.sin(tm), 0.7, dx, dy, a, L * rng.uniform(0.5, 1.0), (*PAL[colk], 0.9 * br))
                if R_ < 1200:
                    for off in (w_ / 2 + 1.5, -w_ / 2 - 1.5):
                        rr = R_ + off
                        self.trail.quad_dir(rr * math.cos(tm), rr * math.sin(tm), 3.5, dx, dy, 1.4, L, (*PAL['sodium'], 0.3 * br))
        Rmax = CORE_ROADS[-1][0]
        for phi in core_radials():                                                  # the radial boulevards, fading outward
            dx, dy = math.cos(phi), math.sin(phi)
            ra = 62.0
            while ra < Rmax:
                rb = min(Rmax, ra + 180.0)
                br = 1.3 - 0.8 * (ra / Rmax)
                cx, cy = dx * (ra + rb) / 2, dy * (ra + rb) / 2
                a = amin((ra + rb) / 2, 1.5)
                self.trail.quad_dir(cx, cy, 0.25, dx, dy, CORE_RADIAL_W, rb - ra, (*PAL['sodium'], E_ROAD / E_TRAIL * 0.6 * br))
                self.trail.quad_dir(cx, cy, 0.35, dx, dy, a * 1.4, (rb - ra) * 1.02, (*PAL['gold'], 0.9 * br))
                for off, colk in ((3.6, 'tail'), (-3.6, 'head')):
                    if rng.random() < 0.8:
                        self.trail.quad_dir(cx - dy * off, cy + dx * off, 0.7, dx, dy, a, (rb - ra) * rng.uniform(0.5, 0.95), (*PAL[colk], 0.9 * br))
                ra = rb
        # the canal ring: still water between the third and fourth ring roads
        acc = Acc('podium_canal')
        N = 96
        for i in range(N):
            t0, t1 = 2 * math.pi * i / N, 2 * math.pi * (i + 1) / N
            pp = [(300.0, t0), (348.0, t0), (348.0, t1), (300.0, t1)]
            acc.poly([(rr * math.cos(t), rr * math.sin(t), 0.3) for rr, t in pp], [(0, 0)] * 4, (0, 0, 0, 1))
        acc.build(mat_water())

    def rings(self):
        for R, zd, wd in RINGS:
            N = int(R / 40)
            a = amin(R, 1.5)
            for i in range(N):
                t0, t1 = 2 * math.pi * i / N, 2 * math.pi * (i + 1) / N
                for off_w, acc, col, h in ((0, self.struct, (0, 0, 0, 1), 2.4),):
                    pts = [(R - wd / 2, t0), (R + wd / 2, t0), (R + wd / 2, t1), (R - wd / 2, t1)]
                    xy = [(rr * math.cos(t), rr * math.sin(t)) for rr, t in pts]
                    self.struct.prism(xy, zd - h, zd, col, cap=True)
                rib = PAL['orange'] if R < 4000 else PAL['magenta']                 # v4: the deck GLOWS — the references' sweeping highway ribbons
                Lseg = R * (t1 - t0)
                self.ribbon.poly([(px, py, zd + 0.06) for px, py in xy], [(0, 0), (0, 1), (Lseg, 1), (Lseg, 0)], (*rib, 1.0))
                # barriers with a lit tube, four traffic trails
                for rr, colk, alpha, z, w in ((R - wd / 2 + 0.6, 'gold' if R < 4000 else 'pink', 0.5, zd, a), (R + wd / 2 - 0.6, 'gold' if R < 4000 else 'pink', 0.5, zd, a)):
                    x0, y0 = rr * math.cos(t0), rr * math.sin(t0)
                    x1, y1 = rr * math.cos(t1), rr * math.sin(t1)
                    self.neon.strip(x0, y0, x1, y1, z, w, w * 0.8, (*PAL[colk], alpha))
                for rr, colk, alpha in ((R - wd * 0.3, 'tail', 0.9), (R - wd * 0.12, 'head', 1.0), (R + wd * 0.12, 'tail', 0.9), (R + wd * 0.3, 'head', 1.0)):
                    if rng.random() < 0.8:
                        tm = (t0 + t1) / 2
                        cx, cy = rr * math.cos(tm), rr * math.sin(tm)
                        dx, dy = -math.sin(tm), math.cos(tm)
                        self.trail.quad_dir(cx, cy, zd + 0.5, dx, dy, a, R * (t1 - t0) * rng.uniform(0.5, 1.0), (*PAL[colk], alpha))
                if i % 3 == 0:                                                   # pylon
                    px, py = R * math.cos(t0), R * math.sin(t0)
                    self.struct.prism(fp_ellipse(px, py, 3.2, 3.2, 8, 0), 0.0, zd - 2.4, (0, 0, 0, 1))
                    self.struct.box(px, py, zd - 5.0, wd * 0.9, 4.0, 2.6, t0 + math.pi / 2, (0, 0, 0, 1))

    # ---- landmarks
    def landmarks(self):
        # THE NEEDLE: a 900 m supertall with lit vertical spines and a beacon crown
        x, y = polar(7200, 42)
        ang = rng.uniform(0, math.pi / 4)
        fp = fp_chamfer(x, y, 150, 150, 35, ang)
        z = 0.0
        for i, (f, s) in enumerate(((0.32, 0.8), (0.6, 0.72), (0.82, 0.62), (0.94, 0.45), (1.0, 0.25))):
            z1 = 900 * f
            self.fac.prism(fp, z, z1, (0.3, 0.2, 0.1, 0.42), cap=True, cap_acc=self.roof)
            if on('neon'):
                for (px, py) in fp[::2]:
                    self.neon.prism(fp_rect(px, py, 2.2, 2.2, ang), z + 3, z1 - 2, (*PAL['red'], 0.9))
            fp = fp_scale(fp, s)
            z = z1
        self.struct.prism(fp_ellipse(x, y, 4, 4, 8, 0), 900, 1010, (0, 0, 0, 1))
        self.neon.box(x, y, 1010, 6, 6, 6, 0, (*PAL['beacon'], 1.0))
        # THE ARCOLOGY: a stepped pyramid on the harbour shore, every terrace edge lit ember
        x, y = polar(8600, -92)
        ang = rng.uniform(0, math.pi / 4)
        base = 820.0
        fp = fp_rect(x, y, base, base, ang)
        z = 0.0
        for i in range(7):
            z1 = z + 88.0
            self.fac.prism(fp, z, z1, (0.61, 0.5, 0.55, 0.5), cap=True, cap_acc=self.roof)
            if on('neon'):
                for k in range(4):
                    ax, ay = fp[k]
                    bx, by = fp[(k + 1) % 4]
                    self.neon.strip(ax, ay, bx, by, z1 - 1.5, 2.4, 2.4, (*PAL['ember'], 0.8))
            fp = fp_scale(fp, 0.8)
            z = z1
        self.neon.prism(fp_scale(fp, 0.35), z, z + 70, (*PAL['ember'], 1.0))
        # THE TWIN GATES: two 700 m towers joined by three skybridges
        x, y = polar(11500, 158)
        ang = rng.uniform(0, math.pi / 3)
        for sgn in (-1, 1):
            ox, oy = rot(sgn * 210, 0, ang)
            fp = fp_chamfer(x + ox, y + oy, 190, 120, 30, ang)
            self.fac.prism(fp, 0, 700, (0.83, 0.15, 0.62, 0.38), cap=True, cap_acc=self.roof)
            if on('neon'):
                for k in range(len(fp)):
                    ax, ay = fp[k]
                    bx, by = fp[(k + 1) % len(fp)]
                    self.neon.strip(ax, ay, bx, by, 699, 3.0, 3.0, (*PAL['magenta'], 0.9))
        for zb in (280, 460, 640):
            self.struct.box(x, y, zb, 260, 40, 22, ang, (0, 0, 0, 1))
            if on('neon'):
                self.neon.box(x, y, zb + 22, 250, 3, 3, ang, (*PAL['cyan'], 0.7))

    def air_lanes(self):
        """v2: AIR LANES — arcs of dashed head/tail traffic hanging over the city (thin boxes, so they read from the side), never
        across the sign or the moon; plus loose aircraft"""
        features = []
        for i in range(10):
            start = (len(self.trail.v), len(self.trail.f))
            R = rng.uniform(1400, 6500)
            cx, cy = polar(rng.uniform(0, R * 0.9), rng.uniform(-180, 180))
            z = rng.uniform(320, 1000)
            a0, span = rng.uniform(0, 2 * math.pi), rng.uniform(1.2, 2.6)
            N = int(R * span / 60)
            colk = 'head' if i % 2 else 'tail'
            for j in range(N):
                t0, t1 = a0 + span * j / N, a0 + span * (j + 1) / N
                tm = (t0 + t1) / 2
                px, py = cx + R * math.cos(tm), cy + R * math.sin(tm)
                d = math.hypot(px, py)
                if d < 700 or (abs(az_of(px, py)) < LANE_HALF and z > CAM_H + d * math.tan(4.0 * D2R)):
                    continue
                a = amin(d, 1.6)
                (x0, y0), (x1, y1) = (cx + R * math.cos(t0), cy + R * math.sin(t0)), (cx + R * math.cos(t1), cy + R * math.sin(t1))
                self.trail.strip(x0, y0, x1, y1, z, a, a, (*PAL[colk], 0.7))
            features.append(feature_record(self.trail, start, i))
        prune_features(self.trail, 'air_lanes', features, self.composition['secondary'])
        for _ in range(int(30 * DETAIL) + 8):
            r, az = rng.uniform(900, 9000), rng.uniform(-180, 180)
            x, y = polar(r, az)
            z = rng.uniform(150, 650)
            a = amin(r, 1.6)
            head = rng.random() < 0.6
            if SHIPS:                                                        # v7b: the loose aircraft retired with the ships (the draws stay: the city after them does not move)
                self.neon.box(x, y, z, a * 1.1, a * 1.1, a * 1.1, 0, (*(PAL['head'] if head else PAL['tail']), 0.22))

    # ---- v2: SUPERTALLS (user: "there aren't these extremely high skyscrapers ... different kinds of buildings, different heights")
    def mega(self, x, y, h, kind, hue):
        """one megatower of a given silhouette: spire / drum / twins / blade / ziggurat / saucer / cake. Every kind wears the
        window shader, neon spines and collars in its hue, screens on the face toward the tower, a needle + beacon."""
        r = math.hypot(x, y)
        a = amin(r)
        ang = rng.uniform(0, math.pi / 2)
        pal = pal_of(hue)
        nc = tuple(channel * 0.45 for channel in body_col(pal))
        # Same three random draws and silhouettes; shared worn cyber skin
        # replaces the old full-height luminous office grids on hero towers.
        col = (rng.random(), 2.0 + rng.uniform(0.0, 0.95), pal, rng.uniform(0.35, 0.62) * 0.38)

        def outline(fp, z, alpha=0.8, w=None):
            w = w or a * 1.1
            alpha *= 1.0                                                          # v4: full neon (the references' towers are lit to the edge)
            for k in range(len(fp)):
                (ax, ay), (bx, by) = fp[k], fp[(k + 1) % len(fp)]
                self.neon.strip(ax, ay, bx, by, z - w * 0.5, w, w, (*nc, alpha))

        def spines(fp, z0, z1, step=2, alpha=0.7, w=None):
            w = w or a * 1.0
            alpha *= 1.0
            step = max(1, min(step, len(fp) // 4))                              # v4: four spines per tier
            for (px, py) in fp[::step]:
                self.neon.prism(fp_rect(px, py, w, w, ang), z0 + 3, z1 - 2, (*nc, alpha))

        def screen_on(fp, z0, z1, frac_w=0.6, frac_h=0.3, zf=0.6, alpha=1.0):
            i = fp_facing_edge(fp)
            ax, ay = fp[i]
            bx, by = fp[(i + 1) % len(fp)]
            L = math.hypot(bx - ax, by - ay)
            if L < 20:
                return
            sw, sh = L * frac_w, (z1 - z0) * frac_h
            zc = z0 + (z1 - z0) * zf
            dx, dy = (bx - ax) / L, (by - ay) / L
            nx, ny = dy, -dx
            mx, my = (ax + bx) / 2 + nx * 0.8, (ay + by) / 2 + ny * 0.8
            hw, hh = sw / 2, sh / 2
            pts = [(mx - dx * hw, my - dy * hw, zc - hh), (mx + dx * hw, my + dy * hw, zc - hh), (mx + dx * hw, my + dy * hw, zc + hh), (mx - dx * hw, my - dy * hw, zc + hh)]
            self.screen.poly(pts, [(0, 0), (sw, 0), (sw, sh), (0, sh)], (rng.random(), sw, sh, alpha),
                             mi=screen_mi(sw, sh))

        def needle(px, py, z0, L, w):
            self.struct.prism(fp_ellipse(px, py, max(1.5, w), max(1.5, w), 8, 0), z0, z0 + L, (0, 0, 0, 1))
            self.neon.prism(fp_ellipse(px, py, max(1.0, w * 0.6), max(1.0, w * 0.6), 6, 0), z0 + L * 0.3, z0 + L * 0.95, (*nc, 0.5))
            self.neon.box(px, py, z0 + L, a * 3.0, a * 3.0, a * 3.0, 0, (*PAL['beacon'], 1.0))

        def cap_bottom(fp, z):
            self.roof.poly([(px, py, z) for px, py in reversed(fp)], [(px, py) for px, py in reversed(fp)], col)

        if kind == 'spire':
            base = h * rng.uniform(0.085, 0.12)
            fp = fp_chamfer(x, y, base, base, base * 0.22, ang)
            fr, sc = [0.38, 0.58, 0.74, 0.86, 0.94, 1.0], [0.84, 0.8, 0.74, 0.66, 0.5]
            z = 0.0
            for i, f in enumerate(fr):
                z1 = h * f
                self.fac.prism(fp, z, z1, col, cap=True, cap_acc=self.roof)
                spines(fp, z, z1, 2, 0.75)
                outline(fp, z1, 0.9)
                if rng.random() < 0.8:
                    screen_on(fp, z, z1, 0.62, 0.34, 0.55, 1.1)
                if i < len(fr) - 1:
                    fp = fp_scale(fp, sc[i])
                z = z1
            needle(x, y, h, h * 0.12, a * 1.5)
            rad = base * 0.75
        elif kind == 'drum':
            R0 = h * rng.uniform(0.06, 0.08)
            n = rng.randint(3, 4)
            z = 0.0
            for i in range(n):
                z1 = h * (i + 1) / n
                Ri = R0 * (0.82 ** i)
                fp = fp_ellipse(x, y, Ri, Ri * rng.uniform(0.85, 1.0), 28, ang)
                self.fac.prism(fp, z, z1, col, cap=True, cap_acc=self.roof)
                outline(fp, z1, 1.0, a * 1.5)
                outline(fp, z + a * 1.2, 0.6, a * 1.2)
                spines(fp, z, z1, 7, 0.55)
                if i < 2:
                    screen_on(fp, z, z1, 0.4, 0.3, 0.6, 1.0)
                z = z1
            needle(x, y, h, h * 0.14, a * 1.4)
            rad = R0 * 1.1
        elif kind == 'twins':
            w, d = h * 0.11, h * 0.055
            gap = w * 0.55
            for sgn, hh in ((-1, h), (1, h * rng.uniform(0.82, 0.92))):
                ox, oy = rot(sgn * (w / 2 + gap / 2), 0, ang)
                fp = fp_chamfer(x + ox, y + oy, w, d, d * 0.18, ang)
                self.fac.prism(fp, 0, hh, col, cap=True, cap_acc=self.roof)
                spines(fp, 0, hh, 2, 0.8)
                outline(fp, hh, 0.9)
                screen_on(fp, 0, hh, 0.7, 0.16, 0.7, 1.0)
                needle(x + ox, y + oy, hh, h * 0.08, a * 1.2)
            for zb in [h * f for f in (0.3, 0.5, 0.68, 0.84)]:
                self.struct.box(x, y, zb, gap + w * 0.3, d * 0.35, h * 0.012, ang, (0, 0, 0, 1))
                self.neon.box(x, y, zb + h * 0.012, gap + w * 0.25, a * 1.2, a * 1.2, ang, (*PAL['cyan'], 0.8))
            rad = w * 1.2 + gap
        elif kind == 'blade':
            w, d = h * 0.17, h * 0.045
            ang = math.atan2(x, -y) + rng.uniform(-0.35, 0.35)                   # the broad face toward the tower
            fp = fp_rect(x, y, w, d, ang)
            self.fac.prism(fp, 0, h, col, cap=True, cap_acc=self.roof)
            spines(fp, 0, h, 1, 0.85)
            outline(fp, h, 1.0)
            screen_on(fp, 0, h, 0.6, 0.42, 0.62, 1.3)                             # a giant screen
            fin = fp_rect(x, y, w * 0.5, d * 0.25, ang)
            self.struct.prism(fin, h, h * 1.1, (0, 0, 0, 1))
            outline(fin, h * 1.1, 1.0)
            rad = w * 0.6
        elif kind == 'ziggurat':
            n = rng.randint(7, 9)
            base = min(h * rng.uniform(0.9, 1.2), 1200.0)                         # v5d: a 3 km ziggurat at 2.7 km was a wall across the sky
            fp = fp_rect(x, y, base, base, ang)
            z = 0.0
            for i in range(n):
                z1 = h * (i + 1) / n
                self.fac.prism(fp, z, z1, col, cap=True, cap_acc=self.roof)
                outline(fp, z1 - 1.0, 0.85, a * 1.5)
                if i == 1:
                    screen_on(fp, z, z1, 0.5, 0.6, 0.5, 1.0)
                fp = fp_scale(fp, 0.82)
                z = z1
            self.neon.prism(fp_scale(fp, 0.4), z, z + h * 0.08, (*nc, 1.0))
            needle(x, y, z + h * 0.08, h * 0.1, a * 1.4)
            rad = base * 0.55
        elif kind == 'saucer':
            rs = h * 0.03
            shaft = fp_ellipse(x, y, rs, rs, 16, 0)
            self.fac.prism(shaft, 0, h * 0.8, col, cap=True, cap_acc=self.roof)
            spines(shaft, 0, h * 0.8, 4, 0.6)
            R = h * 0.13
            z0, z1 = h * 0.76, h * 0.86
            disc = fp_ellipse(x, y, R, R, 32, 0)
            self.fac.prism(disc, z0, z1, col, cap=True, cap_acc=self.roof)
            cap_bottom(disc, z0)
            outline(disc, z1, 1.0, a * 1.6)
            outline(disc, z0 + a, 0.7, a * 1.4)
            top = fp_ellipse(x, y, R * 0.7, R * 0.7, 32, 0)
            self.struct.prism(top, z1, z1 + h * 0.02, (0, 0, 0, 1))
            needle(x, y, z1 + h * 0.02, h * 0.14, a * 1.4)
            rad = R * 1.05
        else:  # 'cake'
            base = h * rng.uniform(0.16, 0.22)
            n = rng.randint(7, 11)
            fp = fp_chamfer(x, y, base, base, base * 0.15, ang) if rng.random() < 0.5 else fp_ellipse(x, y, base / 2, base / 2, 20, ang)
            z = 0.0
            for i in range(n):
                z1 = h * (i + 1) / n
                self.fac.prism(fp, z, z1, col, cap=True, cap_acc=self.roof)
                outline(fp, z1, 0.55)
                if i == 1:
                    screen_on(fp, z, z1, 0.55, 0.5, 0.5, 1.0)
                if i < n - 1:
                    fp = fp_scale(fp, 0.88)
                z = z1
            needle(x, y, h, h * 0.1, a * 1.3)
            rad = base * 0.6
        if on('ringsx') and kind in ('spire', 'drum', 'twins', 'blade', 'cake'):    # v4: neon rings round the crown (one to three, stacked)
            for k in range(rng.randint(1, 3)):
                self.ring_at(x, y, h * (0.84 + 0.055 * k), rad * (1.45 + 0.35 * k), nc, max(2.0, a * 1.4), rng.uniform(-0.08, 0.08), 1.0, 64)
        if kind in ('spire', 'twins', 'blade', 'cake', 'drum'):
            self.spikes_at(x, y, h, h, nc, rng.randint(6, 12), rad * 0.45)
        if on('sigils') and r < 12000:
            self.sigil_free(x, y, h * rng.uniform(0.45, 0.62), max(30.0, rad * rng.uniform(0.9, 1.4)), pal, rad * 1.12)
        if r < 12000:
            self.mega_detail(x, y, h, rad, nc, pal, ang, a, kind)                 # v5: belts, ring platforms, fins, antennas
        self.excl.append((x, y, rad + 60.0))
        self.mega_tops.append((x, y, h))
        self.tall.append((x, y, h))
        self.n_bld += 1

    def ring_deck(self, x, y, z, Ri, Ro, th, n=48):
        """v5 a dark annular deck round a shaft: top, underside, outer and inner walls"""
        for i in range(n):
            t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            c0, s0, c1, s1 = math.cos(t0), math.sin(t0), math.cos(t1), math.sin(t1)
            top = [(x + Ri * c0, y + Ri * s0, z + th), (x + Ro * c0, y + Ro * s0, z + th), (x + Ro * c1, y + Ro * s1, z + th), (x + Ri * c1, y + Ri * s1, z + th)]
            self.struct.poly(top, [(px-x, py-y) for px, py, _ in top], (0, 0, 0, 1))
            self.struct.poly([(px, py, z) for px, py, _ in reversed(top)],
                             [(px-x, py-y) for px, py, _ in reversed(top)], (0, 0, 0, 1))
            outer_uv = [(Ro*t0, z), (Ro*t1, z), (Ro*t1, z+th), (Ro*t0, z+th)]
            inner_uv = [(Ri*t1, z), (Ri*t0, z), (Ri*t0, z+th), (Ri*t1, z+th)]
            self.struct.poly([(x + Ro * c0, y + Ro * s0, z), (x + Ro * c1, y + Ro * s1, z), (x + Ro * c1, y + Ro * s1, z + th), (x + Ro * c0, y + Ro * s0, z + th)], outer_uv, (0, 0, 0, 1))
            self.struct.poly([(x + Ri * c1, y + Ri * s1, z), (x + Ri * c0, y + Ri * s0, z), (x + Ri * c0, y + Ri * s0, z + th), (x + Ri * c1, y + Ri * s1, z + th)], inner_uv, (0, 0, 0, 1))

    def mega_detail(self, x, y, h, rad, nc, pal, ang, a, kind):
        """v5 (user: "our major buildings need a lot more detail ... the tall buildings with the rings around them"): lit BELTS
        hugging the shaft, one or two RING PLATFORMS (a dark annular deck with lit rims, pods and window blocks on it, light-falls
        pouring from under it), buttress FINS at the foot with lit edges, an ANTENNA ARRAY on the crown"""
        for _ in range(rng.randint(2, 4)):                                       # belts
            zf = rng.uniform(0.12, 0.8)
            self.ring_at(x, y, h * zf, rad * rng.uniform(0.95, 1.12), nc, max(1.6, a * 1.4), 0.0, 0.85, 56)
        for _ in range(rng.randint(1, 2)):                                       # ring platforms
            zp = h * rng.uniform(0.28, 0.72)
            Ri = rad * rng.uniform(0.9, 1.1)
            Ro = min(rad * rng.uniform(1.5, 2.2), Ri + 300.0 + h * 0.06)          # v5d: a deck is a deck, not a county (the ziggurat's was 3.6 km)
            if math.hypot(x, y) - Ro < 900.0:
                continue                                                          # v5d: never over the camera
            th = max(6.0, h * 0.008)
            self.ring_deck(x, y, zp, Ri, Ro, th)
            self.ring_at(x, y, zp + th + a * 0.3, Ro * 1.003, nc, max(1.6, a * 1.5), 0.0, 1.0, 64)
            self.ring_at(x, y, zp - a * 0.3, Ro * 1.003, nc, max(1.2, a * 1.1), 0.0, 0.6, 64)
            self.ring_at(x, y, zp + th + a * 0.3, Ri * 0.995, nc, max(1.2, a * 1.0), 0.0, 0.7, 48)
            npod = rng.randint(6, 14)
            for j in range(npod):                                                # pods and window blocks on the deck
                angp = 2 * math.pi * j / npod + rng.uniform(-0.1, 0.1)
                rr = rng.uniform(Ri + (Ro - Ri) * 0.25, Ro - (Ro - Ri) * 0.2)
                px, py = x + rr * math.cos(angp), y + rr * math.sin(angp)
                bw = (Ro - Ri) * rng.uniform(0.2, 0.42)
                bh = min((Ro - Ri) * rng.uniform(0.25, 0.9), 40.0 + h * 0.07)         # v5d
                pc = (rng.random(), rng.random(), pal, 0.45)
                pod_depth = bw * rng.uniform(0.6, 1.2)
                # Preserve the original conditional beacon draw, but let the new
                # pod own its attached lights instead of leaving a floating cap.
                if pc[1] < PANEL_FRAC:
                    rng.random()
                build_cyber_block(self, cx=px, cy=py, w=bw, d=pod_depth, h=bh,
                    ang=angp, seed=pc[0], pal=pal, distance=math.hypot(px, py),
                    far=math.hypot(px, py) > 11000, neon=on('neon'), base_z=zp + th)
            for _ in range(rng.randint(2, 4)):                                   # light-falls from under the deck
                angf = rng.uniform(0, 2 * math.pi)
                rr = rng.uniform(Ri + (Ro - Ri) * 0.3, Ro - (Ro - Ri) * 0.15)
                fx, fy = x + rr * math.cos(angf), y + rr * math.sin(angf)
                yaw = math.atan2(-fx, -fy)
                self.lightfall(fx, fy, zp, (Ro - Ri) * rng.uniform(0.1, 0.2), min(zp * 0.55, h * 0.3), math.cos(yaw), -math.sin(yaw), nc, rng.uniform(0.8, 1.2))
        if kind in ('spire', 'twins', 'blade', 'drum', 'cake'):                    # buttress fins at the foot
            nf = rng.randint(4, 8)
            for k in range(nf):
                angk = ang + 2 * math.pi * k / nf + math.pi / nf
                dx, dy = math.cos(angk), math.sin(angk)
                r0_, fl = rad * 0.75, min(rad * rng.uniform(0.5, 0.9), 320.0)      # v5d
                fh = h * rng.uniform(0.12, 0.24)
                tk = max(4.0, rad * 0.03)
                fin = [(x + dx * r0_ + dy * tk, y + dy * r0_ - dx * tk), (x + dx * (r0_ + fl) + dy * tk, y + dy * (r0_ + fl) - dx * tk),
                       (x + dx * (r0_ + fl) - dy * tk, y + dy * (r0_ + fl) + dx * tk), (x + dx * r0_ - dy * tk, y + dy * r0_ + dx * tk)]
                self.struct.prism(fin, 0.0, fh, (0, 0, 0, 1), cap=True)
                tube(self.neon, (x + dx * (r0_ + fl), y + dy * (r0_ + fl), fh), (x + dx * r0_, y + dy * r0_, fh + fl * 0.9), max(1.2, a * 1.0), max(1.2, a * 1.0), (*nc, 0.9), 6)
        for _ in range(rng.randint(3, 6)):                                       # the antenna array
            rr = rad * rng.uniform(0.1, 0.4)
            angm = rng.uniform(0, 2 * math.pi)
            mx, my = x + rr * math.cos(angm), y + rr * math.sin(angm)
            mh = h * rng.uniform(0.04, 0.11)
            self.struct.prism(fp_ellipse(mx, my, max(1.5, a * 0.9), max(1.5, a * 0.9), 6, 0), h, h + mh, (0, 0, 0, 1))
            self.neon.prism(fp_ellipse(mx, my, max(1.0, a * 0.6), max(1.0, a * 0.6), 6, 0), h + mh * 0.5, h + mh * 0.92, (*nc, 0.6))
            self.neon.box(mx, my, h + mh, a * 2.4, a * 2.4, a * 2.4, 0, (*(PAL['beacon'] if rng.random() < 0.5 else PAL['white']), 1.0))


    def megatowers(self):
        placed = [(polar(7200, 42), 400.0), (polar(8600, -92), 800.0), (polar(11500, 158), 500.0)]   # the v1 landmarks
        if on('origin'):
            placed.append((polar(ORIGIN['r'], ORIGIN['az']), 1500.0))
        if on('tether'):
            placed.append((polar(TETHER['d'], TETHER['az']), 500.0))

        def ok(x, y, rad):
            if math.hypot(x, y) < 1700:
                return False                                                  # v5: outside the core
            for (px, py), pr in placed:
                if math.hypot(x - px, y - py) < rad + pr:
                    return False
            return True

        def water(x, y):
            az, r = az_of(x, y), math.hypot(x, y)
            return on('water') and BAY[0] < az < BAY[1] and BAY_R[0] < r < BAY_R[1]

        kinds = [('spire', 22), ('drum', 14), ('twins', 14), ('blade', 16), ('ziggurat', 8), ('saucer', 10), ('cake', 16)]
        specs = [(polar(r_, az_), h_, k_, hue_) for az_, r_, h_, k_, hue_ in MEGA_HERO]
        tries = 0
        while len(specs) < len(MEGA_HERO) + MEGA_N and tries < 6000:
            tries += 1
            r_ = min(11500.0, max(1300.0, 3800.0 * math.exp(rng.gauss(0, 0.55))))
            az_ = rng.uniform(-180, 180)
            if abs(az_) < LANE_HALF + 10:
                continue
            x, y = polar(r_, az_)
            if water(x, y):
                continue
            h_ = min(3200.0, max(900.0, 1250.0 * math.exp(rng.gauss(0, 0.42))))   # v5: x1.3
            if r_ > 6000:
                h_ *= 1.25
            k_ = wchoice(kinds)
            if k_ == 'ziggurat' and r_ < 4500:
                k_ = 'cake'                                                       # v5d: the wide pyramids stay far
            specs.append(((x, y), h_, k_, wchoice(NEON_W)))
        far_kinds = [('spire', 30), ('twins', 20), ('ziggurat', 20), ('cake', 20), ('drum', 10)]
        tries = 0
        n_far = 0
        while n_far < FAR_MEGA_N and tries < 6000:
            tries += 1
            r_ = rng.uniform(13000, 24000)
            az_ = rng.uniform(-180, 180)
            if abs(az_) < LANE_HALF + 12:
                continue
            x, y = polar(r_, az_)
            h_ = rng.uniform(2500, 6000)
            specs.append(((x, y), h_, wchoice(far_kinds), wchoice(NEON_W)))
            n_far += 1
        n = 0
        for index, ((x, y), h_, k_, hue_) in enumerate(specs):
            rad = h_ * 0.13 + 80
            if not ok(x, y, rad) or h_ > ship_cap(x, y):                          # v5b: no supertall in front of a battlecruiser
                continue
            placed.append(((x, y), rad))
            marks = self.mark_geometry()
            tall_start, count_start = len(self.tall), self.n_bld
            self.mega(x, y, h_, k_, hue_)
            keep = keep_mega(index, x, y, len(MEGA_HERO))
            self.composition['megatowers'].append(dict(index=index, cx=x, cy=y, h=h_,
                kind=k_, hue=hue_, hero=index < len(MEGA_HERO), kept=keep))
            if not keep:
                self.rewind_geometry(marks)
                self.removed_hosts.update(self.tall[tall_start:])
                self.n_bld = count_start
            n += 1
            log(f'  mega {k_} {hue_}: az {az_of(x, y):.0f} r {math.hypot(x, y):.0f} h {h_:.0f} (top {math.degrees(math.atan2(h_ - CAM_H, math.hypot(x, y))):.0f} deg up)')
        log(f'megatowers: {n} placed ({len(MEGA_HERO)} heroes + rolled + far ring)')

    # ---- v2: RAILS (user: "like the train, I don't see the train")
    def rails(self):
        for line_index, (az_c, d_c, R, zd, hue, n_tr, n_st) in enumerate(RAIL_LINES):
            cx, cy = polar(d_c, az_c)
            nc = PAL[hue]
            wd = 11.0
            N = int(2 * math.pi * R / 60.0)
            phi_near = math.atan2(-cy, -cx) if d_c > 1 else 1.05                # the ring angle facing the camera (the loop: anywhere)

            def P(phi, rr=R, cx=cx, cy=cy):
                return (cx + rr * math.cos(phi), cy + rr * math.sin(phi))
            for i in range(N):
                t0, t1 = 2 * math.pi * i / N, 2 * math.pi * (i + 1) / N
                tm = (t0 + t1) / 2
                px, py = P(tm)
                dist = math.hypot(px, py)
                a = amin(dist, 1.4)
                xy = [P(t0, R - wd / 2), P(t0, R + wd / 2), P(t1, R + wd / 2), P(t1, R - wd / 2)]
                self.struct.prism(xy, zd - 2.2, zd, (0, 0, 0, 1), cap=True)
                self.ribbon.poly([(px, py, zd + 0.06) for px, py in xy], [(0, 0), (0, 1), (R * (t1 - t0), 1), (R * (t1 - t0), 0)], (*nc, 0.55))   # v4: the rail deck glows in the line's hue
                for rr in (R - wd / 2 + a * 0.6, R + wd / 2 - a * 0.6):
                    (x0, y0), (x1, y1) = P(t0, rr), P(t1, rr)
                    self.neon.strip(x0, y0, x1, y1, zd, a, a, (*nc, 0.42))
                if i % 2 == 0:                                                   # a pylon every ~120 m: tapered leg, cross-head, lit cap
                    qx, qy = P(t0)
                    self.struct.prism(fp_ellipse(qx, qy, 4.5 + zd * 0.008, 4.5 + zd * 0.008, 8, 0), 0.0, zd * 0.55, (0, 0, 0, 1))
                    self.struct.prism(fp_ellipse(qx, qy, 3.2 + zd * 0.004, 3.2 + zd * 0.004, 8, 0), zd * 0.55, zd - 2.2, (0, 0, 0, 1))
                    self.struct.box(qx, qy, zd - 5.0, wd * 1.3, 3.5, 2.8, t0 + math.pi / 2, (0, 0, 0, 1))
                    self.neon.box(qx, qy, zd + 0.3, a * 1.3, a * 1.3, a * 1.3, 0, (*nc, 0.35))
                    if zd > 250 and i % 6 == 0:
                        self.neon.box(qx, qy, zd * 0.5, a * 1.3, a * 1.3, a * 1.3, 0, (*PAL['beacon'], 0.5))
            for j in range(n_st):
                phi = phi_near + (j - (n_st - 1) / 2) * (2.1 if d_c < 1 else 0.9) + rng.uniform(-0.15, 0.15)
                if line_index != 0:
                    self.station(P, phi, R, zd, wd, nc)
            for j in range(n_tr):
                if d_c < 1:
                    phi = math.radians([150.0, -70.0, 40.0][j % 3]) + rng.uniform(-0.1, 0.1)   # the loop: one behind, one over the harbour side, one right
                else:
                    phi = phi_near + [0.0, 0.62, -0.5][j % 3] + rng.uniform(-0.06, 0.06)       # the first train sits AT the near point (the hero train)
                ncars = rng.randint(7, 10)
                if line_index != 0 or j != 0:
                    self.train(P, phi, R, zd, wd, nc, ncars=ncars)

    def station(self, P, phi, R, zd, wd, nc):
        L = 90.0
        dphi = L / R
        n = 6
        for i in range(n):
            t0, t1 = phi - dphi / 2 + dphi * i / n, phi - dphi / 2 + dphi * (i + 1) / n
            xy = [P(t0, R + wd / 2), P(t0, R + wd / 2 + 14), P(t1, R + wd / 2 + 14), P(t1, R + wd / 2)]
            self.struct.prism(xy, zd - 1.5, zd + 1.0, (0, 0, 0, 1), cap=True)
            xy2 = [P(t0, R - wd / 2 - 2), P(t0, R + wd / 2 + 16), P(t1, R + wd / 2 + 16), P(t1, R - wd / 2 - 2)]
            self.struct.prism(xy2, zd + 9.0, zd + 10.2, (0, 0, 0, 1), cap=True)
            (x0, y0), (x1, y1) = P(t0, R + wd / 2 + 15.5), P(t1, R + wd / 2 + 15.5)
            self.neon.strip(x0, y0, x1, y1, zd + 9.4, 0.9, 0.9, (*nc, 0.9))
            (x0, y0), (x1, y1) = P(t0, R + wd / 2 + 7), P(t1, R + wd / 2 + 7)
            seg = math.hypot(x1 - x0, y1 - y0)
            self.trail.quad_dir((x0 + x1) / 2, (y0 + y1) / 2, zd + 1.05, (x1 - x0) / seg, (y1 - y0) / seg, 12.0, seg, (*PAL['white'], 0.35))
        for k in range(4):
            t = phi - dphi / 2 + dphi * (k + 0.5) / 4
            qx, qy = P(t, R + wd / 2 + 12)
            self.neon.box(qx, qy, zd + 4.5, 0.8, 0.8, 0.8, 0, (*PAL['white'], 0.5))

    def train(self, P, phi, R, zd, wd, nc, ncars=7):
        # v2b: double-deck maglev cars (a megacity's trains) — a 22 x 4 m car is 2 px at 1080p from 2 km; these read
        car_L, gap, car_W, car_H = 28.0, 1.8, 4.6, 6.0
        dphi_car = (car_L + gap) / R
        rr = R - wd * 0.22
        wincol = (0.6 * nc[0] + 0.4, 0.6 * nc[1] + 0.4, 0.6 * nc[2] + 0.4)
        for c in range(ncars):
            t0 = phi + (c - ncars / 2) * dphi_car
            t1 = t0 + car_L / R
            (x0, y0), (x1, y1) = P(t0, rr), P(t1, rr)
            L = math.hypot(x1 - x0, y1 - y0)
            dx, dy = (x1 - x0) / L, (y1 - y0) / L
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            dist = math.hypot(mx, my)
            a = amin(dist)
            self.struct.box(mx, my, zd + 0.5, L, car_W, car_H, math.atan2(dy, dx), (0, 0, 0, 1))
            for sgn in (-1, 1):                                                  # two window decks a side
                ox, oy = -dy * sgn * (car_W / 2 + 0.05), dx * sgn * (car_W / 2 + 0.05)
                for zw in (zd + 1.6, zd + 4.1):
                    self.neon.strip(x0 + ox, y0 + oy, x1 + ox, y1 + oy, zw, max(0.25, a * 0.5), max(1.3, a * 0.9), (*wincol, 1.1))
            self.neon.strip(x0, y0, x1, y1, zd + 0.12, car_W * 0.6, max(0.3, a * 0.5), (*nc, 1.0))
            self.neon.strip(x0, y0, x1, y1, zd + 0.5 + car_H, car_W * 0.3, max(0.3, a * 0.5), (*nc, 0.5))   # a roof strip
            if c == ncars - 1:
                self.neon.box(x1, y1, zd + 1.6, max(0.8, a), car_W * 0.7, max(0.8, a), math.atan2(dy, dx), (*PAL['white'], 1.0))
            if c == 0:
                self.neon.box(x0, y0, zd + 1.6, max(0.8, a), car_W * 0.7, max(0.8, a), math.atan2(dy, dx), (*PAL['tail'], 1.0))
        for k in range(5):                                                       # the charged-track trail behind the tail
            ta = phi - ncars / 2 * dphi_car - (k + 1) * 25.0 / R
            tb = ta + 25.0 / R
            (x0, y0), (x1, y1) = P(ta, rr), P(tb, rr)
            self.neon.strip(x0, y0, x1, y1, zd + 0.05, car_W * 0.5, 0.25, (*nc, 0.7 * (1 - k / 5)))

    # ---- v2: HOLOGRAPHIC PANELS floating over the roofs (translucent glyph screens with a neon frame)
    def holos(self):
        cands = [c for c in self.tall if 1400 < math.hypot(c[0], c[1]) < 7500 and abs(az_of(c[0], c[1])) > LANE_HALF + 4]
        rng.shuffle(cands)
        for (x, y, h) in cands[:int(70 * DETAIL)]:
            r = math.hypot(x, y)
            w = rng.uniform(40, 150) * (1 + r / 8000)
            hh = w * rng.uniform(0.35, 0.7)
            zc = h + rng.uniform(25, 70) + hh / 2
            yaw = math.atan2(-x, -y) + rng.uniform(-0.6, 0.6)                    # the panel's normal: roughly toward the tower
            nx, ny = math.sin(yaw), math.cos(yaw)
            ax, ay = -ny, nx
            hue = PAL[wchoice(HOLO_W)]
            alpha = rng.uniform(0.7, 1.2)
            pts = [(x - ax * w / 2, y - ay * w / 2, zc - hh / 2), (x + ax * w / 2, y + ay * w / 2, zc - hh / 2),
                   (x + ax * w / 2, y + ay * w / 2, zc + hh / 2), (x - ax * w / 2, y - ay * w / 2, zc + hh / 2)]
            self.holo.poly(pts, [(0, 0), (w, 0), (w, hh), (0, hh)], (*hue, alpha))
            a = amin(r)
            for z in (zc - hh / 2, zc + hh / 2):
                self.neon.strip(x - ax * w / 2, y - ay * w / 2, x + ax * w / 2, y + ay * w / 2, z - a * 0.5, a, a, (*hue, 0.6))
            for sgn in (-1, 1):
                self.neon.prism(fp_rect(x + sgn * ax * w / 2, y + sgn * ay * w / 2, a, a, 0), zc - hh / 2, zc + hh / 2, (*hue, 0.6))


    # ---- v4 THE REFERENCE COPY: rings, spikes, sigils, platforms, light-falls
    def ring_at(self, x, y, z, Rr, nc, tube_r, tilt=0.0, alpha=1.0, n=48):
        neon_ring(self.neon, x, y, z, Rr, tube_r, (*nc, alpha), n, tilt)

    def spikes_at(self, x, y, z, h, nc, n=7, spread=1.0):
        """a spiked crown: n thin tapered spikes leaning outward from the top, their upper part lit in the tower's hue"""
        a = amin(math.hypot(x, y))
        for k in range(n):
            ang_ = rng.uniform(0, 2 * math.pi)
            rr = rng.uniform(0.15, 1.0) * spread
            L = h * rng.uniform(0.06, 0.16)
            root = (x + rr * math.cos(ang_), y + rr * math.sin(ang_), z)
            tip = (x + rr * 1.6 * math.cos(ang_), y + rr * 1.6 * math.sin(ang_), z + L)
            tube(self.struct, root, tip, max(1.2, a * 1.4), max(0.5, a * 0.5), (0, 0, 0, 1), 5)
            self.neon.prism(fp_rect(tip[0], tip[1], max(0.8, a * 1.2), max(0.8, a * 1.2), 0), tip[2] - L * 0.3, tip[2], (*nc, 0.9))

    def sigil_on(self, fp, z0, z1, hp, frac=0.7, zf=0.6):
        """a sigil on the face of footprint fp that looks toward the tower, between z0 and z1"""
        i = fp_facing_edge(fp)
        ax_, ay_ = fp[i]
        bx_, by_ = fp[(i + 1) % len(fp)]
        L = math.hypot(bx_ - ax_, by_ - ay_)
        if L < 16:
            return
        s = min(L * frac, (z1 - z0) * 0.8)
        zc = z0 + (z1 - z0) * zf
        dx, dy = (bx_ - ax_) / L, (by_ - ay_) / L
        nx, ny = dy, -dx
        mx, my = (ax_ + bx_) / 2 + nx * 1.0, (ay_ + by_) / 2 + ny * 1.0
        pts = [(mx - dx * s / 2, my - dy * s / 2, zc - s / 2), (mx + dx * s / 2, my + dy * s / 2, zc - s / 2),
               (mx + dx * s / 2, my + dy * s / 2, zc + s / 2), (mx - dx * s / 2, my - dy * s / 2, zc + s / 2)]
        self.sigil.poly(pts, [(0, 0), (s, 0), (s, s), (0, s)], (rng.random(), s, s, hp))

    def sigil_free(self, x, y, zc, s, hp, off):
        """a sigil floating just outside a tower's axis, facing the camera"""
        yaw = math.atan2(-x, -y)
        nx, ny = math.sin(yaw), math.cos(yaw)
        ax, ay = -ny, nx
        cx, cy = x + nx * off, y + ny * off
        pts = [(cx - ax * s / 2, cy - ay * s / 2, zc - s / 2), (cx + ax * s / 2, cy + ay * s / 2, zc - s / 2),
               (cx + ax * s / 2, cy + ay * s / 2, zc + s / 2), (cx - ax * s / 2, cy - ay * s / 2, zc + s / 2)]
        self.sigil.poly(pts, [(0, 0), (s, 0), (s, s), (0, s)], (rng.random(), s, s, hp))

    def lightfall(self, x, y, ztop, w, L, ax, ay, hue, strength):
        """a light-fall: two crossed vertical translucent sheets pouring DOWN from (x, y, ztop), width w, length L; UV v = 0 at the top"""
        for (bx, by, st) in ((ax, ay, strength), (-ay, ax, strength * 0.8)):
            pts = [(x - bx * w / 2, y - by * w / 2, ztop - L), (x + bx * w / 2, y + by * w / 2, ztop - L),
                   (x + bx * w / 2, y + by * w / 2, ztop), (x - bx * w / 2, y - by * w / 2, ztop)]
            self.fall.poly(pts, [(0, 1), (1, 1), (1, 0), (0, 0)], (*hue, st))

    def sigils(self):
        """v4 (the references): glowing emblems — circle / hexagon / diamond — floating over the tallest towers, facing the tower"""
        cands = [c for c in self.tall if 1200 < math.hypot(c[0], c[1]) < 9000 and abs(az_of(c[0], c[1])) > LANE_HALF + 4]
        rng.shuffle(cands)
        n = 0
        features = []
        for (x, y, h) in cands[:int(40 * DETAIL)]:                             # v5: fewer, bigger towers -> fewer floating emblems
            start = (len(self.sigil.v), len(self.sigil.f))
            r = math.hypot(x, y)
            s = rng.uniform(40, 110) * (1 + r / 7000)
            zc = h + rng.uniform(20, 60) + s / 2
            yaw = math.atan2(-x, -y) + rng.uniform(-0.5, 0.5)
            nx, ny = math.sin(yaw), math.cos(yaw)
            ax, ay = -ny, nx
            hp = pal_of(wchoice(HOLO_W))
            pts = [(x - ax * s / 2, y - ay * s / 2, zc - s / 2), (x + ax * s / 2, y + ay * s / 2, zc - s / 2),
                   (x + ax * s / 2, y + ay * s / 2, zc + s / 2), (x - ax * s / 2, y - ay * s / 2, zc + s / 2)]
            self.sigil.poly(pts, [(0, 0), (s, 0), (s, s), (0, s)], (rng.random(), s, s, hp))
            features.append(feature_record(self.sigil, start, n, self.host_visible(x, y, h)))
            n += 1
        prune_features(self.sigil, 'floating_sigils', features, self.composition['secondary'])
        log(f'sigils: {n} floating + the megatowers\' own')

    def platforms(self, n_want=9):
        """v4 (reference 2): FLOATING PLATFORMS over the mid city — a dark saucer with two neon rims, a lit underside, small window
        towers on top and one to three LIGHT-FALLS pouring from below"""
        n, tries = 0, 0
        while n < n_want and tries < 600:
            tries += 1
            az = rng.uniform(-180, 180)
            if abs(az) < LANE_HALF + 8:
                continue
            d = rng.uniform(1600, 6500)
            x, y = polar(d, az)
            z = rng.uniform(550, 1500) * (1 + d / 9000)
            Rp = rng.uniform(120, 320) * (1 + d / 8000)
            if any(math.hypot(x - mx, y - my) < Rp + 250 and mh > z - 200 for mx, my, mh in self.mega_tops):
                continue
            hue_name = wchoice(NEON_W)
            nc = PAL[hue_name]
            pal = pal_of(hue_name)
            a = amin(d)
            th = Rp * 0.14
            disc = fp_ellipse(x, y, Rp, Rp * rng.uniform(0.85, 1.0), 40, rng.uniform(0, 3))
            self.struct.prism(disc, z - th, z, (0, 0, 0, 1), cap=True)
            self.struct.poly([(px, py, z - th) for px, py in reversed(disc)], [(px, py) for px, py in reversed(disc)], (0, 0, 0, 1))   # v4f: dark underside
            self.ring_at(x, y, z - a, Rp * 1.005, nc, max(0.8, a * 1.1), 0.0, 1.0)
            self.ring_at(x, y, z - th + a, Rp * 1.005, nc, max(0.6, a * 0.9), 0.0, 0.6)
            for _ in range(rng.randint(3, 7)):
                rr = rng.uniform(0, Rp * 0.7)
                ang_ = rng.uniform(0, 2 * math.pi)
                bx, by = x + rr * math.cos(ang_), y + rr * math.sin(ang_)
                w = rng.uniform(Rp * 0.08, Rp * 0.2)
                h = rng.uniform(Rp * 0.25, Rp * 0.9)
                pod_depth = w * rng.uniform(0.6, 1.2)
                pod_angle = rng.uniform(0, 3)
                style = rng.random()
                pod_seed, pod_pal = rng.random(), pal_roll()
                rng.uniform(0.23, 0.39)  # spend retired window-density draw
                build_cyber_block(self, cx=bx, cy=by, w=w, d=pod_depth, h=h,
                    ang=pod_angle, seed=pod_seed, pal=pod_pal, distance=d,
                    far=False, neon=on('neon'), base_z=z)
            for _ in range(rng.randint(1, 3)):
                rr = rng.uniform(0.2, 0.8) * Rp
                ang_ = rng.uniform(0, 2 * math.pi)
                fx, fy = x + rr * math.cos(ang_), y + rr * math.sin(ang_)
                w = rng.uniform(18, 50) * (1 + d / 8000)
                L = min(rng.uniform(1.8, 4.0) * Rp, z - th - 60)
                yaw = math.atan2(-fx, -fy)
                ax_, ay_ = math.cos(yaw), -math.sin(yaw)
                hue_f = PAL[wchoice([('cyan', 30), ('magenta', 25), ('violet', 20), ('blue', 10), ('green', 8), ('pink', 7)])]
                self.lightfall(fx, fy, z - th, w, L, ax_, ay_, hue_f, rng.uniform(0.8, 1.2))
            self.mega_tops.append((x, y, z + Rp * 0.9))
            n += 1
        log(f'platforms: {n}')


    def build_all(self):
        mats = dict(fac=make_cyber_material('sky3d_landmark_armour', legacy=True),
                    roof=make_cyber_material('sky3d_landmark_decks', roof=True, legacy=True),
                    struct=make_cyber_material('sky3d_struct_armour', legacy=True),
                    neon=mat_neon(), screen=mat_screen(), trail=mat_trail(), holo=mat_holo(),
                    sigil=mat_sigil(), fall=mat_lightfall(), ribbon=mat_ribbon(), crystal=mat_crystal())
        mats['screens'] = [mats['screen']] + [mat_screen_image(im) for im in SCREEN_IMGS]
        self.fac.build(mats['fac'])
        self.roof.build(mats['roof'])
        mats['cyber'] = make_cyber_material('sky3d_cyber_armour')
        mats['cyber_roof'] = make_cyber_material('sky3d_cyber_decks', roof=True)
        self.cyber.build(mats['cyber'])
        self.cyber_roof.build(mats['cyber_roof'])
        log('cyber block forms:', self.cyber_counts)
        self.struct.build(mats['struct'])
        self.neon.build(mats['neon'])
        self.screen.build(mats['screens'])
        self.trail.build(mats['trail'])
        self.holo.build(mats['holo'])
        for acc, key in ((self.sigil, 'sigil'), (self.fall, 'fall'), (self.ribbon, 'ribbon'), (self.crystal, 'crystal')):
            ob = acc.build(mats[key])
            if ob:
                ob.visible_shadow = False
        return mats


# ---------------------------------------------------------------- environment pieces
def make_ground(mat):
    acc = Acc('ground')
    N = 96
    acc.poly([(60000 * math.cos(2 * math.pi * i / N), 60000 * math.sin(2 * math.pi * i / N), 0.0) for i in range(N)],
             [(0, 0)] * N, (0, 0, 0, 1))
    acc.build(mat)


def make_water(mat):
    acc = Acc('water')
    a0, a1 = BAY[0] - 1.0, BAY[1] + 1.0
    steps = 24
    r0, r1 = BAY_R
    for i in range(steps):
        t0 = a0 + (a1 - a0) * i / steps
        t1 = a0 + (a1 - a0) * (i + 1) / steps
        p0, p1 = polar(r0, t0), polar(r0, t1)
        q0, q1 = polar(r1, t0), polar(r1, t1)
        acc.poly([(*p0, 0.35), (*q0, 0.35), (*q1, 0.35), (*p1, 0.35)], [(0, 0)] * 4, (0, 0, 0, 1))
    acc.build(mat)


def make_clouds(zc, mat):
    acc = Acc(f'clouds_{int(zc)}')
    N = 64
    acc.poly([(48000 * math.cos(2 * math.pi * i / N), 48000 * math.sin(2 * math.pi * i / N), zc) for i in reversed(range(N))],
             [(0, 0)] * N, (0, 0, 0, 1))
    ob = acc.build(mat)
    ob.visible_shadow = False


def mat_halo(stops=((0.0, (0.95, 0.14, 0.10)), (0.35, (0.72, 0.06, 0.08)), (1.0, (0.38, 0.03, 0.06))), strength=None, power=2.2, name='sky3d_halo'):
    """a soft radial glow on a unit disc facing the camera (the moon's halo; the black holes' gas halos)"""
    m, t = new_mat(name)
    x, y, z = t.sep(t.obj_co())
    r = t.vmath('LENGTH', t.comb(x, y, 0.0))
    fall = t.math('POWER', t.maprange(r, 0.0, 1.0, 1.0, 0.0), power)
    col = t.ramp(t.maprange(r, 0.0, 1.0, 0.0, 1.0), list(stops))
    em = t.emission(col, t.math('MULTIPLY', fall, E_HALO if strength is None else strength))
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    plug(mix.inputs[0], fall)
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(em, mix.inputs[2])
    t.out(mix.outputs[0])
    return m


def moon_disc():
    """v7b the visible moon disc (az, el, r in deg): MOON_REF carried through the title gate's card (gate_point), so the moon peeks
    out behind the crest wherever GATE puts the gate and at its scale; MOON_DISC when the gate's metadata is missing"""
    meta = gate_meta()
    if not meta or SIGN_STYLE != 'gate':
        return MOON_DISC['az'], MOON_DISC['el'], MOON_DISC['r']
    q = gate_point(MOON_REF['u'], MOON_REF['v'], meta) - Vector((0.0, 0.0, CAM_H))
    r_m = MOON_REF['r'] * gate_scale(meta)
    return (math.degrees(math.atan2(q.x, q.y)), math.degrees(math.atan2(q.z, math.hypot(q.x, q.y))),
            math.degrees(math.atan2(r_m, q.length)))


def make_moon(mat):
    daz, dele, dr = moon_disc()
    az, el = daz * D2R, dele * D2R                                          # v7: the disc + halo stand where the reference's moon is
    log(f'moon disc: az {daz:.2f} el {dele:.2f} r {dr:.2f} deg ({MOON_STYLE})')
    md = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    cam = Vector((0.0, 0.0, CAM_H))
    R = MOON_D * math.tan(dr * D2R)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=R, location=tuple(cam + md * MOON_D))
    ob = bpy.context.active_object
    ob.name = 'moon'
    ob.data.materials.append(mat)
    ob.data.shade_smooth()
    ob.visible_shadow = False
    # the halo: a disc behind the moon facing the camera; a unit circle scaled so its Object coords run 0..1
    hd = 1.06 * MOON_D
    hr = R * 5.0
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1.0, fill_type='NGON', location=tuple(cam + md * hd))
    hob = bpy.context.active_object
    hob.name = 'moon_halo'
    hob.scale = (hr, hr, hr)
    hob.rotation_euler = (-md).to_track_quat('Z', 'Y').to_euler()
    hob.data.materials.append(mat_halo() if MOON_STYLE != 'reference' else
                              mat_halo(((0.0, (0.45, 0.30, 0.95)), (0.35, (0.30, 0.16, 0.80)), (1.0, (0.15, 0.06, 0.45))), strength=E_HALO * 0.14, name='sky3d_halo_ref'))
    hob.visible_shadow = False
    # the moonlight: a sun lamp along the moon's direction, soft (the disc is 11 deg across)
    sun = bpy.data.lights.new('moonlight', 'SUN')
    sun.energy = 0.03                                                # v4: W units (the sky's indigo fill does the lighting; the moon adds a red rim)
    sun.color = (1.0, 0.24, 0.16)
    sun.angle = 6.0 * D2R
    so = bpy.data.objects.new('moonlight', sun)
    bpy.context.scene.collection.objects.link(so)
    d = Vector((0.0, -math.cos(MOON_EL * D2R), -math.sin(MOON_EL * D2R)))
    so.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def make_sign(struct_mat, neon_mat):
    """the title gantry: two round masts, top/bottom trusses, a dark chamfered plate, neon border,
    'TOWER OF DOOM' (red) 'II' (ember) and 'CYBERCITY' (cold cyan) as extruded emissive letters"""
    zc = CAM_H + SIGN_D * math.tan(SIGN_EL * D2R)
    y = SIGN_D
    plate_w, plate_h, plate_t = 760.0, 170.0, 6.0
    acc = Acc('sign_struct')
    # plate (chamfered)
    ch = 18.0
    pts = [(-plate_w / 2 + ch, zc - plate_h / 2), (plate_w / 2 - ch, zc - plate_h / 2), (plate_w / 2, zc - plate_h / 2 + ch),
           (plate_w / 2, zc + plate_h / 2 - ch), (plate_w / 2 - ch, zc + plate_h / 2), (-plate_w / 2 + ch, zc + plate_h / 2),
           (-plate_w / 2, zc + plate_h / 2 - ch), (-plate_w / 2, zc - plate_h / 2 + ch)]
    # a vertical prism: build it as a polygon in XZ extruded along Y (front face toward the camera at y - t)
    front = [(x, y, z) for x, z in pts]
    back = [(x, y + plate_t, z) for x, z in pts]
    acc.poly(list(reversed(front)), [(0, 0)] * len(pts), (0, 0, 0, 1))
    acc.poly(back, [(0, 0)] * len(pts), (0, 0, 0, 1))
    for i in range(len(pts)):
        a, b = front[i], front[(i + 1) % len(pts)]
        c, d = back[(i + 1) % len(pts)], back[i]
        acc.poly([a, b, c, d], [(0, 0)] * 4, (0, 0, 0, 1))
    # masts
    mast_x = plate_w / 2 + 34
    mast_top = zc + plate_h / 2 + 46
    for sx in (-1, 1):
        acc.prism(fp_ellipse(sx * mast_x, y + plate_t / 2, 7.5, 7.5, 12, 0), 0.0, mast_top, (0, 0, 0, 1))
        for zr in np.arange(60, mast_top - 10, 60):                             # segment rings
            acc.prism(fp_ellipse(sx * mast_x, y + plate_t / 2, 9.0, 9.0, 12, 0), zr, zr + 4, (0, 0, 0, 1))
    # trusses: chords + X braces, above and below the plate
    for zt in (zc + plate_h / 2 + 12, zc - plate_h / 2 - 12):
        for dz in (0.0, 14.0):
            acc.box(0, y + plate_t / 2, zt + dz - 1.5, 2 * mast_x, 4, 3, 0, (0, 0, 0, 1))
        nb = int(2 * mast_x / 36)
        for i in range(nb):
            x0 = -mast_x + i * (2 * mast_x / nb)
            x1 = x0 + 2 * mast_x / nb
            for (xa, za, xb, zb) in ((x0, zt, x1, zt + 14), (x0, zt + 14, x1, zt)):
                L = math.hypot(xb - xa, zb - za)
                mx, mz = (xa + xb) / 2, (za + zb) / 2
                angb = math.atan2(zb - za, xb - xa)
                # a thin brace as a rotated box in the XZ plane
                c, s = math.cos(angb), math.sin(angb)
                hw, ht = L / 2, 1.2
                q = [(mx - hw * c + ht * s, mz - hw * s - ht * c), (mx + hw * c + ht * s, mz + hw * s - ht * c),
                     (mx + hw * c - ht * s, mz + hw * s + ht * c), (mx - hw * c - ht * s, mz - hw * s + ht * c)]
                fr = [(px, y + plate_t / 2 - 1.2, pz) for px, pz in q]
                bk = [(px, y + plate_t / 2 + 1.2, pz) for px, pz in q]
                acc.poly(list(reversed(fr)), [(0, 0)] * 4, (0, 0, 0, 1))
                acc.poly(bk, [(0, 0)] * 4, (0, 0, 0, 1))
                for k in range(4):
                    acc.poly([fr[k], fr[(k + 1) % 4], bk[(k + 1) % 4], bk[k]], [(0, 0)] * 4, (0, 0, 0, 1))
    acc.build(struct_mat)
    # neon borders on the plate (v2: a crimson outer + a cyan inner) + mast beacons + side light bars
    nacc = Acc('sign_neon')

    def border(poly, colr, alpha, ht):
        for i in range(len(poly)):
            (xa, za), (xb, zb) = poly[i], poly[(i + 1) % len(poly)]
            L = math.hypot(xb - xa, zb - za)
            mx, mz = (xa + xb) / 2, (za + zb) / 2
            angb = math.atan2(zb - za, xb - xa)
            c, s = math.cos(angb), math.sin(angb)
            hw = L / 2 - 0.6
            q = [(mx - hw * c + ht * s, mz - hw * s - ht * c), (mx + hw * c + ht * s, mz + hw * s - ht * c),
                 (mx + hw * c - ht * s, mz + hw * s + ht * c), (mx - hw * c - ht * s, mz - hw * s + ht * c)]
            fr = [(px, y - 1.6, pz) for px, pz in q]
            bk = [(px, y + 0.4, pz) for px, pz in q]
            nacc.poly(list(reversed(fr)), [(0, 0)] * 4, (*colr, alpha))
            for k in range(4):
                nacc.poly([fr[k], fr[(k + 1) % 4], bk[(k + 1) % 4], bk[k]], [(0, 0)] * 4, (*colr, alpha))
    border(pts, PAL['crimson'], 0.6, 1.1)
    ins_w, ins_h = 1 - 2 * 11.0 / plate_w, 1 - 2 * 11.0 / plate_h
    border([(px * ins_w, zc + (pz - zc) * ins_h) for px, pz in pts], PAL['cyan'], 0.32, 0.7)
    for sx in (-1, 1):
        nacc.box(sx * mast_x, y + plate_t / 2, mast_top, 6, 6, 6, 0, (*PAL['beacon'], 1.0))
        nacc.box(sx * (mast_x - 14), y - 1.0, zc - plate_h * 0.3, 2.4, 2.4, plate_h * 0.6, 0, (*PAL['ember'], 0.5))
    nacc.build(neon_mat)
    # the letters
    fonts = {}

    def text(body, font_path, cap_h, zline, x_center, col, strength, spacing=1.0, depth=0.55):
        cu = bpy.data.curves.new('sign_text', 'FONT')
        cu.body = body
        try:
            if font_path not in fonts:
                fonts[font_path] = bpy.data.fonts.load(font_path)
            cu.font = fonts[font_path]
        except Exception as e:
            log('font load failed', font_path, e)
        cu.size = 10.0
        cu.extrude = depth
        cu.space_character = spacing
        cu.align_x = 'CENTER'
        ob = bpy.data.objects.new('sign_text', cu)
        bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        bpy.data.objects.remove(ob, do_unlink=True)
        # measure the cap height on a capital (the body's tallest glyph box)
        co = np.array([v.co[:] for v in me.vertices])
        ymin, ymax = co[:, 1].min(), co[:, 1].max()
        xmin, xmax = co[:, 0].min(), co[:, 0].max()
        s = cap_h / max(0.01, (ymax - ymin))
        mo = bpy.data.objects.new('sign_' + body.replace(' ', '_'), me)
        bpy.context.scene.collection.objects.link(mo)
        mo.scale = (s, s, s)
        mo.rotation_euler = (math.pi / 2, 0, 0)                 # text plane XY -> XZ, its face toward -Y (the camera)
        mo.location = (x_center - (xmin + xmax) / 2 * s, y - depth * s - 0.8, zline - ymin * s)
        face = mat_sign_face(col, strength)
        side = mat_sign_face(col, strength * 0.18)                # the tube's body: the same colour, dim
        me.materials.append(face)
        me.materials.append(side)
        for p in me.polygons:
            p.material_index = 0 if abs(p.normal.z) > 0.9 else 1   # (mesh-local: the glyph face is +-Z before the rotation)
        return mo, (xmax - xmin) * s
    # v2: crimson title, GOLD numeral, "FALLEN CYBERCITY" (the map's name, docs/160) in Agency FB letter by letter so two of
    # FALLEN's tubes can flicker (broken neon), backlight panels behind both lines (the plate catching the neon)
    impact = r'C:\Windows\Fonts\impact.ttf'
    agency = r'C:\Windows\Fonts\AGENCYB.TTF'
    cap_main = SIGN_D * math.tan(3.5 * D2R)
    z_main = zc + plate_h * 0.04
    _, w_title = text('TOWER OF DOOM', impact, cap_main, z_main, -cap_main * 0.62, (1.0, 0.02, 0.03), E_SIGN * 0.55)
    x_ii = w_title / 2 - cap_main * 0.62 + cap_main * 0.78
    text('II', impact, cap_main * 1.02, z_main, x_ii, PAL['gold'], E_SIGN * 0.6)
    sub_cap = cap_main * 0.40
    z_sub = zc - plate_h * 0.36
    word = 'FALLEN CYBERCITY'
    dim = {1: 0.72, 4: 0.88}                                                     # v4h: the A and the E of FALLEN flicker a little (0.28 read as a MISSING letter)
    letters, widths = [], []
    for i, ch in enumerate(word):
        if ch == ' ':
            letters.append(None)
            widths.append(sub_cap * 0.55)
            continue
        mo, w = text(ch, agency, sub_cap, z_sub, 0.0, PAL['cyan'], E_SIGN * 0.5 * dim.get(i, 1.0), depth=0.35)
        letters.append(mo)
        widths.append(w)
    gap = sub_cap * 0.16
    total = sum(widths) + gap * (len(word) - 1)
    cur = -total / 2
    for mo, w in zip(letters, widths):
        if mo is not None:
            mo.location.x += cur + w / 2
        cur += w + gap
    pacc = Acc('sign_backlight')
    x0, x1 = -cap_main * 0.62 - w_title / 2 - 30, x_ii + cap_main * 0.9 + 30
    for (xa, xb, za, zb, colr, e) in ((x0, x1, z_main - cap_main * 0.25, z_main + cap_main * 1.25, PAL['crimson'], 0.35),
                                       (-total / 2 - 25, total / 2 + 25, z_sub - sub_cap * 0.3, z_sub + sub_cap * 1.3, PAL['cyan'], 0.22)):
        pacc.poly([(xa, y - 0.25, za), (xb, y - 0.25, za), (xb, y - 0.25, zb), (xa, y - 0.25, zb)], [(0, 0)] * 4, (*colr, e))
    pacc.build(mat_translucent('sky3d_sign_backlight', 1.0))


def gate_frame():
    """v7 the title gate's card frame: (C = the text box centre in the world, the card's right and up axes, d = the unit view
    direction to C). The card is perpendicular to d, so a camera aimed at the title sees the reference face-on (the jump-pad
    reveal); make_title_gate sets the scale (GATE['w_deg'] over the reference's width)."""
    e = GATE['box_el'] * D2R
    d = Vector((0.0, math.cos(e), math.sin(e)))
    up = Vector((0.0, -math.sin(e), math.cos(e)))
    right = Vector((1.0, 0.0, 0.0))
    C = Vector((0.0, 0.0, CAM_H)) + d * GATE['D']
    return C, right, up, d


_GATE_META = []


def gate_meta():
    """v7b the gate texture's metadata (<GATE_TEX>.json, written by cut_title_gate.py): canvas size, the reference's size and
    padding, the text box centre in canvas px. {} when the texture is missing (the gantry fallback)."""
    if not _GATE_META:
        base = os.path.splitext(GATE_TEX)[0]
        meta = {}
        if os.path.exists(GATE_TEX) and os.path.exists(base + '.json'):
            with open(base + '.json') as f:
                meta = json.load(f)
        _GATE_META.append(meta)
    return _GATE_META[0]


def gate_scale(meta):
    """metres per canvas pixel: GATE['w_deg'] spans the REFERENCE's width at the box centre's distance"""
    return 2.0 * GATE['D'] * math.tan(GATE['w_deg'] / 2 * D2R) / meta.get('ref_width_px', meta.get('size', (1448, 0))[0])


def gate_point(u, v, meta):
    """the world point of canvas pixel (u, v) (0,0 = the texture's top-left) on the gate's card"""
    C, right, up, _ = gate_frame()
    size = meta.get('size', (1448, 1086))
    u0, v0 = meta.get('box_px', (GATE['box_uv'][0] * size[0], GATE['box_uv'][1] * size[1]))
    s = gate_scale(meta)
    return C + right * ((u - u0) * s) + up * ((v0 - v) * s)


SIGN_AOV = 'sign'                                                           # v7b: the view-layer AOV the card writes; finish_sky.py reads it as <raw>.sign.exr


def mat_title_gate(img, glow=None):
    """v7 the gate card: the texture is DISPLAY-referred (the reference's own pixels, Non-Color), decoded with the previews' 2.2,
    divided by the finish's --sat about Rec.709 luminance, emitted at GATE['white'] per display 1.0 over transparency by alpha.
    The glow texture (the neon's halo into the sky, cut_title_gate.py) is ADDED light on the same decode: it never occludes.
    v7b: the painting's neon (max channel neon_lo -> neon_hi, smoothstep) is pushed GATE['neon'] x higher, the glow is emitted at
    GATE['glow'], and the 'sign' AOV (alpha + mask_glow x the glow's max channel) marks the card for finish_sky.py's own knee."""
    m, t = new_mat('sky3d_title_gate')

    def decode(im):
        tex = t.node('ShaderNodeTexImage', extension='CLIP', interpolation='Linear')
        tex.image = im
        plug(tex.inputs['Vector'], t.uv())
        gam = t.node('ShaderNodeGamma')
        t.t.links.new(tex.outputs['Color'], gam.inputs['Color'])
        plug(gam.inputs['Gamma'], 2.2)
        lum = t.vmath('DOT_PRODUCT', gam.outputs['Color'], (0.2126, 0.7152, 0.0722))
        return tex, t.mix_rgb(1.0 / GATE['sat'], t.comb(lum, lum, lum), gam.outputs['Color'])   # Y + (c - Y) / sat

    def maxc(tex):
        r, g, b = t.sep_col(tex.outputs['Color'])
        return t.math('MAXIMUM', t.math('MAXIMUM', r, g), b)
    tex, col = decode(img)
    ramp = t.node('ShaderNodeMapRange', clamp=True, interpolation_type='SMOOTHSTEP')
    plug(ramp.inputs['Value'], maxc(tex))
    plug(ramp.inputs['From Min'], GATE['neon_lo'])
    plug(ramp.inputs['From Max'], GATE['neon_hi'])
    boost = t.math('MULTIPLY_ADD', ramp.outputs['Result'], GATE['neon'] - 1.0, 1.0)             # 1 .. neon
    em = t.emission(col, t.math('MULTIPLY', boost, GATE['white']))
    tr = t.node('ShaderNodeBsdfTransparent')
    mix = t.node('ShaderNodeMixShader')
    t.t.links.new(tex.outputs['Alpha'], mix.inputs[0])
    t.t.links.new(tr.outputs[0], mix.inputs[1])
    t.t.links.new(em, mix.inputs[2])
    aov = t.node('ShaderNodeOutputAOV', aov_name=SIGN_AOV)
    if glow is None:
        t.t.links.new(tex.outputs['Alpha'], aov.inputs['Value'])
        t.out(mix.outputs[0])
        return m
    gtex, gcol = decode(glow)
    plug(aov.inputs['Value'], t.math('MULTIPLY_ADD', maxc(gtex), GATE['mask_glow'], tex.outputs['Alpha'], clamp=True))
    add = t.node('ShaderNodeAddShader')
    t.t.links.new(mix.outputs[0], add.inputs[0])
    t.t.links.new(t.emission(gcol, GATE['glow']), add.inputs[1])
    t.out(add.outputs[0])
    return m


def make_title_gate():
    """v7 THE TITLE GATE — the user's reference painting on one card (GATE_TEX + its _glow and .json; docs/166 §9)"""
    if not os.path.exists(GATE_TEX):
        log(f'title gate: no texture at {GATE_TEX} — falling back to the gantry')
        return False
    img = bpy.data.images.load(GATE_TEX)
    img.colorspace_settings.name = 'Non-Color'
    img.alpha_mode = 'STRAIGHT'
    tw, th = img.size
    base = os.path.splitext(GATE_TEX)[0]
    meta = dict(gate_meta())
    meta.setdefault('size', (tw, th))                                       # w_deg spans the REFERENCE's width; the canvas is padded round it
    u0, v0 = meta.get('box_px', (GATE['box_uv'][0] * tw, GATE['box_uv'][1] * th))
    glow = None
    if os.path.exists(base + '_glow.png'):
        glow = bpy.data.images.load(base + '_glow.png')
        glow.colorspace_settings.name = 'Non-Color'
    s = gate_scale(meta)

    def P(u, v):
        return gate_point(u, v, meta)
    verts = [P(0, th), P(tw, th), P(tw, 0), P(0, 0)]                       # bottom-left, bottom-right, top-right, top-left
    me = bpy.data.meshes.new('title_gate')
    me.from_pydata([tuple(v) for v in verts], [], [(0, 1, 2, 3)])
    uvl = me.uv_layers.new(name='UVMap')
    for li, (uu, vv) in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uvl.data[li].uv = (uu, vv)
    me.materials.append(mat_title_gate(img, glow))
    ob = bpy.data.objects.new('title_gate', me)
    bpy.context.scene.collection.objects.link(ob)
    ob.visible_shadow = False                                               # a 1 km card must not shade the moonlit core in front of it
    if not GATE['lights']:                                                  # v7b: 20x v7's neon would light the core, the fog and the streets pink
        ob.visible_diffuse = False                                          #      and scatter noise through the fog: the camera sees it, the wet
        ob.visible_transmission = False                                     #      glossy ground still mirrors it, nothing else does
        ob.visible_volume_scatter = False
        me.materials[0].cycles.emission_sampling = 'NONE'
    vl = bpy.context.view_layer
    if SIGN_AOV not in [a.name for a in vl.aovs]:                           # v7b: the card's mask for finish_sky.py (setup_sign_mask writes it out)
        a = vl.aovs.add()
        a.name = SIGN_AOV
        a.type = 'VALUE'
    if BLEND:
        img.pack()
        if glow is not None:
            glow.pack()

    def angles(p):
        q = p - Vector((0.0, 0.0, CAM_H))
        return math.degrees(math.atan2(q.x, q.y)), math.degrees(math.atan2(q.z, math.hypot(q.x, q.y)))
    pad_t, pad_x = meta.get('pad_top', 0), meta.get('pad_x', 0)
    rw, rh = meta.get('ref_size', (tw, th))
    tl, br = angles(P(pad_x, pad_t)), angles(P(pad_x + rw, pad_t + rh))
    log(f'title gate: {tw}x{th} texture ({"with" if glow else "no"} glow), {s:.3f} m/px, box centre az 0 el {GATE["box_el"]:.2f}; '
        f'the reference frame spans az {tl[0]:.1f}..{br[0]:.1f}, el {br[1]:.1f}..{tl[1]:.1f}; painted spire tip to el '
        f'{angles(P(u0 - 2.5, pad_t - 104))[1]:.1f}')
    return True


def make_searchlights(city, n=4):
    cands = [c for c in (city.mega_tops or city.tall) if abs(az_of(c[0], c[1])) > 34 and math.hypot(c[0], c[1]) < 9000]
    rng.shuffle(cands)
    for i, (x, y, h) in enumerate(cands[:n]):
        lt = bpy.data.lights.new(f'search_{i}', 'SPOT')
        lt.energy = 1.2e9
        lt.color = (1.0, 0.75, 0.6) if i % 2 else (1.0, 0.35, 0.3)
        lt.spot_size = 2.4 * D2R
        lt.spot_blend = 0.15
        lt.shadow_soft_size = 3.0
        ob = bpy.data.objects.new(f'search_{i}', lt)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = (x, y, h + 4)
        tilt = rng.uniform(40, 62) * D2R
        yaw = rng.uniform(0, 2 * math.pi)
        d = Vector((math.sin(tilt) * math.cos(yaw), math.sin(tilt) * math.sin(yaw), math.cos(tilt)))
        ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()   # a spot emits along its -Z: aim it UP along d
        if not city.host_visible(x, y, h):
            bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.lights.remove(lt)


# ---------------------------------------------------------------- v2 geometry helpers
def tube(acc, p0, p1, r0, r1, col, n=8, cap=False):
    """a frustum along p0 -> p1 (radius r0 at p0, r1 at p1): cables, beams, bolts, spikes, jets, rims"""
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    L = axis.length
    if L < 1e-3:
        return
    axis /= L
    ref = Vector((0.0, 0.0, 1.0)) if abs(axis.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    u = axis.cross(ref).normalized()
    v = axis.cross(u)
    ring0 = [p0 + (u * math.cos(2 * math.pi * i / n) + v * math.sin(2 * math.pi * i / n)) * r0 for i in range(n)]
    ring1 = [p1 + (u * math.cos(2 * math.pi * i / n) + v * math.sin(2 * math.pi * i / n)) * r1 for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        acc.poly([tuple(ring0[i]), tuple(ring0[j]), tuple(ring1[j]), tuple(ring1[i])], [(0, 0), (1, 0), (1, 1), (0, 1)], col)
    if cap:
        acc.poly([tuple(p) for p in reversed(ring0)], [(0, 0)] * n, col)
        acc.poly([tuple(p) for p in ring1], [(0, 0)] * n, col)


def soft_fan(acc, P, d, perp, L, w0, w1, a0, col, n=12, power=1.5):
    """v5e a soft-edged translucent FAN (a comet tail, a jet): a strip of quads along unit `d` from P, half-width w0 -> w1, alpha a0
    on the axis fading to 0 at the edges and along the length (per-corner alpha), in the plane of d and `perp` (choose perp in the
    view plane so the fan faces the camera). A tube cone read as solid grey paper."""
    P, d, perp = Vector(P), Vector(d), Vector(perp)
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        c0, c1 = P + d * (L * t0), P + d * (L * t1)
        h0, h1 = w0 + (w1 - w0) * t0, w0 + (w1 - w0) * t1
        al0, al1 = a0 * (1 - t0) ** power, a0 * (1 - t1) ** power
        for sgn in (1.0, -1.0):
            pts = [tuple(c0), tuple(c0 + perp * (sgn * h0)), tuple(c1 + perp * (sgn * h1)), tuple(c1)]
            acc.poly(pts, [(0, 0), (1, 0), (1, 1), (0, 1)], (*col, al0), cols=[(*col, al0), (*col, 0.0), (*col, 0.0), (*col, al1)])


def annulus(acc, r0, r1, a0, a1, n, col, z=0.0, nr=1):
    """a flat ring (or arc) in the local XY plane; UV = (radial fraction, angle fraction)"""
    for i in range(n):
        t0, t1 = a0 + (a1 - a0) * i / n, a0 + (a1 - a0) * (i + 1) / n
        for k in range(nr):
            ra, rb = r0 + (r1 - r0) * k / nr, r0 + (r1 - r0) * (k + 1) / nr
            fa, fb = k / nr, (k + 1) / nr
            acc.poly([(ra * math.cos(t0), ra * math.sin(t0), z), (rb * math.cos(t0), rb * math.sin(t0), z),
                      (rb * math.cos(t1), rb * math.sin(t1), z), (ra * math.cos(t1), ra * math.sin(t1), z)],
                     [(fa, i / n), (fb, i / n), (fb, (i + 1) / n), (fa, (i + 1) / n)], col)


def slab(acc, c, along, up, L, H, T, col):
    """a thin box: centre c, length L along unit `along`, height H along unit `up`, thickness T across"""
    c, along, up = Vector(c), Vector(along), Vector(up)
    side = along.cross(up).normalized()
    corners = []
    for sa in (-1, 1):
        for su in (-1, 1):
            for ss in (-1, 1):
                corners.append(c + along * (sa * L / 2) + up * (su * H / 2) + side * (ss * T / 2))

    def ix(a, u, s):
        return a * 4 + u * 2 + s
    faces = [(ix(0, 0, 0), ix(0, 1, 0), ix(1, 1, 0), ix(1, 0, 0)), (ix(0, 0, 1), ix(1, 0, 1), ix(1, 1, 1), ix(0, 1, 1)),
             (ix(0, 0, 0), ix(1, 0, 0), ix(1, 0, 1), ix(0, 0, 1)), (ix(0, 1, 0), ix(0, 1, 1), ix(1, 1, 1), ix(1, 1, 0)),
             (ix(0, 0, 0), ix(0, 0, 1), ix(0, 1, 1), ix(0, 1, 0)), (ix(1, 0, 0), ix(1, 1, 0), ix(1, 1, 1), ix(1, 0, 1))]
    for f in faces:
        acc.poly([tuple(corners[i]) for i in f], [(0, 0), (1, 0), (1, 1), (0, 1)], col)


def body_frame(az, el, D=BODY_D):
    """centre, view direction, image-right and image-up for a sky body at (az, el) from the camera"""
    dh = Vector((math.sin(az * D2R) * math.cos(el * D2R), math.cos(az * D2R) * math.cos(el * D2R), math.sin(el * D2R)))
    P = Vector((0.0, 0.0, CAM_H)) + dh * D
    up = (Vector((0.0, 0.0, 1.0)) - dh * dh.z).normalized()
    right = dh.cross(up).normalized()
    return P, dh, right, up


def place(ob, P, xa, ya, za):
    ob.matrix_world = Matrix(((xa.x, ya.x, za.x, P.x), (xa.y, ya.y, za.y, P.y), (xa.z, ya.z, za.z, P.z), (0.0, 0.0, 0.0, 1.0)))


def unit_disc(name, P, normal, radius, mat):
    """a unit circle scaled to `radius`, facing `normal` (object coords run 0..1 in the halo material)"""
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1.0, fill_type='NGON', location=tuple(P))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (radius, radius, radius)
    ob.rotation_euler = Vector(normal).to_track_quat('Z', 'Y').to_euler()
    ob.data.materials.append(mat)
    ob.visible_shadow = False
    return ob


def crosses_lane(p0, p1, n=24):
    """would a segment show in front of the sign / the moon (inside the lane above 3.5 deg)?"""
    for i in range(n + 1):
        q = p0.lerp(p1, i / n)
        d = math.hypot(q.x, q.y)
        if d > 1 and abs(az_of(q.x, q.y)) < LANE_HALF and math.degrees(math.atan2(q.z - CAM_H, d)) > 3.5:
            return True
    return False


# ---------------------------------------------------------------- v2 THE SKY BODIES
def rock_mesh(name, seed_):
    """a lumpy icosphere (unit radius) for the asteroids; six of them are shared by all the instances"""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(0.0, 0.0, 0.0))
    ob = bpy.context.active_object
    ob.name = name
    rs = random.Random(seed_)
    a = [rs.uniform(1.5, 3.5) for _ in range(3)]
    ph = [rs.uniform(0, 6.28) for _ in range(3)]
    sx, sy, sz = rs.uniform(0.7, 1.3), rs.uniform(0.7, 1.3), rs.uniform(0.6, 1.1)
    for v in ob.data.vertices:
        x, y, z = v.co
        f = 1.0 + 0.18 * math.sin(a[0] * x + ph[0]) * math.cos(a[1] * y + ph[1]) + 0.14 * math.sin(a[2] * z + ph[2]) * math.cos(a[0] * x)
        v.co = (x * f * sx, y * f * sy, z * f * sz)
    ob.data.shade_smooth()
    ob.hide_render = True
    ob.hide_viewport = True
    return ob


def scatter_rocks(name, bases, mat, places):
    """instances of the shared rock meshes: places = [(location Vector, radius, yaw, pitch), ...]
    v7c: every static rock is RETIRED (the belt, the drifting rocks, the black holes' debris): real asteroid models fly through the
    map's sky now. The callers still compute `places` (their random draws), so nothing after them moves; only the objects go."""
    if not ROCKS:
        RETIRED_ROCKS[0] += len(places)
        return
    for i, (loc, rad, yaw, pitch) in enumerate(places):
        base = bases[i % len(bases)]
        ob = bpy.data.objects.new(f'{name}_{i}', base.data)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = tuple(loc)
        ob.scale = (rad, rad, rad)
        ob.rotation_euler = (pitch, 0.0, yaw)
        ob.visible_shadow = False
        if len(ob.data.materials) == 0:
            ob.data.materials.append(mat)


def make_bodies():
    """v5 the sky bodies as geometry at BODY_D (docs/166 §7): gas giants (rings, moons), cracked planets, moons and moonlets, TWO
    black holes (oblique spiral disc, shadow, photon ring, the LENSED far side over and under the shadow, polar jets, tidal
    streams, a debris field), spiral galaxies, a comet, an asteroid BELT and drifting rocks. Distant small worlds are dimmed
    (bd['dim']) so the sky reads deep. Frames: image-right / image-up / view direction per body."""
    bases = [rock_mesh(f'rock_base_{k}', SEED * 7 + k) for k in range(6)]
    for b in bases:
        b.data.materials.clear()
    drift_mat = mat_asteroid('sky3d_rock_drift')
    for bd in BODIES:
        P, dh, right, up = body_frame(bd['az'], bd['el'])
        R = BODY_D * math.tan(bd['r'] * D2R)
        bd['R'] = R
        kind = bd['kind']
        dim = bd.get('dim', 1.0)
        if kind == 'galaxy' and not on('galaxies'):
            continue
        if kind in ('gas', 'cracked', 'moon'):
            tilt = bd.get('tilt', rng.uniform(-0.3, 0.3))
            pole = (up * math.cos(tilt) - dh * math.sin(tilt)).normalized()
            xa = right
            ya = pole.cross(xa).normalized()
            xa = ya.cross(pole).normalized()
            bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=R, location=(0.0, 0.0, 0.0))
            ob = bpy.context.active_object
            ob.name = f'{kind}_{bd["name"]}'
            ob.data.shade_smooth()
            ob.data.materials.append(mat_planet(bd) if kind == 'gas' else (mat_cracked(bd) if kind == 'cracked' else mat_moonrock(bd)))
            ob.visible_shadow = False
            place(ob, P, xa, ya, pole)
            if bd.get('ring'):
                inner, outer, _, _ = bd['ring']
                acc = Acc('ring_' + bd['name'])
                annulus(acc, R * inner, R * outer, 0.0, 2 * math.pi, 160, (0, 0, 0, 1), 0.0, 6)
                rob = acc.build(mat_ring(bd))
                rob.visible_shadow = False
                place(rob, P, xa, ya, pole)
            for j, (mx, my, mr) in enumerate(bd.get('moons', [])):
                mb = dict(name=f'{bd["name"]}_m{j}', R=R * mr, dim=dim)
                bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=R * mr, location=tuple(P + right * (mx * R) + up * (my * R)))
                mo = bpy.context.active_object
                mo.name = 'moon_' + mb['name']
                mo.data.shade_smooth()
                mo.data.materials.append(mat_moonrock(mb))
                mo.visible_shadow = False
            log(f'  {kind} {bd["name"]}: az {bd["az"]:.0f} el {bd["el"]:.0f} r {bd["r"]:.1f} deg (R {R:.0f} m, dim {dim:.2f})')
        elif kind == 'hole':
            nrm = (-dh * math.cos(bd['tilt']) + up * math.sin(bd['tilt'])).normalized()      # oblique: tilted from face-on toward image-up
            xa = right
            ya = nrm.cross(xa).normalized()
            xa = ya.cross(nrm).normalized()
            acc = Acc('disc_' + bd['name'])
            annulus(acc, R * 1.12, R * bd['disc_out'], 0.0, 2 * math.pi, 200, (0, 0, 0, 1), 0.0, 12)
            dob = acc.build(mat_disc(bd))
            dob.visible_shadow = False
            place(dob, P, xa, ya, nrm)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=R, location=tuple(P))
            sob = bpy.context.active_object
            sob.name = 'hole_' + bd['name']
            sob.data.shade_smooth()
            sob.data.materials.append(mat_plain('sky3d_black_' + bd['name'], (0.0, 0.0, 0.0), 0.0))
            sob.visible_shadow = False
            xc, yc, nc_ = right, up, -dh
            pacc = Acc('photon_' + bd['name'])
            annulus(pacc, R * 1.0, R * 1.045, 0.0, 2 * math.pi, 96, (0, 0, 0, 1), 0.0, 1)                                    # v4f: a THIN photon ring
            pob = pacc.build(mat_plain('sky3d_photon_' + bd['name'], bd['col_hot'], E_HOLE * 0.9 * dim))
            pob.visible_shadow = False
            place(pob, P, xc, yc, nc_)
            lacc = Acc('lens_' + bd['name'])                                                                     # v5: the lensed far side over and under the shadow
            annulus(lacc, R * 1.05, R * 1.9, 0.0, 2 * math.pi, 128, (0, 0, 0, 1), 0.0, 8)
            lob = lacc.build(mat_lensarc(bd))
            lob.visible_shadow = False
            place(lob, P, xc, yc, nc_)
            unit_disc('halo_' + bd['name'], P + dh * (R * 1.5), -dh, R * 5.0,
                      mat_halo(((0.0, bd['col_mid']), (0.35, bd['col_far']), (0.7, bd['col_edge']), (1.0, (0.02, 0.005, 0.03))), 0.12 * dim, 2.2, 'sky3d_gashalo_' + bd['name']))
            jacc = Acc('jets_' + bd['name'])                                                                     # v5: polar jets along the disc's normal
            jcol = bd.get('jet', (0.45, 0.65, 1.0))
            jperp = nrm.cross(dh).normalized()
            for sgn in (1.0, -1.0):
                for (wf, al) in ((1.0, 0.045), (0.45, 0.07), (0.15, 0.13)):                                      # v5f: nested — a thread with a faint sheath (v5g: fainter)
                    soft_fan(jacc, P + nrm * (sgn * R * 1.0), nrm * sgn, jperp, R * 3.5, R * 0.08 * wf, R * 0.5 * wf, al, jcol, 12, 1.8)
            job = jacc.build(mat_translucent('sky3d_jet_' + bd['name'], E_JET * dim))
            job.visible_shadow = False
            stacc = Acc('streams_' + bd['name'])                                                                 # v5: tidal streams spiralling in
            for k in range(bd.get('streams', 8)):
                phi0 = rng.uniform(0, 2 * math.pi)
                sweep = rng.uniform(2.5, 4.5)
                zoff = R * rng.uniform(-0.12, 0.12)                                                             # v5b: close to the plane (they read as hula hoops at 0.3)
                scol = bd['col_mid'] if k % 2 == 0 else bd['col_far']
                pts = []
                for j in range(30):
                    tt = j / 29
                    rho = R * (bd['disc_out'] * 0.95 - (bd['disc_out'] * 0.95 - 1.3) * tt)
                    phi = phi0 + tt * sweep
                    pts.append(P + xa * (rho * math.cos(phi)) + ya * (rho * math.sin(phi)) + nrm * (zoff * (1 - tt)))
                for j in range(29):
                    tt = j / 29
                    tube(stacc, pts[j], pts[j + 1], R * 0.03 * (1 - 0.5 * tt), R * 0.03 * (1 - 0.5 * (tt + 0.03)), (*scol, 0.35 * (0.35 + 0.65 * tt)), 6)
            stob = stacc.build(mat_translucent('sky3d_stream_' + bd['name'], E_HOLE * 0.45 * dim))
            stob.visible_shadow = False
            rmat = mat_asteroid('sky3d_rock_' + bd['name'], P)                                                   # the debris field, lit by the disc
            places = []
            for i in range(bd.get('debris', 0)):
                phi = rng.uniform(0, 2 * math.pi)
                rho = R * rng.uniform(1.15, 3.8)
                zoff = R * rng.gauss(0, 0.35)
                loc = P + xa * (rho * math.cos(phi)) + ya * (rho * math.sin(phi)) + nrm * zoff
                rad = R * (0.014 + 0.05 * rng.random() ** 2.2)
                if rng.random() < 0.06:
                    rad *= 2.2
                places.append((loc, rad, rng.uniform(0, 6.28), rng.uniform(0, 3.14)))
            for _ in range(4):                                                                                    # v5: clumps along short arcs
                phi0, rho0 = rng.uniform(0, 2 * math.pi), R * rng.uniform(1.6, 3.2)
                for j in range(12):
                    phi = phi0 + j * 0.05 + rng.gauss(0, 0.02)
                    rho = rho0 * (1 + rng.gauss(0, 0.04))
                    loc = P + xa * (rho * math.cos(phi)) + ya * (rho * math.sin(phi)) + nrm * (R * rng.gauss(0, 0.08))
                    places.append((loc, R * (0.012 + 0.03 * rng.random() ** 2), rng.uniform(0, 6.28), rng.uniform(0, 3.14)))
            scatter_rocks('debris_' + bd['name'], bases, rmat, places)
            log(f'  black hole {bd["name"]}: az {bd["az"]:.0f} el {bd["el"]:.0f} r {bd["r"]:.1f} deg, disc to {bd["disc_out"]:.1f} R, {len(places)} rocks{"" if ROCKS else " (retired)"}, jets + {bd.get("streams", 6)} streams')
        elif kind == 'galaxy':
            nrm = (-dh * math.cos(bd['tilt']) + up * math.sin(bd['tilt'])).normalized()
            xa = right
            ya = nrm.cross(xa).normalized()
            xa = ya.cross(nrm).normalized()
            acc = Acc('galaxy_' + bd['name'])
            annulus(acc, R * 0.02, R, 0.0, 2 * math.pi, 96, (0, 0, 0, 1), 0.0, 12)
            gob = acc.build(mat_galaxy(bd))
            gob.visible_shadow = False
            place(gob, P, xa, ya, nrm)
            log(f'  galaxy {bd["name"]}: az {bd["az"]:.0f} el {bd["el"]:.0f} r {bd["r"]:.1f} deg')
        elif kind == 'comet':                                                                                     # v5: a comet — a hot nucleus, a coma, an ion tail and a curved dust tail away from the moon
            M = Vector(moon_dir())
            tdir = (M * -1.0) - dh * dh.dot(M * -1.0)
            if tdir.length < 1e-3:
                tdir = up.copy()
            tdir.normalize()
            Ltail = BODY_D * math.tan(bd['tail'] * D2R)
            col = bd['col']
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=R, location=tuple(P))
            nob = bpy.context.active_object
            nob.name = 'comet_' + bd['name']
            nob.data.shade_smooth()
            nob.data.materials.append(mat_plain('sky3d_comet_core_' + bd['name'], (1.0, 1.0, 1.0), 2.5))
            nob.visible_shadow = False
            unit_disc('coma_' + bd['name'], P + dh * (R * 2.0), -dh, R * 5.0,
                      mat_halo(((0.0, (1.0, 1.0, 1.0)), (0.3, col), (1.0, (0.02, 0.04, 0.08))), 1.2, 2.0, 'sky3d_coma_' + bd['name']))
            tacc = Acc('tail_' + bd['name'])
            perp = tdir.cross(dh).normalized()
            for (wf, al) in ((1.0, 0.16), (0.45, 0.22), (0.16, 0.40)):                                           # v5f: nested fans = a bright thin core in a soft sheath
                soft_fan(tacc, P, tdir, perp, Ltail, R * 0.6 * wf, R * 2.6 * wf, al, col, 14, 1.7)                     # the ion tail
            ddir = (tdir * 0.94 + perp * 0.34).normalized()
            for (wf, al) in ((1.0, 0.10), (0.5, 0.14), (0.2, 0.22)):
                soft_fan(tacc, P, ddir, ddir.cross(dh).normalized(), Ltail * 0.7, R * 0.8 * wf, R * 4.5 * wf, al, (1.0, 0.88, 0.72), 14, 1.5)   # the dust tail
            tob = tacc.build(mat_translucent('sky3d_tail_' + bd['name'], 1.0))
            tob.visible_shadow = False
            log(f'  comet {bd["name"]}: az {bd["az"]:.0f} el {bd["el"]:.0f}, tail {bd["tail"]:.0f} deg')
    if on('asteroids'):
        # drifting rocks, well above the horizon and out of the moon's lane
        places = []
        for i in range(ASTEROIDS_DRIFT):
            az = rng.uniform(-180, 180)
            if abs(az) < LANE_HALF + 6:
                az += 90
            el = rng.uniform(22, 80)
            P, dh, right, up = body_frame(az, el, BODY_D * rng.uniform(0.75, 1.1))
            rad = rng.uniform(60, 320) * (1.6 if rng.random() < 0.08 else 1.0)
            places.append((P, rad, rng.uniform(0, 6.28), rng.uniform(0, 3.14)))
        scatter_rocks('drift', bases, drift_mat, places)
        log(f'  {len(places)} drifting asteroids{"" if ROCKS else " (retired)"}')
        # v5 THE BELT: a band of rocks arcing across the right sky
        places = []
        B = ASTEROID_BELT
        for i in range(B['n']):
            tt = rng.random()
            az = B['az0'] + (B['az1'] - B['az0']) * tt + rng.gauss(0, 1.2)
            el = B['el0'] + B['bulge'] * math.sin(math.pi * tt) + rng.gauss(0, B['spread'])
            az = (az + 180.0) % 360.0 - 180.0
            if abs(az) < LANE_HALF + 6 and el < 30:
                continue
            P, dh, right, up = body_frame(az, el, BODY_D * rng.uniform(0.7, 1.15))
            rad = rng.uniform(90, 380) * (2.0 if rng.random() < 0.05 else 1.0)
            places.append((P, rad, rng.uniform(0, 6.28), rng.uniform(0, 3.14)))
        scatter_rocks('belt', bases, drift_mat, places)
        log(f'  belt: {len(places)} rocks{"" if ROCKS else " (retired)"}')


# ---------------------------------------------------------------- v2 THE ORIGIN + THE STORM
def make_origin(city):
    """"one super, super tall building ... thunderclouds around it ... where all the evil started": a 4 km black spire on an
    island in the harbour — eight tapering tiers of dark glass, crimson veins on every edge, lit collars, eight buttress fins,
    a spiked crown round a red EYE that lights the storm; the RING OF THUNDERCLOUDS is make_storm."""
    x, y = polar(ORIGIN['r'], ORIGIN['az'])
    h, r = ORIGIN['h'], ORIGIN['r']
    a = amin(r)
    nc = PAL['crimson']
    city.excl.append((x, y, 900.0))
    isl = Acc('origin_island')
    pts = [(px + rng.uniform(-40, 40), py + rng.uniform(-40, 40)) for px, py in fp_ellipse(x, y, 720, 560, 28, 0.4)]
    isl.prism(pts, -5.0, 22.0, (0, 0, 0, 1), cap=True)
    isl.prism(fp_scale(pts, 0.6), 22.0, 48.0, (0, 0, 0, 1), cap=True)
    isl.build(mat_rock())
    base = 520.0
    fp = fp_ellipse(x, y, base / 2, base / 2, 8, 0.3)
    col = (0.77, 0.30, pal_of('crimson'), 0.40)                                  # v4h: seed, PANEL style (crimson panels — all the evil glows), crimson, lit fraction
    z = 20.0
    fr = [0.16, 0.34, 0.5, 0.64, 0.76, 0.86, 0.94, 1.0]
    for i, f in enumerate(fr):
        z1 = h * f
        city.fac.prism(fp, z, z1, col, cap=True, cap_acc=city.roof)
        for (px, py) in fp:
            city.neon.prism(fp_rect(px, py, a * 2.2, a * 2.2, 0.3), z + 6, z1 - 4, (*nc, 1.0))
        for k in range(8):
            (ax, ay), (bx, by) = fp[k], fp[(k + 1) % 8]
            city.neon.strip(ax, ay, bx, by, z1 - a, a * 1.8, a * 1.8, (*nc, 1.0))
        if i < len(fr) - 1:
            fp = fp_scale(fp, 0.86)
        z = z1
    zf0, zf1 = h * 0.26, h * 0.40                                                # buttress fins
    rr0 = base / 2 * 0.86 ** 2 * 0.95
    for k in range(8):
        angk = 0.3 + k * math.pi / 4 + math.pi / 8
        dx, dy = math.cos(angk), math.sin(angk)
        fin = [(x + dx * rr0 - dy * 9, y + dy * rr0 + dx * 9), (x + dx * (rr0 + 240) - dy * 9, y + dy * (rr0 + 240) + dx * 9),
               (x + dx * (rr0 + 240) + dy * 9, y + dy * (rr0 + 240) - dx * 9), (x + dx * rr0 + dy * 9, y + dy * rr0 - dx * 9)]
        city.struct.prism(fin, zf0, zf1, (0, 0, 0, 1), cap=True)
        tube(city.neon, (x + dx * (rr0 + 240), y + dy * (rr0 + 240), zf1), (x + dx * rr0, y + dy * rr0, zf1 + 90), a * 0.9, a * 0.9, (*nc, 0.9), 6)
    for k in range(8):                                                           # the crown: eight spikes leaning outward
        angk = 0.3 + k * math.pi / 4 + math.pi / 8
        root = (x + math.cos(angk) * 60, y + math.sin(angk) * 60, h - 40)
        tip = (x + math.cos(angk) * 150, y + math.sin(angk) * 150, h + 280)
        tube(city.struct, root, tip, 15.0, 2.5, (0, 0, 0, 1), 6)
        city.neon.box(tip[0], tip[1], tip[2], a * 2.6, a * 2.6, a * 2.6, 0, (*nc, 1.0))
    if on('ringsx'):                                                             # v4: three giant neon rings (the references' central spires)
        for (zf, rf, colk, al) in ((0.50, 2.1, 'crimson', 1.0), (0.66, 1.75, 'magenta', 0.9), (0.83, 1.45, 'crimson', 1.0)):
            tier_r = base / 2 * 0.86 ** int(zf * 7)
            neon_ring(city.neon, x, y, h * zf, tier_r * rf, max(3.0, a * 1.6), (*PAL[colk], al), 72, rng.uniform(-0.06, 0.06))
    bacc = Acc('origin_beam')                                                    # v4: a beam from the crown into the sky (reference 2)
    for (f0, f1, r0, r1, al) in ((0.0, 0.25, 30.0, 40.0, 0.55), (0.25, 0.6, 40.0, 55.0, 0.30), (0.6, 1.0, 55.0, 80.0, 0.12)):
        tube(bacc, (x, y, h + 200 + 4200 * f0), (x, y, h + 200 + 4200 * f1), r0, r1, (1.0, 0.18, 0.22, al), 12)
    tube(bacc, (x, y, h + 200), (x, y, h + 3200), 9.0, 6.0, (1.0, 0.75, 0.75, 0.9), 8)
    bob = bacc.build(mat_translucent('sky3d_origin_beam', 0.7))
    bob.visible_shadow = False
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=105.0, location=(x, y, h + 120.0))
    eye = bpy.context.active_object
    eye.name = 'origin_eye'
    eye.data.shade_smooth()
    eye.data.materials.append(mat_plain('sky3d_eye', (1.0, 0.04, 0.03), E_BEACON * 0.6))
    eye.visible_shadow = False
    lt = bpy.data.lights.new('origin_light', 'POINT')
    lt.energy = 9.0e5
    lt.color = (1.0, 0.06, 0.05)
    lt.shadow_soft_size = 120.0
    lo = bpy.data.objects.new('origin_light', lt)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (x, y, h + 120.0)
    city.mega_tops.append((x, y, h))
    if on('storm'):
        make_storm(x, y)
    log(f'THE ORIGIN at az {ORIGIN["az"]:.0f} r {r:.0f}: {h:.0f} m (its top {math.degrees(math.atan2(h - CAM_H, r)):.1f} deg up)')


def make_storm(x, y):
    """the ring of thunderclouds round THE ORIGIN: one closed cylinder volume (mat_storm zeroes the density near the shaft and
    lumps the rest), four coloured lights inside it, three branching lightning bolts (emissive tubes = lights for the volume)"""
    r0, r1 = ORIGIN['storm_r']
    z0, z1 = ORIGIN['storm_z']
    zm = (z0 + z1) / 2
    acc = Acc('origin_storm')
    fp = fp_ellipse(0.0, 0.0, r1 * 1.02, r1 * 1.02, 40, 0)
    acc.prism(fp, z0 - zm, z1 - zm, (0, 0, 0, 1), cap=True)
    acc.poly([(px, py, z0 - zm) for px, py in reversed(fp)], [(0, 0)] * len(fp), (0, 0, 0, 1))
    ob = acc.build(mat_storm())
    ob.location = (x, y, zm)
    ob.visible_shadow = False
    for k, (angk, colr, e) in enumerate(((0.9, (0.55, 0.30, 1.0), 1.5e7), (2.6, (1.0, 0.10, 0.12), 1.0e7), (4.4, (0.60, 0.35, 1.0), 1.4e7), (5.6, (1.0, 0.20, 0.30), 0.9e7), (1.8, (0.95, 0.20, 0.85), 1.2e7), (3.6, (0.45, 0.20, 1.0), 1.2e7))):
        rr = (r0 + r1) / 2
        lt = bpy.data.lights.new(f'storm_light_{k}', 'POINT')
        lt.energy = e
        lt.color = colr
        lt.shadow_soft_size = 200.0
        lo = bpy.data.objects.new(f'storm_light_{k}', lt)
        bpy.context.scene.collection.objects.link(lo)
        lo.location = (x + rr * math.cos(angk), y + rr * math.sin(angk), zm + rng.uniform(-200, 200))
    bacc = Acc('origin_bolts')
    a = amin(math.hypot(x, y))
    for k in range(6):                                                           # v4h: six bolts
        angk = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(r0 * 1.1, r1 * 0.8)
        p = Vector((x + rr * math.cos(angk), y + rr * math.sin(angk), rng.uniform(z0 + 200, z1 - 300)))
        if k < 4:
            target = Vector((x + 200 * math.cos(angk), y + 200 * math.sin(angk), rng.uniform(600, 1400)))     # cloud -> the shaft
        else:
            target = Vector((x + rr * 0.9 * math.cos(angk), y + rr * 0.9 * math.sin(angk), 30.0))            # cloud -> the island
        n_seg = 14
        pts = [p]
        for i in range(1, n_seg + 1):
            q = p.lerp(target, i / n_seg)
            if i < n_seg:
                q += Vector((rng.gauss(0, 60), rng.gauss(0, 60), rng.gauss(0, 40)))
            pts.append(q)
        for i in range(n_seg):
            tube(bacc, pts[i], pts[i + 1], a * 1.0, a * 0.9, (0.90, 0.85, 1.0, 1.0), 6)
            if rng.random() < 0.35:
                b = pts[i] + Vector((rng.gauss(0, 150), rng.gauss(0, 150), rng.uniform(-220, -40)))
                tube(bacc, pts[i], b, a * 0.6, a * 0.2, (0.85, 0.75, 1.0, 0.7), 5)
    bob = bacc.build(mat_translucent('sky3d_bolt', E_BOLT))
    bob.visible_shadow = False


# ---------------------------------------------------------------- v2 THE TETHER, BEAMS, LASERS
def make_tether(city):
    """the orbital tether: an anchor megatower, a tapered cyan cable to TETHER.top_h (it converges on the zenith), a climber, a
    wheel station at station_el with lit rims and windows"""
    az, d, ah, top = TETHER['az'], TETHER['d'], TETHER['anchor_h'], TETHER['top_h']
    x, y = polar(d, az)
    city.mega(x, y, ah, 'spire', 'cyan')
    cable = Acc('tether_cable')
    for (z0, z1, r0, r1) in ((ah + 60.0, 8000.0, 12.0, 16.0), (8000.0, 30000.0, 16.0, 26.0), (30000.0, top, 26.0, 230.0)):
        tube(cable, (x, y, z0), (x, y, z1), r0, r1, (*PAL['cyan'], 0.45), 8)
    cable.build(mat_neon())
    city.neon.box(x, y, 21000.0, 60.0, 60.0, 140.0, 0, (*PAL['white'], 1.0))
    zs = CAM_H + d * math.tan(TETHER['station_el'] * D2R)
    bpy.ops.mesh.primitive_torus_add(major_radius=520.0, minor_radius=75.0, major_segments=64, minor_segments=16, location=(x, y, zs))
    tor = bpy.context.active_object
    tor.name = 'tether_station'
    tor.data.shade_smooth()
    tor.data.materials.append(mat_struct())
    bpy.ops.mesh.primitive_cylinder_add(radius=130.0, depth=340.0, vertices=24, location=(x, y, zs))
    hub = bpy.context.active_object
    hub.name = 'tether_hub'
    hub.data.materials.append(mat_struct())
    for k in range(4):
        city.struct.box(x, y, zs - 20.0, 1040.0, 40.0, 40.0, k * math.pi / 4, (0, 0, 0, 1))
    for dz in (85.0, -85.0):
        bpy.ops.mesh.primitive_torus_add(major_radius=520.0, minor_radius=12.0, major_segments=64, minor_segments=8, location=(x, y, zs + dz))
        rim = bpy.context.active_object
        rim.name = f'tether_rim_{dz:+.0f}'
        rim.data.materials.append(mat_plain(f'sky3d_rim{dz:+.0f}', PAL['cyan'], E_NEON * 0.5))
    for k in range(24):
        angk = 2 * math.pi * k / 24
        city.neon.box(x + 596 * math.cos(angk), y + 596 * math.sin(angk), zs - 15.0, 30.0, 30.0, 30.0, 0, (*(PAL['white'] if k % 3 else PAL['cyan']), 0.8))
    log(f'tether: anchor az {az:.0f} d {d:.0f} h {ah:.0f}; station at {zs:.0f} m (el {TETHER["station_el"]:.0f} deg)')


def make_beams(city, n=7):
    """searchlight CONES as translucent geometry (the spot lamps only light the fog near their base; above the fog a beam needs
    a body): from supertall crowns, tilted outward, 3..6 km long, widening and fading along their length"""
    cands = [c for c in city.mega_tops if abs(az_of(c[0], c[1])) > LANE_HALF + 6 and math.hypot(c[0], c[1]) < 9000]
    rng.shuffle(cands)
    acc = Acc('beams')
    features = []
    for i, (x, y, h) in enumerate(cands[:n]):
        start = (len(acc.v), len(acc.f))
        tilt = rng.uniform(3, 14) * D2R                                          # v4: near-vertical pillars of light (reference 2)
        yaw = math.atan2(y, x) + rng.uniform(-1.0, 1.0)                          # outward: never across the moon
        dv = Vector((math.sin(tilt) * math.cos(yaw), math.sin(tilt) * math.sin(yaw), math.cos(tilt)))
        L = rng.uniform(3000, 6000)
        col = [(1.0, 0.96, 0.9), (0.4, 0.9, 1.0), (1.0, 0.25, 0.2), (1.0, 0.5, 0.9)][i % 4]
        p0 = Vector((x, y, h + 10.0))
        for (f0, f1, al) in ((0.0, 0.3, 0.7), (0.3, 0.65, 0.4), (0.65, 1.0, 0.15)):
            tube(acc, p0 + dv * (L * f0), p0 + dv * (L * f1), 8.0 + 40.0 * f0, 8.0 + 40.0 * f1, (*col, al), 10)
        features.append(feature_record(acc, start, i, city.host_visible(x, y, h)))
    prune_features(acc, 'searchlight_beams', features, city.composition['secondary'])
    ob = acc.build(mat_translucent('sky3d_beam', E_BEAM))
    if ob:
        ob.visible_shadow = False


def make_lasers(city, n=4):
    """laser bars between supertall crowns (the old sky's three laser lines), never across the lane"""
    tops = [c for c in city.mega_tops if math.hypot(c[0], c[1]) < 12000 and abs(az_of(c[0], c[1])) > LANE_HALF + 6]
    rng.shuffle(tops)
    acc = Acc('lasers')
    features = []
    k = 0
    for i in range(len(tops) // 2):
        if k >= n:
            break
        (x0, y0, h0), (x1, y1, h1) = tops[2 * i], tops[2 * i + 1]
        p0, p1 = Vector((x0, y0, h0 + 30.0)), Vector((x1, y1, h1 + 30.0))
        if crosses_lane(p0, p1) or (p1 - p0).length < 1500:
            continue
        col = [PAL['red'], PAL['cyan'], PAL['magenta'], PAL['gold']][k % 4]
        rad = amin(min(math.hypot(x0, y0), math.hypot(x1, y1))) * 0.6
        start = (len(acc.v), len(acc.f))
        tube(acc, p0, p1, rad, rad, (*col, 0.85), 6)
        features.append(feature_record(acc, start, k, city.host_visible(x0, y0, h0) and city.host_visible(x1, y1, h1)))
        k += 1
    prune_features(acc, 'crown_lasers', features, city.composition['secondary'])
    ob = acc.build(mat_translucent('sky3d_laser', E_LASER))
    if ob:
        ob.visible_shadow = False


# ---------------------------------------------------------------- v2 SHIPS
def make_airships(mats):
    """dirigibles over the mid city: a dark glossy ellipsoid hull, three neon rims following the hull, a cross of fins, a lit
    gondola, a holo billboard on the flank toward the tower, running lights"""
    for az, d, z, L, hue, adhue in SHIP_DEFS:
        x, y = polar(d, az)
        yaw = (az + 90.0) * D2R
        axis = Vector((math.sin(yaw), math.cos(yaw), 0.0))                       # tangential: broadside to the camera
        up = Vector((0.0, 0.0, 1.0))
        side = axis.cross(up).normalized()
        if side.dot(Vector((-x, -y, 0.0))) < 0:
            side = -side                                                         # `side` points toward the camera
        R = L / 6.5
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0, location=(x, y, z))
        ob = bpy.context.active_object
        ob.name = f'airship_{int(az)}'
        ob.data.shade_smooth()
        ob.scale = (L / 2, R, R)
        ob.rotation_euler = (0.0, 0.0, math.atan2(axis.y, axis.x))
        ob.data.materials.append(mat_hull())
        a = amin(d)
        nc = PAL[hue]
        nacc, sacc, scr = Acc(f'airship_neon_{int(az)}'), Acc(f'airship_struct_{int(az)}'), Acc(f'airship_screen_{int(az)}')
        c = Vector((x, y, z))

        def hull_r(fx):
            return R * math.sqrt(max(0.0, 1.0 - fx * fx))
        for (sy, sz) in ((0.0, 1.0), (0.87, -0.5), (-0.87, -0.5)):
            prev = None
            for i in range(25):
                fx = -0.92 + 1.84 * i / 24
                rr = hull_r(fx) * 1.01
                p = c + axis * (fx * L / 2) + side * (sy * rr) + up * (sz * rr)
                if prev is not None:
                    tube(nacc, prev, p, a * 0.8, a * 0.8, (*nc, 0.75), 5)
                prev = p
        tail = c - axis * (L * 0.42)
        for fin_dir in (up, -up, side, -side):
            slab(sacc, tail + fin_dir * (R * 0.55), axis, fin_dir, L * 0.14, R * 0.7, 2.5, (0, 0, 0, 1))
            tube(nacc, tail + fin_dir * (R * 0.9) + axis * (L * 0.04), tail + fin_dir * (R * 0.9) - axis * (L * 0.05), a * 0.7, a * 0.7, (*nc, 0.8), 5)
        gon = c - up * (R * 1.05) + axis * (L * 0.08)
        slab(sacc, gon, axis, up, L * 0.18, R * 0.22, R * 0.28, (0, 0, 0, 1))
        tube(nacc, gon + side * (R * 0.15) - axis * (L * 0.08), gon + side * (R * 0.15) + axis * (L * 0.08), a * 0.6, a * 0.6, (*PAL['warm'], 0.7), 4)
        sw, sh = L * 0.5, R * 0.9
        sc_ = c + side * (R * 0.96)
        pts = [tuple(sc_ - axis * (sw / 2) - up * (sh / 2)), tuple(sc_ + axis * (sw / 2) - up * (sh / 2)), tuple(sc_ + axis * (sw / 2) + up * (sh / 2)), tuple(sc_ - axis * (sw / 2) + up * (sh / 2))]
        scr.poly(pts, [(0, 0), (sw, 0), (sw, sh), (0, sh)], (rng.random(), sw, sh, 1.3), mi=screen_mi(sw, sh))
        nose = c + axis * (L * 0.5)
        for p, colk in ((nose + side * 1.0, 'tail'), (tail - axis * (L * 0.07), 'green'), (c + up * (R * 1.02), 'white')):
            nacc.box(p.x, p.y, p.z, a * 1.6, a * 1.6, a * 1.6, 0, (*PAL[colk], 1.0))
        nacc.build(mats['neon'])
        sacc.build(mats['struct'])
        scr.build(mats['screens'])
        log(f'  airship az {az:.0f} d {d:.0f} z {z:.0f}: {L:.0f} m ({math.degrees(math.atan2(z - CAM_H, d)):.0f} deg up)')


def make_starships(mats):
    """v5 CAPITAL SHIPS (user: "I can barely tell it's a spaceship ... way more detail ... bigger"): a battlecruiser read from
    below — keel, main hull, dorsal deck and spine, a bridge tower with a lit command deck and sensor masts, two engine nacelles
    and a stern wall with seven hot nozzles and long plumes, swept wings and a dorsal fin with neon edges, rows of lit windows
    on three decks a side and along the belly, a glowing hangar bay below and a lit slot on the flank toward the tower, running
    lights, a bow searchlight; twelve fighters, two escort formations. Hull: mat_hull (dark glossy steel — the nebula reflects)."""
    hull = mat_shiphull()
    fleet = []
    for si, (az, d, z, L, head) in enumerate(STARSHIPS):
        x, y = polar(d, az)
        yaw = (az + 90.0 + head) * D2R
        axis = Vector((math.sin(yaw), math.cos(yaw), 0.0))                       # the bow along +axis
        up = Vector((0.0, 0.0, 1.0))
        side = up.cross(axis).normalized()                                        # right-handed (axis, side, up): CCW footprints stay CCW in the world
        cam = 1.0 if side.dot(Vector((-x, -y, 0.0))) > 0 else -1.0               # which flank faces the tower
        W, H = L * 0.26, L * 0.07
        c = Vector((x, y, z))
        a = amin(math.hypot(d, z - CAM_H))
        nc = PAL[['cyan', 'orange', 'magenta', 'green', 'violet'][si % 5]]
        pcol = (1.0, 0.55, 0.20) if si % 2 == 0 else (0.50, 0.90, 1.0)         # orange or cyan drives
        wcol = (0.70, 0.85, 1.0)
        yaw_w = math.atan2(axis.y, axis.x)
        hacc, sacc, nacc, pl = Acc(f'ship_hull_{si}'), Acc(f'ship_struct_{si}'), Acc(f'ship_neon_{si}'), Acc(f'ship_plume_{si}')

        def P3(fx, fs, fz):
            return c + axis * (fx * L / 2) + side * (fs * W / 2) + up * (fz * H)

        def pt(fx, fs):
            p = P3(fx, fs, 0.0)
            return (p.x, p.y)

        def block(acc, prof, fz0, fz1, col=(0, 0, 0, 1)):
            """a hull block from a CCW (fx, fs) profile between two heights (in H), with its belly face"""
            fp = [pt(fx, fs) for fx, fs in prof]
            acc.prism(fp, c.z + fz0 * H, c.z + fz1 * H, col, cap=True)
            acc.poly([(px, py, c.z + fz0 * H) for px, py in reversed(fp)], [(0, 0)] * len(fp), col)
            return fp

        def hw(fx, half):
            xs = [p[0] for p in half]
            ws = [abs(p[1]) for p in half]
            return float(np.interp(fx, xs, ws))

        def nozzle(e, er):
            nacc.poly([tuple(e + side * (er * math.cos(2 * math.pi * i / 16)) + up * (er * math.sin(2 * math.pi * i / 16))) for i in range(16)], [(0, 0)] * 16, (*pcol, 1.4))
            tube(sacc, e + axis * (L * 0.02), e, er * 1.18, er * 1.18, (0, 0, 0, 1), 12)
            vdir = (e - Vector((0.0, 0.0, CAM_H))).normalized()                                    # v5h: the plume is a nested soft fan facing the camera (tube cones read as tan planks)
            pperp = (axis * -1.0).cross(vdir)
            if pperp.length < 1e-3:
                pperp = up.copy()
            pperp.normalize()
            for (wf, al) in ((1.0, 0.10), (0.55, 0.16), (0.22, 0.32)):
                soft_fan(pl, e, axis * -1.0, pperp, L * 0.5, er * 1.05 * wf, er * 2.6 * wf, al, pcol, 10, 1.5)

        def lamp(p, colk, s=2.0, alpha=1.0):
            nacc.box(p.x, p.y, p.z, a * s, a * s, a * s, 0, (*PAL[colk], alpha))
        main = [(-1.0, -1.0), (-0.2, -0.95), (0.55, -0.5), (1.0, -0.08), (1.0, 0.08), (0.55, 0.5), (-0.2, 0.95), (-1.0, 1.0)]
        main_half = [(-1.0, 1.0), (-0.2, 0.95), (0.55, 0.5), (1.0, 0.08)]
        dorsal = [(-0.9, -0.5), (0.3, -0.42), (0.65, -0.12), (0.65, 0.12), (0.3, 0.42), (-0.9, 0.5)]
        dorsal_half = [(-0.9, 0.5), (0.3, 0.42), (0.65, 0.12)]
        block(hacc, [(-0.95, -0.55), (0.75, -0.2), (0.75, 0.2), (-0.95, 0.55)], -0.9, -0.2)        # the keel
        block(hacc, [(0.7, -0.2), (1.0, -0.05), (1.0, 0.05), (0.7, 0.2)], -0.6, -0.2)                 # the bow keel
        block(hacc, main, -0.2, 0.6)                                                                 # the main hull
        block(hacc, dorsal, 0.6, 1.1)                                                                # the dorsal deck
        block(hacc, [(-0.85, -0.14), (0.5, -0.08), (0.5, 0.08), (-0.85, 0.14)], 1.1, 1.45)           # the spine
        block(hacc, [(-0.62, -0.26), (-0.36, -0.22), (-0.36, 0.22), (-0.62, 0.26)], 1.45, 2.1)       # the bridge tower
        block(hacc, [(-0.6, -0.34), (-0.4, -0.3), (-0.4, 0.3), (-0.6, 0.34)], 2.1, 2.5)              # the command deck
        for fs in (-0.2, 0.2):                                                                        # sensor masts
            block(sacc, [(-0.52, fs - 0.03), (-0.46, fs - 0.03), (-0.46, fs + 0.03), (-0.52, fs + 0.03)], 2.5, 3.2)
            lamp(P3(-0.49, fs, 3.2), 'beacon')
        block(hacc, [(-1.0, -1.08), (-0.82, -1.08), (-0.82, 1.08), (-1.0, 1.08)], -0.7, 1.3)          # the stern wall
        for fs in (-0.75, -0.375, 0.0, 0.375, 0.75):                                                  # five main nozzles
            nozzle(P3(-1.0, fs, 0.3) - axis * 2.0, H * 0.30)
        for sgn in (-1.0, 1.0):                                                                       # the nacelles
            lo, hi = sorted((sgn * 1.04, sgn * 1.40))
            lo_b, hi_b = lo + (0.12 if sgn < 0 else 0.0), hi - (0.12 if sgn > 0 else 0.0)
            block(hacc, [(-0.95, lo), (0.35, lo_b), (0.35, hi_b), (-0.95, hi)], -0.35, 0.45)
            nozzle(P3(-0.95, sgn * 1.22, 0.05) - axis * 2.0, H * 0.34)
            tube(nacc, P3(-0.95, sgn * 1.40, 0.45), P3(0.35, sgn * (1.40 - 0.12), 0.45), a * 0.8, a * 0.8, (*nc, 0.8), 5)   # the nacelle's top outer edge
            tube(nacc, P3(-0.95, sgn * 1.40, -0.35), P3(0.35, sgn * (1.40 - 0.12), -0.35), a * 0.7, a * 0.7, (*nc, 0.5), 5)
            lamp(P3(0.35, sgn * 1.34, 0.1), 'green' if sgn > 0 else 'tail')
            slab(hacc, P3(-0.55, sgn * 1.95, 0.0), axis, side, L * 0.26, W * 0.55, H * 0.08, (0, 0, 0, 1))                    # the wing (v5e: the dark hull, not struct's sheen)
            tube(nacc, P3(-0.29, sgn * 1.40, 0.0), P3(-0.29, sgn * 2.5, 0.0), a * 0.8, a * 0.8, (*nc, 0.9), 5)               # its leading edge
            tube(nacc, P3(-0.81, sgn * 1.40, 0.0), P3(-0.81, sgn * 2.5, 0.0), a * 0.7, a * 0.7, (*nc, 0.5), 5)
            lamp(P3(-0.55, sgn * 2.5, 0.0), 'green' if sgn > 0 else 'tail', 2.2)
        slab(hacc, P3(-0.78, 0.0, 1.9), axis, up, L * 0.18, H * 1.4, H * 0.08, (0, 0, 0, 1))                                 # the dorsal fin
        tube(nacc, P3(-0.96, 0.0, 2.6), P3(-0.60, 0.0, 2.6), a * 0.8, a * 0.8, (*nc, 0.9), 5)
        for i in range(len(main) - 1):                                                                # chine neon along the deck edge
            tube(nacc, P3(*main[i], 0.6), P3(*main[i + 1], 0.6), a * 0.8, a * 0.8, (*nc, 0.75), 5)
        for i in range(len(dorsal) - 1):
            tube(nacc, P3(*dorsal[i], 1.1), P3(*dorsal[i + 1], 1.1), a * 0.7, a * 0.7, (*nc, 0.5), 5)
        nwin = int(L / 11)

        def window_row(half, fz, n, sgn, skip=0.3):
            for i in range(n):
                fx = -0.96 + 1.9 * (i + 0.5) / n
                if fx > half[-1][0] or rng.random() < skip:
                    continue
                p = P3(fx, sgn * (hw(fx, half) + 0.02), fz)
                nacc.box(p.x, p.y, p.z, max(0.6, a * 0.9), max(0.6, a * 0.9), max(0.6, a * 0.9), yaw_w, (*wcol, 0.7))
        for sgn in (-1.0, 1.0):
            window_row(main_half, 0.05, nwin, sgn)
            window_row(main_half, 0.35, nwin, sgn, 0.4)
            window_row(dorsal_half, 0.85, int(nwin * 0.8), sgn)
        nb = int(nwin * 0.8)
        for fs in (-0.32, 0.32):                                                                      # belly rows (we look UP at the ship)
            for i in range(nb):
                fx = -0.9 + 1.6 * (i + 0.5) / nb
                if rng.random() < 0.35:
                    continue
                p = P3(fx, fs, -0.92)
                nacc.box(p.x, p.y, p.z, max(0.6, a * 0.9), max(0.6, a * 0.9), max(0.6, a * 0.9), yaw_w, (*wcol, 0.6))
        for sgn in (-1.0, 1.0):                                                                       # the command deck's window band
            tube(nacc, P3(-0.6, sgn * 0.35, 2.35), P3(-0.4, sgn * 0.31, 2.35), a * 0.6, a * 0.6, (*wcol, 0.9), 4)
        tube(nacc, P3(-0.4, -0.31, 2.35), P3(-0.4, 0.31, 2.35), a * 0.6, a * 0.6, (*wcol, 0.9), 4)
        hb = [P3(-0.15, -0.12, -0.905), P3(0.05, -0.12, -0.905), P3(0.05, 0.12, -0.905), P3(-0.15, 0.12, -0.905)]           # the hangar bay: a small cool slot (v5g: the warm plank read as beige)
        nacc.poly([tuple(p) for p in reversed(hb)], [(0, 0)] * 4, (0.7, 0.85, 1.0, 0.6))
        lamp(P3(1.0, 0.0, 0.2), 'white', 2.4)
        lamp(P3(-0.9, 0.0, 1.45), 'white', 2.0)
        hacc.build(hull)
        sacc.build(mats['struct'])
        nacc.build(mats['neon'])
        pob = pl.build(mat_translucent(f'sky3d_plume_{si}', 0.9))
        pob.visible_shadow = False
        fleet.append((c, axis, side, L, W, H))
        dist = math.hypot(d, z - CAM_H)
        log(f'  starship {si} az {az:.0f} d {d:.0f} z {z:.0f}: {L:.0f} m = {math.degrees(L / dist):.1f} deg long ({math.degrees(math.atan2(z - CAM_H, d)):.0f} deg up)')
    facc, fn = Acc('fighters_struct'), Acc('fighters_neon')

    def fighter(c, axis, L):
        up = Vector((0.0, 0.0, 1.0))
        side = up.cross(axis).normalized()
        a = amin(math.hypot(c.x, c.y))
        yaw_f = math.atan2(axis.y, axis.x)
        fp = [(p.x, p.y) for p in (c + axis * (L * 0.5), c - axis * (L * 0.5) + side * (L * 0.42), c - axis * (L * 0.35), c - axis * (L * 0.5) - side * (L * 0.42))]
        facc.prism(fp, c.z - L * 0.03, c.z + L * 0.03, (0, 0, 0, 1), cap=True)
        facc.poly([(px, py, c.z - L * 0.03) for px, py in reversed(fp)], [(0, 0)] * 4, (0, 0, 0, 1))
        cp = c + axis * (L * 0.1)
        facc.box(cp.x, cp.y, c.z + L * 0.03, L * 0.2, L * 0.08, L * 0.05, yaw_f, (0, 0, 0, 1))                # the canopy
        fn.box(cp.x, cp.y, c.z + L * 0.03 + L * 0.05, max(0.8, a), L * 0.06, max(0.5, a * 0.6), yaw_f, (0.6, 0.85, 1.0, 0.6))
        e = c - axis * (L * 0.37)
        for sgn in (-1, 1):
            ee = e + side * (sgn * L * 0.08)
            fn.box(ee.x, ee.y, ee.z, a * 1.8, a * 1.8, a * 1.8, 0, (0.6, 0.9, 1.0, 2.2))
            for k in range(10):
                tube(fn, ee - axis * (k * L * 0.5), ee - axis * ((k + 1) * L * 0.5), max(0.5, a * 0.8), max(0.4, a * 0.5), (0.5, 0.85, 1.0, 0.9 * (1 - k / 10)), 4)
        for sgn, colk in ((1, 'green'), (-1, 'tail')):
            wtip = c - axis * (L * 0.45) + side * (sgn * L * 0.40)
            fn.box(wtip.x, wtip.y, wtip.z, a * 1.3, a * 1.3, a * 1.3, 0, (*PAL[colk], 1.0))
    n_f = 0
    for si in (0, 2):                                                             # two escort formations (a V of five ahead of a cruiser)
        if si >= len(fleet):
            continue
        c, axis, side, L, W, H = fleet[si]
        Lf = L * 0.07
        lead = c + axis * (L * 0.85) + side * (W * 0.6) + up * (H * 3.5)
        for k in range(-2, 3):
            pos = lead - axis * (abs(k) * Lf * 1.6) + side * (k * Lf * 1.9)
            fighter(pos, axis, Lf)
            n_f += 1
    for _ in range(2):                                                            # and two loose
        az = rng.uniform(-180, 180)
        if abs(az) < LANE_HALF + 8:
            az += 70
        d, z = rng.uniform(1400, 3200), rng.uniform(600, 1500)
        x, y = polar(d, az)
        yaw = rng.uniform(0, 2 * math.pi)
        fighter(Vector((x, y, z)), Vector((math.cos(yaw), math.sin(yaw), 0.0)), rng.uniform(70, 100))
        n_f += 1
    facc.build(mats['struct'])
    fn.build(mats['neon'])
    log(f'  {n_f} fighters')


# ---------------------------------------------------------------- scene
def setup_scene():
    sc = bpy.context.scene
    for o in list(sc.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    sc.world = world_sky()
    cam_d = bpy.data.cameras.new('sky_cam')
    cam_d.type = 'PANO'
    try:
        cam_d.panorama_type = 'EQUIRECTANGULAR'
    except Exception:
        cam_d.cycles.panorama_type = 'EQUIRECTANGULAR'
    cam_d.clip_start = 1.0
    cam_d.clip_end = 300000.0
    cam = bpy.data.objects.new('sky_cam', cam_d)
    sc.collection.objects.link(cam)
    cam.location = (0.0, 0.0, CAM_H)
    cam.rotation_euler = (math.pi / 2, 0.0, 0.0)
    sc.camera = cam
    # render
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    if DEVICE == 'cpu':                                                     # v7b: tests while the game holds the GPU (an 8 GB laptop card)
        cy.device = 'CPU'
    else:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type == 'OPTIX')
        cy.device = 'GPU'
    cy.samples = SAMPLES
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.025
    cy.adaptive_min_samples = min(16, SAMPLES)
    cy.use_denoising = True
    cy.denoiser = 'OPTIX' if DEVICE != 'cpu' else 'OPENIMAGEDENOISE'
    cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    cy.max_bounces = 5
    cy.diffuse_bounces = 2
    cy.glossy_bounces = 3
    cy.transmission_bounces = 2
    cy.volume_bounces = 0
    cy.transparent_max_bounces = 12
    cy.sample_clamp_direct = 0.0
    cy.sample_clamp_indirect = 8.0
    cy.blur_glossy = 1.0
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.volume_step_rate = 1.0
    cy.volume_max_steps = 1024
    cy.use_light_tree = True
    cy.use_auto_tile = True
    cy.tile_size = 2048
    sc.render.use_persistent_data = True
    sc.render.resolution_x = WIDTH
    sc.render.resolution_y = HEIGHT
    sc.render.resolution_percentage = 100
    if REGION:                                                              # v7: a cropped border render of one window (docs/166 §9)
        az0, az1, el0, el1 = [float(v) for v in REGION.split(',')]
        c0, c1 = int(math.floor((az0 / 360.0 + 0.5) * WIDTH)), int(math.ceil((az1 / 360.0 + 0.5) * WIDTH))
        r0, r1 = int(math.floor((90.0 - el1) / 180.0 * HEIGHT)), int(math.ceil((90.0 - el0) / 180.0 * HEIGHT))   # rows from the top
        sc.render.use_border = True
        sc.render.use_crop_to_border = True
        sc.render.border_min_x, sc.render.border_max_x = c0 / WIDTH, c1 / WIDTH        # exact: WIDTH and HEIGHT are powers of two
        sc.render.border_min_y, sc.render.border_max_y = (HEIGHT - r1) / HEIGHT, (HEIGHT - r0) / HEIGHT
        with open(os.path.splitext(OUT)[0] + '.region.json', 'w') as f:
            f.write(f'{{"col0": {c0}, "col1": {c1}, "row0": {r0}, "row1": {r1}, "width": {WIDTH}, "height": {HEIGHT}}}\n')
        log(f'region: columns {c0}..{c1} rows {r0}..{r1} of {WIDTH}x{HEIGHT} (az {az0}..{az1}, el {el0}..{el1})')
    sc.render.film_transparent = False
    sc.render.filter_size = 1.5
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    sc.render.image_settings.exr_codec = 'ZIP'
    sc.render.image_settings.color_mode = 'RGB'
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.filepath = OUT
    return sc


def main():
    log(f'seed {SEED} width {WIDTH} samples {SAMPLES} cam_h {CAM_H} detail {DETAIL} skip {sorted(SKIP) or "-"}')
    sc = setup_scene()
    city = City()
    lots, street_cells = city.layout()
    if on('mega'):
        city.megatowers()                                    # first: the ordinary lots stay out of their footprints
    if on('origin'):
        make_origin(city)
    if on('tether'):
        make_tether(city)
    city.station_keepout = station_plan(RAIL_LINES[0], CAM_H) if on('rails') else None
    city.kept_lots = plan_lots([lot for lot in lots if not city.excluded(lot['cx'], lot['cy'])])
    skipped = 0
    for lot in lots:
        if city.excluded(lot['cx'], lot['cy']):
            skipped += 1
            continue
        city.building(lot)
    log(f'buildings: {city.n_bld} ({skipped} lots under the supertalls)')
    if on('landmarks'):
        city.landmarks()
    if on('streets'):
        city.streets(street_cells)
        city.podium()
    if on('highways'):
        city.rings()
    if on('rails'):
        city.rails()
    if on('sigils'):
        city.sigils()                                        # v4: the sigils took the holo panels' places
    if on('platforms'):
        city.platforms()
    if on('air') and on('lanes'):
        city.air_lanes()
    if on('beams'):
        make_beams(city)
    if on('lasers'):
        make_lasers(city)
    mats = city.build_all()
    if on('rails'):
        station_report = make_cyber_station(RAIL_LINES[0], CAM_H, REPO, log=log)
        with open(os.path.splitext(OUT)[0] + '.station.json', 'w') as f:
            json.dump(station_report, f, indent=2)
    make_ground(mat_ground())
    if on('water'):
        make_water(mat_water())
    if on('fog'):
        make_fog(mat_fog())
    if on('haze'):
        make_haze(mat_haze())
    if on('clouds') and flag('--clouds'):                    # v4: the sky is SPACE — no cloud sheets unless asked for (--clouds)
        mxy = (0.0, (1500.0 - CAM_H) / math.tan(MOON_EL * D2R))
        make_clouds(1500.0, mat_clouds(1500.0, mxy, 0.56, 0.66, E_CLOUD * 1.5))
        mxy2 = (0.0, (2900.0 - CAM_H) / math.tan(MOON_EL * D2R))
        make_clouds(2900.0, mat_clouds(2900.0, mxy2, 0.62, 0.74, E_CLOUD * 0.8))
    if on('moon'):
        make_moon(mat_moon())
    if on('bodies'):
        make_bodies()
        retired_bodies = [ob for ob in bpy.data.objects if object_is_retired(ob.name)]
        city.composition['retired_body_objects'] = [ob.name for ob in retired_bodies]
        for ob in retired_bodies:
            bpy.data.objects.remove(ob, do_unlink=True)
        if RETIRED_ROCKS[0]:
            log(f'rocks: RETIRED (v7c) — {RETIRED_ROCKS[0]} asteroids / debris rocks not built (their random draws kept)')
    if on('ships'):
        if SHIPS:
            make_airships(mats)
            make_starships(mats)
        else:
            retired(make_airships, mats)                     # v7b: RETIRED — the builders only spend their random draws, so the
            retired(make_starships, mats)                    #      searchlights after them stay exactly where v7 put them
    sign_mask = False
    if on('sign'):
        if SIGN_STYLE in ('cyber_hero', 'ominous', 'cyber'):
            builder = {'cyber_hero': make_cyber_hero_title, 'ominous': make_ominous_title,
                       'cyber': make_cyber_title}[SIGN_STYLE]
            report = builder(GATE, CAM_H, REPO, sign_aov=SIGN_AOV, log=log)
            with open(os.path.splitext(OUT)[0] + '.title.json', 'w') as f:
                json.dump(report, f, indent=2)
            sign_mask = setup_sign_mask(sc)
        elif SIGN_STYLE != 'gate' or not make_title_gate():
            make_sign(mats['struct'], mats['neon'])
        else:
            sign_mask = setup_sign_mask(sc)                                  # v7b: the card's AOV -> <raw>.sign.exr for finish_sky.py
    if on('search'):
        make_searchlights(city)
    nfaces = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH')
    city.composition['celestial_counts'] = CELESTIAL_COUNTS
    city.composition['visible_buildings'] = city.n_bld
    city.composition['station_keepout'] = city.station_keepout
    with open(os.path.splitext(OUT)[0] + '.composition.json', 'w') as f:
        json.dump(city.composition, f, indent=2)
    log(f'scene: {len(sc.objects)} objects, {nfaces} faces')
    if BLEND:
        os.makedirs(os.path.dirname(os.path.abspath(BLEND)), exist_ok=True)
        bpy.data.orphans_purge(do_recursive=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(BLEND))
        log(f'saved {BLEND}')
    if NO_RENDER:
        log('no render (--no-render)')
        return
    if os.path.exists(sign_mask_path()):
        os.remove(sign_mask_path())                                          # v7b: never let an old mask pair with this render
    t = time.time()
    bpy.ops.render.render(write_still=True)
    log(f'RENDER {WIDTH}x{HEIGHT} @ {SAMPLES} spp: {time.time() - t:.0f} s -> {OUT} ({os.path.getsize(OUT) / 1048576:.1f} MB)')
    if sign_mask:
        collect_sign_mask()


def retired(fn, *a):
    """v7b: run a RETIRED builder only for its random draws (every later element reads the same stream, so it does not move),
    then delete everything it made; its log lines are muted"""
    before = set(bpy.data.objects)
    _LOG_MUTE.append(1)
    try:
        fn(*a)
    finally:
        _LOG_MUTE.pop()
    made = [o for o in bpy.data.objects if o not in before]
    for o in made:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if data is not None and data.users == 0 and isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
    log(f'{fn.__name__}: RETIRED (v7b) — {len(made)} objects built for their random draws and deleted')


def sign_mask_path():
    return os.path.splitext(OUT)[0] + '.sign.exr'


def setup_sign_mask(sc):
    """v7b: the compositor writes the card's 'sign' AOV (Render Layers -> File Output, half EXR) beside the raw render; the
    Composite passes the picture through untouched. Returns True when armed."""
    vl = bpy.context.view_layer
    if SIGN_AOV not in [a.name for a in vl.aovs]:
        return False
    sc.use_nodes = True
    sc.render.use_compositing = True
    tree = sc.node_tree
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    rl = tree.nodes.new('CompositorNodeRLayers')
    rl.layer = vl.name
    comp = tree.nodes.new('CompositorNodeComposite')
    tree.links.new(rl.outputs['Image'], comp.inputs['Image'])
    if SIGN_AOV not in rl.outputs:
        log(f'sign mask: the Render Layers node has no {SIGN_AOV!r} output — no mask (the finish uses the city knee everywhere)')
        return False
    fo = tree.nodes.new('CompositorNodeOutputFile')
    fo.base_path = os.path.dirname(os.path.abspath(OUT))
    fo.format.file_format = 'OPEN_EXR'
    fo.format.color_depth = '16'
    fo.format.exr_codec = 'ZIP'
    fo.format.color_mode = 'RGB'
    fo.file_slots[0].path = os.path.splitext(os.path.basename(OUT))[0] + '.signmask_'
    tree.links.new(rl.outputs[SIGN_AOV], fo.inputs[0])
    log(f'sign mask: AOV {SIGN_AOV!r} -> {sign_mask_path()}')
    return True


def collect_sign_mask():
    """the File Output node appends the frame number: move <out>.signmask_NNNN.exr to <out>.sign.exr"""
    d = os.path.dirname(os.path.abspath(OUT))
    stem = os.path.splitext(os.path.basename(OUT))[0] + '.signmask_'
    got = sorted(f for f in os.listdir(d) if f.startswith(stem) and f.endswith('.exr'))
    if not got:
        log('sign mask: NOT WRITTEN (no File Output file) — the finish will use the city knee everywhere')
        return
    os.replace(os.path.join(d, got[-1]), sign_mask_path())
    for f in got[:-1]:
        os.remove(os.path.join(d, f))
    log(f'sign mask -> {sign_mask_path()}')


main()
