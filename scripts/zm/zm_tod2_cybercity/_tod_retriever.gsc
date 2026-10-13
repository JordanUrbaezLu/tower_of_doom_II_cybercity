// BO2 MOTD Retriever port. Reference: retained _zm_weap_tomahawk.gsc.
// Native grenade physics/animations until impact or 0.5 s; then BO2's mover.
// State is owned by Archer's level watchdog, including disconnect cleanup.
#using scripts\shared\util_shared;
#using scripts\zm\_zm_utility;
#using scripts\zm\_zm_score;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;
#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;
#using scripts\zm\zm_tod2_cybercity\_tod_ability_fx;   // docs/203: the ability feedback (both views)
#insert scripts\shared\shared.gsh;
#precache( "weapon", "tod_archer_retriever" );
#precache( "fx", "tod/archer/fx_tod_archer_charge" );
#precache( "fx", "tod/archer/fx_tod_archer_trail_charged" );
#precache( "fx", "tod/archer/fx_tod_ret_fire" );
#precache( "rumble", "reload_small" );
#namespace tod_retriever;

// THE RETRIEVER CARD (2026-09-26, user: "in real gameplay this is coming
// through as an upgrade ... the more upgrades you get the more you can throw
// and the more damage it does"). Domain "retriever" (id 57, max 8, Archer).
// Lv0 = no lethal at all; a tod_dev build treats Lv0 as Lv1 so the test
// build still spawns with it. STORED THROWS refill on their own TOD_RET_REFILL
// timer each. DAMAGE rides the grapple's curve, ln( 1 + lvl ) / ln( 9 ),
// rebased so Lv1 is the old x1.0 and Lv8 is x3.0 (table in damage_mult). The
// Lua row 57 mirrors every number here - change both.
//
// MANY AXES IN THE AIR (2026-09-26, user after the build-8 test: "I should be
// able to throw more than one at a time ... it shouldn't limit me to one
// only"): every throw is its own struct in s.axes (flight -> mover -> strike ->
// ricochets -> return -> caught), stepped side by side; a stored throw goes
// the moment you have one, and the refill clock runs whether or not an axe is
// out. Lv1 (one stored throw) still plays one at a time by construction.
// THE FIRE (same request: "should have a fire effect on it as it's floating
// through the air, killing things"): the hellhound's fire trail
// (TOD_RET_FIRE_FX) rides every axe from the hand to the catch, over the
// ember trail the art pass gave it. MAGNETISM (same request: "not magnetizing
// towards zombies like I think it should"): the landing no longer has to be
// within 70 u of a zombie to strike - the nearest candidate inside
// TOD_RET_STRIKE_R is flown to (log MAGNET), candidates and ricochets reach
// TOD_RET_MARK_R, one more ricochet, and the way home checks a wider ring.
#define TOD_RET_REFILL          5     // seconds per stored throw (was the fixed catch cooldown)
#define TOD_RET_CHARGES_LV2     3     // 2 stored throws from this level
#define TOD_RET_CHARGES_LV3     6     // 3 stored throws from this level
#define TOD_RET_CHARGES_LV4     9     // 4 stored throws at Lv9 (2026-09-27: 9 levels, big steps at 3 / 6 / 9)
#define TOD_RET_MAX_LV          9
#define TOD_RET_MARK_R          420   // zombies this close to the landing are candidates + ricochet targets (was 200 / 300)
#define TOD_RET_STRIKE_R        240   // the nearest candidate this close is flown to and hit (was: within 70 of the landing or nothing)
#define TOD_RET_IMMEDIATE_R     70    // this close = hit where it lands, no flight (BO2)
#define TOD_RET_CHAIN_MAX       5     // ricochets after the first hit (was 4)
#define TOD_RET_RETURN_R        180   // a zombie this close to the axe on the way home is hit (was 100)
// THE FLAME IS THE FIRE STAFF'S BOLT TRAIL (build-11 test, 2026-09-26, user: "it
// has no flame to it. It just has the regular model"): the hellhound trail
// `zombie/fx_dog_fire_trail_zmb` exists in the mod tools ONLY AS A STUB (its .efx
// is the gfx_debug_missing_fx placeholder; the real one lives in the base
// fastfile), so it linked clean and drew nothing. This one is a real source.
// ... at three quarters (user on build 14: "too much flames ... 25% less ... hard to see the
// tomahawk"): tools/archer_assets/make_ret_fire_fx.py scales its size / alpha / light graphs.
#define TOD_RET_FIRE_FX         "tod/archer/fx_tod_ret_fire"
// HOP TIME zombie to zombie (user on build 14: "25% slower"): 0.3 s -> 0.4 s per strike.
#define TOD_RET_HOP_SECS        0.4

function init()
{
	level.tod_retriever_weapon = GetWeapon( "tod_archer_retriever" );
	zm_utility::register_lethal_grenade_for_level( "tod_archer_retriever" );
	level.tod_retriever_charge_fx = "tod/archer/fx_tod_archer_charge";
}

// self = player. The card level, with the dev floor.
function card_level()
{
	lvl = tod_upgrades::get_level( self, "retriever" );
	if ( lvl < 1 && IS_TRUE( level.tod_dev ) ) lvl = 1;
	if ( lvl > TOD_RET_MAX_LV ) lvl = TOD_RET_MAX_LV;
	return lvl;
}

function charges_max( lvl )
{
	if ( lvl <= 0 ) return 0;
	if ( lvl >= TOD_RET_CHARGES_LV4 ) return 4;
	if ( lvl >= TOD_RET_CHARGES_LV3 ) return 3;
	if ( lvl >= TOD_RET_CHARGES_LV2 ) return 2;
	return 1;
}

// 1 + 2 x ( c - c1 ) / ( 1 - c1 ), c = ln( 1 + lvl ) / ln( 10 ), c1 = c at Lv1 (9 levels since 2026-09-27).
function damage_mult( lvl )
{
	if ( !isdefined( lvl ) || lvl <= 1 ) return 1.0;
	if ( lvl >= TOD_RET_MAX_LV ) return 3.0;
	m = array( 1.0, 1.0, 1.5, 1.86, 2.14, 2.37, 2.56, 2.72, 2.87, 3.0 );
	return m[ lvl ];
}

// Throwable right now: owned and a stored throw. Axes already out do not block.
function ammo_now( s )
{
	if ( !IS_TRUE( s.ret_on ) ) return 0;
	if ( !isdefined( s.axe_charges ) || s.axe_charges <= 0 ) return 0;
	return 1;
}

function in_flight( s )
{
	if ( !isdefined( s.axes ) ) return 0;
	return s.axes.size;
}

function listen()
{
	self notify( "tod_retriever_respawn" );
	self thread listen_charge();
	self thread listen_throw();
}

function equip( s )
{
	s.old_lethal = self zm_utility::get_player_lethal_grenade();
	if ( s.old_lethal == level.tod_retriever_weapon ) s.old_lethal = level.zombie_lethal_grenade_player_init;
	if ( !isdefined( s.old_lethal ) ) s.old_lethal = level.weaponNone;
	s.old_tactical = self zm_utility::get_player_tactical_grenade();
	if ( s.old_lethal != level.weaponNone && s.old_lethal != level.tod_retriever_weapon ) self TakeWeapon( s.old_lethal );
	if ( s.old_tactical != level.weaponNone ) self TakeWeapon( s.old_tactical );
	self zm_utility::set_player_tactical_grenade( level.weaponNone );
	self zm_utility::set_player_lethal_grenade( level.weaponNone );
	s.axes = [];
	s.axe_seq = 0;
	s.axe_busy = false;   // = an axe is out; read by the HUD only, never a throw gate any more
	s.ret_on = false;
	s.axe_charges = 0;
	s.axe_cd = 0;
	self EnableOffhandWeapons();
	lvl = self card_level();
	log( "EQUIP owner=" + self GetEntityNumber() + " card_lv=" + lvl + " (Lv0 = no lethal until the card)" );
	if ( lvl > 0 ) self give( s );
}

// The card arrived (or the Archer armed with it): hand over the axe, full.
function give( s )
{
	lvl = self card_level();
	s.ret_on = true;
	s.axe_charges = charges_max( lvl );
	s.axe_cd = 0;
	s.flourish_pending = true;
	self GiveWeapon( level.tod_retriever_weapon );
	s.ammo_shown = ammo_now( s );
	self SetWeaponAmmoClip( level.tod_retriever_weapon, s.ammo_shown );
	self SwitchToOffhand( level.tod_retriever_weapon );
	self zm_utility::set_player_lethal_grenade( level.tod_retriever_weapon );
	log( "GIVE owner=" + self GetEntityNumber() + " card_lv=" + lvl + " charges=" + s.axe_charges + " dmg_mult=" + damage_mult( lvl ) );
}

// self = player; every unblocked Archer tick. Grants the axe when the card
// lands, refills stored throws (whether or not axes are out), and keeps the
// clip honest (change-gated).
function tick( s, dt )
{
	lvl = self card_level();
	if ( !IS_TRUE( s.ret_on ) )
	{
		if ( lvl > 0 ) self give( s );
		return;
	}
	cap = charges_max( lvl );
	if ( IS_TRUE( level.tod_dev_unlimited_offhand ) ) { s.axe_charges = cap; s.axe_cd = 0; }   // dev test: no refill wait
	if ( s.axe_charges > cap ) s.axe_charges = cap;
	if ( s.axe_charges < cap )
	{
		if ( s.axe_cd <= 0 ) s.axe_cd = TOD_RET_REFILL;
		s.axe_cd -= dt;
		if ( s.axe_cd <= 0 )
		{
			s.axe_cd = 0;
			s.axe_charges++;
			tod_perk_scatter::play_sound_at_origin( self.origin, "tod_archer_axe_ready", 2 );
			log( "REFILL owner=" + self GetEntityNumber() + " charges=" + s.axe_charges + "/" + cap + " card_lv=" + lvl + " in_flight=" + in_flight( s ) );
		}
	}
	else s.axe_cd = 0;
	ammo = ammo_now( s );
	if ( !isdefined( s.ammo_shown ) || s.ammo_shown != ammo )
	{
		s.ammo_shown = ammo;
		self SetWeaponAmmoClip( level.tod_retriever_weapon, ammo );
	}
}

function listen_charge()
{
	self endon( "disconnect" );
	self endon( "tod_retriever_respawn" );
	for ( ;; )
	{
		self waittill( "grenade_pullback", weapon );
		if ( weapon != level.tod_retriever_weapon ) continue;
		s = self.tod_archer_state;
		if ( !isdefined( s ) || !s.armed ) continue;
		s.charge_start = GetTime();
		s.charge_stage = 0;
		log( "PULLBACK owner=" + self GetEntityNumber() );
	}
}

function reconcile( s )
{
	// Stock spawn/restore paths may run after the class loadout. Repair only
	// on a real inventory/slot mismatch, retaining the throw and cooldown.
	if ( !IS_TRUE( s.ret_on ) )
	{
		// No card yet: the Archer carries no lethal. Strip what stock hands back.
		other = self zm_utility::get_player_lethal_grenade();
		if ( other != level.weaponNone )
		{
			self TakeWeapon( other ); self zm_utility::set_player_lethal_grenade( level.weaponNone );
			log( "LETHAL_STRIP owner=" + self GetEntityNumber() + " weapon=" + other.name + " (no Retriever card)" );
		}
	}
	else if ( !self HasWeapon( level.tod_retriever_weapon ) || self zm_utility::get_player_lethal_grenade() != level.tod_retriever_weapon )
	{
		other = self zm_utility::get_player_lethal_grenade();
		if ( other != level.weaponNone && other != level.tod_retriever_weapon ) self TakeWeapon( other );
		if ( !self HasWeapon( level.tod_retriever_weapon ) ) self GiveWeapon( level.tod_retriever_weapon );
		ammo = ammo_now( s );
		s.ammo_shown = ammo;
		self SetWeaponAmmoClip( level.tod_retriever_weapon, ammo );
		self SwitchToOffhand( level.tod_retriever_weapon );
		self zm_utility::set_player_lethal_grenade( level.tod_retriever_weapon );
		log( "INVENTORY_REPAIR owner=" + self GetEntityNumber() + " ammo=" + ammo );
	}
	other = self zm_utility::get_player_tactical_grenade();
	if ( other != level.weaponNone )
	{
		self TakeWeapon( other ); self zm_utility::set_player_tactical_grenade( level.weaponNone );
		log( "TACTICAL_REPAIR owner=" + self GetEntityNumber() );
	}
}

// After a world pause: re-issue every in-progress strike's MoveTo.
function resume( s )
{
	if ( !isdefined( s.axes ) ) return;
	foreach ( a in s.axes )
	{
		if ( !isdefined( a.axe ) || a.move_left <= 0 ) continue;
		if ( a.phase != "attack" && a.phase != "return_attack" ) continue;
		if ( !isdefined( a.target ) || !IsAlive( a.target ) ) continue;
		duration = a.move_left;
		if ( duration < 0.05 ) duration = 0.05;
		a.axe MoveTo( a.target GetTagOrigin( strike_tag( a.target ) ), duration );
	}
}

function strike_tag( z )
{
	if ( IS_TRUE( z.isdog ) ) return "j_spine1";
	return "j_head";
}

function listen_throw()
{
	self endon( "disconnect" );
	self endon( "tod_retriever_respawn" );
	for ( ;; )
	{
		self waittill( "grenade_fire", grenade, weapon );
		if ( weapon != level.tod_retriever_weapon || !isdefined( grenade ) ) continue;
		s = self.tod_archer_state;
		if ( !isdefined( s ) || !s.armed || ammo_now( s ) == 0 )
		{
			grenade Delete();
			continue;
		}
		s.charge_ms = 0;
		if ( isdefined( s.charge_start ) ) s.charge_ms = GetTime() - s.charge_start;
		s.charge_start = undefined;
		s.axe_charges--;
		s.ammo_shown = ammo_now( s );
		self SetWeaponAmmoClip( level.tod_retriever_weapon, s.ammo_shown );
		if ( !isdefined( s.axes ) ) s.axes = [];
		if ( !isdefined( s.axe_seq ) ) s.axe_seq = 0;
		a = SpawnStruct();
		a.id = s.axe_seq;
		s.axe_seq++;
		a.power = charge_power( s.charge_ms );
		a.mult = damage_mult( self card_level() );
		a.phase = "flight";
		a.flight_left = 0.5;
		a.projectile = grenade;
		a.projectile_origin = grenade.origin;
		a.impact = false;
		a.hits = [];
		a.marked = [];
		a.chain = [];
		a.powerups = [];
		a.move_left = 0;
		a.spin_left = 0;
		a.low_kill = 1;
		a.return_checks = 0;
		a.done = false;
		s.axes[ s.axes.size ] = a;
		s.axe_busy = true;
		grenade.use_grenade_special_bookmark = 1;
		grenade.grenade_multiattack_bookmark_count = 1;
		grenade.owner = self;
		PlayFXOnTag( "tod/archer/fx_tod_archer_trail_charged", grenade, "tag_origin" );
		PlayFXOnTag( TOD_RET_FIRE_FX, grenade, "tag_origin" );
		grenade thread impact_watch( a );
		log( "THROW owner=" + self GetEntityNumber() + " axe=" + a.id + " charge_ms=" + s.charge_ms + " power=" + a.power + " mult=" + a.mult + " charges_left=" + s.axe_charges + " in_flight=" + s.axes.size + " origin=" + grenade.origin );
	}
}

function impact_watch( a )
{
	self endon( "tod_retriever_cancel" );
	self waittill( "death" );
	a.projectile_origin = self.origin;
	a.impact = true;
}

function charge_power( ms )
{
	// Preserve BO2's actual comparisons, including exact-boundary behavior.
	if ( ms > 1000 && ms < 2000 ) return 1.5;
	if ( ms > 2000 ) return 2;
	return 1;
}

// self = player; every unblocked Archer tick. The charge-up, the clip guard,
// then every axe in the air.
function step( s, dt )
{
	if ( isdefined( s.charge_start ) )
	{
		if ( !self IsThrowingGrenade() && GetTime() - s.charge_start > 100 )
		{
			log( "CHARGE_CANCEL owner=" + self GetEntityNumber() );
			s.charge_start = undefined;
		}
		else if ( s.charge_stage < 2 && GetTime() - s.charge_start >= ( s.charge_stage + 1 ) * 1000 )
		{
			s.charge_stage++;
			tod_ability_fx::ring_at( self, level.tod_retriever_charge_fx, 0.6 );   // docs/203 s4: a looping ring on a host that dies
			self PlayRumbleOnEntity( "reload_small" );
			log( "CHARGE owner=" + self GetEntityNumber() + " stage=" + s.charge_stage );
		}
	}
	// A max-ammo event must not hand out a throw the card has not stored.
	if ( ammo_now( s ) == 0 ) self SetWeaponAmmoClip( level.tod_retriever_weapon, 0 );
	if ( !isdefined( s.axes ) || s.axes.size == 0 ) { s.axe_busy = false; return; }
	keep = [];
	foreach ( a in s.axes )
	{
		if ( !IS_TRUE( a.done ) ) self axe_step( s, a, dt );
		if ( !IS_TRUE( a.done ) ) keep[ keep.size ] = a;
	}
	s.axes = keep;
	s.axe_busy = ( s.axes.size > 0 );
}

// One axe, one tick.
function axe_step( s, a, dt )
{
	if ( a.phase == "flight" )
	{
		if ( isdefined( a.projectile ) && !a.impact ) a.projectile_origin = a.projectile.origin;
		a.flight_left -= dt;
		if ( a.impact || !isdefined( a.projectile ) || a.flight_left <= 0 ) self impact( s, a );
		return;
	}
	if ( !isdefined( a.axe ) ) { self finish_axe( s, a, "missing_mover" ); return; }
	if ( !isdefined( a.axe_audio ) )
	{
		a.axe_audio = Spawn( "script_origin", a.axe.origin );
		if ( isdefined( a.axe_audio ) ) { a.axe_audio LinkTo( a.axe ); a.axe_audio PlayLoopSound( "tod_archer_axe_spin" ); }   // the spin rides WITH the axe (2026-09-26)
	}
	a.spin_left -= dt;
	if ( a.spin_left <= 0 ) { a.axe RotatePitch( 90, 0.2 ); a.spin_left = 0.15; }
	if ( isdefined( a.axe_audio ) ) a.axe_audio.origin = a.axe.origin;
	if ( a.move_left > 0 )
	{
		a.move_left -= dt;
		if ( a.move_left > 0 ) return;
		if ( a.phase == "attack" )
		{
			self hit( s, a, a.target );
			// BO2 creates a new mover for the ricochet, resetting its damage counter.
			a.low_kill = 1;
			a.phase = "chain"; a.move_left = 0.2;
			return;
		}
		if ( a.phase == "return_attack" ) { self hit( s, a, a.target ); a.phase = "return"; a.move_left = 0.1; return; }
	}
	if ( a.phase == "chain" )
	{
		if ( a.chain_index >= a.chain_limit ) { self returning( s, a, a.chain_limit ); return; }
		z = a.chain[ a.chain.size - 1 - a.chain_index ];
		a.chain_index++;
		if ( eligible( a, z ) ) self attack( a, z, false );
		else a.move_left = 0.2;
		return;
	}
	if ( a.phase == "return" )
	{
		if ( Distance2DSquared( a.axe.origin, self GetEye() ) <= 4096 ) { self finish_axe( s, a, "caught" ); return; }
		a.axe MoveTo( self GetEye(), 0.25 );
		if ( a.return_checks < 5 )
		{
			nearby = util::get_array_of_closest( a.axe.origin, GetAITeamArray( level.zombie_team ), undefined, undefined, TOD_RET_RETURN_R );
			a.return_checks++;
			if ( isdefined( nearby[0] ) && eligible( a, nearby[0] ) ) { self attack( a, nearby[0], true ); return; }
		}
		a.move_left = 0.1;
	}
}

// The native grenade is done (hit something or 0.5 s): the mover takes over
// where it is, and the strike is chosen.
function impact( s, a )
{
	if ( isdefined( a.projectile ) ) { a.projectile notify( "tod_retriever_cancel" ); a.projectile Delete(); }
	a.projectile = undefined;
	a.axe = Spawn( "script_model", a.projectile_origin );
	if ( !isdefined( a.axe ) ) { self finish_axe( s, a, "spawn_failed" ); return; }
	a.axe SetModel( "tod_archer_retriever_world" ); a.axe NotSolid();
	PlayFXOnTag( level.tod_archer_trail_fx, a.axe, "tag_knife_fx" );
	PlayFXOnTag( TOD_RET_FIRE_FX, a.axe, "tag_knife_fx" );
	if ( a.power > 1 ) PlayFXOnTag( "tod/archer/fx_tod_archer_trail_charged", a.axe, "tag_knife_fx" );
	a.axe_audio = Spawn( "script_origin", a.axe.origin );
	if ( isdefined( a.axe_audio ) ) { a.axe_audio LinkTo( a.axe ); a.axe_audio PlayLoopSound( "tod_archer_axe_spin" ); }   // the spin rides WITH the axe (2026-09-26)
	a.spin_left = 0; a.move_left = 0; a.low_kill = 1;
	a.marked = util::get_array_of_closest( a.axe.origin, GetAITeamArray( level.zombie_team ), undefined, undefined, TOD_RET_MARK_R );
	if ( !isdefined( a.marked ) ) a.marked = [];
	if ( isdefined( level.active_powerups ) )
	{
		a.powerups = util::get_array_of_closest( a.axe.origin, level.active_powerups, undefined, undefined, 200 );
		if ( !isdefined( a.powerups ) ) a.powerups = [];
	}
	log( "IMPACT owner=" + self GetEntityNumber() + " axe=" + a.id + " origin=" + a.axe.origin + " candidates=" + a.marked.size + " powerups=" + a.powerups.size );
	if ( a.powerups.size > 0 )
	{
		foreach ( powerup in a.powerups )
		{
			if ( !isdefined( powerup ) ) continue;
			powerup.origin = a.axe.origin; powerup LinkTo( a.axe );
		}
		self returning( s, a, 0 ); return;
	}
	// The ricochet list is the candidate ring, nearest last (walked from the end).
	a.chain = a.marked;
	a.chain_limit = a.chain.size;
	if ( a.chain_limit > TOD_RET_CHAIN_MAX ) a.chain_limit = TOD_RET_CHAIN_MAX;
	a.chain_index = 0;
	first = a.marked[0];
	if ( isdefined( first ) && IsAlive( first ) )
	{
		d = Distance( a.axe.origin, first.origin );
		if ( d <= TOD_RET_IMMEDIATE_R )
		{
			self hit( s, a, first );
			a.low_kill = 1;
			a.phase = "chain";
			return;
		}
		if ( d <= TOD_RET_STRIKE_R )
		{
			// THE MAGNET: it landed near one - fly to it and hit, then ricochet.
			log( "MAGNET owner=" + self GetEntityNumber() + " axe=" + a.id + " target=" + first GetEntityNumber() + " dist=" + int( d ) + " reach=" + TOD_RET_STRIKE_R );
			self attack( a, first, false );
			return;
		}
	}
	self returning( s, a, 0 );
}

function eligible( a, z )
{
	if ( !isdefined( z ) || !IsAlive( z ) ) return false;
	found = false;
	foreach ( marked in a.marked ) if ( isdefined( marked ) && marked == z ) found = true;
	if ( !found ) return false;
	foreach ( hit in a.hits ) if ( isdefined( hit ) && hit == z ) return false;
	return true;
}

function attack( a, z, returning )
{
	a.target = z;
	a.axe MoveTo( z GetTagOrigin( strike_tag( z ) ), TOD_RET_HOP_SECS );
	a.move_left = TOD_RET_HOP_SECS;
	a.phase = "attack";
	if ( returning ) a.phase = "return_attack";
}

function damage( health, power, round, counter, mult )
{
	if ( power > 2 ) return health + 1;
	if ( round >= 10 && round < 13 && counter <= 3 ) return health + 1;
	if ( round >= 13 && round < 15 && counter <= 2 ) return health + 1;
	return 100 * power * mult;   // x damage_mult( card level ), 2026-09-26. map 1: 1000 (power scale / 10, 2026-09-25; the cleave mark passes it through untouched)
}

function hit( s, a, z )
{
	if ( !isdefined( z ) || !IsAlive( z ) ) return;
	mult = 1.0;
	if ( isdefined( a.mult ) ) mult = a.mult;
	dmg = damage( z.health, a.power, level.round_number, a.low_kill, mult );
	if ( ( level.round_number >= 10 && level.round_number < 13 && a.low_kill <= 3 ) || ( level.round_number >= 13 && level.round_number < 15 && a.low_kill <= 2 ) ) a.low_kill++;
	a.hits[ a.hits.size ] = z;
	log( "HIT owner=" + self GetEntityNumber() + " axe=" + a.id + " target=" + z GetEntityNumber() + " damage=" + dmg + " power=" + a.power + " mult=" + mult + " round=" + level.round_number + " hit=" + a.hits.size );
	tod_ability_fx::axe_hit( z );   // docs/206: the hit drawn on the zombie by the client (a bare server PlayFX drew nothing)
	tod_perk_scatter::play_sound_at_origin( z.origin, "tod_archer_axe_hit", 2 );
	z.tod_cleave_hit = true;
	z DoDamage( int( dmg ), a.axe.origin, self, a.axe, "none", "MOD_GRENADE", 0, level.tod_retriever_weapon );
	if ( isdefined( z ) ) z.tod_cleave_hit = undefined;
	self zm_score::add_to_player_score( 10 );
}

function returning( s, a, checks )
{
	a.phase = "return"; a.return_checks = checks; a.move_left = 0;
	tod_perk_scatter::play_sound_at_origin( a.axe.origin, "tod_archer_axe_return", 2 );
	log( "RETURN owner=" + self GetEntityNumber() + " axe=" + a.id + " hits=" + a.hits.size + " checks=" + checks );
}

// Every axe in the air ends now (the Archer's end_axe: death, class change, ...).
function finish( s, reason )
{
	s.charge_start = undefined;
	if ( !isdefined( s.axes ) ) return;
	foreach ( a in s.axes ) self finish_axe( s, a, reason );
	s.axes = [];
	s.axe_busy = false;
}

function finish_axe( s, a, reason )
{
	if ( IS_TRUE( a.done ) ) return;
	if ( reason == "caught" )
	{
		foreach ( powerup in a.powerups )
		{
			if ( !isdefined( powerup ) ) continue;
			powerup Unlink(); powerup.origin = self.origin;
		}
		a.powerups = [];
		tod_perk_scatter::play_sound_at_origin( self.origin, "tod_archer_axe_catch", 2 );
	}
	destroy_axe( a );
	a.done = true;
	log( "END owner=" + self GetEntityNumber() + " axe=" + a.id + " reason=" + reason + " hits=" + a.hits.size + " charges=" + s.axe_charges + " in_flight=" + ( in_flight( s ) - 1 ) );
}

// Everything, no sounds (the Archer's delete_axe: disconnect, cleanup).
function destroy( s )
{
	s.axe_busy = false; s.charge_start = undefined;
	if ( isdefined( s.axes ) ) foreach ( a in s.axes ) destroy_axe( a );
	s.axes = [];
}

function destroy_axe( a )
{
	if ( isdefined( a.powerups ) ) foreach ( powerup in a.powerups ) if ( isdefined( powerup ) ) powerup Unlink();
	a.powerups = [];
	if ( isdefined( a.projectile ) ) { a.projectile notify( "tod_retriever_cancel" ); a.projectile Delete(); }
	a.projectile = undefined;
	if ( isdefined( a.axe_audio ) )
	{
		a.axe_audio StopLoopSound( 0 ); a.axe_audio StopSounds(); a.axe_audio Delete(); a.axe_audio = undefined;
	}
	if ( isdefined( a.axe ) )
	{
		// Server tag FX belong to their entity. Delete the host as stock BO3
		// does in _zm_ai_raps::cleanup_meteor_fx; no server StopFXOnTag API.
		a.axe Delete(); a.axe = undefined;
	}
}

function log( message )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_RETRIEVER] ms=" + GetTime() + " " + message;
	/#
	PrintLn( line );
	#/
}
