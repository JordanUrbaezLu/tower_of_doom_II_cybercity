#!/usr/bin/env node
// =============================================================================
// led_report.js - what is inside the baked .led, and which reflection probe
// pays for it. Read-only; runs in a second.
//
//   node tools/led_report.js                    the deployed LED + the repo map
//   node tools/led_report.js --led <file.led>   any LED (a peer map, an archive)
//   node tools/led_report.js --map <file.map>   attribute against another map
//   node tools/led_report.js --top N            list the N costliest probes (default 12)
//
// WHY THIS EXISTS (2026-10-02, docs/202 v2): the haven halls' FULL build baked an
// LED of 237.3 MB where the build before baked 119.5 MB, and lit surface area
// (tools/measure_lit_area.js) had gone DOWN. The file answers it itself: its
// `volumes` section is nearly the whole LED - the reflection probes' bounce
// grids - and every probe record carries its origin as three floats, so the
// bytes between one probe's origin and the next are that probe's grid. Four
// fitted hall probes (692 x 692 x 576 boxes at the def's default `resolution`
// 4x) were 28.5 MB each; the 144-unit template probe is 2.1 MB; the transit
// bay's flatter 1120 x 1080 x 448 box at 4x is 15.2 MB. A probe's cost follows
// its box SHAPE (a near-cubic box is dense on all three axes), not its volume.
//
// The LED is the bake's intermediate, not the download: the linker turns the
// grids into one probe-volume texture per lighting state (BC6H, in the xpak).
// For the shipped cost read `node tools/xpak_report.js --csv f.csv` and sum the
// newest build's `probeVolume` + `reflectionProbes` rows.
//
// FORMAT (reverse-read 2026-10-02 from this map, map 1 and zm_tower_of_doom):
//   'LED\0' u32 version(29) u32 ? u32 textLen, text (who/when/GPU/quality),
//   u32 sectionCount, then per section: u32 nameLen, name, u32 version,
//   u32 byteSize, data. Sections seen: entities, volumes, outdoor, wave_water,
//   attenuation_volume. Inside `volumes` each probe record holds its origin as
//   three LE float32 (found by value; the records are in no documented order).
// =============================================================================
'use strict';
const fs = require('fs');
const path = require('path');

const argv = process.argv.slice(2);
const opt = (k) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : null; };
const REPO = path.join(__dirname, '..');

// The private TOD II tools root (docs/154), as lint_tod_navmesh.js reads it.
function defaultLed() {
  return 'C:/BO3Tools/TOD2Cybercity/share/raw/maps/zm/zm_tod2_cybercity.led';
}

const LED = opt('--led') || defaultLed();
const MAP = opt('--map') || path.join(REPO, 'map_source', 'zm', 'zm_tod2_cybercity.map');
const TOP = Number(opt('--top') || 12);
if (!fs.existsSync(LED)) { console.error('led_report: no LED at ' + LED); process.exit(2); }

const b = fs.readFileSync(LED);
let o = 0;
const u32 = () => { const v = b.readUInt32LE(o); o += 4; return v; };
if (b.toString('latin1', 0, 3) !== 'LED') { console.error('led_report: not an LED file'); process.exit(2); }
o = 4; const ver = u32(); u32(); const tlen = u32();
const header = b.toString('latin1', o, o + tlen).trim(); o += tlen;
const n = u32();
const sections = [];
for (let i = 0; i < n && o < b.length; i++) {
  const nl = u32(); const name = b.toString('latin1', o, o + nl); o += nl;
  const sv = u32(); const sz = u32();
  sections.push({ name, version: sv, start: o, size: sz }); o += sz;
}
const MB = (x) => (x / 1e6).toFixed(2) + ' MB';
console.log(`LED ${path.basename(LED)}: ${b.length.toLocaleString()} bytes (version ${ver})`);
for (const line of header.split('\n')) if (/^(Time|Quality|Options):/.test(line)) console.log('  ' + line);
for (const s of sections) console.log(`  section ${s.name.padEnd(20)} v${s.version}  ${s.size.toLocaleString().padStart(14)} bytes  ${(100 * s.size / b.length).toFixed(1)}%`);

// ---- attribute the volumes section to each reflection probe --------------
const vol = sections.find(s => s.name === 'volumes');
if (!vol || !fs.existsSync(MAP)) { if (!fs.existsSync(MAP)) console.log('(no map to attribute probes: ' + MAP + ')'); process.exit(0); }
const mapTxt = fs.readFileSync(MAP, 'utf8').replace(/\r\n/g, '\n');
const probes = [];
const re = /\/\/ entity \d+ — ([^\n]*)\n\{\n([\s\S]*?)\n\}/g; let m;
while ((m = re.exec(mapTxt))) {
  const body = m[2]; if (!/"classname" "reflection_probe"/.test(body)) continue;
  const g = (k) => { const r = body.match(new RegExp('"' + k + '" "([^"]*)"')); return r ? r[1] : null; };
  const origin = (g('origin') || '').split(' ').map(Number);
  if (origin.length !== 3 || origin.some(Number.isNaN)) continue;
  probes.push({ label: m[1], origin, half: g('size_max') || '72 72 72 (default)', res: g('resolution') || (g('grid_density') ? 'grid_density ' + g('grid_density') : '4x (default)') });
}
const hits = [];
for (const p of probes) {
  const key = Buffer.alloc(12); p.origin.forEach((v, i) => key.writeFloatLE(v, i * 4));
  p.found = 0; let at = vol.start - 1;
  while ((at = b.indexOf(key, at + 1)) >= 0 && at < vol.start + vol.size) { hits.push({ at, p }); p.found++; }
}
hits.sort((a, x) => a.at - x.at);
const volEnd = vol.start + vol.size;
for (let i = 0; i < hits.length; i++) hits[i].span = (i + 1 < hits.length ? hits[i + 1].at : volEnd) - hits[i].at;
for (const p of probes) p.bytes = 0;
for (const h of hits) h.p.bytes += h.span;
const lead = hits.length ? hits[0].at - vol.start : vol.size;
const sorted = [...probes].sort((a, x) => x.bytes - a.bytes);
console.log(`\nvolumes: ${probes.length} probes in ${path.basename(MAP)}, ${probes.filter(p => p.found).length} found in the LED; ` +
  `${MB(lead)} before the first probe record (the volume_sun's own grid and headers)`);
console.log(`  ${'probe'.padEnd(34)} ${'bytes'.padStart(10)}  half-extent           resolution`);
for (const p of sorted.slice(0, TOP)) console.log(`  ${p.label.padEnd(34)} ${MB(p.bytes).padStart(10)}  ${String(p.half).padEnd(20)}  ${p.res}`);
if (sorted.length > TOP) {
  const rest = sorted.slice(TOP); const sum = rest.reduce((a, p) => a + p.bytes, 0);
  console.log(`  ... ${rest.length} more probes, ${MB(sum)} together`);
}
const missing = probes.filter(p => !p.found);
if (missing.length) console.log('  not found in the LED (not baked, or a different map): ' + missing.map(p => p.label).join(', '));
