// =============================================================================
// _tod_stray.gsc — THE HUNT: no zombie stays where it cannot get to you.
// (docs/200, THE PURSUIT — the zombie half. The player half is _tod_recall.gsc,
// and both ask _tod_reach.gsc whether a walk exists.)
//
// REV 2 (2026-10-02), user: "zombies not being able to trace or target players
// ... many places where you can jump off ... zombies will be super far away. We
// need a foolproof solution ... The other map had the kind of solution, but I
// think the distance ... was a little bit too big. So sometimes it'll slow down
// the game ... cut that distance ... more fast-paced instead of waiting around
// when you try to teleport and things like that."
//
// WHAT REV 1 (TOD1's v14.45 module, inherited at the seed) COULD NOT SEE:
//   1. THE DROPS. It measured "too far" as a straight cost (2D + 4 x |dz|) and
//      had no notion that 24 laps of this tower are one-way. A zombie on a catch
//      deck 190 below the player scored ~760 — "near" — and was left there for
//      good: it could not climb and nothing moved it. Worse, its destinations had
//      the same blind spot, so a relocation could put a zombie BACK below a drop.
//      (2026-10-01 run: zombie born on lap 43's deck, player on the ledge above,
//      the engine's own CanPath = 0.)
//   2. THE DISTANCE. 6000 cost = four laps of stairs and 8 s of patience before a
//      move. User: too big. Rev 2 moves a zombie that is more than about a floor
//      and a half of stairs from every player it can reach, after 3 s.
// REV 2 LANES, in order of urgency:
//   UNREACH — no living upright player is reachable (tod_reach::can_reach): moved
//             after 1.5 s. This is the drop case, the crown-island case and any
//             co-op split the zombie is on the wrong side of.
//   FAR     — reachable, but the cheapest reachable walk costs > TOD_STRAY_COST:
//             moved after 3 s (waived while a teleport pump drains).
//   IDLE    — near and reachable on paper, but standing still with no path and
//             nothing in swing range for 4 s: the engine is asked (CanPath) and it
//             is moved at once if the engine agrees it cannot walk there, else it
//             gets one re-goal first. Catches what the model cannot see (a seam,
//             a shut door inside the crown).
//   RISE    — a climb-out that never finished (unchanged from rev 1).
// WHERE THEY GO: an authored riser in a live zone that can REACH the player and is
// within TOD_STRAY_COST of him — the engine double-checks the walk (CanPath) on up
// to TOD_STRAY_PROBES candidates — and, when no riser qualifies, any navmesh point
// in a ring round the player (stock's climb-out needs only an origin and angles,
// so the arrival looks the same). Unseen spots first; seen ones once desperate.
// LAST RESORT: an unreachable zombie with nowhere legal to go for 15 s is despawned
// and REFUNDED (zombie_total + 1 — stock zm_giant_cleanup_mgr's own recipe, and
// the Battle Arena's hold_tower already does the same). Rev 1 refused to touch the
// round count at all; a refund of one zombie delays the next round by one spawn,
// and the alternative is a statue holding an actor slot for the rest of the match.
// IT NEVER VANISHES IN YOUR FACE: a zombie on someone's screen is not moved until
// it is desperate, and then it dissolves (the doors' derez burst) instead of
// blinking out.
//
// UNCHANGED FROM REV 1, AND WHY (the long notes are in git history):
//   * TELEPORT, NOT KILL — health and every card mark survive.
//   * THEY CLIMB OUT — relocate() replays stock's _zm_spawner::do_zombie_rise.
//   * rise_cleanup_guard plugs stock's orphaned-anchor leak on a mid-rise death.
//   * THE STALLED CLIMB-OUT watchdog (rise_watch / force_risen).
//   * Stand-downs for the world pause (the finale's sealed states retired 2026-10-05).
// =============================================================================

#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;

#using scripts\shared\array_shared;               // array::random / randomize — spread the destinations
#using scripts\shared\ai\zombie_utility;
// do_zombie_rise: stock's OWN riser climb-out, replayed on a relocated zombie so
// it emerges instead of materialising. It imports no tod module.
#using scripts\zm\_zm_spawner;

#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;
#using scripts\zm\zm_tod2_cybercity\_tod_zombie_speed;   // gait re-assert after a teleport
#using scripts\zm\zm_tod2_cybercity\_tod_reach;          // THE PURSUIT's walk model (docs/200)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;   // derez_burst — the tell when a seen zombie is moved

#insert scripts\shared\shared.gsh;

#namespace tod_stray;

// ---------------------------------------------------------------------------
// THE POLICY (rev 2 — every number the user tunes by feel is in this block)
// ---------------------------------------------------------------------------

// TOO FAR. Estimated walking cost (tod_reach::cost: 2D + 4 x |dz|) of the
// cheapest REACHABLE player. 2400 is about a floor and a half of stairs, or
// ~15-20 s of walking. Rev 1 (TOD1) was 6000 = four laps; user 2026-10-02: "cut
// that distance". The tower's cross-section never reaches 1700, so on the spiral
// this is a vertical rule; the crown hall (1536 square) fits inside it whole.
#define TOD_STRAY_COST          2400

// How long a zombie must stay too far before it moves (rev 1: 8000).
#define TOD_STRAY_PATIENCE      3000

// How long a zombie that can reach NOBODY waits (drops, island, wrong side).
#define TOD_STRAY_UNREACH_MS    1500

// Stock's grace period for a fresh spawn (zm_giant_cleanup_mgr.gsc
// N_CLEANUP_AGE_MIN is 5000; shorter here — a fresh riser below a drop is exactly
// the zombie this exists to move).
#define TOD_STRAY_MIN_AGE       3000

// ...and stock's escape from its "has it entered play yet" guard
// (N_CLEANUP_AGE_TIMEOUT). Past this age the stamp is no longer required — the
// inert-ship insurance (see eligible()).
#define TOD_STRAY_AGE_TIMEOUT   45000

// After a move, leave it alone for this long.
#define TOD_STRAY_COOL          5000

// Stray this long: a SEEN destination is allowed, and a zombie that is itself on
// screen may be moved (it dissolves). Rev 1: 12000.
#define TOD_STRAY_DESPERATE     6000

// Unreachable this long with nowhere legal to go: despawn + refund (header).
#define TOD_STRAY_RECYCLE_MS    15000

#define TOD_STRAY_SWEEP         1.0     // seconds between sweeps (rev 1: 2.0)
#define TOD_STRAY_RUSH_SWEEP    0.5     // ...while a teleport pump is draining
#define TOD_STRAY_RUSH_MS       12000   // how long a pump keeps the fast cadence
#define TOD_STRAY_PER_TICK      4       // moves per normal sweep (now every 1 s — twice rev 1's rate)
#define TOD_STRAY_RUSH_TICK     10      // ...per rushed sweep

// cos(40) — stock's FOV test, verbatim (zm_giant_cleanup_mgr.gsc player_can_see_me).
#define TOD_STRAY_FOV_COS       0.766
// Never land one closer than this to ANY player (a bit over one second of sprint).
#define TOD_STRAY_DEST_MIN      280
// The fallback ring round the player when no riser qualifies, and its
// half-height (one flight — the floors above/below are filtered by reach + CanPath).
#define TOD_STRAY_QUERY_OUTER   900
#define TOD_STRAY_QUERY_HEIGHT  192
// A zombie farther than this from a viewer is a few pixels: moving it is not "seen".
#define TOD_STRAY_SEEN_DIST     2200
// CanPath second opinions per move attempt (each is an engine path query).
#define TOD_STRAY_PROBES        3
// A player who moved this far between two half-second samples was teleported
// (a teleporter ride, the arena, the jump pad landing, a recall): pump.
#define TOD_STRAY_JUMP_DIST     1500
// Dev summary cadence.
#define TOD_STRAY_SUMMARY_MS    15000

// ---------------------------------------------------------------------------
// THE IDLE LANE (2026-09-04, rev 2 tightened) — user then: "enemies just cant
// target you so they just stand still". The distance lanes clear a near zombie as
// healthy; this lane asks whether a near zombie is actually DOING anything.
// ---------------------------------------------------------------------------
#define TOD_STRAY_IDLE_MS       4000    // no meaningful movement this long = idle (rev 1: 6000)
#define TOD_STRAY_IDLE_DIST     48      // movement under this between sweeps is "not moving"
#define TOD_STRAY_IDLE_MELEE    96      // this close to its target = swinging, not stuck
#define TOD_STRAY_IDLE_TRIES    1       // free re-goal passes before it moves (rev 1: 2)
// ITS OWN BUDGET (rev 1's reasoning): an idle rescue can cost a CanPath, a navmesh
// clamp and a ForceTeleport, so it must not ride the distance lanes' budget.
#define TOD_STRAY_IDLE_PER_TICK 2

// ---------------------------------------------------------------------------
// THE STALLED CLIMB-OUT (2026-09-04, unchanged) — a riser that never finishes its
// climb-out is a statue with no FindFlesh service; see force_risen().
// ---------------------------------------------------------------------------
#define TOD_STRAY_RISE_MS       14000   // a climb-out is ~2 s; 14 is "this is never finishing"
#define TOD_STRAY_RISE_SWEEP    2.0

function init()
{
	level endon( "end_game" );
	tod_reach::init();   // idempotent — main() normally ran it already
	level.tod_hunt_n = [];
	level flag::wait_till( "initial_blackscreen_passed" );
	level thread stray_sweep();
	level thread pump_watch();
	level thread rise_watch();
	level thread jump_watch();
	level thread summary_watch();
	hunt_log( "INIT rev=2 cost=" + TOD_STRAY_COST + " patience_ms=" + TOD_STRAY_PATIENCE + " unreach_ms=" + TOD_STRAY_UNREACH_MS
		+ " idle_ms=" + TOD_STRAY_IDLE_MS + " desperate_ms=" + TOD_STRAY_DESPERATE + " recycle_ms=" + TOD_STRAY_RECYCLE_MS
		+ " sweep=" + TOD_STRAY_SWEEP + " per_tick=" + TOD_STRAY_PER_TICK );
}

// ---------------------------------------------------------------------------
// THE STALLED CLIMB-OUT WATCHDOG. Deliberately its OWN sweep and not a lane in
// stray_sweep: that function stands down for the upgrade pause and the sealed
// states, and a rise stalls most easily during exactly those. It reads
// GetAITeamArray rather than get_round_enemy_array so a zombie that never joined
// the round's enemy set is still covered.
// ---------------------------------------------------------------------------
function rise_watch()
{
	level endon( "end_game" );

	for ( ;; )
	{
		wait TOD_STRAY_RISE_SWEEP;

		team = ( ( isdefined( level.zombie_team ) ) ? level.zombie_team : "axis" );
		ai = GetAITeamArray( team );
		if ( !isdefined( ai ) )
			continue;

		now = GetTime();
		for ( i = 0; i < ai.size; i++ )
		{
			z = ai[ i ];
			if ( !isdefined( z ) || !isalive( z ) )
				continue;
			if ( !IS_TRUE( z.in_the_ground ) )
			{
				z.tod_rise_since = undefined;
				continue;
			}
			// A boss is never a riser (direct SpawnActor drops) and drop_in owns
			// its own anim rate — never reach into that.
			if ( IS_TRUE( z.is_boss ) || isdefined( z.tod_boss_kind ) || IS_TRUE( z.tod_dropping ) )
				continue;
			// Widow's Wine's cocoon and Time Warp scale the animation rate, so a
			// climb-out under one is SUPPOSED to take longer — hold the clock.
			if ( IS_TRUE( z.b_widows_wine_cocoon ) || ( z tod_zombie_speed::under_anim_slow() ) )
			{
				z.tod_rise_since = now;
				continue;
			}

			if ( !isdefined( z.tod_rise_since ) )
			{
				z.tod_rise_since = now;
				continue;
			}
			// A world pause is not a stall — HOLD the clock by pushing the start
			// forward one sweep (re-stamping to now would let frequent card picks
			// defer the rescue forever).
			if ( IS_TRUE( level.tod_upgrade_pause ) )
			{
				z.tod_rise_since = z.tod_rise_since + ( TOD_STRAY_RISE_SWEEP * 1000 );
				continue;
			}
			if ( ( now - z.tod_rise_since ) < TOD_STRAY_RISE_MS )
				continue;

			z force_risen();
			WAIT_SERVER_FRAME;
		}
	}
}

// self = a zombie whose climb-out has stalled. Complete the rise by hand, in
// do_zombie_rise's own order, so the zombie joins the behaviour tree. Every call
// here is one stock already makes on this path (rev 1 lists each line's source).
function force_risen()
{
	if ( isdefined( self.anchor ) )
	{
		self Unlink();
		self.anchor Delete();
	}
	self StopAnimScripted();
	self Show();
	// STOCK'S OWN LINE, AND NOT OPTIONAL (_zm_spawner.gsc:3052): without it,
	// zombie_utility::zombie_rise_death stays parked for the zombie's life and
	// later plays the sink-into-the-ground death on a walking zombie.
	self notify( "rise_anim_finished" );
	self.in_the_ground = false;
	self.tod_rise_since = undefined;
	self notify( "risen", "find_flesh" );

	if ( !( self tod_zombie_speed::under_anim_slow() ) )
		self tod_zombie_speed::apply_speed_for_round( tod_zombie_speed::current_round() );

	tally( "rise" );
	hunt_log( "RISE_FORCED at=" + fmt( self.origin ) + " cell=" + tod_reach::describe( self.origin ) );
}

// THE TELEPORTER PUMP. _tod_teleport::do_teleport fires "tod_stray_pump" after a
// ride (and jump_watch below fires it for any other script teleport), which is
// the one moment we KNOW a party just left. The zone manager needs ~1 s to
// rebuild the riser pool round the arrival, so we hold 1.5 s, then run hot.
function pump_watch()
{
	level endon( "end_game" );
	for ( ;; )
	{
		level waittill( "tod_stray_pump" );
		// RE-ARM ON THE SAME FRAME: a second ride inside the 1.5 s hold must not
		// be dropped (two rides within 1.5 s is ordinary co-op).
		level thread pump_arm();
	}
}

function pump_arm()
{
	level endon( "end_game" );
	wait 1.5;
	level.tod_stray_rush = GetTime() + TOD_STRAY_RUSH_MS;
	tally( "pump" );
	hunt_log( "PUMP rush_ms=" + TOD_STRAY_RUSH_MS );
}

function rushing()
{
	return ( isdefined( level.tod_stray_rush ) && GetTime() < level.tod_stray_rush );
}

// ANY PLAYER TELEPORT PUMPS (rev 2). Only the teleporter pads notified before;
// the arena's return, the jump pad's landing, a recall and the bottom return pad
// all move a player thousands of units without one. Sampling positions catches
// every one of them, present and future, without a line in their files.
function jump_watch()
{
	level endon( "end_game" );
	last = [];
	for ( ;; )
	{
		wait 0.5;
		players = GetPlayers();
		jumped = false;
		for ( i = 0; i < players.size; i++ )
		{
			p = players[ i ];
			if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
				continue;
			n = p GetEntityNumber();
			if ( isdefined( last[ n ] ) && DistanceSquared( p.origin, last[ n ] ) > TOD_STRAY_JUMP_DIST * TOD_STRAY_JUMP_DIST )
				jumped = true;
			last[ n ] = p.origin;
		}
		if ( jumped )
			level notify( "tod_stray_pump" );
	}
}

function stray_sweep()
{
	level endon( "end_game" );

	for ( ;; )
	{
		wait ( ( rushing() ) ? TOD_STRAY_RUSH_SWEEP : TOD_STRAY_SWEEP );

		// STAND-DOWNS (rev 1): the world pause (a card pick, a shop spin, a station
		// buy) — moving anything now is visible in a still frame and fights the
		// freeze. (The parked finale's sealed states, which also stood it down,
		// retired whole with the Map One ending, 2026-10-05.)
		// A STAND-DOWN MUST NOT LOOK LIKE IDLING: bank a re-baseline of the motion
		// stamp so the first live sweep after a 15 s card pick does not read the
		// whole horde as motionless for 15 s.
		if ( IS_TRUE( level.tod_upgrade_pause ) )
		{
			level.tod_stray_rebase = true;
			continue;
		}

		zombies = zombie_utility::get_round_enemy_array();
		if ( !isdefined( zombies ) || zombies.size == 0 )
			continue;

		ups = upright_players();
		if ( ups.size == 0 )
			continue;   // nobody upright — leave the map alone (a crawler must not summon the horde)

		budget = ( ( rushing() ) ? TOD_STRAY_RUSH_TICK : TOD_STRAY_PER_TICK );
		idle_budget = TOD_STRAY_IDLE_PER_TICK;
		now = GetTime();

		// THE MOTION STAMP — the idle lane's only input — gets its OWN unbudgeted
		// pass over every zombie, so the tail of a busy sweep never keeps a stale
		// stamp and reads as "motionless" next time (rev 1's reasoning).
		rebase = IS_TRUE( level.tod_stray_rebase );
		level.tod_stray_rebase = undefined;
		for ( i = 0; i < zombies.size; i++ )
		{
			z = zombies[ i ];
			if ( !isdefined( z ) || !isalive( z ) )
				continue;
			if ( rebase || !isdefined( z.tod_idle_org ) || Distance( z.origin, z.tod_idle_org ) > TOD_STRAY_IDLE_DIST )
			{
				z.tod_idle_org   = z.origin;
				z.tod_idle_since = now;
				z.tod_idle_tries = undefined;
				z.tod_nopath_since = undefined;
			}
		}

		for ( i = 0; i < zombies.size; i++ )
		{
			if ( budget <= 0 )
				break;
			z = zombies[ i ];
			if ( !isdefined( z ) || !isalive( z ) )
				continue;
			if ( !( z eligible( now ) ) )
				continue;

			// WHO, AND CAN IT GET THERE. `target` is the nearest upright player by
			// walking cost — where a move would put it. `rbest` / `rtarget` are the
			// cost and the player of the cheapest walk it can actually REACH (-1 /
			// undefined: nobody).
			target = undefined;
			tc = 0;
			rbest = -1;
			rtarget = undefined;
			for ( j = 0; j < ups.size; j++ )
			{
				pt = tod_reach::reach_point( ups[ j ] );
				c = tod_reach::cost( z.origin, pt );
				if ( !isdefined( target ) || c < tc )
				{
					target = ups[ j ];
					tc = c;
				}
				if ( ( rbest < 0 || c < rbest ) && tod_reach::can_reach( z.origin, pt ) )
				{
					rbest = c;
					rtarget = ups[ j ];
				}
			}

			lane = lane_of( rbest );

			if ( lane == "" )
			{
				z.tod_stray_since = undefined;
				// NEAR IS NOT THE SAME AS HEALTHY (rev 1's lesson): a statue in front
				// of a player is near. The idle lane asks whether it is doing anything.
				if ( idle_budget > 0 && z idle_stuck( now ) )
				{
					idle_budget--;               // charged per ATTEMPT, not per move
					// The player it CAN reach — re-goal and destinations are his.
					if ( z idle_rescue( now, rtarget ) )
						budget--;
					WAIT_SERVER_FRAME;           // ...and every attempt costs a frame
				}
				continue;
			}

			if ( !isdefined( z.tod_stray_since ) )
			{
				z.tod_stray_since = now;
				continue;
			}
			waited = now - z.tod_stray_since;
			if ( !due( lane, waited, rushing() ) )
				continue;

			// DESPERATE (rev 1's v16.77 lesson, kept): after a teleport the arrival
			// pose faces the room, so "unseen only" is never achievable — a pump or
			// a long wait allows a seen spot (still never inside DEST_MIN).
			desperate = ( rushing() || waited >= TOD_STRAY_DESPERATE );
			seen = z on_screen();
			if ( seen && !desperate )
				continue;   // it would vanish in front of someone — let it be until it must

			spot = z pick_destination( target, desperate );
			if ( !isdefined( spot ) )
			{
				if ( lane == "unreach" && waited >= TOD_STRAY_RECYCLE_MS )
				{
					z recycle( waited, target );
					budget--;
				}
				else
					no_dest_note( z, lane, waited, target );
				continue;
			}

			z relocate( spot, target, lane, waited, seen );
			budget--;
			WAIT_SERVER_FRAME;      // spread the work, stock's own pacing habit
		}
	}
}

// PURE (tools/test_pursuit.js runs these): which lane a zombie is in, from the
// cost of its cheapest REACHABLE walk (-1 = it can reach nobody).
function lane_of( rbest )
{
	if ( rbest < 0 )
		return "unreach";
	if ( rbest > TOD_STRAY_COST )
		return "far";
	return "";
}

// PURE: has a zombie in `lane` waited long enough to be moved? A teleport pump
// waives the wait (the party just left; the horde should arrive, not walk).
function due( lane, waited, rush )
{
	if ( rush )
		return true;
	if ( lane == "unreach" )
		return ( waited >= TOD_STRAY_UNREACH_MS );
	return ( waited >= TOD_STRAY_PATIENCE );
}

// self = a live trash zombie. get_round_enemy_array() already excludes every
// elite (ignore_enemy_count); the rest are STATE guards: an actor mid-animation
// must not be moved out from under the animation.
function eligible( now )
{
	if ( IS_TRUE( self.is_boss ) || isdefined( self.tod_boss_kind ) )
		return false;                       // belt + braces over ignore_enemy_count
	if ( isdefined( level.zombie_team ) && self.team !== level.zombie_team )
		return false;                       // a Necromancer's helper or a partner is never ours to move
	if ( IS_TRUE( self.tod_frozen ) )
		return false;
	if ( IS_TRUE( self.in_the_ground ) )
		return false;                       // still climbing out (stock's own exclusion)

	// AGE, stock's two-stage shape (zm_giant_cleanup_mgr.gsc:129-147): a grace
	// period always, and "has it entered play yet" only while young. The second
	// stage MUST expire (TOD_STRAY_AGE_TIMEOUT), or a map whose risers never set
	// the stamp would ship this whole module doing nothing.
	age = ( ( isdefined( self.spawn_time ) ) ? ( now - self.spawn_time ) : TOD_STRAY_AGE_TIMEOUT );
	if ( age < TOD_STRAY_MIN_AGE )
		return false;
	if ( age < TOD_STRAY_AGE_TIMEOUT
	  && !IS_TRUE( self.completed_emerging_into_playable_area )
	  && self.script_string !== "find_flesh" )
		return false;

	if ( isdefined( self.tod_stray_cool ) && now < self.tod_stray_cool )
		return false;
	// The field reads cannot throw (IsTraversing has one stock call site and
	// self.is_traversing is never set by BO3 — rev 1's note).
	if ( IS_TRUE( self.is_traversing ) )
		return false;                       // mid-traversal: the anim owns the origin
	if ( IS_TRUE( self.isInMantleAction ) )
		return false;
	if ( self GetPathMode() == "dont move" )
		return false;                       // a mocomp has it pinned
	// Widow's Wine owns a cocooned zombie's position and its FX are anchored to it.
	if ( IS_TRUE( self.b_widows_wine_cocoon ) )
		return false;
	if ( IS_TRUE( self.tod_dropping ) )
		return false;
	return true;
}

// self = an eligible trash zombie the distance lanes cleared as "near".
// -> true if it is a statue rather than a combatant.
function idle_stuck( now )
{
	if ( !isdefined( self.tod_idle_since ) )
		return false;
	if ( ( now - self.tod_idle_since ) < TOD_STRAY_IDLE_MS )
		return false;
	if ( self busy() )
		return false;
	// HasPath() is a real builtin here (_tod_bosses and archetype_zod_companion
	// both call it): a zombie holding a route is walking, just not far.
	if ( self HasPath() )
		return false;
	return true;
}

// IN SWING RANGE THE ORIGIN IS SUPPOSED TO BE STILL. Rev 1 only asked about
// PLAYERS; the 2026-10-01 run showed six zombies motionless on lap 1's stairs
// with their engine `enemy` set to a Necromancer helper — fighting it, not stuck.
// So: any player (downed included — a mob on a crawler is healthy), its own
// engine enemy, or its favourite.
function busy()
{
	victim = nearest_any( self.origin );
	if ( isdefined( victim ) && Distance( self.origin, victim.origin ) < TOD_STRAY_IDLE_MELEE )
		return true;
	if ( isdefined( self.enemy ) && isdefined( self.enemy.origin ) && Distance( self.origin, self.enemy.origin ) < TOD_STRAY_IDLE_MELEE )
		return true;
	if ( isdefined( self.favoriteenemy ) && isdefined( self.favoriteenemy.origin ) && Distance( self.origin, self.favoriteenemy.origin ) < TOD_STRAY_IDLE_MELEE )
		return true;
	return false;
}

// self = an idle zombie. -> true if a relocation budget slot was spent.
function idle_rescue( now, target )
{
	goal = tod_reach::reach_point( target );
	here = GetClosestPointOnNavMesh( self.origin, 48, 32 );

	// (a) ASK THE ENGINE. The model said reachable; if the engine says there is
	// no walk from where it stands, it is stranded on something the model cannot
	// see (a seam, a shut door inside the crown) — move it now.
	nopath = ( isdefined( here ) && !( self CanPath( here, goal ) ) );

	if ( !nopath )
	{
		self.tod_nopath_since = undefined;
		// (b) RE-GOAL + CLAMP: stock's strict projection can silently goal an
		// actor AT ITS OWN ORIGIN (the _tod_bosses::goal_driver ladder fixes that),
		// and a zombie a few units off the mesh is clamped back on it.
		g = GetClosestPointOnNavMesh( goal, 64, 30 );
		if ( !isdefined( g ) )
			g = GetClosestPointOnNavMesh( goal, 128, 15 );
		if ( !isdefined( g ) )
			g = GetClosestPointOnNavMesh( goal, 256, 0 );
		if ( isdefined( here ) && Distance( here, self.origin ) > 4 )
			self ForceTeleport( here, self.angles );
		if ( isdefined( g ) )
			self SetGoal( g );

		self.tod_idle_tries = ( ( isdefined( self.tod_idle_tries ) ) ? self.tod_idle_tries + 1 : 1 );
		if ( self.tod_idle_tries <= TOD_STRAY_IDLE_TRIES )
		{
			self.tod_idle_org   = self.origin;
			self.tod_idle_since = now;          // one more window for (b) to take
			return false;
		}
	}

	// (c) MOVE IT — desperate, so a player standing still cannot wedge the rescue
	// by keeping every riser in view (rev 1's v16.77 lesson); DEST_MIN is never
	// waived even then.
	lane = "idle";
	if ( nopath )
	{
		lane = "idle_nopath";
		if ( !isdefined( self.tod_nopath_since ) )
			self.tod_nopath_since = self.tod_idle_since;
	}
	waited = now - self.tod_idle_since;
	seen = self on_screen();
	spot = self pick_destination( target, true );
	if ( !isdefined( spot ) )
	{
		// The engine says it cannot walk, and there is nowhere legal to put it:
		// the same last resort as the unreach lane, on the same clock.
		if ( nopath && ( now - self.tod_nopath_since ) >= TOD_STRAY_RECYCLE_MS )
		{
			self recycle( now - self.tod_nopath_since, target );
			return true;
		}
		no_dest_note( self, lane, waited, target );
		self.tod_idle_since = now;
		return false;
	}
	self.tod_idle_org   = undefined;
	self.tod_idle_since = undefined;
	self.tod_idle_tries = undefined;
	self.tod_nopath_since = undefined;
	self relocate( spot, target, lane, waited, seen );
	return true;
}

// Living, playing, upright players — the only ones the horde is moved toward (a
// crawler must not be able to summon the horde onto himself, and a jump-pad flyer
// is mid-air between regions).
function upright_players()
{
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
		out[ out.size ] = p;
	}
	return out;
}

// The nearest player of ANY posture, INCLUDING last stand — the right rule for
// asking whether a zombie is BUSY (see busy()).
function nearest_any( org )
{
	best = undefined;
	best_d = 0;
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		if ( p.sessionstate == "spectator" )
			continue;
		d = DistanceSquared( org, p.origin );
		if ( !isdefined( best ) || d < best_d )
		{
			best = p;
			best_d = d;
		}
	}
	return best;
}

// -> true if ANY living, non-spectating player could have this point on screen.
// Stock's test verbatim (zm_giant_cleanup_mgr.gsc player_can_see_me): FOV only,
// no trace — conservative for a DESTINATION (an occluded spot counts as seen).
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
		if ( VectorDot( fwd, VectorNormalize( to ) ) >= TOD_STRAY_FOV_COS )
			return true;
	}
	return false;
}

// self = a zombie. -> true if a player is actually LOOKING at it: in the view
// cone, within TOD_STRAY_SEEN_DIST, and a sight trace from the eye gets there.
// The trace matters here (unlike seen_by_anyone): the question is whether moving
// THIS zombie would make something vanish on screen, and on a spiral the core
// hides most of the horde most of the time.
function on_screen()
{
	org = self.origin + ( 0, 0, 40 );
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		if ( p.sessionstate == "spectator" )
			continue;
		eye = p GetEye();
		to = org - eye;
		d2 = LengthSquared( to );
		if ( d2 > TOD_STRAY_SEEN_DIST * TOD_STRAY_SEEN_DIST )
			continue;
		if ( d2 < 1 )
			return true;
		fwd = AnglesToForward( p GetPlayerAngles() );
		if ( VectorDot( fwd, VectorNormalize( to ) ) < TOD_STRAY_FOV_COS )
			continue;
		if ( SightTracePassed( eye, org, false, self ) )
			return true;
	}
	return false;
}

// -> true if org is closer than DEST_MIN to any living player (never waived).
function too_close( org )
{
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		if ( DistanceSquared( org, p.origin ) < TOD_STRAY_DEST_MIN * TOD_STRAY_DEST_MIN )
			return true;
	}
	return false;
}

// -> is org a legal place to climb out for a zombie that must reach `goal`?
// The causeway-gate rule is rev 1's (still the spawn selector's too); the reach
// and cost tests are rev 2's — never back below a drop, never still too far.
function dest_ok( org, goal )
{
	if ( !IS_TRUE( level.tod_gate_open ) && tod_crown_data::beyond_gate( org ) )
		return false;
	if ( !tod_reach::can_reach( org, goal ) )
		return false;
	if ( tod_reach::cost( org, goal ) > TOD_STRAY_COST )
		return false;
	if ( too_close( org ) )
		return false;
	// THE HAVENS (docs/202): never raise a zombie INSIDE a safe-zone field — the
	// horde has to walk in through it (and its slow). Guarded pointer: the haven
	// module owns the field and is never imported here.
	if ( isdefined( level.tod_haven_inside_fn ) && [[ level.tod_haven_inside_fn ]]( org ) )
		return false;
	return true;
}

// self = the zombie being moved (the agent the engine paths for). -> a spot
// struct (origin / angles / script_string) or undefined.
function pick_destination( target, desperate )
{
	goal = tod_reach::reach_point( target );

	// (1) THE AUTHORED RISERS in the live zones — stock's own pool, rebuilt every
	// second by the zone manager from the active zones round the players.
	if ( isdefined( level.zm_loc_types ) && isdefined( level.zm_loc_types[ "zombie_location" ] ) )
	{
		spots = level.zm_loc_types[ "zombie_location" ];
		unseen = [];
		seen = [];
		for ( i = 0; i < spots.size; i++ )
		{
			sp = spots[ i ];
			if ( !isdefined( sp ) || !isdefined( sp.origin ) )
				continue;
			if ( !dest_ok( sp.origin, goal ) )
				continue;
			if ( seen_by_anyone( sp.origin ) )
				seen[ seen.size ] = sp;
			else
				unseen[ unseen.size ] = sp;
		}
		pick = self first_pathable( unseen, goal );
		if ( !isdefined( pick ) && desperate )
			pick = self first_pathable( seen, goal );
		if ( isdefined( pick ) )
		{
			pick.tod_dest_kind = "riser";
			return pick;
		}
	}

	// (2) THE NAVMESH ROUND THE PLAYER. Stock's climb-out needs only an origin,
	// angles and a script_string (do_zombie_rise, zombie_rise_fx — read, not
	// assumed), so any walkable point looks like a riser on arrival. This is what
	// makes the hunt foolproof where the authored risers are thin: two per lap,
	// and on a drop lap one of them is the ledge.
	q = PositionQuery_Source_Navigation( goal, TOD_STRAY_DEST_MIN, TOD_STRAY_QUERY_OUTER, TOD_STRAY_QUERY_HEIGHT, 48 );
	if ( !isdefined( q ) || !isdefined( q.data ) || q.data.size == 0 )
		return undefined;
	unseen = [];
	seen = [];
	for ( i = 0; i < q.data.size; i++ )
	{
		org = q.data[ i ].origin;
		if ( !isdefined( org ) || !dest_ok( org, goal ) )
			continue;
		s = SpawnStruct();
		s.origin = org;
		yaw = 0;
		to = goal - org;
		to = ( to[ 0 ], to[ 1 ], 0 );
		if ( LengthSquared( to ) > 1 )
		{
			a = VectorToAngles( to );
			yaw = a[ 1 ];
		}
		s.angles = ( 0, yaw, 0 );
		s.script_string = "find_flesh";   // what every riser on this map carries (zombie_think reads it)
		if ( seen_by_anyone( org ) )
			seen[ seen.size ] = s;
		else
			unseen[ unseen.size ] = s;
	}
	pick = self first_pathable( unseen, goal );
	if ( !isdefined( pick ) && desperate )
		pick = self first_pathable( seen, goal );
	if ( isdefined( pick ) )
		pick.tod_dest_kind = "navmesh";
	return pick;
}

// self = the zombie. -> the first spot (in random order — rev 1's pile-up lesson)
// from which the engine confirms a walk to `goal`, after at most TOD_STRAY_PROBES
// engine path queries. The model already said yes; this is the second opinion.
function first_pathable( pool, goal )
{
	if ( !isdefined( pool ) || pool.size == 0 )
		return undefined;
	pool = array::randomize( pool );
	probes = 0;
	for ( i = 0; i < pool.size; i++ )
	{
		if ( probes >= TOD_STRAY_PROBES )
			break;
		a = GetClosestPointOnNavMesh( pool[ i ].origin, 48, 32 );
		if ( !isdefined( a ) )
			continue;
		probes++;
		if ( self CanPath( a, goal ) )
		{
			pool[ i ].tod_dest_nav = a;
			return pool[ i ];
		}
	}
	return undefined;
}

// self = the stray. spot = a riser or a synthesized navmesh spot.
function relocate( spot, target, lane, waited, seen )
{
	from = self.origin;
	// IT WAS ON SOMEONE'S SCREEN (only ever when desperate): it dissolves — the
	// doors' derez burst — instead of blinking out.
	if ( IS_TRUE( seen ) )
		tod_perk_scatter::derez_burst( from + ( 0, 0, 36 ) );

	self zombie_utility::reset_attack_spot();   // release the claimed spot back there

	dest = spot.tod_dest_nav;
	if ( !isdefined( dest ) )
		dest = GetClosestPointOnNavMesh( spot.origin, 48, 32 );
	if ( !isdefined( dest ) )
		dest = spot.origin;

	yaw = 0;
	to = target.origin - dest;
	to = ( to[ 0 ], to[ 1 ], 0 );
	if ( LengthSquared( to ) > 1 )
	{
		a = VectorToAngles( to );
		yaw = a[ 1 ];
	}
	self ForceTeleport( dest, ( 0, yaw, 0 ) );

	// Stock's own zone stamp for a spawn location (_zm_utility.gsc:205-208).
	if ( isdefined( spot.zone_name ) )
	{
		self.zone_name = spot.zone_name;
		self.previous_zone_name = spot.zone_name;
	}

	self.tod_stray_since = undefined;
	self.tod_stray_cool = GetTime() + TOD_STRAY_COOL;

	tally( lane );
	kind = "riser";
	if ( isdefined( spot.tod_dest_kind ) )
		kind = spot.tod_dest_kind;
	hunt_log( "MOVE lane=" + lane + " waited_ms=" + waited + " seen=" + IS_TRUE( seen ) + " dest=" + kind
		+ " from=" + fmt( from ) + " " + tod_reach::describe( from ) + " to=" + fmt( dest ) + " " + tod_reach::describe( dest )
		+ " target=" + target GetEntityNumber() + " " + tod_reach::describe( tod_reach::reach_point( target ) )
		+ " cost_after=" + int( tod_reach::cost( dest, tod_reach::reach_point( target ) ) ) );

	// THEY CLIMB OUT (rev 1, v14.45): the giveaway of a teleport is the absence of
	// an arrival, so the arrival is supplied.
	self thread rise_in( spot, target );
}

// LAST RESORT — an unreachable zombie with nowhere legal to go for
// TOD_STRAY_RECYCLE_MS. Despawn and refund it: stock zm_giant_cleanup_mgr's
// delete_zombie_noone_looking recipe (zombie_total++ / zombie_respawns++) with
// the Battle Arena's plain Delete (_tod_arena::hold_tower, proven in play).
function recycle( waited, target )
{
	from = self.origin;
	self zombie_utility::reset_attack_spot();
	if ( isdefined( level.zombie_total ) )
		level.zombie_total++;
	if ( isdefined( level.zombie_respawns ) )
		level.zombie_respawns++;
	tally( "recycle" );
	hunt_log( "RECYCLE waited_ms=" + waited + " at=" + fmt( from ) + " " + tod_reach::describe( from )
		+ " target=" + target GetEntityNumber() + " " + tod_reach::describe( tod_reach::reach_point( target ) ) + " refunded=1" );
	self Delete();
}

// One line per zombie per stall, not one per sweep.
function no_dest_note( z, lane, waited, target )
{
	tally( "no_dest" );
	if ( isdefined( z.tod_hunt_nodest_ms ) && ( GetTime() - z.tod_hunt_nodest_ms ) < 5000 )
		return;
	z.tod_hunt_nodest_ms = GetTime();
	hunt_log( "NO_DEST lane=" + lane + " waited_ms=" + waited + " at=" + fmt( z.origin ) + " " + tod_reach::describe( z.origin )
		+ " target=" + target GetEntityNumber() + " " + tod_reach::describe( tod_reach::reach_point( target ) ) );
}

// self = the relocated zombie. Play stock's own riser climb-out at `spot`, then
// hand the zombie back to the behaviour tree. Called synchronously inside our own
// thread so the SetGoal lands AFTER the climb-out; do_zombie_rise's own
// self endon("death") ends this thread too.
function rise_in( spot, target )
{
	self endon( "death" );

	self thread rise_cleanup_guard();
	self zm_spawner::do_zombie_rise( spot );

	// Move THIS frame rather than on the next find-flesh service tick — the
	// goal_driver ladder, AFTER the rise (never a goal set into a scripted anim).
	if ( isdefined( target ) )
	{
		g = GetClosestPointOnNavMesh( tod_reach::reach_point( target ), 64, 30 );
		if ( !isdefined( g ) )
			g = GetClosestPointOnNavMesh( target.origin, 128, 15 );
		if ( isdefined( g ) )
			self SetGoal( g );
	}

	// ForceTeleport and the scripted rise can both reset the ASM rate; GUARDED
	// because apply_speed_for_round has no under_anim_slow check of its own.
	if ( !( self tod_zombie_speed::under_anim_slow() ) )
		self tod_zombie_speed::apply_speed_for_round( tod_zombie_speed::current_round() );
}

// self = the relocated zombie. Deletes the rise ANCHOR if the zombie dies
// mid-climb-out — stock's do_zombie_rise orphans its script_origin on a death in
// its ~0.1 s move window, and relocations fire continuously on a map whose
// ~1024-slot gentity table is a binding constraint (rev 1's peer-review find).
function rise_cleanup_guard()
{
	self endon( "risen" );

	self waittill( "death" );

	if ( !isdefined( self ) )
		return;
	if ( isdefined( self.anchor ) )
		self.anchor Delete();
	self.in_the_ground = undefined;
}

// ---------------------------------------------------------------------------
// DIAGNOSTICS (CLAUDE.md dev-mode rule): every move, recycle and no-destination
// is one [TOD_HUNT] line with the lane, the wait, both cells and the target; a
// SUMMARY every 15 s while anything happened.
// ---------------------------------------------------------------------------
function tally( key )
{
	if ( !isdefined( level.tod_hunt_n ) )
		level.tod_hunt_n = [];
	if ( !isdefined( level.tod_hunt_n[ key ] ) )
		level.tod_hunt_n[ key ] = 0;
	level.tod_hunt_n[ key ]++;
}

function summary_watch()
{
	level endon( "end_game" );
	last = "";
	for ( ;; )
	{
		wait ( TOD_STRAY_SUMMARY_MS / 1000 );
		line = "";
		keys = GetArrayKeys( level.tod_hunt_n );
		for ( i = 0; i < keys.size; i++ )
			line = line + " " + keys[ i ] + "=" + level.tod_hunt_n[ keys[ i ] ];
		if ( line == last )
			continue;
		last = line;
		hunt_log( "SUMMARY totals:" + line + " rushing=" + rushing() );
	}
}

function fmt( v )
{
	if ( !isdefined( v ) )
		return "none";
	return "(" + int( v[ 0 ] ) + " " + int( v[ 1 ] ) + " " + int( v[ 2 ] ) + ")";
}

function hunt_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_HUNT] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
