'use strict';
// tools/haven/review_scene.js — the floor-10 haven's REAL emitted geometry for the
// Blender review (tools/haven/preview.py, docs/202).
//
//   node tools/haven/review_scene.js [--map <path to a generated .map>] [--out <json>]
//
// Reads the .map through tools/convex_brush.js (the planes cod2map is handed) and keeps
// every visible brush near the floor-10 haven (v2, THE HEART: the hall in the opened
// core, its loggia, the porch, the walls, the galleries and the spiral flights around
// them) with its faces, materials and normals; every light entity in the same box; and
// the haven's own anchors from tools/haven_layout.js (the dome, the furniture, the
// teleporter). Never regenerates.
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const CB = require(path.join(ROOT, 'tools', 'convex_brush'));
const H = require(path.join(ROOT, 'tools', 'haven_layout'));

const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d; };
const MAP = path.resolve(ROOT, arg('--map', 'map_source/zm/zm_tod2_cybercity.map'));
const OUT = path.resolve(ROOT, arg('--out', 'art/haven/review/scene.json'));

const LAP = 10, LAP_RISE = 384;
const Z = (LAP - 1) * LAP_RISE + LAP_RISE / 2;     // the haven floor = lap 10's mid landing (3648)
const BOX = { lo: [-1500, -1700, Z - 700], hi: [900, 900, Z + 900] };
const SKIP = /^(clip|clip_player|clip_ai|caulk|nodraw|sky|trigger|portal|hint|skip|mantle|ladder)/i;

const text = fs.readFileSync(MAP, 'utf8');
const brushes = [];
let bad = 0;
for (const m of text.matchAll(/^\/\/ brush \d+ [—-] (.*?)\r?\n\{([\s\S]*?)^\}/gm)) {
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

// light entities: { "classname" "light" ... "origin" ... }
const lights = [];
for (const m of text.matchAll(/^\{\r?\n([\s\S]*?)^\}/gm)) {     // an entity block ends at a line that is just "}" (guids carry braces)
  if (!/^"classname" "light"\r?$/m.test(m[1])) continue;
  const kv = Object.fromEntries([...m[1].matchAll(/^"([^"]+)" "([^"]*)"/gm)].map(x => [x[1], x[2]]));
  const o = (kv.origin || '').split(/\s+/).map(Number);
  if (o.length !== 3 || o.some(v => !Number.isFinite(v))) continue;
  if (o.some((v, i) => v < BOX.lo[i] || v > BOX.hi[i])) continue;
  lights.push({ name: kv.targetname || 'light', origin: o, color: (kv._color || '1 1 1').split(/\s+/).map(Number),
    radius: +kv.radius || 300, stops: +kv.stops || 8 });
}

const f = H.FURN;
const furniture = ['pap', 'station', 'crate', 'perk_a', 'perk_b'].map(k => ({ key: k, org: [...f[k].org, Z], face: f[k].face, half: f[k].half, back: f[k].back, h: f[k].h }));
const scene = {
  schema: 1, map: path.relative(ROOT, MAP).replace(/\\/g, '/'), lap: LAP, z: Z,
  dome: { centre: [H.C[0], H.C[1], Z], R: H.DOME_R, C: H.DOME_C, S: H.DOME_S, top: H.DOME_TOP },
  teleporter: [-H.SPUR_CX, -H.SPUR_PAD_Y, Z],
  respawn: H.RESPAWN.map(p => [p[0], p[1], Z]),
  furniture, brushes, lights,
};
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(scene));
console.log(`HAVEN REVIEW SCENE: ${brushes.length} brushes, ${lights.length} lights near floor ${LAP} (z ${Z}) from ${scene.map}` + (bad ? ` (${bad} unbuildable skipped)` : '') + ` -> ${path.relative(ROOT, OUT)}`);
