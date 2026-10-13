// tools/breacher/test_fusion_air.js - THE BREACHER'S LAUNCH + AIR STEERING, run as shipped GSC.
//
// 2026-09-29, user: "the cluster grenade needs to add a bit of sideways velocity depending on how
// close to the center you are and the Breacher needs better air steering like the Slasher has on
// map 1. Also cluster should only send you flying if you jump to avoid players from accidentally
// clustering themselves and getting themselves killed".
//
// The three functions are pulled out of the GSC, turned into JavaScript by a handful of textual
// rewrites (no hand-written copy of the maths) and run against an engine-shaped mock:
//   fusion_push        _tod_class_cards: straight up over the burst, thrown out beside it, never
//                      more than TOD_FJUMP_PUSH_MAX, weaker toward the edge of the reach
//   fusion_jump_try    _tod_class_cards: airborne = launch now; grounded = launch only after a jump
//                      inside TOD_FJUMP_JUMP_GRACE_MS; blocked (jump pad, mantle, down) = never
//   breacher_air_steer _tod_class_kit (reworked 2026-10-01, user: "I want it to be like the athlete"):
//                      ONE lane per flight. ATHLETE mode (a take-off with momentum) = map 1's lane 4 at Lv5:
//                      strafe curves, budget TOD_BAIR_BUDGET deg, speed kept, smooth per tick, never snapped
//                      back. LAUNCH mode (a slow take-off) = air control toward the stick, one tick's accel
//                      at most, no speed farming. No input = no write. A Fusion launch re-anchors.
// Also: the C4 is THROWN (not plantable: a planted offhand cannot be used in the air, user 2026-10-01) and
// the Archer's landing-stumble watcher counts an airborne Breacher.
// Negative controls: the old always-launch gate, a steer with no budget, map 1's snap-back clamp and the
// whole 2026-09-29 steer (fixtures/bair_v1_20260929.gsc, replayed on the user's own launch) must FAIL.
'use strict';
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..', '..');
const MOD = path.join(root, 'scripts', 'zm', 'zm_tod2_cybercity');
const cards = fs.readFileSync(path.join(MOD, '_tod_class_cards.gsc'), 'utf8');
const kit = fs.readFileSync(path.join(MOD, '_tod_class_kit.gsc'), 'utf8');
let checks = 0;
const fails = [];
const ok = (c, msg) => { checks++; if (!c) fails.push(msg); };

const defs = src => Object.fromEntries([...src.matchAll(/^#define\s+(TOD_\w+)\s+([-\d.]+)\s*(?:\/\/.*)?$/gm)].map(m => [m[1], +m[2]]));
const D = { ...defs(cards), ...defs(kit) };
const body = (src, name) => {
  const m = src.match(new RegExp('function ' + name + '\\(([^)]*)\\)\\s*\\{([\\s\\S]*?)\\n\\}'));
  if (!m) throw new Error('no function ' + name);
  return { params: m[1].split(',').map(s => s.trim()).filter(Boolean), text: m[2] };
};
// A GSC vector literal is a GROUPING paren (not a call: no name, `)` or `]` before it) holding exactly
// two top-level commas; its parts may nest parens of their own, so this walks balanced brackets.
function tuples(s) {
  let out = '', i = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === '"') { const j = s.indexOf('"', i + 1); out += s.slice(i, j + 1); i = j + 1; continue; }
    const before = out.match(/([A-Za-z_]\w*|[\])])\s*$/);
    if (c === '(' && (!before || before[1] === 'return')) {
      let depth = 0, j = i, cuts = [];
      for (; j < s.length; j++) {
        const d = s[j];
        if (d === '"') { j = s.indexOf('"', j + 1); continue; }
        if (d === '(' || d === '[') depth++;
        else if (d === ')' || d === ']') { depth--; if (depth === 0) break; }
        else if (d === ',' && depth === 1) cuts.push(j);
      }
      const inner = s.slice(i + 1, j);
      if (cuts.length === 2) {
        const a = s.slice(i + 1, cuts[0]), b = s.slice(cuts[0] + 1, cuts[1]), c3 = s.slice(cuts[1] + 1, j);
        out += 'vec(' + tuples(a) + ',' + tuples(b) + ',' + tuples(c3) + ')';
      } else out += '(' + tuples(inner) + ')';
      i = j + 1;
      continue;
    }
    out += c; i++;
  }
  return out;
}
// GSC -> JS: comments out, method calls, vector literals, waits, endons, #define names.
function toJs(text) {
  let s = text.replace(/\/\/[^\n]*/g, '');
  s = s.replace(/\b(self|p) endon\([^;]*\);/g, '');
  s = s.replace(/\b(self|p|e) ([A-Za-z_]\w*)\(/g, '$1.$2(');
  s = tuples(s);
  s = s.replace(/\bwait\s+([\d.]+)\s*;/g, 'yield $1;');
  return s;
}
function compile(fn, env, generator) {
  const js = toJs(fn.text);
  const locals = [...new Set([...js.replace(/"[^"\n]*"/g, '').matchAll(/(?<![.\w])([A-Za-z_]\w*)\s*=(?!=)/g)].map(m => m[1]))]
    .filter(n => !fn.params.includes(n) && n !== 'self');
  const decl = locals.length ? 'let ' + locals.join(',') + ';' : '';
  const src = `with (env) { return function${generator ? '*' : ''}(self${fn.params.length ? ',' + fn.params.join(',') : ''}) { ${decl} ${js} } }`;
  return new Function('env', src)(env);
}
const deg = Math.PI / 180;
const base = {
  ...D, vec: (a, b, c) => [a, b, c], isdefined: x => x !== undefined && x !== null, IS_TRUE: x => !!x,
  Sqrt: Math.sqrt, Abs: Math.abs, Int: x => Math.trunc(x), Length: v => Math.hypot(v[0], v[1], v[2]),
  AngleClamp180: a => { a = ((a + 180) % 360 + 360) % 360 - 180; return a; },
  VectorToAngles: v => [0, Math.atan2(v[1], v[0]) / deg, 0],
  AnglesToForward: a => [Math.cos(a[1] * deg), Math.sin(a[1] * deg), 0],
  AnglesToRight: a => [Math.sin(a[1] * deg), -Math.cos(a[1] * deg), 0],
  Distance: (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]),
};

// ---- 1. THE PUSH ------------------------------------------------------------------------------
const pushFn = compile(body(cards, 'fusion_push'), { ...base });
const push = (feet, org, reach) => pushFn(null, feet, org, reach);
const len2 = v => Math.hypot(v[0], v[1]);
const R = 176;   // tier-2 reach (112 + 64)
ok(len2(push([0, 0, 30], [0, 0, 0], R)) < 1e-9, 'straight over the burst: no sideways push (straight up)');
const beside = push([80, 0, 30], [0, 0, 0], R);
ok(beside[0] > 0 && Math.abs(beside[1]) < 1e-9 && beside[2] === 0, 'beside the burst: pushed AWAY from it, flat');
ok(len2(beside) > 150 && len2(beside) <= D.TOD_FJUMP_PUSH_MAX, `a mid-reach push is a real shove (${len2(beside).toFixed(0)} u/s, max ${D.TOD_FJUMP_PUSH_MAX})`);
for (let x = 0; x <= R; x += 8) for (const z of [0, 20, 60, 120])
  ok(len2(push([x, 0, z], [0, 0, 0], R)) <= D.TOD_FJUMP_PUSH_MAX + 1e-9, `never over PUSH_MAX at (${x},${z})`);
// same direction from the burst, nearer = stronger (the "how close to the center" part)
const dir = [0.8, 0, 0.6];
const at = k => push([dir[0] * k, dir[1] * k, dir[2] * k - D.TOD_FJUMP_CHEST], [0, 0, 0], R);
ok(len2(at(40)) > len2(at(100)) && len2(at(100)) > len2(at(170)), 'closer to the burst = a stronger push along the same line');
ok(Math.abs(len2(at(R)) - D.TOD_FJUMP_PUSH_MAX * D.TOD_FJUMP_PUSH_EDGE * 0.8) < 0.5, 'at the edge of the reach the push is PUSH_EDGE of max (its sideways share)');

// ---- 2. THE JUMP GATE --------------------------------------------------------------------------
function runTry(src, scenario) {
  let now = 1000, launched = null;
  const logs = [];
  const p = {
    tod_fjump_ms: scenario.lastMs, ground: scenario.ground, flying: scenario.flying, mantle: scenario.mantle,
    IsOnGround() { return this.ground; }, IsMantling() { return !!this.mantle; }, GetEntityNumber() { return 0; },
    fusion_jump_blocked() { return this.flying ? 'jumppad' : (this.mantle ? 'mantle' : undefined); },
    fusion_jump(org, l, reach, waited) { launched = { waited }; },
  };
  const env = { ...base, GetTime: () => now, IsAlive: () => true, dev_log: s => logs.push(s) };
  const gen = compile(body(src, 'fusion_jump_try'), env, true)(p, [0, 0, 0], 3, R);
  for (let tick = 0; tick < 40; tick++) {
    const r = gen.next(); if (r.done) break;
    now += 50;
    if (scenario.jumpAtMs !== undefined && now - 1000 >= scenario.jumpAtMs) p.ground = false;
  }
  return { launched, logs };
}
{
  const a = runTry(cards, { ground: false });
  ok(a.launched && a.launched.waited === 0, 'airborne at the burst: launched at once');
  const b = runTry(cards, { ground: true, jumpAtMs: 100 });
  ok(b.launched && b.launched.waited >= 50 && b.launched.waited <= D.TOD_FJUMP_JUMP_GRACE_MS, `grounded, jumps 100 ms later: launched (waited ${b.launched && b.launched.waited} ms)`);
  const c = runTry(cards, { ground: true });
  ok(!c.launched && c.logs.some(l => /FUSION_JUMP_SKIP .*reason=no_jump/.test(l)), 'grounded and never jumps: NO launch, logged no_jump (the user\'s accident)');
  const d = runTry(cards, { ground: true, jumpAtMs: D.TOD_FJUMP_JUMP_GRACE_MS + 200 });
  ok(!d.launched, 'a jump long after the burst does not launch');
  const e = runTry(cards, { ground: false, flying: true });
  ok(!e.launched && e.logs.some(l => /reason=jumppad/.test(l)), 'a jump-pad flyer is never launched');
  const f = runTry(cards, { ground: false, mantle: true });
  ok(!f.launched && f.logs.some(l => /reason=mantle/.test(l)), 'a mantling Breacher is never launched');
  const g = runTry(cards, { ground: false, lastMs: 900 });
  ok(!g.launched, 'one try per burst (a second call inside TOD_FJUMP_GAP_MS is ignored)');
  // NEGATIVE CONTROL: the old gate (launch whatever the ground says) must fail the accident check
  const old = cards.replace(/\twaited = 0;\n\tif \( self IsOnGround\(\) \)\n\t\{[\s\S]*?\n\t\}\n\tself fusion_jump/, '\twaited = 0;\n\tself fusion_jump');
  ok(old !== cards, 'negative control built (the always-launch gate)');
  const h = runTry(old, { ground: true });
  ok(!!h.launched, 'NEGATIVE CONTROL: the always-launch gate DOES launch a grounded player (so the check above can fail)');
}
ok(/p thread fusion_jump_try\( org, l, rj \);/.test(cards) && !/p fusion_jump\( org, l \);/.test(cards), 'blast_heal routes every burst through the jump gate');
ok(!/TOD_FJUMP_PUSH\s+140/.test(cards), 'the flat 140 shove is retired');

// ---- 3. AIR STEERING (reworked 2026-10-01: "I want it to be like the athlete") ------------------
// ONE lane per flight: ATHLETE mode (a take-off with momentum = map 1's lane 4) or LAUNCH mode (a slow
// take-off = air control). The 2026-09-29 function (fixtures/bair_v1_20260929.gsc) ran both lanes at
// once and they fought; it is replayed on the user's own launch as the negative control.
const oldAir = fs.readFileSync(path.join(__dirname, 'fixtures', 'bair_v1_20260929.gsc'), 'utf8');
function flight(src, s) {
  const writes = [], logs = [];
  let now = 5000;
  const p = {
    vel: s.vel.slice(), stick: s.stick || [0, 0], yaw: s.yaw || 0, ground: false, act: s.act !== false,
    tod_fjump_air: undefined, tod_fjump_launch_ms: undefined,
    can_act() { return this.act; }, IsMantling() { return false; }, GetLinkedEnt() { return undefined; },
    IsOnGround() { return this.ground; }, GetVelocity() { return this.vel.slice(); },
    GetNormalizedMovement() { return [this.stick[0], this.stick[1], 0]; }, GetPlayerAngles() { return [0, this.yaw, 0]; },
    SetVelocity(v) { this.vel = v.slice(); writes.push(v.slice()); }, GetEntityNumber() { return 0; },
    AttackButtonPressed() { return !!s.fire; }, IsReloading() { return false; },
  };
  const env = { ...base, GetTime: () => now, dev_log: m => logs.push(m) };
  const step = compile(body(src, 'breacher_air_steer'), env);
  const trace = [];
  for (let t = 0; t < (s.ticks || 40); t++) {
    if (s.at && s.at[t]) s.at[t](p, now);
    if (s.yawRate) p.yaw += s.yawRate;
    step(p);
    trace.push(p.vel.slice());
    now += 50;
  }
  if (s.land) { p.ground = true; step(p); }
  return { p, writes, trace, logs };
}
const hspeed = v => Math.hypot(v[0], v[1]);
const heading = v => Math.atan2(v[1], v[0]) / deg;
const maxKick = (start, trace) => { let k = 0, prev = start; for (const v of trace) { k = Math.max(k, Math.hypot(v[0] - prev[0], v[1] - prev[1])); prev = v; } return k; };
const ACC = D.TOD_BAIR_DRIFT_ACCEL * D.TOD_KIT_TICK;
{
  // ATHLETE MODE (a take-off with momentum): map 1's lane 4
  ok(D.TOD_BAIR_TURN === 90 + 30 * 5 && D.TOD_BAIR_BUDGET === 20 + 8 * 5, `the turn rate / budget are map 1's ATHLETE at Lv5 (${D.TOD_BAIR_TURN} deg/s, ${D.TOD_BAIR_BUDGET} deg)`);
  const idle = flight(kit, { vel: [300, 0, 200] });
  ok(idle.writes.length === 0, 'no input: the engine\'s own flight is never written (a momentum flight)');
  ok(idle.logs.some(l => /BAIR_MODE .*mode=athlete why=takeoff speed=300/.test(l)), 'a 300 u/s take-off flies ATHLETE mode (logged)');
  const turn = flight(kit, { vel: [300, 0, 200], stick: [0, 1], yaw: 0, ticks: 60 });
  const turned = Math.abs(heading(turn.p.vel));
  ok(turned > 30, `strafe curves the flight (${turned.toFixed(1)} deg)`);
  ok(turned <= D.TOD_BAIR_BUDGET + 1e-6, `never past the budget (${turned.toFixed(1)} of ${D.TOD_BAIR_BUDGET} deg)`);
  ok(turn.trace.every(v => hspeed(v) <= 300 + 1e-6), 'curving never adds speed');
  const stepMax = D.TOD_BAIR_TURN * D.TOD_KIT_TICK * deg;
  ok(maxKick([300, 0], turn.trace) <= 2 * 300 * Math.sin(stepMax / 2) + 1e-6, `smooth: one tick turns the flight at most ${(D.TOD_BAIR_TURN * D.TOD_KIT_TICK).toFixed(0)} deg (largest change ${maxKick([300, 0], turn.trace).toFixed(1)} u/s)`);
  const fwdOnly = flight(kit, { vel: [300, 0, 0], stick: [1, 0], yaw: 0 });
  const backOnly = flight(kit, { vel: [300, 0, 0], stick: [-1, 0], yaw: 0 });
  ok(fwdOnly.writes.length === 0 && backOnly.writes.length === 0, 'forward / back stick does nothing to a momentum flight (map 1: strafe steers, the stick axis does not)');
  // the budget never turns a flight BACK: a heading already past it (the engine's own air control) is left alone
  const past = { 6: (p) => { const s0 = hspeed(p.vel), h = 80 * deg; p.vel = [Math.cos(h) * s0, Math.sin(h) * s0, p.vel[2]]; } };
  const held = flight(kit, { vel: [300, 0, 0], stick: [0, -1], yaw: 0, ticks: 8, at: past });
  ok(Math.abs(heading(held.trace[6]) - 80) < 1e-6, `a heading already past the budget is never snapped back (stays ${heading(held.trace[6]).toFixed(1)} deg)`);
  const snapBack = kit.replace(/\n\t+if \( \( step \* gap \) < 0 \) step = 0;/, '');
  ok(snapBack !== kit, 'negative control built (map 1\'s clamp, which can turn a step back)');
  const snapped = flight(snapBack, { vel: [300, 0, 0], stick: [0, -1], yaw: 0, ticks: 8, at: past });
  ok(heading(snapped.trace[6]) < 79, `NEGATIVE CONTROL: without the rule the clamp snaps it back (${heading(snapped.trace[6]).toFixed(1)} deg)`);

  // LAUNCH MODE (a slow take-off): air control
  const vert = flight(kit, { vel: [0, 0, 700], stick: [1, 0], yaw: 90, ticks: 30 });
  ok(vert.logs.some(l => /BAIR_MODE .*mode=launch why=takeoff/.test(l)), 'a near-vertical take-off flies LAUNCH mode (logged)');
  ok(hspeed(vert.p.vel) > 150 && hspeed(vert.p.vel) <= D.TOD_BAIR_DRIFT + 1e-6, `a vertical launch moves where the stick points, up to ${D.TOD_BAIR_DRIFT} (${hspeed(vert.p.vel).toFixed(0)})`);
  ok(Math.abs(heading(vert.p.vel) - 90) < 0.5, 'the air control follows the view-relative stick');
  ok(flight(kit, { vel: [60, 0, 900] }).writes.length === 0, 'no input: a launch is never written either');
  const keepGoing = flight(kit, { vel: [190, 0, 0], stick: [1, 0], yaw: 0 });
  ok(keepGoing.trace.every(v => Math.abs(hspeed(v) - 190) < 1e-6), 'pushing the way you already fly never slows you (190 kept)');
  const brake = flight(kit, { vel: [120, 0, 0], stick: [-1, 0], yaw: 0, ticks: 40 });
  ok(brake.p.vel[0] < 0 && hspeed(brake.p.vel) <= D.TOD_BAIR_DRIFT + 1e-6 && maxKick([120, 0], brake.trace) <= ACC + 1e-6, 'pulling back brakes and reverses, never faster than DRIFT, never more than one tick\'s accel');
  // no speed farming: the stick swept round while the view spins (the air-strafe trick) never beats max(start, DRIFT)
  const farm = flight(kit, { vel: [150, 0, 900], ticks: 120, yawRate: 9, at: Object.fromEntries([...Array(120).keys()].map(t => [t, (p) => { const a = t * 0.7; p.stick = [Math.cos(a), Math.sin(a)]; }])) });
  ok(farm.trace.every(v => hspeed(v) <= Math.max(150, D.TOD_BAIR_DRIFT) + 1e-6), `no speed farming: a spinning stick + view never beats max(start, DRIFT) (peak ${Math.max(...farm.trace.map(hspeed)).toFixed(0)})`);

  // THE USER'S LAUNCH (the 09-30 17:56 + 10-01 logs: speed_out ~150 behind, W + D held, the view turning):
  // the shipping steer eases the flight round; the 2026-09-29 one fought itself every tick.
  const theirs = { vel: [-140, 60, 995], stick: [1, 0.7], yaw: 0, yawRate: 3, ticks: 50 };
  const now1 = flight(kit, theirs), was = flight(oldAir, theirs);
  ok(maxKick([-140, 60], now1.trace) <= ACC + 1e-6, `the user's launch: the flight eases (largest change ${maxKick([-140, 60], now1.trace).toFixed(1)} u/s a tick, max ${ACC})`);
  // the logged symptom: the turn lane's work (BAIR_LAND turned_deg) far past its budget = another lane undoing it every tick
  ok((now1.p.tod_bair_turned || 0) <= D.TOD_BAIR_BUDGET, `the user's launch: no lane undoes another (turn-lane work ${(now1.p.tod_bair_turned || 0).toFixed(0)} deg, budget ${D.TOD_BAIR_BUDGET})`);
  ok(was.p.tod_bair_turned > 5 * D.TOD_BAIR_BUDGET, `NEGATIVE CONTROL: the 2026-09-29 steer fights itself on the same launch (${was.p.tod_bair_turned.toFixed(0)} deg of turning against a ${D.TOD_BAIR_BUDGET}-deg budget; the logs read 388..1859)`);

  ok(flight(kit, { vel: [300, 0, 0], stick: [0, 1], act: false }).writes.length === 0, 'a frozen / downed / pad-flying Breacher (can_act false) is never steered');
  // a Fusion launch mid-flight: the new push must not be trimmed back by the old anchor (a push under the
  // x1.25 re-anchor rule: 250 -> 277 u/s; without the launch stamp the cone trims it to the old 250)
  const launchAt = { 10: (p, now) => { p.vel = [250, 120, 900]; p.tod_fjump_launch_ms = now; } };
  const relaunch = flight(kit, { vel: [250, 0, 0], ticks: 14, at: launchAt });
  ok(Math.abs(hspeed(relaunch.trace[12]) - Math.hypot(250, 120)) < 1, `a Fusion launch re-anchors the steering (speed kept ${hspeed(relaunch.trace[12]).toFixed(0)})`);
  ok(relaunch.logs.some(l => /BAIR_MODE .*why=fusion/.test(l)), 'the re-anchor is logged why=fusion');
  const stale = flight(kit, { vel: [250, 0, 0], ticks: 14, at: { 10: (p) => { p.vel = [250, 120, 900]; } } });
  ok(hspeed(stale.trace[12]) <= 250 + 1e-6, `NEGATIVE CONTROL: the same push with no launch stamp is trimmed to the old cap (${hspeed(stale.trace[12]).toFixed(0)})`);
  // NEGATIVE CONTROL: without the budget clamp the strafe lane turns past the budget
  const noBudget = kit.replace(/if \( new_dev > TOD_BAIR_BUDGET \) step = TOD_BAIR_BUDGET - cur_dev;\n\t+else if \( new_dev < \( 0 - TOD_BAIR_BUDGET \) \) step = \( 0 - TOD_BAIR_BUDGET \) - cur_dev;/, '');
  ok(noBudget !== kit, 'negative control built (no turn budget)');
  const free = flight(noBudget, { vel: [300, 0, 0], stick: [0, 1], yaw: 0, ticks: 80 });
  const cut = flight(kit, { vel: [300, 0, 0], stick: [0, 1], yaw: 0, ticks: 80 });
  ok(Math.abs(heading(free.p.vel)) > Math.abs(heading(cut.p.vel)) + 5, 'NEGATIVE CONTROL: removing the budget turns further (so the budget check can fail)');
  // THE LANDING SUMMARY: what the player did in the air
  const landed = flight(kit, { vel: [300, 0, 200], fire: true, ticks: 6, land: true });
  ok(landed.logs.some(l => /BAIR_LAND .*mode=athlete .*fire_ticks=6 reload_ticks=0 c4_press=0 c4_air=0 cluster_press=0 cluster_air=0/.test(l)), 'BAIR_LAND reports the mode, the shots, the reload and the air presses against throws');
}
ok(/if \( kit == TOD_KIT_BREACHER \) self breacher_air_steer\(\);/.test(kit), 'kit_loop steers the Breacher every tick');
ok(/if \( frag_edge \) self\.tod_bair_c4_press\+\+;/.test(kit) && /if \( tac_edge \) self\.tod_bair_cl_press\+\+;/.test(kit), 'kit_loop counts the C4 / Cluster presses made in the air');
ok((kit.match(/air = !\( self IsOnGround\(\) \);/g) || []).length === 2 && /C4_PLANT .*" airborne=" \+ air/.test(kit) && /CLUSTER_THROW .*" airborne=" \+ air/.test(kit), 'every C4 / Cluster throw logs whether it left the hand in the air');
ok(/!self can_act\(\) \|\| self IsMantling\(\) \|\| isdefined\( self GetLinkedEnt\(\) \)/.test(kit), 'the steer refuses a frozen, mantling or linked Breacher');
// THE C4 IN THE AIR (2026-10-01, user: "the breacher cant throw C4 mid air"): "plantable" makes an offhand
// planted like a claymore, which the engine refuses off the ground (the Cluster, not plantable, always
// threw in the air). The C4 is thrown; bBoxTrace keeps the capsule hit-trace plantable gave its sticking.
{
  const gdt = fs.readFileSync(path.join(root, 'source_data', 'tod_breacher_kit.gdt'), 'utf8');
  const c4 = (gdt.match(/"tod_c4" \( "grenadeweapon\.gdf" \)\s*\{([\s\S]*?)\n\t\}/) || [])[1] || '';
  ok(/"plantable" "0"/.test(c4), 'the C4 is thrown, not planted (a planted offhand cannot be used in the air)');
  ok(/"bBoxTrace" "1"/.test(c4) && /"stickiness" "Stick to all"/.test(c4), 'the C4 keeps its capsule hit-trace and sticks to everything');
}
// THE LANDING (map 1's athlete lands clean): the Archer's host-dvar watcher holds the landing stumble off while
// any Archer OR Breacher is airborne
{
  const archer = fs.readFileSync(path.join(MOD, '_tod_archer.gsc'), 'utf8');
  const sw = (archer.match(/function stumble_watch\(\)[\s\S]*?\n\}/) || [''])[0];
  ok(/is_archer\( p \) \|\| is_breacher\( p \)/.test(sw) && /function is_breacher\( player \)[\s\S]{0,160}"heavy"/.test(archer), 'no landing stumble while a Breacher is airborne (the Archer\'s watcher counts Breachers)');
}

if (fails.length) { console.error(`BREACHER FUSION/AIR: ${fails.length} of ${checks} checks FAILED`); for (const f of fails) console.error('  FAIL ' + f); process.exit(1); }
console.log(`BREACHER FUSION/AIR: ${checks} checks - push straight up over the burst and outward beside it (max ${D.TOD_FJUMP_PUSH_MAX}, ${D.TOD_FJUMP_PUSH_EDGE * 100}% at the edge), launch only on a jump (grace ${D.TOD_FJUMP_JUMP_GRACE_MS} ms), ATHLETE mode = map 1's lane 4 (${D.TOD_BAIR_TURN} deg/s, ${D.TOD_BAIR_BUDGET} deg) / LAUNCH mode = air control (${D.TOD_BAIR_DRIFT} u/s), one lane per flight, the C4 thrown in the air, negative controls. PASS`);
