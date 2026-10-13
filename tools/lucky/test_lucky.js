'use strict';
// THE LUCKY SOURCES' GATE (docs/197): the Lucky Clover drop, the Lucky Meteor, the Golden Zombie.
//
// Runs the SHIPPING GSC's pure functions through tools/sky_ships/gsc_eval.js (never a hand copy that
// could drift), checks the user's numbers and every wiring lockstep (power-up name server <-> client,
// zone lines, precaches, effect files, sound aliases, models), then breaks each contract on purpose
// (NEGATIVE CONTROLS) and requires this gate to catch it.
//
//   node tools/lucky/test_lucky.js              the gate (build_map.ps1 runs it before the linker)
//   node tools/lucky/test_lucky.js --ledger F   post-link: every lucky asset is in the linker ledger F
const fs = require('fs');
const path = require('path');
const { gscLoad, V } = require('../sky_ships/gsc_eval.js');

const ROOT = path.resolve(__dirname, '..', '..');
const rd = p => fs.readFileSync(path.join(ROOT, p), 'utf8');
const SCRIPTS = 'scripts/zm/zm_tod2_cybercity/';
const LUCKY_GSC = SCRIPTS + '_tod_lucky.gsc';
const LUCKY_CSC = SCRIPTS + '_tod_lucky.csc';
const GOLD_GSC = SCRIPTS + '_tod_golden_zombie.gsc';
const LUCK_GSC = SCRIPTS + '_tod_luck.gsc';
const ZONE = 'zone_source/zm_tod2_cybercity.zone';
const ENTRY_GSC = 'scripts/zm/zm_tod2_cybercity.gsc';
const ENTRY_CSC = 'scripts/zm/zm_tod2_cybercity.csc';

let fails = 0, checks = 0, QUIET = false;
function ok(cond, msg) { checks++; if (!cond) { fails++; if (!QUIET) console.log('  FAIL  ' + msg); } }

function defines(text) {
  const d = {};
  const re = /^#define\s+(\w+)\s+([^\n]+?)\s*(?:\/\/[^\n]*)?$/gm;
  let m;
  while ((m = re.exec(text))) d[m[1]] = m[2].trim();
  return d;
}
const num = s => parseFloat(String(s).replace(/[()]/g, ''));
const str = s => String(s).replace(/^"|"$/g, '');

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const sub = (a, b) => V(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const len = a => Math.hypot(a[0], a[1], a[2]);
const builtins = { VectorDot: dot, RandomFloat: n => Math.random() * n };

// ---------------------------------------------------------------------------------------------
// THE CHECKS, as a function of the source texts, so a negative control can feed a broken text.
// ---------------------------------------------------------------------------------------------
function run(src, quiet) {
  const saved = [fails, checks, QUIET];
  fails = 0; checks = 0; QUIET = !!quiet;
  const log = quiet ? () => {} : (...a) => console.log(...a);

  const D = defines(src.lucky);
  let g;
  try { g = gscLoad([['tod_lucky', src.lucky]], D, { builtins }); } catch (e) { ok(false, 'the lucky GSC does not load in gsc_eval: ' + e.message); }

  // --- the user's numbers ---------------------------------------------------------------------
  ok(num(D.TOD_CLOVER_BARS) === 3, 'the clover pays 3 bars (user: "maybe like three luck bars" -> "Yes"), got ' + D.TOD_CLOVER_BARS);
  ok(str(D.TOD_CLOVER_NAME) === 'tod_luck_clover', 'the power-up name is tod_luck_clover');
  ok(/[^!\w]POWERUP_ONLY_AFFECTS_GRABBER\s*,\s*!POWERUP_ANY_TEAM\s*,\s*!POWERUP_ZOMBIE_GRABBABLE/.test(src.lucky),
    'the clover is registered like the perk bottle / PaP / Zombie Blood (grabber only = the white glow the user named)');
  ok(/powerup_set_statless_powerup\(\s*TOD_CLOVER_NAME\s*\)/.test(src.lucky), 'the clover is statless (a custom name has no pers stat: the grab thread would throw)');
  ok(/tod_luck::add_bars\(\s*player\s*,\s*TOD_CLOVER_BARS\s*\)/.test(src.lucky), 'the grab pays through tod_luck::add_bars (segment by segment, the LUCK card applies)');
  const add = src.lucky.indexOf('add_zombie_powerup( TOD_CLOVER_NAME');
  const set1 = src.lucky.indexOf('powerup_set_can_pick_up_in_last_stand( TOD_CLOVER_NAME');
  ok(add >= 0 && set1 > add, 'the power-up setters come AFTER add_zombie_powerup (the struct only exists after it)');

  // --- the client half ------------------------------------------------------------------------
  const cn = str(D.TOD_CLOVER_NAME || '');
  ok(new RegExp('include_zombie_powerup\\(\\s*"' + cn + '"\\s*\\)').test(src.luckyCsc) && new RegExp('add_zombie_powerup\\(\\s*"' + cn + '"\\s*\\)').test(src.luckyCsc),
    'the client includes AND adds the same power-up name (LOCKSTEP _tod_lucky.csc)');

  // --- the meteor's pure math -----------------------------------------------------------------
  if (g) {
    const sweep = num(D.TOD_METEOR_SWEEP), drop = num(D.TOD_METEOR_DROP);
    let worst = 0;
    for (let i = 0; i < 400; i++) {
      const focus = V((Math.random() - 0.5) * 3000, (Math.random() - 0.5) * 3000, Math.random() * 19000);
      const bearing = Math.random() * 360;
      const dist = num(D.TOD_METEOR_DIST_MIN) + Math.random() * (num(D.TOD_METEOR_DIST_MAX) - num(D.TOD_METEOR_DIST_MIN));
      const alt = num(D.TOD_METEOR_ALT_MIN) + Math.random() * (num(D.TOD_METEOR_ALT_MAX) - num(D.TOD_METEOR_ALT_MIN));
      const m = g.call('meteor_plan', [focus, bearing, dist, alt, sweep, drop]);
      const h0 = Math.hypot(m.start[0] - focus[0], m.start[1] - focus[1]);
      const h1 = Math.hypot(m.end[0] - focus[0], m.end[1] - focus[1]);
      worst = Math.max(worst, Math.abs(h0 - dist), Math.abs(h1 - dist));
      const mid = g.call('meteor_point', [m, 0.5]);
      worst = Math.max(worst, Math.abs(mid[2] - (focus[2] + alt)), Math.abs((m.start[2] - m.end[2]) - drop));
      const p0 = g.call('meteor_point', [m, -1]), p1 = g.call('meteor_point', [m, 2]);
      worst = Math.max(worst, len(sub(p0, m.start)), len(sub(p1, m.end)));
    }
    ok(worst < 0.01, 'meteor_plan / meteor_point: both ends at the pass distance, the middle at the altitude, the drop across it, t clamped (worst error ' + worst.toFixed(4) + ')');

    // the box: a focus near the wall must be refused, one at the tower accepted
    const safe = g.call('meteor_plan', [V(0, 0, 8000), 0, num(D.TOD_METEOR_DIST_MAX), 900, sweep, drop]);
    const edge = g.call('meteor_plan', [V(num(D.TOD_METEOR_BOX) - 500, 0, 8000), 0, num(D.TOD_METEOR_DIST_MAX), 900, sweep, drop]);
    // the same pass turned 90 degrees along the Y wall: its X never leaves the box, so only the Y test can refuse it
    const edgeY = g.call('meteor_plan', [V(0, num(D.TOD_METEOR_BOX) - 500, 8000), 90, num(D.TOD_METEOR_DIST_MAX), 900, 20, drop]);
    ok(g.call('meteor_in_box', [safe]) === true && g.call('meteor_in_box', [edge]) === false && g.call('meteor_in_box', [edgeY]) === false,
      'meteor_in_box: a pass from the tower fits the sealed sky box, one against either wall (X or Y) does not');

    // the view ray: dead centre, just inside, just outside, behind, beside the eye
    const eye = V(0, 0, 60), R = num(D.TOD_METEOR_HIT_R);
    const c = V(5000, 0, 60);
    const aim = v => { const l = len(v); return V(v[0] / l, v[1] / l, v[2] / l); };
    ok(g.call('meteor_ray_hit', [eye, V(1, 0, 0), c, R]) === true, 'the ray hits a rock dead ahead');
    const inside = aim(V(5000, R * 0.95, 0)), outside = aim(V(5000, R * 1.1, 0));
    ok(g.call('meteor_ray_hit', [eye, inside, c, R]) === true, 'the ray hits a rock just inside the hit radius');
    ok(g.call('meteor_ray_hit', [eye, outside, c, R]) === false, 'the ray misses a rock just outside the hit radius');
    ok(g.call('meteor_ray_hit', [eye, V(-1, 0, 0), c, R]) === false, 'the ray never hits a rock behind the shooter');
    ok(g.call('meteor_ray_hit', [eye, V(1, 0, 0), V(30, 0, 60), R]) === false, 'the ray never hits something at the shooter\'s own eye');

    // the rock must be FAIR to hit: the hit radius covers the rock itself, and at the pass's
    // closest and farthest points the target is between 1 and 6 degrees across
    const rad = num(D.TOD_METEOR_RADIUS);
    ok(R >= rad, 'the hit radius (' + R + ') is at least the rock\'s own size (' + rad + '): a shot on the rock always counts');
    const near = num(D.TOD_METEOR_DIST_MIN) * Math.cos(sweep / 2 * Math.PI / 180), far = num(D.TOD_METEOR_DIST_MAX);
    const degNear = 2 * Math.atan(R / near) * 180 / Math.PI, degFar = 2 * Math.atan(R / far) * 180 / Math.PI;
    ok(degFar >= 1.0 && degNear <= 8.0, 'the target is 1-8 degrees across over the whole pass (far ' + degFar.toFixed(2) + ', near ' + degNear.toFixed(2) + ')');
    log('  meteor: target ' + degFar.toFixed(2) + '-' + degNear.toFixed(2) + ' degrees across; pass ' + D.TOD_METEOR_FLIGHT_SECS + ' s');
  }

  // --- the meteor's behaviour contracts (structural) ------------------------------------------
  ok(/if\s*\(\s*!IS_TRUE\(\s*level\.tod_upgrade_pause\s*\)\s*\)\s*\{\s*m\.t\s*\+=/.test(src.lucky), 'the flight only advances while no card deal pauses the world');
  ok(/self\.tod_class\s*==\s*"slasher"/.test(src.lucky), 'the Warrior (slasher) cannot break a meteor with a punch');
  ok(/level\.tod_arena_active/.test(src.lucky), 'no meteor while the party is in the Battle Arena');
  ok(/specific_powerup_drop\(\s*TOD_CLOVER_NAME\s*,\s*land\s*\)/.test(src.lucky), 'a broken meteor lands a Lucky Clover');
  ok(/BulletTracePassed\(\s*eye\s*,\s*near\s*,/.test(src.lucky), 'a shot through a wall does not count (line of sight to the rock)');
  ok(/tod_luck_dev_never/.test(src.lucky) === false, 'sanity');

  // --- the luck helper -------------------------------------------------------------------------
  ok(/function add_bars\(\s*player\s*,\s*n\s*\)/.test(src.luck) && /add\(\s*player\s*,\s*TOD_LUCK_MAX\s*\/\s*TOD_LUCK_SEGS\s*\)/.test(src.luck),
    'tod_luck::add_bars pays one segment per step through add() (the LUCK card and the pips apply)');
  ok(/#define TOD_LUCK_KILL_BUDGET\s+12\b/.test(src.luck), 'the kill budget is 12 a round (user: "Make it 12%")');

  // --- the golden zombie ------------------------------------------------------------------------
  if (src.gold) {
    const G = defines(src.gold);
    ok(num(G.TOD_GOLDEN_PER_ROUND) === 1, 'exactly one golden zombie per round (user: "Golden zombie make one per round"), got ' + G.TOD_GOLDEN_PER_ROUND);
    ok(/function golden_round_tick\(\)[\s\S]*?level\.tod_golden_count = 0;[\s\S]*?level\.tod_golden_made = 0;/.test(src.gold),
      'every new round resets the count and the golden made (golden_round_tick)');
    try {
      const gg = gscLoad([['tod_golden_zombie', src.gold]], G, { builtins });
      let bad = 0;
      for (const total of [1, 2, 6, 24, 60, 105, 510])
        for (const draw of [0, 0.25, 0.5, 0.75, 0.999999]) {
          const t = gg.call('golden_target', [total, num(G.TOD_GOLDEN_SPAN), draw]);
          const top = Math.max(1, Math.floor(total * num(G.TOD_GOLDEN_SPAN)));
          if (!(t >= 1 && t <= top && Number.isInteger(t))) bad++;
        }
      ok(bad === 0, 'golden_target: the round\'s golden is always one of its first ' + G.TOD_GOLDEN_SPAN + ' of spawns, tiny rounds included (' + bad + ' bad)');
    } catch (e) { ok(false, 'golden_target does not run in gsc_eval: ' + e.message); }
    ok(num(G.TOD_GOLDEN_BARS) === 3, 'the killer gets 3 bars (user: "give 3 bars to the killer"), got ' + G.TOD_GOLDEN_BARS);
    ok(/tod_luck::add_bars\(\s*killer\s*,\s*TOD_GOLDEN_BARS\s*\)/.test(src.gold), 'the golden kill pays the KILLER through tod_luck::add_bars');
    ok(/tod_partner_owner/.test(src.gold), 'a companion\'s golden kill pays its owner');
    // NEVER LOST: a golden the players did not get to kill is re-issued to the next ordinary spawn
    const death = (src.gold.match(/function golden_death_watch\(\)[\s\S]*?\n}/) || [''])[0];
    ok(/!isdefined\( self \)[\s\S]*?golden_owe\(/.test(death), 'a golden removed without dying is owed (golden_owe on the removed path)');
    ok(/!isdefined\( killer \)[\s\S]*?golden_owe\(/.test(death), 'a golden killed by no player (a nuke, a trap) is owed (golden_owe on the no-killer path)');
    ok(/function golden_owe\([\s\S]*?level\.tod_golden_owed\+\+/.test(src.gold) && num(G.TOD_GOLDEN_OWED_MAX) >= 1,
      'golden_owe adds an owed golden (capped at TOD_GOLDEN_OWED_MAX)');
    const roll = (src.gold.match(/function golden_roll\(\)[\s\S]*?\n}/) || [''])[0];
    const swap = roll.indexOf('wait TOD_GOLDEN_SWAP_WAIT');
    ok(swap > 0 && roll.slice(0, swap).indexOf('endon( "death" )') < 0,
      'no endon( "death" ) before the swap wait: a spawn killed inside it gives its claim back instead of taking it along');
    ok(/level\.tod_golden_owed > 0/.test(roll) && /level\.tod_golden_owed--/.test(roll), 'an owed golden goes to the next ordinary spawn first');
  } else ok(false, 'the golden zombie module exists (' + GOLD_GSC + ')');

  // --- wiring: zone, entry scripts, precaches, files -------------------------------------------
  for (const f of [LUCKY_GSC, LUCKY_CSC, GOLD_GSC])
    ok(new RegExp('^scriptparsetree,' + f.replace(/\./g, '\\.') + '\\s*$', 'm').test(src.zone), 'zone scriptparsetree line for ' + f);
  ok(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_lucky;/.test(src.entryGsc) && /tod_lucky::init\(\)/.test(src.entryGsc), 'the entry .gsc #usings and inits _tod_lucky');
  ok(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_golden_zombie;/.test(src.entryGsc) && /tod_golden_zombie::init\(\)/.test(src.entryGsc), 'the entry .gsc #usings and inits _tod_golden_zombie');
  ok(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_lucky;/.test(src.entryCsc), 'the entry .csc #usings _tod_lucky (the client half of the power-up)');

  const models = [str(D.TOD_CLOVER_MODEL), str(D.TOD_METEOR_MODEL)];
  if (src.gold) { const G = defines(src.gold); for (const k of Object.keys(G)) if (/^TOD_GOLDEN_MODEL_/.test(k)) models.push(str(G[k])); }
  for (const mdl of models) {
    ok(new RegExp('^xmodel,' + mdl + '\\s*$', 'm').test(src.zone), 'zone xmodel line for ' + mdl);
    ok(new RegExp('#precache\\(\\s*"model"\\s*,\\s*"' + mdl + '"\\s*\\)').test(src.lucky + (src.gold || '')), 'model precache for ' + mdl);
  }
  const fx = [];
  for (const [k, v] of Object.entries(D)) if (/_FX_/.test(k)) fx.push(str(v));
  if (src.gold) for (const [k, v] of Object.entries(defines(src.gold))) if (/_FX_/.test(k)) fx.push(str(v));
  for (const f of fx) {
    ok(f.length <= 63, 'effect path under the 63-character runtime limit: ' + f);
    ok(new RegExp('^fx,' + f + '\\s*$', 'm').test(src.zone), 'zone fx line for ' + f);
    ok(new RegExp('#precache\\(\\s*"fx"\\s*,\\s*"' + f + '"\\s*\\)').test(src.lucky + (src.gold || '')), 'fx precache for ' + f);
    ok(src.fxExists(f), 'the effect file exists: share/raw/fx/' + f + '.efx');
  }
  // --- the precache table (LT-fix / LT-meteor, 2026-10-05) --------------------------------------
  // An empty-name #precache never reaches the linker's precache table (the bgcache asset in the .ff): the linker
  // flattens the file's directives, drops the empty name, and every later directive of that file is misread (the
  // table even held a bogus string "model", the next directive's type). The one that stood first in _tod_lucky.gsc
  // took all four of the file's effect precaches with it: every meteor threw "effect tod/luck/fx_luck_meteor_trail
  // was not precached" and flew with no trail (all 19 archived meteors, 7 sessions, 09-30..10-05). The zone line and
  // the asset ledger were both fine, so neither check above could see it; tools/verify_bgcache.py reads the linked
  // table itself after a build.
  const emptyPre = /^[ \t]*#precache\(\s*"\w+"\s*,\s*""\s*\)/m;
  ok(!emptyPre.test(src.lucky) && !emptyPre.test(src.gold || ''), 'no empty-name #precache in the lucky modules (the linker drops the precaches after it)');
  ok(src.emptyPrecache.length === 0, 'no empty-name #precache in scripts/ that can cost a later one (' + src.emptyPrecache.join(', ') + ')');
  if (!quiet && src.emptyTrailing && src.emptyTrailing.length) console.log('  note: trailing empty-name precaches via #define (last in their file, nothing to lose): ' + src.emptyTrailing.join(', '));
  const ns = src.lucky.search(/^#namespace\s/m);
  for (const f of fx.filter(f => /meteor|clover/.test(f))) {
    const at = src.lucky.search(new RegExp('^#precache\\(\\s*"fx"\\s*,\\s*"' + f + '"\\s*\\)', 'm'));
    ok(at >= 0 && ns > at, 'the fx precache for ' + f + ' is a directive of its own line in the preamble (before #namespace)');
  }

  const snd = [];
  for (const [k, v] of Object.entries(D)) if (/_SND_/.test(k)) snd.push(str(v));
  if (src.gold) for (const [k, v] of Object.entries(defines(src.gold))) if (/_SND_/.test(k)) snd.push(str(v));
  for (const a of snd) ok(src.aliases.has(a), 'sound alias defined in a sound/aliases CSV: ' + a);

  const r = [fails, checks];
  fails = saved[0] + (quiet ? 0 : r[0]); checks = saved[1] + (quiet ? 0 : r[1]); QUIET = saved[2];
  return r;
}

// THE EMPTY-NAME DETECTOR (LT-fix 2026-10-05). `#define NAME "value"` lines of a text (comments stripped).
function stringDefines(text) {
  const d = {};
  for (const m of text.replace(/\/\/[^\n]*/g, '').matchAll(/^[ \t]*#define\s+(\w+)\s+"([^"]*)"/gm)) d[m[1]] = m[2];
  return d;
}
// One file's #precache directives in order: a literal "" fails; an empty name through a #define (the file's own or
// an #insert'ed .gsh's, `gsh`) fails when another #precache follows it, else it is only listed as trailing.
function scanEmptyPrecache(text, rel, gsh) {
  const defs = { ...(gsh || {}), ...stringDefines(text) };
  const pre = [], fail = [], trailing = [];
  text.split(/\r?\n/).forEach((l, i) => { const m = /^[ \t]*#precache\(\s*"\w+"\s*,\s*(.+?)\s*\)\s*;/.exec(l); if (m) pre.push([i + 1, m[1]]); });
  pre.forEach(([ln, arg], k) => {
    if (/^""/.test(arg)) { fail.push(rel + ':' + ln); return; }
    const tok = /^(\w+)$/.exec(arg);
    if (!tok || defs[tok[1]] !== '') return;
    if (k < pre.length - 1) fail.push(rel + ':' + ln + ' (via #define ' + tok[1] + ', ' + (pre.length - 1 - k) + ' directive(s) after it)');
    else trailing.push(rel + ':' + ln);
  });
  return { fail, trailing };
}

function loadSources() {
  const aliases = new Set();
  const dir = path.join(ROOT, 'sound', 'aliases');
  if (fs.existsSync(dir)) for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.csv'))) {
    for (const line of fs.readFileSync(path.join(dir, f), 'utf8').split(/\r?\n/)) {
      const name = line.split(',')[0].trim();
      if (name && !name.startsWith('#') && name !== 'Name') aliases.add(name);
    }
  }
  const tryRead = p => { try { return rd(p); } catch (e) { return null; } };
  // every empty-name #precache in scripts/ (file:line) that can cost a precache (LT-fix / LT-meteor): the linker
  // flattens a file's directives, drops the empty name and misreads EVERY directive after it in that file. A literal
  // "" always fails; an empty name that comes through a #define (same file or an #insert'ed .gsh under scripts/)
  // fails when another #precache follows it, and is only listed (emptyTrailing) when it is the file's last directive
  // (the vendored Logical power-ups' hint strings: nothing after them to lose).
  const emptyPrecache = [], emptyTrailing = [];
  const walk = d => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) walk(p);
      else if (/\.(gsc|csc)$/.test(e.name)) {
        const text = fs.readFileSync(p, 'utf8');
        let gsh = {};
        for (const m of text.matchAll(/^[ \t]*#insert\s+([\w\\/]+\.gsh)\s*;/gm)) {
          const g = path.join(ROOT, m[1].replace(/\\/g, '/'));
          if (fs.existsSync(g)) gsh = { ...gsh, ...stringDefines(fs.readFileSync(g, 'utf8')) };
        }
        const r = scanEmptyPrecache(text, path.relative(ROOT, p).replace(/\\/g, '/'), gsh);
        emptyPrecache.push(...r.fail); emptyTrailing.push(...r.trailing);
      }
    }
  };
  walk(path.join(ROOT, 'scripts'));
  return {
    lucky: rd(LUCKY_GSC), luckyCsc: rd(LUCKY_CSC), gold: tryRead(GOLD_GSC), luck: rd(LUCK_GSC),
    zone: rd(ZONE), entryGsc: rd(ENTRY_GSC), entryCsc: rd(ENTRY_CSC), aliases, emptyPrecache, emptyTrailing,
    fxExists: f => fs.existsSync(path.join(ROOT, 'share', 'raw', 'fx', f + '.efx')),
  };
}

// ---------------------------------------------------------------------------------------------
if (process.argv[2] === '--ledger') {
  // POST-LINK: every lucky model and effect is in the linker's asset ledger.
  const ledger = fs.readFileSync(process.argv[3], 'utf8');
  const src = loadSources();
  const D = defines(src.lucky), G = src.gold ? defines(src.gold) : {};
  const want = [];
  for (const d of [D, G]) for (const [k, v] of Object.entries(d)) {
    if (/_MODEL(_|$)/.test(k)) want.push(['xmodel', str(v)]);
    if (/_FX_/.test(k)) want.push(['fx', str(v)]);
  }
  // the asset ledger's rows are "index,type,name,resident,streamed,parentStack"
  const have = new Set();
  for (const line of ledger.split(/\r?\n/)) {
    const c = line.split(',');
    if (c.length > 2) have.add(c[1].trim().toLowerCase() + ',' + c[2].trim().replace(/\\/g, '/').toLowerCase());
  }
  let miss = 0;
  for (const [t, n] of want) {
    if (!have.has(t + ',' + n.toLowerCase())) { miss++; console.log('  MISSING from the ledger: ' + t + ',' + n); }
  }
  console.log(miss ? 'LUCKY LEDGER FAIL: ' + miss + ' missing' : 'LUCKY LEDGER OK: ' + want.length + ' assets linked');
  process.exit(miss ? 1 : 0);
}

const src = loadSources();
console.log('LUCKY SOURCES GATE (docs/197)');
run(src, false);

// THE EMPTY-NAME DETECTOR ITSELF, on fixtures (LT-fix 2026-10-05): a literal "" fails anywhere; a #define-resolved
// empty name fails only with a directive after it (the 09-29 _tod_lucky shape); the vendored Logical power-ups'
// shape (the empty hint string LAST in its file, its define in an #insert'ed .gsh) is listed, never failed.
{
  const lit = scanEmptyPrecache('#precache( "string", "" );\n#precache( "fx", "tod/luck/fx_luck_meteor_trail" );\n', 'a.gsc', {});
  ok(lit.fail.length === 1 && /^a\.gsc:1$/.test(lit.fail[0]), 'detector: a literal empty name fails (the 09-29 _tod_lucky line)');
  const viaDef = scanEmptyPrecache('#define HINT ""\n#precache( "string", HINT );\n#precache( "model", "m" );\n', 'b.gsc', {});
  ok(viaDef.fail.length === 1 && /via #define HINT, 1 directive/.test(viaDef.fail[0]), 'detector: a #define-resolved empty name with a directive after it fails: ' + viaDef.fail[0]);
  const logical = scanEmptyPrecache('#precache( "material", "logical_powerup_timewarp" );\r\n#precache( "string", TIMEWARP_POWERUP_STRING );\r\n', 'c.gsc', { TIMEWARP_POWERUP_STRING: '' });
  ok(logical.fail.length === 0 && logical.trailing.length === 1, 'detector: an empty hint LAST in its file (the Logical power-ups, define in the .gsh) is listed, not failed');
  const fine = scanEmptyPrecache('#define N "tod/x"\n#precache( "fx", N );\n#precache( "fx", "tod/y" );\n', 'd.gsc', {});
  ok(fine.fail.length === 0 && fine.trailing.length === 0, 'detector: named precaches pass');
}

// NEGATIVE CONTROLS: each break must fail the gate.
const controls = [
  ['clover pays 2 bars', s => ({ ...s, lucky: s.lucky.replace(/#define TOD_CLOVER_BARS\s+3/, '#define TOD_CLOVER_BARS          2') })],
  ['clover is a TEAM drop (green glow)', s => ({ ...s, lucky: s.lucky.replace('POWERUP_ONLY_AFFECTS_GRABBER, !POWERUP_ANY_TEAM', '!POWERUP_ONLY_AFFECTS_GRABBER, !POWERUP_ANY_TEAM') })],
  ['clover not statless', s => ({ ...s, lucky: s.lucky.replace(/zm_powerups::powerup_set_statless_powerup\(\s*TOD_CLOVER_NAME\s*\);/, '') })],
  ['client adds a different name', s => ({ ...s, luckyCsc: s.luckyCsc.replace(/add_zombie_powerup\(\s*"tod_luck_clover"\s*\)/, 'add_zombie_powerup( "tod_luck_clovr" )') })],
  ['ray hits behind the shooter', s => ({ ...s, lucky: s.lucky.replace('if ( along < 64 )', 'if ( along < -1000000 )') })],
  ['ray ignores the hit radius', s => ({ ...s, lucky: s.lucky.replace('return ( perp <= r );', 'return ( perp <= r * 3 );') })],
  ['the plan forgets the drop', s => ({ ...s, lucky: s.lucky.replace('alt + drop * 0.5 );', 'alt );') })],
  ['the box check skips y', s => ({ ...s, lucky: s.lucky.replace('|| Abs( p[ 1 ] ) > TOD_METEOR_BOX ', '') })],
  ['the flight ignores the pause', s => ({ ...s, lucky: s.lucky.replace(/if \( !IS_TRUE\( level\.tod_upgrade_pause \) \)(\s*\{\s*m\.t \+=)/, 'if ( true )$1') })],
  ['the Warrior can punch a meteor', s => ({ ...s, lucky: s.lucky.replace('self.tod_class == "slasher"', 'self.tod_class == "nobody"') })],
  ['two golden zombies a round', s => ({ ...s, gold: (s.gold || '').replace(/#define TOD_GOLDEN_PER_ROUND\s+1\b/, '#define TOD_GOLDEN_PER_ROUND      2') })],
  ['the golden lands past the span', s => ({ ...s, gold: (s.gold || '').replace('top = int( total * span );', 'top = int( total * span * 3 );') })],
  ['a new round forgets to reset', s => ({ ...s, gold: (s.gold || '').replace('level.tod_golden_made = 0;', 'level.tod_golden_made = level.tod_golden_made;') })],
  ['a nuked golden is simply lost', s => ({ ...s, gold: (s.gold || '').replace('golden_owe( ent, "no_player_killer" );', 'log( "no luck" );') })],
  ['the claim dies with an instant kill', s => ({ ...s, gold: (s.gold || '').replace(/function golden_roll\(\)\r?\n\{\r?\n/, m => m + '\tself endon( "death" );\n') })],
  ['golden pays the wrong player', s => ({ ...s, gold: (s.gold || '').replace(/tod_luck::add_bars\(\s*killer\s*,/, 'tod_luck::add_bars( self,') })],
  ['kill budget back at 18', s => ({ ...s, luck: s.luck.replace(/#define TOD_LUCK_KILL_BUDGET\s+12\b/, '#define TOD_LUCK_KILL_BUDGET   18') })],
  ['a zone line lost', s => ({ ...s, zone: s.zone.replace(/^xmodel,tod_luck_clover\s*$/m, '') })],
  // LT-meteor: the 2026-09-29..10-05 source, whose leading empty-name precache cost the meteor its trail
  ['the empty-name precache is back', s => ({ ...s, lucky: s.lucky.replace(/^#precache\( "model", "tod_luck_clover" \);/m, '#precache( "string", "" );   // the power-up\'s blank hint\n$&') })],
  ['another module adds an empty-name precache', s => ({ ...s, emptyPrecache: ['scripts/zm/zm_tod2_cybercity/_tod_example.gsc:12'] })],
  ['the trail precache sits after #namespace', s => ({ ...s, lucky: s.lucky.replace(/^#precache\( "fx", "tod\/luck\/fx_luck_meteor_trail" \);\r?\n/m, '').replace(/^#namespace tod_lucky;/m, '$&\n#precache( "fx", "tod/luck/fx_luck_meteor_trail" );') })],
];
let caught = 0;
for (const [name, mutate] of controls) {
  const [f] = run(mutate(src), true);
  if (f > 0) caught++; else console.log('  FAIL  negative control NOT caught: ' + name);
}
checks += controls.length;
if (caught !== controls.length) fails += controls.length - caught;

console.log((fails ? 'LUCKY GATE FAIL: ' + fails + ' of ' : 'LUCKY GATE OK: ') + checks + ' checks (' + caught + '/' + controls.length + ' negative controls caught)');
process.exit(fails ? 1 : 0);
