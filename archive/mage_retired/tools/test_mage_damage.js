// Run the shipping GSC arithmetic and final-damage HUD wrapper with native
// calls stubbed. Engine armor remains native; its returned value is the oracle.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const root='scripts/zm/zm_tod2_cybercity/';
const mage=fs.readFileSync(root+'_tod_mage_elements.gsc','utf8');
const bosses=fs.readFileSync(root+'_tod_bosses.gsc','utf8').replace(/\r/g,'');
const ui=fs.readFileSync(root+'_tod_upgrade_ui.gsc','utf8');
const upgrades=fs.readFileSync(root+'_tod_upgrades.gsc','utf8');
function body(src,name){
 const clean=src.replace(/\/\/[^\n]*/g,'');
 const a=clean.indexOf('{',clean.indexOf('function '+name+'('));assert(a>=0,name);
 let b=a+1,d=1;while(d){if(clean[b]==='{')d++;if(clean[b]==='}')d--;b++;}
 return clean.slice(a+1,b-1);
}
const env={isdefined:x=>x!==undefined,IS_TRUE:x=>x===true,IsSubStr:(s,x)=>s.includes(x),IsPlayer:p=>p.player,int:Math.trunc,
 staff_element:w=>w?.element,demigod_mult:()=>1,charge_mult:()=>1,tier:()=>1,
 victim_family:v=>v.family,on_family_mult:()=>1,off_family_mult:()=>1,family_answerable:()=>true,get_level:p=>p.card,pap_tier:(p)=>p.pap||0,has_dark:(p,k)=>!!(p.dark&&p.dark[k])};
for(const m of mage.matchAll(/#define\s+(TOD_MAGE_\w+)\s+([\d.]+)/g))env[m[1]]=Number(m[2]);
vm.createContext(env);
const mult=body(mage,'staff_mult').replace(/attacker (demigod_mult|charge_mult)\(\)/g,'$1(attacker)').replace(/tod_classes::|tod_upgrades::/g,'');
vm.runInContext(`function mult(attacker,victim,weapon){let el,m,t,fam,off;${mult}}`,env);
for(const [el,rate] of [['fire',.20],['ice',.15]])for(let lv=0;lv<=6;lv++) {
 const actual=env.mult({player:true,card:lv},{family:el},{element:el});
 const flat=el==='ice'?env.TOD_MAGE_ICE_NERF:1;
 assert(Math.abs(actual/env.TOD_MAGE_TIER1_MULT/flat-(1+rate*lv))<1e-9,`${el} level ${lv}`);
}
// Compare the live matchup paths against the previous balance, including
// every tier/card level, Archmage and representative PaP/direct/splash inputs.
vm.runInContext(`function on_family_mult(el){${body(mage,'on_family_mult')}}
function off_family_mult(el){${body(mage,'off_family_mult')}}`,env);
env.tier=p=>p.tier; env.demigod_mult=p=>p.arch;
const beast=env.TOD_MAGE_ICE_VS_BEAST, off=env.TOD_MAGE_ICE_OFF;
assert.equal(beast,2.85); assert.equal(off,0.8);   // 2026-09-09 playtest pass: 3.352 -> 2.85, ICE_OFF 1.00 -> 0.80
assert.equal(env.TOD_MAGE_VS_HORDE,1.75);
for(const el of ['lightning','fire','ice'])for(const family of ['lightning','fire','ice','panzer'])
for(const tier of [1,2,3])for(const card of [0,1,2,3,4,5,6])for(const arch of [1,2.2]) {
 const p={player:true,tier,card,arch},v={family},w={element:el};
 const after=env.mult(p,v,w);
 env.TOD_MAGE_ICE_VS_BEAST=beast/0.8;env.TOD_MAGE_ICE_OFF=off/0.8;   // the flat 20% cut is still exactly 20% at every cell
 const before=env.mult(p,v,w);
 env.TOD_MAGE_ICE_VS_BEAST=beast;env.TOD_MAGE_ICE_OFF=off;
 for(const raw of [200,1200])for(const pap of [1,1.5625,2.44140625])
  assert(Math.abs(after*raw*pap-before*raw*pap*(el==='ice'?.8:1))<1e-7,el+' damage ratio');
}
// The additional class-wide cut is exactly 20% at every tier and matchup,
// including both staff identities, all card levels and transformed/charged hits.
const tierKeys=['TOD_MAGE_TIER1_MULT','TOD_MAGE_TIER2_MULT','TOD_MAGE_TIER3_MULT'];
const currentTiers=tierKeys.map(k=>env[k]);
assert.deepEqual(currentTiers,[.6256,1.36,2.686]);   // = the v18.51 0.92/2/3.95 ladder x0.8 x0.85
env.charge_mult=p=>p.charge;
for(const el of ['lightning','fire','ice'])for(const q of [0,1])
for(const family of ['lightning','fire','ice','panzer'])for(const tier of [1,2,3])
for(const card of [0,1,2,3,4,5,6])for(const arch of [1,2.2,2.7])for(const charge of [1,2.5]) {
 const p={player:true,tier,card,arch,charge},v={family},w={name:`tod_staff_${el}_q${q}`,element:el};
 const after=env.mult(p,v,w);
 tierKeys.forEach((k,i)=>env[k]=[.92,2,3.95][i]);
 const before=env.mult(p,v,w);
 tierKeys.forEach((k,i)=>env[k]=currentTiers[i]);
 assert(Math.abs(after-before*.68)<1e-9,'all staff damage x0.8 x0.85 vs the v18.51 ladder');
 // Chain share comes from the already-scaled hit; it is not scaled twice.
 if(el==='lightning')assert(Math.abs(Math.trunc(after*1000*.5)-Math.trunc(before*1000*.5)*.68)<=1);
}
// Lightning nerf (2026-09-09): x0.90 unpacked, x0.80 packed, vs the same body
// with both defines at 1.0; fire and ice untouched by it.
{ const ln=env.TOD_MAGE_LIGHTNING_NERF, lp=env.TOD_MAGE_LIGHTNING_PAP_NERF; assert.equal(ln,.9); assert.equal(lp,.8);
  for(const el of ['lightning','fire','ice'])for(const family of ['lightning','panzer','fire'])for(const tier of [1,3])for(const pap of [0,1,2,3])for(const card of [0,6]) {
   const p={player:true,tier,card,arch:1,charge:1,pap},v={family},w={name:'tod_staff_'+el+'_q0',element:el};
   const after=env.mult(p,v,w); env.TOD_MAGE_LIGHTNING_NERF=1;env.TOD_MAGE_LIGHTNING_PAP_NERF=1; const before=env.mult(p,v,w);
   env.TOD_MAGE_LIGHTNING_NERF=ln;env.TOD_MAGE_LIGHTNING_PAP_NERF=lp;
   const want=el==='lightning'?(pap>=1?.8:.9):1; assert(Math.abs(after-before*want)<1e-9,'lightning nerf '+el+' pap'+pap+' t'+tier); } }
// Ice nerf (2026-09-09, retuned v18.77): x0.68 everywhere, x0.238 (0.68 x 0.35) on the armour family and the
// Panzer, vs the same body with both defines at 1.0; lightning/fire untouched.
{ const fn=env.TOD_MAGE_ICE_NERF, fa=env.TOD_MAGE_ICE_VS_ARMOUR_ROBOT; assert.equal(fn,.68); assert.equal(fa,.35); assert.equal(env.TOD_MAGE_FIRE_VS_ARMOUR,1.75);   // v18.77: 0.80 -> 0.68, 0.60 -> 0.35
  for(const el of ['lightning','fire','ice'])for(const family of ['lightning','ice','fire','panzer'])for(const tier of [1,2,3])for(const card of [0,3,6])for(const pap of [0,1]) {
   const p={player:true,tier,card,arch:1,charge:1,pap},v={family},w={name:'tod_staff_'+el+'_q0',element:el};
   const after=env.mult(p,v,w); env.TOD_MAGE_ICE_NERF=1;env.TOD_MAGE_ICE_VS_ARMOUR_ROBOT=1; const before=env.mult(p,v,w);
   env.TOD_MAGE_ICE_NERF=fn;env.TOD_MAGE_ICE_VS_ARMOUR_ROBOT=fa;
   const want=el!=='ice'?1:((family==='fire'||family==='panzer')?fn*fa:fn); assert(Math.abs(after-before*want)<1e-9,'ice nerf '+el+' vs '+family); } }
// 2026-09-09 playtest: fire on the beast family pays TOD_MAGE_FIRE_VS_BEAST at EVERY tier (never answerable-gated).
{ assert.equal(env.TOD_MAGE_FIRE_VS_BEAST,.35);   // v18.77: 0.50 -> 0.35
  const savedFA=env.family_answerable; env.family_answerable=()=>false;
  for(const tier of [1,2,3]){ const p={player:true,tier,card:0,arch:1,charge:1,pap:0};
    const beastHit=env.mult(p,{family:'ice'},{name:'tod_staff_fire_q0',element:'fire'});
    const hordeHit=env.mult(p,{family:'lightning'},{name:'tod_staff_fire_q0',element:'fire'});
    assert(Math.abs(beastHit/hordeHit-env.TOD_MAGE_FIRE_VS_BEAST)<1e-9,'fire vs beast at tier '+tier); }
  env.family_answerable=savedFA; }
// Dark FIRE BLAST / ICE SHATTER: +0.50 on the card multiplier, nothing else moves.
{ for(const [el,key,rate,add] of [['fire','mage_fire',.2,env.TOD_MAGE_FIRE_DARK_ADD],['ice','mage_ice',.15,env.TOD_MAGE_ICE_DARK_ADD]]){
    assert.equal(add,.5);
    for(const card of [0,6]){ const base={player:true,tier:3,card,arch:1,charge:1,pap:0};
      const plain=env.mult(base,{family:el},{name:'tod_staff_'+el+'_q0',element:el});
      const dark=env.mult({...base,dark:{[key]:true}},{family:el},{name:'tod_staff_'+el+'_q0',element:el});
      assert(Math.abs(dark/plain-(1+rate*card+add)/(1+rate*card))<1e-9,'dark '+el+' card '+card); } } }
assert(mage.includes('share = int( dmg * chain_fraction( attacker ) );'));
const chainBranch=upgrades.slice(upgrades.indexOf('if ( IS_TRUE( self.tod_mage_chain_hit ) )'));
assert(chainBranch.indexOf('return arc;')<chainBranch.indexOf('level.tod_mage_staff_mult'),'chain must exit before rescaling');
vm.runInContext(`function deferred(victim,weapon){${body(ui,'defer_staff_damage_number')}}`,env);
Object.assign(env,{self:{tod_staff_damage_number_final:true},calls:[],outputs:[],nativeResult:2000,
 calc:(...args)=>{env.calls.push(args);return env.nativeResult;},
 headshot_kind:()=> 'none',push:(attacker,damage,head,red)=>env.outputs.push({attacker,damage,head,red})});
const wrap=body(bosses,'tod_mechz_damage_wrap')
 .replace('self tod_mechz_damage_calc(', 'calc(')
 .replace(/tod_upgrade_ui::defer_staff_damage_number/g,'deferred')
 .replace(/tod_upgrades::headshot_kind/g,'headshot_kind')
 .replace('attacker tod_upgrade_ui::push_dmg_num(', 'push(attacker,');
vm.runInContext(`function hit(inflictor,attacker,damage,dFlags,mod,weapon,point,dir,hitLoc,offsetTime,boneIndex){let result,headshot;${wrap}}`,env);
const player={player:true};
for(const el of ['lightning','fire','ice'])for(const q of [0,1])for(const mod of ['MOD_PROJECTILE','MOD_PROJECTILE_SPLASH']) {
 const weapon={name:`tod_staff_${el}_q${q}`};
 for(const result of [undefined,0,400,2000,3999.9]) {
  env.nativeResult=result;env.outputs=[];env.calls=[];
  assert.equal(env.hit(null,player,4000,0,mod,weapon,null,null,'none',0,0),result,'do not change damage');
  assert.equal(env.calls.length,1,'stock calculation runs once');
  assert.equal(env.outputs.length,result>0?1:0,'only one final positive number');
  if(result>0)assert.equal(env.outputs[0].damage,Math.trunc(result),'4000 incoming must not masquerade as final');
 }
}
for(const [victim,weapon] of [[{}, {name:'tod_staff_lightning_q0'}],[{tod_staff_damage_number_final:true},{name:'ak74u'}],[{tod_staff_damage_number_final:true},undefined]]) {
 assert.equal(env.deferred(victim,weapon),false,'ordinary actors and guns keep original display lane');
}
assert(/if \( !tod_upgrade_ui::defer_staff_damage_number\( self, weapon \) \)\s+attacker tod_upgrade_ui::push_dmg_num\( final, headshot, b_sprint_armor \);/.test(upgrades),'early number suppressed for wrapped Panzer staff hits');
assert(bosses.includes('boss.actor_damage_func = &tod_mechz_damage_wrap;\n\tboss.tod_staff_damage_number_final = true;'),'marker and final handler installed together');
console.log('Mage damage passed: fire/ice Lv0-6 rates; 60 final Panzer result cases; exact one-time post-armor numbers; unchanged return values and other display lanes.');
