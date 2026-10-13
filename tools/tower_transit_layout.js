'use strict';
// =============================================================================
// THE DEPARTURE HALL (docs/196) — the top-floor teleporter bay, and the bottom
// return apron. Coordinates are in the crown's odd frame (the generator point-
// mirrors them by CM); the base apron is absolute. The generator emits BOTH the
// runtime route rows and the map markers from this file, so geometry and script
// cannot drift.
//
// User 2026-09-29: "Please redesign the teleporter bay so it looks a lot nicer
// on this map." The 2026-09-27 bay was a plain 840 x 800 box: purple walls, a
// flat ceiling, three pads on coloured mats. The hall is now a CRUCIFORM in the
// crown's own architectural language (cobalt floors, violet panelled walls,
// bevelled ruby piers on gold bases, gold arches, jewel accents):
//
//            N ARM  (GATE 10, cyan floor)
//                 |
//   APSE -- CROSSING -- NAVE -- door -- the terrace (the jump pad lands N of it)
//  (GATE 20,      |
//   green floor,  S ARM  (GATE 30, orange floor)
//   the WINDOW)
//
//  * You enter on axis from the terrace. Straight ahead, through the crossing,
//    the apse's panoramic WINDOW frames the sky's TOWER OF DOOM II sign, which
//    stands due WEST after the sky's -90 roll (the first jump's opening scene
//    looks at the same sign; _tod_jumppad.gsc).
//  * Each gate is its own arm: a floor in the destination district's colour, a
//    gold ring round the pad, a gold floor number in front of it, and a portal
//    on the back wall (bevelled ruby pilasters, a gold arch, a district-colour
//    panel with a lit numeral plaque; the apse's portal frames the window).
//  * The CROSSING: four bevelled ruby piers carry four gold arches; above them
//    an OPEN ROOF — an octagonal gold oculus ring on four struts, with gold ribs
//    cresting every arm — so the sky, the mast and the crown stay in view (the
//    user took the roof off the breather lounges for exactly that).
//  * Underneath: a stepped graphite keel with a ruby pendant, echoing the crown's
//    bell, for everyone who looks up from the spiral or flies past it.
//
// COLLISION / LINT RULES this file keeps (each one load-bearing):
//  * Every walkable surface is an AXIS BOX (the geometry lint only reads boxes
//    as floors; convex brushes are decoration). The pads stand flush on the
//    arm floors (no plinth): the route rows' z is the floor top.
//  * Walls are AXIS BOXES built from one rectilinear outline: horizontal (x)
//    walls own every corner square (extended at convex corners), vertical (y)
//    walls are trimmed at reflex corners — no overlaps, no gaps (asserted).
//  * Windows are real openings with clip_player glazing (bullets pass, players
//    do not), exactly the old bay's "window guard".
//  * Floor markings are 1-unit decals ON TOP of continuous slabs, and no two
//    decals overlap in plan (asserted: coplanar decals would z-fight).
//  * Nothing solid within 84 of a pad centre below 72 up, nothing within the
//    arrival fan-out (test_tower_transit re-proves both from the emitted brushes).
// =============================================================================

const T = 20;                 // wall thickness
const H = 448;                // clear wall height (the cornice sits above)
const NAVE  = {x1:-900,  x2:-500,  y1:180, y2:540};
const CROSS = {x1:-1260, x2:-900,  y1:180, y2:540};
const NARM  = {x1:-1260, x2:-900,  y1:540, y2:900};
const SARM  = {x1:-1260, x2:-900,  y1:-180, y2:180};
const APSE  = {x1:-1620, x2:-1260, y1:180, y2:540};
const DOOR  = {y1:264, y2:456, h:256};   // 192 wide: its 16u gold jambs leave the old 160 clear
// THE WINDOW: the apse's whole back wall above a 56u sill, so the sky's title sign
// (due west, ~6..16 deg up) sits inside it from the door (1150 away: 0..16 deg) and
// from the crossing. Gate 20's slim pilasters stand at its edges.
const APSE_WIN = {y1:204, y2:516, z1:56, z2:396};
const CX = (CROSS.x1 + CROSS.x2) / 2, CY = (CROSS.y1 + CROSS.y2) / 2;   // (-1080, 360): the crossing's centre

// ROOM = the hall's interior bounding box + the door (read by the generator's
// terrace rails, the zone volume, the probe and the nav seeds).
const ROOM = {x1:APSE.x1, x2:NAVE.x2, y1:SARM.y1, y2:NARM.y2, height:H, doorY1:DOOR.y1, doorY2:DOOR.y2};

// Floor 40 carries the BATTLE ARENA chamber instead (docs/185, user 2026-09-27:
// "floor 40 doesnt have a tower teleporter just a chamber"); its slot here is empty.
// Each gate: its pad, its district colour (the floor of its arm, the numeral, the
// gate light), and which way its portal faces (into the crossing).
const PADS = [
  {floor:30, x:CX, y:-40, arm:SARM, face:[0, 1],  floorMat:'tower_orange_floor', panelMat:'bronze_wall', light:'1 0.48 0.14'},
  {floor:20, x:-1480, y:CY, arm:APSE, face:[1, 0], window:true, floorMat:'tower_green_floor', panelMat:'tower_green_wall', light:'0.24 1 0.46'},
  {floor:10, x:CX, y:760, arm:NARM, face:[0, -1], floorMat:'tower_cyan_floor', panelMat:'tower_blue_wall', light:'0.3 0.66 1'},
];
const ARRIVAL = [-620, CY];
const FLOOR_ARRIVE_OFF = 208; // 120 gather + 48 co-op ring + 40 units of clearance
// Risers: in the nave, clear of the piers and >= 165 from the arrival (the
// materialize rule), so the horde comes at the party from the door side.
const RISERS = [[-800, 230], [-800, 490]];
const BASE = {x1:-240,x2:240,y1:-980,y2:-560,pad:[0,-800,0],arrival:[0,-580,0],risers:[[-220,-620,0],[220,-620,0]]};

// Nav seeds: one per floor region (cod2map keeps a region only if it is big or
// seeded — the navmesh-is-seeded-flood lesson).
const SEEDS = [ARRIVAL, [CX, CY], ...PADS.map(p => [p.x + p.face[0] * 150, p.y + p.face[1] * 150])];

// THE LIGHTS (all lightingstate1 = powered; the generator's light()). Colours
// are kept saturated (tools/art_cohesion/tower_lighting.js "transit hall" rule).
const LIGHTS = [
  ...PADS.map(p => ({label:`transit hall gate ${p.floor}`, org:[p.x - p.face[0] * 60, p.y - p.face[1] * 60, 250], color:p.light, radius:300, stops:8.6})),
  {label:'transit hall crossing', org:[CX, CY, 390], color:'1 0.86 0.66', radius:440, stops:8.5},
  {label:'transit hall nave', org:[-700, CY, 320], color:'0.78 0.88 1', radius:380, stops:8.4},
  // the front door, lit from the terrace side so it reads from the jump pad's landing
  {label:'transit hall door', org:[NAVE.x2 + 60, CY, 300], color:'1 0.78 0.46', radius:260, stops:8.2},
];
// THE AMBIENCE (stock looping FX already zoned for the lounges; _tod_atmosphere
// plays them from the generated transit_hall_fx()): motes falling through the
// oculus, a slow haze in the crossing, a curl of wind-fog at the open window.
const FX = [
  {key:'tod_lounge_motes', org:[CX, CY, 430]},
  {key:'tod_lounge_haze',  org:[CX, CY, 110]},
  {key:'tod_lounge_fog',   org:[APSE.x1 + 40, CY, 4]},
];

function routes({top,mirror,spurX,spurY,crown}) {
  const p=(x,y,z=top)=>[mirror*x,mirror*y,z],yaw=a=>(a+(mirror<0?180:0))%360;
  const rows=[];
  for(const pad of PADS) {
    const z=(pad.floor-1)*384+192;
    rows.push({id:`top_to_${pad.floor}`,src:p(pad.x,pad.y),src_yaw:yaw(0),
      dst:[-spurX,-spurY+FLOOR_ARRIVE_OFF,z],dst_yaw:90,lock:`enter_lap${pad.floor+1}`,
      zone:`lap${pad.floor}_zone`,hint:`down to FLOOR ${pad.floor}`,arrival_flag:'',return_crown:false});
    rows.push({id:`floor_${pad.floor}_to_top`,src:[-spurX,-spurY,z],src_yaw:0,
      dst:p(...ARRIVAL),dst_yaw:yaw(0),lock:'',zone:'roof_zone',hint:'up to the TOP BAY',arrival_flag:'',return_crown:false});
  }
  rows.push({id:'base_to_crown',src:BASE.pad,src_yaw:90,
    dst:p(crown[0]+160,crown[1]+100),dst_yaw:yaw(0),lock:'',zone:'crown_zone',
    hint:'up to the CROWN',arrival_flag:'tod_crown_tele',return_crown:true});
  rows.push({id:'crown_to_base',src:p(...crown),src_yaw:yaw(0),
    dst:BASE.arrival,dst_yaw:90,lock:'enter_lap1',zone:'base_zone',hint:'down to the GROUND FLOOR',arrival_flag:'',return_crown:false});
  return rows;
}

// ---------------------------------------------------------------------------
// The hall. `k` = the generator's emitters, all in the odd frame, z relative
// to the floor top z0:  k.box(label,x1,x2,y1,y2,z1,z2,mat)       axis box
//                       k.poly(label,vertices,faces,mat)           convex solid
//                       k.bevel(label,x1,x2,y1,y2,z1,z2,mat,amt)  chamfered box
// Every label starts "transit bay " (the transit gate's texture-scale check).
// ---------------------------------------------------------------------------
function roof(k, z0) {
  const kit = n => 'tod_cc_' + n;
  const B = (n, x1, x2, y1, y2, z1, z2, mat) => {
    if (!(x1 < x2 && y1 < y2 && z1 < z2)) throw new Error(`transit hall: degenerate box "${n}" ${[x1, x2, y1, y2, z1, z2]}`);
    k.box('transit bay ' + n, x1, x2, y1, y2, z0 + z1, z0 + z2, mat.startsWith('clip') ? mat : kit(mat));
  };
  const P = (n, verts, faces, mat) => k.poly('transit bay ' + n, verts.map(([x, y, z]) => [x, y, z0 + z]), faces, kit(mat));
  const V = (n, x1, x2, y1, y2, z1, z2, mat, amt) => k.bevel('transit bay ' + n, x1, x2, y1, y2, z0 + z1, z0 + z2, kit(mat), amt);

  // ---- FLOORS: continuous slabs, one per region; each arm in its gate's colour.
  // The E-W bar (apse + crossing + nave + the door threshold) is split so the apse
  // can wear its gate colour; slabs run under the walls (walls stand on them).
  B('floor apse',     APSE.x1 - T, APSE.x2, APSE.y1 - T, APSE.y2 + T, -16, 0, PADS[1].floorMat);
  B('floor crossing', CROSS.x1, CROSS.x2, CROSS.y1, CROSS.y2, -16, 0, 'floor');
  B('floor nave',     NAVE.x1, NAVE.x2 + T, NAVE.y1 - T, NAVE.y2 + T, -16, 0, 'floor');
  B('floor north arm', NARM.x1 - T, NARM.x2 + T, NARM.y1, NARM.y2 + T, -16, 0, PADS[2].floorMat);
  B('floor south arm', SARM.x1 - T, SARM.x2 + T, SARM.y1 - T, SARM.y2, -16, 0, PADS[0].floorMat);
  // (the crossing's own slab stops at its four sides; the arm and apse slabs meet it flush)
  for (const [n, r] of [['apse', APSE], ['north arm', NARM], ['south arm', SARM], ['nave', NAVE]]) {
    const pad = 12;
    B(`foundation ${n}`, r.x1 - T + pad, r.x2 + T - pad, r.y1 - T + pad, r.y2 + T - pad, -64, -16, 'graphite');
  }
  B('foundation crossing', CROSS.x1, CROSS.x2, CROSS.y1, CROSS.y2, -64, -16, 'graphite');

  // ---- WALLS from ONE rectilinear outline (counter-clockwise, interior on the left).
  const outline = [
    [NAVE.x2, NAVE.y1], [NAVE.x2, NAVE.y2],          // east (the door)
    [NAVE.x1, NAVE.y2], [NARM.x2, NARM.y2],          // nave north, north arm east
    [NARM.x1, NARM.y2], [NARM.x1, NARM.y1],          // north arm back (GATE 10), north arm west
    [APSE.x1, APSE.y2], [APSE.x1, APSE.y1],          // apse north, apse back (GATE 20 + the window)
    [SARM.x1, SARM.y2], [SARM.x1, SARM.y1],          // apse south, south arm west
    [SARM.x2, SARM.y1], [SARM.x2, SARM.y2],          // south arm back (GATE 30), south arm east
  ];                                                  // ... then nave south back to the start
  // openings per edge: {a0,a1: the span along the edge's own axis, z1,z2}
  const WIN = (c, w = 96) => ({a0:c - w / 2, a1:c + w / 2, z1:96, z2:336, win:true});
  const openings = {
    '0': [{a0:DOOR.y1, a1:DOOR.y2, z1:0, z2:DOOR.h, door:true}],
    '1': [WIN(-780), WIN(-620)],                              // nave north: the crown side
    '2': [WIN(PADS[2].y)],                                    // north arm east, beside gate 10
    '4': [WIN(PADS[2].y)],                                    // north arm west
    '5': [WIN(PADS[1].x)],                                    // apse north, beside gate 20
    '6': [{a0:APSE_WIN.y1, a1:APSE_WIN.y2, z1:APSE_WIN.z1, z2:APSE_WIN.z2, win:true, big:true}],   // THE WINDOW (the sign, due west)
    '7': [WIN(PADS[1].x)],                                    // apse south
    '8': [WIN(PADS[0].y)],                                    // south arm west, beside gate 30
    '10': [WIN(PADS[0].y)],                                   // south arm east
    '11': [WIN(-780), WIN(-620)],                             // nave south
  };   // e3 and e9 are gate 10's and gate 30's back walls: no windows there
  const n = outline.length, wallBoxes = [];
  const signedArea = outline.reduce((s, [x, y], i) => { const [x2, y2] = outline[(i + 1) % n]; return s + x * y2 - x2 * y; }, 0);
  if (signedArea <= 0) throw new Error('transit hall outline must be counter-clockwise');
  const cross = (a, b) => a[0] * b[1] - a[1] * b[0];
  for (let i = 0; i < n; i++) {
    const A = outline[i], Bp = outline[(i + 1) % n], Pp = outline[(i - 1 + n) % n], Nn = outline[(i + 2) % n];
    const d = [Math.sign(Bp[0] - A[0]), Math.sign(Bp[1] - A[1])];
    const out = [d[1], -d[0]];                                   // interior on the LEFT -> outward is the right-hand normal
    const horiz = d[1] === 0;
    const convexAt = (prev, cur, next) => cross([cur[0] - prev[0], cur[1] - prev[1]], [next[0] - cur[0], next[1] - cur[1]]) > 0;
    const cA = convexAt(Pp, A, Bp), cB = convexAt(A, Bp, Nn);
    // span along the edge axis
    let s0 = horiz ? A[0] : A[1], s1 = horiz ? Bp[0] : Bp[1];
    const dirSign = horiz ? d[0] : d[1];
    // corner ownership: horizontal walls extend T at convex corners; vertical walls trim T at reflex corners
    if (horiz) { if (cA) s0 -= dirSign * T; if (cB) s1 += dirSign * T; }
    else { if (!cA) s0 += dirSign * T; if (!cB) s1 -= dirSign * T; }
    const lo = Math.min(s0, s1), hi = Math.max(s0, s1);
    const fixed = horiz ? A[1] : A[0];
    const t0 = out[horiz ? 1 : 0] > 0 ? fixed : fixed - T, t1 = t0 + T;
    const ops = (openings[String(i)] || []).slice().sort((a, b) => a.a0 - b.a0);
    for (const o of ops) if (o.a0 < lo + 8 || o.a1 > hi - 8) throw new Error(`transit hall: opening on wall ${i} runs into a corner`);
    const box = (label, a0, a1, z1, z2, mat) => {
      if (a1 <= a0 || z2 <= z1) return;
      if (horiz) B(label, a0, a1, t0, t1, z1, z2, mat); else B(label, t0, t1, a0, a1, z1, z2, mat);
      wallBoxes.push({i, a0, a1, z1, z2, horiz, t0, t1});
    };
    // the wall's own layered skin (flush layers, so corners stay consistent):
    // graphite skirting, violet panels, a gold head line level with the gate capitals, violet
    const layers = [[0, 20, 'graphite'], [20, 336, 'wall'], [336, 344, 'gold'], [344, H, 'wall']];
    const solid = (a0, a1, z1, z2, tag) => {
      for (const [l0, l1, mat] of layers) box(`wall ${i} ${tag} ${l0}`, a0, a1, Math.max(z1, l0), Math.min(z2, l1), mat);
    };
    let cur = lo;
    for (const o of ops) {
      solid(cur, o.a0, 0, H, `run ${cur}`);
      // the opening: sill below, head above, a gold frame round it, glazing in it
      solid(o.a0, o.a1, 0, o.z1, `sill ${o.a0}`);
      solid(o.a0, o.a1, o.z2, H, `head ${o.a0}`);
      const f = o.door ? 16 : 10;
      box(`frame ${i} ${o.a0} jamb a`, o.a0, o.a0 + f, o.z1, o.z2, 'gold');
      box(`frame ${i} ${o.a0} jamb b`, o.a1 - f, o.a1, o.z1, o.z2, 'gold');
      box(`frame ${i} ${o.a0} head`, o.a0 + f, o.a1 - f, o.z2 - f, o.z2, 'gold');
      if (!o.door) {
        box(`frame ${i} ${o.a0} sill`, o.a0 + f, o.a1 - f, o.z1, o.z1 + f, 'gold');
        const g0 = o.a0 + f, g1 = o.a1 - f;
        if (horiz) k.box(`transit bay window guard ${i} ${o.a0}`, g0, g1, t0, t1, z0 + o.z1 + f, z0 + o.z2 - f, 'clip_player');
        else k.box(`transit bay window guard ${i} ${o.a0}`, t0, t1, g0, g1, z0 + o.z1 + f, z0 + o.z2 - f, 'clip_player');
      }
      cur = o.a1;
    }
    solid(cur, hi, 0, H, `run ${cur}`);
    // cornice: a gold band on the wall head
    // (BLOCK-class kit materials only above the floor: the geometry lint reads a
    // thin DECK-class slab — brass, gold_line, the crystals — as a floor to stand on)
    box(`cornice ${i}`, lo, hi, H, H + 20, 'gold');
    box(`cornice ${i} crest`, lo, hi, H + 20, H + 28, 'bronze_wall');
  }
  // no two wall boxes of different walls may overlap (corner ownership proven)
  for (let a = 0; a < wallBoxes.length; a++) for (let b = a + 1; b < wallBoxes.length; b++) {
    const p = wallBoxes[a], q = wallBoxes[b];
    if (p.i === q.i) continue;
    const r = w => w.horiz ? [w.a0, w.a1, w.t0, w.t1] : [w.t0, w.t1, w.a0, w.a1];
    const [px1, px2, py1, py2] = r(p), [qx1, qx2, qy1, qy2] = r(q);
    if (px1 < qx2 && qx1 < px2 && py1 < qy2 && qy1 < py2 && p.z1 < q.z2 && q.z1 < p.z2)
      throw new Error(`transit hall: wall ${p.i} and wall ${q.i} overlap`);
  }

  // ---- THE DOOR from the terrace: a jewelled keystone over the gold-framed opening.
  V('door keystone', NAVE.x2 - 12, NAVE.x2, CY - 20, CY + 20, DOOR.h - 16, DOOR.h + 36, 'ruby', 5);
  // ... and its face on the TERRACE: ruby pilasters either side on gold bases, a
  // gold plate and a keystone over the opening (the hall's front door, seen from
  // the jump pad's landing).
  const XO = NAVE.x2 + T;                                        // the east wall's outer face (the terrace edge)
  for (const [n, y0, y1] of [['south', DOOR.y1 - 30, DOOR.y1 - 6], ['north', DOOR.y2 + 6, DOOR.y2 + 30]]) {
    B(`door pilaster base ${n}`, XO, XO + 16, y0 - 4, y1 + 4, 0, 18, 'gold');
    V(`door pilaster ${n}`, XO, XO + 12, y0, y1, 18, DOOR.h + 24, 'oxblood', 4);
    B(`door pilaster capital ${n}`, XO, XO + 16, y0 - 4, y1 + 4, DOOR.h + 24, DOOR.h + 40, 'gold');
  }
  B('door plate', XO, XO + 6, DOOR.y1 - 34, DOOR.y2 + 34, DOOR.h + 40, DOOR.h + 64, 'gold');
  V('door keystone out', XO, XO + 12, CY - 20, CY + 20, DOOR.h - 16, DOOR.h + 36, 'ruby', 5);

  // ---- THE CROSSING: four bevelled ruby piers on gold bases, gold capitals.
  const piers = [[CROSS.x1, CROSS.y1], [CROSS.x2, CROSS.y1], [CROSS.x1, CROSS.y2], [CROSS.x2, CROSS.y2]];
  for (const [px, py] of piers) {
    B(`pier base ${px} ${py}`, px - 34, px + 34, py - 34, py + 34, 0, 22, 'gold');
    V(`pier shaft ${px} ${py}`, px - 28, px + 28, py - 28, py + 28, 22, 312, 'oxblood', 10);
    B(`pier capital ${px} ${py}`, px - 34, px + 34, py - 34, py + 34, 312, 336, 'gold');
  }
  // four gold arches over the crossing's four openings, springing from the capitals
  arch(P, 'crossing arch north', 'x', CROSS.x1, CROSS.x2, CROSS.y2, 32, 336, 84, 26, 'gold', 9);
  arch(P, 'crossing arch south', 'x', CROSS.x1, CROSS.x2, CROSS.y1, 32, 336, 84, 26, 'gold', 9);
  arch(P, 'crossing arch west',  'y', CROSS.y1, CROSS.y2, CROSS.x1, 32, 336, 84, 26, 'gold', 9);
  arch(P, 'crossing arch east',  'y', CROSS.y1, CROSS.y2, CROSS.x2, 32, 336, 84, 26, 'gold', 9);
  // THE OCULUS: an octagonal gold ring over the crossing on four struts from the pier tops
  const RO = 150, RI = 118, RZ1 = 470, RZ2 = 492;
  ring(P, 'oculus', CX, CY, RI, RO, RZ1, RZ2, 8, Math.PI / 8 * 0, 'gold');
  for (const [px, py] of piers) {
    const ang = Math.atan2(py - CY, px - CX), dx = Math.cos(ang), dy = Math.sin(ang), nx = -dy, ny = dx, w = 11;
    const rOut = Math.hypot(px - CX, py - CY), rIn = RO - 6;
    const pt = (r, s, z) => [CX + dx * r + nx * s, CY + dy * r + ny * s, z];
    P(`oculus strut ${px} ${py}`, [pt(rOut, -w, 336), pt(rOut, w, 336), pt(rOut, w, 364), pt(rOut, -w, 364),
      pt(rIn, -w, RZ1), pt(rIn, w, RZ1), pt(rIn, w, RZ2 + 6), pt(rIn, -w, RZ2 + 6)], HEX, 'gold');
  }
  // four jewels on the ring's axis points: the destinations' colours + the door's gold
  for (const [ax, ay, mat] of [[0, -1, 'bronze_wall'], [-1, 0, 'emerald'], [0, 1, 'sapphire'], [1, 0, 'ruby']]) {
    const jx = CX + ax * (RO + RI) / 2, jy = CY + ay * (RO + RI) / 2;
    V(`oculus jewel ${ax} ${ay}`, jx - 14, jx + 14, jy - 14, jy + 14, RZ2, RZ2 + 22, mat, 6);
  }
  // a gold cross spanning the ring, and a ruby lantern hanging from its crossing on a brass rod
  B('oculus bar x', CX - RO, CX + RO, CY - 5, CY + 5, RZ1 + 4, RZ2 - 4, 'gold');
  B('oculus bar y', CX - 5, CX + 5, CY - RO, CY - 5, RZ1 + 4, RZ2 - 4, 'gold');
  B('oculus bar y2', CX - 5, CX + 5, CY + 5, CY + RO, RZ1 + 4, RZ2 - 4, 'gold');
  B('oculus rod', CX - 3, CX + 3, CY - 3, CY + 3, 406, RZ1 + 4, 'gold');
  octa(P, 'oculus lantern', CX, CY, 384, 30, 22, 'ruby');

  // ---- THE RIBS: gold arches cresting each arm (the open roof's skeleton)
  arch(P, 'rib nave east', 'y', NAVE.y1, NAVE.y2, -620, 24, H, 64, 20, 'gold', 7, true);
  arch(P, 'rib nave west', 'y', NAVE.y1, NAVE.y2, -780, 24, H, 64, 20, 'gold', 7, true);
  arch(P, 'rib north arm', 'x', NARM.x1, NARM.x2, PADS[2].y, 24, H, 64, 20, 'gold', 7, true);
  arch(P, 'rib south arm', 'x', SARM.x1, SARM.x2, PADS[0].y, 24, H, 64, 20, 'gold', 7, true);
  arch(P, 'rib apse', 'y', APSE.y1, APSE.y2, PADS[1].x, 24, H, 64, 20, 'gold', 7, true);

  // ---- THE GATES: a portal on each arm's back wall facing the crossing.
  const decals = [];
  for (const pad of PADS) gate(pad);
  function gate(pad) {
    const [fx, fy] = pad.face;                    // unit vector from the back wall toward the crossing
    const horizWall = fx === 0;                   // back wall runs along x (the N and S arms)
    const wallFace = horizWall ? (fy > 0 ? pad.arm.y1 : pad.arm.y2) : (fx > 0 ? pad.arm.x1 : pad.arm.x2);
    const along = horizWall ? pad.x : pad.y;      // the portal's centre along the wall
    const D = 36;                                 // pilaster depth off the wall
    const into = (a, b) => [wallFace + (horizWall ? fy : fx) * a, wallFace + (horizWall ? fy : fx) * b].sort((p, q) => p - q);
    const rect = (a0, a1, d0, d1, z1, z2, mat, n, bevel) => {
      const [q0, q1] = into(d0, d1);
      if (horizWall) { if (bevel) V(n, a0, a1, q0, q1, z1, z2, mat, bevel); else B(n, a0, a1, q0, q1, z1, z2, mat); }
      else { if (bevel) V(n, q0, q1, a0, a1, z1, z2, mat, bevel); else B(n, q0, q1, a0, a1, z1, z2, mat); }
    };
    const tag = `gate ${pad.floor}`;
    if (pad.window) {
      // THE WINDOW GATE: slim pilasters at the window's edges, a gold lintel from
      // capital to capital over it, and the gate's jewel on the lintel.
      const off = (APSE_WIN.y2 - APSE_WIN.y1) / 2 + 12;
      for (const s of [-1, 1]) {
        const c = along + s * off;
        rect(c - 16, c + 16, 0, 34, 0, 24, 'gold', `${tag} pilaster base ${s}`);
        rect(c - 12, c + 12, 0, 30, 24, APSE_WIN.z2, 'oxblood', `${tag} pilaster ${s}`, 5);
      }
      rect(along - off - 16, along + off + 16, 0, 34, APSE_WIN.z2, APSE_WIN.z2 + 24, 'gold', `${tag} lintel`);
      rect(along - 16, along + 16, 0, 40, APSE_WIN.z2 + 6, APSE_WIN.z2 + 40, 'emerald', `${tag} jewel`, 6);
    } else {
      for (const s of [-1, 1]) {
        const c = along + s * 140;
        rect(c - 26, c + 26, 0, D + 6, 0, 24, 'gold', `${tag} pilaster base ${s}`);
        rect(c - 20, c + 20, 0, D, 24, 320, 'oxblood', `${tag} pilaster ${s}`, 7);
        rect(c - 26, c + 26, 0, D + 6, 320, 344, 'gold', `${tag} pilaster capital ${s}`);
      }
      // the gold arch over the pilasters
      const [q0, q1] = into(0, D);
      arch(P, `${tag} arch`, horizWall ? 'x' : 'y', along - 140, along + 140, (q0 + q1) / 2, D, 344, 64, 28, 'gold', 9);
    }
    if (!pad.window) {
      // the district-colour panel inside the portal, and its numeral plaque
      rect(along - 116, along + 116, 0, 8, 24, 344, pad.panelMat, `${tag} panel`);
      rect(along - 64, along + 64, 8, 14, 214, 318, 'graphite', `${tag} plaque`);
      rect(along - 70, along + 70, 8, 12, 208, 214, 'gold', `${tag} plaque sill`);
      rect(along - 70, along + 70, 8, 12, 318, 324, 'gold', `${tag} plaque head`);
      // the numerals, read by a player facing the wall (u = the viewer's right)
      const right = horizWall ? [-fy, 0] : [0, fx];   // facing (-fx,-fy): right-hand = rotate facing clockwise
      digits(String(pad.floor), (u, v, du, dv, n) => {
        const a0 = along + right[horizWall ? 0 : 1] * u, a1 = along + right[horizWall ? 0 : 1] * (u + du);
        rect(Math.min(a0, a1), Math.max(a0, a1), 14, 18, 228 + v, 228 + v + dv, 'gold', `${tag} numeral ${n}`);
      }, 32, 76, 8, 16);
    }
    // FLOOR: a gold ring round the pad, and the gate's number on the approach
    decals.push({n:`${tag} ring`, c:[pad.x, pad.y], r:106});
    ring(P, `${tag} ring`, pad.x, pad.y, 96, 106, 0, 1, 12, 0, 'gold_line');
    const fwd = pad.face;
    const walkDir = [-fwd[0], -fwd[1]], rightHand = [walkDir[1], -walkDir[0]];
    const numCenter = [pad.x + fwd[0] * 190, pad.y + fwd[1] * 190];   // on the approach: ring edge 106 + 12 clear + a 72-long numeral
    digits(String(pad.floor), (u, v, du, dv, n) => {
      // u along the reader's right, v along the reader's walking direction ("up" on the floor)
      const p0 = [numCenter[0] + rightHand[0] * u + walkDir[0] * v, numCenter[1] + rightHand[1] * u + walkDir[1] * v];
      const p1 = [numCenter[0] + rightHand[0] * (u + du) + walkDir[0] * (v + dv), numCenter[1] + rightHand[1] * (u + du) + walkDir[1] * (v + dv)];
      const x1 = Math.min(p0[0], p1[0]), x2 = Math.max(p0[0], p1[0]), y1 = Math.min(p0[1], p1[1]), y2 = Math.max(p0[1], p1[1]);
      B(`${tag} floor numeral ${n}`, x1, x2, y1, y2, 0, 1, 'gold_line');
      decals.push({n:`${tag} floor numeral ${n}`, box:[x1, x2, y1, y2]});
    }, 40, 72, 10, 16);
  }

  // ---- THE MEDALLION at the crossing's centre + the door's axis lines
  ring(P, 'medallion', CX, CY, 104, 120, 0, 1, 12, 0, 'gold_line');
  decals.push({n:'medallion', c:[CX, CY], r:120});
  for (const dy of [-26, 26]) {
    B(`axis line ${dy}`, CX + 124, NAVE.x2 - 12, CY + dy - 4, CY + dy + 4, 0, 1, 'gold_line');
    decals.push({n:`axis line ${dy}`, box:[CX + 124, NAVE.x2 - 12, CY + dy - 4, CY + dy + 4]});
  }
  // decals must never overlap in plan (coplanar 1u tops would z-fight)
  const bb = d => d.box || [d.c[0] - d.r, d.c[0] + d.r, d.c[1] - d.r, d.c[1] + d.r];
  for (let a = 0; a < decals.length; a++) for (let b = a + 1; b < decals.length; b++) {
    const p = decals[a], q = decals[b];
    if (p.n.split(' floor numeral')[0] === q.n.split(' floor numeral')[0] && p.box && q.box) continue;   // a numeral's own segments are gapped by construction
    const [px1, px2, py1, py2] = bb(p), [qx1, qx2, qy1, qy2] = bb(q);
    if (px1 < qx2 && qx1 < px2 && py1 < qy2 && qy1 < py2) throw new Error(`transit hall: floor decals "${p.n}" and "${q.n}" overlap`);
  }

  // ---- UNDERNEATH: a stepped graphite keel under the crossing, a gold band,
  // and a ruby pendant (the crown's bell, in miniature); ribs under the arms.
  V('keel tier 1', CX - 176, CX + 176, CY - 176, CY + 176, -112, -64, 'graphite', 16);
  B('keel band', CX - 150, CX + 150, CY - 150, CY + 150, -122, -112, 'gold');
  V('keel tier 2', CX - 120, CX + 120, CY - 120, CY + 120, -176, -122, 'graphite', 14);
  V('keel tier 3', CX - 64, CX + 64, CY - 64, CY + 64, -224, -176, 'oxblood', 10);
  octa(P, 'keel pendant', CX, CY, -262, 44, 38, 'ruby');
  for (const [n, r, along] of [['north arm', NARM, 'y'], ['south arm', SARM, 'y'], ['apse', APSE, 'x'], ['nave', NAVE, 'x']])
    for (const f of [0.3, 0.7]) {
      if (along === 'y') { const y = r.y1 + (r.y2 - r.y1) * f; B(`underside rib ${n} ${f}`, r.x1 + 24, r.x2 - 24, y - 16, y + 16, -104, -64, 'graphite'); }
      else { const x = r.x1 + (r.x2 - r.x1) * f; B(`underside rib ${n} ${f}`, x - 16, x + 16, r.y1 + 24, r.y2 - 24, -104, -64, 'graphite'); }
    }
}

// A convex hexahedron's six faces (vertex order: 0-3 one end, 4-7 the other, same winding).
const HEX = [[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]];

// A segmental arch of K convex segments. It spans `axis` ('x' or 'y') from s0 to s1,
// centred on the perpendicular coordinate p with depth dep, springing at zs, rising R,
// radial thickness t.
function arch(P, label, axis, s0, s1, p, dep, zs, R, t, mat, K, noSpringers) {
  const S = s1 - s0, m = (s0 + s1) / 2, r = (S * S / 4 + R * R) / (2 * R), zc = zs + R - r, th = Math.asin((S / 2) / r);
  const pt = (s, z, q) => axis === 'x' ? [s, q, z] : [q, s, z];
  for (let i = 0; i < K; i++) {
    const a0 = -th + 2 * th * i / K, a1 = -th + 2 * th * (i + 1) / K;
    const In = a => [m + r * Math.sin(a), zc + r * Math.cos(a)], Out = a => [m + (r + t) * Math.sin(a), zc + (r + t) * Math.cos(a)];
    const q0 = p - dep / 2, q1 = p + dep / 2;
    const ring4 = q => [pt(...In(a0), q), pt(...In(a1), q), pt(...Out(a1), q), pt(...Out(a0), q)];
    P(`${label} ${i + 1}`, [...ring4(q0), ...ring4(q1)], HEX, mat);
  }
  // springers: a block under each foot, so the radial cut never floats off its capital
  // (a rib that springs from the cornice has the cornice under it instead)
  if (noSpringers) return;
  for (const [s, side] of [[s0, 'a'], [s1, 'b']]) {
    const reach = t * Math.sin(th) + 4, lo = Math.min(s, s + (s === s0 ? -1 : 1) * reach), hi = Math.max(s, s + (s === s0 ? -1 : 1) * reach);
    const a = Math.min(lo, s + (s === s0 ? 1 : -1) * 6), b = Math.max(hi, s + (s === s0 ? 1 : -1) * 6);
    const q0 = p - dep / 2, q1 = p + dep / 2, z2 = zs + t * Math.cos(th);
    const v = [pt(a, zs, q0), pt(b, zs, q0), pt(b, z2, q0), pt(a, z2, q0), pt(a, zs, q1), pt(b, zs, q1), pt(b, z2, q1), pt(a, z2, q1)];
    P(`${label} springer ${side}`, v, HEX, mat);
  }
}

// An N-gon ring (convex trapezoid prisms) centred (cx,cy), radii ri..ro, z1..z2.
function ring(P, label, cx, cy, ri, ro, z1, z2, N, rot, mat) {
  for (let i = 0; i < N; i++) {
    const a0 = rot + 2 * Math.PI * i / N, a1 = rot + 2 * Math.PI * (i + 1) / N;
    const at = (r, a, z) => [cx + r * Math.cos(a), cy + r * Math.sin(a), z];
    const rin = ri / Math.cos(Math.PI / N) * 1, rout = ro / Math.cos(Math.PI / N) * 1;   // apothem = the given radius
    P(`${label} ${i + 1}`, [at(rin, a0, z1), at(rout, a0, z1), at(rout, a1, z1), at(rin, a1, z1),
                            at(rin, a0, z2), at(rout, a0, z2), at(rout, a1, z2), at(rin, a1, z2)], HEX, mat);
  }
}

// An octahedral jewel (8 faces), centre z, half-width w, half-height h.
function octa(P, label, cx, cy, cz, w, h, mat) {
  const v = [[cx + w, cy, cz], [cx, cy + w, cz], [cx - w, cy, cz], [cx, cy - w, cz], [cx, cy, cz + h], [cx, cy, cz - h]];
  P(label, v, [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4], [1, 0, 5], [2, 1, 5], [3, 2, 5], [0, 3, 5]], mat);
}

// Seven-segment numerals. emit(u, v, du, dv, name) is called once per lit segment in a
// local frame: u = the reader's right, v = up; the whole string is centred on u = 0,
// v runs 0..h. w = digit width, h = height, s = stroke, gap = between digits.
function digits(str, emit, w, h, s, gap) {
  const SEG = {'0':'abcdef', '1':'bc', '2':'abged', '3':'abgcd'};
  const total = str.length * w + (str.length - 1) * gap, g = 2;
  for (let i = 0; i < str.length; i++) {
    const u0 = -total / 2 + i * (w + gap), segs = SEG[str[i]];
    if (!segs) throw new Error(`transit hall: no numeral shape for "${str[i]}"`);
    const R = {
      a: [u0 + g, h - s, w - 2 * g, s], d: [u0 + g, 0, w - 2 * g, s], g: [u0 + g, (h - s) / 2, w - 2 * g, s],
      f: [u0, (h + s) / 2 + g, s, (h - s) / 2 - s - 2 * g], e: [u0, s + g, s, (h - s) / 2 - s - 2 * g],
      b: [u0 + w - s, (h + s) / 2 + g, s, (h - s) / 2 - s - 2 * g], c: [u0 + w - s, s + g, s, (h - s) / 2 - s - 2 * g],
    };
    for (const c of segs) emit(R[c][0], R[c][1], R[c][2], R[c][3], `${i}${c}`);
  }
}

function base(box, railH = 56, capTop = 168) {   // railH/capTop from the generator (RAIL_VIS_H, 2026-09-29): a lowered rail's clip starts at the floor
  const r=BASE,b=(n,x1,x2,y1,y2,z1,z2,mat)=>box('transit return '+n,x1,x2,y1,y2,z1,z2,'tod_cc_'+mat);
  b('floor',r.x1-20,r.x2+20,r.y1-20,r.y2,-16,0,'floor');
  for(const [name,x1,x2,y1,y2] of [['W',r.x1-20,r.x1,r.y1-20,r.y2],
    ['E',r.x2,r.x2+20,r.y1-20,r.y2],['S',r.x1,r.x2,r.y1-20,r.y1]]) {
    b('rail '+name,x1,x2,y1,y2,0,railH,'gold');
    box('transit return rail cap '+name,x1,x2,y1,y2,(railH<56?0:56),capTop,'clip');
  }
  b('pad inset',-88,88,r.pad[1]-88,r.pad[1]+88,0,1,'gold_deck');
}
module.exports={ROOM,PADS,ARRIVAL,FLOOR_ARRIVE_OFF,RISERS,BASE,SEEDS,LIGHTS,FX,routes,roof,base};
