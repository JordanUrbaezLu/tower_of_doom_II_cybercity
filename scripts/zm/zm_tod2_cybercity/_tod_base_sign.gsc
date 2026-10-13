// =============================================================================
// _tod_base_sign.gsc - THE CYBERCITY SIGN on the plaza's tower wall (TOD II, docs/208)
//
// Ported from map 1 (its v19.69 / v19.68u / v19.68w: user 2026-10-02 "Add the Tower
// of Doom Cybercity sign part of tower wall where players spawn at"). On map 1 this
// wall is the spawn; on this map the plaza is THE GROUND FLOOR, the bottom of the
// descent - the same old tower wall, so the party reaches map 1's sign at the end
// of the fall.
//
// THE MODEL: Nikolai's neon TOWER OF DOOM / CYBERCITY sign, map 1's clean relief
// rebuild `tod_cybercity_sign2` (60K triangles, one 4096 front-projected colour
// sheet, the CYBERCITY line levelled). Front = model +X; origin = its BACK plane,
// horizontal centre, bottom edge. Map-owned GDT source_data/tod_fan_props.gdt, held
// to tools/fan_props/manifest.json by tools/fan_props/verify.py.
//
// POWER: it hangs DARK (`_off`: the neon unlit glass, no glow) until power_on, then
// a neon start - two stutters, a dim catch (`_dim`), the full light. All three are
// skinOverride twins of ONE mesh, so every step is one SetModel. Here the power
// comes on in the crown, long before anyone reaches the plaza: the party finds it
// lit. Power on before the sign spawns = ON, no flicker.
//
// THE SPOT: the core's WEST face over the base ammo crate (map 1's spot, centred on
// the W spine). The anchor is GENERATED (_tod_breather_data.gsc base_sign_org/yaw,
// from gen_tower_map.js BASE_SIGN), and the generator asserts it clear of lap 2's
// W flight overhead, the crate underneath and the face's corners, and cuts its
// body clip + a steep cap. Move it there, never here.
//
// DIAGNOSTICS (tod_dev): [TOD_SIGN] INIT / LIT / FAIL.
// =============================================================================

#using scripts\shared\flag_shared;

#using scripts\zm\zm_tod2_cybercity\_tod_breather_data;   // GENERATED - base_sign_org/yaw

#insert scripts\shared\shared.gsh;

#precache( "model", "tod_cybercity_sign2" );
#precache( "model", "tod_cybercity_sign2_off" );
#precache( "model", "tod_cybercity_sign2_dim" );

#namespace tod_base_sign;

#define TOD_SIGN_MODEL     "tod_cybercity_sign2"       // ON
#define TOD_SIGN_MODEL_OFF "tod_cybercity_sign2_off"   // power off: the neon dark
#define TOD_SIGN_MODEL_DIM "tod_cybercity_sign2_dim"   // the flicker's half step
#define TOD_SIGN_REVISION  "tod2_sign_relief_3"        // map 1's sign_relief_3, ported (docs/208); logged at INIT
#define TOD_SIGN_POWER_LAG 0.4                         // the current reaches the sign a beat after the switch

function init()
{
	level thread place();
}

function place()
{
	level endon( "end_game" );

	// Like every scripted fixture: the wall is there from frame one, but spawning
	// props before the blackscreen races the stock world init.
	level flag::wait_till( "initial_blackscreen_passed" );

	org = tod_breather_data::base_sign_org();
	yaw = tod_breather_data::base_sign_yaw();
	m = Spawn( "script_model", org );
	if ( !isdefined( m ) )
	{
		dev_log( "FAIL spawn returned undefined (entity pool full) org=" + org );
		return;   // a missing sign is cosmetic; never throw
	}
	m.angles = ( 0, yaw, 0 );
	power = ( level flag::exists( "power_on" ) && level flag::get( "power_on" ) );
	if ( power )
		m SetModel( TOD_SIGN_MODEL );
	else
		m SetModel( TOD_SIGN_MODEL_OFF );
	level.tod_base_sign = m;
	dev_log( "INIT rev=" + TOD_SIGN_REVISION + " model=" + TOD_SIGN_MODEL + " org=" + org + " yaw=" + yaw + " ent=" + m GetEntityNumber() + " power_on=" + power );
	if ( !power )
		m thread light_on_power();
}

// Dark until power_on, then a neon start: each step is a model and how long it holds;
// the last is ON for good. A deleted sign ends the thread.
function light_on_power()
{
	self endon( "death" );
	level endon( "end_game" );

	if ( !level flag::exists( "power_on" ) )
	{
		dev_log( "FAIL no power_on flag - the sign stays dark" );
		return;
	}
	level flag::wait_till( "power_on" );
	t0 = GetTime();
	wait TOD_SIGN_POWER_LAG;
	steps = array( TOD_SIGN_MODEL_DIM, TOD_SIGN_MODEL_OFF, TOD_SIGN_MODEL, TOD_SIGN_MODEL_OFF,
	               TOD_SIGN_MODEL_DIM, TOD_SIGN_MODEL_OFF, TOD_SIGN_MODEL_DIM, TOD_SIGN_MODEL );
	holds = array( 0.1, 0.15, 0.05, 0.35, 0.1, 0.1, 0.25, 0 );
	for ( i = 0; i < steps.size; i++ )
	{
		self SetModel( steps[ i ] );
		if ( holds[ i ] > 0 )
			wait holds[ i ];
	}
	dev_log( "LIT power_on_to_lit_ms=" + ( GetTime() - t0 ) + " steps=" + steps.size + " model=" + TOD_SIGN_MODEL );
}

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_SIGN] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
