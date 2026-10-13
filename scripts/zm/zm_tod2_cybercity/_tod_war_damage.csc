// =============================================================================
// _tod_war_damage.csc - THE WAR DAMAGE PASS (docs/205): the tower after the war.
//
// User 2026-10-03: "The tower needs a bit more flavor. The broken off pieces look
// to clean. The map is basically the first map but looks like its been fallen and
// beaten up by wars."
//
// CLIENT ONLY, like the sky fleet: every player's own game draws the damage.
//   * THE WOUNDS: one merged model per break (24) and one per five ordinary floors
//     (tools/war_damage/layout.js places Treyarch's stock rubble, slabs, rebar, iron,
//     cables, glass, dark burn / blast decal cards and shrapnel holes; build_clusters.py merges
//     them). Spawned once per local client: no collision, no server entity, invisible
//     to every server trace (the Archer's grapple never anchors on them).
//   * THE LIFE IN THEM: dust trickling off the snapped ledges, embers and smoke on
//     the rubble, sparking cables, fires with firelight, floating ash, tall smoke
//     columns. Looping effects played AT a position (PlayFX, no host entity) with
//     looping 3D sounds at a position (audio::playloopat, no entity), started and
//     stopped in a WINDOW round the local player (TOD_WAR_WINDOW_*), capped per client
//     (TOD_WAR_FX_MAX, TOD_WAR_LIGHT_MAX). The smoke columns are always on: they are
//     how the war reads from the crown and the terrace.
//   * REV 2 - THE POWER (phase 2, docs/205 s7): beside every blast crater a LED fixture
//     dangles off its mount and the power conduit is torn open. When the power comes
//     back (_tod_war_damage.gsc raises the 1-bit world clientfield TOD_WAR_POWER_FIELD
//     at the power wave's first floor) every client replays the wave's own top-down
//     schedule (LOCKSTEP TOD_WAR_WAVE_* against _tod_fall.gsc TOD_FALL_WAVE_SECS and
//     tod_crown_data::wave_orgs(): 51 floors, z 19168 down by 384, over 12 s): as it
//     passes a floor the torn conduit's CONDUCTORS (a separate two-state client model,
//     tod_war_conductor_<a|b>_off -> _on) come alive, a cyan arc spits at the torn
//     mouth, and the dangling fixture's tube starts to flicker - a real dynamic light
//     in the lamp effect (tools/war_damage/make_fx.py), budgeted like the firelights.
//     Powered-only anchors (flag 16) never run before the wave reaches their height; a
//     late joiner gets the bit in his first snapshot and sees everything already lit.
// GENERATED DATA: _tod_war_damage_data.csc (never hand-edit; node tools/war_damage/layout.js).
// Logs: [TOD_WAR] INIT / POWER / CONDUCTORS / WINDOW (TOD_WAR_LOG; 0 before a publish).
// =============================================================================

#using scripts\shared\audio_shared;
#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;

#using scripts\zm\zm_tod2_cybercity\_tod_war_damage_data;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#namespace tod_war_damage;

#define TOD_WAR_ENABLED     1
#define TOD_WAR_LOG         1       // [TOD_WAR] records for the first playtests; 0 before a publish
#define TOD_WAR_REV         2
#define TOD_WAR_TICK        0.5     // the effect window is re-judged this often (real seconds)
#define TOD_WAR_WINDOW_Z    700     // an effect runs only within this height of the local player (~1.8 floors)...
#define TOD_WAR_WINDOW_XY   1800    // ...and this far sideways (the arena and the crown are elsewhere)
#define TOD_WAR_FX_MAX      28      // effects running at once per player, the always-on columns included
#define TOD_WAR_LIGHT_MAX   4       // dynamic lights running at once per player: firelights + flickering tubes
#define TOD_WAR_FIRE_LIGHT  "light/fx_light_fire_flicker_noshad_small"
#define TOD_WAR_LAMP_FIRST  8       // effect kinds from this index carry their own dynamic light (LOCKSTEP layout.js KINDS: lamp_a/b/c)
#define TOD_WAR_POWER_FIELD "tod_war_power"   // LOCKSTEP _tod_war_damage.gsc
#define TOD_WAR_WAVE_TOP_Z  19168   // LOCKSTEP tod_crown_data::wave_orgs()[ 0 ] z (the first floor the wave lights)
#define TOD_WAR_WAVE_STEP   384     // LOCKSTEP one floor
#define TOD_WAR_WAVE_FLOORS 51      // LOCKSTEP wave_orgs().size
#define TOD_WAR_WAVE_SECS   12      // LOCKSTEP _tod_fall.gsc TOD_FALL_WAVE_SECS

// LOCKSTEP: the kind order of tools/war_damage/layout.js FX (= fx_kind() in the data file).
#precache( "client_fx", "dirt/fx_dust_fall_sm_lit" );
#precache( "client_fx", "electric/fx_elec_sparks_sm_wire_orange" );
#precache( "client_fx", "fire/fx_fire_ground_rubble_sm_50x50" );
#precache( "client_fx", "smoke/fx_smk_ground_rubble_50x50" );
#precache( "client_fx", "fire/fx_fire_ground_rubble_50x50" );
#precache( "client_fx", "debris/fx_debris_ash_float_lg" );
#precache( "client_fx", "smoke/fx_smk_column_wind_slow_sm_tall_dark" );
#precache( "client_fx", "tod/war/fx_war_arc" );
#precache( "client_fx", "tod/war/fx_war_tube_flicker_a" );
#precache( "client_fx", "tod/war/fx_war_tube_flicker_b" );
#precache( "client_fx", "tod/war/fx_war_tube_flicker_c" );
#precache( "client_fx", "light/fx_light_fire_flicker_noshad_small" );

REGISTER_SYSTEM( "tod_war_damage", &__init__, undefined )

function __init__()
{
	if ( !TOD_WAR_ENABLED )
		return;
	level.tod_war_fx = array( "dirt/fx_dust_fall_sm_lit", "electric/fx_elec_sparks_sm_wire_orange",
		"fire/fx_fire_ground_rubble_sm_50x50", "smoke/fx_smk_ground_rubble_50x50", "fire/fx_fire_ground_rubble_50x50",
		"debris/fx_debris_ash_float_lg", "smoke/fx_smk_column_wind_slow_sm_tall_dark",
		"tod/war/fx_war_arc", "tod/war/fx_war_tube_flicker_a", "tod/war/fx_war_tube_flicker_b", "tod/war/fx_war_tube_flicker_c" );
	level.tod_war_power_at = [];        // per local client: the real-time ms the power bit arrived (undefined = not yet)
	level.tod_war_power_snap = [];      // per local client: true when it arrived in the first snapshot (already on: no wave)
	level.tod_war_conductors = [];
	clientfield::register( "world", TOD_WAR_POWER_FIELD, VERSION_SHIP, 1, "int", &power_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );
	callback::on_localclient_connect( &on_local_connect );
}

function on_local_connect( localClientNum )
{
	n = tod_war_damage_data::cluster_count();
	made = 0;
	for ( i = 0; i < n; i++ )
	{
		m = spawn( localClientNum, tod_war_damage_data::cluster_org( i ), "script_model" );
		if ( !isdefined( m ) )
			continue;
		m SetModel( tod_war_damage_data::cluster_model( i ) );
		made++;
	}
	// the torn conduits' conductors: dead (_off) until the power wave passes them
	nc = tod_war_damage_data::conductor_count();
	level.tod_war_conductors[ localClientNum ] = [];
	cmade = 0;
	for ( i = 0; i < nc; i++ )
	{
		c = spawn( localClientNum, tod_war_damage_data::conductor_org( i ), "script_model" );
		if ( !isdefined( c ) )
			continue;
		c.angles = tod_war_damage_data::conductor_angles( i );
		c.tod_war_model = tod_war_damage_data::conductor_model( i );
		c.tod_war_on = false;
		c SetModel( c.tod_war_model + "_off" );
		level.tod_war_conductors[ localClientNum ][ level.tod_war_conductors[ localClientNum ].size ] = c;
		cmade++;
	}
	war_log( "INIT rev=" + TOD_WAR_REV + " local=" + localClientNum + " models=" + made + "/" + n + " conductors=" + cmade + "/" + nc
		+ " fx_anchors=" + tod_war_damage_data::fx_count() + " power=" + isdefined( level.tod_war_power_at[ localClientNum ] )
		+ " window_z=" + TOD_WAR_WINDOW_Z + " window_xy=" + TOD_WAR_WINDOW_XY + " fx_max=" + TOD_WAR_FX_MAX + " light_max=" + TOD_WAR_LIGHT_MAX );
	level thread fx_window( localClientNum );
}

// The server's one bit: the power wave started (or, in the first snapshot, had already run).
function power_cb( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
	if ( !newVal )
		return;
	if ( isdefined( level.tod_war_power_at[ localClientNum ] ) )
		return;
	level.tod_war_power_at[ localClientNum ] = GetRealTime();
	level.tod_war_power_snap[ localClientNum ] = IS_TRUE( bInitialSnap );
	war_log( "POWER local=" + localClientNum + " initial_snap=" + IS_TRUE( bInitialSnap ) + " wave=" + TOD_WAR_WAVE_SECS + "s top_z=" + TOD_WAR_WAVE_TOP_Z );
}

// PURE: the height the power wave has reached for this client. Everything AT OR ABOVE it is powered.
function wave_z( localClientNum )
{
	if ( !isdefined( level.tod_war_power_at[ localClientNum ] ) )
		return 1000000;                                                          // no power yet: nothing is
	if ( IS_TRUE( level.tod_war_power_snap[ localClientNum ] ) )
		return -1000000;                                                         // it was already on: everything is
	t = ( GetRealTime() - level.tod_war_power_at[ localClientNum ] ) / 1000.0;
	return TOD_WAR_WAVE_TOP_Z - t * ( TOD_WAR_WAVE_FLOORS * TOD_WAR_WAVE_STEP / TOD_WAR_WAVE_SECS );
}

// PURE: does effect anchor i run for a player whose origin is `eye`, with the wave at wz?
function wanted( i, eye, wz )
{
	flags = tod_war_damage_data::fx_flags( i );
	org = tod_war_damage_data::fx_org( i );
	if ( ( flags & 16 ) && org[ 2 ] < wz )
		return false;                                                            // powered only: the wave has not reached it
	if ( flags & 2 )
		return true;
	return ( Abs( org[ 2 ] - eye[ 2 ] ) <= TOD_WAR_WINDOW_Z && Distance2D( org, eye ) <= TOD_WAR_WINDOW_XY );
}

// PURE: does anchor i hold a dynamic light while it runs? (a firelight rides it, or it is a flickering tube)
function has_light( i, s )
{
	if ( isdefined( s ) && isdefined( s.light ) )
		return true;
	return tod_war_damage_data::fx_kind( i ) >= TOD_WAR_LAMP_FIRST;
}

function fx_window( localClientNum )
{
	n = tod_war_damage_data::fx_count();
	live = [];          // anchor index -> struct { fx, light, sound } while it runs
	last = -1;
	lit_total = 0;
	for ( ;; )
	{
		waitrealtime( TOD_WAR_TICK );   // a client `wait` counts frames (~2.7x fast at 165 fps): real time
		player = GetLocalPlayer( localClientNum );
		if ( !isdefined( player ) )
			continue;
		eye = player.origin;
		wz = wave_z( localClientNum );
		// (0) the conductors the wave has passed come alive
		lit = 0;
		cs = level.tod_war_conductors[ localClientNum ];
		for ( j = 0; j < cs.size; j++ )
		{
			c = cs[ j ];
			if ( !isdefined( c ) || IS_TRUE( c.tod_war_on ) || c.origin[ 2 ] < wz )
				continue;
			c SetModel( c.tod_war_model + "_on" );
			c.tod_war_on = true;
			lit++;
		}
		if ( lit )
		{
			lit_total += lit;
			war_log( "CONDUCTORS local=" + localClientNum + " lit=" + lit + " total=" + lit_total + "/" + cs.size + " wave_z=" + int( wz ) );
		}
		running = 0;
		lights = 0;
		capped = 0;
		// (1) stop what left the window; count what stays
		for ( i = 0; i < n; i++ )
		{
			if ( !isdefined( live[ i ] ) )
				continue;
			if ( wanted( i, eye, wz ) )
			{
				running++;
				if ( has_light( i, live[ i ] ) )
					lights++;
				continue;
			}
			stop( localClientNum, i, live[ i ] );
			live[ i ] = undefined;
		}
		// (2) start what came in, under the budgets (a fire over the light budget burns without its light; a
		//     flickering tube IS its light, so it waits for a slot)
		for ( i = 0; i < n; i++ )
		{
			if ( isdefined( live[ i ] ) || !wanted( i, eye, wz ) )
				continue;
			if ( running >= TOD_WAR_FX_MAX )
			{
				capped++;
				continue;
			}
			if ( tod_war_damage_data::fx_kind( i ) >= TOD_WAR_LAMP_FIRST && lights >= TOD_WAR_LIGHT_MAX )
			{
				capped++;
				continue;
			}
			live[ i ] = start( localClientNum, i, lights < TOD_WAR_LIGHT_MAX );
			running++;
			if ( has_light( i, live[ i ] ) )
				lights++;
		}
		if ( running != last )
		{
			war_log( "WINDOW local=" + localClientNum + " z=" + int( eye[ 2 ] ) + " running=" + running + " lights=" + lights + " capped=" + capped + " wave_z=" + int( wz ) );
			last = running;
		}
	}
}

function start( localClientNum, i, light_ok )
{
	s = SpawnStruct();
	org = tod_war_damage_data::fx_org( i );
	ang = tod_war_damage_data::fx_angles( i );
	flags = tod_war_damage_data::fx_flags( i );
	s.fx = PlayFX( localClientNum, level.tod_war_fx[ tod_war_damage_data::fx_kind( i ) ], org, AnglesToForward( ang ), AnglesToUp( ang ) );
	if ( ( flags & 1 ) && light_ok )
		s.light = PlayFX( localClientNum, TOD_WAR_FIRE_LIGHT, org + ( 0, 0, 24 ), ( 0, 0, 1 ), ( 1, 0, 0 ) );
	if ( flags & 4 )
		s.sound = "tod_war_fire_lp";
	else if ( flags & 8 )
		s.sound = "tod_war_spark_lp";
	else if ( flags & 32 )
		s.sound = "tod_war_tube_lp";
	else if ( flags & 64 )
		s.sound = "tod_war_arc_lp";
	if ( isdefined( s.sound ) )
		audio::playloopat( s.sound, org );
	return s;
}

function stop( localClientNum, i, s )
{
	if ( isdefined( s.fx ) )
		StopFX( localClientNum, s.fx );            // live particles finish their own fade
	if ( isdefined( s.light ) )
		KillFX( localClientNum, s.light );
	if ( isdefined( s.sound ) )
		audio::stoploopat( s.sound, tod_war_damage_data::fx_org( i ) );
}

function war_log( msg )
{
	if ( !TOD_WAR_LOG )
		return;
	line = "[TOD_WAR] ms=" + GetRealTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
