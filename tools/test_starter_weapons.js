// Guard the class-weapon balance (EVEN TIERS, 2026-09-25), native rates and full upgrade ladders.
// TOD II (2026-09-20, docs/153): the skirmisher T1 is the Hellbound Saug (cc_saug,
// sound stem t8_saug9mm); it inherits the MSMC's reference DPS (docs/139).
const fs=require('fs'),assert=require('assert/strict');
const source=fs.readFileSync('source_data/tod_weapon_twins.gdt','utf8');
const blocks=new Map([...source.matchAll(/"([^"\n]+)" \( "[a-z]+weapon.gdf" \)\s*\{([\s\S]*?)\n\t\}/g)].map(m=>[m[1],Object.fromEntries([...m[2].matchAll(/"([^"\n]+)" "([^"\n]*)"/g)].map(f=>[f[1],f[2]]))]));
// EVEN TIERS (2026-09-25, gen_tod_twins.js TIER_SUSTAINED): every Skirmisher / Archer /
// Breacher primary holds MAP 1's gun-class mean SUSTAINED DPS for its tier (a full
// magazine + a reload from empty; a Charge Shot bow's minimum draw counts in its
// interval), base and PaP, recomputed here from the EMITTED blocks.
// THE AUTOMATIC BOW (2026-10-05, docs/218): a bow that releases itself at full draw (chargeShotFireWhenQueueReachesMax 1)
// is HELD, so its sustained fire is the full draw (fireTime + chargeShotMaxTime) at x3 (_tod_archer_bow TOD_AB_MAX_MULT,
// gen_tod_twins AUTO_DRAW_FULL_MULT); a manual-release bow still counts its minimum draw at x1.
const AUTO_FULL=3;
const cyc=(f,tapRule=false)=>{const clip=+f.clipSize;let iv=+f.fireTime+(f.boltAction==='1'?+f.rechamberTime:0),full=1;
 if((+f.chargeShotMaxLevel||0)>0){if(!tapRule&&f.chargeShotFireWhenQueueReachesMax==='1'){iv+=+f.chargeShotMaxTime;full=AUTO_FULL;}else iv+=(+f.chargeShotMinTime||0);}
 const rl=f.segmentedReload==='1'?(+f.reloadStartTime||0)+Math.ceil((clip-(+f.reloadStartAdd||0))/(+f.reloadAmmoAdd||1))*+f.reloadTime+(+f.reloadEndTime||0):(+f.reloadEmptyTime||+f.reloadTime);
 return +f.damage*full*(+f.shotCount||1)*clip/(clip*iv+rl);};
const TARGET={1:[1235,2228],2:[2193,3858],3:[3574,6295]};
for(const [b,u,tier] of [
 ['cc_bow_d0s0_zm','cc_bow_up_d0s0_zm',1],['cc_crossbow_d0s0','cc_crossbow_up_d0s0',2],['cc_fire_bow_d0s0_zm','cc_fire_bow_up_d0s0_zm',3],
 ['cc_mozambique_e0','cc_mozambique_up_e0',1],['cc_rem870_e0','cc_rem870_up_e0',2],['cc_peacekeeper_e0','cc_peacekeeper_up_e0',3]]){
 const B=blocks.get(b),U=blocks.get(u);assert(B&&U,b+' / '+u+' emitted');
 assert(Math.abs(cyc(B)/TARGET[tier][0]-1)<.01,b+' sustained DPS '+cyc(B).toFixed(0)+' vs tier '+tier+' '+TARGET[tier][0]);
 assert(Math.abs(cyc(U)/TARGET[tier][1]-1)<.01,u+' sustained DPS '+cyc(U).toFixed(0)+' vs tier '+tier+' '+TARGET[tier][1]);
 // NEGATIVE CONTROL (2026-10-05): the old tap rule on an auto-release bow must NOT read as even - it would mean the
 // pin forgot the held full draw and every held arrow pays x3 on top of a tap-pinned damage.
 if(B.chargeShotFireWhenQueueReachesMax==='1')assert(Math.abs(cyc(B,true)/TARGET[tier][0]-1)>.2,b+' the tap rule must not balance an automatic bow');
}
// THE NECROMANCER (2026-09-26) replaced the Skirmisher: its primary is the Skull of
// Nan Sapwe as a CLASS GUN (all damage in _tod_necro_skull.gsc), one "_b" form + PaP.
for(const name of ['tod_necro_skull_b','tod_necro_skull_up_b']){
 const f=blocks.get(name);assert(f,name+' emitted');
 assert.equal(f.inventoryType,'primary',name+' is a primary, not a hero gadget');
 assert.equal(f.gadget_type,'none');assert.equal(f.altWeapon,'');
 assert.notEqual(f.weaponClass,'pistol',name+' must never be the last-stand pistol');
 assert.equal(+f.clipSize,100);assert.equal(+f.maxAmmo,0);assert.equal(f.clipOnly,'1');
 assert.equal(f.gunModel,'wpn_t7_zmb_dlc2_keeper_head_view');
}
// Breacher models, reserves, optics and pump timing are unchanged by the rebalance - except the Mozambique's
// reserve, 20 -> 30 magazines on 2026-10-04 (the first real-run review: no crown crate, card-earned C4/Cluster).
for(const [b,u,model,modelUp,mags] of [
 ['cc_mozambique_e0','cc_mozambique_up_e0','tod_bra_moz_view','tod_bra_moz_pap_view',30],
 ['cc_rem870_e0','cc_rem870_up_e0','vm_t6_remington870mcs','vm_t6_remington870mcs',7],
 ['cc_peacekeeper_e0','cc_peacekeeper_up_e0','tod_bra_pk_view','hb_am_peacekeeper_view',6]]){
 const B=blocks.get(b),U=blocks.get(u);
 assert.equal(B.gunModel,model);assert.equal(U.gunModel,modelUp);
 assert.equal(+B.maxAmmo,mags);assert.equal(+U.maxAmmo,mags);
 assert(!/reflex|elo|sight|optic|dot|scope/i.test(U.attachViewModel1||''),u+' packed forms carry no optic');   // glass_ammo* is the Apex ammo window, not a sight
 if(B.boltAction==='1')assert(Math.abs(+U.rechamberTime-+B.rechamberTime*.8)<.0001,u+' PaP pumps 25% faster');
}
// FALLOFF NEVER RISES WITH RANGE (2026-09-25, the "backwards shotgun falloff"): on every
// generated weapon each damage step is <= the one before it.
let curves=0;
for(const [name,f] of blocks){
 const steps=['damage','damage2','damage3','damage4','damage5'].map(k=>+f[k]||0).filter(v=>v>0);
 if(steps.length<2)continue;curves++;
 for(let i=1;i<steps.length;i++)assert(steps[i]<=steps[i-1],name+' damage rises with range: '+steps.join(' > '));
}
assert(curves>=13,'falloff curves found: '+curves+' (13 when written: the shotgun sidearms + the 870, base and PaP)');
assert.equal(blocks.get('cc_rem870_up_e0').adsUpAnim,'am_t6_remington870mcs_ads_up');
// 2026-09-26 (user, map one's Peacekeeper): both forms trace map one's blue plasma and hit with the energy
// table; the PaP fires the plain Apex aliases map one's PaP fired (not the mythic hb_am_peacekeeper_fire_*).
for(const n of ['cc_peacekeeper_e0','cc_peacekeeper_up_e0']){const b=blocks.get(n);
 assert.equal(b.tracerType,'mtl_s1_blue_plasma_tracer',n+' tracerType');assert.equal(b.enemyTracerType,'mtl_s1_blue_plasma_tracer',n+' enemyTracerType');
 assert.equal(b.normalImpactsFxTable,'bullet_small_energy_enter',n+' normalImpactsFxTable');}
// 2026-09-26 (user: Peacekeeper "range unlimited ... the damage still has fall off ... minimum ... 25%"): gen_tod_twins
// tune.reach - every form's pellets trace to 20000 (a spread gun's reach IS minDamageRange), falloff walks down over the
// gun's own 550 -> 1100 span in four even steps to 25%, and holds 25% beyond.
for(const [n,f] of blocks){if(!/^cc_peacekeeper(_up)?_e[0-3]$/.test(n))continue;const d=+f.damage,fl=Math.max(1,Math.round(d*.25));
 assert.equal(+f.minDamageRange,20000,n+' minDamageRange (unlimited reach)');assert.equal(+f.minDamage,fl,n+' minDamage = 25%');
 assert.equal(+f.maxDamageRange,550,n+' maxDamageRange');
 for(let i=1;i<=4;i++){assert.equal(+f['damage'+(i+1)],Math.max(1,Math.round(d*(1-.75*i/4))),n+' damage'+(i+1));
  assert(Math.abs(+f['damageRange'+(i+1)]-(550+550*i/4))<.01,n+' damageRange'+(i+1)+' '+f['damageRange'+(i+1)]);}}
{const b=blocks.get('cc_peacekeeper_up_e0');for(const [k,v] of [['fireSound','wpn_apex_peacekeeper_fire_npc'],['lastShotSound','wpn_apex_peacekeeper_fire_npc'],
 ['fireSoundPlayer','wpn_apex_peacekeeper_fire_plr'],['lastShotSoundPlayer','wpn_apex_peacekeeper_fire_plr']])assert.equal(b[k],v,'cc_peacekeeper_up_e0 '+k);}
for(const gone of ['cc_saug_f0h0','cc_saug_up_f0h0','cc_m1927_h0','cc_r99_h0','t9_mac10_f0h0','t9_stoner63_p0','t6_msmc_f0h0','t9_mp5_h0','t6_mp7_h0','t6_mk48_p0','t5_hk21_b','t6_death_machine_p0'])assert(!blocks.has(gone),gone+' still emitted');
const rows=fs.readFileSync('sound/aliases/tod_ports.csv','utf8').split(/\r?\n/).map(r=>r.split(','));
for(const [stem,count] of [['wpn_apex_mozambique_',10],['wpn_apex_peacekeeper_',12],['hb_am_peacekeeper_',2],['hb_am_donor_wpn_apex_peacekeeper_',2],['wpn_t6_rem870mcs_',12]]){
 const aliases=rows.filter(r=>r[0].startsWith(stem));
 assert.equal(aliases.length,count,stem);
 for(const row of aliases)for(const col of [3,4,5])if(row[col])assert(fs.existsSync('sound_assets/'+row[col].replace(/\\/g,'/')),row[col]);
}
assert(!rows.some(r=>/^(wpn_t8_saug9mm_|wpn_t8_m1927_|hb_am_car_fire_|wpn_t6_mk48_|wpn_t5_hk21_|wpn_t6_death_machine_)/.test(r[0])),'retired heavy alias rows still present');
console.log('Starter swaps: EVEN TIERS - all 6 Archer/Breacher primaries within 1% of the map 1 gun-class mean sustained DPS (1235/2193/3574, PaP 2228/3858/6295; an automatic bow counts its HELD full draw at x3); Necromancer skull = primary class gun; Breacher models/reserves/no packed optics; '+curves+' falloff curves never rise with range; sound aliases resolve to vendored wavs PASS.');
