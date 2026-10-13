#!/usr/bin/env node
// test_dealer.js - THE DEALER boss asset contract (docs/199), a build gate.
//
// Static checks on the files that must agree for the boss character to load:
//   1. the export manifest, the install manifest and the files on disk agree (hashes)
//   2. every clip the anim mapping table names is one we ship (Keeper or Dealer) or a stock one
//      and every Dealer row names an AUTHORED clip (tod_dealer_f_* float set / tod_dealer_g_* ground set)
//   3. every script-only alias the design relies on is in the mapping table (the Mangler lesson:
//      an %anim outside the table does not load)
//   4. the selector table references only aliases the mapping table defines
//   5. the aitype chain points at the Dealer tables, the Dealer character and the Dealer archetype
//   6. the behavior tree's death StartFunction is the Dealer's, and every other function is stock
//      or Keeper-registered (the Dealer script must register dealerDeathStart before a spawn)
//   7. the GDT defines every material the three binaries name, every image those materials
//      name, both bodies, the scythe and both weapon models
//   8. the zone (if wired) lists the aitype, the five models and the 45 authored clips (never a raw pack clip)
//   9. HIS SOUNDS (W2B / PK10): every "Sound" note on his clips names HIS alias (tod_dealer.csv), none the Keeper
//      Protector's (DLC4 aliases nothing here defines = silence), the melee hit's Self Notify untouched
//  10. HIS LOOK (W2B / PK11): every effect the module plays is precached, generated and (once wired) zoned; every one
//      rides a carrier; the borrowed Keeper portal and skull scream are gone; the hum, the dissolve and the hit ring
'use strict';
const fs = require('fs');
const path = require('path');
const REPO = path.resolve(__dirname, '..', '..');
const R = p => fs.readFileSync(path.join(REPO, p), 'utf8').replace(/\r\n/g, '\n');
const EX = p => fs.existsSync(path.join(REPO, p));
let fails = 0, passes = 0;
function ok(cond, what) { if (cond) { passes++; return; } fails++; console.log('FAIL ' + what); }

const exportMan = JSON.parse(R('art/dealer_boss/engine_kit/export_manifest.json'));
const installMan = JSON.parse(R('model_export/tod_dealer/install_manifest.json'));
const gdt = R('source_data/tod_dealer.gdt');
const keeperGdt = R('source_data/tod_keeper.gdt');
const combatGdt = R('source_data/tod_dealer_combat.gdt');
const blocks = {};
for (const m of (gdt + keeperGdt).matchAll(/^\t"([^"]+)" (?:\( "([^"]+)" \)|\[ "([^"]+)" \])/gm)) blocks[m[1]] = m[2] ? m[2].replace(/\.gdf$/, '') : 'child';

// 1. manifests vs disk
const crypto = require('crypto');
const sha = p => crypto.createHash('sha256').update(fs.readFileSync(path.join(REPO, p))).digest('hex');
for (const lod of exportMan.lods.filter(l => l.lod === 0)) ok(EX(lod.file) && sha(lod.file) === lod.sha256, '1 lod0 binary matches the export manifest: ' + lod.file);
for (const [png, h] of Object.entries(exportMan.textures)) ok(EX('model_export/tod_dealer/_images/' + png) && sha('model_export/tod_dealer/_images/' + png) === h, '1 atlas on disk: ' + png);
for (const [f, h] of Object.entries(installMan.files)) ok(EX(f) && sha(f) === h, '1 installed file matches: ' + f);
ok(installMan.master_sha256 === exportMan.master_sha256, '1 install was run against the current export (master sha)');

// 2.-3. anim mapping table
const am = R('animtables/tod_dealer.ai_am').split('\n').filter(l => l && !l.startsWith('#'));
const aliases = new Map();
for (const row of am) { const c = row.split(',').map(s => s.trim()).filter(Boolean); aliases.set(c[0], c.slice(1)); }
const shipped = new Set([...(keeperGdt + combatGdt).matchAll(/^\t"([^"]+)" \( "xanim\.gdf" \)/gm)].map(m => m[1]).concat([...gdt.matchAll(/^\t"([^"]+)" \( "xanim\.gdf" \)/gm)].map(m => m[1])));
const STOCK_CLIP = /^(ai_zombie_base_|void$)/;   // base zombie clips live in the tools root; void is the debug selector
for (const [alias, clips] of aliases) for (const c of clips) ok(shipped.has(c) || STOCK_CLIP.test(c), '2 mapping clip is shipped or stock: ' + alias + ' -> ' + c);
for (const [alias, clip] of Object.entries(installMan.script_aliases)) ok(aliases.has(alias) && aliases.get(alias)[0] === clip, '3 script alias in the table: ' + alias);
for (const c of installMan.clips) ok(shipped.has(c), '3 new clip has a GDT block: ' + c);
// THE TWO STATES ride the arms position: ARMS_UP (state one, levitating, scythe) = the authored float set,
// ARMS_DOWN (state two, the cracked mask, machine gun) = the authored ground set. Never a raw Keeper clip on a Dealer row.
for (const v of [0, 1, 2, 3]) {
  ok(aliases.get('anim_zombie_walk_au_v' + v)[0] === 'tod_dealer_f_walk', '3 WALK up = the authored float stride');
  ok(aliases.get('anim_zombie_run_au_v' + v)[0] === 'tod_dealer_f_run', '3 RUN up = the authored float run');
  ok(aliases.get('anim_zombie_sprint_au_v' + v)[0] === 'tod_dealer_f_sprint', '3 SPRINT up = the authored float sprint');
  ok(aliases.get('anim_zombie_walk_ad_v' + v)[0] === 'tod_dealer_g_ens_run_v1', '3 WALK down = the authored ground run');
  ok(aliases.get('anim_zombie_sprint_ad_v' + v)[0] === 'tod_dealer_g_ens_sprint_v1', '3 SPRINT down = the authored ground sprint');
}
ok((aliases.get('anim_zombie_melee_walk_au') || []).length === 2 && aliases.get('anim_zombie_melee_walk_au').every(c => c.startsWith('tod_dealer_f_')), '3 two scythe cuts in state one');
ok((aliases.get('anim_zombie_melee_walk_ad') || []).length === 7 && aliases.get('anim_zombie_melee_walk_ad').every(c => c.startsWith('tod_dealer_g_')), '3 seven ground swipes in state two');
ok((aliases.get('anim_zombie_melee_run_ad') || []).length === 5, '3 five ground run-swipes');
ok(aliases.get('anim_dealer_idle_ground')[0] === 'tod_dealer_g_ens_idle', '3 the ground idle alias');
ok(aliases.get('anim_zombie_keeper_idle').every(c => c.startsWith('tod_dealer_f_idle')), '3 the float idles');
for (const side of ['front', 'back', 'left', 'right']) ok((aliases.get('anim_zombie_death_' + side) || []).every(c => c.startsWith('tod_dealer_g_ens_dth_')), '3 deaths are the ground set: ' + side);
for (const [alias, clip] of aliases) if (alias.startsWith('anim_dealer_') || /^anim_zombie_((walk|run|sprint)_(au|ad)_v\d(_pain_chest_f)?|melee_(walk|run)_(au|ad)|keeper_idle|death_front|super_sprint)$/.test(alias))
  for (const c of clip) ok(c.startsWith('tod_dealer_'), '3 no raw Keeper clip on a Dealer row: ' + alias + ' -> ' + c);
// the authored files on disk are the ones the report and the manifest describe
for (const [name, h] of Object.entries(installMan.authored)) ok(EX('xanim_export/tod_dealer/' + name + '.xanim_bin') && sha('xanim_export/tod_dealer/' + name + '.xanim_bin') === h, '3 authored clip on disk: ' + name);
ok(Object.keys(installMan.authored).length === 45, '3 forty-five authored clips');
for (const src of installMan.source_clips) ok(!EX('xanim_export/tod_dealer/' + src + '.xanim_bin'), '3 no raw pack clip ships beside the authored ones: ' + src);

// 4. selector table aliases + the state rows
const ast = R('animtables/tod_dealer.ai_ast');
for (const m of ast.matchAll(/\b(ANIM_[A-Z0-9_]+)\b/g)) ok(aliases.has(m[1].toLowerCase()), '4 selector alias is mapped: ' + m[1]);
const sel = name => { const i = ast.indexOf(name + '\n'); return ast.slice(i, ast.indexOf('\n,\n', i)).split('\n'); };
const idle = sel('idle@zombie'), move = sel('move@zombie');
ok(idle.some(r => r.startsWith('ARMS_UP,') && r.includes('ANIM_ZOMBIE_KEEPER_IDLE')) && idle.some(r => r.startsWith('ARMS_DOWN,') && r.includes('ANIM_DEALER_IDLE_GROUND')), '4 idle selector splits on the arms position');
ok(move[1].startsWith('_arms_position,_locomotion_speed,'), '4 move selector keys on the arms position');
ok(move.filter(r => r.startsWith('ARMS_UP,')).length === 13 && move.filter(r => r.startsWith('ARMS_DOWN,')).length === 13, '4 thirteen move rows per state');
ok(move.some(r => r.startsWith('ARMS_DOWN,') && r.includes('_AD_')) && !move.some(r => r.startsWith('ARMS_DOWN,') && r.includes('_AU_')), '4 ARMS_DOWN rows use the AD aliases');
ok(move.some(r => r.startsWith('ARMS_DOWN,') && r.includes('ANIM_DEALER_SUPER_SPRINT_GROUND')), '4 super sprint has a ground row');
// THE LINKER'S RULE (2026-10-01): every clip a move@zombie row names must be a "looping" xanim, or every linker on
// the shared root aborts before packing the .ff (it did, at 10:39, on tod_dealer_f_walk)
const loopingOf = (name, field) => { field = field || 'looping'; const all = gdt + keeperGdt; const head = '\t"' + name + '" ( "xanim.gdf" )'; const i = all.indexOf(head); if (i < 0) return null; const j = all.indexOf('\n\t}', i); const f = all.slice(i, j).match(new RegExp('"' + field + '" "([^"]*)"')); return f ? f[1] : '0'; };
const rowClips = rows => { const out = new Set(); for (const row of rows.slice(2)) for (const m of row.matchAll(/\b(ANIM_[A-Z0-9_]+)\b/g)) for (const c of (aliases.get(m[1].toLowerCase()) || [])) out.add(c); return out; };
const moveClips = rowClips(move), noLoopClips = new Set([...rowClips(idle), ...rowClips(sel('melee@zombie'))]);
ok(moveClips.size >= 5 && noLoopClips.size >= 6, '4 selector rows reach clips (move ' + moveClips.size + ', idle+melee ' + noLoopClips.size + ')');
for (const c of moveClips) {
  ok(loopingOf(c) === '1', '4 move@zombie clip is looping: ' + c + ' (looping=' + loopingOf(c) + ')');
  ok(loopingOf(c, 'loopsync') === '1', '4 move@zombie clip is loop-synced: ' + c);
}
// AND THE OTHER WAY (build 4, 11:55): idle@zombie / melee@zombie rows "require non-looping" and "non-loop sync" clips;
// the pack's Protector idle_attack blocks ship looping 1, so the installer must force them off
for (const c of noLoopClips) {
  ok(!moveClips.has(c), '4 clip is not on both a move row and an idle/melee row: ' + c);
  ok(loopingOf(c) !== '1', '4 idle/melee clip is NOT looping: ' + c + ' (looping=' + loopingOf(c) + ')');
  ok(loopingOf(c, 'loopsync') !== '1', '4 idle/melee clip is NOT loop-synced: ' + c);
}

// 5. aitype chain
const arche = (gdt.match(/"archetype_tod_dealer" \( "aitype\.gdf" \)[\s\S]*?\n\t\}/) || [''])[0];
ok(/"animMappingTableName" "tod_dealer\.ai_am"/.test(arche) && /"animSelectorTableName" "tod_dealer\.ai_ast"/.test(arche) &&
   /"animStateMachineName" "tod_dealer\.ai_asm"/.test(arche) && /"behaviorTreeName" "tod_dealer\.ai_bt"/.test(arche), '5 archetype names the Dealer tables');
ok(/"character1" "c_tod_dealer"/.test(arche) && /"archetype" "dealer"/.test(arche), '5 archetype is "dealer" with c_tod_dealer');
ok(blocks['variant_tod_dealer'] === 'child' && blocks['spawner_tod_dealer'] === 'child', '5 variant and spawner blocks exist');
ok(/"c_tod_dealer" \( "character\.gdf" \)[\s\S]*?"body" "tod_dealer_body"/.test(gdt), '5 character body is tod_dealer_body');

// 6. behavior tree
const bt = JSON.parse(R('share/raw/behavior/tod_dealer.ai_bt'));
const fns = new Set();
(function walk(n) { for (const k of ['scriptFunction', 'StartFunction', 'UpdateFunction', 'TerminateFunction', 'ActionName']) if (n[k]) fns.add(n[k].toLowerCase()); (n.children || []).forEach(walk); })(bt);
ok(fns.has('dealerdeathstart') && !fns.has('genesiskeeperdeathstart'), '6 death StartFunction is dealerDeathStart');
const STOCK = new Set(['disablerepath', 'enablerepath', 'locomotionshouldtraverse', 'startragdoll', 'wascrushedbyinterdimensionalgunblackhole',
  'waskilledbyinterdimensionalgun', 'zombiedeathaction', 'zombiefindfleshservice', 'zombieidgundeathupdate', 'zombieshouldmelee', 'zombieshouldmove',
  'zombieshouldmoveaway', 'zombieshouldproceduraltraverse', 'zombieshouldstun', 'zombiestunactionend', 'zombiestunactionstart', 'defaultaction',
  'zombieidleaction', 'zombiemoveaction', 'zombiemoveaway', 'zombietraverseaction', 'dealerdeathstart']);
for (const f of fns) ok(STOCK.has(f), '6 tree function is stock or the Dealer\'s: ' + f);
const dealerGsc = 'scripts/zm/zm_tod2_cybercity/_tod_dealer_finale.gsc';
if (EX(dealerGsc)) ok(/RegisterBehaviorTreeScriptAPI\(\s*"dealerDeathStart"/.test(R(dealerGsc)), '6 the Dealer script registers dealerDeathStart');
else console.log('note: ' + dealerGsc + ' not written yet - the tree death function is unregistered until it is');

// 7. GDT coverage of the binaries' materials, their images, the models
const ALL_MATS = new Set(exportMan.lods.flatMap(l => l.materials));
const STOCK_MAT = new Set(['mtl_wpn_t7_paint_left', 'mtl_wpn_t7_paint_right', 'mtl_wpn_t7_paint_top']);
for (const m of ALL_MATS) ok(blocks[m] === 'material' || STOCK_MAT.has(m), '7 material block for ' + m);
for (const m of [...gdt.matchAll(/^\t"(mtl_[^"]+)" \( "material\.gdf" \)([\s\S]*?)\n\t\}/gm)]) {
  for (const img of m[2].matchAll(/"(?:colorMap|normalMap|specColorMap|cosinePowerMap|colorMap00|colorMap01|occMap)" "(i_[^"$]+)"/g))
    ok(blocks[img[1]] === 'image', '7 image block for ' + m[1] + ' -> ' + img[1]);
}
for (const x of ['tod_dealer_body', 'tod_dealer_body_cracked', 'tod_dealer_scythe', ...Object.values(installMan.weapon_models)]) ok(blocks[x] === 'xmodel', '7 xmodel block ' + x);
ok(/"tod_dealer_body" \( "xmodel\.gdf" \)[\s\S]*?"filename" "tod_dealer\\\\tod_dealer_lod0\.xmodel_bin"/.test(gdt), '7 body filename is the masked lod0');
ok(/"tod_dealer_body_cracked" \( "xmodel\.gdf" \)[\s\S]*?"filename" "tod_dealer\\\\tod_dealer_cracked_lod0\.xmodel_bin"/.test(gdt), '7 cracked filename');
// 7b. HIS OWN FACE (user 2026-10-02): nothing of any borrowed character ships. The cracked body carries ONLY the three
// Dealer materials (same bake as the masked one); no donor head material, image or model anywhere in the GDT, the
// manifests or the zone; the old unmasked body is gone whole.
for (const l of exportMan.lods) ok(l.materials.every(m => /^mtl_tod_dealer_(body|head|hands|scythe)$/.test(m)), '7b body materials are the Dealer\'s own only: ' + l.file);
for (const [name, text] of [['gdt', gdt], ['export manifest', JSON.stringify(exportMan)], ['install manifest', JSON.stringify(installMan)]])
  ok(!/richtofen|c_zom_der_|mtl_c_gen_|_unmasked/i.test(text), '7b no borrowed head and no unmasked body in the ' + name);
ok(exportMan.states && exportMan.states.masked === 'tod_dealer' && exportMan.states.cracked === 'tod_dealer_cracked', '7b the export names the two states');
const crackedLod0 = exportMan.lods.find(l => l.model === 'tod_dealer_cracked' && l.lod === 0), maskedLod0 = exportMan.lods.find(l => l.model === 'tod_dealer' && l.lod === 0);
ok(crackedLod0 && maskedLod0 && crackedLod0.meshes.head.state_faces_dropped > 1000 && maskedLod0.meshes.head.state_faces_dropped > 1000, '7b each state drops the other state\'s mask faces');
ok(crackedLod0 && maskedLod0 && crackedLod0.meshes.body.faces === maskedLod0.meshes.body.faces && crackedLod0.meshes.hands.faces === maskedLod0.meshes.hands.faces, '7b body and hands are identical across the two states');

// 8. zone wiring (only once wire.py has run)
const zone = R('zone_source/zm_tod2_cybercity.zone');
if (zone.includes('aitype,spawner_tod_dealer')) {
  const lines = new Set(zone.split('\n').map(l => l.trim()));
  for (const l of ['aitype,spawner_tod_dealer', 'xmodel,tod_dealer_body', 'xmodel,tod_dealer_body_cracked', 'xmodel,tod_dealer_scythe', ...Object.values(installMan.weapon_models).map(v => 'xmodel,' + v), ...installMan.clips.map(c => 'xanim,' + c)])
    ok(lines.has(l), '8 zone line ' + l);
  ok(!lines.has('xmodel,tod_dealer_body_unmasked') && !zone.toLowerCase().includes('richtofen'), '8 the old unmasked body is not zoned');
  if (false) for (const l of [])
    ok(lines.has(l), '8 zone line ' + l);
  for (const src of installMan.source_clips) ok(!lines.has('xanim,' + src), '8 no raw pack clip zoned: ' + src);
  if (false) for (const l of [])
    ok(lines.has(l), '8 zone line ' + l);
} else console.log('note: zone not wired yet (tools/dealer_boss/wire.py, right before the build)');

// 9. HIS SOUNDS ON HIS CLIPS (W2B / PK10): tools/dealer_boss/install.py NOTE_ALIASES remaps the pack's Sound notes
const soundNotes = text => {
  const out = [];
  for (const m of text.matchAll(/^\t"(tod_dealer_[fg]_[^"]+)" \( "xanim\.gdf" \)\n\t\{\n([\s\S]*?)\n\t\}/gm)) {
    const f = Object.fromEntries([...m[2].matchAll(/^\t\t"([^"]+)" "([^"]*)"/gm)].map(x => [x[1], x[2]]));
    for (const [k, v] of Object.entries(f)) {
      const n = k.match(/^((?:sound_)?customnote\d+)action$/);
      if (n && v !== 'None') out.push({ clip: m[1], note: n[1], action: v, alias: f[n[1] + 'actionparam1'] || '' });
    }
  }
  return out;
};
const DEALER_CSV = EX('sound/aliases/tod_dealer.csv') ? R('sound/aliases/tod_dealer.csv') : '';
const dealerAliases = new Set(DEALER_CSV.split('\n').slice(1).map(l => l.split(',')[0]).filter(Boolean));
const OLD_NOTE = /keeperprot|keeper_teleport|keeper_spawn|^zombie_melee$|^footstep_(left|right)_large$/;
const notesProblems = list => {
  const bad = [];
  for (const n of list.filter(n => n.action === 'Sound')) {
    if (OLD_NOTE.test(n.alias)) bad.push(n.clip + ' ' + n.note + ' still names ' + n.alias);
    if (n.alias.startsWith('tod_dealer_') && !dealerAliases.has(n.alias)) bad.push(n.clip + ' ' + n.note + ' names ' + n.alias + ', which tod_dealer.csv does not define');
  }
  return bad;
};
const notes = soundNotes(gdt);
const nbad = notesProblems(notes);
ok(dealerAliases.size >= 11, '9 tod_dealer.csv defines his aliases (' + dealerAliases.size + ')');
ok(nbad.length === 0, '9 every Sound note on his clips names his own defined alias: ' + nbad.slice(0, 3).join('; '));
const has = (clip, alias) => notes.some(n => n.clip === clip && n.action === 'Sound' && n.alias === alias);
for (const c of ['tod_dealer_f_idle_attack_left', 'tod_dealer_f_idle_attack_right'])
  ok(has(c, 'tod_dealer_scythe_swing') && has(c, 'tod_dealer_attack_vox'), '9 the scythe cut carries the swing and his effort: ' + c);
for (const c of ['tod_dealer_g_ens_attack_v1', 'tod_dealer_g_ens_attack_v2', 'tod_dealer_g_ens_attack_v3', 'tod_dealer_g_ens_attack_v4', 'tod_dealer_g_zod_attack_v1', 'tod_dealer_g_zod_attack_v2', 'tod_dealer_g_zod_attack_v4'])
  ok(has(c, 'tod_dealer_bash') && notes.some(n => n.clip === c && n.action === 'Self Notify' && n.alias === 'zombie_melee'),
     '9 a state-two swing carries the bash AND keeps its zombie_melee hit (Self Notify): ' + c);
ok(has('tod_dealer_g_ens_run_v1', 'tod_dealer_step') && has('tod_dealer_g_ens_sprint_v1', 'tod_dealer_step'), '9 his boots on the state-two run and sprint');
ok(has('tod_dealer_f_bamf_in', 'tod_dealer_bamf_out') && has('tod_dealer_f_bamf_out', 'tod_dealer_bamf_in'), '9 the bamf clips play his rift (bamf_in = he vanishes)');
{
  const planted = gdt.replace('"customnote6actionparam1" "tod_dealer_scythe_swing"', '"customnote6actionparam1" "zmb_keeperprot_attack"');
  ok(planted !== gdt && notesProblems(soundNotes(planted)).length > 0, '9 NEGATIVE: a Keeper alias planted back on a clip is caught');
  const undef = gdt.replace('"tod_dealer_scythe_swing"', '"tod_dealer_scythe_swingx"');
  ok(notesProblems(soundNotes(undef)).length > 0, '9 NEGATIVE: a note naming an alias tod_dealer.csv does not define is caught');
}
const installPy = R('tools/dealer_boss/install.py');
ok(/def remap_sound_notes\(blk\)/.test(installPy) && /b, _ = remap_sound_notes\(b\)/.test(installPy), '9 install.py remaps the notes of every authored clip block it writes');
const noteAliasesBlock = (installPy.match(/NOTE_ALIASES = \{([\s\S]*?)\n\}/) || [])[1];
ok(!!noteAliasesBlock, '9 the sound-note mapping dictionary exists');
for (const m of noteAliasesBlock.matchAll(/^    '([^']+)': '(tod_dealer_[a-z_]+)',/gm)) ok(dealerAliases.has(m[2]), '9 NOTE_ALIASES target is defined: ' + m[1] + ' -> ' + m[2]);

// 10. HIS LOOK + HIS SOUND IN THE MODULE (W2B / PK10 + PK11)
if (EX(dealerGsc)) {
  const G = R(dealerGsc);
  const defs = Object.fromEntries([...G.matchAll(/^#define\s+(\w+)\s+"([^"]+)"/gm)].map(m => [m[1], m[2]]));
  const fxDefs = Object.entries(defs).filter(([k]) => k.startsWith('TOD_DEALER_FX_'));
  ok(fxDefs.length === 8, '10 eight effects named (' + fxDefs.length + ')');
  for (const [k, v] of fxDefs) {
    ok(G.includes('#precache( "fx", "' + v + '" );'), '10 precached: ' + v);
    ok(EX('share/raw/fx/' + v + '.efx'), '10 generated (tools/dealer_fx/gen_fx.py): ' + v);
    ok(new RegExp('\\b' + k + '\\b').test(G.replace(/^#define.*$/gm, '')), '10 played: ' + k);
  }
  ok(!/fx_portal_keeper_spawn_os_zod_zmb|evt_zombie_skull_scream/.test(G), '10 the borrowed Keeper portal and skull scream are gone');
  ok((G.match(/PlayFXOnTag\(/g) || []).length === 1 && G.includes('PlayFXOnTag( fx, self, "tag_origin" );') && !/\bPlayFX\(/.test(G),
     '10 every effect rides a carrier (one PlayFXOnTag, on the carrier\'s tag_origin; no bare PlayFX)');
  ok(G.includes('LinkTo( self, tag, offset, ( 0, 0, 0 ) )') && G.includes('if ( !isdefined( self GetTagOrigin( tag ) ) )'), '10 a linked carrier is bone-guarded');
  const fnBody = name => (G.match(new RegExp('^function ' + name + '\\([^)]*\\)\\s*\\n\\{([\\s\\S]*?)\\n\\}', 'm')) || ['', ''])[1];
  const sp = fnBody('spawn_boss'), mc = fnBody('mask_crack'), dw = fnBody('death_watch'), cc = fnBody('corpse_cleanup'), hit = fnBody('dealer_hit_cb');
  ok(/TOD_DEALER_FX_ARRIVE/.test(sp) && /TOD_DEALER_SND_SPAWN/.test(sp) && /aura_set\( 1 \)/.test(sp) && /PlayLoopSound\( TOD_DEALER_SND_HUM/.test(sp), '10 the arrival: the rift, its sound, the shadow, the hum');
  ok(/TOD_DEALER_FX_SHATTER/.test(mc) && /TOD_DEALER_FX_EYE_DIE/.test(mc) && /aura_set\( 2 \)/.test(mc) && /StopLoopSound/.test(mc) && /TOD_DEALER_SND_CRACK/.test(mc), '10 the crack: the shatter at the face, the eye, the hot shadow, the hum dies, the crack');
  ok(/aura_set\( 0 \)/.test(dw) && /StopLoopSound/.test(dw) && /TOD_DEALER_FX_DEATH/.test(dw) && /TOD_DEALER_SND_DEATH/.test(dw) && dw.indexOf('TOD_DEALER_FX_DEATH') < dw.indexOf('grant_elite_reward'), '10 the death: the shadow off, the burst and the scream BEFORE the reward');
  ok(/TOD_DEALER_FX_DISSOLVE/.test(cc) && cc.indexOf('TOD_DEALER_FX_DISSOLVE') < cc.indexOf('self Delete()'), '10 the body burns away and is deleted under the dissolve');
  const genFx = EX('tools/dealer_fx/gen_fx.py') ? R('tools/dealer_fx/gen_fx.py') : '';
  const delMs = (genFx.match(/^DISSOLVE_DELETE_MS = (\d+)/m) || [])[1];
  const dsecs = (G.match(/^#define TOD_DEALER_DISSOLVE_SECS\s+([\d.]+)/m) || [])[1];
  ok(delMs && dsecs && Math.abs(+delMs / 1000 - +dsecs) < 1e-6, 'LOCKSTEP 10 the dissolve\'s last billow lands on the delete (gen_fx ' + delMs + ' ms, gsc ' + dsecs + ' s)');
  ok(G.includes('ArrayInsert( level.player_damage_callbacks, &dealer_hit_cb, 0 );') && !!hit && (hit.match(/return [^;]+;/g) || []).every(r => r === 'return -1;') && !/\bwait\b/.test(hit),
     '10 the hit ring is a read-only first listener (every path returns -1, never a wait)');
  ok(/TOD_DEALER_SND_HIT\b/.test(hit) && /tod_dealer_state == 2[\s\S]*TOD_DEALER_SND_HIT_BASH/.test(hit),
     '10 the ring follows his weapon: the blade in state one, the blunt stock in state two');
  ok(/rift Delete\(\)/.test(sp) && sp.indexOf('TOD_DEALER_SND_SPAWN') > sp.indexOf('SpawnActor('),
     '10 a failed spawn withdraws the rift and plays no tear (the house retries every 2 s)');
  for (const k of ['TOD_DEALER_SND_SPAWN', 'TOD_DEALER_SND_CRACK', 'TOD_DEALER_SND_DEATH', 'TOD_DEALER_SND_HIT', 'TOD_DEALER_SND_HIT_BASH', 'TOD_DEALER_SND_HUM'])
    ok(defs[k] && dealerAliases.has(defs[k]), '10 his sound is defined in tod_dealer.csv: ' + k + ' = ' + defs[k]);
  {
    // the hum is an entity loop: it must also die with him on any exit path the script never sees (tod_jt_jet's shape)
    const csvRows = DEALER_CSV.split(/\r?\n/);
    const hdr = (csvRows[0] || '').split(',');
    const hum = (csvRows.find(l => l.startsWith((defs.TOD_DEALER_SND_HUM || '#') + ',')) || '').split(',');
    ok(hum[hdr.indexOf('Looping')] === 'LOOPING' && hum[hdr.indexOf('StopOnEntDeath')] === 'yes', '10 the hum loops and dies with him (LOOPING, StopOnEntDeath yes)');
  }
  if (zone.includes('aitype,spawner_tod_dealer') && EX('share/raw/fx/tod/dealer')) {
    const zl = new Set(zone.split('\n').map(l => l.trim()));
    for (const f of fs.readdirSync(path.join(REPO, 'share/raw/fx/tod/dealer')).filter(f => f.endsWith('.efx')))
      ok(zl.has('fx,tod/dealer/' + f.slice(0, -4)), '10 zone line fx,tod/dealer/' + f.slice(0, -4));
  }
}

console.log((fails ? 'FAIL ' : 'PASS ') + 'test_dealer ' + passes + ' checks, ' + fails + ' failures');
process.exit(fails ? 1 : 0);
