// storyboard_data.js - THE FIRST JUMP'S CRASH: the camera and the ships at chosen moments, from the LIVE scene
// (scene_live.js), for render_storyboard.py. Prints JSON. The nominal flight: the pad's centre to the landing
// spots' centre (test_jump_title.js proves the other take-offs and landings).
'use strict';
const G = require('./scene_geometry');
const live = require('./scene_live');

const L = live.load();
const LAND = L.SPOTS.reduce((a, s) => G.add(a, G.mul(s, 1 / L.SPOTS.length)), [0, 0, 0]);
const v = G.sub(LAND, L.PAD);
const launchYaw = G.deg(Math.atan2(v[1], v[0]));
const cam = L.cam({ pitch: 0, yaw: launchYaw }, launchYaw);   // the script's own camera path, the nominal rider
const d = [0, Math.cos(G.rad(L.S.DIVE)), -Math.sin(G.rad(L.S.DIVE))];
const home = { A: G.add(L.S.CRASH, G.mul(d, -(L.S.BOW + L.S.RUN))), B: G.add(L.S.CRASH, G.mul(d, L.S.BOW + L.S.RUN)) };
const contact = { A: G.add(L.S.CRASH, G.mul(d, -L.S.BOW)), B: G.add(L.S.CRASH, G.mul(d, L.S.BOW)) };
const warpAt = { A: L.S.WARP_A, B: L.S.WARP_B };
const angles = { A: [L.S.DIVE, 90], B: [-L.S.DIVE, 270] };

function shipAt(k, t) {
  if (t < warpAt[k] || t >= L.BEATS.IMPACT + L.S.UNDER_WHITE) return null;
  let o = home[k];
  if (t >= L.BEATS.SHIPS) {
    const f = G.trapezoid(t - L.BEATS.SHIPS, L.S.RUN_SECS, L.S.RUN_SECS * L.S.RUN_ACCEL, 0);
    o = G.add(home[k], G.mul(G.sub(contact[k], home[k]), f));
  }
  const ax = G.modelAxes(angles[k][0], angles[k][1]);
  return { origin: o, bow: G.add(o, G.mul(ax.f, L.GUN.hi[0])), tail: G.add(o, G.mul(ax.f, L.GUN.lo[0])),
           up: ax.u, warp: t - warpAt[k], burn: t >= L.BEATS.SHIPS ? t - L.BEATS.SHIPS : null, variant: k };
}

const B = L.BEATS, REVEAL = B.IGNITE + L.S.REVEAL, HOLD = REVEAL + L.S.FLICKER_SECS;   // the lit card holds: the blaze
const frames = [
  { t: 1.2, label: 'the turn: the DULL sign swings in' },
  { t: L.S.WARP_A + 0.12, label: 'the magenta gunship WARPS IN' },
  { t: L.S.WARP_B + 0.12, label: 'the green gunship warps in, bow to bow' },
  { t: (L.J.SETTLE + B.SHIPS) / 2, label: 'THE STANDOFF over the dull sign' },
  { t: B.SHIPS + 0.75, label: 'THE CHARGE: engines flaring, they ram' },
  { t: B.IMPACT + 0.15, label: 'THE CRASH: the white flash' },
  { t: B.IMPACT + 1.2, label: 'THE FIREBALL fills the frame' },
  { t: REVEAL + 0.1, label: 'THE REVEAL: the sign flickers on' },
  { t: HOLD + 1.2, label: 'THE TITLE, lit and blazing; wreckage falls to the city' },
  { t: B.END - 0.2, label: 'the last look before the swing back' },
];
const out = {
  beats: L.BEATS, flash: L.FLASH, scene: L.S, sign: { yaw: L.S.SIGN_YAW, el: L.S.SIGN_EL },
  frames: frames.map(f => ({ ...f, eye: G.eyeAt(f.t, L.J, L.PAD, LAND), view: cam(f.t),
                             ships: ['A', 'B'].map(k => shipAt(k, f.t)).filter(Boolean) })),
};
process.stdout.write(JSON.stringify(out));
