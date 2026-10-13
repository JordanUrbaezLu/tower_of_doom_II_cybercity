// Execute the shipping weapon recognition, delayed FX guard and pulse cleanup.
const fs=require('fs'),assert=require('assert/strict');
const skull=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_necro_skull.gsc','utf8');
const summon=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_necro_summon.gsc','utf8');
function body(src,name){return src.match(new RegExp('function '+name+'\\([^)]*\\)[^{]*\\{([\\s\\S]*?)\\n\\}'))[1];}
const defined=x=>x!==undefined&&x!==null;
const form=new Function('self','isdefined','IsSubStr','TOD_NECRO_STEM','let w;'+body(skull,'skull_form').replace('self GetCurrentWeapon()','self.weapon'));
for(const name of ['tod_necro_skull','tod_necro_staff2','tod_necro_staff3'])for(const up of [false,true]){
 assert.equal(form({weapon:{name:name+(up?'_up_b':'_b')}},defined,(s,t)=>s.includes(t),'tod_necro_skull'),up?2:1);
}
for(const weapon of [undefined,{}, {name:'cc_fire_bow_up_d3'}, {name:'tod_necro_pulse3'}])assert.equal(form({weapon},defined,(s,t)=>s.includes(t),'tod_necro_skull'),0);
const Generator=Object.getPrototypeOf(function*(){}).constructor;
const promote=new Generator('self','m','v','epoch','isdefined',body(skull,'promote_loop').replace('self endon(','self.endon(').replace('wait 0.1;','yield .1;').replace('self clientfield::set(','self.set('));
for(const interrupt of ['none','stop','new_mode_epoch']){
 const calls=[],self={tod_necro_mode:1,tod_necro_mode_epoch:4,endon(){},set:(...args)=>calls.push(args)};
 const it=promote(self,1,5,4,defined);it.next();
 if(interrupt==='stop')self.tod_necro_mode=0;
 if(interrupt==='new_mode_epoch')self.tod_necro_mode_epoch++;
 it.next();assert.equal(calls.length,interrupt==='none'?1:0);
 if(calls.length)assert.deepEqual(calls[0],['tod_necro_fx',6]);
}
let src=body(summon,'staff_pulse_restore')
 .replace(/level endon\([^;]+;/,'')
 .replace(/owner laststand::player_is_in_laststand\(\)/g,'owner.down')
 .replace(/owner GetCurrentWeapon\(\)/g,'owner.current')
 .replace(/owner GetEntityNumber\(\)/g,'owner.id')
 .replace(/owner (HasWeapon|TakeWeapon|ShouldDoInitialWeaponRaise|SwitchToWeaponImmediate)\(/g,'owner.$1(')
 .replace(/wait 0.05;/g,'yield .05;');
const restore=new Generator('owner','previous','proxy','token','isdefined','IsAlive','GetTime','dev_log','let started,pose_logged,current,current_name;'+src);
for(const event of ['normal','switched','dead','down','new_life','previous_removed','disconnect']){
 let now=0,alive=true;const calls=[],previous={name:'tod_necro_staff3_up_b'},proxy={name:'tod_necro_pulse3'},other={name:'sidearm'};
 const owner={id:3,current:proxy,down:false,tod_necro_pulse_token:17,tod_necro_pulse_busy:true,
   inventory:new Set([previous,proxy]),HasWeapon(w){return this.inventory.has(w)},TakeWeapon(w){this.inventory.delete(w);calls.push('take')},
   ShouldDoInitialWeaponRaise(){},SwitchToWeaponImmediate(w){this.current=w;calls.push('restore')}};
 const it=restore(owner,previous,proxy,17,x=>defined(x)&&(x!==owner||event!=='disconnect'||now<100),()=>alive,()=>now,()=>{});
 for(let step=0;step<20;step++){
   if(step===2){
    if(event==='switched')owner.current=other;
    if(event==='dead')alive=false;
    if(event==='down')owner.down=true;
    if(event==='new_life')owner.tod_necro_pulse_token=undefined;
    if(event==='previous_removed')owner.inventory.delete(previous);
   }
   if(it.next().done)break;now+=50;
 }
 assert.equal(calls.includes('restore'),event==='normal',event);
 if(!['new_life','disconnect'].includes(event)){
   assert.equal(owner.inventory.has(proxy),false,event);assert.equal(owner.tod_necro_pulse_busy,false,event);
 } else assert.equal(calls.length,0,event);
}
console.log('NECRO STAFF RUNTIME PASS: all tier/PaP forms, stale FX promotion rejection, pulse normal/switch/death/down/respawn/disconnect cleanup.');
