#!/usr/bin/env node
'use strict';
// =============================================================================
// test_wunderstrahl.js - THE WUNDERSTRAHL gate (docs/219, 2026-10-05).
//
// User: "a really super strong laser gun ... an automatic laser. So you can hold it down".
// Chosen: it shares the Gift of Death's drop 50/50, no overheat, a yellow core.
//
// Reads the SHIPPING sources; the pure functions of _tod_wunderstrahl.gsc run verbatim through
// tools/sky_ships/gsc_eval.js (never a copy):
//   A. THE SHARED SLOT   drop_gate: refused while a power-up gun is out / before the power,
//                        TOD_WS_DROP_PCT of the rolls otherwise; LOCKSTEP with _tod_powerups'
//                        TOD_MINIGUN_DROP_PCT (the two halves sum to the slot's old 50), and the
//                        Death Machine's gate refuses while anyone holds this gun.
//   B. THE WINDOW        paused_for (a card deal / a menu / a spin stops the clock), beam_lane (IsFiring
//                        first; the trigger only after IsFiring never reported and the gun has been
//                        up TOD_WS_FALLBACK_TICKS).
//   C. THE DAMAGE        victim_kind, ticks_for / tick_damage_for (a horde zombie dies in exactly
//                        TOD_WS_HORDE_TICKS ticks from full on ANY round; elites / the Dealer by their
//                        counts; rampage stretches every count by its HP levers; Insta-Kill speeds the
//                        horde only), seg_seg_dist2 against a brute-force reference on random segments,
//                        beam_touches (in front only, stops at the wall, the per-kind radius).
//   D. LOCKSTEP          the beam's range (make_fx.py BEAM_RANGE) = TOD_WS_RANGE; the weapon / model
//                        names in install.py = the GSC's; the precached effects are zoned.
//   E. WIRING            (repo mode) the entry scripts arm the module, the zone includes its package,
//                        the client half adds the same clientfield, the tray row, the power-scale
//                        exemption, the guards that read the gun's var, the sync lines, the szc row.
// Every rule in A-C has a NEGATIVE CONTROL: the clause is cut from a copy and the table must fail.
//
//   node tools/wunderstrahl/test_wunderstrahl.js                 the repo (the build gate)
//   node tools/wunderstrahl/test_wunderstrahl.js --root DIR      an overlay (a stage): DIR first, the repo behind it;
//                                                                E reports PENDING for files not yet wired
// =============================================================================
const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const { gscLoad } = require('../sky_ships/gsc_eval.js');

const argv = process.argv.slice(2);
const ri = argv.indexOf('--root');
const OVER = ri >= 0 ? path.resolve(argv[ri + 1]) : null;
const STAGE = !!OVER;

function readOpt(rel) {
  for (const base of (OVER ? [OVER, ROOT] : [ROOT])) {
    const p = path.join(base, rel);
    if (fs.existsSync(p)) return fs.readFileSync(p, 'utf8').replace(/\r\n/g, '\n');
  }
  return null;
}
function read(rel) {
  const t = readOpt(rel);
  if (t === null) { console.log('  FAIL ' + rel + ' is missing'); process.exit(1); }
  return t;
}

let passes = 0, fails = 0, pending = 0;
function check(ok, good, bad) {
  if (ok) { passes++; console.log('  ok   ' + good); }
  else { fails++; console.log('  FAIL ' + (bad || good)); }
}
function wired(ok, good, bad) {          // a wiring claim: PENDING (not a failure) in stage mode
  if (ok) { passes++; console.log('  ok   ' + good); }
  else if (STAGE) { pending++; console.log('  PEND ' + (bad || good)); }
  else { fails++; console.log('  FAIL ' + (bad || good)); }
}
function section(t) { console.log('\n' + t); }

const GSC_REL = 'scripts/zm/zm_tod2_cybercity/_tod_wunderstrahl.gsc';
const CSC_REL = 'scripts/zm/zm_tod2_cybercity/_tod_wunderstrahl.csc';
const WS = read(GSC_REL);

function defs(text) {
  const out = {};
  for (const m of text.matchAll(/^#define\s+(\w+)\s+\(?\s*(-?[\d.]+)\s*\)?\s*(?:\/\/.*)?$/gm)) out[m[1]] = Number(m[2]);
  return out;
}
function sdefs(text) {
  const out = {};
  for (const m of text.matchAll(/^#define\s+(\w+)\s+"([^"]*)"/gm)) out[m[1]] = m[2];
  return out;
}
const D = defs(WS);
const S = sdefs(WS);
const IS_TRUE = x => x !== undefined && x !== null && !!x;
function load(text) { return gscLoad([['tod_wunderstrahl', text]], D, { builtins: { IS_TRUE } }); }
function fnBody(text, name) {
  const re = new RegExp('\\bfunction\\s+' + name + '\\s*\\([^)]*\\)\\s*(?:\\/\\/[^\\n]*\\s*)?\\{');
  const m = re.exec(text);
  if (!m) return null;
  let depth = 1, j = m.index + m[0].length;
  while (depth && j < text.length) { if (text[j] === '{') depth++; else if (text[j] === '}') depth--; j++; }
  return text.slice(m.index, j);
}
// a copy of the module with one line of one function removed (a negative control)
function cut(text, fn, needle) {
  const body = fnBody(text, fn);
  if (!body || body.indexOf(needle) < 0) throw new Error('negative control: ' + fn + ' has no ' + needle);
  return text.replace(body, body.replace(needle, ''));
}
const g = load(WS);
const V = (x, y, z) => { const v = [x, y, z]; v.isVec = true; return v; };

// =============================================================================
section('A. THE SHARED SLOT');
function dropTable(m) {
  let ok = true;
  for (let roll = 0; roll < 100; roll++) {
    if (m.call('drop_gate', [true, roll]) !== false) ok = false;                         // blocked: never
    if (m.call('drop_gate', [false, roll]) !== (roll < D.TOD_WS_DROP_PCT)) ok = false;   // free: the share
  }
  return ok;
}
check(dropTable(g), `drop_gate: refused while blocked, ${D.TOD_WS_DROP_PCT}% of the rolls otherwise`, 'drop_gate does not follow the slot rule');
check(!dropTable(load(cut(WS, 'drop_gate', 'if ( IS_TRUE( blocked ) ) return false;'))), 'negative control: a gate that forgets the block is caught', 'the table misses a gate without its block');
const PU = readOpt('scripts/zm/zm_tod2_cybercity/_tod_powerups.gsc') || '';
const minigunPct = (PU.match(/^#define\s+TOD_MINIGUN_DROP_PCT\s+(\d+)/m) || [])[1];
wired(Number(minigunPct) === D.TOD_WS_DROP_PCT && Number(minigunPct) + D.TOD_WS_DROP_PCT === 50,
  `the slot is shared 50/50: Death Machine ${minigunPct} + Wunderstrahl ${D.TOD_WS_DROP_PCT} = the old 50`,
  `TOD_MINIGUN_DROP_PCT is ${minigunPct}: the two halves must be equal and sum to 50`);
const minGate = fnBody(PU, 'tod_should_drop_minigun') || '';
wired(/zombie_powerup_tod_wunderstrahl_on/.test(minGate), 'the Death Machine\'s gate refuses while anyone holds the Wunderstrahl', 'tod_should_drop_minigun ignores a held Wunderstrahl (two big guns at once)');
const shouldDrop = fnBody(WS, 'should_drop') || '';
check(/zm_powerups::minigun_no_drop\(\)/.test(shouldDrop) && /anyone_holds\(\)/.test(shouldDrop),
  'should_drop carries stock\'s minigun rules (no gun out, the power / solo rule) and refuses while this gun is out', 'should_drop lost a stock rule');

// =============================================================================
section('B. THE WINDOW');
{
  let ok = true;
  for (const w of [false, true]) for (const m of [false, true]) for (const s of [false, true])
    if (g.call('paused_for', [w, m, s]) !== (w || m || s)) ok = false;
  check(ok, 'paused_for: a card deal, a menu or a spin stops the clock; nothing else does', 'paused_for is wrong');
  check(g.call('paused_for', [undefined, undefined, undefined]) === false, 'paused_for: undefined flags run the clock', 'paused_for stops on undefined');
}
function laneTable(m) {
  const F = D.TOD_WS_FALLBACK_TICKS;
  const cases = [
    [[false, true, true, false, 99], ''],              // the gun is not up: nothing
    [[true, true, false, false, 0], 'isfiring'],        // the engine says firing
    [[true, true, true, true, 0], 'isfiring'],
    [[true, false, true, false, F - 1], ''],            // the trigger, not yet long enough
    [[true, false, true, false, F], 'attack'],          // the fallback
    [[true, false, true, true, F + 9], ''],             // IsFiring has reported this window: never the fallback
    [[true, false, false, false, F + 9], ''],           // no trigger
  ];
  return cases.every(([a, want]) => m.call('beam_lane', a) === want);
}
check(laneTable(g), `beam_lane: IsFiring first; the trigger only after ${D.TOD_WS_FALLBACK_TICKS} ticks and only if IsFiring never reported`, 'beam_lane is wrong');
check(!laneTable(load(cut(WS, 'beam_lane', '&& !IS_TRUE( seen_isfiring )'))), 'negative control: a fallback that ignores a working IsFiring is caught', 'the table misses the seen_isfiring guard');
const loop = fnBody(WS, 'beam_loop') || '';
check(/tod_upgrade_pause/.test(loop) && /tod_jumppad_flying/.test(loop) && /player_is_in_laststand/.test(loop),
  'no beam damage while the world is paused, the holder flies (a jump-pad flyer is untouchable) or is down', 'beam_loop misses a refusal');
const cd = fnBody(WS, 'countdown') || '';
check(/_show_solo_hud = true/.test(cd) && /paused_for\(/.test(cd), 'the countdown re-asserts the tray gate each frame and stands still when frozen', 'countdown lost the keep-alive or the pause');
check(/level\._zombie_tesla_powerup_last_stand_func = &last_stand;/.test(WS) && /weapon_watch_gunner_downed\( TOD_WS_POWERUP \)/.test(fnBody(WS, 'last_stand') || ''),
  'going down takes the gun through stock\'s spare Wunderwaffe last-stand hook', 'the last-stand take is not wired');
check(/powerup_set_prevent_pick_up_if_drinking\( TOD_WS_POWERUP, true \)/.test(WS) && /powerup_set_statless_powerup\( TOD_WS_POWERUP \)/.test(WS),
  'the drop is refused mid-drink (the Death Machine\'s rule) and statless (no pers stat for a custom name)', 'a stock power-up setter is missing');
{
  const init = fnBody(WS, '__init__') || '';
  const add = init.indexOf('add_zombie_powerup(');
  const lastStandSetter = init.indexOf('powerup_set_can_pick_up_in_last_stand(');
  check(add > 0 && lastStandSetter > add, 'the level.zombie_powerups setter runs AFTER add_zombie_powerup (its struct exists only then)', 'a level.zombie_powerups setter runs before the add (a load crash)');
}

// =============================================================================
section('C. THE DAMAGE');
check(g.call('victim_kind', ['dealer', 'keeper', true]) === 'boss'
   && g.call('victim_kind', ['doppelghast', 'zombie', true]) === 'elite'
   && g.call('victim_kind', ['mangler', undefined, false]) === 'elite'
   && g.call('victim_kind', [undefined, 'raz', false]) === 'elite'
   && g.call('victim_kind', [undefined, 'zombie', true]) === 'elite'
   && g.call('victim_kind', [undefined, 'zombie', false]) === 'horde'
   && g.call('victim_kind', [undefined, undefined, false]) === 'horde',
  'victim_kind: the Dealer is the boss; any boss kind, boss flag or non-zombie archetype is an elite; the rest is horde', 'victim_kind sorts wrong');
function ticksToKill(m, hp, kind, rampage, hm, em, dm) {
  let h = hp, n = 0;
  while (h > 0 && n < 100000) { h -= m.call('tick_damage_for', [hp, kind, rampage, hm, em, dm]); n++; }
  return n;
}
function dmgTable(m) {
  let ok = true;
  for (const hp of [14, 45, 135, 482, 1717, 6000, 23411]) {                  // early rounds to deep rounds (new units)
    if (ticksToKill(m, hp, 'horde', false, 1.2, 1.5, 1) !== D.TOD_WS_HORDE_TICKS) ok = false;
    if (ticksToKill(m, hp * 4, 'elite', false, 1.2, 1.5, 1) > D.TOD_WS_ELITE_TICKS) ok = false;
    if (ticksToKill(m, hp, 'horde', false, 1.2, 1.5, 3) !== 1) ok = false;  // Insta-Kill's 3x: one tick
  }
  return ok;
}
check(dmgTable(g), `a horde zombie dies in exactly ${D.TOD_WS_HORDE_TICKS} contact ticks (${(D.TOD_WS_HORDE_TICKS * D.TOD_WS_TICK).toFixed(1)} s) on any round, elites in at most ${D.TOD_WS_ELITE_TICKS}, Insta-Kill makes it one`,
  'the tick damage does not hold its round-independent kill counts');
check(!dmgTable(load(cut(WS, 'tick_damage_for', '+ 1'))), 'negative control: a tick without its +1 (an extra tick to kill) is caught', 'the table misses the +1');
{
  const rampHorde = ticksToKill(g, 1717, 'horde', true, 1.2, 1.5, 1);
  const rampElite = ticksToKill(g, 6868, 'elite', true, 1.2, 1.5, 1);
  check(rampHorde > D.TOD_WS_HORDE_TICKS && rampElite > D.TOD_WS_ELITE_TICKS,
    `rampage (the hard mode) stretches the laser too: horde ${rampHorde} ticks, elites ${rampElite}`, 'rampage does not slow the laser (CLAUDE.md: every easing knob keeps a rampage branch)');
  check(ticksToKill(g, 1717, 'elite', false, 1.2, 1.5, 3) === ticksToKill(g, 1717, 'elite', false, 1.2, 1.5, 1),
    'Insta-Kill does not speed elites (their numbers are fixed, as for every elite)', 'Insta-Kill multiplies elite ticks');
  const bossTicks = ticksToKill(g, 30000, 'boss', false, 1.2, 1.5, 1);
  const windowTicks = Math.round(D.TOD_WS_SECS / D.TOD_WS_TICK);
  check(windowTicks / bossTicks <= 0.11, `a whole window held on the Dealer takes ${(100 * windowTicks / bossTicks).toFixed(1)}% of him (cap 11%)`, 'the Dealer melts under one window');
}
// seg_seg_dist2 against a brute-force reference
function bruteDist2(p1, q1, p2, q2) {
  let best = Infinity;
  const N = 400;
  for (let i = 0; i <= N; i++) {
    const s = i / N, a = [p1[0] + (q1[0] - p1[0]) * s, p1[1] + (q1[1] - p1[1]) * s, p1[2] + (q1[2] - p1[2]) * s];
    // the exact closest point on segment 2 to a (clamped projection)
    const d = [q2[0] - p2[0], q2[1] - p2[1], q2[2] - p2[2]];
    const dd = d[0] * d[0] + d[1] * d[1] + d[2] * d[2];
    let t = dd > 1e-9 ? ((a[0] - p2[0]) * d[0] + (a[1] - p2[1]) * d[1] + (a[2] - p2[2]) * d[2]) / dd : 0;
    t = Math.max(0, Math.min(1, t));
    const b = [p2[0] + d[0] * t, p2[1] + d[1] * t, p2[2] + d[2] * t];
    const e = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2;
    if (e < best) best = e;
  }
  return best;
}
{
  let seed = 7;
  const rnd = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
  const R = () => V((rnd() - 0.5) * 400, (rnd() - 0.5) * 400, (rnd() - 0.5) * 200);
  let worst = 0, n = 0;
  for (; n < 400; n++) {
    const p1 = R(), q1 = (n % 13 === 0) ? p1 : R(), p2 = R(), q2 = (n % 17 === 0) ? p2 : R();
    const got = Math.sqrt(g.call('seg_seg_dist2', [p1, q1, p2, q2])), want = Math.sqrt(bruteDist2(p1, q1, p2, q2));
    worst = Math.max(worst, got - want);   // the exact answer can only be <= the sampled one
    if (got < want - 1.5) worst = Math.max(worst, 99);
  }
  const par = Math.sqrt(g.call('seg_seg_dist2', [V(0, 0, 0), V(100, 0, 0), V(0, 10, 0), V(100, 10, 0)]));
  check(worst < 0.6 && Math.abs(par - 10) < 1e-6, `seg_seg_dist2 matches a brute-force reference on ${n} random pairs (worst +${worst.toFixed(3)} u) and on parallel segments`,
    `seg_seg_dist2 is off by ${worst.toFixed(3)} u (parallel case ${par})`);
}
function touchTable(m) {
  const eye = V(0, 0, 60), stop = V(1000, 0, 60), fwd = V(1, 0, 0);
  const body = (x, y) => [V(x, y, 6), V(x, y, 6 + 64)];
  const c = [
    [body(300, 10), 16, true],      // on the line
    [body(300, 15.9), 16, true],    // at the edge
    [body(300, 30), 16, false],     // beside it
    [body(1100, 0), 16, false],     // past the wall
    [body(-60, 0), 16, false],      // behind the eye
    [body(-8, 0), 16, false],       // just behind the eye, within the radius of it: only the in-front rule refuses it
    [body(300, 25), 26, true],      // an elite's wider reach
  ];
  return c.every(([b, r, want]) => m.call('beam_touches', [eye, stop, fwd, b[0], b[1], r]) === want);
}
check(touchTable(g), 'beam_touches: on the line and within the radius, in front of the eye, short of the wall', 'beam_touches is wrong');
check(!touchTable(load(cut(WS, 'beam_touches', 'if ( ahead <= 0 ) return false;'))), 'negative control: a beam that also burns behind the holder is caught', 'the table misses the in-front rule');
check(/exempt|power scale/i.test(WS) && /tod_dmg_mult/.test(fnBody(WS, 'hit') || ''), 'the tick reads the Insta-Kill multiplier', 'hit() ignores the Insta-Kill window');
{
  // THE KILL BURSTS: lit first, then unlit, then the sound alone (a twenty-kill line must not raise twenty lights)
  const L = D.TOD_WS_KILL_LIT_PER_SEC, N = D.TOD_WS_KILL_NL_PER_SEC;
  function pickTable(m) {
    let lit = 0, nl = 0, none = 0;
    for (let k = 0; k < 40; k++) {
      const p = m.call('kill_fx_pick', [lit, nl]);
      if (p === 'lit') lit++; else if (p === 'nl') nl++; else none++;
    }
    return lit === L && nl === N && none === 40 - L - N && m.call('kill_fx_pick', [undefined, undefined]) === 'lit';
  }
  check(pickTable(g), `a kill streak bursts lit ${L} a second, then unlit ${N}, then sound only`, 'kill_fx_pick does not bound the bursts');
  check(!pickTable(load(cut(WS, 'kill_fx_pick', 'if ( nl_n < TOD_WS_KILL_NL_PER_SEC ) return "nl";'))), 'negative control: a budget with no unlit tier is caught', 'the table misses the unlit tier');
  const host = fnBody(WS, 'fx_host_run') || '';
  check(D.TOD_WS_FX_HOST_WAIT >= 0.1 && /wait TOD_WS_FX_HOST_WAIT;\s*PlayFXOnTag\( fx, self, "tag_origin" \);/.test(host) && /self Delete\(\);/.test(host)
     && !/tod_ability_fx|burst_at\(/.test(WS.replace(/\/\/[^\n]*/g, '')) && /#precache\( "model", "tag_origin" \)/.test(WS),
    `the kill / burn effects ride their own tag_origin carrier: ${D.TOD_WS_FX_HOST_WAIT * 1000} ms to replicate, PlayFXOnTag, then the host deletes itself`,
    'fx_host_run plays before two frames, never deletes its host, or the module still reaches for another lane');
  const zfx = [...WS.matchAll(/#precache\(\s*"fx",\s*"([^"]+)"\s*\)/g)].map(m => m[1]);
  check(['TOD_WS_FX_DIE', 'TOD_WS_FX_DIE_NL', 'TOD_WS_FX_BURN'].every(k => zfx.includes(S[k])), 'every effect the module plays is precached', 'a played effect is not precached');
}
{
  const cb = fnBody(WS, 'beam_damage_cb') || '';
  const init = fnBody(WS, '__init__') || '';
  check(/zm::register_actor_damage_callback\( &beam_damage_cb \);/.test(init) && /#using scripts\\zm\\_zm;/.test(WS),
    'the beam answers the actor-damage chain (a system __init__: ahead of upgrade_damage_cb)', 'beam_damage_cb is not registered');
  check(/weapon != level\.tod_ws_weapon \) return -1;/.test(cb) && /!= "horde" \) return -1;/.test(cb) && /tod_upgrade_pause \) \) return 0;/.test(cb) && /return damage;/.test(cb),
    'the callback passes a horde tick unchanged, leaves elites / the Dealer / other weapons to the chain, and deals nothing while the world is frozen',
    'beam_damage_cb lost a clause (a card would multiply the tick twice, or an elite\'s own lane would be skipped)');
}
{
  const at = ms => g.call('reach_at', [ms]);
  const sp = D.TOD_WS_LAUNCH_SPEED, rg = D.TOD_WS_RANGE, tk = D.TOD_WS_TICK * 1000;
  const ok = Math.abs(at(0) - sp * tk / 1000) < 1e-6 && Math.abs(at(100) - sp * (100 + tk) / 1000) < 1e-6
    && at(100000) === rg && at(-50) === at(0) && at(undefined) === at(0) && at(0) > 0;
  check(ok, `the reach grows at the beam's launch speed (${sp} u/s: ${Math.round(at(0))} u on the first tick, the full ${rg} u by ${Math.round(1000 * rg / sp - tk)} ms)`,
    'reach_at does not follow the launch speed / range');
  check(/beam_tick\( reach_at\( GetTime\(\) - t0 \) \)/.test(fnBody(WS, 'beam_loop') || '') && /far = eye \+ fwd \* reach;/.test(fnBody(WS, 'beam_tick') || ''),
    'the tick traces only as far as the beam has reached', 'beam_tick ignores the growing reach');
}

// =============================================================================
section('D. LOCKSTEP');
const FXGEN = readOpt('tools/wunderstrahl/fx/make_fx.py');
const range = FXGEN ? Number((FXGEN.match(/^BEAM_RANGE\s*=\s*(\d+)/m) || [])[1]) : NaN;
wired(range === D.TOD_WS_RANGE, `the beam reaches as far as the damage: BEAM_RANGE ${range} = TOD_WS_RANGE ${D.TOD_WS_RANGE}`, `BEAM_RANGE ${range} != TOD_WS_RANGE ${D.TOD_WS_RANGE}`);
const launch = FXGEN ? Number((FXGEN.match(/^BEAM_LAUNCH_SPEED\s*=\s*(\d+)/m) || [])[1]) : NaN;
wired(launch === D.TOD_WS_LAUNCH_SPEED, `the damage reach grows as fast as the beam shoots out: BEAM_LAUNCH_SPEED ${launch} = TOD_WS_LAUNCH_SPEED ${D.TOD_WS_LAUNCH_SPEED}`,
  `BEAM_LAUNCH_SPEED ${launch} != TOD_WS_LAUNCH_SPEED ${D.TOD_WS_LAUNCH_SPEED}`);
const INST = read('tools/wunderstrahl/install.py');
check((INST.match(/^WEAPON = '([^']+)'/m) || [])[1] === S.TOD_WS_WEAPON && (INST.match(/^PICKUP = '([^']+)'/m) || [])[1] === S.TOD_WS_PICKUP_MODEL,
  `install.py names the weapon ${S.TOD_WS_WEAPON} and the pickup ${S.TOD_WS_PICKUP_MODEL}, like the GSC`, 'install.py and the GSC disagree on a name');
const ZPKG = readOpt('zone_source/tod2_wunderstrahl.zpkg') || '';
for (const fx of [...WS.matchAll(/#precache\(\s*"fx",\s*"([^"]+)"\s*\)/g)].map(m => m[1]))
  wired(ZPKG.split('\n').includes('fx,' + fx), `the zone carries ${fx} (precached by the module)`, `${fx} is precached but not zoned`);
wired(ZPKG.split('\n').includes('weapon,' + S.TOD_WS_WEAPON) && ZPKG.split('\n').includes('xmodel,' + S.TOD_WS_PICKUP_MODEL),
  'the zone carries the weapon and the pickup model', 'the zone package lacks the weapon or the pickup model');

// =============================================================================
section('E. WIRING');
const CSC = readOpt(CSC_REL) || '';
check(/include_zombie_powerup\( "tod_wunderstrahl" \)/.test(CSC) && /add_zombie_powerup\( "tod_wunderstrahl", "tod_wunderstrahl" \)/.test(CSC)
   && S.TOD_WS_POWERUP === 'tod_wunderstrahl' && /add_zombie_powerup\( TOD_WS_POWERUP, TOD_WS_PICKUP_MODEL, [^;]*TOD_WS_POWERUP, TOD_WS_VAR_TIME, TOD_WS_VAR_ON \)/.test(WS),
  'the client includes + adds the power-up with the server\'s clientfield name', 'the clientfield halves disagree (a load-time mismatch)');
const MAINGSC = readOpt('scripts/zm/zm_tod2_cybercity.gsc') || '';
const MAINCSC = readOpt('scripts/zm/zm_tod2_cybercity.csc') || '';
wired(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_wunderstrahl;/.test(MAINGSC) && /#using scripts\\zm\\zm_tod2_cybercity\\_tod_wunderstrahl;/.test(MAINCSC),
  'both entry scripts #using the module (REGISTER_SYSTEM self-init)', 'an entry script does not arm the module');
const ZONE = readOpt('zone_source/zm_tod2_cybercity.zone') || '';
wired(/^include,tod2_wunderstrahl$/m.test(ZONE), 'the main zone includes tod2_wunderstrahl', 'the main zone does not include the package');
const TRAY = readOpt('ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumPowerupsContainer.lua') || '';
wired(/clientFieldName = "tod_wunderstrahl",\s*name = "Wunderstrahl",\s*image = "i_tod_pu2_wunderstrahl"/.test(TRAY), 'the tray has a Wunderstrahl row on the same clientfield', 'no tray row for tod_wunderstrahl');
const LOAD = readOpt('ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumLoadout.lua') || '';
wired(/\[ "tod2_wunderstrahl" \]\s*=\s*"wunderstrahl"/.test(LOAD), 'the gun bay draws the Wunderstrahl\'s own picture', 'no TOD_GUN_CAT row for tod2_wunderstrahl');
const PS = readOpt('scripts/zm/zm_tod2_cybercity/_tod_power_scale.gsc') || '';
wired(/IsSubStr\( weapon\.name, "wunderstrahl" \)/.test(fnBody(PS, 'exempt_reason') || ''), 'the power scale exempts the beam (its numbers are already a tenth)', 'the power scale would divide the beam a second time');
for (const [rel, fn] of [['scripts/zm/zm_tod2_cybercity/_tod_powerups.gsc', 'grab_pap'], ['scripts/zm/zm_tod2_cybercity/_tod_powerups.gsc', 'zombie_blood_clear'],
                         ['scripts/zm/zm_tod2_cybercity/_tod_class_terminal.gsc', null], ['scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc', null]]) {
  const t = readOpt(rel) || '';
  const scope = fn ? (fnBody(t, fn) || '') : t;
  const minigun = (scope.match(/zombie_powerup_minigun_on/g) || []).length;
  const ws = (scope.match(/zombie_powerup_tod_wunderstrahl_on/g) || []).length;
  wired(minigun > 0 && ws >= minigun, `${path.basename(rel)}${fn ? '::' + fn : ''}: every Gift of Death guard reads the Wunderstrahl too (${ws}/${minigun})`,
    `${path.basename(rel)}${fn ? '::' + fn : ''}: ${minigun} Gift of Death guard(s), ${ws} read the Wunderstrahl`);
}
const SYNC = readOpt('tools/sync_to_modtools.ps1') || '';
for (const d of ['model_export\\tod_wunderstrahl', 'model_export\\tod_wunderstrahl_fx', 'xanim_export\\tod_wunderstrahl'])
  wired(SYNC.includes('"' + d + '"'), `the sync carries ${d}`, `sync_to_modtools.ps1 does not copy ${d}`);
const SZC = readOpt('sound/zoneconfig/zm_tod2_cybercity.szc') || '';
wired(/"Filename": "tod_wunderstrahl\.csv"/.test(SZC), 'the sound zone loads tod_wunderstrahl.csv', 'the szc has no tod_wunderstrahl.csv entry');
const BUILD = readOpt('tools/build_map.ps1') || '';
wired(/test_wunderstrahl\.js/.test(BUILD) && /wunderstrahl[\\/]install\.py/.test(BUILD), 'build_map.ps1 runs this gate and the installer check', 'build_map.ps1 does not gate the Wunderstrahl');

console.log(`\n${fails ? 'FAIL' : 'OK'}: ${passes} passed, ${fails} failed${pending ? ', ' + pending + ' pending (stage mode)' : ''}`);
process.exit(fails ? 1 : 0);
