// test_rampage_levers.js — v18.74: the four RAMPAGE levers that ride the shared
// knobs (elite roof, zombies-at-once, elite HP, horde HP) evaluated from the
// ACTUAL GSC bodies for every party size, breaker off and on, and that the
// off-state is the identity everywhere. (The armored sprinter's x1.5-once
// section retired with the sprinter, 2026-10-05: it now pins that it stays gone.)
//   node tools/test_rampage_levers.js
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const root = require('path').join(__dirname, '..');
const read = f => fs.readFileSync(require('path').join(root, 'scripts/zm/zm_tod2_cybercity', f), 'utf8');
const bosses = read('_tod_bosses.gsc'), corpse = read('_tod_corpse_cleanup.gsc'),
      speed = read('_tod_zombie_speed.gsc');

function defines(src) {
  const out = {};
  for (const m of src.matchAll(/^#define\s+(\w+)\s+([-\d.]+)/gm)) out[m[1]] = Number(m[2]);
  return out;
}
function body(src, name) {
  const at = src.indexOf('function ' + name + '(');
  assert.ok(at >= 0, 'function ' + name + ' not found');
  const start = src.indexOf('{', at);
  let end = start + 1, depth = 1;
  while (depth) { if (src[end] === '{') depth++; if (src[end] === '}') depth--; end++; }
  return src.slice(start + 1, end - 1);
}
// GSC -> JS: strip line comments, expand defines, `x.size` -> `x.length`,
// `else if` chains are already valid JS. Locals are plain assignments, so run
// each body as a function whose locals are declared up front.
function toJs(src, name, D) {
  let b = body(src, name).replace(/\/\/.*$/gm, '');
  for (const [k, v] of Object.entries(D)) b = b.replace(new RegExp('\\b' + k + '\\b', 'g'), String(v));
  b = b.replace(/\.size\b/g, '.length');
  const locals = [...new Set([...b.matchAll(/^\s*(\w+)\s*=/gm)].map(m => m[1]))];
  return 'function ' + name + '() {' + (locals.length ? ' let ' + locals.join(',') + ';' : '') + b + '}';
}

const D = Object.assign({}, defines(bosses), defines(corpse), defines(speed));
for (const k of ['TOD_RAMPAGE_ELITE_ROOF_ADD', 'TOD_RAMPAGE_AI_LIMIT_ADD', 'TOD_RAMPAGE_HP_MULT', 'TOD_RAMPAGE_ZHEALTH_MULT'])
  assert.ok(Number.isFinite(D[k]), k + ' define missing');

const ctx = { level: {}, players: [], IS_TRUE: x => x === true, isdefined: x => x !== undefined };
ctx.GetPlayers = () => ctx.players;
vm.createContext(ctx);
vm.runInContext(toJs(bosses, 'elite_roof_all', D), ctx);
vm.runInContext(toJs(bosses, 'rampage_hp_mult', D), ctx);
vm.runInContext(toJs(corpse, 'ai_limit_for_party', D), ctx);
vm.runInContext(toJs(speed, 'health_mult', D), ctx);
vm.runInContext(toJs(speed, 'rampage_horde_mult', D), ctx);

const roofOff = [5, 7, 9, 11], roofOn = [8, 10, 12, 14];
const aiOff = [36, 42, 48, 54], aiOn = [46, 52, 58, 58];   // 2026-09-28: +20% over TOD1, rampage under TOD_AI_LIMIT_CEIL 58
const hordeOff = [1.00, 1.20, 1.35, 1.50];
for (const on of [false, true]) {
  ctx.level.tod_rampage_on = on;
  for (let np = 0; np <= 4; np++) {
    ctx.players = Array(np).fill({});
    const i = Math.max(np, 1) - 1;
    assert.equal(ctx.elite_roof_all(), (on ? roofOn : roofOff)[i], `roof np=${np} on=${on}`);
    assert.equal(ctx.ai_limit_for_party(), (on ? aiOn : aiOff)[i], `ai_limit np=${np} on=${on}`);
    assert.equal(ctx.rampage_hp_mult(), on ? 1.5 : 1.0, `elite hp on=${on}`);
    assert.equal(ctx.rampage_horde_mult(), on ? 1.2 : 1.0, `horde factor on=${on}`);
    assert.ok(Math.abs(ctx.health_mult() - hordeOff[i] * (on ? 1.2 : 1.0)) < 1e-9, `horde hp np=${np} on=${on}`);
  }
}
// The absent field is FALSE (every consumer treats undefined as off).
ctx.level = {}; ctx.players = [{}];
assert.equal(ctx.elite_roof_all(), 5); assert.equal(ctx.ai_limit_for_party(), 36);
assert.equal(ctx.rampage_hp_mult(), 1.0); assert.equal(ctx.health_mult(), 1.0);

// W2E (2026-10-05): THE ARMORED SPRINTER retired whole (its director was parked under ONLY ZOMBIES), and with it the
// Map One boss_hp curve that multiplied rampage_hp_mult for the Panzer / Protector / Fury / hellhound. rampage_hp_mult
// stays the ONE owner of TOD_RAMPAGE_HP_MULT (asserted above); these pin the retirement.
assert.ok(!fs.existsSync(require('path').join(root, 'scripts/zm/zm_tod2_cybercity/_tod_sprinter.gsc')), 'the sprinter module stays retired');
assert.ok(!/function boss_hp\(/.test(bosses), 'the Map One boss HP curve stays retired');
assert.equal((bosses.match(/TOD_RAMPAGE_HP_MULT/g) || []).length >= 2 && (body(bosses, 'rampage_hp_mult').match(/TOD_RAMPAGE_HP_MULT/g) || []).length, 1,
  'rampage_hp_mult is the one reader of TOD_RAMPAGE_HP_MULT');
// And the ONLY writer of the flag is still the rampage module.
for (const [n, s] of [['bosses', bosses], ['corpse', corpse], ['speed', speed]])
  assert.ok(!/level\.tod_rampage_on\s*=/.test(s), n + ' must not write level.tod_rampage_on');

console.log(`rampage levers: roof ${roofOff}->${roofOn}, zombies ${aiOff}->${aiOn}, elite HP x1.5 (one owner), horde HP x1.2; the sprinter stays retired; off-state identity at every party size. PASS`);

// ---- v19.0: THE ROUND SEAL IS GONE AND MUST NOT COME BACK SILENTLY --------
// User: "I want to remove the round 9 rampage lock. It will be toggleable
// throughout the game." The whole seal was retired WHOLE — the constant, the
// predicate, the watcher, the banner thread, the eventstring, the Lua widget
// and the zoned plate. A future session re-adding any one of them would make
// the switch stop working at a round again, silently, so pin all of it here.
const rampage = read('_tod_rampage.gsc');
const rampageCode = rampage.split('\n').filter(l => !l.trim().startsWith('//')).join('\n');

for (const dead of ['TOD_RAMPAGE_LOCK_ROUND', 'locked()', 'lock_watcher', 'seal_banner', 'tod_rampage_sealed'])
  assert.ok(!rampageCode.includes(dead), `the round seal is retired: ${dead} must not return`);

// the flag is still flipped by a real toggle, not set one-way
assert.ok(/level\.tod_rampage_on\s*=\s*!IS_TRUE\(\s*level\.tod_rampage_on\s*\)/.test(rampageCode),
  'every use must FLIP the state (map 1 failure mode F2 was a one-way "if(active) continue")');

// exactly one writer of the flag, still
assert.equal((rampageCode.match(/level\.tod_rampage_on\s*=/g) || []).length, 2,
  'exactly two writes: the init to false and the one toggle');

// the only refusal left is the world pause; there must be no round comparison
assert.ok(!/level\.round_number\s*>=/.test(rampageCode),
  'no round comparison may gate the inducer any more');

// the two sealed hint strings are gone, so the map got two permanent slots back
assert.ok(!/sealed/.test(rampage.match(/function hint_for_state\(\)[\s\S]*$/)[0]),
  'hint_for_state must be down to its two live strings');

// the retirement is WHOLE: no zone line and no Lua widget left behind
const zone = fs.readFileSync(require('path').join(root, 'zone_source/zm_tod2_cybercity.zone'), 'utf8');
assert.ok(!zone.includes('i_tod_banner_rampage_sealed'), 'the seal plate must not stay zoned (load RAM)');
const hudLua = fs.readFileSync(require('path').join(root, 'ui/uieditor/menus/hud/tod_upgrade.lua'), 'utf8');
assert.ok(!hudLua.includes('TodRampageSealed') && !hudLua.includes('i_tod_banner_rampage_sealed'),
  'the Lua seal widget must go with it, or the lint sees an image nothing zones');

console.log('rampage seal: retired whole — no round constant, predicate, watcher, banner, eventstring, zone line or Lua widget. PASS');
