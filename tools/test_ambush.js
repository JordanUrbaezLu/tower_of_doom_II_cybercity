'use strict';
// tools/test_ambush.js — THE AMBUSH + THE TRICKLE's build gate (docs/204, 2026-10-03).
//
// Runs the SHIPPING GSC through tools/sky_ships/gsc_eval.js:
//   * _tod_ambush.gsc — the share, the direction roll, the bucket rule, the try order, the
//     legality filter (with _tod_reach's walk model on the REAL generated drops / crown /
//     arena data), the focus pick and the whole pick end to end (ring -> classify -> zone ->
//     CanPath -> the spot stock's climb-out reads), plus its dev log;
//   * _tod_endless_rounds.gsc — the spawn hook (finale_spawn_selection) and the trickle
//     (tod_spawn_delay) against map 1's numbers: more zombies a second, the round length held.
// Then LOCKSTEP with THE HUNT (_tod_stray) and the generator, the WIRING, and NEGATIVE
// CONTROLS: mutants of the shipping code, each re-running the sections that must catch it.
// Usage: node tools/test_ambush.js [--why] [--time]
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8').replace(/\r\n/g, '\n');
const { gscLoad, V } = require('./sky_ships/gsc_eval.js');

const S = 'scripts/zm/zm_tod2_cybercity/';
const AMBUSH = read(S + '_tod_ambush.gsc');
const ENDLESS = read(S + '_tod_endless_rounds.gsc');
const REACH = read(S + '_tod_reach.gsc');
const STRAY = read(S + '_tod_stray.gsc');
const DOORS = read(S + '_tod_door_data.gsc');
const CROWN = read(S + '_tod_crown_data.gsc');
const ARENA = read(S + '_tod_arena_data.gsc');
const HOUSE = read(S + '_tod_house_data.gsc');   // docs/207: legal() reads it beside the arena's
const ZONE = read('zone_source/zm_tod2_cybercity.zone');
const BUILD = read('tools/build_map.ps1');
const GEN = read('tools/gen_tower_map.js');
const LAYOUT = require('./broken_tower_layout.js');
const WHY = process.argv.includes('--why');

let fails = 0, checks = 0;
function check(ok, label) { checks++; if (!ok) { fails++; console.log('FAIL ' + label); } }
const MEASURED = {};                       // the base run's numbers, printed with the verdict
const defs = text => Object.fromEntries([...text.matchAll(/^#define\s+(\w+)\s+(-?[\d.]+)/gm)].map(m => [m[1], m[2]]));
const AD = defs(AMBUSH), ED = defs(ENDLESS), RD = defs(REACH), SD = defs(STRAY);
const A = k => +AD[k];
const D2R = Math.PI / 180;

// MAP 1's trickle, the reference this map must beat (Tower of Doom 1's _tod_endless_rounds.gsc,
// read 2026-10-03: stock x 0.83 floored 0.25, stock round size 24 + 6 a player). Pinned here on
// purpose: the user's ask is "more hectic than the first", so the first is the yardstick.
const MAP1 = { mult: 0.83, floor: 0.25, maxAi: 24, perPlayer: 6 };

// ---------------------------------------------------------------------------
// The generated drop table (as test_pursuit.js reads it) and the lap height.
// ---------------------------------------------------------------------------
const drops = new Map();
for (const lap of LAYOUT.DROP_LAPS) {
  const text = DOORS.split(`case ${lap}:`)[1].split('return r;')[0];
  const row = { lap, flag: `enter_lap${lap}` };
  for (const key of ['upper', 'lower', 'lo', 'hi']) row[key] = V(...text.match(new RegExp(`r\\.${key} = \\( ([^)]*) \\)`))[1].split(',').map(Number));
  drops.set(lap, row);
}
const genLaps = +GEN.match(/^const LAPS = (\d+);/m)[1];
const gs = GEN.match(/^const STEPS = (\d+), TREAD = (\d+), RISE = (\d+);/m);
const genRise = 2 * (+gs[1]) * (+gs[3]);
const L = (lap, off) => (lap - 1) * genRise + off;
function towerFlags(open) {
  const f = {};
  for (let k = 1; k <= genLaps; k++) if (!drops.has(k)) f['enter_lap' + k] = open;
  f.enter_roof = open;
  return f;
}

// ---------------------------------------------------------------------------
// Stock's curves, verbatim (_zm.gsc get_zombie_spawn_delay / get_zombie_count_for_round,
// zombie_utility.gsc default_max_zombie_func). GSC int() truncates.
// ---------------------------------------------------------------------------
function stockDelay(n, players) {
  if (n > 60) n = 60;
  let d = { 1: 2.0, 2: 1.5, 3: 0.89, 4: 0.67 }[players];
  for (let i = 1; i < n; i++) { d *= 0.95; if (d <= 0.1) { d = 0.1; break; } }
  return d;
}
function stockCount(n, players, maxAi, perPlayer) {
  let max = maxAi;
  let mult = n / 5;
  if (mult < 1) mult = 1;
  if (n >= 10) mult *= n * 0.15;
  if (players === 1) max += Math.trunc((0.5 * perPlayer) * mult);
  else max += Math.trunc(((players - 1) * perPlayer) * mult);
  if (n < 2) return Math.trunc(max * 0.25);
  if (n < 3) return Math.trunc(max * 0.3);
  if (n < 4) return Math.trunc(max * 0.5);
  if (n < 5) return Math.trunc(max * 0.7);
  if (n < 6) return Math.trunc(max * 0.9);
  return max;
}
const map1Delay = (n, p) => Math.max(stockDelay(n, p) * MAP1.mult, MAP1.floor);

// ---------------------------------------------------------------------------
// The interpreter harness. Method calls and pointer calls become plain builtins.
// ---------------------------------------------------------------------------
const IS_TRUE = x => x !== undefined && x !== null && !!x && x !== 0;
function translate(t) {
  return t.replace(/^\s*\/#\s*$/gm, '').replace(/^\s*#\/\s*$/gm, '')
    .replace(/level flag::exists\(/g, 'flag_exists(')
    .replace(/level flag::get\(/g, 'flag_get(')
    .replace(/(\w+) laststand::player_is_in_laststand\(\)/g, 'laststand_of( $1 )')
    .replace(/\[\[ level\.tod_haven_inside_fn \]\]\( ([\w.]+) \)/g, 'haven_inside_stub( $1 )')
    .replace(/\[\[ level\.tod_haven_calm_fn \]\]\(\)/g, 'haven_calm_stub()')   // docs/202 v3: the x1.19 rest asks the haven's field
    .replace(/\[\[ level\.tod_stock_spawn_delay_func \]\]\( (\w+) \)/g, 'stock_delay( $1 )')
    .replace(/(\w+) GetPlayerAngles\(\)/g, 'player_angles( $1 )')
    .replace(/(\w+) GetEntityNumber\(\)/g, 'ent_num( $1 )')
    .replace(/(\w+) CanPath\( /g, 'can_path( $1, ')
    .replace(/(\w+) IsTouching\( /g, 'is_touching( $1, ')
    .replace(/\bpath_agent\( self \)/g, 'path_agent( self_stub() )')
    .replace(/\bself tod_ambush::pick\( /g, 'tod_ambush::pick( ')
    .replace(/" at=" \+ org\b/g, '" at=" + vec_str( org )');   // the interpreter has no string + vector
}
function lcg(seed) {
  let s = seed >>> 0;
  return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; };
}
const norm = v => { const l = Math.hypot(v[0], v[1], v[2]); return l > 0 ? V(v[0] / l, v[1] / l, v[2] / l) : V(0, 0, 0); };
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const fwdOf = yaw => V(Math.cos(yaw * D2R), Math.sin(yaw * D2R), 0);
const P = (x, y, z, extra = {}) => ({ origin: V(x, y, z), last_valid_position: V(x, y, z), sessionstate: 'playing', yaw: 0, num: 0, ...extra });
const box = (c, half, halfZ) => ({ mins: V(c[0] - half, c[1] - half, c[2] - halfZ), maxs: V(c[0] + half, c[1] + half, c[2] + halfZ) });
function ringAround(c, radii, stepDeg, dzs, fromDeg = 0, toDeg = 360) {
  const pts = [];
  for (const r of radii) for (let a = fromDeg; a < toDeg; a += stepDeg) for (const dz of dzs)
    pts.push(V(Math.round(c[0] + r * Math.cos(a * D2R)), Math.round(c[1] + r * Math.sin(a * D2R)), c[2] + dz));
  return pts;
}

function makeEnv() {
  return { flags: towerFlags(true), players: [], now: 0, rng: lcg(20261003), nplayers: 1, canPathCalls: 0, touchCalls: 0, spawns: 0,
           queries: 0, lastQuery: null, printed: [], ring: [], agents: [], self: undefined };
}
function load(ambush, endless, env) {
  const all = { ...defs(REACH), ...defs(endless), ...defs(ambush) };
  return gscLoad([
    ['tod_ambush', translate(ambush)], ['tod_endless_rounds', translate(endless)], ['tod_reach', translate(REACH)],
    ['tod_crown_data', CROWN], ['tod_arena_data', ARENA], ['tod_house_data', HOUSE],
  ], all, {
    random: () => env.rng(),
    builtins: {
      IS_TRUE,
      flag_exists: f => env.flags[f] !== undefined,
      flag_get: f => !!env.flags[f],
      'tod_door_data::get_drop_info': lap => drops.get(lap),
      'tod_breather_data::lounge_index_at': o => (env.loungeAt && env.loungeAt(o)) ? 0 : -1,
      laststand_of: p => !!p.downed,
      haven_inside_stub: o => !!(env.havenAt && env.havenAt(o)),
      haven_calm_stub: () => !!env.calm,   // docs/202 v3: a living player stands inside a TAKEN haven field
      stock_delay: n => stockDelay(n, env.nplayers),
      player_angles: p => V(0, p.yaw || 0, 0),
      ent_num: p => p.num || 0,
      can_path: (ai, a, b) => { env.canPathCalls++; return env.canPath ? !!env.canPath(a, b) : true; },
      is_touching: (ent, vol) => {
        env.touchCalls++;
        const o = ent.origin;
        return o[0] >= vol.mins[0] && o[0] <= vol.maxs[0] && o[1] >= vol.mins[1] && o[1] <= vol.maxs[1] && o[2] >= vol.mins[2] && o[2] <= vol.maxs[2];
      },
      self_stub: () => env.self,
      'array::random': a => a[Math.floor(env.rng() * a.length)],
      Distance2D: (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]),
      DistanceSquared: (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2,
      LengthSquared: v => v[0] * v[0] + v[1] * v[1] + v[2] * v[2],
      VectorDot: dot, VectorNormalize: norm,
      GetPlayers: () => env.players, isplayer: p => !!p,
      isalive: p => !!p && p.alive !== false, IsAlive: p => !!p && p.alive !== false,
      IsActor: e => !!(e && e.actor), GetAITeamArray: () => env.agents,
      GetTime: () => env.now, GetArrayKeys: o => Object.keys(o),
      Spawn: (cls, pos) => { env.spawns++; return { classname: cls, origin: pos }; },
      PositionQuery_Source_Navigation: (o, mn, mx, h, sp) => {
        env.queries++; env.lastQuery = [o, mn, mx, h, sp];
        return { data: (env.ringFn ? env.ringFn(o) : env.ring).map(p => ({ origin: p })) };
      },
      PrintLn: s => env.printed.push(s),
      vec_str: v => '(' + v.join(', ') + ')',
    },
  });
}

// The shipping classification, re-derived independently from the logged spot (the check
// does not trust the module's own bucket).
function seenBy(players, org) {
  return players.some(p => p && p.alive !== false && p.sessionstate !== 'spectator'
    && dot(fwdOf(p.yaw || 0), norm(V(org[0] - p.origin[0], org[1] - p.origin[1], org[2] - p.origin[2]))) >= A('TOD_AMBUSH_FOV_COS'));
}
function flatDot(focus, org) {
  return dot(fwdOf(focus.yaw || 0), norm(V(org[0] - focus.origin[0], org[1] - focus.origin[1], 0)));
}

// sections: A share, B roll, C bucket, D order, E legal, F focus, G1 split + spot, G2 seen,
// G3 cache, G4 gap, G5 fallback, G6 zones, G7 engine path, G8 guards, G9 path agent,
// H the hook, I the trickle. `only` = null runs everything at full size (the base run).
function suite(ambush, endless, only = null) {
  const out = [];
  const t = (ok, label) => { if (!ok) out.push(label); };
  const run = s => !only || only.includes(s);
  const big = !only;
  const env = makeEnv();
  let g;
  try { g = load(ambush, endless, env); } catch (e) { return ['the shipping GSC failed to load: ' + e.message]; }
  const call = (n, a) => g.call(n, a);
  try {
    call('tod_reach::build_cuts', []);
    g.level.tod_reach_ready = true;
    g.level.tod_reach_spawn_kept = 0; g.level.tod_reach_spawn_cut = 0; g.level.tod_reach_spawn_open = 0; g.level.tod_reach_spawn_far = 0;
    g.level.tod_gate_open = true;        // TOD II: the finale is parked, the terrace gate opens at init
    g.level.tod_ambush_on = true;
    g.level.round_number = 15;
    g.level.zombie_team = 'axis';
    const share = (r, ramp) => call('tod_ambush::share_pct', [r, ramp]);
    const c = V(0, 0, L(12, 192));
    const zones = () => ({ lap12: { is_enabled: true, is_active: true, is_spawning_allowed: true, volumes: [box(c, 2000, 600)] } });
    g.level.zones = zones();
    env.agents = [{ actor: true, archetype: 'zombie' }];
    env.self = { actor: true, archetype: 'zombie' };
    const fresh = () => { env.now += 1000; };
    const pick = () => call('tod_ambush::pick', [[]]);
    const tally = () => ({ ...(g.level.tod_ambush_n || {}) });
    const solo = () => { env.players = [P(c[0], c[1], c[2], { yaw: 0, num: 0 })]; };
    const fullRing = () => { env.ring = ringAround(c, [250, 300, 420, 540, 660, 780, 880], 15, [0]); };
    const anyIn = n => { let any = false; for (let i = 0; i < n; i++) { fresh(); if (pick() !== undefined) any = true; } return any; };

    // ---- A. THE SHARE -------------------------------------------------------------
    if (run('A')) {
      t(share(1, false) === A('TOD_AMBUSH_PCT_START'), `share: round 1 = ${A('TOD_AMBUSH_PCT_START')}% (got ${share(1, false)})`);
      t(share(A('TOD_AMBUSH_FULL_ROUND'), false) === A('TOD_AMBUSH_PCT_FULL'), `share: round ${A('TOD_AMBUSH_FULL_ROUND')} = ${A('TOD_AMBUSH_PCT_FULL')}%`);
      t(share(100, false) === A('TOD_AMBUSH_PCT_FULL'), 'share: holds at the full share past the full round');
      t(share(undefined, false) === A('TOD_AMBUSH_PCT_START') && share(0, false) === A('TOD_AMBUSH_PCT_START'), 'share: no round / round 0 reads as round 1');
      let mono = true, prev = -1, inRange = true;
      for (let r = 1; r <= 80; r++) {
        const s = share(r, false), sr = share(r, true);
        if (s < prev) mono = false;
        prev = s;
        if (!(s >= 0 && s <= A('TOD_AMBUSH_PCT_MAX') && sr <= A('TOD_AMBUSH_PCT_MAX') && sr >= s)) inRange = false;
      }
      t(mono, 'share: never falls as the rounds climb');
      t(inRange, 'share: always within 0..TOD_AMBUSH_PCT_MAX, and the Rampage inducer never lowers it');
      t(share(1, true) === A('TOD_AMBUSH_PCT_START') + A('TOD_AMBUSH_PCT_RAMPAGE'), 'share: the Rampage inducer adds its points');
    }

    // ---- B. THE DIRECTION ROLL ------------------------------------------------------
    if (run('B')) {
      const roll = { ahead: 0, behind: 0, flank: 0 };
      for (let r = 0; r < 100; r++) roll[call('tod_ambush::intent_of', [r])]++;
      t(roll.ahead === A('TOD_AMBUSH_AHEAD_PCT') && roll.behind === A('TOD_AMBUSH_BEHIND_PCT') && roll.flank === 100 - A('TOD_AMBUSH_AHEAD_PCT') - A('TOD_AMBUSH_BEHIND_PCT'),
        `direction roll: ahead ${roll.ahead} / behind ${roll.behind} / flank ${roll.flank} of 100`);
    }

    // ---- C. THE BUCKET RULE ---------------------------------------------------------
    if (run('C')) {
      const bucket = (d, seen) => call('tod_ambush::bucket_of', [d, seen]);
      t(bucket(0.95, false) === 'ahead' && bucket(0.95, true) === 'ahead', 'bucket: in front is AHEAD, seen or not');
      t(bucket(A('TOD_AMBUSH_AHEAD_COS'), false) === 'ahead', 'bucket: the ahead edge is ahead');
      t(bucket(-0.95, false) === 'behind', 'bucket: behind and unseen is BEHIND');
      t(bucket(-0.95, true) === 'flank', 'bucket: behind but SEEN by someone is a flank, never "behind"');
      t(bucket(A('TOD_AMBUSH_BEHIND_COS'), false) === 'behind', 'bucket: the behind edge is behind');
      t(bucket(0, false) === 'flank' && bucket(0, true) === 'flank', 'bucket: beside is a flank');
    }

    // ---- D. THE TRY ORDER -----------------------------------------------------------
    if (run('D')) {
      for (const intent of ['ahead', 'behind', 'flank']) {
        const o = call('tod_ambush::try_order', [intent]);
        t(o[0] === intent, `try order: "${intent}" is tried first`);
        t([...o].sort().join() === 'ahead,behind,flank', `try order: "${intent}" falls back through every direction`);
      }
      t(call('tod_ambush::try_order', ['ahead'])[1] === 'flank' && call('tod_ambush::try_order', ['behind'])[1] === 'flank', 'try order: a flank before the opposite direction');
    }

    // ---- E. LEGALITY (the real walk model, the real generated data) -------------------
    if (run('E')) {
      const legal = (o, goal) => call('tod_ambush::legal', [o, goal]);
      const hero = P(c[0], c[1], c[2]);
      env.players = [hero];
      t(legal(V(c[0] + 500, c[1], c[2]), c), 'legal: a point 500 away on the same floor is legal');
      t(!legal(V(c[0] + 200, c[1], c[2]), c), `legal: inside TOD_AMBUSH_INNER (${A('TOD_AMBUSH_INNER')}) of a player is refused`);
      env.players = [hero, P(c[0] + 650, c[1], c[2], { downed: true })];
      t(!legal(V(c[0] + 600, c[1], c[2]), c), 'legal: next to a DOWNED player is refused too');
      env.players = [hero, P(c[0] + 650, c[1], c[2], { sessionstate: 'spectator' })];
      t(legal(V(c[0] + 600, c[1], c[2]), c), 'legal: a spectator does not count');
      const r43 = drops.get(43);
      env.players = [P(r43.upper[0], r43.upper[1], r43.upper[2])];
      t(!legal(V(r43.lower[0] + 400, r43.lower[1], r43.lower[2]), r43.upper), 'legal: below a drop while the player is on its ledge is refused (the walk model)');
      t(legal(V(r43.upper[0] + 400, r43.upper[1], r43.upper[2]), r43.upper), 'legal: the ledge floor itself is legal');
      env.players = [hero];
      g.level.tod_haven_inside_fn = 'point_inside_live';
      const hv = V(c[0] + 500, c[1], c[2]);
      env.havenAt = o => Math.hypot(o[0] - hv[0], o[1] - hv[1]) < 200 && Math.abs(o[2] - hv[2]) < 96;
      t(!legal(hv, c), 'legal: inside a live safe-zone field is refused');
      t(legal(V(c[0] - 500, c[1], c[2]), c), 'legal: outside the field is legal');
      env.havenAt = undefined; g.level.tod_haven_inside_fn = undefined;
      const arenaGoal = V(-8000, -8400, 0);
      env.players = [P(arenaGoal[0], arenaGoal[1], arenaGoal[2])];
      t(!legal(V(-8000, -7900, 0), arenaGoal), 'legal: inside the Battle Arena is refused');
      const terrace = V(0, 300, 19392);
      env.players = [P(terrace[0], terrace[1], terrace[2])];
      g.level.tod_gate_open = false;
      t(!legal(V(0, 800, 19392), terrace), 'legal: beyond the shut causeway gate is refused');
      g.level.tod_gate_open = true;
      t(legal(V(0, 800, 19392), terrace), 'legal: the same point with the gate open is legal');
      const hall = V(0, 8608, 19392);
      env.players = [P(hall[0], hall[1], hall[2])];
      g.level.tod_fall_sealed = true;
      t(!legal(V(500, 8608, 19392), hall), 'legal: the crown island after the Fall seals is refused');
      g.level.tod_fall_return_open = true;
      t(legal(V(500, 8608, 19392), hall), 'legal: the island again once the bottom return opens');
      g.level.tod_fall_sealed = false; g.level.tod_fall_return_open = false;
      // (W2E 2026-10-05: the sealed-hall rule retired with the Map One ending - no writer of tod_crown_sealed is left;
      // the WIRING section pins that legal() no longer reads it.)
    }

    // ---- F. THE FOCUS ---------------------------------------------------------------
    if (run('F')) {
      const focus = () => call('tod_ambush::pick_focus', []);
      const up = P(c[0], c[1], c[2], { num: 1 });
      env.players = [P(0, 0, 0, { downed: true }), P(0, 0, 0, { sessionstate: 'spectator' }), P(0, 0, 0, { tod_jumppad_flying: true }), up];
      let onlyUp = true;
      for (let i = 0; i < 30; i++) if (focus() !== up) onlyUp = false;
      t(onlyUp, 'focus: never a crawler, a spectator or a jump-pad flyer');
      env.players = [P(0, 0, 0, { downed: true })];
      t(focus() === undefined, 'focus: nobody upright -> no ambush');
      env.players = [up];
      g.level.tod_haven_inside_fn = 'point_inside_live';
      env.havenAt = o => Math.hypot(o[0] - up.origin[0], o[1] - up.origin[1]) < 50;
      t(focus() === undefined, 'focus: a player resting inside a safe-zone field is never ambushed');
      env.havenAt = undefined; g.level.tod_haven_inside_fn = undefined;
      env.players = [P(-8000, -8000, 0)];
      t(focus() === undefined, 'focus: a player in the Battle Arena is never the focus');
      env.players = [up];
      env.now = 100000;
      up.tod_ambush_ms = env.now - 100;
      t(focus() === undefined, 'focus: ambushed 100 ms ago -> waits out TOD_AMBUSH_GAP_MS');
      up.tod_ambush_ms = env.now - A('TOD_AMBUSH_GAP_MS');
      t(focus() === up, 'focus: after TOD_AMBUSH_GAP_MS he is eligible again');
      delete up.tod_ambush_ms;
    }

    // ---- G1. THE PICK, END TO END: the share, the split, the spot ---------------------
    if (run('G1')) {
      solo(); fullRing();
      g.level.tod_dev = true;
      const N = big ? 1200 : 300;
      const got = { ahead: 0, behind: 0, flank: 0 };
      let returned = 0, badSpot = 0, badDist = 0, badFace = 0, badBehind = 0, badAhead = 0, parsed = 0, offCentre = 0;
      for (let i = 0; i < N; i++) {
        fresh();
        g.level.tod_ambush_logged = 0;
        env.printed.length = 0;
        const s = pick();
        if (env.lastQuery && env.lastQuery[0] !== env.players[0].last_valid_position) offCentre++;
        if (s === undefined) continue;
        returned++;
        if (!(s.script_noteworthy === 'riser_location' && s.script_string === 'find_flesh' && s.zone_name === 'lap12' && s.tod_ambush === true && Array.isArray(s.angles)))
          badSpot++;
        if (env.players.some(p => Math.hypot(...[0, 1, 2].map(k => s.origin[k] - p.origin[k])) < A('TOD_AMBUSH_INNER'))) badDist++;
        const line = env.printed.find(l => / PICK /.test(l));
        if (!line) continue;
        parsed++;
        const gotB = line.match(/got=(\w+)/)[1];
        const f = env.players[0];
        got[gotB]++;
        const want = Math.atan2(f.origin[1] - s.origin[1], f.origin[0] - s.origin[0]) / D2R;
        if (Math.abs(((s.angles[1] - want) % 360 + 540) % 360 - 180) > 0.01) badFace++;
        const d = flatDot(f, s.origin);
        if (gotB === 'behind' && (seenBy(env.players, s.origin) || d > A('TOD_AMBUSH_BEHIND_COS') + 1e-9)) badBehind++;
        if (gotB === 'ahead' && d < A('TOD_AMBUSH_AHEAD_COS') - 1e-9) badAhead++;
      }
      g.level.tod_dev = false;
      const frac = returned / N;
      if (big) { MEASURED.share = (frac * 100).toFixed(1) + '%'; MEASURED.split = `${got.ahead}/${got.behind}/${got.flank}`; }
      t(Math.abs(frac - share(15, false) / 100) < (big ? 0.05 : 0.08), `pick: about ${share(15, false)}% of round-15 spawns are ambushes (got ${(frac * 100).toFixed(1)}%)`);
      t(badSpot === 0, `pick: every spot is a riser stock's climb-out reads (riser_location / find_flesh / zone / angles) (${badSpot} bad)`);
      t(badDist === 0, `pick: never inside TOD_AMBUSH_INNER of any player (${badDist} bad)`);
      t(parsed === returned, `pick: every ambush writes its PICK log line in dev (${parsed} of ${returned})`);
      t(badFace === 0, `pick: every riser faces its focus (${badFace} bad)`);
      t(badBehind === 0, `pick: a "behind" spawn is behind its focus and off screen (${badBehind} bad)`);
      t(badAhead === 0, `pick: an "ahead" spawn is in front of its focus (${badAhead} bad)`);
      t(offCentre === 0, 'pick: the ring is centred on the focus\'s navmesh point');
      const tot = got.ahead + got.behind + got.flank, tol = big ? 0.06 : 0.12;
      t(tot > 0 && Math.abs(got.ahead / tot - A('TOD_AMBUSH_AHEAD_PCT') / 100) < tol && Math.abs(got.behind / tot - A('TOD_AMBUSH_BEHIND_PCT') / 100) < tol,
        `pick: the direction split follows the roll (ahead ${got.ahead} / behind ${got.behind} / flank ${got.flank})`);
      t(env.spawns === 1, `pick: ONE persistent zone probe for the whole run (spawned ${env.spawns})`);
      t(env.lastQuery && env.lastQuery[1] === A('TOD_AMBUSH_INNER') && env.lastQuery[2] === A('TOD_AMBUSH_OUTER') && env.lastQuery[3] === A('TOD_AMBUSH_HEIGHT') && env.lastQuery[4] === A('TOD_AMBUSH_SPACING'),
        'pick: the navmesh ring is queried with the ring knobs');
    }

    // ---- G2. "BEHIND" MEANS OFF EVERY SCREEN (a teammate watching his back) -----------
    if (run('G2')) {
      const h1 = P(c[0], c[1], c[2], { yaw: 0, num: 0 });
      const h2 = P(c[0] + 420, c[1], c[2], { yaw: 180, num: 1 });
      env.players = [h1, h2];
      fullRing();
      g.level.tod_dev = true;
      let behind = 0, badBehind = 0;
      for (let i = 0; i < (big ? 600 : 200); i++) {
        fresh();
        g.level.tod_ambush_logged = 0;
        env.printed.length = 0;
        const s = pick();
        const line = env.printed.find(l => / PICK /.test(l));
        if (s === undefined || !line) continue;
        const f = env.players.find(p => p.num === +line.match(/focus=(\d+)/)[1]);
        if (line.match(/got=(\w+)/)[1] !== 'behind') continue;
        behind++;
        if (seenBy(env.players, s.origin) || flatDot(f, s.origin) > A('TOD_AMBUSH_BEHIND_COS') + 1e-9) badBehind++;
      }
      g.level.tod_dev = false;
      t(badBehind === 0, `pick: with a teammate watching his back, no "behind" spawn is on anyone's screen (${badBehind} of ${behind} bad)`);
    }

    // ---- G3. THE RING CACHE ---------------------------------------------------------
    if (run('G3')) {
      solo();
      env.ring = ringAround(c, [420, 540, 660], 15, [0]);
      const q0 = env.queries;
      env.now += 5000; call('tod_ambush::ring', [env.players[0], c]);
      env.now += 100; call('tod_ambush::ring', [env.players[0], c]);
      t(env.queries - q0 === 1, 'ring: cached for TOD_AMBUSH_CACHE_MS');
      env.now += A('TOD_AMBUSH_CACHE_MS'); call('tod_ambush::ring', [env.players[0], c]);
      t(env.queries - q0 === 2, 'ring: re-queried after TOD_AMBUSH_CACHE_MS');
    }

    // ---- G4. THE GAP: two spawns in one moment never both rise round one player ---------
    if (run('G4')) {
      solo(); fullRing();
      g.level.round_number = 40; g.level.tod_rampage_on = true;
      let first;
      for (let i = 0; i < 40 && first === undefined; i++) { fresh(); first = pick(); }
      t(first !== undefined, 'pick: an ambush happens');
      let second = false;
      for (let i = 0; i < 20; i++) if (pick() !== undefined) second = true;   // same moment, many tries
      t(!second, 'pick: further spawns in the same moment do not rise round the same player (the gap)');
      let again;
      for (let i = 0; i < 40 && again === undefined; i++) { env.now += A('TOD_AMBUSH_GAP_MS'); again = pick(); }
      t(again !== undefined, 'pick: after the gap he can be ambushed again');
      g.level.round_number = 15; g.level.tod_rampage_on = false;
    }

    // ---- G5. FALLBACK: a roll with no point in its direction takes another -------------
    if (run('G5')) {
      solo();
      env.ring = ringAround(c, [420, 540, 660, 780], 10, [0], 150, 211);   // everything behind him
      const n0 = tally();
      let hits = 0;
      for (let i = 0; i < (big ? 300 : 120); i++) { fresh(); if (pick() !== undefined) hits++; }
      const n1 = tally();
      t(hits > 0 && (n1.fallback || 0) > (n0.fallback || 0), `pick: a roll with no point in its direction falls back to another (${(n1.fallback || 0) - (n0.fallback || 0)} fallbacks)`);
      t((n1.no_spot || 0) === (n0.no_spot || 0), 'pick: a fallback never ends in "no spot" while any direction has a legal point');
    }

    // ---- G6. THE ZONE RULE (stock's: enabled, active, spawning allowed) ----------------
    if (run('G6')) {
      solo(); fullRing();
      g.level.zones.lap12.is_active = false;
      const p0 = env.canPathCalls;
      t(!anyIn(150), 'pick: never in a zone that is not active');
      t(env.canPathCalls === p0, 'pick: a point outside a spawnable zone never costs a path check');
      g.level.zones = zones();
      g.level.zones.lap12.is_spawning_allowed = false;
      t(!anyIn(150), 'pick: never in a zone with spawning switched off');
      // A live zone whose volume does not hold the ring: every lookup touches and misses.
      g.level.zones = { elsewhere: { is_enabled: true, is_active: true, is_spawning_allowed: true, volumes: [box(V(c[0] + 9000, c[1], c[2]), 300, 300)] } };
      let maxTouch = 0, any = false;
      for (let i = 0; i < 150; i++) { fresh(); const t0 = env.touchCalls; if (pick() !== undefined) any = true; maxTouch = Math.max(maxTouch, env.touchCalls - t0); }
      t(!any, 'pick: a point in no spawnable zone is never used');
      t(maxTouch > 0 && maxTouch <= A('TOD_AMBUSH_ZONE_TRIES'), `pick: at most TOD_AMBUSH_ZONE_TRIES zone lookups a spawn (max ${maxTouch})`);
      g.level.zones = zones();
    }

    // ---- G7. THE ENGINE'S WORD: CanPath false -> no spot, and a bounded number asked ---
    if (run('G7')) {
      solo(); fullRing();
      env.canPath = () => false;
      let maxPath = 0, any = false;
      for (let i = 0; i < 150; i++) { fresh(); const p0 = env.canPathCalls; if (pick() !== undefined) any = true; maxPath = Math.max(maxPath, env.canPathCalls - p0); }
      t(!any, 'pick: a point the engine cannot path to the player is never used');
      t(maxPath > 0 && maxPath <= A('TOD_AMBUSH_PROBES'), `pick: at most TOD_AMBUSH_PROBES engine path checks a spawn (max ${maxPath})`);
      env.canPath = undefined;
    }

    // ---- G8. THE GUARDS: an arena trip, a card pause, no init (the finale's aggro guard retired 2026-10-05) ---
    if (run('G8')) {
      solo(); fullRing();
      for (const flag of ['tod_arena_active', 'tod_upgrade_pause']) {
        g.level[flag] = true;
        t(!anyIn(80), `pick: no ambush while level.${flag}`);
        g.level[flag] = false;
      }
      g.level.tod_ambush_on = false;
      t(!anyIn(80), 'pick: nothing before init');
      g.level.tod_ambush_on = true;
    }

    // ---- G9. THE PATH AGENT: the zombie itself, else any live zombie, else nothing -----
    if (run('G9')) {
      solo(); fullRing();
      const nA = tally();
      for (let i = 0; i < 60; i++) { fresh(); pick(); }
      const nB = tally();
      t((nB.agent_self || 0) > (nA.agent_self || 0) && (nB.agent_other || 0) === (nA.agent_other || 0), 'path agent: the zombie being spawned answers its own path check');
      env.self = {};                     // a hook called without a zombie (self is not an actor)
      for (let i = 0; i < 60; i++) { fresh(); pick(); }
      const nC = tally();
      t((nC.agent_other || 0) > (nB.agent_other || 0), 'path agent: without one, any live zombie answers');
      env.agents = [];
      t(!anyIn(60), 'path agent: no actor at all -> the corners');
      env.agents = [{ actor: true, archetype: 'zombie' }];
      env.self = { actor: true, archetype: 'zombie' };
    }

    // ---- H. THE HOOK (finale_spawn_selection, the non-finale path) --------------------
    if (run('H')) {
      solo();
      env.ring = ringAround(c, [420, 540, 660, 780], 15, [0]);
      const cornerA = { origin: V(336, 336, L(12, 192)), script_noteworthy: 'riser_location' };
      const cornerB = { origin: V(-336, 336, L(12, 384)), script_noteworthy: 'riser_location' };
      const M = big ? 600 : 200;
      let amb = 0, corner = 0, undef = 0;
      for (let i = 0; i < M; i++) {
        fresh();
        const s = call('tod_endless_rounds::finale_spawn_selection', [[cornerA, cornerB]]);
        if (s === undefined) undef++;
        else if (s.tod_ambush) amb++;
        else if (s === cornerA || s === cornerB) corner++;
      }
      t(undef === 0, 'hook: always hands stock a spot');
      t(Math.abs(amb / M - share(15, false) / 100) < (big ? 0.07 : 0.1), `hook: round 15 -> about ${share(15, false)}% ambush spawns, the rest on the corners (${amb} / ${corner})`);
      g.level.zones.lap12.is_active = false;
      amb = 0; corner = 0;
      for (let i = 0; i < 100; i++) { fresh(); const s = call('tod_endless_rounds::finale_spawn_selection', [[cornerA, cornerB]]); if (s && s.tod_ambush) amb++; else if (s === cornerA || s === cornerB) corner++; }
      t(amb === 0 && corner === 100, 'hook: when the ambush has nothing, the authored corners carry every spawn');
      g.level.zones = zones();
    }

    // ---- I. THE TRICKLE (tod_spawn_delay, run verbatim) -------------------------------
    if (run('I')) {
      const ED = defs(endless);          // the knobs of the text under test (a mutant's, too)
      const delay = n => call('tod_endless_rounds::tod_spawn_delay', [n]);
      // THE RAMP (2026-10-04, user after the first real playthrough: "Zombies are spawning in way too
      // fast too early ... Game should ramp up"). The early trickle is SLOWER on purpose: the resolver
      // is the late-game trickle x the ramp factor (x TOD_SPAWN_RAMP_EARLY on round 1, easing to x1.0
      // on TOD_SPAWN_RAMP_FULL_ROUND; rampage eases out on TOD_RAMPAGE_SPAWN_RAMP_FULL_ROUND). docs/204's
      // "more hectic than map 1" is held from the full round on, where the ramp has ended. The old
      // contract (hotter than map 1 from round 1) is a negative control below ("the ramp removed").
      const early = +ED.TOD_SPAWN_RAMP_EARLY, fullR = +ED.TOD_SPAWN_RAMP_FULL_ROUND, fullRR = +ED.TOD_RAMPAGE_SPAWN_RAMP_FULL_ROUND;
      const rampOf = (n, full) => (n <= 1 ? early : (n >= full ? 1 : early + (1 - early) * (n - 1) / (full - 1)));
      env.players = [P(0, 0, 0)];
      let hotter = true, minRate = 99, minLen = 99, maxLen = 0, worst = '', exact = true, exactAt = '', rampSlower = true, late = 0;
      for (let p = 1; p <= 4; p++) {
        env.nplayers = p;
        for (let n = 1; n <= 60; n++) {
          const d = delay(n), d1 = map1Delay(n, p), rf = rampOf(n, fullR);
          const want = Math.max(stockDelay(n, p) * +ED.TOD_SPAWN_MULT * rf, +ED.TOD_SPAWN_FLOOR);
          if (!(Math.abs(d - want) < 1e-9)) { if (exact) exactAt = `${p}p r${n}: ${d} vs ${want}`; exact = false; }
          g.level.tod_rampage_on = true;
          if (!(delay(n) <= d + 1e-9)) rampSlower = false;   // the hard mode is never the slower trickle
          g.level.tod_rampage_on = false;
          // the round's length against map 1's, the ramp factored out: the round SIZE must still carry the rate
          const lateD = Math.max(stockDelay(n, p) * +ED.TOD_SPAWN_MULT, +ED.TOD_SPAWN_FLOOR);   // the trickle without the ramp
          const ratio = (stockCount(n, p, +ED.TOD_ROUND_MAX_AI, +ED.TOD_ROUND_AI_PER_PLAYER) * (n < fullR ? lateD : d)) / (stockCount(n, p, MAP1.maxAi, MAP1.perPlayer) * d1);
          if (ratio < minLen) { minLen = ratio; worst = `${p}p r${n}`; }
          maxLen = Math.max(maxLen, ratio);
          if (n < fullR) continue;   // the ramp's rounds: slower than the late trickle by design (exact, above)
          late++;
          if (!(d < d1)) hotter = false;
          minRate = Math.min(minRate, d1 / d);
        }
      }
      env.nplayers = 1;
      if (big) { MEASURED.rate = 'x' + minRate.toFixed(2); MEASURED.len = `x${minLen.toFixed(2)}..x${maxLen.toFixed(2)}`; }
      t(early > 1 && fullR > 1 && fullR <= 30 && fullRR < fullR, `trickle: THE RAMP starts slower (x${early}), ends by round 30 (the user's figure; ${fullR}) and rampage eases out of it sooner (round ${fullRR})`);
      t(exact, `trickle: every round is the late trickle x THE RAMP, exactly (x${early} on round 1, x1.0 from round ${fullR})${exact ? '' : ' - first miss ' + exactAt}`);
      t(late >= 4 * 30, `trickle: the late game is checked over 30+ rounds at every party size (${late / 4} rounds)`);
      t(hotter, `trickle: from round ${fullR} on, every party size spawns faster than map 1`);
      t(minRate >= 1.15, `trickle: from round ${fullR} on, at least +15% zombies a second over map 1 (min x${minRate.toFixed(3)})`);
      t(minLen >= 0.88 && maxLen <= 1.06, `trickle: with the ramp factored out, a round lasts -12%..+6% of map 1's (the round size rose with the rate) (x${minLen.toFixed(3)} at ${worst} .. x${maxLen.toFixed(3)})`);
      t(rampSlower, 'trickle: Rampage never trickles slower than the normal mode, at any round or party size');
      t(Math.abs(delay(60) - +ED.TOD_SPAWN_FLOOR) < 1e-9, 'trickle: deep rounds sit on TOD_SPAWN_FLOOR');
      g.level.tod_rampage_on = true;
      t(Math.abs(delay(60) - +ED.TOD_RAMPAGE_SPAWN_FLOOR) < 1e-9 && delay(fullRR + 5) < map1Delay(fullRR + 5, 1) * 0.8, 'trickle: the Rampage inducer squeezes harder and floors lower once its ramp is over');
      g.level.tod_rampage_on = false;
      g.level.tod_fall_phase = true;
      t(Math.abs(delay(5) - Math.max(stockDelay(5, 1) * +ED.TOD_SPAWN_MULT * rampOf(5, fullR) * +ED.TOD_FALL_SPAWN_MULT, +ED.TOD_SPAWN_FLOOR)) < 1e-9, 'trickle: the crown phase (the Fall) runs at TOD_FALL_SPAWN_MULT x the ramp');
      g.level.tod_fall_phase = false;
      const base5 = delay(5);
      env.loungeAt = () => true;
      t(Math.abs(delay(5) - base5) < 1e-9, 'trickle: standing in the hall (the loggia) no longer calms the spawn clock (docs/202 v3)');
      env.loungeAt = undefined;
      g.level.tod_haven_calm_fn = 'calm_any';
      env.calm = true;
      t(Math.abs(delay(5) - base5 * 1.19) < 1e-9, 'trickle: a player inside a TAKEN haven field keeps the x1.19 rest');
      env.calm = false;
      t(Math.abs(delay(5) - base5) < 1e-9, 'trickle: no one inside = no rest');
      g.level.tod_haven_calm_fn = undefined;
      g.level.tod_finale_aggro = true;   // W2E (2026-10-05): the finale's own floor retired with the ending
      t(Math.abs(delay(5) - base5) < 1e-9, 'trickle: a stale finale flag no longer owns the floor (the Map One ending retired)');
      g.level.tod_finale_aggro = false;
    }
  } catch (e) {
    out.push('the suite threw: ' + (e && e.message));
  }
  return out;
}

const t0 = Date.now();
const base = suite(AMBUSH, ENDLESS);
if (process.argv.includes('--time')) console.log(`base suite: ${Date.now() - t0} ms`);
checks += 1;
for (const f of base) { fails++; console.log('FAIL ' + f); }

// ---------------------------------------------------------------------------
// LOCKSTEP + POLICY PINS
// ---------------------------------------------------------------------------
check(A('TOD_AMBUSH_INNER') >= +SD.TOD_STRAY_DEST_MIN, `LOCKSTEP: the ring's inner edge (${A('TOD_AMBUSH_INNER')}) >= THE HUNT's too-close bar (${SD.TOD_STRAY_DEST_MIN})`);
check(A('TOD_AMBUSH_OUTER') + A('TOD_AMBUSH_HEIGHT') * +RD.TOD_REACH_Z_WEIGHT <= +SD.TOD_STRAY_COST,
  `LOCKSTEP: the ring's worst walking cost (${A('TOD_AMBUSH_OUTER')} + ${A('TOD_AMBUSH_HEIGHT')} x ${RD.TOD_REACH_Z_WEIGHT}) <= THE HUNT's far bar (${SD.TOD_STRAY_COST}) - an ambush spawn is never relocated as FAR`);
check(A('TOD_AMBUSH_FOV_COS') === +SD.TOD_STRAY_FOV_COS, 'LOCKSTEP: the sight test is THE HUNT\'s (stock\'s FOV)');
check(A('TOD_AMBUSH_HEIGHT') <= genRise / 2, `the ring reaches one flight up and down at most (${A('TOD_AMBUSH_HEIGHT')} <= ${genRise / 2})`);
check(A('TOD_AMBUSH_AHEAD_PCT') + A('TOD_AMBUSH_BEHIND_PCT') < 100, 'a flank share exists');
check(A('TOD_AMBUSH_AHEAD_COS') > 0 && A('TOD_AMBUSH_BEHIND_COS') < 0, 'ahead is in front, behind is behind');
check(A('TOD_AMBUSH_PCT_START') <= A('TOD_AMBUSH_PCT_FULL') && A('TOD_AMBUSH_PCT_FULL') <= A('TOD_AMBUSH_PCT_MAX') && A('TOD_AMBUSH_PCT_MAX') < 100,
  'share: start <= full <= max < 100 (the authored corners always keep some spawns)');
check(A('TOD_AMBUSH_PROBES') >= 1 && A('TOD_AMBUSH_PROBES') <= 3, 'at most three engine path checks a spawn');
check(+ED.TOD_SPAWN_MULT < MAP1.mult && +ED.TOD_SPAWN_MULT >= 0.65, `TOD_SPAWN_MULT ${ED.TOD_SPAWN_MULT}: hotter than map 1 (${MAP1.mult}) and inside the ledger's working band (0.65+)`);
check(+ED.TOD_SPAWN_FLOOR < MAP1.floor && +ED.TOD_RAMPAGE_SPAWN_FLOOR < +ED.TOD_SPAWN_FLOOR, 'the floors: under map 1\'s, the Rampage floor under the normal one');
check(+ED.TOD_ROUND_MAX_AI > MAP1.maxAi && +ED.TOD_ROUND_AI_PER_PLAYER > MAP1.perPlayer, 'the round size rose with the rate');

// ---------------------------------------------------------------------------
// WIRING
// ---------------------------------------------------------------------------
const fnBody = (text, name) => { const m = text.match(new RegExp('function ' + name + '\\s*\\([^)]*\\)[^\\n{]*\\s*\\{([\\s\\S]*?)\\n\\}')); return m ? m[1] : ''; };
const fss = fnBody(ENDLESS, 'finale_spawn_selection');
const ii = s => fss.indexOf(s);
check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_ambush;/.test(ENDLESS), '_tod_endless_rounds #uses _tod_ambush');
check(/^\s*tod_ambush::init\(\s*\);/m.test(fnBody(ENDLESS, 'init')), 'tod_endless_rounds::init() starts THE AMBUSH');
check(/level\.zombie_vars\[ "zombie_max_ai" \] = TOD_ROUND_MAX_AI;/.test(ENDLESS) && /level\.zombie_vars\[ "zombie_ai_per_player" \] = TOD_ROUND_AI_PER_PLAYER;/.test(ENDLESS), 'init writes the round size knobs');
check(/level\.zombie_vars\[ "zombie_spawn_delay" \] = 2\.0 \* TOD_SPAWN_MULT \* TOD_SPAWN_RAMP_EARLY \* TOD_FALL_SPAWN_MULT;/.test(ENDLESS), 'the round-1 preset is the resolver\'s own round 1 in the crown (TOD_SPAWN_MULT x THE RAMP x the Fall)');
const tsd = fnBody(ENDLESS, 'tod_spawn_delay');
check(/d = d \* TOD_SPAWN_MULT;/.test(tsd) && /d = d \* spawn_ramp_mult\( n_round \);/.test(tsd) && /fl = TOD_SPAWN_FLOOR;/.test(tsd) && !/d \* 0\.83|fl = 0\.25/.test(tsd), 'tod_spawn_delay reads the knobs and THE RAMP, no bare 0.83 / 0.25 left');
check(ii('self tod_ambush::pick( spots )') > ii('tod_reach::filter_spawns') && ii('self tod_ambush::pick( spots )') > ii('on_crown_island'),
  'the hook runs AFTER every spawn filter');
// W2E (2026-10-05): the finale's aggro branch, its road bands, the lane lottery and the sealed hall retired whole with the
// Map One ending, so the hook is the selector's tail for every spawn: the ambush, else stock's random corner.
check(/ambush = self tod_ambush::pick\( spots \);\s*if \( isdefined\( ambush \) \)\s*return ambush;\s*return array::random\( spots \);\s*$/.test(fss)
  && !/tod_finale_aggro|tod_crown_sealed|tod_lane_seal|finale_road|finale_band/.test(fss),
  'the hook is the selector\'s tail and falls back to stock\'s random corner; nothing of the finale is left in it');
check(!/tod_crown_sealed|tod_finale_aggro/.test(AMBUSH.replace(/\/\/[^\n]*/g, '')), 'THE AMBUSH reads no retired finale state (its sealed-hall rule and aggro guard retired)');
check(/scriptparsetree,scripts\/zm\/zm_tod2_cybercity\/_tod_ambush\.gsc/.test(ZONE), 'the module is zoned');
check(/test_ambush\.js/.test(BUILD), 'build_map.ps1 runs this gate');
// The import graph: the round module imports this one, so nothing here may reach back to it.
const usingOf = text => [...text.matchAll(/^#using scripts\\zm\\zm_tod2_cybercity\\(\w+);/gm)].map(m => m[1]);
const allowed = new Set(['_tod_reach', '_tod_crown_data', '_tod_arena_data', '_tod_house_data']);
check(usingOf(AMBUSH).every(u => allowed.has(u)), `_tod_ambush imports only leaf modules (${usingOf(AMBUSH).join(', ')})`);
{
  const seen = new Set(), stack = usingOf(AMBUSH);
  let cycle = false;
  while (stack.length) {
    const m = stack.pop();
    if (m === '_tod_endless_rounds') cycle = true;
    if (seen.has(m)) continue;
    seen.add(m);
    const p = path.join(ROOT, S + m + '.gsc');
    if (fs.existsSync(p)) stack.push(...usingOf(fs.readFileSync(p, 'utf8')));
  }
  check(!cycle, 'no import path from _tod_ambush back to _tod_endless_rounds');
}
const AMBUSH_CODE = AMBUSH.replace(/\/\/[^\n]*/g, '');
check(!/get_zone_from_position/.test(AMBUSH_CODE) && (AMBUSH_CODE.match(/Spawn\( "script_origin"/g) || []).length === 1, 'the zone test moves ONE probe (no entity spawned per lookup)');
check(/PositionQuery_Source_Navigation\(\s*goal,\s*TOD_AMBUSH_INNER,\s*TOD_AMBUSH_OUTER,\s*TOD_AMBUSH_HEIGHT,\s*TOD_AMBUSH_SPACING\s*\)/.test(AMBUSH), 'the ring query uses the ring knobs');
// 2026-10-04 (docs/210): the gate may also read level.tod_diag, the console-only diagnostics switch that keeps
// feature logs printing with dev mode off. Still PrintLn inside the developer block; nothing else may ride it.
check(/function dev_log\( msg \)\s*\{\s*if \( !(?:IS_TRUE\( level\.tod_dev \)|\( IS_TRUE\( level\.tod_dev \) \|\| IS_TRUE\( level\.tod_diag \) \)) \)\s*return;[\s\S]*?\/#\s*PrintLn\( line \);\s*#\/\s*\}/.test(AMBUSH), 'the logs are console-only (dev or diag), PrintLn inside the developer block');
check(/s\.script_noteworthy = "riser_location";/.test(AMBUSH), 'the spot is a riser (stock\'s climb-out)');

// ---------------------------------------------------------------------------
// NEGATIVE CONTROLS — each mutant must be caught by the sections named for it.
// ---------------------------------------------------------------------------
let mutants = 0;
function mutant(label, file, from, to, sections) {
  mutants++;
  const src = file === 'ambush' ? AMBUSH : ENDLESS;
  if (!src.includes(from)) { fails++; console.log(`FAIL negative control "${label}": its anchor text is gone`); return; }
  const m = src.replace(from, to);
  const caught = suite(file === 'ambush' ? m : AMBUSH, file === 'endless' ? m : ENDLESS, sections);
  checks++;
  if (caught.length === 0) { fails++; console.log(`FAIL negative control "${label}" was NOT caught`); }
  else if (WHY) console.log(`  caught "${label}": ${caught[0]}`);
}
mutant('legality without the walk model', 'ambush', 'if ( !tod_reach::can_reach( org, goal ) )\n\t\treturn false;', '', ['E']);
mutant('legality without the distance rule', 'ambush', 'if ( too_close( org ) )\n\t\treturn false;', '', ['E']);
mutant('legality without the safe-zone field', 'ambush', 'if ( isdefined( level.tod_haven_inside_fn ) && [[ level.tod_haven_inside_fn ]]( org ) )\n\t\treturn false;', '', ['E']);
mutant('legality without the arena', 'ambush', 'if ( tod_arena_data::in_arena( org ) || tod_house_data::in_house( org ) || tod_house_data::in_parlour( org ) )\n\t\treturn false;', '', ['E']);
mutant('legality without the causeway gate', 'ambush', 'if ( !IS_TRUE( level.tod_gate_open ) && tod_crown_data::beyond_gate( org ) )\n\t\treturn false;', '', ['E']);
mutant('legality without the Fall seal', 'ambush', 'if ( IS_TRUE( level.tod_fall_sealed ) && !IS_TRUE( level.tod_fall_return_open ) && tod_crown_data::jumppad_enabled() && tod_crown_data::on_crown_island( org ) )\n\t\treturn false;', '', ['E']);
mutant('"behind" ignores who can see it', 'ambush', 'if ( dot <= TOD_AMBUSH_BEHIND_COS && !seen )', 'if ( dot <= TOD_AMBUSH_BEHIND_COS )', ['C', 'G2']);
mutant('a crawler can be the focus', 'ambush', 'if ( p laststand::player_is_in_laststand() )\n\t\t\tcontinue;', '', ['F']);
mutant('a resting player can be the focus', 'ambush', 'if ( isdefined( level.tod_haven_inside_fn ) && [[ level.tod_haven_inside_fn ]]( p.origin ) )\n\t\t\tcontinue;', '', ['F']);
mutant('the gap is ignored', 'ambush', 'if ( isdefined( p.tod_ambush_ms ) && ( now - p.tod_ambush_ms ) < TOD_AMBUSH_GAP_MS )\n\t\t\tcontinue;', '', ['F', 'G4']);
mutant('the gap is never stamped', 'ambush', 'focus.tod_ambush_ms = GetTime();', '', ['G4']);
mutant('zones are ignored', 'ambush', 'zone = spawn_zone( org );', 'zone = "lap12";', ['G6']);
mutant('the engine path check is ignored', 'ambush', 'if ( !( ai CanPath( org, goal ) ) )', 'if ( false )', ['G7']);
mutant('the probe budget is ignored', 'ambush', 'if ( probes >= TOD_AMBUSH_PROBES || zones >= TOD_AMBUSH_ZONE_TRIES )', 'if ( false )', ['G6', 'G7']);
mutant('the asked direction is not tried first', 'ambush', 'return array( "ahead", "flank", "behind" );', 'return array( "behind", "flank", "ahead" );', ['D', 'G1']);
mutant('the share never grows', 'ambush', 'pct = TOD_AMBUSH_PCT_FULL;', 'pct = TOD_AMBUSH_PCT_START;', ['A', 'G1']);
mutant('the spot is not a riser', 'ambush', 's.script_noteworthy = "riser_location";', 's.script_noteworthy = "spawn_location";', ['G1']);
mutant('a probe entity per lookup', 'ambush', 'if ( !isdefined( level.tod_ambush_probe ) )', 'if ( true )', ['G1']);
mutant('the guards are gone', 'ambush', 'if ( IS_TRUE( level.tod_arena_active ) || IS_TRUE( level.tod_upgrade_pause ) )', 'if ( false )', ['G8']);
mutant('the hook is not called', 'endless', 'ambush = self tod_ambush::pick( spots );', 'ambush = undefined;', ['H']);
mutant('the trickle back at map 1', 'endless', '#define TOD_SPAWN_MULT           0.70', '#define TOD_SPAWN_MULT           0.83', ['I']);
mutant('the floor back at map 1', 'endless', '#define TOD_SPAWN_FLOOR          0.20', '#define TOD_SPAWN_FLOOR          0.25', ['I']);
mutant('the round size not raised (rounds race)', 'endless', '#define TOD_ROUND_MAX_AI         28', '#define TOD_ROUND_MAX_AI         24', ['I']);
// the pre-2026-10-04 trickle (hotter than map 1 from round 1, no ramp) is the old behaviour, kept as a fixture
mutant('the ramp removed (the pre-2026-10-04 trickle)', 'endless', 'd = d * spawn_ramp_mult( n_round );', '', ['I']);
mutant('the ramp never ends', 'endless', '#define TOD_SPAWN_RAMP_FULL_ROUND 30', '#define TOD_SPAWN_RAMP_FULL_ROUND 300', ['I']);
if (process.argv.includes('--time')) console.log(`all: ${Date.now() - t0} ms`);

if (fails) { console.log(`AMBUSH GATE FAILED: ${fails} of ${checks} checks`); process.exit(1); }
console.log(`AMBUSH OK: ${checks} checks — share / direction / bucket / legality (real drops, crown, arena, havens) / focus / the pick end to end (${AD.TOD_AMBUSH_PCT_START}% -> ${AD.TOD_AMBUSH_PCT_FULL}% by round ${AD.TOD_AMBUSH_FULL_ROUND}, ahead ${AD.TOD_AMBUSH_AHEAD_PCT} / behind ${AD.TOD_AMBUSH_BEHIND_PCT}), the hook, the trickle vs map 1, lockstep with THE HUNT, wiring, ${mutants} negative controls caught.`);
console.log(`  measured: round-15 ambush share ${MEASURED.share} (ahead/behind/flank ${MEASURED.split}); zombies a second vs map 1 at least ${MEASURED.rate}; round length vs map 1 ${MEASURED.len}`);
