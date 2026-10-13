// make_tier_fx.js - the Breacher's explosions, SMALLER AT THE LOWER CHARGE TIERS (2026-09-26).
//
// User, after build 16: "I like where we are as the max tier visuals ... tone it down each tier below,
// not each level, but like each tier where you start getting more clusters and more C4s ... less
// explosive, less big, less overwhelming, to kind of push players to keep upgrading."
// So the TOP tier plays today's effects UNCHANGED (the stock files), and every lower tier plays a
// uniformly SHRUNK copy of the same effect written here:
//   every velocity graph, size graph and spawn offset x s   (a smaller fireball that flies less far)
//   the light intensity graph x s                              (a dimmer flash)
//   the one-shot particle counts x s, never below 1            (less debris, less smoke)
//   mute: true drops the effect's own spawn sounds             (the quietest tier)
// Gravity, lifetimes, colours and materials are kept, so each tier reads as the same explosion, only
// smaller. The tiers and their scales are the TIERS table; _tod_class_kit.gsc picks the file by the
// charge tier (C4: Lv1/3/5/7 = tiers 1..4; Cluster: Lv1/4/8 = tiers 1..3). Re-run it; never hand-edit
// the outputs.
//
//   node tools/breacher/make_tier_fx.js           write share/raw/fx/tod/breacher/fx_tod_*_t<N>.efx
//   node tools/breacher/make_tier_fx.js --check   exit 1 if any output is missing or differs
'use strict';
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const TOOLS = 'C:/BO3Tools/TOD2Cybercity';   // the private Tower II tools root (tools/tod2_workspace.ps1)
const STOCK = (p) => path.join(TOOLS, 'share', 'raw', 'fx', ...p.split('/')) + '.efx';
const OURS = (p) => path.join(REPO, 'share', 'raw', 'fx', ...p.split('/')) + '.efx';

// donor = the effect the top tier plays today. out = the map-owned name (<= 63 chars: the runtime cuts
// longer fx paths). One row per LOWER tier; the top tier is the donor itself.
const TIERS = [
  // STICKY C4: the stock large fireball on top of the charge's own grenade blast (4 tiers)
  { donor: STOCK('explosions/fx_exp_generic_lg'), out: 'tod/breacher/fx_tod_c4_blast_t1', s: 0.55, mute: true },
  { donor: STOCK('explosions/fx_exp_generic_lg'), out: 'tod/breacher/fx_tod_c4_blast_t2', s: 0.70 },
  { donor: STOCK('explosions/fx_exp_generic_lg'), out: 'tod/breacher/fx_tod_c4_blast_t3', s: 0.85 },
  // CLUSTER: the canister's burst and every bomblet's pop (3 tiers)
  { donor: STOCK('explosions/fx_exp_grenade_default'), out: 'tod/breacher/fx_tod_cl_burst_t1', s: 0.60 },
  { donor: STOCK('explosions/fx_exp_grenade_default'), out: 'tod/breacher/fx_tod_cl_burst_t2', s: 0.80 },
  { donor: OURS('tod/fuse/fx_tod_fuse_bomblet_exp'), out: 'tod/breacher/fx_tod_cl_pop_t1', s: 0.60 },
  { donor: OURS('tod/fuse/fx_tod_fuse_bomblet_exp'), out: 'tod/breacher/fx_tod_cl_pop_t2', s: 0.80 },
];

const GRAPH_SCALED = /^(\t(?:velGraph[01][XYZ]|sizeGraph[01]|scaleGraph|lightRadiusGraph|lightIntensityGraph) )(-?[0-9.]+)$/;
const PAIR_SCALED = /^(\t(?:spawnOrgX|spawnOrgY|spawnOrgZ|spawnOffsetRadius|spawnOffsetHeight) )(-?[0-9.]+) (-?[0-9.]+);$/;
const ONE_SHOT = /^(\tspawnOneShot )(\d+) (\d+);$/;
const f6 = (n) => {
  const v = n.toFixed(6);
  return v === '-0.000000' ? '0.000000' : v;
};

// The element kinds these donors are made of. Anything else (a MODEL / mesh element above all) stops the
// tool: a mesh does not shrink with its size graphs the way a sprite does, so it would ship full size.
const KINDS = new Set(['billboardSprite', 'orientedSprite', 'tail', 'line', 'decal', 'lensFlare', 'runner', 'cloud', 'elemSpawnSound', 'elemFollowSound']);
const FX_PATH = /"([a-z0-9_]+(?:\/[a-z0-9_]+)+)"/g;   // a child effect: runner / emission / attachment / fxOnImpact / fxOnDeath

// Shrink one effect by s into `out`. A CHILD effect it spawns (in ANY field - the lead's rule after the
// tomahawk, 2026-09-26) is shrunk by the same s into `<out>_c<N>` and the reference repointed, so no
// part of a lower tier plays at full size. A child that cannot be found stops the tool.
function shrink(donor, out, s, mute, files) {
  const raw = fs.readFileSync(donor, 'utf8');
  if (raw.includes('gfx_debug_missing_fx')) throw new Error(`${donor} is a stub (gfx_debug_missing_fx)`);
  if (out.length > 63) throw new Error(`${out} is ${out.length} chars (the runtime cuts fx paths at 63)`);
  const eol = raw.includes('\r\n') ? '\r\n' : '\n';
  const lines = raw.split(eol);
  let graphs = 0, pairs = 0, shots = 0, muted = 0;
  const kinds = {};
  const children = [];
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    let m;
    if ((m = l.match(/^\t([A-Za-z]+)$/)) && lines[i + 1] === '\t{') {
      if (!KINDS.has(m[1])) throw new Error(`${donor}: element kind "${m[1]}" is not one this tool can shrink (a mesh?) - refusing`);
      kinds[m[1]] = (kinds[m[1]] || 0) + 1;
    }
    if ((m = l.match(GRAPH_SCALED))) { lines[i] = m[1] + f6(parseFloat(m[2]) * s); graphs++; continue; }
    if ((m = l.match(PAIR_SCALED))) { lines[i] = `${m[1]}${f6(parseFloat(m[2]) * s)} ${f6(parseFloat(m[3]) * s)};`; pairs++; continue; }
    if ((m = l.match(ONE_SHOT))) {
      const n = parseInt(m[2], 10), r = parseInt(m[3], 10);
      lines[i] = `${m[1]}${n > 0 ? Math.max(1, Math.round(n * s)) : 0} ${Math.round(r * s)};`;
      shots++;
      continue;
    }
    // mute: empty every "elemSpawnSound { "alias" };" block (the same shape as an empty elemFollowSound)
    if (mute && l === '\telemSpawnSound' && lines[i + 1] === '\t{') {
      let j = i + 2;
      while (j < lines.length && lines[j] !== '\t};') j++;
      if (j >= lines.length) throw new Error('unterminated elemSpawnSound in ' + donor);
      muted += j - (i + 2);
      lines.splice(i + 2, j - (i + 2));
      continue;
    }
    if (l.includes('/')) {
      lines[i] = l.replace(FX_PATH, (all, ref) => {
        const src = [OURS(ref), STOCK(ref)].find((p) => fs.existsSync(p));
        if (!src) throw new Error(`${donor}: child effect "${ref}" not found in the repo or the tools root - refusing`);
        const name = `${out}_c${children.length}`;
        children.push({ ref, name });
        shrink(src, name, s, mute, files);
        return `"${name}"`;
      });
    }
  }
  // Signatures: a donor that changed shape fails loudly instead of shipping an unscaled copy.
  if (graphs === 0 || shots === 0) throw new Error(`${donor}: nothing scaled (graphs ${graphs}, counts ${shots}) - the .efx format moved`);
  files.push({ out, text: lines.join(eol), donor, s, graphs, pairs, shots, muted, kinds, children });
}

const check = process.argv.includes('--check');
const files = [];
for (const row of TIERS) shrink(row.donor, row.out, row.s, !!row.mute, files);
if (TIERS.some((r) => r.mute) && !files.some((f) => f.muted > 0)) throw new Error('mute asked for but no spawn sound found');
let bad = 0;
for (const f of files) {
  const out = OURS(f.out);
  if (check) {
    const have = fs.existsSync(out) ? fs.readFileSync(out, 'utf8') : null;
    if (have !== f.text) { console.error(`[make_tier_fx] ${path.relative(REPO, out)} is missing or stale - re-run without --check`); bad++; }
  } else {
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, f.text);
    const kinds = Object.entries(f.kinds).map(([k, n]) => `${k} ${n}`).join(', ');
    const kids = f.children.map((c) => `${c.ref} -> ${c.name}`).join('; ');
    console.log(`[make_tier_fx] wrote ${f.out} x${f.s} from ${path.basename(f.donor)}: ${f.graphs} graphs, ${f.pairs} offsets, ${f.shots} counts${f.muted ? `, ${f.muted} sound(s) muted` : ''} | ${kinds}${kids ? ' | children: ' + kids : ''}`);
  }
}
if (check) {
  if (bad) process.exit(1);
  console.log(`[make_tier_fx] OK - ${files.length} effects (${TIERS.length} tiers + ${files.length - TIERS.length} children) match their donors`);
} else {
  console.log('[make_tier_fx] zone lines:\n' + files.map((f) => 'fx,' + f.out).join('\n'));
}
