// test_spawn_ramp.js — THE RAMP (user 2026-10-04, the first real playthrough: "Zombies are
// spawning in way too fast too early. Too many too early. Game should ramp up. Even the max
// amount is the max max. Maybe early rounds should have a max - x until maybe round 30 where
// it actually allows the cap").
//
// Evaluates the ACTUAL GSC bodies (the test_rampage_levers.js recipe):
//   _tod_corpse_cleanup.gsc  ai_limit_for_party / ai_ramp_round / ai_ramp_frac / ai_limit_now
//   _tod_endless_rounds.gsc  spawn_ramp_mult
// and proves, for every party size, round 1..60, breaker off and on:
//   * the cap starts at about a third of the party cap and reaches ALL of it on round 30
//     (rampage: round 15), never above the party cap, never below TOD_AI_RAMP_MIN, and never
//     drops as the rounds climb;
//   * the trickle is TOD_SPAWN_RAMP_EARLY x slower on round 1 and x1.0 from the same round;
//   * the Battle Arena's fixed difficulty round drives the cap mid-fight;
//   * the cap's ONE WRITER (init + ai_limit_watch) writes ai_limit_now(), and the trickle
//     resolver multiplies by spawn_ramp_mult() BEFORE the floor;
//   * the round-1 preset is the resolver's own round-1 answer.
// Negative controls: each structural check is re-run on a mutated source and must fail.
//   node tools/test_spawn_ramp.js
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert/strict');
const root = path.join(__dirname, '..');
const read = f => fs.readFileSync(path.join(root, 'scripts/zm/zm_tod2_cybercity', f), 'utf8');
const corpse = read('_tod_corpse_cleanup.gsc'), rounds = read('_tod_endless_rounds.gsc');

function defines(src) {
  const out = {};
  for (const m of src.matchAll(/^#define\s+(\w+)\s+([-\d.]+)/gm)) out[m[1]] = Number(m[2]);
  return out;
}
function body(src, name) {
  const at = src.indexOf('function ' + name + '(');
  assert.ok(at >= 0, 'function ' + name + ' not found');
  const start = src.indexOf('{', at);
  let end = start + 1, depth = 1;
  while (depth) { if (src[end] === '{') depth++; if (src[end] === '}') depth--; end++; }
  return src.slice(start + 1, end - 1);
}
function params(src, name) {
  const m = src.match(new RegExp('function ' + name + '\\(([^)]*)\\)'));
  return m[1].split(',').map(s => s.trim()).filter(Boolean);
}
// GSC -> JS: strip comments, expand defines, `x.size` -> `x.length`, locals declared up front.
function toJs(src, name, D) {
  let b = body(src, name).replace(/\/\/.*$/gm, '');
  for (const [k, v] of Object.entries(D)) b = b.replace(new RegExp('\\b' + k + '\\b', 'g'), String(v));
  b = b.replace(/\.size\b/g, '.length');
  const ps = params(src, name);
  const locals = [...new Set([...b.matchAll(/^\s*(\w+)\s*=/gm)].map(m => m[1]))].filter(l => !ps.includes(l));
  return 'function ' + name + '(' + ps.join(', ') + ') {' + (locals.length ? ' let ' + locals.join(',') + ';' : '') + b + '}';
}

const D = Object.assign({}, defines(corpse), defines(rounds));
for (const k of ['TOD_AI_RAMP_START_FRAC', 'TOD_AI_RAMP_FULL_ROUND', 'TOD_RAMPAGE_AI_RAMP_FULL_ROUND', 'TOD_AI_RAMP_MIN',
                 'TOD_SPAWN_RAMP_EARLY', 'TOD_SPAWN_RAMP_FULL_ROUND', 'TOD_RAMPAGE_SPAWN_RAMP_FULL_ROUND', 'TOD_FALL_SPAWN_MULT'])
  assert.ok(Number.isFinite(D[k]), k + ' define missing');

// LOCKSTEP: the cap and the trickle ramp on the same rounds.
assert.equal(D.TOD_AI_RAMP_FULL_ROUND, D.TOD_SPAWN_RAMP_FULL_ROUND, 'LOCKSTEP: the cap and the trickle reach full on the same round');
assert.equal(D.TOD_RAMPAGE_AI_RAMP_FULL_ROUND, D.TOD_RAMPAGE_SPAWN_RAMP_FULL_ROUND, 'LOCKSTEP: rampage ramps both on the same round');
assert.ok(D.TOD_RAMPAGE_AI_RAMP_FULL_ROUND < D.TOD_AI_RAMP_FULL_ROUND, 'rampage (the hard mode) must reach the full cap SOONER');
assert.ok(D.TOD_AI_RAMP_START_FRAC > 0 && D.TOD_AI_RAMP_START_FRAC < 1, 'the ramp must start below the party cap');
assert.ok(D.TOD_SPAWN_RAMP_EARLY > 1, 'the early trickle must be SLOWER (a delay multiplier above 1)');

const ctx = { level: {}, players: [], IS_TRUE: x => x === true, isdefined: x => x !== undefined, int: x => Math.trunc(x) };
ctx.GetPlayers = () => ctx.players;
vm.createContext(ctx);
for (const f of ['ai_limit_for_party', 'ai_ramp_round', 'ai_ramp_frac', 'ai_limit_now']) vm.runInContext(toJs(corpse, f, D), ctx);
vm.runInContext(toJs(rounds, 'spawn_ramp_mult', D), ctx);

let checks = 0;
const party = [36, 42, 48, 54], partyRampage = [46, 52, 58, 58];
for (const on of [false, true]) {
  ctx.level = { tod_rampage_on: on };
  const full = on ? D.TOD_RAMPAGE_AI_RAMP_FULL_ROUND : D.TOD_AI_RAMP_FULL_ROUND;
  for (let np = 1; np <= 4; np++) {
    ctx.players = Array(np).fill({});
    const cap = (on ? partyRampage : party)[np - 1];
    assert.equal(ctx.ai_limit_for_party(), cap, `party cap np=${np} on=${on} (test_rampage_levers.js owns these)`);
    let prev = -1;
    for (let r = 1; r <= 60; r++) {
      ctx.level.round_number = r;
      const n = ctx.ai_limit_now();
      assert.ok(n <= cap, `r${r} np=${np} on=${on}: ${n} over the party cap ${cap}`);
      assert.ok(n >= D.TOD_AI_RAMP_MIN, `r${r}: under the floor`);
      assert.ok(n >= prev, `r${r} np=${np} on=${on}: the cap dropped ${prev} -> ${n}`);
      if (r >= full) assert.equal(n, cap, `r${r} np=${np} on=${on}: the whole cap from round ${full}`);
      if (r === 1) assert.equal(n, Math.max(D.TOD_AI_RAMP_MIN, Math.round(cap * D.TOD_AI_RAMP_START_FRAC)), `round 1 np=${np} on=${on}`);
      prev = n; checks += 3;
      const m = ctx.spawn_ramp_mult(r);
      if (r <= 1) assert.ok(Math.abs(m - D.TOD_SPAWN_RAMP_EARLY) < 1e-9, 'trickle round 1');
      if (r >= full) assert.equal(m, 1.0, `trickle r${r} on=${on}: x1.0 from round ${full}`);
      assert.ok(m >= 1.0 && m <= D.TOD_SPAWN_RAMP_EARLY + 1e-9, `trickle r${r} in range`);
      if (r > 1) assert.ok(m <= ctx.spawn_ramp_mult(r - 1) + 1e-9, `trickle r${r}: slower than the round before`);
      checks += 2;
    }
  }
}
// solo, breaker off: the numbers players feel (round 1 / 10 / 20 / 30)
ctx.level = {}; ctx.players = [{}];
const solo = [1, 10, 20, 30].map(r => { ctx.level.round_number = r; return ctx.ai_limit_now(); });
assert.deepEqual(solo, [12, 19, 28, 36], 'solo caps at rounds 1/10/20/30');
// the Battle Arena's fixed difficulty round drives the ramp mid-fight, and only mid-fight
ctx.level = { round_number: 3, tod_arena_hp_round: 30 };
assert.equal(ctx.ai_limit_now(), 36, 'the arena fights at its own round');
delete ctx.level.tod_arena_hp_round;
assert.equal(ctx.ai_limit_now(), 14, 'back in the tower, the tower round (solo round 3)');
// a 0-player frame never returns under the floor
ctx.players = []; ctx.level = { round_number: 1 };
assert.ok(ctx.ai_limit_now() >= D.TOD_AI_RAMP_MIN, 'a 0-player frame keeps the floor');
checks += 4;

// STRUCTURE (with negative controls): the one writer writes ai_limit_now(); the resolver ramps
// before the floor; the round-1 preset carries the ramp and the crown factor.
function structure(cs, rs) {
  const bad = [];
  if (!/level\.zombie_ai_limit\s*=\s*ai_limit_now\(\s*\)/.test(body(cs, 'init'))) bad.push('init must write ai_limit_now()');
  if (!/lim\s*=\s*ai_limit_now\(\s*\)/.test(body(cs, 'ai_limit_watch'))) bad.push('ai_limit_watch must read ai_limit_now()');
  if ((cs.match(/level\.zombie_ai_limit\s*=/g) || []).length !== 2) bad.push('level.zombie_ai_limit has exactly two writes (init + the watch)');
  const sd = body(rs, 'tod_spawn_delay');
  const ramp = sd.indexOf('spawn_ramp_mult( n_round )'), floor = sd.indexOf('if ( d < fl )');
  if (ramp < 0 || floor < 0 || ramp > floor) bad.push('tod_spawn_delay must apply spawn_ramp_mult before the floor');
  if (!/zombie_spawn_delay" \] = 2\.0 \* TOD_SPAWN_MULT \* TOD_SPAWN_RAMP_EARLY \* TOD_FALL_SPAWN_MULT;/.test(rs)) bad.push('the round-1 preset must carry the ramp and the crown factor');
  return bad;
}
const live = structure(corpse, rounds);
assert.deepEqual(live, [], 'structure: ' + live.join('; '));
const mutants = [
  ['init writes the party cap', corpse.replace('level.zombie_ai_limit    = ai_limit_now();', 'level.zombie_ai_limit    = ai_limit_for_party();'), rounds],
  ['the watch reads the party cap', corpse.replace('lim = ai_limit_now();', 'lim = ai_limit_for_party();'), rounds],
  ['the resolver skips the ramp', corpse, rounds.replace('d = d * spawn_ramp_mult( n_round );', '')],
  ['the round-1 preset skips the ramp', corpse, rounds.replace('2.0 * TOD_SPAWN_MULT * TOD_SPAWN_RAMP_EARLY * TOD_FALL_SPAWN_MULT;', '2.0 * TOD_SPAWN_MULT;')],
];
for (const [what, cs, rs] of mutants) {
  assert.notEqual(cs + rs, corpse + rounds, `mutant "${what}" did not change the source (stale anchor)`);
  assert.ok(structure(cs, rs).length > 0, `negative control missed: ${what}`);
}
console.log(`SPAWN RAMP OK ${checks} checks, ${mutants.length} mutants caught; solo cap r1/r10/r20/r30 = ${solo.join('/')}, trickle x${D.TOD_SPAWN_RAMP_EARLY} -> x1.0 by round ${D.TOD_SPAWN_RAMP_FULL_ROUND} (rampage ${D.TOD_RAMPAGE_SPAWN_RAMP_FULL_ROUND})`);
