// =============================================================================
// _tod_ambush.gsc - THE AMBUSH: the horde rises round YOU, not at the corners
// (docs/204, 2026-10-03; user: "This map should be more hectic than the first ...
// Lets check spawns and spawn rate speed and things as well. We should have
// challenging spawn points as well to make it tougher").
//
// WHAT WAS THERE. Every ordinary floor of the tower has exactly TWO authored risers,
// one on each landing corner, and stock picked one at random from the active zones
// (your floor and the floors above and below): six fixed corners, the same on all
// fifty floors. A player learns them in two floors, holds a landing facing the
// stairs, and the trickle arrives in a queue from known directions - and a third of
// it rose a floor away and spent its first seconds walking. The first map had the
// same layout, the same picker and the same trickle (docs/204 s1).
//
// WHAT THIS DOES. A share of the ordinary spawns (TOD_AMBUSH_PCT_*: 30% on round 1
// rising to 60% by round 15, +15 with the Rampage inducer, never over 80) climbs out
// of the navmesh in a ring round ONE upright player instead, with a direction:
//   AHEAD   (50%) in front of where they are facing: the stairs they are heading
//           down, the landing they are running at. May be on screen - a zombie
//           clawing out of the floor in front of you is the point - but never
//           inside TOD_AMBUSH_INNER of anybody (the ~2 s climb-out + ~1.5 s of
//           sprint is the warning).
//   BEHIND  (35%) behind them AND off everyone's screen: the floor they just left,
//           the flight above. The camping counter.
//   FLANK   (15%) anywhere else in the ring.
// The other spawns keep the authored corners (variety, and the hall / base / wing
// layouts the generator designed). The rolled direction falls back to the others
// when it has no legal point, then to the corners.
//
// THE RULES IT NEVER BREAKS (each one is a filter the spawn hook already applies to
// the corners, re-applied to the synthesized point - _tod_endless_rounds::
// finale_spawn_selection, THE PURSUIT docs/200, THE HAVENS docs/202):
//   * the point can WALK to the player (tod_reach::can_reach - never below a drop),
//     and the ENGINE agrees (CanPath, at most TOD_AMBUSH_PROBES queries a pick);
//   * it is in an enabled, ACTIVE zone that allows spawning (stock's own rule for
//     a riser, _zm_zonemgr create_spawner_list) - so a sealed crown hall, a
//     disabled zone or a room behind a shut door never raises one;
//   * never inside a live safe-zone field, and a player standing in one is never
//     the focus (the haven is a rest: the horde has to walk in through the slow);
//   * never in the Battle Arena, the card pause or an arena trip (their own spawn
//     rules own those moments);
//   * the crown rules: nothing beyond the causeway gate while it is shut, nothing on
//     the crown island after the Fall seals it (the finale's aggro guard and its
//     sealed-hall rule retired with the Map One ending, 2026-10-05);
//   * one ambush round the same player at most every TOD_AMBUSH_GAP_MS (no wall of
//     zombies appearing at once);
//   * the ring (TOD_AMBUSH_OUTER, +/- TOD_AMBUSH_HEIGHT) fits inside THE HUNT's
//     "too far" bar, so _tod_stray never moves an ambush spawn as FAR, and the inner
//     edge is wider than its DEST_MIN (tools/test_ambush.js asserts both).
// THE ARRIVAL is stock's own climb-out (the riser anim, the dirt burst, the sound)
// at the synthesized point: the spot is a struct with script_noteworthy
// "riser_location", exactly what _tod_stray's navmesh arrivals use.
//
// ONE OWNER of "where does an ordinary zombie rise". Imports only leaf modules: the
// round module imports this one, so anything here that reached _tod_bosses (which
// imports the round module) would be a cycle - which is why the sight test is its
// own copy of stock's FOV test and not _tod_stray's.
//
// LOGS (dev): [TOD_AMBUSH] INIT (every knob), PICK (the first TOD_AMBUSH_LOG_FIRST:
// asked / got direction, distance, height, view dot, seen, zone, probes, the round
// share, the bucket sizes), SUMMARY every 15 s while anything happened (pool /
// ahead / behind / flank / fallback / no_focus / no_ring / no_spot / zone_fail /
// path_fail / no_actor / agent_self / agent_other).
// =============================================================================

#using scripts\shared\laststand_shared;

#using scripts\zm\zm_tod2_cybercity\_tod_reach;
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;
#using scripts\zm\zm_tod2_cybercity\_tod_arena_data;
#using scripts\zm\zm_tod2_cybercity\_tod_house_data;   // GENERATED - in_house / in_parlour: THE DEALER'S HOUSE is away too (docs/207)

#insert scripts\shared\shared.gsh;

#namespace tod_ambush;

// ---- THE SHARE: how many ordinary spawns rise round a player ------------------------
#define TOD_AMBUSH_PCT_START      30      // round 1
#define TOD_AMBUSH_PCT_FULL       60      // from TOD_AMBUSH_FULL_ROUND on (linear between)
#define TOD_AMBUSH_FULL_ROUND     15
#define TOD_AMBUSH_PCT_RAMPAGE    15      // added while the Rampage inducer is on
#define TOD_AMBUSH_PCT_MAX        80      // the authored corners always keep a fifth

// ---- THE DIRECTION: of the ambush spawns ---------------------------------------------
#define TOD_AMBUSH_AHEAD_PCT      50      // in front of the focus
#define TOD_AMBUSH_BEHIND_PCT     35      // behind the focus, off every screen
                                          // the remainder (15) is a flank
#define TOD_AMBUSH_AHEAD_COS      0.5     // ahead = within 60 degrees of the view (yaw only)
#define TOD_AMBUSH_BEHIND_COS     -0.25   // behind = more than ~105 degrees from the view

// ---- THE RING round the focus ---------------------------------------------------------
#define TOD_AMBUSH_INNER          360     // never closer than this to ANY player (> _tod_stray's DEST_MIN 280)
#define TOD_AMBUSH_OUTER          900     // the ring's outer edge
#define TOD_AMBUSH_HEIGHT         192     // one flight up or down: the stairs ahead and behind on the spiral
#define TOD_AMBUSH_SPACING        64      // navmesh query grid
#define TOD_AMBUSH_SCAN           64      // ring points classified per pick (random sample)
#define TOD_AMBUSH_CACHE_MS       500     // a player's ring query is reused this long

// ---- THE GUARDS ------------------------------------------------------------------------
#define TOD_AMBUSH_GAP_MS         600     // one ambush round the same player at most this often
#define TOD_AMBUSH_PROBES         2       // engine CanPath second opinions per pick
#define TOD_AMBUSH_ZONE_TRIES     4       // zone lookups per pick (one probe entity, moved)
#define TOD_AMBUSH_FOV_COS        0.766   // stock's "can a player see this" (zm_giant_cleanup_mgr player_can_see_me)

// ---- DIAGNOSTICS -----------------------------------------------------------------------
#define TOD_AMBUSH_LOG_FIRST      40
#define TOD_AMBUSH_SUMMARY_MS     15000

function init()
{
	if ( IS_TRUE( level.tod_ambush_on ) )
		return;
	level.tod_ambush_on = true;
	level.tod_ambush_n = [];
	level.tod_ambush_logged = 0;
	level thread summary_watch();
	dev_log( "INIT rev=1 pct=" + TOD_AMBUSH_PCT_START + "->" + TOD_AMBUSH_PCT_FULL + "@r" + TOD_AMBUSH_FULL_ROUND
		+ " rampage=+" + TOD_AMBUSH_PCT_RAMPAGE + " max=" + TOD_AMBUSH_PCT_MAX
		+ " split=ahead" + TOD_AMBUSH_AHEAD_PCT + "/behind" + TOD_AMBUSH_BEHIND_PCT + "/flank" + ( 100 - TOD_AMBUSH_AHEAD_PCT - TOD_AMBUSH_BEHIND_PCT )
		+ " ring=" + TOD_AMBUSH_INNER + "-" + TOD_AMBUSH_OUTER + " h=" + TOD_AMBUSH_HEIGHT + " gap_ms=" + TOD_AMBUSH_GAP_MS + " probes=" + TOD_AMBUSH_PROBES );
}

// =============================================================================
// THE DECISIONS (pure - tools/test_ambush.js runs these verbatim)
// =============================================================================

// -> the % of ordinary spawns that rise round a player this round.
function share_pct( round, rampage )
{
	if ( !isdefined( round ) || round < 1 )
		round = 1;
	pct = TOD_AMBUSH_PCT_FULL;
	if ( round < TOD_AMBUSH_FULL_ROUND )
		pct = TOD_AMBUSH_PCT_START + ( ( TOD_AMBUSH_PCT_FULL - TOD_AMBUSH_PCT_START ) * ( round - 1 ) ) / ( TOD_AMBUSH_FULL_ROUND - 1 );
	if ( IS_TRUE( rampage ) )
		pct = pct + TOD_AMBUSH_PCT_RAMPAGE;
	if ( pct > TOD_AMBUSH_PCT_MAX )
		pct = TOD_AMBUSH_PCT_MAX;
	return int( pct );
}

// roll 0..99 -> the direction this ambush asks for.
function intent_of( roll )
{
	if ( roll < TOD_AMBUSH_AHEAD_PCT )
		return "ahead";
	if ( roll < TOD_AMBUSH_AHEAD_PCT + TOD_AMBUSH_BEHIND_PCT )
		return "behind";
	return "flank";
}

// -> the direction a ring point lies in. dot = the yaw-only view direction of the
// focus . the flat direction to the point; seen = any player could have it on screen.
// A point behind the focus that SOMEONE sees is not "behind" - it is a flank.
function bucket_of( dot, seen )
{
	if ( dot >= TOD_AMBUSH_AHEAD_COS )
		return "ahead";
	if ( dot <= TOD_AMBUSH_BEHIND_COS && !seen )
		return "behind";
	return "flank";
}

// -> the order the directions are tried in: the one asked for, then a flank, then
// the opposite. An ambush never turns into "no spawn": the corners are the last resort.
function try_order( intent )
{
	if ( intent == "ahead" )
		return array( "ahead", "flank", "behind" );
	if ( intent == "behind" )
		return array( "behind", "flank", "ahead" );
	return array( "flank", "behind", "ahead" );
}

// -> may a zombie climb out at org to come for the player whose navmesh point is
// goal? Every rule the spawn hook applies to the authored corners, re-applied.
function legal( org, goal )
{
	if ( !isdefined( org ) || !isdefined( goal ) )
		return false;
	if ( !tod_reach::can_reach( org, goal ) )
		return false;
	if ( too_close( org ) )
		return false;
	if ( isdefined( level.tod_haven_inside_fn ) && [[ level.tod_haven_inside_fn ]]( org ) )
		return false;
	if ( tod_arena_data::in_arena( org ) || tod_house_data::in_house( org ) || tod_house_data::in_parlour( org ) )
		return false;
	if ( !IS_TRUE( level.tod_gate_open ) && tod_crown_data::beyond_gate( org ) )
		return false;
	if ( IS_TRUE( level.tod_fall_sealed ) && !IS_TRUE( level.tod_fall_return_open ) && tod_crown_data::jumppad_enabled() && tod_crown_data::on_crown_island( org ) )
		return false;
	return true;
}

// -> true if org is inside TOD_AMBUSH_INNER of ANY living player, downed ones too
// (a crawler must not have a zombie climb out on top of them either).
function too_close( org )
{
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		if ( p.sessionstate == "spectator" )
			continue;
		if ( DistanceSquared( org, p.origin ) < TOD_AMBUSH_INNER * TOD_AMBUSH_INNER )
			return true;
	}
	return false;
}

// -> true if ANY living, non-spectating player could have org on screen. Stock's
// cleanup test verbatim (FOV only, no trace): conservative for a "behind" spawn -
// an occluded point a player faces still counts as seen.
function seen_by_anyone( org )
{
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		if ( p.sessionstate == "spectator" )
			continue;
		to = org - p.origin;
		if ( LengthSquared( to ) < 1 )
			return true;
		fwd = AnglesToForward( p GetPlayerAngles() );
		if ( VectorDot( fwd, VectorNormalize( to ) ) >= TOD_AMBUSH_FOV_COS )
			return true;
	}
	return false;
}

// -> a random upright player the next ambush may rise round, or undefined. Not a
// crawler (a downed player must not draw the horde onto themself), not a jump-pad
// flyer (between regions), not anyone inside a live safe-zone field or the arena,
// and not anyone ambushed in the last TOD_AMBUSH_GAP_MS.
function pick_focus()
{
	now = GetTime();
	out = [];
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		if ( p.sessionstate == "spectator" )
			continue;
		if ( p laststand::player_is_in_laststand() )
			continue;
		if ( IS_TRUE( p.tod_jumppad_flying ) )
			continue;
		if ( isdefined( p.tod_ambush_ms ) && ( now - p.tod_ambush_ms ) < TOD_AMBUSH_GAP_MS )
			continue;
		if ( isdefined( level.tod_haven_inside_fn ) && [[ level.tod_haven_inside_fn ]]( p.origin ) )
			continue;
		if ( tod_arena_data::in_arena( p.origin ) || tod_house_data::in_house( p.origin ) || tod_house_data::in_parlour( p.origin ) )
			continue;
		out[ out.size ] = p;
	}
	if ( out.size == 0 )
		return undefined;
	return out[ RandomInt( out.size ) ];
}

// =============================================================================
// THE PICK - self = the zombie stock is spawning (the spawn hook inherits it from
// _zm_spawner::do_zombie_spawn). -> a riser spot, or undefined to use the corners.
// =============================================================================
function pick( spots )
{
	if ( !IS_TRUE( level.tod_ambush_on ) )
		return undefined;
	if ( IS_TRUE( level.tod_arena_active ) || IS_TRUE( level.tod_upgrade_pause ) )
		return undefined;

	rnd = 1;
	if ( isdefined( level.round_number ) )
		rnd = level.round_number;
	pct = share_pct( rnd, level.tod_rampage_on );
	if ( RandomInt( 100 ) >= pct )
	{
		tally( "pool" );
		return undefined;
	}
	// The engine path check needs an agent. Stock calls the hook from the zombie's
	// own spawn thread, so self is that zombie; if a build ever calls it without one,
	// any live zombie-team actor paths the same navmesh (agent_self / agent_other in
	// the SUMMARY say which happened).
	ai = path_agent( self );
	if ( !isdefined( ai ) )
	{
		tally( "no_actor" );
		return undefined;
	}
	focus = pick_focus();
	if ( !isdefined( focus ) )
	{
		tally( "no_focus" );
		return undefined;
	}
	intent = intent_of( RandomInt( 100 ) );
	goal = tod_reach::reach_point( focus );
	pts = ring( focus, goal );
	if ( pts.size == 0 )
	{
		tally( "no_ring" );
		return undefined;
	}

	// Classify a random sample of the ring by direction from the focus.
	ang = focus GetPlayerAngles();
	fwd = AnglesToForward( ( 0, ang[ 1 ], 0 ) );
	buckets = [];
	buckets[ "ahead" ] = [];
	buckets[ "behind" ] = [];
	buckets[ "flank" ] = [];
	// A partial shuffle: TOD_AMBUSH_SCAN distinct random points, O(SCAN) not O(ring).
	n = TOD_AMBUSH_SCAN;
	if ( n > pts.size )
		n = pts.size;
	for ( i = 0; i < n; i++ )
	{
		j = i + RandomInt( pts.size - i );
		t = pts[ i ];
		pts[ i ] = pts[ j ];
		pts[ j ] = t;
		org = pts[ i ];
		if ( !legal( org, goal ) )
			continue;
		to = org - focus.origin;
		to = ( to[ 0 ], to[ 1 ], 0 );
		if ( LengthSquared( to ) < 1 )
			continue;
		b = bucket_of( VectorDot( fwd, VectorNormalize( to ) ), seen_by_anyone( org ) );
		buckets[ b ][ buckets[ b ].size ] = org;
	}

	order = try_order( intent );
	probes = 0;
	zones = 0;
	for ( k = 0; k < order.size; k++ )
	{
		pool = buckets[ order[ k ] ];
		for ( i = 0; i < pool.size; i++ )
		{
			if ( probes >= TOD_AMBUSH_PROBES || zones >= TOD_AMBUSH_ZONE_TRIES )
				break;
			org = pool[ i ];
			zones++;
			zone = spawn_zone( org );
			if ( !isdefined( zone ) )
			{
				tally( "zone_fail" );
				continue;
			}
			probes++;
			if ( !( ai CanPath( org, goal ) ) )
			{
				tally( "path_fail" );
				continue;
			}
			spot = make_spot( org, focus, zone );
			focus.tod_ambush_ms = GetTime();
			tally( order[ k ] );
			if ( order[ k ] != intent )
				tally( "fallback" );
			pick_log( intent, order[ k ], org, focus, zone, probes, pct, buckets );
			return spot;
		}
	}
	tally( "no_spot" );
	return undefined;
}

// -> the actor whose CanPath answers for the spawn: me when I am a living actor,
// else the first living zombie-team actor, else undefined. The archetype read
// comes before IsActor so a non-entity self (level) never reaches the builtin.
function path_agent( me )
{
	if ( isdefined( me ) && isdefined( me.archetype ) && IsActor( me ) && IsAlive( me ) )
	{
		tally( "agent_self" );
		return me;
	}
	if ( !isdefined( level.zombie_team ) )
		return undefined;
	a = GetAITeamArray( level.zombie_team );
	for ( i = 0; i < a.size; i++ )
	{
		if ( isdefined( a[ i ] ) && IsAlive( a[ i ] ) && IsActor( a[ i ] ) )
		{
			tally( "agent_other" );
			return a[ i ];
		}
	}
	return undefined;
}

// focus's ring of navmesh points, cached TOD_AMBUSH_CACHE_MS per player (a pick
// every spawn would otherwise run one query per zombie).
function ring( focus, goal )
{
	now = GetTime();
	if ( isdefined( focus.tod_ambush_q ) && isdefined( focus.tod_ambush_q_ms ) && ( now - focus.tod_ambush_q_ms ) < TOD_AMBUSH_CACHE_MS )
		return focus.tod_ambush_q;
	pts = [];
	q = PositionQuery_Source_Navigation( goal, TOD_AMBUSH_INNER, TOD_AMBUSH_OUTER, TOD_AMBUSH_HEIGHT, TOD_AMBUSH_SPACING );
	if ( isdefined( q ) && isdefined( q.data ) )
	{
		for ( i = 0; i < q.data.size; i++ )
		{
			if ( isdefined( q.data[ i ].origin ) )
				pts[ pts.size ] = q.data[ i ].origin;
		}
	}
	focus.tod_ambush_q = pts;
	focus.tod_ambush_q_ms = now;
	return pts;
}

// -> the zone org is in, if a riser there would be legal by STOCK's rule (enabled,
// active, spawning allowed - _zm_zonemgr create_spawner_list), else undefined.
// ONE persistent probe entity moved to the point (stock's own pattern in
// _zm_utility check_point_in_enabled_zone): get_zone_from_position would spawn and
// delete a script_origin per lookup. Only the zones stock would spawn in are tested.
function spawn_zone( org )
{
	if ( !isdefined( level.zones ) )
		return undefined;
	probe = zone_probe( org + ( 0, 0, 32 ) );
	if ( !isdefined( probe ) )
		return undefined;
	keys = GetArrayKeys( level.zones );
	for ( i = 0; i < keys.size; i++ )
	{
		z = level.zones[ keys[ i ] ];
		if ( !isdefined( z ) || !IS_TRUE( z.is_enabled ) || !IS_TRUE( z.is_active ) || !IS_TRUE( z.is_spawning_allowed ) )
			continue;
		if ( !isdefined( z.volumes ) )
			continue;
		for ( v = 0; v < z.volumes.size; v++ )
		{
			if ( isdefined( z.volumes[ v ] ) && probe IsTouching( z.volumes[ v ] ) )
				return keys[ i ];
		}
	}
	return undefined;
}

// -> the persistent zone probe, moved to pos.
function zone_probe( pos )
{
	if ( !isdefined( level.tod_ambush_probe ) )
		level.tod_ambush_probe = Spawn( "script_origin", pos );
	else
		level.tod_ambush_probe.origin = pos;
	return level.tod_ambush_probe;
}

// -> a riser spot at org facing the focus: the fields stock's climb-out reads
// (_zm_utility move_zombie_spawn_location -> _zm_spawner do_zombie_rise) and the
// script_string every authored riser on this map carries.
function make_spot( org, focus, zone )
{
	s = SpawnStruct();
	s.origin = org;
	yaw = 0;
	to = focus.origin - org;
	to = ( to[ 0 ], to[ 1 ], 0 );
	if ( LengthSquared( to ) > 1 )
	{
		a = VectorToAngles( to );
		yaw = a[ 1 ];
	}
	s.angles = ( 0, yaw, 0 );
	s.script_noteworthy = "riser_location";
	s.script_string = "find_flesh";
	s.zone_name = zone;
	s.tod_ambush = true;
	return s;
}

// =============================================================================
// DIAGNOSTICS (CLAUDE.md dev-mode rule)
// =============================================================================
function tally( key )
{
	if ( !isdefined( level.tod_ambush_n ) )
		level.tod_ambush_n = [];
	if ( !isdefined( level.tod_ambush_n[ key ] ) )
		level.tod_ambush_n[ key ] = 0;
	level.tod_ambush_n[ key ]++;
}

function pick_log( intent, got, org, focus, zone, probes, pct, buckets )
{
	if ( !IS_TRUE( level.tod_dev ) )
		return;
	if ( !isdefined( level.tod_ambush_logged ) )
		level.tod_ambush_logged = 0;
	if ( level.tod_ambush_logged >= TOD_AMBUSH_LOG_FIRST )
		return;
	level.tod_ambush_logged++;
	to = org - focus.origin;
	ang = focus GetPlayerAngles();
	fwd = AnglesToForward( ( 0, ang[ 1 ], 0 ) );
	flat = ( to[ 0 ], to[ 1 ], 0 );
	dot = 0;
	if ( LengthSquared( flat ) > 1 )
		dot = VectorDot( fwd, VectorNormalize( flat ) );
	dev_log( "PICK asked=" + intent + " got=" + got + " dist=" + int( Distance2D( org, focus.origin ) ) + " dz=" + int( to[ 2 ] )
		+ " dot=" + ( int( dot * 100 ) / 100.0 ) + " seen=" + seen_by_anyone( org ) + " zone=" + zone + " probes=" + probes
		+ " focus=" + focus GetEntityNumber() + " round=" + level.round_number + " pct=" + pct
		+ " buckets=" + buckets[ "ahead" ].size + "/" + buckets[ "behind" ].size + "/" + buckets[ "flank" ].size
		+ " at=" + org );
}

function summary_watch()
{
	level endon( "end_game" );
	last = "";
	for ( ;; )
	{
		wait ( TOD_AMBUSH_SUMMARY_MS / 1000 );
		if ( !isdefined( level.tod_ambush_n ) )
			continue;
		line = "";
		keys = GetArrayKeys( level.tod_ambush_n );
		for ( i = 0; i < keys.size; i++ )
			line = line + " " + keys[ i ] + "=" + level.tod_ambush_n[ keys[ i ] ];
		if ( line == last )
			continue;
		last = line;
		rnd = 0;
		if ( isdefined( level.round_number ) )
			rnd = level.round_number;
		dev_log( "SUMMARY round=" + rnd + " share=" + share_pct( rnd, level.tod_rampage_on ) + "% totals:" + line );
	}
}

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_AMBUSH] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
