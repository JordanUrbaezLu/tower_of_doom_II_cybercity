// tools/test_hot_streak.js - THE HOT STREAK + THE REACH (docs/201, 2026-10-02): runs the SHIPPING GSC, translated,
// and proves what the player is promised.
//   node tools/test_hot_streak.js
//
// THE HOT STREAK (_tod_luck.gsc): every transition of streak_result / streak_end (EPIC +1, LEGENDARY +2, anything
//   less or a down ends it, heat = streak - 1 at most 3); the ONE multiplier table read in all three places
//   (_tod_luck, _tod_upgrades roll_rarity, TodSpinReel.lua); the card roll swept at every heat against an
//   independent mirror (COMMON pays, never below 0, the guarantees never read heat); the deal report (once per deal,
//   never the tier / locked / dev-test card) and its wiring; the run simulation with the shipped table.
// THE REACH (_tod_upgrade_ui.gsc): reach_roll / reach_plan on every rarity and headroom (never what could not have
//   happened, one reach a deal, the forced dev cases), the measured reach rates against the defines, and
//   reveal_slot run for every reveal shape: its beats (<= 15 a deal on the 4-bit counter), its rarity pushes and
//   its sounds (a reach's hitch is always the plain thump, SO CLOSE deflates then stings, BREAK THROUGH crashes).
// Does not emulate the engine or LUI: tools/test_card_pull.lua and tools/test_spin_reel.lua drive the real Lua.
'use strict';
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict'), path = require('path'), cp = require('child_process');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const LUCK = read('scripts/zm/zm_tod2_cybercity/_tod_luck.gsc');
const UPG = read('scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc');
const UI = read('scripts/zm/zm_tod2_cybercity/_tod_upgrade_ui.gsc');
const SHOP = read('scripts/zm/zm_tod2_cybercity/_tod_shop.gsc');
const REEL = read('ui/uieditor/widgets/HUD/AetheriumWidgets/TodSpinReel.lua');
const PULL = read('ui/uieditor/widgets/HUD/AetheriumWidgets/TodPull.lua');
const MENU = read('ui/uieditor/menus/hud/tod_upgrade.lua');
let checks = 0;
const ok = (v, m) => { assert.ok(v, m); checks++; };

function body(src, name) {
  const clean = src.replace(/\/\/[^\n]*/g, '');
  const start = clean.indexOf('function ' + name + '(');
  assert(start >= 0, 'function ' + name);
  const a = clean.indexOf('{', start); let b = a + 1, depth = 1;
  while (depth) { if (clean[b] === '{') depth++; if (clean[b] === '}') depth--; b++; }
  return clean.slice(a + 1, b - 1);
}
const defsOf = src => { const d = {}; for (const m of src.matchAll(/#define (TOD_\w+)\s+([-\d.]+)/g)) d[m[1]] = Number(m[2]); return d; };
// GSC -> JS: the few shapes these functions use
const translate = c => c
  .replace(/foreach \( (\w+) in ([^)]+) \)/g, 'for (const $1 of $2)')
  .replace(/\.size\b/g, '.length')
  .replace(/\bint\(/g, 'Math.trunc(')
  .replace(/&"/g, '"')
  .replace(/\[\[ ([^\]]+) \]\]\(/g, '$1(')
  .replace(/\b(\w+) thread (\w+)\(/g, '$1.thread_$2(')
  .replace(/\b(self|player) (\w+)\(/g, '$1.$2(')
  .replace(/SpawnStruct\(\)/g, '({})')
  .replace(/\bwait\(/g, 'wait_(');

let seed = 2026;
const rng = () => { seed = (seed + 0x6D2B79F5) | 0; let t = seed; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const env = Object.assign({
  array: (...a) => a, level: {}, rf: 0, useRf: false,
  isdefined: x => x !== undefined && x !== null, isplayer: x => !!(x && x.isPlayer),
  IS_TRUE: x => x === true || x === 1,
  RandomInt: n => Math.floor(rng() * n), RandomFloat: n => (env.useRf ? env.rf : rng() * n),
  dev_log: () => {}, tier_rarity_factor: () => 1.0, domain_id: () => 7, wait_: () => {},
  GetTime: () => 0,
}, defsOf(LUCK), defsOf(UPG), defsOf(UI));
vm.createContext(env);
const load = (src, name, args, locals) =>
  vm.runInContext(`function ${name}(${args}){${locals ? 'let ' + locals + ';' : ''}${translate(body(src, name))}}`, env);
load(LUCK, 'heat', 'player', '');
load(LUCK, 'heat_mult', 'player', 'h');
load(LUCK, 'streak_result', 'player,best,source,fb_secs', 's,old,h,change');
load(LUCK, 'streak_end', 'player,why', 'had,old');
load(UPG, 'heat_mult_of', 'player', 'h');
load(UPG, 'roll_rarity', 'player,tier', 'b,t,rare,epic,leg,f,hm,roll');
load(UI, 'reveal_rarity', 'o', 'r');
load(UI, 'reach_near_pct', 'r', '');
load(UI, 'reach_break_pct', 'r', '');
load(UI, 'reach_roll', 'o', 'r,near_ok,b,n,x');
load(UI, 'reach_plan', 'opts', 'names,i,o,kind,p,r,result,forced');
load(UI, 'streak_report', 'opts', 'best,i,o,r');
load(UI, 'reveal_slot', 'slot,o,sc,plan', 'rar,reach_at,reach_win,k,dwell');

// THE ONE TABLE: _tod_luck sets it, _tod_upgrades and _tod_shop read it, the reel draws it
const tableSrc = (LUCK.match(/level\.tod_heat_mult = array\(([^)]*)\);/) || ['', ''])[1];
const HEAT = tableSrc.split(',').map(Number);
ok(HEAT.length === 4 && HEAT[0] === 1 && HEAT.every((x, i) => i === 0 || x > HEAT[i - 1]), 'the heat table is cold 1.0 then rising: ' + HEAT);
env.level.tod_heat_mult = HEAT;
const reelHeat = ((REEL.match(/HEAT_MULT = \{ \[ 0 \] = ([^}]*)\}/) || ['', ''])[1]).split(',').map(x => Number(x.trim())).filter(x => !isNaN(x));
ok(JSON.stringify(reelHeat) === JSON.stringify(HEAT), 'TodSpinReel.lua heats its odds by the same table (' + reelHeat + ')');
ok(body(UPG, 'heat_mult_of').includes('level.tod_heat_mult[ h ]') && !/^#using[^\n]*\\_tod_luck;/m.test(UPG), '_tod_upgrades reads the table as a field (never #using _tod_luck: the cycle rule)');
ok(body(SHOP, 'roll_rarity').includes('hm = tod_luck::heat_mult( self );'), '_tod_shop rolls with tod_luck::heat_mult');
ok(!/heat/i.test(body(UPG, 'guarantee_rarity')) && !/heat/i.test(body(SHOP, 'roll_rarity').split('roll = RandomFloat( 100 );')[1]), 'the luck guarantees never read heat');
const NAMES = ['WARM', 'HEATING UP', 'ON FIRE'];
ok(REEL.includes('HEAT_NAME = { [ 0 ] = "", "WARM", "HEATING UP", "ON FIRE" }') && MENU.includes('{ "WARM", "HEATING UP", "ON FIRE" }'), 'the spin chip, the HUD chip and the panel line name the heat the same way: ' + NAMES);

// ---- THE STREAK: every transition, executed
const pushes = [], feedback = [];
const mk = () => ({ isPlayer: true, GetEntityNumber: () => 0, push_heat: c => pushes.push(c), thread_streak_feedback: (o, h, s) => feedback.push([o, h, s]) });
let p = mk();
const step = (best, src) => { env.streak_result(p, best, src || 'deal', 0.5); return [p.tod_luck_streak, p.tod_luck_heat]; };
ok(JSON.stringify(step(3)) === '[1,0]', 'one EPIC: a streak of 1, still cold (one hit is not a streak)');
ok(JSON.stringify(step(3)) === '[2,1]' && env.heat_mult(p) === HEAT[1], 'two EPICs in a row: WARM, x' + HEAT[1]);
ok(JSON.stringify(step(3)) === '[3,2]' && env.heat_mult(p) === HEAT[2], 'three: HEATING UP, x' + HEAT[2]);
ok(JSON.stringify(step(4)) === '[5,3]' && env.heat_mult(p) === HEAT[3], 'a LEGENDARY counts double: ON FIRE, x' + HEAT[3]);
ok(JSON.stringify(step(4)) === '[7,3]', 'heat never passes ON FIRE');
ok(JSON.stringify(step(2)) === '[0,0]' && env.heat_mult(p) === 1, 'anything below EPIC ENDS the streak (cold, x1)');
ok(feedback.some(f => f[0] === 3 && f[1] === 0), 'its end is heard (a hiss) and drawn');
p = mk(); step(4);
ok(JSON.stringify([p.tod_luck_streak, p.tod_luck_heat]) === '[2,1]', 'a single LEGENDARY: WARM at once');
env.streak_end(p, 'down');
ok(p.tod_luck_streak === 0 && p.tod_luck_heat === 0, 'going down ends it');
feedback.length = 0; pushes.length = 0;
env.streak_end(p, 'down');
ok(feedback.length === 0 && pushes.length === 0, 'a down with no streak is silent (the HUD is already cold: nothing is sent, nothing is heard)');
p = mk(); env.streak_result(p, 0, 'deal', 0); env.streak_result(p, undefined, 'deal', 0); env.streak_result(undefined, 4, 'deal', 0);
ok(p.tod_luck_streak === undefined, 'nothing countable leaves the streak alone (a lone tier card, garbage)');
feedback.length = 0; pushes.length = 0; p = mk();
step(3); ok(feedback.length === 0 && pushes[pushes.length - 1] === 0, 'a streak that grows without heating up refreshes the HUD at once, no sound');
step(3); ok(feedback.length === 1 && feedback[0][0] === 0 && feedback[0][1] === 1 && feedback[0][2] === 0.5, 'heating up: the feedback thread carries the change and waits fb_secs (sound and pulse land together)');
const fb = body(LUCK, 'streak_feedback');
ok(fb.indexOf('wait secs;') < fb.indexOf('self push_heat( change );') && fb.includes('"tod_heat_fire"') && fb.includes('"tod_heat_up"') && fb.includes('"tod_heat_out"'), 'the HUD copy and the three sounds come after the wait');
// RT 2026-10-05: THE TOAST (kind 3, our typeface) replaced the stock-font IPrintLnBold; team_toast skips the player himself
ok(fb.includes('self tod_upgrade_ui::team_toast( 3, 0, "tod_pull_alert" );') && !fb.includes('IPrintLnBold') && body(UI, 'team_toast').includes('p == self') && body(UI, 'team_toast').includes('LuiNotifyEvent( &"tod_toast", 3, kind, who, code )'), 'reaching ON FIRE tells the teammates (never the player himself), as THE TOAST');
ok(body(LUCK, 'down_watcher').includes('streak_end( self, "down" );'), 'the down edge ends the streak');
ok(body(LUCK, 'on_player_spawned').includes('self push_heat( 0 );') && body(LUCK, 'on_player_spawned').includes('self thread heat_resend_watch();'), 'a fresh life hears its heat, and a hot one is re-sent (HUD rebuilds)');
ok(LUCK.includes('#precache( "eventstring", "tod_luck_heat" );') && MENU.includes('"tod_luck_heat"') && REEL.includes('"tod_luck_heat"'), 'the heat event is precached and both HUD listeners hear it');
ok(body(LUCK, 'init').includes('level.tod_luck_streak_fn = &streak_result;'), 'the card deal reports through level.tod_luck_streak_fn');

// ---- the card roll at every heat (_tod_upgrades roll_rarity, swept) against an independent mirror
const mirror = (t, hm) => { const rare = 27 + 9 * t, epic = (13 + 7 * t) * hm, leg = (4 + 4 * t) * hm; return [100 - rare - epic - leg, rare, epic, leg]; };
env.useRf = true;
for (let h = 0; h <= 3; h++) for (const bar of [0, 30, 50, 80, 100]) {
  const pl = { tod_luck_bar: bar, tod_luck_heat: h };
  const c = [0, 0, 0, 0];
  for (let i = 0; i < 10000; i++) { env.rf = i / 100; c[env.roll_rarity(pl, 0) - 1]++; }
  const got = c.map(x => x / 100), want = mirror(bar / 100, HEAT[h]);
  ok(got.every((x, i) => Math.abs(x - want[i]) < 0.02), `cards at bar ${bar}, heat ${h}: ${got.map(x => x.toFixed(2))} (mirror ${want.map(x => x.toFixed(2))})`);
  ok(want[0] > 0, 'COMMON stays above 0 at bar ' + bar + ' heat ' + h);
}
env.useRf = false;

// ---- THE REACH: who may reach (never what could not have happened)
const card = (rar, cur, max, extra) => Object.assign({ domain: 'luck', rarity: rar, cur, max }, extra || {});
for (let i = 0; i < 400; i++) {
  assert.equal(env.reach_roll(card(3, 0, 9, { domain: 'tier' })), 0, 'never the CLASS TIER card');
  assert.equal(env.reach_roll(card(3, 0, 9, { locked: true })), 0, 'never a floor-locked card');
  assert.equal(env.reach_roll(card(4, 0, 9, { rarity_locked: true })), 0, 'never a rarity-locked domain');
  assert.notEqual(env.reach_roll(card(3, 6, 9)), 1, 'no SO CLOSE to LEGENDARY without 4 levels of room (cur 6 of 9 has 3)');
  assert.notEqual(env.reach_roll(card(1, 0, 9)), 2, 'a COMMON can never BREAK THROUGH (there is no rung below it)');
  assert.notEqual(env.reach_roll(card(4, 0, 9)), 1, 'a LEGENDARY can never come SO CLOSE (there is no rung above it)');
}
ok(true, 'reach eligibility held over 400 x 6 rolls (tier, locked, rarity-locked, headroom, no rung below / above)');
ok(env.reach_roll(card(3, 0, 9, { tod_reach_force: 1 })) === 1 && env.reach_roll(card(4, 0, 9, { tod_reach_force: 2 })) === 2, 'the dev bench forces SO CLOSE and BREAK THROUGH');
ok(env.reach_roll(card(3, 6, 9, { tod_reach_force: 1 })) === 0 && env.reach_roll(card(1, 0, 9, { tod_reach_force: 2 })) === 0, 'even forced, a reach that could not happen does not');
// the measured rates, per card by its real rarity (plenty of room), against the defines
for (const [rar, nearDef, breakDef] of [[1, 'TOD_PULL_NEAR_1', null], [2, 'TOD_PULL_NEAR_2', 'TOD_PULL_BREAK_2'], [3, 'TOD_PULL_NEAR_3', 'TOD_PULL_BREAK_3'], [4, null, 'TOD_PULL_BREAK_4']]) {
  let n = 0, b = 0; const N = 40000;
  for (let i = 0; i < N; i++) { const k = env.reach_roll(card(rar, 0, 9)); if (k === 1) n++; if (k === 2) b++; }
  const want = [nearDef ? env[nearDef] : 0, breakDef ? env[breakDef] : 0];
  ok(Math.abs(100 * n / N - want[0]) < 1.0 && Math.abs(100 * b / N - want[1]) < 1.0, `rarity ${rar}: SO CLOSE ${(100 * n / N).toFixed(1)} (wants ${want[0]}), BREAK THROUGH ${(100 * b / N).toFixed(1)} (wants ${want[1]})`);
}
// one reach a deal: the left card first, the right only if the left did not (the translated functions read `self`
// as a context global: give reach_plan its logger)
env.self = { pull_log: () => {} };
{
  let left = 0, right = 0;
  const N = 20000;
  for (let i = 0; i < N; i++) {
    const plan = env.reach_plan([card(4, 0, 9), card(4, 0, 9)]);
    if (plan && plan.slot === 'A') left++;
    if (plan && plan.slot === 'B') right++;
  }
  // two LEGENDARY cards break through 60 in 100 each: the left 60 %, the right only on the left's other 40 %, 60 % of it
  const b4 = env.TOD_PULL_BREAK_4 / 100;
  ok(Math.abs(left / N - b4) < 0.02 && Math.abs(right / N - (1 - b4) * b4) < 0.02, 'one reach a deal: the left reaches ' + (100 * left / N).toFixed(1) + '%, the right only when the left did not (' + (100 * right / N).toFixed(1) + '%)');
}
const plan = env.reach_plan([card(3, 0, 9, { tod_reach_force: 1 }), card(4, 0, 9, { tod_reach_force: 2 })]);
ok(plan && plan.slot === 'A' && plan.win === false && plan.rung === 3, 'a forced SO CLOSE on the left plans the left card at its EPIC rung');
const plan2 = env.reach_plan([card(1, 0, 9, { locked: true }), card(4, 0, 9, { tod_reach_force: 2 })]);
ok(plan2 && plan2.slot === 'B' && plan2.win === true && plan2.rung === 3, 'a BREAK THROUGH to LEGENDARY strains from the EPIC rung');

// ---- reveal_slot, executed for every reveal shape: beats, pushes, sounds
function reveal(rar, planned) {
  const log = [];
  let beats = 0;
  const self = {
    pull_beat: () => { beats++; log.push('BEAT'); },
    set_field: (f, v) => log.push(f + '=' + v),
    PlayLocalSound: a => log.push('snd:' + a),
    announce_legendary: () => log.push('ANNOUNCE'),
  };
  env.self = self;
  env.reveal_slot('A', card(rar, 0, 9), 1.0, planned);
  return { beats, log };
}
const P = (rung, win) => ({ slot: 'A', rung, win });
for (let rar = 1; rar <= 4; rar++) {
  const r = reveal(rar, undefined);
  ok(r.beats === 1 + rar, `a plain ${rar}-rung card: ${r.beats} beats (the start + one hitch a rung)`);
}
{
  const r = reveal(3, P(3, false));    // EPIC, SO CLOSE
  const L = r.log.join(' ');
  ok(r.beats === 1 + 3 + 2, 'SO CLOSE adds two beats (the reach, its resolution): ' + r.beats);
  ok(/BEAT snd:tod_pull_beat BEAT snd:tod_pull_reach BEAT snd:tod_pull_reach_fail snd:tod_super_sting todUpgAD=7$/.test(L), 'SO CLOSE: the plain thump (never the sting first), the reach, the deflate, THEN the sting and the flip: ' + L);
  ok(!r.log.includes('todUpgAR=3'), 'SO CLOSE never pushes the rung above');
}
{
  const r = reveal(4, P(3, true));     // LEGENDARY, BREAK THROUGH from EPIC
  const L = r.log.join(' ');
  ok(r.beats === 1 + 4 + 1, 'BREAK THROUGH adds one beat (the reach; the climb resolves it): ' + r.beats);
  ok(/todUpgAR=2 snd:tod_pull_rung_3 BEAT snd:tod_pull_beat BEAT snd:tod_pull_reach todUpgAR=3 snd:tod_pull_break BEAT snd:tod_pull_legendary todUpgAD=7 ANNOUNCE$/.test(L), 'BREAK THROUGH: thump, reach, the climb CRASHES through, then the jackpot sting: ' + L);
}
{
  const r = reveal(1, P(1, false));    // COMMON, SO CLOSE to RARE
  const L = r.log.join(' ');
  ok(/BEAT snd:tod_pull_reach BEAT snd:tod_pull_reach_fail snd:tod_card_land todUpgAD=7$/.test(L) && !L.includes('tod_super_sting'), 'a COMMON that comes SO CLOSE lands with the card land, no sting: ' + L);
}
// the worst deal on the 4-bit beat counter: one reach, the other card plain
let worst = 0;
for (let a = 1; a <= 4; a++) for (let b = 1; b <= 4; b++) {
  const shapes = [[undefined, undefined]];
  if (a <= 3) shapes.push([P(a, false), undefined]);
  if (a >= 2) shapes.push([P(a - 1, true), undefined]);
  if (b <= 3) shapes.push([undefined, P(b, false)]);
  if (b >= 2) shapes.push([undefined, P(b - 1, true)]);
  for (const [pa, pb] of shapes) worst = Math.max(worst, reveal(a, pa).beats + reveal(b, pb).beats);
}
ok(worst === 11 && worst <= 15, 'the worst deal needs ' + worst + ' beats, inside todUpgHold\'s 15');
ok(body(UI, 'reveal_deal').includes('plan = self reach_plan( opts );') && (body(UI, 'reveal_deal').match(/reveal_slot\( "[AB]", opts\[ [01] \], sc, plan \)/g) || []).length === 2, 'reveal_deal plans one reach and hands it to both slots');

// ---- the deal report: once per deal, the best card it SHOWED, never the tier / locked / dev-test card
{
  const calls = [];
  env.level.tod_luck_streak_fn = (pl, best, src, secs) => calls.push([best, src, secs]);
  env.self = { pull_log: () => {} };
  const deal = [card(2, 0, 9), card(3, 0, 9)];
  env.streak_report(deal);
  env.streak_report(deal);     // the deferred station deal re-presents the SAME cards
  ok(calls.length === 1 && calls[0][0] === 3 && calls[0][1] === 'deal', 'a deal reports its best card once, even when it is shown twice');
  calls.length = 0;
  env.streak_report([card(4, 0, 9, { domain: 'tier' }), card(1, 0, 9)]);
  ok(calls.length === 1 && calls[0][0] === 1, 'the CLASS TIER card never counts (here the COMMON beside it does)');
  calls.length = 0;
  env.streak_report([card(4, 0, 9, { domain: 'tier' })]);
  ok(calls.length === 0, 'a lone tier card counts for nothing (the streak is left alone)');
  env.streak_report([card(4, 0, 9, { dev_test: true }), card(4, 0, 9, { dev_test: true })]);
  ok(calls.length === 0, 'the dev CARD TEST bench never counts');
  env.streak_report([card(4, 0, 9, { locked: true }), card(3, 0, 9)]);
  ok(calls.length === 1 && calls[0][0] === 3, 'a floor-locked card never counts');
  const pc = body(UI, 'present_choice');
  ok(pc.indexOf('self reveal_deal( opts );') < pc.indexOf('self streak_report( opts );') && pc.indexOf('self streak_report( opts );') < pc.indexOf('self set_field( "todUpgFocus", 1 );'), 'the deal counts once its cards are face up, before the pick');
  ok(SHOP.includes('tod_luck::streak_result( self, rar + 1, "spin", TOD_SPIN_STREAK_FB_SECS );'), 'a Black Market spin is a pull too');
  ok(body(UPG, 'card_test_option').includes('o.dev_test = true;'), 'every dev bench card is tagged as a test');
  ok(body(UPG, 'make_option').includes('o.rarity_locked = true;'), 'a rarity-locked domain marks its card (it never reaches)');
}

// ---- the sounds the scripts play exist (2D rows in tod_near.csv, GENERATED by tools/near_miss/make_sounds.py)
const nearCsv = read('sound/aliases/tod_near.csv');
for (const a of ['tod_pull_reach', 'tod_pull_reach_fail', 'tod_pull_break', 'tod_heat_up', 'tod_heat_fire', 'tod_heat_out', 'tod_spin_teeter', 'tod_spin_near'])
  ok(new RegExp('^' + a + ',.*,2d,', 'm').test(nearCsv), 'alias exists (2D): ' + a);
ok(PULL.includes('"tod_pull_reach_flick"') && PULL.includes('"tod_pull_tremble"') && PULL.includes('function P.ReachClear( s )'), 'the reveal draws the reach (TodPull.lua)');

// ---- what it does over a run: the planning simulation with the SHIPPED table (a knob change shows its effect here)
const sim = cp.execFileSync(process.execPath, [path.join(root, 'tools/near_miss/sim_hot_streak.js'), '--mult', HEAT.slice(1).join(','), '--runs', '30000'], { encoding: 'utf8' });
const shownLine = sim.split('\n').find(l => l.startsWith('shown'));
const hotShare = Number(((shownLine || '').match(/pulls made while hot\s+([\d.]+)%/) || [])[1]);
ok(hotShare > 5 && hotShare < 35, 'a streak stays the lucky minority: hot on ' + hotShare + '% of pulls (under 35)');
console.log(shownLine.trim());

console.log(`HOT STREAK + REACH PASS: ${checks} checks; streak transitions + feedback + wiring, one heat table in three places, the card roll heated at every bar, the guarantees heat-blind, reach eligibility + forced cases + measured rates, one reach a deal, reveal_slot beats / pushes / sounds for every shape (worst ${worst} of 15), the deal report once per deal, the sounds, the run simulation.`);
