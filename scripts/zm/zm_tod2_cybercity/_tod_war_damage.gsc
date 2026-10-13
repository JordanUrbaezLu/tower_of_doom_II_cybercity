// =============================================================================
// _tod_war_damage.gsc - the server half of THE WAR DAMAGE PASS (docs/205 s7): ONE BIT, THE POWER.
//
// Everything the war damage draws is client-side (_tod_war_damage.csc, _tod_war_sky.csc). The one thing a client
// cannot know on its own is WHEN THE POWER CAME ON: the broken lights try to catch and the torn conductors come
// alive as the power wave (_tod_fall::power_wave, top down over TOD_FALL_WAVE_SECS) passes their floor. So this
// module raises a 1-bit world clientfield at the wave's FIRST floor (the `tod_power_wave_z` notify the wave sends,
// the same cue the havens boot on), or on the `power_on` flag if the wave never runs (a dev path, a late power);
// each client runs the wave's own top-down schedule from the edge (LOCKSTEP: TOD_WAR_WAVE_* in the .csc against
// TOD_FALL_WAVE_SECS and tod_crown_data::wave_orgs(), gated by tools/war_damage/test_war_damage.js). A late
// joiner receives the bit in his first snapshot and sees everything already lit.
// Logs `[TOD_WAR] POWER` (dev).
// =============================================================================

#using scripts\shared\clientfield_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\system_shared;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#namespace tod_war_damage;

#define TOD_WAR_POWER_FIELD "tod_war_power"
#define TOD_WAR_POWER_GRACE 1.5          // s after the power_on flag for the wave's own cue to arrive first

REGISTER_SYSTEM( "tod_war_damage", &__init__, undefined )

function __init__()
{
	clientfield::register( "world", TOD_WAR_POWER_FIELD, VERSION_SHIP, 1, "int" );
}

function init()
{
	level thread power_watch();
}

function power_watch()
{
	level endon( "end_game" );
	if ( level flag::exists( "power_on" ) && level flag::get( "power_on" ) )
	{
		set_power( "already_on" );
		return;
	}
	level thread wave_watch();
	level flag::wait_till( "power_on" );
	wait TOD_WAR_POWER_GRACE;
	set_power( "power_on_flag" );
}

function wave_watch()
{
	level endon( "end_game" );
	level waittill( "tod_power_wave_z", z );
	set_power( "wave z=" + z );
}

function set_power( why )
{
	if ( IS_TRUE( level.tod_war_power ) )
		return;
	level.tod_war_power = true;
	level clientfield::set( TOD_WAR_POWER_FIELD, 1 );
	war_log( "POWER why=" + why );
}

function war_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_WAR] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
