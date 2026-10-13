'use strict';
// Read actual emitted support walls and surrounding play geometry; never regenerate.
const fs=require('fs'),path=require('path'),C=require('../convex_brush');
const root=path.resolve(__dirname,'../..');
const map=fs.readFileSync(path.join(root,'map_source/zm/zm_tod2_cybercity.map'),'utf8');
const {placements}=require('./layout').geometry();
const scenes=placements.map(p=>({...p,solids:[]}));
for(const m of map.matchAll(/^\/\/ brush \d+ [\u2014-] (.*?)\r?\n\{([\s\S]*?)^\}/gm)) {
  const planes=C.readPlanes(m[2]);if(planes.length<4||!planes.some(p=>p.mat.startsWith('tod_cc_')))continue;
  const h=C.hull(planes);
  for(const sc of scenes) {
    const p=sc.centre;
    if(h.hi.some((v,i)=>v<p[i]-(i===2?140:430))||h.lo.some((v,i)=>v>p[i]+(i===2?210:430)))continue;
    sc.solids.push({label:m[1],lo:h.lo,hi:h.hi,faces:h.faces.filter(f=>f.mat.startsWith('tod_cc_')).map(f=>({mat:f.mat,n:f.n,vertices:f.vertices}))});
  }
}
// Every panel must really back onto one opaque emitted solid, including corners.
for(const sc of scenes) {
  const right=[-sc.normal[1],sc.normal[0],0];
  sc.supports=[];
  for(const u of [-sc.width/2-.7,sc.width/2+.7]) for(const v of [-sc.height/2-.7,sc.height/2+.7]) {
    const p=sc.centre.map((x,i)=>x+right[i]*u+(i===2?v:0)-sc.normal[i]*2.01);
    const wall=sc.solids.find(s=>s.lo.every((x,i)=>p[i]>=x-.001)&&s.hi.every((x,i)=>p[i]<=x+.001));
    if(!wall)throw Error(`Dealer panel ${sc.id} corner has no emitted opaque support: ${p}`);
    sc.supports.push(wall.label);
  }
}
const out=path.join(root,'art/dealer_presence/context.json');
if(process.argv.includes('--check')) {
  if(JSON.stringify(scenes)!==fs.readFileSync(out,'utf8'))throw Error('Dealer context changed since matched review');
} else fs.writeFileSync(out,JSON.stringify(scenes));
console.log('DEALER_SUPPORT_CHECK',scenes.map(s=>`${s.id}: ${[...new Set(s.supports)].join(', ')} (${s.solids.length} nearby solids)`).join('; '));
