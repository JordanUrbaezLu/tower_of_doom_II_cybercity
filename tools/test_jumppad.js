#!/usr/bin/env node
// tools/test_jumppad.js — THE JUMP PAD's build gate (docs/163).
//
// The pad is four files that must agree (gen_tower_map.js emits the .map and
// _tod_crown_data.gsc; _tod_jumppad.gsc flies the arc; the zone packs it) plus
// guards in six others. Nothing else checks any of it before the linker, and
// the one failure a player would meet — the arc passing THROUGH something, or
// a set-down outside a live zone (the out-of-playable instakill) — builds,
// bakes and boots clean. So this reads the FINISHED files and proves:
//
//   1. LOCKSTEP. The .map's tod_jumppad_launch / tod_jumppad_land structs sit
//      exactly on _tod_crown_data.gsc's jumppad_launch_org / land_center.
//   2. BOTH ENDS ARE IN A LIVE ZONE. The pad is inside a crown_zone volume
//      and every landing spot inside a roof_zone volume (info_volume brushes
//      from the .map), so neither the take-off nor the set-down is ever a
//      moment outside the playable area.
//   2b. THE DE MACHINE'S SHELL (docs/163 s9). The pad is Der Eisendrache's
//      jumpsphere, a model with no collision; the generator's `jump pad shell`
//      clip ring is its body. Proven: the ring never cuts into the trigger and
//      leaves no dead corner inside it, and its opening is the model's doorway,
//      facing the bridge corridor.
//   3. THE ARC IS CLEAR. The flight is a scripted mover that ignores
//      collision, so nothing stops it passing through a brush — this does.
//      The path is rebuilt from _tod_jumppad.gsc's OWN define
//      (TOD_JUMPPAD_APEX) exactly as the script builds it, from five take-off
//      points across the trigger circle to each of the four landing spots,
//      and a standing player's box (32 x 32 x 72) is swept along it against
//      every worldspawn brush (convex brushes by their real planes).
//   4. WIRING. The module is zoned and threaded, its model is zoned, its
//      alias exists, and every guard the header of _tod_jumppad.gsc promises
//      is present in the file that owns it — including _tod_fall's two seal
//      rules (a flyer is not yet out; the hall's spawning is re-asserted off).
//
// Skips cleanly (exit 0, says so) when jumppad_enabled() is 0 — the road is
// whole and there is no pad.
// Usage: node tools/test_jumppad.js [path/to/map]
'use strict';
const fs = require('fs');
const path = require('path');
const CB = require('./convex_brush');

const REPO = path.join(__dirname, '..');
const MOD = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity');
const MAP = process.argv[2] || path.join(REPO, 'map_source', 'zm', 'zm_tod2_cybercity.map');
const read = (p) => fs.readFileSync(p, 'utf8');
const fails = [];
const ok = [];
const check = (cond, good, bad) => { if (cond) ok.push(good); else fails.push(bad); };

// ---- the generated anchors ---------------------------------------------------
const crown = read(path.join(MOD, '_tod_crown_data.gsc'));
const en = crown.match(/function jumppad_enabled\(\)\s*\{\s*return\s+(\d+);/);
if (!en) { console.error('test_jumppad: _tod_crown_data.gsc has no jumppad_enabled() — regenerate (node tools/gen_tower_map.js)'); process.exit(1); }
if (en[1] !== '1') { console.log('test_jumppad: jumppad_enabled() is 0 (the causeway is whole) — nothing to check.'); process.exit(0); }
const vec = (name) => {
  const m = crown.match(new RegExp(`function ${name}\\(\\)\\s*\\{\\s*return\\s*\\(\\s*(-?[\\d.]+),\\s*(-?[\\d.]+),\\s*(-?[\\d.]+)\\s*\\);`));
  if (!m) throw new Error(`test_jumppad: no ${name}() in _tod_crown_data.gsc`);
  return m.slice(1, 4).map(Number);
};
const PAD = vec('jumppad_launch_org');
const LAND = vec('jumppad_land_center');
const PAD_R = Number(crown.match(/function jumppad_trigger_r\(\)\s*\{\s*return\s+(\d+);/)[1]);
const spotsBlock = crown.match(/function jumppad_land_orgs\(\)\s*\{([\s\S]*?)return a;/)[1];
const SPOTS = [...spotsBlock.matchAll(/\(\s*(-?[\d.]+),\s*(-?[\d.]+),\s*(-?[\d.]+)\s*\)/g)].map(m => m.slice(1, 4).map(Number));
check(SPOTS.length >= 1, `${SPOTS.length} landing spots`, 'jumppad_land_orgs() is empty');

// ---- the script's own flight constants ------------------------------------
const jp = read(path.join(MOD, '_tod_jumppad.gsc'));
const def = (n) => { const m = jp.match(new RegExp(`#define ${n}\\s+("?)([^"\\s]+)\\1`)); if (!m) throw new Error(`test_jumppad: no #define ${n}`); return m[2]; };
const APEX = Number(def('TOD_JUMPPAD_APEX'));
// THE DE MACHINE (docs/163 s9): five models (the machine, its deck dark / blue, the landing pad dark / blue), four of
// DE's flinger effects, three of its sounds
const MODELS = ['FRAME', 'DECK_OFF', 'DECK_ON', 'LAND_OFF', 'LAND_ON'].map(k => def('TOD_JUMPPAD_MODEL_' + k));
const FXS = ['LAUNCH', 'TRAIL', 'GLOW', 'DUST'].map(k => def('TOD_JUMPPAD_FX_' + k));
const SNDS = ['CHARGE', 'LAUNCH', 'LAND'].map(k => def('TOD_JUMPPAD_SND_' + k));
const MODEL = MODELS[0];

// ---- the .map ------------------------------------------------------------------
const map = read(MAP);
const entStart = map.indexOf('// entity 1 ');
const world = map.slice(0, entStart);
const ents = map.slice(entStart).split(/\n(?=\/\/ entity \d+ )/);
const struct = (tn) => {
  const b = ents.find(e => e.includes(`"targetname" "${tn}"`) && e.includes('"classname" "script_struct"'));
  if (!b) return null;
  return b.match(/"origin" "(\S+) (\S+) (\S+)"/).slice(1, 4).map(Number);
};
const sL = struct('tod_jumppad_launch'), sT = struct('tod_jumppad_land');
const same = (a, b) => a && b && a.every((v, i) => Math.abs(v - b[i]) < 0.5);
check(same(sL, PAD), `launch struct == jumppad_launch_org ${PAD}`, `launch struct ${sL} != jumppad_launch_org ${PAD} (regenerate: node tools/gen_tower_map.js)`);
check(same(sT, LAND), `landing struct == jumppad_land_center ${LAND}`, `landing struct ${sT} != jumppad_land_center ${LAND} (regenerate)`);

// zone volumes: every info_volume brush, by targetname
function volumes(zone) {
  const out = [];
  for (const e of ents) {
    if (!e.includes('"classname" "info_volume"') || !e.includes(`"targetname" "${zone}"`)) continue;
    for (const body of e.split('\n{').slice(1)) {
      const planes = CB.readPlanes(body);
      if (planes.length >= 4) out.push(CB.hull(planes));
    }
  }
  return out;
}
const inside = (p, boxes) => boxes.some(h => h.planes.every(q => CB.dot(q.n, p) <= q.d + 0.5));
const crownVol = volumes('crown_zone'), roofVol = volumes('roof_zone');
check(crownVol.length > 0 && roofVol.length > 0, 'crown_zone and roof_zone volumes found', 'crown_zone / roof_zone info_volume brushes not found in the .map');
check(inside([PAD[0], PAD[1], PAD[2] + 32], crownVol), 'the pad stands inside a crown_zone volume',
      'the pad is NOT inside any crown_zone volume — a player waiting on it would be out of the playable area');
for (const s of SPOTS)
  check(inside([s[0], s[1], s[2] + 32], roofVol), `landing spot ${s} inside a roof_zone volume`,
        `landing spot ${s} is NOT inside any roof_zone volume — the set-down would be the out-of-playable instakill`);

// ---- 3. THE ARC --------------------------------------------------------------
const brushes = [];
{
  const re = /^\/\/ brush \d+ — (.*)$/gm;
  const heads = [];
  let m;
  while ((m = re.exec(world))) heads.push({ label: m[1], at: m.index });
  for (let i = 0; i < heads.length; i++) {
    const body = world.slice(heads[i].at, i + 1 < heads.length ? heads[i + 1].at : world.length);
    const planes = CB.readPlanes(body);
    if (planes.length < 4) continue;
    try { const h = CB.hull(planes); brushes.push({ label: heads[i].label, planes, lo: h.lo, hi: h.hi }); } catch (e) { /* degenerate: not a solid */ }
  }
}
check(brushes.length > 1000, `${brushes.length} worldspawn brushes parsed`, `only ${brushes.length} worldspawn brushes parsed — parser drift`);

// ---- 2b. THE DE MACHINE'S SHELL (docs/163 s9) -------------------------------------
// The machine is a script_model with no collision; gen_tower_map cuts a ring of clip wedges round it (`jump pad shell
// N`), open at its doorway. Bound here to the anchors the script reads: every wedge is clip, the whole ring stays
// outside the trigger circle + a player's half-width (nobody stands inside the trigger against the wall, nobody
// outside the machine can reach the trigger), and the opening faces the model's doorway (yaw + 180) = the bridge
// corridor the party walks in from (the balcony's north edge).
const SHELL = brushes.filter(b => /^jump pad shell \d+$/.test(b.label));
const HALF_P = 16;   // a standing player's half-width (the sweep below uses the same box)
{
  const YAW = Number(crown.match(/function jumppad_launch_yaw\(\)\s*\{\s*return\s+(-?[\d.]+);/)[1]);
  const BAL = vec('jumppad_balcony_maxs');
  check(SHELL.length >= 12, `the machine's shell: ${SHELL.length} clip wedges`, `only ${SHELL.length} 'jump pad shell' wedges in the .map (the machine would have no body)`);
  check(SHELL.every(b => b.planes.every(p => p.mat === 'clip')), 'every shell wedge is pure clip (invisible: the model is what you see)',
        'a shell wedge carries a visible material');
  const ang = (x, y) => ((Math.atan2(y - PAD[1], x - PAD[0]) * 180 / Math.PI) + 360) % 360;
  let rMin = Infinity, rMax = 0;
  const covered = new Array(360).fill(false);
  for (const b of SHELL) {
    const h = CB.hull(b.planes);
    const as = [];
    for (const v of h.vertices) { const r = Math.hypot(v[0] - PAD[0], v[1] - PAD[1]); rMin = Math.min(rMin, r); rMax = Math.max(rMax, r); as.push(ang(v[0], v[1])); }
    // the wedge's angular span (it never straddles more than 180 deg)
    let lo = Math.min(...as), hi = Math.max(...as);
    if (hi - lo > 180) { const w = as.map(a => (a > 180 ? a - 360 : a)); lo = Math.min(...w); hi = Math.max(...w); }
    for (let a = Math.ceil(lo); a <= Math.floor(hi); a++) covered[(a + 360) % 360] = true;
  }
  const inner = rMin * Math.cos(Math.PI / 180 * 8);   // a wedge's inner face is a chord (<= 16 deg): its middle sits this close
  check(inner > PAD_R, `the shell's inner face (${inner.toFixed(1)} from the pad) never cuts into the ${PAD_R} trigger: only a player inside the machine launches`,
        `the shell (inner face ${inner.toFixed(1)}) reaches into the ${PAD_R} trigger circle`);
  check(PAD_R >= inner - HALF_P, `no dead corner: a player pressed against the inner wall stands ${(inner - HALF_P).toFixed(1)} from the centre, inside the ${PAD_R} trigger`,
        `a player against the machine's inner wall stands ${(inner - HALF_P).toFixed(1)} from the centre, outside the ${PAD_R} trigger: inside the machine and not launched`);
  check(rMax <= 130, `the shell ends at ${rMax.toFixed(1)} (the machine's plinth)`, `the shell reaches ${rMax.toFixed(1)} from the pad - wider than the machine`);
  // the opening: the longest run of uncovered degrees
  let best = { len: 0, mid: null };
  for (let s = 0; s < 360; s++) {
    if (covered[s] || !covered[(s + 359) % 360]) continue;
    let len = 0; while (len < 360 && !covered[(s + len) % 360]) len++;
    if (len > best.len) best = { len, mid: (s + len / 2) % 360 };
  }
  const off = (a, b) => { const d = Math.abs(((a - b) % 360 + 360) % 360); return Math.min(d, 360 - d); };
  const door = (YAW + 180) % 360, toHall = ang(PAD[0], BAL[1]);
  check(best.mid !== null && best.len >= 40 && best.len <= 70 && off(best.mid, door) <= 3,
        `the shell is open ${best.len} deg round ${best.mid === null ? '-' : best.mid.toFixed(0)} deg = the machine's doorway (yaw ${YAW} + 180)`,
        `the shell's opening (${best.len} deg round ${best.mid}) is not the machine's doorway at ${door} deg`);
  check(off(door, toHall) <= 3, `the doorway faces the bridge corridor (${toHall.toFixed(0)} deg, the balcony's north edge)`,
        `the machine's doorway faces ${door} deg but the party walks in from ${toHall.toFixed(0)} deg`);
}
// The overlook curb is low, but its invisible collision still reaches the
// original 168u rail/cap top. This must not open a hop-over or a gap below clip.
const balcony = brushes.find(b => b.label === 'causeway launch deck');
if (balcony) {
  const adjacent = b => [0,1].some(a => {
    const o=1-a;
    return (Math.abs(b.hi[a]-balcony.lo[a])<.01 || Math.abs(b.lo[a]-balcony.hi[a])<.01)
      && b.hi[o]>balcony.lo[o] && b.lo[o]<balcony.hi[o];
  });
  const rails=brushes.filter(b=>b.label.startsWith('causeway rail ')&&!b.label.endsWith(' cap')&&adjacent(b));
  check(rails.length===5, 'five balcony curb runs', `expected five balcony curb runs, got ${rails.length}`);
  for (const rail of rails) {
    const cap=brushes.find(b=>b.label===rail.label+' cap'), floor=balcony.hi[2];
    check(rail.lo[2]===floor&&rail.hi[2]-floor===12, `${rail.label}: visible curb 12u`, `${rail.label}: balcony view blocked by a tall rail`);
    check(cap&&cap.lo[2]===floor&&cap.hi[2]===floor+168&&
      [0,1].every(a=>cap.lo[a]===rail.lo[a]&&cap.hi[a]===rail.hi[a])&&cap.planes.every(p=>p.mat==='clip'),
      `${rail.label}: continuous invisible barrier to 168u`, `${rail.label}: collision gap or lowered barrier`);
  }
}
else check(false, '', 'launch deck missing from balcony curb check');
const HALF = 16, TALL = 72;
// a player box against a brush: AABB overlap, then every brush plane must fail
// to separate (the box's nearest corner to the plane is inside it). Strict
// inequalities, so standing ON a deck (box bottom == deck top) is not a hit.
function boxHits(p, b) {
  const lo = [p[0] - HALF, p[1] - HALF, p[2]], hi = [p[0] + HALF, p[1] + HALF, p[2] + TALL];
  for (let a = 0; a < 3; a++) if (!(lo[a] < b.hi[a] - 0.01 && hi[a] > b.lo[a] + 0.01)) return false;
  for (const q of b.planes) {
    const c = [q.n[0] >= 0 ? lo[0] : hi[0], q.n[1] >= 0 ? lo[1] : hi[1], q.n[2] >= 0 ? lo[2] : hi[2]];
    if (CB.dot(q.n, c) >= q.d - 0.01) return false;
  }
  return true;
}
const starts = [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]].map(([dx, dy]) => [PAD[0] + dx * PAD_R, PAD[1] + dy * PAD_R, PAD[2]]);
const N = 400;
let hits = [], apexZ = -Infinity;
for (const src of starts)
  for (const dst of SPOTS) {
    const x1 = Math.min(src[0], dst[0]) - 64, x2 = Math.max(src[0], dst[0]) + 64;
    const y1 = Math.min(src[1], dst[1]) - 64, y2 = Math.max(src[1], dst[1]) + 64;
    // the machine's own shell is skipped: it is invisible clip round the take-off (2b binds it to the trigger), and the
    // rider is linked to a mover, so clip stops nothing - what must stay clear is everything a camera could fly through
    const near = brushes.filter(b => b.hi[0] > x1 && b.lo[0] < x2 && b.hi[1] > y1 && b.lo[1] < y2 && b.hi[2] > src[2] - 8
                                     && !/^jump pad shell \d+$/.test(b.label));
    for (let i = 0; i <= N; i++) {
      const u = i / N, lift = 4 * APEX * u * (1 - u);
      const p = [src[0] + (dst[0] - src[0]) * u, src[1] + (dst[1] - src[1]) * u, src[2] + (dst[2] - src[2]) * u + lift];
      if (p[2] > apexZ) apexZ = p[2];
      for (const b of near) if (boxHits(p, b)) { hits.push(`u=${u.toFixed(3)} at (${p.map(v => v.toFixed(0)).join(',')}) inside "${b.label}"`); break; }
    }
  }
check(hits.length === 0, `the arc is clear: ${starts.length} take-offs x ${SPOTS.length} spots x ${N + 1} samples, apex z ${apexZ.toFixed(0)}`,
      `the arc passes through geometry (${hits.length} samples) — first: ${hits.slice(0, 4).join(' | ')}`);

// ---- 3b. THE HANG CLOCK (docs/196) ---------------------------------------------
// The script walks the SAME parabola swept above on a warped clock, hang_u(). This
// replays the script's OWN defines through the same formula and proves the clock
// can never run backwards or stall, ends exactly on the spot, and gives what the
// user asked for: more time near the top and a soft touch-down, on BOTH flights.
const num = (n) => { const m = jp.match(new RegExp(`#define ${n}\\s+\\(?\\s*(-?[\\d.]+)\\s*\\)?`)); if (!m) throw new Error(`test_jumppad: no numeric #define ${n}`); return Number(m[1]); };
const W = { A: num('TOD_JUMPPAD_WARP_A'), B: num('TOD_JUMPPAD_WARP_B'), C: num('TOD_JUMPPAD_WARP_C'), D: num('TOD_JUMPPAD_WARP_D'), L: num('TOD_JUMPPAD_WARP_L') };
const FLIGHT = num('TOD_JUMPPAD_FLIGHT_SECS'), CINE = num('TOD_JUMPPAD_CINE_SECS'), STEP = num('TOD_JUMPPAD_STEP');
const TP = 2 * Math.PI;
const hangU = t => t + W.A * Math.sin(TP * t) / TP - W.B * (Math.cos(TP * t) - 1) / TP
  + W.C * Math.sin(2 * TP * t) / (2 * TP) - W.D * (Math.cos(2 * TP * t) - 1) / (2 * TP) + W.L * (t - t * t);
const speed = t => 1 + W.A * Math.cos(TP * t) + W.B * Math.sin(TP * t) + W.C * Math.cos(2 * TP * t) + W.D * Math.sin(2 * TP * t) + W.L * (1 - 2 * t);
check(/function hang_u\( t \)[\s\S]{0,220}sin\( a \)[\s\S]{0,420}\( t - t \* t \)/.test(jp), 'hang_u() is the replayed formula', '_tod_jumppad.gsc hang_u() no longer matches the formula this test replays');
check(Math.abs(hangU(0)) < 1e-9 && Math.abs(hangU(1) - 1) < 1e-9, 'the hang clock starts at the pad and ends on the spot (u 0 -> 1)', `hang_u(0)=${hangU(0)} hang_u(1)=${hangU(1)}`);
let minS = Infinity, backwards = 0;
for (let i = 0; i <= 4000; i++) { const t = i / 4000; minS = Math.min(minS, speed(t)); if (i && hangU(t) < hangU((i - 1) / 4000)) backwards++; }
check(minS > 0.15 && backwards === 0, `the hang clock only moves forward (slowest ${minS.toFixed(2)}x the mean)`, `the hang clock stalls or runs backwards (min speed ${minS.toFixed(3)}, ${backwards} backward samples)`);
check(speed(0) >= 1.3 && speed(0.5) <= 0.7 && speed(1) <= 0.4,
      `launch ${speed(0).toFixed(2)}x / apex ${speed(0.5).toFixed(2)}x / touch-down ${speed(1).toFixed(2)}x the mean speed`,
      `the hang profile lost its shape: launch ${speed(0).toFixed(2)} apex ${speed(0.5).toFixed(2)} touch-down ${speed(1).toFixed(2)}`);
const dist = Math.hypot(SPOTS[0][0] - PAD[0], SPOTS[0][1] - PAD[1]);
// THE DWELL (2026-10-01, the user: "The pause mid air jump scene should last another 500ms before going down"): a FIRST
// flight walks the same arc on the same hang clock (CINE - DWELL long) with DWELL seconds slipped in round the apex,
// cine_arc_frac() in the script (a raised-cosine slow-down). This replica is proven against the shipping function below.
const DW = { DWELL: num('TOD_JUMPPAD_CINE_DWELL'), AT: num('TOD_JUMPPAD_CINE_DWELL_AT'), SPAN: num('TOD_JUMPPAD_CINE_DWELL_SPAN') };
const cineFrac = (t, dw = DW) => {
  let x = t - (dw.AT - dw.SPAN * 0.5);
  if (x > dw.SPAN) x = dw.SPAN;
  if (x > 0) t -= dw.DWELL * (x / dw.SPAN - Math.sin(TP * x / dw.SPAN) / TP);
  return t / (CINE - dw.DWELL);
};
const FLIGHTS = [['every flight', FLIGHT, t => hangU(t / FLIGHT), FLIGHT],
                 ['the first flight (scene)', CINE, t => hangU(Math.min(1, cineFrac(t))), CINE - DW.DWELL]];
for (const [name, T, uAt, arcT] of FLIGHTS) {
  let top = 0; for (let i = 0; i < 20000; i++) { const u = uAt((i + 0.5) * T / 20000); if (4 * u * (1 - u) >= 0.8) top += T / 20000; }
  const vz = 4 * APEX * speed(1) / arcT, oldTop = 0.4472 * 4.5, oldVz = 4 * 2200 / 4.5;
  check(top > oldTop * 1.5 && vz < oldVz * 0.35,
        `${name}: ${T}s, ${top.toFixed(1)}s in the top fifth of the arc (was ${oldTop.toFixed(1)}), touch-down ${vz.toFixed(0)} u/s down (was ${oldVz.toFixed(0)})`,
        `${name}: not enough hang (${top.toFixed(2)}s near the top) or too hard a landing (${vz.toFixed(0)} u/s)`);
  // SMOOTHNESS: the mover walks straight MoveTo segments, so what a rider can feel
  // is how much one segment differs from the next (a velocity kink), not how long
  // one is. The old flight kinked 8.7u per 0.1s segment (its constant gravity).
  const n = Math.round(T / STEP), seg = [];
  for (let i = 1; i <= n; i++) { const a = uAt((i - 1) * T / n), b = uAt(i * T / n); seg.push([dist * (b - a), 4 * APEX * ((b - b * b) - (a - a * a))]); }
  let kink = 0, peak = 0;
  for (let i = 0; i < seg.length; i++) { peak = Math.max(peak, Math.hypot(...seg[i]) / STEP); if (i) kink = Math.max(kink, Math.hypot(seg[i][0] - seg[i - 1][0], seg[i][1] - seg[i - 1][1])); }
  check(kink < 8.7, `${name}: smooth — the largest kink between ${STEP}s segments is ${kink.toFixed(2)}u (the old flight: 8.7u); peak speed ${peak.toFixed(0)} u/s`,
        `${name}: a ${kink.toFixed(2)}u kink between segments would read as a hitch`);
}
check(CINE > FLIGHT, 'the first flight is the longer one', `TOD_JUMPPAD_CINE_SECS ${CINE} must exceed TOD_JUMPPAD_FLIGHT_SECS ${FLIGHT}`);
// THE DWELL's contract: the whole of it is spent at the top, nothing before the ignite moves (the crash is framed on
// the arc up to there), the swing back finds the rider where it always did, and the clock never comes near a stop.
{
  const IGNITE = num('TOD_JUMPPAD_CINE_IGNITE_AT');
  const SWING0 = num('TOD_JUMPPAD_CINE_TURN_AT') + num('TOD_JUMPPAD_CINE_TURN_SECS') + num('TOD_JUMPPAD_CINE_HOLD_SECS');
  let lo = 0, hi = 1;
  for (let k = 0; k < 60; k++) { const m = (lo + hi) / 2; if (hangU(m) < 0.5) lo = m; else hi = m; }
  const nearTop = (uAt, T) => { let s = 0; for (let i = 0; i < 40000; i++) { const u = uAt((i + 0.5) * T / 40000); if (4 * APEX * u * (1 - u) >= APEX - 50) s += T / 40000; } return s; };
  const dwellBad = (dw) => {
    const e = [], arcT = CINE - dw.DWELL, t0 = dw.AT - dw.SPAN / 2, t1 = dw.AT + dw.SPAN / 2;
    const f = (t) => cineFrac(t, dw);
    if (Math.abs(f(0)) > 1e-9 || Math.abs(f(CINE) - 1) > 1e-9) e.push(`the first flight's clock runs ${f(0)} -> ${f(CINE)}, not 0 -> 1 (CINE_SECS - DWELL must be the arc's own length)`);
    if (1 - 2 * dw.DWELL / dw.SPAN < 0.5) e.push(`the dwell slows the arc to ${(1 - 2 * dw.DWELL / dw.SPAN).toFixed(2)}x: too close to a stop (widen DWELL_SPAN)`);
    if (t0 < IGNITE + 0.1) e.push(`the dwell starts at ${t0.toFixed(2)} s, before the ignite (${IGNITE}): it would move the rider off the crash's framing`);
    if (t1 > SWING0) e.push(`the dwell ends at ${t1.toFixed(2)} s, after the swing back (${SWING0.toFixed(2)})`);
    const midArc = f(dw.AT) * arcT, apexArc = lo * arcT;
    if (Math.abs(midArc - apexArc) > 0.05) e.push(`the dwell's middle is ${midArc.toFixed(2)} s into the arc, the apex ${apexArc.toFixed(2)}: off the top`);
    const gain = nearTop(t => hangU(Math.min(1, f(t))), CINE) - nearTop(t => hangU(t / arcT), arcT);
    if (Math.abs(gain - dw.DWELL) > 0.06) e.push(`the dwell adds ${gain.toFixed(2)} s within 50 u of the apex, not ${dw.DWELL}`);
    return e;
  };
  const bad = dwellBad(DW);
  check(!bad.length, `THE DWELL: +${DW.DWELL}s at the top (${(DW.AT - DW.SPAN / 2).toFixed(2)}..${(DW.AT + DW.SPAN / 2).toFixed(2)} s, after the ignite, before the swing back), the arc's pace never under ${(1 - 2 * DW.DWELL / DW.SPAN).toFixed(2)}x`,
        'THE DWELL: ' + bad.join(' | '));
  check(dwellBad({ ...DW, AT: DW.AT - 1 }).length > 0, 'negative control: a dwell 1 s off the apex is caught', 'NEGATIVE CONTROL MISSED: an off-apex dwell passed');
  check(dwellBad({ ...DW, SPAN: 4.0 }).length > 0, 'negative control: a dwell reaching back before the ignite is caught', 'NEGATIVE CONTROL MISSED: a dwell over the crash passed');
  // the replica IS the shipping function (tools/sky_ships/gsc_eval.js runs cine_arc_frac itself)
  const { gscLoad } = require('./sky_ships/gsc_eval.js');
  const defs = Object.fromEntries([...jp.matchAll(/^#define (\w+)\s+\(?\s*(-?[\d.]+)\s*\)?/gm)].map(m => [m[1], Number(m[2])]));
  const g = gscLoad([['tod_jumppad', jp]], defs, { builtins: { sin: x => Math.sin(x * Math.PI / 180) } });
  let worst = 0;
  for (let t = 0; t <= CINE + 1e-9; t += STEP) worst = Math.max(worst, Math.abs(g.call('cine_arc_frac', [t]) - cineFrac(t)));
  check(worst < 1e-9, `the shipping cine_arc_frac() is the replayed dwell (worst ${worst.toExponential(1)})`, `_tod_jumppad.gsc cine_arc_frac() differs from the replayed dwell by ${worst}`);
  check(/function arc_point\( src, d, i, n, cine \)[\s\S]{0,200}hang_u\( cine_arc_frac\( i \* TOD_JUMPPAD_STEP \) \)/.test(jp),
        'arc_point walks a first flight on the dwell clock', 'arc_point() no longer walks a first flight through cine_arc_frac()');
}

// ---- 3c. THE OPENING SCENE (docs/196) --------------------------------------------
// The camera aims at the sky's title sign. WHERE THAT SIGN IS IN GAME (docs/196 §3, MEASURED
// 2026-09-29 on the user's second play): the engine turns the WHOLE sky by the SSI's SUN AZIMUTH
// plus the material's skyRotation:
//     the image's centre column faces world yaw  -(sunAz + skyRotation)      (image-right = the viewer's right)
//     sunAz = the SSI yaw when its pitch is past 90 (the light travels down the far side), else yaw + 180
// The raw render's sign sits on its centre column; finish_sky.py np.rolls the picture `roll`
// degrees (+ = content moves right = toward lower yaw), so the sign stands at -(sunAz + rot) - roll.
// THE EVIDENCE (the self-checks below re-derive each one from this rule):
//   * the user's 15:33 screenshot (roll 0, rot 180, sun 140): the view rebuilt from the .map + the
//     equirect puts the sign's centre at yaw 41.4 (+-1.5); the rule says 40. The old reading
//     "-roll + skyRotation" (180) is what sent the jump camera to an empty sky.
//   * Nastian's T9 skies paint the sun on the centre column with pitch past 90 AND under 90:
//     only the sun-azimuth term lines both up (zm_tungsten: sun column u 0.5338, the rule 0.5336).
//   * Treyarch's mp_sector (rot 236, sun 244): its painted sun (u 0.49-0.52) at the rule's 0.489.
// A consequence to guard: changing ANY live SSI's yaw now turns the visible sky, so every SSI the
// sun volume uses is read and each must put the sign where the camera looks.
// LOCKSTEP: docs/sky_preview/sky3d_stats.json (roll), source_data/tod_skybox.gdt
// (mtl_skybox_tod_cybercity "skyRotation" + the SSIs' yaw / pitch), the .map's volume_sun ssi keys
// and TOD_JUMPPAD_CINE_SIGN_YAW.
const norm360 = (a) => ((a % 360) + 360) % 360;
const yawOff = (a, b) => { const d = Math.abs(norm360(a) - norm360(b)); return Math.min(d, 360 - d); };
const sunAz = (yaw, pitch) => (Math.cos(pitch * Math.PI / 180) < 0 ? norm360(yaw) : norm360(yaw + 180));
const skyCentre = (sun, rot) => norm360(-(sun + rot));                  // the image's centre column, world yaw
const signYaw = (roll, rot, sun) => norm360(skyCentre(sun, rot) - roll); // the raw centre moved `roll` right
const sunColumn = (sun, rot) => norm360((0.5 - (2 * sun + rot) / 360) * 360) / 360;   // where a sky's own sun must be painted
{ // the rule against the measurements (a regression to any other rule fails here first)
  const shot = signYaw(0, 180, 140);
  check(yawOff(shot, 41.4) <= 3, `sky rule: roll 0 + skyRotation 180 + sun 140 -> the sign at yaw ${shot} (the user's screenshot measured 41.4)`,
        `sky rule self-check: the screenshot's setup gives ${shot}, measured 41.4`);
  check(yawOff(norm360(-0 + 180), 41.4) > 90, 'sky rule: the old "-roll + skyRotation" reading misses the screenshot by > 90 deg (it is dead)',
        'sky rule self-check: the old reading would pass the screenshot');
  const tung = sunColumn(sunAz(353.96, 24.32), 0);
  check(Math.abs(tung - 0.5338) * 360 <= 1, `sky rule: Nastian zm_tungsten's painted sun at u ${tung.toFixed(4)} (measured 0.5338)`,
        `sky rule self-check: zm_tungsten's sun column ${tung.toFixed(4)} vs 0.5338`);
  const sector = sunColumn(sunAz(244, 150), 236);
  check(sector > 0.47 && sector < 0.53, `sky rule: Treyarch mp_sector's painted sun at u ${sector.toFixed(3)} (measured 0.49-0.52)`,
        `sky rule self-check: mp_sector's sun column ${sector.toFixed(3)}`);
}
const statsPath = path.join(REPO, 'docs', 'sky_preview', 'sky3d_stats.json');
const skyGdtPath = path.join(REPO, 'source_data', 'tod_skybox.gdt');
function ssiOf(gdt, name) {                     // -> { yaw, pitch } of an SSI defined in the GDT, or null
  const block = gdt.split('"' + name + '" ( "ssi.gdf" )')[1];
  if (!block) return null;
  const body = block.slice(0, block.indexOf('\n\t}'));
  const y = body.match(/"yaw" "(-?[\d.]+)"/), p = body.match(/"pitch" "(-?[\d.]+)"/);
  return y && p ? { yaw: Number(y[1]), pitch: Number(p[1]) } : null;
}
function sunVolumeSsis(mapText) {               // every ssi / ssi1..ssi4 the map's volume_sun names
  const ent = mapText.split(/\n\{\n/).find((b) => /"classname" "volume_sun"/.test(b)) || '';
  return [...new Set([...ent.matchAll(/"ssi\d?" "([^"]+)"/g)].map((m) => m[1]))];
}
function skyCheck(roll, rot, gdt, mapText, have) {   // -> { good, bad } for the live scene
  const names = sunVolumeSsis(mapText);
  if (!names.length) return { bad: 'the map\'s volume_sun names no SSI: cannot prove where the sky\'s sign is (docs/196 §3)' };
  const rows = [];
  for (const n of names) {
    const s = ssiOf(gdt, n);
    if (!s) return { bad: `SSI ${n} (the volume_sun's) has no yaw / pitch in source_data/tod_skybox.gdt: cannot prove where the sky's sign is` };
    const az = sunAz(s.yaw, s.pitch), y = signYaw(roll, rot, az);
    if (yawOff(y, have) > 1) {
      const need = norm360(-az - roll - have);
      return { bad: `with SSI ${n} (sun ${az}) + skyRotation ${rot} + roll ${roll} the sky's sign is at yaw ${y}, but the camera looks at ${have}: set skyRotation ${need} (docs/196 §3)` };
    }
    rows.push(`${n} sun ${az}`);
  }
  return { good: `the scene looks where the sky's sign is: -(sun + skyRotation ${rot}) - roll ${roll} = yaw ${have} for every live SSI (${rows.join(', ')})` };
}
if (fs.existsSync(statsPath) && fs.existsSync(skyGdtPath)) {
  const roll = Number(JSON.parse(read(statsPath)).roll || 0);
  const gdt = read(skyGdtPath);
  const mtl = gdt.split('"mtl_skybox_tod_cybercity" ( "material.gdf" )')[1] || '';
  const rm = mtl.match(/"skyRotation" "(-?[\d.]+)"/);
  const have = norm360(num('TOD_JUMPPAD_CINE_SIGN_YAW'));
  const mapText = read(MAP);
  if (!rm) fails.push('mtl_skybox_tod_cybercity has no "skyRotation": cannot prove where the sky\'s sign is (docs/196 §3)');
  else {
    const rot = Number(rm[1]);
    const r = skyCheck(roll, rot, gdt, mapText, have);
    if (r.good) ok.push(r.good); else fails.push(r.bad);
    // NEGATIVE CONTROLS: the 15:33 build's skyRotation 180, and a live SSI turned 10 deg, must both be caught
    const n1 = skyCheck(roll, 180, gdt, mapText, have);
    check(!!n1.bad, 'negative control: the played skyRotation 180 (the sign at ~40) is caught', 'NEGATIVE CONTROL MISSED: skyRotation 180 passed');
    const turned = gdt.replace(/("tod_ssi_cybercity" \( "ssi\.gdf" \)[\s\S]*?"yaw" ")(-?[\d.]+)(")/, (m, a, v, b) => a + (Number(v) + 10) + b);
    const n2 = skyCheck(roll, rot, turned, mapText, have);
    check(!!n2.bad, 'negative control: an SSI yaw turned 10 deg (it turns the visible sky) is caught', 'NEGATIVE CONTROL MISSED: a turned SSI passed');
  }
} else check(false, '', 'docs/sky_preview/sky3d_stats.json or source_data/tod_skybox.gdt missing: cannot prove where the sky\'s sign is');
const pitch = num('TOD_JUMPPAD_CINE_SIGN_PITCH');
check(pitch <= -4 && pitch >= -20, `the scene frames the text box ${-pitch} deg up`, `TOD_JUMPPAD_CINE_SIGN_PITCH ${pitch} is outside the sign's band`);
const tl = ['TURN_AT', 'TURN_SECS', 'HOLD_SECS', 'BACK_SECS'].map(k => num('TOD_JUMPPAD_CINE_' + k)).reduce((a, b) => a + b, 0);
check(tl + num('TOD_JUMPPAD_CINE_FREE_SECS') + 0.6 <= CINE, `the scene (${tl.toFixed(1)}s + ${num('TOD_JUMPPAD_CINE_FREE_SECS')}s release) ends before the touch-down (${CINE}s)`,
      `the scene timeline (${tl}s) overruns the flight (${CINE}s): the camera would still be locked at the landing`);
check(/#precache\( "eventstring", "tod_jump_cine" \);/.test(jp), 'tod_jump_cine eventstring precached', 'the letterbox event is not precached (it would silently never fire)');
// THE CRASH (docs/196 §4): the client scene's five beats (tod_jump_title_start / _ships / _impact / _ignite /
// _end; session 9c's salute hears _ignite). Their timing, framing and wiring are proven by
// tools/jump_title/test_jump_title.js; here only that the retired reveal hook is gone.
check(!/tod_jump_reveal/.test(jp) && (jp.match(/util::clientNotify\( "tod_jump_title_start" \)/g) || []).length === 1,
      'the scene opens the client crash once (tod_jump_title_start); the retired tod_jump_reveal hook is gone', 'the client beat contract changed shape (see tools/jump_title/test_jump_title.js)');
const cineEnd = (jp.match(/function cine_end\([\s\S]*?\n\}/) || [''])[0];
check(/ShowViewModel\(\)/.test(cineEnd) && /tod_menu_frozen/.test(cineEnd) && /LuiNotifyEvent\( &"tod_jump_cine", 1, 0 \)/.test(cineEnd) && /cine_title_end\(\)/.test(cineEnd),
      'cine_end restores the gun (never over a menu), the letterbox and ends the client crash', 'cine_end no longer restores every piece the scene took');
check(/function finish\(\)\s*\{\s*self cine_end\(/.test(jp), 'every flight end (landing, death, disconnect) runs cine_end first', 'finish() must run cine_end first');
check(/tod_upgrade_pause[\s\S]{0,40}tod_menu_frozen/.test((jp.match(/function cine_wait\([\s\S]*?\n\}/) || [''])[0]), 'a card deal or menu freeze tears the scene down at once', 'cine_wait no longer yields to a card deal');
check(/#define TOD_JUMPPAD_CINE_EVERY\s+0\b/.test(jp), 'the scene plays on the first flight only (CINE_EVERY 0)', 'TOD_JUMPPAD_CINE_EVERY is armed — the user asked for the first time only');
const atmo = read(path.join(MOD, '_tod_atmosphere.gsc'));
// 2026-09-29 (user: "the first song starts up once you enter the crown balcony that the jump pad
// lives on. No mid air on the jump pad"): the band's cue is a living player inside the GENERATED
// balcony box, BEFORE the flight; the reveal stays as the fallback cue.
const ambient = (atmo.match(/function ambient_music\(\)[\s\S]*?\n\}/) || [''])[0];
const balconyFn = (atmo.match(/function balcony_player\(\)[\s\S]*?\n\}/) || [''])[0];
check(/p = balcony_player\(\);/.test(ambient) && ambient.indexOf('balcony_player()') < ambient.indexOf('IS_TRUE( level.tod_jump_title )')
      && /level util::waittill_any_timeout\( [\d.]+, "tod_jump_title" \);/.test(ambient)
      && /tod_crown_data::jumppad_balcony_mins\(\)/.test(balconyFn) && /tod_crown_data::jumppad_balcony_maxs\(\)/.test(balconyFn)
      && /level notify\( "tod_jump_title" \);/.test(jp),
      'the first band starts when a player steps onto the jump-pad balcony (the reveal is the fallback)', 'the music no longer starts on the balcony');
{
  const crownData = read(path.join(MOD, '_tod_crown_data.gsc'));
  const num = s => (s || '').replace(/[()\s]/g, '').split(',').map(Number);
  const mn = num((crownData.match(/function jumppad_balcony_mins\(\)\s*\{\s*return (\([^)]*\))/) || [])[1]);
  const mx = num((crownData.match(/function jumppad_balcony_maxs\(\)\s*\{\s*return (\([^)]*\))/) || [])[1]);
  const pad = num((crownData.match(/function jumppad_launch_org\(\)\s*\{\s*return (\([^)]*\))/) || [])[1]);
  const inside = mn.length === 3 && mx.length === 3 && pad.length === 3 && [0, 1, 2].every(i => pad[i] >= mn[i] && pad[i] <= mx[i]);
  check(inside, 'the GENERATED balcony box holds the launch pad', 'the balcony box is missing or does not hold the launch pad');
}

// ---- 3d. THE CAMERA PATH (the second pass, 2026-09-30) ------------------------------
// The user after the first real run of the scene: "The cinematic view jump is okay but its not super smooth. The
// player wavers back and forth towards the end of jump". The first pass locked the view with a LerpViewAngleClamp
// closing late onto a mover turned by four separate RotateTo moves (the rider's own look was squeezed out mid-turn),
// and at the end dipped the view 32 deg down and pulled it 24 deg back up while handing control back. The camera is
// now ONE path, cine_cam_plan / cine_cam_angles, stepped with the arc every server frame. This RUNS those shipping
// functions (tools/sky_ships/gsc_eval.js, never a copy) from 63 launch views to every landing spot, at the server's
// own step, and proves:
//   * no jump when the lock closes: the path starts exactly on the rider's own view;
//   * smooth: no step over MAX_STEP deg a frame, no change of pace over MAX_KINK deg between frames;
//   * no waver: pitch and yaw each move ONE way through the turn and ONE way through the return;
//   * still when control comes back: no motion from the end of the return (FREE) to the touch-down;
//   * on the sign through the hold, and landing on the flight's heading, LAND_PITCH down.
// Two negative controls must FAIL it: the first pass's ending (down to 32, back up) and a lock that snaps.
{
  const { gscLoad, V } = require('./sky_ships/gsc_eval.js');
  const A180 = (a) => { let r = ((a % 360) + 360) % 360; if (r > 180) r -= 360; return r; };
  const defs = Object.fromEntries([...jp.matchAll(/^#define (\w+)\s+\(?\s*(-?[\d.]+)\s*\)?/gm)].map(m => [m[1], Number(m[2])]));
  const g = gscLoad([['tod_jumppad', jp]], defs, { builtins: { AngleClamp180: A180 } });
  const TURN_AT = num('TOD_JUMPPAD_CINE_TURN_AT'), SETTLE = TURN_AT + num('TOD_JUMPPAD_CINE_TURN_SECS');
  const SWING = SETTLE + num('TOD_JUMPPAD_CINE_HOLD_SECS'), FREE = SWING + num('TOD_JUMPPAD_CINE_BACK_SECS');
  const LANDP = num('TOD_JUMPPAD_CINE_LAND_PITCH'), SIGNP = num('TOD_JUMPPAD_CINE_SIGN_PITCH'), SIGNY = num('TOD_JUMPPAD_CINE_SIGN_YAW');
  const MAX_STEP = 7.5, MAX_KINK = 1.6;   // deg per 0.05 s frame (150 deg/s), deg of pace change frame to frame
  const path = (view, fy) => {
    const plan = g.call('cine_cam_plan', [V(view[0], view[1], 0), fy]);
    return (t) => { const a = g.call('cine_cam_angles', [plan, t]); return [a[0], a[1]]; };
  };
  const judge = (cam, view, fy) => {
    const e = [], n = Math.round(CINE / STEP), s = [];
    for (let i = 0; i <= n; i++) s.push(cam(i * STEP));
    if (Math.abs(s[0][0] - view[0]) > 1e-6 || Math.abs(A180(s[0][1] - view[1])) > 1e-6)
      e.push(`the lock jumps from the rider's view (${view.map(v => v.toFixed(1))}) to (${s[0].map(v => v.toFixed(1))})`);
    const dir = { turn: [0, 0], back: [0, 0] };
    let prev = null, peak = 0;
    for (let i = 1; i <= n && !e.length; i++) {
      const t = i * STEP, d = [s[i][0] - s[i - 1][0], A180(s[i][1] - s[i - 1][1])], step = Math.hypot(d[0], d[1]);
      peak = Math.max(peak, step / STEP);
      if (step > MAX_STEP) e.push(`a ${step.toFixed(1)} deg step at ${t.toFixed(2)} s`);
      else if (prev && Math.hypot(d[0] - prev[0], d[1] - prev[1]) > MAX_KINK) e.push(`a ${Math.hypot(d[0] - prev[0], d[1] - prev[1]).toFixed(2)} deg jolt at ${t.toFixed(2)} s`);
      else if (t > FREE + 1e-9 && step > 1e-7) e.push(`the camera still turns after control comes back (${t.toFixed(2)} s, ${step.toFixed(3)} deg)`);
      prev = d;
      const ph = t <= SETTLE + 1e-9 ? 'turn' : (t > SWING + 1e-9 ? 'back' : null);
      if (ph) for (const k of [0, 1]) {
        if (Math.abs(d[k]) < 1e-7) continue;
        if (dir[ph][k] && dir[ph][k] !== Math.sign(d[k])) { e.push(`the ${k ? 'yaw' : 'pitch'} turns back during the ${ph === 'turn' ? 'turn' : 'return'} (${t.toFixed(2)} s): a waver`); break; }
        dir[ph][k] = Math.sign(d[k]);
      }
    }
    const mid = cam((SETTLE + SWING) / 2), end = s[n];
    if (Math.abs(A180(mid[1] - SIGNY)) > 8 || Math.abs(mid[0] - SIGNP) > 3) e.push(`mid-hold the camera is at (${mid.map(v => v.toFixed(1))}), off the sign (${SIGNP}, ${SIGNY})`);
    if (Math.abs(end[0] - LANDP) > 1e-6 || Math.abs(A180(end[1] - fy)) > 1e-6) e.push(`it lands looking (${end.map(v => v.toFixed(1))}), not (${LANDP}, ${fy.toFixed(1)})`);
    return { e, peak };
  };
  const views = [];
  for (const vp of [-40, -10, 0, 15, 27.35, 45, 70]) for (const dy of [-170, -90, -35, -23, 0, 20, 35, 90, 170]) views.push([vp, dy]);
  const errs = [];
  let runs = 0, peak = 0, peakAt = '';
  for (const dst of SPOTS) {
    const fy = Math.atan2(dst[1] - PAD[1], dst[0] - PAD[0]) * 180 / Math.PI;
    for (const [vp, dy] of views) {
      const view = [vp, fy + dy], r = judge(path(view, fy), view, fy);
      runs++;
      if (r.peak > peak) { peak = r.peak; peakAt = `(${vp}, ${dy >= 0 ? '+' : ''}${dy})`; }
      if (r.e.length) errs.push(`launch view (${vp}, ${dy >= 0 ? '+' : ''}${dy}) to spot ${dst}: ${r.e.join('; ')}`);
    }
  }
  const logged = judge(path([27.35, -114.62], -91), [27.35, -114.62], -91).peak;
  check(!errs.length,
        `the camera path (the shipping cine_cam_angles, ${runs} flights x ${Math.round(CINE / STEP)} frames): starts on the rider's view, <= ${MAX_STEP} deg a frame with no jolt over ${MAX_KINK}, ONE way through the turn and the return, still from ${FREE.toFixed(1)} s (control back) to the touch-down, lands at ${LANDP} deg on the heading; fastest ${peak.toFixed(0)} deg/s from ${peakAt}, the user's own launch view ${logged.toFixed(0)} deg/s`,
        `the camera path: ${errs.slice(0, 3).join(' | ')}${errs.length > 3 ? ` (+${errs.length - 3} more)` : ''}`);
  // negative controls: the first pass's ending (the return dips to 32 then rises back while control returns) and a
  // lock that snaps the view to the flight's heading must both fail
  const view0 = [27.35, -114.62], fy0 = -91, good = path(view0, fy0);
  const ez = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x));
  const dip = (t) => {
    if (t <= SWING) return good(t);
    const a = good(SWING), down = ez((t - SWING) / 1.8), up = ez((t - SWING - 1.8) / 1.6);
    return [a[0] + (32 - a[0]) * down + (LANDP - 32) * up, a[1] + A180(fy0 - a[1]) * down];
  };
  check(judge(dip, view0, fy0).e.length > 0, 'negative control: the first pass\'s ending (down to 32 deg, back up under the player\'s hand) is caught',
        'NEGATIVE CONTROL MISSED: the dip-and-rise ending passed the camera checks');
  const snap = (t) => (t < TURN_AT ? [0, fy0] : good(t));
  check(judge(snap, view0, fy0).e.length > 0, 'negative control: a lock that snaps the view to the flight\'s heading is caught',
        'NEGATIVE CONTROL MISSED: a snapping lock passed the camera checks');
  // THE WIRING of the path: planned from the rider's view BEFORE the link, the link has no view arc, the arc loop steps
  // it every frame (each step wrapped next to the mover's own angles), cine_run turns nothing, a cut stops it
  const launchFn = (jp.match(/function launch\(\)[\s\S]*?\n\}/) || [''])[0];
  const runFn = (jp.match(/function cine_run\([\s\S]*?\n\}/) || [''])[0];
  const endFn = (jp.match(/function cine_end\([\s\S]*?\n\}/) || [''])[0];
  const iPlan = launchFn.indexOf('cam = cine_cam_plan( self GetPlayerAngles(), yaw[ 1 ] );');
  const iLink = launchFn.indexOf('self PlayerLinkToDelta( mover, "tag_origin", 1, 0, 0, 0, 0 );');
  check(iPlan > 0 && iLink > iPlan && /mover\.angles = cine_cam_angles\( cam, 0 \);/.test(launchFn)
        && /mover RotateTo\( cine_cam_step\( mover\.angles, cine_cam_angles\( cam, j \* TOD_JUMPPAD_STEP \) \), secs_move \);/.test(launchFn)
        && /mover MoveTo\( arc_point\( src, d, j, n, cine \), secs_move \);/.test(launchFn) && num('TOD_JUMPPAD_LOOKAHEAD') >= 2
        && !/RotateTo|LerpViewAngleClamp\([^;]*, 0, 0, 0, 0 \)/.test(runFn) && /tod_jumppad_cam_cut = true;/.test(endFn)
        && /AngleClamp180\( want\[ 1 \] - now\[ 1 \] \)/.test(jp),
        'the path is planned from the rider\'s view before a no-arc link, stepped with the arc every frame (the short way), cine_run turns nothing, a cut scene stops it',
        'the camera path\'s wiring changed: launch() must plan from GetPlayerAngles before linking with no view arc and step cine_cam_angles every frame; cine_run must not rotate or close the clamp');
}

// ---- 4. WIRING -----------------------------------------------------------------
const zone = read(path.join(REPO, 'zone_source', 'zm_tod2_cybercity.zone'));
const entry = read(path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity.gsc'));
const has = (file, re) => re.test(read(path.join(MOD, file)));
check(/^scriptparsetree,scripts\/zm\/zm_tod2_cybercity\/_tod_jumppad\.gsc\s*$/m.test(zone), 'module zoned', 'zone lacks scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_jumppad.gsc');
for (const m of MODELS) {
  check(new RegExp(`^xmodel,${m}\\s*$`, 'm').test(zone), `pad model ${m} zoned`, `zone lacks xmodel,${m} (TOD_JUMPPAD_MODEL_*)`);
  check(new RegExp(`#precache\\( "model", "${m}" \\);`).test(jp), `pad model ${m} precached`, `_tod_jumppad.gsc does not #precache ${m}`);
}
const gdt = fs.existsSync(path.join(REPO, 'source_data', 'tod_jumppad.gdt')) ? read(path.join(REPO, 'source_data', 'tod_jumppad.gdt')) : '';
check(MODELS.every(m => gdt.includes(`"${m}" ( "xmodel.gdf" )`)), 'every pad model has its block in source_data/tod_jumppad.gdt (tools/jumppad/install_de_jumppad.py)',
      'source_data/tod_jumppad.gdt lacks a pad model block - run python tools/jumppad/install_de_jumppad.py');
for (const f of FXS) {
  check(new RegExp(`^fx,${f}\\s*$`, 'm').test(zone), `effect ${f} zoned`, `zone lacks fx,${f}`);
  check(new RegExp(`#precache\\( "fx", "${f}" \\);`).test(jp), `effect ${f} precached`, `_tod_jumppad.gsc does not #precache fx ${f}`);
}
// the machine wakes dark -> blue at the power, the flights glow the landing pad until they land OR abort
check(/function power_watch\(\)[\s\S]{0,400}flag::wait_till\( "power_on" \)[\s\S]{0,200}SetModel\( TOD_JUMPPAD_MODEL_DECK_ON \)/.test(jp),
      'the deck lights blue when the power comes on', 'power_watch() no longer swaps the deck to TOD_JUMPPAD_MODEL_DECK_ON at the power');
check(/level\.tod_jumppad_flights\[ op \] = true;/.test(jp) && /function flight_guard[\s\S]{0,400}level\.tod_jumppad_flights\[ op \] = undefined;/.test(jp)
      && /notify\( "tod_jumppad_landed" \);\s*\n\s*level\.tod_jumppad_flights\[ op \] = undefined;/.test(jp),
      'an inbound flight is cleared on the set-down AND on an abort (the landing pad never glows for nobody)',
      'level.tod_jumppad_flights is not cleared on both the set-down and flight_guard\'s abort');
check(!/tod_teleport::/.test(jp.replace(/\/\/[^\n]*/g, '')), 'the pad no longer borrows the teleporter\'s effects', '_tod_jumppad.gsc still calls tod_teleport::');
check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_jumppad;/.test(entry) && /level thread tod_jumppad::init\(\);/.test(entry),
      'module #using + threaded from the entry script', 'zm_tod2_cybercity.gsc does not #using/thread tod_jumppad::init()');
check(/tod_crown_data::jumppad_enabled\(\)[\s\S]{0,400}fall_enables_roof_zone/.test(entry),
      'roof_zone enabled on the Fall gate (no crown adjacency) when the road is cut', 'zm_tod2_cybercity.gsc lacks the jumppad_enabled() roof_zone wiring');
const aliasCsv = fs.readdirSync(path.join(REPO, 'sound', 'aliases')).map(f => read(path.join(REPO, 'sound', 'aliases', f))).join('\n');
for (const s of SNDS) {
  const row = aliasCsv.split(/\r?\n/).find(l => l.startsWith(s + ','));
  const wav = row && row.split(',')[3];
  const wavOk = wav && fs.existsSync(path.join(REPO, 'sound_assets', ...wav.split('\\')));
  check(row && /,3d,,,NONLOOPING,/.test(row) && wavOk, `alias ${s}: 3D one-shot on ${wav}`,
        `alias ${s} missing, not a 3D one-shot, or its wav (${wav}) is not in sound_assets (python tools/jumppad/install_de_jumppad.py)`);
}
{
  const windAlias = def('TOD_JUMPPAD_WIND_ALIAS');
  const row = aliasCsv.split(/\r?\n/).find(l => l.startsWith(windAlias + ','));
  const wav = row && row.split(',')[3];
  const wavOk = wav && fs.existsSync(path.join(REPO, 'sound_assets', ...wav.split('\\')));
  check(row && /,3d,,,LOOPING,/.test(row) && wavOk, `alias ${windAlias}: 3D LOOPING on ${wav}`,
        `alias ${windAlias} missing, not a 3D loop, or its wav (${wav}) is not in sound_assets — the flight would be silent`);
}
const guards = [
  ['_tod_athlete.gsc', /IsMantling\(\) \|\| IS_TRUE\( self\.tod_jumppad_flying \)/, 'ATHLETE parks mid-flight'],
  // W2E (2026-10-05): _tod_bosses' anchor_player / pick_target_player retired whole with the Panzer / Protector
  // directors they served; the live elites anchor on tod_doppelghast::target_player (the cyber-elite director, the
  // crown hunters), whose valid_target is what must refuse a flyer now.
  ['_tod_bosses.gsc', /^(?![\s\S]*function (?:anchor_player|pick_target_player)\()/, 'the Map One director anchors stay retired'],
  ['_tod_doppelghast.gsc', /function valid_target\([\s\S]{0,300}tod_jumppad_flying/, 'the live elite anchor (valid_target) skips flyers'],
  ['_tod_endless_rounds.gsc', /tod_fall_sealed[\s\S]{0,900}on_crown_island/, 'no riser on the sealed island'],
  ['_tod_fall.gsc', /tod_jumppad_flying/, 'the Fall counts a flyer as not yet out'],
  ['_tod_fall.gsc', /hall_spawn_guard/, 'the Fall re-asserts the hall\'s spawning off after the seal'],
  ['_tod_fall.gsc', /on_crown_island/, 'the Fall seals on the crown ISLAND (hall + stub)'],
];
for (const [f, re, what] of guards) check(has(f, re), what, `${f}: missing — ${what}`);

// ---- report --------------------------------------------------------------------
for (const s of ok) console.log('  ok   ' + s);
if (fails.length) {
  console.error(`\ntest_jumppad FAILED (${fails.length}):`);
  for (const f of fails) console.error('  FAIL ' + f);
  process.exit(1);
}
console.log(`\ntest_jumppad OK — pad ${PAD} -> ${SPOTS.length} spots round ${LAND}, apex +${APEX}, model ${MODEL}.`);
