#!/usr/bin/env node
// build_probe_lui.js - compile the telemetry probe's inner Lua chunk to T7 HavokScript
// bytecode and splice it into the outer menu shell (2026-10-04).
//
//   tools/telemetry_probe/tod_telem_probe_chunk.lua  -> tools/hksc/hksc.exe -> \ddd string
//   tools/telemetry_probe/tod_telem_probe_outer.tpl.lua  (marker @@TOD_TELEM_BYTECODE@@)
//   => tools/telemetry_probe/out/tod_telem_probe.lua   (STAGED; land.js copies it into ui/)
//
// Why bytecode-in-a-string: L3akMod (the link-time Lua compiler in the shared mod tools)
// rejects any source that names io / os, and retail HKS has no runtime SOURCE compiler, so
// the only way to reach io/os from a usermap is precompiled bytecode undumped through
// load(reader). Same recipe the old map shipped (its docs/40 "THE WORKING RECIPE").
//
// Usage: node tools/telemetry_probe/build_probe_lui.js [--check]
//   --check : rebuild into a temp buffer and fail if out/ differs (a gate-style run).

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const HERE = __dirname;
const ROOT = path.join(HERE, '..', '..');
const HKSC = path.join(ROOT, 'tools', 'hksc', 'hksc.exe');
const CHUNK = path.join(HERE, 'tod_telem_probe_chunk.lua');
const TPL = path.join(HERE, 'tod_telem_probe_outer.tpl.lua');
const OUT_DIR = path.join(HERE, 'out');
const OUT = path.join(OUT_DIR, 'tod_telem_probe.lua');
const MARKER = '@@TOD_TELEM_BYTECODE@@';
// The page the "url" mode opens at game over in the ARMED build only. The user's own
// Cloudflare Worker from the first map; /health is a trivial GET that stores nothing.
const URL = 'https://acc-leaderboard.jordana-urbaez.workers.dev/health?src=tod2probe';

function die(msg) { console.error('[build_probe_lui] FAIL: ' + msg); process.exit(1); }

if (!fs.existsSync(HKSC)) die('missing compiler ' + HKSC + ' (see tools/hksc/README.md)');
if (/[\\"'!%;]/.test(URL)) die('URL contains a character that would break the Lua splice');

function compileChunk() {
  const src = fs.readFileSync(CHUNK, 'utf8').split('@@TOD_TELEM_URL@@').join(URL);
  if (src.indexOf('@@') >= 0) die('unreplaced @@ placeholder left in the chunk source');
  const tmpSrc = path.join(OUT_DIR, 'chunk.subst.tmp.lua');
  const tmpOut = path.join(OUT_DIR, 'chunk.tmp.luac');
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(tmpSrc, src, 'utf8');
  try {
    execFileSync(HKSC, ['-s', '-o', tmpOut, tmpSrc], { stdio: 'pipe' });
  } catch (e) {
    die('hksc failed: ' + (e.stderr ? e.stderr.toString() : e.message));
  } finally {
    if (fs.existsSync(tmpSrc)) fs.unlinkSync(tmpSrc);
  }
  const bc = fs.readFileSync(tmpOut);
  fs.unlinkSync(tmpOut);
  // T7 HKS header: \x1bLua, version 0x51, format 0x0e - byte-identical to MACHIN[A]'s save.lua
  const hdr = [0x1b, 0x4c, 0x75, 0x61, 0x51, 0x0e];
  for (let i = 0; i < hdr.length; i++) {
    if (bc[i] !== hdr[i]) die('compiled to non-T7-HKS bytecode (header ' + [...bc.slice(0, 6)].map(b => b.toString(16)).join(' ') + ')');
  }
  let esc = '';
  for (const x of bc) esc += '\\' + String(x).padStart(3, '0');
  return { esc, len: bc.length };
}

function render() {
  const { esc, len } = compileChunk();
  const tpl = fs.readFileSync(TPL, 'latin1');
  if (tpl.indexOf(MARKER) < 0) die('template has no ' + MARKER + ' marker');
  if (tpl.indexOf(MARKER) !== tpl.lastIndexOf(MARKER)) die('template has more than one marker');
  // whitelist guard: the OUTER file must never name a blocked global (link-time compiler)
  const outerSrc = tpl.replace(/--[^\n]*/g, '').replace(/"(?:\\.|[^"\\])*"/g, '""');
  for (const g of ['io', 'os', '_G', 'getfenv', 'loadstring', 'rawget', 'select']) {
    if (new RegExp('(^|[^\\w.])' + g + '\\b').test(outerSrc)) die('outer template names blocked global "' + g + '"');
  }
  // repo Lua is CRLF; normalise so the landed file matches its neighbours
  const text = tpl.replace(MARKER, esc).replace(/\r?\n/g, '\r\n');
  return { text, len };
}

const check = process.argv.includes('--check');
const { text, len } = render();
if (check) {
  const cur = fs.existsSync(OUT) ? fs.readFileSync(OUT, 'latin1') : null;
  // the bytecode is deterministic for the same source + hksc, so a byte compare is fair
  if (cur !== text) die('out/tod_telem_probe.lua is stale - run build_probe_lui.js');
  console.log('[build_probe_lui] --check OK (' + len + ' bytecode bytes)');
} else {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(OUT, text, 'latin1');
  console.log('[build_probe_lui] out/tod_telem_probe.lua <- ' + len + ' bytecode bytes; url=' + URL);
}
