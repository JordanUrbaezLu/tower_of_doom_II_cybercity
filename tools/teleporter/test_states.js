// Execute the actual GSC transition and refresh bodies with mocked entities.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const s=fs.readFileSync(path.resolve(__dirname,'../../scripts/zm/zm_tod2_cybercity/_tod_teleport.gsc'),'utf8');
function body(n){const a=s.split('function '+n+'(')[1].split('\nfunction ')[0];return a.slice(a.indexOf('{'));}
function adapt(a){return a.replace(/\b([\w.]+) (SetModel|Delete|NotSolid|notify|SetHintString|PlayLoopSound|StopLoopSound)\(/g,'$1.$2(').replace('h thread recharge_chase();','h.motion=true;').replaceAll('tod_perk_scatter::play_sound_at_origin','readySound');}
const made=[],log=[];let fail=false,clock=0,reason=1,readyCues=0,destination=true;
function entity(){const x={origin:[0,0,0],angles:[0,0,0],SetModel(v){this.model=v;},Delete(){this.deleted=true;},NotSolid(){},notify(v){this.stopped=v;},SetHintString(v){this.hint=v;},PlayLoopSound(v){this.loop=v;this.loops=(this.loops||0)+1;},StopLoopSound(){this.loop=undefined;}};made.push(x);return x;}
const ctx={level:{tod_upgrade_pause:false},undefined,IS_TRUE:v=>v===true,isdefined:v=>v!==undefined&&!v?.deleted,Spawn:()=>fail?undefined:entity(),state_log:v=>log.push(v),transit_log:v=>log.push(v),destination_ready:()=>destination,GetTime:()=>clock,pad_lock_reason:()=>reason,pad_lock_reason_at:()=>reason,spawn_beam:()=>entity(),fx_dev_log:()=>{},readySound:()=>readyCues++};
vm.createContext(ctx);
vm.runInContext('function model_state(m,state){let mode,prev,h,was_ready;'+adapt(body('model_state'))+'\n}',ctx);
vm.runInContext('function refresh(t){let state,reason,prev;'+adapt(body('refresh'))+'\n}',ctx);
const t=entity();t.tod_tp_route={id:'test_route'};t.tod_tp_model=entity();t.tod_tp_src=[0,0,0];t.tod_tp_cooldown_until=0;t.tod_tp_hint_ready='ready';
ctx.refresh(t);assert.equal(t.tod_tp_model.model,'tod_teleporter_off');assert.equal(t.tod_tp_beam,undefined);
// docs/202 v3: lock reason 3 = the haven's guardians still live -> dark, the guardians hint, no chase host
reason=3;ctx.refresh(t);assert.equal(t.tod_tp_state,'corrupted');assert.equal(t.tod_tp_model.model,'tod_teleporter_off');assert(t.hint.includes('defeat the guardians'));assert.equal(t.tod_tp_beam,undefined);assert.equal(t.tod_tp_model.tod_tp_chase,undefined,'a corrupted haven pad is dark, not pending');
reason=2;ctx.refresh(t);assert.equal(t.tod_tp_state,'destination');assert.equal(t.tod_tp_model.model,'tod_teleporter_off');
const lockedChase=t.tod_tp_model.tod_tp_chase;assert(lockedChase.motion);assert.equal(t.tod_tp_model.tod_tp_visual_state,'pending');
ctx.refresh(t);assert.equal(t.tod_tp_model.tod_tp_chase,lockedChase,'pending must not duplicate hosts');
reason=0;ctx.refresh(t);assert.equal(t.tod_tp_model.model,'tod_teleporter');assert(t.tod_tp_beam);assert.equal(readyCues,0);
assert(lockedChase.deleted);
destination=false;ctx.refresh(t);assert.equal(t.tod_tp_state,'destination');assert.equal(t.tod_tp_model.tod_tp_visual_state,'pending');assert.equal(t.tod_tp_beam,undefined);
destination=true;ctx.refresh(t);assert.equal(t.tod_tp_model.model,'tod_teleporter');assert(t.tod_tp_beam);assert.equal(readyCues,0,'Zone activation is not a recharge-complete cue');
const beam=t.tod_tp_beam;t.tod_tp_cooldown_until=60000;ctx.refresh(t);assert(beam.deleted);assert.equal(t.tod_tp_model.model,'tod_teleporter_off');const chase=t.tod_tp_model.tod_tp_chase;assert(chase.motion);
ctx.refresh(t);assert.equal(t.tod_tp_model.tod_tp_chase,chase);
reason=2;ctx.refresh(t);assert.equal(t.tod_tp_model.tod_tp_chase,chase,'same yellow chase across pending reasons');
reason=1;ctx.refresh(t);assert(chase.deleted&&chase.stopped==='tp_chase_stop');assert.equal(t.tod_tp_model.tod_tp_chase,undefined);
reason=0;ctx.refresh(t);assert(t.tod_tp_model.tod_tp_chase!==chase);clock=60000;ctx.refresh(t);assert.equal(t.tod_tp_model.model,'tod_teleporter');assert.equal(readyCues,1);
ctx.refresh(t);assert.equal(readyCues,1);ctx.level.tod_upgrade_pause=true;ctx.refresh(t);assert.equal(t.tod_tp_model.model,'tod_teleporter_off');assert.equal(t.tod_tp_beam,undefined);
assert(t.tod_tp_model.tod_tp_chase?.motion,'powered pause is pending yellow');
ctx.level.tod_upgrade_pause=false;ctx.refresh(t);assert.equal(t.tod_tp_model.model,'tod_teleporter');
fail=true;t.tod_tp_cooldown_until=120000;ctx.refresh(t);assert.equal(t.tod_tp_model.tod_tp_chase,undefined);assert.equal(t.tod_tp_model.model,'tod_teleporter_off');fail=false;ctx.refresh(t);assert(t.tod_tp_model.tod_tp_chase);
ctx.model_state(t.tod_tp_model,'off');assert.equal(t.tod_tp_model.tod_tp_chase,undefined);assert(made.filter(m=>m.motion).every(m=>m.deleted));
ctx.model_state(t.tod_tp_model,'pending');assert(t.tod_tp_model.tod_tp_chase.motion);
ctx.model_state(t.tod_tp_model,'power');assert.equal(t.tod_tp_model.tod_tp_chase,undefined);
ctx.model_state(undefined,'ready');
// Power wins even when both the cooldown and upgrade pause are active.
ctx.level.tod_upgrade_pause=true;reason=1;ctx.refresh(t);
assert.equal(t.tod_tp_model.model,'tod_teleporter_off');assert.equal(t.tod_tp_model.tod_tp_chase,undefined);assert.equal(t.tod_tp_beam,undefined);
assert(s.includes('self RotateYaw( 360, 3 )'));assert(s.includes('#define TOD_TP_COOLDOWN_SEC   60'));assert(s.includes('#define TOD_TP_CHARGE_SEC     0.8'));
assert(s.includes('palette=green_yellow'));
// PK23 (2026-10-05): THE PAD HUMS - a ready pad loops its idle hum (once, not per refresh), a recharging pad's chase
// host carries the rising whir (so it ends with the chase), a dark pad is silent.
{
  const m=entity();
  ctx.model_state(m,'off');assert.equal(m.loop,undefined,'a dark pad is silent');
  ctx.model_state(m,'ready');assert.equal(m.loop,'tod_teleport_idle_lp','a ready pad hums');
  ctx.model_state(m,'ready');assert.equal(m.loops,1,'the hum starts once, never per refresh');
  ctx.model_state(m,'recharge');assert.equal(m.loop,undefined,'leaving ready stops the hum');
  const ch=m.tod_tp_chase;assert.equal(ch.loop,'tod_teleport_cool_lp','the recharge chase carries the whir');
  ctx.model_state(m,'ready');assert(ch.deleted,'the chase (and its whir) is deleted');assert.equal(m.loop,'tod_teleport_idle_lp');
  ctx.model_state(m,'off');assert.equal(m.loop,undefined,'power off silences the pad');
}
console.log('TELEPORTER STATES PASS: no-power dark, corrupted-haven dark (docs/202 v3), green ready, yellow pending for lock/cooldown/pause, one chase, cleanup/retry, exact cooldown boundary, no extra ready cues and the pad hums (PK23).');
