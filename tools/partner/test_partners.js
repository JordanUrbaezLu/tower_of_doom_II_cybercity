// Executes shipping GSC state transitions with stubbed native input/entity calls.
// Does not claim to emulate the native AI/nav/renderer; those need a user match.
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const root = require('path').resolve(__dirname, '../..');
const src = fs.readFileSync(root+'/scripts/zm/zm_tod2_cybercity/_tod_partners.gsc','utf8');
function body(name) {
  const clean=src.replace(/\/\/[^\n]*/g,'');
  const start=clean.indexOf('function '+name+'(');
  assert(start>=0,name);
  const a=clean.indexOf('{',start);let b=a+1,depth=1;
  while(depth){if(clean[b]==='{')depth++;if(clean[b]==='}')depth--;b++;}
  return clean.slice(a+1,b-1);
}
function translate(code) {
  return code.replace(/(?:self|level) endon\([^;]+;/g,'')
    .replace(/\bself laststand::player_is_in_laststand\(\)/g,'self.down')
    .replace(/\bp laststand::player_is_in_laststand\(\)/g,'p.down')
    .replace(/\b(self|p|a|e|s\.actor|s\.visual|s\.target) (GetEntityNumber|IPrintLn|PlaySound|PlayLocalSound|PlayLoopSound|StopLoopSound|IsTouching|UseButtonPressed|Delete|ASMSetAnimationRate|ClearPath|SetGoal|ForceTeleport)\(/g,'$1.$2(')
    .replace(/\b\w+ thread (\w+)\(/g,'$1(')   // PK22: `level thread destroyed_fx(` / `e thread delete_after(` -> a plain call on a stub
    .replace(/tod_shop::/g,'tod_shop.')
    .replace(/foreach\s*\(\s*(\w+)\s+in\s+([^)]+)\)/g,'for (const $1 of $2)')
    .replace(/\.size\b/g,'.length')
    .replace(/wait ([^;]+);/g,'yield $1;');
}
function context() {
  const level={tod_class_select_done:true,tod_partner_records:[],tod_partner_defs:
    ['CIVIL PROTECTOR','TALON','R.A.P.S.','CERBERUS'].map((title,i)=>({title,hp:[1800,1000,1400,2200][i]}))};
  const env={level,now:10000,notes:[],log:()=>{},isdefined:x=>x!==undefined&&x!==null,
    isalive:x=>!!x&&x.alive!==false,isplayer:x=>!!x&&x.player===true,IS_TRUE:x=>x===true,
    int:Math.trunc,SpawnStruct:()=>({}),Spawn:(kind,origin)=>({origin,PlaySound(a){env.sounds.push(a)}}),GetTime:()=>env.now,
    // PK22: the destruction's lanes + the loop defines (the effects / hosts are stubs; the sound names are real)
    sounds:[],bursts:[],fx_burst:(fx)=>{env.bursts.push(fx)},delete_after:()=>{},IsPlayer:x=>!!x&&x.player===true,
    TOD_PTN_BLAST_FX:'dlc1/castle/fx_elec_teleport_flash_lg',TOD_PTN_HIT_FX:'electric/fx_elec_spark_loop_sm',TOD_PTN_DEATH_SECS:1.2,TOD_PTN_LOOP_FADE:0.25,
    // THE BLACK MARKET SPIN (docs/188): the shop's item API, stubbed per test; empty = no items.
    TOD_PTN_REBUILD_MS:45000,TOD_ITEM_PLATING:1,TOD_ITEM_OVERCLOCK:2,TOD_ITEM_HOLLOW:3,TOD_ITEM_SIGHT:4,TOD_ITEM_NANO:5,TOD_ITEM_ARC:6,TOD_ITEM_SALVAGE:7,TOD_ITEM_REBOOT:8,TOD_ITEM_LUCKY:9,items:{},
    tod_shop:{item_mult:(p,c,i)=>(env.items[i]?env.items[i].mult:1),item_rarity:(p,c,i)=>(env.items[i]?env.items[i].rar:-1),
      item_value:(i,r)=>(env.items[i]?env.items[i].value:0)},push_items:()=>{}};
  vm.createContext(env);
  for(const [name,args,locals] of [
    ['ensure_state','p','s,i'],['max_hp','s,id',''],['rebuild_ms','s,id','r'],['start_rebuild','s,id,now',''],['nano_tick','s,a','r,heal'],['retire','s,reason',''],['usable','p',''],
    ['incoming_damage','inflictor,attacker,damage','s'],
    ['freeze_reason','p',''],['freeze','s,a,why','p'],['thaw','s,a,now','p'],
    ['closest_target','origin,players','nearest,dist,d,elite,kind'],
    ['owner_ground','s,p,now','goal,how'],
    ['tick','s','p,now,id,a,why,paused,nav,goal,far,stuck,org,gd,target_num'],
    ['gift_companion','p,id','s,previous'],
    ['loop_set','s,on',''],['destroyed_fx','s,id,org,generation','e,p']]) {
    vm.runInContext(`function ${name}(${args}){${locals?'let '+locals+';':''}${translate(body(name))}}`,env);
  }
  vm.runInContext(`function* testAction(bench){let s,id,d,previous;${translate(body('test_bench_action'))}}`,env);
  vm.runInContext(`function* death(s,id,generation){${translate(body('partner_death')).replace('self waittill( "death" );','yield "death";')}}`,env);
  const player=id=>({player:true,alive:true,down:false,held:true,touching:true,origin:[0,0,0],
    GetEntityNumber:()=>id,UseButtonPressed(){return this.held},IsTouching(){return this.touching},
    IPrintLn:s=>env.notes.push(s),PlaySound:()=>{},PlayLocalSound:a=>env.sounds.push('local'+id+':'+a)});
  env.self=player(0);env.p2=player(1);env.ensure_state(env.self);env.ensure_state(env.p2);
  env.step=g=>{const r=g.next();if(!r.done)env.now+=r.value*1000;return r};
  env.finish=g=>{env.self.held=false;for(let i=0;i<100;i++)if(env.step(g).done)return;throw Error('action leaked')};
  return env;
}
let checks=0;function ok(v,m){assert.ok(v,m);checks++}
// THE DEALER'S GIFT (docs/209, user 2026-10-04: "he should gift you a random AI companion on first use that doesnt
// use up your luck"): _tod_shop's gift reel hands the companion over through level.tod_partner_gift_fn ->
// gift_companion, executed here. The docs/159 collect-two-parts / build / equip flow is retired (checked below).
for(let id=0;id<4;id++){
  const e=context(),s=e.self.tod_ptn;let pushed=0;e.push_items=()=>{pushed++};
  ok(s!==e.p2.tod_ptn && s.built!==e.p2.tod_ptn.built,'coop ownership');
  ok(s.chosen===-1&&!s.built.some(Boolean),'a fresh player owns no companion');
  ok(e.gift_companion(e.self,id)===true,'the gift takes ('+id+')');
  ok(s.chosen===id&&s.built[id]===true&&s.ready[id]===0,'the gift is held and owned at once (no build, no equip step)');
  ok(s.hp[id]===e.level.tod_partner_defs[id].hp,'it arrives at full health');
  ok(pushed===1&&s.gifts===1,'the chips / companion row are told at once');
  ok(e.p2.tod_ptn.chosen===-1&&!e.p2.tod_ptn.built[id],'the gift is personal: the teammate still has none');
}
{
  const e=context(),s=e.self.tod_ptn;let deleted=0;
  for(const bad of [-1,4,undefined,null])ok(e.gift_companion(e.self,bad)===false&&s.chosen===-1,'an id outside the four is refused: '+bad);
  ok(e.gift_companion({player:false},1)===false,'only a player can be given one');
  // a tester's bench pick still out when a gift lands: it leaves first (never two), its health is kept
  s.chosen=3;s.actor={alive:true,health:777,Delete(){deleted++}};
  ok(e.gift_companion(e.self,1)===true&&deleted===1&&!s.actor&&s.hp[3]===777&&s.chosen===1,'a live companion is retired (health kept) before the gift takes its place');
  ok(s.built[1]&&s.gifts===1,'owned');
}
{
  // the docs/159 flow is RETIRED WHOLE: no parts, no workshop prompts, no part models precached
  for(const gone of ['function part_hint(','function bench_hint(','function pickup_loop(','function bench_action(','function reconcile_pickups(','tod_partner_parts','PARTNER PART','Bring 2 parts','_part1" )','_part2" )','s.parts'])
    ok(!src.includes(gone),'retired: '+gone);
  const wt=body('workshop_tables');
  ok(wt.includes('tod_breather_data::partner_bench_org( id )')&&wt.includes('"p8_zm_crafting_table"'),'the four workshop crafting tables still stand on their generated anchors (the map clips round them)');
  ok(!/use_trigger|SetHintString|SetScale/.test(wt),'the workshop tables are set dressing: no prompt, no trigger, no scale model');
  ok(src.includes('level.tod_partner_gift_fn = &gift_companion;'),'the shop reaches the gift through one pointer');
  ok(/bench_loop\(\)[^]*?p thread test_bench_action\( self \);/.test(src)&&!/bench_loop\(\)[^]*?bench_action\( self \)[^]*?bench_action\( self \)/.test(src),'the bench loop serves the crown TEST benches only');
}
{
  const e=context(),s=e.self.tod_ptn;let deleted=0;s.chosen=1;
  s.actor={alive:true,health:321,Delete(){deleted++}};s.visual={Delete(){deleted++}};
  e.retire(s,'switch');ok(s.hp[1]===321&&deleted===2&&!s.actor&&!s.visual,'switch saves integrity and deletes both entities');
  e.retire(s,'again');ok(deleted===2,'cleanup is idempotent');
  s.actor={alive:false,Delete(){deleted++}};e.retire(s,'switch_on_death');
  ok(s.hp[1]===0&&s.ready[1]===e.now+45000,'death cannot be bypassed by switching');
  const enemy={alive:true};
  ok(e.incoming_damage(null,e.self,100)===0,'no friendly fire');
  ok(e.incoming_damage(null,{tod_is_partner:true},100)===0,'no ally damage');
  ok(e.incoming_damage(null,enemy,500)===180,'bounded enemy damage');
  e.level.tod_upgrade_pause=true;ok(e.incoming_damage(null,enemy,100)===0,'pause immunity');
}
{
  // Native cleanup may remove the actor before the manager's next 100 ms poll.
  // Drive the actual death watcher and poll through that ordering.
  const e=context(),s=e.self.tod_ptn;let removed=0,deployed=0,stopped=0;
  s.chosen=1;s.generation=2;s.visual={origin:[0,0,60],Delete(){removed++},StopLoopSound(){stopped++}};s.loop_on=true;
  const old=e.death(s,1,1);old.next();old.next();
  ok(s.hp[1]===1000&&s.ready[1]===0,'stale death notification cannot reset a replacement');
  ok(e.bursts.length===0&&e.sounds.length===0,'PK22: a stale death plays no destruction');
  const death=e.death(s,1,2);death.next();death.next();
  ok(s.hp[1]===0&&s.ready[1]===e.now+45000,'death callback preserves cooldown after native actor deletion');
  // PK22 (2026-10-05): THE DESTRUCTION - the blast flash + the sparks on hosts, the crunch from a host at the spot,
  // the owner's 2D cue, and the drone's hover loop cut the moment it dies
  ok(e.bursts.includes('dlc1/castle/fx_elec_teleport_flash_lg')&&e.bursts.includes('electric/fx_elec_spark_loop_sm'),'PK22: a destroyed companion bursts (flash + sparks)');
  ok(e.sounds.includes('tod_ptn_destroyed')&&e.sounds.includes('local0:tod_ptn_destroyed_plr'),'PK22: the crunch at the spot + the owner hears it');
  ok(stopped===1&&s.loop_on===false,'PK22: the dead drone stops its loop at once');
  e.deploy=()=>{deployed++};e.tick(s);
  ok(removed===1&&!s.visual&&!deployed,'orphan visual removed immediately during cooldown');
  e.now+=44900;e.tick(s);ok(!deployed&&removed===1,'dead partner stays absent before cooldown');
  e.now+=100;e.tick(s);ok(deployed===1&&s.hp[1]===1000,'cooldown expiry restores full integrity before deployment');
}
{
  // Crown test benches: no parts/build, swap keeps the old partner's integrity,
  // a dead partner's rebuild wait is skipped, same bench dismisses.
  const e=context(),s=e.self.tod_ptn;let deleted=0;
  const run=id=>{e.self.held=true;s.busy=true;const g=e.testAction({tod_type:id});e.step(g);e.finish(g);};
  run(0);ok(s.chosen===0&&!s.built[0]&&!s.busy,'test bench equips with no gift and no rebuild wait (a test pick is never OWNED)');
  s.actor={alive:true,health:900,Delete(){deleted++}};
  run(3);ok(s.chosen===3&&s.hp[0]===900&&deleted===1&&s.hp[3]===2200,'test swap retires the old partner at full health for the new');
  s.actor={alive:false,Delete(){deleted++}};
  const t0=e.now;run(1);ok(s.chosen===1&&s.ready[1]===0&&s.ready[3]===t0+45000,'test bench skips only the new partner rebuild wait');
  s.actor={alive:true,health:500,Delete(){deleted++}};
  run(1);ok(s.chosen===-1&&!s.actor&&s.hp[1]===1000&&s.ready[1]===0,'same test bench dismisses and refills');
  // Deleting the actor on a swap may raise its death notify: the watcher must be stale by then.
  s.chosen=2;s.hp[2]=777;s.generation=5;s.actor={alive:true,health:777,Delete(){deleted++}};
  const w=e.death(s,2,5);w.next();e.retire(s,'switch');w.next();
  ok(s.hp[2]===777&&s.ready[2]===0,'a retired partner is never booked as destroyed');
  ok(!e.sounds.includes('tod_ptn_destroyed'),'PK22: a retired (switched / gifted) partner never plays the destruction');
}
{
  // Playtest 2026-09-28: a Hide()n actor is not networked - it stood still and its
  // client FX never drew. The body must be hidden by HidePart on j_mainroot instead.
  const dep=body('deploy');
  ok(!/\ba Hide\(\)/.test(dep),'deploy never Hide()s the partner actor');
  ok(dep.includes('a HidePart( "j_mainroot", "", true )'),'drone body hidden by HidePart(j_mainroot)');
  ok(dep.includes('s.visual NotSolid()'),'visual model is not solid');
  // Every shot / blast effect is precached AND zoned (a server one-shot draws nothing: all must loop).
  const zone=fs.readFileSync(root+'/zone_source/zm_tod2_cybercity.zone','utf8');
  for(const m of src.matchAll(/#define TOD_PTN_\w+_FX\s+"([^"]+)"/g)){
    ok(src.includes(`#precache( "fx", "${m[1]}" )`),'precached '+m[1]);
    ok(new RegExp('^fx,'+m[1].replace(/\//g,'\\/')+'\\s*$','m').test(zone),'zoned '+m[1]);
  }
  ok(body('attack').includes('tracer( from,'),'every gun shot draws a tracer');
  // THE ARRIVAL (docs/209): every deploy materialises with the teleporter's own arrival, on the host-based lanes
  ok(/a = SpawnActor\([^]*?arrive_fx\( org \);/.test(dep),'deploy plays the arrival at the spawn point, after the actor exists');
  const af=body('arrive_fx');
  ok(af.includes('tod_teleport::fx_burst( "tod_tp_kino"')&&af.includes('tod_teleport::discharge( org );'),'the arrival = the kino beam + the teleporter discharge (flash, release field, derez, warp)');
  ok(/#using scripts\\zm\\zm_tod2_cybercity\\_tod_teleport;/.test(src)&&src.indexOf('_tod_teleport;')<src.indexOf('#insert'),'_tod_teleport is #used before the first #insert');
  // NO STUB EFFECTS: a gfx_debug_missing_fx stub zones, links and draws NOTHING (the R.A.P.S. blast was one until
  // 2026-10-04). Checked against the private tools root when it is on this machine; the old stub is the control.
  const MT='C:/BO3Tools/TOD2Cybercity/share/raw/fx/';
  if(fs.existsSync(MT)){
    const stub=f=>{const q=MT+f+'.efx';return fs.existsSync(q)&&fs.readFileSync(q,'utf8').includes('gfx_debug_missing_fx');};
    ok(stub('electric/fx_elec_burst_lg_z270_os'),'control: the retired blast IS a stub, so the check below can fail');
    for(const m of src.matchAll(/#define TOD_PTN_\w+_FX\s+"([^"]+)"/g))ok(!stub(m[1]),'not a stub: '+m[1]);
  }
  // Playtest 2 (2026-09-28): HidePart left the body's weapon floating under every drone.
  ok(/a HidePart\( "j_mainroot", "", true \);[^]*?a ai::gun_remove\(\);/.test(dep),'drone bodies drop their weapon model');
  // R.A.P.S. must never park: it always gets a roam goal and always sprints.
  const tk=body('tick');
  ok(tk.includes('if ( id == 2 ) goal = raps_goal( s, goal, now );'),'R.A.P.S. goal comes from raps_goal');
  ok(tk.includes('if ( id == 2 || DistanceSquared( a.origin, goal ) > 105 * 105 ) a SetGoal( goal, true );'),'R.A.P.S. is never goaled at its own feet');
  ok(tk.includes('a.v_robot_land_position = goal;'),'sprint switch fed the partner goal');
  // The companion BT's only walk branch requires zodCompanionAbleToShoot: a partner
  // returning false there can never walk (playtest 2 MOVE_STALL with haspath=1).
  const arch=fs.readFileSync(root+'/scripts/zm/archetype_zod_companion.gsc','utf8');
  const able=arch.slice(arch.indexOf('function private zodcompanionabletoshoot'),arch.indexOf('function private zodcompanionshouldtacticalwalk'));
  ok(/IS_TRUE\( entity\.tod_is_partner \) \) return true;/.test(able)&&!/tod_is_partner \) \) return false/.test(able),'partners pass the BT walk gate (zodCompanionAbleToShoot)');
  ok(dep.includes('a.ignoreall = s.quiet;')&&body('freeze').includes('a.ignoreall = true;')&&body('thaw').includes('a.ignoreall = s.frz_ignoreall;'),'drones never get a native enemy; a freeze silences every companion and the thaw hands its own setting back');
  const rg=body('raps_goal');
  ok(rg.includes('"charge"')&&rg.includes('"orbit"'),'R.A.P.S. charges or orbits, no idle mode');
  for(const tag of ['MOVE_STALL','"MOVE ','"SHOT ','SHOT_SKIP','"DAMAGE ']) ok(src.includes(tag),'log '+tag);
  ok(/#define TOD_PARTNER_TEST_BENCHES [01]\s/.test(src)&&fs.readFileSync(root+'/tools/build_map.ps1','utf8').includes('TOD_PARTNER_TEST_BENCHES'),'publish gate knows the test switch');
}
{
  const anchors=fs.readFileSync(root+'/scripts/zm/zm_tod2_cybercity/_tod_breather_data.gsc','utf8');
  const gen=fs.readFileSync(root+'/tools/gen_tower_map.js','utf8');
  for(const fn of ['partner_bench_org','partner_bench_yaw']) {
    ok(src.includes('tod_breather_data::'+fn+'('),'runtime reads generated '+fn);
    ok(anchors.includes('function '+fn+'(')&&gen.includes(fn),'generator owns '+fn);
  }
  const benchBlock=anchors.match(/function partner_bench_org\([^]*?\n}/)[0];
  const orgs=[...benchBlock.matchAll(/case (\d): return \( ([^)]*) \)/g)].map(m=>m[2].split(',').map(Number));
  ok(orgs.length===4,'four generated workshop benches');
  for(let i=0;i<orgs.length;i++)for(let j=i+1;j<orgs.length;j++)
    ok(Math.hypot(...orgs[i].map((v,k)=>v-orgs[j][k]))>200,'bench trigger cylinders separate');
  ok(!src.includes('vault_spawn_org()'),'nothing is laid out beside the Vault spawn any more (the parts are retired)');
  ok(src.includes('borg + fwd * 57 + ( 0, 0, 36 )'),'a crown test bench trigger stands 57 units in front of its bench');
}
// THE BLACK MARKET SPIN items (docs/188), through the shipping helpers.
{
  const e=context(),s=e.self.tod_ptn;
  ok(e.max_hp(s,1)===1000&&e.rebuild_ms(s,1)===45000,'no items = the base health and the 45 s rebuild');
  e.items[1]={rar:3,mult:2.2,value:2.2};ok(e.max_hp(s,1)===2200,'LEGENDARY PLATING = x2.2 max health');
  e.items[8]={rar:3,mult:1,value:10000};e.start_rebuild(s,1,e.now);
  ok(s.hp[1]===0&&s.ready_len[1]===10000&&s.ready[1]===e.now+10000,'QUICK REBOOT shortens the rebuild and the HUD bar length');
  s.chosen=1;const a={health:100,maxhealth:1000};s.nano_acc=0;
  e.items[5]={rar:1,mult:1,value:0.02};for(let i=0;i<10;i++)e.nano_tick(s,a);
  ok(a.health===120,'NANO REPAIR heals 2 percent of max health per second at 10 Hz (got '+a.health+')');
  a.health=999;for(let i=0;i<50;i++)e.nano_tick(s,a);ok(a.health===1000,'NANO REPAIR never overheals');
  ok(src.includes('level.tod_partner_items_changed = &items_changed;'),'the shop reaches the partner through one pointer');
  ok(body('deal_damage').includes('TOD_ITEM_HOLLOW')&&body('attack').includes('TOD_ITEM_OVERCLOCK')&&body('attack').includes('arc_chain('),'damage / fire rate / arcs read the items');
  ok(body('kill_credit').includes('TOD_ITEM_SALVAGE')&&body('kill_credit').includes('TOD_ITEM_LUCKY'),'kills read SALVAGE and LUCKY CHARM');
  ok(src.includes('#precache( "eventstring", "tod_ptn_items" )'),'the chip event is precached beside its sender');
}
// PASS 2 (2026-09-29): QUICK REBOOT socketed mid-rebuild shortens the RUNNING timer
// (executed through the shipping items_changed); NANO REPAIR sits behind the pause gate.
{
  const e=context(),s=e.self.tod_ptn;
  e.fx_burst=()=>{};e.GetTime=()=>e.now;
  const code=translate(body('items_changed')).replace(/level thread (\w+)\(/g,'$1(');
  vm.runInContext(`function items_changed(p,comp,installed){let s,a,old,now,org,want,served,left;${code}}`,e);
  s.chosen=1;s.actor=undefined;
  s.ready_len[1]=45000;s.ready[1]=e.now+40000;              // 5 s served of 45
  e.items[8]={rar:3,mult:1,value:10000};
  e.items_changed(e.self,1,true);
  ok(s.ready[1]===e.now+5000&&s.ready_len[1]===10000,'LEGENDARY QUICK REBOOT mid-rebuild: 5 s served, 5 s left (got '+(s.ready[1]-e.now)+')');
  s.ready_len[1]=45000;s.ready[1]=e.now+20000;              // 25 s served of 45
  e.items_changed(e.self,1,true);
  ok(s.ready[1]===e.now,'already served longer than the new rebuild: ready now');
  s.ready_len[1]=10000;s.ready[1]=e.now+8000;delete e.items[8];
  e.items_changed(e.self,1,false);
  ok(s.ready[1]===e.now+8000,'a slower (or removed) reboot never lengthens a running rebuild');
  const t=body('tick');
  ok(t.indexOf('nano_tick( s, a );')>t.indexOf('if ( paused ) return;'),'NANO REPAIR heals only after the pause gate');
  // (the companion bar's spin / card-deal hide moved to the HUD veil with the status plate: section PK08 below)
}
// THE COMPANION STATUS PLATE (PK08, W2G 2026-10-05). The three stock-font hudelems status_hud drew are GONE:
// the server sends the plate ONE int event (tod_ptn_hud: companion + 1, state, value, len, flags) from the
// manager tick, re-sent unchanged every TOD_PTN_HUD_BEAT_MS, and TodCompanionPlate.lua draws it under the HUD
// veil (tod_upgrade.lua HudOnly). Executes the shipping push_hud / hud_percent / clear_hud through every state.
// NEGATIVE CONTROL: the pre-PK08 status_hud (a verbatim fixture below) must fail the no-hudelem contract.
{
  const OLD_STATUS_HUD = [
    'function status_hud( s )', '{', '    if ( s.chosen < 0 || !isalive( s.owner ) ) { clear_hud( s ); return; }',
    '    if ( !isdefined( s.hud_label ) )', '    {', '        s.hud_label = hud_element( s.owner, -138 );',
    '        s.hud_label.fontScale = 1.1;', '    }', '}', 'function hud_element( p, y )', '{',
    '    h = NewClientHudElem( p );', '    h.horzAlign = "right"; h.vertAlign = "bottom";', '    return h;', '}'].join('\n');
  const noHudelems = code => !/NewClientHudElem|function status_hud\(|function hud_element\(|\bhud_label\b/.test(code.replace(/\/\/[^\n]*/g, ''));
  ok(noHudelems(src), 'the companion status is no longer stock-font hudelems (NewClientHudElem / status_hud / hud_label gone)');
  ok(!noHudelems(OLD_STATUS_HUD), 'negative control: the pre-PK08 status_hud fails the no-hudelem contract');
  ok(src.includes('#precache( "eventstring", "tod_ptn_hud" );'), 'the plate event is precached beside its sender');
  ok(/tick\( s \);\s*push_hud\( s \);\s*push_state\( s \);/.test(src), 'the manager sends the plate every tick (change-gated + heartbeat)');
  ok(/#define TOD_PTN_HUD_FROZEN\s+1/.test(src) && /#define TOD_PTN_HUD_OUT\s+2/.test(src) && /#define TOD_PTN_HUD_BEAT_MS\s+3000/.test(src), 'the flags (LOCKSTEP TodCompanionPlate.lua CP.F_*) and the 3 s heartbeat');
  ok(!body('tick').includes('IPrintLn'), 'no stock-font "destroyed" print: the plate shows DESTROYED + the countdown');
  const e = context(), s = e.self.tod_ptn;
  const sent = []; e.self.LuiNotifyEvent = (...a) => sent.push(a.slice(1)); e.p2.LuiNotifyEvent = () => {};
  e.logs = []; e.log = m => e.logs.push(m);
  Object.assign(e, { TOD_PTN_UI_NONE: 0, TOD_PTN_UI_ACTIVE: 1, TOD_PTN_UI_REBUILD: 2, TOD_PTN_UI_DEPLOYING: 3,
    TOD_PTN_HUD_FROZEN: 1, TOD_PTN_HUD_OUT: 2, TOD_PTN_HUD_BEAT_MS: 3000 });
  const tr = code => translate(code).replace(/&"/g, '"')
    .replace(/\b(p|s\.owner) (LuiNotifyEvent|GetEntityNumber)\(/g, '$1.$2(');
  vm.runInContext(`function hud_percent(s,comp){let top,hp,value;${tr(body('hud_percent'))}}`, e);
  vm.runInContext(`function push_hud(s){let p,now,comp,state,value,whole,flags,sig,moment;${tr(body('push_hud'))}}`, e);
  vm.runInContext(`function clear_hud(s){${tr(body('clear_hud'))}}`, e);
  const J = JSON.stringify, lastSent = () => J(sent[sent.length - 1]);
  e.push_hud(s);
  ok(lastSent() === J([5, 0, 0, 0, 0, 0]), 'none held: companion 0, state 0 ' + lastSent());
  e.push_hud(s); ok(sent.length === 1, 'unchanged inside the heartbeat: no second event');
  e.now += 3000; e.push_hud(s); ok(sent.length === 2 && lastSent() === J([5, 0, 0, 0, 0, 0]), 'the 3 s heartbeat re-sends the same tuple');
  e.gift_companion(e.self, 1); s.actor = { alive: true, health: 1000 };
  e.push_hud(s); ok(lastSent() === J([5, 2, 1, 100, 0, 0]), 'the gift: TALON active at 100 ' + lastSent());
  s.hp[1] = 300; e.push_hud(s); ok(lastSent() === J([5, 2, 1, 30, 0, 0]), 'damaged: 30 percent');
  s.hp[1] = 1; e.push_hud(s); ok(lastSent() === J([5, 2, 1, 5, 0, 0]), 'a living companion never reads 0');
  e.self.tod_spin_locked = true; e.push_hud(s); ok(lastSent() === J([5, 2, 1, 5, 0, 1]), 'frozen with its owner (a spin): flag 1');
  e.self.tod_spin_locked = undefined; e.self.down = true; e.push_hud(s); ok(lastSent() === J([5, 2, 1, 5, 0, 0]), 'a downed owner releases it: not frozen, the plate still shows');
  e.self.down = false;
  s.actor = undefined; e.start_rebuild(s, 1, e.now); e.push_hud(s);
  ok(lastSent() === J([5, 2, 2, 45, 45, 0]), 'destroyed: 45 s left of a 45 s rebuild ' + lastSent());
  e.now += 1000; e.push_hud(s); ok(lastSent() === J([5, 2, 2, 44, 45, 0]), 'the countdown ticks once a second');
  s.ready_len[1] = 10000; s.ready[1] = e.now + 4500; e.push_hud(s);
  ok(lastSent() === J([5, 2, 2, 5, 10, 0]), 'QUICK REBOOT shortened it mid-rebuild: the bar\'s length follows ' + lastSent());
  e.now = s.ready[1]; e.push_hud(s); ok(lastSent() === J([5, 2, 3, 100, 0, 0]), 'rebuilt, on its way: DEPLOYING at the 100 it returns with ' + lastSent());
  e.self.alive = false; e.push_hud(s); ok(lastSent() === J([5, 2, 3, 100, 0, 2]), 'the owner is dead: flag 2 (the plate hides)');
  e.self.alive = true; s.hud_sig = undefined; const n1 = sent.length; e.push_hud(s);
  ok(sent.length === n1 + 1 && lastSent() === J([5, 2, 3, 100, 0, 0]), 'a respawn (player_spawned clears the signature) re-sends at once');
  ok(body('player_spawned').includes('hud_sig = undefined'), 'player_spawned clears the plate signature');
  const logs0 = e.logs.length; for (const hp of [900, 800, 700]) { s.actor = { alive: true }; s.hp[1] = hp; e.push_hud(s); }
  ok(e.logs.length === logs0 + 1, 'health steps send but log once (transitions only): ' + (e.logs.length - logs0));
  e.clear_hud(s); ok(lastSent() === J([5, 0, 0, 0, 0, 0]) && s.hud_sig === undefined, 'clear_hud (the end of the match) hides the plate');
  const n2 = sent.length; e.clear_hud({ owner: undefined }); e.push_hud({ owner: undefined, chosen: 0 });
  ok(sent.length === n2, 'a disconnected owner: no call, no throw');
}
// THE FREEZE (user 2026-09-29: "your AI partner companion should also freeze so we
// can't kill things while you are spinning or getting your cards"). The user's
// 15:32 run: in each 10 s Black Market spin the Cerberus shot ~50 times and
// killed 2-8 zombies while its owner could not play. Drives the shipping tick,
// freeze_reason, freeze, thaw, incoming_damage and closest_target.
{
  const mk=()=>{
    const e=context(),cnt={attacks:0,heals:0,deploys:0,teleports:0};
    e.logs=[];e.log=m=>e.logs.push(m);
    Object.assign(e,{GetClosestPointOnNavMesh:()=>undefined,abs:Math.abs,
      DistanceSquared:(u,v)=>(u[0]-v[0])**2+(u[1]-v[1])**2+(u[2]-v[2])**2,
      Distance:(u,v)=>Math.sqrt(e.DistanceSquared(u,v)),
      target_for:()=>e.zombie,raps_goal:(s,g)=>g,landing_point:()=>[5,5,0],
      visual_tick:()=>{},move_watch:()=>{},raps_touch:()=>{},path_start_watch:()=>{},attack:()=>{cnt.attacks++},deploy:()=>{cnt.deploys++},
      ArrayGetClosest:(o,arr)=>arr.reduce((b,x)=>(!b||e.DistanceSquared(o,x.origin)<e.DistanceSquared(o,b.origin))?x:b,undefined)});
    e.nano_tick=()=>{cnt.heals++};
    e.zombie={alive:true,origin:[400,0,0],GetEntityNumber:()=>77};
    return {e,cnt};
  };
  // What deploy leaves on the record and the actor (quiet = the drones' ignoreall).
  const actor=(e,s,id,cnt)=>{
    const quiet=(id!==0);
    const a={alive:true,health:900,maxhealth:1000,origin:[300,0,0],ignoreall:quiet,ignoreme:false,rate:1,goals:[],cleared:0,
      tod_partner_state:s,ASMSetAnimationRate(r){this.rate=r},ClearPath(){this.cleared++},SetGoal(g){this.goals.push(g)},
      ForceTeleport(){cnt.teleports++},GetEntityNumber:()=>48};
    s.chosen=id;s.actor=a;s.paused=false;s.quiet=quiet;s.rate=(id===2?1.35:1.0);if(id===2)a.rate=1.35;
    s.shots=0;s.kills=0;s.next_shot=0;s.next_goal=0;s.next_log=Infinity;s.goal=[0,0,0];
    s.last_origin=a.origin;s.stuck_since=e.now;s.move_ref=a.origin;s.move_ref_ms=e.now;
    return a;
  };
  const hit=(e,a,dmg)=>{const me=e.self;e.self=a;const r=e.incoming_damage(null,e.zombie,dmg);e.self=me;return r;};
  // 1. SOLO SPIN: frozen for the whole spin, including a card deal taking it over.
  {
    const {e,cnt}=mk(),s=e.self.tod_ptn,a=actor(e,s,3,cnt);
    e.tick(s);ok(cnt.attacks===1&&!s.paused,'a free companion fights');
    e.self.tod_spin_locked=true;e.self.tod_menu_frozen=true;   // _tod_shop spin_lock
    e.now+=100;e.tick(s);
    ok(s.paused&&s.frz_why==='owner_spin'&&a.ignoreall===true&&a.ignoreme===true&&a.rate===0.01,'the spin freezes it: no native enemy, untargetable, stopped');
    ok(a.cleared===1&&a.goals[a.goals.length-1]===a.origin,'frozen where it stands (path cleared, goal at its feet)');
    const heals=cnt.heals;
    for(let i=0;i<100;i++){e.now+=100;e.tick(s);}
    ok(cnt.attacks===1,'no shots for the whole 10 s spin (got '+(cnt.attacks-1)+')');
    ok(cnt.heals===heals,'no NANO REPAIR while frozen');
    ok(hit(e,a,120)===0,'a zombie swing lands on nothing while it is frozen');
    e.self.tod_menu_frozen=undefined;e.now+=100;e.tick(s);
    ok(s.paused&&s.frz_why==='owner_spin','the spin lock holds it through the hand-over gap to a card deal');
    e.level.tod_upgrade_pause=true;e.now+=100;e.tick(s);
    ok(s.paused&&s.frz_why==='world_pause'&&e.logs.some(l=>l.startsWith('PAUSE_REASON')&&l.includes('from=owner_spin to=world_pause')),'a deal taking the spin over is a reason change, never a thaw');
    ok(e.logs.filter(l=>l.startsWith('PAUSE value=1')).length===1,'one freeze line for the whole spin');
    e.level.tod_upgrade_pause=false;e.self.tod_spin_locked=undefined;e.now+=100;e.tick(s);
    ok(!s.paused&&a.ignoreall===true&&a.ignoreme===false&&a.rate===1,'the thaw hands the drone back its own ignoreall, targetable, its own rate');
    ok(cnt.attacks===2,'it fights again the tick the screen closes');
    ok(cnt.teleports===0&&s.stuck_since===e.now,'10 s frozen is not stuck: no RECOVER teleport when the spin ends');
    const off=e.logs.find(l=>l.startsWith('PAUSE value=0'));
    ok(off&&/ why_was=world_pause /.test(off)&&/ shots_during=0 kills_during=0 hits_blocked=1 /.test(off),'the PAUSE value=0 line proves no shots, no kills and the blocked hit: '+off);
    ok(hit(e,a,120)===120,'hurtable again after the thaw');
    // positive control for the teleport check above: a stale clock does RECOVER
    s.stuck_since=e.now-8000;s.next_goal=0;e.now+=100;e.tick(s);
    ok(cnt.teleports===1,'control: a partner stuck 8 s away from its owner is recovered, so the no-teleport check can fail');
  }
  // 2. CO-OP: only the dealt player's companion freezes, each by its own reason.
  {
    const {e,cnt}=mk(),s1=e.self.tod_ptn,s2=e.p2.tod_ptn;
    const a1=actor(e,s1,0,cnt),a2=actor(e,s2,1,cnt);
    e.p2.tod_menu_frozen=true;e.tick(s1);e.tick(s2);
    ok(!s1.paused&&s2.paused&&s2.frz_why==='owner_menu'&&cnt.attacks===1,'co-op: only the companion of the player in a card deal freezes');
    ok(a1.ignoreall===false&&a1.ignoreme===false&&a1.rate===1,'the other companion is untouched');
    e.p2.tod_menu_frozen=undefined;e.p2.tod_solo_upg_active=true;e.now+=100;e.tick(s2);
    ok(s2.paused&&s2.frz_why==='owner_cards','a co-op altar deal holds it too (the same card screen)');
    e.p2.down=true;e.now+=100;e.tick(s2);
    ok(!s2.paused&&a2.ignoreme===false&&a2.ignoreall===true,'a DOWNED owner releases it: it fights over its crawling owner');
    e.level.tod_upgrade_pause=true;e.now+=100;e.tick(s1);e.tick(s2);
    ok(s1.paused&&s2.paused&&s2.frz_why==='world_pause','a world pause holds every companion, a downed owner included');
    e.level.tod_upgrade_pause=false;e.p2.down=false;e.p2.tod_solo_upg_active=undefined;e.now+=100;e.tick(s1);e.tick(s2);
    ok(!s1.paused&&!s2.paused&&a1.ignoreall===false&&a2.ignoreall===true,'each thaws to its own setting: the Protector may shoot, the drone stays quiet');
  }
  // 3. The thaw hands back whatever the companion had, not fixed values (9c review).
  {
    const {e,cnt}=mk(),s=e.self.tod_ptn,a=actor(e,s,2,cnt);
    a.ignoreme=true;e.self.tod_menu_frozen=true;e.tick(s);
    e.self.tod_menu_frozen=undefined;e.now+=100;e.tick(s);
    ok(!s.paused&&a.ignoreme===true&&a.rate===1.35,'thaw restores the pre-freeze ignoreme and R.A.P.S. keeps its 1.35 sprint rate');
  }
  // 4. Zombies stop picking a frozen companion (the closest-player seam).
  {
    const {e,cnt}=mk(),s=e.self.tod_ptn,a=actor(e,s,3,cnt);
    e.level.tod_partner_records=[s];
    ok(e.closest_target([400,0,0],[e.self])===a,'control: a zombie beside a free companion goes for it');
    e.self.tod_spin_locked=true;e.tick(s);
    ok(e.closest_target([400,0,0],[e.self])===e.self,'a frozen companion is never the zombie target');
  }
  // 5. A companion due back mid-spin waits for the screen to close.
  {
    const {e,cnt}=mk(),s=e.self.tod_ptn;
    s.chosen=1;s.actor=undefined;s.ready[1]=0;s.retry=0;
    e.self.tod_spin_locked=true;e.tick(s);ok(cnt.deploys===0,'no deploy into a frozen scene');
    e.self.tod_spin_locked=undefined;e.tick(s);ok(cnt.deploys===1,'it deploys the tick the spin ends');
  }
  // 6. NEGATIVE CONTROL: the gate shipped before this fix (world pause only)
  // reproduces the user report - the companion fights through the spin.
  {
    const {e,cnt}=mk(),s=e.self.tod_ptn;actor(e,s,3,cnt);
    e.freeze_reason=p=>(e.level.tod_upgrade_pause===true?'world_pause':undefined);
    e.self.tod_spin_locked=true;e.self.tod_menu_frozen=true;
    for(let i=0;i<100;i++){e.now+=100;e.tick(s);}
    ok(!s.paused&&cnt.attacks>=50,'negative control: the old gate keeps shooting through the spin (got '+cnt.attacks+' attacks)');
  }
  ok(body('freeze_reason').indexOf('world_pause')<body('freeze_reason').indexOf('player_is_in_laststand'),'the world pause is read before the downed-owner release');
}
// PK22 (2026-10-05): THE MOVEMENT LOOPS - the shipping loop_set + freeze, driven: each drone type its own loop on its
// visual, change-gated (no re-trigger per tick), silenced by a freeze, and nothing for the Civil Protector (its own feet).
{
  const e=context(),s=e.self.tod_ptn;const calls=[];
  const vis=()=>({PlayLoopSound(a){calls.push('play:'+a)},StopLoopSound(){calls.push('stop')},Delete(){calls.push('del')}});
  for(const [id,alias] of [[1,'tod_ptn_talon_hover_lp'],[2,'tod_ptn_raps_roll_lp'],[3,'tod_ptn_cerberus_servo_lp']]){
    calls.length=0;s.chosen=id;s.visual=vis();s.loop_on=undefined;
    e.loop_set(s,true);e.loop_set(s,true);
    ok(calls.join()==='play:'+alias,'PK22: type '+id+' plays '+alias+' once (change-gated)');
    e.loop_set(s,false);ok(calls[calls.length-1]==='stop'&&s.loop_on===false,'PK22: type '+id+' loop stops');
  }
  calls.length=0;s.chosen=0;s.visual=undefined;e.loop_set(s,true);ok(calls.length===0,'PK22: the Civil Protector has no drone loop');
  calls.length=0;s.chosen=1;s.visual=vis();s.loop_on=true;
  const a={origin:[0,0,0],ignoreall:false,ignoreme:false,ASMSetAnimationRate(){},ClearPath(){},SetGoal(){}};
  s.shots=0;s.kills=0;e.freeze(s,a,'owner_spin');
  ok(calls.join()==='stop'&&s.loop_on===false,'PK22: a freeze silences the drone');
  const src2=src.replace(/\/\/[^\n]*/g,'');
  ok(/function visual_tick\([^]*?if \( id == 1 \) loop_set\( s, true \);/.test(src2),'PK22: visual_tick (after the pause gate) restarts the loop after a thaw');
  ok(/s\.visual Delete\(\);[^\n]*\n\s*s\.actor = undefined; s\.visual = undefined; s\.target = undefined; s\.loop_on = undefined;/.test(src),'PK22: retire deletes the visual (Delete ends its loop) and clears the latch');
}
// THE BOWLING BALL (user 2026-10-05: "I would expect it to hit things like by physically running them over
// or touching them ... too fast too. It was like almost like teleporting everywhere"). Executes the shipping
// raps_goal / raps_touch: the lock holds through a closer zombie and the 700..950 band, lets go on a kill, a
// stray or 4 s untouched (and skips that one), the rate is slower per mode, a touch hits once per 600 ms.
{
  const num=n=>Number((src.match(new RegExp('#define '+n+'\\s+([0-9.]+)'))||[])[1]);
  const D={};for(const n of ['HUNT_R','RELEASE_R','LOCK_MS','ORBIT_R','ORBIT_STEP','ORBIT_MS','RATE_ORBIT','RATE_CHARGE','TOUCH_R','TOUCH_MS','TOUCH_FRAC'])D['TOD_PTN_RAPS_'+n]=num('TOD_PTN_RAPS_'+n);
  for(const [k,v] of Object.entries(D))ok(Number.isFinite(v),'define '+k);
  ok(D.TOD_PTN_RAPS_RATE_ORBIT<D.TOD_PTN_RAPS_RATE_CHARGE&&D.TOD_PTN_RAPS_RATE_CHARGE<1.35,'slower than the 885 u/s ball (1.35), and it rams faster than it circles');
  ok(D.TOD_PTN_RAPS_RELEASE_R>D.TOD_PTN_RAPS_HUNT_R+100,'the release line sits well past the lock line (no flip-flop at 700)');
  ok(!/#define TOD_PTN_RAPS_RATE\s/.test(src),'the single 1.35 rate is retired');
  const tr2=code=>translate(code).replace(/\b(z|s\.owner|s\.raps_lock) (GetEntityNumber|GetVelocity)\(/g,'$1.$2(');
  const mkRaps=fnSrc=>{
    const logs=[],hits=[],rates=[];
    const env=Object.assign({},D,{logs,hits,rates,isdefined:x=>x!==undefined&&x!==null,isalive:x=>!!x&&x.alive!==false,IS_TRUE:x=>x===true,
      abs:Math.abs,int:Math.trunc,log:m=>logs.push(m),item_mult:()=>1,TOD_ITEM_SIGHT:4,TOD_PTN_HIT_FX:'fx',TOD_PTN_HIT_SECS:0.3,
      Distance:(u,v)=>Math.hypot(u[0]-v[0],u[1]-v[1],u[2]-v[2]),Distance2D:(u,v)=>Math.hypot(u[0]-v[0],u[1]-v[1]),
      GetClosestPointOnNavMesh:()=>undefined,AnglesToForward:()=>[1,0,0],fx_burst:()=>{},axis:[],GetAITeamArray:()=>env.axis,
      deal_damage:(s,z,frac)=>{hits.push([z.id,frac]);return 7;}});
    vm.createContext(env);
    vm.runInContext(`function raps_goal(s,owner_goal,now){let p,a,sight,z,why,goal,mode,base,want,target_num;${tr2(fnSrc('raps_goal'))}}`,env);
    vm.runInContext(`function raps_touch(s,now){let a,r2,dx,dy,hp,dmg;${tr2(fnSrc('raps_touch'))}}`,env);
    return env;
  };
  const zombie=(id,x)=>({id,alive:true,origin:[x,0,0],health:50,GetEntityNumber:()=>id});
  const rec=env=>({owner:{origin:[0,0,0],GetEntityNumber:()=>0},actor:{origin:[0,0,0],ASMSetAnimationRate(r){env.rates.push(r)}},
    chosen:2,raps_mode:'',rate:D.TOD_PTN_RAPS_RATE_ORBIT,orbit:0,next_orbit:0,raps_touches:0});
  {
    const env=mkRaps(body),s=rec(env),A=zombie(31,600),B=zombie(32,300);
    s.target=A;env.raps_goal(s,[0,0,0],1000);
    ok(s.raps_lock===A&&s.raps_mode==='charge'&&s.rate===D.TOD_PTN_RAPS_RATE_CHARGE,'locks the zombie it charges at the charge rate');
    s.target=B;env.raps_goal(s,[0,0,0],1200);
    ok(s.raps_lock===A&&s.target===A,'a closer zombie does not steal the lock (the blast follows the lock)');
    A.origin=[800,0,0];s.target=undefined;env.raps_goal(s,[0,0,0],1400);
    ok(s.raps_lock===A&&s.raps_mode==='charge','inside the 700..950 band it keeps ramming');
    A.origin=[1000,0,0];env.raps_goal(s,[0,0,0],1600);
    ok(s.raps_lock===undefined&&s.raps_mode==='orbit'&&s.rate===D.TOD_PTN_RAPS_RATE_ORBIT,'past the release line it lets go and circles at the orbit rate');
    ok(env.logs.some(l=>/RAPS_RELEASE .*target=31 why=far/.test(l)),'RAPS_RELEASE why=far logged');
    s.target=B;env.raps_goal(s,[0,0,0],1800);ok(s.raps_lock===B,'then locks the next one in reach');
    B.alive=false;s.target=undefined;env.raps_goal(s,[0,0,0],2000);
    ok(s.raps_lock===undefined&&env.logs.some(l=>/why=dead/.test(l)),'a dead lock lets go (why=dead)');
    const C=zombie(33,200);s.target=C;env.raps_goal(s,[0,0,0],3000);
    env.raps_goal(s,[0,0,0],3000+D.TOD_PTN_RAPS_LOCK_MS+1);
    ok(s.raps_lock===undefined&&s.raps_skip===C&&env.logs.some(l=>/target=33 why=no_touch/.test(l)),'4 s without a touch lets go and remembers that one');
    s.target=C;env.raps_goal(s,[0,0,0],3000+D.TOD_PTN_RAPS_LOCK_MS+200);
    ok(s.raps_lock===undefined&&s.raps_mode==='orbit','it does not lock the unreachable zombie straight back');
  }
  // The user's run: one zombie hovering at the 700 line while the owner moves. The 2026-09-28 goal flipped
  // charge <-> orbit on every crossing; the lock holds.
  {
    const OLD="    p = s.owner; a = s.actor;\n    if ( isdefined( s.target ) && isalive( s.target ) && Distance( s.target.origin, p.origin ) < TOD_PTN_RAPS_HUNT_R * item_mult( s, TOD_ITEM_SIGHT ) )\n    {\n        goal = GetClosestPointOnNavMesh( s.target.origin, 64, 16 );\n        if ( !isdefined( goal ) ) goal = s.target.origin;\n        mode = \"charge\";\n    }\n    else\n    {\n        goal = owner_goal;\n        mode = \"orbit\";\n    }\n    if ( mode != s.raps_mode )\n    {\n        s.raps_mode = mode;\n        log( \"RAPS_MODE \" + mode );\n    }\n    return goal;\n";
    const flips=fnSrc=>{const env=mkRaps(fnSrc),s=rec(env),Z=zombie(40,690);let n=0,last='';
      for(let i=0;i<20;i++){Z.origin=[(i%2)?710:690,0,0];s.target=Z;s.raps_lock_touch=1000+i*200;env.raps_goal(s,[0,0,0],1000+i*200);if(s.raps_mode!==last){n++;last=s.raps_mode;}}return n;};
    const oldFlips=flips(name=>name==='raps_goal'?OLD:body(name)),newFlips=flips(body);
    ok(oldFlips>=19,'negative control: the old goal flips on every crossing ('+oldFlips+')');
    ok(newFlips===1,'the lock holds across the 700 line ('+newFlips+' mode change)');
  }
  {
    const env=mkRaps(body),s=rec(env),near=zombie(51,40),far=zombie(52,60),high=zombie(53,30);high.origin=[30,0,60];
    env.axis=[near,far,high];s.raps_lock=near;s.raps_lock_touch=0;
    env.raps_touch(s,5000);
    ok(env.hits.length===1&&env.hits[0][0]===51&&env.hits[0][1]===D.TOD_PTN_RAPS_TOUCH_FRAC,'rolls into the zombie at 40 u (half a blast); 60 u flat and 60 up are not touched');
    ok(s.raps_lock_touch===5000&&near.tod_raps_touch_ms===5000,'a touch keeps the lock and stamps the zombie for the throw');
    env.raps_touch(s,5100);ok(env.hits.length===1,'the same zombie is not hit again inside 600 ms');
    env.raps_touch(s,5000+D.TOD_PTN_RAPS_TOUCH_MS);ok(env.hits.length===2,'after 600 ms it is hit again');
    ok(env.logs.some(l=>/RAPS_TOUCH .*target=51 n=1 damage=7 .*locked=true/.test(l)),'RAPS_TOUCH logged with the lock');
  }
  {
    // OFF LIMITS WHILE BOUND (2026-10-05): a zombie a Necromancer is binding is never touched, picked, arced or shot.
    const env=mkRaps(body),s=rec(env),bound=zombie(61,30);bound.tod_necro_binder={};
    env.axis=[bound];env.raps_touch(s,9000);
    ok(env.hits.length===0,'the R.A.P.S. rolls past a zombie being bound');
    for(const fn of ['target_for','arc_chain','raps_touch'])ok(body(fn).includes('if ( isdefined( z.tod_necro_binder ) ) continue;'),fn+' skips a bound zombie');
    ok(body('attack').includes('if ( isdefined( target.tod_necro_binder ) ) continue;')&&body('attack').includes('if ( isdefined( z.tod_necro_binder ) ) return;'),'the blast and the shot skip a bound zombie');
    ok(body('raps_goal').includes('why = "bound"'),'a lock that gets bound lets go');
  }
  const tk2=body('tick');
  ok(tk2.indexOf('if ( id == 2 ) raps_touch( s, now );')>tk2.indexOf('if ( paused ) return;'),'the touch runs after the pause gate (a frozen ball hits nothing)');
  ok(body('kill_credit').indexOf('raps_fling( attacker.tod_partner_state, self );')<body('kill_credit').indexOf('p = attacker.tod_partner_owner;'),'a roll-over kill is thrown even when the owner is down');
  const fl=body('raps_fling');
  for(const s2 of ['s.chosen != 2','GetTime() - z.tod_raps_touch_ms > 100','isdefined( z.tod_boss_kind )','IS_TRUE( z.tod_bat_launched )','level.ragdoll_limit_check','z StartRagdoll();','z LaunchRagdoll( impulse );','"RAPS_FLING '])
    ok(fl.includes(s2),'raps_fling keeps: '+s2);
}
// THE DROP (LT-fix 2026-10-05, staged first as LT-mocomp; the user's 17:33 run threw 211 SCRIPTERROR pairs in stock
// animation_state_machine_mocomp.gsc while the R.A.P.S. followed its owner down the broken drops). (A) STATIC: every
// traversal type the generated .map places, looked up in the partner aitype's selector table exactly as the engine
// does (combat_traverse@traversal, the node's animscript, else the "*" row), must name a mocomp that is either native
// or registered by a map script. (B) EXECUTED: the shipping register_drop_traversal / drop_traverse_start /
// drop_traverse_end. (C) NEGATIVE CONTROL: the module without the registration fails (A), as the 15:10 .ff did.
{
  const path=require('path');
  const MOCOMP_NATIVE=new Set([
    // registered by NO stock or map script and still error-free in every archived run: zm_factory_zombie.ai_ast
    // takes every zm_jump_down_190 drop with the first (all runs since 2026-09-27); the second is its non-strict twin
    'mocomp_move_strict_traversal@locomotion','mocomp_move_traversal@locomotion']);
  const gdt=fs.readFileSync(root+'/source_data/tod_partners.gdt','utf8');
  const blk=gdt.slice(gdt.indexOf('"spawner_tod_partner" ( "aitype.gdf" )'));
  const astName=(/"animSelectorTableName" "([^"]+)"/.exec(blk)||[])[1];
  ok(!!astName,'the partner aitype names a selector table');
  const astPath=[root+'/animtables/'+astName,'C:/BO3Tools/TOD2Cybercity/share/raw/animtables/'+astName].find(p=>fs.existsSync(p));
  ok(!!astPath,'the partner selector table is readable: '+astName);
  const table=p=>{const ast=fs.readFileSync(p,'latin1').replace(/\r/g,'');
    const sel=ast.split('\n,\n').map(b=>b.trim().split('\n')).find(l=>l[0].trim().toLowerCase()==='combat_traverse@traversal');
    ok(!!sel,'the table has combat_traverse@traversal: '+p);
    const hdr=sel[1].split(','),ti=hdr.indexOf('_traversal_type'),mi=hdr.indexOf('_animation_mocomp');
    const rows=sel.slice(2).map(l=>l.split(','));
    return kind=>{const r=rows.find(x=>x[ti].toLowerCase()===kind.toLowerCase())||rows.find(x=>x[ti]==='*');return r?r[mi].toLowerCase():undefined;};};
  const live=table(astPath);
  // the 15:10 .ff's table (stock): its "*" row is what the 17:33 drops selected
  const STOCK_AST='C:/BO3Tools/TOD2Cybercity/share/raw/animtables/zod_robot_companion.ai_ast';
  const stock=fs.existsSync(STOCK_AST)?table(STOCK_AST):undefined;
  const map=fs.readFileSync(root+'/map_source/zm/zm_tod2_cybercity.map','latin1');
  const kinds=new Set();for(const m of map.matchAll(/"classname" "node_negotiation_begin"[^}]*?"animscript" "([^"]+)"/g))kinds.add(m[1]);
  ok(kinds.size>=1,'the generated map places negotiation drops ('+[...kinds].join()+')');
  const registered=gsc=>{const defs={};for(const m of gsc.matchAll(/#define\s+(\w+)\s+"([^"]+)"/g))defs[m[1]]=m[2];
    const out=new Set();for(const m of gsc.matchAll(/RegisterAnimationMocomp\(\s*("([^"]+)"|(\w+))/g))out.add((m[2]||defs[m[3]]||'').toLowerCase());return out;};
  const scriptsDir=root+'/scripts';const allGsc=[];(function walk(d){for(const e of fs.readdirSync(d,{withFileTypes:true})){const p=path.join(d,e.name);
    if(e.isDirectory())walk(p);else if(/\.gsc$/.test(e.name))allGsc.push(p);}})(scriptsDir);
  const unsupported=(srcPartners,pick)=>{const reg=new Set();for(const f of allGsc){const t=/_tod_partners\.gsc$/.test(f)?srcPartners:fs.readFileSync(f,'utf8');
      for(const n of registered(t))reg.add(n);}
    const bad=[];for(const k of kinds){const mc=pick(k);
      if(!mc||!(MOCOMP_NATIVE.has(mc)||reg.has(mc)))bad.push(k+' -> '+(mc||'(no row)'));}return bad;};
  const bad=unsupported(src,live);
  ok(bad.length===0,'(A) every drop type the companion can take ('+astName+') names a native or registered mocomp; unsupported: '+bad.join('; '));
  const old=src.replace(/AnimationStateNetwork::RegisterAnimationMocomp\([^;]*;/,'');
  ok(old!==src,'the registration call is where the negative control expects it');
  if(stock){
    // (A2) the safety net holds on the stock table too (its "*" row), whatever table the aitype names
    ok(unsupported(src,stock).length===0,'(A2) with the stock table the "*" row mocomp is registered by the module');
    // (C) negative control: the 15:10 .ff = stock table + no registration -> the 17:33 errors
    ok(unsupported(old,stock).some(b=>/mocomp_teleport_traversal@zombie/.test(b)),'(C) negative control: stock table without the registration selects an unregistered mocomp (the 17:33 errors)');
  }
  // (B) executed
  const e=context();const logs=[];e.log=m=>logs.push(m);
  e.TOD_PTN_TRAV_MOCOMP='mocomp_teleport_traversal@zombie';
  const regs=[];e.AnimationStateNetwork={RegisterAnimationMocomp:(n,a,b,c)=>regs.push([n,a,b,c])};
  e.Distance=(x,y)=>Math.hypot(x[0]-y[0],x[1]-y[1],x[2]-y[2]);
  let arrived=[];e.arrive_fx=o=>arrived.push(o);
  const tr=code=>translate(code.replace(/\b(entity|s\.owner) (OrientMode|AnimMode|ForceTeleport|GetEntityNumber)\(/g,'$1.$2(')
    .replace(/AnimationStateNetwork::/g,'AnimationStateNetwork.').replace(/&(\w+)/g,'$1'));
  vm.runInContext(`function register_drop_traversal(){${tr(body('register_drop_traversal'))}}`,e);
  vm.runInContext(`function drop_traverse_start(entity,mocompAnim,b,f,d){let node,kind,src,dst,ang,s,now,owner_num,owner_dist;${tr(body('drop_traverse_start'))}}`,e);
  vm.runInContext(`function drop_traverse_end(entity,mocompAnim,b,f,d){let held;${tr(body('drop_traverse_end'))}}`,e);
  e.level._AnimationMocomps=undefined;e.register_drop_traversal();
  ok(regs.length===0&&/TRAVERSE_MOCOMP skipped/.test(logs.pop()),'no mocomp table: nothing registered, logged');
  e.level._AnimationMocomps={};e.register_drop_traversal();
  ok(regs.length===1&&regs[0][0]==='mocomp_teleport_traversal@zombie'&&regs[0][1]===e.drop_traverse_start&&regs[0][2]===undefined&&regs[0][3]===e.drop_traverse_end,'(B) registers the stock name with start + terminate');
  ok(/TRAVERSE_MOCOMP registered/.test(logs.pop()),'the registration is logged');
  e.level._AnimationMocomps={'mocomp_teleport_traversal@zombie':['stock']};e.register_drop_traversal();
  ok(regs.length===1&&/already_registered/.test(logs.pop()),'an existing registration is never replaced');
  ok(/register_drop_traversal\(\);/.test(body('init')),'init registers it');
  const mkActor=(partner)=>{const calls=[];const a={origin:[-336,-288,18242],angles:[0,90,0],calls,
    traverseStartNode:{animscript:'zm_jump_down_190'},traverseEndNode:{origin:[-336,-237,18052],angles:[0,90,0]},
    OrientMode(m,y){calls.push('orient:'+m+':'+y)},AnimMode(m){calls.push('anim:'+m)},
    ForceTeleport(o,an,f){calls.push('tp');this.origin=o},GetEntityNumber:()=>26};
    if(partner){const s=e.self.tod_ptn;s.chosen=2;s.actor=a;s.owner=e.self;s.visual={origin:[0,0,0]};s.stuck_since=0;s.move_ref_ms=0;
      a.tod_is_partner=true;a.tod_partner_state=s;}
    return a;};
  e.self.origin=[-330,-180,18050];
  { const a=mkActor(true),s=e.self.tod_ptn;e.now=50000;arrived=[];e.drop_traverse_start(a);
    ok(a.calls.join()==='orient:face angle:90,anim:zonly_physics,tp','(B) start: faces its heading, holds on z-only physics, teleports');
    ok(a.origin.join()==='-336,-237,18052','the companion lands on the drop END node');
    ok(s.visual.origin.join()==='-336,-237,18052'&&s.visual_last.join()==='-336,-237,18052','its drone body snaps with it');
    ok(arrived.length===1&&arrived[0].join()==='-336,-237,18052','it materialises with the arrival look');
    ok(s.stuck_since===50000&&s.move_ref_ms===50000,'a drop restarts the stuck / stall clocks at the landing');
    const l=logs.pop();ok(/^TRAVERSE_TELEPORT partner=1 owner=0 type=2 actor=26 kind=zm_jump_down_190 .* drop=190 /.test(l),'logged with owner, type, kind and drop height: '+l);
    e.now=52750;e.drop_traverse_end(a);
    // (a GSC bool prints 1; the JS stand-in prints true)
    ok(/^TRAVERSE_END actor=26 partner=(1|true) held_ms=2750 /.test(logs.pop())&&a.tod_drop_ms===undefined,'terminate logs how long the state held it');
  }
  { const a=mkActor(false);arrived=[];e.drop_traverse_start(a);
    ok(a.calls.includes('tp')&&arrived.length===0&&/^TRAVERSE_TELEPORT partner=0 /.test(logs.pop()),'any other actor on that row is teleported the stock way, no companion arrival');
  }
  { const a=mkActor(true);a.traverseEndNode=undefined;arrived=[];e.drop_traverse_start(a);
    ok(!a.calls.includes('tp')&&arrived.length===0&&/^TRAVERSE_SKIP reason=no_end_node/.test(logs.pop()),'no end node: no teleport, logged');
  }
  { const a=mkActor(true);const s=a.tod_partner_state;s.actor={other:true};arrived=[];e.drop_traverse_start(a);
    ok(arrived.length===0&&/partner=0/.test(logs.pop()),'a stale actor (not its state\'s current body) never touches the live companion\'s visual');
  }
  ok(!/\bwait\b|endon/.test(body('drop_traverse_start')+body('drop_traverse_end')+body('register_drop_traversal')),'mocomp callbacks never wait or endon');
}
// LT-fix (2026-10-05; the user's 17:33 run, archive tmp/elite_tracking/runs/20261005_175358_367_fe125096).
// (1) THE OWNER'S GROUND: an airborne owner (a drop, the jump pad, a ledge jump) is off the mesh; the old fallback
// goaled the companion at his raw origin IN THE AIR (PATHFIND_FAILURE_INVALID_END to z 19741, 350 u over the crown
// floor, 250 ms after a jump-pad launch) and target_for measured from that air point (target=-1).
// (2) A JUMP-PAD FLYER IS UNTOUCHABLE: no RECOVER teleport and no deploy anchored on him mid-flight.
// (3) NOT STUCK AT ITS GOAL: a R.A.P.S. parked on the guardian it charges was RECOVERed off it (stuck=1).
// (4) ELITES HUNT PLAYERS ONLY: the closest-player seam handed the Mangler the companion every behaviour tick
// (160 [TOD_MANGLER] RETARGET lines) while its players-only hunt wrote the player back.
// (5) A NECROMANCER'S BIND IS HIS: target_for (the peer's binder skip) still holds with the ground anchor.
{
  const ground=[0,5000,19392], air=[0,5000,19742];
  // (1) owner_ground, executed
  {
    const e=context(),s=e.self.tod_ptn;const logs=[];e.log=m=>logs.push(m);s.chosen=2;
    let navAt=ground;e.GetClosestPointOnNavMesh=()=>navAt;
    e.self.origin=[0,5000,19392];
    ok(e.owner_ground(s,e.self,1000)===ground&&logs.length===0,'(1) a grounded owner: the mesh under him, nothing logged');
    navAt=undefined;e.self.origin=air;e.self.last_valid_position=ground;
    ok(e.owner_ground(s,e.self,1250)===ground,'(1) an airborne owner: stock last_valid_position (his last on-mesh point), never his air origin');
    ok(logs.length===1&&/^OWNER_OFF_MESH owner=0 type=2 anchor=last_valid_position flying=false /.test(logs[0]),'(1) the off-mesh spell is logged once: '+logs[0]);
    e.owner_ground(s,e.self,1450);ok(logs.length===1,'(1) ... and only once per spell');
    navAt=ground;e.self.origin=ground;e.owner_ground(s,e.self,2250);
    ok(logs.length===2&&/^OWNER_ON_MESH owner=0 type=2 off_ms=1000 /.test(logs[1])&&s.air_ms===undefined,'(1) back on the mesh: OWNER_ON_MESH with the spell length: '+logs[1]);
    navAt=undefined;e.self.origin=air;e.self.last_valid_position=undefined;
    ok(e.owner_ground(s,e.self,3000)===air&&/anchor=origin/.test(logs[2]),'(1) no last_valid_position at all: his origin (the old behaviour, never worse)');
    const tk=body('tick');
    ok(tk.includes('goal = owner_ground( s, p, now );')&&!tk.includes('if ( !isdefined( goal ) ) goal = p.origin;'),'(1) tick goals the owner\'s ground, not his raw origin');
    // the 15:10 lane, verbatim (fixture): a NEGATIVE CONTROL for the check above
    const OLD_TICK='        goal = GetClosestPointOnNavMesh( p.origin, 96, 24 );\n        if ( !isdefined( goal ) ) goal = p.origin;\n        if ( id == 2 ) goal = raps_goal( s, goal, now );';
    ok(!OLD_TICK.includes('goal = owner_ground( s, p, now );')&&OLD_TICK.includes('if ( !isdefined( goal ) ) goal = p.origin;'),'(1) negative control: the 15:10 tick fell back to the raw (airborne) origin');
    ok(tk.indexOf('s.anchor = goal;')>=0&&tk.indexOf('s.anchor = goal;')<tk.indexOf('s.target = target_for( s );'),'(1) the anchor is set before target_for measures from it');
    const OLD_ORBIT='        if ( !isdefined( goal ) || abs( goal[ 2 ] - p.origin[ 2 ] ) > 48 ) goal = base;   // no floor there: roll to the owner';
    ok(!/p\.origin/.test(body('raps_goal'))&&/p\.origin\[ 2 \]/.test(OLD_ORBIT),'(1) raps_goal measures from the ground anchor (the 15:10 one compared the orbit point with the airborne owner)');
  }
  // (1)+(5) target_for, executed: from the ground anchor, and never a bound zombie
  {
    const e=context(),s=e.self.tod_ptn;
    Object.assign(e,{abs:Math.abs,item_mult:()=>1,SightTracePassed:()=>true,
      DistanceSquared:(u,v)=>(u[0]-v[0])**2+(u[1]-v[1])**2+(u[2]-v[2])**2});
    const z=(id,o,extra)=>Object.assign({alive:true,origin:o,GetEntityNumber:()=>id},extra||{});
    const zs=[z(31,[100,5000,19392],{tod_necro_binder:e.p2}),z(32,[300,5000,19392])];
    e.GetAITeamArray=()=>zs;
    vm.runInContext(`function target_for(s){let sight,best,nearest,anchor,dist,from;${translate(body('target_for'))}}`,e);
    s.chosen=2;s.owner=e.self;s.actor={origin:[0,5000,19392]};e.self.origin=air;s.anchor=ground;
    const t=e.target_for(s);
    ok(t===zs[1],'(1) an airborne owner\'s companion still finds the zombie beside it (measured from his ground)');
    ok(t!==zs[0],'(5) ... and never the nearer zombie a Necromancer is binding');
    s.anchor=undefined;
    ok(e.target_for(s)===undefined,'(1) control: measured from the airborne origin (350 u up) every zombie drops, the 17:33 target=-1');
    ok(/s\.anchor = undefined;/.test(body('deploy')),'(1) a fresh deploy starts with no stale anchor');
  }
  // (2)+(3) tick, executed: the flyer hold, the deploy refusal and the stuck-at-goal rule
  {
    const mkT=()=>{
      const e=context(),cnt={teleports:0,deploys:0};const logs=[];e.log=m=>logs.push(m);
      Object.assign(e,{GetClosestPointOnNavMesh:(o)=>o,abs:Math.abs,
        DistanceSquared:(u,v)=>(u[0]-v[0])**2+(u[1]-v[1])**2+(u[2]-v[2])**2,
        target_for:()=>undefined,landing_point:()=>[5,5,0],path_start_watch:()=>{},
        visual_tick:()=>{},move_watch:()=>{},raps_touch:()=>{},attack:()=>{},deploy:()=>{cnt.deploys++}});
      e.Distance=(u,v)=>Math.sqrt(e.DistanceSquared(u,v));e.nano_tick=()=>{};
      const s=e.self.tod_ptn;e.self.origin=[0,0,0];
      const a={alive:true,health:900,maxhealth:1000,origin:[1500,0,0],ignoreall:true,ignoreme:false,goals:[],
        tod_partner_state:s,ASMSetAnimationRate(){},ClearPath(){},SetGoal(g){this.goals.push(g)},
        ForceTeleport(o){cnt.teleports++;this.origin=o},GetEntityNumber:()=>26};
      s.chosen=2;s.actor=a;s.paused=false;s.rate=0.6;s.shots=0;s.kills=0;s.next_shot=0;s.next_goal=0;s.next_log=Infinity;
      s.last_origin=a.origin;s.stuck_since=e.now;s.goal=[0,0,0];
      return {e,cnt,logs,s,a};
    };
    { const {e,cnt,logs,s,a}=mkT();e.raps_goal=(s,g)=>g;
      e.self.tod_jumppad_flying=true;
      for(let i=0;i<5;i++){e.now+=200;e.tick(s);}
      ok(cnt.teleports===0,'(2) a companion 1500 u from a FLYING owner is never teleported to him mid-flight');
      ok(logs.filter(l=>/^RECOVER_HOLD owner=0 type=2 reason=owner_flying/.test(l)).length===1,'(2) RECOVER_HOLD is logged once per flight');
      e.self.tod_jumppad_flying=undefined;e.now+=200;e.tick(s);
      ok(cnt.teleports===1&&logs.some(l=>/^RECOVER_HOLD released /.test(l))&&logs.some(l=>/^RECOVER owner=0 type=2 far=true stuck=false goal_dist=\d+ to=5,5,0/.test(l)),'(2) he lands: released, and the far rule brings it to him at once');
      s.actor=undefined;s.ready[2]=0;s.retry=0;e.self.tod_jumppad_flying=true;e.tick(s);
      ok(cnt.deploys===0,'(2) a companion due back never deploys beside a flyer');
      e.self.tod_jumppad_flying=undefined;e.tick(s);ok(cnt.deploys===1,'(2) ... it deploys the tick he lands');
    }
    { const {e,cnt,logs,s,a}=mkT();a.origin=[400,0,0];s.last_origin=a.origin;
      e.raps_goal=(s,g)=>[410,0,0];   // charging a zombie it has reached: its goal is under it
      s.stuck_since=e.now-8000;e.now+=200;e.tick(s);
      ok(cnt.teleports===0,'(3) a R.A.P.S. parked ON the zombie it charges (goal 10 u away) is fighting, not stuck');
      e.raps_goal=(s,g)=>[900,0,0];s.next_goal=0;e.now+=200;e.tick(s);
      ok(cnt.teleports===1&&logs.some(l=>/^RECOVER .*stuck=true goal_dist=500 /.test(l)),'(3) control: short of a far goal for 7 s is still recovered');
    }
  }
  // (4) closest_target, executed: an elite keeps the player; a plain zombie still diverts
  {
    const e=context(),s=e.self.tod_ptn;const logs=[];e.log=m=>logs.push(m);
    Object.assign(e,{abs:Math.abs,DistanceSquared:(u,v)=>(u[0]-v[0])**2+(u[1]-v[1])**2+(u[2]-v[2])**2,
      ArrayGetClosest:(o,arr)=>arr.reduce((b,x)=>(!b||e.DistanceSquared(o,x.origin)<e.DistanceSquared(o,b.origin))?x:b,undefined)});
    e.Distance=(u,v)=>Math.sqrt(e.DistanceSquared(u,v));
    const player=e.self;player.origin=[0,0,0];
    s.chosen=2;s.owner=player;s.actor={alive:true,origin:[400,0,0],GetEntityNumber:()=>26};s.paused=false;
    e.level.tod_partner_records=[s];
    e.self={alive:true,origin:[450,0,0]};   // an ordinary zombie asking
    ok(e.closest_target([450,0,0],[player])===s.actor,'(4) control: an ordinary zombie beside the companion still goes for it');
    const mangler={alive:true,is_boss:true,tod_boss_kind:'mangler',GetEntityNumber:()=>45};e.self=mangler;
    ok(e.closest_target([450,0,0],[player])===player,'(4) a Mangler beside the companion keeps the player (its hunt is players-only)');
    ok(logs.length===1&&/^AGGRO_SKIP elite=45 kind=mangler companion=26 type=2 /.test(logs[0]),'(4) AGGRO_SKIP once per elite: '+logs[0]);
    e.closest_target([450,0,0],[player]);ok(logs.length===1,'(4) ... never again for that elite');
    e.self={alive:true,is_boss:true,GetEntityNumber:()=>32};
    ok(e.closest_target([450,0,0],[player])===player&&/kind=boss/.test(logs[1]),'(4) any is_boss actor (no tod_boss_kind) keeps the player too');
    e.self=player;
    ok(e.closest_target([450,0,0],[player])===s.actor,'(4) the seam asked on a player\'s behalf is unchanged');
    // NEGATIVE CONTROL: the 15:10 closest_target (verbatim fixture) hands the Mangler the companion (the tug-of-war)
    const OLD_CLOSEST=[
      '    nearest = ArrayGetClosest( origin, players );','    if ( !isdefined( nearest ) ) return undefined;',
      '    dist = DistanceSquared( origin, nearest.origin );','    foreach ( s in level.tod_partner_records )','    {',
      '        if ( !isdefined( s.owner ) || !isalive( s.owner ) || !isdefined( s.actor ) || !isalive( s.actor ) ) continue;',
      '        if ( IS_TRUE( s.paused ) ) continue;','        d = DistanceSquared( origin, s.actor.origin );',
      '        if ( d < 230 * 230 && d < dist && abs( origin[ 2 ] - s.actor.origin[ 2 ] ) < 80 )','        { dist = d; nearest = s.actor; }',
      '    }','    return nearest;'].join('\n');
    vm.runInContext(`function closest_target_old(origin,players){let nearest,dist,d;${translate(OLD_CLOSEST)}}`,e);
    e.self=mangler;
    ok(e.closest_target_old([450,0,0],[player])===s.actor,'(4) negative control: the 15:10 seam gave the Mangler the companion');
  }
  // path_start_watch is diagnostics only: once a second, and it writes nothing but its own throttle
  {
    const e=context(),s=e.self.tod_ptn;const logs=[];e.log=m=>logs.push(m);
    Object.assign(e,{BulletTrace:()=>({position:[0,0,17000]}),Length:v=>Math.hypot(...v)});
    vm.runInContext(`function path_start_watch(s,a,nav,now){let nav_dz,ground_hit,ground_pos;${translate(body('path_start_watch')).replace(/\ba (GetVelocity|HasPath)\(/g,'a.$1(').replace(/\bs\.owner GetEntityNumber\(/g,'s.owner.GetEntityNumber(')}}`,e);
    const a={origin:[0,0,17100],GetVelocity:()=>[870,0,0],HasPath:()=>true};s.owner=e.self;s.chosen=2;s.raps_mode='orbit';s.goal=[0,0,17000];
    e.path_start_watch(s,a,undefined,5000);e.path_start_watch(s,a,undefined,5500);e.path_start_watch(s,a,[0,0,17000],6000);
    ok(logs.length===2&&/^PATH_START_OFF owner=0 type=2 .* nav=false nav_dz=-1 floor_dz=100 speed=870 /.test(logs[0])&&/nav_dz=100 /.test(logs[1]),'PATH_START_OFF: throttled to 1/s, with the lift over the floor and the speed: '+logs[0]);
    const tk=body('tick');
    ok(/else path_start_watch\( s, a, nav, now \);/.test(tk),'tick runs it only when its own origin is off the mesh');
  }
}
console.log(`Partners PASS: ${checks} assertions against shipping GSC; THE BOWLING BALL (R.A.P.S. lock / release / touch / throw, old flip-flop caught); THE DEALER'S GIFT hand-off (docs/209, executed: every companion, co-op, refusals, a live pick retired first), the retired parts/bench flow, the arrival, no stub effects, cooldown, cleanup, damage, placement, the owner freeze, THE DROP (traversal mocomp, static + executed + negative control) and LT-fix (the owner's ground, the flyer hold, stuck-at-goal, elites keep the player).`);
