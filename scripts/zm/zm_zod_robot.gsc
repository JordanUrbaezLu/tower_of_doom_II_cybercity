#using scripts\codescripts\struct;
#using scripts\shared\ai\zombie_death;
#using scripts\shared\ai\zombie_utility;
#using scripts\shared\animation_shared;
#using scripts\shared\array_shared;
#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\name_shared;
#using scripts\shared\scene_shared;
#using scripts\shared\system_shared;
#using scripts\zm\_zm;
#using scripts\zm\_zm_audio;
#using scripts\zm\_zm_bgb;
#using scripts\zm\_zm_laststand;
#using scripts\zm\_zm_score;
#using scripts\zm\_zm_spawner;
#using scripts\zm\_zm_unitrigger;
#using scripts\zm\_zm_utility;
#using scripts\zm\archetype_zod_companion;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#namespace zm_zod_robot;

#precache( "fx", "zombie/fx_robot_helper_jump_landing_zod_zmb" );
#precache( "fx", "zombie/fx_robot_helper_trail_sky_zod_zmb" );
#precache( "fx", "zombie/fx_robot_helper_ground_tell_zod_zmb" );

REGISTER_SYSTEM_EX( "zm_zod_robot", &__init__, undefined, undefined )

// ============================== INITIALIZE ==============================

function __init__()
{
	// # CLIENTFIELD REGISTRATION
	clientfield::register( "scriptmover", "robot_switch", VERSION_SHIP, 1, "int" );
	clientfield::register( "world", "robot_lights", VERSION_SHIP, 2, "int" );
	// # CLIENTFIELD REGISTRATION
	
	// # FLAGS
	level flag::init( "ee_complete" );
	level flag::init( "police_box_ready" );
	level flag::init( "police_box_in_use" );
	level flag::init( "police_box_hide" );
	// # FLAGS
	
	// # VARIABLES AND SETTINGS
	level.n_civil_protector_cost = 2000;
	level.zombie_robot_spawners = getEntArray( "zombie_robot_spawner", "script_noteworthy" );
	level.zombie_robot_gold_spawners = getEntArray( "zombie_robot_gold_spawner", "script_noteworthy" );
	// # VARIABLES AND SETTINGS
	
	// # REGISTER FX
	level._effect[ "robot_landing" ] = "zombie/fx_robot_helper_jump_landing_zod_zmb";
	level._effect[ "robot_sky_trail" ] = "zombie/fx_robot_helper_trail_sky_zod_zmb";
	level._effect[ "robot_ground_spawn" ] = "zombie/fx_robot_helper_ground_tell_zod_zmb";
	// # REGISTER FX	
	
	// # REGISTER CALLBACKS / OVERRIDES
	zombie_utility::add_zombie_gib_weapon_callback( "ar_standard_companion", &zod_robot_gib_validate, &zod_robot_gib_head_validate );
	level.check_end_solo_game_override = &check_end_solo_game_override;
	level._game_module_game_end_check = &_game_module_game_end_check;
	zm::register_player_damage_callback( &zod_robot_player_damage_override );
	// # REGISTER CALLBACKS / OVERRIDES
	
	// (THREAD LOGIC: the police-box callbox chain, the fuse craftable and the Civil Protector
	// upgrade trigger left with the Map 1 purge, 2026-10-04 - Map 2 has no police box. The
	// AI companions use this module only for the archetype, landing damage and vox.)
}

function zod_robot_player_damage_override( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, psOffsetTime )
{
	if ( isdefined( eAttacker ) && IS_TRUE( eAttacker.tod_is_partner ) ) return 0;
	// [acc] FIXED 2026-07-02 (GOD-MODE KILLER): stock chain semantics - _zm.gsc
	// check_player_damage_callbacks returns the FIRST callback result != -1 and SKIPS the rest.
	// The pack's original `return iDamage` here short-circuited EVERY later player-damage
	// callback, including _acc_elites' god-mode zeroing ("I was dying in god mode"). Return -1
	// = "no opinion", let the chain continue. (The pack's ally no-damage guard checked the
	// TYPO'd field `.archeype` so it never fired anyway - and it must STAY dead for the
	// ROGUE PROTECTOR boss, whose archetype IS zod_companion and whose bullets must damage
	// players; his hit strength is tuned in the weapon GDT playerDamage field instead.)
	return -1;
}

// ============================== INITIALIZE ==============================

// ============================== CALLBACKS / OVERRIDES ==============================

function check_end_solo_game_override()
{
	if ( isDefined( level.ai_robot ) )
		return 1;
	
	return 0;
}

function _game_module_game_end_check()
{
	if ( IS_TRUE( level.reviving_a_player ) )
		return 0;
	
	return 1;
}

// ============================== CALLBACKS / OVERRIDES ==============================

// ============================== FUNCTIONALITY ==============================

// Shared by the Civil Protector's landing and _tod_bosses::landing_kill_splash.
// Every boss / elite carries a boss flag or tod_boss_kind. (The armored sprinter
// carried neither and was read by its own flag here until it retired whole,
// 2026-10-05.) Keep this specific to entrance damage; do not change global
// enemy balance.
function landing_splash_immune( actor )
{
	if ( !isdefined( actor ) || !IsAlive( actor ) ) return true;
	return ( IS_TRUE( actor.is_boss ) || IS_TRUE( actor.acc_is_boss )
	      || IS_TRUE( actor.acc_is_mini_boss ) || isdefined( actor.tod_boss_kind ) );
}

function zod_robot_do_landing_damage( v_origin, e_attacker, n_radius )
{
	a_ai_zombies = array::get_all_closest( v_origin, getAITeamArray( "axis" ), undefined, undefined, n_radius );
	foreach ( ai_zombie in a_ai_zombies )
	{
		if ( landing_splash_immune( ai_zombie ) )
			continue;
		if ( isDefined( e_attacker ) )
			ai_zombie doDamage( ai_zombie.health + 10000, ai_zombie.origin, e_attacker );
		else
			ai_zombie doDamage( ai_zombie.health + 10000, ai_zombie.origin );
		
		n_distance_sqr = distanceSquared( ai_zombie.origin, v_origin );
		n_dist_mult = n_distance_sqr / SQR( n_radius );
		v_fling = ai_zombie.origin - v_origin;
		v_fling = v_fling + vectorScale( ( 0, 0, 1 ), 15 );
		v_fling = vectorNormalize( v_fling );
		n_size = 50 + 20 * n_dist_mult;
		v_fling = ( v_fling[ 0 ], v_fling[ 1 ], abs( v_fling[ 2 ] ) );
		v_fling = vectorScale( v_fling, n_size );
		ai_zombie startRagdoll();
		ai_zombie launchRagdoll( v_fling );
	}
}

function private zod_robot_gib_head_validate( str_damage_location )
{
	if ( !isDefined( str_damage_location ) )
		return 0;
	
	switch ( str_damage_location )
	{
		case "head":
			return 1;
		case "helmet":
			return 1;
		case "neck":
			return 1;
		default:
			return 0;
		
	}
}

function private zod_robot_gib_validate( n_damage_percent )
{
	return 1;
}

function zod_robot_play_vox( e_entity, str_suffix, n_delay )
{
	e_entity endon("death");
	e_entity endon("disconnect");
	str_alias = "vox_crbt_robot_" + str_suffix;
	n_variants = zm_spawner::get_number_variants(str_alias);
	if ( n_variants <= 0 )
		return;
	
	n_variant = randomIntRange( 0, n_variants + 1 );
	
	if ( isDefined( n_delay ) )
		wait n_delay;
	
	if ( isDefined( e_entity ) && !IS_TRUE( e_entity.is_speaking ) )
	{
		e_entity.is_speaking = 1;
		e_entity PlaySoundWithNotify( str_alias + "_" + n_variant, "sndDone" );
		e_entity waittill( "sndDone" );
		e_entity.is_speaking = 0;
	}
}

// ============================== FUNCTIONALITY ==============================
