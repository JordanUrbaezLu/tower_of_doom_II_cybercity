'use strict';
const fs=require('fs'),assert=require('assert/strict'),path=require('path'),C=require('./convex_brush');
const root=path.resolve(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8');
const map=read('map_source/zm/zm_tod2_cybercity.map'),contract=require('./tower_transit_contract'),routes=contract.read(map);
const data=read('scripts/zm/zm_tod2_cybercity/_tod_crown_data.gsc'),src=read('scripts/zm/zm_tod2_cybercity/_tod_teleport.gsc');
const records=data.split('function transit_routes()')[1].split('r = SpawnStruct();').slice(1);
assert.equal(records.length,8);
for(const r of routes) {
  const row=records.find(b=>b.includes(`r.id = "${r.id}";`));assert(row,r.id+' runtime row');
  for(const k of ['src','dst'])assert.deepEqual(row.match(new RegExp(`r\\.${k} = \\( ([^)]*) \\)`))[1].split(',').map(Number),r[k]);
  for(const k of ['zone','lock'])assert(row.includes(`r.${k} = "${r[k]}";`),r.id+' '+k);
}
const top=routes.find(r=>r.id==='top_to_30').src[2];
for(const floor of [30,20,10]) {
  const down=routes.find(r=>r.id===`top_to_${floor}`),up=routes.find(r=>r.id===`floor_${floor}_to_top`);
  assert.equal(down.lock,`enter_lap${floor+1}`,'Descending entry gate unlocks its lounge');
  assert.equal(down.dst[2],(floor-1)*384+192);assert.equal(up.dst[2],top);assert.equal(up.zone,'roof_zone');
  assert.equal(up.lock,'','Returning upstairs never requires finishing the descent');
}
assert.equal(routes.find(r=>r.id==='crown_to_base').lock,'enter_lap1');
assert.equal(routes.find(r=>r.id==='base_to_crown').zone,'crown_zone');
assert(!/"targetname" "tpbay_zone"|"targetname" "tod_door_tpbay"|tp bay wall [WES]/.test(map),'Old room and door removed');
assert(!/add_adjacent_zone\( "base_zone", "tpbay_zone"/.test(read('scripts/zm/zm_tod2_cybercity.gsc')));
const kit=require('./art_cohesion/crown_materials.json').materials;
for(const m of map.matchAll(/^\/\/ brush \d+ [^\n]*transit (?:bay|return)[^\n]*\r?\n\{([\s\S]*?)^\}/gm))
  for(const f of m[1].matchAll(/\) tod_cc_(\w+) (\d+) (\d+) /g))
    assert(+f[2]===kit[f[1]].size&&+f[3]===kit[f[1]].size,'Transit texture scale matches the crown kit');

const brushes=[...map.matchAll(/^\/\/ brush \d+ [^\n]*\r?\n\{([\s\S]*?)^\}/gm)]
  .map(m=>C.readPlanes(m[1])).filter(ps=>ps.length>=4).map(ps=>({ps,h:C.hull(ps)}));
function clearFloor(org,margin) {
  // Independent emitted-solid test: support under each sampled capsule point,
  // with 70 units of headroom (including the highest 1-unit inset deck).
  const near=brushes.filter(b=>b.h.lo[2]<org[2]+72&&b.h.hi[2]>org[2]-18&&
    b.h.lo[0]<=org[0]+margin&&b.h.hi[0]>=org[0]-margin&&b.h.lo[1]<=org[1]+margin&&b.h.hi[1]>=org[1]-margin);
  for(const [x,y] of [[0,0],...[...Array(16)].map((_,i)=>[Math.cos(i*Math.PI/8)*margin,Math.sin(i*Math.PI/8)*margin])]) {
    const spans=near.map(b=>C.verticalSpan(b.ps,org[0]+x,org[1]+y)).filter(Boolean);
    const floor=spans.filter(s=>Math.abs(s[1]-org[2])<=2).map(s=>s[1]);
    assert(floor.length,`Unsupported pad/arrival ${org} offset ${x},${y}`);
    const z=Math.max(...floor);assert(!spans.some(s=>s[0]<z+70&&s[1]>z+2),`Blocked pad/arrival ${org}`);
  }
}
for(const r of routes) {clearFloor(r.src,84);clearFloor(r.dst,66);
  for(const other of routes)if(Math.abs(other.src[2]-r.dst[2])<80)
    assert(Math.hypot(other.src[0]-r.dst[0],other.src[1]-r.dst[1])>=120+48+16,`${r.id} arrival enters ${other.id} gather`);
}
for(let i=0;i<routes.length;i++)for(let j=i+1;j<routes.length;j++)
  if(Math.abs(routes[i].src[2]-routes[j].src[2])<96)
    assert(Math.hypot(routes[i].src[0]-routes[j].src[0],routes[i].src[1]-routes[j].src[1])>=220,'Pad use triggers overlap');

// Execute the shipping gating and preparation functions with engine calls stubbed.
const body=(s,n)=>s.match(new RegExp('function '+n+'\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\}'))[1];
const defined=v=>v!==undefined&&v!==null,yes=v=>v===true;
const level={zones:{roof_zone:{is_enabled:true}}},logs=[];
const ready=new Function('level','isdefined','IS_TRUE','route',body(src,'destination_ready')).bind(null,level,defined,yes);
assert(ready({zone:'roof_zone'}));assert(!ready({zone:'missing'}));level.zones.roof_zone.is_enabled=false;assert(!ready({zone:'roof_zone'}));level.zones.roof_zone.is_enabled=true;
let opens=0,returns=0,allowDoor=true,allowReturn=true;
const prep=new Function('destination_ready','doors','fall','transit_log','route',body(src,'prepare_arrival')
  .replace(/tod_doors::force_open_by_flag/g,'doors.open').replace(/tod_fall::open_for_transit_return/g,'fall.open'))
  .bind(null,ready,{open:()=>{opens++;return allowDoor;}},{open:()=>{returns++;return allowReturn;}},m=>logs.push(m));
assert(prep({id:'test',zone:'roof_zone',arrival_flag:'',return_crown:false}));assert.equal(opens,0);
assert(!prep({id:'test',zone:'missing',arrival_flag:'door',return_crown:true}));assert.equal(opens,0);
assert(prep({id:'test',zone:'roof_zone',arrival_flag:'door',return_crown:true}));assert.equal(returns,1);
allowDoor=false;assert(!prep({id:'test',zone:'roof_zone',arrival_flag:'door',return_crown:true}));assert.equal(returns,1);
allowDoor=true;allowReturn=false;assert(!prep({id:'test',zone:'roof_zone',arrival_flag:'door',return_crown:true}));
const flags={exists:k=>k==='power_on'||k==='reached',get:k=>k==='power_on'};
const lock=new Function('flags','isdefined','lock_flag',body(src,'pad_lock_reason').replace(/level flag::/g,'flags.')).bind(null,flags,defined);
assert.equal(lock(''),0);assert.equal(lock(undefined),0);assert.equal(lock('reached'),2);assert.equal(lock('missing'),2,'Missing destination flag fails closed');
flags.get=()=>true;assert.equal(lock('reached'),0);flags.get=()=>false;assert.equal(lock(''),1);

// Returning reopens collision/pathing AND restores spawning/respawns, once.
const fallSrc=read('scripts/zm/zm_tod2_cybercity/_tod_fall.gsc');
const state={zones:{crown_zone:{is_spawning_allowed:false}},notify(){}},points=[{script_noteworthy:'crown_zone',locked:true},{script_noteworthy:'roof_zone',locked:true}];
let restored=0;const slab={NotSolid(){restored++;},ConnectPaths(){restored++;},Hide(){restored++;}};
const restore=new Function('level','isdefined','IS_TRUE','release_spawns','alarm_stop','getPoints','fall_log',
  'let pts,n,i;'+body(fallSrc,'open_for_transit_return').replace(/TOD_FALL_ZONE/g,'"crown_zone"')
    .replace(/level thread alarm_stop\(\)/g,'alarm_stop()').replace(/level notify\(/g,'level.notify(')
    .replace(/level\.tod_fall_slab (NotSolid|ConnectPaths|Hide)\(/g,'level.tod_fall_slab.$1(')
    .replace(/struct::get_array\([^)]*\)/g,'getPoints()').replace(/pts\.size/g,'pts.length'))
  .bind(null,state,defined,yes,()=>{},()=>{},()=>points,()=>{});
assert.equal(restore(),false,'Missing gate denies return');state.tod_fall_slab=slab;
assert(restore());assert(restore());assert.equal(restored,3,'Restore is idempotent');
assert.equal(state.tod_fall_phase,false);assert.equal(state.zones.crown_zone.is_spawning_allowed,true);
assert.equal(points[0].locked,false);assert.equal(points[1].locked,true);
const guard=new Function('level','IS_TRUE','return function*(){'+body(fallSrc,'hall_spawn_guard')
  .replace(/level endon\([^;]+;/g,'').replace(/wait 0.5;/g,'yield;')+'}').call(null,state,yes)();
guard.next();assert(guard.next().done,'Sealed-zone watchdog stops after the return');
for(const f of ['_tod_endless_rounds.gsc','_tod_doppelghast.gsc'])assert(read('scripts/zm/zm_tod2_cybercity/'+f).includes('!IS_TRUE( level.tod_fall_return_open )'),'Enemy filters honor crown return');
assert(body(src,'do_teleport').indexOf('prepare_arrival( route )')<body(src,'do_teleport').indexOf('SetOrigin('),'Prepare before moving riders');
assert(!fallSrc.includes('tele = Spawn( "script_model", tod_crown_data::crown_tele_org() )'),'No duplicate crown prop');

const sample=[{id:'top_to_40',src:[1,0,0],dst:[2,0,0],zone:'lap40_zone'}],ref=()=>[0,0,0];
const under=p=>p[0]===0?0:p[0]===1?1:2;
assert.equal(contract.nativeCheck(sample,under,[0,0,0],ref).length,0);
assert(contract.nativeCheck(sample,()=>-1,[],ref).length,'Missing compiled mesh rejected');
assert(contract.nativeCheck(sample,under,[0,1,0],ref).length,'Detached pad rejected');
console.log('TOWER_TRANSIT_PASS: 8 emitted/runtime routes; pad and arrival clearance; reached-floor locks; live-zone guards; crown gate/spawn/respawn restore; stale/missing navmesh rejection. Native playtest pending.');
