#!/usr/bin/env node
'use strict';
// =============================================================================
// tools/test_dealer_house.js - THE DEALER'S HOUSE gate (docs/207, user 2026-10-04).
//
// The Battle Arena's last level is the final fight in the Dealer's two rooms: THE PARLOUR (the Black
// Market box, the cut scene, THE LAST ROLL, the laugh) and THE HOUSE (the drain to one health under
// his corrupted dome, the two-state fight). This gate proves, before a build:
//   1. THE ROOMS     the layout module loads and proves itself; the GENERATED _tod_house_data.gsc is
//                    exactly what it writes (a stale regen fails); the generated functions answer
//                    through gsc_eval (arrivals on the dais, the gates in the pit, the bounds); both
//                    rooms are in the .map, labelled for the lints; each room's air reaches the void
//                    at every arrival / gate / probe (a sealed room renders invisible), with a lidded
//                    negative control per room.
//   2. THE FLOW      _tod_house.gsc: the pure pieces run (the drain's line, the farthest gate, the
//                    shield verdict, the 2D line set); the sequence is parlour -> dome and drain ->
//                    fight -> end; every freeze / shield / hold / dome / trigger / shop has its undo in
//                    release() + end(); the damage guard sits first; every line it says is a dealer
//                    line with a shipped wav, an alias row and a length in the GENERATED table; the
//                    letterbox keep-alive beat exists in TodJumpCine.
//   3. THE ARENA     _tod_arena.gsc branches to the house after hold_tower on the last level (and only
//                    there), hands the readout push + watch through level pointers, the fall guard
//                    covers the house, the ride home charges from level.tod_arena_depart, the HOUSE /
//                    DEALER flags are LOCKSTEP with TodArena.lua and _tod_house's WAVE bit.
//   4. THE LAST ROLL _tod_shop.gsc: the CURSED tile and code are LOCKSTEP with TodSpinReel.lua, the
//                    reel runs on every player with one seed, lands with the cursed code, pays nothing,
//                    sockets nothing; the cycler and the voice watchers sleep under the hold; the three
//                    cursed images are generated, in the GDT, zoned and named by the reel.
//   5. THE WIRING    the two zones in the entry script, the zone lines, the cue csv in the zone config,
//                    the dealer's hold + hooks, the test spawn off, the arena-region readers, the lints
//                    (islands, navmesh, model clip columns), the build steps, the hint route.
//   2b. THE BARKS    (PK14 / W2B) his voice between the story lines: the scythe calls (state one, a landed hit,
//                    sometimes), the chase taunts (state two, on a clock), the low line (once); a deck never repeats
//                    the line just said, a bark never starts over a line still speaking, the crack and the death cut
//                    any bark and come a beat AFTER his sound (the mask's crack, the death scream), never over it.
//   6. MUTANTS       a gate that cannot fail is not a gate: every clause is broken once and must be caught.
//
// Usage: node tools/test_dealer_house.js   (exit 1 on any failure; build_map.ps1 runs it)
// =============================================================================
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8').replace(/\r\n/g, '\n');
const exists = rel => fs.existsSync(path.join(ROOT, rel));
const { gscLoad, V } = require('./sky_ships/gsc_eval.js');
const cb = require('./convex_brush.js');

const S = 'scripts/zm/zm_tod2_cybercity/';
const HOUSE = read(S + '_tod_house.gsc');
const DATA = read(S + '_tod_house_data.gsc');
const ARENA = read(S + '_tod_arena.gsc');
const ARENA_DATA = read(S + '_tod_arena_data.gsc');
const SHOP = read(S + '_tod_shop.gsc');
const DEALER = read(S + '_tod_dealer_finale.gsc');
const ENTRY = read('scripts/zm/zm_tod2_cybercity.gsc');
const REEL = read('ui/uieditor/widgets/HUD/AetheriumWidgets/TodSpinReel.lua');
const TODARENA = read('ui/uieditor/widgets/HUD/AetheriumWidgets/TodArena.lua');
const TODHAVEN = read('ui/uieditor/widgets/HUD/AetheriumWidgets/TodHaven.lua');
const CINE = read('ui/uieditor/widgets/HUD/AetheriumWidgets/TodJumpCine.lua');
const ZONE = read('zone_source/zm_tod2_cybercity.zone');
const GDT = read('source_data/tod_ui_images.gdt');
const BUILD = read('tools/build_map.ps1');
const MAP = read('map_source/zm/zm_tod2_cybercity.map');
const GEOM_LINT = read('tools/lint_tod_geometry.js');
const NAV_LINT = read('tools/lint_tod_navmesh.js');
const SHOP_CSV = read('sound/aliases/tod_shop.csv');
const HOUSE_CSV = read('sound/aliases/tod_house.csv');
const SZC = read('sound/zoneconfig/zm_tod2_cybercity.szc');
const VO_TABLE = read(S + '_tod_shop_vo.gsc');
const LINES = JSON.parse(read('tools/black_market_vo/lines.json')).lines;
const LAYOUT = require('./dealer_house_layout.js');

let fails = 0, checks = 0;
function check(ok, label) { checks++; if (!ok) { fails++; console.log('FAIL ' + label); } }
const defs = text => Object.fromEntries([...text.matchAll(/^#define\s+(\w+)\s+(-?[\d.]+)/gm)].map(m => [m[1], m[2]]));
const body = (text, name) => { const m = text.match(new RegExp('^function ' + name + '\\([^)]*\\)\\s*\\n\\{([\\s\\S]*?)\\n\\}', 'm')); return m ? m[1] : null; };
const IS_TRUE = x => !!x && x !== 0;

// ---------------------------------------------------------------------------
// 1. THE ROOMS
// ---------------------------------------------------------------------------
check(DATA === LAYOUT.dataGsc(), 'the GENERATED _tod_house_data.gsc is exactly what the layout writes (regen: node tools/gen_tower_map.js)');
check(LAYOUT.HOUSE.half > require('./battle_arena_layout.js').ARENA.half, 'the house is bigger than the arena (user: "slightly bigger")');
check(LAYOUT.PARLOUR.half * 2 <= 768 && LAYOUT.PARLOUR.height <= 400, 'the parlour is a small box');
const g = gscLoad([['tod_house', HOUSE], ['tod_house_data', DATA], ['tod_arena_data', ARENA_DATA]], defs(HOUSE), { builtins: { IS_TRUE,
  Distance: (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]) } });
{
  const arr = g.call('tod_house_data::house_arrivals', []), dais = g.call('tod_house_data::house_dais', []);
  check(arr.length === 4 && arr.every(a => a[2] === dais[2] && g.call('tod_house_data::on_house_dais', [a])), 'the 4 house arrivals stand on the dais top');
  const gates = g.call('tod_house_data::house_gates', []);
  check(gates.length === 4 && gates.every(p => g.call('tod_house_data::in_house', [p]) && !g.call('tod_house_data::on_house_dais', [p])), 'the 4 gates are in the house, off the dais');
  const par = g.call('tod_house_data::parlour_arrivals', []);
  check(par.length === 4 && par.every(p => g.call('tod_house_data::in_parlour', [p]) && !g.call('tod_house_data::in_house', [p])), 'the 4 parlour arrivals are in the parlour, not the house');
  check(!g.call('tod_house_data::in_house', [V(0, 0, 0)]) && !g.call('tod_house_data::in_parlour', [V(0, 0, 0)]), 'the tower is in neither room');
  check(!g.call('tod_arena_data::in_arena', [dais]) && !g.call('tod_house_data::in_house', [g.call('tod_arena_data::arena_dais', [])]), 'the house and the arena are different rooms');
  check(g.call('tod_house_data::house_mood_orgs', []).length === 5, 'five mood hosts (four pylons, the dais last)');
  check(g.call('tod_house_data::house_nav_probes', []).every(p => g.call('tod_house_data::in_house', [p])), 'every surface probe is inside the house');
  const counter = g.call('tod_house_data::parlour_counter', []), shop = g.call('tod_house_data::parlour_shop_org', []);
  check(Math.abs(counter[1] - (shop[1] - 96)) < 1e-6 && counter[0] === shop[0], 'the last roll stands TOD_SPIN_TRIG_OUT (96) before the counter');
}
check(/^\/\/ brush \d+ — dealer parlour floor$/m.test(MAP) && /^\/\/ brush \d+ — dealer house floor$/m.test(MAP), 'both rooms are in the generated .map (their floors)');
check(/^\/\/ brush \d+ — dealer parlour shop hull 0$/m.test(MAP), 'the hut\'s hull clips are in the .map');
check(/targetname" "house_parlour_zone"/.test(MAP) && /targetname" "house_zone"/.test(MAP), 'both zones are in the .map');

// 1b. THE ROOMS' AIR REACHES THE VOID (the arena gate's flood, per room)
for (const [name, probes, lid] of [
  ['dealer parlour', [...LAYOUT.P_ARRIVALS.map(p => ['arrival', p]), [`counter`, LAYOUT.P_COUNTER]], { A: LAYOUT.PARLOUR, O: LAYOUT.POUTER, gap: LAYOUT.PVENT.gap }],
  ['dealer house', [...LAYOUT.H_ARRIVALS.map(p => ['arrival', p]), ...LAYOUT.H_GATES.map(p => ['gate', p]), ...LAYOUT.H_PROBES.map(p => ['probe', p])], { A: LAYOUT.HOUSE, O: LAYOUT.HOUTER, gap: LAYOUT.HVENT.gap }],
]) {
  const VX = 4;
  const solids = [];
  for (const m of MAP.matchAll(new RegExp('\\/\\/ brush \\d+ — (' + name + '[^\\n]*)\\n\\{([\\s\\S]*?)\\n\\}', 'g'))) {
    const planes = cb.readPlanes(m[2]);
    if (planes.length < 4 || planes.every(p => /clip/i.test(p.mat))) continue;
    const h = cb.hull(planes);
    solids.push({ planes, lo: h.lo, hi: h.hi });
  }
  check(solids.length > 30, `${name}: its visible brushes are in the generated .map (${solids.length})`);
  const lo = [0, 1, 2].map(i => Math.floor((Math.min(...solids.map(b => b.lo[i])) - 2 * VX) / VX) * VX);
  const hi = [0, 1, 2].map(i => Math.ceil((Math.max(...solids.map(b => b.hi[i])) + 2 * VX) / VX) * VX);
  const [NX, NY, NZ] = [0, 1, 2].map(i => (hi[i] - lo[i]) / VX);
  const at = (x, y, z) => (z * NY + y) * NX + x;
  const base = new Uint8Array(NX * NY * NZ);
  for (const b of solids) {
    const P = b.planes.map(p => [p.n[0], p.n[1], p.n[2], p.d - 0.01 + VX / 2 * (Math.abs(p.n[0]) + Math.abs(p.n[1]) + Math.abs(p.n[2]))]);
    const i0 = [0, 1, 2].map(i => Math.max(0, Math.floor((b.lo[i] - lo[i]) / VX) - 1));
    const i1 = [0, 1, 2].map(i => Math.min([NX, NY, NZ][i] - 1, Math.ceil((b.hi[i] - lo[i]) / VX)));
    for (let z = i0[2]; z <= i1[2]; z++) { const cz = lo[2] + (z + 0.5) * VX;
      for (let y = i0[1]; y <= i1[1]; y++) { const cy = lo[1] + (y + 0.5) * VX;
        for (let x = i0[0]; x <= i1[0]; x++) { const cx = lo[0] + (x + 0.5) * VX;
          let k = 0; while (k < P.length && P[k][0] * cx + P[k][1] * cy + P[k][2] * cz < P[k][3]) k++;
          if (k === P.length) base[at(x, y, z)] = 1; } } }
  }
  const Q = new Int32Array(1 << 24);
  function voidAir(solid) {
    const lab = Uint8Array.from(solid); let head = 0, tail = 0;
    const push = k => { if (lab[k]) return; lab[k] = 2; Q[tail] = k; tail = (tail + 1) & (Q.length - 1); if (tail === head) throw new Error('air flood: queue overflow'); };
    for (let z = 0; z < NZ; z++) for (let y = 0; y < NY; y++) for (let x = 0; x < NX; x++) if (!x || !y || !z || x === NX - 1 || y === NY - 1 || z === NZ - 1) push(at(x, y, z));
    while (head !== tail) { const k = Q[head]; head = (head + 1) & (Q.length - 1); const x = k % NX, y = Math.floor(k / NX) % NY, z = Math.floor(k / (NX * NY));
      if (x > 0) push(k - 1); if (x < NX - 1) push(k + 1); if (y > 0) push(k - NX); if (y < NY - 1) push(k + NX); if (z > 0) push(k - NX * NY); if (z < NZ - 1) push(k + NX * NY); }
    return lab;
  }
  const cell = p => at(...[0, 1, 2].map(i => Math.floor((p[i] + (i === 2 ? 40 : 0) - lo[i]) / VX)));
  const open = voidAir(base);
  const sealed = probes.filter(([, p]) => open[cell(p)] !== 2);
  check(sealed.length === 0, `${name}: the room's air reaches the void at all ${probes.length} points (a sealed room renders invisible)` + sealed.slice(0, 3).map(([k, p]) => `; ${k} ${p.map(Math.round)} ${open[cell(p)] === 1 ? 'inside a solid' : 'SEALED'}`).join(''));
  const lidded = Uint8Array.from(base);
  const z0 = Math.floor((lid.A.z + lid.A.height - lo[2]) / VX), z1 = Math.ceil((lid.A.z + lid.A.height + lid.gap - lo[2]) / VX);
  const x0 = Math.floor((lid.A.cx - lid.O - lo[0]) / VX), x1 = Math.ceil((lid.A.cx + lid.O - lo[0]) / VX), y0 = Math.floor((lid.A.cy - lid.O - lo[1]) / VX), y1 = Math.ceil((lid.A.cy + lid.O - lo[1]) / VX);
  for (let z = z0; z < z1; z++) for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) lidded[at(x, y, z)] = 1;
  const shut = voidAir(lidded);
  check(probes.every(([, p]) => shut[cell(p)] !== 2), `${name}: negative control - the roof slot lidded, the flood finds the room sealed`);
}

// ---------------------------------------------------------------------------
// 2. THE FLOW (_tod_house.gsc)
// ---------------------------------------------------------------------------
const D = defs(HOUSE);
{
  const steps = +D.TOD_HOUSE_DRAIN_STEPS;
  const t = (hp0, s) => g.call('drain_target', [hp0, s, steps]);
  check(t(100, 0) === 100 && t(100, steps) === 1 && t(250, steps) === 1, 'drain_target: full at step 0, ONE at the last step');
  let mono = true; for (let s = 1; s <= steps; s++) if (t(100, s) > t(100, s - 1)) mono = false;
  check(mono && t(100, 5) < 100 && t(100, 5) > 1, 'drain_target never climbs and never reaches one early');
  check(t(1, 3) === 1 && t(100, steps + 7) === 1 && t(100, 4) >= 1, 'drain_target floors at one (a player already at one, a step past the end)');
  check(g.call('shield_verdict', [true]) === true && g.call('shield_verdict', [false]) === false && g.call('shield_verdict', [undefined]) === false, 'shield_verdict reads the flag');
  const gates = [V(100, 0, 0), V(-100, 0, 0), V(0, 100, 0), V(0, -100, 0)];
  const far = g.call('farthest_gate', [gates, [V(90, 5, 0), V(80, -5, 0)]]);
  check(far[0] === -100 && far[1] === 0, 'farthest_gate: he comes in from across the pit');
  check(g.call('farthest_gate', [gates, []])[0] === 100 && g.call('farthest_gate', [[], [V(0, 0, 0)]]) === undefined, 'farthest_gate: no party -> the first gate; no gates -> undefined');
  check(g.call('line_is_2d', ['tod_house_vo_dome']) === true && g.call('line_is_2d', ['tod_house_vo_welcome']) === false, 'the arena lines are 2D, the parlour lines are from the mask');
}
const run = body(HOUSE, 'run');
check(!!run && run.indexOf('parlour( lvl, op )') < run.indexOf('dome_and_drain()') && run.indexOf('dome_and_drain()') < run.indexOf('won = fight()') && run.indexOf('won = fight()') < run.indexOf('end()'), 'run(): parlour -> dome and drain -> fight -> end');
check(!!run && /zm_zonemgr::enable_zone\( pz \)/.test(run) && /zm_zonemgr::enable_zone\( hz \)/.test(run) && /is_spawning_allowed = false/.test(run), 'run() enables both zones before anyone moves and lets nothing spawn in them');
check(!!run && /level\.tod_trial_box = house_box\(\)/.test(run) && /level\.tod_arena_active = true/.test(run) && /level\.tod_arena_depart = tod_house_data::house_dais\(\)/.test(run), 'run() holds the elites, marks the arena active and sets the ride home\'s departure');
check(!!run && /return false;/.test(run) && run.indexOf('return false;') < run.indexOf('zm_zonemgr::enable_zone( pz )'), 'a missing zone refuses before anyone moves (the caller refunds)');
const par = body(HOUSE, 'parlour');
check(!!par && par.indexOf('tod_atmosphere::channel_stop()') < par.indexOf('house_shop_begin') && par.indexOf('cine_begin()') < par.indexOf('tod_house_vo_welcome') && par.indexOf('tod_house_vo_offer') < par.indexOf('cine_end()'),
  'the parlour: silence, the counter lights, the scene opens before the first line and closes after the offer');
check(!!par && par.indexOf('roll_wait()') < par.indexOf('tod_shop::house_roll( roller, party )') && par.indexOf('house_roll( roller, party )') < par.indexOf('tod_house_vo_cursed') && par.indexOf('tod_house_vo_cursed') < par.indexOf('tod_house_vo_laugh') && par.indexOf('tod_house_vo_laugh') < par.indexOf('house_roll_end( party )') && par.indexOf('house_roll_end( party )') < par.indexOf('tod_house_vo_send'),
  'the last roll: the offer, the reel, CURSED, the laugh over the banner, the panel drops, the send');
check(!!par && /menu_freeze\( true \)/.test(par) && par.indexOf('menu_freeze( true )') < par.indexOf('house_roll( roller, party )'), 'everyone is frozen for the reel');
check(!!par && /tod_teleport::fx_burst\( "tod_tp_charge"/.test(par) && /wait TOD_HOUSE_SEND_SECS;/.test(par) && par.indexOf('wait TOD_HOUSE_SEND_SECS;') < par.indexOf('tod_teleport::discharge( charge_org )'), 'the send is the transit pads\' beat: charge, wait, discharge');
check(/level thread tod_teleport::fx_burst/.test(HOUSE) && !/^\t+tod_teleport::fx_burst\(/m.test(HOUSE), 'every fx_burst is threaded (an inline one is a delay: the arena v1 lesson)');
const dd = body(HOUSE, 'dome_and_drain');
check(!!dd && /SetScale\( TOD_HOUSE_DOME_SCALE \)/.test(dd) && /"tod_haven_dome_dark_flash"/.test(dd) && /"tod_haven_dome_dark"/.test(dd) && /TOD_HOUSE_SND_HUM, 1/.test(dd) && /TOD_HOUSE_FX_CORRUPT/.test(dd),
  'the dome is the haven\'s corrupted field: the flash skin, the stutter, the dark skin, the hum, the red fx, scaled up');
check(!!dd && /level\.tod_house_shield = true;/.test(dd) && /EnableInvulnerability\(\)/.test(dd) && /LuiNotifyEvent\( &"tod_haven", 4, 1, 0, 1, 0 \)/.test(dd) && /TOD_HOUSE_SND_DARK_IN/.test(dd),
  'the darkness: the shield, invulnerability, the haven HUD\'s CORRUPTED state and the swallow on every player');
check(!!dd && dd.indexOf('level thread say_all_now( "tod_house_vo_dome" )') < dd.indexOf('drain();') && dd.indexOf('drain();') < dd.indexOf('say_all( "tod_house_vo_one" )'), 'he talks over the drain; ONE after it');
check(!!dd && /menu_freeze\( true \)/.test(dd), 'the party stays frozen for the dome');
const drain = body(HOUSE, 'drain');
check(!!drain && /LuiNotifyEvent\( &"tod_house_cut", 1, 1 \)/.test(drain) && /TOD_HOUSE_SND_CUT/.test(drain) && /TOD_HOUSE_SND_DRAIN/.test(drain) && /hold_at\( p, s - 1 \)/.test(drain), 'every cut flickers and bites; the line is held between cuts');
check(/function hold_one\(\)[\s\S]*level endon\( "tod_house_release" \)/.test(HOUSE), 'the one-health hold ends at the release');
const fight = body(HOUSE, 'fight');
check(!!fight && /level\.tod_dealer_hold = true;/.test(fight) && fight.indexOf('level.tod_dealer_hold = true;') < fight.indexOf('spawn_boss( gate, target )'), 'he is held before he spawns');
check(!!fight && /farthest_gate\( tod_house_data::house_gates\(\), orgs \)/.test(fight), 'he rises at the gate farthest from the party');
check(!!fight && /DEALER_NOSHOW/.test(fight) && fight.indexOf('DEALER_NOSHOW') < fight.indexOf('return true;') && /release\(\);/.test(fight.slice(fight.indexOf('DEALER_NOSHOW'), fight.indexOf('return true;'))), 'a Dealer who never comes is logged and the party is never stranded');
check(!!fight && fight.indexOf('tod_house_vo_fight') < fight.indexOf('release();', fight.indexOf('tod_house_vo_fight')) && fight.indexOf('level thread dome_break()', fight.indexOf('DEALER_NOSHOW') + 20) < fight.indexOf('say_all( "tod_house_vo_fight" )'),
  'the fight line: the dome breaks under it, the release at its end');
check(!!fight && /hud\( TOD_HOUSE_HUD_WAVE \)/.test(fight) && /tod_atmosphere::arena_music_start\(\)/.test(fight) && /TOD_HOUSE_SND_HORN/.test(fight) && /level thread mood_on\(\)/.test(fight), 'the fight starts with the readout, the horn, the boss track and the mood lights');
check(!!fight && /while \( isdefined\( dealer \) && IsAlive\( dealer \) \)\s*\n\s*wait 0\.5;/.test(fight), 'the fight waits for his death (or his loss) by polling, never a notify alone');
const rel = body(HOUSE, 'release');
check(!!rel && /level\.tod_house_shield = false;/.test(rel) && /level\.tod_dealer_hold = false;/.test(rel) && /level notify\( "tod_house_release" \)/.test(rel) && /menu_freeze\( false \)/.test(rel) && /DisableInvulnerability\(\)/.test(rel),
  'release(): the shield, the hold, the one-health line, the freeze and the invulnerability all let go');
check(!!rel && /pause_invuln_held_elsewhere\(\)/.test(rel) && /tod_spin_locked/.test(rel), 'release() never strips an invulnerability another owner holds');
const end = body(HOUSE, 'end');
check(!!end && /cine_end\(\)/.test(end) && /darkness_off\( p \)/.test(end) && /tod_shop::house_shop_end\(\)/.test(end) && /dome_break\(\)/.test(end) && /tod_house_roll_trig/.test(end) && /level\.tod_house_shield = false;/.test(end) && /level\.tod_dealer_hold = undefined;/.test(end),
  'end(): the scene, the darkness, the counter, the dome, the trigger, the shield and the hold are all undone');
const ce = body(HOUSE, 'cine_end'), cbg = body(HOUSE, 'cine_begin');
check(!!cbg && /PlayerLinkToDelta\( mover, "tag_origin", 1, TOD_HOUSE_CINE_YAW, TOD_HOUSE_CINE_YAW, TOD_HOUSE_CINE_PITCH, TOD_HOUSE_CINE_PITCH \)/.test(cbg) && /menu_freeze\( true \)/.test(cbg) && /HideViewModel\(\)/.test(cbg) && /LuiNotifyEvent\( &"tod_jump_cine", 1, 1 \)/.test(cbg),
  'the scene: the soft freeze, the view locked on the mask with room to breathe, the gun down, the letterbox');
check(!!ce && /Unlink\(\)/.test(ce) && /ShowViewModel\(\)/.test(ce) && /menu_freeze\( false \)/.test(ce) && /LuiNotifyEvent\( &"tod_jump_cine", 1, 0 \)/.test(ce) && /if \( !IS_TRUE\( self\.tod_house_cine \) \)\s*\n\s*return;/.test(ce), 'cine_end undoes all of it, once');
check(/LuiNotifyEvent\( &"tod_jump_cine", 1, 3 \)/.test(HOUSE) && /elseif d\[ 1 \] == 3 then[\s\S]*Watch:beginAnimation\( "tod_jump_watch", WATCHDOG_MS/.test(CINE), 'the letterbox keep-alive: the 3 beat re-arms TodJumpCine\'s watchdog');
check(+D.TOD_HOUSE_CINE_KEEP_SECS < 17, 'the keep-alive beats faster than the letterbox watchdog (17 s)');
check(/ArrayInsert\( level\.player_damage_callbacks, &house_damage_guard, 0 \)/.test(HOUSE) && /function house_damage_guard[\s\S]*?return 0;/.test(HOUSE), 'the damage guard is installed first and eats everything under the shield');
check(/level\.tod_dealer_crack_fn = &on_crack;/.test(HOUSE) && /level\.tod_dealer_death_fn = &on_death;/.test(HOUSE), 'the dealer\'s voice hooks are installed');
check(/^#define TOD_HOUSE_LOG\s+\d/m.test(HOUSE) && /#precache\( "eventstring", "tod_house_cut" \)/.test(HOUSE) && /#precache\( "eventstring", "tod_haven" \)/.test(HOUSE) && /#precache\( "eventstring", "tod_jump_cine" \)/.test(HOUSE), 'the log switch and the three eventstrings are declared');
check(/SetHintString\( TOD_HOUSE_HINT_ROLL \)/.test(HOUSE) && /^#define TOD_HOUSE_HINT_ROLL\s+"Hold \^3\[\{\+activate\}\]\^7 \^5BLACK MARKET\^7 - /m.test(HOUSE), 'the last roll\'s one constant prompt leads with the BLACK MARKET noun');
// every line he says exists, is shipped, has its row and its length
const said = [...new Set([...HOUSE.matchAll(/"(tod_house_vo_\w+)"/g)].map(m => m[1]))];
const byFile = Object.fromEntries(LINES.map(l => [l.file, l]));
check(said.length >= 12, `the house says ${said.length} lines`);
for (const a of said) {
  check(byFile[a] && byFile[a].group === 'house', `line ${a} is in lines.json (group house)`);
  check(exists('sound_assets/tod/sfx/' + a + '.wav'), `line ${a} is shipped`);
  check(new RegExp('^' + a + ',').test(SHOP_CSV.replace(/\r/g, '')) || SHOP_CSV.includes('\n' + a + ','), `line ${a} has its alias row`);
  check(new RegExp('case "' + a + '": return [\\d.]+;').test(VO_TABLE), `line ${a} has its length in the GENERATED table`);
  const is2d = g.call('line_is_2d', [a]);
  check(!!byFile[a] && ((byFile[a].pan === '2d') === !!is2d), `line ${a}: ${is2d ? '2D' : '3D'} in the script matches its row`);
}
check(LINES.filter(l => l.group === 'house').every(l => !/whisper/i.test(l.text)), 'no whispered line (the voice rule)');
check(/^#define TOD_HOUSE_HUD_WAVE\s+(\d+)/m.test(HOUSE) && HOUSE.match(/^#define TOD_HOUSE_HUD_WAVE\s+(\d+)/m)[1] === defs(ARENA).TOD_ARENA_HUD_WAVE, 'LOCKSTEP: the house\'s WAVE bit is the arena\'s');

// ---------------------------------------------------------------------------
// 2b. THE BARKS (PK14 / W2B): his voice between the story lines, never over them
// ---------------------------------------------------------------------------
{
  const gb = gscLoad([['tod_house', HOUSE], ['tod_house_data', DATA], ['tod_arena_data', ARENA_DATA]], defs(HOUSE), { builtins: { IS_TRUE } });
  const swipes = gb.call('swipe_lines', []), taunts = gb.call('taunt_lines', []);
  check(swipes.length === 3 && taunts.length === 4, `three scythe calls and four chase taunts (${swipes.length} / ${taunts.length})`);
  check(swipes.every(a => byFile[a] && byFile[a].pan === '2d' && byFile[a].mode !== 'manic') && taunts.every(a => byFile[a] && byFile[a].pan === '2d' && byFile[a].mode === 'manic'),
    'the scythe calls are the soft register, the taunts the manic one, all 2D (his voice in the arena)');
  check(!!byFile['tod_house_vo_low'] && byFile['tod_house_vo_low'].pan === '2d' && /"tod_house_vo_low"/.test(HOUSE), 'the low line exists, 2D, and is said');
  // the deck: never the line just said, every line once before any repeats
  const said = {};
  let last, seen = new Set(), repeats = 0;
  for (let k = 0; k < 4; k++) {
    const i = gb.call('deck_pick', [said, 4, last, k * 7 + 3]);
    if (i === last) repeats++;
    seen.add(i); said[i] = true; last = i;
  }
  check(seen.size === 4 && repeats === 0, 'deck_pick: four draws of a four-line deck say all four, never the same twice running');
  check(gb.call('deck_pick', [{ 0: true, 1: true, 2: true }, 3, 2, 5]) !== 2, 'deck_pick: a spent deck starts a new cycle without the line just said');
  // the quiet: never inside the bark gap, never within the quiet of a line still on a lane
  check(gb.call('bark_quiet', [10000, 12000, [], 2500]) === false && gb.call('bark_quiet', [10000, 9000, [9000], 2500]) === false && gb.call('bark_quiet', [10000, 9000, [5000], 2500]) === true,
    'bark_quiet: no bark inside the gap or within the quiet after a line; free once both have passed');
  // the scythe call's verdict
  const sv = (...a) => gb.call('swipe_verdict', a);
  check(sv(1, false, 100, 20, 50000, 0, 0) === 'ok' && sv(2, false, 100, 20, 50000, 0, 0) === 'state' && sv(1, true, 100, 20, 50000, 0, 0) === 'held'
    && sv(1, false, 20, 30, 50000, 0, 0) === 'lethal' && sv(1, false, 100, 20, 50000, 60000, 0) === 'gap' && sv(1, false, 100, 20, 50000, 0, 99) === 'chance',
    'swipe_verdict: state one only, never held, never a hit that may down (the down line owns it), never inside the gap, then the chance');
  check(gb.call('low_due', [false, 19, 100]) === true && gb.call('low_due', [true, 19, 100]) === false && gb.call('low_due', [false, 50, 100]) === false && gb.call('low_due', [false, 0, 100]) === false,
    'low_due: once, at a fifth of his health, while he lives');
  const guard = body(HOUSE, 'house_damage_guard'), fightB = body(HOUSE, 'fight'), bw = body(HOUSE, 'bark_watch');
  check(!!guard && /level thread swipe_bark\( eAttacker, self, sMeansOfDeath, iDamage \);/.test(guard) && guard.indexOf('swipe_bark') < guard.indexOf('shield_verdict'),
    'the damage guard hears his landed hits (threaded, before the shield verdict: it never changes what the guard returns)');
  check(!!fightB && /level thread bark_watch\( dealer \);/.test(fightB), 'the fight arms the barks');
  check(!!bw && /if \( IS_TRUE\( level\.tod_upgrade_pause \) \|\| IS_TRUE\( level\.tod_dealer_hold \) \)/.test(bw) && /dealer\.tod_dealer_state != 2/.test(bw)
    && /TOD_HOUSE_CRACK_LINE_DELAY \+ tod_shop_vo::secs\( "tod_house_vo_crack" \) \+ TOD_HOUSE_TAUNT_FIRST/.test(bw),
    'bark_watch: quiet under a card deal and the hold, taunts only in state two, the first one after the crack line has been said');
  const oc = body(HOUSE, 'on_crack'), od = body(HOUSE, 'on_death'), sla = body(HOUSE, 'story_line_after');
  check(!!oc && oc.indexOf('bark_yield( "crack" )') >= 0 && /level thread story_line_after\( "tod_house_vo_crack", TOD_HOUSE_CRACK_LINE_DELAY, "crack" \);/.test(oc),
    'the crack cuts a bark at once and says its line a beat after the mask\'s crack and shriek');
  check(!!od && od.indexOf('bark_yield( "death" )') >= 0 && /level\.tod_house_swipes = undefined;/.test(od) && /level thread story_line_after\( "tod_house_vo_death", TOD_HOUSE_DEATH_LINE_DELAY, "death" \);/.test(od),
    'the death ends the barks, cuts one still speaking, and says his last words after the death scream');
  check(!!sla && sla.indexOf('wait secs;') < sla.indexOf('bark_yield( why );') && sla.indexOf('bark_yield( why );') < sla.indexOf('say_all_now( alias );'),
    'story_line_after: the beat, then whatever bark started in it is cut, then the line');
  check(+D.TOD_HOUSE_CRACK_LINE_DELAY > 0.3 && +D.TOD_HOUSE_CRACK_LINE_DELAY < 1.5 && +D.TOD_HOUSE_DEATH_LINE_DELAY > 0.5 && +D.TOD_HOUSE_DEATH_LINE_DELAY < 2.0,
    `the beats are short (crack ${D.TOD_HOUSE_CRACK_LINE_DELAY} s, death ${D.TOD_HOUSE_DEATH_LINE_DELAY} s): his words follow his sound, they never wait on it`);
  const by = body(HOUSE, 'bark_yield');
  check(!!by && /StopLocalSound\( p\.tod_house_bark \)/.test(by) && /p\.tod_house_vo_until = undefined;/.test(by), 'bark_yield stops the bark on the lane and frees the lane');
  check(/p\.tod_house_bark = undefined;/.test(body(HOUSE, 'say_to')), 'a story line takes the lane back from a bark (say_to unmarks it)');
}

// ---------------------------------------------------------------------------
// 3. THE ARENA (_tod_arena.gsc)
// ---------------------------------------------------------------------------
const AD = defs(ARENA);
const arun = body(ARENA, 'arena_run');
check(!!arun && arun.indexOf('held = hold_tower();') < arun.indexOf('tod_house::run( lvl, op )') && arun.indexOf('tod_house::run( lvl, op )') < arun.indexOf('zone = tod_arena_data::arena_zone();'), 'the branch sits after hold_tower and before the arena opens');
// 2026-10-04 (docs/210): the house no longer puts level 10's arena hit multiplier on the Dealer (his own x1.25 is
// the whole number: 45 x 2.35 x 1.25 = 131 was two hits through Juggernog) and fights at the static health round.
check(!!arun && /if \( lvl >= TOD_ARENA_LEVELS \)\s*\n\s*\{\s*\n(?:\s*\/\/[^\n]*\n)*\s*level\.tod_arena_dmg_mult = undefined;\s*\n\s*level\.tod_arena_hp_round = hp_round\( lvl \);/.test(arun) && !('TOD_ARENA_HOUSE' in AD), 'the house takes the last level and only the last (the TOD_ARENA_HOUSE toggle retired with the Keeper, W2E), no arena hit multiplier on the Dealer, the static health round');
check(/level\.tod_arena_hp_round = undefined;/.test(body(ARENA, 'arena_win')) && /level\.tod_arena_hp_round = hp_round\( lvl \);/.test(arun) && /function hp_round\( lvl \) \{ return TOD_ARENA_HP_ROUND_BASE \+ TOD_ARENA_HP_ROUND_STEP \* \( lvl - 1 \); \}/.test(ARENA), 'the arena fights at a static health round per level and the win hands the tower its round back (docs/210)');
check(/if \( isdefined\( level\.tod_arena_hp_round \) \) r = level\.tod_arena_hp_round;/.test(body(read(S + '_tod_power_scale.gsc'), 'track_rounds')), 'the power scale holds the arena\'s static round while a fight runs');
check(/if \( isdefined\( e\.tod_haven_guard \) \)\s*\n\s*continue;/.test(body(ARENA, 'hold_tower')), 'the arena trip keeps a haven\'s guardians (deleting them cleansed the haven for free)');
check(!!arun && /tod_teleport::discharge\( org \);\s*\n\s*if \( !tod_house::run\( lvl, op \) \)/.test(arun), 'the chamber discharges in the jump frame, then the house runs');
check(!!arun && /release_tower\( held \);\s*\n\s*if \( TOD_ARENA_COST > 0 \) payer zm_score::add_to_player_score\( TOD_ARENA_COST \);/.test(arun.slice(arun.indexOf('house_closed'))), 'a house that cannot open releases the tower and refunds');
check(!!arun && arun.slice(arun.indexOf('tod_house::run')).indexOf('level notify( "tod_arena_fight_over" )') > 0 && /arena_win\( lvl, held \);\s*\n\s*return;\s*\n\s*\}/.test(arun), 'the win path: fight over, arena_win, return');
check(/level\.tod_arena_hud_push_fn = &hud_push;/.test(ARENA) && /level\.tod_arena_hud_watch_fn = &hud_watch;/.test(ARENA) && /tod_house::init\(\);/.test(ARENA), 'init hands the readout to the house and starts it');
check(/\( tod_arena_data::in_arena\( org \) \|\| tod_house_data::in_house\( org \) \)/.test(body(ARENA, 'fall_guard_verdict')), 'the fall guard covers the house');
const hp = body(ARENA, 'hud_push');
check(!!hp && /if \( IS_TRUE\( h\.boss\.tod_dealer \) \)\s*\n\s*flags = flags \+ TOD_ARENA_HUD_DEALER;/.test(hp) && /if \( IS_TRUE\( h\.house \) \)\s*\n\s*flags = flags \+ TOD_ARENA_HUD_HOUSE;/.test(hp), 'hud_push adds the DEALER bit for him and the HOUSE bit for the room');
const aw = body(ARENA, 'arena_win');
check(!!aw && /dais = level\.tod_arena_depart;/.test(aw) && /level\.tod_arena_depart = undefined;/.test(aw), 'the ride home charges from the house\'s dais and forgets it');
check(/notice = "BATTLE ARENA - THE FINAL FIGHT"/.test(ARENA) && /banner = "BATTLE ARENA - THE FINAL FIGHT"/.test(ARENA), 'the chamber and the jump name the final fight');
check(/#insert scripts\\zm\\zm_tod2_cybercity\\_tod_tester\.gsh;/.test(ARENA) && /if \( TOD_TESTER_KIT && TOD_ARENA_TEST_START_LEVEL > 1 \)/.test(ARENA), 'the tester kit\'s start level rides the one switch');
const lua = Object.fromEntries([...TODARENA.matchAll(/^local (FLAG_\w+) = (\d+)/gm)].map(m => [m[1], +m[2]]));
check(lua.FLAG_HOUSE === +AD.TOD_ARENA_HUD_HOUSE && lua.FLAG_DEALER === +AD.TOD_ARENA_HUD_DEALER, 'LOCKSTEP HOUSE / DEALER bits GSC vs TodArena.lua');
check(/waveLine = "THE FINAL FIGHT"/.test(TODARENA) && /line, rgb = "THE DEALER", RED/.test(TODARENA), 'the readout reads THE FINAL FIGHT / THE DEALER');
check(/elseif name == "tod_house_cut" then[\s\S]*?STATE_CORRUPT[\s\S]*?pulse\( CUT_A/.test(TODHAVEN), 'TodHaven flickers red on the drain\'s cut inside the corrupted state');

// ---------------------------------------------------------------------------
// 4. THE LAST ROLL (_tod_shop.gsc + TodSpinReel.lua)
// ---------------------------------------------------------------------------
const SD = defs(SHOP);
const cursed = REEL.match(/^local CURSED = \{ tile = (\d+), code = (\d+), name = "CURSED"/m);
check(!!cursed && +cursed[1] === +SD.TOD_SPIN_CURSED_TILE && +cursed[2] === +SD.TOD_SPIN_CODE_CURSED, 'LOCKSTEP the cursed tile and code: _tod_shop vs TodSpinReel');
check(+SD.TOD_SPIN_CURSED_TILE >= 40 && +SD.TOD_SPIN_CURSED_TILE % 4 === 0 && Math.floor(+SD.TOD_SPIN_CURSED_TILE / 4) > 9, 'the cursed tile is an item the wheel does not have (past item 9)');
check(+SD.TOD_SPIN_CODE_CURSED > 3, 'the cursed code is none of the socket codes (1..3)');
check(Math.floor(+SD.TOD_SPIN_CURSED_TEASE / 4) === 9 && +SD.TOD_SPIN_CURSED_TEASE % 4 === 3, 'the hang before the curse is a LEGENDARY LUCKY CHARM');
const hr = body(SHOP, 'house_roll');
check(!!hr && /foreach \( p in party \)[\s\S]*LuiNotifyEvent\( &"tod_spin_open", 4, seed, prize, tease, luck \* 64 \+ TOD_SPIN_STEPS \)/.test(hr) && /LuiNotifyEvent\( &"tod_spin_step", 2, k, ms \)/.test(hr) && /LuiNotifyEvent\( &"tod_spin_land", 2, prize, TOD_SPIN_CODE_CURSED \)/.test(hr),
  'house_roll: open, every step and the cursed landing go to every player of the party');
check(!!hr && /seed = RandomIntRange\( 1, 60000 \);/.test(hr) && (hr.match(/seed = /g) || []).length === 1, 'one seed for everyone (the same reel on every screen)');
check(!!hr && !/tod_luck::/.test(hr) && !/tod_spin_items/.test(hr) && !/tod_spin_slots"/.test(hr) && !/minus_to_player_score/.test(hr), 'the last roll pays nothing, touches no slot and charges nothing');
check(!!hr && /tod_house_cursed/.test(hr) && /tod_pull_beat/.test(hr) && /step_ms\( k, 0, 1 \)/.test(hr), 'the cursed landing has its sound; the heartbeat on the hang; the near-miss cadence');
check(/function house_roll_end\( party \)[\s\S]*LuiNotifyEvent\( &"tod_spin_end", 1, 0 \)/.test(SHOP), 'house_roll_end drops the panel on every screen');
check(/if \( IS_TRUE\( level\.tod_shop_hold \) \) \{ wait 0\.25; continue; \}/.test(SHOP) && (SHOP.match(/if \( IS_TRUE\( level\.tod_shop_hold \) \) continue;/g) || []).length === 2, 'the cycler and both voice watchers sleep under the hold');
check(/function house_shop_begin\( origin, yaw \)[\s\S]*level\.tod_spin_trig TriggerEnable\( false \)/.test(SHOP) && /function house_shop_end\(\)[\s\S]*level\.tod_shop_hold = false;/.test(SHOP), 'the counter lights with its own prompts dark; the end wakes the cycler');
check(/if v == CURSED\.tile then[\s\S]*?landCursed\( code \)/.test(REEL) && /local function landCursed\( code \)/.test(REEL) && /PrizeName:setText\( "HOUSE WINS" \)/.test(REEL), 'the reel lands the curse on its own path');
check(/local function paintTile\( t, v, hot \)\s*\n\s*if v == CURSED\.tile then/.test(REEL) && /t\.Img:setImage\( reg\( ART\.cursed\.tile \) \)/.test(REEL), 'the cursed tile wears its own art before the item lookup');
for (const img of ['i_tod_spin_tile_cursed', 'i_tod_spin_banner_cursed', 'i_tod_spin_ico_cursed']) {
  check(exists('source_data/tod_ui_images/_images/' + img + '.png'), `${img}.png exists (GENERATED)`);
  check(new RegExp('^image,' + img + '$', 'm').test(ZONE), `${img} is zoned`);
  check(GDT.includes('"' + img + '" ( "image.gdf" )') && GDT.includes('"baseImage" "source_data/tod_ui_images/_images/' + img + '.png"'), `${img} has its GDT block`);
  check(REEL.includes('"' + img + '"'), `TodSpinReel names ${img}`);
}

// ---------------------------------------------------------------------------
// 5. THE WIRING
// ---------------------------------------------------------------------------
check(/zm_zonemgr::zone_init\( "house_parlour_zone" \);/.test(ENTRY) && /zm_zonemgr::zone_init\( "house_zone" \);/.test(ENTRY), 'both zones are created by the entry script');
check(/^scriptparsetree,scripts\/zm\/zm_tod2_cybercity\/_tod_house\.gsc$/m.test(ZONE) && /^scriptparsetree,scripts\/zm\/zm_tod2_cybercity\/_tod_house_data\.gsc$/m.test(ZONE), 'both scripts are zoned');
check(/"Filename"\s*:\s*"tod_house\.csv"/.test(SZC) && /^tod_house_cursed,/m.test(HOUSE_CSV) && /^tod_house_drain,/m.test(HOUSE_CSV) && /^tod_house_cut,/m.test(HOUSE_CSV), 'the three cues ride tod_house.csv and the zone config loads it');
check(/^#define TOD_DEALER_TEST_SPAWN\s+0/m.test(DEALER), 'the Dealer\'s crown-hall test spawn is OFF (the house is his place)');
check(/if \( IS_TRUE\( level\.tod_dealer_hold \) \)[\s\S]*?self\.ignoreall = true;[\s\S]*?continue;/.test(body(DEALER, 'brain')) && /if \( was_held \)[\s\S]*?self\.ignoreall = \( IS_TRUE\( level\.tod_upgrade_pause \) \|\| IS_TRUE\( self\.tod_dealer_attacking \) \|\| \( self dc_disabled\(\) \) \);/.test(body(DEALER, 'brain')), 'the Dealer holds (and lets go) under level.tod_dealer_hold');
check(/level thread \[\[ level\.tod_dealer_crack_fn \]\]\( self \);/.test(DEALER) && /level thread \[\[ level\.tod_dealer_death_fn \]\]\( self \);/.test(DEALER), 'the crack and the death call the house\'s hooks');
for (const [file, fn] of [['_tod_ambush.gsc', 'legal'], ['_tod_reach.gsc', 'region_of'], ['_tod_atmosphere.gsc', null], ['_tod_gauge.gsc', null]]) {
  const t = read(S + file);
  check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_house_data;/.test(t) && /tod_house_data::in_house\(/.test(t) && /tod_house_data::in_parlour\(/.test(t), `${file} treats the house like the arena (away)`);
}
check(/prefix: 'dealer house', seed: 'dealer house floor'/.test(GEOM_LINT) && /prefix: 'dealer parlour', seed: 'dealer parlour floor'/.test(GEOM_LINT) && /dealer parlour shop hull \\d\+/.test(GEOM_LINT) && /dealer \(house\|parlour\) \(\?!\.\*ramp\$\)/.test(GEOM_LINT), 'lint_tod_geometry knows both islands, the hut\'s hull and the shaped solids');
check(/_tod_house_data\.gsc/.test(NAV_LINT) && /house_nav_probes/.test(NAV_LINT) && /parlour_arrivals/.test(NAV_LINT), 'lint_tod_navmesh reads the house\'s anchors');
check(/dealer_house\/make_spin_art\.py"\) --check/.test(BUILD) && /dealer_house\/make_sounds\.py"\) --check/.test(BUILD) && /test_dealer_house\.js/.test(BUILD) && /TOD_HOUSE_LOG/.test(BUILD), 'build_map.ps1 runs the art, the cues and this gate, and refuses to publish the log');
check(/'_tod_house\.gsc': \[ 'DefaultHint' \]/.test(read('tools/lint_tod_hints.js')), 'the hint lint routes the last roll\'s prompt to the default card');
check(/_tod_house_data/.test(read('tools/test_pursuit.js')) && /_tod_house_data/.test(read('tools/test_ambush.js')) && /_tod_house_data/.test(read('tools/test_battle_arena.js')), 'the pursuit, ambush and arena gates load the house data beside the arena\'s');

// ---------------------------------------------------------------------------
// 6. MUTANTS (each must be caught by a check above re-run on the mutated text)
// ---------------------------------------------------------------------------
function mutantsCaught() {
  const caught = [];
  const tryOne = (label, text, mutate, probe) => {
    const bad = mutate(text);
    if (bad === text) { fails++; console.log('FAIL mutant "' + label + '": its anchor text is gone'); return; }
    let ok = false;
    try { ok = probe(bad); } catch (e) { ok = true; }
    if (ok) caught.push(label); else { fails++; console.log('FAIL mutant "' + label + '" was NOT caught'); }
    checks++;
  };
  const gh = text => gscLoad([['tod_house', text], ['tod_house_data', DATA], ['tod_arena_data', ARENA_DATA]], defs(text), { builtins: { IS_TRUE } });
  tryOne('a drain that stops above one', HOUSE, t => t.replace(/^#define TOD_HOUSE_ONE_HP\s+1\b/m, '#define TOD_HOUSE_ONE_HP          2'), t => gh(t).call('drain_target', [100, 10, 10]) !== 1);
  tryOne('a drain that cuts past the last step and under one', HOUSE, t => t.replace('\tif ( step > steps )\n\t\tstep = steps;\n', '').replace('\tif ( t < TOD_HOUSE_ONE_HP )\n\t\tt = TOD_HOUSE_ONE_HP;\n', ''), t => gh(t).call('drain_target', [100, 17, 10]) !== 1);
  tryOne('a drain that never reaches one', HOUSE, t => t.replace('t = int( hp0 - ( hp0 - TOD_HOUSE_ONE_HP ) * step / steps + 0.5 );', 't = int( hp0 - ( hp0 - TOD_HOUSE_ONE_HP ) * step / ( steps + 1 ) + 0.5 );'), t => gh(t).call('drain_target', [100, 10, 10]) !== 1);
  tryOne('the nearest gate instead of the farthest', HOUSE, t => t.replace('if ( d > best_d )', 'if ( best_d < 0 || d < best_d )'), t => { const f = gh(t).call('farthest_gate', [[V(100, 0, 0), V(-100, 0, 0)], [V(90, 0, 0)]]); return f[0] !== -100; });
  tryOne('a shield that lets damage through', HOUSE, t => t.replace('\tif ( !shield_verdict( level.tod_house_shield ) )\n\t\treturn -1;\n\treturn 0;', '\treturn -1;'), t => !/function house_damage_guard[\s\S]*?return 0;/.test(t));
  tryOne('a release that leaves the party frozen', HOUSE, t => t.replace("\t\tp tod_upgrades::menu_freeze( false );\n\t\tif ( !IS_TRUE( p.tod_pause_invuln )", "\t\tif ( !IS_TRUE( p.tod_pause_invuln )"), t => !/menu_freeze\( false \)/.test(body(t, 'release')));
  tryOne('an end that leaves the counter lit', HOUSE, t => t.replace('\ttod_shop::house_shop_end();\n', ''), t => !/tod_shop::house_shop_end\(\)/.test(body(t, 'end')));
  tryOne('a fight that strands the party when he never comes', HOUSE, t => t.replace('\t\trelease();\n\t\treturn true;\n\t}\n\tdealer.tod_arena = true;', '\t\treturn true;\n\t}\n\tdealer.tod_arena = true;'), t => { const f = body(t, 'fight'); return !/release\(\);/.test(f.slice(f.indexOf('DEALER_NOSHOW'), f.indexOf('return true;'))); });
  tryOne('the fight starting before his line', HOUSE, t => t.replace('\tsay_all( "tod_house_vo_fight" );\n\trelease();', '\trelease();\n\tsay_all( "tod_house_vo_fight" );'), t => { const f = body(t, 'fight'); return !(f.indexOf('tod_house_vo_fight') < f.indexOf('release();', f.indexOf('tod_house_vo_fight'))); });
  tryOne('an inline fx_burst (a delay)', HOUSE, t => t.replace('\tlevel thread tod_teleport::fx_burst( "tod_tp_kino", front + ( 0, 0, 4 ), 3.0 );', '\ttod_teleport::fx_burst( "tod_tp_kino", front + ( 0, 0, 4 ), 3.0 );'), t => /^\t+tod_teleport::fx_burst\(/m.test(t));
  tryOne('a hold that never ends', HOUSE, t => t.replace('\tlevel endon( "tod_house_release" );\n\twhile ( true )\n\t{\n\t\tforeach ( p in playing_players() )\n\t\t\thold_at( p, TOD_HOUSE_DRAIN_STEPS );', '\twhile ( true )\n\t{\n\t\tforeach ( p in playing_players() )\n\t\t\thold_at( p, TOD_HOUSE_DRAIN_STEPS );'), t => !/function hold_one\(\)[\s\S]*level endon\( "tod_house_release" \)/.test(t));
  tryOne('a keep-alive slower than the watchdog', HOUSE, t => t.replace(/^#define TOD_HOUSE_CINE_KEEP_SECS\s+\d+/m, '#define TOD_HOUSE_CINE_KEEP_SECS  20'), t => !(+defs(t).TOD_HOUSE_CINE_KEEP_SECS < 17));
  tryOne('a branch after the arena opens', ARENA, t => t.replace('\theld = hold_tower();\n\t// THE DEALER\'S HOUSE (docs/207)', '\theld = hold_tower();\n\tzone = tod_arena_data::arena_zone();\n\t// THE DEALER\'S HOUSE (docs/207)'), t => { const r = body(t, 'arena_run'); return !(r.indexOf('tod_house::run( lvl, op )') < r.indexOf('zone = tod_arena_data::arena_zone();')); });
  tryOne('the house on every level', ARENA, t => t.replace('if ( lvl >= TOD_ARENA_LEVELS )\n\t{\n\t\t// NO ARENA HIT MULTIPLIER', 'if ( true )\n\t{\n\t\t// NO ARENA HIT MULTIPLIER'), t => !/if \( lvl >= TOD_ARENA_LEVELS \)\s*\n\s*\{\s*\n(?:\s*\/\/[^\n]*\n)*\s*level\.tod_arena_dmg_mult = undefined;\s*\n\s*level\.tod_arena_hp_round = hp_round\( lvl \);/.test(body(t, 'arena_run')));
  tryOne('the arena hit multiplier back on the Dealer', ARENA, t => t.replace('\t\tlevel.tod_arena_dmg_mult = undefined;\n\t\tlevel.tod_arena_hp_round = hp_round( lvl );', '\t\tlevel.tod_arena_dmg_mult = dmg_mult( lvl );\n\t\tlevel.tod_arena_hp_round = hp_round( lvl );'), t => !/if \( lvl >= TOD_ARENA_LEVELS \)\s*\n\s*\{\s*\n(?:\s*\/\/[^\n]*\n)*\s*level\.tod_arena_dmg_mult = undefined;\s*\n\s*level\.tod_arena_hp_round = hp_round\( lvl \);/.test(body(t, 'arena_run')));
  tryOne('a win that leaves the static round set', ARENA, t => t.replace('\tlevel.tod_arena_hp_round = undefined;   // the tower round', '\t// the tower round'), t => !/level\.tod_arena_hp_round = undefined;/.test(body(t, 'arena_win')));
  tryOne('a trip that deletes the guardians', ARENA, t => t.replace('\t\tif ( isdefined( e.tod_haven_guard ) )\n\t\t\tcontinue;\n', ''), t => !/if \( isdefined\( e\.tod_haven_guard \) \)\s*\n\s*continue;/.test(body(t, 'hold_tower')));
  tryOne('a readout that names the Keeper for him', ARENA, t => t.replace('\t\t\tflags = flags + TOD_ARENA_HUD_DEALER;', '\t\t\tflags = flags + TOD_ARENA_HUD_BOSS;'), t => !/if \( IS_TRUE\( h\.boss\.tod_dealer \) \)\s*\n\s*flags = flags \+ TOD_ARENA_HUD_DEALER;/.test(body(t, 'hud_push')));
  tryOne('a fall guard blind to the house', ARENA, t => t.replace('( tod_arena_data::in_arena( org ) || tod_house_data::in_house( org ) )', 'tod_arena_data::in_arena( org )'), t => !/\( tod_arena_data::in_arena\( org \) \|\| tod_house_data::in_house\( org \) \)/.test(body(t, 'fall_guard_verdict')));
  tryOne('a ride home from the wrong dais', ARENA, t => t.replace('\t\tdais = level.tod_arena_depart;', '\t\tdais = dais;'), t => !/dais = level\.tod_arena_depart;/.test(body(t, 'arena_win')));
  tryOne('a cursed tile the reel does not share', REEL, t => t.replace(/^local CURSED = \{ tile = 60,/m, 'local CURSED = { tile = 56,'), t => { const c = t.match(/^local CURSED = \{ tile = (\d+), code = (\d+)/m); return +c[1] !== +SD.TOD_SPIN_CURSED_TILE; });
  tryOne('a last roll that pays luck back', SHOP, t => t.replace('    log( "HOUSE_ROLL_LAND code="', '    tod_luck::add( roller, 50 );\n    log( "HOUSE_ROLL_LAND code="'), t => /tod_luck::/.test(body(t, 'house_roll')));
  tryOne('a last roll with a seed per player', SHOP, t => t.replace('        p.tod_spin_slots_shown = undefined;\n        p LuiNotifyEvent( &"tod_spin_open"', '        seed = RandomIntRange( 1, 60000 );\n        p.tod_spin_slots_shown = undefined;\n        p LuiNotifyEvent( &"tod_spin_open"'), t => (body(t, 'house_roll').match(/seed = /g) || []).length !== 1);
  tryOne('a cycler that wakes under the hold', SHOP, t => t.replace('        if ( IS_TRUE( level.tod_shop_hold ) ) { wait 0.25; continue; }\n', ''), t => !/if \( IS_TRUE\( level\.tod_shop_hold \) \) \{ wait 0\.25; continue; \}/.test(t));
  tryOne('the test spawn back on', DEALER, t => t.replace(/^#define TOD_DEALER_TEST_SPAWN\s+0/m, '#define TOD_DEALER_TEST_SPAWN     1'), t => !/^#define TOD_DEALER_TEST_SPAWN\s+0/m.test(t));
  tryOne('a Dealer who never holds', DEALER, t => t.replace('\t\t\tself.ignoreall = true;\n\t\t\twas_held = true;\n\t\t\tcontinue;', '\t\t\twas_held = true;\n\t\t\tcontinue;'), t => !/if \( IS_TRUE\( level\.tod_dealer_hold \) \)[\s\S]*?self\.ignoreall = true;[\s\S]*?continue;/.test(body(t, 'brain')));
  tryOne('a readout that names no dealer', TODARENA, t => t.replace('line, rgb = "THE DEALER", RED', 'line, rgb = "THE KEEPER", RED'), t => !/line, rgb = "THE DEALER", RED/.test(t));
  tryOne('a stale generated room', DATA, t => t.replace(/function house_half\(\)\s+\{ return \d+; \}/, 'function house_half()       { return 1; }'), t => t !== LAYOUT.dataGsc());
  // THE BARKS (PK14 / W2B)
  tryOne('a deck that says the same line twice running', HOUSE, t => t.replace('\tif ( free.size > 1 && isdefined( last ) )', '\tif ( false )'),
    t => { const g2 = gh(t); for (let r = 0; r < 12; r++) if (g2.call('deck_pick', [{}, 3, 1, r]) === 1) return true; return false; });
  tryOne('a scythe call in state two', HOUSE, t => t.replace('\tif ( state != 1 )\n\t\treturn "state";\n', ''), t => gh(t).call('swipe_verdict', [2, false, 100, 20, 50000, 0, 0]) !== 'state');
  tryOne('a scythe call on the hit that downs him', HOUSE, t => t.replace('\tif ( dmg >= hp )\n\t\treturn "lethal";\n', ''), t => gh(t).call('swipe_verdict', [1, false, 20, 30, 50000, 0, 0]) !== 'lethal');
  tryOne('a bark over a line still speaking', HOUSE, t => t.replace('\t\tif ( isdefined( u ) && now < u + quiet_ms )\n\t\t\treturn false;\n', ''), t => gh(t).call('bark_quiet', [10000, 9000, [9000], 2500]) !== false);
  tryOne('the crack line over the crack', HOUSE, t => t.replace('\tlevel thread story_line_after( "tod_house_vo_crack", TOD_HOUSE_CRACK_LINE_DELAY, "crack" );', '\tlevel thread say_all_now( "tod_house_vo_crack" );'),
    t => !/level thread story_line_after\( "tod_house_vo_crack", TOD_HOUSE_CRACK_LINE_DELAY, "crack" \);/.test(body(t, 'on_crack')));
  tryOne('a low line that comes back', HOUSE, t => t.replace('\tif ( IS_TRUE( said ) || maxhp <= 0 || hp <= 0 )', '\tif ( maxhp <= 0 || hp <= 0 )'), t => gh(t).call('low_due', [true, 19, 100]) !== false);
  return caught;
}
const caught = mutantsCaught();

if (fails) { console.log(`\nDEALER'S HOUSE GATE FAILED: ${fails}/${checks} checks`); process.exit(1); }
console.log(`DEALER'S HOUSE OK: ${checks} checks - the two rooms (generated, vented, in the .map), the flow (parlour -> last roll -> laugh -> dome and drain -> fight -> end), the arena's branch, the readout flags, the cursed reel (LOCKSTEP), the wiring; ${caught.length} mutants caught`);
