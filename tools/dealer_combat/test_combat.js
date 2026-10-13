'use strict';
// Executes the shipping footprint/lifecycle functions. Engine effects/threads are
// checked for ordering/ownership; native playback remains the user's playtest.
const fs=require('fs'), path=require('path'), assert=require('assert');
const {gscLoad,V}=require('../sky_ships/gsc_eval');
const repo=path.resolve(__dirname,'../..');
const ix=process.argv.indexOf('--root');
const root=ix<0?repo:path.resolve(process.argv[ix+1]);
const read=p=>fs.readFileSync(path.join(root,p),'utf8').replace(/\r\n/g,'\n');
const base='scripts/zm/zm_tod2_cybercity/';
const src=read(base+'_tod_dealer_finale.gsc');
const house=read(base+'_tod_house.gsc'), bosses=read(base+'_tod_bosses.gsc');
const defs=Object.fromEntries([...src.matchAll(/^#define\s+(TOD_DC_\w+)\s+([\d.]+)\s*$/gm)].map(m=>[m[1],+m[2]]));
let passed=0;
function ok(value,message){assert(value,message);passed++;}
function evaluate(text){return gscLoad([['dealer',text]],defs,{builtins:{IS_TRUE:x=>x===true||x===1,
 DistanceSquared:(a,b)=>a.reduce((s,x,i)=>s+(x-b[i])**2,0)}});}
const g=evaluate(src), call=(n,...args)=>g.call(n,args);
for(const [args,want] of [
 [[true,1,1,7,7,false,false],'ok'], [[false,1,1,7,7,false,false],'gone'],
 [[true,2,1,7,7,false,false],'phase'], [[true,1,1,8,7,false,false],'superseded'],
 [[true,1,1,7,7,true,false],'pause'], [[true,1,1,7,7,false,true],'hold'],
 [[true,1,1,7,7,undefined,undefined],'ok'], [[false,2,1,8,7,true,true],'gone']
]) ok(call('dc_verdict',...args)===want,'generation/lifetime verdict '+want);
const center=V(100,200,3);
for(const [p,want] of [[V(100,200,3),true],[V(200,200,3),true],[V(201,200,3),false],
 [V(170,270,3),true],[V(171,271,3),false],[V(100,200,93),true],[V(100,200,94),false]])
 ok(call('dc_in_shock',p,center)===want,'100u footprint and 90u height '+p);
const start=V(0,0,40), end=V(500,0,40);
for(const [p,want] of [[V(250,0,40),true],[V(250,24,40),true],[V(250,25,40),false],
 [V(-1,0,40),false],[V(501,0,40),false],[V(250,0,65),false]])
 ok(call('dc_in_shot',p,start,end)===want,'finite covered segment '+p);
ok(!call('dc_in_shot',start,start,start),'zero-length shot');
ok(!call('dc_in_shot',V(450,0,40),start,V(300,0,40)),'cover clips target beyond wall');
ok(call('dc_in_shot',V(250,0,40),start,end)&&!call('dc_in_shock',V(250,0,3),V(500,0,3)),
 'co-op player on ray outside warning cannot be damaged');
const fn=n=>{const m=src.match(new RegExp('^function '+n+'\\([^)]*\\)\\s*\\n\\{([\\s\\S]*?)\\n\\}','m'));assert(m,n);return m[1];};
const shock=fn('dc_shock'), burst=fn('dc_burst'), clean=fn('dc_cleanup'), brain=fn('brain');
ok(shock.indexOf('TOD_DC_SHOCK_TELL ) )')<shock.indexOf('TOD_DC_FX_SHOCK'),'shock waits for warning');
ok(shock.includes('foreach ( point in impacts )')&&shock.includes('if ( !isdefined( impact ) ) continue;'),
 'no impact carrier means no invisible damage');
ok(shock.includes('break; // Overlapping'),'overlapping marks damage once');
ok(burst.includes('dc_in_shock( p.origin, center ) && dc_in_shot('),'burst damage requires warned footprint');
ok(burst.includes('TOD_DC_BURST_TELL + TOD_DC_BURST_SHOTS * TOD_DC_SHOT_GAP + 0.2'),
 'warning remains through all rounds');
ok(burst.includes('if ( !isdefined( bullet ) ) break;'),'no tracer means no invisible hit');
ok(fn('dc_visible').includes('fraction" ] == 1'),'walls block even the final one percent');
ok(fn('dc_muzzle').includes('barrel[ "fraction" ] < 1')&&burst.includes('if ( !isdefined( muzzle ) ) break;'),
 'barrel cannot shoot from far side of cover');
ok(clean.indexOf('ctx.warned = [];')<clean.indexOf('if ( !isdefined( self ) ) return;'),
 'deleted actor still withdraws sounds exactly once');
ok(clean.includes('self.tod_dealer_attack_serial != ctx.serial')&&clean.includes('self dc_disabled()'),
 'stale cast cannot restore new weapon or clear stun');
ok(fn('dc_disabled').includes('IS_TRUE( self.tod_frozen )')&&fn('dc_disabled').includes('tod_stun_until'),
 'EMP, Bash and freeze cancel attack');
ok((brain.match(/self dc_disabled\(\)/g)||[]).length>=3,'pause and dialogue release preserve stun ownership');
ok(fn('mask_crack').trim().startsWith('self dc_cancel( "phase" );'),'phase withdraws old cast first');
ok(fn('death_watch').includes('self dc_cancel( "death" );'),'death withdraws cast');
ok(fn('combat').includes('TOD_DC_OPENING_GRACE')&&defs.TOD_DC_OPENING_GRACE>=6,'opening recovery grace');
ok(fn('dc_damage').includes('level.tod_house_shield')&&fn('dc_damage').includes('level.tod_upgrade_pause'),
 'drain shield and upgrade pause suppress damage');
ok(/tod_keeper_dmg \) && isdefined\( sMeansOfDeath \) && sMeansOfDeath == "MOD_MELEE"/.test(bosses),
 'swing multiplier applies only to melee; arena scaling remains');
ok(house.includes('TOD_HOUSE_DEATH_LINE_DELAY + tod_shop_vo::secs( "tod_house_vo_death" ) + 0.25'),
 'complete last word before win cards');
ok(src.includes('%tod_dealer_c_shock')&&src.includes('%tod_dealer_c_burst')&&
 fn('dc_begin').includes('undefined, 1.0, 0.1'),'actual gun clips use authored timing');
for(const name of ['warning','charge','shock','muzzle','tracer'])
 ok(src.includes('#precache( "fx", "tod/dealer_combat/fx_dc_'+name+'" );'),'FX precached '+name);
ok(defs.TOD_DC_SHOT_GAP===.25&&defs.TOD_DC_SHOT_TRAVEL===.1,'cadence is on native .05s polling grid');
// Negative controls execute altered shipping functions; the expected results must change.
let caught=0;
for(const [text,n,args,want] of [
 [src.replace('if ( serial != expected_serial ) return "superseded";',''), 'dc_verdict',[true,1,1,8,7,false,false],'superseded'],
 [src.replace('if ( t < 0 || t > 1 ) return false;',''),'dc_in_shot',[V(501,0,40),start,end],false],
 [src.replace('Abs( d[ 2 ] ) <= TOD_DC_HEIGHT','true'),'dc_in_shock',[V(100,200,94),center],false]
]) { if(evaluate(text).call(n,args)!==want)caught++; }
ok(caught===3,'three planted lifetime/cover/floor regressions caught');
if(root===repo){
 const zone=read('zone_source/zm_tod2_cybercity.zone');
 const am=read('animtables/tod_dealer.ai_am');
 const gdt=read('source_data/tod_dealer_combat.gdt');
 for(const kind of ['shock','burst']){
  ok(am.includes('anim_dealer_weapon_'+kind+',tod_dealer_c_'+kind+','),'generic tree maps '+kind);
  ok(zone.includes('xanim,tod_dealer_c_'+kind)&&gdt.includes('"tod_dealer_c_'+kind+'" ( "xanim.gdf" )'),'native clip registered '+kind);
 }
 const szc=JSON.parse(read('sound/zoneconfig/zm_tod2_cybercity.szc'));
 ok(szc.Sources.some(s=>s.Filename==='tod_dealer_combat.csv'),'weapon sound table loaded');
 for(const name of ['warning','charge','shock','muzzle','tracer'])
  ok(zone.includes('fx,tod/dealer_combat/fx_dc_'+name),'FX zoned '+name);
}
console.log('DEALER COMBAT PASS: '+passed+' checks; actual footprint/lifetime code, 3 negative controls. Native fight unplayed.');
