'use strict';
// Read emitted navigation entities, never substitute generator-computed geometry.
const assert=require('assert');
function read(map) {
  const entities=[...map.matchAll(/^\/\/ entity \d+[^\r\n]*\r?\n([\s\S]*?)(?=^\/\/ entity |$(?![\s\S]))/gm)].map(m=>Object.fromEntries([...m[1].matchAll(/^"([^"]+)" "([^"]*)"/gm)].map(k=>[k[1],k[2]])));
  const rows=[],seen=new Set();
  for(const e of entities.filter(e=>e.script_noteworthy==='tod_tower_drop')) {
    assert(e.classname==='node_negotiation_begin'&&e.animscript==='zm_jump_down_190','Drop must use the shipped zombie traversal');
    const ends=entities.filter(x=>x.targetname===e.target);assert.strictEqual(ends.length,1,'Missing/duplicate drop endpoint');
    const end=ends[0];assert(end.classname==='node_negotiation_end'&&!end.target,'Drop must be directed, with no return traversal');
    const from=e.origin.split(/\s+/).map(Number),to=end.origin.split(/\s+/).map(Number),lap=+e.script_int;
    assert(!seen.has(lap),'Duplicate drop lap');seen.add(lap);
    assert(from.concat(to).every(Number.isFinite),'Bad drop coordinates');
    assert(Math.abs(from[2]-to[2]-190)<.01&&Math.abs(Math.hypot(from[0]-to[0],from[1]-to[1])-51)<.01,'Stock traversal displacement changed');
    assert(from[0]===to[0]&&Math.abs(from[0])===336,'Drop outside the main stair lane');
    assert(!entities.some(x=>x.targetname===`tod_door_lap${lap}`),'Broken transition still has a paid slab');
    rows.push({lap,from:from.map((v,i)=>v-(i===2?2:0)),to:to.map((v,i)=>v-(i===2?2:0)),sign:Math.sign(from[1]-to[1]),entity:e,end});
  }
  return rows.sort((a,b)=>a.from[2]-b.from[2]);
}
module.exports={read};
