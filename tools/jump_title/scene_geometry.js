// scene_geometry.js - THE FIRST JUMP'S CRASH (docs/196 §4): where the camera is, what it frames,
// and where the two gunships can fly. Pure math, shared by the solver CLI and test_jumppad.
//
// The flight (a player's FIRST flight, _tod_jumppad.gsc): a straight line from the take-off to the
// landing spot plus a parabola APEX high at the middle, walked on the hang clock hang_u(). The
// camera is the rider's eye (origin + 60); WHERE it looks is the script's own camera path
// (cine_cam_angles), run by scene_live.js (L.cam) - this file keeps no copy of it (the first
// pass's copy here modelled RotateTo moves and a rider who launched looking level down the flight).
// BO3 angles: pitch + = DOWN; yaw 0 = +X, 90 = +Y.
'use strict';

const rad = (d) => d * Math.PI / 180;
const deg = (r) => r * 180 / Math.PI;
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const len = (a) => Math.sqrt(dot(a, a));
const norm = (a) => mul(a, 1 / len(a));

// BO3 forward / right / up for (pitch, yaw), pitch + = down.
function basis(pitch, yaw) {
  const p = rad(pitch), y = rad(yaw);
  const F = [Math.cos(p) * Math.cos(y), Math.cos(p) * Math.sin(y), -Math.sin(p)];
  const R = [Math.sin(y), -Math.cos(y), 0];
  const U = cross(R, F);
  return { F, R, U };
}

// A model's world axes for (pitch, yaw): bow +X, port +Y, up +Z (the fleet's convention).
function modelAxes(pitch, yaw) {
  const p = rad(pitch), y = rad(yaw);
  const f = [Math.cos(p) * Math.cos(y), Math.cos(p) * Math.sin(y), -Math.sin(p)];
  const l = [-Math.sin(y), Math.cos(y), 0];
  const u = cross(f, l);
  return { f, l, u };
}

function corners(origin, pitch, yaw, lo, hi) {
  const { f, l, u } = modelAxes(pitch, yaw);
  const out = [];
  for (const x of [lo[0], hi[0]]) for (const y of [lo[1], hi[1]]) for (const z of [lo[2], hi[2]])
    out.push(add(origin, add(mul(f, x), add(mul(l, y), mul(u, z)))));
  return out;
}

// RotateTo's trapezoid: the fraction done after t of a T-second move with accel ta and decel td.
function trapezoid(t, T, ta, td) {
  if (t <= 0) return 0;
  if (t >= T) return 1;
  const v = 1 / (T - ta / 2 - td / 2);
  if (t < ta) return 0.5 * v * t * t / ta;
  if (t <= T - td) return 0.5 * v * ta + v * (t - ta);
  const r = T - t;
  return 1 - 0.5 * v * r * r / td;
}

// The hang clock (_tod_jumppad.gsc hang_u, sin/cos in degrees there = radians here).
function hangU(t, W) {
  const a = 2 * Math.PI * t;
  let u = t + W.A * Math.sin(a) / (2 * Math.PI) - W.B * (Math.cos(a) - 1) / (2 * Math.PI)
        + W.C * Math.sin(2 * a) / (4 * Math.PI) - W.D * (Math.cos(2 * a) - 1) / (4 * Math.PI) + W.L * (t - t * t);
  return Math.min(1, Math.max(0, u));
}

// The share of the arc's hang clock walked t seconds into a first flight (_tod_jumppad.gsc cine_arc_frac, THE DWELL:
// the arc's own clock is CINE_SECS - DWELL long, DWELL seconds slipped in round the apex; tools/test_jumppad.js proves
// this replica against the shipping function).
function cineArcFrac(t, J) {
  let x = t - (J.DWELL_AT - J.DWELL_SPAN * 0.5);
  if (x > J.DWELL_SPAN) x = J.DWELL_SPAN;
  if (x > 0) t -= J.DWELL * (x / J.DWELL_SPAN - Math.sin(2 * Math.PI * x / J.DWELL_SPAN) / (2 * Math.PI));
  return t / (J.CINE_SECS - J.DWELL);
}

// The rider's eye at t seconds into a first flight.
function eyeAt(t, J, src, dst) {
  const u = hangU(Math.min(1, cineArcFrac(t, J)), J.W);
  const d = sub(dst, src);
  const p = add(src, mul(d, u));
  return [p[0], p[1], p[2] + 4 * J.APEX * u * (1 - u) + 60];
}

// Hor+ field of view: cg_fov is the 4:3 horizontal angle; 16:9 widens it, the vertical stays.
function frustum(cgFov, letterbox) {
  const t = Math.tan(rad(cgFov) / 2);
  const tx = t * (16 / 9) / (4 / 3), ty = t * 0.75;
  return { tx, ty: letterbox ? ty * (720 - 2 * 86) / 720 : ty };
}

// -> the point's screen position in units of the frame's half size ([-1,1] = inside), or null (behind).
function project(q, eye, view, fr) {
  const { F, R, U } = basis(view.pitch, view.yaw);
  const d = sub(q, eye), z = dot(d, F);
  if (z <= 1) return null;
  return [dot(d, R) / z / fr.tx, dot(d, U) / z / fr.ty];
}
const inFrame = (s) => s !== null && Math.abs(s[0]) <= 1 && Math.abs(s[1]) <= 1;

// A world point `dist` along (elevation, yaw) from `eye` (elevation + = up).
function along(eye, el, yaw, dist) {
  const { F } = basis(-el, yaw);
  return add(eye, mul(F, dist));
}

// The gap between two AABBs (0 when they touch or overlap).
function boxGap(alo, ahi, blo, bhi) {
  let s = 0;
  for (let i = 0; i < 3; i++) {
    const g = Math.max(0, blo[i] - ahi[i], alo[i] - bhi[i]);
    s += g * g;
  }
  return Math.sqrt(s);
}
function aabb(pts) {
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (const p of pts) for (let i = 0; i < 3; i++) { lo[i] = Math.min(lo[i], p[i]); hi[i] = Math.max(hi[i], p[i]); }
  return { lo, hi };
}

module.exports = { rad, deg, add, sub, mul, dot, cross, len, norm, basis, modelAxes, corners, trapezoid, hangU, cineArcFrac,
                   eyeAt, frustum, project, inFrame, along, boxGap, aabb };
