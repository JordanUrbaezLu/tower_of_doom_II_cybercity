// Exercise the actual state-transition body with a mocked snapshot scheduler.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const root=path.resolve(__dirname,'../..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const server=read('scripts/zm/zm_tod2_cybercity/_tod_shop.gsc');
const client=read('scripts/zm/zm_tod2_cybercity/_tod_shop.csc');
const timing=read('scripts/zm/zm_tod2_cybercity/_tod_shop_timing.csc');
function body(source,name){const s=source.split('function '+name+'(')[1].split('\nfunction ')[0];return s.slice(s.indexOf('{'));}
let trans=body(server,'activate')
 .replace(/foreach \( (\w+) in ([^)]+) \)/g,'for (const $1 of $2)')
 .replace(/wait ([\d.]+);/g,'yield $1;')
 .replace(/\b(\w+) clientfield::set\(/g,'$1.setField(')
 .replace(/\b(\w+) (SetModel|Delete|Show|Hide|NotSolid|notify)\(/g,'$1.$2(')
 .replace(/\bp thread pressure_motion\(\);/g,'p.motion=true;')
 .replace(/\b(\w+(?:\.\w+)*)\.size\b/g,'$1.length')
 .replace(/\( (0|90|73), (-?\d+(?:\.\d+)?|s\.yaw), (-?\d+(?:\.\d+)?) \)/g,'[$1,$2,$3]');
function scenario(failAt=-1){
 const entities=[],logs=[];
 function model(){const m={SetModel(v){this.model=v;},Delete(){this.deleted=true;},Hide(){this.hidden=true;},Show(){this.hidden=false;},NotSolid(){},notify(){},setField(k,v){this.field=v;}};entities.push(m);return m;}
 const level={tod_shop_active:-1,tod_shop_busy:false,tod_dev:false,tod_shops:[0,1,2].map(id=>({id,origin:[0,0,0],yaw:0,parts:[],body:model()}))};
 let spawned=0;
 const ctx={level,undefined,IS_TRUE:x=>x===true,isdefined:x=>x!==undefined&&!x?.deleted,TOD_SHOP_LOG:1,array:(...a)=>a,Spawn:()=>spawned++===failAt?undefined:model(),local_to_world:()=>[0,0,0],log:s=>logs.push(s),spin_trigger_place:i=>{level.spin_at=i;}};
 vm.createContext(ctx);vm.runInContext('function* activate(index,reason){let previous,s,p,next,names,failed,j,offset,value;'+trans+'}',ctx);
 function run(index){const it=ctx.activate(index,'test');let r;const waits=[];while(!(r=it.next()).done)waits.push(r.value);return {result:r.value,waits};}
 return {ctx,level,entities,logs,run};
}
let s=scenario();assert.equal(s.run(0).result,true);assert.equal(s.level.tod_shop_active,0);assert.equal(s.level.tod_shops[0].parts.length,15);assert.equal(s.entities.filter(p=>!p.deleted&&!p.hidden&&p.field>0).length,12);
const old=[...s.level.tod_shops[0].parts];assert.equal(s.run(1).result,true);assert(old.every(p=>p.deleted&&p.field===0));assert.equal(s.level.tod_shops[0].body.model,'tod_shop_off');assert.equal(s.level.tod_shop_active,1);
assert.equal(s.level.spin_at,1);   // the BLACK MARKET SPIN trigger follows the active shop (docs/188)
assert.equal(s.run(-1).result,true);assert(s.level.tod_shops.every(p=>p.parts.length===0&&p.body.model==='tod_shop_off'));assert.equal(s.level.spin_at,-1);
assert.equal(s.run(3).result,false);s.level.tod_shop_busy=true;assert.equal(s.run(0).result,false);
s=scenario(5);assert.equal(s.run(0).result,false);assert.equal(s.level.tod_shop_active,-1);assert.equal(s.level.tod_shop_busy,false);assert(s.level.tod_shops.every(p=>p.parts.length===0));assert(s.entities.slice(3).every(p=>p.deleted));
s=scenario();s.level.tod_shops[1].body.Delete();assert.equal(s.run(1).result,false);assert.equal(s.level.tod_shop_busy,false);
// Actual generated sign lookup and actual client pulse math agree with the art contract.
const anim={Cos:v=>Math.cos(v*Math.PI/180),Sin:v=>Math.sin(v*Math.PI/180),tod_shop_timing:{}};vm.createContext(anim);
vm.runInContext('function power_bus(frame){let v;'+body(timing,'power_bus')+'}',anim);anim.tod_shop_timing.power_bus=anim.power_bus;
vm.runInContext('function letter(kind,frame){let v;'+body(timing,'letter')+'}',anim);anim.tod_shop_timing.letter=anim.letter;
vm.runInContext('function brightness(kind,frame){let phase;'+body(client,'brightness').replaceAll('tod_shop_timing::','tod_shop_timing.')+'}',anim);
for(const kind of [2,3,4]){let values=Array.from({length:181},(_,i)=>anim.brightness(kind,i+1));assert.equal(Math.max(...values),1);assert.equal(Math.min(...values),0);assert.equal(values[0],values[180]);}
assert(Array.from({length:180},(_,i)=>anim.brightness(1,i+1)).every(v=>v===1));
for(const kind of [5,6,7,8,9,10,11,12]){let v=Array.from({length:181},(_,i)=>anim.brightness(kind,i+1));if(kind===5)assert(Math.min(...v)>.025);else assert.equal(Math.min(...v),0);assert(Math.max(...v)<=1.00001);assert(Math.abs(v[0]-v[180])<1e-6);}
// Compare actual evaluated Blender emission to actual runtime code on every frame.
const evaluated=JSON.parse(read('art/partner_shop/electrical_evaluated.json'));
const samplesByKind={2:['neon letter T',5.5],3:['neon letter E',5.5],4:['neon letter C',5.5],5:['mask slow red breath',3.1],6:['left red energy core',3.3],7:['counter canister red pulse',2.5],8:['existing tall core red pulse',3.1]};
for(let i=0;i<4;i++)samplesByKind[9+i]=['left core scan '+i,3];
vm.runInContext('function pressure_angle(kind,phase)'+body(server,'pressure_angle'),anim);
for(const row of evaluated){
 for(const [kind,[mat,peak]] of Object.entries(samplesByKind)){
  const actual=anim.brightness(+kind,row.frame);
  assert.equal(actual>0,+kind===5||row.bus>0,'shared circuit / independent mask mismatch at frame '+row.frame+' kind '+kind);
  assert(Math.abs(actual-row.emission[mat]/peak)<1e-5,'art/runtime drift '+mat+' frame '+row.frame);
 }
 assert(Math.abs(anim.pressure_angle(14,(row.frame-1)*360/90)-row.valve_degrees)<1e-4);
}
assert.equal(anim.pressure_angle(14,0),0);assert.equal(anim.pressure_angle(14,180),100);
for(let frame=2;frame<=181;frame++)assert(Math.abs(anim.brightness(5,frame)-anim.brightness(5,frame-1))<.018,'mask pulse has an abrupt flash');
const events=JSON.parse(read('art/partner_shop/electrical_timing.json')).events;assert.equal(events.length,10);
for(const [_,org,f] of events){assert(timing.includes('.frame = '+f+';'));assert.equal(anim.power_bus(f),0);assert.equal(anim.power_bus(f-1),1);}
assert.deepEqual(events.filter(e=>e[0]==='right core').map(e=>e[2]),[31,91,151]);
const audio=JSON.parse(read('art/partner_shop/audio_manifest.json')).audio_events;
assert.deepEqual(audio.map(e=>e.frame),[31,91,151]);assert.equal(new Set(audio.map(e=>e.sound)).size,3);
const budget=Math.max(...[31,91,151].map(f=>events.filter(e=>e[2]===f).length))*6;assert.equal(budget,24);
assert(client.indexOf('fx = PlayFX(')<client.indexOf('self PlaySound('));assert(client.includes('tick - last_tick < 8'));assert(client.includes('!CF_CALLBACK_ZERO_ON_NEW_ENT'));assert(client.includes('"hdrScale"'));
assert(server.includes('wait 0.1; // model DObjs'));assert(server.includes('level thread end_cleanup();'));assert(server.includes('p clientfield::set( "todShopPart", 0 )'));
const data=read('scripts/zm/zm_tod2_cybercity/_tod_crown_data.gsc');const orgbody=body(data,'shop_orgs');let coords=[...orgbody.matchAll(/= \( ([-\d.]+), ([-\d.]+), ([-\d.]+) \)/g)].map(m=>m.slice(1).map(Number));assert.equal(coords.length,2);   // ONE hall shop + the balcony's display shop (user 2026-09-25)
assert(Math.hypot(coords[0][0]-coords[1][0],coords[0][1]-coords[1][1])>800);
const map=read('map_source/zm/zm_tod2_cybercity.map');for(let i=0;i<2;i++)for(let j=0;j<4;j++)assert(map.includes('crown item shop '+i+' hull '+j));assert(!map.includes('crown item shop 2 hull'));
assert(read('scripts/zm/zm_tod2_cybercity/_tod_shop.gsc').includes('% TOD_SHOP_CYCLE;'));assert(read('scripts/zm/zm_tod2_cybercity/_tod_shop.gsc').includes('#define TOD_SHOP_CYCLE 1'));
const gen=read('tools/gen_tower_map.js');assert(gen.includes('const CROWN_SHOPS = ['));assert(gen.includes('CROWN_SHOPS.forEach((p,i)=>c.push'));
const reg=/"scriptmover", "todShopPart", VERSION_SHIP, 5, "int"/;assert(reg.test(server)&&reg.test(client));
const zone=read('zone_source/zm_tod2_cybercity.zone');assert(zone.includes('include,tod_shop'));
assert(read('tools/sync_to_modtools.ps1').includes('"model_export\\tod_shop"'), 'guarded sync must deploy shop geometry and textures');
console.log('SHOP PASS: state handoff/off, allocation failure, missing body, guarded transitions, sign/pulse seams, sound/FX timeline, three spaced anchors and collision ownership.');
require('./test_client_sync.js');
