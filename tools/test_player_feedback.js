// Execute the changed GSC helpers with mocked players/time; no engine substitute.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const tp=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_teleport.gsc','utf8');
function body(src,name){
    src=src.replace(/\/\/[^\n]*/g,'');
    let a=src.indexOf('{',src.indexOf('function '+name+'(')),b=a+1,d=1;
    assert(a>=0,name);while(d){if(src[b]==='{')d++;if(src[b]==='}')d--;b++;}
    return src.slice(a+1,b-1);
}
const env={isdefined:v=>v!==undefined,IsAlive:p=>p.alive,int:Math.trunc,
    array:(...v)=>v,abs:Math.abs,clock:1000,flags:{},
    level:{tod_tp_trigs:[]},players:[],GetTime:()=>env.clock,
    Distance:(a,b)=>Math.hypot(...a.map((n,i)=>n-b[i])),Distance2D:(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]),
    GetPlayers:()=>env.players,
    flagExists:k=>k in env.flags,flagGet:k=>env.flags[k]};
for(const m of tp.matchAll(/#define\s+(TOD_\w+)\s+([\d.]+)/g))env[m[1]]=Number(m[2]);
vm.createContext(env);
for(const [name,args,locals] of [['pad_lock_reason','lock_flag','unused'],['pad_locked','lock_flag','unused'],['recharge_seconds','until','left'],['recharge_pad_for','player','best,nearest,i,t,d']]){
    const b=body(tp,name).replace(/level flag::exists\(/g,'flagExists(').replace(/level flag::get\(/g,'flagGet(').replace(/level.tod_tp_trigs.size/g,'level.tod_tp_trigs.length');
    vm.runInContext(`function ${name}(${args}){let ${locals};${b}}`,env);
}
assert.equal(env.pad_lock_reason(undefined),1);
env.flags={power_on:true,enter_lap10:false};assert.equal(env.pad_lock_reason('enter_lap10'),2);
assert.equal(env.pad_lock_reason(undefined),0,'down ride only needs power');
env.flags.enter_lap10=true;assert.equal(env.pad_locked('enter_lap10'),false);
for(const [delta,seconds] of [[60000,60],[59001,60],[59000,59],[1,1],[0,0],[-1,0]])assert.equal(env.recharge_seconds(env.clock+delta),seconds);
env.level.tod_tp_trigs=[{tod_tp_src:[-110,0,0],tod_tp_radius:110},{tod_tp_src:[110,0,0],tod_tp_radius:110},{tod_tp_src:[-110,0,384],tod_tp_radius:110}];
assert.equal(env.recharge_pad_for({alive:true,origin:[-100,0,0]}),0);
assert.equal(env.recharge_pad_for({alive:true,origin:[100,0,0]}),1);
assert.equal(env.recharge_pad_for({alive:true,origin:[-100,0,384]}),2);
assert.equal(env.recharge_pad_for({alive:true,origin:[0,200,0]}),-1);
assert.equal(env.recharge_pad_for({alive:false,origin:[-100,0,0]}),-1);
console.log('Player feedback GSC: teleporter locks/seconds/adjacent pads/heights pass.');
