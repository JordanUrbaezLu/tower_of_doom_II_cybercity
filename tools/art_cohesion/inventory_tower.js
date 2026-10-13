'use strict';
// Actual lower-tower faces for the material review, with no substitute geometry.
const fs=require('fs'),path=require('path'),C=require('../convex_brush');
const root=path.resolve(__dirname,'../..'),map=fs.readFileSync(path.join(root,'map_source/zm/zm_tod2_cybercity.map'),'utf8');
const rows=[];
for(const m of map.matchAll(/^\/\/ brush \d+ [\u2014-] (.*?)\r?\n\{([\s\S]*?)^\}/gm)) {
  const planes=C.readPlanes(m[2]);if(!planes.some(p=>p.mat.startsWith('tod_cc_')))continue;
  const h=C.hull(planes);
  if(h.lo[2]<-20||h.hi[2]>1536||Math.max(...h.lo.slice(0,2).map(Math.abs),...h.hi.slice(0,2).map(Math.abs))>1500)continue;
  rows.push({label:m[1],faces:h.faces.filter(f=>f.mat.startsWith('tod_cc_')).map(f=>({mat:f.mat,n:f.n,vertices:f.vertices}))});
}
fs.mkdirSync(path.join(root,'tmp/tower_design'),{recursive:true});
fs.writeFileSync(path.join(root,'tmp/tower_design/review_inventory.json'),JSON.stringify(rows));
console.log('TOWER_REVIEW_INVENTORY',rows.length,'actual solids');
