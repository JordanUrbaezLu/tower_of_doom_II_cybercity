'use strict';
const fs=require('fs'),path=require('path'),C=require('../convex_brush');
const root=path.resolve(__dirname,'../..'),map=fs.readFileSync(path.join(root,'map_source/zm/zm_tod2_cybercity.map'),'utf8');
const rows=[];
for(const m of map.matchAll(/^\/\/ brush \d+ [\u2014-] (.*?)\r?\n\{([\s\S]*?)^\}/gm)) {
  const ps=C.readPlanes(m[2]);if(!ps.length)continue;
  const h=C.hull(ps);
  // Entire detached crown island and its visible shell, including underside.
  // Names capture its ornament even if an outer tip crosses the spatial band.
  const island=(h.lo[1]>=5000&&h.hi[2]>=14000&&h.hi[0]<5000&&h.lo[0]>-5000);
  if(!island&&!/^crown (skirt|point|rib|front cross|finial|jewel|cullinan|pendilia|girandole|monde|beacon|mouth|hall|cap|wall|cornice|gate|ermine|band|arch|rim|chevron|rosette|merlon)/.test(m[1]))continue;
  if(ps.every(p=>/^(clip|sky|caulk|nodraw|trigger|volume)/.test(p.mat)))continue;
  rows.push({label:m[1],lo:h.lo,hi:h.hi,faces:h.faces.map(f=>({mat:f.mat,n:f.n,d:f.d,vertices:f.vertices,area:f.area})),materials:[...new Set(ps.map(p=>p.mat))]});
}
const mats={};for(const r of rows)for(const f of r.faces){const a=mats[f.mat]??={faces:0,area:0,examples:[]};a.faces++;a.area+=f.area;if(a.examples.length<6&&!a.examples.includes(r.label))a.examples.push(r.label);}
const out=path.join(root,'art/cybercity_materials');fs.writeFileSync(path.join(out,'crown_inventory.json'),JSON.stringify({brushes:rows.length,materials:mats,rows},null,2));
console.log(JSON.stringify({brushes:rows.length,materials:mats},null,2));
