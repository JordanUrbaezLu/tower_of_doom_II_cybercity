'use strict';
// THE BATTLE ARENA (docs/185, user 2026-09-27). ONE source for both ends of it:
//   * THE CHAMBER on floor 40 — since docs/202 v2 (THE HEART) the haven's
//     force field itself: the arena's gate stands at the field's centre and
//     every living player steps into the field (tools/haven_layout.js CHAMBER:
//     its bounding box + its radius). The chamber charges and the party is sent
//     to the arena. (Until v2 it was the old haven's pad platform, walled and
//     roofed; CHAMBER_DOOR_Z is kept for that history only.)
//   * THE ARENA — a detached room at ARENA.cx/cy, its own zone `arena_zone`,
//     reached ONLY by script teleport. A win sends the party to the top bay.
// The generator emits the geometry, the zone + risers + navmesh seeds, the
// lights/probes and GENERATED _tod_arena_data.gsc from these numbers, so the
// script and the map can never drift. Absolute world coordinates throughout.
//
// THE CRUCIBLE (docs/185 v2, 2026-10-03, user: "the battle arena needs to be
// actually designed. Should be a unique fighting area. with no real spot to camp
// and have heights to allow vertical traversal for some characters. Really should
// play into the characters for skill gap but be super hard as well so spawns need
// to be thought out and structures"). The placeholder square became a colosseum
// on three levels, every one of them reachable ON FOOT, so the horde can follow
// anyone anywhere (a perch the zombies cannot reach is exactly the camp the user
// ruled out, and the Archer's grapple refuses a landing with no navmesh under it
// for the same reason):
//   THE PIT    z 0     the open floor, four quadrants, a pylon in each, eight
//                      lit GATES in its walls (the elites' entrances)
//   THE RING   z 120   a running track round all four walls; its inner edge is an
//                      open ledge (drop into the pit anywhere); four PINWHEEL
//                      STAIRS climb to it, one per quadrant
//   THE SPOKES z 120-240  four rising bridges from the ring's mid-walls to the
//                      centre, each with a flat landing half way (a riser spot)
//   THE DAIS   z 240   the centre, high over the pit on four pillars; the party
//                      lands here and the return teleporter fires here. It
//                      OVERCHARGES during a fight (_tod_arena.gsc), so the one
//                      spot four players could hold is a spot they must leave.
//   THE UNDERCROFT     the pit floor under the dais (224 of headroom): close quarters
// THE SKILL GAP is built into the heights: the stairs are the slow way up for
// everyone; the Archer's grapple, the Breacher's Fusion launch (300-620 up) and
// a jump off any ledge are the fast ways; the Warrior's slam dives from any of
// them into the pit; every ledge is open (no rails) and the arena takes no fall
// damage (_tod_arena.gsc), so going DOWN is always free and going UP is a skill.
// No dead ends: the ring is a loop, every spoke joins two places, the dais has
// four ways on. No corners to back into: the pit's corners are the ring.
//
// THE CONDUIT INLAYS. tools/art_cohesion/conduit_layout.js places the arena's
// eight floor wire inlays on the `battle arena floor` brush's own grid (x -452,
// -196, 60, 316 / y -484, -228, 28 off the centre) and skips a grid point a
// solid covers. That brush keeps its old extent (FLOOR_OLD) and the layout below
// keeps the same eight points open and the same three (-452 column) covered, so
// the baked tod_conduit_arena model needs no re-export (conduit_layout.js
// --check stays green; the SW stair, the SW pylon and the W spoke's pier are the
// three covers).

const CHAMBER_LAP = 40;          // the haven whose field is the chamber
const CHAMBER_H = 256;           // "inside the chamber" reaches this far above the hall floor
const CHAMBER_DOOR_Z = 192;      // the doorway lintel's underside (BR_WIN_TOP, the gate lintel's band)

// The room. Floor top at z; inside half-extent `half`; walls `wall` thick and
// `height` tall. Far south-west of the tower: clear of the undercity (x >=
// -2592), the crown (x >= -3064, y >= -280) and inside the sky seal / umbra
// volumes (asserted by the generator against its own derived bounds).
const ARENA = { cx: -8000, cy: -8000, z: 0, half: 832, wall: 20, height: 560 };

// THE VENTED ROOF (2026-09-28, user: "It has no textures currently and
// everything is invisible"). A FULLY SEALED room is invisible in this
// toolchain: the linker's UmbraConvert classes a closed pocket of air as the
// INSIDE of a solid and draws nothing from a camera in it. So the room is OPEN
// to the void for the occlusion step and CLOSED to the eye: the ceiling floats
// `gap` above the wall tops and overhangs a `ch`-wide channel to a hanging
// SKIRT wall whose bottom stops at `skirtBot`. Air goes over the wall, along the
// channel and out under the skirt; a sight line from anywhere a player can stand
// rises over the wall top, so it lands on the skirt or the ceiling.
// v2: THE GAP IS A SLOT NOW (128 -> 24). The linker prints UmbraConvert's own
// settings (`smallest_occluder=72.000 small_hole=4.000`): any opening of 4 units
// or more is open air to it, while 24 is too low for any player body (standing
// 72, crouched ~50) — the Breacher's launch and the Archer's rope can reach the
// ceiling now, and a 128 gap would have let them out over the wall. No clip is
// needed (and none is used, so the vent never depends on how Umbra treats clip).
const VENT = { gap: 24, ch: 64, t: 20, skirtBot: 360 };
const OUTER = ARENA.half + ARENA.wall + VENT.ch + VENT.t;          // the ceiling / skirt half-extent (936)
const TOP = ARENA.z + ARENA.height + VENT.gap + 20;               // the ceiling's top face (604)

// ---- the levels -------------------------------------------------------------
const RING_Z = 120;              // THE RING: 10 risers of 12 above the pit
const RD = 192;                  // its depth (wall face to ledge)
const RI = ARENA.half - RD;      // 640: the ledge line (the pit is |x|,|y| < RI)
const DAIS_Z = 240;              // THE DAIS: 10 more risers
const DH = 192;                  // its half-extent (384 square)
const SLAB = 16;                 // every walkable slab (the tower's: consecutive treads overlap 4)
const RISE = 12;                 // every riser in the room (the tower's)
const SPOKE_HW = 64;             // a spoke is 128 wide
const SPOKE_TREAD = 32;          // 5 treads + a landing + 5 treads: ring -> dais
const LAND = [352, 480];         // a spoke's landing, as distance from the centre along its axis
const LAND_Z = RING_Z + 5 * RISE;   // 180
const STAIR = { u: [-480, -352], tread: 24, steps: 10, foot: 400 };   // the pinwheel stair, S-face frame
const PYLON = { at: [-440, -232], hw: 32 };                          // SW quadrant, S-face frame
const PILLAR = { at: 168, hw: 24 };                                  // the dais's four corner pillars
const PIER = { hw: 24, a: 360, b: 472 };                             // under each spoke landing
const GATE_U = [-224, 224];      // two gates per pit wall (S-face frame: x)
const MOOD_Z = 236;              // THE MOOD LIGHTS (v2.1): a light host just over each pylon's collar (196..212) ...
const MOOD_DAIS_Z = DAIS_Z + 140;   // ... and one over the dais; _tod_arena.gsc colours them by level (the dais one goes white-hot for the overcharge)
const LEDGE_MAX = DAIS_Z;        // the deepest drop off any arena edge (lint_tod_geometry.js ARENA_LEDGE_MAX)
const FLOOR_OLD = 532;           // `battle arena floor` keeps the v1 room's extent (THE CONDUIT INLAYS above)

// ---- the four-fold pinwheel ---------------------------------------------------
// Everything with a direction is written once in the S-FACE FRAME (the south pit
// wall at y = -RI, the pit at y > -RI) and turned k * 90 degrees anticlockwise:
// k=0 S face, k=1 E face, k=2 N face, k=3 W face.
function rotPt(k, x, y) {
  for (let i = 0; i < k; i++) [x, y] = [-y, x];
  return [x, y];
}
function rotRect(k, x1, x2, y1, y2) {
  const a = rotPt(k, x1, y1), b = rotPt(k, x2, y2);
  return [Math.min(a[0], b[0]), Math.max(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[1], b[1])];
}
const FACE = ['S', 'E', 'N', 'W'];

// ---- arrivals and spawn points ------------------------------------------------
// Four arrivals on the dais round the teleporter, facing out over the arena.
const ARRIVALS = [[-80, -80], [80, -80], [-80, 80], [80, 80]]
  .map(([dx, dy]) => [ARENA.cx + dx, ARENA.cy + dy, ARENA.z + DAIS_Z]);

// SPAWN POINTS, every one on a FLAT deck (a riser on a stair buries itself or
// hangs in the air): 8 gates (the elites' entrances, and ordinary risers),
// 4 open pit spots, 2 in the undercroft, 8 on the ring, 4 on the spoke landings.
// None on the dais itself: the dais is the arrival and the overcharge does its
// own pressing. _tod_arena.gsc's director scores them each spawn (docs/185 v2).
const SPAWNS = [];
for (let k = 0; k < 4; k++) {
  for (const u of GATE_U) { const [x, y] = rotPt(k, u, -RI + 64); SPAWNS.push({ kind: 'gate', x, y, z: 0, face: FACE[k] }); }
  { const [x, y] = rotPt(k, -320, -320); SPAWNS.push({ kind: 'pit', x, y, z: 0, face: FACE[k] }); }
  for (const u of [-224, 224]) { const [x, y] = rotPt(k, u, -(ARENA.half - RD / 2)); SPAWNS.push({ kind: 'ring', x, y, z: RING_Z, face: FACE[k] }); }
  { const [x, y] = rotPt(k, 0, -(LAND[0] + LAND[1]) / 2); SPAWNS.push({ kind: 'landing', x, y, z: LAND_Z, face: FACE[k] }); }
}
SPAWNS.push({ kind: 'undercroft', x: 96, y: -96, z: 0, face: '-' }, { kind: 'undercroft', x: -96, y: 96, z: 0, face: '-' });
const RISERS = SPAWNS.map(s => [ARENA.cx + s.x, ARENA.cy + s.y, ARENA.z + s.z]);
// THE MOOD LIGHT HOSTS (v2.1): the four pylon collars, then the dais LAST (_tod_arena.gsc
// mood_dais() addresses the last entry)
const MOOD = [0, 1, 2, 3].map(k => { const [x, y] = rotPt(k, PYLON.at[0], PYLON.at[1]); return [ARENA.cx + x, ARENA.cy + y, ARENA.z + MOOD_Z]; });
MOOD.push([ARENA.cx, ARENA.cy, ARENA.z + MOOD_DAIS_Z]);
const GATES = SPAWNS.filter(s => s.kind === 'gate').map(s => [ARENA.cx + s.x, ARENA.cy + s.y, ARENA.z + s.z]);

// Navmesh seeds on every surface no riser stands on (the risers seed their own;
// the stairs and spoke flights seed themselves through rampWedgeY/X).
const SEEDS = [[0, 0, 2], [0, 0, DAIS_Z + 2], [120, 120, DAIS_Z + 2], [-120, -120, DAIS_Z + 2],
  ...[[-736, -736], [736, -736], [-736, 736], [736, 736], [0, -736], [0, 736], [-736, 0], [736, 0]].map(([x, y]) => [x, y, RING_Z + 2]),
  ...[[-560, 0], [560, 0], [0, -560], [0, 560]].map(([x, y]) => [x, y, 2])]
  .map(([dx, dy, z]) => [ARENA.cx + dx, ARENA.cy + dy, ARENA.z + z]);

// One point on every surface (and every stair) the horde must be able to reach:
// lint_tod_navmesh.js requires each to stand on the arena's ONE navmesh
// component (the "no spot zombies cannot get to" proof, after cod2map).
const NAV_PROBES = [];
for (let k = 0; k < 4; k++) {
  const p = (x, y, z) => { const [a, b] = rotPt(k, x, y); NAV_PROBES.push([ARENA.cx + a, ARENA.cy + b, ARENA.z + z]); };
  p(-320, -320, 0);                                                  // the quadrant
  p(0, -(ARENA.half - RD / 2), RING_Z);                              // the ring, mid-wall
  p(-(ARENA.half - RD / 2), -(ARENA.half - RD / 2), RING_Z);          // the ring, corner
  p((STAIR.u[0] + STAIR.u[1]) / 2, -(STAIR.foot + STAIR.tread * STAIR.steps / 2), RING_Z / 2);   // the pinwheel stair, half way
  p(0, -(RI - 2.5 * SPOKE_TREAD), RING_Z + 2.5 * RISE);               // the spoke's lower flight
  p(0, -(LAND[0] + LAND[1]) / 2, LAND_Z);                            // its landing
  p(0, -(LAND[0] - 2.5 * SPOKE_TREAD), LAND_Z + 2.5 * RISE);          // its upper flight
}
NAV_PROBES.push([ARENA.cx, ARENA.cy, ARENA.z], [ARENA.cx, ARENA.cy, ARENA.z + DAIS_Z]);

const LIGHT_PIT = '1 0.42 0.28';        // red-orange pools on the pit
const LIGHT_RING = '0.55 0.85 1';       // cool light along the walls
const LIGHT_DAIS = '1 0.82 0.55';       // warm gold over the dais

// The zone: one volume over the room, the spawn points as its risers, a dog spot.
function zone(volumeBrush) {
  const A = ARENA, o = A.half + A.wall;
  // a riser within 165 of an arrival (in plan, on the same level) would rise
  // inside a landing capsule; one a level below cannot meet it
  for (const [sx, sy, sz] of ARRIVALS) for (const [rx, ry, rz] of RISERS)
    if (Math.abs(sz - rz) < 100 && Math.hypot(sx - rx, sy - ry) < 165)
      throw new Error(`battle arena arrival (${sx},${sy},${sz}) within 165 of riser (${rx},${ry},${rz})`);
  return {
    name: 'arena_zone',
    brushes: [volumeBrush(A.cx - o, A.cx + o, A.cy - o, A.cy + o, A.z - 16, A.z + A.height)],
    risers: RISERS,
    dog: [A.cx, A.cy - 300, A.z],
  };
}

// ---------------------------------------------------------------------------
// THE ROOM. E = the generator's emitters, all absolute, kit roles only:
//   E.box(label, x1,x2,y1,y2,z1,z2, role)          an axis box (walkable or not)
//   E.bevel(label, x1,x2,y1,y2,z1,z2, role, amount) a chamfered solid (never a floor)
//   E.poly(label, vertices, faces, role)           a convex solid (the spoke beams)
//   E.rampY / E.rampX(label, ..., rise, tread)      the clip slope over a flight
// Labels start `battle arena` — lint_tod_geometry's own island bucket keys on
// it. Floors wear DECK roles (the lint's walkability flood follows them);
// everything else wears BLOCK roles, so no trim can become a floor nobody can
// reach (an unreachable arena floor fails the lint's detached count).
// ---------------------------------------------------------------------------
function geometry(E) {
  const A = ARENA, h = A.half, w = A.wall, cx = A.cx, cy = A.cy, z0 = A.z;
  const B = (n, x1, x2, y1, y2, z1, z2, role) => E.box(`battle arena ${n}`, cx + x1, cx + x2, cy + y1, cy + y2, z0 + z1, z0 + z2, role);
  const V = (n, x1, x2, y1, y2, z1, z2, role, amt) => E.bevel(`battle arena ${n}`, cx + x1, cx + x2, cy + y1, cy + y2, z0 + z1, z0 + z2, role, amt);
  const RB = (k, n, x1, x2, y1, y2, z1, z2, role) => { const r = rotRect(k, x1, x2, y1, y2); B(n, r[0], r[1], r[2], r[3], z1, z2, role); };
  const RV = (k, n, x1, x2, y1, y2, z1, z2, role, amt) => { const r = rotRect(k, x1, x2, y1, y2); V(n, r[0], r[1], r[2], r[3], z1, z2, role, amt); };
  // A flight in the S-face frame rising toward -y (down the page, toward the
  // wall it climbs): treads from `start` (the downhill edge of tread 1) step by
  // `tread` toward -y. The ramp plane runs through every tread's downhill
  // nosing and feathers onto the lower floor over one tread (the tower's
  // Treyarch-measured convention, gen_tower_map.js STAIR RAMP CLIP).
  const ramp = (k, n, u1, u2, yNear, yFar, zNear, zFar, tread) => {
    // the plane's own span in the S frame: y from yFar (high end) to yNear (low end)
    const [x1, x2, y1, y2] = rotRect(k, u1, u2, yFar, yNear);
    const args = [`battle arena ${n}`];
    if (k % 2 === 0) {
      // runs along y: the S frame's y1 (= yFar) is the high end at k=0; turned 180 the ends swap
      const lo = k === 0 ? zFar : zNear, hi = k === 0 ? zNear : zFar;
      E.rampY(...args, cx + x1, cx + x2, cy + y1, cy + y2, z0 + lo, z0 + hi, RISE, tread);
    } else {
      // runs along x: k=1 turns S-frame -y into +x (the high end at x2); k=3 into -x
      const lo = k === 1 ? zNear : zFar, hi = k === 1 ? zFar : zNear;
      E.rampX(...args, cy + y1, cy + y2, cx + x1, cx + x2, z0 + lo, z0 + hi, RISE, tread);
    }
  };

  // --- the floor, the shell, the vented roof --------------------------------
  B('floor', -FLOOR_OLD, FLOOR_OLD, -FLOOR_OLD, FLOOR_OLD, -SLAB, 0, 'tower_red_floor');
  B('floor apron N', -h - w, h + w, FLOOR_OLD, h + w, -SLAB, 0, 'tower_red_floor');
  B('floor apron S', -h - w, h + w, -h - w, -FLOOR_OLD, -SLAB, 0, 'tower_red_floor');
  B('floor apron E', FLOOR_OLD, h + w, -FLOOR_OLD, FLOOR_OLD, -SLAB, 0, 'tower_red_floor');
  B('floor apron W', -h - w, -FLOOR_OLD, -FLOOR_OLD, FLOOR_OLD, -SLAB, 0, 'tower_red_floor');
  B('foundation', -h - w, h + w, -h - w, h + w, -64, -SLAB, 'graphite');
  B('wall N', -h - w, h + w, h, h + w, 0, A.height, 'graphite');
  B('wall S', -h - w, h + w, -h - w, -h, 0, A.height, 'graphite');
  B('wall W', -h - w, -h, -h, h, 0, A.height, 'graphite');
  B('wall E', h, h + w, -h, h, 0, A.height, 'graphite');
  const O = OUTER, K = h + w + VENT.ch, cz = A.height + VENT.gap;
  B('ceiling', -O, O, -O, O, cz, cz + 20, 'ceiling');
  B('skirt N', -O, O, K, O, VENT.skirtBot, cz, 'graphite');
  B('skirt S', -O, O, -O, -K, VENT.skirtBot, cz, 'graphite');
  B('skirt W', -O, -K, -K, K, VENT.skirtBot, cz, 'graphite');
  B('skirt E', K, O, -K, K, VENT.skirtBot, cz, 'graphite');

  for (let k = 0; k < 4; k++) {
    const F = FACE[k];
    // --- THE RING (one strip per wall; N/S strips own the corners) ----------
    if (k % 2 === 0) {
      RB(k, `ring ${F} body`, -h, h, -h, -RI, 0, RING_Z - SLAB, 'oxblood');
      RB(k, `ring ${F} deck`, -h, h, -h, -RI, RING_Z - SLAB, RING_Z, 'brass');
    } else {
      RB(k, `ring ${F} body`, -RI, RI, -h, -RI, 0, RING_Z - SLAB, 'oxblood');
      RB(k, `ring ${F} deck`, -RI, RI, -h, -RI, RING_Z - SLAB, RING_Z, 'brass');
    }
    // the ledge's gold band (under the deck edge, 4 proud), broken round the stair
    RB(k, `ring ${F} band a`, -RI, STAIR.u[0], -RI, -RI + 4, RING_Z - 24, RING_Z - SLAB, 'gold');
    RB(k, `ring ${F} band b`, STAIR.u[1], RI, -RI, -RI + 4, RING_Z - 24, RING_Z - SLAB, 'gold');
    // --- THE GATES: lit frames in the pit wall (the elites come in here) ----
    GATE_U.forEach((g, i) => {
      const n = `gate ${F}${i + 1}`;
      RB(k, `${n} post a`, g - 64, g - 48, -RI, -RI + 6, 0, 96, 'gold');
      RB(k, `${n} post b`, g + 48, g + 64, -RI, -RI + 6, 0, 96, 'gold');
      RB(k, `${n} lintel`, g - 64, g + 64, -RI, -RI + 6, 84, 96, 'gold');
      for (const b of [-26, 0, 26]) RB(k, `${n} bar ${b}`, g + b - 4, g + b + 4, -RI, -RI + 3, 6, 84, 'cyan');
      RB(k, `${n} mouth`, g - 48, g + 48, -RI + 6, -RI + 38, 0, 1, 'gold_line');   // walk-over (the pad-ring precedent)
    });
    // --- THE PINWHEEL STAIR: pit -> ring, against this face ------------------
    for (let s = 1; s <= STAIR.steps; s++) {
      const yNear = -STAIR.foot - STAIR.tread * (s - 1), yFar = yNear - STAIR.tread, top = RISE * s;
      RB(k, `stair ${F} tread ${s}`, STAIR.u[0], STAIR.u[1], yFar, yNear, Math.max(0, top - SLAB), top, 'brass');
      if (top - SLAB > 0) RB(k, `stair ${F} fill ${s}`, STAIR.u[0], STAIR.u[1], yFar, yNear, 0, top - SLAB, 'oxblood');
    }
    ramp(k, `stair ${F} ramp`, STAIR.u[0], STAIR.u[1], -STAIR.foot + STAIR.tread, -STAIR.foot - STAIR.tread * (STAIR.steps - 1), 0, RISE * STAIR.steps, STAIR.tread);
    // --- THE SPOKE: ring -> landing -> dais, over the pit ---------------------
    for (let s = 1; s <= 5; s++) {
      const yNear = -RI + SPOKE_TREAD * (s - 1), yFar = yNear + SPOKE_TREAD, top = RING_Z + RISE * s;
      RB(k, `spoke ${F} lower tread ${s}`, -SPOKE_HW, SPOKE_HW, yNear, yFar, top - SLAB, top, 'gold_panel');
    }
    RB(k, `spoke ${F} landing`, -SPOKE_HW, SPOKE_HW, -LAND[1], -LAND[0], LAND_Z - SLAB, LAND_Z, 'gold_panel');
    for (let s = 1; s <= 5; s++) {
      const yNear = -LAND[0] + SPOKE_TREAD * (s - 1), yFar = yNear + SPOKE_TREAD, top = LAND_Z + RISE * s;
      RB(k, `spoke ${F} upper tread ${s}`, -SPOKE_HW, SPOKE_HW, yNear, yFar, top - SLAB, top, 'gold_panel');
    }
    // the spoke flights rise toward +y in the S frame (toward the centre), the
    // reverse of the stair; written with the same helper by mirroring the ends
    spokeRamp(k, `spoke ${F} lower ramp`, -RI - SPOKE_TREAD, -RI + 4 * SPOKE_TREAD, RING_Z, RING_Z + 5 * RISE);
    spokeRamp(k, `spoke ${F} upper ramp`, -LAND[0] - SPOKE_TREAD, -LAND[0] + 4 * SPOKE_TREAD, LAND_Z, LAND_Z + 5 * RISE);
    RB(k, `spoke ${F} pier`, -PIER.hw, PIER.hw, -PIER.b, -PIER.a, 0, LAND_Z - SLAB, 'graphite');
    // THE BEAM under each flight: a sloped plate whose top runs through every
    // tread's underside corner (never above a tread, so the walk is untouched)
    // and anchors into the ring / landing / dais slab at its ends. From the pit
    // the spokes read as bridges, not as stairs hung in the air.
    beam(k, `spoke ${F} lower beam`, -RI, -LAND[1], RING_Z + RISE - SLAB);
    beam(k, `spoke ${F} upper beam`, -LAND[0], -DH, LAND_Z + RISE - SLAB);
    // --- THE PYLON: floor to wall top, a cyan collar at head height ---------
    RV(k, `pylon ${F}`, PYLON.at[0] - PYLON.hw, PYLON.at[0] + PYLON.hw, PYLON.at[1] - PYLON.hw, PYLON.at[1] + PYLON.hw, 0, A.height, 'graphite', 12);
    RB(k, `pylon ${F} collar`, PYLON.at[0] - PYLON.hw - 4, PYLON.at[0] + PYLON.hw + 4, PYLON.at[1] - PYLON.hw - 4, PYLON.at[1] + PYLON.hw + 4, 196, 212, 'cyan');
    // --- the walls above the ring: pilasters, a cyan seam, a gold cornice ----
    for (const u of [-512, -256, 0, 256, 512]) RB(k, `wall ${F} pilaster ${u}`, u - 16, u + 16, -h, -h + 8, RING_Z, A.height - 24, 'bronze_wall');
    RB(k, `wall ${F} seam`, -h, h, -h, -h + 6, 300, 306, 'cyan');
    RB(k, `wall ${F} cornice`, -h, h, -h, -h + 12, A.height - 24, A.height, 'gold');
    // --- the corner column (flush in the corner: nothing to stand behind) ---
    RV(k, `corner ${F}`, -h, -h + 64, -h, -h + 64, RING_Z, A.height, 'gold', 10);
    // --- the dais pillar (under its corner) and the under-glow --------------
    RV(k, `dais pillar ${F}`, -PILLAR.at - PILLAR.hw, -PILLAR.at + PILLAR.hw, -PILLAR.at - PILLAR.hw, -PILLAR.at + PILLAR.hw, 0, DAIS_Z - SLAB, 'gold', 8);
    RB(k, `dais underglow ${F}`, -DH + 8, DH - 8, -DH, -DH + 8, DAIS_Z - SLAB - 12, DAIS_Z - SLAB, 'cyan');
  }
  // a flight's beam (S frame, the flight climbs toward +y from yLow): top = the
  // treads' underside line (zLow at yLow, +RISE per SPOKE_TREAD), 12 thick
  function beam(k, n, yLow, yHigh, zLow) {
    const zHigh = zLow + (yHigh - yLow) * RISE / SPOKE_TREAD, t = 12;
    const pts = [[-SPOKE_HW, yLow, zLow - t], [SPOKE_HW, yLow, zLow - t], [SPOKE_HW, yHigh, zHigh - t], [-SPOKE_HW, yHigh, zHigh - t],
      [-SPOKE_HW, yLow, zLow], [SPOKE_HW, yLow, zLow], [SPOKE_HW, yHigh, zHigh], [-SPOKE_HW, yHigh, zHigh]]
      .map(([x, y, z]) => { const [a, b] = rotPt(k, x, y); return [cx + a, cy + b, z0 + z]; });
    E.poly(`battle arena ${n}`, pts, [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [3, 2, 6, 7], [0, 3, 7, 4], [1, 2, 6, 5]], 'bronze_wall');
  }
  // the S-frame spoke flights climb toward +y: tread 1's downhill edge is at
  // y = start, the plane passes z0 + RISE*s at y = start + TREAD*(s-1)
  function spokeRamp(k, n, yLow, yHigh, zLow, zHigh) {
    const [x1, x2, y1, y2] = rotRect(k, -SPOKE_HW, SPOKE_HW, yLow, yHigh);
    const label = `battle arena ${n}`;
    if (k === 0) E.rampY(label, cx + x1, cx + x2, cy + y1, cy + y2, z0 + zLow, z0 + zHigh, RISE, SPOKE_TREAD);
    else if (k === 2) E.rampY(label, cx + x1, cx + x2, cy + y1, cy + y2, z0 + zHigh, z0 + zLow, RISE, SPOKE_TREAD);
    else if (k === 1) E.rampX(label, cy + y1, cy + y2, cx + x1, cx + x2, z0 + zHigh, z0 + zLow, RISE, SPOKE_TREAD);
    else E.rampX(label, cy + y1, cy + y2, cx + x1, cx + x2, z0 + zLow, z0 + zHigh, RISE, SPOKE_TREAD);
  }
  // --- THE DAIS --------------------------------------------------------------
  B('dais', -DH, DH, -DH, DH, DAIS_Z - SLAB, DAIS_Z, 'gold_deck');
  for (let k = 0; k < 4; k++) RB(k, `dais ring ${FACE[k]}`, -128, 112, -128, -112, DAIS_Z, DAIS_Z + 1, 'ruby');   // walk-over ring round the teleporter
}

function lights(light, probe) {
  const A = ARENA, L = (n, x, y, z, c, r) => light(`battle arena light ${n}`, A.cx + x, A.cy + y, A.z + z, c, r, 6, 1);
  L('dais', 0, 0, 470, LIGHT_DAIS, 560);
  L('undercroft', 0, 0, 150, LIGHT_PIT, 380);
  for (let k = 0; k < 4; k++) {
    const F = FACE[k], p = (x, y) => rotPt(k, x, y);
    L(`pit ${F}`, ...p(-380, -380), 300, LIGHT_PIT, 520);
    L(`ring ${F}`, ...p(0, -(A.half - 96)), 380, LIGHT_RING, 600);
    L(`corner ${F}`, ...p(-(A.half - 128), -(A.half - 128)), 300, LIGHT_PIT, 420);
  }
  probe('probe battle arena', A.cx, A.cy, A.z + 120);
  probe('probe battle arena dais', A.cx, A.cy, A.z + DAIS_Z + 90);
}

// ---------------------------------------------------------------------------
// THE LAYOUT PROVES ITSELF (run at require time by the generator, the parity
// lint and the arena gate): every spawn point on a flat deck at its height and
// clear of every solid; headroom under every walkway; the pinwheel clear of the
// pylons, spokes, gates and dais; nothing outside the room.
// ---------------------------------------------------------------------------
function decks() {
  // [x1,x2,y1,y2,topZ], relative to the room's centre
  const out = [[-ARENA.half, ARENA.half, -ARENA.half, ARENA.half, 0]];   // the pit (minus solids, below)
  for (let k = 0; k < 4; k++) {
    const r = k % 2 === 0 ? rotRect(k, -ARENA.half, ARENA.half, -ARENA.half, -RI) : rotRect(k, -RI, RI, -ARENA.half, -RI);
    out.push([...r, RING_Z]);
    out.push([...rotRect(k, -SPOKE_HW, SPOKE_HW, -LAND[1], -LAND[0]), LAND_Z]);
  }
  out.push([-DH, DH, -DH, DH, DAIS_Z]);
  return out;
}
function solids() {
  // the things a spawn point must not stand in (centre coordinates, [x1,x2,y1,y2,z1,z2])
  const out = [];
  for (let k = 0; k < 4; k++) {
    out.push([...rotRect(k, STAIR.u[0], STAIR.u[1], -STAIR.foot - STAIR.tread * STAIR.steps, -STAIR.foot), 0, RING_Z]);
    out.push([...rotRect(k, PYLON.at[0] - PYLON.hw, PYLON.at[0] + PYLON.hw, PYLON.at[1] - PYLON.hw, PYLON.at[1] + PYLON.hw), 0, ARENA.height]);
    out.push([...rotRect(k, -PIER.hw, PIER.hw, -PIER.b, -PIER.a), 0, LAND_Z - SLAB]);
    out.push([...rotRect(k, -PILLAR.at - PILLAR.hw, -PILLAR.at + PILLAR.hw, -PILLAR.at - PILLAR.hw, -PILLAR.at + PILLAR.hw), 0, DAIS_Z]);
    out.push([...rotRect(k, -SPOKE_HW, SPOKE_HW, -RI, -LAND[1]), RING_Z - 4, LAND_Z]);       // the spoke's lower flight (over the pit)
    out.push([...rotRect(k, -SPOKE_HW, SPOKE_HW, -LAND[0], -DH), LAND_Z - 4, DAIS_Z]);        // its upper flight
    out.push([...rotRect(k, -ARENA.half, -ARENA.half + 64, -ARENA.half, -ARENA.half + 64), RING_Z, ARENA.height]);   // corner column
    for (const g of GATE_U) out.push([...rotRect(k, g - 64, g + 64, -RI, -RI + 6), 0, 96]);
  }
  out.push([-DH, DH, -DH, DH, DAIS_Z - SLAB, DAIS_Z]);
  return out;
}
(function selfCheck() {
  const D = decks(), S = solids();
  const inside = (p, r, m = 0) => p[0] > r[0] + m && p[0] < r[1] - m && p[1] > r[2] + m && p[1] < r[3] - m;
  for (const s of SPAWNS) {
    const p = [s.x, s.y];
    // on a deck at its own height, at least 24 in from that deck's edge (a capsule fits)
    if (!D.some(d => d[4] === s.z && inside(p, d, 24))) throw new Error(`battle arena spawn ${s.kind} (${s.x},${s.y},${s.z}) is not on a flat deck`);
    // the pit spots: the pit is |x|,|y| < RI and not under a spoke's low end
    if (s.z === 0 && !(Math.abs(s.x) < RI - 24 && Math.abs(s.y) < RI - 24)) throw new Error(`battle arena spawn ${s.kind} (${s.x},${s.y}) is under the ring`);
    // 32 clear of every solid that reaches its standing height + 72
    for (const b of S) if (b[4] < s.z + 72 && b[5] > s.z + 2 && p[0] > b[0] - 32 && p[0] < b[1] + 32 && p[1] > b[2] - 32 && p[1] < b[3] + 32)
      throw new Error(`battle arena spawn ${s.kind} (${s.x},${s.y},${s.z}) is inside or against a solid [${b.join(',')}]`);
  }
  // headroom (the navmesh agent is 72 tall): under a spoke's lowest tread, under the dais
  if (RING_Z + RISE - SLAB < 96) throw new Error('battle arena: under-spoke headroom below 96');
  if (DAIS_Z - SLAB < 200) throw new Error('battle arena: undercroft headroom below 200');
  // the spoke lands exactly on the dais and the ring
  if (-LAND[0] + 5 * SPOKE_TREAD !== -DH) throw new Error('battle arena: the upper spoke flight does not meet the dais edge');
  if (-RI + 5 * SPOKE_TREAD !== -LAND[1]) throw new Error('battle arena: the lower spoke flight does not meet its landing');
  if (STAIR.foot + STAIR.tread * STAIR.steps !== RI) throw new Error('battle arena: the pinwheel stair does not meet the ring edge');
  if (RISE * STAIR.steps !== RING_Z || RING_Z + 10 * RISE !== DAIS_Z) throw new Error('battle arena: riser count drifted from the level heights');
  // the pinwheel stair clear of the gates, the spoke, the pylon (S frame)
  for (const g of GATE_U) if (STAIR.u[1] > g - 64 - 32 && STAIR.u[0] < g + 64 + 32) throw new Error('battle arena: a pinwheel stair crowds a gate');
  if (STAIR.u[1] > -SPOKE_HW - 96) throw new Error('battle arena: a pinwheel stair crowds the spoke');
  // the vent can never let a body out (Umbra's small_hole is 4; a crouched body ~50)
  if (VENT.gap < 4 || VENT.gap >= 32) throw new Error('battle arena: the roof slot must be >= 4 (open air to Umbra) and < 32 (closed to a body)');
  if (VENT.skirtBot >= ARENA.height) throw new Error('battle arena: the skirt must hang below the wall top (the eye must not see out)');
  if (DAIS_Z + 72 >= ARENA.height) throw new Error('battle arena: the highest eye must stay below the wall top');
  if (ARRIVALS.some(([x, y, z]) => z !== ARENA.z + DAIS_Z || Math.abs(x - ARENA.cx) > DH - 40 || Math.abs(y - ARENA.cy) > DH - 40)) throw new Error('battle arena: an arrival is off the dais');
})();

// GENERATED _tod_arena_data.gsc. `chamber` = { org:[x,y,z], r, x1,x2,y1,y2 } the
// floor-40 field (absolute, even frame; r = its radius, 0 = the box alone); `ret`
// = { org:[x,y,z], yaw } the top bay's arrival.
function dataGsc(chamber, ret) {
  const v = (p) => `( ${p[0]}, ${p[1]}, ${p[2]} )`;
  const A = ARENA;
  const s = [];
  const arr = (name, rows, fmt, note) => {
    if (note) s.push(note);
    s.push(`function ${name}()`);
    s.push('{');
    s.push('\ta = [];');
    rows.forEach((p, i) => s.push(`\ta[ ${i} ] = ${fmt(p)};`));
    s.push('\treturn a;');
    s.push('}');
  };
  s.push('// GENERATED by tools/gen_tower_map.js (tools/battle_arena_layout.js) — DO NOT HAND-EDIT (regen instead).');
  s.push('// THE BATTLE ARENA (docs/185): the floor-40 chamber, the arena room (THE CRUCIBLE,');
  s.push('// v2) and the top-bay return, from the same numbers that cut the brushes.');
  s.push('');
  s.push('#namespace tod_arena_data;');
  s.push('');
  s.push(`function chamber_lap()   { return ${CHAMBER_LAP}; }`);
  s.push(`function chamber_org()   { return ${v(chamber.org)}; }`);
  s.push('// the chamber floor rect (players "inside" = within it, near its deck height) and,');
  s.push('// when chamber_r() > 0, within that radius of chamber_org() too (the haven field)');
  s.push(`function chamber_min()   { return ( ${chamber.x1}, ${chamber.y1}, ${chamber.org[2]} ); }`);
  s.push(`function chamber_max()   { return ( ${chamber.x2}, ${chamber.y2}, ${chamber.org[2] + CHAMBER_H} ); }`);
  s.push(`function chamber_yaw()   { return ${chamber.yaw}; }`);
  s.push(`function chamber_r()     { return ${chamber.r || 0}; }`);
  s.push(`function arena_center()  { return ( ${A.cx}, ${A.cy}, ${A.z} ); }`);
  s.push(`function arena_half()    { return ${A.half}; }`);
  s.push(`function arena_top()     { return ${A.z + A.height}; }   // the wall tops: nothing walkable reaches them`);
  s.push('// THE DAIS: the arrival, the return teleporter and the overcharge');
  s.push(`function arena_dais()    { return ( ${A.cx}, ${A.cy}, ${A.z + DAIS_Z} ); }`);
  s.push(`function arena_dais_half() { return ${DH}; }`);
  s.push(`function arena_ring_z()  { return ${A.z + RING_Z}; }`);
  s.push('function arena_zone()    { return "arena_zone"; }');
  arr('arena_arrivals', ARRIVALS, v);
  arr('arena_spawns', RISERS, v, '// enemy spawn points (the arena_zone risers): every one on a flat deck');
  arr('arena_spawn_kinds', SPAWNS, (p) => `"${p.kind}"`, '// per spawn point: gate / pit / undercroft / ring / landing (the director\'s weights)');
  arr('arena_gates', GATES, v, '// the eight lit gates in the pit walls: the elites\' entrances');
  s.push('// PUBLIC: is this world position inside the arena room (walls, vented roof and');
  s.push('// all)? The room stands at z ' + A.z + ', which the altitude-based systems');
  s.push('// would read as "floor 1" - the class-tier floor tracker (_tod_gauge) and the');
  s.push('// music bands (_tod_atmosphere) skip a player for whom this is true.');
  s.push('function in_arena( org )');
  s.push('{');
  s.push('\tif ( !isdefined( org ) )');
  s.push('\t\treturn false;');
  s.push(`\treturn ( Abs( org[ 0 ] - ( ${A.cx} ) ) <= ${OUTER} && Abs( org[ 1 ] - ( ${A.cy} ) ) <= ${OUTER} && org[ 2 ] >= ${A.z - 128} && org[ 2 ] <= ${TOP} );`);
  s.push('}');
  s.push('// PUBLIC: is this position standing on the dais (the overcharge\'s reach)?');
  s.push('function on_dais( org )');
  s.push('{');
  s.push('\tif ( !isdefined( org ) )');
  s.push('\t\treturn false;');
  s.push(`\treturn ( Abs( org[ 0 ] - ( ${A.cx} ) ) <= ${DH + 16} && Abs( org[ 1 ] - ( ${A.cy} ) ) <= ${DH + 16} && org[ 2 ] >= ${A.z + DAIS_Z - 8} && org[ 2 ] <= ${A.z + DAIS_Z + 96} );`);
  s.push('}');
  arr('arena_nav_probes', NAV_PROBES, v, '// one point on every surface the horde must reach (read by tools/lint_tod_navmesh.js only)');
  arr('arena_mood_orgs', MOOD, v, '// THE MOOD LIGHTS (v2.1): a glow host over each pylon collar, the dais LAST');
  s.push(`function return_org()    { return ${v(ret.org)}; }`);
  s.push(`function return_yaw()    { return ${ret.yaw}; }`);
  s.push('function return_zone()   { return "roof_zone"; }');
  s.push('');
  return s.join('\n');
}

module.exports = {
  CHAMBER_LAP, CHAMBER_H, CHAMBER_DOOR_Z, ARENA, VENT, OUTER, TOP, RING_Z, DAIS_Z, DH, RI, LEDGE_MAX, FLOOR_OLD,
  ARRIVALS, RISERS, SPAWNS, GATES, SEEDS, NAV_PROBES, MOOD, zone, geometry, lights, dataGsc, rotPt, rotRect,
};
