#!/usr/bin/env node
// preview_base_plan.js — top-down plans of the TOD II base complex (docs/158),
// drawn from the EMITTED brushes and entities in map_source/zm/zm_tod2_cybercity.map.
// No bake, no Radiant, ~1 s. Two sheets:
//
//   plan_undercity.png   z around UC_Z (-384): the Vault, the Conduit, the shaft foot
//   plan_plaza.png       z around 0: the tower plaza, the four workshop wings, the
//                        shaft's top landing, the teleport bay and the power hall
//
//   node tools/preview_base_plan.js            -> docs/158_base_plan/plan_*.png
//   node tools/preview_base_plan.js --out DIR
//
// What it draws is what cod2map will compile — the layout tables are not read.
// Colour = the vertigo material's hue, brightness = height above the level's
// floor (floor slabs dark, walls bright). Entities are drawn as marks from the
// .map (not from the generator): risers as red dots, initial spawns yellow,
// door trigger boxes as green outlines with the door flag, perk parking spots
// cyan, respawn-group points magenta. The partner benches and part shelf come
// from the GENERATED data file, which is exactly what the script reads.
'use strict';
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const REPO = path.resolve(__dirname, '..');
const MAP = path.join(REPO, 'map_source', 'zm', 'zm_tod2_cybercity.map');
const DATA = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_breather_data.gsc');
const args = process.argv.slice(2);
const outDir = args.includes('--out') ? args[args.indexOf('--out') + 1] : path.join(REPO, 'docs', '158_base_plan');

// --- parse worldspawn boxes + the entities we mark -----------------------------
const text = fs.readFileSync(MAP, 'utf8');
function parseWorld(t) {
  const end = t.indexOf('// entity 1 ');
  const lines = (end >= 0 ? t.slice(0, end) : t).split(/\r?\n/);
  const out = [];
  let label = null;
  for (let i = 0; i < lines.length; i++) {
    const lm = lines[i].match(/^\/\/ brush \d+ — (.*)$/);
    if (lm) { label = lm[1]; continue; }
    if (lines[i] !== '{' || label === null) continue;
    const planes = []; let mat = null;
    for (let j = i + 1; j < lines.length && lines[j] !== '}'; j++) {
      const pm = lines[j].match(/^ \( (\S+) (\S+) (\S+) \) \( (\S+) (\S+) (\S+) \) \( (\S+) (\S+) (\S+) \) (\S+) /);
      if (!pm) continue;
      const v = pm.slice(1, 10).map(Number); mat = pm[10];
      const verts = [[v[0], v[1], v[2]], [v[3], v[4], v[5]], [v[6], v[7], v[8]]];
      for (let a = 0; a < 3; a++) if (verts[0][a] === verts[1][a] && verts[1][a] === verts[2][a]) planes.push([a, verts[0][a]]);
    }
    if (planes.length === 6 && mat) {
      const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
      for (const [a, v] of planes) { lo[a] = Math.min(lo[a], v); hi[a] = Math.max(hi[a], v); }
      out.push({ label, mat, lo, hi });
    }
    label = null;
  }
  return out;
}
function parseEntities(t) {
  const ents = [];
  const blocks = t.split(/^\/\/ entity \d+.*$/m).slice(1);
  for (const b of blocks) {
    const kv = {};
    for (const m of b.matchAll(/^"([^"]+)" "([^"]*)"$/gm)) kv[m[1]] = m[2];
    // a trigger's brush bounds (the door trigger boxes)
    const bounds = [];
    for (const m of b.matchAll(/^ \( (\S+) (\S+) (\S+) \) \( (\S+) (\S+) (\S+) \) \( (\S+) (\S+) (\S+) \) /gm)) {
      const v = m.slice(1, 10).map(Number);
      for (let a = 0; a < 3; a++) if (v[a] === v[3 + a] && v[a] === v[6 + a]) bounds.push([a, v[a]]);
    }
    if (bounds.length) {
      const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
      for (const [a, v] of bounds) { lo[a] = Math.min(lo[a], v); hi[a] = Math.max(hi[a], v); }
      kv._lo = lo; kv._hi = hi;
    }
    if (kv.origin) kv._org = kv.origin.split(' ').map(Number);
    ents.push(kv);
  }
  return ents;
}
const brushes = parseWorld(text);
const ents = parseEntities(text);
const data = fs.readFileSync(DATA, 'utf8');
const benches = [...data.matchAll(/case (\d): return \( (-?\d+), (-?\d+), 0 \);/g)].map(m => [+m[2], +m[3], +m[1]]);
const partRow = data.match(/return \( (-?\d+), (-?\d+) \+ n \* (\d+), (-?\d+) \);/);
const parts = partRow ? Array.from({ length: 8 }, (_, n) => [+partRow[1], +partRow[2] + n * +partRow[3]]) : [];
const qr = data.match(/function vault_qr_org\(\)\s*\{\s*return \( (-?\d+), (-?\d+), (-?\d+) \)/);

// --- colours ------------------------------------------------------------------
const HUE = {
  yellow: [255, 210, 60], red: [255, 70, 70], blue: [90, 150, 255], dark_blue: [40, 70, 200], cyan: [80, 220, 255],
  green: [90, 255, 120], orange: [255, 140, 40], purple: [190, 100, 255], pink: [255, 120, 200], light_pink: [255, 170, 210],
  white: [240, 240, 255], dark_white: [120, 120, 130], pap: [255, 230, 120], off: [30, 30, 30],
};
function matColour(mat) {
  if (mat === 'clip' || mat === 'clip_player' || mat === 'sky') return null;
  let m = mat.match(/^mwiii_vertigo_retro_synth_([a-z_]+?)(?:_tinted(?:_edge)?)?$/);
  if (!m) m = mat.match(/^tod_door_([a-z]+)$/);
  const base = m ? (HUE[m[1]] || [200, 200, 200]) : [160, 160, 160];
  return /_tinted|^tod_door/.test(mat) ? base : base.map(v => Math.round(v * 0.75));
}

// --- raster -------------------------------------------------------------------
function makeCanvas(w, h) { const px = Buffer.alloc(w * h * 3, 18); return { w, h, px }; }
function fillRect(c, x1, y1, x2, y2, rgb) {
  x1 = Math.max(0, Math.floor(x1)); y1 = Math.max(0, Math.floor(y1)); x2 = Math.min(c.w, Math.ceil(x2)); y2 = Math.min(c.h, Math.ceil(y2));
  for (let y = y1; y < y2; y++) for (let x = x1; x < x2; x++) { const o = (y * c.w + x) * 3; c.px[o] = rgb[0]; c.px[o + 1] = rgb[1]; c.px[o + 2] = rgb[2]; }
}
function strokeRect(c, x1, y1, x2, y2, rgb, dash) {
  x1 = Math.floor(x1); y1 = Math.floor(y1); x2 = Math.ceil(x2) - 1; y2 = Math.ceil(y2) - 1;
  const put = (x, y, i) => { if (dash && (i % 6) >= 3) return; if (x < 0 || y < 0 || x >= c.w || y >= c.h) return; const o = (y * c.w + x) * 3; c.px[o] = rgb[0]; c.px[o + 1] = rgb[1]; c.px[o + 2] = rgb[2]; };
  let i = 0;
  for (let x = x1; x <= x2; x++, i++) { put(x, y1, i); put(x, y2, i); }
  for (let y = y1; y <= y2; y++, i++) { put(x1, y, i); put(x2, y, i); }
}
function dot(c, x, y, r, rgb) { fillRect(c, x - r, y - r, x + r, y + r, rgb); }
const FONT = {
  A: '0E1F1B1F1B1B1B', B: '1E1B1E1B1B1B1E', C: '0E1B1818181B0E', D: '1E1B1B1B1B1B1E', E: '1F18181E18181F', F: '1F18181E181818', G: '0E1B181F1B1B0F',
  H: '1B1B1B1F1B1B1B', I: '0E060606060E00', J: '070303031B1B0E', K: '1B1B1E1C1E1B1B', L: '18181818181B1F', M: '111B1F1F151111', N: '111919151313111',
  O: '0E1B1B1B1B1B0E', P: '1E1B1B1E181818', Q: '0E1B1B1B1F0E03', R: '1E1B1B1E1C1E1B', S: '0F181E0F03031E', T: '1F060606060606', U: '1B1B1B1B1B1B0E',
  V: '1B1B1B1B1B0E04', W: '1111111515151B', X: '1B1B0E040E1B1B', Y: '1B1B0E06060606', Z: '1F03060C18181F', ' ': '00000000000000', '-': '0000001F000000',
  0: '0E1B1B1B1B1B0E', 1: '060E06060606060E', 2: '0E1B03060C181F', 3: '1E03030E03031E', 4: '1B1B1B1F030303', 5: '1F18181E03031E', 6: '0E18181E1B1B0E',
  7: '1F0303060C0C0C', 8: '0E1B1B0E1B1B0E', 9: '0E1B1B0F03030E', '.': '00000000000606', ':': '00060600060600', '/': '01030306060C18', '_': '0000000000001F',
};
function label(c, x, y, str, rgb, s = 2) {
  let cx = x;
  for (const ch of str.toUpperCase()) {
    const g = FONT[ch] || FONT[' '];
    for (let r = 0; r < 7; r++) {
      const bits = parseInt(g.slice(r * 2, r * 2 + 2), 16);
      for (let col = 0; col < 5; col++) if (bits & (1 << (4 - col))) fillRect(c, cx + col * s, y + r * s, cx + col * s + s, y + r * s + s, rgb);
    }
    cx += 6 * s;
  }
}
function writePng(file, c) {
  const raw = Buffer.alloc((c.w * 3 + 1) * c.h);
  for (let y = 0; y < c.h; y++) { raw[y * (c.w * 3 + 1)] = 0; c.px.copy(raw, y * (c.w * 3 + 1) + 1, y * c.w * 3, (y + 1) * c.w * 3); }
  const crcTable = []; for (let n = 0; n < 256; n++) { let cc = n; for (let k = 0; k < 8; k++) cc = (cc & 1) ? (0xedb88320 ^ (cc >>> 1)) : (cc >>> 1); crcTable[n] = cc >>> 0; }
  const crc = b => { let cc = 0xffffffff; for (const x of b) cc = crcTable[(cc ^ x) & 0xff] ^ (cc >>> 8); return (cc ^ 0xffffffff) >>> 0; };
  const chunk = (type, d) => { const len = Buffer.alloc(4); len.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(type), d]); const cr = Buffer.alloc(4); cr.writeUInt32BE(crc(td)); return Buffer.concat([len, td, cr]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(c.w, 0); ihdr.writeUInt32BE(c.h, 4); ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  fs.writeFileSync(file, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]));
}

// --- one sheet ----------------------------------------------------------------
// bounds in world units, zBand = [zFloorLo, zFloorHi] selects brushes whose
// bottom sits within it (floors and the walls that stand on them); marks from
// the entity list whose origin z is inside [zLo, zHi].
function sheet(name, x1, x2, y1, y2, zFloor, zTop, notes) {
  const SCALE = 0.25, PAD = 40;
  const W = Math.round((x2 - x1) * SCALE) + PAD * 2, H = Math.round((y2 - y1) * SCALE) + PAD * 2 + 60;
  const c = makeCanvas(W, H);
  const toPx = (x, y) => [PAD + (x - x1) * SCALE, PAD + (y2 - y) * SCALE];   // north up
  const inBand = b => b.hi[0] > x1 && b.lo[0] < x2 && b.hi[1] > y1 && b.lo[1] < y2 && b.lo[2] >= zFloor - 40 && b.lo[2] < zTop;
  const list = brushes.filter(inBand).sort((a, b) => a.hi[2] - b.hi[2]);
  for (const b of list) {
    const col = matColour(b.mat);
    const [px1, py2] = toPx(b.lo[0], b.lo[1]), [px2, py1] = toPx(b.hi[0], b.hi[1]);
    if (!col) { if (b.mat !== 'sky') strokeRect(c, px1, py1, px2, py2, [90, 90, 90], true); continue; }
    const top = b.hi[2] - zFloor;
    const k = top <= 1 ? 0.35 : top <= 20 ? 0.5 : top <= 60 ? 0.7 : top <= 140 ? 0.85 : 1.0;
    fillRect(c, px1, py1, px2, py2, col.map(v => Math.round(v * k)));
  }
  // entities
  const inZ = e => e._org && e._org[2] >= zFloor - 40 && e._org[2] < zTop && e._org[0] > x1 && e._org[0] < x2 && e._org[1] > y1 && e._org[1] < y2;
  for (const e of ents) {
    if (e.classname === 'trigger_use' && e.targetname === 'zombie_door' && e._lo && e._lo[2] >= zFloor - 40 && e._lo[2] < zTop) {
      const [ax, by] = toPx(e._lo[0], e._lo[1]), [bx, ay] = toPx(e._hi[0], e._hi[1]);
      if (bx < 0 || ax > W || by < 0 || ay > H) continue;
      strokeRect(c, ax, ay, bx, by, [80, 255, 120]);
      label(c, ax + 2, ay - 9, e.script_flag.replace('enter_', ''), [80, 255, 120], 1);
    }
    if (!inZ(e)) continue;
    const [px, py] = toPx(e._org[0], e._org[1]);
    if (e.script_noteworthy === 'riser_location') dot(c, px, py, 3, [255, 60, 60]);
    else if (e.script_noteworthy === 'dog_location') strokeRect(c, px - 3, py - 3, px + 3, py + 3, [255, 120, 60]);
    else if (e.script_noteworthy === 'initial_spawn') dot(c, px, py, 2, [255, 230, 60]);
    else if (e.targetname === 'zm_perk_machine' || e.classname === 'misc_prefab') dot(c, px, py, 3, [80, 220, 255]);
    else if (e.classname === 'info_player_start') strokeRect(c, px - 4, py - 4, px + 4, py + 4, [255, 230, 60]);
    else if (e.targetname === 'tod_respawn_base' || e.targetname === 'initial_spawn_points') {}
    else if (e.targetname && /^tod_respawn_/.test(e.targetname)) dot(c, px, py, 2, [255, 100, 255]);
    else if (e.classname === 'light') strokeRect(c, px - 2, py - 2, px + 2, py + 2, [255, 255, 160]);
  }
  for (const [bx, by, id] of benches) {
    if (by < y1 || by > y2 || bx < x1 || bx > x2) continue;
    const [px, py] = toPx(bx, by); if (0 < zFloor) continue;
    if (zFloor < -100) continue;
    strokeRect(c, px - 12, py - 4, px + 12, py + 4, [255, 255, 255]); label(c, px - 10, py + 6, 'BENCH ' + id, [255, 255, 255], 1);
  }
  if (zFloor < -100) {
    for (const [bx, by] of parts) { const [px, py] = toPx(bx, by); dot(c, px, py, 2, [255, 255, 255]); }
    if (qr) { const [px, py] = toPx(+qr[1], +qr[2]); strokeRect(c, px - 8, py - 4, px + 8, py + 4, [80, 220, 255]); label(c, px - 8, py + 6, 'QR', [80, 220, 255], 1); }
  }
  let ly = H - 56;
  for (const n of notes) { label(c, PAD, ly, n, [200, 200, 210], 2); ly += 16; }
  fs.mkdirSync(outDir, { recursive: true });
  const file = path.join(outDir, `plan_${name}.png`);
  writePng(file, c);
  console.log(`wrote ${file}  (${W}x${H}, ${list.length} brushes)`);
}

sheet('undercity', -2800, -500, -1200, 260, -384, -100, [
  'UNDERCITY Z -384: VAULT (SPAWN, 4 WINDOWS, QR) - CONDUIT (PARTS SHELF) - SHAFT FOOT',
  'RED DOTS RISERS, YELLOW SPAWNS, GREEN DOOR TRIGGERS, WHITE PART PROPS, CYAN QR',
]);
sheet('plaza', -1560, 1700, -1560, 1560, 0, 200, [
  'PLAZA Z 0: TOWER CORE CENTRE, WINGS N/E/S/W WITH PARTNER BENCHES, SHAFT LANDING W',
  'TELEPORT BAY S, POWER HALL SE, PERK PARKING N WALL. GREEN = DOOR TRIGGERS',
]);
