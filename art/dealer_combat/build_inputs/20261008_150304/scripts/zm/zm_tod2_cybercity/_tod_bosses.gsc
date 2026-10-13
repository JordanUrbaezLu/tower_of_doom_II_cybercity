// =============================================================================
// _tod_bosses.gsc - THE SHARED ELITE INFRASTRUCTURE. Health bars live in
// _tod_elite_hp.gsc (docs/174) - every elite wears one.
//
// RETIRED WHOLE 2026-10-05 (W2E, user: "Just dont include assets not on this map
// in the build"): this file used to drive the two Map One tower bosses, the
// PANZER (Spiki mechz pack) and the ROGUE PROTECTOR (HB21 civil protector
// re-teamed axis), plus the finale's pressure lane, the sky-drop entrance and the
// stuck watch every Map One elite threaded. All of it went with the systems;
// the code and the packs are in archive/map1_carryover/. The live elites are the
// Mangler and the Doppelghast (_tod_cyber_elites, the crown hunters, the havens,
// the Battle Arena) and the Dealer (_tod_house); each spawns and paces itself.
//
// WHAT IS LEFT, and who calls it:
//   pick_spawn_point()      - a legal landing spot near an anchor (the
//                             Doppelghast's relocation; the arena's room box)
//   elites_over_roof() /    - the COMBINED elite roof, party-aware, +3 on
//   elite_roof_all()          rampage (_tod_cyber_elites::hold_reason)
//   grant_elite_reward()    - the killer's 500, the feed row, the perk bottle
//                             roll, the shield / DEMON SLAYER seams
//   boss_player_damage()    - the player-damage callback: the haven barrier and
//                             field, the arena's hit multiplier, the Dealer's
//                             swing (tod_keeper_dmg), the defensive domains and
//                             the dev demigod clamp
//   rampage_hp_mult()       - the one owner of TOD_RAMPAGE_HP_MULT
//   boss_pause_watch()      - the per-tick freeze for an elite that opts in
//   landing_kill_splash()   - the arrival shockwave helper (bosses immune)
//   dev_ai_*                - the [TOD_AI] actor diagnostics (dev only)
// =============================================================================

#using scripts\shared\ai\archetype_utility;
#using scripts\shared\flag_shared;
#using scripts\shared\spawner_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_powerups;   // specific_powerup_drop (the elite perk bottle)

#insert scripts\shared\shared.gsh;

#using scripts\zm\_zm;
#using scripts\zm\_zm_score;
#using scripts\zm\_zm_utility;
// get_zone_from_position — an elite must never be placed behind a closed door
// (user 2026-08-21: an elite spawned on the first set of stairs even though the
// door was not opened). See the ZONE GATE in pick_spawn_point.
#using scripts\zm\_zm_zonemgr;

#using scripts\zm\zm_zod_robot;   // landing_splash_immune (the stock companion pack; named by its installed zpkg)

#using scripts\zm\zm_tod2_cybercity\_tod_door_data;    // v18.76 — get_door_info (the door frontier; GENERATED leaf module, no cycle)
#using scripts\zm\zm_tod2_cybercity\_tod_reach;        // THE PURSUIT (docs/200) — pick_spawn_point refuses a spot that cannot walk to its anchor
#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;

// THE KILL-FEED LABEL (v17.47, 2026-09-04). The row grant_elite_reward sends
// (v17.37) was NEVER precached, so it reached the feed as an empty name. The kit
// precaches all fifteen of ITS labels in _zm_aetherium_hud.gsc; ours has to be
// precached HERE, in the module that sends it. And it MUST sit here, after ALL
// #using/#insert directives: between them it kills the compile with "No
// generated data" — live 2026-08-20. (KF_BOSS, the Panzer's team-wide jackpot
// row, retired with him 2026-10-05.)
#precache( "string", "ZM_AETHERIUM_KF_ELITE" );

// THE COMBINED ELITE ROOF, enforced by elites_over_roof() (the cyber-elite
// director's hold_reason reads it).
//
// PARTY-AWARE SINCE v18.1 — 5 / 7 / 9 / 11 (user 2026-09-06: "elites at once
// we can drop so 5 solo, 7 duo, 9 trio, 11 quads", answering a solo-vs-trio
// audit). It was FLAT 12 from v14.20, which made the roof the map's single
// worst solo penalty: a lone player could face all 12 at once, the same wall a
// quad splits four ways.
#define TOD_ELITE_ROOF_SOLO     5     // one player
#define TOD_ELITE_ROOF_PER      2     // per extra player: 5 / 7 / 9 / 11
// RAMPAGE (v18.74, user 2026-09-10: "Rampage increases elites at once by 3").
// Added by elite_roof_all() while the breaker is thrown: 8 / 10 / 12 / 14.
#define TOD_RAMPAGE_ELITE_ROOF_ADD 3
// RAMPAGE HP (v14.25, user: "all elites and bosses get 1.25x health on
// rampage"; v18.74, user 2026-09-10: "Elites panzer and zombies health
// increase by 20%" — 1.25 x 1.20 = 1.5). ONE constant, one owner:
// rampage_hp_mult(). Do not inline 1.5 anywhere. The HORDE's own rampage health
// lives in _tod_zombie_speed (TOD_RAMPAGE_ZHEALTH_MULT), not here.
// ⚠️ 2026-10-05 (W2E): its last consumers (the Map One boss_hp curve for the
// Panzer / Protector / Fury / hellhound and the sprinter promotion) retired
// whole. The live elites take their HP from tod_doppelghast::hunter_hp(), which
// carries only the horde's x1.2 - see LAND.md / docs/status_log.md.
#define TOD_RAMPAGE_HP_MULT      1.5

// --- spawn placement --------------------------------------------------------
#define TOD_BOSS_CLEARANCE       150   // min distance from every living boss
#define TOD_BOSS_ZONE_CHECKS     12    // max get_zone_from_position calls per spawn pick (each spawns a temp entity)
// v18.76 — THE DOOR FRONTIER (the v18.9 "boss behind an unbought door" finding,
// left out of that pass as its one regression risk; user 2026-09-10: fix it).
// Lap zone volumes overhang the next lap by 200 units, so the sealed flight
// above an unbought door reads as an ENABLED zone to get_zone_from_position
// and the zone gate in pick_spawn_point lets an elite land where nobody can
// reach it. The doors themselves are the authority: door n sits on the landing
// at lap n's floor (its generated org is 40 up from that floor), so any
// candidate whose feet are above the LOWEST unbought door's floor is behind
// it. The lift keeps that landing itself legal (navmesh points sit AT floor z;
// the first tread past the slab is 12 up).
#define TOD_BOSS_FRONTIER_DOOR_Z 40    // door org z above its landing floor (gen_tower_map: door centre height)
#define TOD_BOSS_FRONTIER_LIFT   4
#define TOD_BOSS_FRONTIER_LAPS   50    // enter_lap1..50, then enter_roof
// docs/160 — THE DESCENT. The party starts at the crown and buys the doors
// going DOWN, so the frontier is the other way up: the HIGHEST unbought door
// is the one the party has not passed yet, and everything BELOW its landing
// is behind it. door_frontier_z walks enter_roof, enter_lap50 .. enter_lap1
// and frontier_blocks rejects a candidate under the floor. With 1 the climb
// rule above is dead code; LOCKSTEP with DESCENT in gen_tower_map.js.
#define TOD_BOSS_DESCENT         1
#define TOD_BOSS_PLAYER_CLEAR    100   // min distance from every player

// --- rewards (v14.5, user 2026-08-30: "elites give 500 on kill. Only the
// person who kills gets the money. The payout is still effected by double
// points and bounty upgrade"): TOD_ELITE_PTS to the KILLER ONLY, scaled by
// double points + the BOUNTY domain; one shared number, one function
// (grant_elite_reward). LUCK is separate: last hit only (tod_luck::boss_kill,
// called by each elite's own death watch). ----------------------------------
#define TOD_ELITE_PTS            500
// v18.96 — THE PERK BOTTLE (user 2026-09-13: "elite kills have a 10% chance of
// dropping a perk bottle on death"). Every elite death that pays the killer
// rolls this on the corpse's spot; the drop is the map's own `tod_free_pap`
// powerup (the perk-bottle model that grants a random MAP-TRUTH perk, or max
// ammo + luck when every sellable perk is held), behind the same power gate
// every bottle drop in this map obeys.
#define TOD_ELITE_BOTTLE_PCT     10

#namespace tod_bosses;

function init()
{
	level endon( "end_game" );

	level flag::wait_till( "initial_blackscreen_passed" );
	wait 3;

	// The player-damage callback (see the function): the haven barrier and
	// field, the arena's hits, the Dealer's swing, the defensive domains, the
	// tower demigod clamp. Registered once, here.
	zm::register_player_damage_callback( &boss_player_damage );

	if ( IS_TRUE( level.tod_dev ) )
		level thread dev_ai_watch();
}

// Console-only diagnostics (2026-09-10: intermittent elite tracking stalls).
// Diagnostic readers only. All recorder writes use tod_ai_diag_* fields.
// Do not use CalcApproximatePathToPosition: it clears the actor's current path.
function dbg( msg )
{
	if ( IS_TRUE( level.tod_dev ) ) dev_ai_log( "EVENT " + msg );
}

function dev_ai_log( msg )
{
	// The native loader REQUIRES this block for PrintLn, even in a devmap.
	// Keep literal assembly outside it: mod devblock literals were blank in
	// the native console, while an already-built string is retained intact.
	line = "[TOD_AI] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function dev_ai_value( value )
{
	if ( !isdefined( value ) ) return "-";
	return "" + value;
}

function dev_ai_pos( org )
{
	if ( !isdefined( org ) ) return "-";
	return "(" + ( int( org[ 0 ] * 10 ) / 10.0 ) + "," + ( int( org[ 1 ] * 10 ) / 10.0 ) + "," + ( int( org[ 2 ] * 10 ) / 10.0 ) + ")";
}

function dev_ai_ent( ent )
{
	if ( !isdefined( ent ) ) return -1;
	return ent GetEntityNumber();
}

function dev_ai_age( stamp )
{
	if ( !isdefined( stamp ) ) return -1;
	return GetTime() - stamp;
}

function dev_ai_entities( ents )
{
	if ( !isdefined( ents ) ) return "-";
	result = "[";
	foreach ( ent in ents ) result += dev_ai_ent( ent ) + ",";
	return result + "]";
}

function dev_ai_kind( ai )
{
	if ( isdefined( ai.tod_boss_kind ) ) return ai.tod_boss_kind;
	return "ordinary";
}

function dev_ai_flags( ai )
{
	return " ignoreall=" + dev_ai_value( ai.ignoreall ) + " ignoreme=" + dev_ai_value( ai.ignoreme )
		+ " pacifist=" + dev_ai_value( ai.pacifist ) + " frozen=" + dev_ai_value( ai.tod_frozen )
		+ " ignore_flesh=" + dev_ai_value( ai.ignore_find_flesh )
		+ " dropping=" + dev_ai_value( ai.tod_dropping ) + " parked=" + dev_ai_value( ai.tod_bt_parked )
		+ " think=" + dev_ai_value( ai.zombie_think_done ) + " in_ground=" + dev_ai_value( ai.in_the_ground )
		+ " eslow=" + dev_ai_value( ai.tod_eslow_mult ) + " web=" + dev_ai_value( ai.b_widows_wine_slow )
		+ " cocoon=" + dev_ai_value( ai.b_widows_wine_cocoon );
}

function dev_ai_world()
{
	stock_pause = undefined;
	if ( level flag::exists( "world_is_paused" ) ) stock_pause = level flag::get( "world_is_paused" );
	return " round=" + dev_ai_value( level.round_number ) + " dev=" + dev_ai_value( level.tod_dev )
		+ " god=" + dev_ai_value( level.tod_god ) + " dev_doors=" + dev_ai_value( level.tod_dev_doors )
		+ " pause=" + dev_ai_value( level.tod_upgrade_pause )
		+ " stock_pause=" + dev_ai_value( stock_pause ) + " tp=" + dev_ai_value( level.tod_tp_stamp )
		+ " pause_on_ms=" + dev_ai_value( level.tod_ai_diag_pause_on ) + " pause_off_ms=" + dev_ai_value( level.tod_ai_diag_pause_off )
		+ " rampage=" + dev_ai_value( level.tod_rampage_on );
}

function dev_ai_player_flags( p )
{
	return " valid=" + zm_utility::is_player_valid( p ) + " targetable=" + zm_utility::is_player_valid( p, true )
		+ " notarget=" + p IsNoTarget() + " ignore=" + dev_ai_value( p.ignoreme )
		+ " ignore_count=" + dev_ai_value( p.ignorme_count ) + " blood=" + dev_ai_value( p.tod_in_blood )
		+ " ai_ignore_counter=" + dev_ai_value( p.ignore_counter )
		+ " state=" + dev_ai_value( p.sessionstate );
}

// Scan transitions at 500 ms; full context every 2 s. All species is explicit:
// the API's omitted species defaults to human, missing dogs and robots.
// Log ordinary actors too so native entity-number errors have a family and
// moving controls. The per-actor first-seen time disambiguates reused slots.
function dev_ai_watch()
{
	level endon( "end_game" );
	dev_ai_log( "START schema=2 build=20260910f scan_ms=500 detail_ms=2000 species=all" );
	previous = [];
	last_world = "";
	last_tick = GetTime();
	next_detail = 0;
	for ( ;; )
	{
		wait 0.5;
		if ( !IS_TRUE( level.tod_dev ) ) return;
		started = GetTime();
		detail = started >= next_detail;
		if ( detail ) next_detail = started + 2000;
		world_state = dev_ai_world();
		if ( detail || world_state != last_world ) dev_ai_log( "WORLD" + world_state );
		last_world = world_state;
		players = GetPlayers();
		foreach ( p in players )
		{
			if ( !isdefined( p ) || !isplayer( p ) ) continue;
			flags = dev_ai_player_flags( p );
			if ( !detail && isdefined( p.tod_ai_diag_flags ) && flags == p.tod_ai_diag_flags ) continue;
			p.tod_ai_diag_flags = flags;
			blood_left = undefined;
			if ( isdefined( p.zombie_vars ) ) blood_left = p.zombie_vars[ "zombie_powerup_zombie_blood_time" ];
			dev_ai_log( "PLAYER id=" + dev_ai_ent( p ) + " pos=" + dev_ai_pos( p.origin ) + flags
				+ " hp=" + p.health + " blood_left=" + dev_ai_value( blood_left )
				+ " lastnav=" + dev_ai_pos( p.last_valid_position )
				+ " mesh=" + dev_ai_pos( GetClosestPointOnNavMesh( p.origin, 64, 30 ) ) );
		}
		actors = GetAISpeciesArray( "all", "all" );
		current = [];
		seen = [];
		alive_count = 0;
		elite_count = 0;
		foreach ( ai in actors )
		{
			if ( !isdefined( ai ) || !isalive( ai ) ) continue;
			alive_count++;
			id = dev_ai_ent( ai );
			kind = dev_ai_kind( ai );
			elite = kind != "ordinary";
			if ( elite ) elite_count++;
			fresh = !isdefined( ai.tod_ai_diag_born );
			if ( fresh )
			{
				ai.tod_ai_diag_born = started;
				ai.tod_ai_diag_moved = started;
				ai.tod_ai_diag_anchor = ai.origin;
				dev_ai_log( "APPEAR id=" + id + " born_ms=" + started + " kind=" + kind
					+ " pos=" + dev_ai_pos( ai.origin ) + " species=" + dev_ai_value( ai.species )
					+ " archetype=" + dev_ai_value( ai.archetype ) + " team=" + dev_ai_value( ai.team ) );
			}
			// Accumulated displacement, so slow movement is not mislabeled stationary.
			if ( DistanceSquared( ai.origin, ai.tod_ai_diag_anchor ) >= 64 )
			{
				ai.tod_ai_diag_moved = started;
				ai.tod_ai_diag_anchor = ai.origin;
			}
			stamp = spawnstruct();
			stamp.id = id;
			stamp.born = ai.tod_ai_diag_born;
			stamp.ent = ai;
			stamp.kind = kind;
			stamp.org = ai.origin;
			current[ current.size ] = stamp;
			seen[ id ] = stamp.born;
			has_path = ai HasPath();
			flags = " kind=" + kind + " path=" + has_path + " fav=" + dev_ai_ent( ai.favoriteenemy )
				+ " enemy=" + dev_ai_ent( ai.enemy ) + dev_ai_flags( ai );
			if ( elite ) flags += " rate=" + ai GetEntityAnimRate() + " script=" + dev_ai_value( ai.scriptstate );
			changed = !isdefined( ai.tod_ai_diag_flags ) || flags != ai.tod_ai_diag_flags;
			ai.tod_ai_diag_flags = flags;
			if ( !detail && !fresh && !changed ) continue;
			tag = "ACTOR id=" + id + " born_ms=" + stamp.born;
			if ( elite ) tag = "ELITE id=" + id + " born_ms=" + stamp.born;
			dev_ai_log( tag + " pos=" + dev_ai_pos( ai.origin ) + " still_ms=" + ( started - ai.tod_ai_diag_moved )
				+ " hp=" + ai.health + flags );
			if ( elite ) dev_ai_detail( ai, players, has_path, detail );
		}
		foreach ( old in previous )
		{
			if ( isdefined( seen[ old.id ] ) && seen[ old.id ] == old.born ) continue;
			reason = "removed";
			if ( isdefined( old.ent ) && !isalive( old.ent ) ) reason = "dead";
			if ( isdefined( seen[ old.id ] ) ) reason = "slot_reused";
			dev_ai_log( "GONE id=" + old.id + " born_ms=" + old.born + " kind=" + old.kind
				+ " reason=" + reason + " lastpos=" + dev_ai_pos( old.org ) );
		}
		previous = current;
		elapsed = GetTime() - started;
		if ( detail || elapsed > 100 || started - last_tick > 1000 )
			dev_ai_log( "TICK gap_ms=" + ( started - last_tick ) + " cost_ms=" + elapsed
				+ " actors=" + actors.size + " live=" + alive_count + " elites=" + elite_count
				+ " ai_limit=" + dev_ai_value( level.zombie_ai_limit ) + " actor_limit=" + dev_ai_value( level.zombie_actor_limit ) );
		last_tick = started;
	}
}

function dev_ai_detail( ai, players, has_path, routes )
{
	id = " id=" + dev_ai_ent( ai ) + " born_ms=" + ai.tod_ai_diag_born;
	mesh = GetClosestPointOnNavMesh( ai.origin, 64, 30 );
	inside = undefined;
	if ( isdefined( level.tod_trial_box ) ) inside = box_contains( ai.origin, level.tod_trial_box );
	path_length = undefined;
	if ( has_path ) path_length = ai GetPathLength();
	dev_ai_log( "NAV" + id + " mesh=" + dev_ai_pos( mesh ) + " inside=" + dev_ai_value( inside )
		+ " path_mode=" + ai GetPathMode()
		+ " goal=" + dev_ai_pos( ai.goalpos ) + " radius=" + dev_ai_value( ai.goalradius )
		+ " path_start=" + dev_ai_pos( ai.pathstartpos ) + " path_goal=" + dev_ai_pos( ai.pathgoalpos )
		+ " path_length=" + dev_ai_value( path_length ) + " path_wait=" + dev_ai_value( ai.pathwaittime )
		+ " last_path=" + dev_ai_value( ai.lastpathtime ) );
	dev_ai_log( "MOTION" + id + " vel=" + dev_ai_pos( ai GetVelocity() ) + " onground=" + ai IsOnGround()
		+ " linked=" + dev_ai_ent( ai GetLinkedEnt() ) + " move_type=" + dev_ai_value( ai.movementtype )
		+ " last_script=" + dev_ai_value( ai.lastscriptstate ) + " state_reason=" + dev_ai_value( ai.statechangereason )
		+ " anim=" + dev_ai_value( ai.animname ) + " script_anim=" + dev_ai_value( ai.script_animname )
		+ " anim_scale=" + dev_ai_value( ai.animtranslationscale ) + " gunblocked=" + dev_ai_value( ai.gunblockedbywall ) );
	dev_ai_log( "STATE" + id + " asm_status=" + ai ASMGetStatus()
		+ " pause_write_ms=" + dev_ai_value( ai.tod_ai_diag_pause_write )
		+ " pause_pending=" + dev_ai_value( ai.tod_elite_pause_pending ) + " pause_resume_ms=" + dev_ai_value( ai.tod_ai_diag_pause_resume )
		+ " base_rate=" + dev_ai_value( ai.tod_elite_base_rate )
		+ " drop_age=" + dev_ai_age( ai.tod_drop_stamp ) + " eslow_age=" + dev_ai_age( ai.tod_eslow_until )
		+ " hit_age=" + dev_ai_age( ai.tod_actor_cb_ms ) + " dealt_age=" + dev_ai_age( ai.tod_dealt_ms )
		+ " flame=" + dev_ai_value( ai.isShootingFlame ) + " octobomb=" + isdefined( ai.destroy_octobomb )
		+ " ignored_players=" + dev_ai_entities( ai.ignore_player ) + " travel=" + dev_ai_value( ai.isTraveling )
		+ " pain_block=" + dev_ai_value( ai.blockingPain ) + " furious=" + dev_ai_value( ai.isFurious )
		+ " dog_seen=" + dev_ai_value( ai.hasSeenFavoriteEnemy ) + " dog_last=" + dev_ai_pos( ai.lastTargetPosition )
		+ " target_override=" + isdefined( ai.no_target_override ) + " goal_override=" + isdefined( ai.enemy_location_override_func ) );
	// Path existence and line of sight are different questions. Test both against
	// EVERY player, including ignored/downed players; their eligibility is above.
	// Never call setters or path recalculation. Expensive probes only on heartbeat.
	if ( !routes ) return;
	foreach ( p in players )
	{
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) ) continue;
		// Native failures between PROBE and ROUTE may belong to this diagnostic
		// query. Keep them separate from errors raised by the live goal driver.
		dev_ai_log( "PROBE" + id + " player=" + dev_ai_ent( p ) );
		pmesh = GetClosestPointOnNavMesh( p.origin, 64, 30 );
		raw_path = ai CanPath( ai.origin, p.origin );
		mesh_path = undefined;
		if ( isdefined( mesh ) && isdefined( pmesh ) ) mesh_path = ai CanPath( mesh, pmesh );
		trace = BulletTrace( ai.origin + ( 0, 0, 40 ), p.origin + ( 0, 0, 40 ), false, ai );
		dev_ai_log( "ROUTE" + id + " player=" + dev_ai_ent( p ) + " distance=" + int( Distance( ai.origin, p.origin ) )
			+ " dz=" + int( p.origin[ 2 ] - ai.origin[ 2 ] ) + " raw=" + raw_path + " projected=" + dev_ai_value( mesh_path )
			+ " see=" + ai CanSee( p ) + " ray=" + trace[ "fraction" ] + " hit=" + dev_ai_pos( trace[ "position" ] ) );
	}
}

// THE COMBINED ELITE ROOF's live count (v14.20, cut to the live elites 2026-10-05).
// Until W2E this summed the Panzer, the Protectors, the Reavers and the hounds as
// well; all four directors retired whole, so the round elites (the Doppelghast and
// the Mangler, _tod_cyber_elites) are the whole sum. Counted live off the AI list:
// a stored counter could leak on a pack-side actor Delete and pin the roof.
function elites_all_alive()
{
	cyber = 0;
	foreach ( a in GetAISpeciesArray( "all", "all" ) )
		if ( isdefined( a ) && isalive( a ) && ( IS_TRUE( a.tod_doppelghast ) || IS_TRUE( a.tod_mangler ) ) )
			cyber++;
	return cyber;
}

// TRUE while the combined roof is full (the finale's exemption retired with it, 2026-10-05).
function elites_over_roof()
{
	return ( elites_all_alive() >= elite_roof_all() );   // v18.1 — party-aware; ONE owner, read it, never the define
}

// PUBLIC — the combined roof's value for THIS party size, and since v18.1 the
// single owner of it: elites_over_roof() above calls this rather than reading
// the define, so the two can never disagree. (The hound director that also read
// it retired whole 2026-10-05.)
function elite_roof_all()
{
	np = GetPlayers().size;
	if ( np < 1 )
		np = 1;
	roof = TOD_ELITE_ROOF_SOLO + ( np - 1 ) * TOD_ELITE_ROOF_PER;
	if ( IS_TRUE( level.tod_rampage_on ) )
		roof = roof + TOD_RAMPAGE_ELITE_ROOF_ADD;   // v18.74 — hard mode's own roof
	return roof;
}

// ---------------------------------------------------------------------------
// Spawn placement — anchored to a living player, navmesh-scattered, clear of
// players + living bosses. (The finale's far-anchor seam retired 2026-10-05.)
// ---------------------------------------------------------------------------

function pick_spawn_point( anchor )
{
	// Living bosses to keep clear of.
	bosses = [];
	a_ai = GetAISpeciesArray( "all" );
	for ( i = 0; i < a_ai.size; i++ )
	{
		ai = a_ai[ i ];
		if ( !isdefined( ai ) || !isalive( ai ) )
			continue;
		if ( IS_TRUE( ai.is_boss ) || IS_TRUE( ai.acc_is_boss ) || IS_TRUE( ai.acc_is_mini_boss ) )
			bosses[ bosses.size ] = ai;
	}
	players = GetPlayers();
	frontier = door_frontier_z();   // v18.76 — once per pick; undefined off the tower
	// THE BATTLE ARENA's room (level.tod_trial_box, _tod_arena) sits at ground level,
	// BELOW every unbought tower door, so the tower's frontier rejected every
	// candidate in it and a relocated elite fell back onto the anchor player
	// (2026-09-29). The room's own box already confines the pick below.
	if ( isdefined( level.tod_trial_box ) )
		frontier = undefined;

	// Two passes (v9.19): 400u, then 800u. Anchors are PLAYER positions now,
	// and on a narrow flight — every near candidate behind a closed door or
	// inside the player/boss clearance — the old single pass fell straight
	// through to "spawn on the player". The wider pass reaches the flight
	// below/above first.
	for ( pass = 0; pass < 2; pass++ )
	{
		radius = ( ( pass == 0 ) ? 400 : 800 );
		queryResult = PositionQuery_Source_Navigation( anchor, 0, radius, 40, 32 );
		if ( !isdefined( queryResult ) || queryResult.data.size == 0 )
			continue;

		clear = [];
		checks = 0;
		for ( i = 0; i < queryResult.data.size; i++ )
		{
			p = queryResult.data[ i ].origin;
			ok = true;
			// THE BATTLE ARENA: while a fight runs (_tod_arena sets
			// level.tod_trial_box to the arena room) nothing may land outside the
			// room — a boss placed off the detached room is stranded, can never
			// reach the party, and holds a roof slot for the whole fight.
			if ( isdefined( level.tod_trial_box ) && !( box_contains( p, level.tod_trial_box ) ) )
				ok = false;
			// THE PURSUIT (docs/200, 2026-10-02): never a spot that cannot WALK to
			// the anchor — below a drop the anchor stands above, across the island,
			// out of the arena. Every elite spawn AND every elite relocation comes
			// through here (the Doppelghast's and the Mangler's reloc_point too), so
			// a stuck elite can no longer be "rescued" onto another catch deck.
			if ( ok && !( tod_reach::can_reach( p, anchor ) ) )
				ok = false;
			for ( j = 0; j < bosses.size; j++ )
			{
				if ( DistanceSquared( p, bosses[ j ].origin ) < TOD_BOSS_CLEARANCE * TOD_BOSS_CLEARANCE )
				{
					ok = false;
					break;
				}
			}
			if ( ok )
			{
				for ( j = 0; j < players.size; j++ )
				{
					if ( isdefined( players[ j ] ) &&
					     DistanceSquared( p, players[ j ].origin ) < TOD_BOSS_PLAYER_CLEAR * TOD_BOSS_PLAYER_CLEAR )
					{
						ok = false;
						break;
					}
				}
			}
			// v18.76 — THE DOOR FRONTIER (see the define): above the lowest
			// unbought door is behind it, whatever the overhanging zone says
			// (docs/160: BELOW the highest unbought door under the descent).
			if ( ok && isdefined( frontier ) && frontier_blocks( p[ 2 ], frontier ) )
				ok = false;
			// ZONE GATE (user 2026-08-21: an elite spawned on the first set of
			// stairs even though the door was not opened). PositionQuery_Source_Navigation
			// searches a RADIUS and DisconnectPaths does NOT delete navmesh
			// polys — it only blocks pathing THROUGH the slab — so the query
			// happily returns points behind a closed door. Reject any candidate
			// that is not inside a currently ENABLED zone (ignore_enabled_check
			// = false). Capped at TOD_BOSS_ZONE_CHECKS per pass because each call
			// spawns (and deletes) a temp script_origin.
			if ( ok && checks < TOD_BOSS_ZONE_CHECKS )
			{
				checks++;
				zn = zm_zonemgr::get_zone_from_position( p, false );
				if ( !isdefined( zn ) )
					ok = false;
			}
			else if ( ok )
				ok = false;   // out of budget — do not risk an unvetted point

			if ( ok )
				clear[ clear.size ] = p;
		}

		if ( clear.size > 0 )
			return clear[ RandomInt( clear.size ) ];
	}

	// Nothing vetted in either pass: fall back to the ANCHOR itself rather
	// than an unvetted query point — it is a living player's position, a spot
	// we already trust to be on the mesh and inside an enabled zone.
	return anchor;
}

// -> is org strictly inside the axis-aligned box b (fields x1/x2, y1/y2, z1/z2)?
// The Battle Arena's room box (_tod_arena::arena_box, published as
// level.tod_trial_box while a fight runs). Strict comparisons: a point exactly
// on a face counts as outside.
function box_contains( org, b )
{
	return ( org[ 0 ] > b.x1 && org[ 0 ] < b.x2 && org[ 1 ] > b.y1 && org[ 1 ] < b.y2 && org[ 2 ] > b.z1 && org[ 2 ] < b.z2 );
}

// v18.76 — the z above which a candidate is behind an unbought door, or
// undefined when there is no frontier to enforce (every door bought, or
// a flag stock has not initialised yet -- door_init flag::init's them, and an
// unknown flag is treated as "no frontier", never as "sealed": a missing
// reading must not empty the spawn pick). Walks the lap doors bottom-up and
// stops at the first shut one, so it spawns at most ONE door-info struct.
function door_frontier_z()
{
	if ( TOD_BOSS_DESCENT )
	{
		// docs/160: top-down — the first SHUT door from the crown is the one
		// the party has not passed; its landing floor (minus the lift, so
		// the landing itself stays legal) is the floor of the legal world.
		for ( n = TOD_BOSS_FRONTIER_LAPS + 1; n >= 1; n-- )
		{
			flag = ( ( n <= TOD_BOSS_FRONTIER_LAPS ) ? ( "enter_lap" + n ) : "enter_roof" );
			if ( !( level flag::exists( flag ) ) )
				return undefined;
			if ( level flag::get( flag ) )
				continue;
			info = tod_door_data::get_door_info( flag );
			if ( !isdefined( info ) || !isdefined( info.org ) )
				return undefined;
			return info.org[ 2 ] - TOD_BOSS_FRONTIER_DOOR_Z - TOD_BOSS_FRONTIER_LIFT;
		}
		return undefined;
	}
	for ( n = 1; n <= TOD_BOSS_FRONTIER_LAPS + 1; n++ )
	{
		flag = ( ( n <= TOD_BOSS_FRONTIER_LAPS ) ? ( "enter_lap" + n ) : "enter_roof" );
		if ( !( level flag::exists( flag ) ) )
			return undefined;
		if ( level flag::get( flag ) )
			continue;
		info = tod_door_data::get_door_info( flag );
		if ( !isdefined( info ) || !isdefined( info.org ) )
			return undefined;
		return info.org[ 2 ] - TOD_BOSS_FRONTIER_DOOR_Z + TOD_BOSS_FRONTIER_LIFT;
	}
	return undefined;
}

// -> is a candidate at this z on the wrong side of the frontier?
function frontier_blocks( z, frontier )
{
	if ( TOD_BOSS_DESCENT )
		return ( z < frontier );
	return ( z > frontier );
}

// PUBLIC — RAMPAGE INDUCER (v14.25, user 2026-08-30: "all elites and bosses get
// 1.25x health on rampage"; x1.5 since v18.74). The one owner of
// TOD_RAMPAGE_HP_MULT. Its consumers were the Map One boss_hp curve (Panzer,
// Protector, Fury, hellhound) and the sprinter promotion, all retired whole
// 2026-10-05; the live elites' HP comes from tod_doppelghast::hunter_hp().
function rampage_hp_mult()
{
	if ( IS_TRUE( level.tod_rampage_on ) )
		return TOD_RAMPAGE_HP_MULT;
	return 1.0;
}

// PUBLIC — landing kill-splash: every axis AI in radius EXCEPT bosses dies with a
// ragdoll fling (the pack's splash killed the landing boss itself — the live
// spawn-die-reward loop; and a sibling boss on multi-boss rounds). KEPT as the
// shared arrival helper when the drop-in entrance that called it retired with
// the Panzer and the Rogue Protector (2026-10-05); tools/test_landing_immunity.js
// pins its immunity rules against the stock companion's own landing loop.
function landing_kill_splash( v_origin, e_boss )
{
	level endon( "end_game" );
	n_radius = 350;
	a_ai = GetAITeamArray( "axis" );
	for ( i = 0; i < a_ai.size; i++ )
	{
		ai_zombie = a_ai[ i ];
		if ( !isdefined( ai_zombie ) || !isalive( ai_zombie ) )
			continue;
		if ( isdefined( e_boss ) && ai_zombie == e_boss )
			continue;
		if ( zm_zod_robot::landing_splash_immune( ai_zombie ) )
			continue;
		if ( DistanceSquared( ai_zombie.origin, v_origin ) > n_radius * n_radius )
			continue;

		v_fling = ai_zombie.origin - v_origin;
		v_fling = v_fling + ( 0, 0, 15 );
		v_fling = VectorNormalize( v_fling );
		v_fling = ( v_fling[ 0 ], v_fling[ 1 ], abs( v_fling[ 2 ] ) );
		v_fling = VectorScale( v_fling, 60 );

		ai_zombie DoDamage( ai_zombie.health + 10000, ai_zombie.origin );
		ai_zombie StartRagdoll();
		ai_zombie LaunchRagdoll( v_fling );
	}
}

// ---------------------------------------------------------------------------
// Shared: pause watch, damage plumbing, rewards
// ---------------------------------------------------------------------------

// 2026-10-05: every elite that threaded this (the Panzer, the Rogue Protector,
// the Apothicon Fury, the hellhound) retired whole; the Mangler, the Doppelghast
// and the Dealer run their own freeze in their chase loops. KEPT (the brief's
// shared-infrastructure list, gated by tools/test_elite_pause_restore.js) for
// any elite that opts in; the Fury notes below are why the freeze is per tick.
//
// The upgrade-choice pause freezes all axis AI (set_world_pause: ignoreall +
// anim rate 0.05) — but it only enumerates AI alive AT pause time, and rate
// restore is left to the zombie sweep, which skips bosses by design. This
// watcher is the boss-side symmetric half: it APPLIES the freeze too (covers
// a boss that finished spawning mid-pause) and restores on the unpause edge.
//
// THE FREEZE IS RE-ASSERTED EVERY TICK, NOT STAMPED AT THE EDGE (v17.94, user
// 2026-09-05, the first real Warden King run: "the apothican furys didnt
// freeze during the dark upgrades. Meaning a player could just die"). The
// edge stamp was correct for an actor whose only rate writer is this file;
// the Apothicon Fury is not one. Its archetype writes the rate ITSELF on
// every teleport/bamf/traversal terminate (archetype_apothicon_fury.gsc:
// mocompApothiconFuryTeleportTerminate, apothiconBamfIn — both
// ASMSetAnimationRate( 1 )), so one bamf in flight when the pause landed put
// it back to full speed for the rest of the freeze, with was_paused already
// true and nothing here ever writing again. Now every tick under the pause
// writes ignoreall + 0.05, so the longest a re-stamp can survive is 0.25 s.
//
// AND A FURY IS PARKED AT ITS TREE'S IDLE BRANCH (tod_bt_idle_on_pause, set by
// _tod_reaver::spawn_reaver). Rate 0.05 slows a behaviour, it does not stop
// the tree CHOOSING one: apothiconCanBamf/apothiconShouldMeleeCondition are
// evaluated every frame regardless of rate, a bamf is a ForceTeleport that
// needs no animation time, and ignoreall only stops zombieTargetService
// from picking a NEW enemy (zombie.gsc:443) — the one it already had stays in
// .enemy, which is all the melee and bamf conditions read. The one switch
// that stops the WHOLE tree is the root's own spawn gate: idlespawnbehavior
// runs a looping idle@zombie while zombieIsThinkDone is false, above every
// combat branch (zm_genesis_apothicon_fury.ai_bt:135-152; _zm_behavior.gsc
// :1138 reads zombie_think_done) — the exact mechanism that made a parked
// riser a statue (memory parked-riser-idle-behavior; a bug there, the lever
// here). So the park writes zombie_think_done = false, the un-park writes it
// back to 1, and _tod_reaver::reaver_tune's own delayed write of 1 defers to
// the park (a Fury whose meteor was in flight when the pause began would
// otherwise un-park itself one second later). The Fury's damage callback
// also reads this field and returns 0 while it is false — which under the
// pause is what upgrade_damage_cb returns anyway. Opt-in per elite ON
// PURPOSE: the Panzer, the Protector and the hound run trees this file has
// not read for that gate, and all three have frozen correctly in every played
// pause since August; nothing changes for them beyond the per-tick re-assert.
function boss_pause_watch( base_rate )   // self = the boss
{
	self endon( "death" );
	level endon( "end_game" );

	// v17.84 — THE ONE STAMP OF AN ELITE'S TRUE ANIMATION RATE. Every elite
	// already threads this watcher with its own rate (hound/Reaver 1.0,
	// TOD_PANZER_ANIM_RATE, TOD_RP_ANIM_RATE), so recording it here is the only
	// way tod_zombie_speed::slow_elite's restore can never disagree with this
	// watcher's restore. NOT .tod_base_rate: that field also picks a sky-drop
	// relocation over a ground tell (tod_boss_stuck_watch above), and a hound or
	// a Reaver must not acquire an entrance by becoming slowable.
	self.tod_elite_base_rate = base_rate;

	was_paused = false;
	for ( ;; )
	{
		wait 0.25;
		if ( !isdefined( self ) || !isalive( self ) )
			return;
		if ( IS_TRUE( self.tod_dropping ) )
			continue;   // mid-entrance: drop_in owns ignoreall + the anim rate,
			            // and it re-reads tod_upgrade_pause itself on reveal. An
			            // unpause edge landing inside the 2s fall would otherwise
			            // clear ignoreall and restore the rate on a Ghosted,
			            // undamageable boss.
		now = IS_TRUE( level.tod_upgrade_pause );
		if ( now )
		{
			// every tick, not the edge — see the header (v17.94)
			self.ignoreall = true;
			self ASMSetAnimationRate( 0.05 );
			if ( IS_TRUE( self.tod_bt_idle_on_pause ) && !IS_TRUE( self.tod_bt_parked ) )
			{
				self.tod_bt_parked = true;
				self.zombie_think_done = false;
			}
		}
		else if ( was_paused || IS_TRUE( self.tod_elite_pause_pending ) )
		{
			self.ignoreall = false;
			// The freeze writer owns this latch; a sub-tick pause still needs
			// its rate restored. Keep an unexpired elite slow across the pause.
			self.tod_elite_pause_pending = undefined;
			resume_rate = base_rate;
			if ( isdefined( self.tod_eslow_until ) && isdefined( self.tod_eslow_mult )
			  && GetTime() < self.tod_eslow_until )
				resume_rate *= self.tod_eslow_mult;
			// THE HAVEN'S FIELD (docs/202): an elite paused inside a safe-zone dome
			// comes back at the field's slow. A plain field read (never an import).
			if ( isdefined( self.tod_safe_mult ) )
				resume_rate *= self.tod_safe_mult;
			self ASMSetAnimationRate( resume_rate );
			if ( IS_TRUE( level.tod_dev ) )
			{
				self.tod_ai_diag_pause_resume = GetTime();
				dbg( "PAUSE_RESTORE id=" + dev_ai_ent( self ) + " rate=" + resume_rate + " missed_edge=" + !was_paused );
			}
			if ( IS_TRUE( self.tod_bt_parked ) )
			{
				self.tod_bt_parked = undefined;
				self.zombie_think_done = 1;
			}
		}
		was_paused = now;
	}
}

// Player-damage callback: the haven barrier and field, the Battle Arena's hit
// multiplier, the Dealer's swing (tod_keeper_dmg), the three defensive domains
// and the tower demigod clamp. Return -1 = no opinion (the chain contract).
// (The Rogue Protector's bullet/rocket lanes, the Panzer's electroball lane, the
// hellhound bite cut and the two boss sight shields retired whole 2026-10-05.)
function boss_player_damage( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, psOffsetTime )
{
	if ( !isdefined( iDamage ) || iDamage <= 0 )
		return -1;
	// LAST STAND IS DELIBERATELY OUT OF SCOPE HERE, AND THE OMITTED THIRD ARGUMENT
	// IS WHAT PUTS IT THERE. zm_utility::is_player_valid( player,
	// checkIgnoreMeFlag, ignore_laststand_players ) returns FALSE for a crawler
	// when the third is absent, so this bails on line two for a downed player and
	// every lane below is skipped.
	//
	// THAT IS CORRECT, AND IT WAS BRIEFLY "FIXED" ON 2026-09-07 BEFORE THE READ
	// WAS FINISHED. The reasoning was that a downed player must be taking raw,
	// uncapped boss damage with no DR and no through-wall shield, which would
	// make the ten-second solo self-revive unsurvivable next to a Panzer. Every
	// step of that is true except the premise: stock zeroes the damage outright,
	// AFTER running this callback chain and BEFORE anything can be applied —
	// _zm.gsc:5136-5140, "Sledgehammer fix for Issue 43492. This should stop the
	// player from taking any damage while in laststand", a bare
	//     if ( self laststand::player_is_in_laststand() ) return 0;
	// sitting 26 lines below check_player_damage_callbacks. A downed player in
	// this game takes NO damage from anything. Nothing below this line could ever
	// have reached a crawler, so there was never a gap to close.
	//
	// (Passing the argument would also have let a boss swinging at a crawler stamp
	// itself "engaging" for the Map One stuck watch; that watch retired 2026-10-05.)
	//
	// THE WRONG LESSON WAS DRAWN FROM THE RIGHT SEARCH: Callback_PlayerDamage
	// (_zm.gsc:1415-1567) really does contain no last-stand early-out, and that
	// was read as proof there is none. The zero lives in a DIFFERENT function.
	// If you are about to change this line, open _zm.gsc:5136 first.
	if ( !zm_utility::is_player_valid( self ) )
		return -1;

	// AN ELITE THAT IS HITTING SOMEBODY IS ENGAGING: stamped for the [TOD_AI]
	// diagnostics' dealt_age (the stuck watch that also read it retired with the
	// Map One elites, 2026-10-05). Cheapest possible stamp on a path that already
	// runs for every hit a boss lands.
	if ( isdefined( eAttacker ) && isdefined( eAttacker.tod_boss_kind ) )
		eAttacker.tod_dealt_ms = GetTime();

	// THE HAVEN'S BARRIER (docs/202 v4, user 2026-10-03: "bullets cannot go in or outside the
	// dome. Until its a safe zone"): an enemy on the other side of a corrupted field's barrier
	// hurts nobody. The barrier's brushes already stop shots and the elites' own line checks;
	// this catches a swing over the rim and splash. Guarded pointer (_tod_haven owns the field;
	// never imported here); a player is never the attacker here (no friendly fire).
	if ( isdefined( level.tod_haven_barrier_fn ) && isdefined( eAttacker ) && !isplayer( eAttacker ) && [[ level.tod_haven_barrier_fn ]]( eAttacker, self ) )
		return 0;

	final = iDamage;
	touched = false;

	// THE BATTLE ARENA (docs/185): "stronger hits" per arena level. Set by
	// _tod_arena only while a fight runs; before the defensive domains so they
	// compose with it instead of being partly eaten by an int() floor after them.
	if ( isdefined( level.tod_arena_dmg_mult ) && isdefined( eAttacker ) && !isplayer( eAttacker ) )
	{
		final = int( final * level.tod_arena_dmg_mult );
		if ( final < 1 ) final = 1;
		touched = true;
	}

	// THE DEALER's swing (docs/199): _tod_dealer_finale stamps tod_keeper_dmg
	// (TOD_DEALER_MELEE_MULT) on him at spawn. The field kept the Keeper's name
	// when the Keeper and his soul lines retired whole (2026-10-05); any
	// non-player melee attacker carrying it hits this much harder. Ranged attacks
	// have their own tuned damage; do not multiply them by the swing bonus. Same place as the
	// arena lane, for the same reason.
	if ( isdefined( eAttacker ) && !isplayer( eAttacker ) && isdefined( eAttacker.tod_keeper_dmg ) && isdefined( sMeansOfDeath ) && sMeansOfDeath == "MOD_MELEE" )
	{
		final = int( final * eAttacker.tod_keeper_dmg );
		if ( final < 1 ) final = 1;
		touched = true;
	}

	// DMG REDUCTION domain (the shared upgrade, replaced HEALTH 2026-08-20):
	// v16 ladder — 6/11/15/18/20% cumulative at Lv1..Lv5 (was a flat 5%/Lv to
	// -25%).
	//
	// The number is NOT written here any more. It used to be a bare
	// `1.0 - 0.05 * dr_lvl` literal duplicated across two lanes, and the comment
	// on this one still claimed "-4%" long after the retune — which is exactly
	// what a second copy of a constant does. tod_upgrades::dr_mult() is the one
	// owner now; it returns 1.0 for an unowned domain, so the > 0 guard moved
	// inside it.
	dr = tod_upgrades::dr_mult( self );
	// THE HAVEN'S FIELD (docs/202, user 2026-10-02: "you'll take ... 33% less
	// damage"): a player inside a safe-zone dome takes TOD_HAVEN_DR of ENEMY
	// damage — gated on an attacker that is not a player (players cannot hurt
	// each other here, so that excludes self-damage) and never a fall. Guarded
	// pointer (_tod_haven owns the field; never imported here).
	haven_dr = 1.0;
	if ( isdefined( level.tod_safezone_dr ) && isdefined( eAttacker ) && !isplayer( eAttacker ) && sMeansOfDeath !== "MOD_FALLING" )
		haven_dr = [[ level.tod_safezone_dr ]]( self );
	dr = dr * haven_dr;
	if ( dr < 1.0 )
	{
		reduced = int( final * dr );
		if ( reduced < 1 )
			reduced = 1;
		// the STATS line's tally: what the haven's field alone took off this hit
		if ( haven_dr < 1.0 && isdefined( level.tod_haven_note_fn ) )
			[[ level.tod_haven_note_fn ]]( int( final * ( dr / haven_dr ) ) - reduced );
		if ( reduced != final )
		{
			final = reduced;
			touched = true;
		}
	}

	// SPRINT ARMOR (domain 32, session f2e3ffc8 2026-08-23): -5%/Lv while the
	// player is actually sprinting THIS INSTANT. Multiplies AFTER the DR domain,
	// so the two stack multiplicatively rather than summing to a bigger flat cut
	// (tod_upgrades::sprint_armor_mult returns 1.0 when not sprinting, when the
	// domain is unowned, or for a non-player, and floors at 0.05).
	sa = tod_upgrades::sprint_armor_mult( self );
	if ( sa < 1.0 )
	{
		reduced = int( final * sa );
		if ( reduced < 1 )
			reduced = 1;
		if ( reduced != final )
		{
			final = reduced;
			touched = true;
		}
	}

	// BACK ARMOR (domain 36, v9.45): -10%/Lv when eAttacker is inside the rear
	// arc of this player's view. Same shape and the same slot as SPRINT ARMOR,
	// so all three defensive domains stack MULTIPLICATIVELY rather than summing
	// into one flat cut (DR Lv10 + SPRINT ARMOR Lv5 + BACK ARMOR Lv3, all at
	// once and from behind while sprinting, is 0.5 x 0.75 x 0.7 = x0.2625 —
	// deep, but it takes three maxed cards and a specific situation to reach).
	// The attacker is passed in because "behind" is a bearing, not a state.
	ba = tod_upgrades::back_armor_mult( self, eAttacker );
	if ( ba < 1.0 )
	{
		reduced = int( final * ba );
		if ( reduced < 1 )
			reduced = 1;
		if ( reduced != final )
		{
			final = reduced;
			touched = true;
		}
	}

	// Tower demigod (level.tod_god): damage lands for real, health floors at
	// 1 HP. Same clamp shape as map 1's acc_god.
	if ( IS_TRUE( level.tod_god ) )
	{
		if ( final >= self.health )
			final = self.health - 1;
		if ( final < 0 )
			final = 0;
		return final;
	}

	if ( touched && final != iDamage )
		return final;
	return -1;
}

// ELITE down (v14.5 — the user quote at the TOD_ELITE_PTS define): the flat
// 500 goes to THE KILLER ALONE, scaled by
//   1. DOUBLE POINTS — level.zombie_vars[team]["zombie_point_scalar"], the
//      exact multiplier stock applies to normal kill money (_zm_score.gsc:341,
//      set 2/1 by _zm_powerup_double_points.gsc:79/:97), and
//   2. the BOUNTY domain — 1.0 + 5%/Lv via level.tod_bounty_mult_fn (the
//      pointer pattern tod_bounty_preview_fn established; no _tod_upgrades
//      import from this module, no cycle). Weapon-agnostic like the widened
//      domain itself.
// NO KILLER = NO MONEY, on purpose ("Only the person who kills gets the
// money"): an elite reaped by cleanup, a trap, another boss or the void pays
// nobody. `attacker` comes from each module's waittill("death", attacker)
// watcher — every elite watcher carries it. Callers: _tod_mangler,
// _tod_doppelghast, _tod_dealer_finale (the Map One elites' four callers retired
// whole 2026-10-05). Silent like every kill payout since 2026-08-20 (the score
// delta tells).
function grant_elite_reward( name, attacker, org )
{
	if ( isdefined( attacker ) && IS_TRUE( attacker.tod_is_partner ) )
	{
		owner = attacker.tod_partner_owner;
		if ( !isdefined( owner ) || !isplayer( owner ) ) return;
		owner_pts = int( TOD_ELITE_PTS * 0.5 );
		// THE HAVENS (docs/202): an owner standing inside a safe-zone field is paid a quarter
		if ( isdefined( level.tod_haven_kill_pay_fn ) )
			owner_pts = [[ level.tod_haven_kill_pay_fn ]]( owner, owner_pts );
		owner zm_score::add_to_player_score( owner_pts );
		elite_bottle_roll( name, owner, org );
		return;
	}
	if ( !isdefined( attacker ) || !isplayer( attacker ) )
		return;

	pts = TOD_ELITE_PTS;
	if ( isdefined( attacker.team )
	  && isdefined( level.zombie_vars[ attacker.team ] )
	  && isdefined( level.zombie_vars[ attacker.team ][ "zombie_point_scalar" ] ) )
	{
		pts = pts * level.zombie_vars[ attacker.team ][ "zombie_point_scalar" ];
	}
	if ( isdefined( level.tod_bounty_mult_fn ) )
		pts = pts * [[ level.tod_bounty_mult_fn ]]( attacker );
	// THE HAVENS (docs/202, user 2026-10-02): a killer standing inside a safe-zone
	// field is paid a quarter (banked to exact tens by _tod_haven::kill_pay), and the
	// feed row below shows exactly that number.
	if ( isdefined( level.tod_haven_kill_pay_fn ) )
		pts = [[ level.tod_haven_kill_pay_fn ]]( attacker, int( pts ) );

	attacker zm_score::add_to_player_score( int( pts ) );

	// THE FEED ROW (v17.37). KILLER ONLY, matching who the money went to — the
	// same rule the payout itself follows. The value sent is the FINAL one,
	// after double points and BOUNTY, so the row can never disagree with the
	// score it just added; the kit's own arms recompute a nominal value instead
	// and that is what made the +100/+110 bug of 2026-08-23.
	//
	// A trash-kill row may appear ALONGSIDE this one for the same corpse (an
	// elite the kit's own arms also recognise). That is not a duplicate: those
	// are two separate payouts — stock's kill money and this 500 — and the
	// feed's running total is the sum a player actually banked.
	attacker LuiNotifyEvent( &"score_event", 2, &"ZM_AETHERIUM_KF_ELITE", int( pts ) );

	// v18.96 — the perk bottle roll (org = where the elite died; undefined = no drop).
	elite_bottle_roll( name, attacker, org );

	// RIOT SHIELD (v17.16, user 2026-09-04: "every elite you kills takes off 2
	// seconds from the recharge time"). This function is where that hangs
	// because it is the ONE place every elite death already resolves to a
	// single killer — every alternative would have meant five separate hooks
	// and five chances to miss one. Guarded level pointer, set in
	// _tod_riotshield::init; never a #using (the KB cycle rule, exactly like
	// tod_bounty_mult_fn above). No-ops unless that player is mid-recharge.
	if ( isdefined( level.tod_shield_elite_kill ) )
		[[ level.tod_shield_elite_kill ]]( attacker );

	// DEMON SLAYER (the Warrior's card, 2026-09-27 class pass 2): an elite kill opens its
	// speed + damage window. The same ONE-seam reasoning as the shield line above; guarded
	// level pointer set in _tod_class_cards::init, never a #using.
	if ( isdefined( level.tod_cc_elite_kill_fn ) )
		attacker [[ level.tod_cc_elite_kill_fn ]]( name );
}

// =============================================================================
// v18.96 — THE PERK BOTTLE ROLL (see TOD_ELITE_BOTTLE_PCT). Called from
// grant_elite_reward with the corpse's spot. Power on, 10%.
// =============================================================================
function elite_bottle_roll( name, attacker, org )
{
	if ( !isdefined( org ) )
		return;
	if ( !( level flag::exists( "power_on" ) ) || !( level flag::get( "power_on" ) ) )
	{
		elite_dev_log( "bottle: " + name + " died before power — no roll" );
		return;
	}
	roll = RandomInt( 100 );
	if ( roll >= TOD_ELITE_BOTTLE_PCT )
	{
		elite_dev_log( "bottle: " + name + " roll " + roll + " >= " + TOD_ELITE_BOTTLE_PCT + " — no drop" );
		return;
	}
	// level thread — specific_powerup_drop can wait internally (map 1's blocking-callers rule).
	level thread zm_powerups::specific_powerup_drop( "tod_free_pap", org );
	elite_dev_log( "bottle: " + name + " roll " + roll + " < " + TOD_ELITE_BOTTLE_PCT + " — PERK BOTTLE dropped at " + org + " for player " + attacker GetEntityNumber() );
}

function elite_dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_ELITE_DROP] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
