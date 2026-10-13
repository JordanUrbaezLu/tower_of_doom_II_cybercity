#!/usr/bin/env node
// =============================================================================
// lint_tod_navmesh.js — READ THE NAVMESH cod2map ACTUALLY WROTE and prove the
// towers are ONE connected walk each. Gate, not advisory.
//
// WHY THIS EXISTS (2026-09-04, user: "random spots on the map zombies won't
// attack you ... around floor 42-44 they won't but above and below they will ...
// there are spots where you just can't get targeted").
//
// Zombies do not chase the player. They chase `player.last_valid_position`, the
// player's cached navmesh point (stock player_shared::last_valid_position),
// and they need a PATH to it. Both are navmesh questions, so "won't attack HERE"
// is always "the mesh under HERE is wrong". Every previous pass on this bug
// reasoned about the mesh from the .map, the seeds and the .hkt BYTE SIZE,
// because nothing could read the mesh itself. This tool reads it.
//
// WHAT IT FOUND THE FIRST TIME IT RAN: 18 connected components. The tower was
// cut into horizontal SLABS — z 0..6170, 6228..6938, 7045..12314, 12342..14618,
// 14785..16154, 16321+ — and the spire, 10,000 units away, was cut at the SAME
// heights. Faces exist on every flight (a vertex census is green), but the
// faces on either side of each seam have oppositeFace = -1: the slabs are not
// stitched. Floor 43 (z 16128-16512) sits on the 16154/16321 seam; floor 17 on
// the 6170 one (the v17.7 "no mesh above floor 17" outage was this seam PLUS
// pruning); floors 19, 33 and 39 on the others. A player standing on a seam
// island cannot be reached from either side, and a zombie chasing across a
// seam stops dead.
//
// THE CAUSE (proven by compile + re-read, ~45 s a round): every seam was inside
// the E flight of ODD laps 17/19/33/39/43 — the same laps on both towers, which
// rules out anything spatial and points at per-lap arithmetic. The stair ramp
// wedge's top plane passed EXACTLY through every tread's front-top nosing edge,
// handing Havok a walkable plane with fifteen coplanar contact lines per flight;
// its overlapping-triangle fixup slivers that, and on laps whose plane
// arithmetic (a function of y and z only — hence identical 10,000 units away in
// x) rounds badly, the ramp's faces come out unstitched. Disabling the
// simplifier's height partitioning through a per-map settings override changed
// the face count and left every seam, so that was NOT it. The fix is RAMP_LIFT
// (2) in gen_tower_map.js: the whole wedge sits 2 above the nosings, no tread
// edge touches the plane, and the same mesh re-read as 2 components (tower +
// crown road, spire). This tool is what proved that and keeps proving it on
// every full build (build_map.ps1, right after cod2map).
//
// FILE FORMAT (Havok 2014.2 binary tagfile, reverse-read from the bytes; every
// claim below was validated against the mesh it decoded — a/b < V, oppositeFace
// < F, startEdge[i+1]-startEdge[i] == numEdges[i] for all 1262 faces):
//   * magic CAB00D1E D011FACE; several tagfiles concatenated (settings, user
//     edge pairs, cluster graph, query mediator + hkaiNavMesh).
//   * ints are LEB128 varints with the SIGN IN THE LOW BIT (3 -> -1, 8 -> 4).
//   * an array of structs is [count][member bitfield][per present member:
//     one type varint, then `count` values] — struct-of-arrays.
//   * hkaiNavMesh members in order: faces{startEdgeIndex, startUserEdgeIndex,
//     numEdges, numUserEdges, clusterIndex, padding}, edges{a, b, oppositeEdge,
//     oppositeFace, flags, paddingByte, userEdgeCost}, vertices (hkVector4 =
//     4 float32, IN METRES: game units / 39.3701, plain x,y,z order).
//   The object data follows the LAST type descriptor of the tagfile that
//   declares hkaiNavMesh; we anchor on that and search a short window for the
//   faces array signature (count, bitfield, type 8, ascending run from 0).
//
// USAGE
//   node tools/lint_tod_navmesh.js [path/to/zm_tod2_cybercity_navmesh.hkt]
//        [--json out.json] [--verbose] [--no-gate]
//   Default path = the mod tools' share/raw/maps/zm/<map>_navmesh.hkt.
//   Exit 1 when the gate fails (see GATE below). --no-gate = report only.
//
// GATE. Regions are classified by face centroid: TOWER (|x|,|y| < 700, the
// 50-floor spiral incl. the base arena), OTHER (the
// crown, causeway, breather spurs, teleport bay). The gate requires:
//   1. every TOWER floor's faces (per-floor z bands of LAP_RISE 384) share ONE
//      component with floor 1 — no slab seams, no islands;
//   2. no island (component) of >= ISLAND_MIN_FACES faces inside the tower.
//      (The Endless Spire's own check left with the spire, 2026-09-29.)
//   3. (docs/163, when _tod_crown_data.gsc says jumppad_enabled 1) THE CROWN
//      ISLAND: a face under hall_center(), the jump pad sharing the hall's
//      component, and the landing sharing the tower's floor-1 component.
//   Singleton slivers OUTSIDE the towers are reported, not failed.
// =============================================================================
'use strict';
const fs = require('fs');
const path = require('path');

const M = 39.3701;                 // Havok metres -> game units
const LAP_RISE = 384;
const TOWER_FLOORS = 50;
const ISLAND_MIN_FACES = 1;        // any island inside a tower fails

const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const opt = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : undefined; };
const VERBOSE = flag('--verbose');
const NO_GATE = flag('--no-gate');

function defaultHkt() {
  const roots = [
    'C:/BO3Tools/TOD2Cybercity',
  ];
  for (const r of roots) {
    const p = path.join(r, 'share/raw/maps/zm/zm_tod2_cybercity_navmesh.hkt');
    if (fs.existsSync(p)) return p;
  }
  return null;
}

const HKT = args.find(a => !a.startsWith('--') && a.endsWith('.hkt')) || defaultHkt();
if (!HKT || !fs.existsSync(HKT)) { console.error('lint_tod_navmesh: no .hkt found (' + HKT + ')'); process.exit(2); }
const buf = fs.readFileSync(HKT);
const N = buf.length;

// ---- varints ----------------------------------------------------------------
function vread(pos) {
  let v = 0, s = 0, i = pos;
  for (;;) { const b = buf[i++]; v += (b & 0x7f) * Math.pow(2, s); s += 7; if (!(b & 0x80)) break; if (s > 63 || i > N) throw new Error('bad varint @' + pos); }
  return [v, i];
}
const sm = (v) => (v & 1) ? -Math.floor(v / 2) : v / 2;   // sign in the low bit
function readArr(pos, n) { const [t, p0] = vread(pos); const out = new Array(n); let p = p0; for (let k = 0; k < n; k++) { const [v, q] = vread(p); out[k] = sm(v); p = q; } return [t, out, p]; }

// ---- locate the hkaiNavMesh object ----------------------------------------
function lastIndexOfStr(s, from) { const b = Buffer.from(s, 'latin1'); return buf.lastIndexOf(b, from === undefined ? N : from); }
const meshType = lastIndexOfStr('hkaiNavMesh\u0000') >= 0 ? lastIndexOfStr('hkaiNavMesh\u0000') : lastIndexOfStr('hkaiNavMesh');
if (meshType < 0) { console.error('lint_tod_navmesh: no hkaiNavMesh type in file'); process.exit(2); }
// the tagfile's descriptor list ends with hkaiStreamingSetVolumeConnection's last member
const anchor = buf.indexOf(Buffer.from('oppositeCellIndex', 'latin1'), meshType);
if (anchor < 0) { console.error('lint_tod_navmesh: descriptor anchor not found'); process.exit(2); }

function findFaces(from) {
  for (let s = from; s < from + 96; s++) {
    try {
      const [c, p1] = vread(s); const F = sm(c);
      if (F < 100 || F > 200000) continue;
      const [bits, p2] = vread(p1);
      if (!(bits & 1)) continue;
      const [t, p3] = vread(p2);
      if (t !== 8) continue;
      let p = p3, prev = -1, ok = true;
      for (let k = 0; k < Math.min(F, 64); k++) { const [v, q] = vread(p); const d = sm(v); if (k === 0 && d !== 0) { ok = false; break; } if (d < prev) { ok = false; break; } prev = d; p = q; }
      if (ok) return { F, bits, pos: p1 };
    } catch (e) { /* keep scanning */ }
  }
  return null;
}
const fh = findFaces(anchor + 'oppositeCellIndex'.length);
if (!fh) { console.error('lint_tod_navmesh: faces array not found after descriptor table'); process.exit(2); }

const FACE_MEMBERS = ['startEdgeIndex', 'startUserEdgeIndex', 'numEdges', 'numUserEdges', 'clusterIndex', 'padding'];
const EDGE_MEMBERS = ['a', 'b', 'oppositeEdge', 'oppositeFace', 'flags', 'paddingByte', 'userEdgeCost'];
const F = fh.F;
const faces = {};
let pos = fh.pos;
{
  const [bits, p] = vread(pos); pos = p;
  for (let m = 0; m < FACE_MEMBERS.length; m++) {
    if (!(bits & (1 << m))) continue;
    const [t, arr, q] = readArr(pos, F); faces[FACE_MEMBERS[m]] = arr; pos = q;
  }
}
for (const need of ['startEdgeIndex', 'numEdges']) if (!faces[need]) { console.error('lint_tod_navmesh: faces lack ' + need); process.exit(2); }
let consistent = 0;
for (let i = 0; i + 1 < F; i++) if (faces.startEdgeIndex[i + 1] - faces.startEdgeIndex[i] === faces.numEdges[i]) consistent++;
if (consistent !== F - 1) { console.error(`lint_tod_navmesh: face table inconsistent (${consistent}/${F - 1}) — format drift, refusing to judge`); process.exit(2); }
const E_expect = faces.startEdgeIndex[F - 1] + faces.numEdges[F - 1];

const edges = {};
let E;
{
  const [c, p1] = vread(pos); E = sm(c);
  if (E !== E_expect) { console.error(`lint_tod_navmesh: edge count ${E} != implied ${E_expect}`); process.exit(2); }
  const [bits, p2] = vread(p1); pos = p2;
  for (let m = 0; m < EDGE_MEMBERS.length; m++) {
    if (!(bits & (1 << m))) continue;
    if (EDGE_MEMBERS[m] === 'userEdgeCost') { const [t, q0] = vread(pos); pos = q0 + 4 * E; continue; }
    const [t, arr, q] = readArr(pos, E); edges[EDGE_MEMBERS[m]] = arr; pos = q;
  }
}
for (const need of ['a', 'b', 'oppositeFace']) if (!edges[need]) { console.error('lint_tod_navmesh: edges lack ' + need); process.exit(2); }
const V = Math.max(...edges.a, ...edges.b) + 1;
for (const o of edges.oppositeFace) if (o >= F) { console.error('lint_tod_navmesh: oppositeFace out of range'); process.exit(2); }

// vertices: float32 x4 in metres, right after the edge arrays (short header)
let vstart = null;
for (let s = pos - 4; s < pos + 24; s++) {
  if (s < 0 || s + 16 * V > N) continue;
  let ok = true;
  for (let k = 0; k < V; k++) {
    const i = s + 16 * k; const x = buf.readFloatLE(i), y = buf.readFloatLE(i + 4), z = buf.readFloatLE(i + 8);
    if (!(Number.isFinite(x) && Number.isFinite(y) && Number.isFinite(z) && Math.abs(x) < 1500 && Math.abs(y) < 1500 && z > -100 && z < 1500)) { ok = false; break; }
  }
  if (ok) { vstart = s; break; }
}
if (vstart === null) { console.error('lint_tod_navmesh: vertex array not found after edges'); process.exit(2); }
const P = new Array(V);
for (let k = 0; k < V; k++) { const i = vstart + 16 * k; P[k] = [buf.readFloatLE(i) * M, buf.readFloatLE(i + 4) * M, buf.readFloatLE(i + 8) * M]; }

// ---- centroids, components ---------------------------------------------------
const C = new Array(F);
for (let f = 0; f < F; f++) {
  const s = faces.startEdgeIndex[f], n = faces.numEdges[f]; let cx = 0, cy = 0, cz = 0;
  for (let e = s; e < s + n; e++) { const p = P[edges.a[e]]; cx += p[0]; cy += p[1]; cz += p[2]; }
  C[f] = [cx / n, cy / n, cz / n];
}
const comp = new Int32Array(F).fill(-1); let nc = 0;
for (let f = 0; f < F; f++) {
  if (comp[f] >= 0) continue; const st = [f]; comp[f] = nc;
  while (st.length) { const g = st.pop(); const s = faces.startEdgeIndex[g], n = faces.numEdges[g]; for (let e = s; e < s + n; e++) { const o = edges.oppositeFace[e]; if (o >= 0 && comp[o] < 0) { comp[o] = nc; st.push(o); } } }
  nc++;
}
const compSize = new Array(nc).fill(0); for (let f = 0; f < F; f++) compSize[comp[f]]++;
function region(c) { if (Math.abs(c[0]) < 700 && Math.abs(c[1]) < 700) return 'tower'; return 'other'; }

function floorTable(regionName, floors, xOff) {
  const rows = []; let baseComp = null; const bad = [];
  for (let fl = 1; fl <= floors + 1; fl++) {
    const zl = (fl - 1) * LAP_RISE - 8, zh = fl * LAP_RISE + 8;
    const fs2 = []; for (let f = 0; f < F; f++) if (region(C[f]) === regionName && C[f][2] >= zl && C[f][2] <= zh) fs2.push(f);
    if (fl === 1 && fs2.length) baseComp = comp[fs2[0]];
    const comps = [...new Set(fs2.map(f => comp[f]))].sort((a, b) => b - a);
    const foreign = comps.filter(c => c !== baseComp);
    if (fs2.length === 0 && fl <= floors) bad.push({ fl, why: 'NO FACES' });
    if (foreign.length) bad.push({ fl, why: 'split: comps ' + comps.map(c => `${c}(${compSize[c]})`).join(' ') });
    rows.push({ fl, faces: fs2.length, comps, foreign: foreign.length > 0 });
  }
  return { baseComp, rows, bad };
}
const tower = floorTable('tower', TOWER_FLOORS, 0);

// ---- THE CROWN ISLAND (docs/163) ---------------------------------------------
// Once the causeway is CUT (gen_tower_map.js CW_CUT) the crown hall and its stub
// are a third walk, reached only by spawning there and left only by the one-way
// jump pad. Nothing above checks it — it is region 'other' — and it no longer
// shares a component with the tower, so its mesh now rests on its OWN seeds.
// Three facts, each a face under a generated anchor (point-in-polygon in plan,
// face within 64u of the anchor's height), all read from _tod_crown_data.gsc so
// a parity flip or a moved pad follows automatically:
//   1. the HALL is meshed at all (zombies spawn there from the first frame);
//   2. the PAD shares the hall's component (a player waiting at the pad is
//      reachable — otherwise the launch deck is a safe camp);
//   3. the LANDING shares the tower's floor-1 component (the party arrives on
//      ground the horde can reach).
function crownAnchors() {
  const f = path.join(__dirname, '..', 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_crown_data.gsc');
  if (!fs.existsSync(f)) return null;
  const t = fs.readFileSync(f, 'utf8');
  const en = t.match(/function jumppad_enabled\(\)\s*\{\s*return\s+(\d+);/);
  if (!en || en[1] !== '1') return null;
  const vec = (name) => {
    const m = t.match(new RegExp(`function ${name}\\(\\)\\s*\\{\\s*return\\s*\\(\\s*(-?[\\d.]+),\\s*(-?[\\d.]+),\\s*(-?[\\d.]+)\\s*\\);`));
    if (!m) throw new Error(`lint_tod_navmesh: _tod_crown_data.gsc has no ${name}() — regenerate (node tools/gen_tower_map.js)`);
    return m.slice(1, 4).map(Number);
  };
  // 2026-09-28: THE ALARM BUTTON's stand (a clip, `crown hall alarm button stand body`, +-10) stands ON hall_center(),
  // so the navmesh has a deliberate hole exactly there. The hall's probe point steps 64 south, still on the dais and
  // clear of the stand; it still proves the hall is meshed and names the hall's component.
  let hall = vec('hall_center');
  const btn = t.match(/function alarm_button_org\(\)\s*\{\s*return\s*\(\s*(-?[\d.]+),\s*(-?[\d.]+),/);
  if (btn && Math.abs(Number(btn[1]) - hall[0]) < 32 && Math.abs(Number(btn[2]) - hall[1]) < 32) hall = [hall[0], hall[1] - 64, hall[2]];
  return { hall, pad: vec('jumppad_launch_org'), land: vec('jumppad_land_center') };
}
function faceUnder(p) {
  for (let f = 0; f < F; f++) {
    const s = faces.startEdgeIndex[f], n = faces.numEdges[f];
    // height by the face's own vertex span, not its centroid: a ramp face's
    // centroid can sit 100+ units from the tread a point is standing on
    let zlo = Infinity, zhi = -Infinity;
    for (let e = s; e < s + n; e++) { const z = P[edges.a[e]][2]; if (z < zlo) zlo = z; if (z > zhi) zhi = z; }
    if (p[2] < zlo - 48 || p[2] > zhi + 48) continue;
    let inside = false;
    for (let e = s, k = s + n - 1; e < s + n; k = e++) {
      const a = P[edges.a[e]], b = P[edges.a[k]];
      if (((a[1] > p[1]) !== (b[1] > p[1])) && (p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0])) inside = !inside;
    }
    if (inside) return f;
  }
  return -1;
}
const sourceMap=fs.readFileSync(path.join(__dirname,'../map_source/zm/zm_tod2_cybercity.map'),'utf8');
const towerDrops=require('./broken_tower_contract').read(sourceMap);
if(towerDrops.length) {
  const descentRegion=c=>c[2]>=-8&&c[2]<=(TOWER_FLOORS+1)*LAP_RISE+8?region(c):'other';
  const descent=require('./broken_tower_navcheck').check(towerDrops,C,comp,descentRegion,faceUnder);
  tower.bad=descent.bad;tower.descent=descent;tower.topComp=descent.topComp;
  // Each section must remain one connected walk; only the authored cuts may
  // split it. No arbitrary component-count or per-floor waiver is accepted.
  if(tower.baseComp!==descent.baseComp) tower.bad.push({fl:1,why:'base anchor disagrees with the lowest descent section'});
}
const crownA = crownAnchors();
const crown = { checked: !!crownA, bad: [] };
if (crownA) {
  crown.hall = faceUnder(crownA.hall);
  crown.pad = faceUnder(crownA.pad);
  crown.land = faceUnder(crownA.land);
  if (crown.hall < 0) crown.bad.push('the crown hall has NO navmesh under hall_center() — the crown island\'s seeds did not take');
  if (crown.pad < 0) crown.bad.push('the jump pad has NO navmesh under jumppad_launch_org()');
  else if (crown.hall >= 0 && comp[crown.pad] !== comp[crown.hall])
    crown.bad.push(`the jump pad (comp ${comp[crown.pad]}) is not in the hall's component (${comp[crown.hall]}) — the hall's zombies cannot reach a player at the pad`);
  if (crown.land < 0) crown.bad.push('the jump pad landing has NO navmesh under jumppad_land_center()');
  else if (comp[crown.land] !== (tower.topComp ?? tower.baseComp))
    crown.bad.push(`the jump pad landing (comp ${comp[crown.land]}) is not in the tower's arrival component (${tower.topComp ?? tower.baseComp}) — the party lands where the horde cannot follow`);
}

// Transit pads must sit on each area's real walking component. Teleports do
// not join components or weaken the ordinary-walk/drop gates above.
const transitRoutes=require('./tower_transit_contract').read(sourceMap);
const transitBad=require('./tower_transit_contract').nativeCheck(transitRoutes,faceUnder,comp,zone=>{
  if(zone==='roof_zone')return crownA.land;
  if(zone==='crown_zone')return crownA.hall;
  if(zone==='base_zone')return [0,-480,0];
  const lap=Number(zone.match(/^lap(\d+)_zone$/)[1]);
  return [-336,-336,(lap-1)*LAP_RISE+192];
});

// ---- THE BATTLE ARENA (docs/185) --------------------------------------------
// A fourth walk, reached only by script teleport from the floor-40 chamber.
// Read from GENERATED _tod_arena_data.gsc: every arrival spot and every spawn
// point stands on ONE arena component (zombies rising at a spawn can reach a
// player at an arrival), and the chamber pad shares floor 40's component (the
// horde can reach a party waiting in the chamber).
function arenaAnchors() {
  const f = path.join(__dirname, '..', 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_arena_data.gsc');
  if (!fs.existsSync(f)) return null;
  const t = fs.readFileSync(f, 'utf8');
  const vecs = (name) => {
    const body = t.split(`function ${name}()`)[1];
    if (!body) throw new Error(`lint_tod_navmesh: _tod_arena_data.gsc has no ${name}() — regenerate (node tools/gen_tower_map.js)`);
    return [...body.split('\n}')[0].matchAll(/\(\s*(-?[\d.]+),\s*(-?[\d.]+),\s*(-?[\d.]+)\s*\)/g)].map(m => m.slice(1, 4).map(Number));
  };
  const lap = Number((t.match(/function chamber_lap\(\)\s*\{\s*return\s+(\d+);/) || [])[1]);
  // docs/185 v2 THE CRUCIBLE: one point on every surface (pit, ring, stairs, spokes,
  // landings, dais) — absent from a v1 data file, so optional here
  const probes = t.includes('function arena_nav_probes()') ? vecs('arena_nav_probes') : [];
  return { arrivals: vecs('arena_arrivals'), spawns: vecs('arena_spawns'), probes, chamber: vecs('chamber_org')[0], lap };
}
const arenaA = arenaAnchors();
const arena = { checked: !!arenaA, bad: [] };
if (arenaA) {
  // THE CRUCIBLE (docs/185 v2): every arrival, every spawn point AND every surface
  // probe on ONE component — no level of the arena the horde cannot walk to (a
  // perch it cannot reach is the camp the user ruled out)
  const pts = [...arenaA.arrivals.map(p => ['arrival', p]), ...arenaA.spawns.map(p => ['spawn', p]), ...arenaA.probes.map(p => ['surface', p])];
  let ac = null;
  for (const [kind, p] of pts) {
    const f = faceUnder(p);
    if (f < 0) { arena.bad.push(`${kind} (${p.join(',')}) has NO navmesh — the arena's seeds did not take`); continue; }
    if (ac === null) ac = comp[f];
    else if (comp[f] !== ac) arena.bad.push(`${kind} (${p.join(',')}) is in component ${comp[f]}, not the arena's ${ac}`);
  }
  arena.comp = ac;
  const cf = faceUnder(arenaA.chamber), rf = faceUnder([-336, -336, (arenaA.lap - 1) * LAP_RISE + 192]);
  if (cf < 0) arena.bad.push(`the floor-${arenaA.lap} chamber pad (${arenaA.chamber.join(',')}) has NO navmesh`);
  else if (rf >= 0 && comp[cf] !== comp[rf]) arena.bad.push(`the floor-${arenaA.lap} chamber (comp ${comp[cf]}) is cut off from floor ${arenaA.lap} (comp ${comp[rf]})`);
}

// ---- THE DEALER'S HOUSE (docs/207) -------------------------------------------
// Read from GENERATED _tod_house_data.gsc: the house's arrivals, gates and surface probes on
// ONE component (the Dealer walks up to anyone anywhere), and the parlour's arrivals on mesh.
function houseAnchors() {
  const f = path.join(__dirname, '..', 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_house_data.gsc');
  if (!fs.existsSync(f)) return null;
  const t = fs.readFileSync(f, 'utf8');
  const vecs = (name) => {
    const body = t.split(`function ${name}()`)[1];
    if (!body) throw new Error(`lint_tod_navmesh: _tod_house_data.gsc has no ${name}() — regenerate (node tools/gen_tower_map.js)`);
    return [...body.split('\n}')[0].matchAll(/\(\s*(-?[\d.]+),\s*(-?[\d.]+),\s*(-?[\d.]+)\s*\)/g)].map(m => m.slice(1, 4).map(Number));
  };
  return { arrivals: vecs('house_arrivals'), gates: vecs('house_gates'), probes: vecs('house_nav_probes'), parlour: vecs('parlour_arrivals') };
}
const houseA = houseAnchors();
const house = { checked: !!houseA, bad: [] };
if (houseA) {
  const pts = [...houseA.arrivals.map(p => ['arrival', p]), ...houseA.gates.map(p => ['gate', p]), ...houseA.probes.map(p => ['surface', p])];
  let hc = null;
  for (const [kind, p] of pts) {
    const f = faceUnder(p);
    if (f < 0) { house.bad.push(`${kind} (${p.join(',')}) has NO navmesh — the house's seeds did not take`); continue; }
    if (hc === null) hc = comp[f];
    else if (comp[f] !== hc) house.bad.push(`${kind} (${p.join(',')}) is in component ${comp[f]}, not the house's ${hc}`);
  }
  house.comp = hc;
  for (const p of houseA.parlour) if (faceUnder(p) < 0) house.bad.push(`parlour arrival (${p.join(',')}) has NO navmesh`);
}

// ---- report -----------------------------------------------------------------
console.log(`navmesh ${path.basename(HKT)}: ${F} faces, ${E} edges, ${V} verts, ${nc} components (${fs.statSync(HKT).size} bytes)`);
const byRegion = {};
for (let f = 0; f < F; f++) { const r = region(C[f]); byRegion[comp[f]] = byRegion[comp[f]] || {}; byRegion[comp[f]][r] = (byRegion[comp[f]][r] || 0) + 1; }
const order = [...Array(nc).keys()].sort((a, b) => compSize[b] - compSize[a]);
for (const c of order) {
  const zs = []; for (let f = 0; f < F; f++) if (comp[f] === c) zs.push(C[f][2]);
  console.log(`  comp ${String(c).padStart(3)}  faces ${String(compSize[c]).padStart(5)}  ${JSON.stringify(byRegion[c]).padEnd(40)} z ${Math.min(...zs).toFixed(0)}..${Math.max(...zs).toFixed(0)}`);
}
function printTable(name, t) {
  if(t.descent&&t.bad.length===0){console.log(`${name}: ${t.descent.sections} connected walk sections, ${t.descent.links.length} directed stock drop traversals; every takeoff/landing has compiled navmesh`);return;}
  if (!VERBOSE && t.bad.length === 0) { console.log(`${name}: all ${t.rows.length - 1} floors in component ${t.baseComp} — connected`); return; }
  console.log(`${name}: base component ${t.baseComp}`);
  for (const r of t.rows) if (VERBOSE || r.foreign || r.faces === 0) console.log(`   floor ${String(r.fl).padStart(3)}  faces ${String(r.faces).padStart(3)}  comps ${JSON.stringify(r.comps)}${r.foreign ? '   <-- SEAM / ISLAND' : ''}`);
}
printTable('TOWER', tower);
if (crown.checked)
  console.log(crown.bad.length === 0
    ? `CROWN ISLAND (jump pad): hall + pad in component ${comp[crown.hall]} (${compSize[comp[crown.hall]]} faces), landing in the tower's ${tower.topComp ?? tower.baseComp} — connected`
    : `CROWN ISLAND (jump pad): ${crown.bad.length} problem(s) — see the gate below`);
// --islands (v17.70): where ARE the foreign components? One line per component
// that is not its tower's base: size + the centroid of its first face, so a
// single-face island can be matched to a brush without a bisect.
if (flag('--islands')) {
  for (const [name, t] of [['TOWER', tower]]) {
    const seen = new Set();
    for (const r of t.rows) for (const c of r.comps) {
      if (c === t.baseComp || seen.has(c)) continue; seen.add(c);
      let f0 = -1; for (let f = 0; f < F; f++) if (comp[f] === c) { f0 = f; break; }
      const c0 = C[f0];
      console.log(`  ${name} island comp ${c} (${compSize[c]} faces) first face at ${c0.map(v => v.toFixed(0)).join(' ')}`);
    }
  }
}

// Original BO6 counter footprint: every purchaser surface must share its haven centre's native component.
const wunderfizz = require('./wunderfizz/native_navcheck').check(require('./wunderfizz_layout').nodes(), faceUnder, comp);
console.log(`WUNDERFIZZ: ${wunderfizz.checked} floors / ${wunderfizz.probes} purchaser probes; ${wunderfizz.bad.length} native path problem(s).`);

const jsonOut = opt('--json');
if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify({ hkt: HKT, F, E, V, components: nc, compSize, tower, wunderfizz, transit: {routes:transitRoutes.length,bad:transitBad} }, null, 1));

const failures = [];
for (const b of wunderfizz.bad) failures.push(`Wunderfizz: ${b}`);
for (const b of tower.bad) failures.push(`tower floor ${b.fl}: ${b.why}`);
for (const b of crown.bad) failures.push(`crown island: ${b}`);
for (const b of transitBad) failures.push(`transit: ${b}`);
for (const b of arena.bad) failures.push(`battle arena: ${b}`);
for (const b of house.bad) failures.push(`dealer house: ${b}`);
if (arena.checked) console.log(`BATTLE ARENA: ${arenaA.arrivals.length} arrivals + ${arenaA.spawns.length} spawns + ${arenaA.probes.length} surface probes ${arena.bad.length ? 'FAILED' : 'in component ' + arena.comp}; floor-${arenaA.lap} chamber checked.`);
if (house.checked) console.log(`DEALER'S HOUSE: ${houseA.arrivals.length} arrivals + ${houseA.gates.length} gates + ${houseA.probes.length} surface probes ${house.bad.length ? 'FAILED' : 'in component ' + house.comp}; ${houseA.parlour.length} parlour arrivals on mesh.`);
console.log(`TRANSIT: ${transitRoutes.length} pads and arrival fan-outs checked; ${transitBad.length} problem(s).`);
if (failures.length) {
  console.log(`\nNAVMESH ${NO_GATE ? 'WARNINGS' : 'GATE FAILED'} (${failures.length}):`);
  for (const f of failures) console.log('  ' + f);
  console.log('A seam means zombies cannot path across it and a player standing on it cannot be reached; see the header of this tool.');
  if (!NO_GATE) process.exit(1);
} else {
  console.log(tower.descent ? '\nNAVMESH GATE OK: main descent sections and endpoints verified. Stock traversal playback remains a native playtest check.' : '\nNAVMESH GATE OK: the tower is one connected walk.');
}
