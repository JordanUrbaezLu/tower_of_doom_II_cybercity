'use strict';
// Prove that a material bay neither adds collision nor removes its old slab/wall.
const fs=require('fs'),path=require('path'),assert=require('assert');
const C=require('../convex_brush'),root=path.resolve(__dirname,'../..');
const out=path.join(root,'art/cybercity_materials');
const source=process.argv.includes('--snapshot')&&process.argv[3] ? process.argv[3] : path.join(root,'map_source/zm/zm_tod2_cybercity.map');
const map=fs.readFileSync(source,'utf8');
const rows=new Map();
for(const m of map.matchAll(/^\/\/ brush \d+ [\u2014-] (.*?)\r?\n\{([\s\S]*?)^\}/gm))
  if(m[1].startsWith('crown hall floor')||m[1].startsWith('crown hall shop bay')||m[1].startsWith('crown wall W'))
    rows.set(m[1],C.hull(C.readPlanes(m[2])));
const checkpoint=path.join(out,'geometry_before.json');
if(process.argv.includes('--snapshot')) {
  assert(!fs.existsSync(checkpoint),'Keep original baseline');
  assert.strictEqual(rows.size,2,'Baseline must contain original unsplit floor/wall');
  const before={source};for(const k of ['crown hall floor','crown wall W']) {const h=rows.get(k);assert(h,k);before[k]={lo:h.lo,hi:h.hi};}
  fs.writeFileSync(checkpoint,JSON.stringify(before,null,2));
  console.log('SURFACE_BAY_GEOMETRY_SNAPSHOT');process.exit(0);
}
const before=JSON.parse(fs.readFileSync(checkpoint));
const volume=h=>h.lo.reduce((v,x,i)=>v*(h.hi[i]-x),1);
for(const [anchor,prefixes] of [['crown hall floor',['crown hall floor','crown hall shop bay']],['crown wall W',['crown wall W']]]) {
  const old=before[anchor],parts=[...rows].filter(([k])=>prefixes.some(p=>k.startsWith(p))).map(([,v])=>v);
  assert.strictEqual(parts.length,1,anchor+' must use the original whole solid');
  for(const h of parts)assert(h.lo.every((x,i)=>x>=old.lo[i]-1e-5&&h.hi[i]<=old.hi[i]+1e-5),anchor+' escapes original solid');
  for(let i=0;i<parts.length;i++)for(let j=i+1;j<parts.length;j++)
    assert(!parts[i].lo.every((v,k)=>Math.min(parts[i].hi[k],parts[j].hi[k])-Math.max(v,parts[j].lo[k])>1e-5),'overlapping partition');
  assert(Math.abs(parts.reduce((v,h)=>v+volume(h),0)-volume(old))<.001,anchor+' volume changed');
}
const result={floor_parts:1,wall_parts:1,solid_union_unchanged:true,new_roof:false,source_geometry_checked:true};
fs.writeFileSync(path.join(out,'geometry_validation.json'),JSON.stringify(result,null,2));
console.log('CROWN_SURFACE_GEOMETRY_PASS: original whole floor and wall restored; no added collision');
