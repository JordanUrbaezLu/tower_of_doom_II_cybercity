'use strict';
// tools/fxgen/horde_eyes/test_eye_glow.js - THE HORDE'S EYES (PK04, 2026-10-04): the wiring contract.
//
//   node tools/fxgen/horde_eyes/test_eye_glow.js               the repo
//   node tools/fxgen/horde_eyes/test_eye_glow.js --root DIR    DIR's files first, the repo for the rest (a stage)
//   node tools/fxgen/horde_eyes/test_eye_glow.js --ledger F    POST-LINK: both effects + the client script are in the
//                                                              linker's asset ledger F
//
// The stock eye lane (_zm.csc createZombieEyesInternal) plays level._override_eye_fx / self._eyeglow_fx_override when
// set, else zm_usermap's ORANGE. This gate proves the map sets them, with the generated effects, before any actor
// lights an eye: the names agree in every file that carries them (the .gsh, the generator, the zone, the golden zombie's
// body define), the client module runs right after zm_usermap::main(), it chains the stock "additional" eye callback
// instead of stealing it, it re-lights a golden zombie's already-lit red eyes (delete THEN create), and the SHIPPING
// eye_fx_for_model() picks gold for the golden body only (run through tools/sky_ships/gsc_eval.js). Then it breaks the
// sources nine ways and requires a catch on each (the mutants).
const fs = require('fs');
const path = require('path');
const { gscLoad } = require('../../sky_ships/gsc_eval.js');

const REPO = path.resolve(__dirname, '..', '..', '..');
const argv = process.argv.slice(2);
const opt = (k) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : undefined; };
const ROOT = opt('--root') ? path.resolve(opt('--root')) : REPO;

const P = {
  gsh: 'scripts/zm/zm_tod2_cybercity/_tod_eye_glow.gsh',
  csc: 'scripts/zm/zm_tod2_cybercity/_tod_eye_glow.csc',
  entry: 'scripts/zm/zm_tod2_cybercity.csc',
  zone: 'zone_source/zm_tod2_cybercity.zone',
  golden: 'scripts/zm/zm_tod2_cybercity/_tod_golden_zombie.gsc',
  charcoal: 'scripts/zm/zm_tod2_cybercity/_tod_cyber_zombies.gsc',
  gen: 'tools/fxgen/horde_eyes/make_fx.py',
};
function read(rel) {
  for (const base of [ROOT, REPO]) {
    const f = path.join(base, rel);
    if (fs.existsSync(f)) return fs.readFileSync(f, 'utf8').replace(/\r\n/g, '\n');
  }
  return null;
}

function defines(text) {
  const d = {};
  for (const m of (text || '').matchAll(/^\s*#define\s+(\w+)\s+("[^"]*"|[^\s/]+)/gm)) d[m[1]] = m[2];
  return d;
}
const unq = s => (s || '').replace(/^"|"$/g, '');
function fnBody(src, name) {
  const m = new RegExp('function\\s+' + name + '\\s*\\([^)]*\\)\\s*\\{').exec(src || '');
  if (!m) return null;
  let depth = 1, j = m.index + m[0].length;
  while (depth && j < src.length) { if (src[j] === '{') depth++; else if (src[j] === '}') depth--; j++; }
  return src.slice(m.index + m[0].length, j - 1);
}
const strip = s => (s || '').replace(/\/\/[^\n]*/g, '').replace(/\/\*[\s\S]*?\*\//g, '');

// ---- the contract, as a function of the sources (so the mutants can run it) ----------------------------------------
function check(src) {
  const e = [];
  const ok = (c, msg) => { if (!c) e.push(msg); };
  for (const [k, v] of Object.entries(src)) if (v === null && k !== 'ledger') e.push('missing file: ' + P[k]);
  if (e.length) return e;

  // 1. the names, one source: the .gsh; the generator and the golden zombie agree with it
  const D = defines(src.gsh);
  const horde = unq(D.TOD_EYE_FX_HORDE), golden = unq(D.TOD_EYE_FX_GOLDEN), body = unq(D.TOD_EYE_GOLDEN_BODY);
  ok(horde && golden && body, 'the .gsh does not define TOD_EYE_FX_HORDE / TOD_EYE_FX_GOLDEN / TOD_EYE_GOLDEN_BODY');
  const relDir = (/^REL_DIR = '([^']+)'/m.exec(src.gen) || [])[1];
  const prefix = (/^PREFIX = '([^']+)'/m.exec(src.gen) || [])[1];
  const stems = [...(/EFFECTS = \{([\s\S]*?)\n\}/.exec(src.gen) || ['', ''])[1].matchAll(/'(fx_\w+)':/g)].map(m => m[1]);
  ok(prefix && stems.length === 2, 'cannot read the generator\'s PREFIX / EFFECTS');
  ok(stems.map(s => prefix + s).includes(horde), 'TOD_EYE_FX_HORDE ' + horde + ' is not an effect the generator makes');
  ok(stems.map(s => prefix + s).includes(golden), 'TOD_EYE_FX_GOLDEN ' + golden + ' is not an effect the generator makes');
  ok(horde !== golden, 'the horde and golden effects are the same');
  for (const s of stems) ok(src.efx.includes(s), 'the generated ' + relDir + '/' + s + '.efx is not on disk (run make_fx.py)');
  for (const n of [horde, golden]) ok(n.length <= 63, n + ' is over 63 characters (the engine truncates it)');
  const goldDefs = defines(src.golden);
  ok(unq(goldDefs.TOD_GOLDEN_MODEL_BODY) === body, 'TOD_EYE_GOLDEN_BODY "' + body + '" != _tod_golden_zombie.gsc TOD_GOLDEN_MODEL_BODY '
    + goldDefs.TOD_GOLDEN_MODEL_BODY);

  // 2. the zone packs both effects and the client script
  const zl = src.zone.split('\n').map(l => l.trim());
  ok(zl.includes('fx,' + horde), 'the zone has no fx,' + horde);
  ok(zl.includes('fx,' + golden), 'the zone has no fx,' + golden);
  ok(zl.includes('scriptparsetree,' + P.csc), 'the zone has no scriptparsetree,' + P.csc);

  // 3. the entry client script runs it, right after zm_usermap::main() (which sets the orange), before any actor
  const entry = strip(src.entry);
  ok(/^#using scripts\\zm\\zm_tod2_cybercity\\_tod_eye_glow;/m.test(src.entry), 'zm_tod2_cybercity.csc does not #using _tod_eye_glow');
  const main = fnBody(entry, 'main') || '';
  const iu = main.indexOf('zm_usermap::main();'), ii = main.indexOf('tod_eye_glow::init();');
  ok(iu >= 0 && ii > iu, 'tod_eye_glow::init() is not called after zm_usermap::main() in the client main()');
  ok(ii < 0 || !/\bwait\b|waitforclient/.test(main.slice(iu, ii)), 'something waits between zm_usermap::main() and tod_eye_glow::init()');

  // 4. the module: precache, the level override, the chained callback, the golden re-light
  const csc = strip(src.csc);
  ok(/^#using scripts\\zm\\_zm;/m.test(src.csc), '_tod_eye_glow.csc does not #using scripts\\zm\\_zm (zm:: calls)');
  ok(/^#insert scripts\\zm\\zm_tod2_cybercity\\_tod_eye_glow\.gsh;/m.test(src.csc), '_tod_eye_glow.csc does not #insert the .gsh');
  ok(/#precache\(\s*"client_fx",\s*TOD_EYE_FX_HORDE\s*\)/.test(csc), 'TOD_EYE_FX_HORDE is not precached as a client_fx');
  ok(/#precache\(\s*"client_fx",\s*TOD_EYE_FX_GOLDEN\s*\)/.test(csc), 'TOD_EYE_FX_GOLDEN is not precached as a client_fx');
  const init = fnBody(csc, 'init') || '';
  ok(/level\._override_eye_fx\s*=\s*TOD_EYE_FX_HORDE\s*;/.test(init), 'init() does not set level._override_eye_fx = TOD_EYE_FX_HORDE');
  const save = init.search(/level\.tod_eye_prev_cb\s*=\s*level\.zombie_eyes_clientfield_cb_additional\s*;/);
  const take = init.search(/level\.zombie_eyes_clientfield_cb_additional\s*=\s*&eyes_cb\s*;/);
  ok(save >= 0 && take > save, 'init() does not save the previous eye callback before taking the hook (it must chain, not steal)');
  const cb = fnBody(csc, 'eyes_cb') || '';
  const prev = cb.search(/self \[\[ level\.tod_eye_prev_cb \]\]\( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump \)/);
  ok(prev >= 0, 'eyes_cb() does not pass every argument on to the previous callback');
  const guard = cb.search(/!isdefined\( newVal \) \|\| !newVal \)\s*return;/);
  ok(guard >= 0 && guard > prev, 'eyes_cb() does not stop on an eyes-OFF call (newVal 0) after the chain');
  const del = cb.indexOf('zm::deleteZombieEyes( localClientNum )'), cre = cb.indexOf('zm::createZombieEyes( localClientNum )');
  const set = cb.search(/self\._eyeglow_fx_override\s*=\s*fx\s*;/);
  ok(set >= 0 && del > set && cre > del, 'eyes_cb() must set the gold override, THEN put out the red (delete), THEN re-light (create)');
  ok(/eye_fx_for_model\(\s*self\.model\s*\)/.test(cb), 'eyes_cb() does not choose by the body model (eye_fx_for_model( self.model ))');

  // 5. the SHIPPING chooser, run: gold for the golden body only
  try {
    const g = gscLoad([['tod_eye_glow', src.csc]], D);
    const pick = m => g.call('eye_fx_for_model', [m]);
    ok(pick(body) === golden, 'the golden body does not get the golden eye effect');
    for (const m of ['tod_charcoal_c_zom_dlc3_zombie_sentinel_body', 'tod_cyber_sprinter_body', 'c_zom_der_zombie_body1', '', undefined])
      ok(pick(m) === undefined, 'a non-golden body (' + m + ') does not keep the level effect');
  } catch (ex) { e.push('eye_fx_for_model() does not run in gsc_eval: ' + ex.message); }

  // 6. one owner: nothing else in scripts/ takes the hooks (a later owner would silently drop ours)
  for (const [rel, text] of src.others) {
    if (/zombie_eyes_clientfield_cb_additional\s*=/.test(strip(text))) e.push(rel + ' also assigns level.zombie_eyes_clientfield_cb_additional');
    if (/_override_eye_fx\s*=/.test(strip(text))) e.push(rel + ' also assigns level._override_eye_fx');
  }

  // 7. the server's dev START line names the effect it claims (no bare "orange=0")
  const start = (/dev_log\(\s*"START rev=[\s\S]*?\);/.exec(src.charcoal) || [''])[0];
  ok(/eye_fx=" \+ TOD_EYE_FX_HORDE/.test(start), '_tod_cyber_zombies.gsc START line does not report eye_fx=TOD_EYE_FX_HORDE');
  ok(/^#insert scripts\\zm\\zm_tod2_cybercity\\_tod_eye_glow\.gsh;/m.test(src.charcoal), '_tod_cyber_zombies.gsc does not #insert the .gsh');
  return e;
}

function sources() {
  const efxDir = path.join(ROOT, 'share/raw/fx/tod/cyber'), efxRepo = path.join(REPO, 'share/raw/fx/tod/cyber');
  const efx = [];
  for (const d of [efxDir, efxRepo]) if (fs.existsSync(d)) for (const f of fs.readdirSync(d)) if (f.endsWith('.efx')) efx.push(f.slice(0, -4));
  const others = [];
  const walk = (d) => { for (const x of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, x.name); if (x.isDirectory()) walk(p); else if (/\.(gsc|csc)$/.test(x.name)) others.push(p); } };
  walk(path.join(REPO, 'scripts'));
  const mine = path.join(REPO, P.csc);
  return {
    gsh: read(P.gsh), csc: read(P.csc), entry: read(P.entry), zone: read(P.zone), golden: read(P.golden),
    charcoal: read(P.charcoal), gen: read(P.gen), efx,
    others: others.filter(p => path.resolve(p) !== path.resolve(mine)).map(p => [path.relative(REPO, p).replace(/\\/g, '/'),
      (() => { const rel = path.relative(REPO, p); const staged = path.join(ROOT, rel); return fs.readFileSync(fs.existsSync(staged) ? staged : p, 'utf8'); })()]),
  };
}

// ---- POST-LINK -------------------------------------------------------------------------------------------------------
if (opt('--ledger')) {
  const D = defines(read(P.gsh));
  const want = [['fx', unq(D.TOD_EYE_FX_HORDE)], ['fx', unq(D.TOD_EYE_FX_GOLDEN)], ['scriptparsetree', P.csc]];
  const have = new Set();
  for (const line of fs.readFileSync(opt('--ledger'), 'utf8').split(/\r?\n/)) {
    const c = line.split(',');
    if (c.length > 2) have.add(c[1].trim().toLowerCase() + ',' + c[2].trim().replace(/\\/g, '/').toLowerCase());
  }
  const miss = want.filter(([t, n]) => !have.has(t + ',' + n.toLowerCase()));
  for (const [t, n] of miss) console.log('  MISSING from the ledger: ' + t + ',' + n);
  console.log(miss.length ? 'HORDE EYES LEDGER FAIL' : 'HORDE EYES LEDGER OK (' + want.length + ' assets)');
  process.exit(miss.length ? 1 : 0);
}

// ---- the contract + the mutants ----------------------------------------------------------------------------------------
const base = sources();
const errs = check(base);
if (errs.length) {
  for (const x of errs) console.log('  FAIL ' + x);
  console.log('HORDE EYES FAIL (' + errs.length + ')');
  process.exit(1);
}
const MUTANTS = [
  ['the level override is gone', s => ({ ...s, csc: s.csc.replace(/level\._override_eye_fx = TOD_EYE_FX_HORDE;/, '') })],
  ['init is never called', s => ({ ...s, entry: s.entry.replace(/\ttod_eye_glow::init\(\);\n/, '') })],
  ['init runs before zm_usermap (the stock orange would win a later reset)', s => ({ ...s,
    entry: s.entry.replace(/\ttod_eye_glow::init\(\);\n/, '').replace('\tzm_usermap::main();', '\ttod_eye_glow::init();\n\tzm_usermap::main();') })],
  ['the golden body name drifts', s => ({ ...s, gsh: s.gsh.replace('"tod_golden_zombie_body"', '"tod_golden_zombie_body2"') })],
  ['the zone drops the red effect', s => ({ ...s, zone: s.zone.replace(/^fx,tod\/cyber\/fx_tod_charcoal_eye_glow_red\n/m, '') })],
  ['every zombie turns gold', s => ({ ...s, csc: s.csc.replace(/if \( model == TOD_EYE_GOLDEN_BODY \)\n\t\treturn TOD_EYE_FX_GOLDEN;\n\treturn undefined;/,
    'if ( model == TOD_EYE_GOLDEN_BODY )\n\t\treturn TOD_EYE_FX_GOLDEN;\n\treturn TOD_EYE_FX_GOLDEN;') })],
  ['the hook is stolen, not chained', s => ({ ...s, csc: s.csc.replace(/\tif \( isdefined\( level\.tod_eye_prev_cb \) \)\n\t\tself \[\[ level\.tod_eye_prev_cb \]\][^\n]*\n/, '') })],
  ['the red is re-lit before it is put out', s => ({ ...s, csc: s.csc
    .replace('self zm::deleteZombieEyes( localClientNum );', '@@DEL@@').replace('self zm::createZombieEyes( localClientNum );', 'self zm::deleteZombieEyes( localClientNum );')
    .replace('@@DEL@@', 'self zm::createZombieEyes( localClientNum );') })],
  ['a peer script also takes the hook', s => ({ ...s, others: [...s.others, ['scripts/zm/peer.csc', 'function f() { level.zombie_eyes_clientfield_cb_additional = &g; }']] })],
];
let caught = 0;
for (const [name, mut] of MUTANTS) {
  const m = mut(base);
  const changed = JSON.stringify(m) !== JSON.stringify(base);
  const hit = changed && check(m).length > 0;
  if (hit) caught++; else console.log('  MUTANT SURVIVED' + (changed ? '' : ' (did not apply)') + ': ' + name);
}
if (caught !== MUTANTS.length) { console.log('HORDE EYES FAIL (a mutant survived)'); process.exit(1); }
console.log('HORDE EYES OK (names in lockstep, zone + entry wired, chained hook, golden re-light, gsc_eval chooser, '
  + caught + '/' + MUTANTS.length + ' mutants caught)' + (ROOT !== REPO ? ' [root ' + path.relative(REPO, ROOT) + ']' : ''));
