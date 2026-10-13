// =============================================================================
// _tod_lucky.gsc — THE LUCKY CLOVER + THE LUCKY METEOR (2026-09-29, docs/197).
//
// The user, after the kill budget went to 12 a round: "I would like to add a golden zombie
// that has a 1% chance of spawning and give 3 bars to the killer ... Build this, lucky
// meteor and lucky die drop. It should be a lucky clover model and act just like regular
// drops that have the white glow" ... "Things like perk bottle pap all have the white glow,
// Zombie blood." (The golden zombie is its own module, _tod_golden_zombie.gsc.)
//
// THE LUCKY CLOVER — a power-up (Blender-authored model TOD_CLOVER_MODEL). The grabber gets
//   TOD_CLOVER_BARS luck bars (tod_luck::add_bars: one segment at a time, the pip ladder
//   climbing). It is registered EXACTLY like the map's other grabber-only drops (the perk
//   bottle, the PaP drop, Zombie Blood): POWERUP_ONLY_AFFECTS_GRABBER is what gives it
//   stock's "solo" glow, the pale white-blue one the user means. Anyone can pick it up;
//   only the grabber gains. It drops two ways:
//     * in the normal random drops, at TOD_CLOVER_DROP_PCT of a regular drop's share (the
//       same per-roll gate the PaP drop uses: stock re-rolls a refused pick, so the total
//       drop rate is unchanged and only the mix moves — _tod_powerups' DROP RATES note);
//     * every time a Lucky Meteor is shot down (below).
//
// THE LUCKY METEOR — every TOD_METEOR_EVERY rounds (from round TOD_METEOR_FIRST_ROUND) a
//   burning gold meteor crosses the sky LOW over the party: a real server script_model at real
//   scale inside the sealed sky box, so EVERY player sees the same rock (the sky fleet is
//   client-only scenery drawn separately on each screen — nothing there can be shot). Its
//   pass is planned from one upright player (the FOCUS): a straight chord TOD_METEOR_SWEEP
//   degrees of bearing wide, TOD_METEOR_DIST out, TOD_METEOR_ALT above them, falling
//   TOD_METEOR_DROP across the pass, traced clear of every brush (five parallel lines as wide
//   as the rock) and in line of sight from the focus for most of the pass. It stays under the
//   sky fleet's asteroid band (their rocks drift above 22 degrees of elevation).
//   SHOOTING IT: every weapon_fired runs the view ray (the _tod_secret bears' test): the ray
//   must pass within TOD_METEOR_HIT_R of the rock, in front, with a clear line to it. Any
//   gun, bow or staff counts; the WARRIOR (class key "slasher") cannot: its primaries are
//   fists and blades, and a punch aimed at the sky must not break a rock 5000 units away.
//   THE BREAK: a gold burst + a boom everyone hears; the shooter hears the headshot ding; a
//   glowing clover fragment streaks from the burst to an open-air point beside the shooter
//   (TOD_CLOVER_APPROACH out, TOD_CLOVER_APPROACH_UP up; every leg traced), drops the last
//   stretch onto the floor and lands as the Lucky Clover (specific_powerup_drop, which
//   places the power-up 40 above the spot — the fragment ends its flight exactly there).
//   MISSED: it finishes its pass and flies on out of sight.
//   PAUSES WITH THE WORLD: the flight advances only while no card deal holds the world
//   (level.tod_upgrade_pause), so a deal mid-pass never costs the party its meteor.
//
// Dev logs (level.tod_dev or level.tod_diag): [TOD_LUCKY] READY / CLOVER_DROP / CLOVER_GRAB / METEOR_ROUND /
//   METEOR_PLAN_FAIL / METEOR_SPAWN / METEOR_HIT / METEOR_MISS / METEOR_LAND. READY carries rev= (the precache fix's
//   marker) and METEOR_SPAWN / METEOR_HIT / METEOR_LAND name the effect they bind (trail= / burst= / land=): a
//   SCRIPTERROR "effect ... was not precached" in the same millisecond as one of them names the effect the linker
//   left out of the precache table.
// =============================================================================

#using scripts\codescripts\struct;
#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;

#using scripts\zm\_zm_powerups;

#using scripts\zm\zm_tod2_cybercity\_tod_luck;            // add_bars (the clover's payout)
#using scripts\zm\zm_tod2_cybercity\_tod_killconfirm;     // ding (the shooter's hit confirm)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;    // play_sound_at_origin (the map's proven 3D sound lane)

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#insert scripts\zm\_zm_powerups.gsh;

// NO EMPTY-NAME PRECACHE HERE (2026-10-05, LT-fix / LT-meteor). A string precache with an EMPTY name stood first in
// this block from 2026-09-29, and the linker never put ANY of this file's effects into the map's precache table (the
// bgcache asset in the .ff, decoded: 109 server effects, every other module's present, these four absent), so every
// meteor threw "effect tod/luck/fx_luck_meteor_trail was not precached" and flew with no trail (all 19 meteors
// archived, 7 sessions, 09-30..10-05). The mechanism, read off the table: the linker flattens a file's #precache
// arguments into one list and drops the empty name, so the list shifts by one - the next directive's TYPE ("model")
// was stored as a bogus string, and every later directive in the file was read as a (name, type) pair with an invalid
// type and thrown away. The models below survived only because their zone xmodel lines feed the table too. The blank
// localized hint that add_zombie_powerup takes needs no precache: stock only stores it (struct.hint). Directives
// BEFORE an empty name, or an empty name that is a file's LAST directive, lose nothing. tools/lucky/test_lucky.js
// refuses a literal empty name in scripts/ and any empty name (#define-resolved too) with a directive after it;
// tools/verify_bgcache.py proves the linked table after a build.
#precache( "model", "tod_luck_clover" );
#precache( "model", "tod_luck_meteor" );
#precache( "model", "tag_origin" );
#precache( "fx", "tod/luck/fx_luck_meteor_trail" );
#precache( "fx", "tod/luck/fx_luck_meteor_burst" );
#precache( "fx", "tod/luck/fx_luck_clover_trail" );
#precache( "fx", "tod/luck/fx_luck_clover_land" );

#namespace tod_lucky;

// ---- the clover (LOCKSTEP: the powerup name with _tod_lucky.csc) -------------------------
#define TOD_CLOVER_NAME          "tod_luck_clover"
#define TOD_CLOVER_MODEL         "tod_luck_clover"
#define TOD_CLOVER_BARS          3        // user: "give you maybe like three luck bars" -> "1. Yes"
#define TOD_CLOVER_DROP_PCT      50       // share of a regular drop's slot in the random drops (0 = meteor only)
#define TOD_CLOVER_GRAB_SND      "tod_spin_luck"   // the Black Market's "the luck pours in" (docs/194 M3)

// ---- the meteor ---------------------------------------------------------------------------
#define TOD_METEOR_MODEL         "tod_luck_meteor"
#define TOD_METEOR_FX_TRAIL      "tod/luck/fx_luck_meteor_trail"
#define TOD_METEOR_FX_BURST      "tod/luck/fx_luck_meteor_burst"
#define TOD_CLOVER_FX_TRAIL      "tod/luck/fx_luck_clover_trail"
#define TOD_CLOVER_FX_LAND       "tod/luck/fx_luck_clover_land"
#define TOD_METEOR_SND_ANNOUNCE  "tod_luck_meteor_announce"   // 2D, every player: look up
#define TOD_METEOR_SND_LOOP      "tod_luck_meteor_loop"       // 3D loop on the rock: find it by ear
#define TOD_METEOR_SND_BURST     "tod_luck_meteor_burst"      // 3D, carries the whole tower
#define TOD_CLOVER_SND_FALL      "tod_luck_clover_fall"       // 3D loop on the falling fragment
#define TOD_CLOVER_SND_LAND      "tod_luck_clover_land"       // 3D, the touch-down

#define TOD_METEOR_EVERY         2        // one meteor every this many rounds ...
#define TOD_METEOR_FIRST_ROUND   3        // ... from this round (after the opening deal)
#define TOD_METEOR_DELAY_MIN     12       // unpaused seconds into its round before it may appear
#define TOD_METEOR_DELAY_MAX     45
#define TOD_METEOR_RETRY_SECS    8        // a refused launch (paused, arena, no clear pass) tries again
#define TOD_METEOR_FLIGHT_SECS   13.0     // unpaused seconds across the pass
#define TOD_METEOR_TICK          0.1
#define TOD_METEOR_DIST_MIN      4500     // the pass's end points, this far from the focus ...
#define TOD_METEOR_DIST_MAX      6500     // (the chord's middle comes to ~0.77 of it at the default sweep)
#define TOD_METEOR_ALT_MIN       500      // ... this high above the focus's feet (mid-pass)
#define TOD_METEOR_ALT_MAX       1400
#define TOD_METEOR_SWEEP         80       // degrees of bearing the pass covers
#define TOD_METEOR_DROP          600      // height lost from one end of the pass to the other
#define TOD_METEOR_RADIUS        150      // the rock's size: the clearance traces run this wide
#define TOD_METEOR_HIT_R         195      // the view ray must pass this close to the rock's centre: >= its farthest lump (182, verify_native)
#define TOD_METEOR_BOX           11600    // |x| and |y| stay under this (the sealed sky box is +-12,032)
#define TOD_METEOR_Z_MAX         36000    // and z under this (the box's ceiling is higher)
#define TOD_METEOR_PLAN_TRIES    14
#define TOD_METEOR_SAMPLES       12       // the pass is traced as this many segments
#define TOD_METEOR_SEEN_MIN      2        // of the 3 sight checks (1/4, 1/2, 3/4) at least this many clear
#define TOD_METEOR_EXIT_SECS     4.0      // a missed rock flies on this long past the pass, then goes

// ---- the clover fragment's fall ----------------------------------------------------------
#define TOD_CLOVER_APPROACH      700      // the open-air point beside the shooter: this far out ...
#define TOD_CLOVER_APPROACH_UP   420      // ... and this high above the landing
#define TOD_CLOVER_STREAK_SECS   1.1      // burst -> the approach point
#define TOD_CLOVER_DROP_SECS     0.5      // the approach point -> the floor
#define TOD_CLOVER_LAND_R_MIN    64       // it lands this far from the shooter ...
#define TOD_CLOVER_LAND_R_MAX    104      // ... up to this far
#define TOD_CLOVER_LAND_DZ       40       // and no more than this above / below their feet
#define TOD_POWERUP_LIFT         40       // specific_powerup_drop spawns the power-up this high

#define TOD_LUCKY_LOG            1        // [TOD_LUCKY] records under level.tod_dev
#define TOD_LUCKY_REV            "precache2"   // READY's rev= marker: the build without the empty-name precache (LT-meteor)

REGISTER_SYSTEM( "tod_lucky", &__init__, undefined )

// THE CLOVER'S REGISTRATION — the _tod_powerups contract, line for line: register_powerup
// first (it auto-includes the name server-side), then add_zombie_powerup, THEN the setters
// (they write the struct add creates — _tod_powerups' "live crash 2026-08-20"), then the
// statless table (a custom name has no pers stat: without it stock's grab thread throws on
// pickup after our effect ran — _tod_powerups' v17.99 note). The client half is
// _tod_lucky.csc (include + add, the same name).
function __init__()
{
	zm_powerups::register_powerup( TOD_CLOVER_NAME, &grab_clover );
	zm_powerups::add_zombie_powerup( TOD_CLOVER_NAME, TOD_CLOVER_MODEL, &"", &should_drop_clover, POWERUP_ONLY_AFFECTS_GRABBER, !POWERUP_ANY_TEAM, !POWERUP_ZOMBIE_GRABBABLE );
	zm_powerups::powerup_set_can_pick_up_in_last_stand( TOD_CLOVER_NAME, 0 );
	zm_powerups::powerup_set_statless_powerup( TOD_CLOVER_NAME );
}

// Threaded from the entry script after the systems are up.
function init()
{
	level.tod_lucky_meteor = undefined;
	callback::on_spawned( &on_player_spawned );
	level thread meteor_director();
	log( "READY rev=" + TOD_LUCKY_REV + " clover=" + TOD_CLOVER_NAME + " drop_pct=" + TOD_CLOVER_DROP_PCT + " meteor_every=" + TOD_METEOR_EVERY + " first_round=" + TOD_METEOR_FIRST_ROUND );
}

function on_player_spawned()   // self = player
{
	if ( IS_TRUE( self.tod_lucky_shot_watch ) )
		return;
	self.tod_lucky_shot_watch = true;
	self thread meteor_shot_watch();
}

// =============================================================================
// THE LUCKY CLOVER
// =============================================================================

// The random-drop gate: a refused pick is re-rolled by stock, so this is a SHARE of a
// regular drop's slot, not a chance per kill (see the header).
function should_drop_clover()
{
	return ( RandomInt( 100 ) < TOD_CLOVER_DROP_PCT );
}

// self = the power-up; player = the grabber. The stock contract (_zm_powerups): return TRUE
// = not consumed (stock keeps polling); no return value = consumed, and stock then plays
// zmb_powerup_grabbed and the grab effect itself.
function grab_clover( player )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return true;
	if ( player laststand::player_is_in_laststand() )
		return true;
	player PlayLocalSound( TOD_CLOVER_GRAB_SND );
	level thread tod_luck::add_bars( player, TOD_CLOVER_BARS );
	log( "CLOVER_GRAB player=" + player GetEntityNumber() + " bars=" + TOD_CLOVER_BARS + " bar_before=" + tod_luck::get( player ) + " at=" + self.origin );
}

// =============================================================================
// THE LUCKY METEOR — the director
// =============================================================================

function meteor_director()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );

	last = -1;
	for ( ;; )
	{
		r = level.round_number;
		if ( isdefined( r ) && r != last )
		{
			last = r;
			if ( r >= TOD_METEOR_FIRST_ROUND && ( ( r - TOD_METEOR_FIRST_ROUND ) % TOD_METEOR_EVERY ) == 0 )
				level thread meteor_round( r );
		}
		wait 1;
	}
}

// One meteor for round r: wait a random stretch of UNPAUSED time, then keep trying until
// one launches or the round moves on.
function meteor_round( r )
{
	level endon( "end_game" );

	delay = RandomFloatRange( TOD_METEOR_DELAY_MIN, TOD_METEOR_DELAY_MAX );
	log( "METEOR_ROUND round=" + r + " delay=" + delay );
	while ( delay > 0 )
	{
		wait 0.5;
		if ( !IS_TRUE( level.tod_upgrade_pause ) )
			delay -= 0.5;
		if ( level.round_number != r )
			return;
	}
	for ( ;; )
	{
		reason = meteor_refusal();
		if ( reason == "" )
		{
			focus = meteor_focus();
			if ( isdefined( focus ) && meteor_launch( focus, r ) )
				return;
			reason = "no_clear_pass";
		}
		log( "METEOR_WAIT round=" + r + " reason=" + reason );
		wait TOD_METEOR_RETRY_SECS;
		if ( level.round_number != r )
		{
			log( "METEOR_SKIPPED round=" + r + " (the round ended first)" );
			return;
		}
	}
}

function meteor_refusal()
{
	if ( isdefined( level.tod_lucky_meteor ) )
		return "live";
	if ( IS_TRUE( level.tod_upgrade_pause ) )
		return "paused";
	if ( IS_TRUE( level.tod_arena_active ) )
		return "arena";
	if ( !isdefined( meteor_focus() ) )
		return "nobody";
	return "";
}

// A random upright player on their feet in the tower: not down, not mid jump-pad flight.
function meteor_focus()
{
	cands = [];
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !isplayer( p ) || !IsAlive( p ) )
			continue;
		if ( p laststand::player_is_in_laststand() || IS_TRUE( p.tod_jumppad_flying ) )
			continue;
		if ( p.sessionstate != "playing" )
			continue;
		cands[ cands.size ] = p;
	}
	if ( cands.size == 0 )
		return undefined;
	return cands[ RandomInt( cands.size ) ];
}

// PURE (tools/lucky/test_lucky.js runs it): the pass from a focus point. bearing / sweep in
// degrees; the start is higher than the end by `drop`, the middle sits `alt` above the focus.
function meteor_plan( focus, bearing, dist, alt, sweep, drop )
{
	m = SpawnStruct();
	a0 = bearing - sweep * 0.5;
	a1 = bearing + sweep * 0.5;
	m.start = focus + ( Cos( a0 ) * dist, Sin( a0 ) * dist, alt + drop * 0.5 );
	m.end   = focus + ( Cos( a1 ) * dist, Sin( a1 ) * dist, alt - drop * 0.5 );
	return m;
}

// PURE: the point t (0..1) along the pass (a straight chord).
function meteor_point( m, t )
{
	if ( t < 0 )
		t = 0;
	if ( t > 1 )
		t = 1;
	return m.start + ( m.end - m.start ) * t;
}

// PURE: every sample of the pass inside the sealed sky box.
function meteor_in_box( m )
{
	for ( i = 0; i <= TOD_METEOR_SAMPLES; i++ )
	{
		p = meteor_point( m, ( i * 1.0 ) / TOD_METEOR_SAMPLES );   // float: never integer division
		if ( Abs( p[ 0 ] ) > TOD_METEOR_BOX || Abs( p[ 1 ] ) > TOD_METEOR_BOX || p[ 2 ] > TOD_METEOR_Z_MAX )
			return false;
	}
	return true;
}

// PURE: the view ray test (the _tod_secret bears' form). eye / fwd = the shooter's eye and
// unit view direction; true when the ray passes within r of `center`, in front of the eye.
function meteor_ray_hit( eye, fwd, center, r )
{
	v = center - eye;
	along = VectorDot( v, fwd );
	if ( along < 64 )
		return false;
	perp = Length( v - fwd * along );
	return ( perp <= r );
}

// ENGINE: is the straight run a -> b clear of the world for something `r` wide? Five parallel
// bullet traces (the centre + four offsets on the plane across the run). Characters ignored.
function run_clear( a, b, r )
{
	d = b - a;
	len = Length( d );
	if ( len < 1 )
		return true;
	dir = d / len;
	side = VectorCross( dir, ( 0, 0, 1 ) );
	if ( Length( side ) < 0.01 )
		side = ( 1, 0, 0 );
	side = VectorNormalize( side );
	up = VectorNormalize( VectorCross( side, dir ) );
	offs = array( ( 0, 0, 0 ), side * r, side * ( 0 - r ), up * r, up * ( 0 - r ) );
	foreach ( o in offs )
	{
		if ( !BulletTracePassed( a + o, b + o, false, undefined ) )
			return false;
	}
	return true;
}

// ENGINE: plan + validate a pass for this focus, spawn it and fly it. False = no clear pass.
function meteor_launch( focus, r )
{
	feet = focus.origin;
	eye = focus GetEye();
	for ( k = 0; k < TOD_METEOR_PLAN_TRIES; k++ )
	{
		m = meteor_plan( feet, RandomFloat( 360 ), RandomFloatRange( TOD_METEOR_DIST_MIN, TOD_METEOR_DIST_MAX ),
			RandomFloatRange( TOD_METEOR_ALT_MIN, TOD_METEOR_ALT_MAX ), TOD_METEOR_SWEEP, TOD_METEOR_DROP );
		if ( !meteor_in_box( m ) )
			continue;
		clear = true;
		for ( i = 0; i < TOD_METEOR_SAMPLES && clear; i++ )
			clear = run_clear( meteor_point( m, ( i * 1.0 ) / TOD_METEOR_SAMPLES ), meteor_point( m, ( ( i + 1 ) * 1.0 ) / TOD_METEOR_SAMPLES ), TOD_METEOR_RADIUS );
		if ( !clear )
			continue;
		seen = 0;
		for ( q = 1; q <= 3; q++ )
		{
			if ( BulletTracePassed( eye, meteor_point( m, q * 0.25 ), false, focus ) )
				seen++;
		}
		if ( seen < TOD_METEOR_SEEN_MIN )
			continue;
		level thread meteor_fly( m, focus, r, k + 1 );
		return true;
	}
	log( "METEOR_PLAN_FAIL round=" + r + " focus=" + focus GetEntityNumber() + " at=" + feet + " tries=" + TOD_METEOR_PLAN_TRIES );
	return false;
}

// ENGINE: the flight. Advances only while the world is not paused; ends broken or missed.
function meteor_fly( m, focus, r, tries )
{
	level endon( "end_game" );

	m.ent = Spawn( "script_model", m.start );
	m.ent SetModel( TOD_METEOR_MODEL );
	m.ent.angles = ( RandomInt( 360 ), RandomInt( 360 ), RandomInt( 360 ) );
	m.host = Spawn( "script_model", m.start );
	m.host SetModel( "tag_origin" );
	m.host LinkTo( m.ent );
	wait 0.05;   // ONE SERVER FRAME: the host's DObj must exist on the client before an effect binds to its tag
	PlayFXOnTag( TOD_METEOR_FX_TRAIL, m.host, "tag_origin" );
	m.ent PlayLoopSound( TOD_METEOR_SND_LOOP, 0.5 );
	m.broken = false;
	m.t = 0;
	m.spin = ( RandomFloatRange( -40, 40 ), RandomFloatRange( 50, 90 ), RandomFloatRange( -30, 30 ) );
	level.tod_lucky_meteor = m;

	foreach ( p in GetPlayers() )
		p PlayLocalSound( TOD_METEOR_SND_ANNOUNCE );
	log( "METEOR_SPAWN round=" + r + " focus=" + focus GetEntityNumber() + " start=" + m.start + " end=" + m.end + " plan_tries=" + tries + " trail=" + TOD_METEOR_FX_TRAIL + " host=" + m.host GetEntityNumber() );

	while ( m.t < 1 && !m.broken )
	{
		if ( !IS_TRUE( level.tod_upgrade_pause ) )
		{
			m.t += TOD_METEOR_TICK / TOD_METEOR_FLIGHT_SECS;
			m.ent MoveTo( meteor_point( m, m.t ), TOD_METEOR_TICK * 1.25 );
			m.ent RotateTo( m.ent.angles + m.spin * TOD_METEOR_TICK, TOD_METEOR_TICK * 1.25 );
		}
		wait TOD_METEOR_TICK;
	}
	if ( m.broken )
		return;   // meteor_break owns the rest

	// MISSED: fly on past the pass and go.
	log( "METEOR_MISS round=" + r );
	level.tod_lucky_meteor = undefined;
	dir = VectorNormalize( m.end - m.start );
	m.ent MoveTo( m.ent.origin + dir * ( Length( m.end - m.start ) / TOD_METEOR_FLIGHT_SECS ) * TOD_METEOR_EXIT_SECS, TOD_METEOR_EXIT_SECS );
	wait TOD_METEOR_EXIT_SECS;
	meteor_remove( m );
}

// The map's full stop (_tod_atmosphere / _tod_retriever): StopLoopSound takes a FADE on the server, StopSounds
// clears anything still playing, and the Delete waits a frame so the stop reaches the clients first. Deleting the
// host is what ends its attached trail (never a server StopFXOnTag).
function meteor_remove( m )
{
	ent = m.ent; host = m.host;
	m.ent = undefined; m.host = undefined;
	if ( isdefined( ent ) )
	{
		ent StopLoopSound( 0.3 );
		ent StopSounds();
	}
	if ( isdefined( host ) )
		host Delete();
	wait 0.05;
	if ( isdefined( ent ) )
		ent Delete();
}

// =============================================================================
// THE LUCKY METEOR — the shot
// =============================================================================

function meteor_shot_watch()   // self = player
{
	self endon( "disconnect" );
	level endon( "end_game" );

	for ( ;; )
	{
		self waittill( "weapon_fired" );
		m = level.tod_lucky_meteor;
		if ( !isdefined( m ) || IS_TRUE( m.broken ) || !isdefined( m.ent ) )
			continue;
		if ( isdefined( self.tod_class ) && self.tod_class == "slasher" )
			continue;   // the Warrior: fists and blades (header)
		if ( self laststand::player_is_in_laststand() )
			continue;
		eye = self GetEye();
		fwd = AnglesToForward( self GetPlayerAngles() );
		c = m.ent.origin;
		if ( !meteor_ray_hit( eye, fwd, c, TOD_METEOR_HIT_R ) )
			continue;
		// a clear line to the near side of the rock (the rock itself never blocks it)
		near = c - VectorNormalize( c - eye ) * TOD_METEOR_RADIUS;
		if ( !BulletTracePassed( eye, near, false, self ) )
		{
			log( "METEOR_BLOCKED player=" + self GetEntityNumber() + " (on the line, but a wall is in the way)" );
			continue;
		}
		meteor_break( m, self );
	}
}

function meteor_break( m, shooter )
{
	if ( IS_TRUE( m.broken ) )
		return;
	m.broken = true;
	level.tod_lucky_meteor = undefined;
	org = m.ent.origin;
	log( "METEOR_HIT player=" + shooter GetEntityNumber() + " at=" + org + " t=" + m.t + " range=" + int( Distance( shooter.origin, org ) ) + " burst=" + TOD_METEOR_FX_BURST );

	fx_at( TOD_METEOR_FX_BURST, org, 4 );
	tod_perk_scatter::play_sound_at_origin( org, TOD_METEOR_SND_BURST, 6 );
	tod_killconfirm::ding( shooter );
	level thread meteor_remove( m );
	level thread clover_fall( org, shooter );
}

// =============================================================================
// THE LUCKY METEOR — the clover's fall to the shooter
// =============================================================================

function clover_fall( from, shooter )
{
	level endon( "end_game" );

	land = undefined;
	if ( isdefined( shooter ) && isplayer( shooter ) )
		land = clover_landing( shooter );
	if ( !isdefined( land ) )
	{
		log( "METEOR_LAND_NONE (no shooter footing) — no clover" );
		return;
	}
	hover = land + ( 0, 0, TOD_POWERUP_LIFT );
	approach = clover_approach( from, hover );

	frag = Spawn( "script_model", from );
	frag SetModel( TOD_CLOVER_MODEL );
	frag.angles = ( 0, RandomInt( 360 ), 0 );
	host = Spawn( "script_model", from );
	host SetModel( "tag_origin" );
	host LinkTo( frag );
	wait 0.05;   // ONE SERVER FRAME before the trail binds (see meteor_fly)
	PlayFXOnTag( TOD_CLOVER_FX_TRAIL, host, "tag_origin" );
	frag PlayLoopSound( TOD_CLOVER_SND_FALL, 0.1 );
	spin_secs = TOD_CLOVER_STREAK_SECS + TOD_CLOVER_DROP_SECS + 0.2;
	frag RotateYaw( 540 * spin_secs, spin_secs );   // RotateYaw, not RotateVelocity: stock never uses the latter

	how = "direct";
	if ( isdefined( approach ) )
	{
		how = "approach";
		frag MoveTo( approach, TOD_CLOVER_STREAK_SECS, 0, TOD_CLOVER_STREAK_SECS * 0.3 );
		wait TOD_CLOVER_STREAK_SECS;
		frag MoveTo( hover, TOD_CLOVER_DROP_SECS, TOD_CLOVER_DROP_SECS * 0.3, 0 );
		wait TOD_CLOVER_DROP_SECS;
	}
	else if ( BulletTracePassed( from, hover, false, undefined ) )
	{
		frag MoveTo( hover, TOD_CLOVER_STREAK_SECS + TOD_CLOVER_DROP_SECS, 0, 0.3 );
		wait TOD_CLOVER_STREAK_SECS + TOD_CLOVER_DROP_SECS;
	}
	else
		how = "flash";   // no clear line anywhere: it simply lands, the flash covers it

	frag StopLoopSound( 0.1 );
	frag StopSounds();
	host Delete();
	frag thread delete_next_frame();
	fx_at( TOD_CLOVER_FX_LAND, land, 3 );
	tod_perk_scatter::play_sound_at_origin( land, TOD_CLOVER_SND_LAND, 4 );
	level thread zm_powerups::specific_powerup_drop( TOD_CLOVER_NAME, land );
	log( "METEOR_LAND at=" + land + " how=" + how + " shooter=" + shooter GetEntityNumber() + " trail=" + TOD_CLOVER_FX_TRAIL + " land=" + TOD_CLOVER_FX_LAND );
}

// ENGINE: a floor point beside the player: on the navmesh, level with their feet, in plain
// sight of them. Outward from the tower's axis first (the side the fragment arrives from),
// then around; their own feet as the last resort.
function clover_landing( p )
{
	base = p.origin;
	if ( !p IsOnGround() && isdefined( p.last_valid_position ) )
		base = p.last_valid_position;
	out = ( base[ 0 ], base[ 1 ], 0 );
	if ( Length( out ) < 64 )
		out = AnglesToForward( ( 0, p.angles[ 1 ], 0 ) );
	out_ang = VectorToAngles( out );
	yaw0 = out_ang[ 1 ];
	offs = array( 0, 45, -45, 90, -90, 135, -135, 180 );
	foreach ( o in offs )
	{
		d = AnglesToForward( ( 0, yaw0 + o, 0 ) );
		q = GetClosestPointOnNavMesh( base + d * RandomFloatRange( TOD_CLOVER_LAND_R_MIN, TOD_CLOVER_LAND_R_MAX ), 48 );
		if ( !isdefined( q ) )
			continue;
		if ( Abs( q[ 2 ] - base[ 2 ] ) > TOD_CLOVER_LAND_DZ )
			continue;
		if ( !BulletTracePassed( base + ( 0, 0, 40 ), q + ( 0, 0, 40 ), false, p ) )
			continue;
		return q;
	}
	q = GetClosestPointOnNavMesh( base, 48 );
	if ( isdefined( q ) )
		return q;
	return base;
}

// ENGINE: an open-air point beside the landing, with a clear line from the burst to it and
// from it down to the power-up's spot. Outward from the tower's axis first, then around.
function clover_approach( from, hover )
{
	out = ( hover[ 0 ], hover[ 1 ], 0 );
	yaw0 = 0;
	if ( Length( out ) >= 64 )
	{
		out_ang = VectorToAngles( out );
		yaw0 = out_ang[ 1 ];
	}
	offs = array( 0, 45, -45, 90, -90, 135, -135, 180 );
	foreach ( o in offs )
	{
		a = hover + AnglesToForward( ( 0, yaw0 + o, 0 ) ) * TOD_CLOVER_APPROACH + ( 0, 0, TOD_CLOVER_APPROACH_UP );
		if ( Abs( a[ 0 ] ) > TOD_METEOR_BOX || Abs( a[ 1 ] ) > TOD_METEOR_BOX )
			continue;
		if ( !BulletTracePassed( from, a, false, undefined ) )
			continue;
		if ( !BulletTracePassed( a, hover, false, undefined ) )
			continue;
		return a;
	}
	return undefined;
}

// =============================================================================
// Shared helpers
// =============================================================================

// A ONE-SHOT effect rides a short-lived tag_origin carrier, played one server frame after it spawns
// (_tod_class_kit::fx_at: a bare server PlayFX of a one-shot does not render in this map, and one played in the
// carrier's first frame can beat the entity to the client). The carrier goes after `life` seconds.
function fx_at( effect, org, life )
{
	host = Spawn( "script_model", org );
	if ( !isdefined( host ) )
	{
		log( "FX_DROPPED effect=" + effect + " at=" + org + " (entity pool full)" );
		return;
	}
	host SetModel( "tag_origin" );
	host thread fx_at_play( effect, life );
}

function fx_at_play( effect, life )   // self = the carrier
{
	self endon( "death" );
	wait 0.05;
	PlayFXOnTag( effect, self, "tag_origin" );
	wait life;
	self Delete();
}

function delete_next_frame()   // self = an entity whose sounds were just stopped
{
	wait 0.05;
	if ( isdefined( self ) )
		self Delete();
}

function log( msg )
{
	if ( !TOD_LUCKY_LOG || !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_LUCKY] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
