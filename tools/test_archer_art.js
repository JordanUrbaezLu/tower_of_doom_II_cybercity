// Execute shipping cleanup/callback code to catch split-screen and stale-host leaks.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const gsc=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_archer.gsc','utf8');
const csc=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_archer.csc','utf8');
const retriever=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_retriever.gsc','utf8');
function body(src,name){
  const open=src.indexOf('{',src.indexOf('function '+name+'('));let end=open+1,depth=1;
  while(depth){if(src[end]==='{')depth++;if(src[end]==='}')depth--;end++;}
  return src.slice(open+1,end-1);
}
const calls=[];
const ctx=vm.createContext({isdefined:v=>v!==undefined,self:{archer_beams:[]},BeamKill:(c,b)=>calls.push(['kill',c,b]),notify:n=>calls.push(['notify',n]),start:(c,v)=>calls.push(['start',c,v])});
const cb=body(csc,'hook_cb').replace(/self notify\(/g,'notify(').replace(/self thread hook_start\(/g,'start(');
vm.runInContext('function callback(localClientNum,oldVal,newVal){'+cb+'}',ctx);
ctx.self.archer_beams[0]=11;ctx.self.archer_beams[1]=22;
ctx.callback(0,17,0);
assert.equal(ctx.self.archer_beams[0],undefined);assert.equal(ctx.self.archer_beams[1],22);
assert.deepEqual(calls.filter(x=>x[0]==='kill'),[['kill',0,11]]);
ctx.callback(1,18,18);assert.deepEqual(calls.at(-1),['start',1,18]);
ctx.callback(1,18,0);assert.equal(calls.filter(x=>x[0]==='kill').length,2,'zero after a reset cannot double-kill old handles');
ctx.callback(0,0,undefined);assert.equal(calls.at(-1)[0],'notify','missing/zero snapshot never starts a cable');
assert(csc.includes('self waittill( "entityshutdown" )') && csc.includes('BeamKill( localClientNum, beam )'),'delete without replicated zero kills cable');
assert(csc.includes('!CF_HOST_ONLY'),'remote clients receive cable');
assert(csc.includes('attempts < 30'),'missing DObj cannot create immortal wait');

const freed=[];
ctx.s={hook:{id:'hook'},hook_audio:{id:'audio'}};
ctx.destroy=e=>freed.push(e.id);ctx.stop=()=>freed.push('stop');ctx.clear=()=>freed.push('zero');
const clean=body(gsc,'delete_hook').replace(/s.hook clientfield::set\([^;]+;/g,'clear();').replace(/s\.(hook|hook_audio) Delete\(\)/g,'destroy(s.$1)').replace(/s.hook_audio Stop(?:LoopSound|Sounds)\([^;]+;/g,'stop();');
vm.runInContext('function cleanup(s){'+clean+'}',ctx);
ctx.cleanup(ctx.s);ctx.cleanup(ctx.s);
assert.equal(ctx.s.hook,undefined);assert.equal(ctx.s.hook_audio,undefined);
assert.deepEqual(freed,['zero','hook','stop','stop','audio'],'idempotent cleanup stops loop before deleting host');
for(const name of ['watch','on_spawned','end_grapple'])assert(body(gsc,name).includes('delete_hook('),'host cleanup at '+name);
assert(!gsc.includes('PlaySoundAtPosition('),'custom 3D cues use the proven emitter path');
assert(body(gsc,'end_axe').includes('tod_retriever::finish') && body(retriever,'destroy').includes('destroy_axe( a )') && body(retriever,'destroy_axe').includes('a.axe Delete()'),'normal axe end deletes every attached-trail host (one struct per axe since 2026-09-26)');
for(const name of ['watch','on_spawned'])assert(body(gsc,name).includes('delete_axe('),'axe cleanup at '+name);
const stopAxe=body(gsc,'stop_axe_audio').replace(/s.axe_audio Delete\(\)/g,'destroy(s.axe_audio)').replace(/s.axe_audio Stop(?:LoopSound|Sounds)\([^;]+;/g,'stop();');
vm.runInContext('function stop_axe_audio(s){'+stopAxe+'}',ctx);
const deleteAxe=body(retriever,'destroy_axe').replace(/foreach \( powerup in a.powerups \)/g,'for (const powerup of a.powerups)').replace(/powerup Unlink\(\)/g,'powerup.Unlink()').replace(/a\.(axe|axe_audio|projectile) Delete\(\)/g,'destroy(a.$1)').replace(/a.axe_audio Stop(?:LoopSound|Sounds)\([^;]+;/g,'stop();').replace(/a.projectile notify\([^;]+;/g,'clear();');
vm.runInContext('function delete_axe(a){'+deleteAxe+'}',ctx);
freed.length=0;ctx.s={axe:{id:'axe'},axe_audio:{id:'spin'}};
ctx.delete_axe(ctx.s);ctx.delete_axe(ctx.s);
assert.deepEqual(freed,['stop','stop','spin','axe'],'spin loop and attached-trail host cleaned exactly once');
assert(body(gsc,'update').includes('stop_axe_audio( s )'),'menus silence paused projectile');
const zone=fs.readFileSync('zone_source/zm_tod2_cybercity.zone','utf8');
for(const asset of ['beam,tod_archer_cable','xmodel,tod_archer_hook','fx,tod/archer/fx_tod_archer_trail','scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_archer.csc'])assert(zone.includes(asset),asset);
const entry=fs.readFileSync('scripts/zm/zm_tod2_cybercity.csc','utf8');assert(entry.includes('#using scripts\\zm\\zm_tod2_cybercity\\_tod_archer;'));
console.log('ARCHER ART passed: independent viewers, refresh/zero/deletion, idempotent sound/host cleanup, bounded waits and native wiring. User playtest pending.');
