'use strict';
// THE MANGLER'S VOICE + THE MACHINE MUSIC (wave 2 / W2F, 2026-10-05) - the shipping rules of _tod_bo6_audio.gsc run
// through tools/sky_ships/gsc_eval.js (never a copy), plus the wiring every moment hangs on.
//
// The Mangler had no voice at all (watch_damage returned for it). It now speaks at BO6's own moments: an arrival roar,
// a grunt on the swing (BO6 AIVox@vox_melee, frame 5), a bellow as the cannon fires (AIVox@vox_shoot, frame 58 - before
// the frame-61 shot), the vox_berserk roar the first time it is beaten to half health, pain grunts on a gap, a growl
// while it hunts and a dying roar that outlives the corpse. This proves, from the shipping functions:
//   - mangler_pain_pick: ONE berserk roar per Mangler (even mid-attack), pain never mid-attack, never inside the gap,
//     never on top of its own last voice, nothing on the killing blow or a bad health read;
//   - mangler_amb_ready / mangler_last_vox: the growl waits for the attack, its own voice and the map-wide gate, and
//     only the Mangler's voices count (a Doppelghast's scream on the same entity table never blocks it);
//   - a simulated 30 s fight (hits at 8 / s from full health to dead, two melee windows): exactly one roar, pains
//     at least TOD_MANGLER_PAIN_GAP_MIN_MS apart, none inside an attack window;
//   - the frames land in order inside their clips (the grunt before the melee hit, the bellow before the shot);
//   - the wiring: attach / melee / cannon / death / pain watch call the right names, the death voice rides a carrier
//     (sound_at), the old bail-out is gone, every emitted mangler vox has its row in sound/aliases/tod_mangler_vox.csv
//     and every row is emitted, both perk machines carry their own music and PhD no longer borrows Mule Kick's.
// Negative controls (the shipping text broken three ways) must FAIL the same checks.
//   node tools/original_rips/test_original_rips.js [--root DIR]
const fs = require('fs'), path = require('path');
const argRoot = process.argv.indexOf('--root');
const root = argRoot > 0 ? path.resolve(process.argv[argRoot + 1]) : path.resolve(__dirname, '..', '..');
const { gscLoad } = require(path.join(__dirname, '..', 'sky_ships', 'gsc_eval.js'));
const MOD = path.join(root, 'scripts', 'zm', 'zm_tod2_cybercity');
const read = p => fs.readFileSync(p, 'utf8');
const SRC = read(path.join(MOD, '_tod_bo6_audio.gsc'));
const MANGLER = read(path.join(MOD, '_tod_mangler.gsc'));
const defsOf = text => Object.fromEntries([...text.matchAll(/^#define\s+(TOD_\w+)\s+(-?[\d.]+)\b/gm)].map(m => [m[1], m[2]]));
const defs = defsOf(SRC);

let checks = 0, fails = 0;
const ok = (c, m) => { checks++; if (!c) { fails++; console.log('  FAIL ' + m); } };
const code = t => t.replace(/\/\/[^\n]*/g, '');

// ---- the defines ------------------------------------------------------------------------------------------------
const D = k => +defs[k];
ok(D('TOD_MANGLER_VOX_MELEE_F') === 5 && D('TOD_MANGLER_VOX_SHOOT_F') === 58, 'the AIVox frames: vox_melee 5, vox_shoot 58');
ok(D('TOD_MANGLER_BERSERK_FRAC') > 0 && D('TOD_MANGLER_BERSERK_FRAC') < 1, 'the berserk threshold is a fraction of health');
ok(D('TOD_MANGLER_PAIN_GAP_MIN_MS') >= 1000 && D('TOD_MANGLER_PAIN_GAP_MAX_MS') > D('TOD_MANGLER_PAIN_GAP_MIN_MS'), 'the pain gap is a real range (>= 1 s)');
ok(D('TOD_MANGLER_VOX_GAP_MS') > 0 && D('TOD_MANGLER_AMB_MIN_S') > 0 && D('TOD_MANGLER_AMB_MAX_S') > D('TOD_MANGLER_AMB_MIN_S'), 'the voice gap and the growl cadence are set');
ok(D('TOD_MANGLER_AMB_GLOBAL_MS') > 0, 'the map-wide growl gate is set');
// the frames sit inside their clips, before the moment they voice
const fps = D('TOD_BO6_FPS');
const windup = +((MANGLER.match(/windup = ([\d.]+) \/ self\.tod_mangler_cannon_rate;/) || [])[1]);
const meleeHit = +((MANGLER.match(/wait ([\d.]+); \/\/ BO6 hit_melee marker/) || [])[1]);
ok(fps === 30 && windup > 0 && D('TOD_MANGLER_VOX_SHOOT_F') / fps < windup, 'the bellow (frame ' + D('TOD_MANGLER_VOX_SHOOT_F') + ') lands before the cannon fires (' + windup + ' s at 1x)');
ok(windup - D('TOD_MANGLER_VOX_SHOOT_F') / fps <= 0.2, 'the bellow is within 0.2 s of the shot (it voices the shot, not the windup)');
ok(meleeHit > 0 && D('TOD_MANGLER_VOX_MELEE_F') / fps < meleeHit, 'the swing grunt (frame ' + D('TOD_MANGLER_VOX_MELEE_F') + ') lands before the melee hit (' + meleeHit + ' s)');

// ---- the pure functions, shipping text ----------------------------------------------------------------------------
function load(text) {
  const g = gscLoad([['tod_bo6_audio', text]], defsOf(text));
  return {
    pick: (h, mx, b, a, now, next, last) => g.call('mangler_pain_pick', [h, mx, b, a, now, next, last]),
    amb: (a, now, last, glob) => !!g.call('mangler_amb_ready', [a, now, last, glob]),
    lastVox: actor => g.call('mangler_last_vox', [actor]),
  };
}

function verify(G, label) {
  const bad = [];
  const P = (...a) => G.pick(...a);
  const gap = D('TOD_MANGLER_VOX_GAP_MS');
  // single hits
  if (P(900, 1000, false, false, 10000, 0, undefined) !== 'pain') bad.push(label + ': a first hit at full health is not a pain grunt');
  if (P(500, 1000, false, false, 10000, 0, undefined) !== 'roar') bad.push(label + ': the first hit to half health is not the berserk roar');
  if (P(400, 1000, false, true, 10000, 99999, 9990) !== 'roar') bad.push(label + ': the berserk roar is withheld mid-attack / in the gap (it is the moment the damage lands)');
  if (P(400, 1000, true, false, 10000, 0, undefined) !== 'pain') bad.push(label + ': after the roar a hit under half is not a pain grunt');
  if (P(900, 1000, false, true, 10000, 0, undefined) !== '') bad.push(label + ': a pain grunt plays mid-attack');
  if (P(900, 1000, false, false, 10000, 10500, undefined) !== '') bad.push(label + ': a pain grunt plays inside the gap');
  if (P(900, 1000, false, false, 10000, 0, 10000 - gap + 1) !== '') bad.push(label + ': a pain grunt plays on top of its own last voice');
  if (P(900, 1000, false, false, 10000, 0, 10000 - gap - 1) !== 'pain') bad.push(label + ': a pain grunt is withheld after the voice gap passed');
  if (P(0, 1000, false, false, 10000, 0, undefined) !== '') bad.push(label + ': the killing blow voices a pain (the death voice owns it)');
  if (P(-5, 1000, false, false, 10000, 0, undefined) !== '') bad.push(label + ': a negative-health hit voices');
  if (P(500, 0, false, false, 10000, 0, undefined) !== '' || P(500, undefined, false, false, 10000, 0, undefined) !== '') bad.push(label + ': a bad maxhealth voices');
  // the growl gate
  if (G.amb(true, 10000, undefined, undefined)) bad.push(label + ': it growls mid-attack');
  if (G.amb(false, 10000, 10000 - gap + 1, undefined)) bad.push(label + ': it growls on top of its own voice');
  if (G.amb(false, 10000, undefined, 10001)) bad.push(label + ': the map-wide growl gate is ignored');
  if (!G.amb(false, 10000, 10000 - gap - 1, 10000)) bad.push(label + ': a clear growl is refused');
  // last vox: the Mangler's voices only
  if (G.lastVox({}) !== undefined) bad.push(label + ': a silent Mangler has a last voice');
  if (G.lastVox({ tod_bo6_audio_last: { vox_ai_mangler_pain: 300, vox_ai_mangler_roar: 700, vox_ai_mangler_melee: 500 } }) !== 700) bad.push(label + ': the last voice is not the latest of its voices');
  if (G.lastVox({ tod_bo6_audio_last: { vox_ai_ghoul_roar: 900, fly_ai_mangler_spawn: 950 } }) !== undefined) bad.push(label + ': a non-voice cue counts as its voice');
  if (G.lastVox({ tod_bo6_audio_last: { vox_ai_mangler_shoot: 1200, vox_ai_mangler_ambience: 1100 } }) !== 1200) bad.push(label + ': the bellow is not counted as a voice');
  // a simulated fight: hits at 8 / s for 30 s, health 1000 -> 0, attack windows 6-8 s and 18-20 s; the watch's loop
  // (structure pinned below) around the shipping pick
  let seed = 12345;
  const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  const actor = { tod_bo6_audio_last: {} };
  let health = 1000, berserk = false, nextPain = 0;
  const voices = [];
  for (let now = 125; now <= 30000 && health > 0; now += 125) {
    health -= 4.3;
    const attacking = (now >= 6000 && now < 8000) || (now >= 18000 && now < 20000);
    const pick = P(Math.round(health), 1000, berserk, attacking, now, nextPain, G.lastVox(actor));
    if (pick === 'roar') {
      berserk = true;
      nextPain = now + D('TOD_MANGLER_PAIN_GAP_MAX_MS');
      actor.tod_bo6_audio_last.vox_ai_mangler_roar = now;
      voices.push({ now, v: 'roar', attacking });
    } else if (pick === 'pain') {
      nextPain = now + D('TOD_MANGLER_PAIN_GAP_MIN_MS') + Math.floor(rnd() * (D('TOD_MANGLER_PAIN_GAP_MAX_MS') - D('TOD_MANGLER_PAIN_GAP_MIN_MS')));
      actor.tod_bo6_audio_last.vox_ai_mangler_pain = now;
      voices.push({ now, v: 'pain', attacking });
    }
  }
  const roars = voices.filter(x => x.v === 'roar'), pains = voices.filter(x => x.v === 'pain');
  if (roars.length !== 1) bad.push(label + ': the fight drew ' + roars.length + ' berserk roars (want 1)');
  if (pains.some(x => x.attacking)) bad.push(label + ': a pain grunt played inside an attack window');
  for (let i = 1; i < voices.length; i++)
    if (voices[i].now - voices[i - 1].now < D('TOD_MANGLER_PAIN_GAP_MIN_MS') && voices[i].v === 'pain') { bad.push(label + ': two voices ' + (voices[i].now - voices[i - 1].now) + ' ms apart'); break; }
  if (pains.length < 6 || pains.length > 20) bad.push(label + ': the fight drew ' + pains.length + ' pain grunts (want a steady 6-20 over 30 s, not silence or a wall)');
  return bad;
}

const shipping = verify(load(SRC), 'shipping');
for (const b of shipping) ok(false, b);
ok(shipping.length === 0, 'the shipping mangler_pain_pick / mangler_amb_ready / mangler_last_vox: one roar, spaced pains, none mid-attack');

// negative controls: the shipping text broken three ways must fail the same verification
const noLatch = SRC.replace('if ( !berserked && health <= maxhealth * TOD_MANGLER_BERSERK_FRAC ) return "roar";', 'if ( health <= maxhealth * TOD_MANGLER_BERSERK_FRAC ) return "roar";');
ok(noLatch !== SRC && verify(load(noLatch), 'no-latch').length > 0, 'negative control: without the berserk latch it roars on every hit under half');
const noAttack = SRC.replace(/(function mangler_pain_pick[\s\S]*?)if \( attacking \) return "";/, '$1');
ok(noAttack !== SRC && verify(load(noAttack), 'no-attack-guard').length > 0, 'negative control: without the attack guard a grunt plays mid-swing');
const noGap = SRC.replace('if ( now < next_pain_ms ) return "";', '');
ok(noGap !== SRC && verify(load(noGap), 'no-gap').length > 0, 'negative control: without the pain gap the grunts wall the mix');

// ---- the wiring -----------------------------------------------------------------------------------------------------
const C = code(SRC);
const need = [
  ['attach: the arrival roar', /actor thread timed\( "vox_ai_mangler_roar", TOD_MANGLER_SPAWN_ROAR_F, 1, "spawn_roar" \);/],
  ['attach: the growl cadence', /if \( TOD_MANGLER_AMB_MIN_S > 0 \) actor thread mangler_ambience_cadence\(\);/],
  ['melee: the swing grunt on its frame', /actor thread timed\( "vox_ai_mangler_melee", TOD_MANGLER_VOX_MELEE_F, 1, "melee_timed" \);/],
  ['cannon: the bellow on its frame at the clip rate', /actor thread timed\( "vox_ai_mangler_shoot", TOD_MANGLER_VOX_SHOOT_F, rate, "cannon_timed" \);/],
  ['watch_damage hands the Mangler to its pain watch', /if \( kind == "mangler" \)\s*\{\s*self mangler_pain_watch\(\);\s*return;\s*\}/],
  ['death: the dying roar', /emit\( actor, "vox_ai_mangler_death", "death_voice" \);/],
  ['the dying roar rides a carrier', /source_alias == "vox_ai_mangler_death" \)\s*sound_at\( alias, actor\.origin, TOD_BO6_TAIL_SECS \);/],
  ['the pain watch: health, maxhealth, latch, attack, gap, last voice', /mangler_pain_pick\( self\.health, self\.maxhealth, IS_TRUE\( self\.tod_bo6_mangler_berserk \),\s*IS_TRUE\( self\.tod_mangler_attacking \), now, next_pain, mangler_last_vox\( self \) \);/],
  ['the pain watch: the roar sets the latch and the long gap', /self\.tod_bo6_mangler_berserk = true;\s*next_pain = now \+ TOD_MANGLER_PAIN_GAP_MAX_MS;\s*emit\( self, "vox_ai_mangler_roar", "berserk" \);/],
  ['the pain watch: a pain sets a random gap', /next_pain = now \+ RandomIntRange\( TOD_MANGLER_PAIN_GAP_MIN_MS, TOD_MANGLER_PAIN_GAP_MAX_MS \);\s*emit\( self, "vox_ai_mangler_pain", "damage" \);/],
  ['the pain watch ends with the Mangler', /function mangler_pain_watch\(\)\s*\{\s*self endon\( "death" \);\s*level endon\( "end_game" \);/],
  ['the growl cadence: the gate, then the map-wide stamp, then the growl', /if \( !mangler_amb_ready\( IS_TRUE\( self\.tod_mangler_attacking \), now, mangler_last_vox\( self \), level\.tod_bo6_mangler_amb_next_ms \) \) continue;\s*level\.tod_bo6_mangler_amb_next_ms = now \+ TOD_MANGLER_AMB_GLOBAL_MS;\s*emit\( self, "vox_ai_mangler_ambience", "ambience_cadence" \);/],
  ['the growl cadence ends with the Mangler', /function mangler_ambience_cadence\(\)\s*\{\s*self endon\( "death" \);\s*level endon\( "end_game" \);/],
  ['every voice goes through emit (the world-pause refusal)', /function emit\( actor, source_alias, event \)\s*\{\s*if \( !isdefined\( actor \) \|\| IS_TRUE\( level\.tod_upgrade_pause \) \) return;/],
  ['the bank probe lists the new aliases', /"hb_bo6_vox_ai_mangler_roar"[\s\S]*"mus_perk_phd_stinger"/],
];
for (const [what, re] of need) ok(re.test(C), '_tod_bo6_audio: ' + what);
ok(!/if \( kind == "mangler" \) return;/.test(C), 'the old Mangler voice bail-out is gone');
ok(!/PlaySoundAtPosition/i.test(C), 'no PlaySoundAtPosition in the BO6 lane (a custom alias is silent through it)');
// the callers in _tod_mangler.gsc still reach the three public cues and the death
const MC = code(MANGLER);
for (const s of ['tod_bo6_audio::attach( self, "mangler" );', 'tod_bo6_audio::mangler_melee( self );',
                 'tod_bo6_audio::mangler_cannon_windup( self, self.tod_mangler_cannon_rate );', 'tod_bo6_audio::death( self, "mangler" );'])
  ok(MC.includes(s), '_tod_mangler calls ' + s);

// every mangler vox the lane emits has its row, and every row is emitted
const emitted = new Set([...C.matchAll(/"(vox_ai_mangler_[a-z0-9_]+)"/g)].map(m => 'hb_bo6_' + m[1]));
const csvPath = path.join(root, 'sound', 'aliases', 'tod_mangler_vox.csv');
ok(fs.existsSync(csvPath), 'sound/aliases/tod_mangler_vox.csv exists');
if (fs.existsSync(csvPath)) {
  const lines = read(csvPath).split(/\r?\n/).filter(Boolean);
  const hdr = lines[0].split(',');
  const col = k => hdr.indexOf(k);
  const rows = lines.slice(1).map(l => l.split(','));
  const names = new Set(rows.map(r => r[col('Name')]));
  for (const a of emitted) ok(names.has(a), 'row for ' + a);
  for (const n of names) ok(emitted.has(n), n + ' is emitted (no dead row)');
  ok(emitted.size === 6, 'six Mangler voices: roar, melee, shoot, pain, death, ambience (' + emitted.size + ')');
  for (const r of rows) {
    ok(r[col('PanType')] === '3d' && r[col('Looping')] === 'NONLOOPING' && r[col('Template')] === 'UIN_MOD', r[col('Name')] + ' is the BO6 lane row shape (UIN_MOD 3d NONLOOPING)');
    ok(fs.existsSync(path.join(root, 'sound_assets', r[col('FileSpec')].replace(/\\/g, '/'))), 'wav ' + r[col('FileSpec')]);
  }
}

// the machines' own music
const EC = code(read(path.join(MOD, '_tod_perk_electric_cherry.gsc')));
const PHD = code(read(path.join(MOD, '_tod_perk_phd.gsc')));
ok(/function ec_machine_setup\([^)]*\)\s*\{[^}]*use_trigger\.script_sound\s*=\s*"mus_perk_deathperception_jingle";[^}]*use_trigger\.script_label\s*=\s*"mus_perk_deathperception_stinger";/.test(EC), 'Death Perception (ec_machine_setup) sets its BO6 jingle and stinger');
ok(/function phd_machine_setup\([^)]*\)\s*\{[^}]*use_trigger\.script_sound\s*=\s*"mus_perk_phd_jingle";[^}]*use_trigger\.script_label\s*=\s*"mus_perk_phd_stinger";/.test(PHD), 'PhD (phd_machine_setup) sets its BO6 jingle and stinger');
ok(!/mus_perks_mulekick_/.test(PHD), 'PhD no longer plays retired Mule Kick\'s music');
const jcsv = path.join(root, 'sound', 'aliases', 'tod_perk_jingles.csv');
ok(fs.existsSync(jcsv), 'sound/aliases/tod_perk_jingles.csv exists');
if (fs.existsSync(jcsv)) {
  const lines = read(jcsv).split(/\r?\n/).filter(Boolean);
  const hdr = lines[0].split(',');
  const col = k => hdr.indexOf(k);
  const rows = lines.slice(1).map(l => l.split(','));
  const names = rows.map(r => r[col('Name')]).sort();
  ok(JSON.stringify(names) === JSON.stringify(['mus_perk_deathperception_jingle', 'mus_perk_deathperception_stinger', 'mus_perk_phd_jingle', 'mus_perk_phd_stinger']), 'the four machine-music rows, nothing else');
  for (const r of rows) {
    ok(r[col('Storage')] === 'streamed' && r[col('PanType')] === '3d' && r[col('Looping')] === 'nonlooping', r[col('Name')] + ' is the stock perk-jingle row (streamed 3d nonlooping)');
    ok(!r[col('ContextType')] && !r[col('ContextValue')], r[col('Name')] + ' carries no sound context');
  }
}

console.log(fails ? `ORIGINAL RIPS TEST FAILED: ${fails} of ${checks}` :
  `ORIGINAL RIPS TEST OK: ${checks} checks - one berserk roar, spaced pain grunts never mid-attack, gated growls, the frames before their moments, every voice wired and rowed, both machines on their own music, 3 negative controls caught`);
process.exit(fails ? 1 : 0);
