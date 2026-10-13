'use strict';
// Exercise the shipping power transition and init, including partial spawn failure.
const fs=require('fs'),assert=require('assert/strict'),cp=require('child_process');
cp.execFileSync(process.execPath,[__dirname+'/15_conduit_mounts.js','--check'],{stdio:'inherit'});
const src=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_power_conduits.gsc','utf8');
const body=n=>src.match(new RegExp('function '+n+'\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\}'))[1];
const layout=JSON.parse(fs.readFileSync('art/cybercity_materials/color_restoration/conduit_mounts.json','utf8')),mounts=layout.groups;
const translate=s=>s.replace(/level endon\([^;]+;/g,'').replace(/level flag::wait_till\( "power_on" \);/g,'yield;')
 .replace(/level flag::(exists|get)\(/g,'flags.$1(').replace(/tod_conduit_data::/g,'data.').replace(/\.size/g,'.length')
 .replace(/host (SetModel|NotSolid)\(/g,'host.$1(').replace(/level thread power_watch\(\);/g,'threads++;')
 .replace(/foreach \( host in level.tod_conduit_hosts \)/g,'for (const host of level.tod_conduit_hosts)');
const model=new Function('model','powered',body('model_for_power'));
function harness(powered,fail=-1){
 const level={},hosts=[],logs=[],data={origins:()=>mounts.map(r=>r.org),angles:()=>mounts.map(r=>r.angles),kinds:()=>mounts.map(r=>r.kind),models:()=>mounts.map(r=>r.model),counts:()=>mounts.map(r=>r.count)};
 let index=0;const flags={exists:()=>true,get:()=>powered},Spawn=(kind,org)=>{
  if(index++===fail)return undefined;
  const h={kind,org,SetModel(v){this.model=v;},NotSolid(){this.solid=false;}};hosts.push(h);return h;
 };
 const names=['level','flags','data','Spawn','isdefined','model_for_power','conduit_log'],args=[level,flags,data,Spawn,x=>x!==undefined,model,m=>logs.push(m)];
 const init=new Function(...names,'return function(){let orgs,angles,kinds,models,counts,channels,powered,i,host,threads=0;'+translate(body('init'))+'return threads;}')(...args);
 const on=new Function(...names,'return function*(){let live,channels;'+translate(body('power_watch'))+'}')(...args);
 return{level,hosts,logs,init,on};
}
let h=harness(false);assert.equal(h.init(),1);assert.equal(h.hosts.length,mounts.length);
assert(h.hosts.every((x,i)=>x.model===mounts[i].model+'_off'&&x.solid===false));
h.init();assert.equal(h.hosts.length,mounts.length,'duplicate initialization cannot add fixtures');
let g=h.on();g.next();assert(h.hosts.every(x=>x.model.endsWith('_off')),'dark until power flag releases');g.next();assert(h.hosts.every(x=>x.model.endsWith('_on')));
assert(h.hosts.every((x,i)=>x.model===mounts[i].model+'_on'),'Each region must use its own geometry after power');
assert(h.logs.some(x=>x===`ON hosts=${mounts.length} channels=${layout.rows.length} reason=power_on`));
h=harness(true);h.init();assert(h.hosts.every(x=>x.model.endsWith('_on')),'initialization after power must use lit twins immediately');
h=harness(false,17);h.init();assert.equal(h.hosts.length,mounts.length-1);assert(h.logs.some(x=>x.startsWith('SPAWN_FAILED id=17')));g=h.on();g.next();g.next();assert(h.hosts.every(x=>x.model===x.tod_conduit_model+'_on'));
assert(h.logs.includes(`ON hosts=${mounts.length-1} channels=${layout.rows.length-mounts[17].count} reason=power_on`),'Failure cannot shift another region onto the wrong model');
const alarm=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_crown_alarm.gsc','utf8');assert(alarm.includes('tod_power_conduits::init();'));
assert(!alarm.match(/function stop\(\)[\s\S]*tod_power_conduits::/),'alarm seal must not shut down the powered tower');
assert(src.includes('level flag::wait_till( "power_on" )'),'persistent flag supports power before init and joining players');
console.log('CONDUIT_STATE_PASS: dark before power; all on after power; init already powered; idempotent init; spawn failure logged and isolated; no collision; alarm seal independent.');
