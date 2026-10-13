'use strict';
// Transit review inventory: every crown-kit solid near the top hall (and the base
// apron), with its faces, plus the map's own lights there — read from the
// FINISHED .map, never from the generator. Consumed by transit_preview.py.
// Usage: node tools/art_cohesion/inventory_transit.js [map]
const fs=require('fs'),path=require('path'),C=require('../convex_brush');
const root=path.resolve(__dirname,'../..');
const mapPath=process.argv[2]||path.join(root,'map_source/zm/zm_tod2_cybercity.map');
const map=fs.readFileSync(mapPath,'utf8');
const routes=require('../tower_transit_contract').read(map),top=routes.find(r=>r.id==='top_to_30').src[2],rows=[];
// docs/196: the departure hall reaches x -1640, y -200..920, z top-330 (the keel's
// pendant) .. top+560 (the oculus jewels); the box keeps the terrace, the mast's
// foot and the landing deck in shot for context.
const inTop=h=>h.lo[2]>=top-400&&h.hi[2]<=top+700&&h.lo[0]>=-1800&&h.hi[0]<=800&&h.lo[1]>=-400&&h.hi[1]<=1400;
const inBase=h=>h.lo[2]>=-16&&h.hi[2]<=350&&h.lo[0]>=-560&&h.hi[0]<=560&&h.lo[1]>=-1050&&h.hi[1]<=560;
for(const m of map.matchAll(/^\/\/ brush \d+ [—-] (.*?)\r?\n\{([\s\S]*?)^\}/gm)) {
  const ps=C.readPlanes(m[2]);if(!ps.some(p=>p.mat.startsWith('tod_cc_')))continue;
  const h=C.hull(ps);let area;
  if(inTop(h))area='top';
  if(inBase(h))area='base';
  if(!area)continue;
  rows.push({area,label:m[1],faces:h.faces.filter(f=>f.mat.startsWith('tod_cc_')).map(f=>({mat:f.mat,n:f.n,vertices:f.vertices.map(p=>[p[0],p[1],p[2]-(area==='top'?top:0)])}))});
}
const lights=[];
for(const m of map.matchAll(/^\/\/ entity \d+ [^\n]*\r?\n([\s\S]*?)(?=^\/\/ entity |$(?![\s\S]))/gm)) {
  const k=Object.fromEntries([...m[1].matchAll(/^"([^"]+)" "([^"]*)"/gm)].map(x=>[x[1],x[2]]));
  if(k.classname!=='light'||!k.origin)continue;
  const o=k.origin.split(' ').map(Number);
  if(o[2]<top-100||o[2]>top+700||o[0]<-1800||o[0]>800||o[1]<-400||o[1]>1400)continue;
  lights.push({name:k.targetname||'',org:[o[0],o[1],o[2]-top],color:(k._color||'1 1 1').split(' ').map(Number),radius:+k.radius||300,stops:+k.stops||8});
}
const out=path.join(root,'tmp/transit_bay');fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'inventory.json'),JSON.stringify({top,rows,routes,lights}));
console.log('TRANSIT_INVENTORY',rows.length,'actual map solids,',lights.length,'lights');
