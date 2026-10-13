// Run the shipping pose coroutine with a small event/cancellation harness.
const fs=require('fs'), assert=require('assert/strict');
const source=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_necro_summon.gsc','utf8');
function body(name){return source.match(new RegExp('function '+name+'\\([^)]*\\)[^{]*\\{([\\s\\S]*?)\\n\\}'))[1];}
// 2026-10-05 THE ONE PLAY (user: "they go up and animate, and then they stick to the floor and
// then freeze"): the lift clip plays ONCE; the hold slows it in place (bind_hold_keep). A second
// play re-places the body at the align point, the floor.
function translatePose(text){return text
 .replace(/self endon\(/g,'self.endon(')
 .replace(/self thread animation::play\(/g,'self.play(')
 .replace(/self thread bind_hold_keep\(/g,'self.keep(')
 .replace(/self ASMSetAnimationRate\(/g,'self.rate(')
 .replace(/self GetEntityNumber\(\)/g,'self.id')
 .replace(/wait rise_s;/,'yield rise_s;');}
const GeneratorFunction=Object.getPrototypeOf(function*(){}).constructor;
function makePose(text){return new GeneratorFunction('self','owner','GetAnimLength','min','isdefined','GetTime','dev_log','TOD_BIND_ANIM','Int','TOD_BIND_HOLD_RATE',
 'let pose, rise_s, rate;'+translatePose(text));}
function runPose(make,lv,cancel){
 const duration=Math.floor(7200*(1-.071*lv));
 let now=0;const calls=[],rates=[],keeps=[],events=new Set(),logs=[];
 const owner={tod_necro_bind_ms:duration,tod_necro_bind_t0:0};
 const z={id:42,tod_necro_binder:owner,tod_necro_bind_origin:[1,2,3],tod_necro_bind_angles:[0,90,0],origin:[1,2,41],
  endon:e=>events.add(e),play:(...a)=>calls.push(a),rate:r=>rates.push(r),keep:o=>keeps.push(o)};
 const run=make(z,owner,()=>1.5,Math.min,x=>x!==undefined,()=>now,s=>logs.push(s),'lift',Math.trunc,.01);
 const rise=run.next();assert.equal(rise.done,false);
 const first=calls[0];
 if(events.has(cancel))run.return();
 else {if(cancel==='owner_gone')z.tod_necro_binder=undefined;now=rise.value*1000;run.next();}
 return {duration,calls,rates,keeps,logs,rise,first,owner};
}
const pose=makePose(body('bind_pose'));
for(let lv=0;lv<=9;lv++) {
 for(const cancel of ['none','tod_necro_bind_end','death','owner_gone']) {
  const r=runPose(pose,lv,cancel);
  assert.equal(r.first[5],0,'automatic blend-out must stay disabled');
  assert.equal(r.rates.length,1,'the rise sets its pace once');
  assert(Math.abs(r.rates[0]*r.first[3]*r.rise.value/1.5-.55)<1e-9,'rise must stop in the held portion');
  assert(r.rise.value*1000<r.duration,'hold begins before conversion at every power level');
  assert.equal(r.calls.length,1,'ONE play, never restarted: a second play re-places the body on the floor (user 2026-10-05)');
  if(cancel==='none') {
   assert.equal(r.keeps.length,1);assert.equal(r.keeps[0],r.owner,'the hold keeps THIS bind');
   assert.equal(r.logs.length,1);assert(/lift_z=38/.test(r.logs[0]),'the hold logs the lift height');
  } else assert.equal(r.keeps.length,0,'cancel/death/owner loss cannot start a delayed hold');
 }
}
// NEGATIVE CONTROL: the 2026-10-04 hold (a second play at the 55% pose) fails the one-play contract.
{
 const shipped=body('bind_pose');
 const old=shipped.replace('self thread bind_hold_keep( owner );',
  'self thread animation::play( TOD_BIND_ANIM, self.tod_necro_bind_origin, self.tod_necro_bind_angles, 0, 0, 0, 0, pose );');
 assert.notEqual(old,shipped,'negative control anchor moved');
 const r=runPose(makePose(old),0,'none');
 assert.equal(r.calls.length,2,'negative control: the old hold is a second play');
 assert.deepEqual(r.calls[1].slice(1,3),r.first.slice(1,3),'negative control: the old hold restarts at the floor align point');
}
// THE HOLD KEEPER: re-asserts the crawl every frame while THIS bind holds the zombie.
const keep=body('bind_hold_keep');
for(const s of ['self endon( "death" )','self endon( "tod_necro_bind_end" )','IS_TRUE( self.tod_necro_lifted ) && self.tod_necro_binder === owner','self ASMSetAnimationRate( TOD_BIND_HOLD_RATE )','wait 0.05'])
 assert(keep.includes(s),'bind_hold_keep lost: '+s);
assert(/#define TOD_BIND_HOLD_RATE\s+0\.0\d/.test(source),'TOD_BIND_HOLD_RATE must be a crawl (under 0.1)');
// The drop and the conversion take the crawl off before the zombie walks or dies.
assert(body('bind_drop').includes('self ASMSetAnimationRate( 1 )'),'bind_drop restores the rate');
{
 const fin=body('bind_finish');
 const at=fin.indexOf('z ASMSetAnimationRate( 1 )');
 assert(at>0&&at<fin.indexOf('z.tod_necro_lifted = undefined'),'bind_finish restores the rate before it clears the lift');
}
// The round's pace sweep leaves a lifted zombie alone (it would run the held clip into its fall).
{
 const speed=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_zombie_speed.gsc','utf8');
 const sweep=speed.match(/function apply_speed_for_round\([^)]*\)[^{]*\{([\s\S]*?)\n\}/)[1];
 const at=sweep.indexOf('IS_TRUE( self.tod_necro_lifted )');
 assert(at>0&&at<sweep.indexOf('ASMSetAnimationRate'),'the pace sweep must skip a lifted zombie before it writes a rate');
}
// OFF LIMITS WHILE BOUND (2026-10-05): helpers and companions leave the zombie alone; its own ignoreme comes back.
{
 const st=body('bind_start'),dr=body('bind_drop'),fin=body('bind_finish'),ht=body('helper_target');
 assert(st.indexOf('z.tod_necro_bind_ig = ( IS_TRUE( z.ignoreme ) ? 1 : 0 );')>0&&st.indexOf('z.ignoreme = true;')>st.indexOf('z.tod_necro_bind_ig ='),'bind_start keeps the zombie own ignoreme, then sets it');
 const back='ignoreme = ( ';
 assert(dr.indexOf(back)>0&&dr.indexOf(back)<dr.indexOf('if ( !IsAlive( self ) )'),'bind_drop puts ignoreme back before its dead-zombie return');
 assert(fin.indexOf(back)>0&&fin.indexOf(back)<fin.indexOf('z.tod_necro_lifted = undefined'),'bind_finish puts ignoreme back');
 assert(ht.includes('!isdefined( helper.tod_necro_target.tod_necro_binder )')&&ht.includes('if ( isdefined( z.tod_necro_binder ) ) continue;'),'helper_target never keeps or picks a bound zombie');
}
// A lost bind says why (the aim, the distance, a kill) so the next log can tell them apart.
assert(source.includes('self bind_cancel( "lost_" + self bind_lost_why( b ) )'));
for(const w of ['"dead"','"taken"','"timeout"','"far"','"aim"']) assert(body('bind_lost_why').includes('return '+w),'bind_lost_why lost '+w);
assert(body('bind_drop').indexOf('notify( "tod_necro_bind_end" )')<body('bind_drop').indexOf('animation::stop'));
assert(body('bind_finish').includes('kind == "thrall" && IS_TRUE( z.tod_necro_lifted )'));
assert(body('bind_finish').includes('scripted=')&&body('bind_finish').includes('IsPlayingAnimScripted()'));
const client=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_necro_skull.csc','utf8');
const callback=client.match(/function necro_bomb_play[^]*?\n\}/)[0];
assert(!callback.includes('level._effect[ "tod_necro_bomb" ]'),'caster flash must never play');
assert(callback.includes('tod_necro_ring_'));
assert(callback.indexOf('wait 0.05')<callback.indexOf('clientfield::get'), 'read the radius after snapshot callbacks finish');
const material=fs.readFileSync('source_data/tod_necro_pulse.gdt','utf8');
assert(material.includes('"materialType" "effect_lit_emissive_blend"'));
assert(material.includes('"scaleRGB" "64"'), 'retain native ring HDR brightness');
const pulseBody=callback.slice(callback.indexOf('{')+1,callback.lastIndexOf('}'))
 .replace('wait 0.05;','yield .05;')
 .replace('self clientfield::get( "tod_necro_bomb_band" )','self.band')
 .replace('self GetEntityNumber()','self.id')
 .replace('origin + ( 0, 0, 12 )','[origin[0],origin[1],origin[2]+12]')
 .replace('( 0, 0, 1 )','[0,0,1]').replace('( 1, 0, 0 )','[1,0,0]');
const pulsePlay=new GeneratorFunction('self','lc','origin','level','isdefined','PlayFX','fx_log','let band,handle;'+pulseBody);
for(const lateBand of [0,1,2,3]) {
 const self={id:0,band:0},calls=[],level={_effect:Object.fromEntries([0,1,2,3].map(i=>['tod_necro_ring_'+i,'ring'+i]))};
 const run=pulsePlay(self,0,[10,20,30],level,x=>x!==undefined,(...args)=>{calls.push(args);return 1},()=>{});
 assert.equal(run.next().value,.05);assert.equal(calls.length,0);
 self.band=lateBand;self.origin=[999,999,999];run.next();
 assert.equal(calls[0][1],'ring'+lateBand,'same-snapshot radius update must reach first cast');
 assert.deepEqual(calls[0][2],[10,20,42],'moving caster must not drag the pulse origin');
}
for(let i=0;i<4;i++) {
 const fx=fs.readFileSync(`share/raw/fx/tod/necro/fx_necro_pulse_ring${i}.efx`,'utf8');
 assert.equal((fx.match(/\n\tname /g)||[]).length,38);
 assert.equal((fx.match(/name \"soul_wisp_/g)||[]).length,24);
 assert.equal((fx.match(/name \"soul_glyph_/g)||[]).length,12);
 assert.equal((fx.match(/lifeSpanMsec 750 0;/g)||[]).length,36);
 assert(fx.includes('gfx_smk_whisp_anim_em'));
 assert(fx.includes('gfx_keeper_symbols_zod_em'));
 assert(!fx.includes('gfx_fire_'));
 const souls=fx.split(/(?=\{\r?\n\tname )/).filter(b=>/name "soul_(wisp|glyph)_/.test(b));
 const field=(b,k)=>Number(b.match(new RegExp('\\n\\t'+k+' ([^ ;\\r\\n]+)'))[1]);
 for(const soul of souls) {
  const y=field(soul,'spawnOrgY'),z=field(soul,'spawnOrgZ');
  assert(Math.abs(Math.hypot(y,z)-88)<.001,'souls must spawn outside the caster');
  const vy=field(soul,'velGraph0Y'),vz=field(soul,'velGraph0Z');
  assert(Math.abs(Math.hypot(y+vy*.14,z+vz*.14)-[360,440,520,600][i])<.001,'souls must reach the damage edge with the wave');
  assert.equal(field(soul,'spawnOneShot'),1,'bounded one-shot soul particles');
 }
 assert.equal((fx.match(/"mtl_tod_necro_pulse"/g)||[]).length,2);
 assert(!/dynamicLight|lensFlare|gfx_ring_thin/.test(fx));
 assert.equal((fx.match(/lifeSpanMsec 800 0;/g)||[]).length,2);
}
for(const file of fs.readdirSync('share/raw/fx/tod/necro').filter(x=>/^fx_necro_mangler_aura.*\.efx$/.test(x))) {
 const fx=fs.readFileSync('share/raw/fx/tod/necro/'+file,'utf8');
 assert(!fx.includes('gfx_fire_'),'aura flame atlas survived in '+file);
}
const child=fs.readFileSync('share/raw/fx/tod/necro/fx_necro_mangler_aura_c0.efx','utf8');
assert.equal((child.match(/gfx_smk_whisp_anim_em/g)||[]).length,3,'keep the soul wisps');
console.log('NECRO VISIBILITY: one-play lift + in-air hold (old floor restart caught), pose/cancel/death/owner-loss across ten power levels, conversion guard, flame removal and four wave bands passed. Native pose/FX review pending.');
