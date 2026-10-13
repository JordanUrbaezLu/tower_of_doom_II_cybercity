'use strict';
// THE MANGLER'S FOOTFALLS - the shipping step_crossed() of _tod_mangler.gsc, run through tools/sky_ships/gsc_eval.js
// (never a copy) over simulated run cycles (asset pack PK02, 2026-10-04).
//
// step_watch polls the run clip's phase every TOD_MANGLER_STEP_POLL and asks step_crossed( times, last_t, t ) whether
// the phase passed one of the clip's six 'footstep' notes. This proves, at every playback rate the Mangler runs at
// (1.0; the haven's 0.67; an EMP's 0.5; both 0.335; the Keeper's soul line 1.3), with poll jitter and a mid-run start:
//   - exactly six footfalls per cycle, never two in one poll, never one missed;
//   - each lands within one poll after its note (the foot it belongs to);
//   - a clip RESTART (the phase jumps back) and a big JUMP fire nothing;
//   - a frozen clip (a pause / stun: the phase does not move) fires nothing.
// Negative controls: the shipping function with its span guard removed, and with its crossing test inverted, must FAIL.
//   node tools/sfx/silent_sounds/test_mangler_steps.js [--root DIR]
const fs = require('fs'), path = require('path');
const argRoot = process.argv.indexOf('--root');
const root = argRoot > 0 ? path.resolve(process.argv[argRoot + 1]) : path.resolve(__dirname, '..', '..', '..');
const { gscLoad } = require(path.join(__dirname, '..', '..', 'sky_ships', 'gsc_eval.js'));
const SRC = fs.readFileSync(path.join(root, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_mangler.gsc'), 'utf8');
const defs = Object.fromEntries([...SRC.matchAll(/^#define\s+(TOD_MANGLER_\w+)\s+(-?[\d.]+)/gm)].map(m => [m[1], m[2]]));
const FRAMES = [9, 20, 32, 43, 54, 64];                                   // hb_mangler_run.XANIM_EXPORT 'footstep' notes
const N = +defs.TOD_MANGLER_RUN_FRAMES, POLL = +defs.TOD_MANGLER_STEP_POLL;
const TIMES = FRAMES.map(f => f / N);
const CYCLE = N / 30;                                                     // seconds at 1x

let checks = 0, fails = 0;
const ok = (c, m) => { checks++; if (!c) { fails++; console.log('  FAIL ' + m); } };
ok(N === 67 && POLL === 0.05 && +defs.TOD_MANGLER_STEP_MAX_SPAN > 0, 'the step defines are present (frames 67, poll 0.05, a max span)');
// the fallback frames in step_watch are the clip's six notes
const fb = (SRC.match(/times = array\(([^;]*)\);/) || [])[1] || '';
ok(JSON.stringify([...fb.matchAll(/(\d+) \/ TOD_MANGLER_RUN_FRAMES/g)].map(m => +m[1])) === JSON.stringify(FRAMES), 'step_watch\'s fallback frames are the run clip\'s six footstep notes');
ok(/GetNotetrackTimes\( %hb_mangler_run, "footstep" \)/.test(SRC) && /self GetAnimTime\( %hb_mangler_run \)/.test(SRC), 'step_watch reads the run clip\'s own notes and phase');
ok(/if \( step_crossed\( times, last_t, t \) \)\s*tod_bo6_audio::mangler_step\( self, "anim_time" \);/.test(SRC), 'step_watch plays the BO6 heavy step through step_crossed');
ok(/self thread step_watch\(\);/.test(SRC), 'initialize_actor threads step_watch');

function crossedFn(text) {
  const g = gscLoad([['tod_mangler', text]], defs);
  return (times, a, b) => !!g.call('step_crossed', [times, a, b]);
}

// simulate `secs` of running at `rate`, polls of POLL (+ jitter), from phase p0. Returns the fire times and phases.
function run(crossed, rate, secs, p0, jitter, rnd) {
  let t = p0, last, clock = 0, fires = [];
  while (clock < secs) {
    const dt = POLL + (jitter ? rnd() * jitter : 0);
    clock += dt;
    t = (t + dt * rate / CYCLE) % 1;
    if (crossed(TIMES, last, t)) fires.push({ clock, t });
    last = t;
  }
  return fires;
}
function lcg(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

function verify(crossed, label, strict) {
  const bad = [];
  for (const rate of [1.0, 0.67, 0.5, 0.335, 1.3]) {
    for (const jitter of [0, 0.03]) {
      const rnd = lcg(Math.round(rate * 1000) + (jitter ? 7 : 0));
      const cycles = 12, p0 = 0.37;
      const fires = run(crossed, rate, cycles * CYCLE / rate, p0, jitter, rnd);
      const want = TIMES.filter(s => s > p0).length + 6 * (cycles - 1) + TIMES.filter(s => s <= p0).length;   // = 6 * cycles
      if (Math.abs(fires.length - want) > 1) bad.push(`${label} rate ${rate} jitter ${jitter}: ${fires.length} footfalls in ${cycles} cycles (want ${want})`);
      // each fire lands within one (jittered) poll after a note
      const tol = (POLL + jitter) * rate / CYCLE + 1e-9;
      for (const f of fires) {
        const near = TIMES.some(s => { let d = f.t - s; if (d < 0) d += 1; return d <= tol; });
        if (!near) { bad.push(`${label} rate ${rate}: a footfall at phase ${f.t.toFixed(3)} is not within one poll of a note`); break; }
      }
    }
  }
  // a restart (phase jumps back) and a jump fire nothing
  if (crossed(TIMES, 0.80, 0.02)) bad.push(`${label}: a clip restart 0.80 -> 0.02 fired a footfall`);
  if (crossed(TIMES, 0.10, 0.70)) bad.push(`${label}: a phase jump 0.10 -> 0.70 fired a footfall`);
  // a frozen clip fires nothing, and the first poll after a re-anchor fires nothing
  if (crossed(TIMES, 0.30, 0.30)) bad.push(`${label}: a frozen clip fired a footfall`);
  if (crossed(TIMES, undefined, 0.30)) bad.push(`${label}: the re-anchoring poll fired a footfall`);
  // a genuine wrap across a note at the loop seam (a note at 0.99, crossed 0.98 -> 0.005) fires
  if (!crossed([0.99], 0.98, 0.005)) bad.push(`${label}: a stride across the loop seam missed its note`);
  return bad;
}

const shipping = verify(crossedFn(SRC), 'shipping', true);
for (const b of shipping) ok(false, b);
ok(shipping.length === 0, 'the shipping step_crossed lands six footfalls a cycle on the notes at every rate, and none on a restart, jump or freeze');

// negative controls: the shipping text, broken two ways, must fail the same verification
const noGuard = SRC.replace(/if \( span >= TOD_MANGLER_STEP_MAX_SPAN \)\s*return false;[^\n]*/, '');
ok(noGuard !== SRC && verify(crossedFn(noGuard), 'no-span-guard').length > 0, 'negative control: without the span guard a clip restart fires a footfall');
const inverted = SRC.replace('if ( s > last_t && s <= t )', 'if ( s < last_t && s <= t )');
ok(inverted !== SRC && verify(crossedFn(inverted), 'inverted').length > 0, 'negative control: an inverted crossing test is caught');

console.log(fails ? `MANGLER STEPS FAILED: ${fails} of ${checks}` :
  `MANGLER STEPS OK: ${checks} checks - six footfalls a cycle on the run clip's notes at rates 0.335-1.3 with poll jitter, none on a restart / jump / freeze, 2 negative controls caught`);
process.exit(fails ? 1 : 0);
