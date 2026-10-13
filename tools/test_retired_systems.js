'use strict';
// THE RETIREMENT PIN (W2E, 2026-10-05; user: "Just dont include assets not on this map in the build").
//
// Every parked / switched-off Map One system left the build WHOLE that day, its files moved to archive/map1_carryover/
// (see archive/map1_carryover/_landed_w2e.json): the crown finale / extraction (TOD_FINALE_PARKED 1), the Panzer (the
// vendored Spiki mechz pack), the Rogue Protector BOSS (the Civil Protector companion stays), the Apothicon Fury
// (_tod_reaver + the HB21 pack), the hellhound director (the dog aitypes stay: the Necromancer's soul hound), the
// armored sprinter, the Keeper at arena level 10 (his archetype half stays: the Dealer rides it), and the eight parked
// cards (SPRINT FIRE, SCAVENGER, FIRE RATE, HANDLING, RUN AND GUN, SECOND WIND, SOUL SIPHON, TRAILBLAZER).
//
// "Whole" is the contract this gate holds: no module, #using, call, zone line, alias row, image block, live
// add_domain or clientfield of a retired system may come back, and the shared pieces the live map still uses (the
// elite infra in _tod_bosses, the Dealer's archetype half of _tod_keeper, the crown props that replaced the finale's
// live half, the domain ids that stay mapped) must stay. Half a retirement is either dead weight or a white square.
// To bring one back, restore it whole from the archive and take its rows out of this file in the same edit.
//
// It also holds the DEAD READS out (GONE_READS): no live script may still ask about a retired system's state (the
// sprinter flag, the Panzer's flags, the finale's aggro / hold-out / sealed hall / lane lottery / song clock, the
// elite-director unlock stamp, SOUL SIPHON's hook, a retired elite's kind string) - nothing writes any of them now.
//
// Twelve negative controls at the bottom re-run the audit on a tree with one thing put back; each must be caught.
const fs = require('fs');
const path = require('path');

const R = path.resolve(__dirname, '..');
const MOD = 'scripts/zm/zm_tod2_cybercity/';

// ---- what retired -----------------------------------------------------------------------------------------------------
const GONE_FILES = [
  MOD + '_tod_finale.gsc', MOD + '_tod_reaver.gsc', MOD + '_tod_hellhounds.gsc', MOD + '_tod_sprinter.gsc',
  MOD + '_tod_runandgun.gsc', MOD + '_tod_keeper.csc',
  'scripts/zm/mechz_spiki.gsc', 'scripts/zm/mechz_spiki.csc',
  'scripts/zm/zm_genesis_apothicon_fury.gsc', 'scripts/zm/zm_genesis_apothicon_fury.csc', 'scripts/zm/zm_genesis_apothicon_fury.gsh',
  'scripts/shared/ai/archetype_apothicon_fury.gsc', 'scripts/shared/ai/archetype_apothicon_fury.csc',
  'scripts/shared/ai/archetype_apothicon_fury.gsh', 'scripts/shared/ai/archetype_apothicon_fury_interface.gsc',
  'sound_assets/tod/music/tod_music_finale.wav',
  'source_data/tod_ui_images/_images/i_tod_banner_finale.png', 'source_data/tod_ui_images/_images/i_tod_win_banner.png',
  'source_data/tod_ui_images/_images/i_tod_win_emblem.png', 'source_data/tod_ui_images/_images/i_tod_prompt_icon_extract.png',
  'source_data/tod_ui_images/_images/i_tod_prompt_icon_crown.png',
  'model_export/tod_cyber_zombie/tod_cyber_sprinter_lod0.xmodel_bin',
  'tools/keeper/test_keeper.js', 'tools/test_panzer_flame_fx.js',
];
// the retired modules' script paths (a #using of one is a compile against an archived file)
const GONE_MODULES = ['zm_tod2_cybercity\\_tod_finale', 'zm_tod2_cybercity\\_tod_reaver', 'zm_tod2_cybercity\\_tod_hellhounds',
  'zm_tod2_cybercity\\_tod_sprinter', 'zm_tod2_cybercity\\_tod_runandgun', 'scripts\\zm\\mechz_spiki',
  'scripts\\zm\\zm_genesis_apothicon_fury', 'scripts\\shared\\ai\\archetype_apothicon_fury'];
// the retired namespaces (a call into one is an unresolved external at load)
const GONE_NAMESPACES = ['tod_finale', 'tod_reaver', 'tod_hellhounds', 'tod_sprinter', 'tod_runandgun', 'mechz_spiki',
  'zm_genesis_apothicon_fury', 'apothiconfurybehavior', 'apothiconfuryinterface'];
// a zone line naming any of these packs a retired asset
const GONE_ZONE = ['mechz_spiki', 'apothicon_fury', '_tod_reaver', '_tod_hellhounds', '_tod_sprinter', 'tod_cyber_sprinter',
  '_tod_runandgun', '_tod_finale', 'spawner_tod_keeper', '_tod_keeper.csc', 'acc_zod_robot_boss', 'i_tod_win_',
  'i_tod_banner_finale', 'i_tod_prompt_icon_extract', 'i_tod_prompt_icon_crown', 'p7_out_mech_spawn_pad_light'];
const GONE_ALIASES = ['tod_music_finale', 'tod_sprint_ricochet', 'tod_scavenger', 'tod_trail_ignite', 'tod_trail_sizzle',
  'tod_trail_loop', 'tod_trail_loop_sm', 'fly_civil_protector_loop'];
const GONE_GDT = ['i_tod_banner_finale', 'i_tod_win_banner', 'i_tod_win_emblem', 'i_tod_prompt_icon_extract',
  'i_tod_prompt_icon_crown', 'tod_win_banner', 'tod_win_emblem',
  // the armored sprinter's roster variant (tools/install_cyber_roster.py no longer emits it)
  'tod_cyber_sprinter', 'tod_cyber_sprinter_head1', 'tod_cyber_sprinter_head2', 'tod_cyber_sprinter_head3',
  'mtl_tod_roster_armor_torso', 'mtl_tod_roster_armor_sleeves', 'mtl_tod_roster_armor_leftleg', 'mtl_tod_roster_armor_rightleg',
  'mtl_tod_roster_sprinter', 'i_tod_roster_sprinter_c', 'i_tod_roster_sprinter_n', 'i_tod_roster_sprinter_s',
  'i_tod_roster_sprinter_g', 'i_tod_roster_sprinter_e'];
// DEAD READS: a live line that still asks about a retired system is half a retirement (no writer is left for any of
// these: the sprinter flag, the Panzer's mechz flag, the finale's states, the lane lottery, the elite-director unlock
// stamp, SOUL SIPHON's hook, the retired elites' kind strings).
const GONE_READS = /\btod_is_sprinter\b|\bis_mechz\b|\bacc_is_panzer\b|\bacc_is_rogue_protector\b|\btod_finale_(aggro|holdout|spawn_floor|song_start|song_end|music|state)\b|\btod_crown_sealed\b|\btod_lane_seal_m(in|ax)s\b|\bbreather_unlock\b|\btod_enemy_unlock_round\b|\btod_cc_siphon_fn\b|\btod_panzer_|\btod_keeper_(rate|dr|boss)\b|tod_boss_kind\s*==\s*"(panzer|protector|reaver|hellhound|sprinter|keeper)"/;
// the parked cards: key -> the id that STAYS mapped (the id tables are append-only)
const GONE_DOMAINS = { sprintfire: 21, reserve: 8, firerate: 15, handling: 16, runandgun: 23, secondwind: 33, soulsiphon: 17, trailblazer: 46 };
// _tod_bosses: the Map One boss half that left, and the shared elite infra the live map still calls
const BOSSES_GONE_FN = ['director', 'boss_hp', 'grant_boss_reward', 'apply_player_mitigations', 'finale_pressure_start'];
const BOSSES_KEPT_FN = ['pick_spawn_point', 'elites_over_roof', 'elite_roof_all', 'grant_elite_reward', 'landing_kill_splash',
  'boss_pause_watch', 'boss_player_damage', 'rampage_hp_mult', 'frontier_blocks'];

// ---- the audit (pure over a reader, so the negative controls can hand it a mutated tree) -------------------------------
function codeOf(text, rel) {
  // the code part of every line: // (and Lua --) comments are history, not a reference
  const mk = rel.endsWith('.lua') ? '--' : '//';
  return text.split(/\r?\n/).map((l) => {
    let i = 0;
    for (;;) {
      const j = l.indexOf(mk, i);
      if (j < 0) return l;
      if ((l.slice(0, j).match(/"/g) || []).length % 2 === 0) return l.slice(0, j);
      i = j + mk.length;
    }
  }).join('\n');
}

function walk(io, dir, exts) {
  const out = [];
  for (const rel of io.list(dir)) if (exts.some((e) => rel.endsWith(e))) out.push(rel);
  return out;
}

function audit(io) {
  const bad = [];
  const fail = (m) => bad.push(m);

  // A. the retired files are gone from their live paths
  for (const f of GONE_FILES) if (io.exists(f)) fail('retired file is back at its live path: ' + f);

  // B. no script names a retired module or calls into a retired namespace
  for (const rel of walk(io, 'scripts', ['.gsc', '.csc', '.gsh'])) {
    const code = codeOf(io.read(rel), rel);
    for (const m of GONE_MODULES) if (new RegExp('#using\\s+[^;]*' + m.replace(/\\/g, '\\\\') + '\\s*;', 'i').test(code)) fail(rel + ' #uses the retired ' + m);
    for (const ns of GONE_NAMESPACES) if (new RegExp('\\b' + ns + '::', 'i').test(code)) fail(rel + ' calls into the retired namespace ' + ns + '::');
    if (/\btodFinaleWarn\b/.test(code)) fail(rel + ' still names the retired todFinaleWarn clientfield');
    const dead = code.match(GONE_READS);
    if (dead) fail(rel + ' still reads a retired system\'s state: ' + dead[0]);
  }

  // C. the zone packs nothing of them; the sound zone loads no Panzer table
  const zone = io.read('zone_source/zm_tod2_cybercity.zone');
  for (const g of GONE_ZONE) {
    const re = new RegExp('^[a-z_]+,[^\\n]*' + g.replace(/[.\\]/g, (c) => '\\' + c), 'mi');
    const hit = zone.match(re);
    if (hit) fail('zone line packs a retired asset: ' + hit[0].trim());
  }
  if (!/^scriptparsetree,scripts\/zm\/zm_tod2_cybercity\/_tod_crown_props\.gsc\s*$/m.test(zone)) fail('the crown props module (the finale\'s live half) is not zoned');
  if (!/^scriptparsetree,scripts\/zm\/zm_tod2_cybercity\/_tod_keeper\.gsc\s*$/m.test(zone)) fail('the Dealer\'s archetype half (_tod_keeper.gsc) left the zone');
  if (/"mechz_spiki"/.test(io.read('sound/zoneconfig/zm_tod2_cybercity.szc'))) fail('the sound zone still loads the Panzer\'s mechz_spiki table');
  // The Keeper's portal effect stays zoned only while a live script still plays it (the Dealer borrowed it for his
  // arrival until W2B gave him his own rift): a zoned effect nothing plays is the Keeper half-retired.
  if (/^fx,zombie\/fx_portal_keeper_spawn_os_zod_zmb\s*$/m.test(zone)
      && !walk(io, 'scripts', ['.gsc', '.csc', '.gsh']).some((rel) => codeOf(io.read(rel), rel).includes('fx_portal_keeper_spawn_os_zod_zmb')))
    fail('the zone packs the Keeper portal effect but no live script plays it: drop its fx,zombie/fx_portal_keeper_spawn_os_zod_zmb line');

  // D. no alias row, no image / material block
  for (const rel of walk(io, 'sound/aliases', ['.csv'])) {
    for (const line of io.read(rel).split(/\r?\n/)) {
      const name = line.split(',')[0];
      if (GONE_ALIASES.includes(name) || /^tod_sprint_ricochet/.test(name)) fail(rel + ' still defines the retired alias ' + name);
    }
  }
  for (const rel of walk(io, 'source_data', ['.gdt'])) {
    const t = io.read(rel);
    for (const n of GONE_GDT) if (t.includes('\t"' + n + '" (')) fail(rel + ' still carries the retired block ' + n);
  }

  // E. the parked cards: no live add_domain, no Lua row that still sells them; their ids stay mapped
  const upg = codeOf(io.read(MOD + '_tod_upgrades.gsc'), '.gsc');
  const ui = io.read(MOD + '_tod_upgrade_ui.gsc');
  const lua = io.read('ui/uieditor/menus/hud/tod_upgrade.lua');
  for (const [key, id] of Object.entries(GONE_DOMAINS)) {
    if (new RegExp('add_domain\\(\\s*"' + key + '"').test(upg)) fail('the retired card "' + key + '" is dealt again (a live add_domain)');
    if (!new RegExp('case "' + key + '":\\s*return ' + id + ';').test(ui)) fail('id ' + id + ' ("' + key + '") is no longer mapped - the id tables are APPEND-ONLY');
    const row = lua.match(new RegExp('^\\s*\\[' + id + '\\]\\s*=\\s*\\{\\s*name\\s*=\\s*"[^"]*",\\s*desc\\s*=\\s*"([^"]*)"', 'm'));
    if (!row) fail('tod_upgrade.lua lost DOMAIN row ' + id + ' (rows are id-keyed and nil-safe; keep it)');
    else if (row[1] !== 'REMOVED 2026-10-05') fail('tod_upgrade.lua DOMAIN row ' + id + ' still describes the retired card: "' + row[1] + '"');
  }
  if (/\bTodFinaleWarn\b/.test(codeOf(lua, '.lua'))) fail('tod_upgrade.lua still builds the retired finale road banner');

  // F. _tod_bosses: the Map One boss half stays gone, the live elite infra stays
  const bosses = io.read(MOD + '_tod_bosses.gsc');
  for (const f of BOSSES_GONE_FN) if (new RegExp('^function ' + f + '\\(', 'm').test(bosses)) fail('_tod_bosses carries the retired ' + f + '()');
  for (const f of BOSSES_KEPT_FN) if (!new RegExp('^function ' + f + '\\(', 'm').test(bosses)) fail('_tod_bosses lost the shared ' + f + '() the live map calls');

  // G. the Keeper: his boss half (system, clientfields, arena wave, toggle) is gone; the Dealer's archetype half stays
  const keeper = io.exists(MOD + '_tod_keeper.gsc') ? io.read(MOD + '_tod_keeper.gsc') : '';
  if (!keeper) fail('_tod_keeper.gsc (the Dealer\'s archetype half) is missing');
  else {
    if (/REGISTER_SYSTEM|clientfield::register/.test(codeOf(keeper, '.gsc'))) fail('_tod_keeper.gsc carries the retired boss half again (a system / clientfield)');
    if (!/^function keeper_blackboard\(/m.test(keeper)) fail('_tod_keeper.gsc lost keeper_blackboard (the Dealer\'s archetype rides it)');
  }
  const arena = codeOf(io.read(MOD + '_tod_arena.gsc'), '.gsc');
  if (/TOD_ARENA_HOUSE|TOD_ARENA_KEEPER_|function boss_wave\(|tod_keeper::/.test(arena)) fail('_tod_arena carries the retired Keeper wave / toggle again');

  // H. the entry: ONLY ZOMBIES holds, the crown props replaced the finale's live half
  const entry = io.read('scripts/zm/zm_tod2_cybercity.gsc');
  if (!/^\s*level\.tod_only_zombies = true;/m.test(entry)) fail('level.tod_only_zombies = true left the entry script');
  if (!/^\s*level thread tod_crown_props::init\(\);/m.test(codeOf(entry, '.gsc'))) fail('the entry script no longer runs tod_crown_props::init');

  return bad;
}

// ---- the real tree ----------------------------------------------------------------------------------------------------
function treeIO(root) {
  const io = {
    exists: (rel) => fs.existsSync(path.join(root, rel)),
    read: (rel) => fs.readFileSync(path.join(root, rel), 'utf8'),
    list: (dir) => {
      const out = [];
      const go = (d) => {
        let ents = [];
        try { ents = fs.readdirSync(path.join(root, d), { withFileTypes: true }); } catch (e) { return; }
        for (const e of ents) {
          const rel = d + '/' + e.name;
          if (e.isDirectory()) go(rel); else out.push(rel);
        }
      };
      go(dir);
      return out;
    },
  };
  return io;
}

function overlay(io, edits) {
  // edits: { rel: text | null (deleted) | true (exists, empty) }
  return {
    exists: (rel) => (rel in edits ? edits[rel] !== null : io.exists(rel)),
    read: (rel) => (rel in edits ? (edits[rel] === true ? '' : edits[rel]) : io.read(rel)),
    list: (dir) => {
      const base = io.list(dir).filter((r) => !(r in edits) || edits[r] !== null);
      for (const r of Object.keys(edits)) if (r.startsWith(dir + '/') && edits[r] !== null && !base.includes(r)) base.push(r);
      return base;
    },
  };
}

const real = treeIO(R);
const problems = audit(real);
if (problems.length) {
  for (const p of problems) console.error('RETIRED: ' + p);
  console.error('test_retired_systems: FAIL (' + problems.length + '). A retired Map One system came back, or a piece the live map shares left. Retire whole or restore whole (archive/map1_carryover/).');
  process.exit(1);
}

// ---- negative controls: put ONE thing back, the audit must catch it ---------------------------------------------------
const entry = real.read('scripts/zm/zm_tod2_cybercity.gsc');
const zone = real.read('zone_source/zm_tod2_cybercity.zone');
const upg = real.read(MOD + '_tod_upgrades.gsc');
const bosses = real.read(MOD + '_tod_bosses.gsc');
const keeper = real.read(MOD + '_tod_keeper.gsc');
const uiCsv = real.read('sound/aliases/tod_ui.csv');
const NEG = [
  ['a #using of the Fury director', { 'scripts/zm/zm_tod2_cybercity.gsc': entry.replace(/^(#using [^\n]*\n)/m, '$1#using scripts\\zm\\zm_tod2_cybercity\\_tod_reaver;\n') }, 'retired zm_tod2_cybercity\\_tod_reaver'],
  ['the finale zoned again', { 'zone_source/zm_tod2_cybercity.zone': zone + '\nscriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_finale.gsc\n' }, 'zone line packs a retired asset'],
  ['TRAILBLAZER dealt again', { [MOD + '_tod_upgrades.gsc']: upg + '\nfunction x() { add_domain( "trailblazer", "TRAILBLAZER", "x", 5, array( "assault" ), 1 ); }\n' }, 'the retired card "trailblazer" is dealt again'],
  ['the finale song row back', { 'sound/aliases/tod_ui.csv': uiCsv + 'tod_music_finale,,tod/music/tod_music_finale.wav\n' }, 'retired alias tod_music_finale'],
  ['the sprinter module back', { [MOD + '_tod_sprinter.gsc']: true }, 'retired file is back at its live path'],
  ['ONLY ZOMBIES dropped', { 'scripts/zm/zm_tod2_cybercity.gsc': entry.replace(/level\.tod_only_zombies = true;/, 'level.tod_only_zombies = false;') }, 'tod_only_zombies = true left'],
  ['the shared landing splash cut with the bosses', { [MOD + '_tod_bosses.gsc']: bosses.replace(/^function landing_kill_splash\(/m, 'function landing_kill_splash_x(') }, 'lost the shared landing_kill_splash()'],
  ['the Keeper\'s boss half back', { [MOD + '_tod_keeper.gsc']: keeper + '\nfunction __init__() { clientfield::register( "actor", "tod_keeper_fx", 1, 1, "int" ); }\n' }, 'carries the retired boss half again'],
  ['a dead sprinter read back', { [MOD + '_tod_keeper.gsc']: keeper + '\nfunction x( e ) { return IS_TRUE( e.tod_is_sprinter ); }\n' }, 'reads a retired system\'s state: tod_is_sprinter'],
  ['the finale aggro branch back', { [MOD + '_tod_keeper.gsc']: keeper + '\nfunction y() { if ( IS_TRUE( level.tod_finale_aggro ) ) return; }\n' }, 'reads a retired system\'s state: tod_finale_aggro'],
  ['the sprinter roster block back', { 'source_data/tod_cyber_roster.gdt': real.read('source_data/tod_cyber_roster.gdt') + '\t"tod_cyber_sprinter" ( "xmodel.gdf" )\n\t{\n\t}\n' }, 'still carries the retired block tod_cyber_sprinter'],
  ['the Keeper portal zoned with nothing playing it', portalNeg(), 'packs the Keeper portal effect but no live script plays it'],
];
// the zone packs the portal line while every script that names the portal is stripped of it (whichever way the
// Dealer's arrival is wired when this runs)
function portalNeg() {
  const edits = { 'zone_source/zm_tod2_cybercity.zone': zone.replace(/^fx,zombie\/fx_portal_keeper_spawn_os_zod_zmb\s*$/m, '') + '\nfx,zombie/fx_portal_keeper_spawn_os_zod_zmb\n' };
  for (const rel of walk(real, 'scripts', ['.gsc', '.csc', '.gsh'])) {
    const t = real.read(rel);
    if (t.includes('fx_portal_keeper_spawn_os_zod_zmb')) edits[rel] = t.split('fx_portal_keeper_spawn_os_zod_zmb').join('fx_x');
  }
  return edits;
}
let caught = 0;
for (const [name, edits, want] of NEG) {
  const got = audit(overlay(real, edits));
  if (!got.some((m) => m.includes(want))) {
    console.error('test_retired_systems: negative control "' + name + '" was NOT caught (wanted: ' + want + '; got: ' + JSON.stringify(got) + ')');
    process.exit(1);
  }
  caught++;
}
console.log('test_retired_systems: ' + GONE_FILES.length + ' retired files, ' + GONE_ZONE.length + ' zone names, ' + GONE_ALIASES.length + ' aliases, '
  + Object.keys(GONE_DOMAINS).length + ' parked cards stay retired; the shared elite infra, the Dealer\'s archetype half and the crown props stay live; '
  + caught + ' negative controls caught. PASS');
