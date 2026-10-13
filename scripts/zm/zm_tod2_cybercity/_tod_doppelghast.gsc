// =============================================================================
// _tod_doppelghast.gsc — THE DOPPELGHAST (BO6's two-headed "ghoul"), ported
// from Tower of Doom II: Hellbound's _tod_bo6_dev.gsc (docs/160 §9).
//
// User 2026-09-24: "In this room after some time if players dont leave after
// 1:30 dopplghast will start to spawn in every 30 seconds." — THE FALL's
// hunters (_tod_fall::hunters_watch owns the clock; this module owns the
// actor).
//
// WHAT CAME FROM HELLBOUND, UNCHANGED IN SPIRIT: the aitype
// (spawner_hb_doppelghast_dev — hb_bo6_dev_ai.gdt, its .ai_am / .ai_ast in
// animtables/, the zm_zombie ASM + BT), the model + nine converted BO6 clips
// (hb_doppelghast.gdt), the two juke clips and their root-motion paths
// (_tod_doppelghast_motion.gsh), the chase / sprint-burst / juke / melee /
// death-burst behaviour, the 1.5 playback walk rate, and the BO6 source audio
// (_tod_bo6_audio.gsc + its generated notetrack table; the ghoul rows of
// Hellbound's hb_bo6_enemy_audio.csv as sound/aliases/hb_bo6_ghoul.csv).
// WHAT THIS MAP DOES DIFFERENTLY: no Amalgam, no dev showcase, no field-boss
// scaling, no Hellbound class-path stuns; the death lane is THIS map's elite
// lane (tod_luck::boss_kill -> the kill confirm, grant_elite_reward -> the
// killer's 500 x2x x BOUNTY, our own corpse delete); the spawn tell is the
// hound entrance's lightning; the stuck relocation is a navmesh query round
// the target, hall risers while the crown phase holds.
//
// CONTRACTS: the actor is boss-flagged (is_boss / acc_is_boss /
// acc_is_mini_boss + tod_boss_custom_speed) so the horde speed sweep, corpse
// cleanup and the elite roof all treat it as an elite; it drives its own
// animation rate from chase() every 0.25 s (0.05 under a world pause, the
// same freeze set_world_pause writes). `self.tod_doppelghast` marks it for
// _tod_fall::clear_hall, which deletes any left inside the sealed crown.
//
// DIAGNOSTICS: [TOD_DOPPEL] SPAWN / READY / MELEE / DEATH / RELOCATE /
// DENIED print without the dev flag while TOD_DOPPEL_LOG is 1 (first
// playtests — zero before publish); the juke / sprint chatter is dev-only.
// =============================================================================

#using scripts\shared\flag_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_utility;
#using scripts\zm\_zm_spawner;
#using scripts\shared\ai\zombie_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_bosses;         // grant_elite_reward (the killer's 500)
#using scripts\zm\zm_tod2_cybercity\_tod_luck;           // boss_kill (luck + the kill confirm)
#using scripts\zm\zm_tod2_cybercity\_tod_zombie_speed;   // health_mult (the party HP table)
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;     // GENERATED: in_hall, hall_riser_orgs
#using scripts\zm\zm_tod2_cybercity\_tod_bo6_audio;      // the BO6 source audio (Hellbound's module)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;   // play_sound_at_origin (host-based 3D sound, proven)
#using scripts\zm\zm_tod2_cybercity\_tod_elite_fx;       // PK26: the death charge + blast, the juke smear, the claw glow

#insert scripts\shared\shared.gsh;

#using_animtree( "generic" );
#precache( "model", "hb_bo6_doppelghast" );
#precache( "model", "tod_doppelgast_black_robot" );
#precache( "fx", "blood/fx_blood_impact_exp_body_lg_zmb" );
#precache( "fx", "blood/fx_blood_neck_spray_zmb" );

#define TOD_DOPPEL_SPAWNER        "spawner_hb_doppelghast_dev"
// THE FASTER DOPPELGHAST (Hellbound, user 2026-09-18: "50% faster without
// causing regressions especially in the animation"): a PLAYBACK multiplier on
// the ASM locomotion (run AND the sprint burst), so root motion and the clip
// scale together. NOT while attacking (melee is AnimScripted at its own rate
// and its 0.6 s hit marker is authored at 1.0), NOT while juking (the juke
// path is timed to the 30 fps root motion), and RESET TO 1.0 ON DEATH so the
// death clip keeps its length and the 3 s gore burst still lands mid-fall.
// 2026-10-04 (user, first real playthrough: "Doppleghast are way too fast"):
// 1.5 -> 1.0, the clip's own authored pace. The sprint burst is rarer and shorter
// too (TOD_DOPPEL_SPRINT_*), so a closing burst is a tell, not the default.
// 2026-10-05 (user, next run: "Doppleghast are a bit too slow with the changes"): HALFWAY BACK - the walk
// 1.0 -> 1.25 and the sprint bursts between the two (every 4.75-8 s for 1.15-1.95 s; 1.5 / 3.5-6.5 / 1.3-2.3 was
// "way too fast", 1.0 / 6-9.5 / 1-1.6 "a bit too slow").
#define TOD_DOPPEL_WALK_RATE      1.25
#define TOD_DOPPEL_SPRINT_GAP_MIN 4750   // ms between sprint bursts (6000..9500 on 10-04, 3500..6500 before)
#define TOD_DOPPEL_SPRINT_GAP_MAX 8000
#define TOD_DOPPEL_SPRINT_MIN     1150   // ms a burst lasts (1000..1600 on 10-04, 1300..2300 before)
#define TOD_DOPPEL_SPRINT_MAX     1950
// ELITE HEALTH (user 2026-10-04, same run: "Elites dont have enough HP"). The run's
// log had a 912-HP guardian Doppelghast die about a second after the player
// stepped into its dome, and round elites die 1-3 s after the reveal. ONE knob
// for every elite that takes its HP from hunter_hp() (the round director, the
// crown ramp, the Battle Arena, the haven guardians and every Mangler): the
// `units` each caller passes stay its RELATIVE weight, this scales them all.
#define TOD_ELITE_HP_MULT         4
#define TOD_DOPPEL_MELEE_DAMAGE   35
#define TOD_DOPPEL_DEATH_RADIUS   128
#define TOD_DOPPEL_DEATH_DAMAGE   25
#define TOD_DOPPEL_TELL_SECS      1.2    // ghosted over the ground lightning before the reveal (the hound lane)
#define TOD_DOPPEL_STUCK_SECS     12     // no progress for this long -> relocate
#define TOD_DOPPEL_CORPSE_SECS    7      // the source death clip is 199 frames at 30 fps
#define TOD_DOPPEL_LOG            1      // TEMPORARY — prints with dev OFF for the first playtests; zero before publish

#namespace tod_doppelghast;

// The juke root-motion table (generated). Inserted AFTER the namespace line on
// purpose: a function inserted before it lands in the file's default namespace
// and the unqualified juke_root_path() call below then fails to link
// ("Unresolved external", map failed to load 2026-09-24). Hellbound does the same.
#insert scripts\zm\zm_tod2_cybercity\_tod_doppelghast_motion.gsh;

function log( msg )
{
	if ( !TOD_DOPPEL_LOG && !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_DOPPEL] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_DOPPEL] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function init()
{
	tod_bo6_audio::init();
	level.tod_doppel_generation = 0;
	level.tod_doppel_alive = 0;
}

// PUBLIC — living Doppelghasts.
function alive_count()
{
	n = 0;
	foreach ( a in GetAISpeciesArray( "all", "all" ) )
		if ( isdefined( a ) && isalive( a ) && IS_TRUE( a.tod_doppelghast ) )
			n++;
	return n;
}

// PUBLIC — a random living, upright, playing player (the hunt's first target).
function target_player()
{
	c = [];
	foreach ( p in GetPlayers() )
		if ( valid_target( p ) )
			c[ c.size ] = p;
	if ( c.size == 0 )
		return undefined;
	return c[ RandomInt( c.size ) ];
}

function valid_target( p )
{
	if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
		return false;
	if ( IS_TRUE( p.ignoreme ) || IS_TRUE( p.tod_jumppad_flying ) )
		return false;
	if ( isdefined( p.sessionstate ) && p.sessionstate != "playing" )
		return false;
	if ( !( zm_utility::is_player_valid( p ) ) )
		return false;
	return true;
}

// HP = `units` zombies of the current round at this party's table, x TOD_ELITE_HP_MULT.
function hunter_hp( units )
{
	base = 15;   // map 1: 150 (power scale / 10, 2026-09-25)
	if ( isdefined( level.zombie_health ) && level.zombie_health > 0 )
		base = level.zombie_health;
	hp = int( base * units * tod_zombie_speed::health_mult() * TOD_ELITE_HP_MULT + 0.5 );
	if ( hp < 50 * TOD_ELITE_HP_MULT )   // map 1: 500
		hp = 50 * TOD_ELITE_HP_MULT;
	return hp;
}

// PUBLIC — spawn ONE Doppelghast at org, hunting `target` (a valid player, or
// a random one), with `units` zombies of HP. Returns the actor or undefined
// (actor pool / no target). Ghosted until the tell; every contract in
// setup_actor / initialize_actor below.
function spawn_hunter( org, target, units )
{
	if ( !isdefined( target ) || !valid_target( target ) )
		target = target_player();
	if ( !isdefined( target ) )
	{
		log( "DENIED reason=no_target" );
		return undefined;
	}
	if ( GetFreeActorCount() < 1 )
	{
		log( "DENIED reason=actor_pool" );
		return undefined;
	}
	facing = VectorToAngles( target.origin - org );
	actor = SpawnActor( TOD_DOPPEL_SPAWNER, org, ( 0, facing[ 1 ], 0 ), "tod_doppelghast", true );
	if ( !isdefined( actor ) )
	{
		log( "DENIED reason=spawn_failed spawner=" + TOD_DOPPEL_SPAWNER );
		return undefined;
	}
	level.tod_doppel_generation++;
	setup_actor( actor, target, units, level.tod_doppel_generation );
	log( "SPAWN generation=" + level.tod_doppel_generation + " entity=" + actor GetEntityNumber() + " hp=" + actor.health + " origin=" + org + " round=" + level.round_number + " alive=" + alive_count() );
	return actor;
}

// The one flag set every Doppelghast gets (Hellbound's setup_actor, elite form).
function setup_actor( actor, target, units, generation )
{
	actor.tod_doppelghast = true;
	actor.tod_bo6_dev_kind = "doppelghast";   // read by _tod_bo6_audio (its emit() gate)
	actor.tod_bo6_dev_generation = generation;
	actor.tod_boss_kind = "doppelghast";
	actor.is_boss = true;
	actor.acc_is_boss = true;
	actor.acc_is_mini_boss = true;
	actor.tod_boss_custom_speed = true;
	actor.acc_boss_custom_speed = true;
	actor.ignore_enemy_count = true;
	actor.ignore_round_spawn_failsafe = true;
	actor.no_powerups = true;
	actor.disableAmmoDrop = true;
	actor.ignore_nuke = true;
	actor.spawn_time = GetTime();
	actor.starting_round = level.round_number;
	actor.zombieMeleePlayerCounter = 0;
	actor ClearEntityOwner();
	actor.health = hunter_hp( units );
	actor.maxhealth = actor.health;
	actor.favoriteenemy = target;
	actor.ignoreall = true;
	actor.ignoreme = true;
	actor Ghost();   // hidden until initialize_actor reveals it, after the tell
	actor.tod_bo6_rate = 1.0;
	actor thread initialize_actor();
	actor thread death_watch( generation );
}

function initialize_actor()
{
	self endon( "death" );
	level endon( "end_game" );
	wait 0.05;
	self SetModel( "tod_doppelgast_black_robot" ); // Same native bones/weights; original eye materials.
	self.targetname = "zombie_boss";
	self.animname = "zombie_boss";
	self.is_zombie = true;
	self.allowdeath = true;
	self.gibbed = true;
	self.head_gibbed = true;
	self.force_gib = false;
	self allowedStances( "stand" );
	self setPhysParams( 15, 0, 72 );
	self.goalradius = 32;
	self.disableArrivals = true;
	self.disableExits = true;
	self.ignoreSuppression = true;
	self.grenadeawareness = 0;
	self.badplaceawareness = 0;
	self.a.disablepain = true;
	self.allowpain = false;
	self.allowmelee = false;
	self.canattack = false;
	self.meleeDamage = TOD_DOPPEL_MELEE_DAMAGE;
	self.variant_type = 0;
	self.zombie_move_speed = "run";
	self.zombie_arms_position = "down";
	self.freezegun_damage = 0;
	self.flame_damage_time = 0;
	self.zombie_damaged_by_bar_knockdown = false;
	self.ai_state = "zombie_think";
	self.find_flesh_struct_string = "find_flesh";
	self.zombie_think_done = true;
	self.zombie_init_done = true;
	self.team = level.zombie_team;
	self.updateSight = false;
	self setAvoidanceMask( "avoid none" );
	self PushActors( true );
	self zm_utility::disable_react();
	self zm_utility::init_zombie_run_cycle();
	self.zombie_move_speed = "run";
	self.zombie_arms_position = "down";
	self.variant_type = 0;
	self.needs_run_update = true;
	self.deathanim = %hb_doppelghast_dth_01;
	self.deathFunction = &zm_spawner::zombie_death_animscript;
	self.thundergun_knockdown_func = level.basic_zombie_thundergun_knockdown;
	self.tesla_head_gib_func = &zm_spawner::zombie_tesla_head_gib;
	self thread zm_spawner::enemy_death_detection();
	// THE DEATH EVENT: zm_spawner::zombie_death_event is the ONLY caller of
	// the death-event callbacks (kill feel, _tod_upgrades' class-gun kill
	// hooks, corpse cleanup — which returns early on the boss triad, so the
	// body still belongs to corpse_cleanup below). Level-owned, waits on
	// "death", like _zm_ai_dogs. No double fire: deathFunction runs the OTHER
	// callback list.
	level thread zm_spawner::zombie_death_event( self );
	zm_utility::recalc_zombie_array();

	// THE TELL: ghosted since setup_actor and still ignoreall — the hound
	// entrance's lightning build-up on the ground, the pre-spawn crackle,
	// the hold (the clock stops with the world during a card pause), then
	// the bolt crack and a quake, and the actor is put back on its spot.
	self spawn_tell( self.origin, TOD_DOPPEL_TELL_SECS );

	self EnableAimAssist();
	self Show();
	self.ignoreme = false;
	self.ignoreall = false;
	self.hasSeenFavoriteEnemy = true;
	self SetGoal( self.origin );
	self PathMode( "move allowed" );
	tod_bo6_audio::attach( self, "doppelghast" );
	self notify( "zombie_init_done" );
	self.tod_motion_start = self.origin;
	self.tod_bo6_sprinting = false;
	self.tod_bo6_next_sprint = GetTime() + 1000;
	self.tod_bo6_next_juke = GetTime() + RandomIntRange( 1400, 2600 );
	self.tod_bo6_last_juke = RandomInt( 2 );
	self.tod_bo6_juke_repeats = 0;
	self thread chase();
	self thread attacks();
	self thread rate_reset_on_death();
	log( "READY generation=" + self.tod_bo6_dev_generation + " model=" + self.model + " walk_rate=" + TOD_DOPPEL_WALK_RATE + " in_hall=" + tod_crown_data::in_hall( self.origin ) );
}

// self = the ghosted actor. The hound lane's recipe (_tod_hellhounds::hound_spawn_in).
function spawn_tell( org, secs )
{
	host = undefined;
	if ( isdefined( level._effect ) && isdefined( level._effect[ "lightning_dog_spawn" ] ) )
	{
		host = Spawn( "script_model", org );
		if ( isdefined( host ) )
		{
			host SetModel( "tag_origin" );
			PlayFxOnTag( level._effect[ "lightning_dog_spawn" ], host, "tag_origin" );
		}
	}
	tod_perk_scatter::play_sound_at_origin( org, "zmb_hellhound_prespawn", 4 );
	self SetGoal( self.origin );   // hold the spot; the BT has no target while ignoreall
	elapsed = 0;
	while ( elapsed < secs )
	{
		wait 0.1;
		if ( !IS_TRUE( level.tod_upgrade_pause ) )
			elapsed += 0.1;
	}
	while ( IS_TRUE( level.tod_upgrade_pause ) )
		wait 0.1;
	tod_perk_scatter::play_sound_at_origin( org, "zmb_hellhound_bolt", 4 );
	Earthquake( 0.4, 0.6, org, 800 );
	self ForceTeleport( org, self.angles );   // back on the bolt, whatever the BT did meanwhile
	if ( isdefined( host ) )
		host Delete();
}

// The death clip plays through the same ASM the walk rate scales, and the
// death burst is timed to that clip at 1.0 (3 s = source frame 90). Put the
// rate back the moment it dies; chase() has already ended on "death".
function rate_reset_on_death()
{
	level endon( "end_game" );
	self waittill( "death" );
	if ( !isdefined( self ) )
		return;
	self ASMSetAnimationRate( 1 );
}

function set_gait( speed, variant )
{
	self.zombie_move_speed = speed;
	self.variant_type = variant;
	self.needs_run_update = true;
	self notify( "needs_run_update" );
}

function sprint_state( target )
{
	distance = Distance( self.origin, target.origin );
	if ( self.tod_bo6_sprinting )
	{
		if ( GetTime() >= self.tod_bo6_sprint_end || distance < 110 || IS_TRUE( level.tod_upgrade_pause ) )
		{
			self.tod_bo6_sprinting = false;
			self set_gait( "run", 0 );
			self.tod_bo6_next_sprint = GetTime() + RandomIntRange( TOD_DOPPEL_SPRINT_GAP_MIN, TOD_DOPPEL_SPRINT_GAP_MAX );
			dev_log( "SPRINT_END generation=" + self.tod_bo6_dev_generation + " target_distance=" + distance );
		}
	}
	else if ( GetTime() >= self.tod_bo6_next_sprint && distance > 180 && !IS_TRUE( self.tod_bo6_attacking ) && !IS_TRUE( level.tod_upgrade_pause ) )
	{
		if ( !BulletTracePassed( self.origin + ( 0, 0, 48 ), target.origin + ( 0, 0, 36 ), false, self, target ) )
			return;
		self.tod_bo6_sprinting = true;
		self.tod_bo6_sprint_start = GetTime();
		self.tod_bo6_sprint_origin = self.origin;
		self.tod_bo6_sprint_end = GetTime() + RandomIntRange( TOD_DOPPEL_SPRINT_MIN, TOD_DOPPEL_SPRINT_MAX );
		self set_gait( "super_sprint", 1 );
		dev_log( "SPRINT_START generation=" + self.tod_bo6_dev_generation + " target_distance=" + distance );
	}
}

// Original root paths are preflighted with an actor capsule and floor probes.
// Authored BO3 decisions (Hellbound): irregular jukes during pursuit, then a
// sprint burst. No aim-reading, no teleport dodge.
function juke_world( origin, forward, left, local )
{
	return origin + forward * local[ 0 ] + left * local[ 1 ];
}

function maneuver_segment_clear( start, end )
{
	clearance = PhysicsTraceEx( start + ( 0, 0, 8 ), end + ( 0, 0, 8 ), ( -17, -17, 0 ), ( 17, 17, 88 ), self, true );
	if ( clearance[ "fraction" ] < 0.99 )
		return false;
	floor = PhysicsTraceEx( end + ( 0, 0, 16 ), end - ( 0, 0, 20 ), ( -10, -10, 0 ), ( 10, 10, 4 ), self, true );
	// Reject drops, steep steps and embedded starting points.
	if ( floor[ "fraction" ] < 0.1 || floor[ "fraction" ] > 0.8 )
		return false;
	return true;
}

function try_juke( target )
{
	if ( GetTime() < self.tod_bo6_next_juke )
		return false;
	if ( DistanceSquared( self.origin, target.origin ) < 62500 || Abs( self.origin[ 2 ] - target.origin[ 2 ] ) > 40 )
		return false;
	if ( !BulletTracePassed( self.origin + ( 0, 0, 48 ), target.origin + ( 0, 0, 36 ), false, self, target ) )
		return false;
	side = RandomInt( 2 );
	if ( self.tod_bo6_juke_repeats >= 2 )
		side = 1 - self.tod_bo6_last_juke;
	forward = VectorNormalize( ( target.origin[ 0 ], target.origin[ 1 ], self.origin[ 2 ] ) - self.origin );
	left = ( -forward[ 1 ], forward[ 0 ], 0 );
	origin = self.origin;
	for ( attempt = 0; attempt < 2; attempt++ )
	{
		path = juke_root_path( side );
		previous = origin;
		clear = true;
		for ( frame = 0; frame < path.size; frame += 3 )
		{
			point = juke_world( origin, forward, left, path[ frame ] );
			if ( !self maneuver_segment_clear( previous, point ) )
			{
				clear = false;
				break;
			}
			previous = point;
		}
		endpoint = juke_world( origin, forward, left, path[ path.size - 1 ] );
		if ( clear && self maneuver_segment_clear( previous, endpoint ) )
		{
			self.tod_bo6_juking = true;   // claim before the attack thread can run
			self thread play_juke( target, side, path, origin, forward, left );
			return true;
		}
		side = 1 - side;
	}
	self.tod_bo6_next_juke = GetTime() + RandomIntRange( 1800, 3000 );
	return false;
}

function play_juke( target, side, path, origin, forward, left )
{
	self endon( "death" );
	level endon( "end_game" );
	self.tod_bo6_sprinting = false;
	self.ignoreall = true;
	self.v_zombie_custom_goal_pos = origin;
	attack_anim = %hb_doppelghast_juke_l_short_01;
	if ( side == 1 )
		attack_anim = %hb_doppelghast_juke_r_short_01;
	angles = VectorToAngles( forward );
	self AnimScripted( "note_notify", origin, angles, attack_anim, "normal", undefined, 1, 0.1 );
	tod_bo6_audio::doppel_juke_start( self );   // the push-off whoosh at the clip's frame 5 (its AudioOneShot@ notes never reach script, PK02)
	tod_elite_fx::juke( self );   // PK26: the dark smear along the dodge (the clip's frame-11 effect; dies with a pause or the actor)
	started = GetTime();
	duration = ( path.size - 1 ) / 30.0;
	reason = "complete";
	while ( GetTime() - started < duration * 1000 )
	{
		wait 0.05;
		if ( IS_TRUE( level.tod_upgrade_pause ) )
		{
			reason = "pause";
			break;
		}
		if ( !isdefined( target ) || !( zm_utility::is_player_valid( target ) ) )
		{
			reason = "target_invalid";
			break;
		}
		frame = Int( ( GetTime() - started ) * 0.03 ) + 3;
		if ( frame >= path.size )
			frame = path.size - 1;
		point = juke_world( origin, forward, left, path[ frame ] );
		if ( !self maneuver_segment_clear( self.origin, point ) )
		{
			reason = "path_changed";
			break;
		}
		if ( DistanceSquared( self.origin, target.origin ) < 8100 )
		{
			reason = "melee_range";
			break;
		}
	}
	self StopAnimScripted( 0.15 );
	tod_bo6_audio::doppel_juke_end( self, reason );   // the landing snarl (the clip's last frame; none on a pause's cut)
	self.tod_bo6_juking = false;
	self.ignoreall = IS_TRUE( level.tod_upgrade_pause );
	self set_gait( "run", 0 );
	self.tod_bo6_next_sprint = GetTime();
	self.tod_bo6_next_juke = GetTime() + RandomIntRange( 2200, 5000 );
	if ( self.tod_bo6_last_juke == side )
		self.tod_bo6_juke_repeats++;
	else
		self.tod_bo6_juke_repeats = 1;
	self.tod_bo6_last_juke = side;
	dev_log( "JUKE generation=" + self.tod_bo6_dev_generation + " side=" + side + " reason=" + reason );
}

// THE HUNT RULE (Hellbound 2026-09-19): keep the target while valid and
// reachable, else the nearest reachable player; nobody reachable -> hold the
// current one and let the relocate lane work.
function hunt_target()
{
	current = self.favoriteenemy;
	keep = valid_target( current );
	// THE HAVEN'S GUARDIANS (docs/202 v3): a guardian hunts its own floor only (tod_hunt_filter, _tod_haven::guard_target_ok)
	if ( keep && isdefined( self.tod_hunt_filter ) && !( self [[ self.tod_hunt_filter ]]( current ) ) )
		keep = false;
	if ( keep )
	{
		now = GetTime();
		if ( !isdefined( self.tod_hunt_recheck_ms ) )
			self.tod_hunt_recheck_ms = now + 2000;
		if ( now < self.tod_hunt_recheck_ms )
			return current;
		self.tod_hunt_recheck_ms = now + 2000;
		if ( self FindPath( self.origin, current.origin, false, false ) )
			return current;
	}
	best = undefined;
	best_d = 0;
	foreach ( p in GetPlayers() )
	{
		if ( !valid_target( p ) )
			continue;
		if ( isdefined( self.tod_hunt_filter ) && !( self [[ self.tod_hunt_filter ]]( p ) ) )
			continue;   // not on this guardian's floor
		if ( keep && p == current )
			continue;   // just proved off the mesh this pass
		if ( !( self FindPath( self.origin, p.origin, false, false ) ) )
			continue;
		d = DistanceSquared( self.origin, p.origin );
		if ( !isdefined( best ) || d < best_d )
		{
			best = p;
			best_d = d;
		}
	}
	if ( isdefined( best ) )
		return best;
	if ( keep )
		return current;
	if ( isdefined( self.tod_hunt_filter ) )
		return undefined;   // a guardian with nobody on its floor stands down (never a random player elsewhere)
	return target_player();
}

function chase()
{
	self endon( "death" );
	level endon( "end_game" );
	previous = self.origin;
	stuck = 0;
	while ( 1 )
	{
		wait 0.25;
		if ( IS_TRUE( level.tod_upgrade_pause ) )
		{
			// stand like the pause does (set_world_pause writes the same 0.05)
			if ( isdefined( self.favoriteenemy ) )
				self sprint_state( self.favoriteenemy );
			self.ignoreall = true;
			self.v_zombie_custom_goal_pos = self.origin;
			self ASMSetAnimationRate( 0.05 );
			continue;
		}
		rate = 1.0;
		if ( !IS_TRUE( self.tod_bo6_attacking ) && !IS_TRUE( self.tod_bo6_juking ) )
			rate = TOD_DOPPEL_WALK_RATE;
		// THE HAVEN'S FIELD (docs/202): 0.67 inside a safe-zone dome — while it
		// MOVES only: the juke and the melee marker are timed at 1.0 (above).
		if ( isdefined( self.tod_safe_mult ) && !IS_TRUE( self.tod_bo6_attacking ) && !IS_TRUE( self.tod_bo6_juking ) )
			rate *= self.tod_safe_mult;
		self ASMSetAnimationRate( rate );
		if ( IS_TRUE( self.tod_bo6_attacking ) || IS_TRUE( self.tod_bo6_juking ) )
		{
			self.v_zombie_custom_goal_pos = self.origin;
			continue;
		}
		self.ignoreall = false;
		target = self hunt_target();
		if ( !isdefined( target ) )
		{
			// a haven guardian with no target walks home (tod_hunt_home); anyone else holds
			self.v_zombie_custom_goal_pos = ( isdefined( self.tod_hunt_home ) ? self.tod_hunt_home : self.origin );
			continue;
		}
		self.favoriteenemy = target;
		if ( self try_juke( target ) )
			continue;
		self sprint_state( target );
		self.hasSeenFavoriteEnemy = true;
		self.v_zombie_custom_goal_pos = target.origin;
		if ( DistanceSquared( self.origin, previous ) < 64 && DistanceSquared( self.origin, target.origin ) > 22500 )
			stuck += 0.25;
		else
		{
			stuck = 0;
			previous = self.origin;
		}
		if ( !IS_TRUE( self.tod_bo6_attacking ) && stuck >= TOD_DOPPEL_STUCK_SECS )
		{
			org = reloc_point( target );
			if ( isdefined( org ) )
			{
				self ForceTeleport( org );
				self.tod_motion_start = org;
				log( "RELOCATE generation=" + self.tod_bo6_dev_generation + " stuck=" + stuck + " to=" + org );
				stuck = 0;
				previous = org;
			}
		}
	}
}

// A spot to come back from being stuck: a hall riser while the crown phase
// holds and the target is inside (the farthest one from every player), else
// a navmesh point 200-600 round the target that no player stands near.
function reloc_point( target )
{
	// THE HAVEN'S GUARDIANS (docs/202 v4: "the elites are not allowed to leave the dome"): a
	// guardian's stuck relocation lands on a spot inside its own field (_tod_haven::guard_reloc).
	// Both elites come here (_tod_mangler::spawn_position calls this with the Mangler as self).
	if ( isdefined( self.tod_reloc_fn ) )
		return self [[ self.tod_reloc_fn ]]( target );
	if ( !valid_target( target ) ) return undefined;
	for ( tries = 0; tries < 3; tries++ )
	{
		p = tod_bosses::pick_spawn_point( target.origin );
		if ( !isdefined( p ) ) continue;
		// Navigation queries can reach the separate crown island through air.
		if ( tod_crown_data::on_crown_island( p ) != tod_crown_data::on_crown_island( target.origin ) ) continue;
		if ( IS_TRUE( level.tod_fall_sealed ) && !IS_TRUE( level.tod_fall_return_open ) && tod_crown_data::in_hall( p ) ) continue;
		ok = true;
		foreach ( pl in GetPlayers() )
		{
			if ( isdefined( pl ) && isalive( pl ) && DistanceSquared( p, pl.origin ) < 40000 )
			{
				ok = false;
				break;
			}
		}
		if ( ok )
			return p;
	}
	return undefined;
}

// PUBLIC — the hall riser farthest from the nearest living player (never
// undefined: the hall always has four).
function hall_spot()
{
	orgs = tod_crown_data::hall_riser_orgs();
	best = orgs[ 0 ];
	best_d = -1;
	for ( i = 0; i < orgs.size; i++ )
	{
		near = -1;
		foreach ( p in GetPlayers() )
		{
			if ( !isdefined( p ) || !isalive( p ) )
				continue;
			d = DistanceSquared( orgs[ i ], p.origin );
			if ( near < 0 || d < near )
				near = d;
		}
		if ( near < 0 )
			near = 0;
		if ( near > best_d )
		{
			best = orgs[ i ];
			best_d = near;
		}
	}
	return best;
}

function attacks()
{
	self endon( "death" );
	level endon( "end_game" );
	attack_anim = %hb_doppelghast_stn_melee_01;
	hit_time = 0.6;   // original hit marker: frame 18 at 30 fps
	recovery = 0.75;
	reach = 90;
	while ( 1 )
	{
		wait 0.1;
		if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( self.tod_bo6_juking ) )
			continue;
		target = self.favoriteenemy;
		// IS_TRUE( ignoreme ): the chase already drops an untargetable (cloaked) player, but the
		// favourite outlives that, so the swing checks it too (2026-09-27, INVISIBILITY CLOAK)
		if ( !isdefined( target ) || !( zm_utility::is_player_valid( target ) ) || IS_TRUE( target.ignoreme ) )
			continue;
		if ( DistanceSquared( self.origin, target.origin ) > reach * reach )
			continue;
		if ( !BulletTracePassed( self.origin + ( 0, 0, 48 ), target.origin + ( 0, 0, 36 ), false, self, target ) )
			continue;
		self.tod_bo6_attacking = true;
		self.ignoreall = true;
		angles = VectorToAngles( ( target.origin[ 0 ], target.origin[ 1 ], self.origin[ 2 ] ) - self.origin );
		self AnimScripted( "note_notify", self.origin, angles, attack_anim );
		// the swing's whoosh + attack scream at the clip's own frames 3 / 13: its
		// AudioOneShot@ notetracks never reach script, so the swing was silent (PK02)
		tod_bo6_audio::doppel_swing( self );
		tod_elite_fx::claw( self );   // PK26: the windup's tell - a red-hot claw for the clip's own effect window (frames 2-22)
		wait hit_time;
		hit = false;
		if ( !IS_TRUE( level.tod_upgrade_pause ) && isdefined( target ) && zm_utility::is_player_valid( target )
		     && DistanceSquared( self.origin, target.origin ) < ( reach + 30 ) * ( reach + 30 )
		     && BulletTracePassed( self.origin + ( 0, 0, 48 ), target.origin + ( 0, 0, 36 ), false, self, target ) )
		{
			target DoDamage( self.meleeDamage, self.origin, self, self, "none", "MOD_MELEE" );
			hit = true;
		}
		log( "MELEE generation=" + self.tod_bo6_dev_generation + " hit=" + hit + " round=" + level.round_number );
		wait recovery;
		self StopAnimScripted( 0.2 );
		self.tod_bo6_attacking = false;
		self.ignoreall = false;
		self.needs_run_update = true;
		self notify( "needs_run_update" );
	}
}

// THIS MAP'S ELITE DEATH LANE (the hound precedent): luck + the kill confirm
// for the killer, the killer's 500 (x2x x BOUNTY, the bottle roll), the BO6
// death vox, then the level-owned burst + delete.
function death_watch( generation )
{
	level endon( "end_game" );
	self waittill( "death", attacker );
	if ( isdefined( attacker ) && isplayer( attacker ) )
		tod_luck::boss_kill( attacker, "doppelghast" );
	org = undefined;
	if ( isdefined( self ) )
		org = self.origin;
	tod_bosses::grant_elite_reward( "DOPPELGHAST", attacker, org );
	log( "DEATH generation=" + generation + " killer=" + ( ( isdefined( attacker ) && isplayer( attacker ) ) ? attacker GetEntityNumber() : -1 ) + " round=" + level.round_number + " alive=" + alive_count() );
	if ( isdefined( self ) )
	{
		tod_bo6_audio::death( self, "doppelghast" );
		level thread corpse_cleanup( self );
	}
}

function corpse_cleanup( actor )
{
	level endon( "end_game" );
	level thread death_burst( actor );
	wait TOD_DOPPEL_CORPSE_SECS;
	if ( isdefined( actor ) )
		actor Delete();
}

function fx_host( effect, org )
{
	host = Spawn( "script_model", org );
	if ( !isdefined( host ) )
		return undefined;
	host SetModel( "tag_origin" );
	PlayFXOnTag( effect, host, "tag_origin" );
	return host;
}

function expire_fx( seconds )
{
	level endon( "end_game" );
	wait seconds;
	if ( isdefined( self ) )
		self Delete();
}

// Level-owned carriers survive the source death clip's frame-61 ragdoll. The BO6
// frame-2/5/90 events cannot be exported: the frame-2 squib is BO3 blood, the
// frame-5 torso charge and the frame-90 needle blast are PK26's composed effects
// (_tod_elite_fx: the build-up, then the blast with its hurt zone drawn on the
// floor), and the stock gore burst still plays with the blast.
function death_burst( actor )
{
	level endon( "end_game" );
	if ( !isdefined( actor ) || IS_TRUE( actor.tod_bo6_death_burst_started ) )
		return;
	actor.tod_bo6_death_burst_started = true;
	generation = actor.tod_bo6_dev_generation;
	origin = actor GetTagOrigin( "j_spine4" );
	if ( !isdefined( origin ) )
		origin = actor.origin + ( 0, 0, 48 );
	started = GetTime();
	wait 0.1;
	squib = fx_host( "blood/fx_blood_neck_spray_zmb", origin );
	if ( isdefined( squib ) )
		squib thread expire_fx( 1 );
	// PK26 THE CHARGE: from this squib to the blast (TOD_ELITE_FX_CHARGE_MS), riding the torso
	charge = tod_elite_fx::charge_start( origin, generation );
	while ( GetTime() - started < 3000 )
	{
		if ( isdefined( actor ) )
		{
			torso = actor GetTagOrigin( "j_spine4" );
			if ( isdefined( torso ) )
				origin = torso;
		}
		tod_elite_fx::charge_follow( charge, origin );
		wait 0.05;
	}
	tod_elite_fx::charge_end( charge, generation );
	burst = fx_host( "blood/fx_blood_impact_exp_body_lg_zmb", origin );
	if ( isdefined( burst ) )
		burst thread expire_fx( 3 );
	tod_elite_fx::blast( origin, actor, generation );   // PK26 THE BLAST: on the floor, the hurt zone (TOD_DOPPEL_DEATH_RADIUS) drawn round it
	tod_bo6_audio::sound_at( "hb_bo6_evt_ai_ghoul_death_oneshot", origin, 10 );   // a carrier: PlaySoundAtPosition is silent for a custom alias here (PK02)
	if ( isdefined( actor ) )
		actor Hide();
	// a small, avoidable death blast (Hellbound balance); world LOS keeps it
	// out of a sealed room; never under a world pause
	if ( !IS_TRUE( level.tod_upgrade_pause ) )
	{
		foreach ( player in GetPlayers() )
		{
			if ( !( zm_utility::is_player_valid( player ) ) )
				continue;
			center = player.origin + ( 0, 0, 36 );
			if ( DistanceSquared( center, origin ) > TOD_DOPPEL_DEATH_RADIUS * TOD_DOPPEL_DEATH_RADIUS )
				continue;
			if ( !BulletTracePassed( origin, center, false, actor, player ) )
				continue;
			player DoDamage( TOD_DOPPEL_DEATH_DAMAGE, origin, actor, actor, "none", "MOD_PROJECTILE_SPLASH" );
		}
	}
}
