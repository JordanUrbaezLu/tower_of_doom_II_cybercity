// tools/fxgen/elites/test_elite_fx.js - THE ELITES' EFFECTS gate (PK26, 2026-10-05).
//   node tools/fxgen/elites/test_elite_fx.js [--root DIR]      (DIR: a tree laid out like the repo; default the repo)
// Proves, from the SHIPPING files:
//   A  the generated effects are fresh and valid (make_fx.py --check + --selftest), the sounds are fresh (make_sounds.py
//      --check), every effect the module precaches is generated, zoned and <= 63 characters, and the module's LOCKSTEP
//      clock is the one the generator built against;
//   B  the lane: every effect rides a tag_origin carrier (no bare PlayFX, no PlayFXOnTag on an actor), every carrier dies
//      (a deadline, the actor's death, a world pause, the failsafe), the linked carriers are capped and counted back,
//      the cue rides a script_origin (never PlaySoundAtPosition), the logger is console-only and dev / diag gated;
//   C  the hooks sit at the real moments: the Doppelghast's charge starts with the squib, follows the torso inside the
//      existing loop and ends at the blast, the blast lands with the damage, the juke smear right after the juke clip
//      starts, the claw right after the swipe clip starts; the Mangler's ground thud, break-up, hide and delete in order;
//      both modules #using the module and the module is zoned;
//   D  the claw's bone is the measured one and the shipping robot model carries it (when the private tools root exists);
//   E  negative controls: a removed hook, a bare PlayFX, an unzoned effect, a hook before the clip, a forever loop in a
//      one-shot effect are each caught.
'use strict';
const fs = require('fs'), path = require('path'), cp = require('child_process');
const argRoot = process.argv.indexOf('--root');
const root = argRoot > 0 ? path.resolve(process.argv[argRoot + 1]) : path.resolve(__dirname, '..', '..', '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const exists = p => fs.existsSync(path.join(root, p));
let checks = 0, fails = 0;
const ok = (v, m) => { if (v) checks++; else { fails++; console.log('  FAIL ' + m); } };
const S = 'scripts/zm/zm_tod2_cybercity/';
const MOD = read(S + '_tod_elite_fx.gsc');
const DOP = read(S + '_tod_doppelghast.gsc');
const MANG = read(S + '_tod_mangler.gsc');
const ZONE = read('zone_source/zm_tod2_cybercity.zone');
const zoneHas = line => ZONE.split(/\r?\n/).some(l => l.replace(/\s*\/\/.*$/, '').trim() === line);
const noComments = s => s.replace(/\/\/[^\n]*/g, '');
const body = (src, name) => { const m = src.match(new RegExp('function ' + name + '\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\}')); return m ? m[1] : ''; };
const defs = src => { const d = {}; for (const m of src.matchAll(/#define\s+(TOD_\w+)\s+("[^"]*"|-?[\d.]+)/g)) d[m[1]] = m[2].replace(/^"|"$/g, ''); return d; };
const D = defs(MOD);

// ---- A. generated + zoned ----------------------------------------------------------------------------------------
console.log('A. the effects and the sounds');
{
  const py = (args) => cp.spawnSync('python', ['-B', path.join(__dirname, ...args.slice(0, 1)), ...args.slice(1), '--out-root', root], { encoding: 'utf8' });
  let r = py(['make_fx.py', '--check']);
  ok(r.status === 0, 'make_fx.py --check: ' + (r.stdout + r.stderr).trim().split('\n').pop());
  r = py(['make_fx.py', '--selftest']);
  ok(r.status === 0, 'make_fx.py --selftest: ' + (r.stdout + r.stderr).trim().split('\n').pop());
  r = py(['make_sounds.py', '--check']);
  ok(r.status === 0, 'make_sounds.py --check: ' + (r.stdout + r.stderr).trim().split('\n').pop());
  const pre = [...MOD.matchAll(/#precache\( "fx", "([^"]+)" \);/g)].map(m => m[1]);
  ok(pre.length === 5, 'the module precaches the five effects (' + pre.length + ')');
  for (const fx of pre) {
    ok(fx.startsWith('tod/elites/') && fx.length <= 63, 'a map-owned path <= 63 chars: ' + fx);
    ok(exists('share/raw/fx/' + fx + '.efx'), 'generated: ' + fx);
    ok(zoneHas('fx,' + fx), 'zoned: fx,' + fx);
    ok(Object.values(D).includes(fx), 'a #define names it: ' + fx);
  }
  const disk = fs.existsSync(path.join(root, 'share/raw/fx/tod/elites')) ? fs.readdirSync(path.join(root, 'share/raw/fx/tod/elites')).filter(f => f.endsWith('.efx')) : [];
  ok(disk.length === 5 && disk.every(f => pre.includes('tod/elites/' + f.slice(0, -4))), 'no stray effect in tod/elites (' + disk.join(' ') + ')');
  for (const k of ['TOD_ELITE_FX_CHARGE_MS', 'TOD_ELITE_FX_JUKE_ON_MS', 'TOD_ELITE_FX_JUKE_SECS', 'TOD_ELITE_FX_CLAW_SECS', 'TOD_ELITE_FX_CLAW_TAG',
                   'TOD_ELITE_FX_MANGLER_SECS', 'TOD_ELITE_FX_BLAST_SECS', 'TOD_ELITE_FX_LINKED_MAX'])
    ok(D[k] !== undefined, 'LOCKSTEP define present: ' + k);
  // the charge spans the squib (+0.1 s) to the blast (+3.0 s) of death_burst
  const db = body(DOP, 'death_burst');
  const blastMs = Number((db.match(/while \( GetTime\(\) - started < (\d+) \)/) || [])[1]);
  const squibS = Number((db.match(/started = GetTime\(\);\s*wait ([\d.]+);/) || [])[1]);
  ok(blastMs > 0 && squibS > 0 && Math.abs(blastMs - squibS * 1000 - Number(D.TOD_ELITE_FX_CHARGE_MS)) < 1,
     `TOD_ELITE_FX_CHARGE_MS (${D.TOD_ELITE_FX_CHARGE_MS}) = the blast (${blastMs}) - the squib (${squibS * 1000})`);
  const csv = exists('sound/aliases/tod_elite_fx.csv') ? read('sound/aliases/tod_elite_fx.csv') : '';
  for (const a of [D.TOD_ELITE_FX_CHARGE_ALIAS, defs(MANG).TOD_MANGLER_GROUND_ALIAS, defs(MANG).TOD_MANGLER_IMPACT_ALIAS])
    ok(a && new RegExp('^' + a + ',[^\\n]*,3d,', 'mi').test(csv), 'a 3D row in tod_elite_fx.csv: ' + a);
  {
    const rows = csv.split(/\r?\n/).filter(Boolean), head = (rows[0] || '').split(','), iP = head.indexOf('Pauseable'), iC = head.indexOf('ContextType');
    ok(iP > 0 && rows.slice(1).every(r => r.split(',')[iP] !== 'yes' && !r.split(',')[iC]), 'one-shot cues: never Pauseable, no sound context');
  }
  const szc = JSON.parse(read('sound/zoneconfig/zm_tod2_cybercity.szc'));
  ok(szc.Sources.some(s => s.Type === 'ALIAS' && s.Filename === 'tod_elite_fx.csv'), 'the .szc loads tod_elite_fx.csv');
}

// ---- B. the lane ---------------------------------------------------------------------------------------------------
console.log('B. the lane');
function laneProblems(src) {
  const s = noComments(src), bad = [];
  if (/(^|[^\w:])PlayFX\s*\(/m.test(s)) bad.push('a bare server PlayFX');
  for (const m of s.matchAll(/PlayFXOnTag\(\s*[^,]+,\s*([^,]+),/g)) if (m[1].trim() !== 'self') bad.push('PlayFXOnTag on ' + m[1].trim());
  if (!/function carrier_play\( effect \)[\s\S]*?self endon\( "death" \);\s*wait 0\.05;[^\n]*\n\s*PlayFXOnTag\( effect, self, "tag_origin" \);/.test(s)) bad.push('the carrier does not wait a frame before its effect');
  if (/PlaySoundAtPosition/.test(s)) bad.push('PlaySoundAtPosition (silent for a custom alias here)');
  return bad;
}
{
  ok(laneProblems(MOD).length === 0, 'carriers only, one frame before the effect, no silent lane: ' + laneProblems(MOD).join('; '));
  ok(/host SetModel\( "tag_origin" \);/.test(MOD) && (MOD.match(/Spawn\( "script_model"/g) || []).length === 2, 'two carrier spawns, both tag_origin (the charge, the linked)');
  const lw = body(MOD, 'linked_watch');
  ok(/level endon\( "end_game" \);/.test(lw) && /!isdefined\( actor \) \|\| !IsAlive\( actor \)/.test(lw) && /IS_TRUE\( level\.tod_upgrade_pause \)/.test(lw)
     && /level\.tod_elite_fx_live--;/.test(lw) && /host Delete\(\);/.test(lw), 'a linked carrier dies at its deadline, on death or a pause, and gives its slot back');
  const lk = body(MOD, 'linked');
  ok(/level\.tod_elite_fx_live >= TOD_ELITE_FX_LINKED_MAX/.test(lk) && /level\.tod_elite_fx_live\+\+;/.test(lk) && /level thread linked_watch\(/.test(lk), 'the linked carriers are capped and counted (the watcher is level-owned)');
  ok(/GetTagOrigin\( tag \);\s*if \( !isdefined\( org \) \)/.test(lk) && lk.indexOf('GetTagOrigin( tag )') < lk.indexOf('LinkTo('), 'a missing bone is refused before any LinkTo');
  ok(/host thread carrier_failsafe\(/.test(body(MOD, 'charge_start')) && /host Delete\(\);/.test(body(MOD, 'charge_end')), 'the charge carrier ends at the blast, with a failsafe');
  ok(/tod_ability_fx::burst_at\( TOD_ELITE_FX_BLAST, floor, TOD_ELITE_FX_UP, TOD_ELITE_FX_BLAST_SECS \);/.test(MOD)
     && /tod_ability_fx::burst_at\( TOD_ELITE_FX_MANGLER, org, TOD_ELITE_FX_UP, TOD_ELITE_FX_MANGLER_SECS \);/.test(MOD), 'the world one-shots go through the one owner (burst_at), up-facing');
  ok(/#define TOD_ELITE_FX_UP\s+\( -90, 0, 0 \)/.test(MOD) && /host\.angles = TOD_ELITE_FX_UP;/.test(MOD), 'the impact frame (+X up) on every up-facing carrier');
  ok(/function dev_log\( msg \)\s*\{\s*if \( !\( IS_TRUE\( level\.tod_dev \) \|\| IS_TRUE\( level\.tod_diag \) \) \)\s*return;\s*line = [^\n]+\n\s*\/#\s*PrintLn\( line \);\s*#\//.test(MOD), 'the logger: dev / diag gated, the string built outside /# #/');
  ok(!/IPrintLn|iprintln/.test(MOD), 'nothing on screen');
  ok(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_ability_fx;/.test(MOD) && !/#using scripts\\zm\\zm_tod2_cybercity\\_tod_(?!ability_fx)/.test(noComments(MOD)), 'a leaf: it imports only the burst owner');
  ok(zoneHas('scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_elite_fx.gsc'), 'zoned: the module');
}

// ---- C. the hooks ---------------------------------------------------------------------------------------------------
console.log('C. the hooks');
function doppelProblems(src) {
  const bad = [];
  if (!/#using scripts\\zm\\zm_tod2_cybercity\\_tod_elite_fx;/.test(src)) bad.push('no #using');
  const db = body(src, 'death_burst');
  const iSquib = db.indexOf('fx_host( "blood/fx_blood_neck_spray_zmb"'), iCharge = db.indexOf('tod_elite_fx::charge_start( origin, generation );');
  const iLoop = db.indexOf('while ( GetTime() - started <'), iFollow = db.indexOf('tod_elite_fx::charge_follow( charge, origin );');
  const iEnd = db.indexOf('tod_elite_fx::charge_end( charge, generation );'), iBlast = db.indexOf('tod_elite_fx::blast( origin, actor, generation );');
  const iDamage = db.indexOf('DoDamage( TOD_DOPPEL_DEATH_DAMAGE');
  if (!(iSquib >= 0 && iCharge > iSquib && iLoop > iCharge)) bad.push('the charge does not start with the squib, before the torso loop');
  const loop = iLoop >= 0 ? db.slice(iLoop, db.indexOf('}', db.indexOf('wait 0.05;', iLoop))) : '';
  if (!(iFollow > iLoop && loop.includes('tod_elite_fx::charge_follow( charge, origin );'))) bad.push('the charge does not follow the torso inside the loop');
  if (!(iEnd > iFollow && iBlast > iEnd && iDamage > iBlast)) bad.push('the charge does not end at the blast / the blast is not drawn before the damage');
  if (/LinkTo\(/.test(db)) bad.push('something links to the (client-only) ragdoll');
  const pj = body(src, 'play_juke'), iAnim = pj.indexOf('self AnimScripted('), iJuke = pj.indexOf('tod_elite_fx::juke( self );'), iLoopJ = pj.indexOf('while ( GetTime() - started');
  if (!(iAnim >= 0 && iJuke > iAnim && iJuke < iLoopJ)) bad.push('the juke smear is not hooked right after the juke clip starts');
  const at = body(src, 'attacks'), iSwing = at.indexOf('self AnimScripted( "note_notify", self.origin, angles, attack_anim );'), iClaw = at.indexOf('tod_elite_fx::claw( self );'), iHit = at.indexOf('wait hit_time;');
  if (!(iSwing >= 0 && iClaw > iSwing && iClaw < iHit)) bad.push('the claw is not hooked right after the swipe clip starts');
  return bad;
}
function manglerProblems(src) {
  const bad = [];
  if (!/#using scripts\\zm\\zm_tod2_cybercity\\_tod_elite_fx;/.test(src)) bad.push('no #using');
  const cc = body(src, 'corpse_cleanup');
  const order = ['wait TOD_MANGLER_GROUND_SECS;', 'tod_bo6_audio::sound_at( TOD_MANGLER_GROUND_ALIAS', 'wait TOD_MANGLER_BURST_SECS - TOD_MANGLER_GROUND_SECS;',
                 'GetTagOrigin( "j_spine4" )', 'tod_elite_fx::mangler_burst( torso, generation );', 'tod_bo6_audio::sound_at( TOD_MANGLER_IMPACT_ALIAS, torso',
                 'wait TOD_MANGLER_HIDE_SECS;', 'self Hide();', 'wait TOD_MANGLER_GONE_SECS;', 'self Delete();'];
  let at = -1;
  for (const s of order) { const i = cc.indexOf(s, at + 1); if (i < 0) { bad.push('corpse_cleanup lacks / misorders: ' + s); break; } at = i; }
  const d = defs(src), sum = Number(d.TOD_MANGLER_BURST_SECS) + Number(d.TOD_MANGLER_HIDE_SECS) + Number(d.TOD_MANGLER_GONE_SECS);
  if (!(Number(d.TOD_MANGLER_GROUND_SECS) < Number(d.TOD_MANGLER_BURST_SECS) && Math.abs(Number(d.TOD_MANGLER_BURST_SECS) - 66 / 30) < 0.05 && sum <= 3.5))
    bad.push('the timeline: the thud before the burst at the clip end (66 frames), the body gone within 3.5 s');
  return bad;
}
{
  ok(doppelProblems(DOP).length === 0, '_tod_doppelghast: ' + (doppelProblems(DOP).join('; ') || 'charge / blast / juke / claw at their moments'));
  ok(manglerProblems(MANG).length === 0, '_tod_mangler: ' + (manglerProblems(MANG).join('; ') || 'thud, break-up, hide, delete in order'));
  ok(/blood\/fx_blood_neck_spray_zmb/.test(DOP) && /blood\/fx_blood_impact_exp_body_lg_zmb/.test(DOP), 'the stock squib and the gore burst still play (the blast adds to them)');
}

// ---- D. the claw's bone ----------------------------------------------------------------------------------------------
console.log('D. the claw bone');
{
  const tag = D.TOD_ELITE_FX_CLAW_TAG;
  ok(/^bone_[0-9a-f]+$|^j_\w+$/.test(tag || ''), 'the claw tag is a bone name: ' + tag);
  const robot = 'C:/BO3Tools/TOD2Cybercity/model_export/tod_cyber_elites/tod_doppelgast_black_robot.XMODEL_BIN';
  if (fs.existsSync(robot)) ok(fs.readFileSync(robot).includes(Buffer.from(tag)), 'the shipping robot model carries the claw bone ' + tag);
  else console.log('  (no private tools root here: the robot model check is skipped)');
  ok(/"tod_doppelgast_black_robot"/.test(DOP), 'the Doppelghast still wears the robot model the bone was checked on');
}

// ---- E. negative controls ----------------------------------------------------------------------------------------------
console.log('E. negative controls');
{
  ok(doppelProblems(DOP.replace('tod_elite_fx::claw( self );', '')).length > 0, 'NEGATIVE: a removed claw hook is caught');
  ok(doppelProblems(DOP.replace('\t\ttod_elite_fx::charge_follow( charge, origin );\n', '')).length > 0, 'NEGATIVE: a charge that stops following the torso is caught');
  const early = DOP.replace(/(\t)(self AnimScripted\( "note_notify", origin, angles, attack_anim, "normal", undefined, 1, 0\.1 \);)/, '$1tod_elite_fx::juke( self );\n$1$2')
                   .replace(/\n\ttod_elite_fx::juke\( self \);   \/\/ PK26[^\n]*/, '');
  ok(early !== DOP && doppelProblems(early).length > 0, 'NEGATIVE: a juke hook before the clip starts is caught');
  ok(manglerProblems(MANG.replace('    self Hide();\n', '')).length > 0, 'NEGATIVE: a Mangler that never hides is caught');
  ok(laneProblems(MOD + '\nfunction bad( org ) { PlayFX( TOD_ELITE_FX_BLAST, org ); }\n').length > 0, 'NEGATIVE: a bare PlayFX is caught');
  ok(laneProblems(MOD + '\nfunction bad( a ) { PlayFXOnTag( TOD_ELITE_FX_CLAW, a, "j_spine4" ); }\n').length > 0, 'NEGATIVE: an effect played on an actor is caught');
  const unzoned = ZONE.split(/\r?\n/).filter(l => !l.startsWith('fx,tod/elites/fx_tod_doppel_claw')).join('\n');
  ok(!unzoned.split('\n').some(l => l.trim() === 'fx,tod/elites/fx_tod_doppel_claw'), 'NEGATIVE: an unzoned effect is caught by the zone check');
}

console.log(`\nELITE FX: ${checks} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);
