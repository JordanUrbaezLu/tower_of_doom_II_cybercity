'use strict';
// tools/battle_arena_review/review_scene.js — the Battle Arena's REAL emitted geometry
// for the Blender review (tools/battle_arena_review/preview.py, docs/185 v2).
//
//   node tools/battle_arena_review/review_scene.js [--map <a generated .map>] [--out <json>]
//
// Reads the .map through tools/convex_brush.js (the planes cod2map is handed) and
// keeps every visible brush of the arena with its faces, materials and normals, every
// light entity inside it, and the layout's own anchors from tools/battle_arena_layout.js
// (the arrivals, the spawn points by kind, the gates, the dais). Never regenerates.
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const CB = require(path.join(ROOT, 'tools', 'convex_brush'));
const L = require(path.join(ROOT, 'tools', 'battle_arena_layout'));

const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d; };
const MAP = path.resolve(ROOT, arg('--map', 'map_source/zm/zm_tod2_cybercity.map'));
const OUT = path.resolve(ROOT, arg('--out', 'art/battle_arena/review/scene.json'));

const A = L.ARENA, o = L.OUTER + 64;
const BOX = { lo: [A.cx - o, A.cy - o, A.z - 80], hi: [A.cx + o, A.cy + o, L.TOP + 40] };
const SKIP = /^(clip|clip_player|clip_ai|caulk|nodraw|sky|trigger|portal|hint|skip|mantle|ladder)/i;

const text = fs.readFileSync(MAP, 'utf8');
const brushes = [];
let bad = 0;
for (const m of text.matchAll(/^\/\/ brush \d+ [—-] (.*?)\r?\n\{([\s\S]*?)^\}/gm)) {
  if (!m[1].startsWith('battle arena')) continue;
  const planes = CB.readPlanes(m[2]);
  if (planes.length < 4) continue;
  if (planes.every(p => SKIP.test(p.mat))) continue;
  let h;
  try { h = CB.hull(planes); } catch (e) { bad++; continue; }
  if (h.hi.some((v, i) => v < BOX.lo[i]) || h.lo.some((v, i) => v > BOX.hi[i])) continue;
  const faces = h.faces.filter(f => !SKIP.test(f.mat) && f.vertices.length >= 3)
    .map(f => ({ mat: f.mat, n: f.n.map(v => +v.toFixed(5)), v: f.vertices.map(p => p.map(x => +x.toFixed(3))) }));
  if (faces.length) brushes.push({ label: m[1], faces });
}

const lights = [];
for (const m of text.matchAll(/^\{\r?\n([\s\S]*?)^\}/gm)) {
  if (!/^"classname" "light"\r?$/m.test(m[1])) continue;
  const kv = Object.fromEntries([...m[1].matchAll(/^"([^"]+)" "([^"]*)"/gm)].map(x => [x[1], x[2]]));
  const p = (kv.origin || '').split(/\s+/).map(Number);
  if (p.length !== 3 || p.some(v => !Number.isFinite(v))) continue;
  if (p.some((v, i) => v < BOX.lo[i] || v > BOX.hi[i])) continue;
  lights.push({ name: kv.targetname || 'light', origin: p, color: (kv._color || '1 1 1').split(/\s+/).map(Number),
    radius: +kv.radius || 300, stops: +kv.stops || 8 });
}

const scene = {
  schema: 1, map: path.relative(ROOT, MAP).replace(/\\/g, '/'),
  centre: [A.cx, A.cy, A.z], half: A.half, ring_z: A.z + L.RING_Z, dais_z: A.z + L.DAIS_Z, dais_half: L.DH, top: L.TOP,
  arrivals: L.ARRIVALS,
  spawns: L.SPAWNS.map(s => ({ kind: s.kind, org: [A.cx + s.x, A.cy + s.y, A.z + s.z] })),
  brushes, lights,
};
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(scene));
console.log(`BATTLE ARENA REVIEW SCENE: ${brushes.length} brushes, ${lights.length} lights, ${scene.spawns.length} spawn points from ${scene.map}` + (bad ? ` (${bad} unbuildable skipped)` : '') + ` -> ${path.relative(ROOT, OUT)}`);
