// =============================================================================
// _tod_necro_skull.gsc — THE NECROMANCER'S SKULL (2026-09-26, user: "remove the
// skirmisher and add in a necromancer ... the skull ... he will be holding and
// using and kind of sucks in the zombies' soul and kills them").
//
// The weapon is the Skull of Nan Sapwe (Zetsubou No Shima), re-authored as a
// PRIMARY by tools/necromancer/make_skull_gdt.py (tod_necro_skull_b / _up_b).
// The asset does no damage of its own; everything is here. The logic is map 1's
// play-proven HB21 port (_zm_weap_keeper_skull.gsc), rebuilt for a class gun:
//
//   HOLD FIRE  = THE SOUL BEAM, A HEALTH DRAIN (user 2026-09-26: "the skull move
//                should drain health and not really stop the zombies in place ...
//                you should see kind of some soul aura going from their AI body to
//                your player"). Everything in front of you (cone + line of sight,
//                TOD_NECRO_RANGE), elites included, is drained for as long as the
//                beam holds it. The class tier's DPS (beam_dps: the map's mean gun
//                DPS for that tier, TIER_SUSTAINED in gen_tod_twins.js) is the beam's
//                TOTAL on one soul; each extra soul held adds TOD_NECRO_CROWD of it,
//                split evenly (crowd_share - user 2026-09-26 "a little bit too much
//                damage": four souls took a full gun each until then). Nobody is held or
//                lifted any more - they keep walking at you. Each caught actor wears
//                actor state 2, and the CLIENT flies soul wisps from its chest to
//                you (_tod_necro_skull.csc soul_stream). A plain zombie the drain
//                finishes has its soul torn out (state 1) and refunds the meter.
//                (Until 2026-09-26 the beam played stock's death-ray scene - the
//                zombie lifted and froze - and killed it whole after 1 s. That lift
//                is the SUMMON's now.)
//   HOLD AIM   = SUMMON HELPERS (_tod_necro_summon.gsc): aim at a zombie, the
//                skull's torch lifts it (the death-ray scene) and binds it, then it
//                turns into your helper - tier 1 a thrall (that zombie, turned),
//                tier 2 a soul hound, tier 3 the Mangler (it rises from that
//                zombie's body). The meter pays per helper.
//   THE SOUL METER is the clip (100). The beam spends TOD_NECRO_BEAM_COST/s, a
//   helper costs its summon price, every soul taken refunds TOD_NECRO_SOUL_REFUND,
//   and it refills TOD_NECRO_REGEN/s after TOD_NECRO_REGEN_DELAY idle. Empty =
//   the beam cuts out until TOD_NECRO_RESTART is back. There is no ammo to buy.
//   PaP (_up) = faster drain, more targets, longer reach.
//
// WIDOW'S WINE = BURNED OUT (user, same day: "when it gets Widow's Wine ... it'll
// actually activate the burned out gobblegum functionality ... because this
// class doesn't have ... any grenades"). The Necromancer carries no grenades
// (_tod_class_kit TOD_KIT_NECRO), so stock Widow's contact web can never fire
// for it. Instead, with the perk: when a zombie MELEES the Necromancer, every
// zombie within TOD_NECRO_BURN_RADIUS bursts into flame and dies — stock's
// Burned Out gobblegum and its FX (fx_bgb_burned_out_1p/3p/_fire_torso). Elites
// are skipped, the way a Nuke skips them.
// CHARGES ARE WIDOW'S GRENADES (user 2026-09-26: "it should just use the Widow's
// Wine trigger ... you can hold four at once ... if you have no more, it doesn't
// trigger. If you grab a spider drop, it replenishes one ... I don't want a max").
// No per-round cap: a script count that follows the stock widow's grenade stack
// source for source (_zm_perk_widows_wine / _zm_powerup_ww_grenade / _zm):
//   gain the perk            -> full (TOD_NECRO_BURN_MAX, the stack of 4)
//   a zombie melee hit       -> spends 1 (none left = nothing happens)
//   a spider drop (ww_grenade powerup) -> +1, capped at the stack
//   Max Ammo                 -> full
//   round start              -> stock's award_grenades_for_survivors rule
//                               (0 -> 2, 1 -> 3, 2+ -> 4)
//   lose the perk            -> 0
// The only other rule: a hit inside TOD_NECRO_BURN_GAP_MS of a burst spends
// nothing (the burst already cleared the radius; a swarm would waste the stack). The 720 radius is stock's figure as recalled from the decompiled
// gum (the gum's script is not in the Mod Tools) — the one knob to check.
//
// CLIENTFIELDS (lockstep with _tod_necro_skull.csc, same names, types, bits):
//   allplayers "tod_necro_fx"   3 bits int: 0 off / 1 beam start / 2 beam loop /
//                                            3 summon channel start / 4 channel loop (the torch light)
//   allplayers "tod_necro_burn" 1 bit counter: the Burned Out burst (1p + 3p)
//   actor      "tod_necro_soul" 3 bits int: 0 off / 1 soul torn out / 2 drained (the
//                                            soul stream to the beam) / 3 being bound
//                                            (the summon lift) / 4 burned out / 5 thrall /
//                                            6 soul hound / 7 Mangler (5-7 = helper auras,
//                                            1, 3 and 5-7 set by _tod_necro_summon)
//   ONE actor field for all five states on purpose: the actor pool is the tight
//   one (memory actor-clientfield-bit-budget); map 1 spent three fields here.
//   allplayers had one 1-bit registration before this.
//
// LOGS: [TOD_NECRO] under tod_dev — INIT, BEAM on/off (targets, meter), SOUL
// (kill, drain time), ELITE_DRAIN (damage), SUMMON on/off (the channel), METER_EMPTY,
// BURN (charges, killed) and BURN_DENY (why).
// =============================================================================

#using scripts\codescripts\struct;
#using scripts\shared\ai\systems\gib;
#using scripts\shared\ai\zombie_utility;
#using scripts\shared\animation_shared;
#using scripts\shared\array_shared;
#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\math_shared;
#using scripts\shared\scene_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_necro_summon;
#using scripts\zm\zm_tod2_cybercity\_tod_ability_fx;   // 2026-10-05: the empty meter's refused cue (a leaf module)

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#define TOD_NECRO_STEM            "tod_necro_skull"
#define TOD_NECRO_CLASS           "necromancer"
#define TOD_NECRO_TICK            0.05

// ---- the beam ---------------------------------------------------------------
#define TOD_NECRO_RANGE           500      // map 1 / stock skull reach (units)
#define TOD_NECRO_RANGE_UP        650
#define TOD_NECRO_DOT             0.85     // acquire cone (map 1's is_player_looking_at 0.85)
#define TOD_NECRO_HOLD_DOT        0.75     // a caught zombie stays caught a little wider
#define TOD_NECRO_MAX_TARGETS     2        // souls drained at once (4 until 2026-09-27; SOUL BEAM adds one at Lv3 / Lv6 / Lv9 -> 5)
#define TOD_NECRO_MAX_TARGETS_UP  3        // packed (6 until 2026-09-27 -> 6 at Lv9)
// THE SOUL-RIP MINIMUM (2026-09-27, user: the beam "kills things instantly, which I don't
// think it should"; the 00:09 log: all 27 souls taken on the FIRST tick, held_ms=0). An
// ordinary zombie's soul can only be torn out after this long in the beam; until then the
// drain never lands the lethal bite. The first bite also waits one TOD_NECRO_STEP now.
// SOUL BEAM cuts it by 150 ms at Lv3 / Lv6 / Lv9 (1.0 -> 0.55 s). Elites are unaffected
// (they are never ripped; the drain simply wears them down).
#define TOD_NECRO_SOUL_MIN_MS     1000
// THE DRAIN: DoDamage per second PER ACTOR IN THE BEAM, in the map's OLD units -
// the power scale takes it x0.1 like every player hit. = TIER_SUSTAINED
// (gen_tod_twins.js), the map's mean gun DPS per class tier, base and PaP: the
// skull is the Necromancer's gun on every tier, so the tier moves the drain.
#define TOD_NECRO_DPS_T1          1235
#define TOD_NECRO_DPS_T2          2193
#define TOD_NECRO_DPS_T3          3574
#define TOD_NECRO_DPS_UP_T1       2228
#define TOD_NECRO_DPS_UP_T2       3858
#define TOD_NECRO_DPS_UP_T3       6295
#define TOD_NECRO_DPS_MULT        1.0      // THE ONE BALANCE KNOB: every target's drain x this
#define TOD_NECRO_CROWD           0.5      // the tier DPS is the beam's TOTAL on one soul; each extra soul held adds this much of it, split evenly (user 2026-09-26: "a little bit too much damage")
#define TOD_NECRO_STEP            0.25     // damage cadence (s): 4 hits/s per target

// ---- the soul meter (the clip) ------------------------------------------------
#define TOD_NECRO_METER_MAX       100
#define TOD_NECRO_BEAM_COST       7        // per second of beam
#define TOD_NECRO_SOUL_REFUND     3        // per soul taken
#define TOD_NECRO_REGEN           14       // per second, idle
#define TOD_NECRO_REGEN_DELAY     1.0      // s after the last use
#define TOD_NECRO_RESTART         20       // an emptied meter must refill this far

// ---- Widow's Wine = Burned Out ----------------------------------------------------
#define TOD_NECRO_BURN_PERK       "specialty_widowswine"
#define TOD_NECRO_BURN_RADIUS     720
#define TOD_NECRO_BURN_MAX        4        // the widow's grenade stack
#define TOD_NECRO_BURN_GAP_MS     1500     // hits this soon after a burst spend nothing

#namespace tod_necro_skull;

// THE CLIENTFIELDS REGISTER HERE, NOT IN init() (2026-09-26, the user's first
// launch of the 10:48 build: "Com_ERROR: Attempt to register ClientField
// tod_necro_fx post finalization of ClientField registration period failed").
// _tod_main::init runs at level init, AFTER the engine closes registration;
// REGISTER_SYSTEM's __init__ runs before it, the way _tod_archer / _tod_boss_fx /
// _tod_perk_lights and the lockstep .csc already do. LOCKSTEP with the .csc.
REGISTER_SYSTEM( "tod_necro_skull", &__init__, undefined )
function __init__()
{
	clientfield::register( "allplayers", "tod_necro_fx", VERSION_SHIP, 3, "int" );
	clientfield::register( "allplayers", "tod_necro_burn", VERSION_SHIP, 1, "counter" );
	clientfield::register( "allplayers", "tod_necro_bomb_band", VERSION_SHIP, 2, "int" );   // Soul Pulse ring size band 0..3 REGISTERED BEFORE the counter (LOCKSTEP csc): the client applies fields in this order, so the counter's callback reads the band just sent - after it, the first pulse of a new size drew the old ring (build 16 log: band 0 vs 3)
	clientfield::register( "allplayers", "tod_necro_bomb", VERSION_SHIP, 1, "counter" );   // Soul Pulse blast (client fx)
	clientfield::register( "actor", "tod_necro_soul", VERSION_SHIP, 3, "int" );
}

function init()
{
	level.tod_necro_w = GetWeapon( TOD_NECRO_STEM + "_b" );
	level.tod_necro_w_up = GetWeapon( TOD_NECRO_STEM + "_up_b" );
	callback::on_spawned( &on_spawned );
	dev_log( "INIT rev=4 staff_tiers=2,3 crowd=" + TOD_NECRO_CROWD + " drain=dps base=" + weapon_ok( level.tod_necro_w ) + " up=" + weapon_ok( level.tod_necro_w_up )
		+ " range=" + TOD_NECRO_RANGE + " dps_t1=" + TOD_NECRO_DPS_T1 + " mult=" + TOD_NECRO_DPS_MULT + " targets=" + TOD_NECRO_MAX_TARGETS + " rip_min_ms=" + TOD_NECRO_SOUL_MIN_MS + " cards=core9"
		+ " burn_radius=" + TOD_NECRO_BURN_RADIUS + " burn_max=" + TOD_NECRO_BURN_MAX );
	level thread burn_round_refill();
	level thread burn_hook_spider_drop();
}

function weapon_ok( w )
{
	return ( isdefined( w ) && w != level.weaponNone );
}

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_NECRO] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// =============================================================================
// per life
// =============================================================================
function on_spawned()
{
	self notify( "tod_necro_respawn" );
	self.tod_necro_meter = TOD_NECRO_METER_MAX;
	self.tod_necro_locked = false;
	self.tod_necro_mode = 0;
	self.tod_necro_targets = 0;
	self.tod_necro_last_use = 0;
	self.tod_necro_burn_next = 0;
	if ( !isdefined( self.tod_necro_burn_left ) ) self.tod_necro_burn_left = 0;
	self clientfield::set( "tod_necro_fx", 0 );
	self thread skull_loop();
	self thread burnout_watch();
	self thread burn_perk_watch();
	self thread burn_max_ammo_watch();
}

function is_necro()
{
	return ( isdefined( self.tod_class ) && self.tod_class == TOD_NECRO_CLASS );
}

// the held weapon IS the skull (either form); returns 0 none / 1 base / 2 PaP
function skull_form()
{
	w = self GetCurrentWeapon();
	if ( !isdefined( w ) || !isdefined( w.name ) || ( !IsSubStr( w.name, TOD_NECRO_STEM ) && !IsSubStr( w.name, "tod_necro_staff" ) ) ) return 0;
	if ( IsSubStr( w.name, "_up" ) ) return 2;
	return 1;
}

function can_act()
{
	if ( !isdefined( self ) || !IsAlive( self ) ) return false;
	if ( self laststand::player_is_in_laststand() ) return false;
	if ( IS_TRUE( self.tod_menu_frozen ) || IS_TRUE( level.tod_upgrade_pause ) ) return false;
	if ( IS_TRUE( self.tod_jumppad_flying ) ) return false;
	if ( self IsMeleeing() ) return false;
	return true;
}

function set_mode( m )
{
	if ( self.tod_necro_mode == m ) return;
	was = self.tod_necro_mode;
	self.tod_necro_mode = m;
	if ( !isdefined( self.tod_necro_mode_epoch ) ) self.tod_necro_mode_epoch = 0;
	self.tod_necro_mode_epoch++;
	// one frame of "start" so the client plays the start burst, then the loop
	if ( m == 1 || m == 3 )
	{
		// the Pack-a-Punched skull's beam sends 5/6 (its own recoloured beam +
		// hum on the client); the base skull and the summon channel keep 1/2, 3/4
		v = m;
		if ( m == 1 && self skull_form() == 2 ) v = 5;
		self clientfield::set( "tod_necro_fx", v );
		self thread promote_loop( m, v, self.tod_necro_mode_epoch );
	}
	else
		self clientfield::set( "tod_necro_fx", 0 );
	if ( m == 1 ) dev_log( "BEAM on player=" + self GetEntityNumber() + " meter=" + Int( self.tod_necro_meter ) );
	else if ( m == 3 ) dev_log( "SUMMON on player=" + self GetEntityNumber() + " meter=" + Int( self.tod_necro_meter ) );
	else if ( was == 1 ) dev_log( "BEAM off player=" + self GetEntityNumber() + " meter=" + Int( self.tod_necro_meter ) + " targets_left=" + self.tod_necro_targets );
	else if ( was == 3 ) dev_log( "SUMMON off player=" + self GetEntityNumber() + " meter=" + Int( self.tod_necro_meter ) );
}

function promote_loop( m, v, epoch )
{
	self endon( "disconnect" );
	wait 0.1;
	if ( isdefined( self ) && self.tod_necro_mode == m && self.tod_necro_mode_epoch == epoch )
		self clientfield::set( "tod_necro_fx", v + 1 );
}

function skull_loop()
{
	self endon( "disconnect" );
	self endon( "tod_necro_respawn" );
	level endon( "end_game" );
	for ( ;; )
	{
		wait TOD_NECRO_TICK;
		form = self skull_form();
        held = self GetCurrentWeapon();
        if ( form != 0 && isdefined( held ) && self.tod_necro_held !== held )
        {
            self set_mode( 0 );
            self tod_necro_summon::bind_cancel( "weapon_change" );
            self.tod_necro_held = held;
            dev_log( "STAFF_EQUIP player=" + self GetEntityNumber() + " weapon=" + held.name + " form=" + form );
        }
		if ( form == 0 || !self is_necro() )
		{
			self set_mode( 0 );
			self meter_regen();
			self tod_necro_summon::bind_cancel( "holster" );   // a half bind never carries over
			continue;
		}
		up = ( form == 2 );
		ok = self can_act();
		if ( self.tod_necro_locked && self.tod_necro_meter >= TOD_NECRO_RESTART )
		{
			self.tod_necro_locked = false;
			dev_log( "METER_READY player=" + self GetEntityNumber() + " meter=" + Int( self.tod_necro_meter ) );
		}
		pressed = self AttackButtonPressed();
		// THE RECHARGE IS HEARD (user 2026-10-05: "I like this concept of the necromancer ... not having
		// unlimited ammo and needs to recharge"): a fire press on a meter still refilling is refused out
		// loud, once per press. The beam used to just not come (10 empties in that run, nothing said).
		if ( ok && self.tod_necro_locked && pressed && !IS_TRUE( self.tod_necro_fire_down ) )
			tod_ability_fx::kit_deny( self, "beam", "meter_recharging" );
		self.tod_necro_fire_down = pressed;
		fire = ( ok && !self.tod_necro_locked && pressed && self.tod_necro_meter > 0 );
		aim = ( ok && !fire && !self.tod_necro_locked && self AdsButtonPressed() );
		if ( fire )
		{
			self set_mode( 1 );
			self tod_necro_summon::bind_cancel( "fire" );   // firing drops a zombie being bound
			self.tod_necro_last_use = GetTime();
			self.tod_necro_meter -= TOD_NECRO_BEAM_COST * TOD_NECRO_TICK * self tod_necro_summon::beam_cost_mult();   // SOUL BEAM card
			self beam_acquire( up );
		}
		else if ( self tod_necro_summon::aim_tick( aim ) )
		{
			self set_mode( 3 );   // the skull's torch light while it binds a zombie
		}
		else
		{
			self set_mode( 0 );
			self meter_regen();
		}
		if ( self.tod_necro_meter <= 0 )
		{
			self.tod_necro_meter = 0;
			if ( !self.tod_necro_locked )
			{
				self.tod_necro_locked = true;
				self set_mode( 0 );
				tod_ability_fx::kit_deny( self, "beam", "meter_empty" );   // the beam cuts out: say so
				dev_log( "METER_EMPTY player=" + self GetEntityNumber() + " restart_at=" + TOD_NECRO_RESTART );
			}
		}
		// the clip IS the meter: the HUD's ammo count reads it, and the Charge
		// Shot release can never empty the weapon
		w = self GetCurrentWeapon();
		if ( self GetWeaponAmmoClip( w ) != Int( self.tod_necro_meter ) )
			self SetWeaponAmmoClip( w, Int( self.tod_necro_meter ) );
	}
}

function meter_regen()
{
	if ( self.tod_necro_meter >= TOD_NECRO_METER_MAX ) return;
	if ( GetTime() - self.tod_necro_last_use < TOD_NECRO_REGEN_DELAY * 1000 ) return;
	self.tod_necro_meter = min( TOD_NECRO_METER_MAX, self.tod_necro_meter + TOD_NECRO_REGEN * TOD_NECRO_TICK );
}

// =============================================================================
// targets
// =============================================================================
// A plain horde zombie the drain finishes has its soul torn out (the rip + a meter
// refund); everything else - bosses and elites carry tod_boss_kind, dogs /
// Manglers / Doppelghasts are other archetypes - just takes the damage and dies
// its own death.
function is_elite( ai )
{
	if ( ai.archetype !== "zombie" ) return true;
	if ( isdefined( ai.tod_boss_kind ) ) return true;
	if ( IS_TRUE( ai.ignore_nuke ) ) return true;
	return false;
}

function in_cone( ai, dot, range )
{
	if ( !isdefined( ai ) || !IsAlive( ai ) ) return false;
	if ( DistanceSquared( self.origin, ai.origin ) > range * range ) return false;
	if ( self util::is_player_looking_at( ai GetCentroid(), dot, false ) ) return true;
	if ( self util::is_player_looking_at( ai.origin, dot, false ) ) return true;
	return false;
}

function has_sight( ai )
{
	return SightTracePassed( self GetEye(), ai GetCentroid(), false, self );
}

// per target, per second, OLD units (see TOD_NECRO_DPS_*). The SOUL BEAM card (the
// Necromancer's CORE WEAPON card since 2026-09-27): +10% / Lv on every target, applied
// HERE rather than in the damage callback so the soul-rip test sees the real bite
// (Lua DETAIL[39]). The DAMAGE card that used to double this is retired.
function beam_dps( up, elite )
{
	t = self tod_necro_summon::tier();
	if ( up ) d = ( t >= 3 ? TOD_NECRO_DPS_UP_T3 : ( t == 2 ? TOD_NECRO_DPS_UP_T2 : TOD_NECRO_DPS_UP_T1 ) );
	else      d = ( t >= 3 ? TOD_NECRO_DPS_T3 : ( t == 2 ? TOD_NECRO_DPS_T2 : TOD_NECRO_DPS_T1 ) );
	d = d * TOD_NECRO_DPS_MULT * self tod_necro_summon::beam_dmg_mult();   // SOUL BEAM, the core card: +10% / Lv (2026-09-27)
	return d;
}

// THE CROWD SHARE: the beam's tier DPS is its TOTAL on one soul, and each extra
// soul held adds TOD_NECRO_CROWD of it, split evenly. One soul = x1 (a gun's DPS);
// four = x2.5 total, 0.625 each (it was x4 total, a full gun on every soul).
function crowd_share()
{
	n = self.tod_necro_targets;
	if ( !isdefined( n ) || n < 1 ) n = 1;
	return ( 1 + TOD_NECRO_CROWD * ( n - 1 ) ) / n;
}

function beam_acquire( up )
{
	cap = ( up ? TOD_NECRO_MAX_TARGETS_UP : TOD_NECRO_MAX_TARGETS ) + self tod_necro_summon::beam_targets_add();   // SOUL BEAM card
	if ( self.tod_necro_targets >= cap ) return;
	range = ( up ? TOD_NECRO_RANGE_UP : TOD_NECRO_RANGE ) * self tod_necro_summon::reach_range_mult();   // REAPER'S REACH (2026-09-27)
	dot = TOD_NECRO_DOT - self tod_necro_summon::reach_dot_cut();
	a = util::get_array_of_closest( self.origin, GetAITeamArray( level.zombie_team ), undefined, cap * 2, range );
	foreach ( ai in a )
	{
		if ( self.tod_necro_targets >= cap ) return;
		if ( !isdefined( ai ) || !IsAlive( ai ) || isdefined( ai.tod_necro_drainer ) ) continue;
		if ( isdefined( ai.tod_necro_binder ) || IS_TRUE( ai.marked_for_death ) ) continue;   // a zombie being bound is the summon's
		if ( !self in_cone( ai, dot, range ) || !self has_sight( ai ) ) continue;
		self thread drain( ai, up, range );
	}
}

// THE DRAIN: damage over time while the beam holds the actor. It is never held,
// lifted or slowed - the only tell is the soul stream (state 2, drawn by the
// client) and the damage.
function drain( ai, up, range )
{
	self endon( "disconnect" );
	ai.tod_necro_drainer = self;
	self.tod_necro_targets++;
	elite = is_elite( ai );
	ai clientfield::set( "tod_necro_soul", 2 );   // client: the soul stream from its chest to this player
	dev_log( "BEAM targets=" + self.tod_necro_targets + " dps_each=" + Int( self beam_dps( up, elite ) * self crowd_share() )
		+ " share=" + self crowd_share() + " elite=" + elite + " up=" + up );
	w = self GetCurrentWeapon();
	t0 = GetTime();
	next_hit = t0 + TOD_NECRO_STEP * 1000;   // no bite on the frame the beam touches it (2026-09-27)
	rip_min = TOD_NECRO_SOUL_MIN_MS - self tod_necro_summon::beam_rip_cut_ms();
	dealt = 0;
	hits = 0;
	why = "released";
	for ( ;; )
	{
		if ( !isdefined( ai ) || !IsAlive( ai ) ) { why = "dead"; break; }
		if ( isdefined( ai.tod_necro_binder ) ) { why = "bound"; break; }   // the summon took it over
		if ( !isdefined( self ) || self.tod_necro_mode < 1 || self.tod_necro_mode > 2 || self skull_form() == 0 ) break;
		if ( !self in_cone( ai, TOD_NECRO_HOLD_DOT - self tod_necro_summon::reach_dot_cut(), range * 1.15 ) ) { why = "left_cone"; break; }
		now = GetTime();
		if ( now >= next_hit )
		{
			next_hit = now + TOD_NECRO_STEP * 1000;
			amt = Int( self beam_dps( up, elite ) * self crowd_share() * TOD_NECRO_STEP + 0.5 );
			// the power scale takes a player hit x0.1: the drain finishes a plain
			// zombie when a tenth of the step would, and then takes its soul whole
			if ( !elite && amt * 0.1 >= ai.health )
			{
				// the lethal bite waits for the soul-rip minimum: the soul keeps
				// streaming (no damage lands) until it has been in the beam long enough
				if ( ( now - t0 ) < rip_min )
				{
					wait TOD_NECRO_TICK;
					continue;
				}
				self soul_take( ai, ( now - t0 ), dealt );
				why = "soul";
				break;
			}
			ai DoDamage( amt, ai GetCentroid(), self, self, "none", "MOD_UNKNOWN", 0, w );
			dealt += amt;
			hits++;
			if ( !isdefined( ai ) || !IsAlive( ai ) )
			{
				self tod_necro_summon::bomb_charge( "drain" );   // an elite (or anything) the drain finished feeds the Soul Bomb
				why = "dead";
				break;
			}
		}
		wait TOD_NECRO_TICK;
	}
	if ( isdefined( self ) ) self.tod_necro_targets = Int( max( 0, self.tod_necro_targets - 1 ) );
	if ( isdefined( ai ) )
	{
		if ( ai.tod_necro_drainer === self ) ai.tod_necro_drainer = undefined;
		// the stream stops (a corpse keeps its field otherwise); a zombie torn out
		// (1) or taken by the summon (3) already carries its next state
		if ( why != "soul" && why != "bound" ) ai clientfield::set( "tod_necro_soul", 0 );
	}
	if ( hits >= 4 || elite )
		dev_log( "DRAIN player=" + ( isdefined( self ) ? self GetEntityNumber() : -1 ) + " target=" + ( isdefined( ai ) ? ai GetEntityNumber() : -1 )
			+ " kind=" + ( isdefined( ai ) && isdefined( ai.archetype ) ? ai.archetype : "gone" ) + " elite=" + elite + " end=" + why
			+ " held_ms=" + ( GetTime() - t0 ) + " dealt_old=" + dealt + " hits=" + hits + " up=" + up );
}

// the drain's last bite: the soul leaves (the rip on the client), the meter drinks it
function soul_take( ai, held_ms, dealt )
{
	self.tod_necro_meter = min( TOD_NECRO_METER_MAX, self.tod_necro_meter + TOD_NECRO_SOUL_REFUND );
	self notify( "tod_necro_soul" );
	self tod_necro_summon::bomb_charge( "beam" );   // every soul the beam takes feeds the Soul Bomb
	dev_log( "SOUL player=" + self GetEntityNumber() + " target=" + ai GetEntityNumber() + " held_ms=" + held_ms
		+ " dealt_old=" + dealt + " health=" + ai.health + " meter=" + Int( self.tod_necro_meter ) );
	tod_necro_summon::soul_kill( ai, self, undefined, "beam", 0 );   // state 1, a network frame, then the kill (paid as a kill)
}

// =============================================================================
// WIDOW'S WINE = BURNED OUT
// =============================================================================
function burnout_watch()
{
	self endon( "disconnect" );
	self endon( "tod_necro_respawn" );
	for ( ;; )
	{
		self waittill( "damage", amount, attacker, dir, point, mod );
		if ( !self is_necro() ) continue;
		if ( !isdefined( mod ) || mod != "MOD_MELEE" || !isdefined( attacker ) || !IsAI( attacker ) ) continue;
		if ( !self HasPerk( TOD_NECRO_BURN_PERK ) ) continue;
		if ( self.tod_necro_burn_left <= 0 )
		{
			dev_log( "BURN_DENY player=" + self GetEntityNumber() + " why=no_charges round=" + level.round_number );
			continue;
		}
		if ( GetTime() < self.tod_necro_burn_next )
		{
			dev_log( "BURN_DENY player=" + self GetEntityNumber() + " why=gap left_ms=" + ( self.tod_necro_burn_next - GetTime() ) );
			continue;
		}
		self.tod_necro_burn_left--;
		self.tod_necro_burn_next = GetTime() + TOD_NECRO_BURN_GAP_MS;
		self thread burnout_result();
	}
}

// ---- the charge count (a widow's grenade stack) --------------------------------
// BURNED OUT card (2026-09-27): one more charge at Lv3 / Lv6 / Lv9 (4 -> 7).
function burn_max() { return TOD_NECRO_BURN_MAX + self tod_necro_summon::burn_card_bonus(); }

function burn_set( n, why )
{
	if ( n > self burn_max() ) n = self burn_max();
	if ( n < 0 ) n = 0;
	if ( n == self.tod_necro_burn_left ) return;
	dev_log( "BURN_CHARGES player=" + self GetEntityNumber() + " " + self.tod_necro_burn_left + "->" + n + " why=" + why );
	self.tod_necro_burn_left = n;
}

// gain the perk = a full stack, lose it = none (stock gives / takes the grenade)
function burn_perk_watch()
{
	self endon( "disconnect" );
	self endon( "tod_necro_respawn" );
	had = false;
	for ( ;; )
	{
		has = ( self is_necro() && self HasPerk( TOD_NECRO_BURN_PERK ) );
		if ( has && !had ) self burn_set( self burn_max(), "perk_gained" );
		else if ( !has && had ) self burn_set( 0, "perk_lost" );
		had = has;
		wait 0.25;
	}
}

// Max Ammo refills lethal grenades, so it refills the stack
function burn_max_ammo_watch()
{
	self endon( "disconnect" );
	self endon( "tod_necro_respawn" );
	for ( ;; )
	{
		self waittill( "zmb_max_ammo" );
		if ( self is_necro() && self HasPerk( TOD_NECRO_BURN_PERK ) ) self burn_set( self burn_max(), "max_ammo" );
	}
}

// stock _zm::award_grenades_for_survivors at every round start
function burn_round_refill()
{
	level endon( "end_game" );
	for ( ;; )
	{
		level waittill( "start_of_round" );
		foreach ( p in GetPlayers() )
		{
			if ( !isdefined( p ) || !p is_necro() || !p HasPerk( TOD_NECRO_BURN_PERK ) ) continue;
			if ( p laststand::player_is_in_laststand() ) continue;
			// stock's fraction bands (< .25 / < .5 of the stack) as counts
			mx = p burn_max();
			if ( p.tod_necro_burn_left * 4 < mx ) p burn_set( Int( Max( 2, mx / 2 ) ), "round_start" );
			else if ( p.tod_necro_burn_left * 2 < mx ) p burn_set( Int( Max( 3, ( mx * 3 ) / 4 ) ), "round_start" );
			else p burn_set( mx, "round_start" );
		}
	}
}

// A spider drop (stock "ww_grenade" powerup) gives a Necromancer one charge;
// everyone else keeps stock's grenade refill. Wraps the registered grab.
function burn_hook_spider_drop()
{
	wait 0.05;
	if ( !isdefined( level._custom_powerups ) || !isdefined( level._custom_powerups[ "ww_grenade" ] ) )
	{
		dev_log( "BURN_HOOK none=ww_grenade (Widow's Wine not in this map?)" );
		return;
	}
	level.tod_necro_ww_grab_orig = level._custom_powerups[ "ww_grenade" ].grab_powerup;
	level._custom_powerups[ "ww_grenade" ].grab_powerup = &burn_spider_grab;
	dev_log( "BURN_HOOK ww_grenade wrapped" );
}

// self = the powerup
function burn_spider_grab( player )
{
	if ( isdefined( player ) && player is_necro() && player HasPerk( TOD_NECRO_BURN_PERK )
		&& !player laststand::player_is_in_laststand() )
	{
		player burn_set( player.tod_necro_burn_left + 1, "spider_drop" );
		return;
	}
	if ( isdefined( level.tod_necro_ww_grab_orig ) )
		return self [[ level.tod_necro_ww_grab_orig ]]( player );
}

function burnout_result()
{
	self clientfield::increment( "tod_necro_burn" );
	refill = self tod_necro_summon::burn_card_meter();   // BURNED OUT card: +2 soul meter / Lv per burst
	if ( refill > 0 ) self.tod_necro_meter = min( TOD_NECRO_METER_MAX, self.tod_necro_meter + refill );
	a = array::get_all_closest( self.origin, GetAITeamArray( level.zombie_team ), undefined, undefined, TOD_NECRO_BURN_RADIUS );
	n = 0;
	skipped = 0;
	foreach ( ai in a )
	{
		if ( !isdefined( ai ) || !IsAlive( ai ) ) continue;
		if ( is_elite( ai ) || IS_TRUE( ai.marked_for_death ) || zm_utility::is_magic_bullet_shield_enabled( ai ) )
		{
			skipped++;
			continue;
		}
		ai.marked_for_death = true;
		ai clientfield::set( "tod_necro_soul", 4 );
		ai thread burnout_kill( self );
		n++;
	}
	dev_log( "BURN player=" + self GetEntityNumber() + " killed=" + n + " skipped_elites=" + skipped
		+ " charges_left=" + self.tod_necro_burn_left );
}

function burnout_kill( player )
{
	self endon( "death" );
	util::wait_network_frame();
	wait RandomFloatRange( 0.05, 0.3 );
	if ( !isdefined( self ) || !IsAlive( self ) ) return;
	if ( isdefined( player ) )
	{
		self DoDamage( self.health + 666, self.origin, player, player, "none", "MOD_BURNED" );
		player tod_necro_summon::bomb_charge( "burn" );   // a Burned Out kill feeds the Soul Bomb
	}
	else
		self DoDamage( self.health + 666, self.origin );
}
