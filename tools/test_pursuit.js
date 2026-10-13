'use strict';
// tools/test_pursuit.js — THE PURSUIT's build gate (docs/200).
//
// Runs the SHIPPING GSC of _tod_reach.gsc (the walk model), _tod_stray.gsc's pure
// lane functions and destination filter, and _tod_recall.gsc's verdict through
// tools/sky_ships/gsc_eval.js, against the REAL generated data (_tod_door_data's
// 24 drop rows, _tod_crown_data's island, _tod_arena_data's room). Then:
//   * LOCKSTEP — the model's constants against tools/gen_tower_map.js and
//     tools/broken_tower_layout.js (the drops' heights pin both cut offsets);
//   * WIRING — the spawn hook, the targeting hook, the elite picker, the zone and
//     the init calls actually reach the model;
//   * NEGATIVE CONTROLS — mutants of the shipping code, each of which must be
//     caught by the suite (a gate that cannot fail is not a gate).
// Usage: node tools/test_pursuit.js
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8').replace(/\r\n/g, '\n');
const { gscLoad, V } = require('./sky_ships/gsc_eval.js');

const S = 'scripts/zm/zm_tod2_cybercity/';
const REACH = read(S + '_tod_reach.gsc');
const STRAY = read(S + '_tod_stray.gsc');
const RECALL = read(S + '_tod_recall.gsc');
const DOORS = read(S + '_tod_door_data.gsc');
const CROWN = read(S + '_tod_crown_data.gsc');
const ARENA = read(S + '_tod_arena_data.gsc');
const HOUSE = read(S + '_tod_house_data.gsc');   // docs/207: the reach's region test reads it beside the arena's
const GEN = read('tools/gen_tower_map.js');
const LAYOUT = require('./broken_tower_layout.js');

let fails = 0, checks = 0;
function check(ok, label) {
  checks++;
  if (!ok) { fails++; console.log('FAIL ' + label); }
}

// ---------------------------------------------------------------------------
// The generated drop table, parsed the way test_broken_tower.js does it (the
// generated file is a switch statement, which gsc_eval does not interpret).
// ---------------------------------------------------------------------------
const drops = new Map();
for (const lap of LAYOUT.DROP_LAPS) {
  const text = DOORS.split(`case ${lap}:`)[1].split('return r;')[0];
  const row = { lap, flag: `enter_lap${lap}` };
  for (const key of ['upper', 'lower', 'lo', 'hi']) row[key] = V(...text.match(new RegExp(`r\\.${key} = \\( ([^)]*) \\)`))[1].split(',').map(Number));
  drops.set(lap, row);
}

// ---------------------------------------------------------------------------
// LOCKSTEP with the generator.
// ---------------------------------------------------------------------------
const defs = text => Object.fromEntries([...text.matchAll(/^#define\s+(\w+)\s+(-?[\d.]+)/gm)].map(m => [m[1], m[2]]));
const RD = defs(REACH), SD = defs(STRAY), CD = defs(RECALL);
const genLaps = +GEN.match(/^const LAPS = (\d+);/m)[1];
const gs = GEN.match(/^const STEPS = (\d+), TREAD = (\d+), RISE = (\d+);/m);
const genRise = 2 * (+gs[1]) * (+gs[3]), riser = +gs[3];
check(+RD.TOD_REACH_LAPS === genLaps, `TOD_REACH_LAPS ${RD.TOD_REACH_LAPS} == gen LAPS ${genLaps}`);
check(+RD.TOD_REACH_LAP_RISE === genRise, `TOD_REACH_LAP_RISE ${RD.TOD_REACH_LAP_RISE} == gen LAP_RISE ${genRise}`);
check(+RD.TOD_REACH_DOOR_CUT > 2 && +RD.TOD_REACH_DOOR_CUT < riser, `door cut +${RD.TOD_REACH_DOOR_CUT} sits between the landing (+0..2) and the first tread (+${riser})`);
check(drops.size === 24, '24 generated drop rows');
for (const r of drops.values()) {
  const b = (r.lap - 1) * genRise;
  check(r.lower[2] - b < +RD.TOD_REACH_DROP_CUT && r.upper[2] - b > +RD.TOD_REACH_DROP_CUT,
    `drop ${r.lap}: deck +${r.lower[2] - b} < cut +${RD.TOD_REACH_DROP_CUT} < ledge +${r.upper[2] - b}`);
  check(r.hi[2] - b < +RD.TOD_REACH_DROP_CUT, `drop ${r.lap}: the catch landing volume (top +${r.hi[2] - b}) is wholly below the cut`);
}
// Every door the model gates must exist with the flag the zone graph uses, on its lap's floor.
for (let k = 1; k <= genLaps; k++) {
  if (drops.has(k)) continue;
  const m = DOORS.match(new RegExp(`case "enter_lap${k}":\\s*info\\.org = \\( (-?\\d+), (-?\\d+), (-?\\d+) \\)`));
  check(!!m, `door enter_lap${k} in the generated door table`);
  if (m) check(+m[3] - (k - 1) * genRise === 40, `door enter_lap${k} trigger sits on floor ${k - 1} (+40)`);
}
check(/case "enter_roof":/.test(DOORS), 'enter_roof in the generated door table');

// ---------------------------------------------------------------------------
// The interpreter harness. `texts` lets the negative controls swap in mutants.
// ---------------------------------------------------------------------------
const IS_TRUE = x => x !== undefined && x !== null && !!x && x !== 0;
function translate(t) {
  return t.replace(/level flag::exists\(/g, 'flag_exists(')
          .replace(/level flag::get\(/g, 'flag_get(')
          .replace(/(\w+) laststand::player_is_in_laststand\(\)/g, 'laststand_of( $1 )')
          .replace(/\[\[ level\.tod_haven_inside_fn \]\]\( org \)/g, 'haven_inside_stub( org )');   // docs/202: the haven filter's pointer call
}
function load(reach, stray, recall, env) {
  const all = { ...defs(reach), ...defs(stray), ...defs(recall) };
  const g = gscLoad([
    ['tod_reach', translate(reach)], ['tod_stray', translate(stray)], ['tod_recall', translate(recall)],
    ['tod_crown_data', CROWN], ['tod_arena_data', ARENA], ['tod_house_data', HOUSE],
  ], all, {
    builtins: {
      IS_TRUE,
      'tod_door_data::get_drop_info': lap => drops.get(lap),
      haven_inside_stub: o => !!(env.havenAt && env.havenAt(o)),   // docs/202: a test sets env.havenAt to put a field somewhere
      flag_exists: f => env.flags[f] !== undefined,
      flag_get: f => !!env.flags[f],
      laststand_of: p => !!p.downed,
      Distance2D: (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]),
      DistanceSquared: (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2,
      GetPlayers: () => env.players, isplayer: p => !!p, isalive: p => !!p && p.alive !== false,
      GetTime: () => env.now || 0,
    },
  });
  return g;
}
// A tower with every lap door and the roof SHUT (the descent's start), or OPEN.
function towerFlags(open) {
  const f = {};
  for (let k = 1; k <= genLaps; k++) if (!drops.has(k)) f['enter_lap' + k] = open;
  f.enter_roof = open;
  return f;
}
const L = (lap, off) => (lap - 1) * genRise + off;     // a height on lap `lap`
const P = (x, y, z, extra = {}) => ({ origin: V(x, y, z), last_valid_position: V(x, y, z), sessionstate: 'playing', ...extra });

function suite(reach, stray, recall) {
  const out = [];
  const t = (ok, label) => { if (!ok) out.push(label); };
  const env = { flags: towerFlags(true), players: [] };
  const g = load(reach, stray, recall, env);
  g.call('tod_reach::build_cuts', []);
  g.level.tod_reach_ready = true;
  g.level.tod_reach_spawn_kept = 0; g.level.tod_reach_spawn_cut = 0; g.level.tod_reach_spawn_open = 0; g.level.tod_reach_spawn_far = 0;
  const reachOk = (a, b) => g.call('tod_reach::can_reach', [a, b]);

  // THE DROPS — every one of the 24, on the real generated coordinates.
  for (const r of drops.values()) {
    t(!reachOk(r.lower, r.upper), `drop ${r.lap}: a zombie on the catch deck cannot climb to the ledge`);
    t(reachOk(r.upper, r.lower), `drop ${r.lap}: a zombie on the ledge can drop to the deck`);
  }
  // The 2026-10-01 run's exact pair: zombie on lap 43's deck, player on its ledge.
  t(!reachOk(V(305, 255, 16130), V(305, 255, 16320)), 'the logged lap-43 strand (deck 16130 -> ledge 16320) is unreachable');
  // Whole tower, every door open: top to bottom yes, bottom to top no (24 drops in the way).
  t(reachOk(V(0, 960, 19392), V(0, 0, 0)), 'terrace -> plaza walks down the whole open tower');
  t(!reachOk(V(0, 0, 0), V(0, 960, 19392)), 'plaza -> terrace is blocked (drops are down-only)');
  t(reachOk(V(-336, -336, L(2, 192)), V(336, -336, L(1, 0))), 'lap 2 -> lap 1 (doors only between) walks');
  t(reachOk(V(336, -336, L(1, 100)), V(-336, -336, L(2, 192))), 'lap 1 -> lap 2 climbs through an open door');
  // Doors.
  env.flags = towerFlags(false);
  g.call('tod_reach::rebuild_closed', []);
  t(!reachOk(V(336, -336, L(12, 192)), V(336, -336, L(10, 192))), 'a shut door blocks the walk down (lap 12 -> lap 10)');
  t(!reachOk(V(336, -336, L(10, 192)), V(336, -336, L(12, 192))), 'a shut door blocks the walk up (lap 10 -> lap 12)');
  t(!reachOk(V(0, 0, -384), V(336, -256, 100)), 'the Undercity cannot reach lap 1 through a shut enter_lap1');
  t(!reachOk(V(0, 960, 19392), V(0, 0, L(50, 300))), 'the terrace cannot reach lap 50 through a shut enter_roof');
  t(reachOk(V(336, -336, L(10, 100)), V(-336, -336, L(10, 300))), 'one lap, no cut between: always reachable');
  t(reachOk(V(-336, -336, L(10, 192)), V(-750, -460, L(10, 192))), 'lap 10 stairs <-> its lounge (same height band)');
  env.flags = towerFlags(true);
  env.flags.enter_lap11 = false;
  g.call('tod_reach::rebuild_closed', []);
  t(!reachOk(V(336, -336, L(11, 192)), V(336, -336, L(10, 192))), 'only enter_lap11 shut: lap 11 -> lap 10 blocked');
  t(reachOk(V(336, -336, L(12, 192)), V(336, -336, L(11, 192))), 'only enter_lap11 shut: lap 12 -> lap 11 open');
  // An unknown flag never blocks (fail open).
  env.flags = towerFlags(true);
  delete env.flags.enter_lap12;
  g.call('tod_reach::rebuild_closed', []);
  t(reachOk(V(336, -336, L(12, 192)), V(336, -336, L(11, 192))), 'an unknown door flag fails OPEN');
  env.flags = towerFlags(true);
  g.call('tod_reach::rebuild_closed', []);
  // Regions.
  const hall = V(0, 8608, 19392), terrace = V(0, 960, 19392), arena = V(-8000, -7552, 0), base = V(0, 0, 0);
  t(!reachOk(hall, terrace) && !reachOk(terrace, hall), 'crown island <-> terrace: no walk either way (the pad is one-way, players only)');
  t(!reachOk(arena, base) && !reachOk(base, arena), 'arena <-> tower: no walk either way');
  t(reachOk(V(-8000, -8448, 0), V(-7552, -8000, 0)), 'inside the arena: always');
  t(reachOk(hall, V(0, 5320, 19392)), 'hall -> balcony (one island)');
  // Fail-open edges.
  t(reachOk(undefined, terrace) && reachOk(terrace, undefined), 'undefined points fail open');
  g.level.tod_reach_ready = false;
  t(reachOk(V(0, 0, 0), V(0, 960, 19392)), 'an uninitialised model fails open');
  g.level.tod_reach_ready = true;

  // closest(): a player it can reach beats a nearer one it cannot.
  const r43 = drops.get(43);
  const onLedge = P(r43.upper[0], r43.upper[1], r43.upper[2]);
  const below = P(336, -336, L(41, 192));
  const zDeck = r43.lower;
  t(g.call('tod_reach::closest', [zDeck, [onLedge, below]]) === below, 'closest(): the reachable player below wins over the nearer one on the ledge');
  t(g.call('tod_reach::closest', [zDeck, [onLedge]]) === onLedge, 'closest(): nobody reachable -> still a target (the nearest)');
  const near = P(-336, -336, L(30, 192)), farP = P(-336, -336, L(25, 192));
  t(g.call('tod_reach::closest', [V(-336, -336, L(31, 300)), [farP, near]]) === near, 'closest(): among reachable players the cheaper walk wins');
  t(g.call('tod_reach::reachable_players', [zDeck, [onLedge, below]]).length === 1, 'reachable_players() drops the unreachable one');
  t(g.call('tod_reach::reachable_players', [zDeck, [onLedge]]).length === 1, 'reachable_players() never empties the list');

  // filter_spawns(): the root fix — no riser below a drop while the party is above it.
  env.players = [P(r43.upper[0], r43.upper[1], r43.upper[2])];
  const riserBelow = { origin: V(336, 336, L(42, 192)) }, riserDeck = { origin: r43.lower };
  const riserAbove = { origin: V(-336, 336, L(43, 384)) }, riserLedge = { origin: r43.upper };
  let kept = g.call('tod_reach::filter_spawns', [[riserBelow, riserDeck, riserAbove, riserLedge]]);
  t(kept.length === 2 && kept.includes(riserAbove) && kept.includes(riserLedge), 'filter_spawns(): only the risers above the drop survive while the player is on the ledge');
  env.players = [P(336, -336, L(42, 300))];
  kept = g.call('tod_reach::filter_spawns', [[riserBelow, riserDeck, riserLedge]]);
  t(kept.length === 3, 'filter_spawns(): with the player below, every riser above (and near) can drop to him');
  // PREFER NEAR: a reachable riser beyond the hunt's bar is skipped while a near one exists...
  env.players = [P(336, -336, L(41, 192))];
  const riserFar = { origin: V(-336, 336, L(45, 384)) };
  kept = g.call('tod_reach::filter_spawns', [[riserBelow, riserFar]]);
  t(kept.length === 1 && kept[0] === riserBelow, 'filter_spawns(): a far reachable riser is skipped while a near one exists');
  // ...and kept when it is the only reachable riser (soft preference).
  kept = g.call('tod_reach::filter_spawns', [[riserFar]]);
  t(kept.length === 1 && kept[0] === riserFar, 'filter_spawns(): a far reachable riser is kept when nothing near exists');
  // The reach test, on its own: the deck under the ledge is NEAR but unreachable,
  // the only reachable riser is far — the deck must still be dropped.
  env.players = [P(r43.upper[0], r43.upper[1], r43.upper[2])];
  kept = g.call('tod_reach::filter_spawns', [[riserDeck, riserFar]]);
  t(kept.length === 1 && kept[0] === riserFar, 'filter_spawns(): an unreachable riser is dropped even when every reachable one is far');
  env.players = [P(0, 8608, 19392)];
  kept = g.call('tod_reach::filter_spawns', [[riserBelow, riserDeck]]);
  t(kept.length === 2, 'filter_spawns(): a pool with nobody reachable is left to stock (fail-safe)');
  env.players = [P(r43.upper[0], r43.upper[1], r43.upper[2], { downed: true }), P(336, -336, L(41, 192))];
  kept = g.call('tod_reach::filter_spawns', [[riserDeck, riserAbove]]);
  t(kept.length === 2, 'filter_spawns(): anchors on upright players only while one exists');
  env.players = [P(r43.upper[0], r43.upper[1], r43.upper[2], { tod_jumppad_flying: true }), P(r43.lower[0], r43.lower[1], r43.lower[2])];
  kept = g.call('tod_reach::filter_spawns', [[riserDeck]]);
  t(kept.length === 1, 'filter_spawns(): a jump-pad flyer anchors nothing');

  // THE HUNT's pure pieces.
  t(g.call('tod_stray::lane_of', [-1]) === 'unreach', 'lane_of(-1) = unreach');
  t(g.call('tod_stray::lane_of', [+SD.TOD_STRAY_COST + 1]) === 'far', 'lane_of(cost+1) = far');
  t(g.call('tod_stray::lane_of', [+SD.TOD_STRAY_COST]) === '', 'lane_of(cost) = fine');
  t(!g.call('tod_stray::due', ['unreach', +SD.TOD_STRAY_UNREACH_MS - 1, false]) && g.call('tod_stray::due', ['unreach', +SD.TOD_STRAY_UNREACH_MS, false]), 'due(unreach) at TOD_STRAY_UNREACH_MS');
  t(!g.call('tod_stray::due', ['far', +SD.TOD_STRAY_PATIENCE - 1, false]) && g.call('tod_stray::due', ['far', +SD.TOD_STRAY_PATIENCE, false]), 'due(far) at TOD_STRAY_PATIENCE');
  t(g.call('tod_stray::due', ['far', 0, true]), 'a teleport pump waives the wait');
  // dest_ok(): a relocation never lands below a drop, never too far, never in a face.
  env.players = [P(r43.upper[0], r43.upper[1], r43.upper[2])];
  g.level.tod_gate_open = true;
  const goal = r43.upper;
  t(!g.call('tod_stray::dest_ok', [r43.lower, goal]), 'dest_ok(): the catch deck under the player is refused');
  t(!g.call('tod_stray::dest_ok', [V(336, -336, L(42, 192)), goal]), 'dest_ok(): a riser a floor below the drop (past DEST_MIN, inside the cost) is refused');
  t(g.call('tod_stray::dest_ok', [V(-336, 336, L(43, 384)), goal]), 'dest_ok(): the floor above the ledge is accepted');
  t(!g.call('tod_stray::dest_ok', [V(r43.upper[0], r43.upper[1] - 100, r43.upper[2]), goal]), 'dest_ok(): inside DEST_MIN of a player is refused');
  t(!g.call('tod_stray::dest_ok', [V(-336, 336, L(49, 300)), goal]), 'dest_ok(): a spot still too far is refused');
  t(!g.call('tod_stray::dest_ok', [V(0, 8000, 19392), goal]), 'dest_ok(): another region is refused');
  // THE HAVENS (docs/202): a spot inside a live safe-zone field is refused; the same spot with no field is not.
  const haven = V(-336, 336, L(43, 384));
  g.level.tod_haven_inside_fn = 'point_inside_live';
  env.havenAt = o => Math.hypot(o[0] - haven[0], o[1] - haven[1]) < 240 && Math.abs(o[2] - haven[2]) < 96;
  t(!g.call('tod_stray::dest_ok', [haven, goal]), 'dest_ok(): a spot inside a live haven field is refused');
  env.havenAt = () => false;
  t(g.call('tod_stray::dest_ok', [haven, goal]), 'dest_ok(): the same spot with no field there is accepted');
  g.level.tod_haven_inside_fn = undefined;
  env.havenAt = undefined;

  // THE RECALL's verdict (rev 2, user 2026-10-02: "Teleporting to safety should only
  // be when you fall of the map completely ... fine with players trying to hack and
  // jump down all the way").
  const st = () => ({});
  const dec = (s, now, z, vz, settled, inmap, floor) => g.call('tod_recall::decide', [s, now, z, vz, settled, inmap, floor]);
  const FZ = +CD.TOD_RECALL_FALL_Z, VZ = +CD.TOD_RECALL_VOID_Z, OOB = +CD.TOD_RECALL_OOB_MS;
  let s = st(); s.fall_ref = 19392;
  t(dec(s, 0, 19392 - FZ - 1, -300, false, true, false) === 'fall', 'FALL: two floors below the safe spot, falling, nothing under him -> returned');
  s = st(); s.fall_ref = 19392;
  t(dec(s, 0, 19392 - FZ - 1, -300, false, true, true) === '', 'FALL: the same drop with a floor under him (jumping down the tower) is never judged');
  s = st(); s.fall_ref = 19392;
  t(dec(s, 0, 19392 - 20 * genRise, -3000, false, true, true) === '', 'FALL: twenty floors straight down onto the tower is still allowed');
  t(dec(st(), 0, 18000, -300, false, true, false) === '', 'FALL needs a safe reference (none after a teleport/exemption)');
  s = st(); s.fall_ref = 19392;
  t(dec(s, 0, 19392 - 190, -300, false, true, false) === '', 'FALL: a 190 drop is not a fall');
  s = st(); s.fall_ref = 19392;
  t(dec(s, 0, 19392 - FZ - 1, 50, false, true, false) === '', 'FALL: moving up (a launch) is not a fall');
  // THE VOID: under the Undercity floor only the sealed sky floor exists.
  t(dec(st(), 0, VZ - 1, -300, false, false, false) === 'void', 'VOID: falling past the lowest floor on the map -> returned');
  t(dec(st(), 0, VZ - 64, 0, true, false, true) === 'void', 'VOID: standing on the sealed sky floor -> returned');
  t(dec(st(), 0, -genRise, 0, true, true, true) === '', 'VOID: the Undercity floor itself is not the void');
  // OFF THE MAP: standing in no zone at all.
  s = st();
  t(dec(s, 1000, 0, 0, true, false, true) === '' && dec(s, 1000 + OOB - 1, 0, 0, true, false, true) === '', 'OFF THE MAP waits TOD_RECALL_OOB_MS');
  t(dec(s, 1000 + OOB, 0, 0, true, false, true) === 'oob', 'OFF THE MAP returns after TOD_RECALL_OOB_MS');
  s = st();
  t(dec(s, 1000, 5000, -400, false, false, true) === '' && dec(s, 1000 + OOB + 500, 4000, -600, false, false, true) === '',
    'OFF THE MAP: a player in the air outside every zone is never timed (a long drop down the tower)');
  s = st();
  dec(s, 1000, 0, 0, true, false, true);
  t(dec(s, 1500, 40, 100, false, false, true) === '', 'OFF THE MAP: a hop holds the clock...');
  t(dec(s, 1000 + OOB, 0, 0, true, false, true) === 'oob', '...so hopping cannot dodge the return');
  s = st();
  dec(s, 1000, 0, 0, true, false, true);
  dec(s, 1500, 0, 0, true, true, true);
  t(dec(s, 1000 + OOB, 0, 0, true, false, true) === '', 'OFF THE MAP: stepping back onto the map clears the clock');
  s = st(); s.cool_until = 5000;
  dec(s, 1000, 0, 0, true, false, true);
  t(dec(s, 2100, 0, 0, true, false, true) === '', 'OFF THE MAP respects the cooldown');
  // ON THE MAP (any zone, enabled or not, near the navmesh or not): never returned.
  s = st(); s.fall_ref = L(30, 192);
  t([0, 1000, 5000, 60000].every(n => dec(s, n, L(20, 192), 0, true, true, true) === ''), 'ON THE MAP: standing ten floors down, below unbought doors, is never returned');
  // THE PRICE: he arrives at 1 HP; a downed player keeps his last stand.
  t(g.call('tod_recall::arrival_health', [150, false]) === 1, 'arrival_health(): an upright player arrives at 1 HP');
  t(g.call('tod_recall::arrival_health', [37, true]) === 37, 'arrival_health(): a downed player keeps his last stand untouched');
  // Teleport vs fall: a big move the player's own velocity cannot explain is a teleport...
  t(g.call('tod_recall::is_teleport', [5000, 0]), 'is_teleport(): a 5000-unit move at rest is a teleport');
  t(!g.call('tod_recall::is_teleport', [+CD.TOD_RECALL_JUMP_DIST, 0]), 'is_teleport(): nothing under TOD_RECALL_JUMP_DIST is a teleport');
  // ...and a terminal-velocity fall (4000 u/s -> 800 a tick) is NOT, or a void fall would never be judged.
  t(!g.call('tod_recall::is_teleport', [800, 4000]), 'is_teleport(): a 4000 u/s fall is not a teleport');
  t(g.call('tod_recall::is_teleport', [8000, 4000]), 'is_teleport(): a ride far beyond the fall speed still is');
  t(g.call('tod_recall::is_safe', [true, true, +CD.TOD_RECALL_SAFE_GAP, false]) && !g.call('tod_recall::is_safe', [false, true, 0, false])
    && !g.call('tod_recall::is_safe', [true, false, 0, false]) && !g.call('tod_recall::is_safe', [true, true, 0, true])
    && !g.call('tod_recall::is_safe', [true, true, +CD.TOD_RECALL_SAFE_GAP + 1, false]), 'is_safe(): grounded, on the map, on the mesh, upright');
  return out;
}

const base = suite(REACH, STRAY, RECALL);
for (const f of base) { fails++; console.log('FAIL ' + f); }
checks += 1;

// ---------------------------------------------------------------------------
// POLICY PINS — the user's asks, so a later retune is a decision, not a drift.
// ---------------------------------------------------------------------------
check(+SD.TOD_STRAY_COST <= 3000 && +SD.TOD_STRAY_COST >= 1800, `TOD_STRAY_COST ${SD.TOD_STRAY_COST}: cut from TOD1's 6000 ("cut that distance"), and still > one lap + the hall`);
check(+SD.TOD_STRAY_PATIENCE <= 4000, `TOD_STRAY_PATIENCE ${SD.TOD_STRAY_PATIENCE} <= 4000 (TOD1: 8000)`);
check(+SD.TOD_STRAY_UNREACH_MS < +SD.TOD_STRAY_PATIENCE, 'an unreachable zombie moves sooner than a far one');
check(+RD.TOD_REACH_SPAWN_NEAR === +SD.TOD_STRAY_COST, `LOCKSTEP: the spawn filter's near bar (${RD.TOD_REACH_SPAWN_NEAR}) == THE HUNT's far bar (${SD.TOD_STRAY_COST})`);
check(+CD.TOD_RECALL_FALL_Z > 190 * 2, 'a fall is far deeper than a designed drop (190)');
check(+CD.TOD_RECALL_ENABLED === 1, 'THE RECALL is switched on');
// Rev 2 (user 2026-10-02): only a fall off the map is returned, at 1 HP.
check(CD.TOD_RECALL_PERCH_GAP === undefined && !/perch|gap/i.test((RECALL.split('function decide(')[1] || '').split('\nfunction ')[0]),
  'no perch rule: decide() never looks at the navmesh gap, so standing anywhere on the map is never returned (user 2026-10-02)');
check(+CD.TOD_RECALL_ARRIVAL_HP === 1, 'a fall off the map costs all but 1 HP (user 2026-10-02: "at 1 HP")');
check(/^const UC_Z\s+= -LAP_RISE;/m.test(GEN), 'gen: UC_Z (the Undercity floor, the lowest floor on the map) is -LAP_RISE');
{
  const ucZ = -genRise, skyM = GEN.match(/^const SKY_FLOOR = UC_Z - (\d+)/m);
  check(!!skyM, 'gen: SKY_FLOOR sits a fixed depth under UC_Z');
  const skyFloor = skyM ? ucZ - +skyM[1] : NaN;
  check(+CD.TOD_RECALL_VOID_Z < ucZ && +CD.TOD_RECALL_VOID_Z > skyFloor,
    `LOCKSTEP: the void line ${CD.TOD_RECALL_VOID_Z} sits under the Undercity floor (${ucZ}) and over the sealed sky floor (${skyFloor})`);
  const arenaLo = ARENA.match(/org\[ 2 \] >= (-?\d+)/);
  check(!!arenaLo && +arenaLo[1] > +CD.TOD_RECALL_VOID_Z, `the Battle Arena (z >= ${arenaLo && arenaLo[1]}) is above the void line`);
}

// ---------------------------------------------------------------------------
// WIRING — the hooks actually reach the model.
// ---------------------------------------------------------------------------
const MAIN = read('scripts/zm/zm_tod2_cybercity.gsc');
const ENDLESS = read(S + '_tod_endless_rounds.gsc');
const BOSSES = read(S + '_tod_bosses.gsc');
const ZONE = read('zone_source/zm_tod2_cybercity.zone');
const BUILD = read('tools/build_map.ps1');
const fnBody = (text, name) => { const m = text.match(new RegExp('function ' + name + '\\s*\\([^)]*\\)[^\\n{]*\\s*\\{([\\s\\S]*?)\\n\\}')); return m ? m[1] : ''; };
check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_reach;/.test(MAIN) && /#using scripts\\zm\\zm_tod2_cybercity\\_tod_recall;/.test(MAIN), 'zm_tod2_cybercity.gsc #uses _tod_reach and _tod_recall');
check(/tod_reach::init\(\s*\);/.test(MAIN), 'main() builds the walk model');
check(/level thread tod_recall::init\(\s*\);/.test(MAIN), 'main() starts THE RECALL');
const tcp = fnBody(MAIN, 'tod_closest_player');
check(/tod_reach::closest\(\s*origin,\s*players\s*\)/.test(tcp) && /tod_reach::reachable_players\(\s*origin,\s*players\s*\)/.test(tcp), 'tod_closest_player chases the nearest REACHABLE player (both lanes)');
const fss = fnBody(ENDLESS, 'finale_spawn_selection');
check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_reach;/.test(ENDLESS), '_tod_endless_rounds #uses _tod_reach');
check(/^\s*spots = tod_reach::filter_spawns\(\s*spots\s*\);/m.test(fss) && fss.indexOf('tod_reach::filter_spawns') < fss.indexOf('beyond_gate'), 'finale_spawn_selection filters by reach FIRST');
const pick = fnBody(BOSSES, 'pick_spawn_point');
check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_reach;/.test(BOSSES) && /tod_reach::can_reach\(\s*p,\s*anchor\s*\)/.test(pick), 'pick_spawn_point (every elite spawn + relocation) refuses unreachable spots');
check(/scriptparsetree,scripts\/zm\/zm_tod2_cybercity\/_tod_reach\.gsc/.test(ZONE) && /scriptparsetree,scripts\/zm\/zm_tod2_cybercity\/_tod_recall\.gsc/.test(ZONE), 'both new modules are zoned');
check(/test_pursuit\.js/.test(BUILD), 'build_map.ps1 runs this gate');
check(/tod_reach::can_reach\(\s*org,\s*goal\s*\)/.test(fnBody(STRAY, 'dest_ok')), 'THE HUNT validates every destination against the model');
check(/self CanPath\(\s*a,\s*goal\s*\)/.test(fnBody(STRAY, 'first_pathable')), 'THE HUNT asks the engine (CanPath) before using a destination');
check(/level\.player_out_of_playable_area_monitor_callback = &oopa_cb;/.test(RECALL) && /in_kill_brush\(\)/.test(fnBody(RECALL, 'oopa_cb')), 'THE RECALL owns out-of-bounds, kill brushes keep stock\'s verdict');
// Rev 2: the map is ANY zone, enabled or not (a floor below an unbought door).
check(!/zone_is_enabled/.test(fnBody(RECALL, 'map_zone')) && /IsTouching\(/.test(fnBody(RECALL, 'map_zone')), 'map_zone(): every zone counts, enabled or not');
check(/self map_zone\(\) != ""/.test(fnBody(RECALL, 'oopa_cb')) && fnBody(RECALL, 'oopa_cb').indexOf('map_zone') < fnBody(RECALL, 'oopa_cb').indexOf('gave_up'),
  'oopa_cb(): a player on the map (below an unbought door too) is spared stock\'s kill');
check(/inmap = \( zone != "" \);/.test(fnBody(RECALL, 'watch')) && /zone = self map_zone\(\);/.test(fnBody(RECALL, 'watch')), 'watch() judges "on the map" through map_zone()');
check(/BulletTrace\([^;]*TOD_RECALL_VOID_Z/.test(fnBody(RECALL, 'has_floor_below')), 'has_floor_below() traces down to the void line');
check(/floor_below = self has_floor_below\(\);/.test(fnBody(RECALL, 'watch')), 'watch() feeds the floor test into the verdict');
check(/self\.health = arrival_health\( self\.health, downed \);/.test(fnBody(RECALL, 'recall')), 'the return applies the 1 HP price (arrival_health)');
for (const flag of ['tod_jumppad_flying', 'tod_grappling', 'tod_archer_state', 'tod_menu_frozen', 'tod_spin_locked', 'tod_solo_upg_active', 'tod_cls_term_locked', 'tod_upgrade_pause'])
  check(fnBody(RECALL, 'exempt').includes(flag), `THE RECALL never judges a player under ${flag}`);

// ---------------------------------------------------------------------------
// NEGATIVE CONTROLS — each mutant must be caught by the suite above.
// ---------------------------------------------------------------------------
let mutants = 0;
function mutant(label, file, from, to) {
  mutants++;
  const src = { reach: REACH, stray: STRAY, recall: RECALL }[file];
  if (!src.includes(from)) { fails++; console.log(`FAIL negative control "${label}": its anchor text is gone from _tod_${file}.gsc`); return; }
  const m = src.replace(from, to);
  const caught = suite(file === 'reach' ? m : REACH, file === 'stray' ? m : STRAY, file === 'recall' ? m : RECALL);
  checks++;
  if (caught.length === 0) { fails++; console.log(`FAIL negative control "${label}" was NOT caught`); }
}
mutant('drops climbable (upward drop test removed)', 'reach',
  'return ( ( level.tod_reach_drop_pre[ b ] - level.tod_reach_drop_pre[ a ] ) == 0 );', 'return true;');
mutant('drop cut above the ledge', 'reach', '#define TOD_REACH_DROP_CUT    96', '#define TOD_REACH_DROP_CUT    200');
mutant('shut doors ignored', 'reach',
  'if ( !level.tod_reach_cut_drop[ i ] && !door_open( level.tod_reach_cut_flag[ i ] ) )\n\t\t\tadd = 1;', 'if ( false )\n\t\t\tadd = 1;');
mutant('regions ignored', 'reach', 'if ( rf != region_of( to ) )\n\t\treturn false;', '');
mutant('spawn filter returns everything', 'reach', 'level.tod_reach_spawn_kept++;\n\tif ( keep.size < spots.size )', 'level.tod_reach_spawn_kept++;\n\tkeep = spots;\n\tif ( keep.size < spots.size )');
mutant('spawn filter loses its near preference', 'reach', 'if ( near.size > 0 )\n\t{', 'if ( false )\n\t{');
mutant('destination reach test removed', 'stray', 'if ( !tod_reach::can_reach( org, goal ) )\n\t\treturn false;', '');
mutant('haven field guard removed', 'stray', 'if ( isdefined( level.tod_haven_inside_fn ) && [[ level.tod_haven_inside_fn ]]( org ) )\n\t\treturn false;', '');
mutant('teleport test ignores velocity', 'recall', 'return ( dist > speed * TOD_RECALL_TICK * 1.5 + 100 );', 'return true;');
const FALL_IF = 'if ( !settled && vz < 0 && isdefined( s.fall_ref ) && z < s.fall_ref - TOD_RECALL_FALL_Z && !floor_below )';
mutant('fall ignores the floor below (rev 1: jumping down the tower was returned)', 'recall', FALL_IF,
  'if ( !settled && vz < 0 && isdefined( s.fall_ref ) && z < s.fall_ref - TOD_RECALL_FALL_Z )');
mutant('fall ignores the safe reference', 'recall', FALL_IF, 'if ( !settled && vz < 0 && !floor_below )');
mutant('void line ignored', 'recall', 'if ( z < TOD_RECALL_VOID_Z )\n\t\treturn "void";', 'if ( false )\n\t\treturn "void";');
mutant('off-map clock runs in the air', 'recall', 'if ( !settled )\n\t\t\treturn "";   // in the air', 'if ( false )\n\t\t\treturn "";   // in the air');
mutant('arrival at full health', 'recall', 'return TOD_RECALL_ARRIVAL_HP;', 'return health;');

if (fails) { console.log(`PURSUIT GATE FAILED: ${fails} of ${checks} checks`); process.exit(1); }
console.log(`PURSUIT OK: ${checks} checks — the walk model on all 24 real drops + doors + regions, the spawn filter, reachable targeting, THE HUNT's lanes/destinations, THE RECALL's verdict (rev 2: only a fall off the map, at 1 HP), lockstep with the generator, wiring, ${mutants} negative controls caught.`);
