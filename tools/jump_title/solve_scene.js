// solve_scene.js - THE FIRST JUMP'S CRASH (docs/196 §4): re-solve where the crash happens.
//
//   node tools/jump_title/solve_scene.js
//
// Run it after anything moves the shot (the pad, the landing spots, the flight's timing, the sign's bearing):
// it reads the live scene (scene_live.js), searches the crash point (distance R and elevation el from the rider's
// eye at the impact, on the camera's bearing), the approach slope phi and the run S, and prints every candidate
// that keeps both ships inside the sealed sky volume and >= MARGIN from every brush / keep-out (session 9c's map
// reader), frames the crash within 6 deg of the centre on every take-off x landing, and keeps both bows in a
// 65-deg frame at the settle and the charge. Copy the chosen CRASH / DIVE / RUN / WRECK_A / WRECK_B into
// _tod_jump_title.csc, then `node tools/jump_title/test_jump_title.js`.
'use strict';
const G = require('./scene_geometry');
const live = require('./scene_live');
const lanes = require('../sky_ships/gen_lanes.js');

const L = live.load();
const map = lanes.readMap();
const OBST = map.boxes.concat(lanes.KEEP_OUT.map(k => ({ lo: k.lo, hi: k.hi })));
const V = map.volume, EDGE = 200, MARGIN = lanes.MARGIN;
const P = L.PAD, r = L.PAD_R;
const SRCS = [P, G.add(P, [r, 0, 0]), G.add(P, [-r, 0, 0]), G.add(P, [0, r, 0]), G.add(P, [0, -r, 0])];
const LAND_C = L.SPOTS.reduce((a, s) => G.add(a, G.mul(s, 1 / L.SPOTS.length)), [0, 0, 0]);
const launchYaw = (src, dst) => { const v = G.sub(dst, src); return G.deg(Math.atan2(v[1], v[0])); };
const BOW = L.GUN.hi[0];
// the camera: the script's own path (scene_live L.cam) for the nominal rider, launched level looking down the flight
const camOf = (ly) => L.cam({ pitch: 0, yaw: ly }, ly);

function scene(p) {
  const eye = G.eyeAt(L.BEATS.IMPACT, L.J, P, LAND_C), view = camOf(launchYaw(P, LAND_C))(L.BEATS.IMPACT);
  const C = G.along(eye, p.el, view.yaw, p.R).map(Math.round);
  const d = [0, Math.cos(G.rad(p.phi)), -Math.sin(G.rad(p.phi))];
  return { C, d, A0: G.add(C, G.mul(d, -(BOW + p.S))), A1: G.add(C, G.mul(d, -BOW)),
           B0: G.add(C, G.mul(d, BOW + p.S)), B1: G.add(C, G.mul(d, BOW)) };
}

function score(p) {
  const s = scene(p), bad = [];
  let minGap = Infinity;
  for (const [a, b, pitch, yaw] of [[s.A0, s.A1, p.phi, 90], [s.B0, s.B1, -p.phi, 270]]) {
    const n = Math.ceil(G.len(G.sub(b, a)) / 150);
    for (let i = 0; i <= n; i++) {
      const cs = G.corners(G.add(a, G.mul(G.sub(b, a), i / n)), pitch, yaw, L.GUN.lo, L.GUN.hi);
      if (cs.some(c => c.some((v, k) => v < V.lo[k] + EDGE || v > V.hi[k] - EDGE))) bad.push('outside the volume');
      const bb = G.aabb(cs);
      for (const ob of OBST) minGap = Math.min(minGap, G.boxGap(bb.lo, bb.hi, ob.lo, ob.hi));
    }
  }
  if (minGap < MARGIN) bad.push('clearance ' + Math.round(minGap));
  const fr = G.frustum(65, true);
  let centre = 0, bows = 0;
  for (const src of SRCS) for (const dst of L.SPOTS) {
    const cv = camOf(launchYaw(src, dst));
    let e = G.eyeAt(L.BEATS.IMPACT, L.J, src, dst), v = cv(L.BEATS.IMPACT);
    const pc = G.project(s.C, e, v, fr);
    centre = Math.max(centre, pc ? Math.max(Math.abs(G.deg(Math.atan(pc[0] * fr.tx))), Math.abs(G.deg(Math.atan(pc[1] * fr.ty)))) : 180);
    for (const t of [L.J.SETTLE, L.BEATS.SHIPS]) {
      e = G.eyeAt(t, L.J, src, dst); v = cv(t);
      for (const [o, pitch, yaw] of [[s.A0, p.phi, 90], [s.B0, -p.phi, 270]]) {
        const q = G.project(G.add(o, G.mul(G.modelAxes(pitch, yaw).f, BOW)), e, v, fr);
        bows = Math.max(bows, q ? Math.max(Math.abs(q[0]), Math.abs(q[1])) : 99);
      }
    }
  }
  if (centre > 6) bad.push(`crash ${centre.toFixed(1)} deg off centre`);
  if (bows > 0.97) bad.push(`bow at |screen| ${bows.toFixed(2)}`);
  return { p, s, bad, gap: Math.round(minGap), centre: +centre.toFixed(2), bows: +bows.toFixed(2) };
}

const all = [];
for (const R of [5500, 6000, 6500]) for (const el of [10.5, 11.5, 12.5]) for (const phi of [8, 12, 16]) for (const S of [2400, 2900, 3400])
  all.push(score({ R, el, phi, S }));
const good = all.filter(x => !x.bad.length).sort((a, b) => a.centre - b.centre || b.gap - a.gap);
console.log(`crash placements: ${all.length} tried, ${good.length} pass`);
for (const g of good.slice(0, 10)) {
  const round = (v) => v.map(Math.round).join(', ');
  console.log(`  R ${g.p.R} el ${g.p.el} phi ${g.p.phi} run ${g.p.S}: CRASH ( ${round(g.s.C)} ) WRECK_A ( ${round(g.s.A1)} ) WRECK_B ( ${round(g.s.B1)} )`
              + `  gap ${g.gap} centre ${g.centre} deg bows ${g.bows}`);
}
if (!good.length) for (const x of all.slice(0, 6)) console.log('  ' + JSON.stringify(x.p) + ' ' + x.bad.slice(0, 3).join('; '));
