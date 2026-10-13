'use strict';
// =============================================================================
// tools/war_damage/test_war_damage.js - THE WAR DAMAGE PASS's build gate (docs/205).
//
//   * FRESH: layout.js --check (the placement + the generated CSC data, whose own
//     checks keep every piece out of the landing spot, the walkway middle, the rail
//     band and the next lap's landing), make_sounds.py --check, make_fx.py --check,
//     build_conduit_torn.py --check, and the merged models against the layout, kits
//     and GDT they were built from (clusters.json hashes, every LOD file, the GDT
//     block: no collision, three LODs); the conductor twins against their record.
//   * REAL ASSETS: every effect exists (stock or generated), is not a
//     gfx_debug_missing_fx stub and uses no _pcloud material; every decal card's
//     material is a PLAIN decal type (no alpha-reveal map) and is never zoned bare
//     (a model's material rides in with the model); every rendered wav exists.
//   * WIRING: the zone (all four scripts, every cluster + conductor model, every
//     effect), the main csc + gsc entries, the sound zone config, the sync rows.
//   * LOCKSTEP: the CSC's effect list and precaches == layout.js FX order; the sound
//     flag bits; the lamp kind index; the power wave constants against _tod_fall.gsc
//     and tod_crown_data::wave_orgs(); the power clientfield's name between the gsc
//     and the csc; the sky director's sign bearing against the jump title's, its
//     tracer speed against make_fx.py, its scene-hold beats against the jump title's.
//   * NEGATIVE CONTROLS: each check is run on a mutated input that must fail it.
// Usage: node tools/war_damage/test_war_damage.js
//        node tools/war_damage/test_war_damage.js --ledger <usermap assetinfo/<map>.csv>   (after a link:
//        all four scripts, every effect, every cluster model with ALL its triangles in all three LODs, every
//        conductor twin with all its triangles in both LODs - the converter drops degenerate triangles silently,
//        so the compiled count must equal the merged count)
// =============================================================================
const fs = require('fs'), path = require('path'), crypto = require('crypto'), { spawnSync } = require('child_process');
const ROOT = path.resolve(__dirname, '..', '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8').replace(/\r\n/g, '\n');
const sha = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const TOOLS = 'C:\\BO3Tools\\TOD2Cybercity';
const STOCK = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Call of Duty Black Ops III 455130';
const SCRIPTS = 'scripts/zm/zm_tod2_cybercity/';
const WAR_SCRIPTS = ['_tod_war_damage.gsc', '_tod_war_damage.csc', '_tod_war_damage_data.csc', '_tod_war_sky.csc'];

let checks = 0, fails = 0;
function check(ok, label) { checks++; if (!ok) { fails++; console.log('FAIL ' + label); } }

// ---------------------------------------------------------------------------
// The checks as pure functions over texts, so the negative controls can mutate them.
// ---------------------------------------------------------------------------
function fxProblems(name, text) {
  const out = [];
  if (text === null) out.push(`${name}: no .efx in the repo, the tools root or the stock root`);
  else {
    if (/gfx_debug_missing_fx/.test(text)) out.push(`${name}: a placeholder stub (gfx_debug_missing_fx)`);
    if (/_pcloud/i.test(text)) out.push(`${name}: uses a _pcloud material (the map's known crash class)`);
  }
  return out;
}
function decalProblems(name, gdtText) {
  const m = gdtText.match(new RegExp('"' + name + '"\\s*\\(\\s*"material\\.gdf"\\s*\\)\\s*\\{([^}]+)\\}'));
  if (!m) return [`${name}: no material block in the stock decal GDTs`];
  const f = Object.fromEntries([...m[1].matchAll(/"([^"\n]+)"\s*"([^"\n]*)"/g)].map(x => [x[1], x[2]]));
  const out = [];
  if (!/decal/.test(f.materialType || '')) out.push(`${name}: materialType ${f.materialType} is not a decal type`);
  if (/reveal/.test(f.materialType || '') || (f.alphaRevealMap || '') !== '') out.push(`${name}: an alpha-REVEAL decal (needs a reveal amount a model card does not drive)`);
  return out;
}
function conductorModels(layout) { return [...new Set(layout.conductors.flatMap(c => [c.model + '_off', c.model + '_on']))].sort(); }
function skyFx(sky) { return [...sky.matchAll(/#precache\( "client_fx", "([^"]+)" \);/g)].map(m => m[1]); }
function zoneProblems(zone, layout, sky) {
  const out = [], has = l => zone.split('\n').some(x => x.trim() === l);
  for (const s of WAR_SCRIPTS) if (!has(`scriptparsetree,${SCRIPTS}${s}`)) out.push(`zone: no scriptparsetree for ${s}`);
  for (const c of layout.clusters) if (!has(`xmodel,${c.name}`)) out.push(`zone: no xmodel line for ${c.name}`);
  for (const m of conductorModels(layout)) if (!has(`xmodel,${m}`)) out.push(`zone: no xmodel line for the conductor twin ${m}`);
  for (const fx of [...Object.values(layout.fx_map), layout.fire_light, ...skyFx(sky)]) if (!has(`fx,${fx}`)) out.push(`zone: no fx line for ${fx}`);
  for (const mats of Object.values(layout.decal_materials)) for (const m of mats)
    if (has(`material,${m}`)) out.push(`zone: decal material ${m} zoned BARE (a model's material rides in with the model)`);
  for (const m of ['mtl_tod_conduit_wire_off', 'mtl_tod_conduit_wire_on'])
    if (has(`material,${m}`)) out.push(`zone: conductor material ${m} zoned BARE (it rides in with the conductor models)`);
  return out;
}
function lockstepProblems(csc, layout) {
  const out = [], m = csc.match(/level\.tod_war_fx = array\(([\s\S]*?)\);/);
  if (!m) return ['csc: no level.tod_war_fx = array( ... ) list'];
  const list = [...m[1].matchAll(/"([^"]+)"/g)].map(x => x[1]), want = Object.values(layout.fx_map);
  if (JSON.stringify(list) !== JSON.stringify(want)) out.push(`csc: the effect list ${JSON.stringify(list)} != layout.js FX order ${JSON.stringify(want)}`);
  for (const fx of [...want, layout.fire_light]) if (!csc.includes(`#precache( "client_fx", "${fx}" );`)) out.push(`csc: no #precache for ${fx}`);
  if (!csc.includes(`"${layout.fire_light}"`)) out.push('csc: the firelight effect is not the layout\'s');
  const kinds = Object.keys(layout.fx_map), lampFirst = +(csc.match(/#define TOD_WAR_LAMP_FIRST\s+(\d+)/) || [])[1];
  if (lampFirst !== kinds.indexOf('lamp_a')) out.push(`csc: TOD_WAR_LAMP_FIRST ${lampFirst} != the index of lamp_a in layout.js KINDS (${kinds.indexOf('lamp_a')})`);
  if (!kinds.slice(lampFirst).every(k => k.startsWith('lamp_'))) out.push('layout: every kind from lamp_a on must be a lamp (they carry their own light)');
  // the sound flag bits: the csc must map each bit to the alias layout.js assigned it
  for (const [alias, bit] of Object.entries(layout.sound_flags))
    if (!new RegExp(`flags & ${bit} \\)\\s*s\\.sound = "${alias}";`).test(csc)) out.push(`csc: sound flag ${bit} must select "${alias}" (layout.js SOUNDS)`);
  if (!/\( flags & 16 \) && org\[ 2 \] < wz/.test(csc)) out.push('csc: a powered-only anchor (flag 16) must wait for the wave to reach its height');
  return out;
}
function waveOrgs(crown) {
  const m = crown.match(/function wave_orgs\(\)\s*\{([\s\S]*?)\n\}/);
  if (!m) return [];
  return [...m[1].matchAll(/a\[ (\d+) \] = \( ([-\d.]+), ([-\d.]+), ([-\d.]+) \);/g)].map(x => +x[4]);
}
function waveProblems(csc, gsc, fall, crown) {
  const out = [], def = (t, k) => (t.match(new RegExp('#define ' + k + '\\s+("[^"]*"|[-\\d.]+)')) || [])[1];
  const zs = waveOrgs(crown);
  if (zs.length < 2) return ['tod_crown_data::wave_orgs() not readable'];
  if (+def(csc, 'TOD_WAR_WAVE_SECS') !== +def(fall, 'TOD_FALL_WAVE_SECS')) out.push(`csc TOD_WAR_WAVE_SECS ${def(csc, 'TOD_WAR_WAVE_SECS')} != _tod_fall.gsc TOD_FALL_WAVE_SECS ${def(fall, 'TOD_FALL_WAVE_SECS')}`);
  if (+def(csc, 'TOD_WAR_WAVE_TOP_Z') !== zs[0]) out.push(`csc TOD_WAR_WAVE_TOP_Z ${def(csc, 'TOD_WAR_WAVE_TOP_Z')} != wave_orgs()[0] z ${zs[0]}`);
  if (+def(csc, 'TOD_WAR_WAVE_FLOORS') !== zs.length) out.push(`csc TOD_WAR_WAVE_FLOORS ${def(csc, 'TOD_WAR_WAVE_FLOORS')} != wave_orgs().size ${zs.length}`);
  if (+def(csc, 'TOD_WAR_WAVE_STEP') !== zs[0] - zs[1]) out.push(`csc TOD_WAR_WAVE_STEP ${def(csc, 'TOD_WAR_WAVE_STEP')} != the wave's floor step ${zs[0] - zs[1]}`);
  if (def(csc, 'TOD_WAR_POWER_FIELD') !== def(gsc, 'TOD_WAR_POWER_FIELD')) out.push('the power clientfield name differs between the gsc and the csc');
  const name = (def(gsc, 'TOD_WAR_POWER_FIELD') || '').replace(/"/g, '');
  if (!new RegExp(`clientfield::register\\( "world", TOD_WAR_POWER_FIELD, VERSION_SHIP, 1, "int" \\)`).test(gsc)) out.push('gsc: the power clientfield must be a 1-bit world int');
  if (!/clientfield::register\( "world", TOD_WAR_POWER_FIELD, VERSION_SHIP, 1, "int", &power_cb/.test(csc)) out.push('csc: the power clientfield must be registered 1-bit world with power_cb');
  if (!name) out.push('no TOD_WAR_POWER_FIELD');
  if (!/level waittill\( "tod_power_wave_z"/.test(gsc) || !/level notify\( "tod_power_wave_z"/.test(fall)) out.push('gsc: must wait for the wave cue _tod_fall.gsc notifies (tod_power_wave_z)');
  if (!/level flag::wait_till\( "power_on" \)/.test(gsc)) out.push('gsc: must also raise the bit on the power_on flag (no wave: a dev power)');
  return out;
}
function skyProblems(sky, jt, fxTables, lanes) {
  const out = [], def = (t, k) => (t.match(new RegExp('#define ' + k + '\\s+("[^"]*"|[-\\d.]+)')) || [])[1];
  if (+def(sky, 'TOD_WAR_SKY_SIGN_YAW') !== +def(jt, 'TOD_JT_SIGN_YAW')) out.push(`sky TOD_WAR_SKY_SIGN_YAW ${def(sky, 'TOD_WAR_SKY_SIGN_YAW')} != _tod_jump_title.csc TOD_JT_SIGN_YAW ${def(jt, 'TOD_JT_SIGN_YAW')}`);
  for (const beat of ['tod_jump_title_start', 'tod_jump_title_end'])
    if (!sky.includes(`"${beat}"`) || !jt.includes(`listen( "${beat}" )`)) out.push(`sky: must hold on the jump title's beat ${beat}`);
  const speed = +(sky.match(/speed = (\d+);/) || [])[1];
  if (speed !== fxTables.tracer.speed) out.push(`sky: the tracer speed ${speed} != make_fx.py TRACER speed ${fxTables.tracer.speed}`);
  const hi = +(lanes.match(/function volume_hi\(\) \{ return \( (\d+),/) || [])[1];
  if (!(+def(sky, 'TOD_WAR_SKY_R_MAX') <= hi - 200)) out.push(`sky: TOD_WAR_SKY_R_MAX ${def(sky, 'TOD_WAR_SKY_R_MAX')} must stay inside the sealed box (${hi} - 200)`);
  if (!(+def(sky, 'TOD_WAR_SKY_R_MIN') >= 5000)) out.push('sky: the war must stay far (R_MIN >= 5000)');
  if (!(+def(sky, 'TOD_WAR_SKY_SIGN_KEEP') >= 30)) out.push('sky: the sign keep-out must be at least 30 degrees');
  // the user's first run (2026-10-03 15:45): with the radius clamped only by the box, every site sat at R_MAX and every
  // boom came exactly 2.0 s late - the distance must be PICKED in r_min..R_MAX and then clamped
  if (!/box_reach\(\s*cam\s*,\s*d\s*,\s*300\s*\)\s*,\s*RandomFloatRange\(\s*r_min\s*,\s*TOD_WAR_SKY_R_MAX\s*\)\s*\)/.test(sky))
    out.push('sky: site() must pick its distance in r_min..R_MAX (RandomFloatRange) before the box clamp, or every flash sits at R_MAX');
  if (!/tod_sky_ships::ents_free\( localClientNum, 1 \)/.test(sky) || (sky.match(/tod_sky_ships::ents_add\( localClientNum, -1 \)/g) || []).length < 2) out.push('sky: the wreck must take and return one entity of the fleet budget on every exit');
  for (const alias of [...sky.matchAll(/"(tod_war_[a-z_]+)"/g)].map(m => m[1]).filter(a => !a.startsWith('tod_war_sky')))
    if (!alias.startsWith('tod_war_far_') && !alias.startsWith('tod_war_wreck')) out.push(`sky: unexpected alias ${alias}`);
  return out;
}
function conductorGdtProblems(gdt, names) {
  const out = [];
  for (const n of names) {
    const b = gdt.match(new RegExp('"' + n + '" \\( "xmodel\\.gdf" \\)\\n\\{([\\s\\S]*?)\\n\\}'));
    if (!b) { out.push(`${n}: no GDT block`); continue; }
    if (!/"CollisionMap" ""/.test(b[1]) || !/"BulletCollisionLOD" "None"/.test(b[1])) out.push(`${n}: a conductor twin must have no collision`);
    if (!/"mediumLod" "tod_war_damage\//.test(b[1])) out.push(`${n}: two LODs in the GDT`);
    if (!/"filename" "tod_war_damage\//.test(b[1])) out.push(`${n}: its LOD0 must live in model_export/tod_war_damage`);
  }
  return out;
}

// ---------------------------------------------------------------------------
// --ledger: after a link, the compiled assets carry everything, every triangle included.
// ---------------------------------------------------------------------------
function csvRows(p) {
  const lines = fs.readFileSync(p, 'utf8').replace(/^﻿/, '').split(/\r?\n/).filter(Boolean);
  const head = lines[0].split(',');
  return lines.slice(1).map(l => { const v = l.split(','); return Object.fromEntries(head.map((h, i) => [h, v[i]])); });
}
// `deployed` (optional) = what the linker actually consumed: { zoned(line), binSha(file) }. A peer's build syncs the
// tree BEFORE a later edit here lands (the gates read the REPO, the linker the DEPLOYED copy), so the ledger is
// held to what ITS zone named, and a model's triangle count is compared only when the deployed .xmodel_bin IS the
// one this record describes (a stale bin is reported, never failed: its own build verified it).
function ledgerProblems(assets, xmodels, layout, rec, torn, sky, deployed) {
  const out = [], notes = [], have = new Set(assets.map(r => r.type + ',' + r.name));
  const expect = line => !deployed || deployed.zoned(line);
  const fresh = (file, sha256) => !deployed || deployed.binSha(path.basename(file)) === sha256;
  const hasMat = m => assets.some(r => r.type === 'material' && (r.name === m || r.name.endsWith('/' + m)));
  for (const s of WAR_SCRIPTS) if (expect(`scriptparsetree,${SCRIPTS}${s}`) && !have.has(`scriptparsetree,${SCRIPTS}${s}`)) out.push(`ledger: no scriptparsetree for ${s}`);
  for (const fx of [...Object.values(layout.fx_map), layout.fire_light, ...skyFx(sky)]) if (expect('fx,' + fx) && !have.has('fx,' + fx)) out.push('ledger: effect not compiled: ' + fx);
  for (const mats of Object.values(layout.decal_materials)) for (const m of mats) if (!hasMat(m)) out.push('ledger: decal material not compiled: ' + m);
  const condNames = conductorModels(layout).filter(n => expect('xmodel,' + n));
  if (condNames.length) for (const m of ['mtl_tod_conduit_wire_off', 'mtl_tod_conduit_wire_on']) if (!hasMat(m)) out.push('ledger: conductor material not compiled: ' + m);
  const xm = Object.fromEntries(xmodels.map(r => [r.name, r]));
  // The xmodel ledger lists LODs LOWEST DETAIL FIRST (tod_teleporter reads 5000 ... 49324, a stock rock
  // 16 ... 118): our lod L is column (lodCount - 1 - L).
  let checked = 0, stale = 0;
  for (const c of layout.clusters) {
    if (!expect('xmodel,' + c.name)) continue;
    const row = xm[c.name];
    if (!row) { out.push('ledger: cluster model not compiled: ' + c.name); continue; }
    if (+row.lodCount !== 3) out.push(`ledger: ${c.name} compiled with ${row.lodCount} LODs, not 3`);
    for (const m of rec.models.filter(x => x.asset === c.name)) {
      if (!fresh(m.file, m.sha256)) { stale++; continue; }
      checked++;
      const col = 'tris' + (+row.lodCount - 1 - m.lod);
      if (+row[col] !== m.triangles) out.push(`ledger: ${c.name} lod${m.lod} compiled ${row[col]} triangles, merged ${m.triangles} (read the converter log under share/assetconvert/xmesh/v6/)`);
    }
  }
  for (const name of condNames) {
    const row = xm[name];
    if (!row) { out.push('ledger: conductor twin not compiled: ' + name); continue; }
    if (+row.lodCount !== 2) out.push(`ledger: ${name} compiled with ${row.lodCount} LODs, not 2`);
    for (const m of torn.models.filter(x => path.basename(x.file).startsWith(name + '_lod'))) {
      if (!fresh(m.file, m.sha256)) { stale++; continue; }
      checked++;
      const lod = +path.basename(m.file).match(/_lod(\d)/)[1], col = 'tris' + (+row.lodCount - 1 - lod);
      if (+row[col] !== m.triangles) out.push(`ledger: ${name} lod${lod} compiled ${row[col]} triangles, exported ${m.triangles}`);
    }
  }
  if (stale) notes.push(`${stale} deployed LOD files predate this record (a build synced before the current layout landed): their triangle counts were verified by their own build, not here`);
  out.notes = notes; out.checked = checked;
  return out;
}
const li = process.argv.indexOf('--ledger');
if (li > 0) {
  const assetsPath = process.argv[li + 1], xmodelPath = assetsPath.replace(/\.csv$/, '_xmodel.csv');
  const layoutL = JSON.parse(read('art/war_damage/layout.json')), recL = JSON.parse(read('art/war_damage/clusters.json'));
  const tornL = JSON.parse(read('art/war_damage/conduit_torn.json')), skyL = read(SCRIPTS + '_tod_war_sky.csc');
  const assets = csvRows(assetsPath), xmodels = csvRows(xmodelPath);
  // what the linker consumed: the deployed zone + the deployed model files (the sync copies both at a build's start)
  const zonePath = path.join(TOOLS, 'usermaps', 'zm_tod2_cybercity', 'zone_source', 'zm_tod2_cybercity.zone');
  const binDir = path.join(TOOLS, 'model_export', 'tod_war_damage');
  let deployed = null;
  if (fs.existsSync(zonePath)) {
    const zoneLines = new Set(fs.readFileSync(zonePath, 'utf8').split(/\r?\n/).map(l => l.trim()));
    deployed = { zoned: l => zoneLines.has(l), binSha: f => fs.existsSync(path.join(binDir, f)) ? sha(path.join(binDir, f)) : null };
  } else console.log('NOTE: no deployed zone at ' + zonePath + ' - checking the full repo expectation');
  const probs = ledgerProblems(assets, xmodels, layoutL, recL, tornL, skyL, deployed);
  for (const pr of probs) console.log('FAIL ' + pr);
  for (const n of probs.notes) console.log('NOTE ' + n);
  // negative controls: a cluster one triangle short at LOD0 and at LOD2, a conductor twin one short, must each be
  // caught - on models whose deployed files ARE this record's (a stale deployment cannot be exercised)
  const short = (name, col) => xmodels.map(r => r.name === name ? { ...r, [col]: String(+r[col] - 1) } : r);
  const freshCluster = layoutL.clusters.find(c => recL.models.filter(m => m.asset === c.name).every(m => !deployed || deployed.binSha(path.basename(m.file)) === m.sha256) && xmodels.some(r => r.name === c.name));
  const freshCond = conductorModels(layoutL).find(n => tornL.models.filter(m => path.basename(m.file).startsWith(n + '_lod')).every(m => !deployed || deployed.binSha(path.basename(m.file)) === m.sha256) && xmodels.some(r => r.name === n));
  const n0 = probs.length;
  let caught = true;
  if (freshCluster) {
    const top = 'tris' + (+xmodels.find(r => r.name === freshCluster.name).lodCount - 1);
    caught = ledgerProblems(assets, short(freshCluster.name, top), layoutL, recL, tornL, skyL, deployed).length > n0
      && ledgerProblems(assets, short(freshCluster.name, 'tris0'), layoutL, recL, tornL, skyL, deployed).length > n0;
  } else console.log('NOTE: no cluster model in this ledger matches the current record: the triangle negative control could not run');
  if (freshCond) caught = caught && ledgerProblems(assets, short(freshCond, 'tris1'), layoutL, recL, tornL, skyL, deployed).length > n0;
  else console.log('NOTE: no conductor twin in this ledger matches the current record: its negative control could not run');
  if (!caught) console.log('FAIL negative control "a compiled model one triangle short" was NOT caught');
  if (probs.length || !caught) { console.log(`WAR DAMAGE LEDGER FAILED: ${probs.length} problems`); process.exit(1); }
  const tris = recL.models.filter(m => m.lod === 0).reduce((a, m) => a + m.triangles, 0);
  console.log(`WAR DAMAGE LEDGER OK: every war script / effect / material / model the deployed zone named is compiled; ${probs.checked} LOD files with every triangle (${tris} merged at LOD0 in the current record), ${conductorModels(layoutL).length} conductor twins; negative controls ${freshCluster ? 'caught' : 'skipped (stale deployment)'}.`);
  process.exit(0);
}

// ---------------------------------------------------------------------------
// FRESH
// ---------------------------------------------------------------------------
const run = (cmd, args) => spawnSync(cmd, args, { cwd: ROOT, encoding: 'utf8', env: { ...process.env, TOD_WAR_STAGE: '' } });
const lay = run(process.execPath, ['tools/war_damage/layout.js', '--check']);
check(lay.status === 0, 'layout.js --check: ' + (lay.stdout + lay.stderr).trim().split('\n').slice(-3).join(' | '));
for (const tool of ['make_sounds.py', 'make_fx.py', 'build_conduit_torn.py']) {
  const r = run('python', ['tools/war_damage/' + tool, '--check']);
  check(r.status === 0, `${tool} --check: ` + (r.stdout + r.stderr).trim().split('\n').slice(-2).join(' | '));
}

const layout = JSON.parse(read('art/war_damage/layout.json'));
const rec = JSON.parse(read('art/war_damage/clusters.json'));
const torn = JSON.parse(read('art/war_damage/conduit_torn.json'));
const fxTables = JSON.parse(read('art/war_damage/fx_tables.json'));
check(rec.layout_sha256 === sha(path.join(ROOT, 'art/war_damage/layout.json')), 'the merged models were built from THIS layout (clusters.json layout_sha256)');
check(rec.kit_sha256 === sha(path.join(ROOT, 'art/war_damage/kit.json')), 'the merged models were built from THIS kit (clusters.json kit_sha256)');
check(rec.kit_war_sha256 === sha(path.join(ROOT, 'art/war_damage/kit_war.json')), 'the merged models were built from THESE torn conduit bodies (clusters.json kit_war_sha256)');
check(rec.gdt_sha256 === sha(path.join(ROOT, 'source_data/tod_war_damage.gdt')), 'source_data/tod_war_damage.gdt is the one build_clusters.py wrote');
check(torn.gdt_sha256 === sha(path.join(ROOT, 'source_data/tod_war_conductors.gdt')), 'source_data/tod_war_conductors.gdt is the one build_conduit_torn.py wrote');
const gdt = read('source_data/tod_war_damage.gdt');
for (const c of layout.clusters) {
  const lods = rec.models.filter(m => m.asset === c.name);
  check(lods.length === 3 && [0, 1, 2].every(l => lods.some(m => m.lod === l)), `${c.name}: three LOD records`);
  for (const m of lods) {
    const p = path.join(ROOT, m.file);
    check(fs.existsSync(p) && sha(p) === m.sha256, `${c.name} lod${m.lod}: ${m.file} present and unchanged`);
    check(m.triangles > 0, `${c.name} lod${m.lod}: has triangles`);
  }
  const b = gdt.match(new RegExp('"' + c.name + '" \\( "xmodel\\.gdf" \\)\\n\\{([\\s\\S]*?)\\n\\}'));
  check(!!b, `${c.name}: a GDT block`);
  if (b) {
    check(/"CollisionMap" ""/.test(b[1]) && /"BulletCollisionLOD" "None"/.test(b[1]), `${c.name}: no collision (decorative: nothing to stand on, nothing a grapple can hit)`);
    check(/"mediumLod" "tod_war_damage\//.test(b[1]) && /"lowLod" "tod_war_damage\//.test(b[1]), `${c.name}: three LODs in the GDT`);
  }
}
check(layout.clusters.length <= 40, `${layout.clusters.length} client models <= 40`);
const condGdt = read('source_data/tod_war_conductors.gdt'), condNames = conductorModels(layout);
for (const pr of conductorGdtProblems(condGdt, condNames)) check(false, pr);
checks++;
for (const m of torn.models) {
  const p = path.join(ROOT, m.file);
  check(fs.existsSync(p) && sha(p) === m.sha256, `${m.file} present and unchanged (conduit_torn.json)`);
}
check(condNames.every(n => torn.models.some(m => path.basename(m.file) === n + '_lod0.xmodel_bin') && torn.models.some(m => path.basename(m.file) === n + '_lod1.xmodel_bin')), 'every conductor twin the layout names has both LOD files');
check(layout.conductors.length >= 24 && layout.conductors.length <= 48, `${layout.conductors.length} conductor client models in 24..48`);
check(layout.totals.lamps === 24, `${layout.totals.lamps} flickering fixtures: one per break`);

// ---------------------------------------------------------------------------
// REAL ASSETS
// ---------------------------------------------------------------------------
const efx = name => { for (const base of [ROOT, TOOLS, STOCK]) { const p = path.join(base, 'share', 'raw', 'fx', name + '.efx'); if (fs.existsSync(p)) return fs.readFileSync(p, 'latin1'); } return null; };
const sky = read(SCRIPTS + '_tod_war_sky.csc');
for (const fx of [...Object.values(layout.fx_map), layout.fire_light, ...skyFx(sky)]) for (const pr of fxProblems(fx, efx(fx))) check(false, pr);
checks++;
const decalGdt = fs.readdirSync(path.join(STOCK, 'texture_assets')).filter(f => /^t7_decal.*\.gdt$/.test(f)).map(f => fs.readFileSync(path.join(STOCK, 'texture_assets', f), 'latin1')).join('\n');
for (const mats of Object.values(layout.decal_materials)) for (const m of mats) for (const pr of decalProblems(m, decalGdt)) check(false, pr);
checks++;
const db = path.join(TOOLS, 'gdtdb', 'gdt.db');
if (fs.existsSync(db)) {
  const bytes = fs.readFileSync(db);
  for (const mats of Object.values(layout.decal_materials)) for (const m of mats) check(bytes.includes(Buffer.from(m)), `${m} is in the private gdt.db`);
}
const aliases = read('sound/aliases/tod_war.csv');
for (const row of aliases.split('\n').slice(1).filter(Boolean)) {
  const [name, , , spec] = row.split(',');
  if (spec.startsWith('tod\\war\\')) check(fs.existsSync(path.join(ROOT, 'sound_assets', spec.replace(/\\/g, '/'))), `alias ${name}: its rendered wav exists in the repo`);
}

// ---------------------------------------------------------------------------
// WIRING + LOCKSTEP
// ---------------------------------------------------------------------------
const zone = read('zone_source/zm_tod2_cybercity.zone');
for (const pr of zoneProblems(zone, layout, sky)) check(false, pr);
checks++;
const csc = read(SCRIPTS + '_tod_war_damage.csc'), gsc = read(SCRIPTS + '_tod_war_damage.gsc');
for (const pr of lockstepProblems(csc, layout)) check(false, pr);
checks++;
const fall = read(SCRIPTS + '_tod_fall.gsc'), crown = read(SCRIPTS + '_tod_crown_data.gsc'), jt = read(SCRIPTS + '_tod_jump_title.csc'), lanes = read(SCRIPTS + '_tod_sky_lanes.csc');
for (const pr of waveProblems(csc, gsc, fall, crown)) check(false, pr);
checks++;
for (const pr of skyProblems(sky, jt, fxTables, lanes)) check(false, pr);
checks++;
const mainCsc = read('scripts/zm/zm_tod2_cybercity.csc'), mainGsc = read('scripts/zm/zm_tod2_cybercity.gsc');
check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_war_damage;/.test(mainCsc), 'the main csc #uses _tod_war_damage');
check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_war_sky;/.test(mainCsc), 'the main csc #uses _tod_war_sky');
check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_war_damage;/.test(mainGsc) && /level thread tod_war_damage::init\(\);/.test(mainGsc), 'the main gsc #uses _tod_war_damage and threads its init');
check(/"Filename": "tod_war\.csv"/.test(read('sound/zoneconfig/zm_tod2_cybercity.szc')), 'the sound zone config lists tod_war.csv');
for (const a of [...new Set([...csc.matchAll(/"(tod_war_[a-z_]+_lp)"/g), ...sky.matchAll(/"(tod_war_(?:far|wreck)[a-z_]*)"/g)].map(m => m[1]))])
  check(new RegExp('^' + a + ',', 'm').test(aliases), `alias ${a} (named by a script) is defined in tod_war.csv`);
for (const alias of Object.keys(layout.sound_flags)) check(new RegExp('^' + alias + ',', 'm').test(aliases) && csc.includes(`"${alias}"`), `alias ${alias} defined and used by the csc`);
const sync = read('tools/sync_to_modtools.ps1');
check(/model_export\\tod_war_damage/.test(sync), 'the sync copies model_export/tod_war_damage');
check(/sound_assets\\tod\\war/.test(sync), 'the sync copies sound_assets/tod/war');
const fxMax = +(csc.match(/#define TOD_WAR_FX_MAX\s+(\d+)/) || [])[1], lightMax = +(csc.match(/#define TOD_WAR_LIGHT_MAX\s+(\d+)/) || [])[1];
check(fxMax > 0 && fxMax <= 30, `TOD_WAR_FX_MAX ${fxMax} in 1..30`);
check(lightMax > 0 && lightMax <= 4, `TOD_WAR_LIGHT_MAX ${lightMax} in 1..4 (each is a dynamic light)`);
check(!/\bspawn\( *localClientNum, [^;]*"script_model" \)[\s\S]*SetModel\( "tag_origin" \)/.test(csc), 'effects play at a position (no tag_origin host entities)');
for (const kind of ['lamp_a', 'lamp_b', 'lamp_c']) check(layout.clusters.some(c => c.fx.some(f => f.kind === kind)), `the layout uses ${kind}`);

// ---------------------------------------------------------------------------
// NEGATIVE CONTROLS: every check above must fail on a broken input.
// ---------------------------------------------------------------------------
function control(label, problems) { checks++; if (!problems.length) { fails++; console.log(`FAIL negative control "${label}" was NOT caught`); } }
control('a stub effect', fxProblems('x', 'element ... gfx_debug_missing_fx ...'));
control('a _pcloud effect', fxProblems('x', 'material "fx_dust_pcloud" ...'));
control('a missing effect', fxProblems('x', null));
control('a reveal decal', decalProblems('t7_decal_grunge_burnt_stain_01', decalGdt));
control('a non-decal material', decalProblems('fake', '"fake" ( "material.gdf" )\n{\n"materialType" "lit"\n}'));
control('a cluster model left out of the zone', zoneProblems(zone.replace(`xmodel,${layout.clusters[0].name}\n`, ''), layout, sky));
control('a conductor twin left out of the zone', zoneProblems(zone.replace(`xmodel,${condNames[0]}\n`, ''), layout, sky));
control('a sky effect left out of the zone', zoneProblems(zone.replace(`fx,${skyFx(sky)[0]}\n`, ''), layout, sky));
control('a decal material zoned bare', zoneProblems(zone + `\nmaterial,${layout.decal_materials.blast[0]}\n`, layout, sky));
control('the csc effect list out of order', lockstepProblems(csc.replace('"dirt/fx_dust_fall_sm_lit", "electric/fx_elec_sparks_sm_wire_orange"', '"electric/fx_elec_sparks_sm_wire_orange", "dirt/fx_dust_fall_sm_lit"'), layout));
control('a missing precache', lockstepProblems(csc.replace('#precache( "client_fx", "debris/fx_debris_ash_float_lg" );', ''), layout));
control('a sound flag bit pointing at the wrong alias', lockstepProblems(csc.replace('flags & 32 )\n\t\ts.sound = "tod_war_tube_lp";', 'flags & 32 )\n\t\ts.sound = "tod_war_arc_lp";'), layout));
control('a wave length out of step', waveProblems(csc.replace(/#define TOD_WAR_WAVE_SECS\s+\d+/, '#define TOD_WAR_WAVE_SECS   13'), gsc, fall, crown));
control('a wave top out of step', waveProblems(csc.replace(/#define TOD_WAR_WAVE_TOP_Z\s+\d+/, '#define TOD_WAR_WAVE_TOP_Z  19200'), gsc, fall, crown));
control('a renamed power field on one side', waveProblems(csc, gsc.replace('#define TOD_WAR_POWER_FIELD "tod_war_power"', '#define TOD_WAR_POWER_FIELD "tod_war_powerx"'), fall, crown));
control('the sign bearing out of step', skyProblems(sky.replace(/#define TOD_WAR_SKY_SIGN_YAW\s+\d+/, '#define TOD_WAR_SKY_SIGN_YAW   90'), jt, fxTables, lanes));
control('the tracer speed out of step', skyProblems(sky.replace(/speed = \d+;/, 'speed = 1000;'), jt, fxTables, lanes));
control('every sky site pinned at R_MAX (the first run)', skyProblems(sky.replace(/RandomFloatRange\(\s*r_min\s*,\s*TOD_WAR_SKY_R_MAX\s*\)/, 'TOD_WAR_SKY_R_MAX'), jt, fxTables, lanes));
control('a conductor twin with collision', conductorGdtProblems(condGdt.replace('"CollisionMap" ""', '"CollisionMap" "x"'), condNames.slice(0, 1)));

if (fails) { console.log(`WAR DAMAGE GATE FAILED: ${fails} of ${checks} checks`); process.exit(1); }
console.log(`WAR DAMAGE OK: ${checks} checks - ${layout.clusters.length} client models (${layout.totals.props} stock props + ${layout.totals.decals} scorch cards), ${layout.totals.fx} effect anchors (${layout.totals.lamps} flickering fixtures, ${layout.totals.arcs} live arcs), ${layout.conductors.length} conductor twins, fresh merge + torn conduits + effects + sounds, real effects, plain decals, wiring, lockstep (wave, power field, sign, tracer), 18 negative controls caught.`);
