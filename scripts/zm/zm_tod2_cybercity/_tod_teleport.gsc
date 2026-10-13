// Fixed descent transit: four top-bay/floor pairs and a separate base/crown pair.
// Routes, arrivals and gate flags come from the map generator. Existing pad art,
// power, 60-second cooldown, fire-time group gather and downed ride-along remain.

#using scripts\shared\flag_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_score;     // the 750 fare (2026-09-28): can_player_purchase / minus_to_player_score
#using scripts\zm\_zm_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;
#using scripts\zm\zm_tod2_cybercity\_tod_fall;
#using scripts\zm\zm_tod2_cybercity\_tod_doors;          // crown return opens the side room from inside
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;   // derez_burst / play_sound_at_origin (host-based, proven)
#using scripts\zm\zm_tod2_cybercity\_tod_zombie_speed;   // slow() — the ONE writer for a timed anim-rate cut (v15 item 14)

#insert scripts\shared\shared.gsh;

// AFTER every #using/#insert — between them it kills the compile ("No
// generated data", live 2026-08-20). Map-owned model + stock FX; the matching
// xmodel,/fx, zone lines force-pack them (the finale-props rule).
#precache( "model", "tod_teleporter" );
#precache( "model", "tod_teleporter_off" );
#precache( "model", "tod_tp_recharge" );
#precache( "fx", "tod/teleporter/fx_tod_tp_ready" );
#precache( "fx", "tod/teleporter/fx_tod_tp_charge_field" );
#precache( "fx", "tod/teleporter/fx_tod_tp_release_field" );
#precache( "fx", "dlc4/genesis/fx_sophia_elec_charge_teleporter" );
#precache( "fx", "dlc1/castle/fx_elec_teleport_flash_lg" );
#precache( "fx", "dlc5/theater/fx_teleport_flashback_kino" );

#precache( "eventstring", "tod_tp_recharge" );

#namespace tod_teleport;

// v10.3 (playtest 2026-08-23: "teleporters take way too long to activate"):
// charge 2.2 -> 0.8s and cooldown 60 -> 30s. The 2.2s Kino wind-up was pure
// theatre inherited from map 1; at 0.8 the flash/derez still read.
#define TOD_TP_COOLDOWN_SEC   60   // 30 -> 45 -> 60, both 2026-08-29 (final: "Make the recharge on teleporters 1 minute")
#define TOD_TP_CHARGE_SEC     0.8
#define TOD_TP_COST           750  // 2026-09-28 (user: "Make the teleporter cost 750 on use. For any teleporter. The battle arena teleporter is free"): paid by the player who starts the warp; riders travel free
#define TOD_TP_STATE_LOG      1 // Bring-up in the user's normal match; zero after acceptance.
#define TOD_TP_TRIG_RADIUS    110     // the assembled pad is ~167 wide — stand in the ring
#define TOD_TP_TRIG_HEIGHT    96
// TOD_TP_BAY_TRIG_R IS GONE (v10.24). It existed only because the v10.22 bay
// was squeezed into the arena's east strip, where 170u spacing was all there
// was and the trigger had to shrink to 85 to fit it. The bay now has its own
// ROOM, so the pads sit at least 220 apart and the normal TOD_TP_TRIG_RADIUS
// (110) applies again — bigger, more forgiving triggers and one less special
// case.
#define TOD_TP_GATHER         120     // riders within this (2D) at FIRE time — v10.4: must be >= TOD_TP_TRIG_RADIUS (110), else a player who ACTIVATED from the trigger rim is excluded by his own ride (audit find)
#define TOD_TP_GATHER_Z       80      // ...and on the pad's floor (the balcony below shares no x/y, this is belt-and-braces)
#define TOD_TP_RING           48      // fan-out ring at the arrival pad (no capsule stack)
// THE DEPARTURE SLOW (v15 item 14, user 2026-08-31: "Teleporters should slow
// zombies in the radius as its being used"). Applied at the DEPARTURE pad only,
// the instant the charge starts — the arrival side is meant to be a clean exit,
// and slowing there would blunt the one moment the map wants to feel dangerous.
// Duration outlasts the 0.8s charge deliberately: the value of the slow is the
// half-second AFTER you rematerialize somewhere else, when the horde that was on
// you is still untangling itself.
#define TOD_TP_SLOW_RADIUS    256     // 2D, generous vs the 110 trigger ring — this is the crowd pressing in, not the pad itself
#define TOD_TP_SLOW_RATE      0.5     // half playback rate; composes with the round curve via slow_mult()
#define TOD_TP_SLOW_MS        3000    // 3s, vs TOD_TP_CHARGE_SEC 0.8
// Each generated row is one physical source pad. The top hub has three
// (30/20/10); each of those lounges has one; the base and crown each have one
// (8 total). Floor 40 carries the BATTLE ARENA chamber instead (_tod_arena).
function init()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	fx_register();
	level.tod_tp_trigs = [];
	level thread recharge_hud_watch();
	routes = tod_crown_data::transit_routes();
	transit_log( "INIT rev=2 routes=" + routes.size + " top_bay=3 floor_returns=3 base_crown=2" );
	for ( i = 0; i < routes.size; i++ )
	{
		r = routes[ i ];
		transit_log( "ROUTE id=" + r.id + " src=" + r.src + " dst=" + r.dst + " zone=" + r.zone + " lock=" + r.lock );
		level thread spawn_pad( r );
	}
}

function transit_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_TELEPORT] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// No zone is silently enabled here: a shortcut can only reach a live floor.
// This catches stale map/script pairs before anyone is moved into invalid space.
function destination_ready( route )
{
	return isdefined( level.zones ) && isdefined( level.zones[ route.zone ] )
	    && IS_TRUE( level.zones[ route.zone ].is_enabled );
}

function prepare_arrival( route )
{
	if ( !destination_ready( route ) )
	{
		transit_log( "DENY id=" + route.id + " reason=destination_zone_off zone=" + route.zone );
		return false;
	}
	if ( route.arrival_flag != "" && !tod_doors::force_open_by_flag( route.arrival_flag ) )
	{
		transit_log( "DENY id=" + route.id + " reason=arrival_door_missing flag=" + route.arrival_flag );
		return false;
	}
	if ( route.return_crown && !tod_fall::open_for_transit_return() )
	{
		transit_log( "DENY id=" + route.id + " reason=crown_return_not_ready" );
		return false;
	}
	return true;
}

// Shared by activation and displayed status: 0 available, 1 power, 2 floor,
// 3 THE HAVEN (docs/202 v3): a pad inside a haven whose guardians still live is
// dead until the haven is taken (level.tod_haven_locked_fn, _tod_haven::point_locked).
function pad_lock_reason_at( lock_flag, org )
{
	reason = pad_lock_reason( lock_flag );
	if ( reason == 1 )
		return 1;
	if ( isdefined( org ) && isdefined( level.tod_haven_locked_fn ) && [[ level.tod_haven_locked_fn ]]( org ) )
		return 3;
	return reason;
}

function pad_lock_reason( lock_flag )
{
	if ( !( level flag::exists( "power_on" ) && level flag::get( "power_on" ) ) ) return 1;
	if ( !isdefined( lock_flag ) || lock_flag == "" ) return 0;
	if ( !level flag::exists( lock_flag ) ) return 2;
	if ( !level flag::get( lock_flag ) ) return 2;
	return 0;
}

function pad_locked( lock_flag )
{
	return pad_lock_reason( lock_flag ) != 0;
}

function fx_register()
{
	if ( !isdefined( level._effect ) )
		level._effect = [];
	level._effect[ "tod_tp_beam" ]   = "tod/teleporter/fx_tod_tp_ready"; // low field leaves the metal deck visible
	level._effect[ "tod_tp_charge_field" ] = "tod/teleporter/fx_tod_tp_charge_field";
	level._effect[ "tod_tp_release_field" ] = "tod/teleporter/fx_tod_tp_release_field";
	level._effect[ "tod_tp_charge" ] = "dlc4/genesis/fx_sophia_elec_charge_teleporter"; // the wind-up
	level._effect[ "tod_tp_flash" ]  = "dlc1/castle/fx_elec_teleport_flash_lg";         // the bright discharge
	level._effect[ "tod_tp_kino" ]   = "dlc5/theater/fx_teleport_flashback_kino";       // arrival "materialize" beam
}

// Shared by all eight transit pads and the Battle Arena chamber. Keep this
// public function name for the arena caller (_tod_arena). One native model replaces the
// old nine fragments; origin is the same floor point used by triggers/FX.
function spawn_der_teleporter( origin, yaw_base )
{
	m = Spawn( "script_model", origin );
	if ( !isdefined( m ) )
	{
		model_dev_log( "spawn_failed", origin, yaw_base );
		return undefined;
	}
	// Spawn dark; the owning availability check chooses green or pending.
	m SetModel( "tod_teleporter_off" );
	m.angles = ( 0, yaw_base, 0 );
	m NotSolid();
	level thread model_end_cleanup( m );
	model_dev_log( "spawned", origin, yaw_base );
	return m;
}

// Power off/shutdown = dark; usable = green; powered but pending = yellow chase.
// Model twins share the accepted metal geometry and surface finish.
function model_state( m, state )
{
	if ( !isdefined( m ) ) return;
	mode = "off";
	if ( state == "ready" ) mode = "ready";
	else if ( state == "recharge" || state == "destination" || state == "paused" || state == "pending" ) mode = "pending";
	if ( isdefined( m.tod_tp_visual_state ) && m.tod_tp_visual_state == mode )
		if ( mode != "pending" || isdefined( m.tod_tp_chase ) ) return;
	prev = m.tod_tp_visual_state;
	if ( isdefined( m.tod_tp_chase ) )
	{
		m.tod_tp_chase notify( "tp_chase_stop" );
		m.tod_tp_chase Delete();
	}
	m.tod_tp_chase = undefined;
	if ( mode == "ready" ) m SetModel( "tod_teleporter" );
	else m SetModel( "tod_teleporter_off" );
	// PK23 (2026-10-05): a powered pad HUMS - the ready pad its low energy field (on the pad), the recharging pad a
	// quiet endless rising whir (on the chase host, so it ends with the chase). Dark = silent. tod_amb.csv.
	was_ready = ( isdefined( prev ) && prev == "ready" );
	if ( mode == "ready" && !was_ready ) m PlayLoopSound( "tod_teleport_idle_lp", 0.5 );
	else if ( mode != "ready" && was_ready ) m StopLoopSound( 0.5 );
	if ( mode == "pending" )
	{
		h = Spawn( "script_model", m.origin );
		if ( isdefined( h ) )
		{
			h SetModel( "tod_tp_recharge" ); h.angles = m.angles; h NotSolid();
			m.tod_tp_chase = h; h thread recharge_chase();
			m.tod_tp_chase_failed = false;
			h PlayLoopSound( "tod_teleport_cool_lp", 0.5 );
		}
		else if ( !IS_TRUE( m.tod_tp_chase_failed ) )
		{
			state_log( "CHASE_FAIL origin=" + m.origin ); m.tod_tp_chase_failed = true;
		}
	}
	m.tod_tp_visual_state = mode;
	if ( !isdefined( prev ) ) prev = "new";
	if ( prev != mode )
		state_log( "STATE origin=" + m.origin + " from=" + prev + " to=" + mode + " reason=" + state + " chase=" + isdefined( m.tod_tp_chase ) );
}
function recharge_chase()
{
	self endon( "death" ); self endon( "tp_chase_stop" );
	for ( ;; ) { self RotateYaw( 360, 3 ); wait 3; }
}
function model_end_cleanup( m )
{
	level waittill( "end_game" );
	model_state( m, "off" );
}
function state_log( msg )
{
	// Normal user playtest bring-up; retain the standard dev gate after acceptance.
	if ( !IS_TRUE( level.tod_dev ) && !TOD_TP_STATE_LOG ) return;
	line = "[TOD_TELEPORT_STATE] rev=2 palette=green_yellow ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function model_dev_log( state, origin, yaw )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_TELEPORT_MODEL] ms=" + GetTime() + " rev=1 state=" + state + " model=tod_teleporter origin=" + origin + " yaw=" + yaw + " pieces=1 collision=none";
	/#
	PrintLn( line );
	#/
}

// The idle beam on a permanent tag_origin host (the derez host pattern minus
// the delete). Returns the host so a pad can switch it off while recharging.
function spawn_beam( origin )
{
	h = Spawn( "script_model", origin + ( 0, 0, 2 ) );
	if ( !isdefined( h ) )
	{
		fx_dev_log( "tod_tp_beam", "host_failed", origin );
		return undefined;
	}
	h SetModel( "tag_origin" );
	PlayFxOnTag( level._effect[ "tod_tp_beam" ], h, "tag_origin" );
	fx_dev_log( "tod_tp_beam", "ready_emitted", origin );
	return h;
}

// One source pad, its model and trigger, and its independent cooldown.
function spawn_pad( route )
{
	level endon( "end_game" );
	src = route.src;
	src_yaw = route.src_yaw;
	trig_r = TOD_TP_TRIG_RADIUS;
	hint_ready = "Hold ^3[{+activate}]^7 ^5TELEPORTER^7 - " + route.hint + " ^2[Cost: 750]";   // LOCKSTEP TOD_TP_COST; a literal so lint_tod_hints expands it (one constant string per pad, as before)
	lock_flag = route.lock;

	pad_model = spawn_der_teleporter( src, src_yaw );

	// Script-spawned use-trigger => TriggerIgnoreTeam is REQUIRED (no prompt
	// otherwise). Raised 32u so the cursor lands.
	t = Spawn( "trigger_radius_use", src + ( 0, 0, 32 ), 0, trig_r, TOD_TP_TRIG_HEIGHT );
	if ( !isdefined( t ) )
	{
		transit_log( "PAD_FAILED id=" + route.id + " reason=trigger_spawn" );
		return;
	}
	t.tod_tp_route = route;
	t TriggerIgnoreTeam();
	t SetCursorHint( "HINT_NOICON" );
	t.tod_tp_src = src;
	t.tod_tp_model = pad_model;
	t.tod_tp_radius = trig_r;
	t.tod_tp_hint_ready = hint_ready;
	t.tod_tp_lock_flag = lock_flag;
	t.tod_tp_cooldown_until = 0;
	level.tod_tp_trigs[ level.tod_tp_trigs.size ] = t;

	refresh( t );                 // ready: beam on + the use hint
	level thread state_ticker( t );

	for ( ;; )
	{
		t waittill( "trigger", player );
		if ( !isdefined( player ) || !isplayer( player ) )
			continue;
		if ( !zm_utility::is_player_valid( player ) )
			continue;   // downed / spectating
		// A teammate is down under your feet and you are holding USE to revive
		// them — do NOT charge the pad and warp away, leaving them to bleed out
		// on a floor nobody else can reach. Reviving polls the raw USE button
		// (_zm_laststand.gsc:1129) independently of which prompt is drawn, so
		// without this the revive press fires the teleporter too.
		// SOUNDED, unlike the door/crate/PaP guards: this pad's mute refusals are
		// exactly what produced the 2026-08-26 "teleporter wasn't activated"
		// report, so every refusal here now announces itself.
		if ( player zm_utility::in_revive_trigger() )
		{
			player PlaySound( "zmb_no_purchase" );
			continue;
		}
		// THE WORLD IS FROZEN FOR AN UPGRADE PICK — refuse, but SAY SO.
		//
		// THIS SILENCE IS THE "TELEPORTER WASN'T ACTIVATED" BUG (live report
		// 2026-08-26: "A player died and i got to a floor 30 with teleporter and
		// it wasnt activated. But before that I was using teleporters fine").
		// The pad was refusing CORRECTLY and the refusal was completely mute: no
		// sound, no hint change, beam still lit. Indistinguishable from a dead
		// trigger, so it read as a broken teleporter.
		//
		// AND THE WINDOW IS WIDE, WHICH IS WHY THIS IS REACHABLE EVERY FOURTH
		// ROUND RATHER THAN BEING A FREAK COINCIDENCE. run_upgrade_event holds
		// the pause until every participant picks or 20s elapse, but
		// player_choice_flow calls menu_freeze(false) PER PLAYER the instant
		// that player locks a card. So the first player to choose is unfrozen
		// and running around a still-paused world for the remaining ~13-18s —
		// free to walk onto a pad that will ignore them without a peep. A player
		// who was DOWN or DEAD when the event fired is excluded from the event
		// entirely (_tod_upgrades.gsc:1672), so they are never frozen at all and
		// hit this window from the very first second.
		//
		// Every OTHER refusal in this loop plays zmb_no_purchase; this one now
		// matches them. The availability lights now go dark during this pause;
		// refresh reuses the existing ready hint and adds no triggerstring.
		if ( IS_TRUE( level.tod_upgrade_pause ) )
		{
			player PlaySound( "zmb_no_purchase" );
			continue;
		}
		if ( IS_TRUE( t.tod_tp_busy ) )
			continue;   // a charge is already running on this pad

		// LOCKED (an up pad whose breather door is unbought) or recharging ->
		// the stock deny sound (no caption).
		if ( pad_lock_reason_at( t.tod_tp_lock_flag, t.tod_tp_src ) != 0 || !destination_ready( route ) || GetTime() < t.tod_tp_cooldown_until )
		{
			transit_log( "DENY id=" + route.id + " player=" + ( player GetEntityNumber() ) + " lock_reason=" + pad_lock_reason( route.lock ) + " zone_ready=" + destination_ready( route ) + " cooldown_ms=" + ( t.tod_tp_cooldown_until - GetTime() ) );
			player PlaySound( "zmb_no_purchase" );
			continue;
		}

		// THE FARE (2026-09-28): the player who starts the warp pays; the pad refuses (sounded,
		// logged) when they cannot afford it. Checked AFTER every other refusal so a locked or
		// recharging pad never reads as a money problem.
		if ( !( player zm_score::can_player_purchase( TOD_TP_COST ) ) )
		{
			transit_log( "DENY id=" + route.id + " player=" + ( player GetEntityNumber() ) + " reason=no_money cost=" + TOD_TP_COST + " score=" + player.score );
			player PlaySound( "zmb_no_purchase" );
			continue;
		}
		player zm_score::minus_to_player_score( TOD_TP_COST );
		player PlaySound( "zmb_cha_ching" );
		transit_log( "CHARGE id=" + route.id + " player=" + player GetEntityNumber() + " dst=" + route.dst + " paid=" + TOD_TP_COST );
		// Arm the cooldown BEFORE the warp so a second press can't double-fire,
		// flip the pad to its recharging look, then run the sequence.
		t.tod_tp_cooldown_until = GetTime() + TOD_TP_COOLDOWN_SEC * 1000;
		t.tod_tp_busy = true;
		refresh( t );
		do_teleport( route );
		t.tod_tp_busy = undefined;
	}
}

// Ready state -> beam + hint, applied on the EDGE only (two constant hint
// strings — the engine caps the triggerstring cache at 250 UNIQUE strings, so
// never a per-second countdown in the hint).
function refresh( t )
{
	if ( !isdefined( t ) )
		return;
	// Four fixed hints; countdown numbers travel through LUI, not SetHintString.
	state = "ready";
	reason = pad_lock_reason_at( t.tod_tp_lock_flag, t.tod_tp_src );
	if ( reason == 1 )
		state = "power";
	else if ( reason == 3 )
		state = "corrupted";   // docs/202 v3: the haven's guardians still live
	else if ( reason == 2 || !destination_ready( t.tod_tp_route ) )
		state = "destination";
	else if ( GetTime() < t.tod_tp_cooldown_until )
		state = "recharge";
	else if ( IS_TRUE( level.tod_upgrade_pause ) )
		state = "paused";
	model_state( t.tod_tp_model, state );
	if ( isdefined( t.tod_tp_state ) && t.tod_tp_state == state )
		return;
	prev = t.tod_tp_state;   // undefined on the very first call (spawn_pad init)
	t.tod_tp_state = state;
	transit_log( "STATE id=" + t.tod_tp_route.id + " state=" + state + " lock_reason=" + reason );
	fx_dev_log( "tod_tp_beam", "pad_" + state, t.tod_tp_src );
	if ( state == "ready" )
	{
		if ( !isdefined( t.tod_tp_beam ) )
			t.tod_tp_beam = spawn_beam( t.tod_tp_src );
		t SetHintString( t.tod_tp_hint_ready );
		// RECHARGE-COMPLETE cue (2026-08-29, docs/43) — the beam snapping back on
		// was the map's one state change with a visual and no sound at all.
		//
		// GATED ON prev == "recharge" AND NOTHING ELSE, which is the whole trick:
		// refresh() also runs once per pad from spawn_pad (:320) with prev
		// undefined, so an ungated call here would fire every teleporter in the
		// map simultaneously at level start. The locked -> ready edge is excluded
		// too: that is a breather door being bought, which already has its own
		// purchase feedback, and it would double up on it.
		if ( isdefined( prev ) && prev == "recharge" )
			tod_perk_scatter::play_sound_at_origin( t.tod_tp_src, "tod_teleport_ready", 4 );
	}
	else
	{
		if ( isdefined( t.tod_tp_beam ) )
			t.tod_tp_beam Delete();
		t.tod_tp_beam = undefined;
		if ( state == "power" )
			t SetHintString( "^5TELEPORTER^7 - ^1power required" );
		else if ( state == "corrupted" )
			t SetHintString( "^5TELEPORTER^7 - ^1defeat the guardians" );
		else if ( state == "destination" )
			t SetHintString( "^5TELEPORTER^7 - ^1destination locked" );
		else if ( state == "paused" )
			t SetHintString( t.tod_tp_hint_ready ); // existing deny cue explains a card-pick pause
		else
			t SetHintString( "^5TELEPORTER^7 - ^1recharging..." );
	}
}

// Catches the cooldown-elapsed edge (beam back on, hint back to usable).
function state_ticker( t )
{
	level endon( "end_game" );
	for ( ;; )
	{
		wait 1;
		if ( !isdefined( t ) )
			return;
		refresh( t );
	}
}

// Only the pad whose use radius contains this player supplies the countdown.
// The eight use radii do not overlap; height excludes other floors.
function recharge_pad_for( player )
{
	if ( !IsAlive( player ) ) return -1;
	best = -1;
	nearest = 999999;
	for ( i = 0; i < level.tod_tp_trigs.size; i++ )
	{
		t = level.tod_tp_trigs[ i ];
		if ( !isdefined( t ) ) continue;
		if ( abs( player.origin[2] - t.tod_tp_src[2] ) > TOD_TP_TRIG_HEIGHT ) continue;
		d = Distance2D( player.origin, t.tod_tp_src );
		if ( d > t.tod_tp_radius || d >= nearest ) continue;
		nearest = d;
		best = i;
	}
	return best;
}

function recharge_seconds( until )
{
	left = until - GetTime();
	if ( left <= 0 ) return 0;
	return int( ( left + 999 ) / 1000 );
}

function recharge_hud_watch()
{
	level endon( "end_game" );
	tick = 0;
	for ( ;; )
	{
		foreach ( p in GetPlayers() )
		{
			pad = recharge_pad_for( p );
			secs = 0;
			pct = 0;
			if ( pad >= 0 )
			{
				t = level.tod_tp_trigs[ pad ];
				if ( !pad_locked( t.tod_tp_lock_flag ) )
					secs = recharge_seconds( t.tod_tp_cooldown_until );
				if ( secs > 0 )
					pct = int( 100.0 * ( TOD_TP_COOLDOWN_SEC - secs ) / TOD_TP_COOLDOWN_SEC );
			}
			// Changes only, plus a five-second refresh for recreated HUD widgets.
			if ( tick == 0 || !isdefined( p.tod_tp_hud_seconds ) || p.tod_tp_hud_seconds != secs
			  || !isdefined( p.tod_tp_hud_pad ) || p.tod_tp_hud_pad != pad )
			{
				p.tod_tp_hud_seconds = secs;
				p.tod_tp_hud_pad = pad;
				p LuiNotifyEvent( &"tod_tp_recharge", 2, secs, pct );
			}
		}
		wait 0.25;
		tick++;
		if ( tick >= 20 ) tick = 0;
	}
}

// Throwaway FX host: PlayFxOnTag on a tag_origin for `secs`, then delete. NO
// endon — a thread killed mid-wait would orphan the host with a looping FX
// playing (map 1 review).
function fx_burst( key, origin, secs, overlay_key = undefined )
{
	if ( !isdefined( level._effect[ key ] ) )
	{
		fx_dev_log( key, "asset_missing", origin );
		return;
	}
	op = GetTime();
	h = Spawn( "script_model", origin );
	if ( !isdefined( h ) )
	{
		fx_dev_log( key, "host_failed", origin, op );
		return;
	}
	h SetModel( "tag_origin" );
	// Arrival's existing delay settles the rider. This separate delay gives
	// the newly created host time to replicate before its one-shot FX event.
	WAIT_SERVER_FRAME;
	WAIT_SERVER_FRAME;
	if ( !isdefined( h ) )
	{
		fx_dev_log( key, "host_lost", origin, op );
		return;
	}
	PlayFxOnTag( level._effect[ key ], h, "tag_origin" );
	fx_dev_log( key, "emitted", origin, op );
	// Both layers share the same lifetime/host. No extra entity per overlay.
	if ( isdefined( overlay_key ) )
	{
		if ( isdefined( level._effect[ overlay_key ] ) )
		{
			PlayFxOnTag( level._effect[ overlay_key ], h, "tag_origin" );
			fx_dev_log( overlay_key, "overlay_emitted", origin, op );
		}
		else
			fx_dev_log( overlay_key, "overlay_missing", origin, op );
	}
	wait secs;
	if ( isdefined( h ) )
		h Delete();
	fx_dev_log( key, "finished", origin, op );
}

function fx_dev_log( key, state, origin, op = 0 )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_TELEPORT_FX] rev=2 ms=" + GetTime() + " op=" + op + " key=" + key + " state=" + state + " origin=" + origin;
	/#
	PrintLn( line );
	#/
}

// The bright DISCHARGE at a pad: flash + the de-rez burst (numbers + zap) +
// the warp boom.
function discharge( origin )
{
	level thread fx_burst( "tod_tp_flash", origin + ( 0, 0, 4 ), 2.0, "tod_tp_release_field" );
	tod_perk_scatter::derez_burst( origin );
	tod_perk_scatter::play_sound_at_origin( origin, "tod_warp", 3 );
}

// THE DEPARTURE SLOW (v15 item 14). Every trash zombie within
// TOD_TP_SLOW_RADIUS of the departing pad drops to TOD_TP_SLOW_RATE playback
// for TOD_TP_SLOW_MS.
//
// GOES THROUGH tod_zombie_speed::slow(), NEVER a raw ASMSetAnimationRate. The
// speed module runs a 1.5s keep-alive sweep that RE-ASSERTS gait+rate from the
// round curve (one-shot overrides decay — the map-1 lesson), so a hand-written
// rate here would be silently stomped within 1.5s and the feature would look
// like it half-worked. slow() is the supported lane: the sweep multiplies
// slow_mult() back in, so a live slow survives every re-assert and an expired
// one restores itself.
//
// slow() also brings three exclusions we want for free and should not
// re-implement: bosses and custom-speed enemies are skipped (their ASMs freeze
// if stomped), anything already under another system's anim slow (Widow's Wine
// cocoon, Time Warp) is left alone, and a stronger live slow is never weakened.
// So ELITES ARE IMMUNE BY CONSTRUCTION — a Panzer walks through the field at
// full speed, which is the correct read for a boss.
function slow_the_crowd( org )
{
	if ( !isdefined( org ) )
		return;
	ai = GetAISpeciesArray( "all" );
	for ( i = 0; i < ai.size; i++ )
	{
		z = ai[ i ];
		if ( !isdefined( z ) || !isalive( z ) )
			continue;
		if ( Distance2D( z.origin, org ) > TOD_TP_SLOW_RADIUS )
			continue;
		z tod_zombie_speed::slow( TOD_TP_SLOW_RATE, TOD_TP_SLOW_MS );
	}
}

// Kino teleport, no player lock: CHARGE (FX at torso height + hum) -> fire.
function do_teleport( route )
{
	src = route.src;
	dst = route.dst;
	dst_yaw = route.dst_yaw;
	slow_the_crowd( src );   // v15 item 14 — fires WITH the charge, not after it
	level thread fx_burst( "tod_tp_charge", src + ( 0, 0, 40 ), TOD_TP_CHARGE_SEC + 0.5, "tod_tp_charge_field" );
	// tod_teleport_fire (2026-08-29, docs/43): the map's own 2.2s time-distortion
	// warp, replacing the ported acc hum. Emitted at SRC, so what each side hears
	// differs and that is correct:
	//   * the RIDER hears its first TOD_TP_CHARGE_SEC (0.8s) — the wind-up — and
	//     then leaves, so it is cut off mid-sweep by the arrival discharge at dst.
	//     The cut IS the translocation; do not "fix" it by re-playing the full
	//     asset at dst, which would read as two teleports.
	//   * anyone LEFT BEHIND near the pad hears the whole 2.2s.
	// Side effect worth keeping: tod_warp now only marks the two DISCHARGES, so
	// departure and arrival no longer open with the identical cue.
	tod_perk_scatter::play_sound_at_origin( src, "tod_teleport_fire", 4 );
	wait TOD_TP_CHARGE_SEC;

	discharge( src );   // departure flash + boom

	// Gather at FIRE time: whoever is standing on the pad NOW rides.
	//
	// A CRAWLER RIDES ALONG (v15, user 2026-08-31: "If you are down on a
	// teleporter it should still teleport you"). The third arg of stock
	// is_player_valid is `ignore_laststand_players` (_zm_utility.gsc), so this
	// keeps every other exclusion intact — dead, spectating, intermission and
	// is_zombie all still fail — and lifts ONLY the last-stand clause. Note
	// IsAlive() is TRUE in last stand, so the laststand clause really was the
	// whole gate.
	//
	// RIDE-ALONG ONLY, NOT SELF-ACTIVATION: the trigger's own gates upstream
	// (:328 is_player_valid, and in_revive_trigger at :338) are UNCHANGED, so a
	// crawler still cannot fire the pad themselves. That asymmetry is the point
	// — a downed player yanking their own body out from under the teammate who
	// is mid-revive is a worse outcome than not riding at all. They ride when
	// somebody standing decides to take them.
	//
	// ⚠️ UNPROVEN LINK, TEST IN GAME BEFORE TRUSTING: the revive trigger is
	// LinkTo'd to the player (_zm_laststand.gsc:849-852), which SHOULD track a
	// hard SetOrigin — but that cannot be proven from source. If it does not
	// follow, the teleported crawler is unrevivable at the destination, which is
	// strictly worse than the bug this fixes. Discriminator: crawler on a pad ->
	// teammate rides them -> teammate revives at arrival.
	riders = [];
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || !zm_utility::is_player_valid( p, false, true ) )
			continue;
		if ( Distance2D( p.origin, src ) > TOD_TP_GATHER )
			continue;
		if ( abs( p.origin[ 2 ] - src[ 2 ] ) > TOD_TP_GATHER_Z )
			continue;
		riders[ riders.size ] = p;
	}

	// Prepare before SetOrigin: the crown side door and sealed hall must be open.
	// Empty charges never open doors or change the Fall phase.
	if ( riders.size > 0 && !prepare_arrival( route ) ) return;
	transit_log( "FIRE id=" + route.id + " riders=" + riders.size + " src=" + src + " dst=" + dst );
	for ( i = 0; i < riders.size; i++ )
	{
		ang = i * 360 / riders.size;
		off = ( cos( ang ) * TOD_TP_RING, sin( ang ) * TOD_TP_RING, 0 );   // ring so capsules don't stack
		riders[ i ] SetOrigin( dst + off );
		riders[ i ] SetPlayerAngles( ( 0, dst_yaw, 0 ) );
		transit_log( "ARRIVE id=" + route.id + " player=" + riders[ i ] GetEntityNumber() + " origin=" + riders[ i ].origin + " zone=" + route.zone );
	}

	// A ride moves players thousands of units in ONE FRAME, which every
	// distance-watching system reads as "the thing I am watching just stalled".
	// tod_bosses::tod_boss_stuck_watch resets its no-progress accumulator on this
	// counter — without it, a breather ride makes `best` unbeatable and the
	// watchdog relocates a boss that was never stuck, which is exactly the
	// "elites randomly spawn at you when you are too far away" report.
	if ( riders.size > 0 )
	{
		level.tod_tp_stamp = ( ( isdefined( level.tod_tp_stamp ) ) ? level.tod_tp_stamp + 1 : 1 );
		// The ride is the ONE moment we know for certain a party just abandoned a
		// floor. _tod_stray waits out the zone manager's riser rebuild, then runs
		// hot for 6s so the horde arrives instead of walking forty floors down.
		// NOTIFY ONLY — no import in either direction, so _tod_stray can be
		// deleted without touching this file and this line becomes a no-op.
		level notify( "tod_stray_pump" );
	}

	// TWO FRAMES BETWEEN THE RIDE AND THE ARRIVAL FX (v17.31, user 2026-09-04:
	// "occasionally the teleporter fx wont trigger. The sfx always does but
	// sometimes you will use it and not see any teleporter lightning fx").
	//
	// WHAT THE REPORT RULES OUT, and this is the useful half. The obvious suspect
	// was the gentity pool — fx_burst opens with `h = Spawn(...); if (!isdefined(h))
	// return;` and drops the effect silently when the pool is full, which would be
	// exactly this intermittent. It is NOT that: play_sound_at_origin
	// (_tod_perk_scatter.gsc:929) spawns a script_origin and carries the SAME
	// "entity pool full — drop the sound" guard, so an exhausted pool would take
	// the sound with it. The sound ALWAYS plays. One observation, one suspect
	// eliminated.
	//
	// WHAT IS LEFT is the asymmetry between the two lanes at the moment of a ride.
	// The riders were SetOrigin'd thousands of units away in the loop above and
	// this ran in the SAME server frame. A sound is emitted by an entity that then
	// lives 3-4 s, so a client has a long window to resolve it; PlayFxOnTag is a
	// ONE-SHOT event on a host spawned that same frame, with no replay — a client
	// whose snapshot has not yet caught up with where its player now IS misses it
	// outright and there is no second chance. That is the shape of the bug:
	// intermittent, FX-only, and only on the lane that moves the viewer.
	//
	// ⚠️ HONEST STATUS: the elimination above is SOUND; the replacement mechanism
	// is INFERRED, not proven from source — nothing here can observe a client's
	// snapshot. What is certain is that a same-frame teleport-then-effect is the
	// one thing this lane does that the sound lane does not care about, and that
	// two frames is the cheapest way to stop doing it. If the report survives this
	// build, the next suspect is the FX host itself (spawn it BEFORE the ride so
	// it is already replicating, and only then PlayFxOnTag) — do NOT re-open the
	// entity-pool theory, it is dead on the evidence above.
	//
	// COST: ~0.1 s of extra `tod_tp_busy` on a pad whose cooldown is already armed
	// (TOD_TP_COOLDOWN_SEC, set before this function was called), so nothing the
	// player can reach is gated on it. The departure flash is deliberately NOT
	// delayed — the rider is meant to miss that one (the sound comment above says
	// why: "the cut IS the translocation"), and the bystanders who do see it never
	// moved, so their snapshot was never stale.
	WAIT_SERVER_FRAME;
	WAIT_SERVER_FRAME;

	// ARRIVAL: materialize beam + flash + boom at the base pad (fires even
	// for an empty ride — the device still discharged).
	level thread fx_burst( "tod_tp_kino", dst + ( 0, 0, 4 ), 3.0 );
	discharge( dst );
}
