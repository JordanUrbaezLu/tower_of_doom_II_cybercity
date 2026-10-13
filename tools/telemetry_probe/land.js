#!/usr/bin/env node
// land.js - land or remove the TELEMETRY PROBE in ONE step (2026-10-04).
//
//   node tools/telemetry_probe/land.js --status   what is landed right now (read-only)
//   node tools/telemetry_probe/land.js --apply    land all five pieces (idempotent)
//   node tools/telemetry_probe/land.js --remove   retire WHOLE (idempotent)
//
// The pieces (a gated path must be self-consistent at every instant, so they land together):
//   1. scripts/zm/zm_tod2_cybercity/_tod_telem.gsc            <- tools/telemetry_probe/_tod_telem.gsc
//   2. ui/uieditor/menus/hud/tod_telem_probe.lua              <- tools/telemetry_probe/out/tod_telem_probe.lua
//   3. zone: scriptparsetree line after _tod_gameover.gsc; rawfile line after tod_upgrade.lua
//   4. entry script: #using line after the _tod_shop using
//   5. entry script: `level thread tod_telem::init();` after tod_elite_hp::init()
//   6. client entry script: `LuiLoad( "ui.uieditor.menus.hud.tod_telem_probe" );` after the class-select LuiLoad
//      (rev 4: the piece revs 1-3 lacked - without it the menu's Lua never runs)
// Every anchor is asserted UNIQUE before anything is written; each file keeps its own line
// endings (all four targets are CRLF today; the copied sources are normalised to the target's).
// Run the build gates (python tools/run_build_gates.py) after --apply, before any build.

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', '..');
const SRC_GSC = path.join(__dirname, '_tod_telem.gsc');
const SRC_LUA = path.join(__dirname, 'out', 'tod_telem_probe.lua');
const DST_GSC = path.join(ROOT, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_telem.gsc');
const DST_LUA = path.join(ROOT, 'ui', 'uieditor', 'menus', 'hud', 'tod_telem_probe.lua');
const ZONE = path.join(ROOT, 'zone_source', 'zm_tod2_cybercity.zone');
const ENTRY = path.join(ROOT, 'scripts', 'zm', 'zm_tod2_cybercity.gsc');
const ENTRY_CSC = path.join(ROOT, 'scripts', 'zm', 'zm_tod2_cybercity.csc');

const ZONE_SPT_ANCHOR = 'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_gameover.gsc';
const ZONE_SPT_LINE = 'scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_telem.gsc';
const ZONE_RAW_ANCHOR = 'rawfile,ui/uieditor/menus/hud/tod_upgrade.lua';
const ZONE_RAW_LINE = 'rawfile,ui/uieditor/menus/hud/tod_telem_probe.lua   // TELEMETRY PROBE (tools/telemetry_probe, dev test only)';
const USING_ANCHOR = '#using scripts\\zm\\zm_tod2_cybercity\\_tod_shop;';
const USING_LINE = '#using scripts\\zm\\zm_tod2_cybercity\\_tod_telem;    // TELEMETRY PROBE (tools/telemetry_probe): dev test of the local-storage channel';
const THREAD_ANCHOR = '\tlevel thread tod_elite_hp::init();';
const THREAD_LINES = [
  '\t// TELEMETRY PROBE (tools/telemetry_probe/README.md): inert unless TOD_TELEM_LOG is 1.',
  '\tlevel thread tod_telem::init();',
];

// 6. client entry script: LuiLoad the probe menu (THE missing piece of revs 1-3: without it OpenLUIMenu
//    returns a handle and the menu's Lua never executes - the 4-file contract, docs/19 of the first map)
const LUILOAD_ANCHOR = '	LuiLoad( "ui.uieditor.menus.hud.tod_class_select" );';
const LUILOAD_LINES = [
  '	// TELEMETRY PROBE LUI (tools/telemetry_probe; same 4-file contract; removed whole by land.js --remove)',
  '	LuiLoad( "ui.uieditor.menus.hud.tod_telem_probe" );',
];

function die(msg) { console.error('[land] FAIL: ' + msg); process.exit(1); }
function eolOf(text) { return /\r\n/.test(text) ? '\r\n' : '\n'; }
function readLines(file) {
  const text = fs.readFileSync(file, 'utf8');
  const eol = eolOf(text);
  const lines = text.split(/\r?\n/);
  return { lines, eol };
}
function writeLines(file, lines, eol) { fs.writeFileSync(file, lines.join(eol), 'utf8'); }
function findUnique(lines, exact, what) {
  const hits = [];
  lines.forEach((l, i) => { if (l.replace(/\s+$/, '') === exact.replace(/\s+$/, '')) hits.push(i); });
  if (hits.length !== 1) die(what + ': expected exactly one anchor line, found ' + hits.length + ' for "' + exact + '"');
  return hits[0];
}
function hasLine(lines, startsWith) { return lines.findIndex(l => l.trim().startsWith(startsWith)) >= 0; }
function normaliseTo(srcFile, eol) {
  return fs.readFileSync(srcFile, 'utf8').replace(/\r?\n/g, eol);
}

function status() {
  const z = readLines(ZONE).lines, e = readLines(ENTRY).lines, c = readLines(ENTRY_CSC).lines;
  const s = {
    gsc: fs.existsSync(DST_GSC),
    lua: fs.existsSync(DST_LUA),
    zone_spt: hasLine(z, ZONE_SPT_LINE),
    zone_raw: hasLine(z, 'rawfile,ui/uieditor/menus/hud/tod_telem_probe.lua'),
    using: hasLine(e, '#using scripts\\zm\\zm_tod2_cybercity\\_tod_telem;'),
    thread: hasLine(e, 'level thread tod_telem::init();'),
    luiload: hasLine(c, 'LuiLoad( "ui.uieditor.menus.hud.tod_telem_probe" );'),
  };
  const n = Object.values(s).filter(Boolean).length;
  console.log('[land] status: ' + JSON.stringify(s) + ' -> ' + (n === 0 ? 'NOT LANDED' : n === 7 ? 'LANDED (all 7)' : 'PARTIAL (' + n + '/7) - fix before building'));
  return s;
}

function apply() {
  if (!fs.existsSync(SRC_LUA)) die('missing ' + SRC_LUA + ' - run build_probe_lui.js first');
  // zone
  const z = readLines(ZONE);
  if (!hasLine(z.lines, ZONE_SPT_LINE)) {
    const i = findUnique(z.lines, ZONE_SPT_ANCHOR, 'zone scriptparsetree anchor');
    z.lines.splice(i + 1, 0, ZONE_SPT_LINE);
  }
  if (!hasLine(z.lines, 'rawfile,ui/uieditor/menus/hud/tod_telem_probe.lua')) {
    const i = findUnique(z.lines, ZONE_RAW_ANCHOR, 'zone rawfile anchor');
    z.lines.splice(i + 1, 0, ZONE_RAW_LINE);
  }
  // entry
  const e = readLines(ENTRY);
  if (!hasLine(e.lines, '#using scripts\\zm\\zm_tod2_cybercity\\_tod_telem;')) {
    const i = findUnique(e.lines, USING_ANCHOR, 'entry #using anchor');
    e.lines.splice(i + 1, 0, USING_LINE);
  }
  if (!hasLine(e.lines, 'level thread tod_telem::init();')) {
    const i = findUnique(e.lines, THREAD_ANCHOR, 'entry thread anchor');
    e.lines.splice(i + 1, 0, ...THREAD_LINES);
  }
  // client entry script
  const c = readLines(ENTRY_CSC);
  if (!hasLine(c.lines, 'LuiLoad( "ui.uieditor.menus.hud.tod_telem_probe" );')) {
    const i = findUnique(c.lines, LUILOAD_ANCHOR, 'client entry LuiLoad anchor');
    c.lines.splice(i + 1, 0, ...LUILOAD_LINES);
  }
  // files (normalised to the neighbours' line endings = CRLF)
  fs.writeFileSync(DST_GSC, normaliseTo(SRC_GSC, e.eol), 'utf8');
  fs.writeFileSync(DST_LUA, fs.readFileSync(SRC_LUA, 'latin1'), 'latin1');
  writeLines(ZONE, z.lines, z.eol);
  writeLines(ENTRY, e.lines, e.eol);
  writeLines(ENTRY_CSC, c.lines, c.eol);
  console.log('[land] applied. Next: python tools/run_build_gates.py, then .\\tools\\build_map.ps1 -GscOnly (never while BlackOps3 runs).');
  status();
}

function remove() {
  const z = readLines(ZONE);
  z.lines = z.lines.filter(l => !l.trim().startsWith(ZONE_SPT_LINE) && !l.trim().startsWith('rawfile,ui/uieditor/menus/hud/tod_telem_probe.lua'));
  const e = readLines(ENTRY);
  e.lines = e.lines.filter(l => !l.trim().startsWith('#using scripts\\zm\\zm_tod2_cybercity\\_tod_telem;')
    && !l.trim().startsWith('level thread tod_telem::init();')
    && !l.trim().startsWith('// TELEMETRY PROBE (tools/telemetry_probe/README.md)'));
  const c = readLines(ENTRY_CSC);
  c.lines = c.lines.filter(l => !l.trim().startsWith('LuiLoad( "ui.uieditor.menus.hud.tod_telem_probe" );')
    && !l.trim().startsWith('// TELEMETRY PROBE LUI (tools/telemetry_probe'));
  if (fs.existsSync(DST_GSC)) fs.unlinkSync(DST_GSC);
  if (fs.existsSync(DST_LUA)) fs.unlinkSync(DST_LUA);
  writeLines(ZONE, z.lines, z.eol);
  writeLines(ENTRY, e.lines, e.eol);
  writeLines(ENTRY_CSC, c.lines, c.eol);
  console.log('[land] removed WHOLE (module, rawfile, zone lines, entry lines, client LuiLoad).');
  status();
}

const arg = process.argv[2];
if (arg === '--status') status();
else if (arg === '--apply') apply();
else if (arg === '--remove') remove();
else die('usage: land.js --status | --apply | --remove');
