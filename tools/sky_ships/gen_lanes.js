'use strict';
// THE SKY FLEET's flight lanes (docs/192) - GENERATED from the live map, never typed.
//
//   node tools/sky_ships/gen_lanes.js           write scripts/zm/zm_tod2_cybercity/_tod_sky_lanes.csc + art/sky_ships/lanes.json
//   node tools/sky_ships/gen_lanes.js --check   rebuild in memory and FAIL if the committed .csc differs (the build gate)
//
// A lane is a straight PASS across the sealed sky box (ships fly far beyond its ends as scaled stand-ins).
// For every ship class it lists the altitude BANDS
// (the ship's origin z) where the WHOLE ship - its exported bounds from art/sky_ships/manifest.json, grown by
// MARGIN - clears every solid brush in map_source (measured with tools/convex_brush.js, the planes the
// compiler reads) and every KEEP_OUT box, and stays inside the umbra/sun volume the whole way, including
// the warp-in and warp-out points. Invisible player-clip brushes are ignored (a ship through one is not
// seen), the jump arc is a KEEP_OUT because a player flies there. Re-run after any geometry change; the
// build runs --check so a new wall can never end up inside a lane.
const fs = require('fs'), path = require('path');
const cb = require('../convex_brush.js');
const ROOT = path.resolve(__dirname, '..', '..');
const MAP = path.join(ROOT, 'map_source/zm/zm_tod2_cybercity.map');
const MANIFEST = path.join(ROOT, 'art/sky_ships/manifest.json');
const OUT_CSC = path.join(ROOT, 'scripts/zm/zm_tod2_cybercity/_tod_sky_lanes.csc');
const OUT_JSON = path.join(ROOT, 'art/sky_ships/lanes.json');
const FX_TABLES = path.join(ROOT, 'art/sky_ships/fx_tables.json');   // tools/sky_ships/gen_fx.py: flame buckets, star speeds
const SKY_BUILD = path.join(ROOT, 'tools/sky3d/build_city.py');      // session 22's sky: where the painted black holes are
const SKY_GDT = path.join(ROOT, 'source_data/tod_skybox.gdt');        // the sky's turn (skyRotation) + the SSI sun yaw

const MARGIN = 1500;          // no ship ever passes within this of a solid brush or a keep-out box
const EDGE = 200;             // and the whole ship stays this far inside the umbra/sun volume
const Z_FLOOR = 2500;         // never below the plaza's roofline
const MIN_BAND = 1200;        // an altitude band thinner than this is not worth a lane
const HEADING_STEP = 10;      // degrees; a lane is flown both ways, so 0..170
const OFFSET_STEP = 1000;     // units between parallel lanes
// Things that are not brushes but must stay clear (session 61, 2026-09-29): the crown -> tower jump arc
// (players fly through it) and the new transit hall. Grown by MARGIN like every brush.
const KEEP_OUT = [
  { name: 'jump arc (session 61)', lo: [-1500, 500, 19300], hi: [1500, 5800, 22200] },
  { name: 'transit hall (session 61)', lo: [-1660, -200, 19060], hi: [-460, 920, 19950] },   // grown 2026-09-29 (keel pendant + oculus jewels)
];
// The classes this generator serves, LOCKSTEP with _tod_sky_ships.csc (it asks for lanes by name).
const CLASSES = ['dreadnought', 'hauler', 'gunship', 'fighter'];
const MIN_LEN = { dreadnought: 7000, hauler: 9000, gunship: 10000, fighter: 12000 };
// A fighter wing is up to five ships in a V: the wing is wider and longer than one fighter.
const WING = { fighter: { back: 1800, side: 1500 } };

// HOW EACH CLASS FLIES (docs/192 s9, v2: user 2026-09-29 "they should be going across the sky like an airplane ...
// spawn in far away and then they move towards the tower. And then they fly away from the tower once they pass it").
// ONE table: the director reads it through the generated motion() and the lanes below are grown by it.
//   speed      cruise through the pass (units/s)            xs      far-approach scale: far out the ship moves at
//   spawn_px   how big it first appears (1080p, hfov 80.7)          speed*(1+d/xs), so it looms steadily, slows in
//   glide      descent before the pass, deg [min, max]              and speeds away (halves its distance every
//   climb      climb after the pass, deg [min, max]                 xs*ln2/speed s far out)
//   weave      [amplitude units, period s] side-to-side S-curve     bob     [amplitude, period] up and down
//   bank       deg of roll at the weave's extremes (into the turn)   sway_*  [deg, period] slow roll / pitch
//   first / gap / cap / wing   the schedule: first arrival (s), gap between arrivals [min, max] (s), live cap,
//                              ships per sortie [min, max] (a V wing for fighters)
//   worm       v3 (user 2026-09-29: "some of the spaceships should come through like a wormhole"): [% of flights that
//              ARRIVE through a rift, % that LEAVE through one, the rift's radius (units: the ship's / wing's cross-section),
//              the ship's size on screen where the rift opens (px at 1080p)]
//   hi         v4 THE HIGH LAYER (user 2026-09-30: "add more but at a higher altitude ... the sky filled up ... 1.5x more"):
//              a SECOND schedule per class { first, gap, cap } flown in the band ABOVE the low layer's (the director's
//              TOD_SKY_HI_ALT_* window, crossing nearly overhead); the low schedule is untouched, so this ADDS traffic.
//              Sized so the expected ships in the sky at once come to ~1.5x the v3 fleet (test_sky_ships.js prints both).
//   convoy     v4 [% of normal (non-rift) flights that lead a convoy, followers min, max, seconds astern]: the followers
//              fly the lead's exact path (fixed-path sorties, a little staggered) - a freight convoy / a patrol pair.
const MOTION = {
  dreadnought: { speed: 380, xs: 6000, spawn_px: 14, glide: [1, 4], climb: [2, 6], weave: [0, 30], bob: [40, 19], bank: 0,
                 sway_roll: [1.5, 22], sway_pitch: [0.6, 17], first: 20, gap: [30, 75], cap: 1, wing: [1, 1], worm: [40, 30, 4200, 70],
                 hi: { first: 60, gap: [90, 200], cap: 1 }, convoy: [0, 0, 0, 0] },
  hauler:      { speed: 520, xs: 5000, spawn_px: 14, glide: [1, 5], climb: [2, 7], weave: [60, 26], bob: [60, 13], bank: 3,
                 sway_roll: [2.5, 15], sway_pitch: [1.0, 11], first: 8, gap: [15, 45], cap: 2, wing: [1, 1], worm: [25, 20, 2000, 70],
                 hi: { first: 14, gap: [30, 90], cap: 1 }, convoy: [30, 1, 2, 16] },
  gunship:     { speed: 1000, xs: 4000, spawn_px: 12, glide: [2, 7], climb: [3, 9], weave: [260, 10], bob: [110, 7], bank: 14,
                 sway_roll: [0, 10], sway_pitch: [0, 10], first: 25, gap: [12, 35], cap: 2, wing: [1, 1], worm: [35, 30, 1900, 80],
                 hi: { first: 35, gap: [25, 70], cap: 1 }, convoy: [22, 1, 1, 7] },
  fighter:     { speed: 2200, xs: 3500, spawn_px: 10, glide: [3, 9], climb: [4, 12], weave: [300, 6.5], bob: [140, 5], bank: 32,
                 sway_roll: [0, 10], sway_pitch: [0, 10], first: 5, gap: [10, 30], cap: 2, wing: [3, 5], worm: [30, 25, 1900, 90],
                 hi: { first: 10, gap: [20, 60], cap: 1 }, convoy: [0, 0, 0, 0] },
};
// THE FLAMES (v3): each nozzle's drive kind (LOCKSTEP with gen_fx.py KINDS; the director's kind index is this order).
const KIND_ORDER = ['plasma_capital', 'plasma', 'fire', 'fire_heavy'];
function nozzleKind(ship, r) {
  if (ship === 'dreadnought') return r >= 250 ? 'plasma_capital' : 'plasma';
  if (ship === 'gunship') return 'plasma';
  if (ship === 'fighter') return 'fire';
  return 'fire_heavy';
}
// THE ASTEROIDS (v3): how often each rock is picked (the manifest's rocks, by key; they must sum to 100).
const ROCK_WEIGHT = { '1': 30, '2': 22, '3': 13, '4': 15, '5': 20 };
// THE BLACK HOLES' ROCKS (v3): how many orbit each painted black hole and which way round.
const HOLE_ROCKS = { gargantua: [9, 1], maelstrom: [6, -1] };   // v4: 1.5x (6 / 4 in v3)
const PX_RAD = (80.7 * Math.PI / 180) / 1920;      // one 1080p pixel at the in-game hfov, radians
// The extra clearance a class's motion needs around its lane: the weave sideways; the bob plus the wings dipping
// in a bank / roll sway plus the nose/tail in a pitch sway, vertically.
function motionGrow(c, r) {
  const M = MOTION[c], deg = Math.PI / 180;
  const half = r.half_width + (WING[c] ? WING[c].side : 0);
  return { side: M.weave[0], up: M.bob[0] + half * Math.sin((M.bank + M.sway_roll[0]) * deg) + Math.max(-r.bounds[0][0], r.bounds[1][0]) * Math.sin(M.sway_pitch[0] * deg) };
}

// THE SCALED STAND-IN (docs/192 s9): a ship beyond the sealed box is drawn at the same bearing, closer and smaller
// (distance x k, size x k: identical on screen). The director presses the stand-in against the box wall along
// the line of sight; it must never overlap a structure there, so every solid within SHELL of a side wall or of
// the top is listed (grown by BLOCK_GROW, merged into BLOCK_CELL buckets). A stand-in touching one is hidden that
// tick (the structure stands between the player and the far ship).
const SHELL = 7000, BLOCK_GROW = 400, BLOCK_CELL = 3000;

// THE FIRST-JUMP SALUTE (session 61's opening scene, _tod_jumppad.gsc + _tod_jump_title.csc, user 2026-09-29):
// the rider hangs at ~(0, 3300, 21800) looking due WEST at the dimmed sky sign; two of these gunships crash head-on
// in front of it at (-5879, 3390, 23190) (t 3.9; the WHITE-OUT is full from 3.97 to 4.32 s and clears through orange
// by ~5.47), the sign IGNITES (t 4.1, `tod_jump_title_ignite` to the flyer's client, inside the full white) and the
// hold runs to t 7.3 (`tod_jump_title_end`, also sent at once on any cut). Final beats from session 61's
// _tod_jump_title.csc / _tod_jumppad.gsc. Both flights spawn AT IGNITE, under the white-out, so neither pops in:
//   reveal_high  a fighter wing crossing the blazing sign north -> south, high and BEHIND the crash smoke
//                (x -9500, z 26000), entering the frame's right third and passing its centre ~2 s after ignite;
//   reveal_low   a hauler far away near the horizon left of the sign, already approaching: it passes the tower
//                about half a minute after the rider lands. Its lane is a generated hauler lane (see build()).
// v3 (61's longer first jump, 2026-09-29 17:05: ignite 4.8, the sign revealed ~7.2, the hold to 9.8, the swing back at
// 10.3; the user plays at ~104 hfov): the salute spawns SALUTE_DELAY (1.6 s) after ignite, when the white-out is long
// gone, so the wing starts OUTSIDE even a 104-degree frame (approach 8,100) and crosses the sign ~2.3 s later, in the
// hold; the hauler starts ~9 px far over the horizon.
const REVEAL_CAM = [0, 2713, 21952];                // the rider at 8.5 s (61's solve_scene.js)
const REVEAL_HIGH = { cls: 'fighter', a: [-9500, 9500], b: [-9500, -11000], z: 26000, speed: 4800, approach: 8100, glide: 0, climb: 4 };
const REVEAL_LOW = { cls: 'hauler', heading: [3, 20], zwant: [22800, 27000], approach_px: 9, glide: 3, climb: 4 };

function readMap() {
  const txt = fs.readFileSync(MAP, 'utf8');
  const boxes = []; let volume = null;
  let depth = 0, cls = null, buf = [], inBrush = false;
  for (const ln of txt.split('\n')) {
    const s = ln.trim();
    if (s === '{') { depth++; if (depth === 1) cls = null; if (depth === 2) { buf = []; inBrush = true; } continue; }
    if (s === '}') {
      if (depth === 2 && inBrush) {
        inBrush = false;
        const planes = cb.readPlanes(buf.join('\n'));
        if (planes.length) {
          let h = null; try { h = cb.hull(planes); } catch (e) { h = null; }
          if (h) {
            if (cls === 'umbra_volume') volume = { lo: h.lo, hi: h.hi };
            else if ((cls === 'worldspawn' || cls === 'script_brushmodel') &&
                     !planes.every(p => p.mat === 'sky' || /^clip/.test(p.mat))) boxes.push({ lo: h.lo, hi: h.hi });
          }
        }
      }
      depth--; continue;
    }
    if (depth === 1) { const m = s.match(/^"classname" "([^"]+)"/); if (m) cls = m[1]; }
    else if (depth >= 2 && inBrush) buf.push(ln);
  }
  if (!volume) throw new Error('no umbra_volume in the map: the lanes need the sealed volume');
  return { boxes, volume };
}

// Does the rectangle (segment a->b grown by `half` sideways and `ext` along it) overlap an axis-aligned box
// in XY? Separating axes: the box's x/y and the rectangle's along/across.
function rectHitsBox(a, b, half, ext, lo, hi) {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
  const ux = dx / L, uy = dy / L, vx = -uy, vy = ux;
  const cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2, hl = L / 2 + ext;
  const corners = [[hl, half], [hl, -half], [-hl, half], [-hl, -half]].map(([p, q]) => [cx + ux * p + vx * q, cy + uy * p + vy * q]);
  const rx0 = Math.min(...corners.map(c => c[0])), rx1 = Math.max(...corners.map(c => c[0]));
  const ry0 = Math.min(...corners.map(c => c[1])), ry1 = Math.max(...corners.map(c => c[1]));
  if (rx1 < lo[0] || rx0 > hi[0] || ry1 < lo[1] || ry0 > hi[1]) return false;
  const bc = [[lo[0], lo[1]], [hi[0], lo[1]], [lo[0], hi[1]], [hi[0], hi[1]]];
  for (const [ax, ay, lim] of [[ux, uy, hl], [vx, vy, half]]) {
    const c = cx * ax + cy * ay;
    const ps = bc.map(([x, y]) => x * ax + y * ay);
    if (Math.max(...ps) < c - lim || Math.min(...ps) > c + lim) return false;
  }
  return true;
}

function subtract(bands, lo, hi) {
  const out = [];
  for (const [a, b] of bands) {
    if (hi <= a || lo >= b) { out.push([a, b]); continue; }
    if (lo > a) out.push([a, lo]);
    if (hi < b) out.push([hi, b]);
  }
  return out;
}


function segDist(p, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy;
  const t = L2 > 0 ? Math.min(1, Math.max(0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2)) : 0;
  return Math.hypot(a[0] + dx * t - p[0], a[1] + dy * t - p[1]);
}

// Solids within SHELL of a side wall or of the top, grown and merged: what a stand-in must never overlap.
function makeBlockers(obst, volume) {
  const near = obst.filter(o => {
    const dx = Math.min(o.lo[0] - volume.lo[0], volume.hi[0] - o.hi[0]);
    const dy = Math.min(o.lo[1] - volume.lo[1], volume.hi[1] - o.hi[1]);
    return Math.min(dx, dy, volume.hi[2] - o.hi[2]) < SHELL;
  });
  const buckets = new Map();
  for (const o of near) {
    const lo = o.lo.map(v => v - BLOCK_GROW), hi = o.hi.map(v => v + BLOCK_GROW);
    const key = [0, 1, 2].map(i => Math.floor((lo[i] + hi[i]) / 2 / BLOCK_CELL)).join(',');
    const b = buckets.get(key);
    if (!b) buckets.set(key, { lo: lo.slice(), hi: hi.slice() });
    else for (let i = 0; i < 3; i++) { b.lo[i] = Math.min(b.lo[i], lo[i]); b.hi[i] = Math.max(b.hi[i], hi[i]); }
  }
  const vol = x => (x.hi[0] - x.lo[0]) * (x.hi[1] - x.lo[1]) * (x.hi[2] - x.lo[2]);
  const list = [...buckets.values()];
  for (let merged = true; merged;) {                      // merge overlapping buckets while the union stays tight
    merged = false;
    for (let i = 0; i < list.length && !merged; i++) for (let j = i + 1; j < list.length && !merged; j++) {
      const a = list[i], b = list[j];
      if (![0, 1, 2].every(k => a.lo[k] <= b.hi[k] && b.lo[k] <= a.hi[k])) continue;
      const u = { lo: [0, 1, 2].map(k => Math.min(a.lo[k], b.lo[k])), hi: [0, 1, 2].map(k => Math.max(a.hi[k], b.hi[k])) };
      if (vol(u) <= 1.6 * (vol(a) + vol(b))) { list[i] = u; list.splice(j, 1); merged = true; }
    }
  }
  return { list: list.map(b => ({ lo: b.lo.map(Math.floor), hi: b.hi.map(Math.ceil) })), near };
}

// A class's clearance footprint along a path (the ship, its wing and its motion).
function dims(c, r) {
  const g = motionGrow(c, r);
  return { back: -r.bounds[0][0] + (WING[c] ? WING[c].back : 0), front: r.bounds[1][0],
           half: r.half_width + (WING[c] ? WING[c].side : 0) + g.side,
           zmin: r.bounds[0][2] - MARGIN - g.up, zmax: r.bounds[1][2] + MARGIN + g.up, up: g.up };
}

// The rocks from the export (06_export.py): [models, radius, veins, weight].
function manifestRocks(manifest) {
  const rocks = (manifest.rocks || []).slice().sort((a, b) => a.rock.localeCompare(b.rock));
  if (!rocks.length) throw new Error('manifest has no rocks (run tools/sky_ships/10_asteroids.py + 06_export.py)');
  let sum = 0;
  const out = rocks.map(r => {
    const w = ROCK_WEIGHT[r.rock];
    if (w === undefined) throw new Error('no ROCK_WEIGHT for rock ' + r.rock);
    sum += w;
    return { models: r.models, radius: r.radius, veins: !!r.veins, weight: w };
  });
  if (sum !== 100) throw new Error('ROCK_WEIGHT must sum to 100 over the exported rocks, not ' + sum);
  return out;
}

// THE PAINTED BLACK HOLES, where the game shows them. The sky's centre column faces yaw -(SSI sun yaw + skyRotation)
// (61 + 22, docs/196 s3: the engine's own sky shader); the sign is at azimuth 0 there, and a body at azimuth A (docs/166:
// + = image right) sits at yaw S - A, elevation unchanged. The disc: build_city.py's own frame - its normal tilted from
// face-on (-dh) toward image-up by `tilt`, its axes image-right and normal x right.
function skyHoles() {
  const py = fs.readFileSync(SKY_BUILD, 'utf8');
  const gdt = fs.readFileSync(SKY_GDT, 'utf8');
  const block = name => {
    const m = gdt.match(new RegExp('"' + name + '" \\( "[a-z]+\\.gdf" \\)\\s*\\{([\\s\\S]*?)\\n\\t\\}'));
    if (!m) throw new Error('no ' + name + ' in tod_skybox.gdt');
    return m[1];
  };
  const field = (b, k) => { const m = b.match(new RegExp('"' + k + '" "([^"]*)"')); if (!m) throw new Error('no ' + k); return +m[1]; };
  const rot = field(block('mtl_skybox_tod_cybercity'), 'skyRotation');
  const sun = field(block('tod_ssi_cybercity'), 'yaw');
  const S = ((-(sun + rot)) % 360 + 360) % 360;
  const D2R = Math.PI / 180, holes = [];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const norm = v => { const l = Math.hypot(...v); return v.map(x => x / l); };
  for (const m of py.matchAll(/dict\(kind='hole', name='(\w+)', az=(-?[\d.]+), el=(-?[\d.]+), r=([\d.]+), tilt=([\d.]+)/g)) {
    const [, name, az, el, r, tilt] = m;
    if (!HOLE_ROCKS[name]) throw new Error('no HOLE_ROCKS for the black hole ' + name);
    const yaw = (S - +az) * D2R, e = +el * D2R, tl = +tilt * D2R;
    const dh = [Math.cos(e) * Math.cos(yaw), Math.cos(e) * Math.sin(yaw), Math.sin(e)];
    const up = [-Math.sin(e) * Math.cos(yaw), -Math.sin(e) * Math.sin(yaw), Math.cos(e)];
    const right = norm(cross(dh, up));
    const nrm = norm(dh.map((x, i) => -x * Math.cos(tl) + up[i] * Math.sin(tl)));
    const e2 = norm(cross(nrm, right));
    holes.push({ name, az: +az, el: +el, r: +r, tilt: +tilt, yaw: ((S - +az) % 360 + 360) % 360, sign_yaw: S, dir: dh, e1: right, e2,
                 count: HOLE_ROCKS[name][0], spin: HOLE_ROCKS[name][1] });
  }
  if (holes.length !== Object.keys(HOLE_ROCKS).length) throw new Error('expected ' + Object.keys(HOLE_ROCKS).join('/') + ' in build_city.py, found ' + holes.map(h => h.name));
  return holes;
}

function build() {
  const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  const ship = {};
  for (const r of manifest.ships) ship[r.ship] = r;
  for (const c of CLASSES) if (!ship[c]) throw new Error('manifest has no ' + c + ' (run tools/sky_ships/06_export.py)');
  const { boxes, volume } = readMap();
  const obst = boxes.concat(KEEP_OUT.map(k => ({ lo: k.lo, hi: k.hi })));
  const V0 = [volume.lo[0] + EDGE, volume.lo[1] + EDGE], V1 = [volume.hi[0] - EDGE, volume.hi[1] - EDGE];
  const lanes = [];
  let id = 0;
  for (let hd = 0; hd < 180; hd += HEADING_STEP) {
    const ux = Math.cos(hd * Math.PI / 180), uy = Math.sin(hd * Math.PI / 180), vx = -uy, vy = ux;
    for (let off = -11000; off <= 11000; off += OFFSET_STEP) {
      // The full chord of the sealed box along this line.
      let t0 = -1e9, t1 = 1e9;
      const px = vx * off, py = vy * off;
      for (const [p, u, a, b] of [[px, ux, V0[0], V1[0]], [py, uy, V0[1], V1[1]]]) {
        if (Math.abs(u) < 1e-9) { if (p < a || p > b) { t0 = 1; t1 = 0; } continue; }
        let s0 = (a - p) / u, s1 = (b - p) / u; if (s0 > s1) [s0, s1] = [s1, s0];
        t0 = Math.max(t0, s0); t1 = Math.min(t1, s1);
      }
      if (t1 - t0 < 4000) continue;
      const entry = { id: id++, heading: hd, offset: off, per: {} };
      for (const c of CLASSES) {
        const r = ship[c];
        const { back, front, half, zmin, zmax, up } = dims(c, r);
        // Keep the whole ship (its wing and its weave) inside the box at both ends: shrink the chord so the
        // origin never goes where the bow or the stern would leave the volume. Beyond the ends the director
        // draws the SCALED STAND-IN (the far approach and the departure).
        const reach = Math.max(back, front);
        let s0 = t0 + reach, s1 = t1 - reach;
        const inside = (t) => {
          const x = px + ux * t, y = py + uy * t;
          for (const [p, q] of [[front, half], [front, -half], [-back, half], [-back, -half]]) {
            const cx = x + ux * p + vx * q, cy = y + uy * p + vy * q;
            if (cx < V0[0] || cx > V1[0] || cy < V0[1] || cy > V1[1]) return false;
          }
          return true;
        };
        while (s0 < s1 && !inside(s0)) s0 += 100;
        while (s1 > s0 && !inside(s1)) s1 -= 100;
        if (s1 - s0 < MIN_LEN[c]) continue;
        const a = [px + ux * s0, py + uy * s0], b = [px + ux * s1, py + uy * s1];
        // Altitude bands for the ORIGIN: inside the volume (with the bob / bank / sway), above the plaza, clear.
        let bands = [[Math.max(Z_FLOOR, volume.lo[2] + EDGE - r.bounds[0][2] + up), volume.hi[2] - EDGE - r.bounds[1][2] - up]];
        for (const o of obst) {
          if (!rectHitsBox(a, b, half + MARGIN, reach + MARGIN, o.lo, o.hi)) continue;
          bands = subtract(bands, o.lo[2] - zmax, o.hi[2] - zmin);
          if (!bands.length) break;
        }
        bands = bands.filter(([lo, hi]) => hi - lo >= MIN_BAND).map(([lo, hi]) => [Math.ceil(lo), Math.floor(hi)]);
        if (bands.length) entry.per[c] = { a: a.map(Math.round), b: b.map(Math.round), bands };
      }
      if (Object.keys(entry.per).length) lanes.push(entry);
    }
  }
  const blk = makeBlockers(boxes, volume);                 // solids only: the keep-outs are air

  // THE REVEAL. High: a fixed fighter path, checked clear like a lane where it is inside the box.
  const reveal = {};
  {
    const R = REVEAL_HIGH, c = R.cls, r = ship[c], d = dims(c, r);
    const a = R.a, b = R.b, z = R.z;
    for (const o of obst) {
      if (!rectHitsBox(a, b, d.half + MARGIN, Math.max(d.back, d.front) + MARGIN, o.lo, o.hi)) continue;
      if (z + d.zmax > o.lo[2] && z + d.zmin < o.hi[2]) throw new Error('REVEAL high path is blocked by a brush at ' + o.lo.map(Math.round) + ' .. ' + o.hi.map(Math.round));
    }
    if (z + r.bounds[1][2] + d.up > volume.hi[2] - EDGE) throw new Error('REVEAL high path too high');
    reveal.reveal_high = { ship: c, a: [a[0], a[1], z], b: [b[0], b[1], z], speed: R.speed, approach: R.approach, glide: R.glide, climb: R.climb };
  }
  {
    // Low: the generated hauler lane that best fits the shot - heading ~10 deg (so the far approach sits ~10 deg left
    // of the sign, low over the horizon), flown west -> east, passing the tower ~7,000 units out, at a band that
    // covers the rider's altitude band. Its a/b come from a real lane, so it is clear by construction.
    const R = REVEAL_LOW, c = R.cls;
    let best = null;
    for (const l of lanes) {
      const p = l.per[c];
      if (!p || l.heading < R.heading[0] || l.heading > R.heading[1]) continue;
      const band = p.bands.find(([lo, hi]) => lo <= R.zwant[1] && hi >= R.zwant[0]);
      if (!band) continue;
      const z = Math.max(band[0], Math.min(band[1], (R.zwant[0] + R.zwant[1]) / 2));
      const dd = segDist([0, 0], p.a, p.b);
      const score = Math.abs(l.heading - 10) * 400 + Math.abs(dd - 7000);
      if (!best || score < best.score) best = { score, a: p.a, b: p.b, z: Math.round(z) };
    }
    if (!best) throw new Error('REVEAL low: no hauler lane with heading ' + R.heading + ' and a band in ' + R.zwant);
    const r = ship[c], approach = Math.round((r.bounds[1][0] - r.bounds[0][0]) / (R.approach_px * PX_RAD));
    reveal.reveal_low = { ship: c, a: [best.a[0], best.a[1], best.z], b: [best.b[0], best.b[1], best.z], speed: MOTION[c].speed,
                          approach, glide: R.glide, climb: R.climb };
  }
  return { lanes, volume, obstacles: obst.length, boxes: obst, reveal, ship, blockers: blk.list, near: blk.near, manifest_sha: manifest.gdt_sha256,
           rocks: manifestRocks(manifest), holes: skyHoles(), fx: JSON.parse(fs.readFileSync(FX_TABLES, 'utf8')) };
}

function emitCsc(res) {
  const L = [];
  const v = a => '( ' + a.map(Math.round).join(', ') + ' )';
  L.push('// GENERATED by tools/sky_ships/gen_lanes.js from map_source + art/sky_ships/manifest.json - DO NOT HAND-EDIT.');
  L.push('// THE SKY FLEET flight data (docs/192). Lanes: array( a, b, bands ) where a/b are the ends of a straight');
  L.push('// pass (the ship ORIGIN, z = 0; fly either way) and bands = [ ( zlo, zhi, 0 ), ... ] the origin altitudes');
  L.push('// where the whole ship - with its wing and its weave / bob / bank - clears every brush and keep-out box by');
  L.push('// ' + MARGIN + ' units and stays inside the sealed volume. Beyond a lane\'s ends a ship is drawn as a scaled');
  L.push('// stand-in (blockers() lists what it must never overlap). The build re-tests the committed data.');
  L.push('');
  L.push('#namespace tod_sky_lanes;');
  L.push('');
  L.push('function volume_lo() { return ' + v(res.volume.lo) + '; }');
  L.push('function volume_hi() { return ' + v(res.volume.hi) + '; }');
  L.push('');
  L.push('// Each ship class exported size (art/sky_ships/manifest.json): array( back, front, half_width, zlo, zhi ).');
  L.push('function size( ship )');
  L.push('{');
  for (const c of CLASSES) {
    const r = res.ship[c];
    L.push('\tif ( ship == "' + c + '" ) return array( ' + [Math.round(-r.bounds[0][0]), Math.round(r.bounds[1][0]), Math.round(r.half_width), Math.round(r.bounds[0][2]), Math.round(r.bounds[1][2])].join(', ') + ' );');
  }
  L.push('\treturn array( 1000, 1000, 500, -200, 200 );');
  L.push('}');
  L.push('');
  L.push('// How each class flies (gen_lanes.js MOTION; docs/192 s9). approach = where it first appears, the distance at');
  L.push('// which it is spawn_px pixels long at 1080p. v4: hi_* = the high layer\'s schedule, convoy_* = followers on the');
  L.push('// lead\'s path (docs/192 s12).');
  L.push('function motion( ship )');
  L.push('{');
  L.push('\tm = SpawnStruct();');
  for (const c of CLASSES) {
    const M = MOTION[c], r = res.ship[c];
    const approach = Math.round((r.bounds[1][0] - r.bounds[0][0]) / (M.spawn_px * PX_RAD));
    L.push('\tif ( ship == "' + c + '" )');
    L.push('\t{');
    L.push('\t\tm.speed = ' + M.speed + '; m.xs = ' + M.xs + '; m.approach = ' + approach + ';');
    L.push('\t\tm.glide_min = ' + M.glide[0] + '; m.glide_max = ' + M.glide[1] + '; m.climb_min = ' + M.climb[0] + '; m.climb_max = ' + M.climb[1] + ';');
    L.push('\t\tm.weave_a = ' + M.weave[0] + '; m.weave_t = ' + M.weave[1] + '; m.bob_a = ' + M.bob[0] + '; m.bob_t = ' + M.bob[1] + '; m.bank = ' + M.bank + ';');
    L.push('\t\tm.sway_roll = ' + M.sway_roll[0] + '; m.sway_roll_t = ' + M.sway_roll[1] + '; m.sway_pitch = ' + M.sway_pitch[0] + '; m.sway_pitch_t = ' + M.sway_pitch[1] + ';');
    L.push('\t\tm.first = ' + M.first + '; m.gap_min = ' + M.gap[0] + '; m.gap_max = ' + M.gap[1] + '; m.cap = ' + M.cap + '; m.wing_min = ' + M.wing[0] + '; m.wing_max = ' + M.wing[1] + ';');
    const wormApproach = Math.round((r.bounds[1][0] - r.bounds[0][0]) / (M.worm[3] * PX_RAD));
    L.push('\t\tm.worm_in = ' + M.worm[0] + '; m.worm_out = ' + M.worm[1] + '; m.worm_r = ' + M.worm[2] + '; m.worm_approach = ' + wormApproach + ';');
    L.push('\t\tm.hi_first = ' + M.hi.first + '; m.hi_gap_min = ' + M.hi.gap[0] + '; m.hi_gap_max = ' + M.hi.gap[1] + '; m.hi_cap = ' + M.hi.cap + ';');
    L.push('\t\tm.convoy_pct = ' + M.convoy[0] + '; m.convoy_min = ' + M.convoy[1] + '; m.convoy_max = ' + M.convoy[2] + '; m.convoy_gap = ' + M.convoy[3] + ';');
    L.push('\t}');
  }
  L.push('\treturn m;');
  L.push('}');
  L.push('');
  L.push('// Blinking-light anchors in ship space (art/sky_ships/manifest.json): array( x, y, z, kind ), kind "s" = white');
  L.push('// strobe, "b" = red beacon.');
  L.push('function lights( ship )');
  L.push('{');
  L.push('\tl = [];');
  for (const c of CLASSES) {
    L.push('\tif ( ship == "' + c + '" )');
    L.push('\t{');
    for (const [x, y, z, k] of res.ship[c].lights || []) L.push('\t\tl[ l.size ] = array( ' + [x, y, z].map(Math.round).join(', ') + ', "' + k + '" );');
    L.push('\t}');
  }
  L.push('\treturn l;');
  L.push('}');
  L.push('');
  const f3 = v => '( ' + v.map(x => (Math.round(x * 1e6) / 1e6).toString()).join(', ') + ' )';
  L.push('// v3 THE FLAMES: each nozzle TAG (06_export.py: tag_eng_<i>, turned aft) = array( tag, radius, kind, main, ref, x, y, z ):');
  L.push('// kind ' + KIND_ORDER.map((k, i) => i + ' ' + k).join(' / ') + ' (gen_fx.py), main = a glint when far, ref = the');
  L.push('// kind reference radius (its bucket 0).');
  L.push('function nozzles( ship )');
  L.push('{');
  L.push('\tn = [];');
  for (const c of CLASSES) {
    const nz = res.ship[c].nozzles || [];
    const rmax = Math.max(...nz.map(n => n[3]));
    L.push('\tif ( ship == "' + c + '" )');
    L.push('\t{');
    nz.forEach(([x, y, z, r], i) => {
      const kind = nozzleKind(c, r), ref = res.fx.kinds[kind];
      if (ref === undefined) throw new Error('fx_tables has no kind ' + kind);
      L.push('\t\tn[ n.size ] = array( "tag_eng_' + i + '", ' + r + ', ' + KIND_ORDER.indexOf(kind) + ', ' + (r >= 0.6 * rmax ? 1 : 0) + ', ' + ref + ', ' + [x, y, z].map(v => Math.round(v)).join(', ') + ' );');
    });
    L.push('\t}');
  }
  L.push('\treturn n;');
  L.push('}');
  L.push('');
  L.push('// v3 THE ASTEROIDS (10_asteroids.py + 06_export.py): array( models, bounding radius, veins, pick weight % ).');
  L.push('function rocks()');
  L.push('{');
  L.push('\tr = [];');
  for (const k of res.rocks) L.push('\tr[ r.size ] = array( array( ' + k.models.map(m => '"' + m + '"').join(', ') + ' ), ' + k.radius + ', ' + (k.veins ? 1 : 0) + ', ' + k.weight + ' );');
  L.push('\treturn r;');
  L.push('}');
  L.push('');
  L.push('// v3 THE BLACK HOLES: the painted holes where the game shows them (the sign at yaw ' + res.holes[0].sign_yaw + ' = -(SSI sun yaw + skyRotation);');
  L.push('// a body at azimuth A sits at yaw sign - A): array( centre dir, shadow radius deg, disc axis 1, disc axis 2, rocks,');
  L.push('// spin, name ).');
  L.push('function holes()');
  L.push('{');
  L.push('\th = [];');
  for (const h of res.holes)
    L.push('\th[ h.size ] = array( ' + f3(h.dir) + ', ' + h.r + ', ' + f3(h.e1) + ', ' + f3(h.e2) + ', ' + h.count + ', ' + h.spin + ', "' + h.name + '" );   // az ' + h.az + ' -> yaw ' + h.yaw + ', el ' + h.el);
  L.push('\treturn h;');
  L.push('}');
  L.push('');
  L.push('// v3 SHOOTING STARS + FIREBALLS: the runner speeds / lives baked into their effects (gen_fx.py STARS / FIREBALL).');
  L.push('function star_speed( v )');
  L.push('{');
  ['a', 'b', 'c'].forEach((k, i) => L.push('\tif ( v == ' + i + ' ) return ' + res.fx.stars[k].speed + ';'));
  L.push('\treturn ' + res.fx.stars.a.speed + ';');
  L.push('}');
  L.push('function star_secs( v )');
  L.push('{');
  ['a', 'b', 'c'].forEach((k, i) => L.push('\tif ( v == ' + i + ' ) return ' + res.fx.stars[k].life_ms / 1000 + ';'));
  L.push('\treturn ' + res.fx.stars.a.life_ms / 1000 + ';');
  L.push('}');
  L.push('function ball_speed() { return ' + res.fx.fireball.speed + '; }');
  L.push('function ball_secs() { return ' + res.fx.fireball.life_ms / 1000 + '; }');
  L.push('');
  L.push('// Solids near the box walls a scaled stand-in must never overlap: array( lo, hi ).');
  L.push('function blockers()');
  L.push('{');
  L.push('\tb = [];');
  for (const b of res.blockers) L.push('\tb[ b.size ] = array( ' + v(b.lo) + ', ' + v(b.hi) + ' );');
  L.push('\treturn b;');
  L.push('}');
  L.push('');
  L.push('// The first-jump reveal flights (session 61\'s scene): fixed, checked paths.');
  for (const [key, r] of Object.entries(res.reveal)) {
    L.push('function ' + key + '()');
    L.push('{');
    L.push('\ts = SpawnStruct();');
    L.push('\ts.ship = "' + r.ship + '"; s.a = ' + v(r.a) + '; s.b = ' + v(r.b) + ';');
    L.push('\ts.speed = ' + r.speed + '; s.approach = ' + r.approach + '; s.glide = ' + r.glide + '; s.climb = ' + r.climb + ';');
    L.push('\treturn s;');
    L.push('}');
  }
  L.push('');
  for (const c of CLASSES) {
    const rows = res.lanes.filter(l => l.per[c]);
    L.push('function ' + c + '()');
    L.push('{');
    L.push('\tl = [];');
    for (const l of rows) {
      const p = l.per[c];
      const bands = p.bands.map(([lo, hi]) => '( ' + lo + ', ' + hi + ', 0 )').join(', ');
      L.push('\tl[ l.size ] = array( ( ' + p.a[0] + ', ' + p.a[1] + ', 0 ), ( ' + p.b[0] + ', ' + p.b[1] + ', 0 ), array( ' + bands + ' ) );');
    }
    L.push('\treturn l;');
    L.push('}');
    L.push('');
  }
  return L.join('\n');
}

// test_sky_ships.js requires this file for the map reader and the tables; only a direct run generates / checks.
module.exports = { readMap, rectHitsBox, makeBlockers, MOTION, CLASSES, KEEP_OUT, MARGIN, EDGE, PX_RAD, WING, REVEAL_CAM, KIND_ORDER, skyHoles };
if (require.main !== module) return;
const res = build();
const csc = emitCsc(res);
const counts = Object.fromEntries(CLASSES.map(c => [c, res.lanes.filter(l => l.per[c]).length]));
// THE GATE RE-TESTS WHAT THE GAME WILL FLY, not whether the file is byte-fresh: other sessions change the map all
// the time, and an unrelated wall must not fail their build. The COMMITTED lanes (and the reveal paths) are
// re-checked against the LIVE map's brushes + KEEP_OUT with the motion's clearance; every live solid near the box
// walls must still be covered by a committed blocker. Fail only on a real problem; a stale-but-safe file passes
// with a note (regenerate when convenient).
const DATA_FUNCS = ['size', 'motion', 'lights', 'nozzles', 'rocks', 'holes', 'star_speed', 'star_secs', 'ball_speed', 'ball_secs'];
function funcText(text, name) {
  const at = text.indexOf('function ' + name + '(');
  if (at < 0) return null;
  let i = text.indexOf('{', at), depth = 0;
  for (; i < text.length; i++) {
    if (text[i] === '{') depth++;
    else if (text[i] === '}' && --depth === 0) break;
  }
  return text.slice(at, i + 1);
}
function checkCommitted(text, fresh) {
  const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  const ship = {};
  for (const r of manifest.ships) ship[r.ship] = r;
  const { boxes, volume } = readMap();
  // SKY_LANES_EXTRA='[[x0,y0,z0],[x1,y1,z1]]' adds a fake wall: the negative control in test_sky_ships.js.
  const extra = process.env.SKY_LANES_EXTRA ? [JSON.parse(process.env.SKY_LANES_EXTRA)].map(([lo, hi]) => ({ lo, hi })) : [];
  const obst = boxes.concat(KEEP_OUT.map(k => ({ lo: k.lo, hi: k.hi })), extra);
  const V0 = [volume.lo[0] + EDGE, volume.lo[1] + EDGE], V1 = [volume.hi[0] - EDGE, volume.hi[1] - EDGE];
  const errs = [];
  let checked = 0;
  const test = (label, c, a, b, zlo, zhi, box) => {
    const r = ship[c], d = dims(c, r);
    const L = Math.hypot(b[0] - a[0], b[1] - a[1]), ux = (b[0] - a[0]) / L, uy = (b[1] - a[1]) / L, vx = -uy, vy = ux;
    if (box) {
      for (const [px, py, fw] of [[a[0], a[1], -d.back], [a[0], a[1], d.front], [b[0], b[1], -d.back], [b[0], b[1], d.front]])
        for (const q of [d.half, -d.half]) {
          const cx = px + ux * fw + vx * q, cy = py + uy * fw + vy * q;
          if (cx < V0[0] - 1 || cx > V1[0] + 1 || cy < V0[1] - 1 || cy > V1[1] + 1) { errs.push(label + ' leaves the sealed volume'); return; }
        }
      if (zlo + r.bounds[0][2] - d.up < volume.lo[2] + EDGE - 1 || zhi + r.bounds[1][2] + d.up > volume.hi[2] - EDGE + 1) { errs.push(label + ' leaves the volume vertically'); return; }
    }
    for (const o of obst) {
      if (!rectHitsBox(a, b, d.half + MARGIN, Math.max(d.back, d.front) + MARGIN, o.lo, o.hi)) continue;
      if (zhi + d.zmax > o.lo[2] && zlo + d.zmin < o.hi[2]) { errs.push(label + ' is now blocked by a brush at ' + o.lo.map(Math.round) + ' .. ' + o.hi.map(Math.round)); return; }
    }
    checked++;
  };
  for (const m of text.matchAll(/function (\w+)\(\)\s*\{\s*l = \[\];([\s\S]*?)return l;/g)) {
    if (!ship[m[1]]) { errs.push('lanes for an unknown class ' + m[1]); continue; }
    for (const r of m[2].matchAll(/array\( \( (-?\d+), (-?\d+), 0 \), \( (-?\d+), (-?\d+), 0 \), array\( ([^;]*) \) \);/g))
      for (const b of r[5].matchAll(/\( (-?\d+), (-?\d+), 0 \)/g))
        test(m[1] + ' lane (' + r[1] + ',' + r[2] + ')->(' + r[3] + ',' + r[4] + ') z ' + b[1] + '..' + b[2], m[1], [+r[1], +r[2]], [+r[3], +r[4]], +b[1], +b[2], true);
  }
  // reveal_high may start beyond the box (a stand-in); only its clearance is tested. reveal_low is a lane.
  for (const m of text.matchAll(/function (reveal_\w+)\(\)\s*\{\s*s = SpawnStruct\(\);\s*s\.ship = "(\w+)"; s\.a = \( (-?\d+), (-?\d+), (-?\d+) \); s\.b = \( (-?\d+), (-?\d+), (-?\d+) \);/g))
    test(m[1], m[2], [+m[3], +m[4]], [+m[6], +m[7]], +m[5], +m[5], m[1] !== 'reveal_high');
  // every live solid near the walls must sit inside a committed blocker (a new wall there would cut a stand-in)
  const committed = [...text.matchAll(/b\[ b\.size \] = array\( \( (-?\d+), (-?\d+), (-?\d+) \), \( (-?\d+), (-?\d+), (-?\d+) \) \);/g)]
    .map(m => ({ lo: [+m[1], +m[2], +m[3]], hi: [+m[4], +m[5], +m[6]] }));
  const live = makeBlockers(boxes.concat(extra), volume).near;
  let uncovered = 0;
  for (const o of live)
    if (!committed.some(b => [0, 1, 2].every(k => b.lo[k] <= o.lo[k] && o.hi[k] <= b.hi[k]))) {
      if (uncovered++ < 3) errs.push('a solid near the sky wall is not in blockers(): ' + o.lo.map(Math.round) + ' .. ' + o.hi.map(Math.round));
    }
  if (uncovered > 3) errs.push('... ' + (uncovered - 3) + ' more solids near the sky walls are not covered');
  // v3: the data that does NOT come from the map (sizes, motion, lights, nozzles, rocks, the black holes, star speeds) must be
  // exactly what the export / the fx / the sky say now: a stale copy flies flames on the wrong tags or rocks round empty sky.
  for (const name of DATA_FUNCS) {
    const a = funcText(text, name), b = funcText(fresh, name);
    if (a !== b) errs.push('tod_sky_lanes::' + name + '() is stale (the export, fx_tables.json or the sky moved): run node tools/sky_ships/gen_lanes.js');
  }
  return { errs, checked, blockers: committed.length };
}

if (process.argv.includes('--check')) {
  const have = fs.existsSync(OUT_CSC) ? fs.readFileSync(OUT_CSC, 'utf8').replace(/\r\n/g, '\n') : '';
  if (!have) { console.error('SKY LANES MISSING: run node tools/sky_ships/gen_lanes.js'); process.exit(1); }
  const { errs, checked, blockers } = checkCommitted(have, csc);
  if (errs.length) {
    console.error('SKY LANES BLOCKED by the live map (' + errs.length + '): ' + errs.slice(0, 5).join(' | ') + '\n  Fix: node tools/sky_ships/gen_lanes.js (then rebuild)');
    process.exit(1);
  }
  if (checked < 400) { console.error('SKY LANES: only ' + checked + ' committed lane bands'); process.exit(1); }
  const fresh = have === csc;
  console.log('SKY LANES OK: ' + checked + ' committed lane bands re-tested clear against ' + res.obstacles + ' live obstacles, ' + blockers + ' blockers cover every solid near the sky walls' +
    (fresh ? ' (file is fresh)' : ' (NOTE: the map changed since generation; regenerate when convenient: node tools/sky_ships/gen_lanes.js)'));
} else {
  fs.writeFileSync(OUT_CSC, csc);
  fs.writeFileSync(OUT_JSON, JSON.stringify({ margin: MARGIN, edge: EDGE, z_floor: Z_FLOOR, keep_out: KEEP_OUT, motion: MOTION, volume: res.volume, counts,
                                              blockers: res.blockers, reveal: res.reveal, lanes: res.lanes }, null, 1));
  fs.mkdirSync(path.join(ROOT, 'tmp/sky_ships'), { recursive: true });
  fs.writeFileSync(path.join(ROOT, 'tmp/sky_ships/obstacles.json'), JSON.stringify(res.boxes.map(b => [b.lo.map(Math.round), b.hi.map(Math.round)])));
  console.log('SKY LANES WRITTEN', JSON.stringify(counts), 'obstacles', res.obstacles, 'blockers', res.blockers.length,
              'reveal_low', JSON.stringify(res.reveal.reveal_low.a) + '->' + JSON.stringify(res.reveal.reveal_low.b));
}
