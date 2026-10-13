#!/usr/bin/env node
// =============================================================================
// test_elite_hp.js — build gate for the OVER-HEAD HEALTH BARS (docs/174).
//
// Everything the bars need lives in FOUR places that nothing else keeps in
// step: the module's #precache list, source_data/tod_hud_bars.gdt (images +
// materials), the .zone's image,/material, lines, and the PNGs on disk. A
// material precached but not zoned is a LOAD ERROR; an image zoned but not
// on disk is a linker miss; a kind stamped by a spawner with no height row
// draws at the fallback height; a draw size that is not the PNG size / 4
// stretches the art.
//
// THE COLOUR CONTRACT (user 2026-10-01: elites RED, the Necromancer's helpers
// WHITE, "so you can tell the difference"): the full rest frame of every set
// is DECODED and its fill sampled - sets e / b must be red, set s white - so a
// re-run of an old generator, or an art drop in the wrong colour, fails here
// instead of in the user's game. The helpers' wiring (helper_register stamps
// tod_necro_helper + tod_hpbar_frac, helper_life keeps the frac) is checked too.
// This proves all of it, then breaks itself eleven ways.
// =============================================================================
'use strict';
const fs = require('fs');
const path = require('path');

const REPO = path.join(__dirname, '..');
const MOD = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_elite_hp.gsc');
const ENTRY = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity.gsc');
const ZONE = path.join(REPO, 'zone_source', 'zm_tod2_cybercity.zone');
const GDT = path.join(REPO, 'source_data', 'tod_hud_bars.gdt');
const IMG_DIR = path.join(REPO, 'source_data', 'tod_hud_bars', '_images');
const SCRIPT_DIR = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity');
const NECRO = path.join(SCRIPT_DIR, '_tod_necro_summon.gsc');
const zlib = require('zlib');

// 11 rest frames + 20 edge-pulse frames (_h1 small / _h2 peak, none on the empty 00) per set.
// e = elite (RED), b = boss (RED), s = the Necromancer's helpers (WHITE).
const SETS = ['e', 'b', 's'];
const EXPECTED = [];
for (const tag of SETS) for (let q = 0; q <= 10; q++) {
  const base = `tod_hpbar_${tag}_${String(q).padStart(2, '0')}`;
  EXPECTED.push(base);
  if (q > 0) EXPECTED.push(base + '_h1', base + '_h2');
}
// the canvas size each set's PNGs must have, and the draw size (canvas / 4) the
// script must use for it — a mismatch STRETCHES the art
const SIZES = {
  e: { png: [336, 72], def: ['TOD_HPBAR_W', 'TOD_HPBAR_H'], colour: 'red' },
  b: { png: [544, 80], def: ['TOD_HPBAR_BOSS_W', 'TOD_HPBAR_BOSS_H'], colour: 'red' },
  s: { png: [288, 64], def: ['TOD_HPBAR_SUMMON_W', 'TOD_HPBAR_SUMMON_H'], colour: 'white' },
};
const setOf = (n) => n.match(/^(?:i_)?tod_hpbar_([a-z])_/)[1];
// the Necromancer's helper kinds (_tod_necro_summon helper_register) -> bar rows
const SUMMON_KINDS = ['summon_thrall', 'summon_hound', 'summon_mangler'];

function pngSize(buf) {
  if (buf.length < 24 || buf.readUInt32BE(0) !== 0x89504e47) return null;
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}

// Minimal PNG decoder (8-bit RGB / RGBA, non-interlaced, all five row filters) —
// enough for the generator's output AND a hand-delivered drop. -> {w,h,px(x,y)}
function decodePNG(buf) {
  const s = pngSize(buf);
  if (!s) return null;
  let off = 8, depth = 0, ctype = 0, inter = 0;
  const idat = [];
  while (off < buf.length) {
    const len = buf.readUInt32BE(off), type = buf.toString('ascii', off + 4, off + 8);
    const data = buf.subarray(off + 8, off + 8 + len);
    if (type === 'IHDR') { depth = data[8]; ctype = data[9]; inter = data[12]; }
    if (type === 'IDAT') idat.push(data);
    off += 12 + len;
  }
  const bpp = ctype === 6 ? 4 : ctype === 2 ? 3 : 0;
  if (depth !== 8 || !bpp || inter) return null;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const stride = s.w * bpp, out = Buffer.alloc(stride * s.h);
  for (let y = 0; y < s.h; y++) {
    const f = raw[y * (stride + 1)], src = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1));
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? out[y * stride + x - bpp] : 0;
      const b = y > 0 ? out[(y - 1) * stride + x] : 0;
      const c = x >= bpp && y > 0 ? out[(y - 1) * stride + x - bpp] : 0;
      let v = src[x];
      if (f === 1) v += a;
      else if (f === 2) v += b;
      else if (f === 3) v += (a + b) >> 1;
      else if (f === 4) { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); v += (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c); }
      out[y * stride + x] = v & 0xFF;
    }
  }
  return { w: s.w, h: s.h, px: (x, y) => { const i = y * stride + x * bpp; return [out[i], out[i + 1], out[i + 2], bpp === 4 ? out[i + 3] : 255]; } };
}

// The fill colour of a FULL rest frame (_10): the mean of the opaque pixels in a
// band through the middle of the canvas, from 20% to 80% of its width (inside the
// track, clear of the frame ends and the leading edge).
function fillColour(buf) {
  const img = decodePNG(buf);
  if (!img) return null;
  let r = 0, g = 0, b = 0, n = 0;
  const y0 = Math.floor(img.h * 0.42), y1 = Math.ceil(img.h * 0.58);
  for (let y = y0; y < y1; y++) for (let x = Math.floor(img.w * 0.2); x < Math.floor(img.w * 0.8); x++) {
    const p = img.px(x, y);
    if (p[3] < 200) continue;
    r += p[0]; g += p[1]; b += p[2]; n++;
  }
  return n ? [r / n, g / n, b / n] : null;
}
const isRed = (c) => c[0] > 150 && c[0] > 2.2 * c[1] && c[0] > 2.2 * c[2];
const isWhite = (c) => Math.min(c[0], c[1], c[2]) > 185 && Math.max(c[0], c[1], c[2]) - Math.min(c[0], c[1], c[2]) < 40;

// inputs: { mod, entry, zone, gdt, pngs: {name: Buffer|null}, kinds: [..] } -> [problems]
function check(inp) {
  const p = [];
  const same = (a, b, label) => {
    const A = new Set(a), B = new Set(b);
    for (const x of A) if (!B.has(x)) p.push(`${label}: ${x} missing`);
    for (const x of B) if (!A.has(x)) p.push(`${label}: ${x} unexpected`);
  };
  // 1. precache list
  const pre = [...inp.mod.matchAll(/#precache\(\s*"material",\s*"([^"]+)"\s*\)/g)].map((m) => m[1]);
  same(EXPECTED, pre, '#precache');
  // 2. GDT image + material entries, material -> image binding, 2d type
  const gdtImgs = [...inp.gdt.matchAll(/"(i_[^"]+)"\s*\(\s*"image\.gdf"\s*\)/g)].map((m) => m[1]);
  const gdtMats = [...inp.gdt.matchAll(/"([^"]+)"\s*\(\s*"material\.gdf"\s*\)/g)].map((m) => m[1]);
  same(EXPECTED.map((n) => 'i_' + n), gdtImgs, 'GDT image');
  same(EXPECTED, gdtMats, 'GDT material');
  for (const n of EXPECTED) {
    const blk = inp.gdt.split(`"${n}" ( "material.gdf" )`)[1];
    if (!blk) continue;
    const body = blk.split('\n\t}')[0];
    if (!body.includes(`"colorMap" "i_${n}"`)) p.push(`GDT material ${n}: colorMap is not i_${n}`);
    if (!body.includes('"materialType" "2d_blend"')) p.push(`GDT material ${n}: not 2d_blend`);
  }
  for (const n of EXPECTED) {
    const blk = inp.gdt.split(`"i_${n}" ( "image.gdf" )`)[1];
    if (!blk) continue;
    const body = blk.split('\n\t}')[0];
    if (!body.includes(`"baseImage" "source_data/tod_hud_bars/_images/i_${n}.png"`)) p.push(`GDT image i_${n}: baseImage path wrong`);
    if (!body.includes('"noMipMaps" "1"') || !body.includes('"noPicMip" "1"')) p.push(`GDT image i_${n}: needs noMipMaps/noPicMip 1`);
  }
  // 3. zone lines
  const zoneLines = inp.zone.split(/\r?\n/).map((l) => l.trim());
  same(EXPECTED.map((n) => 'image,i_' + n), zoneLines.filter((l) => l.startsWith('image,i_tod_hpbar_')), 'zone image');
  same(EXPECTED.map((n) => 'material,' + n), zoneLines.filter((l) => l.startsWith('material,tod_hpbar_')), 'zone material');
  if (!zoneLines.includes('scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_elite_hp.gsc')) p.push('zone: _tod_elite_hp.gsc scriptparsetree line missing');
  // 4. PNGs
  for (const n of EXPECTED) {
    const buf = inp.pngs['i_' + n];
    if (!buf) { p.push(`png i_${n}.png missing`); continue; }
    const s = pngSize(buf);
    const want = SIZES[setOf(n)].png;
    if (!s || s.w !== want[0] || s.h !== want[1]) p.push(`png i_${n}.png: expected ${want[0]}x${want[1]}, got ${s ? s.w + 'x' + s.h : 'not a PNG'}`);
  }
  // 4b. the script's draw size = PNG size / 4 (4 source px per hudelem unit)
  for (const k of Object.keys(SIZES)) {
    const [dw, dh] = SIZES[k].def.map((d) => { const m = inp.mod.match(new RegExp('#define\\s+' + d + '\\s+(\\d+)')); return m ? +m[1] : NaN; });
    const [pw, ph] = SIZES[k].png;
    if (dw !== pw / 4 || dh !== ph / 4) p.push(`draw size ${SIZES[k].def.join('/')} = ${dw}x${dh}, expected ${pw / 4}x${ph / 4} (PNG ${pw}x${ph} / 4)`);
  }
  // 4c. THE COLOUR CONTRACT: elites + bosses RED, the Necromancer's helpers WHITE
  for (const tag of SETS) {
    const buf = inp.pngs[`i_tod_hpbar_${tag}_10`];
    if (!buf) continue;
    const c = fillColour(buf);
    const want = SIZES[tag].colour;
    const ok = c && (want === 'red' ? isRed(c) : isWhite(c));
    if (!ok) p.push(`colour: set ${tag} must be ${want.toUpperCase()}, fill of i_tod_hpbar_${tag}_10 is ${c ? c.map(Math.round).join(',') : 'unreadable'}`);
  }
  // 5. entry wiring — one #using, one init thread
  if (!/#using scripts\\zm\\zm_tod2_cybercity\\_tod_elite_hp;/.test(inp.entry)) p.push('entry: #using _tod_elite_hp missing');
  const threads = (inp.entry.match(/level thread tod_elite_hp::init\(\);/g) || []).length;
  if (threads !== 1) p.push(`entry: expected exactly 1 tod_elite_hp::init thread, found ${threads}`);
  // 6. every kind a spawner stamps has a height row (else the fallback height)
  const rows = new Set([...inp.mod.matchAll(/case "([a-z_]+)":\s*return TOD_HPBAR_Z_/g)].map((m) => m[1]));
  for (const k of inp.kinds) if (!rows.has(k)) p.push(`bar_zoff: no height row for tod_boss_kind "${k}"`);
  // W2E (2026-10-05): the Panzer, Rogue Protector, Fury, hellhound, armored sprinter and Keeper retired whole -
  // a row for one of them is dead weight (and a sign the kind came back half-way).
  for (const k of ['panzer', 'protector', 'reaver', 'hellhound', 'sprinter', 'keeper']) if (rows.has(k)) p.push(`bar_zoff: a row for the retired kind "${k}"`);
  for (const k of SUMMON_KINDS) if (!rows.has(k)) p.push(`bar_zoff: no height row for the Necromancer helper kind "${k}"`);
  // 6b. the helpers' wiring: a helper is stamped on the frame it becomes one, it
  // publishes what is left of it, and the bar module reads both
  if (!/h\.tod_necro_helper\s*=\s*true;/.test(inp.necro)) p.push('necro: helper_register no longer stamps h.tod_necro_helper');
  if (!/h\.tod_hpbar_frac\s*=\s*1;/.test(inp.necro)) p.push('necro: helper_register must start tod_hpbar_frac at 1');
  if (!/self\.tod_hpbar_frac\s*=\s*self helper_left_frac\(/.test(inp.necro)) p.push('necro: helper_life must keep tod_hpbar_frac current');
  if (!/return IS_TRUE\( z\.tod_necro_helper \);/.test(inp.mod)) p.push('is_summon must read tod_necro_helper');
  if (!/z\.tod_hpbar_frac/.test(inp.mod.replace(/\/\/.*$/gm, ''))) p.push('module never reads tod_hpbar_frac (the helper bar would sit full)');
  if (!/GetAITeamArray\( "allies" \)/.test(inp.mod)) p.push('scan never looks at "allies" (helpers would never get a bar)');
  // 7. the callback must stay read-only (return false) and never use hud::create*
  if (!/function on_zombie_damage[\s\S]*?return false;\s*\}/.test(inp.mod)) p.push('on_zombie_damage must return false');
  const code = inp.mod.replace(/\/\/.*$/gm, '');   // comments may NAME the trap; code may not use it
  if (/hud::create/.test(code)) p.push('module must not use hud::create* (they ignore SetTargetEnt)');
  return p;
}

function load() {
  const pngs = {};
  for (const n of EXPECTED) {
    const f = path.join(IMG_DIR, `i_${n}.png`);
    pngs['i_' + n] = fs.existsSync(f) ? fs.readFileSync(f) : null;
  }
  const kinds = new Set();
  for (const f of fs.readdirSync(SCRIPT_DIR)) {
    if (!f.endsWith('.gsc')) continue;
    const s = fs.readFileSync(path.join(SCRIPT_DIR, f), 'utf8');
    for (const m of s.matchAll(/\.tod_boss_kind\s*=\s*"([a-z_]+)"/g)) kinds.add(m[1]);
  }
  return {
    mod: fs.readFileSync(MOD, 'utf8'),
    entry: fs.readFileSync(ENTRY, 'utf8'),
    zone: fs.readFileSync(ZONE, 'utf8'),
    gdt: fs.readFileSync(GDT, 'utf8'),
    necro: fs.readFileSync(NECRO, 'utf8'),
    pngs,
    kinds: [...kinds],
  };
}

function main() {
  const inp = load();
  const problems = check(inp);
  if (problems.length) {
    console.error('[test_elite_hp] FAIL');
    for (const x of problems) console.error('  - ' + x);
    process.exit(1);
  }
  // negative controls: each mutation must be caught
  const breaks = [
    ['drop a precache', (i) => ({ ...i, mod: i.mod.replace('#precache( "material", "tod_hpbar_e_07" );', '') })],
    ['drop a zone material line', (i) => ({ ...i, zone: i.zone.replace(/material,tod_hpbar_b_03\r?\n/, '') })],
    ['lose a PNG', (i) => ({ ...i, pngs: { ...i.pngs, i_tod_hpbar_e_00: null } })],
    ['new kind without a row', (i) => ({ ...i, kinds: [...i.kinds, 'amalgam'] })],
    ['draw size drifts from the art', (i) => ({ ...i, mod: i.mod.replace(/#define TOD_HPBAR_W\s+\d+/, '#define TOD_HPBAR_W 48') })],
    ['lose a hit frame precache', (i) => ({ ...i, mod: i.mod.replace('#precache( "material", "tod_hpbar_b_04_h2" );', '') })],
    ['double init thread', (i) => ({ ...i, entry: i.entry + '\nlevel thread tod_elite_hp::init();\n' })],
    ['elite set back to white', (i) => ({ ...i, pngs: { ...i.pngs, i_tod_hpbar_e_10: i.pngs.i_tod_hpbar_s_10 } })],
    ['helper set drawn red', (i) => ({ ...i, pngs: { ...i.pngs, i_tod_hpbar_s_10: i.pngs.i_tod_hpbar_b_10 } })],
    ['helper never publishes its frac', (i) => ({ ...i, necro: i.necro.replace(/self\.tod_hpbar_frac\s*=\s*self helper_left_frac\(/, 'self.x = self helper_left_frac(') })],
    ['lose a helper height row', (i) => ({ ...i, mod: i.mod.replace(/case "summon_hound":\s*return TOD_HPBAR_Z_/, 'case "x": return TOD_HPBAR_Z_') })],
    ['a retired kind comes back with a row', (i) => ({ ...i, mod: i.mod.replace('case "dealer":      return TOD_HPBAR_Z_DEALER;', 'case "dealer":      return TOD_HPBAR_Z_DEALER;\n\t\tcase "panzer":      return TOD_HPBAR_Z_BOSS;') })],
  ];
  for (const [name, fn] of breaks) {
    if (check(fn(inp)).length === 0) {
      console.error(`[test_elite_hp] NEGATIVE CONTROL FAILED: "${name}" was not caught`);
      process.exit(1);
    }
  }
  const cols = SETS.map((tag) => `${tag}=${fillColour(inp.pngs[`i_tod_hpbar_${tag}_10`]).map(Math.round).join('/')}`).join(' ');
  console.log(`[test_elite_hp] OK: ${EXPECTED.length} materials in lockstep across precache / GDT / zone / PNGs (sizes = draw size x 4); colours elite+boss RED, helpers WHITE (${cols}); kinds ${inp.kinds.sort().join(',')} + sprinter + ${SUMMON_KINDS.join(',')} all have height rows; helper wiring OK; ${breaks.length}/${breaks.length} negative controls caught`);
}
main();
