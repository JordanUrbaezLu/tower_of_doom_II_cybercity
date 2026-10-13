#!/usr/bin/env node
'use strict';
// Executes the installed GSC functions, with engine calls lowered
// to explicit natives. Tests policy/transaction state; no game/native animation
// claim is made. Engine waits/endons are checked structurally, not simulated.
const fs = require('fs');
const path = require('path');
const {gscLoad} = require('../sky_ships/gsc_eval');
const read = p => fs.readFileSync(path.join(__dirname,'../../scripts/zm/zm_tod2_cybercity',p),'utf8').replace(/\r\n/g,'\n');
const WF = read('_tod_wunderfizz.gsc'), ROSTER = read('_tod_perk_roster.gsc');
const D = Object.fromEntries([...WF.matchAll(/^#define\s+(\w+)\s+(\d+)/gm)].map(m=>[m[1],+m[2]]));
let passes=0, fails=0;
function check(ok, label) { if(ok) {passes++; console.log('ok '+label);} else {fails++;console.error('FAIL '+label);} }
function same(a,b) {return JSON.stringify(a)===JSON.stringify(b);}
function body(src,name) {
  const m=new RegExp('\\bfunction\\s+'+name+'\\s*\\([^)]*\\)\\s*\\{').exec(src);
  if(!m) throw Error('Missing '+name);
  let i=m.index+m[0].length,depth=1;
  while(depth&&i<src.length) {if(src[i]==='{')depth++;if(src[i]==='}')depth--;i++;}
  return src.slice(m.index,i);
}
function lower(src) {
  const native={
    'HasPerk':'NativeHasPerk','zm_perks::has_perk_paused':'NativeHasPaused',
    'zm_utility::can_player_purchase_perk':'NativeCanPerk',
    'zm_score::can_player_purchase':'NativeCanPay','zm_score::minus_to_player_score':'NativeMinus',
    'zm_score::add_to_player_score':'NativeAdd','zm_perks::give_perk':'NativeGivePerk',
    'zm_perks::perk_abort_drinking':'NativeAbort','laststand::player_is_in_laststand':'NativeDown',
    'zm_weapons::switch_back_primary_weapon':'NativeRestore','HasWeapon':'NativeHasWeapon',
    'TakeWeapon':'NativeTakeWeapon','CloseLUIMenu':'NativeCloseMenu','LuiNotifyEvent':'NativeEvent',
    'notify':'NativeNotify'
  };
  let out=src.replace(/&"/g,'"');
  for(const [from,to] of Object.entries(native)) {
    const esc=from.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    out=out.replace(new RegExp('(\\b(?:tx\\.p|p|self))\\s+'+esc+'\\(\\s*','g'),(_,p)=>to+'( '+p+', ');
  }
  out=out.replace(/\(\s*(p|self|tx\.p),\s*\)/g,'( $1 )');
  out=out.replace(/level thread finish_cleanup\(\s*tx,\s*why\s*\)/g,'ScheduleCleanup( tx, why )');
  out=out.replace(/p thread drink_worker\(\s*tx\s*\)/g,'ScheduleDrink( p, tx )');
  return out;
}
function load(wf=WF, roster=ROSTER) {
  const events=[],logs=[],cleanup=[],drink=[],calls=[];
  let g;
  const builtins={
    IS_TRUE:x=>x!==undefined&&x!==null&&!!x, int:Math.trunc,
    IsAlive:p=>!!p.alive,
    NativeHasPerk:(p,k)=>!!(p.held&&p.held[k]),
    NativeHasPaused:(p,k)=>!!(p.paused&&p.paused[k]),
    NativeCanPerk:p=>p.canPerk!==false,
    NativeCanPay:(p,cost)=>p.score>=cost||!!p.shoppingFree,
    NativeMinus:(p,cost)=>{calls.push(['debit',cost]);if(!p.shoppingFree)p.score-=cost;return undefined;},
    NativeAdd:(p,amount,total)=>{calls.push(['refund',amount,total]);p.score+=amount;},
    NativeGivePerk:(p,k,bought)=>{calls.push(['give',k,bought]);p.held[k]=true;},
    NativeAbort:p=>{calls.push(['abort']);p.is_drinking--;p.controls=true;},
    NativeDown:p=>!!p.downed,
    NativeRestore:(p,w,immediate)=>{calls.push(['restore',w,immediate]);p.weapon=w;},
    NativeHasWeapon:(p,w)=>!!(p.weapons&&p.weapons[w]),
    NativeTakeWeapon:(p,w)=>{calls.push(['take',w]);delete p.weapons[w];},
    NativeCloseMenu:(p,m)=>{calls.push(['close',m]);},
    NativeEvent:(p,name,n,...values)=>events.push({p,name,n,values}),
    NativeNotify:(p,name,...args)=>calls.push(['notify',name,...args]),
    ScheduleCleanup:(tx,why)=>cleanup.push({tx,why}),
    ScheduleDrink:(p,tx)=>drink.push({p,tx}),
    'zm_perks::use_solo_revive':()=>!!g.level.solo,
    'tod_wunderfizz::state':p=>({...openState,...p.state}),
    'tod_wunderfizz::cue':(p,m,k,perk)=>calls.push(['cue',k,perk]),
    'tod_wunderfizz::dev_log':s=>logs.push(s),
    'tod_wunderfizz::snapshot':p=>({cost:g.call('tod_wunderfizz::price_from_count',[g.call('tod_perk_roster::owned_count',[p])]),owned:g.call('tod_perk_roster::owned_mask',[p]),available:511}),
    GetTime:()=>1000,
  };
  g=gscLoad([['tod_wunderfizz',lower(wf)],['tod_perk_roster',lower(roster)]],D,{builtins});
  g.level.tod_wf_seq=20;g.level.tod_wf_sessions=[];
  g.level._custom_perks=Object.fromEntries(keys.map(k=>[k,{perk_bottle_weapon:'can_'+k}]));
  g.events=events;g.logs=logs;g.cleanup=cleanup;g.drink=drink;g.calls=calls;
  g.flush=()=>{while(cleanup.length) {const c=cleanup.shift();g.call('tod_wunderfizz::finish_cleanup',[c.tx,c.why]);}};
  return g;
}
const keys=['specialty_armorvest','specialty_fastreload','specialty_quickrevive','specialty_staminup','specialty_widowswine','specialty_combat_efficiency','specialty_doubletap2','specialty_nomotionsensor','specialty_electriccherry'];
const openState={alive:true,downed:false,drafted:true,intermission:false,menu:false,world_pause:false,flying:false,grappling:false,mantling:false,grounded:true,ability:false,cloaked:false,reviving:false,swapping:false,powerup_weapon:false,drinking:false,haven_locked:false,machine_live:true,in_range:true,power:true,solo:false,lives:0};
function player(score=10000){return {score,held:{},paused:{},num_perks:999,canPerk:true,alive:true,weapons:{rifle:true},weapon:'rifle',is_drinking:0,controls:true};}
function session(g,p,op=1,m={floor:1,buyers:0}) {
  const n=g.call('tod_perk_roster::owned_count',[p]);
  const tx={p,machine:m,op,seq:op,client:op,phase:'menu',cost:2000+500*n,owned:g.call('tod_perk_roster::owned_mask',[p]),available:511,menu:'menu_'+op,finished:false,granted:false,refunded:false,debit:0};
  p.tod_wf_tx=tx;p.tod_wf_menu_active=true;m.buyers++;g.level.tod_wf_sessions[op]=tx;return tx;
}

const g=load();
check(same(g.call('tod_perk_roster::keys',[]),keys),'explicit nine roster identity/order');
check(new Set(keys).size===9,'one entry per perk, no obsolete registry additions');
check(same(Array.from({length:9},(_,i)=>g.call('tod_wunderfizz::price_from_count',[i])),[2000,2500,3000,3500,4000,4500,5000,5500,6000]),'all nine current-ownership prices');
for(let mask=0;mask<512;mask++){
  const p=player();for(let i=0;i<9;i++)if(mask&(1<<i)){if(i%2)p.held[keys[i]]=true;else p.paused[keys[i]]=true;}
  p.held.specialty_extra_registry_perk=true;p.num_perks=999;
  const n=Array.from({length:9},(_,i)=>!!(mask&(1<<i))).filter(Boolean).length;
  if(g.call('tod_perk_roster::owned_count',[p])!==n||g.call('tod_perk_roster::owned_mask',[p])!==mask){check(false,'all 512 held/paused masks');break;}
  if(mask===511)check(true,'all 512 held/paused masks count once, num_perks/unrelated perks ignored');
}
{
  const p=player();p.held[keys[0]]=true;p.paused[keys[0]]=true;
  check(g.call('tod_perk_roster::owned_count',[p])===1,'held plus paused same perk counted once');
  p.perk_purchased=keys[1];g.level._custom_perks.specialty_extra_registry_perk={};
  check(same(g.call('tod_perk_roster::free_pool',[p]),keys.slice(2)),'free bottle survives zero machine entities; excludes owned, paused, pending, unrelated registry');
  p.canPerk=false;check(g.call('tod_perk_roster::free_pool',[p]).length===0,'free bottle keeps stock perk-cap permission');
  p.canPerk=true;for(const k of keys)p.held[k]=true;
  check(g.call('tod_perk_roster::give_random',[p])===undefined,'full roster receives no duplicate free perk');
}
{
  const f=load(),p=player();for(const k of keys)if(k!==keys[2])p.held[k]=true;f.level.solo=true;
  check(f.call('tod_perk_roster::give_random',[p])===keys[2]&&f.level.solo_game_free_player_quickrevive===true,'solo free QR preserves free-use exemption');
  check(f.calls.some(c=>same(c,['give',keys[2],false])),'free bottle still uses stock give_perk with bought=false');
}
check(g.call('tod_wunderfizz::qr_paid_allowed',[true,undefined])===true&&g.call('tod_wunderfizz::qr_paid_allowed',[true,2])===true&&g.call('tod_wunderfizz::qr_paid_allowed',[true,3])===false&&g.call('tod_wunderfizz::qr_paid_allowed',[false,9])===true,'QR ledger: undefined/0..2 solo paid uses allowed, third exhausted, co-op independent');
for(let id=1;id<=9;id++){
  check(g.call('tod_wunderfizz::offer_allowed',[false,true,false,true,0,id])===(id===3),'power-off solo availability id='+id);
  check(!g.call('tod_wunderfizz::offer_allowed',[false,true,false,false,0,id]),'power-off co-op refuses id='+id);
  check(!g.call('tod_wunderfizz::offer_allowed',[true,true,true,false,0,id])&&!g.call('tod_wunderfizz::offer_allowed',[false,false,true,false,0,id]),'owned/unregistered refused id='+id);
}
check(!g.call('tod_wunderfizz::offer_allowed',[false,true,true,true,3,3]),'exhausted solo QR refused even with power');
check(g.call('tod_wunderfizz::cancel_allowed',[{seq:7,phase:'menu',finished:false},0])&&!g.call('tod_wunderfizz::cancel_allowed',[{seq:7,phase:'drink',finished:false},0]),'unhydrated close.0 closes only a current menu, never a charged drink');
check(!g.call('tod_wunderfizz::cancel_allowed',[{seq:7,phase:'menu',finished:false},6])&&!g.call('tod_wunderfizz::cancel_allowed',[{seq:7,phase:'menu',finished:true},7]),'stale or completed cancellation refused');
for(const s of ['', '0','10','-1','1.0','01','1junk','NaN','1e0'])check(g.call('tod_wunderfizz::response_id',[s])===0,'malformed UI ID rejected '+JSON.stringify(s));
for(let i=1;i<=9;i++)check(g.call('tod_wunderfizz::response_id',[''+i])===i,'exact UI ID '+i);
const refuses=[['alive',false,'down'],['downed',true,'down'],['drafted',false,'draft'],['intermission',true,'end_game'],['menu',true,'menu'],['world_pause',true,'menu'],['flying',true,'airborne'],['grappling',true,'airborne'],['mantling',true,'airborne'],['grounded',false,'airborne'],['ability',true,'ability'],['cloaked',true,'ability'],['reviving',true,'hands'],['swapping',true,'hands'],['powerup_weapon',true,'hands'],['drinking',true,'drink'],['haven_locked',true,'haven'],['machine_live',false,'machine'],['in_range',false,'range']];
check(g.call('tod_wunderfizz::refusal_from_state',[openState,false])==='','eligible player opens');
for(const [field,value,why]of refuses)check(g.call('tod_wunderfizz::refusal_from_state',[{...openState,[field]:value},false])===why,'state refusal '+field);
check(g.call('tod_wunderfizz::refusal_from_state',[{...openState,drinking:true},true])==='','own drink is not canceled as another drink');
check(g.call('tod_wunderfizz::refusal_from_state',[{...openState,downed:true,menu:true,grounded:false},true])==='down','down wins simultaneous state refusal');
const reserveCases=[['session',[undefined,1,1,'',false,true,true,2000]],['session',[{phase:'drink',seq:1,cost:2000},1,1,'',false,true,true,2000]],['stale',[{phase:'menu',seq:2,cost:2000},1,1,'',false,true,true,2000]],['perk',[{phase:'menu',seq:1,cost:2000},1,10,'',false,true,true,2000]],['perk',[{phase:'menu',seq:1,cost:2000},1,1.5,'',false,true,true,2000]],['down',[{phase:'menu',seq:1,cost:2000},1,1,'down',false,true,true,2000]],['owned',[{phase:'menu',seq:1,cost:2000},1,1,'',true,true,true,2000]],['offer',[{phase:'menu',seq:1,cost:2000},1,1,'',false,false,true,2000]],['quote',[{phase:'menu',seq:1,cost:2000},1,1,'',false,true,true,2500]],['points',[{phase:'menu',seq:1,cost:2000},1,1,'',false,true,false,2000]]];
for(const [why,args]of reserveCases)check(g.call('tod_wunderfizz::reserve_allowed',args)===why,'transaction recheck '+why);
for(const [why,want]of [['points',1],['stale',2],['quote',2],['owned',3],['offer',3],['range',4],['grant_failed',6]])check(g.call('tod_wunderfizz::result_code',[why])===want,'UI reason '+why);
{
  const f=load(),p=player(),tx=session(f,p);
  check(f.call('tod_wunderfizz::respond',[p,tx.seq,1])===''&&p.score===8000&&tx.debit===2000&&tx.phase==='drink','valid purchase reserves/debits once');
  check(p.perk_purchased===keys[0]&&f.drink.length===1,'pending perk and one worker reserved');
  check(f.call('tod_wunderfizz::respond',[p,tx.seq,1])==='session'&&p.score===8000&&f.drink.length===1,'repeated response cannot duplicate purchase');
}
{
  const f=load(),p=player(0),tx=session(f,p);p.shoppingFree=true;
  check(f.call('tod_wunderfizz::respond',[p,tx.seq,2])===''&&tx.debit===0&&p.score===0,'Shopping Free debit measured as zero (minus returns undefined)');
  f.call('tod_wunderfizz::finish',[tx,'down']);f.flush();
  check(p.score===0&&!f.calls.some(c=>c[0]==='refund'),'interrupted Shopping Free cannot mint price points');
}
{
  const f=load(),p=player(),tx=session(f,p);p.held[keys[7]]=true;
  check(f.call('tod_wunderfizz::respond',[p,tx.seq,1])==='quote'&&p.score===10000&&f.drink.length===0,'free bottle raises price while menu open -> stale quote refuses without debit');
  check(tx.seq!==1&&tx.cost===2500,'changed ownership rotates displayed quote');
  check(f.call('tod_wunderfizz::respond',[p,1,1])==='stale'&&p.score===10000,'old displayed quote refuses after refresh');
  const stable=tx.seq;f.call('tod_wunderfizz::push_state',[tx,true]);check(tx.seq===stable,'heartbeat repeats stable quote sequence');
  delete p.held[keys[7]];f.call('tod_wunderfizz::push_state',[tx,true]);check(tx.cost===2000&&tx.seq!==stable,'lost perk lowers price and rotates quote');
}
{
  const f=load(),p=player(1999),tx=session(f,p);
  check(f.call('tod_wunderfizz::respond',[p,tx.seq,1])==='points'&&p.score===1999,'insufficient points has no debit');
  check(f.events.some(e=>e.name==='tod_wf_result'&&e.n===2&&same(e.values,[tx.seq,1])),'purchase rejection releases UI with result event');
}
{
  const f=load(),p=player(),tx=session(f,p);p.state={in_range:false};
  check(f.call('tod_wunderfizz::respond',[p,tx.seq,1])==='range'&&p.score===10000,'range departure rechecked before debit');
  check(f.events.some(e=>e.name==='tod_wf_state'&&e.n===5&&e.values.length===5),'state event is precisely five integers');
}
for(const why of ['down','death','range','timeout','menu','spawned','end_game','perk_abort_drinking']){
  const f=load(),p=player(),tx=session(f,p);
  f.call('tod_wunderfizz::respond',[p,tx.seq,1]);
  tx.drink_started=true;tx.drinking_before=0;tx.original='rifle';tx.can='can';p.weapons.can=true;p.weapon='can';p.is_drinking=1;p.controls=false;
  f.call('tod_wunderfizz::finish',[tx,why]);f.call('tod_wunderfizz::finish',[tx,why]);
  check(tx.finished&&f.cleanup.length===1&&!f.call('tod_wunderfizz::owns_session',[tx]),'cleanup claim once, late grant disabled '+why);
  f.flush();
  check(p.score===10000&&p.perk_purchased===undefined&&p.tod_wf_tx===undefined&&p.tod_wf_menu_active===undefined&&tx.machine.buyers===0&&f.level.tod_wf_sessions[tx.client]===undefined,'refund/pending/menu/session released '+why);
  check(p.is_drinking===0&&p.controls&&p.weapon==='rifle'&&!p.weapons.can,'bottle/control/original weapon cleanup '+why);
  check(f.calls.filter(c=>c[0]==='refund').length===1&&f.calls.some(c=>same(c,['refund',2000,false])),'actual debit refunded once without total-earned boost '+why);
}
{
  const f=load(),p=player(),tx=session(f,p);f.call('tod_wunderfizz::respond',[p,tx.seq,1]);tx.granted=true;
  f.call('tod_wunderfizz::finish',[tx,'granted']);f.flush();
  check(p.score===8000&&!f.calls.some(c=>c[0]==='refund'),'granted perk never refunded');
}
{
  const f=load(),m={floor:32,buyers:0},a=player(),b=player();b.paused[keys[4]]=true;
  const ta=session(f,a,1,m),tb=session(f,b,2,m);
  f.call('tod_wunderfizz::respond',[a,ta.seq,1]);f.call('tod_wunderfizz::respond',[b,tb.seq,2]);
  check(a.score===8000&&b.score===7500&&ta.debit===2000&&tb.debit===2500&&m.buyers===2,'co-op same counter: separate ownership prices/pending reservations');
  f.call('tod_wunderfizz::finish',[ta,'down']);f.flush();
  check(a.score===10000&&b.score===7500&&b.tod_wf_tx===tb&&m.buyers===1,'one co-op exit cannot release/refund the other buyer');
  f.call('tod_wunderfizz::finish',[tb,'close']);f.flush();check(b.score===10000&&m.buyers===0,'last co-op buyer releases machine hold');
}
{
  const f=load(),p=player(),tx=session(f,p);f.call('tod_wunderfizz::respond',[p,tx.seq,1]);tx.p=undefined;
  f.call('tod_wunderfizz::finish',[tx,'disconnect']);f.flush();
  check(tx.machine.buyers===0&&f.level.tod_wf_sessions[tx.client]===undefined&&f.logs.some(l=>l.includes('REFUND_SKIPPED')),'deleted disconnected entity releases machine/session, honestly logs uncreditable debit');
}
// Mutation controls prove that the gates exercise the safety decisions.
{
  const mutant=load(WF,ROSTER.replace('p HasPerk( perk ) || p zm_perks::has_perk_paused( perk )','p HasPerk( perk )'));
  const p=player();p.paused[keys[0]]=true;
  check(mutant.call('tod_perk_roster::owned_count',[p])!==1,'negative control catches lost paused ownership');
}
{
  const mutant=load(WF.replace('tx.debit = tx.before - tx.after;','tx.debit = cost;')),p=player(0),tx=session(mutant,p);p.shoppingFree=true;
  mutant.call('tod_wunderfizz::respond',[p,tx.seq,1]);mutant.call('tod_wunderfizz::finish',[tx,'down']);mutant.flush();
  check(p.score!==0,'negative control catches nominal-price Shopping Free refund');
}
{
  let caught=0;
  const src=body(WF,'refusal_from_state');
  for(const [field,value,why]of refuses){
    const literal=(value?'s.':'!s.')+field;
    const changed=src.replace(new RegExp(literal.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b'),'false');
    const mutant=load(WF.replace(src,changed));
    if(mutant.call('tod_wunderfizz::refusal_from_state',[{...openState,[field]:value},false])!==why)caught++;
  }
  check(caught===refuses.length,'negative controls catch all '+refuses.length+' refused state clauses');
}
const claim=body(WF,'finish'),clean=body(WF,'finish_cleanup'),watch=body(WF,'session_watch'),worker=body(WF,'drink_worker'),respond=body(WF,'respond');
check(claim.indexOf('tx.finished = true')<claim.indexOf('level thread finish_cleanup')&&!/notify\(/.test(claim),'finish claims synchronously then detaches cleanup before abort endon');
check(!/\bendon\s*\(/.test(clean)&&!/(?:self|p)\s+thread\s+finish_cleanup/.test(claim),'cleanup is level-owned and has no worker lifetime endons');
check(!/\bendon\s*\(/.test(watch)&&/wait 0\.1/.test(watch)&&/now >= tx\.deadline/.test(watch),'independent 100 ms watchdog always owns timeout');
check(/self endon\( "tod_wf_abort" \)/.test(worker)&&/zm_perks::perk_give_bottle_begin/.test(worker)&&/zm_perks::perk_give_bottle_end/.test(worker)&&/zm_perks::give_perk\( tx\.perk, true \)/.test(worker),'paid worker keeps stock can and give_perk callbacks/HUD/QR ledger');
const reserve=respond.slice(respond.indexOf('tx.phase = "drink"'),respond.indexOf('p.perk_purchased = perk'));
check(!/\bwait\b|\bthread\b|cue\(/.test(reserve)&&/tx\.before = p\.score;[\s\S]*minus_to_player_score\( cost \);[\s\S]*tx\.after = p\.score/.test(reserve),'reservation/debit/actual score capture has no yield');
check(!/GetEntArray|zombie_vending/.test(ROSTER),'free roster has no physical vending entity dependency');
check(/p\.perk_purchased == tx\.perk/.test(clean)&&/p\.tod_wf_tx\.op == tx\.op/.test(clean),'cleanup guards pending/current session ownership');
check(/TOD_WF_DRINK_MS 8000/.test(WF)&&/TOD_WF_MENU_MS 20000/.test(WF),'separate finite menu and drink deadlines');
console.log('\n'+passes+' passed; '+fails+' failed. Source policy proof only; native animation, audio, menu routing and engine endons require user playtest.');
process.exitCode=fails?1:0;
