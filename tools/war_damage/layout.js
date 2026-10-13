'use strict';
// =============================================================================
// tools/war_damage/layout.js - THE WAR DAMAGE PASS (docs/205), the placement half.
//
// User 2026-10-03: "The tower needs a bit more flavor. The broken off pieces look
// to clean. The map is basically the first map but looks like its been fallen and
// beaten up by wars."
//
// Places Treyarch's own stock props (art/war_damage/kit.json, probe_kit.py), stock
// burn / blast / crack DECAL CARDS, and the effect + sound anchors that bring the
// damage alive:
//   * THE 24 BREAKS (tools/broken_tower_layout.js): the snapped lip made jagged
//     (slab chunks still hanging off its edges, long rebar bent out over the drop,
//     short bars hanging straight down, a torn plate), the lip, the wall under it,
//     the core wall and the catch deck scorched, rubble + a fallen slab + chunks +
//     scrap + glass on the deck (never in the landing spot or the walkway middle),
//     rebar through a blast on the core above every head, the old stair's iron
//     hanging off the outside, the column's rebar cage standing out of the snapped
//     stump, cables hanging; dust trickling off the ledge, embers on the rubble,
//     sparks on a cable, some fires with firelight, ash, a few tall smoke columns.
//   * SCATTERED DAMAGE on the ordinary floors: a scorched landing corner with
//     debris, a cable hanging off the outside, an iron beam sticking out past the
//     rail, a blast with rebar on the core wall above every head.
//   * PHASE 2 (docs/205 s7) THE BLAST'S WIRING: beside every crater the LED fixture
//     ripped off its mount dangles by one bracket (its tube flickers once the power
//     is back: a real flickering light), and the power conduit is TORN OPEN on the
//     other side (tools/war_damage/build_conduit_torn.py: the armored strip curled off
//     the wall, fray cables hanging from the torn mouth) - its two conductors are a
//     SEPARATE two-state client model (tod_war_conductor_<a|b>_<off|on>) that comes
//     alive as the power wave passes the floor, with a cyan arc spitting at the mouth.
//     Some ordinary-floor blasts tear a conduit too.
// Everything is DECORATIVE: drawn client-side by _tod_war_damage.csc, merged into one
// model per break and one per five floors (build_clusters.py), no collision, nothing
// a server trace can hit (the Archer's grapple never anchors on it). The .map does
// not change: no re-bake. The CHECKS below keep every piece in a safe zone: out of
// the landing spot, the walkway middle, the rail band and the next lap's landing.
//
// Each break / lap is composed in ITS OWN frame: s = +1 (odd laps: the east flight,
// the NE mid landing) as the generator writes it; s = -1 (even laps) is the same
// layout turned 180 degrees about the tower axis, exactly as broken_tower_layout.js
// mirrors its boxes (x,y -> -x,-y). Seeded per lap: no two breaks alike, and a re-run
// gives the same tower. Phase 2 draws from its OWN random stream per lap, so every
// phase-1 piece keeps its reviewed place.
//
// Usage: node tools/war_damage/layout.js          (writes the layout + the CSC data)
//        node tools/war_damage/layout.js --check  (writes nothing; fails if stale)
//        TOD_WAR_STAGE=<dir> writes both into <dir> (a staged copy)
// =============================================================================
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const { DROP_LAPS, placement } = require('../broken_tower_layout.js');
const readJson = rel => JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));
// the stock prop kit + the repo-built torn conduit bodies (kit_war.json, root "repo")
const KIT = Object.assign({}, readJson('art/war_damage/kit.json').props, readJson('art/war_damage/kit_war.json'));
const TORN = readJson('art/war_damage/conduit_torn.json');

const LAP_RISE = 384, LAPS = 50;
const HAVEN_LAPS = new Set([10, 11, 20, 21, 30, 31, 40, 41]);         // the core opens here (docs/202 v2)
const HAVEN_BANDS = [[10, 11], [20, 21], [30, 31], [40, 41]].map(([a, b]) => [(a - 1) * LAP_RISE, b * LAP_RISE]);
const SMOKE_COLUMNS = 6, FIRES = 8;                                    // tower-wide, spread by height
const LAP_TORN_PCT = 0.45;                                             // an ordinary-floor blast tears its conduit this often
// Stock decal materials (every one a PLAIN decal type - no alpha-reveal map - and in the gdt.db). CHOSEN BY
// MEASUREMENT (Blender reads the 4th TIFF sample PIL drops; sRGB luminance where the alpha is solid): a scorch
// must be DARKER than the dark district panels it sits on. Kept: charred_stain_01 0.10, blast_01 0.16, the metal
// bullet / shrapnel holes 0.01. Dropped: burn_impact_01 0.22, charred_stain_02 0.23 (ash grey) and the concrete
// cracks_01 0.34 - all read as PALE patches on the panels (the first preview showed them near-white).
const DECALS = {
  blast: ['t7_decal_blast_01'],                                                       // lit_decal
  stain: ['t7_decal_grunge_charred_stain_01'],                                        // lit_decal_diffuse_spec_gloss
  holes: ['t7_decal_bullet_metal_impact_01', 't7_decal_bullet_metal_exit_02', 't7_decal_bullet_metal_exit_03'],   // lit_decal_advanced
};
const DECAL_LIFT = 0.4;                                                // off the surface it sits on

// ---------------------------------------------------------------------------
// Math: the conduit batcher's own rotation (build_conduit_batches.py rotate()):
// roll about X, then pitch about Y, then yaw about Z, in BO3 degrees. It IS the
// engine's frame (local +X = AnglesToForward, +Y = -AnglesToRight, +Z = AnglesToUp),
// which is what lets a conductor ENTITY spawned with these angles sit exactly inside
// the torn body BAKED with the same rotation.
// ---------------------------------------------------------------------------
const R = d => d * Math.PI / 180;
function rotate(v, [p, y, r]) {
  const [x0, y0, z0] = v, cr = Math.cos(R(r)), sr = Math.sin(R(r)), cp = Math.cos(R(p)), sp = Math.sin(R(p)), cy = Math.cos(R(y)), sy = Math.sin(R(y));
  const a = [x0, y0 * cr - z0 * sr, y0 * sr + z0 * cr];
  const b = [a[0] * cp + a[2] * sp, a[1], -a[0] * sp + a[2] * cp];
  return [b[0] * cy - b[1] * sy, b[0] * sy + b[1] * cy, b[2]];
}
const add = (a, b) => a.map((v, i) => v + b[i]);
const mul = (a, k) => a.map(v => v * k);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
function bounds(model, org, angles, scale) {                          // world AABB of a placed prop
  const k = KIT[model]; if (!k) throw new Error('not in the kit: ' + model);
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (const cx of [k.min[0], k.max[0]]) for (const cy of [k.min[1], k.max[1]]) for (const cz of [k.min[2], k.max[2]]) {
    const p = add(rotate([cx * scale[0], cy * scale[1], cz * scale[2]], angles), org);
    for (let i = 0; i < 3; i++) { lo[i] = Math.min(lo[i], p[i]); hi[i] = Math.max(hi[i], p[i]); }
  }
  return { lo, hi };
}
function rng(seed) {                                                  // mulberry32
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
const pick = (r, list) => list[Math.floor(r() * list.length) % list.length];
const between = (r, a, b) => a + (b - a) * r();
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const qspin = r => 90 * Math.floor(r() * 4) + between(r, -4, 4);     // wall/floor cards turn in quarters: a 45-degree card is 41% wider
const ofRole = role => Object.keys(KIT).filter(n => KIT[n].role === role);
const SMALL_CHUNKS = ofRole('chunk').filter(n => Math.max(...KIT[n].max.map((v, i) => v - KIT[n].min[i])) <= 16);
const FRAY_CABLES = ofRole('cable').filter(n => KIT[n].min[2] > -12);   // the straighter wires (a torn conduit's cables hang straight down)
// +Y (a beam's length) onto unit direction d, the width staying level: yaw, then roll tips it.
function alongY(d) { return [0, Math.atan2(d[1], d[0]) * 180 / Math.PI - 90, Math.atan2(d[2], Math.hypot(d[0], d[1])) * 180 / Math.PI]; }
const unit = v => { const n = Math.hypot(...v); return v.map(c => c / n); };
// BO3 angles whose forward (+X) is unit direction d (pitch positive = down).
const dirAngles = d => [-Math.asin(clamp(d[2], -1, 1)) * 180 / Math.PI, Math.atan2(d[1], d[0]) * 180 / Math.PI, 0];
// The frame these angles give must be the one the composition reasons about (a wrong sign here would put a conductor
// entity beside its baked body, or a fixture inside the wall): proved per placement, not assumed.
function assertAxes(angles, local, world, what) {
  const got = rotate(local, angles);
  if (got.some((v, i) => Math.abs(v - world[i]) > 1e-6)) throw new Error(`${what}: local ${local} -> ${got.map(v => v.toFixed(4))}, wanted ${world}`);
}

// ---------------------------------------------------------------------------
// Placing: a prop or a decal card in the frame, checked against its zone + the forbidden list.
// ---------------------------------------------------------------------------
function place(list, zone, model, org, angles = [0, 0, 0], scale = [1, 1, 1], tag = '') {
  const bb = bounds(model, org, angles, scale);
  list.push({ model, org: org.map(v => +v.toFixed(2)), angles: angles.map(v => +v.toFixed(2)), scale: scale.map(v => +v.toFixed(3)), zone, tag, bb });
  return bb;
}
// Rest on a floor: the rotated bottom touches floorZ, sunk `sink` units into it.
function rest(list, zone, model, xy, floorZ, angles, scale, tag, sink = 0.6) {
  const bb0 = bounds(model, [xy[0], xy[1], 0], angles, scale);
  return place(list, zone, model, [xy[0], xy[1], floorZ - bb0.lo[2] - sink], angles, scale, tag);
}
// A decal card flat on a surface: centre c (on the surface), outward normal n, card
// width axis u (in the surface), size w x h, spun `spin` degrees about n. The card is
// lifted DECAL_LIFT off the surface; build_clusters.py winds it to face n.
function decal(list, zone, material, c, n, u, w, h, spin, tag) {
  const v0 = cross(n, u), cs = Math.cos(R(spin)), sn = Math.sin(R(spin));
  const uu = add(mul(u, cs), mul(v0, sn)), vv = add(mul(u, -sn), mul(v0, cs));
  const centre = add(c, mul(n, DECAL_LIFT));
  const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([a, b]) => add(centre, add(mul(uu, a * w / 2), mul(vv, b * h / 2))));
  const lo = [0, 1, 2].map(i => Math.min(...corners.map(p => p[i]))), hi = [0, 1, 2].map(i => Math.max(...corners.map(p => p[i])));
  list.push({ decal: material, org: centre.map(v => +v.toFixed(2)), n, u: uu.map(v => +v.toFixed(5)), v: vv.map(v => +v.toFixed(5)), w: +w.toFixed(1), h: +h.toFixed(1), zone, tag, bb: { lo, hi } });
}

// ---------------------------------------------------------------------------
// THE CHECKS, in the s = +1 frame. A piece must sit wholly inside its SAFE ZONE and
// touch nothing in the FORBIDDEN list (belt and braces). Decal cards live on surface
// zones (a rectangle of a real face, so a card never overhangs into the air).
// ---------------------------------------------------------------------------
const fails = [];
const inside = (bb, z) => bb.lo[0] >= z.x[0] && bb.hi[0] <= z.x[1] && bb.lo[1] >= z.y[0] && bb.hi[1] <= z.y[1] && bb.lo[2] >= z.z[0] && bb.hi[2] <= z.z[1];
const overlaps = (bb, z) => bb.lo[0] < z.x[1] && bb.hi[0] > z.x[0] && bb.lo[1] < z.y[1] && bb.hi[1] > z.y[0] && bb.lo[2] < z.z[1] && bb.hi[2] > z.z[0];
const fmtBB = bb => `x[${bb.lo[0].toFixed(0)},${bb.hi[0].toFixed(0)}] y[${bb.lo[1].toFixed(0)},${bb.hi[1].toFixed(0)}] z[${bb.lo[2].toFixed(0)},${bb.hi[2].toFixed(0)}]`;

function breakZones(b) {
  return {
    teeth:     { x: [258, 414], y: [245, 256], z: [b + 140, b + 191] },         // under the snapped lip, over every head
    lipCore:   { x: [250, 306], y: [198, 282], z: [b + 140, b + 206] },         // the lip's two ends (players drop
    lipRail:   { x: [366, 422], y: [198, 282], z: [b + 140, b + 206] },         //   mid-lip; zombies at x 336)
    outside:   { x: [437, 640], y: [-250, 312], z: [b - 160, b + 262] },        // past the rail: free air
    stump:     { x: [437, 470], y: [226, 282], z: [b + 226, b + 380] },         // on the snapped frame stump (x 436-456)
    core:      { x: [255.5, 266.5], y: [-240, 230], z: [b + 150, b + 360] },    // the core wall at the deck, above heads
    coreFix:   { x: [255.5, 266.5], y: [-240, 230], z: [b + 150, b + 362] },    // the dangling fixture, flat on that wall
    coreTorn:  { x: [255.5, 336], y: [-240, 160], z: [b + 100, b + 362] },      // the torn conduit curling off it + its fray
    deckCore:  { x: [256, 312], y: [-232, 150], z: [b - 1, b + 2 + 20] },       // debris against the core wall
    deckRail:  { x: [372, 416], y: [-232, 150], z: [b - 1, b + 2 + 24] },       // debris against the rail
    deckFlat:  { x: [256, 416], y: [-232, 166], z: [b - 1, b + 2 + 8] },        // flat debris may cross the walk
    // decal surfaces (real faces): the wall under the ledge, the core at the deck, the deck, the ledge top at the lip
    fasciaFace: { x: [258, 414], y: [255, 256.5], z: [b + 4, b + 174] },
    coreFace:   { x: [255.5, 257], y: [-240, 240], z: [b + 4, b + 380] },
    deckFace:   { x: [258, 414], y: [-236, 250], z: [b + 1.5, b + 3] },
    ledgeFace:  { x: [258, 414], y: [258, 410], z: [b + 191.5, b + 193] },
  };
}
function breakForbidden(b) {
  return [
    { why: 'the landing column (mid-lip drop, zombie node at x 336)', x: [306, 366], y: [166, 245], z: [b + 2 + 8, b + 272] },
    { why: 'the landing body space', x: [256, 416], y: [166, 222], z: [b + 2 + 8, b + 140] },
    { why: 'the rail band below the visible rail top', x: [416.5, 436.5], y: [-256, 256], z: [b + 2, b + 41] },
    { why: 'the walkway middle above ankle height, to head height + 26', x: [312, 372], y: [-256, 256], z: [b + 2 + 8, b + 100] },
    { why: 'the previous lap\'s end landing (spawn point, conduits)', x: [256, 416], y: [-416, -240], z: [b - 1, b + 120] },
  ];
}
function lapZones(b) {
  return {
    corner:        { x: [384, 416], y: [384, 416], z: [b + 190, b + 192 + 24] },  // the NE mid landing's outer corner
    outsideCorner: { x: [437, 520], y: [300, 470], z: [b + 40, b + 260] },        // past the NE corner rail
    outsideFlight: { x: [437, 640], y: [-240, 240], z: [b - 120, b + 220] },      // past the E flight rail
    coreGrid:      { x: [255.5, 266.5], y: [-230, 230], z: [b + 330, b + 700] },  // the core above the E flight
    coreTornLap:   { x: [255.5, 336], y: [-230, 230], z: [b + 300, b + 700] },    // a torn conduit curling off it, well over the flight
    coreFace:      { x: [255.5, 257], y: [-236, 236], z: [b + 322, b + 740] },    // decal: the same face
    cornerFace:    { x: [300, 414], y: [300, 414], z: [b + 191.5, b + 193] },     // decal: the NE landing floor
  };
}
const crossesHaven = (z0, z1) => HAVEN_BANDS.some(([a, c]) => z0 < c && z1 > a);
function check(where, list, zones, forbid = []) {
  for (const p of list) {
    const what = p.model || p.decal;
    if (!zones[p.zone]) { fails.push(`${where} ${p.tag}: no zone ${p.zone}`); continue; }
    if (!inside(p.bb, zones[p.zone])) fails.push(`${where} ${p.tag} (${what}) leaves its zone ${p.zone}: ${fmtBB(p.bb)}`);
    for (const f of forbid) if (overlaps(p.bb, f)) fails.push(`${where} ${p.tag} (${what}) enters ${f.why}: ${fmtBB(p.bb)}`);
  }
}

// ---------------------------------------------------------------------------
// PHASE 2: a conduit torn open on the +X core face (s = +1 frame), its conductors live,
// fray cables hanging from the torn mouth, the arc spitting there once powered.
// The strip is placed with its local +X UP the wall and its local +Z OUT of it.
// ---------------------------------------------------------------------------
const WALL_X = 256, OFF_WALL = 0.3;                                   // the core face; a hair off it (no z-fight)
function tornConduit(rw, props, fx, conductors, zone, y, z, tag) {
  const vc = pick(rw, ['a', 'b']), ang = [-90, 180, 0], org = [WALL_X + OFF_WALL, +y.toFixed(2), +z.toFixed(2)];
  assertAxes(ang, [1, 0, 0], [0, 0, 1], tag + ' +X up');
  assertAxes(ang, [0, 0, 1], [1, 0, 0], tag + ' +Z out of the wall');
  place(props, zone, 'tod_war_conduit_torn_' + vc, org, ang, [1, 1, 1], tag);
  conductors.push({ model: 'tod_war_conductor_' + vc, org, angles: ang, tag });
  const mouth = add(org, rotate(TORN.variants[vc].free_end, ang));
  for (let i = 0, n = 1 + Math.floor(rw() * 2); i < n; i++) {        // the fray: a cable or two hanging from the torn mouth
    const sy = between(rw, 0.4, 0.6);
    place(props, zone, pick(rw, FRAY_CABLES), [mouth[0] - 2 + between(rw, -2, 2), mouth[1] + between(rw, -4, 4), mouth[2] + 1], [0, between(rw, -35, 35) + 90, -90], [0.6, sy, 0.6], tag + ' fray');
  }
  fx.push({ kind: 'arc', org: [mouth[0] + 1.5, mouth[1], mouth[2]].map(v => +v.toFixed(1)), angles: [0, 0, 0], powered: true, sound: 'tod_war_arc_lp' });
  return vc;
}

// ---------------------------------------------------------------------------
// ONE BREAK (s = +1 frame; b = the lap's base; the ledge lip at y 256, top z b+192)
// ---------------------------------------------------------------------------
function composeBreak(lap, fireSet, smokeSet) {
  const { b } = placement(lap), r = rng(lap * 2654435761), props = [], decals = [], fx = [], conductors = [];
  // (1) THE JAGGED LIP. Slab chunks still hanging off both ends, tipped down over the drop.
  for (const [zone, x0, x1] of [['lipCore', 278, 282], ['lipRail', 392, 396]]) {
    const model = pick(r, ofRole('slab')), sc = model.endsWith('lg_03_no_metal') ? between(r, 0.42, 0.5) : between(r, 0.55, 0.65);
    place(props, zone, model, [between(r, x0, x1), 252, b + 176], [between(r, -8, 8), between(r, -12, 12), between(r, 26, 44)], [sc, sc, sc], 'hanging slab');
  }
  //     Long rebar bent out over the drop at both ends.
  for (const [zone, x0, x1, side] of [['lipCore', 266, 286, -1], ['lipRail', 386, 406, 1], ['lipCore', 266, 286, -1], ['lipRail', 386, 406, 1]]) {
    const th = between(r, 26, 40), yaw = -90 - side * between(r, 0, 14), sx = between(r, 1.3, 1.55);
    const d = rotate([1, 0, 0], [th, yaw, 0]), start = [between(r, x0, x1), 255, b + 186];
    place(props, zone, pick(r, ofRole('rebar')), add(start, mul(d, 17.25 * sx)), [th, yaw, between(r, 0, 360)], [sx, 1, 1], 'bent-out rebar');
  }
  //     Short bars hanging straight down in the middle, and a torn plate.
  for (let i = 0; i < 2 + Math.floor(r() * 2); i++)
    place(props, 'teeth', pick(r, ofRole('rebar')), [between(r, 304, 368), 250.5, b + 190 - 17.6], [84 + r() * 10, (r() < 0.5 ? 0 : 180) + between(r, -4, 4), 0], [1, 1, 1], 'tooth');
  place(props, 'teeth', pick(r, ofRole('scrap')), [between(r, 300, 372), 251, b + 181], [0, between(r, -7, 7), 90], [1, 1, 1], 'torn lip plate');
  // (2) SCORCH: the lip, the wall under it, the core beside the deck, the deck (cards).
  decal(decals, 'ledgeFace', pick(r, DECALS.stain), [336 + between(r, -4, 4), 304, b + 192], [0, 0, 1], [1, 0, 0], 140, 80, between(r, -4, 4), 'scorched lip');
  decal(decals, 'fasciaFace', pick(r, [...DECALS.stain, ...DECALS.blast]), [336 + between(r, -3, 3), 256, b + 96 + between(r, -6, 6)], [0, -1, 0], [1, 0, 0], 136, between(r, 120, 130), (r() < 0.5 ? 0 : 180) + between(r, -3, 3), 'scorched wall');
  const blastY = between(r, -125, 110), blastZ = b + between(r, 160, 250);
  decal(decals, 'coreFace', pick(r, DECALS.blast), [256, blastY, blastZ], [1, 0, 0], [0, 1, 0], between(r, 170, 200), between(r, 170, 200), qspin(r), 'core blast');
  //     THE SHRAPNEL: small dark metal holes peppered round the blast and across the wall under the lip. (The three
  //     draws the old concrete-crack card took are still made, so every other piece keeps its reviewed place; the
  //     holes draw from their own stream.)
  r(); between(r, 70, 140); qspin(r);
  const rs = rng(lap * 7919 + 101);
  for (let i = 0, n = 6 + Math.floor(rs() * 4); i < n; i++) {
    const a = rs() * Math.PI * 2, rad = between(rs, 80, 150), sz = between(rs, 9, 20);
    const y = Math.max(-238 + sz, Math.min(238 - sz, blastY + Math.cos(a) * rad));
    const z = Math.max(b + 6 + sz, Math.min(b + 378 - sz, blastZ + Math.sin(a) * rad));
    decal(decals, 'coreFace', pick(rs, DECALS.holes), [256, y, z], [1, 0, 0], [0, 1, 0], sz, sz, between(rs, 0, 360), 'shrapnel');
  }
  for (let i = 0, n = 2 + Math.floor(rs() * 3); i < n; i++) {
    const sz = between(rs, 8, 16);
    decal(decals, 'fasciaFace', pick(rs, DECALS.holes), [between(rs, 266 + sz, 406 - sz), 256, b + between(rs, 12 + sz, 166 - sz)], [0, -1, 0], [1, 0, 0], sz, sz, between(rs, 0, 360), 'shrapnel');
  }
  const deck = b + 2, pileY = between(r, -130, 30);
  decal(decals, 'deckFace', pick(r, DECALS.stain), [336, pileY, deck], [0, 0, 1], [1, 0, 0], 140, between(r, 140, 170), between(r, -4, 4), 'charred deck');
  decal(decals, 'deckFace', pick(r, DECALS.stain), [336, between(r, 160, 168), deck], [0, 0, 1], [1, 0, 0], 140, 140, qspin(r), 'scorched landing');
  // (3) THE CORE above every head: rebar showing through the blast.
  place(props, 'core', pick(r, ofRole('rebar_grid')), [259.9, blastY + between(r, -20, 20), Math.max(b + 186, Math.min(b + 324, blastZ + between(r, -20, 20)))], [0, 90, 0], [1, 1, 1], 'rebar in the blast');
  // (4) OUTSIDE: the column's rebar cage standing out of the snapped stump, the old stair's iron
  //     hanging from it, cables hanging.
  place(props, 'stump', 'p7_rebar_column_128', [450, between(r, 246, 258), b + 238 + 62], [between(r, -3, 3), between(r, 0, 360), between(r, -3, 3)], [1, 1, 1], 'column cage');
  const beamLen = between(r, 150, 210), start = [462, between(r, 236, 262), b + between(r, 198, 222)];
  const ha = R(between(r, -60, -25)), dir = unit([Math.cos(ha) * 0.6, Math.sin(ha) * 0.6, -between(r, 0.5, 0.8)]);
  place(props, 'outside', 'p7_zm_der_gantry_beam_01', add(start, mul(dir, beamLen / 2)), alongY(dir), [0.5, beamLen / 552, 0.7], 'hanging stair iron');
  const cables = [];
  for (let i = 0; i < 1 + Math.floor(r() * 2); i++) {
    const at = [452, between(r, 214, 292), b + between(r, 176, 236)], sy = between(r, 1.2, 1.8);
    place(props, 'outside', pick(r, ofRole('cable')), at, [0, between(r, -20, 20) + 90, -90], [1, sy, 1], 'hanging cable');
    cables.push([at[0], at[1], at[2] - 64 * sy]);
  }
  // (5) THE DECK: rubble against the core wall, a fallen slab + chunks by the rail, scatter, glass, scrap.
  rest(props, 'deckCore', 'p7_debris_concrete_rubble_pile_03', [284, pileY], deck, [0, between(r, -3, 3), 0], [0.54, 1.1, 1.05], 'rubble pile', 2.5);
  rest(props, 'deckCore', pick(r, SMALL_CHUNKS), [between(r, 274, 290), pileY + between(r, 66, 86)], deck, [0, between(r, 0, 360), 0], [1, 1, 1], 'chunk', 1.5);
  rest(props, 'deckRail', 'p7_debris_concrete_rubble_lg_03_no_metal', [390, between(r, -200, -40)], deck, [between(r, -4, 4), between(r, 84, 96), between(r, 4, 8)], [0.45, 0.45, 0.45], 'fallen slab', 1.5);
  for (let i = 0; i < 3 + Math.floor(r() * 2); i++)
    rest(props, 'deckRail', pick(r, SMALL_CHUNKS), [between(r, 392, 402), between(r, -20, 132)], deck, [between(r, -20, 20), between(r, 0, 360), between(r, -20, 20)], [1, 1, 1], 'chunk', 1.5);
  rest(props, 'deckFlat', 'p7_debris_concrete_rubble_scattered_01', [336, between(r, -150, 10)], deck, [0, between(r, 0, 360), 0], [0.72, 0.72, 1], 'scatter', 0.4);
  rest(props, 'deckFlat', pick(r, ofRole('glass')), [between(r, 324, 340), between(r, 30, 100)], deck, [0, between(r, 0, 360), 0], [1, 1, 1], 'glass', -0.15);
  rest(props, 'deckRail', pick(r, ofRole('scrap')), [between(r, 388, 398), between(r, -60, 100)], deck, [0, between(r, 0, 360), 0], [0.9, 0.9, 0.9], 'scrap', 0.8);

  // EFFECTS + SOUNDS (anchors; the CSC hosts them near the player; `always` = seen from far).
  fx.push({ kind: 'dust', org: [+between(r, 300, 372).toFixed(1), 249, b + 175], angles: [90, 0, 0] });
  if (r() < 0.65 && cables.length) fx.push({ kind: 'sparks', org: cables[0].map(v => +v.toFixed(1)), angles: [0, 0, 0], sound: 'tod_war_spark_lp' });
  fx.push({ kind: r() < 0.75 ? 'smolder' : 'smoke_low', org: [285, +pileY.toFixed(1), deck + 14], angles: [-90, 0, 0], sound: 'tod_war_fire_lp' });
  if (fireSet.has(lap)) fx.push({ kind: 'fire', org: [285, +(pileY + between(r, -28, 28)).toFixed(1), deck + 8], angles: [-90, 0, 0], light: true, sound: 'tod_war_fire_lp' });
  if (r() < 0.45) fx.push({ kind: 'ash', org: [336, +between(r, -80, 80).toFixed(1), b + 120], angles: [0, 0, 0] });
  if (smokeSet.has(lap)) fx.push({ kind: 'smoke_column', org: [520, +between(r, -60, 80).toFixed(1), b + 10], angles: [-90, 0, 0], always: true });

  // (6) PHASE 2 - THE BLAST'S WIRING, from its own stream. The crater's emptier side gets the torn conduit, the
  //     other side the fixture, both clear of the landing column (y >= 166) and the rebar in the blast.
  const rw = rng(lap * 104729 + 7), side = blastY < 0 ? 1 : -1;
  //     The fixture: its top bracket still bolted at (256, yf, zf), the body hanging down tilted phi off vertical,
  //     away from the crater; the mount plane a hair off the wall, the body (local -Z) out of it. Frame: local +Z into
  //     the wall, local +Y down the hang (angles [-phi, 90, -90], proved below).
  const yf = clamp(blastY - side * 118, -190, 140), zf = clamp(blastZ + between(rw, -30, 40), b + 150 + 70, b + 360 - 8);
  const phi = -side * between(rw, 12, 32), down = [0, Math.sin(R(phi)), -Math.cos(R(phi))], fixAng = [-phi, 90, -90];
  assertAxes(fixAng, [0, 0, 1], [-1, 0, 0], `lap ${lap} fixture: +Z into the wall`);
  assertAxes(fixAng, [0, 1, 0], down, `lap ${lap} fixture: +Y down the hang`);
  const fixC = add([WALL_X + 0.4, yf, zf], mul(down, 30.3));          // centre: half the length down from the top bracket
  place(props, 'coreFix', 'p7_light_fixture_led_ceiling_01_dmg', fixC, fixAng, [1, 1, 1], 'dangling fixture');
  const bulbs = add(fixC, [4.6, 0, 0]);                               // just outside the broken diffuser (local z -4.41)
  fx.push({ kind: pick(rw, ['lamp_a', 'lamp_b', 'lamp_c']), org: bulbs.map(v => +v.toFixed(1)), angles: dirAngles(down).map(v => +v.toFixed(2)), powered: true, sound: 'tod_war_tube_lp' });
  //     The torn conduit on the other side (origin = the strip's middle; b droops 65 below it).
  tornConduit(rw, props, fx, conductors, 'coreTorn', clamp(blastY + side * 115, -190, 140), clamp(blastZ - 10 + between(rw, -24, 24), b + 216, b + 311), 'torn conduit');

  check(`lap ${lap}`, props, breakZones(b), breakForbidden(b));
  check(`lap ${lap}`, decals, breakZones(b));
  return { props, decals, fx, conductors, blastY };
}

// ---------------------------------------------------------------------------
// SCATTER on an ordinary lap (s = +1 frame: the E flight b..b+192, the NE mid landing at b+192).
// ---------------------------------------------------------------------------
function composeLap(lap) {
  const b = (lap - 1) * LAP_RISE, r = rng(lap * 40503 + 7), props = [], decals = [], fx = [], conductors = [];
  const menu = ['corner', 'cable', 'beam', 'core'].filter(k => k !== 'core' || !crossesHaven(b + 322, b + 740));
  const n = 1 + (r() < 0.6 ? 1 : 0), used = new Set();
  for (let i = 0; i < n; i++) {
    let k = pick(r, menu); while (used.has(k)) k = menu[(menu.indexOf(k) + 1) % menu.length]; used.add(k);
    if (k === 'corner') {
      decal(decals, 'cornerFace', pick(r, DECALS.stain), [357, 357, b + 192], [0, 0, 1], [1, 0, 0], 100, 100, qspin(r), 'scorched corner');
      for (let j = 0; j < 2 + Math.floor(r() * 2); j++)
        rest(props, 'corner', pick(r, SMALL_CHUNKS), [between(r, 396, 404), between(r, 396, 404)], b + 192, [between(r, -12, 12), between(r, 0, 360), between(r, -12, 12)], [1, 1, 1], 'corner chunk', 1.2);
      rest(props, 'corner', pick(r, ofRole('scrap')), [between(r, 398, 402), between(r, 398, 402)], b + 192, [0, between(r, 0, 360), 0], [0.7, 0.7, 0.7], 'corner scrap', 0.6);
    } else if (k === 'cable') {
      const at = [452, between(r, 330, 400), b + between(r, 186, 236)], sy = between(r, 1.1, 1.6);
      place(props, 'outsideCorner', pick(r, ofRole('cable')), at, [0, between(r, -20, 20) + 90, -90], [1, sy, 1], 'hanging cable');
      if (r() < 0.25) fx.push({ kind: 'sparks', org: [at[0], +at[1].toFixed(1), +(at[2] - 64 * sy).toFixed(1)], angles: [0, 0, 0], sound: 'tod_war_spark_lp' });
    } else if (k === 'beam') {
      const len = between(r, 120, 165), dir = unit([1, between(r, -0.3, 0.3), -between(r, 0.05, 0.35)]), start = [462, between(r, -150, 150), b + between(r, 40, 150)];
      place(props, 'outsideFlight', 'p7_zm_der_gantry_beam_01', add(start, mul(dir, len / 2)), alongY(dir), [0.45, len / 552, 0.6], 'beam stub');
    } else {
      const y = between(r, -120, 120), z = b + between(r, 440, 600);
      decal(decals, 'coreFace', pick(r, DECALS.blast), [256, y, z], [1, 0, 0], [0, 1, 0], between(r, 160, 200), between(r, 160, 200), qspin(r), 'core blast');
      place(props, 'coreGrid', pick(r, ofRole('rebar_grid')), [259.9, y + between(r, -20, 20), z + between(r, -20, 20)], [0, 90, 0], [1, 1, 1], 'rebar in the blast');
      // PHASE 2: some of these blasts tore the conduit beside them too (its own stream: the scatter above keeps its place)
      const rw = rng(lap * 104729 + 7);
      if (rw() < LAP_TORN_PCT)
        tornConduit(rw, props, fx, conductors, 'coreTornLap', clamp(y + (y < 0 ? 1 : -1) * 110, -200, 200), clamp(z + between(rw, -20, 20), b + 300 + 66, b + 700 - 49), 'torn conduit');
    }
  }
  check(`lap ${lap}`, props, lapZones(b));
  check(`lap ${lap}`, decals, lapZones(b));
  return { props, decals, fx, conductors };
}

// ---------------------------------------------------------------------------
// THE TOWER: turn every frame into world space, group into clusters.
// ---------------------------------------------------------------------------
const turn = (s, v) => s > 0 ? v : [-v[0], -v[1], v[2]];
const norm360 = v => +(((v % 360) + 360) % 360).toFixed(2);
const r5 = v => +v.toFixed(5);
const toWorld = (s, item) => item.decal
  ? { ...item, org: turn(s, item.org).map(v => +v.toFixed(2)), n: turn(s, item.n).map(r5), u: turn(s, item.u).map(r5), v: turn(s, item.v).map(r5) }
  : { ...item, org: turn(s, item.org).map(v => +v.toFixed(2)), angles: item.angles ? [item.angles[0], norm360(item.angles[1] + (s > 0 ? 0 : 180)), item.angles[2]] : item.angles };
const spread = (laps, k) => { const out = new Set(); for (let i = 0; i < k; i++) out.add(laps[Math.round(i * (laps.length - 1) / Math.max(1, k - 1))]); return out; };
const byHeight = [...DROP_LAPS].sort((a, b) => b - a);
const smokeSet = spread(byHeight.filter((_, i) => i % 2 === 0), SMOKE_COLUMNS), fireSet = spread(byHeight.filter((_, i) => i % 2 === 1), FIRES);

const clusters = [], conductors = [], scorchLabels = {};
for (const lap of DROP_LAPS) {
  const { s, b } = placement(lap), c = composeBreak(lap, fireSet, smokeSet);
  clusters.push({ name: `tod_war_break_${String(lap).padStart(2, '0')}`, kind: 'break', laps: [lap], org: turn(s, [336, 0, b]),
    props: c.props.map(p => toWorld(s, p)), decals: c.decals.map(d => toWorld(s, d)), fx: c.fx.map(f => toWorld(s, f)) });
  conductors.push(...c.conductors.map(x => ({ ...toWorld(s, x), lap })));
  // BUILD B (docs/205 s7b): the map's own surfaces at the break wear the SCORCHED twin of their kit role
  // (tools/art_cohesion/tower_surfaces.js reads this): the seven broken pieces and the lip landing whole, and of the
  // core quadrant holding the crater only the face the crater is on (its outward normal, world space).
  const lip = s > 0 ? 'NE' : 'SW';
  for (const piece of ['broken catch deck', 'broken outer rail', 'broken landing fascia', 'broken frame outer stump', 'broken frame core scar',
    'broken nose fragment a', 'broken nose fragment b', `${lip} landing`, `${lip} landing para a`, `${lip} landing para b`])
    scorchLabels[`lap${lap} ${piece}`] = { faces: null };
  const quadrant = s > 0 ? (c.blastY > 0 ? 'NE' : 'SE') : (c.blastY > 0 ? 'SW' : 'NW');
  scorchLabels[`core band lap${lap} ${quadrant}`] = { faces: [s, 0, 0] };
}
const regions = new Map();
for (let lap = 3; lap <= LAPS - 1; lap++) {
  if (DROP_LAPS.includes(lap) || HAVEN_LAPS.has(lap)) continue;
  const s = lap % 2 ? 1 : -1, c = composeLap(lap), key = Math.floor((lap - 1) / 5);
  if (!regions.has(key)) regions.set(key, { props: [], decals: [], fx: [], laps: [] });
  const g = regions.get(key); g.laps.push(lap);
  g.props.push(...c.props.map(p => toWorld(s, p))); g.decals.push(...c.decals.map(d => toWorld(s, d))); g.fx.push(...c.fx.map(f => toWorld(s, f)));
  conductors.push(...c.conductors.map(x => ({ ...toWorld(s, x), lap })));
}
for (const [key, g] of [...regions].sort((a, b) => a[0] - b[0])) {
  if (!g.props.length && !g.decals.length) continue;
  clusters.push({ name: `tod_war_floors_${String(key * 5 + 1).padStart(2, '0')}`, kind: 'scatter', laps: g.laps, org: [0, 0, Math.round((key * 5 + 2.5) * LAP_RISE)], props: g.props, decals: g.decals, fx: g.fx });
}

// ---------------------------------------------------------------------------
// BUDGETS + OUTPUT
// ---------------------------------------------------------------------------
const FX = {   // kind -> effect (stock ones verified real: no gfx_debug_missing_fx stub, no _pcloud; tod/war ones GENERATED by make_fx.py)
  dust: 'dirt/fx_dust_fall_sm_lit',
  sparks: 'electric/fx_elec_sparks_sm_wire_orange',
  smolder: 'fire/fx_fire_ground_rubble_sm_50x50',
  smoke_low: 'smoke/fx_smk_ground_rubble_50x50',
  fire: 'fire/fx_fire_ground_rubble_50x50',
  ash: 'debris/fx_debris_ash_float_lg',
  smoke_column: 'smoke/fx_smk_column_wind_slow_sm_tall_dark',
  arc: 'tod/war/fx_war_arc',                              // phase 2: the live conductors at a torn mouth (powered)
  lamp_a: 'tod/war/fx_war_tube_flicker_a',                // phase 2: the dangling fixtures' flickering tubes (powered;
  lamp_b: 'tod/war/fx_war_tube_flicker_b',                //   each carries its own dynamic light)
  lamp_c: 'tod/war/fx_war_tube_flicker_c',
};
const FIRE_LIGHT = 'light/fx_light_fire_flicker_noshad_small';
const KINDS = Object.keys(FX);
const LAMP_KINDS = ['lamp_a', 'lamp_b', 'lamp_c'];
const SOUNDS = { tod_war_fire_lp: 4, tod_war_spark_lp: 8, tod_war_tube_lp: 32, tod_war_arc_lp: 64 };   // flag bits (LOCKSTEP: the CSC)
const allFx = clusters.flatMap(c => c.fx);
const totals = { clusters: clusters.length, props: clusters.reduce((n, c) => n + c.props.length, 0), decals: clusters.reduce((n, c) => n + c.decals.length, 0), fx: allFx.length,
  fires: allFx.filter(f => f.kind === 'fire').length, smoke_columns: allFx.filter(f => f.kind === 'smoke_column').length,
  sparks: allFx.filter(f => f.kind === 'sparks').length, sounds: allFx.filter(f => f.sound).length,
  lamps: allFx.filter(f => LAMP_KINDS.includes(f.kind)).length, arcs: allFx.filter(f => f.kind === 'arc').length,
  conductors: conductors.length, torn_conduits: clusters.reduce((n, c) => n + c.props.filter(p => KIT[p.model].role === 'conduit_torn').length, 0) };
if (totals.clusters > 40) fails.push(`${totals.clusters} cluster models: the client budget is 40`);
if (totals.fires !== FIRES) fails.push(`${totals.fires} fires, expected ${FIRES}`);
if (totals.smoke_columns !== SMOKE_COLUMNS) fails.push(`${totals.smoke_columns} smoke columns, expected ${SMOKE_COLUMNS}`);
if (totals.lamps !== DROP_LAPS.length) fails.push(`${totals.lamps} flickering fixtures, expected one per break (${DROP_LAPS.length})`);
if (totals.arcs !== totals.conductors || totals.torn_conduits !== totals.conductors) fails.push(`torn conduits ${totals.torn_conduits} / conductor models ${totals.conductors} / arcs ${totals.arcs} must agree`);
if (totals.conductors < DROP_LAPS.length || totals.conductors > 48) fails.push(`${totals.conductors} conductor client models: expected one per break and up to 48`);
for (const c of clusters) if (!c.props.length && !c.decals.length) fails.push(`${c.name} is empty`);
for (const f of allFx) if (!KINDS.includes(f.kind)) fails.push(`unknown effect kind ${f.kind}`);
for (const f of allFx) if (f.sound && !(f.sound in SOUNDS)) fails.push(`unknown sound ${f.sound}`);
for (const f of allFx) if (LAMP_KINDS.includes(f.kind) && !f.powered) fails.push(`a lamp anchor must be powered-only`);

if (fails.length) { for (const f of fails) console.log('FAIL ' + f); console.log(`WAR DAMAGE LAYOUT FAILED: ${fails.length} problems`); process.exit(1); }

const layout = { generated_by: 'tools/war_damage/layout.js', fx_map: FX, fire_light: FIRE_LIGHT, decal_materials: DECALS, sound_flags: SOUNDS, totals,
  clusters: clusters.map(c => ({ name: c.name, kind: c.kind, laps: c.laps, org: c.org,
    props: c.props.map(({ bb, ...p }) => p), decals: c.decals.map(({ bb, ...d }) => d), fx: c.fx })),
  conductors: conductors.map(({ bb, ...x }) => x) };
const layoutText = JSON.stringify(layout, null, 1) + '\n';

// The client data the CSC reads (GENERATED - never hand-edit).
const vec = v => `( ${v.map(n => +(+n).toFixed(1)).join(', ')} )`;
const sw = (name, rows, dflt) => `function ${name}( i )\n{\n\tswitch ( i )\n\t{\n${rows.map((v, i) => `\t\tcase ${i}: return ${v};`).join('\n')}\n\t}\n\treturn ${dflt};\n}\n`;
let csc = `// GENERATED by tools/war_damage/layout.js - DO NOT EDIT. THE WAR DAMAGE PASS (docs/205).\n`
  + `// ${totals.clusters} cluster models (${totals.props} stock props + ${totals.decals} scorch cards merged), ${totals.fx} effect anchors: ${totals.fires} fires, ${totals.smoke_columns} smoke columns, ${totals.sparks} sparks,\n`
  + `// ${totals.lamps} flickering fixtures, ${totals.arcs} live arcs; ${totals.conductors} two-state conductor models (phase 2).\n\n`
  + `#namespace tod_war_damage_data;\n\n`;
csc += `function cluster_count() { return ${clusters.length}; }\n`;
csc += sw('cluster_model', clusters.map(c => `"${c.name}"`), '""');
csc += sw('cluster_org', clusters.map(c => vec(c.org)), '( 0, 0, 0 )');
csc += `function fx_count() { return ${allFx.length}; }\n`;
csc += `// kind: ${KINDS.map((k, i) => `${i} ${k}`).join(', ')}\n`;
csc += sw('fx_kind', allFx.map(f => KINDS.indexOf(f.kind)), '-1');
csc += sw('fx_org', allFx.map(f => vec(f.org)), '( 0, 0, 0 )');
csc += sw('fx_angles', allFx.map(f => vec(f.angles)), '( 0, 0, 0 )');
csc += `// flags: 1 = a firelight rides it, 2 = always on (seen from far), 4 = fire crackle loop, 8 = spark buzz loop,\n`
  + `//        16 = powered only (runs once the power wave has passed its height), 32 = tube hum loop, 64 = arc buzz loop\n`;
csc += sw('fx_flags', allFx.map(f => (f.light ? 1 : 0) | (f.always ? 2 : 0) | (f.powered ? 16 : 0) | (f.sound ? SOUNDS[f.sound] : 0)), '0');
csc += `// the torn conduits' conductors: <model>_off at connect, <model>_on once the power wave has passed their height\n`;
csc += `function conductor_count() { return ${conductors.length}; }\n`;
csc += sw('conductor_model', conductors.map(c => `"${c.model}"`), '""');
csc += sw('conductor_org', conductors.map(c => vec(c.org)), '( 0, 0, 0 )');
csc += sw('conductor_angles', conductors.map(c => vec(c.angles)), '( 0, 0, 0 )');

// The map's scorched surfaces (GENERATED - never hand-edit; the generator's tower_surfaces.js reads it).
const scorchText = JSON.stringify({ generated_by: 'tools/war_damage/layout.js', breaks: DROP_LAPS.length, labels: scorchLabels }, null, 1) + '\n';

const OUT_LAYOUT = path.join(ROOT, 'art/war_damage/layout.json');
const OUT_CSC = path.join(ROOT, 'scripts/zm/zm_tod2_cybercity/_tod_war_damage_data.csc');
const OUT_SCORCH = path.join(ROOT, 'art/war_damage/scorch.json');
if (process.argv.includes('--check')) {
  const stale = [[OUT_LAYOUT, layoutText], [OUT_CSC, csc], [OUT_SCORCH, scorchText]].filter(([p, t]) => !fs.existsSync(p) || fs.readFileSync(p, 'utf8').replace(/\r\n/g, '\n') !== t);
  if (stale.length) { for (const [p] of stale) console.log('STALE ' + path.relative(ROOT, p)); console.log('WAR DAMAGE LAYOUT STALE: run node tools/war_damage/layout.js'); process.exit(1); }
  console.log(`WAR DAMAGE LAYOUT OK (fresh): ${JSON.stringify(totals)}`);
} else {
  const stage = process.env.TOD_WAR_STAGE;
  const outL = stage ? path.join(stage, 'layout.json') : OUT_LAYOUT, outC = stage ? path.join(stage, '_tod_war_damage_data.csc') : OUT_CSC, outS = stage ? path.join(stage, 'scorch.json') : OUT_SCORCH;
  fs.mkdirSync(path.dirname(outL), { recursive: true });
  fs.writeFileSync(outL, layoutText); fs.writeFileSync(outC, csc); fs.writeFileSync(outS, scorchText);
  console.log(`WAR DAMAGE LAYOUT written${stage ? ' (staged)' : ''}: ${JSON.stringify(totals)}; ${Object.keys(scorchLabels).length} scorched map labels`);
}
