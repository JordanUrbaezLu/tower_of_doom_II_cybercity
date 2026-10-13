// test_jump_title.js - THE FIRST JUMP'S CRASH (docs/196 §4): the build gate.
//
//   node tools/jump_title/test_jump_title.js                  prove the scene against the live sources
//   node tools/jump_title/test_jump_title.js --ledger <csv>   after a link: every crash asset is in the fastfile
//
// Every number is READ from the shipping sources (scene_live.js), then:
//   A. LOCKSTEP    the pairs that must agree across files (run time = the beat gap, the bow = the gunship's
//                  bounds, the sign's bearing / elevation / layout distance, the wreck points = the contact)
//   B. THE BEATS   in order, never two in one server frame (util::clientNotify is a per-player STATE: a second
//                  one in the same frame overwrites the first), the ignition and the hull removal INSIDE the full
//                  white, the fireball SEEN >= 1 s before the reveal; THE SIGN (docs/196 s6): dull by the bake, the
//                  LIT CARD shown only at the reveal (>= 1 s after the impact), its flicker short, >= 2.5 s of the
//                  held lit title before the swing back, the GENERATED blaze's life and curves on this timeline (a
//                  stale .efx fails), the flight long enough, the client's watchdog never cutting a live scene
//   C. THE FRAME   on every take-off (the pad and its trigger edge) x landing spot x 25 launch views (the camera
//                  starts on the rider's own view since the second pass: the script's own path, RUN by scene_live),
//                  in a 65-deg letterboxed frame: each ship in frame at its warp, both bows at the settle and the
//                  charge, the crash within 6 deg of the centre at the impact, the sign near the centre through the hold
//   D. THE SKY     every corner of both ships on their whole path (hover bob included) inside the sealed sky volume
//                  by 200 u and >= 1,500 u from every brush and keep-out (session 9c's rule, 9c's own map reader);
//                  the sign host and the lit card's centre inside the volume for the whole flight, the card BEHIND
//                  every hull point that could cross it (it would hide a ship in front of it otherwise)
//   E. THE WIRING  the five beats sent once each (no retired tod_jump_reveal), the client listening to all five,
//                  every effect generated + precached + zoned, every alias row + wav present, the sound table in
//                  the zone config, the ships hidden until their warp, THE CLOCK (no script `wait <seconds>` and no
//                  MoveTo / RotateTo in the client scene: a client wait counts frames, 2.7x fast on the user's
//                  machine in the first play), no veil anywhere (retired), the reveal's surge, THE LIT CARD (its
//                  model / material / image in the GENERATED GDT, the model zoned, the receipt on the live geometry,
//                  shown by the reveal and by a scene cut after the ignite, never deleted by a scene)
//   F. HEARD       (the second play: "the ships should have some sound effect before the boom of flying spaceships")
//                  the warp and the engines play at full level out past the farthest ship, the ship loop is the
//                  gunship engine, every crash cue at full alias volume (the balcony music never ducks)
// Each family carries a NEGATIVE CONTROL: a copy of the live scene broken the way that check exists for must FAIL.
'use strict';
const fs = require('fs');
const path = require('path');
const G = require('./scene_geometry');
const live = require('./scene_live');

const ok = [], fails = [];
const check = (cond, good, bad) => { (cond ? ok : fails).push(cond ? good : bad); };

let L;
try { L = live.load(); } catch (e) { console.error('test_jump_title FAIL: ' + e.message); process.exit(1); }
const ROOT = L.ROOT;
// THE CAMERA (the second pass, 2026-09-30): the script's own path from the rider's view at the launch (L.cam RUNS
// _tod_jumppad.gsc's cine_cam_plan / cine_cam_angles). The frame is proven for the spread of views a player walking
// onto the pad has - the user's first run launched 27 deg down and 23 deg right of the flight - not only for a rider
// looking level down it. Captured here: the negative controls below clone L, and a clone carries no functions.
const CAM = L.cam;
const VIEWS = [];
for (const p of [-10, 0, 15, 27.35, 40]) for (const dy of [-35, -23, 0, 20, 35]) VIEWS.push([p, dy]);
const read = (rel) => live.read(rel);
const exists = (rel) => fs.existsSync(path.join(ROOT, rel));

// ---- A. LOCKSTEP ---------------------------------------------------------------------------------------------
function lockstep(L) {
  const e = [];
  const d = [0, Math.cos(G.rad(L.S.DIVE)), -Math.sin(G.rad(L.S.DIVE))];
  if (Math.abs(L.S.RUN_SECS - (L.BEATS.IMPACT - L.BEATS.SHIPS)) > 1e-6)
    e.push(`TOD_JT_RUN_SECS ${L.S.RUN_SECS} != IMPACT_AT - SHIPS_AT ${(L.BEATS.IMPACT - L.BEATS.SHIPS).toFixed(3)}: the hulls would meet before / after the white-out`);
  if (L.S.BOW !== L.GUN.hi[0]) e.push(`TOD_JT_BOW ${L.S.BOW} != the gunship's bow (manifest bounds x max ${L.GUN.hi[0]})`);
  if (L.S.SIGN_YAW !== L.J.SIGN_YAW) e.push(`TOD_JT_SIGN_YAW ${L.S.SIGN_YAW} != TOD_JUMPPAD_CINE_SIGN_YAW ${L.J.SIGN_YAW}`);
  if (L.S.SIGN_EL !== L.SIGN_BOX_EL) e.push(`TOD_JT_SIGN_EL ${L.S.SIGN_EL} != build_city.py GATE box_el ${L.SIGN_BOX_EL} (the authored cyber monument)`);
  if (L.S.SIGN_DIST !== L.FX_SIGN_DIST) e.push(`TOD_JT_SIGN_DIST ${L.S.SIGN_DIST} != gen_fx.py SIGN_DIST ${L.FX_SIGN_DIST}: the glows would miss the letters`);
  if (!L.CARD) e.push('no lit sign card receipt (python tools/jump_title/make_sign_card.py)');
  else {
    if (L.CARD.sign_dist !== L.S.SIGN_DIST) e.push(`the lit card is sized at ${L.CARD.sign_dist} u, the client rides the bearing at ${L.S.SIGN_DIST}: it would not cover the dull sign`);
    if (L.CARD.model !== L.S.SIGN_MODEL) e.push(`the card receipt names ${L.CARD.model}, the client spawns ${L.S.SIGN_MODEL}`);
    if (Math.abs(L.CARD.box_el - L.S.SIGN_EL) > 1e-9) e.push(`the card was laid out at box_el ${L.CARD.box_el}, the client's bearing is el ${L.S.SIGN_EL}`);
    const want = 2 * L.S.SIGN_DIST * Math.tan(G.rad(L.CARD.w_deg / 2));
    if (Math.abs(L.CARD.width - want) > 1) e.push(`the card is ${L.CARD.width.toFixed(0)} u wide, the sky's ${L.CARD.w_deg}-deg gate at ${L.S.SIGN_DIST} u is ${want.toFixed(0)}`);
  }
  if (Math.abs(L.S.REVEAL - L.FX.REVEAL) > 1e-6) e.push(`TOD_JT_REVEAL ${L.S.REVEAL} != gen_fx.py REVEAL ${L.FX.REVEAL}: the surge would not meet the sparks`);
  const wa = G.add(L.S.CRASH, G.mul(d, -L.S.BOW)), wb = G.add(L.S.CRASH, G.mul(d, L.S.BOW));
  if (G.len(G.sub(wa, L.S.WRECK_A)) > 2) e.push(`TOD_JT_WRECK_A ${L.S.WRECK_A} is not ship A at the contact (${wa.map(Math.round)})`);
  if (G.len(G.sub(wb, L.S.WRECK_B)) > 2) e.push(`TOD_JT_WRECK_B ${L.S.WRECK_B} is not ship B at the contact (${wb.map(Math.round)})`);
  return e;
}

// ---- B. THE BEATS --------------------------------------------------------------------------------------------
function beats(L) {
  const e = [], B = L.BEATS, F = L.FLASH, S = L.S, J = L.J;
  const order = [['START', B.START], ['SHIPS', B.SHIPS], ['IMPACT', B.IMPACT], ['IGNITE', B.IGNITE], ['END', B.END]];
  for (let i = 1; i < order.length; i++)
    if (!(order[i][1] - order[i - 1][1] >= 0.1))
      e.push(`beat ${order[i][0]} (${order[i][1]}) is not >= 0.1 s after ${order[i - 1][0]} (${order[i - 1][1]}): two clientNotify in one frame overwrite each other`);
  if (!(S.WARP_A > 0.2 && S.WARP_A < S.WARP_B && S.WARP_B <= B.SHIPS - 0.3))
    e.push(`the warps (${S.WARP_A} / ${S.WARP_B}) must come in order and >= 0.3 s before the charge (${B.SHIPS})`);
  if (B.SHIPS < J.SETTLE) e.push(`the charge (${B.SHIPS}) starts before the camera settles (${J.SETTLE.toFixed(2)})`);
  const whiteOn = F.IN / 1000, whiteOff = (F.IN + F.HOLD) / 1000;
  const ig = B.IGNITE - B.IMPACT;
  if (!(ig >= whiteOn && ig <= whiteOff - 0.1))
    e.push(`the ignition is ${ig.toFixed(2)} s after the impact, outside the FULL white (${whiteOn.toFixed(2)}..${(whiteOff - 0.1).toFixed(2)}): the sign would be SEEN switching on`);
  if (!(S.UNDER_WHITE >= whiteOn && S.UNDER_WHITE <= whiteOff - 0.1))
    e.push(`TOD_JT_UNDER_WHITE ${S.UNDER_WHITE} is outside the full white (${whiteOn.toFixed(2)}..${(whiteOff - 0.1).toFixed(2)}): the hulls would be seen vanishing`);
  // THE FIREBALL, THEN THE TITLE (the first play: "the kaboom ended early"; "make sure sign doesnt light up until
  // explosion happens"). The white burns out onto the fire; the smoke over the sign lifts only once the fire covers
  // it; the title emerges inside that lifting; then it holds, clear and blazing.
  const clear = B.IMPACT + (F.IN + F.HOLD + F.OUT) / 1000;           // the white has burnt out: the fire is seen
  const reveal = B.IGNITE + S.REVEAL;                                 // the lit card flickers on, its power surge
  const holds = reveal + S.FLICKER_SECS;                              // ... and holds lit: the blaze starts
  // THE FIFTH PASS: the sign lights as the white burns out onto the fireball (the user: "taking a little bit too long to
  // light up"): never under the FULL white (a flicker nobody sees), never before the explosion has covered it.
  // 2026-10-01 (the user: "the lights on the sign should start about 300ms earlier"): 0.9 s after the impact, so the floor
  // is 0.8. whiteOff is measured from the impact (the old line compared it to the absolute reveal and could never fail).
  if (reveal < B.IMPACT + whiteOff + 0.5) e.push(`the reveal (${reveal.toFixed(2)} s) comes < 0.5 s after the full white ends (${(B.IMPACT + whiteOff).toFixed(2)} s): the flicker would be lost in the white`);
  if (reveal > clear + 1.0) e.push(`the reveal (${reveal.toFixed(2)} s) comes > 1 s after the white burns out (${clear.toFixed(2)} s): the dull sign sits in the fire too long`);
  if (reveal < B.IMPACT + 0.8) e.push(`the sign lights ${(reveal - B.IMPACT).toFixed(2)} s after the impact (< 0.8): it would show lit before the explosion covers it`);
  if (!(S.FLICKER_SECS > 0.2 && S.FLICKER_SECS <= 0.8)) e.push(`the flicker lasts ${S.FLICKER_SECS} s (want 0.2..0.8: a neon sign taking power, not a strobe)`);
  if (!(L.FX.RING_AT >= 0.1 && L.FX.EYES_AT > L.FX.RING_AT && L.FX.EYES_AT <= 1.5))
    e.push(`the cyber crest's ring (+${L.FX.RING_AT}) and sensors (+${L.FX.EYES_AT}) must flare after the card holds, in order, within 1.5 s`);
  if (B.END - holds < 2.5) e.push(`only ${(B.END - holds).toFixed(2)} s of the held, lit title before the swing back (want >= 2.5)`);
  // the GENERATED blaze on THIS timeline (a stale .efx would blaze at the old times)
  const bl = L.FX.BLAZE_LIFE / 1000;
  const bOn = L.FX.BLAZE_CURVE[1][0] * bl, bHoldEnd = L.FX.BLAZE_CURVE[2][0] * bl;
  if (bOn > 0.5) e.push(`the title's glows take ${bOn.toFixed(2)} s to reach full over the held card (want a surge, <= 0.5 s)`);
  if (Math.abs(holds + bHoldEnd - B.END) > 0.05) e.push(`the blaze stops holding at ${(holds + bHoldEnd).toFixed(2)} s, not at the swing back ${B.END} s (python tools/jump_title/gen_fx.py)`);
  const ringOn = L.FX.RING_CURVE[2][0] * bl, eyeOn = L.FX.EYE_CURVE[2][0] * bl;
  if (Math.abs(ringOn - (L.FX.RING_AT + 0.1)) > 0.05 || Math.abs(eyeOn - (L.FX.EYES_AT + 0.1)) > 0.05)
    e.push(`the ring / eye flares in fx_jt_blaze (${ringOn.toFixed(2)} / ${eyeOn.toFixed(2)} s after the card holds) are not gen_fx's RING_AT / EYES_AT: regenerate`);
  if (J.SWING_BACK + J.BACK_SECS > J.CINE_SECS - 0.5) e.push(`the swing back ends at ${(J.SWING_BACK + J.BACK_SECS).toFixed(2)} s, too close to the touch-down (${J.CINE_SECS})`);
  if (!(S.WATCHDOG > J.CINE_SECS && S.WATCHDOG > B.END + 2)) e.push(`TOD_JT_WATCHDOG ${S.WATCHDOG} could cut a live scene (flight ${J.CINE_SECS} s)`);
  // the host must outlive the blaze's fade (else the glows would stop following the sign)
  if (holds + L.FX.BLAZE_LIFE / 1000 > B.END + S.HOST_LINGER)
    e.push(`the blaze fades out at ${(holds + L.FX.BLAZE_LIFE / 1000).toFixed(2)} s but its host is deleted at ${(B.END + S.HOST_LINGER).toFixed(2)} s (TOD_JT_HOST_LINGER)`);
  if (holds + L.FX.BLAZE_LIFE / 1000 < B.END + 0.5)
    e.push(`the blaze (${L.FX.BLAZE_LIFE} ms) dies before the swing back (${B.END} s)`);
  return e;
}

// ---- C. THE FRAME --------------------------------------------------------------------------------------------
const launchYaw = (src, dst) => { const v = G.sub(dst, src); return G.deg(Math.atan2(v[1], v[0])); };
function takeoffs(L) {
  const P = L.PAD, r = L.PAD_R;
  return [P, G.add(P, [r, 0, 0]), G.add(P, [-r, 0, 0]), G.add(P, [0, r, 0]), G.add(P, [0, -r, 0])];
}
function shipsOf(L) {
  const d = [0, Math.cos(G.rad(L.S.DIVE)), -Math.sin(G.rad(L.S.DIVE))];
  const k = L.S.BOW + L.S.RUN;
  return {
    d,
    A: { home: G.add(L.S.CRASH, G.mul(d, -k)), contact: G.add(L.S.CRASH, G.mul(d, -L.S.BOW)), pitch: L.S.DIVE, yaw: 90 },
    B: { home: G.add(L.S.CRASH, G.mul(d, k)), contact: G.add(L.S.CRASH, G.mul(d, L.S.BOW)), pitch: -L.S.DIVE, yaw: 270 },
  };
}
function frame(L) {
  const e = [], fr = G.frustum(65, true), sh = shipsOf(L);
  const m = (p) => (p ? Math.max(Math.abs(p[0]), Math.abs(p[1])) : 99);
  const sign = (eye) => G.along(eye, L.S.SIGN_EL, L.S.SIGN_YAW, 1e6);
  let worst = { warpA: 0, warpB: 0, bows: 0, crash: 0, sign: 0 };
  for (const src of takeoffs(L)) for (const dst of L.SPOTS) for (const [vp, vy] of VIEWS) {
    const ly = launchYaw(src, dst), cam = CAM({ pitch: vp, yaw: ly + vy }, ly);
    const at = (t) => ({ eye: G.eyeAt(t, L.J, src, dst), view: cam(t) });
    let v = at(L.S.WARP_A); worst.warpA = Math.max(worst.warpA, m(G.project(sh.A.home, v.eye, v.view, fr)));
    v = at(L.S.WARP_B); worst.warpB = Math.max(worst.warpB, m(G.project(sh.B.home, v.eye, v.view, fr)));
    for (const t of [L.J.SETTLE, L.BEATS.SHIPS]) {
      v = at(t);
      for (const s of [sh.A, sh.B]) {
        const bow = G.add(s.home, G.mul(G.modelAxes(s.pitch, s.yaw).f, L.S.BOW));
        worst.bows = Math.max(worst.bows, m(G.project(bow, v.eye, v.view, fr)));
      }
    }
    v = at(L.BEATS.IMPACT);
    const pc = G.project(L.S.CRASH, v.eye, v.view, fr);
    const off = pc ? Math.max(Math.abs(G.deg(Math.atan(pc[0] * fr.tx))), Math.abs(G.deg(Math.atan(pc[1] * fr.ty)))) : 180;
    worst.crash = Math.max(worst.crash, off);
    for (let t = L.J.SETTLE; t <= L.BEATS.END + 1e-9; t += 0.1) {
      v = at(t);
      worst.sign = Math.max(worst.sign, m(G.project(sign(v.eye), v.eye, v.view, fr)));
    }
  }
  if (worst.warpA > 0.97) e.push(`ship A is out of a 65-deg frame at its warp (${L.S.WARP_A} s, |screen| ${worst.warpA.toFixed(2)}): its arrival would be missed`);
  if (worst.warpB > 0.97) e.push(`ship B is out of a 65-deg frame at its warp (${L.S.WARP_B} s, |screen| ${worst.warpB.toFixed(2)})`);
  if (worst.bows > 0.97) e.push(`a bow leaves the 65-deg frame at the settle / charge (|screen| ${worst.bows.toFixed(2)})`);
  if (worst.crash > 6) e.push(`the crash is ${worst.crash.toFixed(1)} deg off the frame centre at the impact`);
  if (worst.sign > 0.5) e.push(`the sign drifts to |screen| ${worst.sign.toFixed(2)} during the hold (the title must stay central)`);
  return { e, worst };
}

// ---- D. THE SKY ----------------------------------------------------------------------------------------------
let MAP = null;
function sky(L) {
  const e = [];
  if (!MAP) {
    const lanes = require('../sky_ships/gen_lanes.js');
    const m = lanes.readMap();
    MAP = { boxes: m.boxes.concat(lanes.KEEP_OUT.map(k => ({ lo: k.lo, hi: k.hi, name: k.name }))), volume: m.volume, MARGIN: lanes.MARGIN };
  }
  const EDGE = 200, sh = shipsOf(L), V = MAP.volume;
  let minGap = Infinity, who = '';
  for (const [name, s] of [['A', sh.A], ['B', sh.B]]) {
    const n = Math.ceil(G.len(G.sub(s.contact, s.home)) / 150);
    for (let i = 0; i <= n; i++) {
      const o = G.add(s.home, G.mul(G.sub(s.contact, s.home), i / n));
      for (const bob of (i === 0 ? [-L.S.BOB, L.S.BOB] : [0])) {
        const cs = G.corners(G.add(o, [0, 0, bob]), s.pitch, s.yaw, L.GUN.lo, L.GUN.hi);
        for (const c of cs) for (let k = 0; k < 3; k++)
          if (c[k] < V.lo[k] + EDGE || c[k] > V.hi[k] - EDGE) { e.push(`ship ${name} leaves the sealed sky volume at ${o.map(Math.round)}`); return e; }
        const bb = G.aabb(cs);
        for (const ob of MAP.boxes) {
          const g = G.boxGap(bb.lo, bb.hi, ob.lo, ob.hi);
          if (g < minGap) { minGap = g; who = `ship ${name} vs ${ob.name || 'a brush ' + JSON.stringify([ob.lo.map(Math.round), ob.hi.map(Math.round)])}`; }
        }
      }
    }
  }
  if (minGap < MAP.MARGIN) e.push(`clearance ${Math.round(minGap)} < ${MAP.MARGIN} (${who})`);
  // the sign host and the lit card's centre ride camera + bearing x SIGN_DIST for the whole flight (the card for the
  // match: from every take-off, landing and the flight between them it must sit inside the volume)
  const dir = G.basis(-L.S.SIGN_EL, L.S.SIGN_YAW).F;
  for (const src of takeoffs(L)) for (const dst of L.SPOTS)
    for (let t = 0; t <= L.J.CINE_SECS + 1e-9; t += 0.25) {
      const h = G.add(G.eyeAt(t, L.J, src, dst), G.mul(dir, L.S.SIGN_DIST));
      for (let k = 0; k < 3; k++)
        if (h[k] < V.lo[k] || h[k] > V.hi[k]) { e.push(`the sign host / lit card leaves the sky volume at t=${t.toFixed(2)} (${h.map(Math.round)})`); return e; }
    }
  // THE CARD IS BEHIND THE SHIPS: a hull point that projects inside the card's extent must be nearer the camera than
  // the card, else the (opaque where the sign is) card would hide the ship. Every hull corner, every warp / standoff /
  // ram position, every take-off x landing, sampled over the flight.
  let nearestBehind = Infinity, behindAt = '';
  if (L.CARD) {
    const half = L.CARD.width / 2;
    for (const src of takeoffs(L)) for (const dst of L.SPOTS)
      for (let t = 0; t <= L.BEATS.IMPACT + 1e-9; t += 0.1) {
        const eye = G.eyeAt(t, L.J, src, dst);
        const centre = G.add(eye, G.mul(dir, L.S.SIGN_DIST));
        for (const [name, sh0] of [['A', sh.A], ['B', sh.B]]) {
          const f = t < L.BEATS.SHIPS ? 0 : Math.min(1, G.trapezoid ? G.trapezoid(t - L.BEATS.SHIPS, L.S.RUN_SECS, L.S.RUN_SECS * L.S.RUN_ACCEL, 0) : (t - L.BEATS.SHIPS) / L.S.RUN_SECS);
          const o = G.add(sh0.home, G.mul(G.sub(sh0.contact, sh0.home), f));
          for (const c of G.corners(o, sh0.pitch, sh0.yaw, L.GUN.lo, L.GUN.hi)) {
            const rel = G.sub(c, eye), depth = G.dot ? G.dot(rel, dir) : rel[0] * dir[0] + rel[1] * dir[1] + rel[2] * dir[2];
            const lateral = G.len(G.sub(rel, G.mul(dir, depth)));
            if (lateral <= half * 1.02 && depth >= L.S.SIGN_DIST - 100) { if (depth < nearestBehind) { nearestBehind = depth; behindAt = `ship ${name} at t=${t.toFixed(1)} (depth ${Math.round(depth)}, lateral ${Math.round(lateral)})`; } }
          }
        }
      }
    if (behindAt) e.push(`a hull point sits behind the lit card inside its extent: ${behindAt} (TOD_JT_SIGN_DIST ${L.S.SIGN_DIST}): the card would hide it`);
  }
  return { e, minGap: Math.round(minGap), who };
}

// ---- F. THE SHIPS ARE HEARD ------------------------------------------------------------------------------------
// The second play (2026-09-30): "the ships should have some sound effect before the boom of flying spaceships". The
// first pass's engines were a jet hiss at alias volume 74 fading from 3,000 u, with the ships ~7,000..9,000 u away
// under -9..-11 LUFS of balcony music that never ducks. Every ship sound plays at full level at the ships' real
// distance (from every take-off x landing, at both warps and the charge), and every crash cue at full alias volume.
function audible(L, csv) {
  const e = [], sh = shipsOf(L);
  const rows = csv.split(/\r?\n/).filter(Boolean).map(l => l.split(','));
  const head = rows[0] || [], col = (n) => head.indexOf(n), row = (a) => rows.find(r => r[0] === a);
  let far = 0;
  for (const src of takeoffs(L)) for (const dst of L.SPOTS)
    for (const [t, o] of [[L.S.WARP_A, sh.A.home], [L.S.WARP_B, sh.B.home], [L.BEATS.SHIPS, sh.A.home], [L.BEATS.SHIPS, sh.B.home]])
      far = Math.max(far, G.len(G.sub(o, G.eyeAt(t, L.J, src, dst))));
  for (const a of ['tod_jt_warp', 'tod_jt_jet']) {
    const r = row(a);
    if (!r) { e.push(`no alias row ${a}`); continue; }
    const dmin = Number(r[col('DistMin')]), dmax = Number(r[col('DistMaxDry')]);
    if (!(dmin >= far)) e.push(`${a}: DistMin ${dmin} < the farthest ship (${Math.round(far)} u): it fades under the music`);
    if (!(dmax > dmin)) e.push(`${a}: DistMaxDry ${dmax} must lie past DistMin ${dmin}`);
  }
  for (const a of ['tod_jt_warp', 'tod_jt_jet', 'tod_jt_charge', 'tod_jt_boom']) {
    const r = row(a);
    if (r && !(Number(r[col('VolMax')]) >= 100)) e.push(`${a}: VolMax ${r[col('VolMax')]} (the crash's cues play at full volume over the music)`);
  }
  const jet = row('tod_jt_jet');
  if (jet && !/tod_jt_engine\.wav$/i.test(jet[col('FileSpec')])) e.push(`tod_jt_jet plays ${jet[col('FileSpec')]}, not the gunship engine loop (tod_jt_engine.wav)`);
  return { e, far: Math.round(far) };
}

// ---- E. THE WIRING -------------------------------------------------------------------------------------------
function wiring(texts) {
  const e = [];
  const { jp, jt, zone, entry, csv, szc, fxDir, wav } = texts;
  const count = (t, re) => (t.match(re) || []).length;
  if (count(jp, /util::clientNotify\( "tod_jump_title_start" \)/g) !== 1) e.push('_tod_jumppad.gsc must send tod_jump_title_start exactly once');
  for (const b of ['ships', 'impact', 'ignite'])
    if (count(jp, new RegExp('cine_beat\\( op, "tod_jump_title_' + b + '"', 'g')) !== 1) e.push(`_tod_jumppad.gsc must send tod_jump_title_${b} exactly once (cine_beat)`);
  const titleEnd = (jp.match(/function cine_title_end\(\)[\s\S]*?\n\}/) || [''])[0];
  if (count(titleEnd, /util::clientNotify\( "tod_jump_title_end" \)/g) !== 1 || count(jp, /"tod_jump_title_end"/g) !== 1)
    e.push('tod_jump_title_end must be sent from cine_title_end only, once');
  const cineEnd = (jp.match(/function cine_end\([\s\S]*?\n\}/) || [''])[0];
  if (!/cine_title_end\(\)/.test(cineEnd)) e.push('cine_end must end the client scene (cine_title_end): a cut-short scene would leave the ships up');
  const reveal = (jp.match(/function cine_reveal\([\s\S]*?\n\}/) || [''])[0];
  if (/util::clientNotify\(/.test(reveal)) e.push('cine_reveal sends a clientNotify in the ignition\'s frame: it would overwrite tod_jump_title_ignite');
  if (/tod_jump_reveal/.test(jp)) e.push('_tod_jumppad.gsc still sends the retired tod_jump_reveal (session 9c listens on tod_jump_title_ignite now)');
  if (!/LuiNotifyEvent\( &"tod_jump_cine", 1, 2 \)/.test(jp)) e.push('the impact no longer fires the white-out (tod_jump_cine 1, 2)');
  for (const b of ['start', 'ships', 'impact', 'ignite', 'end'])
    if (!new RegExp('level thread listen\\( "tod_jump_title_' + b + '" \\)').test(jt)) e.push(`_tod_jump_title.csc does not listen for tod_jump_title_${b}`);
  if (!/SetModel\( model \);\s*\n\s*ship Hide\(\);/.test(jt)) e.push('ship_spawn must Hide() the ship right after SetModel (never seen before its warp)');
  if (!/ship Show\(\);/.test((jt.match(/function arrive\([\s\S]*?\n\}/) || [''])[0])) e.push('arrive() must Show() the ship with its warp flash');
  if (!/self\.origin = GetCamPosByLocalClientNum\( localClientNum \) \+ dir \* TOD_JT_SIGN_DIST;/.test(jt)) e.push('the sign host no longer follows the camera every frame (the glows would slide off the sign)');
  if (!/scriptparsetree,scripts\/zm\/zm_tod2_cybercity\/_tod_jump_title\.csc/.test(zone)) e.push('the zone does not load _tod_jump_title.csc');
  if (!/#using scripts\\zm\\zm_tod2_cybercity\\_tod_jump_title;/.test(entry)) e.push('zm_tod2_cybercity.csc does not #using _tod_jump_title (its REGISTER_SYSTEM would never run)');
  for (const m of ['tod_sky_gunship', 'tod_sky_gunship_b'])
    if (!new RegExp('^xmodel,' + m + '\\s*$', 'm').test(zone)) e.push(`the zone does not carry xmodel ${m} (the fleet's gunship)`);
  // THE LIT SIGN CARD (docs/196 s6): the model the reveal shows over the dull bake
  const model = texts.signModel;
  if (!new RegExp('^xmodel,' + model + '\\s*$', 'm').test(zone)) e.push(`the zone does not carry xmodel ${model} (the lit sign card)`);
  if (new RegExp('^material,mtl_' + model.replace(/^tod_/, 'tod_') + '\\s*$', 'm').test(zone) || /^material,mtl_tod_jt_sign_lit\s*$/m.test(zone))
    e.push('the lit card\'s material is zoned bare (a model material is never zoned bare: it links twice, no type)');
  const gdt = texts.cardGdt || '';
  for (const [kind, name] of [['xmodel', model], ['material', 'mtl_' + model.replace(/^tod_/, 'tod_')], ['image', 'i_' + model.replace(/^tod_/, 'tod_')]])
    if (!new RegExp('"' + name + '" \\( "' + kind + '\\.gdf" \\)').test(gdt)) e.push(`source_data/tod_jump_title.gdt has no ${kind} block ${name} (python tools/jump_title/make_sign_card.py)`);
  if (!/"materialType" "lit_emissive_transparent"/.test(gdt)) e.push('the lit card\'s material is not lit_emissive_transparent (the alpha-blended emissive the inducer\'s glass proved)');
  if (!texts.cardPng) e.push('model_export/tod_jump_title/_images/i_tod_jt_sign_lit.png is missing');
  if (!texts.cardBin) e.push('model_export/tod_jump_title/tod_jt_sign_lit.xmodel_bin is missing');
  if (!/model_export\\tod_jump_title/.test(texts.sync)) e.push('tools/sync_to_modtools.ps1 does not copy model_export/tod_jump_title (the card would never reach the tools root)');
  if (!/make_sign_card\.py"\) --check/.test(texts.build)) e.push('tools/build_map.ps1 does not run make_sign_card.py --check');
  const pre = [...jt.matchAll(/#precache\( "client_fx", "([^"]+)" \);/g)].map(m => m[1]);
  const used = [...new Set([...jt.matchAll(/"(tod\/(?:jump|sky)\/fx_[a-z_]+)"/g)].map(m => m[1]))];
  for (const f of used) if (!pre.includes(f)) e.push(`${f} is played but not precached`);
  for (const f of pre) {
    if (!new RegExp('^fx,' + f.replace(/\//g, '\\/') + '\\s*$', 'm').test(zone)) e.push(`${f} is precached but not zoned`);
    if (f.startsWith('tod/jump/') && !fxDir.includes(f.split('/').pop() + '.efx')) e.push(`${f}.efx was never generated (python tools/jump_title/gen_fx.py)`);
  }
  for (const f of fxDir) if (/^fx_jt_.*\.efx$/.test(f) && !pre.includes('tod/jump/' + f.replace(/\.efx$/, ''))) e.push(`${f} is generated but nothing plays it`);
  const aliases = [...jt.matchAll(/#define TOD_JT_ALIAS_\w+\s+"([^"]+)"/g)].map(m => m[1]).filter(a => a !== 'zmb_turn_on');
  const rows = csv.split(/\r?\n/).filter(Boolean).map(l => l.split(','));
  const head = rows[0] || [];
  const col = (n) => head.indexOf(n);
  // the dealer's laugh at the lit sign (2026-09-30) is the Black Market voice's own row in tod_shop.csv (tools/black_market_vo)
  const shopRows = fs.readFileSync(path.join(ROOT, 'sound/aliases/tod_shop.csv'), 'utf8').split(/\r?\n/).filter(Boolean).map(l => l.split(','));
  for (const a of aliases) {
    if (a.startsWith('tod_spin_vo_')) {
      const sr = shopRows.find(x => x[0] === a);
      if (!sr) e.push(`alias ${a} has no row in sound/aliases/tod_shop.csv (the dealer's table)`);
      else if (sr[shopRows[0].indexOf('PanType')] !== '2d') e.push(`alias ${a} must be a 2D row (a cinematic cue on the flyer's client), got ${sr[shopRows[0].indexOf('PanType')]}`);
      continue;
    }
    const r = rows.find(x => x[0] === a);
    if (!r) { e.push(`alias ${a} has no row in sound/aliases/tod_jump.csv`); continue; }
    const spec = r[col('FileSpec')] || '';
    if (/[\t\r\n]/.test(spec)) e.push(`alias ${a}: FileSpec has an escape character in it`);
    if (!wav(spec)) e.push(`alias ${a}: sound_assets/${spec.replace(/\\/g, '/')} is missing`);
    const want3d = a === 'tod_jt_warp' || a === 'tod_jt_jet';
    if ((r[col('PanType')] === '3d') !== want3d) e.push(`alias ${a}: PanType ${r[col('PanType')]} (want ${want3d ? '3d' : '2d'})`);
    if ((r[col('Looping')] === 'LOOPING') !== (a === 'tod_jt_jet')) e.push(`alias ${a}: Looping ${r[col('Looping')]}`);
  }
  if (!/"Filename": "tod_jump\.csv"/.test(szc)) e.push('sound/zoneconfig/zm_tod2_cybercity.szc does not load tod_jump.csv');
  // THE VEIL IS RETIRED (2026-09-30): the sky bakes the sign dull; nothing may play, zone or generate a veil again
  if (/fx_jt_veil/.test(jt) || /^fx,tod\/jump\/fx_jt_veil\s*$/m.test(zone) || fxDir.includes('fx_jt_veil.efx'))
    e.push('fx_jt_veil is back (the sign is baked dull now; a smoke veil over a lit sign is the retired design)');
  // THE CLOCK (the first play, 2026-09-29): a client `wait` counts frames (it ran 2.7x fast on the user's ~165 fps
  // machine: the watchdog cut the explosion at +1.2 s) and a MoveTo rides the same clock. Every delay in the scene
  // is waitrealtime and every motion is set per frame from GetRealTime; clock_probe alone waits on purpose.
  const code = jt.replace(/\/\/[^\n]*/g, '');
  const probe = (code.match(/function clock_probe\([\s\S]*?\n\}/) || [''])[0];
  const rest = code.replace(probe, '');
  const plain = rest.match(/\bwait\b\s*\(?\s*[\w.]+/g) || [];
  if (plain.length) e.push(`_tod_jump_title.csc times with a script wait (${plain.join(' | ')}): use waitrealtime (a client wait counts frames)`);
  const movers = rest.match(/\b(MoveTo|MoveX|MoveY|MoveZ|MoveGravity|RotateTo|RotateYaw|RotatePitch|RotateRoll|RotateVelocity)\s*\(/g) || [];
  if (movers.length) e.push(`_tod_jump_title.csc moves with ${movers.join(', ')}: those ride the frame-counted script clock (set .origin per frame from GetRealTime)`);
  if (!/waitrealtime\( TOD_JT_WATCHDOG \);/.test(rest)) e.push('the watchdog does not wait in real time');
  const igniteFn = (rest.match(/function ignite\([\s\S]*?\n\}/) || [''])[0];
  const revealFn = (rest.match(/function reveal\([\s\S]*?\n\}/) || [''])[0];
  const cleanupFn = (rest.match(/function cleanup\([\s\S]*?\n\}/) || [''])[0];
  const droppedFn = (rest.match(/function dropped\([\s\S]*?\n\}/) || [''])[0];
  const sceneFn = (rest.match(/function scene\([\s\S]*?\n\}/) || [''])[0];
  if (!/level thread reveal\( localClientNum, s \);/.test(igniteFn)) e.push('ignite() does not start the reveal');
  if (!/waitrealtime\( TOD_JT_REVEAL \);/.test(revealFn) || !/TOD_JT_ALIAS_IGNITE/.test(revealFn) || !/TOD_JT_ALIAS_POWER/.test(revealFn))
    e.push('the reveal must wait TOD_JT_REVEAL in real time and then play the power surge (tod_jt_ignite + zmb_turn_on)');
  if (/TOD_JT_ALIAS_IGNITE|TOD_JT_ALIAS_POWER/.test(igniteFn)) e.push('the power surge plays at the ignition again (buried under the boom): it belongs to the reveal');
  // THE LIT CARD: shown by the reveal (with the flicker) and by a scene cut after the ignite (at once); loaded hidden at
  // the start; never shown or deleted by anything else
  if (/sign_on\(|Show\(\)|fx_jt_blaze/.test(igniteFn)) e.push('ignite() lights the sign or starts the blaze: it must stay dull under the fire until the reveal');
  if (!/sign_on\( localClientNum, "reveal", true \);/.test(revealFn)) e.push('the reveal does not flicker the lit card on (sign_on(..., true))');
  if (!/"tod\/jump\/fx_jt_blaze"/.test(revealFn)) e.push('the reveal does not start the blaze over the held card');
  if (!/tod_jump_title_ignite[\s\S]*sign_on\( localClientNum, why, false \)/.test(cleanupFn)) e.push('a scene cut after the ignite does not light the sign at once (cleanup)');
  if (/tod_jt_lit\[[^\]]*\] Delete|card Delete/.test(cleanupFn + droppedFn)) e.push('a scene deletes the lit card: it belongs to the client for the match');
  if (!/lit_card\( localClientNum \);/.test(sceneFn)) e.push('the scene does not load the lit card at its start (it must be resident before the reveal)');
  const cardFn = (rest.match(/function lit_card\([\s\S]*?\n\}/) || [''])[0];
  if (!/SetModel\( TOD_JT_SIGN_MODEL \);\s*card Hide\(\);/.test(cardFn)) e.push('lit_card() must Hide() the card right after SetModel (dull until the reveal)');
  if (!/card thread sign_follow\( localClientNum \);/.test(cardFn)) e.push('the lit card does not follow the camera (it would slide off the sign)');
  const onFn = (rest.match(/function sign_on\([\s\S]*?\n\}/) || [''])[0];
  if (!/waitrealtime\( p\[ i \] \/ 1000\.0 \)/.test(onFn) || !/card Show\(\);/.test(onFn)) e.push('sign_on() must flicker in real time and end with the card shown');
  return e;
}

function wiringTexts() {
  return {
    jp: L.text.jp, jt: L.text.jt,
    zone: read('zone_source/zm_tod2_cybercity.zone'),
    entry: read('scripts/zm/zm_tod2_cybercity.csc'),
    csv: exists('sound/aliases/tod_jump.csv') ? read('sound/aliases/tod_jump.csv') : '',
    szc: read('sound/zoneconfig/zm_tod2_cybercity.szc'),
    fxDir: exists('share/raw/fx/tod/jump') ? fs.readdirSync(path.join(ROOT, 'share/raw/fx/tod/jump')) : [],
    wav: (spec) => exists('sound_assets/' + spec.replace(/\\/g, '/')),
    signModel: L.S.SIGN_MODEL, cardGdt: L.CARD_GDT,
    cardPng: exists('model_export/tod_jump_title/_images/i_tod_jt_sign_lit.png'),
    cardBin: exists('model_export/tod_jump_title/tod_jt_sign_lit.xmodel_bin'),
    sync: read('tools/sync_to_modtools.ps1'), build: read('tools/build_map.ps1'),
  };
}

// ---- the ledger (after a link) ---------------------------------------------------------------------------------
if (process.argv.includes('--ledger')) {
  const p = process.argv[process.argv.indexOf('--ledger') + 1];
  const t = p && fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : '';
  if (!t) { console.error('test_jump_title --ledger: no ledger at ' + p); process.exit(1); }
  const want = [...L.text.jt.matchAll(/#precache\( "client_fx", "([^"]+)" \);/g)].map(m => 'fx,' + m[1] + ',');
  const miss = want.filter(w => !t.includes(',' + w));
  const script = /scripts\/zm\/zm_tod2_cybercity\/_tod_jump_title\.csc/.test(t);
  const card = t.includes(',xmodel,' + L.S.SIGN_MODEL + ',') && t.includes(',material,mc/mtl_' + L.S.SIGN_MODEL.replace(/^tod_/, 'tod_') + ',')
    && t.includes(',image,i_' + L.S.SIGN_MODEL.replace(/^tod_/, 'tod_'));
  if (miss.length || !script || !card) {
    console.error('JUMP TITLE LEDGER FAIL: ' + (miss.length ? 'missing ' + miss.join(' ') : '') + (script ? '' : ' _tod_jump_title.csc not linked')
      + (card ? '' : ' the lit sign card (xmodel ' + L.S.SIGN_MODEL + ' + its material + image) not linked'));
    process.exit(1);
  }
  console.log(`JUMP TITLE LEDGER OK: ${want.length} effects + the client script + the lit sign card linked`);
  process.exit(0);
}

// ---- run the live scene --------------------------------------------------------------------------------------
const a = lockstep(L); check(!a.length, 'A. lockstep: run time = beat gap, bow = the gunship, sign bearing / elevation / layout distance agree, wreck points = the contact', 'A. ' + a.join(' | '));
const b = beats(L); check(!b.length, `B. beats: start / warps ${L.S.WARP_A} + ${L.S.WARP_B} / charge ${L.BEATS.SHIPS} / impact ${L.BEATS.IMPACT} / ignite ${L.BEATS.IGNITE} (inside the full white) / reveal ${(L.BEATS.IGNITE + L.S.REVEAL).toFixed(2)} (the lit card flickers ${L.S.FLICKER_SECS} s, the blaze from ${(L.BEATS.IGNITE + L.S.REVEAL + L.S.FLICKER_SECS).toFixed(2)}) / end ${L.BEATS.END}; the hulls go at +${L.S.UNDER_WHITE} under the white`, 'B. ' + b.join(' | '));
const c = frame(L); check(!c.e.length, `C. frame (65 deg, letterboxed, ${takeoffs(L).length} take-offs x ${L.SPOTS.length} landings x ${VIEWS.length} launch views): A at its warp ${c.worst.warpA.toFixed(2)}, B ${c.worst.warpB.toFixed(2)}, bows ${c.worst.bows.toFixed(2)}, crash ${c.worst.crash.toFixed(1)} deg off centre, sign ${c.worst.sign.toFixed(2)}`, 'C. ' + c.e.join(' | '));
const d = sky(L); check(!d.e.length, `D. sky: both ships inside the sealed volume on their whole path, nearest solid / keep-out ${d.minGap} u (${d.who}), the sign host + lit card inside the volume, the card behind every hull point that crosses it`, 'D. ' + (d.e || d).join(' | '));
const f = audible(L, wiringTexts().csv); check(!f.e.length, `F. heard: the warp and the engines at full level out past the farthest ship (${f.far} u), the ship loop is the gunship engine, every crash cue at full alias volume`, 'F. ' + f.e.join(' | '));
const e = wiring(wiringTexts()); check(!e.length, 'E. wiring: five beats once each, the client listens to all five, 7 effects precached + zoned + generated (no veil), 6 aliases with their wavs, the sound table loaded, ships hidden until their warp, the host follows the camera, the lit card generated + zoned + synced + gated, shown only by the reveal / a cut after the ignite', 'E. ' + e.join(' | '));

// ---- negative controls: the checks must catch the breakage they exist for -----------------------------------------
const clone = (o) => JSON.parse(JSON.stringify(o));
const neg = (name, fn) => { let caught = false; try { caught = fn(); } catch (err) { caught = false; } check(caught, 'negative control: ' + name + ' is caught', 'NEGATIVE CONTROL MISSED: ' + name); };
neg('RUN_SECS off the beat gap', () => { const x = clone(L); x.S.RUN_SECS += 0.3; return lockstep(x).length > 0; });
neg('a glow distance out of step with gen_fx', () => { const x = clone(L); x.S.SIGN_DIST = 9000; return lockstep(x).length > 0; });
neg('the ignition outside the white (4.6 s)', () => { const x = clone(L); x.BEATS.IGNITE = x.BEATS.IMPACT + 0.7; return beats(x).length > 0; });
neg('a stale blaze (the old life from the ignite)', () => { const x = clone(L); x.FX.BLAZE_LIFE = 7300; return beats(x).length > 0; });
neg('the sign lit right after the impact (reveal 0.3 s)', () => { const x = clone(L); x.S.REVEAL = 0.3; x.FX.REVEAL = 0.3; return beats(x).length > 0; });
neg('the sign lit 2.4 s after the impact again (the fourth pass)', () => { const x = clone(L); x.S.REVEAL = 2.2; x.FX.REVEAL = 2.2; return beats(x).length > 0; });
neg('the flicker inside a longer full white (0.7 s hold)', () => { const x = clone(L); x.FLASH.HOLD = 700; return beats(x).some(m => /lost in the white/.test(m)); });
neg('a flicker that strobes for 1.2 s', () => { const x = clone(L); x.S.FLICKER_SECS = 1.2; return beats(x).length > 0; });
neg('the card sized at the old 11,000 u', () => { const x = clone(L); x.CARD.sign_dist = 11000; return lockstep(x).length > 0; });
neg('the card in front of the ships (SIGN_DIST 6000)', () => { const x = clone(L); x.S.SIGN_DIST = 6000; x.CARD.sign_dist = 6000; x.CARD.width = 2 * 6000 * Math.tan(G.rad(x.CARD.w_deg / 2)); const r = sky(x); return (r.e || r).length > 0; });
neg('too little time on the title', () => { const x = clone(L); x.BEATS.END = x.BEATS.IGNITE + x.S.REVEAL + x.S.FLICKER_SECS + 1.0; return beats(x).length > 0; });
neg('a script wait in the client scene', () => { const t = wiringTexts(); t.jt = t.jt.replace('waitrealtime( TOD_JT_UNDER_WHITE );', 'wait TOD_JT_UNDER_WHITE;'); return wiring(t).length > 0; });
neg('a MoveTo in the client scene', () => { const t = wiringTexts(); t.jt += '\nfunction bob() { self MoveTo( ( 0, 0, 60 ), 1.1 ); }\n'; return wiring(t).length > 0; });
neg('the sign lit at the ignition (under the fire)', () => { const t = wiringTexts(); t.jt = t.jt.replace(/(function ignite\([^)]*\)\s*\{)/, '$1\n\tsign_on( localClientNum, "ignite", false );'); return wiring(t).length > 0; });
neg('the veil back in the zone', () => { const t = wiringTexts(); t.zone += '\nfx,tod/jump/fx_jt_veil\n'; return wiring(t).length > 0; });
neg('a scene deleting the lit card', () => { const t = wiringTexts(); t.jt = t.jt.replace(/(function cleanup\([^)]*\)\s*\{)/, '$1\n\tlevel.tod_jt_lit[ localClientNum ] Delete();'); return wiring(t).length > 0; });
neg('the card model not zoned', () => { const t = wiringTexts(); t.zone = t.zone.replace(/^xmodel,tod_jt_sign_lit\s*$/m, ''); return wiring(t).length > 0; });
neg('the card material zoned bare', () => { const t = wiringTexts(); t.zone += '\nmaterial,mtl_tod_jt_sign_lit\n'; return wiring(t).length > 0; });
neg('the power surge back at the ignition', () => { const t = wiringTexts(); t.jt = t.jt.replace(/(function ignite\([^)]*\)\s*\{)/, '$1\n\tPlaySound( localClientNum, TOD_JT_ALIAS_IGNITE, ( 0, 0, 0 ) );'); return wiring(t).length > 0; });
neg('a blaze outliving its host', () => { const x = clone(L); x.S.HOST_LINGER = 0.5; return beats(x).length > 0; });
neg('two beats in one frame', () => { const x = clone(L); x.BEATS.IGNITE = x.BEATS.IMPACT + 0.02; return beats(x).length > 0; });
neg('the hulls removed before the white is full', () => { const x = clone(L); x.S.UNDER_WHITE = 0.02; return beats(x).length > 0; });
neg('ship B warping in off the frame edge', () => { const x = clone(L); x.S.WARP_B = 1.6; return frame(x).e.length > 0; });
neg('the crash moved 3,000 u north', () => { const x = clone(L); x.S.CRASH = G.add(x.S.CRASH, [0, 3000, 0]); return frame(x).e.length > 0; });
neg('the crash dropped into the tower', () => { const x = clone(L); x.S.CRASH = [0, 3000, 21000]; const r = sky(x); return (r.e || r).length > 0; });
neg('ship_spawn without the Hide', () => { const t = wiringTexts(); t.jt = t.jt.replace(/ship Hide\(\);/, ''); return wiring(t).length > 0; });
neg('a clientNotify in the ignition frame (cine_reveal)', () => { const t = wiringTexts(); t.jp = t.jp.replace(/(function cine_reveal\([^)]*\)\s*\{)/, '$1\n\tself util::clientNotify( "tod_x" );'); return wiring(t).length > 0; });
neg('the retired tod_jump_reveal sent again', () => { const t = wiringTexts(); t.jp += '\n\tself util::clientNotify( "tod_jump_reveal" );\n'; return wiring(t).length > 0; });
neg('an effect precached but not zoned', () => { const t = wiringTexts(); t.zone = t.zone.replace(/^fx,tod\/jump\/fx_jt_boom\s*$/m, ''); return wiring(t).length > 0; });
neg('an alias row missing', () => { const t = wiringTexts(); t.csv = t.csv.split(/\r?\n/).filter(l => !l.startsWith('tod_jt_boom,')).join('\n'); return wiring(t).length > 0; });
neg('the engines fading from 3,000 u again (the first pass)', () => { const t = wiringTexts(); const rows = t.csv.split(/\r?\n/); const h = rows[0].split(','); const i = h.indexOf('DistMin'); t.csv = rows.map(l => { const x = l.split(','); if (x[0] === 'tod_jt_jet') x[i] = '3000'; return x.join(','); }).join('\n'); return audible(L, t.csv).e.length > 0; });
neg('the ship loop back on the fleet\'s jet hiss at volume 74', () => { const t = wiringTexts(); const rows = t.csv.split(/\r?\n/); const h = rows[0].split(','); t.csv = rows.map(l => { const x = l.split(','); if (x[0] === 'tod_jt_jet') { x[h.indexOf('FileSpec')] = 'tod\\sfx\\tod_sky_jet.wav'; x[h.indexOf('VolMax')] = '74'; } return x.join(','); }).join('\n'); return audible(L, t.csv).e.length > 0; });

for (const s of ok) console.log('  ok   ' + s);
for (const s of fails) console.log('  FAIL ' + s);
if (fails.length) { console.log(`\ntest_jump_title FAILED (${fails.length})`); process.exit(1); }
console.log(`\ntest_jump_title OK - the crash at ${L.S.CRASH.join(',')}: warps ${L.S.WARP_A}/${L.S.WARP_B}, charge ${L.BEATS.SHIPS}, impact ${L.BEATS.IMPACT}, ignite ${L.BEATS.IGNITE}, swing back ${L.BEATS.END}.`);
