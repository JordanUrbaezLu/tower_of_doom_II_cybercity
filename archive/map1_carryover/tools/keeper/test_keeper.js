#!/usr/bin/env node
// test_keeper.js - the Keeper boss contract (docs/186), a build gate.
//
// Static checks on the files that must agree for the boss to load and for the
// soul lines to work. Each one names the failure it prevents:
//   1. server and client register the same two actor clientfields, same order,
//      bits and version            (a mismatch desyncs every clientfield index)
//   2. the behavior tree names only functions stock or _tod_keeper registers
//      (the pack's robot traversal functions are unregistered in this map)
//   3. the zone carries both scripts, the aitype, both models, every clip and
//      every effect the scripts precache            (the linker is silent on an
//      unzoned effect; the game plays nothing)
//   4. the aitype chain points at the tables the installer wrote
//   5. the user's numbers: 2 lines max, 15 s after a linked elite dies
//   6. the three buffs are READ where they take effect (stronger / aggressive /
//      tankier), and cleared by the Keeper's death
//   7. the arena spawns him on the last wave of the last level only
//   8. every clip in his anim mapping table is a clip we ship or a stock one
'use strict';
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const R = p => fs.readFileSync(path.join(REPO, p), 'utf8').replace(/\r\n/g, '\n');
const Z = 'scripts/zm/zm_tod2_cybercity/';
let fails = 0, passes = 0;
function ok(cond, what) {
  if (cond) { passes++; return; }
  fails++;
  console.log('FAIL ' + what);
}

const gsc = R(Z + '_tod_keeper.gsc');
const csc = R(Z + '_tod_keeper.csc');
const zone = R('zone_source/zm_tod2_cybercity.zone');
const zoneLines = new Set(zone.split('\n').map(l => l.trim()));

// 1. clientfields
const cf = t => [...t.matchAll(/clientfield::register\(\s*"(\w+)",\s*"(\w+)",\s*(\w+),\s*(\d+),\s*"(\w+)"/g)].map(m => m.slice(1, 6).join('|'));
ok(JSON.stringify(cf(gsc)) === JSON.stringify(cf(csc)) && cf(gsc).length === 2,
   '1 clientfields differ: server ' + JSON.stringify(cf(gsc)) + ' client ' + JSON.stringify(cf(csc)));
ok(/REGISTER_SYSTEM\(\s*"tod_keeper"/.test(gsc) && /REGISTER_SYSTEM\(\s*"tod_keeper"/.test(csc), '1 both halves register in a system __init__');
ok(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_keeper;/.test(R('scripts/zm/zm_tod2_cybercity.csc')), '1 the client entry #uses _tod_keeper.csc');
ok(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_keeper;/.test(R(Z + '_tod_main.gsc')) && /tod_keeper::init\(\)/.test(R(Z + '_tod_main.gsc')), '1 _tod_main #uses and inits _tod_keeper');

// 2. behavior tree functions
const bt = JSON.parse(R('share/raw/behavior/tod_keeper.ai_bt'));
const fns = new Set();
(function walk(n) {
  for (const k of ['scriptFunction', 'StartFunction', 'UpdateFunction', 'TerminateFunction', 'ActionName'])
    if (n[k]) fns.add(n[k].toLowerCase());
  (n.children || []).forEach(walk);
})(bt);
const STOCK = new Set(['disablerepath', 'enablerepath', 'locomotionshouldtraverse', 'startragdoll',
  'wascrushedbyinterdimensionalgunblackhole', 'waskilledbyinterdimensionalgun', 'zombiedeathaction',
  'zombiefindfleshservice', 'zombieidgundeathupdate', 'zombieshouldmelee', 'zombieshouldmove',
  'zombieshouldmoveaway', 'zombieshouldproceduraltraverse', 'zombieshouldstun', 'zombiestunactionend',
  'zombiestunactionstart', 'defaultaction', 'zombieidleaction', 'zombiemoveaction', 'zombiemoveaway',
  'zombietraverseaction']);   // registered by zombie.gsc / _zm_behavior / archetype_utility / archetype_locomotion_utility
const ours = new Set([...gsc.matchAll(/RegisterBehaviorTreeScriptAPI\(\s*"(\w+)"/g)].map(m => m[1].toLowerCase()));
for (const f of fns)
  ok(STOCK.has(f) || ours.has(f), '2 behavior tree names an unregistered function: ' + f);
ok(!/robot/i.test(JSON.stringify(bt)), '2 no robot traversal left in the tree');

// 3. zone
for (const l of ['scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_keeper.gsc', 'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_keeper.csc',
  'aitype,spawner_tod_keeper', 'xmodel,tod_keeper_body', 'xmodel,tod_keeper_dissolve'])
  ok(zoneLines.has(l), '3 zone line missing: ' + l);
const clips = fs.readdirSync(path.join(REPO, 'xanim_export/tod_keeper')).map(f => f.replace(/\.xanim_bin$/i, ''));
ok(clips.length === 82, '3 expected the 82 Keeper clips, found ' + clips.length);
for (const c of clips) ok(zoneLines.has('xanim,' + c), '3 clip not zoned: ' + c);
for (const t of [gsc, csc])
  for (const m of t.matchAll(/#precache\(\s*"(?:client_)?fx",\s*"([^"]+)"\s*\)/g))
    ok(zoneLines.has('fx,' + m[1]), '3 effect not zoned: ' + m[1]);
for (const m of gsc.matchAll(/#precache\(\s*"model",\s*"([^"]+)"\s*\)/g))
  ok(zoneLines.has('xmodel,' + m[1]), '3 model not zoned: ' + m[1]);

// 4. the GDT
const gdt = R('source_data/tod_keeper.gdt');
for (const t of ['tod_keeper.ai_am', 'tod_keeper.ai_ast', 'tod_keeper.ai_asm', 'tod_keeper.ai_bt'])
  ok(gdt.includes('"' + t + '"'), '4 aitype does not name ' + t);
for (const p of ['animtables/tod_keeper.ai_am', 'animtables/tod_keeper.ai_ast', 'share/raw/animstatemachines/tod_keeper.ai_asm', 'share/raw/behavior/tod_keeper.ai_bt'])
  ok(fs.existsSync(path.join(REPO, p)), '4 table missing on disk: ' + p);
ok(/"spawner_tod_keeper" \[ "variant_tod_keeper" \]/.test(gdt) && /"variant_tod_keeper" \[ "archetype_tod_keeper" \]/.test(gdt)
   && /"archetype_tod_keeper" \( "aitype.gdf" \)/.test(gdt), '4 the aitype chain archetype -> variant -> spawner');
ok(/"character1" "c_tod_keeper"/.test(gdt) && /"body" "tod_keeper_body"/.test(gdt), '4 the character wears tod_keeper_body');

// 5. the user's numbers
const def = (t, n) => { const m = t.match(new RegExp('#define\\s+' + n + '\\s+([\\d.]+)')); return m ? Number(m[1]) : NaN; };
ok(def(gsc, 'TOD_KEEPER_LINKS_MAX') === 2, '5 "He can have 2 max"');
ok(def(gsc, 'TOD_KEEPER_RELINK_MS') === 15000, '5 "15 seconds to cast another soul line once that elite is killed"');
ok(/s\.ready_ms = now \+ TOD_KEEPER_RELINK_MS;/.test(gsc), '5 the relink window starts when the linked elite dies');
ok(def(gsc, 'TOD_KEEPER_LINK_DMG') > 1 && def(gsc, 'TOD_KEEPER_LINK_RATE') > 1 && def(gsc, 'TOD_KEEPER_LINK_DR') < 1,
   '5 a line makes an elite stronger (>1), faster (>1) and tankier (<1)');

// 6. the three buffs are read, and cleared on his death
ok(/eAttacker\.tod_keeper_dmg/.test(R(Z + '_tod_bosses.gsc')), '6 STRONGER: boss_player_damage reads tod_keeper_dmg');
ok(/self\.tod_keeper_dr/.test(R(Z + '_tod_power_scale.gsc')), '6 TANKIER: the power-scale front door reads tod_keeper_dr');
ok(/tod_keeper_rate/.test(R(Z + '_tod_mangler.gsc')), '6 AGGRESSIVE: the Mangler chase reads tod_keeper_rate');
ok(/tod_keeper_rate/.test(R(Z + '_tod_doppelghast.gsc')), '6 AGGRESSIVE: the Doppelghast chase reads tod_keeper_rate');
const brk = (gsc.match(/function break_all\([\s\S]*?\n\}/) || [''])[0];
for (const f of ['tod_keeper_dmg', 'tod_keeper_rate', 'tod_keeper_dr', 'tod_keeper_link_by'])
  ok(brk.includes('e.' + f + ' = undefined'), '6 break_all clears ' + f);
ok(/break_all\(\s*"keeper_died"\s*\)/.test(gsc), '6 the Keeper\'s death breaks every line');

// 7. the arena
const arena = R(Z + '_tod_arena.gsc');
ok(/if \( lvl >= TOD_ARENA_LEVELS && w == TOD_ARENA_WAVES \)\n\t\t\tboss_wave\( lvl, w \);/.test(arena), '7 the boss wave is the last wave of the last level only');
ok(/tod_keeper::spawn_boss\(/.test(arena) && /keeper\.tod_arena = true;/.test(arena) && /track\( keeper \);/.test(arena),
   '7 the arena spawns, marks and tracks him (the wave waits for him)');
ok(/IS_TRUE\( ai\.tod_arena \)/.test(gsc), '7 he links only the arena\'s own elites');

// 8. every mapped clip ships or is stock
const am = R('animtables/tod_keeper.ai_am');
const mapped = new Set(am.split('\n').slice(1).flatMap(l => l.split(',').slice(1)).map(s => s.trim()).filter(Boolean));
const inGdt = new Set([...gdt.matchAll(/^\t"([^"]+)" \( "xanim\.gdf" \)/gm)].map(m => m[1]));
for (const c of mapped)
  ok(inGdt.has(c) || /^ai_zombie_base_/.test(c) || c === 'void', '8 mapped clip is neither ours nor stock base: ' + c);

console.log((fails ? 'KEEPER CONTRACT FAILED: ' + fails + ' failure(s), ' : 'KEEPER CONTRACT OK: ') + passes + ' checks passed');
process.exit(fails ? 1 : 0);
