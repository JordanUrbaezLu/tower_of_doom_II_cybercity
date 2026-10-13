// tools/test_doppelghast.js — THE DOPPELGHAST PREFLIGHT (docs/160 §9).
//
// The Doppelghast is Hellbound's BO6 ghoul port. Its aitype / character /
// model / clip GDTs are NOT in this repo (they are installed at the private
// tools root, snapshotted in donor_gdt/hellbound/ — the docs/153 donor rule),
// so a build on a fresh root would link a spawner that does not exist and
// SpawnActor would return undefined every 30 s in the crown. This gate proves,
// before the linker runs:
//   1. the tools root carries the aitype + model + clip GDTs, the AI tables,
//      the xmodel_bin and every xanim_bin the tables and the script name;
//   2. this repo carries the zone lines, the script modules, the sound table
//      + its wavs, and the szc entry;
//   3. every %anim the script plays is in the AI mapping table (Hellbound's
//      docs/BO6_DEV_SPAWN_TEST.md:160 — a zone xanim line alone is not enough);
//   4. every "hb_bo6_" alias the audio module can fire has a row, and every
//      Secondary those rows name is in the table too.
// Run: node tools/test_doppelghast.js   (build_map.ps1 runs it before the lints)
'use strict';
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
let fails = 0, checks = 0;
function ok(cond, msg) { checks++; if (!cond) { fails++; console.error('  FAIL ' + msg); } }
function read(p) { return fs.readFileSync(p, 'utf8'); }

// --- the PRIVATE tools root (tools/tod2_workspace.js: the isolation guard) --
const tools = require('./tod2_workspace.js').toolsRoot();
ok(tools && fs.existsSync(tools), 'private tools root exists: ' + tools);

const gdtAi = path.join(tools, 'source_data', 'hb_bo6_dev_ai.gdt');
const gdtModel = path.join(tools, 'source_data', 'hb_doppelghast.gdt');
ok(fs.existsSync(gdtAi), 'tools root has source_data/hb_bo6_dev_ai.gdt (the aitype)');
ok(fs.existsSync(gdtModel), 'tools root has source_data/hb_doppelghast.gdt (model + clips)');
if (fs.existsSync(gdtAi)) {
  const g = read(gdtAi);
  for (const a of ['"archetype_hb_doppelghast_dev" ( "aitype.gdf" )', '"spawner_hb_doppelghast_dev" [ "variant_hb_doppelghast_dev" ]',
                   '"c_hb_doppelghast_dev" ( "character.gdf" )', '"animMappingTableName" "hb_doppelghast_dev.ai_am"', '"animSelectorTableName" "hb_doppelghast_dev.ai_ast"'])
    ok(g.includes(a), 'aitype GDT defines ' + a);
}
ok(fs.existsSync(path.join(tools, 'model_export', 'hb', 'doppelghast', 'hb_bo6_doppelghast.XMODEL_BIN')), 'tools root has the xmodel_bin');
const CLIPS = ['idle_01', 'walk_01', 'run_01', 'sprint_01', 'stn_melee_01', 'stn_melee_02', 'sprint_melee_01', 'run_pain_l_01', 'dth_01', 'juke_l_short_01', 'juke_r_short_01'];
// R5 (2026-10-04): only the clips a script plays (%anim) are zoned; the _dev clips the AI tables map read the
// other bins straight from the tools root, so every bin above must still exist.
const ZONED_CLIPS = ['stn_melee_01', 'dth_01', 'juke_l_short_01', 'juke_r_short_01'];
for (const c of CLIPS)
  ok(fs.existsSync(path.join(tools, 'xanim_export', 'hb', 'doppelghast', `hb_doppelghast_${c}.XANIM_BIN`)), `tools root has xanim_bin ${c}`);

// --- the repo: AI tables, snapshots, sync mapping ---------------------------
for (const t of ['hb_doppelghast_dev.ai_am', 'hb_doppelghast_dev.ai_ast'])
  ok(fs.existsSync(path.join(root, 'animtables', t)), 'repo animtables/' + t);
ok(read(path.join(root, 'tools', 'sync_to_modtools.ps1')).includes('RepoRel = "animtables"'), 'sync maps animtables/');
for (const s of ['hb_doppelghast.gdt', 'hb_bo6_dev_ai.gdt'])
  ok(fs.existsSync(path.join(root, 'donor_gdt', 'hellbound', s)), 'donor snapshot donor_gdt/hellbound/' + s);

// --- the repo: scripts + zone ---------------------------------------------
const mod = path.join(root, 'scripts', 'zm', 'zm_tod2_cybercity');
for (const f of ['_tod_doppelghast.gsc', '_tod_bo6_audio.gsc', '_tod_bo6_audio_events.gsh', '_tod_doppelghast_motion.gsh', '_tod_fall.gsc'])
  ok(fs.existsSync(path.join(mod, f)), 'module ' + f);
const zone = read(path.join(root, 'zone_source', 'zm_tod2_cybercity.zone'));
for (const line of ['scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_doppelghast.gsc', 'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_bo6_audio.gsc',
                    'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_fall.gsc', 'aitype,spawner_hb_doppelghast_dev', 'xmodel,hb_bo6_doppelghast',
                    'fx,blood/fx_blood_impact_exp_body_lg_zmb', 'fx,blood/fx_blood_neck_spray_zmb',
                    'aitype,spawner_zm_factory_zombie_dog',   // the spawn tell's lightning + zmb_hellhound_* ride the stock dog aitype
                    ...ZONED_CLIPS.map(c => `xanim,hb_doppelghast_${c}`)])
  ok(zone.split(/\r?\n/).some(l => l.trim() === line), 'zone line ' + line);

// --- every scripted %anim is in the AI mapping table ------------------------
const dop = read(path.join(mod, '_tod_doppelghast.gsc'));
const am = read(path.join(root, 'animtables', 'hb_doppelghast_dev.ai_am'));
const anims = new Set([...dop.matchAll(/%(hb_doppelghast_[a-z0-9_]+)/g)].map(m => m[1]));
ok(anims.size >= 4, 'script plays %anims: ' + [...anims].join(' '));
for (const a of anims) ok(am.includes(a), `%${a} is in hb_doppelghast_dev.ai_am (the generic-tree trap)`);
ok(dop.includes('#using_animtree( "generic" )'), 'script uses the generic animtree');
ok(dop.includes('"spawner_hb_doppelghast_dev"'), 'script spawns spawner_hb_doppelghast_dev');

// --- the audio table: every alias the module can fire, and its secondaries --
const csvPath = path.join(root, 'sound', 'aliases', 'hb_bo6_ghoul.csv');
ok(fs.existsSync(csvPath), 'sound/aliases/hb_bo6_ghoul.csv');
const szc = read(path.join(root, 'sound', 'zoneconfig', 'zm_tod2_cybercity.szc'));
ok(JSON.parse(szc).Sources.some(s => s.Type === 'ALIAS' && s.Filename === 'hb_bo6_ghoul.csv'), 'szc lists hb_bo6_ghoul.csv');
if (fs.existsSync(csvPath)) {
  const lines = read(csvPath).split(/\r?\n/).filter(Boolean);
  const hdr = lines[0].split(',');
  const iName = hdr.indexOf('Name'), iFile = hdr.indexOf('FileSpec'), iSec = hdr.indexOf('Secondary');
  const rows = lines.slice(1).map(l => l.split(','));
  const names = new Set(rows.map(r => r[iName]));
  const audio = read(path.join(mod, '_tod_bo6_audio.gsc')) + read(path.join(mod, '_tod_bo6_audio_events.gsh'));
  // every ghoul source alias the module or its notetrack table can emit
  const fired = new Set([...audio.matchAll(/"((?:evt|fly|vox)_ai_ghoul_[a-z0-9_]+)"/g)].map(m => 'hb_bo6_' + m[1]));
  fired.add('hb_bo6_evt_ai_ghoul_death_oneshot');   // PlaySoundAtPosition in the death burst
  for (const a of fired) ok(names.has(a), `alias row for ${a}`);
  for (const r of rows) {
    const sec = iSec >= 0 ? r[iSec] : '';
    if (sec) ok(names.has(sec), `secondary ${sec} of ${r[iName]} is in the table`);
    const wav = path.join(root, 'sound_assets', r[iFile].replace(/\\/g, '/'));
    ok(fs.existsSync(wav), `wav ${r[iFile]}`);
  }
  ok(rows.length >= 50, `table has ${rows.length} rows`);
}

// --- the Fall wiring ---------------------------------------------------------
const fall = read(path.join(mod, '_tod_fall.gsc'));
for (const s of ['tod_doppelghast::spawn_hunter', 'tod_doppelghast::hall_spot', 'tod_doppelghast::alive_count', '#define TOD_FALL_HUNT_AFTER_SECS   90', '#define TOD_FALL_HUNT_EVERY_SECS   30', 'tod_mangler::spawn_at', 'gap = gap * TOD_FALL_HUNT_DECAY;', 'level.tod_crown_pap_live = true;'])
  ok(fall.includes(s), '_tod_fall has ' + s);
ok(read(path.join(mod, '_tod_main.gsc')).includes('tod_doppelghast::init();'), '_tod_main inits the module');
ok(read(path.join(mod, '_tod_crown_data.gsc')).includes('function hall_riser_orgs()'), 'crown data emits hall_riser_orgs');

// --- the calm, the alarm, the siren (docs/160 section 10) ------------------
for (const t of ['#define TOD_FALL_CALM_SECS   20', 'flag::clear( TOD_FALL_SPAWN_FLAG )', 'flag::set( TOD_FALL_SPAWN_FLAG )',
                 'tod_crown_data::alarm_org()', 'tod_crown_alarm::start();',
                 // 2026-09-29: the siren is a wind-up, a TRUE loop on the host, and a wind-down at the door
                 'e PlaySound( TOD_FALL_SIREN_START );', 'e PlayLoopSound( TOD_FALL_SIREN_LOOP, TOD_FALL_SIREN_XFADE );',
                 'e StopLoopSound( TOD_FALL_SIREN_STOP_FADE );', 'e PlaySound( TOD_FALL_SIREN_STOP );', 'level thread siren_stop();',
                 // THE LEVER (2026-09-24): the calm waits for the pull, stock's flip + sparks, the siren is a 30 s one-shot;
                 // since docs/208 the power switch is the Grid Terminal: its generated anchor, and the press boots its screen
                 '#define TOD_FALL_LEVER           1', 'tod_crown_data::power_terminal_org()', 'tod_power_terminal::boot( who );',
                 'tod_crown_data::power_terminal_trig()', 'handle = tod_power_terminal::spawn_at( org, yaw );',
                 // 2026-09-25: the flip's sparks ride a carrier (bare PlayFX never rendered here), and the
                 // alarm switch glows + sparks until it is pulled ("players can actually gravitate towards it")
                 'spark_burst( fx_org );', 'PlayFXOnTag( TOD_FALL_LEVER_SPARKS, host, "tag_origin" );', 'self thread switch_attract( fx_org );',
                 'self notify( "tod_switch_pulled" );',
                 // 2026-09-28 (user): no red glow above the alarm button; the siren repeats until the escape door opens
                 'function alarm_until_escape()', 'level flag::get( TOD_FALL_FLAG )', 'level thread alarm_until_escape();',
                 'flood( TOD_FALL_LEVER_LEAD_SECS );', 'level.tod_fall_lever_pulled = true;',
                 // TWO SWITCHES (2026-09-25): the alarm in the crown starts the game, the power at the overlook arms after it
                 'tod_crown_data::alarm_button_org()', 'button_press( handle, fx_org );', 'cap SetModel( TOD_FALL_BUTTON_CAP_OFF );', 'TOD_FALL_ALARM_HINT', 'power_switch_on( player.name );', 'level.tod_fall_power_ms = GetTime();',
                 'while ( !IS_TRUE( level.tod_fall_flood ) && !power_is_on() )', 'function power_seal_safety()',
                 'while ( !IS_TRUE( level.tod_fall_flood ) )', 'IS_TRUE( p.tod_jumppad_flying )', 'function hall_spawn_guard()',
                 'tod_crown_data::jumppad_enabled()', 'tod_crown_data::on_crown_island( org )'])
  ok(fall.includes(t), '_tod_fall has ' + t);
ok(!/PlayFX\( TOD_FALL_LEVER_SPARKS/.test(fall), 'no bare server PlayFX for the switch sparks (it does not render)');
ok(!/set_glow\( glow, TOD_FALL_ATTRACT_GLOW \)/.test(fall) && !/#define TOD_FALL_ATTRACT_GLOW/.test(fall), 'no attract glow above the alarm button (user 2026-09-28)');
ok(!/flood\( lead_secs \)\s*\{[^}]*power_on\(\)/.test(fall), 'the alarm (flood) no longer turns the power on');
// W2E (2026-10-05): the four Map One directors that honoured ONLY ZOMBIES (the Panzer / Protector director in
// _tod_bosses, _tod_reaver, _tod_hellhounds, _tod_sprinter) retired WHOLE; none may come back half-way.
for (const f of ['_tod_reaver.gsc', '_tod_hellhounds.gsc', '_tod_sprinter.gsc'])
  ok(!fs.existsSync(path.join(mod, f)), f + ' retired whole (archive/map1_carryover)');
ok(!/function director\(\)/.test(read(path.join(mod, '_tod_bosses.gsc'))), 'the Panzer / Protector director retired whole');
ok(read(path.join(root, 'scripts', 'zm', 'zm_tod2_cybercity.gsc')).includes('level.tod_only_zombies = true;'), 'ONLY ZOMBIES is on');
ok(read(path.join(root, 'ui', 'uieditor', 'widgets', 'HUD', 'ZM_CursorHint', 'ZMCursorHintNew.lua')).includes('"the alarm",'), 'the alarm prompt noun is claimed');
ok(fall.includes('"spawn_zombies"'), "_tod_fall holds the flood on stock's spawn_zombies flag");
const crown = read(path.join(mod, '_tod_crown_data.gsc'));
for (const t of ['function alarm_org()', 'function alarm_mount_orgs()', 'function jumppad_enabled()', 'function on_crown_island( org )'])
  ok(crown.includes(t), 'crown data emits ' + t);
const csc = read(path.join(mod, '_tod_perk_lights.csc'));
ok(csc.includes('level._effect[ "tod_glow_11" ] = "tod/crown_alarm/fx_tod_alarm_sweep";'), 'perk-light client lane maps index 11 to the alarm light');
ok(csc.includes('#precache( "client_fx", "tod/crown_alarm/fx_tod_alarm_sweep" );'), 'client precache of the alarm light');
ok(read(path.join(root, 'zone_source/tod_crown_alarm.zpkg')).includes('fx,tod/crown_alarm/fx_tod_alarm_sweep'), 'alarm package includes the red sweep light');
// THE ALARM MUST STOP AT THE DOOR (2026-09-29): alarm_stop() raises tod_fall_alarm_off, which
// ends any thread that endon's it, so a watcher that endon's it must never call alarm_stop()
// inline (that killed the door's shutdown; the siren and beacons ran on to the seal).
const untilEscape = (fall.match(/function alarm_until_escape\(\)\s*\{[\s\S]*?\n\}/) || [''])[0];
ok(/level endon\( "tod_fall_alarm_off" \)/.test(untilEscape) && /level thread alarm_stop\(\);/.test(untilEscape)
   && !/^\s*alarm_stop\(\);/m.test(untilEscape), 'alarm_until_escape threads alarm_stop (an inline call kills its own shutdown)');
for (const c of (fall.match(/^[^\n/]*\balarm_stop\(\);/gm) || []))
  ok(/level thread alarm_stop\(\);/.test(c), 'every alarm_stop() call is threaded: ' + c.trim());
ok(!/TOD_FALL_SIREN_REPEAT_SECS|TOD_FALL_SIREN_ALIAS/.test(fall), 'the timed one-shot repeat is retired');
const bosses = read(path.join(root, 'sound', 'aliases', 'tod_bosses.csv')).split(/\r?\n/);
ok(!bosses.some(l => l.startsWith('tod_fall_siren,')), 'the old 30 s one-shot row is retired');
for (const [name, loop] of [['tod_fall_siren_start', 'NONLOOPING'], ['tod_fall_siren_loop', 'LOOPING'], ['tod_fall_siren_stop', 'NONLOOPING']]) {
  const row = bosses.find(l => l.startsWith(name + ','));
  ok(!!row, 'tod_bosses.csv has the ' + name + ' row');
  if (!row) continue;
  const h = bosses[0].split(','), r = row.split(',');
  const col = k => r[h.indexOf(k)];
  ok(col('Looping') === loop && col('PanType') === '3d' && col('Pauseable') === 'yes', name + ' is ' + loop + ' + 3d + Pauseable (pauses with the script\'s waits)');
  ok(fs.existsSync(path.join(root, 'sound_assets', col('FileSpec').replace(/\\/g, '/'))), name + ' wav in the repo: ' + col('FileSpec'));
  ok(fall.includes('"' + name + '"'), '_tod_fall names ' + name);
}
// LOCKSTEP with tools/fall_siren/make_siren_clips.py (the clip lengths the script waits on)
const clipPy = read(path.join(root, 'tools', 'fall_siren', 'make_siren_clips.py'));
const pyNum = k => { const m = clipPy.match(new RegExp('^' + k + ' = ([0-9.]+)', 'm')); return m ? m[1] : null; };
const gscNum = k => { const m = fall.match(new RegExp('#define ' + k + '\\s+([0-9.]+)')); return m ? m[1] : null; };
ok(pyNum('XFADE') !== null && pyNum('XFADE') === gscNum('TOD_FALL_SIREN_XFADE'), 'siren crossfade matches the clip recipe (' + pyNum('XFADE') + ')');
ok(pyNum('STOP_SECS') !== null && pyNum('STOP_SECS') === gscNum('TOD_FALL_SIREN_STOP_SECS'), 'siren wind-down length matches the clip recipe (' + pyNum('STOP_SECS') + ')');
{
  // the wind-up clip ends XFADE after the loop takes over: its length pins TOD_FALL_SIREN_LOOP_AT
  const wav = path.join(root, 'sound_assets', 'tod', 'sfx', 'tod_fall_siren_start.wav');
  if (fs.existsSync(wav)) {
    const b = fs.readFileSync(wav);
    const rate = b.readUInt32LE(24), blockAlign = b.readUInt16LE(32);
    let off = 12, len = 0;
    while (off + 8 <= b.length) { const id = b.toString('ascii', off, off + 4), sz = b.readUInt32LE(off + 4); if (id === 'data') { len = sz; break; } off += 8 + sz + (sz & 1); }
    const secs = len / blockAlign / rate;
    const loopAt = parseFloat(gscNum('TOD_FALL_SIREN_LOOP_AT')), xf = parseFloat(gscNum('TOD_FALL_SIREN_XFADE'));
    ok(Math.abs(secs - (loopAt + xf)) < 0.01, 'wind-up clip (' + secs.toFixed(3) + ' s) = LOOP_AT + XFADE (' + (loopAt + xf).toFixed(3) + ' s)');
  }
}
for (const t of ['function lever_org()', 'function lever_yaw()', 'function alarm_button_org()', 'function alarm_button_yaw()'])
  ok(crown.includes(t), 'crown data emits ' + t);
for (const t of ['xmodel,p7_zm_der_pswitch_body', 'xmodel,p7_zm_der_pswitch_handle', 'fx,electric/fx_elec_sparks_directional_orange',
                 'xmodel,tod_alarm_button_stand', 'xmodel,tod_alarm_button_cap_on', 'xmodel,tod_alarm_button_cap_off'])
  ok(zone.split(/\r?\n/).some(l => l.trim() === t), 'zone line ' + t);
// THE INTRO (2026-09-24): a LOOPING 2d streamed row (the stoppable shape) cut by its clock or by the lever
const ui = read(path.join(root, 'sound', 'aliases', 'tod_ui.csv')).split(/\r?\n/);
const intro = ui.find(l => l.startsWith('tod_fall_intro,'));
ok(!!intro, 'tod_ui.csv has the tod_fall_intro row');
if (intro) {
  const h = ui[0].split(','), r = intro.split(',');
  const col = k => r[h.indexOf(k)];
  ok(col('Looping') === 'LOOPING' && col('PanType') === '2d' && col('Storage') === 'STREAMED', 'intro row is LOOPING + 2d + STREAMED');
  ok(fs.existsSync(path.join(tools, 'sound_assets', col('FileSpec').replace(/\\/g, '/'))), 'intro wav at the tools root: ' + col('FileSpec'));
}
const atmo = read(path.join(mod, '_tod_atmosphere.gsc'));
for (const t of ['#define TOD_MUSIC_INTRO         1', '#define TOD_VEIL                 0', 'function tower_fog()', 'level.tod_fall_power_ms', 'TOD_VEIL_CLEAR_SECS * 1000.0', 'channel_play( TOD_MUSIC_INTRO_ALIAS );', 'IS_TRUE( level.tod_fall_lever_pulled ) || IS_TRUE( level.tod_fall_flood )',
               // silence through the crown phase; the early cues: a player on the jump-pad balcony
               // (user 2026-09-29), else the first jump's title reveal (docs/196)
               'while ( IS_TRUE( level.tod_fall_phase ) )', 'p = balcony_player();', 'IS_TRUE( level.tod_jump_title )'])
  ok(atmo.includes(t), '_tod_atmosphere has ' + t);
ok(read(path.join(mod, '_tod_zombie_speed.gsc')).includes('if ( IS_TRUE( level.tod_fall_phase ) )\n\t\tr = 1.0;'), 'crown phase pins the sprint rate at exactly 1.0');
// 2026-09-25: the crown altar is RETIRED again; the item shop takes its shrine, the PaP wakes with the alarm
ok(!read(path.join(mod, '_tod_upgrades.gsc')).includes('\tstation_place( tod_crown_data::station_org(), tod_crown_data::station_trig_org(), tod_crown_data::station_yaw() );'), 'the crown altar is gone');
ok(read(path.join(root, 'tools', 'gen_tower_map.js')).includes('{x:-644,y:HYC,z:TOP2,yaw:90}'), 'the hall shop stands in the west shrine (the altar spot)');
{ const pap = read(path.join(root, 'scripts', 'zm', 'zm_cwpap.gsc'));
  ok(pap.includes('function machine_powered()') && pap.includes('IS_TRUE( level.tod_crown_pap_live )') && pap.includes('m_power machine_powered()'), 'the crown PaP is live from the alarm (zm_cwpap machine_powered)'); }
{ const hw = fall.slice(fall.indexOf('function hunters_watch()'), fall.indexOf('THE POWER'));
  ok(!hw.includes('tod_only_zombies'), 'the crown ramp is not switched off by ONLY ZOMBIES'); }
// the generator's three lighting switches (docs/162 step 0/1) leave their marks in the map
const map = read(path.join(root, 'map_source', 'zm', 'zm_tod2_cybercity.map'));
// THE GATE (user 2026-09-25, twice): shut and a 5000 buy at spawn, even in a dev build
ok(/#define TOD_FALL_GATE_OPEN\s+0\b/.test(fall), 'the Fall gate is NOT opened free at init (TOD_FALL_GATE_OPEN 0)');
ok(fall.includes('level.tod_fall_gate_flag = TOD_FALL_FLAG;'), '_tod_fall publishes its gate flag');
ok(read(path.join(mod, '_tod_doors.gsc')).includes('d.script_flag == level.tod_fall_gate_flag'), 'the dev door harness skips the Fall gate');
ok(fall.includes('function gate_state_log()'), 'the gate state is logged at +6 s');
ok(map.includes('"targetname" "tod_light_hall_fill_44"'), 'the crown hall fill grid (4 x 4) is in the map');
// THE ALARM LIGHTS THE HALL (2026-09-25): Radiant 3 carries the hall's lights only (+ the enclosed hallway's
// junction / east corridor / power room, so the power can be found in the dark), the alarm selects it
ok(fall.includes('level util::set_lighting_state( 2 );'), 'the alarm switches to script state 2 (Radiant 3: the hall lit)');
ok(map.includes('"ssi3" "tod_ssi_cybercity_dark"'), 'ssi3 filled (the alarm state keeps the dark sky)');
{
  const ents = map.split('// entity ').filter(e => e.includes('"classname" "light"'));
  const st3 = ents.filter(e => e.includes('"lightingstate3" "1"'));
  ok(st3.length >= 16 && st3.every(e => /"targetname" "tod_light_(crown_gate|shrine_[WE]|hall_(reredos|dais|spawn|fill_\d\d)|extraction|hallway_(junction|east|power))"/.test(e)), 'Radiant 3 lights = exactly the hall set (' + st3.length + ')');
  ok(!ents.some(e => /tod_light_hall_shop/.test(e) && e.includes('"lightingstate3" "1"')), 'the shop pools wait for the power');
}
ok(!map.includes('tod_light_test_T1'), 'T1 test lights retired (answered 2026-09-25: boots Radiant State 2)');
ok(map.includes('"ssi2" "tod_ssi_cybercity_dark"'), 'ssi2 = the pre-power dark SSI (THE BLACKOUT)');
// THE BLACKOUT (2026-09-25): no glowing face, every light waits for the power, the wave flips the state
ok(!/\) mwiii_vertigo_retro_synth_[a-z_]+ [-\d.]+ [-\d.]+ [-\d.]+ [-\d.]+ [-\d.]+ [-\d.]+ lightmap_gray/.test(map), 'no vertigo (glowing) face left in the map');
ok(!/"lightingstate2" "1"/.test(map), 'no light is on in Radiant State 2 (the boot state)');
ok(/"lightingstate1" "1"/.test(map), 'the lights are on in Radiant State 1 (powered)');
const skyg = read(path.join(root, 'source_data', 'tod_skybox.gdt'));
ok(skyg.includes('"tod_ssi_cybercity_dark" ( "ssi.gdf" )'), 'the pre-power SSI exists');
ok(fall.includes('level util::set_lighting_state( 0 );') && fall.includes('function power_wave()') && fall.includes('tod_crown_data::wave_orgs()'), 'the power wave flips the lighting state');
for (const t of ['function wave_orgs()', 'function wave_fx()']) ok(crown.includes(t), 'crown data emits ' + t);
const mats = read(path.join(root, 'source_data', 'tod_materials.gdt'));
for (const sfx of JSON.parse(read(path.join(root, 'tools', 'tod_black_materials.json'))).suffixes)
  ok(mats.includes(`"tod_black_${sfx}" ( "material.gdf" )`), 'black clone tod_black_' + sfx);
ok(map.includes('"target" "tod_sun_probe_target"') && map.includes('"targetname" "tod_sun_probe_target"'), 'sun-probe target + info_null (docs/162 T3)');
ok((map.match(/crown hall alarm (gantry|pendant|core)/g) || []).length === 2 && !map.includes('crown hall alarm core'), 'gantry and pendant support the modeled beacon; old cube removed');

if (fails) { console.error(`Doppelghast preflight FAILED: ${fails} of ${checks} checks`); process.exit(1); }
console.log(`Doppelghast preflight OK: ${checks} checks (aitype/model/clips at the tools root, AI tables, zone, audio table + wavs, the Fall wiring, the calm/alarm/siren)`);
