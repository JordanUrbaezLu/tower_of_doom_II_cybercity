#!/usr/bin/env node
// =============================================================================
// gen_tod_door_materials.js — THE MATTE DOOR MATERIALS (v18.99g, 2026-09-13)
//
// User, on a screenshot of the base arena: "ALso fix this door. It has a
// reflection bug." The buyable door slab was rendering as a smeared mirror with
// the neon skyline in it.
//
// IT IS NOT TRANSPARENT AND IT IS NOT A LIGHTING BUG. Measured out of
// <modtools>/source_data/_emox/emox_mwiii_vertigo_assets.gdt: every one of the
// pack's 30 materials — the ENTIRE world kit, floors, walls, treads and door
// slabs alike — is configured as a polished flat mirror:
//
//     colorMap            $white_diffuse      pure-white albedo
//     specColorMap        $white_specular     full-white specular
//     specAmount          1                   at full strength
//     specColorStrength   100
//     cosinePowerMap      i_..._g             a gloss map measured 97% WHITE,
//                                             i.e. gloss pinned at maximum
//     glossRangeMax       16
//     reflectionProbeAmount 1                 full environment reflection
//     envMapMin/Max/Exponent  1 / 1 / 1       flat, NO fresnel falloff
//     normalMap           ""                  NO normal map at all
//     transparent         0                   (so: not see-through — a mirror)
//
// White albedo + max gloss + no normal map + full probe = a perfectly flat
// mirror plane with zero surface breakup, which is exactly the recipe for an
// undistorted, smeared environment reflection on a big flat brush face.
//
// WHY THE DOOR SHOWS IT WORST, of all the surfaces that share this: the door
// slab is `<hue>_tinted_edge`, the DIMMEST rung of the pack's brightness ladder
// (scaleRGB 5, against the arena wall's 15), and it is the FILLED tile texture
// with no grid lines to break a reflection up. A constant-strength reflection
// laid over the dimmest, flattest, largest surface in the room wins.
//
// THE FIX, and why it is a NEW material rather than an edit to the pack: the
// vertigo GDT is a SHARED tools-root file (memory shared-gdt-crosses-maps) and
// `_tinted_edge` is also every landing, breather floor, the terrace, the
// causeway deck and the extraction pad. Editing it in place would take the
// reflections off half the map's FLOORS as a side effect of fixing a door. So
// this clones the five DISTRICT hues into our own source_data/tod_materials.gdt
// as `tod_door_<hue>` — byte-identical to their donors except the name and a
// zeroed specular/reflection block — and only the DOOR SLAB emission sites in
// gen_tower_map.js point at them. Everything else keeps the look it shipped.
//
// ⚠️ A MATERIAL NAME NOTHING DECLARES IS SUBSTITUTED **SILENTLY** by the linker
// (memory vertigo-pack-is-two-textures). The proof a new one converted is its
// ABSENCE from the linker's known-waived warning list in a run whose waived
// count is unchanged — 10 as of this build. tod_hall_* (v17.86) is the
// precedent that this lane works.
//
// ALSO FOUND AND NOT FIXED HERE — THE PROBE BOXES ARE A SEPARATE, MAP-WIDE BUG.
// gen_tower_map.js's probe() emits every one of the map's 46 reflection probes
// with Radiant's DEFAULT parallax box, `size_min`/`size_max` "72 72 72", i.e. a
// 144-unit cube — inside a 1,120-unit arena and a 1,536-unit crown hall. Map 1
// is the counter-example and its generator comment says so out loud: "GROW the
// box to each zone's extent"; its probes carry real room-sized boxes
// (size_max "712.25 544.75 198.25" / size_min "634.5 548.5 73.25") and no
// `radius` key at all. A parallax box that small projects the cubemap onto a
// tiny volume next to the camera, which is what makes the reflection SMEAR
// rather than sit on the geometry. Fixing it changes reflections across the
// whole map and needs a fresh LED bake, so it is the user's call, not a
// side effect of a door fix.
//
// Usage:  node tools/gen_tod_door_materials.js         (rewrites the block)
//         node tools/gen_tod_door_materials.js --check (verifies, exits 1 on drift)
// =============================================================================
'use strict';
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const OUT = path.join(REPO, 'source_data', 'tod_materials.gdt');

// The mod tools root, detected exactly the way build_map.ps1 does.
function modTools() {
  const guesses = [
    'C:/BO3Tools/TOD2Cybercity',
  ];
  for (const g of guesses) if (fs.existsSync(path.join(g, 'bin', 'modlauncher.exe'))) return g;
  throw new Error('mod tools root not found (looked for bin/modlauncher.exe)');
}

const DONOR_GDT = path.join(modTools(), 'source_data', '_emox', 'emox_mwiii_vertigo_assets.gdt');

// The five DISTRICT hues, LOCKSTEP with DISTRICTS in gen_tower_map.js. A sixth
// name here with no district is dead weight; a missing one is a white square.
const HUES = ['blue', 'green', 'orange', 'yellow', 'red'];

// THE WHOLE POINT OF THE FILE. Every other field is copied verbatim from the
// donor so the door keeps its exact colour, texture and emissive brightness —
// only its response to the environment changes.
const MATTE = {
  specAmount: '0',
  specColorStrength: '0',
  specColorTint: '0 0 0 1',
  specColorTint1: '0 0 0 1',
  specColorTint2: '0 0 0 1',
  specColorTint3: '0 0 0 1',
  reflectionProbeAmount: '0',
  envMapMin: '0',
  envMapMax: '0',
  glossRangeMax: '0',
  glossRangeMin: '0',
};

// THE DARK HALL (2026-09-24, docs/164 — user: "near-black, pools of light",
// "keep edge lines only", "crown hall first"). A SECOND FAMILY from the same
// tool: six clones of the PLAIN grid materials — black tiles with one thin
// glowing line per tile edge, the pack's own "edge lines only" texture — with
//   * the mirror zeroed (MATTE, exactly as the doors),
//   * the emissive line at the Materials doc's 2^EV value for this map's
//     exposure clamp (EV 3 -> scaleRGB 8; the donor's 15 "runs hot", docs/162
//     03 §3.2), one stop under the donor,
//   * the albedo halved (colorTint 0.5) so a light pool reads as light on a
//     dark surface, not as white glare on a $white_diffuse face.
// `floor` and `step` are DECK in lint_tod_geometry.js (things you stand on);
// the rest are BLOCK. Used ONLY inside the crown hall (gen_tower_map.js
// MAT.hall*, behind DARK_HALL); the circlet outside keeps its gold. Byte-
// identical clones under two names (step/gold both from `yellow`) are
// deliberate: the lint classes by NAME, and a floor and a pier must not share
// one. Every knob is one line here; a re-run rewrites the GDT block.
const DARK = [
  ['floor', 'dark_blue'],   // the hall floor                                   DECK
  ['step',  'yellow'],      // sanctuary tiers + the uplink dais (floors)       DECK
  ['wall',  'purple'],      // the velvet walls, corners, gate lintel           BLOCK
  ['gold',  'yellow'],      // piers, arcade, cornice, posts, frames, canopies  BLOCK
  ['ruby',  'red'],         // pier shafts                                      BLOCK
  ['brass', 'orange'],      // reredos field + upper panels                     BLOCK
];
const DARK_FIELDS = { ...MATTE, scaleRGB: '8.0', colorTint: '0.5 0.5 0.5 1' };
const DARK_NAMES = DARK.map(([k]) => `tod_dark_${k}`);

// THE BLACKOUT (2026-09-25, user: "the map should be dark ... really dark ...
// the only thing that you can see pretty well is maybe the sky, and then once
// power's on things will light up"; asked, they chose "remove the glow
// everywhere"). A THIRD FAMILY: one clone per vertigo material the map uses,
// `tod_black_<suffix>`, with the emission OFF (scaleRGB 0 — the glowing grid
// cannot switch with the power, so it goes), the mirror zeroed (MATTE), and the
// albedo set to the donor's own line hue x BLACK.albedo so a powered light
// pool reads as coloured light on a dark surface. The list is SHARED with the
// generator and the geometry lint through tools/tod_black_materials.json.
const BLACK = JSON.parse(fs.readFileSync(path.join(__dirname, 'tod_black_materials.json'), 'utf8'));
function blackTint(body, suffix) {
  const m = body.match(/"colorTint1"\s+"([^"]*)"/);
  if (!m) throw new Error(`donor has no colorTint1: ${suffix}`);
  const c = m[1].trim().split(/\s+/).map(Number);
  const k = BLACK.albedo;
  return `${(c[0] * k).toFixed(4)} ${(c[1] * k).toFixed(4)} ${(c[2] * k).toFixed(4)} 1`;
}

function donorBlock(name) {
  const src = fs.readFileSync(DONOR_GDT, 'utf8');
  const head = `\t"${name}" ( "material.gdf" )`;
  const i = src.indexOf(head);
  if (i < 0) throw new Error(`donor material not found: ${name}`);
  const open = src.indexOf('{', i + head.length);
  if (open < 0) throw new Error(`donor block malformed: ${name}`);
  // The blocks are flat (one level of braces), so the first closing brace at
  // the block's own indent ends it. Scan with a depth counter anyway.
  let depth = 0, end = -1;
  for (let k = open; k < src.length; k++) {
    if (src[k] === '{') depth++;
    else if (src[k] === '}') { depth--; if (depth === 0) { end = k; break; } }
  }
  if (end < 0) throw new Error(`donor block unterminated: ${name}`);
  return src.slice(open, end + 1);
}

function build() {
  const out = [];
  for (const hue of HUES) {
    let body = donorBlock(`mwiii_vertigo_retro_synth_${hue}_tinted_edge`);
    for (const [field, value] of Object.entries(MATTE)) {
      const re = new RegExp(`("${field}")\\s+"[^"]*"`, 'g');
      // PRESENCE, not change: several of these fields are already "0" in the
      // donor, and an unchanged body is the correct outcome for those. Testing
      // for a change would false-alarm on exactly the fields needing no edit.
      if (!re.test(body)) throw new Error(`field not present in donor, cannot zero it: ${field} (${hue})`);
      re.lastIndex = 0;
      body = body.replace(re, `$1 "${value}"`);
    }
    out.push(`\t"tod_door_${hue}" ( "material.gdf" )`);
    out.push(body.split('\n').map(l => l).join('\n'));
  }
  for (const [k, donor] of DARK) {
    let body = donorBlock(`mwiii_vertigo_retro_synth_${donor}`);
    for (const [field, value] of Object.entries(DARK_FIELDS)) {
      const re = new RegExp(`("${field}")\\s+"[^"]*"`, 'g');
      if (!re.test(body)) throw new Error(`field not present in donor, cannot set it: ${field} (dark ${k} <- ${donor})`);
      re.lastIndex = 0;
      body = body.replace(re, `$1 "${value}"`);
    }
    out.push(`\t"tod_dark_${k}" ( "material.gdf" )`);
    out.push(body);
  }
  for (const suffix of BLACK.suffixes) {
    let body = donorBlock(`mwiii_vertigo_retro_synth_${suffix}`);
    const fields = { ...MATTE, scaleRGB: '0', colorTint: blackTint(body, suffix) };
    for (const [field, value] of Object.entries(fields)) {
      const re = new RegExp(`("${field}")\\s+"[^"]*"`, 'g');
      if (!re.test(body)) throw new Error(`field not present in donor, cannot set it: ${field} (black ${suffix})`);
      re.lastIndex = 0;
      body = body.replace(re, `$1 "${value}"`);
    }
    out.push(`\t"tod_black_${suffix}" ( "material.gdf" )`);
    out.push(body);
  }
  return out.join('\n');
}

function main() {
  const check = process.argv.includes('--check');
  const gdt = fs.readFileSync(OUT, 'utf8');
  const block = build();

  // Native gdtdb rejects // comments. Identify our owned blocks by name.
  const clean = gdt.replace(/^\s*\/\/[^\r\n]*\r?\n/gm, '');
  const owned = [...clean.matchAll(/^\t"tod_(?:door_(?:blue|green|orange|yellow|red)|dark_(?:floor|step|wall|gold|ruby|brass)|black_[a-z_]+)"\s*\(\s*"material\.gdf"\s*\)\s*\{[\s\S]*?^\t\}/gm)];
  let next;
  if (owned.length) {
    // The first run after the DARK family was added finds only the five door
    // blocks; that is a legal starting state, not a corruption.
    if (![HUES.length, HUES.length + DARK.length, HUES.length + DARK.length + BLACK.suffixes.length].includes(owned.length)) throw Error('Incomplete or duplicated tod_door / tod_dark / tod_black material set');
    const first = owned[0], last = owned[owned.length - 1];
    next = clean.slice(0, first.index) + block + clean.slice(last.index + last[0].length);
  } else {
    const close = clean.lastIndexOf('}');
    if (close < 0) throw Error('tod_materials.gdt has no closing brace');
    next = clean.slice(0, close) + block + '\n' + clean.slice(close);
  }

  if (check) {
    if (next !== gdt) {
      console.error('tod_door_* / tod_dark_* materials are STALE — run: node tools/gen_tod_door_materials.js');
      process.exit(1);
    }
    console.log(`tod_door_* / tod_dark_* / tod_black_* materials OK (${HUES.length} matte door hues + ${DARK.length} dark hall clones + ${BLACK.suffixes.length} blackout clones)`);
    return;
  }
  fs.writeFileSync(OUT, next, 'utf8');
  console.log(`wrote ${OUT}  (${HUES.length} matte door materials: ${HUES.map(h => 'tod_door_' + h).join(', ')}; ${DARK.length} dark hall clones: ${DARK_NAMES.join(', ')}; ${BLACK.suffixes.length} blackout clones tod_black_*)`);
}

main();
