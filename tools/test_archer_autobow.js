// THE AUTOMATIC BOW + THE GRAPPLE'S INVISIBLE WALL (2026-10-05, docs/218) - the gate.
//   node tools/test_archer_autobow.js
// User: "you hold it down and then once it's fully charged it shoots ... when it's maxed out it almost becomes an
// automatic bow ... the shots don't go far enough ... The grapple, you can kind of just go out of the map".
// Runs the SHIPPING pure GSC (tools/sky_ships/gsc_eval.js) - the bow's QUICK DRAW curve, draw windows and the
// held-arrow rule, the wall's column + cut - and proves every emitted Archer weapon form agrees with the script
// numbers, the Lua card rows and the generator tables (read as TEXT: requiring gen_tod_twins.js RUNS it).
// What it cannot prove: that the engine draws again on a held trigger (chargeShotFireWhenQueueReachesMax), the feel,
// or the zone volumes' real shapes - the user's playtest and the [TOD_ABOW] HOLD_* / [TOD_ARCHER] WALL logs do.
'use strict';
const fs = require('fs'), path = require('path'), assert = require('assert');
const { gscLoad, V } = require('./sky_ships/gsc_eval');
const root = path.join(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const DIR = 'scripts/zm/zm_tod2_cybercity/';
const BOW = read(DIR + '_tod_archer_bow.gsc'), ARCHER = read(DIR + '_tod_archer.gsc'), RUNE = read(DIR + '_tod_archer_rune.gsc');
const UPG = read(DIR + '_tod_upgrades.gsc'), LUA = read('ui/uieditor/menus/hud/tod_upgrade.lua'), GEN = read('tools/gen_tod_twins.js');
const TWINS = read('source_data/tod_weapon_twins.gdt');
let checks = 0;
const ok = (c, label) => { assert(c, label); checks++; };
const near = (a, b, tol, label) => { assert(Math.abs(a - b) <= tol, label + ': ' + a + ' vs ' + b); checks++; };
const defs = src => Object.fromEntries([...src.matchAll(/^#define\s+(\w+)\s+(-?[\d.]+)\b/gm)].map(m => [m[1], Number(m[2])]));
const genArr = name => { const m = GEN.match(new RegExp('^const ' + name + ' = \\[([^\\]]+)\\]', 'm')); assert(m, name); return m[1].split(',').map(Number); };
const genNum = name => { const m = GEN.match(new RegExp('^const ' + name + ' = ([\\d.]+);', 'm')); assert(m, name); return Number(m[1]); };

// ---- 1. the generator tables: x3 at Lv9 on 3^(Lv/9), the weapon steps at Lv0 / 2 / 4 / 6 / 8 ----
const STEP = genArr('SHOTSPEED_STEP'), VEL = genArr('SHOTSPEED_VEL'), FULL = genNum('AUTO_DRAW_FULL_MULT');
ok(STEP.length === 5 && VEL.length === 5, 'five QUICK DRAW forms (s0..s4): the registration count does not move');
STEP.forEach((t, k) => near(t, Math.pow(3, -2 * k / 9), 1e-4, 'SHOTSPEED_STEP s' + k + ' = 3^(-' + 2 * k + '/9)'));
ok(VEL.every((v, k) => k === 0 || v > VEL[k - 1]) && VEL[4] <= 1.6, 'arrow speed rises every step, x1.6 at the top (flat arrows: speed buys lead, not range)');

// ---- 2. the shipping bow functions, verbatim ----
const BD = defs(BOW);
ok(FULL === BD.TOD_AB_MAX_MULT, 'LOCKSTEP: the DPS pin divides a held arrow by the script\'s full-draw x' + BD.TOD_AB_MAX_MULT);
near(BD.TOD_AB_QD_LEVEL_MULT, Math.pow(3, 1 / 9), 1e-4, 'TOD_AB_QD_LEVEL_MULT = 3^(1/9)');
const builtins = { IsSubStr: (s, sub) => String(s).includes(sub), Int: Math.trunc };
const g = gscLoad([['tod_archer_bow', BOW]], BD, { builtins });
const speed = L => 1 / g.call('shot_step_lv', [L]) * g.call('qd_level_mult', [L]);
for (let L = 0; L <= 9; L++) {
  near(g.call('shot_step_lv', [L]), STEP[Math.min(Math.floor(L / 2), 4)], 1e-9, 'shot_step_lv(' + L + ') = the weapon step');
  near(speed(L), Math.pow(3, L / 9), 0.004 * Math.pow(3, L / 9), 'QUICK DRAW Lv' + L + ' = 3^(' + L + '/9): every level the same +13%');
  ok((g.call('qd_level_mult', [L]) > 1) === (L % 2 === 1), 'the 13% is damage on an odd level only (Lv' + L + ')');
}
near(speed(9), 3, 0.01, 'Lv9 = three times as fast: the almost automatic bow');
near(g.call('shot_step_lv', [-3]), 1, 0, 'no card'); near(g.call('shot_step_lv', [14]), STEP[4], 0, 'clamped at s4');
for (const [name, base] of [['cc_bow_d0s0', BD.TOD_AB_PLAIN_MAX], ['cc_bow_up_d2s0', BD.TOD_AB_PLAIN_MAX * BD.TOD_AB_PAP_TIME],
                            ['cc_fire_bow_d1s0', BD.TOD_AB_FIRE_MAX], ['cc_fire_bow_up_d0s0', BD.TOD_AB_FIRE_MAX * BD.TOD_AB_PAP_TIME]])
  for (let L = 0; L <= 9; L++) near(g.call('draw_window_lv', [name, L]), base * STEP[Math.min(Math.floor(L / 2), 4)], 1e-9, name + ' window Lv' + L);
// THE ONE RULE: an arrow that leaves with the trigger down is a full draw, whatever the clock says
for (const held of [-0.2, 0, 0.05, 0.2, 9]) ok(g.call('shot_frac', [true, held, 0.2071]) === 1, 'held arrow = full draw (clock ' + held + ')');
ok(g.call('shot_frac', [false, 0.05, 0.55]) === 0, 'a tap under the minimum draw is a tap');
near(g.call('shot_frac', [false, 0.325, 0.55]), 0.5, 1e-9, 'a released half draw is half');
ok(g.call('shot_frac', [false, 0.55, 0.55]) === 1 && g.call('shot_frac', [false, 3, 0.55]) === 1, 'a release at / past full draw is full');
ok(g.call('draw_frac', [0.12, 0.1356]) === 1 && g.call('draw_frac', [0.08, 0.1356]) === 0, 'a packed Lv8 draw (~0.04 s past the minimum): past the minimum IS full');
// NEGATIVE CONTROL: timing a held arrow by the 50 ms server clock (the old rule) shorts it - one frame early at Lv8 is
// worth a third of the draw, so the clock alone would hand an automatic bow x2.4 arrows instead of x3
ok(g.call('draw_frac', [0.2071 - 0.05, 0.2071]) < 0.6, 'negative control: the clock alone shorts a held Lv8 arrow');

// ---- 3. every emitted Archer form agrees with the script ----
const blocks = new Map([...TWINS.matchAll(/"([^"\n]+)" \( "[a-z]+weapon\.gdf" \)\s*\{([\s\S]*?)\n\t\}/g)]
  .map(m => [m[1], Object.fromEntries([...m[2].matchAll(/"([^"\n]+)" "([^"\n]*)"/g)].map(f => [f[1], f[2]]))]));
let bows = 0, xbows = 0;
for (const [name, f] of blocks) {
  const sm = name.match(/_d(\d)s(\d)(?:_zm)?$/);
  if (!/^cc_(fire_)?bow/.test(name) && !/^cc_crossbow/.test(name)) continue;
  assert(sm, name + ' carries d/s levels');
  const s = +sm[2], L = 2 * s, up = name.includes('_up');
  near(+f.projectileSpeed, (/crossbow/.test(name) ? 5000 : 4500) * VEL[s], 1, name + ' projectileSpeed');
  ok(f.guidedMissileType === 'None', name + ' flies FLAT (guidance None, the T9 nail gun\'s; "Ballistic" dropped 576 u over 3000)');
  if (/^cc_crossbow/.test(name)) {
    xbows++;
    ok(f.fireType === 'Full Auto', name + ' is a held repeater');
    ok(+f.clipSize === (up ? 13 : 10) && f.ammoCountClipRelative === '1', name + ' magazine ' + f.clipSize);
    near(+f.fireTime, 0.35 * (up ? 0.8 : 1) * STEP[s], 1e-3, name + ' fireTime');
    near(+f.reloadEmptyTime, 1.6 * (up ? 0.75 : 1) * STEP[s], 1e-3, name + ' reload');
    continue;
  }
  bows++;
  ok(f.fireType === 'Charge Shot' && f.chargeShotMaxLevel === '1', name + ' is a one-level draw');
  ok(f.chargeShotFireWhenQueueReachesMax === '1', name + ' releases ITSELF at full draw (the automatic bow)');
  near(+f.chargeShotMaxTime, g.call('draw_window_lv', [name, L]), 1e-3, name + ' full draw = the script window (LOCKSTEP)');
  near(+f.fireTime, g.call('release_lv', [name, L]), 1e-3, name + ' release = the script\'s redraw wait (LOCKSTEP)');
  near(+f.holdFireTime, +f.chargeShotMaxTime, 1e-4, name + ' the pull-back clip ends exactly at full draw');
  near(+f.chargeShotMinTime, BD.TOD_AB_MIN_TIME, 1e-9, name + ' minimum draw');
  ok(+f.chargeShotMaxTime > +f.chargeShotMinTime, name + ' full draw is past the minimum');
  ok(+f.startAmmo === +f.clipSize && f.maxAmmo === '0', name + ' quiver starts full');
}
ok(bows === 80 && xbows === 40, 'all 120 Archer forms checked (' + bows + ' bow, ' + xbows + ' crossbow)');
{ const fb = blocks.get('cc_fire_bow_d0s0_zm'), fbu = blocks.get('cc_fire_bow_up_d0s0_zm');
  ok(+fb.explosionInnerDamage === 280 && +fb.explosionOuterDamage === 140 && +fbu.explosionInnerDamage === 483 && +fbu.explosionOuterDamage === 241,
    'the Fire Bow splash follows the cadence (same damage per second at full draw)'); }

// ---- 4. the bow's wiring (the engine-facing half) ----
const fn = (src, name) => { const i = src.search(new RegExp('function (private )?' + name + '\\(')); assert(i >= 0, name); let d = 0, j = src.indexOf('{', i);
  for (; j < src.length; j++) { if (src[j] === '{') d++; if (src[j] === '}' && --d === 0) break; } return src.slice(i, j + 1); };
const stamp = fn(BOW, 'stamp_shot');
ok(/held = self AttackButtonPressed\(\);/.test(stamp) && /shot_frac\( held,/.test(stamp), 'stamp_shot: the trigger decides a held arrow');
ok(/self\.tod_ab_press_ms = now \+ Int\( self release_time\( weapon \) \* 1000 \);/.test(stamp), 'after a held arrow the next draw starts when its release ends (a later half draw is timed from there)');
ok(/\( now - self\.tod_ab_shot_ms \) <= TOD_AB_SAME_SHOT_MS/.test(stamp), 'one decision per arrow: weapon_fired and missile_fire share it');
ok(/frac = self stamp_shot\( w \);/.test(fn(BOW, 'fire_watch')) && /proj\.tod_ab_charge = self stamp_shot\( w \);/.test(fn(BOW, 'projectile_watch_notify')), 'both shot notifies stamp through stamp_shot');
const draw = fn(BOW, 'draw_watch');
ok(/self\.tod_ab_press_ms < now \) self\.tod_ab_press_ms = now;/.test(draw), 'a fresh press never cuts a held chain\'s scheduled draw short');
ok(/creak_for != self\.tod_ab_press_ms/.test(draw) && /win >= TOD_AB_CUE_MIN/.test(draw), 'one creak per draw, none at an automatic cadence');
ok(/HOLD_STALL/.test(draw) && /HOLD_END/.test(fn(BOW, 'hold_end')), 'the logs say whether the engine drew again on a held trigger');
const cm = fn(BOW, 'charge_mult');
ok(/is_archer_gun\( weapon \)/.test(cm) && /qd = quickdraw_mult\( attacker, weapon \);/.test(cm) && /mult_for\( frac \) \* qd/.test(cm), 'charge_mult: draw x QUICK DRAW on arrows, QUICK DRAW alone on bolts');
ok(/IsSubStr\( weapon\.name, "cc_crossbow" \)/.test(fn(BOW, 'is_archer_gun')), 'the crossbow is an Archer gun for QUICK DRAW');
ok(!/#using scripts\\zm\\zm_tod2_cybercity\\_tod_/.test(BOW.replace(/\/\/[^\n]*/g, '')), 'the bow module stays a leaf (imports no tod module)');
const loop = fn(RUNE, 'loop_watch');
ok(/tod_archer_bow::draw_window\( w \)/.test(loop) && /TOD_RUNE_LOOP_FROM/.test(loop) && !/TOD_RUNE_ARM_MS/.test(RUNE), 'the rune hum reads the live draw window');
ok(/tod_archer_bow::charge_mult\( attacker, inflictor, weapon, meansofdeath \)/.test(UPG), 'the damage callback still applies the Archer shot');
{ const ax = fn(UPG, 'axis_level'); ok(/l >= 8 \) return 4;/.test(ax) && /l >= 6 \) return 3;/.test(ax) && /l >= 4 \) return 2;/.test(ax) && /l >= 2 \) return 1;/.test(ax), 'axis_level: QUICK DRAW steps at Lv2 / 4 / 6 / 8'); }

// ---- 5. the card text, everywhere ----
const gscDesc = (UPG.match(/add_domain\( "shotspeed",\s+"QUICK DRAW",\s+"([^"]+)"/) || [])[1];
const luaRow = (LUA.match(/\[35\] = \{ name = "QUICK DRAW", desc = "([^"]+)", face = \{ "([^"]+)", "([^"]+)" \}, max = 9 \}/) || []);
ok(gscDesc && luaRow[1] === gscDesc, 'QUICK DRAW desc: GSC == Lua');
ok(/automatic/i.test(gscDesc) && /3 times/.test(gscDesc) && !/twice/.test(gscDesc), 'the desc says x3 / almost automatic');
ok(luaRow[2] && luaRow[3] && luaRow[2].length <= 29 && luaRow[3].length <= 29 && /AUTOMATIC AT LV9/.test(luaRow[3]), 'the card face (2 lines that fit)');
{
  const det = (LUA.match(/^\s*\[35\] = \{ eff = "\{V\}", act = function[^\n]*/m) || [''])[0];
  const tab = n => { const m = det.match(new RegExp('local ' + n + ' = \\{ ([^}]+) \\}')); assert(m, 'DETAIL[35] ' + n); return m[1].split(',').map(Number); };
  const S = tab('S'), Vt = tab('V'), D = tab('D');
  for (let L = 0; L <= 9; L++) {
    near(S[L], 1 / STEP[Math.min(Math.floor(L / 2), 4)], 0.006, 'pause row S Lv' + L + ' = the weapon step');
    near(Vt[L], VEL[Math.min(Math.floor(L / 2), 4)], 0.006, 'pause row V Lv' + L);
    near(D[L], Math.pow(3, L / 9), 0.006, 'pause row D Lv' + L + ' = 3^(Lv/9)');
  }
  ok(/\( L % 2 == 1 \) and ", \+13% hits"/.test(det), 'the odd-level 13% is on the row');
  ok('draws x2.66 faster, arrows x1.60, +13% hits'.length <= 46, 'the widest act line fits the 46-character budget');
}

// ---- 6. THE INVISIBLE WALL, run verbatim against a box model of the tower ----
// The tower's lap zones are four boxes from the core (256) to the rails' outer face (436), floor to TOP + 100;
// the core is solid (BulletTracePassed fails into it). Above z 20000 is no zone (the sky).
const AD = defs(ARCHER);
const ring = p => Math.max(Math.abs(p[0]), Math.abs(p[1])) <= 436 && Math.max(Math.abs(p[0]), Math.abs(p[1])) >= 256 && p[2] >= -16 && p[2] <= 20000;
const inCore = p => Math.abs(p[0]) < 256 && Math.abs(p[1]) < 256;
// in_play is the one engine-facing callee (a probe + IsTouching): stubbed by the box world under the name the
// interpreter resolves a same-file call to (ns::name wins over a bare builtin)
const wb = { IsSubStr: builtins.IsSubStr, Int: Math.trunc, in_play: p => ring(p), 'tod_archer::in_play': p => ring(p),
  VectorNormalize: v => { const l = Math.hypot(v[0], v[1], v[2]) || 1; return V(v[0] / l, v[1] / l, v[2] / l); },
  BulletTracePassed: (a, b) => !inCore(b) };
const w = gscLoad([['tod_archer', ARCHER]], AD, { builtins: wb });
const tick = 0.05, look = tick * AD.TOD_ARCHER_WALL_LOOK;
function fly(pos, vel, ticks, s = {}) {   // the user's case: the rope let go, the swing carries on (no gravity on x / y)
  let p = V(...pos), v = V(...vel), cuts = 0;
  for (let i = 0; i < ticks; i++) {
    const real = V(p[0], p[1], p[2] + AD.TOD_ARCHER_WALL_CHEST);
    const col = w.call('wall_column', [real, s]);
    if (col !== undefined) { const nv = w.call('wall_cut', [col, real, v, look, undefined]); if (nv !== undefined) { assert(nv[2] === v[2], 'never a roof: vertical speed untouched'); v = nv; cuts++; } }
    p = V(p[0] + v[0] * tick, p[1] + v[1] * tick, p[2] + v[2] * tick);
  }
  return { p, v, cuts };
}
{ // 20:21 floor 42: "arrived" at (389, 62, 16500) with 895 u/s outward (+y) and 235 (+x), 320 up
  const r = fly([389.4, 62.4, 16500.8], [235.3, 894.9, 320], 40);
  ok(Math.abs(r.p[0]) <= 436 && Math.abs(r.p[1]) <= 436, 'the floor-42 swing stays on the tower (' + r.p.map(Math.round) + ')');
  ok(r.cuts > 0 && r.v[0] === 0 && r.v[1] === 0, 'it slid into the corner and stopped there, like a wall');
}
{ const r = fly([300, 0, 1000], [-50, 600, 0], 10); ok(r.cuts === 0, 'moving inside the ring: untouched'); }
{ const r = fly([400, 0, 1000], [-900, 0, 0], 4); ok(r.cuts === 0, 'toward the solid core: the world stops you, the wall stays out of it'); }
{ const r = fly([600, 0, 1000], [900, 0, 0], 4); ok(r.cuts === 0, 'already out: never trapped outside (the Recall owns it)'); }
{ // over the top of every zone (z 20100) after rising out of the ring: the column it came up is judged - no roof
  const s = { wall_z: 19990 }, r = fly([300, 300, 20100], [0, 1200, 400], 10, s);
  ok(Math.abs(r.p[1]) <= 436 && r.cuts > 0, 'above the zones the column is still walled (' + r.p.map(Math.round) + ')');
}
{ const s = {}; const col = w.call('wall_column', [V(300, 0, 1036), s]); ok(col && s.wall_z === 1036, 'in play: the chest is the column and its height is remembered'); }
// the wiring: on the rope AND in the air after it, never a teleport, never on a jump-pad flight, hooks out of bounds refused
const upd = fn(ARCHER, 'update'), step = fn(ARCHER, 'wall_step'), grab = fn(ARCHER, 'try_grapple');
ok(upd.indexOf('self grapple_step( dt );') < upd.indexOf('self wall_step( s, dt );'), 'the wall runs after the rope\'s own velocity write');
ok(/s\.grace <= 0 \|\| self IsOnGround\(\)/.test(step) && /IS_TRUE\( self\.tod_jumppad_flying \) \) return;/.test(step), 'on the rope or airborne in its grace; never on a jump-pad flight');
ok(!/SetOrigin/.test(step + fn(ARCHER, 'wall_cut') + fn(ARCHER, 'wall_column') + fn(ARCHER, 'in_play')), 'velocity only: the wall never moves the player');
ok(/"out_of_bounds"/.test(grab) && grab.indexOf('"out_of_bounds"') < grab.indexOf('s.hook_cd ='), 'a hook outside the play area is refused before the cooldown is spent');
ok(/reason == "out_of_bounds" \) return "Can't grapple out of the map"/.test(ARCHER), 'the refusal is said in plain words');
ok(/hook_in_play\( tr\[ "position" \] \+ tr\[ "normal" \] \* 48/.test(fn(ARCHER, 'aim_hint')), 'the aim tick goes dark over a hook outside the play area');
ok(/!hook_in_play\( arrive \+/.test(grab), 'the grapple asks the same hook rule');
// the hook rule, verbatim: in a zone, or straight above one at the archer's chest height (a high hall wall); never sideways out
w.call('wall_column', [V(300, 0, 1036), {}]);   // warm the interpreter's cache of the file
const hookOk = (pt, chestZ) => w.call('hook_in_play', [V(...pt), chestZ]);
ok(hookOk([300, 91, 16537], 16166), 'the floor-42 core-wall hook (inside the ring) is allowed');
ok(!hookOk([520, 91, 16537], 16166), 'a hook past the rails is refused');
ok(hookOk([300, 300, 20200], 19950), 'a hook above the top zone but over the ring (a high wall) is allowed');
ok(!hookOk([600, 0, 900], 1036), 'a hook below the archer and outside is refused');
ok(!hookOk([520, 0, 20200], 19950), 'above the zones AND past the rails is refused');
ok(/GetEntArray\( "player_volume", "script_noteworthy" \)/.test(fn(ARCHER, 'in_play')) && /probe IsTouching\( v \)/.test(fn(ARCHER, 'in_play')), 'in_play: stock\'s probe + IsTouching over every zone volume');
ok(/walls=/.test(fn(ARCHER, 'end_grapple')) && /WALL player=/.test(step), 'logged: WALL lines + walls= on GRAPPLE_END');

console.log('ARCHER AUTO BOW + GRAPPLE WALL: ' + checks + ' checks passed (shipping GSC run verbatim; emitted forms, Lua rows and generator tables in lockstep; the engine\'s held-trigger redraw and the feel are the playtest).');
