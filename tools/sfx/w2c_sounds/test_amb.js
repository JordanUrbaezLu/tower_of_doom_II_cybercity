'use strict';
// =============================================================================
// THE WORLD AMBIENCE gate (PK23, 2026-10-05): runs the SHIPPING decision functions of
// scripts/zm/zm_tod2_cybercity/_tod_amb.csc against its GENERATED anchors (_tod_amb_data.csc) through the house
// interpreter (tools/sky_ships/gsc_eval.js) - never a hand-written copy - and checks the module's lanes structurally.
//
//   A. THE ROOMS     every room box classifies as its own kind; the tower above the plaza is open air
//   B. THE BEDS      wind full high, city full low, both silent in the Undercity and the quiet rooms, monotonic in
//                    between, the plaza = its street bed + a breeze; every level inside 0..1
//   C. THE ANCHORS   every room-tone anchor stands inside a room of its own kind, within its loop's reach of the
//                    whole room, and the start / stop hysteresis can never flap
//   D. THE LANES     the beds are loops on client script_origins faded by volume (never a 2D loop nobody can stop),
//                    each emitter start has its stop, drips / knocks only in the Undercity, the logger is gated
//   E. NEGATIVE CONTROLS  a wind left on underground, a plaza that loses its bed, and a dropped stoploopat are caught
//
//   node tools/sfx/w2c_sounds/test_amb.js [--root DIR]        exit 0 = pass
// =============================================================================
const fs = require('fs');
const path = require('path');
const { gscLoad, V } = require('../../sky_ships/gsc_eval.js');

const ai = process.argv.indexOf('--root');
const ROOT = ai > 0 ? path.resolve(process.argv[ai + 1]) : path.join(__dirname, '..', '..', '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8').replace(/\r\n/g, '\n');
const AMB = read('scripts/zm/zm_tod2_cybercity/_tod_amb.csc');
const DATA = read('scripts/zm/zm_tod2_cybercity/_tod_amb_data.csc');
const CSV = read('sound/aliases/tod_amb.csv');

let passes = 0, fails = 0;
function check(ok, good, bad) {
  if (ok) { passes++; } else { fails++; console.log('  FAIL ' + (bad || good)); }
}
function defs(text) {
  const out = {};
  for (const m of text.matchAll(/^#define\s+(\w+)\s+\(?\s*(-?[\d.]+)\s*\)?\s*(?:\/\/.*)?$/gm)) out[m[1]] = Number(m[2]);
  return out;
}
const D = defs(AMB);
const IS_TRUE = v => v === true || v === 1;
function load(ambText) {
  return gscLoad([['tod_amb', ambText], ['tod_amb_data', DATA]], defs(ambText), { builtins: { IS_TRUE } });
}
const g = load(AMB);
const kinds = g.call('tod_amb_data::room_kinds', []);
const mins = g.call('tod_amb_data::room_mins', []);
const maxs = g.call('tod_amb_data::room_maxs', []);
const ekinds = g.call('tod_amb_data::emitter_kinds', []);
const eorgs = g.call('tod_amb_data::emitter_orgs', []);
const near = (a, b) => Math.abs(a - b) < 1e-6;
const centre = i => V((mins[i][0] + maxs[i][0]) / 2, (mins[i][1] + maxs[i][1]) / 2, mins[i][2] + 64);
const firstKindAt = p => {
  for (let i = 0; i < kinds.length; i++) {
    const pad = D.TOD_AMB_ROOM_PAD;
    if (p[0] >= mins[i][0] - pad && p[0] <= maxs[i][0] + pad && p[1] >= mins[i][1] - pad && p[1] <= maxs[i][1] + pad
      && p[2] >= mins[i][2] - pad && p[2] <= maxs[i][2] + pad) return kinds[i];
  }
  return '';
};

// ---- A. THE ROOMS -----------------------------------------------------------
check(kinds.length === g.call('tod_amb_data::room_count', []) && mins.length === kinds.length && maxs.length === kinds.length,
  'A: the room tables agree in size', 'A: room_kinds / room_mins / room_maxs / room_count disagree');
check(['undercity', 'plaza', 'quiet'].every(k => kinds.includes(k)), 'A: all three room kinds are generated', 'A: a room kind is missing from the data');
for (let i = 0; i < kinds.length; i++) {
  const c = centre(i);
  const k = g.call('room_kind_at', [c]);
  check(k === firstKindAt(c), 'A: room ' + i, 'A: room ' + i + ' (' + kinds[i] + ') centre classifies as "' + k + '"');
  check(g.call('room_index_at', [c]) >= 0, 'A: room_index_at finds room ' + i, 'A: room_index_at misses room ' + i + "'s own centre");
}
// the plaza is the ground at the tower's foot: the open tower above it, the crown and the descent are open air
for (const p of [V(0, 0, 2000), V(0, 0, 9000), V(0, 5320, 19392), V(0, -790, 1500)])
  check(g.call('room_kind_at', [p]) === '', 'A: open air at ' + p, 'A: ' + p + ' classifies as a room (' + g.call('room_kind_at', [p]) + ')');

// ---- B. THE BEDS ------------------------------------------------------------
const lv = (p, k) => g.call('bed_levels', [p, k]);
const inUnit = v => v[0] >= 0 && v[0] <= 1 && v[1] >= 0 && v[1] <= 1;
let prev = null, mono = true, unit = true;
for (let z = 21000; z >= -600; z -= 150) {
  const v = lv(V(0, 5000, z), '');
  unit = unit && inUnit(v);
  if (prev && (v[0] > prev[0] + 1e-9 || v[1] < prev[1] - 1e-9)) mono = false;
  prev = v;
}
check(mono, 'B: descending, the wind never rises and the far city never falls', 'B: the beds are not monotonic in height');
check(unit, 'B: every bed level stays inside 0..1', 'B: a bed level left 0..1');
const top = lv(V(0, 5000, 19392), '');
check(near(top[0], 1) && near(top[1], 0), 'B: the crown hears full wind and no city', 'B: crown levels ' + top);
const low = lv(V(0, 5000, 600), '');
check(near(low[0], D.TOD_AMB_WIND_FLOOR) && near(low[1], 1), 'B: the ground hears the far city and a breeze', 'B: ground levels ' + low);
const mid = lv(V(0, 5000, 5000), '');
check(mid[0] > D.TOD_AMB_WIND_FLOOR && mid[0] < 1 && mid[1] > 0 && mid[1] < 1, 'B: mid-tower blends both', 'B: mid levels ' + mid);
for (const k of ['undercity', 'quiet']) {
  const v = lv(V(0, 0, 0), k);
  check(near(v[0], 0) && near(v[1], 0), 'B: ' + k + ' mutes both beds', 'B: ' + k + ' levels ' + v);
}
const pz = lv(V(0, 0, 80), 'plaza');
check(near(pz[0], D.TOD_AMB_WIND_FLOOR) && near(pz[1], 1), 'B: the plaza = full far city + a breeze', 'B: plaza levels ' + pz);

// ---- C. THE ANCHORS ---------------------------------------------------------
check(ekinds.length === eorgs.length && ekinds.length === g.call('tod_amb_data::emitter_count', []) && ekinds.length > 0,
  'C: the anchor tables agree', 'C: emitter tables disagree');
const reach = {};
for (const line of CSV.split('\n')) {
  const c = line.split(',');
  if (c[0] === 'tod_amb_undercity_lp' || c[0] === 'tod_amb_plaza_lp') reach[c[0]] = Number(c[20]);
}
for (let i = 0; i < ekinds.length; i++) {
  const k = g.call('room_kind_at', [eorgs[i]]);
  check(k === ekinds[i], 'C: anchor ' + i, 'C: anchor ' + i + ' (' + ekinds[i] + ') stands in "' + k + '"');
}
// every Undercity / plaza room box has an anchor of its kind whose loop reaches its farthest corner
for (let i = 0; i < kinds.length; i++) {
  if (kinds[i] === 'quiet') continue;
  const alias = kinds[i] === 'undercity' ? 'tod_amb_undercity_lp' : 'tod_amb_plaza_lp';
  const R = reach[alias];
  const corners = [];
  for (const x of [mins[i][0], maxs[i][0]]) for (const y of [mins[i][1], maxs[i][1]]) corners.push([x, y, mins[i][2] + 64]);
  const worst = Math.max(...corners.map(c => Math.min(...eorgs.map((o, j) => ekinds[j] === kinds[i]
    ? Math.hypot(c[0] - o[0], c[1] - o[1], c[2] - o[2]) : 1e9))));
  check(R > 0 && worst <= R, 'C: room ' + i + ' is in reach of its tone', 'C: room ' + i + ' corner is ' + Math.round(worst) + ' from its nearest tone (DistMaxDry ' + R + ')');
}
check(D.TOD_AMB_EMIT_OFF > D.TOD_AMB_EMIT_ON && D.TOD_AMB_EMIT_ON >= Math.max(reach.tod_amb_undercity_lp || 0, reach.tod_amb_plaza_lp || 0),
  'C: an anchor starts before its loop can be heard and the hysteresis cannot flap', 'C: EMIT_ON / EMIT_OFF are wrong for the loops\' reach');

// ---- D. THE LANES -----------------------------------------------------------
const body = name => { const a = AMB.split('function ' + name + '(')[1]; return a ? a.split('\nfunction ')[0] : ''; };
const RUN = body('run'), EMIT = body('emitters'), LOG = body('amb_log');
check(/wind_host = Spawn\( localClientNum, [^;]*"script_origin" \)/.test(RUN) && /city_host = Spawn\( localClientNum, [^;]*"script_origin" \)/.test(RUN),
  'D: each bed rides its own client script_origin', 'D: a bed is not on a client script_origin');
check(/wind_host PlayLoopSound\( "tod_amb_tower_wind"/.test(RUN) && /city_host PlayLoopSound\( "tod_amb_city_far"/.test(RUN),
  'D: the beds are entity loops (stoppable by handle)', 'D: a bed is played some other way');
check(/SetSoundVolume\( wind, lv\[ 0 \] \)/.test(RUN) && /SetSoundVolume\( city, lv\[ 1 \] \)/.test(RUN) && /SetSoundVolumeRate\( wind,/.test(RUN) && /SetSoundVolumeRate\( city,/.test(RUN),
  'D: the beds are faded by volume every tick', 'D: the beds are not faded by volume');
check(/waitrealtime\(/.test(RUN) && !/\bwait\s/.test(RUN), 'D: the loop ticks in real time (a client wait counts frames)', 'D: run() uses a frame-counted wait');
const starts = (EMIT.match(/audio::playloopat\(/g) || []).length, stops = (EMIT.match(/audio::stoploopat\(/g) || []).length;
check(starts > 0 && starts === stops, 'D: every emitter start has its stop', 'D: playloopat ' + starts + ' vs stoploopat ' + stops);
check(/if \( kind == "undercity" \)\s*\{[^]*?"tod_amb_drip"[^]*?"tod_amb_pipe"/.test(RUN), 'D: drips and knocks fall only in the Undercity', 'D: the drips / knocks escaped the Undercity branch');
check(/if \( lv\[ 0 \] >= TOD_AMB_GUST_WIND \)/.test(RUN), 'D: gusts only where the wind is strong', 'D: gusts are not gated on the wind');
check(/if \( !TOD_AMB_LOG \)\s*return;/.test(LOG) && /\/#\s*PrintLn\( line \);\s*#\//.test(LOG), 'D: the logger is gated and its PrintLn sits in a dev block',
  'D: amb_log is ungated or prints outside /# #/');
check(!/PlaySoundAtPosition/i.test(AMB), 'D: no PlaySoundAtPosition (it fails a CSC load)', 'D: PlaySoundAtPosition in a CSC');
for (const a of ['tod_amb_tower_wind', 'tod_amb_city_far', 'tod_amb_undercity_lp', 'tod_amb_plaza_lp']) {
  const row = CSV.split('\n').find(l => l.startsWith(a + ','));
  check(row && /,LOOPING,/.test(row), 'D: ' + a + ' is a LOOPING row', 'D: ' + a + ' is missing or not LOOPING in tod_amb.csv');
}
for (const a of ['tod_amb_gust', 'tod_amb_drip', 'tod_amb_pipe']) {
  const row = CSV.split('\n').find(l => l.startsWith(a + ','));
  check(row && /,3d,/.test(row) && /,NONLOOPING/.test(row), 'D: ' + a + ' is a 3D one-shot', 'D: ' + a + ' is not a 3D one-shot');
}

// ---- E. NEGATIVE CONTROLS ---------------------------------------------------
function caught(label, mutated, probe) {
  let hit;
  try { hit = probe(load(mutated)); } catch (e) { hit = true; }
  check(hit, 'E: caught - ' + label, 'E: MISSED - ' + label);
}
const BED_GATE = 'if ( kind == "undercity" || kind == "quiet" )';
check(AMB.includes(BED_GATE), 'E: the bed gate is where the controls expect it', 'E: the negative controls cannot find the bed gate');
caught('the wind left on underground', AMB.replace(BED_GATE, 'if ( kind == "quiet" )'),
  m => { const v = m.call('bed_levels', [V(0, 0, 0), 'undercity']); return !(near(v[0], 0) && near(v[1], 0)); });
const PLAZA = /(if \( kind == "plaza" \)\s*\{\s*wind = TOD_AMB_WIND_FLOOR;\s*)c = 1;/;
check(PLAZA.test(AMB), 'E: the plaza branch is where the controls expect it', 'E: the negative controls cannot find the plaza branch');
caught('the plaza loses its street bed', AMB.replace(PLAZA, '$1c = 0;'),
  m => { const v = m.call('bed_levels', [V(0, 0, 80), 'plaza']); return !near(v[1], 1); });
const dropped = EMIT.replace(/audio::stoploopat\( "tod_amb_plaza_lp", orgs\[ i \] \);/, ';');
check(dropped !== EMIT && (dropped.match(/audio::stoploopat\(/g) || []).length !== (dropped.match(/audio::playloopat\(/g) || []).length,
  'E: caught - a dropped stoploopat', 'E: MISSED - a dropped stoploopat');

console.log((fails ? 'AMBIENCE FAIL: ' + fails + ' failed, ' : 'AMBIENCE PASS: ') + passes + ' checks - ' + kinds.length + ' rooms ('
  + kinds.filter(k => k === 'undercity').length + ' Undercity, ' + kinds.filter(k => k === 'plaza').length + ' plaza, '
  + kinds.filter(k => k === 'quiet').length + ' quiet), ' + ekinds.length + ' anchors; beds by height, rooms, reach, lanes, 3 negative controls');
process.exit(fails ? 1 : 0);
