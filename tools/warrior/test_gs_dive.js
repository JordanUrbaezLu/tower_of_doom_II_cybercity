// THE AIR SLAM (2026-09-27, user: "the cyber smash [should] pull you down with force and
// land on impact whether you are super high or not"). Runs the SHIPPING gs_dive_* functions
// from _tod_class_kit.gsc against a falling-body mock: the engine integrates velocity and
// gravity between 50 ms ticks, a floor stops the body and sets IsOnGround, and an obstacle
// that is not ground (a zombie's head) stops it WITHOUT setting IsOnGround.
// Negative control: the same dive with the downward pull removed must miss its landing time.
const fs = require('fs'), assert = require('assert/strict'), path = require('path');
const KIT = process.argv[2] || path.join(__dirname, '../../scripts/zm/zm_tod2_cybercity/_tod_class_kit.gsc');
const kit = fs.readFileSync(KIT, 'utf8').replace(/\r\n/g, '\n');
const defs = Object.fromEntries([...kit.matchAll(/^#define\s+(TOD_GS_\w+)\s+([\d.]+)/gm)].map(m => [m[1], +m[2]]));
const vec = (...a) => a, add = (a, b) => a.map((x, i) => x + b[i]), sub = (a, b) => a.map((x, i) => x - b[i]);

function extract(name) {
  const m = kit.match(new RegExp('function ' + name + '\\(([^)]*)\\)\\s*\\{([\\s\\S]*?)\\n\\}'));
  assert(m, 'missing function ' + name);
  return { params: m[1].split(',').map(s => s.trim()).filter(Boolean), body: m[2] };
}
function transpile(src) {
  return src.replace(/\/\/[^\n]*/g, '')
    .replace(/\bself ([A-Za-z_]\w*)\(/g, 'self.$1(')
    .replace(/\( 0, 0, ([^()]*) \)/g, 'vec(0,0,$1)')
    .replace(/self\.origin \+ (vec\([^)]*\))/g, 'add(self.origin,$1)')
    .replace(/self\.origin - (vec\([^)]*\))/g, 'sub(self.origin,$1)')
    .replace(/\bMin\(/g, 'Math.min(');
}
function build(mutate = s => s) {
  const fns = {};
  for (const n of ['gs_dive_fall_ms', 'gs_dive_hang_ms', 'gs_dive_start', 'gs_dive_update', 'gs_dive_end', 'gs_fall_guard']) {
    const f = extract(n); let code = mutate(transpile(f.body));
    const vars = [...new Set([...code.replace(/"[^"\n]*"/g, '').matchAll(/(?<![.\w])([a-z_]\w*)\s*=(?!=)/g)].map(m => m[1]))]
      .filter(v => !f.params.includes(v) && v !== 'self');
    fns[n] = { params: f.params, code, vars };
  }
  return env => {
    const out = {};
    for (const [n, f] of Object.entries(fns)) {
      out[n] = new Function('e', `with(e){ return function(self${f.params.map(p => ',' + p).join('')}){ ${f.vars.length ? 'let ' + f.vars.join(',') + ';' : ''} ${f.code} } }`)(env);
    }
    // plain (self-less) calls between them, as GSC resolves them in the file's namespace
    env.gs_dive_fall_ms = h => out.gs_dive_fall_ms(undefined, h);
    env.gs_dive_hang_ms = ms => out.gs_dive_hang_ms(undefined, ms);
    return out;
  };
}

const G = 800;
function run(opt, mutate) {
  let now = 10000; const logs = [];
  const p = { origin: [0, 0, opt.z], velocity: opt.vel || [600, 0, 200], ground: false };
  const env = { ...defs, vec, add, sub, GetTime: () => now, isdefined: x => x !== undefined, IS_TRUE: x => !!x,
    SpawnStruct: () => ({}), dev_log: s => logs.push(s),
    BulletTrace: (a, b) => opt.floor === undefined ? { fraction: 1, position: b, surfacetype: 'none' }
      : { fraction: (a[2] - opt.floor) / (a[2] - b[2]), position: [a[0], a[1], opt.floor], surfacetype: 'metal' } };
  const f = build(mutate)(env);
  Object.assign(p, { IsOnGround() { return this.ground }, GetPlayerGravity: () => G, SetVelocity(v) { this.velocity = v },
    GetEntityNumber: () => 1, gs_dive_end: (d, r) => f.gs_dive_end(p, d, r) });
  const d = f.gs_dive_start(p, 7);
  if (!d) return { d, logs };
  const x0 = p.origin[0]; let ticks = 0;
  while (!d.done && ticks++ < 400) {
    f.gs_dive_update(p, d);
    if (d.done) break;
    // the engine: 50 ms of velocity + gravity, then collision
    const dt = 0.05, v = p.velocity;
    let z = p.origin[2] + v[2] * dt - 0.5 * G * dt * dt;
    p.origin = [p.origin[0] + v[0] * dt, p.origin[1] + v[1] * dt, z];
    p.velocity = [v[0], v[1], v[2] - G * dt];
    const stop = opt.head !== undefined && z <= opt.head ? opt.head : (z <= opt.floor ? opt.floor : undefined);
    if (stop !== undefined) { p.origin[2] = stop; p.velocity = [0, 0, 0]; p.ground = stop === opt.floor; }
    now += 50;
  }
  return { d, logs, p, x0, total: now - 10000, guard: f.gs_fall_guard, f };
}

let cases = 0;
function landed_case(z, label, mutate) {
  const r = run({ z, floor: 0 }, mutate);
  assert(r.d, label + ': a dive starts off the ground');
  assert.equal(r.d.reason, 'landed', label + ': lands on the floor');
  assert.equal(r.p.origin[2], 0, label + ': on the floor');
  assert(Math.abs(r.p.origin[0] - r.x0) < 1e-9, label + ': straight down (the carry is stopped)');
  assert(r.d.hang_ms >= defs.TOD_GS_DIVE_HANG_MIN_MS && r.d.hang_ms <= defs.TOD_GS_DIVE_HANG_MAX_MS, label + ': hang bounded');
  assert(r.total <= r.d.hang_ms + r.d.fall_ms + 150, `${label}: lands on time (${r.total} ms vs est ${r.d.hang_ms + r.d.fall_ms})`);
  assert(r.logs.some(s => s.startsWith('GS_DIVE_START') && s.includes('height=' + z)), label + ': logs the traced floor distance');
  assert(r.logs.some(s => s.startsWith('GS_DIVE_END') && s.includes('reason=landed')));
  cases++;
  return r;
}
landed_case(150, 'short drop');
const mid = landed_case(600, 'mid drop');
const high = landed_case(2000, 'high drop');
const crown = landed_case(19000, 'crown to base');
// a short drop is held long enough that it lands near the sword's swing frame
const short = run({ z: 400, floor: 0 });
assert(Math.abs(short.total - defs.TOD_GS_SWORD_IMPACT_MS) <= 150 || short.d.hang_ms === defs.TOD_GS_DIVE_HANG_MAX_MS, 'short drop lines up with the swing');
cases++;
assert(high.total < crown.total && mid.total <= high.total, 'higher = longer, never mid-air');
// too low / no floor: no dive (the old path)
assert.equal(run({ z: 30, floor: 0 }).d, undefined, 'a 30 u hop lands on its own'); cases++;
assert.equal(run({ z: 500 }).d, undefined, 'no floor below: no dive'); cases++;
// held up by a zombie's head: slam there instead of hanging forever
const head = run({ z: 1000, floor: 0, head: 300 });
assert.equal(head.d.reason, 'blocked', 'a non-ground stop ends the dive'); assert.equal(head.p.origin[2], 300); cases++;
// fall damage: blocked while diving and just after, passed otherwise
const g = head.guard, pl = { GetEntityNumber: () => 1 };
const now0 = 10000 + head.total;
assert.equal(g(Object.assign({}, pl, { tod_gs_diving: true }), 0, 0, 50, 0, 'MOD_FALLING'), 0);
assert.equal(g(Object.assign({}, pl, { tod_gs_dive_land_ms: now0 }), 0, 0, 50, 0, 'MOD_FALLING'), 0);
assert.equal(g(Object.assign({}, pl, { tod_gs_diving: true }), 0, 0, 50, 0, 'MOD_MELEE'), -1);
assert.equal(g(Object.assign({}, pl, {}), 0, 0, 50, 0, 'MOD_FALLING'), -1);
cases++;
// NEGATIVE CONTROL: without the downward pull the body only falls under gravity
assert.throws(() => landed_case(2000, 'no pull', s => s.replace('self.SetVelocity( vec(0,0,down) );', '')), /lands on time/);
cases++;
// structure: the sword slam waits for the dive, and a Bash can hand over to it
assert(/dive = owner gs_dive_start\( token \)/.test(kit) && /owner gravsmash_hit\( "dive" \)/.test(kit), 'sword slam uses the dive');
assert(/if \( isdefined\( owner\.tod_gs_queued \) \)[\s\S]{0,40}cut = true/.test(kit), 'Bash cuts on a queued smash');
assert(/ArrayInsert\( level\.player_damage_callbacks, &gs_fall_guard, 0 \)/.test(kit), 'fall guard registered');
cases++;
console.log(`GS DIVE PASS: ${cases} cases (crown drop ${crown.total} ms, 2000 u ${high.total} ms, 600 u ${mid.total} ms), negative control caught.`);
