// =============================================================================
// _tod_reach.gsc — CAN SOMETHING STANDING AT A WALK TO B? (docs/200, THE PURSUIT)
//
// User 2026-10-02: "zombies not being able to trace or target players ... there
// are many places where you can jump off and you can't get back on unless you do
// some special movement ... zombies don't have these animations ... we need a
// foolproof solution". This file is the one place that answers the question every
// other part of THE PURSUIT asks: the spawn filter, zombie targeting, the stray
// relocator and the elite spawn picker all call can_reach().
//
// WHY A MODEL AND NOT THE ENGINE. The engine has CanPath(), and _tod_stray uses it
// as a SECOND opinion on the few spots it is about to use. It cannot be the first
// opinion: it is a full A* per call, and the old targeting code (zm_tod2_cybercity
// .gsc, tod_closest_player) records the stock PathDistance probe failing at range
// on this 19,000-unit spiral. A per-zombie, per-player, per-tick question needs an
// answer that costs a few comparisons and is the same at 20 units and 20,000.
//
// THE MODEL. Three REGIONS no zombie crosses: the TOWER (the Undercity, the plaza,
// all fifty laps, the crown stair, the terrace and the top transit bay — one walk),
// the CROWN ISLAND (the hall and everything off it; the jump pad only goes one way
// and only carries players) and the BATTLE ARENA (a detached room). Inside the
// tower, the spiral is a CHAIN: every lap transition is a CUT that is either
//   * a PAID DOOR — passable both ways once bought (its zone flag is set), or
//   * a BROKEN DROP — the 24 one-way drops (docs/tower_design/BROKEN_TOWER.md):
//     a zombie can go DOWN it (native zm_jump_down_190 negotiation, seen working in
//     the 2026-10-01 run: zombie 44 dropped 18254 -> 18049) and can NEVER come up.
// So walking from A to B crosses the cuts between their heights, and the walk is
// legal iff no crossed door is shut and, going UP, no crossed cut is a drop.
//
// WHERE THE CUTS SIT. Lap k climbs from floor k-1 (z = (k-1) x 384) to floor k.
//   door k : on floor k-1's end landing, at the foot of lap k's first flight. The
//            landing is z+0..2, the first tread z+12 — the cut is at +8.
//   drop k : the catch deck is z+2, the ledge (the old mid landing) z+192 — the
//            cut is at +96.
//   roof   : enter_roof on lap 50's end landing (19200), the crown stair above.
// Everything walkable on the spiral is monotonic in z (the lounges, the transit
// spurs and the floor-40 arena chamber all sit on their lap's mid landing), so a
// height alone places a point in its cell. LOCKSTEP with tools/gen_tower_map.js
// (LAPS, LAP_RISE, STEPS x RISE) and the generated drop table — tools/
// test_pursuit.js reads both and fails the build if they drift.
//
// FAIL OPEN. Anything this file cannot vouch for — an uninitialised table, an
// unknown flag, an undefined point — answers "reachable". The failure mode of the
// model is therefore today's stock behaviour, never a new strand.
// =============================================================================

#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;

#using scripts\zm\zm_tod2_cybercity\_tod_door_data;
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;
#using scripts\zm\zm_tod2_cybercity\_tod_arena_data;
#using scripts\zm\zm_tod2_cybercity\_tod_house_data;   // GENERATED - in_house / in_parlour: THE DEALER'S HOUSE is the arena's region (docs/207)

#insert scripts\shared\shared.gsh;

#namespace tod_reach;

// LOCKSTEP with tools/gen_tower_map.js — test_pursuit.js asserts all three.
#define TOD_REACH_LAPS        50
#define TOD_REACH_LAP_RISE    384
#define TOD_REACH_DOOR_CUT    8      // landing z+0..2 | first tread z+12
#define TOD_REACH_DROP_CUT    96     // catch deck z+2 | ledge z+192

// Walking cost of height on the spiral: two flights of 512 tread plus two
// landings buy one LAP_RISE of 384, so a unit of height costs ~4 of path.
#define TOD_REACH_Z_WEIGHT    4

#define TOD_REACH_TOWER       0
#define TOD_REACH_CROWN       1
#define TOD_REACH_ARENA       2

// Dev summary cadence for the spawn filter (one line, only if it did anything).
#define TOD_REACH_SUMMARY_MS  15000

// THE SPAWN FILTER'S "NEAR" BAR — LOCKSTEP with _tod_stray's TOD_STRAY_COST
// (tools/test_pursuit.js asserts they are equal). A riser farther than this from
// every player it can reach would raise a zombie THE HUNT moves three seconds
// later: two climb-outs for one zombie and a horde that arrives late — the
// "waiting around" the user named. Near risers are preferred; far ones are kept
// only when nothing near exists.
#define TOD_REACH_SPAWN_NEAR  2400

function init()
{
	if ( IS_TRUE( level.tod_reach_ready ) )
		return;
	build_cuts();
	level.tod_reach_ready = true;
	level.tod_reach_spawn_kept = 0;
	level.tod_reach_spawn_cut = 0;
	level.tod_reach_spawn_open = 0;
	level.tod_reach_spawn_far = 0;
	level thread door_watch();
	level thread summary_watch();
	drops = level.tod_reach_drop_pre[ level.tod_reach_cut_z.size ];
	reach_log( "INIT rev=1 cuts=" + level.tod_reach_cut_z.size + " drops=" + drops + " doors=" + ( level.tod_reach_cut_z.size - drops )
		+ " lap_rise=" + TOD_REACH_LAP_RISE + " door_cut=+" + TOD_REACH_DOOR_CUT + " drop_cut=+" + TOD_REACH_DROP_CUT );
}

// The chain, bottom to top. Lap order IS height order (door +8 < drop +96 < the
// next lap's +384), so the arrays come out sorted with no sort.
function build_cuts()
{
	cz = [];
	cdrop = [];
	cflag = [];
	for ( k = 1; k <= TOD_REACH_LAPS; k++ )
	{
		b = ( k - 1 ) * TOD_REACH_LAP_RISE;
		n = cz.size;
		if ( isdefined( tod_door_data::get_drop_info( k ) ) )
		{
			cz[ n ] = b + TOD_REACH_DROP_CUT;
			cdrop[ n ] = true;
			cflag[ n ] = "";
		}
		else
		{
			cz[ n ] = b + TOD_REACH_DOOR_CUT;
			cdrop[ n ] = false;
			cflag[ n ] = "enter_lap" + k;
		}
	}
	n = cz.size;
	cz[ n ] = ( TOD_REACH_LAPS * TOD_REACH_LAP_RISE ) + TOD_REACH_DOOR_CUT;
	cdrop[ n ] = false;
	cflag[ n ] = "enter_roof";

	level.tod_reach_cut_z = cz;
	level.tod_reach_cut_drop = cdrop;
	level.tod_reach_cut_flag = cflag;

	dp = [];
	dp[ 0 ] = 0;
	for ( i = 0; i < cz.size; i++ )
	{
		add = 0;
		if ( cdrop[ i ] )
			add = 1;
		dp[ i + 1 ] = dp[ i ] + add;
	}
	level.tod_reach_drop_pre = dp;
	rebuild_closed();
}

// Prefix count of SHUT doors below each cut. Doors only ever open, so this is
// rebuilt on each opening (door_wait) and never otherwise.
function rebuild_closed()
{
	cp = [];
	cp[ 0 ] = 0;
	for ( i = 0; i < level.tod_reach_cut_z.size; i++ )
	{
		add = 0;
		if ( !level.tod_reach_cut_drop[ i ] && !door_open( level.tod_reach_cut_flag[ i ] ) )
			add = 1;
		cp[ i + 1 ] = cp[ i ] + add;
	}
	level.tod_reach_closed_pre = cp;
}

// An unknown flag never blocks (fail open — see the header).
function door_open( flag )
{
	if ( !isdefined( flag ) || flag == "" )
		return true;
	if ( !( level flag::exists( flag ) ) )
		return true;
	return level flag::get( flag );
}

function door_watch()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	rebuild_closed();
	waiting = 0;
	for ( i = 0; i < level.tod_reach_cut_flag.size; i++ )
	{
		if ( level.tod_reach_cut_drop[ i ] )
			continue;
		f = level.tod_reach_cut_flag[ i ];
		if ( !( level flag::exists( f ) ) )
		{
			reach_log( "NO_FLAG cut=" + i + " flag=" + f + " (treated as open)" );
			continue;
		}
		level thread door_wait( f );
		waiting++;
	}
	reach_log( "DOORS watching=" + waiting + " shut=" + level.tod_reach_closed_pre[ level.tod_reach_cut_z.size ] );
}

function door_wait( f )
{
	level endon( "end_game" );
	level flag::wait_till( f );
	rebuild_closed();
	reach_log( "DOOR_OPEN flag=" + f + " shut_left=" + level.tod_reach_closed_pre[ level.tod_reach_cut_z.size ] );
}

// ---------------------------------------------------------------------------
// THE QUESTIONS
// ---------------------------------------------------------------------------

function region_of( org )
{
	if ( tod_arena_data::in_arena( org ) || tod_house_data::in_house( org ) || tod_house_data::in_parlour( org ) )
		return TOD_REACH_ARENA;   // docs/207: the Dealer's two rooms are away like the arena
	if ( tod_crown_data::on_crown_island( org ) )
		return TOD_REACH_CROWN;
	return TOD_REACH_TOWER;
}

// Number of cuts at or below z = the chain cell a height sits in (0 = below the
// first door: the plaza and the Undercity; size = above enter_roof).
function cut_index( z )
{
	cz = level.tod_reach_cut_z;
	lo = 0;
	hi = cz.size;
	while ( lo < hi )
	{
		mid = int( ( lo + hi ) / 2 );
		if ( cz[ mid ] <= z )
			lo = mid + 1;
		else
			hi = mid;
	}
	return lo;
}

// Cell a -> cell b along the chain. Down: only a shut door stops the walk (a drop
// IS a way down). Up: a shut door or any drop stops it.
function chain_ok( a, b )
{
	if ( a == b )
		return true;
	if ( a > b )
		return ( ( level.tod_reach_closed_pre[ a ] - level.tod_reach_closed_pre[ b ] ) == 0 );
	if ( ( level.tod_reach_closed_pre[ b ] - level.tod_reach_closed_pre[ a ] ) != 0 )
		return false;
	return ( ( level.tod_reach_drop_pre[ b ] - level.tod_reach_drop_pre[ a ] ) == 0 );
}

// -> true if something standing at `from` can WALK to `to`. DIRECTED.
function can_reach( from, to )
{
	if ( !isdefined( from ) || !isdefined( to ) )
		return true;
	if ( !IS_TRUE( level.tod_reach_ready ) )
		return true;
	rf = region_of( from );
	if ( rf != region_of( to ) )
		return false;
	if ( rf != TOD_REACH_TOWER )
		return true;   // the island and the arena are one cell each: their inner doors only ever open with a player behind them
	return chain_ok( cut_index( from[ 2 ] ), cut_index( to[ 2 ] ) );
}

// Where a zombie actually goes for this player: stock's navmesh shadow of them
// (player_shared::last_valid_position — the point every zombie goal uses,
// _zm_behavior.gsc zombieUpdateGoal), or the origin before stock has one.
function reach_point( p )
{
	if ( isdefined( p.last_valid_position ) )
		return p.last_valid_position;
	return p.origin;
}

// Estimated WALKING cost between two points (see TOD_REACH_Z_WEIGHT).
function cost( a, b )
{
	dz = a[ 2 ] - b[ 2 ];
	if ( dz < 0 )
		dz = 0 - dz;
	return Distance2D( a, b ) + dz * TOD_REACH_Z_WEIGHT;
}

// -> the player a zombie at `origin` should chase, from a list stock has already
// filtered (valid, not ignored — zm_utility::get_closest_valid_player). A player
// it can REACH always beats one it cannot; among equals the cheaper walk wins.
// Never undefined while the list has a player: a zombie nobody can reach still
// chases the nearest one as far as the geometry lets it, and _tod_stray moves it
// within seconds (an undefined pick would park it with no enemy at all).
function closest( origin, players )
{
	best = undefined;
	best_c = 0;
	best_r = false;
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) )
			continue;
		pt = reach_point( p );
		r = can_reach( origin, pt );
		c = cost( origin, pt );
		if ( !isdefined( best ) || ( r && !best_r ) || ( r == best_r && c < best_c ) )
		{
			best = p;
			best_c = c;
			best_r = r;
		}
	}
	return best;
}

// -> `players` minus the ones a zombie at `origin` cannot reach — or the whole
// list when it can reach none of them (the caller keeps a target either way).
function reachable_players( origin, players )
{
	keep = [];
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( isdefined( p ) && can_reach( origin, reach_point( p ) ) )
			keep[ keep.size ] = p;
	}
	if ( keep.size == 0 )
		return players;
	return keep;
}

// Living, playing players. Downed players count only when nobody is upright,
// and a jump-pad flyer never anchors anything (he is mid-air between regions).
function anchors()
{
	up = [];
	any = [];
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		if ( p.sessionstate == "spectator" )
			continue;
		if ( IS_TRUE( p.tod_jumppad_flying ) )
			continue;
		any[ any.size ] = reach_point( p );
		if ( !( p laststand::player_is_in_laststand() ) )
			up[ up.size ] = reach_point( p );
	}
	if ( up.size > 0 )
		return up;
	return any;
}

// THE SPAWN FILTER (called first thing by _tod_endless_rounds::
// finale_spawn_selection, stock's own spawn-spot hook). Keeps the risers from
// which at least one player is reachable. This is the root fix for the drops:
// the zone graph is two-way, so while you stand above a drop the floor BELOW it
// is an active zone and stock raised zombies on its catch deck — under you, with
// no way up (2026-10-01 run: a zombie born on lap 43's deck, the player on the
// ledge 190 above, the engine's own CanPath = 0). Same fail-safe shape as every
// filter in that function: a pool that is ALL unreachable is left to stock,
// because stock cannot take "no spot" — _tod_stray then moves what rises.
function filter_spawns( spots )
{
	if ( !IS_TRUE( level.tod_reach_ready ) || !isdefined( spots ) || spots.size == 0 )
		return spots;
	pts = anchors();
	if ( pts.size == 0 )
		return spots;
	keep = [];
	for ( i = 0; i < spots.size; i++ )
	{
		sp = spots[ i ];
		if ( !isdefined( sp ) || !isdefined( sp.origin ) )
			continue;
		for ( j = 0; j < pts.size; j++ )
		{
			if ( can_reach( sp.origin, pts[ j ] ) )
			{
				keep[ keep.size ] = sp;
				break;
			}
		}
	}
	if ( keep.size == 0 )
	{
		level.tod_reach_spawn_open++;
		return spots;
	}
	level.tod_reach_spawn_kept++;
	if ( keep.size < spots.size )
		level.tod_reach_spawn_cut += ( spots.size - keep.size );

	// PREFER NEAR (see TOD_REACH_SPAWN_NEAR): of the reachable risers, the ones
	// within the hunt's bar of a player they can reach. A soft preference — an
	// empty near set keeps every reachable riser.
	near = [];
	for ( i = 0; i < keep.size; i++ )
	{
		for ( j = 0; j < pts.size; j++ )
		{
			if ( cost( keep[ i ].origin, pts[ j ] ) <= TOD_REACH_SPAWN_NEAR && can_reach( keep[ i ].origin, pts[ j ] ) )
			{
				near[ near.size ] = keep[ i ];
				break;
			}
		}
	}
	if ( near.size > 0 )
	{
		if ( near.size < keep.size )
			level.tod_reach_spawn_far += ( keep.size - near.size );
		return near;
	}
	return keep;
}

// -> "tower:<cell>" / "crown" / "arena" — for log lines.
function describe( org )
{
	if ( !isdefined( org ) )
		return "none";
	r = region_of( org );
	if ( r == TOD_REACH_ARENA )
		return "arena";
	if ( r == TOD_REACH_CROWN )
		return "crown";
	if ( !IS_TRUE( level.tod_reach_ready ) )
		return "tower:?";
	return "tower:" + cut_index( org[ 2 ] );
}

function summary_watch()
{
	level endon( "end_game" );
	last_k = 0;
	last_c = 0;
	last_o = 0;
	last_f = 0;
	for ( ;; )
	{
		wait ( TOD_REACH_SUMMARY_MS / 1000 );
		k = level.tod_reach_spawn_kept;
		c = level.tod_reach_spawn_cut;
		o = level.tod_reach_spawn_open;
		f = level.tod_reach_spawn_far;
		if ( c == last_c && o == last_o && f == last_f )
		{
			last_k = k;
			continue;
		}
		reach_log( "SPAWN_FILTER picks=" + ( k - last_k ) + " unreachable_risers_dropped=" + ( c - last_c ) + " far_risers_skipped=" + ( f - last_f )
			+ " all_unreachable_fallbacks=" + ( o - last_o ) );
		last_k = k;
		last_c = c;
		last_o = o;
		last_f = f;
	}
}

// The proven PrintLn pattern (CLAUDE.md dev diagnostics): assemble outside the
// developer block, print inside it.
function reach_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_REACH] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
