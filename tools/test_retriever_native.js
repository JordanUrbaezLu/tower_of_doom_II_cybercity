// Run the shipping BO2-derived decisions/state machine with deterministic
// entities. Native physics/animation rendering remain the user's playtest.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const src=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_retriever.gsc','utf8');
const archer=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_archer.gsc','utf8');
function fn(name,text=src){let start=text.indexOf('function '+name+'(');assert(start>=0,name);let open=text.indexOf('{',start),end=open+1,d=1;while(d){if(text[end]==='{')d++;if(text[end]==='}')d--;end++;}return text.slice(start,end);}
const calls=[],ctx=vm.createContext({isdefined:x=>x!==undefined,IsAlive:z=>!!z&&z.health>0,IS_TRUE:x=>!!x,int:Math.trunc,
  GetTime:()=>0,GetAITeamArray:()=>[],Distance2DSquared:(a,b)=>(a[0]-b[0])**2+(a[1]-b[1])**2,
  PlayFX:()=>{},PlayFXOnTag:()=>{},log:()=>{},
  util:{get_array_of_closest:()=>[]},upgrades:{get_level:(p,k)=>p.card[k]||0},array:(...a)=>a,scatter:{play_sound_at_origin:()=>{}},abfx:{ring_at:()=>{}, axe_hit:()=>{}},level:{round_number:1,zombie_team:'axis',tod_retriever_weapon:{name:'retriever'}},
  self:{card:{},origin:[0,0,0],IsThrowingGrenade:()=>false,GetEye:()=>[0,0,60],GetEntityNumber:()=>0,SetWeaponAmmoClip:()=>{},score:0},
  Spawn:()=>({origin:[0,0,0],PlayLoopSound:()=>{},StopLoopSound:()=>{},StopSounds:()=>{},Delete:()=>{}})});
function translate(code){return code.replace(/\/\/[^\n]*/g,'').replace(/foreach\s*\(\s*(\w+)\s+in\s+([^\)]+)\)/g,'for (const $1 of $2)')
 .replace(/\.size\b/g,'.length').replace(/tod_perk_scatter::/g,'scatter.').replace(/tod_ability_fx::/g,'abfx.').replace(/tod_upgrades::/g,'upgrades.').replace(/util::/g,'util.')
 .replace(/self zm_score::add_to_player_score\( 10 \)/g,'self.score += 10')
 .replace(/z.origin \+ \( 0, 0, 40 \)/g,'z.origin')
 .replace(/\b(self|z|powerup|first|a\.axe_audio|a\.axe|a\.projectile|s\.axe_audio|s\.axe|s\.projectile)\s+(\w+)\s*\(/g,'$1.$2(');}
for(const m of src.matchAll(/#define\s+(TOD_RET_\w+)\s+([\d.]+)/g))ctx[m[1]]=Number(m[2]);   // the shipping knobs, read from the GSC
for(const name of ['card_level','charges_max','damage_mult','ammo_now','in_flight','strike_tag','charge_power','damage','eligible','attack','returning','hit','finish','finish_axe','destroy','destroy_axe','step','axe_step'])vm.runInContext(translate(fn(name)),ctx);
for(const name of ['card_level','attack','returning','hit','finish','finish_axe','axe_step'])ctx.self[name]=(...args)=>ctx[name](...args);
ctx.self.impact=(s,a)=>{calls.push('impact');a.done=true;};   // the native handover is mocked: the axe is done
for(const [ms,want] of [[0,1],[999,1],[1000,1],[1001,1.5],[1999,1.5],[2000,1],[2001,2],[2999,2],[3000,2],[10000,2]])assert.equal(ctx.charge_power(ms),want,'BO2 charge '+ms);
// POWER SCALE (2026-09-25): the flat hit is BO2's 1000 x power at one tenth (100 x power); the kill rules stay health + 1.
for(const [round,counter,power,want] of [[1,1,1,100],[9,1,2,200],[10,3,1,5001],[10,4,1,100],[12,3,1.5,5001],[13,2,1,5001],[13,3,2,200],[14,2,2,5001],[15,1,2,200],[50,1,1.5,150]])assert.equal(ctx.damage(5000,power,round,counter,1),want,'BO2 damage '+[round,counter,power]);
const zombie=(id)=>({health:5000,origin:[100,0,0],GetTagOrigin(){return this.origin},GetEntityNumber:()=>id,DoDamage(d){this.health-=d}});
const z1=zombie(1),b=zombie(2),c=zombie(3),unmarked=zombie(4);
const axe={origin:[100,0,0],RotatePitch:()=>{},MoveTo(pos,time){this.origin=pos;calls.push(['move',time])},Delete:()=>calls.push('delete')};
// MANY AXES (2026-09-26): one struct per throw in s.axes; step() walks them all.
let ax={id:0,phase:'chain',spin_left:0,move_left:0,axe,axe_audio:ctx.Spawn(),power:2,mult:1,hits:[],marked:[z1,b,c],chain:[z1,b,c,unmarked],chain_index:0,chain_limit:4,powerups:[],low_kill:1,return_checks:0,done:false};
let s={ret_on:true,axe_charges:1,axes:[ax],axe_busy:true};
assert.equal(ctx.eligible(ax,unmarked),false,'the marked ring constrains the reversed ricochet list');
ctx.step(s,.05);assert.equal(ax.chain_index,1);assert.equal(ax.phase,'chain','farthest unmarked entry skipped');
for(let i=0;i<150&&s.axes.length;i++)ctx.step(s,.05);
assert.deepEqual(ax.hits.map(z=>z.GetEntityNumber()),[3,2,1],'native reverse candidate order');
assert.equal(ctx.self.score,30,'original ten points per script hit');
assert.equal(s.axes.length,0,'catch drops the axe from the air');assert.equal(s.axe_busy,false,'nothing in the air');
// two axes step side by side and each is caught on its own
const mk=(id)=>({id,phase:'return',spin_left:0,move_left:0,axe:{...axe,origin:[500,0,0]},axe_audio:ctx.Spawn(),power:1,mult:1,hits:[],marked:[],chain:[],chain_index:0,chain_limit:0,powerups:[],low_kill:1,return_checks:5,done:false});
s={ret_on:true,axe_charges:0,axes:[mk(1),mk(2)]};ctx.step(s,.05);assert.equal(s.axes.length,2,'both axes still flying home');
for(let i=0;i<40&&s.axes.length;i++)ctx.step(s,.05);assert.equal(s.axes.length,0,'both caught');assert(calls.filter(x=>x==='delete').length>=3,'every mover deleted');
// THE RETRIEVER CARD (2026-09-26): Lv0 no lethal (dev floor 1), throws 1/2/3/4 at Lv1/3/6/9 (9 levels since 2026-09-27), damage x1.0 -> x3.0.
ctx.self.card={};ctx.level.tod_dev=false;assert.equal(ctx.self.card_level(),0,'no card = no Retriever');
ctx.level.tod_dev=true;assert.equal(ctx.self.card_level(),1,'dev build spawns with it');ctx.level.tod_dev=false;
for(const [lv,ch] of [[0,0],[1,1],[2,1],[3,2],[5,2],[6,3],[8,3],[9,4]])assert.equal(ctx.charges_max(lv),ch,'stored throws Lv'+lv);
let prevM=0;for(let lv=1;lv<=9;lv++){const m=ctx.damage_mult(lv);assert(m>prevM,'damage rises every level');prevM=m;}
assert.equal(ctx.damage_mult(1),1,'Lv1 = the old damage');assert.equal(ctx.damage_mult(9),3,'Lv9 = x3 (9 levels since 2026-09-27)');
assert.equal(ctx.damage(5000,2,20,1,3),600,'Lv8 full charge = 600 at one tenth');assert.equal(ctx.damage(5000,1,11,1,3),5001,'BO2 kill rules untouched by the card');
assert.equal(ctx.ammo_now({ret_on:false,axe_charges:3}),0,'no card, no throw');assert.equal(ctx.ammo_now({ret_on:true,axe_busy:true,axes:[{}],axe_charges:2}),1,'an axe in the air no longer blocks a stored throw (2026-09-26)');
assert.equal(ctx.ammo_now({ret_on:true,axe_charges:1}),1);assert.equal(ctx.ammo_now({ret_on:true,axe_charges:0}),0);
assert(calls.some(c=>Array.isArray(c)&&c[1]===.4),'chain move = TOD_RET_HOP_SECS 0.4 s (BO2 .3; user 2026-09-26 build-14 test: "25% slower" zombie to zombie)');
let unlinks=0;const powerup={origin:[99,0,0],Unlink:()=>unlinks++};
s={ret_on:true,axe_charges:0,axes:[{id:3,axe:{...axe},powerups:[powerup],hits:[],done:false}]};ctx.finish(s,'caught');ctx.destroy(s);assert.equal(s.axes.length,0,'finish empties the air');
assert.equal(unlinks,1,'powerup detached exactly once');assert.deepEqual(powerup.origin,[0,0,0],'powerup delivered to player');
s={ret_on:true,axe_charges:0,axe_cd:0,axes:[{id:4,phase:'flight',flight_left:.5,projectile:{origin:[10,0,0]},impact:false,done:false}]};
for(let i=0;i<11;i++)ctx.step(s,.05);assert(calls.includes('impact'),'native projectile hands over after .5 seconds');assert.equal(s.axes.length,0,'the handed-over (mock-finished) axe leaves the air');
assert(!/\b(?:LoadFX|StopFXOnTag)\s*\(/i.test(src+archer),'regression: these FX calls are not BO3 GSC builtins');
assert(src.includes('waittill( "grenade_fire"')&&src.includes('waittill( "grenade_pullback"'),'engine owns offhand input and release');
assert(!archer.includes('self try_axe()'),'no scripted button throw bypass');
assert(archer.includes('s.view_kind == "flourish" && s.view_logged'),'flourish timer begins after selection');
vm.runInContext(translate(fn('reconcile').replace(/self zm_utility::/g,'self.')),ctx);vm.runInContext(translate(fn('give').replace(/self zm_utility::/g,'self.')),ctx);vm.runInContext(translate(fn('tick')),ctx);ctx.self.give=(...a)=>ctx.give(...a);
ctx.level.weaponNone={name:'none'};
let current={name:'frag'},tactical={name:'monkey'},owns=false,ammo=-1,gives=0;
Object.assign(ctx.self,{
  HasWeapon:()=>owns,TakeWeapon:()=>{},GiveWeapon:()=>{owns=true;gives++},SwitchToOffhand:()=>{},
  SetWeaponAmmoClip:(_weapon,n)=>{ammo=n},get_player_lethal_grenade:()=>current,
  set_player_lethal_grenade:w=>{current=w},get_player_tactical_grenade:()=>tactical,
  set_player_tactical_grenade:w=>{tactical=w}
});
let bare={ret_on:false};ctx.reconcile(bare);assert.equal(current,ctx.level.weaponNone,'no card: stock lethal stripped');assert.equal(gives,0,'no card: no axe');
current={name:'frag'};tactical={name:'monkey'};
ctx.reconcile({ret_on:true,axes:[{}],axe_charges:0});
assert.equal(ammo,0,'stock inventory repair cannot invent a throw: one out, none stored');
assert.equal(current,ctx.level.tod_retriever_weapon);assert.equal(tactical,ctx.level.weaponNone);
ctx.reconcile({ret_on:true,axes:[{}],axe_charges:0});assert.equal(gives,1,'stable inventory is not re-granted every tick');
owns=false;ctx.reconcile({ret_on:true,axe_busy:false,axe_charges:0,axe_cd:4});assert.equal(ammo,0,'repair preserves the refill');
owns=false;ctx.reconcile({ret_on:true,axe_busy:false,axe_charges:2,axe_cd:0});assert.equal(ammo,1,'a stored throw is throwable');
// tick: the card lands mid-run -> the axe is handed over full; refills run whether or not an axe is out (2026-09-26).
ctx.self.card={retriever:0};owns=false;gives=0;let t={ret_on:false,axe_busy:false,axe_charges:0,axe_cd:0};
ctx.tick(t,.05);assert.equal(gives,0,'no card: tick grants nothing');
ctx.self.card={retriever:6};ctx.tick(t,.05);assert.equal(gives,1,'card lands: axe granted');assert.equal(t.axe_charges,3,'full stored throws');assert.equal(ammo,1);
t.axe_charges=0;t.axes=[{},{},{}];ctx.tick(t,.05);assert.equal(ammo,0,'three out, none stored = nothing to throw');
t.axe_charges=1;for(let i=0;i<98;i++)ctx.tick(t,.05);assert.equal(t.axe_charges,1,'refill takes 5 s, and it runs with axes in the air');assert.equal(ammo,1,'the stored one is throwable while the others fly');
ctx.tick(t,.05);ctx.tick(t,.05);assert.equal(t.axe_charges,2,'one throw back after 5 s');
for(let i=0;i<101;i++)ctx.tick(t,.05);assert.equal(t.axe_charges,3,'second throw back after 5 more');for(let i=0;i<50;i++)ctx.tick(t,.05);assert.equal(t.axe_charges,3,'never above the cap');
vm.runInContext(translate(fn('equip').replace(/self zm_utility::/g,'self.')),ctx);
ctx.self.EnableOffhandWeapons=()=>{};ctx.level.zombie_lethal_grenade_player_init={name:'frag'};
current=ctx.level.tod_retriever_weapon;s={};ctx.equip(s);
assert.equal(s.old_lethal,ctx.level.zombie_lethal_grenade_player_init,'respawn cannot save Retriever as the non-Archer grenade');
assert(archer.includes('isdefined( s.old_lethal ) ) self zm_utility::set_player_lethal_grenade'),'non-Archer empty states do not overwrite stock grenade bookkeeping');
vm.runInContext(translate(fn('restore_view_controls',archer)),ctx);
let cycling=0,offhands=0,blocked='menu';
ctx.self.EnableWeaponCycling=()=>cycling++;ctx.self.EnableOffhandWeapons=()=>offhands++;
ctx.self.blocked_reason=()=>blocked;ctx.self.tod_class='heavy';
s={view_restore_controls:true};ctx.restore_view_controls(s);assert.equal(cycling,0,'menu keeps ownership');
blocked='';ctx.restore_view_controls(s);assert.equal(cycling,1,'new class releases the Archer cycling lock');assert.equal(offhands,1);
ctx.restore_view_controls(s);assert.equal(cycling,1,'release occurs once');
ctx.self.tod_class='slasher';s={view_restore_controls:true};ctx.restore_view_controls(s);assert.equal(cycling,2);assert.equal(offhands,2,'every class gets its offhands back');
s={view_restore_controls:true,view_weapon:{}};ctx.restore_view_controls(s);assert.equal(cycling,2,'active presentation keeps ownership');
assert(fn('update',archer).indexOf('restore_view_controls( s )')<fn('update',archer).indexOf('if ( !is_archer'),'deferred release runs even after a class change');
assert(fn('on_spawned',archer).includes('s.view_restore_controls = IS_TRUE( old.view_restore_controls )'),'respawn preserves a deferred release');
console.log('NATIVE RETRIEVER: BO2 charge boundaries, round damage, chain ordering/timing, score, catch/cooldown, powerup cleanup, native handover, input ownership and LoadFX regression passed.');
