'use strict';
// The tower's actual brush faces around one break, for tools/war_damage/preview_break.py
// (the same reading as tools/art_cohesion/inventory_tower.js, any height band, any output).
// Usage: node tools/war_damage/preview_inventory.js <lap> <out.json>
const fs = require('fs'), path = require('path'), C = require('../convex_brush');
const root = path.resolve(__dirname, '../..');
const lap = +process.argv[2], out = process.argv[3];
if (!lap || !out) { console.error('usage: preview_inventory.js <lap> <out.json>'); process.exit(2); }
const b = (lap - 1) * 384, zLo = b - 500, zHi = b + 900;
const map = fs.readFileSync(path.join(root, 'map_source/zm/zm_tod2_cybercity.map'), 'utf8');
const rows = [];
for (const m of map.matchAll(/^\/\/ brush \d+ [—-] (.*?)\r?\n\{([\s\S]*?)^\}/gm)) {
  const planes = C.readPlanes(m[2]); if (!planes.some(p => p.mat.startsWith('tod_cc_'))) continue;
  const h = C.hull(planes);
  if (h.hi[2] < zLo || h.lo[2] > zHi || Math.max(...h.lo.slice(0, 2).map(Math.abs), ...h.hi.slice(0, 2).map(Math.abs)) > 1500) continue;
  rows.push({ label: m[1], faces: h.faces.filter(f => f.mat.startsWith('tod_cc_')).map(f => ({ mat: f.mat, n: f.n, vertices: f.vertices })) });
}
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify(rows));
console.log('WAR_PREVIEW_INVENTORY lap', lap, rows.length, 'solids in z', zLo, '..', zHi);
