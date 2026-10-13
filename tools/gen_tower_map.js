#!/usr/bin/env node
// =============================================================================
// gen_tower_map.js — generator for map_source/zm/zm_tod2_cybercity.map
//
// THE .map IS GENERATED: this file's layout tables are the source of truth.
// Run `node tools/gen_tower_map.js` to (re)write BOTH:
//   map_source/zm/zm_tod2_cybercity.map
//   scripts/zm/zm_tod2_cybercity/_tod_door_data.gsc   (door buy-trigger coords)
// Hand-edits to those two files WILL be clobbered — change the tables here.
//
// v3 — THE FULL TOWER (user 2026-08-18, overnight mandate): 25 laps of
// open-air spiral around the solid core (was 3), rooftop arena on top at
// z=19200. Neon palette CYCLES through 8 colors lap by lap (all names
// verified against the installed eMoX GDT). Perks / wallbuys ladder up the
// climb; door costs escalate 750 -> 4000 (roof 5000). Reflection probes every
// 3rd lap. Miami night skybox all around; scripted fog rides
// _tod_atmosphere.gsc (not this file).
//
//   base arena  z=0        base_zone     power switch, Quick Revive, SMG wall,
//                                        mystery box, 3 class-select stations
//   lap N       (N-1)*768  lapN_zone     door enter_lapN
//   THE CROWN   z=19392    roof_zone     door enter_roof — the finale plaza
//
// Spiral (per lap, CCW): E flight north -> NE landing -> N flight west ->
// NW landing -> W flight south -> SW landing -> S flight east -> SE landing
// (= next lap start). 16 steps x 12u rise / 32u tread per flight; steps are
// 16u slabs (the lap above spirals 752u overhead).
//
// v9 — THE CROWN (user 2026-08-21: "at the top of the map there is nothing...
// design the top of the map and design the ending. Also the last platform
// isn't even connected to the stairs"). Two things changed:
//   1. THE BUG. The roof arrival was an ODD-lap-only special case inside the
//      flight loop. v8 doubled LAPS to 50 — an EVEN final lap — so that branch
//      never ran: no arrival landing was ever emitted, and the roof door slab
//      hung in open air on a side floor 50 does not build. The roof was
//      literally unreachable. The crown is now built from the SAME parity math
//      as the flights (CROWN_LAP = LAPS+1, mirror factor CM), so it welds to
//      the stairs for ANY value of LAPS. Change LAPS freely; the top follows.
//   2. THE TOP. One more flight (the CROWN STAIR) climbs off the final landing
//      to the CROWN DECK at z=TOP2 — a 1152x1152 plaza capping the core, WIDER
//      THAN THE BASE ARENA, with a glowing cornice visible from the street.
//      Plaza furniture: the UPLINK dais dead centre, 4 corner PYLONS, PaP west,
//      Mule Kick east, an upgrade terminal south, and the EXTRACTION PAD north.
//      The finale logic that drives them lives in _tod_finale.gsc and reads its
//      anchor points from the GENERATED _tod_crown_data.gsc (this file emits
//      it, same no-drift contract as _tod_door_data.gsc).
//
// LED-BAKE BUDGET: ~2400 brushes at 25 laps. The bake is THE gate
// (docs/BO3_MAPMAKING_KB.md §1) — tools/_bake_test.ps1 -TimeoutSec 420 after
// any regen. If it CRASHES (brush.cpp:1860): first bump PARA_EVERY 2 -> 4
// (halves parapet brushes), then reduce LAPS.
// =============================================================================

'use strict';

const fs = require('fs');
const path = require('path');
const TOWER_LIGHTING = require('./art_cohesion/tower_lighting');
const BROKEN_TOWER = require('./broken_tower_layout');
const TRANSIT = require('./tower_transit_layout');
const ARENA_LAYOUT = require('./battle_arena_layout');   // THE BATTLE ARENA (docs/185)
const HOUSE_LAYOUT = require('./dealer_house_layout');   // THE DEALER'S HOUSE (docs/207): the parlour + the final arena
const WUNDERFIZZ = require('./wunderfizz_layout');
const WUNDERFIZZ_NODES = WUNDERFIZZ.nodes();
const HAVEN = require('./haven_layout');                 // THE HAVENS (docs/202): the safe zones on floors 10/20/30/40

const REPO = path.join(__dirname, '..');
// TOD_MAP_OUT lets a run write the .map somewhere else, so a variant can be
// generated and BAKED (`_bake_test.ps1 -TestMap <path>`) without touching the
// shipped one. Added 2026-08-25 to A/B a bake time that would not reproduce —
// which is the only honest way to answer "what actually made the bake slow".
const MAP_OUT = process.env.TOD_MAP_OUT || path.join(REPO, 'map_source', 'zm', 'zm_tod2_cybercity.map');
const DOOR_GSC_OUT = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_door_data.gsc');
const CROWN_GSC_OUT = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_crown_data.gsc');
const BREATHER_GSC_OUT = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_breather_data.gsc');

// ---------------------------------------------------------------------------
// Layout constants
// ---------------------------------------------------------------------------
const CORE = 256;          // core half-extent (solid column, roof on top)
const PX = 416;            // path outer edge (path width 160)
const PARA = 20;           // parapet thickness
const PARA_H = 56;         // parapet height above the local step/landing
const ARENA = 540;         // base arena half-extent (104u ring around the tower)
const WALL = 20;
const BASE_WALL_H = 128;
const SLAB = 16;

// ---------------------------------------------------------------------------
// The old four-pad bottom room is replaced by an open crown-return apron.
// The hub is now on the top terrace; all pad and room geometry lives together.
const TPB_DOOR = 160; // existing south opening, now an ungated return-pad exit

const LAPS = 50;                              // v8: DOUBLED (user 2026-08-21) — top z=19200
const STEPS = 16, TREAD = 32, RISE = 12;      // per flight: 512 run, 192 rise
// A flight spans exactly one core face, so STEPS*TREAD must equal 2*CORE. That
// was an unguarded hand-maintained coincidence until 2026-08-27 — docs/39's
// blast-radius trial set TREAD 48 and got a 50-storey map with the climb
// SILENTLY severed (no throw; only the geometry lint caught it). Free insurance:
if (STEPS * TREAD !== 2 * CORE) throw new Error(`STEPS*TREAD (${STEPS * TREAD}) must equal 2*CORE (${2 * CORE}) — the flight no longer spans its core face`);
const FLIGHT_RISE = STEPS * RISE;             // 192
const LAP_RISE = 2 * FLIGHT_RISE;             // 384 — v6: TWO flights per floor (user 2026-08-20)
const TOP = LAPS * LAP_RISE;                  // 19200 — rooftop level
const PARA_EVERY = 2;                         // parapet box per N steps (bake knob)
// Invisible cap over every rail run so a rail top is not a launch pad (v9,
// user 2026-08-21). 112 is well over a BO3 jump from a rail top.
const RAIL_CAP_H = 112;
// THE VIEW-HEIGHT RAILS (2026-09-29, user: "lower the railings on our current tower by about
// thirty percent. Thirty percent of the height. I want it to be lower so people can actually view
// the skybox. Right now the railing covers up a lot of space on the screen"). Every VISIBLE rail on
// the main tower is RAIL_VIEW_SCALE of its old PARA_H; the COLLISION IS UNCHANGED: a lowered rail's
// invisible clip starts at its FLOOR (the 2026-09-27 balcony curb recipe, crail) and still tops out
// at floor + PARA_H + RAIL_CAP_H (168), so no rail can be hopped that stopped a player before, and
// the geometry lint's edge guard (a brush from floor+4 to floor+52) is the clip. PARA_H stays 56:
// it also sizes the lounge sills (BR_SILL_H) and the balcony barrier (BZ1). 1.0 = the old map.
// RAIL_VIS_H must stay above the lint's step height (18) and the conduit inlays' mount (+-9).
const RAIL_VIEW_SCALE = 0.7;
const RAIL_VIS_H = Math.round(PARA_H * RAIL_VIEW_SCALE);   // 39
if (RAIL_VIS_H <= 20 || RAIL_VIS_H > PARA_H) throw new Error(`RAIL_VIS_H ${RAIL_VIS_H} must be in (20, ${PARA_H}]`);
const railClipZ = (z) => (RAIL_VIS_H < PARA_H ? z : z + PARA_H);   // where a rail's clip starts: its floor once lowered

// ---------------------------------------------------------------------------
// THE UNDERCITY + THE WORKSHOP WINGS (TOD II base layout, 2026-09-23, docs/158;
// user: "it's kinda gonna start in a cyber basement ... you're gonna have to
// open up a few doors, not just going up but laterally and up ... zombies will
// spawn at four windows at spawn ... make your way to the tower zone ... it'll
// be square-ish and then in each direction there will be a door that branches
// out to another section ... each one of those rooms will have a crafting bench
// where you can then create your protector ... four different protectors ...
// the tower will be right in the middle of this open area room").
//
// THE ROUTE:
//   THE VAULT      spawn, z=UC_Z (one tower floor DOWN). Four WINDOW NICHES the
//                  horde climbs out of, Quick Revive on its north wall.
//   enter_conduit  the lateral door, in the wall the Vault shares with
//   THE CONDUIT    the second basement room: the eight partner PARTS on a shelf
//                  along its west wall, the stair foot in its east wall.
//   THE SHAFT      one straight 32-tread flight (UC_STEPS x RISE = LAP_RISE)
//                  climbing EAST between 128-tall walls, open to the sky.
//   enter_base     the "up" door, in the arena's WEST wall at the top landing.
//   THE TOWER PLAZA the old base arena, UNTOUCHED: core, lap-1 door, station,
//                  hoop, crate, inducer, teleport bay (S), power hall (SE).
//   THE WINGS      one door per plaza wall -> a 160-wide hallway -> a 512-square
//                  workshop with a PARTNER BENCH on its far wall: N Civil
//                  Protector, E Talon, S R.A.P.S., W Cerberus (the
//                  _tod_partners buildables; their anchors are EMITTED into
//                  _tod_breather_data.gsc from the WINGS table below, and the
//                  bench collision clips are cut here, so bench and clip can
//                  never drift).
//
// WHY THE ARENA DOES NOT MOVE: a dozen scripts read absolute base coordinates
// (teleport up_orgs, the station, the hoop, the crate, the inducer, the perk
// pads, the secret bears, the music emitter ...). Everything new is built
// AROUND it - below it and beside it - so not one of those anchors changes.
//
// WHERE EACH WALL'S DOORS GO, and why (each measured against the live triggers
// on that wall - the "no two use-triggers overlap" rule, r96 door spheres):
//   W wall  y[-240,-80]  enter_base (the shaft's top landing behind it). NOT
//           centred: the base ammo crate's trigger (-376,0) r72 reaches x=-448
//           and a centred door's inner sphere (-490,0) r96 reaches x=-394.
//           y[320,480]   the West Workshop.
//   N wall  x[-80,80]    the North Workshop. The perk park row is re-pitched
//           4 + 4 around it and Quick Revive parks in the Vault (its pad).
//   E wall  y[300,460]   the East Workshop, in the NE gutter north of the lap-1
//           flight's anti-bypass wall; the power hall keeps the SE.
//   S wall  x[-540,-380] the South Workshop, hugging the SW corner: the bay
//           door owns the centre and the rampage inducer's r96 trigger owns
//           x[-360,-168] (INDUCER_X nudged -280 -> -264 so both clear by 4u).
// The arena's own risers moved off the new door mouths (see base_zone).
// ---------------------------------------------------------------------------
const UC_Z        = -LAP_RISE;                 // -384: the Undercity floor top
const UC_WALL_H   = 192;                       // floor to ceiling underside
const UC_CEIL_T   = 16;
const UC_TOP      = UC_Z + UC_WALL_H;          // -192: ceiling underside
const UC_BAND_Z   = 120;                       // cyan seam band on every undercity wall: z[+120,+136]
const UC_STEPS    = LAP_RISE / RISE;           // 32 treads climb the whole LAP_RISE in one flight
if (UC_STEPS !== Math.floor(UC_STEPS)) throw new Error('UC_STEPS must be whole');
// THE SHAFT: 256 wide, centred on SHAFT_CY, treads run along x, climbing EAST.
const SHAFT_CY     = -160, SHAFT_HW = 128;
const SHAFT_TOP_X2 = -(ARENA + WALL);          // -560: the top landing ends at the arena's W wall
const SHAFT_TOP_X1 = SHAFT_TOP_X2 - 240;       // -800: a 240-deep top landing (the door's outer trigger stands on it)
const SHAFT_FLT_X2 = SHAFT_TOP_X1;             // tread 32's east edge
const SHAFT_FLT_X1 = SHAFT_FLT_X2 - UC_STEPS * TREAD;   // -1824: the first riser
const SHAFT_FOOT_X1 = SHAFT_FLT_X1 - 172;      // -1996: foot landing x[-1996,-1824]
// THE CONDUIT: west of the foot landing; its east wall band is x[-2016,-1996].
const CD_X2 = SHAFT_FOOT_X1 - WALL, CD_X1 = CD_X2 - 512;          // interior x[-2528,-2016]
const CD_Y1 = SHAFT_CY - 288, CD_Y2 = SHAFT_CY + 288;              // interior y[-448,128]
// THE VAULT: south of the conduit; the two share ONE wall band (y[-468,-448]).
const VT_Y2 = CD_Y1 - WALL, VT_Y1 = VT_Y2 - 560;                   // interior y[-1028,-468]
const VT_X1 = -2592, VT_X2 = -1952;                               // interior, 640 wide
const VT_CX = (VT_X1 + VT_X2) / 2, VT_CY = (VT_Y1 + VT_Y2) / 2;   // -2272, -748
const CONDUIT_DOOR_X = VT_CX;                  // enter_conduit, centred in the shared wall
const VAULT_QR = [VT_X2 - 108, VT_Y2 - 29];    // Quick Revive backs the Vault's N wall east of the door (the arena's 29u standoff)
// WINDOW NICHES: a 160-wide recess 96 deep past the wall's inner face, the
// riser at its centre, clip_player across the mouth (players stay out, zombies
// walk through), a 12u cyan sill, a lit red back panel.
const WIN_W = 160, WIN_D = 96, WIN_SILL = 12, WIN_H = 128;
const VAULT_WINDOWS = [
  { side: 'W', c: VT_CY },
  { side: 'E', c: VT_CY },
  { side: 'S', c: VT_X1 + 160 },
  { side: 'S', c: VT_X2 - 160 },
];
// THE PARTNER PARTS SHELF: eight props along the Conduit's west wall, 64 apart.
const PART_SHELF_X = CD_X1 + 25, PART_SHELF_Y0 = CD_Y1 + 48, PART_SHELF_PITCH = 64;
// THE NEW DOORS' PRICES (-GscOnly to change: they ride _tod_door_data.gsc).
const CONDUIT_DOOR_COST = 500;
const BASE_DOOR_COST    = 750;
const WING_DOOR_COST    = 1000;
// THE ARENA'S NEW OPENINGS (see the wall table above)
const WEXIT_Y = [SHAFT_CY - 80, SHAFT_CY + 80];   // enter_base in the W wall: y[-240,-80]
const WING_HALL_L = 364;              // hallway floor u[560,924]; the room's near wall band starts at 924
const WING_ROOM = 512;                // room interior, square
// The WINGS table. ax/sg = the outward axis and its sign; dc = the doorway's
// centre along the wall; rc = the room's centre along the wall (a room may be
// offset from its own hallway, the South one is: the teleport bay is in the
// way); hue = the wing's own colour (panel behind the bench, floor ring,
// hallway band, lights); zoneVMax clamps a zone volume against a neighbour.
const WINGS = [
  { key: 'n', dest: 'the North Workshop', partner: 0, ax: 'y', sg: +1, dc: 0,    rc: 0,    hue: 'green',  light: '0.35 1 0.45' },
  { key: 'e', dest: 'the East Workshop',  partner: 1, ax: 'x', sg: +1, dc: 380,  rc: 380,  hue: 'orange', light: '1 0.6 0.2' },
  { key: 's', dest: 'the South Workshop', partner: 2, ax: 'y', sg: -1, dc: -460, rc: -536, hue: 'purple', light: '0.7 0.4 1', zoneVMax: -280 },
  { key: 'w', dest: 'the West Workshop',  partner: 3, ax: 'x', sg: -1, dc: 400,  rc: 480,  hue: 'red',    light: '1 0.35 0.35' },
];
// bench body = the measured p8_zm_crafting_table bounds (tools/partner/
// install_assets.py): 101 across, 29 deep (10 in front of the origin, 19
// behind), 44 tall. The script puts the use trigger 57 in front of the origin.
const BENCH_ACROSS = 51, BENCH_FRONT = 10, BENCH_BACK = 19, BENCH_H = 44;
const BENCH_STANDOFF = 8;             // the body's back to the far wall's inner face
// The wing's LOCAL FRAME: u runs outward from the arena centre along the wing's
// axis (the arena wall's outer face is u = ARENA + WALL), v runs across it.
function wingFrame(w) {
  const toW = (u, v) => (w.ax === 'y' ? [v, w.sg * u] : [w.sg * u, v]);
  const rect = (u1, u2, v1, v2, z1, z2) => {
    const [ax1, ay1] = toW(u1, v1), [ax2, ay2] = toW(u2, v2);
    return { x1: Math.min(ax1, ax2), x2: Math.max(ax1, ax2), y1: Math.min(ay1, ay2), y2: Math.max(ay1, ay2), z1, z2 };
  };
  const box = (label, u1, u2, v1, v2, z1, z2, mat) => {
    const r = rect(u1, u2, v1, v2, z1, z2);
    addBox(`wing ${w.key} ${label}`, r.x1, r.x2, r.y1, r.y2, r.z1, r.z2, mat);
  };
  const out = toW(1, 0);                                   // outward unit vector
  const faceYaw = (Math.round(Math.atan2(-out[1], -out[0]) * 180 / Math.PI) + 360) % 360;   // faces back toward the arena
  return { toW, rect, box, out, faceYaw, pt: (u, v) => toW(u, v) };
}
// Wing u-stations (shared by the geometry, the entities and the emitted data)
const WU0 = ARENA + WALL;                 // 560: the arena wall's outer face = hallway start
const WU_HALL_END = WU0 + WING_HALL_L;    // 924: hallway end = the room's near wall band
const WU_ROOM1 = WU_HALL_END + WALL;      // 944: room interior start
const WU_ROOM2 = WU_ROOM1 + WING_ROOM;    // 1456: room interior end (the far wall's inner face)
const WU_ROOM3 = WU_ROOM2 + WALL;         // 1476: the far wall's outer face
const WU_BENCH = WU_ROOM2 - BENCH_STANDOFF - BENCH_BACK;   // 1429: bench origin

// ---------------------------------------------------------------------------
// STAIR RAMP CLIP (2026-08-27) — the stair-feel fix. Full research: docs/39.
//
// Players complained the stairs are "slippery going down / sticky going up".
// The geometry is NOT defective (docs/39 §2: every transition on the climb is
// exactly 0 or +12, zero anomalies on a 1-unit walk) — the problem is that this
// was the only staircase in shipped-or-custom BO3 content that players WALK ON
// STEPPED COLLISION. Every stock Treyarch stair carries a sloped clip wedge
// over its treads (verified in the shipped prefab source: zm_giant staircases
// use metal_clip at atan(8/12); stairs_curved clips a HELICAL stair with a
// 16-brush fan). The wedge removes all ~1,616 discrete step events per climb:
// no riser planes to catch a diagonal move going up, no per-step camera
// correction, continuous ground contact (friction + full steering) going down.
//
// MATERIAL = plain `clip` since v16.61a (2026-09-02) — Treyarch's own shipped
// configuration (zm_giant uses metal_clip, the same flags + a surface type).
// From 2026-08-27 to v16.60 it was `clip_player`, chosen to isolate the
// player-side variable for the feel experiment (docs/39 G1b):
//   * clip.gdt (art_assets/t6_legacy/texture_assets/clip.gdt, re-read
//     2026-09-02): clip_player = playerClip 1, aiClip 0, bulletClip 0,
//     canShootClip 0 — blocks PLAYERS ONLY; plain clip = the SAME flags with
//     aiClip 1. So bullets and grenades still pass through either wedge and
//     hit the treads; the only thing `clip` adds is ZOMBIE collision.
//   * radiant/configs/navmesh.json lists clip_player in "exclusions" and NOT
//     plain clip. Under clip_player the navmesh — and every zombie path — was
//     byte-identical with the ramps in or out, and zombies climbed the 16
//     stepped treads: ~9 discrete 12-unit hops per second at sprint speed,
//     the only BO3 staircase anywhere that AI climbs on stepped collision.
//     THAT is what a head lock-on (Deadshot, and the stock torso assist to a
//     lesser degree) was tracking — the user's "bounces up and down when a
//     zombie runs up stairs". Under plain clip the navmesh cuts on the wedge
//     (20.556° against maxWalkableSlope 46), so zombies glide the slope the
//     way they do on every Treyarch stair and the target head moves smoothly.
//     Docs/39 G1a called this "likely an AI improvement ... must be walked
//     with a horde before shipping" — that walk is the v16.61a test.
//   * measure_lit_area.js's UNLIT regex is start-anchored (^clip): `clip` and
//     `clip_player` both stay out of the lit-area budget; metal_clip would be
//     mis-counted as ~30M u² of phantom lit area, which is why not metal_clip.
//   * The breather lounges' WINDOW VOIDS used to share this key. They must
//     stay clip_player (players stay in, bullets AND zombies pass — a zombie
//     must never path onto a window sill), so they ride MAT.winClip now.
// REVERT TO THE OLD FEEL EXPERIMENT: MAT.rampClip = 'clip_player', regen,
// FULL build (the navmesh is what changes either way).
//
// PLANE PLACEMENT (Treyarch's, measured from their prefabs, not guessed): the
// wedge top is the plane through the FRONT-TOP NOSING CORNER of every tread —
// the unique lowest plane at the stair's slope that never dips below a tread
// top. It touches each tread at its front edge and stands at most +RISE above
// it at the back. Both ends land flush: the top end welds into the landing at
// exactly landing height, and the bottom end knife-edges into the approach
// floor over the last TREAD units before the first riser (a 0->12 feather,
// exactly the stock arrangement). Underside = the same plane RAMP_T lower,
// which stays inside the tread slabs the whole way (tread slab bottom is
// top-16 and consecutive treads overlap 4 in z), so NO invisible face is ever
// exposed under the open-air stairs — the lap-1 arena strip under the east
// flight stays walkable.
//
// TOOLING CONTRACT (all verified before this shipped):
//   * lint_tod_geometry.js parses axis-constant planes only and drops a wedge
//     at `planes.length !== 6` BEFORE the material table lookup — so the lint
//     neither aborts on the material nor sees the ramps at all. Its proofs
//     still hold for the treads underneath, which stay exactly as they were;
//     the ramps themselves are proven by the generator's own construction
//     (slope asserted = RISE/TREAD, ends asserted flush by arithmetic here).
//   * measure_lit_area.js counts them in its skipped/unlit bucket (^clip).
//   * The wedges do NOT go through addBox(), so the crown self-measure
//     (crownBB) never sees the crown-stair ramp — irrelevant, it is inside the
//     crown stair's existing envelope.
//
// REVERT: set STAIR_RAMP_CLIP = false, node tools/gen_tower_map.js, FULL
// rebuild. Nothing else references it — no GSC, no zone, no data file.
// ---------------------------------------------------------------------------
const STAIR_RAMP_CLIP = true;
const RAMP_T = 16;             // vertical thickness = SLAB: underside stays buried in the tread slabs
// RAMP_LIFT (2026-09-04, navmesh seams — user: "random spots on the map zombies
// won't attack you ... around floor 42-44"). The wedge top used to pass EXACTLY
// through every tread's front-top nosing edge, so each flight handed cod2map a
// walkable plane with fifteen coplanar contact LINES on it. Havok's overlapping-
// triangle fixup turns that into slivers, and on specific laps — the same laps on
// BOTH towers, because the plane arithmetic depends only on y and z — the ramp's
// faces come out unstitched: tools/lint_tod_navmesh.js read the shipped .hkt as
// 18 connected components, every seam inside the E flight of laps 17/19/33/39/43
// (floor 43 = the user's 42-44 report; lap 17 = the v17.7 "no mesh above floor
// 17" ceiling, which was this seam plus pruning). Lifting the whole wedge by
// RAMP_LIFT puts every nosing strictly UNDER the plane — no contact, no sliver —
// while the walking surface, the slope and the seeds are otherwise unchanged
// (the underside stays inside the tread slabs for any LIFT <= SLAB - 4; the two
// ends become 2-unit steps onto/off the landings, under Havok maxStepHeight 18).
// Players never touched the treads except at the nosings, so this moves the
// visible feet by 2 units and nothing else. The gate that proves it every full
// build is lint_tod_navmesh.js (build_map.ps1, right after cod2map).
const RAMP_LIFT = 2;

// ---------------------------------------------------------------------------
// THE CROWN (v9) — the top of the map.
//
// PARITY IS THE WHOLE POINT. The spiral alternates sides per lap: an ODD lap
// climbs E then N and finishes on the NW landing; an EVEN lap climbs W then S
// and finishes on the SE landing. So the final landing's CORNER depends on
// LAPS' parity. v8's roof arrival was hardcoded to the odd case and silently
// vanished when LAPS became even. Here the crown is treated as ONE MORE LAP
// (CROWN_LAP = LAPS + 1) and every crown coordinate is written in the ODD
// frame, then point-mirrored through the tower axis by CM when the crown lap
// is even. Odd-frame crown = E flight up the east face, arriving on the NORTH
// apron; even-frame = the exact mirror (W flight, SOUTH apron). Both weld to
// whatever landing the spiral actually ended on.
// ---------------------------------------------------------------------------
const CROWN_LAP    = LAPS + 1;                  // the crown stair is "lap LAPS+1"
const CROWN_ODD    = ( CROWN_LAP % 2 === 1 );   // odd -> E flight, N arrival
const CM           = ( CROWN_ODD ? 1 : -1 );    // point-mirror factor for crown coords
const TOP2         = TOP + FLIGHT_RISE;         // 19392 — the crown level (terrace / causeway / hall floor)
// The route, in order (odd frame — all y's flip under CM):
//   CROWN STAIR  final landing -> TOP2, gold treads, up the east face
//   TERRACE      a 960x224 forecourt along the capital's north face; you arrive
//                at its east end and turn toward the causeway
//   CAUSEWAY     "the pathway" (user): 224 wide, 640 long, on-axis, three cyan
//                portal frames, glowing underside — over 19,000 units of air
//   CROWN HALL   "the crown house" (user): 1536 x 1536 open-top citadel,
//                576-tall walls, 4 corner towers + 3 pilaster spikes + a
//                twin-spired gate, cyan cornice, inverted-ziggurat underbelly
//                ending in a glowing gravity core. It FLOATS beside the tower.
//   MAST         on the core top: a 5-tier spire to TOP2+1920 with a red beacon
const TER_W        = 480;                       // terrace half-width (x)
const TER_Y1       = CORE, TER_Y2 = 480;        // terrace band (y): 224 deep off the capital face
// THE LAST MILE (v10, user 2026-08-23: "the road to the pyramid needs to be
// long ... they get ambushed in all directions"). The causeway is now the
// finale ARENA, not a connector, so it grew on BOTH axes:
//   LENGTH 640 -> 6400. The finale clock is the length of the closing song
//   (197s). Unopposed sprint is roughly 250 u/s, so 6400 is about 26s of pure
//   running — the rest of the song is the fight. Tune here, and re-run the LED
//   bake gate: this is the single biggest lit surface on the map now.
//   WIDTH 224 -> 576. A 224-wide bridge can only be attacked from ahead and
//   behind, which is the opposite of "ambushed in all directions". At 576 the
//   risers below can sit off-centre on alternating sides and there is room to
//   be flanked, to dodge, and to fight backwards.
// v10.9 (user 2026-08-23: "make the path to the castle very thin"). 576 -> 160
// wide, which is EXACTLY the tower's own stair width (PX 416 - CORE 256), so
// the road reads as one last flight rather than a plaza. This reverses the v10
// widening: that was mine, to make "ambushed in all directions" survivable on
// a bridge. The user has since asked for the opposite feel AND for spawns to
// come from AHEAD instead of the flanks (see the causeway risers below and
// _tod_endless_rounds::finale_spawn_selection), so the flanking room the width
// existed to provide is no longer what the encounter is built on. Rails stay:
// at 160 wide over 19,000 units of air, they are the difference between a
// gauntlet and a coin flip.
const CW_HALF      = 80;                        // causeway half-width (160 wide)
const CW_LEN       = 7360;                      // walked length exceeds this: the lanes climb, dive and jog
// THE ROAD WINDS AND FORKS — and since v12 every lane is a DIFFERENT shape
// (v10.11 user: "can twist and turn and go up and down ... split into
// multiple paths that converge. Lets be creative"; v12 user: "scary and
// anxious"). ONE shape description lives in this file and it is the one in
// SECTION 5c (ridge / broken stair -> THE NARROWS -> undercroft / plank /
// weave) — this header deliberately does not carry a second copy, because a
// second copy is how the v10.10 comment ended up describing a serpentine
// that no longer existed.
// FIRST AND LAST RUN ARE ON THE AXIS AT TOP2, and that is load-bearing: the
// entrance must line up with the terrace mouth where the gate stands, and the
// exit with the hall gate opening (x +/-GATE_HALF). A run ending off-axis or
// off-height would put players against the citadel south WALL, not its door.
// The full layout, the y-budget and the brush recipe live in section 5c.
// The road's own geometry constants (CW_LAT, CW_SWING, tread/rise, the grid)
// live in SECTION 5c with the code that uses them — they were up here when the
// road was a straight strip described by two numbers, and having half the shape
// 500 lines from the other half is how the v10.10 comment ended up describing a
// serpentine that no longer existed.
const HS           = TER_Y2 + CW_LEN;           // hall south outer face
const HW           = 768;                       // hall half-width           (1536 wide)
const HD           = 1536;                      // hall depth
const HN           = HS + HD;                   // hall north outer face     (2656)
const HYC          = ( HS + HN ) / 2;           // hall centre y             (1888)
const HWALL        = 40, HWALL_H = 576;         // wall thickness / height (unjumpable)
const CTOWER       = 192;                       // corner tower footprint (square)
const GATE_HALF    = 128, GATE_H = 256;         // gate opening (256 wide x 256 tall)
const POST_W       = 40;                        // gate post width
const RAIL_H       = PARA_H;                    // 56: chest-high rails everywhere up here + caps
const DAIS         = 112, DAIS_H = 16;          // uplink dais (16 = one step; 32 would need a jump)
const EXFIL_Y      = HN - HWALL - 224;          // extraction pad centre, north end of the hall
const EXFIL_HALF   = 80;                        // 160 sq pad (the 129-wide pad light sits on it)
const MAST_TIERS   = [ [ 512, 320 ], [ 384, 320 ], [ 256, 320 ], [ 128, 384 ], [ 48, 576 ] ];  // [width, height]
const MAST_TOP     = TOP2 + MAST_TIERS.reduce( ( a, t ) => a + t[ 1 ], 0 );   // TOP2 + 1920

// ---------------------------------------------------------------------------
// THE CIRCLET (v11, user 2026-08-25: "make the crown larger and more gold and
// look more like a crown ... It just looks like a castle with spikes. We can do
// so so so much better").
//
// WHAT WAS WRONG, MEASURED RATHER THAN FELT. Render the old citadel from the
// base arena (`node tools/preview_crown.js`, the `street`/`under` views) and it
// is a 1536-wide blue box with nine narrowing spires on it, standing on a navy
// underside. At the base-arena slant distance of 22,079 units, 1 degree of arc
// is 29.5 px and the legibility floor is about half a degree:
//
//     0.5 deg = 193 units.  1.0 deg = 385 units.  NOTHING NARROWER THAN ~384
//     UNITS CAN CARRY ANY PART OF THE READ FROM THE TOWER.
//
// The old gate spire tip was 20 units (0.05 deg, 1.5 px). The pilaster tip 24.
// The corner-tower tip 40. Six of the nine spires were at or under the vanishing
// threshold — the crown was one 4-degree box with hair on it, which is exactly
// what the user described.
//
// AND THE UNDERSIDE IS 60% OF THE PIXELS. Every sight line from the tower comes
// from the SOUTH and from BELOW, so the near (south) rim occludes the interior,
// the far rim and everything behind them for the whole climb. What a player on
// the street can actually see is three things: the UNDERSIDE, the SOUTH BAND's
// outer face, and the SOUTH RIM's points silhouetted against pure night sky.
// The old underside was MAT.ground (dark_blue_tinted) — almost exactly the
// atmosphere fog colour (_tod_atmosphere.gsc, 0.16 0.14 0.30) — so it rendered
// as a black square. That is why the crown had no pull.
//
// AND YOU CANNOT LIGHT IT. Every crown light is radius 460-900 (see the CL block
// down in the lights section); a 900-unit light does nothing for a 4096-unit
// object. THE EXTERIOR READ IS CARRIED BY MATERIAL, NOT BY LIGHT ENTITIES.
// Light entities up here exist only to make the RED points of the vertical
// axis bloom: the apex beacon, the great ruby, and (v12) the girandole.
//
// THE SHAPE. A rectangular gold circlet CENTRED ON THE HALL, so the play floor
// sits inside it the way a head sits inside a crown — 544 units of clear air on
// the y sides, 960 on the x sides, the band's bottom 832 BELOW the floor and its
// top 640 ABOVE the hall wall tops. The floor, the walls and everything the
// finale stands on DO NOT MOVE (user: "We dont need to edit the floor of the
// room or space"): every constant below is additive, outboard of |x|=HW and of
// y=[HS,HN], and the ring's inner faces clear the hall on all four sides.
//
// WHY A RECTANGLE AND NOT A SQUARE. Width is what you see; depth is invisible.
// A 4096-square ring would put its south rim 2048 in front of centre and bury
// its own monde behind that rim until floor ~35. At CR_HY 1632 the monde clears
// at floor 7 and the finial clears from the ground.
//
// WHY H/width = 1.61 AND NOT THE HERALDIC 1.4. From the base the elevation angle
// is 67 degrees, so vertical extent is foreshortened by cos(67) = 0.39. Building
// the true 1.4 would read as 0.55:1 — a squashed plate — from the street.
// Do not push past 1.7 or it becomes a papal tiara.
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// CR_SCALE — THE ONE KNOB (v11.1, user 2026-08-25: "I want the scale to be even
// more. I want players to be in awe when they see the crown.")
//
// 1.0 was the v11 crown: 4096 wide over the band, and from the base arena that
// is 10.6 deg of arc — big, correct, and not yet awe. At 1.4 the band is 5728
// and the real bounding box is 6128 (the east/west point HEADS stand proud of
// it), 13,888 tall overall: 14.8 deg, and 3.9x the width of the citadel this all
// started from. The generator PRINTS the measured box on every run — read it
// there rather than trusting this comment.
//
// AND 1.4 IS WHERE IT STOPS — FOR DESIGN REASONS, NOT BAKE ONES.
//
// ⚠️ THIS PARAGRAPH USED TO SAY THE OPPOSITE AND IT WAS WRONG. It read: "1.4 is
// where it stops, because the bake said so — the SAME 4,700 brushes bake in
// 38.2 s at 1.0 and 126.2 s at 1.4, 3.3x the time for ~2x the lit area… a step
// to 1.6 would plausibly be 250-300 s or trip brush.cpp:1860." **THE 126.2 s
// READING WAS TAKEN ONCE AND NEVER REPRODUCED.** The same map at 1.4 has since
// baked at 35.1, 31.9 and 31.8 s, and an A/B on byte-identical geometry
// differing only in material distribution came in at 31.3 s. Bake timing on this
// map is dominated by HOST STATE, not by map content, across everything
// measured. Read `_bake_test.ps1` as BAKED/CRASHED and nothing else; for the
// budget question run `node tools/measure_lit_area.js`, which is deterministic.
// Full series in docs/34 §8. (This correction is here because THIS is the file
// the next session reads before changing the crown — leaving the retracted
// number in the docs but not in the generator is how folklore survives.)
//
// The real reason 1.4 is the number: the crown reads correctly at 1.4 and the
// user signed the look off. What DOES constrain further growth is the ROAD —
// the pinned south face is 6912 against cwY[8] = 6880, a 32-unit margin, so any
// further scale-up throws the 5f.1 assert until the causeway is re-cut.
// If area ever does need buying back: `caulk` (noDraw and still solid, stock,
// used in Treyarch's own zm_giant.map source) on buried faces is the untouched
// lever, and it needs a per-face boxFaces() plus a deliberate
// lint_tod_geometry.js material entry.
//
// SCALE UNIFORMLY. Every proportion in the design was derived against the
// heraldic canon and against the 384-unit legibility floor, and the user has
// already signed off on how it LOOKS — so the correct way to make it bigger is
// to multiply, not to re-litigate ratios one at a time. `CS()` is the multiplier;
// it snaps to the 16-grid so nothing lands on a half unit.
//
// TWO THINGS DELIBERATELY DO NOT SCALE:
//   * BAND_T. Band thickness is the DEPTH OF THE TUNNEL the causeway walks
//     through. 320 is already the deepest passage in the map (the hall gate is
//     40); scaling it to 448 would deepen it for no visual gain, since you only
//     ever see the band's face, never its thickness.
//   * The south outer face, CR_S_FACE. It is pinned (see below).
// ---------------------------------------------------------------------------
const CR_SCALE     = 1.4;
const CS = ( v ) => Math.round( v * CR_SCALE / 16 ) * 16;   // scale, then snap to the 16-grid
// THE SOUTH FACE IS PINNED AND THE CROWN GROWS NORTH AROUND IT. The south band
// has to land inside the causeway's F APPROACH — the one stretch that is flat,
// on-axis, 160 wide and at TOP2 — and that stretch is only 800 deep, so there
// was no room to grow southward at all: at CR_HY 1632 the old ring was already
// within 32 units of the J4 merge. So the crown is no longer centred on the
// hall. It is anchored to the ROAD, and CR_CY floats north as it grows. Nobody
// can ever see that: every sight line is from the south, depth is invisible,
// and the hall's own walls occlude the ring's inner faces from inside.
const CR_S_FACE    = 6912;                      // south outer face (ermine) — PINNED to the road
const CR_HX        = CS(2048);                  // half-width  x  (2864 -> 5728 across the band at 1.4)
const CR_HY        = CS(1632);                  // half-depth  y  — see the road assert in 5f.1
const BAND_T       = 320;                       // ring wall thickness — NOT scaled, see above
const CR_CHAM      = CS(512);                  // true diagonal corner depth
const CR_ERM       = CS(64);                    // how far the ermine rim stands proud of the band
const CR_CY        = CR_S_FACE + CR_ERM + CR_HY;   // derived: the south face cannot move
// The vertical schedule, all relative to TOP2. The ratios these land on are the
// St Edward's canon to within 2% (band top 0.20 H, fleurs 0.44, crosses 0.55,
// arch springing 0.55, arch crown 0.72, monde centre 0.80, finial 1.00) — that
// is the point of the numbers, not something to tune away.
const CR_SKIRT_BOT = CS(-3136);                 // glowing core, the bottom of the velvet cap
const CR_ERM_Z1    = CS(-832), CR_ERM_Z2 = CS(-576);  // the ermine rim: the widest line in the silhouette
const CR_C1_Z      = CS(-40);                   // C1 spans CR_ERM_Z2 -> here (all of it below the road)
const CR_C2_Z      = CS(160), CR_C3_Z = CS(384), CR_C4_Z = CS(640);
const CR_RIM_Z     = CS(704);                   // top of the rim strip — above this there is ONLY sky and points
const CR_SHORT_TOP = CS(2112);                  // fleur-de-lis heads
const CR_TALL_TOP  = CS(2880);                  // crosses pattee — also the arch springing
const CR_FRONT_TOP = CS(3456);                  // the FRONT CROSS: taller than its neighbours
const CR_ARCH_CROWN= CS(3840);                  // where the two dipped arches meet the monde
const CR_MONDE_Z2  = CS(4864);
const CR_FINIAL_Z2 = CS(5760);
const CR_BEACON_Z2 = CS(6784);                  // the red star over the crown, visible from the base arena
const CROWN_TOP    = TOP2 + CR_BEACON_Z2;
const CROWN_BOT    = TOP2 + CR_SKIRT_BOT;
// The mouth: the causeway walks THROUGH the rim before it reaches the hall gate.
// Z IS DERIVED FROM THE BAND, NOT WRITTEN DOWN: the mouth is exactly courses C2
// and C3, so it can never drift out of the band as the schedule scales. The
// scale-up is a straight win here — the opening grows from 640x424 to 896x592.
const CR_MOUTH_HALF = CS(320);
const CR_MOUTH_Z1  = CR_C1_Z, CR_MOUTH_Z2 = CR_C3_Z;   // C1 and C4 stay continuous
// Outer envelope, INCLUDING the proud ermine — everything downstream derives
// from these two rather than from a literal.
const CR_OUT_X     = CR_HX + CR_ERM;            // 2112
const CR_OUT_Y     = CR_CY + CR_HY + CR_ERM;    // 10304 (north face, odd frame)

// ---------------------------------------------------------------------------
// THE AMMO CRATE — ONE CONTRACT FOR EVERY CRATE IN THE MAP
// (v17.37 facing, v17.38 the rest; user 2026-09-04: "Lets do this one run and
// master ammo crates so we dont ever have to touch them again")
// ---------------------------------------------------------------------------
// A crate is FOUR things and every one of them is derived from ONE origin and
// ONE yaw, here: the facing, the occupancy box (its collision), the use
// trigger, and the model. Base, the four breathers, the crown, the spire arena,
// every spire shelf and every spire hub read this block — there is no other
// crate recipe, and _tod_ammo_crate.gsc reads the trigger numbers back out of
// GENERATED _tod_breather_data.gsc (crate_trig_out / crate_trig_r), so the
// script cannot drift from the table that asserts it.
//
// FACING. west_ammo_crate_model's FRONT is the mesh's local -right, i.e.
// yaw + 90 — not the yaw - 90 every tower crate was authored against. v14.23
// already ran this experiment on the spire: the user's answer to "which crates
// face wrong" was "All of them", so all four spire yaws were flipped 180 and
// that entry closed with "verify by eye next run and record the winning
// convention at BR_FURN". The 2026-09-04 report ("Pap and ammo crate are not
// facing the center of the crown room" — the crown crate being a
// tower-convention crate on an EAST wall at yaw 270) was that verification.
const CRATE_YAW_N = 0;      // front = world +y — a crate whose wall is SOUTH of it
const CRATE_YAW_W = 90;     // front = world -x — wall EAST of it
const CRATE_YAW_S = 180;    // front = world -y — wall NORTH of it
const CRATE_YAW_E = 270;    // front = world +x — wall WEST of it
function crateFront(yaw) {
  const y = ((yaw % 360) + 360) % 360;
  if (y === CRATE_YAW_N) return [0, 1];
  if (y === CRATE_YAW_W) return [-1, 0];
  if (y === CRATE_YAW_S) return [0, -1];
  if (y === CRATE_YAW_E) return [1, 0];
  throw new Error(`crateFront: crate yaw ${yaw} is not one of the four cardinal CRATE_YAW_* values`);
}
// OCCUPANCY. The mesh is NOT centred on its origin: at CRATE_YAW_E it occupies
// x[-37,+38] y[-19,+45] (measured, zeroy_s4_ammo_crate at SetScale 2.5) — 13u
// off-axis along its wide side. The other three yaws are that box rotated about
// the origin, so every "ammo crate body" clip in the map is the mesh's real
// footprint at its real yaw. THEY DISAGREED BEFORE: the v14.23 flip turned four
// spire yaws and left every box at the yaw-270 occupancy (26u off the mesh),
// and the spire arena crate carried a script-clip row that ran FRONT-TO-BACK
// through the crate (AnglesToRight is the front at these yaws), planting an
// invisible lip in front of the face that held the player out of the trigger.
// 2026-10-04 (docs/208): THE AMMO BOX V6 (Nikolai's, map 1's v19.69b) on every crate. Its case is
// 98 across, CENTRED (y +-49 at CRATE_YAW_E; the old crate's 13u off-axis is gone), 37 behind the
// origin to 33 in front, 29.4 tall (map 1 art/fan_props/manifest.json "chest": the case's back edge
// at -37, its front at +32.19, rounded out). The facing convention is unchanged.
function crateBox(cx, cy, yaw) {
  const y = ((yaw % 360) + 360) % 360;
  const E = { x1: -37, x2: 33, y1: -49, y2: 49 };   // tod_ammo_chest (Ammo Box V6) at CRATE_YAW_E (was zeroy_s4 x[-37,38] y[-19,45])
  let b;
  if (y === CRATE_YAW_E)      b = E;
  else if (y === CRATE_YAW_W) b = { x1: -E.x2, x2: -E.x1, y1: -E.y2, y2: -E.y1 };   // 180: (x,y) -> (-x,-y)
  else if (y === CRATE_YAW_N) b = { x1: -E.y2, x2: -E.y1, y1: E.x1,  y2: E.x2  };   // +90 CCW: (x,y) -> (-y,x)
  else if (y === CRATE_YAW_S) b = { x1: E.y1,  x2: E.y2,  y1: -E.x2, y2: -E.x1 };   // -90:     (x,y) -> (y,-x)
  else throw new Error(`crateBox: crate yaw ${yaw} is not one of the four cardinal CRATE_YAW_* values`);
  return { x1: cx + b.x1, x2: cx + b.x2, y1: cy + b.y1, y2: cy + b.y2 };
}
// The clip is the case's own height (docs/208): the V6 is 29.4 tall, and a 58-tall clip over it
// would be an invisible ledge a body stands on 29 units above the box - the perch map 1 had to cap
// (its v19.71). A 30-tall top is one a zombie still swings at, and every crate trigger's origin
// (crate_trig_out in front, +40 up) stays clear over it from the front and both sides.
const CRATE_BOX_H = 30;     // occupancy height above the crate's floor (V6: 29.4)
// THE TRIGGER (v17.38, user: "check the trigger on all ammo crates. Some of them
// are off and you cant get ammo unless at a certain angle"). Every crate used
// to spawn its trigger_radius_use ON the model origin with radius 72 — and the
// occupancy box holds a player's origin >= 38 + ~16 (capsule) = 54u from that
// origin, so the usable band in front of the face was 54..72: EIGHTEEN UNITS,
// and only along the face's centre line. Stand naturally, or a little off-axis,
// and there was no prompt; the spire arena crate's invisible lip made it worse.
// The trigger now sits CRATE_TRIG_OUT in front of the origin — the stations'
// and PaP machines' own grammar (BR_FURN.pap/station trig = org + 56) — so the
// band runs from the face to ~128u out and ±72 across it. Radius unchanged.
const CRATE_TRIG_OUT = 56;
const CRATE_TRIG_R = 72;
function crateTrig(org, yaw) {
  const f = crateFront(yaw);
  return [org[0] + f[0] * CRATE_TRIG_OUT, org[1] + f[1] * CRATE_TRIG_OUT];
}

// Sky enclosure (the SEAL)
// v9: widened 1900 -> 2900 for the crown hall (outer face at y=2656 in either
// frame) and raised to clear the mast tip + corner needles.
// v10: the long causeway pushes the hall's outer face to y=HN (8416 at
// CW_LEN 6400), so the seal has to clear it. DERIVED, not a literal — a future
// CW_LEN change must never be able to leave the hall outside the skybox, which
// would be a hole in the world rather than a cosmetic bug. Symmetric on both
// axes because CM mirrors the whole crown to -y on an even crown lap.
// v11: it now has to clear THE CIRCLET too, and that was a real trap rather
// than a hypothetical one. SKY_IN tracked HN in Y ONLY and SKY_TOP tracked the
// MAST ONLY, and the two asserts further down test the CAUSEWAY, never the
// crown — so the old seal had 620 units of headroom above the corner-tower tips
// and nothing whatsoever would have fired when the beacon needle went 4564
// units through the roof of the world. Both are max()'d over the crown now, and
// section 5f asserts the crown against them.
const SKY_IN = Math.max(2900, HN + 384, CR_OUT_Y + 512, CR_OUT_X + 512), SKY_TH = 32;
// The sky floor sits under the UNDERCITY now (docs/158): the Vault, the Conduit
// and the shaft foot are at UC_Z (-384) with 16-thick slabs, so the seal has to
// be below -400 or the sky floor slab would cut straight through the shaft.
const SKY_FLOOR = UC_Z - 128, SKY_BOT = SKY_FLOOR - 32;   // -512 / -544
// Derived from everything under it (the crown, the mast), never a literal. (The Endless Spire
// once fed this max() too; it was removed 2026-09-29 and never set the ceiling: the floor below did.)
// ⚠️ THE SKY SEAL / SUN VOLUME MUST NEVER SHRINK BELOW THIS (v17.80, 2026-09-05, docs/107).
// SKY_TOP sizes BOTH the sky enclosure and the `volume_sun` brush (the map-wide sun / light-grid
// volume, grid_density 32). It used to be governed by whatever was tallest, and when v17.69 cut the
// spire from 100 to 70 laps the spire term fell from 39,168 to 27,648, CROWN_TOP (28,896) took
// over, and SKY_TOP dropped from 39,468 to 29,196 — 10,272 units. From that build on THE WHOLE
// TOWER READ YELLOW-OLIVE: every surface, the viewmodel and the zombies lit by a warm light that
// honoured the base lights' POSITIONS but not their colour or their lighting state (authored OFF
// before power), i.e. the engine on default light parameters. Six builds of sky / sun / light /
// fog / vision / dev-flag reverts changed nothing because none of those had changed. Proof:
//   - v17.79: this floor at 39,168 + a from-nothing .led  -> DARK at the crate (published look);
//     .led 45,041,494 B.
//   - v17.80 bisect: floor 0 + a from-nothing .led        -> the crash-era .led size again,
//     44,592,078 B, byte-identical to every yellow bake; deletion of the .led was NOT the fix.
//   - the control map (Repositories/test+map) bakes clean on this host, so it is not the tools.
// The published v17.58 build had the 100-lap spire and therefore this height by accident. The
// mechanism inside Radiant is not known (a light-grid partition of the volume is the likely lane);
// the RULE is empirical and cheap: hold the floor. If the geometry ever grows past it, max() wins.
const SUN_VOLUME_TOP_MIN = 39168;
const SKY_TOP = Math.max(MAST_TOP, CROWN_TOP, SUN_VOLUME_TOP_MIN) + 300;
const BARRIER_TOP = SKY_TOP - 300;   // THE INVISIBLE BARRIER's top (2026-09-26): every clip wall runs to here - under the umbra/fpstool lid (SKY_TOP - 200) and inside the crown bbox assert (z2 + 256 <= SKY_TOP)

// Neon palette, cycled per lap (ALL names verified in the installed
// emox_mwiii_vertigo_assets.gdt 2026-08-17/18).
const PALETTE = [
  { key: 'cyan',   light: '0.35 0.9 1' },
  { key: 'purple', light: '0.66 0.35 1' },
  { key: 'pink',   light: '1 0.35 0.8' },
  { key: 'green',  light: '0.35 1 0.6' },
  { key: 'orange', light: '1 0.6 0.25' },
  { key: 'yellow', light: '1 0.95 0.35' },
  { key: 'red',    light: '1 0.3 0.3' },
  { key: 'blue',   light: '0.35 0.55 1' },
];
// ---------------------------------------------------------------------------
// v16.11 — THE TOWER FACELIFT (user 2026-09-01: "Look into overall design
// enhancement we can make to the tower physical appearance ... Lets do the
// first 4" of the ranked review, artifact "Cybercity Tower Facelift"):
//   1. DISTRICT PALETTE (here)     colour means height
//   2. DOOR GATES THAT OPEN         post + lintel + sill per lap door, the slab
//                                   in the district it opens into; the slab
//                                   SLIDES into the core on purchase
//                                   (_tod_doors.gsc TOD_DOOR_SLIDE)
//   3. BASE PLAZA + WAYFINDING      floor traces spawn -> first door / power
//                                   hall, a foot ring under the core, cyan
//                                   pilasters + cornice on the arena walls
//   4. TELEPORT BAY COLOUR CODE     each up pad wears its destination lounge's
//                                   colour (pad square + light)
// ONE SWITCH, FACELIFT, gates all four geometry halves (same construction as
// BR_POLISH): false regenerates the v16.7 map byte-for-byte (proven by md5
// when the switch was added). Flipping it is a regen + FULL build. The script
// half (the slide) has its own TOD_DOOR_SLIDE define.
//
// 1. DISTRICTS. The old scheme cycled treads/parapets/core through the 8-entry
// PALETTE per lap and landings through 5 edge hues, so the same colour never
// meant the same height and the two cycles only realigned every 40 floors.
// Now five districts of DISTRICT_LAPS floors, each ONE hue family, in the
// order the breather lounges ALREADY wear (BREATHER_THEME: 10 blue, 20 green,
// 30 orange, 40 gold) — the lounge is the district's culmination — and RED
// for 41-50, the map's danger colour, for the ten hardest floors under the
// gold crown (no lounge up there; the spire is red too but on black with
// different bones). These five are exactly the five hues the pack ships as
// `_tinted_edge` landing tiles, so nothing new is needed. The core band per
// lap takes the district colour too: from the base the tower reads as five
// stacked bands, and the lap lights follow lapPal for free.
// RHYTHM inside a district — laps must still differ from their neighbours:
// treads (and the core band) alternate `_tinted` on odd floors and
// `_tinted_edge` on even floors. NOT the parapets: a `_tinted` parapet is a
// 56-tall `_tinted` slab, which lint_tod_geometry classes as a walkable DECK
// (<= MAX_SLAB) and would flag hundreds of false unguarded edges; parapets
// stay plain hue (BLOCK). The end landing of lap L already wears lap L+1's
// colour (edgeMatOf(lap + 1) below), so at a district boundary the landing
// where you buy the next door is the FIRST thing in the new colour — the
// "one more floor" tell for free.
// ---------------------------------------------------------------------------
const FACELIFT = true;
const DISTRICT_LAPS = 10;
const DISTRICTS = [
  { key: 'blue',   light: '0.35 0.55 1' },   // floors  1-10 — the base arena's blue; lounge 10
  { key: 'green',  light: '0.35 1 0.6'  },   // floors 11-20 — lounge 20
  { key: 'orange', light: '1 0.6 0.25'  },   // floors 21-30 — lounge 30
  { key: 'yellow', light: '1 0.85 0.35' },   // floors 31-40 — lounge 40, the crown's gold foreshadowed
  { key: 'red',    light: '1 0.3 0.3'   },   // floors 41-50 — danger; the last ten under the crown
];
// lap is 0-based; lap 50 (edgeMatOf(lap + 1) on the last lap, the crown's
// own lap index) clamps to the last district.
function districtOf(lap) { return DISTRICTS[Math.min(DISTRICTS.length - 1, Math.max(0, Math.floor(lap / DISTRICT_LAPS)))]; }
function lapPal(lap) { return FACELIFT ? districtOf(lap) : PALETTE[lap % PALETTE.length]; }
function stepMatOf(lap) {
  if (!FACELIFT) return `mwiii_vertigo_retro_synth_${lapPal(lap).key}_tinted`;
  return `mwiii_vertigo_retro_synth_${districtOf(lap).key}_${lap % 2 === 0 ? 'tinted' : 'tinted_edge'}`;
}
function paraMatOf(lap) { return `mwiii_vertigo_retro_synth_${lapPal(lap).key}`; }
// TRON GRID floors (user 2026-08-20 design pick): dark tiles with GLOWING
// SEAMS — the pack's `_tinted_edge` family (only blue/green/orange/red/
// yellow exist). Pre-facelift: cycled per lap on landings + breather balconies;
// facelift: the district hue.
const EDGE_COLORS = ['blue', 'green', 'orange', 'red', 'yellow'];
function edgeMatOf(lap) {
  if (!FACELIFT) return `mwiii_vertigo_retro_synth_${EDGE_COLORS[lap % EDGE_COLORS.length]}_tinted_edge`;
  return `mwiii_vertigo_retro_synth_${districtOf(lap).key}_tinted_edge`;
}

// DOOR SLABS ONLY (v18.99g). Same hue ladder as edgeMatOf, but the matte clones
// — see MAT.door's note and tools/gen_tod_door_materials.js. This exists as its
// own function precisely so the swap CANNOT leak onto the landings, breather
// floors, terrace, causeway deck or extraction pad, which are edgeMatOf's other
// callers and are supposed to keep their wet-neon reflection.
// LOCKSTEP: the five names here are generated from DISTRICTS, are declared in
// source_data/tod_materials.gdt, and are classified BLOCK in
// tools/lint_tod_geometry.js — a name missing from any of those three is a
// silent linker substitution, i.e. a white square nobody warns you about.
function doorMatOf(lap) {
  if (!FACELIFT) return MAT.door;
  return `tod_door_${districtOf(lap).key}`;
}

// ---------------------------------------------------------------------------
// v17.28 — FLOOR 1 GOES BLACK (Workshop, Nikolai 2026-09-04): "the walls all
// have the black and blue grid ... remove the blue only on the first floor and
// just make it consistently that black and blue grid checker (only leave the
// green buyable doors and blue buyable door) ... right now the blue wrapping
// around it makes it a little more difficult to see which blue is the buyable
// door ... add that black and blue checker to the bottom part of the column of
// the tower outside where the blue purchasable door is."
//
// HE IS DESCRIBING A MEASURABLE FACT, not a taste. The whole vertigo pack is
// TWO textures and one brightness number (read out of
// emox_mwiii_vertigo_assets.gdt, 2026-09-04):
//
//   <colour>              i_..._e         BLACK tiles + a thin bright grid line, scaleRGB 15
//   <colour>_tinted       i_..._tinted_e  FILLED tiles glowing at the seams,   scaleRGB 10
//   <colour>_tinted_edge  i_..._tinted_e  the SAME texture and the SAME tint,  scaleRGB 5
//
// So `_tinted_edge` is not an "edge" variant of anything — it is `_tinted` at
// HALF BRIGHTNESS. (The old comment on edgeMatOf calling it "dark tiles with
// GLOWING SEAMS" described the texture both share.) That single fact explains
// the report: at ground level the arena FLOOR was `dark_blue_tinted` (filled,
// 10) and the core's lap-1 band `blue_tinted` (filled, 10), while the buyable
// door slab is `blue_tinted_edge` (filled, 5) — the door is the SAME TEXTURE
// and roughly the same hue as everything around it, at HALF the brightness of
// the wall it is cut beside. It is the dimmest blue in a room full of brighter
// blue, which is exactly backwards.
//
// The fix is his: ground level drops to the PLAIN family (black tiles + a blue
// grid line), so the only FILLED blue left down there is the lap-1 door slab
// and the 1-10 teleport pad it is colour-matched to. Green keeps the power and
// teleport-bay doors. Nothing above floor 1 changes.
//
// ONE SWITCH, BASE_GRID, so the whole look A/Bs in one edit; false regenerates
// the pre-v17.28 base exactly.
//
// ⚠️ THE FLOOR MATERIAL IS LOAD-BEARING FOR lint_tod_geometry.js, which classes
// DECK vs BLOCK by MATERIAL NAME and HARD-FAILS on a name it does not know.
// Every plain `<colour>` in its table is BLOCK (parapets, rails, base walls),
// so handing the arena floor a plain material the lint already knew would have
// deleted the floor from its walkability model and reported the whole map as
// unreachable. `dark_blue` is used NOWHERE ELSE in this map, so it can be added
// there as DECK with a one-to-one meaning — which is the lint's own rule that
// a material's class is derived from the labels that use it. Pick a plain
// colour that is already in service for something else and that rule breaks.
const BASE_GRID = true;
// How many core bands from the ground wear the floor's grid material. Band 0 is
// z 0..384 and carries the floor-1 door; band 1 is z 384..768 and carries the
// floor-2 door. Two puts the change-over above the arena walls (128) and out of
// the eyeline from the spawn, and leaves the column visibly standing ON the
// black grid it is lit against. The four plain-hue SPINES are untouched, so the
// column keeps its four vertical lines all the way up.
const BASE_GRID_LAPS = 2;

// THE DARK HALL (2026-09-24, docs/164; user, on four questions: "near-black,
// pools of light" / "keep edge lines only" / "darken the sky too" / "crown hall
// first"). ONE switch: the crown hall's INTERIOR faces go to the matte
// plain-grid clones (tod_dark_*, made by tools/gen_tod_door_materials.js — black
// tiles, one thin line per edge, no mirror, line at scaleRGB 8, albedo 0.5) and
// its lights become a few tight pools on all four lighting states (the crown
// light block). false = the v16.35 basilica look, for a bisect. The circlet
// OUTSIDE the hall keeps its gold either way; the sky (source_data/tod_skybox.gdt
// skyStops + the EXR's target score) is the other half of the pass and is
// global.
const DARK_HALL = true;

// THE BLACKOUT (2026-09-25, user: "the map should be dark and it should be
// really dark ... the only thing that brings light or that you can see pretty
// well is maybe the sky and then once power's on things will light up
// dynamically"; on three questions: ALMOST PITCH BLACK / REMOVE THE GLOW
// EVERYWHERE / A WAVE DOWN THE TOWER). Three switches, all here:
//   BLACKOUT          every face's vertigo material (and the tod_dark_* hall /
//                     tod_door_* clones) is swapped AS THE .map IS WRITTEN for its
//                     no-glow clone tod_black_<suffix> (tools/tod_black_materials.json;
//                     GDT blocks from tools/gen_tod_door_materials.js). World
//                     emission cannot switch with the power, so it is gone; the
//                     powered look is the LIGHTS. The trial halls' art plates
//                     (tod_hall_*, the parked spire) are left alone.
//   LIGHTS_AT_POWER   every light entity is lightingstate1 ONLY (Radiant State 1
//                     = script state 0). The map boots in Radiant State 2 —
//                     PROVEN by the user's 2026-09-25 log ([TOD_LIGHTSTATE]
//                     level=1 player=1 at spawn, blackscreen and power) — so
//                     every light is OFF until _tod_fall's power wave calls
//                     util::set_lighting_state( 0 ).
//   SSI_PREPOWER      the sun volume's ssi2 (the boot state) is a darker clone of
//                     the night SSI (sun -3 stops); ssi1 (powered) is unchanged.
// The sky's own light on the world is `skyStops` in source_data/tod_skybox.gdt
// (6 -> 4 in the same pass, -> 1 after the user's second look); the visible sky
// keeps sky_intensity_factor 6.5. The dark SSI's sun: -5.2, then -7.2.
const BLACKOUT = true;
const LIGHTS_AT_POWER = true;
const SSI_PREPOWER = 'tod_ssi_cybercity_dark';
// "a bit too dark with the power off ... and when the power's on it's still a
// little bit too dark ... probably 25% lighter" (user, after the 11:43 build,
// which they liked otherwise: "keep it how you have it"). 25 % = log2(1.25) =
// +0.32 stops, on EVERY light source at once so the look keeps its balance:
// every placed light (here), skyStops 1.0 -> 1.32 and both SSIs' sun +0.32
// (source_data/tod_skybox.gdt).
// 2026-09-25 17:00 (user: "still too dark ... exaggerate and ramp it up just so I can see that it changes. I want to see a lot of light"): 0.32 -> 1.32 (x2 more per light).
// 2026-09-25 21:45 (user: "the map is a bit too light now ... we definitely did [overdo it] ... tone it back a little bit more"): HALF the 17:00 move, 1.32 -> 0.82 (the recorded pull-back plan; exposure halved in the same pass, source_data/tod_skybox.gdt).
// 2026-09-25 22:20 (user, after playing the 22:03 build: "it was still a little bit too bright"): half again, 0.82 -> 0.57 (dark SSI ev 2.5/3 sun -4.8, powered ev 2.75/3.25, skyStops 2.85 in the same pass — a quarter of the 17:00 move is left).
const LIGHT_STOPS_ADD = 0.57;
// The crown's Pack-a-Punch / item-shop light pools (see THE VENDOR POOLS in the hall block). false = removed (user 2026-09-25 21:45).
const CROWN_VENDOR_LIGHTS = false;
// THE ALARM LIGHTS THE HALL (user 2026-09-25: "when you activate the alarm
// system in the crown, then the crown lights turn on. Which is different from
// the power being turned on for the whole map ... so you can actually see while
// you're fighting. And the item shop won't turn on ... all that is activated
// by the power switch"). A THIRD LIGHTING STATE: Radiant State 3 = script state
// 2 = the dark map with ONLY the crown hall's lights (mask 'alarm' = states 1
// and 3). The boot state (Radiant 2) has none; the powered state (Radiant 1)
// has every light. volume_sun ssi3 = the dark SSI (the sky and sun stay the
// pre-power ones until the power). _tod_fall's flood() calls
// util::set_lighting_state( 2 ); the power wave ends on state 0 as before.
// Which lights: HALL_ALARM_LIGHTS below (the hall's pools + the fill grid; NOT
// the shop pools, the balcony or the overlook — they are the power's).
const HALL_ALARM_LIGHTS = /^tod light (crown gate|shrine [WE]|hall (reredos|dais|spawn|fill \d\d)|extraction|hallway (junction|east|power))$/;   // the hallway three (2026-09-25): the power must be findable in the dark

const MAT = {
  // NOT the base floor — `ground` is also the tower shell, the crown hall floor
  // and the spire's base slab (see every MAT.ground call site). Floor 1 has its
  // own entry below precisely so those three do not follow it.
  ground: 'mwiii_vertigo_retro_synth_dark_blue_tinted',   // TRON GRID: navy tiles (was grey asphalt)
  // GROUND LEVEL ONLY: the arena slab, the power-hall floor and the teleport-bay
  // floor. `dark_blue` is the exact plain twin of `dark_blue_tinted` — same
  // tint (0.067 0.198 1), grid texture instead of filled — so this is literally
  // "keep the colour, drop the fill".
  // v17.32: `blue` (0.373 0.727 1), not `dark_blue` (0.067 0.198 1) — user asked
  // for the lighter tint. ⚠️ BE CLEAR WHAT THIS DOES: both are the SAME plain
  // texture at the SAME scaleRGB 15, and that texture is ~96% black, so the tint
  // only recolours the thin GRID LINE. It lifts the lines from deep blue to pale
  // sky blue; it does NOT make the tiles less black. The room's brightness comes
  // from BASE_LIGHT_BAKE below, not from here — an earlier note in this session
  // listed the two as alternative brightness knobs and that was wrong.
  baseFloor: BASE_GRID ? 'mwiii_vertigo_retro_synth_blue' : 'mwiii_vertigo_retro_synth_dark_blue_tinted',
  // THE COLUMN'S PLINTH STAYS THE DARKER TINT and no longer shares the floor's
  // material. It has to: the core's four SPINES are paraMatOf(lap) = plain
  // `blue` for district 1, so a plinth in plain `blue` would be the same material
  // as the spines standing in it and the four vertical lines would vanish for the
  // first two bands. `dark_blue` keeps the plinth reading behind them.
  baseColumn: BASE_GRID ? 'mwiii_vertigo_retro_synth_dark_blue' : 'mwiii_vertigo_retro_synth_blue_tinted',
  // THE WAYFINDING GLOW MOVES OFF BLUE. The inlay ring, the three power/door
  // traces and the core foot ring were `blue_tinted_edge` — byte-identical to
  // the lap-1 door slab, so the one thing on the floor that is supposed to say
  // "the way through" was drawn in the door's own material. Cyan is already the
  // arena's accent (pilasters + cornice) and it is a hue the spiral never uses
  // for a district, so at ground level cyan now means "this room" and blue means
  // "the way up". `cyan_tinted` is deliberate: the pack ships NO
  // `cyan_tinted_edge` (30 materials, verified) and the linker substitutes an
  // invented name silently. It is also brightness 10 against the old 5, so the
  // traces read BETTER on the darker floor, not worse.
  baseInlay: BASE_GRID ? 'mwiii_vertigo_retro_synth_blue_tinted' : 'mwiii_vertigo_retro_synth_blue_tinted_edge',
  baseWall: 'mwiii_vertigo_retro_synth_blue',
  pilaster: 'mwiii_vertigo_retro_synth_cyan',              // v16.11 facelift: arena wall pilasters + cornice (the crown fascia's cyan)
  landing: 'mwiii_vertigo_retro_synth_dark_white',        // fallback only — landings now use edgeMatOf(lap)
  roofFloor: 'mwiii_vertigo_retro_synth_pap',             // the payoff floor under PaP
  roofPara: 'mwiii_vertigo_retro_synth_yellow',
  // BUYABLE DOORS — GLOWING GREEN SEAM (user 2026-08-27: "making the doors more
  // obvious to buy. They look quite similar to the walls ... see if we have a
  // wall in that same pack that can be used").
  //
  // WHY THE OLD FLAT RED FAILED, measured rather than guessed:
  //   * the wall a door is set into is the CORE BAND, stepMatOf(lap) =
  //     `<PALETTE>_tinted`, and PALETTE cycles EIGHT colours — one of which is
  //     RED. On lap % 8 == 6 the door was red-on-red against its own wall, i.e.
  //     6 of the 50 floors.
  //   * every landing and balcony is `_tinted_edge` (glowing seams), so a flat
  //     door was the ONLY major surface in the map with no glow at all. It did
  //     not read as a door; it read as wall.
  //
  // A FIXED HUE CANNOT SOLVE THIS — with eight wall colours cycling, whatever
  // colour the door takes, one lap in eight matches it. So the door has to
  // differ in KIND, not in hue: `_tinted_edge` makes it the only VERTICAL
  // glowing-grid surface in the map, on every lap, against flat `_tinted` walls.
  //
  // GREEN because this map already speaks it: exfilPad below is
  // green_tinted_edge, so green already means "the way through". Green is also
  // the universal buyable convention. Residual: the wall is green_tinted on
  // lap % 8 == 3, so on 6 floors the HUE matches — but the door still carries a
  // seam grid the wall does not, which is the read that was missing before.
  //
  // Same pack (emox_mwiii_vertigo_assets), so the theme is untouched. NOTE the
  // `_tinted_edge` family exists ONLY for blue/green/orange/red/yellow — the
  // geometry lint will not catch an invented name, the linker just substitutes.
  // v18.99g THE DOOR IS MATTE NOW (user 2026-09-13: "fix this door. It has a
  // reflection bug"). tod_door_green is a byte-for-byte clone of
  // green_tinted_edge — same texture, same tint, same scaleRGB 5 — with its
  // specular and reflection-probe response zeroed, because every material in
  // the vertigo pack is configured as a polished flat mirror (white albedo,
  // 97%-white gloss map, no normal map, reflectionProbeAmount 1) and a door
  // slab is the largest, dimmest, flattest surface in the room, so the
  // reflection won. Generated by tools/gen_tod_door_materials.js — READ ITS
  // HEADER before touching door materials; it also records the separate,
  // still-open probe-box bug. doorMatOf() below is the one selector.
  door: 'tod_door_green',
  clip: 'clip',
  // the stair ramp wedges (tower, crown, causeway, spire) — plain clip since
  // v16.61a so ZOMBIES climb the slope too; see the STAIR RAMP CLIP block up in
  // the constants (and why not metal_clip: the lit-area tool).
  rampClip: 'clip',
  // player-only clip for the breather lounges' window voids: bullets and
  // zombies pass, players stay in. Was MAT.rampClip until v16.61a split them.
  winClip: 'clip_player',
  sky: 'sky',
  // --- the crown (v9) ---
  crownStep: 'mwiii_vertigo_retro_synth_yellow_tinted',        // the last flight is GOLD — you can see the prize
  crownBand: 'mwiii_vertigo_retro_synth_pap',                  // the core's capital block
  crownRing: 'mwiii_vertigo_retro_synth_yellow_tinted_edge',   // glowing inlay ring on the deck
  crownFascia: 'mwiii_vertigo_retro_synth_cyan',               // cornice: the crown glows from 19000 units down
  exfilPad: 'mwiii_vertigo_retro_synth_green_tinted_edge',     // the way out
  // --- THE CIRCLET (v11) — a GOLD VALUE LADDER, not one flat yellow ---------
  // "More gold" is not "everything gold": gold only reads as gold against a
  // dark foil. Target proportions on the exterior are roughly 60% gold, 25%
  // velvet/brass, 10% white, 5% jewel. The old citadel was ~70% blue.
  // Every name below was checked against the installed
  // emox_mwiii_vertigo_assets.gdt on 2026-08-25 — that pack has 30 materials
  // and NO metal, so the ladder is built out of value, not out of a shader.
  // Beware: `_tinted_edge` exists ONLY for blue/green/orange/red/yellow (there
  // is no purple_tinted_edge and no cyan_tinted_edge), and the geometry lint's
  // colour loop would happily pass a name the linker then substitutes.
  crownGold: 'mwiii_vertigo_retro_synth_yellow',               // BRIGHT gold: points, arches, finial, rim strip
  crownGoldPanel: 'mwiii_vertigo_retro_synth_yellow_tinted',   // gold panel (#e3cd3b): the band courses
  crownBrass: 'mwiii_vertigo_retro_synth_orange_tinted',       // old brass (#ed871a): the dark foil the gold reads against
  crownGoldSeam: 'mwiii_vertigo_retro_synth_yellow_tinted_edge', // glowing gold seam: inlays only
  crownVelvet: 'mwiii_vertigo_retro_synth_purple_tinted',      // the cap under the floor, and the hall walls
  // ERMINE — the white fur roll at the bottom of the band, and the single
  // strongest read from the base arena (a bright annulus at the widest point of
  // the silhouette). NOTE: `white` is NOT in lint_tod_geometry.js's material
  // table by default; it was added there deliberately as BLOCK in this same
  // change, because an unclassified material is a HARD ABORT of the build gate.
  crownErmine: 'mwiii_vertigo_retro_synth_white',
  // the ermine's dark tails. `dark_white` is a neutral 0.188 grey (measured
  // value 2.8 against the ermine's 13.1) — the pack's only real dark short of
  // `off`, which is scaleRGB 0 and would read as a hole punched in the crown
  // against a night skybox rather than as fur. Added to lint_tod_geometry.js's
  // material table as BLOCK in the same change.
  crownErmineSpot: 'mwiii_vertigo_retro_synth_dark_white',
  jewelRuby: 'mwiii_vertigo_retro_synth_red_tinted_edge',
  jewelSapphire: 'mwiii_vertigo_retro_synth_blue_tinted_edge',
  jewelEmerald: 'mwiii_vertigo_retro_synth_green_tinted_edge',
  // THE DARK HALL (DARK_HALL above): the hall's interior only. Each falls back
  // to the material that face wore before the pass, so the switch is a bisect.
  hallFloor: DARK_HALL ? 'tod_dark_floor' : 'mwiii_vertigo_retro_synth_dark_blue_tinted',   // = MAT.ground before
  hallStep:  DARK_HALL ? 'tod_dark_step'  : 'mwiii_vertigo_retro_synth_yellow_tinted',      // sanctuary tiers (crownGoldPanel before); the dais was crownRing
  hallWall:  DARK_HALL ? 'tod_dark_wall'  : 'mwiii_vertigo_retro_synth_purple_tinted',      // = crownVelvet before
  hallGold:  DARK_HALL ? 'tod_dark_gold'  : 'mwiii_vertigo_retro_synth_yellow',             // = crownGold before
  hallRuby:  DARK_HALL ? 'tod_dark_ruby'  : 'mwiii_vertigo_retro_synth_red_tinted_edge',    // = jewelRuby before (pier shafts only)
  hallBrass: DARK_HALL ? 'tod_dark_brass' : 'mwiii_vertigo_retro_synth_orange_tinted',      // = crownBrass before
};
// THE ONE MATERIAL RULE ON THE CROWN, and it is a build gate, not taste:
// lint_tod_geometry.js classifies `_tinted` / `_tinted_edge` as DECK and calls
// any DECK brush <= MAX_SLAB (64) thick IN Z a walkable floor. A 48-thick gold
// moulding 19,000 units in the air would become a floor node with no guard on
// any edge, and the baseline is `unguardedEdges: 0`. So:
//   ANY HORIZONTAL ELEMENT 64 UNITS THICK OR THINNER MUST USE A PLAIN COLOUR.
// That is why the rim strip and every fillet below are MAT.crownGold (plain)
// and the band courses — all hundreds thick — are MAT.crownGoldPanel.
// A vertical plaque (a jewel boss, the ruby) is safe at any thickness, because
// the test is on its Z extent, which is its height.
const BASE_LIGHT = '0.4 0.6 1';
const ROOF_LIGHT = '1 0.6 0.25';

// Sky / sun (Nastian T9 pack, installed)
//
// v14.37 — DARKER SKY (user 2026-08-30: "make the map darker or change the sky
// box to something dark"). Swapped miami_night -> dark_night, the pack's own
// darker pairing. THE SKYBOX AND SSI ARE WORLDSPAWN KEYS: they are baked into
// the .d3dbsp at compile, so this is a FULL-BUILD change and can never be a
// runtime swap (the spire's dynamic sky is done with fog instead — see
// the Endless Spire's fog, removed with the spire 2026-09-29).
//
// The two ssi entries are IDENTICAL except for the skybox they carry (diffed in
// acc_nastian_t9_skyboxes.gdt: same colorSRGB 0.7913/1/1/1, ev 6, evcmp 2.5,
// evmax 3.5, evmin 3, stops -2.2, pitch 130, bounceCount 4, dynamicShadow 1).
// So this swaps the SKY IMAGE and nothing about the sun rig — the lighting
// solve is unchanged and the LED bake has no new work to do.
//   acc_ssi_miami_night -> skybox_t9_mp_miami        (city glow, the old look)
//   acc_ssi_dark_night  -> skybox_t9_zm_silver_dark  (dark zm sky, this one)
// If a darker-still sky is ever wanted, the pack also ships
// skybox_t9_mp_black_sea and skybox_t9_mp_moscow; changing SKYBOX_MODEL alone
// is NOT enough — the ssi carries its own skyboxmodel key and would fight it,
// so always move the PAIR together, and update the zone's xmodel line.
// v14.40 — REVERTED TO MIAMI, and the reason is the whole design (user
// 2026-08-31: "But its only in the spire correct? Thats the whole point").
// THE SPIRE'S SKY IS THE CONTRAST, so darkening the TOWER works against it —
// arriving somewhere black is a smaller moment if you already were somewhere
// black. And the revert costs the spire NOTHING: at TOD_SPIRE_FOG_OPACITY 0.90
// with halfDist 1400, anything at sky distance is fully fogged, so the skybox
// is INVISIBLE from the spire no matter which one is baked. The baked sky
// therefore only ever decides how the TOWER looks — pick it for the tower.
// (v14.37 briefly shipped dark_night/silver_dark map-wide. Kept in history
// because the pairing is proven-good if a darker tower is ever wanted: the two
// ssi entries are identical apart from their skybox, so swapping the PAIR is a
// safe one-line change that does not touch the sun rig or the bake.)
// v17.78 (2026-09-05, user: "Still yellow, lets do this. Just revert back to the miami view.
// Revert all the code we touched to try to make this work and ill get a screenshot"): the
// MIAMI PAIR is back — the exact v17.70 sky — so the user can A/B screenshot Miami against the
// cybercity builds. The cybercity sky (v17.71-v17.77: tools/gen_tod_sky.js +
// source_data/tod_skybox.gdt, `skybox_tod_cybercity` / `tod_ssi_cybercity`) is DORMANT, not
// deleted: the files stay, nothing references them, and the pair below is the only switch.
// The same revert put the fsi back to zm_factory_volumetric, the spawn light back to
// `1 0.9 0.78`, LIGHT_TINT to null and the zone's xmodel line back to skybox_t9_mp_miami.
// v17.81 (2026-09-05, user "Looks good. Lets implement" on the v17.80 sun-volume fix): THE
// CYBERCITY NIGHT SKY IS BACK — the pair below and the zone's xmodel line, NOTHING ELSE. The
// fsi, the spawn light and LIGHT_TINT stay at their published (Miami-era) values, so the only
// difference from v17.80 is the sky image + its ssi clone. The yellow was never the sky
// (docs/107: the sun volume), so this is the first build where the sky is judged on a
// correctly lit base. Back to Miami = skybox_t9_mp_miami / acc_ssi_miami_night here + the
// zone's xmodel line (always the pair, never one of them).
const SKYBOX_MODEL = 'skybox_tod_cybercity';   // THE CYBERCITY SKY (docs/104) — self-authored, tools/gen_tod_sky.js
const SSI = 'tod_ssi_cybercity';               // its ssi: a clone of acc_ssi_miami_night carrying skyboxmodel skybox_tod_cybercity (LOCKSTEP with the line above)
// v17.77 THE RED-LIGHT TEST — the colour gel over EVERY point light the map emits (tower,
// lounges, crown, spire; applied inside light(), the single emitter). [r,g,b] multiplier in
// 0..1, luma held per light; `null` = off. The sun's gel is colorSRGB on the SSI above
// (source_data/tod_skybox.gdt) and the sky light's is `gen_tod_sky.js --tint` — the three
// together are "the light on the entire map". Full story at the light() block, §lights.
const LIGHT_TINT = null;   // v17.78: OFF (the v17.77 red test was [1, 0.2, 0.2]; the map came back "still yellow")

// PERKS (v5, user 2026-08-20): NO fixed perk ladder — the 6 machines PARK
// along the base-arena N wall and _tod_perk_scatter.gsc relocates them to
// random pads at load (+ reshuffles after each Panzer). Parking = graceful
// fallback: if capture ever fails they stay buyable here. 4 park via the
// stock prefabs; Widow's Wine + Electric Cherry have NO prefab — raw
// zm_perk_machine structs (map 1's exact recipe). DoubleTap retired from
// the roster (the 6: jugg, sleight, revive, staminup, widows, cherry).
// NINE machines now (user 2026-08-25: "I dont want a perk on the crown" +
// "2 on each breather"). PhD Flopper moved off the crown into the scatter pool,
// which makes the pad math land exactly: _tod_perk_scatter has 9 pads — the base
// arena (Quick Revive pinned) plus TWO on each of the four breathers — so 9
// machines fill every one. At 8 machines one breather pad was always empty.
//
// X SPACING RE-CUT 150 -> 130 to fit the ninth: ARENA is a 540 half-extent and
// the old row already reached 525, so a slot at 675 would have parked a machine
// OUTSIDE the arena wall. Parking is only the fallback position (the scatter
// relocates these at load) but it has to stay reachable if capture ever fails.
// v13.3 (user 2026-08-28: "I have downloaded the Bo7 perk machines. Can we
// miggrate to those machines?") — THE WHOLE ROSTER WEARS THE BO7/BO6 MESHES
// (wetegg/sat port, install-side at <root>\_custom\_wetegg\models\sat\ +
// per-machine GDTs in the shared source_data — root-only, our sync COPIES and
// never mirrors, so they survive builds; credits owed before publish, the
// pack ships no readme). Every machine is now the INLINE-STRUCT lane the
// widow's/cherry/nuke entries proved across v6-v13: stock
// perk_machine_spawn_init builds the machine script_model AND the
// zombie_vending trigger from the struct's model/noteworthy/script_string
// (_tod_perk_scatter.gsc:253's verified chain), so a model swap is JUST a
// model name. The retired stock prefabs carried only two extras: 6 clientside
// spot lights and 3 attack_spot structs — both pinned to the PARK ROW, which
// players never see lit (machines scatter at load), so nothing player-facing
// is lost. Noteworthies are copied VERBATIM from the stock prefabs (read
// 2026-08-28, map_source\_prefabs\zm\zm_core — doubletap is
// specialty_doubletap2, not "doubletap"). Every t10/sat machine has an _on
// twin with lit emissive maps; _tod_perk_lights swaps models at power-on.
// In-game verify list (first armed run): yaw convention (ports usually keep
// the stock -Y front — if all nine face backwards, flip the one yaw below),
// footprint vs the 130u park pitch and pad clearances, base seam at z=0.
// docs/158: the North Workshop's door takes the middle of the N wall (x[-80,80]),
// so the row is EIGHT machines at pitch 110, four each side of it, and QUICK
// REVIVE parks IN THE VAULT on its own pad (VAULT_QR — emitted to
// _tod_breather_data::vault_qr_org, which _tod_perk_scatter::build_pads reads,
// so the machine never moves). The Vault is the spawn room now, and the solo
// carve-out's whole reason was "a self-revive before the first door".
// docs/160 (DESCENT): QUICK REVIVE PARKS ON THE TERRACE — the end of the road
// out of the crown, the last flat ground before the first spiral door, and
// the nearest point to the spawn that is NOT sealed behind the Fall gate (a
// solo life bought in the hall could never be re-bought after the seal).
// Backs the terrace's north rail west of the causeway mouth at the plaza
// row's 29u standoff, facing south; 124u east of it stands the finale's
// (now dormant) uplink terminal, 100u west the terrace riser. Emitted to
// _tod_breather_data::terrace_qr_org/yaw/front, which build_pads reads.
// THE BALCONY (user 2026-09-25): Quick Revive moves from the terrace (the far
// side of the gap) to the balcony's NORTH rail, west of the approach mouth
// (x +-80), at the same 29u standoff, facing south. cwY[8] is not declared
// yet here, so the edge is written out and asserted against it below.
// THE ENCLOSED HALLWAY (user 2026-09-25 ~22:10) pushes the balcony HALLWAY_PUSH
// further from the crown: the gate opens into a walled, roofed hallway and a
// junction room between the crown's face and the balcony (see HW_ROOMS).
const HALLWAY_PUSH = 1160;
const BALCONY_N  = TER_Y2 + CW_LEN - 960 - HALLWAY_PUSH;   // = cwY[8] - HALLWAY_PUSH, the balcony's north edge (5720)
const TERRACE_QR = cpt(-400, BALCONY_N - 29, TOP2);
const PERK_PARK = []; // all nine individual vendors replaced by per-floor BO6 Wunderfizz
for (const pk of PERK_PARK)   // the N-wall row must clear the North Workshop's doorway posts (x +-100)
  if (pk.y === undefined && Math.abs(pk.x) < 100 + 60) throw new Error(`perk park ${pk.noteworthy} parks in the North Workshop doorway`);
const PERK_PARK_Y = 511;   // base N wall interior, machines face south (500 -> 511 v13.5: the BO7 meshes are shallower than the p7 stock ones — user: "QR has a bit of space between its back and the wall"; the scatter pads moved 11u wallward in lockstep)
// (WALLBUYS REMOVED — user 2026-08-20: never asked for; the box + class guns carry weapons)
// x1.5 2026-08-20 (user): was 750 +250/lap cap 4000 -> 1125 +375/lap cap 6000.
// v9.41 2026-08-23 (user: "Doors cost too much. Lets make it so they
// increase by 200 every level"): the STEP drops 375 -> 200; lap-1 door and the
// 6000 cap unchanged. The cap now binds at lap 26 (was lap 14): laps 1-25 cost
// 1125..5925, laps 26-50 cost 6000. Climb total to the roof door: 238,125 (was
// 265,875) + the 7500 roof door. The cost rides in BOTH the .map entity
// (zombie_cost, for the BSP) and the generated _tod_door_data.gsc — the GSC
// prefers the data-file value, so a price change is a -GscOnly build.
// v10.4 2026-08-23 — THE LADDER WAS THE MAP'S REAL LENGTH, and it was too long.
// Summed rather than estimated: the 52 generated rows totalled 186,975, and the
// flat 25,000 extraction on top made the minimum win path 211,975. The fastest
// solo class does not cross that until round 27-28 (round ~29 once a realistic
// perk + PaP kit is bought), i.e. 90-120 minutes with no between-round pause —
// and it lands on top of the ammo curve going negative, on a map with no box and
// no wallbuys. The finale is the best content in the map and essentially nobody
// was reaching it.
//
// The perverse part that made it worse than it looked: BO3 pays 10 per damaging
// HIT, so building damage REDUCES income. A PaP'd, DAMAGE-Lv5 MAC-10 cuts points
// per zombie ~42% — the player who builds correctly arrives LATER.
//
// One lever, pulled hard, per the audit: the ladder itself. base/step/cap only —
// ROOF_DOOR_COST and POWER_DOOR_COST are deliberately untouched to keep the
// change surface small.
//   ladder    178,725 -> 106,680  (57%)
//   win path  211,975 -> 139,930  (66%)
//   floor 10   15,750 ->  10,200      floor 20  41,500 -> 26,400
//   floor 30   77,250 ->  48,600      floor 40 123,000 -> 76,680
//   cap now binds at lap 39 (was lap 50, i.e. never in practice)
// Floor 10 still costs a real climb, so the first non-QuickRevive perk is still
// earned rather than handed over. TUNE HERE FIRST if the beta says the run is
// still long — this is the one knob that moves the map's length, and the number
// to playtest is THE ROUND EXTRACTION BECOMES BUYABLE, not the door price.
const DOOR_COST_BASE = 750;    // the lap-1 door (was 1125)
const DOOR_COST_STEP = 60;     // per lap (was 100, was 200, was 375)
const DOOR_COST_CAP  = 3000;   // was 6000 — bound at lap 50, so it never really applied
function doorCost(lap) { return Math.min(DOOR_COST_BASE + DOOR_COST_STEP * (lap - 1), DOOR_COST_CAP); }
const ROOF_DOOR_COST = 7500;   // x1.5 2026-08-20 (was 5000)
// THE FALL (docs/160, user 2026-09-23: "all the players will spawn up in the
// crown room ... about $5,000 to open up the gate ... once everyone's out of
// the crown the doors will lock up ... they actually need to go down instead
// of up"). TOD II STARTS AT THE TOP. The party spawns in the crown hall, the
// hall's own gate is the first buyable door (FALL_GATE_COST, the `tod_fall`
// row below) and every door after it is bought going DOWN.
// DESCENT flips the lap doors' DESTINATIONS (enter_lapN now leads to floor
// N-1; enter_lap1 to the plaza) and re-keys the PRICE LADDER to the order the
// doors are actually met: the roof door first (k=0), enter_lap50 next ...
// enter_lap1 last (k=50). Same base / step / cap as the climb, so the map's
// length in points is unchanged; only the direction is. The lap doors' SLABS,
// triggers and flags are untouched — a door is a door from either side, and
// the zone adjacency it sets is two-way (stock add_adjacent_zone default).
// CROWN_CLEAN drops the hall's ammo crate (user, same day: "similar to Moon
// ... clean out the crown so there's no ammo crates or anything ... add a
// pack-a-punch" — the PaP was already the east shrine; the altar is retired
// in _tod_upgrades::station_spawn, the crate in _tod_ammo_crate).
const DESCENT = true;
// THE GATE POST STANDS IN THE RAIL BAND (map 1's v19.57 fix, ported 2026-10-04; user after the
// first real playthrough: "The doors have an odd gap between them and the railing or something.
// Map 1 doesnt have this"). The post used to stand OUTSIDE the band (x PX+PARA..+20), so above the
// low rail the band's own 20 units were open air beside every closed door - map 1's "small empty
// slit". It now fills the band on the door line (x PX..PX+PARA), floor to lintel top, and the two
// rail runs that meet at the door line are NOTCHED back DOOR_POST_NOTCH each side (the parapet
// emission reads doorPostAt), so the closed slab meets the post edge to edge and nothing overlaps
// or shares a plane with it. DESCENT: a collapsed lap (BROKEN_TOWER.drops) has no door, so no post.
const DOOR_POST_NOTCH = 10;   // the post reaches this far past the door line's centre each way (y +-256 -> +-266 / +-246)
const doorPostAt = (lapNo) => FACELIFT && lapNo >= 1 && lapNo <= LAPS && !(DESCENT && BROKEN_TOWER.drops.has(lapNo));   // the DOORS table asserts it agrees with every gate it emits
const CROWN_CLEAN = true;
// docs/163 — THE CUT (user 2026-09-24: "there's a bridge that goes from the
// tower to the crown. This entire bridge most of like 80% of it needs to be
// removed and there needs to be a jump pad from one side to the other").
// true = the causeway keeps only a stub at each end (section 5c) and a
// one-way JUMP PAD on the crown's stub throws the party across the gap to the
// terrace's stub (_tod_jumppad.gsc, anchors in _tod_crown_data.gsc). The hall
// and its stub become their own island: its own zone volume, its own navmesh
// seeds, and the Fall seals once every living player has CROSSED. false = the
// v12 road, byte-for-byte (the lanes, the forks, the lane-lottery slabs).
const CW_CUT = true;
const FALL_GATE_COST = 5000;
const HW_DOOR_COST = 1500;   // the enclosed hallway's two side doors (user 2026-09-25: 1500 each)   // "about $5,000" (user) — party-size scaled by _tod_doors::door_price like every door
function descentCost(k) { return Math.min(DOOR_COST_BASE + DOOR_COST_STEP * k, DOOR_COST_CAP); }
const POWER_DOOR_COST = 750;   // x1.5 2026-08-20 (was 500) — the power-room gate
// BREATHER FLOORS (user 2026-08-19: "every 5 or so levels you have a breather
// landmark"): four rest stops on the climb (now the descent), all on EVEN laps.
const BREATHER_LAPS = new Set([10, 20, 30, 40]);   // respaced for 50 laps (still 4, still 2 perks each)

// ---------------------------------------------------------------------------
// THE HAVENS (docs/202, user 2026-10-02: "Our safe zones on this map need to act
// more like a safe zone ... a dome or like a force field that animates when you
// walk in and walk out ... these safe zones shouldn't be huge ... I don't want it
// to be like map one ... 33% slower and 33% less damage"). The TOD1 breather
// lounges (the v13 walled room with windows, the v16.7 polish, the 320-long
// gantry; docs/42) are RETIRED: every breather floor carries a HAVEN. v2 (THE
// HEART, user 2026-10-02: "make sure the teleporter for that floor is actually in
// the center of the safe zone ... maybe the safe zone can actually be inside the
// tower like how the endless tower has trials inside"): the core column OPENS at
// the haven floor into a hall with a loggia under the next lap's flights, the
// force-field dome at its heart and the teleporter (the Battle Arena gate on 40)
// at the dome's centre; the machines ring the hall outside the field.
//
// ONE SOURCE: tools/haven_layout.js cuts the geometry, the vendor anchors, the
// spur, the zone volumes, the risers, the seeds, the respawn spots, the lights
// and the script data. This file only calls it, so a haven change is one file.
// The field's GAMEPLAY (the 33% slow, the 33% damage reduction, the screen
// effect, the ripples) is _tod_haven.gsc, which reads the same numbers through
// the generated _tod_breather_data.gsc. The pre-haven lounge is in git history.
// ---------------------------------------------------------------------------
if (HAVEN.CORE !== CORE || HAVEN.PX !== PX || HAVEN.PARA !== PARA || HAVEN.SLAB !== SLAB
    || HAVEN.RAIL_VIS_H !== RAIL_VIS_H || HAVEN.RAIL_CLIP_TOP !== PARA_H + RAIL_CAP_H)
  throw new Error('tools/haven_layout.js frame constants drifted from the generator (CORE/PX/PARA/SLAB/rails)');
// The pad, in the generator's historical ODD-frame convention (the even havens
// are its point mirror): the transit routes and the pad markers derive from these
// two numbers (the field's centre).
const SPUR_CX = HAVEN.SPUR_CX, SPUR_PAD_Y = HAVEN.SPUR_PAD_Y;
if (HAVEN.STEPS !== STEPS || HAVEN.TREAD !== TREAD || HAVEN.RISE !== RISE || HAVEN.PARA_EVERY !== PARA_EVERY
    || HAVEN.FLIGHT_RISE !== FLIGHT_RISE || HAVEN.LAP_RISE !== LAP_RISE)
  throw new Error('tools/haven_layout.js stair constants drifted from the generator (STEPS/TREAD/RISE/PARA_EVERY)');
// The hall's cut must land on the lap band seams: the W wall's arch top is the
// haven band's top, and the core resumes at the start of the band two laps up.
if (HAVEN.CUT.arch.top !== FLIGHT_RISE) throw new Error('haven arch top must be the lap band seam (FLIGHT_RISE above the hall floor)');
if (HAVEN.CUT.voidH !== LAP_RISE + FLIGHT_RISE) throw new Error('haven void must end on a lap band seam (LAP_RISE + FLIGHT_RISE)');
if (HAVEN.TP_ARRIVE !== TRANSIT.FLOOR_ARRIVE_OFF) throw new Error('haven arrival offset drifted from tower_transit_layout FLOOR_ARRIVE_OFF');
// The district each haven caps (the tower's DISTRICTS order): the threshold,
// spur and pad floors and the pad pylons wear it; the dome itself is the one
// colour every haven shares — the field's cyan over a dark violet deck.
const BREATHER_THEME = {
  10: { key: 'blue',   light: '0.35 0.55 1', floor: 'floor',              wall: 'tower_blue_wall' },
  20: { key: 'green',  light: '0.35 1 0.6',  floor: 'tower_green_floor',  wall: 'tower_green_wall' },
  30: { key: 'orange', light: '1 0.6 0.25',  floor: 'tower_orange_floor', wall: 'bronze_wall' },
  40: { key: 'yellow', light: '1 0.85 0.35', floor: 'gold_deck',          wall: 'tower_gold_wall' },
};
for (const l of BREATHER_LAPS) {
  // The haven is authored in the EVEN (mirrored) frame because every breather
  // lap is even; an odd one would need a parity pass — refuse a half-mirrored map.
  if (l % 2 !== 0) throw new Error(`breather lap ${l} is ODD — tools/haven_layout.js authors the even frame only`);
  if (!BREATHER_THEME[l]) throw new Error(`breather lap ${l} has no BREATHER_THEME entry`);
}
// The vendor anchors (EVEN-frame absolutes; the same shape the v13 BR_FURN had,
// so the data emitter and the crate clip read them unchanged). perk_e / perk_w
// keep their historical names for the two perk pads.
const BR_FURN = {
  pap: HAVEN.FURN.pap, station: HAVEN.FURN.station, crate: HAVEN.FURN.crate,
  perk_e: HAVEN.FURN.wunderfizz, perk_w: HAVEN.FURN.wunderfizz, tp: HAVEN.FURN.tp,
};
const MIN_TRIG_GAP = HAVEN.MIN_TRIG_GAP;
const TP_ARRIVE_OFF = TRANSIT.FLOOR_ARRIVE_OFF; // co-op ring clears the next departure's gather
const TP_GATHER = 120;       // mirrored from _tod_teleport.gsc TOD_TP_GATHER (assert only)
{
  // A landing rider inside the pad's own gather is swept along by the next
  // departure (v10.4); the pad trigger stays inside the field's ring; the
  // up-arrival lands inside the field (tools/haven_layout.js asserts its whole
  // co-op ring is on the hall floor).
  if (TP_ARRIVE_OFF <= TP_GATHER + 48) throw new Error('tp arrival fan-out lands inside the pad gather');
  if (HAVEN.DOME_R - BR_FURN.tp.r < 24) throw new Error('tp pad trigger reaches the field ring');
  if (Math.hypot(HAVEN.ARRIVAL[0] - HAVEN.C[0], HAVEN.ARRIVAL[1] - HAVEN.C[1]) > HAVEN.DOME_R - HAVEN.IN_PAD) throw new Error('tp arrival lands outside the field');
}

// ---------------------------------------------------------------------------
// Emitters (proven plane family — do not touch the placeholder numbers)
// ---------------------------------------------------------------------------
let guidCounter = 0x100;
function guid() {
  guidCounter++;
  const c = guidCounter.toString(16).toUpperCase().padStart(12, '0');
  return `{7D0DB000-70D0-4E0A-8A3F-${c}}`;
}

function box(x1, x2, y1, y2, z1, z2, tex) {
  if (x1 >= x2 || y1 >= y2 || z1 >= z2) {
    throw new Error(`degenerate box ${tex}: x[${x1},${x2}] y[${y1},${y2}] z[${z1},${z2}]`);
  }
  const t = `${tex} 128 128 0 0 0 0 lightmap_gray 16384 16384 0 0 0 0`;
  return [
    '{',
    ` guid "${guid()}"`,
    ` ( 134.5 459.5 ${z1} ) ( 86.5 459.5 ${z1} ) ( 86.5 419.5 ${z1} ) ${t}`,
    ` ( 94.5 419.5 ${z2} ) ( 94.5 459.5 ${z2} ) ( 142.5 459.5 ${z2} ) ${t}`,
    ` ( 86.5 ${y1} 88 ) ( 134.5 ${y1} 88 ) ( 134.5 ${y1} 0 ) ${t}`,
    ` ( ${x2} 415.5 88 ) ( ${x2} 455.5 88 ) ( ${x2} 455.5 0 ) ${t}`,
    ` ( 138.5 ${y2} 88 ) ( 90.5 ${y2} 88 ) ( 90.5 ${y2} 0 ) ${t}`,
    ` ( ${x1} 459.5 88 ) ( ${x1} 419.5 88 ) ( ${x1} 419.5 0 ) ${t}`,
    '}',
  ].join('\n');
}

// v17.88 (docs/110): a box whose faces carry an EXPLICIT texture size and
// offset — the face string is "<mat> xSize ySize xOff yOff rot 0", so a 256 x
// 128 plaque maps its whole image once when xs/ys are the face's own extent
// and the offsets cancel the world position (the projection is axial from the
// world origin, U = the face's horizontal world axis, V = world z).
function boxTex(x1, x2, y1, y2, z1, z2, tex, xs, ys, xo, yo) {
  const plain = box(x1, x2, y1, y2, z1, z2, tex);
  return plain.split(`${tex} 128 128 0 0 0 0`).join(`${tex} ${xs} ${ys} ${xo} ${yo} 0 0`);
}
function addBoxTex(label, x1, x2, y1, y2, z1, z2, tex, xs, ys, xo, yo) {
  addBox(label, x1, x2, y1, y2, z1, z2, tex);
  const b = worldBrushes[worldBrushes.length - 1];
  b.text = boxTex(x1, x2, y1, y2, z1, z2, tex, xs, ys, xo, yo);
}
// Direct kit materials need the same authored texture scale as the crown remap.
function transitBox(label,x1,x2,y1,y2,z1,z2,tex) {
  const role=require('./art_cohesion/crown_materials.json').materials[tex.slice(7)];
  const size=role ? role.size : 128;
  addBoxTex(label,x1,x2,y1,y2,z1,z2,tex,size,size,0,0);
}
function transitCBox(label,x1,x2,y1,y2,z1,z2,tex) {
  if(CM===1)transitBox(label,x1,x2,y1,y2,z1,z2,tex);
  else transitBox(label,-x2,-x1,-y2,-y1,z1,z2,tex);
}
// docs/196 THE DEPARTURE HALL's shaped pieces (arches, rings, struts, jewels,
// bevelled piers): convex solids in the crown's own plane idiom (crownPoly /
// crownBevel), but written with the KIT's texture size per face like transitBox
// (test_tower_transit checks every "transit bay" face against the kit) and
// kept OUT of crownBB (the label is not "crown ..."). Decoration only: every
// walkable surface in the hall is a transitCBox.
function transitPlanes(label,planes,tex) {
  const role=require('./art_cohesion/crown_materials.json').materials[tex.slice(7)];
  const size=role ? role.size : 128;
  const h=CB.hull(planes);
  addBox(label,h.x1,h.x2,h.y1,h.y2,h.z1,h.z2,tex);   // the shared accounting (allBoxes, the sky-seal / clearance asserts)
  const t=`${tex} ${size} ${size} 0 0 0 0 lightmap_gray 16384 16384 0 0 0 0`;
  const lines=planes.map(q=>` ( ${q.v[0].join(' ')} ) ( ${q.v[1].join(' ')} ) ( ${q.v[2].join(' ')} ) ${t}`);
  worldBrushes[worldBrushes.length-1].text=['{',` guid "${guid()}"`,...lines,'}'].join('\n');
}
function transitCPoly(label,vertices,faces,tex) {
  const vs=vertices.map(p=>cpt(...p));
  const center=[0,1,2].map(i=>vs.reduce((s,p)=>s+p[i],0)/vs.length);
  const planes=faces.map(face=>{
    let v=face.slice(0,3).map(i=>vs[i]);
    let q=CB.plane(v,tex);
    if(CB.dot(q.n,CB.sub(center,v[0]))>0){v=[v[2],v[1],v[0]];q=CB.plane(v,tex);}
    if(face.some(i=>Math.abs(CB.dot(q.n,vs[i])-q.d)>0.01))
      throw new Error(`non-planar transit hall face: ${label}`);
    if(vs.some(p=>CB.dot(q.n,p)>q.d+0.01))
      throw new Error(`non-convex transit hall solid: ${label}`);
    return q;
  });
  transitPlanes(label,planes,tex);
}
function transitCBevel(label,x1,x2,y1,y2,z1,z2,tex,amount) {
  const lo=[CM===1?x1:-x2,CM===1?y1:-y2,z1];
  const hi=[CM===1?x2:-x1,CM===1?y2:-y1,z2];
  const mid=lo.map((v,i)=>(v+hi[i])/2), half=lo.map((v,i)=>(hi[i]-v)/2);
  const b=Math.min(amount,...half.map(v=>v*0.42));
  const ps=[];
  function cut(n,d) {
    n=CB.norm(n);const point=mid.map((v,i)=>v+n[i]*d);
    const u=CB.norm(CB.cross(n,Math.abs(n[2])<0.9?[0,0,1]:[0,1,0]));
    const v=CB.cross(n,u);
    ps.push(CB.plane([point.map((x,i)=>x+u[i]*128),point,point.map((x,i)=>x+v[i]*128)],tex));
  }
  for(let a=0;a<3;a++)for(const sign of [-1,1]){const n=[0,0,0];n[a]=sign;cut(n,half[a]);}
  for(let a=0;a<3;a++)for(let c=a+1;c<3;c++)for(const sa of [-1,1])for(const sc of [-1,1]){
    const n=[0,0,0];n[a]=sa;n[c]=sc;
    cut(n,(half[a]+half[c]-b)/Math.SQRT2);
  }
  transitPlanes(label,ps,tex);
}
// docs/202 THE HAVENS: absolute even-frame emitters (no crown mirror). Kit
// roles only ('tod_cc_' + role), with the kit's texture size per face like the
// transit hall, so verify_tower_design / the lint's material table know them.
function havenBox(label, x1, x2, y1, y2, z1, z2, role) {
  transitBox(label, x1, x2, y1, y2, z1, z2, 'tod_cc_' + role);
}
function havenClip(label, x1, x2, y1, y2, z1, z2) {
  addBox(label, x1, x2, y1, y2, z1, z2, MAT.clip);
}
// A convex solid with one kit role per face (or one for all). Face winding is
// normalised outward and every face is checked planar and the solid convex.
function havenPoly(label, vertices, faces, roles) {
  const kit = require('./art_cohesion/crown_materials.json').materials;
  const center = [0, 1, 2].map(i => vertices.reduce((s, p) => s + p[i], 0) / vertices.length);
  const planes = faces.map((face, fi) => {
    const role = Array.isArray(roles) ? roles[fi] : roles;
    if (!kit[role]) throw new Error(`haven: unknown kit role ${role} on ${label}`);
    const mat = 'tod_cc_' + role;
    let v = face.slice(0, 3).map(j => vertices[j]);
    let q = CB.plane(v, mat);
    if (CB.dot(q.n, CB.sub(center, v[0])) > 0) { v = [v[2], v[1], v[0]]; q = CB.plane(v, mat); }
    if (face.some(j => Math.abs(CB.dot(q.n, vertices[j]) - q.d) > 0.01)) throw new Error(`non-planar haven face: ${label}`);
    if (vertices.some(p => CB.dot(q.n, p) > q.d + 0.01)) throw new Error(`non-convex haven solid: ${label}`);
    return q;
  });
  const h = CB.hull(planes);
  addBox(label, h.x1, h.x2, h.y1, h.y2, h.z1, h.z2, planes[0].mat);   // the shared accounting
  const lines = planes.map(q => {
    const size = kit[q.mat.slice(7)].size;
    return ` ( ${q.v[0].join(' ')} ) ( ${q.v[1].join(' ')} ) ( ${q.v[2].join(' ')} ) ${q.mat} ${size} ${size} 0 0 0 0 lightmap_gray 16384 16384 0 0 0 0`;
  });
  worldBrushes[worldBrushes.length - 1].text = ['{', ` guid "${guid()}"`, ...lines, '}'].join('\n');
}
// docs/202 v4 THE BARRIER: a convex polyhedron as ENTITY brush text (one face per
// polygon, wound outward, every face checked planar and the solid convex) in one
// material - the haven barrier's shell rides a script_brushmodel, not worldspawn.
function polyBrushText(label, vertices, faces, mat) {
  const center = [0, 1, 2].map(i => vertices.reduce((s, p) => s + p[i], 0) / vertices.length);
  const lines = faces.map((face) => {
    let v = face.slice(0, 3).map(j => vertices[j]);
    let q = CB.plane(v, mat);
    if (CB.dot(q.n, CB.sub(center, v[0])) > 0) { v = [v[2], v[1], v[0]]; q = CB.plane(v, mat); }
    if (face.some(j => Math.abs(CB.dot(q.n, vertices[j]) - q.d) > 0.02)) throw new Error(`non-planar brush face: ${label}`);
    if (vertices.some(p => CB.dot(q.n, p) > q.d + 0.02)) throw new Error(`non-convex brush: ${label}`);
    return ` ( ${q.v[0].join(' ')} ) ( ${q.v[1].join(' ')} ) ( ${q.v[2].join(' ')} ) ${mat} 128 128 0 0 0 0 lightmap_gray 16384 16384 0 0 0 0`;
  });
  return ['{', ` guid "${guid()}"`, ...lines, '}'].join('\n');
}
// A chamfered box (the transit hall's bevel, absolute coordinates).
function havenBevel(label, x1, x2, y1, y2, z1, z2, role, amount) {
  const tex = 'tod_cc_' + role;
  const lo = [x1, y1, z1], hi = [x2, y2, z2];
  const mid = lo.map((v, i) => (v + hi[i]) / 2), half = lo.map((v, i) => (hi[i] - v) / 2);
  const b = Math.min(amount, ...half.map(v => v * 0.42));
  const ps = [];
  function cut(n, d) {
    n = CB.norm(n); const point = mid.map((v, i) => v + n[i] * d);
    const u = CB.norm(CB.cross(n, Math.abs(n[2]) < 0.9 ? [0, 0, 1] : [0, 1, 0]));
    const v = CB.cross(n, u);
    ps.push(CB.plane([point.map((x, i) => x + u[i] * 128), point, point.map((x, i) => x + v[i] * 128)], tex));
  }
  for (let a = 0; a < 3; a++) for (const sign of [-1, 1]) { const n = [0, 0, 0]; n[a] = sign; cut(n, half[a]); }
  for (let a = 0; a < 3; a++) for (let c = a + 1; c < 3; c++) for (const sa of [-1, 1]) for (const sc of [-1, 1]) {
    const n = [0, 0, 0]; n[a] = sa; n[c] = sc;
    cut(n, (half[a] + half[c] - b) / Math.SQRT2);
  }
  transitPlanes(label, ps, tex);
}
const worldBrushes = [];
const allBoxes = [];   // every axis box's AABB (docs/162 T3: the sun-probe target must sit in open air)

// ---------------------------------------------------------------------------
// NAVMESH SEEDS ON SURFACES NO RISER STANDS ON (2026-09-04)
// ---------------------------------------------------------------------------
// Seeds are emitted one per RISER (tower §5, spire §6f) and risers live ONLY on
// LANDINGS by construction — §6f says so in its own words ("a riser on a stair
// hangs in mid-air or buries itself under a crest"). So every STAIR FLIGHT, and
// on the spire every crate shelf, hub porch fan and the summit apron, has
// carried no seed at all.
//
// THAT IS NOT THE SAME AS "covered by the landing's seed". cod2map64 is Havok AI
// region pruning, not a flood: it meshes the world, splits it into CONNECTED
// REGIONS, and keeps a region only if its AREA clears a threshold OR a seed sits
// on it (within pruning.minDistanceToSeedPoints = 14). A region CONNECTED to a
// seeded one can still be dropped, and this map has already paid for that lesson
// twice (the detached spire v14.19, the tower above ~floor 17 v17.7). The
// evidence that it is still paying: v17.14 took the spire from 22 seeds to 278
// with BYTE-IDENTICAL GEOMETRY and the .hkt went 110,468 -> 114,624. Entities
// that add no surface cannot grow a mesh unless previously-PRUNED regions are
// now KEPT — so regions were being pruned, and per-landing seeding recovered
// only some of them.
//
// THE RULE, third time of writing and the first time stated about SURFACES:
// seed every walkable SURFACE, not every walkable zone and not every riser.
// Risers are a SPAWN table; they were never a COVERAGE table. Because the ramp
// seeds are taken inside rampWedgeY/rampWedgeX themselves, from the very
// arguments the wedge is built from, a new flight anywhere in this map is
// seeded by construction and cannot be forgotten again.
//
// node_pathnode is free: it is on radiant/configs/navmesh.json's EXCLUSION list
// (carves nothing), is invisible, and spawns NO runtime gentity, so the ~1024
// gentity budget is untouched. Buffered rather than emitted inline because
// `entities` / ent() do not exist yet at this point in the file (the tower's
// ramps are written ~2,500 lines before them); flushed after section 6.
const navSeeds = [];
function navSeed(label, x, y, z) {
  navSeeds.push({ label, org: [Math.round(x), Math.round(y), Math.round(z)] });
}
// ONE KNOB. 3 puts a seed roughly every 128 units of run / 48 of rise on a
// standard flight. Drop to 1 if the entity count ever matters; raise if a .hkt
// delta says the mesh still fragments finer than this.
const RAMP_SEEDS = 3;
// THE CROWN MEASURES ITSELF. The sky seal used to be asserted against DERIVED
// constants (CR_OUT_X / CR_OUT_Y), and those understate the truth: the east and
// west point HEADS stand 200 units proud of the band they sit on, so the derived
// figure was 104 short before anyone scaled anything. An element that sticks out
// further than its own constant suggests is exactly the bug the seal assert
// exists to catch, so the assert reads THIS instead — the real bounding box of
// every brush actually emitted with a crown or mast label.
const crownBB = { x1: Infinity, x2: -Infinity, y1: Infinity, y2: -Infinity, z1: Infinity, z2: -Infinity };
const crownBoxes = [];
function addBox(label, x1, x2, y1, y2, z1, z2, tex) {
  if (/^(crown|mast)\b/.test(label)) {
    crownBB.x1 = Math.min(crownBB.x1, x1); crownBB.x2 = Math.max(crownBB.x2, x2);
    crownBB.y1 = Math.min(crownBB.y1, y1); crownBB.y2 = Math.max(crownBB.y2, y2);
    crownBB.z1 = Math.min(crownBB.z1, z1); crownBB.z2 = Math.max(crownBB.z2, z2);
    // kept for the road-intrusion assert in 5f.9 — see the comment there
    crownBoxes.push({ label, x1, x2, y1, y2, z1, z2 });
  }
  allBoxes.push({ label, x1, x2, y1, y2, z1, z2, tex });   // tex: the floor numbers' sightline check tells a visible solid from a clip (docs/208)
  worldBrushes.push({ label, text: box(x1, x2, y1, y2, z1, z2, tex) });
}

// --- crown mirror helpers ---------------------------------------------------
// Every crown box/point/yaw below is authored in the ODD frame (E flight up the
// east face, arriving on the NORTH apron). When the crown lap is EVEN the whole
// assembly is point-mirrored through the tower axis (x,y -> -x,-y), which maps
// the E flight onto the W flight and the N arrival onto the S arrival — exactly
// the mirror the spiral itself uses. Mirroring an interval flips its ends, so
// cbox re-orders them to keep x1<x2 / y1<y2 (the degenerate-box rule).
// Crown architecture uses true convex solids. Bounding boxes still feed the
// sky/causeway clearance assertions; emitted planes feed the independent tools.
const CB = require('./convex_brush');
function crownPoly(label, vertices, faces, tex) {
  const vs=vertices.map(p=>cpt(...p));
  const center=[0,1,2].map(i=>vs.reduce((s,p)=>s+p[i],0)/vs.length);
  const planes=faces.map(face=>{
    let v=face.slice(0,3).map(i=>vs[i]);
    let q=CB.plane(v,tex);
    if(CB.dot(q.n,CB.sub(center,v[0]))>0){v=[v[2],v[1],v[0]];q=CB.plane(v,tex);}
    if(face.some(i=>Math.abs(CB.dot(q.n,vs[i])-q.d)>0.01))
      throw new Error(`non-planar crown face: ${label}`);
    if(vs.some(p=>CB.dot(q.n,p)>q.d+0.01))
      throw new Error(`non-convex crown profile: ${label}`);
    return q;
  });
  crownPlanes(label,planes,tex);
}
function crownPlanes(label,planes,tex) {
  const h=CB.hull(planes);
  // Use the existing accounting path, then replace just its brush definition.
  addBox(label,h.x1,h.x2,h.y1,h.y2,h.z1,h.z2,tex);
  const lines=planes.map(q=>rampPlane(...q.v,q.mat));
  worldBrushes[worldBrushes.length-1].text=['{',` guid "${guid()}"`,...lines,'}'].join('\n');
}
function crownBevel(label,x1,x2,y1,y2,z1,z2,tex,amount) {
  const lo=[CM===1?x1:-x2,CM===1?y1:-y2,z1];
  const hi=[CM===1?x2:-x1,CM===1?y2:-y1,z2];
  const mid=lo.map((v,i)=>(v+hi[i])/2), half=lo.map((v,i)=>(hi[i]-v)/2);
  const b=Math.min(amount,...half.map(v=>v*0.42));
  const ps=[];
  function cut(n,d,mat) {
    n=CB.norm(n);const point=mid.map((v,i)=>v+n[i]*d);
    const u=CB.norm(CB.cross(n,Math.abs(n[2])<0.9?[0,0,1]:[0,1,0]));
    const v=CB.cross(n,u);
    ps.push(CB.plane([point.map((x,i)=>x+u[i]*128),point,point.map((x,i)=>x+v[i]*128)],mat));
  }
  for(let a=0;a<3;a++)for(const sign of [-1,1]){const n=[0,0,0];n[a]=sign;cut(n,half[a],tex);}
  for(let a=0;a<3;a++)for(let c=a+1;c<3;c++)for(const sa of [-1,1])for(const sc of [-1,1]){
    const n=[0,0,0];n[a]=sa;n[c]=sc;
    cut(n,(half[a]+half[c]-b)/Math.SQRT2,tex===MAT.crownBrass?MAT.crownGoldPanel:tex);
  }
  crownPlanes(label,ps,tex);
}
function cbox(label, x1, x2, y1, y2, z1, z2, tex) {
  // Only decorative solid architecture: walking slabs, structural wall seals,
  // vendor clips and floor inlays retain their exact collision contracts.
  if(/^crown (point|rib |front cross|finial|jewel|cullinan|pendilia|girandole|monde|beacon|mouth jamb|mouth corbel|hall pier|hall shrine.*(pilaster|canopy)|hall reredos|gate post|cornice)/.test(label)
      && !/^(clip|sky)/.test(tex)) {
    crownBevel(label,x1,x2,y1,y2,z1,z2,tex,Math.min(48,Math.min(x2-x1,y2-y1,z2-z1)*0.18));return;
  }
  if (CM === 1) addBox(label, x1, x2, y1, y2, z1, z2, tex);
  else addBox(label, -x2, -x1, -y2, -y1, z1, z2, tex);
}
// Loft matching convex profiles; shared boundaries are identical, avoiding
// stair-step silhouettes and cracks between adjacent ribbon sections.
function crownLoft(label,lower,upper,tex) {
  const n=lower.length,faces=[Array.from({length:n},(_,i)=>i),Array.from({length:n},(_,i)=>i+n)];
  for(let i=0;i<n;i++)faces.push([i,(i+1)%n,(i+1)%n+n,i+n]);
  crownPoly(label,[...lower,...upper],faces,tex);
}
function crownOct(hx,hy,z,c=Math.min(CR_CHAM,Math.min(hx,hy)*0.32)) {
  return [[-hx+c,-hy],[hx-c,-hy],[hx,-hy+c],[hx,hy-c],[hx-c,hy],[-hx+c,hy],[-hx,hy-c],[-hx,-hy+c]].map(([x,y])=>[x,CR_CY+y,z]);
}
function crownOrb(tag,x,y,z,rx,ry,rz,tex) {
  const n=12,stacks=8;
  for(let j=0;j<stacks;j++) {
    const ring=t=>{const r=Math.max(0.015,Math.cos(t));return Array.from({length:n},(_,i)=>{
      const a=i*2*Math.PI/n;return [x+rx*r*Math.cos(a),y+ry*r*Math.sin(a),z+rz*Math.sin(t)];});};
    crownLoft(`${tag} facet ${j+1}`,ring(-Math.PI/2+Math.PI*j/stacks),ring(-Math.PI/2+Math.PI*(j+1)/stacks),tex);
  }
}
function cpt(x, y, z) { return [CM * x, CM * y, z]; }
function cyaw(y) { return CM === 1 ? y : ((y + 180) % 360); }

// --- STAIR RAMP CLIP emitters (see the constants block for the full note) ---
// These are the map's ONLY non-axis-aligned brushes, and that is deliberate:
// box() stays the sole general-purpose writer, and every tool that parses the
// .map (geometry lint, parity lint, measure_lit_area, audit_hidden_faces,
// preview_crown) either skips or buckets a brush whose planes are not all
// axis-constant — verified per-tool on 2026-08-27, docs/39 §5-G1.
// Plane convention (matches box()): three points per plane, outward normal
// = (P1-P2)x(P3-P2). The slope is ASSERTED equal to RISE/TREAD, which is what
// welds the wedge to the nosing line and both landings by arithmetic.
function rampPlane(p1, p2, p3, tex) {
  const t = `${tex} 128 128 0 0 0 0 lightmap_gray 16384 16384 0 0 0 0`;
  return ` ( ${p1.join(' ')} ) ( ${p2.join(' ')} ) ( ${p3.join(' ')} ) ${t}`;
}
function rampWedge(label, planes, tex) {
  worldBrushes.push({
    label,
    text: ['{', ` guid "${guid()}"`, ...planes.map((p) => rampPlane(p[0], p[1], p[2], tex)), '}'].join('\n'),
  });
}
// A wedge whose top slopes along Y: z = zAtY1 at y1, zAtY2 at y2 (either end
// may be the high one). x1<x2, y1<y2 always — these are bounds, not direction.
// rise/tread default to the tower's stair scale; roadStair passes its own
// (CW_RISE/CW_TREAD) — the assert is what welds the plane to the nosings.
function rampWedgeY(label, x1, x2, y1, y2, zAtY1, zAtY2, tex, rise = RISE, tread = TREAD) {
  if (x1 >= x2 || y1 >= y2) throw new Error(`ramp wedge ${label}: degenerate bounds`);
  if (Math.abs(zAtY2 - zAtY1) * tread !== (y2 - y1) * rise)
    throw new Error(`ramp wedge ${label}: slope must be rise/tread or it misses the nosings`);
  // Navmesh seeds ride the SAME arguments the wedge is built from, so they can
  // never drift from the surface they vouch for. +2z matches the riser-seed
  // convention; the wedge top IS the AI-walkable surface since v16.61a.
  for (let s = 1; s <= RAMP_SEEDS; s++) {
    const t = s / (RAMP_SEEDS + 1);
    navSeed(`${label} ${s}`, (x1 + x2) / 2, y1 + (y2 - y1) * t, zAtY1 + (zAtY2 - zAtY1) * t + 2);
  }
  // RAMP_LIFT: the emitted wedge sits LIFT above the nosing plane the caller
  // described (see the constant). Seeds above were placed off the caller's plane
  // + 2, i.e. exactly on the lifted surface — still inside minDistanceToSeedPoints.
  zAtY1 += RAMP_LIFT; zAtY2 += RAMP_LIFT;
  rampWedge(label, [
    [[x2, y1, zAtY1], [x1, y1, zAtY1], [x1, y2, zAtY2]],                               // top (sloped, up)
    [[x1, y1, zAtY1 - RAMP_T], [x2, y1, zAtY1 - RAMP_T], [x2, y2, zAtY2 - RAMP_T]],    // bottom (sloped, down)
    [[x1, y1, zAtY1], [x2, y1, zAtY1], [x2, y1, zAtY1 - 64]],                          // end -y
    [[x2, y2, zAtY2], [x1, y2, zAtY2], [x1, y2, zAtY2 - 64]],                          // end +y
    [[x1, y1 + 64, zAtY1], [x1, y1, zAtY1], [x1, y1, zAtY1 - 64]],                     // side -x
    [[x2, y1, zAtY1], [x2, y1 + 64, zAtY1], [x2, y1 + 64, zAtY1 - 64]],                // side +x
  ], tex);
}
// The X-sloping mirror: z = zAtX1 at x1, zAtX2 at x2.
function rampWedgeX(label, y1, y2, x1, x2, zAtX1, zAtX2, tex, rise = RISE, tread = TREAD) {
  if (y1 >= y2 || x1 >= x2) throw new Error(`ramp wedge ${label}: degenerate bounds`);
  if (Math.abs(zAtX2 - zAtX1) * tread !== (x2 - x1) * rise)
    throw new Error(`ramp wedge ${label}: slope must be rise/tread or it misses the nosings`);
  // Same as rampWedgeY, with the run on x (note this function is bounded
  // y1,y2 FIRST — the seed must not copy the other one blind).
  for (let s = 1; s <= RAMP_SEEDS; s++) {
    const t = s / (RAMP_SEEDS + 1);
    navSeed(`${label} ${s}`, x1 + (x2 - x1) * t, (y1 + y2) / 2, zAtX1 + (zAtX2 - zAtX1) * t + 2);
  }
  zAtX1 += RAMP_LIFT; zAtX2 += RAMP_LIFT;   // see rampWedgeY
  rampWedge(label, [
    [[x1, y1, zAtX1], [x1, y2, zAtX1], [x2, y2, zAtX2]],                               // top (sloped, up)
    [[x1, y2, zAtX1 - RAMP_T], [x1, y1, zAtX1 - RAMP_T], [x2, y1, zAtX2 - RAMP_T]],    // bottom (sloped, down)
    [[x1, y2, zAtX1], [x1, y1, zAtX1], [x1, y1, zAtX1 - 64]],                          // end -x
    [[x2, y1, zAtX2], [x2, y2, zAtX2], [x2, y2, zAtX2 - 64]],                          // end +x
    [[x1, y1, zAtX1], [x1 + 64, y1, zAtX1], [x1 + 64, y1, zAtX1 - 64]],                // side -y
    [[x1 + 64, y2, zAtX1], [x1, y2, zAtX1], [x1, y2, zAtX1 - 64]],                     // side +y
  ], tex);
}

// ---------------------------------------------------------------------------
// 1. Sky enclosure
// ---------------------------------------------------------------------------
addBox('sky floor', -(SKY_IN + SKY_TH), SKY_IN + SKY_TH, -(SKY_IN + SKY_TH), SKY_IN + SKY_TH, SKY_BOT, SKY_FLOOR, MAT.sky);
addBox('sky top', -(SKY_IN + SKY_TH), SKY_IN + SKY_TH, -(SKY_IN + SKY_TH), SKY_IN + SKY_TH, SKY_TOP, SKY_TOP + SKY_TH, MAT.sky);
addBox('sky wall S', -(SKY_IN + SKY_TH), SKY_IN + SKY_TH, -(SKY_IN + SKY_TH), -SKY_IN, SKY_FLOOR, SKY_TOP, MAT.sky);
addBox('sky wall N', -(SKY_IN + SKY_TH), SKY_IN + SKY_TH, SKY_IN, SKY_IN + SKY_TH, SKY_FLOOR, SKY_TOP, MAT.sky);
addBox('sky wall W', -(SKY_IN + SKY_TH), -SKY_IN, -SKY_IN, SKY_IN, SKY_FLOOR, SKY_TOP, MAT.sky);
addBox('sky wall E', SKY_IN, SKY_IN + SKY_TH, -SKY_IN, SKY_IN, SKY_FLOOR, SKY_TOP, MAT.sky);

// ---------------------------------------------------------------------------
// 2. Base arena: ground + wall + full-height clip
// ---------------------------------------------------------------------------
addBox('ground slab', -(ARENA + WALL), ARENA + WALL, -(ARENA + WALL), ARENA + WALL, -SLAB, 0, MAT.baseFloor);
// ---------------------------------------------------------------------------
// v17.32 — ONE WIDTH, ONE COLOUR, AND THE POWER LANE ACTUALLY REACHES THE POWER
// (user 2026-09-04: "the floor has these strip designs. Can we make that blue
// instead of teal. Its alos not complleted I dont think. Lets redesign this
// strip so it looks cleaner and consistent").
//
// WHAT WAS ACTUALLY INCONSISTENT — measured, not guessed. The base carried
// THREE different line weights for one visual language:
//     perimeter ring    64 wide   (ARENA-84 .. ARENA-20)
//     core foot ring    40 wide
//     wayfinding lane   20 wide
// and the lane ran 16u INSIDE the ring's inner edge for its whole length,
// parallel to it and never touching it. Two lines doing the same job, at
// different weights, that never meet — which is exactly what reads as
// unfinished.
//
// AND IT GENUINELY WAS INCOMPLETE. The power lane — the whole reason these
// exist (Workshop 2026-08-26: "having a difficult time finding the power.
// Where is it?") — stopped at x=580. That is TWENTY UNITS past the doorway,
// into a hallway that runs to x=1640. It pointed at the power room and quit
// before the switch.
//
// NOW: every line in the arena is TRACE_W wide, every line is the same blue,
// and one continuous lane runs spawn -> south -> through the power door ->
// down the hall to the switch.
//
// TWO RULES THAT DECIDED THE COORDINATES, both learned by nearly breaking them:
//
//  1. COPLANAR DECALS MUST ABUT, NEVER OVERLAP. Everything here is 1u at
//     z[0,1]; two of them sharing floor is a z-fight, not a brighter line. The
//     lane therefore STOPS at the perimeter ring's inner edge and RESUMES at its
//     outer edge (the ring carries the crossing), and the door spur stops at
//     y=-266, which is where the lap-1 door gate's own SILL starts — that sill
//     is also a 1u z[0,1] strip in this exact spot.
//  2. NOTHING MAY RUN UNDER A WALL. The power room's north wall is
//     x[280,540] y[-420,-400]; the lane rides y[-460,-420] so its north edge is
//     that wall's south face. The old 20-wide lane at y[-440,-420] cleared it by
//     luck, not by construction.
//
// The TELEPORT BAY's own ring is deliberately NOT widened to TRACE_W: its E/W
// runs sit at x 204..220 and the up-pad squares reach x=198, so 40 wide would
// collide with them. It takes the new blue and keeps its 16u width. That is a
// constraint, not an oversight.
// ---------------------------------------------------------------------------
const TRACE_W = 40;
const RG_O = ARENA - 20, RG_I = RG_O - TRACE_W;   // perimeter ring 480..520

// TRON GRID inlay: a glowing ring 1u proud around the arena perimeter. N and S
// span the full width; W and E fill between them, so the corners mitre and no
// two boxes overlap.
addBox('base inlay N', -RG_O, RG_O, RG_I, RG_O, 0, 1, MAT.baseInlay);
addBox('base inlay S', -RG_O, RG_O, -RG_O, -RG_I, 0, 1, MAT.baseInlay);
addBox('base inlay W', -RG_O, -RG_I, -RG_I, RG_I, 0, 1, MAT.baseInlay);
addBox('base inlay E', RG_I, RG_O, -RG_I, RG_I, 0, 1, MAT.baseInlay);
// v16.11 FACELIFT §3 — BASE PLAZA + WAYFINDING. Players have reported not
// finding the power ("having a difficult time finding the power. Where is
// it?", Workshop 2026-08-26). Three 1u glow traces in the inlay material, the
// same decal trick as the ring: from the spawn band south to the south lane,
// east along the lane straight into the power hallway's mouth (the opening is
// y[-540,-420]; the trace rides its north edge at y[-440,-420], 16u clear of
// the inlay ring's inner edge at -456), and a spur north to the first door
// (its trigger starts at y=-306; the spur stops at -310). Plus a FOOT RING
// 40 wide around the core so the column visibly lands on the floor. NO EAST
// BOX since v16.80: the lap-1 under-stair fill (section 4) is solid from the
// floor across x[256,416], y[-224,256], so the ring's east run would be buried
// inside it; the fill IS the column landing on that side.
// Nothing here is taller than 1u: a step to the lint, a decal to the eye.
if (FACELIFT) {
  const LN_S = -460, LN_N = LN_S + TRACE_W;        // the east lane, y[-460,-420]
  const LN_W = -450, LN_E = LN_W + TRACE_W;        // the spawn lane, x[-450,-410]

  // THE LANE, one continuous path in four pieces: it leaves the perimeter ring
  // beside the spawn, runs south, turns east, crosses under the ring, passes
  // through the power door and ends 20u short of the hall's east wall — at the
  // switch. The two east pieces exist only because rule 1 forbids drawing over
  // the ring; walked, it is one unbroken line.
  addBox('base trace ring spur', -RG_I, LN_W, -TRACE_W / 2, TRACE_W / 2, 0, 1, MAT.baseInlay);
  addBox('base trace spawn', LN_W, LN_E, LN_N, TRACE_W / 2, 0, 1, MAT.baseInlay);
  addBox('base trace east', LN_W, RG_I, LN_S, LN_N, 0, 1, MAT.baseInlay);
  // ...under the ring at x[480,520]...
  addBox('base trace power hall', RG_O, 1600, LN_S, LN_N, 0, 1, MAT.baseInlay);

  // THE DOOR SPUR runs off the foot ring's south-east stub, east to the path
  // edge, stopping at the lap-1 door gate's SILL (y=-266). It CANNOT come off
  // the lane instead: the lane is inside the power room for all x in [280,540],
  // and the only clear channel north out of it is x[256,280] — 24 wide, against
  // the core's east face — so a spur there would be off-width and half-buried.
  addBox('base trace door', CORE + TRACE_W, PX, -306, -266, 0, 1, MAT.baseInlay);

  // THE FOOT RING. Three runs, and the EAST side is open BY CONSTRUCTION, not by
  // omission: the lap-1 under-stair fill is solid from the floor across
  // x[256,416] y[-224,256] (section 4), so an east run would be buried inside it
  // — the staircase IS what lands on that side. The N and S runs deliberately
  // over-run to CORE+TRACE_W so the ring turns its corners and terminates against
  // the stair rather than just stopping in open floor.
  addBox('core foot N', -(CORE + TRACE_W), CORE + TRACE_W, CORE, CORE + TRACE_W, 0, 1, MAT.baseInlay);
  addBox('core foot S', -(CORE + TRACE_W), CORE + TRACE_W, -(CORE + TRACE_W), -CORE, 0, 1, MAT.baseInlay);
  addBox('core foot W', -(CORE + TRACE_W), -CORE, -CORE, CORE, 0, 1, MAT.baseInlay);
}
// SPLIT — the TELEPORT BAY doorway passes through at x[-TPB_DOOR,TPB_DOOR].
// The clip above (base clip S) is deliberately NOT split: it spans z[128,1600]
// and becomes the lintel over the opening, so the doorway is walk-through at
// player height and still un-jumpable.
//
// v16.11 FACELIFT §3 — the five arena walls are emitted by baseWallRun: the
// same blue volume split along its length into runs with a 40-wide CYAN
// PILASTER every 280 units (centres at ±140 and ±420, skipped where a doorway
// or a wall end is within 20u), and a 20-tall cyan CORNICE on top. Flush,
// so nothing intrudes into the arena; the pilasters are the wall's own
// material swapped, not new surface, and the cornice is the only new area.
// The annexes (teleport bay, power hall) keep plain walls.
function baseWallRun(label, x1, x2, y1, y2) {
  if (!FACELIFT) { addBox(label, x1, x2, y1, y2, 0, BASE_WALL_H, MAT.baseWall); return; }
  const alongX = (x2 - x1) > (y2 - y1);
  const a1 = alongX ? x1 : y1, a2 = alongX ? x2 : y2;
  const emit = (l, s1, s2, mat) => (alongX
    ? addBox(l, s1, s2, y1, y2, 0, BASE_WALL_H, mat)
    : addBox(l, x1, x2, s1, s2, 0, BASE_WALL_H, mat));
  const cuts = [];
  for (let c = -420; c <= 420; c += 280) if (c - 20 > a1 && c + 20 < a2) cuts.push(c);
  let cur = a1, k = 0;
  for (const c of cuts) {
    if (c - 20 > cur) emit(`${label} run ${++k}`, cur, c - 20, MAT.baseWall);
    emit(`${label} pilaster ${k}`, c - 20, c + 20, MAT.pilaster);
    cur = c + 20;
  }
  if (a2 > cur) emit(`${label} run ${++k}`, cur, a2, MAT.baseWall);
  addBox(`${label} cornice`, x1, x2, y1, y2, BASE_WALL_H, BASE_WALL_H + 20, MAT.pilaster);
}
// docs/158 — THE PLAZA HAS FIVE MORE DOORWAYS (one per wall for the workshop
// wings, plus the Undercity exit in the W wall). Every run below is the old
// wall minus a 160-wide gap; the gaps' slabs are DOORS entries (the wing loop
// and the undercity block) and each gap gets a cyan lintel so the cornice
// reads continuous. The full-height clips above (base clip *) stay WHOLE and
// are the un-jumpable lintel over every opening, exactly as for the bay door.
// S wall, west part: the corner stub keeps the SW corner sealed (the W wall
// run stops at y=-540), then the South Workshop's gap x[-540,-380], then the
// run to the bay door.
baseWallRun('base wall S w corner', -(ARENA + WALL), -ARENA, -(ARENA + WALL), -ARENA);
baseWallRun('base wall S w', WINGS[2].dc + 80, -TPB_DOOR, -(ARENA + WALL), -ARENA);
baseWallRun('base wall S e', TPB_DOOR, ARENA + WALL, -(ARENA + WALL), -ARENA);
// N wall: the North Workshop's gap x[-80,80] in the middle (the perk park row
// is re-pitched 4 + 4 around it — see PERK_PARK).
baseWallRun('base wall N w', -(ARENA + WALL), WINGS[0].dc - 80, ARENA, ARENA + WALL);
baseWallRun('base wall N e', WINGS[0].dc + 80, ARENA + WALL, ARENA, ARENA + WALL);
// W wall: the Undercity exit y[-240,-80] (south half) and the West Workshop
// y[320,480] (north half).
baseWallRun('base wall W s', -(ARENA + WALL), -ARENA, -ARENA, WEXIT_Y[0]);
baseWallRun('base wall W m', -(ARENA + WALL), -ARENA, WEXIT_Y[1], WINGS[3].dc - 80);
baseWallRun('base wall W n', -(ARENA + WALL), -ARENA, WINGS[3].dc + 80, ARENA);
addBox('base doorway lintel W exit', -(ARENA + WALL), -ARENA, WEXIT_Y[0], WEXIT_Y[1], BASE_WALL_H, BASE_WALL_H + 20, MAT.pilaster);
// base wall E: SPLIT — the power hallway passes through at y[-540,-420]
// (user 2026-08-20: "hallway needs to be like 5x longer" — it now runs
// outside the arena to x=1640; see the POWER ROOM section), and the East
// Workshop's gap y[300,460] (docs/158).
baseWallRun('base wall E s', ARENA, ARENA + WALL, -420, WINGS[1].dc - 80);
baseWallRun('base wall E n', ARENA, ARENA + WALL, WINGS[1].dc + 80, ARENA);
// v18.99g — THE DOORWAY LINTELS. The cornice is emitted per WALL RUN, and the
// south and east walls are SPLIT around their doorways, so the 20-tall cyan band
// that caps every other inch of the arena simply stopped at each opening. That
// left a genuinely open slot above each door — 320 x 20 over the teleport bay,
// 120 x 20 over the power hallway — and because the annex beyond is itself only
// BASE_WALL_H tall and open-topped, what you saw through that slot was SKY. On
// the screenshot that reported the door "reflection bug" it reads as the city
// showing through the top of the door, which is a separate defect from the
// mirror finish fixed in MAT.door, and it is a real hole, not a material.
// Only the visible band is added: the anti-vault clip above these openings
// already runs BASE_WALL_H..BASE_CLIP_TOP, so nothing about collision or the
// 128-unit walk-through clearance changes.
// v19.18c (user 2026-09-16: "remove the top part of the bay door ... because
// it's blocking zombies from launching into the hole"): the SOUTH doorway
// lintel is GONE again, and so is the invisible wall-hop clip over that
// opening — `base clip S` is split around x[-TPB_DOOR, TPB_DOOR] below. From
// the teleport bay the band and the clip together were the bar every bat
// fling hit on its way to the hoop. The 320-wide notch above the bay door is
// open sky by design now; the doorway's own anti-vault clip rides in the door
// slab and still seals it until the door is bought.
addBox('base doorway lintel E', ARENA, ARENA + WALL, -ARENA, -420,
       BASE_WALL_H, BASE_WALL_H + 20, MAT.pilaster);
// BASE_CLIP_TOP (user 2026-08-20 "invisible walls on the platforms"): the
// enlarged breather balconies extend to y/x ±816 — PAST the arena clip planes
// at ±540..560 — so full-height clips cut invisible walls straight across
// every breather. Cap them below the first breather floor (floor 5 mid slab
// bottom = 1712); the clips only need to stop base-arena wall-hops anyway.
const BASE_CLIP_TOP = 1600;
addBox('base clip S w', -(ARENA + WALL), -TPB_DOOR, -(ARENA + WALL), -ARENA, BASE_WALL_H, BASE_CLIP_TOP, MAT.clip);
addBox('base clip S e', TPB_DOOR, ARENA + WALL, -(ARENA + WALL), -ARENA, BASE_WALL_H, BASE_CLIP_TOP, MAT.clip);
addBox('base clip N', -(ARENA + WALL), ARENA + WALL, ARENA, ARENA + WALL, BASE_WALL_H, BASE_CLIP_TOP, MAT.clip);
addBox('base clip W', -(ARENA + WALL), -ARENA, -ARENA, ARENA, BASE_WALL_H, BASE_CLIP_TOP, MAT.clip);
addBox('base clip E', ARENA, ARENA + WALL, -420, ARENA, BASE_WALL_H, BASE_CLIP_TOP, MAT.clip);
// clip ABOVE the hallway pass-through (the wall line stays sealed over z=128)
addBox('power hall doorway clip', ARENA, ARENA + WALL, -ARENA, -420, BASE_WALL_H, BASE_CLIP_TOP, MAT.clip);

// THE BASE AMMO CRATE (v14.3) — core WEST face. This is the single source of
// truth for its position: the collision clip is cut HERE (exactly like the
// five breather/crown crates — the model ships NO collision data) and the
// origin/yaw are emitted into GENERATED _tod_breather_data.gsc
// (base_crate_org/base_crate_yaw), which _tod_ammo_crate.gsc reads — the
// door-data no-drift contract. HISTORY THAT MUST NOT REPEAT: v13.23 placed
// this crate script-side at (320,0,0) — "the emptiest base wall" — which is
// the strip UNDER LAP 1'S EAST FLIGHT (x[256,416], the very strip the
// teleport bay was moved out of, see the TPB note near the top), and its
// three script-clip DisconnectPaths carves severed the stair navmesh both
// ways (Workshop report Pinkbrotha4310 2026-08-30). A wall strip is "empty"
// precisely when a flight runs over it. The asserts below make that mistake
// mechanical: the geometry lint CANNOT see script collision, and now there
// is none — the clip is a real brush the lint and the navmesh compiler both
// understand. FACING AND COLLISION both come from the one crate convention
// above (CRATE_YAW_W / crateBox) — never re-type an occupancy box here.
const BASE_CRATE = { org: [-320, 0], yaw: CRATE_YAW_W };
// The four PARTNER BENCHES stood along the north wall here (a peer session's
// first placement, 2026-09-23); docs/158 moves each into its own workshop
// wing. Their collision clips are cut in the wing loop (label `wing <k>
// partner bench body`, exempt from the geometry lint's misplaced-wall rule
// like the crate bodies, for the same reason: p8_zm_crafting_table ships no
// collision) and their origins are EMITTED to _tod_breather_data.gsc, which
// _tod_partners::stations() reads. Nothing about a bench is typed twice.
{
  const [bcx, bcy] = BASE_CRATE.org;
  const box = crateBox(bcx, bcy, BASE_CRATE.yaw);   // z 0..CRATE_BOX_H
  // 1. NEVER inside a ground-level flight footprint (+24u margin). The only
  //    flight at base z is lap 1's E flight (odd laps climb E+N): x[CORE,PX],
  //    y[-CORE,CORE], z 0..192 — the Pinkbrotha strip.
  if (box.x2 > CORE - 24 && box.x1 < PX + 24 && box.y2 > -CORE - 24 && box.y1 < CORE + 24)
    throw new Error('base ammo crate box overlaps the lap-1 E flight footprint (the v13.23 navmesh break) — move BASE_CRATE');
  // 2. It must BACK the core's west face (a crate floating mid-arena is a
  //    different design and would need its own review): back edge within 64u
  //    of x=-CORE and not inside the core.
  if (box.x2 > -CORE || box.x2 < -CORE - 64)
    throw new Error('base ammo crate no longer backs the core west face — re-review the placement');
  // 3. The walkway past its front must stay at least a doorway wide (128u)
  //    to the arena W wall inner face, so the clip can never become a choke.
  if (box.x1 - (-ARENA) < 128)
    throw new Error(`base ammo crate leaves only ${box.x1 + ARENA}u of west walkway — needs >= 128`);
  addBox('base ammo crate body', box.x1, box.x2, box.y1, box.y2, 0, CRATE_BOX_H, MAT.clip);
}

// THE CYBERCITY SIGN (docs/208, map 1's v19.69 / v19.71 ported): Nikolai's TOWER OF DOOM /
// CYBERCITY neon sign, map 1's relief rebuild `tod_cybercity_sign2`, on the core's WEST face
// over the base ammo crate - map 1's spawn wall, this map's Ground Floor: the bottom of the
// descent. A script_model (_tod_base_sign.gsc, OFF until the power, then a neon start); its
// anchor rides into _tod_breather_data.gsc (base_sign_org/_yaw). SIZE = the relief's measured
// bounds (map 1 art/fan_props/sign_relief.json: x 0..24.201 off the wall, y +-128, z 0.239..
// 118.99), pinned here because tools/fan_props/manifest.json pins the binary. Front = model +X,
// origin = its back plane, horizontal centre, bottom edge; yaw 180 faces west.
const BASE_SIGN = { y: 0, z1: 160, proud: 0.5, yaw: 180, size: [24.201, 256, 118.99] };
// A STEEP CAP (map 1's v19.71 perch-cap shape, without its deferred wall search): a clip wedge
// whose flat bottom sits on a ledge and whose top rises CAP_SLOPE per unit toward `back` (a unit
// axis into the wall), its high edge buried `bury` (CAP_BURY) into that wall - no flat top anywhere,
// so nothing can stand on it; a free-standing prop passes bury 0 (its high edge is a free edge, the
// slope's own, with a sheer face behind it). 3.5 = 74 degrees (map 1 measured: 56 still standable, 72 not).
const CAP_SLOPE = 3.5, CAP_BURY = 16;
function steepCap(label, fp, zBot, back, tex, bury = CAP_BURY) {
  if (Math.abs(back[0]) + Math.abs(back[1]) !== 1) throw new Error(`steepCap ${label}: back must be a unit axis`);
  // in a frame where `back` is +u: u0 = the open front edge, u1 = the buried back edge; v = across
  const along = back[0] !== 0 ? 0 : 1, s = back[along];
  const lo = along === 0 ? [fp.x1, fp.y1] : [fp.y1, fp.x1], hi = along === 0 ? [fp.x2, fp.y2] : [fp.y2, fp.x2];
  const u0 = s > 0 ? lo[0] : hi[0], u1 = (s > 0 ? hi[0] : lo[0]) + s * bury, v1 = lo[1], v2 = hi[1];
  const zTop = (u) => zBot + 1 + Math.abs(u - u0) * CAP_SLOPE;   // a 1-unit front face, then the slope
  const P = (u, v, z) => (along === 0 ? [u, v, z] : [v, u, z]);
  // six planes, outward normals by the (p1 - p2) x (p3 - p2) rule rampPlane writes
  const pts = [
    [P(u0, v1, zBot), P(u1, v1, zBot), P(u1, v2, zBot)],                                // bottom
    [P(u0, v2, zTop(u0)), P(u1, v2, zTop(u1)), P(u1, v1, zTop(u1))],                    // top (sloped)
    [P(u0, v1, zBot), P(u0, v2, zBot), P(u0, v2, zTop(u0))],                            // front
    [P(u1, v2, zBot), P(u1, v1, zBot), P(u1, v1, zTop(u1))],                            // back (buried)
    [P(u0, v1, zBot), P(u0, v1, zTop(u0)), P(u1, v1, zTop(u1))],                        // side v1
    [P(u1, v2, zBot), P(u1, v2, zTop(u1)), P(u0, v2, zTop(u0))],                        // side v2
  ];
  // orient every plane outward against the wedge's own centroid (no winding mistakes possible)
  const cen = [0, 1, 2].map(i => pts.flat().reduce((a, p) => a + p[i], 0) / 18);
  const planes = pts.map(([a, b, c]) => {
    const n = CB.cross(CB.sub(a, b), CB.sub(c, b));
    return CB.dot(n, CB.sub(cen, b)) > 0 ? [c, b, a] : [a, b, c];
  });
  rampWedge(label, planes, tex);
  const xs = [P(u0, v1, 0)[0], P(u1, v2, 0)[0]], ys = [P(u0, v1, 0)[1], P(u1, v2, 0)[1]];
  allBoxes.push({ label, x1: Math.min(...xs), x2: Math.max(...xs), y1: Math.min(...ys), y2: Math.max(...ys), z1: zBot, z2: zTop(u1), tex });
}
{
  const [d, w, h] = BASE_SIGN.size;                // x = off the wall, y = across, z = up
  const y1 = BASE_SIGN.y - w / 2, y2 = BASE_SIGN.y + w / 2, z2 = BASE_SIGN.z1 + h;
  // 1. ON the face, 32 clear of both corners (the corners are where the flights turn).
  if (y1 < -CORE + 32 || y2 > CORE - 32) throw new Error(`base sign y[${y1},${y2}] runs off the core west face`);
  // 2. UNDER lap 2's W flight, which climbs over this face from z 384: 64 below the lowest
  //    tread underside anywhere over the sign's span (the cap stays under it too).
  let under = Infinity;
  for (let i = 1; i <= STEPS; i++) {
    const ty1 = CORE - TREAD * i, ty2 = CORE - TREAD * (i - 1);
    if (ty2 > y1 && ty1 < y2) under = Math.min(under, LAP_RISE + RISE * i - SLAB);
  }
  if (z2 > under - 64) throw new Error(`base sign top ${z2} is within 64 of the lap-2 W flight underside (${under})`);
  // 3. ABOVE the base ammo crate standing under it: 32 clear of its body top.
  const cb = crateBox(BASE_CRATE.org[0], BASE_CRATE.org[1], BASE_CRATE.yaw);
  if (cb.y2 > y1 && cb.y1 < y2 && BASE_SIGN.z1 < CRATE_BOX_H + 32) throw new Error(`base sign bottom ${BASE_SIGN.z1} sits within 32 of the base ammo crate (${CRATE_BOX_H})`);
  // 4. Its face stands no further out than the crate's, so nothing at head height juts
  //    past the furniture line of the west walkway.
  if (-CORE - BASE_SIGN.proud - d < cb.x1) throw new Error('base sign stands further off the core than the base ammo crate');
  // 5. ITS BODY: a clip box round the relief (1 unit of air each side, so a body meets the clip
  //    before the mesh) and a steep cap on its top ledge, leaning into the core - a Breacher's
  //    launch must not find a flat place to stand up there. The cap must stay under the flight.
  const sx1 = Math.floor(-CORE - BASE_SIGN.proud - d - 1), sy1 = Math.floor(y1 - 1), sy2 = Math.ceil(y2 + 1), sz2 = Math.ceil(z2 + 1);
  addBox('base sign body', sx1, -CORE, sy1, sy2, BASE_SIGN.z1 - 1, sz2, MAT.clip);
  const capTopAtFace = sz2 + 1 + (-CORE - sx1) * CAP_SLOPE;
  if (capTopAtFace > under - 16) throw new Error(`base sign cap reaches ${capTopAtFace} at the core face, within 16 of the lap-2 W flight underside (${under})`);
  steepCap('base sign cap', { x1: sx1, x2: -CORE, y1: sy1, y2: sy2 }, sz2, [1, 0], MAT.clip);
}

// ---------------------------------------------------------------------------
// 2b. THE UNDERCITY (docs/158) — the Vault, the Conduit, the Shaft. z = UC_Z.
// ---------------------------------------------------------------------------
// Materials: floors are MAT.ground (dark_blue_tinted, DECK to the lint — the
// crown hall floor's material), walls the plinth's plain dark_blue with a cyan
// seam band, ceilings plain dark_blue (BLOCK: a `_tinted` ceiling slab would be
// a detached floor 192 units up to the lint), window backs the ruby seam.
const ucFloor = (label, x1, x2, y1, y2) => addBox(label, x1, x2, y1, y2, UC_Z - SLAB, UC_Z, MAT.ground);
const ucCeil  = (label, x1, x2, y1, y2) => addBox(label, x1, x2, y1, y2, UC_TOP, UC_TOP + UC_CEIL_T, MAT.baseColumn);
function ucWall(label, x1, x2, y1, y2) {   // three bands: dark / cyan seam / dark
  addBox(`${label} lower`, x1, x2, y1, y2, UC_Z, UC_Z + UC_BAND_Z, MAT.baseColumn);
  addBox(`${label} seam`,  x1, x2, y1, y2, UC_Z + UC_BAND_Z, UC_Z + UC_BAND_Z + 16, MAT.pilaster);
  addBox(`${label} upper`, x1, x2, y1, y2, UC_Z + UC_BAND_Z + 16, UC_TOP, MAT.baseColumn);
}
// A WINDOW NICHE on one of the Vault's walls. d = depth measured OUTWARD from
// the wall's inner face (the wall band is d[0,WALL]); c = the cross coordinate.
// The vault's floor and ceiling already cover the band; the niche adds its own
// floor/roof beyond it. Floor is PLAIN (BLOCK) so the lint invents no floor
// nodes inside a room players cannot enter; the mouth's clip_player is what
// keeps them out and what lets a zombie walk through (navmesh ignores it).
const VAULT_RISERS = [];
function ucWindow(win, i) {
  const map = (d, c) => (win.side === 'W' ? [VT_X1 - d, c] : win.side === 'E' ? [VT_X2 + d, c] : [c, VT_Y1 - d]);
  const nb = (label, d1, d2, c1, c2, z1, z2, mat) => {
    const [ax1, ay1] = map(d1, c1), [ax2, ay2] = map(d2, c2);
    addBox(`vault window ${i + 1} ${label}`, Math.min(ax1, ax2), Math.max(ax1, ax2), Math.min(ay1, ay2), Math.max(ay1, ay2), z1, z2, mat);
  };
  const c = win.c, h = WIN_W / 2, D = WALL + WIN_D;   // the niche interior runs d[WALL, D]
  nb('floor',     WALL, D + WALL, c - h - WALL, c + h + WALL, UC_Z - SLAB, UC_Z, MAT.baseColumn);
  nb('back',      D, D + WALL, c - h - WALL, c + h + WALL, UC_Z, UC_Z + WIN_H, MAT.jewelRuby);   // the lit red panel the zombie stands against
  nb('side a',    WALL, D, c - h - WALL, c - h, UC_Z, UC_Z + WIN_H, MAT.baseColumn);
  nb('side b',    WALL, D, c + h, c + h + WALL, UC_Z, UC_Z + WIN_H, MAT.baseColumn);
  nb('roof',      WALL, D + WALL, c - h - WALL, c + h + WALL, UC_Z + WIN_H, UC_TOP + UC_CEIL_T, MAT.baseColumn);
  nb('lintel',    0, WALL, c - h, c + h, UC_Z + WIN_H, UC_TOP, MAT.baseColumn);   // over the mouth, inside the wall band
  nb('sill',      0, WALL, c - h, c + h, UC_Z, UC_Z + WIN_SILL, MAT.pilaster);
  nb('mouth clip', 0, WALL, c - h, c + h, UC_Z + WIN_SILL, UC_Z + WIN_H, MAT.winClip);
  const [rx, ry] = map(WALL + WIN_D / 2 + 10, c);   // 58 past the inner face: mid-niche
  VAULT_RISERS.push([rx, ry, UC_Z]);
  return map;
}
{
  // ---- THE VAULT ------------------------------------------------------------
  const X1 = VT_X1 - WALL, X2 = VT_X2 + WALL, Y1 = VT_Y1 - WALL;   // outer faces (N band = the shared wall)
  ucFloor('vault floor', X1, X2, Y1, VT_Y2);
  ucCeil('vault ceiling', X1, X2, Y1, VT_Y2);
  const winsS = VAULT_WINDOWS.filter(w => w.side === 'S').map(w => w.c).sort((a, b) => a - b);
  const winW = VAULT_WINDOWS.find(w => w.side === 'W').c, winE = VAULT_WINDOWS.find(w => w.side === 'E').c;
  // S wall, split around its two windows
  ucWall('vault wall S a', X1, winsS[0] - WIN_W / 2, Y1, VT_Y1);
  ucWall('vault wall S b', winsS[0] + WIN_W / 2, winsS[1] - WIN_W / 2, Y1, VT_Y1);
  ucWall('vault wall S c', winsS[1] + WIN_W / 2, X2, Y1, VT_Y1);
  // W and E walls, split around their window
  ucWall('vault wall W a', X1, VT_X1, VT_Y1, winW - WIN_W / 2);
  ucWall('vault wall W b', X1, VT_X1, winW + WIN_W / 2, VT_Y2);
  ucWall('vault wall E a', VT_X2, X2, VT_Y1, winE - WIN_W / 2);
  ucWall('vault wall E b', VT_X2, X2, winE + WIN_W / 2, VT_Y2);
  // N wall = THE SHARED BAND with the Conduit (its S wall), carrying enter_conduit
  ucWall('vault wall N a', X1, CONDUIT_DOOR_X - 80, VT_Y2, VT_Y2 + WALL);
  ucWall('vault wall N b', CONDUIT_DOOR_X + 80, X2, VT_Y2, VT_Y2 + WALL);
  addBox('vault door lintel', CONDUIT_DOOR_X - 80, CONDUIT_DOOR_X + 80, VT_Y2, VT_Y2 + WALL, UC_Z + 128, UC_TOP, MAT.baseColumn);
  VAULT_WINDOWS.forEach(ucWindow);
  // four cyan corner pilasters and two ceiling beams — the room's structure
  for (const [px, py] of [[VT_X1, VT_Y1], [VT_X2 - 40, VT_Y1], [VT_X1, VT_Y2 - 40], [VT_X2 - 40, VT_Y2 - 40]])
    addBox('vault pilaster', px, px + 40, py, py + 40, UC_Z, UC_TOP, MAT.pilaster);
  addBox('vault beam a', VT_X1 + 40, VT_X2 - 40, VT_CY - 160 - 24, VT_CY - 160 + 24, UC_TOP - 24, UC_TOP, MAT.pilaster);
  addBox('vault beam b', VT_X1 + 40, VT_X2 - 40, VT_CY + 160 - 24, VT_CY + 160 + 24, UC_TOP - 24, UC_TOP, MAT.pilaster);
  // the wayfinding trace: from the spawn rows north to the door (1u decal)
  addBox('vault trace', VT_CX - 20, VT_CX + 20, VT_CY - 72, VT_Y2, UC_Z, UC_Z + 1, MAT.baseInlay);
  navSeed('vault centre', VT_CX, VT_CY, UC_Z + 2);

  // ---- THE CONDUIT ----------------------------------------------------------
  const CX1 = CD_X1 - WALL, CX2 = CD_X2 + WALL, CY2 = CD_Y2 + WALL;   // its S band is the vault's N wall
  ucFloor('conduit floor', CX1, CX2, VT_Y2, CY2);
  ucCeil('conduit ceiling', CX1, CX2, VT_Y2, CY2);
  ucWall('conduit wall W', CX1, CD_X1, CD_Y1, CY2);   // from the shared band's north face
  ucWall('conduit wall N', CX1, CX2, CD_Y2, CY2);
  // E wall around the shaft mouth (the foot landing is 256 wide, y = SHAFT_CY +- SHAFT_HW)
  ucWall('conduit wall E a', CD_X2, CX2, CD_Y1, SHAFT_CY - SHAFT_HW);
  ucWall('conduit wall E b', CD_X2, CX2, SHAFT_CY + SHAFT_HW, CY2);
  // THE CAP over the mouth: from the ceiling top up to the shaft walls' top, so
  // the open-topped shaft is sealed westward above the Conduit's roof.
  addBox('conduit mouth cap', CD_X2, CX2, SHAFT_CY - SHAFT_HW - WALL, SHAFT_CY + SHAFT_HW + WALL, UC_TOP + UC_CEIL_T, BASE_WALL_H, MAT.baseWall);
  addBox('conduit mouth cap clip', CD_X2, CX2, SHAFT_CY - SHAFT_HW - WALL, SHAFT_CY + SHAFT_HW + WALL, BASE_WALL_H, 800, MAT.clip);
  addBox('conduit beam a', CD_X1, CD_X2, CD_Y1 + 160 - 24, CD_Y1 + 160 + 24, UC_TOP - 24, UC_TOP, MAT.pilaster);
  addBox('conduit beam b', CD_X1, CD_X2, CD_Y2 - 160 - 24, CD_Y2 - 160 + 24, UC_TOP - 24, UC_TOP, MAT.pilaster);
  // the trace: door -> north to the shaft axis -> east to the foot landing (two abutting pieces)
  addBox('conduit trace n', VT_CX - 20, VT_CX + 20, VT_Y2 + WALL, SHAFT_CY - 20, UC_Z, UC_Z + 1, MAT.baseInlay);
  addBox('conduit trace e', VT_CX - 20, CD_X2, SHAFT_CY - 20, SHAFT_CY + 20, UC_Z, UC_Z + 1, MAT.baseInlay);
  navSeed('conduit centre', (CD_X1 + CD_X2) / 2, SHAFT_CY, UC_Z + 2);

  // ---- THE SHAFT ------------------------------------------------------------
  const SY1 = SHAFT_CY - SHAFT_HW, SY2 = SHAFT_CY + SHAFT_HW;     // -288 / -32
  const SX2 = SHAFT_TOP_X2;                                       // -560
  for (const [tag, y1, y2] of [['shaft wall S', SY1 - WALL, SY1], ['shaft wall N', SY2, SY2 + WALL]]) {
    addBox(`${tag} lower`, CX2, SX2, y1, y2, UC_Z - SLAB, UC_TOP, MAT.baseColumn);   // underground band
    addBox(`${tag} seam`,  CX2, SX2, y1, y2, UC_TOP, UC_TOP + UC_CEIL_T, MAT.pilaster); // the ceiling line, as a cyan seam
    addBox(`${tag} upper`, CX2, SX2, y1, y2, UC_TOP + UC_CEIL_T, BASE_WALL_H, MAT.baseWall);   // the plaza's blue above ground
    addBox(`${tag} clip`,  CX2, SX2, y1, y2, BASE_WALL_H, 800, MAT.clip);
  }
  addBox('shaft foot landing', CX2, SHAFT_FLT_X1, SY1, SY2, UC_Z - SLAB, UC_Z, edgeMatOf(0));
  for (let i = 1; i <= UC_STEPS; i++)
    addBox(`shaft step ${i}`, SHAFT_FLT_X1 + TREAD * (i - 1), SHAFT_FLT_X1 + TREAD * i, SY1, SY2, UC_Z + RISE * i - SLAB, UC_Z + RISE * i, stepMatOf(0));
  addBox('shaft under-flight fill', SHAFT_FLT_X1, SHAFT_FLT_X2, SY1, SY2, UC_Z - SLAB, UC_Z + RISE - SLAB, MAT.baseColumn);
  addBox('shaft top landing', SHAFT_TOP_X1, SX2, SY1, SY2, -SLAB, 0, edgeMatOf(0));
  addBox('shaft top landing fill', SHAFT_TOP_X1, SX2, SY1, SY2, UC_Z - SLAB, -SLAB, MAT.baseColumn);
  if (STAIR_RAMP_CLIP) {
    // nosing line from one TREAD before the first riser (feathering over the
    // foot landing) to tread 32's front edge, exactly the tower's recipe.
    rampWedgeX('undercity shaft ramp', SY1, SY2, SHAFT_FLT_X1 - TREAD, SHAFT_FLT_X2 - TREAD, UC_Z, UC_Z + LAP_RISE, MAT.rampClip);
  }
  navSeed('shaft foot', (CX2 + SHAFT_FLT_X1) / 2, SHAFT_CY, UC_Z + 2);
  navSeed('shaft top', (SHAFT_TOP_X1 + SX2) / 2, SHAFT_CY, 2);
  console.log(`  undercity: vault x[${VT_X1},${VT_X2}] y[${VT_Y1},${VT_Y2}], conduit x[${CD_X1},${CD_X2}] y[${CD_Y1},${CD_Y2}], shaft ${UC_STEPS} treads x[${SHAFT_FLT_X1},${SHAFT_FLT_X2}] -> door y[${WEXIT_Y}], z ${UC_Z}`);
}

// ---------------------------------------------------------------------------
// 2c. THE WORKSHOP WINGS (docs/158) — one per plaza wall, in the local frame
// (u outward, v across; see wingFrame). Hallway 160 wide, room 512 square,
// bench on the far wall facing the entrance, two risers by the entrance
// corners, the wing's hue on the far panel / floor ring / hallway band.
// ---------------------------------------------------------------------------
const WING_RISERS = {};
for (const w of WINGS) {
  const F = wingFrame(w), { box } = F;
  const dc = w.dc, rc = w.rc, R = WING_ROOM / 2;
  const mHue = `mwiii_vertigo_retro_synth_${w.hue}`, mPanel = `mwiii_vertigo_retro_synth_${w.hue}_tinted`;
  const mFloor = MAT.ground;
  // the doorway's cyan lintel in the arena wall (the cornice continues)
  box('door lintel', ARENA, WU0, dc - 80, dc + 80, BASE_WALL_H, BASE_WALL_H + 20, MAT.pilaster);
  // HALLWAY: floor, two banded walls, clips
  box('hall floor', WU0, WU_HALL_END, dc - 100, dc + 100, -SLAB, 0, mFloor);
  for (const [tag, v1, v2] of [['hall wall a', dc - 100, dc - 80], ['hall wall b', dc + 80, dc + 100]]) {
    box(`${tag} lower`, WU0, WU_HALL_END, v1, v2, 0, 60, MAT.baseWall);
    box(`${tag} band`,  WU0, WU_HALL_END, v1, v2, 60, 76, mHue);
    box(`${tag} upper`, WU0, WU_HALL_END, v1, v2, 76, BASE_WALL_H, MAT.baseWall);
    box(`${tag} clip`,  WU0, WU_HALL_END, v1, v2, BASE_WALL_H, 800, MAT.clip);
  }
  // ROOM: floor (covers its wall bands), near wall around the mouth, far wall
  // with the hue panel behind the bench, two side walls, clips on all
  box('room floor', WU_HALL_END, WU_ROOM3, rc - R - WALL, rc + R + WALL, -SLAB, 0, mFloor);
  box('room near wall a', WU_HALL_END, WU_ROOM1, rc - R - WALL, dc - 80, 0, BASE_WALL_H, MAT.baseWall);
  box('room near wall b', WU_HALL_END, WU_ROOM1, dc + 80, rc + R + WALL, 0, BASE_WALL_H, MAT.baseWall);
  box('room near clip a', WU_HALL_END, WU_ROOM1, rc - R - WALL, dc - 80, BASE_WALL_H, 800, MAT.clip);
  box('room near clip b', WU_HALL_END, WU_ROOM1, dc + 80, rc + R + WALL, BASE_WALL_H, 800, MAT.clip);
  box('room mouth lintel', WU_HALL_END, WU_ROOM1, dc - 80, dc + 80, BASE_WALL_H, BASE_WALL_H + 20, mHue);
  box('room far wall a', WU_ROOM2, WU_ROOM3, rc - R - WALL, rc - 128, 0, BASE_WALL_H, MAT.baseWall);
  box('room far panel',  WU_ROOM2, WU_ROOM3, rc - 128, rc + 128, 0, BASE_WALL_H, mPanel);
  box('room far wall b', WU_ROOM2, WU_ROOM3, rc + 128, rc + R + WALL, 0, BASE_WALL_H, MAT.baseWall);
  box('room far clip',   WU_ROOM2, WU_ROOM3, rc - R - WALL, rc + R + WALL, BASE_WALL_H, 800, MAT.clip);
  box('room side wall a', WU_HALL_END, WU_ROOM3, rc - R - WALL, rc - R, 0, BASE_WALL_H, MAT.baseWall);
  box('room side wall b', WU_HALL_END, WU_ROOM3, rc + R, rc + R + WALL, 0, BASE_WALL_H, MAT.baseWall);
  box('room side clip a', WU_HALL_END, WU_ROOM3, rc - R - WALL, rc - R, BASE_WALL_H, 800, MAT.clip);
  box('room side clip b', WU_HALL_END, WU_ROOM3, rc + R, rc + R + WALL, BASE_WALL_H, 800, MAT.clip);
  // INLAYS (1u decals; every pair ABUTS, none overlap — the coplanar rule)
  box('runner',      WU0 + 20, WU_ROOM1 + 20, dc - 20, dc + 20, 0, 1, mPanel);              // door -> into the room
  box('ring near',   WU_ROOM1 + 20, WU_ROOM1 + 60, rc - 236, rc + 236, 0, 1, mPanel);
  box('ring side a', WU_ROOM1 + 60, WU_ROOM2 - 60, rc - 236, rc - 196, 0, 1, mPanel);
  box('ring side b', WU_ROOM1 + 60, WU_ROOM2 - 60, rc + 196, rc + 236, 0, 1, mPanel);
  box('ring far a',  WU_ROOM2 - 60, WU_ROOM2 - 20, rc - 236, rc - 64, 0, 1, mPanel);         // split around the bench body
  box('ring far b',  WU_ROOM2 - 60, WU_ROOM2 - 20, rc + 64, rc + 236, 0, 1, mPanel);
  // THE BENCH BODY (a script model with no collision — the crate rule)
  box('partner bench body', WU_BENCH - BENCH_FRONT, WU_BENCH + BENCH_BACK, rc - BENCH_ACROSS, rc + BENCH_ACROSS, 0, BENCH_H, MAT.clip);
  // risers by the entrance corners (they rise between a bench camper and the
  // way out), the dog point mid-room, a navmesh seed in the hallway
  WING_RISERS[w.key] = [[...F.pt(WU_ROOM1 + 56, rc - 200), 0], [...F.pt(WU_ROOM1 + 56, rc + 200), 0]];
  navSeed(`wing ${w.key} hallway`, ...F.pt(WU0 + WING_HALL_L / 2, dc), 2);
  // ASSERTS: the bench trigger (57 in front, r48) clears both risers by the
  // rule's 64u; the door's inner sphere clears the room (trivially) and the
  // wing's own risers sit inside its zone box.
  const [bx, by] = F.pt(WU_BENCH - 57, rc);
  for (const [rx, ry] of WING_RISERS[w.key])
    if (Math.hypot(rx - bx, ry - by) < 48 + 64) throw new Error(`wing ${w.key}: a riser is inside the bench trigger`);
}
console.log(`  wings: ${WINGS.map(w => `${w.key}=${w.dest.replace('the ', '')}(${w.hue}, partner ${w.partner})`).join(' ')}`);

// ---------------------------------------------------------------------------
// 3. The core (one palette band per lap; its top IS the rooftop)
// ---------------------------------------------------------------------------
// v16.13 FACELIFT §7 — CORE SPINES. The core was one 512-square box per lap
// with nothing on any face for 19,200 units. Each band is now SPLIT INTO A
// CROSS: a CORE_SPINE_W-wide bar across the middle of each face, full height,
// in the district's PLAIN hue (the parapets' bright material — it reads
// against both the `_tinted` and the `_tinted_edge` bands the treads
// alternate through), and four corner blocks in the band material as before.
// Seven boxes tile the same volume exactly (no overlap, no coplanar overlap —
// adjacent faces on the same plane are side by side), so the surface area
// and the lit area are unchanged, nothing protrudes into a tread, and the
// lint sees the same solid column. Four unbroken lit lines run from the
// base to the crown and change colour at every district. Every flight runs
// along the core, so this is the surface a player looks at most.
const CORE_SPINE_W = 32;

// THE HOOP (v19.18, user 2026-09-16: "a hole inside the tower where you can
// attempt to launch zombies into the hole for like an extra 20 dollars ...
// above the heavenly altar ... in between the heavenly altar and the top part
// of that staircase"). A RECESS cut into the core's SOUTH face directly above
// the base upgrade station (the HEAVENLY GIFT ALTAR, model (0,-320), 127 tall,
// trigger cylinder topping out at 132) and under the floor-2 south flight
// (lap 2 climbs W+S; its lowest tread over the opening bottoms out at ~644).
// A cyan rim proud of the face frames it and a cyan backboard lights the back,
// so it reads as a target from the arena floor. _tod_corpse_cleanup.gsc scores
// a bat-flung body whose spine passes through the box (TOD_HOOP_PTS).
//
// THE BOX IS EMITTED, NOT COPIED: base_hoop_lo/_hi ride into
// _tod_breather_data.gsc from these constants, the same no-drift contract the
// crate, inducer and station anchors use — the target the player sees IS the
// volume the script tests. The recess stays INSIDE lap 1's band (asserted), so
// only lap 1's three south-face boxes are cut; everything else is untouched.
//
// LINT: the recess floor is the top of a MAT.baseColumn block (plain
// `dark_blue`, BLOCK to lint_tod_geometry at any height) and the rim/backboard
// are MAT.pilaster (plain `cyan`, also BLOCK) — nothing here is a `_tinted`
// DECK, so no detached ledge is invented 240 units up the column.
//
// HEIGHT IS THE ONE UNMEASURED NUMBER. LaunchRagdoll's impulse-to-arc mapping
// is not documented anywhere in this repo, so HOOP_Z1 is a first placement,
// and the script logs every fling's apex and landing ([TOD_HOOP] FLIGHT) so a
// single dev playtest says where the bodies actually go. Move HOOP_Z1 from
// that log, never from a guess; it is a full build either way (geometry).
const HOOP_HALF_W  = 48;    // opening half-width: 96 across — a body fits, a miss is a miss
const HOOP_Z1      = 200;   // opening floor (v19.20, user 2026-09-16 after the first real run: "move the hole a little bit down" - 240 -> 200; 68 above the trigger top, the assert's floor is 196)
const HOOP_H       = 96;    // opening height
const HOOP_DEPTH   = 64;    // recess depth into the core (y -256 -> -192)
const HOOP_RIM     = 12;    // rim bar thickness
const HOOP_RIM_OUT = 16;    // rim proud of the face (y -272 -> -256)
const HOOP_BOARD   = 4;     // lit backboard plate at the back of the recess
const HOOP = { x1: -HOOP_HALF_W, x2: HOOP_HALF_W, y1: -CORE, y2: -CORE + HOOP_DEPTH, z1: HOOP_Z1, z2: HOOP_Z1 + HOOP_H };
{
  const STATION_TOP = 132;                                   // trigger cylinder [32, 132]; mesh 127 (station_place)
  if (HOOP.z1 <= STATION_TOP + 64) throw new Error(`hoop floor ${HOOP.z1} is within 64 of the base station's top (${STATION_TOP})`);
  if (HOOP.z2 + HOOP_RIM > LAP_RISE) throw new Error(`hoop (top ${HOOP.z2 + HOOP_RIM}) leaves lap 1's core band (${LAP_RISE}) — the cut only knows how to split lap 1`);
  // Lowest lap-2 S tread whose x-range overlaps the rim: slab bottom must clear the rim top.
  const mid2 = LAP_RISE + FLIGHT_RISE;
  let under = Infinity;
  for (let i = 1; i <= STEPS; i++) {
    const sx1 = -CORE + TREAD * (i - 1), sx2 = -CORE + TREAD * i;
    if (sx2 > HOOP.x1 - HOOP_RIM && sx1 < HOOP.x2 + HOOP_RIM) under = Math.min(under, mid2 + RISE * i - SLAB);
  }
  if (HOOP.z2 + HOOP_RIM >= under - 64) throw new Error(`hoop rim top ${HOOP.z2 + HOOP_RIM} is within 64 of the floor-2 S flight underside (${under})`);
  if (HOOP_HALF_W + HOOP_RIM > CORE) throw new Error('hoop rim wider than the core face');
}
// Emit `box` minus the axis-aligned `hole` as up to six NON-OVERLAPPING boxes
// (x slabs either side, then y slabs front/back of the remaining column, then
// z slabs below/above). A box the hole misses is emitted whole, same label.
function addBoxMinus(label, x1, x2, y1, y2, z1, z2, mat, h) {
  boxMinusParts(label, x1, x2, y1, y2, z1, z2, h, 'hoop', (l, a, b, c, d, e, f) => addBox(l, a, b, c, d, e, f, mat));
}
// The box minus one cut box, as up to six boxes handed to emit(label, x1..z2) - addBoxMinus's
// split (its labels exactly when `noun` is 'hoop'), shared so a second cut can split the pieces
// of the first (the haven band: the porch's cut, then the sunken stair's - docs/202 v6).
function boxMinusParts(label, x1, x2, y1, y2, z1, z2, h, noun, emit) {
  if (!h || h.x1 >= x2 || h.x2 <= x1 || h.y1 >= y2 || h.y2 <= y1 || h.z1 >= z2 || h.z2 <= z1) { emit(label, x1, x2, y1, y2, z1, z2); return; }
  const cx1 = Math.max(x1, h.x1), cx2 = Math.min(x2, h.x2);
  const cy1 = Math.max(y1, h.y1), cy2 = Math.min(y2, h.y2);
  const cz1 = Math.max(z1, h.z1), cz2 = Math.min(z2, h.z2);
  if (x1 < cx1) emit(`${label} W of ${noun}`, x1, cx1, y1, y2, z1, z2);
  if (cx2 < x2) emit(`${label} E of ${noun}`, cx2, x2, y1, y2, z1, z2);
  if (y1 < cy1) emit(`${label} S of ${noun}`, cx1, cx2, y1, cy1, z1, z2);
  if (cy2 < y2) emit(`${label} N of ${noun}`, cx1, cx2, cy2, y2, z1, z2);
  if (z1 < cz1) emit(`${label} below ${noun}`, cx1, cx2, cy1, cy2, z1, cz1);
  if (cz2 < z2) emit(`${label} above ${noun}`, cx1, cx2, cy1, cy2, cz2, z2);
}
// v17.28 — THE COLUMN'S FOOT WEARS THE FLOOR'S GRID (Workshop, Nikolai: "add
// that black and blue checker to the bottom part of the column of the tower
// outside where the blue purchasable door is"). The lap-1 and lap-2 door
// slabs are cut in beside these quadrants, and a FILLED band at brightness 10
// beside a FILLED door slab at brightness 5 is why the door does not read.
// Plain here means the wall behind the door is black tiles + a grid line and
// the door is the only lit fill in the frame. See the BASE_GRID block.
// One band = seven pieces: the N/S and W/E face bars (sm) and four quadrants (bm).
function corePieces(lap) {
  if (!FACELIFT) return [{ tag: '', x1: -CORE, x2: CORE, y1: -CORE, y2: CORE, mat: stepMatOf(lap), hoop: true }];
  const h = CORE_SPINE_W / 2, sm = paraMatOf(lap);
  const bm = (BASE_GRID && lap < BASE_GRID_LAPS) ? MAT.baseColumn : stepMatOf(lap);
  // The three boxes that own the SOUTH face take the hoop recess on lap 1 (a
  // no-op `hole` everywhere else — addBoxMinus emits the box whole).
  return [
    { tag: ' spine NS', x1: -h, x2: h, y1: -CORE, y2: CORE, mat: sm, hoop: true },   // the N and S face bars
    { tag: ' spine W', x1: -CORE, x2: -h, y1: -h, y2: h, mat: sm },                 // the W face bar
    { tag: ' spine E', x1: h, x2: CORE, y1: -h, y2: h, mat: sm },                   // the E face bar
    { tag: ' NW', x1: -CORE, x2: -h, y1: h, y2: CORE, mat: bm },
    { tag: ' NE', x1: h, x2: CORE, y1: h, y2: CORE, mat: bm },
    { tag: ' SW', x1: -CORE, x2: -h, y1: -CORE, y2: -h, mat: bm, hoop: true },
    { tag: ' SE', x1: h, x2: CORE, y1: -CORE, y2: -h, mat: bm, hoop: true },
  ];
}
// THE HAVEN HALL (docs/202 v2, tools/haven_layout.js CUT): at a haven floor the
// column STOPS under the hall floor (m - SLAB) and resumes VOID_H higher. In the
// two bands between, only the S and W faces stand, as WALL_T-thick walls cut from
// the same seven pieces (so they keep the column's colours and the S and W
// flights read exactly as before); the W wall is open below the arch top over the
// porch. Under the porch fan the column is cut down to PORCH_LOW so every fan cell
// sits on solid column one step above its tread.
const HV = HAVEN.CUT;
for (let lap = 0; lap < LAPS; lap++) {
  const z1 = lap * LAP_RISE, z2 = (lap + 1) * LAP_RISE;
  const hole = (lap === 0) ? HOOP : null;   // the hoop recess lives in lap 1's band only (asserted above)
  const L = `core band lap${lap + 1}`;
  const pieces = corePieces(lap);
  const hallHere = BREATHER_LAPS.has(lap + 1);   // this band holds a hall floor (m = z1 + FLIGHT_RISE)
  const hallBelow = BREATHER_LAPS.has(lap);      // this band is the void over a hall
  if (hallHere && hallBelow) throw new Error(`haven laps ${lap} and ${lap + 1} are adjacent: their halls would share a band`);
  if (!hallHere && !hallBelow) {
    for (const p of pieces) addBoxMinus(`${L}${p.tag}`, p.x1, p.x2, p.y1, p.y2, z1, z2, p.mat, p.hoop ? hole : null);
    continue;
  }
  if (hole) throw new Error('the hoop band cannot hold a haven hall');
  const m = hallHere ? z1 + FLIGHT_RISE : z1 - FLIGHT_RISE;
  let wz1 = z1;
  if (hallHere) {
    const cut = { x1: HV.porch.x1, x2: HV.porch.x2, y1: HV.porch.y1, y2: HV.porch.y2, z1: m + HV.porch.zLo, z2: m - SLAB };
    // docs/202 v6: and the sunken stair's (its foot runs through the core's W face under the W wall)
    const T = HV.trench, stair = { x1: T.x1, x2: T.x2, y1: T.y1, y2: T.y2, z1: m + T.zLo, z2: m + T.zHi };
    for (const p of pieces)
      boxMinusParts(`${L}${p.tag} under the haven`, p.x1, p.x2, p.y1, p.y2, z1, m - SLAB, cut, 'hoop',
        (l, a, b, c, d, e, f) => boxMinusParts(l, a, b, c, d, e, f, stair, 'stair', (l2, a2, b2, c2, d2, e2, f2) => addBox(l2, a2, b2, c2, d2, e2, f2, p.mat)));
    wz1 = m - SLAB;
  }
  const walls = [
    { tag: 'S wall', x1: -CORE, x2: CORE, y1: -CORE, y2: HV.wallIn },
    { tag: 'W wall', x1: -CORE, x2: HV.wallIn, y1: hallHere ? HV.arch.y2 : HV.wallIn, y2: CORE },
  ];
  for (const w of walls) for (const p of pieces) {
    const x1 = Math.max(p.x1, w.x1), x2 = Math.min(p.x2, w.x2), y1 = Math.max(p.y1, w.y1), y2 = Math.min(p.y2, w.y2);
    if (x1 < x2 && y1 < y2) addBox(`${L}${p.tag} haven ${w.tag}`, x1, x2, y1, y2, wz1, z2, p.mat);
  }
}
// THE HOOP'S RIM AND BACKBOARD (see the HOOP block above the loop): four cyan
// bars proud of the south face framing the opening, and a cyan plate at the
// back of the recess (its rear face is buried against the recess back wall, so
// nothing z-fights). Labels start with `core` so measure_lit_area groups them
// with the column. Plain-hue material = BLOCK to the lint at any height.
{
  const rx1 = HOOP.x1 - HOOP_RIM, rx2 = HOOP.x2 + HOOP_RIM, ry1 = -CORE - HOOP_RIM_OUT, ry2 = -CORE;
  addBox('core hoop rim bottom', rx1, rx2, ry1, ry2, HOOP.z1 - HOOP_RIM, HOOP.z1, MAT.pilaster);
  addBox('core hoop rim top',    rx1, rx2, ry1, ry2, HOOP.z2, HOOP.z2 + HOOP_RIM, MAT.pilaster);
  addBox('core hoop rim W',      rx1, HOOP.x1, ry1, ry2, HOOP.z1, HOOP.z2, MAT.pilaster);
  addBox('core hoop rim E',      HOOP.x2, rx2, ry1, ry2, HOOP.z1, HOOP.z2, MAT.pilaster);
  addBox('core hoop backboard',  HOOP.x1, HOOP.x2, HOOP.y2 - HOOP_BOARD, HOOP.y2, HOOP.z1, HOOP.z2, MAT.pilaster);
}
// THE CAPITAL: one more core band carrying the column from the spiral's top
// (TOP) up to the crown deck (TOP2). Its top face IS the middle of the plaza,
// and its east face is the crown stair's inner wall. In the PaP material, so
// the last 192 units of the tower read as the prize from the street.
// (The old z=TOP roof overlay + 4 parapets are GONE — they would now be buried
// inside this band, and the crown deck replaces them wholesale.)
addBox('core capital band', -CORE, CORE, -CORE, CORE, TOP, TOP2, MAT.crownBand);

// ---------------------------------------------------------------------------
// 4. The spiral: flights + landings + parapets, per lap (CCW: E N W S)
// ---------------------------------------------------------------------------
function slabZ(top) { return [top - SLAB, top]; }

// v6 (user 2026-08-20): TWO flights per floor (was four) — each lap = HALF a
// revolution (LAP_RISE 384), floors come twice as fast. Odd floors (1-based)
// climb the EAST+NORTH sides, even floors WEST+SOUTH; the spiral stays
// continuous CCW: E->NE->N->NW | W->SW->S->SE. Breathers ride each floor's
// MID landing (odd: NE balcony N+E; even: SW balcony S+W, mirrored).
for (let lap = 0; lap < LAPS; lap++) {
  const b = lap * LAP_RISE;
  const stepMat = stepMatOf(lap), paraMat = paraMatOf(lap);
  const odd = (lap % 2 === 0);   // 1-based odd floor
  const mid = b + FLIGHT_RISE, end = b + LAP_RISE;

  if (odd) {
    // E flight (x[CORE,PX], y -CORE -> +CORE)
    for (let i = 1; i <= STEPS; i++) {
      const [z1, z2] = slabZ(b + RISE * i);
      addBox(`lap${lap + 1} E step ${i}`, CORE, PX, -CORE + TREAD * (i - 1), -CORE + TREAD * i, z1, z2, stepMat);
    }
    // v16.80 (Workshop: Nikolai 2026-09-03, Pinkbrotha4310 08-30) — THE VOID
    // UNDER THE FIRST FLIGHT WAS A SAFE ROOM. Lap 1's E flight is the only
    // flight whose underside meets a walkable floor (the arena): the pocket
    // opens under the NE landing with 176 of clearance and loses RISE per
    // tread toward the door (~8 at tread 2). The zombie navmesh stops part-way
    // in, a crouched or prone player fits further, and stock find-flesh just
    // SetGoals the player origin — no reachable mesh point, so every zombie
    // and every boss stood still. Filled with VISIBLE stepped solids, one per
    // tread (top = that tread's slab bottom; tread 1's is below the floor),
    // in the arena wall material so it reads as the stair's own underside on
    // sight. Every internal face is buried by construction (fill i's north
    // face by fill i+1 and tread i's slab; west by the core, east by the
    // anti-bypass wall, bottom by the ground slab), so the only lit face is
    // the 160x176 wall closing the mouth under the NE landing. NOT a clip:
    // an invisible fill repeats the v10.3 "invisible barrier under the
    // stairs" report and trips the lint's misplaced-wall rule. The spire's
    // lap 1 (section 6c) carries the identical fill.
    if (lap === 0) {
      for (let i = 2; i <= STEPS; i++)
        addBox(`lap1 E under-stair fill ${i}`, CORE, PX, -CORE + TREAD * (i - 1), -CORE + TREAD * i, b, b + RISE * i - SLAB, MAT.baseWall);
    }
    addBox(`lap${lap + 1} NE landing`, CORE, PX, CORE, PX, ...slabZ(mid), edgeMatOf(lap));
    // N flight (y[CORE,PX], x CORE -> -CORE)
    for (let i = 1; i <= STEPS; i++) {
      const [z1, z2] = slabZ(mid + RISE * i);
      addBox(`lap${lap + 1} N step ${i}`, CORE - TREAD * i, CORE - TREAD * (i - 1), CORE, PX, z1, z2, stepMat);
    }
    // v9: the old odd-only "final NW landing (roof arrival)" special case is
    // GONE. It only fired when LAPS was odd, so v8's LAPS=50 built no arrival
    // at all — the roof was unreachable. EVERY lap now ends on its normal
    // landing, and the CROWN section below grows the final flight off whichever
    // landing the parity actually produced.
    addBox(`lap${lap + 1} NW landing`, -PX, -CORE, CORE, PX, ...slabZ(end), edgeMatOf(lap + 1));
    if (STAIR_RAMP_CLIP) {
      // E flight: nosing line from (y=-CORE-TREAD, z=b) to (y=CORE-TREAD, z=b+192).
      // The low TREAD units feather over the approach floor (SE landing / the
      // arena at lap 1, slab z[b-16,b] — the underside stays buried); the high
      // end face sits exactly in step 16's slab z[b+176,b+192].
      rampWedgeY(`lap${lap + 1} E stair ramp`, CORE, PX, -CORE - TREAD, CORE - TREAD, b, b + FLIGHT_RISE, MAT.rampClip);
      // N flight: mirrored form, sloping down toward +x into the NE landing.
      rampWedgeX(`lap${lap + 1} N stair ramp`, CORE, PX, -CORE + TREAD, CORE + TREAD, mid + FLIGHT_RISE, mid, MAT.rampClip);
    }
  } else {
    // W flight (x[-PX,-CORE], y CORE -> -CORE)
    for (let i = 1; i <= STEPS; i++) {
      const [z1, z2] = slabZ(b + RISE * i);
      addBox(`lap${lap + 1} W step ${i}`, -PX, -CORE, CORE - TREAD * i, CORE - TREAD * (i - 1), z1, z2, stepMat);
    }
    addBox(`lap${lap + 1} SW landing`, -PX, -CORE, -PX, -CORE, ...slabZ(mid), edgeMatOf(lap));
    // S flight (y[-PX,-CORE], x -CORE -> +CORE)
    for (let i = 1; i <= STEPS; i++) {
      const [z1, z2] = slabZ(mid + RISE * i);
      addBox(`lap${lap + 1} S step ${i}`, -CORE + TREAD * (i - 1), -CORE + TREAD * i, -PX, -CORE, z1, z2, stepMat);
    }
    addBox(`lap${lap + 1} SE landing`, CORE, PX, -PX, -CORE, ...slabZ(end), edgeMatOf(lap + 1));
    if (STAIR_RAMP_CLIP) {
      // Point mirrors of the odd lap's pair (x,y -> -x,-y), same welds.
      rampWedgeY(`lap${lap + 1} W stair ramp`, -PX, -CORE, -CORE + TREAD, CORE + TREAD, b + FLIGHT_RISE, b, MAT.rampClip);
      rampWedgeX(`lap${lap + 1} S stair ramp`, -PX, -CORE, -CORE - TREAD, CORE - TREAD, mid, mid + FLIGHT_RISE, MAT.rampClip);
    }
  }

  // THE HAVEN (docs/202 v2, THE HEART) at the floor's MID landing level: the
  // hall over the opened core, its loggia, the porch fan, the galleries' inner
  // rails, the pylons and the rings. Every brush comes from tools/haven_layout.js
  // (labels `lap<L> haven ...`); the S / W walls and the core cut are the core
  // band loop's. On ARENA_LAYOUT.CHAMBER_LAP the field itself is the Battle
  // Arena chamber (its gate at the centre; no walls).
  if (BREATHER_LAPS.has(lap + 1)) {
    if (odd) throw new Error(`haven on odd lap ${lap + 1}: tools/haven_layout.js authors the even frame only`);
    HAVEN.geometry({ box: havenBox, clip: havenClip, poly: havenPoly, bevel: havenBevel,
      rampX: (label, y1, y2, x1, x2, za, zb, rise, tread) => rampWedgeX(label, y1, y2, x1, x2, za, zb, MAT.rampClip, rise, tread) },
      lap + 1, mid, BREATHER_THEME[lap + 1], { postAbove: doorPostAt(lap + 2) });
    // AMMO CRATE COLLISION — the crate model ships NO collision, so the .map
    // carries a clip inside the mesh (lint MODEL_CLIP_COLUMNS: the label MUST end
    // "ammo crate body"), cut by crateBox from the same anchor the data file
    // emits, so clip and model can never drift.
    const [ccx, ccy] = BR_FURN.crate.org;
    const cb = crateBox(ccx, ccy, BR_FURN.crate.yaw);
    addBox(`lap${lap + 1} ammo crate body`, cb.x1, cb.x2, cb.y1, cb.y2, mid, mid + CRATE_BOX_H, MAT.clip);
    const ct = crateTrig(BR_FURN.crate.org, BR_FURN.crate.yaw);
    if (Math.abs(ct[0] - BR_FURN.crate.trig[0]) > 0.01 || Math.abs(ct[1] - BR_FURN.crate.trig[1]) > 0.01)
      throw new Error('haven crate trigger drifted from the crate recipe (crateTrig)');
  }

  // PARAPETS (outer edges + landing corners, per parity)
  if (odd) {
    if (lap === 0) {
      // THE FIRST FLIGHT'S OUTER WALL — a 288-tall slab (not a 56 parapet) so
      // nobody hops onto the stairs from the east gutter past the first door.
      // MATERIAL = the arena WALL material (v9.34, user 2026-08-23: "an
      // invisible wall attached to the stairs near that tight hallway"): the
      // lap-palette neon-edge material it used to wear reads as a faint glow
      // at night, so players walked into an unlit 288-unit barrier they could
      // not see. Same blue as the base walls = reads as a wall on sight.
      addBox('lap1 E parapet (anti-bypass wall)', PX, PX + PARA, -CORE + (doorPostAt(1) ? DOOR_POST_NOTCH : 0), CORE, 0, 288, MAT.baseWall);   // the lap-1 gate post takes the first 10
    } else {
      for (let j = 1; j <= STEPS / PARA_EVERY; j++) {
        const top = b + RISE * PARA_EVERY * j;
        // z1 is top - RISE*(PARA_EVERY-1), NOT top (fixed 2026-08-27, docs/39 §4#7):
        // a parapet box spans PARA_EVERY treads but used to start at the HIGHER
        // tread's top, leaving a 12-tall see-through slot to the void under the
        // rail over every lower tread — ~800 map-wide. The box now drops to the
        // lowest tread it guards. Top face unchanged, so RAIL_CAP_H still holds.
        const y1 = -CORE + TREAD * PARA_EVERY * (j - 1) + ((j === 1 && doorPostAt(lap + 1)) ? DOOR_POST_NOTCH : 0);   // the gate post takes the first 10
        addBox(`lap${lap + 1} E para ${j}`, PX, PX + PARA, y1, -CORE + TREAD * PARA_EVERY * j, top - RISE * (PARA_EVERY - 1), top + RAIL_VIS_H, paraMat);
      }
    }
    for (let j = 1; j <= STEPS / PARA_EVERY; j++) {
      const top = mid + RISE * PARA_EVERY * j;
      addBox(`lap${lap + 1} N para ${j}`, CORE - TREAD * PARA_EVERY * j, CORE - TREAD * PARA_EVERY * (j - 1), PX, PX + PARA, top - RISE * (PARA_EVERY - 1), top + RAIL_VIS_H, paraMat); // ankle gap: see E para
    }
    if (BREATHER_LAPS.has(lap + 1)) {
      addBox(`lap${lap + 1} NE landing para a`, PX, PX + PARA, CORE, PX, mid, mid + RAIL_VIS_H, paraMat);
    } else {
      addBox(`lap${lap + 1} NE landing para a`, PX, PX + PARA, CORE, PX + PARA, mid, mid + RAIL_VIS_H, paraMat);
      addBox(`lap${lap + 1} NE landing para b`, CORE, PX, PX, PX + PARA, mid, mid + RAIL_VIS_H, paraMat);
    }
    // v9: the odd-only "final NW landing para" special case is gone with the
    // landing it railed (see above).
    addBox(`lap${lap + 1} NW landing para a`, -PX - PARA, -PX, CORE + (doorPostAt(lap + 2) ? DOOR_POST_NOTCH : 0), PX + PARA, end, end + RAIL_VIS_H, paraMatOf(lap + 1));   // the next lap's gate post takes the first 10
    addBox(`lap${lap + 1} NW landing para b`, -PX, -CORE, PX, PX + PARA, end, end + RAIL_VIS_H, paraMatOf(lap + 1));
  } else {
    for (let j = 1; j <= STEPS / PARA_EVERY; j++) {
      const top = b + RISE * PARA_EVERY * j;
      const y2 = CORE - TREAD * PARA_EVERY * (j - 1) - ((j === 1 && doorPostAt(lap + 1)) ? DOOR_POST_NOTCH : 0);   // the gate post takes the last 10
      addBox(`lap${lap + 1} W para ${j}`, -PX - PARA, -PX, CORE - TREAD * PARA_EVERY * j, y2, top - RISE * (PARA_EVERY - 1), top + RAIL_VIS_H, paraMat); // ankle gap: see E para
    }
    for (let j = 1; j <= STEPS / PARA_EVERY; j++) {
      const top = mid + RISE * PARA_EVERY * j;
      addBox(`lap${lap + 1} S para ${j}`, -CORE + TREAD * PARA_EVERY * (j - 1), -CORE + TREAD * PARA_EVERY * j, -PX - PARA, -PX, top - RISE * (PARA_EVERY - 1), top + RAIL_VIS_H, paraMat); // ankle gap: see E para
    }
    if (BREATHER_LAPS.has(lap + 1) && HAVEN.OPENS_SW_LANDING) {
      addBox(`lap${lap + 1} SW landing para a`, -PX - PARA, -PX, -PX, -CORE, mid, mid + RAIL_VIS_H, paraMat);
    } else {
      addBox(`lap${lap + 1} SW landing para a`, -PX - PARA, -PX, -PX - PARA, -CORE, mid, mid + RAIL_VIS_H, paraMat);
      addBox(`lap${lap + 1} SW landing para b`, -PX, -CORE, -PX - PARA, -PX, mid, mid + RAIL_VIS_H, paraMat);
    }
    addBox(`lap${lap + 1} SE landing para a`, PX, PX + PARA, -PX - PARA, -CORE - (doorPostAt(lap + 2) ? DOOR_POST_NOTCH : 0), end, end + RAIL_VIS_H, paraMatOf(lap + 1));   // the next lap's gate post takes the last 10
    addBox(`lap${lap + 1} SE landing para b`, CORE, PX, -PX - PARA, -PX, end, end + RAIL_VIS_H, paraMatOf(lap + 1));
  }

  // -------------------------------------------------------------------------
  // RAIL CAPS (v9, user 2026-08-21: "you can just jump on top of the guard
  // rails on the stairs and jump off the map").
  //
  // PARA_H is 56 and a BO3 jump tops out around that — so every rail is a
  // mountable ledge, and from a rail top the drop outside is 19,000 units of
  // nothing. The obvious fix (raise PARA_H) is the WRONG one: the rail would
  // then sit above eye height and the whole point of an open-air spiral over a
  // neon city is that you can SEE the city while you climb.
  //
  // So the rails stay 56 tall and get an invisible CLIP CAP instead: a `clip`
  // volume filling the airspace directly above each rail run. You can still
  // hop onto a rail; you simply cannot get any higher or move outward. And
  // because a clip does not have to follow the stairs, ONE box spans a whole
  // flight's worth of stepped parapet — 4 brushes per lap instead of one per
  // rail segment (~200 total, not ~900, which matters: the LED bake is the
  // gate and it is already at 44.5s).
  //
  // Each cap's bottom sits at the run's LOWEST rail top and its top clears the
  // HIGHEST rail top by RAIL_CAP_H, so no segment is standable. Caps live in
  // the parapet's own x/y band (outside the walkway), so they never pinch the
  // stairs, and they top out far below the next same-side lap (+768).
  // A breather lap OPENS its mid landing into the balcony (the corner rail is
  // omitted there) — so the caps must stop short of that doorway or they wall
  // the balcony off / leave an invisible pillar standing on its floor.
  // v2 (docs/202): the haven hall opens off the W flight's porch, not the SW
  // landing, so the landing keeps its corner rails and caps (OPENS_SW_LANDING).
  const br = BREATHER_LAPS.has(lap + 1) && HAVEN.OPENS_SW_LANDING;
  if (odd) {
    // E flight rail + the NE landing's east rail, one cap
    if (lap === 0) {
      // v10.3 — THE BASE-FLOOR INVISIBLE BARRIER (playtest 2026-08-23: "the
      // invisible barrier is still there. Its under the stairs... on the base
      // floor"). The generic E cap starts at b+PARA_H = z56 — KNEE height —
      // and at lap 1 'b' is the ARENA FLOOR, so the cap stood as an invisible
      // 20-thin wall at x=416 across the whole east band, including under the
      // NE landing where nothing visible suggests a wall (the v9.34 fix made
      // the 288 anti-bypass SLAB visible, but this clip hovered on top of and
      // beyond it, y all the way to 436). At ground level the cap protects
      // nothing — hopping the first flight's rail lands you on the arena
      // floor. So at lap 1 the cap keeps only the spans that matter:
      //   * over the anti-bypass wall (y[-CORE,CORE]) from the WALL'S TOP
      //     (288) up — the wall itself already blocks below;
      //   * beside the NE landing (y[CORE,PX+PARA]) from the LANDING RAIL top
      //     (mid+PARA_H = 248) up — head-high off the base floor, so nothing
      //     at ground level can touch it.
      addBox('lap1 rail cap E over wall', PX, PX + PARA, -CORE, CORE, 288, b + FLIGHT_RISE + PARA_H + RAIL_CAP_H, MAT.clip);
      addBox('lap1 rail cap E landing', PX, PX + PARA, CORE, PX + PARA, railClipZ(mid), b + FLIGHT_RISE + PARA_H + RAIL_CAP_H, MAT.clip);
    } else {
      addBox(`lap${lap + 1} rail cap E`, PX, PX + PARA, -CORE, (br ? PX : PX + PARA), railClipZ(b), b + FLIGHT_RISE + PARA_H + RAIL_CAP_H, MAT.clip);
    }
    // N flight rail + (non-breather) the NE landing's north rail
    addBox(`lap${lap + 1} rail cap N`, -CORE, (br ? CORE : PX + PARA), PX, PX + PARA, railClipZ(mid), mid + FLIGHT_RISE + PARA_H + RAIL_CAP_H, MAT.clip);
    // NW landing corner rails (a different z tier — their own caps)
    addBox(`lap${lap + 1} rail cap NW a`, -PX - PARA, -PX, CORE, PX + PARA, railClipZ(end), end + PARA_H + RAIL_CAP_H, MAT.clip);
    addBox(`lap${lap + 1} rail cap NW b`, -PX, -CORE, PX, PX + PARA, railClipZ(end), end + PARA_H + RAIL_CAP_H, MAT.clip);
  } else {
    addBox(`lap${lap + 1} rail cap W`, -PX - PARA, -PX, (br ? -PX : -PX - PARA), CORE, railClipZ(b), b + FLIGHT_RISE + PARA_H + RAIL_CAP_H, MAT.clip);
    addBox(`lap${lap + 1} rail cap S`, (br ? -CORE : -PX - PARA), CORE, -PX - PARA, -PX, railClipZ(mid), mid + FLIGHT_RISE + PARA_H + RAIL_CAP_H, MAT.clip);
    addBox(`lap${lap + 1} rail cap SE a`, PX, PX + PARA, -PX - PARA, -CORE, railClipZ(end), end + PARA_H + RAIL_CAP_H, MAT.clip);
    addBox(`lap${lap + 1} rail cap SE b`, CORE, PX, -PX - PARA, -PX, railClipZ(end), end + PARA_H + RAIL_CAP_H, MAT.clip);
  }

  // (v13: the breather rail caps, the window guards and the ammo-crate
  // collision clip are all emitted by the BREATHER LOUNGE block above — the
  // room's window band carries clip_player, the spur rails carry MAT.clip
  // caps, and the crate clip derives from BR_FURN so it tracks the data file.)
}

// ---------------------------------------------------------------------------
// 5. THE CROWN (v9) — everything above the spiral. Odd frame; cbox mirrors.
// ---------------------------------------------------------------------------
// a rail run + its invisible cap, in one call (z = the floor the rail stands on)
// Main descent only: replace authored flights before later geometry/anchor audits.
if (DESCENT) BROKEN_TOWER.reshape(worldBrushes, allBoxes, navSeeds, addBox, stepMatOf, paraMatOf, RAIL_VIS_H);

// Original BO6 counter collision inside the four existing haven domes.
// These add no side rooms or changes to the descent's landing rails.
for (const n of WUNDERFIZZ_NODES) WUNDERFIZZ.geometry({
  collision: (label,vertices,faces,mat) => {
    const mins=[0,1,2].map(i=>Math.min(...vertices.map(p=>p[i]))), maxs=[0,1,2].map(i=>Math.max(...vertices.map(p=>p[i])));
    addBox(label,mins[0],maxs[0],mins[1],maxs[1],mins[2],maxs[2],mat);
    worldBrushes[worldBrushes.length-1].text=polyBrushText(label,vertices,faces,mat);
  },
},n);

function crail(label, x1, x2, y1, y2, z, mat, visibleHeight = RAIL_VIS_H) {
  cbox(label, x1, x2, y1, y2, z, z + visibleHeight, mat || MAT.roofPara);
  // A low curb gets an independent floor-to-top invisible wall. Its player
  // collision overlaps the small visible curb; the original 168u envelope stays.
  const clipBottom = visibleHeight < RAIL_H ? z : z + RAIL_H;
  cbox(`${label} cap`, x1, x2, y1, y2, clipBottom, z + RAIL_H + RAIL_CAP_H, MAT.clip);
}
// `cspike()` AND `SKY_MAT_PINK` LIVED HERE AND ARE DELETED (v11, 2026-08-25).
// cspike stacked tiers that could only get NARROWER, and every caller it ever
// had was a crown spire: the 4 corner towers (192->144->96->40), the 3 mid
// pilasters (128->96->56->24) and the 2 gate spires (32->20), all of them
// tipped in SKY_MAT_PINK. Measured from the base arena those tips were 0.10,
// 0.06 and 0.05 degrees — 3 px, 1.8 px and 1.5 px — so none of them was ever
// visible from anywhere in the map, and the shape they made is the thing the
// user was describing when he said "it just looks like a castle with spikes".
// A form that narrows to a point is a SPIRE. The crown's replacement helper is
// `cfleuron()` in section 5f, whose whole reason for existing is that a tier
// may be WIDER than the one below it. If a narrowing stack is ever wanted
// again, write it there and say what it is for — do not resurrect this one.

// --- 5a. CROWN STAIR: the last flight, gold, welded to the final landing ----
// In the odd frame this is an E flight from the SE landing (y=-CORE) up to
// the terrace (y=+CORE). With LAPS even the crown lap is odd and CM=+1, so it
// really is the east face; with LAPS odd it mirrors to the west face off the
// NW landing. Either way the first tread sits on the landing the spiral
// actually finished on — that is the whole fix for "the last platform isn't
// connected to the stairs".
for (let i = 1; i <= STEPS; i++) {
  const [z1, z2] = slabZ(TOP + RISE * i);
  cbox(`crown step ${i}`, CORE, PX, -CORE + TREAD * (i - 1), -CORE + TREAD * i, z1, z2, MAT.crownStep);
}
if (STAIR_RAMP_CLIP) {
  // The crown stair's ramp, mirrored by hand because the wedge emitters do not
  // go through cbox (they are not AABBs). CM point-mirror maps the odd-frame E
  // form onto the W form — the same mapping the spiral's own even laps use.
  // (Does not register in crownBB — it sits inside the crown stair's envelope.)
  if (CM === 1) rampWedgeY('crown stair ramp', CORE, PX, -CORE - TREAD, CORE - TREAD, TOP, TOP + FLIGHT_RISE, MAT.rampClip);
  else rampWedgeY('crown stair ramp', -PX, -CORE, -CORE + TREAD, CORE + TREAD, TOP + FLIGHT_RISE, TOP, MAT.rampClip);
}
for (let j = 1; j <= STEPS / PARA_EVERY; j++) {
  const top = TOP + RISE * PARA_EVERY * j;
  cbox(`crown stair rail ${j}`, PX, PX + PARA, -CORE + TREAD * PARA_EVERY * (j - 1), -CORE + TREAD * PARA_EVERY * j, top - RISE * (PARA_EVERY - 1), top + RAIL_VIS_H, MAT.roofPara); // ankle gap: see E para
}
cbox('crown stair rail cap', PX, PX + PARA, -CORE, CORE, railClipZ(TOP), TOP2 + RAIL_H + RAIL_CAP_H, MAT.clip);

// --- 5a2. THE TOWER SHELL (v13.5, user 2026-08-28: "Im considering add walls
// to the toer so you cant see outside except for the side that can see the
// crown" / "Except for the side facing the crown. It gives visuals for
// players") ------------------------------------------------------------------
// Three walls enclose the spiral — EAST, SOUTH, WEST — and the NORTH stays
// fully open: the crown floats north of the tower, so the open side IS the
// crown view, revealed more with every lap climbed. What this changes: the
// climb becomes a shaft — Tron floors and door glow against dark walls, the
// Miami sky and the crown visible only through the north opening (and through
// each lounge's own windows, which poke out past the shell).
//
// GEOMETRY RULES, each load-bearing:
//  * Inner faces at +/-SHELL_IN = PX+PARA+24 — a 24u air gap outside the
//    parapets, so nothing is coplanar with a parapet face (z-fight rule) and
//    the lint's edge logic is untouched (walls stand in the void, never on
//    deck; boss/zombie navmesh never knew the void existed).
//  * STARTS at z = LAP_RISE (384): the base arena (half-extent 540) is WIDER
//    than the shell, so the shell begins above lap 1 and the arena keeps its
//    open-air street feel; from the arena you look UP into the shaft mouth.
//  * ENDS at z = TOP (19200): the roof deck, terrace, crown stair and
//    causeway stay open to the sky.
//  * BREATHER GAPS: the four lounges (all even laps -> all on the SW side)
//    span x[-800,-256] y[-992,-416] — they CROSS both the S and W shell
//    planes, so those two walls open for each breather's full z band
//    [mid-16, mid+400] (floor slab underside to just past the roof trim).
//    The lounges are their own walls there; the teleporter spurs stay
//    floating outside the shell, exactly the v13 exposure design. The E wall
//    has no breathers and runs unbroken.
//  * Corners: E and W own the S corners (their y spans run to -SHELL_OUT);
//    the S wall spans between their inner faces. Zero overlap, zero gap.
//  * MAT.ground (dark navy) on all faces — the decade-banding decoration
//    pass (docs/24 / Fifty Floors review) has a canvas now, not a decision.
const TOWER_SHELL = false;  // OFF (user 2026-08-29: "Remove the walls. They are
                            // ugly and you didnt vene implement them correctly.")
                            // The v13.5 shell lasted one build. Kept as a flag,
                            // not deleted: the geometry was lint/bake-proven, so
                            // if a future enclosed-shaft look is wanted, start
                            // here — but sell the LOOK to the user first with a
                            // preview render, which is the step this skipped.
if (TOWER_SHELL) {
  const SHELL_IN  = PX + PARA + 24;   // 460
  const SHELL_TH  = 32;
  const SHELL_OUT = SHELL_IN + SHELL_TH;   // 492
  const SHELL_Z0  = LAP_RISE;         // 384
  const SHELL_Z1  = TOP;              // 19200
  // Breather z bands (ascending), derived — never hand-copied.
  const shellGaps = [...BREATHER_LAPS].sort((a, b) => a - b)
    .map(lap => { const mid = (lap - 1) * LAP_RISE + FLIGHT_RISE; return [mid - 16, mid + 400]; });
  // EAST — one unbroken slab, S corner owned, stops at the N opening.
  addBox('tower shell E', SHELL_IN, SHELL_OUT, -SHELL_OUT, SHELL_IN, SHELL_Z0, SHELL_Z1, MAT.ground);
  // SOUTH + WEST — five segments each, gapped at the four breather bands.
  let zlo = SHELL_Z0;
  const bands = [...shellGaps, [SHELL_Z1, SHELL_Z1]];
  for (let i = 0; i < bands.length; i++) {
    const [glo, ghi] = bands[i];
    if (glo > zlo) {
      addBox(`tower shell S ${i + 1}`, -SHELL_IN, SHELL_IN, -SHELL_OUT, -SHELL_IN, zlo, glo, MAT.ground);
      addBox(`tower shell W ${i + 1}`, -SHELL_OUT, -SHELL_IN, -SHELL_OUT, SHELL_IN, zlo, glo, MAT.ground);
    }
    zlo = ghi;
  }
}

// --- 5b. TERRACE: the forecourt along the capital's arrival face -----------
// Glow-edge tiles; the stair's last tread (top = TOP2, y up to +CORE) meets its
// south edge flush. Its south side for x[-CORE,CORE] is the mast's base tier
// (solid), so the core top is never a walkable surface.
cbox('terrace', -TER_W, TER_W, TER_Y1, TER_Y2, TOP2 - SLAB, TOP2, MAT.crownRing);
cbox('terrace under-glow', -TER_W, TER_W, TER_Y1, TER_Y2, TOP2 - SLAB - 24, TOP2 - SLAB, MAT.crownFascia);
crail('terrace rail N west', -TER_W - PARA, -CW_HALF - PARA, TER_Y2, TER_Y2 + PARA, TOP2);
crail('terrace rail N east', CW_HALF + PARA, TER_W + PARA, TER_Y2, TER_Y2 + PARA, TOP2);
// The transit hall shares this edge. docs/196: its EAST WALL (x -500..-480, the
// rail line) now runs the whole edge and past both ends, door and all, so the two
// rail stubs either side of the doorway would stand inside that wall — they are
// emitted only if the hall ever stops covering the edge.
{
  const R = TRANSIT.ROOM, hallCovers = R.x2 === -TER_W - PARA && R.y1 < TER_Y1 - PARA && R.y2 > TER_Y2;
  if (!hallCovers) {
    crail('terrace rail W south', -TER_W - PARA, -TER_W, TER_Y1 - PARA, R.doorY1, TOP2);
    crail('terrace rail W north', -TER_W - PARA, -TER_W, R.doorY2, TER_Y2, TOP2);
  }
  if (R.doorY1 < TER_Y1 || R.doorY2 > TER_Y2) throw new Error('the transit hall door must open onto the terrace (TER_Y1..TER_Y2)');
}
TRANSIT.roof({box: transitCBox, poly: transitCPoly, bevel: transitCBevel}, TOP2);
crail('terrace rail E', TER_W, TER_W + PARA, TER_Y1 - PARA, TER_Y2, TOP2);
// south edge: west of the core (void below), and east of the stair rail (void below)
crail('terrace rail S west', -TER_W - PARA, -CORE, TER_Y1 - PARA, TER_Y1, TOP2);
crail('terrace rail S east', PX + PARA, TER_W + PARA, TER_Y1 - PARA, TER_Y1, TOP2);

// --- 5c. THE LAST MILE: the causeway ----------------------------------------
// v10.12 (user 2026-08-23: "Keep adding geometry, one thing to be carefull of
// are holes and miss placed walls").
//
// HOW THIS SECTION IS BUILT, AND WHY IT IS BUILT THAT WAY
// ------------------------------------------------------
// The v10.11 road hand-cut its own rails: each piece knew which of its own
// faces to guard, and each junction hand-computed the gaps where a branch
// opened off it (`face()` walking a sorted list of mouth x-centres). That works
// for a road made of parallel strips and starts producing slivers and holes the
// moment the road TURNS — which is exactly what the user then asked for. Every
// dogleg would be a new hand-reasoned rail case, and the failure mode is not a
// crash: it is a 20-unit gap over 19,000 units of open sky that nobody sees
// until a player walks through it. This map has already shipped that bug once,
// in the other direction (the lap-1 "rail cap E" starting at knee height ON the
// arena floor, reported three times as an invisible barrier before it was found).
//
// So the road is no longer drawn. It is DECLARED as a set of flat, grid-aligned
// DECK CELLS, and the rails are DERIVED from the union of those cells:
//
//   roadFlat()  / roadStair()   declare deck. They never emit a rail.
//   roadPortal()                declares "geometry I do not own continues here"
//                               (the terrace mouth, the citadel gate opening).
//   roadEmit()                  rasterises every cell onto a 20-unit grid and
//                               guards EVERY exposed edge it finds.
//
// Three properties then hold BY CONSTRUCTION rather than by inspection:
//
//   1. NO UNGUARDED EDGE. A rail goes on every grid column face whose neighbour
//      is not deck. There is no way to forget one, because nothing is written
//      by hand — a hole would have to be a hole in the cell list, and (3)
//      catches that.
//   2. NO MISPLACED WALL. ROAD_G === PARA === 20, so a rail occupies EXACTLY the
//      one unoccupied grid column outside the edge it guards. A rail can never
//      land on deck, because the column it sits in is by definition not deck.
//      This is the whole reason the grid is 20 and not 16 or 32; if you change
//      PARA you must change ROAD_G with it or that guarantee silently dies.
//   3. NO UNWALKABLE JOIN. Adjacent occupied columns are asserted to be within
//      ROAD_STEP_MAX of each other. A dogleg that misses its neighbour by a
//      cell, or a flight that lands 40 units proud of its landing, throws AT
//      GENERATION TIME instead of shipping.
//
// tools/lint_tod_geometry.js re-proves all three by parsing the FINISHED .map,
// independently of this code, so a bug in the builder above cannot hide behind
// the builder's own assertions.
//
// THE SHAPE, south to north (v12, user 2026-08-26: "the paths to get to the
// crown building are pretty simple and straight forward. Lets be more creative
// ... the run over to it should be scary and anxious driving"). The v10.12
// road was two MIRRORED doglegs and a plank — learn one fork and you knew the
// other, and mirrored shapes cannot be scary twice. Every lane is now a
// DIFFERENT KIND of fear, and the two forks teach opposite lessons:
//
//   A   GATE RUN     on-axis, flat. The GATE seals its mouth until EXTRACTION.
//   J1  FORK
//   W*  THE RIDGE   (west)  climbs +256 and ZIGZAGS along the crest — outer
//                           run, cut back in, inner run, descend. Longest walk,
//                           longest sightlines, and the best view of the crown
//                           on the whole road: height = vision = exposure.
//   E*  THE BROKEN STAIR (east)  steps DOWN into sunken pockets — drop, pocket,
//                           drop, a 640-long hollow at -256 you cannot see out
//                           of, then ONE long blind climb to the merge. The
//                           short straight lane, bought with blindness.
//   J2  MERGE
//   N   THE NARROWS  on-axis, flat — and the deck PINCHES to 120 for the middle
//                    stretch. Everybody crosses this, single file, under the
//                    second portal frame. The one guaranteed choke on the road.
//   J3  THREE-WAY FORK — three flavours of fear, pick one:
//   W*  THE UNDERCROFT (west)  plunges -384 (the deepest the road goes), a wide
//                           ambush CISTERN at the bottom, then a 960-unit blind
//                           ascent straight into the merge. Feels safe, is
//                           lonely — stairs draw no risers, so the pressure all
//                           waits in the basin. From the bottom the crown's
//                           whole underside hangs overhead.
//   P*  THE PLANK   (centre) 120 wide, dead straight, lifted +256 clear of
//                           everything — no cover at all, and it splits into
//                           four pieces so it is the riser-DENSEST lane per
//                           unit length. The exposed fast line.
//   E*  THE WEAVE   (east)  flat at deck height the whole way but SERPENTINES
//                           through four jogs — nine pieces, nine risers, the
//                           most infested ground on the road. Flat does not
//                           mean safe.
//   J4  MERGE
//   F   APPROACH     on-axis, flat, into the citadel gate.
//
// (An emergent bonus the boss code already provides: anchor_player keys the
// Panzer to the HIGHEST living player and protectors to the LOWEST — so the
// plank draws the Panzer plug and the undercroft draws the swarm. Recorded in
// docs/32 as the altitude-sorting oddity; here it is the design.)
//
// LOAD-BEARING: A and F are on-axis at TOP2 because they must meet the terrace
// mouth and the hall's gate opening (x +/-GATE_HALF). Every branch returns to
// TOP2 before a merge, so junctions are always flat. The span budget cwSpan is
// UNCHANGED from v10.12 — every fork/landing boundary keeps its y — so the
// 5f.1/5f.9 crown-vs-road asserts and the pinned CR_S_FACE stay valid without
// re-derivation. Verticality note: the undercroft's -384 slightly exceeds the
// +-256 envelope the finale's yaw-only "ahead" tests were tuned against
// (_tod_endless_rounds.gsc:172-178) — same mechanism, deeper trough; the
// fallback paths there degrade gracefully (spawn lands beside instead of
// ahead). Do not go deeper than 384 without re-reading that comment.

const ROAD_G        = 20;    // rasterisation grid. MUST equal PARA — see (2) above.
const ROAD_STEP_MAX = 18;    // BO3 walks up to this without a jump (stock stepSize)
const CW_TREAD      = 40;    // stair tread depth (multiple of ROAD_G)
const CW_RISE       = 16;    // stair rise per tread (<= ROAD_STEP_MAX)
const CW_HUMP       = 256;   // how far a raised/sunken branch leaves TOP2
const CW_PLANK_HUMP = 256;   // plank lift. v12: 192 -> 256 — with the second
                             // fork's west lane now DIVING CW_DEEP the plank
                             // reads taller by matching the ridge, and 256 is
                             // exactly the envelope the finale's yaw-only
                             // "ahead" spawn test was already tuned against.
const CW_DEEP       = 384;   // the undercroft's plunge — the deepest the road
                             // goes. 384 = 24 treads = 960 of run each way.
                             // HARD CEILING: see the verticality note in the
                             // shape comment above before deepening this.
const CW_LAT        = 400;   // branch centreline offset from the axis
const CW_SWING      = 720;   // outer-lane centreline: the ridge crest and the weave's far runs
// THE PLANK IS NARROW — 120, against 160 everywhere else.
//
// This went 120 -> 160 -> 120 in one session and the round trip is worth
// recording. The widening was caution: nothing in this map or map 1 has had a
// zombie path a walkway under 160, so 120 was an unproven width on the piece of
// road that is supposed to be the DANGEROUS one, and if the navmesh came out
// thin there and zombies avoided it, the exposed shortcut would quietly become
// the safe route.
//
// Review killed that reasoning: at 160 the plank is STRICTLY DOMINANT. It is
// the shortest line through the second fork by ~1200 units, it is no narrower
// than the alternatives, and being raised costs a player nothing on a bridge in
// open sky where there was never any cover to lose. A choice with no downside
// is not a choice. And the failure the widening was insuring against — zombies
// avoiding the plank — produces the SAME safe-shortcut outcome that 160
// guarantees outright. So 120 is weakly dominant: better if pathing works, no
// worse if it does not. 120 still fits three zombies abreast (~40-45 each).
// It is on the playtest list either way.
const CW_PLANK_HALF = 60;

// Narrowest walkable lane the road is allowed to declare, cross-axis. Nothing
// in this map or map 1 has ever had a zombie path along a walkway under 160
// (the spiral itself is PX-CORE = 160), so anything below that is unproven
// rather than wrong. 120 is set as the tripwire, not as a physical limit: a
// zombie is ~40-45 units wide, so 60 would be the true floor. If a future
// design genuinely wants a narrower catwalk, RAISE this deliberately and
// accept that zombie pathing on it is untested — the failure mode is that they
// avoid it, which silently turns whatever you built as the dangerous route
// into the safe one.
const CW_MIN_LANE   = 120;

// How wide the road opens out to where it meets the citadel gate. The gate
// opening is GATE_HALF*2 = 256 and the road is 160, and the difference used to
// be open hall floor guarded by nothing — walk in a little wide and you drop
// 19,000 units. Asserted rather than commented: both of these were prose in the
// first cut and the second one was violated within the hour.
const CW_FLARE      = 120;
if (CW_FLARE > GATE_HALF) throw new Error(`CW_FLARE ${CW_FLARE} would foul the gate posts at ${GATE_HALF}`);
if (CW_FLARE % ROAD_G)    throw new Error(`CW_FLARE ${CW_FLARE} is not a multiple of ROAD_G ${ROAD_G}`);
if (CW_FLARE < CW_HALF)   throw new Error(`CW_FLARE ${CW_FLARE} is narrower than the road it flares from`);

if (ROAD_G !== PARA) throw new Error('ROAD_G must equal PARA or derived rails can land on deck');
if (CW_RISE > ROAD_STEP_MAX) throw new Error('CW_RISE exceeds the walkable step');

// ---- the deck-cell model ---------------------------------------------------
// A CELL is a flat, grid-aligned rectangle of deck at one height. Stairs are
// just many cells. Nothing here is ever a slope: a ramp cannot be rasterised
// onto a grid without picking a height per column anyway, and pretending
// otherwise is how the ankle-gap under a stepped parapet got shipped in v10.11.
const roadCells = [];    // { tag, x1, x2, y1, y2, z, deck }
// Road cells whose exposed edges get a FULL-HEIGHT WALL (HW_H clear + a roof)
// instead of a chest-high rail, plus a roof over the footprint and posts in the
// outside corners (the enclosed hallway, 2026-09-25). Filled by tag before
// roadEmit(); roadEmit reads it.
const ROAD_WALLED = new Set();
// Set by roadEmit(). Rails are DERIVED from the finished occupancy map, so a
// cell declared after the derivation would get no rails at all and could be
// overlapped by one — the silent version of exactly the defect this design
// exists to prevent.
let roadSealed = false;
const roadPieces = [];   // { tag, cx, cy, cz, kind } — one per NAMED piece, for risers/lights

function roadAssertGrid(tag, ...vals) {
  for (const v of vals)
    if (v % ROAD_G !== 0)
      throw new Error(`road "${tag}": ${v} is not a multiple of ROAD_G (${ROAD_G})`);
}

// deck:false = "something else owns the floor here, but it IS floor" — used for
// the terrace mouth and the citadel gate opening so the rail pass does not wall
// the road off from the two things it has to connect to.
function roadCell(tag, x1, x2, y1, y2, z, deck) {
  if (roadSealed) throw new Error(`road "${tag}": declared AFTER roadEmit() — it would get no rails`);
  roadAssertGrid(tag, x1, x2, y1, y2);
  if (x1 >= x2 || y1 >= y2) throw new Error(`road "${tag}": degenerate footprint`);
  roadCells.push({ tag, x1, x2, y1, y2, z, deck });
}

function roadPiece(tag, kind, cx, cy, cz) { roadPieces.push({ tag, kind, cx, cy, cz }); }

// A flat piece: one cell, one deck brush, one under-glow.
function roadFlat(tag, x1, x2, y1, y2, z) {
  if (Math.min(x2 - x1, y2 - y1) < CW_MIN_LANE)
    throw new Error(`road "${tag}": ${Math.min(x2 - x1, y2 - y1)}u lane is under CW_MIN_LANE ${CW_MIN_LANE}`);
  roadCell(tag, x1, x2, y1, y2, z, true);
  cbox(tag, x1, x2, y1, y2, z - SLAB, z, MAT.crownRing);
  cbox(`${tag} under-glow`, x1, x2, y1, y2, z - SLAB - 24, z - SLAB, MAT.crownFascia);
  roadPiece(tag, 'flat', (x1 + x2) / 2, (y1 + y2) / 2, z);
}

// A stepped piece along +y: one cell and one brush PER TREAD, so the rail pass
// guards every tread at its own height and no tread can end up with a parapet
// floating above its ankles.
function roadStair(tag, x1, x2, yA, yB, zA, zB) {
  // cross-axis only: a tread is deliberately shallow along the direction of travel
  if (x2 - x1 < CW_MIN_LANE)
    throw new Error(`road "${tag}": ${x2 - x1}u lane is under CW_MIN_LANE ${CW_MIN_LANE}`);
  const n = Math.round(Math.abs(zB - zA) / CW_RISE);
  if (n < 1) throw new Error(`road "${tag}": not a stair`);
  if (Math.abs(zB - zA) !== n * CW_RISE)
    throw new Error(`road "${tag}": rise ${zB - zA} is not a whole number of ${CW_RISE}u treads`);
  if (yB - yA !== n * CW_TREAD)
    throw new Error(`road "${tag}": ${n} treads need ${n * CW_TREAD}u of run, got ${yB - yA}`);
  const dz = (zB - zA) / n;
  for (let i = 0; i < n; i++) {
    const y0 = yA + CW_TREAD * i, y1 = y0 + CW_TREAD;
    const zt = zA + dz * (i + 1);   // the tread you step ONTO
    roadCell(`${tag} ${i + 1}`, x1, x2, y0, y1, zt, true);
    cbox(`${tag} step ${i + 1}`, x1, x2, y0, y1, zt - SLAB, zt, MAT.crownRing);
    cbox(`${tag} step ${i + 1} under-glow`, x1, x2, y0, y1, zt - SLAB - 24, zt - SLAB, MAT.crownFascia);
  }
  // STAIR RAMP CLIP (2026-08-27, docs/39) — the road's stairs get the same
  // invisible MAT.rampClip wedge as the tower's flights, emitted here so every
  // current AND future roadStair is ramped by construction. The nosing plane:
  //   * FALLING along +y: (yA,zA)->(yB,zB) touches every tread's downhill edge
  //     and welds flush at both ends — no feather needed.
  //   * RISING along +y: the same line shifted one tread back,
  //     (yA-CW_TREAD, zA)->(yB-CW_TREAD, zB) — it passes through every riser
  //     top, feathers 0->CW_RISE over the last CW_TREAD of the approach flat
  //     (every rising stair's approach is a wider flat at zA, checked per call
  //     site 2026-08-27: J1 fork / hollow 2 / cistern / J3 fork), and leaves
  //     the last tread's own top to carry the deck to yB.
  // The wedge is not a cell: rails, risers, reachability and every roadEmit
  // assert see exactly the geometry they saw before. Underside = plane - RAMP_T,
  // which stays inside the tread slabs (RISE == SLAB == 16 exactly here).
  if (STAIR_RAMP_CLIP) {
    if (zB < zA) rampWedgeY(`${tag} ramp`, x1, x2, yA, yB, zA, zB, MAT.rampClip, CW_RISE, CW_TREAD);
    else rampWedgeY(`${tag} ramp`, x1, x2, yA - CW_TREAD, yB - CW_TREAD, zA, zB, MAT.rampClip, CW_RISE, CW_TREAD);
  }
  roadPiece(tag, 'stair', (x1 + x2) / 2, (yA + yB) / 2, (zA + zB) / 2);
}

// "The floor continues here and I do not own it." Emits nothing.
function roadPortal(tag, x1, x2, y1, y2, z) { roadCell(tag, x1, x2, y1, y2, z, false); }

// ---- the rail pass ---------------------------------------------------------
// Rasterise, check every adjacency, guard every exposed face. This is the only
// code in the section that emits a rail.
function roadEmit() {
  roadSealed = true;
  const key = (gx, gy) => `${gx},${gy}`;
  const occ = new Map();

  for (const c of roadCells) {
    for (let x = c.x1; x < c.x2; x += ROAD_G) {
      for (let y = c.y1; y < c.y2; y += ROAD_G) {
        const k = key(x, y);
        const prev = occ.get(k);
        // OVERLAP IS ALWAYS A BUG HERE. This road never crosses over itself, so
        // two cells claiming one column means a copy-paste or an arithmetic
        // slip — and the rail pass would silently guard the wrong height.
        if (prev)
          throw new Error(`road overlap at (${x},${y}): "${prev.tag}" and "${c.tag}"`);
        occ.set(k, { z: c.z, tag: c.tag, deck: c.deck });
      }
    }
  }

  // Every 4-neighbour pair must be walkable. A dogleg that misses its partner by
  // one cell shows up here as an unguarded edge instead (correct, if ugly); a
  // flight that lands proud of its landing shows up as this throw.
  const DIRS = [[-ROAD_G, 0, 'W'], [ROAD_G, 0, 'E'], [0, -ROAD_G, 'S'], [0, ROAD_G, 'N']];
  const edges = [];   // { dir, gx, gy, z }
  for (const [k, cell] of occ) {
    const [gx, gy] = k.split(',').map(Number);
    for (const [dx, dy, dir] of DIRS) {
      const n = occ.get(key(gx + dx, gy + dy));
      if (!n) { if (cell.deck) edges.push({ dir, gx, gy, z: cell.z }); continue; }
      if (Math.abs(n.z - cell.z) > ROAD_STEP_MAX)
        throw new Error(
          `road step ${Math.abs(n.z - cell.z)}u > ${ROAD_STEP_MAX}u between "${cell.tag}" and "${n.tag}" at (${gx},${gy})`);
    }
  }

  // REACHABILITY, proven on the cell list before a single brush is written.
  // Flood from the terrace mouth; the citadel mouth must be in the flood, and
  // nothing may be outside it.
  const start = roadCells.find(c => c.tag === 'causeway terrace mouth');
  const goal = roadCells.find(c => c.tag === 'causeway citadel mouth');
  if (!start || !goal) throw new Error('road: both mouths must be declared');
  // BREADTH-first, so the distance it records is the SHORTEST walk. That number
  // matters: the finale clock is the length of one song (TOD_FINALE_SONG_SECS,
  // 191s) and the road is what the clock is for. If the quickest line through
  // here ever stops being comfortably runnable inside the song while fighting,
  // the ending becomes unwinnable and nothing else in the map will say so.
  const flood = (sx, sy) => {
    const seen = new Map([[key(sx, sy), 0]]);
    let frontier = [[sx, sy]];
    let depth = 0;
    while (frontier.length) {
      const next = [];
      depth++;
      for (const [gx, gy] of frontier) {
        const here = occ.get(key(gx, gy));
        for (const [dx, dy] of DIRS) {
          const nk = key(gx + dx, gy + dy);
          if (seen.has(nk)) continue;
          const n = occ.get(nk);
          if (!n || Math.abs(n.z - here.z) > ROAD_STEP_MAX) continue;
          seen.set(nk, depth);
          next.push([gx + dx, gy + dy]);
        }
      }
      frontier = next;
    }
    return seen;
  };
  const seen = flood(start.x1, start.y1);
  let goalDepth;
  if (!CW_CUT) {
    goalDepth = seen.get(key(goal.x1, goal.y1));
    if (goalDepth === undefined)
      throw new Error('road: the citadel mouth is NOT reachable from the terrace mouth');
    if (seen.size !== occ.size) {
      const orphan = [...occ].find(([k]) => !seen.has(k));
      throw new Error(`road: ${occ.size - seen.size} column(s) unreachable, first in "${orphan[1].tag}"`);
    }
  } else {
    // docs/163 THE CUT. Two islands, each proven whole from its own mouth, and
    // proven APART — a future edit that re-bridges the gap must flip CW_CUT,
    // not leave a jump pad beside a walkable road. The route the Fall needs is
    // one way: citadel mouth -> the pad (walk) -> the landing (the jump) ->
    // the terrace mouth (walk). Both walks are asserted here; the jump itself
    // is modelled by lint_tod_geometry from the two jump-pad structs.
    const seenC = flood(goal.x1, goal.y1);
    const pad = key(JP_PAD[0], JP_PAD[1]), land = key(JP_LAND[0], JP_LAND[1]);
    if (!seenC.has(pad)) throw new Error('road: the jump pad is NOT walkable from the citadel mouth');
    if (!seen.has(land)) throw new Error('road: the jump pad landing is NOT walkable from the terrace mouth');
    for (const k of seen.keys())
      if (seenC.has(k)) throw new Error(`road: the cut is not a cut — (${k}) is walkable from both mouths`);
    const orphan = [...occ].find(([k]) => !seen.has(k) && !seenC.has(k));
    if (orphan) throw new Error(`road: column (${orphan[0]}) in "${orphan[1].tag}" is walkable from neither mouth`);
    goalDepth = seenC.get(pad) + seen.get(land);   // walked length either side of the jump
  }

  // Merge each exposed face into the longest runs of equal height, then guard
  // them. Merging is cosmetic (fewer, cleaner brushes); the guarantee comes from
  // the edge list, not from the merge.
  const groups = new Map();
  for (const e of edges) {
    // W/E faces run along y; N/S faces run along x.
    const along = (e.dir === 'W' || e.dir === 'E') ? e.gy : e.gx;
    const fixed = (e.dir === 'W' || e.dir === 'E') ? e.gx : e.gy;
    const tag = occ.get(key(e.gx, e.gy)).tag;
    const walled = ROAD_WALLED.has(tag);   // a hallway wall, not a rail
    const visibleHeight = tag === 'causeway launch deck' ? JP_BALCONY_CURB_H : RAIL_VIS_H;
    const gk = `${e.dir}|${fixed}|${e.z}|${walled}|${visibleHeight}`;
    if (!groups.has(gk)) groups.set(gk, { dir: e.dir, fixed, z: e.z, walled, visibleHeight, along: [] });
    groups.get(gk).along.push(along);
  }
  // PORTAL COVERAGE. A portal says "other geometry owns the floor here"; if the
  // rail pass wants to guard an edge that points INTO a portal's band, the
  // portal is too narrow for the road that meets it, and the rail is about to
  // be planted on somebody else's floor. That is not a hole and not an
  // invisible wall, so nothing downstream catches it — it has to throw here.
  const portals = roadCells.filter(c => !c.deck);
  for (const e of edges) {
    const [nx, ny] = { W: [e.gx - ROAD_G, e.gy], E: [e.gx + ROAD_G, e.gy],
                       S: [e.gx, e.gy - ROAD_G], N: [e.gx, e.gy + ROAD_G] }[e.dir];
    const lateral = (e.dir === "W" || e.dir === "E");
    for (const q of portals) {
      // Compare the rail against the portal ACROSS THE PORTAL'S THIN AXIS only.
      // A portal is a one-cell-deep strip: a mouth wide in x is thin in y, and
      // only a north/south rail can land in its row. Testing the wide axis too
      // fires on every side rail the road has, anywhere along its length, purely
      // because their x happens to fall inside the mouth's width.
      const thinInY = (q.x2 - q.x1) > (q.y2 - q.y1);
      if (thinInY === lateral) continue;   // this edge cannot reach that band
      const inBand = thinInY ? (ny >= q.y1 && ny < q.y2) : (nx >= q.x1 && nx < q.x2);
      if (!inBand) continue;
      throw new Error(
        `road: a rail would stand inside portal "${q.tag}" at (${nx},${ny}) — the portal is ` +
        `narrower than the road face that meets it, so this rail lands on geometry the road does not own`);
    }
  }

  // WALLED CELLS (the enclosed hallway): their exposed edges get a wall in the
  // same neighbour column a rail would take, from under the deck to the roof's
  // top, so the room is sealed; every column a wall takes is also withheld from
  // any RAIL run that would land on it (an open deck's rail meeting a hallway
  // wall at a shared corner column would otherwise stand inside the wall and
  // z-fight on its faces).
  const isWalled = (tag) => ROAD_WALLED.has(tag);
  const wallCols = new Set();
  const colOf = (e) => ({ W: [e.gx - ROAD_G, e.gy], E: [e.gx + ROAD_G, e.gy], S: [e.gx, e.gy - ROAD_G], N: [e.gx, e.gy + ROAD_G] }[e.dir]);
  for (const e of edges) if (isWalled(occ.get(key(e.gx, e.gy)).tag)) wallCols.add(key(...colOf(e)));
  const WALL_Z2 = (z) => z + HW_H + SLAB;

  let railN = 0, wallN = 0;
  for (const g of groups.values()) {
    g.along.sort((a, b) => a - b);
    let run = [g.along[0], g.along[0] + ROAD_G];
    const runs = [run];
    for (let i = 1; i < g.along.length; i++) {
      if (g.along[i] === run[1]) run[1] += ROAD_G;
      else { run = [g.along[i], g.along[i] + ROAD_G]; runs.push(run); }
    }
    // The guard sits in the neighbour column, which the edge list has already
    // established is not deck.
    const o = { W: [g.fixed - ROAD_G, g.fixed], E: [g.fixed + ROAD_G, g.fixed + 2 * ROAD_G],
                S: [g.fixed - ROAD_G, g.fixed], N: [g.fixed + ROAD_G, g.fixed + 2 * ROAD_G] }[g.dir];
    const lateral = (g.dir === 'W' || g.dir === 'E');
    for (const [a1, a2] of runs) {
      if (g.walled) {
        wallN++;
        const lbl = `causeway hallway wall ${g.dir}${wallN}`;
        if (lateral) cbox(lbl, o[0], o[1], a1, a2, g.z - SLAB, WALL_Z2(g.z), MAT.hallWall);
        else         cbox(lbl, a1, a2, o[0], o[1], g.z - SLAB, WALL_Z2(g.z), MAT.hallWall);
        continue;
      }
      // a rail run, split around any column a hallway wall already owns
      const pieces = [];
      let cur = null;
      for (let q = a1; q < a2; q += ROAD_G) {
        const colKey = lateral ? key(o[0], q) : key(q, o[0]);
        if (wallCols.has(colKey)) { cur = null; continue; }
        if (!cur) { cur = [q, q + ROAD_G]; pieces.push(cur); } else cur[1] = q + ROAD_G;
      }
      for (const [p1, p2] of pieces) {
        railN++;
        const lbl = `causeway rail ${g.dir}${railN}`;
        if (lateral) crail(lbl, o[0], o[1], p1, p2, g.z, undefined, g.visibleHeight);
        else         crail(lbl, p1, p2, o[0], o[1], g.z, undefined, g.visibleHeight);
      }
    }
  }
  // ROOFS + CORNER POSTS for the walled cells. A roof covers exactly its cell
  // (cells never overlap, so roofs tile); a wall run stops at its cell's edge,
  // so every OUTSIDE corner leaves one empty column between two wall runs —
  // a post fills it. A column is a post if it is not deck, not already a wall,
  // has a wall column on one horizontal AND one vertical side, and touches a
  // walled deck column diagonally.
  let roofN = 0, postN = 0;
  for (const c of roadCells.filter(c => c.deck && isWalled(c.tag))) {
    roofN++;
    cbox(`causeway hallway roof ${roofN}`, c.x1, c.x2, c.y1, c.y2, c.z + HW_H, WALL_Z2(c.z), MAT.hallWall);
    cbox(`causeway hallway roof clip ${roofN}`, c.x1, c.x2, c.y1, c.y2, WALL_Z2(c.z), BARRIER_TOP, MAT.clip);   // THE INVISIBLE BARRIER (2026-09-26): nobody lands on a hallway roof
  }
  const postDone = new Set();
  for (const [k, cell] of occ) {
    if (!cell.deck || !isWalled(cell.tag)) continue;
    const [gx, gy] = k.split(',').map(Number);
    for (const [dx, dy] of [[-1, -1], [-1, 1], [1, -1], [1, 1]]) {
      const cx = gx + dx * ROAD_G, cy = gy + dy * ROAD_G, ck = key(cx, cy);
      if (occ.has(ck) || wallCols.has(ck) || postDone.has(ck)) continue;
      const h = wallCols.has(key(cx - ROAD_G, cy)) || wallCols.has(key(cx + ROAD_G, cy));
      const v = wallCols.has(key(cx, cy - ROAD_G)) || wallCols.has(key(cx, cy + ROAD_G));
      if (!h || !v) continue;
      postDone.add(ck);
      postN++;
      cbox(`causeway hallway post ${postN}`, cx, cx + ROAD_G, cy, cy + ROAD_G, cell.z - SLAB, WALL_Z2(cell.z), MAT.hallWall);
    }
  }
  return { columns: occ.size, edges: edges.length, rails: railN, walls: wallN, roofs: roofN, posts: postN, walk: goalDepth * ROAD_G };
}

// ---- the layout ------------------------------------------------------------
// y-budget, south to north. These must sum to CW_LEN or run F misses the hall.
//   A 640 | J1 160 | branches 2240 | J2 160 | C 640 | J3 160 | branches 2240
//   | J4 160 | F 960   =  7360
const ZB      = TOP2;
const CW_LAND = 480;                       // junction landings span x +/-CW_LAND
const cwSpan  = [640, 160, 2240, 160, 640, 160, 2240, 160, 960];
const cwY     = [TER_Y2];
cwSpan.forEach(L => cwY.push(cwY[cwY.length - 1] + L));
if (cwY[cwY.length - 1] - TER_Y2 !== CW_LEN)
  throw new Error(`causeway spans sum to ${cwY[cwY.length - 1] - TER_Y2}, CW_LEN is ${CW_LEN}`);

// THE CUT (docs/163, CW_CUT) — what survives of the road. Odd frame, y south
// -> north; every value a multiple of ROAD_G (roadAssertGrid enforces it).
//   terrace side:  A gate-run  TER_Y2 .. JP_LAND_Y1   (the road's old first
//                  240 units, on-axis, 160 wide — the terrace mouth + portal 1)
//                  LANDING    JP_LAND_Y1 .. JP_LAND_Y2  (480 x 480, where the
//                  pad sets the party down)
//   ---- the gap: 5200 units of sky, 81% of the visible span (TER_Y2 .. the
//        crown's south face CR_S_FACE), nothing in it ----
//   crown side:    LAUNCH     JP_LAUNCH_Y1 .. cwY[8]  (480 x 480, the pad at
//                  its centre)
//                  F approach + flare cwY[8] .. cwY[9]  UNCHANGED — it is the
//                  tunnel through the crown's band (5f.1 pins the band's south
//                  face inside it) and the courtyard to the hall gate.
// The crown does not move: HS is still TER_Y2 + CW_LEN. Only deck is removed.
const JP_DECK_HALF = 240;                   // the LANDING deck: 480 wide
const JP_LAND_Y1   = TER_Y2 + 240;          // 720
const JP_LAND_Y2   = JP_LAND_Y1 + 480;      // 1200
const JP_LAUNCH_Y2 = cwY[8] - HALLWAY_PUSH; // 5720 — pushed south of the enclosed hallway (was cwY[8] = 6880)
if (BALCONY_N !== JP_LAUNCH_Y2) throw new Error(`BALCONY_N ${BALCONY_N} != JP_LAUNCH_Y2 ${JP_LAUNCH_Y2} (the Quick Revive pin)`);
// THE BALCONY (user 2026-09-25: "it needs to be relatively big ... it has to
// fit the shop, the jump pad, Quick Revive"). The launch deck is 1280 x 640
// now: x +-JP_LAUNCH_HALF, y JP_LAUNCH_Y1..JP_LAUNCH_Y2. Its width is bounded
// by the crown's frontispiece piers (x +-800..944, y 6848+, down to deck
// height): 5f.9 below proves no crown brush stands on it. The pad sits 240 in
// from the south rail (the arc sweep in test_jumppad clears the rail cap by
// ~200 there); the display shop takes the west half, Quick Revive the north
// rail west of the approach, and the east rail opens into THE OVERLOOK.
const JP_LAUNCH_HALF = 640;
const JP_BALCONY_CURB_H = 12;             // ankle-height view edge; original 168u collision envelope retained
const JP_LAUNCH_Y1 = JP_LAUNCH_Y2 - 640;    // 6240
// The pad and the landing, deck centres. The pad trigger radius and the four
// landing spots ride out to _tod_crown_data.gsc (section 7) from these.
const JP_PAD       = [0, JP_LAUNCH_Y1 + 240];                  // (0, 6480)
// THE ENCLOSED HALLWAY (user 2026-09-25 ~22:10): "players will start at the
// crown. Then they'll open up the gate. That gate will [lead to] an enclosed
// hallway. So you can't see out of it ... left, right, middle. The middle leads
// to the bridge where you'll be outside ... left it leads to power and the right
// will lead to the teleporter ... left will cost money, right will cost money,
// middle will just be a locked door until power is on ... push out everything
// that was outside out farther away from the crown". On three questions: the
// right room holds a NEW teleporter, a prop with no destination yet; the power
// room is enclosed too (it replaced THE OVERLOOK, which looked down the tower);
// both side doors cost 1500.
//
// Walking out of the gate (south, -y) the party's LEFT is +x (east).
//   the F approach + flare (the throat through the crown, unchanged cells) and
//   HW_JUNC, the junction room, are WALLED and ROOFED (ROAD_WALLED);
//   LEFT  (east):  HW_EAST corridor behind door tod_crown_power (1500) -> HW_POWER, the lever;
//   RIGHT (west):  HW_WEST corridor behind door tod_crown_tele  (1500) -> HW_TELE, the teleporter prop;
//   MIDDLE (south): HW_SOUTH corridor behind tod_crown_bridge_door, shut until
//                  the power (_tod_fall::power_switch_on opens it) -> THE BALCONY.
// All are road cells (roadFlat), so the rail pass, the reachability flood and
// the geometry lint cover them; a WALLED cell gets a full-height wall where a
// rail would stand, a roof over its footprint and corner posts (roadEmit).
// Everything stays under the crown's south-face rib 3 (foot at y 6688 for
// x 1144..1560, and its mirror) and inside the sealed island (section 7).
const HW_H     = 256;   // clear height inside the hallway = the gate's GATE_H (the lintel above it is solid)
const HW_JUNC  = { x1: -320, x2: 320, y1: 6240, y2: cwY[8] };                  // 640 x 640, meets the F approach at cwY[8]
const HW_EAST  = { x1: HW_JUNC.x2, x2: 800, y1: 6480, y2: 6640 };                // 480 x 160, the door at its west end
const HW_POWER = { x1: HW_EAST.x2, x2: 1280, y1: 6180, y2: 6660 };               // 480 x 480
const HW_WEST  = { x1: -HW_EAST.x2, x2: -HW_EAST.x1, y1: HW_EAST.y1, y2: HW_EAST.y2 };
const HW_TELE  = { x1: -HW_POWER.x2, x2: -HW_POWER.x1, y1: HW_POWER.y1, y2: HW_POWER.y2 };
const HW_SOUTH = { x1: -CW_HALF, x2: CW_HALF, y1: JP_LAUNCH_Y2, y2: HW_JUNC.y1 }; // 160 x 520, the bridge door at its north end
// the lever: against the power room's EAST wall, front to the room (yaw 270 =
// the prefab's front, its -y side at yaw 0, turned to face -x)
const HW_LEVER = [HW_POWER.x2 - 30, (HW_POWER.y1 + HW_POWER.y2) / 2];
// the teleporter prop: the room's centre, facing the door (east)
const HW_TELE_ORG = [(HW_TELE.x1 + HW_TELE.x2) / 2, (HW_TELE.y1 + HW_TELE.y2) / 2];
const TRANSIT_ROUTES = TRANSIT.routes({top:TOP2,mirror:CM,spurX:SPUR_CX,spurY:SPUR_PAD_Y,crown:HW_TELE_ORG});
const HW_ROOMS = { HW_JUNC, HW_EAST, HW_POWER, HW_WEST, HW_TELE, HW_SOUTH };
for (const [n, c] of Object.entries(HW_ROOMS))
  for (const v of [c.x1, c.x2, c.y1, c.y2]) if (v % ROAD_G) throw new Error(`${n} is off the ${ROAD_G} grid: ${v}`);
if (HW_POWER.y2 + ROAD_G > 6688) throw new Error("the power room (or its north wall) reaches the crown's south-face rib 3 (y 6688)");
if (HW_JUNC.y2 !== cwY[8]) throw new Error('the junction must meet the F approach at cwY[8]');
// THE GRID TERMINAL (docs/208, map 1's v19.68q + v19.68u ported): THE POWER SWITCH is Nikolai's
// Grid Terminal V5 (`tod_power_terminal`: GRID CONTROL / RESTART SEQUENCE REQUIRED, the HOLD
// button), hung on the power room's EAST wall where the stock lever stood (HW_LEVER), facing the
// room (yaw 180: the model's front is its +X). MEASURED (map 1 art/fan_props/manifest.json "power"):
// x 0..10.86 off the wall, y +-30.12, z 0..88. _tod_fall spawns it through _tod_power_terminal and
// plays the dial + screen boot on the press. Its BODY CLIP runs floor to roof (the room is roofed):
// no ledge on an 88-tall top, nothing to stand on behind the screen. The trigger stands
// POWER_TERM_TRIG_OUT in front of its face, lifted, inside the room and outside the clip (a clip
// over a use-trigger's origin kills its sight trace - the dead-trigger trap).
const POWER_TERM_DEPTH = 10.86, POWER_TERM_HALF = 30.12, POWER_TERM_H = 88;
const POWER_TERM = { org: [HW_POWER.x2 - 0.5, (HW_POWER.y1 + HW_POWER.y2) / 2], yaw: 180 };
const POWER_TERM_TRIG_OUT = 24, POWER_TERM_TRIG_R = 48, POWER_TERM_TRIG_LIFT = 24, POWER_TERM_TRIG_H = 72;
{
  const [px, py] = POWER_TERM.org, face = px - POWER_TERM_DEPTH;
  POWER_TERM.trig = [+(face - POWER_TERM_TRIG_OUT).toFixed(3), py];
  const cx1 = Math.floor(face - 1), cy1 = Math.floor(py - POWER_TERM_HALF - 1), cy2 = Math.ceil(py + POWER_TERM_HALF + 1);
  if (cy1 <= HW_POWER.y1 + 20 || cy2 >= HW_POWER.y2 - 20) throw new Error('the power terminal runs off its stretch of the east wall');
  if (POWER_TERM.trig[0] - POWER_TERM_TRIG_R <= HW_POWER.x1) throw new Error('the power terminal trigger leaves the power room');
  if (py - POWER_TERM_TRIG_R <= HW_POWER.y1 || py + POWER_TERM_TRIG_R >= HW_POWER.y2) throw new Error('the power terminal trigger reaches the power room side walls');
  if (POWER_TERM.trig[0] >= cx1) throw new Error('the power terminal trigger origin is inside its own clip');
  if (POWER_TERM_H > HW_H) throw new Error('the power terminal is taller than the power room');
  cbox('hallway power terminal body', cx1, HW_POWER.x2, cy1, cy2, TOP2, TOP2 + HW_H, MAT.clip);
}
// THE RAMPAGE INDUCER ON THE BALCONY (user 2026-09-25: "bring the rampage
// inducer ... the model and the glow everything ... place that on the bridge on
// that open area where the jump pad is and the item shop"). It stood in the base
// arena (base_inducer_org), which is the END of the run since the Fall. It
// mirrors the display shop across the pad: east half, same y. _tod_rampage
// reads crown_inducer_org/_trig_r (section 7) when the jump pad is live.
const CROWN_INDUCER = [440, JP_LAUNCH_Y1 + 320];
const CROWN_INDUCER_TRIG_R = 96;
const JP_LAND      = [0, (JP_LAND_Y1 + JP_LAND_Y2) / 2];       // (0, 960)
// THE DE JUMP PAD (2026-10-03, docs/163 s9; user: "I want it to have the jump pad model from der eisendrache. Can we
// switch it over with same functionality"). The pad wears Der Eisendrache's JUMPSPHERE now (tools/jumppad/
// install_de_jumppad.py): a broken-open half-sphere machine ~210 wide and 139 tall on a 215-wide lit deck, entered
// through a doorway on its local -x side and left through its broken-open local +x side. JP_PAD_YAW turns it so the
// doorway faces the bridge corridor (the authored +y, where the party walks in from HW_SOUTH) and the open side faces
// the flight (the authored -y, toward the terrace): DE's own arrangement (castle_flinger_01: the doorway faces away
// from the destination). The machine is a script_model with no collision of its own (CollisionMap ""), so the ring of
// clip below (JP_SHELL_*) is its collision, with a gap at the doorway.
const JP_PAD_YAW   = 270;                   // authored; the model's local -x doorway faces +y (asserted against HW_SOUTH below)
const JP_PAD_R     = 40;                    // trigger: origin within 40 of the pad centre = standing INSIDE the machine (72 on
                                            // the open teleporter deck until 2026-10-03; now a player who has walked through
                                            // the doorway launches, and nobody outside the shell can: asserted below)
const JP_SHELL_R1  = 52;                    // the clip ring's inner radius: just inside the machine's innermost posts (r 54-59,
                                            // measured on its LOD0 in the body layer z 12..64)
const JP_SHELL_R2  = 98;                    // its outer radius: the plinth's rim (the frame's footprint is +-97 x / -111..99 y;
                                            // the deck disc beyond it is 3 units tall and walkable)
const JP_SHELL_H   = 150;                   // over the dome (139): nobody stands on the machine
const JP_SHELL_DOOR_HALF = 27;              // deg either side of the doorway left open (the model's own doorway is +-20 deg:
                                            // the 7 deg margin each side keeps the gap wide enough for the navmesh to grow
                                            // through - lint_tod_navmesh proves the pad stays in the hall's component)
const JP_SHELL_SEG = 16;                    // deg per clip segment at most (a 16-deg chord sits 0.5 u inside the circle)
// ... except where the machine's side gadgets (the valve wheel, the gauges) stand out past the plinth: measured on its
// LOD0 between z 8 and 130, every direction reaches <= 99 but the model's local 215..285 deg (r 104-115, at knee to
// head height). Those wedges reach JP_SHELL_BULGE_R2, so a player walking round the machine never wades into them.
const JP_SHELL_BULGE = { from: 215, to: 285, r2: 118 };   // degrees in the MODEL's frame (they turn with JP_PAD_YAW)
const JP_LAND_YAW  = 90;                    // authored; the DE landing pad's local -x (its exit side) faces the terrace (-y)
// Four set-down spots ON the DE landing pad (it stands at the landing centre: a 145-wide disc whose middle 60 is its
// lowest, ~1-2 u). 2x2, 48 apart in x and 44 in y, so no two 32-wide capsules can land on one another (they were 160 x
// 120 on the bare deck). Every one is >= 165 from every landing-deck riser (the v10.22 materialize rule) — asserted below.
const JP_LAND_SPOTS = [[-24, -22], [24, -22], [-24, 22], [24, 22]].map(([dx, dy]) => [JP_LAND[0] + dx, JP_LAND[1] + dy]);
const JP_LAND_RISERS = [[-JP_DECK_HALF + 40, JP_LAND_Y2 - 40], [JP_DECK_HALF - 40, JP_LAND_Y2 - 40]];   // the two far corners
if (CW_CUT) {
  for (const [sx, sy] of JP_LAND_SPOTS)
    for (const [rx, ry] of JP_LAND_RISERS)
      if (Math.hypot(sx - rx, sy - ry) < 165)
        throw new Error(`jump pad landing spot (${sx},${sy}) is ${Math.hypot(sx - rx, sy - ry).toFixed(0)}u from riser (${rx},${ry}) — under the 165u materialize rule`);
  if (JP_LAND_Y2 >= JP_LAUNCH_Y1) throw new Error('jump pad: the landing deck reaches the launch deck — there is no gap to jump');
  if (CR_S_FACE <= JP_LAUNCH_Y2) throw new Error(`jump pad: the launch deck (to y ${JP_LAUNCH_Y2}) runs into the crown's south face ${CR_S_FACE}`);
  if (JP_PAD[1] - JP_PAD_R - 120 < JP_LAUNCH_Y1) throw new Error('jump pad: the pad is too close to the balcony\'s south rail for the arc sweep');
  // THE DE MACHINE: the trigger is the inside of the shell and nothing else. A 32-wide player stands at most
  // JP_SHELL_R1 - 16 from the centre inside the ring, so a trigger at least that big launches everyone who walks in (no
  // dead corner inside the machine), and a trigger smaller than the ring is out of reach from outside it.
  if (JP_PAD_R < JP_SHELL_R1 - 16) throw new Error(`jump pad: a player can stand ${JP_SHELL_R1 - 16} in from the shell, outside the ${JP_PAD_R} trigger: a dead spot inside the machine`);
  if (JP_PAD_R >= JP_SHELL_R1) throw new Error('jump pad: the trigger reaches the shell ring, so a player outside the machine could launch through its wall');
  // the doorway (the model's local -x, at JP_PAD_YAW + 180) must face the bridge corridor the party walks in from
  const doorAt = (JP_PAD_YAW + 180) % 360, toHall = Math.atan2(JP_LAUNCH_Y2 - JP_PAD[1], 0 - JP_PAD[0]) * 180 / Math.PI;
  if (Math.abs(((doorAt - toHall) % 360 + 540) % 360 - 180) > 1)
    throw new Error(`jump pad: the machine's doorway faces ${doorAt} deg but the bridge corridor is at ${toHall.toFixed(1)} deg`);
  // every landing spot on the landing pad's low middle (<= 36 from its centre), no two closer than a player
  for (const [sx, sy] of JP_LAND_SPOTS)
    if (Math.hypot(sx - JP_LAND[0], sy - JP_LAND[1]) > 36) throw new Error(`jump pad landing spot (${sx},${sy}) is off the landing pad's middle`);
  for (let i = 0; i < JP_LAND_SPOTS.length; i++)
    for (let j = i + 1; j < JP_LAND_SPOTS.length; j++)
      if (Math.hypot(JP_LAND_SPOTS[i][0] - JP_LAND_SPOTS[j][0], JP_LAND_SPOTS[i][1] - JP_LAND_SPOTS[j][1]) < 40)
        throw new Error('jump pad: two landing spots are closer than a player is wide');
}

const LX = [-CW_LAT - CW_HALF, -CW_LAT + CW_HALF];   // west branch lane
const EX = [CW_LAT - CW_HALF, CW_LAT + CW_HALF];     // east branch lane
const LW = [-CW_SWING - CW_HALF, -CW_SWING + CW_HALF];  // west outer lane (ridge crest / cistern west edge)
const EW = [CW_SWING - CW_HALF, CW_SWING + CW_HALF];    // east outer lane (the weave's far runs)
const PX_ = [-CW_PLANK_HALF, CW_PLANK_HALF];         // the centre plank

// THE TWO MOUTHS. Declared, never drawn — the terrace and the citadel own those
// floors. Without them the rail pass would wall the road off at both ends.
roadPortal('causeway terrace mouth', -CW_HALF, CW_HALF, TER_Y2 - ROAD_G, TER_Y2, ZB);
// THE CITADEL MOUTH IS CW_FLARE WIDE, NOT CW_HALF. This was 160 while the road
// that meets it flares to 240, and the 40 units either side promptly became
// what the rail pass thought was an exposed edge — so it dutifully guarded them,
// putting two rail bollards and their clip caps ON THE CROWN HALL FLOOR, inside
// the gate opening, at the finish line. Three independent reviewers found it and
// none of the automated checks did: the road builder cannot see the hall, and
// the geometry lint only reports INVISIBLE misplaced walls, so a visible rail
// standing on somebody else's floor passes clean. roadEmit now throws on it —
// see the portal-coverage assert there.
roadPortal('causeway citadel mouth', -CW_FLARE, CW_FLARE, cwY[9], cwY[9] + ROAD_G, ZB);

// docs/163 THE CUT: three pieces instead of the whole road (the F approach and
// its flare below are common to both layouts). Labels keep the `causeway`
// prefix on purpose — lint_tod_geometry's road bucket, its exact-grid proof
// and the rail pass all key on it.
if (CW_CUT) {
  roadFlat('causeway A gate-run', -CW_HALF, CW_HALF, cwY[0], JP_LAND_Y1, ZB);
  roadFlat('causeway landing deck', -JP_DECK_HALF, JP_DECK_HALF, JP_LAND_Y1, JP_LAND_Y2, ZB);
  roadFlat('causeway launch deck', -JP_LAUNCH_HALF, JP_LAUNCH_HALF, JP_LAUNCH_Y1, JP_LAUNCH_Y2, ZB);   // THE BALCONY
  // THE ENCLOSED HALLWAY (see HW_ROOMS): every piece walled + roofed
  roadFlat('causeway hallway junction', HW_JUNC.x1, HW_JUNC.x2, HW_JUNC.y1, HW_JUNC.y2, ZB);
  roadFlat('causeway hallway east', HW_EAST.x1, HW_EAST.x2, HW_EAST.y1, HW_EAST.y2, ZB);
  roadFlat('causeway hallway power room', HW_POWER.x1, HW_POWER.x2, HW_POWER.y1, HW_POWER.y2, ZB);
  roadFlat('causeway hallway west', HW_WEST.x1, HW_WEST.x2, HW_WEST.y1, HW_WEST.y2, ZB);
  roadFlat('causeway hallway teleporter room', HW_TELE.x1, HW_TELE.x2, HW_TELE.y1, HW_TELE.y2, ZB);
  roadFlat('causeway hallway south', HW_SOUTH.x1, HW_SOUTH.x2, HW_SOUTH.y1, HW_SOUTH.y2, ZB);
  for (const t of ['causeway hallway junction', 'causeway hallway east', 'causeway hallway power room',
                   'causeway hallway west', 'causeway hallway teleporter room', 'causeway hallway south'])
    ROAD_WALLED.add(t);
} else {   // ---- the v12 road, unchanged: every lane below up to the J4 merge ----
// A — the gate run. The GATE (an entity, emitted further down) stands across it.
roadFlat('causeway A gate-run', -CW_HALF, CW_HALF, cwY[0], cwY[1], ZB);
roadFlat('causeway J1 fork', -CW_LAND, CW_LAND, cwY[1], cwY[2], ZB);

// (roadDogleg is GONE — v12. It built both halves of a fork as one mirrored
// helper, which is exactly why the road felt "simple and straightforward":
// mirrored shapes cannot surprise twice. The lanes below are written out one
// by one ON PURPOSE — each is a different shape — and every block's y-run is
// pinned to the cwY[] boundaries, so roadStair's own tread arithmetic plus the
// roadEmit adjacency sweep replace the old end-y asserts.)

// FIRST FORK — THE RIDGE (west) vs THE BROKEN STAIR (east).
// The ridge is the long open lane: climb, run the OUTER crest, cut back in,
// run the INNER shelf, descend. Two direction changes at height, so the crest
// never shows you all of itself — and from +256 it is the best view of the
// crown anywhere on the road. The awe lane, paid for in exposure and distance.
{
  const zTop = ZB + CW_HUMP, climb = CW_TREAD * (CW_HUMP / CW_RISE);   // 640
  const yA = cwY[2];
  roadStair('causeway W ridge climb', LX[0], LX[1], yA, yA + 640, ZB, zTop);
  roadFlat('causeway W ridge elbow out', LW[0], LX[1], yA + 640, yA + 800, zTop);
  roadFlat('causeway W ridge crest', LW[0], LW[1], yA + 800, yA + 1200, zTop);
  roadFlat('causeway W ridge jog', LW[0], LX[1], yA + 1200, yA + 1360, zTop);
  roadFlat('causeway W ridge shelf', LX[0], LX[1], yA + 1360, yA + 1600, zTop);
  roadStair('causeway W ridge descent', LX[0], LX[1], yA + 1600, cwY[3], zTop, ZB);
  if (yA + 1600 + climb !== cwY[3]) throw new Error('ridge y-budget does not close on J2');
}
// The broken stair is the short blind lane: two half-drops with a pocket
// between them, a 640-long HOLLOW at -256 whose walls hide everything, then
// one unbroken 16-tread ascent — the merge above is invisible until the last
// step. Straight in plan, terrifying in section. The hollow is split in two
// so the deepest ground on this fork is also its riser-densest.
{
  const zMid = ZB - CW_HUMP / 2, zLow = ZB - CW_HUMP;
  const yA = cwY[2];
  roadStair('causeway E steps drop 1', EX[0], EX[1], yA, yA + 320, ZB, zMid);
  roadFlat('causeway E steps pocket', EX[0], EX[1], yA + 320, yA + 640, zMid);
  roadStair('causeway E steps drop 2', EX[0], EX[1], yA + 640, yA + 960, zMid, zLow);
  roadFlat('causeway E hollow 1', EX[0], EX[1], yA + 960, yA + 1280, zLow);
  roadFlat('causeway E hollow 2', EX[0], EX[1], yA + 1280, yA + 1600, zLow);
  roadStair('causeway E hollow climb', EX[0], EX[1], yA + 1600, cwY[3], zLow, ZB);
}

roadFlat('causeway J2 merge', -CW_LAND, CW_LAND, cwY[3], cwY[4], ZB);

// THE NARROWS — the old flat spine, with its middle PINCHED to the plank's
// width. Every route crosses this, so the pinch is the road's one guaranteed
// choke: 320 units of single file directly under the second portal frame,
// with the shoulder bollards the rail pass derives marking the squeeze. Two
// pieces, two risers — the choke feeds itself.
roadFlat('causeway N throat south', -CW_HALF, CW_HALF, cwY[4], cwY[4] + 160, ZB);
roadFlat('causeway N narrows 1', -CW_PLANK_HALF, CW_PLANK_HALF, cwY[4] + 160, cwY[4] + 320, ZB);
roadFlat('causeway N narrows 2', -CW_PLANK_HALF, CW_PLANK_HALF, cwY[4] + 320, cwY[4] + 480, ZB);
roadFlat('causeway N throat north', -CW_HALF, CW_HALF, cwY[4] + 480, cwY[5], ZB);

roadFlat('causeway J3 fork', -CW_LAND, CW_LAND, cwY[5], cwY[6], ZB);

// SECOND FORK — three ways, three flavours of fear.
// THE UNDERCROFT (west): a pure V — 24 treads down, a wide CISTERN at -384,
// 24 treads back up. Stairs draw no risers, so the descent is eerily quiet and
// the cistern is where the ambush lives; the ascent is 960 units of stairs
// with the merge hidden past the crest the whole way. From the cistern floor
// the crown's entire underside hangs overhead — the deep lane is also the
// map's best look UP at the thing you are running toward.
{
  const zLow = ZB - CW_DEEP, run = CW_TREAD * (CW_DEEP / CW_RISE);   // 960
  const yA = cwY[6];
  roadStair('causeway W undercroft descent', LX[0], LX[1], yA, yA + run, ZB, zLow);
  roadFlat('causeway W undercroft cistern', LW[0], LX[1], yA + run, yA + run + 320, zLow);
  roadStair('causeway W undercroft ascent', LX[0], LX[1], yA + run + 320, cwY[7], zLow, ZB);
  if (yA + 2 * run + 320 !== cwY[7]) throw new Error('undercroft y-budget does not close on J4');
}
// THE PLANK (centre) — unchanged in spirit from v10.11, raised to +256 so it
// clears the fork by the full hump. Dead straight, 120 wide, no cover at all.
// Same walked length as the undercroft's straight V — the choice between them
// is not distance, it is WHICH fear: constant fire in the open, or the quiet
// deep and one blind climb. See CW_PLANK_HALF for the 120-not-160 record.
{
  const climb = CW_TREAD * (CW_PLANK_HUMP / CW_RISE);   // 640
  const zTop = ZB + CW_PLANK_HUMP;
  const yA = cwY[6], yB = yA + climb, yC = cwY[7] - climb;
  roadStair('causeway P plank climb', PX_[0], PX_[1], yA, yB, ZB, zTop);
  // FOUR pieces, not one. Risers are placed one per flat piece, so a single
  // long plank drew ONE riser while other lanes drew three — the lane meant
  // to be the hot one was the quietest on the road. Split, it is dense: four
  // risers over the short straight middle, with nothing to hide behind.
  const seg = (yC - yB) / 4;
  for (let i = 0; i < 4; i++)
    roadFlat(`causeway P plank ${i + 1}`, PX_[0], PX_[1], yB + seg * i, yB + seg * (i + 1), zTop);
  roadStair('causeway P plank drop', PX_[0], PX_[1], yC, cwY[7], zTop, ZB);
}
// THE WEAVE (east): never leaves deck height, never runs straight for more
// than 480 units. Four jogs = eight blind corners; nine flat pieces = nine
// risers, the most infested ground on the road. Flat does not mean safe —
// this is the lane for players who fear stairs more than zombies.
{
  const yA = cwY[6];
  const W = [
    ['run 1', EX[0], EX[1], 0, 240], ['jog 1', EX[0], EW[1], 240, 400],
    ['run 2', EW[0], EW[1], 400, 880], ['jog 2', EX[0], EW[1], 880, 1040],
    ['run 3', EX[0], EX[1], 1040, 1280], ['jog 3', EX[0], EW[1], 1280, 1440],
    ['run 4', EW[0], EW[1], 1440, 1760], ['jog 4', EX[0], EW[1], 1760, 1920],
    ['run 5', EX[0], EX[1], 1920, 2240],
  ];
  for (const [nm, x1, x2, y1, y2] of W)
    roadFlat(`causeway E weave ${nm}`, x1, x2, yA + y1, yA + y2, ZB);
  if (yA + 2240 !== cwY[7]) throw new Error('weave y-budget does not close on J4');
}

roadFlat('causeway J4 merge', -CW_LAND, CW_LAND, cwY[7], cwY[8], ZB);
}   // ---- end of the v12 road (!CW_CUT) ----
// F — the approach, and then a FLARE into the citadel gate.
//
// THE FLARE IS A BUG FIX, not decoration (lint_tod_causeway, 2026-08-23). The
// gate opening is GATE_HALF*2 = 256 wide; the road is 160 wide with rails out to
// +/-100. That left ~28 units of open hall floor on EACH side of the doorway,
// inside the opening, guarded by nothing — walk into the citadel a little wide
// and you drop 19,000 units. Nothing in the .map said so and the road's own rail
// pass could not see it, because the hole was not on the road: it was on the
// hall's floor, one column past where the road stopped.
//
// So the mouth widens to meet the opening. The rail pass then guards the flare's
// own flanks and the two gap columns become deck. The side rails overlap the
// gate posts by ~12 units, which is fine — the CSG merges them and a rail dying
// into a gate post is what it should look like anyway.

roadFlat('causeway F approach', -CW_HALF, CW_HALF, cwY[8], cwY[9] - 160, ZB);
roadFlat('causeway F gate flare', -CW_FLARE, CW_FLARE, cwY[9] - 160, cwY[9], ZB);
// THE ENCLOSED HALLWAY begins at the gate: the throat through the crown is walled + roofed too
if (CW_CUT) { ROAD_WALLED.add('causeway F approach'); ROAD_WALLED.add('causeway F gate flare'); }

const CW_STATS = roadEmit();
// THE INVISIBLE BARRIER on the balcony (2026-09-26, see the crown wall clip
// block): the E / W rails and the N rail outside the bridge doorway carry clip
// to the sky. The SOUTH rail keeps its 168u player clip, but stays open ABOVE
// that on purpose: the jump pad's arc leaves over it (test_jumppad sweeps that lane) - a swing over that rail is the one
// way off the balcony and it lands in the Fall, where _tod_archer's out-of-
// bounds return catches a miss.
{
  const BZ1 = ZB + PARA_H + RAIL_CAP_H;
  cbox('crown balcony clip W', -JP_LAUNCH_HALF - ROAD_G, -JP_LAUNCH_HALF, JP_LAUNCH_Y1, JP_LAUNCH_Y2, BZ1, BARRIER_TOP, MAT.clip);
  cbox('crown balcony clip E', JP_LAUNCH_HALF, JP_LAUNCH_HALF + ROAD_G, JP_LAUNCH_Y1, JP_LAUNCH_Y2, BZ1, BARRIER_TOP, MAT.clip);
  cbox('crown balcony clip N west', -JP_LAUNCH_HALF - ROAD_G, -CW_HALF - ROAD_G, JP_LAUNCH_Y2, JP_LAUNCH_Y2 + ROAD_G, BZ1, BARRIER_TOP, MAT.clip);
  cbox('crown balcony clip N east', CW_HALF + ROAD_G, JP_LAUNCH_HALF + ROAD_G, JP_LAUNCH_Y2, JP_LAUNCH_Y2 + ROAD_G, BZ1, BARRIER_TOP, MAT.clip);
}
const CW_WALK = CW_STATS.walk;   // shortest walk, terrace mouth -> citadel mouth

// PORTAL FRAMES on the three on-axis stretches — the milestones you run through,
// and the only three places where the whole party is guaranteed to be in one lane.
// v12: each portal carries its own x-offset now — portal 2 stands at the
// NARROWS' pinched width (posts riding the shoulder-rail line at +-80), so the
// frame itself announces the squeeze; 1 and 3 keep the full road width.
// docs/163 THE CUT: the gate-run is 240 long now, so its portal stands at the
// stub's midpoint, and the narrows portal went with the narrows. The gold one
// inside the crown's throat is on the crown's stub and stays exactly where it was.
const CW_PORTALS = [
  { y: (cwY[0] + (CW_CUT ? JP_LAND_Y1 : cwY[1])) / 2, xo: CW_HALF + PARA, m: MAT.crownFascia },   // mid gate-run
  ...(CW_CUT ? [] : [{ y: (cwY[4] + cwY[5]) / 2, xo: CW_PLANK_HALF + PARA, m: MAT.crownFascia }]), // over the narrows pinch
  // THE LAST PORTAL IS GOLD, NOT CYAN, because it is not on the road any more.
  // Measured 2026-08-25: portal 3 stands at y 7344-7376, and the crown's band
  // inner face is at 7328 — so the third portal is INSIDE THE CROWN'S THROAT,
  // 16 units past the wall, in the courtyard between the rim and the hall gate.
  // In cyan it was the brightest object in the arrival shot and the only foreign
  // hue in the composition, sitting exactly on the map's most important framing
  // moment. The road's language is cyan and the crown's is gold; the colour
  // change IS the arrival, so the portal that stands inside the crown wears the
  // crown's colour. The first two keep the road's.
  { y: (cwY[8] + cwY[9]) / 2, xo: CW_HALF + PARA, m: MAT.crownGold },
];
CW_PORTALS.forEach(({ y: yp, xo, m }, k) => {
  cbox(`causeway portal ${k + 1} post W`, -xo - 24, -xo, yp - 16, yp + 16, ZB, ZB + 224, m);
  cbox(`causeway portal ${k + 1} post E`, xo, xo + 24, yp - 16, yp + 16, ZB, ZB + 224, m);
  cbox(`causeway portal ${k + 1} lintel`, -xo - 24, xo + 24, yp - 16, yp + 16, ZB + 224, ZB + 256, m);
});

// THE AVENUE (v12) — four PAIRS of jewelled gold pylons floating in the void
// beside the road: two flanking the gate-run (visible from the terrace all
// game, through the sealed gate — the road advertises itself), two flanking
// the narrows' throats. A ceremonial avenue is the oldest scale-rhythm trick
// there is: passing identical markers is what makes 7,000 units FEEL like
// 7,000 units. They hang bottomless over the drop — bead below, head above,
// both WIDER than the shaft (the pendilia rule: nothing narrows to its tip).
// PLACEMENT RULES — ASSERTED below, not just written down (the CW_FLARE block
// records what happens to prose rules in this section: "violated within the
// hour"):
//   * x +-360: the nearest pylon FACE (head/collar at |x| 288) is 188 units
//     from the widest rail cap face (x 100) — but distance is NOT what makes
//     them unreachable: every derived rail carries a 168-tall clip cap
//     (RAIL_H 56 + RAIL_CAP_H 112, crail()), so no jump can even be STARTED
//     toward a pylon from any deck. The gap is hygiene, not the guarantee.
//   * y clear of every junction landing AND of the landing-edge rail columns
//     (a pylon overlapping a derived rail would CSG-weld into it). Tightest
//     today: 20 units to the J2-north / J3-south rail columns.
//   * every _tinted/_tinted_edge box is >64 tall in z, so the lint can never
//     class a pylon slab as an unguarded floor node hanging over the void.
//   * labels start with neither crown/mast (crownBB stays the circlet's) nor
//     causeway/terrace (the lint's road bucket stays pure road) — which also
//     means NO EXISTING GATE SEES A PYLON: not 5f.9, not the sky-seal bb, not
//     the lint (non-floor solids). Hence the assert below is the only guard.
// Sapphire jewels, not ruby: blue is the ROAD's language (cyan portals, cyan
// deck glow) — the colour change at the mouth stays the arrival cue.
const PYLON_HALF = 72;   // the widest tier (the head)
function avenuePylon(tag, px, py) {
  // THE ONE PYLON GATE: no pylon may come within one grid column (ROAD_G) of
  // any declared road cell — the rails and their caps live in exactly that
  // one column outside each deck edge, so "clear of cell+ROAD_G" IS "clear of
  // every rail the pass can ever derive". Fires on any future nudge of
  // CW_LAND, the span budget, pylon y's, or PYLON_HALF.
  for (const c of roadCells)
    if (px + PYLON_HALF > c.x1 - ROAD_G && px - PYLON_HALF < c.x2 + ROAD_G &&
        py + PYLON_HALF > c.y1 - ROAD_G && py - PYLON_HALF < c.y2 + ROAD_G)
      throw new Error(`avenue pylon at (${px},${py}) fouls road cell "${c.tag}" or its rail column`);
  cbox(`${tag} bead`, px - 64, px + 64, py - 64, py + 64, TOP2 - 384, TOP2 - 288, MAT.jewelSapphire);
  cbox(`${tag} shaft`, px - 40, px + 40, py - 40, py + 40, TOP2 - 288, TOP2 + 416, MAT.crownGold);
  cbox(`${tag} collar`, px - 64, px + 64, py - 64, py + 64, TOP2 - 16, TOP2 + 64, MAT.crownBrass);
  cbox(`${tag} head`, px - 72, px + 72, py - 72, py + 72, TOP2 + 416, TOP2 + 496, MAT.crownGold);
  cbox(`${tag} pip`, px - 48, px + 48, py - 48, py + 48, TOP2 + 496, TOP2 + 576, MAT.jewelSapphire);
}
// docs/163 THE CUT: the two mid-road pairs flanked the narrows, which is sky
// now — they move to the corners of the LAUNCH deck, so the pad stands between
// four gold pylons and the landing deck keeps the original two pairs.
// THE BALCONY (2026-09-25): the launch-side pair moved out to flank the 1280
// balcony, one grid column + the head clear of its rails, the north one under
// the piers' y (6848) and clear of the overlook passage's rail column.
const AVENUE = CW_CUT
  ? [[360, 640], [360, 960],
     [JP_LAUNCH_HALF + ROAD_G + PYLON_HALF + 20, JP_LAUNCH_Y1 + 80],
     [JP_LAUNCH_HALF + ROAD_G + PYLON_HALF + 20, JP_LAUNCH_Y2 - 80]]
  : [[360, 640], [360, 960], [360, 3792], [360, 4208]];
for (const [px, py] of AVENUE)
  for (const sx of [-1, 1])
    avenuePylon(`avenue pylon y${py}${sx > 0 ? 'E' : 'W'}`, sx * px, py);

// The road's own extremes, for the zone volume. DERIVED — a volume that misses
// a piece of road leaves it outside roof_zone, i.e. no spawns and no zone logic
// on that piece, which is invisible until somebody plays it.
const CW_XMIN = Math.min(...roadCells.map(c => c.x1)) - PARA - 64;
const CW_XMAX = Math.max(...roadCells.map(c => c.x2)) + PARA + 64;
const CW_ZMIN = Math.min(...roadCells.map(c => c.z)) - SLAB - 64;
const CW_ZMAX = Math.max(...roadCells.map(c => c.z)) + 400;
// Y from the DECK cells only — the two portals are the terrace and the hall
// floor, which belong to their own volumes. This used to be the literals
// TER_Y2..HS while x and z were derived, so a switchback that left that band
// would have landed in NO ZONE AT ALL: no risers, get_zone_from_position
// undefined so every boss spawn candidate there rejected, and no zone logic
// ever seeing a player standing on it. Nothing would have said so.
const CW_YMIN = Math.min(...roadCells.filter(c => c.deck).map(c => c.y1));
const CW_YMAX = Math.max(...roadCells.filter(c => c.deck).map(c => c.y2));
// docs/163 THE CUT — each stub's own box, for its OWN zone: the terrace stub
// joins roof_zone, the crown stub joins crown_zone (the hall's). One box over
// both would put a player on the launch deck in the terrace's zone and hand the
// crown's stub to whichever zone happened to be occupied. Y is the deck cells
// plus a rail-and-margin at the stub's FREE end only (its other end meets a
// neighbour volume: the terrace at TER_Y2, the hall at HS).
const JP_GAP_MID = (JP_LAND_Y2 + JP_LAUNCH_Y1) / 2;
function jpSideBox(pred) {
  const cs = roadCells.filter(c => c.deck && pred(c));
  return {
    x1: Math.min(...cs.map(c => c.x1)) - PARA - 64, x2: Math.max(...cs.map(c => c.x2)) + PARA + 64,
    y1: Math.min(...cs.map(c => c.y1)), y2: Math.max(...cs.map(c => c.y2)),
    z1: Math.min(...cs.map(c => c.z)) - SLAB - 64, z2: Math.max(...cs.map(c => c.z)) + 400,
  };
}
const JP_TER_BOX = CW_CUT ? jpSideBox(c => c.y2 <= JP_GAP_MID) : null;
const JP_CRN_BOX = CW_CUT ? jpSideBox(c => c.y1 >= JP_GAP_MID) : null;
if (CW_CUT) {
  JP_TER_BOX.y2 += PARA + 64;   // past the landing deck's north rail
  JP_CRN_BOX.y1 -= PARA + 64;   // past the launch deck's south rail
  if (JP_TER_BOX.y1 !== TER_Y2 || JP_CRN_BOX.y2 !== HS)
    throw new Error(`jump pad zone boxes do not meet their neighbours: terrace stub from ${JP_TER_BOX.y1} (TER_Y2 ${TER_Y2}), crown stub to ${JP_CRN_BOX.y2} (HS ${HS})`);
}

// THE SKY ENCLOSURE IS DERIVED FROM THE HALL, NOT FROM THE ROAD. SKY_IN is
// max(2900, HN + 384), so it follows CW_LEN through HS -> HN — but only in y.
// A road that swung far enough sideways, or a crest tall enough, would poke
// through the enclosure and leave a hole in the world that no geometry check
// here would notice. Cheap to assert, so assert it.
if (Math.max(-CW_XMIN, CW_XMAX) + 256 > SKY_IN)
  throw new Error(`causeway reaches x ${CW_XMAX} but the sky wall is at ${SKY_IN}`);
if (CW_ZMAX + 256 > SKY_TOP)
  throw new Error(`causeway reaches z ${CW_ZMAX} but the sky ceiling is at ${SKY_TOP}`);

// PUBLIC to the zone code below. Every point is on a piece of road, at that
// piece's own height — placed BY SHAPE, never by fraction of length. Half this
// road is no longer at x=0 and no longer at TOP2, and a fractional point would
// hang in mid-air or bury itself under a crest. Flats only: a riser on a stair
// tread surfaces a zombie mid-flight.
function causewayRunPoints() {
  return roadPieces.filter(p => p.kind === 'flat').map(p => cpt(p.cx, p.cy, p.cz));
}
// ...and the same points in the CROWN FRAME, unmirrored. The only caller is the
// light pass, which wraps every point in CL() and applies cpt() itself, so a
// mirrored value here would be double-mirrored. The name says "crownFrame"
// because the two functions above and below differ ONLY in whether cpt() has
// been applied, and at CM=+1 — the only parity anyone has generated — they
// return identical numbers. Anyone adding a second consumer (FX emitters,
// ambient sound origins, debug markers) would reach for whichever name looked
// convenient and be right half the time, in the frame nobody tests.
function causewayLightPointsCrownFrame() {
  return roadPieces.filter(p => p.kind === 'flat').map(p => [p.cx, p.cy, p.cz]);
}
function causewayPortalPoints() { return CW_PORTALS.map(p => cpt(0, p.y, TOP2)); }

// --- 5d. CROWN HALL: the citadel ---------------------------------------------
// THIS IS NOW THE INNER CHAMBER OF THE CIRCLET, not the building. Section 5f
// wraps a 4096 x 3264 x 6592 gold crown around everything below. The hall's
// floor, walls, gate, dais, sconces and extraction pad are UNCHANGED in
// position (user 2026-08-25: "We dont need to edit the floor of the room or
// space") — only their materials moved, from blue to velvet-and-gold, because
// the inside of a crown is what this room is now.
// Whole-crown material pass: retain the original single slab and wall solids.
// art_cohesion/crown_surfaces.js assigns the complete island's authored finishes.
cbox('crown hall floor',-HW,HW,HS,HN,TOP2-SLAB,TOP2,MAT.hallFloor);

// THE UNDERBELLY IS THE MAP'S MOST-SEEN SURFACE AND IT USED TO BE INVISIBLE.
// The old three ziggurat tiers + gravity core were MAT.ground (dark_blue_tinted)
// — within a few percent of the atmosphere's fog colour — so from the base arena
// they rendered as a black square (see docs/crown_now_under.png). They are gone.
// The velvet cap here and the ten-tier gold/brass skirt in 5f replace them: from
// below you now look up the inside of a banded cone, which is the "radiate
// crown" read and the thing that actually carries the silhouette.
cbox('crown cap velvet', -832, 832, HYC - 832, HYC + 832, TOP2 + CR_ERM_Z1, TOP2 - 112, MAT.crownVelvet);
cbox('crown cap fillet', -856, 856, HYC - 856, HYC + 856, TOP2 - 112, TOP2 - SLAB, MAT.crownGold);

// walls — run BETWEEN the gate posts (no overlapping solids). VELVET now: they
// are invisible from outside once the band exists, but they are the whole
// interior of the hold-out arena, and purple-and-gold is what the inside of a
// crown looks like.
const WZ1 = TOP2, WZ2 = TOP2 + HWALL_H;
cbox('crown wall S west', -(HW - CTOWER), -GATE_HALF - POST_W, HS, HS + HWALL, WZ1, WZ2, MAT.hallWall);
cbox('crown wall S east', GATE_HALF + POST_W, HW - CTOWER, HS, HS + HWALL, WZ1, WZ2, MAT.hallWall);
cbox('crown gate lintel', -GATE_HALF, GATE_HALF, HS, HS + HWALL, TOP2 + GATE_H, WZ2, MAT.hallWall);
cbox('crown wall N', -(HW - CTOWER), HW - CTOWER, HN - HWALL, HN, WZ1, WZ2, MAT.hallWall);
cbox('crown wall W',-HW,-HW+HWALL,HS+CTOWER,HN-CTOWER,WZ1,WZ2,MAT.hallWall);
cbox('crown wall E', HW - HWALL, HW, HS + CTOWER, HN - CTOWER, WZ1, WZ2, MAT.hallWall);
// the wall corners the old corner towers used to fill. They were 192-square
// stacks that narrowed 192->144->96->40; a shape that narrows to a point is a
// SPIRE, and spires are the castle token this redesign exists to kill. The
// corner posts stay (the wall needs closing) but they are plain velvet mass now
// and the crown's actual points live out on the ring, 1888 units further out.
for (const [sx, sy, tag] of [[-1, HS, 'SW'], [1, HS, 'SE'], [-1, HN - CTOWER, 'NW'], [1, HN - CTOWER, 'NE']])
  cbox(`crown wall corner ${tag}`, sx > 0 ? HW - CTOWER : -HW, sx > 0 ? HW : -(HW - CTOWER), sy, sy + CTOWER, WZ1, WZ2, MAT.hallWall);
// gold cornice band, 16 proud of the outer faces, top 64 of the wall. It only
// reads from INSIDE now (the band hides the hall completely from outside), so
// it went from cyan to a glowing gold seam.
cbox('crown cornice S', -HW - 16, HW + 16, HS - 16, HS, WZ2 - 64, WZ2, MAT.hallGold);
cbox('crown cornice N', -HW - 16, HW + 16, HN, HN + 16, WZ2 - 64, WZ2, MAT.hallGold);
cbox('crown cornice W', -HW - 16, -HW, HS, HN, WZ2 - 64, WZ2, MAT.hallGold);
cbox('crown cornice E', HW, HW + 16, HS, HN, WZ2 - 64, WZ2, MAT.hallGold);

// the GATE: gold posts flanking the opening. The two 32->20 spires that used to
// stand on them subtended 0.05 and 0.6 degrees from the base arena — 1.5 px and
// half a pixel — i.e. they were never visible from anywhere in the map. Deleted.
cbox('crown gate post W', -GATE_HALF - POST_W, -GATE_HALF, HS - 24, HS + HWALL + 24, TOP2, WZ2 + 64, MAT.hallGold);
cbox('crown gate post E', GATE_HALF, GATE_HALF + POST_W, HS - 24, HS + HWALL + 24, TOP2, WZ2 + 64, MAT.hallGold);

// THE INVISIBLE BARRIER (user 2026-09-26, after the first grapple playtest: "I'm
// still able to go out of bounds ... build invisible barriers going up on all
// the areas that we don't want to go out of bounds. I don't want an invisible
// roof ... and I'm also able to land on places I shouldn't"). The rope reaches
// 3000-5000 units and the hall walls are 576 tall, so a hook on a wall top or
// on the crown above carried the player over the wall onto the bell (docs: the
// 11:39 log, OOB x15). Map 1's answer, reused: plain `clip` from every wall's
// top straight up to the SKY (no roof - the sky is open, the LINE is closed).
// Clip is invisible, unlit, not in the lit-area budget; the navmesh never
// reaches it. The gate opening stays open (its lintel top is clipped like the
// wall). The corner posts and gate posts get the same column.
{
  const CZ1 = WZ2;
  cbox('crown wall clip S west', -(HW - CTOWER), -GATE_HALF - POST_W, HS, HS + HWALL, CZ1, BARRIER_TOP, MAT.clip);
  cbox('crown wall clip S east', GATE_HALF + POST_W, HW - CTOWER, HS, HS + HWALL, CZ1, BARRIER_TOP, MAT.clip);
  cbox('crown wall clip S lintel', -GATE_HALF, GATE_HALF, HS, HS + HWALL, CZ1, BARRIER_TOP, MAT.clip);
  cbox('crown wall clip N', -(HW - CTOWER), HW - CTOWER, HN - HWALL, HN, CZ1, BARRIER_TOP, MAT.clip);
  cbox('crown wall clip W', -HW, -HW + HWALL, HS + CTOWER, HN - CTOWER, CZ1, BARRIER_TOP, MAT.clip);
  cbox('crown wall clip E', HW - HWALL, HW, HS + CTOWER, HN - CTOWER, CZ1, BARRIER_TOP, MAT.clip);
  for (const [sx, sy, tag] of [[-1, HS, 'SW'], [1, HS, 'SE'], [-1, HN - CTOWER, 'NW'], [1, HN - CTOWER, 'NE']])
    cbox(`crown wall corner clip ${tag}`, sx > 0 ? HW - CTOWER : -HW, sx > 0 ? HW : -(HW - CTOWER), sy, sy + CTOWER, CZ1, BARRIER_TOP, MAT.clip);
  cbox('crown gate post clip W', -GATE_HALF - POST_W, -GATE_HALF, HS - 24, HS + HWALL + 24, WZ2 + 64, BARRIER_TOP, MAT.clip);
  cbox('crown gate post clip E', GATE_HALF, GATE_HALF + POST_W, HS - 24, HS + HWALL + 24, WZ2 + 64, BARRIER_TOP, MAT.clip);
}

// interior: the uplink dais (unchanged since v10; the alarm button stands on it)...
cbox('uplink dais', -DAIS, DAIS, HYC - DAIS, HYC + DAIS, TOP2, TOP2 + DAIS_H, MAT.hallStep);

// ...and THE BASILICA (v16.35, 2026-09-02). User: the hall was "quite open
// and the spots where ammo crate and pap and alter are odd and not intuitive
// ... less open ... organizes things ... enhances the room", with one rule:
// "dont change the overall size or outside of functionality". So the floor,
// the walls, the gate, the dais and every zone box are byte-identical to v12;
// this block only FURNISHES the inside. Plan, before/after drawings and the
// options rejected: docs/70_crown_hall_basilica.md.
//
// THE PLAN IN ONE LINE: gate -> nave -> crossing -> sanctuary. Two pier lines
// at x +-NAVE_X make a 768-wide nave and two 304-clear aisles; the two upgrade
// shrines (HEAVENLY GIFT ALTAR west, PACK-A-PUNCH east) face each other across
// the dais at the crossing under gold canopies; the ammo crate stays in the
// east aisle one bay inside the gate; the extraction pad rises on a two-step
// sanctuary in front of a reredos on the north wall. NOTHING IS ROOFED — the
// crown overhead is why this room exists — every piece stops at +248 under a
// 576 wall, and the one tall object (the reredos, +456 with its monde) stands
// against the far wall where it closes the axis instead of the sky.
//
// THE OLD FURNITURE IS GONE ON PURPOSE: the four +-448 pylon plinths (v12) are
// replaced by the colonnade, and the 1u glowing ring at +-632 — whose WEST
// band sat under the altar's trigger origin for three months and killed its
// prompt (v16.27, memory trigger-origin-under-decal) — by the carpet seams.
//
// CONTRACTS KEPT (read _tod_finale before moving anything here):
//   * hall_center + the 160 gather ring (gather_spot): all four seats land on
//     open nave floor; the two on the transept seams stand on 1u walk-over.
//   * the dais: untouched (ASCEND teleporter + trigger, the hound spawner).
//   * hall risers (+-560, HS+280 / HN-280): open aisle bays; the nearest pier
//     base ends at x 440, the sanctuary at x 320, the canopies are overhead.
//   * siege_panzer_org moves 100u toward the axis (crown-data emission) to
//     keep clear floor round the drop — TOD_BOSS_CLEARANCE is boss-to-boss,
//     nothing in the director checks boss-to-geometry for us.
//   * hall_pillar_orgs (the count-in glow hosts) ride the FOUR CROSSING PIERS,
//     above the beam (+232) and below every light.
//   * exfil_org's z is PAD_TOP, emitted from the same constant as the pad.
//   * lint_tod_geometry: every level change is 16 (STEP_MAX 18, no rails
//     needed) and every OVERHEAD piece — beams, capitals, canopies — is PLAIN
//     gold, never a tinted material: the lint classes a <=64-thick tinted slab
//     as a DECK and would flood a "floor" at +216. The sanctuary tiers are
//     tinted ON PURPOSE (walkable). Pier bases are plain gold: a 24-tall
//     BLOCK, not a step.
//   * every vendor trigger origin floats (v16.27), so a 1u seam under a
//     machine's approach can no longer kill its prompt.
//   * no two solids overlap: beam segments run BETWEEN capitals, seams stop at
//     each other's edges, the canopy rests ON the pilasters and panel.
const NAVE_X   = 384;                                   // pier line: nave 768, aisles 304 clear (424 -> 728)
const PIER_Y   = [-632, -408, -184, 184, 408, 632].map(d => HYC + d);   // 7976 8200 8424 | 8792 9016 9240
const PIER_H   = 176, PIER_CAP = 40;                    // ruby shaft to +176; gold capital = the beam depth
const BEAM_Z1  = TOP2 + PIER_H, BEAM_Z2 = BEAM_Z1 + PIER_CAP;   // +176 .. +216
const SHR_Y1   = HYC - 112, SHR_Y2 = HYC + 112;         // the shrine bay (224) inside the 288-clear crossing gap
const PIL_W    = 32;                                    // wall pilasters framing each shrine bay
const CAN_Z1   = BEAM_Z2, CAN_Z2 = BEAM_Z2 + 32;        // canopy +216 .. +248, resting on the pilasters
const SANC_Y1  = HN - HWALL - 384;                      // sanctuary tier 1 starts here (8952)
const SANC_X1  = 320, SANC_X2 = 280;                    // tier 1 / tier 2 half-widths (clear of the pier bases at 328)
const PAD_TOP  = 40;                                    // the pad's top over TOP2 — exfil_org() below reads THIS
const SEAM_W   = 24, SEAM_X = 300;                      // the nave carpet seams, 24 wide at x +-300
const WALL_IN  = HW - HWALL;                            // 728, the long walls' inner face
// Item-shop native test: three separated bays, front in local -Y. These anchors
// also emit script data below; their collision lives inside the visible hut.
// ONE SHOP IN THE HALL (user 2026-09-25: "the crown has two item shops inside
// of it. It should only have one"): the west bay's hut is the hall's shop; the
// east bay and the north (sanctuary) copies are gone — the sanctuary's top step
// now carries the ALARM SWITCH.
const CROWN_SHOPS = [
  // THE WEST SHRINE (user 2026-09-25: "there is a altar. I want that removed.
  // And in that spot, I want the item shop ... the item shop on one side, pack
  // a punch on the other"). The hut stands where the altar stood (x -664 =
  // wall + 64), 20 further out for its depth, facing EAST across the dais at
  // the PaP. Its solid is 198 wide x 124 deep x 130 tall: it clears the shrine
  // pilasters (y HYC+-112) by ~10 and the canopy (+216) by 86.
  {x:-644,y:HYC,z:TOP2,yaw:90},
  // THE BALCONY (user 2026-09-25: "an empty shop that players can look at"):
  // a hut on the balcony's west half, facing east across the pad. _tod_shop
  // cycles the ACTIVE shop over the first TOD_SHOP_CYCLE (1) anchors only, so
  // this one is never active: the dark, silent OFF body, by construction.
  {x:-500,y:JP_LAUNCH_Y1+320,z:TOP2,yaw:90},
];
const SHOP_CLIPS = [
  [-65,65,-43,46,0,89], [-70,70,-56,-43,0,45],
  [-97,-70,-27,33,19,79], [69,94,-29,0,24,77],
];
CROWN_SHOPS.forEach((p,i)=> {
  const a=p.yaw*Math.PI/180;
  SHOP_CLIPS.forEach((b,j)=> {
    const corners=[[b[0],b[2]],[b[0],b[3]],[b[1],b[2]],[b[1],b[3]]].map(([x,y])=>[p.x+x*Math.cos(a)-y*Math.sin(a),p.y+x*Math.sin(a)+y*Math.cos(a)]);
    cbox(`crown item shop ${i} hull ${j}`,Math.round(Math.min(...corners.map(q=>q[0]))),Math.round(Math.max(...corners.map(q=>q[0]))),Math.round(Math.min(...corners.map(q=>q[1]))),Math.round(Math.max(...corners.map(q=>q[1]))),p.z+b[4],p.z+b[5],MAT.clip);
  });
});
// THE DE JUMP PAD's SHELL (2026-10-03, docs/163 s9): the machine (tod_jumppad_frame, a script_model with CollisionMap "")
// has no collision of its own, so this ring of clip is its body: JP_SHELL_R1 .. R2 round the pad, floor to JP_SHELL_H,
// open JP_SHELL_DOOR_HALF either side of its doorway. Convex wedge prisms (transitCPoly: mirrored by cpt for the crown's
// parity, planarity + convexity checked), labelled `jump pad shell N`: lint_tod_geometry's MODEL_CLIP_COLUMNS (a model
// stands in them) and test_jumppad's arc sweep skips them (the rider is linked to a mover, so a clip is nothing to the
// flight; the VISIBLE machine is cleared by the trigger: every take-off is inside JP_SHELL_R1, out through the open
// side). Not `crown ...`: the circlet's bounding box and the road-intrusion asserts stay the circlet's.
if (CW_CUT) {
  const door = (JP_PAD_YAW + 180) % 360;
  const arc = 360 - 2 * JP_SHELL_DOOR_HALF, n = Math.ceil(arc / JP_SHELL_SEG), step = arc / n;
  const at = (r, deg, z) => [JP_PAD[0] + r * Math.cos(deg * Math.PI / 180), JP_PAD[1] + r * Math.sin(deg * Math.PI / 180), z];
  const z0 = ZB, z1 = ZB + JP_SHELL_H;
  // the bulge in this frame: the model's local angle + its yaw
  const bulge = (a0, a1) => {
    const lo = (JP_SHELL_BULGE.from + JP_PAD_YAW) % 360, len = JP_SHELL_BULGE.to - JP_SHELL_BULGE.from;
    const rel = a => ((a - lo) % 360 + 360) % 360;
    return [a0 + 0.5, (a0 + a1) / 2, a1 - 0.5].some(a => rel(a) < len);   // the wedge overlaps [lo, lo + len] (not just touches it)
  };
  for (let i = 0; i < n; i++) {
    const a0 = door + JP_SHELL_DOOR_HALF + i * step, a1 = a0 + step;
    const r2 = bulge(a0, a1) ? JP_SHELL_BULGE.r2 : JP_SHELL_R2;
    transitCPoly(`jump pad shell ${i}`,
      [at(JP_SHELL_R1, a0, z0), at(r2, a0, z0), at(r2, a1, z0), at(JP_SHELL_R1, a1, z0),
       at(JP_SHELL_R1, a0, z1), at(r2, a0, z1), at(r2, a1, z1), at(JP_SHELL_R1, a1, z1)],
      [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], MAT.clip);
  }
  // the shell leaves walking room (a 32-wide player) round every other thing on the balcony
  const room = Math.max(JP_SHELL_R2, JP_SHELL_BULGE.r2) + 32;
  const shopR = Math.max(...SHOP_CLIPS.flatMap(b => [Math.hypot(b[0], b[2]), Math.hypot(b[0], b[3]), Math.hypot(b[1], b[2]), Math.hypot(b[1], b[3])]));
  const near = [['the south rail', JP_PAD[1] - JP_LAUNCH_Y1 - PARA, 0], ['the west rail', JP_PAD[0] + JP_LAUNCH_HALF - PARA, 0],
                ['the east rail', JP_LAUNCH_HALF - PARA - JP_PAD[0], 0],
                ['the rampage inducer', Math.hypot(CROWN_INDUCER[0] - JP_PAD[0], CROWN_INDUCER[1] - JP_PAD[1]), CROWN_INDUCER_TRIG_R],
                ['Quick Revive', Math.hypot(-400 - JP_PAD[0], BALCONY_N - 29 - JP_PAD[1]), 64],   // TERRACE_QR, authored (it is cpt'd)
                ['the launch deck nav seed', Math.hypot(0, JP_LAUNCH_Y1 + 60 - JP_PAD[1]), 0],
                ...CROWN_SHOPS.map((p, i) => [`item shop ${i}`, Math.hypot(p.x - JP_PAD[0], p.y - JP_PAD[1]), shopR])];
  for (const [what, d, r] of near)
    if (d - r < room) throw new Error(`jump pad shell: ${what} is ${(d - r).toFixed(0)} from the pad's centre, inside the machine's ${room}`);
}
const ZS1 = TOP2, ZS2 = TOP2 + 1;                       // every seam: 1u, walk-over (the lounge pad-ring precedent)

// the colonnade: 12 piers (gold base / ruby shaft / gold capital) and the beam
for (const sx of [-1, 1]) {
  const cx = sx * NAVE_X, tag = sx < 0 ? 'W' : 'E';
  PIER_Y.forEach((py, i) => {
    cbox(`crown hall pier ${tag}${i + 1} base`, cx - 56, cx + 56, py - 56, py + 56, TOP2, TOP2 + 24, MAT.hallGold);
    cbox(`crown hall pier ${tag}${i + 1} shaft`, cx - 40, cx + 40, py - 40, py + 40, TOP2 + 24, BEAM_Z1, MAT.hallRuby);
    cbox(`crown hall pier ${tag}${i + 1} capital`, cx - 52, cx + 52, py - 52, py + 52, BEAM_Z1, BEAM_Z2, MAT.hallGold);
    if (i < PIER_Y.length - 1) {
      const a=py+52,b=PIER_Y[i+1]-52;
      for(let k=0;k<8;k++) {
        const ring=t=>{const y=a+(b-a)*t,z=BEAM_Z1+48*Math.sin(Math.PI*t);
          return [[cx-24,y,z],[cx+24,y,z],[cx+24,y,z+PIER_CAP],[cx-24,y,z+PIER_CAP]];};
        crownLoft(`crown hall arcade ${tag}${i+1}-${k+1}`,ring(k/8),ring((k+1)/8),MAT.hallGold);
      }
    }
  });
  // the shrine bay: two wall pilasters, a glowing panel between them behind
  // the machine, and a canopy spanning wall -> pier line over it. The machine
  // anchors (station_org west, the PaP prefab east) sit at HYC, 64 off the
  // wall face — the same standoff both have used since 2026-08-28.
  const wx1 = sx < 0 ? -WALL_IN : WALL_IN - PIL_W, wx2 = wx1 + PIL_W;
  cbox(`crown hall shrine ${tag} pilaster S`, wx1, wx2, SHR_Y1 - PIL_W, SHR_Y1, TOP2, BEAM_Z2, MAT.hallGold);
  cbox(`crown hall shrine ${tag} pilaster N`, wx1, wx2, SHR_Y2, SHR_Y2 + PIL_W, TOP2, BEAM_Z2, MAT.hallGold);
  const px1 = sx < 0 ? -WALL_IN : WALL_IN - 4, px2 = px1 + 4;
  cbox(`crown hall shrine ${tag} panel`, px1, px2, SHR_Y1, SHR_Y2, TOP2 + 32, BEAM_Z2, MAT.crownGoldSeam);
  const cx1 = sx < 0 ? -WALL_IN : NAVE_X + 40, cx2 = sx < 0 ? -(NAVE_X + 40) : WALL_IN;
  cbox(`crown hall shrine ${tag} canopy`, cx1, cx2, SHR_Y1 - PIL_W, SHR_Y2 + PIL_W, CAN_Z1, CAN_Z2, MAT.hallGold);
}

// the sanctuary: two 16-unit tiers (walkable, tinted on purpose), the pad on
// top, and the reredos closing the axis on the north wall — brass field (the
// dark foil the gold reads against), gold frame 8 proud, ruby stone 16 proud,
// gold crest and a ruby monde. Everything stays under the cornice (+512).
cbox('crown hall sanctuary tier 1', -SANC_X1, SANC_X1, SANC_Y1, HN - HWALL, TOP2, TOP2 + 16, MAT.hallStep);
cbox('crown hall sanctuary tier 2', -SANC_X2, SANC_X2, SANC_Y1 + 40, HN - HWALL, TOP2 + 16, TOP2 + 32, MAT.hallStep);
cbox('extraction pad', -EXFIL_HALF, EXFIL_HALF, EXFIL_Y - EXFIL_HALF, EXFIL_Y + EXFIL_HALF, TOP2 + 32, TOP2 + PAD_TOP, MAT.exfilPad);
const RER_Y2 = HN - HWALL, RER_Y1 = RER_Y2 - 32;
cbox('crown hall reredos field', -SANC_X2, SANC_X2, RER_Y1, RER_Y2, TOP2 + 32, TOP2 + 352, MAT.hallBrass);
cbox('crown hall reredos jamb W', -SANC_X2, -SANC_X2 + 24, RER_Y1 - 8, RER_Y1, TOP2 + 32, TOP2 + 352, MAT.hallGold);
cbox('crown hall reredos jamb E', SANC_X2 - 24, SANC_X2, RER_Y1 - 8, RER_Y1, TOP2 + 32, TOP2 + 352, MAT.hallGold);
cbox('crown hall reredos sill', -SANC_X2 + 24, SANC_X2 - 24, RER_Y1 - 8, RER_Y1, TOP2 + 32, TOP2 + 56, MAT.hallGold);
cbox('crown hall reredos head', -SANC_X2 + 24, SANC_X2 - 24, RER_Y1 - 8, RER_Y1, TOP2 + 328, TOP2 + 352, MAT.hallGold);
cbox('crown hall reredos stone', -64, 64, RER_Y1 - 16, RER_Y1, TOP2 + 112, TOP2 + 272, MAT.jewelRuby);
cbox('crown hall reredos crest', -128, 128, RER_Y1, RER_Y2, TOP2 + 352, TOP2 + 416, MAT.hallGold);
// 72 tall, NOT 40: jewelRuby is a tinted_edge material, and the geometry lint
// classes any tinted brush <= 64 thick as a DECK — a 40-tall monde read as a
// walkable floor at +456 with six unguarded edges. Taller than MAX_SLAB it is
// a solid again. Top +488, still under the cornice (+512).
cbox('crown hall reredos monde', -32, 32, RER_Y1 + 8, RER_Y2, TOP2 + 416, TOP2 + 488, MAT.jewelRuby);

// Upper wall arcades carry the interior's architectural scale. Recessed dark
// bays framed by gold ribs; all begin above +288, clear of vendors and players.
for(const sx of [-1,1]) {
  const x=sx*(WALL_IN-5);
  for(const py of [HYC-480,HYC+480]) {
    cbox(`crown hall upper panel ${sx} ${py}`,Math.min(x,x+sx*4),Math.max(x,x+sx*4),py-144,py+144,TOP2+288,TOP2+480,MAT.hallBrass);
    for(const sy of [-1,1]) {
      const y=py+sy*144;
      // The end bays meet solid corner piers. Trim inside those piers is
      // completely buried; keep only the exposed inner jamb of each bay.
      if(y-10<HS+CTOWER || y+10>HN-CTOWER)continue;
      cbox(`crown hall shrine frame pilaster ${sx} ${py} ${sy}`,
        sx<0?-WALL_IN:WALL_IN-12,sx<0?-WALL_IN+12:WALL_IN,
        y-10,y+10,TOP2+288,TOP2+480,MAT.hallGold);
    }
  }
}

// the floor: a processional carpet in the map's own wayfinding language (the
// lounges' spokes, the plaza's traces) — two nave seams, a threshold bar at
// the gate end, a bar at the sanctuary foot, a rim round the dais, a transept
// seam to each shrine (split where it crosses a nave seam) and a spoke to the
// crate (after CRATE_ORG below).
cbox('crown hall seam nave W', -SEAM_X - SEAM_W / 2, -SEAM_X + SEAM_W / 2, HS + HWALL + 104, SANC_Y1 - 24, ZS1, ZS2, MAT.crownRing);
cbox('crown hall seam nave E', SEAM_X - SEAM_W / 2, SEAM_X + SEAM_W / 2, HS + HWALL + 104, SANC_Y1 - 24, ZS1, ZS2, MAT.crownRing);
cbox('crown hall seam threshold', -SEAM_X - SEAM_W / 2, SEAM_X + SEAM_W / 2, HS + HWALL + 80, HS + HWALL + 104, ZS1, ZS2, MAT.crownRing);
cbox('crown hall seam sanctuary foot', -SEAM_X - SEAM_W / 2, SEAM_X + SEAM_W / 2, SANC_Y1 - 24, SANC_Y1, ZS1, ZS2, MAT.crownRing);
cbox('crown hall dais rim S', -160, 160, HYC - 160, HYC - 136, ZS1, ZS2, MAT.crownRing);
cbox('crown hall dais rim N', -160, 160, HYC + 136, HYC + 160, ZS1, ZS2, MAT.crownRing);
cbox('crown hall dais rim W', -160, -136, HYC - 136, HYC + 136, ZS1, ZS2, MAT.crownRing);
cbox('crown hall dais rim E', 136, 160, HYC - 136, HYC + 136, ZS1, ZS2, MAT.crownRing);
cbox('crown hall seam transept W1', -(SEAM_X - SEAM_W / 2), -160, HYC - SEAM_W / 2, HYC + SEAM_W / 2, ZS1, ZS2, MAT.crownRing);
cbox('crown hall seam transept W2', -600, -(SEAM_X + SEAM_W / 2), HYC - SEAM_W / 2, HYC + SEAM_W / 2, ZS1, ZS2, MAT.crownRing);
cbox('crown hall seam transept E1', 160, SEAM_X - SEAM_W / 2, HYC - SEAM_W / 2, HYC + SEAM_W / 2, ZS1, ZS2, MAT.crownRing);
cbox('crown hall seam transept E2', SEAM_X + SEAM_W / 2, 600, HYC - SEAM_W / 2, HYC + SEAM_W / 2, ZS1, ZS2, MAT.crownRing);

// THE HALL AMMO CRATE (v12, user 2026-08-26: "we need an ammo crate in that
// room"). Same two-sided contract as the four breather crates: the MODEL and
// its use-trigger are script-spawned by _tod_ammo_crate.gsc (which reads the
// origin from GENERATED _tod_crown_data.gsc — see crown_crate_org() at the
// bottom of this file, the door-data no-drift pattern), and the generator
// contributes ONLY this invisible collision clip, because the xmodel ships
// with no collision at all (the whole story: the breather crate block in
// section 4). Position: EAST wall, mirroring the upgrade station on the west
// wall — measured clear of the wall inner face (728: model bbox reaches
// ~717.8, 10u standoff), the sconce column above (z-gap ~137), the exfil
// trigger, the gather ring, the hall risers AND the east glowing ring inlay
// (inlay E ends at x=632; the model bbox starts at ~634.5 — the review caught
// the first cut at 672 nicking the glow strip by 1.5u). CRATE_YAW_W = facing
// west, into the hall (the mirrored box runs y 8263..8327 — still clear of the
// wall panel and the seam spoke, both of which are decoration on the wall).
// Bounds are the breather crate's measured yaw-270 occupancy translated to
// (672, 8308) with the same 4u inset; under CM=-1 the point-mirror of this box
// equals the 180-degree-rotated crate exactly, so clip and model stay welded at
// either parity. v17.37: box AND yaw now come from crateBox()/CRATE_YAW_W, so
// the 26u mesh offset can no longer be left behind by a facing change. THE LABEL MUST END "ammo crate body" —
// lint_tod_geometry's MODEL_CLIP_COLUMNS whitelist matches on it.
const CRATE_ORG = [676, 8308];
const CRATE_YAW = CRATE_YAW_W;   // v17.37: was 270 — see the crate convention
// docs/160 CROWN_CLEAN (user: "similar to Moon ... clean out the crown so
// there's no ammo crates or anything"): no crate, so no clip, no bay panel,
// no spoke. _tod_ammo_crate no longer places the model either; the anchor
// below is still emitted for the climb layout.
// THE ALARM BUTTON (user 2026-09-28: "replace [the alarm switch] with a red button on top of a stand in the
// centre of the crown"): the Blender-authored stand (tools/alarm_button) is a script_model with no collision of its
// own, so this clip stands in for it, the crate's way. Centre of the uplink dais; +-10 inside the 12-radius base
// plate, up to the console top (37). THE LABEL MUST END "alarm button stand body" (lint_tod_geometry
// MODEL_CLIP_COLUMNS). LOCKSTEP: tools/alarm_button/01_author.py STAND_R / CONSOLE_Z.
const ABTN_HALF = 10, ABTN_H = 37;
cbox('crown hall alarm button stand body', -ABTN_HALF, ABTN_HALF, HYC - ABTN_HALF, HYC + ABTN_HALF, TOP2 + DAIS_H, TOP2 + DAIS_H + ABTN_H, MAT.clip);
if (!CROWN_CLEAN) {
  const cb = crateBox(CRATE_ORG[0], CRATE_ORG[1], CRATE_YAW);
  cbox('crown hall ammo crate body', cb.x1, cb.x2, cb.y1, cb.y2, TOP2, TOP2 + CRATE_BOX_H, MAT.clip);
  // v16.35: the crate's bay in the basilica — a low glow panel on the wall
  // behind it (below the sconce row at +200) and the carpet spoke from the east
  // nave seam to its approach. Both clear the clip body above (panel x 724..728
  // vs body to 714; spoke ends at x 600 vs body from 639).
  cbox('crown hall crate panel', WALL_IN - 4, WALL_IN, CRATE_ORG[1] - 32, CRATE_ORG[1] + 32, TOP2 + 24, TOP2 + 120, MAT.crownGoldSeam);
  cbox('crown hall seam crate spoke', SEAM_X + SEAM_W / 2, 600, CRATE_ORG[1] - SEAM_W / 2, CRATE_ORG[1] + SEAM_W / 2, ZS1, ZS2, MAT.crownRing);
}

// --- 5d'. THE ALARM (docs/crown_alarm, user 2026-09-26) ----------------------
// The gantry and pendant support the central Blender-authored rotating beacon.
// Its inverted housing hangs 456..504 above the floor, clear of the +260 hall
// lights. Twelve more fixtures stand on the hall piers, sixteen on the crown
// point stones and one at the apex. Mount transforms are generated below.
// _tod_crown_alarm owns the physical rotors and red spotlights; the original
// alarm_org remains the siren anchor. The old cube and orbit hosts are gone.
// GOLD, not brass: crownBrass is an `_tinted` hue, which lint_tod_geometry classes
// as DECK, and a deck-class brush under MAX_SLAB (64) thick reads as a FLOOR —
// the 24-thick beam scored 158 unguarded edges and 152 unreachable nodes on
// the peer's first lint (2026-09-24). Plain hues are BLOCK to the lint.
const ALARM_GANTRY_W = 24, ALARM_GANTRY_H = 24;
const ALARM_GANTRY_Z2 = WZ2 - 8, ALARM_GANTRY_Z1 = ALARM_GANTRY_Z2 - ALARM_GANTRY_H;   // +544..+568
const ALARM_PEND_Z1   = ALARM_GANTRY_Z1 - 40;                                          // +504..+544
const ALARM_CORE      = 24;                                                            // half-size: a 48 cube
const ALARM_CORE_Z1   = ALARM_PEND_Z1 - 2 * ALARM_CORE, ALARM_CORE_Z2 = ALARM_PEND_Z1; // +456..+504
const ALARM_ORG       = [0, HYC, (ALARM_CORE_Z1 + ALARM_CORE_Z2) / 2];                 // the hosts' pivot (odd frame)
if (ALARM_CORE_Z1 <= TOP2 + 260) throw new Error('alarm core reaches the hall lights (+260) — raise it');
cbox('crown hall alarm gantry',  -WALL_IN, WALL_IN, HYC - ALARM_GANTRY_W / 2, HYC + ALARM_GANTRY_W / 2, ALARM_GANTRY_Z1, ALARM_GANTRY_Z2, MAT.hallGold);
cbox('crown hall alarm pendant', -8, 8, HYC - 8, HYC + 8, ALARM_PEND_Z1, ALARM_GANTRY_Z1, MAT.hallGold);
// The old cube and floating orbit lights are replaced by an inverted,
// Blender-authored physical beacon mounted to the pendant's bottom face.
// The original alarm_org remains the siren anchor. Mounts are emitted below.

// --- 5e. THE MAST: the tower's own spire on the core top (axis-symmetric) ----
{
  let z = TOP2;
  const MAST_MATS = [MAT.crownBand, MAT.crownBand, MAT.roofPara, MAT.crownFascia, MAT.crownFascia];
  MAST_TIERS.forEach(([w, h], i) => {
    addBox(`mast tier ${i + 1}`, -w / 2, w / 2, -w / 2, w / 2, z, z + h, MAST_MATS[i]);
    z += h;
  });
  // THE TOWER WEARS A SMALL CROWN (v11). Eight points around the mast's
  // shoulder, standing on tier 1's rim at TOP2+320 — which is 320 above the
  // core top, so nothing can be walked on or blocked. This is the one piece of
  // the composition that sits directly over the base-arena player's head, and
  // it is what makes the whole thing legible in a sentence: the tower wears a
  // small crown, and the citadel IS the crown. The red beacon at mast_tip_org()
  // is untouched — MAST_TOP must not move, _tod_finale.gsc puts a prop there.
  const MP = [[192, 0], [-192, 0], [0, 192], [0, -192], [136, 136], [-136, 136], [136, -136], [-136, -136]];
  MP.forEach(([px, py], i) => {
    addBox(`mast crown point ${i + 1} shaft`, px - 48, px + 48, py - 48, py + 48, TOP2 + 320, TOP2 + 704, MAT.crownGold);
    addBox(`mast crown point ${i + 1} head`, px - 88, px + 88, py - 88, py + 88, TOP2 + 704, TOP2 + 832, MAT.crownGold);
    addBox(`mast crown point ${i + 1} pip`, px - 32, px + 32, py - 32, py + 32, TOP2 + 832, TOP2 + 928, MAT.jewelRuby);
  });
}

// ---------------------------------------------------------------------------
// 5f. THE CIRCLET (v11) — the crown itself
// ---------------------------------------------------------------------------
// See the CIRCLET block up in the constants for WHY every number is what it is
// (the 384-unit legibility floor, the south-only occlusion, the underside being
// 60% of the pixels, and why light entities cannot help up here).
//
// True convex crown surfaces are decoded from their emitted planes by the
// preview, geometry lint, area meter and hidden-face audit (2026-09-15).
// Keep the gameplay floor and the causeway joins on their original grid.
// Decorative bevels carve inward; the road/sky asserts retain full envelopes.
//
// LINT CONTRACT for everything below (lint_tod_geometry.js):
//   * label everything `crown ...` — labels starting with `causeway`/`terrace`
//     land in the ROAD detachment bucket, which is gated at zero.
//   * plain colours are BLOCK and can never become floor at any size;
//     `_tinted`/`_tinted_edge` are DECK and become FLOOR at <= 64 thick in Z.
//   * the 20x20 column at (x in [0,20), y in [7840,7860)) is the lint's ONLY
//     working citadel reachability anchor (its fallback at y=9360 is already
//     blocked by `crown wall N`). Nothing may be put there above TOP2+18.
// ---------------------------------------------------------------------------

// One octagonal ring course, split into eight convex wall sectors. Band
// courses flare continuously from the previous course's top width. The south
// sector splits around the existing approach opening at its original height.
function crownCourse(tag, hx, hy, t, z1, z2, mat, mouthHalf) {
  const taper=/^crown band C/.test(tag)?CS(64):0;
  function sections(z,shrink) {
    const outer=crownOct(hx-shrink,hy-shrink,z,CR_CHAM);
    const inner=crownOct(hx-shrink-t,hy-shrink-t,z,CR_CHAM-t*(2-Math.SQRT2));
    return {outer,inner};
  }
  const lo=sections(z1,taper),hi=sections(z2,0);
  for(let i=0;i<8;i++) {
    const j=(i+1)%8;
    const face=r=>[r.outer[i],r.outer[j],r.inner[j],r.inner[i]];
    if(i===0 && mouthHalf) {
      for(const sign of [-1,1]) {
        const half=r=>{
          const f=face(r);
          if(sign<0){f[1]=[-mouthHalf,f[1][1],f[1][2]];f[2]=[-mouthHalf,f[2][1],f[2][2]];}
          else {f[0]=[mouthHalf,f[0][1],f[0][2]];f[3]=[mouthHalf,f[3][1],f[3][2]];}
          return f;
        };
        crownLoft(`${tag} face S ${sign<0?'west':'east'}`,half(lo),half(hi),mat);
      }
    } else crownLoft(`${tag} face ${i}`,face(lo),face(hi),mat);
  }
}

// cfleuron — cspike's opposite number. cspike can only make a NARROWING stack,
// and a shape that narrows to a point is a spire; spires are the single most
// castle-shaped thing in architecture and they are why the old crown read the
// way it did. A crown point is the other way round: a thin shaft carrying a
// head that is WIDER than the shaft. A cross pattee is literally named for its
// widening arms. Tier = [widthAlongFan, widthAcross, height, material].
function cfleuron(label, cx, cy, z0, tiers, fan) {
  let z = z0;
  let previous=null;
  tiers.forEach(([wf, wc, h, mat], i) => {
    const hx = (fan === 'x' ? wf : wc) / 2, hy = (fan === 'x' ? wc : wf) / 2;
    // Broad crown heads flare out from their shafts, then close through an
    // angled shoulder. No square shelf at the head/cap transition.
    const lower=(i===3 || i===4)?previous:[hx,hy];
    const ring=(a,b,z)=>{
      const bevel=Math.min(a,b)*0.24;
      return [[-a+bevel,-b],[a-bevel,-b],[a,-b+bevel],[a,b-bevel],[a-bevel,b],[-a+bevel,b],[-a,b-bevel],[-a,-b+bevel]].map(([x,y])=>[cx+x,cy+y,z]);
    };
    crownLoft(`${label} ${i+1}`,ring(...lower,z),ring(hx,hy,z+h),mat);
    previous=[hx,hy];
    z += h;
  });
  return z;
}

// --- 5f.1 the assertions that keep the circlet inside the world -------------
{
  // THE ROAD MUST SURVIVE. CR_HY is 1632 and not 1728 or 2048 for exactly one
  // reason: the south band has to land inside the causeway's F APPROACH, the
  // one stretch that is flat, on-axis, 160 wide and at TOP2. Anywhere else and
  // the ring would have to be pierced by three separate mouths through a fork
  // that is on stairs at three different heights.
  const y0 = CR_CY - CR_HY - CR_ERM, y1 = CR_CY - CR_HY + BAND_T;
  if (y0 <= cwY[8] || y1 >= cwY[9] - 160)
    throw new Error(`crown ring south band [${y0},${y1}] must lie inside the causeway F approach ` +
      `[${cwY[8]},${cwY[9] - 160}] — CR_HY ${CR_HY} puts it over a fork`);
  if (CR_MOUTH_HALF < CW_HALF + PARA + 40)
    throw new Error(`crown mouth half ${CR_MOUTH_HALF} would foul the road rails at ${CW_HALF + PARA}`);
  if (CR_MOUTH_Z2 - CR_MOUTH_Z1 < GATE_H)
    throw new Error('crown mouth is lower than the hall gate it leads to');
  // The ring must never touch the hall it surrounds — the user's constraint was
  // "We dont need to edit the floor of the room or space", and this is what
  // enforces it rather than hoping.
  if (CR_HX - BAND_T <= HW + 64)
    throw new Error(`crown ring inner face x ${CR_HX - BAND_T} does not clear the hall wall at ${HW}`);
  if (CR_CY - CR_HY + BAND_T >= HS - 64 || CR_CY + CR_HY - BAND_T <= HN + 64)
    throw new Error('crown ring inner face does not clear the hall in y');
  // The arches are scenery, not a ceiling.
  if (CR_TALL_TOP < HWALL_H + 1024)
    throw new Error('crown arches must clear the hall wall tops by 1024');
  // (The SEAL asserts live at the END of 5f — they measure the crown's real
  // bounding box, which does not exist yet at this point in the file.)
}

// --- 5f.2 the skirt: the surface the whole map actually looks at ------------
// The former stacked skirt is retired. The bell below uses continuous
// octagonal lofts and follows the existing crown envelope and pendant axis.
// SIGN-SYMMETRIC 16-SNAP for ornament-row u positions (the bell, and the
// ermine underside row in 5f.10). Math.round() rounds -53.5 to -53 but +53.5
// to +54, so a mirror-symmetric formula produced mirror-ASYMMETRIC positions —
// and the jewel pick keys on |u|/16, so the v12 first cut drew emerald west
// against ruby east on the one crown in the world that must be symmetric
// (adversarial review 2026-08-26).
const snapU = (x) => Math.sign(x) * Math.round(Math.abs(x) / 16) * 16;
// THE PENDILIA OWN THE STRAND LINES. The south cords (5f.8) hang at
// u = 0, +-3PT_X/8, +-3PT_X/4 (0 / 1014 / 2028 at CR_SCALE 1.4) and drop as
// far as z -1824 rel TOP2 — straight through the z-band of the tier-0 teeth,
// the tier-1 studs and the ermine underside row. The v12 first cut centred
// all three rows on u=0 and the centre cord passed clean through the centre
// ornament of each (review, same day). So every rim-height ornament row on
// the south face sits at the MIDPOINTS BETWEEN the strands instead:
// 3PT_X/16 and 9PT_X/16, which CS(368)/CS(1088) approximate within 8 units
// at any scale. Deeper tiers (2+) are below the longest cord and keep their
// own pitch. Four positions, symmetric by construction.
const SAFE_U = [-CS(1088), -CS(368), CS(368), CS(1088)];

{
  // THE RIBBED BELL — broad panels and eight structural ribs carry the
  // silhouette from below; brass reveals separate the panels at three levels.
  // An octagonal bell with continuous sloping faces. Three broad brass
  // reveals articulate its height without repeating a staircase silhouette.
  const profiles=[
    [1.00,CR_ERM_Z1],[0.94,CS(-960)],[0.80,CS(-1510)],
    [0.58,CS(-2080)],[0.34,CS(-2530)],[0.19,CR_SKIRT_BOT]
  ];
  const hx=CR_HX-CR_ERM,hy=CR_HY-CR_ERM;
  for(let i=0;i<profiles.length-1;i++) {
    const [fa,za]=profiles[i],[fb,zb]=profiles[i+1];
    crownLoft(`crown skirt swept shell ${i+1}`,
      crownOct(hx*fb,hy*fb,TOP2+zb,Math.min(hx,hy)*0.30*fb),
      crownOct(hx*fa,hy*fa,TOP2+za,Math.min(hx,hy)*0.30*fa),MAT.crownGoldPanel);
    // Eight substantial ribs follow the actual sloping surface and stay
    // attached at every joint. Bright edges remain legible against gold panels.
    const ra=crownOct(hx*fa,hy*fa,TOP2+za,Math.min(hx,hy)*0.30*fa);
    const rb=crownOct(hx*fb,hy*fb,TOP2+zb,Math.min(hx,hy)*0.30*fb);
    for(let k=0;k<8;k++) {
      const w=CS(44);
      const ring=p=>[[-w,-w],[w,-w],[w,w],[-w,w]].map(([x,y])=>[p[0]+x,p[1]+y,p[2]]);
      crownLoft(`crown skirt rib ${i+1}-${k}`,ring(rb[k]),ring(ra[k]),MAT.crownGold);
    }
    if(i>0 && i<4) crownLoft(`crown skirt reveal ${i}`,
      crownOct(hx*fa+CS(24),hy*fa+CS(24),TOP2+za-CS(32),Math.min(hx,hy)*0.30*fa),
      crownOct(hx*fa+CS(24),hy*fa+CS(24),TOP2+za+CS(32),Math.min(hx,hy)*0.30*fa),MAT.crownBrass);
  }

  // --- THE GIRANDOLE — the drop pendant --------------------------------------
  // The v11 core was a 544-square ruby cube: the natural focal point of the
  // entire climb, delivered at 1.4 degrees. It is now a proper chandelier
  // drop — collar, chain, a stepped ruby ORB (the monde trick, inverted),
  // a flaring gold coronet and a ruby drop-stone — hanging BELOW the bell's
  // throat, and it completes the crown's red vertical axis: beacon above,
  // great ruby front, girandole below. Every stage is WIDER than the stage
  // above where it matters (orb over chain, coronet over orb-foot, stone over
  // pip) — the pendilia rule, at architectural size. One light entity makes
  // the orb bloom the way the great ruby does; it is the third and LAST red
  // light the crown gets (the CL block counts all three) — the girandole
  // exists to be the climb's magnet, and the axis is complete at three.
  {
    const G = [
      // [half, height, material]  top -> tip
      [CS(184), CS(72), MAT.crownGold],     // collar, tucked under tier 10's floor
      [CS(104), CS(128), MAT.crownGold],    // the chain
      [CS(208), CS(112), MAT.jewelRuby],    // orb shoulder
      [CS(264), CS(240), MAT.jewelRuby],    // orb equator — the widest stage
      [CS(208), CS(112), MAT.jewelRuby],    // orb foot
      [CS(256), CS(64), MAT.crownGold],     // coronet — flares back OUT under the orb
      [CS(96), CS(88), MAT.crownGold],      // pip
      [CS(136), CS(112), MAT.jewelRuby],    // the drop stone — wider than its pip
    ];
    let z = TOP2 + CR_SKIRT_BOT;
    G.forEach(([h, hh, mat], i) => {
      cbox(`crown girandole ${i + 1}`, -h, h, CR_CY - h, CR_CY + h, z - hh, z, mat);
      z -= hh;
    });
  }
}

// --- 5f.3 the band: ermine rim, four flaring courses, the pearl rim ---------
// The FLARE is the move that stops this being a curtain wall. Band courses step
// OUTWARD going up — 1856 -> 1920 -> 1984 -> 2048, which is 192 of batter over
// 1216 of height, about 9 degrees — and the ermine below them is proud of even
// the topmost course. That gives the correct crown profile: a fur roll at the
// very bottom that is the widest line in the whole silhouette, a nipped waist
// above it, then a splay to the band's top edge. Plumb walls make castles.
crownCourse('crown ermine', CR_HX + CR_ERM, CR_HY + CR_ERM, BAND_T + CR_ERM,
  TOP2 + CR_ERM_Z1, TOP2 + CR_ERM_Z2, MAT.crownErmine);
// THE FOUR COURSES CLIMB THE VALUE LADDER, they do not just step outward.
// All four used to be crownGoldPanel, which meant the flare — the move the whole
// silhouette rests on — was invisible on any face: one material, one value, one
// plate. Every material in this pack is lit_emissive (self-lit), so a step in
// geometry produces NO shading difference on its own. Value has to be authored.
// Brass at the bottom against the white ermine, gold panel through the middle,
// bright plain gold at the top under the rim, so the band reads dark-to-light as
// it splays. The measured ladder is orange_tinted 5.8 / yellow_tinted 7.8 /
// yellow 13.5, which is a 2.3:1 spread across the band.
crownCourse('crown band C1', CR_HX - CS(192), CR_HY - CS(192), BAND_T,
  TOP2 + CR_ERM_Z2, TOP2 + CR_C1_Z, MAT.crownBrass);
crownCourse('crown band C2', CR_HX - CS(128), CR_HY - CS(128), BAND_T,
  TOP2 + CR_C1_Z, TOP2 + CR_C2_Z, MAT.crownGoldPanel, CR_MOUTH_HALF);
crownCourse('crown band C3', CR_HX - CS(64), CR_HY - CS(64), BAND_T,
  TOP2 + CR_C2_Z, TOP2 + CR_C3_Z, MAT.crownGoldPanel, CR_MOUTH_HALF);
crownCourse('crown band C4', CR_HX, CR_HY, BAND_T,
  TOP2 + CR_C3_Z, TOP2 + CR_C4_Z, MAT.crownGold);
// the pearl rim: thin, so it MUST be a plain colour (see the material rule)
crownCourse('crown rim', CR_HX + CS(48), CR_HY + CS(48), BAND_T + CS(48),
  TOP2 + CR_C4_Z, TOP2 + CR_RIM_Z, MAT.crownGold);
// TWO PROUD ASTRAGALS. A band this tall with nothing but jewels on it is a wall
// with jewels on it. These are the horizontal divisions every real circlet has,
// and they are the reason the flare reads as three distinct courses instead of
// one leaning surface. Under MAX_SLAB thick, so both MUST be a plain colour.
crownCourse('crown astragal lower', CR_HX - CS(96), CR_HY - CS(96), BAND_T + CS(48),
  TOP2 + CR_C1_Z - CS(32), TOP2 + CR_C1_Z + CS(48), MAT.crownGold, CR_MOUTH_HALF);
crownCourse('crown astragal upper', CR_HX + CS(16), CR_HY + CS(16), BAND_T + CS(48),
  TOP2 + CR_C3_Z - CS(32), TOP2 + CR_C3_Z + CS(32), MAT.crownGold);
// THE MOUTH'S JAMBS — and they were completely buried until 2026-08-25.
// Measured: the jamb (x 448..576, y 6912..7216) sat entirely INSIDE the
// frontispiece side panel (x 448..944, y 6912..7136), with their south faces on
// the SAME PLANE. So the element the design record credits with "turning a hole
// in the rim into a gate" was invisible, and where it was not invisible it was
// coplanar with a different material — a z-fight waiting for a driver to break
// the tie. The gate's edge had literally zero geometric relief; it was a change
// of material on a flat wall.
// They now stand CS(240) proud of the band and are wide enough to read, so the
// opening has a genuine 336-unit reveal. The frontispiece is pushed back behind
// them (see 5f.7) so no two faces share a plane.
// MP1 vs MP_DEEP — AND THIS DISTINCTION IS A ROAD SAFETY RULE, NOT A STYLE ONE.
// The first cut of the proud jamb used a single MP1 = CR_CY-CR_HY-CS(240) =
// 6672 for the whole family. The causeway's J4 LANDING is 960 wide (x +-480)
// and runs y 6720..6880 at TOP2 — so that put four 176-tall solid gold blocks
// ON WALKABLE DECK, straight through the landing's north guard rail.
// `lint_tod_geometry` CANNOT SEE THAT: its misplaced-wall check only fires on a
// `clip` brush with no visible solid beside it, and a visible solid just drops
// the node from `stand` silently — while the flood still walks the middle of a
// 960-wide landing, so reachability stays green too.
//   MP1     = 6912, flush with the ermine line. Anything reaching DOWN to the
//             road deck uses this: it is north of the landing (6880) and north
//             of the rail that caps it (6900).
//   MP_DEEP = 6672, the full 336 reveal. ONLY for elements whose bottom is well
//             clear of head height over that landing — the cap and the corbels,
//             both of which live above TOP2+368. That is what corbelling IS:
//             the gate's head oversails the threshold, the threshold stays clear.
// Section 5f.9 now asserts this rather than trusting it.
const MJ = CS(160), MP1 = CR_CY - CR_HY - CS(64), MP_DEEP = CR_CY - CR_HY - CS(240);
const MP2 = CR_CY - CR_HY + CS(144);
for (const sx of [-1, 1]) {
  cbox(`crown mouth jamb ${sx > 0 ? 'E' : 'W'}`,
    sx > 0 ? CR_MOUTH_HALF : -CR_MOUTH_HALF - MJ, sx > 0 ? CR_MOUTH_HALF + MJ : -CR_MOUTH_HALF,
    MP1, MP2, TOP2, TOP2 + CR_C4_Z, MAT.crownGold);
  // corbels in the mouth's top corners. They narrow the OPENING at the head
  // only — the centre headroom the road needs is untouched, and they sit well
  // above the deck so they can never read as a blocker in a road column.
  cbox(`crown mouth corbel ${sx > 0 ? 'E' : 'W'}`,
    sx > 0 ? CR_MOUTH_HALF - MJ : -CR_MOUTH_HALF, sx > 0 ? CR_MOUTH_HALF : -CR_MOUTH_HALF + MJ,
    MP_DEEP, MP2, TOP2 + CR_MOUTH_Z2 - CS(128), TOP2 + CR_MOUTH_Z2, MAT.crownGold);
}
// THE KEYSTONE IS DELETED (v11.2). It sat at x +-176, y from 6896, z 19936-20182
// — entirely behind `crown cullinan bezel` (x +-536, y from 6832, z 19952-20400),
// which is 64 units IN FRONT of it and covers it in x and z but for a 16-unit
// sliver. It was ~93% buried: bake cost for nothing. The Cullinan and its bezel
// already are the centrepiece over the mouth, which is what a keystone is for.
// A STEPPED PEDIMENT over the mouth. Three courses corbelling inward above the
// lintel, so the gate has a head instead of stopping dead at a flat soffit.
// It sits between the Cullinan and the front cross and ties the three into one
// vertical event on the centreline — which is the whole composition's axis.
for (let k = 0; k < 3; k++)
  cbox(`crown mouth pediment ${k + 1}`, -(CS(512) - k * CS(128)), CS(512) - k * CS(128),
    CR_CY - CR_HY - CS(32) - k * 16, CR_CY - CR_HY + CS(96),
    TOP2 + CR_C4_Z + k * CS(96), TOP2 + CR_C4_Z + (k + 1) * CS(96), MAT.crownGoldPanel);
// THE MOUTH'S LINING. The road runs the full band thickness through solid gold
// here, and without this the tunnel is the same flat gold as everything else.
// The glowing seam material turns it into a lit threshold you walk through —
// the one piece of the crown every player is guaranteed to see from arm's length.
{
  const y1 = CR_CY - CR_HY - CS(32), y2 = CR_CY - CR_HY + BAND_T + CS(96), LT = CS(24);
  for (const sx of [-1, 1])
    cbox(`crown mouth lining ${sx > 0 ? 'E' : 'W'}`,
      sx > 0 ? CR_MOUTH_HALF - LT : -CR_MOUTH_HALF, sx > 0 ? CR_MOUTH_HALF : -CR_MOUTH_HALF + LT,
      y1, y2, TOP2 + CR_MOUTH_Z1, TOP2 + CR_MOUTH_Z2, MAT.crownGoldSeam);
  // THICKER THAN MAX_SLAB, NOT 24, and that is a lint constraint rather than a
  // look: the glowing-seam family is DECK, and a DECK brush 64 thick or less
  // becomes a walkable floor surface — this one would be a floor node hanging
  // over the causeway with no guard on any edge. Over MAX_SLAB it is a wall.
  cbox('crown mouth soffit', -CR_MOUTH_HALF, CR_MOUTH_HALF, y1, y2,
    TOP2 + CR_MOUTH_Z2 - CS(80), TOP2 + CR_MOUTH_Z2, MAT.crownGoldSeam);
}

// --- 5f.4 the sixteen points ------------------------------------------------
// 8 tall crosses pattee alternating with 8 short fleurs-de-lis, sitting on the
// ring's wall centreline. Across the SOUTH FACE — the only face anybody ever
// sees from the tower — that reads, left to right:
//     TALL corner   short   FRONT CROSS   short   TALL corner
// Five teeth, alternating, with a dominant centre. That is a crown and nothing
// else. Above the rim strip there is NOTHING but points and sky: if the mass
// carried on up between the teeth they would read as buttresses.
const PT_X = CR_HX - BAND_T / 2, PT_Y = CR_HY - BAND_T / 2;
const PT_CX = CR_HX - CR_CHAM / 2 - CS(112), PT_CY = CR_HY - CR_CHAM / 2 - CS(112);  // on the chamfer's centreline
const PZ = TOP2 + CR_RIM_Z;
// [widthAlongFan, widthAcross, height, material] — note every head is WIDER
// than the shaft that carries it.
// The hierarchy is deliberate and survives any CR_SCALE: a tall head must beat
// a fleur head must beat the sky gap between them, or the rhythm across the
// face stops reading as alternating. At CR_SCALE 1.4 those are 896 / 784 /
// ~560 units — 2.3, 2.0 and 1.45 degrees from the base arena.
// THE PIP WAS A SPIRE AND IT SHIPPED THAT WAY. Measured on the generated .map,
// a tall point ran 400 -> 896 -> 496 -> 208 -> 320: a 4.3:1 collapse over 624
// units of height, which is exactly the cspike() silhouette this whole redesign
// was written to delete, rebuilt out of cfleuron(). Worse, 208 units subtends
// 0.54 degrees from the base arena — sitting right on the shimmer floor.
// The pip is now 400 (the width of the shaft it stands over) and the stone above
// it FLARES to 448, so the profile reads cap -> neck -> flaring stone. Nothing
// on this crown may narrow toward its own tip.
// The cap is BRASS, not gold panel: self-lit materials mean the head only reads
// as three parts if those parts are three different values.
// THE SHAFT IS BANDED, NOT ONE POST. A tall point's shaft is 1,888 units of
// dead rectangle, and from the terrace these are the dominant verticals in the
// frame. Because every material here is self-lit, a plain moulding ring on it
// would produce no value change at all — so the articulation IS a material
// change: gold / brass / gold, with the brass course slightly proud so it also
// breaks the outline. That replaces the old separate `collar` box, which was
// 40 units of relief in the same colour as the shaft and therefore invisible.
// The three heights must sum to TALL_SHAFT_H.
const TALL_SHAFT_H = CS(1344), TALL_HEAD_H = CS(384), TALL_CAP_H = CS(256), TALL_PIP_H = CS(192);
const SH_A = Math.round(TALL_SHAFT_H * 0.42 / 16) * 16;
const SH_B = TALL_SHAFT_H - 2 * SH_A;
const TALL_TIERS = [
  [CS(288), CS(352), SH_A, MAT.crownGold],
  [CS(320), CS(384), SH_B, MAT.crownBrass],
  [CS(288), CS(352), SH_A, MAT.crownGold],
  [CS(640), CS(512), TALL_HEAD_H, MAT.crownGold],
  [CS(352), CS(352), TALL_CAP_H, MAT.crownBrass],
  [CS(288), CS(288), TALL_PIP_H, MAT.crownGold]];
const CORNER_TIERS = [
  [CS(352), CS(352), SH_A, MAT.crownGold],
  [CS(384), CS(384), SH_B, MAT.crownBrass],
  [CS(352), CS(352), SH_A, MAT.crownGold],
  [CS(640), CS(640), TALL_HEAD_H, MAT.crownGold],
  [CS(352), CS(352), TALL_CAP_H, MAT.crownBrass],
  [CS(288), CS(288), TALL_PIP_H, MAT.crownGold]];
// Point positions are DERIVED from the ring, never written down: three per side
// at quarter-points of the wall centreline, plus one on each chamfer. A literal
// pitch would put the teeth in the wrong place the moment CR_SCALE moved, and
// the jewels and pendilia below take their bays from the same halves.
const PT_BX = PT_X / 2, PT_BY = PT_Y / 2;
const CR_POINTS = [
  [-PT_BX, CR_CY - PT_Y, 'short', 'x'], [0, CR_CY - PT_Y, 'front', 'x'], [PT_BX, CR_CY - PT_Y, 'short', 'x'],
  [-PT_BX, CR_CY + PT_Y, 'short', 'x'], [0, CR_CY + PT_Y, 'tall', 'x'], [PT_BX, CR_CY + PT_Y, 'short', 'x'],
  [-PT_X, CR_CY - PT_BY, 'short', 'y'], [-PT_X, CR_CY, 'tall', 'y'], [-PT_X, CR_CY + PT_BY, 'short', 'y'],
  [PT_X, CR_CY - PT_BY, 'short', 'y'], [PT_X, CR_CY, 'tall', 'y'], [PT_X, CR_CY + PT_BY, 'short', 'y'],
  [-PT_CX, CR_CY - PT_CY, 'corner', 'x'], [PT_CX, CR_CY - PT_CY, 'corner', 'x'],
  [-PT_CX, CR_CY + PT_CY, 'corner', 'x'], [PT_CX, CR_CY + PT_CY, 'corner', 'x'],
];
// The four corner point heads — where the finale's quarter-progress beacons
// live now that the hall's pylon plinths are gone. See pylon_orgs() at the
// bottom of this file. Standing on the cap under the pip, so it is derived from
// the tier heights and cannot drift when CR_SCALE moves.
const CROWN_BEACON_XY = CR_POINTS.filter(p => p[2] === 'corner').map(p => [p[0], p[1]]);
// ON TOP OF THE STONE, not on top of the cap. This used to stop at
// shaft+head+cap, which is the pip's BOTTOM face — so all four finale
// quarter-progress beacons were spawned inside the 400-wide pip brush and
// entombed, model and aura both. The point of moving them out of the hall was
// to be seen, so the whole tier stack has to be counted: shaft, head, cap, pip,
// AND the jewel stone that caps it, plus a little clearance so the prop's own
// bounds are clear of the stone's top face.
const CROWN_BEACON_Z = CR_RIM_Z + TALL_SHAFT_H + TALL_HEAD_H + TALL_CAP_H + TALL_PIP_H + CS(224) + 24;

// THE RIBS. One vertical buttress under each point, running the whole band from
// the ermine to the rim strip and standing proud of the topmost course. Without
// them the sixteen points are stuck onto a smooth wall like candles on a cake;
// with them the band reads as SUPPORTING the points, which is what the eye
// wants from any load-bearing arcade and what turns a hoop into a circlet.
// They also give the flare something to be measured against on the walk in.
// NOTE the two exclusions, both deliberate:
//   * the SOUTH MID rib is skipped — that is where the mouth is, and a rib
//     there would wall up the road. The Cullinan does that job on the lintel.
//   * corner ribs are square posts on the chamfer rather than face ribs; an
//     axis-aligned box cannot stand proud of a 45-degree face.
// THREE THINGS WERE WRONG WITH THE RIBS AND ALL THREE COST NOTHING TO FIX
// (measured off the generated .map, 2026-08-25):
//
// 1. THEY WERE NARROWER THAN THE POINTS THEY CARRY. A rib was 256 wide under a
//    384 fleur shaft and 416 under a 496 corner shaft, so every one of the
//    sixteen points overhung its own buttress by 40-64 a side. That does not
//    read as support, it reads as a mistake. A buttress must be at least as wide
//    as its load.
// 2. THEY BARELY PROTRUDED. Every articulating element on the band lived inside
//    a 96-unit slot on a 6128-wide elevation: ribs 80 proud, rim 64, upper
//    astragal 16. That is 1.6% of the width, which is why the band read as one
//    flat plate in every walk-up render.
//    THE FIX IS TO SPLIT `out` BY AXIS. Silhouette rule H — sky between and
//    behind the points — is about the X profile. A south or north rib protruding
//    in Y changes the silhouette not at all, because you are looking down that
//    axis. So S/N ribs now stand 320 proud and E/W ribs stay inside the ermine.
// 3. THEY WERE THE SAME GOLD AS EVERYTHING ELSE. Every material in this pack is
//    lit_emissive (self-lit) — geometry does NOT self-shadow here, so relief
//    only reads if it carries a MATERIAL CHANGE. Brass ribs are the dark foil
//    the design doc asks for and never delivered on the band. Legal despite
//    `orange_tinted` being DECK: the rib's Z extent is 1696, far over MAX_SLAB.
CR_POINTS.forEach(([px, py, kind, fan], i) => {
  const z1 = TOP2 + CR_ERM_Z2, z2 = TOP2 + CR_C4_Z, tag = `crown rib ${i + 1}`;
  if (kind === 'front') return;
  if (kind === 'corner') {
    // matches the 496-wide corner shaft above it
    cbox(tag, px - CS(176), px + CS(176), py - CS(176), py + CS(176), z1, z2, MAT.crownBrass);
    return;
  }
  const inset = CS(192);   // keys into C1. NOT +CS(32): that put the rib back face exactly on C4 inner (7328), brass against gold, coplanar - a z-fight on a surface the hold-out looks straight at.
  const out = (fan === 'x') ? CS(224) : CS(56);   // S/N stand proud; E/W stay in the ermine
  const w = CS(144);                         // 400 wide — wider than the 384 shaft it carries
  if (fan === 'x') {
    const s = py < CR_CY ? -1 : 1;      // south face or north face
    const f = CR_CY + s * (CR_HY + out), b = CR_CY + s * (CR_HY - inset);
    cbox(tag, px - w, px + w, Math.min(f, b), Math.max(f, b), z1, z2, MAT.crownBrass);
  } else {
    const s = px < 0 ? -1 : 1;          // west face or east face
    const f = s * (CR_HX + out), b = s * (CR_HX - inset);
    cbox(tag, Math.min(f, b), Math.max(f, b), py - w, py + w, z1, z2, MAT.crownBrass);
  }
});
CR_POINTS.forEach(([px, py, kind, fan], i) => {
  const tag = `crown point ${i + 1} ${kind}`;
  // (The separate `collar` box that used to sit here is gone. It was 40 units
  // proud in the SAME material as the shaft, and on self-lit geometry that is
  // no value change and no outline change — i.e. invisible from everywhere,
  // paid for in bake. The shaft's brass middle band in TALL_TIERS does the job
  // properly, because it changes material as well as width.)
  // Every tall point is finialled with a STONE, cycling the three jewel
  // colours. 224 is 0.58 deg from the base arena — over the shimmer threshold,
  // so the rim reads as gold teeth tipped with colour rather than gold teeth.
  // KEYED ON POSITION, NOT ON ARRAY INDEX. `i % 3` looked fine until you notice
  // CR_POINTS lists the four corners last, so indices 12 and 13 are the SW and
  // SE corners and got ruby and emerald — a visible asymmetry on the one face
  // anybody ever looks at. A key built from |x| and |y - CR_CY| is symmetric in
  // both axes by construction, so mirrored points always match.
  const JT = [MAT.jewelRuby, MAT.jewelEmerald, MAT.jewelSapphire][
    Math.round((Math.abs(px) + Math.abs(py - CR_CY)) / 16) % 3];
  if (kind === 'tall' || kind === 'corner') {
    const top = cfleuron(tag, px, py, PZ, kind === 'tall' ? TALL_TIERS : CORNER_TIERS, fan);
    cbox(`${tag} stone`, px - CS(160), px + CS(160), py - CS(160), py + CS(160), top, top + CS(224), JT);
  }
  else if (kind === 'short') {
    // FLEUR-DE-LIS. The transverse bar is the token that NAMES the shape — it
    // is what separates a fleur from three lumps on a stick — so it is the
    // widest thing here (448 = 1.16 deg = 34 px from the base arena).
    // `off` slides along the fan axis, `w` is the width across it: one helper
    // and the whole shape works on a north/south wall or an east/west one.
    const P = (t, off, w, across, z1, z2, mat) => {
      const dx = fan === 'x' ? off : 0, dy = fan === 'x' ? 0 : off;
      const hx = (fan === 'x' ? w : across) / 2, hy = (fan === 'x' ? across : w) / 2;
      cbox(`${tag} ${t}`, px + dx - hx, px + dx + hx, py + dy - hy, py + dy + hy, z1, z2, mat);
    };
    // THE CENTRE LOBE WAS NARROWER THAN ITS OWN SHAFT (336 against 384), which
    // breaks the one rule every point on this crown has to obey, and the tip was
    // 176 = 0.46 deg, under the legibility floor. Centre lobe now 448, tip 288.
    // Side lobes are GOLD PANEL rather than plain so the centre petal dominates:
    // with self-lit materials, three plain-gold lumps at the same value are
    // three lumps on a stick, which is precisely what a fleur must not be.
    P('shaft', 0, CS(272), CS(320), PZ, PZ + CS(832), MAT.crownGold);
    P('bar', 0, CS(512), CS(320), PZ + CS(736), PZ + CS(864), MAT.crownGold);
    P('lobe C', 0, CS(320), CS(240), PZ + CS(832), PZ + CS(1408), MAT.crownGold);
    P('lobe L', -CS(208), CS(176), CS(192), PZ + CS(832), PZ + CS(1184), MAT.crownGoldPanel);
    P('lobe R', CS(208), CS(176), CS(192), PZ + CS(832), PZ + CS(1184), MAT.crownGoldPanel);
    P('tip', 0, CS(208), CS(208), PZ + CS(1408), PZ + CS(1552), MAT.jewelSapphire);
  }
});

// --- 5f.5 THE FRONT CROSS ---------------------------------------------------
// Real crowns have a FRONT; forts are omnidirectional, and four identical faces
// is one of the reasons the old citadel read as a keep. This is the south mid
// point, 576 taller than its neighbours, standing on the NEAR rim — which means
// it is the one tall element in the whole composition that can never be
// occluded by the crown's own south band, from any height on the tower. It
// carries the great ruby, and it is what magnetises the base arena.
{
  const fy = CR_CY - PT_Y, S = 'crown front cross';
  cbox(`${S} shaft`, -CS(192), CS(192), fy - CS(208), fy + CS(208), PZ, PZ + CS(1600), MAT.crownGold);
  cbox(`${S} upper`, -CS(176), CS(176), fy - CS(176), fy + CS(176), PZ + CS(1600), PZ + CS(2496), MAT.crownGold);
  cbox(`${S} pip`, -CS(112), CS(112), fy - CS(112), fy + CS(112), PZ + CS(2496), PZ + CS(2752), MAT.jewelRuby);
  // the transverse arm — its TOP is also the south foot of the N-S arch, which
  // is heraldically right: the arches spring from the crosses pattee, and the
  // front cross carries on above the springing.
  cbox(`${S} arm`, -CS(512), CS(512), fy - CS(176), fy + CS(176), PZ + CS(1856), PZ + CS(2176), MAT.crownGold);
  for (const s of [-1, 1])
    cbox(`${S} arm flare ${s > 0 ? 'E' : 'W'}`, s > 0 ? CS(288) : -CS(512), s > 0 ? CS(512) : -CS(288),
      fy - CS(208), fy + CS(208), PZ + CS(1760), PZ + CS(2272), MAT.crownGold);
  // THE GREAT RUBY — 716 square at CR_SCALE 1.4, which is 1.86 deg and 55 px
  // from the floor of the base arena. One of only two crown elements that gets
  // a real light entity, because it is the thing that magnetises the street.
  // THE RUBY TAKES THE ARM'S OWN HEIGHT, not the flares'. It used to be 720 tall
  // like the arm-end flares while the arm between them is 448, so the south
  // elevation read [720][a 45-wide notch][720] and the FLARE — the entire reason
  // this element is called a cross pattee — never appeared. Now the profile is
  // centre 448, ends 720: arms visibly wider at their tips, which is the shape.
  cbox(`${S} ruby`, -CS(256), CS(256), fy - CS(288), fy - CS(208), PZ + CS(1856), PZ + CS(2176), MAT.jewelRuby);
  cbox(`${S} ruby bezel`, -CS(288), CS(288), fy - CS(272), fy - CS(208), PZ + CS(1824), PZ + CS(2208), MAT.crownGoldPanel);
}

// --- 5f.6 the arches, the monde, the finial, the beacon ---------------------
// A crown CONVERGES; a castle TERMINATES in a wall-walk. The closure is also a
// reveal staged across the whole climb: from the base the arches and monde are
// occluded by the near rim and contribute nothing, the monde clears at floor 7,
// the arch crowns at floor 18, and from the terrace they are the entire
// silhouette. From inside the hall during the hold-out they are a golden vault
// overhead, which is the single best thing the crown can give the ending.
const ARCH_SPRING = TOP2 + CR_TALL_TOP, ARCH_RISE = CR_ARCH_CROWN - CR_TALL_TOP;
const ARCH_N = 8, ARCH_HW = CS(176), ARCH_TH = CS(320);
// `skip` drops the first N segments. The N-S arch's SOUTH half springs off the
// front cross's arm, and the front cross's upper member is 480 deep and 1248
// tall right there — so segment 1 came out 90% inside it, paying full bake for a
// brush you cannot see. Only that half needs it: the north foot is a 400-wide
// pip and does not swallow anything.
function archHalf(tag, axis, from, to, skip = 0) {
  const count=24;
  for(let k=skip?1:0;k<count;k++) {
    const u=k/count,v=(k+1)/count;
    const a=from+(to-from)*u,b=from+(to-from)*v;
    const za=ARCH_SPRING+ARCH_RISE*Math.sin(Math.PI/2*u);
    const zb=ARCH_SPRING+ARCH_RISE*Math.sin(Math.PI/2*v);
    const ring=(p,z)=>axis==='y'
      ?[[-ARCH_HW,p,z-ARCH_TH],[ARCH_HW,p,z-ARCH_TH],[ARCH_HW,p,z],[-ARCH_HW,p,z]]
      :[[p,CR_CY-ARCH_HW,z-ARCH_TH],[p,CR_CY+ARCH_HW,z-ARCH_TH],[p,CR_CY+ARCH_HW,z],[p,CR_CY-ARCH_HW,z]];
    crownLoft(`${tag} swept ${k+1}`,ring(a,za),ring(b,zb),MAT.crownGold);
  }
}
// The arch ribbon must be thicker than its own worst step or it breaks into a
// dotted line. sin(90/8 deg) = 0.195 of the rise is the first and biggest step.
if (ARCH_RISE * Math.sin(Math.PI / 16) > ARCH_TH)
  throw new Error(`crown arch step ${Math.round(ARCH_RISE * Math.sin(Math.PI / 16))} exceeds the ${ARCH_TH} ribbon — the arch would gap`);
archHalf('crown arch NS south', 'y', CR_CY - PT_Y, CR_CY, 1);
archHalf('crown arch NS north', 'y', CR_CY + PT_Y, CR_CY);
archHalf('crown arch EW west', 'x', -PT_X, 0);
archHalf('crown arch EW east', 'x', PT_X, 0);
// PEARLS ON THE ARCHES (v12). Real crown arches carry a row of pearls — it is
// the single most recognisable piece of crown jewellery grammar after the
// ermine, and the arches were bare gold ribbons. Three ermine-white beads per
// half-arch, on segments 2/4/6: white (13.1) on gold (13.5) is nearly no VALUE
// step, so what these buy is the serrated OUTLINE against the sky — the one
// currency that always spends on self-lit materials. Segment 7 is skipped
// deliberately: the two arches CROSS at the crown, and beads from both would
// collide there. 176-square = 1.1 deg from the terrace, where the arches ARE
// the silhouette; from the base they are group texture on a line that already
// reads. Plain-colour white, so the lint can never call one a floor.
{
  const PB = CS(88), PH = CS(96);
  const pearls = (tag, axis, from, to, skip = 0) => {
    for (const k of [2, 4, 6]) {
      if (k < skip) continue;
      const u = Math.round(from + (to - from) * (k + 0.5) / ARCH_N);
      const top = Math.round(ARCH_SPRING + ARCH_RISE * Math.sin(Math.PI / 2 * (k + 1) / ARCH_N));
      crownOrb(`${tag} pearl ${k}`,axis==='y'?0:u,axis==='y'?u:CR_CY,top+PH/2,PB,PB,PH/2,MAT.crownErmine);
    }
  };
  pearls('crown arch NS south', 'y', CR_CY - PT_Y, CR_CY, 1);
  pearls('crown arch NS north', 'y', CR_CY + PT_Y, CR_CY);
  pearls('crown arch EW west', 'x', -PT_X, 0);
  pearls('crown arch EW east', 'x', PT_X, 0);
}
{
  // THE MONDE — eight stepped slabs on a circle, plus an equator fillet in
  // bright gold. Real mondes have exactly that band and it is what stops a
  // stepped sphere reading as a stack of boxes.
  // Slab height is DERIVED so the eight courses land exactly on CR_MONDE_Z2 at
  // any CR_SCALE — a literal 128 leaves a 32-unit step in the sphere at 1.4.
  crownOrb('crown monde',0,CR_CY,TOP2+(CR_ARCH_CROWN+CR_MONDE_Z2)/2,
    CS(504),CS(504),(CR_MONDE_Z2-CR_ARCH_CROWN)/2,MAT.crownGoldPanel);
  const ME = TOP2 + (CR_ARCH_CROWN + CR_MONDE_Z2) / 2, MEH = CS(544);
  cbox('crown monde equator', -MEH, MEH, CR_CY - MEH, CR_CY + MEH, ME - CS(48), ME + CS(48), MAT.crownGold);
  // THE FINIAL — a cross pattee, arms wider at the ends than at the crossing.
  // Its arms run on BOTH axes: from the terrace you read the E-W pair, from
  // directly below you read whichever presents area, and a cross that only
  // exists on one axis disappears from half the map.
  const F = 'crown finial';
  cbox(`${F} shaft`, -CS(128), CS(128), CR_CY - CS(128), CR_CY + CS(128), TOP2 + CR_MONDE_Z2, TOP2 + CS(5568), MAT.crownGold);
  cbox(`${F} arm EW`, -CS(384), CS(384), CR_CY - CS(112), CR_CY + CS(112), TOP2 + CS(5184), TOP2 + CS(5376), MAT.crownGold);
  cbox(`${F} arm NS`, -CS(112), CS(112), CR_CY - CS(384), CR_CY + CS(384), TOP2 + CS(5184), TOP2 + CS(5376), MAT.crownGold);
  for (const s of [-1, 1]) {
    cbox(`${F} arm flare ${s > 0 ? 'E' : 'W'}`, s > 0 ? CS(288) : -CS(384), s > 0 ? CS(384) : -CS(288),
      CR_CY - CS(128), CR_CY + CS(128), TOP2 + CS(5136), TOP2 + CS(5424), MAT.crownGold);
    cbox(`${F} arm flare ${s > 0 ? 'N' : 'S'}`, -CS(128), CS(128),
      CR_CY + Math.min(s * CS(288), s * CS(384)), CR_CY + Math.max(s * CS(288), s * CS(384)),
      TOP2 + CS(5136), TOP2 + CS(5424), MAT.crownGold);
  }
  cbox(`${F} crossing stone`, -CS(160), CS(160), CR_CY - CS(160), CR_CY + CS(160), TOP2 + CS(5216), TOP2 + CS(5344), MAT.jewelEmerald);
  cbox(`${F} top flare`, -CS(176), CS(176), CR_CY - CS(176), CR_CY + CS(176), TOP2 + CS(5568), TOP2 + CS(5664), MAT.crownGold);
  cbox(`${F} pip`, -CS(80), CS(80), CR_CY - CS(80), CR_CY + CS(80), TOP2 + CS(5664), TOP2 + CR_FINIAL_Z2, MAT.crownGold);
  // THE BEACON. Its job is to clear the south rim's occlusion line — which it
  // does by 1,392 units — and be SEEN from the floor of the base arena,
  // vertically aligned with the great ruby below it.
  //
  // THE FIRST CUT WAS A 160-WIDE NEEDLE AND THAT WAS THE OLD MISTAKE AGAIN.
  // Clearing the occlusion line is not the same as resolving: 160 units at
  // 22,079 is 0.41 deg = 12 px, under the half-degree floor, so it would have
  // shimmered away exactly like the gate spires it replaced. And from directly
  // below, a vertical member presents almost NO area at all — the preview's
  // `street` view shows the whole upper crown as a hairline. So the apex is a
  // STAR, not a spike: a cross of horizontal plates, because horizontal is the
  // only orientation that has any area when you are looking straight up at it.
  cbox('crown beacon needle', -CS(80), CS(80), CR_CY - CS(80), CR_CY + CS(80), TOP2 + CR_FINIAL_Z2, TOP2 + CS(6272), MAT.crownGold);
  cbox('crown beacon core', -CS(224), CS(224), CR_CY - CS(224), CR_CY + CS(224), TOP2 + CS(6272), TOP2 + CS(6720), MAT.jewelRuby);
  cbox('crown beacon arm EW', -CS(384), CS(384), CR_CY - CS(80), CR_CY + CS(80), TOP2 + CS(6432), TOP2 + CS(6592), MAT.jewelRuby);
  cbox('crown beacon arm NS', -CS(80), CS(80), CR_CY - CS(384), CR_CY + CS(384), TOP2 + CS(6432), TOP2 + CS(6592), MAT.jewelRuby);
  cbox('crown beacon pip', -CS(80), CS(80), CR_CY - CS(80), CR_CY + CS(80), TOP2 + CS(6720), TOP2 + CR_BEACON_Z2, MAT.crownGold);
}

// --- 5f.7 the jewels --------------------------------------------------------
// One boss per bay between adjacent points, keyed into C2 and C3 and standing
// 48 proud of C3's face. 320 square = 0.86 deg = 25 px from the base arena, so
// they are the smallest thing on the crown that still resolves.
// A vertical plaque is safe in a `_tinted_edge` material at any thickness — the
// lint's floor test is on the Z extent, which here is the boss's height.
{
  const JH = CS(160), JZ1 = TOP2, JZ2 = TOP2 + CS(320), JP = CS(48), JK = CS(128);
  const JM = [MAT.jewelRuby, MAT.jewelSapphire, MAT.jewelEmerald];
  const oS = CR_CY - CR_HY - JP, iS = CR_CY - CR_HY + JK;    // south face band
  const oN = CR_CY + CR_HY + JP, iN = CR_CY + CR_HY - JK;
  // A BAY IS THE GAP BETWEEN TWO ADJACENT POINTS, so its centre is computed from
  // where the points ACTUALLY are, never from a fraction of the wall. The old
  // fraction form put the outer bosses at 3/4 of PT_X = 2028 while the corner
  // point sits on the chamfer centreline at PT_CX = 2344 — so the moment the
  // corner ribs were widened to match their shafts, the boss ran into the post
  // and was partly buried. Midpoints cannot drift: widen a rib, move a point or
  // change CR_SCALE and the boss stays centred in its bay by construction.
  const BAYX = [-(PT_CX + PT_BX) / 2, -PT_BX / 2, PT_BX / 2, (PT_CX + PT_BX) / 2];
  const BAYY = [-(PT_CY + PT_BY) / 2, -PT_BY / 2, PT_BY / 2, (PT_CY + PT_BY) / 2];
  // THE TWO INNER SOUTH BOSSES WERE ENTIRELY BURIED. The frontispiece occupies
  // the two bays either side of the centreline by design (|x| up to CS(672)),
  // and the bosses for those bays sat inside it — 448-wide coloured slabs
  // completely enclosed in solid gold, costing bake and rendering nothing.
  // They are skipped rather than moved: the centreline already carries the
  // frontispiece, the Cullinan and the front cross, which is the busiest event
  // on the crown. It does not need two more stones behind a wall.
  // The NORTH face keeps all four — nothing is in front of them there.
  let n = 0;
  for (const jx of BAYX) {
    n++;
    if (Math.abs(jx) > CS(672) + JH)
      cbox(`crown jewel S${n}`, jx - JH, jx + JH, oS, iS, JZ1, JZ2, JM[n % 3]);
    cbox(`crown jewel N${n}`, jx - JH, jx + JH, iN, oN, JZ1, JZ2, JM[(n + 1) % 3]);
  }
  for (const jy of BAYY.map(d => CR_CY + d)) {
    cbox(`crown jewel W${++n}`, -CR_HX - JP, -CR_HX + JK, jy - JH, jy + JH, JZ1, JZ2, JM[n % 3]);
    cbox(`crown jewel E${n}`, CR_HX - JK, CR_HX + JP, jy - JH, jy + JH, JZ1, JZ2, JM[(n + 1) % 3]);
  }
  // THE FRONTISPIECE. A raised panel on the south band, spanning the two bays
  // either side of the centreline, that the Cullinan is set into. Without it
  // the front stone floats on a flat wall; with it the crown has a facade, and
  // the centreline reads as one vertical event from the mouth through the
  // stone to the front cross. It is 800 tall, so it is a wall, not a floor.
  // SPLIT AROUND THE MOUTH, and this is not a detail — the first cut spanned the
  // full +-672 for the whole band height and walled the causeway up inside the
  // rim. `lint_tod_geometry` caught it instantly: `terrace -> citadel walkable:
  // NO`, 336 detached road nodes. Anything that crosses x=0 on the south band
  // between CR_MOUTH_Z1 and CR_MOUTH_Z2 is a wall across the road.
  // fy1 is CS(16) proud, not CS(64): the frontispiece now sits BEHIND the mouth
  // jambs (which stand CS(240) proud) instead of sharing a plane with them.
  // Two different materials on one plane is a z-fight, and it also flattened the
  // gate's edge to nothing. Depth order out from the band is now:
  // jamb (240) > rib (224) > ermine (96) > rim (64) > frontispiece (16) > C4 (0).
  const fy1 = CR_CY - CR_HY - CS(16), fy2 = CR_CY - CR_HY + CS(96);
  const FW = CS(672), FP = CS(576);
  cbox('crown frontispiece head', -FW, FW, fy1, fy2,
    TOP2 + CR_MOUTH_Z2, TOP2 + CR_RIM_Z, MAT.crownGoldPanel);
  for (const s of [-1, 1])
    cbox(`crown frontispiece ${s > 0 ? 'E' : 'W'}`, s > 0 ? CR_MOUTH_HALF : -FW, s > 0 ? FW : -CR_MOUTH_HALF,
      fy1, fy2, TOP2 + CR_C1_Z, TOP2 + CR_MOUTH_Z2, MAT.crownGoldPanel);
  for (const s of [-1, 1])
    cbox(`crown frontispiece pier ${s > 0 ? 'E' : 'W'}`, s > 0 ? FP : -FW, s > 0 ? FW : -FP,
      CR_CY - CR_HY - CS(112), fy2, TOP2 + CR_C1_Z, TOP2 + CR_RIM_Z, MAT.crownGold);
  // THE CULLINAN — the band's front stone, on the lintel DIRECTLY ABOVE the
  // mouth the player walks through and DIRECTLY BELOW the front cross. It is
  // the brightest single point on the south elevation and it sits on the
  // centreline of the entire composition. Its z is derived from the courses it
  // straddles (C4 and the rim strip) so it cannot slide off the lintel.
  const CUZ1 = TOP2 + CR_C4_Z - CS(240), CUZ2 = TOP2 + CR_RIM_Z + CS(16);
  cbox('crown cullinan', -CS(320), CS(320), CR_CY - CR_HY - CS(144), fy2,
    CUZ1 + CS(32), CUZ2 - CS(32), MAT.jewelSapphire);
  cbox('crown cullinan bezel', -CS(384), CS(384), CR_CY - CR_HY - CS(128), fy2,
    CUZ1, CUZ2, MAT.crownGold);
}

// --- 5f.8 the pendilia ------------------------------------------------------
// Byzantine hanging strands off the ermine rim (the kamelaukion's pendilia).
// They hang at the OUTER edge of the rim rather than into the cone, so they
// read as a fringe on the silhouette's widest line instead of cluttering the
// concentric underside — which is the surface doing most of the work. They are
// under the legibility floor individually from the base, but they are a group
// read there and they are the detail that pays off on the walk in.
{
  const drops = [512, 704, 512].map(CS), PW = CS(80), PB = CS(112), PIN = CS(128);
  const strand = (tag, cx, cy, i) => {
    const d = drops[i % drops.length], z0 = TOP2 + CR_ERM_Z1;
    cbox(`${tag} cord`, cx - PW, cx + PW, cy - PW, cy + PW, z0 - d, z0, MAT.crownGold);
    cbox(`${tag} bead`, cx - PB, cx + PB, cy - PB, cy + PB, z0 - d - CS(224), z0 - d, MAT.jewelSapphire);
  };
  const yS = CR_CY - CR_HY - CR_ERM + PIN, yN = CR_CY + CR_HY + CR_ERM - PIN;
  [-3 * PT_X / 4, -3 * PT_X / 8, 0, 3 * PT_X / 8, 3 * PT_X / 4].forEach((jx, i) => {
    strand(`crown pendilia S${i + 1}`, jx, yS, i);
    strand(`crown pendilia N${i + 1}`, jx, yN, i + 1);
  });
  [-3 * PT_Y / 4, 0, 3 * PT_Y / 4].map(d => CR_CY + d).forEach((jy, i) => {
    strand(`crown pendilia W${i + 1}`, -CR_HX - CR_ERM + PIN, jy, i);
    strand(`crown pendilia E${i + 1}`, CR_HX + CR_ERM - PIN, jy, i + 1);
  });
}

// ---------------------------------------------------------------------------
// 5f.10 THE SECOND DETAIL SCALE (v11.2, user 2026-08-25: "Its scale is perfect.
// It looks fantastic. Now I want to review the design and add some details to
// it. To make it look nicer and more pleasing and impressive.")
//
// TWO MEASUREMENTS DECIDED EVERYTHING IN THIS SECTION.
//
// 1. THE MATERIALS ARE SELF-LIT. All 30 in the emox vertigo pack are
//    `lit_emissive_*` (verified in the GDT). A face pointing down and a face
//    pointing at the sky emit the same. So GEOMETRY DOES NOT SELF-SHADOW HERE:
//    a corbel, a ledge or a moulding produces NO value change on its own.
//    Relief only pays when it (a) breaks the silhouette against sky or a darker
//    neighbour, or (b) CARRIES A DIFFERENT MATERIAL. Everything below either
//    changes material or changes the outline. Nothing below is there to catch
//    light, because nothing here can.
//
// 2. THE CROWN IS ALREADY 84% OF THE MAP'S LIT AREA (run
//    `node tools/measure_lit_area.js`). The bake costs AREA — the same 4,700
//    brushes went 38.2 s to 126.2 s purely by scaling. So detail here must be
//    SMALL: a 200-unit cube is 0.24M against the crown's 807M. Small relief is
//    nearly free; a new LARGE SURFACE is what would cost. That is why this
//    section adds ~90 small brushes and not one new panel.
//
// AND WHERE IT GOES IS DECIDED BY WHERE A PLAYER CAN STAND. They can be: in the
// base arena, on the spiral, on the breathers, on the terrace, anywhere on the
// causeway, in the mouth, and on the hall floor. NOWHERE ELSE — they cannot fly
// and cannot reach the band. The reachable close views are all from the SOUTH:
// the terrace (~6,500 out), the plank (the raised centre route, 700-2,000 out —
// the real money view, see preview_crown.js), the mouth itself, and the hall
// floor looking up. So detail goes on the SOUTH face, the mouth and the ermine.
// The E/W/N band faces get nothing: they are only ever seen from 22,000 units,
// where the 384-unit legibility floor says sub-degree detail shimmers, so a
// brush spent there is pure bake cost for a surface nobody resolves.
// ---------------------------------------------------------------------------

// Apply a detail box to one of the ring's four flat faces. `u` is the position
// ALONG the face (x on the S/N faces, y offset from CR_CY on the W/E faces),
// `w` its width along that face, `out` how far it stands proud, `keyed` how far
// it sinks back into the wall so it never floats.
function crownFaceBox(tag, face, hx, hy, u, w, z1, z2, out, keyed, mat) {
  if (face === 'S') cbox(tag, u - w / 2, u + w / 2, CR_CY - hy - out, CR_CY - hy + keyed, z1, z2, mat);
  else if (face === 'N') cbox(tag, u - w / 2, u + w / 2, CR_CY + hy - keyed, CR_CY + hy + out, z1, z2, mat);
  else if (face === 'W') cbox(tag, -hx - out, -hx + keyed, CR_CY + u - w / 2, CR_CY + u + w / 2, z1, z2, mat);
  else cbox(tag, hx - keyed, hx + out, CR_CY + u - w / 2, CR_CY + u + w / 2, z1, z2, mat);
}

// --- ERMINE SPOTS -----------------------------------------------------------
// The ermine rim is the widest line in the whole silhouette and the strongest
// single read from the base arena — and it was a blank white bar. Heraldic
// ermine is white WITH DARK TAILS; that pattern is the entire reason a white
// band on a crown reads as fur rather than as paint. Two staggered rows, which
// is how ermine is actually diapered.
// 224 wide = 0.58 deg from the base arena, over the shimmer floor, so they
// resolve as spots instead of greying the ring down to a flat mid tone.
{
  const EW = CS(160), EH = CS(176), EO = CS(24);
  const z1 = TOP2 + CR_ERM_Z1, z2 = TOP2 + CR_ERM_Z2, mid = (z1 + z2) / 2;
  const hx = CR_HX + CR_ERM, hy = CR_HY + CR_ERM;
  let n = 0;
  for (const face of ['S', 'N']) {
    const span = (CR_HX - CR_CHAM) * 2;
    const cols = Math.max(3, Math.round(span / CS(760)) | 1);
    for (let i = 0; i < cols; i++) {
      // snapped to the 16-grid — span/cols never divides evenly here
      const u = Math.round((-span / 2 + span * (i + 0.5) / cols) / 16) * 16;
      // upper row on the odd columns, lower row on the even ones — a diaper
      const hi = (i % 2 === 0);
      crownFaceBox(`crown ermine spot ${++n}`, face, hx, hy, u, EW,
        hi ? mid + CS(8) : mid - EH - CS(8), hi ? mid + EH + CS(8) : mid - CS(8),
        EO, CS(32), MAT.crownErmineSpot);
    }
  }
  // v12: THE UNDERSIDE ROW. From the upper half of the spiral the sight line
  // has climbed past the ermine's face and what you see is its BOTTOM — the
  // widest, whitest annulus on the crown, and it was blank. One row of tails
  // hanging just under the south rim (south only: the rest of the annulus is
  // never seen — the tower is due south of the crown). They are keyed CS(32)
  // up into the ermine body so nothing floats, and their south face stands
  // CS(24) PROUD of the ermine's — the first cut put both on the same y plane,
  // dark_white against white, five z-fights on the strongest read from the
  // base (the mouth-jamb defect, again; caught by the same-day review). The
  // row rides SAFE_U: the pendilia cords fall straight past this z-band.
  {
    const yS = CR_CY - hy;
    for (const u of SAFE_U)
      cbox(`crown ermine spot ${++n}`, u - EW, u + EW, yS - CS(24), yS + CS(128),
        TOP2 + CR_ERM_Z1 - CS(24), TOP2 + CR_ERM_Z1 + CS(32), MAT.crownErmineSpot);
  }
}

// --- DENTILS UNDER THE RIM --------------------------------------------------
// A dentil course is the oldest "this is finished architecture, not a wall" cue
// there is, and it is one of the few kinds of relief that still works on
// self-lit materials: it reads as a broken OUTLINE against the dark recess
// behind it, not as a shaded moulding. South face only — see the header.
// Z extent CS(64) = 96, over MAX_SLAB, but plain `yellow` anyway so it can never
// be classed as floor at any scale.
{
  // A DENTIL COURSE IS INTERRUPTED BY ITS BUTTRESSES — that is how the real thing
  // behaves, and here it is not optional. At the rim's height the south face is
  // already occupied: the ribs stand 320 proud, the mouth jamb caps 384, the
  // Cullinan bezel 176, all of them in FRONT of a 56-proud dentil. An evenly
  // spaced course across the whole face buried more than half of itself and the
  // survivors read as scattered blocks, not as a course.
  // So: compute the RUNS between the obstructions and fill each one at its own
  // pitch. Every dentil emitted is one a player can actually see.
  // Each range is the obstruction's REAL extent plus half a dentil, so the
  // course stops exactly where something stands in front of it and no further.
  const DW = CS(72), DP = CS(88), DO = CS(40), HALF = CR_HX - CR_CHAM, P = DW / 2;
  const BLOCK = [
    [0, CS(384) + P],                                        // the Cullinan bezel
    [CR_MOUTH_HALF - CS(24) - P, CR_MOUTH_HALF + MJ + CS(48) + P], // the mouth jamb cap
    [CS(576) - P, CS(672) + P],                              // the frontispiece piers
    [PT_BX - CS(144) - P, PT_BX + CS(144) + P],              // the south ribs
    [PT_CX - CS(176) - P, Infinity],                         // the corner posts
  ].sort((a, b) => a[0] - b[0]);
  const runs = [];
  let cur = 0;
  for (const [a, b] of BLOCK) { if (a > cur) runs.push([cur, Math.min(a, HALF)]); cur = Math.max(cur, b); }
  if (cur < HALF) runs.push([cur, HALF]);
  let d = 0;
  for (const [a, b] of runs) {
    const n = Math.floor((b - a) / DP);
    for (let i = 0; i < n; i++) {
      const u = Math.round((a + (b - a) * (i + 0.5) / n) / 16) * 16;   // 16-grid
      for (const s of [-1, 1])
        crownFaceBox(`crown dentil ${++d}`, 'S', CR_HX + CS(48), CR_HY + CS(48), s * u, DW,
          TOP2 + CR_C4_Z - CS(96), TOP2 + CR_C4_Z, DO, CS(48), MAT.crownGold);
    }
  }
}

// --- THE CULLINAN BECOMES A CUT STONE ---------------------------------------
// It is the focal point of the entire south elevation and it was a single flat
// slab 896 wide — from the plank it reads as a blue rectangle painted on gold.
// A real stone of that size in a crown is a CABOCHON in a clawed collet: a
// stepped dome held by four claws. Three stacked plates give the dome, four
// small gold blocks give the claws, and the outline stops being a rectangle.
{
  const cy1 = CR_CY - CR_HY, S = 'crown cullinan';
  const zc = (TOP2 + CR_C4_Z - CS(240) + TOP2 + CR_RIM_Z + CS(16)) / 2;
  const steps = [[CS(224), CS(112), CS(72)], [CS(144), CS(72), CS(112)]];
  steps.forEach(([hw, hh, out], k) => {
    cbox(`${S} facet ${k + 1}`, -hw, hw, cy1 - CS(144) - out, cy1 - CS(144),
      zc - hh, zc + hh, MAT.jewelSapphire);
  });
  for (const sx of [-1, 1]) for (const sz of [-1, 1])
    cbox(`${S} claw ${sx > 0 ? 'E' : 'W'}${sz > 0 ? 'U' : 'D'}`,
      sx > 0 ? CS(288) : -CS(352), sx > 0 ? CS(352) : -CS(288),
      cy1 - CS(176), cy1 - CS(48),
      sz > 0 ? zc + CS(112) : zc - CS(208), sz > 0 ? zc + CS(208) : zc - CS(112),
      MAT.crownGold);
}

// --- BOSS COLLETS -----------------------------------------------------------
// The Cullinan and the great ruby both sit in a gold surround; the remaining
// face bosses were coloured slabs stuck flat to a wall with nothing holding
// them, which reads as a decal rather than a stone. One plate behind each, a
// little larger than the stone, is the cheapest possible collet.
// South and north only — the E/W faces are never seen close (header).
{
  const CH = CS(200), CZ = CS(400), OB = (PT_CX + PT_BX) / 2;   // the outer bay centre
  for (const jx of [-OB, OB]) {
    crownFaceBox(`crown collet S${jx < 0 ? 'W' : 'E'}`, 'S', CR_HX, CR_HY, jx, CH * 2,
      TOP2 - CS(40), TOP2 + CZ, CS(24), CS(160), MAT.crownGold);
  }
}

// --- SUNKEN PANELS IN THE SOUTH BAYS ----------------------------------------
// THE NUMBER-ONE COMPLAINT IN EVERY CRITIQUE. Between the ribs, each outer south
// bay is an unbroken field roughly 660 wide by 1,800 tall carrying one boss and
// nothing else — the single largest flat surface a player ever walks past, and
// it reads as an untextured wall in every close render.
// You cannot RECESS anything with additive boxes, so the panel is implied the
// way real masonry implies it: a raised FRAME around a quiet centre. Four thin
// bars per bay, plain gold standing proud of the gold-panel field, which is a
// 13.5-against-7.8 value step and therefore reads without any light at all.
// The horizontals are under MAX_SLAB in Z, so plain colour is MANDATORY here.
// THE PANEL FITS THE BAY IT IS IN, and the bay is measured, not assumed. The
// first cut centred a CS(300) half-width panel on the bay midpoint, which put
// BOTH its stiles behind the very buttresses that define the bay — the ribs
// stand 320 proud at |x| 1152-1552 and the corner posts at 2104+, and the panel
// spanned 1428-2268. `tools/audit_hidden_faces.js` caught both stiles at 100%
// buried on all six faces: a frame with no sides is not a frame.
// The clear span is rib-outer to post-inner, so that is what it is derived from.
{
  const RIB_OUT = PT_BX + CS(144), POST_IN = PT_CX - CS(176);
  const BW = CS(40), BO = CS(64), BK = CS(96), PAD = CS(48);
  const a = RIB_OUT + PAD, b = POST_IN - PAD;
  const cx = (a + b) / 2, half = (b - a) / 2;
  const z1 = TOP2 + CR_C1_Z + CS(80), z2 = TOP2 + CR_C3_Z - CS(48);
  if (half > BW * 2) for (const sx of [-1, 1]) {
    const tag = sx > 0 ? 'SE' : 'SW';
    for (const s of [-1, 1])
      crownFaceBox(`crown panel ${tag} stile ${s > 0 ? 'E' : 'W'}`, 'S', CR_HX, CR_HY,
        sx * (cx + s * half), BW, z1, z2, BO, BK, MAT.crownGold);
    for (const [nm, za, zb] of [['head', z2 - BW, z2], ['sill', z1, z1 + BW]])
      crownFaceBox(`crown panel ${tag} ${nm}`, 'S', CR_HX, CR_HY, sx * cx, half * 2 + BW,
        za, zb, BO, BK, MAT.crownGold);
  }
}

// --- THE MOUTH: bases, capitals and a ribbed vault ---------------------------
// The mouth is the ONE piece of the crown every player is guaranteed to see from
// arm's length, and it is the only place on the whole fabric with a light
// entity (`tod light crown mouth`), so it is the only place where relief behaves
// the way relief is supposed to. It gets the densest detail on the crown.
{
  const JX = CR_MOUTH_HALF, MJ2 = CS(160), y2 = CR_CY - CR_HY + CS(144);
  for (const sx of [-1, 1]) {
    // A BASE AND A CAPITAL, so the jamb stands ON something and stops AT
    // something. The BASE takes MP1 because it reaches down to the road deck and
    // must stay north of the J4 landing; the CAP takes MP_DEEP and oversails,
    // which is exactly the corbel a real gate head does over its own threshold.
    // The BASE takes its projection entirely in X (it is already wider than the
    // jamb) and NONE in Y: it sits exactly on MP1, because any southward
    // oversail at deck height lands on the J4 landing. The CAP is high enough to
    // oversail freely. The 5f.9 road assert enforces this — it caught a 64-unit
    // `- CS(48)` on the base that was left over from when both shared a line.
    for (const [nm, za, zb, yy] of [
      ['base', TOP2, TOP2 + CS(128), MP1],
      ['cap', TOP2 + CR_C4_Z - CS(160), TOP2 + CR_C4_Z, MP_DEEP - CS(48)]])
      cbox(`crown mouth jamb ${nm} ${sx > 0 ? 'E' : 'W'}`,
        sx > 0 ? JX - CS(24) : -JX - MJ2 - CS(48), sx > 0 ? JX + MJ2 + CS(48) : -JX + CS(24),
        yy, y2, za, zb, MAT.crownGold);
  }
  // two longitudinal vault ribs under the soffit. They run N-S so they can never
  // cross x=0 on the south band (constraint C), and they sit CS(80) below the
  // soffit, leaving well over GATE_H of clearance over the road.
  for (const sx of [-1, 1])
    cbox(`crown mouth vault rib ${sx > 0 ? 'E' : 'W'}`,
      sx > 0 ? CS(200) : -CS(272), sx > 0 ? CS(272) : -CS(200),
      CR_CY - CR_HY - CS(32), CR_CY - CR_HY + BAND_T + CS(96),
      TOP2 + CR_MOUTH_Z2 - CS(160), TOP2 + CR_MOUTH_Z2 - CS(80), MAT.crownGold);
}

// --- POINT PLINTHS ----------------------------------------------------------
// Every shaft on the rim just started in mid-air where it met the rim strip.
// A plinth is the cheapest way to make sixteen posts read as STANDING on the
// crown rather than being stuck to it, and it is a silhouette break so it works
// on self-lit materials. South row and the four corners only: the north and
// side points are never seen from close enough for a 128-tall block to resolve.
CR_POINTS.forEach(([px, py, kind], i) => {
  if (kind === 'front') return;
  if (!(py < CR_CY || kind === 'corner')) return;      // south row + corners
  const w = (kind === 'corner') ? CS(232) : (kind === 'tall' ? CS(216) : CS(200));
  cbox(`crown point ${i + 1} plinth`, px - w, px + w, py - w, py + w,
    PZ - CS(24), PZ + CS(112), MAT.crownGoldPanel);
});

// --- 5f.9 THE SEAL, asserted against the crown's REAL bounding box ----------
// This runs last on purpose: it reads crownBB, which is accumulated by addBox as
// the crown is emitted, so it sees what was actually cut rather than what the
// constants imply. Before v11 the seal was `SKY_IN = max(2900, HN + 384)` and
// `SKY_TOP = MAST_TOP + 300`, and the only asserts in the file tested the
// CAUSEWAY — so nothing whatsoever would have fired when the beacon went
// thousands of units through the roof of the world. A hole in the sky is a hole
// in the world, not a cosmetic bug.
// THE CROWN MUST NOT STAND ON THE ROAD, and this is asserted against the brushes
// rather than against the constants — because the constants version passed while
// four gold blocks were sitting on the causeway's J4 landing.
//
// 5f.1 checks `CR_CY - CR_HY - CR_ERM > cwY[8]`, which is true (6912 > 6880) and
// says nothing at all about a jamb, a base or a corbel that reaches 336 units
// further south than the band it hangs off. That is exactly what happened in the
// v11.2 detail pass, and NO EXISTING GATE CAUGHT IT: lint_tod_geometry's
// misplaced-wall check only fires on a `clip` brush with no visible solid, and a
// VISIBLE solid silently drops the node from `stand` — while the reachability
// flood still walks the middle of a 960-wide landing, so it stayed green too.
//
// The invariant nobody had written down: south of cwY[8] the road is 960 wide to
// +-CW_LAND, so any crown brush there must be either outside that width or high
// enough over it that a player walks under (STAND_HI is 70; use 96 for margin).
// docs/163 THE CUT: the deck south of cwY[8] is the LAUNCH deck now (640 deep,
// +-JP_LAUNCH_HALF since the balcony) instead of the J4 landing — same
// invariant, new footprint.
// THE ENCLOSED HALLWAY (2026-09-25): the same proof for every hallway room —
// no crown brush may stand in a room, in its wall columns, or through its roof
// (the frontispiece piers reach deck height at x 800..944, y 6848+; rib 3's
// foot reaches y 6688 at x 1144..1560). The shop hulls are the huts' own collision.
if (CW_CUT) {
  for (const [n, c] of Object.entries(HW_ROOMS)) {
    const hit = crownBoxes.filter(b =>
      !/^crown item shop \d+ hull \d+$/.test(b.label) &&
      b.x1 < c.x2 + ROAD_G && b.x2 > c.x1 - ROAD_G && b.y1 < c.y2 + ROAD_G && b.y2 > c.y1 - ROAD_G &&
      b.z1 < TOP2 + HW_H + SLAB && b.z2 > TOP2 - SLAB - 24);
    if (hit.length) throw new Error(`${hit.length} crown brush(es) stand in ${n}: ${hit.slice(0, 4).map(b => `${b.label} x[${b.x1},${b.x2}] y[${b.y1},${b.y2}] z[${b.z1},${b.z2}]`).join('; ')}`);
  }
}
{
  const RY = cwY[8], RX = (CW_CUT ? JP_LAUNCH_HALF : CW_LAND) + PARA + 20, RZ = TOP2 + 96;
  const RY1 = CW_CUT ? JP_LAUNCH_Y1 : cwY[7];
  // the balcony's display shop (CROWN_SHOPS[3]) stands on the deck ON PURPOSE:
  // its hulls are the hut's own collision (the lint's MODEL_CLIP_COLUMNS), not
  // an obstruction — the same standing the hall's three have inside the hall.
  const onRoad = crownBoxes.filter(b =>
    !/^crown item shop \d+ hull \d+$/.test(b.label) &&
    b.y1 < RY && b.y2 > RY1 && b.x1 < RX && b.x2 > -RX && b.z1 < RZ && b.z2 > TOP2 + 2);
  if (onRoad.length) {
    const l = onRoad.slice(0, 6).map(b =>
      `\n    ${b.label}  x[${b.x1},${b.x2}] y[${b.y1},${b.y2}] z[${b.z1},${b.z2}]`).join('');
    throw new Error(`${onRoad.length} crown brush(es) stand on the causeway landing ` +
      `(south of y=${RY}, within x +-${RX}, below z=${RZ}) — they would be an obstruction ` +
      `on the road that the geometry lint cannot see:${l}`);
  }
}
{
  const bb = crownBB;
  const R = Math.max(-bb.x1, bb.x2, -bb.y1, bb.y2);
  if (bb.z2 + 256 > SKY_TOP)
    throw new Error(`crown reaches z ${bb.z2} but the sky ceiling is at ${SKY_TOP}`);
  if (bb.z2 > SKY_TOP - 200)
    throw new Error(`crown reaches z ${bb.z2} but the umbra/fpstool lid is at ${SKY_TOP - 200}`);
  if (bb.z1 - 256 < SKY_FLOOR)
    throw new Error(`crown descends to z ${bb.z1} but the sky floor is at ${SKY_FLOOR}`);
  if (R + 256 > SKY_IN)
    throw new Error(`crown reaches ${R} from the axis but the sky wall is at ${SKY_IN}`);
  // (the umbra/fpstool volume is asserted where VOL_R is defined — it is
  // declared further down the file, in the entities section)
  console.log(`  crown: x[${bb.x1},${bb.x2}] y[${bb.y1},${bb.y2}] z[${bb.z1},${bb.z2}] ` +
    `(${bb.x2 - bb.x1} wide, ${bb.z2 - bb.z1} tall, CR_SCALE ${CR_SCALE}); ` +
    `sky wall ${SKY_IN}, ceiling ${SKY_TOP}`);
}

// ---------------------------------------------------------------------------
// Entities
// ---------------------------------------------------------------------------
const entities = [];
function ent(label, lines) { entities.push({ label, text: lines.join('\n') }); }
function kv(k, v) { return `"${k}" "${v}"`; }

// Stock Giant negotiation pair, one direction only. No invisible walkable ramp.
// Native reference: zm_giant_nodes.map, zm_jump_down_190, 51u forward / 190u down.
if (DESCENT) for (const lap of BROKEN_TOWER.DROP_LAPS) {
  const p=BROKEN_TOWER.placement(lap),end=`tod_drop_lap${lap}_end`;
  ent(`lap${lap} broken zombie drop begin`,['{',`guid "${guid()}"`,kv('classname','node_negotiation_begin'),
    kv('origin',p.upper.map((v,i)=>v+(i===2?2:0)).join(' ')),kv('angles',`0 ${p.yaw} 0`),
    kv('animscript','zm_jump_down_190'),kv('target',end),kv('script_noteworthy','tod_tower_drop'),kv('script_int',lap),kv('cost_modifier','1'),'}']);
  ent(`lap${lap} broken zombie drop end`,['{',`guid "${guid()}"`,kv('classname','node_negotiation_end'),
    kv('origin',p.lower.map((v,i)=>v+(i===2?2:0)).join(' ')),kv('angles',`0 ${p.yaw} 0`),kv('targetname',end),'}']);
  for(const kind of ['upper','lower']) {
    const lo=kind==='lower'?p.lo:[p.lo[0],p.s>0?256:-352,p.b+192];
    const hi=kind==='lower'?p.hi:[p.hi[0],p.s>0?352:-256,p.b+292];
    ent(`lap${lap} broken ${kind} trigger`,['{',`guid "${guid()}"`,kv('classname','trigger_multiple'),
      kv('targetname',`tod_tower_drop_${kind}`),kv('script_int',lap),kv('spawnflags','0'),
      box(lo[0],hi[0],lo[1],hi[1],lo[2],hi[2],'trigger'),'}']);
  }
}

function volumeBrush(x1, x2, y1, y2, z1, z2) {
  const t = 'volume 64 64 0 0 0 0 lightmap_gray 16384 16384 0 0 0 0';
  return [
    '{',
    ` guid "${guid()}"`,
    ` ( 134.5 459.5 ${z1} ) ( 86.5 459.5 ${z1} ) ( 86.5 419.5 ${z1} ) ${t}`,
    ` ( 94.5 419.5 ${z2} ) ( 94.5 459.5 ${z2} ) ( 142.5 459.5 ${z2} ) ${t}`,
    ` ( 86.5 ${y1} 88 ) ( 134.5 ${y1} 88 ) ( 134.5 ${y1} 0 ) ${t}`,
    ` ( ${x2} 415.5 88 ) ( ${x2} 455.5 88 ) ( ${x2} 455.5 0 ) ${t}`,
    ` ( 138.5 ${y2} 88 ) ( 90.5 ${y2} 88 ) ( 90.5 ${y2} 0 ) ${t}`,
    ` ( ${x1} 459.5 88 ) ( ${x1} 419.5 88 ) ( ${x1} 419.5 0 ) ${t}`,
    '}',
  ].join('\n');
}
function matBrush(x1, x2, y1, y2, z1, z2, mat) {
  return box(x1, x2, y1, y2, z1, z2, mat);
}

// mirrored volume brush (crown zones) — same re-ordering rule as cbox
function cvolume(x1, x2, y1, y2, z1, z2) {
  return CM === 1 ? volumeBrush(x1, x2, y1, y2, z1, z2) : volumeBrush(-x2, -x1, -y2, -y1, z1, z2);
}
// mirrored {x1,x2,y1,y2,z1,z2} spec (door slab/trig/clip boxes)
function cspec(s) {
  return CM === 1 ? s : { x1: -s.x2, x2: -s.x1, y1: -s.y2, y2: -s.y1, z1: s.z1, z2: s.z2 };
}

// --- zones + spawners -------------------------------------------------------
// v9: the FINAL lap's volumes stop just above its last landing (TOP+100) —
// stock-height ring volumes (b+LAP_RISE+200) would swallow the crown stair
// and the terrace, and level.zones iteration order would then report every
// player up there as "lap50_zone" forever. The crown stair past the door
// belongs to roof_zone (its volumes start at TOP-SLAB).
function lapVolumeBrushes(lapBase, isLast) {
  const z1 = lapBase - SLAB, z2 = isLast ? TOP + 100 : lapBase + LAP_RISE + 200;
  return [
    volumeBrush(CORE, PX + PARA, -CORE, CORE, z1, z2),
    volumeBrush(-PX - PARA, -CORE, -CORE, CORE, z1, z2),
    volumeBrush(-PX - PARA, PX + PARA, CORE, PX + PARA, z1, z2),
    volumeBrush(-PX - PARA, PX + PARA, -PX - PARA, -CORE, z1, z2),
  ];
}

// Riser points down the causeway. Section 5c owns WHERE they go, because only
// the code that lays the road knows where the road actually is (see roof_zone
// below for why that matters now).
function causewayRisers() { return causewayRunPoints(); }

const ZONES = [
  {
    name: 'base_zone',
    brushes: [
      volumeBrush(-(ARENA + WALL), ARENA + WALL, -(ARENA + WALL), ARENA + WALL, -SLAB, 368),
      volumeBrush(TRANSIT.BASE.x1-40, TRANSIT.BASE.x2+40, TRANSIT.BASE.y1-40, TRANSIT.BASE.y2, -SLAB, 368),
      // THE POWER HALLWAY'S EXTERIOR LEG MOVED OUT OF base_zone (v13.1) into
      // power_zone below, for the reason the teleport bay is its own zone: it
      // is a SEALED room until enter_power is bought, and base_zone is live
      // from round 1, so the riser this change adds would have spawned zombies
      // behind a DisconnectPaths'd door with no way out — actor slots burnt on
      // enemies nobody can reach or kill. Coverage is not lost, only deferred:
      // power_zone carries the same volume and goes live on the same flag, and
      // nothing can drop in there before the door opens because nothing can
      // die in there. The 20u threshold strip x[540,560] (the gap cut through
      // the arena's east wall) stays base_zone — it holds no riser, and
      // carving it out of the arena box would cost a brush to buy nothing.
    ],
    // SE riser: the (470,-470) corner is now the POWER ROOM, and the y=-360
    // relocation (user 2026-08-20) still landed it in a dead pocket — the east
    // gutter (x[416,540]) is sealed from the walkway by the lap1 anti-bypass
    // wall (x416..436, y[-256,256], z0..288) and capped on the south by the
    // power-room north wall (y=-400), so a zombie there could only mill at the
    // first-door corner (user 2026-08-21: "stuck at a wall near the first stair
    // door"). Moved ONTO the open walkway ring, south of the E-flight base and
    // the door slab (y=-256), where it paths freely to the arena and up.
    // docs/158: the SW riser (-470,-470) sat inside the South Workshop door's
    // inner sphere (-460,-530) r96 and the NW one (-470,470) inside the West
    // Workshop's (-530,400): both moved onto open floor >150u from every door
    // trigger. NE (470,470) is 115u from the East Workshop's (530,380,40).
    risers: [[-470, -380, 0], [336, -336, 0], [-380, 440, 0], [470, 470, 0]],
    dog: [0, -470, 0],
  },
];
for (let lap = 1; lap <= LAPS; lap++) {
  const b = (lap - 1) * LAP_RISE;
  const oddz = (lap % 2 === 1);
  const brushes = lapVolumeBrushes(b, lap === LAPS);
  if (BREATHER_LAPS.has(lap)) {
    // THE HAVEN HALL (docs/202 v2) stands over the core, where no ring volume
    // reaches (the core used to be solid) — cover it (tools/haven_layout.js); the
    // loggia is inside the ring volumes already. A point outside every zone volume
    // gets no spawn logic, no drop logic and THE RECALL's out-of-bounds verdict,
    // and nothing says so until someone plays it.
    if (oddz) throw new Error(`haven zone on odd lap ${lap}`);
    brushes.push(...HAVEN.zoneBrushes(volumeBrush, b - SLAB, b + LAP_RISE + 200));
  }
  // HAVEN RISERS (docs/202). History: v10.12 put risers INSIDE the breather
  // lounges (user 2026-08-23: "The safe breather zones need to be a lot less
  // safe") and v13.2 added one on the spur. The haven is a SAFE ZONE now (user
  // 2026-10-02): nothing rises inside the field. The horde rises on the lap's
  // own two landings (the ordinary floor's risers) and on the hall floor round
  // the field (six, 165+ from the teleporter arrival: the v10.22 materialize
  // rule) — every one OUTSIDE the field, so the pressure is real but it has to
  // walk into the field (and its 33% slow) to reach you.
  // NOTE FOR THE BAKE: risers are spawn structs; they add no brushes.
  const brz = b + FLIGHT_RISE;   // the haven sits on the floor's MID landing
  ZONES.push({
    name: `lap${lap}_zone`,
    brushes: brushes,
    risers: BREATHER_LAPS.has(lap)
      ? HAVEN.risers(brz, b + LAP_RISE)
      : (oddz
      ? [[336, 336, b + FLIGHT_RISE], [-336, 336, b + LAP_RISE]]
      : [[-336, -336, b + FLIGHT_RISE], [336, -336, b + LAP_RISE]]),
    dog: oddz ? [336, 336, b + FLIGHT_RISE] : [-336, -336, b + FLIGHT_RISE],
  });
  // THE HAVEN'S SURFACES (docs/202). The navmesh is a seeded region prune, not
  // a flood (memory navmesh-is-seeded-flood): seed every walkable SURFACE —
  // the hall, the loggia arms, the south strip, the porch fan. The two landings are
  // seeded by their risers again (the 2026-09-04 "breather laps have no landing
  // seed" gap closed itself when the landing risers came back).
  if (BREATHER_LAPS.has(lap))
    for (const [label, x, y, z] of HAVEN.seeds(b + FLIGHT_RISE)) navSeed(`lap${lap} ${label}`, x, y, z);
}
// roof_zone (v9) = the crown APPROACH: stair + terrace, causeway. Two risers
// on the terrace ends and one on every piece of the road; the dog/fallback
// struct on the terrace.
// docs/160 — THE HALL IS ITS OWN ZONE NOW (crown_zone, right below). It was
// the third brush of this one, with its four risers in this list. Under
// DESCENT the party SPAWNS in the hall and the Fall gate seals it behind
// them, so the hall has to be (a) the START zone — enabled at init, its
// risers live from the first frame — and (b) a zone whose spawning can be
// switched OFF at the seal (_tod_fall::seal sets is_spawning_allowed false)
// without touching the road's. One shared volume could do neither: risers
// in a sealed hall would keep rising for as long as anyone stood on the
// road (adjacent + occupied = active), path-severed and stranded.
ZONES.push({
  name: 'roof_zone',
  brushes: [
    cvolume(TRANSIT.ROOM.x1-20, TRANSIT.ROOM.x2, TRANSIT.ROOM.y1-20, TRANSIT.ROOM.y2+20, TOP2-SLAB, TOP2+TRANSIT.ROOM.height),
    cvolume(-TER_W - PARA, TER_W + PARA, -CORE, TER_Y2 + PARA, TOP - SLAB, TOP2 + 400),          // crown stair + terrace
    // BOUNDING BOX OF THE WHOLE ROAD, MEASURED FROM THE ROAD (v10.12). The
    // doglegs swing to x +/-800 and the branches leave TOP2 in both directions,
    // so this is computed from the declared deck cells rather than written down:
    // anything the volume misses is outside roof_zone, which means no spawns and
    // no zone logic on that piece of road, and nothing says so until someone
    // plays it. A hand-maintained literal here has been wrong twice.
    // docs/163 THE CUT: only the terrace's stub (gate-run + landing deck) is
    // roof_zone now; the crown's stub belongs to crown_zone below.
    (CW_CUT ? cvolume(JP_TER_BOX.x1, JP_TER_BOX.x2, JP_TER_BOX.y1, JP_TER_BOX.y2, JP_TER_BOX.z1, JP_TER_BOX.z2)
            : cvolume(CW_XMIN, CW_XMAX, CW_YMIN, CW_YMAX, CW_ZMIN, CW_ZMAX)),                          // causeway
    ...(DESCENT ? [] : [cvolume(-HW - 16, HW + 16, HS - 16, HN + 16, TOP2 - SLAB, TOP2 + 700)]),  // hall (climb layout only)
  ],
  // v10 — THE LAST MILE. The road used to have NO risers, so everything on it
  // had to walk in from the terrace or the hall: a queue, not an ambush.
  // causewayRunPoints() now puts one on EVERY piece of the road — the three
  // on-axis stretches and all four branches — each on its own centreline at its
  // own height (v10.11; the old evenly-spaced x=+/-180 points assumed a straight
  // strip at TOP2 and half of them would now be hanging in mid-air). A party
  // that splits at a fork gets clawed at on both branches at once.
  // Concurrency is NOT set here — level.zombie_ai_limit / zombie_actor_limit
  // still bind (see _tod_finale::finale_director). More risers buys VARIETY OF
  // DIRECTION, never more simultaneous AI, which is exactly the distinction
  // that keeps this from blowing the actor cap. While the gate is shut none of
  // them are eligible at all — _tod_endless_rounds::finale_spawn_selection.
  risers: [
    ...(DESCENT ? [] : [cpt(-560, HS + 280, TOP2), cpt(560, HS + 280, TOP2),
                        cpt(-560, HN - 280, TOP2), cpt(560, HN - 280, TOP2)]),
    cpt(-400, 368, TOP2), cpt(400, 368, TOP2),
    ...TRANSIT.RISERS.map(([x,y])=>cpt(x,y,TOP2)),
    // docs/163 THE CUT: one riser per road piece would put one ON the pad and
    // one ON the landing spot. The landing deck gets two at its far corners
    // (>= 165u from every set-down spot, asserted in 5c); the gate-run and the
    // crown's stub get none — the crown's zombies come out of the hall.
    ...(CW_CUT ? JP_LAND_RISERS.map(([rx, ry]) => cpt(rx, ry, TOP2)) : causewayRisers()),
  ],
  dog: DESCENT ? cpt(0, 368, TOP2) : cpt(0, HYC, TOP2),
});
// crown_zone (docs/160) = THE HALL, the START zone under DESCENT. The same
// four risers the hall always had (they dig up through the citadel floor in
// its four quarters — open aisle bays, clear of the piers and the shrines),
// the dog struct at the hall centre (the dais). The volume starts at the
// gate's own south face (HS) so it never overlaps the causeway's, which ends
// at the citadel mouth portal (CW_YMAX is deck cells only); its z band is the
// old hall brush's. The Fall gate's inner trigger sphere is inside this box,
// the outer one on the road — a player at either is in exactly one zone.
// docs/163 THE CUT: + the crown's stub (launch deck, approach, flare), which
// only the hall can reach on foot. Its players keep the hall's risers live
// (occupied zone = active zone), so waiting at the pad is never safe; the
// hall's is_spawning_allowed switch at the seal covers the stub too.
if (DESCENT) ZONES.push({
  name: 'crown_zone',
  brushes: [
    cvolume(-HW - 16, HW + 16, HS, HN + 16, TOP2 - SLAB, TOP2 + 700),
    ...(CW_CUT ? [cvolume(JP_CRN_BOX.x1, JP_CRN_BOX.x2, JP_CRN_BOX.y1, JP_CRN_BOX.y2, JP_CRN_BOX.z1, JP_CRN_BOX.z2)] : []),
  ],
  risers: [
    cpt(-560, HS + 280, TOP2), cpt(560, HS + 280, TOP2),
    cpt(-560, HN - 280, TOP2), cpt(560, HN - 280, TOP2),
  ],
  dog: cpt(0, HYC, TOP2),
});

// The bottom return apron is open to the base, so it shares the base zone.
ZONES.find(z => z.name === 'base_zone').risers.push(...TRANSIT.BASE.risers);

// POWER HALL (v13.1, user 2026-08-28: "add one zombie spawn in the power switch
// hallway towards the switch in the back. The issue is players will camp in
// here so adding a spawn might help that").
//
// WHY IT IS ITS OWN ZONE and not two more lines in base_zone: identical to the
// teleport bay's reasoning above. The hall is sealed by the enter_power door
// (slab Solid + DisconnectPaths at x=280) until it is bought, and base_zone is
// live from round 1 — a riser in there on the base's ticket would spawn
// zombies into a corridor with a severed navmesh from the very first round.
// They would path nowhere, die to nothing, and hold actor slots against the
// 45-zombie cap for the whole run. The zone gate is what makes the riser safe.
//
// THE CAMP THIS BREAKS: the hall is a 1,060-long dead end with ONE mouth, so a
// player standing at the east cap covers the only approach and never has to
// turn around. The riser goes BEHIND that firing line, not in front of it —
// west of it and the camp is untouched.
//
// PLACEMENT x=1400, measured rather than eyeballed:
//   corridor walkable  x[560,1620], y[-540,-420] -> centreline y=-480
//   power switch       origin x=1613, USE TRIGGER x[1589,1608]
//   riser -> trigger   189u clear, so a zombie can never rise standing inside
//                      the switch's trigger and block the buy (the same
//                      no-two-things-in-one-trigger rule the tp-bay pads and
//                      the lounge furniture are spaced by)
//   riser -> east cap  220u — inside the last fifth of the hall, which is the
//                      half a camper actually occupies
//   hall lights (x 800/1200/1560) are z=100 point lights, no collision
// The dog point sits mid-corridor: a hound needs run-up, and dropping one on
// top of the riser would stack two spawn events on one 120-wide strip.
ZONES.push({
  name: 'power_zone',
  brushes: [
    volumeBrush(560, 1660, -580, -380, -SLAB, 368),
  ],
  risers: [[1400, -480, 0]],
  dog: [1100, -480, 0],
});

// THE UNDERCITY ZONES (docs/158). The Vault is the START zone (init_zones[0]
// in zm_tod2_cybercity.gsc); its risers are the four window niches. The
// Conduit's zone carries the shaft too (two brushes: the room and the shaft
// slot), so the whole climb is live once enter_conduit is bought and nothing
// on it is a dead pocket. Both meet base_zone's box at the arena wall face.
ZONES.push({
  name: 'vault_zone',
  brushes: [volumeBrush(VT_X1 - WALL - WIN_D - 40, VT_X2 + WALL + WIN_D + 40, VT_Y1 - WALL - WIN_D - 40, VT_Y2, UC_Z - SLAB, UC_Z + 368)],
  risers: VAULT_RISERS,
  dog: [VT_CX, VT_CY, UC_Z],
});
ZONES.push({
  name: 'conduit_zone',
  brushes: [
    volumeBrush(CD_X1 - WALL, CD_X2 + WALL, VT_Y2, CD_Y2 + WALL, UC_Z - SLAB, UC_Z + 368),
    volumeBrush(CD_X2 + WALL, SHAFT_TOP_X2, SHAFT_CY - SHAFT_HW - WALL, SHAFT_CY + SHAFT_HW + WALL, UC_Z - SLAB, 368),
  ],
  // by the east wall, flanking the shaft mouth: they rise between the player
  // and the stairs, 172u from the door's conduit-side trigger
  risers: [[CD_X2 - 84, CD_Y2 - 32, UC_Z], [CD_X2 - 84, CD_Y1 + 32, UC_Z]],
  dog: [(CD_X1 + CD_X2) / 2, SHAFT_CY, UC_Z],
});
// THE WING ZONES: hallway + room, from the arena wall's outer face outward;
// clamped where a neighbour's box (the teleport bay's) would overlap.
for (const w of WINGS) {
  const F = wingFrame(w), R = WING_ROOM / 2;
  let v1 = Math.min(w.dc - 100, w.rc - R - WALL) - 20, v2 = Math.max(w.dc + 100, w.rc + R + WALL) + 20;
  if (w.zoneVMax !== undefined) v2 = Math.min(v2, w.zoneVMax);
  if (w.zoneVMin !== undefined) v1 = Math.max(v1, w.zoneVMin);
  const r = F.rect(WU0, WU_ROOM3 + 20, v1, v2, -SLAB, 368);
  for (const [rx, ry] of WING_RISERS[w.key])
    if (rx < r.x1 || rx > r.x2 || ry < r.y1 || ry > r.y2) throw new Error(`wing ${w.key}: riser (${rx},${ry}) outside its zone box`);
  ZONES.push({
    name: `wing_${w.key}_zone`,
    brushes: [volumeBrush(r.x1, r.x2, r.y1, r.y2, r.z1, r.z2)],
    risers: WING_RISERS[w.key],
    dog: [...F.pt(WU_ROOM1 + R, w.rc), 0],
  });
}
// THE BATTLE ARENA (docs/185): its own zone, adjacent to nothing (script
// teleport only); _tod_arena enables it before the party lands. Risers and
// their navmesh seeds come from the loop below like every tower zone's.
ZONES.push(ARENA_LAYOUT.zone(volumeBrush));
// THE DEALER'S HOUSE (docs/207): two more islands (the parlour, the final arena), adjacent to
// nothing; _tod_house enables them before the party lands on level 10.
for (const zn of HOUSE_LAYOUT.zones(volumeBrush)) ZONES.push(zn);
// no two zone boxes may overlap (a player in two zones is claimed by both)
{
  const boxes = [];
  for (const zn of ZONES) for (const b of zn.brushes) {
    // a volume brush's bound on each axis is the coordinate its three points
    // share (the other two coordinates on that plane are Radiant dummies)
    const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (const l of b.split('\n').filter(l => l.startsWith(' ('))) {
      const m = l.match(/\( (\S+) (\S+) (\S+) \) \( (\S+) (\S+) (\S+) \) \( (\S+) (\S+) (\S+) \)/).slice(1, 10).map(Number);
      for (let a = 0; a < 3; a++) if (m[a] === m[3 + a] && m[a] === m[6 + a]) { lo[a] = Math.min(lo[a], m[a]); hi[a] = Math.max(hi[a], m[a]); }
    }
    boxes.push({ zn: zn.name, x1: lo[0], x2: hi[0], y1: lo[1], y2: hi[1], z1: lo[2], z2: hi[2] });
  }
  const ground = boxes.filter(b => b.z1 < 400 && /^(base|vault|conduit|wing_|tpbay|power)/.test(b.zn));
  for (let i = 0; i < ground.length; i++) for (let j = i + 1; j < ground.length; j++) {
    const a = ground[i], b = ground[j];
    if (a.zn === b.zn) continue;
    if (a.x1 < b.x2 && b.x1 < a.x2 && a.y1 < b.y2 && b.y1 < a.y2 && a.z1 < b.z2 && b.z1 < a.z2)
      throw new Error(`zone volumes overlap: ${a.zn} x[${a.x1},${a.x2}] y[${a.y1},${a.y2}] vs ${b.zn} x[${b.x1},${b.x2}] y[${b.y1},${b.y2}]`);
  }
}
for (const zn of ZONES) {
  ent(`${zn.name} info_volume`, [
    '{',
    `guid "${guid()}"`,
    kv('classname', 'info_volume'),
    kv('script_noteworthy', 'player_volume'),
    kv('target', `${zn.name}_spawners`),
    kv('targetname', zn.name),
    ...zn.brushes,
    '}',
  ]);
  zn.risers.forEach(([sx, sy, sz], i) => {
    ent(`${zn.name} riser ${i + 1}`, [
      '{',
      `guid "${guid()}"`,
      kv('classname', 'script_struct'),
      kv('angles', '0 270 0'),
      kv('origin', `${sx} ${sy} ${sz}`),
      kv('script_noteworthy', 'riser_location'),
      kv('script_string', 'find_flesh'),
      kv('targetname', `${zn.name}_spawners`),
      kv('_color', '1 0 0'),
      '}',
    ]);
  });
  // NAVMESH SEEDS — THE TOWER (2026-09-03). THE SAME BUG THE SPIRE SHIPPED IN
  // v14.0-v14.18, IN THE OTHER TOWER, AND IT WENT UNSEEDED FOR LONGER.
  //
  // User: "zombies are spawning in and not moving ... only if you get close
  // they move", "if I throw a monkey it disappears instantly and I hear
  // samantha", "around floor 18 ... anything above they wont target". One
  // cause explains all three: NO NAVMESH above ~floor 17. An off-mesh zombie
  // has no path and no find_flesh, so it stands until stock's direct
  // proximity aggro fires; a Cymbal Monkey needs mesh under it to become a
  // zombie_poi and is discarded instantly when there is none; and the Sam
  // laugh is this map's own documented tell for the out-of-playable monitor
  // (zm_tod2_cybercity.gsc:532 and :845 — god mode MASKS it, which is why the
  // v17.6 disarm is when it became audible rather than when it broke).
  //
  // WHY IT ONLY BIT NOW. cod2map64 FLOOD-GROWS navmesh from seed entities
  // only (radiant/configs/navmesh.json "seeds": node_*, mp_*spawn*,
  // cp_*spawn*, info_player_start, actor_*). Grep the emitted .map for those
  // classes and the whole 50-floor tower had exactly TWO, both standing on
  // the base arena floor: the factory spawner and info_player_start. Every
  // other thing this file places is on the EXCLUSION list (script_struct,
  // info_volume, script_brushmodel, light, node_*), so nothing seeded a
  // single floor by accident. Fifty floors of spiral were meshed by one flood
  // climbing from z=0, and a flood has a finite reach: it used to clear the
  // tower, and after the floors changed it stopped somewhere around lap 17.
  // The §6f comment below already spelled this mechanism out and named the
  // two base seeds — it fixed the SPIRE and left the tower riding the flood.
  //
  // A SEED PER ZONE IS THE RULE, NOT A PATCH FOR ONE BAD FLOOR. Seeding only
  // where it broke would re-break the moment the geometry moves again, and
  // "which lap does the flood die on" is not a number anything checks. One
  // node_pathnode per RISER (not per zone as §6f does — the tower's two
  // risers per lap sit on the mid and end landings, i.e. one on each flight's
  // top, which is exactly the coverage a flight-by-flight flood wants) makes
  // every landing its own origin, so no lap can be orphaned by the one below
  // it failing to hand the flood upward. node_pathnode is itself on the
  // exclusion list (it carves nothing), is invisible, spawns no runtime
  // gentity and is untargeted by script — zm_giant ships six the same way.
  // Risers stand on proven-open landing floor by construction, so a seed can
  // never land inside a brush.
  //
  // A NEW DETACHED REGION NEEDS ITS OWN SEED — and so does a region the flood
  // merely HAPPENS to reach today. FULL build: the navmesh is what changes.
  zn.risers.forEach(([sx, sy, sz], i) => {
    ent(`${zn.name} navmesh seed ${i + 1}`, [
      '{',
      `guid "${guid()}"`,
      kv('classname', 'node_pathnode'),
      kv('origin', `${sx} ${sy} ${sz + 2}`),
      kv('_color', '1 0 1'),
      '}',
    ]);
  });
  ent(`${zn.name} dog location`, [
    '{',
    `guid "${guid()}"`,
    kv('classname', 'script_struct'),
    kv('origin', `${zn.dog[0]} ${zn.dog[1]} ${zn.dog[2]}`),
    kv('script_noteworthy', 'dog_location'),
    kv('targetname', `${zn.name}_spawners`),
    kv('_color', '1 0 0'),
    '}',
  ]);
}

// --- player start / initial spawns / respawn / intermission -----------------
//
// SPAWN MOVED SOUTH BAND -> WEST BAND (user 2026-08-27: "I do want to make sure
// players dont spawn in at a door buyable in their radius. Currently the spawn
// for the map is outside doors where you can see the trigger as you are
// selecting your class. There is one side of the first floor that has no doors
// or perks. Thats where I want to move the spawn").
//
// THE BUG, MEASURED: _tod_doors spawns a trigger_radius_use of RADIUS 96 at each
// door's org AND at org+off (both sides of the slab). Against the old south-band
// spawns that put SIX OF THE EIGHT start points inside a live buy trigger:
//   (-64,-462) (64,-462)   -> enter_tpbay (0,-530)  93.4u   INSIDE
//   (-64,-498) (64,-498)   -> enter_tpbay (0,-530)  71.6u   INSIDE
//   (192,-462) (192,-498)  -> enter_power (270,-480) 80.0u  INSIDE
// so most of the party stared at a "Hold F to buy" prompt through the whole
// 30-second class draft. The old row also sat 64u from the base dog spawn
// (0,-470).
//
// WHY WEST. Enumerating the base ring by side (ARENA 540 outer, CORE 256 inner,
// so each band is 284 wide):
//   NORTH  9 perk parking pads along y=500 (x -520..520)
//   SOUTH  all three base doors' triggers (enter_tpbay 0,-550 / enter_power
//          270,-480 / and enter_lap1's south reach), the base upgrade station on
//          the core south face (0,-320, trigger 0,-360), intermission, tp-bay
//   EAST   enter_lap1 (336,-256) + the lap1 anti-bypass wall
//   WEST   NOTHING. No door, no perk pad, no station, no wallbuy (this map has
//          none), no box (none either). The class-select stations that used to
//          live at the base were removed 2026-08-20.
// So the west band is the only side with no interactable at all — exactly the
// side the user identified.
//
// PLACEMENT is the old 4x2 grid TRANSPOSED onto the band: 4 points along y at
// the same 128 spacing, 2 rows across x at the same 36 spacing, same z=28. That
// keeps quad/trio/duo/solo behaviour identical — stock fills from the same
// eight-struct list, it just reads different coordinates. Clearances:
//   nearest door trigger .......... 572u (enter_tpbay)   vs the 96u radius
//   base upgrade station trigger .. 491u
//   nearest perk pad (-520,500) ... 313u
//   nearest zombie riser .......... 278u  (-470,-470 and -470,470, tied)
//   base dog spawn (0,-470) ....... 511u
//   west wall face (x=-540) ....... 42u   (identical to the old row's clearance
//                                          from the south wall — same margin)
// All eight sit inside base_zone's volume (it spans the full arena + walls), so
// the start-room group stays selectable exactly as before.
//
// WHAT MOVES WITH THEM: info_player_start, the player_respawn_point GROUP origin
// (its children are these structs — leaving the parent behind would scatter the
// group's distance maths across the arena), and 'tod light base spawn', the
// dedicated warm light that exists to light the spawn. What does NOT move, and
// why: 'probe base' has radius 2048 and covers the whole 1080-wide arena from
// anywhere in it; the intermission camera is a spectator view, not a spawn; and
// _tod_atmosphere's music emitter at (0,-490,100) only needs to be in OPEN AIR
// (its aliases are 2D), which that point still is.
//
// EVERY OTHER KEY ON THESE STRUCTS IS UNCHANGED — in particular
// script_noteworthy "start_room" and the script_string gametype list. A
// player_respawn_point is LOCKED at init and unlocks only by noteworthy match
// (_zm_zonemgr.gsc:827); this map has already shipped an inert respawn group
// once by dropping that key. Only `origin` moves here.
// docs/158 — THE PARTY SPAWNS IN THE VAULT (the Undercity), facing north at
// the door to the Conduit. Same 4 x 2 grid as before (128 along the row, 36
// between rows, +28 above the floor), so quad/trio/duo/solo fill identically.
// Clearances: the door's vault-side trigger (VT_CX, -498) r96 is 240u from the
// nearest point; the window risers are >= 180u away (a zombie never climbs out
// onto a spawning player); Quick Revive's pad is 200u+ east of the row.
// The old west-band row survives as the PLAZA RESPAWN GROUP below (co-op
// respawns land beside the tower once base_zone is open, like the breather
// groups), and its warm light keeps its old spot at the exit door's mouth.
const SPAWN_BAND_X = -480;   // the plaza's west band (core face -256, wall -540) — the co-op respawn group
// docs/160 — THE PARTY SPAWNS IN THE CROWN HALL (DESCENT). Eight points in
// the nave's north bay, between the last pier row (y HYC+184, bases to +240)
// and the sanctuary foot seam (SANC_Y1 - 24 = HYC+... see 5d), facing SOUTH
// down the nave at the Fall gate — the whole hall, the Pack-a-Punch in the
// east shrine and the one door out are in view from the first frame. Same
// 4 x 2 grid as every start group this map has had (128 along the row, 40
// between rows, +28 above the floor), so quad/trio/duo/solo fill identically.
// Clearances: pier bases E4/W4 start at x 328 (row ends at x 192 + hull);
// the nave seams at x +-300 are 1u walk-overs; the hall risers (+-560,
// HN-280) are ~400u away (a zombie never climbs out onto a spawning player,
// the 165u rule); the gate's inner trigger sphere (0, HS+HWALL/2+60) r96 is
// ~1000u south. Every point is inside crown_zone's volume. Coordinates are
// authored in the crown's ODD frame and mirrored by cpt()/cyaw() like all
// crown geometry — a raw coordinate here would put the group on the wrong
// side of the tower at the other parity.
// The Vault's eight points survive as the VAULT RESPAWN GROUP below, gated on
// vault_zone like every other zone group (the Undercity is the run's end now).
const HALL_SPAWN_Y = [HYC + 260, HYC + 300];
const HALL_SPAWN_X = [-192, -64, 64, 192];
{
  const [px, py, pz] = cpt(0, HALL_SPAWN_Y[0] - 30, TOP2 + 40);
  ent('info_player_start', [
    '{', `guid "${guid()}"`, kv('classname', 'info_player_start'),
    kv('angles', `0 ${cyaw(270)} 0`), kv('origin', `${px} ${py} ${pz}`), '}',
  ]);
  const [gx, gy, gz] = cpt(0, HALL_SPAWN_Y[0], TOP2 + 28);
  ent('player_respawn_point', [
    '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
    kv('angles', `0 ${cyaw(270)} 0`), kv('origin', `${gx} ${gy} ${gz}`),
    kv('radius', '2000'), kv('script_int', '2000'),
    kv('script_noteworthy', 'start_room'),
    kv('script_string', 'zclassic_start_room zcleansed_start_room zgrief_start_room'),
    kv('target', 'initial_spawn_points'), kv('targetname', 'player_respawn_point'),
    kv('_color', '1 0 0'), '}',
  ]);
}
const SPAWNS = [];
for (const sy of HALL_SPAWN_Y) for (const sx of HALL_SPAWN_X) SPAWNS.push(cpt(sx, sy, TOP2 + 28));
SPAWNS.forEach(([sx, sy, sz], i) => {
  ent(`initial spawn ${i + 1}`, [
    '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
    kv('_color', i % 2 ? '1 0 1' : '1 1 0'),
    kv('angles', `0 ${cyaw(270)} 0`), kv('origin', `${sx} ${sy} ${sz}`),
    kv('radius', '32'), kv('script_int', `${(i % 2) + 1}`),
    kv('script_noteworthy', 'initial_spawn'),
    kv('script_string', 'zcleansed_start_room'),
    kv('targetname', 'initial_spawn_points'), '}',
  ]);
});
// THE CROWN HALL RESPAWN GROUP (docs/160): the same bay, gated on crown_zone
// so a co-op death during the crown phase comes back inside the hall. At the
// seal _tod_fall LOCKS this group again (spawn_points[i].locked = true — the
// same field stock's selector reads), so nobody can ever respawn behind the
// shut gate: a player on the road's north end is nearer this group than the
// terrace's, and stock picks by distance among unlocked groups.
if (DESCENT) {
  const [gx, gy, gz] = cpt(0, HALL_SPAWN_Y[1], TOP2 + 28);
  ent('crown hall respawn group', [
    '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
    kv('angles', `0 ${cyaw(270)} 0`), kv('origin', `${gx} ${gy} ${gz}`),
    kv('radius', '2000'), kv('script_int', '2000'),
    kv('script_noteworthy', 'crown_zone'),
    kv('target', 'tod_respawn_hall'), kv('targetname', 'player_respawn_point'),
    kv('_color', '1 0 0'), '}',
  ]);
  HALL_SPAWN_X.forEach((sx, i) => {
    const [px, py, pz] = cpt(sx, HALL_SPAWN_Y[1], TOP2 + 28);
    ent(`crown hall spawn ${i + 1}`, [
      '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
      kv('_color', i % 2 ? '1 0 1' : '1 1 0'),
      kv('angles', `0 ${cyaw(270)} 0`), kv('origin', `${px} ${py} ${pz}`),
      kv('radius', '32'), kv('targetname', 'tod_respawn_hall'), '}',
    ]);
  });
}
// THE VAULT RESPAWN GROUP (docs/158's start room, docs/160's last room):
// gated on vault_zone. Four of the old eight points, the row nearest the
// spawn light.
ent('vault respawn group', [
  '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
  kv('angles', '0 90 0'), kv('origin', `${VT_CX} ${VT_CY - 72} ${UC_Z + 28}`),
  kv('radius', '2000'), kv('script_int', '2000'),
  kv('script_noteworthy', 'vault_zone'),
  kv('target', 'tod_respawn_vault'), kv('targetname', 'player_respawn_point'),
  kv('_color', '1 0 0'), '}',
]);
[-192, -64, 64, 192].forEach((dx, i) => {
  ent(`vault spawn ${i + 1}`, [
    '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
    kv('_color', i % 2 ? '1 0 1' : '1 1 0'),
    kv('angles', '0 90 0'), kv('origin', `${VT_CX + dx} ${VT_CY - 52} ${UC_Z + 28}`),
    kv('radius', '32'), kv('targetname', 'tod_respawn_vault'), '}',
  ]);
});
// THE PLAZA RESPAWN GROUP (docs/158): gated on base_zone exactly like the
// breather groups are gated on their lap zones (script_noteworthy == zone
// name, no script_string). Four points on the west band, north of the exit
// door's inner sphere ((-510,-160) r96 -> y >= -64) and south of the West
// Workshop's ((-530,400) r96 -> y <= 304).
ent('plaza respawn group', [
  '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
  kv('angles', '0 90 0'), kv('origin', `${SPAWN_BAND_X} 120 28`),
  kv('radius', '2000'), kv('script_int', '2000'),
  kv('script_noteworthy', 'base_zone'),
  kv('target', 'tod_respawn_base'), kv('targetname', 'player_respawn_point'),
  kv('_color', '1 0 0'), '}',
]);
[[-462, 80], [-462, 160], [-498, 80], [-498, 160]].forEach(([sx, sy], i) => {
  ent(`plaza spawn ${i + 1}`, [
    '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
    kv('_color', i % 2 ? '1 0 1' : '1 1 0'),
    kv('angles', '0 90 0'), kv('origin', `${sx} ${sy} 28`),
    kv('radius', '32'), kv('targetname', 'tod_respawn_base'), '}',
  ]);
});
// --- BREATHER RESPAWN GROUPS (co-op audit 2026-08-23) ------------------------
// The map used to emit exactly ONE player_respawn_point — the base-arena group
// above — and no spawn-override callback anywhere in scripts/. Stock's selector
// therefore had a one-element candidate list, so EVERY bled-out co-op player
// came back at z=28 regardless of how high the party had climbed. A floor-40
// death was a 53,088-unit re-ascent past every door, unperked (nothing sets
// _retain_perks), and because breather balconies deliberately emit no risers the
// lone returning player pulled most of the spawn budget onto himself the whole
// way up. In practice he did not climb — he looped the arrival pad.
//
// Stock picks the group CLOSEST to a living teammate, but only if the group's
// origin sits inside an ENABLED zone (_zm.gsc:3399 check_point_in_enabled_zone).
// So a breather group is automatically ineligible until that lap's door is
// bought, and a party can never respawn past a door it has not paid for. That
// gating is a property of WHERE the struct is; it needs no script support.
//
// script_string is DELIBERATELY OMITTED. get_player_spawns_for_gametype
// (_zm_gametype.gsc:589) filters a struct to matching locations when it carries
// a gametype string and adds it to ALL locations when it does not. The base
// group carries "zclassic_start_room ..." because it IS the start room; these
// are not, and must stay eligible in every mode the map runs in.
//
// `locked` is omitted too, matching the base group — stock never initialises it,
// and only maps that want a spawn disabled ever set it true (zm_giant.gsc:413).
//
// PLACEMENT (docs/202): INSIDE THE HAVEN'S FIELD — a 2 x 2 round the dome
// centre (tools/haven_layout.js RESPAWN, asserted clear of every machine), so a
// bled-out co-op player comes back in the safe zone. The haven platform is in
// lap{N}_zone (HAVEN.zoneBrushes), which is what gates the group. Mid-landing
// top is (lap-1)*LAP_RISE + FLIGHT_RISE; the +28 matches the base spawns'
// height above their own floor.
const BREATHER_SPAWN_XY = HAVEN.RESPAWN;
[...BREATHER_LAPS].sort((a, b) => a - b).forEach((lap) => {
  const brz = (lap - 1) * LAP_RISE + FLIGHT_RISE + 28;
  const brTn = `tod_respawn_lap${lap}`;
  ent(`lap${lap} breather respawn group`, [
    '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
    kv('angles', '0 90 0'), kv('origin', `${HAVEN.C[0]} ${HAVEN.C[1]} ${brz}`),
    kv('radius', '2000'), kv('script_int', '2000'),
    // script_noteworthy IS REQUIRED, and its absence made this whole feature
    // INERT (verification pass 2026-08-23). manage_zones() LOCKS every
    // player_respawn_point at zone-manager init (_zm_zonemgr.gsc:810-828), and
    // the ONLY unlock anywhere in the stock zm tree is enable_zone's
    // `spawn_points[i].script_noteworthy == zone_name` (:505-510) — all three
    // selection sites then skip anything still locked. So these four groups
    // could never unlock, and bled-out co-op players kept falling back to
    // spectator_respawn (the base arena): exactly the exile the v10.4 entry
    // claims to have fixed. The balcony brush belongs to lap{N}_zone, so that
    // is the correct gate — and it delivers the door-gating the original
    // comment wanted, since the zone only enables once that lap's door is
    // bought. (The base group's 'start_room' matches no zone on this map
    // either, but that one is harmless: stock's fallback lands in the same
    // arena it names, which is why nobody noticed.)
    kv('script_noteworthy', `lap${lap}_zone`),
    kv('target', brTn), kv('targetname', 'player_respawn_point'),
    kv('_color', '1 0 0'), '}',
  ]);
  BREATHER_SPAWN_XY.forEach(([sx, sy], i) => {
    ent(`lap${lap} breather spawn ${i + 1}`, [
      '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
      kv('_color', i % 2 ? '1 0 1' : '1 1 0'),
      kv('angles', '0 90 0'), kv('origin', `${sx} ${sy} ${brz}`),
      kv('radius', '32'), kv('targetname', brTn), '}',
    ]);
  });
});

// --- CROWN RESPAWN GROUP (review 2026-08-23) --------------------------------
// The four breather groups above stop a co-op death being a 50-floor re-climb,
// but they stop at floor 40 — there was NOTHING on the crown. A player who bled
// out on the terrace, on the causeway or inside the citadel fell all the way
// back to the base arena, and during THE LAST MILE that is not a setback, it is
// removal from the game: the run is a 191-second song, the gate is behind them,
// and 8,600 units of road plus a 50-floor climb do not fit in what is left of
// it. One player dying ended that player's finale outright.
//
// ON THE TERRACE, not in the citadel, and that is the whole design of it: you
// come back at the START of the road and have to run it again. Respawning past
// the gate would hand the ending to anyone willing to trade a down for a
// teleport, which is the opposite of what the road is for.
//
// Gated for free by roof_zone, exactly like the breather groups are gated by
// their lap zones: script_noteworthy must equal the zone name or manage_zones()
// leaves the group LOCKED forever (the trap that made all four breather groups
// inert until 2026-08-23), and stock also refuses any group whose origin is not
// inside an ENABLED zone. So this cannot be used before the roof door is bought.
//
// PLACEMENT: the terrace is x[-TER_W,TER_W] y[TER_Y1,TER_Y2] at TOP2. The four
// points sit EAST of centre, clear of the causeway mouth (x +/-100, where the
// gate stands) and clear of the uplink terminal at x -(CW_HALF+96). Mirrored by
// cpt() like every other crown coordinate — the terrace itself is emitted
// through cbox, so raw coordinates here would put the whole group on the wrong
// side of the tower at the other parity.
const CROWN_SPAWN_XY = [[240, 320], [360, 320], [240, 420], [360, 420]];
{
  const gz = TOP2 + 28;   // +28 above the deck, matching the base group
  const org = cpt(0, (TER_Y1 + TER_Y2) / 2, gz);
  ent('crown respawn group', [
    '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
    kv('angles', `0 ${cyaw(90)} 0`), kv('origin', `${org[0]} ${org[1]} ${org[2]}`),
    kv('radius', '2000'), kv('script_int', '2000'),
    kv('script_noteworthy', 'roof_zone'),
    kv('target', 'tod_respawn_crown'), kv('targetname', 'player_respawn_point'),
    kv('_color', '1 0 0'), '}',
  ]);
  CROWN_SPAWN_XY.forEach(([sx, sy], i) => {
    const o = cpt(sx, sy, gz);
    ent(`crown spawn ${i + 1}`, [
      '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
      kv('_color', i % 2 ? '1 0 1' : '1 1 0'),
      kv('angles', `0 ${cyaw(90)} 0`), kv('origin', `${o[0]} ${o[1]} ${o[2]}`),
      kv('radius', '32'), kv('targetname', 'tod_respawn_crown'), '}',
    ]);
  });
}

ent('intermission', [
  '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
  kv('angles', '0 90 0'), kv('origin', '0 -500 104'),
  kv('target', 'intermission_b'), kv('targetname', 'intermission'),
  kv('_color', '1 0 0'), '}',
]);
ent('intermission_b', [
  '{', `guid "${guid()}"`, kv('classname', 'script_struct'),
  kv('angles', '0 30 0'), kv('origin', '-460 -460 104'),
  kv('targetname', 'intermission_b'), kv('_color', '1 0 0'), '}',
]);

// --- AI factory alternatives: stock runtime filter keeps exactly one --------
// Both use the same spawn location/settings. All modes select the native cyber
// mix before spawn initialization. Keep historical markers compatible with BSPs.
for (const [factory, marker] of [
  ['actor_spawner_zm_factory_zombie', 'tod_cyber_stock'],
  ['actor_archetype_tod_charcoal_zombie', 'tod_cyber_dev'],
]) {
ent('zombie factory spawner ' + marker, [
  '{', `guid "${guid()}"`,
  kv('classname', factory), kv('script_string', marker),
  kv('ALERTONSPAWN', '0'), kv('MAKEROOM', '1'), kv('SCRIPT_FORCESPAWN', '1'),
  kv('angles', '0 270 0'), kv('count', '9999'), kv('export', '1'),
  kv('origin', '470 470 208'),
  kv('script_disable_bleeder', '1'), kv('script_forcespawn', '1'),
  kv('script_noteworthy', 'zombie_spawner'), kv('SPAWNER', '1'),
  kv('_color', '1 0.25 0'), kv('engageMaxDist', '700'), kv('engageMinDist', '250'),
  kv('model', 'c_zom_test_body1'), kv('script_dropammo', '1'),
  kv('sm_active_count_max', '3'), kv('sm_active_count_min', '3'),
  kv('spawnflags', '19'), '}',
]);
}

// --- buyable doors (25 lap doors + the rooftop flight) -----------------------
// v6 doors: odd floors enter the E flight at the SE corner (S walkway),
// even floors enter the W flight at the NW corner (N walkway).
// A door's anti-bypass clip rises 600 above the doorway so nobody vaults the
// slab — but it must never poke up THROUGH the floor above it. lap50's did:
// 18816+600 = 19416, and the terrace deck is at 19392, so 24 units of invisible
// clip stood on the terrace floor. 24 > the 18-unit step, so it was a wall you
// could not walk over and could not see — the same defect class as the lap-1
// rail cap that took three bug reports to find, caught this time by
// tools/lint_tod_geometry.js before anyone played it.
//
// Clamped to the UNDERSIDE of the crown floor. A no-op for laps 1-49 (600 never
// reaches it) and exactly right for lap 50. The ROOF door is deliberately not
// clamped: it sits on the opposite face, the lint proves it intrudes on nothing,
// and shortening it there would trade a real anti-bypass guard for no gain.
function doorClipTop(b) { return Math.min(b + 600, TOP2 - SLAB); }

const DOORS = [];
// v16.11 FACELIFT §2 — DOOR GATES THAT OPEN. Every lap door was a bare
// 160x20x128 slab in one green material that blinked away on purchase. Now:
//   slabMat   the `_tinted_edge` of the district the door opens INTO, so at a
//             district boundary the door is the first thing in the new colour
//   post      a 20-square glow post in that district's plain hue standing IN
//             THE RAIL BAND (x PX..PX+PARA) on the door line, floor to lintel
//             top, so the closed slab meets it edge to edge with no slot. The
//             two rail runs that meet at the door line are NOTCHED back
//             DOOR_POST_NOTCH each side (the parapet emission reads
//             doorPostAt), so the post overlaps nothing and nothing is
//             coplanar with it. Until 2026-10-04 it stood OUTSIDE the band and
//             the band's own 20 units of open air above the low rail beside
//             every closed door was the user's "odd gap between them and the
//             railing" (map 1 fixed the same slit in v19.57).
//   lintel    a 24-tall bar over the path from the core face to the post's
//             outer face, sitting ON the slab's top (z1 = slab z2), so the
//             doorway reads as a framed gate from both sides
//   sill      a 1u strip of the slab material in the floor under the slab —
//             hidden while the door is shut, revealed when it SLIDES INTO THE
//             CORE (_tod_doors.gsc: MoveX toward x=0 by the slab's own width
//             plus 8, then Hide/NotSolid/ConnectPaths as before). The rise the
//             map's dead `script_vector 0 0 130` keys were authored for was
//             dropped for the slide: a rising slab would pass through any
//             lintel low enough to read as a frame.
// The roof, power and bay doors keep their old slab and get no gate (different
// walls, different frames); only enter_lapN doors carry `gate`.
for (let lap = 1; lap <= LAPS; lap++) {
  const b = (lap - 1) * LAP_RISE;
  const dMat = doorMatOf(lap - 1);     // the district you are buying into (MATTE — v18.99g)
  if (DESCENT && BROKEN_TOWER.drops.has(lap)) continue; // collapsed gate: free one-way drop
  const gMat = paraMatOf(lap - 1);                             // its plain hue (post + lintel)
  if (lap % 2 === 1) {
    DOORS.push({
      flag: `enter_lap${lap}`, cost: DESCENT ? descentCost(LAPS + 1 - lap) : doorCost(lap), target: `tod_door_lap${lap}`,
      dest: DESCENT ? (lap > 1 ? `the Spiral - Floor ${lap - 1}` : 'the Ground Floor') : `the Spiral - Floor ${lap}`,
      slab: { x1: CORE, x2: PX, y1: -266, y2: -246, z1: b, z2: b + 128 },
      trig: { x1: CORE, x2: PX, y1: -306, y2: -206, z1: b, z2: b + 128 },
      clip: { x1: CORE, x2: PX + PARA, y1: -266, y2: -246, z1: b + 128, z2: doorClipTop(b) },
      org: [336, -256, b + 40], off: [0, 60, 0],
      slabMat: dMat,
      gate: FACELIFT ? {
        mat: gMat,
        post:   { x1: PX, x2: PX + PARA, y1: -266, y2: -246, z1: b, z2: (lap === 1 ? 288 : b + 152) },   // IN the rail band (doorPostAt); lap 1: up the 288 anti-bypass wall it now ends
        lintel: { x1: CORE, x2: PX + PARA, y1: -266, y2: -246, z1: b + 128, z2: b + 152 },
        sill:   { x1: CORE, x2: PX, y1: -266, y2: -246, z1: b, z2: b + 1 },
      } : undefined,
    });
  } else {
    DOORS.push({
      flag: `enter_lap${lap}`, cost: DESCENT ? descentCost(LAPS + 1 - lap) : doorCost(lap), target: `tod_door_lap${lap}`,
      dest: DESCENT ? (lap > 1 ? `the Spiral - Floor ${lap - 1}` : 'the Ground Floor') : `the Spiral - Floor ${lap}`,
      slab: { x1: -PX, x2: -CORE, y1: 246, y2: 266, z1: b, z2: b + 128 },
      trig: { x1: -PX, x2: -CORE, y1: 206, y2: 306, z1: b, z2: b + 128 },
      clip: { x1: -PX - PARA, x2: -CORE, y1: 246, y2: 266, z1: b + 128, z2: doorClipTop(b) },
      org: [-336, 256, b + 40], off: [0, 60, 0],
      slabMat: dMat,
      gate: FACELIFT ? {
        mat: gMat,
        post:   { x1: -(PX + PARA), x2: -PX, y1: 246, y2: 266, z1: b, z2: b + 152 },   // IN the rail band (doorPostAt)
        lintel: { x1: -(PX + PARA), x2: -CORE, y1: 246, y2: 266, z1: b + 128, z2: b + 152 },
        sill:   { x1: -PX, x2: -CORE, y1: 246, y2: 266, z1: b, z2: b + 1 },
      } : undefined,
    });
  }
}
// The rail notches (doorPostAt) and the posts must agree lap for lap: a notch with no post is a
// 10-unit hole in the railing, a post with no notch a solid overlapping the parapet.
for (let lap = 1; lap <= LAPS + 1; lap++) {
  const gated = DOORS.some(d => d.flag === `enter_lap${lap}` && d.gate);
  if (gated !== doorPostAt(lap)) throw new Error(`lap ${lap}: doorPostAt says ${doorPostAt(lap)} but the DOORS table ${gated ? 'has' : 'has no'} gate post`);
}
// CROWN DOOR (v9): gates the FIRST TREAD of the crown stair, on whichever
// landing the spiral ended on. This is exactly the odd-lap door formula with
// b=TOP, point-mirrored by CM for an even crown lap — the old version was
// hardcoded to "lap 25 ends via the N flight" and with LAPS=50 it hung a slab
// in open air on the wrong side of the tower.
DOORS.push({
  // DESCENT: this is the FIRST spiral door the party meets (bought from the
  // terrace side, k=0 on the descent ladder) and it opens DOWN onto floor 50.
  flag: 'enter_roof', cost: DESCENT ? descentCost(0) : ROOF_DOOR_COST, target: 'tod_door_roof',
  dest: DESCENT ? `the Spiral - Floor ${LAPS}` : 'the Crown',
  slab: cspec({ x1: CORE, x2: PX, y1: -266, y2: -246, z1: TOP, z2: TOP + 128 }),
  trig: cspec({ x1: CORE, x2: PX, y1: -306, y2: -206, z1: TOP, z2: TOP + 128 }),
  clip: cspec({ x1: CORE, x2: PX + PARA, y1: -266, y2: -246, z1: TOP + 128, z2: TOP + 600 }),
  org: cpt(336, -256, TOP + 40), off: [0, 60, 0],
});
// THE FALL GATE (docs/160): the crown hall's own door, bought FROM INSIDE for
// FALL_GATE_COST. Until TOD II this brush was the finale's "crown door" —
// emitted on its own further down, opened at init and slammed shut for the
// hold-out. It is a row of THIS table now so _tod_doors owns the buy (hint,
// party-size price, the flag, the open) and _tod_fall.gsc owns the one thing
// no other door does: it SEALS AGAIN once every living player is out (Show +
// Solid + DisconnectPaths — the spire's hall-gate contract). It fills the gate
// opening exactly (x +-GATE_HALF under the lintel, which is solid velvet up to
// the cornice), so it carries NO anti-vault clip. Trigger spheres 60 either
// side of the wall's centre plane, r96: the inner one stands on the nave's
// threshold seam (a 1u walk-over) and clears the first pier bases (x 328+);
// the outer one stands on the flare deck.
// THE ENCLOSED HALLWAY'S SIDE DOORS (user 2026-09-25: "left will cost money,
// right will cost money", 1500 each on the question). Each slab fills its
// corridor's first column (the junction's wall line) to the hallway roof, so
// no clip; trigger spheres 60 either side, the inner one in the junction.
if (DESCENT && CW_CUT) {
  for (const [flag, target, dest, sx] of [['tod_crown_power', 'tod_door_crown_power', 'the Power Room', 1],
                                          ['tod_crown_tele', 'tod_door_crown_tele', 'the Teleporter', -1]]) {
    const xa = sx > 0 ? HW_EAST.x1 : HW_WEST.x2 - ROAD_G, xb = xa + ROAD_G;
    DOORS.push({
      flag, cost: HW_DOOR_COST, target, dest,
      slab: cspec({ x1: xa, x2: xb, y1: HW_EAST.y1, y2: HW_EAST.y2, z1: TOP2, z2: TOP2 + HW_H }),
      trig: cspec({ x1: xa - 40, x2: xb + 40, y1: HW_EAST.y1, y2: HW_EAST.y2, z1: TOP2, z2: TOP2 + 128 }),
      org: cpt((xa + xb) / 2, (HW_EAST.y1 + HW_EAST.y2) / 2, TOP2 + 40), off: [CM * 60, 0, 0],
    });
  }
}
if (DESCENT) DOORS.push({
  flag: 'tod_fall', cost: FALL_GATE_COST, target: 'tod_crown_door',
  dest: 'the Causeway',
  slab: cspec({ x1: -GATE_HALF, x2: GATE_HALF, y1: HS, y2: HS + HWALL, z1: TOP2, z2: TOP2 + GATE_H }),
  trig: cspec({ x1: -GATE_HALF, x2: GATE_HALF, y1: HS - 40, y2: HS + HWALL + 40, z1: TOP2, z2: TOP2 + 128 }),
  org: cpt(0, HS + HWALL / 2, TOP2 + 40), off: [0, CM * 60, 0],
});
// v17.29 — EVERY GROUND-LEVEL DOOR IS THE TOWER DOOR'S BLUE (user 2026-09-04:
// "We can make all the doors on first floor blue like the tower door").
//
// The power-room and teleport-bay doors had no `slabMat` at all, so they fell
// through to MAT.door (green) while the lap-1 door beside them took the district
// hue. DERIVED from the same expression the lap doors use — `edgeMatOf(0)` is
// literally what floor 1's door resolves to — rather than a literal
// `blue_tinted_edge`, so if district 1 is ever re-hued these follow it instead
// of quietly becoming the odd ones out. Under FACELIFT=false the tower door is
// green, and "like the tower door" then correctly means green, so the ternary is
// the whole rule.
//
// NOTE this drops the green/blue split Nikolai proposed alongside the black
// floor ("only leave the green buyable doors and blue buyable door"). Deliberate,
// on the user's call: the three ground doors are in three different walls in
// three different rooms, so they were never told apart by hue, and against the
// v17.28 black floor a single saturated blue is the strongest "buy me" the pack
// can draw. MAT.door still owns the ROOF door, the causeway gate and the crown
// door — none of them are on floor 1, and none of them change here.
const GROUND_DOOR_MAT = doorMatOf(0);   // matte blue — v18.99g
// POWER ROOM (user 2026-08-20): a longish hallway in the base SE corner —
// buyable door at the west end, power switch behind it at the east end.
// Interior x[280,540] y[-540,-420]; south/east sides are the arena walls,
// north side is a new wall, the west face IS the door slab.
DOORS.push({
  flag: 'enter_power', cost: POWER_DOOR_COST, target: 'tod_door_power',
  dest: 'the Power Room', slabMat: GROUND_DOOR_MAT,
  slab: { x1: 260, x2: 280, y1: -540, y2: -420, z1: 0, z2: 128 },
  trig: { x1: 220, x2: 320, y1: -540, y2: -420, z1: 0, z2: 128 },
  clip: { x1: 260, x2: 280, y1: -540, y2: -420, z1: 128, z2: 600 },
  org: [270, -480, 40], off: [60, 0, 0],
});
// THE UNDERCITY'S TWO DOORS (docs/158). enter_conduit sits in the wall the
// Vault shares with the Conduit (the lateral door); enter_base fills the exit
// gap in the arena's WEST wall at the top of the shaft (the "up" door). Both
// carry the ground-door blue. Trigger offsets 40: 20u past each face.
DOORS.push({
  flag: 'enter_conduit', cost: CONDUIT_DOOR_COST, target: 'tod_door_conduit',
  dest: 'the Conduit', slabMat: GROUND_DOOR_MAT,
  slab: { x1: CONDUIT_DOOR_X - 80, x2: CONDUIT_DOOR_X + 80, y1: VT_Y2, y2: VT_Y2 + WALL, z1: UC_Z, z2: UC_Z + 128 },
  trig: { x1: CONDUIT_DOOR_X - 80, x2: CONDUIT_DOOR_X + 80, y1: VT_Y2 - 40, y2: VT_Y2 + WALL + 40, z1: UC_Z, z2: UC_Z + 128 },
  clip: { x1: CONDUIT_DOOR_X - 80, x2: CONDUIT_DOOR_X + 80, y1: VT_Y2, y2: VT_Y2 + WALL, z1: UC_Z + 128, z2: UC_TOP },
  org: [CONDUIT_DOOR_X, VT_Y2 + WALL / 2, UC_Z + 40], off: [0, 40, 0],
});
DOORS.push({
  flag: 'enter_base', cost: BASE_DOOR_COST, target: 'tod_door_base',
  dest: 'the Tower Plaza', slabMat: GROUND_DOOR_MAT,
  slab: { x1: -(ARENA + WALL), x2: -ARENA, y1: WEXIT_Y[0], y2: WEXIT_Y[1], z1: 0, z2: 128 },
  trig: { x1: -(ARENA + WALL) - 40, x2: -ARENA + 40, y1: WEXIT_Y[0], y2: WEXIT_Y[1], z1: 0, z2: 128 },
  clip: { x1: -(ARENA + WALL), x2: -ARENA, y1: WEXIT_Y[0], y2: WEXIT_Y[1], z1: 128, z2: 600 },
  org: [-(ARENA + WALL / 2), SHAFT_CY, 40], off: [40, 0, 0],
});
// THE FOUR WORKSHOP DOORS, one per plaza wall, from the WINGS table.
for (const w of WINGS) {
  const F = wingFrame(w);
  const [ox, oy] = F.pt(ARENA + WALL / 2, w.dc);
  DOORS.push({
    flag: `enter_wing_${w.key}`, cost: WING_DOOR_COST, target: `tod_door_wing_${w.key}`,
    dest: w.dest, slabMat: GROUND_DOOR_MAT,
    slab: F.rect(ARENA, WU0, w.dc - 80, w.dc + 80, 0, 128),
    trig: F.rect(ARENA - 40, WU0 + 40, w.dc - 80, w.dc + 80, 0, 128),
    clip: F.rect(ARENA, WU0, w.dc - 80, w.dc + 80, 128, 600),
    org: [ox, oy, 40], off: [F.out[0] * 40, F.out[1] * 40, 0],
  });
}
// docs/158 — NO TWO DOOR TRIGGER SPHERES MAY OVERLAP (r96 each, at org +- off),
// and none may swallow a ground-level use trigger. Checked over every ground
// door against each other; the crate/inducer/station spheres are asserted in
// their own blocks. A failure here is a wall-table mistake, never a script one.
const DOOR_SPHERES = [];   // every ground door's two r96 use spheres, for the inducer check beside INDUCER_TRIG
{
  const ground = DOORS.filter(d => d.org[2] < 500);
  const spheres = [];
  for (const d of ground) for (const s of [1, -1])
    spheres.push({ flag: d.flag, x: d.org[0] + s * d.off[0], y: d.org[1] + s * d.off[1], z: d.org[2] + s * d.off[2] });
  // Only pairs involving a docs/158 door are gated: enter_lap1's south sphere
  // (336,-316) and enter_power's east sphere (330,-480) have shipped 28u inside
  // each other since v10 and are the user's to revisit, not this assert's.
  const NEW_DOORS = new Set(['enter_conduit', 'enter_base', ...WINGS.map(w => `enter_wing_${w.key}`)]);
  for (let i = 0; i < spheres.length; i++) for (let j = i + 1; j < spheres.length; j++) {
    const a = spheres[i], b = spheres[j];
    if (a.flag === b.flag) continue;
    if (!NEW_DOORS.has(a.flag) && !NEW_DOORS.has(b.flag)) continue;
    if (Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z) < 192)
      throw new Error(`door triggers overlap: ${a.flag} (${a.x},${a.y}) vs ${b.flag} (${b.x},${b.y})`);
  }
  // the base crate (r72 at CRATE_TRIG_OUT in front of its origin); the inducer
  // is checked beside its own constants (they are defined further down)
  const cf = crateFront(BASE_CRATE.yaw);
  const crateT = { x: BASE_CRATE.org[0] + cf[0] * CRATE_TRIG_OUT, y: BASE_CRATE.org[1] + cf[1] * CRATE_TRIG_OUT, r: CRATE_TRIG_R };
  for (const s of spheres)
    if (Math.hypot(s.x - crateT.x, s.y - crateT.y) < 96 + crateT.r)
      throw new Error(`door trigger ${s.flag} (${s.x},${s.y}) overlaps the base crate trigger (${crateT.x},${crateT.y}) r${crateT.r}`);
  DOOR_SPHERES.push(...spheres);
  // every ground riser stays outside every door sphere — for the docs/158 doors
  // and the docs/158 zones; base_zone's (336,-336) riser has deliberately stood
  // 20u from enter_lap1's south sphere since v10 (the "stuck at a wall" fix)
  const NEW_ZONES = /^(vault|conduit|wing_)/;
  for (const zn of ZONES) for (const [rx, ry, rz] of zn.risers) for (const s of spheres)
    if ((NEW_DOORS.has(s.flag) || NEW_ZONES.test(zn.name)) && Math.hypot(rx - s.x, ry - s.y, rz - s.z) < 96)
      throw new Error(`${zn.name} riser (${rx},${ry},${rz}) rises inside door trigger ${s.flag}`);
}
for (const d of DOORS) {
  ent(`door trigger ${d.flag}`, [
    '{', `guid "${guid()}"`,
    kv('classname', 'trigger_use'),
    kv('targetname', 'zombie_door'),
    kv('target', d.target),
    // CONSTANT, NOT d.cost — the 250-triggerstring cap (2026-08-30).
    // Stock _zm_blockers::door_init runs as a system PRELOAD (REGISTER_SYSTEM_EX
    // -> shared.gsh's __func_init_preload -> system::run_pre_systems, called from
    // CodeCallback_PreInitialization, i.e. BEFORE the map's main() executes a
    // single line) and ends in set_hint_string(self,"default_buy_door",cost) ->
    // SetHintString(&"ZOMBIE_BUTTON_BUY_OPEN_DOOR_COST", cost). That mints ONE
    // PERMANENT BG-cache 'triggerstring' slot per DISTINCT cost, and the cache
    // caps at 250 for the whole match. Per-lap pricing put 41 distinct values in
    // here, so stock burned 41 slots on prompts nobody ever sees — _tod_doors.gsc
    // TriggerEnable(false)s all 53 of those triggers a second later.
    //
    // SAFE BECAUSE THIS VALUE IS DEAD DATA: _tod_doors.gsc seeds cost=1000 from
    // this key and then overrides it from the GENERATED _tod_door_data.gsc
    // (info.cost WINS, v9.41 — that is what keeps a price change -GscOnly), and
    // all 53 rows define info.cost. A door with no data row returns before it
    // ever gets a trigger. 1000 matches the GSC's own fallback exactly.
    //
    // The REAL per-door price is emitted further down as `info.cost = ${d.cost}`
    // in _tod_door_data.gsc. Do not "fix" this line to match it.
    kv('zombie_cost', '1000'),
    kv('script_flag', d.flag),
    matBrush(d.trig.x1, d.trig.x2, d.trig.y1, d.trig.y2, d.trig.z1, d.trig.z2, 'trigger'),
    '}',
  ]);
  ent(`door slab ${d.flag}`, [
    '{', `guid "${guid()}"`,
    kv('classname', 'script_brushmodel'),
    kv('targetname', d.target),
    kv('script_vector', '0 0 130'),
    kv('script_transition_time', '1.5'),
    matBrush(d.slab.x1, d.slab.x2, d.slab.y1, d.slab.y2, d.slab.z1, d.slab.z2, d.slabMat || MAT.door),
    // v16.13 — THE ANTI-VAULT CLIP RIDES IN THE SLAB ENTITY (user 2026-09-01:
    // "above doors there are invisible walls so if they jump down stairs
    // sometimes they hit an invisible wall above where the door would be").
    // It used to be a WORLDSPAWN brush from the slab's top (b+128) to b+600,
    // which is permanent: it kept stopping players for the rest of the match
    // after the door was bought. A jump down the flight toward the doorway
    // puts the head at ~135-150 above the door's floor as it crosses the
    // door line (12u treads, 39u jump, 72u eye) — straight into a brush whose
    // bottom is 128 up. As a second brush of the script_brushmodel it is
    // Solid + DisconnectPaths while the door is shut (the vault guard is
    // intact — a shut door still needs it, a 128 slab is jumpable with a
    // slide-jump under the ATHLETE dvar), slides into the core with the slab
    // (all solid core above every doorway), and goes NotSolid with it. No
    // script change: every open path already Hide/NotSolid/ConnectPaths the
    // entity. The rail-band column it also covered (x to PX+PARA) is under the
    // parapets' own rail caps, so nothing is lost there. Same fix on the
    // spire's 100 doors (section 6e), the roof, power and bay doors.
    // docs/160: the Fall gate has no clip (its lintel is solid to the cornice).
    ...(d.clip ? [matBrush(d.clip.x1, d.clip.x2, d.clip.y1, d.clip.y2, d.clip.z1, d.clip.z2, MAT.clip)] : []),
    '}',
  ]);
  if (d.gate) {   // v16.11 facelift §2 — see the DOORS block
    const g = d.gate;
    addBox(`door gate post ${d.flag}`, g.post.x1, g.post.x2, g.post.y1, g.post.y2, g.post.z1, g.post.z2, g.mat);
    addBox(`door gate lintel ${d.flag}`, g.lintel.x1, g.lintel.x2, g.lintel.y1, g.lintel.y2, g.lintel.z1, g.lintel.z2, g.mat);
    addBox(`door gate sill ${d.flag}`, g.sill.x1, g.sill.x2, g.sill.y1, g.sill.y2, g.sill.z1, g.sill.z2, d.slabMat);
  }
}

// THE HAVEN BARRIERS (docs/202 v4, user 2026-10-03: "bullets cannot go in or outside
// the dome. Until its a safe zone. Then bullets can shoot through and kill things
// both ways"): one script_brushmodel per haven floor, a shell of convex brushes on
// the field's sphere (tools/haven_layout.js barrierBrushes) in tod_haven_barrier
// (tools/haven/make_dome.py: the stock weapon clip + missile clip + no penetration,
// nonsolid to bodies). _tod_haven.gsc finds it by name (haven_barrier_name), keeps it
// NotSolid until the dome boots, Solid while the haven is corrupted, NotSolid from
// the cleanse. The navmesh skips the classname (navmesh.json), so it carves nothing.
for (const L of [...BREATHER_LAPS].sort((a, b) => a - b)) {
  const m = (L - 1) * LAP_RISE + FLIGHT_RISE;
  const brushes = HAVEN.barrierBrushes(m).map(b => polyBrushText(`lap${L} haven ${b.label}`, b.verts, b.faces, HAVEN.BARRIER.mat));
  ent(`lap${L} haven barrier`, [
    '{', `guid "${guid()}"`,
    kv('classname', 'script_brushmodel'),
    kv('targetname', `tod_haven_barrier_${L}`),
    ...brushes,
    '}',
  ]);
}

// THE ENCLOSED HALLWAY'S MIDDLE DOOR (2026-09-25): "middle will just be a
// locked door until power is on". Not a DOORS row — nobody buys it: a
// script_brushmodel across the bridge corridor's north end, Solid +
// DisconnectPaths from init, opened by _tod_fall::power_switch_on (Hide +
// NotSolid + ConnectPaths, the doors' own open). It fills the corridor to the
// roof, so it needs no anti-vault clip.
if (CW_CUT && DESCENT) {
  const bd = cspec({ x1: HW_SOUTH.x1, x2: HW_SOUTH.x2, y1: HW_SOUTH.y2 - ROAD_G, y2: HW_SOUTH.y2, z1: TOP2, z2: TOP2 + HW_H });
  ent('crown bridge door', [
    '{', `guid "${guid()}"`,
    kv('classname', 'script_brushmodel'),
    kv('targetname', 'tod_crown_bridge_door'),
    matBrush(bd.x1, bd.x2, bd.y1, bd.y2, bd.z1, bd.z2, MAT.door),
    '}',
  ]);
}

// THE CAUSEWAY GATE (v10.11) — the road is CUT until EXTRACTION is bought.
// Same slab contract as every buyable door here: _tod_finale makes it
// Solid + DisconnectPaths at init and Hide + NotSolid + ConnectPaths on the
// buy, so the navmesh is genuinely severed and the horde cannot path the road
// early either. Emitted HERE, not in section 5c, because entities[] does not
// exist yet up there.
{
  const g = cspec({
    x1: -CW_HALF - PARA, x2: CW_HALF + PARA,
    y1: TER_Y2, y2: TER_Y2 + 24, z1: TOP2, z2: TOP2 + 256,
  });
  ent('causeway gate', [
    '{', `guid "${guid()}"`,
    kv('classname', 'script_brushmodel'),
    kv('targetname', 'tod_causeway_gate'),
    matBrush(g.x1, g.x2, g.y1, g.y2, g.z1, g.z2, MAT.door),
    '}',
  ]);
}
// THE CROWN DOOR (v10.26) — the citadel's own gate, and the OPPOSITE contract to
// the causeway gate above. That one starts SEALED and opens when you pay; this
// one starts OPEN (you have to be able to walk in) and SLAMS SHUT when the
// hold-out begins, sealing the party inside for the final fight.
//
// It fills the gate opening EXACTLY: x +-GATE_HALF is the hole the south wall
// leaves between its two gate posts, and GATE_H is the lintel height above it
// ('crown gate lintel' fills WZ2 down to TOP2+GATE_H). So this brush is the
// missing 256x256 rectangle and nothing else — it cannot foul a post or a rail.
//
// _tod_finale::crown_door_init makes it Hide + NotSolid + ConnectPaths at map
// start (open), and crown_door_close() does Show + Solid + DisconnectPaths.
// THE CLOSE IS DEFERRED UNTIL AFTER THE PARTY IS TELEPORTED TO THE HALL CENTRE
// — a brush that solidifies on top of a player is the crush case the door slabs
// have always been careful about, and here it would land on somebody standing
// in the doorway by definition.
// docs/160 — UNDER DESCENT THE CROWN DOOR IS A ROW OF THE DOORS TABLE (flag
// `tod_fall`, the same targetname, the same brush): the buyable Fall gate,
// emitted by the door loop above with its dead trigger_use. This standalone
// emission is kept ONLY for the climb layout (DESCENT false), where the
// finale still owns it.
if (!DESCENT) {
  const cd = cspec({
    x1: -GATE_HALF, x2: GATE_HALF,
    y1: HS, y2: HS + HWALL, z1: TOP2, z2: TOP2 + GATE_H,
  });
  ent('crown door', [
    '{', `guid "${guid()}"`,
    kv('classname', 'script_brushmodel'),
    kv('targetname', 'tod_crown_door'),
    matBrush(cd.x1, cd.x2, cd.y1, cd.y2, cd.z1, cd.z2, MAT.door),
    '}',
  ]);
}
// THE LANE LOTTERY SEALS (v12.13, docs/41 §B1) — five slabs, one across each
// branch lane's SOUTH mouth just past its fork landing. ALL start OPEN
// (_tod_finale::lane_seals_init does Hide+NotSolid+ConnectPaths at init); at
// the extraction buy the finale rolls ONE lane per fork and seals it
// (Show+Solid+DisconnectPaths) BEFORE the causeway gate opens, so no player
// can be standing in a slab when it solidifies (they are all behind the
// still-solid causeway gate; the dev harness opens that gate early, so the
// script also occupancy-checks before sealing). Same contract, same material,
// same visual grammar as the causeway gate above. SOUTH mouth only: every lane
// stays path-connected via its merge, so nothing — player or zombie — can be
// stranded inside a sealed lane; it is a dead end you walk back out of.
// Indices are load-bearing (_tod_finale rolls 0-1 for fork 1, 2-4 for fork 2):
//   0 f1 W ridge | 1 f1 E broken stair | 2 f2 W undercroft | 3 f2 C plank | 4 f2 E weave
// docs/163 THE CUT: the five lanes are gone, so are their seals. The parked
// finale's lane_seals_init finds no tod_lane_seal_0 and leaves the lottery off
// ("a road with every lane open is survivable, a script error is not").
if (!CW_CUT) {
  const seals = [
    ['f1 ridge',      LX[0],  LX[1],  cwY[2]],
    ['f1 bstair',     EX[0],  EX[1],  cwY[2]],
    ['f2 undercroft', LX[0],  LX[1],  cwY[6]],
    ['f2 plank',      PX_[0], PX_[1], cwY[6]],
    ['f2 weave',      EX[0],  EX[1],  cwY[6]],
  ];
  seals.forEach(([tag, x1, x2, y], i) => {
    // z1 is TOP2-32, not TOP2: the two DESCENDING lanes (broken stair, under-
    // croft) drop 16 within their first tread, so a slab based at TOP2 would
    // hover with a 16u see-through slot beneath it. 32 buries the base inside
    // the tread/under-glow brushes on every lane (deck slab is 16, glow 24).
    const s = cspec({ x1, x2, y1: y, y2: y + 24, z1: TOP2 - 32, z2: TOP2 + 256 });
    ent(`lane seal ${tag}`, [
      '{', `guid "${guid()}"`,
      kv('classname', 'script_brushmodel'),
      kv('targetname', `tod_lane_seal_${i}`),
      matBrush(s.x1, s.x2, s.y1, s.y2, s.z1, s.z2, MAT.door),
      '}',
    ]);
  });
}
// docs/163 THE JUMP PAD — two markers. lint_tod_geometry reads them as the ONE
// one-way edge of its reachability flood (launch -> landing); Radiant shows
// them; the game reads the same numbers from _tod_crown_data.gsc (section 7),
// never these structs. script_struct: no runtime gentity, on navmesh.json's
// exclusion list (carves nothing), and no script asks for these targetnames.
// THE CROWN'S STUB IS A DETACHED REGION NOW, so it gets its own navmesh seeds
// (the hall's four riser seeds would flood it through the open gate today —
// "a region the flood merely HAPPENS to reach" is exactly the case the seed
// rule above names): one on the launch deck beside the pad, one in the
// crown's throat on the approach.
if (CW_CUT) {
  const [lx, ly, lz] = cpt(JP_PAD[0], JP_PAD[1], TOP2);
  const [tx, ty, tz] = cpt(JP_LAND[0], JP_LAND[1], TOP2);
  ent('jump pad launch', ['{', `guid "${guid()}"`, kv('classname', 'script_struct'),
    kv('origin', `${lx} ${ly} ${lz}`), kv('targetname', 'tod_jumppad_launch'), kv('target', 'tod_jumppad_land'),
    kv('radius', `${JP_PAD_R}`), kv('_color', '1 0.85 0.35'), '}']);
  ent('jump pad landing', ['{', `guid "${guid()}"`, kv('classname', 'script_struct'),
    kv('origin', `${tx} ${ty} ${tz}`), kv('targetname', 'tod_jumppad_land'),
    kv('radius', '160'), kv('_color', '0.35 0.9 1'), '}']);
  navSeed('jump pad launch deck', ...cpt(JP_PAD[0], JP_LAUNCH_Y1 + 60, TOP2 + 2));
  navSeed('hallway junction', ...cpt(0, (HW_JUNC.y1 + HW_JUNC.y2) / 2 - 120, TOP2 + 2));
  navSeed('hallway power room', ...cpt((HW_POWER.x1 + HW_POWER.x2) / 2 - 60, (HW_POWER.y1 + HW_POWER.y2) / 2, TOP2 + 2));
  navSeed('hallway teleporter room', ...cpt(HW_TELE_ORG[0], HW_TELE.y1 + 80, TOP2 + 2));
  navSeed('jump pad crown throat', ...cpt(0, cwY[8] + 400, TOP2 + 2));
}
// Transit markers are exported from the SAME rows as the runtime routes.
// Validators inspect these emitted entities; they are not ordinary walk links.
for(const row of TRANSIT_ROUTES) {
  ent(`transit source ${row.id}`,['{',`guid "${guid()}"`,kv('classname','script_struct'),
    kv('targetname','tod_transit_source'),kv('script_string',row.id),kv('origin',row.src.join(' ')),
    kv('target',`tod_transit_arrival_${row.id}`),kv('script_flag',row.lock),'}']);
  ent(`transit arrival ${row.id}`,['{',`guid "${guid()}"`,kv('classname','script_struct'),
    kv('targetname',`tod_transit_arrival_${row.id}`),kv('origin',row.dst.join(' ')),
    kv('script_noteworthy',row.zone),'}']);
}
navSeed('transit bay arrival',...cpt(...TRANSIT.ARRIVAL,TOP2+2));
// docs/196: one seed per region of the hall (the crossing, each gate's arm) —
// TRANSIT.SEEDS; the arrival seed above covers the nave.
TRANSIT.SEEDS.slice(1).forEach(([x,y],i)=>navSeed(`transit bay region ${i+1}`,...cpt(x,y,TOP2+2)));
navSeed('transit return apron',0,-800,2);

// --- prefabs: base kit + the ladder up the tower -----------------------------
function prefab(label, model, x, y, z, yaw, scriptString) {
  // v13.6: a model containing '/' is a path under _prefabs/ (e.g.
  // 'ALXS/alxs_cwpap_prefab.map'); a bare name keeps the legacy zm_core home.
  const prefabPath = model.includes('/') ? '_prefabs/' + model : '_prefabs/zm/zm_core/' + model;
  const lines = [
    '{', `guid "${guid()}"`, kv('classname', 'misc_prefab'),
    kv('angles', `0 ${yaw} 0`), kv('model', prefabPath), kv('origin', `${x} ${y} ${z}`),
  ];
  if (scriptString) lines.push(kv('script_string', scriptString));
  lines.push('}');
  ent(label, lines);
}
const PERK_LOC = 'zclassic_perks_start_room';
// Base arena (z=0)
// POWER ROOM hallway v2 (user 2026-08-20: "5x longer"): the SE-corner
// corridor now punches THROUGH the arena's east wall and runs outside to
// x=1620 — door at x=280, switch at x~1596, corridor ~1340u (~5.2x the v1).
// Interior leg: arena S wall + the north wall below; exterior leg: own
// floor/walls/clips under the (widened) skybox.
addBox('power room north wall', 280, 540, -420, -400, 0, BASE_WALL_H, MAT.baseWall);
addBox('power hall floor', 560, 1640, -560, -400, -SLAB, 0, MAT.baseFloor);
addBox('power hall wall N', 560, 1620, -420, -400, 0, BASE_WALL_H, MAT.baseWall);
addBox('power hall wall S', 560, 1620, -560, -540, 0, BASE_WALL_H, MAT.baseWall);
addBox('power hall wall E', 1620, 1640, -560, -400, 0, BASE_WALL_H, MAT.baseWall);
addBox('power hall clip N', 560, 1640, -420, -400, BASE_WALL_H, 800, MAT.clip);
addBox('power hall clip S', 560, 1640, -560, -540, BASE_WALL_H, 800, MAT.clip);
addBox('power hall clip E', 1620, 1640, -560, -400, BASE_WALL_H, 800, MAT.clip);
// Power switch at the FAR east end, BACK to the east cap, FACING WEST down
// the corridor (yaw 270 — model front is local -Y, the live-verified vending
// convention; the old yaw-180 at the core's south face pointed it INTO the
// wall, untriggerable).
// FLUSH TO THE WALL (user 2026-08-21 "not up against the wall, some space in
// between"): the prefab's body clip spans local y[-8,+7] (back = +7) and yaw
// 270 maps local +Y onto world +X, so the back lands at origin.x+7. The east
// cap's inner face is x=1620 -> origin 1613 (the old 1596 left a 17u gap).
// The use trigger (local y[-24,-5]) ends up at x[1589,1608], still in the hall.
prefab('base power switch', 'power_switch.map', 1613, -480, 0, 270);
// hallway lights (the exterior leg is outside every arena light's radius)
light('power hall light 1', 800, -480, 100, '0.3 0.9 1', 380, 6, 1);
light('power hall light 2', 1200, -480, 100, '0.3 0.9 1', 380, 6, 1);
light('power hall light 3', 1560, -480, 100, '0.3 0.9 1', 380, 6, 1);

// ---------------------------------------------------------------------------
// POWER WAYFINDING DECALS (v18.99, user: "I downloaded a power switch decal ...
// decals that we can add to the power hallway, and maybe one decal or two right
// outside the door. So players know where to turn on power, and they'll see it
// and they know to open the door").
//
// THE PACK IS MAP 1'S AND IT IS ALREADY INSTALLED IN THE SHARED TOOLS ROOT
// (`model_export/codimages/arrow_coldwar_dogcanary/*.gdt` + the
// `_modelos_dogcanary` pngs, there since 2026-07-12), so this map pays nothing
// to use it. Materials, READ OUT OF THAT GDT rather than guessed from the
// numbering — the material order and the image order do NOT line up:
//     arrow_power_coldwar1 = the word POWER        arrow_power_coldwar4 = LEFT arrow
// (the other nine are a curved arrow, an up-right arrow, ENGINE, VENT, STAIRS,
// Assemble, PASSWORD, Family, STOLEN.) They are `usage decal` /
// `lit_emissive_scroll_transparent` at scaleRGB 16 — they GLOW, which is the
// point in a hallway lit by three cyan point lights.
// NO ZONE LINE IS NEEDED: world-geometry materials ride in through the
// compiled BSP, which is why map 1 ships these with no `material,` row either.
// It is still a FULL build — the .map changes.
//
// THE RECIPE IS MAP 1'S PROVEN CHALK-MESH, NOT A BRUSH: a flat quad
// DECAL_PROUD off the wall face with `contents nonColliding`, texture mapped
// once (u 0 -> 1024 across the columns, v 0 -> -1024 up the rows). A brush
// would give a picture collision, a navmesh cut and six textured faces.
//
// WINDING DECIDES WHICH WAY THE ART FACES, and map 1 paid for the rule:
// normal = u_dir x v_dir with v_dir = +z, so
//     -y normal -> columns Xmin->Xmax        +y normal -> columns Xmax->Xmin
//     -x normal -> columns Ymax->Ymin        +x normal -> columns Ymin->Ymax
// with u0 always the VIEWER'S LEFT and the texture unmirrored. Consequence
// that decides every arrow below: on a +y-normal wall the viewer faces SOUTH,
// so texture-left is EAST — which is why the LEFT arrow is the one that points
// a player east, down this hall, at the switch. Every decal here is on a
// +y-normal face for exactly that reason.
const DECAL_PROUD = 2;
const DECAL_Z1 = 32, DECAL_Z2 = 96;   // map 1's band on a 0..128 wall
const DECAL_W = 64;                   // map 1's size; the sources are square 512s
const DECAL_TAB = String.fromCharCode(9);   // map 1's vertex rows are tab-indented
function decalMesh(label, mat, cols) {
  // cols = [[ax, ay], [bx, by]] in draw order; each column is bottom then top.
  const [c0, c1] = cols;
  const v = (x, y, z, u, w) => `${DECAL_TAB}v ${x} ${y} ${z} t ${u} ${w}`;
  worldBrushes.push({ label, text: [
    '{',
    ` guid "${guid()}"`,
    ' mesh',
    ' {',
    ' contents nonColliding;',
    ' toolFlags;',
    `  ${mat}`,
    '  lightmap_gray',
    '  2 2 0 8',
    '  (',
    v(c0[0], c0[1], DECAL_Z1, 0, '-0 -1.0001428 -6.7082205'),
    v(c0[0], c0[1], DECAL_Z2, 0, '-1024 -0.99985725 -9.0415535'),
    '  )',
    '  (',
    v(c1[0], c1[1], DECAL_Z1, 1024, '-0 0.87485725 -6.7084455'),
    v(c1[0], c1[1], DECAL_Z2, 1024, '-1024 0.87514287 -9.0417786'),
    '  )',
    ' }',
    '}',
  ].join('\n') });
}
// A decal on a wall face at constant y whose normal points +y (the viewer is
// north of it, facing south). Columns run Xmax -> Xmin per the rule above.
function decalSouthWall(label, mat, faceY, xCentre) {
  const x1 = xCentre - DECAL_W / 2, x2 = xCentre + DECAL_W / 2, y = faceY + DECAL_PROUD;
  decalMesh(label, mat, [[x2, y], [x1, y]]);
}
const DECAL_POWER = 'arrow_power_coldwar1';   // the word POWER
const DECAL_EAST  = 'arrow_power_coldwar4';   // LEFT arrow = EAST on a +y face
// OUTSIDE THE DOOR (the two the user asked for). The door slab is x[260,280];
// west of it the arena's south wall runs x[160,260] (the teleport-bay opening
// eats everything west of 160), and the power room's north wall x[280,540]
// faces the arena across the corridor. One on each, so the pair reads from the
// arena floor: the word on the long wall you can see from the core, the arrow
// at the door mouth pointing into it.
decalSouthWall('power decal arena POWER', DECAL_POWER, -400, 408);   // power room N wall, faces the arena
decalSouthWall('power decal arena arrow', DECAL_EAST,  -540, 212);   // arena S wall, beside the door
// INSIDE THE HALL — three arrows down the south wall, then the word just short
// of the switch at x=1613. All on the same face the player has on their right
// the whole walk east. (The base teddy bear sits at x=1614 on this wall; the
// last decal ends at 1512, clear of it.)
decalSouthWall('power decal hall arrow 1', DECAL_EAST,  -540, 332);    // interior leg, just past the door
decalSouthWall('power decal hall arrow 2', DECAL_EAST,  -540, 792);
decalSouthWall('power decal hall arrow 3', DECAL_EAST,  -540, 1152);
decalSouthWall('power decal hall POWER',   DECAL_POWER, -540, 1480);   // the switch is at 1613

// BEGIN DEALER PRESENCE: three small fixed panels on existing opaque walls.
// No collision, lights, entity spawns or runtime animation. Shared native
// geometry and matched Blender reviews: tools/dealer_presence/layout.js.
require('./dealer_presence/layout').emit({worldBrushes,guid,CM,TOP2,CORE,LAP_RISE,FLIGHT_RISE});
// END DEALER PRESENCE

// ---------------------------------------------------------------------------
// Single bottom-floor crown return: a railed open apron, no room or buy door.
// ---------------------------------------------------------------------------
TRANSIT.base(transitBox, RAIL_VIS_H, RAIL_H + RAIL_CAP_H);
light('tp bay return light',0,-800,180,'0.65 0.82 1',280,8.5,1);

// v18.99e/f/g THE RAMPAGE INDUCER STAND (user 2026-09-13: players "don't know
// what it's for" — the wall breaker read as a power switch; then "move it into
// the main room ... on the wall across from QR in spawn"; then, on seeing it,
// "the inducer is way too high to even trigger"). The switch is the BO6 aether
// canister (t10_zm_aether_canister, 12 x 12 x 29 — decoded from the
// xmodel_bin), knee-high on the floor, so it stands on this plinth against the
// BASE ARENA's SOUTH wall — the wall across from the pinned Quick Revive pad
// (-75, 511). Straight across from QR is the teleport-bay doorway (x +-160), so
// the plinth sits on the free wall run just WEST of it, between the -420 and
// -140 pilaster slots (the -140 one is skipped at the door end).
//
// ⚠️ THREE THINGS WENT WRONG IN v18.99e/f AND ALL THREE ARE FIXED HERE:
//   1. HEIGHT — the plinth was 72 tall, which puts a 29-tall device's BASE
//      above a 60-unit eye line. INDUCER_PLINTH_H is 32 now: waist-high pedestal,
//      device top at 61, dead on the eye line.
//   2. THE DEAD TRIGGER — the v18.99f trigger origin sat at the device's own
//      x/y, i.e. INSIDE this brush, and a use-trigger whose ORIGIN is inside any
//      solid never prompts (memory trigger-origin-under-decal; paid for by the
//      extraction obelisk, the hall crate and the crown altar before this). The
//      trigger now sits INDUCER_TRIG_OUT in FRONT of the plinth's north face on
//      open floor — the ammo crate / station grammar (CRATE_TRIG_OUT 56).
//   3. IT READ AS FLOATING — MAT.baseColumn is plain `dark_blue`, a black tile
//      with a dim grid, so the plinth vanished against a black floor and the
//      device looked stuck to the wall in mid-air. MAT.pilaster (plain `cyan`)
//      is the arena's own accent for "this is a fixture", and plain colours are
//      BLOCK to the geometry lint at ANY height, so a short plinth is safe.
//      (Both earlier lint failures were the 1u `baseInlay` CAP — a `_tinted`
//      DECK raised off the floor — never the plinth itself.)
//
// Clearances on the south band: enter_tpbay trigger box x[-160,160] y[-600,-500]
// (48u from this trigger's rim in x), base station trigger (0,-360) r64 290u
// away, dog spawn (0,-470) 280u, SW riser (-470,-470) 193u, spawn structs 370u+.
// EVERY NUMBER BELOW IS EMITTED into _tod_breather_data.gsc as base_inducer_org
// / _trig / _yaw and READ BACK by _tod_rampage.gsc, so the brush and the script
// cannot drift — the same no-drift contract the base ammo crate rides.
const INDUCER_X       = -264;   // docs/158: -280 -> -264 so its r96 trigger clears the South Workshop door's inner sphere (-460,-530) by 4u; the bay door trigger box (x>=-160) is still 8u clear
const INDUCER_PLINTH_H = 0;     // v18.99i: FLOOR-MOUNTED, no pedestal
const INDUCER_PLINTH_D = 48;    // depth out from the wall (y -540 .. -492)
// v18.99k (user: "it should be kind of in a radius all around it"): the trigger
// is centred ON the device and reaches every side. INDUCER_TRIG_OUT is gone.
const INDUCER_TRIG_R   = 96;
const INDUCER_YAW      = 90;    // local +X points north, into the arena
const INDUCER_FACE_Y  = -ARENA + INDUCER_PLINTH_D;              // -492
const INDUCER_ORG     = [INDUCER_X, -ARENA + INDUCER_PLINTH_D / 2];   // on the plinth's centre
const INDUCER_TRIG    = [INDUCER_X, INDUCER_ORG[1]];   // ON the device; script lifts it 40 above the prop
// v18.99i (user: "I don't really want it on a... an object, so we can just put
// it on the floor") - NO PEDESTAL. The device stands on the arena floor, which
// is also how BO6 places it. INDUCER_PLINTH_H is 0 now and nothing is cut here;
// INDUCER_PLINTH_D survives only as the depth the device stands off the wall.
// THE ASSERT THAT CLOSES note 2 FOR GOOD: the trigger origin must be clear of
// the plinth in plan. Nothing else stands on this wall run, and the trigger is
// lifted 40u off the floor in script, so plan clearance is the whole test.
// The pedestal is gone, so the only solid that can swallow this trigger origin
// is the arena's south WALL. Keep the check: the dead-trigger trap is why this
// whole block is generator-owned, and a future nudge of INDUCER_X/_TRIG_OUT is
// exactly how it would come back.
if (INDUCER_TRIG[1] <= -ARENA)
  throw new Error('rampage inducer trigger origin is inside the arena south wall — the dead-trigger trap');
if (Math.abs(INDUCER_TRIG[0]) - INDUCER_TRIG_R < -TPB_DOOR - 0
    && INDUCER_TRIG[1] - INDUCER_TRIG_R < -500 && INDUCER_TRIG[0] + INDUCER_TRIG_R > -TPB_DOOR)
  throw new Error('rampage inducer trigger overlaps the enter_tpbay door trigger');
// docs/158: and against EVERY ground door's use spheres (the South Workshop's
// inner sphere (-460,-530) is the one that forced INDUCER_X to -264)
for (const s of DOOR_SPHERES)
  if (Math.hypot(s.x - INDUCER_TRIG[0], s.y - INDUCER_TRIG[1]) < 96 + INDUCER_TRIG_R)
    throw new Error(`rampage inducer trigger overlaps door trigger ${s.flag} (${s.x},${s.y})`);
// docs/196 THE DEPARTURE HALL's lights: each gate in its district's colour, a
// warm key under the oculus, a cool fill in the nave (tower_lighting.js keeps
// the "transit hall" colours saturated; every one waits for the power).
for(const L of TRANSIT.LIGHTS) {
  const [x,y,z]=cpt(L.org[0],L.org[1],TOP2+L.org[2]);
  light(L.label,x,y,z,L.color,L.radius,L.stops,1);
}

// MYSTERY BOX REMOVED (user 2026-08-22: "I also never asked you to include it
// in the map"). It also fought the class design: stock weapon_give at the
// 2-primary limit takes the weapon you are HOLDING, so a box pull with the
// class gun out deleted it — and the class gun carries every upgrade, the tier
// ladder and the PaP state. Do not re-add without the user asking.
// prefab('base mystery box start', 'buyable_magic_box_start.map', -526, -200, -0.5, 0);
// PERK PARKING ROW (see PERK_PARK — the scatter relocates these at load).
// yaw 269.999 SINCE v13.3c: these back a NORTH wall and must face south, and
// the BO7/BO6 port meshes front on model-local +X where the old stock
// p7_zm_vending_* models fronted on -Y (measured — see the long note on the
// yaw in _tod_perk_scatter::build_pads, which carries the matching -90 for
// every scatter pad). This row is only the pre-scatter fallback parking spot,
// but it is visible at spawn, and it is what a machine keeps if capture ever
// fails — so it has to be right too. The old value was 359.999.
for (const pk of PERK_PARK) {
  if (pk.prefab) {
    prefab(`perk park ${pk.prefab}`, pk.prefab, pk.x, PERK_PARK_Y, 0, 269.999, PERK_LOC);
  } else {
    ent(`perk park ${pk.noteworthy}`, [
      '{', `guid "${guid()}"`,
      kv('classname', 'script_struct'),
      kv('angles', `0 ${pk.yaw !== undefined ? pk.yaw : 269.999} 0`),
      kv('model', pk.struct),
      kv('origin', `${pk.x} ${pk.y !== undefined ? pk.y : PERK_PARK_Y} ${pk.z !== undefined ? pk.z : 0}`),
      kv('script_noteworthy', pk.noteworthy),
      kv('script_string', PERK_LOC),
      kv('targetname', 'zm_perk_machine'),
      kv('_color', '1 0 0'), '}',
    ]);
  }
}
// (wallbuy emission removed with WALLBUY_AT — user 2026-08-20)
// THE CROWN — the payoff (v9): PaP + Mule Kick inside the hall, backed on the
// gate wall either side of the entrance (33u standoff, facing into the hall —
// yaw 180 = back to a south wall in the odd frame; cyaw flips it). The
// finale props (uplink, pylons, pad light, sconces, beacon) are SCRIPT-spawned
// by _tod_finale.gsc from _tod_crown_data.gsc — carved-GDT models are safest
// as script_model+SetModel (zone `xmodel,` line), never as baked misc_models.
{
  // STANDOFF 33 -> 64 (user live report 2026-08-28: "final boss room. Pap is
  // inside the wall"). THE HALL HAS TWO MACHINES AND BOTH WERE AUTHORED AT 33:
  // this real Pack-a-Punch, 33u off the SOUTH wall's inner face (HS+HWALL=7880,
  // so origin y=7913), and the upgrade station 33u off the WEST wall. 33 is a
  // copied constant in this section, not a measured clearance, and it is the
  // tightest standoff any vending machine has in the map — the base station
  // sits 64u off the core face and the breather lounges 44u off theirs.
  //
  // I FIXED THE STATION FIRST AND ON A WRONG PREMISE, so the reasoning is
  // recorded rather than quietly overwritten: I had concluded the hall held no
  // real PaP at all, because I grepped the emitted .map for "pack_a_punch" and
  // "packapunch" and the stock prefab is named vending_weapon_upgrade_spawnable
  // — a name containing neither. VERIFY ASSET EXISTENCE BY WHAT THE GENERATOR
  // EMITS, NEVER BY STRING-MATCHING ITS OUTPUT; a prefab's filename is not its
  // subject. Both machines now use the base station's proven 64.
  //
  // v16.35 THE BASILICA (user 2026-09-02: the old spot was "odd and not
  // intuitive" — on the SOUTH wall beside the gate, facing north, i.e. behind
  // a player who has just run in). The machine now takes the EAST SHRINE at
  // the crossing: on the east wall at HYC, 64 off the inner face (the same
  // proven standoff), facing WEST across the dais at the upgrade altar in the
  // west shrine — the two upgrade machines flank the choice point. Its bay is
  // cut in section 5d (pilasters, glow panel, canopy at +216); its clips are
  // script (_tod_powerups::crown_pap_clips) and follow the model.
  //
  // YAW — v17.37 (user 2026-09-04: "Pap and ammo crate are not facing the
  // center of the crown room"). THE OLD DERIVATION WAS BUILT ON A CLAIM NOBODY
  // CHECKED: it read "at the old S-wall placement cyaw(180) faced the machine
  // NORTH into the room (user-verified for a month)" and rotated from there to
  // cyaw(270) for west. Both were wrong, and the prefab says so in its own
  // file. _prefabs/ALXS/alxs_cwpap_prefab.map holds the machine model at an
  // INTERNAL yaw of 270 and its pap_trigger_struct at (-25,0,0) — the side a
  // player stands on is prefab-local -x. A misc_prefab's angles COMPOSE with
  // that, so the machine's world facing is 180 + the instance yaw:
  //     cyaw(0) -> WEST (into the hall, across the dais at the altar)
  //     cyaw(180) -> east      cyaw(270) -> north (what shipped: along the wall)
  // Cross-check that needs no prefab file: _tod_powerups::pap_place_clips
  // spreads the machine's colliders along AnglesToForward — "the mesh's local
  // +X, its WIDE axis" — so the cabinet's face is perpendicular to its entity
  // yaw, and the four breather machines (BR_FURN.pap, W wall, yaw 90, facing
  // east, played for weeks) fix that perpendicular as yaw - 90. The prefab's
  // internal 270 lands the model at 180 when the instance is 270 = facing
  // north. VERIFY BY EYE and correct here, one number — same rule as v13.6.
  //
  // CLEARANCES at (664, HYC): the shrine pilasters sit at y HYC+-112..+-144,
  // the machine is ~128 wide along y; the nearest pier base (E4, y HYC+184)
  // starts at x 328 — 250u clear of the machine's front; the crate's clip body
  // (y 8289..8353) is 200u south along the same wall.
  const [px, py, pz] = cpt(HW - HWALL - 64, HYC, TOP2);
  // v13.6 (user 2026-08-29: "I just downloaded bo6 pap. Lets replace all pap
  // machines with this new version. Lets keep the FX and animations from this
  // pack if possible."): the stock vending_weapon_upgrade prefab is REPLACED
  // by the ALXS CW/BO6 PaP — an animated machine with its own FX, sounds and
  // buy script (zm_cwpap, de-singularized in v13.12 so the four breather
  // vendors run the same flow wearing this pack's mesh).
  prefab('crown pack-a-punch', 'ALXS/alxs_cwpap_prefab.map', px, py, pz, cyaw(0), PERK_LOC);
  // NO PERK ON THE CROWN (user 2026-08-25: "I dont want a perk on the crown").
  // The crown carries Pack-a-Punch and nothing else. Mule Kick used to sit here;
  // its replacement, PhD Flopper, went into the PERK_PARK scatter pool instead
  // so that every one of the scatter pads gets a machine — see PERK_PARK.
  // (The "mirrored companion slot" this block used to compute is now literally
  // where the upgrade altar stands — station_org(), the west shrine.)
}

// NOTE (2026-08-22, HARD-WON — do NOT re-add stock PaP prefabs here):
// A second stock `zm_pack_a_punch` zbarrier FATALS THE MAP LOAD. Stock
// _zm_pack_a_punch::spawn_init renames EVERY such zbarrier to the shared
// "vending_packapunch", then vending_weapon_upgrade() does a SINGULAR
// GetEnt("vending_packapunch") which errors with two or more. Map 1 paid for
// this exact lesson (its CHANGELOG "Working 2nd Pack-a-Punch in Paradise").
// v9.16 briefly shipped 4 breather PaP prefabs here and the map would not
// load. The breather Pack-a-Punches are SCRIPT-SPAWNED standalone vendors
// instead (script_model + trigger_radius_use, never the zm_pack_a_punch
// targetname) — see _tod_powerups.gsc::breather_pap_spawn.

// --- lights: 3 per lap (landing pools, palette-cycled) + base + roof ---------
// v17.77 — THE RED-LIGHT TEST (user 2026-09-05: "if i asked for a red tint of light on the
// entire map how would you do it and can you implement"). The map's light comes from three
// sources and each has ONE colour knob:
//   1. the SKY IMAGE (the ambient; bakes through skyStops) — `gen_tod_sky.js --tint r,g,b`;
//   2. the SUN — `colorSRGB` on tod_ssi_cybercity in source_data/tod_skybox.gdt;
//   3. every POINT LIGHT — `_color` on the entity, and ALL of them (36 call sites, ~310
//      lights, tower + crown + spire) are emitted by light() below, so LIGHT_TINT here is
//      the whole lane.
// Everything else that can colour the screen is NOT light: the vision file (a post-grade,
// must stay neutral — it is force-restored per client on every revive), the LUT material,
// and the fog (the tower has none; fog_off()). All three light knobs are BAKED: FULL build.
// The rule: colour x LIGHT_TINT, then rescaled so the light's LUMA is unchanged (a tint is a
// cast, not a dimming); if a channel passes 1 the colour is renormalised to max 1 and the
// overflow goes into `stops` (one stop = 2x) — a light that was already red gets brighter-red
// instead of clipping. `null` = off, byte-identical .map. The knob itself, LIGHT_TINT, sits
// with SKYBOX_MODEL / SSI near the top of the file (the first light() call runs before this
// block is reached, and a `const` here would be in its temporal dead zone).
// docs/162 STEP 0 / STEP 1 — the three switches (the comment block before the
// volume_sun section says what each one is). Declared here because the T1
// lights are emitted from the crown light block below, before that section.
const LIGHT_TEST_T1 = false;   // ANSWERED 2026-09-25 by the user's log: boots script state 1 = Radiant State 2
const SUN_SSI2 = true;
const SUN_PROBE_TARGET = true;
const SUN_PROBE_TARGET_NAME = 'tod_sun_probe_target';
const SUN_PROBE_TARGET_ORG = [490, -120, 200];   // the open ring between the stair band (to ~436) and the arena wall (540), 200 up

function tintLight(color, stops) {
  if (!LIGHT_TINT) return [color, stops];
  const luma = v => 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
  const c = color.trim().split(/\s+/).map(Number);
  let t = c.map((v, i) => v * LIGHT_TINT[i]);
  const k = luma(c) / Math.max(luma(t), 1e-9);
  t = t.map(v => v * k);
  const mx = Math.max(...t);
  let s = stops;
  if (mx > 1) { t = t.map(v => v / mx); s = +(stops + Math.log2(mx)).toFixed(3); }
  return [t.map(v => +v.toFixed(4)).join(' '), s];
}
// `mask` = lightingstate1..4. The map-wide default (0,1,1,1) is the v9 authoring
// ("off in State 1"); docs/162 reads stock usermaps as booting Radiant State 2,
// which docs/162 T1 (LIGHT_TEST_T1) is testing. The dark hall's pools pass
// (1,1,1,1): power is on from the first frame in TOD II, so there is no state
// in which the hall should be unlit, and the pools then do not hang on T1's
// answer.
function light(label, x, y, z, color, radius, stops, bake, mask = [0, 1, 1, 1]) {
  const profile = TOWER_LIGHTING.tune(label, color, radius, stops);
  ({color, radius, stops} = profile);
  [color, stops] = tintLight(color, stops);
  if (LIGHTS_AT_POWER) mask = (mask === 'alarm') ? [1, 0, 1, 0] : [1, 0, 0, 0];   // THE BLACKOUT: every light waits for the power; the hall's for the alarm (HALL_ALARM_LIGHTS)
  else if (mask === 'alarm') mask = [1, 1, 1, 1];
  stops = +(stops + LIGHT_STOPS_ADD).toFixed(3);   // +25 % (see LIGHT_STOPS_ADD)
  ent(label, [
    '{', `guid "${guid()}"`, kv('classname', 'light'),
    kv('targetname', label.replace(/\W+/g, '_')),
    kv('origin', `${x} ${y} ${z}`),
    kv('PRIMARY_TYPE', 'PRIMARY_OMNI'), kv('PRIMARY_NOSHADOWMAP', '1'),
    kv('ENABLE_FALLOFF', '1'), kv('_color', color),
    kv('radius', `${radius}`), kv('stops', `${stops}`),
    kv('falloffdistance', '12'), kv('bake_intensity_scale', `${bake}`),
    kv('client_server', 'ClientSide'), kv('def_tile', '1 1'),
    kv('excludeDedicated', 'Off'), kv('far_edge', `${profile.farEdge ?? 0.949999988079071}`),
    ...(profile.spec === undefined ? [] : [kv('spec_comp', `${profile.spec}`),
      kv('culling_cutoff', '20'), kv('culling_falloff', '60')]),
    kv('fov_outer', '90'),
    kv('lightingstate1', `${mask[0]}`), kv('lightingstate2', `${mask[1]}`),
    kv('lightingstate3', `${mask[2]}`), kv('lightingstate4', `${mask[3]}`),
    kv('penumbraRadius', '1.5'), kv('roundness', '0.5'),
    kv('shadowUpdate', 'Never'), kv('shadowmapScale', '1'),
    kv('superellipse', '0.75 1 0.75 1'), kv('volumetricSampleCount', '8'),
    kv('name', 'light'), kv('spawnflags', '82'), '}',
  ]);
}
// BASE_LIGHT_BAKE (v17.32, user 2026-09-04: "Tiny bit brighter"). v17.28 took
// the arena floor from a FILLED emissive (dark_blue_tinted, scaleRGB 10) to the
// plain grid texture, which is ~96% black — so the floor stopped lighting the
// room and the four corner lights are now most of what is down here.
//
// THIS IS THE ONLY REAL BRIGHTNESS KNOB IN THE BASE. The floor TINT is not one:
// `blue` and `dark_blue` are the same texture at the same scaleRGB, so the tint
// moves the grid LINE colour and nothing else (see MAT.baseFloor). Raising the
// light instead of the material keeps the black floor black, which is the look
// that was asked for, and lifts the walls and the players standing on it.
//
// bake_intensity_scale, not radius: radius would change WHERE the pools fall and
// re-shape the room. 1.35 is deliberately small — "tiny bit" — and it is one
// number to move again after a look.
const BASE_LIGHT_BAKE = 1.35;
light('tod light base 1', -470, -470, 240, BASE_LIGHT, 520, 6, BASE_LIGHT_BAKE);
light('tod light base 2', 470, -470, 240, BASE_LIGHT, 520, 6, BASE_LIGHT_BAKE);
light('tod light base 3', -470, 470, 240, BASE_LIGHT, 520, 6, BASE_LIGHT_BAKE);
light('tod light base 4', 470, 470, 240, BASE_LIGHT, 520, 6, BASE_LIGHT_BAKE);
// Follows the spawn to the WEST band (2026-08-27) — it exists to light the
// start point, and leaving it in the south would have left the new spawn lit
// only by the two blue corner lights while the empty south stayed warm. Same
// colour, same radius, same height; only x/y move.
// v17.76 (2026-09-05): '1 0.9 0.78' was THE OLIVE POOL. The floor's colourMap is $white_diffuse, so this
// one warm omni painted the spawn, the core's face, hands, guns and zombies olive-yellow; Miami's warm
// sky-light tinted everything the same way and hid it (the Workshop screenshots show the base gold-olive
// under Miami too) — the blue sky exposed it. Cool white now, same radius/stops. Read docs/104 §4d.
// v17.78: back to the warm '1 0.9 0.78' — the v17.76 cool-white swap was part of the yellow hunt
// the user asked to revert whole ("revert all the code we touched") for the Miami A/B screenshot.
light('tod light base spawn', SPAWN_BAND_X - 10, 0, 200, '1 0.9 0.78', 420, 6, BASE_LIGHT_BAKE);
for (let lap = 0; lap < LAPS; lap++) {
  const b = lap * LAP_RISE, c = lapPal(lap).light;
  const oddl = (lap % 2 === 0);
  if (oddl) {
    light(`tod light lap${lap + 1} mid`, 336, 336, b + FLIGHT_RISE + 160, c, 420, 6, 1);
    light(`tod light lap${lap + 1} end`, -336, 336, b + LAP_RISE + 160, c, 420, 6, 1);
  } else {
    light(`tod light lap${lap + 1} mid`, -336, -336, b + FLIGHT_RISE + 160, c, 420, 6, 1);
    light(`tod light lap${lap + 1} end`, 336, -336, b + LAP_RISE + 160, c, 420, 6, 1);
  }
  // THE HAVEN'S LIGHTS (docs/202): a cool key over the dome, a district-colour
  // pool on the threshold and the pad, and a cyan spill at each anchor fin's gem
  // (tools/haven_layout.js lights(); tower_lighting.js keeps them saturated).
  if (BREATHER_LAPS.has(lap + 1)) {
    if (oddl) throw new Error(`haven lights on odd lap ${lap + 1}`);
    for (const L of HAVEN.lights(lap + 1, b + FLIGHT_RISE, BREATHER_THEME[lap + 1].light))
      light(L.label, ...L.org, L.color, L.radius, L.stops, 1);
  }
}
// THE CROWN (v9) — gold on the approach, cyan at the gate, gold in the hall,
// green over the extraction pad, a red beacon on the mast tip.
{
  const CL = (label, x, y, z, color, radius) => { const [a, b, c] = cpt(x, y, z); light(label, a, b, c, color, radius, 6, 1); };
  CL('tod light crown stair', 336, 0, TOP + 96 + 160, '1 0.85 0.35', 460);
  CL('tod light terrace W', -300, 368, TOP2 + 170, '1 0.85 0.35', 460);
  CL('tod light terrace E', 300, 368, TOP2 + 170, '1 0.85 0.35', 460);
  // one per on-axis stretch and one down the middle of every branch (7). A
  // fraction-of-length point would now hang in the air over a fork.
  causewayLightPointsCrownFrame().forEach((o, k) => CL(`tod light causeway ${k + 1}`, o[0], o[1], o[2] + 180, '0.35 0.9 1', 420));
  if (!DARK_HALL) {
    CL('tod light crown gate', 0, HS + 60, TOP2 + 200, '0.35 0.9 1', 520);
    // The four hall lights hang on the quarter points at +260 — since v16.35
    // that is 24u outside the pier line (bases end at x 440) and 44u above the
    // beam top (+216), so each one lights an aisle bay and the nave beside it.
    // Nothing in the basilica reaches +260: pier caps +216, canopies +248.
    const HQ = 448;
    CL('tod light hall SW', -HQ, HYC - HQ, TOP2 + 260, '1 0.85 0.35', 620);
    CL('tod light hall SE', HQ, HYC - HQ, TOP2 + 260, '1 0.85 0.35', 620);
    CL('tod light hall NW', -HQ, HYC + HQ, TOP2 + 260, '1 0.85 0.35', 620);
    CL('tod light hall NE', HQ, HYC + HQ, TOP2 + 260, '1 0.85 0.35', 620);
    CL('tod light hall dais', 0, HYC, TOP2 + 240, '1 0.95 0.5', 520);
    CL('tod light extraction', 0, EXFIL_Y, TOP2 + 200, '0.35 1 0.6', 460);
    // v16.35 THE BASILICA: one warm light under each shrine canopy (canopy
    // underside +216, the machines top out ~+127, so +160 sits in the clear
    // between them), and a wash on the reredos from 64u in front of its face.
    CL('tod light shrine W', -600, HYC, TOP2 + 160, '1 0.85 0.35', 360);
    CL('tod light shrine E', 600, HYC, TOP2 + 160, '1 0.85 0.35', 360);
    CL('tod light reredos', 0, HN - HWALL - 96, TOP2 + 300, '1 0.85 0.35', 420);
  } else {
    // THE DARK HALL'S POOLS (docs/164; docs/162 09 §2.2 "pools and contrast, not
    // even coverage", 08 §0.3 "Giant light values are the best stock starting
    // point": The Giant's lights are median stops 7 / radius 150, ours were all
    // 6 / 420-620). The four quarter-point hall lights are GONE — they were the
    // even coverage. What stays is one pool per thing a player must find, each
    // motivated by a fixture it hangs under, and everything between them falls
    // to the sky's ambient (which this pass cut ~5 stops) and the grid lines.
    // Every one is on ALL FOUR lighting states (see light()'s mask note).
    //   key pools   the two shrines: the altar (W) and the Pack-a-Punch (E), under
    //               their canopies — the strongest lights in the room, tight.
    //   wayfinding  the gate (cyan, the way out) — kept, tightened.
    //   landmarks   the reredos wash (north wall), the dais under the alarm (dim:
    //               the alarm's own flashing red FX light owns that spot once it
    //               fires), the parked extraction pad (dim green).
    //   the spawn   a cool, dim pool on the west wall's spawn band so the party
    //               sees itself and its hands; the rest of the west aisle is dark.
    //   the shops   one dim red pool over each of the peer's three item shops
    //               (CROWN_SHOPS; the active one carries its own sky marker).
    const HL = (label, x, y, z, color, radius, stops) => { const [a, b, c] = cpt(x, y, z); light(label, a, b, c, color, radius, stops, 1, HALL_ALARM_LIGHTS.test(label) ? 'alarm' : [1, 1, 1, 1]); };
    HL('tod light crown gate', 0, HS + 60, TOP2 + 200, '0.35 0.9 1', 400, 6);
    // THE VENDOR POOLS ARE GONE (user 2026-09-25 21:45: "there are lights over pack
    // a punch and the shop ... In the crown, I want those specific lights to just be
    // removed"). shrine W stood over the item shop (it took the altar's spot), shrine
    // E over the Pack-a-Punch, and one red pool hung over each CROWN_SHOPS hut. All
    // three kinds are off behind this one switch; true restores them byte-for-byte.
    if (CROWN_VENDOR_LIGHTS) {
      HL('tod light shrine W', -600, HYC, TOP2 + 160, '1 0.85 0.35', 300, 7);
      HL('tod light shrine E', 600, HYC, TOP2 + 160, '1 0.85 0.35', 300, 7);
    }
    HL('tod light hall reredos', 0, HN - HWALL - 96, TOP2 + 300, '1 0.85 0.35', 320, 5);
    HL('tod light hall dais', 0, HYC, TOP2 + 240, '1 0.95 0.5', 260, 4);
    HL('tod light extraction', 0, EXFIL_Y, TOP2 + 200, '0.35 1 0.6', 240, 4);
    HL('tod light hall spawn', -WALL_IN + 140, (HALL_SPAWN_Y[0] + HALL_SPAWN_Y[1]) / 2, TOP2 + 140, '0.75 0.85 1', 260, 4);
    if (CROWN_VENDOR_LIGHTS) CROWN_SHOPS.forEach((p, i) => HL(`tod light hall shop ${i + 1}`, p.x, p.y, p.z + 160, '1 0.35 0.3', 200, 4));
    // THE HALL FILL (user 2026-09-25: "in the crown, there's not enough lights to
    // fill up the entire space ... it's still dark in some areas ... make sure the
    // lighting fills up everything"). The nine pools above are accents; this is an
    // even 4 x 4 grid over the whole 1456 x 1424 interior, a cool dim white, each
    // radius reaching past its neighbours (pitch ~364 in x, ~356 in y), clear of the
    // pier rows (x +-384) and above the arcade beams. Powered state only, like
    // every light (LIGHTS_AT_POWER); before the power the hall is the sky's.
    {
      const iy1 = HS + HWALL, iy2 = HN - HWALL, ix = WALL_IN;
      const xs = [-3, -1, 1, 3].map(k => Math.round(k * ix / 4));
      const ys = [1, 3, 5, 7].map(k => Math.round(iy1 + k * (iy2 - iy1) / 8));
      if (xs.some(x => Math.abs(Math.abs(x) - NAVE_X) < 80)) throw new Error('hall fill light on a pier row');
      xs.forEach((x, i) => ys.forEach((y, j) => HL(`tod light hall fill ${i + 1}${j + 1}`, x, y, TOP2 + 320, '0.75 0.82 1', 460, 4)));
    }
    // THE BALCONY + THE ENCLOSED HALLWAY (2026-09-25): a cool pool over the
    // pad and a warm one at Quick Revive out on the balcony; inside the hallway
    // (no sky reaches it) a pool in the junction, one in the east corridor and a
    // warm one over the lever — those three are ALARM lights (HALL_ALARM_LIGHTS),
    // because the party must find the power in the dark before it is on. The
    // teleporter room and the bridge corridor light with the power.
    if (CW_CUT) {
      HL('tod light balcony pad', JP_PAD[0], JP_PAD[1], TOP2 + 220, '0.35 0.9 1', 480, 6);
      HL('tod light balcony qr', TERRACE_QR[0], TERRACE_QR[1] - 60, TOP2 + 160, '1 0.85 0.35', 260, 5);
      HL('tod light hallway junction', 0, (HW_JUNC.y1 + HW_JUNC.y2) / 2, TOP2 + HW_H - 40, '0.75 0.82 1', 420, 4);
      HL('tod light hallway east', (HW_EAST.x1 + HW_EAST.x2) / 2, (HW_EAST.y1 + HW_EAST.y2) / 2, TOP2 + HW_H - 40, '0.75 0.82 1', 280, 4);
      HL('tod light hallway power', HW_LEVER[0] - 120, HW_LEVER[1], TOP2 + HW_H - 40, '1 0.85 0.35', 340, 5);
      HL('tod light hallway west', (HW_WEST.x1 + HW_WEST.x2) / 2, (HW_WEST.y1 + HW_WEST.y2) / 2, TOP2 + HW_H - 40, '0.75 0.82 1', 280, 4);
      HL('tod light hallway teleporter', HW_TELE_ORG[0], HW_TELE_ORG[1], TOP2 + HW_H - 40, '0.35 0.9 1', 340, 5);
      HL('tod light hallway south', 0, (HW_SOUTH.y1 + HW_SOUTH.y2) / 2, TOP2 + HW_H - 40, '0.75 0.82 1', 300, 4);
    }
  }
  light('tod light mast beacon', 0, 0, MAST_TOP + 24, '1 0.25 0.2', 900, 6, 1);
  // docs/162 T1 (see LIGHT_TEST_T1): the two state-test lights, raw colours (no
  // LIGHT_TINT), the map's own key set otherwise, 48 apart on the west wall's
  // inner face level with the spawn band. Remove them once T1 is answered.
  if (LIGHT_TEST_T1) {
    for (const [label, color, mask, y] of [['tod light test T1 green', '0 1 0', [1, 0, 0, 0], HALL_SPAWN_Y[1]],
                                           ['tod light test T1 red',   '1 0 0', [0, 1, 0, 0], HALL_SPAWN_Y[1] - 48]]) {
      const o = cpt(-WALL_IN + 48, y, TOP2 + 100);
      ent(label, [
        '{', `guid "${guid()}"`, kv('classname', 'light'),
        kv('targetname', label.replace(/\W+/g, '_')),
        kv('origin', `${o[0]} ${o[1]} ${o[2]}`),
        kv('PRIMARY_TYPE', 'PRIMARY_OMNI'), kv('PRIMARY_NOSHADOWMAP', '1'),
        kv('ENABLE_FALLOFF', '1'), kv('_color', color),
        kv('radius', '200'), kv('stops', '6'),
        kv('falloffdistance', '12'), kv('bake_intensity_scale', '1'),
        kv('client_server', 'ClientSide'), kv('def_tile', '1 1'),
        kv('excludeDedicated', 'Off'), kv('far_edge', '0.949999988079071'),
        kv('fov_outer', '90'),
        kv('lightingstate1', `${mask[0]}`), kv('lightingstate2', `${mask[1]}`),
        kv('lightingstate3', `${mask[2]}`), kv('lightingstate4', `${mask[3]}`),
        kv('penumbraRadius', '1.5'), kv('roundness', '0.5'),
        kv('shadowUpdate', 'Never'), kv('shadowmapScale', '1'),
        kv('superellipse', '0.75 1 0.75 1'), kv('volumetricSampleCount', '8'),
        kv('name', 'light'), kv('spawnflags', '82'), '}',
      ]);
    }
  }
  // THE CIRCLET'S ONLY THREE LIGHTS (v11, +1 in v12). A 900-unit light does
  // nothing for a 4096-unit object, so the crown's exterior read is carried by
  // MATERIAL and these exist only to make the RED points of the vertical axis
  // bloom: the beacon at the apex, the great ruby on the front cross, and —
  // v12 — the GIRANDOLE hanging under the bell, which is the one object every
  // climbing player faces for fifty floors. Adding more would cost bake time
  // and change nothing anyone can see from the tower.
  CL('tod light crown ruby', 0, CR_CY - PT_Y - 300, TOP2 + CR_RIM_Z + 2016, '1 0.25 0.2', 900);
  CL('tod light crown beacon', 0, CR_CY, CROWN_TOP + 24, '1 0.25 0.2', 900);
  // SOUTH of the orb, not centred on it: at (0, CR_CY, orb-height) the origin
  // sits INSIDE the CS(264)-half ruby equator brush and a light inside solid
  // illuminates nothing (caught by arithmetic 2026-08-26, the same trap as the
  // entombed quarter-beacons). CS(480) south clears the orb by ~300 and biases
  // the bloom onto the pendant's SOUTH face — the only side anybody sees.
  CL('tod light crown girandole', 0, CR_CY - CS(480), TOP2 + CR_SKIRT_BOT - CS(480), '1 0.25 0.2', 900);
  // and one warm wash inside the circlet's mouth, where the party walks through
  CL('tod light crown mouth', 0, CR_CY - CR_HY + 160, TOP2 + 300, '1 0.85 0.35', 560);
}

// --- reflection probes: base + every 3rd lap + roof --------------------------
function probe(label, x, y, z) {
  ent(label, [
    '{', `guid "${guid()}"`, kv('classname', 'reflection_probe'),
    kv('origin', `${x} ${y} ${z}`), kv('radius', '2048'),
    kv('ao_power', '2'), kv('ao_range', '16'), kv('ao_strength', '1'),
    kv('blend_maxs', '3 3 3'), kv('blend_mins', '3 3 3'), kv('box', '1'),
    kv('client_server', 'ClientSide'), kv('debugColor', '1 1 1'),
    kv('debug_render_index_x', '64'), kv('exploderFade', '1'),
    kv('grid_density', '16'), kv('high_detail', '1'), kv('in_play_space', '1'),
    kv('name', 'probe'), kv('placement_offset', '72'),
    kv('size_max', '72 72 72'), kv('size_min', '72 72 72'), '}',
  ]);
}
probe('probe base', 0, -490, 150);
// Fitted room probe; half-extents reach the floor, ceiling and side walls.
{
  const r=TRANSIT.ROOM,org=cpt((r.x1+r.x2)/2,(r.y1+r.y2)/2,TOP2+r.height/2);
  const half=`${(r.x2-r.x1)/2} ${(r.y2-r.y1)/2} ${r.height/2}`;   // docs/196: the box reaches the hall's walls, floor and cornice
  ent('probe transit bay',['{',`guid "${guid()}"`,kv('classname','reflection_probe'),
    kv('origin',org.join(' ')),kv('box','1'),kv('size_min',half),kv('size_max',half),
    kv('blend_mins','4 4 4'),kv('blend_maxs','4 4 4'),kv('resolution','4x'),kv('in_play_space','1'),'}']);
}
// docs/158 — THE UNDERCITY'S LIGHT: dim cyan pools under the ceilings, a warm
// pool on the spawn rows, a RED lamp inside every window niche (the horde's
// door reads as a hazard from across the room), the shaft lit every 400 units
// of run. The wings: one hue light in the hallway, two arena-blue pools in the
// room, a hue wash on the bench. One probe per room.
{
  const UC_LIGHT = '0.3 0.9 1', UC_R = 420, UC_LZ = UC_Z + 150;
  light('tod light vault 1', VT_X1 + 200, VT_Y1 + 180, UC_LZ, UC_LIGHT, UC_R, 6, BASE_LIGHT_BAKE);
  light('tod light vault 2', VT_X2 - 200, VT_Y1 + 180, UC_LZ, UC_LIGHT, UC_R, 6, BASE_LIGHT_BAKE);
  light('tod light vault 3', VT_X1 + 200, VT_Y2 - 180, UC_LZ, UC_LIGHT, UC_R, 6, BASE_LIGHT_BAKE);
  light('tod light vault 4', VT_X2 - 200, VT_Y2 - 180, UC_LZ, UC_LIGHT, UC_R, 6, BASE_LIGHT_BAKE);
  light('tod light vault spawn', VT_CX, VT_CY - 72, UC_LZ, '1 0.9 0.78', 380, 6, BASE_LIGHT_BAKE);
  light('tod light vault revive', VAULT_QR[0], VAULT_QR[1] - 60, UC_Z + 120, '0.4 0.6 1', 260, 6, 1);
  VAULT_RISERS.forEach(([rx, ry], i) => light(`tod light vault window ${i + 1}`, rx, ry, UC_Z + 80, '1 0.25 0.2', 220, 6, 1));
  light('tod light conduit 1', CD_X1 + 160, SHAFT_CY, UC_LZ, UC_LIGHT, UC_R, 6, BASE_LIGHT_BAKE);
  light('tod light conduit 2', CD_X2 - 160, SHAFT_CY, UC_LZ, UC_LIGHT, UC_R, 6, BASE_LIGHT_BAKE);
  light('tod light conduit shelf', PART_SHELF_X + 80, (CD_Y1 + CD_Y2) / 2, UC_Z + 110, '1 0.6 0.2', 300, 6, 1);
  light('tod light conduit door', CONDUIT_DOOR_X, VT_Y2 + 60, UC_Z + 110, '0.4 0.6 1', 300, 6, 1);
  // the shaft: z follows the flight (UC_Z + RISE per TREAD of run past the first riser)
  for (let k = 0; k < 3; k++) {
    const lx = SHAFT_FLT_X1 + 128 + k * 400;
    const lz = UC_Z + RISE * ((lx - SHAFT_FLT_X1) / TREAD) + 180;
    light(`tod light shaft ${k + 1}`, lx, SHAFT_CY, lz, UC_LIGHT, 380, 6, BASE_LIGHT_BAKE);
  }
  light('tod light shaft top', (SHAFT_TOP_X1 + SHAFT_TOP_X2) / 2, SHAFT_CY, 190, '0.4 0.6 1', 340, 6, BASE_LIGHT_BAKE);
  probe('probe vault', VT_CX, VT_CY, UC_Z + 140);
  probe('probe conduit', (CD_X1 + CD_X2) / 2, SHAFT_CY, UC_Z + 140);
  probe('probe shaft', (SHAFT_FLT_X1 + SHAFT_FLT_X2) / 2, SHAFT_CY, UC_Z + LAP_RISE / 2 + 100);
  for (const w of WINGS) {
    const F = wingFrame(w), R = WING_ROOM / 2;
    const L = (label, u, v, z, color, radius, bake = 1) => { const [x, y] = F.pt(u, v); light(`tod light wing ${w.key} ${label}`, x, y, z, color, radius, 6, bake); };
    L('hall', WU0 + WING_HALL_L / 2, w.dc, 110, w.light, 340);
    L('room a', WU_ROOM1 + 136, w.rc - 160, 200, BASE_LIGHT, 460, BASE_LIGHT_BAKE);
    L('room b', WU_ROOM1 + 136, w.rc + 160, 200, BASE_LIGHT, 460, BASE_LIGHT_BAKE);
    L('bench', WU_ROOM2 - 56, w.rc, 150, w.light, 300);
    const [px, py] = F.pt(WU_ROOM1 + R, w.rc);
    probe(`probe wing ${w.key}`, px, py, 150);
  }
}
for (let lap = 1; lap <= LAPS; lap += 3) {
  const pxp = (lap % 2 === 1) ? 336 : -336;
  probe(`probe lap${lap}`, pxp, pxp, (lap - 1) * LAP_RISE + FLIGHT_RISE + 150);
}
// docs/202 v2: each haven hall is a room (walls, a ceiling, a loggia) - one fitted
// box probe per hall (the transit bay's recipe), its box reaching the walls, the
// loggia's rails, the floor and the ceiling (tools/haven_layout.js PROBE).
for (const lap of [...BREATHER_LAPS].sort((a, b) => a - b)) {
  const P = HAVEN.PROBE, m = (lap - 1) * LAP_RISE + FLIGHT_RISE;
  ent(`probe lap${lap} haven hall`, ['{', `guid "${guid()}"`, kv('classname', 'reflection_probe'),
    kv('origin', `${P.org[0]} ${P.org[1]} ${m + P.org[2]}`), kv('box', '1'),
    kv('size_min', P.half.join(' ')), kv('size_max', P.half.join(' ')),
    kv('blend_mins', '4 4 4'), kv('blend_maxs', '4 4 4'), kv('in_play_space', '1'), '}']);
}
{
  const [tx, ty, tz] = cpt(0, 368, TOP2 + 150);
  probe('probe crown terrace', tx, ty, tz);
  const [hx, hy, hz] = cpt(0, HYC, TOP2 + 200);
  probe('probe crown hall', hx, hy, hz);
  // v11: `probe crown hall` has radius 2048 and the circlet now reaches +-2048
  // in x and 1696 in y off centre, so the band, the points and the arches were
  // all outside every probe in the map. Three more cover the ring's south face
  // (the one everybody looks at), its north face, and the upper crown.
  const RP = (label, x, y, z) => { const [a, b, c2] = cpt(x, y, z); probe(label, a, b, c2); };
  RP('probe crown ring S', 0, CR_CY - CR_HY - 256, TOP2 + CR_C2_Z);
  RP('probe crown ring N', 0, CR_CY + CR_HY + 256, TOP2 + CR_C2_Z);
  RP('probe crown upper', 0, CR_CY, TOP2 + CR_ARCH_CROWN);
}

// docs/162 STEP 0 / STEP 1 (user 2026-09-24: "review the lighting on the map and
// make sure it gives that atmosphere we are looking for"). Three switches, each
// one of the reference's three P0 tests (docs/162 10 §7.3), ALL ON for the first
// lighting build so one playtest answers all three; flip one OFF to bisect.
//   T1  two small test lights on the hall's west wall beside the spawn: GREEN
//       lit only in Radiant State 1, RED only in State 2. Which one is lit tells
//       us which state the game runs, and whether our lights render at all.
//       The matching [TOD_LIGHTSTATE] log is in _tod_fall.gsc.
//   T2  ssi2 = the night SSI. The game runs Radiant State 2 [INFERRED] and its
//       slot was EMPTY, which the linker filled with default_day (a warm daytime
//       sun at stops 14 and an exposure clamp of 1..16 — the opposite of dark).
//   T3  the global probe out of the mast brush: a `target` on an info_null in
//       open air over the plaza ring (the probe lights everything outside the
//       53 default probe boxes, and Treyarch's own sun volumes all target one).
// (the switches themselves are declared above tintLight(): the T1 lights are
// emitted from the crown light block, which runs before this section)

// --- volume_sun / umbra / fpstool -------------------------------------------
ent('volume_sun', [
  '{', `guid "${guid()}"`, kv('classname', 'volume_sun'),
  kv('ssi', SSI), kv('grid_density', '32'), kv('shadowBiasScale', '1'),
  kv('shadowSplitDistance', '2000'), kv('ssi1', SSI),
  ...(SUN_SSI2 ? [kv('ssi2', BLACKOUT ? SSI_PREPOWER : SSI)] : []),   // docs/162 T2; THE BLACKOUT: the boot state's darker sun
  ...(LIGHTS_AT_POWER ? [kv('ssi3', SSI_PREPOWER)] : []),            // THE ALARM's state (Radiant 3): the dark sky, the hall's lights
  ...(SUN_PROBE_TARGET ? [kv('target', SUN_PROBE_TARGET_NAME)] : []),   // docs/162 T3
  kv('streamLighting', '1'),
  matBrush(-(SKY_IN + SKY_TH), SKY_IN + SKY_TH, -(SKY_IN + SKY_TH), SKY_IN + SKY_TH, SKY_BOT, SKY_TOP + SKY_TH, 'sun_volume'),
  '}',
]);
// bounds cover the breather balconies (out to y=708), the power hallway (x to
// 1640), the crown hall (outer face at |y|=HN plus its cornice) and — v11 —
// THE CIRCLET, which reaches 10304 in y and 2112 in x. Geometry outside the
// umbra/fpstool volume is not a crash, but it drops out of occlusion culling
// and out of the fps tool's accounting, and the crown is now the largest single
// object in the map.
const VOL_R = Math.max(ARENA + WALL, HAVEN.EXTENT + 12, 1700, HN + 64,
  Math.max(-crownBB.x1, crownBB.x2, -crownBB.y1, crownBB.y2) + 128);
if (Math.max(-crownBB.x1, crownBB.x2, -crownBB.y1, crownBB.y2) + 64 > VOL_R)
  throw new Error(`crown reaches ${Math.max(-crownBB.x1, crownBB.x2, -crownBB.y1, crownBB.y2)} but the umbra/fpstool volume stops at ${VOL_R}`);
ent('umbra_volume', [
  '{', `guid "${guid()}"`, kv('classname', 'umbra_volume'),
  matBrush(-VOL_R, VOL_R, -VOL_R, VOL_R, UC_Z - 32, SKY_TOP - 200, 'umbra_volume'),   // docs/158: down to the Undercity
  '}',
]);
ent('volume_fpstool', [
  '{', `guid "${guid()}"`, kv('classname', 'volume_fpstool'),
  matBrush(-VOL_R, VOL_R, -VOL_R, VOL_R, UC_Z - 32, SKY_TOP - 200, 'volume_fpstool'),
  '}',
]);

// ---------------------------------------------------------------------------
// 6z. THE BATTLE ARENA (docs/185) — tools/battle_arena_layout.js owns the
// numbers. A detached room reached only by script teleport from the floor-40
// chamber; a win returns the party to the top bay's arrival.
// ---------------------------------------------------------------------------
{
  const A = ARENA_LAYOUT.ARENA, o = ARENA_LAYOUT.OUTER;   // the vented roof's overhang is the room's outer edge
  const ax1 = A.cx - o, ax2 = A.cx + o, ay1 = A.cy - o, ay2 = A.cy + o;
  if (Math.max(-ax1, ax2, -ay1, ay2) + 256 > SKY_IN) throw new Error(`battle arena reaches ${Math.max(-ax1, ax2, -ay1, ay2)} — inside the sky seal margin (SKY_IN ${SKY_IN})`);
  if (Math.max(-ax1, ax2, -ay1, ay2) + 64 > VOL_R) throw new Error(`battle arena reaches ${Math.max(-ax1, ax2, -ay1, ay2)} but the umbra/fpstool volume stops at ${VOL_R}`);
  if (ARENA_LAYOUT.TOP > SKY_TOP - 200 || A.z - 64 < SKY_FLOOR) throw new Error('battle arena outside the sky seal vertically');
  // clear of every other brush in the map by 512 (it is an island) - which also
  // keeps the vent's way out (under the skirts) open to the void
  for (const bx of allBoxes)
    if (!bx.label.startsWith('battle arena') && bx.x1 < ax2 + 512 && bx.x2 > ax1 - 512 && bx.y1 < ay2 + 512 && bx.y2 > ay1 - 512
        && bx.z1 < ARENA_LAYOUT.TOP + 512 && bx.z2 > A.z - 576 && !/^sky /.test(bx.label))
      throw new Error(`battle arena crowds '${bx.label}'`);
  // THE CRUCIBLE (docs/185 v2): kit-role boxes, chamfered solids and the
  // stair ramp clip (the tower's own wedge, seeded by construction)
  ARENA_LAYOUT.geometry({
    box: (label, x1, x2, y1, y2, z1, z2, role) => transitBox(label, x1, x2, y1, y2, z1, z2, 'tod_cc_' + role),
    bevel: (label, x1, x2, y1, y2, z1, z2, role, amount) => havenBevel(label, x1, x2, y1, y2, z1, z2, role, amount),
    poly: (label, vertices, faces, role) => havenPoly(label, vertices, faces, role),
    rampY: (label, x1, x2, y1, y2, zA, zB, rise, tread) => rampWedgeY(label, x1, x2, y1, y2, zA, zB, MAT.rampClip, rise, tread),
    rampX: (label, y1, y2, x1, x2, zA, zB, rise, tread) => rampWedgeX(label, y1, y2, x1, x2, zA, zB, MAT.rampClip, rise, tread),
  });
  ARENA_LAYOUT.lights(light, probe);
  for (const [x, y, z] of ARENA_LAYOUT.SEEDS) navSeed('battle arena floor', x, y, z);

  // the chamber (floor 40, the EVEN frame: every breather is even — asserted
  // at BREATHER_THEME) and the top bay's arrival (the crown frame, CM)
  const cl = ARENA_LAYOUT.CHAMBER_LAP;
  if (!BREATHER_LAPS.has(cl)) throw new Error(`battle arena chamber lap ${cl} is not a breather`);
  const cz = (cl - 1) * LAP_RISE + FLIGHT_RISE;
  // docs/202 v2: the chamber IS the haven's field (the arena gate at its centre)
  const HC = HAVEN.CHAMBER;
  const chamber = { org: [HC.org[0], HC.org[1], cz], r: HC.r, x1: HC.x1, x2: HC.x2, y1: HC.y1, y2: HC.y2, yaw: 0 };
  const ret = { org: cpt(...TRANSIT.ARRIVAL, TOP2), yaw: (CM < 0 ? 180 : 0) };
  if (TRANSIT.PADS.some(p => p.floor === cl)) throw new Error(`floor ${cl} is the arena chamber — it must not also carry a transit pad (tower_transit_layout PADS)`);
  const ARENA_GSC_OUT = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_arena_data.gsc');
  fs.mkdirSync(path.dirname(ARENA_GSC_OUT), { recursive: true });
  fs.writeFileSync(ARENA_GSC_OUT, ARENA_LAYOUT.dataGsc(chamber, ret), 'utf8');
  console.log(`wrote ${ARENA_GSC_OUT}`);
  console.log(`  battle arena: room x[${ax1},${ax2}] y[${ay1},${ay2}] z ${A.z}; chamber floor ${cl} at (${chamber.org.join(', ')}); return (${ret.org.join(', ')})`);
}

// ---------------------------------------------------------------------------
// 6zz. THE DEALER'S HOUSE (docs/207) - tools/dealer_house_layout.js owns the numbers.
// Two detached rooms reached only by script teleport from the arena's chamber on
// level 10: THE PARLOUR (the Black Market box) and THE HOUSE (the final arena).
// ---------------------------------------------------------------------------
{
  const H = HOUSE_LAYOUT;
  const rooms = [['dealer parlour', H.PARLOUR, H.POUTER, H.PTOP], ['dealer house', H.HOUSE, H.HOUTER, H.HTOP]];
  for (const [name, A, o, top] of rooms) {
    const ax1 = A.cx - o, ax2 = A.cx + o, ay1 = A.cy - o, ay2 = A.cy + o;
    const reach = Math.max(-ax1, ax2, -ay1, ay2);
    if (reach + 256 > SKY_IN) throw new Error(`${name} reaches ${reach} — inside the sky seal margin (SKY_IN ${SKY_IN})`);
    if (reach + 64 > VOL_R) throw new Error(`${name} reaches ${reach} but the umbra/fpstool volume stops at ${VOL_R}`);
    if (top > SKY_TOP - 200 || A.z - 64 < SKY_FLOOR) throw new Error(`${name} outside the sky seal vertically`);
    // an island: clear of every other brush in the map by 512 (the vent's way out stays open to the void)
    for (const bx of allBoxes)
      if (!bx.label.startsWith(name) && bx.x1 < ax2 + 512 && bx.x2 > ax1 - 512 && bx.y1 < ay2 + 512 && bx.y2 > ay1 - 512
          && bx.z1 < top + 512 && bx.z2 > A.z - 576 && !/^sky /.test(bx.label))
        throw new Error(`${name} crowds '${bx.label}'`);
  }
  H.geometry({
    box: (label, x1, x2, y1, y2, z1, z2, role) => transitBox(label, x1, x2, y1, y2, z1, z2, 'tod_cc_' + role),
    bevel: (label, x1, x2, y1, y2, z1, z2, role, amount) => havenBevel(label, x1, x2, y1, y2, z1, z2, role, amount),
    poly: (label, vertices, faces, role) => havenPoly(label, vertices, faces, role),
    rampY: (label, x1, x2, y1, y2, zA, zB, rise, tread) => rampWedgeY(label, x1, x2, y1, y2, zA, zB, MAT.rampClip, rise, tread),
    rampX: (label, y1, y2, x1, x2, zA, zB, rise, tread) => rampWedgeX(label, y1, y2, x1, x2, zA, zB, MAT.rampClip, rise, tread),
    clip: (label, x1, x2, y1, y2, z1, z2) => addBoxTex(label, x1, x2, y1, y2, z1, z2, MAT.clip, 128, 128, 0, 0),   // the hut's hull
  });
  H.lights(light, probe);
  for (const [x, y, z] of H.P_SEEDS) navSeed('dealer parlour floor', x, y, z);
  for (const [x, y, z] of H.H_SEEDS) navSeed('dealer house floor', x, y, z);
  const HOUSE_GSC_OUT = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_house_data.gsc');
  fs.writeFileSync(HOUSE_GSC_OUT, H.dataGsc(), 'utf8');
  console.log(`wrote ${HOUSE_GSC_OUT}`);
  console.log(`  dealer's house: parlour at (${H.PARLOUR.cx}, ${H.PARLOUR.cy}) half ${H.PARLOUR.half}; house at (${H.HOUSE.cx}, ${H.HOUSE.cy}) half ${H.HOUSE.half}, dais z ${H.DAIS_Z}, ring z ${H.RING_Z}`);
}

// ---------------------------------------------------------------------------
// NAVMESH SEEDS — flush (see navSeed's block beside `worldBrushes`)
// ---------------------------------------------------------------------------
// Every flight needs seeding: the coverage rule is not negotiable.
navSeeds.forEach((s) => {
  ent(`navmesh seed ${s.label}`, [
    '{',
    `guid "${guid()}"`,
    kv('classname', 'node_pathnode'),
    kv('origin', `${s.org[0]} ${s.org[1]} ${s.org[2]}`),
    kv('_color', '1 0 1'),
    '}',
  ]);
});
console.log(`  navmesh seeds: ${navSeeds.length} on ramps/shelves/porches/aprons (RAMP_SEEDS=${RAMP_SEEDS}), plus one per riser`);

// ---------------------------------------------------------------------------
// Output: the .map
// ---------------------------------------------------------------------------
const out = [];
out.push('iwmap 4');
out.push('"script_startingnumber" 0');
out.push('"000_Global" flags expanded  active');
out.push('"000_Global/No Comp" flags hidden ignore ');
out.push('"The Map" flags expanded ');
out.push('// entity 0');
out.push('{');
out.push(`guid "${guid()}"`);
out.push(kv('classname', 'worldspawn'));
out.push(kv('lightingquality', '1024'));
out.push(kv('samplescale', '1'));
out.push(kv('skyboxmodel', SKYBOX_MODEL));
out.push(kv('ssi', SSI));
out.push(kv('wsi', 'default_night'));
// ⚠️ THIS LINE IS WHY THE MAP NEVER RENDERED FOG (v14.41, root cause).
// `fsi` is the FOG SETTINGS asset, baked into the BSP from worldspawn like the
// ssi. We shipped `default`, and <modtools>/source_data/fog.gdt's "default"
// entry carries **"fogopacity" "0"** — the fog system was CLAMPED OFF at the
// asset level, so every SetVolFog call in _tod_atmosphere set colour and
// distances on a fog that could never draw. User confirmed live: "Yes this map
// has never rendered fog."
// `zm_factory_volumetric` is stock zm_factory's own volumetric entry —
// "fogopacity" "1", i.e. the full range available — and is therefore a
// SHIPPED, PROVEN-IN-A-REAL-ZM-MAP fog asset rather than something authored
// here. Everything else in it is ordinary (fogintensity 1, sane
// maxlit*fogdistance); script owns colour/distance/height at runtime.
// NO ZONE LINE IS NEEDED: fog settings ride in via the worldspawn/BSP, exactly
// like the ssi (verified — there is no `fog,` asset type in any stock .zone).
// If fog ever reads too heavy at range, `zm_factory_afog` (fogopacity 0.5) is
// the gentler proven alternative; change it HERE, it is a full build.
// `fsi` STAYS `default` — v14.41 changed it to zm_factory_volumetric on the
// theory that "default" carrying fogopacity 0 was why this map never rendered
// fog. THAT THEORY IS DEAD: map 1 (abandoned_cyber_city) renders fog fine with
// `fsi "default"`, and so does stock zm_giant. The fsi was never the problem;
// the problem was that _tod_atmosphere called SetVolFog twice and stopped,
// while map 1 runs a PERSISTENT re-assert loop it calls "the single fog
// authority" — its own comments record a one-shot call as the original "no
// haze" bug. Reverted rather than left changed, so this map matches the two
// working references instead of deviating from both.
// v14.43 — `zm_factory_volumetric` as a DELIBERATE HEDGE, not a theory.
// Two explanations for SetVolFog's 8th arg are still live and I cannot settle
// them from here: the API doc says <transition time>, but MAP 1 passes an
// opacity there and its fog renders. This asset covers BOTH:
//   - if arg 8 IS opacity, an fsi with fogopacity 1 is simply a permissive
//     ceiling and changes nothing about our 0.90;
//   - if arg 8 is a TRANSITION TIME, then opacity can only come from the fsi,
//     and `default` (fogopacity 0) would clamp the fog off no matter what.
// zm_factory_volumetric is stock zm_factory's own entry (fogopacity 1), so it
// is shipped-and-proven rather than authored here. Costs nothing under either
// theory. NOTE map 1 and zm_giant both render fog on `default`, so this is NOT
// claimed as the root cause — it is insurance while the real one is confirmed.
// v17.75 (2026-09-05, user: "Still yellow ... maybe its fog"): zm_factory_volumetric carries litfog 1 +
// sunintensityscale 2 + an orange haze — SUN-LIT FOG, which the 8-arg SetVolFog in fog_off() cannot
// switch off (it only moves distances/colour). That was the olive wash, the light shafts and the
// yellow strip on the core; Miami'"'"'s warm horizon hid it, the purple sky exposed it. tod_fsi_cybercity
// (source_data/tod_skybox.gdt) is that asset with the sun-lit lane OFF and fogopacity 1 kept for the
// spire'"'"'s red fog. Rides in via worldspawn like the ssi — no zone line.
// v17.78: zm_factory_volumetric again — the v17.70 value — for the Miami A/B screenshot (the user
// asked for every yellow-hunt change reverted). tod_fsi_cybercity stays in the GDT, unreferenced.
out.push(kv('fsi', 'zm_factory_volumetric'));
out.push(kv('gravity', '800'));
out.push(kv('lodbias', 'default'));
out.push(kv('lutmaterial', 'luts_t7_default'));
out.push(kv('numOmniShadowSlices', '24'));
out.push(kv('numSpotShadowSlices', '64'));
// docs/166 §6.4 (2026-09-25, THE REFERENCE COPY): the VISIBLE sky box is multiplied by this factor (docs/162 05 §4.4,
// range 0..10; it does not light the bake). 2026-09-27 tower design pass: the factor is already at its maximum.
// Re-finish the same v6 raw at score 0.64 (was 0.32), retaining saturation 1.2; skyStops 1.85 -> 0.85
// in tod_skybox.gdt compensates the doubled EXR energy. Same display factor at both view angles.
// 2026-09-25 14:30 (user: "I want the skylight to be brighter too, without it impacting the ground light as much"): 6.5 -> 8.5 = +31 % on the VISIBLE sky only (this key does not light the bake).
const SKY_INTENSITY_FACTOR = '10';   // 17:00 exaggerate pass: the key's documented max
out.push(kv('sky_intensity_factor0', SKY_INTENSITY_FACTOR));
out.push(kv('sky_intensity_factor1', SKY_INTENSITY_FACTOR));
out.push(kv('state_alias_1', 'State 1'));
out.push(kv('state_alias_2', 'State 2'));
out.push(kv('state_alias_3', 'State 3'));
out.push(kv('state_alias_4', 'State 4'));
// docs/162 T3 — the sun volume's global probe target. Emitted LAST so the
// open-air assert sees every axis box the map emits (crown lofts and bevels
// are not boxes, but the target sits at the plaza, far from the crown).
if (SUN_PROBE_TARGET) {
  const [px, py, pz] = SUN_PROBE_TARGET_ORG;
  const hit = allBoxes.find(b => px > b.x1 && px < b.x2 && py > b.y1 && py < b.y2 && pz > b.z1 && pz < b.z2);
  if (hit) throw new Error(`sun probe target (${px},${py},${pz}) is inside brush "${hit.label}" — move SUN_PROBE_TARGET_ORG into open air`);
  const near = allBoxes.filter(b => px > b.x1 - 48 && px < b.x2 + 48 && py > b.y1 - 48 && py < b.y2 + 48 && pz > b.z1 - 48 && pz < b.z2 + 48).map(b => b.label);
  if (near.length) console.log(`sun probe target: within 48u of ${near.join(', ')}`);
  ent('tod sun probe target', ['{', `guid "${guid()}"`, kv('classname', 'info_null'),
    kv('targetname', SUN_PROBE_TARGET_NAME), kv('origin', `${px} ${py} ${pz}`), '}']);
}
const CROWN_SURFACES = require('./art_cohesion/crown_surfaces');
const TOWER_SURFACES = require('./art_cohesion/tower_surfaces');
// Actual flight midpoints, mirrored with the same parity as the walkable stairs.
// Emitted before serializing entities so the new pools join the existing power state.
let routePools = 0;
for (const p of TOWER_LIGHTING.stairPools(LAPS, LAP_RISE, FLIGHT_RISE, (CORE + PX) / 2)) {
  // THE WAR DAMAGE PASS phase 2 (docs/205 s7b): the broken flight's pool went with the flight - a break is dark but
  // for its rubble fires and the dangling fixture's flicker (verify_tower_design.js counts 100 - the drops)
  if (DESCENT && /flight1$/.test(p.label) && BROKEN_TOWER.drops.has(+p.label.match(/^lap(\d+)/)[1])) continue;
  light(`tod light route ${p.label}`, ...p.origin, '0.78 0.88 1', 280, 8.5, 1);
  routePools++;
}
// ---------------------------------------------------------------------------
// THE FLOOR NUMBERS (docs/208) - ON THE DOORS ONLY since 2026-10-05 (user: "The numbers on the
// railings for each floor can be removed. I only want it on the door."). 2026-10-04 also stood
// every floor's number on the inner face of the outer rail of its end landing, where a descending
// player arrives on it; those rail numbers are RETIRED WHOLE (their emitter, their world quads and
// their view check). What stays is the number on every paid door (doorNumber, below).
// One chalk-mesh quad per digit (map 1's decalQuad: contents nonColliding - no brush, collision,
// navmesh or entity), the map's OWN HUD digits in the district colour of the floor the door opens
// onto (tools/floor_numbers/make_assets.py writes the atlas and the five tod_floornum_* materials;
// its --check holds FLOORNUM_INK / FLOORNUM_ROWS below to the atlas ink). World materials ride the
// BSP: no zone line; a FULL build.
// EMITTED LAST - each door's digits are appended to its slab entity after every other brush and
// entity has its guid - so TOD_FLOORNUMS=0 regenerates the map without them and nothing else moves.
// THE BLACKOUT: the decal is steady emissive (world emission cannot switch with the power), and
// nobody reaches the tower before the power: the crown island is sealed until power_on (the
// balcony door, the jump pad).
// checkFloorNumbers() proves, for every door number, the slab behind it, nothing in front of it
// and a clear view from the flight the player comes down.
// ---------------------------------------------------------------------------
const FLOORNUM_ON = process.env.TOD_FLOORNUMS !== '0';
const FLOORNUM_CELL = 192, FLOORNUM_ATLAS = 2048, FLOORNUM_CELL_H = 256;
// Per digit, the atlas columns its quad crops (its ink + 14 px for the glow skirt), and the rows
// (shared). LOCKSTEP with tools/floor_numbers/make_assets.py (--check measures the ink).
const FLOORNUM_INK = [[23, 168], [42, 148], [23, 166], [25, 166], [23, 166], [24, 165], [23, 166], [26, 165], [23, 166], [23, 166]];
const FLOORNUM_ROWS = [40, 213];
const FLOORNUM_PROUD = 1.5;     // off the door face (map 1's decal standoff)
const FLOORNUM_EYE = 60;        // the check's standing eye over the tread it is read from
// Map 1's chalk-mesh quad with arbitrary corners: cols = [[bottom, top] at the left edge,
// [bottom, top] at the right edge], each vertex [x, y, z, u, v]; normal = u_dir x v_dir.
// floornumQuadText -> the mesh block's text: a brush of a door's own script_brushmodel (doorNumber).
function floornumQuadText(mat, cols) {
  const v = (p, lm) => `${DECAL_TAB}v ${p[0]} ${p[1]} ${p[2]} t ${p[3]} ${p[4]} ${lm}`;
  return [
    '{',
    ` guid "${guid()}"`,
    ' mesh',
    ' {',
    ' contents nonColliding;',
    ' toolFlags;',
    `  ${mat}`,
    '  lightmap_gray',
    '  2 2 0 8',
    '  (',
    v(cols[0][0], '-1.0001428 -6.7082205'),
    v(cols[0][1], '-0.99985725 -9.0415535'),
    '  )',
    '  (',
    v(cols[1][0], '0.87485725 -6.7084455'),
    v(cols[1][1], '0.87514287 -9.0417786'),
    '  )',
    ' }',
    '}',
  ].join('\n');
}
// Floor F's digits, H tall, centred at (cx, face + out * PROUD) on the y-plane facing `out`
// (horizontal unit vector), centre height zc; emit(label, mat, cols) once per digit, left to right.
// The text's right is out turned so that right x up = out (a viewer facing -out reads it
// unmirrored): out (0,+1) -> right (-1,0); out (0,-1) -> right (+1,0).
function floorDigits(F, cx, face, out, zc, H, labelBase, emit) {
  const rt = [-out[1], out[0]];
  // rt x (0,0,1) = (rt[1], -rt[0]) must be the outward normal, or the quad faces into its wall
  if (Math.abs(rt[1] - out[0]) > 1e-9 || Math.abs(-rt[0] - out[1]) > 1e-9) throw new Error(`${labelBase}: the digits would face into their wall`);
  const digits = String(F).split('').map(Number);
  const px = H / (FLOORNUM_ROWS[1] - FLOORNUM_ROWS[0]);
  const widths = digits.map(d => (FLOORNUM_INK[d][1] - FLOORNUM_INK[d][0]) * px);
  const total = widths.reduce((a, w) => a + w, 0), hh = H / 2;
  const uOf = (d, p) => +((d * FLOORNUM_CELL + p) / FLOORNUM_ATLAS * 1024).toFixed(3);
  const vOf = (row) => +((row / FLOORNUM_CELL_H - 1) * 1024).toFixed(3);
  const at = (s, tz) => [+(cx + rt[0] * s + out[0] * FLOORNUM_PROUD).toFixed(3), +(face + rt[1] * s + out[1] * FLOORNUM_PROUD).toFixed(3), +(zc + tz).toFixed(3)];
  const mat = `tod_floornum_${districtOf(F - 1).key}`;
  let a = -total / 2;
  digits.forEach((d, k) => {
    const b = a + widths[k];
    const u0 = uOf(d, FLOORNUM_INK[d][0]), u1 = uOf(d, FLOORNUM_INK[d][1]);
    const vb = vOf(FLOORNUM_ROWS[1]), vt = vOf(FLOORNUM_ROWS[0]);
    emit(`${labelBase} digit ${k + 1}`, mat, [
      [[...at(a, -hh), u0, vb], [...at(a, hh), u0, vt]],
      [[...at(b, -hh), u1, vb], [...at(b, hh), u1, vt]],
    ]);
    a = b;
  });
  return { total, hh, rt, mat };
}
// THE FLOOR NUMBER ON THE DOOR (user 2026-10-04, after the first real playthrough: "The number of
// the floor should be on the door you buy"). Every lap door and the roof door carries the number of
// the floor it opens onto (its `dest`), centred on the slab face the descending player walks up to,
// as chalk-mesh quads INSIDE the door's own script_brushmodel: the number slides into the core with
// the slab and hides with it (stock precedent: zm_giant's "mature_blood" brushmodel is nothing but
// nonColliding decal meshes that script shows and hides). The Ground Floor door (enter_lap1) carries
// none (the plaza has no number either). The colour you read on the door is the district colour of
// the floor behind it. Since 2026-10-05 the doors are the ONLY floor numbers (the rail numbers are
// retired, see the header above).
const DOOR_NUM_H = 48;          // the digits' height on the 128-tall slab
const DOOR_NUM_ZC = 76;         // their centre over the door's own floor (a player 3 treads up looks a little down at it)
const DOOR_NUM_MARGIN = 12;     // kept clear of the slab's edges
const DOOR_NUM_SIGNS = [];
// -> the floor a door opens onto (0: none)
function doorFloorNumber(d) {
  const m = /^enter_lap(\d+)$/.exec(d.flag);
  if (m) return DESCENT ? +m[1] - 1 : +m[1];   // DESCENT: enter_lapN opens onto floor N-1 (N = 1: the Ground Floor, no number)
  if (d.flag === 'enter_roof' && DESCENT) return LAPS;
  return 0;
}
function doorNumber(d) {
  const F = doorFloorNumber(d);
  if (F < 1) return;
  if (!d.slab || d.slab.y2 - d.slab.y1 !== 20) throw new Error(`door number ${d.flag}: expected a 20-thick slab across the flight`);
  const s = d.slab, front = (s.y1 + s.y2) / 2 < 0 ? 1 : -1;   // the side the descending player walks up to (the odd frame's door faces +y)
  const out = [0, front], face = front > 0 ? s.y2 : s.y1, cx = (s.x1 + s.x2) / 2, zc = s.z1 + DOOR_NUM_ZC;
  const meshes = [];
  const g = floorDigits(F, cx, face, out, zc, DOOR_NUM_H, `door number ${d.flag}`, (label, mat, cols) => meshes.push(floornumQuadText(mat, cols)));
  if (g.total / 2 > (s.x2 - s.x1) / 2 - DOOR_NUM_MARGIN) throw new Error(`door number ${d.flag}: ${Math.round(g.total)} wide does not fit the slab`);
  if (zc - g.hh < s.z1 + DOOR_NUM_MARGIN || zc + g.hh > s.z2 - DOOR_NUM_MARGIN) throw new Error(`door number ${d.flag}: leaves the slab's height`);
  const e = entities.find(en => en.label === `door slab ${d.flag}`);
  if (!e) throw new Error(`door number ${d.flag}: no door slab entity`);
  const cut = e.text.lastIndexOf('}');
  e.text = e.text.slice(0, cut) + meshes.join('\n') + '\n' + e.text.slice(cut);
  // the eye the check reads it from: on the approach flight, three treads up and 112 back
  DOOR_NUM_SIGNS.push({ F, flag: d.flag, cx, face, out, rt: g.rt, s1: -g.total / 2, s2: g.total / 2, z1: zc - g.hh, z2: zc + g.hh,
    eyes: [[cx, face + front * 112, s.z1 + RISE * 3 + FLOORNUM_EYE]], digits: meshes.length });
}
// THE CHECK, against every axis box the generator recorded (allBoxes; convex brushes are there as
// their bounding boxes - conservative, they can only add a false "blocked"). Door slabs are
// script_brushmodels, not in allBoxes, so each number's own slab is read from DOORS. Sampled 5 x 3
// per number.
const FLOORNUM_TOOL = /^(clip|clip_player|sky|caulk|nodraw|portal|trigger|volume|sun_volume|umbra_volume|volume_fpstool|tod_haven_barrier)/;
function checkFloorNumbers() {
  const inBox = (p, b) => p[0] > b.x1 && p[0] < b.x2 && p[1] > b.y1 && p[1] < b.y2 && p[2] > b.z1 && p[2] < b.z2;
  const visible = b => !FLOORNUM_TOOL.test(b.tex || '');
  // Slab test: does the open segment p->q cross the box's interior?
  const crosses = (p, q, b) => {
    let t0 = 0, t1 = 1;
    for (let i = 0; i < 3; i++) {
      const lo = [b.x1, b.y1, b.z1][i], hi = [b.x2, b.y2, b.z2][i], d = q[i] - p[i];
      if (Math.abs(d) < 1e-9) { if (p[i] <= lo || p[i] >= hi) return false; continue; }
      let ta = (lo - p[i]) / d, tb = (hi - p[i]) / d;
      if (ta > tb) [ta, tb] = [tb, ta];
      t0 = Math.max(t0, ta); t1 = Math.min(t1, tb);
      if (t0 >= t1) return false;
    }
    return t1 > 1e-6 && t0 < 1 - 1e-6;
  };
  const bad = [];
  // THE DOOR NUMBERS: the slab (the door's own entity, so never in allBoxes) behind every sample,
  // nothing visible in front of it, and a clear view from the flight the player comes down.
  for (const sg of DOOR_NUM_SIGNS) {
    const d = DOORS.find(r => r.flag === sg.flag), slab = d && d.slab;
    if (!slab) { bad.push(`door ${sg.flag}: no slab`); continue; }
    for (const e of sg.eyes) {
      const hit = allBoxes.find(b => visible(b) && inBox(e, b));
      if (hit) bad.push(`door ${sg.flag}: the eye ${e.join(',')} stands inside ${hit.label}`);
    }
    const zMin = Math.min(sg.z1, ...sg.eyes.map(e => e[2])) - 2, zMax = Math.max(sg.z2, ...sg.eyes.map(e => e[2])) + 2;
    const near = allBoxes.filter(b => visible(b) && b.z2 > zMin && b.z1 < zMax);
    for (let i = 0; i < 5; i++) for (let j = 0; j < 3; j++) {
      const sAt = sg.s1 + (sg.s2 - sg.s1) * (0.08 + 0.84 * i / 4), z = sg.z1 + (sg.z2 - sg.z1) * (0.15 + 0.35 * j);
      const on = [sg.cx + sg.rt[0] * sAt, sg.face + sg.rt[1] * sAt, z];
      const behind = [on[0] - sg.out[0], on[1] - sg.out[1], z];
      const front = [on[0] + sg.out[0] * (FLOORNUM_PROUD + 1), on[1] + sg.out[1] * (FLOORNUM_PROUD + 1), z];
      const seen = [on[0] + sg.out[0] * (FLOORNUM_PROUD + 0.25), on[1] + sg.out[1] * (FLOORNUM_PROUD + 0.25), z];
      if (!inBox(behind, slab)) bad.push(`door ${sg.flag}: sample ${i},${j} has no slab behind it`);
      const blocker = near.find(b => inBox(front, b));
      if (blocker) bad.push(`door ${sg.flag}: ${blocker.label} stands in front of the number`);
      for (const e of sg.eyes) {
        const occ = near.find(b => crosses(e, seen, b));
        if (occ) bad.push(`door ${sg.flag}: ${occ.label} blocks the view from ${e.join(',')}`);
      }
    }
  }
  if (bad.length) throw new Error(`FLOOR NUMBERS: ${bad.length} failures, first: ${[...new Set(bad)].slice(0, 6).join(' | ')}`);
  console.log(`  door numbers: ${DOOR_NUM_SIGNS.length} doors carry the floor they open onto (${DOOR_NUM_SIGNS.reduce((n, s) => n + s.digits, 0)} digits inside their slab entities) - the slab behind every sample, nothing in front, a clear view from the approach`);
}
if (FLOORNUM_ON) {
  // each door's digits ride in its slab entity (no rail numbers since 2026-10-05: the doors only)
  for (const d of DOORS) doorNumber(d);
  const want = DOORS.filter(d => doorFloorNumber(d) >= 1).length;
  if (DOOR_NUM_SIGNS.length !== want || want < 20) throw new Error(`door numbers: ${DOOR_NUM_SIGNS.length} placed of ${want}`);
  checkFloorNumbers();
}

// THE CYBER INDUCER'S BODY (docs/208; map 1's v19.68m body clip + its v19.71 perch cap,
// ported). The device is tools/inducer_cyber's model - art/rampage_inducer_cyber/
// install_manifest.json bounds x -23.1..22, y +-22, z 0..67.15, front local +X - and the
// script_model has no collision of its own, so a CLIP stands in for it WHERE IT SPAWNS
// (the crown balcony while the jump pad is live - the generated jumppad_enabled() is CW_CUT
// - else the base arena; never an invisible box where no device stands): a hair inside the
// footprint, 0..INDUCER_CLIP_H. Over it, INDUCER_PERCH_SLOT higher, a STEEP CAP (steepCap,
// 74 deg: map 1 measured 56 still standable, 72 not) whose high edge rises AWAY from where
// players come from - away from the pad on the balcony, into the south wall in the arena -
// so a Breacher launch or an Archer drop finds no flat top to stand on (map 1's tester stood
// on its uncapped 40-tall clip out of every zombie's reach). The use-trigger stays CENTRED
// ("a radius all around it") in the slot between the two, at INDUCER_TRIG_LIFT, emitted as
// crown_/base_inducer_trig_lift() for _tod_rampage.gsc: a clip over a use-trigger's origin
// blocks its sight trace (the dead-trigger trap). steepCap is the base sign's (above).
const INDUCER_CLIP_HALF = 21, INDUCER_CLIP_H = 40, INDUCER_TRIG_LIFT = 44, INDUCER_PERCH_SLOT = 20;
if (INDUCER_TRIG_LIFT < INDUCER_CLIP_H + 2 || INDUCER_TRIG_LIFT > INDUCER_CLIP_H + INDUCER_PERCH_SLOT - 2)
  throw new Error('the rampage inducer trigger origin must sit in the slot between its body clip and its cap (the dead-trigger trap)');
{
  const balcony = CW_CUT;
  const [ox, oy, oz] = balcony ? cpt(CROWN_INDUCER[0], CROWN_INDUCER[1], TOP2) : [INDUCER_ORG[0], INDUCER_ORG[1], INDUCER_PLINTH_H];
  const fp = { x1: ox - INDUCER_CLIP_HALF, x2: ox + INDUCER_CLIP_HALF, y1: oy - INDUCER_CLIP_HALF, y2: oy + INDUCER_CLIP_HALF };
  const tag = balcony ? 'crown' : 'base';
  if (!balcony && fp.y1 <= -ARENA) throw new Error('rampage inducer body clip reaches into the arena south wall');
  addBox(`${tag} rampage inducer body`, fp.x1, fp.x2, fp.y1, fp.y2, oz, oz + INDUCER_CLIP_H, MAT.clip);
  const back = balcony ? [Math.sign(ox - cpt(JP_PAD[0], JP_PAD[1], TOP2)[0]) || 1, 0] : [0, -1];
  steepCap(`${tag} rampage inducer cap`, fp, oz + INDUCER_CLIP_H + INDUCER_PERCH_SLOT, back, MAT.clip, balcony ? 0 : CAP_BURY);
}

let crownSurfaceFaces=0, towerSurfaceFaces=0;
worldBrushes.forEach((b, i) => {
  const authored=CROWN_SURFACES.apply(b.label,b.text,CM);
  crownSurfaceFaces+=authored.changed;
  const tower=TOWER_SURFACES.apply(b.label,authored.text);
  towerSurfaceFaces+=tower.changed;
  out.push(`// brush ${i} — ${b.label}`);
  out.push(tower.text);
});
out.push('}');
entities.forEach((e, i) => {
  const authored=CROWN_SURFACES.apply(e.label,e.text,CM);
  crownSurfaceFaces+=authored.changed;
  const tower=TOWER_SURFACES.apply(e.label,authored.text);
  towerSurfaceFaces+=tower.changed;
  out.push(`// entity ${i + 1} — ${e.label}`);
  out.push(tower.text);
});
console.log(`  crown art: ${crownSurfaceFaces} world/entity faces use the authored industrial kit`);
console.log(`  tower art: ${towerSurfaceFaces} world/entity faces use crown-family materials; ${routePools} powered stair pools (${2 * LAPS - routePools} broken flights dark)`);
out.push('');

// THE BLACKOUT's material swap (see BLACKOUT): face lines only (every brush
// writer ends a face with the lightmap_gray pair), so no entity key can match.
if (BLACKOUT) {
  const BLK = JSON.parse(fs.readFileSync(path.join(__dirname, 'tod_black_materials.json'), 'utf8'));
  const known = new Set(BLK.suffixes);
  const swaps = {};
  const face = /\) (mwiii_vertigo_retro_synth_[a-z_]+|tod_dark_[a-z]+|tod_door_[a-z]+) (?=[-\d.]+ [-\d.]+ [-\d.]+ [-\d.]+ [-\d.]+ [-\d.]+ lightmap_gray)/g;
  for (let i = 0; i < out.length; i++) {
    if (out[i].indexOf('lightmap_gray') < 0) continue;
    out[i] = out[i].replace(face, (m, name) => {
      let sfx = name.startsWith('mwiii_vertigo_retro_synth_') ? name.slice('mwiii_vertigo_retro_synth_'.length) : BLK.hall_to_black[name];
      if (!sfx || !known.has(sfx)) throw new Error(`BLACKOUT: no black clone for ${name} — add it to tools/tod_black_materials.json and re-run gen_tod_door_materials.js`);
      swaps[name] = (swaps[name] || 0) + 1;
      return `) tod_black_${sfx} `;
    });
  }
  const left = out.join('\n').match(/^ *\([^\n]*\b(mwiii_vertigo_retro_synth_[a-z_]+|tod_dark_[a-z]+|tod_door_[a-z]+)\b[^\n]*/m);   // any FACE line (it starts with a point), whatever its format
  if (left) throw new Error(`BLACKOUT: a glowing face survived the swap: ${left[0].slice(0, 80)}`);
  console.log(`  blackout: ${Object.values(swaps).reduce((a, b) => a + b, 0)} faces -> tod_black_* (${Object.keys(swaps).length} source materials)`);
}
fs.mkdirSync(path.dirname(MAP_OUT), { recursive: true });
fs.writeFileSync(MAP_OUT, out.join('\n'), 'utf8');
console.log(`wrote ${MAP_OUT}  (${worldBrushes.length} world brushes, ${entities.length} entities, ${LAPS} laps, top z=${TOP})`);
// The causeway reports itself because it is the one structure whose shape is
// DERIVED rather than written down — read these numbers here rather than
// trusting any figure copied into a doc or a session brief.
console.log(`  causeway: ${CW_STATS.columns} deck columns, ${CW_STATS.edges} exposed edges guarded by ` +
            `${CW_STATS.rails} rails, ${roadPieces.length} pieces, ` +
            `x[${CW_XMIN},${CW_XMAX}] z[${CW_ZMIN},${CW_ZMAX}], ` +
            (CW_CUT
              ? `CUT (docs/163): gap y ${JP_LAND_Y2}..${JP_LAUNCH_Y1} = ${JP_LAUNCH_Y1 - JP_LAND_Y2}u ` +
                `(${Math.round(100 * (JP_LAUNCH_Y1 - JP_LAND_Y2) / (CR_S_FACE - TER_Y2))}% of the span to the crown face), ` +
                `walked ~${CW_WALK} units either side of the jump pad`
              : `walked length ~${CW_WALK} units`));

// ---------------------------------------------------------------------------
// Output: _tod_door_data.gsc
// ---------------------------------------------------------------------------
const g = [];
g.push('// GENERATED by tools/gen_tower_map.js — DO NOT HAND-EDIT (regen instead).');
g.push('// Door buy-trigger positions for _tod_doors.gsc. A map brush entity has no');
g.push('// usable .origin (reports 0,0,0), so the generator hardcodes each doorway');
g.push("// center + its thin-axis offset here from the same tables that cut the .map.");
g.push('');
g.push('#namespace tod_door_data;');
g.push('');
g.push('function get_door_info( flag )');
g.push('{');
g.push('\tinfo = SpawnStruct();');
g.push('\tswitch ( flag )');
g.push('\t{');
for (const d of DOORS) {
  g.push(`\tcase "${d.flag}":`);
  g.push(`\t\tinfo.org = ( ${d.org.join(', ')} );`);
  g.push(`\t\tinfo.off = ( ${d.off.join(', ')} );`);
  g.push(`\t\tinfo.dest = "${d.dest}";`);
  g.push(`\t\tinfo.cost = ${d.cost};`);   // v9.41: the price lives here too (wins over the BSP's zombie_cost)
  g.push('\t\treturn info;');
}
g.push('\t}');
g.push('\treturn undefined;');
g.push('}');
g.push('');

fs.mkdirSync(path.dirname(DOOR_GSC_OUT), { recursive: true });
g.push('','// Fixed broken descent routes; no purchase trigger on these floors.');
const dropVec = a => `( ${a.join(', ')} )`;
g.push('function get_drop_info( lap )','{','\tswitch ( lap )','\t{');
if (DESCENT) for(const lap of BROKEN_TOWER.DROP_LAPS) {
  const p=BROKEN_TOWER.placement(lap);
  g.push(`\t\tcase ${lap}:`, '\t\t\tr = SpawnStruct();',`\t\t\tr.lap = ${lap};`,`\t\t\tr.flag = "${p.flag}";`,
    `\t\t\tr.upper = ${dropVec(p.upper)};`,`\t\t\tr.lower = ${dropVec(p.lower)};`,
    `\t\t\tr.lo = ${dropVec(p.lo)};`,`\t\t\tr.hi = ${dropVec(p.hi)};`,'\t\t\treturn r;');
}
g.push('\t}','\treturn undefined;','}','function get_drop_by_flag( flag )','{','\tswitch ( flag )','\t{');
if(DESCENT)for(const lap of BROKEN_TOWER.DROP_LAPS)g.push(`\t\tcase "enter_lap${lap}": return get_drop_info( ${lap} );`);
g.push('\t}','\treturn undefined;','}');
fs.writeFileSync(DOOR_GSC_OUT, g.join('\n'), 'utf8');
console.log(`wrote ${DOOR_GSC_OUT}  (${DOORS.length} doors)`);

// ---------------------------------------------------------------------------
// Output: _tod_crown_data.gsc — the finale's anchor points (v9)
// ---------------------------------------------------------------------------
// Everything _tod_finale.gsc and the crown upgrade terminal need to place
// themselves, in the SAME mirrored frame the brushes were cut in. Vectors are
// emitted pre-mirrored, so the GSC never has to know about parity.
const vec = ([x, y, z]) => `( ${x}, ${y}, ${z} )`;
const SCONCES = [];
{
  // v16.35 THE BASILICA: the same twelve sconces (six a side, +200, the
  // acceptance sequence still walks them gate -> pad), re-spaced to clear the
  // shrine bays — pilasters at HYC+-112..+-144 and a canopy at +216..+248 sit
  // exactly where the old 208-pitch put rows 3 and 4. Symmetric about HYC,
  // ascending y so the ignition order is unchanged.
  for (const d of [-560, -372, -188, 188, 372, 560]) {
    const y = HYC + d;
    SCONCES.push({ org: cpt(-HW + HWALL + 2, y, TOP2 + 200), yaw: cyaw(0) });
    SCONCES.push({ org: cpt(HW - HWALL - 2, y, TOP2 + 200), yaw: cyaw(180) });
  }
}
const c = [];
c.push('// GENERATED by tools/gen_tower_map.js — DO NOT HAND-EDIT (regen instead).');
c.push('// Anchor points for the CROWN finale (_tod_finale.gsc) and the crown');
c.push('// upgrade terminal (_tod_upgrades.gsc). Emitted from the same tables that');
c.push('// cut the crown brushes, already point-mirrored for the crown lap parity');
c.push(`// (LAPS=${LAPS}, crown lap ${CROWN_LAP} is ${CROWN_ODD ? 'ODD: east stair, north hall' : 'EVEN: west stair, south hall'}).`);
c.push('');
c.push('#namespace tod_crown_data;');
c.push('');
c.push(`function crown_z()         { return ${TOP2}; }`);
// THE UPLINK MOVED TO THE TERRACE (v10, 2026-08-23). The finale clock is the
// length of the closing song and the run is the road, so the console that
// starts it has to sit where the players ARRIVE, not at the far end of the
// thing they are about to run. Placed WEST of the causeway mouth (mouth is
// x +/-CW_HALF) so it never blocks the road, and facing the road.
c.push(`function uplink_org()      { return ${vec(cpt(-(CW_HALF + 96), (TER_Y1 + TER_Y2) / 2, TOP2))}; }`);
c.push(`function uplink_yaw()      { return ${cyaw(0)}; }`);
// the old hall-dais spot — kept as an anchor so the dais brush still has a
// named centre and a future boss fight has the hall's focal point.
c.push(`function dais_org()        { return ${vec(cpt(0, HYC, TOP2 + DAIS_H))}; }`);
// causeway portal frame centres, south -> north: the road's milestones.
c.push('function portal_orgs()');
c.push('{');
c.push('	a = [];');
(() => { causewayPortalPoints().forEach((o, k) => c.push('	a[ ' + k + ' ] = ' + vec(o) + ';')); })();
c.push('	return a;');
c.push('}');
// THE CAUSEWAY GATE: where it stands, and what counts as being past it.
// beyond_gate() is the spawn filter's test — while the gate is shut, the road
// and the citadel behind it are pathing-severed from the terrace, so a zombie
// risen out there can never reach anybody. It would just stand on the bridge
// holding a slot under the actor cap for the rest of the game. Un-mirrors y by
// CM so the test reads in the crown's own frame whichever parity the crown got.
c.push(`function causeway_gate_org() { return ${vec(cpt(0, TER_Y2 + 12, TOP2 + 128))}; }`);
c.push('function beyond_gate( org )');
c.push('{');
c.push(`	y = org[ 1 ] * ${CM};`);
c.push(`	return ( y > ${TER_Y2} && org[ 2 ] > ${CW_ZMIN} );`);
c.push('}');
// THE CROWN DOOR and the two containment tests the finale runs on.
//
// in_crown() IS THE WIN TEST and it is a BOX, not a radius. The old
// TOD_FINALE_ARRIVE_RAD 1536 sphere from the exfil pad reached ~284 units
// OUTSIDE the gate, so a player standing on the approach counted as "in the
// Crown" — fine when arriving was the whole win, wrong now that arriving is
// what SEALS THE DOOR ON YOU. This is the hall's actual interior: inside the
// four walls, above the floor, with a small inset so someone hugging a wall
// still reads as in.
//
// in_hall() is the same box widened to the gate line — used by the spawn filter
// during the hold-out so risers on the causeway are dropped once the party is
// sealed in (a zombie out there could never reach them and would hold an actor
// slot for the rest of the fight, the same trap beyond_gate() exists to stop).
c.push(`function crown_door_org()  { return ${vec(cpt(0, HS + HWALL / 2, TOP2 + GATE_H / 2))}; }`);
c.push('function in_crown( org )');
c.push('{');
c.push(`	y = org[ 1 ] * ${CM};`);
c.push(`	x = org[ 0 ] * ${CM};`);
c.push(`	if ( x < ${-(HW - HWALL - 8)} || x > ${HW - HWALL - 8} ) return false;`);
c.push(`	if ( y < ${HS + HWALL} || y > ${HN - HWALL} ) return false;`);
c.push(`	return ( org[ 2 ] > ${TOP2 - 64} && org[ 2 ] < ${TOP2 + 400} );`);
c.push('}');
c.push('function in_hall( org )');
c.push('{');
c.push(`	y = org[ 1 ] * ${CM};`);
c.push(`	x = org[ 0 ] * ${CM};`);
c.push(`	if ( x < ${-HW} || x > ${HW} ) return false;`);
c.push(`	if ( y < ${HS} || y > ${HN} ) return false;`);
c.push(`	return ( org[ 2 ] > ${TOP2 - 64} );`);
c.push('}');
// v16.35: the pad sits on the sanctuary — its top is TOP2 + PAD_TOP (section
// 5d), and the prop, the derez bursts and the +30 trigger all hang off this.
c.push(`function exfil_org()       { return ${vec(cpt(0, EXFIL_Y, TOP2 + PAD_TOP))}; }`);
c.push(`function exfil_radius()    { return ${EXFIL_HALF + 16}; }`);
c.push(`function hall_center()     { return ${vec(cpt(0, HYC, TOP2))}; }`);
c.push(`function gate_org()        { return ${vec(cpt(0, HS + HWALL / 2, TOP2))}; }`);
// docs/160 — THE FALL GATE's slab as a world-space AABB (pre-mirrored, mins
// < maxs at either parity): _tod_fall refuses to re-solidify the slab while
// any living player's origin is inside it (+ a hull margin) — the crush case
// every door slab in this map has been careful about.
{
  const g = cspec({ x1: -GATE_HALF, x2: GATE_HALF, y1: HS, y2: HS + HWALL, z1: TOP2, z2: TOP2 + GATE_H });
  c.push(`function fall_gate_mins()  { return ( ${g.x1}, ${g.y1}, ${g.z1} ); }`);
  c.push(`function fall_gate_maxs()  { return ( ${g.x2}, ${g.y2}, ${g.z2} ); }`);
}
// docs/160 — THE HALL'S FOUR RISER SPOTS (the crown_zone risers, pre-mirrored):
// where THE FALL's Doppelghast hunters come up. _tod_fall picks the one
// farthest from the nearest living player. The same four coordinates the
// ZONES table emits as crown_zone's risers — one source, read twice.
c.push('function hall_riser_orgs()');
c.push('{');
c.push('	a = [];');
[[-560, HS + 280], [560, HS + 280], [-560, HN - 280], [560, HN - 280]].forEach(([rx, ry], k) => {
  c.push('	a[ ' + k + ' ] = ' + vec(cpt(rx, ry, TOP2)) + ';');
});
c.push('	return a;');
c.push('}');
// docs/160 §10 — THE ALARM: the ruby core's centre (section 5d' of the map)
// = the pivot the two orbiting glow hosts turn about, and the siren's origin.
c.push(`function alarm_org()       { return ${vec(cpt(ALARM_ORG[0], ALARM_ORG[1], ALARM_ORG[2]))}; }`);
// Physical alarms: every hall pier, original pendant, every rim point and apex.
// Coordinates derive from the SAME geometry constants; no hand-entered mounts.
const ALARM_MOUNTS = [];
for (const sx of [-1, 1]) for (const py of PIER_Y)
  ALARM_MOUNTS.push({org:cpt(sx*NAVE_X,py,BEAM_Z2),angles:[0,cyaw(sx<0?0:180),0],scale:1,kind:'pillar'});
ALARM_MOUNTS.push({org:cpt(0,HYC,ALARM_PEND_Z1),angles:[180,cyaw(0),0],scale:1,kind:'pendant'});
for (const [px,py,kind] of CR_POINTS) {
  const height = kind === 'short' ? CR_RIM_Z+CS(1552)
    : kind === 'front' ? CR_RIM_Z+CS(2752)
    : CR_RIM_Z+TALL_SHAFT_H+TALL_HEAD_H+TALL_CAP_H+TALL_PIP_H+CS(224);
  ALARM_MOUNTS.push({org:cpt(px,py,TOP2+height),angles:[0,cyaw(Math.atan2(py-CR_CY,px)*180/Math.PI),0],scale:4,kind:'point'});
}
ALARM_MOUNTS.push({org:cpt(0,CR_CY,CROWN_TOP),angles:[0,cyaw(0),0],scale:4,kind:'apex'});
if (ALARM_MOUNTS.length !== 30) throw new Error('Crown alarm mount count drift');
for (const [name,key] of [['orgs','org'],['angles','angles'],['scales','scale'],['kinds','kind']]) {
  c.push(`function alarm_mount_${name}()`,'{','\ta = [];');
  ALARM_MOUNTS.forEach((m,i)=>c.push(`\ta[ ${i} ] = ${Array.isArray(m[key])?vec(m[key]):typeof m[key]==='string'?JSON.stringify(m[key]):m[key]};`));
  c.push('\treturn a;','}');
}
const alarmReview=path.join(__dirname,'..','art','crown_alarm');
fs.mkdirSync(alarmReview,{recursive:true});
fs.writeFileSync(path.join(alarmReview,'mounts.json'),JSON.stringify(ALARM_MOUNTS,null,2)+'\n');
// THE LEVER (user 2026-09-24/25, _tod_fall.gsc TOD_FALL_LEVER): the stock
// power switch's two models, script-spawned in THE ENCLOSED HALLWAY'S POWER
// ROOM (HW_LEVER) against its east wall, front to the room (yaw 270: the
// prefab's front is its -y side at yaw 0). Asserted inside the room with the
// body clear of the wall column and the use trigger (28 in front, r 48) inside.
{
  if (!CW_CUT) throw new Error('the lever needs the enclosed hallway (CW_CUT)');
  const [lx, ly] = HW_LEVER, LEVER_FRONT = 28, LEVER_TRIG_R = 48;
  if (lx + 12 >= HW_POWER.x2 - 4) throw new Error('lever body reaches the power room wall');
  if (lx - LEVER_FRONT - LEVER_TRIG_R <= HW_POWER.x1) throw new Error('lever trigger leaves the power room');
  if (ly - LEVER_TRIG_R <= HW_POWER.y1 || ly + LEVER_TRIG_R >= HW_POWER.y2) throw new Error('lever trigger reaches the power room side walls');
  c.push(`function lever_org()       { return ${vec(cpt(lx, ly, TOP2))}; }`);
  c.push(`function lever_yaw()       { return ${cyaw(270)}; }`);
  // THE GRID TERMINAL (docs/208): the power switch's panel, on the east wall (POWER_TERM), and its trigger
  c.push(`function power_terminal_org()  { return ${vec(cpt(POWER_TERM.org[0], POWER_TERM.org[1], TOP2))}; }`);
  c.push(`function power_terminal_yaw()  { return ${cyaw(POWER_TERM.yaw)}; }`);
  c.push(`function power_terminal_trig() { return ${vec(cpt(POWER_TERM.trig[0], POWER_TERM.trig[1], TOP2 + POWER_TERM_TRIG_LIFT))}; }`);
}
// The right-hand crown pad now belongs to _tod_teleport and links the base.
// Existing anchors remain available to geometry and room checks.
{
  const [tx, ty] = HW_TELE_ORG;
  if (tx - 100 <= HW_TELE.x1 || tx + 100 >= HW_TELE.x2 || ty - 100 <= HW_TELE.y1 || ty + 100 >= HW_TELE.y2)
    throw new Error('the teleporter prop does not fit its room');
  c.push(`function crown_tele_org()  { return ${vec(cpt(tx, ty, TOP2))}; }`);
  c.push(`function crown_tele_yaw()  { return ${cyaw(0)}; }`);
}
// THE RAMPAGE INDUCER ON THE BALCONY (see CROWN_INDUCER): _tod_rampage spawns
// the device here instead of the base arena whenever jumppad_enabled(). Its use
// radius must stay clear of the pad trigger, the display shop's hull, Quick
// Revive and the balcony rails.
{
  const [ix, iy] = CROWN_INDUCER, r = CROWN_INDUCER_TRIG_R;
  if (Math.hypot(ix - JP_PAD[0], iy - JP_PAD[1]) < r + JP_PAD_R + 120) throw new Error('the inducer trigger crowds the jump pad');
  const shop = CROWN_SHOPS[1];
  if (Math.hypot(ix - shop.x, iy - shop.y) < r + 160) throw new Error('the inducer crowds the display shop');
  if (Math.hypot(ix - TERRACE_QR[0], iy - TERRACE_QR[1]) < r + 160) throw new Error('the inducer crowds Quick Revive');
  if (ix + 40 > JP_LAUNCH_HALF - 20 || ix - 40 < -JP_LAUNCH_HALF + 20 || iy - 40 < JP_LAUNCH_Y1 + 20 || iy + 40 > JP_LAUNCH_Y2 - 20)
    throw new Error('the inducer body is not inside the balcony');
  c.push(`function crown_inducer_org()    { return ${vec(cpt(ix, iy, TOP2))}; }`);
  c.push(`function crown_inducer_yaw()    { return ${cyaw(180)}; }   // faces the pad (west)`);
  c.push(`function crown_inducer_trig_r() { return ${r}; }`);
  c.push(`function crown_inducer_trig_lift() { return ${INDUCER_TRIG_LIFT}; }   // docs/208: in the slot over the body clip`);
}
// THE ALARM BUTTON (user 2026-09-28, replacing the 2026-09-25 alarm switch on the sanctuary's top step): a red
// button on a stand in the CENTRE of the crown hall, on the uplink dais, facing the spawn rows (north of it, facing
// south). The clip is cut beside the crown crate block above. Asserted clear of the spawn rows (a player never
// spawns in the stand) and inside the dais.
{
  if (ABTN_HALF >= DAIS) throw new Error('alarm button stand is wider than the dais');
  if (HYC + ABTN_HALF + 16 >= HALL_SPAWN_Y[0] - 30) throw new Error('alarm button stand reaches the spawn rows');
  c.push(`function alarm_button_org() { return ${vec(cpt(0, HYC, TOP2 + DAIS_H))}; }`);
  c.push(`function alarm_button_yaw() { return ${cyaw(90)}; }   // faces the spawn rows`);
}
// THE POWER WAVE (2026-09-25, user: "once power's on things will light up
// dynamically ... as it's turning on"; picked A WAVE DOWN THE TOWER). One point
// per floor, TOP DOWN (lap 50 .. lap 1, then the plaza): each floor's own "mid"
// light position (the tower light block's odd/even corners) and its DISTRICT's
// todPerkGlow index (blue 6 / green 2 / orange 4 / yellow 3 / red 1 — the perk
// glow FX, a coloured looping light). _tod_fall plays them one after another
// from the power switch, then flips the baked lighting state on.
{
  const GLOW = { blue: 6, green: 2, orange: 4, yellow: 3, red: 1 };
  const pts = [], fx = [];
  for (let lap = LAPS - 1; lap >= 0; lap--) {
    const b = lap * LAP_RISE, sgn = (lap % 2 === 0) ? 1 : -1;
    pts.push([sgn * 336, sgn * 336, b + FLIGHT_RISE + 160]);
    fx.push(GLOW[districtOf(lap).key]);
  }
  pts.push([0, 0, 240]); fx.push(GLOW.blue);   // the plaza, last
  if (fx.some(v => v === undefined)) throw new Error('power wave: a district has no glow index');
  c.push('function wave_orgs()', '{', '\ta = [];');
  pts.forEach((p, i) => c.push(`\ta[ ${i} ] = ${vec(p)};`));
  c.push('\treturn a;', '}');
  c.push('function wave_fx()', '{', '\ta = [];');
  fx.forEach((v, i) => c.push(`\ta[ ${i} ] = ${v};`));
  c.push('\treturn a;', '}');
}
// docs/163 THE JUMP PAD — _tod_jumppad.gsc's anchors, pre-mirrored. The pad
// throws from the crown's stub to the terrace's; jumppad_enabled() is 0 when
// the road is whole (CW_CUT false) and the module then does nothing.
// on_crown_island(): the hall PLUS its stub (launch deck, approach, flare) —
// everything only the hall can reach on foot. _tod_fall seals once no living
// player is on it (the stub counts: a player waiting at the pad has not left
// the crown), and clears every ordinary zombie left on it at the seal.
c.push(`function jumppad_enabled()     { return ${CW_CUT ? 1 : 0}; }`);
c.push(`function jumppad_launch_org()  { return ${vec(cpt(JP_PAD[0], JP_PAD[1], TOP2))}; }`);
c.push(`function jumppad_launch_yaw()  { return ${cyaw(JP_PAD_YAW)}; }   // the DE machine: its doorway faces the bridge corridor, its open side the tower`);
c.push(`function jumppad_trigger_r()   { return ${JP_PAD_R}; }`);
// THE BALCONY BOX (2026-09-29, user: "the first song starts up once you enter the crown balcony
// that the jump pad lives on ... That way music is started already and cinematic view is
// enhanced"): _tod_atmosphere starts the descent's first band the moment a living player stands
// in the launch deck's footprint (feet 64 below the deck to 256 above it, so a jump still counts).
{
  const a = cpt(-JP_LAUNCH_HALF, JP_LAUNCH_Y1, TOP2 - 64), b = cpt(JP_LAUNCH_HALF, JP_LAUNCH_Y2, TOP2 + 256);
  c.push(`function jumppad_balcony_mins() { return ${vec([Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.min(a[2], b[2])])}; }`);
  c.push(`function jumppad_balcony_maxs() { return ${vec([Math.max(a[0], b[0]), Math.max(a[1], b[1]), Math.max(a[2], b[2])])}; }`);
}
c.push(`function jumppad_land_center() { return ${vec(cpt(JP_LAND[0], JP_LAND[1], TOP2))}; }`);
c.push(`function jumppad_land_yaw()    { return ${cyaw(JP_LAND_YAW)}; }   // the DE landing pad: its exit side faces the terrace`);
c.push('function jumppad_land_orgs()');
c.push('{');
c.push('	a = [];');
JP_LAND_SPOTS.forEach(([sx, sy], k) => c.push('	a[ ' + k + ' ] = ' + vec(cpt(sx, sy, TOP2)) + ';'));
c.push('	return a;');
c.push('}');
c.push('function on_crown_island( org )');
c.push('{');
if (CW_CUT) {
  c.push(`	y = org[ 1 ] * ${CM};`);
  c.push(`	x = org[ 0 ] * ${CM};`);
  // the hall's box OR the stub's (JP_CRN_BOX derives from the crown-side
  // road cells, so the balcony and the overlook rooms are inside by construction)
  c.push(`	if ( x < ${Math.min(-(HW + 64), JP_CRN_BOX.x1)} || x > ${Math.max(HW + 64, JP_CRN_BOX.x2)} ) return false;`);
  c.push(`	if ( y < ${Math.min(JP_LAUNCH_Y1 - PARA - 64, JP_CRN_BOX.y1)} || y > ${HN + 16} ) return false;`);
  c.push(`	return ( org[ 2 ] > ${TOP2 - 256} );`);
} else {
  c.push('	return in_hall( org );');
}
c.push('}');
c.push(`function mast_tip_org()    { return ( 0, 0, ${MAST_TOP} ); }`);
c.push('// Item shops: same table as the generated collision hulls. Front is local -Y.');
for (const key of ['orgs','yaws']) {
  c.push(`function shop_${key}()`,'{','\ta = [];');
  CROWN_SHOPS.forEach((p,i)=>c.push(`\ta[ ${i} ] = ${key==='orgs'?vec(cpt(p.x,p.y,p.z)):cyaw(p.yaw)};`));
  c.push('\treturn a;','}');
}
// THE CROWN UPGRADE STATION — STANDOFF 33 -> 64 (user live report 2026-08-28:
// "final boss room. Pap is inside the wall"). The machine is the
// `chaos_pack_a_punch` mesh (it is the UPGRADE STATION, not a Pack-a-Punch —
// the map has no PaP prefab at all), and it was the tightest-placed of the
// six stations by a wide margin:
//     base station      64u off the core's south face   (model 0,-320 vs CORE 256)
//     breather lounges  44u off the lounge's N wall     (BR_FURN, v13)
//     crown hall        33u off the hall's W wall       <<< the reported one
// The hall's west wall inner face is x = -HW + HWALL = -728, so 33 put the
// origin at -695. 64 matches the BASE station, which is the longest-shipped
// placement of this exact model and has never been reported.
//
// WHY 64 AND NOT A MEASURED NUMBER, STATED HONESTLY: the width profile of this
// mesh is measured (see the long note in _tod_upgrades::station_place — 957,902
// vertex records binned by height, +-52 at the chest-height flare), but that
// pass recorded DEPTH only as a single "53" and never established whether the
// origin sits at the mesh's centre or its front face. If it is centred, 33
// should have cleared by ~6u and something else is wrong; if the body hangs
// backward from the origin, 33 buries it and 64 fixes it. The report says it is
// buried, and 64 is the standoff already proven on the same asset, so this
// takes the proven number rather than a derived one. If it is STILL in the wall
// after this, the origin is not the issue and the next step is to actually
// measure the depth axis off chaos_pack_a_punch.xmodel_bin (LZ4-wrapped; the
// width pass is the recipe) rather than nudging it again.
//
// v16.35 THE BASILICA: the altar moves 300u north to the WEST SHRINE at the
// crossing (y = HYC), facing the Pack-a-Punch in the east shrine across the
// dais. Standoff 64 unchanged. Its bay (pilasters at HYC+-112..+-144, glow
// panel, canopy +216) is cut in section 5d.
// CLEARANCES at the new spot (the trigger keeps its 40u face offset and floats
// +32 since v16.27):
//   trigger (-624, HYC) r64 -> pilaster faces at y HYC+-112: 48u clear;
//     nearest pier base (W3/W4 at y HYC-+184) starts at x -440: 184u clear
//   3 collision clips spread +-32 along AnglesToForward (= +-y at yaw 90),
//     so they move with the model and stay between the pilasters
//   the transept seam under its approach is 1u walk-over
c.push(`function station_org()     { return ${vec(cpt(-HW + HWALL + 64, HYC, TOP2))}; }`);
c.push(`function station_trig_org(){ return ${vec(cpt(-HW + HWALL + 104, HYC, TOP2))}; }`);
c.push(`function station_yaw()     { return ${cyaw(90)}; }`);
c.push('');
c.push('// THE HALL AMMO CRATE (v12) — spawned by _tod_ammo_crate.gsc, which reads');
c.push('// these instead of hardcoding, so the crate and its generator-emitted');
c.push('// collision clip (label "crown hall ammo crate body") can never drift.');
c.push(`function crown_crate_org() { return ${vec(cpt(CRATE_ORG[0], CRATE_ORG[1], TOP2))}; }`);
c.push(`function crown_crate_yaw() { return ${cyaw(CRATE_YAW)}; }`);
c.push('');
c.push('// The finale\'s four QUARTER-PROGRESS beacons — one ignites per quarter of');
c.push('// the closing song (_tod_finale::ignite_pylon). These are the CIRCLET\'s');
c.push('// four corner point caps, NOT anything in the hall: v11 moved the read up');
c.push('// there when the user rejected the old in-room coil models ("weird looking');
c.push('// pipe level model on top"). NOTE v12: the four bare PILLARS returned to');
c.push('// the hall at their old +-448 spots — as pure scenery/cover with NO script');
c.push('// contract. Do not point these beacons back at them; the progress read is');
c.push('// the crown lighting up around you — legible from inside the hall, from');
c.push('// the causeway, and from the tower. The function name is unchanged on');
c.push('// purpose: _tod_finale.gsc needed a model swap, not a rewrite.');
c.push('function pylon_orgs()');
c.push('{');
c.push('\ta = [];');
CROWN_BEACON_XY.forEach(([bx, by], i) => {
  // Finale's separate progress props clear the new 4x alarm housing (193.4u).
  c.push(`\ta[ ${i} ] = ${vec(cpt(bx, by, TOP2 + CROWN_BEACON_Z + 194))};`);
});
c.push('\treturn a;');
c.push('}');
c.push('');
c.push('// wall sconces (light panels) on the two long walls — parallel arrays');
c.push('function sconce_orgs()');
c.push('{');
c.push('\ta = [];');
SCONCES.forEach((s, i) => c.push(`\ta[ ${i} ] = ${vec(s.org)};`));
c.push('\treturn a;');
c.push('}');
c.push('function sconce_yaws()');
c.push('{');
c.push('\ta = [];');
SCONCES.forEach((s, i) => c.push(`\ta[ ${i} ] = ${s.yaw};`));
c.push('\treturn a;');
c.push('}');
c.push('');
// ---------------------------------------------------------------------------
// THE FINALE BEAT SYSTEM (v12.13, docs/41: A1 tide + A2 boss beats + A4
// arrival + riders + B1 lane lottery). Every anchor below is derived from the
// same cwY/lane tables that cut the road, so script and geometry cannot drift.
// ---------------------------------------------------------------------------
c.push('// --- THE FINALE BEAT SYSTEM (v12.13, docs/41) — road-derived anchors -----');
c.push('// road_y: the mirrored y — compare against tide/beat y thresholds with THIS,');
c.push('// never with raw org[1] (the crown lap parity flips the whole road).');
c.push(`function road_y( org )     { return org[ 1 ] * ${CM}; }`);
c.push('// (tide_start_y/tide_end_y/road_north_yaw/tide_curtain_orgs were emitted');
c.push('// here for exactly one day — THE DEREZ TIDE, added and removed 2026-08-27;');
c.push('// post-mortem at the top of _tod_finale.gsc\'s beat table.)');
c.push('// BOSS BEATS (A2): the Panzer lands at the NARROWS north lip (80 past the');
c.push('// pinch exit, on full-width throat deck — fightable from the 320 throat);');
c.push('// two protectors land on the gate APPROACH as the leader crosses J4.');
c.push(`function beat_narrows_org()        { return ${vec(cpt(0, cwY[4] + 560, TOP2))}; }`);
c.push(`function beat_narrows_trigger_y()  { return ${cwY[4]}; }   // leader entering the throat`);
c.push('function beat_flare_orgs()');
c.push('{');
c.push('\ta = [];');
// ±60 on the 160-wide approach and 140 short of the mouth (review FIX 3,
// 2026-08-27): the first cut sat at ±100/y7600 — INSIDE the derived rail
// column over the void, where SpawnActor eats half the boss roof for nothing.
c.push(`\ta[ 0 ] = ${vec(cpt(-60, cwY[9] - 140, TOP2))};`);
c.push(`\ta[ 1 ] = ${vec(cpt(60, cwY[9] - 140, TOP2))};`);
c.push('\treturn a;');
c.push('}');
c.push(`function beat_flare_trigger_y()    { return ${cwY[7]}; }   // leader crossing J4`);
c.push('// A4: the hold-out opener Panzer crashes into the hall here — on open nave');
c.push('// floor: 317u from hall_center (gather ring 160), 92u short of the');
c.push('// sanctuary foot, 136u inside the east pier line (v16.35 basilica).');
c.push(`function siege_panzer_org()        { return ${vec(cpt(192, HYC + 252, TOP2))}; }`);
c.push('// THE CROWN\'S HEARTBEAT rider: the girandole — same coordinate as its');
c.push('// baked light (the ruby drop-pendant under the vortex bell).');
c.push(`function girandole_org()           { return ${vec(cpt(0, CR_CY - CS(480), TOP2 + CR_SKIRT_BOT - CS(480)))}; }`);
c.push('// THE COUNTDOWN AVENUE (A1): glow hosts on the 8 avenue pylon PIPS (pip');
c.push('// body spans +496..+576 over the deck; host at its centre) — ignited blue');
c.push('// at the buy, strobed green on the win (the tide-era red flip is gone).');
c.push('function avenue_pylon_orgs()');
c.push('{');
c.push('\ta = [];');
(() => {
  let k = 0;
  for (const [px, py] of AVENUE)
    for (const sx of [-1, 1])
      c.push(`\ta[ ${k++} ] = ${vec(cpt(sx * px, py, TOP2 + 536))};`);
})();
c.push('\treturn a;');
c.push('}');
c.push('// A4 pillar count-in hosts: the FOUR CROSSING PIERS of the basilica');
c.push('// (v16.35), 16u above the beam top (+216) and well under the +260 lights.');
c.push('function hall_pillar_orgs()');
c.push('{');
c.push('\ta = [];');
(() => {
  [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([sx, sy], i) => {
    c.push(`\ta[ ${i} ] = ${vec(cpt(sx * NAVE_X, HYC + sy * 184, BEAM_Z2 + 16))};`);
  });
})();
c.push('\treturn a;');
c.push('}');
c.push('// THE LANE LOTTERY (B1). Parallel arrays, index = tod_lane_seal_<i>:');
c.push('//   0 f1 W ridge | 1 f1 E broken stair | 2 f2 W undercroft | 3 f2 C plank | 4 f2 E weave');
c.push('// seal_orgs: slab centres (FX anchors). slab/band mins+maxs: WORLD-space');
c.push('// AABBs (pre-mirrored — test raw org x/y against them, no road_y). The');
c.push('// BAND is the whole lane footprint fork->merge, for the riser filter.');
(() => {
  const mb = (x1, x2, y1, y2) => (CM === 1 ? [x1, x2, y1, y2] : [-x2, -x1, -y2, -y1]);
  // docs/163 THE CUT: no lanes -> five empty arrays (the lottery never runs:
  // lane_seals_init finds no slab entity and leaves level.tod_lane_seals unset).
  const seals = CW_CUT ? [] : [
    [LX[0], LX[1], cwY[2]], [EX[0], EX[1], cwY[2]],
    [LX[0], LX[1], cwY[6]], [PX_[0], PX_[1], cwY[6]], [EX[0], EX[1], cwY[6]],
  ];
  const bands = CW_CUT ? [] : [
    // bstair is EX-only (review FIX 6 — the EW copy-paste came from the weave
    // row; the ridge legitimately spans LW..LX and the weave EX..EW)
    [LW[0], LX[1], cwY[2], cwY[3]], [EX[0], EX[1], cwY[2], cwY[3]],
    [LW[0], LX[1], cwY[6], cwY[7]], [PX_[0], PX_[1], cwY[6], cwY[7]], [EX[0], EW[1], cwY[6], cwY[7]],
  ];
  c.push('function lane_seal_orgs()');
  c.push('{');
  c.push('\ta = [];');
  seals.forEach(([x1, x2, y], i) =>
    c.push(`\ta[ ${i} ] = ${vec(cpt((x1 + x2) / 2, y + 12, TOP2 + 128))};`));
  c.push('\treturn a;');
  c.push('}');
  const emitMM = (name, rows, lo) => {
    c.push(`function ${name}()`);
    c.push('{');
    c.push('\ta = [];');
    rows.forEach((r, i) => {
      const m = mb(r[0], r[1], r[2], r[3]);
      c.push(`\ta[ ${i} ] = ( ${lo ? m[0] : m[1]}, ${lo ? m[2] : m[3]}, 0 );`);
    });
    c.push('\treturn a;');
    c.push('}');
  };
  const slabs = seals.map(([x1, x2, y]) => [x1, x2, y, y + 24]);
  emitMM('lane_seal_slab_mins', slabs, true);
  emitMM('lane_seal_slab_maxs', slabs, false);
  emitMM('lane_band_mins', bands, true);
  emitMM('lane_band_maxs', bands, false);
})();
c.push('');
// Top/bottom transit routes: geometry and runtime cannot acquire separate literals.
c.push('// Fixed transit network: four reached-floor pairs and the base/crown pair.');
c.push('function transit_routes()');c.push('{');c.push('    a = [];');
for(const row of TRANSIT_ROUTES) {
  c.push('    r = SpawnStruct();');
  for(const key of ['id','lock','zone','hint','arrival_flag'])c.push(`    r.${key} = "${row[key]}";`);
  for(const key of ['src','dst'])c.push(`    r.${key} = ${vec(row[key])};`);
  for(const key of ['src_yaw','dst_yaw'])c.push(`    r.${key} = ${row[key]};`);
  c.push(`    r.return_crown = ${row.return_crown?'true':'false'};`);
  c.push('    a[ a.size ] = r;');
}
c.push('    return a;');c.push('}');
// docs/196 THE DEPARTURE HALL's ambience: _tod_atmosphere plays these stock
// looping effects (the lounges' own, already zoned) at these anchors.
c.push('');
c.push('// Transit hall ambient FX (docs/196): level._effect key + world origin, from tower_transit_layout.js FX.');
c.push('function transit_hall_fx()');c.push('{');c.push('    a = [];');
for(const f of TRANSIT.FX) {
  c.push('    s = SpawnStruct();');
  c.push(`    s.fx = "${f.key}";`);
  c.push(`    s.org = ${vec(cpt(f.org[0],f.org[1],TOP2+f.org[2]))};`);
  c.push('    a[ a.size ] = s;');
}
c.push('    return a;');c.push('}');
fs.writeFileSync(CROWN_GSC_OUT, c.join('\n'), 'utf8');
console.log(`wrote ${CROWN_GSC_OUT}  (crown lap ${CROWN_LAP}, CM=${CM}, TOP2=${TOP2}, mast top=${MAST_TOP})`);

// ---------------------------------------------------------------------------
// Output: _tod_breather_data.gsc — the lounge furniture anchors (v13)
// ---------------------------------------------------------------------------
// _tod_powerups (PaP), _tod_upgrades (station), _tod_ammo_crate (crate) and
// _tod_teleport (spur pad + up-ride arrival) read these instead of hardcoding,
// so the room, the crate's generator-emitted collision clip and the four
// scripts can never drift — the same contract as _tod_door_data /
// _tod_crown_data. All values are in the EVEN (mirrored) frame every breather
// sits in (asserted at BREATHER_THEME). _tod_perk_scatter deliberately keeps
// its own pad table (its machines relocate at runtime); the S-wall pads are
// mirrored into BR_FURN for the spacing assert only.
{
  const bd = [];
  bd.push('// GENERATED by tools/gen_tower_map.js — DO NOT HAND-EDIT (regen instead).');
  bd.push('// The haven (docs/202) furniture anchors. Source of truth: tools/haven_layout.js');
  bd.push('// in the generator, which asserts every pair of use-triggers clears by');
  bd.push(`// radius_a + radius_b + ${MIN_TRIG_GAP} at generation time — the mechanical form of the`);
  bd.push('// v10.4 rule, added after the shipped PaP/crate pair sat 174u apart with a');
  bd.push('// 38u rim gap and players bought the wrong 5000-point thing.');
  bd.push('// Frame: EVEN/mirrored (all four breathers). z = the lounge mid-slab top.');
  bd.push('');
  bd.push('#namespace tod_breather_data;');
  bd.push('');
  bd.push('// mid-slab z of each breather lounge, ascending (laps 10/20/30/40)');
  const BRZS = [...BREATHER_LAPS].sort((a, b2) => a - b2).map(l => (l - 1) * LAP_RISE + FLIGHT_RISE);
  bd.push(`function breather_zs() { return array( ${BRZS.join(', ')} ); }`);
  bd.push('');
  bd.push('// Shared room detection for the arrival chime and spawn-pressure relief:');
  bd.push('// the haven hall (docs/202 v2) — the hall, its porch and its loggia. The z band');
  bd.push("// stops under the next lap's E flight (its first tread is 204 above the hall).");
  bd.push('function lounge_index_at( o )');
  bd.push('{');
  bd.push('    zs = breather_zs();');
  bd.push('    for ( j = 0; j < zs.size; j++ )');
  bd.push('    {');
  bd.push('        if ( o[ 2 ] < zs[ j ] - 64 || o[ 2 ] > zs[ j ] + 160 ) continue;');
  for (const R of HAVEN.ROOM_RECTS)
    bd.push(`        if ( o[ 0 ] >= ${R.x1} && o[ 0 ] <= ${R.x2} && o[ 1 ] >= ${R.y1} && o[ 1 ] <= ${R.y2} ) return j;`);
  bd.push('    }');
  bd.push('    return -1;');
  bd.push('}');
  const bfun = (name, [x, y]) => bd.push(`function ${name}( z ) { return ( ${x}, ${y}, z ); }`);
  bd.push('');
  bd.push('// PACK-A-PUNCH — in the east loggia, facing the field');
  bfun('pap_org', BR_FURN.pap.org);
  bfun('pap_trig', BR_FURN.pap.trig);
  bd.push(`function pap_yaw() { return ${BR_FURN.pap.yaw}; }`);
  bd.push('');
  bd.push('// UPGRADE STATION — in the east loggia, facing the field');
  bfun('station_org', BR_FURN.station.org);
  bfun('station_trig', BR_FURN.station.trig);
  bd.push(`function station_yaw() { return ${BR_FURN.station.yaw}; }`);
  bd.push('');
  bd.push("// AMMO CRATE — the loggia's north-east corner, facing the field (its collision clip in the .map is cut");
  bd.push('// from this same origin: label "ammo crate body", lint MODEL_CLIP_COLUMNS)');
  bfun('crate_org', BR_FURN.crate.org);
  bd.push(`function crate_yaw() { return ${BR_FURN.crate.yaw}; }`);
  bd.push('');
  bd.push('// THE CRATE TRIGGER RECIPE (v17.38) — read by _tod_ammo_crate::spawn_trigger for');
  bd.push('// EVERY crate in the map (tower, crown and arena): the trigger_radius_use sits');
  bd.push('// crate_trig_out() in FRONT of the crate origin (front = yaw + 90) with this');
  bd.push('// radius. The generator asserts the same numbers against every other');
  bd.push('// vendor trigger in the lounges, so they live here, once.');
  bd.push(`function crate_trig_out() { return ${CRATE_TRIG_OUT}; }`);
  bd.push(`function crate_trig_r()   { return ${CRATE_TRIG_R}; }`);
  bd.push('');
  bd.push('// BASE AMMO CRATE — core WEST face at the base arena, ABSOLUTE coords (no');
  bd.push('// mirror frame; the base is authored absolute). v14.3: origin lives in the');
  bd.push('// generator (BASE_CRATE), which also cuts its "base ammo crate body" clip');
  bd.push('// brush and asserts it clear of the lap-1 E flight — the Workshop navmesh');
  bd.push('// report (Pinkbrotha4310 2026-08-30) is the reason this rides the no-drift');
  bd.push('// contract instead of a hand-typed GSC literal.');
  bd.push(`function base_crate_org() { return ( ${BASE_CRATE.org[0]}, ${BASE_CRATE.org[1]}, 0 ); }`);
  bd.push(`function base_crate_yaw() { return ${BASE_CRATE.yaw}; }`);
  bd.push('');
  bd.push('// THE CYBERCITY SIGN (docs/208) - Nikolai\'s TOWER OF DOOM / CYBERCITY sign on the core WEST');
  bd.push('// face over the base crate, ABSOLUTE coords. The origin is the sign\'s BACK plane centre at its');
  bd.push('// bottom edge, 0.5 proud of the face; the generator (BASE_SIGN) asserts it clear and cuts its');
  bd.push('// body clip + cap. _tod_base_sign.gsc reads both.');
  bd.push(`function base_sign_org() { return ( ${-(CORE + BASE_SIGN.proud)}, ${BASE_SIGN.y}, ${BASE_SIGN.z1} ); }`);
  bd.push(`function base_sign_yaw() { return ${BASE_SIGN.yaw}; }`);
  bd.push('');
  bd.push('// THE RAMPAGE INDUCER (v18.99g) — the BO6 aether canister on its cyan');
  bd.push('// pedestal against the base arena south wall, across from Quick Revive.');
  bd.push('// _tod_rampage.gsc reads all three; the generator cuts the pedestal brush');
  bd.push('// ("base inducer plinth") from the same constants and ASSERTS the trigger');
  bd.push('// origin is outside it, because a use-trigger whose origin is inside a');
  bd.push('// solid never prompts — which is exactly how v18.99f shipped dead.');
  bd.push(`function base_inducer_org()  { return ( ${INDUCER_ORG[0]}, ${INDUCER_ORG[1]}, ${INDUCER_PLINTH_H} ); }`);
  bd.push(`function base_inducer_trig() { return ( ${INDUCER_TRIG[0]}, ${INDUCER_TRIG[1]}, 0 ); }`);
  bd.push(`function base_inducer_yaw()  { return ${INDUCER_YAW}; }`);
  bd.push(`function base_inducer_trig_r() { return ${INDUCER_TRIG_R}; }`);
  bd.push(`function base_inducer_trig_lift() { return ${INDUCER_TRIG_LIFT}; }   // docs/208: in the slot over the body clip`);
  bd.push('');
  bd.push('// THE HOOP (v19.18) — the bat target cut into the core south face above the');
  bd.push('// base upgrade station. _tod_corpse_cleanup::hoop_watch scores a flung body');
  bd.push('// whose spine enters this box; the generator cut the recess and rim from the');
  bd.push('// same numbers, so the target the player sees IS the volume the script tests.');
  bd.push('// lo.y includes the rim standoff so a body entering the mouth counts.');
  bd.push(`function base_hoop_lo() { return ( ${HOOP.x1}, ${HOOP.y1 - HOOP_RIM_OUT}, ${HOOP.z1} ); }`);
  bd.push(`function base_hoop_hi() { return ( ${HOOP.x2}, ${HOOP.y2}, ${HOOP.z2} ); }`);
  bd.push('');
  bd.push("// TELEPORTER — the pad at the field's centre, and where up-riders land");
  bd.push(`// (${TP_ARRIVE_OFF}u north of the pad, still inside the field: outside the pad's ${TP_GATHER}u gather,`);
  bd.push('// so an arrival is never swept along by the next departure — v10.4 rule)');
  bfun('tp_pad_org', BR_FURN.tp.trig);
  bfun('tp_arrival_org', [BR_FURN.tp.trig[0], BR_FURN.tp.trig[1] + TP_ARRIVE_OFF]);
  bd.push('');
  for (const line of HAVEN.dataGsc()) bd.push(line);
  bd.push('');
  // ---- THE UNDERCITY + THE WORKSHOP WINGS (docs/158) ----------------------
  bd.push('// THE UNDERCITY + THE WORKSHOP WINGS (docs/158). Every anchor below is cut');
  bd.push('// from the same tables that cut the rooms (the no-drift contract):');
  bd.push('// _tod_perk_scatter reads the Quick Revive pad, _tod_partners::stations the');
  bd.push('// bench and part anchors (the bench collision clips are generator-cut).');
  bd.push(`function undercity_z()     { return ${UC_Z}; }`);
  bd.push(`function vault_qr_org()    { return ( ${VAULT_QR[0]}, ${VAULT_QR[1]}, ${UC_Z} ); }`);
  // docs/160: the descent's Quick Revive pin (see TERRACE_QR). Pre-mirrored;
  // the front vector is world-space, so it flips with CM like the yaw does.
  bd.push(`function terrace_qr_org()  { return ( ${TERRACE_QR[0]}, ${TERRACE_QR[1]}, ${TERRACE_QR[2]} ); }`);
  bd.push(`function terrace_qr_yaw()  { return ${cyaw(269.999)}; }`);
  bd.push(`function terrace_qr_front(){ return ( 0, ${-CM}, 0 ); }`);
  bd.push(`function vault_spawn_org() { return ( ${VT_CX}, ${VT_CY - 72}, ${UC_Z} ); }`);
  bd.push('');
  bd.push('// PARTNER BENCHES — index = partner id (0 Civil Protector, 1 Talon, 2 R.A.P.S.,');
  bd.push('// 3 Cerberus); yaw = the way the bench FACES (into the room, at the door).');
  const byPartner = [...WINGS].sort((a, b) => a.partner - b.partner);
  const emitSwitch = (arg, rows, fallback) => {   // the body of a switch-return accessor (header pushed by the caller)
    bd.push('{');
    bd.push(`\tswitch ( ${arg} )`);
    bd.push('\t{');
    rows.forEach(([k, v]) => bd.push(`\tcase ${k}: return ${v};`));
    bd.push('\t}');
    bd.push(`\treturn ${fallback};`);
    bd.push('}');
  };
  const benchOrg = w => { const F = wingFrame(w); const [x, y] = F.pt(WU_BENCH, w.rc); return `( ${x}, ${y}, 0 )`; };
  const benchYaw = w => wingFrame(w).faceYaw;
  // (literal function headers on purpose — tools/partner/test_partners.js greps
  // this file for `function partner_bench_org(` to prove the generator owns it)
  bd.push('function partner_bench_org( id )');
  emitSwitch('id', byPartner.map(w => [w.partner, benchOrg(w)]), benchOrg(byPartner[0]));
  bd.push('function partner_bench_yaw( id )');
  emitSwitch('id', byPartner.map(w => [w.partner, benchYaw(w)]), benchYaw(byPartner[0]));
  bd.push('function partner_bench_room( id )');
  emitSwitch('id', byPartner.map(w => [w.partner, `"${w.dest}"`]), `"${byPartner[0].dest}"`);
  bd.push(`function partner_bench_count() { return ${byPartner.length}; }`);
  bd.push('');
  bd.push('// PARTNER PARTS — the shelf along the Conduit\'s west wall, index n = id * 2 +');
  bd.push('// part (0..7), props facing east (yaw 0) into the room, 10 above the floor.');
  bd.push('function partner_part_org( n )');
  bd.push('{');
  bd.push(`\treturn ( ${PART_SHELF_X}, ${PART_SHELF_Y0} + n * ${PART_SHELF_PITCH}, ${UC_Z + 10} );`);
  bd.push('}');
  bd.push('function partner_part_yaw( n ) { return 0; }');
  bd.push(`function partner_part_count() { return ${2 * byPartner.length}; }`);
  bd.push('');
  fs.writeFileSync(BREATHER_GSC_OUT, bd.join('\n'), 'utf8');
  console.log(`wrote ${BREATHER_GSC_OUT}  (${BRZS.length} lounges, themes ${[...BREATHER_LAPS].sort((a, b2) => a - b2).map(l => `${l}:${BREATHER_THEME[l].key}`).join(' ')})`);
}

// One original BO6 counter inside each haven dome: floors 10, 20, 30 and 40.
fs.writeFileSync(path.join(REPO,'scripts','zm','zm_tod2_cybercity','_tod_wunderfizz_data.gsc'),WUNDERFIZZ.dataGsc(WUNDERFIZZ_NODES),'utf8');
