// export_brushes.js - the .map's own convex brushes near an eye, as planes, for view.py (docs/196 §3).
//
//   node tools/sky3d/screenshot_fit/export_brushes.js --eye -6,628,19452 [--radius 16000] [--zmin 12000]
//        [--out tmp/screenshot_fit/brushes.json]
//
// Reads map_source/zm/zm_tod2_cybercity.map through tools/convex_brush.js (the planes cod2map is handed), keeps
// every brush whose footprint is within --radius of the eye and whose top is above --zmin, and writes
// [{ l: label, p: [[nx, ny, nz, d], ...], m: [material, ...], lo, hi }].
'use strict';
const fs = require('fs');
const path = require('path');
const REPO = path.resolve(__dirname, '..', '..', '..');
const CB = require(path.join(REPO, 'tools', 'convex_brush'));

const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d; };
const eye = arg('--eye', '').split(',').map(Number);
if (eye.length !== 3 || eye.some((v) => !Number.isFinite(v))) { console.error('--eye x,y,z is required'); process.exit(1); }
const radius = Number(arg('--radius', '16000')), zmin = Number(arg('--zmin', '12000'));
const out = path.resolve(REPO, arg('--out', 'tmp/screenshot_fit/brushes.json'));

const text = fs.readFileSync(path.join(REPO, 'map_source', 'zm', 'zm_tod2_cybercity.map'), 'utf8');
const re = /^\/\/ brush \d+ [—-] (.*)\r?\n\{([\s\S]*?)^\}/gm;
const keep = [];
let m, bad = 0;
while ((m = re.exec(text))) {
  const planes = CB.readPlanes(m[2]);
  if (!planes.length) continue;
  let h;
  try { h = CB.hull(planes); } catch (e) { bad++; continue; }
  const dx = Math.max(h.lo[0] - eye[0], 0, eye[0] - h.hi[0]), dy = Math.max(h.lo[1] - eye[1], 0, eye[1] - h.hi[1]);
  if (Math.hypot(dx, dy) > radius || h.hi[2] < zmin) continue;
  keep.push({ l: m[1], p: planes.map((p) => [...p.n, p.d]), m: planes.map((p) => p.mat), lo: h.lo, hi: h.hi });
}
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify(keep));
console.log(`brushes ${keep.length} near (${eye.join(', ')}) -> ${path.relative(REPO, out)}` + (bad ? ` (${bad} unbuildable skipped)` : ''));
