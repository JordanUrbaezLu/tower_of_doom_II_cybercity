'use strict';
// Whole-map source audit. Optional pre-pass map proves exact geometry/entity preservation.
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const C=require('../convex_brush'),root=path.resolve(__dirname,'../..');
const file='map_source/zm/zm_tod2_cybercity.map',map=fs.readFileSync(path.join(root,file),'utf8');
const brushes=text=>[...text.matchAll(/^\/\/ brush \d+ [\u2014-] (.*?)\r?\n\{([\s\S]*?)^\}/gm)].map(m=>({label:m[1],body:m[2],planes:C.readPlanes(m[2])}));
const ents=text=>new Map([...text.matchAll(/^\/\/ entity \d+ [\u2014-] (.*?)\r?\n([\s\S]*?)(?=^\/\/ entity |$(?![\s\S]))/gm)].map(m=>[m[1],{body:m[2],kv:Object.fromEntries([...m[2].matchAll(/^"([^"]+)" "([^"]*)"/gm)].map(k=>[k[1],k[2]]))}]));
const all=brushes(map),entities=ents(map),lights=[...entities].filter(([,e])=>e.kv.classname==='light');
const route=lights.filter(([label])=>/^tod light route /.test(label));
const {DROP_LAPS}=require('../broken_tower_layout');
assert.strictEqual(route.length,100-DROP_LAPS.length,'Two light pools per lap across the 50 laps, less the broken flight at every break (docs/205 s7b; the Endless Spire and its 70 laps were removed 2026-09-29)');
assert(!/\) (?:tod_black_|tod_dark_|tod_door_|mwiii_vertigo_retro_synth_|tod_hall_wall_)/.test(map),'Legacy architecture remains');
// tod_haven_barrier (docs/202 v4, 2026-10-03) is a TOOL surface like clip: the stock clip_weapon_noimpact block copied
// whole (noDraw 1, usage clip, nonSolid) + missileClip/noPenetrate, on the four haven barrier brushmodels. Never drawn.
const utility=/^(sky|clip|clip_player|clip_slick|caulk|nodraw|trigger|volume|sun_volume|umbra_volume|volume_fpstool|tod_haven_barrier)$/;
const materials={};
for(const p of C.readPlanes(map)){
 assert(p.mat.startsWith('tod_cc_')||utility.test(p.mat),'Unconverted visible material '+p.mat);
 materials[p.mat]=(materials[p.mat]||0)+1;
}
const solids=all.filter(b=>b.planes.some(p=>p.mat.startsWith('tod_cc_'))).map(b=>({...b,h:C.hull(b.planes)}));
const buried=[];
for(const [label,{kv}] of route) {
  assert.deepStrictEqual([1,2,3,4].map(i=>kv['lightingstate'+i]),['1','0','0','0'],label+' power mask');
  assert(+kv.radius<384 && +kv.culling_falloff>+kv.culling_cutoff,label+' locality/culling');
  const p=kv.origin.split(' ').map(Number);
  for(const s of solids) if(p.every((v,i)=>v>s.h.lo[i]&&v<s.h.hi[i])&&s.planes.every(q=>C.dot(q.n,p)<q.d-.01)) buried.push({light:label,brush:s.label});
}
assert.deepStrictEqual(buried,[],'New light origins buried in architecture');
const report={world_brushes:all.length,lights:lights.length,new_stair_pools:route.length,buried_new_lights:buried.length,legacy_architecture_faces:0,power_masks_verified:true,geometry_compared:false,native_build_verified:false,native_visual_verified:false};
report.material_faces=materials;report.architecture_faces=Object.entries(materials).filter(([k])=>k.startsWith('tod_cc_')).reduce((sum,[,n])=>sum+n,0);
report.retained_signage='None: all structural surfaces use the crown kit (the trial halls left with the Endless Spire).';
const baseline=process.argv[2];
if(baseline) {
  const old=fs.readFileSync(baseline,'utf8'),oldBrushes=brushes(old),oldEnts=ents(old);
  const signature=b=>b.planes.map(p=>p.v);
  assert.deepStrictEqual(all.map(b=>[b.label,signature(b)]),oldBrushes.map(b=>[b.label,signature(b)]),'Brush planes changed');
  const stripMaterials=s=>s.replace(/(\) )[\w/]+ ([-\d.]+) ([-\d.]+) (?=[-\d.]+ [-\d.]+ [-\d.]+ [-\d.]+ lightmap_gray)/g,'$1MATERIAL UV UV ');
  let retuned=0;
  for(const [label,before] of oldEnts) {
    const after=entities.get(label);assert(after,'Missing entity '+label);
    if(before.kv.classname==='light') {
      const omit=new Set(['_color','radius','stops','far_edge','spec_comp','culling_cutoff','culling_falloff']);
      const unchanged=kv=>Object.fromEntries(Object.entries(kv).filter(([k])=>!omit.has(k)));
      assert.deepStrictEqual(unchanged(after.kv),unchanged(before.kv),label+' state/origin/behavior changed');
      if(after.body!==before.body)retuned++;
    } else assert.strictEqual(stripMaterials(after.body),stripMaterials(before.body),label+' changed');
  }
  for(const [label] of entities)assert(oldEnts.has(label)||/^tod light route /.test(label),'Unexpected entity '+label);
  report.geometry_compared=true;report.retuned_existing_lights=retuned;
  report.baseline_sha256=crypto.createHash('sha256').update(old).digest('hex');
}
const stats=JSON.parse(fs.readFileSync(path.join(root,'docs/sky_preview/sky3d_stats.json')));
const sky=fs.readFileSync(path.join(root,'source_data/tod_skybox.gdt'),'utf8');
const stops=+sky.match(/"skyStops" "([^"]+)"/)[1];
// 2026-09-28 (user: "sky box is not bright enough at all ... agents are getting stuck"): skyStops ALSO scales the
// VISIBLE sky, so this gate's old "energy ratio must be 1" rule forced every brighter-picture pass to cancel itself on
// screen. The sky is now DELIBERATELY 8x (3 stops) over the 2026-09-26 baseline: skyStops 0.85 -> 3.85. To change the
// sky's brightness again, move SKY_STOPS / SKY_RATIO here in the same edit and SAY it changes the look.
// 2026-09-29 (user: "a little bit of increase on the brightness of the sky"): +0.5 stop, 3.85 -> 4.35 = the sky
// on screen AND its light on the world x1.41; the ratio over the 2026-09-26 baseline is 2^3.5 = 11.31x.
// 2026-09-29 13:36 (session 22's re-finish: the title sign +25% and much brighter, the static ships out, roll 0;
// the sign's in-game bearing is -(the SSI sun azimuth + skyRotation) - roll, so skyRotation 40 puts it due west,
// docs/196 §3): the measured score is 0.6865 (the finish's target stays 0.64; the brighter sign lifts the mean). A
// rotation turns the picture, it does not change the mean, so SKY_SCORE does not move with skyRotation.
// 2026-09-29 16:00 (session 22, user: "remove the asteroids ... we're going to add actual asteroid models"): every static rock
// out of the picture (docs/166 §9.8); the city still solves to 0.64, the whole sky 0.6865346 -> 0.6865103 (-0.004 %, no visible change).
// 2026-09-29 v8: authored cyber monument + industrial lower city; raised celestial bodies.
// City score remains 0.64; the new sign contributes less energy, giving a measured whole-sky 0.64566344.
// Keep SSI/exposure/stops; the changed distribution requires a fresh full lighting bake (docs/166 section 10).
// 2026-09-30 shared city/planet detail pass: fixed approved gain (no re-normalization),
// dull before-jump title. Measured city .45513866, whole sky .44508159; native lit card
// is a separate source. The changed baked radiance requires a fresh FULL lighting bake.
const SKY_SCORE=0.4450453221797943, SKY_STOPS=4.35, SKY_RATIO=(SKY_SCORE*Math.pow(2,SKY_STOPS))/(.32*Math.pow(2,1.85));
assert(Math.abs(stats.score-SKY_SCORE)<.00001,'Sky score');assert.strictEqual(stops,SKY_STOPS,'Sky stops');
report.sky_score=stats.score;report.sky_stops=stops;
report.sky_bake_energy_ratio=(stats.score*Math.pow(2,stops))/(.32*Math.pow(2,1.85));
assert(Math.abs(report.sky_bake_energy_ratio-SKY_RATIO)<.0001,'Sky energy is not the intended '+SKY_RATIO+'x');
fs.mkdirSync(path.join(root,'docs/tower_design'),{recursive:true});
fs.writeFileSync(path.join(root,'docs/tower_design/source_validation.json'),JSON.stringify(report,null,2)+'\n');
console.log('TOWER_DESIGN_SOURCE_PASS',JSON.stringify(report));
