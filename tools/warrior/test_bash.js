// Execute shipping Bash and corpse coroutines against deterministic engine edges.
const fs=require('fs'),assert=require('assert/strict');
const kit=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_class_kit.gsc','utf8');
const cleanup=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_corpse_cleanup.gsc','utf8');
const body=(s,n)=>s.match(new RegExp('function '+n+'\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\}'))[1];
const add=(a,b)=>a.map((x,i)=>x+b[i]),mul=(a,n)=>a.map(x=>x*n),vec=(...a)=>a;
let code=body(kit,'bash_run').replace(/\/\/[^\n]*/g,'')
 .replace(/owner \[\[ level.tod_wm_alt_right_fn \]\]\( previous \)/g,'previous')
 .replace(/\b(owner|level) ([A-Za-z_]\w*)\(/g,'$1.$2(')
 .replace(/foreach \( (\w+) in array\(([^)]*)\) \)/g,'for ( $1 of [$2] )')
 .replace(/\( 0, angles\[ 1 \], 0 \)/g,'vec(0, angles[1], 0)')
 .replace(/\( 0, 0, ([^()]*) \)/g,'vec(0,0,$1)')
 .replace('owner.origin + vec(0,0,1)','add(owner.origin,vec(0,0,1))')
 .replace('owner.origin + right * side + vec(0,0,height)','add(add(owner.origin,mul(right,side)),vec(0,0,height))')
 .replace('a + fwd * 30','add(a,mul(fwd,30))')
 .replace('owner.origin + fwd * 24','add(owner.origin,mul(fwd,24))')
 .replace('ahead + vec(0,0,24)','add(ahead,vec(0,0,24))')
 .replace('ahead - vec(0,0,8)','add(ahead,vec(0,0,-8))')
 .replace('fwd * speed','mul(fwd,speed)')
 .replace('velocity + vec(0,0,vz)','add(velocity,vec(0,0,vz))')
 .replace(/wait 0.05;/g,'yield 0.05;');
const variables=[...new Set([...code.replace(/"[^"\n]*"/g,'').matchAll(/\b(\w+)\s*=(?!=)/g)].map(m=>m[1]))]
 .filter(n=>!['owner','previous','proxy','token','blade','tod_bash_busy','tod_bash_token'].includes(n));
const make=src=>new Function('e',`with(e) { return function*(owner,previous,proxy,token,blade){let ${variables.join(',')};${src}} }`);
// ENGINE-FAITHFUL MOCK (2026-09-27). The 15:07 build locked Bash with FreezeControls
// and this test passed, because its mock treated FreezeControls as harmless. The real
// engine ignores SetVelocity and weapon switches on a frozen player: the user's 18:25
// log had travel=0 and proxy_up_after_ms=-1 on every cast. Frozen = no movement here.
function run_all(src){
let count=0;
for(const blade of ['cc_punch_k0','cc_gauntlet_k0','cc_gold_sword_k0'])
for(const terrain of ['floor','air','stairs','ledge','wall'])
for(const interrupt of ['none','death','weapon','respawn','disconnect','smash']) {
 let now=1000,logs=[],steps=0,alive=true;
 const proxy={name:'proxy'},previous={name:blade};
 const player={origin:[0,0,0],velocity:[0,75,-100],angles:terrain==='air'?[-20,0,0]:[0,0,0],
  frozen:false,tod_bash_token:now,tod_bash_busy:true,current:proxy,
  GetPlayerAngles(){return this.angles},IsOnGround(){return terrain!=='air'},can_act(){return alive},
  FreezeControls(b){this.frozen=b},SetPlayerAngles(a){this.angles=a},SetOrigin(a){if(!this.frozen)this.origin=a},
  SetVelocity(a){this.velocity=a},GetVelocity(){return this.frozen?[0,0,0]:this.velocity},GetStance(){return 'stand'},
  GetCurrentWeapon(){return this.current},GetEntityNumber(){return 1},HasWeapon(){return true},
  ShouldDoInitialWeaponRaise(){},SwitchToWeaponImmediate(w){if(!this.frozen)this.current=w},TakeWeapon(){},
  EnableWeaponFire(){},AllowMelee(){},bash_sync(){},bash_path(){return 0},bash_impact(){},
  gs_after_bash(w){this.smash_from=w;this.tod_gs_queued=undefined}};
 const defs=Object.fromEntries([...kit.matchAll(/^#define\s+(TOD_BASH_\w+)\s+([\d.]+)/gm)].map(m=>[m[1],+m[2]]));
 const e={...defs,level:{endon(){}},vec,add,mul,isdefined:x=>x!==undefined,GetTime:()=>now,
  AnglesToForward:a=>{const p=a[0]*Math.PI/180,y=a[1]*Math.PI/180;return [Math.cos(p)*Math.cos(y),Math.cos(p)*Math.sin(y),-Math.sin(p)].map(v=>Math.abs(v)<1e-12?0:v)},
  AnglesToRight:a=>{const y=a[1]*Math.PI/180;return [Math.sin(y),-Math.cos(y),0].map(v=>Math.abs(v)<1e-12?0:v)},
  IsSubStr:(s,p)=>s.includes(p),Distance2D:(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]),unlimited:()=>true,
  dev_log:s=>logs.push(s),BulletTrace(a,b){
   const floor=a[0]===b[0]&&a[1]===b[1];
   if(floor&&terrain==='stairs'){steps++;return {fraction:.5,normal:[0,0,1],position:[b[0],b[1],player.origin[2]+8]}}
   return {fraction:!floor&&terrain==='wall'?0:1,normal:[0,0,1],position:b};
  }};
 const run=make(src)(e)(player,previous,proxy,1000,previous);
 for(let tick=0;tick<30;tick++){
  const r=run.next();if(r.done)break;
  // the player turns the view every tick of the dash: the path must not follow it
  player.angles=[player.angles[0],player.angles[1]+20,0];
  if(!player.frozen) player.origin=add(player.origin,mul(player.velocity,r.value));
  now+=r.value*1000;
  if(tick===2){
   if(interrupt==='death')alive=false;
   if(interrupt==='weapon')player.current=previous;
   if(interrupt==='respawn'){player.tod_bash_token=undefined;}
   if(interrupt==='smash')player.tod_gs_queued=now; // Cyber Smash pressed mid-dash (2026-09-27)
   if(interrupt==='disconnect'){ /* engine destroys the entity and its inputs */ run.return();break; }
  }
 }
 if(interrupt==='smash'){
  assert(logs.some(s=>s.startsWith('BASH_CUT')),'a queued smash cuts the dash');
  assert.equal(player.smash_from,previous,'the smash returns to the blade the Bash came from');
  assert.equal(player.tod_bash_busy,undefined,'the Bash lets go before the slam');
  assert(logs.some(s=>s.startsWith('BASH_END')&&s.includes('cut=true')));
 } else assert.equal(player.smash_from,undefined,'no smash without a press');
 if(interrupt==='none'){
  assert.equal(player.current,previous,'the blade comes back after the swing');assert.equal(player.tod_bash_busy,undefined);
  assert.equal(player.origin[1],0,'no incoming strafe or view turn bends the dash');
  if(terrain==='wall')assert.equal(player.origin[0],0,'solid wall cancels propulsion');
  else assert(player.origin[0]>100,'air, ledges and stairs all advance');
  if(terrain==='air')assert(player.origin[2]>0,'airborne dash follows the latched pitch');
  if(terrain==='stairs')assert(steps>0&&player.origin[2]>1,'stair assistance rises without cancelling');
  assert(logs.some(s=>s.startsWith('BASH_START')&&s.includes('steer=latched')));
 }
 count++;
}
return count;
}
const count=run_all(code);
// NEGATIVE CONTROL: the shipped 15:07 lock must fail this test now.
const locked=code.replace('started = GetTime();','started = GetTime(); owner.FreezeControls(true);');
assert.notEqual(locked,code,'negative control could not re-insert the old lock');
assert.throws(()=>run_all(locked),/advance|blade comes back/,'negative control: a FreezeControls lock must stop the dash');
// NEGATIVE CONTROL: a dash that re-reads the view each tick (steerable) must fail.
const steered=code.replace('elapsed = GetTime() - started;','elapsed = GetTime() - started; fwd = AnglesToForward( owner.GetPlayerAngles() );');
assert.notEqual(steered,code,'negative control could not re-insert view steering');
assert.throws(()=>run_all(steered),/bends the dash/,'negative control: a dash that follows the view must fail');
assert(!/^[^\/\n]*FreezeControls\s*\(/m.test(kit),'Bash must never FreezeControls: a frozen player ignores SetVelocity and weapon switches');
// Reproduce real callback order: cleanup starts first, then Warrior marks the fling.
let corpse=body(cleanup,'corpse_remove').replace(/\/\/[^\n]*/g,'')
 .replace(/self ([A-Za-z_]\w*)\(/g,'self.$1(')
 .replace(/zombie_utility::get_current_actor_count\(\)/g,'actors')
 .replace(/wait ([\w.]+);/g,'yield $1;');
const Generator=Object.getPrototypeOf(function*(){}).constructor;
const remove=new Generator('self','linger','isdefined','IS_TRUE','actors','TOD_CORPSE_LINGER','TOD_BAT_LINGER','TOD_ACTOR_LIMIT','TOD_CORPSE_PANIC','TOD_CORPSE_SETTLE','bat_log',corpse);
for(const pressure of [10,64])for(const fling of [false,true]){
 let ghost=false,deleted=false,solid=true;
 const z={NotSolid(){solid=false},Ghost(){ghost=true},Delete(){deleted=true},GetEntityNumber(){return 9}};
 const r=remove(z,undefined,e=>e!==undefined,Boolean,pressure,2,3.5,64,8,.1,()=>{});
 assert.equal(r.next().value,.05);assert.equal(solid,false,'collision goes away on death frame');assert.equal(ghost,false);
 if(fling)z.tod_bat_launched=true; // later death callback, same frame
 const next=r.next();
 if(fling){assert.equal(next.value,3.5);assert.equal(ghost,false,'sword ragdoll stays visible at actor cap')}
 else if(pressure===64)assert.equal(ghost,true,'non-flung bodies still obey pool pressure');
 while(!r.next().done){}assert(deleted,'every corpse has bounded cleanup');
}
console.log(`WARRIOR PASS: ${count} Bash terrain/weapon/interruption cases (view turning every tick, engine-faithful FreezeControls negative control) and corpse callback-order regression.`);
