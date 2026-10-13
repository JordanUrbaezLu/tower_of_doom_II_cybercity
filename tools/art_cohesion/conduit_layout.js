'use strict';
// Supported inlays grouped into regional models to conserve server entities.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),C=require('../convex_brush');
const root=path.resolve(__dirname,'../..'),text=fs.readFileSync(path.join(root,'map_source/zm/zm_tod2_cybercity.map'),'utf8');
const solids=new Map();
for(const m of text.matchAll(/^\/\/ brush \d+ [\u2014-] (.*?)\r?\n\{([\s\S]*?)^\}/gm)){
 const ps=C.readPlanes(m[2]);if(ps.some(p=>p.mat.startsWith('tod_cc_')))solids.set(m[1],C.hull(ps));
}
const rows=[];
function rotate(v,angles){
 const [p,y,r]=angles.map(a=>a*Math.PI/180),[x0,y0,z0]=v;
 const a=[x0,y0*Math.cos(r)-z0*Math.sin(r),y0*Math.sin(r)+z0*Math.cos(r)];
 const b=[a[0]*Math.cos(p)+a[2]*Math.sin(p),a[1],-a[0]*Math.sin(p)+a[2]*Math.cos(p)];
 return [b[0]*Math.cos(y)-b[1]*Math.sin(y),b[0]*Math.sin(y)+b[1]*Math.cos(y),b[2]];
}
function mount(label,kind,org,angles,axis,sign,group,scale=[1.4,1,1]){
 const h=solids.get(label);assert(h,label);
 const plane=sign>0?h.hi[axis]:h.lo[axis];
 assert(Math.abs(org[axis]-plane-sign*.12)<.001,label+' surface offset');
 assert(h.faces.some(f=>Math.abs(f.n[axis]-sign)<.001&&Math.abs(f.d-sign*plane)<.001),label+' mounting face');
 const normal=rotate([0,0,1],angles);assert(Math.abs(normal[axis]-sign)<1e-6,label+' normal');
 for(const x of [-48,48])for(const y of [-9,9]){
  const v=rotate([x*scale[0],y*scale[1],0],angles).map((q,i)=>q+org[i]-normal[i]*.12);
  assert(h.faces.every(f=>C.dot(f.n,v)<=f.d+.001),label+' footprint escapes support');
 }
 rows.push({label,kind,org,angles,axis,sign,group,scale});
}
for(const [prefix,count,region] of [['',50,'tower']])for(let lap=1;lap<=count;lap++){   // the Endless Spire's 70 laps left with it 2026-09-29
 const group=region+'_'+String(Math.ceil(lap/5)).padStart(2,'0');
 for(const corner of lap%2?['NE','NW']:['SW','SE']){
  const label=`${prefix}lap${lap} ${corner} landing`,h=solids.get(label);assert(h,label);
  for(const fraction of [.25,.75])mount(label,'floor',[(h.lo[0]+h.hi[0])/2,h.lo[1]+(h.hi[1]-h.lo[1])*fraction,h.hi[2]+.12],[0,0,0],2,1,group);
  const axis=solids.has(label+' para a')?0:1,wall=label+' para '+(axis===0?'a':'b'),w=solids.get(wall);assert(w,wall);
  // Inside for descent; outside for the crown overlook.
  for(const sign of [-1,1]){
   const org=w.lo.map((v,i)=>(v+w.hi[i])/2);org[axis]=(sign>0?w.hi[axis]:w.lo[axis])+sign*.12;
   mount(wall,'wall',org,axis===0?[0,sign*90,90]:[0,0,-sign*90],axis,sign,group);
  }
 }
}
function floorEdges(label,group){
 const h=solids.get(label);assert(h,label);
 if(h.hi[0]-h.lo[0]<160||h.hi[1]-h.lo[1]<96)return;
 let placed=0;
 for(let y=h.lo[1]+48;y<=h.hi[1]-48;y+=256)for(let x=h.lo[0]+80;x<=h.hi[0]-80;x+=256){
  if(placed>=8)continue;
  const corners=[[-67.2,-9],[67.2,-9],[-67.2,9],[67.2,9],[0,0]].map(([dx,dy])=>[x+dx,y+dy,h.hi[2]]);
  if(!corners.every(v=>h.faces.every(f=>C.dot(f.n,v)<=f.d+.001)))continue;
  // Exclude covered floor pieces (raised decks, rails and doorframes).
  if([...solids].some(([other,b])=>other!==label && corners.some(v=>{
   const p=[v[0],v[1],v[2]+1.5];return p.every((q,i)=>q>b.lo[i]&&q<b.hi[i])&&b.faces.every(f=>C.dot(f.n,p)<f.d-.01);
  })))continue;
  mount(label,'floor',[x,y,h.hi[2]+.12],[0,0,0],2,1,group);placed++;
 }
}
for(const [label] of solids){
 let group;
 if(/^lap\d+ breather (floor|spur neck floor)$/.test(label))group='breather_'+label.match(/lap(\d+)/)[1];
 // docs/202 THE HAVENS v2 (THE HEART, the hall in the opened core): the loggia's district decks carry the
 // inlays under the old lounges' group names (same host models); the hall floor inside the field keeps the
 // field's own rings, and the teleporter at its centre stands clear (a script model, invisible to the cover
 // test below).
 else if(/^lap\d+ haven loggia (east|north) floor$/.test(label))group='breather_'+label.match(/lap(\d+)/)[1];
 else if(/^wing [nesw] (hall|room) floor$/.test(label))group='base_'+label.split(' ')[1];
 else if(/^(ground slab|vault floor|conduit floor|power hall floor|transit return floor)$/.test(label))group='base_'+label.split(' ')[0];
 // docs/196: the departure hall's floor is five slabs (the apse, the crossing, the nave and the two arms)
 else if(/^(transit bay floor( (apse|crossing|nave|north arm|south arm))?|terrace)$/.test(label))group='top_transit';
 else if(/^causeway hallway (power|teleporter) room$/.test(label))group='crown_side';
 else if(label==='crown hall floor')group='crown_hall';
 else if(label==='battle arena floor')group='arena';
 if(group)floorEdges(label,group);
}
for(const side of ['W','E'])for(const y of [8144,8456,8768,9080]){
 const label='crown wall '+side,h=solids.get(label),sign=side==='W'?1:-1;
 mount(label,'wall',[(sign>0?h.hi[0]:h.lo[0])+sign*.12,y,h.lo[2]+160],[0,sign*90,90],0,sign,'crown_hall');
}
assert.equal(new Set(rows.map(r=>r.org.join(','))).size,rows.length,'Duplicate conduit');
assert.equal(rows.filter(r=>r.group.startsWith('tower_')).length,400);
const groups=[...new Set(rows.map(r=>r.group))].map(kind=>{
 const members=rows.filter(r=>r.group===kind),org=[0,1,2].map(i=>Math.round(members.reduce((a,r)=>a+r.org[i],0)/members.length));
 return {kind,org,angles:[0,0,0],model:'tod_conduit_'+kind,count:members.length};
});
assert(groups.length<=70,'Do not exceed the previous 70 server entities');
const func=(name,key)=>`function ${name}()\n{\n    return array(\n${groups.map(r=>'        '+(Array.isArray(r[key])?'( '+r[key].join(', ')+' )':typeof r[key]==='number'?r[key]:'"'+r[key]+'"')).join(',\n')}\n    );\n}\n`;
const precache=groups.flatMap(r=>['off','on'].map(s=>`#precache( "model", "${r.model}_${s}" );`)).join('\n');
const gsc='// Generated from actual map support planes by 15_conduit_mounts.js.\n'+precache+'\n#namespace tod_conduit_data;\n\n'+[['origins','org'],['angles','angles'],['kinds','kind'],['models','model'],['counts','count']].map(([n,k])=>func(n,k)).join('\n');
const zone='// Generated powered architecture, grouped to conserve server entities.\n'+groups.flatMap(r=>['off','on'].map(s=>'xmodel,'+r.model+'_'+s)).join('\n')+'\n';
const output=path.join(root,'scripts/zm/zm_tod2_cybercity/_tod_conduit_data.gsc'),zpath=path.join(root,'zone_source/tod_power_conduits.zpkg');
const manifest=path.join(root,'art/cybercity_materials/color_restoration/conduit_mounts.json');
if(process.argv.includes('--check')){
 assert.equal(fs.readFileSync(output,'utf8'),gsc,'Conduit data stale: regenerate and export models after geometry edits');
 assert.equal(fs.readFileSync(zpath,'utf8'),zone,'Conduit package stale');
 const prior=JSON.parse(fs.readFileSync(manifest,'utf8'));assert.deepEqual(prior.rows,rows);assert.deepEqual(prior.groups,groups);
}else{
 fs.writeFileSync(output,gsc);fs.writeFileSync(zpath,zone);
 fs.writeFileSync(manifest,JSON.stringify({map_sha256:crypto.createHash('sha256').update(text).digest('hex'),rows,groups},null,2)+'\n');
}
console.log(`CONDUIT_MOUNTS_PASS: ${rows.length} supported inlays in ${groups.length} hosts; all 50 tower floors, interior/exterior walls, crown, transit, base, breathers and arena.`);
