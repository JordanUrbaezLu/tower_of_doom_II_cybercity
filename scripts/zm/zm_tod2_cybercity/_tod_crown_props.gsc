// =============================================================================
// _tod_crown_props.gsc — THE CROWN'S SCENERY AND ITS PARKED ROAD (2026-10-05).
//
// WHAT THIS IS. The live half of the retired Map One ending. Tower of Doom II
// starts IN the crown and descends (THE FALL, docs/160), so the extraction ending
// _tod_finale.gsc sold at the terrace never ran here: it sat behind
// TOD_FINALE_PARKED 1 and its init did three things and returned. Those three
// things are this file, verbatim in behaviour, and everything else (the uplink
// buy, the road and its beats, the hold-out, the extraction pad, the win screen,
// the closing song, the road banner) retired WHOLE to archive/map1_carryover/
// (W2E, user: "Just dont include assets not on this map in the build").
//
//   1. THE PROPS. The uplink console on the terrace (with its clip), the four
//      warning beacons on the circlet's corner points, the mast beacon with its
//      red aura and the hall's wall sconces. Scenery the crown has always had;
//      the extraction pad (red/green pad lights) did NOT spawn while parked and
//      is gone with the ending.
//   2. THE LANE SEALS. Five generated script_brushmodels on the causeway
//      (tod_lane_seal_0..4, gen_tower_map.js) are hidden, non-solid and
//      path-connected, exactly as the parked init left them.
//   3. THE TERRACE GATE. tod_causeway_gate opens silently at init and
//      level.tod_gate_open is set, which the spawn filters read
//      (_tod_endless_rounds, _tod_ambush, _tod_stray): with it unset they would
//      drop every riser past the terrace, i.e. the crown phase's own risers.
//
// Every anchor comes from the GENERATED _tod_crown_data.gsc, so this file can
// never drift from the .map. No hint strings, no clientfields, no sounds.
// Logs: [TOD_CROWN_PROPS] (dev / diag) - one READY line with every count.
// =============================================================================

#using scripts\shared\flag_shared;

#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_lights;     // set_glow (the aura clientfield; server PlayFX never renders)

#insert scripts\shared\shared.gsh;

// carved T7 props already in the Mod Tools GDT DB, spawned with SetModel (never baked misc_models)
#precache( "model", "p7_zm_sta_dragon_network_data_terminal" );   // the terrace console (also the class terminal's)
#precache( "model", "p7_zm_asc_light_cage_warning_red" );         // the mast beacon + the circlet's four corner beacons
#precache( "model", "p7_zm_moo_light_panel_01_long" );            // the hall's wall sconces

#define TOD_CROWN_GLOW_RED       1       // tod_perk_lights::perk_color_index's red
#define TOD_CROWN_LANE_SEALS     5       // tod_lane_seal_0..4 (gen_tower_map.js THE LANE LOTTERY)

#namespace tod_crown_props;

function init()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );

	props = spawn_props();
	seals = lane_seals_park();
	gate = gate_park();
	dev_log( "READY props=" + props + " lane_seals_hidden=" + seals + "/" + TOD_CROWN_LANE_SEALS + " gate=" + gate
		+ " gate_open=" + IS_TRUE( level.tod_gate_open ) );
}

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_CROWN_PROPS] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function prop( model, org, yaw )
{
	m = Spawn( "script_model", org );
	if ( !isdefined( m ) )
		return undefined;   // entity pool full — a missing prop is cosmetic, never throw
	m.angles = ( 0, yaw, 0 );
	m SetModel( model );
	return m;
}

// -> how many props stood up (the log's count). Same props, same spots, same
// order as the parked _tod_finale::spawn_props.
function spawn_props()
{
	n = 0;

	// the terrace console. DO NOT REPLACE IT WITH A WORLD BRUSH: a solid brush on
	// a trigger origin swallowed a buy once (2026-08-27) and the clip below is a
	// script entity for the same reason.
	if ( isdefined( prop( "p7_zm_sta_dragon_network_data_terminal", tod_crown_data::uplink_org(), tod_crown_data::uplink_yaw() ) ) )
		n++;
	// COLLISION (user 2026-08-25: "Add a clip to the extraction station. Its walk
	// through currently"): a script_model is visual only, so the console gets the
	// stock vendor clip (zm_collision_perks1, _zm_perks.gsc:1551's recipe).
	// DisconnectPaths is MANDATORY: the navmesh ignores entity collision.
	uclip = Spawn( "script_model", tod_crown_data::uplink_org(), 1 );
	if ( isdefined( uclip ) )
	{
		uclip.angles = ( 0, tod_crown_data::uplink_yaw(), 0 );
		uclip SetModel( "zm_collision_perks1" );
		uclip.script_noteworthy = "clip";
		uclip DisconnectPaths();
	}

	// the circlet's four corner point beacons (gen_tower_map.js 5f.4 pylon_orgs)
	orgs = tod_crown_data::pylon_orgs();
	for ( i = 0; i < orgs.size; i++ )
		if ( isdefined( prop( "p7_zm_asc_light_cage_warning_red", orgs[ i ], 0 ) ) )
			n++;

	// the mast beacon: a warning light at the spire tip with a red aura — the
	// tower's own "you are here" seen from every lap below
	beacon = prop( "p7_zm_asc_light_cage_warning_red", tod_crown_data::mast_tip_org(), 0 );
	if ( isdefined( beacon ) )
	{
		tod_perk_lights::set_glow( beacon, TOD_CROWN_GLOW_RED );
		n++;
	}

	// the hall's wall sconces
	so = tod_crown_data::sconce_orgs();
	sy = tod_crown_data::sconce_yaws();
	for ( i = 0; i < so.size; i++ )
		if ( isdefined( prop( "p7_zm_moo_light_panel_01_long", so[ i ], sy[ i ] ) ) )
			n++;
	return n;
}

// The five lane seals hidden, non-solid and path-connected (the parked init's
// lane_seals_init, verbatim). -> how many were found. A missing one is generator
// drift: an open lane is survivable, a script error is not.
function lane_seals_park()
{
	n = 0;
	for ( i = 0; i < TOD_CROWN_LANE_SEALS; i++ )
	{
		e = GetEnt( "tod_lane_seal_" + i, "targetname" );
		if ( !isdefined( e ) )
			continue;
		e Hide();
		e NotSolid();
		e ConnectPaths();
		n++;
	}
	return n;
}

// The terrace gate OPEN, silently, from init: Hide + NotSolid + ConnectPaths
// (nobody is on the terrace to see a road "appear"; it was always there). Sets
// level.tod_gate_open, which the spawn filters read. -> "open" / "missing".
function gate_park()
{
	level.tod_gate_open = true;
	gate = GetEnt( "tod_causeway_gate", "targetname" );
	if ( !isdefined( gate ) )
		return "missing";
	gate Hide();
	gate NotSolid();
	gate ConnectPaths();
	return "open";
}
