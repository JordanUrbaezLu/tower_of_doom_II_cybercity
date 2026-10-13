'use strict';
const assert=require('assert/strict');
function read(map) {
  const ents=[...map.matchAll(/^\/\/ entity \d+ [^\n]*\r?\n([\s\S]*?)(?=^\/\/ entity |$(?![\s\S]))/gm)]
    .map(m=>Object.fromEntries([...m[1].matchAll(/^"([^"]+)" "([^"]*)"/gm)].map(k=>[k[1],k[2]])));
  const sources=ents.filter(e=>e.targetname==='tod_transit_source');
  assert.equal(sources.length,8,'Transit source markers: three paired floors (30/20/10; 40 is the arena chamber) + crown/base pair');
  assert.equal(new Set(sources.map(e=>e.script_string)).size,8,'Unique transit route IDs');
  return sources.map(e=>{
    const matches=ents.filter(d=>d.targetname===e.target);assert.equal(matches.length,1,`${e.script_string} unique arrival`);
    const dest=matches[0],vec=v=>v.split(' ').map(Number);
    return {id:e.script_string,src:vec(e.origin),dst:vec(dest.origin),lock:e.script_flag,zone:dest.script_noteworthy};
  });
}
function nativeCheck(routes,faceUnder,comp,reference) {
  const bad=[];
  for(const row of routes)for(const [name,org] of [['source',row.src],['arrival',row.dst]]) {
    const zone=name==='arrival'?row.zone:row.id.startsWith('top_to_')?'roof_zone':
      row.id.startsWith('floor_')?`lap${row.id.split('_')[1]}_zone`:row.id==='base_to_crown'?'base_zone':'crown_zone';
    const ref=reference(zone),rf=faceUnder(ref);
    // Arrival fan-out must also be on the destination's walking component.
    const offsets=name==='arrival'?[[0,0],[48,0],[-48,0],[0,48],[0,-48]]:[[0,0]];
    for(const [x,y] of offsets) {
      const f=faceUnder([org[0]+x,org[1]+y,org[2]]);
      if(f<0||rf<0||comp[f]!==comp[rf])bad.push(`${row.id} ${name} (${x},${y}) has no connected mesh in ${zone}`);
    }
  }
  return bad;
}
module.exports={read,nativeCheck};
