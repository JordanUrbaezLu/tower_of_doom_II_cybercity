// FIXTURE (tools/test_battle_arena.js): the Battle Arena v1 teleport code, verbatim from
// scripts/zm/zm_tod2_cybercity/_tod_arena.gsc as shipped 2026-09-28..2026-10-02 (docs/185).
// It is the NEGATIVE CONTROL for the jump-timing check: its three inline fx_burst calls are
// the latency the user reported 2026-10-03 ("waits way too long to actually teleport ... It
// doesnt line up"; measured in the 2026-10-01 log: use -> jump 6.6 s). Never edit; never zone.

#define TOD_ARENA_CHARGE_SECS   3.0    // the chamber "running" before the jump
#define TOD_ARENA_LAND_SECS     3.0    // breath after landing before wave 1
#define TOD_ARENA_RING          48     // top-bay arrival fan-out (the transit ring)

function arena_run( payer )
{
	level endon( "end_game" );
	lvl = level.tod_arena_level;
	set = pick_set();
	org = tod_arena_data::chamber_org();

	// 1. the chamber runs
	tod_teleport::fx_burst( "tod_tp_charge", org + ( 0, 0, 40 ), TOD_ARENA_CHARGE_SECS + 0.5, "tod_tp_charge_field" );
	tod_perk_scatter::play_sound_at_origin( org, "tod_teleport_fire", 4 );
	foreach ( p in playing_players() )
		p IPrintLnBold( "BATTLE ARENA - LEVEL " + lvl );
	dev_log( "CHARGE level=" + lvl + " set=" + set.name );
	wait TOD_ARENA_CHARGE_SECS;

	// 2. hold the tower, open the arena
	held = hold_tower();
	zone = tod_arena_data::arena_zone();
	if ( !isdefined( level.zones[ zone ] ) )
	{
		dev_log( "ABORT reason=no_zone zone=" + zone );
		release_tower( held );
		if ( TOD_ARENA_COST > 0 ) payer zm_score::add_to_player_score( TOD_ARENA_COST );   // refund: nothing happened
		return;
	}
	zm_zonemgr::enable_zone( zone );
	// spawning ALLOWED while the party is inside: stock's zombie think still
	// walks level.zm_loc_types (built from active + allowed zones) before it
	// honours our chosen spot, and with the party here the arena is the only
	// active zone. Stock's own round spawner is held by the flag (hold_tower).
	level.zones[ zone ].is_spawning_allowed = true;
	level.tod_trial_box = arena_box();
	level.tod_arena_active = true;
	level.tod_arena_dmg_mult = dmg_mult( lvl );
	tod_atmosphere::arena_music_start();   // 2026-09-28 (user): the boss music plays for the arena fight

	// 3. the jump
	tod_teleport::discharge( org );
	land = tod_arena_data::arena_arrivals();
	centre = tod_arena_data::arena_center();
	party = playing_players();
	for ( i = 0; i < party.size; i++ )
	{
		dst = land[ i % land.size ];
		face = VectorToAngles( dst - centre );   // outward: each player faces the walls the enemies rise from
		party[ i ] SetOrigin( dst );
		party[ i ] SetPlayerAngles( ( 0, face[ 1 ], 0 ) );
	}
	level.tod_tp_stamp = ( isdefined( level.tod_tp_stamp ) ? level.tod_tp_stamp + 1 : 1 );
	WAIT_SERVER_FRAME;
	tod_teleport::fx_burst( "tod_tp_kino", centre + ( 0, 0, 4 ), 3.0 );
	tod_teleport::discharge( centre );
	dev_log( "ENTER level=" + lvl + " set=" + set.name + " party=" + party.size + " hp_mult=" + hp_mult( lvl ) + " dmg_mult=" + level.tod_arena_dmg_mult
		+ " zombies/wave=" + zombie_count( set, lvl ) + " refunded=" + held.refunded );
	wait TOD_ARENA_LAND_SECS;

	// 4. the waves
	for ( w = 1; w <= TOD_ARENA_WAVES; w++ )
	{
		if ( lvl >= TOD_ARENA_LEVELS && w == TOD_ARENA_WAVES )
			boss_wave( lvl, w );   // THE KEEPER (docs/186)
		spawn_wave( set, lvl, w );
		wait_wave_clear( lvl, w );
		if ( w < TOD_ARENA_WAVES )
			wait TOD_ARENA_WAVE_GAP;
	}

	// 5. the win
	arena_win( lvl, held );
}

function arena_win( lvl, held )
{
	level endon( "end_game" );
	level.tod_arena_dmg_mult = undefined;
	dev_log( "WIN level=" + lvl );

	// everyone gets a card: the downed are stood back up first
	foreach ( p in playing_players() )
		if ( p laststand::player_is_in_laststand() )
			p thread zm_laststand::auto_revive( p );
	foreach ( p in playing_players() )
		p IPrintLnBold( "ARENA LEVEL " + lvl + " CLEARED" );
	wait 1.0;

	// THE CARD, in a frozen world (set_world_pause first so nothing lands
	// between the win and the pick, then run_upgrade_event)
	tod_upgrades::set_world_pause( true );
	wait 1.5;
	tod_upgrades::run_upgrade_event();
	if ( IS_TRUE( level.tod_upgrade_pause ) && !isdefined( level.tod_station_pause_owner ) )
		tod_upgrades::set_world_pause( false );   // the empty-deal release (nobody had anything left)
	level.tod_arena_level = lvl + 1;
	dev_log( "DEALT level=" + lvl + " next=" + level.tod_arena_level );

	// back to the tower: the top bay
	dst = tod_arena_data::return_org();
	rz = tod_arena_data::return_zone();
	if ( isdefined( level.zones[ rz ] ) && !IS_TRUE( level.zones[ rz ].is_enabled ) )
	{
		zm_zonemgr::enable_zone( rz );
		dev_log( "RETURN enabled_zone=" + rz );
	}
	centre = tod_arena_data::arena_center();
	tod_teleport::fx_burst( "tod_tp_charge", centre + ( 0, 0, 40 ), 1.3, "tod_tp_charge_field" );
	wait 0.8;
	tod_teleport::discharge( centre );
	party = playing_players();
	for ( i = 0; i < party.size; i++ )
	{
		ang = i * 360 / party.size;
		off = ( 0, 0, 0 );
		if ( party.size > 1 )
			off = ( Cos( ang ) * TOD_ARENA_RING, Sin( ang ) * TOD_ARENA_RING, 0 );
		party[ i ] SetOrigin( dst + off );
		party[ i ] SetPlayerAngles( ( 0, tod_arena_data::return_yaw(), 0 ) );
	}
	level.tod_tp_stamp = ( isdefined( level.tod_tp_stamp ) ? level.tod_tp_stamp + 1 : 1 );
	WAIT_SERVER_FRAME;
	tod_teleport::fx_burst( "tod_tp_kino", dst + ( 0, 0, 4 ), 3.0 );
	tod_teleport::discharge( dst );

	// the arena closes, the tower resumes
	if ( isdefined( level.tod_trial_box ) && IS_TRUE( level.tod_trial_box.tod_arena ) )
		level.tod_trial_box = undefined;
	level.tod_arena_active = false;
	tod_atmosphere::arena_music_end();   // a random already-unlocked floor track comes back (2026-09-28)
	zone = tod_arena_data::arena_zone();
	if ( isdefined( level.zones[ zone ] ) )
		level.zones[ zone ].is_spawning_allowed = false;   // nobody there; never a stock spawn in an empty arena
	release_tower( held );
	level notify( "tod_stray_pump" );
	dev_log( "RETURN level=" + lvl + " party=" + party.size + " at=" + dst + ( level.tod_arena_level > TOD_ARENA_LEVELS ? " CONQUERED" : "" ) );
	if ( level.tod_arena_level > TOD_ARENA_LEVELS )
		foreach ( p in playing_players() )
			p IPrintLnBold( "THE BATTLE ARENA IS CONQUERED" );
}
