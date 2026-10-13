'use strict';
const HAVEN_FLOORS = Object.freeze([10, 20, 30, 40]);
const finite3 = p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite);
const rotate = (p, org, yaw) => {
  const a = yaw * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
  return [org[0] + p[0] * c - p[1] * s, org[1] + p[0] * s + p[1] * c, org[2] + p[2]];
};
const standingProbes = n => [-16, 0, 16].map(d =>
  [n.trig[0] - d * n.front[1], n.trig[1] + d * n.front[0], n.org[2] + 2]);
function dependencies(deps) {
  return {haven:deps.haven || require('../haven_layout'), asset:deps.asset || require('../wunderfizz_layout').ASSET};
}

// Use the existing hall's actual floor rectangles and spherical field, including
// the imported animation's full bounds. No ordinary landing/alcove is a vendor.
function placementProblems(nodes, deps = {}) {
  const {haven, asset} = dependencies(deps), bad = [];
  const floors = nodes.map(n => n.floor);
  if (nodes.length !== HAVEN_FLOORS.length || new Set(floors).size !== HAVEN_FLOORS.length ||
      HAVEN_FLOORS.some(f => !floors.includes(f)) || floors.some(f => !HAVEN_FLOORS.includes(f)))
    bad.push('counter coverage must contain exactly haven floors 10,20,30,40');
  for (const n of nodes) {
    const prefix = 'floor ' + n.floor;
    if (!finite3(n.org) || !finite3(n.trig) || !finite3(n.front) || !Number.isFinite(n.yaw)) {
      bad.push(prefix + ' has invalid placement coordinates'); continue;
    }
    if (n.id !== n.floor || n.kind !== 'haven' || n.alcove) bad.push(prefix + ' must be a haven descriptor without an alcove');
    const z = (n.floor - 1) * haven.LAP_RISE + haven.FLIGHT_RISE;
    if (Math.abs(n.org[2] - z) > .002) bad.push(prefix + ' machine is detached from its own haven floor');
    const direction = (n.yaw + asset.frontYaw) * Math.PI / 180;
    const front = [Math.cos(direction), Math.sin(direction), 0];
    if (front.some((v, i) => Math.abs(v - n.front[i]) > .002)) bad.push(prefix + ' front disagrees with the original native facing');
    const inward = Math.atan2(haven.C[1] - n.org[1], haven.C[0] - n.org[0]) * 180 / Math.PI;
    if (Math.abs(((n.yaw + asset.frontYaw - inward + 540) % 360) - 180) > 1)
      bad.push(prefix + ' machine must face into its haven dome');
    const trigger = rotate([asset.triggerOffset, 0, asset.triggerLift], n.org, n.yaw);
    if (trigger.some((v, i) => Math.abs(v - n.trig[i]) > .002) || n.r !== asset.triggerRadius)
      bad.push(prefix + ' purchaser anchor differs from the original native offset/radius');
    const footprint = [asset.mins[0], asset.maxs[0]].flatMap(x =>
      [asset.mins[1], asset.maxs[1]].map(y => rotate([x, y, 0], n.org, n.yaw)));
    if (footprint.some(p => !haven.onFloor(p))) bad.push(prefix + ' animated machine footprint leaves its haven hall floor');
    if (footprint.some(p => haven.domeZ(Math.hypot(p[0] - haven.C[0], p[1] - haven.C[1])) < asset.maxs[2] + 8))
      bad.push(prefix + ' full animated machine bounds reach outside its haven dome');
    for (const [i, p] of standingProbes(n).entries()) {
      if (!haven.onFloor(p, 16)) bad.push(prefix + ' purchaser probe ' + i + ' leaves its haven hall floor');
      if (!haven.insideBody([p[0], p[1], p[2] - z], haven.IN_R3 - 16))
        bad.push(prefix + ' purchaser probe ' + i + ' lies outside its haven dome');
    }
  }
  return bad;
}

// Probe compiled WALK surfaces at standing feet and require connection to the
// same haven's centre. The parent checker still verifies all directed drops,
// the crown, PaP, arena, Dealer and transit routes independently.
function check(nodes, faceUnder, components, deps = {}) {
  const {haven, asset} = dependencies(deps), rows = [], bad = placementProblems(nodes, {haven, asset});
  for (const n of nodes) {
    if (!finite3(n.org) || !finite3(n.trig) || !finite3(n.front)) continue;
    const route = [...haven.C, (n.floor - 1) * haven.LAP_RISE + haven.FLIGHT_RISE + 2];
    const rf = faceUnder(route), probes = standingProbes(n), probeFaces = probes.map(faceUnder);
    if (rf < 0) bad.push('floor ' + n.floor + ' haven centre has no native mesh');
    probeFaces.forEach((f, i) => {
      if (f < 0) bad.push('floor ' + n.floor + ' purchaser probe ' + i + ' has no native mesh');
      else if (components[f] === undefined || (rf >= 0 && components[f] !== components[rf]))
        bad.push('floor ' + n.floor + ' purchaser probe ' + i + ' is disconnected from its haven centre');
    });
    rows.push({floor:n.floor, route, routeFace:rf, probes, probeFaces, component:rf >= 0 ? components[rf] : null});
  }
  return {rows, bad, checked:rows.length, probes:rows.reduce((sum, row) => sum + row.probes.length, 0)};
}

if (require.main === module) {
  const assert = require('assert/strict'), path = require('path');
  const opt = name => {const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : null;};
  const root = opt('--root') ? path.resolve(opt('--root')) : path.resolve(__dirname, '../..');
  const tools = opt('--layout-stage') ? path.resolve(opt('--layout-stage')) : path.join(root, 'tools');
  const layout = require(path.join(tools, 'wunderfizz_layout'));
  const deps = {haven:require(path.join(root, 'tools/haven_layout')), asset:layout.ASSET};
  const nodes = layout.nodes(), clone = () => JSON.parse(JSON.stringify(nodes));
  const run = (a, under = () => 0, comp = [8]) => check(a, under, comp, deps);
  const good = run(nodes); assert.equal(good.bad.length, 0, good.bad.join('; '));
  assert.equal(good.rows.length, 4); assert.equal(good.probes, 12);
  assert.equal(good.rows[0].probes[1][2], nodes[0].org[2] + 2, 'feet use the floor, not elevated hint/trigger');
  const purchaser = p => Math.abs(p[0] - deps.haven.C[0]) > 1;
  assert(run(nodes, p => purchaser(p) ? -1 : 0).bad.some(x => x.includes('no native mesh')));
  assert(run(nodes, p => purchaser(p) ? 1 : 0, [8,9]).bad.some(x => x.includes('disconnected')));
  assert(run(nodes.slice(1)).bad.some(x => x.includes('exactly haven')));
  let a = clone(); a.push({...a[0], id:50, floor:50}); assert(run(a).bad.some(x => x.includes('exactly haven')));
  a = clone(); a[0].floor = 11; assert(run(a).bad.some(x => x.includes('exactly haven')));
  a = clone(); a[0].org[2] += 384; assert(run(a).bad.some(x => x.includes('detached')));
  a = clone(); a[0].org[0] += 700; a[0].trig[0] += 700; assert(run(a).bad.some(x => x.includes('outside its haven dome')));
  a = clone(); a[0].yaw += 180; assert(run(a).bad.some(x => x.includes('face into')));
  const enlarged = {...deps.asset, maxs:[...deps.asset.maxs]}; enlarged.maxs[2] = 300;
  assert(placementProblems(nodes, {...deps, asset:enlarged}).some(x => x.includes('full animated machine bounds')));
  console.log('WUNDERFIZZ NATIVE NAV CHECK SELFTEST PASS: four havens / 12 probes; holes, detached components, missing/unexpected floors, outside-dome bodies and wrong facing rejected');
}
module.exports = {check, placementProblems, standingProbes, HAVEN_FLOORS};
