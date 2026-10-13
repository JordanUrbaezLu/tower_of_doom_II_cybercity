// Execute the actual staged HUD/update/client-watch bodies with engine boundaries mocked.
const fs=require('fs'),assert=require('assert/strict');
const read=p=>fs.readFileSync(p,'utf8');
const gsc=read('scripts/zm/zm_tod2_cybercity/_tod_cyber_sword.gsc');
const csc=read('scripts/zm/zm_tod2_cybercity/_tod_cyber_sword.csc');
const kit=read('art/cyber_sword/integration/scripts/zm/zm_tod2_cybercity/_tod_class_kit.gsc');
const body=(code,name)=>code.match(new RegExp('function '+name+'\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\}'))[1];
const defined=x=>x!==undefined;
const updateText=body(gsc,'update').replace(/\/#|#\//g,'')
 .replace('self clientfield::set_to_player(','self.send(').replace('self GetEntityNumber()','self.id');
const update=new Function('self','level','ready','reason','isdefined','IsAlive','IS_TRUE','GetTime','PrintLn',
 'let value,line;'+updateText);
const fields=[],logs=[];
const player={id:0,alive:true,send:(name,v)=>fields.push([name,v]),tod_bash_charges:1,
 gs_kills_left:()=>left,gs_tier:()=>tier,c4_max:()=>1,cluster_max:()=>1,
 LuiNotifyEvent:()=>{},update:(r,reason)=>update(player,{tod_dev:true},r,reason,defined,p=>p.alive,Boolean,()=>10,x=>logs.push(x))};
let left=20,tier=3,dev=false;
const hudText=body(kit,'hud_send').replace(/self tod_cyber_sword::update\(/g,'self.update(')
 .replace(/self tod_necro_summon::soul_bomb_left\(\)/g,'0')
 .replace(/self (gs_kills_left|gs_tier|c4_max|cluster_max|LuiNotifyEvent)\(/g,'self.$1(')
 .replace(/&"/g,'"');
const hud=new Function('self','kit','TOD_KIT_NECRO','TOD_KIT_WARRIOR','TOD_GS_TIER_MIN','unlimited','GetTime','IS_TRUE','isdefined','Int',
 'let lethal,tac,now,key;'+hudText);
const tick=(k=1)=>hud(player,k,3,1,3,()=>dev,()=>10,Boolean,defined,Math.trunc);
tick();assert.equal(player.tod_cyber_sword_ready,0);
for(let i=0;i<40;i++)tick();assert.equal(fields.length,1,'no per-frame replication/log spam');
left=0;tick();assert.equal(player.tod_cyber_sword_ready,1);
player.tod_gs_busy=true;tick();assert.equal(player.tod_cyber_sword_ready,0);
player.tod_gs_busy=false;left=9;tick();assert.equal(player.tod_cyber_sword_ready,0);
dev=true;tick();assert.equal(player.tod_cyber_sword_ready,1,'existing dev bypass honored');
tier=2;tick();assert.equal(player.tod_cyber_sword_ready,0,'dev bypass must not unlock tier');
tier=3;tick();player.alive=false;tick();assert.equal(player.tod_cyber_sword_ready,0);
player.alive=true;tick();tick(2);assert.equal(player.tod_cyber_sword_ready,0);
tick();tick(3);assert.equal(player.tod_cyber_sword_ready,0);
assert.equal(logs.length,fields.length,'every edge has a diagnostic');
assert(body(kit,'kit_switch').includes('tod_cyber_sword::update( false, "kit_switch" )'));
assert(body(kit,'gravsmash_fire').indexOf('tod_cyber_sword::update')<body(kit,'gravsmash_fire').indexOf('real_weapon( TOD_GS_SWORD_PROXY )'));
assert(hudText.indexOf('self.update(')<hudText.indexOf('self.tod_kit_hud == key'),'readiness precedes HUD throttle');
const isSword=new Function('weapon','isdefined','IsSubStr',body(csc,'is_sword'));
const valid=w=>isSword(w,defined,(s,part)=>s.includes(part));
let weapon={name:'cc_gold_sword_up_k3'},mapped=[];
const owner={tod_cyber_sword_ready:1,MapShaderConstant:(...a)=>mapped.push(a)};
const watchText=body(csc,'glow_watch').replace(/self endon\([^;]+;/g,'')
 .replace('self MapShaderConstant(','self.MapShaderConstant(').replace('wait 0.05;','yield;');
const watch=new Function('self','GetCurrentWeapon','is_sword','isdefined','IS_TRUE','Min',
 'return function*(localClientNum){let last_weapon,brightness,weapon,target;'+watchText+'}')(owner,()=>weapon,valid,defined,Boolean,Math.min);
const loop=watch(0);for(let i=0;i<6;i++)loop.next();assert.equal(mapped.at(-1)[4],1);
owner.tod_cyber_sword_ready=0;loop.next();assert.equal(mapped.at(-1)[4],0,'spent is immediately dark');
weapon={name:'cc_gauntlet_k0'};const n=mapped.length;loop.next();assert.equal(mapped.length,n,'other weapons own their constants');
weapon={name:'tod_cyber_sword_cast'};loop.next();assert.equal(mapped.length,n,'cast uses its static ready skin');
owner.tod_cyber_sword_ready=1;weapon={name:'tod_cyber_sword_bash'};loop.next();assert(mapped.at(-1)[4]>0&&mapped.at(-1)[4]<1);
// build 16: the Warrior's sword Bash proxy (the Cyber Sword model on the bat's lunge clip)
weapon={name:'tod_bash_sword_zm'};loop.next();assert(mapped.at(-1)[4]>0&&mapped.at(-1)[4]<1,'sword Bash proxy drives the glow');
assert.equal(valid({name:'tod_bash_sword'}),true,'engine-stripped proxy name');
assert.equal(valid(undefined),false);assert.equal(valid({name:'cc_gold_sword_k0_zm'}),true);
for(const code of [gsc,csc])assert(code.includes('"toplayer", "todCyberSwordReady", VERSION_SHIP, 1, "int"'));
assert(body(csc,'on_spawned').includes('self != GetLocalPlayer( localClientNum )'));
assert(body(csc,'cleanup').includes('"death", "disconnect", "entityshutdown"'));
// LT-fix 2026-10-05: every game over threw "cannot set field of removed entity" here (~6.15 s after end_game, when
// stock player_intermission removes the client player). The guard sits between the wait and the first field write.
{
 const guarded=cl=>{const w=cl.indexOf('util::waittill_any('),g=cl.indexOf('if ( !isdefined( self ) )'),f=cl.indexOf('self.tod_cyber_sword_ready = 0;');return w>0&&g>w&&f>g;};
 assert(guarded(body(csc,'cleanup')),'cleanup returns when the client entity is gone before it writes a field');
 const OLD='\n\tself endon( "tod_cyber_sword_restart" );\n\tself util::waittill_any( "death", "disconnect", "entityshutdown" );\n\tself notify( "tod_cyber_sword_stop" );\n\tself.tod_cyber_sword_ready = 0;';
 assert(!guarded(OLD),'negative control: the 2026-09-26 cleanup wrote the field unguarded');
 assert(/#define TOD_SWORD_C_LOG\s+[01]\b/.test(csc)&&body(csc,'c_log').includes('"[TOD_SWORD_C] "')&&body(csc,'cleanup').includes('c_log( "CLEANUP'),'the removed-entity exit is logged ([TOD_SWORD_C] CLEANUP, its own switch)');
}
assert(read('art/cyber_sword/integration/scripts/zm/zm_tod2_cybercity.csc').includes('#using scripts\\zm\\zm_tod2_cybercity\\_tod_cyber_sword;'));
console.log('CYBER_SWORD_STATE_PASS: HUD/tier/kills/busy/dev/class/death, edge logs, client fade, switch isolation, bash/slam and field lockstep');
