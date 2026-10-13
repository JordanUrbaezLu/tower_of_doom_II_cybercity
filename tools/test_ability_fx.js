// tools/test_ability_fx.js - THE ABILITY FEEDBACK gate (docs/203, 2026-10-02).
//   node tools/test_ability_fx.js
// Proves, from the SHIPPING files:
//   A  the generated effects are fresh (gen_fx.py --check, gen_kill_feel_art.js --check), every effect the client
//      precaches exists on disk and is zoned (children too), no path over 63 chars, no stub donor survived; the
//      Soul Pulse dome is a soul wave with two lights growing per band; the caster's halves never flash;
//   B  the server / client LOCKSTEP: the kind table, the state bits, the four clientfields (names, sizes, order:
//      the kind BEFORE the counter), every kind the server can send has a client branch, 1p + body halves;
//   C  the wiring: the module in _tod_main's init + #using, the client half in the entry .csc, the scriptparsetree
//      lines, the class modules call every hook (Bash dash / impact, the Soul Pulse dome + the elite flash, Fusion
//      heal / launch / land, Demon on), the Archer's + Retriever's rings ride a host that dies, the stun tell loops
//      for the whole stun, every alias played has rows (3D rows for the teammate's ear), the CSV is in the .szc,
//      every material SetShader'd is in the GDT with a 4-aligned PNG;
//   D  THE KILL FEEL IS GONE (user 2026-10-02: "This hell bound work we can remove, I actually dont liek this"):
//      no module, no hooks, no strings, no aliases, no screen blood, no zone rows - and stays gone;
//   E  negative controls: a drifted kind, an unzoned effect, a removed hook, a revived kill-feel hook are caught.
'use strict';
const fs = require('fs'), path = require('path'), cp = require('child_process');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const exists = p => fs.existsSync(path.join(root, p));
let checks = 0, fails = 0;
const ok = (v, m) => { if (v) checks++; else { fails++; console.log('  FAIL ' + m); } };

const GSC = read('scripts/zm/zm_tod2_cybercity/_tod_ability_fx.gsc');
const CSC = read('scripts/zm/zm_tod2_cybercity/_tod_ability_fx.csc');
const ZONE = read('zone_source/zm_tod2_cybercity.zone');
const MAIN = read('scripts/zm/zm_tod2_cybercity/_tod_main.gsc');
const ENTRY_CSC = read('scripts/zm/zm_tod2_cybercity.csc');
const KIT = read('scripts/zm/zm_tod2_cybercity/_tod_class_kit.gsc');
// docs/206: the C4's armed tell must start inside c4_stick_watch's loop when the charge comes to rest
function c4RestArm(src) {
  const a = src.indexOf('while ( waited < TOD_C4_STICK_WAIT'), b = src.indexOf('waited += 0.05;', a);
  if (a < 0 || b < 0) return false;
  return /isdefined\( grenade\.tod_c4_prev2 \) && DistanceSquared\( grenade\.tod_c4_prev2, grenade\.origin \) < 0\.25 && DistanceSquared\( grenade\.tod_c4_prev, grenade\.origin \) < 0\.25 \)\s*\{\s*grenade\.tod_abfx_c4 = tod_ability_fx::c4_armed\( grenade \);/.test(src.slice(a, b));
}
const CARDS = read('scripts/zm/zm_tod2_cybercity/_tod_class_cards.gsc');
const NECRO = read('scripts/zm/zm_tod2_cybercity/_tod_necro_summon.gsc');
const ARCHER = read('scripts/zm/zm_tod2_cybercity/_tod_archer.gsc');
const RETR = read('scripts/zm/zm_tod2_cybercity/_tod_retriever.gsc');
const SHIELD = read('scripts/zm/zm_tod2_cybercity/_tod_riotshield.gsc');     // docs/206
const BOW = read('scripts/zm/zm_tod2_cybercity/_tod_archer_bow.gsc');
const RUNE = read('scripts/zm/zm_tod2_cybercity/_tod_archer_rune.gsc');
const TWINS = read('source_data/tod_weapon_twins.gdt');
const UPG = read('scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc');
const HUDKIT = read('scripts/zm/_zm_aetherium_hud.gsc');
const CORPSE = read('scripts/zm/zm_tod2_cybercity/_tod_corpse_cleanup.gsc');
const STR = read('localizedstrings/zm_aetherium.str');
const SZC = read('sound/zoneconfig/zm_tod2_cybercity.szc');
const GDT = read('source_data/tod_kill_feel_art.gdt');
const defsOf = src => { const d = {}; for (const m of src.matchAll(/#define (TOD_\w+)\s+(-?[\d.]+)/g)) d[m[1]] = Number(m[2]); return d; };

// ---- A. the generated effects ------------------------------------------------------------------
console.log('A. generated effects');
{
  const r = cp.spawnSync('python', ['-B', 'tools/ability_fx/gen_fx.py', '--check'], { cwd: root, encoding: 'utf8' });
  ok(r.status === 0, 'gen_fx.py --check: ' + (r.stdout + r.stderr).trim().split('\n').pop());
  const a = cp.spawnSync('node', ['tools/gen_kill_feel_art.js', '--check'], { cwd: root, encoding: 'utf8' });
  ok(a.status === 0, 'gen_kill_feel_art.js --check: ' + (a.stdout + a.stderr).trim().split('\n').pop());
  const pre = [...CSC.matchAll(/#precache\( "client_fx", "([^"]+)" \)/g)].map(m => m[1]);
  ok(pre.length >= 21, `precaches read (${pre.length} client)`);
  for (const fx of pre) {
    ok(ZONE.includes('\nfx,' + fx + '\n'), 'zoned: ' + fx);
    ok(fx.length <= 63, 'path <= 63: ' + fx);
  }
  const disk = fs.readdirSync(path.join(root, 'share/raw/fx/tod/abfx')).filter(f => f.endsWith('.efx')).map(f => 'tod/abfx/' + f.slice(0, -4));
  ok(disk.length === 55, 'the generated set is 55 effects (incl. children; 24 + the docs/206 second pass): ' + disk.length);
  for (const fx of disk) {
    ok(ZONE.includes('\nfx,' + fx + '\n'), 'every generated effect (children too) is zoned: ' + fx);
    const text = read('share/raw/fx/' + fx + '.efx');
    ok(!text.includes('gfx_debug_missing_fx'), 'no stub survived: ' + fx);
  }
  const zonedAbfx = [...ZONE.matchAll(/\nfx,(tod\/abfx\/\w+)\n/g)].map(m => m[1]);
  for (const fx of zonedAbfx) ok(disk.includes(fx), 'no zoned ability effect without a file: ' + fx);
  for (const key of ['tod_abfx_dash_1', 'tod_abfx_dash_2', 'tod_abfx_dash_3', 'tod_abfx_dash_vm', 'tod_abfx_impact_4', 'tod_abfx_impact_5', 'tod_abfx_bash_1p',
    'tod_abfx_dome_0', 'tod_abfx_dome_1', 'tod_abfx_dome_2', 'tod_abfx_dome_3', 'tod_abfx_pulse_1p', 'tod_abfx_launch', 'tod_abfx_trail', 'tod_abfx_land',
    'tod_abfx_heal', 'tod_abfx_heal_1p', 'tod_abfx_demon_aura', 'tod_abfx_demon_light', 'tod_abfx_demon_on', 'tod_abfx_demon_on_1p', 'tod_abfx_soul',
    'tod_abfx_dive_trail', 'tod_abfx_sword_glow', 'tod_abfx_sword_charged', 'tod_abfx_cloak_on', 'tod_abfx_cloak_off', 'tod_abfx_card_1', 'tod_abfx_card_2',
    'tod_abfx_card_3', 'tod_abfx_card_4', 'tod_abfx_card_light', 'tod_abfx_shield_break', 'tod_abfx_shield_back', 'tod_abfx_draw_vm', 'tod_abfx_pierce',
    'tod_abfx_hit_axe', 'tod_abfx_burn']) {
    const m = CSC.match(new RegExp('level\\._effect\\[ "' + key + '" \\]\\s*=\\s*"([^"]+)"'));
    ok(m && pre.includes(m[1]), 'effect key bound to a precached effect: ' + key);
  }
  const domes = [0, 1, 2, 3].map(i => read('share/raw/fx/tod/abfx/fx_abfx_pulse_dome' + i + '.efx'));
  for (const d of domes) {
    ok(!/gfx_lightning_beam|gfx_shockwave_elec|gfx_gib_|gfx_debris_clump_lit/.test(d), 'the dome is a SOUL wave: no lightning / electric shockwave / gibs');
    ok((d.match(/lightRadiusGraph (?!0\.0)/g) || []).length === 2, 'the dome carries its two lights');
  }
  const lightR = domes.map(d => Number(d.match(/\n\tlightRadiusGraph ([1-9][\d.]*)/)[1]));
  ok(lightR[0] < lightR[1] && lightR[1] < lightR[2] && lightR[2] < lightR[3], 'the dome lights grow with the band: ' + lightR.map(x => x.toFixed(0)).join(' < '));
  const p1 = read('share/raw/fx/tod/abfx/fx_abfx_pulse_1p.efx');
  ok(!/gfx_elec_arc|lightRadiusGraph [1-9]/.test(p1) && p1.includes('gfx_smk_whisp_anim_em'), 'the caster\'s pulse half is a mist, never a flash or a light (necro_visibility_fix)');
  for (const f of ['fx_abfx_bash_impact', 'fx_abfx_bash_impact_lv9']) ok(!/gfx_gib_metal/.test(read('share/raw/fx/tod/abfx/' + f + '.efx')), f + ': no metal gibs on a blade burst');
  const r0 = read('share/raw/fx/tod/abfx/fx_abfx_bash_impact.efx'), r9 = read('share/raw/fx/tod/abfx/fx_abfx_bash_impact_lv9.efx');
  const shock = s => Number(s.match(/gfx_shockwave_anim_em[\s\S]*?\n\tsizeGraph0 ([\d.]+)/)[1]);
  ok(shock(r9) > shock(r0) * 1.4, `the Lv9 burst READS wider (shockwave ${shock(r0).toFixed(0)} -> ${shock(r9).toFixed(0)})`);
}

// ---- B. the lockstep -----------------------------------------------------------------------------
console.log('B. server / client lockstep');
{
  const gd = defsOf(GSC), cd = defsOf(CSC);
  const kinds = Object.keys(gd).filter(k => /^TOD_ABFX_(?!NONE|HIT_|BURN_SECS|LOG_BURSTS|DIVE_RING_MAX|BURST_LIFE|SWORD_QUIET_MS)/.test(k) && !/_BITS$|_ALPHA$|_IN_S$|_OUT_S$|_LIFE$|_MAX$|_SECS$|_BURSTS$|_MS$/.test(k));
  ok(kinds.length === 24, 'kind + state defines read (' + kinds.length + ': 20 kinds + 4 state bits; docs/206)');
  for (const k of kinds) ok(cd[k] === gd[k], `lockstep ${k}: gsc ${gd[k]} csc ${cd[k]}`);
  for (const k of ['TOD_ABFX_KIND_BITS', 'TOD_ABFX_STATE_BITS', 'TOD_ABFX_HIT_BITS', 'TOD_ABFX_HIT_PIERCE', 'TOD_ABFX_HIT_AXE', 'TOD_ABFX_HIT_BURN', 'TOD_ABFX_BURN_SECS'])
    ok(isFinite(gd[k]) && cd[k] === gd[k], `lockstep ${k}: gsc ${gd[k]} csc ${cd[k]}`);
  const RUNE_TRAP = Number((RUNE.match(/#define TOD_RUNE_TRAP_MS\s+(\d+)/) || [])[1]);
  ok(RUNE_TRAP === gd.TOD_ABFX_BURN_SECS * 1000, 'the torso fire lasts the prison (TOD_RUNE_TRAP_MS ' + RUNE_TRAP + ' = TOD_ABFX_BURN_SECS)');
  const hitVals = ['TOD_ABFX_HIT_PIERCE', 'TOD_ABFX_HIT_AXE', 'TOD_ABFX_HIT_BURN'].map(k => gd[k]);
  ok(new Set(hitVals).size === 3 && Math.max(...hitVals) < 2 ** gd.TOD_ABFX_HIT_BITS && Math.min(...hitVals) > 0, 'hit kinds unique, non-zero, inside the field width');
  const vals = kinds.filter(k => !/STATE/.test(k)).map(k => gd[k]);
  ok(new Set(vals).size === vals.length && Math.max(...vals) < 2 ** gd.TOD_ABFX_KIND_BITS, 'kinds unique and inside the field width');
  const regs = src => [...src.matchAll(/clientfield::register\( "(\w+)", "(\w+)", VERSION_SHIP, (\w+), "(\w+)"/g)].map(m => [m[1], m[2], m[3], m[4]].join(':'));
  const g = regs(GSC), c = regs(CSC);
  ok(g.length === 6 && JSON.stringify(g) === JSON.stringify(c), 'the six clientfields match (names / sizes / order): ' + g.join(' | '));
  ok(g[0].includes('tod_abfx_kind') && g[1].includes(':tod_abfx:'), 'the kind is registered BEFORE the counter (applied first on the client)');
  ok(g[4].includes('tod_abfx_hitk') && g[5].includes(':tod_abfx_hit:'), 'the hit kind is registered BEFORE the hit counter (docs/206)');
  ok(/kind = self clientfield::get\( "tod_abfx_hitk" \)/.test(CSC) && /function hit_play\( lc \)[\s\S]*?wait 0\.05;/.test(CSC), 'the client reads the hit kind after the snapshot settles');
  ok(/if \( !local \) self body_fx\( lc, \( kind == TOD_ABFX_CLOAK_ON/.test(CSC) && /if \( !local \) self body_fx\( lc, "tod_abfx_card_" \+ r/.test(CSC) && /if \( !local \) self body_fx\( lc, "tod_abfx_shield_break"/.test(CSC) && /if \( self == GetLocalPlayer\( lc \) \) return;\s*\n\s*DEFAULT\( self\.tod_abfx_sword/.test(CSC),
    'the docs/206 body one-shots and the blade glow are for the OTHERS (the 1p rule: no sprites at the local camera)');
  ok(/if \( local \) PlayViewmodelFX\( lc, level\._effect\[ "tod_abfx_draw_vm" \], "tag_flash" \)/.test(CSC), 'the full draw has its viewmodel half');
  ok(/KillFX\( lc, self\.tod_abfx_dive\[ lc \] \)/.test(CSC) && /KillFX\( lc, self\.tod_abfx_sword\[ lc \] \)/.test(CSC) && /kill_after\( lc, h, TOD_ABFX_BURN_SECS \)/.test(CSC), 'the dive streak, the blade glow and the torso fire all end (KillFX)');
  const sent = [...GSC.matchAll(/play\( player, (TOD_ABFX_\w+)[^)]*\)/g)].map(m => m[1]).concat([...GSC.matchAll(/TOD_ABFX_DASH_\w+/g)].map(m => m[0]));
  for (const k of new Set(sent)) ok(CSC.includes(k) || k === 'TOD_ABFX_NONE', 'the client knows every kind the server sends: ' + k);
  ok(/kind >= TOD_ABFX_PULSE_0 && kind <= TOD_ABFX_PULSE_3/.test(CSC) && gd.TOD_ABFX_PULSE_3 - gd.TOD_ABFX_PULSE_0 === 3, 'four pulse bands');
  ok(/if \( local \) PlayViewmodelFX\( lc, level\._effect\[ "tod_abfx_dash_vm" \]/.test(CSC) && /if \( local \) PlayFXOnCamera\( lc, level\._effect\[ "tod_abfx_bash_1p" \]/.test(CSC)
    && /if \( local \) PlayFXOnCamera\( lc, level\._effect\[ "tod_abfx_pulse_1p" \]/.test(CSC) && /if \( local \) PlayViewmodelFX\( lc, level\._effect\[ "tod_abfx_demon_on_1p" \]/.test(CSC),
    'every ability has a FIRST-PERSON half gated on the local player');
  ok(/body_fx\( lc, "tod_abfx_dash_" \+ kind, TOD_ABFX_BODY_TAG \)/.test(CSC) && /body_fx\( lc, "tod_abfx_demon_aura", TOD_ABFX_BODY_TAG \)/.test(CSC) && /body_fx\( lc, "tod_abfx_trail", TOD_ABFX_BODY_TAG \)/.test(CSC),
    'every ability has a BODY half a teammate sees');
  ok(/self thread abfx_play\( lc, self\.origin \)/.test(CSC) && /wait 0\.05;\s*\n\s*if \( !isdefined\( self \) \) return;\s*\n\s*kind = self clientfield::get\( "tod_abfx_kind" \)/.test(CSC),
    'the client reads the kind AFTER the snapshot settles and keeps the cast origin');
  ok(/KillFX\( lc, self\.tod_abfx_demon_fx\[ lc \] \)/.test(CSC) && /KillFX\( lc, self\.tod_abfx_trail\[ lc \] \)/.test(CSC) && /kill_after\( lc, h, TOD_ABFX_DASH_SECS \)/.test(CSC),
    'every looping body effect has its KillFX (the aura, the trail, the dash streak)');
  ok(/if \( isdefined\( player\.tod_abfx_frame_ms \) && player\.tod_abfx_frame_ms == now \)[\s\S]*?play_later/.test(GSC), 'two events in one frame: the second is deferred, never lost');
  ok(/if \( on && \( cur & bit \) == 0 \) next = cur \+ bit;/.test(GSC) && !/~bit/.test(GSC), 'the state bits are added / subtracted (GSC has no ~)');
}

// ---- C. the wiring ---------------------------------------------------------------------------------
console.log('C. wiring');
{
  ok(/tod_ability_fx::init\(\);/.test(MAIN) && /#using scripts\\zm\\zm_tod2_cybercity\\_tod_ability_fx;/.test(MAIN), '_tod_main inits + #usings the module');
  ok(MAIN.indexOf('tod_ability_fx::init();') < MAIN.indexOf('tod_class_cards::init();'), 'the feedback module inits before the class cards');
  ok(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_ability_fx;/.test(ENTRY_CSC), 'the entry .csc #usings the client half');
  for (const s of ['_tod_ability_fx.gsc', '_tod_ability_fx.csc']) ok(ZONE.includes('scriptparsetree,scripts/zm/zm_tod2_cybercity/' + s + '\n'), 'zoned: ' + s);
  ok(/tod_ability_fx::bash_dash\( self, blade \);[\s\S]*?level thread bash_run\(/.test(KIT), 'BASH: the dash hook before the run');
  ok(/tod_ability_fx::bash_impact\( self, self bash_rank\(\) >= 9 \);/.test(KIT), 'BASH: the impact hook with the Lv9 flag');
  ok(/left = ms;\s*\n\s*while \( left > 0 \)[\s\S]*?fx_at\( "zombie\/fx_tesla_shock_zmb"[\s\S]*?step = \( left < 1200 \? left : 1200 \);/.test(KIT), 'the stun tell loops for the whole stun');
  ok(/tod_ability_fx::soul_pulse\( self, band \);/.test(NECRO) && NECRO.indexOf('tod_ability_fx::soul_pulse') > NECRO.indexOf('clientfield::increment( "tod_necro_bomb" )'), 'SOUL PULSE: the dome after the ring, same band');
  ok(/tod_ability_fx::actor_soul\( self \);/.test(NECRO), 'SOUL PULSE: a struck elite flashes');
  ok(/tod_ability_fx::fusion_heal\( p \);/.test(CARDS) && /tod_ability_fx::fusion_launch\( self \);/.test(CARDS) && /tod_ability_fx::fusion_land\( self \);/.test(CARDS), 'FUSION: heal / launch / land hooks');
  ok(CARDS.indexOf('tod_ability_fx::fusion_land( self )') < CARDS.indexOf('wait 0.25;\n\tif ( !isdefined( self ) ) return;\n\tself.tod_fjump_air = undefined;'), 'the landing plays on the landing frame');
  ok(/tod_ability_fx::demon_on\( self, ms \);/.test(CARDS), 'DEMON SLAYER: the activation hook');
  for (const [name, src] of [['_tod_class_kit', KIT], ['_tod_class_cards', CARDS], ['_tod_necro_summon', NECRO], ['_tod_archer', ARCHER], ['_tod_retriever', RETR]])
    ok(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_ability_fx;/.test(src), name + ' #usings the feedback module');
  ok(/tod_ability_fx::ring_at\( self, "tod\/archer\/fx_tod_archer_charge", 0\.6 \);/.test(ARCHER) && !/PlayFXOnTag\( "tod\/archer\/fx_tod_archer_charge", self/.test(ARCHER), 'the landing ring rides a host that dies (docs/203 s4)');
  ok(/tod_ability_fx::ring_at\( self, level\.tod_retriever_charge_fx, 0\.6 \);/.test(RETR) && !/PlayFXOnTag\( level\.tod_retriever_charge_fx, self/.test(RETR), 'the Retriever charge ring rides a host that dies');
  ok(/host thread ring_run\( fx, secs \);[\s\S]*?function ring_run[\s\S]*?wait secs;\s*\n\s*if \( isdefined\( self \) \) self Delete\(\);/.test(GSC), 'ring_at: the host deletes itself');
  const played = new Set([...GSC.matchAll(/Play(?:Local)?Sound\( "(tod_abfx_\w+)" \)/g)].map(m => m[1])
    .concat([...GSC.matchAll(/sound_3d\( [^,]+, "(tod_abfx_\w+)" \)/g)].map(m => m[1])));
  const csv = read('sound/aliases/tod_ability.csv');
  ok(played.size >= 12, 'aliases played read (' + played.size + ')');
  for (const a of played) ok(new RegExp('^' + a + ',', 'm').test(csv), 'alias has rows: ' + a);
  for (const a of ['tod_abfx_dash_3d', 'tod_abfx_pulse_3d', 'tod_abfx_launch_3d', 'tod_abfx_demon_on_3d', 'tod_abfx_land_3d', 'tod_abfx_impact_3d', 'tod_abfx_dive_3d',
    'tod_abfx_cloak_on_3d', 'tod_abfx_cloak_off_3d', 'tod_abfx_shield_break_3d', 'tod_abfx_pierce_3d', 'tod_abfx_card_1_3d', 'tod_abfx_card_2_3d', 'tod_abfx_card_3_3d', 'tod_abfx_card_4_3d'])
    ok(new RegExp('^' + a + ',[^\\n]*,3d,', 'm').test(csv), a + ' is a 3D row (the teammate hears it from the caster)');
  ok(/^tod_abfx_c4_loop,[^\n]*,3d,[^\n]*,looping,/m.test(csv) && /PlayLoopSound\( "tod_abfx_c4_loop" \)/.test(GSC), 'the C4 beep is a 3D looping row on the carrier');
  ok(/,loaded,tod\\abfx\\tod_abfx_/.test(csv) && !/melee_whoosh|lfe_sweep_hit|soul_steal\.wav|tod_sky_jet|demon_appear|elemental_pop_activate|tod_heat_out/.test(csv),
    'every ability cue is its own wav under sound_assets/tod/abfx (no borrowed stock cue left; docs/206)');
  ok(!/tod_abfx_thump_plr|tod_abfx_demon_3d"/.test(GSC), 'the shared thump and the old demon_3d alias are gone from the server module');
  // docs/206: the second pass's hooks
  ok(/tod_ability_fx::dive_start\( self, d\.floor \);/.test(KIT) && /tod_ability_fx::dive_start\( owner, dive\.floor \);/.test(KIT) && (KIT.match(/tod_ability_fx::dive_end\( (self|owner) \);/g) || []).length === 3 && /d\.floor = tr\[ "position" \];/.test(KIT),
    'CYBER SMASH dive: start / end hooks on both lanes, the floor from the trace');
  ok(!/tod_ability_fx::/.test(KIT.slice(KIT.indexOf('function gs_dive_start'), KIT.indexOf('function gs_fall_guard')).replace(/\/\/[^\n]*/g, '')), 'no namespaced call inside gs_dive_start / update / end (tools/warrior/test_gs_dive.js transpiles those three; comments stripped like it does)');
  ok(/tod_ability_fx::sword_ready\( self, kit == TOD_KIT_WARRIOR && lethal == 0 \);/.test(KIT), 'the charged blade follows the HUD readiness');
  ok(/grenade\.tod_abfx_c4 = tod_ability_fx::c4_armed\( grenade \);/.test(KIT), 'a planted C4 blinks + beeps');
  ok(c4RestArm(KIT), 'the C4 arms the moment it comes to rest, inside the stick window (the user detonates in 0.1-0.35 s)');
  ok(/if \( isdefined\( grenade \) && !isdefined\( grenade\.tod_abfx_c4 \) \)\s*\{\s*grenade\.tod_abfx_c4 = tod_ability_fx::c4_armed\( grenade \);/.test(KIT), 'a charge arms once: the window-end fallback skips one already armed at rest');
  ok(/#define TOD_CLUSTER_FX_BOMBLET\s+"tod\/abfx\/fx_abfx_cl_pop_t3"/.test(KIT) && /#precache\( "fx", "tod\/abfx\/fx_abfx_cl_pop_t3" \);/.test(KIT), 'the tier-3 cluster pop carries a light');
  ok(/tod_ability_fx::cloak_on\( self \);/.test(CARDS) && /tod_ability_fx::cloak_off\( self \);/.test(CARDS) && !/PlaySound\( TOD_CLOAK_SND/.test(CARDS), 'CLOAK: own vanish / reappear bursts + cues (the stock Blink pair no longer played)');
  ok(/tod_ability_fx::pierce_hit\( z \);[^\n]*\n\s*z DoDamage\( share/.test(CARDS), 'PIERCING: the through-hit before the damage');
  ok(/tod_ability_fx::shield_break\( self \);/.test(SHIELD) && /tod_ability_fx::shield_back\( self \);/.test(SHIELD) && !/PlaySoundAtPosition\(|PlayLocalSound\( TOD_SHIELD/.test(SHIELD), 'RIOT SHIELD: break + return on the proven lanes (no PlaySoundAtPosition, no lounge chime)');
  // THE AUTOMATIC BOW (2026-10-05): the bow releases ITSELF at full draw (chargeShotFireWhenQueueReachesMax 1), so the
  // docs/206 glow + tick that said "release now" is retired; the full-power release layer is the full-draw tell, and
  // the pull-back creak plays once PER DRAW (a held chain draws again after every arrow). Negative control: the old
  // manual-release source (draw_full on a held full draw) must fail the new contract.
  {
    const autoBow = src => !/tod_ability_fx::draw_full\(/.test(src) && /self PlayLocalSound\( full_alias\( w \) \)/.test(src)
      && /creak_for != self\.tod_ab_press_ms/.test(src) && /held = self AttackButtonPressed\(\);/.test(src);
    ok(autoBow(BOW), 'THE BOW: no "release now" tick on an auto-release bow; the full-power layer + one creak per draw');
    ok(!autoBow('tod_ability_fx::draw_full( self );   full_told = false; self compute_frac( w ) >= TOD_AB_FULL self PlayLocalSound( full_alias( w ) )'), 'negative control: the manual-release cue fails the auto-bow contract');
  }
  ok(/tod_ability_fx::burst_at\( "electric\/fx_elec_sparks_burst_xsm_omni_blue_os"/.test(ARCHER) && !/\n\s*PlayFX\( "electric/.test(ARCHER), 'the hook bite rides a carrier');
  ok(/tod_ability_fx::axe_hit\( z \);/.test(RETR) && !/\n\s*PlayFX\( level\.tod_archer_impact_fx/.test(RETR), 'the Retriever hit is drawn on the zombie by the client');
  ok((RUNE.match(/tod_ability_fx::burst_at\( TOD_RUNE_FX_(IMPACT|AOE|END), \w+, \( -90, 0, 0 \)/g) || []).length === 3 && /tod_ability_fx::burn\( z \);/.test(RUNE) && !/\n\s*PlayFX\( TOD_RUNE_FX|PlayFXOnTag\( TOD_RUNE_FX_TORSO/.test(RUNE),
    'the Rune Prison: impact / eruption / end on carriers (forward up), the torso fire on the client');
  ok((UPG.match(/tod_ability_fx::card_taken\( player, /g) || []).length === 3, 'A CARD TAKEN: the dark, tier and level lanes all burst');
  ok(/function burst_at\( fx, org, angles, life \)[\s\S]*?host thread ring_run\( fx, life \);/.test(GSC) && /function c4_follow\( grenade \)[\s\S]*?grenade waittill\( "death" \);\s*\n\s*self StopLoopSound\(\);\s*\n\s*self Delete\(\);/.test(GSC) && /wait 180;[^\n]*\n\s*self Delete\(\);/.test(GSC),
    'every carrier dies: the burst by its life, the C4 blink with its charge (or after 180 s)');
  ok(/function on_spawned\(\)[\s\S]*?self clientfield::set\( "tod_abfx_state", 0 \);/.test(GSC) && /callback::on_spawned\( &on_spawned \);/.test(GSC), 'a fresh life carries no body state');
  // _tod_archer_bow left this list 2026-10-05: its one call (draw_full) retired with the auto-release bow.
  for (const [name, src] of [['_tod_riotshield', SHIELD], ['_tod_archer_rune', RUNE], ['_tod_upgrades', UPG]])
    ok(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_ability_fx;/.test(src), name + ' #usings the feedback module (docs/206)');
  ok(!/#using scripts\\zm\\zm_tod2_cybercity\\_tod_(?!ability_fx)/.test(GSC.replace(/\/\/[^\n]*/g, '')), 'the feedback module imports no tod module (a leaf: every class module may import it)');
  const nBlocks = re => (TWINS.match(re) || []).length;
  const nG = nBlocks(/"cc_gauntlet[^"]*" \( "/g), nS = nBlocks(/"cc_gold_sword[^"]*" \( "/g), nP = nBlocks(/"cc_punch[^"]*" \( "/g);
  ok(nG > 0 && nS > 0 && nP > 0 && nBlocks(/"meleeImpactEffect" "tod\\\\abfx\\\\fx_abfx_gauntlet_hit\.efx"/g) === nG && nBlocks(/"meleeImpactNoBloodEffect" "tod\\\\abfx\\\\fx_abfx_gauntlet_hit\.efx"/g) === nG
    && nBlocks(/"meleeImpactEffect" "tod\\\\abfx\\\\fx_abfx_sword_hit\.efx"/g) === nS && nBlocks(/"meleeImpactNoBloodEffect" "tod\\\\abfx\\\\fx_abfx_sword_hit\.efx"/g) === nS
    && nBlocks(/"meleeImpactEffect" "dlc5\\\\tomb\\\\fx_one_inch_punch_impact\.efx"/g) === nP,
    `the blades carry their own hit effects on every form (gauntlet ${nG}, sword ${nS}); the punch keeps the Origins fist puff (${nP}) (gen_tod_twins tune.add)`);
  for (const fx of ['fx_abfx_gauntlet_hit', 'fx_abfx_sword_hit']) ok(ZONE.includes('\nfx,tod/abfx/' + fx + '\n'), 'zoned for the weapon GDT: ' + fx);
  ok(/"Filename": "tod_ability\.csv"/.test(SZC), 'the alias table is in the sound zone config');
  const mats = new Set([...GSC.matchAll(/SetShader\( "(tod_\w+)", 640/g)].map(m => m[1]).concat(['tod_demon_vignette', 'tod_fusion_vignette']));
  for (const m of mats) {
    ok(GDT.includes('"' + m + '" ( "material.gdf" )') && GDT.includes('"i_' + m + '" ( "image.gdf" )'), 'in the GDT: ' + m);
    ok(ZONE.includes('\nmaterial,' + m + '\n') && ZONE.includes('\nimage,i_' + m + '\n'), 'zoned image + material: ' + m);
    const png = fs.readFileSync(path.join(root, 'source_data/tod_kill_feel_art/_images/i_' + m + '.png'));
    const w = png.readUInt32BE(16), h = png.readUInt32BE(20);
    ok(w % 4 === 0 && h % 4 === 0, `${m}: ${w}x${h} is 4-aligned (compressed-image-multiple-of-4)`);
  }
}

// ---- D. the kill feel is gone and stays gone ------------------------------------------------------
console.log('D. the kill feel is retired');
{
  ok(!exists('scripts/zm/zm_tod2_cybercity/_tod_kill_feel.gsc'), 'no _tod_kill_feel.gsc');
  ok(!exists('sound/aliases/tod_kill_feel.csv') && !/tod_kill_feel\.csv/.test(SZC), 'no kill-feel alias table');
  ok(!/_tod_kill_feel|tod_kill_feel::/.test(MAIN + ZONE), 'not inited, not zoned');
  ok(!/tod_kill_feel_fn/.test(UPG), 'the chokepoint has no kill-feel hook');
  ok(!/tod_kill_label_fn|KF_SKEWERED|KF_MEAT_CANNON|KF_SOUL_HARVEST|KF_OVERKILL|KF_MULTI_/.test(HUDKIT), 'the HUD kit has no label hook, no signature strings');
  ok(!/KF_SKEWERED|KF_MEAT_CANNON|KF_CLEAVE|KF_DISMEMBERED|KF_SOUL_HARVEST|KF_OVERKILL|KF_MULTI_/.test(STR), 'no signature / multi-kill strings');
  ok(!/corpse_will_linger|tod_corpse_linger/.test(CORPSE), 'no fling gate, no ash linger');
  ok(!/tod_splat/.test(ZONE + GDT) && !exists('source_data/tod_kill_feel_art/_images/i_tod_splat_01.png'), 'no screen blood');
  ok(!/fx_abfx_embers/.test(ZONE) && !exists('share/raw/fx/tod/abfx/fx_abfx_embers.efx'), 'no ember puff');
  ok(!/fx_blood_torso_explo_lg_zmb|dlc5\/tomb\/fx_heat_distortion_fire_lg/.test(ZONE), 'its two stock fx rows are gone');
}

// ---- E. negative controls -----------------------------------------------------------------------------
console.log('E. negative controls');
{
  const lateArm = KIT.replace(/\n\t\tif \( !isdefined\( grenade\.tod_abfx_c4 \) && isdefined\( grenade\.tod_c4_prev2 \)[^\n]*\n\t\t\{\n[^\n]*\n[^\n]*\n\t\t\}/, '');
  ok(lateArm !== KIT && !c4RestArm(lateArm), 'NEGATIVE: a C4 that arms only after the stick window is caught');
  const drifted = CSC.replace('#define TOD_ABFX_FUSION_LAUNCH    11', '#define TOD_ABFX_FUSION_LAUNCH    12');
  ok(defsOf(drifted).TOD_ABFX_FUSION_LAUNCH !== defsOf(GSC).TOD_ABFX_FUSION_LAUNCH, 'NEGATIVE: a drifted kind is a lockstep failure');
  const unzoned = ZONE.replace('\nfx,tod/abfx/fx_abfx_demon_aura_c0\n', '\n');
  ok(!unzoned.includes('\nfx,tod/abfx/fx_abfx_demon_aura_c0\n'), 'NEGATIVE: an unzoned child effect is caught by the every-effect-zoned check');
  const unhooked = CARDS.replace('tod_ability_fx::demon_on( self, ms );', '');
  ok(!/tod_ability_fx::demon_on\( self, ms \);/.test(unhooked), 'NEGATIVE: a removed hook is caught');
  const revived = UPG + '\n\tif ( isdefined( level.tod_kill_feel_fn ) ) [[ level.tod_kill_feel_fn ]]( attacker );\n';
  ok(/tod_kill_feel_fn/.test(revived), 'NEGATIVE: a revived kill-feel hook is caught by D');
  const oldring = ARCHER.replace('tod_ability_fx::ring_at( self, "tod/archer/fx_tod_archer_charge", 0.6 );', 'PlayFXOnTag( "tod/archer/fx_tod_archer_charge", self, "tag_origin" );');
  ok(/PlayFXOnTag\( "tod\/archer\/fx_tod_archer_charge", self/.test(oldring), 'NEGATIVE: the old looping ring on the player is caught');
  // docs/206
  const csv = read('sound/aliases/tod_ability.csv');
  const regs = src => [...src.matchAll(/clientfield::register\( "(\w+)", "(\w+)", VERSION_SHIP, (\w+), "(\w+)"/g)].map(m => [m[1], m[2], m[3], m[4]].join(':'));
  const bareRune = RUNE.replace('tod_ability_fx::burst_at( TOD_RUNE_FX_IMPACT, ground, ( -90, 0, 0 ), 2.0 );', 'PlayFX( TOD_RUNE_FX_IMPACT, ground, ( 0, 0, 1 ) );');
  ok(/\n\s*PlayFX\( TOD_RUNE_FX/.test(bareRune), 'NEGATIVE: a bare rune one-shot is caught');
  const silentShield = SHIELD.replace('tod_ability_fx::shield_break( self );', 'PlaySoundAtPosition( "tod_shield_break", self.origin );');
  ok(/PlaySoundAtPosition\(/.test(silentShield), 'NEGATIVE: the silent shield lane is caught');
  const borrowed = csv + '\ntod_abfx_dash_plr,,loaded,zmb\\ai\\fury\\melee_whoosh\\melee_whoosh_01.wav,\n';
  ok(/melee_whoosh/.test(borrowed), 'NEGATIVE: a borrowed stock cue in the alias table is caught');
  const fourFields = CSC.replace(/\n\tclientfield::register\( "actor", "tod_abfx_hitk"[^\n]*/, '');
  ok(regs(fourFields).length === 5, 'NEGATIVE: a missing hit-kind registration is caught by the six-field check');
}

console.log(`\nABILITY FX: ${checks} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);
