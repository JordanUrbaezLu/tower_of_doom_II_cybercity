// THE SEAL IS HEARD (LT-fix 2026-10-05). The user's 17:33 run sealed the crown 2 s after he landed from the first
// jump, ~6,920 u from the gate: the cue played only AT the gate (zmb_heavy_door_open, DistMax 2000 / 2400 since the
// map defined it), so "THE CROWN SEALS BEHIND YOU" printed in silence. Executes the shipping seal_cue against stubs:
// a player near the gate hears the gate; a far player hears it TOD_FALL_SEAL_CUE_STEP from him toward the crown,
// played to him alone; the alias's reach covers that spot. NEGATIVE CONTROL: the 15:10 lane (the gate only) leaves
// the 17:33 player out of earshot.
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const root = require('path').resolve(__dirname, '..');
const src = fs.readFileSync(root + '/scripts/zm/zm_tod2_cybercity/_tod_fall.gsc', 'utf8');
let checks = 0; const ok = (v, m) => { assert.ok(v, m); checks++; };
function body(name) {
  const clean = src.replace(/\/\/[^\n]*/g, '');
  const st = clean.indexOf('function ' + name + '(');
  assert(st >= 0, 'function ' + name);
  const a = clean.indexOf('{', st); let b = a + 1, d = 1;
  while (d) { if (clean[b] === '{') d++; if (clean[b] === '}') d--; b++; }
  return clean.slice(a + 1, b - 1);
}
const def = n => { const m = new RegExp('#define\\s+' + n + '\\s+("?)([^"\\s]+)\\1').exec(src); assert(m, n); return m[1] ? m[2] : Number(m[2]); };
const NEAR = def('TOD_FALL_SEAL_CUE_NEAR'), STEP = def('TOD_FALL_SEAL_CUE_STEP'), ALIAS = def('TOD_FALL_SEAL_SOUND');
// the alias the map defines (sound/aliases/*.csv): its DistMaxDry decides who can hear a 3D cue
let reach = 0;
{
  const dir = root + '/sound/aliases';
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.csv'))) {
    const rows = fs.readFileSync(dir + '/' + f, 'utf8').split(/\r?\n/);
    const hdr = rows.find(r => /^Name,/.test(r));
    const row = rows.find(r => r.split(',')[0] === ALIAS);
    if (hdr && row) { const h = hdr.split(','), c = row.split(','); reach = Number(c[h.indexOf('DistMaxDry')]); }
  }
}
ok(reach >= 1000, 'the map defines ' + ALIAS + ' with a 3D reach (DistMaxDry ' + reach + ')');
ok(STEP < reach && NEAR <= reach, 'the per-player spot (' + STEP + ' u) and the near-gate radius (' + NEAR + ' u) sit inside that reach');
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]], len = v => Math.hypot(...v);
const mk = players => {
  const e = { gate: [], spots: [], logs: [] };
  Object.assign(e, {
    TOD_FALL_SEAL_SOUND: ALIAS, TOD_FALL_SEAL_CUE_NEAR: NEAR, TOD_FALL_SEAL_CUE_STEP: STEP,
    isdefined: x => x !== undefined && x !== null, isalive: p => !!p && p.alive !== false, int: Math.trunc,
    Distance: (a, b) => len(sub(a, b)), VectorNormalize: v => { const l = len(v) || 1; return v.map(x => x / l); },
    GetPlayers: () => players, SoundGetPlaybackTime: () => 1182, fall_log: m => e.logs.push(m),
    tod_perk_scatter: { play_sound_at_origin: (o, a) => e.gate.push([o, a]), emitter_cleanup: () => {} },
    Spawn: (k, o) => ({ origin: o, PlaySoundToPlayer(a, p) { e.spots.push({ at: o, alias: a, to: p }); } })
  });
  vm.createContext(e);
  const code = body('seal_cue')
    .replace(/foreach\s*\(\s*(\w+)\s+in\s+([^)]+\))\s*\)/g, 'for (const $1 of $2)')
    .replace(/\bp\.origin \+ dir \* TOD_FALL_SEAL_CUE_STEP \+ \( 0, 0, 48 \)/, '[p.origin[0]+dir[0]*TOD_FALL_SEAL_CUE_STEP,p.origin[1]+dir[1]*TOD_FALL_SEAL_CUE_STEP,p.origin[2]+48]')
    .replace(/\( org\[ 0 \] - p\.origin\[ 0 \], org\[ 1 \] - p\.origin\[ 1 \], 0 \)/, '[org[0]-p.origin[0],org[1]-p.origin[1],0]')
    .replace(/\be PlaySoundToPlayer\(/g, 'e.PlaySoundToPlayer(').replace(/\be thread tod_perk_scatter::emitter_cleanup\(/g, 'tod_perk_scatter.emitter_cleanup(')
    .replace(/tod_perk_scatter::/g, 'tod_perk_scatter.').replace(/\bp GetEntityNumber\(\)/g, 'p.n');
  vm.runInContext(`function seal_cue(org){let near,far,d,dir,at,e;${code}}`, e);
  return e;
};
const GATE = [0, 7860, 19392];
{
  const landed = { n: 0, alive: true, origin: [-24, 938, 19393] };        // the 17:33 player, just landed (TOD_JUMPPAD LAND)
  const inHall = { n: 1, alive: true, origin: [0, 7400, 19392] };         // a teammate still by the gate
  const dead = { n: 2, alive: false, origin: [0, 0, 0] };
  const e = mk([landed, inHall, dead]);
  e.seal_cue(GATE);
  ok(e.gate.length === 1 && e.gate[0][1] === ALIAS, 'the gate itself still sounds (anyone in its earshot)');
  ok(e.spots.length === 1 && e.spots[0].to === landed, 'the far player gets his own cue, played to him alone; the near one and the dead one get none');
  const d = len(sub(e.spots[0].at, landed.origin));
  ok(Math.abs(d - Math.hypot(STEP, 48)) < 1 && d < reach, 'it sounds ' + Math.round(d) + ' u from him, inside the alias\'s ' + reach + ' u reach');
  ok(len(sub(e.spots[0].at, GATE)) < len(sub(landed.origin, GATE)), '... on the crown\'s side of him (the slam comes from behind, where the crown is)');
  ok(e.logs.some(l => /^SEAL_CUE player=0 gate_dist=69\d\d /.test(l)) && e.logs.some(l => /^SEAL_CUE alias=zmb_heavy_door_open ms=1182 near_gate=1 far=1$/.test(l)), 'SEAL_CUE logs each lane and the alias length: ' + e.logs.join(' | '));
}
ok(/seal_cue\( org \);/.test(body('seal')) && !/play_sound_at_origin\( org, TOD_FALL_SEAL_SOUND/.test(body('seal')), 'seal() plays the cue through seal_cue');
// NEGATIVE CONTROL: the 15:10 seal played only at the gate - the 17:33 player was out of earshot
{
  const heard = len(sub([-24, 938, 19393], GATE)) <= reach;
  ok(!heard, 'negative control: the gate alone is ' + Math.round(len(sub([-24, 938, 19393], GATE))) + ' u from the 17:33 player, past the ' + reach + ' u reach');
}
console.log(`FALL SEAL CUE PASS: ${checks} checks - the gate, a per-player cue toward the crown for anyone past ${NEAR} u, inside the alias reach, logged; the 15:10 gate-only lane caught.`);
