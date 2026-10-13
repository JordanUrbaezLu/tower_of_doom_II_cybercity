'use strict';
// tools/test_battle_arena.js — THE BATTLE ARENA's build gate (docs/185 v2, THE CRUCIBLE).
//
// User 2026-10-03: "the battle arena teleporter waits way too long to actually
// teleport please fix the latency. It doesnt line up. Also the battle arena needs
// to be actually designed ... no real spot to camp ... heights ... skill gap ...
// super hard as well so spawns need to be thought out and structures".
//
//   1. THE JUMP LINES UP. The shipping arena_run / arena_win are TIMED from their
//      own text: every `wait`, every server frame and every INLINE fx_burst (which
//      waits out its effect's whole life) between the use and the move. The use ->
//      jump time must equal TOD_ARENA_CHARGE_SECS (= the transit pads'
//      TOD_TP_CHARGE_SEC), the return likewise, the charge effect and sound must
//      start before the charge wait, the arrival flash two frames after the move,
//      and no fx_burst anywhere in the file may run inline. NEGATIVE CONTROL: the
//      v1 code (tools/battle_arena_fixtures/arena_teleport_v1.gsc) must time out at
//      6.6 s — the figure the user's 2026-10-01 log measured (press 482.9 s, jump
//      489.5 s) — and fail every alignment check.
//   2. THE DIRECTOR. spot_score / best_spot / elite_gate / camp_step run as SHIPPED
//      (tools/sky_ships/gsc_eval.js) on the GENERATED spawn points and gates: no
//      spawn inside TOD_ARENA_SPAWN_MIN of anyone while a legal one exists (thousands
//      of random parties over the three levels), the farthest point when none is;
//      the party's backs are favoured over their faces; a camper pulls the spawns
//      and the next elite toward them; zombies already up push spawns elsewhere;
//      the last-used point is not reused while another is legal.
//   3. THE WAVES, THE FALL GUARD, THE DATA: the harder numbers, the truth table of
//      the no-fall-damage guard, the generated room (26 spawn points of five kinds
//      on their decks, 8 gates, 4 arrivals on the dais, in_arena / on_dais bounds).
//   3b. THE ROOM'S AIR REACHES THE VOID. A fully sealed room renders INVISIBLE in
//      this toolchain (Umbra classes its air as the inside of a solid: the v1 box,
//      2026-09-28; memory stale-umbra-cache-invisible-geometry). The air of the
//      GENERATED .map is flooded at Umbra's own hole size (4: any voxel touching a
//      visible brush is solid, so a gap under ~4 closes) and every spawn point,
//      arrival and walk probe must sit in air that reaches the void. NEGATIVE
//      CONTROL: the roof slot lidded, the same flood must find the room sealed.
//      (2026-10-03: the first v2 link's `Filtered N/M inside clusters` rose
//      245/247 -> 256/258; this flood showed the room open and the rise to be dead
//      air behind the corner chamfers, so read a rise with this check, not alone.)
//   4. LOCKSTEP with _tod_teleport.gsc and _tod_zombie_speed.gsc.
//   4b. THE READABLE FIGHT (v2.1): the readout's event (precached, 6 ints, the flag
//      bits and the hot threshold LOCKSTEP with TodArena.lua, the widget attached to
//      the HUD, zoned, veiled and lifetime-tested; seven ints, the shape stock evidences),
//      hud_left / mood_index run as shipped,
//      the mood hosts over real arena surfaces with the dais last, the gate tell before
//      every set elite (threaded charge, cue, flash, then the rise), the horn / sting /
//      fanfare at their beats, the four generated cues in their alias rows and the zone
//      config, the overcharge's late-stepper warning, wave_begin before the boss wave.
//   5. MUTANTS of the shipping code, each of which must be caught.
// Usage: node tools/test_battle_arena.js
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8').replace(/\r\n/g, '\n');
const { gscLoad, V } = require('./sky_ships/gsc_eval.js');

const S = 'scripts/zm/zm_tod2_cybercity/';
const ARENA = read(S + '_tod_arena.gsc');
const DATA = read(S + '_tod_arena_data.gsc');
const HOUSE = read(S + '_tod_house_data.gsc');   // docs/207: the fall guard reads it beside the arena's
const TELEPORT = read(S + '_tod_teleport.gsc');
const SPEED = read(S + '_tod_zombie_speed.gsc');
const V1 = read('tools/battle_arena_fixtures/arena_teleport_v1.gsc');
const LAYOUT = require('./battle_arena_layout.js');

let fails = 0, checks = 0;
function check(ok, label) {
  checks++;
  if (!ok) { fails++; console.log('FAIL ' + label); }
}
const defs = text => Object.fromEntries([...text.matchAll(/^#define\s+(\w+)\s+(-?[\d.]+)/gm)].map(m => [m[1], m[2]]));

// ---------------------------------------------------------------------------
// 1. THE JUMP TIMELINE, read from the script text.
// ---------------------------------------------------------------------------
function body(text, name) {
  const i = text.indexOf(`function ${name}(`);
  if (i < 0) return null;
  let j = text.indexOf('{', i), depth = 0;
  for (; j < text.length; j++) {
    if (text[j] === '{') depth++;
    else if (text[j] === '}' && --depth === 0) break;
  }
  return text.slice(i, j + 1);
}
// Walk a function's lines in order until `stop` matches; sum the time that passes.
// wait EXPR -> EXPR (defines resolved); WAIT_SERVER_FRAME -> 0.05; an INLINE
// tod_teleport::fx_burst( key, org, SECS ... ) -> SECS + two frames (its own host
// replication wait) — exactly what _tod_teleport.gsc's fx_burst does before it returns.
function timeline(fn, D, stop) {
  const evalNum = e => Function(`return (${e.replace(/\b[A-Z_][A-Z0-9_]+\b/g, k => (k in D ? D[k] : k))});`)();
  let t = 0;
  const events = [];
  for (const raw of fn.split('\n')) {
    const line = raw.replace(/\/\/.*$/, '');
    if (stop.test(line)) { events.push({ at: t, what: 'stop', line: raw.trim() }); return { t, events, reached: true }; }
    let m = line.match(/^\s*wait\s+([^;]+);/);
    if (m) { t += evalNum(m[1]); events.push({ at: t, what: 'wait', line: raw.trim() }); continue; }
    if (/^\s*WAIT_SERVER_FRAME\s*;/.test(line)) { t += 0.05; continue; }
    const fa = callArgs(line, 'tod_teleport::fx_burst');
    if (fa) {
      const threaded = /\bthread\b/.test(line);
      events.push({ at: t, what: (threaded ? 'fx ' : 'INLINE fx ') + fa[0].replace(/"/g, ''), line: raw.trim() });
      if (!threaded) t += evalNum(fa[2]) + 0.1;
      continue;
    }
    if (/play_sound_at_origin\([^)]*"tod_teleport_fire"/.test(line)) events.push({ at: t, what: 'sound', line: raw.trim() });
    if (/tod_teleport::discharge\(/.test(line)) events.push({ at: t, what: 'discharge', line: raw.trim() });
  }
  return { t, events, reached: false };
}
const near = (a, b) => Math.abs(a - b) < 1e-6;
// the arguments of the first call to fname on a line, split at top-level commas
// (an origin like `org + ( 0, 0, 40 )` carries commas of its own)
function callArgs(line, fname) {
  const i = line.indexOf(fname + '(');
  if (i < 0) return null;
  const args = [];
  let depth = 0, cur = '';
  for (let j = i + fname.length + 1; j < line.length; j++) {
    const c = line[j];
    if (c === '(') { depth++; cur += c; }
    else if (c === ')') { if (depth === 0) { args.push(cur.trim()); return args; } depth--; cur += c; }
    else if (c === ',' && depth === 0) { args.push(cur.trim()); cur = ''; }
    else cur += c;
  }
  return null;
}
function jumpSuite(text, label) {
  const out = [];
  const t = (ok, msg) => { if (!ok) out.push(`${label}: ${msg}`); };
  const D = defs(text);
  const charge = +D.TOD_ARENA_CHARGE_SECS;
  const run = body(text, 'arena_run'), win = body(text, 'arena_win');
  t(!!run && !!win, 'arena_run and arena_win exist');
  if (!run || !win) return out;
  // no inline fx_burst anywhere in the file
  const inline = text.split('\n').filter(l => /tod_teleport::fx_burst\(/.test(l.replace(/\/\/.*$/, '')) && !/\bthread\b/.test(l));
  t(inline.length === 0, `no fx_burst may run inline (it waits out its effect): ${inline.length} found`);
  // the way in: use -> the move
  const go = timeline(run, D, /\bSetOrigin\(/);
  t(go.reached, 'arena_run moves the party');
  t(near(go.t, charge), `use -> jump takes the charge exactly (${charge}s); got ${go.t.toFixed(2)}s`);
  const ev = (tl, what) => tl.events.filter(e => e.what === what || e.what.startsWith(what));
  const fxIn = ev(go, 'fx tod_tp_charge')[0], sndIn = ev(go, 'sound')[0];
  t(!!fxIn && near(fxIn.at, 0), 'the charge effect starts at the use');
  t(!!sndIn && near(sndIn.at, 0), 'the charge sound starts at the use (with the effect)');
  const dep = ev(go, 'discharge');
  t(dep.length >= 1 && near(dep[dep.length - 1].at, go.t), 'the departure flash fires in the jump frame');
  // the arrival: two frames after the move, threaded, then nothing waits before the landing breath
  const after = run.slice(run.search(/\bSetOrigin\(/));
  const arr = timeline(after, D, /\bwait\s+TOD_ARENA_LAND_SECS\b/);
  const kino = ev(arr, 'fx tod_tp_kino')[0];
  t(!!kino && near(kino.at, 0.1), `the arrival flash fires two frames after the move (got ${kino ? kino.at.toFixed(2) : 'none'}s)`);
  t(arr.reached && near(arr.t, 0.1), `the landing breath starts two frames after the move (got ${arr.t.toFixed(2)}s)`);
  // the way home
  const retSecs = +(D.TOD_ARENA_RETURN_SECS || D.TOD_ARENA_CHARGE_SECS);
  const home = timeline(win.slice(win.search(/return_org\(\)/)), D, /\bSetOrigin\(/);
  t(home.reached && near(home.t, retSecs), `return: charge -> ride takes ${retSecs}s; got ${home.t.toFixed(2)}s`);
  const fxHome = ev(home, 'fx tod_tp_charge')[0], sndHome = ev(home, 'sound')[0];
  t(!!fxHome && near(fxHome.at, 0) && !!sndHome && near(sndHome.at, 0), 'return: the charge effect and sound start together, before the wait');
  const homeAfter = timeline(win.slice(win.search(/\bSetOrigin\(/)), D, /tod_atmosphere::arena_music_end/);
  const kinoHome = ev(homeAfter, 'fx tod_tp_kino')[0];
  t(!!kinoHome && near(kinoHome.at, 0.1), `return: the arrival flash two frames after the ride (got ${kinoHome ? kinoHome.at.toFixed(2) : 'none'}s)`);
  return out;
}

const TD = defs(TELEPORT), AD = defs(ARENA), SD = defs(SPEED);
check(+AD.TOD_ARENA_CHARGE_SECS === +TD.TOD_TP_CHARGE_SEC, `LOCKSTEP TOD_ARENA_CHARGE_SECS ${AD.TOD_ARENA_CHARGE_SECS} == _tod_teleport TOD_TP_CHARGE_SEC ${TD.TOD_TP_CHARGE_SEC}`);
check(+AD.TOD_ARENA_RETURN_SECS <= 1.0, `the return charge is short (${AD.TOD_ARENA_RETURN_SECS}s)`);
check(+AD.TOD_ARENA_SPRINT_ROUND === +SD.TOD_ZSPEED_FULL_ROUND, `LOCKSTEP TOD_ARENA_SPRINT_ROUND ${AD.TOD_ARENA_SPRINT_ROUND} == TOD_ZSPEED_FULL_ROUND ${SD.TOD_ZSPEED_FULL_ROUND}`);
for (const f of jumpSuite(ARENA, 'shipping')) check(false, f);
// NEGATIVE CONTROL: the v1 code must fail, and must time out where the user's log did.
{
  const v1 = jumpSuite(V1, 'v1');
  check(v1.length >= 4, `the v1 fixture fails the jump checks (${v1.length} failures; a check that passes v1 cannot catch the bug)`);
  const D1 = defs(V1);
  const go1 = timeline(body(V1, 'arena_run'), D1, /\bSetOrigin\(/);
  check(Math.abs(go1.t - 6.6) < 0.05, `v1 use -> jump = ${go1.t.toFixed(2)}s, the 6.6 s the user's 2026-10-01 log measured`);
  const arr1 = timeline(body(V1, 'arena_run').slice(body(V1, 'arena_run').search(/\bSetOrigin\(/)), D1, /\bwait\s+TOD_ARENA_LAND_SECS\b/);
  const dis1 = arr1.events.filter(e => e.what === 'discharge').pop();
  check(!!dis1 && Math.abs(dis1.at - 3.15) < 0.01, `v1 arrival flash ${dis1 ? dis1.at.toFixed(2) : '?'}s after landing (the log: 3.15 s)`);
}

// ---------------------------------------------------------------------------
// 2. THE DIRECTOR, as shipped, on the generated room.
// ---------------------------------------------------------------------------
const IS_TRUE = x => !!x && x !== 0;
function loadArena(text) {
  return gscLoad([['tod_arena', text], ['tod_arena_data', DATA], ['tod_house_data', HOUSE]], defs(text), {
    builtins: {
      IS_TRUE,
      Distance: (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]),
      DistanceSquared: (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2,
      VectorNormalize: v => { const l = Math.hypot(v[0], v[1], v[2]) || 1; return V(v[0] / l, v[1] / l, v[2] / l); },
      VectorDot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
    },
  });
}
// a deterministic RNG (mulberry32)
function rng(seed) {
  return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let x = Math.imul(seed ^ seed >>> 15, 1 | seed); x = x + Math.imul(x ^ x >>> 7, 61 | x) ^ x; return ((x ^ x >>> 14) >>> 0) / 4294967296; };
}
const A = LAYOUT.ARENA;
function directorSuite(text, label, scale = 1) {
  const N = n => Math.max(50, Math.round(n * scale));
  const out = [];
  const t = (ok, msg) => { if (!ok) out.push(`${label}: ${msg}`); };
  let g;
  try { g = loadArena(text); } catch (e) { return [`${label}: the arena script does not load in gsc_eval (${e.message})`]; }
  const D = defs(text);
  const MIN = +D.TOD_ARENA_SPAWN_MIN, JIT = +D.TOD_ARENA_SPAWN_JITTER;
  let spots, kinds, gates;
  try {
    spots = g.call('tod_arena_data::arena_spawns', []);
    kinds = g.call('tod_arena_data::arena_spawn_kinds', []);
    gates = g.call('tod_arena_data::arena_gates', []);
  } catch (e) { return [`${label}: the generated arena data does not load (${e.message})`]; }
  const R = rng(1903);
  const levels = [A.z, A.z + LAYOUT.RING_Z, A.z + LAYOUT.DAIS_Z];
  const randomPlayer = () => {
    const z = levels[Math.floor(R() * 3)];
    const span = z === A.z + LAYOUT.DAIS_Z ? LAYOUT.DH : A.half - 40;
    const org = V(A.cx + (R() * 2 - 1) * span, A.cy + (R() * 2 - 1) * span, z);
    const yaw = R() * 360;
    return { org, eye: V(org[0], org[1], org[2] + 60), fwd: V(Math.cos(yaw * Math.PI / 180), Math.sin(yaw * Math.PI / 180), 0) };
  };
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  const pick = (party, live = [], camper, last = -1) => g.call('best_spot', [spots, kinds, party.map(p => p.org), party.map(p => p.eye), party.map(p => p.fwd), live, camper, last, spots.map(() => R() * JIT)]);
  // (a) MIN distance, thousands of random parties
  let legalCases = 0, bad = 0, fallbackBad = 0;
  for (let n = 0; n < N(1500); n++) {
    const party = Array.from({ length: 1 + Math.floor(R() * 4) }, randomPlayer);
    const i = pick(party);
    const dmin = s => Math.min(...party.map(p => dist(s, p.org)));
    const anyLegal = spots.some(s => dmin(s) >= MIN);
    if (anyLegal) { legalCases++; if (dmin(spots[i]) < MIN) bad++; }
    else if (dmin(spots[i]) < Math.max(...spots.map(dmin)) - 1e-6) fallbackBad++;
  }
  t(legalCases > N(1500) * 0.8, `most random parties leave a legal spawn point (${legalCases}/${N(1500)})`);
  t(bad === 0, `never a spawn within ${MIN} of a player while a legal point exists (${bad} violations)`);
  t(fallbackBad === 0, `with no legal point, the farthest point is used (${fallbackBad} violations)`);
  // (b) behind beats in front: a lone player in the pit centre, facing +y
  {
    const p = { org: V(A.cx, A.cy + 40, A.z), eye: V(A.cx, A.cy + 40, A.z + 60), fwd: V(0, 1, 0) };
    let ahead = 0, behind = 0;
    for (let n = 0; n < N(800); n++) {
      const s = spots[pick([p])];
      if (s[1] > p.org[1] + 100) ahead++; else if (s[1] < p.org[1] - 100) behind++;
    }
    t(behind > ahead * 1.5, `the party's back is favoured: behind ${behind} vs ahead ${ahead}`);
  }
  // (c) a camper pulls the spawns: a player on the NE ring corner, the party elsewhere
  {
    const camper = { org: V(A.cx + 736, A.cy + 736, A.z + LAYOUT.RING_Z), eye: V(A.cx + 736, A.cy + 736, A.z + LAYOUT.RING_Z + 60), fwd: V(-0.707, -0.707, 0) };
    const mate = { org: V(A.cx - 600, A.cy - 600, A.z), eye: V(A.cx - 600, A.cy - 600, A.z + 60), fwd: V(1, 0, 0) };
    let free = 0, pulled = 0;
    for (let n = 0; n < N(600); n++) {
      free += dist(spots[pick([camper, mate])], camper.org);
      pulled += dist(spots[pick([camper, mate], [], camper.org)], camper.org);
    }
    t(pulled < free * 0.8, `a camper draws the spawns: mean distance ${Math.round(pulled / N(600))} vs ${Math.round(free / N(600))} without`);
    // and the elite gate: the camper's nearest legal gate; without a camper the farthest legal gate
    const gi = g.call('elite_gate', [gates, [camper.org, mate.org], camper.org, []]);
    const legal = gates.map((s, i) => [i, Math.min(dist(s, camper.org), dist(s, mate.org))]).filter(([, d]) => d >= MIN);
    const nearestLegal = legal.sort((a, b) => dist(gates[a[0]], camper.org) - dist(gates[b[0]], camper.org))[0][0];
    t(gi === nearestLegal, `a camper's elite comes through the legal gate nearest them (got ${gi}, want ${nearestLegal})`);
    const gf = g.call('elite_gate', [gates, [camper.org, mate.org], undefined, []]);
    const farLegal = legal.sort((a, b) => b[1] - a[1])[0][0];
    t(gf === farLegal, `with no camper the elite takes the farthest legal gate (got ${gf}, want ${farLegal})`);
    const gm = g.call('elite_gate', [gates, [camper.org, mate.org], undefined, [farLegal]]);
    t(gm !== farLegal, 'a recently used gate is skipped while another is legal');
  }
  // (d) zombies already up push the spawns away
  {
    const p = { org: V(A.cx, A.cy, A.z + LAYOUT.DAIS_Z), eye: V(A.cx, A.cy, A.z + LAYOUT.DAIS_Z + 60), fwd: V(0, 1, 0) };
    const crowdAt = V(A.cx - 736, A.cy + 224, A.z + LAYOUT.RING_Z);
    const crowd = Array.from({ length: 8 }, () => crowdAt);
    let nearCrowd = 0, nearCrowdFree = 0;
    for (let n = 0; n < N(600); n++) {
      if (dist(spots[pick([p], crowd)], crowdAt) < 400) nearCrowd++;
      if (dist(spots[pick([p])], crowdAt) < 400) nearCrowdFree++;
    }
    t(nearCrowd < nearCrowdFree * 0.5, `a crowd pushes spawns elsewhere: ${nearCrowd} picks near it vs ${nearCrowdFree} with none`);
  }
  // (e) the last point is not repeated while another is legal
  {
    const p = randomPlayer();
    let rep = 0, last = -1;
    for (let n = 0; n < N(300); n++) { const i = pick([p], [], undefined, last); if (i === last) rep++; last = i; }
    t(rep < N(300) * 0.05, `the last-used point is rarely reused (${rep}/${N(300)})`);
  }
  // (a2) the MIN rule itself, at its edge: 10 inside is refused, 10 outside is scored
  {
    const s = spots[0], o = V(s[0] + MIN - 10, s[1], s[2]), o2 = V(s[0] + MIN + 10, s[1], s[2]);
    t(g.call('spot_score', [s, kinds[0], [o], [], [], [], undefined, false, 0]) === -1000000, `a point ${MIN - 10} from a player is refused`);
    t(g.call('spot_score', [s, kinds[0], [o2], [], [], [], undefined, false, 0]) > -1000, `a point ${MIN + 10} from a player is scored`);
  }
  // (f) the camp clock
  t(g.call('camp_step', [3000, 50, 0, 500]) === 3500, 'camp_step: standing still runs the clock');
  t(g.call('camp_step', [3000, +D.TOD_ARENA_CAMP_R + 1, 0, 500]) === 0, 'camp_step: leaving the circle resets it');
  t(g.call('camp_step', [3000, 10, 96, 500]) === 0, 'camp_step: changing level resets it');
  // (g) the waves: harder, monotonic, quiet first waves only at the start
  const set = (zf, elites) => ({ zf, elites });
  const z1 = g.call('zombie_count_for', [set(1.0, 'mangler'), 1, 1]), z10 = g.call('zombie_count_for', [set(1.0, 'mangler'), 10, 1]);
  t(z1 >= 12, `level 1 solo: ${z1} zombies a wave (v1: 6)`);
  t(z10 > z1 * 2.5, `level 10 solo: ${z10} zombies a wave`);
  let mono = true;
  for (let lvl = 2; lvl <= 10; lvl++) if (g.call('zombie_count_for', [set(1.0, 'doppel'), lvl, 2]) < g.call('zombie_count_for', [set(1.0, 'doppel'), lvl - 1, 2])) mono = false;
  t(mono, 'zombies per wave never fall with the level');
  t(g.call('elite_count', [set(1.0, 'mangler'), 'mangler', 1, 1]) === 0, 'level 1 wave 1 is the horde alone');
  t(g.call('elite_count', [set(1.0, 'mangler'), 'mangler', 3, 1]) >= 1, 'from level 3 the first wave has an elite');
  t(g.call('elite_count', [set(1.0, 'mangler'), 'mangler', 10, 2]) >= 4, 'level 10 brings four of the set\'s elites a wave');
  t(g.call('elite_count', [set(1.6, 'none'), 'mangler', 10, 2]) === 0, 'the horde set stays elite-free');
  // (h) the fall guard
  const inA = V(A.cx + 100, A.cy, A.z + 120), outA = V(0, 0, 0);
  t(g.call('fall_guard_verdict', ['MOD_FALLING', inA, true]) === true, 'fall guard: a fall in the arena during a fight is cancelled');
  t(!g.call('fall_guard_verdict', ['MOD_FALLING', inA, false]), 'fall guard: not outside a fight');
  t(!g.call('fall_guard_verdict', ['MOD_FALLING', outA, true]), 'fall guard: not in the tower');
  t(!g.call('fall_guard_verdict', ['MOD_MELEE', inA, true]), 'fall guard: never another kind of damage');
  return out;
}
for (const f of directorSuite(ARENA, 'shipping')) check(false, f);

// ---------------------------------------------------------------------------
// 3. THE GENERATED ROOM
// ---------------------------------------------------------------------------
{
  const g = loadArena(ARENA);
  const spots = g.call('tod_arena_data::arena_spawns', []), kinds = g.call('tod_arena_data::arena_spawn_kinds', []);
  const gates = g.call('tod_arena_data::arena_gates', []), arrivals = g.call('tod_arena_data::arena_arrivals', []);
  const dais = g.call('tod_arena_data::arena_dais', []);
  check(spots.length === 26 && kinds.length === spots.length, `26 spawn points with a kind each (${spots.length}/${kinds.length})`);
  const count = k => kinds.filter(x => x === k).length;
  check(count('gate') === 8 && count('ring') === 8 && count('pit') === 4 && count('landing') === 4 && count('undercroft') === 2, 'the spawn kinds: 8 gate, 4 pit, 2 undercroft, 8 ring, 4 landing');
  check(gates.length === 8 && gates.every(s => spots.some(p => p[0] === s[0] && p[1] === s[1] && p[2] === s[2])), 'the 8 gates are spawn points too');
  check(arrivals.length === 4 && arrivals.every(a => a[2] === dais[2] && g.call('tod_arena_data::on_dais', [a])), 'the 4 arrivals stand on the dais');
  check(spots.every(s => g.call('tod_arena_data::in_arena', [s])) && !g.call('tod_arena_data::in_arena', [V(0, 0, 0)]), 'every spawn point is in the arena; the tower is not');
  check(!g.call('tod_arena_data::on_dais', [V(A.cx, A.cy, A.z)]) && g.call('tod_arena_data::on_dais', [V(A.cx + 100, A.cy - 100, dais[2])]), 'on_dais: the dais yes, the undercroft below it no');
  // the levels the director spreads over: some on each
  check(spots.some(s => s[2] === A.z) && spots.some(s => s[2] === A.z + LAYOUT.RING_Z) && spots.some(s => s[2] > A.z + LAYOUT.RING_Z), 'spawn points on the pit, the ring and the spoke landings');
  // the THE PURSUIT / AMBUSH contract: in_arena keeps its form (test_pursuit.js reads its floor bound)
  check(/org\[ 2 \] >= -?\d+/.test(DATA) && /function in_arena\( org \)/.test(DATA), 'in_arena( org ) keeps the form other gates parse');
  // the script reads what the generator writes
  for (const fn of ['arena_spawns', 'arena_spawn_kinds', 'arena_gates', 'arena_arrivals', 'arena_dais', 'arena_top', 'on_dais', 'in_arena'])
    check(new RegExp(`tod_arena_data::${fn}\\(`).test(ARENA), `_tod_arena.gsc reads tod_arena_data::${fn}`);
  check(/ArrayInsert\(\s*level\.player_damage_callbacks,\s*&arena_fall_guard/.test(ARENA), 'the fall guard is installed');
  check(/level thread dais_purge\(/.test(ARENA) && /level thread camp_watch\(/.test(ARENA), 'the overcharge and the camp clock run with the fight');
  check(/tod_zspeed_round_add\s*=\s*arena_speed_add\(\)/.test(ARENA), 'arena zombies get the sprint offset');
}

// ---------------------------------------------------------------------------
// 3b. THE ROOM'S AIR REACHES THE VOID (a sealed room renders invisible)
// ---------------------------------------------------------------------------
let deadAir = 0;
{
  const cb = require('./convex_brush.js');
  const MAP = read('map_source/zm/zm_tod2_cybercity.map');
  const VX = 4;                                       // Umbra's small_hole (UmbraConvert prints it)
  const solids = [];
  for (const m of MAP.matchAll(/\/\/ brush \d+ — (battle arena[^\n]*)\n\{([\s\S]*?)\n\}/g)) {
    const planes = cb.readPlanes(m[2]);
    if (planes.length < 4 || planes.every(p => /clip/i.test(p.mat))) continue;   // clip draws nothing, occludes nothing
    const h = cb.hull(planes);
    solids.push({ planes, lo: h.lo, hi: h.hi });
  }
  check(solids.length > 200, `the arena's visible brushes are in the generated .map (${solids.length})`);
  const lo = [0, 1, 2].map(i => Math.floor((Math.min(...solids.map(b => b.lo[i])) - 2 * VX) / VX) * VX);
  const hi = [0, 1, 2].map(i => Math.ceil((Math.max(...solids.map(b => b.hi[i])) + 2 * VX) / VX) * VX);
  const [NX, NY, NZ] = [0, 1, 2].map(i => (hi[i] - lo[i]) / VX);
  const at = (x, y, z) => (z * NY + y) * NX + x;
  const base = new Uint8Array(NX * NY * NZ);          // 1 = a voxel that touches a visible brush
  for (const b of solids) {
    // touches: for every plane, the voxel's nearest corner is inside (n.c - r < d)
    const P = b.planes.map(p => [p.n[0], p.n[1], p.n[2], p.d - 0.01 + VX / 2 * (Math.abs(p.n[0]) + Math.abs(p.n[1]) + Math.abs(p.n[2]))]);
    const i0 = [0, 1, 2].map(i => Math.max(0, Math.floor((b.lo[i] - lo[i]) / VX) - 1));
    const i1 = [0, 1, 2].map(i => Math.min([NX, NY, NZ][i] - 1, Math.ceil((b.hi[i] - lo[i]) / VX)));
    for (let z = i0[2]; z <= i1[2]; z++) {
      const cz = lo[2] + (z + 0.5) * VX;
      for (let y = i0[1]; y <= i1[1]; y++) {
        const cy = lo[1] + (y + 0.5) * VX;
        for (let x = i0[0]; x <= i1[0]; x++) {
          const cx = lo[0] + (x + 0.5) * VX;
          let k = 0;
          while (k < P.length && P[k][0] * cx + P[k][1] * cy + P[k][2] * cz < P[k][3]) k++;
          if (k === P.length) base[at(x, y, z)] = 1;
        }
      }
    }
  }
  const Q = new Int32Array(1 << 24);
  function voidAir(solid) {                           // 2 = air connected to the domain's edge (the void)
    const lab = Uint8Array.from(solid);
    let head = 0, tail = 0;
    const push = k => {
      if (lab[k]) return;
      lab[k] = 2; Q[tail] = k; tail = (tail + 1) & (Q.length - 1);
      if (tail === head) throw new Error('air flood: queue overflow');
    };
    for (let z = 0; z < NZ; z++) for (let y = 0; y < NY; y++) for (let x = 0; x < NX; x++)
      if (!x || !y || !z || x === NX - 1 || y === NY - 1 || z === NZ - 1) push(at(x, y, z));
    while (head !== tail) {
      const k = Q[head]; head = (head + 1) & (Q.length - 1);
      const x = k % NX, y = Math.floor(k / NX) % NY, z = Math.floor(k / (NX * NY));
      if (x > 0) push(k - 1);
      if (x < NX - 1) push(k + 1);
      if (y > 0) push(k - NX);
      if (y < NY - 1) push(k + NX);
      if (z > 0) push(k - NX * NY);
      if (z < NZ - 1) push(k + NX * NY);
    }
    return lab;
  }
  // every place a body stands, 40 up (inside the body)
  const probes = [
    ...LAYOUT.RISERS.map(p => ['spawn', p]),
    ...LAYOUT.ARRIVALS.map(p => ['arrival', p]),
    ...LAYOUT.NAV_PROBES.map(p => ['walk probe', p]),
  ];
  const cell = p => at(...[0, 1, 2].map(i => Math.floor((p[i] + (i === 2 ? 40 : 0) - lo[i]) / VX)));
  const open = voidAir(base);
  const sealed = probes.filter(([, p]) => open[cell(p)] !== 2);
  check(sealed.length === 0, `the room's air reaches the void at all ${probes.length} spawn / arrival / walk points (a sealed room renders invisible)`
    + sealed.slice(0, 4).map(([k, p]) => `; ${k} ${p.map(Math.round)} ${open[cell(p)] === 1 ? 'inside a solid' : 'SEALED'}`).join(''));
  for (let k = 0; k < open.length; k++) if (!open[k]) deadAir++;
  // NEGATIVE CONTROL: lid the roof slot (the wall tops up to the ceiling, out to the
  // skirts) and the same flood must find every one of those points sealed.
  const lid = Uint8Array.from(base);
  const O = LAYOUT.OUTER, z0 = Math.floor((A.z + A.height - lo[2]) / VX), z1 = Math.ceil((A.z + A.height + LAYOUT.VENT.gap - lo[2]) / VX);
  const x0 = Math.floor((A.cx - O - lo[0]) / VX), x1 = Math.ceil((A.cx + O - lo[0]) / VX);
  const y0 = Math.floor((A.cy - O - lo[1]) / VX), y1 = Math.ceil((A.cy + O - lo[1]) / VX);
  for (let z = z0; z < z1; z++) for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) lid[at(x, y, z)] = 1;
  const shut = voidAir(lid);
  check(probes.every(([, p]) => shut[cell(p)] !== 2), 'negative control: the roof slot lidded, the same flood finds the room sealed (the check can fail, and the slot is the room\'s one vent)');
}

// ---------------------------------------------------------------------------
// 4b. THE READABLE FIGHT (v2.1)
// ---------------------------------------------------------------------------
const WIDGET = read('ui/uieditor/widgets/HUD/AetheriumWidgets/TodArena.lua');
function readableSuite(text, label) {
  const out = [];
  const t = (ok, msg) => { if (!ok) out.push(`${label}: ${msg}`); };
  const D = defs(text);
  // the event and its shape
  t(/#precache\(\s*"eventstring",\s*"tod_arena"\s*\);/.test(text), 'the tod_arena eventstring is precached');
  t(/LuiNotifyEvent\(\s*&"tod_arena",\s*7,\s*show,\s*h\.lvl,\s*TOD_ARENA_LEVELS,\s*h\.wave,\s*TOD_ARENA_WAVES,\s*left,\s*flags\s*\)/.test(text), 'hud_push sends ( show, level, levels, wave, waves, left, flags ): the seven-value shape stock evidences');
  t(/d\[ 7 \]/.test(WIDGET) && !/d\[ 8 \]/.test(WIDGET), 'the widget reads exactly seven arguments');
  // LOCKSTEP: the flag bits and the hot threshold
  const lua = Object.fromEntries([...WIDGET.matchAll(/^local (FLAG_\w+|HOT) = (\d+)/gm)].map(m => [m[1], +m[2]]));
  // W2E (2026-10-05): five bits - 4 (_BOSS, THE KEEPER) retired with him on BOTH sides and stays unused.
  t(lua.FLAG_WAVE === +D.TOD_ARENA_HUD_WAVE && lua.FLAG_CLEARED === +D.TOD_ARENA_HUD_CLEARED && lua.FLAG_LEVEL === +D.TOD_ARENA_HUD_LEVEL
    && lua.FLAG_HOUSE === +D.TOD_ARENA_HUD_HOUSE && lua.FLAG_DEALER === +D.TOD_ARENA_HUD_DEALER && lua.FLAG_BOSS === undefined && D.TOD_ARENA_HUD_BOSS === undefined,
    `LOCKSTEP flag bits GSC ${D.TOD_ARENA_HUD_WAVE}/${D.TOD_ARENA_HUD_CLEARED}/${D.TOD_ARENA_HUD_LEVEL}/${D.TOD_ARENA_HUD_HOUSE}/${D.TOD_ARENA_HUD_DEALER} vs Lua ${lua.FLAG_WAVE}/${lua.FLAG_CLEARED}/${lua.FLAG_LEVEL}/${lua.FLAG_HOUSE}/${lua.FLAG_DEALER} (the retired _BOSS: GSC ${D.TOD_ARENA_HUD_BOSS}, Lua ${lua.FLAG_BOSS})`);
  t(lua.HOT === +D.TOD_ARENA_HUD_HOT, `LOCKSTEP hot threshold GSC ${D.TOD_ARENA_HUD_HOT} vs Lua ${lua.HOT}`);
  { const bits = [+D.TOD_ARENA_HUD_WAVE, +D.TOD_ARENA_HUD_CLEARED, +D.TOD_ARENA_HUD_LEVEL, +D.TOD_ARENA_HUD_HOUSE, +D.TOD_ARENA_HUD_DEALER];
    t(new Set(bits).size === 5 && [1, 2, 8, 16, 32].every(b => bits.includes(b)), 'the five flag bits are distinct powers of two, 4 left unused (the sum is the only packing the interpreter has)'); }
  t(!/flags\s*=\s*flags\s*\+\s*TOD_ARENA_HUD_DEALER[\s\S]*flags\s*\|\s*/.test(text), 'the dealer bit is added once in hud_push (no bitwise ops: the interpreter has none)');
  t(!/TOD_ARENA_HUD_BOSS\s*\)?\s*;/.test(text.replace(/\/\/[^\n]*/g, '')) && !/^#define TOD_ARENA_HUD_BOSS/m.test(text), 'the Keeper\'s readout bit retired with him (W2E)');
  // the pure functions as shipped
  let g = null;
  try { g = loadArena(text); } catch (e) { t(false, `the arena script does not load in gsc_eval (${e.message})`); }
  if (g) {
    const L = (a, b, c) => g.call('hud_left', [a, b, c]);
    t(L(12, 0, 0) === 12 && L(12, 5, 5) === 12 && L(12, 12, 7) === 7 && L(12, 12, 0) === 0, 'hud_left: not risen + still up');
    t(L(12, 12, 3) === 3 && L(5, 9, 4) === 4, 'hud_left never reads under the ones still up (the Keeper\'s open-ended escorts)');
    t(L(0, 0, 0) === 0 && L(3, 5, 0) === 0, 'hud_left never negative');
    const M = l => g.call('mood_index', [l]);
    const idx = [];
    for (let l = 1; l <= +D.TOD_ARENA_LEVELS; l++) idx.push(M(l));
    t(idx.every(i => i >= 1 && i <= 12), `mood_index stays inside the glow lane (1..12): ${idx.join(',')}`);
    t(idx[0] === 10 && idx[idx.length - 1] === 1, `mood_index: level 1 teal (10), level ${D.TOD_ARENA_LEVELS} red (1); got ${idx[0]} / ${idx[idx.length - 1]}`);
    const order = [10, 3, 4, 1];   // teal -> yellow -> orange -> red
    let ok = true, last = -1;
    for (const i of idx) { const k = order.indexOf(i); if (k < 0 || k < last) ok = false; last = k; }
    t(ok && new Set(idx).size >= 3, `mood_index deepens with the level and never steps back: ${idx.join(',')}`);
    const moods = g.call('tod_arena_data::arena_mood_orgs', []), dais = g.call('tod_arena_data::arena_dais', []);
    t(moods.length === 5, `five mood hosts (${moods.length})`);
    t(moods.every(o => g.call('tod_arena_data::in_arena', [o])), 'every mood host is inside the room');
    t(moods.length > 0 && moods[moods.length - 1][0] === dais[0] && moods[moods.length - 1][1] === dais[1] && moods[moods.length - 1][2] > dais[2], 'the dais host is LAST, over the dais (mood_dais addresses the last)');
    const pyl = moods.slice(0, 4);
    t(pyl.every(o => o[2] > A.z + 196 && o[2] < A.z + LAYOUT.RING_Z + 200) && new Set(pyl.map(o => o[0] + ',' + o[1])).size === 4, 'the four pylon hosts sit over four different pylon collars');
  }
  // the gate tell: charge (threaded) + cue, the wait, the flash (threaded), then the rise
  const gate = body(text, 'gate_rise_think');
  t(!!gate, 'gate_rise_think exists');
  if (gate) {
    const iCharge = gate.search(/level thread tod_teleport::fx_burst\( "tod_tp_charge", org/), iSnd = gate.search(/play_sound_at_origin\( org, TOD_ARENA_SND_GATE/),
      iWait = gate.search(/\bwait TOD_ARENA_GATE_TELL_SECS;/), iFlash = gate.search(/level thread tod_teleport::fx_burst\( "tod_tp_flash", org/), iRise = gate.search(/\bspawn_elite\( kind, org/);
    t(iCharge >= 0 && iSnd > iCharge && iWait > iSnd && iFlash > iWait && iRise > iFlash, 'the gate charges and sounds, waits the tell, flashes, then the elite rises');
    t(/level\.tod_arena_hud\.pending--/.test(gate), 'a gate that has risen its elite is no longer pending');
  }
  const sw = body(text, 'spawn_wave');
  t(!!sw && /gate_rise\( "mangler"/.test(sw) && /gate_rise\( "doppel"/.test(sw) && !/\bspawn_elite\( "(mangler|doppel)"/.test(sw), 'the set\'s elites rise through gate_rise, never a bare spawn_elite');
  t(!!sw && /pending > 0/.test(sw) && /level\.tod_arena_hud\.risen\+\+/.test(sw), 'spawn_wave counts every rise and waits for the gates still charging');
  t(+D.TOD_ARENA_GATE_TELL_SECS >= 0.6 && +D.TOD_ARENA_GATE_TELL_SECS <= 2.0, `the gate tell is a readable beat (${D.TOD_ARENA_GATE_TELL_SECS}s)`);
  // the beats: horn at wave_begin, sting at a cleared wave (never the last), fanfare at the win
  const wb = body(text, 'wave_begin'), wc = body(text, 'wait_wave_clear'), win = body(text, 'arena_win'), run = body(text, 'arena_run');
  t(!!wb && /PlaySoundToPlayer\( TOD_ARENA_SND_WAVE, p \)/.test(wb) && /hud_push\( TOD_ARENA_HUD_WAVE \)/.test(wb), 'wave_begin: the horn to every player + the WAVE flag');
  t(!!wc && /if \( w < TOD_ARENA_WAVES \)[\s\S]*PlaySoundToPlayer\( TOD_ARENA_SND_CLEAR, p \)[\s\S]*hud_push\( TOD_ARENA_HUD_CLEARED \)/.test(wc), 'a cleared wave (not the last) stings and flags CLEARED');
  t(!!win && /PlaySoundToPlayer\( TOD_ARENA_SND_LEVEL, p \)/.test(win) && /hud_push\( TOD_ARENA_HUD_LEVEL \)/.test(win) && win.indexOf('hud_push( TOD_ARENA_HUD_LEVEL )') < win.indexOf('set_world_pause( true )'), 'the win: the fanfare + LEVEL CLEARED before the frozen card');
  t(!!win && win.indexOf('hud_hide()') > win.indexOf('arena_music_end') && /level thread mood_end\(\)/.test(win), 'the ride home hides the readout and ends the mood lights');
  t(!!run && run.indexOf('wave_begin( set, lvl, w )') > 0 && run.indexOf('wave_begin( set, lvl, w )') < run.indexOf('spawn_wave( set, lvl, w )') && run.indexOf('boss_wave') < 0, 'arena_run: wave_begin, then the wave (the Keeper\'s boss wave retired whole, W2E)');
  t(!!run && run.indexOf('level thread hud_watch()') > run.indexOf('SetPlayerAngles') && run.indexOf('hud_push( 0 )') < run.indexOf('wait TOD_ARENA_LAND_SECS') && run.indexOf('level thread mood_start( lvl )') < run.indexOf('wait TOD_ARENA_LAND_SECS'), 'the readout and the mood lights come up with the landing, before the breath');
  // W2E (2026-10-05): the Keeper and his wave retired whole; level 10 is the Dealer's House (the toggle went too).
  t(!/function boss_wave\(/.test(text) && !/function boss_escort\(/.test(text) && !/tod_keeper::/.test(text) && !/TOD_ARENA_(HOUSE|KEEPER_)/.test(text.replace(/\/\/[^\n]*/g, '')),
    'the Keeper\'s boss wave, his escort, his knobs and the TOD_ARENA_HOUSE toggle stay retired');
  // the overcharge's late warning
  const dp = body(text, 'dais_purge');
  t(!!dp && /for \( k = 0; k < int\( TOD_ARENA_PURGE_WARN \/ 0\.25 \); k\+\+ \)/.test(dp) && /PURGE_WARN_LATE/.test(dp) && !/\bwait TOD_ARENA_PURGE_WARN;/.test(dp), 'the wind-up polls the dais and warns whoever steps on');
  t(!!dp && dp.indexOf('mood_dais( TOD_ARENA_MOOD_WARN_IDX )') > 0 && dp.indexOf('mood_dais( TOD_ARENA_MOOD_WARN_IDX )') < dp.indexOf('mood_dais( level.tod_arena_mood_idx )'), 'the dais light goes white for the wind-up and back after');
  // the chamber notice: once per level, after a dwell, a free print
  const cn = body(text, 'chamber_notice_watch');
  t(!!cn && /p\.tod_arena_notice == level\.tod_arena_level/.test(cn) && /TOD_ARENA_NOTICE_MS/.test(cn) && /IPrintLnBold/.test(cn) && !/SetHintString/.test(cn), 'the chamber notice is once per level, after the dwell, on the free lane');
  return out;
}
for (const f of readableSuite(ARENA, 'shipping')) check(false, f);
{
  // the cues: four generated aliases in their rows, the zone config, the wavs on disk
  const csv = read('sound/aliases/tod_arena.csv').split('\n').filter(l => l.trim());
  const head = csv[0].split(','), col = Object.fromEntries(head.map((h, i) => [h, i]));
  const rows = Object.fromEntries(csv.slice(1).map(l => { const c = l.split(','); return [c[col.Name], c]; }));
  for (const [alias, pan] of [['tod_arena_wave', '2d'], ['tod_arena_clear', '2d'], ['tod_arena_level', '2d'], ['tod_arena_gate', '3d']]) {
    const r = rows[alias];
    check(!!r && r[col.PanType] === pan && r[col.Looping] === 'NONLOOPING' && r[col.Bus] === 'BUS_FX', `cue ${alias}: ${pan}, one-shot, BUS_FX`);
    check(!!r && fs.existsSync(path.join(ROOT, 'sound_assets', r[col.FileSpec].replace(/\\/g, '/'))), `cue ${alias}: its wav exists`);
    check(new RegExp(`"${alias}"`).test(ARENA), `cue ${alias}: the script names it`);
  }
  const szc = JSON.parse(read('sound/zoneconfig/zm_tod2_cybercity.szc'));
  check((szc.Sources || []).some(s => s.Type === 'ALIAS' && s.Filename === 'tod_arena.csv'), 'the zone config loads tod_arena.csv');
  // the widget: attached to the HUD, veiled with it, zoned, lifetime-tested
  const hud = read('ui/uieditor/menus/hud/AetheriumHud.lua');
  check(/pcall\( require, "ui\.uieditor\.widgets\.HUD\.AetheriumWidgets\.TodArena" \)/.test(hud) && /self\.TodArena = CoD\.TodArena\.new\( self, controller \)/.test(hud), 'AetheriumHud attaches TodArena');
  check(/self\.AetheriumRoundCounter, self\.TodHaven, self\.TodArena \}/.test(hud), 'TodArena is in the HUD veil list (hidden with the rest)');
  check(/^rawfile,ui\/uieditor\/widgets\/HUD\/AetheriumWidgets\/TodArena\.lua/m.test(read('zone_source/zm_tod2_cybercity.zone')), 'TodArena.lua is zoned');
  check(/'TodHaven','TodArena'/.test(read('tools/test_ui_lifetimes.lua')), 'TodArena is in the UI lifetimes harness');
  check(/test_arena_hud\.lua/.test(read('tools/build_map.ps1')) && /battle_arena\/make_sounds\.py"\) --check/.test(read('tools/build_map.ps1')), 'the build runs the HUD harness and the cue check');
  // v2.2 (user: "replace the round HUD with Battle Arena / Level 1 ... rounds dont count in there"): the
  // HUD V2 round badge reads the same event and wears the GENERATED arena twin + the level for the fight
  const plate = read('ui/uieditor/menus/hud/tod_upgrade.lua'), gdt = read('source_data/tod_ui_images.gdt'), zone = read('zone_source/zm_tod2_cybercity.zone');
  for (const img of ['i_tod_h2_arena_badge', 'i_tod_h2_arena_badge_rampage']) {
    check(new RegExp(`RegisterImage\\( "${img}" \\)`).test(plate), `the status plate registers ${img}`);
    check(new RegExp(`^image,${img}\\r?$`, 'm').test(zone), `${img} is zoned`);
    check(new RegExp(`"${img}" \\( "image\\.gdf" \\)`).test(gdt) && gdt.includes(`"baseImage" "source_data/tod_ui_images/_images/${img}.png"`), `${img} has its GDT block`);
    check(fs.existsSync(path.join(ROOT, 'source_data', 'tod_ui_images', '_images', img + '.png')), `${img}.png exists (generated by tools/battle_arena/make_badge.py)`);
  }
  check(/subscribeToGlobalModel\( Instance, "PerController", "scriptNotify", function \( model \)\s*if Engine\.GetModelValue\( model \) ~= "tod_arena" then return end/.test(plate), 'the status plate listens to tod_arena');
  check(/if lvl == arenaLvl then return end/.test(plate) && /if arenaLvl > 0 then return luckRampageOn and ARENA_RMP_IMG or ARENA_IMG end/.test(plate), 'the badge is change-gated and dresses for the arena in both rampage states');
  const capM = plate.match(/local TOD_ARENA_NUM_CAP, TOD_ARENA_NUM_BASE = ([\d.]+), ([\d.]+)/);
  check(!!capM && +capM[1] < 17 && +capM[2] - +capM[1] >= 10 + 71 * 0.375 + 1, 'the level number sits under the baked LEVEL caption (LOCKSTEP make_badge.py WINDOW_TEXT baseline 71)');
  check(/local function badgeImage\(\)/.test(plate) && /Badge2:setImage\( badgeImage\(\) \)/.test(plate) && !/Badge2:setImage\( luckRampageOn and BADGE_RMP_IMG or BADGE_IMG \)/.test(plate), 'one chooser owns the badge art');
  check(!/BATTLE ARENA - LEVEL/.test(WIDGET) && (WIDGET.match(/CoD\.TodGlyphText\.new\( \{/g) || []).length === 2, 'TodArena carries the wave and the count only: the level is the badge\'s');
  check(/battle_arena\/make_badge\.py"\) --check/.test(read('tools/build_map.ps1')) && /test_arena_badge\.lua/.test(read('tools/build_map.ps1')), 'the build runs the badge generator check and the badge harness');
}

// ---------------------------------------------------------------------------
// 4. MUTANTS — each must be caught (a gate that cannot fail is not a gate).
// ---------------------------------------------------------------------------
const MUTANTS = [
  ['v2.1 the gate charge inline (the tell would delay the whole wave)', s => s.replace('level thread tod_teleport::fx_burst( "tod_tp_charge", org + ( 0, 0, 40 ), TOD_ARENA_GATE_TELL_SECS', 'tod_teleport::fx_burst( "tod_tp_charge", org + ( 0, 0, 40 ), TOD_ARENA_GATE_TELL_SECS')],
  ['v2.1 the elite rises before its gate flashes', s => s.replace('\tlevel thread tod_teleport::fx_burst( "tod_tp_flash", org + ( 0, 0, 4 ), 2.0 );\n\tspawn_elite( kind, org, mult, lvl, w );', '\tspawn_elite( kind, org, mult, lvl, w );\n\tlevel thread tod_teleport::fx_burst( "tod_tp_flash", org + ( 0, 0, 4 ), 2.0 );')],
  ['v2.1 hud_left reads under the ones still up', s => s.replace('\tif ( left < alive )\n\t\tleft = alive;', '\tif ( left < 0 )\n\t\tleft = alive;')],
  ['v2.1 the mood never deepens', s => s.replace('\tif ( lvl >= 9 )\n\t\treturn 1;', '\tif ( lvl >= 9 )\n\t\treturn 10;')],
  ['v2.1 a bare spawn_elite for the set\'s elites', s => s.replace('gate_rise( "mangler", mult, lvl, w );', 'spawn_elite( "mangler", elite_spot(), mult, lvl, w );')],
  ['v2.1 the wind-up no longer warns late steppers', s => s.replace('for ( k = 0; k < int( TOD_ARENA_PURGE_WARN / 0.25 ); k++ )', 'for ( k = 0; k < 0; k++ )')],
  ['v2.1 the last wave stings like the others', s => s.replace('\tif ( w < TOD_ARENA_WAVES )\n\t{\n\t\t// v2.1', '\tif ( true )\n\t{\n\t\t// v2.1')],
  ['the charge effect inline again', s => s.replace('level thread tod_teleport::fx_burst( "tod_tp_charge", org', 'tod_teleport::fx_burst( "tod_tp_charge", org')],
  ['the arrival flash inline again', s => s.replace('level thread tod_teleport::fx_burst( "tod_tp_kino", dais', 'tod_teleport::fx_burst( "tod_tp_kino", dais')],
  ['the v1 3-second charge', s => s.replace(/#define TOD_ARENA_CHARGE_SECS\s+0\.8/, '#define TOD_ARENA_CHARGE_SECS   3.0')],
  ['a wait between the charge and the jump', s => s.replace('\theld = hold_tower();', '\twait 0.5;\n\theld = hold_tower();')],
  ['the sound after the charge wait', s => s.replace(/(\ttod_perk_scatter::play_sound_at_origin\( org, "tod_teleport_fire", 4 \);\n)([\s\S]*?)(\twait TOD_ARENA_CHARGE_SECS;\n)/, '$2$3$1')],
  ['the return charge inline', s => s.replace('level thread tod_teleport::fx_burst( "tod_tp_charge", dais + ( 0, 0, 40 ), TOD_ARENA_RETURN_SECS', 'tod_teleport::fx_burst( "tod_tp_charge", dais + ( 0, 0, 40 ), TOD_ARENA_RETURN_SECS')],
  ['the minimum distance dropped', s => s.replace('if ( dmin < TOD_ARENA_SPAWN_MIN )\n\t\treturn -1000000;', 'if ( dmin < 0 )\n\t\treturn -1000000;')],
  ['the camper pull reversed', s => s.replace('score = score + TOD_ARENA_CAMP_PULL * ( 1 - dc / TOD_ARENA_CAMP_REACH );', 'score = score - TOD_ARENA_CAMP_PULL * ( 1 - dc / TOD_ARENA_CAMP_REACH );')],
  ['the unseen bonus reversed', s => s.replace('< TOD_ARENA_SPAWN_SEEN_DOT )\n\t\t\tunseen++;', '> TOD_ARENA_SPAWN_SEEN_DOT )\n\t\t\tunseen++;')],
  ['no spread cost', s => s.replace('score = score - TOD_ARENA_SPREAD_COST * near;', 'score = score;')],
  ['the gate ignores the camper', s => s.replace('v = 100000 - Distance( gates[ i ], camper );', 'v = dmin;')],
  ['the fall guard on every damage', s => s.replace('mod == "MOD_FALLING" && ', '')],
  ['the old wave sizes', s => s.replace(/#define TOD_ARENA_ZOMBIES_BASE\s+12/, '#define TOD_ARENA_ZOMBIES_BASE  6')],
];
for (const [name, mutate] of MUTANTS) {
  const m = mutate(ARENA);
  if (m === ARENA) { check(false, `mutant "${name}" did not apply (the shipping text moved: update the mutant)`); continue; }
  const caught = jumpSuite(m, 'm').length + directorSuite(m, 'm', 0.25).length + readableSuite(m, 'm').length
    + (+defs(m).TOD_ARENA_CHARGE_SECS !== +TD.TOD_TP_CHARGE_SEC ? 1 : 0);
  check(caught > 0, `mutant "${name}" is caught`);
}

console.log(fails
  ? `\nBATTLE ARENA GATE FAILED: ${fails}/${checks} checks`
  : `BATTLE ARENA OK: ${checks} checks (the jump lines up at ${AD.TOD_ARENA_CHARGE_SECS}s, v1 timed at 6.6s; director, waves, fall guard, room; the room's air reaches the void, ${Math.round(deadAir * 64 / 1000)}k u^3 of sealed dead air; the readout, the gate tell, the cues and the mood lights; ${MUTANTS.length} mutants caught)`);
process.exit(fails ? 1 : 0);
