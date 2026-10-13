// Execute the shipping tier selection and delayed FX-play coroutine.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_class_kit.gsc','utf8');
function fn(name){return source.match(new RegExp('function '+name+'\\([^)]*\\)[^{]*\\{([\\s\\S]*?)\\n\\}'))[0];}
const ctx=vm.createContext({isdefined:x=>x!==undefined,IS_TRUE:x=>x===true,Min:Math.min,dev_log:()=>{},level:{tod_dev:true}});
for(const m of source.matchAll(/^#define\s+(\w+)\s+("[^"]+"|[\d.]+)/gm))ctx[m[1]]=JSON.parse(m[2]);
let tier=1;
ctx.self={c4_max:()=>tier,cluster_max:()=>3,GetEntityNumber:()=>0,IPrintLn:()=>{}};
for(const name of ['kit_tier','c4_tier_fx','c4_tier_radius','c4_tier_quake']) {
 const translated=fn(name).replace(/self (c4_max|cluster_max|GetEntityNumber|IPrintLn)\(/g,'self.$1(');
 vm.runInContext(translated,ctx);
}
for(const dev of [false,true])for(tier=1;tier<=4;tier++) {
 ctx.level.tod_dev=dev;
 for(let throwNo=0;throwNo<100;throwNo++) {
  assert.equal(ctx.kit_tier('c4'),tier,'card tier must never cycle with throws');
  assert.equal(ctx.c4_tier_fx(tier),'explosions/fx_exp_generic_lg','every charge must select the big effect');
 }
 assert(Math.abs(ctx.c4_tier_radius(tier)-(144+24*tier))<1e-8,'retain upgrade-based damage radius');
}
ctx.level.tod_dev=true;
assert.deepEqual(Array.from({length:6},()=>ctx.kit_tier('cluster')),[1,2,3,1,2,3],'C4 fix must not alter the Cluster preview');
assert.equal(ctx.c4_tier_fx(undefined),'explosions/fx_exp_generic_lg');
const GeneratorFunction=Object.getPrototypeOf(function*(){}).constructor;
const body=fn('fx_at_play').split('{').slice(1).join('{').replace(/}\s*$/,'')
 .replace(/self endon\([^;]+;/g,'')
 .replace(/wait 0.05;/,'yield .05;').replace(/self GetEntityNumber\(\)/g,'self.id');
const play=new GeneratorFunction('self','effect','PlayFXOnTag','isdefined','dev_log',body);
const emitted=[],logs=[];
const host={id:77,tod_c4_fx_id:23,origin:[0,0,0]};
const run=play(host,'explosions/fx_exp_generic_lg',(...args)=>emitted.push(args),x=>x!==undefined,s=>logs.push(s));
assert.equal(run.next().value,.05);assert.equal(emitted.length,0,'wait for the host to replicate');
assert.equal(run.next().done,true);assert.equal(emitted.length,1,'one emission per host');
assert.equal(emitted[0][1],host);assert(logs[0].includes('id=23')&&logs[0].includes('host=77'));
const blast=fn('blast');
assert(blast.includes('C4_FX_FAIL')&&blast.includes('reason=entity_pool_full'));
assert(!blast.includes('tier >= 3'),'full presentation must not depend on tier');
assert(blast.includes('fx.tod_c4_fx_id = fx_id'));
assert(fn('expire').includes('C4_FX_END'));
console.log('C4 CONSISTENCY: 800 throws select the full blast, card radii preserved, Cluster unchanged, delayed playback and correlated logs passed. Native rendering awaits user playtest.');
