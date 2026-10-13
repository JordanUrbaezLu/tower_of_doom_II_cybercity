// =============================================================================
// _tod_archer_bow.gsc - THE DRAW: a fully drawn bow hits harder than a tap
// (2026-09-25; Hellbound's docs/94 lever, the damage half only).
//
// User: "the bow should do max damage at full charge and half charge it should
// do more damage ... It does the same damage no matter how charged it is ... we
// want to encourage players to fully cock it back and it'll do max damage."
//
// WHY THERE WAS NO GAP. The bows (cc_bow / cc_fire_bow, cloned from Hellbound's
// hb_bow / hb_fire_bow) are Charge Shot weapons with `chargeShotMaxLevel 1`: the
// engine lets you hold the draw, but the arrow's damage never reads it.
//
// HOW. A per-player poll stamps the fire button's press time while a bow is
// held; "weapon_fired" (raised on release for a Charge Shot weapon) closes the
// interval; the fraction of the bow's own draw window becomes a multiplier from
// TOD_AB_MIN_MULT (tap) to TOD_AB_MAX_MULT (full draw), linear - so a half draw
// is exactly halfway. _tod_upgrades::upgrade_damage_cb applies it to the raw
// hit beside gun_balance_mult, so every card stacks on top of it. The power
// scale's /10 happens before the chain and is untouched.
//
// WHICH SHOT IS WHICH. The fraction is stamped on the ARROW ("grenade_fire"
// hands the projectile over; the damage chain gets it back as `inflictor`) and
// on the player with a timestamp as the fallback. [TOD_ABOW] dev logs say which
// lane answered each hit.
//
// The crossbow (cc_crossbow) is not a draw weapon and is never matched by the draw;
// QUICK DRAW's per-level term (quickdraw_mult) covers it with the bows.
//
// THE AUTOMATIC BOW (2026-10-05, user: "you hold it down and then once it's fully
// charged it shoots ... when it's maxed out it almost becomes an automatic bow").
// The bows now carry chargeShotFireWhenQueueReachesMax 1 (gen_tod_twins): the
// ENGINE releases the arrow at full draw while the trigger is held, and a held
// trigger draws again. So a shot whose trigger is STILL DOWN when it fires is a
// full draw by definition (frac 1, no clock read): at Lv9 QUICK DRAW the whole
// draw is ~0.1 s past the minimum, two server frames, far too coarse to time.
// A released shot is timed as before. After a held shot the next draw starts
// when the release clip ends (now + the form's fireTime), and THAT is the press
// time a later partial release is measured from (a held chain can never pay a
// half draw x3). [TOD_ABOW] FIRE logs auto=1/0; HOLD_STALL says the engine
// wanted a re-press (the trigger stayed down a full cycle with no arrow); HOLD_END
// counts the arrows of one hold.
// =============================================================================

#using scripts\shared\callbacks_shared;

#insert scripts\shared\shared.gsh;

#namespace tod_archer_bow;

#define TOD_AB_REV              "cyber_bow_auto_v2"

// Tap = MIN x, full draw = MAX x, linear between (half draw = 2.0 x).
// MAX is LOCKSTEP gen_tod_twins AUTO_DRAW_FULL_MULT: the even-tier DPS pin divides a held arrow by it.
#define TOD_AB_MIN_MULT         1.0
#define TOD_AB_MAX_MULT         3.0
// Button poll period (s): one server frame.
#define TOD_AB_POLL             0.05
// A player-side stamp older than this is stale; the hit then reads as a tap.
#define TOD_AB_STAMP_TTL_MS     3000
// One shot raises both "weapon_fired" and "missile_fire"; a stamp this fresh is that shot's (the fastest
// possible cycle, a tap at Lv9, is fireTime 0.09 + chargeShotMinTime 0.10 = 190 ms).
#define TOD_AB_SAME_SHOT_MS     100

// Draw windows = the bows' s0 GDT chargeShotMinTime / chargeShotMaxTime, and the release (fireTime) a held
// chain waits out before it draws again - gen_tod_twins cc_bow / cc_fire_bow tune.set (2026-10-05: 0.55 / 0.45
// draws, were 1.2 / 0.8). The PaP forms draw and release x0.8 (setUp + papApply). QUICK DRAW scales all of it
// by shot_step(). LOCKSTEP tools/test_archer_autobow.js.
#define TOD_AB_PLAIN_MAX        0.55
#define TOD_AB_FIRE_MAX         0.45
#define TOD_AB_MIN_TIME         0.10
#define TOD_AB_PLAIN_FIRE       0.30
#define TOD_AB_FIRE_FIRE        0.25
#define TOD_AB_PAP_TIME         0.8
// A draw shorter than this gets no creak and no full-power layer: at an automatic cadence they stack into a buzz
// over the shot sound (the shot itself still plays every arrow).
#define TOD_AB_CUE_MIN          0.3
// A trigger held this long past the next arrow's due time with no arrow = the engine wants a re-press (HOLD_STALL).
#define TOD_AB_STALL_SLACK_MS   400
// QUICK DRAW's per-level term (2026-10-05): speed = 3^(Lv/9), one +13% per level. The weapon steps carry it at
// Lv2 / 4 / 6 / 8; an odd level pays its 13% as arrow / bolt damage here. 3^(1/9) = 1.1298.
#define TOD_AB_QD_LEVEL_MULT    1.1298

// THE DRAW YOU CAN HEAR (2026-09-26 SFX pass; user: "best sound and visual
// effects possible ... for each shot"). The donor bows fire the DE shot sound
// and nothing else: no string creak on the pull, no heavier release at full
// draw. Der Eisendrache's own sheet (elemental_bow_sounds.csv, in this map's
// zone config) carries both for the base and the rune bow: a 2D pullback creak
// (2.2 s, stopped the moment you let go so a tap stays a tap) and a full-power
// release that layers over the shot only when the draw reads >= TOD_AB_FULL.
// PlayLocalSound = the archer alone hears it, same lane as every HUD cue here.
#define TOD_AB_FULL             0.98
#define TOD_AB_DRAW_PLAIN       "wpn_elemental_bow_draw_plr"
#define TOD_AB_DRAW_FIRE        "wpn_runeprison_bow_draw_plr"
#define TOD_AB_FULL_PLAIN       "wpn_elemental_bow_fire_full_plr"
#define TOD_AB_FULL_FIRE        "wpn_runeprison_bow_fire_full_plr"

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_ABOW] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function init()
{
	callback::on_spawned( &on_player_spawned );
	dev_log( "INIT rev=" + TOD_AB_REV + " mult=" + TOD_AB_MIN_MULT + ".." + TOD_AB_MAX_MULT + " auto_release=1" +
	         " draw_plain=" + TOD_AB_MIN_TIME + ".." + TOD_AB_PLAIN_MAX + " release_plain=" + TOD_AB_PLAIN_FIRE +
	         " draw_fire=" + TOD_AB_MIN_TIME + ".." + TOD_AB_FIRE_MAX + " release_fire=" + TOD_AB_FIRE_FIRE +
	         " pap_time=" + TOD_AB_PAP_TIME + " qd_level_mult=" + TOD_AB_QD_LEVEL_MULT );
}

// self = player. One watcher set per player for the whole game.
function on_player_spawned()
{
	if ( IS_TRUE( self.tod_ab_watch_on ) ) return;
	self.tod_ab_watch_on = true;
	self thread draw_watch();
	self thread fire_watch();
	self thread projectile_watch();
}

function is_bow( weapon )
{
	if ( !isdefined( weapon ) || !isdefined( weapon.name ) ) return false;
	return ( IsSubStr( weapon.name, "cc_bow" ) || IsSubStr( weapon.name, "cc_fire_bow" ) );
}

// The Archer's three primaries: the two draw bows and the crossbow (QUICK DRAW's per-level term covers all three).
function is_archer_gun( weapon )
{
	if ( !isdefined( weapon ) || !isdefined( weapon.name ) ) return false;
	return ( is_bow( weapon ) || IsSubStr( weapon.name, "cc_crossbow" ) );
}

// QUICK DRAW's level, read straight off tod_levels: this module imports no tod module (no cycle with _tod_upgrades).
function private qd_level()
{
	if ( isdefined( self.tod_levels ) && isdefined( self.tod_levels[ "shotspeed" ] ) ) return Int( self.tod_levels[ "shotspeed" ] );
	return 0;
}

// ---- THE PURE HALF (self-less, no engine state; tools/test_archer_autobow.js runs these verbatim) ----

// QUICK DRAW (key shotspeed): the time multiplier of the WEAPON STEP a level holds, s0..s4 at Lv0 / 2 / 4 / 6 / 8 =
// 3^(-Lv/9) (2026-10-05: x3 at the top, was x2). The draw window, the release and the engine's own auto-release all
// scale by it, so the script's full draw IS the engine's at every level (the old per-level script window that ran
// ahead of the weapon at odd levels is gone: an odd level is paid by qd_level_mult). LOCKSTEP gen_tod_twins
// SHOTSPEED_STEP + _tod_upgrades axis_level. (DEADEYE's d forms carry only the girth since 2026-09-27.)
function shot_step_lv( lv )
{
	t = array( 1.0, 0.7834, 0.6137, 0.4807, 0.3766 );
	s = Int( lv / 2 );
	if ( s < 0 ) s = 0;
	if ( s > 4 ) s = 4;
	return t[ s ];
}

// QUICK DRAW's per-level term: every level is the same x1.13 of speed; the weapon carries the cadence at the even
// levels, so an ODD level (Lv1 / 3 / 5 / 7 / 9) pays its 13% as arrow / bolt damage.
function qd_level_mult( lv )
{
	if ( lv > 0 && ( lv % 2 ) == 1 ) return TOD_AB_QD_LEVEL_MULT;
	return 1.0;
}

// The full draw (the engine's auto-release point) of a bow named `name` at QUICK DRAW `lv`, in seconds.
function draw_window_lv( name, lv )
{
	m = TOD_AB_PLAIN_MAX;
	if ( IsSubStr( name, "cc_fire_bow" ) ) m = TOD_AB_FIRE_MAX;
	if ( IsSubStr( name, "_up" ) ) m = m * TOD_AB_PAP_TIME;
	return m * shot_step_lv( lv );
}

// The release clip (the form's fireTime) a held chain waits out before it draws again, in seconds.
function release_lv( name, lv )
{
	m = TOD_AB_PLAIN_FIRE;
	if ( IsSubStr( name, "cc_fire_bow" ) ) m = TOD_AB_FIRE_FIRE;
	if ( IsSubStr( name, "_up" ) ) m = m * TOD_AB_PAP_TIME;
	return m * shot_step_lv( lv );
}

// 0..1 for a RELEASE after `held` seconds of a `window`-second draw. A packed bow at Lv8+ draws only ~0.04 s past
// the engine's minimum: there, past the minimum IS the full draw.
function draw_frac( held, window )
{
	span = window - TOD_AB_MIN_TIME;
	if ( span <= 0.05 )
	{
		if ( held >= TOD_AB_MIN_TIME ) return 1;
		return 0;
	}
	frac = ( held - TOD_AB_MIN_TIME ) / span;
	if ( frac < 0 ) frac = 0;
	if ( frac > 1 ) frac = 1;
	return frac;
}

// THE AUTOMATIC BOW's one rule: an arrow that leaves while the trigger is still DOWN was released by the engine at
// full draw (chargeShotFireWhenQueueReachesMax) = 1, whatever the clock says; one that leaves on a release is timed.
function shot_frac( button_down, held, window )
{
	if ( button_down ) return 1;
	return draw_frac( held, window );
}

// ---- the engine-facing half ----

// self = player: the weapon step's time multiplier for this player now.
function shot_step()
{
	return shot_step_lv( self qd_level() );
}

// PUBLIC (self-less): QUICK DRAW's per-level term on the Archer's own arrows and bolts; 1.0 for anything else.
function quickdraw_mult( attacker, weapon )
{
	if ( !isdefined( attacker ) || !isplayer( attacker ) || !is_archer_gun( weapon ) ) return 1.0;
	if ( !isdefined( attacker.tod_class ) || attacker.tod_class != "assault" ) return 1.0;
	return qd_level_mult( attacker qd_level() );
}

// PUBLIC (self = player): the full draw of `weapon` for this player now, in seconds - the engine's auto-release point.
// _tod_archer_rune reads it for the armed-draw hum.
function draw_window( weapon )
{
	return draw_window_lv( weapon.name, self qd_level() );
}

// self = player: the release a held chain waits out, for `weapon` now, in seconds.
function private release_time( weapon )
{
	return release_lv( weapon.name, self qd_level() );
}

// self = player. Stamps the fire button's press time while a bow is held.
function draw_watch()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	pressed = false;
	creak = undefined;    // the draw alias playing right now, if any
	creak_for = -1;       // the draw (its start ms) that creak belongs to: one creak per draw, a held chain draws again
	stall_told = false;   // HOLD_STALL once per hold
	// (docs/206's full-draw glow + tick is retired here, 2026-10-05: it said "release now", and the bow now releases
	// itself at that very moment; the full-power release layer in fire_watch is the full-draw tell.)
	for ( ;; )
	{
		wait TOD_AB_POLL;
		w = self GetCurrentWeapon();
		if ( !is_bow( w ) )
		{
			if ( pressed ) self hold_end( "swapped" );
			pressed = false;
			self.tod_ab_press_ms = undefined;
			creak = self draw_stop( creak );   // swapped away mid-draw
			continue;
		}
		down = self AttackButtonPressed();
		now = GetTime();
		if ( down && !pressed )
		{
			// a fresh press draws from now - unless a held chain already set the next draw (its release is still playing)
			if ( !isdefined( self.tod_ab_press_ms ) || self.tod_ab_press_ms < now ) self.tod_ab_press_ms = now;
			self.tod_ab_hold_ms = now;
			self.tod_ab_hold_shots = 0;
			stall_told = false;
		}
		else if ( !down && pressed )
		{
			creak = self draw_stop( creak );   // released: a tap must not creak on
			self hold_end( "released" );
		}
		if ( down && isdefined( self.tod_ab_press_ms ) && now >= self.tod_ab_press_ms )
		{
			win = self draw_window( w );
			if ( creak_for != self.tod_ab_press_ms )
			{
				creak = self draw_stop( creak );
				creak_for = self.tod_ab_press_ms;
				if ( win >= TOD_AB_CUE_MIN )
				{
					creak = draw_alias( w );
					self PlayLocalSound( creak );
				}
			}
			// THE STALL: a held arrow, then a whole draw and its slack with the trigger down and no next arrow
			if ( !stall_told && isdefined( self.tod_ab_hold_shots ) && self.tod_ab_hold_shots > 0 &&
			     now > self.tod_ab_press_ms + Int( win * 1000 ) + TOD_AB_STALL_SLACK_MS )
			{
				stall_told = true;
				dev_log( "HOLD_STALL player=" + self GetEntityNumber() + " weapon=" + w.name + " held_arrows=" + self.tod_ab_hold_shots +
				         " held_ms=" + ( now - self.tod_ab_hold_ms ) + " draw_ms=" + Int( win * 1000 ) + " (the engine did not draw again on a held trigger)" );
			}
		}
		pressed = down;
	}
}

// self = player: one line per hold that fired at least one arrow on its own (the chain the user asked for).
function private hold_end( why )
{
	if ( isdefined( self.tod_ab_hold_ms ) && isdefined( self.tod_ab_hold_shots ) && self.tod_ab_hold_shots > 0 )
		dev_log( "HOLD_END player=" + self GetEntityNumber() + " why=" + why + " held_arrows=" + self.tod_ab_hold_shots + " held_ms=" + ( GetTime() - self.tod_ab_hold_ms ) );
	self.tod_ab_hold_ms = undefined;
	self.tod_ab_hold_shots = 0;
}

function private draw_alias( weapon )
{
	return ( IsSubStr( weapon.name, "cc_fire_bow" ) ? TOD_AB_DRAW_FIRE : TOD_AB_DRAW_PLAIN );
}

function private full_alias( weapon )
{
	return ( IsSubStr( weapon.name, "cc_fire_bow" ) ? TOD_AB_FULL_FIRE : TOD_AB_FULL_PLAIN );
}

// self = player. Stops the creak if one is playing; always returns undefined.
function private draw_stop( creak )
{
	if ( isdefined( creak ) ) self StopLocalSound( creak );
	return undefined;
}

// self = player. Seconds the current draw has run (0 when there is none; negative while a held chain's release plays).
function private held_secs()
{
	if ( !isdefined( self.tod_ab_press_ms ) ) return 0;
	return ( GetTime() - self.tod_ab_press_ms ) / 1000.0;
}

// self = player. The draw behind the arrow leaving NOW, decided ONCE per shot: "weapon_fired" and "missile_fire"
// both ask, in either order, and the second gets the first one's answer. Trigger still down = the engine released
// it at full draw (chargeShotFireWhenQueueReachesMax) = 1; up = the player let go, timed by draw_frac.
function private stamp_shot( weapon )
{
	now = GetTime();
	if ( isdefined( self.tod_ab_shot_ms ) && ( now - self.tod_ab_shot_ms ) <= TOD_AB_SAME_SHOT_MS && isdefined( self.tod_ab_charge ) )
		return self.tod_ab_charge;
	held = self AttackButtonPressed();
	frac = shot_frac( held, self held_secs(), self draw_window( weapon ) );
	if ( !held && !isdefined( self.tod_ab_press_ms ) ) frac = 0;   // a release with no draw on record reads as a tap
	self.tod_ab_charge = frac;
	self.tod_ab_charge_ms = now;
	self.tod_ab_shot_ms = now;
	self.tod_ab_shot_auto = held;
	self.tod_ab_draw_ms = Int( self draw_window( weapon ) * 1000 );
	if ( held )
	{
		// the next draw starts when this release ends: a partial release later is measured from THERE, so a held
		// chain can never hand a half draw the full x3
		self.tod_ab_press_ms = now + Int( self release_time( weapon ) * 1000 );
		if ( !isdefined( self.tod_ab_hold_shots ) ) self.tod_ab_hold_shots = 0;
		self.tod_ab_hold_shots++;
	}
	else self.tod_ab_press_ms = undefined;
	return frac;
}

function private mult_for( frac )
{
	return TOD_AB_MIN_MULT + ( TOD_AB_MAX_MULT - TOD_AB_MIN_MULT ) * frac;
}

function fire_watch()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	for ( ;; )
	{
		self waittill( "weapon_fired", w );
		if ( !is_bow( w ) ) continue;
		frac = self stamp_shot( w );
		// the full-power release over the shot, when the draw is long enough to hear it (an automatic cadence would buzz)
		if ( frac >= TOD_AB_FULL && self.tod_ab_draw_ms >= Int( TOD_AB_CUE_MIN * 1000 ) ) self PlayLocalSound( full_alias( w ) );
		chain = ( isdefined( self.tod_ab_hold_shots ) ? self.tod_ab_hold_shots : 0 );
		dev_log( "FIRE player=" + self GetEntityNumber() + " weapon=" + w.name + " auto=" + self.tod_ab_shot_auto + " frac=" + frac + " mult=" + mult_for( frac ) +
		         " draw_ms=" + self.tod_ab_draw_ms + " qd=" + self qd_level() + " held_arrows=" + chain );
	}
}

// A bow's arrow is a MISSILE: it raises stock's "missile_fire" (missile, weapon),
// not "grenade_fire" (build-11 log, 2026-09-26: every hit read lane=player because
// no arrow was ever stamped). Both notifies are listened to, one handler.
function projectile_watch()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	self thread projectile_watch_notify( "missile_fire" );
	self thread projectile_watch_notify( "grenade_fire" );
}

function projectile_watch_notify( note )
{
	self endon( "disconnect" );
	level endon( "end_game" );
	for ( ;; )
	{
		self waittill( note, proj, w );
		if ( !isdefined( proj ) || !is_bow( w ) ) continue;
		proj.tod_ab_charge = self stamp_shot( w );
		dev_log( "PROJ player=" + self GetEntityNumber() + " weapon=" + w.name + " frac=" + proj.tod_ab_charge );
	}
}

// The draw behind a hit: the arrow's own stamp, else the shooter's recent one, else a tap.
function private hit_frac( attacker, inflictor )
{
	if ( isdefined( inflictor ) && isdefined( inflictor.tod_ab_charge ) )
		return inflictor.tod_ab_charge;
	if ( isdefined( attacker ) && isdefined( attacker.tod_ab_charge ) && isdefined( attacker.tod_ab_charge_ms ) &&
	     ( GetTime() - attacker.tod_ab_charge_ms ) <= TOD_AB_STAMP_TTL_MS )
		return attacker.tod_ab_charge;
	return 0;
}

// PUBLIC - _tod_upgrades::upgrade_damage_cb, beside gun_balance_mult.
// THE ARCHER'S SHOT (2026-10-05): a bow arrow = its draw (x1 tap .. x3 full) x QUICK DRAW's per-level term; a
// crossbow bolt = the per-level term alone. 1.0 for anything else (any weapon's melee included).
function charge_mult( attacker, inflictor, weapon, mod )
{
	if ( !is_archer_gun( weapon ) ) return 1.0;
	if ( !isdefined( mod ) || mod == "MOD_MELEE" ) return 1.0;
	qd = quickdraw_mult( attacker, weapon );
	if ( !is_bow( weapon ) ) return qd;
	frac = hit_frac( attacker, inflictor );
	m = mult_for( frac ) * qd;
	lane = ( ( isdefined( inflictor ) && isdefined( inflictor.tod_ab_charge ) ) ? "proj" : "player" );
	dev_log( "HIT weapon=" + weapon.name + " mod=" + mod + " frac=" + frac + " lane=" + lane + " qd=" + qd + " mult=" + m );
	return m;
}
