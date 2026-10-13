'use strict';
// =============================================================================
// THE HAVENS (docs/202) — the safe zones on floors 10 / 20 / 30 / 40.
//
// User 2026-10-02: "Our safe zones on this map need to act more like a safe zone
// ... a dome or a force field that animates when you walk in and walk out ...
// 33% slower and 33% less damage." The same evening: "make sure the teleporter
// for that floor is actually in the center of the safe zone. And maybe the safe
// zone can actually be inside the tower like how the endless tower has trials
// inside." 2026-10-03 (v3): the dome is EVIL until its guardians are dead.
//
// v4 THE WHOLE HALL (user 2026-10-03: "Safe zone should be the entire area. All
// things should be encompassed by it. So the radius should bigger and also the
// elites are not allowed to leave the dome ... bullets cannot go in or outside
// the dome. Until its a safe zone ... all perks and ammo crates pap etc should be
// inside of the dome. Going inside will make your screen dark"):
//
//                 N loggia (under the next lap's N flight)       N
//          +--------------------------------------------+       |
//          | post   .  perk   arrival   perk    .   post |   W --+-- E
//          |    .                                   .    | E loggia
//          |  .   crate   ( (o) teleporter )  altar  .   |  (under the next
//   PORCH >  .                                       .   |   lap's E flight)
//          |    .            PaP                  .  post|
//          +--- S wall (the S flight runs outside it) --+
//
//  * THE FIELD is as big as the hall: a low dome centred on the hall (C), its
//    floor ring touching the four sides (it hides into the S / W walls and the
//    E / N rails), its crown low enough to pass under the galleries (the next
//    lap's E and N flights) with room to spare. Only the four corners stay
//    outside: the porch (the way in) and three corners under the stairs, where
//    the horde rises and the field's emitter posts stand.
//  * THE TELEPORTER stays at the field's exact centre (floor 40: the Battle
//    Arena gate; the chamber IS the field).
//  * THE MACHINES ring the teleporter INSIDE the field, backs to it, fronts to
//    the dome: Pack-a-Punch (S), the upgrade altar (E), the ammo crate (W), the
//    two perk pads (NE, NW, either side of the up-riders' landing). The pad's
//    110 trigger and the v10.4 rim rule (two triggers' rims a stride apart) put
//    every vendor trigger 222+ from the centre, and the dome is only tall enough
//    for a machine's body ~270 from it, so a machine facing the pad would stand
//    with its trigger on the pad: they face out (this is the geometry).
//  * THE BARRIER: a shell of brushes on the dome's sphere (barrierBrushes(), one
//    script_brushmodel per haven, material tod_haven_barrier = the stock weapon
//    clip + missile clip): bullets, arrows and grenades stop at it, bodies walk
//    through. _tod_haven.gsc makes it solid while the haven is corrupted and
//    lets it go at the cleanse.
//  * THE WALLS: the core's S and W faces stay as thin walls in the old colours
//    (the generator cuts them with the core bands), so the S and W flights read
//    exactly as before.
//  * THE PORCH: the spire hall's stepped FAN. The W flight's top five treads
//    (12..16) open east into the hall through an archway in the W wall; every
//    adjacency in the fan is one 12-high step, so the flood walks it. Under the
//    fan the generator cuts the core down to PORCH_LOW so every row's lowest
//    cell sits exactly one step above its tread.
//
// FRAME: every haven sits on an EVEN lap (asserted by the generator), so this
// file authors ABSOLUTE even-frame coordinates. z values are relative to the
// floor's mid-landing slab top `m` (the hall floor) unless named otherwise.
//
// COLLISION / LINT RULES this file keeps (each one load-bearing):
//  * Every walkable surface is an AXIS BOX in a DECK role <= 64 tall (the lint's
//    MAX_SLAB); everything above the floor is a BLOCK role (crown_materials.json).
//  * Every walkable edge has an axis guard: a visible 39-tall rail and a CLIP
//    from the floor to floor+168 along the whole edge (the tower convention).
//  * Inlays on the floor are <= 1 tall (the transit gate's pad / arrival tests
//    read anything over 2 as a blocker).
//  * The crate clip label ends "ammo crate body" (the lint's MODEL_CLIP_COLUMNS).
//  * The barrier is an ENTITY (a script_brushmodel): the navmesh skips it (the
//    classname is on navmesh.json's exclusions) and the geometry lint never
//    reads it (worldspawn only); its material is nonsolid to bodies.
// =============================================================================

// --- the tower frame (mirrored from gen_tower_map.js; asserted there) ---------
const CORE = 256, PX = 416, PARA = 20;
const RAIL_VIS_H = 39;         // the tower's visible rail height (RAIL_VIEW_SCALE 0.7 x 56)
const RAIL_CLIP_TOP = 168;     // every rail's clip tops out at floor + PARA_H + RAIL_CAP_H
const SLAB = 16;
const STEPS = 16, TREAD = 32, RISE = 12, PARA_EVERY = 2;   // PARA_EVERY: the tower's parapet rhythm (a rail box per 2 treads)
const FLIGHT_RISE = STEPS * RISE;          // 192
const LAP_RISE = 2 * FLIGHT_RISE;          // 384

// --- THE HALL -----------------------------------------------------------------
const VOID_H = LAP_RISE + FLIGHT_RISE;     // 576: the core resumes at the next lap's NW landing
const WALL_T = 20;                          // the S / W walls, inside the core line
const WALL_IN = -CORE + WALL_T;             // -236: the walls' inner faces
const OUT = PX + PARA;                      // 436: the parapet line
const LINER_T = 4, LINER_H = FLIGHT_RISE;   // the district's wall panel over the walls' inner faces, up to the arch line
// the porch archway in the W wall; its top is the lap band seam (the generator asserts it)
const ARCH = { y1: WALL_IN, y2: -96, top: FLIGHT_RISE };
// THE PORCH: rows k = 1..4 beside treads 16-k (each 12 * k below the hall), three
// 32-wide columns east of the core line; a cell sits 12 below its east neighbour
// until it meets the hall.
const PORCH_ROWS = 4, PORCH_COLS = 3;
const PORCH = { x1: -CORE, x2: -CORE + TREAD * PORCH_COLS, y1: -CORE + TREAD, y2: -CORE + TREAD * (PORCH_ROWS + 1) };   // x[-256,-160] y[-224,-96]
const PORCH_LOW = -RISE * PORCH_ROWS - SLAB;   // -64: the core is cut down to here under the fan
const S_STRIP = { y1: WALL_IN, y2: PORCH.y1 };   // y[-236,-224]: tread 16's level, along the S wall
// the fan's north wall stops 10 short of the fan's east edge (v2's field ring passed
// that corner; kept: the floor between is the hall's)
const PORCH_WALL_X2 = PORCH.x2 - 10;            // -170
const PORCH_WALL_REST = 24;                     // v4: how much of the wall's east end the field's rim may come down onto

// --- THE FIELD (v4: the whole hall) ------------------------------------------
// The hall's walkable square is x / y in [WALL_IN, PX] = [-236, 416]: its centre is C.
const C = [92, 92];            // the field's centre = the teleporter
const DOME_R = 332;            // the field's floor ring (horizontal): 4 past the S / W liners and the E / N rails' faces
const DOME_TOP = 272;          // its crown above the floor: under the galleries' handrails with room (asserted)
// THE SPHERE through the floor ring and the crown: its centre sits DOME_C BELOW the floor
const DOME_S = (DOME_R * DOME_R + DOME_TOP * DOME_TOP) / (2 * DOME_TOP);   // 338.618
const DOME_C = DOME_TOP - DOME_S;                                           // -66.618 (negative: under the floor)
// MEMBERSHIP is three-dimensional (v4): a body is INSIDE once the point BODY_UP above
// its origin (the chest) is within IN_R3 of the sphere's centre, and stays inside
// until it is beyond OUT_R3, so standing on the ring never flickers the screen; a z
// band keeps the sphere's lower half (under the floor) off the laps below.
const BODY_UP = 36;
const IN_PAD = 12, OUT_PAD = 6;
const IN_R3 = DOME_S - IN_PAD, OUT_R3 = DOME_S + OUT_PAD;
const Z_BELOW = 48, Z_ABOVE = DOME_TOP + 40;   // a body counts from floor-48 (the porch's lowest cell) to floor+312
// the field's surface height above the floor at a horizontal distance r from C (-1 past the ring)
const domeZ = (r) => (r > DOME_R ? -1 : DOME_C + Math.sqrt(DOME_S * DOME_S - r * r));
// the horizontal radius of the field's surface at height z above the floor
const domeRAt = (z) => Math.sqrt(Math.max(0, DOME_S * DOME_S - (z - DOME_C) * (z - DOME_C)));
// is a body (origin p = [x, y, z above the floor]) inside, with the in / out radius?
const insideBody = (p, r3) => Math.hypot(p[0] - C[0], p[1] - C[1], (p[2] || 0) + BODY_UP - DOME_C) <= r3;
const RING_W = 8, RING_SEG = 48;            // the base emitter ring (a 1-unit inlay; segments off the floor are dropped)
const PAD_RING = [100, 108];                // the teleporter's own inlay ring (its 110 trigger)
const PROJ_RING = [96, 112];                // the projector ring on the ceiling (inside every gallery rail)
// the galleries' sloped handrail: its top GAL_TOP over the stair's nosing line (30..42
// over each tread), its underside GAL_BELOW under it (below the tread slabs), a cap line
const GAL_TOP = 42, GAL_BELOW = 28, GAL_CAP = 4;
const CEIL_CLEAR = 24;                      // the dome stays this far under every gallery / flight above it

// --- THE BARRIER (v4: "bullets cannot go in or outside the dome until it's a safe zone") ---
// A shell of convex brushes ON the field's sphere: LON segments round, LAT bands from
// BASE (under the floor slab, so nothing slips under the dome over the porch's low
// cells) to the crown, each band THICK units deep. Every brush is the frustum between
// a facet of the sphere and its homothetic image about the sphere's centre (so every
// face is planar and the solid convex), wearing tod_haven_barrier (make_dome.py: the
// stock weapon clip + missile clip + no penetration): it stops bullets, arrows and
// grenades and lets every body through.
const BARRIER = { base: -40, lon: 24, lat: 6, thick: 8, mat: 'tod_haven_barrier' };

// --- v6 THE WAY THROUGH (user 2026-10-04, after the first real playthrough: "the stairs should
// go down on the opposite side then you come from. So you have to at least cross the dome to
// continue going down") ---------------------------------------------------------------------
// You come in by the PORCH (the hall's south-west, off the W flight's top treads), and the way
// on is the SUNKEN STAIR: a stairwell cut into the hall floor along the north side of the core.
// Its MOUTH is at the north-centre (x TRENCH.mouth, between the teleporter and the up-riders'
// landing, so you cross the field to reach it); it runs WEST under the floor, ten stock-pitch
// steps (16 up, 24 deep: a 34-degree flight, a stock BO3 stair's pitch), and its FOOT tunnels
// under the W wall onto the W flight's lowest treads, a few steps above the floor's door. COLLAPSE
// DEBRIS fills the W flight on tread 11, just below the porch, so the old way down past the hall
// is gone. Both ways stay WALKABLE (no drop): a player who walks down to a sealed door can always
// walk back up into the hall. The stairwell is railed both sides (the tower's 39 rail + a clip to
// 168), and only its mouth is open.
const TRENCH = {
  mouth: 0,                    // x of the top step's east edge (the hall floor runs on east of it)
  foot: -CORE,                 // its last step runs on through the W wall's base to the W flight
  y1: 180, y2: 236,            // its width (56); rails 20 either side: y [160,180] and [236,256]
  steps: 10, rise: 16, tread: 24,
};
TRENCH.floor = -TRENCH.steps * TRENCH.rise;                  // -160: the foot, under the W wall
TRENCH.low = TRENCH.floor - SLAB;                            // -176: the core is cut down to here under it
TRENCH.railS = [TRENCH.y1 - PARA, TRENCH.y1];                // [160, 180]
TRENCH.railN = [TRENCH.y2, TRENCH.y2 + PARA];                // [236, 256]
TRENCH.x1 = WALL_IN;                                         // the stairwell inside the hall (x from the W wall's inner face)
// the step k (1..steps): x [mouth - tread k, mouth - tread (k-1)], top -rise k; the last one runs to the foot
const trenchStep = (k) => ({ x1: (k === TRENCH.steps ? TRENCH.foot : TRENCH.mouth - TRENCH.tread * k), x2: TRENCH.mouth - TRENCH.tread * (k - 1), top: -TRENCH.rise * k });
// THE DEBRIS: tread 11 of the W flight (the tread just below the porch's last row), x the flight's
// width, a rubble block + a cap, and a clip column over it (nothing above it to bound: the next W
// flight is 576 up) so nobody hops it.
const W_TREAD = (i) => ({ y1: CORE - TREAD * i, y2: CORE - TREAD * (i - 1), top: -FLIGHT_RISE + RISE * i });   // the lap's own W flight, relative to the hall floor
const DEBRIS = { tread: 11, top: 36, cap: 60, clipTop: 300 };
// THE ENCLOSURE's loggia walls (v6, see geometry()): every piece runs from the slab's underside
// to the bottom of what stands over it on the next lap - its E flight's parapets (one per
// PARA_EVERY treads, the first notched for its door's gate post when there is one), its NE landing's
// parapets, its E flight's first tread and its N flight's last. z relative to the hall floor.
function enclose(postAbove) {
  const out = [], seg = TREAD * PARA_EVERY, pz = (base, j) => base + RISE * PARA_EVERY * j - RISE * (PARA_EVERY - 1);
  const DOOR_NOTCH = 10;   // gen_tower_map.js DOOR_POST_NOTCH (asserted there): the gate post is the first 10 units
  // EAST: x [PX, OUT], under the next lap's E flight (base = FLIGHT_RISE over the hall floor)
  for (let j = 1; j <= STEPS / PARA_EVERY; j++) {
    const y1 = -CORE + seg * (j - 1), y2 = -CORE + seg * j, top = pz(FLIGHT_RISE, j);
    if (j === 1 && postAbove) {
      out.push({ n: 'wall east 1 post', x1: PX, x2: OUT, y1, y2: y1 + DOOR_NOTCH, top: FLIGHT_RISE });   // up to the gate post's foot
      out.push({ n: 'wall east 1', x1: PX, x2: OUT, y1: y1 + DOOR_NOTCH, y2, top });
    } else out.push({ n: `wall east ${j}`, x1: PX, x2: OUT, y1, y2, top });
  }
  out.push({ n: 'wall east corner', x1: PX, x2: OUT, y1: CORE, y2: OUT, top: LAP_RISE });             // under the NE landing's east parapet
  // NORTH: y [PX, OUT], under the NE landing's north parapet, then the N flight (base = LAP_RISE)
  out.push({ n: 'wall north corner', x1: CORE, x2: PX, y1: PX, y2: OUT, top: LAP_RISE });
  for (let j = 1; j <= STEPS / PARA_EVERY; j++)
    out.push({ n: `wall north ${j}`, x1: CORE - seg * j, x2: CORE - seg * (j - 1), y1: PX, y2: OUT, top: pz(LAP_RISE, j) });
  // SOUTH: the loggia's south edge, under the E flight's first tread (its slab's underside)
  out.push({ n: 'wall south', x1: CORE, x2: PX, y1: -CORE, y2: WALL_IN, top: FLIGHT_RISE + RISE - SLAB });
  // WEST: the loggia's west end, under the N flight's last tread
  out.push({ n: 'wall west', x1: -CORE, x2: WALL_IN, y1: CORE, y2: PX, top: LAP_RISE + RISE * STEPS - SLAB });
  return out;
}
const ENCLOSE = enclose(true);   // the shape the checks read (every haven floor's lap above carries a door: gen_tower_map.js asserts it)

// --- the spur numbers the generator still speaks (its odd-frame convention) -----
// Odd frame = the even frame point-mirrored. The pad (the teleporter, the arena
// gate) is the field's centre; the transit routes and the pad markers read these.
const SPUR_CX = -C[0], SPUR_PAD_Y = -C[1];

// --- THE MACHINES (EVEN-frame absolutes), INSIDE the field, FACING IN (v6) ------
// The local geometry of each machine (back depth behind its origin, front depth in
// front of it, the trigger offset in front, the half-width across its face, the
// height) is MEASURED:
//   pap      p9_fxanim_zm_gp_pap_xmodel_off (three zm_collision_perks1 at +-32); its buy
//            trigger is zm_cwpap's unitrigger BOX, 40 x 40 (half-diagonal 28.3): r 32
//   station  tod_heavenly_altar, decoded LOD6: x +-50.9, y -27.9..19.0, z 0..130.9; its
//            trigger is _tod_upgrades::station_place's trigger_radius_use, r 64
//   crate    tod_ammo_chest = Nikolai's Ammo Box V6 (docs/208; crateBox: x[-37,33] y[-49,49] at yaw 270, 29.4 tall)
//   perk     the BO7/BO6 ports at the pads (~ +-32 x +-30, ~110 tall)
// Each sits at `ang` degrees round C (0 = +x), its ORIGIN `rad` from C (moved by `shift`
// if given), and FACES THE TELEPORTER (v6, user 2026-10-04 after the first real playthrough:
// "perks and machines dont face the safe zone inwards. They face it outwards which is just
// wrong"): `face` = ang + 180. v4/v5 faced them out because the pad's 110 trigger and the
// 64-unit stride rule left no room for a trigger between a machine and the pad; v6 keeps the
// stride between MACHINES and uses PAD_TRIG_GAP between a machine and the PAD - a buyer at a
// machine stands with their back to the pad, and 32 is a whole player's width, so no standing
// spot is ever inside both triggers. `trig` is each machine's own trigger offset in front of
// its origin (the PaP's 40-unit box 4 in front of its face, the altar's sphere 8 in front).
const VEND_POLAR = {
  pap:     { ang: 285, rad: 226, back: 48, front: 24, half: 52, trig: 48, r: 32, h: 112 },
  station: { ang: 0,   rad: 243, back: 19, front: 28, half: 51, trig: 36, r: 64, h: 131 },
  crate:   { ang: 180, rad: 276, back: 37, front: 33, half: 49, trig: 56, r: 72, h: 30 },   // due west of the pad: the crate must face a cardinal (crateBox), so it sits on the pad's own row
  wunderfizz: { ang: 240, rad: 260, back: 1.372424, front: 51.240486, half: 27.69132, trig: 83.240486, r: 32, h: 101.473 },
};
for (const v of Object.values(VEND_POLAR)) v.face = (v.ang + 180) % 360;
const MIN_TRIG_GAP = 64;       // the v10.4 rule: rims clear by a stride, not merely miss (machine to machine)
const PAD_TRIG_GAP = 32;       // v6: a machine's trigger rim to the teleporter's (see above)
const TP_TRIG_R = 110;         // _tod_teleport TOD_TP_TRIG_RADIUS (the pad)
const TP_ARRIVE = 208;         // tower_transit_layout FLOOR_ARRIVE_OFF: up-riders land this far +y of the pad
const ARRIVAL = [C[0], C[1] + TP_ARRIVE];
const ARRIVE_RING = 66;        // the co-op fan-out round the arrival (test_tower_transit clearFloor)

const rad = (d) => d * Math.PI / 180;
const r3 = (v) => Math.round(v * 1000) / 1000;
const around = (ang, r) => [r3(C[0] + r * Math.cos(rad(ang))), r3(C[1] + r * Math.sin(rad(ang)))];
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);

// the machines' anchors (org = the origin; the crate's whole numbers keep crateBox exact)
const VEND = {};
for (const [k, v] of Object.entries(VEND_POLAR)) {
  let org = around(v.ang, v.rad);
  if (v.shift) org = [r3(org[0] + v.shift[0]), r3(org[1] + v.shift[1])];
  if (k === 'crate') org = org.map(Math.round);
  VEND[k] = { org, face: v.face, back: v.back, front: v.front, half: v.half, trig: v.trig, r: v.r, h: v.h };
}

// Crate yaw convention (gen_tower_map.js CRATE_YAW_*): front +x = 270, -x = 90, +y = 0, -y = 180.
const CRATE_YAW_FACE = { 0: 270, 180: 90, 90: 0, 270: 180 };
// the crate's measured footprint at its yaw (gen_tower_map.js crateBox, the same numbers)
function crateFootprint(org, yaw) {
  const E = { x1: -37, x2: 33, y1: -49, y2: 49 };   // at yaw 270 (front +x) - the Ammo Box V6, LOCKSTEP gen_tower_map.js crateBox (docs/208)
  let b;
  if (yaw === 270) b = E;
  else if (yaw === 90) b = { x1: -E.x2, x2: -E.x1, y1: -E.y2, y2: -E.y1 };
  else if (yaw === 0) b = { x1: -E.y2, x2: -E.y1, y1: E.x1, y2: E.x2 };
  else b = { x1: E.y1, x2: E.y2, y1: -E.x2, y2: -E.x1 };
  return [[org[0] + b.x1, org[1] + b.y1], [org[0] + b.x2, org[1] + b.y1], [org[0] + b.x2, org[1] + b.y2], [org[0] + b.x1, org[1] + b.y2]];
}

function furniture() {
  const F = {};
  for (const [k, v] of Object.entries(VEND)) {
    const front = [r3(Math.cos(rad(v.face))), r3(Math.sin(rad(v.face)))];
    const trig = [r3(v.org[0] + front[0] * v.trig), r3(v.org[1] + front[1] * v.trig)];
    let yaw;
    if (k === 'crate') {
      if (!(v.face in CRATE_YAW_FACE)) throw new Error('haven: the crate must face a cardinal direction');
      yaw = CRATE_YAW_FACE[v.face];
    } else if (k === 'wunderfizz') {
      yaw = v.face;                                   // the BO7 ports front on local +X (_tod_perk_scatter v13.3c)
    } else {
      yaw = (v.face + 90) % 360;                      // PaP + altar front on local -Y (yaw 90 faces +x)
      if (yaw === 0) yaw = 359.999;                   // the station's historical spelling of 0
    }
    F[k] = { org: v.org.slice(), trig, yaw: r3(yaw), r: v.r, face: v.face, back: v.back, half: v.half, h: v.h, front };
  }
  F.tp = { trig: C.slice(), r: TP_TRIG_R };
  return F;
}
const FURN = furniture();

// a machine's footprint corners (front depth to back depth, across its face)
const machineBox = (k) => {
  const v = VEND[k], f = FURN[k];
  if (k === 'crate') return crateFootprint(v.org, f.yaw);
  const fx = f.front[0], fy = f.front[1];   // toward the front
  const px = -fy, py = fx;                  // across the face
  // a cycle round the rectangle (boxDist reads b - a and d - a as its two edges)
  const at = (s, d) => [r3(v.org[0] + fx * d + px * v.half * s), r3(v.org[1] + fy * d + py * v.half * s)];
  return [at(-1, v.front), at(-1, -v.back), at(1, -v.back), at(1, v.front)];
};
// the distance from a point to a machine's footprint (0 inside it)
const boxDist = (p, pts) => {
  // the footprints are rectangles given as a cycle; a rotated one is tested in its own frame
  const [a, b, , d] = pts;
  const ux = [b[0] - a[0], b[1] - a[1]], uy = [d[0] - a[0], d[1] - a[1]];
  const lx = Math.hypot(...ux), ly = Math.hypot(...uy);
  if (lx < 1e-6 || ly < 1e-6) return Math.min(...pts.map(q => dist(p, q)));
  const ex = [ux[0] / lx, ux[1] / lx], ey = [uy[0] / ly, uy[1] / ly];
  const rx = (p[0] - a[0]) * ex[0] + (p[1] - a[1]) * ex[1], ry = (p[0] - a[0]) * ey[0] + (p[1] - a[1]) * ey[1];
  const dx = Math.max(0, -rx, rx - lx), dy = Math.max(0, -ry, ry - ly);
  return Math.hypot(dx, dy);
};

// THE EMITTER POSTS (v4): the field's projectors stand in three corners of the hall,
// OUTSIDE the field (the fourth corner is the porch, the way in), short enough to
// stand under the stairs over the loggia; a lit collar each, its gem facing the field.
const PYLON_HALF = 20;
const POST_H = 160;
const COLLAR_Z = 132;
const PYLONS = [['se', 390, -150], ['ne', 390, 390], ['nw', -200, 380]];   // the SE post stands north of the loggia's south inlay (conduit_layout.js)
// THE EMITTER GEMS (make_fx.py's anchors, haven_gem_offsets): each collar's corner
// facing the field, at the collar's height; `d` = the outward direction from the
// field's centre (the effects sit 8 in front of the gem, toward the field).
const FINS = PYLONS.map(([tag, x, y]) => {
  const dd = Math.hypot(x - C[0], y - C[1]), k = PYLON_HALF + 4;
  return { tag, gem: [x - Math.sign(x - C[0]) * k, y - Math.sign(y - C[1]) * k, COLLAR_Z], d: [r3((x - C[0]) / dd), r3((y - C[1]) / dd)] };
});
// Respawn spots: four round the teleporter inside the field (a co-op player comes
// back safe), in the two open quarters (the porch side and the south-east), clear of
// every machine.
// v6: re-spread round the machines facing in and off the sunken stair (the west and the south-east quarters)
const RESPAWN = [190, 215, 315, 335].map(a => around(a, 205));
// Risers: on the hall floor OUTSIDE the field (the corners), so the horde rises in
// the hall and has to walk into the field to reach you. None on the porch fan.
const HALL_RISERS = [[280, -210], [350, -212], [300, 390], [388, 310], [-120, 390], [-130, -200]];

// --- THE GUARDIANS (docs/202 v3; v4: "the elites are not allowed to leave the
// dome. They are stuck inside so you must go inside and kill them") -------------
// They rise INSIDE the corrupted field on a ring between the machines and the dome,
// spread round it (one spot each), off every machine and the up-riders' landing.
const GUARD_R = 272;
const GUARD_SPOTS = [25, 75, 105, 130, 205, 262, 310, 335].map(a => around(a, GUARD_R));   // v6: off the sunken stair, the machines facing in and the respawns
// A player this near the heart (2D) in this z band (the hall, its porch, the
// galleries over it) wakes them; the LEASH band is the floor (the banners go to the
// players in it). The guardians' own bound is the FIELD (_tod_haven: they hunt only
// players inside it, and one found outside it is pulled back in).
const WAKE_R = 640, WAKE_Z = [-100, 420];
const LEASH_R = 1100, LEASH_Z = [-200, 620];   // up to the next lap's landings
// THE FLOOR SIGN (user 2026-10-03, tweak #5): a lit card with the floor number on
// the S wall's bare inner face above the liner (LINER_H), facing the field (+y),
// one unit proud of the wall; red while corrupted, the district's colour once safe.
const SIGN = { org: [20, WALL_IN + 1, 330], yaw: 90, w: 360, h: 180 };

// --- the hall floor, as the boxes geometry() cuts (z = 0 everywhere) -----------
// v6: the sunken stair takes the core's north strip west of its mouth (its side walls stand in the
// two rail strips, from the cut's floor up to rail height: geometry()).
const HALL_FLOORS = [
  { n: 'heart', x1: PORCH_WALL_X2, x2: CORE, y1: PORCH.y2, y2: TRENCH.railS[0] },   // x[-170,256] y[-96,160]
  { n: 'heart north', x1: TRENCH.mouth, x2: CORE, y1: TRENCH.railS[0], y2: CORE },  // x[0,256] y[160,256] (east of the stair's mouth)
  { n: 'heart south', x1: PORCH.x2, x2: CORE, y1: PORCH.y1, y2: PORCH.y2 },     // x[-160,256] y[-224,-96] (east of the fan)
  { n: 'heart west', x1: WALL_IN, x2: PORCH_WALL_X2, y1: PORCH.y2 + PARA, y2: TRENCH.railS[0] }, // x[-236,-170] y[-76,160] (north of the porch wall)
  { n: 'heart south strip', x1: -CORE, x2: CORE, y1: S_STRIP.y1, y2: S_STRIP.y2 },
  { n: 'loggia east', x1: CORE, x2: PX, y1: WALL_IN, y2: PX },
  { n: 'loggia north', x1: WALL_IN, x2: CORE, y1: CORE, y2: PX },
];
const inFloors = (p) => HALL_FLOORS.some(f => p[0] >= f.x1 && p[0] <= f.x2 && p[1] >= f.y1 && p[1] <= f.y2);
// the sunken stair's footprint with its rails (nothing may stand, rise or be placed there), and
// the lane in front of its mouth that must stay open (the field's way out)
const TRENCH_KEEP = { x1: WALL_IN, x2: TRENCH.mouth, y1: TRENCH.railS[0], y2: TRENCH.railN[1] };
const MOUTH_LANE = { x1: TRENCH.mouth, x2: TRENCH.mouth + 96, y1: TRENCH.y1, y2: TRENCH.y2 };
// the porch's mouth into the hall (the way in)
const PORCH_LANE = { x1: PORCH.x2, x2: PORCH.x2 + 72, y1: PORCH.y1, y2: PORCH.y2 };
const inRect = (p, r, pad = 0) => p[0] >= r.x1 - pad && p[0] <= r.x2 + pad && p[1] >= r.y1 - pad && p[1] <= r.y2 + pad;
// on the floor with `r` to spare in every direction (sampled, so it is seam-safe
// across the floor's boxes)
const onFloor = (p, r = 0) => {
  if (!inFloors(p)) return false;
  if (r <= 0) return true;
  for (let i = 0; i < 16; i++) if (!inFloors([p[0] + r * Math.cos(i * Math.PI / 8), p[1] + r * Math.sin(i * Math.PI / 8)])) return false;
  return true;
};

// --- what hangs over the hall (relative to the hall floor) ----------------------
// The next lap's E flight runs over the loggia east (its treads' undersides), its NE
// landing over the loggia's corner, its N flight over the loggia north; the galleries'
// sloped handrails hang into the hall along x[236,256] and y[236,256]. -> the lowest
// thing over (x, y), or Infinity (the open void under the core above, VOID_H).
const end = FLIGHT_RISE, mid2 = LAP_RISE;   // the next lap's base / its NE landing, above the hall floor
function ceilingAt(x, y) {
  let c = VOID_H;
  if (x >= CORE && x <= PX && y >= -CORE && y < CORE) {               // the E flight's treads (+ its ramp clip)
    const i = Math.min(STEPS, Math.max(1, Math.ceil((y + CORE) / TREAD)));
    c = Math.min(c, end + RISE * i - SLAB, end + 2 + (y + CORE + TREAD) * RISE / TREAD - SLAB);
  }
  if (x >= CORE && x <= PX && y >= CORE && y <= PX) c = Math.min(c, mid2 - SLAB);   // the NE landing
  if (y >= CORE && y <= PX && x >= -CORE && x < CORE) {               // the N flight's treads
    const i = Math.min(STEPS, Math.max(1, Math.ceil((CORE - x) / TREAD)));
    c = Math.min(c, mid2 + RISE * i - SLAB);
  }
  if (x >= CORE - PARA && x <= CORE && y >= WALL_IN && y <= CORE - PARA)   // the E gallery's handrail
    c = Math.min(c, end + (y + CORE) * RISE / TREAD - GAL_BELOW);
  if (y >= CORE - PARA && y <= CORE && x >= WALL_IN && x <= CORE)          // the N gallery's handrail
    c = Math.min(c, mid2 + (CORE - x) * RISE / TREAD - GAL_BELOW);
  return c;
}

// --- assertions ---------------------------------------------------------------
(function check() {
  // the sphere: the ring at DOME_R on the floor, the crown at DOME_TOP
  if (Math.abs(domeZ(DOME_R)) > 1e-6 || Math.abs(domeZ(0) - DOME_TOP) > 1e-6) throw new Error('haven: the field sphere misses its ring or its crown');
  const ks = Object.keys(FURN);
  for (let i = 0; i < ks.length; i++) for (let j = i + 1; j < ks.length; j++) {
    const a = FURN[ks[i]], b = FURN[ks[j]];
    const d = dist(a.trig, b.trig), gap = (ks[i] === 'tp' || ks[j] === 'tp') ? PAD_TRIG_GAP : MIN_TRIG_GAP;   // v6: machine <-> pad (see PAD_TRIG_GAP)
    if (d < a.r + b.r + gap) throw new Error(`haven furniture ${ks[i]}<->${ks[j]}: triggers ${Math.round(d)}u apart, rims need ${a.r + b.r + gap}`);
  }
  if (PAD_TRIG_GAP < 32) throw new Error('haven: a machine trigger must clear the pad\'s by a whole player (32)');
  for (const k of Object.keys(VEND)) {
    const v = VEND[k], box = machineBox(k);
    // v6: every machine FACES THE TELEPORTER (its front toward C, within a degree)
    const toC = Math.atan2(C[1] - v.org[1], C[0] - v.org[0]) * 180 / Math.PI;
    const off = Math.abs((((v.face - toC) % 360) + 540) % 360 - 180);
    if (off > 1) throw new Error(`haven ${k}: faces ${v.face}, the teleporter is at ${toC.toFixed(1)} (${off.toFixed(1)} off) - every machine faces in`);
    // every machine body stands on the hall floor, 4 clear of the rails
    for (const p of box) if (!onFloor(p) || !onFloor([p[0] + Math.sign(p[0] - v.org[0]) * 4, p[1] + Math.sign(p[1] - v.org[1]) * 4]))
      throw new Error(`haven ${k}: its body leaves the hall floor at (${p.map(Math.round)})`);
    // v6: off the sunken stair and its rails, out of its mouth's lane and the porch's
    if (boxDist([(TRENCH_KEEP.x1 + TRENCH_KEEP.x2) / 2, (TRENCH_KEEP.y1 + TRENCH_KEEP.y2) / 2], box) < 0 || box.some(p => inRect(p, TRENCH_KEEP, 8)))
      throw new Error(`haven ${k}: its body stands on the sunken stair or its rails`);
    for (const lane of [MOUTH_LANE, PORCH_LANE])
      for (let gx = lane.x1; gx <= lane.x2; gx += 8) for (let gy = lane.y1; gy <= lane.y2; gy += 8)
        if (boxDist([gx, gy], box) < 8) throw new Error(`haven ${k}: its body blocks the ${lane === MOUTH_LANE ? 'sunken stair\'s mouth' : 'porch\'s mouth'} at (${gx}, ${gy})`);
    // INSIDE the field (v4: "all perks and ammo crates pap etc should be inside of the dome"):
    // every corner of its body under the dome with 8 to spare, its trigger well inside
    for (const p of box) if (domeZ(dist(p, C)) < v.h + 8) throw new Error(`haven ${k}: its body reaches out of the dome at (${p.map(Math.round)}) (dome ${Math.round(domeZ(dist(p, C)))} < ${v.h + 8})`);
    if (!insideBody([...FURN[k].trig, 0], IN_R3 - 16)) throw new Error(`haven ${k}: its trigger is not well inside the field`);
    // off the pad: its back clear of the teleporter's trigger by 20
    for (const p of box) if (dist(p, C) < TP_TRIG_R + 20) throw new Error(`haven ${k}: its body crowds the teleporter pad`);
    // clear of the up-riders' landing
    if (boxDist(ARRIVAL, box) < ARRIVE_RING + 40) throw new Error(`haven ${k}: crowds the transit arrival`);
  }
  // the field fits the hall: past the walls only where the walls are solid (S / W: the
  // whole height, never the archway), past the rails only under their visible height
  for (let a = 0; a < 360; a += 0.5) for (let r = 200; r <= DOME_R; r += 2) {
    const [x, y] = around(a, r), z = domeZ(r);
    if (x < WALL_IN && y < ARCH.y2 + PARA) throw new Error(`haven: the field reaches the porch archway at (${Math.round(x)}, ${Math.round(y)})`);
    if ((x > PX || y > PX) && z > RAIL_VIS_H - 2) throw new Error(`haven: the field shows over a rail at (${Math.round(x)}, ${Math.round(y)}) z ${Math.round(z)}`);
    if (x > CORE && y < WALL_IN && z > RAIL_VIS_H - 2) throw new Error(`haven: the field shows over the loggia's south rail at (${Math.round(x)}, ${Math.round(y)})`);
    if (x < WALL_IN && y > CORE && z > RAIL_VIS_H - 2) throw new Error(`haven: the field shows over the loggia's west rail at (${Math.round(x)}, ${Math.round(y)})`);
  }
  // ... and under everything that hangs over it: the galleries' handrails, the next
  // lap's flights and its NE landing, with CEIL_CLEAR to spare (sampled on a 4 grid)
  for (let x = WALL_IN; x <= PX; x += 4) for (let y = WALL_IN; y <= PX; y += 4) {
    const z = domeZ(dist([x, y], C));
    if (z < 0) continue;
    const c = ceilingAt(x, y);
    if (z + CEIL_CLEAR > c) throw new Error(`haven: the field meets the stairs over the hall at (${x}, ${y}): dome ${Math.round(z)}, ceiling ${Math.round(c)}`);
  }
  // the barrier's shell stays inside the hall's walls too (it is the same sphere,
  // down to BASE under the floor): its lowest ring lies inside the floor slab or a wall
  if (BARRIER.base > -SLAB || BARRIER.base < PORCH_LOW) throw new Error('haven: the barrier base must sit under the floor slab and above the porch cut');
  // the fan's north wall: the field's rim comes down onto its EAST end (the low edge of
  // the dome meets the low wall where you walk in); it must never run along it - the
  // wall's top is outside the field over all but its last PORCH_WALL_REST units
  for (let x = WALL_IN; x <= PORCH_WALL_X2; x += 1) for (const y of [PORCH.y2, PORCH.y2 + PARA]) {
    const z = domeZ(dist([x, y], C));
    if (z >= 0 && x < PORCH_WALL_X2 - PORCH_WALL_REST) throw new Error(`haven: the field runs along the porch wall's top at (${x}, ${y})`);
  }
  // the arrival lands inside the field, its whole co-op ring on the hall floor
  if (!insideBody([...ARRIVAL, 0], IN_R3 - 20)) throw new Error('haven: the up-riders land outside the field');
  if (!onFloor(ARRIVAL, ARRIVE_RING)) throw new Error('haven: the arrival fan-out leaves the hall floor');
  // the posts: outside the field (all of them, collars too), on the floor, clear of the
  // machines, under the stairs over them, clear of the arrival
  for (const [tag, x, y] of PYLONS) {
    const p = [x, y], h = PYLON_HALF + 4;
    for (const q of [[x - h, y - h], [x + h, y - h], [x + h, y + h], [x - h, y + h]]) {
      if (dist(q, C) < DOME_R + 8) throw new Error(`haven post ${tag}: inside the field`);
      if (!onFloor(q)) throw new Error(`haven post ${tag}: off the floor`);
      if (ceilingAt(q[0], q[1]) < POST_H + 16) throw new Error(`haven post ${tag}: meets the stairs over it`);
    }
    if (dist(p, ARRIVAL) < ARRIVE_RING + PYLON_HALF + 40) throw new Error(`haven post ${tag}: crowds the arrival`);
  }
  // risers: on the floor (24 to spare), OUTSIDE the field (a body there is out by the
  // out radius + 20), off the arrival (the v10.22 materialize rule, 165), clear of the
  // posts, never on the porch
  for (const p of HALL_RISERS) {
    if (!onFloor(p, 24)) throw new Error(`haven riser (${p}) off the hall floor`);
    if (insideBody([...p, 0], OUT_R3 + 20)) throw new Error(`haven riser (${p}) inside the field`);
    if (dist(p, ARRIVAL) < 165) throw new Error(`haven riser (${p}) within 165 of the arrival`);
    for (const [tag, x, y] of PYLONS) if (dist(p, [x, y]) < PYLON_HALF + 50) throw new Error(`haven riser (${p}) against post ${tag}`);
    if (p[0] < PORCH.x2 + 24 && p[1] < PORCH.y2 + 24) throw new Error(`haven riser (${p}) on the porch fan`);
  }
  for (const p of RESPAWN) {
    if (!onFloor(p, 24)) throw new Error(`haven respawn (${p}) off the floor`);
    if (!insideBody([...p, 0], IN_R3 - 30) || dist(p, C) < TP_TRIG_R + 20) throw new Error(`haven respawn (${p}) must stand in the field, off the pad`);
    if (dist(p, ARRIVAL) < 80) throw new Error(`haven respawn (${p}) on the arrival`);
    for (const k of Object.keys(VEND)) if (boxDist(p, machineBox(k)) < 40) throw new Error(`haven respawn (${p}) against ${k}`);
  }
  // the guardians' spots: on the floor (24 to spare), inside the field with room for a
  // tall body under the dome, off the pad trigger, off the arrival ring, clear of every
  // machine (body and trigger), of the respawns and of each other
  for (const p of GUARD_SPOTS) {
    if (!onFloor(p, 24)) throw new Error(`haven guard spot (${p}) off the floor`);
    if (!insideBody([...p, 0], IN_R3 - 20) || domeZ(dist(p, C)) < 120) throw new Error(`haven guard spot (${p}) must stand well inside the field`);
    if (dist(p, C) < TP_TRIG_R + 24) throw new Error(`haven guard spot (${p}) on the pad`);
    if (dist(p, ARRIVAL) < ARRIVE_RING + 4) throw new Error(`haven guard spot (${p}) on the arrival`);
    for (const k of Object.keys(VEND)) {
      if (boxDist(p, machineBox(k)) < 40) throw new Error(`haven guard spot (${p}) against ${k}`);
      if (dist(p, FURN[k].trig) < FURN[k].r + 8) throw new Error(`haven guard spot (${p}) in ${k}'s trigger`);
    }
    for (const q of RESPAWN) if (dist(p, q) < 64) throw new Error(`haven guard spot (${p}) on respawn (${q})`);
    for (const q of GUARD_SPOTS) if (q !== p && dist(p, q) < 64) throw new Error(`haven guard spots (${p}) and (${q}) crowd each other`);
  }
  // the wake band reaches past the hall (its far corner) but never a neighbouring
  // tower section (the crown road starts 5,000 away)
  if (WAKE_R < dist([OUT, OUT], C) + 24 || WAKE_R > 900) throw new Error('haven wake radius must cover the whole hall and stay on its floor');
  if (LEASH_R <= WAKE_R || LEASH_Z[0] > WAKE_Z[0] || LEASH_Z[1] < WAKE_Z[1]) throw new Error('haven leash must contain the wake band');
  // the sign: on the S wall's inner face above the liner, inside the wall's run,
  // under the ceiling, above the field
  {
    const x1 = SIGN.org[0] - SIGN.w / 2, x2 = SIGN.org[0] + SIGN.w / 2, z1 = SIGN.org[2] - SIGN.h / 2, z2 = SIGN.org[2] + SIGN.h / 2;
    if (SIGN.org[1] !== WALL_IN + 1) throw new Error('haven sign must hang one unit proud of the S wall');
    if (x1 < WALL_IN + 8 || x2 > CORE - PARA - 8) throw new Error('haven sign leaves the S wall\'s inner face');
    if (z1 < LINER_H + 8 || z2 > VOID_H - 24) throw new Error('haven sign must sit above the liner and under the ceiling');
    if (z1 < domeZ(dist([SIGN.org[0], SIGN.org[1] + 40], C)) + 16) throw new Error('haven sign must hang above the field');
    if (SIGN.w <= 0 || SIGN.h <= 0 || Math.abs(SIGN.w / SIGN.h - 2) > 1e-9) throw new Error('haven sign card must be 2:1 (its texture is)');
  }
  // the projector ring stays inside every gallery rail (x / y < CORE - PARA)
  if (C[0] + PROJ_RING[1] > CORE - PARA || C[1] + PROJ_RING[1] > CORE - PARA) throw new Error('haven: the projector ring reaches a gallery rail');
  if (C[0] - PROJ_RING[1] < WALL_IN + LINER_T || C[1] - PROJ_RING[1] < WALL_IN + LINER_T) throw new Error('haven: the projector ring reaches a wall');
  // the z band covers the dome and stops well short of the floor above
  if (Z_ABOVE < DOME_TOP || Z_ABOVE >= LAP_RISE - Z_BELOW) throw new Error('haven: the membership z band must cover the dome and stay on its floor');

  // ---- v6 THE WAY THROUGH ------------------------------------------------------
  // the sunken stair: inside the core (its north rail ends on the core's face), every drop a
  // step a player and a zombie can climb, its mouth one step under the hall floor, its run
  // continuous, its foot under the W wall with a walkable head height, and the stock ramp's slope
  const STEP_MAX = 18;
  if (TRENCH.railN[1] !== CORE) throw new Error('haven stair: the north rail must end on the core\'s north face (the loggia floor runs on north of it)');
  if (TRENCH.rise > STEP_MAX || TRENCH.rise < 8) throw new Error(`haven stair: a ${TRENCH.rise} rise is not a walkable step`);
  if (Math.atan2(TRENCH.rise, TRENCH.tread) * 180 / Math.PI > 35) throw new Error('haven stair: steeper than a stock BO3 stair (35 deg)');
  for (let k2 = 1; k2 <= TRENCH.steps; k2++) {
    const s = trenchStep(k2), prev = k2 === 1 ? { x1: TRENCH.mouth, top: 0 } : trenchStep(k2 - 1);
    if (s.x2 !== prev.x1) throw new Error(`haven stair: step ${k2} does not meet step ${k2 - 1}`);
    if (prev.top - s.top !== TRENCH.rise) throw new Error(`haven stair: step ${k2} drops ${prev.top - s.top}, not one rise`);
    if (s.top - SLAB < TRENCH.low) throw new Error(`haven stair: step ${k2}'s tread would sink under the cut's floor`);
  }
  if (trenchStep(TRENCH.steps).x1 !== TRENCH.foot || TRENCH.foot !== -CORE) throw new Error('haven stair: the last step must run through the W wall to the W flight');
  if (TRENCH.x1 !== WALL_IN) throw new Error('haven stair: its rails start at the W wall\'s inner face');
  if (-SLAB - TRENCH.floor < 120) throw new Error(`haven stair: the foot's head room under the W wall is ${-SLAB - TRENCH.floor} (players and zombies need 120)`);
  // the foot meets the W flight: the flight's walking surface (its ramp, RAMP_LIFT over the
  // nosing line) and its treads beside the foot are each within a step of the foot's floor
  const wRamp = (y) => -(y + CORE - TREAD) * RISE / TREAD + 2;   // the W flight's ramp, relative (gen_tower_map.js rampWedgeY + RAMP_LIFT)
  for (let y = TRENCH.y1; y <= TRENCH.y2; y += 2)
    if (Math.abs(wRamp(y) - TRENCH.floor) > STEP_MAX) throw new Error(`haven stair: the foot is ${Math.round(Math.abs(wRamp(y) - TRENCH.floor))} off the W flight's ramp at y ${y}`);
  const besideFoot = [];
  for (let i = 1; i <= STEPS; i++) { const t = W_TREAD(i); if (t.y2 > TRENCH.y1 && t.y1 < TRENCH.y2) besideFoot.push(i); }
  if (!besideFoot.some(i => Math.abs(W_TREAD(i).top - TRENCH.floor) <= STEP_MAX)) throw new Error('haven stair: no W flight tread beside the foot is a step from it');
  // its mouth is away from the porch (the way in) - across the field - and clear of the pad's
  // model and trigger, and of the up-riders' landing's co-op ring
  const mouthC = [TRENCH.mouth, (TRENCH.y1 + TRENCH.y2) / 2];
  if (dist(mouthC, [PORCH.x2, (PORCH.y1 + PORCH.y2) / 2]) < 2 * DOME_R * 0.6) throw new Error('haven stair: its mouth is not across the field from the porch');
  for (const p of [[TRENCH.mouth, TRENCH.railS[0]], [TRENCH.mouth, TRENCH.y1]])
    if (dist(p, C) < TP_TRIG_R + 4) throw new Error('haven stair: its mouth or rail reaches the teleporter\'s trigger');
  if (TRENCH.mouth > ARRIVAL[0] - ARRIVE_RING - 16) throw new Error('haven stair: its north rail reaches the up-riders\' co-op ring');
  if (!onFloor([TRENCH.mouth + 24, (TRENCH.y1 + TRENCH.y2) / 2])) throw new Error('haven stair: no floor in front of its mouth');
  // the cut stays above the lap's base (16 of core under it) and every surface of the stair
  // stays above the door cut of _tod_reach (lap base + 8): the reach model's cells hold
  if (TRENCH.low < -FLIGHT_RISE + 16 || TRENCH.floor <= -FLIGHT_RISE + 8) throw new Error('haven stair: too deep for the lap band (the reach model\'s door cut)');
  // a body at the foot is outside the field (its z band): the guardians never hunt the foot
  if (TRENCH.floor >= -Z_BELOW) throw new Error('haven stair: its foot must lie under the field\'s z band');
  // THE DEBRIS: under the porch's lowest row, above every tread the foot meets - so the flight
  // above it is reached only from the porch and the flight below only from the foot
  const porchTreads = [];
  for (let k2 = 1; k2 <= PORCH_ROWS; k2++) porchTreads.push(STEPS - k2);
  if (DEBRIS.tread >= Math.min(...porchTreads) || DEBRIS.tread <= Math.max(...besideFoot)) throw new Error(`haven debris: tread ${DEBRIS.tread} must lie between the foot's treads (${besideFoot}) and the porch's (${porchTreads})`);
  if (DEBRIS.top - W_TREAD(DEBRIS.tread).top < 64) throw new Error('haven debris: low enough to step or mantle over');
  // THE ENCLOSURE: each wall piece is a real box, and the north/east runs cover the loggia's
  // whole edge with no gap between pieces
  for (const w of ENCLOSE) if (!(w.x1 < w.x2 && w.y1 < w.y2 && w.top > 0)) throw new Error(`haven ${w.n}: degenerate`);
  const runE = ENCLOSE.filter(w => w.x1 === PX).sort((p, q) => p.y1 - q.y1), runN = ENCLOSE.filter(w => w.y1 === PX && w.x2 <= PX).sort((p, q) => p.x1 - q.x1);
  for (let i = 1; i < runE.length; i++) if (runE[i].y1 !== runE[i - 1].y2) throw new Error(`haven enclosure: a gap in the east wall at y ${runE[i - 1].y2}`);
  for (let i = 1; i < runN.length; i++) if (runN[i].x1 !== runN[i - 1].x2) throw new Error(`haven enclosure: a gap in the north wall at x ${runN[i - 1].x2}`);
  if (runE[0].y1 !== -CORE || runE[runE.length - 1].y2 !== OUT || runN[0].x1 !== -CORE || runN[runN.length - 1].x2 !== PX)
    throw new Error('haven enclosure: the east / north walls must span the loggia\'s whole edge');
  // the galleries' walls: their foot under every tread slab's underside over them
  for (let y = WALL_IN; y <= CORE - PARA; y += 4) {
    const i = Math.min(STEPS, Math.max(1, Math.ceil((y + CORE) / TREAD)));
    if (FLIGHT_RISE + RISE * (y + CORE) / TREAD - GAL_BELOW > FLIGHT_RISE + RISE * i - SLAB) throw new Error(`haven E gallery wall: its foot is over the tread at y ${y} (a slit)`);
  }
  for (let x = WALL_IN; x <= CORE; x += 4) {
    const i = Math.min(STEPS, Math.max(1, Math.ceil((CORE - x) / TREAD)));
    if (LAP_RISE + RISE * (CORE - x) / TREAD - GAL_BELOW > LAP_RISE + RISE * i - SLAB) throw new Error(`haven N gallery wall: its foot is over the tread at x ${x} (a slit)`);
  }
  // the dome stays CEIL_CLEAR under the walls' cyan foot trims too (4 proud of the walls)
  for (let y = WALL_IN; y <= CORE - PARA; y += 4) {
    const z = domeZ(dist([CORE - PARA - 4, y], C));
    if (z >= 0 && z + CEIL_CLEAR > FLIGHT_RISE + RISE * (y + CORE) / TREAD - GAL_BELOW) throw new Error(`haven: the field meets the E gallery wall's trim at y ${y}`);
  }
  for (let x = WALL_IN; x <= CORE - PARA; x += 4) {
    const z = domeZ(dist([x, CORE - PARA - 4], C));
    if (z >= 0 && z + CEIL_CLEAR > LAP_RISE + RISE * (CORE - x) / TREAD - GAL_BELOW) throw new Error(`haven: the field meets the N gallery wall's trim at x ${x}`);
  }
  // nothing else stands on the stair, its rails, or its mouth's / the porch's lanes
  const clearOf = (p, pad, what, porchToo = true) => {
    if (inRect(p, TRENCH_KEEP, pad) || inRect(p, MOUTH_LANE, pad)) throw new Error(`haven ${what} (${p.map(Math.round)}) on the sunken stair or its mouth`);
    if (porchToo && inRect(p, PORCH_LANE, Math.min(pad, 16))) throw new Error(`haven ${what} (${p.map(Math.round)}) in the porch's mouth`);
  };
  for (const p of RESPAWN) clearOf(p, 24, 'respawn');
  for (const p of GUARD_SPOTS) clearOf(p, 24, 'guard spot');
  for (const p of HALL_RISERS) clearOf(p, 24, 'riser', false);   // a riser by the way in is v4's corner outside the field (the horde meets you at the door)
  for (const [tag, x, y] of PYLONS) clearOf([x, y], PYLON_HALF + 8, `post ${tag}`);
  // the posts and the risers keep off the new walls (the rails they replaced were the same lines)
  for (const [tag, x, y] of PYLONS) if (x + PYLON_HALF + 4 > PX || y + PYLON_HALF + 4 > PX) throw new Error(`haven post ${tag}: into the enclosure`);
  // NAVMESH SEEDS never stand in a machine (a seed inside the crate's clip seeded its top as a
  // one-face island and split the floor's walk - caught by a scratch cod2map, 2026-10-04) nor on
  // a post; the hall's own seeds stand on its floor, the stair's on its treads
  for (const [label, x, y] of seeds(0)) {
    for (const k of Object.keys(VEND)) if (boxDist([x, y], machineBox(k)) < 16) throw new Error(`haven seed ${label}: inside / against ${k}`);
    for (const [tag, px, py] of PYLONS) if (Math.abs(x - px) < PYLON_HALF + 16 && Math.abs(y - py) < PYLON_HALF + 16) throw new Error(`haven seed ${label}: on post ${tag}`);
    if (/stair/.test(label)) { if (!inRect([x, y], { x1: TRENCH.foot, x2: TRENCH.mouth, y1: TRENCH.y1, y2: TRENCH.y2 })) throw new Error(`haven seed ${label}: off the stair`); }
    else if (!/porch/.test(label) && !onFloor([x, y], 8)) throw new Error(`haven seed ${label}: off the hall floor`);
  }
})();

// Teddy bears (_tod_secret): the pivot is the bear's centre. Since docs/208 the bear is
// the fan's Cyber Teddy (art/cyber_teddy/manifest.json, LOCKSTEP with _tod_secret's
// TOD_SECRET_LIFT / _HALF_DEPTH; tools/cyber_teddy/verify.py checks all three): the
// pivot 14.0 above the surface, "back to a wall" 7.9 off it (its back extent 7.85
// rounded up), and BEAR_EXT = its half extents (local X across, local Y front/back),
// asserted below against the walls and rails. Floor 10: on the hall floor, back to
// the W wall's liner, facing into the hall (east). Floor 20: in the loggia's far
// south-east corner under the next lap's E flight, facing north, BEAR_SIDE off the
// east rail (its 11.3 arm reached 3.4 into the rail at the old 6).
const BEAR_LIFT = 14.0, BEAR_HALF = 7.9, BEAR_SIDE = 11.4;
const BEAR_EXT = [11.311, 7.85];
const BEARS = {
  floor10: { org: [WALL_IN + LINER_T + BEAR_HALF, -40, BEAR_LIFT], yaw: 90, label: 'floor 10 haven heart (back to the W wall)' },
  floor20: { org: [PX - BEAR_SIDE, WALL_IN + BEAR_HALF, BEAR_LIFT], yaw: 180, label: 'floor 20 haven loggia (the SE corner)' },
};
for (const b of Object.values(BEARS)) {
  if (!onFloor(b.org)) throw new Error(`haven bear ${b.label}: off the floor`);
  // docs/208: the WHOLE bear stays on the walkable square - its back off the wall's
  // liner, its arms out of the rails (yaw 0/180: across = world x; 90/270: across = world y)
  const q = ((b.yaw % 180) + 180) % 180;
  if (q !== 0 && q !== 90) throw new Error(`haven bear ${b.label}: its yaw must be axis-aligned`);
  const hx = q === 0 ? BEAR_EXT[0] : BEAR_EXT[1], hy = q === 0 ? BEAR_EXT[1] : BEAR_EXT[0];
  if (b.org[0] - hx < WALL_IN + LINER_T - 1e-6 || b.org[0] + hx > PX + 1e-6 || b.org[1] - hy < WALL_IN - 1e-6 || b.org[1] + hy > PX + 1e-6)
    throw new Error(`haven bear ${b.label}: its body reaches past the floor's walls or rails`);
  for (const [tag, x, y] of PYLONS) if (Math.abs(b.org[0] - x) < PYLON_HALF + 4 + BEAR_HALF + 4 && Math.abs(b.org[1] - y) < PYLON_HALF + 4 + BEAR_HALF + 4) throw new Error(`haven bear ${b.label}: against post ${tag}`);
}

// The lounge box(es) for _tod_breather_data::lounge_index_at (the arrival chime
// and the spawn-relief check): the hall, its porch and its loggia.
const ROOM_RECTS = [{ x1: -CORE, x2: OUT, y1: -CORE, y2: OUT }];
// The farthest any haven brush reaches from the tower axis (VOL_R / sky clearance).
const EXTENT = OUT;
// The Battle Arena chamber on floor 40 (docs/185): THE FIELD ITSELF. The arena's
// gate stands at the field's centre and "everyone inside" means everyone in the
// field (the script tests the box and then the radius).
const CHAMBER = { org: C.slice(), r: DOME_R, x1: C[0] - DOME_R, x2: C[0] + DOME_R, y1: C[1] - DOME_R, y2: C[1] + DOME_R };
// A fitted box reflection probe per hall (the transit bay's recipe): its box
// reaches the hall's walls, the loggia's rails, the floor and the ceiling.
const PROBE = { org: [(-CORE + OUT) / 2, (-CORE + OUT) / 2, VOID_H / 2], half: [(OUT + CORE) / 2, (OUT + CORE) / 2, VOID_H / 2] };
// v6: the generator cuts the core under the sunken stair too (z relative to the hall floor):
// x from the core's W face (the stair's foot tunnels under the W wall) to its mouth, y its width,
// from the cut's floor up to the slab's underside.
const TRENCH_CUT = { x1: TRENCH.foot, x2: TRENCH.mouth, y1: TRENCH.railS[0], y2: TRENCH.railN[1], zLo: TRENCH.low, zHi: -SLAB };   // its side walls fill the rail strips (geometry())

// --- geometry ---------------------------------------------------------------
// `k` = the generator's emitters (all absolute even-frame coordinates):
//   k.box(label, x1,x2,y1,y2,z1,z2, role)        axis box in a kit role (tod_cc_<role>)
//   k.clip(label, x1,x2,y1,y2,z1,z2)              axis clip (invisible guard)
//   k.poly(label, vertices, faces, roles)         convex solid; roles = one per face, or one string
//   k.rampX(label, y1,y2, x1,x2, zAtX1,zAtX2, rise, tread)   the tower's stair ramp clip (gen_tower_map.js rampWedgeX)
// `theme` = { floor: <deck role>, wall: <block role> } from the floor's district.
// `opts.postAbove` = the next lap's door carries a gate post in the rail band (gen_tower_map.js
// doorPostAt): the east wall's first 10 units stop at its foot.
// The S and W WALLS and the core cuts (the porch's and the sunken stair's) are the generator's
// (the core bands' colours); everything else in the hall is here. Every label starts `lap<L> haven `.
function geometry(k, lap, m, theme, opts = {}) {
  const ENCLOSE = enclose(opts.postAbove !== false);
  const L = `lap${lap} haven `;
  const B = (n, x1, x2, y1, y2, z1, z2, role) => {
    if (!(x1 < x2 && y1 < y2 && z1 < z2)) throw new Error(`haven: degenerate box "${n}" ${[x1, x2, y1, y2, z1, z2]}`);
    k.box(L + n, x1, x2, y1, y2, m + z1, m + z2, role);
  };
  const CL = (n, x1, x2, y1, y2, z1, z2) => k.clip(L + n, x1, x2, y1, y2, m + z1, m + z2);
  const P = (n, verts, faces, roles) => k.poly(L + n, verts.map(([x, y, z]) => [r3(x), r3(y), r3(m + z)]), faces, roles);
  // a guarded edge: the clip along the whole run, the visible rail over it
  const rail = (n, x1, x2, y1, y2) => {
    CL(`${n} guard`, x1, x2, y1, y2, 0, RAIL_CLIP_TOP);
    B(`${n} rail`, x1, x2, y1, y2, 0, RAIL_VIS_H, 'graphite');
  };

  // ---- FLOORS (axis decks, HALL_FLOORS + the strips the stair's rails stand on) --
  const floorRole = { 'heart': 'velvet', 'heart north': 'velvet', 'heart south': 'velvet', 'heart west': 'velvet', 'heart south strip': 'velvet', 'loggia east': theme.floor, 'loggia north': theme.floor };
  for (const f of HALL_FLOORS) B(`${f.n} floor`, f.x1, f.x2, f.y1, f.y2, -SLAB, 0, floorRole[f.n]);

  // ---- THE SUNKEN STAIR (v6, see TRENCH): the generator cuts the core under it
  // (CUT.trench); every step is a 16-thick deck tread on a solid filler down to the
  // cut's floor, so no pocket is ever sealed under it and the lint walks the treads;
  // the stock ramp clip rides the nosings (the tower's flights' recipe); the last
  // step runs on under the W wall to the W flight. Railed both sides, open at its mouth.
  for (let k2 = 1; k2 <= TRENCH.steps; k2++) {
    const s = trenchStep(k2);
    B(`stair step ${k2}`, s.x1, s.x2, TRENCH.y1, TRENCH.y2, s.top - SLAB, s.top, theme.floor);
    if (s.top - SLAB > TRENCH.low) B(`stair step ${k2} fill`, s.x1, s.x2, TRENCH.y1, TRENCH.y2, TRENCH.low, s.top - SLAB, theme.wall);   // the foot's tread sits on the cut's floor itself
  }
  // the ramp's line passes every step's descending (west) edge at that step's top: from one tread
  // past the last intermediate step, at the foot's level, up to the mouth (the hall floor's edge)
  // at 0 - the tower flights' rule (gen_tower_map.js rampWedgeY: low end a tread onto the lower
  // landing, high end where the flat top begins)
  // (labelled like the tower's own ramps, `lap<L> ... stair ramp` without the `haven` prefix: the
  // geometry lint models a flight by its treads and skips its ramp clip, as it does every flight's)
  k.rampX(`lap${lap} sunken stair ramp`, TRENCH.y1, TRENCH.y2, TRENCH.mouth - TRENCH.tread * TRENCH.steps, TRENCH.mouth, m + TRENCH.floor, m, TRENCH.rise, TRENCH.tread);
  // its two sides: one solid wall each from the cut's floor to rail height over the hall floor
  // (a parapet round the stairwell on the hall side; under the W wall, the foot's tunnel's sides),
  // with the tower's rail clip over it - one block from every tread's shin to above its chest
  for (const [n, y1, y2] of [['south', TRENCH.railS[0], TRENCH.railS[1]], ['north', TRENCH.railN[0], TRENCH.railN[1]]]) {
    B(`stair wall ${n}`, TRENCH.x1, TRENCH.mouth, y1, y2, TRENCH.low, RAIL_VIS_H, theme.wall);
    B(`stair tunnel wall ${n}`, TRENCH.foot, TRENCH.x1, y1, y2, TRENCH.low, -SLAB, theme.wall);
    CL(`stair ${n} guard`, TRENCH.x1, TRENCH.mouth, y1, y2, 0, RAIL_CLIP_TOP);
  }
  // a lit cyan sill along the mouth's lip (a 1-unit inlay on the hall floor: the way down reads from the field)
  B('stair mouth sill', TRENCH.mouth, TRENCH.mouth + 8, TRENCH.y1, TRENCH.y2, 0, 1, 'cyan');

  // ---- THE COLLAPSE DEBRIS on the W flight (v6, see DEBRIS): tread 11, under the porch --
  {
    const t = W_TREAD(DEBRIS.tread);
    B('debris block', -PX, -CORE, t.y1, t.y2, t.top, DEBRIS.top, theme.wall);
    B('debris cap', -PX + 12, -CORE - 12, t.y1 + 4, t.y2 - 4, DEBRIS.top, DEBRIS.cap, 'graphite');
    CL('debris guard', -PX, -CORE, t.y1, t.y2, DEBRIS.cap, DEBRIS.clipTop);
  }

  // ---- THE PORCH: the stepped fan (solid cells down to the core cut) ----------
  for (let k2 = 1; k2 <= PORCH_ROWS; k2++) {
    const y1 = -CORE + TREAD * k2, y2 = y1 + TREAD;
    for (let s = 1; s <= PORCH_COLS; s++) {
      const top = (s < k2) ? -RISE * (k2 - s) : 0;
      B(`porch row ${k2} cell ${s}`, -CORE + TREAD * (s - 1), -CORE + TREAD * s, y1, y2, PORCH_LOW, top, theme.floor);
    }
  }
  // the fan's north edge: a low wall from the core top up to rail height (the
  // hall floor north of it is 12..36 higher than the cells), clip-capped like
  // every rail; below the core top the core's own face closes the fan
  B('porch wall north', WALL_IN, PORCH_WALL_X2, PORCH.y2, PORCH.y2 + PARA, -SLAB, RAIL_VIS_H, theme.wall);
  CL('porch wall north guard', WALL_IN, PORCH_WALL_X2, PORCH.y2, PORCH.y2 + PARA, 0, RAIL_CLIP_TOP);
  // the archway's lit lintel (the W wall above it is the generator's)
  B('porch arch lintel', -CORE, WALL_IN, ARCH.y1, ARCH.y2, ARCH.top - SLAB, ARCH.top, 'cyan');

  // ---- THE ENCLOSURE (v6, user 2026-10-04 after the first real playthrough: "the zone has
  // these open areas where you can see inside. You shouldnt be able to see until you are on the
  // floor"). The loggia's four open edges were 39-tall rails with sky above them, and the next
  // lap's flights ran round the void behind sloped handrails, so the field was in plain view from
  // the stairs above, from the S flight's end and from outside the tower. Now:
  //   * the loggia's edges are WALLS from the slab's underside up to whatever is over them - the
  //     next lap's E / N flight parapets (stepped like them, ENCLOSE below), its NE landing, the
  //     E flight's first tread and the N flight's last - so they meet with no slot;
  //   * the galleries' inner edges are WALLS from under the flight up to the void's ceiling.
  // From the stairs and from outside, the field cannot be seen; the porch's arch, at the floor's
  // own level, is the way in and the one place to look in from.
  for (const w of ENCLOSE) B(w.n, w.x1, w.x2, w.y1, w.y2, -SLAB, w.top, theme.wall);
  const slope = RISE / TREAD;                                   // the nosing line's rise per unit run
  const ez = (y) => end + slope * (y + CORE);                   // the E flight: climbs toward +y
  const nz = (x) => mid2 + slope * (CORE - x);                  // the N flight: climbs toward -x
  const FACES = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]];
  // a wall along y (x1..x2 thick) from the sloped plane zf(y) + lo up to the flat z `top`
  const wallY = (n, x1, x2, ya, yb, zf, lo, top, role) => P(n, [
    [x1, ya, zf(ya) + lo], [x2, ya, zf(ya) + lo], [x2, yb, zf(yb) + lo], [x1, yb, zf(yb) + lo],
    [x1, ya, top], [x2, ya, top], [x2, yb, top], [x1, yb, top]], FACES, role);
  // a wall along x (y1..y2 thick) from zf(x) + lo up to `top`
  const wallX = (n, xa, xb, y1, y2, zf, lo, top, role) => P(n, [
    [xa, y1, zf(xa) + lo], [xb, y1, zf(xb) + lo], [xb, y2, zf(xb) + lo], [xa, y2, zf(xa) + lo],
    [xa, y1, top], [xb, y1, top], [xb, y2, top], [xa, y2, top]], FACES, role);
  // the galleries: under the flight's treads (GAL_BELOW under its nosing line, below every
  // tread slab's underside) up to the void's ceiling, where the core resumes. The E wall stops at
  // y = 236 and the N wall owns the corner; below y = -236 the S wall closes the E flight.
  wallY('E gallery wall', CORE - PARA, CORE, WALL_IN, CORE - PARA, ez, -GAL_BELOW, VOID_H, theme.wall);
  wallX('N gallery wall', WALL_IN, CORE, CORE - PARA, CORE, nz, -GAL_BELOW, VOID_H, theme.wall);
  // a lit cyan line along each gallery wall's foot, on its hall face (the old cap line's job: the
  // edge of the stairs over you, read from below) - a sloped strip GAL_CAP tall, 4 proud
  const stripY = (n, x1, x2, ya, yb, zf, lo, hi, role) => P(n, [
    [x1, ya, zf(ya) + lo], [x2, ya, zf(ya) + lo], [x2, yb, zf(yb) + lo], [x1, yb, zf(yb) + lo],
    [x1, ya, zf(ya) + hi], [x2, ya, zf(ya) + hi], [x2, yb, zf(yb) + hi], [x1, yb, zf(yb) + hi]], FACES, role);
  const stripX = (n, xa, xb, y1, y2, zf, lo, hi, role) => P(n, [
    [xa, y1, zf(xa) + lo], [xb, y1, zf(xb) + lo], [xb, y2, zf(xb) + lo], [xa, y2, zf(xa) + lo],
    [xa, y1, zf(xa) + hi], [xb, y1, zf(xb) + hi], [xb, y2, zf(xb) + hi], [xa, y2, zf(xa) + hi]], FACES, role);
  stripY('E gallery wall trim', CORE - PARA - 4, CORE - PARA, WALL_IN, CORE - PARA - 4, ez, -GAL_BELOW, -GAL_BELOW + GAL_CAP, 'cyan');
  stripX('N gallery wall trim', WALL_IN, CORE - PARA, CORE - PARA - 4, CORE - PARA, nz, -GAL_BELOW, -GAL_BELOW + GAL_CAP, 'cyan');

  // ---- THE WALL LINERS: the district's wall panel inside the hall, up to the
  // arch line (the lintel's top), so the interior reads as one wainscot --------
  B('liner south', WALL_IN, CORE - PARA, WALL_IN, WALL_IN + LINER_T, 0, LINER_H, theme.wall);   // stops at the E gallery's slot
  B('liner west', WALL_IN, WALL_IN + LINER_T, PORCH.y2 + PARA, CORE, 0, LINER_H, theme.wall);
  B('liner west over the porch wall', WALL_IN, WALL_IN + LINER_T, PORCH.y2, PORCH.y2 + PARA, RAIL_VIS_H, LINER_H, theme.wall);

  // ---- THE EMITTER POSTS (v4): short columns in three corners, a lit collar each
  for (const [tag, x, y] of PYLONS) {
    B(`pylon ${tag}`, x - PYLON_HALF, x + PYLON_HALF, y - PYLON_HALF, y + PYLON_HALF, 0, POST_H, 'graphite');
    B(`pylon ${tag} collar`, x - PYLON_HALF - 4, x + PYLON_HALF + 4, y - PYLON_HALF - 4, y + PYLON_HALF + 4, COLLAR_Z - 12, COLLAR_Z + 12, 'cyan');
    B(`pylon ${tag} cap`, x - PYLON_HALF - 2, x + PYLON_HALF + 2, y - PYLON_HALF - 2, y + PYLON_HALF + 2, POST_H, POST_H + 6, 'cyan');
  }

  // ---- RINGS: the field's base ring (1-unit inlays; a segment that would leave the
  // hall floor - into a wall, a rail or over the porch - is not laid), the pad's
  // ring, and the projector ring on the ceiling over the field ----------------------
  const ring = (n, r0, r1, z0, z1, role, seg, keep) => {
    for (let i = 0; i < seg; i++) {
      const a0 = i * 360 / seg, a1 = (i + 1) * 360 / seg;
      const [i0, i1, o0, o1] = [around(a0, r0), around(a1, r0), around(a0, r1), around(a1, r1)];
      if (keep && ![i0, i1, o0, o1].every(keep)) continue;
      P(`${n} ${i + 1}`, [[...i0, z0], [...i1, z0], [...o1, z0], [...o0, z0], [...i0, z1], [...i1, z1], [...o1, z1], [...o0, z1]],
        [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], role);
    }
  };
  ring('field ring', DOME_R - RING_W, DOME_R, 0, 1, 'cyan', RING_SEG, (p) => onFloor(p, 4));
  ring('pad ring', PAD_RING[0], PAD_RING[1], 0, 1, 'cyan', 24);
  ring('projector ring', PROJ_RING[0], PROJ_RING[1], VOID_H - 16, VOID_H, 'cyan', 24);
  // the projector: an inverted pyramid hanging over the teleporter
  P('projector', [[C[0] - 40, C[1] - 40, VOID_H], [C[0] + 40, C[1] - 40, VOID_H], [C[0] + 40, C[1] + 40, VOID_H], [C[0] - 40, C[1] + 40, VOID_H], [C[0], C[1], VOID_H - 64]],
    [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]], 'graphite');
}

// THE BARRIER's brushes for one haven, `m` = the hall floor's z: each one
// { verts: [[x,y,z]...], faces: [[i...]...] } (absolute), the generator writes them as
// planes of one script_brushmodel (targetname tod_haven_barrier_<floor>).
function barrierBrushes(m) {
  const S = DOME_S, cz = DOME_C;
  const e0 = Math.asin((BARRIER.base - cz) / S);                   // the lowest ring's elevation (under the floor)
  const band = (Math.PI / 2 - e0) / BARRIER.lat;
  const k = (S - BARRIER.thick) / S;                                // the inner face: the homothety about the centre
  const ctr = [C[0], C[1], m + cz];
  const P = (lon, lat) => {                                         // a point ON the sphere
    const e = Math.min(Math.PI / 2, e0 + band * lat), a = lon * 2 * Math.PI / BARRIER.lon;
    return [ctr[0] + S * Math.cos(e) * Math.cos(a), ctr[1] + S * Math.cos(e) * Math.sin(a), ctr[2] + S * Math.sin(e)];
  };
  const inner = (p) => p.map((v, i) => ctr[i] + k * (v - ctr[i]));
  const out = [];
  for (let j = 0; j < BARRIER.lat; j++) for (let i = 0; i < BARRIER.lon; i++) {
    const top = (j === BARRIER.lat - 1);
    const o = top ? [P(i, j), P(i + 1, j), P(i, j + 1)] : [P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)];
    const n = o.length;
    const verts = [...o, ...o.map(inner)].map(p => p.map(r3));
    const faces = [[...Array(n).keys()], [...Array(n).keys()].map(q => q + n)];
    for (let q = 0; q < n; q++) faces.push([q, (q + 1) % n, (q + 1) % n + n, q + n]);
    out.push({ verts, faces, label: `barrier band ${j + 1} seg ${i + 1}` });
  }
  return out;
}

// The core cut + walls the generator emits (its core bands own the colours).
//   the S wall: x[-CORE, CORE] y[-CORE, WALL_IN], from the core top (m - SLAB) to m + VOID_H
//   the W wall: x[-CORE, WALL_IN] y[ARCH.y2 (below the arch top) or WALL_IN (above it), CORE]
//   the core cut under the porch: x[PORCH.x1, PORCH.x2] y[PORCH.y1, PORCH.y2] z m + PORCH_LOW .. m - SLAB
const CUT = {
  voidH: VOID_H, wallT: WALL_T, wallIn: WALL_IN, arch: ARCH,
  porch: { x1: PORCH.x1, x2: PORCH.x2, y1: PORCH.y1, y2: PORCH.y2, zLo: PORCH_LOW },
  trench: TRENCH_CUT,   // v6: the sunken stair (x to the core's W face: its foot tunnels under the W wall)
};

// Zone volumes: the lap's ring volumes cover the loggia; the hall over the core
// needs its own (the core used to be solid, so no ring volume reaches it).
function zoneBrushes(volumeBrush, zLo, zHi) {
  return [volumeBrush(-CORE, CORE, -CORE, CORE, zLo, zHi)];
}

// Risers: the lap's two ordinary landing risers, and the hall's own, OUTSIDE the field.
function risers(m, end) {
  return [[-336, -336, m], [336, -336, end], ...HALL_RISERS.map(([x, y]) => [x, y, m])];
}

// Navmesh seeds: every walkable surface (the navmesh-is-seeded-flood rule): the
// heart, the loggia arms and corner, the south strip and the fan's lower cells.
function seeds(m) {
  const out = [
    ['haven heart', C[0], C[1] + 120, m + 2], ['haven heart w', -200, 0, m + 2],   // v6: off the crate (now due west of the pad: a seed inside its clip seeded its top as an island)
    ['haven loggia e', 336, 0, m + 2], ['haven loggia n', 0, 336, m + 2], ['haven loggia ne', 336, 336, m + 2],
    ['haven south strip', 100, S_STRIP.y2 + 8, m + 2],
  ];
  for (let k2 = 2; k2 <= PORCH_ROWS; k2++)
    out.push([`haven porch row ${k2}`, -CORE + TREAD / 2, -CORE + TREAD * k2 + TREAD / 2, m - RISE * (k2 - 1) + 2]);
  // v6: the sunken stair (its ramp seeds itself too) and its foot under the W wall
  for (const k2 of [3, 6, 9]) {
    const s = trenchStep(k2);
    out.push([`haven stair step ${k2}`, (s.x1 + s.x2) / 2, (TRENCH.y1 + TRENCH.y2) / 2, m + s.top + 2]);
  }
  out.push(['haven stair foot', TRENCH.foot + 8, (TRENCH.y1 + TRENCH.y2) / 2, m + TRENCH.floor + 2]);
  return out;
}

// Lights (all powered: the generator's light() applies LIGHTS_AT_POWER). Labels
// start `tod light lap<L> haven` (tower_lighting.js keeps their colours saturated).
function lights(lap, m, districtLight) {
  const L = `tod light lap${lap} haven`;
  const out = [
    { label: `${L} key`, org: [C[0], C[1], m + 440], color: '0.55 0.9 1', radius: 640, stops: 8.4 },
    { label: `${L} loggia east`, org: [340, 0, m + 150], color: districtLight, radius: 320, stops: 8.2 },
    { label: `${L} loggia north`, org: [0, 340, m + 250], color: districtLight, radius: 320, stops: 8.2 },
    { label: `${L} loggia corner`, org: [340, 340, m + 260], color: districtLight, radius: 260, stops: 8.2 },
    { label: `${L} porch`, org: [-196, -160, m + 150], color: districtLight, radius: 280, stops: 8.2 },
  ];
  for (const [tag, x, y] of PYLONS) {
    const d = dist([x, y], C), ux = (C[0] - x) / d, uy = (C[1] - y) / d;
    out.push({ label: `${L} pylon ${tag}`, org: [r3(x + ux * 40), r3(y + uy * 40), m + COLLAR_Z], color: '0.3 0.8 1', radius: 220, stops: 8.0 });
  }
  return out;
}

// --- the script data (appended to _tod_breather_data.gsc by the generator) -----
function dataGsc() {
  const v = (p) => `( ${p[0]}, ${p[1]}, z )`;
  const lines = [];
  lines.push('// THE HAVENS (docs/202) — the safe-zone field. Every number below is cut from');
  lines.push('// tools/haven_layout.js, the same file that cuts the hall, the rings, the posts');
  lines.push('// and the barrier, so the field the player sees is the volume _tod_haven.gsc tests.');
  lines.push(`function haven_center( z ) { return ${v(C)}; }`);
  lines.push(`function haven_radius()    { return ${DOME_R}; }`);
  lines.push('// v4: membership is the SPHERE (a body\'s chest, haven_body_up() over its origin):');
  lines.push('// in within haven_in_r3() of the sphere\'s centre, out past haven_out_r3(), inside');
  lines.push('// the z band haven_z_below() .. haven_z_above() round the floor');
  lines.push(`function haven_body_up()   { return ${BODY_UP}; }`);
  lines.push(`function haven_in_r3()     { return ${r3(IN_R3)}; }`);
  lines.push(`function haven_out_r3()    { return ${r3(OUT_R3)}; }`);
  lines.push(`function haven_z_below()   { return ${Z_BELOW}; }`);
  lines.push(`function haven_z_above()   { return ${Z_ABOVE}; }`);
  lines.push(`function haven_sphere_r()  { return ${r3(DOME_S)}; }`);
  lines.push(`function haven_sphere_c()  { return ${r3(DOME_C)}; }`);
  lines.push(`function haven_top()       { return ${r3(DOME_TOP)}; }`);
  lines.push('// the two perk pads (_tod_perk_scatter), k = 0 / 1: north-east and north-west of the pad, facing out');
  lines.push('function haven_perk_org( k, z )');
  lines.push('{');
  lines.push(`    if ( k == 0 ) return ${v(FURN.wunderfizz.org)};`);
  lines.push(`    return ${v(FURN.wunderfizz.org)};`);
  lines.push('}');
  lines.push(`function haven_perk_yaw( k ) { if ( k == 0 ) return ${FURN.wunderfizz.yaw}; return ${FURN.wunderfizz.yaw}; }`);
  lines.push(`function haven_perk_front( k ) { if ( k == 0 ) return ( ${FURN.wunderfizz.front[0]}, ${FURN.wunderfizz.front[1]}, 0 ); return ( ${FURN.wunderfizz.front[0]}, ${FURN.wunderfizz.front[1]}, 0 ); }`);
  lines.push('// the emitter gems on the posts\' collars (the field anchors), local to the field centre');
  lines.push('function haven_gem_offsets()');
  lines.push('{');
  lines.push('    a = [];');
  FINS.forEach((f, i) => lines.push(`    a[ ${i} ] = ( ${r3(f.gem[0] - C[0] - f.d[0] * 8)}, ${r3(f.gem[1] - C[1] - f.d[1] * 8)}, ${f.gem[2]} );`));
  lines.push('    return a;');
  lines.push('}');
  lines.push('// the teddy bears that live in the havens (_tod_secret): 1 = floor 10, 2 = floor 20');
  lines.push(`function secret_bear_org( i, z ) { if ( i == 1 ) return ( ${BEARS.floor10.org[0]}, ${BEARS.floor10.org[1]}, z + ${BEARS.floor10.org[2]} ); return ( ${BEARS.floor20.org[0]}, ${BEARS.floor20.org[1]}, z + ${BEARS.floor20.org[2]} ); }`);
  lines.push(`function secret_bear_yaw( i ) { if ( i == 1 ) return ${BEARS.floor10.yaw}; return ${BEARS.floor20.yaw}; }`);
  // the rest stop's two stock ambient loops (_tod_atmosphere::lounge_fx): dust motes
  // drifting down the loggia's open corner, and a soft vent at the porch's foot.
  lines.push('// the rest stop\'s ambient loops (_tod_atmosphere::lounge_fx)');
  lines.push(`function haven_motes_org( z ) { return ( 336, 336, z + 260 ); }`);
  lines.push(`function haven_vent_org( z )  { return ( ${PORCH.x2 + 24}, ${PORCH.y1 + 16}, z + 8 ); }`);
  lines.push('// THE GUARDIANS (docs/202 v3): where they rise (inside the field, spread round it, off');
  lines.push('// the machines and the pad), the wake band round the heart, the floor band their banners reach');
  lines.push('function haven_guard_spots( z )');
  lines.push('{');
  lines.push('    a = [];');
  GUARD_SPOTS.forEach((p, i) => lines.push(`    a[ ${i} ] = ${v(p)};`));
  lines.push('    return a;');
  lines.push('}');
  lines.push(`function haven_wake_r()     { return ${WAKE_R}; }`);
  lines.push(`function haven_wake_z_lo()  { return ${WAKE_Z[0]}; }`);
  lines.push(`function haven_wake_z_hi()  { return ${WAKE_Z[1]}; }`);
  lines.push(`function haven_leash_r()    { return ${LEASH_R}; }`);
  lines.push(`function haven_leash_z_lo() { return ${LEASH_Z[0]}; }`);
  lines.push(`function haven_leash_z_hi() { return ${LEASH_Z[1]}; }`);
  lines.push('// THE FLOOR SIGN (tweak #5): the lit floor-number card on the S wall, facing the field');
  lines.push(`function haven_sign_org( z ) { return ( ${SIGN.org[0]}, ${SIGN.org[1]}, z + ${SIGN.org[2]} ); }`);
  lines.push(`function haven_sign_yaw()    { return ${SIGN.yaw}; }`);
  lines.push('// THE BARRIER (v4): the script_brushmodel on the field\'s sphere, one per haven floor');
  lines.push('function haven_barrier_name( floor ) { return "tod_haven_barrier_" + floor; }');
  return lines;
}

module.exports = {
  CORE, PX, PARA, SLAB, RAIL_VIS_H, RAIL_CLIP_TOP, STEPS, TREAD, RISE, PARA_EVERY, FLIGHT_RISE, LAP_RISE,
  DOME_R, DOME_C, DOME_S, DOME_TOP, IN_PAD, OUT_PAD, IN_R3, OUT_R3, BODY_UP, Z_BELOW, Z_ABOVE, C, ARRIVAL, TP_ARRIVE, ARRIVE_RING,
  VOID_H, WALL_T, WALL_IN, OUT, ARCH, PORCH, PORCH_LOW, S_STRIP, HALL_FLOORS, CUT, onFloor, domeZ, domeRAt, insideBody, ceilingAt,
  SPUR_CX, SPUR_PAD_Y, OPENS_SW_LANDING: false,
  FURN, VEND, MIN_TRIG_GAP, PAD_TRIG_GAP, RESPAWN, PYLONS, PYLON_HALF, POST_H, COLLAR_Z, FINS, HALL_RISERS, BEARS, ROOM_RECTS, EXTENT, CHAMBER, PROBE,
  TRENCH, trenchStep, TRENCH_KEEP, MOUTH_LANE, PORCH_LANE, DEBRIS, W_TREAD, ENCLOSE, enclose,
  GUARD_R, GUARD_SPOTS, WAKE_R, WAKE_Z, LEASH_R, LEASH_Z, SIGN, LINER_H, BARRIER, PROJ_RING, PAD_RING, machineBox,
  geometry, barrierBrushes, zoneBrushes, risers, seeds, lights, dataGsc,
};
