'use strict';
// tools/haven/test_haven.js — THE HAVENS' build gate (docs/202, the safe zones).
//
// User 2026-10-02: the safe zones "need to act more like a safe zone ... a dome or
// like a force field that animates when you walk in and walk out ... zombies ...
// 33% slower and ... 33% less damage". User 2026-10-03 (v3): "the dome should be
// evil at first have doppleghast inside and a couple manglers. You must kill them
// and then the area turns into a safe zone ... two distinct states." User 2026-10-03
// (v4): "Safe zone should be the entire area ... the elites are not allowed to leave
// the dome ... bullets cannot go in or outside the dome. Until its a safe zone ...
// all perks and ammo crates pap etc should be inside of the dome. Going inside will
// make your screen dark".
//
//   A. THE NUMBERS — the user's 33% slower / 33% less damage, kills from inside
//      paying 25%, the bleed-out grace (x1.5, LOCKSTEP with the HUD), the guardian
//      roster (never fewer than a Doppelghast and a couple of Manglers, more below).
//   B. LOCKSTEP — the generated anchors (_tod_breather_data.gsc) agree with the one
//      layout source (tools/haven_layout.js): the field's sphere and its membership
//      radii / body point / z band, the machines INSIDE it, the guardian spots (inside
//      it, spread), the wake / leash bands, the sign, the barrier's name; the dome's
//      manifest agrees with both (the darkness, the barrier material).
//   C. WIRING — zone, precache, eventstrings, the HUD widget's event names and flags,
//      the health tint's bleed mask + the two kit bars, the sound aliases + wavs, the
//      ten effects, the GDT (the barrier material: the stock weapon clip + missile clip
//      + no penetration, nonsolid to bodies), the map's four barrier brushmodels, the
//      sync, _tod_main, the HUD (the darkness), the elite modules' hunt filter and
//      relocation hook, the spawn calm, the pad / arena locks, _tod_bosses' barrier lane.
//   D. HOOKS — every rate writer and both player-damage lanes fold the field in; every
//      kill payout pays through kill_pay, and every arm of the score popup previews it.
//   E. BEHAVIOUR — the SHIPPING _tod_haven.gsc run through tools/sky_ships/gsc_eval.js
//      (method calls / ternaries / threads lowered to what the interpreter speaks):
//      the CORRUPTED state does nothing for you (no slow, no cut, no tax, no bleed, no
//      ripple; the HUD's red state; the pad lock) and takes you into the darkness; its
//      BARRIER stands (solid, every hit across it refused both ways, a guardian always
//      inside its own field, a shot that stops on it answered); the wake raises the
//      roster inside the field on SPREAD spots with the in-field hunt filter, the fence
//      and the relocation hook; the guardians count down, the last one starts THE
//      PURIFICATION (v5: the convulsion keeps the barrier up and the darkness on, the
//      collapse drops the barrier, hides the dome and kills the ordinary zombies inside
//      (never an elite, never outside), the bloom makes the field safe - the darkness
//      lifts with its cue, the floor gets the bigger SECURED flash), and the SAFE state:
//      membership on the sphere with hysteresis, the damage cut and its throttled tell,
//      the crossing flow, the kill pay, the bleed grace (held through a down), the AI
//      edge (slow on / off, the push feedback, the visible-slow carriers and their cap).
//   F. NEGATIVE CONTROLS — mutants of the shipping module that the suite must catch.
//   G. THE PURIFICATION's clock (v5) — the strobe schedule climbs, accelerates and ends
//      inside the convulsion; the generators read it out of the module; the HUD's void
//      and banner kinds are in lockstep; the purge sound covers the timeline; the
//      corrupted dome is its own breached mesh with a dim twin.
//
// Usage: node tools/haven/test_haven.js [--data <path to a _tod_breather_data.gsc>]
//        (--data lets the gate run against a scratch regen before the wire step)
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const read = rel => fs.readFileSync(path.isAbsolute(rel) ? rel : path.join(ROOT, rel), 'utf8').replace(/\r\n/g, '\n');
const exists = rel => fs.existsSync(path.join(ROOT, rel));
const { gscLoad, V } = require('../sky_ships/gsc_eval.js');
const HAVEN_LAYOUT = require('../haven_layout.js');

const FLOORS = [10, 20, 30, 40];
const SIGN_MODELS = [].concat(...FLOORS.map(f => ['tod_haven_sign_' + f, 'tod_haven_sign_' + f + '_dark']));
const DOME_MODELS = ['tod_haven_dome', 'tod_haven_dome_pulse', 'tod_haven_dome_flash', 'tod_haven_dome_dark', 'tod_haven_dome_dark_dim', 'tod_haven_dome_dark_flash'];
const FX_KEYS = ['TOD_HAVEN_FX_AMBIENT', 'TOD_HAVEN_FX_CORRUPT', 'TOD_HAVEN_FX_CROSS', 'TOD_HAVEN_FX_PUSH', 'TOD_HAVEN_FX_BOOT',
  'TOD_HAVEN_FX_WAKE', 'TOD_HAVEN_FX_GUARD_DOWN', 'TOD_HAVEN_FX_CLEANSE', 'TOD_HAVEN_FX_SLOWED', 'TOD_HAVEN_FX_DEFLECT',
  'TOD_HAVEN_FX_FURY', 'TOD_HAVEN_FX_CONVULSE', 'TOD_HAVEN_FX_COLLAPSE'];
const SND_KEYS = ['TOD_HAVEN_SND_ENTER', 'TOD_HAVEN_SND_EXIT', 'TOD_HAVEN_SND_PUSH', 'TOD_HAVEN_SND_ABSORB', 'TOD_HAVEN_SND_IGNITE', 'TOD_HAVEN_SND_HUM',
  'TOD_HAVEN_SND_HUM_DARK', 'TOD_HAVEN_SND_WAKE', 'TOD_HAVEN_SND_GUARD_DOWN', 'TOD_HAVEN_SND_CLEANSE',
  'TOD_HAVEN_SND_DARK_IN', 'TOD_HAVEN_SND_DARK_BREATH', 'TOD_HAVEN_SND_DEFLECT',
  'TOD_HAVEN_SND_PURGE', 'TOD_HAVEN_SND_GROAN', 'TOD_HAVEN_SND_DARK_LIFT'];
// v4: the membership in floor terms (a body standing on the floor): its body point is
// BODY_UP over its origin, so it is in within this horizontal radius of C, out past the other
const R_IN = Math.sqrt(HAVEN_LAYOUT.IN_R3 ** 2 - (HAVEN_LAYOUT.BODY_UP - HAVEN_LAYOUT.DOME_C) ** 2);
const R_OUT = Math.sqrt(HAVEN_LAYOUT.OUT_R3 ** 2 - (HAVEN_LAYOUT.BODY_UP - HAVEN_LAYOUT.DOME_C) ** 2);

// ---------------------------------------------------------------------------
// POST-LINK (build_map.ps1 after the link): every haven asset is in the linker ledger.
//   node tools/haven/test_haven.js --ledger <usermaps/.../assetinfo/zm_tod2_cybercity.csv>
// The ledger's rows are "index,type,name,resident,streamed,parentStack".
// ---------------------------------------------------------------------------
if (process.argv[2] === '--ledger') {
  const ledger = fs.readFileSync(process.argv[3], 'utf8');
  const have = new Set();
  for (const line of ledger.split(/\r?\n/)) {
    const c = line.split(',');
    if (c.length > 2) have.add(c[1].trim().toLowerCase() + ',' + c[2].trim().replace(/\\/g, '/').toLowerCase());
  }
  const want = [
    ...DOME_MODELS.map(m => ['xmodel', m]), ...SIGN_MODELS.map(m => ['xmodel', m]),
    ...['ambient', 'corrupt', 'cross', 'push', 'boot', 'wake', 'guard_down', 'cleanse', 'slowed', 'deflect', 'fury', 'convulse', 'collapse', 'motes'].map(n => ['fx', 'tod/haven/fx_tod_haven_' + n]),
    ['image', 'i_tod_haven_vignette'], ['image', 'i_tod_haven_field'], ['image', 'i_tod_haven_field_dark'], ['image', 'i_tod_haven_darkness'],
    ...FLOORS.map(f => ['image', 'i_tod_haven_sign_' + f]), ...FLOORS.map(f => ['image', 'i_tod_haven_sign_' + f + '_dark']),
    ['scriptparsetree', 'scripts/zm/zm_tod2_cybercity/_tod_haven.gsc'],
    ['rawfile', 'ui/uieditor/widgets/hud/aetheriumwidgets/todhaven.lua'],
  ];
  let miss = 0;
  for (const [t, n] of want) if (!have.has(t + ',' + n.toLowerCase())) { miss++; console.log('  MISSING from the ledger: ' + t + ',' + n); }
  console.log(miss ? `HAVEN LEDGER FAIL: ${miss} missing` : `HAVEN LEDGER OK: ${want.length} assets linked`);
  process.exit(miss ? 1 : 0);
}

const argData = process.argv.indexOf('--data');
const S = 'scripts/zm/zm_tod2_cybercity/';
// Before the wire step the module and the widget wait in art/haven/staged/ (outside every
// scanned tree, so no peer build meets a half-installed feature); after it they are live.
const STAGED = 'art/haven/staged/';
const live = exists(S + '_tod_haven.gsc');
const HAVEN = read(live ? S + '_tod_haven.gsc' : STAGED + '_tod_haven.gsc');
const DATA = read(argData > 0 ? process.argv[argData + 1] : S + '_tod_breather_data.gsc');
const LUA = read(exists('ui/uieditor/widgets/HUD/AetheriumWidgets/TodHaven.lua') ? 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodHaven.lua' : STAGED + 'TodHaven.lua');
const TINT_LUA = read('ui/uieditor/widgets/HUD/AetheriumWidgets/TodHealthTint.lua');
if (!live) console.log('NOTE: reading the STAGED module + widget (art/haven/staged) - the wire step has not run');

let fails = 0, checks = 0;
function check(ok, label) {
  checks++;
  if (!ok) { fails++; console.log('FAIL ' + label); }
}
function section(t) { console.log('-- ' + t); }

// the #defines of a GSC text: numbers, strings and booleans
function defs(text) {
  const out = {};
  for (const m of text.matchAll(/^#define\s+(\w+)\s+(-?[\d.]+|"[^"]*"|true|false)/gm)) out[m[1]] = m[2];
  return out;
}
const D = defs(HAVEN);
const num = k => Number(D[k]);
const str = k => (D[k] || '').replace(/^"|"$/g, '');
// a generated scalar: function name() { return N; }
const genNum = name => { const m = DATA.match(new RegExp('function ' + name + '\\(\\)\\s*\\{\\s*return (-?[\\d.]+);')); return m ? Number(m[1]) : NaN; };
// a generated point list: function name( z ) { a = []; a[ i ] = ( x, y, z ); ... }
const genPoints = name => {
  const st = DATA.indexOf('function ' + name + '(');
  if (st < 0) return [];
  const body = DATA.slice(st, DATA.indexOf('return a;', st));
  return [...body.matchAll(/a\[ \d+ \] = \( (-?[\d.]+), (-?[\d.]+), z \);/g)].map(m => [+m[1], +m[2]]);
};

// =============================================================================
section('A. THE NUMBERS');
check(num('TOD_HAVEN_SLOW') === 0.67, `an enemy inside moves at 0.67 (33% slower) — got ${D.TOD_HAVEN_SLOW}`);
check(num('TOD_HAVEN_DR') === 0.67, `a player inside takes 0.67 of enemy damage (33% less) — got ${D.TOD_HAVEN_DR}`);
check(num('TOD_HAVEN_KILL_PAY') === 0.25, `a kill made from inside pays 0.25 of its money — got ${D.TOD_HAVEN_KILL_PAY}`);
check(num('TOD_HAVEN_BLEEDOUT') === 1.5, `a player downed inside bleeds out 1.5x slower — got ${D.TOD_HAVEN_BLEEDOUT}`);
check(Number((TINT_LUA.match(/local BLEED_MULT = ([\d.]+)/) || [])[1]) === num('TOD_HAVEN_BLEEDOUT'), 'LOCKSTEP: TodHealthTint BLEED_MULT == TOD_HAVEN_BLEEDOUT');
check(num('TOD_HAVEN_CLEANSE_PTS') > 0, 'taking a haven pays everyone something');
// THE ROSTER IS THE PARTY (user 2026-10-05: "the dark dome should spawn in amount of elites as players in game"):
// one guardian per player, the first a Doppelghast; the per-floor roster is retired (THE WAKE runs the function).
check(num('TOD_HAVEN_GUARD_PER_PLAYER') === 1, 'one guardian per player in the game');
check(num('TOD_HAVEN_GUARD_D2_PARTY') === 4, 'a party of four raises a second Doppelghast');
check(!/TOD_HAVEN_GUARD_[DM]_\d|TOD_HAVEN_GUARD_PARTY_D/.test(HAVEN), 'the retired per-floor roster is gone whole');
check(4 * num('TOD_HAVEN_GUARD_PER_PLAYER') <= 7, 'a full party\'s roster stays under the elite roof\'s worst case');
check(num('TOD_HAVEN_GUARD_DOPPEL_UNITS') >= 5 && num('TOD_HAVEN_GUARD_MANGLER_UNITS') >= 5, 'a guardian has at least the round director\'s HP (5 round zombies)');
check(num('TOD_HAVEN_GUARD_ACTOR_RESERVE') >= 2, 'guardians leave actor slots for the horde');

// =============================================================================
section('B. LOCKSTEP');
check(genNum('haven_radius') === HAVEN_LAYOUT.DOME_R, `haven_radius ${genNum('haven_radius')} == layout DOME_R ${HAVEN_LAYOUT.DOME_R}`);
check(Math.abs(genNum('haven_in_r3') - (HAVEN_LAYOUT.DOME_S - HAVEN_LAYOUT.IN_PAD)) < 0.01, `haven_in_r3 ${genNum('haven_in_r3')} == DOME_S - IN_PAD`);
check(Math.abs(genNum('haven_out_r3') - (HAVEN_LAYOUT.DOME_S + HAVEN_LAYOUT.OUT_PAD)) < 0.01, `haven_out_r3 ${genNum('haven_out_r3')} == DOME_S + OUT_PAD`);
check(genNum('haven_body_up') === HAVEN_LAYOUT.BODY_UP && genNum('haven_z_below') === HAVEN_LAYOUT.Z_BELOW && genNum('haven_z_above') === HAVEN_LAYOUT.Z_ABOVE, 'the body point and the z band are the layout\'s');
check(Math.abs(genNum('haven_sphere_r') - HAVEN_LAYOUT.DOME_S) < 0.01, `haven_sphere_r ${genNum('haven_sphere_r')} == DOME_S ${HAVEN_LAYOUT.DOME_S}`);
check(Math.abs(genNum('haven_sphere_c') - HAVEN_LAYOUT.DOME_C) < 0.01, `haven_sphere_c ${genNum('haven_sphere_c')} == DOME_C ${HAVEN_LAYOUT.DOME_C}`);
// v4 THE WHOLE HALL: a low dome as wide as the hall, every machine inside it
check(HAVEN_LAYOUT.DOME_C < 0 && HAVEN_LAYOUT.DOME_R >= 320, `the field is as wide as the hall: ring ${HAVEN_LAYOUT.DOME_R}, its sphere's centre under the floor (${HAVEN_LAYOUT.DOME_C.toFixed(1)})`);
for (const k of ['pap', 'station', 'crate', 'wunderfizz']) {
  const f = HAVEN_LAYOUT.FURN[k];
  check(HAVEN_LAYOUT.insideBody([...f.trig, 0], HAVEN_LAYOUT.IN_R3) && HAVEN_LAYOUT.machineBox(k).every(q => HAVEN_LAYOUT.domeZ(Math.hypot(q[0] - HAVEN_LAYOUT.C[0], q[1] - HAVEN_LAYOUT.C[1])) >= f.h),
    `${k} stands INSIDE the field (its trigger in the membership, its body under the dome)`);
}
check(HAVEN_LAYOUT.HALL_RISERS.every(q => !HAVEN_LAYOUT.insideBody([...q, 0], HAVEN_LAYOUT.OUT_R3)), 'every hall riser is outside the field (the horde walks in)');
check(Math.abs(genNum('haven_top') - HAVEN_LAYOUT.DOME_TOP) < 0.01, `haven_top ${genNum('haven_top')} == DOME_TOP ${HAVEN_LAYOUT.DOME_TOP}`);
const cm = DATA.match(/function haven_center\( z \) \{ return \( (-?[\d.]+), (-?[\d.]+), z \); \}/);
check(!!cm && +cm[1] === HAVEN_LAYOUT.C[0] && +cm[2] === HAVEN_LAYOUT.C[1], `haven_center = layout C ${HAVEN_LAYOUT.C}`);
// the field's sphere meets the floor exactly at the gameplay radius (the dome's contact line IS the ring)
check(Math.abs(Math.sqrt(HAVEN_LAYOUT.DOME_S ** 2 - HAVEN_LAYOUT.DOME_C ** 2) - HAVEN_LAYOUT.DOME_R) < 0.01, 'the sphere meets the floor at DOME_R');
check(genNum('haven_z_above') >= HAVEN_LAYOUT.DOME_TOP, `the z band (${genNum('haven_z_above')}) covers the dome's top (${HAVEN_LAYOUT.DOME_TOP})`);
check(genNum('haven_z_above') < 384 - genNum('haven_z_below'), 'the z band never reaches the floor above (one haven per floor, a lap apart)');
check(!/TOD_HAVEN_Z_(BELOW|ABOVE)/.test(HAVEN), 'the module reads the generated z band (no hand-typed copy)');
const zs = (DATA.match(/function breather_zs\(\) \{ return array\( ([^)]*) \); \}/) || [])[1];
check(!!zs && zs.split(',').length === 4, 'four breather floors (10/20/30/40)');
// the guardians: their spots are the layout's, inside the field and off the pad; the bands are the layout's
const spots = genPoints('haven_guard_spots');
check(spots.length === HAVEN_LAYOUT.GUARD_SPOTS.length && spots.every((p, i) => Math.abs(p[0] - HAVEN_LAYOUT.GUARD_SPOTS[i][0]) < 0.01 && Math.abs(p[1] - HAVEN_LAYOUT.GUARD_SPOTS[i][1]) < 0.01), `haven_guard_spots = the layout's ${HAVEN_LAYOUT.GUARD_SPOTS.length} spots`);
check(spots.length >= 6 && spots.every(p => { const d = Math.hypot(p[0] - HAVEN_LAYOUT.C[0], p[1] - HAVEN_LAYOUT.C[1]); return HAVEN_LAYOUT.insideBody([...p, 0], HAVEN_LAYOUT.IN_R3 - 16) && d > 110 + 20; }), 'every guardian spot is inside the field and off the pad trigger');
check(spots.length >= 4 * num('TOD_HAVEN_GUARD_PER_PLAYER'), 'a spot for every guardian of a full party: they rise spread, one each');
check(/function haven_barrier_name\( floor \) \{ return "tod_haven_barrier_" \+ floor; \}/.test(DATA), 'the barrier\'s name is generated (haven_barrier_name)');
check(genNum('haven_wake_r') === HAVEN_LAYOUT.WAKE_R && genNum('haven_wake_z_lo') === HAVEN_LAYOUT.WAKE_Z[0] && genNum('haven_wake_z_hi') === HAVEN_LAYOUT.WAKE_Z[1], 'the wake band is the layout\'s');
check(genNum('haven_leash_r') === HAVEN_LAYOUT.LEASH_R && genNum('haven_leash_z_lo') === HAVEN_LAYOUT.LEASH_Z[0] && genNum('haven_leash_z_hi') === HAVEN_LAYOUT.LEASH_Z[1], 'the leash band is the layout\'s');
check(HAVEN_LAYOUT.WAKE_R > HAVEN_LAYOUT.DOME_R + HAVEN_LAYOUT.OUT_PAD && HAVEN_LAYOUT.LEASH_R > HAVEN_LAYOUT.WAKE_R, 'the wake band covers the field; the leash band contains the wake band');
check(HAVEN_LAYOUT.WAKE_Z[1] + 100 < 576 + 384 && HAVEN_LAYOUT.LEASH_Z[0] > -384 + 48, 'the bands stay on their own floor (never the haven floor below)');
const sm = DATA.match(/function haven_sign_org\( z \) \{ return \( (-?[\d.]+), (-?[\d.]+), z \+ (-?[\d.]+) \); \}/);
check(!!sm && +sm[1] === HAVEN_LAYOUT.SIGN.org[0] && +sm[2] === HAVEN_LAYOUT.SIGN.org[1] && +sm[3] === HAVEN_LAYOUT.SIGN.org[2] && genNum('haven_sign_yaw') === HAVEN_LAYOUT.SIGN.yaw, 'the sign anchor is the layout\'s');
if (exists('art/haven/manifest.json')) {
  const man = JSON.parse(read('art/haven/manifest.json'));
  check(man.field.R === HAVEN_LAYOUT.DOME_R && man.field.centre_above_floor === HAVEN_LAYOUT.DOME_C, 'the dome model was built from the current layout (manifest R / C)');
  check(Math.abs(man.field.sphere_r - HAVEN_LAYOUT.DOME_S) < 0.01, 'the dome model sphere radius matches the layout');
  check(!!man.states && man.states.safe.length === 3 && man.states.corrupted.length === 3, 'the dome ships a safe skin set and a corrupted skin set (v5: base / dim / flash)');
  // v5 THE BREACHED MESH: the corrupted dome is its own mesh - fewer triangles than the safe lattice, holes in it, a cracked-pane atlas
  check(!!man.dark_lods && man.dark_lods.length === man.lods.length && man.dark_lods.every((d, i) => d.holes > 0 && d.triangles < man.lods[i].triangles), 'the corrupted dome is a breached mesh (holes at every LOD, fewer triangles than the safe lattice)');
  check(!!man.dark && man.dark.hole_fraction >= 0.05 && man.dark.hole_fraction <= 0.2 && man.dark.tiles >= 4, `a tenth-ish of its cells breached (${man.dark && man.dark.hole_fraction}), at least four pane tiles in the atlas`);
  check(!!man.signs && man.signs.card[0] === HAVEN_LAYOUT.SIGN.w && man.signs.card[1] === HAVEN_LAYOUT.SIGN.h && SIGN_MODELS.every(m => man.signs.models.includes(m)), 'the sign card was built to the layout\'s size, one model per floor and state');
  check(!!man.darkness && man.darkness.image === 'i_tod_haven_darkness' && man.darkness.centre < 0.25 && man.darkness.edge >= 0.7, 'the darkness: a dim centre you can fight through, heavy edges (v4: "not crazy but for sure noticable")');
  check(!!man.barrier && man.barrier.material === HAVEN_LAYOUT.BARRIER.mat && man.barrier.overrides.missileClip === '1' && man.barrier.overrides.noPenetrate === '1', 'the barrier material is the weapon clip + missile clip + no penetration');
} else check(false, 'art/haven/manifest.json exists (run tools/haven/make_dome.py)');

// =============================================================================
section('C. WIRING');
const ZONE = read('zone_source/zm_tod2_cybercity.zone');
// a zone line, optionally followed by a // comment
const zoneHas = line => new RegExp('^' + line.replace(/[.\\/]/g, m => '\\' + m) + '\\s*(//.*)?$', 'm').test(ZONE);
check(zoneHas('scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_haven.gsc'), 'zone: the module');
for (const m of [...DOME_MODELS, ...SIGN_MODELS]) {
  check(zoneHas('xmodel,' + m), 'zone: xmodel ' + m);
  check(HAVEN.includes(`#precache( "model", "${m}" );`), 'precache: model ' + m);
}
check(!/^material,mtl_tod_haven_/m.test(ZONE) && !/^image,i_tod_haven_(field|sign)/m.test(ZONE), 'no bare material / model-image zone lines (they ride the xmodels; the bare-material linker trap)');
for (const k of FX_KEYS) {
  const fx = str(k);
  check(zoneHas('fx,' + fx), 'zone: fx ' + fx);
  check(HAVEN.includes(`#precache( "fx", "${fx}" );`), 'precache: fx ' + fx);
  check(exists('share/raw/fx/' + fx + '.efx'), 'effect file share/raw/fx/' + fx + '.efx');
  check(('fx/' + fx).length <= 63, `fx path under 63 chars (the runtime cut): ${fx}`);
}
// PK43 (2026-10-05): THE MOTES - the fourteenth haven effect (tools/haven/make_fx.py), played by _tod_atmosphere's
// lounge_fx under the key tod_lounge_motes (which also feeds the departure hall's GENERATED transit_hall_fx). It
// replaces env/light/fx_light_god_rays_dust_motes, a gfx_debug_missing_fx placeholder in the tools root that the map
// zoned (so the stub shipped and the shaft never drew): the stub must stay neither zoned, precached nor bound.
{
  const ATMO = read(S + '_tod_atmosphere.gsc');
  const MOTES = 'tod/haven/fx_tod_haven_motes', STUB = 'env/light/fx_light_god_rays_dust_motes';
  check(zoneHas('fx,' + MOTES) && ATMO.includes(`#precache( "fx", "${MOTES}" );`) && exists('share/raw/fx/' + MOTES + '.efx'), 'the motes: zoned, precached by _tod_atmosphere, generated');
  const bound = src => (src.match(/level\._effect\[ "tod_lounge_motes" \] = "([^"]+)";/) || [])[1];
  check(bound(ATMO) === MOTES, 'tod_lounge_motes is the map\'s own motes (' + bound(ATMO) + ')');
  check(/lounge_fx_at\( "tod_lounge_motes", tod_breather_data::haven_motes_org\( z \) \);/.test(ATMO), 'the motes still play at every haven threshold');
  check(!zoneHas('fx,' + STUB) && !ATMO.includes(`#precache( "fx", "${STUB}" )`), 'the stub is neither zoned nor precached');
  const oldAtmo = ATMO.replace(`= "${MOTES}";`, `= "${STUB}";`);
  check(oldAtmo !== ATMO && bound(oldAtmo) !== MOTES, 'NEGATIVE: the old stub binding is caught');
}
check(zoneHas('image,i_tod_haven_vignette'), 'zone: image i_tod_haven_vignette (the HUD tint)');
check(zoneHas('image,i_tod_haven_darkness'), 'zone: image i_tod_haven_darkness (v4: the darkness)');
check(!/^material,tod_haven_barrier/m.test(ZONE), 'no zone line for the barrier material (a map brush material rides in through the BSP)');
check(zoneHas('rawfile,ui/uieditor/widgets/HUD/AetheriumWidgets/TodHaven.lua'), 'zone: rawfile TodHaven.lua');
// eventstrings: every LuiNotifyEvent name is precached, and the HUD side listens for each
const events = [...HAVEN.matchAll(/LuiNotifyEvent\( &"(\w+)"/g)].map(m => m[1]);
check(new Set(events).size >= 4, `the module sends its HUD events (${[...new Set(events)].join(' ')})`);
for (const e of new Set(events)) {
  check(HAVEN.includes(`#precache( "eventstring", "${e}" );`), 'precache: eventstring ' + e);
  check(LUA.includes(`"${e}"`) || TINT_LUA.includes(`"${e}"`), 'the HUD listens for ' + e);
}
check(/LuiNotifyEvent\( &"tod_haven", 4, /.test(HAVEN) && /d\[ 4 \]/.test(LUA), 'tod_haven carries four ints (inside, flags, state, left) and the widget reads the fourth');
check(Number((LUA.match(/local FLAG_PULSE = (\d+)/) || [])[1]) === num('TOD_HAVEN_HUD_PULSE'), 'LOCKSTEP: FLAG_PULSE == TOD_HAVEN_HUD_PULSE');
check(Number((LUA.match(/local FLAG_HINT = (\d+)/) || [])[1]) === num('TOD_HAVEN_HUD_HINT'), 'LOCKSTEP: FLAG_HINT == TOD_HAVEN_HUD_HINT');
check(Number((LUA.match(/local STATE_CORRUPT = (\d+)/) || [])[1]) === num('TOD_HAVEN_STATE_CORRUPT') && Number((LUA.match(/local STATE_SAFE = (\d+)/) || [])[1]) === num('TOD_HAVEN_STATE_SAFE'), 'LOCKSTEP: the field states');
check(Number((LUA.match(/local BANNER_WAKE = (\d+)/) || [])[1]) === num('TOD_HAVEN_BANNER_WAKE') && Number((LUA.match(/local BANNER_SECURED = (\d+)/) || [])[1]) === num('TOD_HAVEN_BANNER_SECURED') && Number((LUA.match(/local BANNER_DOWN = (\d+)/) || [])[1]) === num('TOD_HAVEN_BANNER_DOWN'), 'LOCKSTEP: the banner kinds');
check(/RegisterImage\( "i_tod_haven_vignette" \)/.test(LUA), 'the HUD draws the zoned vignette');
check(/RegisterImage\( "i_tod_haven_darkness" \)/.test(LUA) && /darkTo\( state == STATE_CORRUPT \)/.test(LUA), 'the HUD draws the darkness off the CORRUPTED state (v4)');
// the bleed grace reaches the two kit bars
check(/function Tint\.BleedoutMs\( widget, base \)/.test(TINT_LUA) && /todHavenBleedMask/.test(TINT_LUA), 'TodHealthTint carries the bleed mask and BleedoutMs');
for (const w of ['AetheriumPlayerInfo', 'AetheriumPartyPlayers']) {
  const t = read('ui/uieditor/widgets/HUD/AetheriumWidgets/' + w + '.lua');
  const i = t.indexOf('bleedoutTime = CoD.TodHealthTint.BleedoutMs( self, bleedoutTime )');
  check(i > 0 && t.indexOf('beginAnimation("bleedout_timer", bleedoutTime', i) > i, `${w}'s bleed bar asks BleedoutMs before it starts`);
}
// sounds
const CSV = exists('sound/aliases/tod_haven.csv') ? read('sound/aliases/tod_haven.csv') : '';
for (const k of SND_KEYS) {
  const a = str(k);
  const row = CSV.split('\n').find(l => l.startsWith(a + ','));
  check(!!row, 'alias row ' + a + ' in sound/aliases/tod_haven.csv');
  if (row) {
    const wav = (row.match(/,(tod\\haven\\[\w]+\.wav|tod\/haven\/[\w]+\.wav),/) || [])[1];
    check(!!wav && exists('sound_assets/' + wav.replace(/\\/g, '/')), `${a}'s wav exists (${wav})`);
  }
}
check(/^tod_haven_hum_dark,.*LOOPING/m.test(CSV) && /^tod_haven_hum,.*LOOPING/m.test(CSV), 'both hums loop');
check(/^tod_haven_dark_breath,.*NONLOOPING/m.test(CSV) && /^tod_haven_dark_in,.*NONLOOPING/m.test(CSV), 'the darkness sounds are one-shots (the module re-plays the breath; a stuck 2D loop could never be stopped)');
const SZC = exists('sound/zoneconfig/zm_tod2_cybercity.szc') ? read('sound/zoneconfig/zm_tod2_cybercity.szc') : '';
check(/tod_haven\.csv/.test(SZC), 'the sound zone config loads tod_haven.csv');
// the GDT, its sync, the gates
check(exists('source_data/tod_haven.gdt') && read('source_data/tod_haven.gdt') === read('art/haven/tod_haven.gdt'), 'source_data/tod_haven.gdt == the generator\'s staged GDT');
const GDT = exists('source_data/tod_haven.gdt') ? read('source_data/tod_haven.gdt') : '';
for (const m of [...DOME_MODELS, ...SIGN_MODELS]) check(GDT.includes(`"${m}" ( "xmodel.gdf" )`), 'GDT: xmodel ' + m);
// THE BARRIER MATERIAL (v4): the stock weapon clip (whole), + missile clip + no penetration; nonsolid to bodies
{
  const mb = GDT.match(/"tod_haven_barrier" \( "material\.gdf" \)\s*\{([\s\S]*?)\n\t\}/);
  const f = mb ? Object.fromEntries([...mb[1].matchAll(/"(\w+)" "([^"]*)"/g)].map(x => [x[1], x[2]])) : {};
  check(!!mb && Object.keys(f).length > 800, `GDT: the barrier material is the donor's whole block (${Object.keys(f).length} fields)`);
  check(f.bulletClip === '1' && f.missileClip === '1' && f.noPenetrate === '1', 'the barrier stops bullets, missiles and penetration');
  check(f.nonSolid === '1' && f.playerClip === '0' && f.aiClip === '0' && f.vehicleClip === '0', 'the barrier is nonsolid to players and AI (bodies walk through)');
  check(f.noDraw === '1' && f.materialType === 'tools_blend' && f.usage === 'clip', 'the barrier is an invisible tools clip');
}
// THE BARRIER BRUSHMODELS (v4): one per haven floor, every brush in the barrier material
{
  const MAP = read('map_source/zm/zm_tod2_cybercity.map');
  for (const f of FLOORS) {
    const i = MAP.indexOf(`"targetname" "tod_haven_barrier_${f}"`);
    const st = MAP.lastIndexOf('{\n', i), cls = MAP.slice(st, i);
    let depth = 0, e = st;
    for (; e < MAP.length; e++) { if (MAP[e] === '{') depth++; else if (MAP[e] === '}' && --depth === 0) break; }
    const ent = MAP.slice(st, e + 1);
    const brushes = ent.split('\n{').length - 1;
    const faces = (ent.match(/^ \( /gm) || []).length, onMat = (ent.match(/\) tod_haven_barrier 128 128/g) || []).length;
    check(i > 0 && /"classname" "script_brushmodel"/.test(cls), `map: the floor ${f} barrier is a script_brushmodel`);
    check(brushes === HAVEN_LAYOUT.BARRIER.lon * HAVEN_LAYOUT.BARRIER.lat && faces > 0 && faces === onMat, `map: its ${brushes} brushes are the layout's shell, every face in tod_haven_barrier`);
  }
}
const SYNC = read('tools/sync_to_modtools.ps1');
check(/model_export\\tod_haven"\)/.test(SYNC), 'the sync carries model_export\\tod_haven');
const MAIN = read(S + '_tod_main.gsc');
check(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_haven;/.test(MAIN) && /\ttod_haven::init\(\);/.test(MAIN), '_tod_main loads and inits the module');
check(MAIN.indexOf('tod_doppelghast::init();') < MAIN.indexOf('tod_haven::init();') && MAIN.indexOf('tod_mangler::init();') < MAIN.indexOf('tod_haven::init();'), 'the elite modules init before the haven (it spawns through them)');
const HUD = read('ui/uieditor/menus/HUD/AetheriumHud.lua');
check(/TodHaven/.test(HUD), 'AetheriumHud mounts TodHaven');
const BUILD = read('tools/build_map.ps1');
for (const g of ['haven/test_haven.js")', 'haven/make_dome.py', 'haven/make_fx.py', 'haven/make_sounds.py', 'tools/test_haven_hud.lua', "haven/test_haven.js') --ledger"])
  check(BUILD.includes(g), 'build_map runs ' + g);
// THE GUARDIANS hunt their own floor: both elite modules honour the filter and the home spot
for (const mod of ['_tod_doppelghast', '_tod_mangler']) {
  const t = read(S + mod + '.gsc');
  check(/self \[\[ self\.tod_hunt_filter \]\]\( p \)/.test(t) && /self \[\[ self\.tod_hunt_filter \]\]\( current \)/.test(t), `${mod}::hunt_target asks the hunt filter for every candidate and the current target`);
  check(/isdefined\( self\.tod_hunt_filter \)[^\n]*\n\s*return undefined;/.test(t) || /if \( isdefined\( self\.tod_hunt_filter \) \)\s*return undefined;/.test(t), `${mod}::hunt_target returns NO target when the filter leaves none (never a random player)`);
  check(/self\.tod_hunt_home/.test(t), `${mod}::chase goes home when it has no target`);
}
check(/actor\.tod_hunt_filter = &guard_target_ok;/.test(HAVEN) && /actor\.tod_hunt_home = org;/.test(HAVEN), 'the module stamps every guardian with the filter and its home');
check(/actor\.tod_reloc_fn = &guard_reloc;/.test(HAVEN) && /actor thread guard_fence\( h \);/.test(HAVEN), 'the module stamps every guardian with the relocation hook and fences it (v4)');
check(/if \( isdefined\( self\.tod_reloc_fn \) \)\s*return self \[\[ self\.tod_reloc_fn \]\]\( target \);/.test(read(S + '_tod_doppelghast.gsc')), '_tod_doppelghast::reloc_point honours the relocation hook first (both elites relocate through it)');
check(/return tod_doppelghast::reloc_point\( target \);/.test(read(S + '_tod_mangler.gsc')), 'the Mangler relocates through _tod_doppelghast::reloc_point (so the hook covers it)');
check(/level\.tod_haven_prev_actor_damage = level\.callbackActorDamage;\s*level\.callbackActorDamage = &actor_damage_gate;/.test(HAVEN), 'the module wraps the actor damage front door (v4: the barrier\'s damage gate)');
check(/level\.tod_haven_barrier_fn = &barrier_blocks;/.test(HAVEN), 'the module publishes the barrier test for the player-damage lane');
check(/callback::on_spawned\( &haven_on_spawned \);/.test(HAVEN), 'every player\'s shots are watched (the barrier\'s answer)');
check(/tod_mangler::spawn_at\( org, target, \( 0, facing\[ 1 \], 0 \) \)/.test(HAVEN) && /tod_doppelghast::spawn_hunter\( org, target, \(TOD_HAVEN_GUARD_DOPPEL_UNITS\)|tod_doppelghast::spawn_hunter\( org, target, TOD_HAVEN_GUARD_DOPPEL_UNITS \)/.test(HAVEN), 'guardians spawn through the elite modules\' public spawners');
// THE SPAWN CALM (tweak #2) and THE LOCKS
const ENDLESS = read(S + '_tod_endless_rounds.gsc');
check(/function tod_player_in_breather\(\)\s*\{[^}]*\[\[ level\.tod_haven_calm_fn \]\]\(\)/.test(ENDLESS) && !/lounge_index_at/.test(ENDLESS.slice(ENDLESS.indexOf('function tod_player_in_breather('), ENDLESS.indexOf('function tod_player_in_breather(') + 400)), 'the x1.19 rest asks the haven (inside a SAFE field), not the hall box');
check(/level\.tod_haven_calm_fn = &calm_any;/.test(HAVEN) && /level\.tod_haven_locked_fn = &point_locked;/.test(HAVEN), 'the module publishes the calm and lock pointers');
const TP = read(S + '_tod_teleport.gsc');
check(/\[\[ level\.tod_haven_locked_fn \]\]/.test(TP) && /defeat the guardians/.test(TP), 'a pad inside a haven not yet taken is locked, and says so');
const ARENA = read(S + '_tod_arena.gsc');
check(/\[\[ level\.tod_haven_locked_fn \]\]/.test(ARENA) && /haven_corrupted/.test(ARENA), 'the Battle Arena gate refuses while its haven is corrupted');
check(/TOD_ARENA_HINT_GUARDIANS/.test(ARENA), 'the arena shows the guardians hint while corrupted');
// THE SEALED WAY DOWN (2026-10-04, user: "You must secure the dome area before you move on or else
// door cannot be bought"): the haven publishes the seal; the doors refuse on it, show one constant
// SEALED prompt and put back each trigger's OWN spawn-time string (no new triggerstring slot).
check(/level\.tod_haven_door_seal_fn = &door_seal_state;/.test(HAVEN), 'the module publishes the door-seal pointer');
const DOORS = read(S + '_tod_doors.gsc');
{
  const buy = DOORS.slice(DOORS.indexOf('function buy_trigger_wait('), DOORS.indexOf('function open_slab('));
  const iSeal = buy.indexOf('[[ level.tod_haven_door_seal_fn ]]( flag ) == 1'), iPay = buy.indexOf('zm_score::minus_to_player_score( price );');
  check(iSeal > 0 && iPay > iSeal && /== 1 \)\s*\{[\s\S]{0,400}?continue;/.test(buy.slice(iSeal - 80, iPay)), 'a door refuses (and charges nothing) while its haven seals it, asked on every press');
}
check(/function haven_seal_watch\( d \)/.test(DOORS) && /level thread haven_seal_watch\( d \);/.test(DOORS), 'every door runs the seal watch');
check(/t SetHintString\( "Open Door - SEALED - Secure the dome on this floor first" \);/.test(DOORS), 'the sealed prompt is ONE constant string (one triggerstring slot for all four doors)');
check(/t SetHintString\( "Hold \^3\[\{\+activate\}\]\^7 Open Door to " \+ t\.tod_hint_dest \+ " \^2\[Cost: " \+ t\.tod_hint_price \+ "\]" \);/.test(DOORS)
  && /t\.tod_hint_price = door_price_for\( cost, flag \);/.test(DOORS), 'the unseal puts back the trigger\'s own spawn-time string, never a re-priced one');
{
  const LUA = read('ui/uieditor/widgets/HUD/ZM_CursorHint/Prompts/PromptDoors.lua');
  check(/string\.find\( h, "sealed", 1, true \)/.test(LUA) && /SetLocked\( self, true \)/.test(LUA) && /SetFooterVisible\( self, false \)/.test(LUA) && /SetLocked\( self, false \)/.test(LUA),
    'the door card draws the sealed door locked, with no footer and no price, and resets for the next door');
}

// =============================================================================
section('D. HOOKS');
const SPEED = read(S + '_tod_zombie_speed.gsc'), BOSSES = read(S + '_tod_bosses.gsc');
check(/ASMSetAnimationRate\( rate_for_round\( round \+ add \) \* self slow_mult\(\) \* self safe_mult\(\) \);/.test(SPEED), 'the horde\'s ONE rate line folds safe_mult in');
check(/self\.tod_elite_base_rate \* mult \* self safe_mult\(\)/.test(SPEED), 'slow_elite folds safe_mult in');
check(/self\.tod_elite_base_rate \* self safe_mult\(\)/.test(SPEED), 'slow_elite_expire folds safe_mult in');
check(/function safe_mult\(\)\s*\{\s*if \( isdefined\( self\.tod_safe_mult \) \)\s*return self\.tod_safe_mult;\s*return 1\.0;/.test(SPEED), 'safe_mult reads the field (1.0 outside)');
check(/resume_rate \*= self\.tod_safe_mult;/.test(BOSSES), 'the pause restore keeps the field\'s slow');
check(/sMeansOfDeath !== "MOD_FALLING"\s*\)\s*haven_dr = \[\[ level\.tod_safezone_dr \]\]\( self \);/.test(BOSSES)
  && /isdefined\( eAttacker \) && !isplayer\( eAttacker \)/.test(BOSSES.slice(BOSSES.indexOf('haven_dr = 1.0;'), BOSSES.indexOf('haven_dr = 1.0;') + 300)),
  'the normal damage lane: enemy damage only, never a fall');
check(/dr = dr \* haven_dr;/.test(BOSSES), 'the normal lane multiplies the field into DR');
check(!/function apply_player_mitigations\(/.test(BOSSES), 'the Panzer-melee lane (its own field fold) retired whole with the Panzer (W2E, 2026-10-05)');
check(/rate \*= self\.tod_safe_mult;/.test(read(S + '_tod_doppelghast.gsc')), 'the Doppelghast chase loop reads the field');
check(/rate \*= self\.tod_safe_mult;/.test(read(S + '_tod_mangler.gsc')), 'the Mangler chase loop reads the field');
check(/\[\[ level\.tod_haven_inside_fn \]\]\( org \)\s*\)\s*return false;/.test(read(S + '_tod_stray.gsc')), 'the hunt never raises a zombie inside a field');
check(/level notify\( "tod_power_wave_z", orgs\[ i \]\[ 2 \] \);/.test(read(S + '_tod_fall.gsc')), 'the power wave tells the havens which floor it is passing');
check(/level\.tod_safezone_dr = &dr_for;/.test(HAVEN) && /level\.tod_haven_inside_fn = &point_inside_live;/.test(HAVEN), 'the module publishes both pointers');
{
  const lane = BOSSES.indexOf('[[ level.tod_haven_barrier_fn ]]( eAttacker, self )');
  const fnStart = BOSSES.indexOf('function boss_player_damage(');
  check(lane > fnStart && fnStart > 0 && /isdefined\( level\.tod_haven_barrier_fn \) && isdefined\( eAttacker \) && !isplayer\( eAttacker \) && \[\[ level\.tod_haven_barrier_fn \]\]\( eAttacker, self \) \)\s*return 0;/.test(BOSSES),
    '_tod_bosses: enemy damage to a player across a corrupted field\'s barrier is refused (v4)');
  // W2E (2026-10-05): the THROUGH-FLOOR SHIELD this was measured against retired with the Rogue Protector; the barrier
  // must still come before the callback's first damage write.
  check(lane < BOSSES.indexOf('final = iDamage;', fnStart) && BOSSES.indexOf('final = iDamage;', fnStart) > 0, '... before every other lane (nothing can land it first)');
}
// THE KILL PAY: every payout of kill money to a player goes through kill_pay
const UPG = read(S + '_tod_upgrades.gsc'), KIT = read('scripts/zm/_zm_aetherium_hud.gsc');
check(/level\.tod_haven_kill_pay_fn = &kill_pay;/.test(HAVEN) && /level\.tod_haven_kill_preview_fn = &kill_preview;/.test(HAVEN), 'the module publishes the kill-pay pointers');
check(/increment_player_stat\( "grenade_kills" \);\s*\}(\s*\/\/[^\n]*)*\s*if \( isdefined\( level\.tod_haven_kill_pay_fn \) \)\s*player_points = \[\[ level\.tod_haven_kill_pay_fn \]\]\( self, player_points \);\s*return player_points;/.test(UPG),
  'the stock kill money (zombie_death_score) pays through kill_pay');
check(/attacker\.tod_bounty_bank \+= kill_value \* rate \* haven_pay\( attacker \);/.test(UPG), 'BOUNTY\'s bank takes the quarter');
check(/bank \+= bounty_kill_value\( mod, hitloc, attacker \) \* rate \* haven_pay\( attacker \);/.test(UPG), 'BOUNTY\'s popup preview takes the same quarter');
check(/function haven_pay\( player \)\s*\{\s*if \( isdefined\( player \) && isdefined\( player\.tod_haven_pay \) \)\s*return player\.tod_haven_pay;\s*return 1\.0;/.test(UPG), 'haven_pay reads the field (1.0 outside)');
{
  const cb = KIT.slice(KIT.indexOf('function zombie_death_callback('), KIT.indexOf('function get_kill_type_bonus('));
  const scal = (cb.match(/zombie_point_scalar/g) || []).length;
  const paired = (cb.match(/\[\[ level\.tod_haven_kill_preview_fn \]\]\( ([\w.]+), player_points \);\s*player_points \*= level\.zombie_vars\[\1\.team\]\["zombie_point_scalar"\];/g) || []).length;
  check(scal === 8 && paired === scal, `the score popup previews the quarter for the right player right before Double Points in every arm (${paired} of ${scal})`);
}
check(/owner_pts = \[\[ level\.tod_haven_kill_pay_fn \]\]\( owner, owner_pts \);\s*owner zm_score::add_to_player_score\( owner_pts \);/.test(BOSSES)
  && /pts = \[\[ level\.tod_haven_kill_pay_fn \]\]\( attacker, int\( pts \) \);\s*attacker zm_score::add_to_player_score\( int\( pts \) \);/.test(BOSSES),
  'the elite purse pays the killer (and a companion\'s owner) through kill_pay; the feed row shows the paid number');
check(/kill_pts = \[\[ level\.tod_haven_kill_pay_fn \]\]\( p, kill_pts \);\s*p zm_score::add_to_player_score\( kill_pts \);/.test(read(S + '_tod_partners.gsc')), 'a companion\'s kill pays its owner through kill_pay');
check(/kill_pts = \[\[ level\.tod_haven_kill_pay_fn \]\]\( owner, kill_pts \);\s*owner zm_score::add_to_player_score\( kill_pts \);/.test(read(S + '_tod_necro_summon.gsc')), 'a Necromancer helper\'s kill pays its owner through kill_pay');
// the death hook RUN: with the pointer set it returns exactly kill_pay's answer
// for the whole kill; without it, stock's money untouched
{
  const vm = require('vm');
  const body = (src, name) => { const st = src.indexOf('{', src.indexOf('function ' + name + '(')); let e = st + 1, d = 1; while (d) { if (src[e] === '{') d++; if (src[e] === '}') d--; e++; } return src.slice(st + 1, e - 1); };
  const ctx = { isdefined: x => x !== undefined, IS_TRUE: x => x === true, IsSubStr: (a, b) => a.includes(b) };
  vm.createContext(ctx);
  Object.assign(ctx, { base: () => 50, bonus: () => 10, stat: () => {} });
  const h = body(UPG, 'zombie_death_score').replace('zm_score::get_zombie_death_player_points', 'base')
    .replace('self zm_score::player_add_points_kill_bonus', 'bonus').replaceAll('self zm_stats::increment_client_stat', 'stat')
    .replaceAll('self zm_stats::increment_player_stat', 'stat').replace('[[ level.tod_haven_kill_pay_fn ]]', 'level.tod_haven_kill_pay_fn');
  vm.runInContext('function deathScore(self,event,mod,hit_location,zombie_team,damage_weapon) {' + h + '}', ctx);
  ctx.level = { zombie_team: 'axis', zombie_vars: { allies: { zombie_powerup_insta_kill_on: 0 } } };
  const plain = ctx.deathScore({ tod_class: 'assault', team: 'allies' }, 'death', 'MOD_RIFLE_BULLET', 'torso', 'axis', {});
  const seen = [];
  ctx.level.tod_haven_kill_pay_fn = (who, pts) => { seen.push(pts); return 30; };
  const cut = ctx.deathScore({ tod_class: 'assault', team: 'allies' }, 'death', 'MOD_RIFLE_BULLET', 'torso', 'axis', {});
  check(plain === 60 && cut === 30 && seen.join() === '60', `the death hook, run: no field = stock's 60; a field = kill_pay's answer for the whole kill (asked ${seen.join(' / ')})`);
}

// =============================================================================
section('G. THE PURIFICATION (v5)');
const STEPS = ((HAVEN.match(/function purge_strobe_steps\(\)\s*\{\s*return array\(([^)]*)\);/) || [, ''])[1]).split(',').map(s => Number(s.trim())).filter(v => !Number.isNaN(v));
check(STEPS.length >= 6 && STEPS[0] === 0, `the strobe schedule has at least six steps from 0 (${STEPS.length})`);
check(STEPS.every((v, i) => i === 0 || v > STEPS[i - 1]), 'the strobe schedule climbs');
const GAPS = STEPS.slice(1).map((v, i) => v - STEPS[i]);
check(GAPS.length > 0 && GAPS.every((gp, i) => i === 0 || gp < GAPS[i - 1]), `the strobe ACCELERATES (every gap shorter than the last: ${GAPS.join(' ')})`);
check(STEPS.length > 0 && STEPS[STEPS.length - 1] + 70 <= num('TOD_HAVEN_PURGE_CONVULSE_SECS') * 1000, 'the last strobe (70 ms) ends inside the convulsion');
check(num('TOD_HAVEN_PURGE_CONVULSE_SECS') >= 1.5 && num('TOD_HAVEN_PURGE_CONVULSE_SECS') <= 4 && num('TOD_HAVEN_PURGE_VOID_SECS') >= 0.2 && num('TOD_HAVEN_PURGE_VOID_SECS') <= 0.6,
  'the convulsion is 1.5..4 s and the void 0.2..0.6 s (long enough to read, short enough to fight through)');
check(num('TOD_HAVEN_PURGE_INFLATE_SECS') > 0 && num('TOD_HAVEN_PURGE_INFLATE_SECS') <= 1.5 && num('TOD_HAVEN_PURGE_INFLATE_FROM') > 0 && num('TOD_HAVEN_PURGE_INFLATE_FROM') < 0.5, 'the safe dome inflates from a point in under 1.5 s');
check(Number((LUA.match(/local VOID_MS = (\d+)/) || [])[1]) === Math.round(num('TOD_HAVEN_PURGE_VOID_SECS') * 1000), 'LOCKSTEP: TodHaven.lua VOID_MS == TOD_HAVEN_PURGE_VOID_SECS x 1000');
check(Number((LUA.match(/local BANNER_PURGE = (\d+)/) || [])[1]) === num('TOD_HAVEN_BANNER_PURGE') && Number((LUA.match(/local BANNER_COLLAPSE = (\d+)/) || [])[1]) === num('TOD_HAVEN_BANNER_COLLAPSE')
  && Number((LUA.match(/local BANNER_STROBE = (\d+)/) || [])[1]) === num('TOD_HAVEN_BANNER_STROBE'), 'LOCKSTEP: the purification\'s banner kinds');
for (const gen of ['tools/haven/make_fx.py', 'tools/haven/make_sounds.py']) {
  const g = read(gen);
  check(g.includes('purge_strobe_steps') && g.includes('TOD_HAVEN_PURGE_CONVULSE_SECS'), `${gen} reads the convulsion's clock and the strobe schedule out of the module (lockstep by construction)`);
}
{
  const wav = 'sound_assets/tod/haven/tod_haven_purge.wav';
  const secs = exists(wav) ? (fs.statSync(path.join(ROOT, wav)).size - 44) / 2 / 48000 : 0;
  check(secs >= num('TOD_HAVEN_PURGE_CONVULSE_SECS') + num('TOD_HAVEN_PURGE_VOID_SECS'), `the purge sound (${secs.toFixed(2)} s) covers the convulsion + the void`);
}
check(/function collapse\( h \)/.test(HAVEN) && /function purify\( h \)/.test(HAVEN) && /level thread purge_run\( h \);/.test(HAVEN) && /function dome_convulse\( h \)/.test(HAVEN) && /function dome_inflate\( h \)/.test(HAVEN),
  'the timeline: cleanse (entry) -> purge_run -> collapse / purify, the dome\'s own strobe and its inflation');
check(/h\.dome SetScale\( TOD_HAVEN_PURGE_INFLATE_FROM \);/.test(HAVEN) && /h\.dome SetScale\( 1 \);/.test(HAVEN), 'the safe dome inflates from TOD_HAVEN_PURGE_INFLATE_FROM to full');
check((HAVEN.match(/\bEarthquake\(/g) || []).length >= 3, 'the quakes: the convulsion, the collapse, a guardian down');
check(/ai\.tod_ps_exempt = true;\s*ai DoDamage\( ai\.health \+ TOD_HAVEN_PURGE_KILL_MARGIN, ai\.origin \);\s*if \( isdefined\( ai \) \)\s*ai\.tod_ps_exempt = undefined;/.test(HAVEN),
  'the collapse\'s kill is the stock nuke idiom, exempted from the power scale and cleared');
check(num('TOD_HAVEN_PURGE_KILL_MARGIN') === 666, 'the margin is the nuke\'s 666 (a kill intent to the power scale)');
check(/"tod_haven_dome_dark" \( "xmodel\.gdf" \)\s*\{\s*"filename" "tod_haven\/tod_haven_dome_dark_lod0\.xmodel_bin"/.test(GDT) && /mtl_tod_haven_field_dark mtl_tod_haven_field_dark_dim/.test(GDT),
  'the GDT: the corrupted dome is its own mesh, with a dim twin on it');
check(exists('model_export/tod_haven/tod_haven_dome_dark_lod0.xmodel_bin') && exists('model_export/tod_haven/tod_haven_dome_dark_lod1.xmodel_bin'), 'the breached mesh\'s two LODs are exported');
check(CSV.split('\n').filter(l => l.startsWith('tod_haven_groan,')).length >= 2, 'the groan has at least two takes behind one alias');
check(/TodHavenVoid/.test(LUA) && /tod_haven_void_in/.test(LUA) && /tod_haven_void_hold/.test(LUA) && /tod_haven_void_out/.test(LUA), 'the HUD has the void (in -> hold -> out)');
check(/local function grip\(\)/.test(LUA) && /not st\.dark or st\.gripped/.test(LUA), 'the HUD grips the veil through the convulsion (the breath stops)');
check(/RotateYaw\( RandomFloatRange\( TOD_HAVEN_RATCHET_DEG_MIN, TOD_HAVEN_RATCHET_DEG_MAX \), TOD_HAVEN_RATCHET_SECS \);/.test(HAVEN) && /want = "dim";/.test(HAVEN) && /function groan_loop\( h \)/.test(HAVEN),
  'the corrupted look: the ratchet turn, the brown-outs, the groans');
check(/ambient_start\( h, TOD_HAVEN_FX_FURY \);/.test(HAVEN), 'the wake swaps the fight\'s loop in');

// =============================================================================
// E. BEHAVIOUR — the interpreter harness
// =============================================================================
const KEYWORDS = new Set(['if', 'else', 'while', 'for', 'foreach', 'return', 'wait', 'thread', 'notify', 'endon', 'waittill',
  'waittillmatch', 'function', 'in', 'switch', 'case', 'break', 'continue', 'true', 'false', 'undefined', 'waittillframeend']);

// ( C ? A : B ): at statement level (X = ( C ? A : B );) lowered LAZILY to an if / else;
// anywhere else to the eager builtin __tern( C, A, B ) (only literal arms there).
function lowerTernaries(s) {
  for (let guard = 0; guard < 400; guard++) {
    const q = s.indexOf('?');
    if (q < 0) return s;
    let depth = 0, open = -1;
    for (let i = q - 1; i >= 0; i--) {
      if (s[i] === ')') depth++;
      else if (s[i] === '(') { if (depth === 0) { open = i; break; } depth--; }
    }
    let close = -1, colon = -1; depth = 0;
    for (let i = q + 1; i < s.length; i++) {
      const c = s[i];
      if (c === '(') depth++;
      else if (c === ')') { if (depth === 0) { close = i; break; } depth--; }
      else if (c === ':' && depth === 0 && s[i + 1] !== ':' && s[i - 1] !== ':' && colon < 0) colon = i;
    }
    if (open < 0 || close < 0 || colon < 0) throw new Error('lowerTernaries: cannot parse near ' + JSON.stringify(s.slice(q - 40, q + 40)));
    const C = s.slice(open + 1, q).trim(), A = s.slice(q + 1, colon).trim(), B = s.slice(colon + 1, close).trim();
    const before = s.slice(0, open), after = s.slice(close + 1);
    const lhs = before.match(/(^|\n)([ \t]*)([\w.\[\] ]+?) = $/);
    if (lhs && /^\s*;/.test(after)) {
      const head = before.slice(0, before.length - lhs[0].length + lhs[1].length);
      s = head + lhs[2] + 'if ( ' + C + ' ) ' + lhs[3] + ' = ' + A + '; else ' + lhs[3] + ' = ' + B + after.replace(/^\s*/, '');
    } else {
      s = before + '__tern( ' + C + ', ' + A + ', ' + B + ' )' + after;
    }
  }
  throw new Error('lowerTernaries: runaway');
}

// GSC -> what gsc_eval speaks: self becomes every local function's first parameter;
// `obj method( a )` becomes `method( obj, a )`; a plain local call passes self on;
// threads are dropped (the gate never runs a waiting function); dev blocks unwrap.
function lower(src) {
  let s = src.replace(/\r\n/g, '\n').replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '');
  s = s.replace(/^\s*\/#\s*$/gm, '').replace(/^\s*#\/\s*$/gm, '');
  s = s.replace(/&"/g, '"').replace(/&(\w+)/g, '"&$1"').replace(/!==/g, '!=').replace(/===/g, '==');
  // dev_log( ... ); calls go whole: their arguments format vectors into strings,
  // which the interpreter does not model (the logger itself is dev-only output)
  for (let i = s.indexOf('dev_log('); i >= 0; i = s.indexOf('dev_log(', i + 1)) {
    if (/function\s+$/.test(s.slice(Math.max(0, i - 12), i))) continue;
    let depth = 0, j = i + 'dev_log'.length;
    for (; j < s.length; j++) { if (s[j] === '(') depth++; else if (s[j] === ')' && --depth === 0) break; }
    const semi = s.indexOf(';', j);
    s = s.slice(0, i) + ';' + s.slice(semi + 1);   // an empty statement: an unbraced `if ( c ) dev_log( ... );` keeps its meaning
    i = Math.max(0, i - 1);
  }
  s = s.replace(/^[ \t]*[\w.\[\] ]+? thread [^;\n]*;[ \t]*$/gm, '');
  s = s.replace(/^[ \t]*[\w.\[\] ]+? notify\([^;\n]*\);[ \t]*$/gm, '');   // a notify wakes only threads, which the gate never runs
  // a pointer call `obj [[ fn ]]( args )` -> the harness builtin __ptrcall( fn, obj, args )
  s = s.replace(/([\w.]+) \[\[ ([\w.]+) \]\]\( /g, '__ptrcall( $2, $1, ');
  s = lowerTernaries(s);
  const local = new Set([...s.matchAll(/\bfunction\s+(\w+)\s*\(/g)].map(m => m[1]));
  // tokens: identifiers (with ns::), numbers, strings, whitespace, single chars
  const toks = s.match(/[A-Za-z_]\w*(?:::\w+)?|\d+\.\d*|\.\d+|\d+|"(?:[^"\\]|\\.)*"|\s+|[^\s]/g);
  const out = [];
  const lastSig = () => { for (let i = out.length - 1; i >= 0; i--) if (!/^\s+$/.test(out[i])) return i; return -1; };
  for (let i = 0; i < toks.length; i++) {
    const t = toks[i];
    let j = i + 1; while (j < toks.length && /^\s+$/.test(toks[j])) j++;
    const isCall = /^[A-Za-z_]/.test(t) && !KEYWORDS.has(t) && toks[i + 1] === '(';
    if (t === 'function' && /^\s+$/.test(toks[i + 1] || '') && toks[i + 3] === '(') {
      // function NAME( params ) -> function NAME( self[, params] )
      let k = i + 4; while (/^\s+$/.test(toks[k])) k++;
      out.push('function', ' ', toks[i + 2], '( self' + (toks[k] === ')' ? ' ' : ', '));
      i = i + 3;
      continue;
    }
    if (isCall) {
      // a method call? the previous significant token ends an object expression and
      // there is whitespace between it and this name
      const p = lastSig();
      const prev = p >= 0 ? out[p] : '';
      const spaced = p >= 0 && p < out.length - 1;
      const objEnd = spaced && (/^[A-Za-z_]\w*$/.test(prev) && !KEYWORDS.has(prev) || prev === ']');
      let k = i + 2; while (/^\s+$/.test(toks[k])) k++;
      const empty = toks[k] === ')';
      if (objEnd) {
        // pull the object expression (a chain of names, .members and [ index ]es) off the output
        let a = p, depth = 0;
        for (; a >= 0; a--) {
          const o = out[a];
          if (o === ']') { depth++; continue; }
          if (o === '[') { depth--; continue; }
          if (depth > 0) continue;
          if (/^\s+$/.test(o)) { if (a > 0 && (out[a - 1] === '.' || out[a + 1] === '.')) continue; break; }
          if (o === '.' || /^[A-Za-z_]\w*$/.test(o)) continue;
          break;
        }
        const obj = out.splice(a + 1).join('').trim();
        out.push(' ', t, '( ' + obj + (empty ? ' ' : ', '));
        i = i + 1;
        continue;
      }
      if (local.has(t) && out[lastSig()] !== '::') {
        out.push(t, '( self' + (empty ? ' ' : ', '));
        i = i + 1;
        continue;
      }
    }
    out.push(t);
  }
  return out.join('');
}

const IS_TRUE = x => x !== undefined && x !== null && x !== false && x !== 0;
const d2 = (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2;
function load(havenText, env) {
  const all = {};
  for (const [k, v] of Object.entries(defs(havenText))) all[k] = v;
  let ents = 100;
  const g = gscLoad([['tod_haven', lower(havenText)], ['tod_breather_data', DATA]], all, {
    builtins: {
      IS_TRUE, __tern: (c, a, b) => (IS_TRUE(c) ? a : b),
      GetTime: () => env.now,
      GetPlayers: () => env.players,
      GetAITeamArray: () => env.ais,
      GetFreeActorCount: () => env.freeActors,
      GetEntityNumber: e => e.num || 0,
      Distance2DSquared: d2,
      DistanceSquared: (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2,
      Distance: (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]),
      LengthSquared: v => v[0] * v[0] + v[1] * v[1] + v[2] * v[2],
      VectorNormalize: v => { const l = Math.hypot(v[0], v[1], v[2]) || 1; return V(v[0] / l, v[1] / l, v[2] / l); },
      Max: Math.max, sqrt: Math.sqrt, isalive: e => !!e && e.alive !== false, isplayer: e => !!e && !!e.isPlayer,
      PrintLn: () => {}, dev_log: () => {},
      Spawn: (kind, org) => { const e = { kind, origin: org, num: ents++ }; env.spawned.push(e); return e; },
      SetModel: (e, m) => { e.model = m; }, Show: e => { e.shown = true; }, Hide: e => { e.shown = false; },
      NotSolid: e => { if (e) e.solid = false; }, Solid: e => { if (e) e.solid = true; },
      GetEnt: (name, key) => (key === 'targetname' ? env.barriers[name] : undefined),
      'callback::on_spawned': () => {},
      PlayLocalSound: (e, a) => { env.local.push(e.name + ':' + a); }, StopLocalSound: (e, a) => { env.stopped.push(e.name + ':' + a); },
      __ptrcall: (fn, self, ...args) => fn(self, ...args),
      Delete: e => { e.deleted = true; env.deleted.push(e); }, LinkTo: (e, to) => { e.linked = to; },
      ForceTeleport: (e, org) => { e.origin = org; env.teleports.push(org); },
      PlayFXOnTag: () => {}, StopLoopSound: (e, s) => { env.loopStops.push(s); }, PlayLoopSound: (e, a) => { env.loops.push(a); },
      PlaySound: (e, a) => { env.sounds.push(a); },
      PlaySoundToPlayer: (e, a) => { env.sounds.push('2p:' + a); },
      // v5: the purification's engine calls
      SetScale: (e, k) => { e.scale = k; }, Earthquake: (s, d, o, r) => { env.quakes.push([s, d, r]); },
      DoDamage: (e, dmg) => { e.damaged = dmg; e.exempt_at_hit = e.tod_ps_exempt; if (dmg >= (e.health || 0)) e.alive = false; },
      RandomFloatRange: (a, b) => a, cos: d => Math.cos(d * Math.PI / 180), sin: d => Math.sin(d * Math.PI / 180),
      LuiNotifyEvent: (e, name, n, a, b, c, d) => { env.lui.push({ who: e.name, name, a, b, c, d }); },
      ASMSetAnimationRate: (e, r) => { e.rate = r; env.rates.push(r); },
      'laststand::player_is_in_laststand': p => !!p.downed,
      'zm_score::add_to_player_score': (p, n) => { p.score = (p.score || 0) + n; },
      'zombie_utility::is_zombie': e => !!e.is_zombie,
      'tod_zombie_speed::under_anim_slow': () => false,
      'tod_zombie_speed::apply_speed_for_round': (e, r) => { e.rate = 1.2 * (e.tod_safe_mult === undefined ? 1 : e.tod_safe_mult); env.rates.push(e.rate); },
      'tod_zombie_speed::current_round': () => 20,
      'tod_zombie_speed::elite_rate_owned': e => !!env.paused,
      'tod_zombie_speed::elite_rate_now': e => e.tod_elite_base_rate * (e.tod_safe_mult === undefined ? 1 : e.tod_safe_mult),
      'tod_doppelghast::valid_target': p => !!p && !!p.isPlayer && p.alive !== false && p.sessionstate === 'playing' && !p.downed,
      'tod_doppelghast::hunter_hp': units => units * 100,
      'tod_doppelghast::spawn_hunter': (org, target, units) => env.spawnActor('doppelghast', org, target, units),
      'tod_mangler::spawn_at': (org, target, angles) => env.spawnActor('mangler', org, target, 5),
    },
  });
  return g;
}

function suite(havenText) {
  const out = [];
  let n = 0;
  const t = (ok, label) => { n++; if (!ok) out.push(label); };
  const env = { now: 10000, spawned: [], deleted: [], sounds: [], loops: [], lui: [], rates: [], teleports: [], players: [], ais: [], freeActors: 20, actors: [],
    local: [], stopped: [], barriers: {}, quakes: [], loopStops: [] };
  for (const f of FLOORS) env.barriers['tod_haven_barrier_' + f] = { kind: 'script_brushmodel', name: 'barrier ' + f, solid: true };
  env.spawnActor = (kind, org, target, units) => {
    if (env.denySpawn) return undefined;
    const a = { kind, origin: org, alive: true, health: units * 100, maxhealth: units * 100, favoriteenemy: target, num: 500 + env.actors.length, is_zombie: false };
    if (kind === 'doppelghast') a.tod_doppelghast = true; else a.tod_mangler = true;
    env.actors.push(a);
    return a;
  };
  const g = load(havenText, env);
  const L = g.level;
  // init()'s data half, without its threads (lowered: threads dropped, dev_log a builtin)
  g.call('tod_haven::init', [L]);
  t(L.tod_havens && Object.keys(L.tod_havens).length === 4, 'init builds four havens');
  t(typeof L.tod_safezone_dr !== 'undefined' && typeof L.tod_haven_calm_fn !== 'undefined' && typeof L.tod_haven_locked_fn !== 'undefined', 'init publishes the damage, calm and lock pointers');
  const H = L.tod_havens;
  const h0 = H[0];
  t(h0.floor === 10 && H[3].floor === 40 && h0.safe === false && h0.state === 'dark', 'the havens are floors 10 and 40 at the ends, dark and not yet safe');
  // THE SEALED WAY DOWN: a dark (unbooted) haven seals nothing, any other door is no haven's
  const seal = (flag) => g.call('tod_haven::door_seal_state', [L, flag]);
  t(seal('enter_lap10') === 0 && seal('enter_lap40') === 0, 'door seal: a dark haven (before the power) seals nothing');
  t(seal('enter_lap11') === -1 && seal('enter_roof') === -1 && seal(undefined) === -1, 'door seal: a door that is no haven floor\'s way down is never sealed');
  t(Object.values(H).every(h => h.barrier === env.barriers['tod_haven_barrier_' + h.floor] && h.barrier.solid === false && h.barrier_solid === false),
    'init finds every haven\'s barrier by its generated name and lets it go (nothing to stop before the dome boots)');
  const C = h0.center, z = h0.z;
  const IN = R_IN, OUT = R_OUT;   // v4: the sphere's membership in floor terms (a body standing on the floor)
  const at = (dx, dz = 0) => V(C[0] + dx, C[1], z + dz);
  const haven = (o, cur) => g.call('tod_haven::haven_at', [L, o, cur]);
  const lastLui = () => env.lui[env.lui.length - 1];

  // --- membership (any live haven) ---
  t(haven(at(0), -1) === -1, 'a dead (unbooted) haven holds nobody');
  for (const h of Object.values(H)) { h.live = true; h.state = 'corrupt'; }
  t(haven(at(0), -1) === 0, 'the centre is inside');
  t(haven(at(IN - 1), -1) === 0, 'just inside the in-radius is inside');
  t(haven(at(IN + 4), -1) === -1, 'between in and out, a body arriving from outside is NOT yet in (hysteresis)');
  t(haven(at(IN + 4), 0) === 0, 'between in and out, a body already in STAYS in (hysteresis)');
  t(haven(at(OUT + 1), 0) === -1, 'past the out-radius, a body is out');
  t(haven(at(0, -60), -1) === -1, 'below the z band is out (the floor under it)');
  t(haven(at(0, 180), -1) === 0, 'inside the dome high up (a jump, a ledge) is in');
  t(haven(at(0, HAVEN_LAYOUT.DOME_TOP + 10), -1) === -1, 'over the dome\'s crown is out (the sphere, not a cylinder)');
  t(haven(at(IN - 40, 200), -1) === -1, 'high over the rim is out: the galleries over the dome are never inside it');
  t(haven(at(0, 384), -1) === -1, 'the floor above is out');
  t(haven(V(C[0], C[1], H[2].z + 10), -1) === 2, 'floor 30\'s dome holds floor 30');
  t(haven(at(IN + 4), 2) === -1, 'another haven\'s membership never widens this one');
  H[1].live = false;
  t(haven(V(C[0], C[1], H[1].z + 10), -1) === -1, 'an unbooted haven never holds');
  H[1].live = true;

  // ===== THE CORRUPTED STATE: the field does nothing =====
  t(g.call('tod_haven::point_inside_live', [L, at(10)]) === false, 'point_inside_live: a corrupted field is no sanctuary (the horde may rise in it)');
  t(g.call('tod_haven::point_locked', [L, at(0, 32)]) === true, 'point_locked: the pad at a corrupted haven\'s heart is dead');
  t(g.call('tod_haven::point_locked', [L, V(C[0] + 290, C[1] + 290, z + 32)]) === true, 'point_locked: anywhere in that hall reads locked (its far corner, outside the field)');
  t(g.call('tod_haven::point_locked', [L, V(C[0], C[1], z + 2000)]) === false, 'point_locked: a pad elsewhere is free');
  t(seal('enter_lap10') === 1 && seal('enter_lap40') === 1, 'door seal: a live, corrupted haven seals its floor\'s way down');
  H[1].live = false; H[1].booting = true;
  t(seal('enter_lap20') === 1, 'door seal: a haven still booting already seals (no window to slip through)');
  H[1].live = true; H[1].booting = false;
  t(g.call('tod_haven::calm_any', [L]) === false, 'calm_any: nobody inside a safe field');
  const p = { name: 'P1', isPlayer: true, sessionstate: 'playing', origin: at(OUT + 200), num: 0 };
  env.players = [p];
  t(g.call('tod_haven::dr_for', [L, p]) === 1, 'dr_for: a player the module never saw takes full damage');
  const step = (o, dt = 100) => { env.now += dt; p.origin = o; g.call('tod_haven::player_update', [p, env.now]); };
  step(at(OUT + 200));
  env.lui.length = 0; env.sounds.length = 0; env.spawned.length = 0;
  step(at(IN - 30));                                      // walk into the CORRUPTED field
  let ev = lastLui();
  t(p.tod_haven === 0 && ev && ev.name === 'tod_haven' && ev.a === 1 && ev.c === num('TOD_HAVEN_STATE_CORRUPT') && ev.b === num('TOD_HAVEN_HUD_PULSE'), 'walking into a corrupted field: the HUD gets inside + the CORRUPTED state + a pulse, no hint');
  t(env.sounds.length === 0 && env.spawned.length === 0, 'a corrupted field has no crossing ripple and no sound');
  t(p.tod_haven_dark === true && env.local.includes('P1:' + str('TOD_HAVEN_SND_DARK_IN')), 'THE DARKNESS takes you: the swallow plays to you alone (the breath loop is threaded)');
  t(p.tod_haven_pay === undefined, 'no kill tax in a corrupted field');
  t(p.n_bleedout_time_multiplier === undefined && !p.tod_haven_bleed, 'no bleed grace in a corrupted field');
  t(g.call('tod_haven::dr_for', [L, p]) === 1, 'dr_for: a corrupted field cuts nothing');
  t(g.call('tod_haven::calm_any', [L]) === false, 'calm_any: a player inside a corrupted field calms nothing');
  t(h0.flash_until <= env.now, 'the corrupted dome does not flash for a crossing');
  env.sounds.length = 0;
  step(at(OUT + 30));                                     // walk out of the corrupted field
  ev = lastLui();
  t(p.tod_haven === -1 && ev.a === 0 && ev.b === 0 && env.sounds.length === 0, 'leaving a corrupted field drains the HUD silently');
  t(p.tod_haven_dark === false && env.stopped.includes('P1:' + str('TOD_HAVEN_SND_DARK_BREATH')), 'leaving lifts the darkness: its breath is cut');
  const darkIns = env.local.length;
  g.call('tod_haven::dark_set', [p, false]);
  t(env.local.length === darkIns, 'the darkness off twice is a no-op');

  // ===== THE BARRIER (v4): solid while corrupted; every hit across it refused, both ways =====
  g.call('tod_haven::barrier_set', [L, h0, true]);
  t(h0.barrier.solid === true && h0.barrier_solid === true, 'the barrier goes up (solid) with the corrupted dome');
  const pIn = { name: 'IN', isPlayer: true, sessionstate: 'playing', origin: at(IN - 60), tod_haven: 0, num: 6 };
  const pOut = { name: 'OUT', isPlayer: true, sessionstate: 'playing', origin: at(OUT + 120), tod_haven: -1, num: 7 };
  const zIn = { is_zombie: true, origin: at(IN - 50), alive: true, tod_haven_ai: 0, num: 320 };
  const zOut = { is_zombie: true, origin: at(OUT + 90), alive: true, tod_haven_ai: -1, num: 321 };
  const blocks = (a, v) => g.call('tod_haven::barrier_blocks', [L, a, v]);
  t(blocks(pOut, zIn) === true, 'a shot from outside at a body inside is refused');
  t(blocks(pIn, zOut) === true, 'a shot from inside at a body outside is refused');
  t(blocks(zIn, pOut) === true && blocks(zOut, pIn) === true, 'an enemy across the barrier hurts no player (both ways)');
  t(blocks(pIn, zIn) === false && blocks(pOut, zOut) === false, 'the same side: everything lands');
  t(blocks(pIn, pIn) === false && blocks(undefined, zIn) === false && blocks(pOut, undefined) === false, 'self / world / no victim: never refused');
  const guardAtRim = { is_zombie: false, origin: at(OUT + 40), alive: true, tod_haven_ai: -1, tod_haven_guard: 0, num: 322 };
  t(blocks(pIn, guardAtRim) === false && blocks(pOut, guardAtRim) === true, 'a guardian always counts as inside its own field (never untouchable at the rim)');
  const fresh = { is_zombie: true, origin: at(IN - 30), alive: true, num: 323 };
  t(blocks(pOut, fresh) === true, 'an enemy the tick has not seen yet is placed where it stands');
  // the actor damage front door: a blocked hit never reaches the chain; every other hit does
  const chained = [];
  L.tod_haven_prev_actor_damage = (self, inflictor, attacker, dmg) => { chained.push([self.num, attacker && attacker.num, dmg]); };
  g.call('tod_haven::actor_damage_gate', [zIn, pOut, pOut, 50, 0, 'MOD_RIFLE_BULLET', {}, at(0), V(1, 0, 0), 'torso', at(0), 0, 0, 0, 'flesh', V(0, 0, 1)]);
  t(chained.length === 0 && L.tod_haven_stats.blocked === 1, 'the gate swallows a hit across the barrier (no damage, no reaction, no points)');
  g.call('tod_haven::actor_damage_gate', [zIn, pIn, pIn, 50, 0, 'MOD_RIFLE_BULLET', {}, at(0), V(1, 0, 0), 'torso', at(0), 0, 0, 0, 'flesh', V(0, 0, 1)]);
  t(chained.length === 1 && chained[0][2] === 50, 'a hit on the same side goes down the chain untouched');
  // an enemy inside a corrupted field: no slow, no push feedback, no carrier
  const zc = { is_zombie: true, origin: at(IN - 20), alive: true, num: 300 };
  env.ais = [zc];
  env.rates.length = 0; env.spawned.length = 0;
  g.call('tod_haven::ai_update', [zc, env.now]);
  t(zc.tod_haven_ai === 0 && zc.tod_safe_mult === undefined && env.spawned.length === 0 && env.sounds.length === 0, 'a zombie inside a corrupted field is tracked but never slowed, no sparks, no carrier');

  // ===== THE WAKE: the roster rises inside the field =====
  const roster = (n, hv) => { env.players = Array.from({ length: n }, (_, i) => ({ ...p, name: 'P' + (i + 1), num: i }));
    return g.call('tod_haven::guard_count', [L, hv, 'doppelghast']) + 'd' + g.call('tod_haven::guard_count', [L, hv, 'mangler']) + 'm'; };
  const rosters = [1, 2, 3, 4].map(n => roster(n, H[3])).join(' ');
  t(rosters === '1d0m 1d1m 1d2m 2d2m', 'the roster is the party: 1 player 1d, 2 1d1m, 3 1d2m, 4 2d2m (got ' + rosters + ')');
  t([1, 2, 3, 4].map(n => roster(n, h0)).join(' ') === rosters, 'the same roster on every floor (floor 10 = floor 40)');
  env.players = [p];
  const far = { ...p, name: 'FAR', num: 1, origin: V(C[0] + 3000, C[1], z) };
  env.players = [far];
  t(g.call('tod_haven::waker_for', [L, h0]) === undefined, 'a player far away wakes nothing');
  env.players = [{ ...far, origin: V(C[0] + 400, C[1] + 300, z + 250) }];
  t(g.call('tod_haven::waker_for', [L, h0]) !== undefined, 'a player on the gallery over the hall wakes it');
  env.players = [{ ...far, origin: at(100, -384) }];
  t(g.call('tod_haven::waker_for', [L, h0]) === undefined, 'a player one floor down never wakes it');
  env.players = [{ ...far, origin: at(300), downed: true }];
  t(g.call('tod_haven::waker_for', [L, h0]) === undefined, 'a downed player wakes nothing');
  p.origin = at(300, 10);
  // a FULL PARTY at the wake (THE ROSTER IS THE PARTY: 2d2m), so the count-down below has room to run
  env.players = [p, { ...p, name: 'P2', num: 1 }, { ...p, name: 'P3', num: 2 }, { ...p, name: 'P4', num: 3 }];
  env.spawned.length = 0; env.sounds.length = 0; env.lui.length = 0;
  g.call('tod_haven::wake', [L, h0, p]);
  env.players = [p];
  const wanted = 4 * num('TOD_HAVEN_GUARD_PER_PLAYER');
  t(h0.state === 'fight' && h0.guards_wanted === wanted, `the wake arms the fight for ${wanted} guardians`);
  t(env.spawned.some(e => e.kind === 'script_model') && env.sounds.includes(str('TOD_HAVEN_SND_WAKE')), 'the wake convulses the field: effect + roar');
  t(env.lui.some(e => e.name === 'tod_haven_state' && e.a === num('TOD_HAVEN_BANNER_WAKE') && e.b === 10 && e.c === wanted), 'the wake banner names the floor and the roster');
  t(h0.flash_until > env.now, 'the wake flashes the dome');
  g.call('tod_haven::wake', [L, h0, p]);
  t(h0.guards_wanted === wanted, 'a second wake is a no-op');
  // spawning them, one by one, through the elite modules
  env.freeActors = 1;
  t(g.call('tod_haven::spawn_guard', [L, h0, 'doppelghast']) === undefined && h0.guards_spawned === 0, 'no guardian spawns into a full actor pool (the reserve)');
  env.freeActors = 20;
  const g1 = g.call('tod_haven::spawn_guard', [L, h0, 'doppelghast']);
  t(!!g1 && g1.kind === 'doppelghast' && g1.health === num('TOD_HAVEN_GUARD_DOPPEL_UNITS') * 100, 'a guardian Doppelghast spawns with its own HP');
  t(g1.tod_haven_guard === 0 && g1.tod_hunt_filter === '&guard_target_ok' && !!g1.tod_hunt_home, 'the guardian is stamped: its haven, the hunt filter, its home');
  const spotOk = Math.hypot(g1.origin[0] - C[0], g1.origin[1] - C[1]) < IN && Math.hypot(g1.origin[0] - C[0], g1.origin[1] - C[1]) > 110 && Math.abs(g1.origin[2] - z) < 1;
  t(spotOk, 'it rises INSIDE the field, off the pad, on the hall floor');
  t(Math.hypot(g1.origin[0] - p.origin[0], g1.origin[1] - p.origin[1]) > 150, 'it rises on the far side of the field from the player');
  t(g1.tod_reloc_fn === '&guard_reloc' && typeof g1.tod_haven_spot === 'number', 'the guardian holds a spot of its own and the relocation hook');
  const g2 = g.call('tod_haven::spawn_guard', [L, h0, 'mangler']);
  t(!!g2 && g2.tod_haven_spot !== g1.tod_haven_spot && Math.hypot(g2.origin[0] - g1.origin[0], g2.origin[1] - g1.origin[1]) > 60, 'the next guardian rises on ANOTHER spot (v3 stacked them all on one)');
  t(!!g2 && g2.kind === 'mangler' && g2.health === num('TOD_HAVEN_GUARD_MANGLER_UNITS') * 100 && g2.maxhealth === g2.health, 'a guardian Mangler spawns with its own HP (over the module\'s default)');
  t(h0.guards_spawned === 2 && L.tod_haven_stats.guards === 2, 'the haven counts its guardians');
  // the hunt filter (v4): players INSIDE its field only ("the elites are not allowed to leave the dome")
  t(g.call('tod_haven::guard_target_ok', [g1, { ...p, origin: at(IN - 60), tod_haven: 0 }]) === true, 'the filter admits a player inside the field');
  t(g.call('tod_haven::guard_target_ok', [g1, { ...p, origin: at(OUT + 60), tod_haven: -1 }]) === false, 'the filter refuses a player on the floor but outside the field (it will not come out for them)');
  t(g.call('tod_haven::guard_target_ok', [g1, { ...p, origin: V(C[0] + 380, C[1] + 100, z + 580), tod_haven: -1 }]) === false, 'the filter refuses a player on the galleries over the dome');
  t(g.call('tod_haven::guard_target_ok', [g1, { ...p, origin: at(200, -384), tod_haven: undefined }]) === false, 'the filter refuses a player one floor down');
  t(g.call('tod_haven::guard_target_ok', [g1, { ...p, origin: at(IN - 60), tod_haven: undefined }]) === true, 'a player the tick has not seen yet is placed where they stand');
  t(g.call('tod_haven::guard_target_ok', [{ ...g1, tod_haven_guard: undefined }, { ...p, origin: V(C[0] + 1500, C[1], z) }]) === true, 'an elite that is no guardian passes the filter untouched');
  // THE FENCE: a guardian outside its field is put back on its spot inside
  t(g.call('tod_haven::fence_inside', [L, h0, at(IN - 20)]) === true && g.call('tod_haven::fence_inside', [L, h0, at(OUT + 10)]) === true, 'the fence has slack past the rim (a guardian brushing it is not yanked)');
  t(g.call('tod_haven::fence_inside', [L, h0, at(OUT + 60)]) === false && g.call('tod_haven::fence_inside', [L, h0, at(0, -384)]) === false, 'a guardian well outside its field, or a floor down, is outside the fence');
  const home1 = g1.origin.slice();
  g1.origin = at(OUT + 200);
  env.teleports.length = 0; env.spawned.length = 0;
  g.call('tod_haven::guard_fence_now', [g1, h0]);
  t(env.teleports.length === 1 && Math.hypot(g1.origin[0] - home1[0], g1.origin[1] - home1[1]) < 1 && L.tod_haven_stats.fenced === 1, 'the fence puts it back on its own spot inside');
  const busy = { name: 'ON_SPOT', isPlayer: true, sessionstate: 'playing', origin: V(home1[0] + 20, home1[1], z), alive: true, num: 3 };
  env.players = [p, busy];
  const r1 = g.call('tod_haven::guard_reloc', [g1, p]);
  t(!!r1 && Math.hypot(r1[0] - home1[0], r1[1] - home1[1]) > 60 && HAVEN_LAYOUT.insideBody([r1[0] - C[0] + HAVEN_LAYOUT.C[0], r1[1] - C[1] + HAVEN_LAYOUT.C[1], r1[2] - z], HAVEN_LAYOUT.IN_R3)
    && r1[0] !== g2.origin[0], 'a player on its spot: it relocates to another FREE spot inside the field');
  env.players = [p];
  t(g.call('tod_haven::guard_reloc', [{ ...g1, tod_haven_guard: undefined }, p]) === undefined, 'an elite that is no guardian has no relocation hook answer');
  // the count comes down; the last one cleanses
  for (let i = h0.guards_spawned; i < wanted; i++) g.call('tod_haven::spawn_guard', [L, h0, 'mangler']);
  t(h0.guards_spawned === wanted, 'the whole roster is up');
  env.lui.length = 0; env.sounds.length = 0; env.spawned.length = 0;
  g.call('tod_haven::guard_down', [L, h0, 'doppelghast', 'P1']);
  t(h0.guards_down === 1 && g.call('tod_haven::guards_left', [L, h0]) === wanted - 1 && !h0.safe && !IS_TRUE(h0.cleanse_due), 'the first death counts down and does not cleanse');
  t(env.sounds.includes(str('TOD_HAVEN_SND_GUARD_DOWN')) && env.spawned.some(e => e.kind === 'script_model'), 'a guardian down cracks the dome: effect + sound');
  t(env.lui.some(e => e.name === 'tod_haven_state' && e.a === num('TOD_HAVEN_BANNER_DOWN') && e.c === wanted - 1), 'the GUARDIAN DOWN banner carries the count');
  for (let i = 1; i < wanted - 1; i++) g.call('tod_haven::guard_down', [L, h0, 'mangler', 'P1']);
  t(!IS_TRUE(h0.cleanse_due), 'one guardian left: still corrupted');
  g.call('tod_haven::guard_down', [L, h0, 'mangler', 'P1']);
  t(IS_TRUE(h0.cleanse_due) && h0.guards_down === wanted, 'the last guardian down: the cleanse is due');
  // a haven whose roster could not all be raised: it wants only what it has (the give-up path), then cleanses
  const h2 = H[2];
  h2.state = 'fight'; h2.guards_wanted = 3; h2.guards_spawned = 2;
  g.call('tod_haven::guard_down', [L, h2, 'mangler', 'P1']); g.call('tod_haven::guard_down', [L, h2, 'mangler', 'P1']);
  t(!IS_TRUE(h2.cleanse_due), 'two of three down with one still to raise: not yet');
  h2.guards_wanted = h2.guards_spawned;
  g.call('tod_haven::maybe_cleanse', [L, h2]);
  t(IS_TRUE(h2.cleanse_due), 'once the haven wants only what it raised, the cleanse is due');
  h2.state = 'corrupt'; h2.cleanse_due = false; h2.guards_wanted = 0; h2.guards_spawned = 0; h2.guards_down = 0;

  // ===== THE PURIFICATION (v5): the convulsion -> the collapse -> the bloom =====
  p.origin = at(IN - 40);                                 // standing inside when it happens
  env.players = [p, { name: 'P2', isPlayer: true, sessionstate: 'playing', origin: V(C[0] + 2000, C[1], z), num: 1 }];
  step(at(IN - 40));
  t(p.tod_haven_dark === true, 'standing inside the corrupted field: in the darkness');
  t(p.tod_haven === 0 && p.tod_haven_pay === undefined, 'inside the corrupted field, untaxed');
  zc.origin = at(IN - 20); zc.health = 150; g.call('tod_haven::ai_update', [zc, env.now]);
  const zFar = { is_zombie: true, origin: at(OUT + 300), alive: true, health: 150, num: 330 };                                         // outside: lives
  const zElite = { is_zombie: true, origin: at(IN - 30), alive: true, health: 900, tod_boss_kind: 'mangler', tod_mangler: true, num: 331 };   // an elite inside: spared, then slowed
  const zNew = { is_zombie: true, origin: at(IN - 35), alive: true, health: 150, num: 332 };                                           // inside, never ticked: placed where it stands
  g.call('tod_haven::ai_update', [zElite, env.now]);
  env.ais = [zc, zFar, zElite, zNew];
  h0.dome = { name: 'dome', model: 'tod_haven_dome_dark', shown: true };
  h0.sign = { name: 'sign', shown: true };
  env.lui.length = 0; env.sounds.length = 0; env.spawned.length = 0; env.rates.length = 0; env.loops.length = 0; env.quakes.length = 0; env.loopStops.length = 0;
  // 1. THE CONVULSION
  g.call('tod_haven::cleanse', [L, h0]);
  t(h0.state === 'purge' && h0.safe === false && L.tod_haven_stats.cleansed === 0, 'the last guardian down starts THE PURIFICATION: the field is NOT safe through the convulsion');
  t(h0.barrier.solid === true && blocks(pOut, zIn) === true, 'its barrier still stands through the convulsion');
  t(env.sounds.includes(str('TOD_HAVEN_SND_PURGE')) && env.spawned.some(e => e.kind === 'script_model'), 'the convulsion: the purge sound + its effect at the heart');
  t(env.quakes.length === 1 && env.quakes[0][1] === num('TOD_HAVEN_PURGE_CONVULSE_SECS'), 'the floor quakes for the whole convulsion');
  t(env.loopStops.length === 1 && env.loopStops[0] === num('TOD_HAVEN_PURGE_HUM_FADE'), 'the dark hum fades out under it');
  t(env.lui.some(e => e.name === 'tod_haven_state' && e.a === num('TOD_HAVEN_BANNER_PURGE') && e.b === 10 && e.who === 'P1')
    && !env.lui.some(e => e.name === 'tod_haven_state' && e.a === num('TOD_HAVEN_BANNER_PURGE') && e.who === 'P2'), 'the convulsion banner goes to the players on the floor only');
  t(p.tod_haven_dark === true && p.tod_haven_pay === undefined, 'the darkness holds through the convulsion; still untaxed');
  g.call('tod_haven::cleanse', [L, h0]);
  t(env.quakes.length === 1, 'a second cleanse mid-purge is a no-op');
  env.lui.length = 0;
  g.call('tod_haven::strobe_tell', [L, h0, 3]);
  t(env.lui.length === 1 && env.lui[0].who === 'P1' && env.lui[0].a === num('TOD_HAVEN_BANNER_STROBE') && env.lui[0].c === 3, 'a strobe is told to the players inside only, with its index');
  // 2. THE COLLAPSE
  env.lui.length = 0; env.spawned.length = 0; env.quakes.length = 0;
  g.call('tod_haven::collapse', [L, h0]);
  t(h0.collapsed === true && h0.safe === false && h0.state === 'purge', 'the collapse: still not safe (the void comes first)');
  t(h0.barrier.solid === false && h0.barrier_solid === false, 'the collapse takes the barrier down ("then bullets can shoot through and kill things both ways")');
  t(h0.dome.shown === false && h0.sign.shown === false && h0.vis_hold === true, 'the dome and the sign are gone for the void');
  t(env.quakes.length === 1 && env.spawned.some(e => e.kind === 'script_model'), 'the collapse kicks the floor and plays the implosion');
  t(zc.damaged === 150 + num('TOD_HAVEN_PURGE_KILL_MARGIN') && zNew.damaged === 150 + num('TOD_HAVEN_PURGE_KILL_MARGIN') && zc.alive === false,
    'every ordinary zombie inside dies in the collapse (the stock nuke idiom: health + the margin; ticked or not)');
  t(zFar.damaged === undefined && zElite.damaged === undefined, 'a zombie outside and an elite inside are spared');
  t(zc.exempt_at_hit === true && zc.tod_ps_exempt === undefined && h0.purge_kills === 2 && L.tod_haven_stats.purged === 2, 'the kill intent was exempted from the power scale AT the hit and cleared after; the collapse counts its kills');
  t(env.lui.some(e => e.name === 'tod_haven_state' && e.a === num('TOD_HAVEN_BANNER_COLLAPSE') && e.who === 'P1')
    && !env.lui.some(e => e.name === 'tod_haven_state' && e.a === num('TOD_HAVEN_BANNER_COLLAPSE') && e.who === 'P2'), 'the collapse banner (the void) goes to the floor only');
  g.call('tod_haven::collapse', [L, h0]);
  t(env.quakes.length === 1, 'a second collapse is a no-op');
  // 3. THE BLOOM
  env.lui.length = 0; env.sounds.length = 0; env.spawned.length = 0; env.rates.length = 0; env.loops.length = 0; env.local.length = 0;
  g.call('tod_haven::purify', [L, h0]);
  t(h0.safe === true && h0.state === 'safe' && L.tod_haven_stats.cleansed === 1, 'the bloom: the haven is safe');
  t(blocks(pOut, zIn) === false && blocks(zIn, pOut) === false, 'a safe field refuses nothing');
  t(p.tod_haven_dark === false && env.local.includes('P1:' + str('TOD_HAVEN_SND_DARK_LIFT')), 'the bloom lifts the darkness for the player inside, with the lift cue');
  t(env.sounds.includes(str('TOD_HAVEN_SND_CLEANSE')), 'the bloom chord plays at the heart');
  const secured = env.lui.filter(e => e.name === 'tod_haven_state' && e.a === num('TOD_HAVEN_BANNER_SECURED') && e.b === 10);
  t(secured.length === 2 && secured.find(e => e.who === 'P1').c === 1 && secured.find(e => e.who === 'P2').c === 0, 'FLOOR 10 HAVEN SECURED goes to EVERY player; the one on the floor is told so (the bigger flash)');
  t(env.players.every(q => q.score === num('TOD_HAVEN_CLEANSE_PTS')), 'every player is paid the purse');
  t(p.tod_haven_pay === num('TOD_HAVEN_KILL_PAY') && p.tod_haven_bleed === true && p.n_bleedout_time_multiplier === num('TOD_HAVEN_BLEEDOUT'), 'the player inside becomes a member of a safe field at once: the tax, the bleed grace');
  ev = env.lui.filter(e => e.name === 'tod_haven' && e.who === 'P1').at(-1);
  t(ev && ev.a === 1 && ev.c === num('TOD_HAVEN_STATE_SAFE') && (ev.b & num('TOD_HAVEN_HUD_PULSE')) !== 0, 'the player inside gets the SAFE state with a pulse');
  t(zElite.tod_safe_mult === num('TOD_HAVEN_SLOW') && env.rates.length >= 1 && !!zElite.tod_haven_slow_host, 'the enemy left inside is slowed at once and gets its crackle carrier');
  t(!!h0.fx_host && env.spawned.includes(h0.fx_host), 'the safe ambient replaces the fight\'s loop');
  g.call('tod_haven::purify', [L, h0]);
  g.call('tod_haven::cleanse', [L, h0]);
  t(L.tod_haven_stats.cleansed === 1, 'a second bloom, or a cleanse after it, is a no-op');
  t(g.call('tod_haven::point_inside_live', [L, at(10)]) === true, 'point_inside_live: a safe field is a sanctuary');
  t(g.call('tod_haven::point_locked', [L, at(0, 32)]) === false, 'point_locked: the pad is free once the haven is taken');
  t(seal('enter_lap10') === 0 && seal('enter_lap20') === 1, 'door seal: a taken haven unseals its own way down, and only its own');
  t(g.call('tod_haven::calm_any', [L]) === true, 'calm_any: a player inside a safe field calms the spawn clock');
  p.origin = V(C[0] + 400, C[1], z);
  g.call('tod_haven::player_update', [p, env.now += 100]);
  t(g.call('tod_haven::calm_any', [L]) === false, 'calm_any: a player in the loggia (outside the field) calms nothing');
  env.players = [p];
  // a bloom with no collapse before it (another path) still drops the barrier
  const h1 = H[1];
  h1.state = 'fight';
  g.call('tod_haven::barrier_set', [L, h1, true]);
  g.call('tod_haven::purify', [L, h1]);
  t(h1.safe === true && h1.barrier.solid === false, 'a bloom with no collapse before it still drops the barrier');
  h1.safe = false; h1.state = 'corrupt'; h1.collapsed = false; L.tod_haven_stats.cleansed = 1;
  // the enemy leaves: the slow and its carrier go
  zElite.origin = at(OUT + 40);
  g.call('tod_haven::ai_update', [zElite, env.now]);
  t(zElite.tod_safe_mult === undefined && !zElite.tod_haven_slow_host && h0.slow_fx === 0 && env.deleted.length >= 1, 'an enemy leaving drops the slow and its carrier (the count returns to zero)');
  env.ais = [];

  // --- THE BARRIER'S ANSWER (v4): a ripple + a zap where a shot stops on it, throttled per haven ---
  const h3 = H[3];
  g.call('tod_haven::barrier_set', [L, h3, true]);
  t(g.call('tod_haven::barrier_near', [L, V(C[0] + 500, C[1], h3.z + 40)]) === h3, 'a shooter near a corrupted field is traced');
  t(g.call('tod_haven::barrier_near', [L, V(C[0] + 500, C[1], z + 40)]) === undefined, 'a shooter near a SAFE field is not (its barrier is down)');
  t(g.call('tod_haven::barrier_near', [L, V(C[0] + 2500, C[1], h3.z)]) === undefined, 'a shooter far away is not');
  env.spawned.length = 0; env.sounds.length = 0;
  const hitAt = V(C[0] + 300, C[1], h3.z + 60);
  g.call('tod_haven::deflect_feedback', [L, h3, hitAt, p]);
  const ripples = () => env.spawned.filter(e => e.kind === 'script_model').length;
  t(ripples() === 1 && env.sounds.includes(str('TOD_HAVEN_SND_DEFLECT')), 'a shot that stops on the barrier: the crimson ripple + the zap');
  g.call('tod_haven::deflect_feedback', [L, h3, hitAt, p]);
  t(ripples() === 1, 'a second shot inside the gap sparks no new ripple (a full-auto burst is not 10 effects a second)');
  env.now += num('TOD_HAVEN_DEFLECT_GAP_MS');
  g.call('tod_haven::deflect_feedback', [L, h3, hitAt, p]);
  t(ripples() === 2 && L.tod_haven_stats.deflects === 3, 'after the gap it answers again; every shot is counted');
  g.call('tod_haven::barrier_set', [L, h3, false]);

  // --- the field's surface point ---
  const fp = g.call('tod_haven::field_point', [L, h0, at(500, 0), 48]);
  const fr = Math.hypot(fp[0] - C[0], fp[1] - C[1], fp[2] - (z + HAVEN_LAYOUT.DOME_C));
  t(Math.abs(fr - HAVEN_LAYOUT.DOME_S) < 0.01 && fp[0] > C[0] && Math.abs(fp[2] - (z + 48)) < 1e-6, 'field_point sits on the sphere, toward the body, at the asked height');

  // --- the damage cut (safe) ---
  p.tod_haven = -1;
  t(g.call('tod_haven::dr_for', [L, p]) === 1, 'dr_for: outside = full damage');
  p.tod_haven = 0;
  env.lui.length = 0; env.sounds.length = 0;
  t(g.call('tod_haven::dr_for', [L, p]) === num('TOD_HAVEN_DR'), 'dr_for: inside a live safe haven = TOD_HAVEN_DR');
  t(env.lui.length === 1 && env.lui[0].name === 'tod_haven_hit' && env.sounds.includes('2p:' + str('TOD_HAVEN_SND_ABSORB')), 'a hit inside flickers the screen + plays the tink');
  env.now += 100; g.call('tod_haven::dr_for', [L, p]);
  t(env.lui.length === 1, 'a second hit inside the gap does not re-flicker (throttled)');
  env.now += num('TOD_HAVEN_HIT_GAP_MS'); g.call('tod_haven::dr_for', [L, p]);
  t(env.lui.length === 2, 'a hit after the gap flickers again');
  h0.live = false;
  t(g.call('tod_haven::dr_for', [L, p]) === 1, 'dr_for: a haven that is not live cuts nothing');
  h0.live = true;
  p.tod_haven = undefined;
  // the player left during the cleanse checks above: release its bleed grace cleanly
  p.tod_haven_bleed = false; p.n_bleedout_time_multiplier = undefined; p.tod_haven_bleed_prev = undefined;

  // --- the crossing flow (player_update, the shipping code; the haven is SAFE) ---
  env.lui.length = 0; env.sounds.length = 0; env.spawned.length = 0;
  p.tod_haven_entries = 0;
  step(at(OUT + 200));                                    // first sight, outside
  t(env.lui.length === 0 || (lastLui().a === 0), 'first sight outside: nothing (or a silent outside state)');
  env.lui.length = 0;
  step(at(OUT + 80)); step(at(IN + 4));                   // approaching, still out (hysteresis)
  t(p.tod_haven === -1 && env.lui.filter(e => e.a === 1).length === 0, 'approaching the ring is still outside');
  step(at(IN - 30));                                      // walk in
  ev = lastLui();
  t(p.tod_haven === 0 && ev && ev.name === 'tod_haven' && ev.a === 1 && ev.b === (num('TOD_HAVEN_HUD_PULSE') + num('TOD_HAVEN_HUD_HINT')) && ev.c === num('TOD_HAVEN_STATE_SAFE'), 'walking in: HUD inside + pulse + the hint line (first entry) + the SAFE state');
  t(env.sounds.includes(str('TOD_HAVEN_SND_ENTER')), 'walking in plays the enter sound at the field');
  t(env.spawned.some(e => e.kind === 'script_model'), 'walking in spawns the crossing ripple carrier');
  t(p.tod_haven_pay === num('TOD_HAVEN_KILL_PAY'), 'walking in: kills pay the quarter from now on');
  t(p.tod_haven_bleed === true && p.n_bleedout_time_multiplier === num('TOD_HAVEN_BLEEDOUT'), 'walking in: the bleed-out grace (x1.5 from stock\'s own)');
  t(h0.flash_until > env.now, 'walking in flashes the dome');
  const sent = env.lui.length;
  step(at(IN - 20)); step(at(IN - 10));
  t(env.lui.length === sent, 'standing inside sends nothing new inside the re-send window');
  step(at(IN - 10), num('TOD_HAVEN_HUD_RESEND_MS') + 10);
  ev = lastLui();
  t(env.lui.length === sent + 1 && ev.a === 1 && ev.b === 0 && ev.c === num('TOD_HAVEN_STATE_SAFE'), 'the re-send repeats the state with NO pulse flag');
  step(at(IN + 6));                                       // between in and out: still in
  t(p.tod_haven === 0, 'stepping onto the ring from inside keeps you in');
  env.sounds.length = 0;
  step(at(OUT + 30));                                     // walk out
  ev = lastLui();
  t(p.tod_haven === -1 && ev.a === 0 && ev.b === num('TOD_HAVEN_HUD_PULSE'), 'walking out: HUD outside + one pulse');
  t(env.sounds.includes(str('TOD_HAVEN_SND_EXIT')), 'walking out plays the exit sound');
  t(p.tod_haven_pay === undefined, 'walking out: full kill money again');
  t(p.tod_haven_bleed === false && p.n_bleedout_time_multiplier === undefined, 'walking out: stock\'s bleed-out again');
  // entries two and three still carry the hint; the fourth does not
  for (let k = 2; k <= 4; k++) {
    step(at(OUT + 200), 3000); step(at(IN - 40));
    ev = env.lui.filter(e => e.a === 1).at(-1);
    const hint = (ev.b & num('TOD_HAVEN_HUD_HINT')) !== 0;
    t(hint === (k <= num('TOD_HAVEN_HINT_ENTRIES')), `entry ${k}: the hint line ${k <= num('TOD_HAVEN_HINT_ENTRIES') ? 'shows' : 'is gone'}`);
  }
  // a teleport out: no ripple, a silent drain
  env.sounds.length = 0;
  step(at(2000), 100);
  ev = lastLui();
  t(p.tod_haven === -1 && ev.a === 0 && ev.b === 0 && !env.sounds.includes(str('TOD_HAVEN_SND_EXIT')), 'a teleport out: silent drain, no exit sound');
  // death inside: the state drains silently
  step(at(IN - 40), 3000);
  p.sessionstate = 'dead';
  env.sounds.length = 0;
  step(at(IN - 40));
  ev = lastLui();
  t(p.tod_haven === -1 && ev.a === 0 && ev.b === 0 && env.sounds.length === 0, 'dying inside: out, silently');
  t(p.tod_haven_pay === undefined, 'dying inside clears the kill pay');
  p.sessionstate = 'playing';

  // --- THE BLEED GRACE held through a down ---
  step(at(OUT + 200), 3000); step(at(IN - 40));
  t(p.n_bleedout_time_multiplier === num('TOD_HAVEN_BLEEDOUT'), 'inside: the grace');
  p.downed = true;
  g.call('tod_haven::bleed_set', [p, false]);             // the membership would drain mid-down (a death's spectator state)
  t(p.n_bleedout_time_multiplier === num('TOD_HAVEN_BLEEDOUT') && p.tod_haven_bleed === true, 'a downed player keeps the grace when the field lets go (stock would cut the bleed-out to 2 s)');
  p.downed = false;
  p.tod_haven = -1;
  g.call('tod_haven::bleed_release_check', [p]);
  t(p.n_bleedout_time_multiplier === undefined && p.tod_haven_bleed === false, 'up again and outside: stock\'s bleed-out returns');
  p.tod_haven = 0; p.tod_haven_bleed = false;
  g.call('tod_haven::bleed_set', [p, true]);
  p.n_bleedout_time_multiplier = 2.0; p.tod_haven_bleed = false;
  g.call('tod_haven::bleed_set', [p, true]);
  t(Math.abs(p.n_bleedout_time_multiplier - 2.0 * num('TOD_HAVEN_BLEEDOUT')) < 1e-9, 'the grace multiplies a multiplier someone else set (never overwrites it)');
  g.call('tod_haven::bleed_set', [p, false]);
  t(p.n_bleedout_time_multiplier === 2.0, 'and gives it back untouched');
  p.n_bleedout_time_multiplier = undefined;
  step(at(OUT + 300));

  // --- THE KILL PAY: a quarter, banked to exact tens; the popup preview never lies ---
  const q = { name: 'Q', isPlayer: true };
  t(g.call('tod_haven::kill_pay', [L, q, 60]) === 60 && q.tod_haven_bank === undefined, 'kill_pay outside a field: the kill pays in full, nothing banked');
  t(g.call('tod_haven::kill_preview', [L, q, 60]) === 60, 'kill_preview outside a field: in full');
  q.tod_haven_pay = num('TOD_HAVEN_KILL_PAY');
  const kills = [60, 100, 120, 60, 80, 60, 100, 500, 60, 120, 80, 60, 100, 20, 60, 1300];
  let nominal = 0, paid = 0, previewOk = true, tens = true;
  for (let r = 0; r < 20; r++) for (const k of kills) {
    const pv = g.call('tod_haven::kill_preview', [L, q, k]);
    const pay = g.call('tod_haven::kill_pay', [L, q, k]);
    if (pv !== pay) previewOk = false;
    if (pay % 10 !== 0) tens = false;
    nominal += k; paid += pay;
  }
  t(previewOk, 'the popup preview equals the pay, kill after kill');
  t(tens, 'every kill pays whole tens (stock\'s round-up adds nothing)');
  t(paid <= nominal * num('TOD_HAVEN_KILL_PAY') && paid > nominal * num('TOD_HAVEN_KILL_PAY') - 10, `over a stay the kills pay exactly a quarter (${paid} of ${nominal})`);
  t(g.call('tod_haven::kill_pay', [L, q, 0]) === 0, 'a worthless kill pays nothing');
  t(L.tod_haven_stats['kills'] === 20 * kills.length && L.tod_haven_stats['paid'] === paid, 'the STATS counters see every kill and what it paid');

  // --- the AI edge (safe) ---
  const zom = { is_zombie: true, origin: at(OUT + 100), alive: true, num: 301 };
  env.ais = [zom];
  env.rates.length = 0;
  g.call('tod_haven::ai_update', [zom, env.now]);
  t(zom.tod_safe_mult === undefined && env.rates.length === 0, 'a zombie outside: no slow, no write');
  zom.origin = at(IN - 20); env.sounds.length = 0; env.spawned.length = 0;
  env.now += 1000;
  g.call('tod_haven::ai_update', [zom, env.now]);
  t(zom.tod_safe_mult === num('TOD_HAVEN_SLOW'), 'a zombie entering is stamped with the slow');
  t(env.rates.length === 1 && Math.abs(zom.rate - 1.2 * num('TOD_HAVEN_SLOW')) < 1e-9, 'its rate is re-applied AT ONCE with the slow folded in');
  t(env.spawned.filter(e => e.kind === 'script_model' && !e.linked).length === 1 && env.sounds.includes(str('TOD_HAVEN_SND_PUSH')), 'forcing in: the push-through sparks + crackle');
  t(!!zom.tod_haven_slow_host && zom.tod_haven_slow_host.linked === zom && h0.slow_fx === 1, 'THE SLOW IS VISIBLE: a carrier linked to the zombie plays the crackle');
  const z2 = { is_zombie: true, origin: at(IN - 25), alive: true, num: 302 };
  env.spawned.length = 0;
  g.call('tod_haven::ai_update', [z2, env.now + 10]);
  t(z2.tod_safe_mult === num('TOD_HAVEN_SLOW') && env.spawned.filter(e => e.kind === 'script_model' && !e.linked).length === 0, 'a second zombie inside the push gap is slowed but sparks no new effect');
  t(!!z2.tod_haven_slow_host && h0.slow_fx === 2, 'it still gets its own crackle carrier');
  const riser = { is_zombie: true, origin: at(IN - 50), in_the_ground: true, alive: true, num: 303 };
  env.spawned.length = 0; env.now += 2000;
  g.call('tod_haven::ai_update', [riser, env.now]);
  t(riser.tod_safe_mult === num('TOD_HAVEN_SLOW') && env.spawned.filter(e => !e.linked).length === 0, 'a riser climbing out inside is slowed with no push effect');
  env.rates.length = 0;
  g.call('tod_haven::ai_update', [zom, env.now]);
  t(env.rates.length === 0, 'a zombie staying inside is not re-written every tick');
  // the carrier cap: a horde inside gets at most TOD_HAVEN_SLOW_FX_MAX carriers
  const horde = [];
  for (let i = 0; i < num('TOD_HAVEN_SLOW_FX_MAX') + 4; i++) {
    const zz = { is_zombie: true, origin: at(IN - 60 - i), alive: true, num: 400 + i };
    g.call('tod_haven::ai_update', [zz, env.now]);
    horde.push(zz);
  }
  t(h0.slow_fx === num('TOD_HAVEN_SLOW_FX_MAX') && horde.filter(zz => !!zz.tod_haven_slow_host).length === num('TOD_HAVEN_SLOW_FX_MAX') - 3 && L.tod_haven_stats.slowfx_dropped > 0, `the carriers cap at ${D.TOD_HAVEN_SLOW_FX_MAX} per field; the rest are slowed without one`);
  t(horde.every(zz => zz.tod_safe_mult === num('TOD_HAVEN_SLOW')), 'every zombie of the horde is slowed, carrier or not');
  zom.origin = at(OUT + 40);
  g.call('tod_haven::ai_update', [zom, env.now]);
  t(zom.tod_safe_mult === undefined && Math.abs(zom.rate - 1.2) < 1e-9 && !zom.tod_haven_slow_host && h0.slow_fx === num('TOD_HAVEN_SLOW_FX_MAX') - 1, 'a zombie leaving drops the slow, runs at full rate at once and frees its carrier');
  // an elite: re-asserted every tick inside, never while another system owns its rate
  const el = { is_zombie: false, origin: at(IN - 30), tod_elite_base_rate: 1.0, alive: true, num: 310 };
  g.call('tod_haven::ai_update', [el, env.now]);
  t(Math.abs(el.rate - num('TOD_HAVEN_SLOW')) < 1e-9, 'an elite entering runs at base x the slow');
  el.rate = 1.0;     // another writer stomps it (a bamf end, the drop reveal)
  g.call('tod_haven::ai_update', [el, env.now]);
  t(Math.abs(el.rate - num('TOD_HAVEN_SLOW')) < 1e-9, 'an elite inside gets the slow re-asserted on the next tick');
  env.paused = true; el.rate = 0.05;
  g.call('tod_haven::ai_update', [el, env.now]);
  t(el.rate === 0.05, 'never during a world pause (the freeze owns the rate)');
  env.paused = false;
  out.n = n;
  return out;
}

// =============================================================================
section('E. BEHAVIOUR (the shipping module)');
let base;
try { base = suite(HAVEN); } catch (e) { base = ['the suite threw: ' + (e.stack || e).toString().split('\n').slice(0, 3).join(' | ')]; }
for (const f of base) check(false, f);
checks += Math.max(0, (base.n || 0) - base.length);
if (process.env.TOD_HAVEN_VERBOSE) console.log(`   behaviour checks run: ${base.n}`);

// =============================================================================
section('F. NEGATIVE CONTROLS');
const MUTANTS = [
  ['no hysteresis (one radius both ways)', s => s.replace('r2 = ( ( cur == h.index ) ? level.tod_haven_out_r2 : level.tod_haven_in_r2 );', 'r2 = level.tod_haven_in_r2;')],
  ['the cut ignores whether the field is live', s => s.replace('if ( !isdefined( h ) || !h.live || !h.safe )\n\t\treturn 1.0;', 'if ( !isdefined( h ) || !h.safe )\n\t\treturn 1.0;')],
  ['the cut ignores whether the field is SAFE', s => s.replace('if ( !isdefined( h ) || !h.live || !h.safe )\n\t\treturn 1.0;', 'if ( !isdefined( h ) || !h.live )\n\t\treturn 1.0;')],
  ['the re-send pulses again', s => s.replace('self hud_send( ( idx >= 0 ), 0 );', 'self hud_send( ( idx >= 0 ), TOD_HAVEN_HUD_PULSE );')],
  ['the slow never comes off', s => s.replace(/else\s*self\.tod_safe_mult = undefined;/, '')],
  ['a corrupted field slows too', s => s.replace('safe = ( idx >= 0 && level.tod_havens[ idx ].safe );', 'safe = ( idx >= 0 );')],
  ['the hit tell is unthrottled', s => s.replace('if ( !isdefined( player.tod_haven_hit_next ) || now >= player.tod_haven_hit_next )', 'if ( true )')],
  ['a teleport out still flashes', s => s.replace('( ( teleported || self.sessionstate !== "playing" || !was_safe ) ? 0 : TOD_HAVEN_HUD_PULSE )', 'TOD_HAVEN_HUD_PULSE')],
  ['the z band ignored', s => s.replace('if ( o[ 2 ] < h.z - level.tod_haven_z_below || o[ 2 ] > h.z + level.tod_haven_z_above )\n\t\t\tcontinue;\n\t\tr2', 'if ( false )\n\t\t\tcontinue;\n\t\tr2')],
  ['membership is flat (a cylinder, not the sphere)', s => s.replace('if ( DistanceSquared( o + ( 0, 0, level.tod_haven_body_up ), h.sphere ) <= r2 )', 'if ( Distance2DSquared( o, h.center ) <= r2 )')],
  ['the elite re-assert fights the pause', s => s.replace(/if \( self tod_zombie_speed::elite_rate_owned\(\) \)\s*return;/, '')],
  ['the hint forever', s => s.replace('if ( self.tod_haven_entries <= TOD_HAVEN_HINT_ENTRIES )', 'if ( true )')],
  ['the edge never re-applies the rate', s => s.replace(/self\.tod_safe_mult = undefined;\s*self apply_rate\(\);/, 'self.tod_safe_mult = undefined;')],
  ['the kill pay never set on the way in', s => s.replace(/\tself\.tod_haven_pay = TOD_HAVEN_KILL_PAY;[^\n]*\n/, '')],
  ['the kill pay set in a CORRUPTED field too', s => s.replace('if ( !h.safe )\n\t{\n\t\tself.tod_haven_pay = undefined;', 'if ( !h.safe )\n\t{\n\t\tself.tod_haven_pay = TOD_HAVEN_KILL_PAY;')],
  ['the kill pay never cleared on the way out', s => s.replace(/\tself\.tod_haven_pay = undefined;   \/\/ full kill money[^\n]*\n/, '')],
  ['a flat quarter rounded up (no bank)', s => s.replace('player.tod_haven_bank += points * player.tod_haven_pay;\n\tpay = int( player.tod_haven_bank / 10 ) * 10;\n\tplayer.tod_haven_bank -= pay;', 'pay = int( ( points * player.tod_haven_pay + 9.99 ) / 10 ) * 10;')],
  ['the popup preview ignores the bank', s => s.replace('return int( ( bank + points * player.tod_haven_pay ) / 10 ) * 10;', 'return int( ( points * player.tod_haven_pay ) / 10 ) * 10;')],
  ['the sanctuary test ignores SAFE (the horde rises in a safe field)', s => s.replace('return level.tod_havens[ idx ].safe;', 'return true;')],
  ['the pad lock ignores SAFE (the pad stays dead)', s => s.replace('return !level.tod_havens[ j ].safe;', 'return true;')],
  ['the calm ignores SAFE', s => s.replace('if ( isdefined( h ) && h.safe )\n\t\t\treturn true;', 'if ( isdefined( h ) )\n\t\t\treturn true;')],
  ['the door seal ignores SAFE (the way down never opens)', s => s.replace('if ( h.safe )\n\t\t\treturn 0;\n\t\tif ( h.live', 'if ( h.live')],
  ['a dark haven seals its door (a pre-power descent strands the party)', s => s.replace('if ( h.live || IS_TRUE( h.booting ) )\n\t\t\treturn 1;\n\t\treturn 0;', 'return 1;')],
  ['the first guardian down cleanses', s => s.replace('if ( h.guards_down < h.guards_wanted )\n\t\treturn;\n\th.cleanse_due = true;', 'h.cleanse_due = true;')],
  ['the cleanse leaves the enemies inside at full speed', s => s.replace('ai.tod_safe_mult = TOD_HAVEN_SLOW;\n\t\tai apply_rate();', '')],
  ['the cleanse pays nobody', s => s.replace('p zm_score::add_to_player_score( TOD_HAVEN_CLEANSE_PTS );', '')],
  ['the bleed grace never restored', s => s.replace('self.n_bleedout_time_multiplier = self.tod_haven_bleed_prev;', '')],
  ['the bleed grace cut mid-down', s => s.replace(/if \( self laststand::player_is_in_laststand\(\) \)\s*\{\s*if \( !IS_TRUE\( self\.tod_haven_bleed_hold \) \)\s*self thread bleed_release_after_down\(\);\s*return;\s*\}/, '')],
  ['guardians hunt players outside their field', s => s.replace('return ( p.tod_haven == h.index );', 'return true;')],
  ['every guardian rises on one spot (v3)', s => s.replace('if ( pass == 0 && spot_taken( h, i, me ) )', 'if ( false )')],
  ['the fence puts a guardian anywhere but its spot', s => s.replace('to = self guard_home( h );', 'to = self.origin;')],
  ['the relocation ignores the field', s => s.replace('org = self guard_home( h );\n\tdev_log( "GUARD_RELOC', 'org = undefined;\n\tdev_log( "GUARD_RELOC')],
  ['the barrier never goes down at the cleanse', s => s.replace('barrier_set( h, false );   // v4', '// barrier_set( h, false );   // v4')],
  ['the barrier refuses nothing', s => s.replace('if ( a >= 0 && level.tod_havens[ a ].live && !level.tod_havens[ a ].safe )\n\t\treturn true;\n\tif ( v >= 0 && level.tod_havens[ v ].live && !level.tod_havens[ v ].safe )\n\t\treturn true;', '')],
  ['the barrier refuses across a SAFE field too', s => s.replace('if ( a >= 0 && level.tod_havens[ a ].live && !level.tod_havens[ a ].safe )', 'if ( a >= 0 && level.tod_havens[ a ].live )')],
  ['a guardian at the rim is untouchable (not its own field)', s => s.replace('if ( isdefined( ent.tod_haven_guard ) )\n\t\treturn ent.tod_haven_guard;', '')],
  ['the actor gate lets a refused hit through', s => s.replace('dev_log( "BLOCK victim=" + self GetEntityNumber() + " attacker=" + eAttacker GetEntityNumber() + " dmg=" + iDamage + " mod=" + sMeansOfDeath + " n=" + level.tod_haven_stats[ "blocked" ] );\n\t\treturn;', 'dev_log( "BLOCK" );')],
  ['the darkness never takes you', s => s.replace('self dark_set( true );   // v4', '// self dark_set( true );   // v4')],
  ['the darkness never lifts on the way out', s => s.replace('self dark_set( false );           // v4', '// self dark_set( false );           // v4')],
  ['the barrier answers every shot (no throttle)', s => s.replace('if ( now < h.deflect_next )\n\t\treturn;', '')],
  ['guardians spawn into a full actor pool', s => s.replace('if ( GetFreeActorCount() < TOD_HAVEN_GUARD_ACTOR_RESERVE )', 'if ( false )')],
  ['the slow carriers never cap', s => s.replace('if ( h.slow_fx >= TOD_HAVEN_SLOW_FX_MAX )', 'if ( false )')],
  ['a leaving zombie keeps its carrier', s => s.replace('\telse\n\t\tself slow_fx_stop();', '')],
  // v5 THE PURIFICATION
  ['the cleanse is safe at once (no convulsion)', s => s.replace('h.state = "purge";\n\th.purge_ms = GetTime();', 'h.state = "purge";\n\th.purge_ms = GetTime();\n\tpurify( h );')],
  ['the collapse kills nothing', s => s.replace('ai DoDamage( ai.health + TOD_HAVEN_PURGE_KILL_MARGIN, ai.origin );', ';')],
  ['the collapse kills the zombies outside too', s => s.replace('if ( idx != h.index )\n\t\t\tcontinue;\n\t\tai.tod_ps_exempt = true;', 'ai.tod_ps_exempt = true;')],
  ['the collapse kills the elites inside too', s => s.replace('if ( isdefined( ai.tod_boss_kind ) || isdefined( ai.tod_haven_guard ) || IS_TRUE( ai.tod_doppelghast ) || IS_TRUE( ai.tod_mangler ) )\n\t\t\tcontinue;\n', '')],
  ['the kill intent is not exempted from the power scale', s => s.replace('ai.tod_ps_exempt = true;\n\t\tai DoDamage', 'ai DoDamage')],
  ['the collapse leaves the dome up through the void', s => s.replace('h.dome Hide();   // gone for the void; the bloom inflates it back (dome_inflate)', ';')],
  ['the SECURED banner never says who is on the floor', s => s.replace('arg = ( ( near ) ? 1 : 0 );', 'arg = 0;')],
  ['the convulsion banner goes to everyone', s => s.replace('if ( kind != TOD_HAVEN_BANNER_SECURED && TOD_HAVEN_STATE_BAND && !near )', 'if ( false )')],
  ['the strobe is told to everyone', s => s.replace('if ( isdefined( p ) && isdefined( p.tod_haven ) && p.tod_haven == h.index )\n\t\t\tp LuiNotifyEvent( &"tod_haven_state", 3, TOD_HAVEN_BANNER_STROBE', 'if ( isdefined( p ) )\n\t\t\tp LuiNotifyEvent( &"tod_haven_state", 3, TOD_HAVEN_BANNER_STROBE')],
  ['the dark hum never fades at the convulsion', s => s.replace('h.dome StopLoopSound( TOD_HAVEN_PURGE_HUM_FADE );', ';')],
  ['the darkness lifts without its cue', s => s.replace('self PlayLocalSound( TOD_HAVEN_SND_DARK_LIFT );', ';')],
  ['the collapse happens twice', s => s.replace('if ( h.safe || IS_TRUE( h.collapsed ) )\n\t\treturn;\n\th.collapsed = true;', 'h.collapsed = true;')],
];
for (const [name, mutate] of MUTANTS) {
  const m = mutate(HAVEN);
  if (m === HAVEN) { check(false, `negative control "${name}" did not apply (its pattern moved — update the mutant)`); continue; }
  let res;
  try { res = suite(m); } catch (e) { res = ['threw']; }
  check(res.length > 0, `negative control "${name}" is caught`);
  if (process.env.TOD_HAVEN_VERBOSE) console.log(`   mutant "${name}" -> ${res[0]}`);
}

console.log(fails ? `HAVEN GATE FAILED: ${fails} of ${checks} checks` : `HAVEN GATE OK: ${checks} checks, ${MUTANTS.length} mutants caught`);
process.exit(fails ? 1 : 0);
