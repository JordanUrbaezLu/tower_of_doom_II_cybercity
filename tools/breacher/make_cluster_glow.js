// make_cluster_glow.js - the Breacher Cluster's RED GLOW (2026-09-26).
//
// User, after build 14: "I did kind of like the red glow ... a mixture of like the red glow and a flame.
// But now it's just a flame ... somewhere in the middle would be great." The glow they liked was the stock
// DOA red rpg trail (zombie/fx_trail_rpg_red_doa, the Cluster's trail until build 13). Its five elements:
//   def0  an orange omni dynamic light (0.98/0.42/0, r200) = THE GLOW on the ground and walls   KEEP
//   def1  a red flame-base sprite (gfx_fire_flame_base_2_anim_em)                                KEEP
//   def2  a red flicker sprite   (gfx_fire_flicker_base_1_anim_em)                               KEEP
//   def3  a smoke trail billow, runRelToWorld = the long streak that "looks like a flare"         DROP
//   def4  a slow fog puff = the red smoke                                                        DROP
// This writes the stock file minus def3/def4 as a map-owned effect, played WITH the orange flame
// (fire/fx_fire_single_loop_01_xsm_evb) on the canister and every bomblet (_tod_class_kit.gsc
// TOD_CLUSTER_FX_GLOW). Re-run it; never hand-edit the output.
//
//   node tools/breacher/make_cluster_glow.js           write share/raw/fx/tod/breacher/fx_tod_cluster_glow.efx
//   node tools/breacher/make_cluster_glow.js --check   exit 1 if the output is missing or differs
'use strict';
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const TOOLS = 'C:/BO3Tools/TOD2Cybercity';   // the private Tower II tools root (tools/tod2_workspace.ps1)
const SRC = path.join(TOOLS, 'share', 'raw', 'fx', 'zombie', 'fx_trail_rpg_red_doa.efx');
const OUT_NAME = 'tod/breacher/fx_tod_cluster_glow';
const OUT = path.join(REPO, 'share', 'raw', 'fx', ...OUT_NAME.split('/')) + '.efx';
if (OUT_NAME.length > 63) throw new Error(`${OUT_NAME} is ${OUT_NAME.length} chars (the runtime cuts fx paths at 63)`);

const KEEP = ['wraith_looping_def0', 'wraith_looping_def1', 'wraith_looping_def2'];
const DROP = ['wraith_looping_def3', 'wraith_looping_def4'];

function build() {
  const raw = fs.readFileSync(SRC, 'utf8');
  if (raw.includes('gfx_debug_missing_fx')) throw new Error(`${SRC} is a stub (gfx_debug_missing_fx)`);
  const eol = raw.includes('\r\n') ? '\r\n' : '\n';
  const lines = raw.split(eol);
  // An element is a column-0 "{" line through its column-0 "}" line.
  const head = [];
  const elems = [];
  let cur = null;
  for (const l of lines) {
    if (cur === null && l === '{') { cur = [l]; continue; }
    if (cur !== null) {
      cur.push(l);
      if (l === '}') { elems.push(cur); cur = null; }
      continue;
    }
    if (elems.length === 0) head.push(l);
  }
  if (cur !== null) throw new Error('unterminated element in ' + SRC);
  const nameOf = (e) => { const m = e.join('\n').match(/\n\tname "([^"]+)";/); return m ? m[1] : '?'; };
  const names = elems.map(nameOf);
  if (names.join(',') !== [...KEEP, ...DROP].join(',')) throw new Error('unexpected elements in the donor: ' + names.join(', '));
  // Signatures of what we drop / keep, so a changed donor fails loudly instead of silently shipping the wrong half.
  const text = (n) => elems[names.indexOf(n)].join('\n');
  if (!/runRelToWorld/.test(text('wraith_looping_def3'))) throw new Error('def3 is no longer the world-space streak');
  if (!/gfx_fog_slow/.test(text('wraith_looping_def4'))) throw new Error('def4 is no longer the fog puff');
  if (!/gfx_dlight_gen_omni/.test(text('wraith_looping_def0'))) throw new Error('def0 is no longer the glow light');
  const kept = elems.filter((e, i) => KEEP.includes(names[i]));
  const out = [...head, ...kept.flatMap((e, i) => (i ? ['', ...e] : e))];
  // keep whatever trailed the last element (blank lines) the way the donor had it
  const tailStart = lines.lastIndexOf('}') + 1;
  return out.concat(lines.slice(tailStart)).join(eol);
}

const want = build();
if (process.argv.includes('--check')) {
  const have = fs.existsSync(OUT) ? fs.readFileSync(OUT, 'utf8') : null;
  if (have !== want) { console.error(`[make_cluster_glow] ${path.relative(REPO, OUT)} is missing or stale - re-run without --check`); process.exit(1); }
  console.log(`[make_cluster_glow] OK - ${OUT_NAME} matches its donor minus the streak and the smoke`);
} else {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, want);
  console.log(`[make_cluster_glow] wrote ${path.relative(REPO, OUT)} (${want.length} B; kept ${KEEP.join(', ')})`);
}
