// Exercise the shipping director with a deterministic clock and actor pool.
const fs=require('fs'),assert=require('assert/strict');
const read=name=>fs.readFileSync('scripts/zm/zm_tod2_cybercity/'+name+'.gsc','utf8');
const code=read('_tod_cyber_elites');
const body=name=>code.match(new RegExp('function '+name+'\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\}'))[1];
const budget=new Function('round',body('round_budget'));
assert.deepEqual([1,2,3,4,5,13,14,21,22,100].map(budget),[0,0,1,0,1,1,2,2,3,3]);
let translated=body('director').replace(/level endon\([^;]+;/g,'').replace(/level flag::wait_till\([^;]+;/g,'')
 .replace(/wait 0\.5;/g,'yield;').replace(/tod_doppelghast::/g,'doppel.').replace(/tod_mangler::/g,'mangler.')
 .replace(/(actor|target) GetEntityNumber\(\)/g,'$1.id').replace(/\( 0, facing\[1\], 0 \)/g,'[0,facing[1],0]');
const make=new Function('level','doppel','mangler','hold_reason','dev_log','round_budget','isdefined','VectorToAngles',
 'return function*(){let seen_round,left,clock,sequence,previous_reason,round,reason,target,org,kind,facing,actor;'+translated+'}');
function harness(round=3){
 const level={round_number:round},spawns=[],logs=[],state={hold:'',target:true,position:true,pool:true};
 const actor=kind=>{if(!state.pool)return; const a={id:spawns.length+2,health:750};spawns.push({round:level.round_number,kind});return a;};
 const doppel={target_player:()=>state.target?{id:1,origin:0}:undefined,reloc_point:()=>state.position?1:undefined,spawn_hunter:()=>actor('doppelgast')};
 const mangler={spawn_at:()=>actor('mangler')};
 const g=make(level,doppel,mangler,()=>state.hold,m=>logs.push(m),budget,x=>x!==undefined,()=>[0,0,0])();g.next();
 return {level,state,spawns,logs,tick(n){for(let i=0;i<n;i++)g.next();}};
}
let h=harness();h.tick(49);assert.equal(h.spawns.length,0);h.tick(1);assert.deepEqual(h.spawns,[{round:3,kind:'doppelgast'}]);h.tick(300);assert.equal(h.spawns.length,1);
h.level.round_number=4;h.tick(150);assert.equal(h.spawns.length,1);h.level.round_number=5;h.tick(50);assert.equal(h.spawns[1].kind,'mangler');
h.level.round_number=22;h.tick(200);assert.deepEqual(h.spawns.slice(2).map(x=>x.kind),['doppelgast','mangler','doppelgast']);
for(const reason of ['upgrade_pause','world_pause','spawns_held','spire_trial','finale','actor_reserve','shared_elite_roof','mix_cap']){
 h=harness();h.tick(30);h.state.hold=reason;h.tick(1000);assert.equal(h.spawns.length,0);h.state.hold='';h.tick(19);assert.equal(h.spawns.length,0);h.tick(1);assert.equal(h.spawns.length,1);
 assert.equal(h.logs.filter(x=>x.includes('reason='+reason)).length,1);
}
for(const field of ['target','position','pool']){h=harness();h.state[field]=false;h.tick(150);assert.equal(h.spawns.length,0);h.state[field]=true;h.tick(50);assert.equal(h.spawns.length,1);}
h=harness(22);h.state.hold='mix_cap';h.tick(100);h.level.round_number=23;h.tick(1);h.state.hold='';h.tick(250);assert.equal(h.spawns.length,3);assert(h.logs.some(x=>x.includes('expired_budget=3')));
console.log('PASS: shipping elite director timing, introductions, growth/cap, pause clocks, bounded logs, target/position/pool retries and round debt expiry.');

// A packed xanim is insufficient: scripted %clips must be registered in the
// actor's AI mapping table to exist in its runtime generic tree. The 13:07
// user run caught hb_mangler_cannon missing here despite a successful link.
function missingScriptedClips(script,table){
 const mapped=new Set(table.split(/\r?\n/).filter(row=>!row.trim().startsWith('#')).flatMap(row=>row.split(',').slice(1).map(cell=>cell.trim())));
 return [...new Set([...script.matchAll(/%([a-zA-Z_][a-zA-Z0-9_]*)/g)].map(m=>m[1]))].filter(clip=>!mapped.has(clip));
}
for(const [scriptName,tableName] of [['_tod_mangler','hb_mangler'],['_tod_doppelghast','hb_doppelghast_dev']]){
 const script=read(scriptName),table=fs.readFileSync('animtables/'+tableName+'.ai_am','utf8');
 assert.match(script,/#using_animtree\(\s*"generic"\s*\)/);
 assert.deepEqual(missingScriptedClips(script,table),[],scriptName+' scripted clip absent from generic tree mapping');
 if(scriptName==='_tod_mangler'){
  const broken=table.split(/\r?\n/).filter(row=>!row.split(',').slice(1).includes('hb_mangler_cannon')).join('\n');
  assert.deepEqual(missingScriptedClips(script,broken),['hb_mangler_cannon'],'must reproduce the actual user load failure');
 }
}
console.log('PASS: both elite generic-tree mappings contain every scripted %animation; removing the cannon row reproduces the user load failure.');
