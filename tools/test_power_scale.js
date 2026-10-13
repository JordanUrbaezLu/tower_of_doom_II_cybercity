// test_power_scale.js - gate for MAP 1's POWER STRUCTURE AT ONE TENTH (2026-09-25).
// User: "follow the power structure of map 1 but 10x less. HP on players will stay
// same and enemy damage on player will stay same but dps and enemy health will be
// 10x less" / "Lethal and tactical as well" / "so players can easily identify how
// much damage they do". See scripts/zm/zm_tod2_cybercity/_tod_power_scale.gsc.
//
// Checks the shipping sources, not a copy: the horde curve against map 1's own
// stock loop, the damage front door's install + exemptions, every pass-through mark
// cleared after its DoDamage, the elite / boss / Panzer-part numbers at map 1 / 10,
// the crosshair number encoding (GSC and Lua in lockstep), and that the fraction
// carry keeps a hit's average exact.
'use strict';
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const R = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(R, p), 'utf8');
const MOD = 'scripts/zm/zm_tod2_cybercity/';
let checks = 0;
const ok = (c, m) => { assert(c, m); checks++; };

// ---- the horde curve --------------------------------------------------------
const ps = read(MOD + '_tod_power_scale.gsc');
const def = (src, name) => { const m = src.match(new RegExp('#define\\s+' + name + '\\s+([0-9.]+)')); assert(m, name); return +m[1]; };
ok(def(ps, 'TOD_PS_DAMAGE') === 0.1, 'damage knob is x0.1');
ok(def(ps, 'TOD_PS_MAP1_START') === 135 && def(ps, 'TOD_PS_MAP1_INCREASE') === 90 && def(ps, 'TOD_PS_MAP1_EXP_MULT') === 0.1 && def(ps, 'TOD_PS_MAP1_EXP_ROUND') === 10, 'map 1 curve verbatim');
// map 1's stock loop (zombie_utility::ai_calculate_health with 135 / 90 / 0.1)
const map1 = r => { let h = 135; for (let i = 2; i <= r; i++) { if (i >= 10) { const o = h; h += Math.trunc(h * 0.1); if (h < o) return o; } else h = Math.trunc(h + 90); } return h; };
const horde = r => Math.max(1, Math.trunc(map1(r) / 10 + 0.5));
ok(map1(1) === 135 && map1(9) === 855 && map1(10) === 940, 'map 1 curve reproduced (135 / 855 / 940)');
for (let r = 1; r <= 100; r++) ok(Math.abs(horde(r) - map1(r) / 10) <= 0.5, 'round ' + r + ' is map 1 / 10');
ok(/Int\( map1_zombie_hp\( round \) \/ \( TOD_PS_HEALTH_DIV \* 1\.0 \) \+ 0\.5 \)/.test(ps), 'horde_hp rounds map 1 / 10 in float');
ok(/level\.zombie_health = want;/.test(ps) && /wait 0\.05;/.test(ps), 'track_rounds holds level.zombie_health on the curve');
const zs = read(MOD + '_tod_zombie_speed.gsc');
ok(/base = tod_power_scale::horde_hp\( current_round\(\) \);/.test(zs), 'fresh spawns take the exact curve');
ok(!/if \( m == 1 \)\s*\r?\n\s*return;/.test(zs), 'the per-spawn write runs in solo too');
const er = read(MOD + '_tod_endless_rounds.gsc');
ok(/"zombie_health_start" \]\s*= 13\.5;/.test(er) && /"zombie_health_increase" \] = 9;/.test(er), 'stock inputs at map 1 / 10');

// ---- the front door ------------------------------------------------------------
const main = read('scripts/zm/zm_tod2_cybercity.gsc');
const iUser = main.indexOf('zm_usermap::main();'), iPs = main.indexOf('tod_power_scale::init();'), iMain = main.indexOf('level thread tod_main::init();');
ok(iUser > 0 && iPs > iUser && iPs < iMain, 'gate installs after zm_usermap::main (stock sets the callback) and before tod_main::init');
ok(/level\.callbackActorDamage = &actor_damage_entry;/.test(ps) && /self \[\[ level\.tod_ps_stock_actor_damage \]\]\( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, vDamageOrigin, timeOffset, boneIndex, modelIndex, surfaceType, surfaceNormal \);/.test(ps), 'entry forwards all 15 engine arguments to stock');
for (const mark of ['tod_cleave_hit', 'tod_wisp_hit', 'tod_ps_exempt'])
  ok(ps.includes('self.' + mark), 'gate honours the ' + mark + ' mark');
// W2E (2026-10-05): TRAILBLAZER retired whole (a parked card) - its pass-through mark left the front door with it.
ok(!ps.includes('self.tod_trail_hit'), 'the retired TRAILBLAZER mark is gone from the front door');
ok(/IsSubStr\( weapon\.name, "xmas_gun" \)/.test(ps) && /"hero_gravityspikes_melee"/.test(ps), 'Gift of Death + Gravity Spikes exempt by weapon');
ok(/over == 1 \|\| over == 100 \|\| over == 666 \|\| over == 1000 \|\| over == 10000/.test(ps), 'kill-intent signatures exempt');
ok(/!IsPlayer\( attacker \) && !\( IS_TRUE\( attacker\.tod_is_partner \) && IsActor\( attacker \) \)/.test(ps), 'only players and partner robots are scaled');
ok(/self\.team != team \|\| IS_TRUE\( self\.tod_is_partner \)/.test(ps), 'only enemies are scaled (player HP / enemy damage untouched)');

// ---- marks set around a DoDamage are cleared after it (a paused world returns 0
// before the chain consumes them; a leaked mark would exempt the next real hit)
const up = read(MOD + '_tod_upgrades.gsc');
// R5 (2026-10-04): the old CLEAVE splash and THOR'S THUNDER's shock left with the Map 1 purge; the live
// pass-through lane is PIERCING (_tod_class_cards), which must clear its own mark.
ok(/z\.tod_cleave_hit = true;[\s\S]{0,300}?z DoDamage\([^\n]*\);\s*\r?\n\s*if \( isdefined\( z \) && IS_TRUE\( z\.tod_cleave_hit \) \) z\.tod_cleave_hit = undefined;/.test(read(MOD + '_tod_class_cards.gsc')), 'pierce clears its mark');
ok(!/function (cleave_splash|thor_shock|thor_strike|trail_loop|trail_burn_tick)\(/.test(up) && !up.replace(/\/\/[^\n]*/g, '').includes('tod_trail_hit'), 'the retired cleave / thor / trailblazer lanes stay gone (code; comments are history)');
ok(/swing = int\( damage \* mult \* dmult \+ 0\.5 \);/.test(up) && /final = int\( swing \* melee_boss_mult\( attacker, self, is_melee \) \+ 0\.5 \);/.test(up), 'upgrade chain rounds, not truncates');
ok(/push_dmg_num\( kill - 666, headshot \)/.test(up), 'insta-kill number shows the health removed');
const phd = read(MOD + '_tod_perk_phd.gsc');
ok(def(phd, 'TOD_PHD_EXPLODE_DAMAGE') === 100 && /z\.tod_ps_exempt = true;\s*\r?\n\s*z DoDamage\( n_damage, v_burst, self \);\s*\r?\n\s*if \( isdefined\( z \) \) z\.tod_ps_exempt = undefined;/.test(phd), 'PhD floor / 10, exempt + cleared');
ok(/return 100 \* power \* mult;/.test(read(MOD + '_tod_retriever.gsc')), 'Retriever flat hit is 100 x power (x the Retriever card multiplier, 2026-09-26)');
const pa = read(MOD + '_tod_partners.gsc');
ok(/if \( damage < 3 \) damage = 3;/.test(pa) && /if \( damage > 350 \) damage = 350;/.test(pa), 'partner clamps / 10');

// ---- enemy health at map 1 / 10 ---------------------------------------------------
// W2E (2026-10-05): the Rogue Protector (400), the Panzer (1500 + his part pools), the Apothicon Fury (1500) and the
// hellhound (1120) retired WHOLE with their directors and packs - map 1 / 10 is now pinned on the live elites only
// (hunter_hp below). Their absence is the contract: a module coming back half-way re-opens a /10 question.
const bo = read(MOD + '_tod_bosses.gsc');
ok(!/#define TOD_(PROTECTOR|PANZER)_HP_BASE/.test(bo) && !/level\.mechz_/.test(bo), 'the Protector / Panzer HP pools left _tod_bosses');
for (const f of ['_tod_reaver.gsc', '_tod_hellhounds.gsc', '_tod_sprinter.gsc'])
  ok(!fs.existsSync(path.join(R, MOD, f)), f + ' retired whole (archive/map1_carryover)');
ok(!fs.existsSync(path.join(R, 'scripts/zm/mechz_spiki.gsc')), 'the Panzer pack retired whole (archive/map1_carryover)');
// 2026-10-04 (user: "Elites dont have enough HP"): map 1's floor / 10 (50) stays the BASE, and the
// one elite knob TOD_ELITE_HP_MULT scales the whole of hunter_hp() - the round units and the floor alike.
const dg = read(MOD + '_tod_doppelghast.gsc');
ok(/if \( hp < 50 \* TOD_ELITE_HP_MULT \)/.test(dg) && /hp = int\( base \* units \* tod_zombie_speed::health_mult\(\) \* TOD_ELITE_HP_MULT \+ 0\.5 \);/.test(dg)
   && def(dg, 'TOD_ELITE_HP_MULT') >= 1, 'Doppelghast / Mangler floor 50 (map 1 / 10), both scaled by TOD_ELITE_HP_MULT');

// ---- the crosshair number: exact units, lockstep --------------------------------
const ui = read(MOD + '_tod_upgrade_ui.gsc'), lua = read('ui/uieditor/menus/hud/tod_upgrade.lua');
ok(/dmg = int\( dmg \+ 0\.5 \);\s*\r?\n\s*if \( dmg > 2047 \)\s*\r?\n\s*\{\s*\r?\n\s*scale = 1;\s*\r?\n\s*dmg = int\( \( dmg \+ 50 \) \/ 100 \);/.test(ui), 'GSC: exact to 2047, then hundreds');
ok(/local scale = \( math\.floor\( v \/ 8 \) % 2 >= 1 \) and 100 or 1/.test(lua), 'Lua decodes x1 / x100');

// ---- the fraction carry keeps the average exact -------------------------------------
for (const d of [168, 27, 399, 3, 5440, 11]) {
  let rem = 0.5, sum = 0; const n = 1000; const seen = new Set();
  for (let i = 0; i < n; i++) { const v = d * 0.1 + rem; const out = Math.trunc(v); rem = v - out; sum += out; seen.add(out); }
  ok(Math.abs(sum / n - d * 0.1) < 0.01, 'carry exact for ' + d);
  ok(seen.size <= 2, 'carry shows at most two neighbouring numbers for ' + d);
}
console.log(`POWER SCALE: ${checks} checks - horde = map 1 / 10 (r1 ${horde(1)}, r10 ${horde(10)}, r20 ${horde(20)}, r30 ${horde(30)}), front door scales player hits on enemies once, marks exempt + cleared, the live elites at map 1 / 10 (the Map One elites retired), crosshair exact, carry exact. PASS`);
