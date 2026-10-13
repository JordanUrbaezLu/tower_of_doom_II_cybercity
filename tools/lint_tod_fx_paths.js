#!/usr/bin/env node
// lint_tod_fx_paths.js - every effect path this map names must fit the engine's
// 64-byte fx-path buffer: folder + name, no ".efx", <= 63 characters.
//
// Why (2026-09-26, two crash dumps): a parent effect spawning a child whose path
// is 64 chars is TRUNCATED to 63 at runtime, the cut name matches nothing, and
// the FX system access-violates the first time the parent plays (the Necromancer's
// Mangler aura: its generated child was "tod/necro/fx_necro_mangler_aura_fx_keeper_
// ghost_ambient_torso_os", 64; the thrall's sibling at 63 worked). The linker packs
// it without a word. Checked here: every `fx,` line in the zone + zpkgs, and every
// child reference inside every map-owned .efx (zone lines alone miss children).
// Runs on every build incl. -GscOnly (an fx rename is a zone/raw edit).
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const MAX = 63;
const bad = [];

function zoneFiles() {
    const dir = path.join(ROOT, 'zone_source');
    return fs.readdirSync(dir).filter(f => /\.(zone|zpkg)$/.test(f)).map(f => path.join(dir, f));
}
for (const zf of zoneFiles()) {
    const lines = fs.readFileSync(zf, 'latin1').split(/\r?\n/);
    lines.forEach((l, i) => {
        const m = /^\s*fx\s*,\s*([^\s/][^\s]*)/.exec(l);
        if (m && m[1].length > MAX) bad.push(`${path.basename(zf)}:${i + 1} zone line ${m[1].length} chars: ${m[1]}`);
    });
}

function walk(dir, out) {
    if (!fs.existsSync(dir)) return out;
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
        const p = path.join(dir, e.name);
        if (e.isDirectory()) walk(p, out); else if (e.name.endsWith('.efx')) out.push(p);
    }
    return out;
}
const fxRoot = path.join(ROOT, 'share', 'raw', 'fx');
const efx = walk(fxRoot, []);
for (const f of efx) {
    const rel = path.relative(fxRoot, f).replace(/\\/g, '/').replace(/\.efx$/, '');
    if (rel.length > MAX) bad.push(`${rel}.efx: its own path is ${rel.length} chars`);
    const text = fs.readFileSync(f, 'latin1');
    // child references: fxOnImpact / fxOnDeath / emission "name" and runner { "name" }
    const re = /"([a-z0-9_]+\/[a-z0-9_\/]+)"/g;
    let m;
    const seen = new Set();
    while ((m = re.exec(text))) {
        const ref = m[1];
        if (seen.has(ref)) continue;
        seen.add(ref);
        if (ref.length > MAX) bad.push(`${rel}.efx references child ${ref} (${ref.length} chars)`);
    }
}

if (bad.length) {
    console.error(`[lint_tod_fx_paths] FAIL - ${bad.length} effect path(s) over ${MAX} chars (the engine truncates and crashes on a child):`);
    for (const b of bad) console.error('  ' + b);
    process.exit(1);
}
console.log(`[lint_tod_fx_paths] OK - ${efx.length} map-owned .efx + zone fx lines all <= ${MAX} chars`);
