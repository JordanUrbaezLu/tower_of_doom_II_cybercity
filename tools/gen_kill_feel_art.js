#!/usr/bin/env node
// =============================================================================
// gen_kill_feel_art.js - THE ABILITY SCREEN TINTS (docs/203, 2026-10-02)
//
// Ported from Hellbound's tools/gen_kill_feel_art.js. THE KILL FEEL ITSELF WAS RETIRED
// the same day (user: "This hell bound work we can remove, I actually dont liek this"):
// the screen blood, the marker art and the module are gone; the name of this tool and
// its GDT stayed so the two tints it still draws keep their proven material recipe:
//   source_data/tod_kill_feel_art/_images/i_tod_demon_vignette.png 512x384 DEMON SLAYER's red edge tint
//   source_data/tod_kill_feel_art/_images/i_tod_fusion_vignette.png 512x384 EXPLOSIVE FUSION's heal flash
//   source_data/tod_kill_feel_art.gdt                                2 image + 2 material entries
// and prints the 4 zone lines (in zone_source/zm_tod2_cybercity.zone).
//
// Procedural, deterministic, dependency-free (node + zlib only) - the same recipe
// as tools/gen_hpbar_art.js: image `i_<name>` + material `<name>` (2d_blend, the
// tools/hpbar_material.template recipe, proven for a server-hudelem SetShader).
// Every image is 512x384 = a multiple of 4 on both sides (a compressed image
// that is not fails conversion silently, memory compressed-image-multiple-of-4).
//
// Consumer: scripts/zm/zm_tod2_cybercity/_tod_ability_fx.gsc (the two vignettes), by MATERIAL name. A GDT change is a
// FULL build. `--check` fails if the PNGs / GDT on disk differ from a fresh render.
// =============================================================================
'use strict';
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const REPO = path.join(__dirname, '..');
const GDT_NAME = 'tod_kill_feel_art';
const PNG_DIR = path.join(REPO, 'source_data', GDT_NAME, '_images');
const GDT_PATH = path.join(REPO, 'source_data', `${GDT_NAME}.gdt`);
const CHECK = process.argv.includes('--check');

const P = {
  black:   [0x0A, 0x07, 0x05],
  blood:   [0xC2, 0x26, 0x3D],
  bloodHi: [0xD6, 0x3A, 0x50],
  bloodLo: [0x7A, 0x14, 0x24],
  demon:   [0xE0, 0x1A, 0x18],
  demonLo: [0x5A, 0x06, 0x08],
  ember:   [0xFF, 0x8E, 0x2E],
  emberLo: [0xB0, 0x3C, 0x08],
};

// ---- tiny PNG encoder (byte-for-byte the gen_hpbar_art.js one) ----------------
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(buf) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}
function chunk(type, data) {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length, 0);
  const td = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(td), 0);
  return Buffer.concat([len, td, crc]);
}
function encodePNG(img) {
  const { w, h, d } = img;
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (w * 4 + 1)] = 0;
    d.copy(raw, y * (w * 4 + 1) + 1, y * w * 4, (y + 1) * w * 4);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
    chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

// ---- raster ---------------------------------------------------------------------
const clamp8 = (v) => Math.max(0, Math.min(255, Math.round(v)));
const lerp = (a, b, t) => a + (b - a) * t;
const mix = (c1, c2, t) => [lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t)];
class Img {
  constructor(w, h) { this.w = w; this.h = h; this.d = Buffer.alloc(w * h * 4, 0); }
  get(x, y) { const i = (y * this.w + x) * 4; return [this.d[i], this.d[i + 1], this.d[i + 2], this.d[i + 3]]; }
  set(x, y, c, a) {
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return;
    const i = (y * this.w + x) * 4;
    this.d[i] = clamp8(c[0]); this.d[i + 1] = clamp8(c[1]); this.d[i + 2] = clamp8(c[2]); this.d[i + 3] = clamp8(a);
  }
  over(x, y, c, t) {
    if (x < 0 || y < 0 || x >= this.w || y >= this.h || t <= 0) return;
    const p = this.get(x, y);
    const a0 = p[3] / 255, a1 = Math.min(1, t);
    const a = a1 + a0 * (1 - a1);
    if (a <= 0) return;
    const out = [0, 1, 2].map((k) => (c[k] * a1 + p[k] * a0 * (1 - a1)) / a);
    this.set(x, y, out, a * 255);
  }
}
function rnd(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---- the vignettes ----------------------------------------------------------------
// An edge tint: alpha 0 in a wide clear ellipse around the reticle, rising to `edge`
// at the frame, with a soft noisy rim so it reads as smoke / heat and not a frame.
// Drawn at full alpha in the image; the hudelem's own alpha sets the on-screen level.
function drawVignette(seed, hi, lo, inner, pow) {
  const W = 512, H = 384;
  const img = new Img(W, H);
  const r = rnd(seed);
  const cx = W / 2, cy = H / 2;
  // a ring of jittered radii so the rim is organic
  const spikes = 24, jit = [];
  for (let i = 0; i < spikes; i++) jit.push(0.9 + r() * 0.2);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const ex = (x + 0.5 - cx) / (W / 2), ey = (y + 0.5 - cy) / (H / 2);
    const ang = (Math.atan2(ey, ex) + Math.PI) / (2 * Math.PI) * spikes;
    const i0 = Math.floor(ang) % spikes, i1 = (i0 + 1) % spikes;
    const j = lerp(jit[i0], jit[i1], ang - Math.floor(ang));
    const q = Math.hypot(ex, ey) / j;          // 0 centre .. ~1 frame edge
    let t = (q - inner) / (1.0 - inner);
    if (t <= 0) continue;
    t = Math.min(1, Math.pow(t, pow));
    img.over(x, y, mix(hi, lo, t * 0.6), t);
  }
  return img;
}

// ---- GDT ------------------------------------------------------------------------
function imageEntry(name, clamp) {
  return `\t"${name}" ( "image.gdf" )
\t{
\t\t"arabicUnsafe" "0"
\t\t"baseImage" "source_data/${GDT_NAME}/_images/${name}.png"
\t\t"clampU" "${clamp}"
\t\t"clampV" "${clamp}"
\t\t"colorSRGB" "1"
\t\t"compositeChannel1" ""
\t\t"compositeChannel2" ""
\t\t"compositeChannel3" ""
\t\t"compositeChannel4" ""
\t\t"compositeImage1" ""
\t\t"compositeImage2" ""
\t\t"compositeImage3" ""
\t\t"compositeImage4" ""
\t\t"compositeSample1" ""
\t\t"compositeSample2" ""
\t\t"compositeSample3" ""
\t\t"compositeSample4" ""
\t\t"compositeType" ""
\t\t"compressionMethod" "compressed high color"
\t\t"coreSemantic" "sRGB3chAlpha"
\t\t"doNotResize" "0"
\t\t"forceStreaming" "0"
\t\t"fromAlpha" "0"
\t\t"germanUnsafe" "0"
\t\t"glossVarianceScale" "1"
\t\t"himipStreaming" "0"
\t\t"imageType" "Texture"
\t\t"japaneseUnsafe" "0"
\t\t"legallyApproved" "0"
\t\t"matureContent" "0"
\t\t"mipBase" "1/1"
\t\t"mipMask" ""
\t\t"mipMode" "Average"
\t\t"mipNorm" "0"
\t\t"noMipMaps" "1"
\t\t"noPicMip" "1"
\t\t"premulAlpha" "0"
\t\t"semantic" "diffuseMap"
\t\t"streamable" "1"
\t\t"textureAtlasColumnCount" "1"
\t\t"textureAtlasRowCount" "1"
\t\t"type" "image"
\t}
`;
}

function main() {
  const tplPath = path.join(__dirname, 'hpbar_material.template');
  if (!fs.existsSync(tplPath)) throw new Error('tools/hpbar_material.template missing - it is the proven 2d_blend material recipe');
  const tpl = fs.readFileSync(tplPath, 'utf8');

  const out = [];   // [material name, image]
  out.push(['tod_demon_vignette', drawVignette(0x0D3E, P.demon, P.demonLo, 0.52, 1.6)]);
  out.push(['tod_fusion_vignette', drawVignette(0x0F05, P.ember, P.emberLo, 0.58, 1.4)]);

  let gdt = '{\n';
  const files = [];
  for (const [name, img] of out) {
    if (img.w % 4 || img.h % 4) throw new Error(`${name}: a compressed image must be a multiple of 4 on both sides`);
    files.push([path.join(PNG_DIR, `i_${name}.png`), encodePNG(img)]);
    gdt += imageEntry(`i_${name}`, 1);
  }
  for (const [name] of out) gdt += tpl.replace(/__NAME__/g, name);
  gdt += '}\n';
  files.push([GDT_PATH, Buffer.from(gdt, 'utf8')]);

  if (CHECK) {
    let bad = 0;
    for (const [p, buf] of files) {
      if (!fs.existsSync(p) || !fs.readFileSync(p).equals(buf)) { console.log('STALE', path.relative(REPO, p)); bad++; }
    }
    console.log(`kill-feel art --check: ${bad ? bad + ' stale' : 'OK (' + out.length + ' images)'}`);
    process.exit(bad ? 1 : 0);
  }
  fs.mkdirSync(PNG_DIR, { recursive: true });
  for (const [p, buf] of files) fs.writeFileSync(p, buf);
  const zone = out.map(([n]) => `image,i_${n}`).concat(out.map(([n]) => `material,${n}`)).join('\n');
  console.log(`[kill-feel-art] ${out.length} PNGs -> ${path.relative(REPO, PNG_DIR)}`);
  console.log(`[kill-feel-art] GDT image+material -> ${path.relative(REPO, GDT_PATH)}`);
  console.log('[kill-feel-art] zone lines:\n' + zone);
}
main();
