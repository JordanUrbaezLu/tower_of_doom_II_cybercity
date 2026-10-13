// =============================================================================
// _tod_power_scale.gsc - MAP 1's POWER STRUCTURE AT ONE TENTH (2026-09-25)
//
// User: "I want this map to follow the power structure of map 1 but 10x less.
// HP on players will stay same and enemy damage on player will stay same but dps
// and enemy health will be 10x less" - "Lethal and tactical as well. Its all
// output damage and enemy health basically" - "Its so players can easily
// identify how much damage they do".
//
// So time-to-kill is map 1's exactly; only the NUMBERS shrink: a Saug bullet
// reads 17, not 168. Two halves, both owned by this file:
//
//   ENEMY HEALTH  horde_hp(): map 1's own integer zombie curve (start 135, +90 a
//                 round, +10% a round from round 10 - stock's loop, truncation
//                 and all) divided by 10 and rounded. Stock's loop run directly
//                 on 13.5 / 9 drifts up to 5% low at these small numbers, so
//                 track_rounds() holds level.zombie_health on the exact curve and
//                 _tod_zombie_speed::apply_health_scale writes it onto every fresh
//                 spawn. Elite / boss bases are divided at their own defines
//                 (_tod_bosses, _tod_reaver, _tod_hellhounds,
//                 mechz part pools) - everything else derives from these.
//
//   OUTPUT DAMAGE THE FRONT DOOR. level.callbackActorDamage (the engine's one
//                 entry for every hit on an actor; stock sets it to
//                 zm::actor_damage_override_wrapper inside zm_usermap::main) is
//                 wrapped, and every hit a PLAYER (or a player's partner robot)
//                 lands on an ENEMY is divided by 10 BEFORE anything reads it -
//                 so the upgrade cards, headshots, Panzer armor pools, the
//                 crosshair number and the kill feed all see the new value, and
//                 each hit is divided exactly once. Guns, melee, lethals,
//                 tacticals, perks and the partners' own gunfire all pass here.
//
// NOT DIVIDED - damage already written in the NEW units, because it is computed
// from enemy health (which is already a tenth):
//   - the pass-through marks set by their authors: tod_cleave_hit (cleave splash,
//     class kit C4 / Cluster / Smash, Retriever), tod_wisp_hit (Wisp Tea), and
//     tod_ps_exempt (this file's own neutral mark: Thor's Thunder, PhD);
//   - the Gift of Death (the xmas gun: fractions of max health) and the stock
//     Gravity Spikes lift kills (Warrior's Gravity Smash);
//   - kill-intent hits: damage == health + 1 / 100 / 666 / 1000 / 10000;
//   - hits with no attacker (nuke, landing splashes, Kill sweeps) never reach a
//     scale anyway, and enemy-on-enemy damage is not the player's output.
//
// ROUNDING: whole-number damage keeps its exact average by carrying the fraction
// on the victim (tod_ps_rem): a 16.8 bullet reads 17, 17, 17, 17, 16 ... so the
// number a player sees stays steady and the DPS is exact.
//
// Logs [TOD_POWER] (dev only): INIT (curve + bases), the first scaled and first
// exempt hits of a match, and a per-minute count summary.
// =============================================================================
#using scripts\codescripts\struct;
#insert scripts\shared\shared.gsh;

#namespace tod_power_scale;

#define TOD_PS_DAMAGE            0.1     // the one knob: output damage x this
#define TOD_PS_HEALTH_DIV        10      // enemy health / this (the elite defines carry it baked in)
// map 1's zombie curve, verbatim (tower_of_doom_cybercity _tod_endless_rounds + stock)
#define TOD_PS_MAP1_START        135
#define TOD_PS_MAP1_INCREASE     90
#define TOD_PS_MAP1_EXP_MULT     0.1
#define TOD_PS_MAP1_EXP_ROUND    10
#define TOD_PS_LOG_FIRST         25      // first N scaled / exempt hits logged per match

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_POWER] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// Map 1's zombie health for a round, exactly as its stock loop computed it.
function map1_zombie_hp( round )
{
	h = TOD_PS_MAP1_START;
	for ( i = 2; i <= round; i++ )
	{
		if ( i >= TOD_PS_MAP1_EXP_ROUND )
		{
			old = h;
			h += Int( h * TOD_PS_MAP1_EXP_MULT );
			if ( h < old ) return old;   // stock's own overflow guard
		}
		else
			h = Int( h + TOD_PS_MAP1_INCREASE );
	}
	return h;
}

// THE HORDE CURVE: map 1's number for this round, divided by 10, rounded.
function horde_hp( round )
{
	if ( !isdefined( round ) || round < 1 ) round = 1;
	if ( !isdefined( level.tod_ps_hp_cache ) ) level.tod_ps_hp_cache = [];
	if ( !isdefined( level.tod_ps_hp_cache[ round ] ) )
	{
		hp = Int( map1_zombie_hp( round ) / ( TOD_PS_HEALTH_DIV * 1.0 ) + 0.5 );
		if ( hp < 1 ) hp = 1;
		level.tod_ps_hp_cache[ round ] = hp;
	}
	return level.tod_ps_hp_cache[ round ];
}

function init()
{
	level.tod_ps_scaled = 0;
	level.tod_ps_exempt_count = 0;
	level.tod_ps_logged_scaled = 0;
	level.tod_ps_logged_exempt = 0;
	// THE GATE: stock set this inside zm_usermap::main (zm::init ->
	// init_function_overrides); main() calls us right after, so wrapping it here
	// catches every hit for the rest of the match.
	if ( isdefined( level.callbackActorDamage ) && !IS_TRUE( level.tod_ps_installed ) )
	{
		level.tod_ps_installed = true;
		level.tod_ps_stock_actor_damage = level.callbackActorDamage;
		level.callbackActorDamage = &actor_damage_entry;
	}
	level.zombie_health = horde_hp( 1 );
	level thread track_rounds();
	level thread summary_loop();
	dev_log( "INIT damage=x" + TOD_PS_DAMAGE + " gate=" + isdefined( level.tod_ps_stock_actor_damage )
	       + " horde r1=" + horde_hp( 1 ) + " r5=" + horde_hp( 5 ) + " r10=" + horde_hp( 10 ) + " r20=" + horde_hp( 20 )
	       + " r30=" + horde_hp( 30 ) + " r40=" + horde_hp( 40 ) + " r50=" + horde_hp( 50 ) + " (map 1 r20=" + map1_zombie_hp( 20 ) + ")" );
}

// Stock recomputes level.zombie_health at every round start from the zombie_vars
// (13.5 / 9 now, close but truncated); this holds it on the exact curve for
// everything that reads it (the class kit, PhD, Doppelghast / Mangler health,
// partners, the Panzer's armor ratio, sprinter conversions).
function track_rounds()
{
	level endon( "end_game" );
	last = -1;
	for ( ;; )
	{
		r = level.round_number;
		// THE BATTLE ARENA's static health round (_tod_arena hp_round, docs/210): while a fight runs, every reader of
		// level.zombie_health sees that level's fixed round instead of the frozen tower round.
		if ( isdefined( level.tod_arena_hp_round ) ) r = level.tod_arena_hp_round;
		if ( !isdefined( r ) || r < 1 ) r = 1;
		want = horde_hp( r );
		if ( !isdefined( level.zombie_health ) || level.zombie_health != want )
		{
			level.zombie_health = want;
			if ( r != last ) dev_log( "ROUND " + r + " zombie_health=" + want + " (map 1 " + map1_zombie_hp( r ) + ")" );
		}
		last = r;
		wait 0.05;
	}
}

// ---------------------------------------------------------------------------
// THE FRONT DOOR
// ---------------------------------------------------------------------------
function actor_damage_entry( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, vDamageOrigin, timeOffset, boneIndex, modelIndex, surfaceType, surfaceNormal )
{
	why = self exempt_reason( eAttacker, iDamage, weapon );
	if ( why == "" )
	{
		before = iDamage;
		iDamage = self scaled( iDamage );
		level.tod_ps_scaled++;
		if ( IS_TRUE( level.tod_dev ) && level.tod_ps_logged_scaled < TOD_PS_LOG_FIRST )
		{
			level.tod_ps_logged_scaled++;
			self log_hit( "SCALE", before, iDamage, eAttacker, sMeansOfDeath, weapon );
		}
	}
	else if ( why != "no_attacker" && why != "not_enemy" && why != "not_player" )
	{
		level.tod_ps_exempt_count++;
		if ( IS_TRUE( level.tod_dev ) && level.tod_ps_logged_exempt < TOD_PS_LOG_FIRST )
		{
			level.tod_ps_logged_exempt++;
			self log_hit( "EXEMPT reason=" + why, iDamage, iDamage, eAttacker, sMeansOfDeath, weapon );
		}
	}
	self [[ level.tod_ps_stock_actor_damage ]]( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, vDamageOrigin, timeOffset, boneIndex, modelIndex, surfaceType, surfaceNormal );
}

// "" = divide this hit. Anything else names why it passes untouched.
function exempt_reason( attacker, damage, weapon )   // self = the damaged actor
{
	if ( !isdefined( attacker ) ) return "no_attacker";
	if ( !isdefined( damage ) || damage <= 1 ) return "tiny";   // marker hits (a claw DoDamage( 1 ), C4's 1-damage engine blast)
	team = ( isdefined( level.zombie_team ) ? level.zombie_team : "axis" );
	if ( !isdefined( self.team ) || self.team != team || IS_TRUE( self.tod_is_partner ) ) return "not_enemy";
	if ( !IsPlayer( attacker ) && !( IS_TRUE( attacker.tod_is_partner ) && IsActor( attacker ) ) ) return "not_player";
	if ( IS_TRUE( self.tod_cleave_hit ) || IS_TRUE( self.tod_wisp_hit ) || IS_TRUE( self.tod_ps_exempt ) ) return "mark";
	if ( isdefined( weapon ) && isdefined( weapon.name ) )
	{
		if ( IsSubStr( weapon.name, "xmas_gun" ) ) return "gift_of_death";
		if ( IsSubStr( weapon.name, "wunderstrahl" ) ) return "wunderstrahl";   // docs/219: the beam's ticks are fractions of max health
		if ( weapon.name == "hero_gravityspikes_melee" ) return "gravity_spikes";
	}
	if ( isdefined( self.health ) && damage >= self.health )
	{
		over = damage - self.health;
		if ( over == 1 || over == 100 || over == 666 || over == 1000 || over == 10000 ) return "kill_intent";
	}
	return "";
}

// x0.1 with the fraction carried on the victim, so the average is exact and a
// steady weapon shows a steady number.
function scaled( damage )   // self = the damaged actor
{
	if ( !isdefined( self.tod_ps_rem ) ) self.tod_ps_rem = 0.5;
	v = damage * TOD_PS_DAMAGE + self.tod_ps_rem;
	n = Int( v );
	self.tod_ps_rem = v - n;
	return n;
}

function log_hit( what, before, after, attacker, mod, weapon )   // self = the damaged actor
{
	kind = "zombie";
	if ( isdefined( self.tod_boss_kind ) ) kind = self.tod_boss_kind;
	who = ( IsPlayer( attacker ) ? "player" + attacker GetEntityNumber() : "partner" );
	wname = ( ( isdefined( weapon ) && isdefined( weapon.name ) ) ? weapon.name : "none" );
	dev_log( what + " victim=" + self GetEntityNumber() + " kind=" + kind + " by=" + who + " weapon=" + wname
	       + " mod=" + mod + " in=" + before + " out=" + after + " health=" + self.health + " round=" + level.round_number );
}

function summary_loop()
{
	level endon( "end_game" );
	for ( ;; )
	{
		wait 60;
		if ( level.tod_ps_scaled > 0 || level.tod_ps_exempt_count > 0 )
			dev_log( "SUMMARY scaled=" + level.tod_ps_scaled + " exempt=" + level.tod_ps_exempt_count + " zombie_health=" + level.zombie_health + " round=" + level.round_number );
	}
}
