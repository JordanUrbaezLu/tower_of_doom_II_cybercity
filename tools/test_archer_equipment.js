// Execute the scalar decisions from the SHIPPING GSC; assert cross-file wiring.
// Physics, the native model, and replication still require the user's playtest.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const path = require('path');
const root = path.join(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const dir = 'scripts/zm/zm_tod2_cybercity/';
const src = read(dir + '_tod_archer.gsc');
const ctx = vm.createContext({int: Math.trunc, array: (...a) => a, isdefined: v => v !== undefined});
for (const m of src.matchAll(/^#define\s+(\w+)\s+([\d.]+)/gm)) ctx[m[1]] = Number(m[2]);
function body(name) {
  const start = src.indexOf('function ' + name + '(');
  assert(start >= 0, name);
  const open = src.indexOf('{', start);
  let i = open, depth = 0;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    if (src[i] === '}' && --depth === 0) break;
  }
  return src.slice(start, i + 1);
}
for (const name of ['countdown', 'press_edge', 'grapple_curve', 'grapple_range', 'land_secs', 'surface_reason', 'ignores_fall', 'hud_seconds', 'rope_next', 'radial_next', 'tang_scale']) {
  vm.runInContext(body(name), ctx);
}
let checks = 0;
const eq = (a,b,label) => { assert.deepStrictEqual(a,b,label); checks++; };
// THE GRAPPLE CARD (2026-09-25): 8 levels on ln(1+lvl)/ln(9); the table must be that curve.
for (let l = 0; l <= 9; l++) assert(Math.abs(ctx.grapple_curve(l) - Math.log(1+l)/Math.log(10)) < 1e-3, 'curve Lv'+l), checks++;
eq(ctx.grapple_curve(-1), 0, 'no card'); eq(ctx.grapple_curve(12), 1, 'clamped at Lv9');
for (let l = 1; l <= 9; l++) assert(ctx.grapple_curve(l) - ctx.grapple_curve(l-1) < (l > 1 ? ctx.grapple_curve(l-1) - ctx.grapple_curve(l-2) + 1e-9 : 1), 'log: every step smaller than the last'), checks++;
eq(ctx.grapple_range(0), ctx.TOD_ARCHER_RANGE, 'base range without the card');
eq(ctx.grapple_range(9), ctx.TOD_ARCHER_RANGE + ctx.TOD_ARCHER_RANGE_ADD, 'Lv9 range');
assert(Math.abs(ctx.land_secs(9) - 2.5) < 1e-9 && ctx.land_secs(1) > 1 && ctx.land_secs(1) < 1.5, 'landing window a second or two'); checks++;
assert(!src.includes('grapple_cooldown') && src.includes('TOD_ARCHER_GRAPPLE_CD * self aerialist_cd_mult() );   // dev test'), 'recharge is the fixed 12 s x the AERIALIST card (2026-09-27)'); checks++;
for (const [fraction,dist,normal,surface,want] of [
  [1,3000,1,'concrete','no_surface'], [0,400,1,'concrete','no_surface'],
  [.2,500,0,'none','no_surface'], [.9,2700,1,'sky','no_surface'],
  [.02,60,1,'metal','too_close'], [.5,3001,1,'metal','out_of_range'],
  [.5,128,1,'metal',''], [.5,3000,1,'concrete',''], [.5,900,1,'none','']
]) eq(ctx.surface_reason(fraction,dist,normal,surface,3000),want,'surface '+[fraction,dist,normal,surface]);
eq(ctx.surface_reason(.5,4900,1,'metal',ctx.grapple_range(9)),'','Lv9 reaches past the base range');
// Miss/cooldown paths must return BEFORE spending anything or creating flight state.
const grab = body('try_grapple');
assert(grab.indexOf('why != ""') < grab.indexOf('s.hook_cd ='));
assert(grab.indexOf('s.hook_cd > 0') < grab.indexOf('s.hook_cd ='));
checks += 2;
eq(ctx.press_edge(true,false),true,'fresh press');
eq(ctx.press_edge(true,true),false,'hold does not repeat');
eq(ctx.press_edge(false,true),false,'release does not fire');
eq(ctx.press_edge(false,false),false,'idle does not fire');
eq(ctx.countdown(.02,.05),0,'cooldown cannot go negative');
eq(ctx.countdown(8,0),8,'pause preserves cooldown');
eq(ctx.countdown(8,.05),7.95,'active countdown');
eq(ctx.hud_seconds(0),0,'ready');
eq(ctx.hud_seconds(.02),1,'last partial second remains unavailable');
eq(ctx.hud_seconds(7.95),8,'HUD rounds up');
for (const archer of [true,false]) for (const cause of ['MOD_FALLING','MOD_MELEE','MOD_EXPLOSIVE','MOD_SUICIDE']) {
  eq(ctx.ignores_fall(archer,cause),archer && cause === 'MOD_FALLING','class-specific damage '+cause);
}
const update = body('update');
assert(update.indexOf('s.tactical_down = tactical') < update.indexOf('why != ""'), 'menu still samples held buttons');
assert(update.indexOf('why != ""') < update.indexOf('s.hook_cd = countdown'), 'blocked state freezes cooldown');
assert(body('watch').includes('delete_axe( s )'), 'disconnected owner projectile cleanup');
assert(body('on_spawned').includes('delete_axe( old )'), 'reused player slot cleanup');
assert(body('cleanup').includes('self EnableOffhandWeapons();'),'cleanup hands offhands back'); assert(!body('cleanup').includes('"mage"'));
assert(body('playable_area_cb').includes('!self zm::in_kill_brush()'), 'death brushes stay lethal');
assert(body('playable_area_cb').includes('level.tod_archer_prev_oopa_cb'), 'chain existing area callback');
assert(body('grapple_step').includes('"obstructed"') && body('grapple_step').includes('"stalled"'), 'collision escape paths');
// The ONE permitted SetOrigin is floor_release()'s one-unit lift (stock's jump-pad idiom, _zm_jump_pad.gsc:484):
// a grounded player's scripted lift is discarded until the ground trace misses. Anything else is a teleport.
// The other permitted SetOrigin is the out-of-bounds RETURN to stock's last navmesh point (2026-09-26): a stranded
// Archer on the crown's bell (over the hall wall) is put back instead of killed; kill brushes stay lethal.
const srcNoRelease = src.replace(/self SetOrigin\( self\.origin \+ \( 0, 0, 1 \) \);/g, '')
                        .replace(/self SetOrigin\( self\.last_valid_position \+ \( 0, 0, 8 \) \);/g, '');
assert(!/PlayerLinkTo|SetOrigin/.test(srcNoRelease), 'no collision-bypassing player move');
assert(body('playable_area_cb').includes('!IS_TRUE( self.tod_grappling ) && !self zm::in_kill_brush() && isdefined( self.last_valid_position )') && body('playable_area_cb').includes('OOB_RETURN'), 'out-of-bounds return only when the rope is down, never in a kill brush, and logged');
assert(body('floor_release').includes('self SetOrigin( self.origin + ( 0, 0, 1 ) );'), 'floor_release is the one-unit stock lift');
assert(body('grapple_step').includes('self floor_release();') && body('grapple_step').indexOf('self floor_release();') < body('grapple_step').indexOf('self SetVelocity( nv );'), 'grounded lift steps off the floor before the velocity write');
assert(update.includes('tod_retriever::step( s, dt )'), 'native Retriever state is ticked');
assert(!src.includes('self try_axe()'), 'lethal input belongs to the native offhand');
checks += 11;
// THE SWING: momentum is kept, only rope-stretching speed is removed.
const near = (a,b,label) => { assert(Math.abs(a-b) < 1e-6, label+' '+a+' vs '+b); checks++; };
near(ctx.rope_next(1000,1200,.05), 970, 'rope never lengthens, then reels');
near(ctx.rope_next(1000,800,.05), 770, 'slack rope pulls taut at the player');
near(ctx.rope_next(10,5,.05), 0, 'rope floors at zero');
near(ctx.radial_next(0,1000,1000,.05,true), ctx.TOD_ARCHER_KICK, 'standing grapple starts at the kick');
near(ctx.radial_next(800,1000,1000,.05,false), 800+ctx.TOD_ARCHER_PULL_ACCEL*.05, 'pull accelerates, never snaps');
near(ctx.radial_next(-500,1000,970,.05,false), 600, 'rope forbids drifting past its length');
near(ctx.radial_next(5000,2000,2000,.05,false), ctx.TOD_ARCHER_SPEED, 'reel speed cap');
near(ctx.radial_next(1300,80,80,.05,false), 1300, 'NO ease-off near the anchor (2026-09-26): you fly past it');
near(ctx.tang_scale(500), 1, 'swing under cap untouched');
near(ctx.tang_scale(2200), ctx.TOD_ARCHER_TANG_MAX/2200, 'swing capped');
// THE STEER (2026-09-26, Pathfinder): the stick pushes AROUND the anchor, never along the rope.
const v3 = (a,b,c) => ({0:a,1:b,2:c});
Object.assign(ctx, {
  AnglesToForward: a => v3(Math.cos(a[1]*Math.PI/180), Math.sin(a[1]*Math.PI/180), 0),
  AnglesToRight:   a => v3(Math.sin(a[1]*Math.PI/180), -Math.cos(a[1]*Math.PI/180), 0),
  Length: v => Math.hypot(v[0],v[1],v[2]), VectorDot: (a,b) => a[0]*b[0]+a[1]*b[1]+a[2]*b[2],
});
// GSC vector arithmetic in JS: run steer_vec through a tiny rewrite (f * m[0] etc.)
vm.runInContext(body('steer_vec')
  .replace(/\( 0, 0, 0 \)/g, 'v3(0,0,0)').replace(/\( 0, yaw, 0 \)/g, 'v3(0,yaw,0)')
  .replace('f * m[ 0 ] + rt * m[ 1 ]', 'v3(f[0]*m[0]+rt[0]*m[1], f[1]*m[0]+rt[1]*m[1], 0)')
  .replace('wish * ( 1 / mag )', 'v3(wish[0]/mag, wish[1]/mag, wish[2]/mag)')
  .replace('wish - dir * VectorDot( wish, dir )', '(function(d){return v3(wish[0]-dir[0]*d, wish[1]-dir[1]*d, wish[2]-dir[2]*d)})(VectorDot( wish, dir ))')
  .replace('wish * ( TOD_ARCHER_STEER_ACCEL * dt )', '(function(k){return v3(wish[0]*k, wish[1]*k, wish[2]*k)})(TOD_ARCHER_STEER_ACCEL * dt)'), ctx);
ctx.v3 = v3;
{
  const up = v3(0,0,1), east = v3(1,0,0);
  const z = ctx.steer_vec(undefined, 0, up, .05); near(ctx.Length(z), 0, 'no stick = no steer');
  const dead = ctx.steer_vec(v3(0.1,0.1,0), 0, up, .05); near(ctx.Length(dead), 0, 'dead zone');
  const fwd = ctx.steer_vec(v3(1,0,0), 0, up, .05); near(fwd[0], ctx.TOD_ARCHER_STEER_ACCEL*.05, 'forward at yaw 0 pushes +x'); near(fwd[2], 0, 'never along a vertical rope');
  const along = ctx.steer_vec(v3(1,0,0), 0, east, .05); near(ctx.Length(along), 0, 'a push straight down the rope is removed');
  const diag = ctx.steer_vec(v3(1,1,0), 0, up, .05); near(ctx.Length(diag), ctx.TOD_ARCHER_STEER_ACCEL*.05, 'full deflection is normalized');
  const right = ctx.steer_vec(v3(0,1,0), 90, up, .05); near(right[0], ctx.TOD_ARCHER_STEER_ACCEL*.05, 'right of a north view is east');
}
const step = body('grapple_step');
assert(step.includes('steer_vec( m, self GetPlayerAngles()[ 1 ], dir, dt )') && step.includes('TOD_ARCHER_ARRIVE'), 'the stick steers the swing; no slowdown radius'); checks++;
assert(update.includes('jump_edge && IS_TRUE( self.tod_grappling )') && body('end_grapple').includes('reason == "jumped"'), 'jump lets go and keeps momentum'); checks++;
assert(step.includes('self GetVelocity()') && step.includes('VectorDot( v, dir )') && step.includes('tang + dir * r'), 'swing keeps tangential momentum');
assert(!/SetVelocity\( \( 0, 0,/.test(grab), 'attach must not zero the run');
assert(update.includes('end_grapple( why, why != "movement_owned" )'), 'a mantle never brakes');
for (const tag of ['GRAPPLE_TICK','GRAPPLE_STUCK','GRAPPLE_OBSTRUCTED','vel_in=','vel_out=','stuck_events=']) assert(src.includes(tag), 'log '+tag);
checks += 4;
// LANDING: armed at the grapple's end, fired on touch-down, read by the shared owners.
const upg = read(dir+'_tod_upgrades.gsc');
assert(body('update').includes('self land_step( s )'), 'landing is ticked');
assert(body('end_grapple').includes('s.land_pending_until'), 'grapple end arms the landing');
assert(body('cleanup').includes('self land_clear( s )'), 'class change clears the window');
assert(upg.includes('+ self archer_land_speed_bonus()') && /return m \* land;/.test(upg) && upg.includes('return land;'), 'speed + DR through apply_move_speed / dr_mult');
assert(/add_domain\( "distraction", "GRAPPLE", .*, 9, array\( "assault" \)/.test(upg), 'GRAPPLE has 9 levels');
for (const k of ['magsize','recoil','deadshot','headshot','bossdmg','march']) assert(!upg.includes('\n\tadd_domain( "'+k+'"'), k+' retired');   // 2026-09-26: HEADSHOT / GIANT SLAYER / FORCED MARCH cut (user)
{ assert(!/\n\tadd_domain\( "reserve",/.test(upg), 'Archer has no SCAVENGER (the parked card retired whole 2026-10-05, W2E: no class is dealt it)'); }
// THE RETRIEVER CARD (2026-09-26): the lethal is earned, 8 levels, no dark, id 57 on both sides.
assert(/\n\tadd_domain\( "retriever",\s+"HELL'S RETRIEVER", .*, 9, array\( "assault" \)/.test(upg), 'HELL\'S RETRIEVER card: 9 levels, Archer only');
assert(upg.includes('set_no_dark( "retriever" )'), 'Retriever has no dark card');
assert(read(dir+'_tod_upgrade_ui.gsc').includes('case "retriever":   return 57;'), 'Retriever id 57');
assert(/\[57\] = \{ name = "HELL'S RETRIEVER"/.test(read('ui/uieditor/menus/hud/tod_upgrade.lua')), 'Lua row 57');
assert(body('update').includes('self tod_retriever::tick( s, dt )'), 'the card grants the axe and refills throws');
checks += 12;
const main = read(dir+'_tod_main.gsc'), zone=read('zone_source/zm_tod2_cybercity.zone');
assert(main.includes('tod_archer::init();') && !main.includes('tod_distraction::init();'));
assert(zone.includes('scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_archer.gsc'));
assert(zone.includes('xmodel,tod_archer_retriever_world'));
assert(read(dir+'_tod_athlete.gsc').includes('IS_TRUE( self.tod_grappling )'));
assert(read(dir+'_tod_upgrades.gsc').includes('add_domain( "distraction", "GRAPPLE"'));
const hud=read('ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumLoadout.lua');
assert(hud.includes('name == "tod_archer_abil"') && hud.includes('if archerOn then return end') && !hud.includes('manaOn'), 'a class kit owns the offhand tiles (no retired mana path)');
// R5 (2026-10-04): the V1 owned-upgrades plate lists (and CoD.TodTextPlate) left; GRAPPLE (41) draws its
// layered card-v2 face (TodCardArt.lua), and none of its old one-face / rarity cards is zoned.
{
  const art = read('ui/uieditor/widgets/HUD/AetheriumWidgets/TodCardArt.lua'), zone = read('zone_source/zm_tod2_cybercity.zone');
  assert(/\[41\] = "i_tod_card2_art_grapple"/.test(art), 'GRAPPLE (41) draws its card-v2 art');
  assert(zone.includes('image,i_tod_card2_art_grapple'), 'grapple card-v2 art zoned');
  for (const r of ['regular', 'super', 'ultimate', 'dark']) assert(!new RegExp('^image,i_tod_card_grapple_' + r + '\\s*$', 'm').test(zone), 'old grapple card still zoned: grapple_' + r);
  assert(!/\[41\] = "distraction"/.test(read('ui/uieditor/menus/hud/tod_upgrade.lua')), 'no stale Monkey Bomb art on id 41');
}
checks += 8;
console.log(`ARCHER EQUIPMENT: ${checks} checks passed (GSC decisions + lifecycle/integration contracts; native playtest pending).`);
