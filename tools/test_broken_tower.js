'use strict';
const fs=require('fs'),assert=require('assert/strict'),path=require('path');
const root=path.resolve(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8');
const map=read('map_source/zm/zm_tod2_cybercity.map'),routes=require('./broken_tower_contract').read(map),C=require('./convex_brush');
// A bare GUID starts a brush to cod2map, which then aborts expecting a plane.
// Source route parsing alone accepts it, so check the native entity syntax too.
assert(!/^\s*\{[0-9A-F]{8}-[0-9A-F-]+\}\s*$/mi.test(map),'Entity GUIDs must use the native guid "{...}" declaration');
assert.equal(routes.length,24);assert.deepEqual(routes.map(r=>r.lap).sort((a,b)=>b-a),require('./broken_tower_layout').DROP_LAPS);
for(const lap of [1,11,21,31,41,50])assert(map.includes(`"targetname" "tod_door_lap${lap}"`),'Milestone/entry door retained');
const rows=new Map([...map.matchAll(/^\/\/ brush \d+ [\u2014-] (.*?)\r?\n\{([\s\S]*?)^\}/gm)].map(m=>[m[1],C.readPlanes(m[2])]));
const data=read('scripts/zm/zm_tod2_cybercity/_tod_door_data.gsc');
const infos=new Map();
for(const r of routes) {
  const text=data.split(`case ${r.lap}:`)[1]?.split('return r;')[0];assert(text,'Generated drop data');
  const info={lap:r.lap,flag:`enter_lap${r.lap}`};
  for(const key of ['upper','lower','lo','hi'])info[key]=text.match(new RegExp(`r\\.${key} = \\( ([^)]*) \\)`))[1].split(',').map(Number);
  infos.set(r.lap,info);assert.deepEqual(info.upper,r.from);assert.deepEqual(info.lower,r.to);
  assert.equal(info.upper[2]-info.lower[2],190);
  const deck=rows.get(`lap${r.lap} broken catch deck`);assert(deck,'Catch deck');
  for(const x of [272,336,400])for(const y of [-240,-120,0,120,240])assert.equal(C.verticalSpan(deck,Math.sign(r.from[0])*x,y)?.[1],r.to[2],'Whole catch floor supported');
  assert(![...rows.keys()].some(k=>new RegExp(`^lap${r.lap} [EW] (step |stair ramp)`).test(k)),'No old stair or invisible ramp');
}
// Exercise the SHIPPING GSC callback and zone opener with supported native calls stubbed.
const src=read('scripts/zm/zm_tod2_cybercity/_tod_doors.gsc');
const body=n=>src.match(new RegExp('function '+n+'\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\}'))[1];
const translate=s=>s.replace(/tod_door_data::/g,'data.').replace(/level flag::(exists|get|set)\(/g,'flags.$1(').replace(/self GetEntityNumber\(\)/g,'self.GetEntityNumber()');
const logs=[],dataStub={get_drop_info:lap=>infos.get(lap)};
const guard=new Function('self','sMeansOfDeath','iDamage','GetTime','data','isdefined','broken_log','let row,o;'+translate(body('broken_fall_guard')));
const row=infos.get(3),player=()=>({tod_drop_lap:3,tod_drop_ms:1000,origin:[...row.lower],GetEntityNumber:()=>1});
const run=(p,cause='MOD_FALLING',now=1600)=>guard(p,cause,70,()=>now,dataStub,v=>v!==undefined,m=>logs.push(m));
assert.equal(run(player()),0,'Mandatory landing protected');
const p=player();assert.equal(run(p),0);assert.equal(run(p),-1,'Protection consumed');
assert.equal(run(player(),'MOD_BULLET'),-1);assert.equal(run(player(),'MOD_FALLING',3501),-1,'Stale approach');
assert.equal(run({...player(),tod_drop_lap:undefined}),-1);
assert.equal(run({...player(),origin:[0,0,row.lower[2]]}),-1,'Unrelated landing');
assert.equal(run({...player(),origin:[row.lower[0],row.lower[1],row.lower[2]+50]}),-1,'Not on catch floor');
const open=new Function('row','flags','breather_unlock','broken_log',translate(body('broken_open')));
// W2E (2026-10-05): the opener no longer calls breather_unlock (the elite-director stamp retired with those directors),
// so "activated once" is counted on the flag itself.
assert(!/breather_unlock/.test(body('broken_open')),'The retired elite unlock stays out of the zone opener');
let unlocked=0;const flags={exists:()=>true,value:false,get(){return this.value;},set(){this.value=true;unlocked++;}};
assert.equal(open(row,flags,()=>unlocked++,m=>logs.push(m)),true);open(row,flags,()=>unlocked++,()=>{});assert.equal(unlocked,1,'Idempotent zone activation');
assert.equal(open(row,{exists:()=>false},()=>unlocked++,m=>logs.push(m)),false,'Missing flag reported');
assert(logs.some(x=>x.startsWith('LANDING_PROTECTED'))&&logs.some(x=>x.startsWith('NO_ZONE_FLAG')));
// Compiled-navmesh section checker must reject accidental seams and restored bridges.
const nav=require('./broken_tower_navcheck').check;
const ds=[{lap:1,from:[0,0,192],to:[0,0,2]},{lap:2,from:[0,0,576],to:[0,0,386]}];
const centres=[[0,0,0],[0,0,300],[0,0,600]],under=p=>p[2]<97?0:p[2]<481?1:2;
assert.equal(nav(ds,centres,[0,1,2],()=> 'tower',under).bad.length,0);
assert(nav(ds,centres,[0,0,1],()=> 'tower',under).bad.length,'Restored walk bridge/stale bake rejected');
assert(nav(ds,centres,[0,1,2],()=> 'tower',()=>-1).bad.length,'Missing endpoint mesh rejected');
assert(nav(ds,[...centres,[0,0,301]],[0,1,2,3],()=> 'tower',under).bad.length,'Unplanned island rejected');
console.log('BROKEN_TOWER_SOURCE_PASS: 24 fixed drops; broad supported catch floors; no return stairs; milestone doors; generated data; shipping landing/zone logic; navmesh checker negative controls. Native traversal/playtest pending.');
