#!/usr/bin/env node
// =============================================================================
// gen_hpbar_art.js — TOD II over-head health-bar art (docs/174)
//
// Ported from Hellbound's tools/gen_hpbar_art.js (its docs/49 route A) and
// RE-THEMED: smoked glass + light — a near-black translucent track, a thin
// cool-grey frame, a fill lit from the top with a brighter leading edge, and a
// faint lip of the fill's own hue under the frame.
//
// TWO COLOUR FAMILIES, ONE FRAME (user 2026-10-01: "the elites on this map
// have a white bar above them that needs to be changed to red. And then the
// necromancers summoners need to have the white bar. So you can tell the
// difference and you can see how much health they have left"):
//   RED   = ENEMIES: every elite (set e) and the bosses (set b). Pink-white pulse.
//   WHITE = THE NECROMANCER'S HELPERS (set s): thralls, soul hounds, the Mangler.
//           The 2026-09-25 white look, cyan lip, on a smaller bar (an ally's bar
//           must not out-shout an enemy's).
// The frame, track, notches and pulse shape are shared, so the two read as one
// family and only the colour says friend or foe. The user's own red set
// (docs/175) never came back; this generated red replaces that request.
//
// Procedural, deterministic, dependency-free (node + zlib). Re-run after any
// edit; the output is written STRAIGHT INTO the build inputs:
//   source_data/tod_hud_bars/_images/i_tod_hpbar_e_NN[_h1|_h2].png  336x72 ELITE bar, RED (31 files)
//   source_data/tod_hud_bars/_images/i_tod_hpbar_b_NN[_h1|_h2].png  544x80 BOSS bar, RED: Panzer / Keeper / Dealer (31)
//   source_data/tod_hud_bars/_images/i_tod_hpbar_s_NN[_h1|_h2].png  288x64 SUMMON bar, WHITE: the Necromancer's helpers (31)
//     NN = 00..10 fill in tenths (rest frame); _h1 / _h2 = the HIT PULSE frames
//     (small / peak) for NN 01..10 — only the fill's leading edge differs.
//   source_data/tod_hud_bars.gdt                     93 image + 93 material entries
//   docs/174_elite_hpbar_art/zone_lines.txt          the 186 zone lines (pasted in the .zone)
//   docs/174_elite_hpbar_art/precache_lines.txt      the 93 #precache lines (pasted in the .gsc)
//   docs/174_elite_hpbar_art/preview_screen.png / preview_sheet.png / preview_context.png
// Consumer: scripts/zm/zm_tod2_cybercity/_tod_elite_hp.gsc (material names
// tod_hpbar_<e|b|s>_NN). A GDT/PNG change is a FULL build.
//
// Source scale: 4 px per hudelem unit (1 unit = 3 px at 1080p, 4 px at 1440p),
// so the engine only ever downsamples; noMipMaps/noPicMip keep it crisp.
// =============================================================================
'use strict';
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const REPO = path.join(__dirname, '..');
const GDT_NAME = 'tod_hud_bars';
const IMG_DIR = path.join(REPO, 'source_data', GDT_NAME, '_images');
const DOC_DIR = path.join(REPO, 'docs', '174_elite_hpbar_art');

// ---- palette: the shared frame + track ------------------------------------------
const P = {
  black:   [0x05, 0x06, 0x08],   // outer shadow line
  track:   [0x12, 0x14, 0x18],   // smoked-glass track (top)
  trackLo: [0x08, 0x09, 0x0C],   // track floor
  frame:   [0xB4, 0xBA, 0xC4],   // cool grey frame
  frameHi: [0xE6, 0xEA, 0xF0],   // lit top edge
  frameLo: [0x70, 0x76, 0x80],   // shaded bottom edge
};
// ---- the two fill families (friend / foe) -----------------------------------------
// fill/fillHi/fillLo = the fill lit from the top; edge = its brighter leading edge;
// halo = the lip under the frame, the bleed ahead of the edge and the pulse's glow;
// hot = the pulse's core and the heated stretch of fill behind it.
const FILLS = {
  // ENEMIES. A saturated, slightly warm red: reads as red on the near-black night sky
  // AND against the map's magenta/cyan neon (a pure 255,0,0 goes brown on the dark
  // track and pink under bloom). The pulse runs pink-white so it pops off the red.
  red: {
    fill:   [0xE6, 0x1E, 0x2B],
    fillHi: [0xFF, 0x6A, 0x62],   // top highlight
    fillLo: [0x9C, 0x0D, 0x19],   // fill floor
    edge:   [0xFF, 0xA6, 0x96],   // leading edge
    halo:   [0xFF, 0x3E, 0x4E],   // hot red-pink lip / bleed / glow
    hot:    [0xFF, 0xE6, 0xDE],   // pink-white pulse core
  },
  // THE NECROMANCER'S HELPERS. The 2026-09-25 white look, unchanged.
  white: {
    fill:   [0xF2, 0xF4, 0xF7],   // WHITE fill
    fillHi: [0xFF, 0xFF, 0xFF],   // top highlight
    fillLo: [0xC9, 0xCE, 0xD6],   // fill floor (a hair grey so the bar has a body)
    edge:   [0xFF, 0xFF, 0xFF],   // leading edge
    halo:   [0x7F, 0xE8, 0xF4],   // faint cyan lip (Fallen/Blackout accent)
    hot:    [0xFF, 0xFF, 0xFF],
  },
};

// ---- tiny PNG encoder ----------------------------------------------------------
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

// ---- raster helpers --------------------------------------------------------------
class Img {
  constructor(w, h) { this.w = w; this.h = h; this.d = Buffer.alloc(w * h * 4, 0); }
  set(x, y, c, a = 255) {
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return;
    const i = (y * this.w + x) * 4;
    this.d[i] = clamp8(c[0]); this.d[i + 1] = clamp8(c[1]); this.d[i + 2] = clamp8(c[2]); this.d[i + 3] = clamp8(a);
  }
  get(x, y) {
    const i = (y * this.w + x) * 4;
    return [this.d[i], this.d[i + 1], this.d[i + 2], this.d[i + 3]];
  }
  // Porter-Duff OVER: colour c at coverage t onto whatever is there. On a
  // transparent pixel this gives c at alpha t (no dark fringe in the padding).
  blend(x, y, c, t) {
    if (x < 0 || y < 0 || x >= this.w || y >= this.h || t <= 0) return;
    const p = this.get(x, y);
    const pa = p[3] / 255;
    const oa = t + pa * (1 - t);
    if (oa <= 0) return;
    const col = [0, 1, 2].map((i) => (c[i] * t + p[i] * pa * (1 - t)) / oa);
    this.set(x, y, col, 255 * oa);
  }
  rect(x0, y0, w, h, c, a = 255) {
    for (let y = y0; y < y0 + h; y++) for (let x = x0; x < x0 + w; x++) this.set(x, y, c, a);
  }
  blit(src, dx, dy) {
    for (let y = 0; y < src.h; y++) for (let x = 0; x < src.w; x++) {
      const p = src.get(x, y);
      if (p[3] === 0) continue;
      this.blend(dx + x, dy + y, p, p[3] / 255);
    }
  }
  resample(w2, h2) {
    const out = new Img(w2, h2);
    for (let y = 0; y < h2; y++) for (let x = 0; x < w2; x++) {
      const x0 = x * this.w / w2, x1 = (x + 1) * this.w / w2;
      const y0 = y * this.h / h2, y1 = (y + 1) * this.h / h2;
      let r = 0, g = 0, b = 0, a = 0, n = 0;
      for (let yy = Math.floor(y0); yy < Math.ceil(y1); yy++) for (let xx = Math.floor(x0); xx < Math.ceil(x1); xx++) {
        const p = this.get(Math.min(xx, this.w - 1), Math.min(yy, this.h - 1));
        r += p[0] * p[3]; g += p[1] * p[3]; b += p[2] * p[3]; a += p[3]; n++;
      }
      if (a > 0) out.set(x, y, [r / a, g / a, b / a], a / n); else out.set(x, y, [0, 0, 0], 0);
    }
    return out;
  }
}
const clamp8 = (v) => Math.max(0, Math.min(255, Math.round(v)));
const lerp = (a, b, t) => a + (b - a) * t;
const mix = (c1, c2, t) => [lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t)];
function noise(x, y, seed) {
  let n = (x * 374761393 + y * 668265263 + seed * 1442695041) | 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
}

// ---- the bar ----------------------------------------------------------------------
// spec: { w, h, frame (outer shadow px), ring (frame px), ticks[], rivets, seed }
// The picture is a PADDED canvas: the bar body (spec.w x spec.h) sits inside
// spec.padX / spec.padY of transparent margin. The margin is where the HIT
// PULSE (drawHit) swells past the frame; on a rest frame it is empty. The
// margin is symmetric so the waypoint's centre anchor stays the bar's centre.
function canvasSize(spec) { return { cw: spec.w + spec.padX * 2, ch: spec.h + spec.padY * 2 }; }
function barGeom(spec, tenths) {
  const bx = spec.padX + spec.frame, by = spec.padY + spec.frame;
  const bw = spec.w - spec.frame * 2, bh = spec.h - spec.frame * 2;
  const tx = bx + spec.ring, ty = by + spec.ring, tw = bw - spec.ring * 2, th = bh - spec.ring * 2;
  return { tx, ty, tw, th, fw: Math.round(tw * tenths / 10) };
}
function drawBar(spec, tenths) {
  const { cw, ch } = canvasSize(spec);
  const { w, h, frame, ring } = spec;
  const F = FILLS[spec.fill];
  const img = new Img(cw, ch);
  const ox = spec.padX, oy = spec.padY;

  // 1. outer shadow line — a dark gap so the light frame reads on bright sky too
  img.rect(ox, oy, w, h, P.black, 235);

  // 2. cool-grey frame: lit top edge, shaded bottom, flat sides
  const bx = ox + frame, by = oy + frame, bw = w - frame * 2, bh = h - frame * 2;
  for (let y = by; y < by + bh; y++) for (let x = bx; x < bx + bw; x++) {
    const onTop = y < by + ring, onBot = y >= by + bh - ring;
    const onSide = x < bx + ring || x >= bx + bw - ring;
    if (!(onTop || onBot || onSide)) continue;
    let c = P.frame;
    if (onTop) c = mix(P.frame, P.frameHi, 0.7);
    else if (onBot) c = mix(P.frame, P.frameLo, 0.6);
    img.set(x, y, c, 255);
  }
  if (spec.rivets) {
    // boss only: four brighter corner studs
    const r = spec.rivets;
    for (const [rx, ry] of [[bx, by], [bx + bw - r, by], [bx, by + bh - r], [bx + bw - r, by + bh - r]]) {
      img.rect(rx, ry, r, r, P.frameHi, 255);
    }
  }

  // 3. the smoked-glass track (slightly translucent so the world shows through)
  const tx = bx + ring, ty = by + ring, tw = bw - ring * 2, th = bh - ring * 2;
  for (let y = ty; y < ty + th; y++) for (let x = tx; x < tx + tw; x++) {
    const v = (y - ty) / Math.max(1, th - 1);
    let c = mix(P.track, P.trackLo, v);
    const g = (noise(x, y, spec.seed) - 0.5) * 6;
    c = [c[0] + g, c[1] + g, c[2] + g];
    if (y === ty) c = mix(c, F.halo, 0.22);            // faint lip of the fill's hue under the frame
    img.set(x, y, c, 218);
  }
  for (const t of spec.ticks) {                        // notches on the track
    const x = tx + Math.round(tw * t);
    for (let y = ty + 1; y < ty + th - 1; y++) img.blend(x, y, P.frameLo, 0.5);
  }

  // 4. the fill — lit from the top, darker at the floor for body
  const fw = Math.round(tw * tenths / 10);
  if (fw > 0) {
    for (let y = ty; y < ty + th; y++) for (let x = tx; x < tx + fw; x++) {
      const v = (y - ty) / Math.max(1, th - 1);
      let c = v < 0.35 ? mix(F.fillHi, F.fill, v / 0.35) : mix(F.fill, F.fillLo, (v - 0.35) / 0.65);
      const s = (noise(x, y, spec.seed + 3) - 0.5) * 0.02;   // whisper of grain so it is not a flat rect
      c = [c[0] * (1 + s), c[1] * (1 + s), c[2] * (1 + s)];
      if (y === ty + th - 1) c = mix(c, P.frameLo, 0.25);
      img.set(x, y, c, 255);
    }
    // brighter leading edge …
    const edgeW = Math.max(2, Math.round(tw * 0.016));
    for (let x = tx + fw - edgeW; x < tx + fw; x++) {
      for (let y = ty; y < ty + th; y++) img.blend(x, y, F.edge, 0.55);
    }
    // … and a short glow of the fill's hue ahead of it into the track
    const bleed = Math.round(tw * 0.04);
    for (let d = 0; d < bleed; d++) {
      const x = tx + fw + d;
      if (x >= tx + tw) break;
      const t = 0.28 * (1 - d / bleed) * (1 - d / bleed);
      for (let y = ty; y < ty + th; y++) img.blend(x, y, mix(F.fillHi, F.halo, 0.35), t);
    }
  }
  return img;
}

// THE HIT PULSE (user 2026-09-25, after the first play: "I just want the right
// side of the remaining health to pulse ... like a little hit marker ... just
// that little edge"). A waypoint hudelem can only be scaled WHOLE, so the
// pulse is baked: stage 1 (small) and stage 2 (peak) of every fill step add a
// white-hot notch AT THE FILL'S LEADING EDGE that swells past the frame into
// the padding, with a cyan-white glow and the last stretch of fill heated
// toward white. The frame, track and the rest of the fill are pixel-identical
// to the rest frame, so only the edge moves on screen.
const HIT = {
  1: { core: 3, ext: 7,  glow: 10, heat: 0.45, heatLen: 22 },
  2: { core: 5, ext: 13, glow: 16, heat: 0.80, heatLen: 34 },
};
function drawHit(spec, tenths, stage) {
  const img = drawBar(spec, tenths);
  const g = barGeom(spec, tenths);
  if (g.fw <= 0) return img;
  const k = HIT[stage];
  const F = FILLS[spec.fill];
  const s = spec.hitScale;
  const core = Math.round(k.core * s), ext = Math.round(k.ext * s), glow = Math.round(k.glow * s), heatLen = Math.round(k.heatLen * s);
  const xe = g.tx + g.fw;                              // the fill's leading edge
  // heat the last stretch of fill toward the hot core colour
  for (let x = Math.max(g.tx, xe - heatLen); x < xe; x++) {
    const t = k.heat * Math.pow((x - (xe - heatLen)) / heatLen, 1.5);
    for (let y = g.ty; y < g.ty + g.th; y++) img.blend(x, y, F.hot, t);
  }
  // the swelling notch: a solid hot core spanning the track and past the frame,
  // wrapped in a soft glow (hot + the family's halo) that also spills into the padding
  const y0 = g.ty - ext, y1 = g.ty + g.th + ext;       // core vertical span
  const glowC = mix(F.hot, F.halo, 0.45);
  for (let y = y0 - glow; y < y1 + glow; y++) for (let x = xe - core - glow; x < xe + core + glow; x++) {
    const dx = Math.max(0, Math.abs(x + 0.5 - xe) - core);
    const dy = Math.max(0, y0 - (y + 0.5), (y + 0.5) - y1);
    const d = Math.sqrt(dx * dx + dy * dy);
    if (d === 0) { img.blend(x, y, F.hot, 1); continue; }
    const t = Math.pow(Math.max(0, 1 - d / glow), 2) * 0.85;
    img.blend(x, y, glowC, t);
  }
  return img;
}

// SIZES (user 2026-09-25: "It's too small ... both height and width"). The body
// grew ~1.6x wide / ~1.7x tall from the first build (48x6 -> 76x10 units). The
// source stays 4 px per hudelem unit (1 unit = 3 px at 1080p), and the padding
// is part of the drawn size: elite canvas 336x72 -> 84x18 units, boss 544x80 ->
// 136x20 units. _tod_elite_hp.gsc TOD_HPBAR_W/H must equal canvas / 4 (the
// gate checks it).
// The SUMMON bar (2026-10-01) is ~84% of the elite's body: a Necromancer can run
// six helpers at once, and an ally's bar must not out-shout an enemy's. Body
// 256x32 = 64x8 units (192x24 px @1080p), canvas 288x64 -> 72x16 units.
const ELITE  = { w: 304, h: 40, padX: 16, padY: 16, frame: 3, ring: 3, ticks: [0.25, 0.5, 0.75], rivets: 0, seed: 17, hitScale: 1.0,  fill: 'red' };
const BOSS   = { w: 512, h: 48, padX: 16, padY: 16, frame: 4, ring: 4, ticks: [1 / 3, 2 / 3], rivets: 4, seed: 31, hitScale: 1.15, fill: 'red' };
const SUMMON = { w: 256, h: 32, padX: 16, padY: 16, frame: 3, ring: 3, ticks: [0.25, 0.5, 0.75], rivets: 0, seed: 23, hitScale: 0.85, fill: 'white' };

// ---- GDT + zone emission ------------------------------------------------------------
// The image entry is the i_tod_win_emblem recipe (source_data/tod_ui_images.gdt, the
// map's one proven SetShader pair), BC7 ("compressed high color") like it: 62 images
// raw would be ~7 MB resident, and no line in the source is thinner than 3 px.
// clampU/V 1 so the edge never wraps.
function imageEntry(name) {
  return `\t"${name}" ( "image.gdf" )
\t{
\t\t"arabicUnsafe" "0"
\t\t"baseImage" "source_data/${GDT_NAME}/_images/${name}.png"
\t\t"clampU" "1"
\t\t"clampV" "1"
\t\t"colorSRGB" "1"
\t\t"compressionMethod" "uncompressed"
\t\t"coreSemantic" "sRGB3chAlpha"
\t\t"doNotResize" "0"
\t\t"forceStreaming" "0"
\t\t"fromAlpha" "0"
\t\t"imageType" "Texture"
\t\t"mipBase" "1/1"
\t\t"mipMode" "Average"
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
// The material entry is tools/hpbar_material.template = the byte-for-byte
// tod_win_emblem 2d_blend block with the two names substituted.
function materialEntry(tpl, name) { return tpl.replace(/__NAME__/g, name); }

function main() {
  fs.mkdirSync(IMG_DIR, { recursive: true });
  fs.mkdirSync(DOC_DIR, { recursive: true });
  const tpl = fs.readFileSync(path.join(__dirname, 'hpbar_material.template'), 'utf8');
  if (!tpl.includes('__NAME__')) throw new Error('hpbar_material.template has no __NAME__ placeholder');
  // clear stale PNGs (an old size or a retired name must not linger as a build input)
  for (const f of fs.readdirSync(IMG_DIR)) if (/^i_tod_hpbar_.*\.png$/.test(f)) fs.unlinkSync(path.join(IMG_DIR, f));

  const GROUND = [0x1C, 0x1A, 0x22];   // a mid-dark ground, not black: both families must read on both
  const names = [];
  const sets = [['e', ELITE], ['b', BOSS], ['s', SUMMON]];
  for (const [tag, spec] of sets) {
    for (let q = 0; q <= 10; q++) {
      const base = `tod_hpbar_${tag}_${String(q).padStart(2, '0')}`;   // MATERIAL name; image = i_ + it
      fs.writeFileSync(path.join(IMG_DIR, `i_${base}.png`), encodePNG(drawBar(spec, q)));
      names.push(base);
      if (q === 0) continue;                                            // an empty bar has no edge to pulse
      for (const st of [1, 2]) {
        const n = `${base}_h${st}`;
        fs.writeFileSync(path.join(IMG_DIR, `i_${n}.png`), encodePNG(drawHit(spec, q, st)));
        names.push(n);
      }
    }
  }

  // PREVIEW at the real 1080p on-screen size (1 hudelem unit = 3 px; canvas = 4 px/unit):
  // every fill step at rest, then one hit sequence (rest -> peak -> small -> rest) at 60 %.
  const cols = [];
  let H = 12;
  for (const [, spec] of sets) {
    const { cw, ch } = canvasSize(spec);
    const dw = Math.round(cw * 3 / 4), dh = Math.round(ch * 3 / 4);
    cols.push({ spec, dw, dh });
    H += 11 * (dh + 2) + 4 * (dh + 2) + 30;
  }
  const W = Math.max(...cols.map((c) => c.dw)) + 24;
  const screen = new Img(W, H);
  screen.rect(0, 0, W, H, GROUND, 255);
  let py = 10;
  for (const { spec, dw, dh } of cols) {
    for (let q = 10; q >= 0; q--) { screen.blit(drawBar(spec, q).resample(dw, dh), 12, py); py += dh + 2; }
    py += 12;
    for (const st of [0, 2, 1, 0]) {
      const img = st ? drawHit(spec, 6, st) : drawBar(spec, 6);
      screen.blit(img.resample(dw, dh), 12, py); py += dh + 2;
    }
    py += 16;
  }
  fs.writeFileSync(path.join(DOC_DIR, 'preview_screen.png'), encodePNG(screen));
  // native-size close-up of one hit sequence, for judging the edge shape
  const { cw, ch } = canvasSize(ELITE);
  const sheet = new Img(cw + 20, 4 * (ch + 6) + 14);
  sheet.rect(0, 0, sheet.w, sheet.h, GROUND, 255);
  [0, 2, 1, 0].forEach((st, i) => sheet.blit(st ? drawHit(ELITE, 6, st) : drawBar(ELITE, 6), 10, 8 + i * (ch + 6)));
  fs.writeFileSync(path.join(DOC_DIR, 'preview_sheet.png'), encodePNG(sheet));
  // FRIEND vs FOE at 1080p on three grounds (night sky, the dark ground, a magenta
  // neon wash): a boss and an elite (RED) beside two helpers (WHITE), as they meet
  // in a fight. This is the picture that answers "can you tell the difference".
  const grounds = [[0x05, 0x06, 0x0B], GROUND, [0x5A, 0x1E, 0x58]];
  const row = [[BOSS, 7], [ELITE, 4], [SUMMON, 9], [SUMMON, 3]];
  const dims = row.map(([spec]) => { const c = canvasSize(spec); return [Math.round(c.cw * 3 / 4), Math.round(c.ch * 3 / 4)]; });
  const rowW = dims.reduce((a, d) => a + d[0] + 14, 14), rowH = Math.max(...dims.map((d) => d[1])) + 16;
  const ctx = new Img(rowW, rowH * grounds.length);
  grounds.forEach((gc, gi) => {
    ctx.rect(0, gi * rowH, rowW, rowH, gc, 255);
    let x = 14;
    row.forEach(([spec, q], i) => {
      const [dw, dh] = dims[i];
      ctx.blit(drawBar(spec, q).resample(dw, dh), x, gi * rowH + Math.round((rowH - dh) / 2));
      x += dw + 14;
    });
  });
  fs.writeFileSync(path.join(DOC_DIR, 'preview_context.png'), encodePNG(ctx));

  let gdt = '{\n';
  for (const n of names) gdt += imageEntry(`i_${n}`);
  for (const n of names) gdt += materialEntry(tpl, n);
  gdt += '}\n';
  fs.writeFileSync(path.join(REPO, 'source_data', `${GDT_NAME}.gdt`), gdt);

  const zone = names.map((n) => `image,i_${n}`).concat(names.map((n) => `material,${n}`)).join('\n') + '\n';
  fs.writeFileSync(path.join(DOC_DIR, 'zone_lines.txt'), zone);
  // the #precache block _tod_elite_hp.gsc carries (the gate compares it)
  fs.writeFileSync(path.join(DOC_DIR, 'precache_lines.txt'), names.map((n) => `#precache( "material", "${n}" );`).join('\n') + '\n');

  for (const [tag, spec] of sets) {
    const { cw, ch } = canvasSize(spec);
    console.log(`[hpbar-art] set ${tag} (${spec.fill}): canvas ${cw}x${ch} px = draw ${cw / 4}x${ch / 4} units (${Math.round(cw * 3 / 4)}x${Math.round(ch * 3 / 4)} px @1080p)`);
  }
  console.log(`[hpbar-art] ${names.length} PNGs -> ${path.relative(REPO, IMG_DIR)}; GDT ${names.length} images + ${names.length} materials; ${names.length * 2} zone lines`);
}
main();
