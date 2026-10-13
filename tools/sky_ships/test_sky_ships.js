'use strict';
// THE SKY FLEET gate (docs/192), v3. It runs the SHIPPING director functions from _tod_sky_ships.csc and the GENERATED
// flight data from _tod_sky_lanes.csc verbatim (tools/sky_ships/gsc_eval.js interprets the pure GSC) and flies whole
// flights, drifts, orbits and streaks from players all over the map, then checks every lockstep the feature depends on.
// Negative controls at the bottom prove each check can fail.
//   node tools/sky_ships/test_sky_ships.js
//
// SHIPS, per tick, every drawn ship (real or scaled stand-in) must:
//   INSIDE    keep all 8 box corners inside the sealed volume (a stand-in drawn past the walls would vanish);
//   BEARING   sit on the camera ray to the virtual ship, at scale = drawn distance / virtual distance;
//   CLEAR     when shown, never overlap a real solid of the live map (not just the blocker list);
//   SMOOTH    never jump (under 10 degrees of bearing and 25 % of scale between ticks) once fully out of a rift;
// and a flight must APPEAR and VANISH small (or out of / into a rift), approach from out of view (a rift arrival: IN
// view), pass the tower at full size, and end.
// FLAMES: every nozzle shows an effect that exists, a flame within 0.6..1.6x of the drawn nozzle (the size buckets +
//   their hysteresis), a glint only when the nozzle is too small on screen, and few swaps per flight.
// RIFTS: drawn inside the volume, never behind a structure, the right size bucket.
// ASTEROIDS: inside the volume on the camera ray, high in the sky, never popped in or out, visibly moving; the black
//   holes' rocks stay round their hole and are swallowed at its shadow.
// SHOOTING STARS: every streak inside the volume, above the skyline, clear of structures, 8..55 degrees long.
// v4 (user 2026-09-30: "add more but at a higher altitude ... 1.5x more"): THE HIGH LAYER's flights pass HI_ALT_MIN..HI_ALT_MAX
//   over the player and HI_NEAR..HI_FAR sideways (seen >= 29 degrees up) and obey every check above; CONVOY followers fly
//   the lead's path (fixed) clear and pop-free; SATELLITES stay high, on the ray, inside the box, slow and steady; the
//   schedules bring the expected ships in the sky at once to ~1.5x the v3 fleet.
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const { gscLoad, V } = require('./gsc_eval.js');
const G = require('./gen_lanes.js');
const ROOT = path.resolve(__dirname, '..', '..');
const rd = p => fs.readFileSync(path.join(ROOT, p), 'utf8');
const CSC_PATH = 'scripts/zm/zm_tod2_cybercity/_tod_sky_ships.csc';
const LANES_PATH = 'scripts/zm/zm_tod2_cybercity/_tod_sky_lanes.csc';
const csc = rd(CSC_PATH), lanesCsc = rd(LANES_PATH);
const manifest = JSON.parse(rd('art/sky_ships/manifest.json'));
const fxTables = JSON.parse(rd('art/sky_ships/fx_tables.json'));
const defines = Object.fromEntries([...csc.matchAll(/#define (\w+)\s+\(?\s*(-?[\d.]+)\s*\)?/g)].map(m => [m[1], +m[2]]));
const FX_DIR = path.join(ROOT, 'share/raw/fx/tod/sky');
const fxFiles = new Set(fs.readdirSync(FX_DIR).filter(f => f.endsWith('.efx')).map(f => 'tod/sky/' + f.slice(0, -4)));

let seed = 12345;
const rand = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);

// ---- load the shipping director + the generated data ----------------------------------------------------------
function load(cscText, opts = {}) {
  const g = gscLoad([['tod_sky_ships', cscText], ['tod_sky_lanes', lanesCsc]], defines, { random: rand, ...opts });
  const L = g.level;
  L.tod_sky_classes = [];
  L.tod_sky_lo = g.call('tod_sky_lanes::volume_lo', []).map(v => v + defines.TOD_SKY_EDGE); L.tod_sky_lo.isVec = true;
  L.tod_sky_hi = g.call('tod_sky_lanes::volume_hi', []).map(v => v - defines.TOD_SKY_EDGE); L.tod_sky_hi.isVec = true;
  L.tod_sky_blockers = opts.noBlockers ? [] : g.call('tod_sky_lanes::blockers', []);
  L.tod_sky_rocks = g.call('tod_sky_lanes::rocks', []);
  L.tod_sky_holes = g.call('tod_sky_lanes::holes', []);
  L.tod_sky_tag_ok = true;
  L.tod_sky_sat_def = g.call('ball_def', [4]);
  L.tod_sky_ents = [0];
  const adds = [...cscText.matchAll(/add_class\( "(\w+)", array\(([^)]*)\), "(\w+)" \);/g)];
  for (const m of adds) g.call('add_class', [m[1], [...m[2].matchAll(/"(\w+)"/g)].map(x => x[1]), m[3]]);
  return g;
}
const g = load(csc);
// Native identifier semantics, using the FIRST captured failure's camera and
// rock radius. This must execute before costly flight simulations so a local
// d/D collision cannot pass the pure-JS gate again.
function nativeSemanticsRegression() {
  const names = gscLoad([['probe', `
    function local_case(Input) {
      Total = iNpUt;
      foreach (Index, Item in array(2, 3)) total += ITEM + INDEX;
      TOTAL++;
      return tOtAl;
    }
    function key_case() {
      Bag = [];
      BAG["D"] = 7;
      bag["d"] = 11;
      return array(BaG["D"], BAG["d"]);
    }
  `]], {});
  assert.equal(names.call('local_case', [4]), 11, 'parameters/assignments/foreach/increment share case-insensitive local slots');
  assert.deepEqual(names.call('key_case', []), [7, 11], 'string keys must keep their spelling');

  const cam = V(192, 8868, 19452.1);
  const plan = { mid: V(0, 0, 1), across: V(1, 0, 0), axis: V(0, 1, 0), w: 0, secs: 100 };
  const rock = { pick: 1, ang: 1, oa: 0, oc: 0, a0: V(1, 2, 3), spin: V(0, 0, 0) };
  assert.equal(g.level.tod_sky_rocks[rock.pick][1], 655.6, 'captured first failure used the shard radius');
  const distance = 2 * 655.6 / 0.00001;
  const pose = g.call('rock_state', [plan, rock, 0, cam]);
  assert.equal(pose[0].isVec, true, 'zero-age rock must return a vector');
  assert.deepEqual([...pose[0]], [cam[0], cam[1], cam[2] + distance], 'zero-age placement retains camera and direction');
  assert(pose[0].every(Number.isFinite), 'zero-age placement must be finite');

  const fn = /function rock_state\([^)]*\)\s*\{[\s\S]*?\n\}/;
  const body = csc.match(fn)?.[0];
  assert(body && /\bdirection\b/.test(body) && /\bdistance\b/.test(body), 'rock_state must use distinct direction/distance locals');
  const collision = csc.replace(fn, body.replace(/\bdirection\b/g, 'd').replace(/\bdistance\b/g, 'D'));
  const bad = load(collision);
  assert.throws(() => bad.call('rock_state', [plan, rock, 0, cam]), error => {
    assert.match(error.message, /vector \+ not supported/);
    assert.deepEqual([...error.operands[0]], [...cam]);
    assert.equal(error.operands[1], distance * distance, 'd/D reproduces the native first-failure scalar');
    assert.equal(error.operands[1].toExponential(5), '1.71925e+16', 'matches console_mp.log first bad operand');
    return true;
  }, 'negative control must reject native d/D aliasing');
  console.log('PASS native local semantics: mixed-case bindings; zero-age shard at captured camera; d/D negative control reproduces 1.71925e+16');
}
nativeSemanticsRegression();
if (process.argv.includes('--native-semantics-only')) process.exit(0);
const classes = Object.keys(g.level.tod_sky_classes);
const offsets = (() => {                                             // sortie()'s formation slots, from the source
  const m = csc.match(/offsets = array\(((?:\s*\( -?\d+, -?\d+, -?\d+ \),?)+)\s*\);/);
  assert(m, 'sortie() formation offsets not found');
  return [...m[1].matchAll(/\( (-?\d+), (-?\d+), (-?\d+) \)/g)].map(x => V(+x[1], +x[2], +x[3]));
})();

const live = G.readMap();
const solids = live.boxes;
const TICK = defines.TOD_SKY_TICK;
const PX = G.PX_RAD;

function corners(def, ang, k, at) {
  const { f, r, u } = g.angleVectors(ang);
  const out = [];
  for (const cx of [def.front, -def.back]) for (const cy of [def.half, -def.half]) for (const cz of [def.zhi, def.zlo])
    out.push([0, 1, 2].map(j => at[j] + k * (f[j] * cx - r[j] * cy + u[j] * cz)));
  return out;
}
function obbHitsBox(def, ang, k, at, o) {
  const { f, r, u } = g.angleVectors(ang);
  const L = [-r[0], -r[1], -r[2]];
  const axes = [f, L, u];
  const he = [k * (def.front + def.back) / 2, k * def.half, k * (def.zhi - def.zlo) / 2];
  const c = [0, 1, 2].map(j => at[j] + k * (f[j] * (def.front - def.back) / 2 + u[j] * (def.zhi + def.zlo) / 2));
  const bc = [0, 1, 2].map(j => (o.lo[j] + o.hi[j]) / 2), bh = [0, 1, 2].map(j => (o.hi[j] - o.lo[j]) / 2);
  const d = [0, 1, 2].map(j => c[j] - bc[j]);
  const tests = [[1, 0, 0], [0, 1, 0], [0, 0, 1], ...axes];
  for (const a of axes) for (const e of [[1, 0, 0], [0, 1, 0], [0, 0, 1]]) tests.push([a[1] * e[2] - a[2] * e[1], a[2] * e[0] - a[0] * e[2], a[0] * e[1] - a[1] * e[0]]);
  for (const n of tests) {
    const ln = Math.hypot(...n);
    if (ln < 1e-9) continue;
    const ra = axes.reduce((sum, a, i) => sum + he[i] * Math.abs(a[0] * n[0] + a[1] * n[1] + a[2] * n[2]), 0) / ln;
    const rb = (bh[0] * Math.abs(n[0]) + bh[1] * Math.abs(n[1]) + bh[2] * Math.abs(n[2])) / ln;
    if (Math.abs(d[0] * n[0] + d[1] * n[1] + d[2] * n[2]) / ln > ra + rb) return false;
  }
  return true;
}
const inVol = (gg, p, m = 1) => [0, 1, 2].every(j => p[j] >= gg.level.tod_sky_lo[j] - m && p[j] <= gg.level.tod_sky_hi[j] + m);
const pxLen = (def, k, drawn, cam) => (k * (def.front + def.back)) / Math.hypot(drawn[0] - cam[0], drawn[1] - cam[1], drawn[2] - cam[2]) / PX;
const BUCKETS = fxTables.buckets, WORM_B = fxTables.worm_buckets.map(b => b * fxTables.worm_r);

// A rift's checks: drawn inside the volume with its whole ball, not hidden, bucket within 0.7..1.42 of the drawn radius.
function checkRift(gg, rift, cam, errs, label) {
  const si = gg.call('stand_in', [rift.bdef, rift.pv, V(0, 0, 0), cam]);
  const k = si[1], at = si[0], R = rift.rad * k;
  if (![0, 1, 2].every(j => at[j] - R >= gg.level.tod_sky_lo[j] - 1 && at[j] + R <= gg.level.tod_sky_hi[j] + 1)) errs.push('RIFT ' + label + ' drawn outside the volume');
  if (si[2]) errs.push('RIFT ' + label + ' opened behind a structure');
  const want = WORM_B[rift.b], ratio = want / Math.max(R, 1e-6);
  if (ratio < 0.7 || ratio > 1.42) errs.push('RIFT ' + label + ' bucket ' + rift.b + ' (' + want + ') for a drawn radius ' + R.toFixed(0));
}

// Fly one whole flight exactly like sortie()'s loop (it calls the same functions in the same order), on a fixed tick.
function fly(gg, def, cam, fwd, fixed, stats, tier) {
  const errs = [];
  const plan = gg.call('flight_plan', [def, fixed, cam, fwd, cam, tier || 0]);
  if (!plan) return { errs: gg.level.tod_sky_plan_why === 'pops' ? [] : ['no lane for ' + def.name + ' at ' + cam], none: gg.level.tod_sky_plan_why };
  const p = plan.p;
  const sIn = -plan.approach;
  let sOut = p.len + plan.depart, worm_out = plan.worm_out, skipped = 0;
  const count = def.wing_min + Math.floor(rand() * (def.wing_max - def.wing_min + 1));
  const ships = [];
  for (let i = 0; i < count; i++) ships.push({ off: offsets[i], te: plan.worm_in ? -1 : -1000, tx: -1, gone: false, prev: null,
                                               nzb: def.nozzles.map(() => -1), nzk: def.nozzles.map(() => ''), swaps: 0 });
  let s = sIn, t = plan.worm_in ? -defines.TOD_SKY_WORM_OPEN : 0, ticks = 0, full = false, hidden = 0, first = null, last = null;
  let flames = 0, glints = 0, kmin = 1, rout = null;
  const timeline = [];
  if (plan.worm_in) checkRift(gg, plan.rin, cam, errs, 'arrival');
  while (true) {
    const tt = Math.max(t, 0);
    const ang = gg.call('path_pose', [p, s, tt])[1];
    if (worm_out && !rout && s >= sOut - gg.call('path_speed', [p, s]) * defines.TOD_SKY_WORM_LEAD) {
      rout = gg.call('rift_make', [def, gg.call('path_pose', [p, sOut, tt])[0], cam]);
      if (rout.hidden) { rout = null; worm_out = false; sOut = p.len + def.approach; skipped++; }   // sortie()'s WORM_SKIP
      else checkRift(gg, rout, cam, errs, 'departure');
    }
    let allIn = true;
    for (let i = 0; i < ships.length; i++) {
      const sh = ships[i];
      if (sh.gone) continue;
      const along = s + sh.off[0];
      let e;
      if (sh.te < -100) e = 1;
      else if (t >= 0 && along >= sIn) { if (sh.te < 0) sh.te = t; e = gg.call('smooth', [(t - sh.te) / defines.TOD_SKY_WORM_GROW]); }
      else e = 0;
      if (rout && along >= sOut) {
        if (sh.tx < 0) sh.tx = t;
        e = e * (1 - gg.call('smooth', [(t - sh.tx) / defines.TOD_SKY_WORM_SHRINK]));
        if (e <= 0.01) { sh.gone = true; continue; }
      }
      allIn = false;
      const org = gg.call('wing_pose', [p, s, tt, sh.off])[0];
      const si = gg.call('stand_in', [def, org, ang, cam]);
      const drawn = si[0], k = si[1], hid = si[2];
      kmin = Math.min(kmin, k);
      for (const c of corners(def, ang, k, drawn))
        if (!inVol(gg, c)) { errs.push('INSIDE ' + def.name + ' corner ' + c.map(Math.round) + ' k=' + k.toFixed(3)); break; }
      const dv = [0, 1, 2].map(j => org[j] - cam[j]), dd = [0, 1, 2].map(j => drawn[j] - cam[j]);
      const D = Math.hypot(...dv), R = Math.hypot(...dd);
      const cosang = (dv[0] * dd[0] + dv[1] * dd[1] + dv[2] * dd[2]) / (D * R);
      if (cosang < 1 - 1e-9 || Math.abs(k - R / D) > 1e-6) errs.push('BEARING ' + def.name + ' cos=' + cosang + ' k=' + k + ' R/D=' + R / D);
      const shown = !hid && e > 0.001;
      if (shown) {
        const cs = corners(def, ang, k, drawn);
        const lo = [0, 1, 2].map(j => Math.min(...cs.map(c => c[j]))), hi = [0, 1, 2].map(j => Math.max(...cs.map(c => c[j])));
        for (const o of solids)
          if (lo[0] < o.hi[0] && hi[0] > o.lo[0] && lo[1] < o.hi[1] && hi[1] > o.lo[1] && lo[2] < o.hi[2] && hi[2] > o.lo[2] &&
              obbHitsBox(def, ang, k, drawn, o)) {
            errs.push('CLEAR ' + def.name + ' k=' + k.toFixed(3) + ' drawn ' + drawn.map(Math.round) + ' overlaps a solid ' + o.lo.map(Math.round) + '..' + o.hi.map(Math.round));
            break;
          }
      } else if (hid) hidden++;
      if (sh.prev && e >= 1 && sh.prev[2] >= 1) {
        const [pd, pk] = sh.prev;
        const pv = [0, 1, 2].map(j => pd[j] - cam[j]);
        const c2 = (pv[0] * dd[0] + pv[1] * dd[1] + pv[2] * dd[2]) / (Math.hypot(...pv) * R);
        const turn = Math.acos(Math.min(1, c2)) * 180 / Math.PI;
        if (turn > 10) errs.push('SMOOTH ' + def.name + ' bearing jumped ' + turn.toFixed(2) + ' deg at s=' + Math.round(s));
        if (Math.abs(k - pk) / Math.max(pk, 1e-6) > 0.25) errs.push('SMOOTH ' + def.name + ' scale jumped ' + pk.toFixed(4) + ' -> ' + k.toFixed(4));
      }
      sh.prev = [drawn, k, e];
      // FLAMES
      const kd = k * Math.max(e, 0.02);
      for (let n = 0; n < def.nozzles.length; n++) {
        const nz = def.nozzles[n];
        let w = ['', -1];
        if (shown) w = gg.call('engine_want', [nz, kd, R, sh.nzb[n], true]);
        if (w[0] !== sh.nzk[n]) { if (w[0] !== '') sh.swaps++; sh.nzk[n] = w[0]; }
        sh.nzb[n] = w[1];
        if (w[0] === '') continue;
        if (!fxFiles.has(w[0])) errs.push('FLAME ' + def.name + ' names a missing effect ' + w[0]);
        if (w[1] >= 0) {
          flames++;
          const ratio = BUCKETS[w[1]] * nz[4] / (kd * nz[1]);
          if (ratio < 0.6 || ratio > 1.6) errs.push('FLAME ' + def.name + ' nozzle ' + n + ' bucket ' + w[1] + ' is ' + ratio.toFixed(2) + 'x the drawn nozzle');
          if (kd * nz[1] < R * defines.TOD_SKY_FLAME_MIN_RAD - 1e-9) errs.push('FLAME on a nozzle too small to show one');
        } else glints++;
      }
      if (i === 0) {
        if (!first && shown) first = { px: pxLen(def, kd, drawn, cam), dir: dd.map(v => v / R), t };
        if (shown) last = { px: pxLen(def, kd, drawn, cam) };
        if (pxLen(def, kd, drawn, cam) > 25 && timeline.length < 400) timeline.push(t.toFixed(1) + (shown ? 'S' : 'h') + pxLen(def, kd, drawn, cam).toFixed(0));
        if (k >= defines.TOD_SKY_FULL_K) full = true;
      }
    }
    if (t >= 0) s += gg.call('path_speed', [p, s]) * (plan.worm_in ? gg.call('worm_boost', [t]) : 1) * TICK;
    t += TICK;
    ticks++;
    if (rout ? allIn : s > sOut) break;
    if (ticks > 20000) { errs.push('a flight never ended'); break; }
  }
  const swaps = ships.reduce((a, sh) => a + sh.swaps, 0) / ships.length;
  // a nozzle steps through the 5 sizes coming in and going out, plus its far glint: 11 changes a flight; a flicker is dozens
  if (swaps > 14 * Math.max(1, def.nozzles.length)) errs.push('FLAME ' + def.name + ' swapped effects ' + swaps + ' times in one flight');
  if (stats) {
    const S = stats[def.name] = stats[def.name] || { flights: 0, secs: 0, full: 0, hidden: 0, ticks: 0, firstPx: 0, lastPx: 0, flames: 0, glints: 0, win: 0, wout: 0 };
    S.flights++; S.secs += t; S.full += full ? 1 : 0; S.hidden += hidden; S.ticks += ticks * count; S.flames += flames; S.glints += glints;
    S.win += plan.worm_in ? 1 : 0; S.wout += worm_out ? 1 : 0; S.skip = (S.skip || 0) + skipped;
    if (!plan.worm_in && first) S.firstPx = Math.max(S.firstPx, first.px);
    if (!worm_out && last) S.lastPx = Math.max(S.lastPx, last.px);
  }
  return { errs, first, last, full, secs: t, p, hidden, kmin, plan, worm_out, timeline };
}

// ---- 1. flights from where players are, looking every way (normal, and forced through rifts) ---------------------
const spots = {
  'crown hall': [0, 8600, 19460], 'terrace': [0, 500, 19360], 'floor 40': [700, 0, 15460], 'floor 25': [-700, 0, 9660],
  'floor 10': [0, -700, 3860], 'plaza': [0, -2000, 60], 'arena': [-8000, -8000, 124],
};
const views = [[1, 0, 0], [0, 1, 0], [-1, 0, 0], [0.7, -0.7, 0.3]];
const stats = {};
let flights = 0, appearedOutOfView = 0, viewChecks = 0, riftInView = 0, riftFlights = 0, popSkips = 0, retried = 0;
// v4 the high layer: pass altitude over the player, sideways distance and the elevation it is seen at
const hiStats = { flights: 0, relaxed: 0, elMin: 90, overhead: 0, altMin: 1e9, altMax: 0, pops: 0 };
const HI_EL = Math.atan2(defines.TOD_SKY_HI_ALT_MIN, defines.TOD_SKY_HI_FAR) * 180 / Math.PI;   // the lowest an unrelaxed high pass can be seen
for (const c of classes) {
  const base = g.level.tod_sky_classes[c];
  for (const [worm, tier] of [[false, 0], [true, 0], [false, 1]]) {
    const def = Object.assign(Object.create(Object.getPrototypeOf(base)), base, worm ? { worm_in: 100, worm_out: 100 } : { worm_in: 0, worm_out: 0 });
    for (const [where, cam] of Object.entries(spots)) {
      for (const fwd of views) {
        const r = fly(g, def, V(...cam), V(...fwd), undefined, stats, tier);
        assert.deepEqual(r.errs.slice(0, 5), [], c + (worm ? ' rift' : '') + (tier ? ' HIGH' : '') + ' flight from ' + where + ' looking ' + fwd);
        if (r.none === 'pops') { popSkips++; flights++; if (tier) hiStats.pops++; continue; }   // flight_plan found no pop-free way
        if (r.plan.tries > 1) retried++;
        if (tier) {
          hiStats.flights++;
          const alt = r.p.z - cam[2];
          hiStats.altMin = Math.min(hiStats.altMin, alt); hiStats.altMax = Math.max(hiStats.altMax, alt);
          const a = [r.p.a[0], r.p.a[1]], b = [r.p.a[0] + r.p.dir[0] * r.p.len, r.p.a[1] + r.p.dir[1] * r.p.len];
          const side = g.call('seg_dist2d', [V(...cam), V(a[0], a[1], 0), V(b[0], b[1], 0)]);   // the shipping distance
          const el = Math.atan2(alt, side) * 180 / Math.PI;
          if (r.plan.relaxed) hiStats.relaxed++;
          else {
            assert(alt >= defines.TOD_SKY_HI_ALT_MIN - 1 && alt <= defines.TOD_SKY_HI_ALT_MAX + 1, c + ' HIGH flight passes ' + alt.toFixed(0) + ' over the player from ' + where);
            assert(side >= defines.TOD_SKY_HI_NEAR + def.half - 1 && side <= defines.TOD_SKY_HI_FAR + 1, c + ' HIGH flight passes ' + side.toFixed(0) + ' sideways from ' + where);
            assert(el >= HI_EL - 0.5, c + ' HIGH flight is seen only ' + el.toFixed(1) + ' degrees up from ' + where);
            hiStats.elMin = Math.min(hiStats.elMin, el);
            if (el >= 60) hiStats.overhead++;
          }
        }
        assert(r.first, c + ' never shows from ' + where);
        const hf = Math.hypot(fwd[0], fwd[1]);
        const cosv = (r.first.dir[0] * fwd[0] + r.first.dir[1] * fwd[1]) / (hf * Math.hypot(r.first.dir[0], r.first.dir[1]));
        if (!r.plan.worm_in) {
          assert(r.first.px <= 40, c + (tier ? ' HIGH' : '') + ' pops in too big: ' + r.first.px.toFixed(1) + ' px from ' + where);
          viewChecks++;
          if (cosv < defines.TOD_SKY_VIEW_COS) appearedOutOfView++;
        } else {
          riftFlights++;
          if (cosv > 0.3) riftInView++;
        }
        if (!r.worm_out) assert(r.last.px <= 40, c + (tier ? ' HIGH' : '') + ' vanishes too big: ' + r.last.px.toFixed(1) + ' px from ' + where + ' looking ' + fwd + ' lane ' + r.plan.lane + ' tries ' + r.plan.tries + ' relaxed ' + r.plan.relaxed + ' a ' + r.p.a.map(Math.round) + ' dir ' + r.p.dir.map(v => v.toFixed(3)) + ' z ' + Math.round(r.p.z) + ' len ' + Math.round(r.p.len) + ' glide ' + r.p.glide.toFixed(2) + ' climb ' + r.p.climb.toFixed(2) + ' approach ' + r.plan.approach + ' hidden ' + r.hidden + ' timeline ' + r.timeline.join(' '));
        flights++;
      }
    }
  }
}
assert(popSkips <= flights * 0.08, 'too many flights refused for popping: ' + popSkips + '/' + flights);
assert(hiStats.flights >= 90, 'too few high-layer flights flown: ' + hiStats.flights);
assert(hiStats.relaxed <= hiStats.flights * 0.25, 'too many high-layer flights had to relax their window: ' + hiStats.relaxed + '/' + hiStats.flights);
assert(hiStats.overhead >= 10, 'the high layer never crosses near overhead (' + hiStats.overhead + ' passes >= 60 deg up)');
assert(appearedOutOfView / viewChecks > 0.9, 'too many ships first appear in front of the player: ' + appearedOutOfView + '/' + viewChecks);
assert(riftFlights >= 40 && riftInView / riftFlights > 0.6, 'rift arrivals must open where the player is looking: ' + riftInView + '/' + riftFlights);
for (const c of classes) {
  assert(stats[c].full >= stats[c].flights * 0.95, c + ': most flights must reach full size near the tower');
  assert(stats[c].flames > 0, c + ': no flame was ever shown');
  assert(stats[c].win > 0 && stats[c].wout > 0, c + ': the forced rift flights did not use rifts (a structure hid every one?)');
}

// ---- 1b. v4 convoys: a follower on the lead's path (fixed) flies clear, pop-free, parallel and close astern ----------
let convoys = 0, convoyFull = 0;
for (const c of classes) {
  const base = g.level.tod_sky_classes[c];
  if (!(base.convoy_pct > 0)) continue;
  const def = Object.assign(Object.create(Object.getPrototypeOf(base)), base, { worm_in: 0, worm_out: 0 });
  for (const [where, cam] of Object.entries(spots)) {
    for (const fwd of views.slice(0, 2)) {
      const lead = g.call('flight_plan', [def, undefined, V(...cam), V(...fwd), V(...cam), 0]);
      if (!lead) continue;
      const side = (rand() * 2 - 1) * defines.TOD_SKY_CONVOY_SIDE, dz = (rand() * 2 - 1) * defines.TOD_SKY_CONVOY_DZ;
      const fixed = g.call('convoy_fixed', [def, lead, side, dz]);
      const r = fly(g, def, V(...cam), V(...fwd), fixed, null, 0);
      assert.deepEqual(r.errs.slice(0, 5), [], c + ' convoy follower from ' + where + ' looking ' + fwd);
      assert(r.first && r.first.px <= 40, c + ' convoy follower pops in from ' + where);
      assert(Math.abs(r.p.z - lead.p.z - dz) < 1e-6 && Math.hypot(r.p.a[0] - lead.p.a[0], r.p.a[1] - lead.p.a[1]) <= defines.TOD_SKY_CONVOY_SIDE + 1e-6,
             c + ' convoy follower is not on the lead\'s path');
      assert(Math.abs(r.p.len - lead.p.len) < 1e-6 && Math.abs(r.p.speed - lead.p.speed) < 1e-9, c + ' convoy follower flies a different pass');
      if (r.full) convoyFull++;
      convoys++;
    }
  }
  // the gap between a lead and its follower at cruise must exceed the ship, or they overlap in the sky
  assert(def.convoy_gap * 0.85 * def.speed >= def.back + def.front + 400, c + ': convoy followers could overlap the lead (' + (def.convoy_gap * 0.85 * def.speed).toFixed(0) + ' u astern)');
  assert(def.convoy_min >= 1 && def.convoy_max >= def.convoy_min, c + ': convoy follower counts');
}
assert(convoys >= 20 && convoyFull >= convoys * 0.9, 'convoy followers: ' + convoyFull + '/' + convoys + ' reached full size');

// ---- 2. the first-jump salute (61's longer jump: ignite 4.8, the sign revealed ~7.2, the hold to 9.8) ---------------
const REVEAL_CAM = V(...G.REVEAL_CAM), CRASH = [-5879, 3390, 23190];
const DELAY = defines.TOD_SKY_SALUTE_DELAY, YAW_HOLD = 183.5;        // the camera yaw mid-hold (-176.5)
{
  const hi = g.call('tod_sky_lanes::reveal_high', []), lo = g.call('tod_sky_lanes::reveal_low', []);
  const defH = g.level.tod_sky_classes[hi.ship], defL = g.level.tod_sky_classes[lo.ship];
  const rH = fly(g, defH, REVEAL_CAM, V(-1, 0, 0), hi, null);
  assert.deepEqual(rH.errs.slice(0, 5), [], 'reveal_high flight');
  const plan = g.call('flight_plan', [defH, hi, REVEAL_CAM, V(-1, 0, 0), REVEAL_CAM]);
  const p = plan.p;
  let s = -plan.approach, t = 0, crossed = null, minCrash = 1e9, startRel = null;
  while (t < 5) {
    for (const o of offsets.slice(0, defH.wing_max)) {
      const org = g.call('wing_pose', [p, s, t, o])[0];
      minCrash = Math.min(minCrash, Math.hypot(org[0] - CRASH[0], org[1] - CRASH[1], org[2] - CRASH[2]));
    }
    const lead = g.call('wing_pose', [p, s, t, offsets[0]])[0];
    const yaw = Math.atan2(lead[1] - REVEAL_CAM[1], lead[0] - REVEAL_CAM[0]) * 180 / Math.PI;
    const rel = ((yaw - YAW_HOLD + 540) % 360) - 180;
    if (startRel === null) startRel = rel;
    if (crossed === null && rel > 0) crossed = t;
    const el = Math.atan2(lead[2] - REVEAL_CAM[2], Math.hypot(lead[0] - REVEAL_CAM[0], lead[1] - REVEAL_CAM[1])) * 180 / Math.PI;
    // in the frame (the jump camera's ~104 deg wide view), before and just after the crossing: above the title, below the top
    if (Math.abs(rel) < 57 && (crossed === null || t < crossed + 1))
      assert(el > 14 && el < 36, 'the salute leaves the frame vertically or crosses the title (el ' + el.toFixed(1) + ')');
    s += g.call('path_speed', [p, s]) * TICK; t += TICK;
  }
  assert(startRel < -57, 'the salute starts inside a 104-degree frame (' + startRel.toFixed(1) + ' deg from centre)');
  const crossIgn = crossed === null ? null : crossed + DELAY;
  assert(crossIgn !== null && crossIgn >= 3.1 && crossIgn <= 4.6, 'the salute crosses the sign at ignite + ' + crossIgn + ' s (want 3.1..4.6: after the reveal, in the hold)');
  assert(minCrash > 2500, 'the salute flies through the crash fireball (' + Math.round(minCrash) + ' u)');
  const rL = fly(g, defL, REVEAL_CAM, V(-1, 0, 0), lo, null);
  assert.deepEqual(rL.errs.slice(0, 5), [], 'reveal_low flight');
  const b = rL.first.dir;
  const yawL = ((Math.atan2(b[1], b[0]) * 180 / Math.PI - YAW_HOLD + 540) % 360) - 180, elL = Math.asin(b[2]) * 180 / Math.PI;
  assert(Math.abs(yawL) < 40 && elL < 7 && elL > -3, 'reveal_low starts off the horizon beside the sign (yaw ' + yawL.toFixed(1) + ', el ' + elL.toFixed(1) + ')');
  assert(rL.first.px < 12, 'reveal_low starts too big (' + rL.first.px.toFixed(0) + ' px): it would pop in during the hold');
  assert(rL.full, 'reveal_low must come to pass the tower');
  var revealNote = 'salute from ' + startRel.toFixed(0) + ' deg crosses at ignite+' + crossIgn.toFixed(1) + ' s, ' + Math.round(minCrash) + ' u from the crash; hauler ' + yawL.toFixed(0) + ' deg / ' + rL.first.px.toFixed(0) + ' px';
}

// ---- 3. asteroids ---------------------------------------------------------------------------------------------------
const rockStats = { plans: 0, clusters: 0, peakMax: 0, peakMin: 1e9 };
function rockErrs(gg, pl, cam) {
  const errs = [];
  const n = Math.round(pl.secs / 0.5);
  let prevDir = null;
  for (let i = 0; i <= n; i++) {
    const t = Math.min(pl.secs, i * 0.5);
    for (const r of pl.rocks) {
      const st = gg.call('rock_state', [pl, r, t, cam]);
      const rad = gg.level.tod_sky_rocks[r.pick][1];
      const si = gg.call('stand_in', [gg.call('ball_def', [rad]), st[0], st[1], cam]);
      const at = si[0], R = rad * si[1];
      if (st[2] > defines.TOD_SKY_ROCK_MIN_RAD && ![0, 1, 2].every(j => at[j] - R >= gg.level.tod_sky_lo[j] - 1 && at[j] + R <= gg.level.tod_sky_hi[j] + 1))
        errs.push('ROCK INSIDE drawn outside the volume');
      const dv = [0, 1, 2].map(j => st[0][j] - cam[j]), dd = [0, 1, 2].map(j => at[j] - cam[j]);
      const cosang = (dv[0] * dd[0] + dv[1] * dd[1] + dv[2] * dd[2]) / (Math.hypot(...dv) * Math.hypot(...dd));
      if (cosang < 1 - 1e-9) errs.push('ROCK BEARING off the ray');
      const el = Math.asin(dv[2] / Math.hypot(...dv)) * 180 / Math.PI;
      if (el < defines.TOD_SKY_ROCK_EL_MIN - 4) errs.push('ROCK low in the sky (el ' + el.toFixed(1) + ')');
      const px = st[2] / PX;
      if ((t === 0 || t === pl.secs) && px > 0.8) errs.push('ROCK pops ' + (t === 0 ? 'in' : 'out') + ' at ' + px.toFixed(1) + ' px');
      if (r === pl.rocks[0]) {
        rockStats.peakMax = Math.max(rockStats.peakMax, px);
        const u = dv.map(v => v / Math.hypot(...dv));
        if (prevDir) {
          const step = Math.acos(Math.min(1, u[0] * prevDir[0] + u[1] * prevDir[1] + u[2] * prevDir[2])) * 180 / Math.PI / 0.5;
          if (step > 2.5) errs.push('ROCK moves too fast (' + step.toFixed(2) + ' deg/s)');
        }
        prevDir = u;
      }
    }
  }
  const peak = pl.rocks[0].ang * 0.017453 / PX;
  rockStats.peakMin = Math.min(rockStats.peakMin, peak);
  if (peak < 4 || peak > 70) errs.push('ROCK peak size ' + peak.toFixed(1) + ' px (want 4..70)');
  if (pl.w < 0.3) errs.push('ROCK too slow to see moving');
  return errs;
}
for (let n = 0; n < 240; n++) {
  const pl = g.call('rock_plan', []);
  assert(pl, 'rock_plan found no path');
  rockStats.plans++;
  if (pl.cluster) rockStats.clusters++;
  const cam = V(...Object.values(spots)[n % Object.keys(spots).length]);
  const errs = rockErrs(g, pl, cam);
  assert.deepEqual(errs.slice(0, 3), [], 'rock drift ' + n);
}
assert(rockStats.clusters > 20 && rockStats.clusters < 120, 'clusters should be ~30% of drifts: ' + rockStats.clusters);
assert(g.level.tod_sky_rocks.length === (manifest.rocks || []).length && g.level.tod_sky_rocks.length >= 5, 'every exported rock is flown');
assert.equal(g.level.tod_sky_rocks.reduce((a, r) => a + r[3], 0), 100, 'rock pick weights must sum to 100');

// the black holes' rocks: round their hole, in its disc, swallowed at its shadow
const holes = G.skyHoles();
assert(holes.length === 2, 'two painted black holes');
{
  const gdt = rd('source_data/tod_skybox.gdt');
  const rot = +gdt.match(/"skyRotation" "(-?[\d.]+)"/)[1];
  const garg = holes.find(h => h.name === 'gargantua');
  const want = ((-(140 + rot) - 75) % 360 + 360) % 360;
  assert(Math.abs(garg.yaw - want) < 1e-6, 'gargantua yaw must follow skyRotation (' + garg.yaw + ' vs ' + want + ')');
}
let eaten = 0, behindSeen = 0;
for (const h of g.level.tod_sky_holes) {
  for (let n = 0; n < 12; n++) {
    const o = g.call('hole_rock', [h, 0]);
    let behind = 0;
    while (true) {
      const rho = g.call('hole_rho', [o]);
      o.phi += o.w0 * Math.sqrt((o.rho0 ** 3) / (rho ** 3)) * TICK;
      o.t += TICK; o.age += TICK;
      const st = g.call('hole_state', [h, o]);
      if (o.age < 0.15) assert(st[2] / PX < 0.5, 'an orbiting rock pops in at ' + (st[2] / PX).toFixed(1) + ' px');
      const sep = Math.acos(Math.min(1, st[0][0] * h[0][0] + st[0][1] * h[0][1] + st[0][2] * h[0][2])) * 180 / Math.PI;
      assert(sep < h[1] * (o.rho0 + 0.3), 'a rock left its black hole (' + sep.toFixed(2) + ' deg from ' + h[6] + ')');
      if (st[1] && sep < h[1]) behind++;
      if (o.t >= o.secs) { assert(sep < h[1] * 1.35, 'a rock was swallowed away from the shadow (' + (sep / h[1]).toFixed(2) + ' R)'); eaten++; break; }
    }
    if (behind) behindSeen++;
  }
}
assert(eaten === 24, 'every orbiting rock is swallowed');
assert(behindSeen > 0, 'no rock ever passed behind a black hole (the disc plane is wrong?)');

// ---- 3b. v4 satellites: high, on the ray, inside the box, slow and steady, a point of a few pixels from everywhere -------
let sats = 0, satElMin = 90, satHiddenTicks = 0, satPxMin = 1e9, satPxMax = 0;
for (let n = 0; n < 120; n++) {
  const pl = g.call('sat_plan', []);
  assert(pl, 'sat_plan found no path');
  assert(pl.w >= 0.2 && pl.w <= 0.5 && pl.flare_t >= 2 && pl.flare_t <= 5 && pl.secs >= 70 && pl.secs <= 160, 'satellite plan out of range');
  const cam = V(...Object.values(spots)[n % 7]);
  let prev = null;
  for (let tt = 0; tt <= pl.secs; tt += 1) {
    const d = g.call('rock_dir', [pl, tt]);
    const el = Math.asin(Math.max(-1, Math.min(1, d[2]))) * 180 / Math.PI;
    satElMin = Math.min(satElMin, el);
    assert(el >= defines.TOD_SKY_SAT_EL_MIN - 4, 'SAT low in the sky (el ' + el.toFixed(1) + ')');
    const si = g.call('sat_point', [pl, tt, cam]);
    assert(inVol(g, si[0], 5), 'SAT drawn outside the volume at ' + si[0].map(Math.round));
    const dd = [0, 1, 2].map(j => si[0][j] - cam[j]), R = Math.hypot(...dd);
    assert((dd[0] * d[0] + dd[1] * d[1] + dd[2] * d[2]) / R > 1 - 1e-6, 'SAT off the ray');
    if (prev) {
      const step = Math.acos(Math.min(1, d[0] * prev[0] + d[1] * prev[1] + d[2] * prev[2])) * 180 / Math.PI;
      assert(step > 0.15 && step < 0.6, 'SAT moves ' + step.toFixed(2) + ' deg/s');
    }
    prev = d;
    if (si[2]) satHiddenTicks++;
    else {
      const name = g.call('sat_fx', [R * defines.TOD_SKY_SAT_RAD]);
      const S = fxTables.sat.find(([tag]) => name.endsWith('_' + tag))[1];
      const px = S / R / PX;
      satPxMin = Math.min(satPxMin, px); satPxMax = Math.max(satPxMax, px);
      assert(px >= 2 && px <= 8, 'SAT point reads ' + px.toFixed(1) + ' px from ' + Object.keys(spots)[n % 7]);
    }
  }
  sats++;
}
assert(sats === 120 && satHiddenTicks < 120 * 115 * 0.2, 'satellites hidden too often: ' + satHiddenTicks + ' ticks');
for (const [tag, s] of fxTables.sat) assert.equal(g.call('sat_fx', [s]), 'tod/sky/fx_sky_sat_' + tag, 'sat_fx picks its own size ' + tag);

// ---- 4. shooting stars + fireballs ----------------------------------------------------------------------------------
let stars = 0, arcMin = 1e9, arcMax = 0;
for (let n = 0; n < 300; n++) {
  const cam = V(...Object.values(spots)[n % 7]);
  const ball = n % 10 === 9;
  const v = n % 3;
  const speed = ball ? g.call('tod_sky_lanes::ball_speed', []) : g.call('tod_sky_lanes::star_speed', [v]);
  const secs = ball ? g.call('tod_sky_lanes::ball_secs', []) : g.call('tod_sky_lanes::star_secs', [v]);
  const radiant = n % 17 === 0 ? V(0.4, 0.3, 0.87) : undefined;
  const pl = g.call('star_plan', [cam, speed, secs, ball ? 18 : 25, ball ? 48 : 74, radiant]);
  if (!pl) continue;
  stars++;
  const p0 = pl[0], p1 = [0, 1, 2].map(j => pl[0][j] + pl[1][j] * pl[2]);
  assert(inVol(g, p0) && inVol(g, p1), 'STAR outside the sealed volume');
  const e1 = Math.asin((p1[2] - cam[2]) / Math.hypot(p1[0] - cam[0], p1[1] - cam[1], p1[2] - cam[2])) * 180 / Math.PI;
  assert(e1 > 11.9, 'STAR ends below the skyline (el ' + e1.toFixed(1) + ')');
  const a = [0, 1, 2].map(j => p0[j] - cam[j]), b = [0, 1, 2].map(j => p1[j] - cam[j]);
  const arc = Math.acos((a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) / (Math.hypot(...a) * Math.hypot(...b))) * 180 / Math.PI;
  arcMin = Math.min(arcMin, arc); arcMax = Math.max(arcMax, arc);
  assert(arc > 6 && arc < 60, 'STAR arc ' + arc.toFixed(1) + ' deg');
}
assert(stars > 240, 'too many streaks found no path: ' + stars + '/300');
{
  // the speeds baked into the effects are the ones the director plans with
  for (const [i, k] of ['a', 'b', 'c'].entries()) {
    assert.equal(g.call('tod_sky_lanes::star_speed', [i]), fxTables.stars[k].speed);
    assert.equal(g.call('tod_sky_lanes::star_secs', [i]), fxTables.stars[k].life_ms / 1000);
  }
}

// ---- 5. the lockstep the game needs ---------------------------------------------------------------------------------
const zone = rd('zone_source/zm_tod2_cybercity.zone');
const zoneLines = new Set(zone.split(/\r?\n/).map(s => s.trim()));
const modelLines = new Set(manifest.zone_lines);
const aliasCsv = rd('sound/aliases/tod_sky.csv');
const aliases = new Set(aliasCsv.split(/\r?\n/).slice(1).map(r => r.split(',')[0]).filter(Boolean));
function children(fx) {
  const t = fs.readFileSync(path.join(ROOT, 'share/raw/fx', fx + '.efx'), 'utf8');
  return [...t.matchAll(/"(tod\/sky\/[^"]+)"/g)].map(m => m[1]);
}
function lockstep(zoneSet, cscText) {
  const errs = [];
  const fxUsed = new Set([...cscText.matchAll(/"(tod\/sky\/[\w]+)"/g)].map(m => m[1]));
  // session 61's crash scene plays the fleet's gunship engines (gen_fx.py jump_title_gunship): it must stay made + zoned
  const jt = rd('scripts/zm/zm_tod2_cybercity/_tod_jump_title.csc');
  for (const m of jt.matchAll(/"(tod\/sky\/[\w]+)"/g)) {
    if (!fxFiles.has(m[1])) errs.push('the jump title plays ' + m[1] + ', which gen_fx.py no longer makes');
    fxUsed.add(m[1]);
  }
  const precached = new Set([...cscText.matchAll(/#precache\( "client_fx", "([^"]+)" \);/g)].map(m => m[1]));
  const kids = new Set();
  for (const fx of fxUsed) {
    if (!precached.has(fx) && !/fx_sky_eng_gunship$/.test(fx)) errs.push('fx ' + fx + ' used but not precached');
    if (!zoneSet.has('fx,' + fx)) errs.push('fx ' + fx + ' has no zone line');
    if (!fs.existsSync(path.join(ROOT, 'share/raw/fx', fx + '.efx'))) { errs.push('fx file missing ' + fx); continue; }
    const todo = children(fx);                                          // children, and theirs (a burst's fragments)
    while (todo.length) {
      const k = todo.pop();
      if (kids.has(k)) continue;
      kids.add(k);
      if (fs.existsSync(path.join(ROOT, 'share/raw/fx', k + '.efx'))) todo.push(...children(k));
    }
  }
  for (const k of kids) {
    if (!zoneSet.has('fx,' + k)) errs.push('child fx ' + k + ' has no zone line');
    if (!fs.existsSync(path.join(ROOT, 'share/raw/fx', k + '.efx'))) errs.push('child fx file missing ' + k);
  }
  for (const l of zoneSet) if (/^fx,tod\/sky\//.test(l) && !fxUsed.has(l.slice(3)) && !kids.has(l.slice(3))) errs.push('zoned but never played: ' + l);
  for (const f of fxFiles) if (!fxUsed.has(f) && !kids.has(f)) errs.push('an effect file nothing plays: ' + f);
  for (const c of classes) {
    const def = g.level.tod_sky_classes[c];
    for (const m of def.models) {
      if (!modelLines.has('xmodel,' + m)) errs.push('model ' + m + ' is not an exported model');
      if (!zoneSet.has('xmodel,' + m)) errs.push('model ' + m + ' has no zone line');
    }
    if (!aliases.has(def.loop_alias)) errs.push('alias ' + def.loop_alias + ' missing from tod_sky.csv');
    if (!def.lights.length) errs.push(c + ' has no blinking lights');
    const r = manifest.ships.find(x => x.ship === c);
    if (def.nozzles.length !== r.nozzles.length) errs.push(c + ': ' + def.nozzles.length + ' flame tags for ' + r.nozzles.length + ' nozzles');
    def.nozzles.forEach((nz, i) => { if (nz[0] !== 'tag_eng_' + i) errs.push(c + ' nozzle ' + i + ' tag ' + nz[0]); });
  }
  for (const r of g.level.tod_sky_rocks) for (const m of r[0]) {
    if (!modelLines.has('xmodel,' + m)) errs.push('rock ' + m + ' is not an exported model');
    if (!zoneSet.has('xmodel,' + m)) errs.push('rock ' + m + ' has no zone line');
  }
  for (const m of manifest.zone_lines) if (!zoneSet.has(m)) errs.push('exported model not zoned: ' + m);
  for (const a of ['tod_sky_worm_open', 'tod_sky_worm_burst', 'tod_sky_worm_close']) {
    if (!aliases.has(a)) errs.push('alias ' + a + ' missing from tod_sky.csv');
    if (!new RegExp('"' + a + '"').test(cscText)) errs.push('the rift never plays ' + a);
  }
  if ([...zoneSet].some(l => /sky_warp/.test(l)) || /sky_warp/.test(cscText)) errs.push('a retired warp reference is back');
  if ([...fxFiles].some(f => /warp|fx_sky_eng_(?!gunship$)/.test(f))) errs.push('a retired effect file (warp / v2 engine) is back');
  for (const s of ['_tod_sky_ships.csc', '_tod_sky_lanes.csc'])
    if (!zoneSet.has('scriptparsetree,scripts/zm/zm_tod2_cybercity/' + s)) errs.push('no scriptparsetree for ' + s);
  if (!/#using scripts\\zm\\zm_tod2_cybercity\\_tod_sky_ships;/.test(rd('scripts/zm/zm_tod2_cybercity.csc'))) errs.push('entry csc does not #using the fleet');
  if (!/"Filename": "tod_sky\.csv"/.test(rd('sound/zoneconfig/zm_tod2_cybercity.szc'))) errs.push('tod_sky.csv is not in the sound zone config');
  if (!/model_export\\tod_sky_ships/.test(rd('tools/sync_to_modtools.ps1'))) errs.push('the sync does not copy model_export/tod_sky_ships');
  if (!/level waittill\( "tod_jump_title_ignite", localClientNum \)/.test(cscText)) errs.push('the salute does not listen for session 61\'s ignite beat');
  // the size buckets the director picks are the ones the effects were generated at
  BUCKETS.forEach((b, i) => { if (g.call('flame_bucket', [b, -1]) !== i) errs.push('flame bucket ' + i + ' (' + b + ') is not picked for its own size'); });
  WORM_B.forEach((r, i) => { if (g.call('worm_bucket', [r]) !== i) errs.push('rift bucket ' + i + ' (' + r + ') is not picked for its own size'); });
  for (const [kind, ref] of Object.entries(fxTables.kinds)) {
    const ki = G.KIND_ORDER.indexOf(kind);
    if (ki < 0) errs.push('kind ' + kind + ' has no director index');
    for (let b = 0; b < BUCKETS.length; b++) if (!fxFiles.has(g.call('flame_fx', [ki, b]))) errs.push('flame_fx(' + kind + ', ' + b + ') is not an effect');
  }
  return errs;
}
// Whatever spawns must be deleted on every path; the counters go up and down once.
function lifecycle(cscText) {
  const errs = [];
  const body = name => { const m = cscText.match(new RegExp('function ' + name + '\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\}')); return m ? m[1] : null; };
  const src = body('sortie');
  if (!src) return ['no sortie()'];
  const at = src.indexOf('spawn( localClientNum');
  if (at < 0) errs.push('sortie spawns nothing');
  if (/\breturn\b/.test(src.slice(at))) errs.push('a return after the first spawn() leaks ships');
  if ((src.match(/tod_sky_live\[ localClientNum \]\[ key \]\+\+/g) || []).length !== 1) errs.push('live counter must go up exactly once');
  if ((src.match(/tod_sky_live\[ localClientNum \]\[ key \]--/g) || []).length !== 1) errs.push('live counter must come down exactly once');
  if (!/ships\[ i \] Delete\(\)/.test(src)) errs.push('ships are never deleted');
  if (!/StopAllLoopSounds/.test(src)) errs.push('the engine loop is never stopped');
  if (!/engines_off\( localClientNum, ships\[ i \] \)/.test(src)) errs.push('the engine flames are never stopped at the end');
  if (!/rift_end\( localClientNum, rin \)/.test(src) || !/rift_end\( localClientNum, rout \)/.test(src)) errs.push('a rift host can outlive its flight');
  if (/\.origin = /.test(src)) errs.push('a direct .origin write on a client model (no stock precedent: spawn it where it is drawn)');
  const dr = body('drift');
  if (!dr || !/models\[ j \] Delete\(\)/.test(dr) || (dr.match(/tod_sky_rocks_live\[ localClientNum \]--/g) || []).length !== 1) errs.push('drift() must delete its rocks and count down once');
  if (dr && /\breturn\b/.test(dr.slice(dr.indexOf('spawn( localClientNum')))) errs.push('a return after drift() spawns leaks rocks');
  const hl = body('hole_loop');
  if (!hl || !/m Delete\(\)/.test(hl)) errs.push('hole_loop() never deletes a swallowed rock');
  const re = body('rift_end');
  if (!re || !/r\.host Delete\(\)/.test(re)) errs.push('rift_end() does not delete the rift host');
  if (!/waitrealtime/.test(body('class_loop') || '')) errs.push('the fleet schedule must run on real time (waitrealtime)');
  // v4
  const sat = body('satellite');
  if (!sat || !/host Delete\(\)/.test(sat) || (sat.match(/tod_sky_sats_live\[ localClientNum \]--/g) || []).length !== 1) errs.push('satellite() must delete its host and count down once');
  if (sat && /\breturn\b/.test(sat.slice(sat.indexOf('spawn( localClientNum')))) errs.push('a return after satellite() spawns leaks its host');
  if (sat && !/StopFX\( localClientNum, fx \)/.test(sat)) errs.push('satellite() never stops its point effect');
  for (const f of ['satellite_loop', 'convoy_followers'])
    if (!/waitrealtime/.test(body(f) || '')) errs.push(f + '() must run on real time (waitrealtime)');
  if (!/level thread class_loop\( localClientNum, def, 1 \)/.test(body('on_local_connect') || '')) errs.push('the high layer is not started');
  if (!/level thread satellite_loop\( localClientNum \)/.test(body('on_local_connect') || '')) errs.push('the satellites are not started');
  // v4 THE ENTITY BUDGET: every spawn site counts up, every delete site counts down, in the same function
  for (const [fn, up, down] of [['sortie', /ents_add\( localClientNum, ships\.size \)/, /ents_add\( localClientNum, 0 - ships\.size \)/],
                                ['drift', /ents_add\( localClientNum, models\.size \)/, /ents_add\( localClientNum, 0 - models\.size \)/],
                                ['hole_loop', /ents_add\( localClientNum, 1 \)/, /ents_add\( localClientNum, -1 \)/],
                                ['satellite', /ents_add\( localClientNum, 1 \)/, /ents_add\( localClientNum, -1 \)/],
                                ['rift_open', /ents_add\( localClientNum, 1 \)/, null], ['rift_end', null, /ents_add\( localClientNum, -1 \)/]]) {
    const b = body(fn) || '';
    if (up && !up.test(b)) errs.push(fn + '() spawns without counting the budget up');
    if (down && !down.test(b)) errs.push(fn + '() deletes without counting the budget down');
  }
  for (const fn of ['sortie', 'drift', 'satellite']) if (!/ents_free\( localClientNum/.test(body(fn) || '')) errs.push(fn + '() does not ask the budget before spawning');
  const spawns = (cscText.match(/spawn\( localClientNum/g) || []).length, counted = (cscText.match(/ents_add\( localClientNum, (1|ships\.size|models\.size) \)/g) || []).length;
  if (spawns !== counted) errs.push('spawn sites (' + spawns + ') and budget counts (' + counted + ') differ');
  if (!/level\.tod_sky_live\[ localClientNum \]\[ key \] <= 1/.test(src)) errs.push('a convoy may start while the lead is not alone in its tier');
  if (/ball_def\( rad \)/.test(body('hole_loop') || '')) errs.push('hole_loop() makes a struct per rock per tick');
  if (/ball_def\( 4 \)/.test(body('sat_point') || '')) errs.push('sat_point() makes a struct per tick');
  return errs;
}
assert.deepEqual(lockstep(zoneLines, csc), [], 'lockstep');
assert.deepEqual(lifecycle(csc), [], 'lifecycle');
// v4 the schedules: a high layer per class, rarer than the low one, its own live key; the expected ships in the sky at once
// (cap-limited arrival rate x average flight time, from the flights above) come to ~1.5x the v3 fleet
for (const c of classes) {
  const d = g.level.tod_sky_classes[c];
  assert.deepEqual(g.call('sched', [d, 0]), [d.first, d.gap_min, d.gap_max, d.cap], c + ' low schedule');
  assert.deepEqual(g.call('sched', [d, 1]), [d.hi_first, d.hi_gap_min, d.hi_gap_max, d.hi_cap], c + ' high schedule');
  assert(d.hi_cap >= 1 && d.hi_gap_min >= d.gap_min && d.hi_gap_max >= d.gap_max && d.hi_first > 0, c + ': the high layer must be rarer than the low one, never absent');
  assert.equal(g.call('live_key', [d, 1]), c + '_high'); assert.equal(g.call('live_key', [d, 0]), c);
}
const expectFleet = tier => classes.reduce((a, c) => {
  const d = g.level.tod_sky_classes[c], S = stats[c], s = g.call('sched', [d, tier]);
  return a + Math.min(s[3], (S.secs / S.flights) / ((s[1] + s[2]) / 2));
}, 0);
const fleetV3 = expectFleet(0), fleetV4 = fleetV3 + expectFleet(1);
assert(fleetV4 / fleetV3 >= 1.4 && fleetV4 / fleetV3 <= 1.8, 'the high layer should bring the fleet to ~1.5x: ' + (fleetV4 / fleetV3).toFixed(2));
assert(g.level.tod_sky_holes.reduce((a, h) => a + h[4], 0) === 15, 'the black holes carry 9 + 6 rocks (v4)');
// the budget: the worst case of every cap at once (wings, convoys, rocks, orbits, satellites, rift hosts) fits under it
{
  const worst = classes.reduce((a, c) => { const d = g.level.tod_sky_classes[c]; const conv = d.convoy_pct > 0 ? d.convoy_max : 0;
    return a + (d.cap + conv) * d.wing_max + (d.hi_cap + conv) * d.wing_max + 2 * (d.cap + d.hi_cap); }, 0)
    + defines.TOD_SKY_ROCKS_MAX * 4 + 15 + defines.TOD_SKY_SATS_MAX;
  assert(worst <= 1.3 * defines.TOD_SKY_ENT_MAX && worst >= 0.6 * defines.TOD_SKY_ENT_MAX, 'the entity budget (' + defines.TOD_SKY_ENT_MAX + ') is far from the worst case ' + worst);
  g.level.tod_sky_ents = [defines.TOD_SKY_ENT_MAX - 2];
  assert(g.call('ents_free', [0, 2]) === true && g.call('ents_free', [0, 3]) === false, 'ents_free');
  g.call('ents_add', [0, 2]); assert.equal(g.level.tod_sky_ents[0], defines.TOD_SKY_ENT_MAX); g.call('ents_add', [0, -2]);
  assert.equal(g.level.tod_sky_ents[0], defines.TOD_SKY_ENT_MAX - 2);
  g.level.tod_sky_ents = [0];
  var budgetNote = 'worst case ' + worst + ' of ' + defines.TOD_SKY_ENT_MAX;
}
assert.equal(defines.TOD_SKY_LOG, 1, 'dev logs on for the playtest (set 0 before a publish)');
assert(Math.abs(defines.TOD_SKY_PX_RAD - PX) < 1e-6, 'TOD_SKY_PX_RAD must be gen_lanes.js PX_RAD');

// ---- 6. negative controls: each check must be able to fail ----------------------------------------------------------
const broken = [
  ['a return after spawn', lifecycle(csc.replace('\tlevel.tod_sky_live[ localClientNum ][ key ]++;', '\tlevel.tod_sky_live[ localClientNum ][ key ]++;\n\tif ( count > 9 ) return;'))],
  ['a satellite host never deleted', lifecycle(csc.replace('\tif ( isdefined( host ) ) host Delete();', ''))],
  ['the high layer never started', lifecycle(csc.replace('\t\tlevel thread class_loop( localClientNum, def, 1 );', ''))],
  ['a rock drift that never uncounts its rocks', lifecycle(csc.replace('\tents_add( localClientNum, 0 - models.size );', ''))],
  ['a convoy allowed while the lead is not alone', lifecycle(csc.replace('level.tod_sky_live[ localClientNum ][ key ] <= 1\n\t\t&& ', ''))],
  ['no delete', lifecycle(csc.replace(/ships\[ i \] Delete\(\)/, 'ships[ i ] Hide()'))],
  ['no rift cleanup', lifecycle(csc.replace('rift_end( localClientNum, rout );', ''))],
  ['a missing zone model', lockstep(new Set([...zoneLines].filter(l => l !== 'xmodel,tod_sky_hauler_b')), csc)],
  ['a missing zone fx', lockstep(new Set([...zoneLines].filter(l => l !== 'fx,tod/sky/fx_sky_worm_burst_2')), csc)],
  ['a missing child fx', lockstep(new Set([...zoneLines].filter(l => l !== 'fx,tod/sky/fx_sky_star_trail')), csc)],
  ['the warp back in the zone', lockstep(new Set([...zoneLines, 'fx,tod/sky/fx_sky_warp_l']), csc)],
];
for (const [what, errs] of broken) assert(errs.length > 0, 'negative control not caught: ' + what);
let controls = broken.length;
{
  const noFit = load(csc.replace(/if \( w\[ j \] > 0\.000001 \) r = fmin\( r, \( hi\[ j \] - cam\[ j \] \) \/ w\[ j \] \);/, 'if ( w[ j ] > 0.000001 ) r = r;'));
  const def = Object.assign({}, noFit.level.tod_sky_classes.dreadnought, { worm_in: 0, worm_out: 0 });
  const errs = fly(noFit, def, V(0, -2000, 60), V(1, 0, 0), undefined, null).errs;
  assert(errs.some(e => e.startsWith('INSIDE')), 'negative control not caught: a stand-in without the wall fit');
  controls++;
}
{
  const noBlk = load(csc, { noBlockers: true });
  let caught = false;
  for (let n = 0; n < 40 && !caught; n++)
    for (const c of ['hauler', 'dreadnought', 'gunship']) {
      const def = Object.assign({}, noBlk.level.tod_sky_classes[c], { worm_in: 0, worm_out: 0 });
      if (fly(noBlk, def, V(0, 8600, 19460), V(0, 1, 0.2), undefined, null).errs.some(e => e.startsWith('CLEAR'))) { caught = true; break; }
    }
  assert(caught, 'negative control not caught: stand-ins without the blocker list');
  controls++;
}
{
  // flame buckets one step off: the size check must see flames twice / half the nozzle
  const off = load(csc.replace('if ( x > 0.7071 ) b = 0;', 'if ( x > 1.4142 ) b = 0;').replace('else if ( x > 0.3536 ) b = 1;', 'else if ( x > 0.7071 ) b = 1;'));
  let caught = false;
  for (const c of classes) {
    const def = Object.assign({}, off.level.tod_sky_classes[c], { worm_in: 0, worm_out: 0 });
    if (fly(off, def, V(0, -2000, 60), V(1, 0, 0), undefined, null).errs.some(e => e.startsWith('FLAME'))) { caught = true; break; }
  }
  assert(caught, 'negative control not caught: flame buckets off by one');
  controls++;
}
{
  // rocks without the elevation floor: the rock check must see one low in the sky
  const low = load(csc.replace('if ( d0[ 2 ] < Sin( TOD_SKY_ROCK_EL_MIN ) || d1[ 2 ] < Sin( TOD_SKY_ROCK_EL_MIN ) ) continue;', ''));
  let caught = false;
  for (let n = 0; n < 200 && !caught; n++) if (rockErrs(low, low.call('rock_plan', []), V(0, -2000, 60)).some(e => /low in the sky/.test(e))) caught = true;
  assert(caught, 'negative control not caught: rocks allowed low in the sky');
  controls++;
}
{
  // streaks without the box check: one must leave the sealed volume
  const loose = load(csc.replace('if ( box_reach( p0, dir, 300 ) < L ) continue;', ''));
  let caught = false;
  for (let n = 0; n < 300 && !caught; n++) {
    const cam = V(...Object.values(spots)[n % 7]);
    const pl = loose.call('star_plan', [cam, 9000, 0.9, 25, 74, undefined]);
    if (pl && !inVol(loose, [0, 1, 2].map(j => pl[0][j] + pl[1][j] * pl[2]))) caught = true;
  }
  assert(caught, 'negative control not caught: streaks without the box check');
  controls++;
}
{
  // satellites without the elevation floor: one must be planned low in the sky
  const low = load(csc.replace('if ( d0[ 2 ] < Sin( TOD_SKY_SAT_EL_MIN ) || d1[ 2 ] < Sin( TOD_SKY_SAT_EL_MIN ) ) continue;', ''));
  let caught = false;
  for (let n = 0; n < 300 && !caught; n++) {
    const pl = low.call('sat_plan', []);
    for (let tt = 0; tt <= pl.secs && !caught; tt += 2) if (Math.asin(low.call('rock_dir', [pl, tt])[2]) * 180 / Math.PI < defines.TOD_SKY_SAT_EL_MIN - 4) caught = true;
  }
  assert(caught, 'negative control not caught: satellites allowed low in the sky');
  controls++;
}
{
  // the high layer without its altitude floor: a HIGH flight must be found passing low over the player
  const lowHi = load(csc.replace('alt_lo = TOD_SKY_HI_ALT_MIN;', 'alt_lo = TOD_SKY_ALT_MIN;'));
  let caught = false;
  for (let n = 0; n < 60 && !caught; n++) {
    const def = Object.assign({}, lowHi.level.tod_sky_classes.hauler, { worm_in: 0, worm_out: 0 });
    const cam = V(...Object.values(spots)[n % 7]);
    const plan = lowHi.call('flight_plan', [def, undefined, cam, V(1, 0, 0), cam, 1]);
    if (plan && !plan.relaxed && plan.p.z - cam[2] < defines.TOD_SKY_HI_ALT_MIN - 1) caught = true;
  }
  assert(caught, 'negative control not caught: the high layer flying low');
  controls++;
}
// the build's lane check must fail when a wall appears in the open sky the lanes use (and pass without it)
const { spawnSync } = require('child_process');
const lanesCheck = extra => spawnSync(process.execPath, [path.join(__dirname, 'gen_lanes.js'), '--check'],
  { cwd: ROOT, encoding: 'utf8', env: Object.assign({}, process.env, extra ? { SKY_LANES_EXTRA: JSON.stringify(extra) } : {}) });
const clean = lanesCheck(null);
assert.equal(clean.status, 0, 'lane check fails on the live map: ' + clean.stderr + clean.stdout);
const walled = lanesCheck([[-9800, -1000, 20000], [-8200, 1000, 30000]]);
assert.notEqual(walled.status, 0, 'negative control not caught: a wall in the west sky');
assert.match(walled.stderr, /BLOCKED/);
controls++;
assert(g.call('pick_lane', [g.level.tod_sky_classes.dreadnought, V(0, 0, 60000), 0]));
assert(g.call('pick_lane', [g.level.tod_sky_classes.dreadnought, V(0, 0, 60000), 1]));

const summary = Object.fromEntries(classes.map(c => {
  const S = stats[c];
  return [c, Math.round(S.secs / S.flights) + ' s/flight, full ' + S.full + '/' + S.flights + ', rifts in/out ' + S.win + '/' + S.wout
    + ', flame ticks ' + S.flames + ', glint ticks ' + S.glints + ', first<=' + S.firstPx.toFixed(1) + 'px'];
}));
console.log('PASS sky fleet v4: ' + flights + ' whole flights (' + classes.length + ' classes x ' + Object.keys(spots).length + ' spots x ' + views.length +
  ' views, normal + through rifts + the HIGH LAYER) run through the SHIPPING director, every tick INSIDE / BEARING / CLEAR / SMOOTH / FLAMES; high layer: ' +
  hiStats.flights + ' flights passing ' + Math.round(hiStats.altMin) + '..' + Math.round(hiStats.altMax) + ' over the player, seen >= ' + hiStats.elMin.toFixed(0) + ' deg up (' +
  hiStats.overhead + ' near overhead, ' + hiStats.relaxed + ' relaxed, ' + hiStats.pops + ' refused); convoys: ' + convoyFull + '/' + convoys + ' followers full; satellites: ' + sats +
  ' (el >= ' + satElMin.toFixed(0) + ', ' + satPxMin.toFixed(1) + '..' + satPxMax.toFixed(1) + ' px); expected ships in the sky at once ' + fleetV3.toFixed(2) + ' -> ' + fleetV4.toFixed(2) +
  ' (x' + (fleetV4 / fleetV3).toFixed(2) + '); entity budget ' + budgetNote + '; ' +
  appearedOutOfView + '/' + viewChecks + ' first appear out of view, ' + retried + ' re-planned + ' + popSkips + ' refused so nothing pops in or out big, ' + riftInView + '/' + riftFlights + ' rifts open in view; reveal: ' + revealNote +
  '; asteroids: ' + rockStats.plans + ' drifts (' + rockStats.clusters + ' clusters, peak ' + rockStats.peakMin.toFixed(0) + '..' + rockStats.peakMax.toFixed(0) +
  ' px), 24 black-hole orbits swallowed (' + behindSeen + ' passed behind); streaks: ' + stars + ' (' + arcMin.toFixed(0) + '..' + arcMax.toFixed(0) +
  ' deg); lockstep + lifecycle; ' + controls + ' negative controls caught; ' + JSON.stringify(summary));
