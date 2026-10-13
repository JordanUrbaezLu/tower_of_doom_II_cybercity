#!/usr/bin/env node
'use strict';
// =============================================================================
// test_class_terminal.js - THE CROWN'S CLASS TERMINAL gate (2026-10-01).
//
// User 2026-10-01: "In the crown i want an option to switch between classes as
// well. I eventually want to push out a testing phase so testers have access to
// everything in the crown."  -> scripts/zm/zm_tod2_cybercity/_tod_class_terminal.gsc
//
// What it proves, reading the SHIPPING sources (the pure functions run through
// tools/sky_ships/gsc_eval.js, never a copy):
//   A. WIRING      the switch, the module's init + #using + zone line, the console
//                  model and burst effect zoned, the prompt's one constant hint
//                  (its grammar, its noun in TOD_NOUNS, the hint lint's route row),
//                  the sounds it plays, the Lua's show-3 lockstep, the clock's
//                  4-bit quartering, the input's start focus.
//   B. WHO MAY OPEN IT   refuse_code() over every state, its priority, a message per
//                  code - and a NEGATIVE CONTROL PER CLAUSE: each refusal check is
//                  deleted from a copy of the function and the case table must catch it.
//   C. WHERE IT STANDS   terminal_place() from the GENERATED crown anchors: inside the
//                  hall, back to the wall, screen facing in, clear of every crown use
//                  trigger (the generator's r_a + r_b + 64 rule), the risers (165 u),
//                  the piers and the shrine; and the mirror parity.
//   D. THE SLEEPING CARD  _tod_upgrades domain_dormant / class_live_level: another
//                  class's card sleeps, shared / parked / unregistered-class cards never
//                  do, classless never does; the three effect sites + the pause list
//                  read it; negative controls (the old get_level read, a dormancy rule
//                  that forgets the registered-class test).
//   E. THE SESSION  the lock / unlock pairs, the takeover lanes, every exit through
//                  close_session, the kit handover fix, the C4 + shield clears.
// Exit 0 = pass. Wired into tools/build_map.ps1 (every build, -GscOnly included).
// =============================================================================
const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8').replace(/\r\n/g, '\n');
const { gscLoad } = require('./sky_ships/gsc_eval.js');

let passes = 0, fails = 0;
function check(ok, good, bad) {
  if (ok) { passes++; console.log('  ok   ' + good); }
  else { fails++; console.log('  FAIL ' + (bad || good)); }
}
function section(t) { console.log('\n' + t); }

const TERM = read('scripts/zm/zm_tod2_cybercity/_tod_class_terminal.gsc');
const TESTER = read('scripts/zm/zm_tod2_cybercity/_tod_tester.gsh');
const SELECT = read('scripts/zm/zm_tod2_cybercity/_tod_class_select.gsc');
const CLSC = read('scripts/zm/zm_tod2_cybercity/_tod_class_count.gsh');
const MAIN = read('scripts/zm/zm_tod2_cybercity/_tod_main.gsc');
const ZONE = read('zone_source/zm_tod2_cybercity.zone');
const ROUTER = read('ui/uieditor/widgets/HUD/ZM_CursorHint/ZMCursorHintNew.lua');
const HINTLINT = read('tools/lint_tod_hints.js');
const LUA = read('ui/uieditor/menus/hud/tod_class_select.lua');
const UPG = read('scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc');
const SHIELD = read('scripts/zm/zm_tod2_cybercity/_tod_riotshield.gsc');
const KIT = read('scripts/zm/zm_tod2_cybercity/_tod_class_kit.gsc');
const CROWN = read('scripts/zm/zm_tod2_cybercity/_tod_crown_data.gsc');
const SHOP = read('scripts/zm/zm_tod2_cybercity/_tod_shop.gsc');
const PARTNERS = read('scripts/zm/zm_tod2_cybercity/_tod_partners.gsc');
const FALL = read('scripts/zm/zm_tod2_cybercity/_tod_fall.gsc');
const BREATHER = read('scripts/zm/zm_tod2_cybercity/_tod_breather_data.gsc');
const BUILD = read('tools/build_map.ps1');
const ALIASES = fs.readdirSync(path.join(ROOT, 'sound', 'aliases')).filter(f => f.endsWith('.csv'))
  .map(f => read('sound/aliases/' + f)).join('\n');

function defs(text) {
  const out = {};
  for (const m of text.matchAll(/^#define\s+(\w+)\s+\(?\s*(-?[\d.]+)\s*\)?\s*(?:\/\/.*)?$/gm)) out[m[1]] = Number(m[2]);
  return out;
}
const D = defs(TERM);
const CLS_COUNT = Number((CLSC.match(/^#define\s+TOD_CLS_COUNT\s+(\d+)/m) || [])[1]);
const ALL_DEFS = { ...D, TOD_CLS_COUNT: CLS_COUNT };
const IS_TRUE = x => x !== undefined && x !== null && !!x;

// the body of one GSC function (brace-matched), for structural checks
function fnBody(text, name) {
  // a declaration may carry a trailing "// self = player" before its brace
  const re = new RegExp('\\bfunction\\s+' + name + '\\s*\\([^)]*\\)\\s*(?:\\/\\/[^\\n]*\\s*)?\\{');
  const m = re.exec(text);
  if (!m) return null;
  let depth = 1, j = m.index + m[0].length;
  while (depth && j < text.length) { if (text[j] === '{') depth++; else if (text[j] === '}') depth--; j++; }
  return text.slice(m.index, j);
}

// =============================================================================
section('A. WIRING');
{
  const luaN = Number((LUA.match(/^\s*local\s+CLASS_N\s*=\s*(\d+)/m) || [])[1]);
  check(CLS_COUNT === 4 && luaN === CLS_COUNT, `the draft is four classes in both languages (TOD_CLS_COUNT ${CLS_COUNT} in _tod_class_count.gsh, CLASS_N ${luaN} in tod_class_select.lua)`,
    `class count drift: TOD_CLS_COUNT ${CLS_COUNT} vs Lua CLASS_N ${luaN} (both must be 4)`);
}
check(/^#define\s+TOD_TESTER_KIT\s+[01]\b/m.test(TESTER), 'the one switch: TOD_TESTER_KIT in _tod_tester.gsh', '_tod_tester.gsh lost its TOD_TESTER_KIT define');
check(/#insert scripts\\zm\\zm_tod2_cybercity\\_tod_tester\.gsh;/.test(TERM) && /function init\(\)\s*\{\s*if \( !TOD_TESTER_KIT \)\s*return;/.test(TERM),
  'the terminal exists only while the switch is on (init returns first thing)', 'init() no longer gates on TOD_TESTER_KIT');
check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_class_terminal;/.test(MAIN) && /\ttod_class_terminal::init\(\);/.test(MAIN),
  '_tod_main #using + calls tod_class_terminal::init()', '_tod_main does not load the terminal');
check(/^scriptparsetree,scripts\/zm\/zm_tod2_cybercity\/_tod_class_terminal\.gsc$/m.test(ZONE), 'the zone carries the module', 'no scriptparsetree line for _tod_class_terminal.gsc');
check(/^xmodel,p7_zm_sta_dragon_network_data_terminal$/m.test(ZONE) && /^fx,dlc5\/theater\/fx_teleport_flashback_kino$/m.test(ZONE),
  'its console model and burst effect are zoned (both precached by the module)', 'the console model or the kino burst is not zoned');
check(/#precache\( "model", "p7_zm_sta_dragon_network_data_terminal" \)/.test(TERM) && /#precache\( "fx", "dlc5\/theater\/fx_teleport_flashback_kino" \)/.test(TERM),
  'the module precaches what it spawns', 'a spawned model / effect is not precached in the module');
const hints = [...TERM.matchAll(/SetHintString\(\s*("(?:[^"\\]|\\.)*")\s*\)/g)].map(m => JSON.parse(m[1]));
check(hints.length === 1, 'ONE hint string (one permanent triggerstring slot)', `${hints.length} SetHintString literals in the terminal (each distinct one is a permanent slot)`);
const hint = hints[0] || '';
check(/^Hold \^3\[\{\+activate\}\]\^7 \^5CLASS TERMINAL\^7 - [^-/]+ \/ [^-/]+$/.test(hint),
  `the prompt's grammar: "Hold [use] CLASS TERMINAL - <detail> / <detail 2>" (${JSON.stringify(hint)})`, `the hint breaks the default card's grammar: ${JSON.stringify(hint)}`);
check(/"class terminal",/.test(ROUTER), 'its noun is claimed in TOD_NOUNS (the default card, never another route)', 'TOD_NOUNS has no "class terminal"');
check(/'_tod_class_terminal\.gsc': \[ 'DefaultHint' \]/.test(HINTLINT), 'lint_tod_hints declares the module DefaultHint', 'lint_tod_hints has no EXPECTED_ROUTES row for the terminal');
for (const a of ['tod_class_jackin', 'tod_ui_tick', 'tod_warp'])
  check(new RegExp('^' + a + ',', 'm').test(ALIASES), `the alias ${a} exists in sound/aliases`, `the terminal plays ${a} but no alias row defines it`);
check((read('scripts/zm/zm_tod2_cybercity/_tod_doors.gsc').match(/PlaySound\( "zmb_no_purchase" \)/g) || []).length > 0,
  'the refusal sound (stock zmb_no_purchase) is the map\'s established one', 'zmb_no_purchase is no longer used anywhere else - re-check it before trusting it here');
check(D.TOD_CLS_TERM_SECS % 4 === 0 && D.TOD_CLS_TERM_SECS <= 60 && Math.floor((D.TOD_CLS_TERM_SECS + 3) / 4) <= 15,
  `the clock ${D.TOD_CLS_TERM_SECS} s quarters into the 4-bit todUpgTime (${Math.floor((D.TOD_CLS_TERM_SECS + 3) / 4)})`, `TOD_CLS_TERM_SECS ${D.TOD_CLS_TERM_SECS} does not fit the quartered 4-bit field`);
check(D.TOD_CLS_SHOW_TERMINAL === 3 && /if st\.show == 3 then\s*st\.term = true/.test(LUA),
  'todClsShow 3 = the terminal, LOCKSTEP with tod_class_select.lua', 'the terminal show value and the Lua disagree');
check(/CoD\.TodHudVeil\.Set\( "cls_term", st\.term and mode ~= 0 \)/.test(LUA) && /OverrideFunction_CallOriginalSecond\( self, "close"[\s\S]{0,160}CoD\.TodHudVeil\.Set\( "cls_term", false \)/.test(LUA),
  'the Lua veils the HUD only mid-terminal and clears the veil when the panel closes', 'the Lua HUD veil for the terminal is missing or never cleared on close');
for (const s of [...LUA.matchAll(/local TERM_(?:TITLE|SUB1|SUB2|CUR)\s*=\s*"([^"]*)"/g)].map(m => m[1]))
  check(/^[A-Z0-9 \-'.]+$/.test(s), `"${s}" is drawable in the map's typeface`, `"${s}" carries a character the typeface deletes`);
check(/function run_select_input\( timeout, start_focus = undefined \)/.test(SELECT) && /if \( isdefined\( start_focus \) && start_focus >= 1 && start_focus <= TOD_CLS_COUNT \)\s*sel = start_focus;/.test(SELECT),
  'run_select_input opens on a given card (the draft passes none)', 'run_select_input has no start focus');
check(/run_select_input\( TOD_CLS_TIMEOUT \)/.test(SELECT), 'the draft still calls it with its clock alone', 'the draft call changed');
check(/Warn \("TOD_TESTER_KIT is ON/.test(BUILD) && !/Die \("[^"]*TOD_TESTER_KIT/.test(BUILD),
  'build_map WARNS (never refuses) on the tester kit: the testing phase ships it on purpose', 'build_map lost the tester-kit warning, or refuses it');
check(/test_class_terminal\.js/.test(BUILD) && /test_class_terminal_ui\.lua/.test(BUILD), 'build_map runs both terminal gates', 'build_map does not run the terminal gates');
check(/for \( id = 1; id <= TOD_CLS_COUNT; id\+\+ \)\s*\{\s*if \( tod_class_select::class_key\( id \) == key \)\s*return id;\s*\}\s*return tod_class_select::default_focus\(\);/.test(fnBody(TERM, 'slot_of')),
  "the panel opens on the player's own class (slot_of walks the draft's class_key, falls back to its default card)", "slot_of no longer mirrors the draft's slots");

// =============================================================================
section('B. WHO MAY OPEN IT (refuse_code, the shipping function)');
function loadTerm(text) {
  return gscLoad([['tod_class_terminal', text], ['tod_class_select', SELECT]], ALL_DEFS, { builtins: { IS_TRUE } });
}
const g = loadTerm(TERM);
const OPEN = { drafted: 1, alive: 1, downed: 0, grounded: 1, mantling: 0, world_paused: 0, in_menu: 0, flying: 0, grappling: 0,
  ability: 0, cloaked: 0, drinking: 0, reviving: 0, swapping: 0, death_machine: 0 };
const CASES = [
  [{}, ''],
  [{ drafted: 0 }, 'draft'],
  [{ alive: 0 }, 'downed'],
  [{ downed: 1 }, 'downed'],
  [{ world_paused: 1 }, 'menu'],
  [{ in_menu: 1 }, 'menu'],
  [{ grounded: 0 }, 'airborne'],
  [{ flying: 1 }, 'airborne'],
  [{ grappling: 1 }, 'airborne'],
  [{ mantling: 1 }, 'airborne'],
  [{ ability: 1 }, 'ability'],
  [{ cloaked: 1 }, 'ability'],
  [{ drinking: 1 }, 'hands'],
  [{ reviving: 1 }, 'hands'],
  [{ swapping: 1 }, 'hands'],
  [{ death_machine: 1 }, 'hands'],
  // priority: the reason a player would want to hear first
  [{ drafted: 0, downed: 1, in_menu: 1 }, 'draft'],
  [{ downed: 1, in_menu: 1, grounded: 0 }, 'downed'],
  [{ in_menu: 1, grounded: 0, ability: 1 }, 'menu'],
  [{ grounded: 0, ability: 1, drinking: 1 }, 'airborne'],
  [{ ability: 1, drinking: 1 }, 'ability'],
];
function runCases(gl) {
  const bad = [];
  for (const [over, want] of CASES) {
    const st = { ...OPEN, ...over };
    let got;
    try { got = gl.call('tod_class_terminal::refuse_code', [st]); } catch (e) { got = 'ERROR ' + e.message; }
    if (got !== want) bad.push(`${JSON.stringify(over)} -> "${got}" (want "${want}")`);
  }
  return bad;
}
const bad = runCases(g);
check(!bad.length, `refuse_code: ${CASES.length} states, each refused for the right reason (and the open state opens)`, 'refuse_code: ' + bad.join(' | '));
// NEGATIVE CONTROLS: delete each clause from a copy; the case table must catch every deletion
const rcBody = fnBody(TERM, 'refuse_code');
const clauses = [...rcBody.matchAll(/(?:!IS_TRUE|IS_TRUE)\( st\.(\w+) \)/g)].map(m => m[0]);
check(clauses.length >= 15, `refuse_code reads ${clauses.length} state flags`, `refuse_code reads only ${clauses.length} flags (expected 15)`);
let caught = 0;
const missed = [];
for (const c of clauses) {
  const neutral = c.startsWith('!') ? 'false' : 'false';
  const mutantBody = rcBody.replace(c, neutral);
  const mutant = TERM.replace(rcBody, mutantBody);
  if (runCases(loadTerm(mutant)).length > 0) caught++; else missed.push(c);
}
check(missed.length === 0, `negative controls: every one of the ${clauses.length} refusal clauses, deleted, is caught by the case table`,
  'NEGATIVE CONTROL MISSED - the case table does not exercise: ' + missed.join(', '));
const msgs = new Set();
for (const code of ['draft', 'downed', 'menu', 'airborne', 'ability', 'hands']) {
  const m = g.call('tod_class_terminal::refuse_message', [code]);
  msgs.add(m);
  check(typeof m === 'string' && m.startsWith('Class terminal: ') && m.length <= 60 && m !== 'Class terminal: not right now',
    `"${code}" prints "${m}"`, `refuse_message("${code}") = ${JSON.stringify(m)}`);
}
check(msgs.size === 6, 'six refusals, six different lines', 'two refusal codes share one line');
// the state reader covers every flag the decision reads
const rsBody = fnBody(TERM, 'refuse_state');
const unread = [...new Set(clauses.map(c => c.match(/st\.(\w+)/)[1]))].filter(f => !new RegExp('\\bst\\.' + f + ' =').test(rsBody));
check(!unread.length, 'refuse_state() sets every flag refuse_code() reads', 'refuse_state never sets: ' + unread.join(', '));
for (const [flag, src] of [['in_menu', 'self.tod_menu_frozen'], ['in_menu', 'self.tod_spin_locked'], ['in_menu', 'self.tod_solo_upg_active'], ['flying', 'self.tod_jumppad_flying'],
  ['grappling', 'self.tod_grappling'], ['ability', 'self.tod_bash_busy'], ['ability', 'self.tod_gs_diving'], ['ability', 'self.tod_necro_pulse_busy'], ['ability', 'self.tod_necro_bind_t0'],
  ['cloaked', 'self.tod_cloak_until'], ['drinking', 'self.is_drinking'], ['reviving', 'self.is_reviving_any'], ['swapping', 'self.tod_swap_busy'], ['death_machine', 'zombie_powerup_minigun_on']])
  check(new RegExp('st\\.' + flag + ' = [^;]*' + src.replace(/\./g, '\\.')).test(rsBody), `"${flag}" reads ${src}`, `refuse_state's "${flag}" no longer reads ${src}`);

// =============================================================================
section('C. WHERE IT STANDS (terminal_place from the generated crown anchors)');
const cd = gscLoad([['tod_crown_data', CROWN]], {}, {});
const vec = v => [v[0], v[1], v[2]];
const hc = vec(cd.call('hall_center', []));
const crate = vec(cd.call('crown_crate_org', []));
const crateYaw = cd.call('crown_crate_yaw', []);
const place = (h, c) => { const s = g.call('tod_class_terminal::terminal_place', [h, c]); return { side: s.side, org: vec(s.org), yaw: s.yaw, fwd: vec(s.fwd), trig: vec(s.trig) }; };
const P = place(cd.call('hall_center', []), cd.call('crown_crate_org', []));
// the console's measured local bounds (PyCoD off the LOD xmodel_bin, 2026-10-01): x -26.6..21.6,
// y -13.9..20.1, z 0..78.4; the monitor faces local -X
const LB = { x1: -26.6, x2: 21.6, y1: -13.9, y2: 20.1, z2: 78.4 };
function worldBox(org, yaw) {
  const a = yaw * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
  const pts = [[LB.x1, LB.y1], [LB.x1, LB.y2], [LB.x2, LB.y1], [LB.x2, LB.y2]].map(([x, y]) => [org[0] + x * c - y * s, org[1] + x * s + y * c]);
  return { x1: Math.min(...pts.map(p => p[0])), x2: Math.max(...pts.map(p => p[0])), y1: Math.min(...pts.map(p => p[1])), y2: Math.max(...pts.map(p => p[1])) };
}
const box = worldBox(P.org, P.yaw);
const WALL_IN = 728;   // gen_tower_map.js WALL_IN = HW - HWALL (768 - 40)
check(P.org[2] === hc[2], 'stands on the hall floor (the hall centre\'s z)', `z ${P.org[2]} is not the floor ${hc[2]}`);
check(box.x1 >= hc[0] - WALL_IN + 2 && box.x2 <= hc[0] + WALL_IN - 2, `inside the hall (x ${box.x1.toFixed(1)}..${box.x2.toFixed(1)}, walls at +-${WALL_IN})`, `the console pokes into a wall: x ${box.x1.toFixed(1)}..${box.x2.toFixed(1)}`);
const backGap = Math.min(box.x1 - (hc[0] - WALL_IN), (hc[0] + WALL_IN) - box.x2);
check(backGap >= 2 && backGap <= 12, `its back stands ${backGap.toFixed(1)} u off the wall (against it, not floating)`, `its back is ${backGap.toFixed(1)} u off the wall`);
const screen = [Math.cos((P.yaw + 180) * Math.PI / 180), Math.sin((P.yaw + 180) * Math.PI / 180)];
check(screen[0] * (hc[0] - P.org[0]) + screen[1] * (hc[1] - P.org[1]) > 0, `the screen (local -X at yaw ${P.yaw}) faces into the hall`, 'the screen faces the wall');
check(Math.sign(P.org[0] - hc[0]) === -Math.sign(crate[0] - hc[0]) && P.org[1] === crate[1], 'it takes the wall OPPOSITE the crown crate, at the crate\'s y', 'it is not across the nave from the crate');
check(P.fwd[0] * (hc[0] - P.org[0]) > 0 && Math.abs(P.trig[0] - P.org[0]) === D.TOD_CLS_TERM_TRIG_OUT && P.trig[2] === hc[2] + D.TOD_CLS_TERM_TRIG_Z,
  `its use trigger floats ${D.TOD_CLS_TERM_TRIG_Z} u up, ${D.TOD_CLS_TERM_TRIG_OUT} u out in front of the screen`, 'the trigger is not in front of the screen');
{ // within reach: the trigger's near edge touches the console's front face, and its centre is no
  // further out than a step from it - the prompt shows only where the player is looking at the screen
  const front = -LB.x1;   // the screen face is local -X: 26.6 out from the origin
  check(D.TOD_CLS_TERM_TRIG_OUT - D.TOD_CLS_TERM_TRIG_R <= front + 16 && D.TOD_CLS_TERM_TRIG_OUT <= front + 64,
    `the prompt covers the screen (trigger ${D.TOD_CLS_TERM_TRIG_OUT} out, r ${D.TOD_CLS_TERM_TRIG_R}; the screen ${front} out)`,
    `the trigger stands ${D.TOD_CLS_TERM_TRIG_OUT} out with r ${D.TOD_CLS_TERM_TRIG_R}: a player at the screen is outside it`);
}
// every other crown use trigger: the generator's spacing rule, d >= r_a + r_b + 64
const others = [];
{ // the Black Market (the active shop): its trigger TRIG_OUT in front (local -Y) of shop_orgs()[0]
  const so = vec(cd.call('shop_orgs', [])[0]), sy = cd.call('shop_yaws', [])[0];
  const out = Number(SHOP.match(/#define TOD_SPIN_TRIG_OUT\s+(\d+)/)[1]), r = Number(SHOP.match(/#define TOD_SPIN_TRIG_R\s+(\d+)/)[1]);
  const a = sy * Math.PI / 180;
  others.push(['the Black Market', [so[0] + out * Math.sin(a), so[1] - out * Math.cos(a)], r]);
}
{ // the crown crate: crate_trig_out() in front (front = yaw + 90)
  const out = Number(BREATHER.match(/function crate_trig_out\(\)\s*\{\s*return (\d+);/)[1]), r = Number(BREATHER.match(/function crate_trig_r\(\)\s*\{\s*return (\d+);/)[1]);
  const a = (crateYaw + 90) * Math.PI / 180;
  others.push(['the crown crate', [crate[0] + out * Math.cos(a), crate[1] + out * Math.sin(a)], r]);
}
{ // the alarm button: TOD_FALL_BUTTON_TRIG_R round alarm_button_org()
  const b = vec(cd.call('alarm_button_org', [])), r = Number(FALL.match(/#define TOD_FALL_BUTTON_TRIG_R\s+(\d+)/)[1]);
  others.push(['the alarm button', [b[0], b[1]], r]);
}
{ // the partner test benches (while armed): xs, hall centre - N, the trigger fwd * M at radius R
  const tb = fnBody(PARTNERS, 'test_benches');
  const xs = tb.match(/xs = array\( ([^)]*) \)/)[1].split(',').map(Number);
  const dy = Number(tb.match(/c\[ 1 \] - (\d+)/)[1]);
  const um = tb.match(/use_trigger\( borg \+ fwd \* (\d+) \+ \( 0, 0, \d+ \), (\d+) \)/);
  for (const x of xs) others.push([`the partner bench at x ${x}`, [x, hc[1] - dy + Number(um[1])], Number(um[2])]);
}
for (const [name, at, r] of others) {
  const d = Math.hypot(at[0] - P.trig[0], at[1] - P.trig[1]);
  const need = r + D.TOD_CLS_TERM_TRIG_R + 64;
  check(d >= need, `${d.toFixed(0)} u from ${name}'s trigger (needs ${need})`, `the terminal's trigger is ${d.toFixed(0)} u from ${name}'s (needs ${need}): one USE would hit both`);
}
for (const rz of cd.call('hall_riser_orgs', [])) {
  const r = vec(rz);
  const dx = Math.max(box.x1 - r[0], 0, r[0] - box.x2), dy = Math.max(box.y1 - r[1], 0, r[1] - box.y2);
  const dTrig = Math.hypot(r[0] - P.trig[0], r[1] - P.trig[1]);
  check(Math.hypot(dx, dy) >= 165 && dTrig >= 165, `the riser at (${r[0]}, ${r[1]}) is ${Math.hypot(dx, dy).toFixed(0)} u from the console, ${dTrig.toFixed(0)} u from where its user stands (the 165 u rule)`,
    `a hall riser at (${r[0]}, ${r[1]}) is inside 165 u of the terminal`);
}
let pierOk = true;
for (const pz of cd.call('alarm_mount_orgs', []).slice(0, 12)) {   // the twelve hall fixtures ride the colonnade piers (bases 112 square)
  const p = vec(pz);
  const pb = { x1: p[0] - 56, x2: p[0] + 56, y1: p[1] - 56, y2: p[1] + 56 };
  const hitBox = !(box.x2 < pb.x1 || box.x1 > pb.x2 || box.y2 < pb.y1 || box.y1 > pb.y2);
  const dTrig = Math.hypot(Math.max(pb.x1 - P.trig[0], 0, P.trig[0] - pb.x2), Math.max(pb.y1 - P.trig[1], 0, P.trig[1] - pb.y2));
  if (hitBox || dTrig < D.TOD_CLS_TERM_TRIG_R + 16) pierOk = false;
}
check(pierOk, 'clear of all twelve colonnade piers (console and trigger)', 'the console or its trigger overlaps a pier');
{
  const shrineY1 = hc[1] - 112 - 32;   // gen_tower_map SHR_Y1 - PIL_W: the shrine's south pilaster
  check(box.y2 < shrineY1 - 16 || box.y1 > hc[1] + 112 + 32 + 16, `clear of the shrine bay (its pilasters from y ${shrineY1})`, 'the console stands in the shrine bay');
}
{ // the mirror parity: a crate on the other wall puts the console on this one, still facing in
  const M = place([hc[0], hc[1], hc[2]], [2 * hc[0] - crate[0], crate[1], crate[2]]);
  const mb = worldBox(M.org, M.yaw);
  const ms = [Math.cos((M.yaw + 180) * Math.PI / 180), Math.sin((M.yaw + 180) * Math.PI / 180)];
  check(M.side === -P.side && M.org[0] === 2 * hc[0] - P.org[0] && ms[0] * (hc[0] - M.org[0]) > 0 && mb.x1 >= hc[0] - WALL_IN + 2 && mb.x2 <= hc[0] + WALL_IN - 2,
    'the mirror parity (crate on the other wall): the console mirrors and still faces in', 'terminal_place breaks under the mirrored crown');
}

// =============================================================================
section('D. THE SLEEPING CARD (_tod_upgrades domain_dormant / class_live_level)');
const UPG_FNS = ['domain_dormant', 'class_live_level', 'get_level', 'find_domain'].map(n => fnBody(UPG, n));
check(UPG_FNS.every(Boolean), 'the four functions are in _tod_upgrades.gsc', 'missing: ' + ['domain_dormant', 'class_live_level', 'get_level', 'find_domain'].filter((n, i) => !UPG_FNS[i]).join(', '));
function upgCases(fnText) {
  const u = gscLoad([['tod_upgrades', fnText]], {}, { builtins: { IS_TRUE } });
  u.level.tod_classes = { necromancer: {}, assault: {}, heavy: {}, slasher: {} };
  u.level.tod_domains = [
    { key: 'vitality', class_keys: ['slasher'] }, { key: 'adrenaline', class_keys: ['heavy'] }, { key: 'riotshield', class_keys: ['heavy'] },
    { key: 'dr', class_keys: undefined }, { key: 'sprintfire', class_keys: ['parked'] },
  ];
  const lv = { vitality: 5, adrenaline: 4, riotshield: 3, dr: 2, sprintfire: 1 };
  const bad = [];
  const want = (cls, key, n) => {
    const got = u.call('class_live_level', [{ tod_class: cls, tod_levels: lv }, key]);
    if (got !== n) bad.push(`${cls || 'classless'} ${key} -> ${got} (want ${n})`);
  };
  want('slasher', 'vitality', 5); want('assault', 'vitality', 0); want('heavy', 'vitality', 0); want('necromancer', 'vitality', 0);
  want('heavy', 'adrenaline', 4); want('slasher', 'adrenaline', 0); want('heavy', 'riotshield', 3); want('assault', 'riotshield', 0);
  want('assault', 'dr', 2); want('slasher', 'dr', 2);                 // shared: never sleeps
  want('assault', 'sprintfire', 1); want('heavy', 'sprintfire', 1);   // parked (no registered class): never sleeps
  want(undefined, 'vitality', 5);                                     // classless: never sleeps
  want('assault', 'nosuchcard', 0);
  return { bad, u, lv };
}
const UPG_TEXT = UPG_FNS.join('\n');
const D1 = upgCases(UPG_TEXT);
check(!D1.bad.length, 'class_live_level: own-class cards live, other-class cards sleep, shared / parked / classless never sleep', D1.bad.join(' | '));
check(D1.u.call('get_level', [{ tod_class: 'assault', tod_levels: D1.lv }, 'vitality']) === 5,
  'negative control: get_level (the old read) still says 5 for an Archer holding the Warrior\'s VITALITY - the leak class_live_level closes', 'get_level changed meaning');
{
  const leaky = UPG_TEXT.replace(/if \( isdefined\( level\.tod_classes \) && isdefined\( level\.tod_classes\[ k \] \) \)\s*owned_by_a_class = true;/, 'owned_by_a_class = true;');
  check(leaky !== UPG_TEXT && upgCases(leaky).bad.length > 0, 'negative control: a dormancy rule that forgets the registered-class test is caught (parked cards would sleep)', 'NEGATIVE CONTROL MISSED: the registered-class test is unexercised');
}
check(/vitality_hp\( class_live_level\( self, "vitality" \) \)/.test(fnBody(UPG, 'max_hp_floor')) && /has_dark\( self, "vitality" \) && class_live_level\( self, "vitality" \) > 0/.test(fnBody(UPG, 'max_hp_floor')),
  'max_hp_floor reads VITALITY (and its dark rung) through class_live_level', 'max_hp_floor still reads VITALITY with get_level');
check(/lvl = class_live_level\( self, "adrenaline" \)/.test(fnBody(UPG, 'adren_bonus')) && /lvl = class_live_level\( attacker, "adrenaline" \);[^\n]*\n\s*if \( lvl > 0 && is_explosive_kill\( self \) \)/.test(UPG),
  'ADRENALINE (the proc and adren_bonus) reads class_live_level', 'an ADRENALINE read still uses get_level');
check(!/get_level\( (?:self|attacker), "(?:vitality|adrenaline)" \)/.test(UPG), 'no get_level read of VITALITY / ADRENALINE is left', 'a get_level read of VITALITY or ADRENALINE survives');
check((SHIELD.match(/tod_upgrades::class_live_level\( self, TOD_SHIELD_DOMAIN \)/g) || []).length === 2 && /function reconcile\(\)[\s\S]{0,400}class_live_level/.test(SHIELD) && /function recharge_loop\(\)[\s\S]{0,700}class_live_level/.test(SHIELD),
  'the riot shield\'s reconcile + recharge_loop read class_live_level (the 2 s maintain cannot hand an Archer the shield)', 'the riot shield still hands its shield out on get_level');
check(/if \( lvl > 0 && domain_dormant\( self, d \) \)\s*lvl = 0;\s*if \( lvl > 0 \|\| get_level\( self, d\.key \) > 0 \)/.test(fnBody(UPG, 'refresh_upgrade_list')),
  'the pause list sends a sleeping card at level 0 (hidden) and its real level when the class comes back', 'refresh_upgrade_list does not hide sleeping cards');
check(/IS_TRUE\( self\.tod_cls_term_locked \) \|\| IS_TRUE\( self\.tod_cls_term_grace \)/.test(fnBody(UPG, 'pause_invuln_held_elsewhere')),
  'a world pause ending mid-panel cannot strip the terminal\'s invulnerability (pause_invuln_held_elsewhere)', 'pause_invuln_held_elsewhere does not know the terminal');

// =============================================================================
section('E. THE SESSION');
const sess = fnBody(TERM, 'session');
const exits = (sess.match(/\breturn;/g) || []).length;
const viaClose = (sess.match(/self close_session\( [^)]*\);(?:[ \t]*\/\/[^\n]*)?\s*return;/g) || []).length;
const refuseExit = /self release_use\(\);\s*self\.tod_cls_term_busy = undefined;\s*return;/.test(sess);
check(exits === viaClose + 1 && refuseExit, `every one of the session's ${exits} exits goes through close_session (the refusal alone through release_use)`,
  `${exits} returns, ${viaClose} through close_session, refusal exit ${refuseExit}`);
check(/self close_session\( why \);\s*\}\s*$/.test(sess.trim()) || /self close_session\( why \);\s*}$/.test(sess.trim()), 'the switch path ends in close_session', 'the switch path does not end in close_session');
const lockB = fnBody(TERM, 'lock'), unlockB = fnBody(TERM, 'unlock');
check(/increment_ignoreme/.test(lockB) && /decrement_ignoreme/.test(unlockB) && /tod_cls_term_ignored/.test(lockB) && /tod_cls_term_ignored/.test(unlockB),
  'ignoreme goes up once in lock() and down once in unlock() (a latch, so never twice)', 'the ignoreme refcount is not paired');
check((TERM.match(/increment_ignoreme/g) || []).length === 1 && (TERM.match(/decrement_ignoreme/g) || []).length === 1, 'one increment, one decrement in the whole module', 'extra ignoreme calls');
const closeB = fnBody(TERM, 'close_session');
check(/self unlock\(\);/.test(closeB) && /self thread exit_grace\(\);/.test(closeB) && /self menu_close\(\);/.test(closeB) && /self\.tod_cls_term_busy = undefined;/.test(closeB),
  'close_session unlocks, starts the exit grace, closes the menu and frees the player', 'close_session misses a release step');
check(/taken = \( IS_TRUE\( self\.tod_cls_term_taken \) \|\| IS_TRUE\( level\.tod_upgrade_pause \) \);\s*if \( !taken \)\s*\{\s*self tod_class_select::set_field\( "todUpgFocus", 0 \);/.test(closeB),
  'a taken-over close never writes the shared fields (they are the card deal\'s)', 'close_session writes the shared fields after a takeover');
check(/while \( IS_TRUE\( level\.tod_upgrade_pause \) \)\s*wait 0\.1;[\s\S]{0,200}if \( IS_TRUE\( self\.tod_menu_frozen \) && !IS_TRUE\( self\.tod_spin_locked \) && !IS_TRUE\( self\.tod_solo_upg_active \) \)\s*self tod_upgrades::menu_freeze\( false \);/.test(closeB),
  'after a takeover the player is unfrozen only once the deal ends, and only if no other menu owns them', 'the takeover close can unfreeze a player mid-deal');
check(/level endon\( "tod_global_upg_takeover" \);\s*sel = self tod_class_select::run_select_input\( TOD_CLS_TERM_SECS, focus \);/.test(fnBody(TERM, 'input_run')),
  'the input dies on the takeover notify (synchronously, before the deal touches the fields)', 'input_run does not end on the takeover');
check(/level waittill\( "tod_global_upg_takeover" \);\s*self\.tod_cls_term_taken = true;\s*self tod_class_select::set_field\( "todClsShow", 0 \);/.test(fnBody(TERM, 'takeover_watch')),
  'the class panel closes in the takeover\'s own frame', 'takeover_watch does not close the panel on the takeover');
check(/if \( IS_TRUE\( self\.tod_cls_term_taken \) \|\| IS_TRUE\( level\.tod_upgrade_pause \) \)\s*\{\s*self close_session\( "takeover" \);/.test(sess)
  && sess.indexOf('self menu_open();') < sess.indexOf('close_session( "takeover" )') && sess.indexOf('close_session( "takeover" )') < sess.indexOf('"todClsShow", TOD_CLS_SHOW_TERMINAL'),
  'a deal landing while the menu opens closes the visit before any field is written', 'the session can write its fields over a deal that landed during menu_open');
check(/self tod_upgrades::menu_freeze\( false \);\s*ok = self do_switch\( from, to \);/.test(sess), 'the hands come back BEFORE the switch (the swap raises the new gun, tier_up\'s order)', 'do_switch runs while weapons are still disabled');
const sw = fnBody(TERM, 'do_switch');
const iArch = sw.indexOf('tod_archer::cleanup( "class_changed" )'), iAssign = sw.indexOf('tod_classes::assign_class( self, to )'), iKit = sw.indexOf('tod_class_kit::kit_switch'), iSwap = sw.indexOf('swap_primary');
check(iArch > 0 && iArch < iAssign && iAssign < iKit && iKit < iSwap, 'the order: the Archer lets go, then the class, then the kit, then the gun (no other thread sees a mixed state)', 'do_switch is out of order');
check(!/\bwait\b/.test(sw.slice(sw.indexOf('// 1. THE OLD CLASS'), iSwap)), 'nothing between the old class letting go and the gun swap yields', 'do_switch yields between the class change and the swap');
check(/self\.tod_pap_owned = undefined;/.test(sw) && sw.indexOf('self.tod_pap_owned = undefined;') < iSwap, 'the PaP latch clears before the new gun lands (it arrives unpacked)', 'the free-PaP latch survives the switch');
check(/self\.tod_tier_busy = true;/.test(sw) && /self\.tod_tier_busy = undefined;/.test(sw), 'the body loop\'s twin reconcile holds off for the switch (tier_up\'s latch)', 'do_switch does not hold the twin reconcile');
check(/tod_necro_summon::bind_cancel\( "class_change" \);\s*self tod_necro_summon::dismiss_all\( "class_change" \);/.test(sw), 'a Necromancer\'s bind drops and his helpers go', 'the Necromancer\'s helpers / bind are not released');
check(/c4 = self tod_class_kit::clear_planted_c4\(\);\s*shield = self clear_shield\(\);/.test(sw) && /function clear_planted_c4\(\)[\s\S]{0,400}deleteWeaponObjectArray\(\)/.test(KIT),
  'a Breacher\'s planted C4 and riot shield leave with the class', 'the Breacher\'s C4 / shield are not cleared');
check(/self\.maxhealth = hp;\s*self SetMaxHealth\( hp \);/.test(sw) && /if \( self\.health > hp \)\s*self\.health = hp;/.test(sw), 'max health moves to the new class\'s floor, both ways (no free heal)', 'the switch does not set the new health floor');
check(/function kit_switch\( from, to \)[\s\S]{0,900}if \( from == TOD_KIT_WARRIOR && to == 0 \)/.test(KIT) && !/from == TOD_KIT_WARRIOR && to != TOD_KIT_WARRIOR/.test(KIT),
  'kit_switch refills the Warrior\'s pinned frag only for a kit-less class (not the C4 or the Necromancer\'s empty grenade)', 'kit_switch still refills the next kit\'s lethal');
check(/if \( to == TOD_KIT_WARRIOR \) self pin_clips\( to \);/.test(KIT), 'a Warrior\'s frag is pinned at 0 the moment the kit arrives', 'the Warrior kit waits a pin tick for its empty frag');
check(/if \( IS_TRUE\( level\.tod_dev_maxed \) \)\s*self thread tod_upgrades::dev_grant_maxed\( self \);/.test(sess), 'dev\'s maxed state follows the switch (the new class maxed like the drafted one)', 'the dev maxed state is lost on a switch');

console.log(`\nCLASS TERMINAL: ${passes} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);
