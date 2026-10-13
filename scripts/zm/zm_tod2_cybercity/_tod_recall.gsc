// =============================================================================
// _tod_recall.gsc — THE RECALL: a player who falls off the map comes back.
// (docs/200, THE PURSUIT — the player half. The zombie half is _tod_stray.gsc.)
//
// REV 2 (user 2026-10-02, evening): "Teleporting to safety should only be when you
// fall of the map completely. Im fine with players trying to hack and jump down
// all the way. But if they fall off they should spawn where they came from and at
// 1 HP." So the recall no longer judges WHERE a player stands, only whether he has
// left the map. Dropping any number of floors onto the tower, landing below an
// unbought door, standing on a ledge no zombie can reach: all allowed now. Rev 1
// returned all three (FALL two floors below the last safe spot, OUT OF BOUNDS =
// outside every ENABLED zone, PERCH = out of a zombie's swing), and the user hit
// it jumping down the tower.
//
// Why a return and not stock's answer (a laugh and an instant kill), unchanged
// from rev 1: the void is a SOFT-LOCK in god mode (the 2026-09-30 17:56 run has a
// Breacher who launched off the terrace and fell for 25 s, z 19,392 -> -131,161,
// because stock's kill could not land through god mode), and a death for a missed
// Breacher launch punishes the class. The 1 HP is the price of the fall.
//
// THREE WAYS OFF THE MAP, one sampled watcher per player (TOD_RECALL_TICK):
//   FALL — airborne, falling, TOD_RECALL_FALL_Z below the last safe spot, AND
//          nothing under him to land on (traces straight down find no surface
//          above the void line): returned at once. With a floor under him the
//          fall is never judged, however far it goes.
//   VOID — below TOD_RECALL_VOID_Z: under the Undercity floor, the lowest floor
//          on the map, where only the sealed sky floor exists. Returned at once,
//          falling or standing (a player on the sky floor is stuck for good).
//   OOB  — standing (or at rest) in NO zone at all, enabled or not: a roof, an
//          ornament, the crown's underside. Returned after TOD_RECALL_OOB_MS. The
//          clock holds in the air (a hop cannot dodge it) and only the map clears
//          it. A floor below an unbought door IS the map: stock's out-of-playable-
//          area kill is spared there (oopa_cb); kill brushes keep stock's verdict.
// WHERE TO: where he came from, the last SAFE spot (grounded, within
// TOD_RECALL_SAFE_GAP of the navmesh, inside any zone, upright, not mid special
// move), kept by this watcher; stock's player.last_valid_position when none exists
// yet. He arrives at TOD_RECALL_ARRIVAL_HP (a downed player keeps his last stand).
// NEVER JUDGED: the jump-pad flight, an Archer's rope (and its grace), a frozen
// player (card deal, shop spin, class terminal, station), the world pause, the
// half second after any script teleport (a ride, the arena, a recall). The safe
// spot is re-earned at the arrival before anything can fire again.
// =============================================================================

#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;

#using scripts\zm\_zm;
#using scripts\zm\_zm_zonemgr;

#using scripts\zm\zm_tod2_cybercity\_tod_reach;
#using scripts\zm\zm_tod2_cybercity\_tod_teleport;   // discharge / fx_burst — the teleporter's own arrival look

#insert scripts\shared\shared.gsh;

#namespace tod_recall;

// The A/B switch: 0 = stock's out-of-playable-area kill and no recall at all.
#define TOD_RECALL_ENABLED      1

#define TOD_RECALL_TICK         0.2     // seconds between samples per player
#define TOD_RECALL_FALL_Z       768     // two floors below the last safe spot, still falling, nothing under him
#define TOD_RECALL_VOID_Z       -448    // LOCKSTEP gen_tower_map.js: under UC_Z (-384, the Undercity floor), over SKY_FLOOR (-512)
#define TOD_RECALL_OOB_MS       1000    // standing in no zone at all this long
#define TOD_RECALL_REST_SPEED   4       // slower than this counts as standing (wedged on an off-map slope)
#define TOD_RECALL_FOOT_R       16      // the floor test also traces this far out each side (the player hull is 15)
#define TOD_RECALL_ARRIVAL_HP   1       // the price of the fall (user 2026-10-02: "at 1 HP")
#define TOD_RECALL_SAFE_GAP     40      // a safe spot is this close to the navmesh (or closer)
#define TOD_RECALL_MESH_SEARCH  136     // how far mesh_gap() looks for the navmesh
#define TOD_RECALL_JUMP_DIST    600     // moved this far in one tick = a script teleport, not a fall
#define TOD_RECALL_JUMP_MS      500     // ...and nothing is judged for this long after one
#define TOD_RECALL_COOL_MS      1500    // no second return inside this window
#define TOD_RECALL_GIVEUP_MS    8000    // off the map this long with no return possible -> stock decides again

function init()
{
	if ( !TOD_RECALL_ENABLED )
		return;
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	level.tod_recall_vols = GetEntArray( "player_volume", "script_noteworthy" );
	if ( !isdefined( level.tod_recall_vols ) )
		level.tod_recall_vols = [];
	// INSTALLED AFTER THE BLACKSCREEN on purpose: _tod_jumppad and _tod_archer
	// install theirs during load, so this one wraps both and is asked FIRST.
	level.tod_recall_prev_oopa_cb = level.player_out_of_playable_area_monitor_callback;
	level.player_out_of_playable_area_monitor_callback = &oopa_cb;
	callback::on_spawned( &on_spawned );
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
		players[ i ] thread watch();
	recall_log( "INIT rev=2 tick=" + TOD_RECALL_TICK + " fall_z=" + TOD_RECALL_FALL_Z + " void_z=" + TOD_RECALL_VOID_Z
		+ " oob_ms=" + TOD_RECALL_OOB_MS + " arrival_hp=" + TOD_RECALL_ARRIVAL_HP
		+ " volumes=" + level.tod_recall_vols.size + " wrapped_prev_cb=" + isdefined( level.tod_recall_prev_oopa_cb ) );
}

function on_spawned()   // self = player
{
	self thread watch();
}

function rstate()   // self = player
{
	if ( !isdefined( self.tod_recall ) )
	{
		s = SpawnStruct();
		s.count = 0;
		self.tod_recall = s;
	}
	return self.tod_recall;
}

// Forget every running clock (and the fall reference: after an exemption or a
// teleport the old height means nothing).
function reset( s )
{
	s.oob_since = undefined;
	s.fall_ref = undefined;
	s.fail_since = undefined;
}

function watch()   // self = player
{
	self notify( "tod_recall_watch" );
	self endon( "tod_recall_watch" );
	self endon( "disconnect" );
	level endon( "end_game" );

	s = self rstate();
	reset( s );
	s.gave_up = undefined;
	s.last_org = self.origin;
	s.quiet_until = GetTime() + TOD_RECALL_JUMP_MS;

	for ( ;; )
	{
		wait TOD_RECALL_TICK;
		now = GetTime();

		if ( !isalive( self ) || self.sessionstate != "playing" )
		{
			reset( s );
			s.last_org = self.origin;
			continue;
		}

		// ANY SCRIPT TELEPORT (a ride, the arena, the jump pad's set-down, a
		// recall) moves the player farther in one tick than his own velocity can
		// explain. Re-earn the safe spot at the arrival before anything is judged.
		v = self GetVelocity();
		jumped = is_teleport( Distance( self.origin, s.last_org ), Length( v ) );
		s.last_org = self.origin;
		if ( jumped )
		{
			reset( s );
			s.quiet_until = now + TOD_RECALL_JUMP_MS;
			continue;
		}

		why = self exempt();
		if ( why != "" )
		{
			reset( s );
			continue;
		}
		if ( now < s.quiet_until )
			continue;

		grounded = self IsOnGround();
		settled = ( grounded || Length( v ) < TOD_RECALL_REST_SPEED );
		downed = self laststand::player_is_in_laststand();
		zone = self map_zone();
		inmap = ( zone != "" );
		self note_below_doors( s, zone );

		// THE SAFE SPOT, where he came from: on the map, where the horde can reach him.
		if ( grounded && inmap && !downed )
		{
			gap = self mesh_gap();
			if ( is_safe( grounded, inmap, gap, downed ) )
			{
				s.safe = self.origin;
				s.fall_ref = self.origin[ 2 ];
			}
		}

		// THE FLOOR UNDER HIM, traced only when the fall test would otherwise fire,
		// so a normal match never traces at all.
		floor_below = true;
		if ( !settled && v[ 2 ] < 0 && isdefined( s.fall_ref ) && self.origin[ 2 ] < s.fall_ref - TOD_RECALL_FALL_Z )
			floor_below = self has_floor_below();

		act = decide( s, now, self.origin[ 2 ], v[ 2 ], settled, inmap, floor_below );
		if ( act == "" )
		{
			s.fail_since = undefined;
			continue;
		}
		if ( self recall( act, now ) )
			continue;
		// No destination at all (no safe spot yet AND no stock last_valid_position):
		// logged once, and after TOD_RECALL_GIVEUP_MS stock's verdict decides again.
		if ( !isdefined( s.fail_since ) )
		{
			s.fail_since = now;
			recall_log( "FAIL player=" + self GetEntityNumber() + " why=" + act + " reason=no_destination at=" + fmt( self.origin ) );
		}
		else if ( !IS_TRUE( s.gave_up ) && ( now - s.fail_since ) >= TOD_RECALL_GIVEUP_MS )
		{
			s.gave_up = true;   // stock's callback chain decides again (oopa_cb)
			recall_log( "GIVEUP player=" + self GetEntityNumber() + " why=" + act + " at=" + fmt( self.origin ) + " ms=" + ( now - s.fail_since ) );
		}
	}
}

// PURE: was this tick's move a script teleport? Big, AND more than the player's
// own speed covers in a tick (with margin). A long fall passes 3,000 u/s — a pure
// distance test would read it as a teleport every tick and never judge it.
function is_teleport( dist, speed )
{
	if ( dist <= TOD_RECALL_JUMP_DIST )
		return false;
	return ( dist > speed * TOD_RECALL_TICK * 1.5 + 100 );
}

// PURE: a safe spot is grounded, on the map, on (or right beside) the navmesh, upright.
function is_safe( grounded, inmap, gap, downed )
{
	return ( grounded && inmap && gap <= TOD_RECALL_SAFE_GAP && !downed );
}

// PURE — the whole verdict for one sample (tools/test_pursuit.js runs THIS
// function, not a copy). -> "" (nothing), "void", "fall" or "oob".
// Mutates only s's clocks; the caller acts.
function decide( s, now, z, vz, settled, inmap, floor_below )
{
	// (1) THE VOID: under the Undercity floor, the lowest floor on the map.
	if ( z < TOD_RECALL_VOID_Z )
		return "void";

	// (2) FELL OFF: falling, well below where he last stood, nothing under him.
	if ( !settled && vz < 0 && isdefined( s.fall_ref ) && z < s.fall_ref - TOD_RECALL_FALL_Z && !floor_below )
		return "fall";

	// (3) OFF THE MAP: standing in no zone at all.
	if ( !inmap )
	{
		if ( !settled )
			return "";   // in the air: the clock holds, neither started nor cleared
		if ( !isdefined( s.oob_since ) )
		{
			s.oob_since = now;
			return "";
		}
		if ( ( now - s.oob_since ) < TOD_RECALL_OOB_MS )
			return "";
		if ( isdefined( s.cool_until ) && now < s.cool_until )
			return "";
		return "oob";
	}
	s.oob_since = undefined;
	s.gave_up = undefined;
	return "";
}

// PURE: the health he arrives with (tools/test_pursuit.js runs THIS). Falling off
// the map costs all but the last point; a downed player keeps his last stand.
function arrival_health( health, downed )
{
	if ( downed )
		return health;
	return TOD_RECALL_ARRIVAL_HP;
}

// -> "" when THE RECALL may judge this player, else why not (for the log).
function exempt()   // self = player
{
	if ( IS_TRUE( level.intermission ) )
		return "intermission";
	if ( IS_TRUE( level.tod_upgrade_pause ) )
		return "world_pause";
	if ( IS_TRUE( self.tod_jumppad_flying ) )
		return "jump_pad";
	if ( IS_TRUE( self.tod_grappling ) )
		return "grapple";
	if ( isdefined( self.tod_archer_state ) && isdefined( self.tod_archer_state.grace ) && self.tod_archer_state.grace > 0 )
		return "grapple_grace";
	if ( IS_TRUE( self.tod_menu_frozen ) || IS_TRUE( self.tod_spin_locked ) || IS_TRUE( self.tod_solo_upg_active ) || IS_TRUE( self.tod_cls_term_locked ) )
		return "frozen";
	return "";
}

// -> the zone he is standing in, or "" when he is off the map. ANY zone counts,
// enabled or not: a floor below an unbought door is still the map (rev 2). The
// volume list is static, cached once at init, and the last volume he touched is
// tried first, so a normal tick is one test. A life brush counts, as for stock.
function map_zone()   // self = player
{
	if ( self zm::in_life_brush() )
		return "life_brush";
	s = self rstate();
	if ( isdefined( s.vol ) && isdefined( s.vol.targetname ) && self IsTouching( s.vol ) )
		return s.vol.targetname;
	vols = level.tod_recall_vols;
	if ( !isdefined( vols ) )
		return "";
	for ( i = 0; i < vols.size; i++ )
	{
		v = vols[ i ];
		if ( !isdefined( v ) || !isdefined( v.targetname ) )
			continue;
		if ( self IsTouching( v ) )
		{
			s.vol = v;
			return v.targetname;
		}
	}
	return "";
}

// THE NEW ALLOWANCE, LOGGED: a player in a zone that is not enabled yet dropped
// past an unbought door. Rev 1 returned him; now he stays. One line per zone he
// enters, so a playtest shows where people skip the doors.
function note_below_doors( s, zone )   // self = player
{
	if ( zone == "" || zone == "life_brush" || zm_zonemgr::zone_is_enabled( zone ) )
	{
		s.below_zone = undefined;
		return;
	}
	if ( isdefined( s.below_zone ) && s.below_zone == zone )
		return;
	s.below_zone = zone;
	recall_log( "BELOW_DOORS player=" + self GetEntityNumber() + " zone=" + zone + " at=" + fmt( self.origin ) + " " + tod_reach::describe( self.origin ) );
}

// Is there anything to land on under him, above the void line? Five traces
// straight down (his centre and a hull's width out each side; world geometry, no
// characters). The sealed sky floor sits BELOW the line, so the void finds nothing.
function has_floor_below()   // self = player
{
	offs = array( ( 0, 0, 0 ), ( TOD_RECALL_FOOT_R, 0, 0 ), ( 0 - TOD_RECALL_FOOT_R, 0, 0 ),
		( 0, TOD_RECALL_FOOT_R, 0 ), ( 0, 0 - TOD_RECALL_FOOT_R, 0 ) );
	for ( i = 0; i < offs.size; i++ )
	{
		top = self.origin + offs[ i ] + ( 0, 0, 8 );
		tr = BulletTrace( top, ( top[ 0 ], top[ 1 ], TOD_RECALL_VOID_Z ), false, self );
		if ( tr[ "fraction" ] < 1 )
			return true;
	}
	return false;
}

// Distance from the player to the nearest walkable navmesh (0 = standing on it).
function mesh_gap()   // self = player
{
	if ( IsPointOnNavMesh( self.origin, self ) )
		return 0;
	m = GetClosestPointOnNavMesh( self.origin, TOD_RECALL_MESH_SEARCH, 0 );
	if ( !isdefined( m ) )
		return 9999;
	return Distance( self.origin, m );
}

// THE RETURN: to where he came from, at TOD_RECALL_ARRIVAL_HP. -> true if moved.
function recall( why, now )   // self = player
{
	s = self rstate();
	dest = s.safe;
	src = "safe";
	if ( !isdefined( dest ) )
	{
		dest = self.last_valid_position;
		src = "last_valid";
	}
	if ( !isdefined( dest ) )
		return false;
	nav = GetClosestPointOnNavMesh( dest, 64, 15 );
	if ( isdefined( nav ) )
		dest = nav;

	from = self.origin;
	// THE TELL: the teleporter's own discharge (flash, derez, warp) at both ends.
	// A fall into the void leaves out of everyone's sight and gets none.
	if ( why == "oob" )
		tod_teleport::discharge( from );
	self SetOrigin( dest + ( 0, 0, 2 ) );
	self SetVelocity( ( 0, 0, 0 ) );
	level thread tod_teleport::fx_burst( "tod_tp_kino", dest + ( 0, 0, 4 ), 2.0 );
	tod_teleport::discharge( dest );

	// THE PRICE OF THE FALL.
	downed = self laststand::player_is_in_laststand();
	hp_was = self.health;
	self.health = arrival_health( self.health, downed );

	reset( s );
	s.last_org = self.origin;
	s.quiet_until = now + TOD_RECALL_JUMP_MS;
	s.cool_until = now + TOD_RECALL_COOL_MS;
	s.count++;
	recall_log( "RECALL player=" + self GetEntityNumber() + " why=" + why + " src=" + src + " from=" + fmt( from ) + " " + tod_reach::describe( from )
		+ " to=" + fmt( dest ) + " " + tod_reach::describe( dest ) + " hp=" + hp_was + "->" + self.health + " downed=" + downed
		+ " count=" + s.count );
	return true;
}

// Stock's playable-area callback (_zm.gsc player_out_of_playable_area_monitor):
// TRUE = punish (the laugh and the kill), FALSE = spare. ON THE MAP (any zone,
// enabled or not: a floor below an unbought door) he is spared; off it, THE RECALL
// owns him until it gives up. A kill brush keeps stock's verdict.
function oopa_cb()   // self = player
{
	if ( self zm::in_kill_brush() )
		return self prev_cb();
	if ( self map_zone() != "" )
		return false;
	if ( isdefined( self.tod_recall ) && !IS_TRUE( self.tod_recall.gave_up ) )
		return false;
	return self prev_cb();
}

function prev_cb()   // self = player
{
	if ( isdefined( level.tod_recall_prev_oopa_cb ) )
		return self [[ level.tod_recall_prev_oopa_cb ]]();
	return true;
}

function fmt( v )
{
	if ( !isdefined( v ) )
		return "none";
	return "(" + int( v[ 0 ] ) + " " + int( v[ 1 ] ) + " " + int( v[ 2 ] ) + ")";
}

function recall_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_RECALL] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
