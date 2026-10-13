#!/usr/bin/env node
'use strict';
// Executes staged provider policy against explicit native doubles. Engine
// animation notes, DObj replication and sound delivery still need native build
// plus the user's playtest; this gate makes no rendering/audio quality claim.
const fs = require('fs');
const path = require('path');
const {gscLoad} = require('../sky_ships/gsc_eval');
const read = n => fs.readFileSync(path.join(__dirname,'../../scripts/zm/zm_tod2_cybercity',n),'utf8').replace(/\r\n/g,'\n');
const GSC=read('_tod_wunderfizz_machine.gsc'), CSC=read('_tod_wunderfizz_machine.csc');
const D=Object.fromEntries([...GSC.matchAll(/^#define\s+(\w+)\s+(\d+)/gm)].map(m=>[m[1],+m[2]]));
let ok=0,fail=0;
function check(v,label){if(v){ok++;console.log('ok '+label);}else{fail++;console.error('FAIL '+label);}}
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function lower(s,client=false){
  s=s.replace(/\bfunction prompt_and_visibility\( p \)/,'function prompt_and_visibility( self, p )');
  if(client)s=s.replace(/\bfunction idle_cb\( /,'function idle_cb( self, ');
  s=s.replace(/#animtree/g,'"generic"');
  s=s.replace(/&(present|prompt_and_visibility|use_loop)/g,'"$1"');
  s=s.replace(/self endon\(\s*/g,'NativeEndon( self, ');
  s=s.replace(/level thread (world_watch|end_game_watch)\(\s*\)/g,'ScheduleWorldWatch( "$1" )');
  s=s.replace(/level thread idle_shutdown_watch\(\s*/g,'ScheduleShutdownWatch( ');
  s=s.replace(/host waittill\(\s*/g,'WaitShutdown( host, ');
  s=s.replace(/m\.host thread zm_audio::sndPerksJingles_Player\(\s*/g,'NativeJingle( m.host, ');
  s=s.replace(/m\.host thread animation::play\(\s*/g,'ScheduleNativePlay( m.host, ');
  s=s.replace(/\[\[\s*level.custom_vending_precaching\s*\]\]\(\s*\)/g,'NativeCustomPrecache()');
  const native={SetModel:'NativeModel',useanimtree:'NativeAnimTree',
    'clientfield::set':'NativeField','animation::play':'NativePlay','animation::stop':'NativeStop',
    PlaySound:'NativeSound',IPrintLn:'NativeText',PlayLoopSound:'NativeLoop',StopLoopSound:'NativeStopLoop',
    Delete:'NativeDelete',notify:'NativeNotify',GetEntityNumber:'NativeClient',GetTagOrigin:'NativeTagOrigin',
    'util::waittill_dobj':'WaitDObj',SetHintString:'NativeHint',NotSolid:'NativeNotSolid'};
  for(const [from,to]of Object.entries(native)){
    const esc=from.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    s=s.replace(new RegExp('(\\b(?:m\\.host|host|p|self))\\s+'+esc+'\\(\\s*','g'),(_,p)=>to+'( '+p+', ');
  }
  s=s.replace(/\(\s*(m\.host|host|p|self),\s*\)/g,'( $1 )');
  return s;
}
function load(gsrc=GSC,csrc=CSC){
  const events=[],watches=[],logs=[],world=[];
  let now=0,g,onDObj;
  const isdefined=x=>x!==undefined&&!(x&&x.deleted);
  const B={
    IS_TRUE:x=>x===true||x===1,isdefined,min:Math.min,IsAlive:p=>!!p.alive,IsPlayer:p=>!!p.player,
    GetTime:()=>now,GetArrayKeys:Object.keys,
    DistanceSquared:(a,b)=>a.reduce((n,v,i)=>n+(v-b[i])**2,0),GetAnimLength:()=>4,
    NativeClient:p=>p.client,NativeEndon:()=>{},
    Spawn:(type,o,flags)=>g.spawnEnabled===false?undefined:({id:100+events.length,origin:o}),
    NativeNotSolid:h=>{h.notSolid=true;events.push(['notsolid',h.id]);},
    NativeModel:(h,n)=>{events.push(['model',h.id,n]);h.model=n;},
    NativeAnimTree:(h,n)=>events.push(['tree',h.id,n]),
    NativeTagOrigin:(h,n)=>{
      const yaw=h.angles[1]*Math.PI/180;
      const org=[h.origin[0]+50.192905*Math.cos(yaw),h.origin[1]+50.192905*Math.sin(yaw),h.origin[2]+53.877693];
      events.push(['tagorigin',h.id,n,org]);return org;
    },
    NativeField:(h,n,v)=>events.push(['field',h.id,n,v]),
    NativePlay:(h,...args)=>{if(g.nativePlayBlocks)throw new Error('native play waits for scriptedanim');events.push(['play',h.id,...args]);},
    ScheduleNativePlay:(h,...args)=>{events.push(['threadplay',h.id]);events.push(['play',h.id,...args]);},
    NativeStop:(h,n)=>events.push(['stop',h.id,n]),
    NativeSound:(p,n)=>events.push(['sound',p.client,n]),NativeText:(p,n)=>events.push(['text',p.client,n]),
    NativeLoop:(h,n)=>events.push(['loop',h.id,n]),NativeStopLoop:h=>events.push(['stoploop',h.id]),
    NativeDelete:h=>{events.push(['delete',h.id]);h.deleted=true;},
    NativeNotify:(h,n)=>events.push(['notify',h.id,n]),NativeHint:(t,s)=>{events.push(['hint',s]);t.hint=s;},
    NativeJingle:(h,k)=>events.push(['jingle',h.id,k]),
    'util::spawn_model':(n,o,a)=>({id:100+events.length,model:n,origin:o,angles:a}),
    'zm_unitrigger::unregister_unitrigger':s=>events.push(['unregister',Object.keys(s.playertrigger||{})]),
    'zm_unitrigger::unitrigger_force_per_player_triggers':(s,on)=>{s.trigger_per_player=on;},
    'zm_unitrigger::register_static_unitrigger':s=>events.push(['register',s.machine.floor,!!g.backendInit]),
    'tod_wunderfizz_data::nodes':()=>g.nodes,
    'tod_wunderfizz::init':()=>{g.backendInit=true;events.push(['backendinit']);},
    'zm_perks::default_vending_precaching':()=>{events.push(['defaultprecache']);g.level.machine_assets.native=true;g.level._effect.widows_wrap='native-wrap';},
    NativeCustomPrecache:()=>{events.push(['customprecache']);g.level.machine_assets.custom=true;},
    'tod_wunderfizz::cancel':(p,seq,why)=>{events.push(['cancel',p.client,seq,why]);p.tod_wf_tx.finished=true;},
    'tod_wunderfizz_machine::dev_log':s=>logs.push(s),
    'tod_wunderfizz::state':p=>({...validState,...p.state}),
    'tod_wunderfizz::snapshot':p=>({...quote,...p.quote}),
    'tod_wunderfizz::refusal_from_state':s=>s.refusal||'',
    ScheduleWorldWatch:n=>world.push(n),
    ScheduleShutdownWatch:(h,s,lcn)=>watches.push({h,s,lcn}),WaitShutdown:()=>{},
    WaitDObj:(h,lcn)=>{if(onDObj){const hook=onDObj;onDObj=undefined;hook(h,lcn);}},
    PlayFXOnTag:(lcn,fx,h,tag)=>{const id=events.length+1;events.push(['fx',lcn,fx,h.id,tag,id]);return id;},
    StopFX:(lcn,id)=>events.push(['stopfx',lcn,id]),
  };
  g=gscLoad([['tod_wunderfizz_machine',lower(gsrc)],['client',lower(csrc,true)]],D,{builtins:B,random:()=>0.5});
  g.level._effect={tod_wunderfizz_idle:'_t10/vending/fizz_idle'};
  g.events=events;g.logs=logs;g.watches=watches;g.world=world;
  g.setNow=n=>{now=n;};g.onDObj=f=>{onDObj=f;};
  return g;
}
const validState={alive:true,downed:false,drafted:true,menu:false,reviving:false,power:true};
const quote={owned:0,available:511,cost:2000};
function player(client){const p={player:true,alive:true,client,score:10000,origin:[0,0,0]};p.tod_wf_tx={p,seq:client+1,finished:false,granted:false,debit:2000};return p;}
function machine(id=1){return {id,floor:id,org:[0,0,0],yaw:0,trig:[83.240486,0,53.877693],r:32,live:true,powered:true,model_power:true,hum:false,want_hum:false,queue:[],anim_busy:false,buyers:0,next_jingle:1e9,rekicked:false,rekick_pending:false,host:{id,origin:[0,0,0],angles:[0,0,0]},stub:{playertrigger:[]}};}
const call=(g,n,a)=>g.call('tod_wunderfizz_machine::'+n,a);

function startupOrdered(source){
  const g=load(source);g.nodes=[machine(1),machine(2)];call(g,'init',[]);
  return g.events.filter(e=>e[0]==='register').every(e=>e[2])&&!!g.backendInit;
}
check(startupOrdered(GSC),'actual provider init starts backend before registering either counter');
check(!startupOrdered(GSC.replace('tod_wunderfizz::init();','')),'negative control rejects a provider with no backend initialization');
function sparseMilestones(source){
  const g=load(source),floors=[40,10,30,20];
  g.nodes=floors.map((floor,i)=>{
    const m=machine(floor);m.org=[i*30,0,(floor-1)*384+192];m.yaw=60;
    return m;
  });
  try{call(g,'init',[]);}catch(e){return false;}
  const created=g.events.filter(e=>e[0]==='register').map(e=>e[1]);
  return same(created,floors)&&g.level.tod_wf_machines.length===4&&g.nodes.every((m,i)=>m.id===floors[i]&&m.floor===floors[i]&&m.live&&m.host&&m.stub.machine===m);
}
check(sparseMilestones(GSC),'four haven descriptors retain sparse floor identities 10/20/30/40 without dense-ID indexing or extra hosts');
check(!sparseMilestones(GSC.replace('foreach ( m in level.tod_wf_machines )\n    {','foreach ( m in level.tod_wf_machines )\n    {\n        m = level.tod_wf_machines[ m.id ];')),'negative control catches floor IDs incorrectly treated as descriptor-array indexes');
function nativeHintTarget(source){
  const g=load(source);
  g.nodes=[0,90,180,270,240].map((yaw,i)=>{
    const m=machine(i+1),r=yaw*Math.PI/180;m.yaw=yaw;m.org=[i*100,i*-150,i*384];
    m.trig=[m.org[0]+83.240486*Math.cos(r),m.org[1]+83.240486*Math.sin(r),m.org[2]+53.877693];
    return m;
  });
  const stand=g.nodes.map(m=>m.trig.slice());call(g,'init',[]);
  const tags=g.events.filter(e=>e[0]==='tagorigin');
  return tags.length===g.nodes.length&&g.nodes.every((m,i)=>{
    const native=tags.find(e=>e[1]===m.host.id);
    return native&&native[2]==='tag_hint'&&same(m.stub.origin,native[3])&&!same(m.stub.origin,m.trig)&&same(m.trig,stand[i]);
  });
}
check(nativeHintTarget(GSC),'native use origin consumes model tag_hint at all floor orientations while preserving purchaser range/nav point');
check(!nativeHintTarget(GSC.replace('m.stub.origin = m.host GetTagOrigin( "tag_hint" );','m.stub.origin = m.trig;')),'negative control catches native look target moved beneath standing purchaser');
function nonblockingLaunch(source){
  const g=load(source),m=machine(1),other=machine(2),p=player(0);
  // Model the stock helper as a yielding call. The GSC thread scheduler is
  // lowered separately, so a presentation caller cannot invoke it directly.
  g.nativePlayBlocks=true;
  call(g,'present',[p,m,'purchase','perkA']);call(g,'present',[p,other,'purchase','perkB']);
  try{call(g,'presentation_tick',[m,0]);call(g,'presentation_tick',[other,0]);}catch(e){return false;}
  return g.events.filter(e=>e[0]==='threadplay').length===2&&m.anim_end===4100&&other.anim_end===4100;
}
check(nonblockingLaunch(GSC),'yielding native animation helper cannot suspend presentation ticks for another counter');
check(!nonblockingLaunch(GSC.replace('m.host thread animation::play(', 'm.host animation::play(')),'negative control catches synchronous stock animation helper launch');
{
  const g=load();
  check(call(g,'ensure_perk_precache',[])&&g.level.machine_assets.native&&g.level._effect.widows_wrap==='native-wrap','no-vendor stock early return is repaired through original default player-effect precache');
  const n=g.events.length;check(!call(g,'ensure_perk_precache',[])&&g.events.length===n,'existing machine-assets table never runs default precache twice');
  const custom=load();custom.level.custom_vending_precaching='original-hook';
  check(call(custom,'ensure_perk_precache',[])&&custom.level.machine_assets.custom&&!custom.level.machine_assets.native,'no-vendor custom precache hook preserved instead of default');
  const cn=custom.events.length;call(custom,'ensure_perk_precache',[]);
  check(custom.events.length===cn&&custom.level.custom_vending_precaching==='original-hook','original custom hook remains installed and is called once');
  const already=load();already.level.machine_assets={stock:'preserve'};already.level.custom_vending_precaching='original-hook';
  check(!call(already,'ensure_perk_precache',[])&&already.events.length===0&&already.level.machine_assets.stock==='preserve','stock-completed precache records preserved without replaying either hook');
  const bad=load(GSC.replace('else zm_perks::default_vending_precaching();',''));
  call(bad,'ensure_perk_precache',[]);
  check(bad.level._effect.widows_wrap===undefined,'negative control catches missing no-vendor player-effect precache');
}
{
  const g=load(),m=machine();g.spawnEnabled=false;
  check(call(g,'spawn_host',[m,false])===undefined&&g.events.length===0,'exhausted entity pool returns safely before any native model method');
  g.spawnEnabled=true;const h=call(g,'spawn_host',[m,true]);
  check(h.notSolid&&h.scale===1&&h.model==='t10_zm_machine_wunderfizz_fxanim_on','actual spawn produces exact on mesh with authored scale and no duplicate collision');
}

{
  const g=load();
  check(same(call(g,'audible_indices',[[]]),[]),'empty map requests no hum');
  check(same(call(g,'audible_indices',[[360001,2147483647]]),[]),'outside original600-unit wet range is silent');
  check(same(call(g,'audible_indices',[[360000]]),[0]),'original maximum range is inclusive');
  check(same(call(g,'audible_indices',[[9,1,4,16,25,36,49,64]]),[1,2,0,3,4,5]),'closest six win; distant first requests cannot consume global cap');
  check(same(call(g,'audible_indices',[[1,1,1,1,1,1,1]]),[0,1,2,3,4,5]),'stable ties prevent hum lease flicker');
  for(let n=0;n<=50;n++){
    const a=Array.from({length:n},(_,i)=>((i*157+13)%997)**2);
    const expected=a.map((d,i)=>({d,i})).filter(x=>x.d<=360000).sort((a,b)=>a.d-b.d||a.i-b.i).slice(0,6).map(x=>x.i);
    check(same(call(g,'audible_indices',[a]),expected),'voice policy exact sort n='+n);
  }
  check(!same(call(load(GSC.replace('rank < TOD_WF_HUM_LIMIT','rank <= TOD_WF_HUM_LIMIT')),'audible_indices',[[1,2,3,4,5,6,7]]),[0,1,2,3,4,5]),'negative control catches seventh simultaneous hum');
}
{
  const g=load(),m=machine(),a=player(0),b=player(1),other=machine(2);
  call(g,'present',[a,m,'purchase','perkA']);call(g,'present',[b,m,'purchase','perkB']);
  call(g,'present',[a,other,'purchase','perkC']);
  check(m.queue.length===2&&other.queue.length===1,'same-counter co-op and another floor have separate visual queues');
  check(a.score===10000&&b.score===10000&&a.tod_wf_tx.finished===false,'presentation never debits, refunds, finishes or blocks transaction');
  call(g,'presentation_tick',[m,0]);call(g,'presentation_tick',[other,0]);
  check(g.events.filter(e=>e[0]==='play').length===2&&m.queue.length===1,'different counters activate together; same counter serializes');
  const native=g.events.find(e=>e[0]==='play');
  check(native[2]==='t10_zm_machine_wunderfizz_fxanim_activate'&&same(native.slice(-3),[1,0,0]),'exact native clip with zero early blend-out preserves final note');
  call(g,'presentation_tick',[m,4000]);
  check(m.queue.length===1&&g.events.filter(e=>e[0]==='play'&&e[1]===1).length===1,'no overlap before authored final frame plus server guard');
  call(g,'presentation_tick',[m,4100]);
  check(m.queue.length===0&&g.events.filter(e=>e[0]==='play'&&e[1]===1).length===2,'queued co-op activation follows original completion');
  check(g.events.some(e=>e[0]==='stop'&&e[2]===0),'normal completion restores host without an early blend-out');
  check(!g.events.some(e=>e[0]==='sound'&&/^evt_wunderfizz_/.test(e[2])),'script never duplicates authored activation/electricity/spark audio');
}
{
  const g=load(),m=machine(),p=player(0);
  call(g,'present',[p,m,'purchase','perk']);p.tod_wf_tx.finished=true;
  call(g,'presentation_tick',[m,0]);
  check(m.queue.length===0&&!m.anim_busy,'cancelled/refunded pending presentation is pruned');
  p.tod_wf_tx.granted=true;call(g,'present',[p,m,'purchase','perk']);
  call(g,'presentation_tick',[m,100]);
  check(m.anim_busy,'successfully finished grant retains its queued presentation');
  const lost=player(1);lost.tod_wf_tx.p=undefined;call(g,'present',[lost,m,'purchase','perk2']);
  call(g,'prune_queue',[m]);check(m.queue.length===0,'deleted disconnected entity leaves no queued activation');
  call(g,'present',[p,m,'interrupt','perk']);
  check(g.events.some(e=>e[0]==='text'&&e[2].includes('Purchase cancelled'))&&g.events.some(e=>e[0]==='sound'&&e[2]==='zmb_no_purchase'),'interrupt reports visible/audible cancellation after menu close');
}
{
  const g=load(),m=machine(),p=player(0);m.hum=true;m.anim_busy=true;m.buyers=1;
  const live={id:8},dead={id:9,deleted:true};m.stub.playertrigger[0]=live;m.stub.playertrigger[1]=undefined;m.stub.playertrigger[2]=dead;
  p.tod_wf_tx.machine=m;g.level.tod_wf_sessions=[p.tod_wf_tx];
  call(g,'retire',[m,'host_lost']);
  check(!m.live&&!m.host&&!m.hum&&!m.anim_busy&&m.queue.length===0,'forced host loss releases all presentation state');
  check(g.events.some(e=>e[0]==='cancel'&&e[3]==='host_lost'),'host loss explicitly cancels the associated live purchase');
  check(same(g.events.find(e=>e[0]==='unregister')[1],['0']),'undefined/deleted player-trigger holes removed before native unregister');
  const order=g.events.map(e=>e[0]);
  check(order.indexOf('field')<order.indexOf('delete')&&order.indexOf('stoploop')<order.indexOf('delete')&&order.indexOf('stop')<order.indexOf('delete'),'host deletion follows idle0, hum stop and forced animation stop');
  const count=g.events.length;call(g,'retire',[m,'again']);check(g.events.length===count,'retirement idempotent');
}
{
  const g=load(),m=machine();m.powered=false;m.model_power=false;m.anim_busy=true;m.anim_end=4100;
  call(g,'apply_power',[m,true]);
  check(m.powered&&!m.model_power&&!g.events.some(e=>e[0]==='model'),'power arriving mid pre-power QR clip preserves its DObj/native notes');
  call(g,'presentation_tick',[m,4100]);
  check(m.model_power&&g.events.some(e=>e[0]==='model'&&e[2]==='t10_zm_machine_wunderfizz_fxanim_on'),'on model lands at native completion');
  const old=m.host,p=player(0);p.tod_wf_tx.machine=m;g.level.tod_wf_sessions=[p.tod_wf_tx];m.hum=true;
  call(g,'apply_power',[m,false]);
  check(old.deleted&&m.host!==old&&m.host.model==='t10_zm_machine_wunderfizz_fxanim'&&!m.hum,'power loss rebuilds exact off host and destroys authored attached FX owner');
  check(g.events.some(e=>e[0]==='cancel'&&e[3]==='power'),'power loss cancels/refunds through authoritative backend');
}
{
  const g=load(),nodes=Array.from({length:10},(_,i)=>{const m=machine(i+1);m.org=[i*30,0,0];return m;}),p=player(0);
  call(g,'sound_tick',[nodes,[p],0]);
  check(nodes.filter(m=>m.hum).length===6,'ten nearby powered machines request only six exact native loops');
  const count=g.events.filter(e=>e[0]==='loop').length;call(g,'sound_tick',[nodes,[p],500]);
  check(g.events.filter(e=>e[0]==='loop').length===count,'stable proximity does not restart sounds every heartbeat');
  p.origin=[10000,0,0];call(g,'sound_tick',[nodes,[p],1000]);
  check(nodes.every(m=>!m.hum),'leaving audible range releases every global voice');
  nodes.forEach(m=>{m.powered=false;});p.origin=[0,0,0];call(g,'sound_tick',[nodes,[p],1500]);
  check(nodes.every(m=>!m.hum),'unpowered models never own humming loops');
}
{
  const g=load(),m=machine(),p=player(0),t={stub:{machine:m}};
  check(call(g,'prompt_and_visibility',[t,p]),'ready native per-player trigger visible');
  const n=g.events.length;call(g,'prompt_and_visibility',[t,p]);check(g.events.length===n,'unchanged prompt does not repeatedly allocate hint strings');
  p.tod_wf_menu_active=true;check(!call(g,'prompt_and_visibility',[t,p]),'selector hides only its owner prompt');
  p.tod_wf_menu_active=false;p.state={power:false};p.quote={available:4};
  check(call(g,'prompt_and_visibility',[t,p])&&t.hint.includes('Hold'),'stock solo pre-power QR exception still has usable selector');
  p.quote={available:0};call(g,'prompt_and_visibility',[t,p]);check(t.hint.includes('Power required'),'co-op before power communicates power requirement');
  p.quote={owned:511};call(g,'prompt_and_visibility',[t,p]);check(t.hint.includes('All perks owned'),'fully owned roster gives clear world feedback');
  check(new Set(['ready','power','owned','busy','other'].map(k=>call(g,'hint_for_state',[k]))).size===4,'only four static noun-first hint-table entries');
}
{
  const g=load(),host={id:42};
  g.call('client::idle_cb',[host,0,0,1,false,false,'todWunderfizzIdle',false]);
  g.call('client::idle_cb',[host,1,0,1,false,false,'todWunderfizzIdle',false]);
  const a=host.tod_wf_idle_states[0].handle,b=host.tod_wf_idle_states[1].handle;
  check(a!==b&&g.watches.length===2,'separate local-client idle handles and detached shutdown owners');
  g.call('client::idle_cb',[host,0,1,0,false,false,'todWunderfizzIdle',false]);
  check(host.tod_wf_idle_states[0].handle===undefined&&host.tod_wf_idle_states[1].handle===b,'idle0 stops only that client handle');
  const watch=g.watches[1];host.deleted=true;g.call('client::idle_shutdown_watch',[host,watch.s,watch.lcn]);
  check(watch.s.handle===undefined&&g.events.some(e=>e[0]==='stopfx'&&e[1]===1&&e[2]===b),'detached host-loss watcher retains and stops live idle handle');
}
function staleGuard(csrc){
  const g=load(GSC,csrc),h={id:52};
  g.onDObj((host,lcn)=>g.call('client::idle_cb',[host,lcn,1,0,false,false,'todWunderfizzIdle',false]));
  g.call('client::idle_cb',[h,0,0,1,false,false,'todWunderfizzIdle',false]);
  return !g.events.some(e=>e[0]==='fx');
}
check(staleGuard(CSC),'new idle0 while waiting for DObj cannot be undone by stale callback');
check(!staleGuard(CSC.replace('if ( generation != s.generation ) return;','')),'negative control detects stale callback relighting machine');
check(/register\( "scriptmover", "todWunderfizzIdle", VERSION_SHIP, 1, "int" \)/.test(GSC)&&/register\( "scriptmover", "todWunderfizzIdle", VERSION_SHIP, 1, "int", &idle_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT \)/.test(CSC),'server/client field contracts match and late joins replay');
check(/host\.scale = 1;/.test(GSC)&&/m\.stub\.radius = m\.r;/.test(GSC)&&/m\.stub\.origin = m\.host GetTagOrigin\( "tag_hint" \);/.test(GSC),'native authored scale, radius and model hint target are authoritative');
check(GSC.indexOf('tod_wunderfizz::init();')>=0&&GSC.indexOf('tod_wunderfizz::init();')<GSC.indexOf('register_static_unitrigger( m.stub'),'backend callbacks initialized before first native trigger');
check(GSC.indexOf('ensure_perk_precache();')>=0&&GSC.indexOf('ensure_perk_precache();')<GSC.indexOf('tod_wunderfizz::init();'),'native player-effect precache restored before backend or physical interaction');
check(/host NotSolid\(\);/.test(GSC)&&/if \( !isdefined\( host \) \) return undefined;\s*host SetModel/.test(GSC),'no duplicate model collision and exhausted native entity pool is guarded');
check(!/\bPlayFX(?:OnTag)?\s*\(/.test(GSC)&&!GSC.includes('PlaySound( "evt_wunderfizz_activate"'),'authored purchase FX/audio stay engine-owned');
check(/unitrigger_force_per_player_triggers\( m\.stub, true \)/.test(GSC)&&/require_look_at = true/.test(GSC),'native unitrigger is per-player and requires facing machine');
check(GSC.includes('Hold ^3[{+activate}]^7 ^5WUNDERFIZZ^7 - Choose a perk'),'ready hint uses existing prompt-card binding parser, noun title and hold footer');
check(!/\bendon\(/.test(GSC.slice(GSC.indexOf('function world_watch()'),GSC.indexOf('function retire('))),'level presentation owner cannot endon before cleanup');
console.log(`Machine candidate: ${ok} passed, ${fail} failed`);
process.exitCode=fail?1:0;
