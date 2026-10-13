// Archer equipment, docs/168_archer_equipment.md. Internal class key: assault.
// BO3 BulletTrace + ordinary player velocity; never links/teleports the player.
// Retriever uses the recovered BO2 native offhand and script behavior.
#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\system_shared;
#using scripts\shared\laststand_shared;
#using scripts\zm\_zm;
#using scripts\zm\_zm_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_retriever;
#using scripts\zm\zm_tod2_cybercity\_tod_archer_rune;   // the Fire Bow's charged shot (2026-09-26)
#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;
#using scripts\zm\zm_tod2_cybercity\_tod_ability_fx;   // docs/203: the ability feedback (both views)
#using scripts\zm\zm_tod2_cybercity\_tod_upgrade_ui;   // self_toast: THE TOAST (imports only shared: no cycle)
#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#precache( "model", "tod_archer_retriever_world" );
#precache( "model", "tod_archer_hook" );
#precache( "weapon", "tod_archer_retriever_flourish" );
#precache( "weapon", "tod_archer_grapple_view" );
#precache( "fx", "tod/archer/fx_tod_archer_trail" );
#precache( "fx", "tod/archer/fx_tod_archer_impact" );
// 2026-09-26 SFX/VFX pass: the hook bit into a wall with a clank and NO picture,
// and the landing buff (speed + DR) had no tell at all. Both effects are already
// zoned (the spark by the fuse/teleporter work, the charge ring is the Retriever's).
#precache( "fx", "electric/fx_elec_sparks_burst_xsm_omni_blue_os" );   // hook bite
#precache( "fx", "tod/archer/fx_tod_archer_charge" );                  // landing buff
#precache( "rumble", "reload_small" );
#precache( "eventstring", "tod_archer_abil" );
#precache( "eventstring", "tod_archer_aim" );

#define TOD_ARCHER_RANGE       3000
#define TOD_ARCHER_MIN_RANGE   128
#define TOD_ARCHER_SPEED       1300   // max reel speed along the rope
#define TOD_ARCHER_PULL_SECS   4.0
// THE SWING (2026-09-25, user: "more of a swing ... like Pathfinder ... takes
// into account momentum"). The rope never overwrites the player's velocity:
// it adds a pull toward the anchor, removes only the part that would stretch
// the rope, and keeps the sideways part, so a running grapple arcs.
#define TOD_ARCHER_PULL_ACCEL  2200   // units/s^2 added toward the anchor
#define TOD_ARCHER_KICK        450    // minimum reel speed on attach
#define TOD_ARCHER_REEL        600    // rope shortens this much per second
#define TOD_ARCHER_TANG_MAX    1400   // swing (sideways) speed cap (1100 -> 1400 with the steer, 2026-09-26)
// THE STEER (2026-09-26, user: "smooth and correct and fun to use, like a
// swinging grapple, like Pathfinder"). Pathfinder's swing is the MOVEMENT
// STICK: while the rope pulls you in, holding a direction accelerates you
// AROUND the anchor, so a run-up plus a strafe arcs you round it and flings
// you out; JUMP lets go and you keep every bit of speed; nothing slows you
// as you reach the anchor - you fly past it. Read GetNormalizedMovement()
// ([0] forward, [1] right, the athlete's proven read) as a horizontal wish
// in view space, keep only the part PERPENDICULAR to the rope (the rope owns
// the radial axis), and add STEER_ACCEL along it every tick.
#define TOD_ARCHER_STEER_ACCEL 1800   // units/s^2 around the anchor from the stick
#define TOD_ARCHER_STEER_DEAD  0.25   // stick deflection under this = no steer
#define TOD_ARCHER_ARRIVE      100    // release this close to the anchor (was 60; no ease-off any more)
#define TOD_ARCHER_OBSTRUCT_SECS 0.3  // the rope must be blocked this long to detach (0.1 cut swings round corners)
#define TOD_ARCHER_LIFT        220    // hop off the floor while reeling
#define TOD_ARCHER_EXIT_HOP    240    // upward pop when arriving (ledges)
// VERTICAL CAPS (user 2026-09-26, build-11 test: "it's swinging you way too far
// up ... I can go super, super high and just fall down for a couple seconds"):
// the reel pulled UP at the full 1300 u/s and a release mid-pull kept all of it
// (the log: vel_out z=1082). Now the upward part of the swing is capped while
// on the rope, and the upward part of EVERY exit (release / arrive / pinned /
// timeout / obstructed) is capped a little over the ledge hop. Sideways momentum
// is untouched: the swing still carries, it just does not launch you skyward.
#define TOD_ARCHER_UP_MAX      700    // max upward speed while on the rope
#define TOD_ARCHER_EXIT_UP_MAX 320    // max upward speed kept when the rope lets go
// FOOTING (user, build-14 test: "I can land on stuff above where zombies can't get me"):
// the hook only bites where a zombie can follow. The floor under the arrival point
// must have navmesh within TOD_ARCHER_FOOT_R (and within _FOOT_Z of its height); a
// hook with no floor inside TOD_ARCHER_FOOT_DROP below it (a high wall) is allowed:
// you fall to the ground. Refusal reason "no_footing", log GRAPPLE_NO_FOOTING.
#define TOD_ARCHER_FOOT_R      64
#define TOD_ARCHER_FOOT_Z      48
#define TOD_ARCHER_FOOT_DROP   512
#define TOD_ARCHER_UNSTICK     340    // upward nudge when a lip holds you
// THE INVISIBLE WALL (2026-10-05, user: "The grapple, you can kind of just go out of the map ... I wonder if we
// need to build some invisible walls"). A rail's clip stops 168 above its step and the rope lifts you far higher:
// the user's 20:21 run hooked the core wall 280 above the floor-42 stairs, "arrived", kept 895 u/s outward over
// the rail, fell to z -1020 and came back by the Recall at 1 HP. The wall is the play area's own edge - the zone
// volumes, which end at the rails' outer face (every navmesh face sits inside one; THE RECALL calls "no zone at all"
// off the map). On the rope, and in the air after it, the part of the velocity that would carry the archer out of
// every zone over OPEN AIR is removed (solid ahead - the core, a wall - stops you itself); a hook whose arrival
// point is in no zone is refused. Velocity only: never a teleport, and never a roof (going up is not blocked; above
// the zones the column you came up is what is judged). Other classes keep the open tower (user: "Im fine with
// players trying to hack and jump down all the way").
#define TOD_ARCHER_WALL_LOOK   2      // look this many ticks ahead ...
#define TOD_ARCHER_WALL_PAD    20     // ... plus a hull's half-width
#define TOD_ARCHER_WALL_CHEST  36     // test points ride at chest height (stock's own probe tests origin + 40)
#define TOD_ARCHER_WALL_LOG_MS 250    // at most one WALL line per player this often
#define TOD_ARCHER_LOG_EVERY   0.2    // GRAPPLE_TICK sampling, seconds
// PINNED (2026-09-26, the user's build-8 log: "sometimes I'm swinging kind of
// weird"): the rope hooked a crown point OVER the hall wall (line of sight
// across the open roof), the body could not follow - it pressed into the wall
// and the new invisible barrier, slid 2700 u up it and hung there for the rest
// of the 4 s timer, then fell 940 u/s. The rope kept reeling past the body: the
// tell is dist - rope growing while dist stops shrinking. Let go instead.
#define TOD_ARCHER_PIN_SLACK   250    // rope reeled this much shorter than the true distance = the body is held back
#define TOD_ARCHER_PIN_SECS    0.5    // for this long ...
#define TOD_ARCHER_PIN_GAIN    60     // ... while the distance closed less than this
#define TOD_ARCHER_GRACE_SECS  6.0
#define TOD_ARCHER_GRAPPLE_CD  12     // fixed since 2026-09-25 (the card grows range + landing instead)
#define TOD_AERIAL_CD_STEP      0.04   // AERIALIST (2026-09-27): grapple recharge -4% / Lv
#define TOD_AERIAL_WAVE_R       150    // AERIALIST Lv6 landing shockwave radius ...
#define TOD_AERIAL_WAVE_R_LV9   225    // ... and at Lv9
// THE GRAPPLE CARD (2026-09-25, user): 8 levels, every stat on ONE
// logarithmic curve, grapple_curve( lvl ) = ln( 1 + lvl ) / ln( 10 ): big
// early steps that taper, 0 without the card, 1 at Lv9 (9 levels since 2026-09-27). At Lv9:
#define TOD_ARCHER_RANGE_ADD    2000  // +range: 3000 -> 5000
#define TOD_ARCHER_LAND_SPEED   35    // +move speed on landing, percent of scale (base 0.9 -> 1.25)
#define TOD_ARCHER_LAND_DR      60    // damage reduction on landing, percent
#define TOD_ARCHER_LAND_SECS0   0.75  // window length = SECS0 + SECS_ADD * curve
#define TOD_ARCHER_LAND_SECS_ADD 1.75 // Lv1 1.3 s ... Lv9 2.5 s
#define TOD_ARCHER_LAND_WAIT    4.0   // must touch down this soon after the grapple ends
#namespace tod_archer;

REGISTER_SYSTEM( "tod_archer_art", &__init__, undefined )
function __init__()
{
	// Low four bits = player entity number + 1; high bit = dev diagnostics.
	clientfield::register( "scriptmover", "todArcherHook", VERSION_SHIP, 5, "int" );
}

function init()
{
	tod_retriever::init();
	tod_archer_rune::init();
	level.tod_archer_trail_fx = "tod/archer/fx_tod_archer_trail";
	level.tod_archer_impact_fx = "tod/archer/fx_tod_archer_impact";
	level.tod_archer_states = [];
	level.tod_archer_prev_oopa_cb = level.player_out_of_playable_area_monitor_callback;
	level.player_out_of_playable_area_monitor_callback = &playable_area_cb;
	if ( !isdefined( level.player_damage_callbacks ) ) level.player_damage_callbacks = [];
	ArrayInsert( level.player_damage_callbacks, &fall_damage_guard, 0 );
	callback::on_spawned( &on_spawned );
	level thread watch();
	level thread stumble_watch();
	archer_log( "INIT lethal=retriever tactical=grapple no_fall_damage=1 range=" + TOD_ARCHER_RANGE );
}

// NO LANDING STUMBLE, ARCHER ONLY (user 2026-09-26: "remove the slowdown that
// you get when landing ... run full speed right away", then "the slowdown
// landing is only for archer"). The engine's landing deceleration is the host
// dvar jump_slowdownEnable - one value for everyone, so "Archer only" is done
// the way the athlete module did it: the dvar is 0 for exactly as long as an
// Archer is in the air (grappling counts), and back at its shipped value the
// moment none is. THE BREACHER TOO (2026-10-01, user: the Breacher's air steering "like the
// athlete" - map 1's athlete lands clean the same way): an airborne Breacher (a Fusion launch,
// any jump) holds it off as well. A player of another class who lands in that same window also
// lands clean; that is the cost of a host dvar and it is small. The pristine
// value is read once at init (stock's own is 1). Logs STUMBLE off/on edges.
function stumble_watch()
{
	level endon( "end_game" );
	pristine = GetDvarString( "jump_slowdownEnable" );
	if ( !isdefined( pristine ) || pristine == "" ) pristine = "1";
	level.tod_archer_stumble_pristine = pristine;
	current = pristine;
	while ( true )
	{
		airborne = false;
		players = GetPlayers();
		foreach ( p in players )
		{
			if ( !( is_archer( p ) || is_breacher( p ) ) || !IsAlive( p ) ) continue;
			if ( !p IsOnGround() || IS_TRUE( p.tod_grappling ) ) { airborne = true; break; }
		}
		want = ( airborne ? "0" : pristine );
		if ( want != current )
		{
			SetDvar( "jump_slowdownEnable", want );
			current = want;
			archer_log( "STUMBLE " + ( airborne ? "off (an Archer or Breacher is airborne)" : "on (pristine " + pristine + ")" ) );
		}
		wait 0.05;
	}
}

function is_archer( player )
{
	return isdefined( player ) && isdefined( player.tod_class ) && player.tod_class == "assault";
}

// the Breacher (class key "heavy"): no landing stumble after a jump or a Fusion launch (stumble_watch)
function is_breacher( player )
{
	return isdefined( player ) && isdefined( player.tod_class ) && player.tod_class == "heavy";
}

// Respawn dispatch may happen twice. No per-spawn immortal threads or movers.
function on_spawned()
{
	old = level.tod_archer_states[ self GetEntityNumber() ];
	if ( isdefined( old ) ) delete_axe( old );
	if ( isdefined( old ) ) delete_hook( old );
	if ( isdefined( self.tod_archer_state ) ) self cleanup( "respawn" );
	s = SpawnStruct();
	s.owner = self;
	s.armed = false;
	s.axe_cd = 0;
	s.hook_cd = 0;
	s.grace = 0;
	s.lethal_down = true; // require release after menus/spawn, never fire a held key
	s.tactical_down = true;
	s.jump_down = true;
	s.hud_refresh = 0;
	s.aim_refresh = 0;
	if ( isdefined( old ) ) s.view_restore_controls = IS_TRUE( old.view_restore_controls );
	self.tod_archer_state = s;
	level.tod_archer_states[ self GetEntityNumber() ] = s;
	self tod_retriever::listen();
}

// One level-owned loop can delete a disconnected owner's projectile. A player
// thread with endon(disconnect) cannot run cleanup after its owner disappears.
function watch()
{
	level endon( "end_game" );
	previous = GetTime();
	for ( ;; )
	{
		wait 0.05;
		now = GetTime();
		dt = ( now - previous ) / 1000.0;
		previous = now;
		if ( dt > 0.1 ) dt = 0.1;
		foreach ( s in level.tod_archer_states )
		{
			if ( !isdefined( s ) ) continue;
			if ( !isdefined( s.owner ) )
			{
				delete_axe( s );
				delete_hook( s );
				continue;
			}
			s.owner update( s, dt );
		}
	}
}

function blocked_reason()
{
	if ( !IsAlive( self ) ) return "dead";
	if ( self laststand::player_is_in_laststand() ) return "downed";
	if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( self.tod_menu_frozen ) ) return "menu";
	if ( IS_TRUE( self.tod_jumppad_flying ) || self IsMantling() ) return "movement_owned";
	if ( isdefined( self.is_drinking ) && self.is_drinking > 0 ) return "drinking";
	if ( IS_TRUE( self.is_reviving ) ) return "reviving";
	return "";
}

function update( s, dt )
{
	lethal = self FragButtonPressed();
	tactical = self SecondaryOffhandButtonPressed();
	lethal_edge = press_edge( lethal, s.lethal_down );
	tactical_edge = press_edge( tactical, s.tactical_down );
	jump = self JumpButtonPressed();
	jump_edge = press_edge( jump, s.jump_down );
	s.lethal_down = lethal;
	s.tactical_down = tactical;
	s.jump_down = jump;
	self restore_view_controls( s );
	if ( !is_archer( self ) )
	{
		if ( s.armed ) self cleanup( "class_changed" );
		return;
	}
	if ( !s.armed )
	{
		s.armed = true;
		self tod_retriever::equip( s );   // gives the axe only with the Retriever card (sets flourish_pending then)
		// W3E 2026-10-05: player voice, in the CAPS every other bold line uses (was "ARCHER: hold tactical = grapple, release to let go | no fall damage | ...")
		// RT 2026-10-05: THE TOAST, kind 7 (two lines, the same words: "ARCHER - HOLD YOUR TACTICAL TO GRAPPLE" / "NO FALL
		// DAMAGE - EARN HELL'S RETRIEVER FROM A CARD"), in our typeface; it was a stock-font IPrintLnBold at the draft's end
		self tod_upgrade_ui::self_toast( 7, 0 );
		archer_log( "ARM player=" + self GetEntityNumber() );
		lethal_edge = false;
		tactical_edge = false;
	}
	why = self blocked_reason();
	if ( why != "" )
	{
		if ( IS_TRUE( self.tod_grappling ) ) self end_grapple( why, why != "movement_owned" );
		if ( why == "dead" || why == "downed" )
		{
			self end_axe( why );
			self end_view( why );
			s.grace = 0;
		}
		self DisableOffhandWeapons();
		s.offhand_blocked = true;
		// Paused menus freeze recharge and the projectile; inputs are still
		// sampled above, so releasing the menu never spends a held grenade key.
		if ( isdefined( s.axe ) ) s.axe MoveTo( s.axe.origin, 0.05 );
		stop_axe_audio( s );
		self hud_send();
		return;
	}
	if ( IS_TRUE( s.offhand_blocked ) )
	{
		if ( !isdefined( s.view_weapon ) ) self EnableOffhandWeapons();
		tod_retriever::resume( s );
		s.offhand_blocked = false;
	}
	self tod_retriever::reconcile( s );
	if ( IS_TRUE( s.flourish_pending ) && !self IsThrowingGrenade() )
	{
		s.flourish_pending = false;
		self begin_view( "flourish", GetWeapon( "tod_archer_retriever_flourish" ), 1.6 );
	}
	self view_step( dt );
	// Teleports and scripted set-downs must not drag the player back to an anchor.
	if ( isdefined( s.last_origin ) && Distance( self.origin, s.last_origin ) > 300 )
	{
		if ( IS_TRUE( self.tod_grappling ) ) self end_grapple( "relocated", true );
		s.grace = 0;
	}
	s.last_origin = self.origin;
	hook_was_charging = s.hook_cd > 0;
	s.hook_cd = countdown( s.hook_cd, dt );
	if ( hook_was_charging && s.hook_cd == 0 )
		tod_perk_scatter::play_sound_at_origin( self.origin, "tod_archer_hook_ready", 2 );
	// THE RETRIEVER CARD (2026-09-26): grant on the card, stored-throw refills,
	// clip sync - all owned by _tod_retriever.gsc tick().
	self tod_retriever::tick( s, dt );
	s.grace = countdown( s.grace, dt );
	if ( self IsOnGround() && !IS_TRUE( self.tod_grappling ) ) s.grace = 0;
	// HOLD TO GRAPPLE, LET GO TO LET GO (user 2026-09-26, after the first swing:
	// "the grapple should let go once you let go of the trigger button. So you
	// hold it and it grapples. When you let go, the grapple lets go. So you can
	// actually swing"). Before this the button TOGGLED: press to fire, press
	// again to release, and the user was jumping off the rope instead.
	if ( tactical_edge && !IS_TRUE( self.tod_grappling ) ) self try_grapple();
	else if ( !tactical && IS_TRUE( self.tod_grappling ) ) self end_grapple( "released", false );
	// Pathfinder: JUMP lets go of the rope too, momentum kept, plus a hop.
	else if ( jump_edge && IS_TRUE( self.tod_grappling ) ) self end_grapple( "jumped", false );
	if ( IS_TRUE( self.tod_grappling ) ) self grapple_step( dt );
	self wall_step( s, dt );   // THE INVISIBLE WALL: after the rope's own velocity write, on the rope and in the air after it
	self land_step( s );
	self tod_retriever::step( s, dt );
	self hud_send();
}

function countdown( remaining, dt )
{
	if ( remaining <= dt ) return 0;
	return remaining - dt;
}

function press_edge( down, previously_down )
{
	return down && !previously_down;
}

// The GRAPPLE card's one curve: ln( 1 + lvl ) / ln( 10 ), as a table so the
// server needs no log native. 0 = no card, 1 = Lv9 (was ln 9 / Lv8 until 2026-09-27). test_archer_equipment.js
// recomputes every entry from the formula.
function grapple_curve( rank )
{
	if ( !isdefined( rank ) || rank <= 0 ) return 0;
	if ( rank >= 9 ) return 1;
	c = array( 0, 0.301, 0.4771, 0.6021, 0.699, 0.7782, 0.8451, 0.9031, 0.9542, 1 );   // ln( 1 + lvl ) / ln( 10 ): 9 levels since 2026-09-27
	return c[ rank ];
}

function grapple_range( rank )
{
	return TOD_ARCHER_RANGE + TOD_ARCHER_RANGE_ADD * grapple_curve( rank );
}

function land_secs( rank )
{
	return TOD_ARCHER_LAND_SECS0 + TOD_ARCHER_LAND_SECS_ADD * grapple_curve( rank );
}

function surface_reason( fraction, dist, normal_length, surface, range )
{
	if ( fraction >= 1 || fraction <= 0 || normal_length < 0.5 || surface == "sky" ) return "no_surface";
	if ( dist < TOD_ARCHER_MIN_RANGE ) return "too_close";
	if ( dist > range ) return "out_of_range";
	return "";
}

// Where the rope would set you down, can a zombie stand? "" = yes (or a free fall).
function footing_reason( arrive )
{
	down = BulletTrace( arrive, arrive - ( 0, 0, TOD_ARCHER_FOOT_DROP ), false, self );
	if ( down[ "fraction" ] >= 1 ) return "";   // no floor near the hook: a drop to the ground below
	floor = down[ "position" ];
	nav = GetClosestPointOnNavMesh( floor, TOD_ARCHER_FOOT_R, 32 );
	if ( !isdefined( nav ) || Abs( nav[ 2 ] - floor[ 2 ] ) > TOD_ARCHER_FOOT_Z )
	{
		archer_log( "GRAPPLE_NO_FOOTING player=" + self GetEntityNumber() + " arrive=" + arrive + " floor=" + floor + " nav=" + ( isdefined( nav ) ? nav : "none" ) + " surface=" + down[ "surfacetype" ] );
		return "no_footing";
	}
	return "";
}

// THE PLAY AREA (2026-10-05, the invisible wall): is `pt` inside any zone volume? Enabled or not - a floor below an
// unbought door is still the map, as THE RECALL rules. Stock's check_point_in_playable_area is the same method (a
// bare script_model probe + IsTouching every player_volume); here the list is cached once and the volume that
// answered last is tried first, so a normal test is one IsTouching. Fails OPEN (true) when the map has no volumes.
function in_play( pt )
{
	if ( !isdefined( level.tod_archer_vols ) ) level.tod_archer_vols = GetEntArray( "player_volume", "script_noteworthy" );
	vols = level.tod_archer_vols;
	if ( !isdefined( vols ) || vols.size == 0 ) return true;
	if ( !isdefined( level.tod_archer_probe ) )
	{
		level.tod_archer_probe = Spawn( "script_model", pt );
		if ( !isdefined( level.tod_archer_probe ) ) return true;
	}
	probe = level.tod_archer_probe;
	probe.origin = pt;
	if ( isdefined( level.tod_archer_vol_last ) && probe IsTouching( level.tod_archer_vol_last ) ) return true;
	foreach ( v in vols )
	{
		if ( isdefined( v ) && probe IsTouching( v ) )
		{
			level.tod_archer_vol_last = v;
			return true;
		}
	}
	return false;
}

// A hook's arrival point (at chest height) counts as in play when it is in a zone volume, or straight ABOVE one at the
// archer's own chest height `chest_z` (a high wall inside an open-top hall: the column is the play area - never a
// roof). Out = beyond the play area sideways: past the rails, outside a hall, the crown's exterior.
function hook_in_play( arrive, chest_z )
{
	if ( in_play( arrive ) ) return true;
	if ( arrive[ 2 ] <= chest_z ) return false;
	return in_play( ( arrive[ 0 ], arrive[ 1 ], chest_z ) );
}

// THE INVISIBLE WALL, one tick (self = player; see TOD_ARCHER_WALL_*). On the rope and in the air after it (the
// grapple's grace), the HORIZONTAL part of the velocity that would carry the chest out of every zone volume over
// open air is removed, axis by axis, so you slide along the edge like any wall. Never vertical (no roof), never a
// teleport, never on a jump-pad flight (that crosses the void by design), and nothing once already out (THE RECALL
// and the out-of-bounds return own that).
function wall_step( s, dt )
{
	if ( !IS_TRUE( self.tod_grappling ) && ( s.grace <= 0 || self IsOnGround() ) ) return;
	if ( IS_TRUE( self.tod_jumppad_flying ) ) return;
	if ( !isdefined( s.walls ) ) s.walls = 0;
	real = self.origin + ( 0, 0, TOD_ARCHER_WALL_CHEST );
	col = wall_column( real, s );
	if ( !isdefined( col ) ) return;   // already out: THE RECALL / the out-of-bounds return own it; never trap anyone outside
	v = self GetVelocity();
	nv = wall_cut( col, real, v, dt * TOD_ARCHER_WALL_LOOK, self );
	if ( !isdefined( nv ) ) return;
	self SetVelocity( nv );
	s.walls++;
	if ( !isdefined( s.wall_log_t ) || GetTime() >= s.wall_log_t )
	{
		s.wall_log_t = GetTime() + TOD_ARCHER_WALL_LOG_MS;
		axes = "xy";
		if ( nv[ 1 ] == v[ 1 ] ) axes = "x";
		else if ( nv[ 0 ] == v[ 0 ] ) axes = "y";
		archer_log( "WALL player=" + self GetEntityNumber() + " axes=" + axes + " org=" + self.origin + " vel_in=" + v + " vel_out=" + nv +
		            " grappling=" + IS_TRUE( self.tod_grappling ) + " grace=" + s.grace + " above_zones=" + ( col[ 2 ] != real[ 2 ] ) + " walls=" + s.walls );
	}
}

// ---- THE INVISIBLE WALL's pure half (self-less; tools/test_archer_autobow.js runs both verbatim with a box world) ----

// The point the wall judges for a chest at `real`: the chest itself while it is in play (remembered as s.wall_z);
// above the play area, the column it came up at that height (never a roof); undefined when it is simply out.
function wall_column( real, s )
{
	if ( in_play( real ) )
	{
		s.wall_z = real[ 2 ];
		return real;
	}
	if ( !isdefined( s.wall_z ) || real[ 2 ] <= s.wall_z ) return undefined;
	col = ( real[ 0 ], real[ 1 ], s.wall_z );
	if ( !in_play( col ) ) return undefined;
	return col;
}

// The velocity after the wall for a chest at `real` judged at `col`, looking `look` seconds ahead; undefined when
// nothing leaves the play area. Only the horizontal axes that leave are removed; solid ahead (the core, a hall wall)
// is the world's to stop, so nothing is cut there (stopping you short would only rob the swing).
function wall_cut( col, real, v, look, ignore )
{
	h = ( v[ 0 ], v[ 1 ], 0 );
	if ( Length( h ) < 1 ) return undefined;
	ahead = h * look + VectorNormalize( h ) * TOD_ARCHER_WALL_PAD;
	if ( in_play( col + ahead ) ) return undefined;
	if ( !BulletTracePassed( real, real + ahead, false, ignore ) ) return undefined;
	px = TOD_ARCHER_WALL_PAD;
	if ( v[ 0 ] < 0 ) px = 0 - TOD_ARCHER_WALL_PAD;
	py = TOD_ARCHER_WALL_PAD;
	if ( v[ 1 ] < 0 ) py = 0 - TOD_ARCHER_WALL_PAD;
	ex = ( v[ 0 ] != 0 && !in_play( col + ( v[ 0 ] * look + px, 0, 0 ) ) );
	ey = ( v[ 1 ] != 0 && !in_play( col + ( 0, v[ 1 ] * look + py, 0 ) ) );
	if ( !ex && !ey )
	{
		// only the diagonal leaves: a corner
		ex = true;
		ey = true;
	}
	nv = v;
	if ( ex ) nv = ( 0, nv[ 1 ], nv[ 2 ] );
	if ( ey ) nv = ( nv[ 0 ], 0, nv[ 2 ] );
	return nv;
}

function try_grapple()
{
	if ( self IsThrowingGrenade() ) { self refused( "grapple", "using_retriever" ); return; }
	s = self.tod_archer_state;
	if ( isdefined( s.view_weapon ) ) { self refused( "grapple", "equipment_animation" ); return; }
	if ( s.hook_cd > 0 ) { self refused( "grapple", "recharging" ); return; }
	eye = self GetEye();
	forward = AnglesToForward( self GetPlayerAngles() );
	rank = tod_upgrades::get_level( self, "distraction" );
	range = grapple_range( rank );
	tr = BulletTrace( eye, eye + forward * range, false, self );
	if ( !isdefined( tr[ "normal" ] ) ) { self refused( "grapple", "no_surface" ); return; }
	dist = Distance( eye, tr[ "position" ] );
	why = surface_reason( tr[ "fraction" ], dist, Distance( tr[ "normal" ], ( 0, 0, 0 ) ), tr[ "surfacetype" ], range );
	if ( why != "" ) { self refused( "grapple", why ); return; }
	foot = self footing_reason( tr[ "position" ] + tr[ "normal" ] * 48 );
	if ( foot != "" ) { self refused( "grapple", foot ); return; }
	// THE INVISIBLE WALL's other half (2026-10-05): the rope may only pull you to a point inside the play area
	arrive = tr[ "position" ] + tr[ "normal" ] * 48;
	if ( !hook_in_play( arrive + ( 0, 0, TOD_ARCHER_WALL_CHEST - 44 ), self.origin[ 2 ] + TOD_ARCHER_WALL_CHEST ) )
	{
		archer_log( "GRAPPLE_OUT_OF_BOUNDS player=" + self GetEntityNumber() + " arrive=" + arrive + " surface=" + tr[ "surfacetype" ] );
		self refused( "grapple", "out_of_bounds" ); return;
	}
	// Pull the chest to a point OUTSIDE the surface, leaving the player hull
	// clear of walls/ceilings. Native movement retains normal world collision.
	s.anchor = tr[ "position" ] + tr[ "normal" ] * 48;
	s.surface = tr[ "position" ];
	s.pull_left = TOD_ARCHER_PULL_SECS;
	s.stall = 0;
	s.progress_origin = self.origin;
	s.hook_cd = ( IS_TRUE( level.tod_dev_unlimited_offhand ) ? 0 : TOD_ARCHER_GRAPPLE_CD * self aerialist_cd_mult() );   // dev test: no cooldown; AERIALIST -4% / Lv (2026-09-27)
	s.grace = TOD_ARCHER_GRACE_SECS;
	self.tod_grappling = true;
	self begin_view( "grapple", GetWeapon( "tod_archer_grapple_view" ), 0 );
	// KEEP the run: only lift off the floor so ground friction cannot eat it.
	// THE FLOOR EATS A SCRIPTED LIFT (2026-09-26, the user's first playtest:
	// "not really bringing me into the air ... stuck on the ground"): the
	// movement code rewrites a GROUNDED player's velocity every client frame,
	// so a positive z written here was discarded for as long as IsOnGround
	// held - the log showed 1500 u/s of "up" for four seconds with the origin
	// never leaving the bell floor. Stock's own jump pad pays this by moving
	// the player ONE unit up before its per-frame SetVelocity
	// (_zm_jump_pad.gsc:484): off the floor by a unit, the ground trace fails
	// and the velocity sticks.
	// floor_release() is that idiom; every lift in this file goes through it.
	v = self GetVelocity();
	grounded = self IsOnGround();
	if ( grounded && v[ 2 ] < TOD_ARCHER_LIFT + 40 )
	{
		self floor_release();
		self SetVelocity( ( v[ 0 ], v[ 1 ], TOD_ARCHER_LIFT + 40 ) );
	}
	s.launching = true;
	s.rope = Distance( s.anchor, self.origin + ( 0, 0, 44 ) );
	s.t = 0;
	s.log_t = 0;
	s.asked = undefined;
	s.obstruct_t = 0;
	s.nudges = 0;
	s.stall_events = 0;
	s.floor_releases = 0;
	s.min_dist = s.rope;
	s.pin_t = 0;
	s.pin_ref = s.rope;
	s.start_origin = self.origin;
	s.path_len = 0;
	s.peak_speed = Length( v );
	s.walls = 0;          // the invisible wall's catches on this swing (GRAPPLE_END walls=)
	s.wall_z = undefined; // re-measured from this swing
	self start_hook_art( tr[ "normal" ] );
	tod_perk_scatter::play_sound_at_origin( self.origin, "tod_archer_hook_fire", 2 );
	archer_log( "GRAPPLE_ATTACH player=" + self GetEntityNumber() + " from=" + eye + " anchor=" + s.anchor + " surface=" + tr[ "surfacetype" ] + " distance=" + int( dist ) + " range=" + int( range ) + " rank=" + rank + " vel_in=" + v + " speed_in=" + int( Length( v ) ) + " ground=" + grounded + " cooldown=" + s.hook_cd );
}

// Rope length after one tick: never longer than the player is now (a slack
// rope pulls taut where you are), then reeled in.
function rope_next( rope, dist, dt )
{
	if ( dist < rope ) rope = dist;
	rope -= TOD_ARCHER_REEL * dt;
	if ( rope < 0 ) rope = 0;
	return rope;
}

// Speed ALONG the rope (positive = toward the anchor) after one tick: the
// pull adds to it, the rope forbids drifting past its length, the reel speed
// caps it, and it eases off inside the last few feet.
function radial_next( radial, dist, rope, dt, first )
{
	r = radial + TOD_ARCHER_PULL_ACCEL * dt;
	if ( first && r < TOD_ARCHER_KICK ) r = TOD_ARCHER_KICK;
	need = ( dist - rope ) / dt;
	if ( r < need ) r = need;
	if ( r > TOD_ARCHER_SPEED ) r = TOD_ARCHER_SPEED;
	return r;   // no ease-off near the anchor (2026-09-26): you fly past it, Pathfinder-style
}

// The stick's push AROUND the anchor for one tick: (forward, right) in view
// space -> a horizontal wish -> only the part perpendicular to the rope.
// Pure so the gate can run it. Zero inside the dead zone.
function steer_vec( m, yaw, dir, dt )
{
	if ( !isdefined( m ) ) return ( 0, 0, 0 );
	f = AnglesToForward( ( 0, yaw, 0 ) );
	rt = AnglesToRight( ( 0, yaw, 0 ) );
	wish = f * m[ 0 ] + rt * m[ 1 ];
	mag = Length( wish );
	if ( mag < TOD_ARCHER_STEER_DEAD ) return ( 0, 0, 0 );
	if ( mag > 1 ) wish = wish * ( 1 / mag );
	wish = wish - dir * VectorDot( wish, dir );
	return wish * ( TOD_ARCHER_STEER_ACCEL * dt );
}

// Step a GROUNDED player one unit off the floor so the next SetVelocity is
// honoured: stock's jump-pad idiom (_zm_jump_pad.gsc:484). The movement code
// rewrites a grounded player's velocity every client frame and drops any
// scripted lift; one unit up, the ground trace misses and the write sticks.
// Harmless when already airborne (a unit of height), so callers need no guard.
function floor_release()
{
	self SetOrigin( self.origin + ( 0, 0, 1 ) );
}

// Swing speed cap: keeps the direction, trims the magnitude.
function tang_scale( tang_speed )
{
	if ( tang_speed <= TOD_ARCHER_TANG_MAX || tang_speed <= 0 ) return 1;
	return TOD_ARCHER_TANG_MAX / tang_speed;
}

function grapple_step( dt )
{
	s = self.tod_archer_state;
	if ( isdefined( s.hook_audio ) ) s.hook_audio.origin = self.origin;
	chest = self.origin + ( 0, 0, 44 );
	delta = s.anchor - chest;
	dist = Distance( s.anchor, chest );
	s.t += dt;
	moved = Distance( self.origin, s.progress_origin );
	got = moved / dt;   // what the engine actually delivered since last tick
	s.path_len += moved;
	s.progress_origin = self.origin;
	if ( dist < s.min_dist ) s.min_dist = dist;
	if ( dist < TOD_ARCHER_ARRIVE ) { self end_grapple( "arrived", false ); return; }
	if ( s.pull_left <= 0 ) { self end_grapple( "timeout", false ); return; }
	// Recheck visibility every tick: closed doors/new obstacles detach it.
	// Two ticks in a row, so grazing a corner mid-swing does not cut the rope.
	tr = BulletTrace( chest, s.anchor, false, self );
	if ( tr[ "fraction" ] < 0.98 && Distance( tr[ "position" ], s.anchor ) > 24 )
	{
		s.obstruct_t += dt;
		if ( s.obstruct_t >= TOD_ARCHER_OBSTRUCT_SECS )
		{
			archer_log( "GRAPPLE_OBSTRUCTED player=" + self GetEntityNumber() + " at=" + tr[ "position" ] + " surface=" + tr[ "surfacetype" ] + " ent=" + isdefined( tr[ "entity" ] ) + " dist=" + int( dist ) );
			self end_grapple( "obstructed", false ); return;
		}
	}
	else s.obstruct_t = 0;
	s.pull_left -= dt;
	if ( s.launching ) { s.launching = false; return; } // allow the floor pop one physics tick
	// Stuck: we asked for real speed and the engine moved us almost nowhere.
	if ( isdefined( s.asked ) && s.asked > 150 && moved < 3 ) s.stall += dt;
	else s.stall = 0;
	if ( s.stall > 0.5 ) { self end_grapple( "stalled", false ); return; }
	// Pinned: the rope is well past the body and the body is not closing in
	// (a wall or the invisible barrier between you and a hook you can see).
	if ( dist - s.rope > TOD_ARCHER_PIN_SLACK )
	{
		s.pin_t += dt;
		if ( s.pin_t >= TOD_ARCHER_PIN_SECS )
		{
			if ( s.pin_ref - dist < TOD_ARCHER_PIN_GAIN )
			{
				archer_log( "GRAPPLE_PINNED player=" + self GetEntityNumber() + " org=" + self.origin + " dist=" + int( dist ) + " rope=" + int( s.rope ) + " slack=" + int( dist - s.rope ) + " closed=" + int( s.pin_ref - dist ) + " t=" + s.t );
				self end_grapple( "pinned", false ); return;
			}
			s.pin_t = 0; s.pin_ref = dist;
		}
	}
	else { s.pin_t = 0; s.pin_ref = dist; }
	dir = VectorNormalize( delta );
	v = self GetVelocity();
	radial = VectorDot( v, dir );
	tang = v - dir * radial;
	first = ( s.t <= dt * 2 + 0.001 );
	s.rope = rope_next( s.rope, dist, dt );
	r = radial_next( radial, dist, s.rope, dt, first );
	m = self GetNormalizedMovement();
	tang = tang + steer_vec( m, self GetPlayerAngles()[ 1 ], dir, dt );
	tang = tang * tang_scale( Length( tang ) );
	nv = tang + dir * r;
	grounded = self IsOnGround();
	// Friction and floor lips: while grounded and not pulled DOWN, lift - and
	// step off the floor first or the engine discards the lift (see attach).
	if ( grounded && dir[ 2 ] > -0.3 )
	{
		if ( nv[ 2 ] < TOD_ARCHER_LIFT ) nv = ( nv[ 0 ], nv[ 1 ], TOD_ARCHER_LIFT );
		self floor_release();
		s.floor_releases++;
	}
	if ( s.stall > 0.1 )
	{
		// A lip or railing holds the hull: hop up and push off what we hit.
		probe = BulletTrace( chest, chest + dir * 48, false, self );
		push = ( 0, 0, 0 );
		if ( probe[ "fraction" ] < 1 && isdefined( probe[ "normal" ] ) ) push = probe[ "normal" ] * 160;
		nv = nv + push + ( 0, 0, TOD_ARCHER_UNSTICK );
		s.nudges++;
		s.stall_events++;
		archer_log( "GRAPPLE_STUCK player=" + self GetEntityNumber() + " org=" + self.origin + " asked=" + int( s.asked ) + " got=" + int( got ) + " ground=" + grounded + " blocker=" + ( probe[ "fraction" ] < 1 ) + " blocker_surface=" + probe[ "surfacetype" ] + " blocker_normal=" + probe[ "normal" ] + " dist=" + int( dist ) + " nudge=" + s.nudges );
		s.stall = 0.05;   // one nudge per ~0.1 s; three failed nudges end it
	}
	if ( nv[ 2 ] > TOD_ARCHER_UP_MAX ) nv = ( nv[ 0 ], nv[ 1 ], TOD_ARCHER_UP_MAX );   // no skyward launch (2026-09-26)
	self SetVelocity( nv );
	speed = Length( nv );
	if ( speed > s.peak_speed ) s.peak_speed = speed;
	if ( s.t >= s.log_t )
	{
		s.log_t = s.t + TOD_ARCHER_LOG_EVERY;
		archer_log( "GRAPPLE_TICK player=" + self GetEntityNumber() + " t=" + s.t + " org=" + self.origin + " vel=" + nv + " speed=" + int( speed ) + " asked_prev=" + ( isdefined( s.asked ) ? int( s.asked ) : -1 ) + " got=" + int( got ) + " dist=" + int( dist ) + " rope=" + int( s.rope ) + " radial=" + int( r ) + " swing=" + int( Length( tang ) ) + " input=" + ( isdefined( m ) ? m : "none" ) + " ground=" + grounded + " stall=" + s.stall );
	}
	s.asked = speed;
}

// Touch-down after a grapple -> a short burst of speed + damage reduction.
// AERIALIST (the Archer's kit-lane card, 2026-09-27; _tod_class_cards header). The grapple
// recharges 4% / Lv faster (12 s -> 7.7 s). A touch-down after a grapple: Lv3 refills one
// Hell's Retriever throw, Lv6 also sends a shockwave (one round zombie's health to ordinary
// zombies within 150; health-derived, so tod_ps_exempt), Lv9 refills every throw and the
// shockwave reaches 225. LOCKSTEP tod_upgrade.lua DETAIL[29].
function aerialist_cd_mult()
{
	return 1 - TOD_AERIAL_CD_STEP * tod_upgrades::get_level( self, "aerialist" );
}

function aerialist_land( s )
{
	l = tod_upgrades::get_level( self, "aerialist" );
	if ( l < 3 || !isdefined( s ) ) return;
	refilled = 0;
	if ( IS_TRUE( s.ret_on ) && isdefined( s.axe_charges ) )
	{
		cap = tod_retriever::charges_max( self tod_retriever::card_level() );
		want = ( ( l >= 9 ) ? cap : s.axe_charges + 1 );
		if ( want > cap ) want = cap;
		if ( want > s.axe_charges ) { refilled = want - s.axe_charges; s.axe_charges = want; }
	}
	hit = 0;
	if ( l >= 6 )
	{
		r = ( ( l >= 9 ) ? TOD_AERIAL_WAVE_R_LV9 : TOD_AERIAL_WAVE_R );
		dmg = level.zombie_health;
		if ( !isdefined( dmg ) || dmg < 1 ) dmg = 150;
		foreach ( z in GetAITeamArray( level.zombie_team ) )
		{
			if ( !isdefined( z ) || !IsAlive( z ) || DistanceSquared( z.origin, self.origin ) > r * r ) continue;
			if ( IS_TRUE( z.is_boss ) || isdefined( z.tod_boss_kind ) || isdefined( z.tod_necro_kind ) ) continue;
			z.tod_ps_exempt = true;
			z DoDamage( dmg, z.origin, self, self, "none", "MOD_IMPACT" );
			if ( isdefined( z ) ) z.tod_ps_exempt = undefined;
			hit++;
		}
	}
	archer_log( "AERIALIST_LAND player=" + self GetEntityNumber() + " lv=" + l + " throws_refilled=" + refilled + " wave_hits=" + hit );
}

// The two effects are read by _tod_upgrades (apply_move_speed / dr_mult)
// from player fields; this owns only the window and the speed re-apply edges.
function land_step( s )
{
	now = GetTime();
	if ( IS_TRUE( s.land_active ) && now >= self.tod_archer_land_until )
	{
		s.land_active = false;
		if ( isdefined( level.tod_apply_speed_fn ) ) self [[ level.tod_apply_speed_fn ]]();
		archer_log( "LAND_END player=" + self GetEntityNumber() + " origin=" + self.origin );
	}
	if ( !isdefined( s.land_pending_until ) || IS_TRUE( self.tod_grappling ) ) return;
	if ( now > s.land_pending_until ) { s.land_pending_until = undefined; archer_log( "LAND_MISSED player=" + self GetEntityNumber() + " (no touch-down in time)" ); return; }
	if ( !self IsOnGround() ) return;
	s.land_pending_until = undefined;
	self aerialist_land( s );   // AERIALIST (2026-09-27): refills / shockwave, before the GRAPPLE card's own gate
	rank = tod_upgrades::get_level( self, "distraction" );
	if ( rank <= 0 ) return;
	c = grapple_curve( rank );
	secs = land_secs( rank );
	self.tod_archer_land_speed = TOD_ARCHER_LAND_SPEED * c;
	self.tod_archer_land_dr = TOD_ARCHER_LAND_DR * c;
	self.tod_archer_land_until = now + int( secs * 1000 );
	s.land_active = true;
	if ( isdefined( level.tod_apply_speed_fn ) ) self [[ level.tod_apply_speed_fn ]]();
	// THE TELL (2026-09-26): the charge ring at the feet + a small rumble, so the
	// player knows the buff window opened (it used to be invisible and silent).
	tod_ability_fx::ring_at( self, "tod/archer/fx_tod_archer_charge", 0.6 );   // docs/203 s4: the ring is LOOPING; on a host that dies, never on the player (it never stopped)
	self PlayRumbleOnEntity( "reload_small" );
	archer_log( "LAND player=" + self GetEntityNumber() + " rank=" + rank + " speed=+" + self.tod_archer_land_speed + "% dr=" + self.tod_archer_land_dr + "% secs=" + secs + " origin=" + self.origin );
}

function land_clear( s )
{
	s.land_pending_until = undefined;
	was = IS_TRUE( s.land_active );
	s.land_active = false;
	self.tod_archer_land_until = undefined;
	if ( was && isdefined( level.tod_apply_speed_fn ) ) self [[ level.tod_apply_speed_fn ]]();
}

function end_grapple( reason, brake )
{
	s = self.tod_archer_state;
	if ( isdefined( s ) ) delete_hook( s );
	if ( !IS_TRUE( self.tod_grappling ) ) return;
	self.tod_grappling = false;
	self end_view( reason );
	// THE LANDING BUFF arms here and fires on the next touch-down (update()).
	if ( isdefined( s ) && reason != "dead" && reason != "downed" && reason != "respawn" && reason != "class_changed" && ( tod_upgrades::get_level( self, "distraction" ) > 0 || tod_upgrades::get_level( self, "aerialist" ) >= 3 ) )
		s.land_pending_until = GetTime() + int( TOD_ARCHER_LAND_WAIT * 1000 );
	tod_perk_scatter::play_sound_at_origin( self.origin, "tod_archer_hook_release", 2 );
	if ( IsAlive( self ) && !IS_TRUE( self.tod_jumppad_flying ) )
	{
		v = self GetVelocity();
		if ( brake ) v = ( 0, 0, 0 );
		else if ( reason == "arrived" && isdefined( s ) && isdefined( s.anchor ) )
		{
			// Do not slam into the surface: drop the into-anchor part, keep the
			// swing, and pop up so a ledge grab carries onto the ledge.
			dir = VectorNormalize( s.anchor - ( self.origin + ( 0, 0, 44 ) ) );
			into = VectorDot( v, dir );
			if ( into > 0 ) v = v - dir * into;
			if ( v[ 2 ] < TOD_ARCHER_EXIT_HOP ) v = ( v[ 0 ], v[ 1 ], TOD_ARCHER_EXIT_HOP );
		}
		else if ( reason == "jumped" && v[ 2 ] < TOD_ARCHER_EXIT_HOP ) v = ( v[ 0 ], v[ 1 ], TOD_ARCHER_EXIT_HOP );   // let go + the jump
		if ( v[ 2 ] > TOD_ARCHER_EXIT_UP_MAX ) v = ( v[ 0 ], v[ 1 ], TOD_ARCHER_EXIT_UP_MAX );   // the rope never throws you skyward (2026-09-26)
		self SetVelocity( v );
		if ( isdefined( s ) && isdefined( s.t ) )
			archer_log( "GRAPPLE_END player=" + self GetEntityNumber() + " reason=" + reason + " origin=" + self.origin + " t=" + s.t + " from=" + s.start_origin + " straight=" + int( Distance( s.start_origin, self.origin ) ) + " path=" + int( s.path_len ) + " min_dist=" + int( s.min_dist ) + " peak=" + int( s.peak_speed ) + " vel_out=" + v + " speed_out=" + int( Length( v ) ) + " stuck_events=" + s.stall_events + " floor_releases=" + s.floor_releases + " walls=" + ( isdefined( s.walls ) ? s.walls : 0 ) );
		return;
	}
	archer_log( "GRAPPLE_END player=" + self GetEntityNumber() + " reason=" + reason + " origin=" + self.origin );
}

// Presentation owns no movement state. A missing model/host never spends an
// extra charge or leaves a beam or looping sound behind.
function start_hook_art( normal )
{
	s = self.tod_archer_state;
	delete_hook( s );
	owner_id = self GetEntityNumber();
	if ( owner_id < 0 || owner_id > 14 ) { archer_log( "ART_FAIL reason=owner_index owner=" + owner_id ); return; }
	s.hook = Spawn( "script_model", s.surface + normal * 15.5 );
	if ( !isdefined( s.hook ) ) { archer_log( "ART_FAIL reason=hook_spawn" ); return; }
	s.hook SetModel( "tod_archer_hook" );
	s.hook NotSolid();
	s.hook.angles = VectorToAngles( normal * -1 );
	value = owner_id + 1;
	if ( IS_TRUE( level.tod_dev ) ) value += 16;
	s.hook clientfield::set( "todArcherHook", value );
	tod_perk_scatter::play_sound_at_origin( s.surface, "tod_archer_hook_attach", 2 );
	// The bite: a small spark burst off the surface, along its normal (2026-09-26).
	tod_ability_fx::burst_at( "electric/fx_elec_sparks_burst_xsm_omni_blue_os", s.surface + normal * 2, VectorToAngles( normal ), 1.0 );   // docs/206: on a carrier (a bare server PlayFX draws nothing here)
	s.hook_audio = Spawn( "script_origin", self.origin );
	if ( isdefined( s.hook_audio ) )
	{
		s.hook_audio LinkTo( self );   // the pull loop rides WITH the archer (it used to stay where the swing began)
		s.hook_audio PlayLoopSound( "tod_archer_hook_pull" );
	}
	archer_log( "ART_ATTACH owner=" + owner_id + " hook=" + s.hook GetEntityNumber() + " audio=" + isdefined( s.hook_audio ) );
}

function delete_hook( s )
{
	if ( isdefined( s.hook ) )
	{
		s.hook clientfield::set( "todArcherHook", 0 );
		s.hook Delete(); // CSC entityshutdown also kills a beam if zero was coalesced.
		s.hook = undefined;
	}
	if ( isdefined( s.hook_audio ) )
	{
		s.hook_audio StopLoopSound( 0 );
		s.hook_audio StopSounds();
		s.hook_audio Delete();
		s.hook_audio = undefined;
	}
}

function end_axe( reason )
{
    self tod_retriever::finish( self.tod_archer_state, reason );
}

function stop_axe_audio( s )
{
	if ( !isdefined( s.axe_audio ) ) return;
	s.axe_audio StopLoopSound( 0 );
	s.axe_audio StopSounds();
	s.axe_audio Delete();
	s.axe_audio = undefined;
}

function delete_axe( s )
{
    tod_retriever::destroy( s );
}

function cleanup( reason )
{
	s = self.tod_archer_state;
	self end_grapple( reason, true );
	self end_view( reason );
	self end_axe( reason );
	self land_clear( s );
	s.grace = 0;
	s.armed = false;
	if ( self HasWeapon( level.tod_retriever_weapon ) ) self TakeWeapon( level.tod_retriever_weapon );
	// Restore the bookkeeping on respawn too, before the next Archer state
	// snapshots it. Otherwise it can remember Retriever as its old grenade.
	if ( isdefined( s.old_lethal ) ) self zm_utility::set_player_lethal_grenade( s.old_lethal );
	if ( isdefined( s.old_tactical ) ) self zm_utility::set_player_tactical_grenade( s.old_tactical );
	if ( reason == "class_changed" && isdefined( s.old_lethal ) && s.old_lethal != level.weaponNone && s.old_lethal != level.tod_retriever_weapon )
	{
		self GiveWeapon( s.old_lethal ); self SwitchToOffhand( s.old_lethal );
		self zm_utility::set_player_lethal_grenade( s.old_lethal );
	}
	if ( reason == "class_changed" && isdefined( s.old_tactical ) && s.old_tactical != level.weaponNone )
	{
		self GiveWeapon( s.old_tactical ); self SwitchToOffhand( s.old_tactical );
		self zm_utility::set_player_tactical_grenade( s.old_tactical );
	}
	self EnableOffhandWeapons();
	self LuiNotifyEvent( &"tod_archer_abil", 3, 0, 0, 0 );
	self LuiNotifyEvent( &"tod_archer_aim", 1, 0 );
	s.aim_key = 0;
	archer_log( "CLEANUP player=" + self GetEntityNumber() + " reason=" + reason );
}

// Native inventory items own first-person hands and animations. They restore
// the exact previous weapon, with no camera-linked world models or input loop.
function begin_view( kind, weapon, duration )
{
	s = self.tod_archer_state;
	if ( isdefined( s.view_weapon ) ) self end_view( "replaced" );
	s.view_previous = self GetCurrentWeapon();
	s.view_weapon = weapon;
	s.view_kind = kind;
	s.view_left = duration;
	s.view_age = 0;
	s.view_logged = false;
	self GiveWeapon( weapon );
	self DisableWeaponCycling();
	self DisableOffhandWeapons();
	self SwitchToWeapon( weapon );
	archer_log( "VIEW_START owner=" + self GetEntityNumber() + " kind=" + kind + " previous=" + s.view_previous.name );
}

function view_step( dt )
{
	s = self.tod_archer_state;
	if ( !isdefined( s.view_weapon ) ) return;
	s.view_age += dt;
	if ( self GetCurrentWeapon() == s.view_weapon && !s.view_logged )
	{
		s.view_logged = true;
		archer_log( "VIEW_SELECTED owner=" + self GetEntityNumber() + " kind=" + s.view_kind + " age=" + s.view_age );
	}
	if ( !s.view_logged && s.view_age > 2 )
	{
		archer_log( "VIEW_FAIL owner=" + self GetEntityNumber() + " kind=" + s.view_kind + " reason=switch_timeout" );
		self end_view( "switch_timeout" );
		return;
	}
	if ( s.view_kind == "flourish" && s.view_logged )
	{
		s.view_left -= dt;
		if ( s.view_left <= 0 ) self end_view( "flourish_complete" );
	}
}

function end_view( reason )
{
	s = self.tod_archer_state;
	if ( !isdefined( s ) || !isdefined( s.view_weapon ) ) return;
	weapon = s.view_weapon;
	previous = s.view_previous;
	archer_log( "VIEW_END owner=" + self GetEntityNumber() + " kind=" + s.view_kind + " reason=" + reason );
	s.view_weapon = undefined;
	s.view_restore_controls = true;
	if ( IsAlive( self ) && !self laststand::player_is_in_laststand() && isdefined( previous ) && self HasWeapon( previous ) && self GetCurrentWeapon() == weapon )
	{
		self SwitchToWeapon( previous );
		self thread remove_view_weapon( weapon );
	}
	else if ( self HasWeapon( weapon ) ) self TakeWeapon( weapon );
	if ( self blocked_reason() == "" )
	{
		self EnableWeaponCycling();
		if ( is_archer( self ) ) self EnableOffhandWeapons();
		s.view_restore_controls = false;
	}
}

function remove_view_weapon( weapon )
{
	self endon( "disconnect" );
	// Allow the original lower/weapon-change transition before inventory removal.
	wait 0.35;
	if ( self HasWeapon( weapon ) && ( !isdefined( self.tod_archer_state.view_weapon ) || self.tod_archer_state.view_weapon != weapon ) ) self TakeWeapon( weapon );
}

function restore_view_controls( s )
{
	// Run before the class filter: a class change during a menu can finish
	// presentation while the menu still owns input. Release our lock on exit.
	if ( !IS_TRUE( s.view_restore_controls ) || isdefined( s.view_weapon ) ) return;
	if ( self blocked_reason() != "" ) return;
	self EnableWeaponCycling();
	self EnableOffhandWeapons();
	s.view_restore_controls = false;
}

function hud_seconds( remaining )
{
	if ( remaining <= 0 ) return 0;
	return int( remaining + 0.999 );
}

function hud_send()
{
	s = self.tod_archer_state;
	self aim_hint();
	// Lethal slot (2026-09-26, the Retriever card): -2 = no card yet; otherwise
	// stored throws x 1000 + seconds to the next refill. Axes in the air no
	// longer block a throw (many at once since the build-8 test), so the tile
	// shows the stored count + refill clock at all times (the 999 "busy" code is gone).
	// LOCKSTEP with setArcher's CLASS_KITS[0] "charges" slot in AetheriumLoadout.lua.
	axe = -2;
	if ( IS_TRUE( s.ret_on ) ) axe = s.axe_charges * 1000 + hud_seconds( s.axe_cd );
	hook = hud_seconds( s.hook_cd );
	if ( IS_TRUE( self.tod_grappling ) ) hook = -1;
	key = axe + ":" + hook;
	if ( isdefined( s.hud_key ) && s.hud_key == key && GetTime() < s.hud_refresh ) return;
	s.hud_key = key;
	s.hud_refresh = GetTime() + 2000;
	self LuiNotifyEvent( &"tod_archer_abil", 3, 1, axe, hook );
}

function aim_hint()
{
	s = self.tod_archer_state;
	if ( GetTime() < s.aim_refresh ) return;
	s.aim_refresh = GetTime() + 150;
	valid = 0;
	if ( s.hook_cd == 0 && !IS_TRUE( self.tod_grappling ) && self blocked_reason() == "" )
	{
		eye = self GetEye();
		range = grapple_range( tod_upgrades::get_level( self, "distraction" ) );
		tr = BulletTrace( eye, eye + AnglesToForward( self GetPlayerAngles() ) * range, false, self );
		if ( isdefined( tr[ "normal" ] ) && surface_reason( tr[ "fraction" ], Distance( eye, tr[ "position" ] ), Distance( tr[ "normal" ], ( 0, 0, 0 ) ), tr[ "surfacetype" ], range ) == "" &&
		     hook_in_play( tr[ "position" ] + tr[ "normal" ] * 48 + ( 0, 0, TOD_ARCHER_WALL_CHEST - 44 ), self.origin[ 2 ] + TOD_ARCHER_WALL_CHEST ) ) valid = 1;   // the invisible wall: no tick for a hook outside the play area
	}
	if ( isdefined( s.aim_key ) && s.aim_key == valid && GetTime() < s.aim_resend ) return;
	s.aim_key = valid;
	s.aim_resend = GetTime() + 2000;
	self LuiNotifyEvent( &"tod_archer_aim", 1, valid );
}

// PK18 (2026-10-05): a refused grapple is HEARD (tod_ability_fx::kit_deny's muted "nope", throttled per player) and,
// when the reason is one the tile cannot show, SAID in plain words - never the internal reason code (the raw
// "grapple: no_footing" chat lines reached players until now). Recharging / mid-throw / mid-equipment: the tile and the
// hands already say it, so those get the sound alone. The words are throttled like the sound.
function refused( ability, reason )
{
	words = refuse_words( reason );
	now = GetTime();
	if ( words != "" && ( !isdefined( self.tod_archer_refuse_ms ) || now - self.tod_archer_refuse_ms >= 1500 ) )
	{
		self.tod_archer_refuse_ms = now;
		self IPrintLn( words );
	}
	tod_ability_fx::kit_deny( self, ability, reason );
	archer_log( "REFUSE player=" + self GetEntityNumber() + " ability=" + ability + " reason=" + reason );
}

function refuse_words( reason )
{
	if ( reason == "no_surface" ) return "Nothing to grapple there";
	if ( reason == "too_close" ) return "Too close to grapple";
	if ( reason == "out_of_range" ) return "Out of grapple range";
	if ( reason == "no_footing" ) return "No footing there";
	if ( reason == "out_of_bounds" ) return "Can't grapple out of the map";
	return "";
}

// OUT OF BOUNDS (2026-09-26, user: "am I going out of bounds? that's a big
// thing"): the stock monitor asks this every time a player is outside the
// playable area. An Archer mid-grapple (grace) is spared; once the grace runs
// out, stock kills as usual. BOTH outcomes are logged with the origin and
// the last grapple's anchor, throttled to one line per second per player,
// so a playtest shows exactly which edge the rope carried you over.
function playable_area_cb()
{
	if ( is_archer( self ) && isdefined( self.tod_archer_state ) )
	{
		s = self.tod_archer_state;
		spared = ( s.grace > 0 && !self zm::in_kill_brush() );
		if ( !isdefined( s.oob_log_t ) || GetTime() >= s.oob_log_t )
		{
			s.oob_log_t = GetTime() + 1000;
			archer_log( "OOB player=" + self GetEntityNumber() + " org=" + self.origin + " spared=" + spared + " grace=" + s.grace + " grappling=" + IS_TRUE( self.tod_grappling ) + " ground=" + self IsOnGround() + " kill_brush=" + self zm::in_kill_brush() + " last_anchor=" + ( isdefined( s.anchor ) ? s.anchor : "none" ) );
		}
		if ( spared ) return false;
		// THE RETURN (2026-09-26, the user's first playtest): the rope carried
		// the Archer over the hall's wall onto the crown's bell floor - outside
		// every zone, no navmesh, nothing to fight - and they stood there for
		// 45 s (stock's kill was blocked by god mode; in a normal match it is a
		// death). Neither is a game. Once the grace is spent and the rope is
		// down, put them back on the last navmesh point stock tracked for them
		// (player_shared::track_players_last_valid_position - always in bounds)
		// and keep the kill for the kill brushes only.
		if ( !IS_TRUE( self.tod_grappling ) && !self zm::in_kill_brush() && isdefined( self.last_valid_position ) && IsAlive( self ) )
		{
			from = self.origin;
			self SetOrigin( self.last_valid_position + ( 0, 0, 8 ) );
			self SetVelocity( ( 0, 0, 0 ) );
			s.grace = TOD_ARCHER_GRACE_SECS;   // a fresh grace, so a second stranding logs and returns again
			archer_log( "OOB_RETURN player=" + self GetEntityNumber() + " from=" + from + " to=" + self.origin + " last_anchor=" + ( isdefined( s.anchor ) ? s.anchor : "none" ) );
			return false;
		}
	}
	if ( isdefined( level.tod_archer_prev_oopa_cb ) ) return self [[ level.tod_archer_prev_oopa_cb ]]();
	return true;
}

function fall_damage_guard( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, psOffsetTime )
{
	if ( ignores_fall( is_archer( self ), sMeansOfDeath ) )
	{
		archer_log( "FALL_BLOCK player=" + self GetEntityNumber() + " damage=" + iDamage + " origin=" + self.origin );
		return 0;
	}
	return -1;
}

function ignores_fall( archer, cause )
{
	return archer && cause == "MOD_FALLING";
}

function archer_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_ARCHER] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
