'use strict';
// Validate the compiled WALK surfaces at each authored cut. Source traversal
// pairs are directed links, not proof that the runtime animation was exercised.
function check(drops,centroids,components,region,faceUnder) {
  const bad=[],cuts=drops.map(d=>(d.from[2]+d.to[2])/2);
  const bands=Array.from({length:cuts.length+1},()=>new Set());
  for(let f=0;f<centroids.length;f++) if(region(centroids[f])==='tower') {
    const z=centroids[f][2];let b=0;while(b<cuts.length&&z>cuts[b])b++;
    bands[b].add(components[f]);
  }
  const comps=bands.map((s,i)=>{
    if(s.size!==1)bad.push({fl:i,why:`descent section ${i}: expected one WALK component, found ${[...s]} (${s.size})`});
    return [...s][0];
  });
  const used=new Set();for(const c of comps){if(used.has(c))bad.push({fl:0,why:'authored drop sections still connected on foot (or stale navmesh)'});used.add(c);}
  const links=[];
  drops.forEach((d,i)=>{
    const a=faceUnder(d.from),b=faceUnder(d.to);
    if(a<0||b<0) {bad.push({fl:d.lap,why:'drop takeoff or catch deck has no compiled navmesh'});return;}
    const ca=components[a],cb=components[b];
    if(ca!==comps[i+1]||cb!==comps[i])bad.push({fl:d.lap,why:`drop joins unexpected components ${ca} -> ${cb}`});
    links.push({lap:d.lap,from:ca,to:cb});
  });
  const reachable=start=>{const seen=new Set([start]),todo=[start];while(todo.length){const a=todo.pop();for(const l of links)if(l.from===a&&!seen.has(l.to)){seen.add(l.to);todo.push(l.to);}}return seen;};
  const topComp=comps.at(-1),baseComp=comps[0],down=reachable(topComp);
  if(comps.some(c=>!down.has(c)))bad.push({fl:0,why:'top cannot reach every compiled descent section'});
  if(reachable(baseComp).has(topComp))bad.push({fl:0,why:'ordinary return route crosses the broken tower'});
  return {bad,topComp,baseComp,sections:comps.length,links,nativeTraversalPlayed:false};
}
module.exports={check};
