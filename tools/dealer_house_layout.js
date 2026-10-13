'use strict';
// THE DEALER'S HOUSE (docs/207, user 2026-10-04): the Battle Arena's LAST level is the
// final fight, and it has two rooms of its own. ONE source for both, like
// tools/battle_arena_layout.js for the arena: the generator emits the geometry, the
// zones + navmesh seeds, the lights / probes and GENERATED _tod_house_data.gsc from
// these numbers, so the script and the map can never drift. Absolute coordinates.
//
// "a separate arena that is even better and slightly bigger than existing one. This is
// the one players will get sent to on battle arena wave 10. The final fight. It starts
// off as player getting sent into a small box with the Black Market as the only thing
// in the center of room. Then a cut scene ... he then teleports the players into the
// new battle arena and gets the players down to one HP with the same effect that the
// evil dome gives ... He talks a bit and then the boss fight starts" + "you need to
// build two more rooms for this" + "He lets you roll one last time and you get a very
// evil bad roll and he laughs like crazy. This is when he teleports you into the final
// fight".
//
//   THE PARLOUR  a small box (704 square, 320 tall) with the Black Market hut at its
//                exact centre and nothing else: the four arrivals stand before the
//                counter, the walls close, one warm pool over the hut. The cut scene,
//                the last roll and the laugh happen here (_tod_house.gsc).
//   THE HOUSE    the final arena: 1920 square (the arena is 1664), 720 tall. THE PIT
//                at z 0 with THE DAIS in its centre (a 384-square top at z 96 on a solid
//                block with a full-width flight of eight risers down EVERY side and the
//                corners open to the pit: every side is a stair, so the Dealer walks up
//                to anyone on it), the RING at z 120 round the walls (an open ledge onto the pit,
//                four pinwheel stairs), four pylons with lit collars (the mood light
//                hosts), four lit GATES in the pit walls (his entrances), the
//                vented roof. Every level is on foot (the arena's rule: a perch the
//                boss cannot reach is a camp). The party lands on the dais top; the
//                corrupted dome rises over the dais for the drain (the field model
//                scaled up, _tod_house.gsc).
// Both rooms are detached islands reached only by script teleport; both sit inside the
// sky seal / umbra volume (asserted by the generator) and far from everything else.
// Labels start `dealer parlour` / `dealer house`: lint_tod_geometry's island buckets,
// the generator's crowding check and tools/test_dealer_house.js's air flood key on them.

const { rotPt, rotRect } = require('./battle_arena_layout.js');

// ---- THE PARLOUR -------------------------------------------------------------
// North-west of the tower, as far out as the arena is south-west (the arena stands at
// (-8000, -8000)); the house is at (8000, -8000).
const PARLOUR = { cx: -8000, cy: 8000, z: 0, half: 352, wall: 20, height: 320 };
// the vented roof (the arena's: a sealed room is INVISIBLE to the occlusion step; a
// 24 slot over the wall tops into a channel under a hanging skirt vents it to the void)
const PVENT = { gap: 24, ch: 64, t: 20, skirtBot: 220 };
const POUTER = PARLOUR.half + PARLOUR.wall + PVENT.ch + PVENT.t;   // 456
const PTOP = PARLOUR.z + PARLOUR.height + PVENT.gap + 20;          // 364
// THE HUT: the shop model at the centre, FRONT = local -Y (the shop's own convention,
// _tod_shop.gsc TOD_SPIN_TRIG_OUT), so yaw 0 faces the arrivals on the south side.
const SHOP = { x: PARLOUR.cx, y: PARLOUR.cy, z: PARLOUR.z, yaw: 0 };
// its collision, the crown shops' own hull list (gen_tower_map.js SHOP_CLIPS), local
// [x1,x2,y1,y2,z1,z2] at yaw 0
const SHOP_HULL = [[-65, 65, -43, 46, 0, 89], [-70, 70, -56, -43, 0, 45], [-97, -70, -27, 33, 19, 79], [69, 94, -29, 0, 24, 77]];
// the four arrivals: a line before the counter, facing it (yaw 90 = +Y)
const P_ARRIVALS = [[-168, -232], [-56, -232], [56, -232], [168, -232]].map(([dx, dy]) => [PARLOUR.cx + dx, PARLOUR.cy + dy, PARLOUR.z]);
const P_ARRIVAL_YAW = 90;
// THE LAST ROLL's use point: the shop's own trigger spot (TOD_SPIN_TRIG_OUT 96 in front of the counter, 40 up)
const P_COUNTER = [PARLOUR.cx, PARLOUR.cy - 96, PARLOUR.z + 40];
// two risers in the back corners (the zone needs spawn structs; nothing ever spawns here)
const P_RISERS = [[-260, 260], [260, 260]].map(([dx, dy]) => [PARLOUR.cx + dx, PARLOUR.cy + dy, PARLOUR.z]);
const P_SEEDS = [[0, -200, 2], [-240, 0, 2], [240, 0, 2], [0, 240, 2]].map(([dx, dy, z]) => [PARLOUR.cx + dx, PARLOUR.cy + dy, PARLOUR.z + z]);

// ---- THE HOUSE ---------------------------------------------------------------
const HOUSE = { cx: 8000, cy: -8000, z: 0, half: 960, wall: 20, height: 720 };
const HVENT = { gap: 24, ch: 64, t: 20, skirtBot: 480 };
const HOUTER = HOUSE.half + HOUSE.wall + HVENT.ch + HVENT.t;   // 1064
const HTOP = HOUSE.z + HOUSE.height + HVENT.gap + 20;          // 764
const SLAB = 16, RISE = 12;        // the tower's slab / riser (consecutive treads overlap 4)
const RING_Z = 120, RD = 192;      // THE RING: 10 risers up, 192 deep
const RI = HOUSE.half - RD;        // 768: the ledge line
// THE DAIS: a DH-square top at DAIS_Z on a solid block, a full-width flight (DAIS_STEPS
// risers of RISE x DAIS_TREAD under a clip slope) down every side, the corners OPEN. It
// was a pyramid of concentric slabs first (2026-10-04 build 1): cod2map's navmesh gave it
// NO polygon above the pit floor, because Havok merges a terrace it can climb from every
// direction into the floor polygon it rises from (a 12-high slab vanishes into the floor;
// a 48-high one is its own island). A flight with OPEN sides is bordered by its drops -
// the arena's dais + spoke grammar - and meshes; proved with cod2map on scratch variants.
const DAIS_STEPS = 8, DAIS_TREAD = 32, DH = 192;
const DAIS_Z = DAIS_STEPS * RISE;                       // 96
const DAIS_FOOT = DH + DAIS_TREAD * (DAIS_STEPS - 1);   // 416: the lowest slab's half
const STAIR = { u: [-480, -352], tread: 24, steps: 10, foot: RI - 240 };   // the pinwheel stair (S-face frame), foot at 528
const PYLON = { at: [-560, -560], hw: 32 };                                // a pylon per quadrant
const GATE_U = 0;                                                          // one gate per wall, centred
const MOOD_Z = 236, MOOD_DAIS_Z = DAIS_Z + 180;
const LEDGE_MAX = 256;             // the deepest open drop (the ring onto the pit is 120)
const FACE = ['S', 'E', 'N', 'W'];

// the four arrivals on the dais top, round the dome's centre, facing out
const H_ARRIVALS = [[-80, -80], [80, -80], [-80, 80], [80, 80]].map(([dx, dy]) => [HOUSE.cx + dx, HOUSE.cy + dy, HOUSE.z + DAIS_Z]);
// his entrances: the gate mouths (and the zone's risers, never used for a horde)
const H_GATES = [0, 1, 2, 3].map(k => { const [x, y] = rotPt(k, GATE_U, -RI + 72); return [HOUSE.cx + x, HOUSE.cy + y, HOUSE.z]; });
const H_MOOD = [0, 1, 2, 3].map(k => { const [x, y] = rotPt(k, PYLON.at[0], PYLON.at[1]); return [HOUSE.cx + x, HOUSE.cy + y, HOUSE.z + MOOD_Z]; });
H_MOOD.push([HOUSE.cx, HOUSE.cy, HOUSE.z + MOOD_DAIS_Z]);   // the dais LAST (the script addresses the last entry)
const H_SEEDS = [[0, 0, DAIS_Z + 2], [0, -600, 2], [600, 0, 2], [0, 600, 2], [-600, 0, 2],
  ...[[-864, -864], [864, -864], [-864, 864], [864, 864], [0, -864], [0, 864], [-864, 0], [864, 0]].map(([x, y]) => [x, y, RING_Z + 2])]
  .map(([dx, dy, z]) => [HOUSE.cx + dx, HOUSE.cy + dy, HOUSE.z + z]);
// one point on every surface the Dealer must reach (lint_tod_navmesh.js: ONE component)
const H_PROBES = [];
for (let k = 0; k < 4; k++) {
  const p = (x, y, z) => { const [a, b] = rotPt(k, x, y); H_PROBES.push([HOUSE.cx + a, HOUSE.cy + b, HOUSE.z + z]); };
  p(-560, -660, 0);                                                     // the quadrant floor, beside the pylon
  p(0, -(HOUSE.half - RD / 2), RING_Z);                                 // the ring, mid-wall
  p(-(HOUSE.half - RD / 2), -(HOUSE.half - RD / 2), RING_Z);            // the ring, corner
  p((STAIR.u[0] + STAIR.u[1]) / 2, -(STAIR.foot + STAIR.tread * STAIR.steps / 2), RING_Z / 2);   // the pinwheel stair, half way
  p(0, -(DH + DAIS_TREAD * 4), RISE * 4);                               // the dais flight, half way up
  p(0, -RI + 72, 0);                                                    // the gate mouth
}
H_PROBES.push([HOUSE.cx, HOUSE.cy, HOUSE.z + DAIS_Z]);

const LIGHT_PIT = '1 0.30 0.22';
const LIGHT_RING = '0.55 0.85 1';
const LIGHT_DAIS = '1 0.78 0.5';
const LIGHT_PARLOUR = '1 0.42 0.36';

// ---- the zones --------------------------------------------------------------
function zones(volumeBrush) {
  for (const [sx, sy, sz] of H_ARRIVALS) for (const [rx, ry, rz] of H_GATES)
    if (Math.abs(sz - rz) < 100 && Math.hypot(sx - rx, sy - ry) < 165)
      throw new Error(`dealer house arrival (${sx},${sy},${sz}) within 165 of a gate riser (${rx},${ry},${rz})`);
  const po = PARLOUR.half + PARLOUR.wall, ho = HOUSE.half + HOUSE.wall;
  return [
    {
      name: 'house_parlour_zone',
      brushes: [volumeBrush(PARLOUR.cx - po, PARLOUR.cx + po, PARLOUR.cy - po, PARLOUR.cy + po, PARLOUR.z - 16, PARLOUR.z + PARLOUR.height)],
      risers: P_RISERS,
      dog: [PARLOUR.cx, PARLOUR.cy + 240, PARLOUR.z],
    },
    {
      name: 'house_zone',
      brushes: [volumeBrush(HOUSE.cx - ho, HOUSE.cx + ho, HOUSE.cy - ho, HOUSE.cy + ho, HOUSE.z - 16, HOUSE.z + HOUSE.height)],
      risers: H_GATES,
      dog: [HOUSE.cx, HOUSE.cy - 600, HOUSE.z],
    },
  ];
}

// ---------------------------------------------------------------------------
// THE ROOMS. E = the generator's emitters (the arena's set): box / bevel / poly /
// rampY / rampX, absolute coordinates, kit roles only. Floors wear DECK roles,
// everything else BLOCK roles (lint_tod_geometry's walkability flood follows them).
// ---------------------------------------------------------------------------
function geometry(E) {
  parlour(E);
  house(E);
}

function parlour(E) {
  const A = PARLOUR, h = A.half, w = A.wall, cx = A.cx, cy = A.cy, z0 = A.z;
  const B = (n, x1, x2, y1, y2, z1, z2, role) => E.box(`dealer parlour ${n}`, cx + x1, cx + x2, cy + y1, cy + y2, z0 + z1, z0 + z2, role);
  const V = (n, x1, x2, y1, y2, z1, z2, role, amt) => E.bevel(`dealer parlour ${n}`, cx + x1, cx + x2, cy + y1, cy + y2, z0 + z1, z0 + z2, role, amt);
  B('floor', -h - w, h + w, -h - w, h + w, -SLAB, 0, 'tower_red_floor');
  B('foundation', -h - w, h + w, -h - w, h + w, -64, -SLAB, 'graphite');
  B('wall N', -h - w, h + w, h, h + w, 0, A.height, 'oxblood');
  B('wall S', -h - w, h + w, -h - w, -h, 0, A.height, 'oxblood');
  B('wall W', -h - w, -h, -h, h, 0, A.height, 'oxblood');
  B('wall E', h, h + w, -h, h, 0, A.height, 'oxblood');
  const O = POUTER, K = h + w + PVENT.ch, cz = A.height + PVENT.gap;
  B('ceiling', -O, O, -O, O, cz, cz + 20, 'ceiling');
  B('skirt N', -O, O, K, O, PVENT.skirtBot, cz, 'graphite');
  B('skirt S', -O, O, -O, -K, PVENT.skirtBot, cz, 'graphite');
  B('skirt W', -O, -K, -K, K, PVENT.skirtBot, cz, 'graphite');
  B('skirt E', K, O, -K, K, PVENT.skirtBot, cz, 'graphite');
  // the dressing: a gold cornice, a cyan seam at head height, bronze pilasters mid-wall, bevelled corner columns
  for (let k = 0; k < 4; k++) {
    const F = FACE[k];
    const RB = (n, x1, x2, y1, y2, z1, z2, role) => { const r = rotRect(k, x1, x2, y1, y2); B(n, r[0], r[1], r[2], r[3], z1, z2, role); };
    const RV = (n, x1, x2, y1, y2, z1, z2, role, amt) => { const r = rotRect(k, x1, x2, y1, y2); V(n, r[0], r[1], r[2], r[3], z1, z2, role, amt); };
    RB(`wall ${F} cornice`, -h, h, -h, -h + 12, A.height - 20, A.height, 'gold');
    RB(`wall ${F} seam`, -h, h, -h, -h + 6, 150, 156, 'cyan');
    RB(`wall ${F} pilaster`, -16, 16, -h, -h + 8, 0, A.height - 20, 'bronze_wall');
    RV(`corner ${F}`, -h, -h + 48, -h, -h + 48, 0, A.height, 'gold', 10);
  }
  // the floor ring round the hut (a 1-unit inlay, walk-over: the pad-ring precedent) and the counter's own mark
  B('ring N', -160, 160, 148, 160, 0, 1, 'gold_line');
  B('ring S', -160, 160, -160, -148, 0, 1, 'gold_line');
  B('ring W', -160, -148, -148, 148, 0, 1, 'gold_line');
  B('ring E', 148, 160, -148, 148, 0, 1, 'gold_line');
  B('counter mark', -40, 40, -112, -80, 0, 1, 'ruby');
  // THE HUT's collision: the shop's own hull list at the parlour's yaw (0: no rotation)
  SHOP_HULL.forEach((b, j) => E.clip(`dealer parlour shop hull ${j}`, SHOP.x + b[0], SHOP.x + b[1], SHOP.y + b[2], SHOP.y + b[3], SHOP.z + b[4], SHOP.z + b[5]));
}

function house(E) {
  const A = HOUSE, h = A.half, w = A.wall, cx = A.cx, cy = A.cy, z0 = A.z;
  const B = (n, x1, x2, y1, y2, z1, z2, role) => E.box(`dealer house ${n}`, cx + x1, cx + x2, cy + y1, cy + y2, z0 + z1, z0 + z2, role);
  const V = (n, x1, x2, y1, y2, z1, z2, role, amt) => E.bevel(`dealer house ${n}`, cx + x1, cx + x2, cy + y1, cy + y2, z0 + z1, z0 + z2, role, amt);
  const RB = (k, n, x1, x2, y1, y2, z1, z2, role) => { const r = rotRect(k, x1, x2, y1, y2); B(n, r[0], r[1], r[2], r[3], z1, z2, role); };
  const RV = (k, n, x1, x2, y1, y2, z1, z2, role, amt) => { const r = rotRect(k, x1, x2, y1, y2); V(n, r[0], r[1], r[2], r[3], z1, z2, role, amt); };
  // a flight in the S-face frame rising toward -y (the arena's helper): the plane through every
  // tread's downhill nosing, feathered onto the lower floor over one tread
  const ramp = (k, n, u1, u2, yNear, yFar, zNear, zFar, tread) => {
    const [x1, x2, y1, y2] = rotRect(k, u1, u2, yFar, yNear);
    const label = `dealer house ${n}`;
    if (k % 2 === 0) {
      const lo = k === 0 ? zFar : zNear, hi = k === 0 ? zNear : zFar;
      E.rampY(label, cx + x1, cx + x2, cy + y1, cy + y2, z0 + lo, z0 + hi, RISE, tread);
    } else {
      const lo = k === 1 ? zNear : zFar, hi = k === 1 ? zFar : zNear;
      E.rampX(label, cy + y1, cy + y2, cx + x1, cx + x2, z0 + lo, z0 + hi, RISE, tread);
    }
  };
  // --- the floor, the shell, the vented roof --------------------------------
  B('floor', -h - w, h + w, -h - w, h + w, -SLAB, 0, 'tower_red_floor');
  B('foundation', -h - w, h + w, -h - w, h + w, -64, -SLAB, 'graphite');
  B('wall N', -h - w, h + w, h, h + w, 0, A.height, 'graphite');
  B('wall S', -h - w, h + w, -h - w, -h, 0, A.height, 'graphite');
  B('wall W', -h - w, -h, -h, h, 0, A.height, 'graphite');
  B('wall E', h, h + w, -h, h, 0, A.height, 'graphite');
  const O = HOUTER, K = h + w + HVENT.ch, cz = A.height + HVENT.gap;
  B('ceiling', -O, O, -O, O, cz, cz + 20, 'ceiling');
  B('skirt N', -O, O, K, O, HVENT.skirtBot, cz, 'graphite');
  B('skirt S', -O, O, -O, -K, HVENT.skirtBot, cz, 'graphite');
  B('skirt W', -O, -K, -K, K, HVENT.skirtBot, cz, 'graphite');
  B('skirt E', K, O, -K, K, HVENT.skirtBot, cz, 'graphite');
  // --- THE DAIS: the top on its block, a full-width flight down every side, open corners ----
  B('dais top', -DH, DH, -DH, DH, DAIS_Z - SLAB, DAIS_Z, 'gold_deck');
  B('dais body', -DH + 4, DH - 4, -DH + 4, DH - 4, 0, DAIS_Z - SLAB, 'oxblood');
  for (let k = 0; k < 4; k++) {
    const F = FACE[k];
    // treads 1..DAIS_STEPS-1 climb toward the centre (+y in the S frame); the top slab is the last level.
    // Tread s: top RISE*s, from y = -(DH + TREAD*(STEPS-s)) (its riser) to y = -(DH + TREAD*(STEPS-1-s)).
    for (let s = 1; s < DAIS_STEPS; s++) {
      const yFar = -(DH + DAIS_TREAD * (DAIS_STEPS - s)), yNear = yFar + DAIS_TREAD, top = RISE * s;
      RB(k, `dais ${F} tread ${s}`, -DH, DH, yFar, yNear, Math.max(0, top - SLAB), top, 'brass');
      if (top - SLAB > 0) RB(k, `dais ${F} fill ${s}`, -DH, DH, yFar, yNear, 0, top - SLAB, 'oxblood');
    }
  }
  // the dais ring round the arrival (walk-over) and the clip slope over each flight. A flight climbs
  // toward +y in the S frame (toward the centre), the arena spokes' direction: the plane passes
  // z0 + RISE*s at tread s's riser (y = -(DH + TREAD*(STEPS-s))), feathered one tread onto the pit, and
  // lands on the top slab's edge (y = -DH, z = DAIS_Z). The flights' sides are open drops onto the pit
  // floor (<= DAIS_Z, inside LEDGE_MAX): that is what gives the navmesh its borders.
  const daisRamp = (k, n, yLow, yHigh, zLow, zHigh) => {
    const [x1, x2, y1, y2] = rotRect(k, -DH, DH, yLow, yHigh);
    const label = `dealer house ${n}`;
    if (k === 0) E.rampY(label, cx + x1, cx + x2, cy + y1, cy + y2, z0 + zLow, z0 + zHigh, RISE, DAIS_TREAD);
    else if (k === 2) E.rampY(label, cx + x1, cx + x2, cy + y1, cy + y2, z0 + zHigh, z0 + zLow, RISE, DAIS_TREAD);
    else if (k === 1) E.rampX(label, cy + y1, cy + y2, cx + x1, cx + x2, z0 + zHigh, z0 + zLow, RISE, DAIS_TREAD);
    else E.rampX(label, cy + y1, cy + y2, cx + x1, cx + x2, z0 + zLow, z0 + zHigh, RISE, DAIS_TREAD);
  };
  for (let k = 0; k < 4; k++) {
    RB(k, `dais ring ${FACE[k]}`, -128, 112, -128, -112, DAIS_Z, DAIS_Z + 1, 'ruby');
    daisRamp(k, `dais ${FACE[k]} ramp`, -(DAIS_FOOT + DAIS_TREAD), -DH, 0, DAIS_Z);
  }
  for (let k = 0; k < 4; k++) {
    const F = FACE[k];
    // --- THE RING (N/S strips own the corners) ------------------------------
    if (k % 2 === 0) {
      RB(k, `ring ${F} body`, -h, h, -h, -RI, 0, RING_Z - SLAB, 'oxblood');
      RB(k, `ring ${F} deck`, -h, h, -h, -RI, RING_Z - SLAB, RING_Z, 'brass');
    } else {
      RB(k, `ring ${F} body`, -RI, RI, -h, -RI, 0, RING_Z - SLAB, 'oxblood');
      RB(k, `ring ${F} deck`, -RI, RI, -h, -RI, RING_Z - SLAB, RING_Z, 'brass');
    }
    RB(k, `ring ${F} band a`, -RI, STAIR.u[0], -RI, -RI + 4, RING_Z - 24, RING_Z - SLAB, 'gold');
    RB(k, `ring ${F} band b`, STAIR.u[1], RI, -RI, -RI + 4, RING_Z - 24, RING_Z - SLAB, 'gold');
    // --- THE GATE: his entrance, a lit frame in the pit wall ---------------
    RB(k, `gate ${F} post a`, GATE_U - 80, GATE_U - 60, -RI, -RI + 6, 0, 120, 'gold');
    RB(k, `gate ${F} post b`, GATE_U + 60, GATE_U + 80, -RI, -RI + 6, 0, 120, 'gold');
    RB(k, `gate ${F} lintel`, GATE_U - 80, GATE_U + 80, -RI, -RI + 6, 104, 120, 'gold');
    for (const b of [-32, 0, 32]) RB(k, `gate ${F} bar ${b}`, GATE_U + b - 4, GATE_U + b + 4, -RI, -RI + 3, 6, 104, 'oxblood');
    RB(k, `gate ${F} mouth`, GATE_U - 60, GATE_U + 60, -RI + 6, -RI + 40, 0, 1, 'gold_line');
    // --- THE PINWHEEL STAIR: pit -> ring --------------------------------------
    for (let s = 1; s <= STAIR.steps; s++) {
      const yNear = -STAIR.foot - STAIR.tread * (s - 1), yFar = yNear - STAIR.tread, top = RISE * s;
      RB(k, `stair ${F} tread ${s}`, STAIR.u[0], STAIR.u[1], yFar, yNear, Math.max(0, top - SLAB), top, 'brass');
      if (top - SLAB > 0) RB(k, `stair ${F} fill ${s}`, STAIR.u[0], STAIR.u[1], yFar, yNear, 0, top - SLAB, 'oxblood');
    }
    ramp(k, `stair ${F} ramp`, STAIR.u[0], STAIR.u[1], -STAIR.foot + STAIR.tread, -STAIR.foot - STAIR.tread * (STAIR.steps - 1), 0, RISE * STAIR.steps, STAIR.tread);
    // --- THE PYLON: floor to wall top, a ruby collar (the mood light host sits over it) --
    RV(k, `pylon ${F}`, PYLON.at[0] - PYLON.hw, PYLON.at[0] + PYLON.hw, PYLON.at[1] - PYLON.hw, PYLON.at[1] + PYLON.hw, 0, A.height, 'graphite', 12);
    RB(k, `pylon ${F} collar`, PYLON.at[0] - PYLON.hw - 4, PYLON.at[0] + PYLON.hw + 4, PYLON.at[1] - PYLON.hw - 4, PYLON.at[1] + PYLON.hw + 4, 196, 212, 'oxblood');   // BLOCK: a ruby collar would read as a floor to the lint
    // --- the walls above the ring: pilasters, a ruby seam, a gold cornice -----
    for (const u of [-640, -384, -128, 128, 384, 640]) RB(k, `wall ${F} pilaster ${u}`, u - 16, u + 16, -h, -h + 8, RING_Z, A.height - 24, 'bronze_wall');
    RB(k, `wall ${F} seam`, -h, h, -h, -h + 6, 330, 336, 'oxblood');
    RB(k, `wall ${F} cornice`, -h, h, -h, -h + 12, A.height - 24, A.height, 'gold');
    RV(k, `corner ${F}`, -h, -h + 64, -h, -h + 64, RING_Z, A.height, 'gold', 10);
  }
}

function lights(light, probe) {
  const P = PARLOUR, LP = (n, x, y, z, c, r) => light(`dealer parlour light ${n}`, P.cx + x, P.cy + y, P.z + z, c, r, 6, 1);
  LP('hut', 0, 0, 250, '1 0.70 0.50', 420);
  for (let k = 0; k < 4; k++) { const [x, y] = rotPt(k, -260, -260); LP(`corner ${FACE[k]}`, x, y, 200, LIGHT_PARLOUR, 300); }
  probe('probe dealer parlour', P.cx, P.cy - 160, P.z + 110);
  const A = HOUSE, L = (n, x, y, z, c, r) => light(`dealer house light ${n}`, A.cx + x, A.cy + y, A.z + z, c, r, 6, 1);
  L('dais', 0, 0, 520, LIGHT_DAIS, 640);
  for (let k = 0; k < 4; k++) {
    const F = FACE[k], p = (x, y) => rotPt(k, x, y);
    L(`pit ${F}`, ...p(-420, -420), 320, LIGHT_PIT, 600);
    L(`ring ${F}`, ...p(0, -(A.half - 96)), 400, LIGHT_RING, 680);
    L(`corner ${F}`, ...p(-(A.half - 128), -(A.half - 128)), 320, LIGHT_PIT, 460);
  }
  probe('probe dealer house', A.cx, A.cy, A.z + 140);
  probe('probe dealer house dais', A.cx, A.cy, A.z + DAIS_Z + 100);
}

// ---------------------------------------------------------------------------
// THE LAYOUT PROVES ITSELF (run at require time by the generator and the gate).
// ---------------------------------------------------------------------------
(function selfCheck() {
  // the parlour: the arrivals before the counter, outside the hut's hull, a body's width apart
  for (const [x, y] of P_ARRIVALS) {
    const dx = x - SHOP.x, dy = y - SHOP.y;
    if (dy > -120) throw new Error('dealer parlour: an arrival stands on the counter');
    if (Math.abs(dx) > PARLOUR.half - 60 || Math.abs(dy) > PARLOUR.half - 60) throw new Error('dealer parlour: an arrival is against a wall');
  }
  for (let i = 1; i < P_ARRIVALS.length; i++) if (P_ARRIVALS[i][0] - P_ARRIVALS[i - 1][0] < 80) throw new Error('dealer parlour: arrivals too close');
  for (const b of SHOP_HULL) if (Math.max(Math.abs(b[0]), Math.abs(b[1]), Math.abs(b[2]), Math.abs(b[3])) > PARLOUR.half - 160) throw new Error('dealer parlour: the hut crowds a wall');
  if (PVENT.gap < 4 || PVENT.gap >= 32 || HVENT.gap < 4 || HVENT.gap >= 32) throw new Error('dealer house: a roof slot must be >= 4 (open air to Umbra) and < 32 (closed to a body)');
  if (PVENT.skirtBot >= PARLOUR.height || HVENT.skirtBot >= HOUSE.height) throw new Error('dealer house: a skirt must hang below its wall top');
  // the house: the dais foot clear of the stairs and the pylons, the stairs meeting the ring, the gates clear of the stairs
  if (DAIS_FOOT + 48 > STAIR.foot) throw new Error('dealer house: the dais flights crowd the pinwheel stairs');
  if (DAIS_FOOT + 48 > Math.abs(PYLON.at[0]) - PYLON.hw) throw new Error('dealer house: the dais flights crowd a pylon');
  if (STAIR.foot + STAIR.tread * STAIR.steps !== RI) throw new Error('dealer house: the pinwheel stair does not meet the ring edge');
  if (RISE * STAIR.steps !== RING_Z) throw new Error('dealer house: the ring height drifted from its stair');
  if (STAIR.u[1] > GATE_U - 80 - 32 && STAIR.u[0] < GATE_U + 80 + 32) throw new Error('dealer house: a pinwheel stair crowds a gate');
  if (Math.abs(PYLON.at[0]) + PYLON.hw > RI - 24) throw new Error('dealer house: a pylon stands in the ring');
  if (STAIR.u[0] < PYLON.at[0] + PYLON.hw + 24 && STAIR.u[1] > PYLON.at[0] - PYLON.hw - 24 && -STAIR.foot < PYLON.at[1] + PYLON.hw + 24) throw new Error('dealer house: a pinwheel stair runs into its pylon');
  if (RING_Z > LEDGE_MAX || DAIS_Z > LEDGE_MAX) throw new Error('dealer house: an open drop deeper than the ledge rule');
  if (DAIS_Z + 72 >= HOUSE.height || RING_Z + 72 >= HOUSE.height) throw new Error('dealer house: the highest eye must stay below the wall top');
  for (const [x, y, z] of H_ARRIVALS) if (z !== HOUSE.z + DAIS_Z || Math.abs(x - HOUSE.cx) > DH - 40 || Math.abs(y - HOUSE.cy) > DH - 40) throw new Error('dealer house: an arrival is off the dais top');
  for (const [x, y] of H_GATES) if (Math.abs(x - HOUSE.cx) >= RI || Math.abs(y - HOUSE.cy) >= RI) throw new Error('dealer house: a gate riser is under the ring');
  if (H_MOOD.length !== 5) throw new Error('dealer house: five mood hosts (four pylons, then the dais)');
})();

// GENERATED _tod_house_data.gsc. `chamber` is the arena chamber (the party leaves from it).
function dataGsc() {
  const v = (p) => `( ${p[0]}, ${p[1]}, ${p[2]} )`;
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
  s.push('// GENERATED by tools/gen_tower_map.js (tools/dealer_house_layout.js) - DO NOT HAND-EDIT (regen instead).');
  s.push("// THE DEALER'S HOUSE (docs/207): the parlour (the Black Market box) and the house (the final arena),");
  s.push('// from the same numbers that cut the brushes.');
  s.push('');
  s.push('#namespace tod_house_data;');
  s.push('');
  s.push('// THE PARLOUR');
  s.push(`function parlour_center()   { return ( ${PARLOUR.cx}, ${PARLOUR.cy}, ${PARLOUR.z} ); }`);
  s.push(`function parlour_half()     { return ${PARLOUR.half}; }`);
  s.push(`function parlour_top()      { return ${PARLOUR.z + PARLOUR.height}; }`);
  s.push('function parlour_zone()     { return "house_parlour_zone"; }');
  s.push(`function parlour_shop_org() { return ( ${SHOP.x}, ${SHOP.y}, ${SHOP.z} ); }`);
  s.push(`function parlour_shop_yaw() { return ${SHOP.yaw}; }`);
  s.push(`function parlour_counter()  { return ${v(P_COUNTER)}; }   // THE LAST ROLL's use point: TOD_SPIN_TRIG_OUT before the counter`);
  s.push(`function parlour_arrival_yaw() { return ${P_ARRIVAL_YAW}; }`);
  arr('parlour_arrivals', P_ARRIVALS, v, '// the four arrivals: a line before the counter, facing it');
  s.push('// PUBLIC: is this position inside the parlour (walls, vented roof and all)?');
  s.push('function in_parlour( org )');
  s.push('{');
  s.push('\tif ( !isdefined( org ) )');
  s.push('\t\treturn false;');
  s.push(`\treturn ( Abs( org[ 0 ] - ( ${PARLOUR.cx} ) ) <= ${POUTER} && Abs( org[ 1 ] - ( ${PARLOUR.cy} ) ) <= ${POUTER} && org[ 2 ] >= ${PARLOUR.z - 128} && org[ 2 ] <= ${PTOP} );`);
  s.push('}');
  s.push('');
  s.push('// THE HOUSE');
  s.push(`function house_center()     { return ( ${HOUSE.cx}, ${HOUSE.cy}, ${HOUSE.z} ); }`);
  s.push(`function house_half()       { return ${HOUSE.half}; }`);
  s.push(`function house_top()        { return ${HOUSE.z + HOUSE.height}; }   // the wall tops: nothing walkable reaches them`);
  s.push(`function house_dais()       { return ( ${HOUSE.cx}, ${HOUSE.cy}, ${HOUSE.z + DAIS_Z} ); }   // the dais top: the arrival, the dome's centre`);
  s.push(`function house_dais_half()  { return ${DH}; }`);
  s.push(`function house_dais_foot()  { return ${DAIS_FOOT}; }   // the flights' lowest riser`);
  s.push(`function house_ring_z()     { return ${HOUSE.z + RING_Z}; }`);
  s.push('function house_zone()       { return "house_zone"; }');
  arr('house_arrivals', H_ARRIVALS, v, '// the four arrivals on the dais top, facing out');
  arr('house_gates', H_GATES, v, "// the four lit gates in the pit walls: the Dealer's entrances (and the zone's risers)");
  arr('house_nav_probes', H_PROBES, v, '// one point on every surface the Dealer must reach (read by tools/lint_tod_navmesh.js only)');
  arr('house_mood_orgs', H_MOOD, v, '// the mood light hosts: a glow host over each pylon collar, the dais LAST');
  s.push('// PUBLIC: is this position inside the house (walls, vented roof and all)? _tod_arena\'s fall guard,');
  s.push('// the ambush / reach / music / tier-floor readers skip a player for whom this is true.');
  s.push('function in_house( org )');
  s.push('{');
  s.push('\tif ( !isdefined( org ) )');
  s.push('\t\treturn false;');
  s.push(`\treturn ( Abs( org[ 0 ] - ( ${HOUSE.cx} ) ) <= ${HOUTER} && Abs( org[ 1 ] - ( ${HOUSE.cy} ) ) <= ${HOUTER} && org[ 2 ] >= ${HOUSE.z - 128} && org[ 2 ] <= ${HTOP} );`);
  s.push('}');
  s.push('// PUBLIC: standing on the dais top (the drain dome stands over it)?');
  s.push('function on_house_dais( org )');
  s.push('{');
  s.push('\tif ( !isdefined( org ) )');
  s.push('\t\treturn false;');
  s.push(`\treturn ( Abs( org[ 0 ] - ( ${HOUSE.cx} ) ) <= ${DH + 16} && Abs( org[ 1 ] - ( ${HOUSE.cy} ) ) <= ${DH + 16} && org[ 2 ] >= ${HOUSE.z + DAIS_Z - 8} && org[ 2 ] <= ${HOUSE.z + DAIS_Z + 96} );`);
  s.push('}');
  s.push('');
  return s.join('\n');
}

module.exports = {
  PARLOUR, PVENT, POUTER, PTOP, SHOP, SHOP_HULL, P_ARRIVALS, P_ARRIVAL_YAW, P_COUNTER, P_RISERS, P_SEEDS,
  HOUSE, HVENT, HOUTER, HTOP, RING_Z, DAIS_Z, DH, DAIS_FOOT, RI, LEDGE_MAX, H_ARRIVALS, H_GATES, H_MOOD, H_SEEDS, H_PROBES,
  zones, geometry, lights, dataGsc,
};
